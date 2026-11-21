# -*- coding: utf-8 -*-
"""tools/bench/event_cost/event_cost.py(指示書 11-03 §6-1・事象 1 件あたりの固定費)の小さな試験。

- 1,000 件・小さな列と配列で全部の測り(1)〜(5)が動き、JSON の形がそろう。
- 係数(ns/事象)が正。
- 1 日の見積りの和が、役 sum の行だけを足した値になる(合成の event_table)。
- Markdown の表が出る。
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_PATH = ROOT / "tools" / "bench" / "event_cost" / "event_cost.py"


@pytest.fixture(scope="module")
def E():
    name = "event_cost_bench_mod"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _PATH)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def fake_table(tmp_path_factory):
    p = tmp_path_factory.mktemp("et") / "event_table.json"
    p.write_text(json.dumps({"N": 1000, "rows": {
        "llm_calls_mock_x69": {"total": 100},
        "llm_calls_scheduled_planclass_mock_x69": {"total": 60},   # 内訳=和に入れない
        "intents_mock_x69": {"total": 500},                         # 参考=和に入れない
        "walker_steps_x69": {"total": 700},                         # 参考(接頭辞)
        "purchases_mock_x69": {"total": 40},
    }}), encoding="utf-8")
    return p


@pytest.fixture(scope="module")
def doc(E, fake_table, tmp_path_factory):
    d = tmp_path_factory.mktemp("out")
    out, md = d / "ec.json", d / "ec.md"
    rc = E.main(["--counts", "1000", "--repeats", "1", "--heap-size", "2000", "--agents", "1000",
                 "--argmin-max", "1000", "--windows", "20", "--heap-sweep", "500,2000",
                 "--event-table", str(fake_table), "--out", str(out), "--md", str(md), "--quiet"])
    assert rc == 0
    return json.loads(out.read_text(encoding="utf-8")), md.read_text(encoding="utf-8")


def test_shape(doc):
    d, _md = doc
    for k in ("tool", "machine", "params", "results", "summary", "wall_s"):
        assert k in d
    m = d["machine"]
    for k in ("cpu", "ram_gb", "os", "python", "numpy"):
        assert k in m
    r = d["results"]
    assert set(r["heap"]["1000"]) == {"ns_grain", "sec_grain"}
    assert set(r["dispatch"]["1000"]) == {"5", "10"}
    assert set(r["batch"]["1000"]) == {"1", "16", "256"}
    assert set(r["round"]["1000"]) == {"scalar_k1", "single_k1", "single_k16", "single_k256",
                                       "mixed_k16", "mixed_k256"}
    assert "1000" in r["argmin"]
    assert set(r["heap_size_sweep"]) == {"500", "2000"}
    assert r["heap"]["1000"]["ns_grain"]["repeats"] == 1
    assert len(r["heap"]["1000"]["ns_grain"]["runs"]) == 1
    # 列の大きさは hold の形で一定に保たれる
    assert r["heap"]["1000"]["ns_grain"]["runs"][0]["heap_len_end"] == 2000
    assert r["round"]["1000"]["mixed_k16"]["runs"][0]["heap_len_end"] == 2000


def test_coefficients_positive(doc):
    d, _md = doc
    r = d["results"]
    for g in ("ns_grain", "sec_grain"):
        m = r["heap"]["1000"][g]["median"]
        assert m["pop_gross"] > 0 and m["push_gross"] > 0 and m["pair_gross"] > 0
    for kd in ("5", "10"):
        m = r["dispatch"]["1000"][kd]["median"]
        assert m["dict_gross"] > 0 and m["loop_base"] > 0
    for k in ("1", "16", "256"):
        assert r["batch"]["1000"][k]["median"]["per_event"] > 0
        assert r["batch"]["1000"][k]["median"]["per_batch"] > 0
    for v in r["round"]["1000"].values():
        assert v["median"]["per_event"] > 0
    assert r["argmin"]["1000"]["median"]["per_event"] > 0
    assert r["window_scan"]["median"]["per_window"] > 0
    for v in d["summary"]["coefs_ns_per_event"].values():
        assert isinstance(v, float)


def test_day_estimate_sum_only_sum_rows(doc):
    d, _md = doc
    de = d["summary"]["day_estimate"]
    assert de["sum_events"] == 140
    assert de["rows"]["llm_calls_scheduled_planclass_mock_x69"]["role"] == "breakdown"
    assert de["rows"]["intents_mock_x69"]["role"] == "reference"
    assert de["rows"]["walker_steps_x69"]["role"] == "reference"
    c = d["summary"]["coefs_ns_per_event"]["round_scalar_k1"]
    assert de["sum_seconds"]["round_scalar_k1"] == pytest.approx(140 * c / 1e9)
    assert de["step_floor_seconds_per_day"]["1 秒の刻み(86,400)"] == pytest.approx(172.8)


def test_markdown(doc):
    _d, md = doc
    assert "表 1 係数" in md and "表 1b" in md and "表 2" in md
    assert "1,000 件" in md


def test_bad_args(E):
    with pytest.raises(SystemExit):
        E.main(["--counts", "0", "--quiet"])
