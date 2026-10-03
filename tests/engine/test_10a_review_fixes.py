"""10a の検収後の直し(`docs/bench/analysis/wallbounce-1003/review-10a.md`)の既知の答え。

- P1 開始日の検査は気象の再生実日へ置き換えた後の暦で走る(manifest の開始日と同じ日を見る)。
- P2 0:00 でない開始時刻は止める。
- P3 応答の遅れをテープの脇の meta に書き、再生で突き合わせる(違えば止める・値の無い旧テープは 2 とみなす)。
- P4 祝日 CSV の相対パスはリポの根から。読めないときは real で止め、day_index は md5・範囲を null。
- P5 給料日の前営業日への寄せが月をまたぐ分。
- T1 +2 の経路の既知の答え(HEAD の写しで取った final)。T2〜T6 は README の検収後の直しの表を参照。
"""

from __future__ import annotations

import os
import warnings
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

from shibuya.engine import run as RUN
from shibuya.engine.calendar import CalendarWarning, SimCalendar, load_holidays, resolve_repo_path
from shibuya.engine.energy import HomeMeals
from shibuya.engine.run import ResponseDelayWarning, run_day
from shibuya.engine.tape import RUN_META_FILENAME, read_run_meta
from shibuya.world.state import World

from tests.engine.test_calendar import write_csv
from tests.engine.test_tape_deferred import common
from tests.engine.test_tape_deferred import make_client as make_client_d58
from tests.engine.test_tape_wiring import BoomLLM
from tests.llm.test_fleet import FakeVLLM

TPD = 1_440


@pytest.fixture
def table(tmp_path):
    return load_holidays(write_csv(tmp_path / "h.csv"))


# ================================================================= P1
def test_start_check_runs_on_the_calendar_after_the_weather_date(monkeypatch):
    """世界過程が気象の再生実日を決めたら、検査はその日を見る(manifest の開始日と同じ日)。"""
    orig = RUN.WorldProcessRunner

    def runner(*a, **k):
        r = orig(*a, **k)
        r.environment.replay_date = "2026-07-22"   # 合成世界には気象の資産が無いので再生実日を差し込む
        return r

    monkeypatch.setattr(RUN, "WorldProcessRunner", runner)
    with pytest.warns(CalendarWarning, match="2026-07-22"):
        res = run_day(n_agents=10, n_cells=9, ticks=5, school_holidays="2026-07-21:2026-07-23")
    m = res.run_manifest_fields()
    assert m["start_sim_datetime"] == "2026-07-22T00:00:00"
    assert m["calendar"]["start_sim_datetime"] == "2026-07-22T00:00:00"
    assert any("2026-07-22" in w for w in m["calendar"]["start_check"])
    # 再生実日が区間の外なら警告は出ない(置き換える前の 2026-07-28 ではなく 07-22 を見ている)
    with warnings.catch_warnings():
        warnings.simplefilter("error", CalendarWarning)
        res = run_day(n_agents=10, n_cells=9, ticks=5, school_holidays="2026-07-27:2026-07-29")
    assert res.run_manifest_fields()["calendar"]["start_check"] == []


# ================================================================= P2
def test_start_must_be_midnight():
    with pytest.raises(ValueError, match="0:00"):
        SimCalendar(datetime(2026, 8, 3, 9, 0))
    with pytest.raises(ValueError, match="0:00"):
        SimCalendar(datetime(2026, 8, 3, 0, 0, 1))
    SimCalendar(datetime(2026, 8, 3))
    SimCalendar(datetime(2026, 8, 3, tzinfo=timezone(timedelta(hours=9))))
    with pytest.raises(ValueError, match="0:00"):
        run_day(n_agents=10, n_cells=9, ticks=5, start_sim_datetime="2026-08-03T09:00:00")


# ================================================================= P3
def _record(tmp_path, name, delay):
    servers = [FakeVLLM(), FakeVLLM()]
    try:
        for srv in servers:
            srv.total_delay_s = 0.02
        client = make_client_d58(servers, per_replica_in_flight=4, queue_capacity=8)
        return run_day(fleet=client, tape_path=tmp_path / name, fleet_wait_s=2.0, budget=30.0,
                       response_delay=delay, **common(20))
    finally:
        for s in servers:
            s.close()


def _replay(path, **kw):
    return run_day(mode="replay", replay=path, llm=BoomLLM(), budget=30.0, **common(20), **kw)


def test_the_tape_carries_the_response_delay_and_mismatches_stop(tmp_path):
    rec1 = _record(tmp_path, "d1", 1)
    rec2 = _record(tmp_path, "d2", 2)
    assert read_run_meta(tmp_path / "d1") == {"response_delay": 1}
    assert read_run_meta(tmp_path / "d2") == {"response_delay": 2}
    with pytest.raises(ValueError, match="テープは response_delay=1・今の設定は 2"):
        _replay(tmp_path / "d1", response_delay=2)
    with pytest.raises(ValueError, match="テープは response_delay=2・今の設定は 1"):
        _replay(tmp_path / "d2", response_delay=1)
    assert _replay(tmp_path / "d1").final_hash == rec1.final_hash          # 未指定=既定 1 で一致
    assert _replay(tmp_path / "d2", response_delay=2).final_hash == rec2.final_hash


def test_a_tape_without_the_value_is_replayed_as_2_with_one_warning(tmp_path):
    rec = _record(tmp_path, "old", 2)
    os.remove(tmp_path / "old" / RUN_META_FILENAME)            # 10a より前の録画と同じ形
    with pytest.warns(ResponseDelayWarning) as got:
        rep = _replay(tmp_path / "old")
    assert len([w for w in got if issubclass(w.category, ResponseDelayWarning)]) == 1
    assert rep.final_hash == rec.final_hash and rep.tape_miss_count == 0
    assert rep.run_manifest_fields()["response_delay"] == 2
    with warnings.catch_warnings():
        warnings.simplefilter("error", ResponseDelayWarning)
        _replay(tmp_path / "old")                              # 同じテープで 2 回目は警告しない
    with pytest.raises(ValueError, match="テープは response_delay=2・今の設定は 1"):
        _replay(tmp_path / "old", response_delay=1)


# ================================================================= P4
def test_relative_holiday_csv_is_resolved_from_the_repo_root(tmp_path, monkeypatch):
    p = resolve_repo_path("data/calendar/syukujitsu.csv")
    assert p.is_absolute() and p.parts[-3:] == ("data", "calendar", "syukujitsu.csv")
    assert (p.parent.parent.parent / "src" / "shibuya" / "engine" / "calendar.py").is_file()
    assert resolve_repo_path(tmp_path / "x.csv") == tmp_path / "x.csv"
    if p.is_file():                                            # 本物の CSV がある環境だけ
        monkeypatch.chdir(tmp_path)                            # 作業ディレクトリをリポの外へ
        assert load_holidays("data/calendar/syukujitsu.csv").loaded


def test_unreadable_csv_stops_real_and_nulls_the_manifest_in_day_index(tmp_path):
    missing = tmp_path / "none.csv"
    with pytest.raises(ValueError, match="祝日の表"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", CalendarWarning)
            run_day(n_agents=10, n_cells=9, ticks=5, calendar_weekday="real", holiday_csv=missing,
                    start_sim_datetime="2026-08-03")
    with warnings.catch_warnings(record=True) as got:
        warnings.simplefilter("always")
        res = run_day(n_agents=10, n_cells=9, ticks=5, holiday_csv=tmp_path / "none2.csv")
    assert any(issubclass(w.category, CalendarWarning) for w in got)
    cal = res.run_manifest_fields()["calendar"]
    assert cal["holiday_csv_md5"] is None and cal["holiday_csv_range"] is None
    with pytest.raises(ValueError, match="祝日の表"):    # 範囲外の開始日も、読めない時点で real は止まる
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", CalendarWarning)
            run_day(n_agents=10, n_cells=9, ticks=5, calendar_weekday="real", holiday_csv=missing,
                    start_sim_datetime="2030-01-07")


# ================================================================= P5
def test_payday_moved_back_across_the_month_boundary(table):
    c = SimCalendar(datetime(2026, 7, 1), weekday_mode="real", holidays=table, payday_day_of_month=1)
    got = [c.date_of_day(d) for d in range(123) if c.is_payday(d)]   # 2026-07-01〜10-31
    # 8/1(土)→ 7/31(金)。11/1(日)の分も前の営業日 10/30(金)へ寄るので 10 月の中に入る(検算の 4 日+1)。
    assert got == [date(2026, 7, 1), date(2026, 7, 31), date(2026, 9, 1), date(2026, 10, 1), date(2026, 10, 30)]
    assert [x for x in got if x <= date(2026, 10, 1)] == [
        date(2026, 7, 1), date(2026, 7, 31), date(2026, 9, 1), date(2026, 10, 1)]


# ================================================================= T1 +2 の経路の既知の答え
#: HEAD(3342b65・src は a08109a と同じ)の写しで取った final(偽 vLLM・pair_talk・合成世界 2 セル・
#: 200 体 × 600 tick・fleet_wait_s=10・stub・過程なし)。HEAD には切替口が無い=旧の +2。
HEAD_PLUS2_FINAL = "79821d778ea4addf"


def test_plus2_path_reproduces_the_head_final():
    from tests.engine.test_fleet_wiring import CONV_AGENTS, CONV_TICKS, _conv_world, make_client

    servers = [FakeVLLM(), FakeVLLM(), FakeVLLM()]
    try:
        for s in servers:
            s.pair_talk = True
        res = run_day(n_agents=CONV_AGENTS, seed=1, world=_conv_world(), ticks=CONV_TICKS,
                      fleet=make_client(servers), fleet_wait_s=10.0, renderer="stub", processes=False,
                      population=False, world_dir=None, response_delay=2)
    finally:
        for s in servers:
            s.close()
    assert res.conversation_sessions > 0
    assert res.final_hash[:16] == HEAD_PLUS2_FINAL


# ================================================================= T2〜T6
def test_datetime_uses_tick_seconds():
    c = SimCalendar(datetime(2026, 8, 3), tick_seconds=30)
    assert c.datetime_of(90) == datetime(2026, 8, 3, 0, 45)       # 90 × 30 秒(90 分ではない)
    assert c.datetime_of(c.to_T(1, 0)) == datetime(2026, 8, 4)


def test_real_day_key_is_the_day_number(table):
    c = SimCalendar(datetime(2026, 8, 3), weekday_mode="real", day_index=5, holidays=table)
    assert [c.day_key(d) for d in range(4)] == [0, 1, 2, 3]
    assert SimCalendar(datetime(2026, 8, 3), day_index=5).day_key(2) == 7


@pytest.mark.parametrize("start,rest", [("2026-08-08", True), ("2026-08-09", True), ("2026-08-11", True),
                                        ("2026-08-10", False)])
def test_real_mode_rest_day_reaches_the_mock_schedule(tmp_path, monkeypatch, start, rest):
    """real の土・日・祝日(8/11 山の日)の mock ランで、mock 日課へ暦の土休が渡る(平日の月曜は渡らない)。"""
    from shibuya.agents.schedule import MockWeeklySchedule

    seen = []
    orig = MockWeeklySchedule.events_of_day

    def spy(self, day_index=0, *, rest_day=None):
        seen.append(rest_day)
        return orig(self, day_index, rest_day=rest_day)

    monkeypatch.setattr(MockWeeklySchedule, "events_of_day", spy)
    # 土休の日は real の開始日の検査で止まるので、検査だけを空にして mock 日課へ渡る値を見る
    monkeypatch.setattr(SimCalendar, "check_start", lambda self, n=1: [])
    run_day(n_agents=10, n_cells=9, ticks=5, calendar_weekday="real", holiday_csv=write_csv(tmp_path / "h.csv"),
            start_sim_datetime=start)
    assert seen == [rest]


def test_home_meals_are_read_by_tick_of_day():
    class W:  # W17 の最小(1 体・月曜に自宅の食事 1 行)
        from shibuya.agents.weekly import ACTIVITY_WORDS, N_DAYS, PLACE_WORDS

        n_agents = 1
        day_offset = np.array([0, 1] + [1] * 6, dtype=np.int64)
        activity = np.array([ACTIVITY_WORDS.index("食事")], dtype=np.int64)
        place_kind = np.array([PLACE_WORDS.index("自宅")], dtype=np.int64)
        start_min = np.array([7 * 60], dtype=np.int64)

    hm = HomeMeals(1, TPD, W(), np.array([3]), day_index=0, tick_seconds=60)
    ts, cell, act = np.zeros(1, np.int8), np.array([3]), np.zeros(1, np.int8)
    a0, s0 = hm.due(7 * 60, ts, cell, act)
    a1, s1 = hm.due(TPD + 7 * 60, ts, cell, act)
    assert a0.tolist() == [0] and a1.tolist() == [0] and s0.tolist() == s1.tolist()
    assert hm.due(TPD + 7 * 60 + 1, ts, cell, act)[0].size == 0


def test_august_is_summer():
    c = SimCalendar(datetime(2026, 8, 1))
    assert all(c.season(d) == "夏" for d in range(31)) and c.season(31) == "秋"


def test_tape_meta_does_not_touch_the_parquet(tmp_path):
    from shibuya.engine.tape import Tape

    run_day(n_agents=30, n_cells=9, ticks=10, tape_path=tmp_path / "t", renderer="stub", sleep_suppression=False)
    t = Tape(tmp_path / "t")
    assert t.run_meta == {"response_delay": 1}
    assert "response_delay" not in t.calls.schema.names
    assert Path(tmp_path / "t" / RUN_META_FILENAME).read_bytes().endswith(b"\n")
