"""第 1 期 1-3 出来事の記録: 1 日の記録の行数と種類の分布を manifest に出す(口の約束 1-3 の約束 (3)・計器)。

- manifest の一番上の鍵は 1-3 で足していない(T0 の凍結の表 ``tests/engine/time/manifest_keys_frozen.json`` のまま)。
- 日次の記録(``daily`` の各行)の既存の欄の名と順は変えず、末尾に ``events`` を足した(鍵は
  ``manifest_events_keys_frozen.json`` に凍結)。``daily`` は節の表で観測(``manifest_sections``)=節の表は変えない。
- 中身の検算: ``rows``=``by_what`` の和=``by_cause`` の和=その日に書いた行の数・``bytes``=``rows × ROW_BYTES``。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shibuya.core.time_consts import STEPS_PER_DAY
from shibuya.engine import manifest_sections as MS
from shibuya.engine.events import log as EV
from shibuya.engine.run import run_day

HERE = Path(__file__).resolve().parent
FROZEN = json.loads((HERE / "manifest_events_keys_frozen.json").read_text(encoding="utf-8"))
TOP = json.loads((HERE.parent / "time" / "manifest_keys_frozen.json").read_text(encoding="utf-8"))["keys"]


@pytest.fixture(scope="module")
def two_days():
    return run_day(n_agents=60, seed=3, n_cells=9, ticks=STEPS_PER_DAY, sim_days=2, budget=60.0,
                   vocab_version="v3", checkpoint_every=240, processes=False, renderer="stub")


def test_top_level_keys_are_unchanged(two_days):
    assert list(two_days.run_manifest_fields()) == TOP


def test_daily_records_end_with_the_events_field(two_days):
    daily = two_days.run_manifest_fields()["daily"]
    assert len(daily) == 2
    for d in daily:
        keys = list(d)
        assert [k for k in keys if k in FROZEN["daily_keys_before_1_3"]] == FROZEN["daily_keys_before_1_3"]
        assert keys[-1] == "events"
        assert list(d["events"]) == FROZEN["events_keys"]
    assert MS.section_of("daily") == MS.OBSERVED and MS.section_of("daily.events") == MS.OBSERVED


def test_daily_counts_add_up(two_days):
    daily = two_days.run_manifest_fields()["daily"]
    log = two_days.event_log
    for d in daily:
        e = d["events"]
        assert e["on"] is True
        assert e["rows"] == sum(e["by_what"].values()) == sum(e["by_cause"].values()) > 0
        assert e["bytes"] == e["rows"] * EV.ROW_BYTES
        assert e["by_what"]["過程:day_close"] == 1
    assert sum(d["events"]["rows"] for d in daily) == log.n_appended == len(log)
    assert daily[-1]["events"]["live_rows"] == len(log) and daily[-1]["events"]["live_bytes"] == log.nbytes
