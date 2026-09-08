"""world のテスト: 合成小世界・資産読み込み・next-hop・セル/POI レジストリ。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya.world import assets as A
from shibuya.world.state import World

ASSET_DIR = Path("data/world/v2")
HAS_ASSETS = A.assets_available(ASSET_DIR)


# ---------------------------------------------------------------- 合成世界
def test_synthetic_shapes():
    w = World.synthetic(n_cells=139, seed=1)
    assert w.n_cells == 139 and w.n_nodes == 139 and w.n_poi == 278
    assert w.assets.next_hop.shape == (139, 139)
    assert w.cells.density.shape == (139,)
    assert w.pois.stock.shape == (278,)
    assert w.assets.source == "synthetic"


def test_synthetic_is_deterministic():
    a = World.synthetic(n_cells=64, seed=3)
    b = World.synthetic(n_cells=64, seed=3)
    c = World.synthetic(n_cells=64, seed=4)
    assert a.state_hash() == b.state_hash()
    assert a.state_hash() != c.state_hash()


def test_next_hop_reaches_every_target():
    """1 tick=1 ノードで必ず目的地に着く(格子は連結)。"""
    w = World.synthetic(n_cells=49, seed=1)
    node = np.zeros(49, dtype=np.int64)
    target = np.arange(49, dtype=np.int64)
    for _ in range(3 * 49):
        node, arrived = w.graph.step_once(node, target)
        if arrived.all():
            break
    assert np.array_equal(node, target)


def test_route_returns_minus_one_for_invalid():
    w = World.synthetic(n_cells=16, seed=1)
    out = w.route_next_node([-1, 0, 3], [5, -1, 3])
    assert out[0] == -1 and out[1] == -1
    assert out[2] == 3  # 目的地に居るときは自分自身


def test_density_matches_bincount():
    w = World.synthetic(n_cells=8, seed=1)
    cells = np.array([0, 0, 3, 7, -1, 99], dtype=np.int32)
    d = w.compute_density(cells)
    assert d.tolist() == [2, 0, 0, 1, 0, 0, 0, 1]


def test_density_stage_is_monotone():
    w = World.synthetic(n_cells=4, seed=1)
    stages = w.density_stage(np.array([0, 1, 5, 20, 60, 150, 400, 1_000, 5_000]))
    assert stages.tolist() == sorted(stages.tolist())
    assert stages[0] == 0


def test_open_mask_default_hours():
    w = World.synthetic(n_cells=4, seed=1)
    assert not w.open_mask(0).any()
    assert w.open_mask(700).all()
    assert not w.open_mask(1_400).any()
    assert int(w.open_count_per_cell(700).sum()) == w.n_poi


def test_world_freeze_guard():
    w = World.synthetic(n_cells=4, seed=1)
    w.freeze()
    with pytest.raises(ValueError):
        w.cells.density[0] = 1
    with pytest.raises(ValueError):
        w.pois.stock[0] = 1
    with w.writable():
        w.cells.density[0] = 5
    assert int(w.cells.density[0]) == 5 and w.frozen


def test_load_or_synthetic_falls_back(tmp_path):
    w = World.load_or_synthetic(tmp_path / "missing", n_cells=25, seed=1)
    assert w.assets.source == "synthetic" and w.n_cells == 25


def test_missing_assets_raise(tmp_path):
    with pytest.raises(FileNotFoundError):
        A.load_assets(tmp_path)


# ---------------------------------------------------------------- 実資産(あれば)
@pytest.mark.skipif(not HAS_ASSETS, reason="data/world/v2 が無い(C1 の成果物)")
def test_real_assets_load_and_map():
    w = World.load(ASSET_DIR)
    a = w.assets
    # W2 実測ヘッダ: place_id=520(GL 453 + DECK 39 + UG 28)
    assert w.n_cells == 520
    assert a.n_nodes == 3_499 and a.n_poi == 2_337
    # 全ノード・全 POI がセルに写る(格子式の写像が W2 と一致している証拠)
    assert int((a.node_cell < 0).sum()) == 0
    assert int((a.poi_cell < 0).sum()) == 0
    assert a.next_hop.shape == (3_499, 3_499)
    assert a.cell_dist.shape == (520, 520)
    # next-hop は mmap(ラン間共有・M8 非算入)
    assert isinstance(a.next_hop, np.memmap)


@pytest.mark.skipif(not HAS_ASSETS, reason="data/world/v2 が無い")
def test_real_assets_routing_is_vectorized():
    w = World.load(ASSET_DIR)
    src = np.zeros(64, dtype=np.int64)
    dst = np.arange(64, dtype=np.int64)
    nxt = w.route_next_node(src, dst)
    assert nxt.shape == (64,)
    assert np.all((nxt >= -1) & (nxt < w.n_nodes))
