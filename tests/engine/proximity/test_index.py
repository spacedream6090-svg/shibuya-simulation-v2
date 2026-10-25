"""第 2 期 2-2 段 11a: 近傍の索引 ``engine.spatial_index.SpatialIndex``(アジェンダ §2-1「近傍の列挙は総当たりと一致」)。

- ``pairs(d)`` は総当たりと一致する(重なった点・格子の境の点・負の座標を含む 600 点・d=1.0/2.0/2.5/10.3・各組 1 回)。
- 層(band)が違う組は列挙しない。
- ``within``・``query_many`` も総当たりと一致する(自分を除く・距離の境を含む)。
- B5 の単位の在室(``unit_members``・``unit_counts``)。
- 総当たりの比べ方は旧記録(proximity-edge-2026-09-30)の 600 点と同じ作り(781 組・2 m)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.engine.spatial_index import SpatialIndex


def _points() -> np.ndarray:
    rng = np.random.default_rng(7)
    return np.concatenate([
        rng.uniform(-30, 30, (400, 2)),                          # 一様 400
        np.repeat(rng.uniform(-30, 30, (20, 2)), 5, axis=0),    # 同じ点 5 体 × 20
        np.column_stack([np.arange(100) * 2.0 - 100.0 + 1e-9, np.zeros(100)]),  # 2 m 間隔の格子の境 100
    ]).astype(np.float32)                                        # SoA と同じ float32


def _brute(pts: np.ndarray, band: np.ndarray, d: float) -> set[tuple[int, int]]:
    x = pts.astype(np.float64)
    i, j = np.triu_indices(len(pts), 1)
    dd = np.sqrt(((x[i] - x[j]) ** 2).sum(axis=1))
    ok = (dd <= d) & (band[i] == band[j])
    return {(int(a), int(b)) for a, b in zip(i[ok].tolist(), j[ok].tolist())}


@pytest.mark.parametrize("d", [1.0, 2.0, 2.5, 10.3])
def test_pairs_match_bruteforce_600_points(d):
    pts = _points()
    band = np.zeros(len(pts), dtype=np.int8)
    idx = SpatialIndex.build(pts, band)
    A, B = idx.pairs(d)
    got = {(min(a, b), max(a, b)) for a, b in zip(A.tolist(), B.tolist())}
    assert len(got) == len(A)                                   # 各組 1 回(重複なし)
    assert got == _brute(pts, band, d)
    if d == 2.0:
        assert len(got) == 781                                  # 旧記録の 600 点の検算と同じ数


def test_pairs_never_cross_bands():
    pts = _points()
    band = np.random.default_rng(3).integers(-1, 2, len(pts)).astype(np.int8)
    idx = SpatialIndex.build(pts, band)
    A, B = idx.pairs(2.0)
    got = {(min(a, b), max(a, b)) for a, b in zip(A.tolist(), B.tolist())}
    assert got == _brute(pts, band, 2.0)
    assert all(band[a] == band[b] for a, b in got)
    same_xy_other_band = SpatialIndex.build(np.zeros((2, 2), np.float32), np.array([0, 1], np.int8))
    assert same_xy_other_band.pairs(2.0)[0].size == 0           # 同じ座標でも層が違えば組にしない


@pytest.mark.parametrize("d", [1.0, 2.0, 10.3])
def test_within_and_query_many_match_bruteforce(d):
    pts = _points()
    band = np.zeros(len(pts), dtype=np.int8)
    idx = SpatialIndex.build(pts, band)
    x = pts.astype(np.float64)
    for i in range(0, len(pts), 13):
        want = np.flatnonzero((np.sqrt(((x - x[i]) ** 2).sum(axis=1)) <= d) & (np.arange(len(pts)) != i))
        assert np.array_equal(idx.within(i, d), want)
    q = np.arange(0, len(pts), 29)
    qi, ids, dist = idx.query_many(x[q, 0], x[q, 1], band[q], d)
    for k, i in enumerate(q.tolist()):
        want = set(np.flatnonzero(np.sqrt(((x - x[i]) ** 2).sum(axis=1)) <= d).tolist())
        assert set(ids[qi == k].tolist()) == want               # 点から引く=自分も入る(外すのは呼び手)
    assert np.all(dist <= d)


def test_subset_ids_and_point_queries():
    pts = np.array([[0, 0], [1, 0], [0, 1.5], [3, 0], [100, 100]], dtype=np.float32)
    band = np.zeros(5, dtype=np.int8)
    idx = SpatialIndex.build(pts, band, ids=np.array([0, 1, 3]), n_total=5)
    assert len(idx) == 3 and idx.pos.tolist() == [idx.pos[0], idx.pos[1], -1, idx.pos[3], -1]
    assert idx.within(0, 2.0).tolist() == [1]                   # 体 2 は索引の外
    assert idx.within(2, 2.0).tolist() == []                    # 索引に無い体は空
    assert idx.within(2, 2.0, xy=(0.0, 1.5), band=0).tolist() == [0, 1]   # 点から引けば引ける
    assert idx.within(0, 3.0).tolist() == [1, 3]                # 境 3.0 ちょうどを含む


def test_unit_members_and_counts():
    pts = np.zeros((6, 2), np.float32)
    unit = np.array([-1, 4, 4, 9, 4, -1])
    idx = SpatialIndex.build(pts, np.zeros(6, np.int8), unit=unit)
    assert idx.unit_members(4).tolist() == [1, 2, 4]
    assert idx.unit_members(-1).tolist() == []
    assert sorted(idx.unit_counts().tolist()) == [1, 3]


def test_keys_out_of_range_are_refused():
    with pytest.raises(ValueError):
        SpatialIndex.build(np.array([[1e13, 0.0]]), np.zeros(1, np.int8))


def test_index_is_read_only_after_build():
    """検収 L3: 索引の配列は読み取り専用・欄の付け替えと消すのは断る。"""
    idx = SpatialIndex.build(np.zeros((3, 2), np.float32), np.zeros(3, np.int8))
    for name in ("ids", "x", "y", "bands", "unit", "key", "pos"):
        with pytest.raises(ValueError):
            getattr(idx, name)[0] = 1
    with pytest.raises(AttributeError):
        idx.x = np.zeros(3)
    with pytest.raises(AttributeError):
        del idx.ids


def test_unit_members_many_matches_single():
    unit = np.array([-1, 4, 4, 9, 4, -1, 9])
    idx = SpatialIndex.build(np.zeros((7, 2), np.float32), np.zeros(7, np.int8), unit=unit)
    w, ids = idx.unit_members_many([4, -1, 9, 7])
    got = {k: sorted(ids[w == k].tolist()) for k in range(4)}
    assert got == {0: [1, 2, 4], 1: [], 2: [3, 6], 3: []}
