# -*- coding: utf-8 -*-
"""在圏時系列(標本化・エリア集計・形状の量・journal)の検査。"""

from __future__ import annotations

import numpy as np
import pytest


def _toy_map(c7lib, toy_axes):
    """4 セル: 0=northwest / 1=northeast / 2=southwest / 3=southeast(格子中心で決まる)。"""
    ix = np.array([-3, 2, -3, 2])
    iy = np.array([2, 2, -3, -3])
    pids = ["gA_GL", "gB_GL", "gC_GL", "gD_GL"]
    return c7lib.build_area_map(pids, ix, iy, toy_axes)


def test_toy_map_is_one_cell_per_quadrant(c7lib, toy_axes):
    amap = _toy_map(c7lib, toy_axes)
    idx = {n: i for i, n in enumerate(c7lib.AREA_IDS)}
    assert amap.area_of_cell.tolist() == [
        idx["northwest"], idx["northeast"], idx["southwest"], idx["southeast"]
    ]


def test_by_area_and_hour_table(c7lib, toy_axes):
    amap = _toy_map(c7lib, toy_axes)
    ticks = np.array([0, 60, 120])                 # 0時 / 1時 / 2時
    counts = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]], dtype=np.int32)
    s = c7lib.OccupancySeries(ticks=ticks, cell_counts=counts)
    per_area = s.by_area(amap)
    assert per_area.shape == (3, 5)
    # central は空
    assert per_area[:, c7lib.AREA_IDS.index("central")].tolist() == [0, 0, 0]
    assert per_area[0, c7lib.AREA_IDS.index("northwest")] == 1
    tbl = s.area_hour_table(amap)
    assert tbl.shape == (24, 5)
    assert tbl[0, c7lib.AREA_IDS.index("northwest")] == 1.0
    assert tbl[2, c7lib.AREA_IDS.index("southeast")] == 12.0
    assert tbl[5].sum() == 0.0                      # 標本の無い時は 0


def test_hour_table_averages_repeated_hours(c7lib, toy_axes):
    """同じ時に複数標本(5分刻み)があれば平均する。"""
    amap = _toy_map(c7lib, toy_axes)
    ticks = np.array([0, 5, 10])
    counts = np.array([[2, 0, 0, 0], [4, 0, 0, 0], [6, 0, 0, 0]], dtype=np.int32)
    s = c7lib.OccupancySeries(ticks=ticks, cell_counts=counts)
    tbl = s.area_hour_table(amap)
    assert tbl[0, c7lib.AREA_IDS.index("northwest")] == pytest.approx(4.0)


def test_shape_quantities(c7lib):
    """時刻シェア・ピーク時刻・深夜残存率・エリア構成の定義を数値で固定する。"""
    tbl = np.zeros((24, 5))
    tbl[:, 0] = 1.0
    tbl[18, 0] = 10.0                                # central のピークは 18 時
    tbl[:, 1] = 2.0                                  # northwest は平坦
    share = c7lib.hour_share(tbl)
    assert share.shape == (5, 24)
    assert np.allclose(share[:2].sum(axis=1), 1.0)
    assert c7lib.peak_hours(share)[0] == 18
    # 平坦なら深夜残存率=1.0
    assert c7lib.night_residual(share)[1] == pytest.approx(1.0)
    # central は 18 時に集中する分、深夜は 1 未満
    assert c7lib.night_residual(share)[0] < 1.0
    comp = c7lib.area_share(tbl)
    assert comp.sum() == pytest.approx(1.0)
    assert comp[1] > comp[0] * 0.5


def test_kendall_tau_known(c7lib):
    assert c7lib.kendall_tau([1, 2, 3, 4], [1, 2, 3, 4]) == pytest.approx(1.0)
    assert c7lib.kendall_tau([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)


def test_kind_cell_to_area_attr(c7lib, occ, toy_axes):
    """種別×セル → エリア×属性(``KIND_TO_ATTR`` の写像が効く)。"""
    amap = _toy_map(c7lib, toy_axes)
    kc = np.zeros((1, 9, 4), dtype=np.int32)
    kc[0, 3, 0] = 7      # RESIDENT を northwest に 7
    kc[0, 0, 1] = 5      # COMMUTER(=worker)を northeast に 5
    kc[0, 7, 1] = 2      # FOREIGN_VISITOR(=visitor)を northeast に 2
    out = occ.kind_cell_to_area_attr(kc, amap)
    nw = c7lib.AREA_IDS.index("northwest")
    ne = c7lib.AREA_IDS.index("northeast")
    assert out[0, nw, c7lib.ATTR_IDS.index("resident")] == 7
    assert out[0, ne, c7lib.ATTR_IDS.index("worker")] == 5
    assert out[0, ne, c7lib.ATTR_IDS.index("visitor")] == 2


def test_counts_to_area_attr_matches(c7lib, toy_axes):
    amap = _toy_map(c7lib, toy_axes)
    cell = np.array([0, 0, 1, 3, -1])
    kind = np.array([3, 3, 0, 1, 3])
    out = c7lib.counts_to_area_attr(cell, kind, amap)
    assert out[c7lib.AREA_IDS.index("northwest"), c7lib.ATTR_IDS.index("resident")] == 2
    assert out[c7lib.AREA_IDS.index("northeast"), c7lib.ATTR_IDS.index("worker")] == 1
    assert out.sum() == 4                       # cell=-1 は落ちる


def test_journal_roundtrip(c7lib, occ, toy_axes, tmp_path):
    amap = _toy_map(c7lib, toy_axes)
    ticks = np.array([0, 60])
    counts = np.array([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=np.int32)
    kc = np.zeros((2, 9, 4), dtype=np.int32)
    kc[:, 3, 0] = counts[:, 0]
    p = occ.write_journal(tmp_path / "j.npz", ticks, counts, kc,
                          tick_seconds=60, start_hour=0, world_dir="toy")
    s = occ.load_journal(p, amap)
    assert s.ticks.tolist() == [0, 60]
    assert s.cell_counts.tolist() == counts.tolist()
    assert s.area_attr is not None
    assert s.meta["world_dir"] == "toy"
    doc = s.to_json(amap)
    assert doc["area_ids"] == list(c7lib.AREA_IDS)
    assert len(doc["area_hour_counts"]) == 24
    assert len(doc["area_hour_share"]) == 5


def test_series_cell_count_mismatch_raises(c7lib, toy_axes):
    amap = _toy_map(c7lib, toy_axes)
    s = c7lib.OccupancySeries(ticks=np.array([0]), cell_counts=np.zeros((1, 3), dtype=np.int32))
    with pytest.raises(ValueError, match="セル数が違う"):
        s.by_area(amap)


# ---------------------------------------------------------------- 記録器


class _FakeCells:
    def __init__(self, density):
        self.density = density


class _FakeWorld:
    def __init__(self, density):
        self.cells = _FakeCells(density)


class _FakeRegistry:
    def __init__(self, cell, kind):
        self.cell = cell
        self.kind = kind


class _FakeAgents:
    def __init__(self, cell, kind):
        self.registry = _FakeRegistry(cell, kind)


class _FakeResolveModule:
    """``engine.resolve`` の代わり(``apply`` だけ持つ)。"""

    def __init__(self):
        self.calls: list[int] = []

        def apply(plan_confirmed, losers, agents, world, tick, **kw):
            self.calls.append(int(tick))
            return "outcome"

        self.apply = apply


def test_recorder_samples_every_and_restores(occ):
    """``every`` の倍数だけ標本化し、detach で元の ``apply`` に戻る。"""
    mod = _FakeResolveModule()
    original = mod.apply
    world = _FakeWorld(np.array([1, 2, 3, 4], dtype=np.int32))
    agents = _FakeAgents(np.array([0, 1, 1, 3]), np.array([3, 0, 1, 3]))
    rec = occ.OccupancyRecorder(every=2)
    rec.attach(mod)
    assert mod.apply is not original
    for tick in range(6):
        out = mod.apply(None, None, agents, world, tick)
        assert out == "outcome"
    rec.detach()
    assert mod.apply is original
    assert rec.ticks == [0, 2, 4]
    assert mod.calls == list(range(6))            # 呼び出しは素通し(順序も回数も同じ)
    counts = rec.cell_counts()
    assert counts.shape == (3, 4)
    kc = rec.kind_cell_counts()
    assert kc.shape == (3, 9, 4)
    assert int(kc[0].sum()) == 4                  # 4 体ぶん


def test_recorder_context_manager_restores_on_error(occ):
    mod = _FakeResolveModule()
    original = mod.apply
    rec = occ.OccupancyRecorder(every=1)
    try:
        with rec.attach(mod):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert mod.apply is original


def test_recorder_does_not_write_world(occ):
    """標本化は**読み取りだけ**(密度配列の同一性・内容が変わらない)。"""
    mod = _FakeResolveModule()
    density = np.array([1, 2, 3, 4], dtype=np.int32)
    world = _FakeWorld(density)
    agents = _FakeAgents(np.array([0, 1]), np.array([3, 3]))
    rec = occ.OccupancyRecorder(every=1).attach(mod)
    mod.apply(None, None, agents, world, 0)
    rec.detach()
    assert world.cells.density is density
    assert density.tolist() == [1, 2, 3, 4]
    # 標本は複製(あとで density が変わっても標本は動かない)
    density[:] = 0
    assert rec.cell_counts()[0].tolist() == [1, 2, 3, 4]
