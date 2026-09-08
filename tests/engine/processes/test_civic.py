"""公共サービス出動・報道/公式発信・ホテル・インフラ・大規模イベントのテスト。"""

from __future__ import annotations

import numpy as np

from shibuya.agents.state import Activity, AgentKind, ResultCode
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.processes.civic import (
    DISPATCH_MEDIAN_MIN,
    EVENT_WINDOW,
    HOTEL_CHECKIN_MINUTE,
    HOTEL_CHECKOUT_MINUTE,
    PRESS_MINUTES,
    HotelProcess,
    InfraLoadProcess,
    LargeEventProcess,
    PressProcess,
    PublicServiceDispatchProcess,
)
from shibuya.world.assets import ProcessAssets

from .conftest import make_agents, make_world


# ================================================================= 出動
def test_dispatch_delay_is_lognormal_around_the_median():
    world = make_world(16)
    d = PublicServiceDispatchProcess(world, master_seed=3)
    for k in range(400):
        d.request(0, k % 16, (0.0, 0.0))
    mean = d.delay_minutes_total / d.n_dispatched
    assert 1.0 <= mean <= 4.0 * DISPATCH_MEDIAN_MIN
    assert d.n_dispatched == 400


def test_dispatch_arrival_resolves_the_incident():
    world = make_world(9)
    d = PublicServiceDispatchProcess(world, master_seed=1)
    arrive = d.request(10, 2, (5.0, 6.0))
    assert arrive > 10
    assert d.arrivals(arrive - 1) == []
    got = d.arrivals(arrive)
    assert len(got) == 1 and got[0][0] == 2
    assert d.n_arrived == 1 and not d.pending


def test_dispatch_rejects_an_unknown_cell():
    world = make_world(9)
    d = PublicServiceDispatchProcess(world, master_seed=1)
    assert d.request(0, 999, (0.0, 0.0)) == -1
    assert d.n_dispatched == 0


# ================================================================= 報道・公式発信
def test_press_is_due_only_at_the_fixed_minutes():
    world = make_world(9)
    p = PressProcess(world)
    assert p.due(PRESS_MINUTES[0]) and not p.due(PRESS_MINUTES[0] + 1)
    for t in range(1_440):
        p.step(t)
    assert p.n_releases == len(PRESS_MINUTES)


def test_press_line_carries_the_feature_tag_and_no_imperative():
    world = make_world(9)
    p = PressProcess(world)
    assert p.line.startswith("〔素性: 放送")
    assert p.strip.n_removed == 0


# ================================================================= ホテル
def test_hotel_rests_without_hotel_pois():
    world = make_world(9)
    agents, _ = make_agents(world, 10)
    h = HotelProcess(world, agents, ProcessAssets.synthetic())
    assert not h.active
    h.step(HOTEL_CHECKIN_MINUTE)
    assert h.counters()["checkin"] == 0.0


def _hotel_world(n_agents: int = 12, rooms: int = 2):
    world = make_world(9)
    agents, schedule = make_agents(world, n_agents)
    assets = ProcessAssets(source="test", hotel_poi=np.array([0, 1], dtype=np.int64))
    ext = np.zeros(n_agents, dtype=bool)
    ext[:] = True
    h = HotelProcess(world, agents, assets, external_home=ext, rooms_per_poi=rooms)
    return world, agents, schedule, h


def test_hotel_checkin_is_capped_by_the_rooms_and_reports_no_bed():
    world, agents, _schedule, h = _hotel_world(n_agents=12, rooms=1)
    assert h.active
    r = agents.registry
    with agents.writable():
        r.field("kind")[:] = int(AgentKind.VISITOR)
        r.cell[:] = int(world.pois.cell[0])
    h.step(HOTEL_CHECKIN_MINUTE)
    assert h.n_checkin == 1  # 1 室しかない
    assert h.n_no_bed == 11
    assert int(h.rooms_occupied.sum()) == 1


def test_hotel_bed_lets_a_visitor_sleep_away_from_home():
    """``resolve._apply_sleep`` がホテルの客室を寝床として認める(満室なら ``NO_BED``)。"""
    world, agents, schedule, h = _hotel_world(n_agents=6, rooms=4)
    r = agents.registry
    with agents.writable():
        r.field("kind")[:] = int(AgentKind.VISITOR)
        r.cell[:] = int(world.pois.cell[0])
    h.step(HOTEL_CHECKIN_MINUTE)
    assert h.n_checkin == 4
    guests = np.flatnonzero(h.bed_cell >= 0)[:2].astype(np.int64)
    other = np.flatnonzero(h.bed_cell < 0)[:1].astype(np.int64)
    ids = np.concatenate([guests, other])
    intents = C.IntentBatch(
        agent_id=ids,
        action_code=np.full(ids.size, C.ACT_SLEEP, dtype=np.int8),
        target_id=np.full(ids.size, -1, dtype=np.int32),
        resource_id=np.full(ids.size, -1, dtype=np.int32),
        t_notice_ns=np.zeros(ids.size, dtype=np.int64),
    )
    out = R.apply(
        intents, C.IntentBatch.empty(), agents, world, 100, schedule=schedule, hotel=h
    )
    assert out.n_hotel_sleep == 2
    assert list(r.activity[guests]) == [int(Activity.SLEEPING)] * 2
    assert int(r.last_result[int(other[0])]) == int(ResultCode.NO_BED)


def test_hotel_checkout_frees_the_rooms():
    world, agents, _schedule, h = _hotel_world(n_agents=6, rooms=4)
    with agents.writable():
        agents.registry.field("kind")[:] = int(AgentKind.VISITOR)
        agents.registry.cell[:] = int(world.pois.cell[0])
    h.step(HOTEL_CHECKIN_MINUTE)
    assert int(h.rooms_occupied.sum()) > 0
    h.step(HOTEL_CHECKOUT_MINUTE)
    assert int(h.rooms_occupied.sum()) == 0
    assert h.n_checkout > 0 and int((h.bed_cell >= 0).sum()) == 0


# ================================================================= インフラ
def test_infra_load_grows_with_occupancy_and_reports_a_peak():
    world = make_world(9)
    agents, _ = make_agents(world, 30)
    infra = InfraLoadProcess(world, agents)
    for t in range(180):
        infra.step(t)
    c = infra.counters()
    assert c["power_kwh_day"] > 0 and c["water_m3_day"] > 0
    assert 0 <= c["peak_hour"] < 24


# ================================================================= 大規模イベント
def test_large_event_pulls_visitors_in_and_sends_them_back():
    world = make_world(16)
    agents, _ = make_agents(world, 40)
    ev = LargeEventProcess(world, agents, master_seed=2, visitor_delta=5)
    outside = np.arange(8, dtype=np.int64)
    R.place_at_external(agents, outside, np.zeros(outside.size, dtype=np.int64))
    lo, hi = EVENT_WINDOW
    ev.step(lo)
    assert ev.n_in == 5
    assert int((agents.registry.transit_state == 2).sum()) == 3
    ev.step(hi)
    assert ev.n_out == 5
    assert int((agents.registry.transit_state == 2).sum()) == 8
