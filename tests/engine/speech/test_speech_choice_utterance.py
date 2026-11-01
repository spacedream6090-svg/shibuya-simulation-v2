"""第 1 期 1-8b: 1-8 の予約の欄 ``Choice.utterance`` が埋まる側(検収 低6・口の約束 1-8 の約束 (4))。

会話の番の呼び出し(``CONVERSATION_TURN``)の答えに ひと言(空と「なし」でない本文)があるときだけ埋まり、会話の番でない
呼び出し・「なし」・空は None のまま。3 つの実装(LLM・mock・古典)とも同じ規則(``ports._utterance_of``)。口は欄を読まない
(J0 の判断の番号と行為は変わらない)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from shibuya.agents.state import WakeCondition
from shibuya.engine.decision import ports as PS
from shibuya.llm.contract import cross_action_words
from shibuya.llm.mock import MockLLM
from tests.engine.decision._j0 import FakePolicy, ctx_of, vocab_candidates

TURN = int(WakeCondition.CONVERSATION_TURN)


@dataclass(frozen=True)
class _Parse:
    action: str | None
    comment: str
    raw_action: str = ""
    reason: str = "理由"


@dataclass(frozen=True)
class _Res:
    parse: _Parse
    action_code: int = -1
    deferred: bool = False
    observed_tick: int = -1


class _Bridge:
    def __init__(self, comment: str) -> None:
        self.comment = comment

    def finish(self, start: Any, *, complete: Any = None, percept_out: Any = None) -> _Res:
        if complete is not None:
            complete(start)
        return _Res(_Parse("会話", self.comment, raw_action="会話"))


def _ports(comment: str):
    return (PS.LlmPort(_Bridge(comment), seed=1),
            PS.MockPort(_Bridge(comment), MockLLM(1, vocab=cross_action_words("v3"), form="v3"), seed=1),
            PS.ClassicalPort(_Bridge(comment), FakePolicy("会話"), seed=1))


@pytest.mark.parametrize("which", [0, 1, 2])
def test_a_conversation_turn_with_a_comment_fills_the_field(which):
    port = _ports("こんにちは")[which]
    ctx = ctx_of(condition=TURN)
    ch = port.choose(ctx, vocab_candidates("v3", ctx))
    assert ch.utterance == "こんにちは"


@pytest.mark.parametrize("which", [0, 1, 2])
@pytest.mark.parametrize("comment,condition", [("なし", TURN), ("", TURN), ("  ", TURN), ("こんにちは", 3)])
def test_otherwise_the_field_stays_empty(which, comment, condition):
    port = _ports(comment)[which]
    ctx = ctx_of(condition=condition)
    assert port.choose(ctx, vocab_candidates("v3", ctx)).utterance is None
