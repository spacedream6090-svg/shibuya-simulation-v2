"""昼夜・天候・体感温度(D-R2-5 第1陣 1-2 行目)のテスト。

正典: 世界データ構築仕様書 D-W15(実日ブートストラップ)・知覚契約書 §3 内受容(日陰 0.86)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.engine.processes.environment import (
    FALLBACK_THERMAL,
    HEAT_STAGE_TO_THERMAL,
    SHADE_FACTOR,
    EnvironmentProcess,
    select_day,
)
from shibuya.world.assets import ProcessAssets

from .conftest import fake_weather_assets, make_agents, make_world

STRATA = {"平日|晴": ["2026-08-03", "2026-08-05", "2026-08-06"], "平日|雨": ["2026-07-28"]}


# ================================================================= 実日の乱択(D-W15)
def test_select_day_is_deterministic_for_the_same_seed_and_stratum():
    a = select_day(7, "平日|晴", STRATA)
    b = select_day(7, "平日|晴", STRATA)
    assert a == b and a in STRATA["平日|晴"]


def test_select_day_depends_on_the_seed():
    picks = {select_day(s, "平日|晴", STRATA) for s in range(24)}
    assert len(picks) > 1, "seed を変えても同じ日しか出ないなら層内乱択になっていない"


def test_select_day_rejects_an_empty_stratum():
    with pytest.raises(KeyError):
        select_day(1, "平日|雪", STRATA)


def test_replay_date_is_deterministic_and_inside_the_weekday_stratum():
    world = make_world(9)
    agents, _ = make_agents(world, 12)
    pa = fake_weather_assets(world.n_cells)
    a = EnvironmentProcess(world, agents, pa, master_seed=3, day_index=0)
    b = EnvironmentProcess(world, agents, pa, master_seed=3, day_index=0)
    assert a.replay_date == b.replay_date
    assert a.replay_date in pa.weather_dates
    assert a.stratum == "平日|晴"


# ================================================================= 体感温度(内受容)
@pytest.mark.parametrize("stage", [0, 1, 2, 3, 4])
def test_thermal_follows_the_heat_stage_without_shade(stage):
    world = make_world(9)
    agents, _ = make_agents(world, 12)
    pa = fake_weather_assets(world.n_cells, heat_stage=stage)
    env = EnvironmentProcess(world, agents, pa, master_seed=1, day_index=0)
    env.step(600)  # 10:00
    assert np.all(agents.thermal == HEAT_STAGE_TO_THERMAL[stage])


def test_shade_multiplies_the_thermal_by_the_contract_factor():
    """知覚契約書 §3「内受容 … 影グリッド(**係数0.86**)」。"""
    world = make_world(9)
    agents, _ = make_agents(world, 12)
    pa = fake_weather_assets(world.n_cells, heat_stage=4)
    env = EnvironmentProcess(world, agents, pa, master_seed=1, day_index=0)
    env._planes = np.full((288, (world.n_cells + 7) // 8), 0xFF, dtype=np.uint8)  # 全点日陰
    env._cell_point = np.arange(world.n_cells, dtype=np.int32)
    env._shade_cache_frame = -1
    env.step(600)
    want = int(round(HEAT_STAGE_TO_THERMAL[4] * SHADE_FACTOR))
    assert np.all(agents.thermal == want)
    assert want < HEAT_STAGE_TO_THERMAL[4], "日陰が体感温度を下げていない"


def test_shade_bit_is_read_per_cell():
    """セルごとに日陰ビットを引く(全セル同値ではない)。"""
    world = make_world(16)
    agents, _ = make_agents(world, 40, seed=5)
    pa = fake_weather_assets(world.n_cells, heat_stage=4)
    env = EnvironmentProcess(world, agents, pa, master_seed=1, day_index=0)
    planes = np.zeros((288, (world.n_cells + 7) // 8), dtype=np.uint8)
    planes[:, 0] = 0b1010_1010  # 点 0,2,4,6 が日陰
    env._planes = planes
    env._cell_point = np.arange(world.n_cells, dtype=np.int32)
    env._shade_cache_frame = -1
    mask = env._shade_mask(600)
    assert list(mask[:8]) == [True, False, True, False, True, False, True, False]


def test_synthetic_world_falls_back_to_a_fixed_mild_day():
    world = make_world(9)
    agents, _ = make_agents(world, 12)
    env = EnvironmentProcess(world, agents, ProcessAssets.synthetic(), master_seed=1)
    env.step(0)
    assert env.replay_date == ""
    assert np.all(agents.thermal == FALLBACK_THERMAL)


def test_thermal_is_evaluated_on_the_five_minute_grid():
    """正規化規約⑨(5 分丸め)= D-W10 の影グリッド刻みと同一。"""
    world = make_world(9)
    agents, _ = make_agents(world, 12)
    pa = fake_weather_assets(world.n_cells)
    env = EnvironmentProcess(world, agents, pa, master_seed=1)
    env.step(601)  # 5 の倍数でない → 何もしない
    assert env.n_updates == 0
    env.step(600)
    assert env.n_updates == 1


def test_daylight_phase_follows_sunrise_and_sunset():
    world = make_world(9)
    agents, _ = make_agents(world, 12)
    pa = fake_weather_assets(world.n_cells)
    env = EnvironmentProcess(world, agents, pa, master_seed=1)
    env.step(120)  # 02:00
    assert env.daylight == 0
    env.step(720)  # 12:00
    assert env.daylight == 1
    env.step(1_320)  # 22:00
    assert env.daylight == 2
