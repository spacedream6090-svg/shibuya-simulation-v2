# -*- coding: utf-8 -*-
"""セル→5エリア写像(``c7lib.classify_cells`` / ``build_area_map``)の検査。"""

from __future__ import annotations

import json

import numpy as np
import pytest

from .conftest import TOOLS_C7, real_data


def test_polyline_side_signs(c7lib):
    """折れ線の左右判定: 北→南の線は西が負、西→東の線は北が正。"""
    ns = np.array([[0.0, 1000.0], [0.0, -1000.0]])          # 北→南(下向き)
    ew = np.array([[-1000.0, 0.0], [1000.0, 0.0]])          # 西→東(右向き)
    west = c7lib.polyline_side(np.array([-10.0]), np.array([0.0]), ns)
    east = c7lib.polyline_side(np.array([+10.0]), np.array([0.0]), ns)
    north = c7lib.polyline_side(np.array([0.0]), np.array([+10.0]), ew)
    south = c7lib.polyline_side(np.array([0.0]), np.array([-10.0]), ew)
    assert west[0] < 0 < east[0]
    assert south[0] < 0 < north[0]


def test_classify_toy_quadrants(c7lib, toy_axes):
    """合成幾何: 4 象限 + 中心 + 圏外が期待どおりに落ちる。"""
    idx = {name: i for i, name in enumerate(c7lib.AREA_IDS)}
    px = np.array([-500.0, 500.0, -500.0, 500.0, 0.0, 5000.0])
    py = np.array([500.0, 500.0, -500.0, -500.0, 0.0, 0.0])
    got = c7lib.classify_cells(px, py, toy_axes)
    assert got.tolist() == [
        idx["northwest"], idx["northeast"], idx["southwest"], idx["southeast"],
        idx["central"], c7lib.OUTSIDE,
    ]


def test_classify_dilate_moves_boundary(c7lib, toy_axes):
    """±dilate で外縁と中心が膨らむ(感度試験の口が効いている)。"""
    px = np.array([-10.0, 1020.0])
    py = np.array([120.0, 0.0])
    base = c7lib.classify_cells(px, py, toy_axes)
    grown = c7lib.classify_cells(px, py, toy_axes, dilate_m=50.0)
    idx = {name: i for i, name in enumerate(c7lib.AREA_IDS)}
    assert base[0] == idx["northwest"] and grown[0] == idx["central"]
    assert base[1] == c7lib.OUTSIDE and grown[1] != c7lib.OUTSIDE


def test_build_area_map_shape_and_ha(c7lib, toy_axes):
    """格子中心での分類・面積[ha]は GL セルだけ数える。"""
    ix = np.array([-1, -1, 0, 0])
    iy = np.array([-1, 0, -1, 0])
    pids = ["g-1_-1_GL", "g-1_0_UG", "g0_-1_GL", "g0_0_GL"]
    amap = c7lib.build_area_map(pids, ix, iy, toy_axes)
    assert amap.n_cells == 4
    counts = amap.counts()
    assert sum(counts.values()) == 4
    # 100m セル 3 枚が GL → 面積は 3ha 以下(圏外セルは数えない)
    assert sum(amap.area_ha().values()) <= 3.0


def test_area_map_json_roundtrip(c7lib, toy_axes):
    ix = np.arange(-3, 3)
    iy = np.zeros(6, dtype=int)
    pids = [f"g{i}_0_GL" for i in ix]
    amap = c7lib.build_area_map(pids, ix, iy, toy_axes)
    doc = json.loads(json.dumps(amap.to_json(), ensure_ascii=False))
    back = c7lib.AreaMap.from_json(doc)
    assert back.place_ids == amap.place_ids
    assert back.area_of_cell.tolist() == amap.area_of_cell.tolist()


def test_axes_file_is_declared_expedient(c7lib):
    """境界定義ファイルは **expedient** と当てはめの経緯を必ず宣言している。"""
    axes = c7lib.load_axes()
    assert axes["status"] == "expedient"
    assert "fit_note" in axes and "独立検定ではない" in axes["fit_note"]
    for key in ("ns_jr", "ew_west_r246", "ew_east_roppongi"):
        assert len(axes["axes"][key]["waypoints_latlon"]) >= 2


@real_data
def test_real_world_map_gate(c7lib, occ, world_dir):
    """実資産(520 セル)で 5 エリアが全て非空・面積帯を満たす。"""
    amap, gate = occ.build_map(world_dir)
    counts = amap.counts()
    assert amap.n_cells == 520
    for name in c7lib.AREA_IDS:
        assert counts[name] > 0, f"{name} が空"
    assert counts["outside"] > 0, "bbox は 139ha 区域より広いので圏外セルが必ずある"
    assert gate["ok"], gate


@real_data
def test_real_world_sensitivity_reported(occ, world_dir):
    """±50m の感度が測れて、動くセルが 2 割未満(写像が崩壊していない)。"""
    res = occ.sensitivity(world_dir, deltas=(-50.0, 0.0, 50.0))
    ratios = {r["dilate_m"]: r["cells_changed_ratio"] for r in res["rows"]}
    assert ratios[0.0] == 0.0
    assert 0.0 < ratios[-50.0] < 0.2
    assert 0.0 < ratios[50.0] < 0.2
