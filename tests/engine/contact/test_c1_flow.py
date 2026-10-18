"""第 6 期 6-4 C1 合成の流れ(連絡の層と進行役の待ち行列だけを回す台): 届く(送った時刻)・打ち終わりと着信は窓の境目・
気づく/読む/返すは本人の判断・既読・チャットの状態・電話(対面の会話の仕組み)・範囲の外の人・送る文の腕 (c)・長さの上限。"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.engine import batching as BA
from shibuya.engine.contact import attention as AT
from shibuya.engine.contact import deliver as DL
from shibuya.engine.contact import device as DV
from shibuya.engine.contact import port as P
from shibuya.engine.contact.layer import (
    W_ANSWER, W_CALL_END, W_DELIVERED, W_DIAL, W_HANG, W_LATER, W_READ, W_RING, W_SENT, audit_causes,
)
from shibuya.engine.conversation import ConvState
from shibuya.engine.events.log import LlmCall, Process

from tests.engine.contact._c1 import STEP_NS, Harness, by_kind, choose


def _loud(h: Harness) -> None:
    """全員の電話を手に持ち・音あり・イヤホンなし(気づく道を決める)。"""
    d = h.layer.dev
    d._manner[:] = False
    d._place[:] = DV.PLACE_HAND
    d._home[:] = DV.PLACE_HAND
    d._ear[:] = False


def _of(h: Harness, what: str) -> list:
    return [e for e in h.events() if e.what == what]


def test_message_is_typed_until_the_boundary_and_delivered_at_send_time(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_SEND, P.K_TO, P.K_READ_NOW, P.K_NOREPLY, P.K_KEEP)):
        h = Harness()
        _loud(h)
        h.layer.attn.look_at_screen([0], 0)  # 体 0 は画面を見ている(本人の前の判断の代わり)
        h.run(3)
    sent = _of(h, W_SENT)
    assert sent, "送った出来事が無い"
    s0 = sent[0]
    assert s0.who == 0 and s0.whom == 1 and s0.via == "メッセージ" and isinstance(s0.cause, LlmCall)
    st = P.step_of_call_id(s0.cause.call_id)
    assert s0.t_ns == (st + 1) * STEP_NS  # 打ち終わり=判断の刻みの次の窓の境目
    dl = [e for e in _of(h, W_DELIVERED) if e.whom == 0 and e.t_ns == s0.t_ns]
    assert dl and dl[0].who == 1 and dl[0].received_ns == s0.t_ns and dl[0].cause == Process("contact")
    rd = [e for e in _of(h, W_READ) if e.who == 1]
    assert rd and rd[0].t_ns == rd[0].read_ns >= s0.t_ns and isinstance(rd[0].cause, LlmCall)
    assert rd[0].read_ns == P.step_of_call_id(rd[0].cause.call_id) * STEP_NS  # 読んだ時刻=本人の判断の時刻
    assert dl[0].id in rd[0].cause.input_event_ids  # 届いた行が読む判断の原因の入力
    assert rd[0].whom == 0 and rd[0].how_much == 1  # 〔検収 M3〕読んだは会話ごとに 1 行(通数)・既読の行は書かない
    assert not [e for e in h.events() if e.what == "連絡:既読"]
    assert audit_causes(h.log.events(), step_ns=STEP_NS, issued=h.layer.issued_keys())["violations"] == 0


@pytest.mark.parametrize("width_s", [60, 30])
def test_ring_arrives_at_the_window_boundary(monkeypatch, width_s):
    with choose(monkeypatch, by_kind(P.K_CALL, P.K_TO, P.K_WAIT, P.K_DECLINE, P.K_KEEP)):
        h = Harness(width_s=width_s)
        _loud(h)
        h.layer.attn.look_at_screen([0], 0)
        h.run(3)
    dial = _of(h, W_DIAL)
    ring = _of(h, W_RING)
    assert dial and ring and ring[0].who == dial[0].whom and ring[0].whom == dial[0].who
    w = width_s * 10**9
    assert ring[0].t_ns > dial[0].t_ns and ring[0].t_ns - dial[0].t_ns <= w and ring[0].t_ns % w == 0
    assert ring[0].received_ns == ring[0].t_ns
    assert h.queue.window_counts["boundary_events"] >= 1


def test_negative_control_ring_inside_the_window_fails_the_boundary_check(monkeypatch):
    """負の対照: 着信の種類を窓の中で届ける(IN_WINDOW)にすると、かけた時刻と同じ時刻に鳴る=境目の確かめが落ちる。"""
    monkeypatch.setattr(DL, "RING_DELIVERY", BA.IN_WINDOW)
    with choose(monkeypatch, by_kind(P.K_CALL, P.K_TO, P.K_WAIT, P.K_DECLINE, P.K_KEEP)):
        h = Harness()
        _loud(h)
        h.layer.attn.look_at_screen([0], 0)
        h.run(3)
    dial, ring = _of(h, W_DIAL), _of(h, W_RING)
    assert dial and ring
    assert not (ring[0].t_ns > dial[0].t_ns)  # 境目の確かめ(上の試験の条件)が成り立たない


def test_call_uses_the_conversation_mechanism_and_hang_up_is_the_person(monkeypatch):
    turns = {"n": 0}

    def rule(ctx, presented):
        kinds = {c.kind: c.id for c in presented}
        if P.K_TALK in kinds:
            turns["n"] += 1
            return kinds[P.K_TALK] if turns["n"] <= 2 else kinds[P.K_HANG]
        for k in (P.K_CALL, P.K_TO, P.K_WAIT, P.K_ANSWER, P.K_KEEP):
            if k in kinds:
                return kinds[k]
        return presented[0].id

    with choose(monkeypatch, rule):
        h = Harness()
        _loud(h)
        h.layer.attn.look_at_screen([0], 0)
        h.run(8)
    ans = _of(h, W_ANSWER)
    assert ans and isinstance(ans[0].cause, LlmCall)
    talk = [e for e in h.log.events() if e.what == "行為:発話"]
    assert len(talk) == 2 and all(e.via == "通話" for e in talk)
    assert talk[1].cause.input_event_ids == (talk[0].id,)  # 相手の発言が次の番の入力(TM3)
    hang = _of(h, W_HANG)
    assert hang and isinstance(hang[0].cause, LlmCall)
    ends = _of(h, W_CALL_END)
    assert len(ends) == 2 and all(isinstance(e.cause, LlmCall) for e in ends)  # 切ったのは本人
    assert h.layer.calls.closed_by_reason.get("退去") == 1 and not h.layer.calls.sessions
    assert h.layer._ct_hist["call_steps"]


def test_call_hits_the_safety_limit_of_turns(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_TALK, P.K_CALL, P.K_TO, P.K_WAIT, P.K_ANSWER, P.K_KEEP)):
        h = Harness()
        _loud(h)
        h.layer.attn.look_at_screen([0], 0)
        h.run(12)
    ends = _of(h, W_CALL_END)
    assert len(ends) == 2 and all(e.cause == Process("conversation") for e in ends)  # 上限=安全装置(記録)
    assert h.layer.calls.closed_by_reason.get("hard") == 1
    assert h.layer._meter.get("calls_closed:hard") == 1


def test_group_message_and_chat_state(monkeypatch):
    def rule(ctx, presented):
        kinds = {c.kind: c.id for c in presented}
        if ctx.agent_id == 0:
            for k in (P.K_SEND_GROUP, P.K_GROUP):
                if k in kinds:
                    return [c.id for c in presented if c.kind == k and c.id.endswith(":2")][0] \
                        if k == P.K_GROUP else kinds[k]
            return kinds.get(P.K_KEEP, presented[0].id)
        for k in (P.K_READ_NOW, P.K_REPLY, P.K_KEEP):
            if k in kinds:
                return kinds[k]
        return presented[0].id

    with choose(monkeypatch, rule):
        h = Harness()
        _loud(h)
        h.layer.attn.look_at_screen([0], 0)
        h.run(1)
        sent0 = _of(h, W_SENT)
        h.run(3)
    g = [e for e in _of(h, W_SENT) if e.via == "グループ"]
    assert g and g[0].whom == "group:2"
    # 〔検収 M3 ①〕グループの「届いた」は「送った」の 1 行に畳む=届いた行の目印は送った行
    assert not [e for e in _of(h, W_DELIVERED) if e.via == "グループ"]
    for r in (1, 2):
        rows = [x for x in h.layer.mail._inbox.get(r, []) if int(x[2]) == 2]
        assert rows and (int(rows[0][9]), int(rows[0][10])) == g[0].id
    s = h.layer.chats.session("g:2")
    assert s is not None and s.state is ConvState.PARTICIPATING and s.blocks >= 2  # 返事で続いているチャット
    assert sent0 == []  # 刻み 0 の窓の中では送らない(打ち終わりは境目)


def test_notice_gate_by_strength_and_focus(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_LATER)):
        h = Harness()
        d = h.layer.dev
        d._ear[:] = False
        d._manner[1], d._place[1] = True, DV.PLACE_BAG      # 届かない
        d._manner[2], d._place[2] = True, DV.PLACE_POCKET   # 弱い
        d._manner[3], d._place[3] = False, DV.PLACE_HAND    # 強い
        mb = h.layer.mail
        for r in (1, 2, 3):
            mb.deliver(mb.new_message_id(), 0, [r], -1, 0, 0, 5, "こんにちは", lambda a: True)
        h.layer.calls.invite(2, 4, 0, -1, same_cell=True, partner_idle=True, answered=True)  # 2 は通話中(弱い刺激は割り込めない)
        # 〔検収 M4〕関心の的は刻みの終わりに置き直す=前の刻みの終わりの値(ここでは手で置く)を門が読む
        in_call = np.zeros(6, dtype=bool)
        in_call[[2, 4]] = True
        h.layer.attn.sync(in_call, np.zeros(6, dtype=bool))
        h.run(1)
    m = h.layer._meter
    assert m["stimulus:届かない"] == 1 and m["stimulus:弱い"] == 1 and m["stimulus:強い"] == 1
    assert m["noticed"] == 1 and m["not_noticed"] == 2 and m["noticed:周り"] == 1 and m["not_noticed:通話"] == 1
    later = _of(h, W_LATER)
    assert [e.who for e in later] == [3]


def test_outside_person_replies_and_carries_the_origin_mark(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_SEND, P.K_TO, P.K_READ_NOW, P.K_REPLY, P.K_KEEP)):
        h = Harness(cells=[-1, 0, 0, 0, 0, 0])  # 体 0 は範囲の外(体は持つ)
        _loud(h)
        h.layer.attn.look_at_screen([0], 0)
        h.run(4)
    s = [e for e in _of(h, W_SENT) if e.who == 0]
    assert s and s[0].origin == DL.OUTSIDE_ORIGIN
    assert any(e.origin == DL.OUTSIDE_ORIGIN for e in _of(h, W_DELIVERED) if e.whom == 0)
    replies_to_0 = [e for e in _of(h, W_DELIVERED) if e.who == 0]
    assert replies_to_0, "範囲の外の人にも返事が届き、本人の判断で読む"


def test_send_arm_c_sends_the_choice_words(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_SEND, P.K_TO, P.K_KEEP)):
        h = Harness(send="c")
        _loud(h)
        h.layer.attn.look_at_screen([0], 0)
        h.run(2)
    rows = h.layer.mail._inbox[1]
    assert rows and rows[0][8] == P.K_SEND  # 選択の言葉をそのまま


def test_length_cap_is_recorded_in_the_layer(monkeypatch):
    monkeypatch.setattr(P.MockTextPort, "write", lambda self, **kw: "あ" * (P.MESSAGE_MAX_CHARS + 10))
    with choose(monkeypatch, by_kind(P.K_SEND, P.K_TO, P.K_KEEP)):
        h = Harness()
        _loud(h)
        h.layer.attn.look_at_screen([0], 0)
        h.run(2)
    assert h.layer._meter["length_cap_hits"] >= 1
    assert len(h.layer.mail._inbox[1][0][8]) == P.MESSAGE_MAX_CHARS


def test_screen_end_records_minutes_and_sleep_closes_the_screen(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_KEEP)):
        h = Harness()
        h.layer.attn.look_at_screen([0, 1], 0)
        h.run(3)
        h.agents.registry.activity[1] = 4  # 寝た(本人が寝るを選んだ)
        h.run(1)
    assert int(h.layer.attn.gaze([1])[0]) == AT.GAZE_FRONT and int(h.layer.attn.gaze([0])[0]) == AT.GAZE_SCREEN
    assert h.layer._meter["screen_end:sleep"] == 1 and h.layer._ct_hist["screen_minutes"] == {"3": 1}


def test_negative_control_an_engine_rule_for_reading_is_caught(monkeypatch):
    """負の対照: 判断の口を通さずに読む(エンジンが時刻を決める)形に差し替えると、監査が食い違いを数える。"""
    from shibuya.engine.contact import layer as LY

    real = LY.ContactLayer._decide

    def engine_rule(self, T, t_ns, a, purpose, cands):
        c, cause = real(self, T, t_ns, a, purpose, cands)
        # 読む判断だけ原因=エンジン(本人の判断でない)にする
        return c, (Process("contact") if purpose == P.P_NOTICE else cause)

    monkeypatch.setattr(LY.ContactLayer, "_decide", engine_rule)
    with choose(monkeypatch, by_kind(P.K_SEND, P.K_TO, P.K_READ_NOW, P.K_NOREPLY, P.K_KEEP)):
        h = Harness()
        _loud(h)
        h.layer.attn.look_at_screen([0], 0)
        h.run(3)
    assert audit_causes(h.log.events(), step_ns=STEP_NS)["violations"] > 0


def test_device_off_holds_messages_and_rings_are_unreachable(monkeypatch):
    with choose(monkeypatch, by_kind(P.K_CALL, P.K_TO, P.K_KEEP)):
        h = Harness()
        _loud(h)
        h.layer.dev._on[1] = False
        h.layer.attn.look_at_screen([0], 0)
        h.run(3)
    assert h.layer._meter.get("unreachable_off") == 1 and not _of(h, W_RING)
    mb = h.layer.mail
    got, held = mb.deliver(mb.new_message_id(), 0, [1], -1, 0, 0, 1, "x", lambda a: bool(h.layer.dev._on[a]))
    assert held == [1] and got == []


def test_pending_rows_are_rescheduled_at_the_boundary_after_a_rebind(monkeypatch):
    """再開の形: 予約の表に残った送信を新しい待ち行列に結び直すと、境目の時刻で届く(通しと同じ時刻)。"""
    with choose(monkeypatch, by_kind(P.K_SEND, P.K_TO, P.K_KEEP)):
        h = Harness()
        _loud(h)
        h.layer.attn.look_at_screen([0], 0)
        h.run(1)  # 刻み 0 で打ち始め(境目 60 秒の予約)
        rows = h.layer.mail.pending_items()
        assert len(rows) == 1 and rows[0][1][2] == STEP_NS
        # 新しい待ち行列(再開)に結び直す
        q = BA.WindowQueue(width_s=60, start_ns=STEP_NS, step_s=60)
        h.layer._queue = None
        h.layer._seq_key.clear()
        h.layer.bind_queue(q)
        q.run_window()
    sent = _of(h, W_SENT)
    assert sent and sent[0].t_ns == STEP_NS
    assert np.isfinite(float(h.layer.dev.battery()[0]))
