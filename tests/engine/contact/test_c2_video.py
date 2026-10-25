"""第 6 期 6-4 C2: ビデオ通話(電話の器の種類違い)。かける/出るは本人・目の向き=画面(相手の顔)・関心の的=通話・電池の減りは
通話より大きい・発話は ``Utterance``(via=ビデオ通話)で 1 回だけ記録・知覚の事実は ``tool_state`` の ``call_via``(形と版は不変)。"""

from __future__ import annotations

from shibuya.engine.contact import attention as AT
from shibuya.engine.contact import device as DV
from shibuya.engine.contact import port as P
from shibuya.engine.contact.layer import W_ANSWER, W_CALL_END, W_DIAL, W_RING, W_VIDEO_DIAL, audit_causes
from shibuya.engine.events import vocab as V
from shibuya.perception import contact_view as CV

from tests.engine.contact._c1 import STEP_NS
from tests.engine.contact._c2 import Harness2, loud


def _rule(first: str):
    said = {"n": 0}

    def rule(ctx, presented):
        kinds = {c.kind: c.id for c in presented}
        if P.K_TALK in kinds:  # 通話の番: 最初の番だけ話し、次は切る
            if said["n"] == 0:
                said["n"] += 1
                return kinds[P.K_TALK]
            return kinds[P.K_HANG]
        if first in kinds and not said.get("dialed"):  # かけるのは 1 回だけ(終わった後も画面を見ている)
            said["dialed"] = 1
            return kinds[first]
        for k in (P.K_TO, P.K_ANSWER, P.K_WAIT, P.K_KEEP):
            if k in kinds:
                return sorted(c.id for c in presented if c.kind == k)[0]
        return sorted(c.id for c in presented)[0]
    return rule


def _call(monkeypatch, first: str):
    monkeypatch.setattr(P.ContactPort, "_pick", lambda self, ctx, presented, r=_rule(first): r(ctx, presented))
    h = Harness2()
    loud(h)
    h.layer.attn.look_at_screen([0], 0)
    seen = {}

    def watch(hh, T):
        for s in hh.layer.calls.sessions.values():
            seen.setdefault("video", hh.layer.calls.is_video(s.session_id))
            seen.setdefault("gaze1", int(hh.layer.attn._gaze[1]))
            seen.setdefault("focus1", int(hh.layer.attn._focus[1]))
    h.before_step = watch
    b0 = float(h.layer.dev._battery[1])
    h.run(6)
    return h, seen, b0


def test_video_call_round_trip(monkeypatch):
    h, seen, b0 = _call(monkeypatch, P.K_VIDEO)
    dial = h.of(W_VIDEO_DIAL)
    assert [(e.who, e.whom, e.via) for e in dial] == [(0, 1, "ビデオ通話")] and not h.of(W_DIAL)
    assert [e.via for e in h.of(W_RING)] == ["ビデオ通話"]
    ans = h.of(W_ANSWER)
    assert [(e.who, e.via) for e in ans] == [(1, "ビデオ通話")]
    utt = [e for e in h.log.events() if e.what == V.word(V.FAMILY_ACT, "発話")]
    assert len(utt) == 1 and utt[0].via == "ビデオ通話"  # 発話は 1 回だけ記録
    assert {e.via for e in h.of(W_CALL_END)} == {"ビデオ通話"}
    assert seen == {"video": True, "gaze1": AT.GAZE_SCREEN, "focus1": AT.FOCUS_CALL}  # 目は画面(相手の顔)・心は通話
    assert h.layer._meter.get("video:placed") == 1 and h.layer._meter.get("video:turns") == 1
    assert h.layer.calls._video == {}  # 終わったら印を落とす
    assert audit_causes(h.log.events(), step_ns=STEP_NS, issued=h.layer.issued_keys())["violations"] == 0


def test_video_drains_more_than_a_voice_call(monkeypatch):
    hv, _s, b0 = _call(monkeypatch, P.K_VIDEO)
    hc, _s2, b1 = _call(monkeypatch, P.K_CALL)
    assert b0 == b1
    assert float(hv.layer.dev._battery[1]) < float(hc.layer.dev._battery[1])
    assert DV.DRAIN_PER_HOUR[DV.USE_VIDEO] > DV.DRAIN_PER_HOUR[DV.USE_CALL]


def test_percept_value_marks_the_face_without_changing_the_shape():
    base = dict(battery_pct=90, on=True, manner=False, place="手", earphones=False, signal=True, notice_kind=None,
                notice_level=None, notice_channels=(), unread=None, ringing_from=None, in_call_with=3, chats=None)
    voice = CV.contact_lines(None, CV.DeviceView(**base), lambda a: f"P-{a}")
    video = CV.contact_lines(None, CV.DeviceView(**base, call_via="ビデオ通話"), lambda a: f"P-{a}")
    assert voice == ["[B6 通話] P-3と通話中。"] and video == ["[B6 通話] P-3とビデオ通話中(画面に相手の顔が見える)。"]
    ring = dict(base, in_call_with=None, ringing_from=3)
    assert CV.contact_lines(None, CV.DeviceView(**ring), lambda a: f"P-{a}") == ["[B6 着信] P-3からの電話が鳴っている。"]
    assert CV.contact_lines(None, CV.DeviceView(**ring, ringing_via=CV.VIA_VIDEO), lambda a: f"P-{a}") == \
        ["[B6 着信] P-3からのビデオ通話が鳴っている。"]  # 〔検収 L8〕着信の行で via を区別
    from shibuya.engine.contact import calls as CL
    from shibuya.engine.contact import deliver as DL
    from shibuya.perception.facts import PERCEPT_SCHEMA

    assert PERCEPT_SCHEMA == "shibuya.perception/percept/2"  # Percept の形の版は触っていない(値は既存の欄 tool_state)
    assert DL.VIA_VIDEO is CV.VIA_VIDEO and CL.VIA_VIDEO is CV.VIA_VIDEO and CV.VIA_VIDEO in V.VIA_WORDS  # 定義は 1 か所


def test_via_vocabulary_is_closed_and_versioned():
    assert V.VIA_WORDS[-1] == "ビデオ通話" and V.VIA_WORDS[:6] == ("対面", "通話", "メッセージ", "グループ", "SNS", "無し")
    assert V.VOCAB_VERSION == "events-vocab/6-4-c2"
