"""混雑場・流れ・屋内占有・待ち行列(D-R2-5 第1陣 + §7.2 初回実装)のテスト。

正典: 知覚契約書 §3 人物①(密度・流れ)/人物②(行列)・16行表 行2(容量 c・M/M/c・離脱閾値)。
"""

from __future__ import annotations

import numpy as np

from shibuya.agents.state import Activity, ResultCode
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.processes.crowd import (
    DWELL_MAX_TICKS,
    FLOW_NONE,
    WAIT_MAX_TICKS,
    CrowdProcess,
    seats_for_categories,
)
from shibuya.perception import templates as PT

from .conftest import make_agents, make_world


#: 合成 POI の営業時間は 10:00-22:00(``assets.DEFAULT_OPEN_FROM_TICK``)。購入はこの窓の中で試す。
T_OPEN = 700


def _setup(n_agents: int = 20, n_cells: int = 9):
    world = make_world(n_cells)
    agents, schedule = make_agents(world, n_agents)
    return world, agents, CrowdProcess(world, agents), schedule


def _buy_intents(agent_ids, poi):
    a = np.asarray(agent_ids, dtype=np.int64)
    return C.IntentBatch(
        agent_id=a,
        action_code=np.full(a.size, C.ACT_BUY, dtype=np.int8),
        target_id=np.full(a.size, poi, dtype=np.int32),
        resource_id=np.full(a.size, -1, dtype=np.int32),
        t_notice_ns=np.zeros(a.size, dtype=np.int64),
    )


# ================================================================= 席数(容量 c)
def test_seats_are_derived_from_the_category():
    seats = seats_for_categories(("food", "shop", "unknown"))
    assert seats[0] == 30  # 60 m² / 2 m²(飲食)
    assert seats[1] == 25  # 100 m² / 4 m²(物販)
    assert seats[2] >= 1


# ================================================================= 流れ(人物①)
def test_flow_vocabulary_has_three_values_like_the_renderer():
    """レンダラの ``FLOW_WORDS`` は 3 値。8 方位は併置(描画には出さない)。"""
    assert len(PT.FLOW_WORDS) == 3


def test_flow_is_still_when_nobody_moves():
    world, agents, crowd, _ = _setup()
    crowd.step(0)
    occupied = np.asarray(world.cells.density) > 0
    assert np.all(crowd.flow[occupied] == 1)  # 滞留気味
    assert np.all(crowd.flow_dir8[occupied] == FLOW_NONE)


def test_flow_is_coherent_when_everyone_heads_the_same_way():
    world, agents, crowd, _ = _setup(n_agents=12, n_cells=9)
    ids = np.arange(agents.n, dtype=np.int64)
    R.rail_arrive(agents, world, ids, np.zeros(ids.size, dtype=np.int64))
    move = C.IntentBatch(
        agent_id=ids,
        action_code=np.full(ids.size, C.ACT_MOVE, dtype=np.int8),
        target_id=np.full(ids.size, 8, dtype=np.int32),
        resource_id=np.full(ids.size, -1, dtype=np.int32),
        t_notice_ns=np.zeros(ids.size, dtype=np.int64),
    )
    R.apply(move, C.IntentBatch.empty(), agents, world, 1)
    crowd.step(1)
    moving_cells = np.unique(agents.cell[agents.activity == int(Activity.MOVING)])
    moving_cells = moving_cells[moving_cells >= 0]
    assert moving_cells.size >= 1
    assert np.all(crowd.flow[moving_cells] == 2)  # 一方向に流れている
    assert np.all(crowd.flow_dir8[moving_cells] < 8)


def test_flow_dir8_is_quantised_into_eight_sectors():
    world, agents, crowd, _ = _setup(n_agents=8, n_cells=9)
    crowd.step(0)
    assert set(np.unique(crowd.flow_dir8)) <= set(range(9))


# ================================================================= 屋内占有・待ち行列
def test_buying_registers_occupancy_and_full_shops_queue():
    world, agents, crowd, _ = _setup(n_agents=30, n_cells=4)
    poi = 0
    cell = int(world.pois.cell[poi])
    ids = np.arange(6, dtype=np.int64)
    R.rail_arrive(agents, world, ids, np.full(ids.size, cell, dtype=np.int64))
    crowd.seats[poi] = 3
    crowd.step(T_OPEN)
    out = R.apply(_buy_intents(ids, poi), C.IntentBatch.empty(), agents, world, T_OPEN, crowd=crowd)
    assert out.n_purchases == 3
    assert out.n_queued == 3
    queued = np.flatnonzero(agents.registry.queue_poi == poi)
    assert queued.size == 3
    assert np.all(agents.activity[queued] == int(Activity.WAITING))
    seated = np.flatnonzero(agents.registry.poi_ref == poi)
    assert seated.size == 3
    crowd.step(T_OPEN + 1)
    assert int(crowd.occupancy[poi]) == 3
    assert int(crowd.queue_len[poi]) == 3


def test_queue_balks_after_the_wait_threshold():
    world, agents, crowd, _ = _setup(n_agents=20, n_cells=4)
    poi = 0
    cell = int(world.pois.cell[poi])
    ids = np.arange(4, dtype=np.int64)
    R.rail_arrive(agents, world, ids, np.full(ids.size, cell, dtype=np.int64))
    crowd.seats[poi] = 0
    crowd.step(T_OPEN)
    R.apply(_buy_intents(ids, poi), C.IntentBatch.empty(), agents, world, T_OPEN, crowd=crowd)
    assert int(np.count_nonzero(agents.registry.queue_poi == poi)) == 4
    crowd.step(T_OPEN + WAIT_MAX_TICKS - 1)
    assert crowd.n_balked == 0
    crowd.step(T_OPEN + WAIT_MAX_TICKS)
    assert crowd.n_balked == 4
    assert np.all(agents.registry.queue_poi[ids] == -1)
    assert np.all(agents.last_result[ids] == int(ResultCode.INTERRUPTED))


def test_occupancy_is_released_after_the_dwell_limit():
    world, agents, crowd, _ = _setup(n_agents=20, n_cells=4)
    poi = 0
    cell = int(world.pois.cell[poi])
    ids = np.arange(3, dtype=np.int64)
    R.rail_arrive(agents, world, ids, np.full(ids.size, cell, dtype=np.int64))
    crowd.step(T_OPEN)
    R.apply(_buy_intents(ids, poi), C.IntentBatch.empty(), agents, world, T_OPEN, crowd=crowd)
    crowd.step(T_OPEN + 1)
    assert int(crowd.occupancy[poi]) == 3
    crowd.step(T_OPEN + DWELL_MAX_TICKS)
    assert crowd.n_released == 3
    assert int(crowd.occupancy[poi]) == 0
    assert np.all(agents.activity[ids] == int(Activity.IDLE))


def test_queue_rows_gives_the_b4b_material():
    world, agents, crowd, _ = _setup(n_agents=20, n_cells=4)
    poi = 1
    cell = int(world.pois.cell[poi])
    ids = np.arange(5, dtype=np.int64)
    R.rail_arrive(agents, world, ids, np.full(ids.size, cell, dtype=np.int64))
    crowd.seats[poi] = 0
    crowd.step(T_OPEN)
    R.apply(_buy_intents(ids, poi), C.IntentBatch.empty(), agents, world, T_OPEN, crowd=crowd)
    crowd.step(T_OPEN + 1)
    rows = crowd.queue_rows(3)
    assert rows and rows[0][0] == poi and rows[0][2] == 5
    assert f"行列: {rows[0][1]}に{rows[0][2]}人"


def test_mean_wait_is_finite_and_zero_without_a_queue():
    world, agents, crowd, _ = _setup()
    crowd.step(0)
    w = crowd.mean_wait_ticks()
    assert np.all(np.isfinite(w)) and np.all(w == 0.0)


# ================================================================= 列の捌き(D-113 ③・第268)
def _empty():
    return C.IntentBatch.empty()


def _seat_one_and_queue_two(seats=1):
    """席 1 の店に 3 人が来る: 1 人が座り 2 人が並ぶ(並んだ順は id 順)。"""
    world, agents, crowd, _ = _setup(n_agents=30, n_cells=4)
    poi = 0
    cell = int(world.pois.cell[poi])
    ids = np.arange(3, dtype=np.int64)
    R.rail_arrive(agents, world, ids, np.full(ids.size, cell, dtype=np.int64))
    crowd.seats[poi] = seats
    crowd.step(T_OPEN)
    out = R.apply(_buy_intents(ids, poi), _empty(), agents, world, T_OPEN, crowd=crowd)
    assert out.n_purchases == 1 and out.n_queued == 2
    seated = np.flatnonzero(agents.registry.poi_ref == poi)
    return world, agents, crowd, poi, int(seated[0])


def test_queue_is_served_fifo_when_a_seat_frees_up_d113_3():
    world, agents, crowd, poi, seated = _seat_one_and_queue_two()
    waiting = np.flatnonzero(agents.registry.queue_poi == poi)
    assert waiting.tolist() == sorted(waiting.tolist()) and waiting.size == 2
    assert np.all(crowd.queue_action[waiting] == 0)
    money_before = agents.registry.money[waiting].astype(np.int64).copy()
    stock_before = int(world.pois.stock[poi])
    # 席が空かない tick: 誰も入れない
    crowd.step(T_OPEN + 1)
    out = R.apply(_empty(), _empty(), agents, world, T_OPEN + 1, crowd=crowd)
    assert out.n_served_from_queue == 0
    assert np.all(agents.registry.queue_poi[waiting] == poi)
    # 席が空く: 先に並んだ体(id 小)が入り、購入が完了する
    R.release_indoor(agents, np.array([seated]))
    crowd.step(T_OPEN + 2)
    out = R.apply(_empty(), _empty(), agents, world, T_OPEN + 2, crowd=crowd)
    first, second = int(waiting[0]), int(waiting[1])
    assert out.n_served_from_queue == 1 and out.n_purchases == 1
    assert int(agents.registry.poi_ref[first]) == poi
    assert int(agents.activity[first]) == int(Activity.SHOPPING)
    assert int(agents.registry.queue_poi[first]) == -1 and int(agents.registry.queue_since[first]) == -1
    assert int(agents.registry.money[first]) == int(money_before[0]) - int(world.pois.price[poi])
    assert int(agents.last_result[first]) == int(ResultCode.OK)
    assert int(world.pois.stock[poi]) == stock_before - 1
    assert int(agents.registry.queue_poi[second]) == poi
    assert int(agents.activity[second]) == int(Activity.WAITING)
    # もう 1 席: 2 人目
    R.release_indoor(agents, np.array([first]))
    crowd.step(T_OPEN + 3)
    out = R.apply(_empty(), _empty(), agents, world, T_OPEN + 3, crowd=crowd)
    assert out.n_served_from_queue == 1
    assert int(agents.registry.poi_ref[second]) == poi
    crowd.step(T_OPEN + 4)
    assert int(crowd.queue_len[poi]) == 0 and int(crowd.occupancy[poi]) == 1


def test_waiting_bodies_take_the_seat_before_newcomers():
    """FIFO: 空いた席は、この tick に来た買い手より先に並んでいた体が取る。"""
    world, agents, crowd, poi, seated = _seat_one_and_queue_two()
    waiting = np.flatnonzero(agents.registry.queue_poi == poi)
    cell = int(world.pois.cell[poi])
    newcomer = np.array([10], dtype=np.int64)
    R.rail_arrive(agents, world, newcomer, np.full(1, cell, dtype=np.int64))
    R.release_indoor(agents, np.array([seated]))
    crowd.step(T_OPEN + 2)
    out = R.apply(_buy_intents(newcomer, poi), _empty(), agents, world, T_OPEN + 2, crowd=crowd)
    assert out.n_served_from_queue == 1
    assert int(agents.registry.poi_ref[int(waiting[0])]) == poi
    assert int(agents.registry.queue_poi[10]) == poi, "新参は列の後ろへ"
    assert out.n_queued == 1


def test_queue_service_switch_off_keeps_the_old_behaviour():
    world, agents, crowd, poi, seated = _seat_one_and_queue_two()
    waiting = np.flatnonzero(agents.registry.queue_poi == poi)
    R.release_indoor(agents, np.array([seated]))
    crowd.step(T_OPEN + 2)
    out = R.apply(_empty(), _empty(), agents, world, T_OPEN + 2, crowd=crowd, queue_service=False)
    assert out.n_served_from_queue == 0
    assert np.all(agents.registry.queue_poi[waiting] == poi)
    crowd.step(T_OPEN + WAIT_MAX_TICKS)
    assert crowd.n_balked == 2
    assert np.all(agents.last_result[waiting] == int(ResultCode.INTERRUPTED))


def test_queue_disbands_when_the_shop_closes():
    world, agents, crowd, poi, seated = _seat_one_and_queue_two()
    waiting = np.flatnonzero(agents.registry.queue_poi == poi)
    closed_tick = 22 * 60 + 1  # 合成 POI は 10:00-22:00
    assert not bool(world.open_mask(closed_tick)[poi])
    out = R.apply(_empty(), _empty(), agents, world, closed_tick, crowd=crowd)
    assert out.n_queue_closed == 2 and out.n_served_from_queue == 0
    assert np.all(agents.registry.queue_poi[waiting] == -1)
    assert np.all(agents.activity[waiting] == int(Activity.IDLE))
    assert np.all(agents.last_result[waiting] == int(ResultCode.CLOSED))


def test_served_body_that_can_no_longer_pay_leaves_the_queue():
    world, agents, crowd, poi, seated = _seat_one_and_queue_two()
    waiting = np.flatnonzero(agents.registry.queue_poi == poi)
    first = int(waiting[0])
    with agents.writable():
        agents.registry.money[first] = 0
    R.release_indoor(agents, np.array([seated]))
    crowd.step(T_OPEN + 2)
    out = R.apply(_empty(), _empty(), agents, world, T_OPEN + 2, crowd=crowd)
    assert int(agents.last_result[first]) == int(ResultCode.MONEY_SHORT)
    assert int(agents.registry.queue_poi[first]) == -1
    # 空いた 1 席は次の体が取る(同じ tick に行順で詰める)
    assert out.n_served_from_queue == 1
    assert int(agents.registry.poi_ref[int(waiting[1])]) == poi


def test_apply_without_a_crowd_process_never_serves():
    world, agents, _, _ = _setup(n_agents=5, n_cells=4)
    out = R.apply(_empty(), _empty(), agents, world, T_OPEN)
    assert out.n_served_from_queue == 0 and out.n_queue_closed == 0
