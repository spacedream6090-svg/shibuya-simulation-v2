"""第 6 期 6-4 C2: CT4 の習慣(腕 ``SHIBUYA_CONTACT_HABIT``)。

その人自身の過去の選び(状態ごと)から作った習慣で「今読む/後で/無視」「返す/スタンプ/返さない」を答える。記録が閾値未満・
大事な誘い・驚き・ときどき(用途名 ``contact.habit``)は判断の口へ戻す。腕 off は表を作らない(記録の無い体は習慣が無い)。
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import Activity
from shibuya.engine.contact import arm as A
from shibuya.engine.contact import habit as HB
from shibuya.engine.contact import port as P
from shibuya.engine.contact.layer import W_IGNORE, W_LATER, W_READ, audit_causes

from tests.engine.contact._c1 import STEP_NS, by_kind, choose
from tests.engine.contact._c2 import Harness2, loud

SRC = Path(__file__).resolve().parents[3] / "src" / "shibuya" / "engine" / "contact"


# ================================================================= 表の単体
def test_no_records_no_habit_and_threshold():
    b = HB.HabitBook()
    assert b.answer(0, HB.STATE_HOME, "notice") is None  # 記録の無い体は習慣が無い(負の対照)
    for _ in range(HB.HABIT_MIN_RECORDS - 1):
        b.note(0, HB.STATE_HOME, "notice", "後で")
    assert b.answer(0, HB.STATE_HOME, "notice") is None  # 閾値未満
    b.note(0, HB.STATE_HOME, "notice", "後で")
    assert b.answer(0, HB.STATE_HOME, "notice") == "後で"  # 閾値以上=いちばん多い語
    assert b.answer(0, HB.STATE_WORK, "notice") is None  # 状態ごと
    assert b.answer(0, HB.STATE_HOME, "reply") is None  # 判断ごと
    b.note(0, HB.STATE_HOME, "notice", "知らない語")  # 表の外の語は数えない
    assert b.records(0, HB.STATE_HOME, "notice") == HB.HABIT_MIN_RECORDS


def test_tie_takes_the_first_word_in_order():
    b = HB.HabitBook()
    for w in ("無視", "今読む", "無視", "今読む", "後で"):
        b.note(1, HB.STATE_OTHER, "notice", w)
    assert b.answer(1, HB.STATE_OTHER, "notice") == "今読む"


def test_states_from_activity_and_place():
    act = np.array([int(Activity.IDLE), int(Activity.MOVING), int(Activity.IDLE), int(Activity.IDLE),
                    int(Activity.RIDING)])
    cells = np.array([3, 3, 5, 7, -1])
    tr = np.array([0, 0, 0, 0, 0])
    home = np.array([True, True, False, False, False])
    work = np.array([1, 1, 5, 6, 2])
    st = HB.states_of(act, cells, tr, home, work)
    assert [HB.STATE_WORDS[int(x)] for x in st] == ["家", "移動中", "勤務中", "ほか", "移動中"]
    assert HB.states_of(act, cells, tr, home, None)[2] == HB.STATE_OTHER  # 勤め先の表が無ければ勤務中は無い
    # 範囲の外に居る体(出入りの状態 2)の活動は「待機」のまま=移動中に数えない
    out = HB.states_of(np.array([int(Activity.WAITING)] * 2), np.array([-1, 4]), np.array([2, 0]),
                       np.array([False, False]), None)
    assert [HB.STATE_WORDS[int(x)] for x in out] == ["ほか", "移動中"]


# ================================================================= 層の中の道
def _harness(habit: bool) -> Harness2:
    """体 1 は範囲の外に居る(セル −1=習慣を使う体・状態=ほか)・ほかは範囲の中(セル 0)。"""
    h = Harness2(home_cell=[0] * 6, habit=habit, cells=[0, -1, 0, 0, 0, 0])
    loud(h)
    return h


def _seed(h: Harness2, a: int, word: str, n: int = HB.HABIT_MIN_RECORDS, state: int = HB.STATE_OTHER) -> None:
    for _ in range(n):
        h.layer.habit.note(a, state, "notice", word)


def _send(h: Harness2, to: int) -> None:
    mb = h.layer.mail
    mb.deliver(mb.new_message_id(), 0, [to], -1, 0, int(h.queue.head_ns), 5, "こんにちは", lambda a: True)


def test_habit_answers_when_records_are_enough(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_READ_NOW, P.K_NOREPLY, P.K_KEEP)):  # 判断の口なら今読む
        h = _harness(True)
        _seed(h, 1, "後で")
        _send(h, 1)
        j0 = h.layer.model_calls()[0]
        h.run(2)
    later = [e for e in h.of(W_LATER) if e.who == 1]
    assert later and not [e for e in h.of(W_READ) if e.who == 1]  # 習慣=後で(判断の口なら今読む)
    cid = P.parse_call_id(later[0].cause.call_id)
    assert P.purpose_of_serial(cid[2]) == P.P_HABIT_NOTICE and later[0].cause.source == "experience"
    m = h.layer._meter
    assert m.get("habit:answered:notice") == 1 and m.get("habit:answered:ほか:notice") == 1
    assert h.layer.model_calls()[0] == j0  # 判断モデルの呼びに数えない
    assert h.layer.habit.records(1, HB.STATE_OTHER, "notice") == HB.HABIT_MIN_RECORDS + 1  # 習慣で答えた語も数える
    assert audit_causes(h.log.events(), step_ns=STEP_NS, issued=h.layer.issued_keys())["violations"] == 0


def test_in_range_bodies_always_go_to_the_port(monkeypatch):
    """〔親の判断 2026-10-23=問い 2〕習慣で答えるのは範囲の外に居る体だけ(CT4)。範囲の中の体は記録が足りても判断の口へ。"""
    with choose(monkeypatch, by_kind(P.K_READ_NOW, P.K_NOREPLY, P.K_KEEP)):
        h = _harness(True)
        for st in range(len(HB.STATE_WORDS)):
            _seed(h, 2, "後で", state=st)
        _send(h, 2)
        h.run(2)
    assert [e for e in h.of(W_READ) if e.who == 2] and not [e for e in h.of(W_LATER) if e.who == 2]
    m = h.layer._meter
    assert m.get("habit:in_range:notice") == 1 and not m.get("habit:answered:notice")
    assert sum(h.layer.habit.records(2, st, "notice") for st in range(4)) == 4 * HB.HABIT_MIN_RECORDS + 1


def test_below_threshold_goes_to_the_decision_port(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_READ_NOW, P.K_NOREPLY, P.K_KEEP)):
        h = _harness(True)
        _seed(h, 1, "後で", HB.HABIT_MIN_RECORDS - 1)
        _send(h, 1)
        h.run(2)
    assert [e for e in h.of(W_READ) if e.who == 1] and h.layer._meter.get("habit:back:few_records", 0) >= 1
    assert h.layer.habit.records(1, HB.STATE_OTHER, "notice") == HB.HABIT_MIN_RECORDS  # 判断の口の選びも数える


def test_important_offer_goes_back(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_READ_NOW, P.K_NOREPLY, P.K_KEEP)):
        h = _harness(True)
        h.layer.offer_probe = lambda a: int(a) == 1  # カレンダー 2 の返事待ちの誘いが届いている
        _seed(h, 1, "後で")
        _send(h, 1)
        h.run(2)
    assert [e for e in h.of(W_READ) if e.who == 1] and h.layer._meter.get("habit:back:offer") == 1


def test_surprise_goes_back(monkeypatch):
    """驚き=その刻みに起床条件 (i) で起きた体(割り込みと同じ入口=系 contact が刻みの頭に置く ``_interrupted``)。"""
    with choose(monkeypatch, by_kind(P.K_READ_NOW, P.K_NOREPLY, P.K_KEEP)):
        h = _harness(True)
        _seed(h, 1, "後で")
        h.run(1)  # 習慣の状態を置く
        cands = [P.cand(P.K_READ_NOW), P.cand(P.K_LATER), P.cand(P.K_IGNORE)]
        c0, _ = h.layer._habit_or_decide(1, STEP_NS, 1, "notice", P.P_NOTICE, P.P_HABIT_NOTICE, cands)
        h.layer._interrupted[1] = True
        c1, _ = h.layer._habit_or_decide(1, STEP_NS, 1, "notice", P.P_NOTICE, P.P_HABIT_NOTICE, cands)
    assert c0.kind == P.K_LATER and c1.kind == P.K_READ_NOW and h.layer._meter.get("habit:back:surprise") == 1


def test_sometimes_goes_back_with_the_named_stream(monkeypatch):
    seen = []
    real = P.habit_recheck_u

    def spy(seed, step_key, agent, serial):
        seen.append((agent, P.purpose_of_serial(serial)))
        return real(seed, step_key, agent, serial)

    monkeypatch.setattr(P, "habit_recheck_u", spy)
    monkeypatch.setattr(HB, "HABIT_RECHECK_SHARE", 1.0)  # いつも戻す
    with choose(monkeypatch, by_kind(P.K_READ_NOW, P.K_NOREPLY, P.K_KEEP)):
        h = _harness(True)
        _seed(h, 1, "後で")
        _send(h, 1)
        h.run(2)
    assert seen == [(1, P.P_HABIT_NOTICE)] and h.layer._meter.get("habit:back:recheck") == 1
    assert [e for e in h.of(W_READ) if e.who == 1]
    assert P.HABIT_DOMAIN == "contact.habit"
    v = [real(1, 7, 3, 16 + P.P_HABIT_NOTICE) for _ in range(2)]
    assert v[0] == v[1] and 0.0 <= v[0] < 1.0  # 同じ鍵から同じ値(counter)


def test_arm_off_builds_no_table_and_uses_the_port(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_IGNORE, P.K_NOREPLY, P.K_KEEP)):
        h = _harness(False)
        _send(h, 1)
        h.run(2)
    assert [e for e in h.of(W_IGNORE) if e.who == 1]
    assert h.layer.habit._counts == {} and not any(k.startswith("habit:") for k in h.layer._meter)
    assert h.layer.manifest()["habit"] is None


def test_arm_switch_and_fingerprint():
    prev = A.habit()
    try:
        A.set_arm("c1")
        A.set_habit("off")
        assert "habit" not in A.config()  # 習慣 off は C1 の指紋のまま
        A.set_habit("on")
        assert A.config()["habit"] == "on"
        with pytest.raises(ValueError):
            A.set_habit("maybe")
    finally:
        A.set_habit(prev)
        A.set_arm("off")


# ================================================================= AST: エンジンが時刻・回数・中身を決めない
_C2_FUNCS = {"_habit_or_decide", "_charge_decisions", "_face_turn_decisions", "_invite_answer", "_make_group", "_invite",
             "_leave", "_lookup", "_battery_physics"}


def _time_rules(src: str, names: set[str]) -> list[str]:
    """関数の中に「刻み・時刻の剰余」「刻み・時刻と数の比べ」(エンジンが時刻や回数を決める直書き)があれば挙げる。"""
    bad = []
    for fn in [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name in names]:
        for node in ast.walk(fn):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
                bad.append(f"{fn.name}: 剰余(行 {node.lineno})")
            if isinstance(node, ast.Compare):
                parts = [node.left, *node.comparators]
                if any(isinstance(x, ast.Name) and x.id in ("T", "t_ns", "td") for x in parts) and \
                        any(isinstance(x, ast.Constant) and isinstance(x.value, int) for x in parts):
                    bad.append(f"{fn.name}: 時刻と数の比べ(行 {node.lineno})")
    return bad


def test_ast_no_engine_time_or_count_rules_in_c2():
    src = (SRC / "layer.py").read_text(encoding="utf-8")
    found = {n.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef)}
    assert _C2_FUNCS <= found
    assert _time_rules(src, _C2_FUNCS) == []
    for f in ("habit.py", "book.py", "tools.py"):
        assert _time_rules((SRC / f).read_text(encoding="utf-8"),
                           {n.name for n in ast.walk(ast.parse((SRC / f).read_text(encoding="utf-8")))
                            if isinstance(n, ast.FunctionDef)}) == [], f


def test_ast_negative_control_catches_a_planted_rule():
    planted = '''
def _charge_decisions(self, T, t_ns, main_now):
    if T % 1440 == 1320:
        self.dev.plug([0])
    if T >= 600:
        self.dev.plug([1])
'''
    assert len(_time_rules(planted, {"_charge_decisions"})) == 2
