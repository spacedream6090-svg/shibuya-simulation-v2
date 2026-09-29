"""mock 方策の語彙 v3 化(二層の段 3・D-116・第277・アジェンダ §3)。

見るもの
(i)   ``form="v1"``(既定)は従来の 3 ラベル形のまま(v1/v2 の mock の出力は 1 バイトも変わらない)
(ii)  ``form="v3"`` は 5 ラベル形で、パーサ v3 が厳密に読める(書式エラー 0)
(iii) 行為=渡された語彙の一様・「あたり」は 移動 のときだけ・「到着」は 移動 のときだけ・
      活動=固定 6 語・決定論
(iv)  ``engine.run._default_mock("v3")`` が v3 形の mock を返す
"""

from __future__ import annotations

from collections import Counter

import pytest

from shibuya.engine.run import _default_mock
from shibuya.llm import LLMRequest
from shibuya.llm.contract import cross_action_words
from shibuya.llm.mock import (
    MOCK_ACTIVITIES_V3,
    MOCK_UNTILS_V3,
    MOCK_UNTILS_V3_MOVE,
    MockLLM,
)
from shibuya.llm.parser import parse_two_line


def _req(agent: int, tick: int, cls: int = 1) -> LLMRequest:
    return LLMRequest(agent_id=agent, tick=tick, wake_class=cls, prompt="…")


def _v3() -> MockLLM:
    return MockLLM(master_seed=1, vocab=cross_action_words("v3"), form="v3")


def test_v1_form_is_the_default_and_unchanged():
    a = MockLLM(master_seed=1)
    b = MockLLM(master_seed=1, form="v1")
    for t in range(20):
        ta, tb = a.render(_req(3, t)), b.render(_req(3, t))
        assert ta == tb and "ひと言:" in ta and "活動:" not in ta
    assert a.render(_req(3, 0)) == "理由: 疲れがたまってきたから\n行動: 断る 対象: なし ひと言: 少し急ごう"


def test_v3_form_is_read_strictly_by_the_v3_parser():
    m = _v3()
    for agent in range(40):
        for tick in range(0, 400, 37):
            r = parse_two_line(m.render(_req(agent, tick)), "v3")
            assert r.format_ok and r.strict_format_ok and r.strict_two_line, r.errors


def test_v3_draw_rules():
    m = _v3()
    words = cross_action_words("v3")
    acts: Counter[str] = Counter()
    wander_move = move = 0
    for agent in range(300):
        for tick in range(0, 1440, 97):
            r = parse_two_line(m.render(_req(agent, tick)), "v3")
            acts[r.action] += 1
            assert r.activity in MOCK_ACTIVITIES_V3
            if r.action == "移動":
                move += 1
                wander_move += int(r.target.wander)
                assert r.raw_until in MOCK_UNTILS_V3_MOVE
            else:
                assert not r.target.wander, "あたり は 移動 のときだけ"
                assert r.raw_until in MOCK_UNTILS_V3, "到着 は 移動 のときだけ"
    assert set(acts) == set(words), "11 語+なし が全部出る"
    n = sum(acts.values())
    assert max(acts.values()) / n < 1.5 / len(words), "一様(偏りが大きくない)"
    assert 0.25 < wander_move / move < 0.42, "移動の 1/3 が あたり"


def test_v3_is_deterministic_and_counter_based():
    a, b = _v3(), _v3()
    assert [a.render(_req(5, t)) for t in range(30)] == [b.render(_req(5, t)) for t in range(30)]
    assert a.render(_req(5, 3)) != a.render(_req(6, 3))


def test_bad_form_is_refused():
    with pytest.raises(ValueError):
        MockLLM(master_seed=1, form="v2")


def test_default_mock_follows_the_vocab_version():
    assert _default_mock(1, "v1").form == "v1"
    assert _default_mock(1, "v2").form == "v1"
    m3 = _default_mock(1, "v3")
    assert m3.form == "v3" and m3.vocab == cross_action_words("v3")
