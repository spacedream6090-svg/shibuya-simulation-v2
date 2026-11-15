# -*- coding: utf-8 -*-
"""tools/instruments/sealed_tokens_compare.py の試験(11-16 §1-6 の 5=語を出さずに個数だけで比べる)。"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "_sealed_tokens_compare_under_test", ROOT / "tools" / "instruments" / "sealed_tokens_compare.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


S = _load()


def test_compare_counts_only():
    r = S.compare(("alpha", "beta", "gamma_x"), ("beta", "GAMMA", "delta"))
    assert (r["n_a"], r["n_b"], r["common"], r["only_a"], r["only_b"]) == (3, 3, 1, 2, 2)
    assert r["same_set"] is False and r["same_order"] is False
    # gamma_x は GAMMA を含む(大文字小文字をそろえて)=字面の重なり 1。alpha と delta は重ならない
    assert r["only_a_overlapping_b"] == 1 and r["only_b_overlapping_a"] == 1
    # 辞書の値は数と真偽だけ(語が入らない)
    assert all(isinstance(v, (int, bool, str)) for v in r.values())
    assert [k for k, v in r.items() if isinstance(v, str)] == ["schema"]


def test_same_sets():
    r = S.compare(("a", "b"), ("b", "a"))
    assert r["same_set"] is True and r["same_order"] is False and r["only_a"] == 0 and r["only_b"] == 0


def test_output_never_shows_a_token(capsys, tmp_path: Path):
    a, b = S._load_read_guard_tokens(), S._load_w19_tokens()
    out_json = tmp_path / "r.json"
    code = S.main(["--json", str(out_json)])
    captured = capsys.readouterr()
    text = captured.out + captured.err + out_json.read_text(encoding="utf-8")
    assert code in (0, 1)
    # 落ちたときに pytest が語を表示しないよう、当たった数だけを比べる
    leaked = sum(1 for token in set(a) | set(b) if token in text)
    assert leaked == 0, "語が出力に出ている"
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["n_a"] == len(a) and data["n_b"] == len(b)
    assert (code == 0) == data["same_set"]
