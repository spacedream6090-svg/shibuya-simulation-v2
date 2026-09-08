"""世界過程(C4 第1陣 前半)のテスト用フィクスチャ。

合成世界 + 手書きの ``ProcessAssets`` で、実資産が無い CI でも全過程を動かせるようにする。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import AgentState
from shibuya.agents.schedule import synthesize
from shibuya.engine import resolve as R
from shibuya.world.assets import ProcessAssets
from shibuya.world.state import World

WORLD_DIR = Path("data/world/v2")
real_data = pytest.mark.skipif(
    not (WORLD_DIR / "w12_timetables.parquet").exists(), reason="実世界資産が無い"
)


def make_world(n_cells: int = 9, seed: int = 1) -> World:
    return World.synthetic(n_cells=n_cells, seed=seed)


def make_agents(world: World, n: int = 20, seed: int = 1) -> tuple[AgentState, object]:
    """初期化済み(凍結済み)の個体状態と mock 日課。"""
    agents = AgentState(n)
    schedule = synthesize(n, seed, world.n_cells)
    R.initialize(agents, world, schedule)
    agents.freeze()
    world.freeze()
    return agents, schedule


def fake_timetable_assets(
    *,
    platform_cell: int = 0,
    lines: tuple[str, ...] = ("山手線", "井の頭線"),
    departures: tuple[int, ...] = (100, 200, 300),
) -> ProcessAssets:
    """1 駅 2 路線・平日のみの最小時刻表を持つ ``ProcessAssets``。"""
    line_idx = []
    dep = []
    for li in range(len(lines)):
        for d in departures:
            line_idx.append(li)
            dep.append(d + li)  # 路線ごとに 1 分ずらす
    n = len(dep)
    return ProcessAssets(
        source="test",
        tt_lines=tuple(lines),
        tt_line_idx=np.asarray(line_idx, dtype=np.int16),
        tt_calendar=np.zeros(n, dtype=np.int8),
        tt_direction=np.zeros(n, dtype=np.int16),
        tt_departure_min=np.asarray(dep, dtype=np.int32),
        line_platform_cell=np.full(len(lines), platform_cell, dtype=np.int32),
    )


def fake_weather_assets(
    n_cells: int,
    *,
    dates: tuple[str, ...] = ("2026-07-28", "2026-07-29"),
    heat_stage: int = 3,
) -> ProcessAssets:
    """1 層 2 日・全時刻同じ暑さ段の気象資産(影グリッドは無し)。"""
    wbgt = np.full((len(dates), 24), 29.0, dtype=np.float64)
    stage = np.full((len(dates), 24), heat_stage, dtype=np.int8)
    return ProcessAssets(
        source="test",
        weather_dates=dates,
        weather_stratum=tuple("平日|晴" for _ in dates),
        weather_weekday_kind=tuple("平日" for _ in dates),
        weather_type=tuple("晴" for _ in dates),
        sunrise_min=np.full(len(dates), 5 * 60.0),
        sunset_min=np.full(len(dates), 19 * 60.0),
        hourly_wbgt=wbgt,
        hourly_heat_stage=stage,
        cell_street_point=np.arange(n_cells, dtype=np.int32),
        n_street_points=n_cells,
    )


def fake_plan_assets(rows) -> ProcessAssets:
    """``rows`` = ``[(poi, weekday, start, end), …]`` の営業時間 PlanSpec。"""
    arr = np.asarray(rows, dtype=np.int64).reshape(-1, 4)
    return ProcessAssets(
        source="test",
        plan_poi=arr[:, 0].astype(np.int32),
        plan_day=arr[:, 1].astype(np.int8),
        plan_start=arr[:, 2].astype(np.int32),
        plan_end=arr[:, 3].astype(np.int32),
    )
