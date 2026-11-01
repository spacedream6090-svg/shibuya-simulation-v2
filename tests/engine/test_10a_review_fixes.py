"""10a の検収後の直し(`docs/bench/analysis/wallbounce-1003/review-10a.md`)の既知の答え。

- P1 開始日の検査は気象の再生実日へ置き換えた後の暦で走る(manifest の開始日と同じ日を見る)。
- P2 0:00 でない開始時刻は止める。
- P3 応答の遅れをテープの脇の meta に書き、再生で突き合わせる(違えば止める・値の無い旧テープは 2 とみなす)。
- P4 祝日 CSV の相対パスはリポの根から。読めないときは止める(〔第330・RET〕day_index の null の扱いは消した)。
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
from shibuya.engine.systems import build as BLD  # 1-0: 層の組み立ての名前の差し替えの的
from shibuya.engine.calendar import CalendarWarning, SimCalendar, load_holidays, resolve_repo_path
from shibuya.engine.energy import HomeMeals
from shibuya.engine.run import run_day
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
    """開始日の検査は manifest の開始日(暦)と同じ日を見る。

    〔改訂(第330・RET)〕前は legacy の規則(世界の日付=気象の再生実日 2026-07-22 に置き換えた後の暦で検査・day_index の
    違反は警告だけ)を見た(ACT の commit で day_index・legacy を渡して通った)。legacy と day_index を消したので、世界の
    日付は暦のまま(再生日を差し込んでも動かない)・学校の休みに当たれば止める、を見る。"""
    orig = BLD.WorldProcessRunner  # 1-0: 組み立ては engine.systems.build
    made: list[object] = []

    def runner(*a, **k):
        r = orig(*a, **k)
        made.append(r)
        r.environment.replay_date = "2026-07-22"   # 再生日を差し込んでも世界の日付は暦のまま
        return r

    monkeypatch.setattr(BLD, "WorldProcessRunner", runner)
    with pytest.raises(ValueError, match="学校の長期休み"):
        run_day(n_agents=10, n_cells=9, ticks=5, school_holidays="2026-07-12:2026-07-14")
    res = run_day(n_agents=10, n_cells=9, ticks=5, school_holidays="2026-07-21:2026-07-23")
    m = res.run_manifest_fields()
    assert m["start_sim_datetime"] == m["calendar"]["start_sim_datetime"] == "2026-07-13T00:00:00"
    assert m["calendar"]["start_check"] == []
    assert made, "WorldProcessRunner の差し替えが使われていない"


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
def _record(tmp_path, name):
    servers = [FakeVLLM(), FakeVLLM()]
    try:
        for srv in servers:
            srv.total_delay_s = 0.02
        client = make_client_d58(servers, per_replica_in_flight=4, queue_capacity=8)
        return run_day(fleet=client, tape_path=tmp_path / name, fleet_wait_s=2.0, budget=30.0, **common(20))
    finally:
        for s in servers:
            s.close()


def _meta_wo_env(meta):
    """テープの脇の meta から 10f の環境の欄(``env_id``・``environment``)を除いた写し。"""
    return {k: v for k, v in meta.items() if k not in ("env_id", "environment")}


def _replay(path, **kw):
    return run_day(mode="replay", replay=path, llm=BoomLLM(), budget=30.0, **common(20), **kw)


def test_the_tape_carries_the_response_delay_and_old_tapes_stop(tmp_path):
    """テープの脇の meta に応答の遅れ(1)を書く・〔第 4 期 4-3 版上げ 3 回目の第 2 部〕+2(旧)の切替口は消した=値 2 の
    テープ・値の無いテープ(10a より前)は再生しない(前は 2 で録って 2 で再生でき、値が無ければ 2 とみなして警告した)。"""
    import json

    rec1 = _record(tmp_path, "d1")
    # 10f: 環境の欄(env_id・environment)も書く=それを除いた形は今までと同じ
    # 10e(E4): 乱数の既定は counter
    # 〔改訂(第330・ACT)〕暦の規則(calendar_weekday・weather_scheme)も書く(親の決定 (5)・再生の既定)
    cal = {"calendar_weekday": "real", "weather_scheme": "calendar"}
    assert _meta_wo_env(read_run_meta(tmp_path / "d1")) == {"response_delay": 1, "rng_scheme": "counter", "rng_layout": "10e", **cal}
    assert _replay(tmp_path / "d1").final_hash == rec1.final_hash
    with pytest.raises(TypeError):
        _replay(tmp_path / "d1", response_delay=2)
    mp = tmp_path / "d1" / RUN_META_FILENAME
    d = json.loads(mp.read_text(encoding="utf-8"))
    mp.write_text(json.dumps({**d, "response_delay": 2}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="テープは response_delay=2"):
        _replay(tmp_path / "d1")
    d.pop("response_delay")
    mp.write_text(json.dumps(d) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="テープは response_delay=None"):
        _replay(tmp_path / "d1")
    os.remove(mp)                                              # meta の無いテープ=10e より前の録画は止める
    with pytest.raises(ValueError, match="10e より前"):
        _replay(tmp_path / "d1")


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
    """〔改訂(第330・RET)〕前は「day_index では止めず manifest の md5・範囲を null」も見た(day_index を消した)。暦は real
    だけなので、読めない CSV は開始日を渡しても渡さなくても止まる。"""
    missing = tmp_path / "none.csv"
    for start in ("2026-08-03", None, "2030-01-07"):
        with pytest.raises(ValueError, match="祝日の表"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", CalendarWarning)
                run_day(n_agents=10, n_cells=9, ticks=5, holiday_csv=missing, start_sim_datetime=start)


# ================================================================= P5
def test_payday_moved_back_across_the_month_boundary(table):
    c = SimCalendar(datetime(2026, 7, 1), holidays=table, payday_day_of_month=1)
    got = [c.date_of_day(d) for d in range(123) if c.is_payday(d)]   # 2026-07-01〜10-31
    # 8/1(土)→ 7/31(金)。11/1(日)の分も前の営業日 10/30(金)へ寄るので 10 月の中に入る(検算の 4 日+1)。
    assert got == [date(2026, 7, 1), date(2026, 7, 31), date(2026, 9, 1), date(2026, 10, 1), date(2026, 10, 30)]
    assert [x for x in got if x <= date(2026, 10, 1)] == [
        date(2026, 7, 1), date(2026, 7, 31), date(2026, 9, 1), date(2026, 10, 1)]


# ================================================================= T1 +2 の経路(〔第 2 部〕消した)
def test_plus2_path_is_gone():
    """〔第 2 部〕+2(旧)の道(受け取りの位置 B)は消した=``run_day(response_delay=2)`` は止まる(前は HEAD の final
    ``HEAD_PLUS2_FINAL`` を再現した)。"""
    with pytest.raises(TypeError):
        run_day(n_agents=4, ticks=2, renderer="stub", processes=False, population=False, world_dir=None,
                response_delay=2)


# ================================================================= T2〜T6
def test_datetime_uses_tick_seconds():
    c = SimCalendar(datetime(2026, 8, 3), tick_seconds=30)
    assert c.datetime_of(90) == datetime(2026, 8, 3, 0, 45)       # 90 × 30 秒(90 分ではない)
    assert c.datetime_of(c.to_T(1, 0)) == datetime(2026, 8, 4)


def test_real_day_key_is_the_day_number(table):
    c = SimCalendar(datetime(2026, 8, 3), day_index=5, holidays=table)
    assert [c.day_key(d) for d in range(4)] == [0, 1, 2, 3]
    # 〔改訂(第330・RET)〕day_index の暦(鍵 = day_index + 日 = 7)は消した。暦は real だけ=日番号
    assert SimCalendar(datetime(2026, 8, 3), day_index=5).day_key(2) == 2


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
    run_day(n_agents=10, n_cells=9, ticks=5, holiday_csv=write_csv(tmp_path / "h.csv"),
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
    assert _meta_wo_env(t.run_meta) == {"response_delay": 1, "rng_scheme": "counter", "rng_layout": "10e",  # 10c: 乱数の方式も書く(10e: 既定 counter)
                                        "calendar_weekday": "real", "weather_scheme": "calendar"}  # 〔第330・ACT〕暦の規則
    assert set(t.run_meta) == {"response_delay", "rng_scheme", "rng_layout", "env_id", "environment",  # 10f: 環境の欄・10e: 鍵の配置の印
                               "calendar_weekday", "weather_scheme"}  # 〔改訂(第330・ACT)〕暦の規則の 2 欄
    assert "response_delay" not in t.calls.schema.names
    assert Path(tmp_path / "t" / RUN_META_FILENAME).read_bytes().endswith(b"\n")
