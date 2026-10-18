"""第 6 期 6-4 C1 合成の単体: 道具の状態と刺激・周辺視の形・割り込めなかった出来事の腕・チャットの状態・既読・宛先・長さの上限・
体の無い人・判断の口・負の対照の監査・腕の切替。"""

from __future__ import annotations

import dataclasses
import itertools

import numpy as np
import pytest

from shibuya.agents.state import WakeCondition
from shibuya.engine.contact import arm as A
from shibuya.engine.contact import attention as AT
from shibuya.engine.contact import device as DV
from shibuya.engine.contact import port as P
from shibuya.engine.contact.book import ContactBook
from shibuya.engine.contact.chat_state import CHAT_MAX_BLOCKS, CHAT_SILENCE_STEPS, ChatBook, pair_key
from shibuya.engine.contact.deliver import Mailbox
from shibuya.engine.contact import layer as LY
from shibuya.engine.contact.layer import ENGINE_WORDS, PERSON_WORDS, W_DELIVERED, W_LATER, W_READ, W_SENT, audit_causes
from shibuya.engine.conversation import ConvState
from shibuya.engine.decision.port import DecisionContext
from shibuya.engine.events.log import Event, LlmCall, Process
from shibuya.engine.tools import contacts as CT
from shibuya.engine.tools.groups import GroupList
from shibuya.perception import contact_view as CV
from shibuya.perception.facts import (
    BodyView, IntentView, Percept, SceneView, SeenObject, SeenPerson, SelfView, Sound, TimeView, WakeView,
)

from tests.engine.contact._c1 import STEP_NS


# ================================================================= 道具の状態と刺激(CT3・係数を掛けない段の形)
def _devices(n: int = 1) -> DV.Devices:
    return DV.Devices(n, 1)


@pytest.mark.parametrize("manner,place,ear,expect", [
    (False, DV.PLACE_HAND, False, DV.LEVEL_STRONG),     # 音が手元で鳴る
    (False, DV.PLACE_POCKET, False, DV.LEVEL_STRONG),
    (False, DV.PLACE_BAG, False, DV.LEVEL_WEAK),        # かばんの中=弱い(55 − 60 = −5 dB)
    (True, DV.PLACE_POCKET, False, DV.LEVEL_WEAK),      # マナーモード=振動だけ=弱い
    (True, DV.PLACE_BAG, False, DV.LEVEL_NONE),         # マナーモード+かばん=届かない
    (False, DV.PLACE_HAND, True, DV.LEVEL_WEAK),        # イヤホンの音が周りの音に足される(70 − 75.3 = −5.3 dB)
    (False, DV.PLACE_POCKET, True, DV.LEVEL_NONE),      # 64 − 75.3 = −11.3 dB
    (False, DV.PLACE_BAG, True, DV.LEVEL_NONE),
])
def test_manner_mode_and_bag_make_the_notice_weaker(manner, place, ear, expect):
    d = _devices()
    d._manner[0], d._place[0], d._ear[0] = manner, place, ear
    lvl, bits = d.stimulus([0], DV.noise_db_of_stage([1]), [False])  # 騒音の段 1(60 dB 帯)
    assert int(lvl[0]) == expect
    assert (int(bits[0]) & DV.CH_VIBRATION) == (DV.CH_VIBRATION if (manner and place != DV.PLACE_BAG) else 0)


def test_screen_is_strong_and_an_off_device_gets_nothing():
    d = _devices(2)
    d._manner[:] = True
    d._place[:] = DV.PLACE_BAG
    lvl, bits = d.stimulus([0, 1], DV.noise_db_of_stage([0, 0]), [True, False])
    assert lvl.tolist() == [DV.LEVEL_STRONG, DV.LEVEL_NONE] and int(bits[0]) == DV.CH_SCREEN
    d._on[0] = False
    lvl, bits = d.stimulus([0], DV.noise_db_of_stage([0]), [True])
    assert int(lvl[0]) == DV.LEVEL_NONE and int(bits[0]) == 0


def test_the_levels_are_a_shape_not_a_coefficient():
    """負の対照: 同じ状態からはいつも同じ段(確率を引かない)・段は SNR の閾値でだけ変わる。"""
    d = _devices()
    d._manner[0], d._place[0], d._ear[0] = False, DV.PLACE_BAG, False
    out = {int(d.stimulus([0], [nd], [False])[0][0]) for nd in (50.0, 55.0, 57.9, 58.1, 64.9, 65.1, 80.0)
           for _ in range(3)}
    assert out == {DV.LEVEL_STRONG, DV.LEVEL_WEAK, DV.LEVEL_NONE}
    assert int(d.stimulus([0], [57.9], [False])[0][0]) == DV.LEVEL_STRONG   # 55 − 57.9 = −2.9 ≥ −3
    assert int(d.stimulus([0], [58.1], [False])[0][0]) == DV.LEVEL_WEAK
    assert int(d.stimulus([0], [65.1], [False])[0][0]) == DV.LEVEL_NONE     # −10.1 < −10


def test_battery_drains_by_use_and_turns_the_device_off():
    d = _devices(3)
    use = np.array([DV.USE_STANDBY, DV.USE_SCREEN, DV.USE_CALL])
    for _ in range(60):
        d.drain(use, 60)
    b = d.battery()
    assert b[0] > b[2] > b[1] and abs(float(b[1]) - (1.0 - 0.12)) < 1e-4
    d._battery[1] = np.float32(0.0001)
    assert d.drain(use, 60) == 1 and not bool(d._on[1]) and float(d._battery[1]) == 0.0


def test_initial_device_state_comes_from_the_population_seed():
    a, b, c = DV.Devices(2000, 7), DV.Devices(2000, 7), DV.Devices(2000, 8)
    assert np.array_equal(a._manner, b._manner) and np.array_equal(a._home, b._home)
    assert not np.array_equal(a._manner, c._manner)
    assert 0.45 < float(a._manner.mean()) < 0.55 and 0.15 < float(a._ear.mean()) < 0.25


# ================================================================= 目と心の向き(周辺視の粗い気配・割り込みの門)
def _percept(*, reason: int = int(WakeCondition.INTEROCEPTION), salient: tuple[str, ...] = ("人が倒れている",),
             dists: tuple[float, ...] = (0.5, 1.5, 3.0, 8.0)) -> Percept:
    scene = SceneView(cell=3, in_area=True, objects=(SeenObject(1, "poi", name="店"),), signage_poi=-1,
                      crowd_stage=1, flow=0, sounds=(Sound("noise", 1),), salient=salient, near_items=(),
                      field_hash=7, with_signage=(SeenObject(1, "poi", name="店"),))
    people = tuple(SeenPerson(id=10 + i, direction=None, action=1, distance_m=d, acquainted=i == 0)
                   for i, d in enumerate(dists))
    return Percept(agent_id=0, step=5, t_ns=5 * STEP_NS, cell=3,
                   self_view=SelfView(kind=1, money=100, hands_full=False, activity=2),
                   seen_objects=scene.objects, seen_people=people, sounds=scene.sounds,
                   time_view=TimeView(tod_s=300, day_kind=None, band5=1, hour=0, minute=5, weather="晴",
                                      daylight="日中", heat="快適"),
                   body=BodyView(1, 1, 1, 0, 0, 0), wake=WakeView(reason=reason, inviter=None, result=0,
                                                                  result_known=False, last_action=None),
                   intent=None, memories=None, signage_shown=True, watched_n=0, scene=scene)


def test_peripheral_vision_coarsens_the_percept_by_shape():
    p = _percept()
    q = AT.coarsen(p, AT.GAZE_SCREEN, AT.FOCUS_SCREEN, unnoticed_arm="iii")
    assert q.seen_objects == () and q.signage_shown is False and q.seen_people == ()
    att = q.mind_dir
    assert isinstance(att, CV.AttentionView) and att.peripheral and att.gaze == "画面" and att.focus == "画面"
    # 形=周辺視の範囲の中の人の数だけ(2.0 m 以内の 2 人)。誰か・何をしているかは無い
    assert att.people_hint == sum(1 for d in (0.5, 1.5, 3.0, 8.0) if d <= AT.PERIPHERAL_RANGE_M) == 2
    # 同じ入力から同じ写し(確率を引かない)
    assert AT.coarsen(p, AT.GAZE_SCREEN, AT.FOCUS_SCREEN, unnoticed_arm="iii") == q
    # Percept の形(欄)は変えない=既存の欄に値を入れるだけ
    assert [f.name for f in dataclasses.fields(q)] == [f.name for f in dataclasses.fields(p)]


def test_negative_control_front_gaze_keeps_the_facts():
    p = _percept()
    q = AT.coarsen(p, AT.GAZE_FRONT, AT.FOCUS_SURROUND, unnoticed_arm="i")
    assert q.seen_people == p.seen_people and q.seen_objects == p.seen_objects and q.signage_shown
    assert q.scene == p.scene and not q.mind_dir.peripheral and q.mind_dir.unnoticed == ()


@pytest.mark.parametrize("arm,filtered,corner", [("i", True, False), ("ii", True, True), ("iii", False, False)])
def test_unnoticed_events_three_arms(arm, filtered, corner):
    p = _percept()
    q = AT.coarsen(p, AT.GAZE_FRONT, AT.FOCUS_CALL, unnoticed_arm=arm)
    att = q.mind_dir
    assert att.unnoticed == ("人が倒れている",) and att.scene_filtered is filtered
    assert (q.scene.salient == ()) is filtered
    lines = CV.contact_lines(att, None, lambda i: f"P-{i}")
    assert (CV.B6_UNNOTICED_LINE in lines) is corner


def test_an_interrupt_lets_the_event_through():
    p = _percept(reason=int(WakeCondition.CELL_BLOCK))
    q = AT.coarsen(p, AT.GAZE_FRONT, AT.FOCUS_TALK, unnoticed_arm="i")
    assert q.mind_dir.interrupted and q.mind_dir.unnoticed == () and q.scene.salient == p.scene.salient


def test_gate_salient_removes_only_focused_and_not_interrupted():
    @dataclasses.dataclass
    class Ev:
        noticed: np.ndarray

    focus = np.array([AT.FOCUS_SURROUND, AT.FOCUS_SCREEN, AT.FOCUS_CALL, AT.FOCUS_TALK, AT.FOCUS_SCREEN])
    inter = np.array([False, False, False, False, True])
    evs = [Ev(np.array([0, 1, 2, 3, 4])), Ev(np.array([], dtype=np.int64))]
    kept, blocked, reached, by = AT.gate_salient(evs, focus, inter)
    assert (blocked, reached) == (3, 5) and kept[0].tolist() == [0, 4] and kept[1].tolist() == []
    assert evs[0].noticed.tolist() == [0, 1, 2, 3, 4]  # 〔検収 M1〕顕著行為の過程のキャッシュは書き換えない
    assert by == {"周り": 0, "画面": 1, "通話": 1, "会話": 1}


def test_attention_sync_orders_call_screen_talk():
    at = AT.Attention(4)
    at.look_at_screen([1, 3], 0)
    at.sync(np.array([False, False, False, True]), np.array([True, True, False, True]))
    assert at.focus_all().tolist() == [AT.FOCUS_TALK, AT.FOCUS_SCREEN, AT.FOCUS_SURROUND, AT.FOCUS_CALL]
    assert at.gaze_all().tolist() == [AT.GAZE_PARTNER, AT.GAZE_SCREEN, AT.GAZE_FRONT, AT.GAZE_SCREEN]
    onset = at.idle_onset(np.array([0, 2, 7, 0]))
    assert onset.tolist() == []  # 最初の刻みは前の活動が無い=境目にしない
    assert at.idle_onset(np.array([2, 2, 0, 7])).tolist() == [0, 3]


# ================================================================= チャットの会話の状態(対面の会話と同じ器)
def test_chat_state_transitions_like_a_conversation():
    cb = ChatBook()
    k = pair_key(3, 1)
    s = cb.on_message(k, 1, [3], 10)
    assert s.state is ConvState.INVITED and s.participants == [1, 3] and s.speaker == 3
    cb.on_message(k, 1, [3], 11)
    assert s.state is ConvState.INVITED  # 同じ人が続けても招待のまま
    cb.on_message(k, 3, [1], 12)
    assert s.state is ConvState.PARTICIPATING and s.speaker == 1 and s.blocks == 3 and s.calls == {1: 2, 3: 1}
    assert cb.partners_of(1) == (3,) and cb.partners_of(3) == (1,)
    cb.step(12 + CHAT_SILENCE_STEPS)
    assert s.state is ConvState.PARTICIPATING
    cb.step(13 + CHAT_SILENCE_STEPS)
    assert s.state is ConvState.CLOSING and s.close_reason == "soft_silence"
    done = cb.step(14 + CHAT_SILENCE_STEPS)
    assert done == [s] and s.state is ConvState.TERMINAL and cb.session(k) is None
    s2 = cb.on_message(k, 3, [1], 40)
    assert s2.session_id == s.session_id + 1 and s2.state is ConvState.INVITED
    assert cb.chat_counts()["opened"] == 2 and cb.chat_counts()["closed:soft_silence"] == 1


def test_chat_safety_cap_closes_and_counts():
    cb = ChatBook()
    k = pair_key(0, 1)
    for i in range(CHAT_MAX_BLOCKS):
        s = cb.on_message(k, i % 2, [1 - i % 2], 0)
    assert s.state is ConvState.CLOSING and s.close_reason == "hard" and cb.chat_counts()["cap_hits"] == 1


# ================================================================= 既読(道具の性質)
def test_read_marks_reach_the_sender_and_prune_is_bounded():
    mb = Mailbox()
    got, held = mb.deliver(mb.new_message_id(), 0, [1, 2], -1, 0, 100, 5, "こんにちは", lambda a: a != 2)
    assert got == [1] and held == [2] and mb.unread_count(1) == 1 and mb.mail_counts()["held"] == 1
    assert mb.take_unseen() == [(1, 1, 100)] and mb.take_unseen() == []
    rows = mb.read_all(1, 200)
    assert len(rows) == 1 and rows[0][6] == 200 and mb.unread_count(1) == 0
    assert mb._sent[0][4] == 1  # 既読の数(送った側の道具の印)
    assert mb.prune(200 + 10, 5) == 1 and mb.mail_counts()["inbox_rows"] == 0


# ================================================================= 宛先(1-7 の器)と体の無い人
def test_contacts_from_groups_family_only_and_groups_of():
    g = GroupList(household_id=np.array([0, 0, 1, -1]), org_id=np.array([5, 5, 5, -1]))
    bk = ContactBook(4, groups=g)
    assert bk.source() == "groups.family"
    assert bk.personal(None, 0, CT.MESSAGE, 0) == (1,) and bk.personal(None, 0, CT.WORK, 0) == ()
    assert bk.personal(None, 2, CT.MESSAGE, 0) == () and bk.personal(None, 3, CT.CALL, 0) == ()
    assert bk.groups_of(0) == (0, 2) and bk.group_kind(2) == "職場" and bk.members(2) == (0, 1, 2)


def test_contacts_from_relation_flags_and_bodiless_are_dropped():
    class Rel:
        contact_flags = np.array([[CT.CALL | CT.MESSAGE, CT.MESSAGE, CT.CALL, 0]], dtype=np.uint8)

        def _partner_rows(self, agents, ids):
            return np.array([[1, 7, 99, -1]])  # 99=体の無い人(ランの体の外)

    bk = ContactBook(8, rel_layer=Rel())
    assert bk.personal(None, 0, CT.MESSAGE, 0) == (1, 7)
    assert bk.personal(None, 0, CT.CALL, 0) == (1,)  # 体の無い人 99 は入れない(宣言 CT4)
    assert bk.bodiless_dropped == 1


# ================================================================= 判断の口(J0 の形)・長さの上限
def _ctx(agent: int = 3, step: int = 4, code: int = 17) -> DecisionContext:
    return DecisionContext(agent_id=agent, step=step, t_ns=step * STEP_NS, wake_class=-1, condition=-1, cell=0,
                           call_id=P.call_id_of(step, agent, code))


def test_contact_port_is_keyed_and_shuffle_invariant():
    port = P.ContactPort(seed=1, day_key0=0, step_seconds=60)
    cands = [P.cand(P.K_READ_NOW), P.cand(P.K_LATER), P.cand(P.K_IGNORE)]
    a = port.choose(_ctx(), cands)
    for perm in itertools.permutations(cands):
        assert port.choose(_ctx(), list(perm)).candidate_id == a.candidate_id
    picks = {port.choose(_ctx(code=P.serial_of(P.P_NOTICE, k)), cands).candidate_id for k in range(1, 40)}
    assert picks == {P.K_READ_NOW, P.K_LATER, P.K_IGNORE}  # 鍵が違えば違う答えもある(一様の仮のモデル)
    # 〔検収 M3 ④・L5〕テープの形(3 つ目は負=主の判断の起床の級と分ける)・主の判断の形は連絡の呼びでない
    assert P.call_id_of(4, 3, 17) == "4:3:-17" and P.parse_call_id("4:3:-17") == (4, 3, 17)
    assert P.step_of_call_id(P.call_id_of(4, 3, 17)) == 4 and P.step_of_call_id("4:3:1") is None
    assert P.step_of_call_id("c1:4:3:17") is None


def test_decision_serials_do_not_collide_and_have_a_limit():
    """〔検収 L5〕通し番号=k × 16+種類=257 回を超えてもぶつからない・上限で止まる・表は書き換えられない。"""
    got = {P.serial_of(p, k) for p in P.PURPOSES for k in range(1, 400)}
    assert len(got) == len(P.PURPOSES) * 399
    assert all(P.purpose_of_serial(P.serial_of(p, 300)) == p for p in P.PURPOSES)
    with pytest.raises(ValueError):
        P.serial_of(P.P_NOTICE, P.MAX_DECISIONS_PER_STEP)
    with pytest.raises(TypeError):
        P.PURPOSES[99] = "x"  # type: ignore[index]
    with pytest.raises(TypeError):
        P._SOURCE_OF["x"] = "y"  # type: ignore[index]


def test_length_cap_is_only_a_safety_device():
    t, capped = P.cap_text("あ" * (P.MESSAGE_MAX_CHARS + 5))
    assert capped and len(t) == P.MESSAGE_MAX_CHARS
    assert P.cap_text("こんにちは") == ("こんにちは", False)
    assert P.habit_answer(0, "notice") is None  # 習慣は本段では作らない=判断の口に戻す


# ================================================================= 負の対照の監査(エンジンは時刻も回数も決めない)
def test_audit_catches_engine_decided_reads_and_sends():
    c = LlmCall(P.call_id_of(3, 1, P.serial_of(P.P_NOTICE, 1)), (), source="affordance", number=1)
    c2 = LlmCall(P.call_id_of(3, 1, P.serial_of(P.P_WHOM, 2)), (), source="experience", number=1)
    ok = [Event(t_ns=3 * STEP_NS, who=1, what=W_READ, whom=0, via="メッセージ", received_ns=3 * STEP_NS,
                read_ns=3 * STEP_NS, cause=c),
          Event(t_ns=4 * STEP_NS, who=1, what=W_SENT, whom=0, via="メッセージ", cause=c2),
          Event(t_ns=4 * STEP_NS, who=0, what=W_DELIVERED, whom=1, via="メッセージ", received_ns=4 * STEP_NS,
                cause=Process("contact"))]
    assert audit_causes(ok, step_ns=STEP_NS)["violations"] == 0
    bad = [Event(t_ns=3 * STEP_NS, who=1, what=W_READ, whom=0, via="メッセージ", received_ns=3 * STEP_NS,
                 read_ns=3 * STEP_NS, cause=Process("contact")),                        # エンジンが読んだ
           Event(t_ns=9 * STEP_NS, who=1, what=W_SENT, whom=0, via="メッセージ", cause=c2),  # 判断の刻みと離れた送信
           Event(t_ns=4 * STEP_NS, who=0, what=W_DELIVERED, whom=1, via="メッセージ", received_ns=4 * STEP_NS,
                 cause=c)]                                                             # 届くのが本人の判断
    assert audit_causes(bad, step_ns=STEP_NS)["violations"] == 3
    assert PERSON_WORDS.isdisjoint(ENGINE_WORDS)
    # 〔検収 M2〕発行した呼びとの突き合わせ: 控えにある呼びだけを認める・体と判断の種類も合わせる
    iss = [LY.issued_key(3, 1, P.serial_of(P.P_NOTICE, 1)), LY.issued_key(3, 1, P.serial_of(P.P_WHOM, 2))]
    assert audit_causes(ok, step_ns=STEP_NS, issued=iss)["violations"] == 0
    forged = LlmCall(P.call_id_of(3, 1, P.serial_of(P.P_NOTICE, 9)), (), source="affordance", number=1)
    planted = [Event(t_ns=3 * STEP_NS, who=1, what=W_READ, whom=0, via="メッセージ", received_ns=3 * STEP_NS,
                     read_ns=3 * STEP_NS, cause=forged),                       # 偽の呼び(控えに無い)
               Event(t_ns=3 * STEP_NS, who=2, what=W_READ, whom=0, via="メッセージ", received_ns=3 * STEP_NS,
                     read_ns=3 * STEP_NS, cause=c),                            # ほかの体の呼び
               Event(t_ns=3 * STEP_NS, who=1, what=W_LATER, whom=0, via="メッセージ", cause=c2)]  # 種類が語に合わない
    got = audit_causes(planted, step_ns=STEP_NS, issued=iss)
    assert got["violations"] == 3, got
    assert audit_causes(planted[:1], step_ns=STEP_NS)["violations"] == 0  # 控えを渡さないと偽の呼びは見えない(対照)


# ================================================================= 腕の切替
def test_arms_and_config():
    prev = (A.arm(), A.unnoticed(), A.send())
    try:
        A.set_arm("off")
        assert A.config() is None and not A.is_on()
        A.set_arm("c1")
        A.set_unnoticed("ii")
        A.set_send("c")
        assert A.config() == {"arm": "c1", "unnoticed": "ii", "send": "c"}
        for bad in (lambda: A.set_arm("c2"), lambda: A.set_unnoticed("iv"), lambda: A.set_send("a")):
            with pytest.raises(ValueError):
                bad()
    finally:
        A.set_arm(prev[0])
        A.set_unnoticed(prev[1])
        A.set_send(prev[2])


def test_people_hint_words_are_coarse():
    assert [CV.people_hint_word(n) for n in (0, 1, 2, 4, 5, 30)] == ["なし", "1 人", "数人", "数人", "多くの人", "多くの人"]
