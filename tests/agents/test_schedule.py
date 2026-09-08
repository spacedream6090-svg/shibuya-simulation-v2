"""agents.schedule のテスト: T4(規模不変性)とカウンタベース抽選の同値性。"""

from __future__ import annotations

import numpy as np

from shibuya.agents import schedule as S


def test_bulk_and_per_agent_draws_are_identical():
    """一括生成(既定)と個体別 Philox(T4 の定義)が**バイト一致**すること。"""
    bulk = S.draw_words(1234, 64)
    per = S.draw_words_per_agent(1234, np.arange(64))
    assert np.array_equal(bulk, per)
    # 大きな添字でも同値(カウンタが 4 語ブロック境界に乗っている証拠)
    ids = np.array([0, 1, 999, 100_000, 399_999], dtype=np.int64)
    for aid in ids:
        one = S.draw_words(1234, 1, start_agent=int(aid))
        ref = S.draw_words_per_agent(1234, [int(aid)])
        assert np.array_equal(one, ref), aid


def test_t4_scale_invariance_5000_vs_5001():
    """運用設計書 §1.4 T4: n=5,000 と 5,001 で**既存個体の乱数列が不変**。"""
    a = S.synthesize(5_000, 42, n_cells=139)
    b = S.synthesize(5_001, 42, n_cells=139)
    for name in ("home_cell", "work_cell", "leisure_cell", "kind", "initial_money"):
        assert np.array_equal(getattr(a, name), getattr(b, name)[:5_000]), name
    assert np.array_equal(a.base_ticks, b.base_ticks[:5_000])
    assert np.array_equal(a.weekend_ticks, b.weekend_ticks[:5_000])


def test_different_seed_changes_the_schedule():
    a = S.synthesize(256, 1, n_cells=139)
    b = S.synthesize(256, 2, n_cells=139)
    assert not np.array_equal(a.base_ticks, b.base_ticks)


def test_boundaries_are_strictly_increasing_and_in_day():
    sc = S.synthesize(1_000, 7, n_cells=64)
    for arr in (sc.base_ticks, sc.weekend_ticks):
        assert arr.shape == (1_000, S.N_BOUNDARIES)
        assert np.all(np.diff(arr, axis=1) >= 1)
        assert arr.min() >= 0 and arr.max() <= 1_439


def test_cells_are_in_range():
    sc = S.synthesize(500, 3, n_cells=17)
    for name in ("home_cell", "work_cell", "leisure_cell"):
        arr = getattr(sc, name)
        assert arr.min() >= 0 and arr.max() < 17


def test_events_of_day_is_tick_sorted_and_complete():
    sc = S.synthesize(200, 5, n_cells=32)
    agent, slot, tick = sc.events_of_day(0)
    assert agent.size == 200 * S.N_BOUNDARIES
    assert np.all(np.diff(tick) >= 0)
    # 各個体が 5 境界ぶん現れる
    counts = np.bincount(agent, minlength=200)
    assert np.all(counts == S.N_BOUNDARIES)


def test_weekend_pattern_differs_and_day_index_wraps():
    sc = S.synthesize(64, 9, n_cells=32)
    assert not sc.is_weekend(0) and sc.is_weekend(5) and sc.is_weekend(6)
    assert not sc.is_weekend(7)
    assert not np.array_equal(sc.boundary_ticks(0), sc.boundary_ticks(5))
    assert np.array_equal(sc.target_cell(0), sc.work_cell)
    assert np.array_equal(sc.target_cell(5), sc.leisure_cell)


def test_empty_schedule():
    sc = S.synthesize(0, 1, n_cells=8)
    assert sc.base_ticks.shape == (0, S.N_BOUNDARIES)
    agent, slot, tick = sc.events_of_day(0)
    assert agent.size == 0
