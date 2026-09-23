"""C9c-1 ``--area-source {legacy,plateau}`` と席面積の感度腕の検収。

正典
- ``docs/design/v2-c9-geometry-agenda.md`` §6「C9c の範囲(G8 (b))」(ユーザー決定 D-84 (c))。
- ``docs/research/v2-c9-geometry-capacity-research.md`` §2-1(面積)・§1-3(席面積)・§1-4(ホーム)。

検査する 6 点
  (i) 切替口の表と検査関数 / (ii) **既定 legacy でバイト不変**(checkpoint 一致)/
  (iii) plateau で新しい分母が ChangeDetector・EdgeGeometry・レンダラの**同じ 1 本**に入る /
  (iv) manifest 欄(``area_source`` + 資産 SHA)/ (v) 席面積の上書き口 /
  (vi) 法定定数の値と出典(消防法施行規則・建告1441・鈴木 2012)。
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest

from shibuya.engine.change_detect import ChangeDetector
from shibuya.engine.geometry import EdgeGeometry
from shibuya.engine.processes.crowd import (
    DEFAULT_SEAT_AREA_M2,
    SEAT_AREA_M2,
    CrowdProcess,
    seats_for_categories,
)
from shibuya.engine.run import run_day
from shibuya.perception.renderer import PerceptionAssets
from shibuya.world import assets as WA
from shibuya.world.state import World

WORLD_DIR = Path(__file__).resolve().parents[2] / "data" / "world" / "v2"
ASSET = WORLD_DIR / WA.WALKABLE_AREA_FILENAME

SMALL = dict(
    n_agents=32, seed=1, ticks=2, checkpoint_every=2, n_cells=9,
    processes=False, conversations=False,
)


# ================================================================ (i) 表
def test_area_sources_and_default():
    assert WA.AREA_SOURCES == ("legacy", "plateau")
    assert WA.DEFAULT_AREA_SOURCE == "legacy"
    assert WA.check_area_source("plateau") == "plateau"
    with pytest.raises(ValueError):
        WA.check_area_source("PLATEAU")


def test_run_day_rejects_an_unknown_area_source():
    with pytest.raises(ValueError):
        run_day(world=World.synthetic(n_cells=9, seed=1), area_source="実測", **SMALL)


# ================================================================ (ii) バイト不変
def test_default_is_byte_identical_to_explicit_legacy():
    a = run_day(world=World.synthetic(n_cells=9, seed=1), **SMALL)
    b = run_day(world=World.synthetic(n_cells=9, seed=1), area_source="legacy", **SMALL)
    assert a.final_hash == b.final_hash
    assert a.run_manifest_fields()["area_source"] == "legacy"


def test_manifest_carries_the_area_source_field():
    res = run_day(world=World.synthetic(n_cells=9, seed=1), **SMALL)
    fields = res.run_manifest_fields()
    assert fields["area_source"] == "legacy"
    assert fields["seat_area_eatery_m2"] is None
    assert fields["seat_area_retail_m2"] is None
    # 既定では資産 SHA の欄は増えない
    assert WA.WALKABLE_AREA_FILENAME not in fields["frozen_sources"]


def test_plateau_without_the_asset_fails_loudly():
    with pytest.raises(FileNotFoundError):
        run_day(world=World.synthetic(n_cells=9, seed=1), area_source="plateau", **SMALL)


def test_plateau_is_refused_for_injected_renderers():
    with pytest.raises(ValueError):
        run_day(
            world=World.synthetic(n_cells=9, seed=1),
            renderer="stub",
            area_source="plateau",
            **SMALL,
        )


# ================================================================ (iii) 分母は 1 本
def test_the_same_denominator_reaches_detector_and_geometry():
    """``walkable_area_m2`` を替えると LOS 段(起床条件 (i))と Kladek 減速が**同時に**動く。"""
    world = World.synthetic(n_cells=9, seed=1)
    assets = PerceptionAssets.synthetic(world)
    small = np.full(assets.n_cells, 200.0)  # 1,500 → 200 m² = 7.5 倍の密度
    replaced = dataclasses.replace(assets, walkable_area_m2=small)
    assert np.array_equal(replaced.walkable_area_m2, small)

    world.cells.density[:] = 100
    wide = ChangeDetector(4, world.n_cells, walkable_area_m2=assets.walkable_area_m2)
    tight = ChangeDetector(4, world.n_cells, walkable_area_m2=small)
    from shibuya.engine.change_detect import b4_block_raw

    los_wide = b4_block_raw(world, 0, walkable_area_m2=wide.walkable_area_m2)[:, 0]
    los_tight = b4_block_raw(world, 0, walkable_area_m2=tight.walkable_area_m2)[:, 0]
    assert (los_tight > los_wide).all()

    g_wide = EdgeGeometry(world.assets, seed=1, n_agents=4, walkable_area_m2=assets.walkable_area_m2)
    g_tight = EdgeGeometry(world.assets, seed=1, n_agents=4, walkable_area_m2=small)
    assert (
        g_tight.speed_factor_per_cell(world.cells.density)
        < g_wide.speed_factor_per_cell(world.cells.density)
    ).all()
    assert (
        g_tight.density_stage(world.cells.density) >= g_wide.density_stage(world.cells.density)
    ).all()


@pytest.mark.skipif(not ASSET.exists(), reason="C9c-1 資産が無い")
def test_load_walkable_area_matches_the_parquet_order():
    import pyarrow.parquet as pq

    d = pq.read_table(ASSET, columns=["cell_id", "walkable_m2"]).to_pydict()
    ids = [str(v) for v in d["cell_id"]]
    area, sha = WA.load_walkable_area_m2(WORLD_DIR, ids[::-1])
    assert area.tolist() == [float(v) for v in d["walkable_m2"]][::-1]
    assert set(sha) == {WA.WALKABLE_AREA_FILENAME}
    assert len(sha[WA.WALKABLE_AREA_FILENAME]) == 64


@pytest.mark.skipif(not ASSET.exists(), reason="C9c-1 資産が無い")
def test_load_walkable_area_refuses_unknown_cells():
    with pytest.raises(ValueError):
        WA.load_walkable_area_m2(WORLD_DIR, ["g999_999_GL"])


# ================================================================ (v) 席面積
def test_seat_area_override_changes_the_seat_count_only_when_given():
    cats = ("food", "nightlife", "shop", "office")
    base = seats_for_categories(cats)
    same = seats_for_categories(cats, seat_area_m2=None, default_seat_area_m2=None)
    assert base.tolist() == same.tolist()
    # 消防法側(飲食 3.0 / 物販 4.0)= D-84 の「席 4.0/3.0」
    fire = seats_for_categories(
        cats,
        seat_area_m2={k: WA.SEAT_AREA_M2_FIRE_CODE["eatery"] for k in SEAT_AREA_M2},
        default_seat_area_m2=WA.SEAT_AREA_M2_FIRE_CODE["retail"],
    )
    assert fire[0] < base[0] and fire[1] < base[1]      # 飲食は席が減る(2.0 → 3.0)
    assert fire[2] == base[2] and fire[3] == base[3]    # 物販その他は 4.0 のまま=不変


def test_crowd_process_keeps_the_current_table_by_default():
    world = World.synthetic(n_cells=9, seed=1)
    from shibuya.agents.state import AgentState

    p = CrowdProcess(world, AgentState(4))
    assert p.seat_area_m2 == SEAT_AREA_M2
    assert p.default_seat_area_m2 == DEFAULT_SEAT_AREA_M2
    assert p.seats.tolist() == seats_for_categories(world.assets.poi_cat).tolist()


def test_run_day_rejects_a_non_positive_seat_area():
    with pytest.raises(ValueError):
        run_day(world=World.synthetic(n_cells=9, seed=1), seat_area_eatery_m2=0.0, **SMALL)
    with pytest.raises(ValueError):
        run_day(world=World.synthetic(n_cells=9, seed=1), seat_area_retail_m2=-1.0, **SMALL)


def test_seat_area_arm_reaches_the_manifest():
    res = run_day(
        world=World.synthetic(n_cells=9, seed=1),
        seat_area_eatery_m2=3.0,
        seat_area_retail_m2=4.0,
        **SMALL,
    )
    fields = res.run_manifest_fields()
    assert fields["seat_area_eatery_m2"] == 3.0
    assert fields["seat_area_retail_m2"] == 4.0


# ================================================================ (vi) 法定定数
def test_legal_constants_match_the_primary_sources():
    """消防法施行規則 1 条の 3(飲食 3 m² / 物販 4 m²)・建告1441(飲食室 0.7 人/m² =
    1.43 m²/人・売場 0.5 = 2.0)・鈴木 2012(ホーム 3.30 人/m²・整列 4.00〜4.50)。"""
    assert WA.SEAT_AREA_M2_FIRE_CODE == {"eatery": 3.0, "retail": 4.0}
    assert WA.SEAT_AREA_M2_BUILDING_NOTICE["retail"] == 2.0
    assert WA.SEAT_AREA_M2_BUILDING_NOTICE["eatery"] == pytest.approx(1.0 / 0.7, abs=1e-12)
    assert WA.PLATFORM_DWELL_DENSITY_PER_M2 == 3.30
    assert WA.PLATFORM_QUEUE_DENSITY_PER_M2 == (4.00, 4.50)
    # 建告1441 の通路 0.3 m²/人 と鈴木 2012 の実測 3.30 人/m² が独立に一致する(答申 §1-3 c4)
    assert WA.CORRIDOR_MAX_DENSITY_PER_M2 == pytest.approx(3.3333333, abs=1e-6)
    # **現行の実行時既定は法定値ではない**(飲食 2.0 は出所不明の expedient)
    assert SEAT_AREA_M2 == {"food": 2.0, "nightlife": 2.0}
    assert DEFAULT_SEAT_AREA_M2 == WA.SEAT_AREA_M2_FIRE_CODE["retail"] == 4.0
