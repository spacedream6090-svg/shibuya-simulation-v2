"""断面自動車交通(§7.2 初回実装・C 類 + B 類域外発生)のテスト。

正典: 世界データ構築仕様書 D-W11(道路交通センサス R3)・世界過程設計書 §7.2。
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from shibuya.engine.processes.traffic import (
    DAY12_HOURS,
    KLASS_Q12,
    KLASS_Q24,
    THROUGH_TRAFFIC_RATIO,
    TrafficProcess,
)
from shibuya.world.assets import ProcessAssets

from .conftest import WORLD_DIR, make_world, real_data


def _assets(n_cells: int) -> ProcessAssets:
    names = ("primary", "secondary", "tertiary", "footway")
    code = np.array([0, 1, 2, 3, 0], dtype=np.int16)
    return ProcessAssets(
        source="test",
        edge_klass_code=code,
        edge_klass_names=names,
        edge_cell=np.array([0, 0, 1, 1, 2], dtype=np.int32) % max(1, n_cells),
        edge_length_m=np.array([100.0, 200.0, 50.0, 10.0, 300.0]),
    )


def test_hourly_sums_equal_the_24h_volume():
    """検算: Σ_h 時間帯別交通量 = 24 時間交通量。"""
    world = make_world(9)
    proc = TrafficProcess(world, _assets(world.n_cells))
    assert proc.active
    total = proc.edge_hourly.sum(axis=1)
    assert np.allclose(total, proc.q24)


def test_day12_window_carries_the_census_day_volume():
    world = make_world(9)
    proc = TrafficProcess(world, _assets(world.n_cells))
    day = proc.edge_hourly[:, list(DAY12_HOURS)].sum(axis=1)
    want = np.array([KLASS_Q12["primary"], KLASS_Q12["secondary"], KLASS_Q12["tertiary"], 0.0,
                     KLASS_Q12["primary"]])
    assert np.allclose(day, want)


def test_non_road_klasses_carry_no_traffic():
    world = make_world(9)
    proc = TrafficProcess(world, _assets(world.n_cells))
    assert proc.edge_hourly[3].sum() == 0.0  # footway


def test_cell_aggregate_matches_the_edge_sum():
    world = make_world(9)
    proc = TrafficProcess(world, _assets(world.n_cells))
    assert np.isclose(proc.cell_hourly.sum(), proc.edge_hourly.sum())


def test_step_only_switches_on_the_hour():
    world = make_world(9)
    proc = TrafficProcess(world, _assets(world.n_cells))
    proc.step(0)
    first = proc.cell_vehicles.copy()
    proc.step(30)
    assert proc.hour == 0 and np.array_equal(proc.cell_vehicles, first)
    proc.step(8 * 60)
    assert proc.hour == 8
    assert np.allclose(proc.cell_vehicles, proc.cell_hourly[:, 8])


def test_daily_vehicle_km_and_through_share():
    world = make_world(9)
    proc = TrafficProcess(world, _assets(world.n_cells))
    lengths = np.array([100.0, 200.0, 50.0, 10.0, 300.0]) / 1_000.0
    assert np.isclose(proc.daily_vehicle_km, float((proc.q24 * lengths).sum()))
    assert np.isclose(proc.through_vehicle_km, proc.daily_vehicle_km * THROUGH_TRAFFIC_RATIO)


def test_inactive_without_road_assets():
    world = make_world(9)
    proc = TrafficProcess(world, ProcessAssets.synthetic())
    assert not proc.active
    proc.step(0)
    assert proc.daily_vehicle_km == 0.0


# ================================================================= W10 との転記一致
@real_data
def test_klass_defaults_match_the_w10_header():
    """``build`` は実行時に import できないので値を転記した。ずれを機械検査する。"""
    header = json.loads((WORLD_DIR / "W10.header.json").read_text(encoding="utf-8"))
    defaults = header["notes"]["census_defaults"]
    for klass, row in defaults.items():
        assert KLASS_Q12[klass] == pytest.approx(row["q12"]), klass
        assert KLASS_Q24[klass] == pytest.approx(row["q24"]), klass
    assert list(DAY12_HOURS) == header["params"]["census_day12_hours"]
