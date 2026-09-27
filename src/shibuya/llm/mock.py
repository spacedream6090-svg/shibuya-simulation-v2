"""llm.mock — ネットワーク不要の決定論クライアント(MockLLM)とテープ再生クライアント(TapeLLM)。

正典
- 予算宣言表 W2: 「壁時計/シミュ日(Phase 2・5千体・CPU・**mock LLM**)≤10分」
  =「mock は呼び出しコストゼロ級=**エンジン性能の検収値**」。本モジュールがその mock。
- 行動契約書 §1(2行形)・§2.1(12語)= 出力の書式。
- 運用設計書 §2.5: 乱数=Philox・カウンタ=**(tick, entity_id, draw_index)**=呼び出し順非依存。
  ``MockLLM`` は ``core.rng.stream(master_seed, "llm.mock", tick, agent_id, wake_class)`` を使う
  (C2 指示は ``(agent_id, tick)`` の並びだったが、**設計書 §2.5 のカウンタ順**に合わせた)。
- 運用設計書 §2.5: リプレイはテープ完全一致・**テープ外は失敗**(``TapeLLM`` は例外を握り潰さない)。

逐次ループ宣言(P4): なし(1呼=1回の呼び出し。配列化された一括生成は持たない)。

expedient
- 理由・ひと言の語句表、行動語の**一様**抽選、対象の選び方は全て自前(mock は「振る舞いのモデル」
  ではなく、書式と決定論を通す配管)。分布を実データに寄せる意図はない
  ——寄せると mock が暗黙のモデルになり、較正の汚染源になる。
- ``tokens_in``/``tokens_out`` は ``estimate_tokens``(文字数÷2)。
- **語彙 v3 の出力形(二層の段 3・D-116・第277)**: ``form="v3"`` で 5 ラベル形
  (理由・行動・対象・活動・まで)を返す。行為=渡された語彙(11 語+なし)の一様・対象=既存の
  規則(``request.targets`` があればそこから・無ければ なし)に加えて **移動 の 1/3 を「あたり」**・
  活動=固定 6 語の一様・まで={30分, 60分, 次の予定}+移動のときだけ「到着」の一様
  (二層の実装アジェンダ §3)。**行為の分布の錨は D-119 の古典モデルが来るまでの繋ぎ**(expedient)。
  乱数は同じストリームから 6 語引く(v1/v2 の ``form="v1"`` は従来どおり 3 語=**1 バイトも
  変わらない**)。
"""

from __future__ import annotations

from typing import Any, Final

from shibuya.core.rng import stream
from shibuya.core.types import EventClass
from shibuya.llm import (
    ACTION_VOCAB_12,
    NO_TARGET,
    LLMRequest,
    LLMResponse,
    TapeLookup,
    estimate_tokens,
    format_two_line,
)
from shibuya.llm.contract import TARGET_WANDER, format_two_line_v3

__all__ = [
    "MOCK_REASONS",
    "MOCK_COMMENTS",
    "MOCK_RNG_DOMAIN",
    "MOCK_FORMS",
    "MOCK_ACTIVITIES_V3",
    "MOCK_UNTILS_V3",
    "MOCK_UNTILS_V3_MOVE",
    "MOCK_WANDER_ONE_IN",
    "MockLLM",
    "TapeLLM",
]

#: ``core.rng`` のドメイン名(manifest の ``rng.domain_table_version`` で版管理される表の1項)。
MOCK_RNG_DOMAIN: Final[str] = "llm.mock"

#: 理由の語句(各40字以内・1文)。
MOCK_REASONS: Final[tuple[str, ...]] = (
    "予定の時間になったから",
    "空腹を感じたから",
    "人が多くて落ち着かないから",
    "次の用事に間に合わせたいから",
    "疲れがたまってきたから",
    "知人を見かけたから",
    "店が開いていたから",
    "呼ばれた気がしたから",
)

#: ひと言の語句(各20字以内)。
MOCK_COMMENTS: Final[tuple[str, ...]] = (
    NO_TARGET,
    "少し急ごう",
    "混んでいるな",
    "また後で",
    "ちょうどいい",
)

#: 出力形。``"v1"``=行動・対象・ひと言(語彙 v1/v2)/``"v3"``=行動・対象・活動・まで(語彙 v3)。
MOCK_FORMS: Final[tuple[str, ...]] = ("v1", "v3")
#: 語彙 v3 の活動(二層の実装アジェンダ §3 の固定 6 語・一様)。
MOCK_ACTIVITIES_V3: Final[tuple[str, ...]] = ("休む", "店を見る", "散歩", "待つ", "仕事", "食事")
#: 語彙 v3 の「まで」(移動以外)。
MOCK_UNTILS_V3: Final[tuple[str, ...]] = ("30分", "60分", "次の予定")
#: 同(移動のとき=「到着」を足す)。
MOCK_UNTILS_V3_MOVE: Final[tuple[str, ...]] = ("30分", "60分", "到着", "次の予定")
#: 移動の対象を「あたり」にする割合の分母(1/3・アジェンダ §3)。
MOCK_WANDER_ONE_IN: Final[int] = 3
_MOVE_WORD: Final[str] = "移動"


class MockLLM:
    """決定論の 2 行形を返す mock クライアント(ネットワーク・GPU 不要)。

    同じ ``(master_seed, agent_id, tick, wake_class)`` からは常に同じ応答が出る。
    個体数を増やしても既存個体の列は変わらない(カウンタベース=T4)。

    Example:
        >>> llm = MockLLM(master_seed=1234)
        >>> r = llm.complete(LLMRequest(agent_id=7, tick=3, wake_class=1, prompt="…"))
        >>> r.text.splitlines()[1].startswith("行動: ")
        True
    """

    def __init__(
        self,
        master_seed: int | str,
        *,
        domain: str = MOCK_RNG_DOMAIN,
        vocab: tuple[str, ...] = ACTION_VOCAB_12,
        reasons: tuple[str, ...] = MOCK_REASONS,
        comments: tuple[str, ...] = MOCK_COMMENTS,
        form: str = "v1",
        activities: tuple[str, ...] = MOCK_ACTIVITIES_V3,
    ) -> None:
        if not vocab:
            raise ValueError("vocab が空")
        if str(form) not in MOCK_FORMS:
            raise ValueError(f"form は {MOCK_FORMS} のどれか(いま {form!r})")
        if not activities:
            raise ValueError("activities が空")
        self.master_seed = master_seed
        self.domain = domain
        self.vocab = tuple(vocab)
        self.reasons = tuple(reasons)
        self.comments = tuple(comments)
        self.form = str(form)
        self.activities = tuple(activities)
        self.n_calls = 0

    def _stream(self, request: LLMRequest):
        # カウンタ = (tick, entity_id, draw_index)(§2.5)。draw_index の枠に起床クラスを置く。
        # class_rank は制度=−1 を含むため、``-EventClass.INSTITUTION`` を足して非負にする
        # (``core.rng`` のカウンタは 0..2^64−1)。
        draw_index = int(request.wake_class) - int(EventClass.INSTITUTION)
        if draw_index < 0:
            raise ValueError(f"未知の wake_class: {request.wake_class}")
        return stream(
            self.master_seed,
            self.domain,
            int(request.tick),
            int(request.agent_id),
            draw_index,
        )

    def _draws(self, request: LLMRequest) -> tuple[int, int, int]:
        # カウンタ = (tick, entity_id, draw_index)(§2.5)。draw_index の枠に起床クラスを置く。
        # class_rank は制度=−1 を含むため、``-EventClass.INSTITUTION`` を足して非負にする
        # (``core.rng`` のカウンタは 0..2^64−1)。
        draw_index = int(request.wake_class) - int(EventClass.INSTITUTION)
        if draw_index < 0:
            raise ValueError(f"未知の wake_class: {request.wake_class}")
        g = stream(
            self.master_seed,
            self.domain,
            int(request.tick),
            int(request.agent_id),
            draw_index,
        )
        values = g.integers(0, 1 << 31, size=3)
        return int(values[0]), int(values[1]), int(values[2])

    def _render_v3(self, request: LLMRequest) -> str:
        """語彙 v3 の 5 ラベル形(二層の段 3)。同じストリームから 6 語引く。"""
        a, b, c, d, e, f = (int(x) for x in self._stream(request).integers(0, 1 << 31, size=6))
        action = self.vocab[a % len(self.vocab)]
        reason = self.reasons[b % len(self.reasons)]
        target = request.targets[c % len(request.targets)] if request.targets else NO_TARGET
        if action == _MOVE_WORD and d % MOCK_WANDER_ONE_IN == 0:
            target = TARGET_WANDER
        activity = self.activities[e % len(self.activities)]
        untils = MOCK_UNTILS_V3_MOVE if action == _MOVE_WORD else MOCK_UNTILS_V3
        until = untils[f % len(untils)]
        return format_two_line_v3(reason, action, target, activity, until)

    def render(self, request: LLMRequest) -> str:
        """応答本文(2行形)を作る(副作用なし)。``form="v3"`` は 5 ラベル形。"""
        if self.form == "v3":
            return self._render_v3(request)
        a, b, c = self._draws(request)
        action = self.vocab[a % len(self.vocab)]
        reason = self.reasons[b % len(self.reasons)]
        comment = self.comments[c % len(self.comments)]
        target = request.targets[c % len(request.targets)] if request.targets else NO_TARGET
        return format_two_line(reason, action, target, comment)

    def complete(self, request: LLMRequest) -> LLMResponse:
        """``LLMClient`` 契約の同期実装。"""
        text = self.render(request)
        self.n_calls += 1
        return LLMResponse(
            text=text,
            tokens_in=estimate_tokens(request.prompt),
            tokens_out=estimate_tokens(text),
            source="mock",
        )

    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        """非同期版(実 I/O は無いので同期実装をそのまま返す)。"""
        return self.complete(request)


class TapeLLM:
    """録画テープから答えるクライアント。**テープ外は例外**(黙って実LLMへ落とさない)。

    Args:
        lookup: ``lookup(agent_id, tick, wake_class, prompt_hash) -> str`` を持つ任意の
            オブジェクト(``shibuya.engine.tape.Replay`` がそのまま使える)。llm 層は
            engine を import できないため**注入**で受ける(``TapeLookup`` プロトコル)。

    Note:
        テープ外のときに ``lookup`` が投げる例外(``engine.tape.TapeMiss``)は**そのまま伝播**する。
        握り潰して mock へ落とすと「テープ外率」が測れなくなる(運用設計書 §2.5)。
    """

    def __init__(self, lookup: TapeLookup, *, source: str = "tape") -> None:
        if not hasattr(lookup, "lookup"):
            raise TypeError("lookup は lookup(agent_id, tick, wake_class, prompt_hash) を持つこと")
        self._lookup = lookup
        self.source = source
        self.n_calls = 0

    def complete(self, request: LLMRequest) -> LLMResponse:
        """``LLMClient`` 契約の同期実装(完全一致でテープを引く)。"""
        text = self._lookup.lookup(
            int(request.agent_id), int(request.tick), int(request.wake_class), request.prompt_hash
        )
        self.n_calls += 1
        return LLMResponse(
            text=text,
            tokens_in=estimate_tokens(request.prompt),
            tokens_out=estimate_tokens(text),
            source=self.source,
        )

    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        """非同期版(テープ読みは同期)。"""
        return self.complete(request)

    def __getattr__(self, name: str) -> Any:  # pragma: no cover - 委譲(hits/misses 等)
        return getattr(self._lookup, name)
