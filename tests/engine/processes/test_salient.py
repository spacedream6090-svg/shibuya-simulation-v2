"""顕著行為(人物③)と ``p_notice`` の結線のテスト。

正典: 知覚契約書 §3(人物③=B4 到達分)・§3.1(2 段ヒル型・80m 打ち切り・200/tick・A0-A4)・
§4 段2(顕著行為 上位1-2)・§6 起床条件 (i)。
"""

from __future__ import annotations

import numpy as np

from shibuya.agents.state import WakeCondition
from shibuya.core.types import EventClass
from shibuya.engine.processes.civic import PressProcess, PublicServiceDispatchProcess
from shibuya.engine.processes.salient import (
    ABLATION_IDS,
    SalientEvent,
    SalientProcess,
    _as_ablation,
    _cross_neighbours,
)
from shibuya.perception import attention as AT
from shibuya.perception import p_notice as PN

from .conftest import make_agents, make_world


def _proc(n_agents: int = 60, n_cells: int = 25, **kw):
    world = make_world(n_cells)
    agents, _ = make_agents(world, n_agents)
    return world, agents, SalientProcess(world, agents, master_seed=1, **kw)


# ================================================================= 近傍(80m の代用)
def test_cross_neighbours_are_the_four_orthogonal_cells():
    world = make_world(25)
    nb = _cross_neighbours(world)
    assert nb.shape == (25, 4)
    # 各セルは 2-4 個の隣接を持つ(端は -1)
    counts = (nb >= 0).sum(axis=1)
    assert counts.min() >= 2 and counts.max() == 4
    # 対称: a が b の隣なら b も a の隣
    for c in range(25):
        for d in nb[c][nb[c] >= 0]:
            assert c in set(nb[int(d)][nb[int(d)] >= 0].tolist())


def test_candidates_come_from_the_same_cell_and_its_neighbours():
    world, agents, sp = _proc()
    sp._index_cells()
    cell = int(agents.registry.cell[0])
    cand = sp._candidates(cell)
    cells = set(np.asarray(agents.registry.cell, dtype=np.int64)[cand].tolist())
    allowed = {cell} | {int(c) for c in sp._neighbours[cell] if c >= 0}
    assert cells <= allowed
    assert cand.size > 0


# ================================================================= 到達(p_notice)
def test_collapse_events_reach_someone_and_wake_them():
    world, agents, sp = _proc(n_agents=200, n_cells=16, rate_per_10k_per_day=5_000.0)
    seen = 0
    for t in range(200):
        sp.step(t)
        seen += sp.noticed_agents.size
        if sp.noticed_agents.size:
            a, cond, cls = sp.wake_candidates(t)
            assert a.size == sp.noticed_agents.size
            assert set(cond.tolist()) == {int(WakeCondition.CELL_BLOCK)}
            assert set(cls.tolist()) == {int(EventClass.CELL)}
    assert sp.n_collapse > 0
    assert seen > 0


def test_event_budget_caps_two_hundred_per_tick():
    world, agents, sp = _proc(n_agents=50, n_cells=9)
    sp.budget.start_tick(0)
    admitted = sum(1 for _ in range(PN.MAX_EVENTS_PER_TICK + 50) if sp.budget.admit(0))
    assert admitted == PN.MAX_EVENTS_PER_TICK
    assert sp.budget.counters.events_over_cap == 50


def test_ablation_ids_map_to_the_five_stages():
    assert len(ABLATION_IDS) == 5
    for k, name in enumerate(ABLATION_IDS):
        assert _as_ablation(name) == PN.Ablation(k)
        assert _as_ablation(f"A{k}") == PN.Ablation(k)
    assert _as_ablation(PN.Ablation.A4_SOCIAL) == PN.Ablation.A4_SOCIAL


def test_ablation_a0_uses_the_constant_reach():
    """A0(定数 0.54)では距離・向きに依らず約半数が気づく。"""
    world, agents, sp = _proc(
        n_agents=300, n_cells=9, ablation="A0", rate_per_10k_per_day=100_000.0
    )
    noticed = 0
    cand = 0
    for t in range(30):
        sp.step(t)
        noticed += sp.noticed_agents.size
    cand = sp.budget.counters.candidates
    assert cand > 0
    assert 0.2 * cand <= noticed <= 0.9 * cand


# ================================================================= B4 の行(段2)
def test_cell_lines_are_capped_by_the_stage_two_budget():
    world, agents, sp = _proc()
    sp.events = [
        SalientEvent("collapse", 0, (0.0, 0.0), "人が倒れている"),
        SalientEvent("police", 0, (0.0, 0.0), "救急・警察の隊が到着している", moving=True),
        SalientEvent("broadcast", 0, (0.0, 0.0), "〔素性: 放送〕運行情報"),
    ]
    lines = sp._build_cell_lines()
    assert 0 in lines
    assert len(lines[0]) == AT.BUDGET_SALIENT  # 上位 1-2(§4 段2)


def test_broadcasts_do_not_consume_the_salient_event_budget():
    """放送は人物③ではない: 200/tick の顕著イベント予算も p_notice も通さない。"""
    world, agents, sp = _proc(n_agents=40, n_cells=9)
    sp.press = PressProcess(world)
    minute = 7 * 60
    sp.step(minute)
    assert sp.n_broadcast_lines > 0
    assert sp.n_events == 0  # 顕著イベントは 0 件
    assert sp.noticed_agents.size == 0
    assert sp.cell_lines  # それでも B4 の行は出る


# ================================================================= 出動との連結
def test_a_collapse_triggers_a_dispatch_and_the_arrival_is_salient():
    world, agents, _ = _proc()
    d = PublicServiceDispatchProcess(world, master_seed=5)
    sp = SalientProcess(
        world, agents, master_seed=1, dispatch=d, rate_per_10k_per_day=100_000.0
    )
    kinds: set[str] = set()
    for t in range(120):
        sp.step(t)
        kinds |= {e.kind for e in sp.events}
    assert d.n_dispatched > 0
    assert "collapse" in kinds and "police" in kinds
    assert d.n_arrived > 0


# ================================================================= M12(2 byte/体)
def test_notice_state_is_two_bytes_per_agent_and_written_through_resolve():
    world, agents, sp = _proc(n_agents=32, n_cells=9)
    assert sp.pstate.declared_bytes_per_agent == 18  # heading 1 + task 1 + b2/b4 hash 16
    assert sp.pstate.frozen
    sp._update_notice_state()
    assert sp.pstate.frozen  # 窓は閉じて戻る
    assert sp.pstate.heading.dtype == np.uint8 and sp.pstate.task_flag.dtype == np.uint8


# ================================================================= 知覚済み(D-113 ②・第267)
def test_event_seen_tick_marks_everyone_in_the_event_cell_d113_2():
    """事象のセルに居た全員(B4 に行が出た体)の ``event_seen_tick`` がその tick になる。"""
    world, agents, sp = _proc(n_agents=200, n_cells=16, rate_per_10k_per_day=5_000.0)
    assert sp.event_seen_tick.shape == (200,) and int(sp.event_seen_tick.max()) == -1
    marked = False
    for t in range(200):
        sp.step(t)
        raw_cells = {int(ev.cell) for ev in sp.events if ev.kind != "broadcast"}
        if not raw_cells:
            continue
        cell = np.asarray(agents.registry.cell, dtype=np.int64)
        for c in raw_cells:
            occ = np.flatnonzero(cell == c)
            assert occ.size > 0 and np.all(sp.event_seen_tick[occ] == t)
            marked = True
            within = sp.event_seen_within(np.arange(200), t, 5)
            assert np.all(within[occ])
        others = np.flatnonzero(~np.isin(cell, sorted(raw_cells)))
        assert np.all(sp.event_seen_tick[others] < t)
    assert marked


def test_event_seen_within_uses_an_inclusive_window():
    world, agents, sp = _proc(n_agents=10, n_cells=4)
    sp.event_seen_tick[:] = -1
    sp.event_seen_tick[3] = 20
    got = sp.event_seen_within(np.array([3, 4]), 25, 5)
    assert got.tolist() == [True, False]
    assert sp.event_seen_within(np.array([3]), 26, 5).tolist() == [False]
