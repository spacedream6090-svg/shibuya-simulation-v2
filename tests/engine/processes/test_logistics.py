"""宅配ラストマイル・バス/タクシー・道路工事(§7.2 前倒し)のテスト。"""

from __future__ import annotations

import numpy as np

from shibuya.engine.processes.logistics import (
    BUS_HEADWAY_MIN,
    BUS_SERVICE_WINDOW,
    CELL_AREA_M2,
    PARCELS_PER_DAY_WARD,
    PARCEL_HOUR_CURVE,
    ROADWORK_WINDOW,
    SHIBUYA_WARD_AREA_M2,
    BusTaxiProcess,
    LastMileProcess,
    RoadWorksProcess,
)
from shibuya.world.assets import ProcessAssets

from .conftest import WORLD_DIR, make_world, real_data


# ================================================================= 宅配ラストマイル
def test_parcels_are_the_ward_number_scaled_by_the_bbox_area():
    world = make_world(64)
    lm = LastMileProcess(world)
    share = 64 * CELL_AREA_M2 / SHIBUYA_WARD_AREA_M2
    assert lm.bbox_share == share
    assert lm.parcels_today == round(PARCELS_PER_DAY_WARD * share)
    assert int(lm.parcels_per_cell.sum()) == lm.parcels_today


def test_parcels_follow_the_household_weights():
    world = make_world(16)
    hh = np.zeros(16, dtype=np.int64)
    hh[3] = 10
    hh[7] = 30
    lm = LastMileProcess(world, household_per_cell=hh)
    assert lm.parcels_per_cell[7] > lm.parcels_per_cell[3] > 0
    assert int(lm.parcels_per_cell[[0, 1, 2]].sum()) == 0


def test_parcels_are_delivered_on_the_hourly_curve():
    world = make_world(16)
    hh = np.full(16, 5, dtype=np.int64)
    lm = LastMileProcess(world, household_per_cell=hh)
    for t in range(1_440):
        lm.step(t)
    assert 0 < int(lm.delivered.sum()) <= lm.parcels_today
    assert lm.n_batches > 0
    # 配達帯の外(深夜)には 1 個も出ない
    hours = {h for h, _ in PARCEL_HOUR_CURVE}
    assert 3 not in hours and 2 not in hours


# ================================================================= バス・タクシー
def test_bus_rests_without_stop_data():
    world = make_world(9)
    bus = BusTaxiProcess(world, ProcessAssets.synthetic())
    assert not bus.active
    bus.step(500)
    assert bus.counters()["arrivals"] == 0.0


def test_bus_arrives_on_an_equal_interval_plan():
    world = make_world(16)
    assets = ProcessAssets(source="test", bus_stop_cell=np.array([0, 1, 2], dtype=np.int64))
    bus = BusTaxiProcess(world, assets)
    lo, hi = BUS_SERVICE_WINDOW
    for t in range(1_440):
        bus.step(t)
    per_stop = (hi - lo) // BUS_HEADWAY_MIN
    assert bus.n_arrivals == per_stop * 3
    assert bus.counters()["boardings"] == 0.0  # C4 では乗降を作らない


@real_data
def test_bus_stops_come_from_osm_and_land_on_cells():
    """OSM の ``highway=bus_stop`` 127 点がセルへ写像される(座標欠落は幹線へ置く=expedient)。"""
    from shibuya.world.assets import load_process_assets
    from shibuya.world.state import World

    world = World.load(WORLD_DIR)
    assets = load_process_assets(WORLD_DIR, world.assets)
    assert assets.has_bus_stops
    assert assets.bus_stop_cell.size == 127
    assert bool(((assets.bus_stop_cell >= 0) & (assets.bus_stop_cell < world.n_cells)).all())


# ================================================================= 道路工事・占用
def test_road_works_rest_without_road_data():
    world = make_world(9)
    rw = RoadWorksProcess(world, ProcessAssets.synthetic())
    assert not rw.active
    rw.step(0)
    assert rw.counters()["started"] == 0.0


def test_road_works_occupy_at_night_and_clear_in_the_morning():
    world = make_world(16)
    assets = ProcessAssets(
        source="test",
        edge_cell=np.arange(20, dtype=np.int32) % 16,
        edge_klass_code=np.zeros(20, dtype=np.int16),
        edge_length_m=np.full(20, 50.0),
        edge_klass_names=("residential",),
    )
    rw = RoadWorksProcess(world, assets, master_seed=1, n_works=4)
    assert rw.active and rw.planned_edges.size == 4
    lo, hi = ROADWORK_WINDOW
    rw.step(lo)  # 22:00
    assert rw.occupied_edges.size == 4
    assert int(rw.blocked_cells.sum()) > 0
    rw.step(hi + 60)  # 06:00
    assert rw.occupied_edges.size == 0
    assert int(rw.blocked_cells.sum()) == 0
    assert rw.n_started == 4 and rw.n_finished == 4
