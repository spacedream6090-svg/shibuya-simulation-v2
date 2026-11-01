"""第 3 期 3-2(時計の段 T1): 計算のまとめの窓 ``engine.batching.WindowQueue`` の単体(合成の事象だけ・data 不要)。

- 窓の中の順: 時刻 → 体の番号(世界 -1 が先)→ 種類の順位 → 予約の番号。同じ時刻・同じ種類の続きは 1 回の処理。
- 処理の中の予約: 窓の終わりより前は同じ窓で時刻順に続けて回す(TM3 (f))・以降は後の窓。過去への予約は落ちる。
- 窓の中で時刻どおりに回す種類は、幅 W を変えても処理の順も時刻も同じ(10-03 §7-5「窓の幅が結果を変えてはいけない」)。
- 負の対照: 窓の境目で届ける種類(TM1 の電話)を 60 秒未満の時刻に 1 つ入れると、W で処理の順が変わる(遅れ ≤ W)。
- 上限(安全装置): 当たったら残りを次の窓へ持ち越して数える・止めない(0 の遅れで自分を予約し続ける連鎖でも止まる)。
- 幅の検査・予約の番号の払い出し・manifest の欄と節の表。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.core.time_consts import NS_PER_SECOND, STEP_SECONDS
from shibuya.engine import batching as BA
from shibuya.engine import manifest_sections as MS
from shibuya.engine.scheduler import Scheduler

S = NS_PER_SECOND


class _Log:
    """処理の関数の呼び出しを (時刻[ns], 種類, 体の番号の列) で控える。"""

    def __init__(self) -> None:
        self.calls: list[tuple[int, str, tuple[int, ...]]] = []

    def fn(self, name: str):
        def _f(t, agents, seqs):  # noqa: ANN001, ANN202
            assert agents.dtype == np.int64 and seqs.dtype == np.int64 and agents.shape == seqs.shape
            self.calls.append((int(t), name, tuple(int(x) for x in agents)))
        return _f

    def flat(self) -> list[tuple[int, str, int]]:
        return [(t, k, a) for t, k, ags in self.calls for a in ags]


def _drain(q: BA.WindowQueue, end_ns: int) -> None:
    while q.head_ns < end_ns:
        q.run_window()


# ================================================================= 窓の中の順
def test_order_inside_a_window_is_time_then_agent_then_rank_then_seq():
    log = _Log()
    q = BA.WindowQueue(width_s=STEP_SECONDS, start_ns=0)
    q.register(0, "world", log.fn("world"), rank=0)
    q.register(1, "late_rank", log.fn("late_rank"), rank=5)
    q.register(2, "early_rank", log.fn("early_rank"), rank=1)
    # 同じ時刻 10 秒: 体 7 の 2 種類・体 3・世界(-1)/時刻 5 秒: 体 9/時刻 10 秒・体 3 の 2 回目(番号が後)
    q.schedule(10 * S, [7], 1)
    q.schedule(10 * S, [7], 2)
    q.schedule(10 * S, [3], 1)
    q.schedule(10 * S, BA.WORLD, 0)
    q.schedule(5 * S, [9], 1)
    q.schedule(10 * S, [3], 1)
    q.run_window()
    assert log.flat() == [
        (5 * S, "late_rank", 9),
        (10 * S, "world", -1),
        (10 * S, "late_rank", 3), (10 * S, "late_rank", 3),
        (10 * S, "early_rank", 7), (10 * S, "late_rank", 7),
    ]
    # 同じ時刻・同じ種類の続きは 1 回の処理(体 3 の 2 件は 1 回)
    assert [(t // S, k, a) for t, k, a in log.calls] == [
        (5, "late_rank", (9,)), (10, "world", (-1,)), (10, "late_rank", (3, 3)), (10, "early_rank", (7,)),
        (10, "late_rank", (7,))]
    m = q.window_counts
    assert (m["windows"], m["events"], m["dispatches"], m["carried"], m["cap_hits"]) == (1, 6, 5, 0, 0)
    assert q.pending == 0 and q.head_ns == STEP_SECONDS * S


def test_same_time_same_kind_is_one_array_in_agent_order():
    log = _Log()
    q = BA.WindowQueue(width_s=10, start_ns=0)
    q.register(4, "alarm", log.fn("alarm"))
    q.schedule(3 * S, [12, 2, 7, 5], 4)
    q.run_window()
    assert log.calls == [(3 * S, "alarm", (2, 5, 7, 12))]


# ================================================================= 処理の中の予約(TM3 (f))
def test_scheduling_inside_the_window_runs_in_the_same_window_in_time_order():
    log = _Log()
    q = BA.WindowQueue(width_s=STEP_SECONDS, start_ns=0)

    def talk(t, agents, seqs):  # noqa: ANN001, ANN202
        log.fn("talk")(t, agents, seqs)
        if t < 40 * S:  # 会話の番を 15 秒あとに続ける(窓の中は同じ窓・窓の外は後の窓)
            q.schedule(t + 15 * S, agents, 1)

    q.register(1, "talk", talk)
    q.register(2, "alarm", log.fn("alarm"))
    q.schedule(0, [4], 1)
    q.schedule(20 * S, [8], 2)
    q.run_window()
    assert [(t // S, k) for t, k, _a in log.calls] == [(0, "talk"), (15, "talk"), (20, "alarm"), (30, "talk"),
                                                        (45, "talk")]
    assert q.window_counts["in_window"] == 3 and q.window_counts["windows"] == 1
    q.run_window()  # 45+15=60 は窓の外にしない(45 ≥ 40 で止めた)ので次の窓は空
    assert q.window_counts["windows_with_events"] == 1 and q.pending == 0


def test_scheduling_into_the_past_raises():
    q = BA.WindowQueue(width_s=STEP_SECONDS, start_ns=STEP_SECONDS * S)
    q.register(1, "x", lambda t, a, s: None)
    with pytest.raises(ValueError, match="過去"):
        q.schedule(0, [1], 1)  # 窓の外(次の窓の頭より前)
    seen = []
    q2 = BA.WindowQueue(width_s=STEP_SECONDS, start_ns=0)

    def back(t, agents, seqs):  # noqa: ANN001, ANN202
        seen.append(t)
        with pytest.raises(ValueError, match="過去"):
            q2.schedule(t - 1, agents, 1)  # 処理中の時刻より前

    q2.register(1, "back", back)
    q2.schedule(10 * S, [1], 1)
    q2.run_window()
    assert seen == [10 * S] and q2.pending == 0


def test_unknown_kind_and_bad_shapes_raise():
    q = BA.WindowQueue(width_s=STEP_SECONDS, start_ns=0)
    q.register(1, "x", lambda t, a, s: None)
    with pytest.raises(ValueError):
        q.schedule(0, [1], 9)
    with pytest.raises(ValueError):
        q.schedule([0, S, 2 * S], [1, 2], 1)
    with pytest.raises(ValueError):
        q.register(1, "again", lambda t, a, s: None)
    with pytest.raises(ValueError):
        q.register(2, "bad", lambda t, a, s: None, delivery="later")
    assert q.schedule([], [], 1).size == 0


# ================================================================= 幅を変えても同じ(窓の中で時刻どおりの種類)
def _synthetic_world(width_s: int, *, boundary: bool = False) -> tuple[list[tuple[int, str, int]], dict]:
    """合成の世界: 刻みの事象(世界・60 秒ごと)・60 秒未満の時刻の体の事象・処理の中の予約の連鎖。"""
    log = _Log()
    end_ns = 4 * STEP_SECONDS * S
    q = BA.WindowQueue(width_s=width_s, start_ns=0)

    def step(t, agents, seqs):  # noqa: ANN001, ANN202
        log.fn("step")(t, agents, seqs)
        if t + STEP_SECONDS * S < end_ns:
            q.schedule(t + STEP_SECONDS * S, BA.WORLD, BA.KIND_STEP)
        if t == STEP_SECONDS * S:  # 2 回目の刻みで体 7 に 20 秒後の知らせ(届け方は腕)
            q.schedule(t + 20 * S, [7], 3)

    def chain(t, agents, seqs):  # noqa: ANN001, ANN202
        log.fn("chain")(t, agents, seqs)
        if t < 150 * S:
            q.schedule(t + 13 * S, agents, 1)

    q.register(BA.KIND_STEP, "step", step)
    q.register(1, "chain", chain, rank=2)
    q.register(2, "alarm", log.fn("alarm"), rank=1)
    q.register(3, "phone", log.fn("phone"), rank=3, delivery=BA.BOUNDARY if boundary else BA.IN_WINDOW)
    q.schedule(0, BA.WORLD, BA.KIND_STEP)
    q.schedule(7 * S, [5], 1)
    q.schedule([40 * S, 40 * S, 95 * S], [9, 2, 2], 2)
    _drain(q, end_ns)
    return log.flat(), q.window_counts


@pytest.mark.parametrize("width_s", [30, 20, 10, 5, 1])
def test_in_window_kinds_give_the_same_order_and_times_for_every_width(width_s):
    ref, mref = _synthetic_world(STEP_SECONDS)
    got, m = _synthetic_world(width_s)
    assert got == ref
    assert m["windows"] == mref["windows"] * (STEP_SECONDS // width_s)
    assert (m["events"], m["carried"], m["cap_hits"], m["boundary_events"]) == (mref["events"], 0, 0, 0)


def test_negative_control_a_boundary_event_below_60_s_changes_the_order_with_the_width():
    """負の対照: 窓の境目で届ける種類(TM1 の電話)を 60 秒未満の時刻(80 秒)に 1 つ。60 秒の窓では 120 秒(次の窓の頭)に
    届き、体 2 の 95 秒の事象と順が入れ替わる。10 秒の窓では 80 秒に届く(時刻どおり=窓の中の種類と同じ順)。"""
    ref_in, _ = _synthetic_world(STEP_SECONDS)                      # 窓の中で時刻どおり(正解の時刻順)
    o60, m60 = _synthetic_world(STEP_SECONDS, boundary=True)
    o10, m10 = _synthetic_world(10, boundary=True)
    o30, m30 = _synthetic_world(30, boundary=True)
    phone = lambda o: [(t // S, i) for i, (t, k, _a) in enumerate(o) if k == "phone"]  # noqa: E731
    alarm95 = lambda o: next(i for i, (t, k, a) in enumerate(o) if k == "alarm" and t == 95 * S)  # noqa: E731
    assert phone(ref_in)[0][0] == 80 and phone(o10)[0][0] == 80
    assert phone(o60)[0][0] == 120 and phone(o30)[0][0] == 90
    assert phone(o60)[0][1] > alarm95(o60)                 # 60 秒: 95 秒の事象の後に届く=順が変わる
    assert phone(o10)[0][1] < alarm95(o10)                 # 10 秒: 時刻どおり
    assert o60 != ref_in and o30 != ref_in and o10 == ref_in
    # 遅れの計器(≤ W)と単調さ(W を細かくすると遅れは増えない)
    assert (m60["boundary_delay_ns_max"], m30["boundary_delay_ns_max"], m10["boundary_delay_ns_max"]) == (
        40 * S, 10 * S, 0)
    assert all(m["boundary_events"] == 1 for m in (m60, m30, m10))


def test_boundary_event_inside_the_window_goes_to_the_next_window_head():
    log = _Log()
    q = BA.WindowQueue(width_s=STEP_SECONDS, start_ns=0)

    def caller(t, agents, seqs):  # noqa: ANN001, ANN202
        log.fn("caller")(t, agents, seqs)
        q.schedule(t, [4], 2)  # 窓の頭に掛けた電話=窓の境目で届く=次の窓の頭(遅れ W)

    q.register(1, "caller", caller)
    q.register(2, "phone", log.fn("phone"), delivery=BA.BOUNDARY)
    q.schedule(0, [1], 1)
    q.run_window()
    q.run_window()
    assert [(t // S, k) for t, k, _a in log.calls] == [(0, "caller"), (STEP_SECONDS, "phone")]
    assert q.window_counts["boundary_delay_ns_max"] == STEP_SECONDS * S


# ================================================================= 上限(安全装置)と持ち越し
def test_cap_carries_the_rest_to_the_next_window_and_counts():
    log = _Log()
    q = BA.WindowQueue(width_s=STEP_SECONDS, start_ns=0, cap=3)
    q.register(1, "a", log.fn("a"))
    q.schedule([1 * S, 2 * S, 3 * S, 4 * S, 5 * S], [1, 2, 3, 4, 5], 1)
    q.schedule(70 * S, [6], 1)
    q.run_window()
    assert [a for _t, _k, a in log.flat()] == [1, 2, 3]
    m = q.window_counts
    assert (m["carried"], m["cap_hits"], q.pending) == (2, 1, 3)
    q.run_window()  # 持ち越し(時刻は前の窓)が先・次の窓の事象が後
    assert [(t // S, a) for t, _k, a in log.flat()] == [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (70, 6)]
    assert q.window_counts["cap_hits"] == 1 and q.pending == 0


def test_cap_stops_a_zero_delay_loop_without_stopping_the_run():
    """0 の遅れで自分を予約し続ける連鎖(会話の番の暴走の形)でも、窓は上限で閉じて次へ進む(止めない・数える)。"""
    q = BA.WindowQueue(width_s=10, start_ns=0, cap=50)
    n = {"calls": 0}

    def loop(t, agents, seqs):  # noqa: ANN001, ANN202
        n["calls"] += 1
        q.schedule(t, agents, 1)

    q.register(1, "loop", loop)
    q.schedule(0, [1], 1)
    _drain(q, 30 * S)
    m = q.window_counts
    assert m["windows"] == 3 and m["cap_hits"] == 3 and m["events"] == 150 and n["calls"] == 150
    assert m["carried"] == 3 and q.pending == 1


def test_cap_must_be_positive_and_width_must_divide_the_step():
    with pytest.raises(ValueError):
        BA.WindowQueue(width_s=STEP_SECONDS, start_ns=0, cap=0)
    with pytest.raises(ValueError):
        BA.WindowQueue(width_s=7, start_ns=0)
    with pytest.raises(ValueError):
        BA.WindowQueue(width_s=30, start_ns=15 * S)


# ================================================================= 幅の腕・番号・manifest
def test_widths_are_the_divisors_of_the_step_and_the_default_is_the_step():
    assert BA.DEFAULT_WIDTH_S == STEP_SECONDS
    assert BA.WIDTHS_S == tuple(w for w in range(1, STEP_SECONDS + 1) if STEP_SECONDS % w == 0)
    assert {60, 30, 10, 5, 1} <= set(BA.WIDTHS_S) and 7 not in BA.WIDTHS_S
    assert BA.parse_width("30") == 30 and BA.parse_width(5) == 5
    for bad in (7, 0, -60, 120, True, "x", None, 2.5):
        with pytest.raises(ValueError):
            BA.parse_width(bad)


def test_set_arm_and_is_default():
    prev = BA.arm()
    try:
        BA.set_arm(10)
        assert BA.arm() == 10 and not BA.is_default()
        with pytest.raises(ValueError):
            BA.set_arm(7)
        assert BA.arm() == 10
        BA.set_arm(BA.DEFAULT_WIDTH_S)
        assert BA.is_default()
    finally:
        BA.set_arm(prev)


def test_reserve_seq_shares_the_numbering_with_schedule():
    s = Scheduler()
    a = s.schedule_many([1, 2], [0, 0])
    b = s.reserve_seq(3)
    c = s.schedule_many([3], [1])
    assert a.tolist() == [0, 1] and b.tolist() == [2, 3, 4] and c.tolist() == [5]
    assert s.pending == 3 and s.reserve_seq(0).size == 0
    with pytest.raises(ValueError):
        s.reserve_seq(-1)


def test_in_window_and_queued_events_get_distinct_seq():
    got = []
    q = BA.WindowQueue(width_s=STEP_SECONDS, start_ns=0)

    def f(t, agents, seqs):  # noqa: ANN001, ANN202
        got.extend(seqs.tolist())
        if t == 0:
            got.extend(q.schedule([5 * S, 70 * S], [1, 1], 1).tolist())

    q.register(1, "f", f)
    q.schedule(0, [1], 1)
    q.run_window()
    q.run_window()
    # 0 の事象(番号 0)→ 予約: 窓の外 70 秒が番号 1(待ち行列)・窓の中 5 秒が番号 2(払い出し)→ 5 秒(2)→ 70 秒(1)
    assert got == [0, 2, 1, 2, 1]


def test_manifest_fields_keys_match_the_sections_table():
    q = BA.WindowQueue(width_s=10, start_ns=0)
    q.register(BA.KIND_STEP, "step", lambda t, a, s: None)
    d = q.manifest_fields()
    assert tuple(d) == BA.config_keys() + BA.observed_keys()
    assert d["schema"] == BA.SCHEMA and d["width_s"] == 10 and d["default_width_s"] == STEP_SECONDS
    assert d["kinds"] == {"step": {"kind": 0, "rank": 0, "delivery": BA.IN_WINDOW}}
    for k in BA.config_keys():
        assert MS.section_of(f"batching.{k}") == MS.CONFIG, k
    for k in BA.observed_keys():
        assert MS.section_of(f"batching.{k}") == MS.OBSERVED, k
    assert "batching" in MS.MIXED
    assert MS.unlisted_in_mixed({"batching": d}) == []
    assert BA.manifest_fields(None) is None


# ================================================================= 〔3-2 検収 M1〕実行時の守り(負の対照 3 本)
def _started_queue() -> BA.WindowQueue:
    q = BA.WindowQueue(width_s=10, start_ns=0)
    q.register(1, "a", lambda t, a, s: None, rank=2)
    q.schedule([5 * S, 25 * S], [1, 2], 1)
    q.run_window()
    return q


@pytest.mark.parametrize("name,value", [
    ("_bw_head", 0), ("_bw_carry", np.zeros((1, BA.COL_SEQ + 1), dtype=np.int64)), ("width_ns", 1),
    ("width_s", 1), ("cap", 1), ("_bw_meter", {}), ("_bw_kinds", {}), ("_bw_rank", np.zeros(64, dtype=np.int64)),
    ("_bw_sched", None), ("_bw_now", 0), ("new_attr", 1),
])
def test_m1_assignment_from_outside_fails(name, value):
    q = _started_queue()
    before = (q.head_ns, q.window_counts, q.pending)
    with pytest.raises(AttributeError, match="外から書けない"):
        setattr(q, name, value)
    with pytest.raises(AttributeError, match="消せない"):
        delattr(q, "_bw_head")
    assert (q.head_ns, q.window_counts, q.pending) == before  # 何も変わっていない
    _drain(q, 30 * S)
    assert q.window_counts["events"] == 2 and q.pending == 0  # 守りの後も窓は回る(25 秒の事象は 3 つ目の窓)


def test_m1_tables_are_read_only():
    q = _started_queue()
    with pytest.raises(TypeError):
        q._bw_kinds[2] = ("b", lambda t, a, s: None, BA.IN_WINDOW)  # 種類の表(MappingProxyType)
    with pytest.raises(ValueError):
        q._bw_rank[1] = 0  # 順位の表(書けない配列)
    with pytest.raises(TypeError):
        q._bw_meter["windows"] = 0  # 計器(読み取り専用の辞書)
    # 持ち越しの行(上限に当たった後)も書けない配列
    q2 = BA.WindowQueue(width_s=STEP_SECONDS, start_ns=0, cap=1)
    q2.register(1, "a", lambda t, a, s: None)
    q2.schedule([1 * S, 2 * S], [1, 2], 1)
    q2.run_window()
    assert q2.pending == 1
    with pytest.raises(ValueError):
        q2._bw_carry[0, BA.COL_T] = 0
    assert int(q2._bw_rank[1]) == 0 and dict(q._bw_kinds)[1][0] == "a"


def test_m1_register_after_the_start_and_duplicate_names_fail():
    q = BA.WindowQueue(width_s=10, start_ns=0)
    q.register(1, "a", lambda t, a, s: None)
    with pytest.raises(ValueError, match="名"):
        q.register(2, "a", lambda t, a, s: None)  # 名の重複
    late = []

    def h(t, agents, seqs):  # noqa: ANN001, ANN202
        with pytest.raises(RuntimeError, match="閉じた"):
            q.register(3, "late", lambda t, a, s: None)  # ランの途中(処理の関数の中)
        with pytest.raises(AttributeError):
            q._bw_head = 0  # 処理の関数を呼んでいる間も欄は書けない
        late.append(t)

    q.register(2, "h", h)
    q.schedule(0, [1], 2)
    q.run_window()
    with pytest.raises(RuntimeError, match="閉じた"):
        q.register(4, "after", lambda t, a, s: None)  # 最初の窓の後
    assert late == [0] and set(q._bw_kinds) == {1, 2}


# ================================================================= 〔3-2 検収 L6〕輪の外(遠未来の heapq)と上限の manifest
def _far_world(width_s: int) -> tuple[list[tuple[int, str, int]], int]:
    log = _Log()
    q = BA.WindowQueue(width_s=width_s, start_ns=0)

    def hop(t, agents, seqs):  # noqa: ANN001, ANN202
        log.fn("hop")(t, agents, seqs)
        if t < 40 * STEP_SECONDS * S:
            q.schedule(t + 7 * STEP_SECONDS * S + 13 * S, agents, 1)  # 輪(2 刻み)の外=遠未来の heapq を通る

    q.register(1, "hop", hop)
    q.register(2, "alarm", log.fn("alarm"))
    q.schedule([3 * STEP_SECONDS * S + 30 * S, 17 * STEP_SECONDS * S + 1 * S], [4, 2], 1)
    q.schedule([11 * STEP_SECONDS * S + 59 * S, 29 * STEP_SECONDS * S], [9, 9], 2)
    far = q._bw_sched.far_future_pending
    _drain(q, 60 * STEP_SECONDS * S)
    return log.flat(), far


def test_l6_reservations_beyond_the_ring_keep_order_and_times_for_every_width():
    ref, far60 = _far_world(STEP_SECONDS)
    assert far60 >= 3 and len(ref) > 10  # 最初の予約の多くが輪の外(遠未来の heapq)
    for w in (30, 10, 5, 1):
        got, far = _far_world(w)
        assert far >= 3 and got == ref, w


def test_l6_manifest_fields_after_a_cap_hit():
    q = BA.WindowQueue(width_s=STEP_SECONDS, start_ns=0, cap=2)
    q.register(1, "a", lambda t, a, s: None)
    q.schedule([1 * S, 2 * S, 3 * S, 4 * S, 5 * S], [1, 2, 3, 4, 5], 1)
    q.run_window()
    d = q.manifest_fields()
    assert (d["carried"], d["cap_hits"], d["events"], d["pending_at_end"]) == (3, 1, 2, 3)
    q.run_window()
    d = q.manifest_fields()
    assert (d["carried"], d["cap_hits"], d["events"], d["pending_at_end"]) == (4, 2, 4, 1)
    q.run_window()
    d = q.manifest_fields()
    assert (d["carried"], d["cap_hits"], d["events"], d["pending_at_end"]) == (4, 2, 5, 0)


# ================================================================= 〔3-2 検収 L7〕同時刻の束の中で同じ時刻に足した事象
def test_l7_same_time_event_added_inside_a_group_runs_after_the_rest_of_the_group():
    """体 5・9 の束(同じ時刻・同じ種類=1 回の処理)の中で体 3 を同じ時刻に足すと、5 → 9 → 3 の順(体の番号順の例外=宣言)。"""
    log = _Log()
    q = BA.WindowQueue(width_s=STEP_SECONDS, start_ns=0)

    def f(t, agents, seqs):  # noqa: ANN001, ANN202
        log.fn("f")(t, agents, seqs)
        if 5 in agents.tolist():
            q.schedule(t, [3], 1)

    q.register(1, "f", f)
    q.schedule(10 * S, [9, 5], 1)
    q.run_window()
    assert [a for _t, _k, a in log.flat()] == [5, 9, 3]
    assert log.calls == [(10 * S, "f", (5, 9)), (10 * S, "f", (3,))]
