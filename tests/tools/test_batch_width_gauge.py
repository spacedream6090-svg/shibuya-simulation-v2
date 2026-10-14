# -*- coding: utf-8 -*-
"""tools/instruments/batch_width_gauge.py(第 3 期 3-2・TM4 の既定の幅の試験の道具)の試験。

- 合成の記録(3 つの幅 × 6 salt)から表を作る: final の一致の割合・指標の対の差・salt 間の幅(``salt_compare`` の
  ``width_base``)・(g) 中か・(f) 単調か・既定の幅の候補。置き場の指標(遅刻・待ち合わせ)は null と注。
- 差が salt の幅を超える幅は候補にならない・単調でない並びは (f) 偽・正解の幅が無い/重複は落ちる。
- ``table`` の CLI(JSONL → JSON と Markdown)。
- 子プロセスの 1 本(合成の世界 20 体 30 刻み)で記録の形(final・呼数・batching の幅)。
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_PATH = ROOT / "tools" / "instruments" / "batch_width_gauge.py"


@pytest.fixture(scope="module")
def G():
    name = "batch_width_gauge"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _PATH)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


CALLS_REF = [100.0, 104.0, 98.0, 101.0, 99.0, 103.0]


def _records(shift: dict[int, float], final_moves: set[int] = frozenset()) -> list[dict]:
    """幅 60(正解)・30・10 × salt 1〜6。呼数は正解に ``shift[幅]`` を足した値・行動は全部同じ。"""
    out = []
    for w in (60, 30, 10):
        for i, s in enumerate(range(1, 7)):
            out.append({"width_s": w, "salt": s, "final": f"f{s}" + ("x" if w in final_moves else ""),
                        "calls": CALLS_REF[i] + shift.get(w, 0.0), "actions": 500.0 + s,
                        "message_delay_max_s": {60: 0.0, 30: 0.0, 10: 0.0}[w]})
    return out


def test_zero_difference_table_has_every_width_within_and_monotone(G):
    tab = G.table(_records({}))
    assert [r["width_s"] for r in tab["rows"]] == [60, 30, 10] and tab["rows"][0]["is_ref"]
    for r in tab["rows"]:
        assert r["final_equal"] == 1.0 and r["n_salts"] == 6
        m = r["metrics"]["calls"]
        assert m["diff"] == 0.0 and m["within"] is True and m["salt_width"] > 0
        assert r["metrics"]["lateness"]["diff"] is None and r["metrics"]["lateness"]["note"] == G.PLACEHOLDER_NOTE
        assert r["metrics"]["meeting"]["within"] is None
    assert tab["monotone"]["calls"] is True and tab["monotone"]["lateness"] is None
    assert tab["default_candidate_s"] == 60  # 一番大きい幅(正解そのもの)


def test_salt_width_is_the_salt_compare_width_base(G):
    sc = G._salt_compare()
    tab = G.table(_records({30: 1.0}))
    st = sc.paired_stats(CALLS_REF, [c + 1.0 for c in CALLS_REF], alpha=0.05, family_size=1)
    m = next(r for r in tab["rows"] if r["width_s"] == 30)["metrics"]["calls"]
    assert m["salt_width"] == pytest.approx(st["width_base"]) and m["diff"] == pytest.approx(1.0)
    assert m["paired_width"] == pytest.approx(0.0, abs=1e-12)  # 対の差が全部同じ=対の差の幅は 0
    assert m["within"] is True  # 1.0 は salt 間の幅(約 2.5)の中


def test_a_large_difference_is_outside_and_not_a_candidate(G):
    tab = G.table(_records({60: 0.0, 30: 50.0, 10: 0.0}))
    rows = {r["width_s"]: r for r in tab["rows"]}
    assert rows[30]["metrics"]["calls"]["within"] is False
    assert tab["monotone"]["calls"] is False  # 60 → 30 で 0 → 50(増えた)→ 10 で 0
    assert tab["default_candidate_s"] == 60


def test_final_mismatch_blocks_the_candidate(G):
    tab = G.table(_records({}, final_moves={60}), ref_width=10)
    rows = {r["width_s"]: r for r in tab["rows"]}
    assert rows[60]["final_equal"] == 0.0 and rows[30]["final_equal"] == 1.0
    assert tab["default_candidate_s"] == 30


def test_bad_inputs_raise(G):
    with pytest.raises(ValueError, match="正解の幅"):
        G.table(_records({}), ref_width=5)
    recs = _records({})
    with pytest.raises(ValueError, match="2 つ"):
        G.table(recs + [dict(recs[0])])


def test_markdown_and_table_cli(G, tmp_path):
    p = tmp_path / "r.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in _records({30: 1.0})) + json.dumps(
        {"width_s": 5, "salt": 1, "error": "x"}) + "\n", encoding="utf-8")
    oj, om = tmp_path / "t.json", tmp_path / "t.md"
    assert G.main(["table", "--records", str(p), "--out-json", str(oj), "--out-md", str(om)]) == 0
    tab = json.loads(oj.read_text(encoding="utf-8"))
    assert [r["width_s"] for r in tab["rows"]] == [60, 30, 10]  # 誤りの行は落とす
    md = om.read_text(encoding="utf-8")
    assert "60(正解)" in md and "既定の幅の候補" in md and "(f) 単調" in md and "—" in md


def test_run_one_records_the_shape(G, tmp_path):
    kw = {"n_agents": 20, "world_dir": None, "n_cells": 9, "ticks": 30, "checkpoint_every": 10, "population_seed": 1}
    a = G.run_one(60, 1, kw=kw, src=ROOT / "src")
    b = G.run_one(10, 1, kw=kw, src=ROOT / "src")
    assert "error" not in a and "error" not in b, (a.get("error"), b.get("error"))
    assert (a["batching"]["width_s"], b["batching"]["width_s"]) == (60, 10)
    assert a["final"] == b["final"] and a["calls"] == b["calls"] and a["message_delay_max_s"] == 0.0
    assert b["batching"]["windows"] == 30 * 6
