"""engine.conversation のテスト(行動契約書 §3 会話プロトコル)。

開始ゲート5条件/応答判定0.8の決定論/話者交替(招待者始まり)/ハード終了 max_turns 3(+2)/
ソフト終了(話題スタック空・沈黙・退去・セル離脱)/1人1会話/拒否履歴/
会話ターン起床(不応期0)/診断計数。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import REFRACTORY_MINUTES, WakeCondition
from shibuya.core.rng import stream
from shibuya.core.types import EventClass
from shibuya.engine.conversation import (
    ACCEPT_PROBABILITY,
    BACKCHANNELS,
    CLOSING_UTTERANCE,
    D_TALK_METERS,
    MAX_TURNS,
    ConversationManager,
    ConvState,
)

SEED = 20260908


def _manager(**kw) -> ConversationManager:
    kw.setdefault("accept_probability", 1.0)  # ゲートと進行の検査では応答判定を固定
    return ConversationManager(SEED, **kw)


def _open(m: ConversationManager, a=1, b=2, tick=0, cell=5):
    return m.invite(a, b, tick, cell, same_cell=True, partner_idle=True)


# ---------------------------------------------------------------- 開始ゲート
def test_gate_passes_when_all_five_conditions_hold():
    m = _manager()
    g = m.gate(1, 2, 0, same_cell=True, partner_idle=True)
    assert g.ok and g.reason == ""


@pytest.mark.parametrize(
    "kwargs,reason",
    [
        (dict(same_cell=False, partner_idle=True), "not_same_cell"),
        (dict(same_cell=True, partner_idle=False), "partner_busy"),
        (dict(same_cell=True, partner_idle=True, inviter_has_budget=False), "no_call_budget"),
        (dict(same_cell=True, partner_idle=True, partner_has_budget=False), "no_call_budget"),
    ],
)
def test_gate_rejects_each_missing_condition(kwargs, reason):
    m = _manager()
    g = m.gate(1, 2, 0, **kwargs)
    assert not g.ok and g.reason == reason


def test_gate_rejects_self_invitation():
    assert not _manager().gate(1, 1, 0, same_cell=True, partner_idle=True).ok


def test_d_talk_is_declared_even_though_the_proxy_is_same_cell():
    """C3 は「距離≦d_talk」を同一セルで代理する(定数は宣言だけ残す)。"""
    assert D_TALK_METERS == pytest.approx(1.0)


def test_one_conversation_per_agent():
    m = _manager()
    assert _open(m, 1, 2) is not None
    assert m.is_busy(1) and m.is_busy(2)
    assert not m.gate(1, 3, 0, same_cell=True, partner_idle=True).ok
    assert not m.gate(3, 2, 0, same_cell=True, partner_idle=True).ok
    assert _open(m, 3, 4) is not None  # 別の対は開ける


def test_refusal_memory_blocks_the_pair_for_a_while():
    m = _manager(refusal_memory_ticks=30)
    m.record_refusal(1, 2, tick=10)
    assert m.refused_recently(1, 2, 20) and m.refused_recently(2, 1, 20)
    assert not m.gate(1, 2, 20, same_cell=True, partner_idle=True).ok
    assert not m.refused_recently(1, 2, 40)
    assert m.gate(1, 2, 40, same_cell=True, partner_idle=True).ok


# ---------------------------------------------------------------- 応答判定
def test_accept_is_deterministic_for_the_same_key():
    a = ConversationManager(SEED)
    b = ConversationManager(SEED)
    for tick in range(20):
        assert (a._accepts(7, tick)) == (b._accepts(7, tick))


def test_accept_uses_the_declared_rng_stream():
    m = ConversationManager(SEED)
    # 運用設計書 §2.5: カウンタ=(tick, entity_id, …) → (tick=3, inviter=7)
    expected = bool(stream(SEED, "conversation.invite", 3, 7).random() < ACCEPT_PROBABILITY)
    assert m._accepts(7, 3) is expected


def test_accept_rate_is_about_zero_point_eight():
    m = ConversationManager(SEED)
    hits = sum(m._accepts(a, t) for a in range(200) for t in range(10))
    assert 0.75 <= hits / 2_000 <= 0.85


def test_non_response_is_an_ignored_event_and_costs_no_call():
    m = ConversationManager(SEED, accept_probability=0.0)
    assert m.invite(1, 2, 0, 5, same_cell=True, partner_idle=True) is None
    assert m.n_ignored_invites == 1 and m.ignored_events == [(0, 1, 2)]
    assert m.counters()["utterance_blocks"] == 0
    assert not m.is_busy(1) and not m.is_busy(2)


# ---------------------------------------------------------------- 進行
def test_session_starts_participating_with_the_inviter_as_first_speaker():
    m = _manager()
    s = _open(m, 1, 2)
    assert s.state is ConvState.PARTICIPATING
    assert s.inviter == 1 and s.speaker == 1


def test_walking_over_state_can_be_enabled():
    m = _manager(walk_over_ticks=2)
    s = _open(m, 1, 2, tick=0)
    assert s.state is ConvState.WALKING_OVER
    m.step(1)
    assert s.state is ConvState.WALKING_OVER
    m.step(2)
    assert s.state is ConvState.PARTICIPATING


def test_speakers_alternate_starting_with_the_inviter():
    m = _manager()
    s = _open(m, 1, 2)
    order = []
    for tick in range(1, 5):
        order.append(s.speaker)
        m.utterance(s.speaker, tick, action="会話", comment="やあ")
    assert order == [1, 2, 1, 2]


def test_wake_candidates_are_conversation_turns_with_zero_refractory():
    m = _manager()
    s = _open(m, 1, 2, tick=0)
    agents, conditions, classes = m.wake_candidates(1)
    assert agents.tolist() == [1]
    assert conditions.tolist() == [int(WakeCondition.CONVERSATION_TURN)]
    assert classes.tolist() == [int(EventClass.CONVERSATION)]
    assert REFRACTORY_MINUTES[int(WakeCondition.CONVERSATION_TURN)] == 0
    # 同じ tick に2度は起こさない
    m.utterance(1, 1, action="会話", comment="やあ")
    assert m.wake_candidates(1)[0].size == 0
    assert m.wake_candidates(2)[0].tolist() == [2]


def test_backchannels_are_engine_generated_and_deterministic():
    m = _manager()
    s = _open(m, 1, 2)
    text = m.backchannel_for(s, 2)
    assert text in BACKCHANNELS
    assert m.counters()["backchannels"] == 1


def test_interrupt_is_discretised_to_the_next_transition_point():
    m = _manager(max_participants=3)
    s = _open(m, 1, 2)
    m.join(s, 3, tick=0)
    assert s.participants == [1, 2, 3]
    m.request_interrupt(s.session_id, 3)
    m.utterance(1, 1, action="会話", comment="やあ")  # 移行点で 3 が奪う
    assert s.speaker == 3
    assert m.counters()["interrupts"] == 1


def test_join_respects_the_participant_cap():
    m = _manager()  # 既定 2 者
    s = _open(m, 1, 2)
    assert m.join(s, 3, tick=0) is False


# ---------------------------------------------------------------- 終了
def test_hard_stop_at_max_turns_three_calls_per_agent():
    m = _manager()
    s = _open(m, 1, 2)
    for tick in range(1, 1 + 2 * MAX_TURNS):
        m.utterance(s.speaker, tick, action="会話", comment="…")
    assert s.calls == {1: MAX_TURNS, 2: MAX_TURNS}
    assert s.state is ConvState.CLOSING and s.close_reason == "hard"
    m.step(99)
    assert s.state is ConvState.TERMINAL and not m.is_busy(1) and not m.is_busy(2)
    assert m.counters()["closed_hard"] == 1


def test_important_agents_get_two_extra_calls():
    m = _manager(important=[1], topics_per_session=50)
    s = _open(m, 1, 2)
    assert s.max_turns_of == {1: MAX_TURNS + 2, 2: MAX_TURNS}
    for tick in range(1, 40):
        if s.state is not ConvState.PARTICIPATING:
            break
        m.utterance(s.speaker, tick, action="会話", comment="…")
    assert s.calls[1] == MAX_TURNS + 2 and s.calls[2] == MAX_TURNS


def test_soft_stop_when_the_topic_stack_is_empty():
    m = _manager(topics_per_session=1, max_turns=10)
    s = _open(m, 1, 2)
    m.utterance(1, 1, action="会話", comment="…")
    m.utterance(2, 2, action="会話", comment="…")  # 1往復で話題を1本使い切る
    assert s.state is ConvState.CLOSING and s.close_reason == "soft_topics"


def test_soft_stop_on_silence():
    m = _manager(silence_ticks=3)
    s = _open(m, 1, 2, tick=0)
    m.step(3)
    assert s.state is ConvState.PARTICIPATING
    m.step(4)
    assert s.state is ConvState.CLOSING and s.close_reason == "soft_silence"


def test_leaving_is_never_decided_by_the_llm_but_退去_closes_the_session():
    m = _manager()
    s = _open(m, 1, 2)
    m.utterance(1, 1, action="退去", comment="なし")
    assert s.state is ConvState.CLOSING and s.close_reason == "退去"
    assert m.counters()["closed_退去"] == 1


def test_soft_stop_when_a_participant_leaves_the_cell():
    m = _manager()
    s = _open(m, 1, 2, cell=5)
    cells = np.array([0, 5, 5, 0], dtype=np.int32)
    m.step(1, cell=cells)
    assert s.state is ConvState.PARTICIPATING
    cells[2] = 9  # 相手がセルを出た
    m.step(2, cell=cells)
    assert s.state is ConvState.CLOSING and s.close_reason == "left_cell"


def test_session_timeout_is_a_bounded_cleanup():
    m = _manager(silence_ticks=10_000, max_session_ticks=7)
    s = _open(m, 1, 2, tick=0)
    m.step(6)
    assert s.state is ConvState.PARTICIPATING
    m.step(7)
    assert s.close_reason == "timeout"


def test_closing_emits_the_fixed_closing_utterance_then_terminal():
    m = _manager()
    s = _open(m, 1, 2)
    m.utterance(1, 1, action="退去", comment="なし")
    assert m.closing_utterance(s) == CLOSING_UTTERANCE
    finished = m.step(2)
    assert finished == [s] and s.state is ConvState.TERMINAL and s.closed_tick == 2


def test_purge_terminal_frees_the_table():
    m = _manager()
    s = _open(m, 1, 2)
    m.utterance(1, 1, action="退去", comment="なし")
    m.step(2)
    assert m.purge_terminal() == 1 and m.sessions == {}


def test_counters_report_openings_and_reasons():
    m = _manager()
    _open(m, 1, 2)
    m.utterance(1, 1, action="退去", comment="なし")
    m.step(2)
    c = m.counters()
    assert c["sessions_opened"] == 1 and c["sessions_closed"] == 1
    assert c["utterance_blocks"] == 1 and c["closed_退去"] == 1


def test_invalid_configuration_is_rejected():
    with pytest.raises(ValueError):
        ConversationManager(SEED, max_participants=4)
    with pytest.raises(ValueError):
        ConversationManager(SEED, accept_probability=1.5)


# ---------------------------------------------------------------- run_day 結線
class _TalkLLM:
    """偶数tickは「退去」(=全員 idle に戻す)、奇数tickは「会話」を返す台本。"""

    def __init__(self) -> None:
        self.n_calls = 0

    def complete(self, request):
        from shibuya.llm import LLMResponse, format_two_line

        self.n_calls += 1
        word = "会話" if request.tick % 2 else "退去"
        return LLMResponse(text=format_two_line("台本", word, "なし", "やあ"), source="scripted")


def test_run_day_opens_conversation_sessions_when_resolve_creates_them():
    """resolve が会話を成立させたら ``ConversationManager`` が受け取り、話者を起こす。"""
    from shibuya.engine.run import run_day

    res = run_day(
        n_agents=400, seed=5, ticks=360, checkpoint_every=360, n_cells=2,
        budget=400.0, llm=_TalkLLM(),
    )
    counters = res.conversation_counters
    assert counters["sessions_opened"] > 0, counters
    assert res.conversation_sessions == counters["sessions_opened"]
    assert counters["utterance_blocks"] > 0
    assert counters["sessions_closed"] > 0
    assert res.parse_error_rate == 0.0


def test_run_day_leaves_no_conversing_agent_without_a_session():
    """層2指摘(C3): 不応答/却下の招待側が CONVERSING に取り残されない。
    被招待側は C4 まで IDLE のままなので、日末の CONVERSING 数 == 活動セッション数。"""
    from shibuya.engine.run import run_day

    res = run_day(n_agents=400, seed=11, ticks=360)
    c = res.conversation_counters
    assert c["conversing_agents_end"] == c["sessions_active"], c
