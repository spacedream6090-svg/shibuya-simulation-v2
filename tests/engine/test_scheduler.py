"""engine.scheduler のテスト: 順序規約(§2.5)・純関数性・繰り延べ待ち行列の診断列。"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shibuya.core.types import EventClass
from shibuya.engine.scheduler import (
    COL_AGENT,
    COL_CLASS,
    COL_OFFSET,
    DIAG_COLUMNS,
    DeferralQueue,
    Scheduler,
    TickState,
    coalesce_agents,
    order_indices,
    scheduler,
)

SALT = b"test-run-salt"


def _state(rows, tick=0, salt=SALT) -> TickState:
    return TickState(tick=tick, events=np.array(rows, dtype=np.int64).reshape(-1, 4), run_salt=salt)


# ---------------- 順序規約(運用設計書 §2.5) ----------------
def test_offset_then_class_rank_ordering():
    """(offset_ns, class_rank, blake3, agent_id) の昇順。"""
    rows = [
        [7, 213_000_000, int(EventClass.CONVERSATION), 0],
        [1, 0, int(EventClass.CELL), 1],
        [2, 500_000_000, int(EventClass.CONVERSATION), 2],
        [3, 0, int(EventClass.PLAN_BOUNDARY), 3],
        [4, 0, int(EventClass.INSTITUTION), 4],
    ]
    got = scheduler(_state(rows))
    # offset=0 の3件が先(class -1 → 1 → 3)、次に 0.213s、最後に 0.5s
    assert got.tolist() == [4, 3, 1, 7, 2]


def test_tiebreak_is_not_agent_id_order():
    """同一 (offset, class) では blake3 撹拌が効き、ID 昇順にはならない(v1 C-8 の根治)。"""
    n = 64
    rows = [[i, 0, 0, i] for i in range(n)]
    got = scheduler(_state(rows)).tolist()
    assert sorted(got) == list(range(n))
    assert got != list(range(n))
    # 塩が変われば順序も変わる
    other = scheduler(_state(rows, salt=b"other")).tolist()
    assert other != got


def test_pure_function_same_input_same_output():
    rows = [[i, (i % 3) * 1000, i % 4, i] for i in range(50)]
    s1, s2 = _state(rows, tick=17), _state(rows, tick=17)
    assert np.array_equal(scheduler(s1), scheduler(s2))
    # tick が違えば撹拌も違う
    assert not np.array_equal(scheduler(s1), scheduler(_state(rows, tick=18)))


@settings(max_examples=50, deadline=None)
@given(
    events=st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=999),  # agent
            st.integers(min_value=0, max_value=3),  # offset バケット
            st.sampled_from([-1, 0, 1, 2, 3]),  # class_rank
        ),
        min_size=0,
        max_size=40,
    ),
    perm_seed=st.integers(min_value=0, max_value=10_000),
)
def test_property_order_is_independent_of_insertion_order(events, perm_seed):
    """T3 相当: 挿入順を並べ替えても出力(agent_id 列)は変わらない。"""
    rows = [[a, o * 100_000_000, c, i] for i, (a, o, c) in enumerate(events)]
    rng = np.random.default_rng(perm_seed)
    perm = rng.permutation(len(rows)).tolist()
    shuffled = [[rows[p][0], rows[p][1], rows[p][2], j] for j, p in enumerate(perm)]
    assert np.array_equal(scheduler(_state(rows, tick=5)), scheduler(_state(shuffled, tick=5)))


def test_order_indices_is_a_permutation():
    rows = [[i, i % 7, i % 4, i] for i in range(30)]
    idx = order_indices(_state(rows))
    assert sorted(idx.tolist()) == list(range(30))


def test_tick_state_validates_shape_and_dtype():
    with pytest.raises(ValueError):
        TickState(tick=0, events=np.zeros((3, 3), dtype=np.int64))
    with pytest.raises(ValueError):
        TickState(tick=0, events=np.zeros((3, 4), dtype=np.int32))


def test_empty_tick():
    s = _state([])
    assert scheduler(s).size == 0
    assert order_indices(s).size == 0


def test_coalesce_keeps_first_occurrence():
    ids = np.array([5, 3, 5, 9, 3], dtype=np.int64)
    assert coalesce_agents(ids).tolist() == [5, 3, 9]
    assert coalesce_agents(np.empty(0, dtype=np.int64)).size == 0


# ---------------- Scheduler(バケット配列+heap) ----------------
def test_schedule_due_consume_cycle():
    s = Scheduler(run_salt=SALT)
    s.schedule_many([1, 2, 3], [3, 3, 4], 0, int(EventClass.PLAN_BOUNDARY))
    assert s.pending == 3
    assert sorted(s.due(3).tolist()) == [1, 2]
    assert s.due(3).tolist() == s.due(3).tolist(), "取り出しは副作用なし=同じ列"
    assert s.consume(3) == 2
    assert s.due(3).size == 0
    assert s.due(4).tolist() == [3]
    assert s.consume(4) == 1
    assert s.pending == 0


def test_cancel_and_reschedule():
    s = Scheduler(run_salt=SALT)
    seq = s.schedule(7, 3, 0, EventClass.CONVERSATION)
    assert s.cancel(seq) is True
    assert s.cancel(seq) is False, "二重取り消しは False"
    assert s.due(3).size == 0
    assert s.pending == 0

    seq2 = s.schedule(8, 3, 0, EventClass.CELL)
    seq3 = s.reschedule(seq2, 5)
    assert s.due(3).size == 0
    assert s.due(5).tolist() == [8]
    assert seq3 != seq2
    with pytest.raises(KeyError):
        s.reschedule(seq2, 6)


def test_far_future_goes_to_heap_then_ring():
    s = Scheduler(horizon_ticks=10, run_salt=SALT)
    s.schedule_many([1, 2], [5, 50])
    assert s.far_future_pending == 1
    assert s.due(5).tolist() == [1]
    s.consume(5)
    assert s.due(50).tolist() == [2]
    assert s.far_future_pending == 0
    assert s.pending == 1
    s.consume(50)
    assert s.pending == 0


def test_ring_reuse_after_a_full_lap():
    s = Scheduler(horizon_ticks=4, run_salt=SALT)
    s.schedule(1, 0)
    s.consume(0)
    s.schedule(2, 4)  # 同じスロット(4 % 4 == 0)
    assert s.due(4).tolist() == [2]


def test_rejects_past_tick_and_bad_offset():
    s = Scheduler(run_salt=SALT)
    s.consume(10)
    with pytest.raises(ValueError, match="過去"):
        s.schedule(1, 9)
    with pytest.raises(ValueError, match="offset_ns"):
        s.schedule(1, 11, 60 * 10**9)
    with pytest.raises(ValueError, match="長さ"):
        s.schedule_many([1, 2], [11])


def test_due_coalesces_multiple_wakes_of_one_agent():
    """§6 運用規定②: 同一体の複数条件が同時に明けたら 1 呼に合流。"""
    s = Scheduler(run_salt=SALT)
    s.schedule_many([7, 7, 8], [2, 2, 2], [0, 100, 0], [3, 0, 1])
    assert s.due(2).tolist().count(7) == 2
    assert sorted(s.due(2, coalesce=True).tolist()) == [7, 8]


def test_due_events_columns():
    s = Scheduler(run_salt=SALT)
    s.schedule(9, 1, 250_000_000, EventClass.INDIVIDUAL)
    ev = s.due_events(1)
    assert ev.shape == (1, 4)
    assert ev[0, COL_AGENT] == 9
    assert ev[0, COL_OFFSET] == 250_000_000
    assert ev[0, COL_CLASS] == int(EventClass.INDIVIDUAL)


def test_scheduler_matches_pure_function_on_same_state():
    s = Scheduler(run_salt=SALT)
    s.schedule_many([1, 2, 3, 4], [7, 7, 7, 7], [0, 0, 1000, 0], [3, 1, 0, 2])
    state = s.events_at(7)
    assert np.array_equal(s.due(7), scheduler(state))


# ---------------- 繰り延べ待ち行列 ----------------
def test_diag_columns_match_manifest_schema():
    """診断行4列は manifest 側の定義そのもの(engine は再輸出するだけ=定義を増やさない)。"""
    from shibuya.manifest.schema import DIAG_COLUMNS as MANIFEST_DIAG

    assert DIAG_COLUMNS is MANIFEST_DIAG


def test_deferral_queue_counts_all_four_diagnostics():
    q = DeferralQueue()
    q.defer(1, EventClass.CELL, "over_budget", tick=3)
    q.defer_many([2, 3], EventClass.INDIVIDUAL, "over_budget", tick=3)
    q.promote(1, EventClass.CELL)  # CELL → INDIVIDUAL(1段上)
    q.degrade(EventClass.CELL, 2)
    q.suppress(EventClass.INDIVIDUAL)

    totals = q.totals()
    assert totals == {"deferred": 3, "promoted": 1, "degraded": 2, "suppressed": 1}
    assert set(totals) == set(DIAG_COLUMNS)
    assert q.counters()["promoted"]["INDIVIDUAL"] == 1
    assert q.pending(EventClass.CELL).size == 0
    assert sorted(q.pending(EventClass.INDIVIDUAL).tolist()) == [1, 2, 3]
    assert len(q) == 3


def test_deferral_queue_waiting_ticks_and_pop():
    q = DeferralQueue()
    q.defer_many([1, 2, 3], EventClass.PLAN_BOUNDARY, "arbiter", tick=10)
    assert q.waiting_ticks(EventClass.PLAN_BOUNDARY, 25).tolist() == [15, 15, 15]
    assert q.pop_class(EventClass.PLAN_BOUNDARY, 2).tolist() == [1, 2]
    assert q.pending(EventClass.PLAN_BOUNDARY).tolist() == [3]
    assert q.pop_class(EventClass.PLAN_BOUNDARY).tolist() == [3]
    assert len(q) == 0


def test_deferral_queue_rejects_institution_class():
    """制度(−1)はエンジン側イベントで繰り延べ対象外(知覚契約書 §6 の4クラス)。"""
    q = DeferralQueue()
    with pytest.raises(ValueError):
        q.defer(1, EventClass.INSTITUTION, "x")
    with pytest.raises(KeyError):
        q.promote(99, EventClass.CELL)


def test_deferral_queue_interns_reasons():
    q = DeferralQueue()
    a = q.reason_code("budget")
    b = q.reason_code("budget")
    c = q.reason_code("refractory")
    assert a == b != c
    assert q.reason_name(a) == "budget"
