"""第 6 期 6-4 C1 の直し=口の約束 1-3 の (1)「出来事の記録の on/off で結果が変わらない」(カレンダー 2 の検収 M3 と同じ形)。

- 出来事の記録の id は behavior の行(届いた箱 ``CT1I``・通話の発話の未読の列 ``CT1S``)に置かず、診断の表(腕の行 ``CT1Q``=
  ``contact._ct_event_of``・``contact.speech._mark_event_of``)に持つ。読み手は読む判断と通話の番の判断の原因の入力だけ。
- 合成 80 体+腕 c1 で記録 on/off の final と checkpoint の behavior-hash が同じ(メッセージの道と、通話を起こす道の 2 つ)。
- 原因の入力は診断の表から引く(読んだ・通話の番の入力の出来事 id が記録にある届いた/送った/発話の行を指す)・監査の食い違い 0。
- 日の途中の再開で診断の表が戻る(再開した後の原因の入力が通しと同じ)。
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from shibuya.engine.contact import layer as LY
from shibuya.engine.contact import port as P
from shibuya.engine.contact.calls import CallSpeechPort
from shibuya.engine.contact.layer import W_DELIVERED, W_READ, W_SENT
from shibuya.engine.events import log as EV
from shibuya.engine.events.log import EventLog, LlmCall
from shibuya.engine.run import run_day
from shibuya.engine.speech.port import WHAT as W_SPEECH
from shibuya.engine.speech.port import SpeechContext, Utterance
from shibuya.engine.tools import record as TR
from shibuya.engine.tools.groups import GroupList

from tests.engine.contact._c1 import KW, STEP_NS, c1


@pytest.fixture
def with_groups(monkeypatch):
    real = TR.build_fixture

    def build(pop, n_agents, events):
        fx = real(pop, n_agents, events)
        if fx.groups is not None:
            return fx
        ids = np.arange(int(n_agents))
        return dataclasses.replace(fx, groups=GroupList(household_id=ids // 2, org_id=ids // 10))

    monkeypatch.setattr(TR, "build_fixture", build)
    yield


def _prefer_calls(monkeypatch):
    """仮のモデルの規則を差し替えて通話を起こす(test_c1_fixes の L8 と同じ形)。"""
    real = P.ContactPort._pick
    order = (P.K_ANSWER, P.K_TALK, P.K_WAIT, P.K_CALL, P.K_TO, P.K_READ_NOW, P.K_LOOK)

    def pick(self, ctx, presented):
        kinds = {c.kind: c.id for c in presented}
        for k in order:
            if k in kinds:
                return kinds[k]
        return real(self, ctx, presented)

    monkeypatch.setattr(P.ContactPort, "_pick", pick)


def _on_off(kw):
    prev = EV.enabled()
    try:
        with c1():
            EV.set_enabled(True)
            on = run_day(**kw)
            EV.set_enabled(False)
            off = run_day(**kw)
    finally:
        EV.set_enabled(prev)
    return on, off


def _same_behavior(on, off):
    assert on.final_hash == off.final_hash
    cps = lambda r: [(int(c.tick), c.behavior_hash) for c in r.checkpoints]
    assert cps(on) == cps(off) and cps(on)


def _inputs_point_at_logged_rows(r, what, allowed):
    """``what`` の行の原因の入力の出来事 id が、記録にある ``allowed`` の語の行を指す(診断の表から引いた)。→ 入力の数。"""
    log = r.event_log
    n = 0
    for ev in log.events():
        if ev.what != what:
            continue
        c = ev.cause
        assert isinstance(c, LlmCall)
        for eid in c.input_event_ids:
            src = log.get(eid)
            assert src.what in allowed, (ev, src)
            assert int(src.t_ns) <= int(ev.t_ns)
            n += 1
    return n


def test_event_log_on_off_does_not_change_the_c1_arm_run(with_groups):
    """合成 80 体・720 刻み・腕 c1(メッセージとグループの道): 記録 on/off で final と checkpoint の behavior-hash が同じ。"""
    on, off = _on_off(dict(KW))
    _same_behavior(on, off)
    lay, lay_off = on.contact_layer, off.contact_layer
    # 目印は診断の表だけ(記録しないランは空)・届いた行は記録に依らない欄だけ
    assert lay._ct_event_of and not lay_off._ct_event_of
    assert {len(r) for v in lay.mail._inbox.values() for r in v} == {9}
    assert lay.mail._inbox == lay_off.mail._inbox
    # 読む判断の原因の入力=診断の表から引いた届いた行(1 対 1)か送った行(グループ=畳んだ 1 行)
    assert _inputs_point_at_logged_rows(on, W_READ, {W_DELIVERED, W_SENT}) > 0
    au = LY.audit_causes(on.event_log.events(), step_ns=STEP_NS, issued=lay.issued_keys())
    assert au["violations"] == 0 and au["events"] > 0


def test_event_log_on_off_does_not_change_the_c1_arm_run_with_calls(with_groups, monkeypatch):
    """通話を起こす合成のラン: 通話の発話の未読の列は口の目印だけ・記録 on/off で同じ・番の原因の入力は発話の行。"""
    _prefer_calls(monkeypatch)
    on, off = _on_off(dict(KW, ticks=240, checkpoint_every=30, relations="off"))
    assert on.run_manifest_fields()["contact_c1"]["meter"].get("call_turns", 0) > 0
    _same_behavior(on, off)
    lay, lay_off = on.contact_layer, off.contact_layer
    assert lay.speech.inbox == lay_off.speech.inbox
    assert not lay_off.speech._mark_event_of
    talks = [e for e in on.event_log.events() if e.what == W_SPEECH and e.via == "通話"]
    assert talks
    assert _inputs_point_at_logged_rows(on, W_SPEECH, {W_SPEECH}) > 0
    au = LY.audit_causes(on.event_log.events(), step_ns=STEP_NS, issued=lay.issued_keys())
    assert au["violations"] == 0


def _causes_from(r, t0):
    return [(int(e.t_ns), e.who, e.what, e.cause) for e in r.event_log.events()
            if int(e.t_ns) >= t0 and str(e.what).startswith(("連絡:", "行為:発話"))]


def test_resume_restores_the_event_id_tables(with_groups, monkeypatch, tmp_path):
    """日の途中の再開で診断の表が戻る=再開した後の連絡の行と原因(入力の出来事 id を含む)が通しと同じ。"""
    _prefer_calls(monkeypatch)
    stop = 97
    kw = dict(KW, ticks=240, checkpoint_every=30, relations="off")
    with c1():
        straight = run_day(**kw)
        a = run_day(state_out=tmp_path / "state", stop_at_tick=stop, **kw)
        assert a.contact_layer._ct_event_of or a.contact_layer.speech._mark_event_of  # 止めた時刻に目印がある(試験の前提)
        path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
        b = run_day(resume_from=path, **kw)
    assert b.final_hash == straight.final_hash
    t0 = stop * STEP_NS
    got, want = _causes_from(b, t0), _causes_from(straight, t0)
    assert got == want and any(isinstance(c, LlmCall) and c.input_event_ids for *_x, c in got)


def _port(enabled: bool) -> tuple[CallSpeechPort, EventLog]:
    log = EventLog(enabled=enabled)
    return CallSpeechPort(events=log), log


def _say(port: CallSpeechPort, log: EventLog, t_ns: int, a: int, b: int) -> None:
    log.begin_step(int(t_ns))
    port.say(SpeechContext(step=int(t_ns) // STEP_NS, call_id=P.call_id_of(int(t_ns) // STEP_NS, a, 5), cell=0,
                           session=1),
             Utterance(speaker=a, t_ns=int(t_ns), text="もしもし", addressees=(b,), via="通話"))


def test_call_speech_inbox_holds_only_log_independent_marks():
    """通話の発話の口(発話の口の子)の未読の列は記録 on/off で同じ(口の目印)・記録の id は診断の表・引いたら落ちる。"""
    on, log_on = _port(True)
    off, log_off = _port(False)
    for port, log in ((on, log_on), (off, log_off)):
        _say(port, log, 0, 1, 2)
        _say(port, log, 0, 2, 1)
        _say(port, log, STEP_NS, 1, 2)
    assert on.inbox == off.inbox
    assert len(on._mark_event_of) == 3 and off._mark_event_of == {}
    heard = on.take_heard(2, 2)
    ids = on.event_ids(2, [e for e, _w, _t in heard])
    assert len(ids) == 2 and all(log_on.get(e).what == W_SPEECH for e in ids)
    assert len(on._mark_event_of) == 1 and not on._heard_taken  # 渡した分は表から落ち・引いたら控えも落ちた
    assert off.event_ids(2, [e for e, _w, _t in off.take_heard(2, 2)]) == ()


def test_negative_control_eid_in_the_behavior_row_breaks_the_on_off_equality(with_groups, monkeypatch):
    """負の対照: 届いた行に出来事の id を戻すと(直す前の形)記録 on/off で behavior-hash が違う。"""
    real = LY.ContactLayer._send_now

    def send_now(self, t, row):
        n0 = {a: len(v) for a, v in self.mail._inbox.items()}
        real(self, t, row)
        for a, marks in self._ct_event_of.items():
            rows = self.mail._inbox.get(a, [])
            if len(rows) > n0.get(a, 0) and len(rows[-1]) == 9:
                rows[-1].extend(marks[-1][1:])

    monkeypatch.setattr(LY.ContactLayer, "_send_now", send_now)
    on, off = _on_off(dict(KW, ticks=240))
    assert [c.behavior_hash for c in on.checkpoints] != [c.behavior_hash for c in off.checkpoints]
