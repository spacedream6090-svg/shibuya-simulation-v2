"""第 6 期 6-2 カレンダー 2 の単体の試験(合成の台=層だけ): 二人の約束は各自の行・変えられるのは自分の行だけ・変更は出来事の
記録に 1 行・置き場所と確かさと元の会話の欄・壊れた予定だけ拒む・間に合わない/閉店中は記録だけ・アプリは重なりを警告する・
頭の中の予定は記憶で思い出せたときだけ見える(思い出せない体には見えない負の対照・相手が居れば手がかり)・アラームは寝ていれば
起きた後に見える・出来事がきっかけの実行意図・監査の負の対照・呼びの id の形。"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.agents.state import Activity
from shibuya.core.time_consts import NS_PER_SECOND, SECONDS_PER_HOUR
from shibuya.engine.calendar2 import book as B
from shibuya.engine.calendar2 import layer as LY
from shibuya.engine.calendar2 import port as P
from shibuya.engine.contact import port as CP
from shibuya.engine.events.log import Event, LlmCall, Process

from tests.engine.calendar2._ca2 import STEP_NS, Harness, choose

HOUR_NS = SECONDS_PER_HOUR * NS_PER_SECOND


def _rule(prefs_by_purpose, by_agent=None):
    """判断の種類ごとの好み(``{種類: [語か id, …]}``)・体ごとの上書き(``{(体, 種類): [...]}``)。"""
    def rule(ctx, presented):
        _t, a, serial = P.parse_call_id(ctx.call_id)
        purpose = P.purpose_of_serial(serial)
        prefs = (by_agent or {}).get((int(a), purpose)) or prefs_by_purpose.get(purpose, ())
        for k in prefs:
            for c in presented:
                if c.kind == k or c.id == k:
                    return c.id
        return sorted(presented, key=lambda c: (c.kind, c.id))[0].id
    return rule


BASE = {P.P_TURN: [P.K_NO_PROPOSE], P.P_DAY: ["day:0"], P.P_HOUR: ["hour:15"], P.P_LENGTH: ["len:1"],
        P.P_PLACE: ["here"], P.P_RESPOND: [P.K_ACCEPT], P.P_PLACEMENT: [P.K_PLACE_APP], P.P_NOTIFY: ["lead:30"],
        P.P_INTENT: [P.K_NO_INTENT], P.P_GO: [P.K_NOT_YET], P.P_EDIT_WHAT: [P.K_EDIT_TIME], LY.P_OUTSIDE: ["outside:no"],
        LY.P_CERTAIN: [P.K_FIRM]}


def _promise(h, monkeypatch, *, prefs=None, by_agent=None, hour=15):
    """体 0 が対面の会話 1 で体 1 を誘い(刻み 600=10 時)、体 1 が受け、体 0 が聞く(刻み 602)。"""
    p = {**BASE, **(prefs or {})}
    p[P.P_HOUR] = [f"hour:{hour}"]
    ba = {(0, P.P_TURN): [P.K_PROPOSE], **(by_agent or {})}
    monkeypatch.setattr(P.Calendar2Port, "_pick", lambda self, ctx, presented: _rule(p, ba)(ctx, presented))
    h.live.add(1)
    h.layer.note_turn("f:1", 0, 600, "600:0:2", [0, 1])
    h.step(600)
    ba2 = {k: v for k, v in ba.items() if k != (0, P.P_TURN)}  # 誘うのは最初の番だけ
    monkeypatch.setattr(P.Calendar2Port, "_pick", lambda self, ctx, presented: _rule(p, ba2)(ctx, presented))
    h.layer.note_turn("f:1", 1, 601, "601:1:2", [0, 1])
    h.step(601)
    h.layer.note_turn("f:1", 0, 602, "602:0:2", [0, 1])
    h.step(602)


def test_book_rows_are_each_own_and_only_the_owner_can_edit():
    bk = B.PromiseBook()
    a = bk.write(0, {"kind": B.K_PROMISE, "start_ns": HOUR_NS, "cell": 3, "with": [1]}, written_ns=0)
    b = bk.write(1, {"kind": B.K_PROMISE, "start_ns": HOUR_NS, "cell": 3, "with": [0]}, written_ns=0)
    assert a != b and bk.rows[a]["owner"] == 0 and bk.rows[b]["owner"] == 1
    with pytest.raises(PermissionError, match="自分の行だけ"):
        bk.edit(0, b, "start_ns", 2 * HOUR_NS)
    assert bk.edit(1, b, "start_ns", 2 * HOUR_NS) == HOUR_NS and bk.rows[a]["start_ns"] == HOUR_NS
    with pytest.raises(KeyError):
        bk.edit(0, a, "seen", 3)  # 観測の欄は本人の欄でない
    with pytest.raises(KeyError):
        bk.observe(a, "start_ns", 0)  # 本人の欄は観測の口で書けない


def test_broken_is_only_end_before_start_empty_place_or_no_start():
    assert B.broken({"start_ns": -1, "cell": 1}) == "始まりが無い"
    assert B.broken({"start_ns": 10, "end_ns": 9, "cell": 1}) == "終わりが始まりより前"
    assert B.broken({"start_ns": 10, "end_ns": -1, "cell": -1, "place": " "}) == "場所が空"
    assert B.broken({"start_ns": 10, "end_ns": 10, "cell": -1, "place": "駅のあたり"}) is None  # 地名帳に無い場所は言葉のまま
    with pytest.raises(ValueError):
        B.PromiseBook().write(0, {"start_ns": 10, "end_ns": 5, "cell": 1}, written_ns=0)


def test_call_ids_do_not_collide_with_contact_and_parse_back():
    s = P.serial_of(P.P_GO, 3)
    cid = P.call_id_of(5, 7, s)
    assert P.parse_call_id(cid) == (5, 7, s) and P.purpose_of_serial(s) == P.P_GO
    c1 = CP.call_id_of(5, 7, CP.serial_of(CP.P_NOTICE, 3))
    assert P.parse_call_id(c1) is None  # 連絡の判断の id はカレンダー 2 の形でない(通し番号がぶつからない)
    with pytest.raises(ValueError):
        P.serial_of(P.P_GO, P.MAX_DECISIONS_PER_STEP)


def test_a_promise_becomes_each_own_row_with_fields(monkeypatch):
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch, by_agent={(1, P.P_PLACEMENT): [P.K_PLACE_HEAD]})
    rows = list(h.layer.book.rows.values())
    assert sorted(r["owner"] for r in rows) == [0, 1]
    r0 = next(r for r in rows if r["owner"] == 0)
    r1 = next(r for r in rows if r["owner"] == 1)
    assert r0["with"] == [1] and r1["with"] == [0]
    assert r0["start_ns"] == r1["start_ns"] == 15 * HOUR_NS and r0["end_ns"] == 16 * HOUR_NS
    assert r0["cell"] == r1["cell"] == 0  # 「ここ」=誘った人の居たセル
    assert r0["placement"] == B.PL_APP and r1["placement"] == B.PL_HEAD
    assert r0["certain"] == r1["certain"] == 1
    assert r0["origin"] == r1["origin"] == ["対面", "f:1", "600:0:2"]  # 元の会話=会話の番の id
    assert r0["offer"] == r1["offer"] >= 0
    assert r0["notify_ns"] == 15 * HOUR_NS - 30 * 60 * NS_PER_SECOND
    assert r1["trace"] is not None and r0["trace"] is None  # 頭の中の行だけ記憶の痕跡
    whats = [e.what for e in h.events()]
    assert whats.count(LY.W_OFFER) == 1 and whats.count(LY.W_ACCEPT) == 1 and whats.count(LY.W_WRITE) == 2
    assert LY.audit_causes(h.log.events(), step_ns=STEP_NS, issued=h.layer.issued_keys())["violations"] == 0


def test_tentative_answer_gives_tentative_rows(monkeypatch):
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch, prefs={P.P_RESPOND: [P.K_TENTATIVE], LY.P_CERTAIN: [P.K_TENT]})
    assert sorted(r["certain"] for r in h.layer.book.rows.values()) == [0, 0]
    assert LY.W_TENTATIVE in [e.what for e in h.events()]


def test_the_proposer_chooses_own_certainty_not_the_engine(monkeypatch):
    """〔検収 L1〕出した人の確かさは返事を聞いた本人が選ぶ(エンジンが返事から決めない)=相手が仮でも確定で書ける。"""
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch, prefs={P.P_RESPOND: [P.K_TENTATIVE], LY.P_CERTAIN: [P.K_FIRM]})
    by = {r["owner"]: r["certain"] for r in h.layer.book.rows.values()}
    assert by == {0: 1, 1: 0}
    assert h.layer._c2_meter.get("decisions:certain") == 1 and h.layer._c2_meter.get("heard_certainty:確定") == 1


def test_declined_offer_writes_no_rows(monkeypatch):
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch, prefs={P.P_RESPOND: [P.K_DECLINE]})
    assert len(h.layer.book) == 0
    assert h.layer._c2_meter.get("offers_all_declined") == 1


def test_offer_without_answer_lapses_when_the_conversation_ends(monkeypatch):
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    monkeypatch.setattr(P.Calendar2Port, "_pick", lambda self, ctx, presented: _rule(
        BASE, {(0, P.P_TURN): [P.K_PROPOSE]})(ctx, presented))
    h.live.add(1)
    h.layer.note_turn("f:1", 0, 600, "600:0:2", [0, 1])
    h.step(600)
    assert len(h.layer._offers) == 1
    h.live.discard(1)  # 相手の番の前に会話が終わった
    h.step(601)
    assert len(h.layer._offers) == 0 and len(h.layer.book) == 0
    assert h.layer._c2_meter.get("offers_no_answer") == 1 and h.layer._c2_meter.get("answers:返事なし") == 1


def test_change_is_own_row_only_and_one_event(monkeypatch):
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch)
    before = {r["owner"]: dict(r) for r in h.layer.book.rows.values()}
    n0 = len(h.events())
    p = dict(BASE)
    p[P.P_HOUR] = ["hour:18"]
    monkeypatch.setattr(P.Calendar2Port, "_pick", lambda self, ctx, presented: _rule(
        p, {(0, P.P_TURN): [P.K_CHANGE]})(ctx, presented))
    h.layer.note_turn("f:1", 0, 610, "610:0:2", [0, 1])
    h.step(610)
    after = {r["owner"]: r for r in h.layer.book.rows.values()}
    assert after[0]["start_ns"] == 18 * HOUR_NS and after[0]["end_ns"] == 19 * HOUR_NS
    assert after[1]["start_ns"] == before[1]["start_ns"]  # 相手の行は変わらない(各自の理解)
    new = h.events()[n0:]
    assert [e.what for e in new] == [LY.W_EDIT_TIME] and new[0].how_much == after[0]["id"] and new[0].who == 0
    assert LY.audit_causes(h.log.events(), step_ns=STEP_NS, issued=h.layer.issued_keys())["violations"] == 0


def test_cancel_and_certainty_changes(monkeypatch):
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch)
    for T, what, word in ((611, P.K_EDIT_CERTAIN, LY.W_EDIT_CERTAIN), (612, P.K_EDIT_CANCEL, LY.W_CANCEL)):
        p = dict(BASE)
        p[P.P_EDIT_WHAT] = [what]
        monkeypatch.setattr(P.Calendar2Port, "_pick", lambda self, ctx, presented, p=p: _rule(
            p, {(0, P.P_TURN): [P.K_CHANGE]})(ctx, presented))
        h.layer.note_turn("f:1", 0, T, f"{T}:0:2", [0, 1])
        h.step(T)
        assert h.events()[-1].what == word
    r0 = next(r for r in h.layer.book.rows.values() if r["owner"] == 0)
    assert r0["certain"] == 0 and r0["state"] == B.ST_CANCELLED


def _write(h, monkeypatch, content, placement=P.K_PLACE_APP, a=0, T=600):
    p = dict(BASE)
    p[P.P_PLACEMENT] = [placement]
    monkeypatch.setattr(P.Calendar2Port, "_pick", lambda self, ctx, presented: _rule(p)(ctx, presented))
    h.log.begin_step(T * STEP_NS)
    h.layer._codes.clear()
    return h.layer._write_own(T, T * STEP_NS, a, dict({"end_ns": -1, "place": "", "what": ""}, **content), [1], 1,
                              origin=None, offer=-1)


def test_broken_rows_are_rejected_and_only_the_app_tells(monkeypatch):
    h = Harness()
    assert _write(h, monkeypatch, {"start_ns": 15 * HOUR_NS, "end_ns": 14 * HOUR_NS, "cell": 1}) is None
    assert _write(h, monkeypatch, {"start_ns": 15 * HOUR_NS, "cell": -1}, placement=P.K_PLACE_HEAD) is None
    assert len(h.layer.book) == 0
    m = h.layer._c2_meter
    assert m["rejected:終わりが始まりより前"] == 1 and m["rejected:場所が空"] == 1
    assert m["rejected_shown"] == 1 and m["rejected_silent"] == 1
    rej = [e for e in h.events() if e.what == LY.W_REJECT]
    assert len(rej) == 2 and all(isinstance(e.cause, Process) and e.cause.name == "calendar2" for e in rej)


def test_late_and_closed_are_only_recorded(monkeypatch):
    h = Harness(cells=[0, 0, 0, 0, 0, 0])
    world_cells = np.asarray(h.world.pois.cell, dtype=np.int64)
    rep = np.asarray(h.world.assets.cell_rep_node, dtype=np.int64)
    h.agents.registry.node[0] = rep[0]
    far = int(rep.size - 1)
    rid = _write(h, monkeypatch, {"start_ns": 600 * STEP_NS + STEP_NS // 2, "cell": far})
    assert rid is not None  # 間に合わない予定も書ける(記録だけ)
    assert h.layer._c2_meter.get("impossible:write:間に合わない") == 1
    shop = int(world_cells[0])
    runner = SimpleNamespace(opening=SimpleNamespace(open_matrix=np.zeros((world_cells.size, 1440), dtype=bool)))
    h2 = Harness(cells=[0] * 6, runner=runner)
    rid2 = _write(h2, monkeypatch, {"start_ns": 15 * HOUR_NS, "cell": shop})
    assert rid2 is not None and h2.layer._c2_meter.get("impossible:write:閉店中") == 1


def test_app_warns_overlaps(monkeypatch):
    h = Harness()
    _write(h, monkeypatch, {"start_ns": 15 * HOUR_NS, "end_ns": 16 * HOUR_NS, "cell": 1})
    _write(h, monkeypatch, {"start_ns": 15 * HOUR_NS + HOUR_NS // 2, "end_ns": 17 * HOUR_NS, "cell": 2})
    _write(h, monkeypatch, {"start_ns": 15 * HOUR_NS + HOUR_NS // 2, "cell": 2}, placement=P.K_PLACE_PLANNER)
    assert h.layer._c2_meter.get("overlap_warned") == 1 and len(h.layer.book) == 3  # 警告は記録だけ(書くのは本人)


def _forget_step(h, a, rid, start_T, end_T):
    row = h.layer.book.rows[rid]
    for T in range(start_T, end_T):  # 書いてから思い出せなくなる最初の刻み(手がかりなし)
        if not h.layer.recall.recalled(a, row["trace"], T * STEP_NS, cue=False):
            return T
    raise AssertionError("この範囲で思い出せなくならない")


def test_head_row_is_seen_only_when_recalled_negative_control(monkeypatch):
    """頭の中の行は記憶で思い出せたときだけ見える。思い出せない刻みに考えても見えない(負の対照)・相手が同じ所に居れば手がかり。"""
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch, hour=23, by_agent={(1, P.P_PLACEMENT): [P.K_PLACE_HEAD]})
    r1 = next(r for r in h.layer.book.rows.values() if r["owner"] == 1)
    Tf = _forget_step(h, 1, r1["id"], 603, 23 * 60)
    assert h.layer.recall.recalled(1, r1["trace"], Tf * STEP_NS, cue=True)  # 手がかりがあれば思い出せる刻みを選ぶ
    m = h.layer._c2_meter
    hit0, miss0 = m.get("head_recall:思い出した", 0), m.get("head_recall:思い出せない", 0)
    h.step(Tf, main=(1,))  # 考えた(主の判断の呼び)=次の刻みに見る
    h.step(Tf + 1)
    assert h.layer.book.rows[r1["id"]]["seen"] == 0 and m.get("head_recall:思い出せない", 0) == miss0 + 1
    h.agents.registry.cell[0] = 1  # 約束の相手が同じ所に来た=手がかり
    h.step(Tf + 2, main=(1,))
    h.step(Tf + 3)
    assert h.layer.book.rows[r1["id"]]["seen"] == 1 and m.get("head_recall:思い出した", 0) == hit0 + 1


def test_head_row_recalled_soon_after_writing_and_rehearsal(monkeypatch):
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch, hour=23, by_agent={(1, P.P_PLACEMENT): [P.K_PLACE_HEAD]})
    r1 = next(r for r in h.layer.book.rows.values() if r["owner"] == 1)
    h.step(620, main=(1,))
    h.step(621)
    assert h.layer.book.rows[r1["id"]]["seen"] == 1
    assert h.layer.book.rows[r1["id"]]["trace"][0] == 2  # 思い出した回を痕跡に足した(想起の練習)


def test_arbitration_main_first_defers_the_look(monkeypatch):
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch)
    r0 = next(r for r in h.layer.book.rows.values() if r["owner"] == 0)
    h.step(700, main=(0,))
    h.step(701, main=(0,))  # まだ主の判断が続く=見ない
    assert h.layer.book.rows[r0["id"]]["seen"] == 0 and h.layer._c2_meter.get("arbitration:main_first", 0) >= 1
    h.step(702)
    assert h.layer.book.rows[r0["id"]]["seen"] == 1


def test_app_notification_then_depart_and_arrival_meters(monkeypatch):
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch, prefs={P.P_GO: [P.K_DEPART]})
    r0 = next(r for r in h.layer.book.rows.values() if r["owner"] == 0)
    nT = r0["notify_ns"] // STEP_NS
    for T in range(603, 16 * 60 + 1):
        h.step(T)
    m = h.layer._c2_meter
    assert m.get("notified:アプリ") == 2  # 体 0 と体 1 の各自のアプリ
    notes = [e for e in h.events() if e.what == LY.W_NOTIFY and e.who == 0]
    assert len(notes) == 1 and notes[0].t_ns == nT * STEP_NS and notes[0].cause == Process("calendar2")
    dep = [e for e in h.events() if e.what == LY.W_DEPART and e.who == 0]
    assert len(dep) == 1 and dep[0].t_ns == nT * STEP_NS  # 知らせの刻みに考えて出発した(もう居た)
    assert m.get("outcome:5 分前までに着いた", 0) >= 1 and m.get("plan_match:見た数", 0) >= 1
    assert LY.audit_causes(h.log.events(), step_ns=STEP_NS, issued=h.layer.issued_keys())["violations"] == 0


def test_alarm_while_asleep_is_seen_after_waking(monkeypatch):
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch, by_agent={(0, P.P_PLACEMENT): [P.K_PLACE_ALARM]})
    alarm = next(r for r in h.layer.book.rows.values() if r["kind"] == B.K_ALARM)
    promise = h.layer.book.rows[alarm["link"]]
    assert promise["owner"] == alarm["owner"] == 0 and promise["placement"] == B.PL_ALARM
    aT = alarm["notify_ns"] // STEP_NS
    h.agents.registry.activity[0] = int(Activity.SLEEPING)
    for T in range(603, aT + 1):
        h.step(T)
    assert h.layer._c2_meter.get("notified_asleep") == 1 and promise["seen"] == 0
    h.agents.registry.activity[0] = int(Activity.IDLE)
    h.step(aT + 1, main=(0,))
    h.step(aT + 2)
    assert h.layer.book.rows[promise["id"]]["seen"] == 1


def test_event_triggered_intention_cues_the_head_row(monkeypatch):
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch, hour=23, by_agent={(1, P.P_PLACEMENT): [P.K_PLACE_HEAD], (1, P.P_INTENT): [P.K_INTENT]})
    intent = next(r for r in h.layer.book.rows.values() if r["kind"] == B.K_INTENT)
    r1 = h.layer.book.rows[intent["link"]]
    assert intent["owner"] == 1 and intent["trigger"] == 0 and intent["placement"] == B.PL_HEAD
    Tf = _forget_step(h, 1, r1["id"], 603, 23 * 60)
    monkeypatch.setattr(h.layer.recall, "recalled", lambda a, trace, now, cue=False: bool(cue))  # 手がかりだけで思い出す
    h.agents.registry.cell[0] = 1  # きっかけ=相手に会った
    h.step(Tf, main=(1,))
    h.step(Tf + 1)
    assert h.layer._c2_meter.get("intentions:きっかけ") == 1 and h.layer.book.rows[r1["id"]]["seen"] == 1


def test_audit_catches_forged_and_engine_causes():
    log_events = [
        Event(t_ns=0, who=0, what=LY.W_DEPART, cause=LlmCall("0:0:-17", source="plan", number=1)),  # 連絡の形の id
        Event(t_ns=0, who=0, what=LY.W_WRITE, cause=Process("calendar2")),  # 本人の語の原因が道具
        Event(t_ns=0, who=0, what=LY.W_NOTIFY, cause=LlmCall(P.call_id_of(0, 0, P.serial_of(P.P_GO, 1)),
                                                              source="plan", number=1)),  # 道具の語の原因が判断
        Event(t_ns=STEP_NS, who=1, what=LY.W_DEPART, cause=LlmCall(P.call_id_of(1, 0, P.serial_of(P.P_GO, 1)),
                                                                   source="plan", number=1)),  # 体が違う
    ]
    got = LY.audit_causes(log_events, step_ns=STEP_NS, issued=np.zeros(0, dtype=np.int64))
    assert got["events"] == 4 and got["violations"] >= 4


def _many_rows(h, n, minute_of):
    for k in range(n):
        h.layer.book.write(0, {"kind": B.K_PROMISE, "start_ns": minute_of(k) * STEP_NS, "cell": 1, "with": [1],
                               "placement": B.PL_APP}, written_ns=0)


def _edit_turn(h, monkeypatch, seen):
    def rule(ctx, presented):
        _t, _a, serial = P.parse_call_id(ctx.call_id)
        if P.purpose_of_serial(serial) == P.P_EDIT:
            seen.append(sorted(c.id for c in presented))
        return _rule({**BASE, P.P_EDIT_WHAT: [P.K_EDIT_CERTAIN]}, {(0, P.P_TURN): [P.K_CHANGE]})(ctx, presented)

    monkeypatch.setattr(P.Calendar2Port, "_pick", lambda self, ctx, presented: rule(ctx, presented))
    h.live.add(1)
    h.layer.note_turn("f:1", 0, 600, "600:0:2", [0, 1])
    h.step(600)


def test_many_change_candidates_are_narrowed_by_the_person(monkeypatch):
    """〔検収 L4〕候補=見える行の全部。提示の番号の上限を超えると、本人が日 → 時刻で絞る(安全装置には当たらない)。"""
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _many_rows(h, LY.EDIT_MAX_CANDIDATES + 5, lambda k: 12 * 60 + k)  # 12:00〜14:04(同じ日・3 つの時)
    seen: list[list[str]] = []
    _edit_turn(h, monkeypatch, seen)
    assert len(seen) == 3 and seen[0] == ["eday:0"] and [x.split(":")[0] for x in seen[1]] == ["ehour"] * 3
    assert len(seen[2]) <= LY.EDIT_MAX_CANDIDATES and h.layer._c2_meter.get("edit_candidates_capped", 0) == 0
    assert h.layer._c2_meter.get("edit_narrowed:ehour") == 1


def test_change_candidates_safety_cap_counts_when_it_hits(monkeypatch):
    """同じ時刻の行が上限より多いと、絞っても残る=安全装置(始まりの近い順に上限まで)に当たって数える。"""
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _many_rows(h, LY.EDIT_MAX_CANDIDATES + 5, lambda k: 12 * 60)
    seen: list[list[str]] = []
    _edit_turn(h, monkeypatch, seen)
    assert len(seen[-1]) == LY.EDIT_MAX_CANDIDATES and h.layer._c2_meter.get("edit_candidates_capped") == 1


# ================================================================= 〔検収 M1〕時刻を変えたら知らせも同じだけずらす
def test_time_change_moves_the_app_notification(monkeypatch):
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch)  # 体 0=アプリ・15 時・30 分前の知らせ
    r0 = next(r for r in h.layer.book.rows.values() if r["owner"] == 0)
    p = {**BASE, P.P_HOUR: ["hour:18"]}
    monkeypatch.setattr(P.Calendar2Port, "_pick", lambda self, ctx, presented: _rule(
        p, {(0, P.P_TURN): [P.K_CHANGE]})(ctx, presented))
    h.layer.note_turn("f:1", 0, 610, "610:0:2", [0, 1])
    h.step(610)
    assert h.layer.book.rows[r0["id"]]["notify_ns"] == (18 * 60 - 30) * STEP_NS
    monkeypatch.setattr(P.Calendar2Port, "_pick", lambda self, ctx, presented: _rule(BASE)(ctx, presented))
    for T in range(611, 18 * 60 + 1):
        h.step(T)
    notes = [e for e in h.events() if e.what == LY.W_NOTIFY and e.who == 0]
    assert [e.t_ns // STEP_NS for e in notes] == [18 * 60 - 30]  # 17:30 に 1 行だけ(古い 14:30 は鳴らない)


def test_change_after_the_notification_leaves_no_past_marks(monkeypatch):
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch)
    for T in range(603, 14 * 60 + 35):
        h.step(T)
    assert [e.t_ns // STEP_NS for e in h.events() if e.what == LY.W_NOTIFY and e.who == 0] == [14 * 60 + 30]
    T = 14 * 60 + 35
    p = {**BASE, P.P_HOUR: ["hour:15"]}  # 同じ 15 時に「変える」=知らせ(14:30)は過ぎた=帳面に置かない
    monkeypatch.setattr(P.Calendar2Port, "_pick", lambda self, ctx, presented: _rule(
        p, {(0, P.P_TURN): [P.K_CHANGE]})(ctx, presented))
    h.layer.note_turn("f:1", 0, T, f"{T}:0:2", [0, 1])
    h.step(T)
    assert all(k > T for k in h.layer._agenda), sorted(h.layer._agenda)[:5]
    marks = [rid for k, v in h.layer._agenda.items() for code, rid in v if code == 0]
    assert all(rid != next(r for r in h.layer.book.rows.values() if r["owner"] == 0)["id"] for rid in marks)


# ================================================================= 〔検収 M2〕変える候補は見える行だけ
def test_forgotten_head_row_is_not_offered_for_change(monkeypatch):
    """思い出せない頭の中の行は「自分の約束を変える」の候補に出ない(取り消しも変更もできない)=負の対照。思い出せる刻みには出る。"""
    h = Harness(cells=[0, 1, 2, 3, 4, 5])
    _promise(h, monkeypatch, hour=23, by_agent={(1, P.P_PLACEMENT): [P.K_PLACE_HEAD]})
    r1 = next(r for r in h.layer.book.rows.values() if r["owner"] == 1)
    seen: list[set[str]] = []

    def rule(ctx, presented):
        _t, a, serial = P.parse_call_id(ctx.call_id)
        if int(a) == 1 and P.purpose_of_serial(serial) == P.P_TURN:
            seen.append({c.kind for c in presented})
        return _rule({**BASE, P.P_EDIT_WHAT: [P.K_EDIT_CANCEL]}, {(1, P.P_TURN): [P.K_CHANGE]})(ctx, presented)

    monkeypatch.setattr(P.Calendar2Port, "_pick", lambda self, ctx, presented: rule(ctx, presented))
    Tf = _forget_step(h, 1, r1["id"], 603, 23 * 60)
    h.layer.note_turn("p:0:1", 1, Tf, f"{Tf}:1:-9", [0])  # メッセージ=相手は別のセル(手がかりなし)
    h.step(Tf)
    assert seen[-1] == {P.K_PROPOSE, P.K_NO_PROPOSE}  # 「変える」が出ない
    assert h.layer.book.rows[r1["id"]]["state"] == B.ST_LIVE
    h.agents.registry.cell[0] = 1  # 相手が同じ所に居る(手がかり)=思い出せる
    h.layer.note_turn("p:0:1", 1, Tf + 1, f"{Tf + 1}:1:-9", [0])
    h.step(Tf + 1)
    assert P.K_CHANGE in seen[-1] and h.layer.book.rows[r1["id"]]["state"] == B.ST_CANCELLED
