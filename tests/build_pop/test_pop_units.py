"""build.pop の単体テスト: Shapefile 最小パーサ・点包含・床面積按分・IPF・二層抽出。

正典: 決定台帳「母集団合成」④ raking(SRMSE)・⑥ セル割当(建物床面積按分=D-W16)・
6-b 二層抽出(定員先取り層+統計層)。
"""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shibuya.agents.population import Population, sample_population
from shibuya.build.pop import fitting as F
from shibuya.build.pop import shapefile as SH
from shibuya.build.pop import w16_population as W


# ------------------------------------------------------------------ .shp/.dbf の書き出し
def _write_shp(path: Path, rings: list[list[tuple[float, float]]]) -> None:
    """shapeType 5(Polygon)・1 レコード 1 リングの最小 .shp を書く(テスト専用)。"""
    records = b""
    for i, ring in enumerate(rings, start=1):
        pts = np.asarray(ring, dtype=np.float64)
        body = struct.pack("<i", 5)
        body += struct.pack(
            "<4d",
            float(pts[:, 0].min()), float(pts[:, 1].min()),
            float(pts[:, 0].max()), float(pts[:, 1].max()),
        )
        body += struct.pack("<ii", 1, pts.shape[0])
        body += struct.pack("<i", 0)
        body += pts.astype("<f8").tobytes()
        records += struct.pack(">ii", i, len(body) // 2) + body
    file_len = (100 + len(records)) // 2
    head = struct.pack(">iiiiii", 9994, 0, 0, 0, 0, 0)
    head += struct.pack(">ii", file_len, 1000)
    head += struct.pack("<i", 5)
    allpts = np.concatenate([np.asarray(r, dtype=np.float64) for r in rings], axis=0)
    head += struct.pack(
        "<8d",
        float(allpts[:, 0].min()), float(allpts[:, 1].min()),
        float(allpts[:, 0].max()), float(allpts[:, 1].max()),
        0.0, 0.0, 0.0, 0.0,
    )
    path.write_bytes(head + records)


def _write_dbf(path: Path, fields: list[tuple[str, str, int, int]], rows: list[dict]) -> None:
    """dBASE III の最小 .dbf を書く(cp932・テスト専用)。"""
    header_len = 32 + 32 * len(fields) + 1
    rec_len = 1 + sum(f[2] for f in fields)
    head = bytes([0x03, 26, 9, 9]) + struct.pack("<IHH", len(rows), header_len, rec_len)
    head += b"\x00" * 20
    for name, typ, length, dec in fields:
        raw = name.encode("cp932")[:11]
        head += raw + b"\x00" * (11 - len(raw))
        head += typ.encode("ascii")
        head += b"\x00" * 4
        head += bytes([length, dec])
        head += b"\x00" * 14
    head += b"\x0D"
    body = b""
    for row in rows:
        body += b" "
        for name, typ, length, _dec in fields:
            val = str(row[name])
            enc = val.encode("cp932")[:length]
            body += (b" " * (length - len(enc))) + enc if typ == "N" else enc + b" " * (
                length - len(enc)
            )
    path.write_bytes(head + body + b"\x1A")


SQUARE = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
TRIANGLE = [(20.0, 0.0), (30.0, 0.0), (20.0, 10.0)]


def test_shapefile_roundtrip(tmp_path):
    """(a) テスト内で作った .shp/.dbf を自前パーサで読み戻せる。"""
    shp = tmp_path / "t.shp"
    dbf = tmp_path / "t.dbf"
    _write_shp(shp, [SQUARE, TRIANGLE])
    _write_dbf(
        dbf,
        [("KEY_CODE", "C", 11, 0), ("S_NAME", "C", 12, 0), ("JINKO", "N", 10, 0),
         ("AREA", "N", 15, 3)],
        [{"KEY_CODE": "13113001001", "S_NAME": "四角町", "JINKO": 120, "AREA": "100.000"},
         {"KEY_CODE": "13113001002", "S_NAME": "三角町", "JINKO": 30, "AREA": "50.000"}],
    )
    polys = SH.read_shp(shp)
    rows = SH.read_dbf(dbf)
    assert len(polys) == 2 and len(rows) == 2
    assert polys[0].n_rings == 1
    assert polys[0].points.shape == (4, 2)
    assert rows[0]["KEY_CODE"] == "13113001001"
    assert rows[0]["S_NAME"] == "四角町"  # cp932 の往復
    assert rows[0]["JINKO"] == 120
    assert rows[1]["AREA"] == pytest.approx(50.0)
    assert SH.polygon_area(polys[0]) == pytest.approx(100.0)
    assert SH.polygon_area(polys[1]) == pytest.approx(50.0)


def test_unsupported_shape_type_raises(tmp_path):
    """対応範囲外(点)は黙って読まずに例外(範囲の狭さを機械で保証)。"""
    shp = tmp_path / "p.shp"
    body = struct.pack("<i", 1) + struct.pack("<2d", 1.0, 2.0)
    head = struct.pack(">iiiiii", 9994, 0, 0, 0, 0, 0)
    head += struct.pack(">ii", (100 + 8 + len(body)) // 2, 1000)
    head += struct.pack("<i", 1) + struct.pack("<8d", *([0.0] * 8))
    shp.write_bytes(head + struct.pack(">ii", 1, len(body) // 2) + body)
    with pytest.raises(ValueError):
        SH.read_shp(shp)


def test_point_in_polygon_square():
    """(b) 点包含: 内・外・辺の外側。"""
    poly = SH.Polygon(np.zeros(1, dtype=np.int64), np.asarray(SQUARE), (0, 0, 10, 10))
    px = np.array([5.0, 15.0, 9.99, -0.01])
    py = np.array([5.0, 5.0, 5.0, 5.0])
    assert SH.points_in_polygon(px, py, poly).tolist() == [True, False, True, False]


def test_polygon_with_hole_excludes_inner_points():
    """穴つき(2 パート)は交差数の偶奇で内側が抜ける。"""
    outer = np.array([(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)])
    inner = np.array([(4.0, 4.0), (4.0, 6.0), (6.0, 6.0), (6.0, 4.0)])
    poly = SH.Polygon(
        np.array([0, 4], dtype=np.int64), np.concatenate([outer, inner]), (0, 0, 10, 10)
    )
    px = np.array([1.0, 5.0])
    py = np.array([1.0, 5.0])
    assert SH.points_in_polygon(px, py, poly).tolist() == [True, False]


@settings(max_examples=60, deadline=None)
@given(
    st.lists(st.floats(min_value=0.5, max_value=5000.0), min_size=1, max_size=40),
    st.integers(min_value=0, max_value=5000),
)
def test_property_largest_remainder_is_exact_and_monotone(weights, total):
    """(b) 床面積按分の性質: 合計が厳密・重みの大きい方が小さくならない。"""
    out = F.largest_remainder(weights, total)
    assert out.sum() == total
    assert (out >= 0).all()
    w = np.asarray(weights, dtype=np.float64)
    order = np.argsort(-w, kind="stable")
    got = out[order]
    # 同順位(同じ重み)を挟むと 1 だけ前後しうるので「1 を超える逆転が無い」を検査
    assert (np.diff(got.astype(np.int64)) <= 1).all()


@settings(max_examples=40, deadline=None)
@given(
    st.lists(st.floats(min_value=1.0, max_value=1e4), min_size=2, max_size=12),
    st.integers(min_value=1, max_value=2000),
)
def test_property_floor_apportionment_fills_every_cell(areas, total):
    """(b) 空セルの充填: 候補建物があるセルは必ず 1 体以上(合計は不変)。"""
    areas_arr = np.asarray(areas, dtype=np.float64)
    cells = np.arange(areas_arr.size, dtype=np.int64)  # 1 建物 1 セル(最も厳しい形)
    per = F.largest_remainder(areas_arr, total)
    fixed, moved = W._fill_empty_cells(per, cells)
    assert int(fixed.sum()) == total
    assert moved >= 0
    if total >= areas_arr.size:
        assert (fixed > 0).all(), (areas, total, fixed)


# ------------------------------------------------------------------ IPF
def test_ipf_hits_both_margins():
    """(c) IPF が行・列の周辺分布へ収束する。"""
    seed = np.array([[5.0, 1.0], [1.0, 5.0], [2.0, 2.0]])
    row = [100.0, 200.0, 300.0]
    col = [250.0, 350.0]
    res = F.ipf(seed, row, col)
    assert res.max_residual < 1e-9
    np.testing.assert_allclose(res.table.sum(axis=1), row, atol=1e-6)
    np.testing.assert_allclose(res.table.sum(axis=0), col, atol=1e-6)


def test_ipf_keeps_structural_zeros():
    """種の 0 セルは 0 のまま(実行可能な目標のとき周辺は厳密に一致する)。"""
    seed = np.array([[1.0, 0.0], [1.0, 1.0]])
    res = F.ipf(seed, [10.0, 30.0], [20.0, 20.0])
    assert res.max_residual < 1e-9
    assert res.table[0, 1] == pytest.approx(0.0)
    np.testing.assert_allclose(res.table.sum(axis=1), [10.0, 30.0], atol=1e-6)
    np.testing.assert_allclose(res.table.sum(axis=0), [20.0, 20.0], atol=1e-6)


def test_ipf_fills_rows_whose_seed_is_all_zero():
    """目標が正なのに種が全 0 の行は一様種で埋める(構造的ゼロと標本ゼロを区別できない)。"""
    seed = np.array([[1.0, 1.0], [0.0, 0.0]])
    res = F.ipf(seed, [10.0, 10.0], [10.0, 10.0])
    assert res.max_residual < 1e-9
    assert res.table[1].sum() == pytest.approx(10.0)


def test_ipf_rejects_mismatched_totals():
    with pytest.raises(ValueError):
        F.ipf(np.ones((2, 2)), [1.0, 1.0], [1.0, 5.0])


def test_srmse_matches_the_reference_definition():
    """SRMSE=sqrt(K·ΣΔ²)。性別(K=2)は片側 0.5 ポイントで 0.01 = 決定台帳のライン。"""
    assert F.srmse([1, 1], [1, 1]) == pytest.approx(0.0)
    assert F.srmse([50.5, 49.5], [50, 50]) == pytest.approx(0.01, abs=1e-9)
    assert F.srmse([100, 0], [50, 50]) > F.srmse([60, 40], [50, 50])


def test_jsd_is_zero_for_identical_and_one_for_disjoint():
    assert F.jsd([0.5, 0.5], [0.5, 0.5]) == pytest.approx(0.0)
    assert F.jsd([1.0, 0.0], [0.0, 1.0]) == pytest.approx(1.0)


# ------------------------------------------------------------------ 二層抽出
def _fake_population(n: int, n_duty: int = 40) -> Population:
    rng = np.random.default_rng(0)
    kind = rng.integers(0, 4, n).astype(np.int8)
    pool_layer = np.where(np.arange(n) < n_duty, 5, 1).astype(np.int8)
    kind[:10] = 4  # 指令(素材なし)
    pool_layer[:10] = 0
    z = np.zeros(n, dtype=np.int32)
    return Population(
        source=None,
        source_agent_id=np.arange(n, dtype=np.int64),
        kind=kind,
        purpose=np.zeros(n, dtype=np.int8),
        age=rng.integers(0, 90, n).astype(np.uint8),
        sex=rng.integers(0, 2, n).astype(np.int8),
        home_cell=z, work_cell=z, school_cell=z, direction_node=z,
        household_id=z, home_building=z, org_id=z,
        pool_layer=pool_layer, pool_index=z,
        synthetic=np.zeros(n, dtype=bool), is_foreign=np.zeros(n, dtype=bool),
    )


def test_two_stage_sampling_keeps_the_reserved_layer_whole():
    """(d) 定員先取り層(職務者+指令)は縮尺しない。"""
    pop = _fake_population(5_000, n_duty=40)
    reserved = int(pop.reserved_mask.sum())
    small = sample_population(pop, 500, seed=11)
    assert len(small) == 500
    assert int(small.reserved_mask.sum()) == reserved  # 1 体も落ちない
    assert reserved == 40  # プール層 L5(30)+ 指令(10)


def test_two_stage_sampling_is_stratified_and_deterministic():
    """(d) 統計層は (種別×年齢階級×性別) で比例配分・同 seed 同結果。"""
    pop = _fake_population(20_000, n_duty=100)
    a = sample_population(pop, 2_000, seed=7)
    b = sample_population(pop, 2_000, seed=7)
    c = sample_population(pop, 2_000, seed=8)
    assert np.array_equal(a.source_agent_id, b.source_agent_id)
    assert not np.array_equal(a.source_agent_id, c.source_agent_id)
    assert a.population_hash() == b.population_hash()
    assert a.population_hash() != c.population_hash()
    # 種別の構成比が保たれる(統計層のみで比較)
    full = pop.take(np.flatnonzero(~pop.reserved_mask))
    sub = a.take(np.flatnonzero(~a.reserved_mask))
    for k, cnt in full.counts_by_kind().items():
        share_full = cnt / full.n
        share_sub = sub.counts_by_kind().get(k, 0) / sub.n
        assert abs(share_full - share_sub) < 0.02, (k, share_full, share_sub)


def test_sampling_smaller_than_the_reserved_layer_takes_only_the_reserved():
    pop = _fake_population(1_000, n_duty=100)
    small = sample_population(pop, 20, seed=3)
    assert len(small) == 20
    assert bool(small.reserved_mask.all())


def test_sampling_more_than_available_returns_everything():
    pop = _fake_population(100, n_duty=10)
    assert sample_population(pop, 1_000, seed=1) is pop


def test_start_cell_falls_back_to_work_then_school():
    """域外常住の体は 勤務→通学→fallback の順で初期セルに置かれる。"""
    n = 4
    z = np.zeros(n, dtype=np.int32)
    pop = Population(
        source=None, source_agent_id=np.arange(n),
        kind=np.zeros(n, np.int8), purpose=np.zeros(n, np.int8),
        age=np.full(n, 30, np.uint8), sex=np.zeros(n, np.int8),
        home_cell=np.array([7, -1, -1, -1], np.int32),
        work_cell=np.array([-1, 3, -1, -1], np.int32),
        school_cell=np.array([-1, -1, 5, -1], np.int32),
        direction_node=z, household_id=z, home_building=z, org_id=z,
        pool_layer=np.ones(n, np.int8), pool_index=z,
        synthetic=np.zeros(n, bool), is_foreign=np.zeros(n, bool),
    )
    assert pop.start_cell(fallback=9).tolist() == [7, 3, 5, 9]
