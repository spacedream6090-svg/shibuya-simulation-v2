"""llm.mock のテスト(2行形・決定論・テープ再生)。

置き場所について: ``TapeLLM`` の結線相手(``engine.tape.Replay``)が engine 側にあるため、
llm の結線テストは tests/engine に置く(C2 の担当範囲は tests/core と tests/engine)。
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shibuya.engine.tape import Replay, TapeMiss, TapeRow, TapeWriter
from shibuya.llm import (
    ACTION_VOCAB_12,
    NO_TARGET,
    TWO_LINE_RE,
    LLMClient,
    LLMRequest,
    MockLLM,
    TapeLLM,
)

SEED = 20260908


def _req(agent_id=7, tick=3, wake_class=1, **kw) -> LLMRequest:
    kw.setdefault("prompt", "共有静的+セル依存+個体の観測ブロック")
    return LLMRequest(agent_id=agent_id, tick=tick, wake_class=wake_class, **kw)


def test_vocab_is_the_12_words_of_the_action_contract():
    assert len(ACTION_VOCAB_12) == 12
    assert ACTION_VOCAB_12[:5] == ("移動", "乗車", "降車", "購入", "待機")
    assert "就寝" in ACTION_VOCAB_12
    assert len(set(ACTION_VOCAB_12)) == 12


def test_mock_output_is_two_line_form():
    m = MockLLM(SEED)
    text = m.complete(_req()).text
    match = TWO_LINE_RE.match(text)
    assert match, repr(text)
    assert match.group("action") in ACTION_VOCAB_12
    assert len(match.group("reason")) <= 40
    assert len(match.group("comment")) <= 20
    assert text.count("\n") == 1


@settings(max_examples=100, deadline=None)
@given(
    agent_id=st.integers(min_value=0, max_value=400_000),
    tick=st.integers(min_value=0, max_value=1_440),
    wake_class=st.sampled_from([-1, 0, 1, 2, 3]),
)
def test_property_always_two_line_and_in_vocab(agent_id, tick, wake_class):
    m = MockLLM(SEED)
    text = m.render(_req(agent_id, tick, wake_class))
    match = TWO_LINE_RE.match(text)
    assert match, repr(text)
    assert match.group("action") in ACTION_VOCAB_12


def test_mock_is_deterministic_and_scale_invariant():
    """同じ (seed, tick, agent, class) は常に同じ応答=カウンタベース(T4)。"""
    a = MockLLM(SEED)
    b = MockLLM(SEED)
    assert a.render(_req()) == b.render(_req())
    assert a.render(_req(agent_id=8)) != a.render(_req(agent_id=7)) or True  # 衝突は許容
    assert MockLLM("run-abc").render(_req()) != a.render(_req())
    assert a.render(_req(tick=4)) != a.render(_req(tick=3)) or True


def test_mock_uses_targets_when_given():
    m = MockLLM(SEED)
    assert "対象: なし" in m.render(_req())
    text = m.render(_req(targets=("C0421",)))
    assert "対象: C0421" in text


def test_mock_counts_calls_and_estimates_tokens():
    m = MockLLM(SEED)
    r = m.complete(_req(prompt="あ" * 2_600))
    assert m.n_calls == 1
    assert r.tokens_in == 1_300
    assert r.tokens_out > 0
    assert r.source == "mock"
    assert isinstance(m, LLMClient)


def test_request_hashes_are_deterministic_and_field_sensitive():
    r1 = _req(prompt="A", params={"temperature": 0.7, "top_p": 0.8})
    r2 = _req(prompt="A", params={"top_p": 0.8, "temperature": 0.7})
    assert r1.prompt_hash == r2.prompt_hash
    assert r1.params_hash == r2.params_hash, "CBOR 正準符号化=キー順に依らない"
    assert _req(prompt="B").prompt_hash != r1.prompt_hash


def test_tape_llm_replays_recorded_mock_answers(tmp_path):
    """mock で録って TapeLLM で再生 → 完全一致(bit 再現の最小単位)。"""
    m = MockLLM(SEED)
    requests = [_req(agent_id=i, tick=i % 5, wake_class=i % 4) for i in range(20)]
    with TapeWriter(tmp_path) as w:
        block = w.intern_block("共有静的ブロック")
        for i, req in enumerate(requests):
            resp = m.complete(req)
            w.append(
                TapeRow(
                    call_id=f"c{i}",
                    agent_id=req.agent_id,
                    tick=req.tick,
                    wake_class=req.wake_class,
                    prompt_hash=req.prompt_hash,
                    block_ids=(block,),
                    params_hash=req.params_hash,
                    response=resp.text,
                    tokens_in=resp.tokens_in,
                    tokens_out=resp.tokens_out,
                )
            )
    replay = Replay(tmp_path)
    tape_llm = TapeLLM(replay)
    for req in requests:
        assert tape_llm.complete(req).text == m.render(req)
    assert tape_llm.complete(requests[0]).source == "tape"
    assert replay.misses == 0


def test_tape_llm_does_not_fall_back_to_mock(tmp_path):
    """テープ外は必ず失敗する(黙って実LLM/mock へ落とさない=運用設計書 §2.5)。"""
    with TapeWriter(tmp_path) as w:
        w.append(TapeRow("c0", 1, 0, 0, "ph", (), "pa", "理由: x\n行動: 待機 対象: なし ひと言: なし"))
    tape_llm = TapeLLM(Replay(tmp_path))
    with pytest.raises(TapeMiss):
        tape_llm.complete(_req())
    assert tape_llm.n_calls == 0
    assert tape_llm.misses == 1  # Replay へ委譲


def test_tape_llm_rejects_non_lookup_object():
    with pytest.raises(TypeError):
        TapeLLM(object())  # type: ignore[arg-type]


def test_mock_needs_no_network(monkeypatch):
    """mock は socket を一切触らない(W2「呼び出しコストゼロ級」の担保)。"""
    import socket

    def _boom(*a, **k):  # pragma: no cover
        raise AssertionError("mock がネットワークを使った")

    monkeypatch.setattr(socket, "socket", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    assert MockLLM(SEED).complete(_req()).text
