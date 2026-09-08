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
