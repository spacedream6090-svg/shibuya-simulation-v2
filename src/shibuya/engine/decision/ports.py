"""engine.decision.ports — 候補の口の 3 つの実装(同じ入口 ``DecisionPort.choose``)(第 1 期 1-8 J0)。

- ``LlmPort``: 今の「文 → 2 行形 → パーサ → 語彙」を口の後ろに置く(プロンプトは変えない)。口の後ろの道
  (``LLMBridge.finish``)の答えの行為の語を、同じ種類の候補に写す。どの候補にも当たらない答え(語彙の外・役割語・未定義の語・
  書式の誤り)は「その他(自由記述)」=``other_text`` に答えの語(生まれた行動の入口=C-2 の 3)。理由は 2 行形の 1 行目
  (理由を先に=``reason_first``)。
- ``MockPort``: 今の mock の判断と**同じ乱数の鍵から同じ番号**(``MockLLM.action_draw``=(刻み・体・起床の級)の流れの
  1 語目 ``a``)。候補のうち mock の語彙の語を語彙の順に並べ、``a`` を候補の数で割った余りの番号の候補を選ぶ=中身で選ぶ
  (提示の並べ替えに左右されない)。語彙の全部が候補にあれば今の mock と同じ語。口の後ろの道は今のまま通す(対象・活動・
  まで・テープの行=今の mock の本文)。
- ``ClassicalPort``: 古典の方策 G(``engine.classical.ClassicalPolicy``)の答えの 5 つ(``answer``)の行動の語を候補に写す
  (G の構造の答え=本文を読み直さない)。口の後ろの道に同じ方策の口を包んで渡す(応答・計数・副作用は今と同じ)。

どの実装も驚き・迷い・連続値は空(〔決定〕=空で始める)。口は ``ctx`` の値(予想・観測)を解釈しない。
〔第 1 期 1-8b〕「ひと言」の欄 ``Choice.utterance`` は、会話の番の呼び出し(``WakeCondition.CONVERSATION_TURN``)の答えに
ひと言(空と「なし」でない本文)があるときだけ埋める(会話の行だけに戻す=口の約束 1-8 の約束 (4))。発話の口(``engine.speech``)
に通すのは会話の系(``engine.systems.llm_io.utter``)で、口は欄を読まない(J0 の判断の番号・行為は変わらない)。

先例(R-113 §9・形だけ): Concordia ``language_model.sample_choice``(実 LLM と mock が同じ入口・Apache-2.0)。

逐次ループ宣言(P4): ``_answer`` は提示の候補の数ぶん(≤ 20)。
"""

from __future__ import annotations

from typing import Any

from shibuya.agents.state import WakeCondition
from shibuya.engine.decision.port import OTHER_ID, Candidate, DecisionContext, DecisionPort
from shibuya.llm.contract import NO_TARGET

__all__ = ["LlmPort", "MockPort", "ClassicalPort", "PORT_NAMES"]

#: 実装の名(manifest の ``decision_port.port``)。
PORT_NAMES: tuple[str, ...] = ("llm", "mock", "classical")


def _utterance_of(ctx: DecisionContext, res: Any) -> str | None:
    """〔1-8b〕会話の番の答えの「ひと言」(本文)。会話の番でない呼び出し・空・「なし」は ``None``(欄は空のまま)。"""
    if int(ctx.condition) != int(WakeCondition.CONVERSATION_TURN):
        return None
    text = str(getattr(getattr(res, "parse", None), "comment", "") or "").strip()
    return None if (not text or text == NO_TARGET) else text


def _by_kind(presented: tuple[Candidate, ...], word: str | None) -> str | None:
    if word is None:
        return None
    for c in presented:
        if c.kind == word:
            return c.id
    return None


class LlmPort(DecisionPort):
    """口の後ろに今の LLM の道(``bridge``=``engine.llm_bridge.LLMBridge``)を置く実装。"""

    name = "llm"

    def __init__(self, bridge: Any, **kw: Any) -> None:
        super().__init__(**kw)
        self.bridge = bridge

    def _answer(self, ctx: DecisionContext, presented: tuple[Candidate, ...]) -> tuple[str, dict[str, Any]]:
        res = self.bridge.finish(ctx.request)
        parse = res.parse
        cid = _by_kind(presented, getattr(parse, "action", None))
        extra: dict[str, Any] = {"backend": res, "reason": str(getattr(parse, "reason", "") or "") or None,
                                 "reason_first": True, "utterance": _utterance_of(ctx, res)}
        if cid is None:
            raw = str(getattr(parse, "raw_action", "") or "")
            return OTHER_ID, {**extra, "other_text": raw}
        return cid, extra


class MockPort(DecisionPort):
    """今の mock(``llm.mock.MockLLM``)と同じ鍵から同じ番号を選ぶ実装(判断モデルの代役)。"""

    name = "mock"

    def __init__(self, bridge: Any, mock: Any, **kw: Any) -> None:
        super().__init__(**kw)
        self.bridge = bridge
        self.mock = mock
        self._rank = {w: i for i, w in enumerate(mock.vocab)}

    def pick(self, ctx: DecisionContext, presented: tuple[Candidate, ...]) -> str:
        """中身で選ぶ(提示の並びは使わない): mock の語彙の候補を語彙の順に並べ、抽選の値を数で割った余りの候補。"""
        cands = sorted((c for c in presented if c.kind in self._rank), key=lambda c: (self._rank[c.kind], c.id))
        if not cands:
            return OTHER_ID
        a = self.mock.action_draw(ctx.agent_id, ctx.step, ctx.wake_class)
        return cands[a % len(cands)].id

    def _answer(self, ctx: DecisionContext, presented: tuple[Candidate, ...]) -> tuple[str, dict[str, Any]]:
        res = self.bridge.finish(ctx.request)
        cid = self.pick(ctx, presented)
        extra: dict[str, Any] = {"backend": res, "utterance": _utterance_of(ctx, res)}
        if cid == OTHER_ID:
            return OTHER_ID, {**extra, "other_text": ""}
        return cid, extra


class ClassicalPort(DecisionPort):
    """古典の方策 G の答えの行動の語を候補に写す実装。"""

    name = "classical"

    def __init__(self, bridge: Any, policy: Any, **kw: Any) -> None:
        super().__init__(**kw)
        self.bridge = bridge
        self.policy = policy

    def _answer(self, ctx: DecisionContext, presented: tuple[Candidate, ...]) -> tuple[str, dict[str, Any]]:
        got: list[tuple[str, str, str, str, str]] = []

        def complete(request: Any) -> Any:
            resp, ans = self.policy.complete_with_answer(request)
            got.append(ans)
            return resp

        res = self.bridge.finish(ctx.request, complete=complete)
        extra: dict[str, Any] = {"backend": res, "utterance": _utterance_of(ctx, res)}
        if not got:  # 再生のラン(テープの行を引いた)=方策は呼ばれない → 今の道の語で写す
            word = getattr(res.parse, "action", None)
        else:
            word = got[-1][1]
            extra["reason"] = got[-1][0] or None
        cid = _by_kind(presented, word)
        if cid is None:
            return OTHER_ID, {**extra, "other_text": "" if word is None else str(word)}
        return cid, extra
