"""C6 会話招待の設計準拠(09-09): 「対象」欄で名指し → 被招待が**自分の呼**で答える。

正典
- 行動契約書 §1-2: 2 行形の「対象: <セルID|物カテゴリ|**個体ID**>」=対象スロット。
  会話=1 呼 1 発話ブロック・終了はエンジン。
- 知覚契約書 §6: 起床(ii) に**被招待**・相手別不応期(同一相手 60 分 / 同一話者 30 分)。
- C4 の会話状態機械: 招待側 CONVERSING・被招待側は起床 → 応答で成立・``revert_conversation``。

C3 の ``pair_partners``「同じ適用バッチの同セル最小 id」は expedient で、LLM の対象欄を
**無視していた**。本テストはその差を埋めた実装を固定する。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import Activity, AgentState, WakeCondition
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.conversation import (
    PAIR_INVITE_REFRACTORY_TICKS,
    PENDING_INVITE_TTL_TICKS,
    SPEAKER_INVITE_REFRACTORY_TICKS,
    ConversationManager,
)
from shibuya.engine.run import run_day
from shibuya.llm import LLMResponse
from shibuya.world.state import World

TALK_TO = "理由: 知人を見かけたから\n行動: 会話 対象: P-{}　ひと言: こんにちは"
WAIT = "理由: 様子を見るから\n行動: 待機 対象: なし ひと言: なし"


# ------------------------------------------------------------------ 相手の決め方(純関数)


def test_named_person_in_the_same_cell_wins_over_the_batch_fallback():
    a = np.array([0, 1, 2], dtype=np.int64)
    cell = np.array([5, 5, 5], dtype=np.int64)
    all_cells = np.array([5, 5, 5, 5], dtype=np.int64)
    named = np.array([2, -1, 0], dtype=np.int64)
    partner, source = C.talk_partners(a, cell, named, all_cells, 4)
    assert partner[0] == 2 and source[0] == 0  # 名指しが通る
    assert source[1] == 1  # 名指しなし → フォールバック
    assert partner[2] == 0 and source[2] == 0


def test_named_person_in_another_cell_falls_back_and_is_counted():
    a = np.array([0, 1], dtype=np.int64)
    cell = np.array([5, 5], dtype=np.int64)
    all_cells = np.array([5, 5, 9], dtype=np.int64)  # 個体2 は別セル
    named = np.array([2, 2], dtype=np.int64)
    partner, source = C.talk_partners(a, cell, named, all_cells, 3)
    assert list(source) == [1, 1]  # 両方フォールバック
    assert partner[0] == 1 and partner[1] == 0  # 同バッチ最小 id 規則


def test_naming_yourself_or_out_of_range_falls_back():
    a = np.array([0, 1], dtype=np.int64)
    cell = np.array([5, 5], dtype=np.int64)
    all_cells = np.array([5, 5], dtype=np.int64)
    named = np.array([0, 99], dtype=np.int64)  # 自分自身 / 範囲外
    partner, source = C.talk_partners(a, cell, named, all_cells, 2)
    assert list(source) == [1, 1]


def test_alone_in_the_cell_yields_no_partner_and_source_absent():
    a = np.array([7], dtype=np.int64)
    cell = np.array([3], dtype=np.int64)
    all_cells = np.array([3] * 8, dtype=np.int64)
    partner, source = C.talk_partners(a, cell, np.array([-1]), all_cells, 8)
    assert partner[0] == -1 and source[0] == 2


def test_intents_from_responses_fills_the_stats(monkeypatch):
    w = World.synthetic(n_cells=1, seed=1)
    ag = AgentState(6)
    from shibuya.agents.schedule import synthesize

    R.initialize(ag, w, synthesize(6, 1, w.n_cells), day_index=0, ledger=None)
    space = C.ResourceSpace(w.n_poi, 6, w.n_cells)
    stats: dict[str, int] = {}
    ib = C.intents_from_responses(
        ag, w, space, 1,
        np.array([0, 1], dtype=np.int64), np.zeros(2, dtype=np.int64),
        np.array([C.ACT_TALK, C.ACT_TALK], dtype=np.int64),
        target_person=np.array([3, -1], dtype=np.int64), stats=stats,
    )
    assert stats["talk_named"] == 1 and stats["talk_fallback"] == 1
    assert int(ib.target_id[0]) == 3  # 名指しがそのまま対象になる


# ------------------------------------------------------------------ 返事待ちの招待


def make_manager() -> ConversationManager:
    return ConversationManager(master_seed=1)


def test_pending_invite_is_accepted_when_the_invitee_answers_talk():
    m = make_manager()
    assert m.register_pending(1, 2, tick=10, cell=4, same_cell=True)
    assert 2 in m.pending_invites and m.pending_inviter_of(2) == 1
    # 招待が出た tick は相手を起こさない(まだ答えられない)
    assert 2 not in list(m.wake_candidates(10)[0])
    ids, cond, cls = m.wake_candidates(11)
    assert 2 in list(ids)
    assert int(cond[list(ids).index(2)]) == int(WakeCondition.CONVERSATION_TURN)
    s = m.resolve_pending(2, tick=11, accepted=True)
    assert s is not None and sorted(s.participants) == [1, 2]
    assert m.counters()["conv_invites"] == 1 and m.counters()["conv_accepted"] == 1
    assert m.counters()["conv_pending_open"] == 0


def test_pending_invite_is_declined_when_the_invitee_answers_something_else():
    m = make_manager()
    m.register_pending(1, 2, tick=10, cell=4, same_cell=True)
    assert m.resolve_pending(2, tick=11, accepted=False) is None
    assert m.counters()["conv_declined"] == 1 and m.counters()["conv_accepted"] == 0
    assert m.refused_recently(1, 2, 11)  # 断られた記憶が残る


def test_pair_and_speaker_refractory_block_repeat_invites():
    m = make_manager()
    assert m.register_pending(1, 2, tick=10, cell=4, same_cell=True)
    m.resolve_pending(2, tick=11, accepted=False)
    # 同一話者 30 分
    assert m.invite_blocked_by_refractory(1, 3, 11) == "speaker_refractory"
    assert not m.register_pending(1, 3, tick=11, cell=4, same_cell=True)
    assert m.invite_blocked_by_refractory(1, 3, 10 + SPEAKER_INVITE_REFRACTORY_TICKS) == ""
    # 同一相手 60 分(話者不応期が明けても対は残る)
    t = 10 + SPEAKER_INVITE_REFRACTORY_TICKS
    assert m.invite_blocked_by_refractory(1, 2, t) == "pair_refractory"
    assert m.invite_blocked_by_refractory(1, 2, 10 + PAIR_INVITE_REFRACTORY_TICKS) == ""
    assert m.counters()["conv_invite_refractory_blocked"] == 1


def test_pending_invite_expires_and_returns_the_inviter():
    m = make_manager()
    m.register_pending(1, 2, tick=10, cell=4, same_cell=True)
    assert m.expire_pending(10 + PENDING_INVITE_TTL_TICKS) == []
    assert m.expire_pending(11 + PENDING_INVITE_TTL_TICKS) == [1]
    assert m.counters()["conv_pending_expired"] == 1
    assert m.counters()["ignored_invites"] == 1  # 「無視された」= 呼を消費しない


def test_register_pending_rejects_other_cell_self_and_busy():
    m = make_manager()
    assert not m.register_pending(1, 1, tick=0, cell=0, same_cell=True)  # 自分自身
    assert not m.register_pending(1, 2, tick=0, cell=0, same_cell=False)  # 別セル
    m.register_pending(3, 4, tick=0, cell=0, same_cell=True)
    m.resolve_pending(4, tick=1, accepted=True)
    assert not m.register_pending(5, 4, tick=1, cell=0, same_cell=True)  # 会話中


# ------------------------------------------------------------------ resolve(両側 CONVERSING)


def test_set_conversing_marks_both_sides():
    w = World.synthetic(n_cells=1, seed=1)
    ag = AgentState(4)
    from shibuya.agents.schedule import synthesize

    R.initialize(ag, w, synthesize(4, 1, w.n_cells), day_index=0, ledger=None)
    R.set_conversing(ag, np.array([0]), np.array([1]))
    r = ag.registry
    assert int(r.activity[0]) == int(Activity.CONVERSING)
    assert int(r.activity[1]) == int(Activity.CONVERSING)  # **被招待側も**(C4 の穴を閉じた)
    assert int(r.talk_partner[0]) == 1 and int(r.talk_partner[1]) == 0


# ------------------------------------------------------------------ 通しの結線


class NamingLLM:
    """個体 a が「会話 対象: P-(a^1)」と答える台本(**対を組む**)。

    ``a ^ 1`` は (0,1) (2,3) … の対なので、**招待された側の返事が招待者を名指す**
    (承諾の対象規則=中-2 を満たす)。第三者を名指す台本は
    ``NamingLLM(third_party=True)``(=承諾されないことの対照)。
    セルは 2 つなので名指しの一部は別セル= ``talk_partners`` のフォールバックへ落ちる。
    """

    def __init__(self, n: int, decline_even: bool = False, third_party: bool = False) -> None:
        self.n = int(n)
        self.decline_even = decline_even
        self.third_party = third_party

    def partner_of(self, a: int) -> int:
        return (a + 1) % self.n if self.third_party else (a ^ 1) % self.n

    def complete(self, request):
        a = int(request.agent_id)
        if self.decline_even and a % 2 == 0:
            return LLMResponse(text=WAIT, source="scripted")
        return LLMResponse(text=TALK_TO.format(self.partner_of(a)), source="scripted")


#: tick 0 は真夜中で全員 SLEEPING。朝(≈tick 420)を含む長さまで回さないと
#: ``_apply_talk`` の「相手 idle」が満たされず 1 件も成立しない(C6 の切り分けで判明)。
NAMED_TICKS = 600
NAMED_CELLS = 2


def run_named(n_agents: int = 200, ticks: int = NAMED_TICKS, **kw):
    return run_day(
        n_agents=n_agents, seed=1, world=World.synthetic(n_cells=NAMED_CELLS, seed=1),
        ticks=ticks, renderer="stub", processes=False, population=False, world_dir=None, **kw
    )


@pytest.mark.slow
def test_named_target_drives_invites_end_to_end():
    """A が「会話 対象: P-B」→ B が次 tick に被招待で起床 → B の返事で成否が決まる。

    ``NamingLLM`` は ``a ^ 1`` の対を名指すので、**名指しから出た招待**の返事は招待者を
    名指す(承諾)。一方 ``talk_partners`` のフォールバック(同セル・撹拌順の先頭)から出た
    招待の返事は**第三者名指し**になり拒否される。合成世界ではフォールバック由来が多数を
    占めるため承諾は少ない=**承諾の意味論そのものは単体テスト**
    (``test_acceptance_is_consumed_before_phase_c_so_no_false_partner_busy`` ほか)で固定する。
    """
    res = run_named(llm=NamingLLM(200))
    c = res.conversation_counters
    assert c["conv_target_named"] > 0, c  # 対象スロットが実際に使われた
    assert c["conv_invites"] > 0
    assert c["sessions_opened"] == c["conv_accepted"]
    # 帳尻: 出た招待は 成立 / 断り / 期限切れ / 未決 のどれかで必ず説明できる
    assert (
        c["conv_accepted"] + c["conv_declined"] + c["conv_pending_expired"]
        + c["conv_pending_open"] == c["conv_invites"]
    ), c
    assert res.conserved
    assert c["conv_fallback_same_batch"] > 0  # 別セルの名指しはフォールバックへ
    # 成立したセッションは**両側**が CONVERSING。片側だけ CONVERSING でいてよいのは
    # 「返事待ちで待っている招待側」だけ(``conv_pending_open`` 件)。
    act = res.agents.registry.activity
    partner = res.agents.registry.talk_partner
    asymmetric = [
        int(a)
        for a in np.flatnonzero(act == int(Activity.CONVERSING)).tolist()
        if int(partner[a]) < 0 or int(act[int(partner[a])]) != int(Activity.CONVERSING)
    ]
    assert len(asymmetric) <= c["conv_pending_open"], (asymmetric, c["conv_pending_open"])


@pytest.mark.slow
def test_declining_invitees_do_not_open_sessions_and_the_inviter_is_reverted():
    """B が 待機 と答えたら不成立=招待側は CONVERSING に取り残されない。"""
    res = run_named(llm=NamingLLM(200, decline_even=True))
    c = res.conversation_counters
    assert c["conv_invites"] > 0
    assert c["conv_declined"] > 0  # 偶数 id(=被招待)は 待機 と答える → 不成立
    assert c["conv_accepted"] < c["conv_invites"]
    assert c["sessions_opened"] == c["conv_accepted"]
    assert (
        c["conv_accepted"] + c["conv_declined"] + c["conv_pending_expired"]
        + c["conv_pending_open"] == c["conv_invites"]
    ), c
    act = res.agents.registry.activity
    partner = res.agents.registry.talk_partner
    asymmetric = [
        int(a)
        for a in np.flatnonzero(act == int(Activity.CONVERSING)).tolist()
        if int(partner[a]) < 0 or int(act[int(partner[a])]) != int(Activity.CONVERSING)
    ]
    assert len(asymmetric) <= c["conv_pending_open"]  # 断られた招待側は取り残されない


def test_mock_llm_never_names_a_partner_so_the_fallback_path_is_unchanged():
    """MockLLM は「対象: なし」しか書かない=名指し 0・フォールバックのみ(T2 の由来)。"""
    res = run_day(  # ticks: D-56 以降は最初の計画境界(tick 300-480)を跨ぐ窓が要る
        n_agents=400, seed=1, world=World.synthetic(n_cells=4, seed=1), ticks=540,
        renderer="stub", processes=False, population=False, world_dir=None,
    )
    c = res.conversation_counters
    assert c["conv_target_named"] == 0
    assert c["conv_fallback_same_batch"] + c["conv_target_absent"] > 0


# ------------------------------------------------------------------ 承諾の消費(層2 中-1/中-2)


def _world_agents(n: int = 8, n_cells: int = 1):
    from shibuya.agents.schedule import synthesize

    w = World.synthetic(n_cells=n_cells, seed=1)
    ag = AgentState(n)
    R.initialize(ag, w, synthesize(n, 1, w.n_cells), day_index=0, ledger=None)
    return w, ag


def _settle(conv, ag, tick, rows):
    """``run._settle_pending_invites`` を (agent, code, named) の行で呼ぶ。"""
    from shibuya.engine.run import _settle_pending_invites

    ids = np.array([r[0] for r in rows], dtype=np.int64)
    codes = np.array([r[1] for r in rows], dtype=np.int64)
    named = np.array([r[2] for r in rows], dtype=np.int64)
    return _settle_pending_invites(conv, ag, tick, ids, codes, named, R, np)


def _invite(conv, ag, a: int, b: int, tick: int):
    """A が B を招待して返事待ちにする(A は招待側として CONVERSING で待つ)。"""
    R.set_conversing(ag, np.array([a]), np.array([b]))
    R.revert_conversation(ag, np.array([b]))  # 被招待側はまだ IDLE(招待側だけ待つ)
    assert conv.register_pending(a, b, tick=tick, cell=int(ag.registry.cell[a]), same_cell=True)


def test_acceptance_is_consumed_before_phase_c_so_no_false_partner_busy():
    """層2 中-1: 承諾「会話 対象: P-A」は Phase C へ流さない=B に偽の失敗が載らない。"""
    _, ag = _world_agents()
    conv = make_manager()
    _invite(conv, ag, 1, 2, tick=10)
    before = int(ag.registry.last_result[2])
    consumed = _settle(conv, ag, 11, [(2, C.ACT_TALK, 1)])
    assert consumed == {2}  # B の行は intent から外れる(=``_apply_talk`` を通らない)
    assert conv.counters()["conv_accepted"] == 1
    assert int(ag.registry.activity[1]) == int(Activity.CONVERSING)
    assert int(ag.registry.activity[2]) == int(Activity.CONVERSING)
    # B の「直前の結果」(B6 の主語)に PARTNER_BUSY が載っていない
    assert int(ag.registry.last_result[2]) == before
    assert int(ag.registry.fail_streak[2]) == 0


def test_acceptance_without_a_target_is_also_accepted():
    _, ag = _world_agents()
    conv = make_manager()
    _invite(conv, ag, 1, 2, tick=10)
    assert _settle(conv, ag, 11, [(2, C.ACT_TALK, -1)]) == {2}  # 対象なしも承諾
    assert conv.counters()["conv_accepted"] == 1


def test_naming_a_third_party_is_a_refusal_and_stays_an_intent():
    """層2 中-2: 第三者 C を名指した 会話 は A への**拒否**(承諾ではない)。"""
    _, ag = _world_agents()
    conv = make_manager()
    _invite(conv, ag, 1, 2, tick=10)
    consumed = _settle(conv, ag, 11, [(2, C.ACT_TALK, 5)])  # B は C=5 を名指す
    assert consumed == set()  # **消費しない**= B の 会話 は C への新規招待として通る
    assert conv.counters()["conv_declined"] == 1 and conv.counters()["conv_accepted"] == 0
    assert int(ag.registry.activity[1]) == int(Activity.IDLE)  # 招待側 A は戻る


def test_answering_another_action_is_a_refusal():
    _, ag = _world_agents()
    conv = make_manager()
    _invite(conv, ag, 1, 2, tick=10)
    assert _settle(conv, ag, 11, [(2, C.ACT_WAIT, -1)]) == set()
    assert conv.counters()["conv_declined"] == 1
    assert int(ag.registry.activity[1]) == int(Activity.IDLE)


def test_acceptance_from_another_cell_is_a_refusal():
    _, ag = _world_agents(n_cells=4)
    conv = make_manager()
    _invite(conv, ag, 1, 2, tick=10)
    with ag.writable():
        ag.registry.cell[2] = int(ag.registry.cell[1]) + 1  # B が別セルへ移った
    assert _settle(conv, ag, 11, [(2, C.ACT_TALK, 1)]) == set()
    assert conv.counters()["conv_declined"] == 1


def test_settle_is_a_no_op_without_pending_invites():
    _, ag = _world_agents()
    conv = make_manager()
    assert _settle(conv, ag, 5, [(2, C.ACT_TALK, 1)]) == set()
    assert conv.counters()["conv_accepted"] == 0 and conv.counters()["conv_declined"] == 0


def test_intents_from_responses_uses_the_run_salt_for_the_fallback_order():
    """軽-4: フォールバックのセル内順序が **blake3 撹拌**で、塩を変えると並びが変わる。"""
    w, ag = _world_agents(n=6)
    space = C.ResourceSpace(w.n_poi, 6, w.n_cells)
    a = np.arange(6, dtype=np.int64)
    codes = np.full(6, C.ACT_TALK, dtype=np.int64)
    cond = np.zeros(6, dtype=np.int64)
    kw = dict(home_cell=None, work_cell=None, target_person=None)
    plain = C.intents_from_responses(ag, w, space, 7, a, cond, codes, **kw)
    salted = C.intents_from_responses(ag, w, space, 7, a, cond, codes, run_salt=b"s1", **kw)
    other = C.intents_from_responses(ag, w, space, 7, a, cond, codes, run_salt=b"s2", **kw)
    # 塩なし = ID 順(最小 id が相手)。塩ありは撹拌後の並び。
    assert int(plain.target_id[1]) == 0
    assert list(salted.target_id) != list(plain.target_id) or list(other.target_id) != list(
        plain.target_id
    )
    assert list(salted.target_id) == list(
        C.intents_from_responses(ag, w, space, 7, a, cond, codes, run_salt=b"s1", **kw).target_id
    )  # 決定論
