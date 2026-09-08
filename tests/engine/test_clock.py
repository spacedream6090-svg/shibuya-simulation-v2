"""engine.clock のテスト(壁時計非依存・tick↔日時・δ_perc のナノ秒欄)。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from shibuya.core.types import NS_PER_SECOND
from shibuya.engine.clock import SimClock

START = datetime(2026, 9, 8, 5, 0, 0)


def test_tick_datetime_roundtrip():
    c = SimClock(START)
    assert c.to_datetime(0) == START
    assert c.to_datetime(90) == START + timedelta(minutes=90)
    assert c.to_tick(START + timedelta(minutes=90)) == 90
    assert c.to_tick(START + timedelta(minutes=90, seconds=59)) == 90, "tick 内の端数は切り下げ"
    assert c.to_tick_offset(START + timedelta(minutes=90, seconds=30)) == (90, 30 * NS_PER_SECOND)


def test_ticks_per_sim_day():
    assert SimClock(START).ticks_per_sim_day == 1_440
    assert SimClock(START, tick_seconds=30).ticks_per_sim_day == 2_880
    with pytest.raises(ValueError):
        SimClock(START, tick_seconds=7).ticks_per_sim_day


def test_t_sim_ns_uses_delta_perc_seconds():
    """δ_perc(0.2〜1.5秒)は世界時刻を進めず、tick 内ナノ秒欄になる(運用設計書 §2.3)。"""
    c = SimClock(START)
    assert c.t_sim_ns(3, 0.213) == 3 * 60 * NS_PER_SECOND + 213_000_000
    assert c.split(c.t_sim_ns(3, 0.213)) == (3, 213_000_000)
    with pytest.raises(ValueError):
        c.t_sim_ns(3, 61.0)


def test_ceil_tick_matches_t_apply_rule():
    """§2.4: t_apply=起床+δ_perc+δ_think を分tickへ**切り上げ**。"""
    c = SimClock(START)
    assert c.ceil_tick(c.t_sim_ns(3, 0.0)) == 3
    assert c.ceil_tick(c.t_sim_ns(3, 0.213)) == 4
    assert c.ceil_tick(c.t_sim_ns(3, 59.999)) == 4


def test_timezone_mismatch_is_rejected():
    c = SimClock(START)
    with pytest.raises(ValueError):
        c.to_tick(datetime(2026, 9, 8, 6, 0, tzinfo=timezone.utc))
    aware = SimClock(datetime(2026, 9, 8, 5, 0, tzinfo=timezone.utc))
    assert aware.to_tick(datetime(2026, 9, 8, 6, 0, tzinfo=timezone.utc)) == 60


def test_clock_is_hashable_and_frozen():
    c = SimClock(START)
    assert hash(c) == hash(SimClock(START))
    with pytest.raises(Exception):
        c.tick_seconds = 30  # type: ignore[misc]


def test_rejects_bad_arguments():
    with pytest.raises(TypeError):
        SimClock("2026-09-08")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        SimClock(START, tick_seconds=0)
