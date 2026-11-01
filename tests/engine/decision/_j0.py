"""第 1 期 1-8 J0 の試験の道具(候補の列・口の後ろの道の代役・腕の切り替え・小さなラン)。"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any, Iterator

from shibuya.engine.decision import layer as DL
from shibuya.engine.decision.port import DecisionContext
from shibuya.engine.decision.sources import build_candidates
from shibuya.engine.llm_bridge import ACTION_WORD_BY_CODE
from shibuya.llm.contract import cross_action_words, safe_action_word


@contextlib.contextmanager
def decision_arm(name: str) -> Iterator[None]:
    """腕を一時的に切り替える(試験の後は元に戻す)。"""
    prev = DL.arm()
    DL.set_arm(name)
    try:
        yield
    finally:
        DL.set_arm(prev)


@dataclass(frozen=True)
class FakeParse:
    action: str | None
    raw_action: str = ""
    reason: str = ""


@dataclass(frozen=True)
class FakeResult:
    parse: FakeParse
    action_code: int = -1
    deferred: bool = False
    observed_tick: int = -1


class FakeBridge:
    """口の後ろの今の道の代役: ``finish`` は決めた語を答え、``complete`` が渡されたらそれを呼んでから答える。"""

    def __init__(self, word: str | None = None, raw: str = "") -> None:
        self.word = word
        self.raw = raw
        self.n_finish = 0

    def finish(self, start: Any, *, complete: Any = None, percept_out: Any = None) -> FakeResult:
        self.n_finish += 1
        if complete is not None:
            complete(start)
        return FakeResult(parse=FakeParse(self.word, raw_action=self.raw or (self.word or ""), reason="理由"))


class FakePolicy:
    """古典の方策の代役(``complete_with_answer`` が答えの 5 つを返す)。"""

    def __init__(self, action: str) -> None:
        self.action = action
        self.n = 0

    def complete_with_answer(self, request: Any) -> tuple[Any, tuple[str, str, str, str, str]]:
        self.n += 1
        return object(), ("理由", self.action, "なし", "休む", "30分")


def ctx_of(agent_id: int = 7, step: int = 600, wake_class: int = 1, **kw: Any) -> DecisionContext:
    base: dict[str, Any] = dict(agent_id=agent_id, step=step, t_ns=step * 60 * 10**9, wake_class=wake_class,
                                condition=3, cell=2, call_id=f"{step}:{agent_id}:{wake_class}")
    base.update(kw)
    return DecisionContext(**base)


def vocab_candidates(version: str = "v3", ctx: DecisionContext | None = None) -> tuple:
    """語彙の全語+よく考える(源は続ける・語彙の残り・よく考える)。"""
    return build_candidates(ctx or ctx_of(), vocab=cross_action_words(version), continue_word=safe_action_word(version),
                            word_of_code=ACTION_WORD_BY_CODE, kind_words={})


#: 小さなラン(合成の世界・mock・語彙 v3)。
SMALL = dict(n_agents=120, seed=3, n_cells=16, ticks=360, budget=200.0, vocab_version="v3", checkpoint_every=120)
