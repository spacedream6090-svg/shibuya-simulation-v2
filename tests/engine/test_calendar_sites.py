"""10a: 暦を引いていた箇所を暦の口(``engine.calendar.SimCalendar``)へ付け替えた結果の既知の答え。

- 既定(``day_index`` モード)では付け替えの前と同じ値を返す(材料 §2-2 の表の代表: 天気の層・営業時間の
  曜日の行・mock 日課・閉店中の店の翌日・出勤率・天気の実日の鍵・切替口の引数)。
- ``real`` モードでは実の曜日と祝日から引く(祝日=土休・曜日 7 日の表では日曜の行)。
- 日番号を足した鍵(◐ #18 天気の実日・◐ #19 出勤率)は 0 日目が今の鍵のまま・1 日目から変わる。
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.agents.schedule import synthesize
from shibuya.agents.state import AgentState
from shibuya.engine.calendar import SimCalendar, load_holidays
from shibuya.engine.presence import _mix64, attendance_draw
from shibuya.engine.processes import environment as ENV
from shibuya.engine.processes.runner import WorldProcessRunner
from shibuya.engine.run import (
    DEFAULT_RESPONSE_DELAY,
    _named_closed_lookup,
    add_calendar_args,
    add_fleet_args,
    calendar_kwargs_from_args,
)
from shibuya.world.state import World

from tests import _data_ids as D
from tests.engine.test_calendar import write_csv


@pytest.fixture
def table(tmp_path):
    return load_holidays(write_csv(tmp_path / "h.csv"))


def _real(start: datetime, table) -> SimCalendar:
    return SimCalendar(start, holidays=table)


# ================================================================= #3 天気の実日(◐ #18)
def test_weather_day_key_is_unchanged_on_day0_and_moves_from_day1():
    """〔改訂(第330・RET)〕前は legacy の実日の選び方 ``select_day``(0 日目の鍵=層名だけ・1 日目から日番号を足す)を見た
    (legacy と一緒に消した)。暦の規則の日ごとの鍵は ``test_weather_calendar_10e.py`` が見る。"""
    assert not hasattr(ENV, "select_day")


# ================================================================= #2・#7・#20 世界過程
def _runner(day_index=0, calendar=None):
    world = World.synthetic(n_cells=9, seed=1)
    agents = AgentState(20)
    agents.freeze()
    world.freeze()
    return WorldProcessRunner(world=world, agents=agents, seed=1, day_index=day_index, calendar=calendar,
                              schedule=synthesize(20, 1, world.n_cells))


@pytest.mark.parametrize("day_index", [0, 4, 5, 6, 9])
def test_runner_keeps_the_old_values_in_day_index_mode(day_index):
    """暦を渡さない実行器は ``SimCalendar.default(day_index)``(2026-07-13 + day_index 日・祝日の表なし)。曜日の行と土休は
    前と同じ値。〔改訂(第330・RET)〕日ごとの乱数の鍵は日番号(0)になった(前: day_index の暦の ``day_index``)。"""
    r = _runner(day_index)
    assert r.calendar.weekday(0) == day_index % 7
    assert r.opening.day_index == day_index % 7                       # #7 営業時間の曜日の行
    assert r.environment._weekday_kind() == ("土休" if day_index % 7 >= 5 else "平日")  # noqa: SLF001 #2
    assert r.salient.day_index == 0                                   # #20 日ごとの乱数の鍵=日番号
    assert r.dispatch is not None and r.large_event is not None


def test_runner_reads_the_real_calendar(table):
    cal = _real(datetime(2026, 7, 20), table)                         # 海の日(月曜)
    r = _runner(calendar=cal)
    assert r.environment._weekday_kind() == "土休"                    # noqa: SLF001 - 祝日は土休
    # 〔第330・10e E3〕祝日は W7 の祝日の行(PH)。PH の規則の無い店(今の W7 は全部)は日曜の行=今と同じ開閉
    from shibuya.engine.calendar import OPENING_ROW_PH
    from shibuya.engine.processes.opening import rows_of_day
    assert r.opening.day_index == OPENING_ROW_PH
    _pd = np.arange(8, dtype=np.int8)
    assert np.array_equal(rows_of_day(np.zeros(8), _pd, OPENING_ROW_PH, None), _pd == 6)   # 祝日は日曜の行
    assert r.salient.day_index == 0                                   # real の鍵は日番号
    r = _runner(calendar=_real(datetime(2026, 7, 21), table))         # 火曜
    assert r.environment._weekday_kind() == "平日" and r.opening.day_index == 1  # noqa: SLF001


# ================================================================= #12 mock 日課
def test_mock_schedule_takes_the_rest_day_from_the_calendar():
    sc = synthesize(30, 1, 9)
    assert np.array_equal(sc.boundary_ticks(0, rest_day=True), sc.boundary_ticks(5))
    assert np.array_equal(sc.boundary_ticks(5, rest_day=False), sc.boundary_ticks(0))
    for d in range(7):  # rest_day を渡さなければ今の式
        assert np.array_equal(sc.boundary_ticks(d), sc.weekend_ticks if d >= 5 else sc.base_ticks)
    a0 = sc.events_of_day(0, rest_day=True)
    a5 = sc.events_of_day(5)
    assert all(np.array_equal(x, y) for x, y in zip(a0, a5))
    assert np.array_equal(sc.target_cell(0, rest_day=True), sc.leisure_cell)


# ================================================================= #8 閉店中の店の翌日
def _lookup(calendar, fail_tick):
    om = np.zeros((2, 1_440), dtype=bool)                  # POI 0 は当日ずっと閉まっている
    pa = SimpleNamespace(plan_poi=np.array([0, 0, 0, 0]), plan_day=np.array([0, 1, 2, 6]),
                         plan_start=np.array([540, 600, 660, 720]))
    runner = SimpleNamespace(opening=SimpleNamespace(open_matrix=om, assets=pa))
    resolver = SimpleNamespace(named_closed={7: (0, fail_tick)})
    return _named_closed_lookup(resolver, runner, calendar, 60)(7)


def test_named_closed_next_day_comes_from_the_calendar(table):
    # 〔改訂(第330・RET)〕旧い口 SimCalendar.legacy は SimCalendar.default(2026-07-13 + 日数・real)に替えた
    base = SimCalendar.default(0)
    assert _lookup(base, 100) == (0, 100, 600)                       # 月曜の翌日=火曜(今と同じ)
    assert _lookup(base, 1_440 + 100) == (0, 1_540, 660)             # 2 日目(火)の翌日=水曜
    assert _lookup(SimCalendar.default(5), 100) == (0, 100, 720)     # 土曜の翌日=日曜
    # real: 7/19(日)の翌日 7/20 は海の日=日曜の行
    assert _lookup(_real(datetime(2026, 7, 19), table), 100) == (0, 100, 720)
    assert _lookup(_real(datetime(2026, 7, 20), table), 100) == (0, 100, 600)   # 翌日 7/21 は火曜


# ================================================================= ◐ #19 出勤率
def test_attendance_draw_keeps_day0_and_moves_from_day1():
    a = np.arange(5_000, dtype=np.int64)
    old = (_mix64(a.astype(np.uint64)) % np.uint64(10_000)).astype(np.int64)
    assert np.array_equal(attendance_draw(a, day=0, seed=1), old)
    assert np.array_equal(attendance_draw(a, day=0, seed=99), old)          # 0 日目は seed に依らない(今のまま)
    d1 = attendance_draw(a, day=1, seed=1)
    assert np.mean(d1 != old) > 0.99
    assert np.mean(attendance_draw(a, day=1, seed=2) != d1) > 0.99         # 1 日目からは seed で変わる
    assert np.mean(attendance_draw(a, day=2, seed=1) != d1) > 0.99
    assert (d1 >= 0).all() and (d1 < 10_000).all()


# ================================================================= 切替口の引数
def test_cli_switches_and_defaults():
    ap = argparse.ArgumentParser()
    add_fleet_args(ap)
    add_calendar_args(ap)
    args = ap.parse_args([])
    kw = calendar_kwargs_from_args(args)
    # 〔改訂(第330・RET)〕calendar_weekday と rng_scheme の欄は切替口と一緒に消した(ACT: None・None)
    assert kw == {"start_sim_datetime": None,
                  "holiday_csv": "data/calendar/syukujitsu.csv", "school_holidays": "",
                  "response_delay": None}     # 未指定(録画・mock は 1・再生はテープに合わせる=検収後 P3)
    assert DEFAULT_RESPONSE_DELAY == 1
    args = ap.parse_args(["--start-date", "2026-08-03", "--response-delay", "2",
                          "--school-holidays", "2026-07-21:2026-08-31"])
    kw = calendar_kwargs_from_args(args)
    assert kw["start_sim_datetime"] == "2026-08-03"
    assert kw["response_delay"] == 2 and kw["school_holidays"] == "2026-07-21:2026-08-31"
    with pytest.raises(SystemExit):
        ap.parse_args(["--response-delay", "3"])
    with pytest.raises(SystemExit):
        ap.parse_args(["--calendar-weekday", "real"])  # 〔第330・RET〕切替口を消した


def test_cli_main_accepts_the_switches():
    from shibuya import cli

    ap_args = ["--agents", "20", "--world", "no-such-world", "--cells", "9", "--ticks", "5",
               "--start-date", "2026-07-13", "--response-delay", "2"]  # 〔第330・RET〕--calendar-weekday を消した
    assert cli.main(ap_args) in (0, 1)


# ================================================================= #10 鉄道(実の資産があるときだけ)
@pytest.mark.requires_data("world_v2")
def test_rail_timetable_kind_comes_from_the_calendar(table):
    from shibuya.engine.processes.rail import RailProcess
    from shibuya.world.assets import load_process_assets_or_synthetic

    world = World.load_or_synthetic(Path("data/world/v2"), n_cells=139, seed=1)
    pa = load_process_assets_or_synthetic("data/world/v2", world.assets)
    D.skip_unless("timetables", have=pa.has_timetable)
    agents = AgentState(10)

    def n_trains(**kw):
        return int(RailProcess(world, agents, pa, plan_executor=True, **kw).dep_tick.size)

    cal = np.asarray(pa.tt_calendar)
    keep = np.asarray(pa.line_platform_cell)[np.asarray(pa.tt_line_idx)] >= 0
    weekday_n, rest_n = int(((cal == 0) & keep).sum()), int(((cal == 1) & keep).sum())
    assert n_trains(day_index=0) == weekday_n and n_trains(day_index=5) == rest_n      # 今と同じ
    assert n_trains(calendar=_real(datetime(2026, 7, 20), table)) == rest_n            # 祝日=土休ダイヤ
    assert n_trains(calendar=_real(datetime(2026, 7, 21), table)) == weekday_n
