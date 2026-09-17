"""C9c-1 歩行可能面積の実測化(``tools/build_geo/walkable_area.py``)の検収。

正典
- ``docs/research/v2-c9-geometry-capacity-research.md`` **§2-1 S1〜S7**(入力→計算→出力列・
  ゲート 3 つ)・§1-1 a1〜a3(道路構造令の既定幅員)・a9(区の歩道部総面積 897,556 m²)。
- ``docs/design/v2-c9-geometry-agenda.md`` §6「C9c の範囲」(G8 (b))。

検査する 10 点
  (i) クリップは面積を保存する(正方形を 4 セルに跨がせる)/ (ii) 三角形の一意化 /
  (iii) function コードの抽出 / (iv) 幅員規則の表が法定値どおり / (v) S7 ゲート関数 /
  (vi) 折れ線のセル分割 / (vii) 環の一意化(LOD3 が同じ三角形を 6 回持つ)/
  (viii) セル単位の LOD マージ / (ix) 被覆率の分母(道路面の全幅)/
  (x) 実データ(``-m slow``: 答申 a8/a9 の再現・ゲート 3 つ・物理検査)。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

_REPO = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "shibuya_tools_walkable_area", _REPO / "tools" / "build_geo" / "walkable_area.py"
)
assert _SPEC is not None and _SPEC.loader is not None
WA = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = WA
_SPEC.loader.exec_module(WA)

WORLD = _REPO / "data" / "world" / "v2"
PLATEAU = _REPO / "data" / "plateau"
GML = (
    _REPO / "data" / "realworld" / "plateau_2025"
    / "13113_shibuya-ku_pref_2025_citygml_1_op" / "udx" / "tran"
)

#: 答申 §1-1 a8(地物数)・a9(面積[m²])。**生 GML から地物単位で数えた値**
#: (= ``--ring-dedup none --lod-merge feature``)。
ADVISORY_FEATURE_COUNTS = {"1000": 3461, "1020": 1900, "2000": 3505, "3000": 622}
ADVISORY_AREA_M2 = {"2000": 897_556.0, "1000": 1_643_132.0, "1020": 394_352.0, "3000": 57_996.0}
#: 答申 a8「LOD3 幾何を持つのは 歩道部 791・車道部 1,151(+Aux 1)・車道交差部 631」。
ADVISORY_LOD3_COUNTS = {"2000": 791, "1000": 1152, "1020": 631}


# ================================================================ (i) クリップ
def test_clip_preserves_area_across_four_cells():
    """セル境界(100 m)にまたがる 200×200 m の正方形 → 4 セルに 10,000 m² ずつ。"""
    square = [(0.0, 0.0), (200.0, 0.0), (200.0, 200.0), (0.0, 200.0)]
    total = 0.0
    for cx in (0, 1):
        for cy in (0, 1):
            piece = WA.clip_polygon_to_rect(
                square, cx * 100.0, cy * 100.0, (cx + 1) * 100.0, (cy + 1) * 100.0
            )
            area = WA.polygon_area(piece)
            assert area == pytest.approx(10_000.0)
            total += area
    assert total == pytest.approx(WA.polygon_area(square))


def test_triangle_cell_areas_conserve_the_total():
    """三角形の集合をセルに割り振っても合計は動かない(跨ぐものも含む)。"""
    rng = np.random.default_rng(0)
    tri = rng.uniform(-150.0, 250.0, size=(300, 3, 2))
    x, y = tri[:, :, 0], tri[:, :, 1]
    raw = 0.5 * np.abs(
        (x[:, 1] - x[:, 0]) * (y[:, 2] - y[:, 0]) - (x[:, 2] - x[:, 0]) * (y[:, 1] - y[:, 0])
    )
    got = WA.triangle_cell_areas(tri)
    assert sum(got.values()) == pytest.approx(float(raw.sum()), rel=1e-9)
    # 跨ぐ三角形がちゃんと居る(= 遅い道が働いた)ことも確かめる
    assert len(got) > 4


def test_triangle_straddling_one_boundary_splits_in_half():
    tri = np.array([[[90.0, 0.0], [110.0, 0.0], [90.0, 20.0]]])
    got = WA.triangle_cell_areas(tri)
    assert set(got) == {(0, 0), (1, 0)}
    assert sum(got.values()) == pytest.approx(200.0)


# ================================================================ (ii) 一意化
def test_unique_triangle_mask_folds_repeated_faces():
    """PLATEAU の npz は同じ面を 2〜6 回持つ(S1「1 地物 1 LOD=二重計上しない」)。"""
    t = np.array(
        [
            [[0, 0], [10, 0], [0, 10]],
            [[10, 0], [0, 10], [0, 0]],  # 同じ三角形(頂点順だけ違う)
            [[0, 0], [20, 0], [0, 20]],
        ]
    )
    mask = WA.unique_triangle_mask(t)
    assert mask.tolist() == [True, False, True]


# ================================================================ (iii)(iv) 表
def test_function_codes_follow_the_plateau_codelist():
    """2000 歩道部 / 2010 自転車歩行者道 / 2020 歩道 と 1000 車道部 / 1020 車道交差部。"""
    assert WA.SIDEWALK_FUNCTION_CODES == (2000, 2010, 2020)
    assert WA.ROADWAY_FUNCTION_CODES == (1000, 1020)


def test_width_rules_match_the_road_structure_ordinance():
    """道路構造令 11 条 3 項 2.0 m / 10 条の 2 2 項 3.0 m / 5 条 5 項 4.0 m(答申 §1-1)。"""
    for klass in ("footway", "pedestrian", "path", "corridor"):
        assert WA.width_for_klass(klass) == (2.0, "doro11-3_sidewalk_2.0")
    assert WA.width_for_klass("cycleway") == (3.0, "doro10-2-2_cycleped_3.0")
    for klass in ("residential", "service", "unclassified"):
        assert WA.width_for_klass(klass)[0] == 4.0
    for klass in ("tertiary", "secondary", "primary"):
        assert WA.width_for_klass(klass) == (4.0, "doro11-3_sidewalk_both_2x2.0")
    assert WA.width_for_klass("steps")[0] == 1.5
    assert WA.width_for_klass("elevator")[0] == 0.0
    # 表に無い klass は歩道の下限へ落ちる(現データでは 1 本も落ちない)
    assert WA.width_for_klass("未知の道")[0] == 2.0


# ================================================================ (vi) 折れ線
def test_polyline_cell_lengths_split_on_cell_boundaries():
    got = WA.polyline_cell_lengths(np.array([[10.0, 50.0], [310.0, 50.0]]))
    assert sorted(got) == [(0, 0), (1, 0), (2, 0), (3, 0)]
    assert got[(0, 0)] == pytest.approx(90.0)
    assert got[(1, 0)] == pytest.approx(100.0)
    assert got[(3, 0)] == pytest.approx(10.0)
    assert sum(got.values()) == pytest.approx(300.0)


def test_polyline_cell_lengths_handles_diagonals():
    got = WA.polyline_cell_lengths(np.array([[0.0, 0.0], [200.0, 200.0]]))
    assert sum(got.values()) == pytest.approx(float(np.hypot(200.0, 200.0)))
    assert set(got) == {(0, 0), (1, 1)}


# ================================================================ (v) S7 ゲート
def test_gate_values_pass_on_synthetic_numbers():
    side = np.array([2_000.0, 1_500.0, 0.0, 0.0])
    road = np.array([3_000.0, 3_500.0, 0.0, 0.0])
    walk = np.array([2_000.0, 1_500.0, 1_200.0, 900.0])
    legacy = np.array([5_000.0, 5_000.0, 1_500.0, 1_500.0])
    covered = side > 0.0
    g = WA.gate_values(side, road, walk, legacy, covered)
    assert g["i"]["value"] == pytest.approx(1.0)
    assert g["i"]["pass"] and g["i"]["n_cells"] == 2
    assert g["ii"]["value"] == pytest.approx(0.135)
    assert g["ii"]["pass"]
    assert g["iii"]["value"] == pytest.approx(3_500.0)
    assert g["iii"]["pass"]


def test_gate_iii_fails_above_the_district_total():
    side = np.array([WA.DISTRICT_SIDEWALK_TOTAL_M2 + 1.0])
    g = WA.gate_values(side, side * 0.0, side, side, side > 0.0)
    assert not g["iii"]["pass"]


def test_gate_ii_fails_when_the_median_leaves_the_band():
    walk = np.array([10.0, 12.0, 14.0])  # 0.001 前後 = 0.05 未満
    g = WA.gate_values(walk * 0.0, walk * 0.0, walk, np.full(3, 1_500.0), np.zeros(3, bool))
    assert not g["ii"]["pass"]


# ================================================================ (vii) 実データ
@pytest.mark.slow
@pytest.mark.skipif(
    not (WORLD / "c9c_walkable_area.parquet").exists(), reason="C9c-1 資産が無い"
)
def test_real_asset_header_records_the_three_gates():
    """出荷済み資産のヘッダに S7 の 3 ゲートが値つきで載っている。"""
    import pyarrow.parquet as pq

    header = json.loads((WORLD / "c9c_walkable_area.header.json").read_text(encoding="utf-8"))
    gates = header["gates"]
    assert set(gates) == {
        "S7_i_plateau_vs_legacy_ratio_median",
        "S7_ii_walkable_fraction_median",
        "S7_iii_plateau_sidewalk_total_m2",
    }
    assert all(g["pass"] for g in gates.values())
    assert gates["S7_iii_plateau_sidewalk_total_m2"]["value"] <= WA.DISTRICT_SIDEWALK_TOTAL_M2

    assert header["params"]["source"] == "gml"
    assert header["params"]["ring_dedup"] == "exact"
    assert header["params"]["lod_merge"] == "cell"
    assert header["params"]["covered_min_frac"] == WA.DEFAULT_COVERED_MIN_FRAC
    assert header["notes"]["n_cells_over_cell_area"] == 0

    t = pq.read_table(WORLD / "c9c_walkable_area.parquet").to_pydict()
    assert list(t) == [
        "cell_id", "band", "walkable_m2", "plateau_sidewalk_m2",
        "plateau_roadway_m2", "osm_walkable_m2", "width_rule", "source",
    ]
    assert len(t["cell_id"]) == 520
    assert set(t["source"]) <= {"plateau", "osm", "mixed"}
    assert min(t["walkable_m2"]) > 0.0


# ================================================================ (vii) 環の一意化
def test_unique_rings_folds_repeated_and_reversed_rings():
    """渋谷区 2025 の LOD3 TrafficArea は**同じ三角形を 6 回**持つ(実測)。"""
    r = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
    out = WA._unique_rings([(r, 1)] * 6 + [(r[::-1].copy(), 1), (r * 2.0, 1)])
    assert len(out) == 2
    assert WA.signed_ring_area(out[0][0]) == pytest.approx(0.5)


def test_unique_rings_keeps_holes_apart_from_the_same_outer_ring():
    """符号が違えば別物(外環と同じ形の穴は畳まない)。"""
    r = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    assert len(WA._unique_rings([(r, 1), (r, -1)])) == 2


# ================================================================ (viii) LOD マージ
def test_merge_cell_areas_by_lod_prefers_lod3_per_cell():
    per_lod = {3: {(0, 0): 10.0}, 2: {(0, 0): 4.0, (1, 0): 7.0}, 1: {(2, 0): 3.0}}
    assert WA.merge_cell_areas_by_lod(per_lod, "cell") == {(0, 0): 10.0, (1, 0): 7.0, (2, 0): 3.0}
    assert WA.merge_cell_areas_by_lod(per_lod, "feature") == {
        (0, 0): 14.0, (1, 0): 7.0, (2, 0): 3.0
    }
    with pytest.raises(ValueError):
        WA.merge_cell_areas_by_lod(per_lod, "polygon")


def test_lod_merge_modes_and_ring_dedup_modes():
    assert WA.LOD_MERGE_MODES == ("cell", "feature")
    assert WA.RING_DEDUP_MODES == ("exact", "none")
    assert WA.LOD_PREFERENCE == (3, 2, 1)
    assert WA.SOURCE_MODES == ("gml", "npz")


# ================================================================ (ix) 被覆率の分母
def test_road_surface_width_follows_the_lane_width_table():
    """道路構造令 第五条第4項(第四種第一級 3.25 / 第二級・第三級 3.0)+ 第十一条第3項 2.0×2。"""
    assert WA.road_surface_width_for_klass("primary") == pytest.approx(3.25 * 2 + 2.0 * 2)
    assert WA.road_surface_width_for_klass("secondary") == pytest.approx(3.0 * 2 + 2.0 * 2)
    assert WA.road_surface_width_for_klass("tertiary") == pytest.approx(3.0 * 2 + 2.0 * 2)
    # 歩車共存の細街路は車道全幅がそのまま道路面(第五条第5項)
    assert WA.road_surface_width_for_klass("residential") == 4.0
    # 歩行者専用路は歩行可能幅員と同じ(車道が無い)
    for klass in ("footway", "pedestrian", "path", "corridor", "cycleway", "steps", "elevator"):
        assert WA.road_surface_width_for_klass(klass) == WA.width_for_klass(klass)[0]
    assert WA.road_surface_width_for_klass("未知の道") == 4.0
    # 道路面 >= 歩行可能面(分母が分子より小さくならない)
    for klass in WA.WIDTH_RULES:
        assert WA.road_surface_width_for_klass(klass) >= WA.width_for_klass(klass)[0]


def test_default_covered_min_frac_is_declared():
    """被覆の 2 条件の既定(親決定 2026-09-17): 被覆率 ≥ 0.5 かつ 歩道率 ≥ 0.15。

    歩道率 0.15 は「PLATEAU が車道しか持たないセル(歩車共存)は OSM 側の推定へ倒す」
    ための線。0.0 に戻すと ``g2_1_GL`` が 0.40 m² になり ρ=22 人/m² で詰まる。
    """
    assert WA.DEFAULT_COVERED_MIN_FRAC == 0.5
    assert WA.DEFAULT_SIDEWALK_MIN_SHARE == 0.15


# ================================================================ (x) 実データ
@pytest.mark.slow
@pytest.mark.skipif(not GML.exists(), reason="PLATEAU 生 GML が無い")
def test_gml_reader_reproduces_the_advisory_counts_and_areas():
    """答申 a8(地物数・LOD3 の内訳)と a9(区全域の面積)を**地物単位の数え方**で再現する。"""
    crs = json.loads((WORLD / "world_crs.json").read_text(encoding="utf-8"))
    origin = (float(crs["origin_latlon"][0]), float(crs["origin_latlon"][1]))
    mdeg = (float(crs["m_per_deg_lat"]), float(crs["m_per_deg_lon"]))
    _, stats = WA.read_gml_features(GML, origin, mdeg, ring_dedup="none")
    assert stats["n_files"] == 30
    assert stats["n_features_by_code"] == ADVISORY_FEATURE_COUNTS
    assert stats["n_features_without_geometry"] == 0
    for code, n in ADVISORY_LOD3_COUNTS.items():
        assert stats["lod_used_by_code"][code]["3"] == n
    for code, want in ADVISORY_AREA_M2.items():
        got = stats["area_m2_by_code_feature_sum"][code]
        assert abs(got - want) <= 1.0, (code, got, want)
    # 2010 自転車歩行者道 / 2020 歩道 は渋谷区の GML に 1 件も無い
    assert set(stats["n_features_by_code"]) == {"1000", "1020", "2000", "3000"}
    # LOD2 は ``tran_*``・LOD3 は ``traf_*`` の別 ID = 「1 地物 1 LOD」では重なりが落ちない
    assert set(stats["gml_id_prefix_by_lod"]["2"]) == {"tran"}
    assert set(stats["gml_id_prefix_by_lod"]["3"]) == {"traf"}


@pytest.mark.slow
@pytest.mark.skipif(not GML.exists(), reason="PLATEAU 生 GML が無い")
def test_ring_dedup_removes_the_sixfold_repetition():
    """LOD3 の環は 6 重。畳むと環数も面積も減る(答申の 897,556 m² は重複込み)。"""
    crs = json.loads((WORLD / "world_crs.json").read_text(encoding="utf-8"))
    origin = (float(crs["origin_latlon"][0]), float(crs["origin_latlon"][1]))
    mdeg = (float(crs["m_per_deg_lat"]), float(crs["m_per_deg_lon"]))
    _, raw = WA.read_gml_features(GML, origin, mdeg, ring_dedup="none")
    _, ded = WA.read_gml_features(GML, origin, mdeg, ring_dedup="exact")
    assert ded["n_rings"] < raw["n_rings"]
    assert ded["n_features_with_repeated_rings"] > 0
    # 歩道部 LOD3 は重複が特に大きい(LOD2 は 1 面 1 環なので変わらない)
    assert ded["area_m2_by_code_lod"]["2000/lod2"] == pytest.approx(
        raw["area_m2_by_code_lod"]["2000/lod2"]
    )
    assert ded["area_m2_by_code_lod"]["2000/lod3"] < raw["area_m2_by_code_lod"]["2000/lod3"]


@pytest.mark.slow
@pytest.mark.skipif(not GML.exists(), reason="PLATEAU 生 GML が無い")
def test_build_is_deterministic_and_refuses_to_overwrite(tmp_path):
    res1 = WA.build(PLATEAU, WORLD, tmp_path)
    res2 = WA.build(PLATEAU, WORLD, tmp_path / "again")
    assert res1["output"]["sha256"] == res2["output"]["sha256"]
    with pytest.raises(FileExistsError):
        WA.build(PLATEAU, WORLD, tmp_path)


@pytest.mark.slow
@pytest.mark.skipif(not GML.exists(), reason="PLATEAU 生 GML が無い")
def test_default_build_has_no_cell_above_its_own_area(tmp_path):
    """**物理検査**: 100 m セルに 10,000 m² を超える道路面は入らない。

    既定(``ring_dedup=exact`` + ``lod_merge=cell``)では 0 セル。答申と同じ数え方
    (``none`` + ``feature``)では 32 セルが超える=重複計上の物証。
    """
    fixed = WA.build(PLATEAU, WORLD, tmp_path / "fixed")
    assert fixed["notes"]["n_cells_over_cell_area"] == 0
    raw = WA.build(
        PLATEAU, WORLD, tmp_path / "raw", ring_dedup="none", lod_merge="feature"
    )
    assert raw["notes"]["n_cells_over_cell_area"] > 0


@pytest.mark.slow
@pytest.mark.skipif(not (PLATEAU / "tran_lod3.npz").exists(), reason="PLATEAU npz が無い")
def test_npz_source_still_builds(tmp_path):
    """``--source npz``(GML の無い環境用)も動く。値は LOD3 + clip_rect の部分集合。"""
    res = WA.build(PLATEAU, WORLD, tmp_path, source="npz")
    assert res["notes"]["face_source_stats"]["mode"] == "npz"
    assert res["output"]["rows"] == 520
