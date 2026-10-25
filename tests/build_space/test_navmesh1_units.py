"""段 1 ナビメッシュの構築の部品(合成の小さな面・データ不要)。

正: ``docs/design/v2-spatial-design-round-draft.md`` §4 段 1(溶接・多層・接続口・幅の規則・坂・2 回組んで同じ sha・
資産の門=範囲・面積の上限=セル面積の超過なし=第219 の教訓)。
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np
import pytest

from shibuya.build.space import mesh as M
from shibuya.build.space import navmesh1 as N1
from shibuya.build.space import raster as R
from shibuya.world import navmesh as NV
from shibuya.world.navmesh_route import NavPlanner
from tests.build_space import synth as SY


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ------------------------------------------------------------------ 塗りの部品
def test_fill_polygon_square_area_and_hole():
    lab = np.zeros((40, 40), dtype=np.uint8)
    outer = np.array([[2.0, 2.0], [12.0, 2.0], [12.0, 12.0], [2.0, 12.0]])
    hole = np.array([[5.0, 5.0], [9.0, 5.0], [9.0, 9.0], [5.0, 9.0]])
    ex0, ey0, ex1, ey1 = R.polygon_edges([outer, hole])
    n = R.fill_polygon(lab, 0.0, 0.0, 0.5, ex0, ey0, ex1, ey1, 1, R.MODE_IF_ZERO, R.NO_ALLOW)
    # 外 10×10=100 m² − 穴 4×4=16 m² = 84 m² = 336 目
    assert n == 336 and int((lab != 0).sum()) == 336


def test_fill_capsule_width_and_if_zero_priority():
    lab = np.zeros((20, 100), dtype=np.uint8)
    n1 = R.fill_capsule(lab, 0.0, 0.0, 0.5, 5.0, 5.0, 45.0, 5.0, 1.0, 3, R.MODE_IF_ZERO, R.NO_ALLOW)
    assert n1 > 0
    # 先に塗ったものが勝つ(出どころの優先順)
    n2 = R.fill_capsule(lab, 0.0, 0.0, 0.5, 5.0, 5.0, 45.0, 5.0, 1.0, 9, R.MODE_IF_ZERO, R.NO_ALLOW)
    assert n2 == 0 and set(np.unique(lab)) == {0, 3}
    # 幅 2 m の帯の中ほどの列は 4 目
    assert int((lab[:, 50] != 0).sum()) == 4


def test_edt_inside_known_distances():
    mask = np.zeros((11, 11), dtype=np.uint8)
    mask[1:10, 1:10] = 1
    d = R.edt_inside(mask, 1.0)
    assert d[5, 5] == pytest.approx(5.0)
    assert d[1, 1] == pytest.approx(1.0)
    assert d[0, 0] == 0.0


def test_bfs_nearest_label_spreads_inside_allow_only():
    seed = np.zeros((5, 9), dtype=np.int16)
    seed[2, 0] = 1
    seed[2, 8] = 2
    allow = np.ones((5, 9), dtype=np.uint8)
    allow[:, 4] = 0
    lab, dist = R.bfs_nearest_label(seed, allow)
    assert lab[2, 3] == 1 and lab[2, 5] == 2 and lab[2, 4] == 0 and dist[2, 4] == -1


def test_runs_portals_strips_and_components():
    lab = np.zeros((6, 10), dtype=np.uint8)
    lab[0:3, 0:3] = 1           # 左の塊(縦の 1 本の帯)
    lab[3:6, 1:2] = 1           # 下へ続く(重なり 1 目)
    lab[0:2, 6:9] = 2           # 右の離れた塊
    row, x0, x1, src, rptr = M.extract_runs(lab, 32)
    lo, hi, ox0, ox1 = M.run_overlaps(rptr, x0, x1)
    assert np.all(ox1 > ox0)
    strip, ns, cross = M.build_strips(row.size, lo.astype(np.int64), hi.astype(np.int64))
    comp = M.union_find_components(row.size, lo.astype(np.int64), hi.astype(np.int64))
    assert np.unique(comp).size == 2
    # 角だけで触れる 2 つは門でつながらない
    lab2 = np.zeros((2, 4), dtype=np.uint8)
    lab2[0, 0] = 1
    lab2[1, 1] = 1
    row, x0, x1, src, rptr = M.extract_runs(lab2, 32)
    lo, hi, *_ = M.run_overlaps(rptr, x0, x1)
    assert lo.size == 0


def test_close_gaps_fills_corner_touch_and_one_metre_gap():
    lab = np.zeros((20, 20), dtype=np.uint8)
    lab[5:10, 2:8] = 1
    lab[5:10, 10:16] = 1          # 2 目(1 m)の隙間
    lab[12, 3] = 1
    lab[13, 4] = 1                # 角だけで触れる
    n = N1._close_gaps(lab, 1, 16)
    assert n > 0
    assert np.all(lab[6:9, 8:10] == 16)
    row, x0, x1, src, rptr = M.extract_runs(lab, 32)
    lo, hi, *_ = M.run_overlaps(rptr, x0, x1)
    comp = M.union_find_components(row.size, lo.astype(np.int64), hi.astype(np.int64))
    assert np.unique(comp).size == 2   # 上の 2 つの塊は 1 つに・角の 2 目も 1 つに


def test_short_gaps_only_bounded_and_short():
    lab = np.zeros((10, 100), dtype=np.uint8)
    lab[:, 0:20] = 1
    lab[:, 30:60] = 1                  # 5 m の切れ目(20〜30 の目=10 目)
    xy = np.array([[2.0, 2.5], [45.0, 2.5]])
    g = N1._short_gaps(lab, 0.0, 0.0, 0.5, xy, 12.0, 0.25)
    assert len(g) == 1
    assert N1._short_gaps(lab, 0.0, 0.0, 0.5, xy, 4.0, 0.25) == []


def test_sr10_feature_rules():
    lab = np.zeros((4, 10), dtype=np.uint8)
    fid_nosw = np.zeros((4, 10), dtype=np.int32)
    fid_l1 = np.zeros((4, 10), dtype=np.int32)
    fid_nosw[0, :] = 1                  # 歩道の無い詳細の道(住宅街の型)
    fid_l1[1:4, :] = 2                  # LOD1 だけの幹線
    fk = np.array([1, 1, 2], dtype=np.int8)
    dist = np.zeros((4, 10), dtype=np.float32)
    dist[1, :] = 1.0
    dist[2, :] = 3.0
    dist[3, :] = 2.0
    n3, n4, n5 = N1._apply_road_rules(lab, fid_nosw, fid_l1, fk, dist, 2.0)
    assert n3 == 10 and n4 == 0 and n5 == 20
    assert np.all(lab[0] == 3) and np.all(lab[1] == 5) and np.all(lab[2] == 0) and np.all(lab[3] == 5)


def test_min_area_rect_of_rotated_square():
    a = math.radians(30)
    R2 = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    pts = (np.array([[0, 0], [4, 0], [4, 2], [0, 2], [2, 1]]) @ R2.T).astype(float)
    rect = N1._min_area_rect(np.c_[pts, np.zeros(len(pts))])
    e1 = np.hypot(*(rect[1] - rect[0]))
    e2 = np.hypot(*(rect[2] - rect[1]))
    assert sorted([e1, e2]) == pytest.approx([2.0, 4.0], abs=1e-3)


# ------------------------------------------------------------------ 合成の面の全部(溶接・多層・接続口・坂・つなぎ・2 回同じ)
@pytest.fixture(scope="module")
def synth_mesh(tmp_path_factory):
    d = tmp_path_factory.mktemp("nav_synth")
    out, info = SY.build_synth(d)
    return out, info


def test_synth_assets_and_gates(synth_mesh):
    out, info = synth_mesh
    assert NV.navmesh_available(out)
    m = NV.load_navmesh(out)
    assert m.n_floors == 2 and list(m.floor_code) == [0, 1]
    # 接続口=階段 1 本(W1 の階をまたぐ辺)・地上 0 → デッキ 1
    assert m.n_links == 1 and int(m.link_kind[0]) == NV.LINK_STAIRS
    assert int(m.floor_code[m.link_afi[0]]) == 0 and int(m.floor_code[m.link_bfi[0]]) == 1
    assert float(m.link_rise_m[0]) == pytest.approx(8.0 - 0.02 * 25.0, abs=0.2)
    # 島はつなぎの帯で地上の本体とつながる(W1 の n0–n5)
    st = info["stats"]
    assert st["w1_edges_split_component"] == 0
    assert st["area_m2_by_source"].get("bridge_w1", 0.0) > 0.0
    # 節は全部面の上に点がある
    assert int((m.anchor_run >= 0).sum()) == SY.NODES.shape[0]
    # セル面積の超過なし(第219)
    assert st["cells_over_cell_area"] == 0


def test_synth_build_twice_same_sha(synth_mesh, tmp_path):
    out, _ = synth_mesh
    out2, _ = SY.build_synth(tmp_path / "b")
    for f in NV.NAV1_FILES + (NV.NAV1_META,):
        assert _sha(out / f) == _sha(out2 / f), f


def test_synth_routes_inside_and_across_floors(synth_mesh):
    out, _ = synth_mesh
    m = NV.load_navmesh(out)
    a = SY.fake_assets()
    lc = np.full(m.n_links, 20.0)
    pl = NavPlanner(m, a.node_xy, a.edge_u, a.edge_v, a.edge_len_m, None, lc, lc)
    # L 字の角を回る(n0 → n2): 長さは角を回る 2 本の線分に近い
    r = pl.plan(m.anchor_x[0], m.anchor_y[0], int(m.anchor_fi[0]), 2, turn_w=50.0, climb_w=3.8)
    assert r is not None and (r.seg_link < 0).all()
    exact = math.hypot(146.0 - 7.0, 14.0 - 12.0) + math.hypot(148.0 - 146.0, 148.0 - 14.0)
    assert r.length_m <= exact * 1.02 + 1.0
    # 面の上(線分を 0.25 m ごとに見る)
    for k in range(r.pts.shape[0] - 1):
        p, q = r.pts[k], r.pts[k + 1]
        for t in np.linspace(0, 1, max(2, int(np.hypot(*(q - p)) / 0.25))):
            x, y = p + (q - p) * t
            assert any(m.locate(int(r.fi[k]), x + dx, y + dy) >= 0 for dx in (0, 1e-6, -1e-6) for dy in (0, 1e-6, -1e-6))
    # デッキへ(n0 → n4)は階段を通る
    r2 = pl.plan(m.anchor_x[0], m.anchor_y[0], int(m.anchor_fi[0]), 4, turn_w=50.0, climb_w=3.8)
    assert r2 is not None and int((r2.seg_link >= 0).sum()) == 1
    assert int(m.floor_code[r2.fi[-1]]) == 1
    # 3 つの候補の口(呼び手なし=J0 の形)
    c = pl.candidates(m.anchor_x[0], m.anchor_y[0], int(m.anchor_fi[0]), 2, turn_w=50.0, climb_w=3.8)
    assert set(c) == {"shortest", "fewer_turns", "less_climb"} and all(v is not None for v in c.values())


def test_cell_mapping_and_band_fallback(synth_mesh):
    out, _ = synth_mesh
    m = NV.load_navmesh(out)
    cix, ciy, cband = SY.cells()
    lut, cx0, cy0 = NV.cell_lookup_table(cix, ciy, cband)
    # デッキの点 (60, 17) はデッキのセル(4)・デッキのセルの無い列のデッキは地上のセル
    assert NV.cell_of(lut, cx0, cy0, 100.0, 60.0, 17.0, 1) == 4
    assert NV.cell_of(lut, cx0, cy0, 100.0, 160.0, 17.0, 1) == 1
    assert NV.cell_of(lut, cx0, cy0, 100.0, 500.0, 17.0, 0) == -1
    area = NV.area_by_cell(lut, cx0, cy0, 100.0, m.run_floor, m.run_row, m.run_x0, m.run_x1, m.floor_band,
                           m.floor_ox, m.floor_oy, m.res, 5)
    assert area.max() <= 100.0 * 100.0
    assert area.sum() == pytest.approx(float(((m.run_x1 - m.run_x0) * m.res * m.res).sum()))


# ------------------------------------------------------------------ 段 1 の検収の直し(M1・M3・問い 2)
def test_m1_function_2_3_are_trunk_first_and_9020_keeps_the_w1_copy():
    # 地物 1=国道(2)・2=都道(3)・3=不明(9020)・4=不明(9020)。W1 の写しは 1・1・1・2
    fk = np.array([1, 1, 1, 1, 2], dtype=np.int8)
    func = np.array([0, 2, 3, 9020, 9020])
    out = N1._function_first(fk, func)
    assert out.tolist() == [1, 2, 2, 1, 2]
    assert N1.TRUNK_FUNCTIONS == (2, 3)


def test_m3_mask_by_cells_removes_the_cell_less_squares_only():
    # 200 m × 100 m の格子(10 m の目)・セルは左の 100 m の升(地上)だけ
    lut, cx0, cy0 = NV.cell_lookup_table(np.array([0]), np.array([0]), np.array([0], dtype=np.int8))
    lab = np.full((10, 20), 12, dtype=np.uint8)  # つなぎの帯の札
    removed = np.zeros(len(NV.SOURCE_CODES) + 2, dtype=np.int64)
    lab[:, 15:] = 5  # 帯でない面(幹線の縁)
    N1._mask_by_cells(lab, 0.0, 0.0, 10.0, lut, cx0, cy0, 100.0, 0, removed, 7)
    assert (lab[:, :10] == 12).all() and (lab[:, 10:] == 0).all() and int(removed[12]) == 50 and int(removed[5]) == 50
    # つなぎの帯(bridge_w1)の札は切らない(最も近いセルへ倒す=M3 の親の判断)
    lab3 = np.full((10, 20), N1.BRIDGE_W1_LABEL, dtype=np.uint8)
    N1._mask_by_cells(lab3, 0.0, 0.0, 10.0, lut, cx0, cy0, 100.0, 0, removed, N1.BRIDGE_W1_LABEL)
    assert (lab3 == N1.BRIDGE_W1_LABEL).all()
    # デッキの層(1)はその層のセルが無ければ地上のセルへ倒す(11c の形)=左は残る
    lab2 = np.full((10, 20), 12, dtype=np.uint8)
    N1._mask_by_cells(lab2, 0.0, 0.0, 10.0, lut, cx0, cy0, 100.0, 1, removed, 7)
    assert (lab2[:, :10] == 12).all() and (lab2[:, 10:] == 0).all()


def test_m3_fill_nearest_maps_cell_less_squares_to_the_nearest_ground_cell():
    # 升 (0,0) と (3,0) にセル・(1,0)(2,0) は無い=近い方へ(同じ距離なら番号の小さい方)
    lut, cx0, cy0 = NV.cell_lookup_table(np.array([0, 3]), np.array([0, 0]), np.array([0, 0], dtype=np.int8),
                                         fill_nearest=True)
    assert [NV.cell_of(lut, cx0, cy0, 100.0, x, 50.0, 0) for x in (50.0, 150.0, 250.0, 350.0)] == [0, 0, 1, 1]
    raw, _a, _b = NV.cell_lookup_table(np.array([0, 3]), np.array([0, 0]), np.array([0, 0], dtype=np.int8))
    assert NV.cell_of(raw, cx0, cy0, 100.0, 150.0, 50.0, 0) == -1


def test_m3_synth_surface_is_inside_the_cells(synth_mesh):
    _out, info = synth_mesh
    assert info["stats"]["area_outside_cells_m2"] == 0.0


def test_b9_ramp_limit_is_1_12_and_1_8_under_16_cm():
    P = dict(N1.DEFAULT_PARAMS)
    assert P["ramp_max_grade"] == pytest.approx(1.0 / 12.0)
    R_, S_ = NV.LINK_RAMP, NV.LINK_STAIRS
    assert N1._ramp_or_stairs(P, R_, 1.0, 12.5) == R_       # 1/12.5 は歩く
    assert N1._ramp_or_stairs(P, R_, 1.0, 11.0) == S_       # 1/11 は階段
    assert N1._ramp_or_stairs(P, R_, 0.15, 1.3) == R_       # 15 cm・1/8.7 は歩く(16 cm 以下は 1/8)
    assert N1._ramp_or_stairs(P, R_, 0.15, 1.1) == S_       # 15 cm・1/7.3 は階段
    assert N1._ramp_or_stairs(P, R_, 0.20, 2.0) == S_       # 20 cm・1/10 は 1/12 を超える=階段
    assert N1._ramp_or_stairs(P, NV.LINK_ELEVATOR, 5.0, 1.0) == NV.LINK_ELEVATOR
