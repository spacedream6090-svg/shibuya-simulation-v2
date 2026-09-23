"""鉄道運行(D-R2-5 第1陣 3 行目)+ 乗車/降車(行動契約書 §2.1・運用設計書 §2.6)のテスト。"""

from __future__ import annotations

import numpy as np
import pyarrow.parquet as pq
import pytest

from shibuya.agents.state import Activity, ResultCode
from shibuya.economy.accounts import AccountCode
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.processes.rail import (
    ACCEPT_FULL_RATIO,
    ACCEPT_MAX_RATIO,
    ACCEPT_MIN_RATE,
    ACCOUNT_CODE_CARRY_OUT,
    DWELL_TICKS,
    DWELL_TICKS_BY_LINE,
    DWELL_TICKS_TERMINAL,
    LINE_CAPACITY_PERSONS,
    LINE_CONGESTION_CAP_PCT,
    MAX_DWELL_TICKS,
    RailProcess,
)
from shibuya.world.assets import load_process_assets

from .conftest import WORLD_DIR, fake_timetable_assets, make_agents, make_world, real_data


def _rail(
    n_agents: int = 20,
    *,
    departures=(100, 200, 300),
    platform_cell: int = 0,
    lines: tuple[str, ...] = ("山手線", "井の頭線"),
):
    world = make_world(9)
    agents, schedule = make_agents(world, n_agents)
    pa = fake_timetable_assets(
        platform_cell=platform_cell, departures=departures, lines=lines
    )
    rail = RailProcess(world, agents, pa, master_seed=1, day_index=0, schedule=schedule)
    return world, agents, rail


def _intents(agent_ids, code):
    a = np.asarray(agent_ids, dtype=np.int64)
    return C.IntentBatch(
        agent_id=a,
        action_code=np.full(a.size, code, dtype=np.int8),
        target_id=np.full(a.size, -1, dtype=np.int32),
        resource_id=np.full(a.size, -1, dtype=np.int32),
        t_notice_ns=np.zeros(a.size, dtype=np.int64),
    )


def _put_on_platform(agents, world, ids, cell: int) -> None:
    """個体をホームのセルへ置く(``resolve`` の口を通す)。"""
    R.rail_arrive(agents, world, np.asarray(ids, dtype=np.int64),
                  np.full(len(ids), cell, dtype=np.int64))


# ================================================================= 科目番号の一致(engine ↔ economy)
def test_carry_out_account_code_matches_economy():
    """``engine`` は科目名を知らない=**番号だけ**を持つ。値の一致はここで強制する。"""
    assert ACCOUNT_CODE_CARRY_OUT == int(AccountCode.CARRY_OUT)


# ================================================================= ダイヤの展開
def test_trains_per_line_matches_the_timetable_rows():
    _, _, rail = _rail(departures=(100, 200, 300))
    assert rail.trains_per_line() == {"山手線": 3, "井の頭線": 3}
    assert rail.dep_tick.size == 6


def test_dep_ticks_are_sorted_for_the_searchsorted_window():
    _, _, rail = _rail()
    assert np.all(np.diff(rail.dep_tick) >= 0)


def test_trains_at_platform_covers_the_dwell_window():
    _, _, rail = _rail(departures=(100,))
    dep = int(rail.dep_tick[0])
    assert 0 not in rail.trains_at_platform(dep - DWELL_TICKS).tolist()
    assert 0 in rail.trains_at_platform(dep - DWELL_TICKS + 1).tolist()
    assert 0 in rail.trains_at_platform(dep).tolist()
    assert 0 not in rail.trains_at_platform(dep + 1).tolist()


def test_dwell_is_a_per_line_table_terminal_is_two_ticks():
    """D-51 (c): 通過型 1 tick(60 秒)・終端(銀座線・井の頭線)2 tick。"""
    assert DWELL_TICKS == 1 and DWELL_TICKS_TERMINAL == 2 and MAX_DWELL_TICKS == 2
    assert DWELL_TICKS_BY_LINE == {"銀座線": 2, "井の頭線": 2}
    _, _, rail = _rail(departures=(100,))
    # 便 0 = 山手線(dep 100・通過型)/ 便 1 = 井の頭線(dep 101・終端)
    assert rail.dwell.tolist() == [1, 2]
    assert rail.dwell_of_line("銀座線") == 2
    assert rail.dwell_of_line("山手線") == 1
    assert rail.trains_at_platform(99).tolist() == []
    assert rail.trains_at_platform(100).tolist() == [0, 1]  # 井の頭は発車の 1 tick 前から在線
    assert rail.trains_at_platform(101).tolist() == [1]
    assert rail.trains_at_platform(102).tolist() == []
    assert rail.is_at_platform([0, 1], 100).tolist() == [True, True]
    assert rail.is_at_platform([0, 1], 101).tolist() == [False, True]


@real_data
def test_daily_train_count_matches_the_real_timetable_rows_for_that_calendar():
    """ゲート: 路線別の便数が W12 のその暦の行数と一致する。"""
    world = make_world(9)
    from shibuya.world.state import World

    real = World.load(WORLD_DIR)
    agents, schedule = make_agents(real, 30)
    pa = load_process_assets(WORLD_DIR, real.assets)
    rail = RailProcess(real, agents, pa, master_seed=1, day_index=0, schedule=schedule)
    t = pq.read_table(WORLD_DIR / "w12_timetables.parquet", columns=["line", "calendar"]).to_pydict()
    want: dict[str, int] = {}
    for line, cal in zip(t["line"], t["calendar"]):
        if str(cal) == "Weekday":
            want[str(line)] = want.get(str(line), 0) + 1
    got = rail.trains_per_line()
    # **双方向**: 平日ダイヤの全路線がちょうど期待本数で現れ、余分な路線も出ない。
    assert set(got) == set(want), (sorted(set(got) ^ set(want)),)
    assert got == want, {k: (got.get(k), want.get(k)) for k in set(got) | set(want)
                         if got.get(k) != want.get(k)}
    assert sum(got.values()) == sum(want.values()) > 3_000
    assert world.n_cells == 9  # フィクスチャの自己検査


# ================================================================= §2.6 受容関数
def test_accept_rate_matches_the_run_manifest_section_2_6():
    _, _, rail = _rail()
    assert rail.accept_rate(0.5) == 1.0
    assert rail.accept_rate(ACCEPT_FULL_RATIO) == 1.0
    # 200% ちょうどは**実効容量に到達**=乗り残し(§2.6「実効容量=定員×2.0」)。
    # 直下は線形の下端 0.7 に漸近する。
    assert rail.accept_rate(ACCEPT_MAX_RATIO - 1e-9) == pytest.approx(ACCEPT_MIN_RATE)
    assert rail.accept_rate(ACCEPT_MAX_RATIO) == 0.0
    assert rail.accept_rate(ACCEPT_MAX_RATIO + 0.01) == 0.0
    mid = rail.accept_rate((ACCEPT_FULL_RATIO + ACCEPT_MAX_RATIO) / 2)
    assert ACCEPT_MIN_RATE < mid < 1.0


def test_accept_quota_is_capped_by_two_hundred_percent():
    _, _, rail = _rail()
    rail.capacity100[0] = 10.0
    rail.occupancy[0] = 0
    assert rail.accept_quota(0, 5) == 5
    rail.occupancy[0] = 19  # 190% → 受容率は 1.0 と 0.7 の間
    q = rail.accept_quota(0, 10)
    assert 0 < q <= 1  # ハード上限 200% = 20 人 → 残り 1 席
    rail.occupancy[0] = 20  # 200%
    assert rail.accept_quota(0, 10) == 0


def test_left_behind_is_counted_as_a_diagnostic_row():
    """§2.6 (iii) 乗り残しの診断行(``left_behind`` / ``left_behind_rate``)。"""
    _, _, rail = _rail()
    assert rail.counters()["left_behind"] == 0.0
    assert rail.counters()["left_behind_rate"] == 0.0
    rail.capacity100[0] = 10.0
    rail.occupancy[0] = 0
    assert rail.accept_quota(0, 5) == 5  # 全員乗れる
    assert rail.n_left_behind == 0 and rail.n_board_applicants == 5
    rail.occupancy[0] = 20  # 200% = 実効容量ちょうど → 10 人まるごと乗り残し
    assert rail.accept_quota(0, 10) == 0
    assert rail.n_left_behind == 10 and rail.n_board_applicants == 15
    c = rail.counters()
    assert c["left_behind"] == 10.0
    assert c["board_applicants"] == 15.0
    assert c["left_behind_rate"] == pytest.approx(10 / 15)
    assert "乗り残し 10" in rail.summary()


def test_congestion_caps_are_the_official_values():
    """線別混雑率上限(D10′ の照合対象)。**D-51 で 5 行を令和7年度(2025)実績へ更新**。"""
    # 令和6年度のまま据え置く 3 行(2025 値が**親未確認**)
    assert LINE_CONGESTION_CAP_PCT["山手線"] == 139.0
    assert LINE_CONGESTION_CAP_PCT["埼京線"] == 163.0
    assert LINE_CONGESTION_CAP_PCT["銀座線"] == 147.0
    # 令和7年度(2025)実績へ更新した 5 行(答申 §3-1 行 8・親一次確認)
    assert LINE_CONGESTION_CAP_PCT["田園都市線"] == 138.0
    assert LINE_CONGESTION_CAP_PCT["東横線"] == 124.0
    assert LINE_CONGESTION_CAP_PCT["半蔵門線"] == 111.0
    assert LINE_CONGESTION_CAP_PCT["副都心線"] == 117.0
    assert LINE_CONGESTION_CAP_PCT["井の頭線"] == 125.0
    assert LINE_CAPACITY_PERSONS["山手線"] == 26_032 // 16  # 輸送力 ÷ 本数
    assert LINE_CAPACITY_PERSONS["田園都市線"] == round(40_338 / 27)


# ================================================================= 乗車・降車(契約書 §2.1)
def test_boarding_succeeds_on_the_platform_and_pays_the_fare():
    world, agents, rail = _rail(departures=(100,))
    dep = int(rail.dep_tick[0])
    ids = np.arange(3, dtype=np.int64)
    _put_on_platform(agents, world, ids, 0)
    money0 = agents.money[ids].copy()
    out = R.apply(_intents(ids, C.ACT_BOARD), C.IntentBatch.empty(), agents, world, dep, rail=rail)
    assert out.n_boarded == 3
    assert np.all(agents.registry.transit_state[ids] == 1)
    assert np.all(agents.activity[ids] == int(Activity.RIDING))
    assert np.all(agents.money[ids] == money0 - rail.fare_yen)
    assert out.fare_paid == 3 * rail.fare_yen
    assert int(rail.occupancy[0]) == 3


def test_boarding_without_a_train_waits_on_the_platform():
    """**D-51 (a)**: 列車が居なくても失敗にせず、ホームで待つ(意図が消えない)。"""
    world, agents, rail = _rail(departures=(100,))
    ids = np.arange(2, dtype=np.int64)
    _put_on_platform(agents, world, ids, 0)
    out = R.apply(_intents(ids, C.ACT_BOARD), C.IntentBatch.empty(), agents, world, 5, rail=rail)
    assert np.all(agents.last_result[ids] == int(ResultCode.OK))
    assert np.all(agents.activity[ids] == int(Activity.WAITING))
    assert np.all(agents.registry.board_line[ids] >= 0)
    assert np.all(agents.registry.board_since[ids] == 5)
    assert np.all(agents.registry.transit_state[ids] == 0)  # 待ちは在圏(3 値を増やさない)
    assert out.n_board_waiting == 2 and rail.n_board_waiting == 2


def test_boarding_in_another_cell_walks_to_the_nearest_platform():
    """**D-51 (b)**: ホーム以外で乗車を選ぶと、世界が最寄りホームへの移動を組む。"""
    world, agents, rail = _rail(departures=(100,), platform_cell=0)
    dep = int(rail.dep_tick[0])
    ids = np.arange(2, dtype=np.int64)
    _put_on_platform(agents, world, ids, 3)  # ホームでないセル
    R.apply(_intents(ids, C.ACT_BOARD), C.IntentBatch.empty(), agents, world, dep, rail=rail)
    assert np.all(agents.last_result[ids] == int(ResultCode.OK))
    assert np.all(agents.activity[ids] == int(Activity.MOVING))
    assert np.all(agents.target_node[ids] == world.assets.cell_rep_node[0])
    assert np.all(agents.registry.board_line[ids] >= 0)
    assert np.all(agents.registry.board_since[ids] == -1)  # まだ立っていない=待ち時間 0
    assert rail.n_board_walking == 2


def test_boarding_without_the_fare_returns_fare_short():
    world, agents, rail = _rail(departures=(100,))
    dep = int(rail.dep_tick[0])
    ids = np.arange(2, dtype=np.int64)
    _put_on_platform(agents, world, ids, 0)
    rail.fare_yen = 10**9
    R.apply(_intents(ids, C.ACT_BOARD), C.IntentBatch.empty(), agents, world, dep, rail=rail)
    assert np.all(agents.last_result[ids] == int(ResultCode.FARE_SHORT))
    assert np.all(agents.registry.transit_state[ids] == 0)


def test_boarding_over_the_congestion_cap_returns_train_full():
    world, agents, rail = _rail(n_agents=30, departures=(100,))
    dep = int(rail.dep_tick[0])
    ids = np.arange(10, dtype=np.int64)
    _put_on_platform(agents, world, ids, 0)
    rail.capacity100[:] = 2.0
    rail.occupancy[0] = 4  # = 200% → 乗り残し
    out = R.apply(_intents(ids, C.ACT_BOARD), C.IntentBatch.empty(), agents, world, dep, rail=rail)
    assert out.n_boarded == 0
    assert np.all(agents.last_result[ids] == int(ResultCode.TRAIN_FULL))


def test_alight_succeeds_only_while_the_train_is_at_the_platform():
    # 終端(井の頭線・dwell 2 tick)= 発車の 1 tick 前から在線するので dep-1 に乗れる
    world, agents, rail = _rail(departures=(100,), lines=("井の頭線",))
    dep = int(rail.dep_tick[0])
    ids = np.arange(2, dtype=np.int64)
    _put_on_platform(agents, world, ids, 0)
    R.apply(_intents(ids, C.ACT_BOARD), C.IntentBatch.empty(), agents, world, dep - 1, rail=rail)
    assert np.all(agents.registry.transit_state[ids] == 1)
    out = R.apply(_intents(ids, C.ACT_ALIGHT), C.IntentBatch.empty(), agents, world, dep, rail=rail)
    assert out.n_alighted == 2
    assert np.all(agents.registry.transit_state[ids] == 0)
    assert np.all(agents.cell[ids] == 0)
    assert int(rail.occupancy[0]) == 0


def test_alight_when_the_train_does_not_stop_returns_no_stop():
    world, agents, rail = _rail(departures=(100,))
    dep = int(rail.dep_tick[0])
    ids = np.arange(2, dtype=np.int64)
    _put_on_platform(agents, world, ids, 0)
    R.apply(_intents(ids, C.ACT_BOARD), C.IntentBatch.empty(), agents, world, dep, rail=rail)
    R.apply(_intents(ids, C.ACT_ALIGHT), C.IntentBatch.empty(), agents, world, dep + 5, rail=rail)
    assert np.all(agents.last_result[ids] == int(ResultCode.NO_STOP))


def test_alight_without_rail_is_no_stop_c2_compatible():
    world, agents, _ = _rail()
    ids = np.arange(2, dtype=np.int64)
    R.apply(_intents(ids, C.ACT_ALIGHT), C.IntentBatch.empty(), agents, world, 10)
    assert np.all(agents.last_result[ids] == int(ResultCode.NO_STOP))
    R.apply(_intents(ids, C.ACT_BOARD), C.IntentBatch.empty(), agents, world, 10)
    assert np.all(agents.last_result[ids] == int(ResultCode.NO_TRAIN))


# ================================================================= 乗客の保存則
def test_riders_are_never_lost():
    world, agents, rail = _rail(n_agents=40, departures=(100, 200))
    ext = rail.external_home_agents()
    if ext.size:
        R.place_at_external(agents, ext, rail.external_line[ext])
    for t in range(0, 400):
        rail.step(t)
        if t == int(rail.dep_tick[0]):
            here = np.flatnonzero(agents.cell == 0)[:5]
            if here.size:
                R.apply(_intents(here, C.ACT_BOARD), C.IntentBatch.empty(),
                        agents, world, t, rail=rail)
        inb, riding, outside = rail.rider_census()
        assert inb + riding + outside == agents.n, (t, inb, riding, outside)


def test_departure_moves_riders_to_the_external_node():
    world, agents, rail = _rail(departures=(100,))
    dep = int(rail.dep_tick[0])
    ids = np.arange(3, dtype=np.int64)
    _put_on_platform(agents, world, ids, 0)
    R.apply(_intents(ids, C.ACT_BOARD), C.IntentBatch.empty(), agents, world, dep, rail=rail)
    rail.step(dep + 1)
    assert np.all(agents.registry.transit_state[ids] == 2)
    assert np.all(agents.cell[ids] == -1)
    assert rail.n_departed_riders == 3


def test_departures_are_logged_as_scheduled():
    from shibuya.world.processes.actual_log import ActualLog

    world = make_world(9)
    agents, schedule = make_agents(world, 10)
    pa = fake_timetable_assets(departures=(100, 200))
    log = ActualLog("actual_log")
    rail = RailProcess(world, agents, pa, master_seed=1, schedule=schedule, actual_log=log)
    for t in range(0, 320):
        rail.step(t)
    rows = log.rows_for("rail_operation_static")
    assert rows.size == rail.dep_tick.size
    assert set(int(x) for x in rows["deviation"]) == {0}  # SCHEDULED
    rate = log.compliance_rate("rail_operation_static")
    assert rate.rate == 1.0
