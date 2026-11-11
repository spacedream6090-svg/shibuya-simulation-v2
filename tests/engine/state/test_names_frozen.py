"""移す段 2-1(返事その 7 §4-2 の 3・計画 docs/reference/package-map-final-2026-11-09.md §7-2): 名前を変えてはいけない文字列。

見た目はモジュールの道だが中身は ID の文字列(乱数の領域の名・版の ID・ハッシュと指紋の見出し・manifest の節の名・
塩)と、manifest・run_meta・テープの見出し・ハッシュに入る道の形の文字列を ``names_frozen.json`` に凍結した。移す道具が
機械で書き換えると乱数の列やハッシュや manifest が変わるので、src の AST と短いランを見て同じことを確かめる(道と行の
番号は鍵にしない=ファイルを動かしても通る)。

- 乱数の領域の名の 3 つの表の鍵の集合・版の ID の多重集合・ハッシュの見出しの多重集合は、集めたものが凍結と同じ。
- 道の形の乱数の領域の名・接尾・ほかの名は、ランの側の src の定数に出てくる数が凍結と同じ(1 か所だけ書き換えても
  落ちる=検収 L1)。
- 短いランの manifest・run_meta・テープの見出し・ハッシュから拾った道の形の部分が、構成ごと・拾う所ごとに凍結と同じ
  (手の一覧でなくランから拾う=検収 M4。拾い方は ``shaped_names.py``・世界資産の構成は data が要る)。

凍結の作り方は ``docs/bench/analysis/move-346/tools/gen_frozen_names.py``(src の AST はここで別の実装で集める)。
"""

from __future__ import annotations

import ast
import json
import re
from collections import Counter
from pathlib import Path

import pytest

import shibuya

from tests.engine.state import shaped_names as SN

ROOT = Path(__file__).resolve().parents[3]
PKG = ROOT / "src" / "shibuya"
FROZEN = json.loads(Path(__file__).with_name("names_frozen.json").read_text(encoding="utf-8"))
ID_STR = re.compile(r"^shibuya\.[A-Za-z0-9_.]+/")
ID_BYTES = re.compile(rb"^shibuya\.[A-Za-z0-9_.]+/")
WORLD = pytest.mark.requires_data("world_v2:w17_schedule.parquet")


def _sources(with_build: bool) -> list[ast.Module]:
    return [ast.parse(p.read_text(encoding="utf-8")) for p in sorted(PKG.rglob("*.py"))
            if with_build or p.relative_to(PKG).parts[0] != "build"]


def _literals(trees: list[ast.Module]) -> list[str | bytes]:
    """文字列とバイト列の定数(docstring を除く)。"""
    out: list[str | bytes] = []
    for tree in trees:
        doc = set()
        for n in ast.walk(tree):
            body = getattr(n, "body", None)
            if (isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and body
                    and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)):
                doc.add(id(body[0].value))
        out += [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, (str, bytes)) and id(n) not in doc]
    return out


def _top_dict_keys(trees: list[ast.Module], name: str) -> list[list[str]]:
    found = []
    for tree in trees:
        for n in tree.body:
            targets = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, ast.AnnAssign) else []
            if any(isinstance(t, ast.Name) and t.id == name for t in targets) and isinstance(n.value, ast.Dict):
                found.append([k.value for k in n.value.keys if isinstance(k, ast.Constant)])
    return found


RUN_SIDE = _sources(with_build=False)
EVERY = _sources(with_build=True)
RUN_COUNT = Counter(c for c in _literals(RUN_SIDE) if isinstance(c, str))


def test_frozen_file_has_the_declared_shape():
    assert FROZEN["schema"] == "shibuya.tests/move/names-frozen/2"
    assert set(FROZEN) == {"schema", "note", "rng_domains", "rng_domains_path_shaped", "rng_domain_suffixes",
                           "version_ids", "hash_headers", "other_path_shaped", "run_path_shaped"}
    assert sum(len(v) for v in FROZEN["rng_domains"].values()) == 41  # 計画の 42 から第346 で conversation.invite を消した
    assert set(FROZEN["run_path_shaped"]) == set(SN.CONFIGS)


def test_rng_domain_tables_keep_their_keys():
    for name, keys in FROZEN["rng_domains"].items():
        found = _top_dict_keys(RUN_SIDE, name)
        assert len(found) == 1, f"{name} の定義が {len(found)} 個"
        assert sorted(found[0]) == keys, f"{name} の鍵が凍結と違う(乱数の領域の名は変えない)"


def test_path_shaped_rng_domains_are_kept_by_value_and_count():
    keys = {k for v in FROZEN["rng_domains"].values() for k in v}
    suffixes = FROZEN["rng_domain_suffixes"]
    assert {s: RUN_COUNT[s] for s in suffixes} == suffixes, "接尾の文字列の数が変わった"
    for name, count in FROZEN["rng_domains_path_shaped"].items():
        assert name in keys, f"{name} が乱数の領域の名の表に無い"
        assert RUN_COUNT[name] == count, f"{name} の出てくる数が {count} → {RUN_COUNT[name]}(書き換えた?)"
        assert count or any(name.endswith(s) and RUN_COUNT[name[: -len(s)]] for s in suffixes)


def test_version_ids_are_the_frozen_multiset():
    got = sorted(["b", c.decode("utf-8")] if isinstance(c, bytes) else ["s", c] for c in _literals(EVERY)
                 if (ID_BYTES if isinstance(c, bytes) else ID_STR).match(c))
    want = FROZEN["version_ids"]
    assert Counter(map(tuple, got)) == Counter(map(tuple, want)), (
        f"版の ID が変わった: 足りない {sorted(set(map(tuple, want)) - set(map(tuple, got)))[:5]}・"
        f"新しい {sorted(set(map(tuple, got)) - set(map(tuple, want)))[:5]}(足したら理由を記録に書いて更新する)")


def test_hash_headers_are_the_frozen_multiset():
    got = sorted(c.decode("utf-8") for c in _literals(EVERY) if isinstance(c, bytes) and c.startswith(b"shibuya."))
    assert got == FROZEN["hash_headers"]


def test_other_path_shaped_names_are_kept_by_value_and_count():
    got = {v: RUN_COUNT[v] for v in FROZEN["other_path_shaped"]}
    assert got == FROZEN["other_path_shaped"], f"道と同じ形の名の数が変わった(書き換えた?): {got}"


def test_shaped_pattern_finds_both_forms_inside_japanese_text():
    # 〔段 4 の下ごしらえ〕斜線の道は 1 つの定数に置き、入力の文と期待の両方で使う(前は日本語の文の中=移す道具が触らない と、
    # 期待の一覧=移す道具が書き換える に同じ字面を 2 回書いていて、移した後に食い違った)。拾い方の確かめは同じ
    slash = "engine/energy.py"
    text = f"D-118 の式({slash} の見出しの項)・HD-engine.energy-cc73b60c・core.rng.philox_array(seed, …)"
    assert SN.shaped(text) == ["engine.energy", "core.rng.philox_array", slash]
    assert SN.shaped("data/world/v2・world_dir・engine・economy.stage2") == ["economy.stage2"]


@pytest.mark.parametrize("name", [
    pytest.param(n, marks=WORLD) if kind == "world" else n for n, (kind, _kw, _env) in SN.CONFIGS.items()])
def test_run_outputs_contain_exactly_the_frozen_path_shaped_names(name):
    """短いランの manifest・run_meta・テープの見出し・ハッシュから拾った道の形の部分が凍結と同じ(検収 M4)。"""
    got = SN.run_config(name, repo=ROOT, src=Path(shibuya.__file__).resolve().parents[1])
    want = FROZEN["run_path_shaped"][name]
    for src in SN.SOURCES:
        new = sorted(set(got[src]) - set(want[src]))
        gone = sorted(set(want[src]) - set(got[src]))
        assert not new and not gone, f"{name} の {src}: 新しい {new[:5]}・消えた {gone[:5]}(書き換えた?凍結を更新するなら理由を記録に)"
