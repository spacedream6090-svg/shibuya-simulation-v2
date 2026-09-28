# -*- coding: utf-8 -*-
"""KDDI 写像の感度腕(在圏の形 9b・``tools/c7/attr_arms.py``)の検査(合成データ)。"""

from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pytest


@pytest.fixture(scope="module")
def aa():
    import attr_arms as _m

    return _m


def _toy_map(c7lib, toy_axes):
    """4 セル: 0=northwest / 1=northeast / 2=southwest / 3=southeast。"""
    ix = np.array([-3, 2, -3, 2])
    iy = np.array([2, 2, -3, -3])
    return c7lib.build_area_map(["gA_GL", "gB_GL", "gC_GL", "gD_GL"], ix, iy, toy_axes)


def _axes(aa, kind, home, work, school, age=None):
    n = len(kind)
    return aa.AgentAxes(kind=np.asarray(kind), age=np.asarray(age if age is not None else [30] * n),
                        home_area=np.asarray(home), work_area=np.asarray(work), school_area=np.asarray(school))


def test_area_map_is_resident_first_then_worker_then_visitor(aa, c7lib):
    nw, ne = c7lib.AREA_IDS.index("northwest"), c7lib.AREA_IDS.index("northeast")
    ax = _axes(aa, kind=[0, 3, 5, 1], home=[nw, nw, -1, -1], work=[nw, ne, -1, -1], school=[-1, -1, ne, -1])
    m = aa.attr_matrix(ax, "area")
    w, r, v = (c7lib.ATTR_IDS.index(a) for a in ("worker", "resident", "visitor"))
    assert m[0, nw] == r                    # 自宅 == 職場のエリア → 居住者(居住地優先)
    assert m[1, nw] == r and m[1, ne] == w  # 自宅エリアでは居住者・職場エリアでは勤務者
    assert m[2, ne] == w                    # 学校エリア → 勤務者(KDDI: 学生の勤務地=学校)
    assert m[2, nw] == v
    assert (m[3] == v).all()                # 軸なし(域外)→ どこでも来街者
    assert m[1, c7lib.AREA_IDS.index("central")] == v


def test_kind_maps_differ_only_for_students(aa, c7lib):
    base = aa.kind_to_attr_map("kind")
    sw = aa.kind_to_attr_map("kind_student_worker")
    assert base == dict(c7lib.KIND_TO_ATTR)
    assert {k for k in base if base[k] != sw[k]} == {aa.STUDENT_KIND}
    assert sw[aa.STUDENT_KIND] == "worker"
    with pytest.raises(ValueError):
        aa.kind_to_attr_map("area")


def test_dwell0_kind_arm_equals_the_engine_journal_formula(aa, c7lib, occ, toy_axes):
    """体の journal の既定腕(kind・滞在 0・20 歳未満を含む)= 種別 × セルの集計 → ``kind_cell_to_area_attr``。"""
    amap = _toy_map(c7lib, toy_axes)
    rng = np.random.default_rng(3)
    n, T = 40, 180
    kind = rng.integers(0, 9, n)
    cells = rng.integers(-1, 4, (T, n)).astype(np.int16)  # −1 = 舞台外
    ticks = np.arange(T)
    ax = _axes(aa, kind, [-1] * n, [-1] * n, [-1] * n)
    got = aa.area_attr_hour(ticks, cells, amap.area_of_cell, aa.attr_matrix(ax, "kind"))
    on = ticks[ticks % 60 == 0]
    kc = np.zeros((on.size, 9, 4), dtype=np.int64)
    for j, t in enumerate(on):
        ok = cells[t] >= 0
        np.add.at(kc[j], (kind[ok], cells[t][ok]), 1)
    want = aa.kind_journal_table(on, kc, amap, "kind")
    assert np.array_equal(got, want)
    assert got[3:].sum() == 0.0


def test_dwell30_needs_a_continuous_stay_inside_the_hour(aa):
    area_of_cell = np.array([0, 1])
    ticks = np.arange(120)  # 0 時と 1 時
    cells = np.full((120, 4), -1, dtype=np.int16)
    cells[0:30, 0] = 0      # 0 時に 30 分連続 → 数える
    cells[0:29, 1] = 0      # 29 分 → 数えない
    cells[0:20, 2] = 0
    cells[30:50, 2] = 0     # 20 + 20 分(途切れ)→ 数えない
    cells[50:90, 3] = 0     # 0 時に 10 分・1 時に 30 分(時間帯をまたぐ)→ 1 時だけ数える
    attr = np.zeros((4, 5), dtype=np.int64)
    got = aa.area_attr_hour(ticks, cells, area_of_cell, attr, dwell_min=30)
    assert got[0, 0, 0] == 1.0
    assert got[1, 0, 0] == 1.0
    assert got.sum() == 2.0
    snap = aa.area_attr_hour(ticks, cells, area_of_cell, attr, dwell_min=0)
    assert snap[0, 0, 0] == 3.0 and snap[1, 0, 0] == 1.0  # 正時の標本(0:00 と 1:00)だけを見る


def test_exclude_under20_drops_the_young(aa):
    area_of_cell = np.array([0])
    ticks = np.arange(60)
    cells = np.zeros((60, 3), dtype=np.int16)
    attr = np.zeros((3, 5), dtype=np.int64)
    keep = np.array([19, 20, 45]) >= aa.UNDER20_AGE
    assert aa.area_attr_hour(ticks, cells, area_of_cell, attr).sum() == 3.0
    assert aa.area_attr_hour(ticks, cells, area_of_cell, attr, keep=keep).sum() == 2.0
    assert aa.area_attr_hour(ticks, cells, area_of_cell, attr, keep=keep, dwell_min=30).sum() == 2.0


def test_shape_metrics_do_not_judge_and_leave_h1_blank(aa):
    rng = np.random.default_rng(0)
    t3 = rng.random((24, 5, 3)) + 0.1
    obs = {"peak_hour": {a: 18 for a in aa.AREA_IDS}, "night_residual": {a: 0.2 for a in aa.AREA_IDS},
           "area_share": {a: 0.2 for a in aa.AREA_IDS}, "attr_share": {a: [0.3, 0.1, 0.6] for a in aa.AREA_IDS}}
    m = aa.shape_metrics(t3, obs)
    assert m["H1"]["measured"] is False
    text = json.dumps(m, ensure_ascii=False)
    for word in ("pass", "fail", "verdict", "\"ok\""):
        assert word not in text
    assert m["H5"]["kddi_visitor_per_worker"] == pytest.approx(2.0)
    assert m["H5"]["floor_pt_visitor_per_worker"] == [0.16, 0.27]
    assert 0 <= m["H2"]["n_within_1h"] <= 5
    assert sum(m["sim_total_attr_share"]) == pytest.approx(1.0, abs=1e-3)
    assert aa.shape_metrics(t3, {})["H1"]["measured"] is False  # obs 無しでも sim の値は出る


def test_agent_axes_follow_rows_and_guard_the_row_rule(aa):
    area_of_cell = np.array([0, 1, -1])
    pop = SimpleNamespace(kind=np.array([3, 0]), age=np.array([15, 40]), home_cell=np.array([0, -1]),
                          work_cell=np.array([2, 1]), school_cell=np.array([-1, -1]))
    ax = aa.agent_axes(pop, area_of_cell, kind=np.array([3, 0, 8]))  # 母集団より 1 体多い
    assert ax.home_area.tolist() == [0, -1, -1]
    assert ax.work_area.tolist() == [-1, 1, -1]   # セル 2 は 5 エリア外 → −1
    assert ax.age.tolist() == [15, 40, 255]
    with pytest.raises(ValueError):
        aa.agent_axes(pop, area_of_cell, kind=np.array([0, 0]))


def test_recorder_restores_resolve_apply(aa):
    from shibuya.engine import resolve

    orig = resolve.apply
    rec = aa.AgentCellRecorder().attach()
    assert resolve.apply is not orig
    rec.detach()
    assert resolve.apply is orig


def test_kind_journal_rows_list_what_cannot_be_computed(aa, c7lib, occ, toy_axes, tmp_path, monkeypatch):
    amap = _toy_map(c7lib, toy_axes)
    kc = np.zeros((24, 9, 4), dtype=np.int32)
    kc[:, 5, 0] = 10  # 学生 10 体が northwest
    kc[:, 0, 1] = 5
    p = occ.write_journal(tmp_path / "j.npz", np.arange(24) * 60, kc.sum(axis=1), kc, tick_seconds=60, start_hour=0)
    doc = aa.kind_journal_rows(p, amap, {})
    rows = {r["attr_map"]: r for r in doc["rows"]}
    nw = c7lib.AREA_IDS.index("northwest")
    assert rows["kind"]["sim_attr_share"]["northwest"][c7lib.ATTR_IDS.index("visitor")] == 1.0
    assert rows["kind_student_worker"]["sim_attr_share"]["northwest"][c7lib.ATTR_IDS.index("worker")] == 1.0
    assert rows["kind"]["person_hours"] == 24 * 15
    assert len(doc["not_computable"]) == 3
    assert nw >= 0
