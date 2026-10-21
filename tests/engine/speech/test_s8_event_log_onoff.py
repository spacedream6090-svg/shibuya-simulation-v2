"""第 1 期 1-8b 発話の口(腕 ``--speech-port on``)の直し=口の約束 1-3 の (1)「出来事の記録の on/off で結果が変わらない」。

C1 の直し(記録 ``ct_c1/README.md`` §16)と同じ形: 未読の列(状態台帳の腕の行 ``S8``=behavior)の目印は記録に依らない口の通し番号
``(t_ns, 通し番号)`` だけにし、記録に書いた出来事の id は診断の表 ``_mark_event_of``(行 ``S8E``=diag・required)に持つ。読み手は
次の発話の原因の入力(``report_shown`` → ``take_input_ids``)だけ。

- 合成 200 体+腕 on で記録 on/off の final と checkpoint の behavior-hash が同じ・計器(記録の側の ``events`` を除く)が同じ。
- 発話の原因の入力は記録にある発話の行を指す(診断の表から引いた)。
- 発話の直後(未読が残る刻み)で止めた再開=通し・再開した後の発話の行と原因(入力の出来事 id を含む)が通しと同じ。
- 口の単体: 記録 on/off で未読の列が同じ・溢れと期限切れで表から落ちる・描画の報告で記録の id に替わる。
- 負の対照: 未読の列に記録の id を戻す(直す前の形)と記録 on/off で behavior-hash が違う。
"""

from __future__ import annotations

import pytest

from shibuya.engine.events import log as EV
from shibuya.engine.events.log import EventLog, LlmCall
from shibuya.engine.speech import port as P
from shibuya.engine.speech.port import WHAT as W_SPEECH
from tests.engine.speech._s8b import run_small

NS = 60 * 10**9


def _on_off(**kw):
    prev = EV.enabled()
    try:
        EV.set_enabled(True)
        on = run_small("on", **kw)
        EV.set_enabled(False)
        off = run_small("on", **kw)
    finally:
        EV.set_enabled(prev)
    return on, off


@pytest.fixture(scope="module")
def on_off():
    return _on_off()


def test_event_log_on_off_does_not_change_the_s8_arm_run(on_off):
    on, off = on_off
    assert on.final_hash == off.final_hash
    cps = lambda r: [(int(c.tick), c.behavior_hash) for c in r.checkpoints]
    assert cps(on) == cps(off) and cps(on)
    m_on, m_off = on.speech_layer.meter, off.speech_layer.meter
    assert m_on["said"] > 0 and m_on["delivered"] > 0
    assert {k: v for k, v in m_on.items() if k != "events"} == {k: v for k, v in m_off.items() if k != "events"}
    assert on.speech_layer.inbox == off.speech_layer.inbox
    assert off.speech_layer._mark_event_of == {}


def test_speech_causes_point_at_logged_utterances(on_off):
    """発話の原因の入力の出来事 id は記録にある発話の行(診断の表から引いた)=聞こえた発話。"""
    on, _off = on_off
    log = on.event_log
    n = 0
    for ev in log.events():
        if ev.what != W_SPEECH:
            continue
        assert isinstance(ev.cause, LlmCall)
        for eid in ev.cause.input_event_ids:
            src = log.get(eid)
            if src.what == W_SPEECH:
                assert int(src.t_ns) < int(ev.t_ns) and src.whom == ev.who
                n += 1
    assert n > 0


def _speech_rows_from(r, t0):
    return [(int(e.t_ns), e.who, e.whom, e.how_much, e.cause) for e in r.event_log.events()
            if e.what == W_SPEECH and int(e.t_ns) >= t0]


def test_resume_restores_the_mark_table(tmp_path):
    """発話の直後(未読が残る刻み)で止めた再開=通し・再開した後の発話の行と原因が通しと同じ(診断の表が戻る)。"""
    straight = run_small("on")
    evs = [e for e in straight.event_log.events() if e.what == W_SPEECH]
    assert evs
    stop = int(evs[0].t_ns // NS) + 1
    a = run_small("on", state_out=str(tmp_path), stop_at_tick=stop)
    assert a.speech_layer._mark_event_of, "止めた刻みに表の行が無い(試験の前提)"
    path = next(tmp_path.glob("state-T*.npz"))
    b = run_small("on", resume_from=str(path))
    assert b.final_hash == straight.final_hash
    t0 = stop * NS
    got, want = _speech_rows_from(b, t0), _speech_rows_from(straight, t0)
    assert got == want and any(c.input_event_ids for *_x, c in got)


def _say(port, log, t_ns, a, b, sid=1):
    log.begin_step(int(t_ns))
    return port.say(P.SpeechContext(step=int(t_ns) // NS, call_id=f"{int(t_ns) // NS}:{a}:0", cell=0, session=sid),
                    P.Utterance(speaker=a, t_ns=int(t_ns), text="やあ", addressees=(b,)))


def test_unit_marks_are_log_independent_and_the_table_is_bounded():
    on_log, off_log = EventLog(enabled=True), EventLog(enabled=False)
    on, off = P.SpeechPort(events=on_log), P.SpeechPort(events=off_log)
    for port, log in ((on, on_log), (off, off_log)):
        for k in range(5):  # 届け先ごとの上限 3 を超える=溢れた 2 つは表から落ちる
            _say(port, log, 0, 1, 2)
    assert on.inbox == off.inbox and len(on.inbox[2]) == P.HEARD_MAX_PER_ADDRESSEE
    assert len(on._mark_event_of) == P.HEARD_MAX_PER_ADDRESSEE and off._mark_event_of == {}
    assert on.meter["overflow"] == 2
    # 渡して描画が報告した分は記録の id に替わり(次の発話の原因の入力)、表と控えから落ちる
    heard = on.take_heard(2, 1)
    shown = tuple(e for e, _w, _t in heard[:2])
    on.report_shown(2, shown, 0, 0)
    ids = on.take_input_ids(2)
    assert len(ids) == 2 and all(on_log.get(e).what == W_SPEECH for e in ids)
    assert on._mark_event_of == {} and on._heard_taken == {}
    off.report_shown(2, tuple(e for e, _w, _t in off.take_heard(2, 1)[:2]), 0, 0)
    assert off.take_input_ids(2) == ()
    # 閉じたセッションの古い未読(期限切れ)も表から落ちる
    _say(on, on_log, 0, 3, 4)
    assert len(on._mark_event_of) == 1
    assert on.take_heard(4, P.HEARD_TTL_STEPS + 5) == () and on.meter["expired"] == 1
    assert on._mark_event_of == {}


def test_negative_control_log_ids_in_the_inbox_break_the_on_off_equality(monkeypatch):
    """負の対照: 未読の列の目印を記録の id に戻す(直す前の形)と記録 on/off で behavior-hash が違う。"""
    real = P.SpeechPort.say

    def say(self, ctx, utterance):
        eid = real(self, ctx, utterance)
        for a in utterance.addressees:
            q = self.inbox.get(int(a))
            if q and int(self.meter["events"]) and q[-1][0] in self._mark_event_of:
                q[-1] = (self._mark_event_of[q[-1][0]], *q[-1][1:])
        return eid

    monkeypatch.setattr(P.SpeechPort, "say", say)
    on, off = _on_off()
    assert [c.behavior_hash for c in on.checkpoints] != [c.behavior_hash for c in off.checkpoints]
