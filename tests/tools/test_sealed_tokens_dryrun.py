# -*- coding: utf-8 -*-
"""封印の語の表をまとめた語で 2 つの守りを空回しする道具(``tools/instruments/sealed_tokens_dryrun.py``)の試験。

確かめること: 数え方(偽の語と偽の道筋で)・構築の封の守りは表だけを差し替えて呼び、後で元に戻すこと・
出力と記録に語が 1 つも出ないこと(11-20 §1 の 3「語・ファイル名・道は出さない」)。
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "_sealed_tokens_dryrun_under_test", ROOT / "tools" / "instruments" / "sealed_tokens_dryrun.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


S = _load()


def test_merged_keeps_order_and_drops_repeats():
    assert S.merged(("alpha", "beta"), ("beta", "gamma")) == ("alpha", "beta", "gamma")
    assert S.merged((), ("x",)) == ("x",)


def test_path_hit_is_case_blind_and_slash_blind():
    assert S.path_hit("data\\ALPHA_layer\\a.csv", ("alpha",)) is True
    assert S.path_hit("data/other/a.csv", ("alpha",)) is False
    assert S.path_hit("data/x/Gamma.bin", ("GAMMA",)) is True


def test_count_new_path_hits_counts_only_newly_hit_paths():
    paths = ["data/alpha/1", "data/gamma/2", "data/gamma/3", "docs/plain.md"]
    r = S.count_new_path_hits(paths, current=("alpha",), union=("alpha", "gamma"))
    assert r == {"n_paths": 4, "n_hit_current": 1, "n_hit_merged": 3, "n_new": 2}
    same = S.count_new_path_hits(paths, current=("alpha", "gamma"), union=("alpha", "gamma"))
    assert same["n_new"] == 0


def test_build_scan_new_swaps_only_the_table_and_restores_it(tmp_path: Path):
    build = tmp_path / "build"
    (build / "audit").mkdir(parents=True)
    (build / "a.py").write_text("x = 'alpha'\n", encoding="utf-8")
    (build / "b.py").write_text("y = 'gamma and delta'\n", encoding="utf-8")
    (build / "c.py").write_text("z = 1\n", encoding="utf-8")
    fake = types.SimpleNamespace(__file__=str(build / "audit" / "fake_freeze.py"), HOLDOUT_TOKENS=("alpha",))

    def scan(build_root: Path) -> dict[str, list[str]]:
        hits: dict[str, list[str]] = {}
        for p in sorted(build_root.rglob("*.py")):
            found = [t for t in fake.HOLDOUT_TOKENS if t in p.read_text(encoding="utf-8")]
            if found:
                hits[p.relative_to(build_root).as_posix()] = found
        return hits

    fake.scan_build_sources = scan
    r = S.build_scan_new(fake, ("alpha", "gamma", "delta"))
    assert r == {
        "n_files_hit_current": 1,
        "n_files_hit_merged": 2,
        "n_new_files": 1,
        "n_pairs_current": 1,
        "n_pairs_merged": 3,
        "n_new_pairs": 2,
    }
    assert fake.HOLDOUT_TOKENS == ("alpha",)  # 表は元に戻る


def test_output_never_shows_a_token(capsys, tmp_path: Path):
    rg, w19 = S._load_read_guard(), S._load_w19()
    tokens = set(rg.SEALED_TOKENS) | set(rg.GAUGE_DENY_TOKENS) | set(w19.HOLDOUT_TOKENS)
    out_json = tmp_path / "dryrun.json"
    code = S.main(["--json", str(out_json)])
    captured = capsys.readouterr()
    text = captured.out + captured.err + out_json.read_text(encoding="utf-8")
    assert code in (0, 1)
    # 落ちたときに pytest が語を表示しないよう、当たった数だけを比べる
    leaked = sum(1 for token in tokens if token in text)
    assert leaked == 0, "出力か記録に、封印の語が出ている(数だけを出すこと)"
    data = json.loads(out_json.read_text(encoding="utf-8"))
    # 記録の値は、数と真偽と、数だけの入れ子(道筋やファイルの名を入れない)
    def _only_numbers(v) -> bool:
        if isinstance(v, dict):
            return all(_only_numbers(x) for x in v.values())
        return isinstance(v, (int, bool))

    assert all(_only_numbers(v) for k, v in data.items() if k != "schema")
    assert data["n_merged"] <= data["n_sealed"] + data["n_holdout"]
    assert (code == 0) == data["mergeable"]
    assert w19.HOLDOUT_TOKENS == tuple(w19.HOLDOUT_TOKENS)
