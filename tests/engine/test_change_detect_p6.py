"""engine.change_detect のテスト+**予算行 P6 の実測**(≤2 ms/tick@40万体)。

P6 の行: 「変化検出(セルB2/B4ハッシュ再計算+個体B5閾値判定・起床条件(i)(ii)の検出器)
**≤2 ms/tick@40万体・139セル**(ベクトル化・逐次ループなし)」。
セル数は実装計画書 §3 の **453**(「xxhash で 453 回」)で回して報告する
(139/453/520 の食い違いは ``world.assets`` の docstring に記録)。
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from shibuya.agents.state import AgentState, WakeCondition
from shibuya.core.types import EventClass
from shibuya.engine import change_detect as CD
from shibuya.world.state import World


def _consistent_stages(agents: AgentState) -> None:
    for value_field, stage_field in CD.INTERO_VARS:
        v = agents.registry.field(value_field)
        stage = np.zeros(agents.n, dtype=np.int8)
        for e in CD.INTERO_UP_EDGES:
            stage += (v >= e).astype(np.int8)
        agents.registry.field(stage_field)[:] = stage


def _seed_world(n_agents: int, n_cells: int, seed: int = 7):
    w = World.synthetic(n_cells=n_cells, seed=seed)
    a = AgentState(n_agents)
    rng = np.random.default_rng(seed)
    a.registry.cell[:] = rng.integers(0, n_cells, size=n_agents)
    for f in ("hunger", "fatigue", "thermal"):
        a.registry.field(f)[:] = rng.integers(0, 11, size=n_agents)
    _consistent_stages(a)
    w.cells.density[:] = w.compute_density(a.registry.cell)
    return w, a, rng


# ---------------------------------------------------------------- 正しさ
def test_b4_hash_matches_full_recompute():
    """差分だけ再ハッシュしても、全行を計算し直した値と一致する。"""
    w, a, rng = _seed_world(500, 32)
    det = CD.ChangeDetector(a.n, w.n_cells)
    hashes = np.zeros(w.n_cells, dtype=np.uint64)
    for tick in range(5):
        w.cells.density[:] = rng.integers(0, 500, size=w.n_cells)
        res = det.detect(w, a, tick)
        hashes[res.changed_cells] = res.changed_b4_hash
        full = CD.b4_block_hashes(CD.b4_block_raw(w, tick))
        assert np.array_equal(hashes, full), tick


def test_unchanged_cells_are_not_reported():
    w, a, _ = _seed_world(100, 16)
    det = CD.ChangeDetector(a.n, w.n_cells)
    det.detect(w, a, 0)
    res = det.detect(w, a, 1)
    assert res.changed_cells.size == 0
    assert res.cell_wake_agents.size == 0


def test_cell_wake_agents_are_exactly_those_in_changed_cells():
    w, a, _ = _seed_world(300, 16)
    det = CD.ChangeDetector(a.n, w.n_cells)
    det.detect(w, a, 0)
    w.cells.density[3] = 5_000  # 段を跨がせる
    res = det.detect(w, a, 1)
    assert res.changed_cells.tolist() == [3]
    expected = np.flatnonzero(a.registry.cell == 3)
    assert np.array_equal(res.cell_wake_agents, expected)


def test_agents_outside_the_world_are_never_woken_by_cells():
    w, a, _ = _seed_world(50, 8)
    a.registry.cell[:10] = -1
    det = CD.ChangeDetector(a.n, w.n_cells)
    det.detect(w, a, 0)
    w.cells.density[0] = 9_999
    res = det.detect(w, a, 1)
    assert np.all(res.cell_wake_agents >= 10) or res.cell_wake_agents.size == 0


def test_numba_kernel_matches_numpy_reference():
    w, a, _ = _seed_world(2_000, 32)
    mask = np.zeros(w.n_cells, dtype=np.bool_)
    mask[[1, 5, 9]] = True
    o1 = np.empty(a.n, dtype=np.int64)
    o2 = np.empty(a.n, dtype=np.int64)
    k1 = CD._CELL_WAKE(a.registry.cell, mask, o1)
    k2 = CD._cell_wake_numpy(a.registry.cell, mask, o2)
    assert k1 == k2 and np.array_equal(o1[:k1], o2[:k2])


def test_interoception_hysteresis_has_no_oscillation():
    """閾値ちょうどを往復しても、ヒステリシス帯の内側では段が動かない。"""
    w = World.synthetic(n_cells=4, seed=1)
    a = AgentState(1)
    a.registry.cell[:] = 0
    a.registry.hunger[:] = 4  # 上げ閾値ちょうど → 段 1
    _consistent_stages(a)
    det = CD.ChangeDetector(1, w.n_cells)
    det.detect(w, a, 0)
    # 3(= 4-1 のヒステリシス帯)では下がらない
    a.registry.hunger[:] = 3
    res = det.detect(w, a, 1)
    assert res.crossings[0].agent_id.size == 0
    # 2 まで落ちれば段 0 へ
    a.registry.hunger[:] = 2
    res = det.detect(w, a, 2)
    assert res.crossings[0].agent_id.tolist() == [0]
    assert res.crossings[0].new_stage.tolist() == [0]


def test_interoception_up_crossing():
    w = World.synthetic(n_cells=4, seed=1)
    a = AgentState(3)
    a.registry.cell[:] = 0
    a.registry.fatigue[:] = [0, 6, 8]
    _consistent_stages(a)
    det = CD.ChangeDetector(3, w.n_cells)
    det.detect(w, a, 0)
    a.registry.fatigue[:] = [4, 7, 9]
    res = det.detect(w, a, 1)
    fatigue = res.crossings[1]
    assert fatigue.stage_field == "fatigue_stage"
    assert fatigue.agent_id.tolist() == [0, 1, 2]
    assert fatigue.new_stage.tolist() == [1, 2, 3]


def test_candidates_have_condition_and_class():
    w, a, _ = _seed_world(100, 8)
    det = CD.ChangeDetector(a.n, w.n_cells)
    det.detect(w, a, 0)
    w.cells.density[1] = 9_999
    a.registry.hunger[:] = 10
    res = det.detect(w, a, 1)
    agent, cond, cls = res.candidates()
    assert agent.size == cond.size == cls.size
    assert set(cond.tolist()) <= {int(WakeCondition.INTEROCEPTION), int(WakeCondition.CELL_BLOCK)}
    intero = cond == int(WakeCondition.INTEROCEPTION)
    assert np.all(cls[intero] == int(EventClass.INDIVIDUAL))
    assert np.all(cls[~intero] == int(EventClass.CELL))
    # 条件番号の昇順 → 個体 id の昇順(挿入順に依存しない)
    assert np.all(np.diff(cond.astype(np.int64)) >= 0)


def test_detector_does_not_write_to_state():
    """検出器は**書かない**(resolve が唯一の書き手)。"""
    w, a, _ = _seed_world(200, 16)
    a.freeze()
    w.freeze()
    det = CD.ChangeDetector(a.n, w.n_cells)
    det.detect(w, a, 0)  # 凍結したままでも例外が出ない = 書いていない
    w.thaw()
    w.cells.density[2] = 9_999
    w.freeze()
    det.detect(w, a, 1)


# ---------------------------------------------------------------- P6 実測
def _p6_run(n_agents: int, n_cells: int, frac_cells: float, frac_agents: float, ticks: int = 100):
    w, a, rng = _seed_world(n_agents, n_cells, seed=11)
    det = CD.ChangeDetector(n_agents, n_cells)
    det.detect(w, a, 0)  # numba のコンパイルとバッファの温め
    cell_wakes = []
    t0 = time.perf_counter()
    for tick in range(1, ticks + 1):
        k = int(n_cells * frac_cells)
        if k:
            idx = rng.choice(n_cells, size=k, replace=False)
            w.cells.density[idx] = rng.integers(0, 1_200, size=k)
        if frac_agents:
            ai = rng.choice(n_agents, size=int(n_agents * frac_agents), replace=False)
            a.registry.hunger[ai] = rng.integers(0, 11, size=ai.size)
        res = det.detect(w, a, tick)
        for c in res.crossings:  # resolve 相当の書き戻し(定常状態を保つ)
            if c.agent_id.size:
                a.registry.field(c.stage_field)[c.agent_id] = c.new_stage.astype(np.int8)
        cell_wakes.append(res.cell_wake_agents.size)
    ms = (time.perf_counter() - t0) / ticks * 1_000
    return ms, int(np.mean(cell_wakes))


@pytest.mark.slow
def test_p6_change_detection_under_2ms_at_400k_agents():
    """予算行 P6: 40万体×453セル・100 tick の平均 ≤2 ms/tick。"""
    n_agents, n_cells = 400_000, 453
    rows = []
    for label, fc, fa in (
        ("定常(変化なし)", 0.0, 0.0),
        ("セル10%変化", 0.10, 0.0),
        ("セル10%+個体1%跨ぎ", 0.10, 0.01),
    ):
        ms, wakes = _p6_run(n_agents, n_cells, fc, fa)
        rows.append((label, ms, wakes))
    print(f"\n[P6] {n_agents:,}体 × {n_cells}セル × 100 tick "
          f"(numba カーネル={CD.CELL_WAKE_USES_NUMBA})")
    for label, ms, wakes in rows:
        print(f"  {label:22s} {ms:6.3f} ms/tick  (セル起床 {wakes:,}/tick)")
    worst = max(ms for _, ms, _ in rows)
    assert worst <= 2.0, f"P6 超過: {worst:.3f} ms/tick > 2 ms"


def test_p6_scaled_down_runs_in_ci():
    """CI 用の縮小版(4万体×453セル)。絶対値ゲートは slow 側。"""
    ms, wakes = _p6_run(40_000, 453, 0.10, 0.01, ticks=20)
    print(f"\n[P6 縮小] 40,000体×453セル: {ms:.3f} ms/tick (セル起床 {wakes}/tick)")
    assert ms <= 2.0
