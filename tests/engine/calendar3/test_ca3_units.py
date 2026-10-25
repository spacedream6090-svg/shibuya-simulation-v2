"""第 6 期 6-2 カレンダー 3 の単体の試験: 雇い主の口の表(組織ごとのシフトを組む人・週ごとの働く人・正規は触らない・枠=W20 の
約束の形)・暦の常識(祝日の問い合わせの口・常識の文)・店の決まり(枠だけ)・労働時間の行(human=読むだけ)・判断の呼びの id・
監査の負の対照・腕の切替口と設定。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.engine.calendar import SimCalendar, load_holidays
from shibuya.engine.calendar2 import book as B2
from shibuya.engine.calendar2 import port as P2
from shibuya.engine.calendar3 import arm as A3
from shibuya.engine.calendar3 import layer as L3
from shibuya.engine.calendar3 import port as P3
from shibuya.engine.calendar3 import roster as R3
from shibuya.engine.calendar3.knowledge import CommonCalendar, StoreRules, common_line
from shibuya.engine.contact import port as PC
from shibuya.engine.events.log import Event, LlmCall, Process

from tests.engine.calendar3._ca3 import FRAME_A, FRAME_B, FRAME_LONG, MANAGER, UNIT, FakeRights, STEP_NS, \
    synthetic_roster, synthetic_table

ROOT = Path(__file__).resolve().parents[3]
HOLIDAY_CSV = ROOT / "tests" / "fixtures" / "calendar" / "syukujitsu.csv"


def _calendar(start: str) -> SimCalendar:
    return SimCalendar(start_sim_datetime=datetime.fromisoformat(start), holidays=load_holidays(HOLIDAY_CSV))


# ================================================================= 雇い主の口の表
def test_roster_units_scheduler_and_weekly_workers_only():
    n = 80
    ro = synthetic_roster(n)
    assert ro.n_units == n // UNIT
    # 週ごとの働く人=奇数の体だけ(毎週固定の偶数の体は触らない)
    assert sorted(ro.unit_of) == list(range(1, n, 2))
    assert ro.head_counts["weekly_workers"] == n // 2 and ro.head_counts["fixed_workers"] == n // 2
    # シフトを組む人=単位の担当のうち店長の役割の体(単位 2 は 25 番)・ほかは最初の担当(10u 番=毎週固定の体)
    for u in range(ro.n_units):
        want = MANAGER if u == MANAGER // UNIT else u * UNIT
        assert ro.scheduler[u] == want
        assert ro.sched_by[u] == (R3.SCHEDULER_ROLE if u == MANAGER // UNIT else "最初の担当")
        assert ro.workers[u] == [a for a in range(u * UNIT, (u + 1) * UNIT) if a % 2 == 1]
    # 枠=その人の W20 の約束の形(重ならない組・始業の順)
    assert ro.frames[1] == sorted([[*FRAME_A, 1, 1], [*FRAME_B, 1, 1], [*FRAME_LONG, 1, 1]])
    assert ro.units_of(MANAGER) == [MANAGER // UNIT]


def test_roster_outside_employer_and_no_employer_are_not_scheduled():
    from shibuya.engine.rights.initial import OUTSIDE_EMPLOYER_ORG

    n = 20
    ids = np.arange(n, dtype=np.int64)

    class Rights:
        def pairs(self, kind, hk, ok, t):
            if ok == "org":  # 0〜9=外の雇用主・10〜14=組織 1・15〜19=行なし
                return ids[:15], np.where(ids[:15] < 10, OUTSIDE_EMPLOYER_ORG, 1)
            return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)

    ro = R3.build_roster(n_agents=n, rights=Rights(), table=synthetic_table(n))
    assert ro.head_counts["weekly_outside_employer"] == 5  # 1・3・5・7・9(渋谷の外の雇い主=世界のデータのまま)
    assert ro.head_counts["weekly_no_employer"] == 3  # 15・17・19(行なし)
    assert sorted(ro.unit_of) == [11, 13]
    assert ro.sched_by == ["最初の担当"]


def test_roster_store_unit_and_self_scheduling():
    n = 4

    class Rights:
        def pairs(self, kind, hk, ok, t):
            if ok == "store":
                return np.array([3], dtype=np.int64), np.array([7], dtype=np.int64)
            return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)

    ro = R3.build_roster(n_agents=n, rights=Rights(), table=synthetic_table(n))
    assert ro.unit_kind == [R3.UNIT_STORE] and ro.unit_obj == [7]
    assert ro.scheduler == [3] and ro.sched_by == ["本人"]  # 担当が本人だけ=本人が組む(つなぎ)
    assert ro.store_of == {3: 7}
    assert ro.head_counts["weekly_no_employer"] == 1  # 1 番は行なし


def test_roster_without_table_or_population_is_empty():
    assert R3.build_roster(n_agents=5, rights=FakeRights(5), table=None).n_units == 0
    assert R3.roster_for_run(None, None, None, 5).n_units == 0 and R3.w20_table_for_run(None, None) is None


# ================================================================= 暦の常識・店の決まり・労働時間の行
def test_common_knowledge_knows_holidays_for_everyone():
    cal = _calendar("2026-07-19")
    cc = CommonCalendar(cal)
    assert cc.ask(1) == ("2026-07-20", "月", "海の日")
    assert cc.words(1) == "7/20(月・海の日)" and cc.words(0) == "7/19(日)"
    assert common_line(cc, 1) == "今日は 7 月 20 日(月・海の日)。"
    assert CommonCalendar(None).words(3) == "3 日目"
    assert StoreRules().closed_days(0, range(7)) == ()  # 店の休業日は枠だけ(本段は空)


def test_labor_rows_are_human_and_read_only():
    lp = L3.labor_params("2026-07-13")
    assert lp["max_hours_per_week"] == 40 and lp["max_hours_per_day"] == 8 and lp["min_rest_days_per_week"] == 1
    assert lp["kind"] == ["human", "human"] and lp["enforced"] is False
    assert L3.labor_params(None) == {}


# ================================================================= 判断の呼びの id と口
def test_call_ids_do_not_collide_with_contact_or_calendar2():
    s3 = P3.serial_of(P3.P_FRAME, 1)
    assert s3 >= P3.SERIAL_BASE > P2.SERIAL_BASE + (P2.MAX_DECISIONS_PER_STEP << 4)
    cid = P3.call_id_of(5, 7, s3)
    assert P3.parse_call_id(cid) == (5, 7, s3) and P3.purpose_of_serial(s3) == P3.P_FRAME
    assert P3.parse_call_id(P2.call_id_of(5, 7, P2.serial_of(P2.P_TURN, 1))) is None
    assert P3.parse_call_id(PC.call_id_of(5, 7, PC.serial_of(PC.P_WHOM, 1))) is None
    with pytest.raises(ValueError):
        P3.serial_of(P3.P_FRAME, P3.MAX_DECISIONS_PER_STEP)


def test_port_mock_is_uniform_over_candidates_and_deterministic():
    from shibuya.engine.decision.port import DecisionContext

    port = P3.Calendar3Port(seed=1)
    cands = [P3.cand(P3.K_DAY_OFF, id="off")] + [P3.cand(P3.K_FRAME, f"枠 {i}", id=f"frame:{i}") for i in range(3)]
    picks = []
    for k in range(1, 200):
        ctx = DecisionContext(agent_id=3, step=k, t_ns=k * STEP_NS, wake_class=-1, condition=-1, cell=0,
                              call_id=P3.call_id_of(k, 3, P3.serial_of(P3.P_FRAME, 1)))
        ch = port.choose(ctx, cands)
        assert ch.number >= 1
        picks.append(ch.candidate_id)
        assert port.choose(ctx, cands).candidate_id == ch.candidate_id
    assert set(picks) == {"off", "frame:0", "frame:1", "frame:2"}


def test_promise_book_has_the_work_kind_at_the_end():
    assert B2.KINDS[B2.K_WORK] == "勤務" and B2.K_WORK == len(B2.KINDS) - 1
    assert B2.KINDS[:5] == ("二人の約束", "本人の予定", "本人の計画", "アラーム", "出来事の実行意図")


# ================================================================= 監査の負の対照
def test_audit_catches_forged_and_engine_causes():
    s = P3.serial_of(P3.P_FRAME, 1)
    good = LlmCall(P3.call_id_of(2, 4, s), (), source="plan", number=1)
    issued = np.asarray([L3.issued_key(2, 4, s)], dtype=np.int64)
    ok = [Event(t_ns=2 * STEP_NS, who=4, what=L3.W_FRAME, cause=good, how_much=0),
          Event(t_ns=3 * STEP_NS, who=4, what=L3.W_NOTIFY, cause=Process("calendar3"), how_much=1)]
    assert L3.audit_causes(ok, step_ns=STEP_NS, issued=issued)["violations"] == 0
    bad = [
        Event(t_ns=2 * STEP_NS, who=4, what=L3.W_WRITE, cause=good),  # 判断の種類が語に合わない
        Event(t_ns=2 * STEP_NS, who=5, what=L3.W_FRAME, cause=good),  # 体が違う
        Event(t_ns=2 * STEP_NS, who=4, what=L3.W_FRAME, cause=Process("calendar3")),  # 道具が本人の語
        Event(t_ns=3 * STEP_NS, who=4, what=L3.W_NOTIFY, cause=good),  # 判断が道具の語
        Event(t_ns=2 * STEP_NS, who=4, what=L3.W_FRAME,
              cause=LlmCall(P3.call_id_of(2, 4, P3.serial_of(P3.P_FRAME, 2)), (), source="plan", number=1)),  # 控えに無い
    ]
    got = L3.audit_causes(bad, step_ns=STEP_NS, issued=issued)
    assert got["violations"] == 5, got


# ================================================================= 腕
def test_arm_switch_and_config():
    prev = (A3.arm(), A3.trial())
    try:
        A3.set_arm("off")
        assert A3.config() is None and not A3.trial_on()
        A3.set_arm("arm")
        A3.set_trial("on")
        assert A3.config() == {"arm": "arm", "trial": "on"} and A3.trial_on()
        with pytest.raises(ValueError):
            A3.set_arm("on")
        with pytest.raises(ValueError):
            A3.set_trial("yes")
    finally:
        A3.set_arm(prev[0])
        A3.set_trial(prev[1])
