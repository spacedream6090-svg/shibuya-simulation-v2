"""〔v3-0a 案 A(指示書 11-04 §2-1)〕棚卸し §1-1 の 18 か所の同値: 世界の時刻 ``t_ns`` から作った整数(乱数の鍵・呼びの
id・時間帯)が、書き換えの前に材料に入れていた刻みの番号から作った値と同じ(日をまたぐ境・2 日目・再開の後)。

- 口の単位(#3・#5〜#12): 判断の口の基底と腕の口 4 種の並べ替えと選びを、旧の書き方(鍵=``step_key(ctx.step)``)に戻した写しと
  比べる。
- 呼びの id(#1・#4・#14〜#18)と時間帯(#2): 旧の形 ``f"{T}:…"``・``T // TIME_BUCKET_TICKS`` と比べる。
- 習慣の戻し(#13・#15): 連絡の層の合成の台で、旧の鍵 ``step_key(T)`` と旧の呼びの id と比べる。
- ラン: 腕のラン(連絡+習慣+カレンダー 2・3+判断の口 port/店の仕事)を日をまたいで止め、再開した後まで回し、口と層の入口ごとに
  「t_ns から作った整数 == 刻みの番号」を確かめる。艦隊の道(#1・#2)は偽の艦隊のランで、発射した呼びの id と時間帯が旧の形と
  同じことを確かめる。

場所の番号(#)は docs/bench/analysis/v3-2026-11/v30a/README.md §1-1 の表。
"""

from __future__ import annotations

import copy
from collections import Counter
from typing import Any

import pytest

from shibuya.foundation import rng as RNG
from shibuya.foundation import time_consts as TC
from shibuya.engine import run as RUN
from shibuya.engine.calendar2 import layer as L2
from shibuya.mind.plan import calendar2_port as P2
from shibuya.engine.calendar3 import layer as L3
from shibuya.mind.plan import calendar3_port as P3
from shibuya.engine.contact import layer as CL
from shibuya.mind.plan import contact_port as PC
from shibuya.mind.judge.decision import layer as DLY
from shibuya.foundation.ports.decision import SOURCE_AFFORDANCE, Candidate, DecisionContext, DecisionPort
from shibuya.engine.duties import layer as LD
from shibuya.mind.plan import duties_port as PD
from shibuya.engine.systems import boxes as BX

TPD = TC.STEPS_PER_DAY
#: 日をまたぐ境・2 日目・再開の位置(試験の再開は TPD+300 で止める)。
STEPS = (0, 1, 59, 60, TPD - 1, TPD, TPD + 1, TPD + 300, TPD + 301, 2 * TPD - 1, 2 * TPD, 7 * TPD + 5)
ARM_PORTS = ((PC.ContactPort, PC), (P2.Calendar2Port, P2), (P3.Calendar3Port, P3), (PD.DutiesPort, PD))
CANDS = tuple(Candidate(id=f"c{i}", kind=f"k{i % 3}", text=f"候補 {i}", source=SOURCE_AFFORDANCE) for i in range(5))


def _t_ns(T: int, w: int) -> int:
    return BX.TickCtx.of(T, TC.SECONDS_PER_DAY // w, w).t_ns


def _old(port: Any, step: int) -> Any:
    """旧の書き方の写し: 鍵の時刻を刻みの番号から作る(書き換えの前の ``self.step_key(ctx.step)``)。"""
    old = copy.copy(port)
    old.time_key_at = lambda _t_ns, _s=int(step), _p=port: _p.step_key(_s)
    return old


class _First(DecisionPort):
    """判断の口の基底の試験用の実装(提示の 1 番を選ぶ)。"""

    name = "first"

    def _answer(self, ctx: DecisionContext, presented: tuple[Candidate, ...]) -> tuple[str, dict[str, Any]]:
        return next(c.id for c in presented if c.number == 1), {}


# ================================================================= 口の単位(#3・#5〜#12)
@pytest.mark.parametrize("w", [60, 30])
@pytest.mark.parametrize("day_key0", [0, 20_000])
def test_port_key_from_time_is_the_old_key(w, day_key0):
    for cls, _m in ((DecisionPort, None), *ARM_PORTS):
        port = cls(seed=1, day_key0=day_key0, step_seconds=w)
        for T in STEPS:
            assert port.time_key_at(_t_ns(T, w)) == port.step_key(T) == RNG.run_tick_key(day_key0, T, w)


@pytest.mark.parametrize("w", [60, 30])
def test_base_port_presents_and_chooses_as_before(w):
    """#3: 判断の口の基底の並べ替え(``present_rng``)の鍵。"""
    port = _First(seed=7, day_key0=3, step_seconds=w)
    n_diff = 0
    for T in STEPS:
        for a in (0, 5, 4_999):
            ctx = DecisionContext(agent_id=a, step=T, t_ns=_t_ns(T, w), wake_class=1, condition=0, cell=0,
                                  call_id=f"{T}:{a}:1")
            new, old = port.choose(ctx, CANDS), _old(port, T).choose(ctx, CANDS)
            assert new == old
            n_diff += new.candidate_id != "c0"
    assert n_diff > 0  # 並べ替えが効いている(どの鍵でも同じ答えになる試験ではない)


@pytest.mark.parametrize("w", [60, 30])
@pytest.mark.parametrize("cls,mod", ARM_PORTS, ids=[c.__name__ for c, _ in ARM_PORTS])
def test_arm_port_presents_and_draws_as_before(cls, mod, w):
    """#5〜#12: 腕の口の並べ替え(``choose``)と選びの乱数(``_draw``)の鍵。"""
    port = cls(seed=11, day_key0=0, step_seconds=w)
    purpose = next(iter(mod.PURPOSES))
    cands = CANDS if mod is not PD else (PD.cand(PD.K_SHOP, "店を開ける", id="u"), PD.cand(PD.K_WAIT, "まだ", id="w"),
                                         PD.cand(PD.K_RESTOCK, "補充する", id="r"))
    draws = set()
    for T in STEPS:
        for a in (0, 9):
            for k in (1, 2):
                cid = mod.call_id_of(T, a, mod.serial_of(purpose, k))
                ctx = DecisionContext(agent_id=a, step=T, t_ns=_t_ns(T, w), wake_class=-1, condition=-1, cell=0,
                                      call_id=cid)
                old = _old(port, T)
                assert port.choose(ctx, cands) == old.choose(ctx, cands)
                assert port._draw(ctx) == old._draw(ctx)
                draws.add(port._draw(ctx))
    assert len(draws) > 1


# ================================================================= 呼びの id と時間帯(#1・#2・#4・#14〜#18)
@pytest.mark.parametrize("w", [60, 30])
def test_call_ids_and_time_bucket_from_time_are_the_old_ones(w):
    for T in STEPS:
        t = _t_ns(T, w)
        k = RNG.key_time_from_t_ns(t, w)
        for a, cls in ((0, 0), (4_999, 3)):
            assert f"{k}:{a}:{cls}" == f"{T}:{a}:{cls}"  # #1(艦隊の道)・#4(判断の口の層)
        assert k // RUN.TIME_BUCKET_TICKS == T // RUN.TIME_BUCKET_TICKS  # #2
        for _cls, mod in ARM_PORTS:  # #14〜#18(連絡 2 か所・カレンダー 2・3・店の仕事)
            s = mod.serial_of(next(iter(mod.PURPOSES)), 3)
            assert mod.call_id_of(k, 7, s) == mod.call_id_of(T, 7, s)
            assert mod.parse_call_id(mod.call_id_of(k, 7, s)) == (T, 7, s)


# ================================================================= 習慣の戻し(#13・#15)
def test_contact_habit_key_and_call_id_are_the_old_ones(monkeypatch):
    from shibuya.mind.plan import contact_habit as HB
    from tests.engine.contact._c2 import Harness2, loud

    seen: list[tuple[int, int]] = []
    real = PC.habit_recheck_u

    def spy(seed, key, agent, serial):  # noqa: ANN001, ANN202
        seen.append((int(key), int(serial)))
        return real(seed, key, agent, serial)

    monkeypatch.setattr(PC, "habit_recheck_u", spy)
    h = Harness2(home_cell=[0] * 6, habit=True, cells=[0, -1, 0, 0, 0, 0])
    loud(h)
    for _ in range(HB.HABIT_MIN_RECORDS):
        h.layer.habit.note(1, HB.STATE_OTHER, "notice", PC.K_LATER)
    cands = [PC.cand(PC.K_READ_NOW), PC.cand(PC.K_LATER), PC.cand(PC.K_IGNORE)]
    answered = 0
    for T in STEPS:
        h.layer._codes.clear()
        seen.clear()
        c, cause = h.layer._habit_or_decide(T, T * TC.NS_PER_STEP, 1, "notice", PC.P_NOTICE, PC.P_HABIT_NOTICE, cands)
        assert [k for k, _ in seen] == [h.layer.port.step_key(T)]  # #13: 旧の鍵(刻みの番号から)
        got = PC.parse_call_id(cause.call_id)
        assert got is not None and got[0] == T  # #14・#15: 旧の呼びの id の刻み
        assert cause.call_id == PC.call_id_of(T, 1, got[2])
        answered += cause.source == "experience"
    assert answered > 0  # 習慣で答えた道(#15)を通った


# ================================================================= ラン(日をまたぐ・再開の後)
class _Spy:
    def __init__(self) -> None:
        self.seen: Counter[str] = Counter()
        self.bad: list[tuple[str, Any]] = []

    def check(self, where: str, ok: bool, info: Any) -> None:
        self.seen[where] += 1
        if not ok:
            self.bad.append((where, info))


def _call_id_head_is(call_id: str, step: int) -> bool:
    head = str(call_id).split(":")[0]
    return not head.isdigit() or int(head) == int(step)  # カレンダー 1b の id(頭が語)は 18 か所の外


@pytest.fixture
def spy(monkeypatch):
    s = _Spy()
    for cls in (DecisionPort, PC.ContactPort, P2.Calendar2Port, P3.Calendar3Port, PD.DutiesPort):
        real = cls.__dict__["choose"]

        def choose(self, ctx, candidates, _real=real, _n=f"{cls.__name__}.choose"):  # noqa: ANN001, ANN202
            ok = self.time_key_at(ctx.t_ns) == self.step_key(ctx.step) and _call_id_head_is(ctx.call_id, ctx.step)
            s.check(_n, ok, (ctx.step, ctx.t_ns, ctx.call_id))
            return _real(self, ctx, candidates)

        monkeypatch.setattr(cls, "choose", choose)
    for cls, meth in ((CL.ContactLayer, "_decide"), (CL.ContactLayer, "_habit_or_decide"),
                      (L2.Calendar2Layer, "_decide"), (L3.Calendar3Layer, "_decide"), (LD.DutiesLayer, "_decide")):
        real = getattr(cls, meth)

        def wrapped(self, T, t_ns, *a, _real=real, _n=f"{cls.__name__}.{meth}", **k):  # noqa: ANN001, ANN202
            s.check(_n, RNG.key_time_from_t_ns(t_ns, self.step_seconds) == int(T), (T, t_ns))
            return _real(self, T, t_ns, *a, **k)

        monkeypatch.setattr(cls, meth, wrapped)
    real_one = DLY.DecisionLayer.decide_one

    def decide_one(self, bridge, agent_id, step, *a, **k):  # noqa: ANN001, ANN202
        s.check("DecisionLayer.decide_one",
                RNG.key_time_from_t_ns(k["t_ns"], self.port.step_seconds) == int(step), (step, k["t_ns"]))
        return real_one(self, bridge, agent_id, step, *a, **k)

    monkeypatch.setattr(DLY.DecisionLayer, "decide_one", decide_one)
    real_of = BX.TickCtx.of

    def of(T, tpd, step_seconds=TC.STEP_SECONDS):  # noqa: ANN001, ANN202
        c = real_of(T, tpd, step_seconds)
        s.check("TickCtx", RNG.key_time_from_t_ns(c.t_ns, int(step_seconds)) == c.T, (T, c.t_ns))
        return c

    monkeypatch.setattr(BX.TickCtx, "of", staticmethod(of))
    return s


def _stop_and_resume(run_day: Any, tmp_path: Any, kw: dict, stop: int, fresh: Any = None) -> tuple[Any, Any]:
    a = run_day(state_out=tmp_path / "state", stop_at_tick=stop, **kw, **(fresh(True) if fresh else {}))
    path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
    b = run_day(resume_from=path, **kw, **(fresh(False) if fresh else {}))
    return a, b


def test_contact_calendars_and_port_runs_across_the_day_and_resume(spy, monkeypatch, tmp_path):
    """連絡(習慣 on)・カレンダー 2・3・判断の口 port の腕のラン(日 → 月・TPD+300 で止めて再開)。"""
    from tests.engine.calendar3._ca3 import KW, ca3, roster_fixture
    from tests.engine.contact._c2 import habit_arm
    from tests.engine.decision._j0 import decision_arm

    roster_fixture(monkeypatch)
    with ca3(), habit_arm(True), decision_arm(DLY.ARM_PORT):
        a, b = _stop_and_resume(RUN.run_day, tmp_path, dict(KW, sim_days=2), TPD + 300)
    assert b.resume["finished"] and not a.resume["finished"]
    assert spy.bad == []
    for where in ("TickCtx", "DecisionPort.choose", "DecisionLayer.decide_one", "ContactPort.choose",
                  "ContactLayer._decide", "ContactLayer._habit_or_decide", "Calendar2Port.choose",
                  "Calendar2Layer._decide", "Calendar3Port.choose", "Calendar3Layer._decide"):
        assert spy.seen[where] > 0, (where, dict(spy.seen))
    assert spy.seen["TickCtx"] == 2 * TPD  # 止めたランと再開のランで 2 日の全刻み


def test_duties_run_across_the_day_and_resume(spy, monkeypatch, tmp_path):
    """店の仕事の腕のラン(TPD+300 で止めて再開)。"""
    from tests.engine.duties._du import KW, du, fresh

    with du():
        a, b = _stop_and_resume(RUN.run_day, tmp_path, dict(KW, sim_days=2), TPD + 300,
                                fresh=lambda first: fresh(monkeypatch, endow=first))
    assert b.resume["finished"] and not a.resume["finished"]
    assert spy.bad == []
    for where in ("TickCtx", "DutiesPort.choose", "DutiesLayer._decide"):
        assert spy.seen[where] > 0, (where, dict(spy.seen))


def test_fleet_call_ids_and_time_bucket_are_the_old_ones(monkeypatch):
    """#1・#2: 艦隊の道で発射した呼び(偽の艦隊・合成の世界)の id と時間帯が旧の形(``f"{T}:{体}:{級}"``・``T // 5``)。"""
    from shibuya.llm.fleet import FleetBridge
    from tests.engine.test_fleet_wiring import make_client, run_fleet
    from tests.llm.test_fleet import FakeVLLM

    seen: list[tuple[int, Any]] = []
    real = FleetBridge.submit

    def submit(self, calls, *, now_tick=-1):  # noqa: ANN001, ANN202
        seen.extend((int(now_tick), c) for c in calls)
        return real(self, calls, now_tick=now_tick)

    monkeypatch.setattr(FleetBridge, "submit", submit)
    servers = [FakeVLLM(), FakeVLLM()]
    try:
        run_fleet(make_client(servers), ticks=12)
    finally:
        for sv in servers:
            sv.close()
    assert seen
    for T, c in seen:
        assert c.call_id == f"{T}:{int(c.agent_id)}:{int(c.wake_class)}" and int(c.tick) == T
        assert int(c.time_bucket) == T // RUN.TIME_BUCKET_TICKS


def test_old_copy_only_swaps_the_key():
    """(この試験の道具の検査)旧の写しは鍵の口だけを差し替える(元の口は変えない)。"""
    port = PC.ContactPort(seed=1, day_key0=0, step_seconds=60)
    old = _old(port, 5)
    assert old.time_key_at(0) == port.step_key(5) and port.time_key_at(0) == port.step_key(0)
