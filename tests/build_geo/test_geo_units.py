"""build.geo の純粋ヘルパの単体テスト(データ不要)。

対象: 層バンド写像・ノード層の多数決・格子添字と place_id・kind 既定高さ表・
高さ規則(D-W5)・ヘッダのハッシュ規約・pendant 除去・CSR 構築・多角形の面積。
"""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

from shibuya.build.geo import common as C
from shibuya.build.geo import w1_walk_graph as W1
from shibuya.build.geo import w2_cells as W2
from shibuya.build.geo import w3_distances as W3
from shibuya.build.geo import w4_heights as W4


# --- 層バンド(D-W3)------------------------------------------------------------------


@pytest.mark.parametrize(
    "layer,band",
    [(-2, "UG"), (-1, "UG"), (None, "GL"), (0, "GL"), (1, "DECK"), (2, "DECK")],
)
def test_band_of_layer(layer, band):
    assert C.band_of_layer(layer) == band


def test_band_of_layer_rejects_unknown():
    with pytest.raises(ValueError):
        C.band_of_layer(3)


def test_node_layer_majority_plain():
    assert C.node_layer_from_incident([1, 1, 0]) == 1
    assert C.node_layer_from_incident([]) == 0


def test_node_layer_majority_tie_prefers_zero():
    # 同数なら 0 を優先
    assert C.node_layer_from_incident([0, 1]) == 0
    # -2 と 1 が同数(2)で 0 は候補外 → |layer| 最小の 1
    assert C.node_layer_from_incident([-2, 0, 1, -2, 1]) == 1
    # 0 が最多なら 0
    assert C.node_layer_from_incident([0, 0, 1, -2]) == 0


def test_node_layer_majority_tie_without_zero_takes_smallest_abs():
    assert C.node_layer_from_incident([1, -2]) == 1
    assert C.node_layer_from_incident([2, -1]) == -1
    # |layer| が同じなら値の小さい方
    assert C.node_layer_from_incident([1, -1]) == -1


# --- 格子・place_id(D-W2)-------------------------------------------------------------


def test_grid_ij_floor_semantics():
    assert C.grid_ij(0.0, 0.0) == (0, 0)
    assert C.grid_ij(99.9, 100.0) == (0, 1)
    assert C.grid_ij(-0.1, -100.0) == (-1, -1)
    assert C.grid_ij(-100.1, 250.0) == (-2, 2)


def test_place_id_format():
    assert C.place_id(-3, 7, "GL") == "g-3_7_GL"


def test_latlon_to_local_origin_and_scale():
    x, y = C.latlon_to_local(*C.ORIGIN_LATLON)
    assert (abs(x), abs(y)) == (0.0, 0.0)
    # 経度スケール = 111320*cos(原点緯度)
    x1, _ = C.latlon_to_local(C.ORIGIN_LATLON[0], C.ORIGIN_LATLON[1] + 1.0)
    assert math.isclose(x1, 111320.0 * math.cos(math.radians(C.ORIGIN_LATLON[0])))
    _, y1 = C.latlon_to_local(C.ORIGIN_LATLON[0] + 1.0, C.ORIGIN_LATLON[1])
    assert math.isclose(y1, C.M_PER_DEG_LAT)


# --- 高さ規則(D-W5)------------------------------------------------------------------


def test_kind_default_table_covers_v8_kinds():
    v8_kinds = {"house?", "generic", "residential", "retail", "office", "public", "station", "hotel"}
    assert v8_kinds <= set(W4.KIND_DEFAULT_FLOORS)


def test_kind_default_h_is_floors_times_3():
    for kind, floors in W4.KIND_DEFAULT_FLOORS.items():
        assert W4.kind_default_h(kind) == round(floors * W4.H_FLOOR_M, 1)
    assert W4.kind_default_h("未知の kind") == W4.KIND_DEFAULT_FALLBACK_FLOORS * W4.H_FLOOR_M


def test_height_rule_priority():
    # PLATEAU が最優先
    assert W4.height_of("office", 10, 40.04) == (40.0, "plateau")
    # levels は 2 以外のときだけ
    assert W4.height_of("office", 7, None) == (21.0, "levels")
    assert W4.height_of("office", 2, None) == (15.0, "kind_default")
    assert W4.height_of("house?", None, None) == (6.0, "kind_default")


# --- ハッシュ・ヘッダ(§0-1)----------------------------------------------------------


def test_canonical_json_is_key_sorted_and_compact():
    assert C.canonical_json_bytes({"b": 1, "a": [1, 2]}) == b'{"a":[1,2],"b":1}'


def test_param_hash_is_order_independent():
    assert C.param_hash({"a": 1, "b": 2}) == C.param_hash({"b": 2, "a": 1})
    assert C.param_hash({"a": 1}) != C.param_hash({"a": 2})


def test_input_hash_is_order_dependent(tmp_path):
    p1 = tmp_path / "a.bin"
    p2 = tmp_path / "b.bin"
    p1.write_bytes(b"one")
    p2.write_bytes(b"two")
    h12 = C.input_hash([p1, p2])
    h21 = C.input_hash([p2, p1])
    assert h12 != h21
    assert h12 == C.input_hash([p1, p2])
    assert len(h12) == 64


def test_gate_to_json_pass_semantics():
    assert C.Gate("g", 3, 3).to_json()["pass"] is True
    assert C.Gate("g", 3, 4).to_json()["pass"] is False
    # expected=None は「報告のみ」= 常に pass
    assert C.Gate("g", 3, None).to_json()["pass"] is True


def test_write_parquet_is_byte_stable(tmp_path):
    cols = {"a": np.arange(5, dtype=np.int32), "b": ["x", "y", "z", "w", "v"]}
    d1 = tmp_path / "one"
    d2 = tmp_path / "two"
    d1.mkdir()
    d2.mkdir()
    r1 = C.write_parquet(d1, "t.parquet", cols)
    r2 = C.write_parquet(d2, "t.parquet", cols)
    assert r1["sha256"] == r2["sha256"]
    assert r1["rows"] == 5


def test_stage_result_header_roundtrip(tmp_path):
    res = C.StageResult(
        stage="W9",
        stage_version="0.1.0",
        input_hash="0" * 64,
        param_hash="1" * 64,
        params={"k": 1},
        gates=[C.Gate("g", 1, 1)],
        catalog_classes=["建物"],
    )
    path = C.write_header(tmp_path, res)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["stage"] == "W9"
    assert payload["gates"]["g"] == {"value": 1, "expected": 1, "pass": True}
    assert payload["catalog_classes"] == ["建物"]
    assert res.all_passed


# --- W1 pendant 除去 --------------------------------------------------------------------


def test_prune_pendants_removes_chain_keeps_cycle():
    # 三角形 0-1-2 に 2-3-4 の枝がぶら下がる
    edges = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4)]
    alive_n, alive_e = W1.prune_pendants(5, edges)
    assert alive_n == {0, 1, 2}
    assert alive_e == {0, 1, 2}
    assert W1.count_components(alive_n, edges, alive_e) == 1


def test_prune_pendants_dissolves_tree():
    edges = [(0, 1), (1, 2)]
    alive_n, alive_e = W1.prune_pendants(3, edges)
    assert alive_n == set()
    assert alive_e == set()


def test_count_components_two_islands():
    edges = [(0, 1), (2, 3)]
    # 生きているのはエッジ0だけ → {0,1} が1成分・2 と 3 が孤立で計3
    assert W1.count_components({0, 1, 2, 3}, edges, {0}) == 3
    assert W1.count_components({0, 1, 2, 3}, edges, {0, 1}) == 2


# --- W2 多角形 --------------------------------------------------------------------------


def test_ring_stats_unit_square():
    pts = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    area, per, cx, cy = W2._ring_stats(pts)
    assert area == pytest.approx(1.0)
    assert per == pytest.approx(4.0)
    assert (cx, cy) == pytest.approx((0.5, 0.5))
    # 逆回りは負の面積(=外面の判定に使う)
    assert W2._ring_stats(pts[::-1])[0] == pytest.approx(-1.0)


def test_face_traversal_on_single_triangle():
    # 三角形1つ: 有界面1 + 外面1 = 2
    pts = {0: (0.0, 0.0), 1: (1.0, 0.0), 2: (0.0, 1.0)}
    half: list[tuple[int, int, int]] = []
    starts: list[np.ndarray] = []
    for e, (u, v) in enumerate([(0, 1), (1, 2), (2, 0)]):
        half.append((u, v, e))
        starts.append(np.array(pts[v]) - np.array(pts[u]))
        half.append((v, u, e))
        starts.append(np.array(pts[u]) - np.array(pts[v]))
    faces = W2._face_traversal(3, half, starts)
    assert len(faces) == 2
    assert sorted(len(f) for f in faces) == [3, 3]


# --- W3 CSR ------------------------------------------------------------------------------


def test_build_csr_dedups_parallel_edges_with_min_length():
    u = np.array([0, 0, 1, 2])
    v = np.array([1, 1, 2, 2])  # (0,1) が平行辺・(2,2) は自己ループ
    w = np.array([10.0, 4.0, 7.0, 1.0])
    indptr, indices, weights = W3.build_csr(3, u, v, w)
    assert indices.shape[0] == 4  # 無向2本 → 有向4弧
    arcs = {(a, int(indices[k]), float(weights[k])) for a in range(3) for k in range(indptr[a], indptr[a + 1])}
    assert arcs == {(0, 1, 4.0), (1, 0, 4.0), (1, 2, 7.0), (2, 1, 7.0)}
