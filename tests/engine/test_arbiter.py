"""engine.arbiter のテスト: 4クラス固定優先・合流・昇格(starvation-free)・縮退・不応期。

正典: 知覚契約書 §6(繰り延べの優先規則 A案)・予算宣言表 §7-5(診断行4列)・L4。
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shibuya.agents.state import N_WAKE_CONDITIONS, WakeCondition
from shibuya.core.types import EventClass
from shibuya.engine.arbiter import (
    DEGRADE_COST_FACTOR,
    T_MAX_TICKS,
    Arbiter,
    WakeCandidates,
    arbitrate,
    call_budget_per_tick,
)
from shibuya.engine.scheduler import DIAG_COLUMNS

SALT = b"\x01\x02\x03\x04"

_COND_OF_CLASS = {
    int(EventClass.CONVERSATION): int(WakeCondition.CONVERSATION_TURN),
    int(EventClass.PLAN_BOUNDARY): int(WakeCondition.PLAN_GENERAL),
    int(EventClass.INDIVIDUAL): int(WakeCondition.INTEROCEPTION),
    int(EventClass.CELL): int(WakeCondition.CELL_BLOCK),
}


def _cands(agents, classes, since=0) -> WakeCandidates:
    agents = np.asarray(agents, dtype=np.int64)
    classes = np.asarray(classes, dtype=np.int64)
    cond = np.asarray([_COND_OF_CLASS[int(c)] for c in classes], dtype=np.int8)
    since = np.full(agents.size, since, dtype=np.int64) if np.isscalar(since) else np.asarray(since, dtype=np.int64)
    return WakeCandidates(agents, cond, classes, since)


def _permute(c: WakeCandidates, rng) -> WakeCandidates:
    idx = rng.permutation(len(c))
    return c.take(idx)


# ---------------------------------------------------------------- 予算(L4)
def test_l4_budget_arithmetic():
    """4,000,000 呼/日 ÷ 1,440 tick × n/400,000。5,000 体で 34.72 呼/tick=10 呼/体/日。"""
    assert call_budget_per_tick(400_000) == pytest.approx(4_000_000 / 1_440)
    b = call_budget_per_tick(5_000)
    assert b == pytest.approx(34.7222, rel=1e-4)
    assert b * 1_440 / 5_000 == pytest.approx(10.0)


# ---------------------------------------------------------------- 固定優先
def test_fixed_class_priority_beats_arrival_order():
    """会話 > 計画境界 > 個体変化 > セル変化(到着順ではない)。"""
    c = _cands([10, 11, 12, 13], [EventClass.CELL, EventClass.INDIVIDUAL,
                                   EventClass.PLAN_BOUNDARY, EventClass.CONVERSATION])
    d = arbitrate(c, tick=0, budget=2, run_salt=SALT)
    assert d.selected.agent_id.tolist() == [13, 12]
    assert d.selected_eff_class.tolist() == [0, 1]


def test_within_class_waiting_time_descending():
    c = _cands([1, 2, 3], [EventClass.PLAN_BOUNDARY] * 3, since=[8, 5, 9])
    d = arbitrate(c, tick=10, budget=2, run_salt=SALT)
    # 待ち: 3→1, 1→2, 2→5 … 降順 = agent 2(5) → agent 1(2)
    assert d.selected.agent_id.tolist() == [2, 1]


# ---------------------------------------------------------------- 純関数・並び順不変
def test_permuting_candidates_does_not_change_the_outcome():
    rng = np.random.default_rng(0)
    agents = rng.permutation(40)
    classes = rng.integers(0, 4, size=40)
    since = rng.integers(-20, 1, size=40)
    c = _cands(agents, classes, since)
    base = arbitrate(c, tick=0, budget=9, run_salt=SALT)
    for _ in range(20):
        d = arbitrate(_permute(c, rng), tick=0, budget=9, run_salt=SALT)
        assert d.selected.agent_id.tolist() == base.selected.agent_id.tolist()
        assert d.selected_degraded.tolist() == base.selected_degraded.tolist()
        assert np.array_equal(d.diag, base.diag)
        assert sorted(d.deferred.agent_id.tolist()) == sorted(base.deferred.agent_id.tolist())


@settings(max_examples=50, deadline=None)
@given(
    n=st.integers(min_value=0, max_value=60),
    budget=st.floats(min_value=0.0, max_value=40.0),
    seed=st.integers(min_value=0, max_value=10_000),
)
def test_arbitrate_is_a_pure_function(n, budget, seed):
    rng = np.random.default_rng(seed)
    c = _cands(rng.permutation(max(1, n))[:n], rng.integers(0, 4, size=n),
               rng.integers(-30, 1, size=n))
    a = arbitrate(c, tick=3, budget=budget, run_salt=SALT)
    b = arbitrate(c, tick=3, budget=budget, run_salt=SALT)
    assert a.selected.agent_id.tolist() == b.selected.agent_id.tolist()
    assert np.array_equal(a.diag, b.diag)
    assert len(a.selected) + len(a.deferred) + len(a.suppressed) + int(
        a.merged_per_class.sum()
    ) == n


# ---------------------------------------------------------------- 合流(§6 運用規定②)
def test_same_agent_multiple_conditions_merge_into_one_call():
    c = WakeCandidates(
        np.array([7, 7, 7], dtype=np.int64),
        np.array(
            [int(WakeCondition.CELL_BLOCK), int(WakeCondition.INTEROCEPTION),
             int(WakeCondition.PLAN_GENERAL)], dtype=np.int8
        ),
        np.array([int(EventClass.CELL), int(EventClass.INDIVIDUAL),
                  int(EventClass.PLAN_BOUNDARY)], dtype=np.int64),
        np.zeros(3, dtype=np.int64),
    )
    d = arbitrate(c, tick=0, budget=10, run_salt=SALT)
    assert d.n_calls == 1
    # 最上位クラス(計画境界)の代表が残る
    assert int(d.selected.class_rank[0]) == int(EventClass.PLAN_BOUNDARY)
    assert int(d.merged_per_class.sum()) == 2


# ---------------------------------------------------------------- 昇格(starvation-free)
def test_promotion_after_t_max():
    tmax = T_MAX_TICKS[int(EventClass.CELL)]
    c = _cands([1], [EventClass.CELL], since=[0])
    assert arbitrate(c, tick=tmax - 1, budget=10, run_salt=SALT).selected_eff_class.tolist() == [3]
    assert arbitrate(c, tick=tmax, budget=10, run_salt=SALT).selected_eff_class.tolist() == [2]
    assert arbitrate(c, tick=3 * tmax, budget=10, run_salt=SALT).selected_eff_class.tolist() == [0]


def test_promotion_is_counted_as_an_event_not_as_a_state():
    tmax = T_MAX_TICKS[int(EventClass.CELL)]
    c = _cands([1], [EventClass.CELL], since=[0])
    row = DIAG_COLUMNS.index("promoted")
    assert int(arbitrate(c, tick=tmax, budget=10, run_salt=SALT).diag[row].sum()) == 1
    assert int(arbitrate(c, tick=tmax + 1, budget=10, run_salt=SALT).diag[row].sum()) == 0


def test_no_starvation_under_sustained_overload():
    """過負荷でも、どの保留も ``T_max``+予算で決まる上界の内に必ず呼ばれる。"""
    n_agents = 200
    budget = 4.0
    arb = Arbiter(n_agents, SALT, budget)
    first_seen: dict[int, int] = {}
    served: dict[int, int] = {}
    rng = np.random.default_rng(5)
    for tick in range(400):
        ids = rng.choice(n_agents, size=8, replace=False)
        cls = rng.integers(0, 4, size=8)
        c = _cands(ids, cls, since=tick)
        for a in ids.tolist():
            first_seen.setdefault(int(a), tick)
        d = arb.step(tick, c)
        for a in d.selected.agent_id.tolist():
            served.setdefault(int(a), tick)
    # 全ての個体が呼ばれている(誰も飢えていない)
    assert set(first_seen) <= set(served), sorted(set(first_seen) - set(served))
    waits = [served[a] - first_seen[a] for a in first_seen]
    bound = sum(T_MAX_TICKS.values()) + int(np.ceil(len(first_seen) / budget))
    print(f"\n[飢餓なし] 最大待ち {max(waits)} tick ≤ 上界 {bound} tick "
          f"(保留 {arb.n_pending()} 件・呼 {arb.n_calls_total})")
    assert max(waits) <= bound


# ---------------------------------------------------------------- 縮退
def test_degrade_applies_only_to_the_lower_two_classes_and_only_when_over_budget():
    c = _cands(list(range(10)), [EventClass.CELL] * 10)
    d = arbitrate(c, tick=0, budget=4.0, run_salt=SALT)
    # 縮退印は付くが**呼数は L4 の硬い上限**(floor(budget))で切れる。
    # 縮退が減らすのは 1 呼あたりのトークン/計算量であって呼の本数ではない(2026-09-08 修正)。
    assert d.n_calls == 4
    assert d.n_calls < int(4.0 / DEGRADE_COST_FACTOR)
    assert d.selected_degraded.all()
    row = DIAG_COLUMNS.index("degraded")
    assert int(d.diag[row].sum()) == d.n_calls
    # 予算が足りていれば縮退しない
    d2 = arbitrate(c, tick=0, budget=20.0, run_salt=SALT)
    assert not d2.selected_degraded.any()


def test_upper_two_classes_are_never_degraded():
    c = _cands(list(range(10)), [EventClass.CONVERSATION] * 5 + [EventClass.PLAN_BOUNDARY] * 5)
    d = arbitrate(c, tick=0, budget=3.0, run_salt=SALT)
    assert not d.selected_degraded.any()
    assert d.n_calls == 3


# ---------------------------------------------------------------- 不応期
def test_refractory_suppresses_but_does_not_drop_the_state_trigger():
    ru = np.zeros((5, N_WAKE_CONDITIONS), dtype=np.int32)
    ru[2, int(WakeCondition.CELL_BLOCK)] = 100
    c = _cands([1, 2, 3], [EventClass.CELL] * 3)
    d = arbitrate(c, tick=10, budget=10, run_salt=SALT, refractory_until=ru)
    assert d.suppressed.agent_id.tolist() == [2]
    assert sorted(d.selected.agent_id.tolist()) == [1, 3]
    assert int(d.diag[DIAG_COLUMNS.index("suppressed")].sum()) == 1
    # 抑止は繰り延べ待ち行列に積まれない(次回起床時に最新状態で立ち直る=§6 運用規定①)
    assert 2 not in d.deferred.agent_id.tolist()


def test_conversation_has_no_refractory_floor():
    ru = np.zeros((3, N_WAKE_CONDITIONS), dtype=np.int32)
    c = _cands([0, 1, 2], [EventClass.CONVERSATION] * 3)
    d = arbitrate(c, tick=0, budget=10, run_salt=SALT, refractory_until=ru)
    assert len(d.suppressed) == 0 and d.n_calls == 3


def test_refractory_shape_is_validated():
    c = _cands([0], [EventClass.CELL])
    with pytest.raises(ValueError):
        arbitrate(c, tick=0, budget=1, run_salt=SALT, refractory_until=np.zeros((1, 3)))


# ---------------------------------------------------------------- 繰り越しと診断
def test_deferred_items_come_back_next_tick():
    arb = Arbiter(10, SALT, budget=1.0)
    c = _cands([1, 2, 3], [EventClass.CELL] * 3)
    d0 = arb.step(0, c)
    assert d0.n_calls == 1  # 3 件 > 予算 1 → 呼数上限で 1 件(縮退は呼数を増やさない)
    assert arb.n_pending() == 2
    d1 = arb.step(1, WakeCandidates.empty())
    assert d1.n_calls == 1 and arb.n_pending() == 1
    d2 = arb.step(2, WakeCandidates.empty())
    assert d2.n_calls == 1 and arb.n_pending() == 0


def test_counters_shape_matches_deferral_queue():
    arb = Arbiter(10, SALT, budget=1.0)
    arb.step(0, _cands([1, 2, 3], [EventClass.CELL] * 3))
    counters = arb.counters()
    assert set(counters) == set(DIAG_COLUMNS)
    for col in DIAG_COLUMNS:
        assert set(counters[col]) == {c.name for c in arb.classes}
    assert set(arb.totals()) == set(DIAG_COLUMNS)


def test_empty_input_is_handled():
    d = arbitrate(WakeCandidates.empty(), tick=0, budget=5, run_salt=SALT)
    assert d.n_calls == 0 and len(d.deferred) == 0 and int(d.diag.sum()) == 0
