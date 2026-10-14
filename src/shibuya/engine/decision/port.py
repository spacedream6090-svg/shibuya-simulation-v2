"""engine.decision.port — 候補の口 J0 の型と、提示(順のシャッフルと番号)の仕組み(第 1 期 1-8・DM-0・DM4・DM5・DM13・C-2)。

正典
- 口の約束 ``docs/design/v2-foundation-contracts-2026-10-13.md`` の「1-8 候補の口 J0」(〔決定〕=「その他」の割合の既定は
  R-108 の値・驚きと迷いは空で始める)。計画 1-8(「本人の予想」と「今の観測」を並べて判断の入力に載せる=1-2 と合わせて)。
- 決定 10-12 §4-7 DM-0(候補は 5 つの源=経験・周りが示すできること・近い予定・続ける・よく考える)・DM4(短い版と長い版を
  1 つの仕組みで・共通部分を前に)・DM5(驚き 0〜5 の言葉・迷い=1 位と 2 位の差+エントロピー)・DM13(連続値)・§4-12 C-2
  (番号で返す共通の口・対策 4 つ)。回答 10-13b §4-2(知覚の事実と本人の予想を判断の入力に・驚くか・何をするか・よく
  考えるかは判断モデルが決める=口は値を解釈しない)。
- 先例(R-113 §9・形だけ借りた・コードは写していない): Concordia(Apache-2.0)
  ``concordia/document/interactive_document.py`` の ``multiple_choice_question``(候補を並べ替えて記号を振り、選ばれた記号を
  元の番号に戻す)と ``language_model.sample_choice``(実 LLM と mock が同じ入口)。違い: 並べ替えは乱数の鍵(10c の counter
  =``core.rng`` の ``k19_counters``・体と刻みと候補の数)から決める(Concordia は rng を渡さないと種なし)。

形
- ``Candidate``(凍結): ``id``・``kind``(行為の語=語彙の語、または ``DELIBERATE_KIND``)・``text``(頭に浮かんだこととしての
  見せ方=C-2 の 4)・``source``(``SOURCES`` の 5 つ。J0 だけ、語彙の残りを ``SOURCE_VOCAB``=つなぎの印で載せる)・
  ``number``(提示の番号=**最後に振る**=``present``)・``basis``(その候補の元の出来事 id=1-3 の ``EventId``。
  ``LlmCall.input_event_ids`` に入る)。
- ``Choice``(凍結): ``candidate_id``(選んだ候補・「その他」は ``OTHER_ID``)・``number``(選んだ提示の番号)・``kind``・
  ``other_text``(「その他(自由記述)」の中身)・``surprise``(0〜5・空で始める)・``hesitation``(迷い・空)・``continuous``
  (DM13 の連続値の欄・空)・``reason``・``reason_first``(理由を先に書かせたか=C-2 の 2・LLM の側だけ)・``utterance``
  (「ひと言」の欄=1-8b が埋める・空)・``backend``(口の後ろの今の道の結果=``LLMBridge`` の ``BridgeResult``)。
- ``DecisionContext``(凍結): 判断の入力。``percept``(今の観測=1-2 の ``Percept``)と ``prediction``(本人の予想=今は空)を
  並べて持つ(``perception.facts.PerceptCarrier`` の形)。記憶の見え方 ``memory``・道具 ``tools``(1-7 の後)・口の後ろの
  今の道の前半 ``request``(``LLMBridge.CallStart``)。口はどの値も解釈しない(候補を作る側と実装が読む)。
- ``DecisionPort``: ``choose(ctx, candidates) -> Choice`` の 1 つの口。並べ替え(``present``)と答えを元の id に戻すのは土台の
  クラスが行い、実装(``engine.decision.ports`` の ``MockPort``・``ClassicalPort``・``LlmPort``)は「提示した候補のどれか、
  または「その他」」だけを返す(``_answer``)。

「その他(自由記述)」の割合の既定(〔決定〕=R-108 の値): R-108 §1-5・空欄 R108-1=**LLM が「その他」の欄を選ぶ割合を測った
原典は見つからない**(近い証拠は NA が正解でも 8B は 18.3% しか選ばない=Wang ほか 2025 表 2・28 モデル平均の正答率 0.738 →
0.350=Tam ほか 2025 表 7)。§3-3 のとおり低い割合は「候補で足りている」証拠にならない=既定は値を置かず ``None``(未計測)と
し、割合は計器で測る(manifest の ``decision_port.other_ratio``)。mock と古典は「その他」を選ばない(今の道と同じ)。

逐次ループ宣言(P4): ``present`` は候補の数ぶん(≤ 20)・``options_text``・``compose`` も同じ。新しい逐次ループは無い。

expedient(本モジュール分)
- 「その他」は並べ替えず最後に置く(調査の慣行に合わせた・R-108 に原典なし)。
- 番号は 1 から振る。驚きの 6 語は DM5 の答えの言葉のまま(B 群の後に見直す)。
- ``compose`` の短い版と長い版の分け方(共通=描画の共有ブロック B0〜B4b・人ごと=短い版は B6 だけ・長い版は B5 と B6・
  長い版だけ「理由を先に・番号は最後」の指示の文)。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

import numpy as np

from shibuya.core.rng import k19_counters, run_tick_key, stream

__all__ = [
    "PORT_SCHEMA", "SOURCES", "SOURCE_EXPERIENCE", "SOURCE_AFFORDANCE", "SOURCE_PLAN", "SOURCE_CONTINUE",
    "SOURCE_DELIBERATE", "SOURCE_VOCAB", "ALL_SOURCES", "DELIBERATE_KIND", "OTHER_ID", "OTHER_TEXT",
    "SURPRISE_WORDS", "OTHER_SHARE_DEFAULT", "OTHER_SHARE_BASIS", "PRESENT_DOMAIN", "LENGTHS",
    "Candidate", "Hesitation", "Choice", "DecisionContext", "DecisionPort", "present", "present_rng",
    "options_text", "compose",
]

#: 口の形の版(欄を足したり意味を変えたりしたら上げる。manifest の ``decision_port.schema`` に出る)。
PORT_SCHEMA: Final[str] = "shibuya.engine.decision/port/1"

# ---- 候補の 5 つの源(DM-0・この順は記録の並び)----
SOURCE_EXPERIENCE: Final[str] = "experience"   # 本人の経験(似た状況で前にしたこと=記憶)
SOURCE_AFFORDANCE: Final[str] = "affordance"   # 周りが示す「できること」(知覚の中の開いている店など)
SOURCE_PLAN: Final[str] = "plan"               # 近い予定
SOURCE_CONTINUE: Final[str] = "continue"       # 今の行動を続ける
SOURCE_DELIBERATE: Final[str] = "deliberate"   # よく考える(LLM)
SOURCES: Final[tuple[str, ...]] = (
    SOURCE_EXPERIENCE, SOURCE_AFFORDANCE, SOURCE_PLAN, SOURCE_CONTINUE, SOURCE_DELIBERATE,
)
#: J0 だけのつなぎの印: 5 つの源のどれも出さなかった語彙の語(今の道=設計者の一覧)。mock の同値のために候補に残す。
#: つなぎの台帳の行 ``DOC-j0-candidates-vocab``(外す段=判断モデルを既定にする段)。
SOURCE_VOCAB: Final[str] = "vocab"
ALL_SOURCES: Final[tuple[str, ...]] = SOURCES + (SOURCE_VOCAB,)

#: 「よく考える」の候補の種類(行為の語ではない=エンジンは実行しない。選ばれたら上の層を呼ぶ=J3 以降)。
DELIBERATE_KIND: Final[str] = "よく考える"
#: 「その他(自由記述)」の id と見せ方(C-2 の 3)。
OTHER_ID: Final[str] = "other"
OTHER_TEXT: Final[str] = "その他(自由に書く)"
#: 驚き 0〜5 の言葉(DM5 の答え・B 群の後に見直す)。``Choice.surprise`` はこの番号(空=None で始める)。
SURPRISE_WORDS: Final[tuple[str, ...]] = ("予想どおり", "少し違う", "違う", "かなり意外", "とても意外", "ありえない")
#: 「その他」の割合の既定(〔決定〕=R-108 の値=測った原典なし=未計測)。値を置かない。
OTHER_SHARE_DEFAULT: Final[float | None] = None
OTHER_SHARE_BASIS: Final[str] = (
    "R-108 §1-5・空欄 R108-1(LLM が「その他(自由記述)」を選ぶ割合を測った原典なし。近い証拠=NA が正解でも 8B は 18.3%"
    "=Wang ほか 2025 表 2・28 モデル平均 0.738 → 0.350=Tam ほか 2025 表 7)・§3-3(低い割合は候補の十分さの証拠にならない"
    "=既知の答えの検査で測る)"
)
#: 並べ替えの乱数の用途名(``engine.run.MOTION_RNG_DOMAINS``)。
PRESENT_DOMAIN: Final[str] = "decision.present"
#: 入力の長さ(DM4: 短い版=判断モデル・長い版=LLM)。
LENGTHS: Final[tuple[str, ...]] = ("short", "long")


def _event_id_ok(x: Any) -> bool:
    return (isinstance(x, tuple) and len(x) == 2 and all(isinstance(v, (int, np.integer)) for v in x)
            and not any(isinstance(v, bool) for v in x))


@dataclass(frozen=True, slots=True)
class Candidate:
    """候補 1 つ(``number`` は提示のときに振る=作る側は ``None``)。"""

    id: str
    kind: str
    text: str
    source: str
    number: int | None = None
    #: その候補の元の出来事 id(1-3 の ``EventId``=``(t_ns, seq)``)。無ければ空。
    basis: tuple[tuple[int, int], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip() or self.id == OTHER_ID:
            raise ValueError(f"Candidate.id は空でない文字列(「その他」の id {OTHER_ID!r} は使えない)(いま {self.id!r})")
        if not isinstance(self.kind, str) or not self.kind.strip():
            raise ValueError("Candidate.kind は空でない文字列(行為の語か「よく考える」)")
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("Candidate.text は空でない文字列(頭に浮かんだこととしての見せ方)")
        if self.source not in ALL_SOURCES:
            raise ValueError(f"Candidate.source は {ALL_SOURCES} のどれか(いま {self.source!r})")
        if self.number is not None and (isinstance(self.number, bool) or not isinstance(self.number, int)
                                        or self.number < 1):
            raise ValueError(f"Candidate.number は 1 以上の整数か None(いま {self.number!r})")
        if not all(_event_id_ok(x) for x in self.basis):
            raise ValueError(f"Candidate.basis の要素は (t_ns, seq) の組(いま {self.basis!r})")
        object.__setattr__(self, "basis", tuple((int(x[0]), int(x[1])) for x in self.basis))


@dataclass(frozen=True, slots=True)
class Hesitation:
    """迷い(DM5): 1 位と 2 位の確率の差(``margin``)と分布のエントロピー(``entropy``・自然対数)。"""

    margin: float
    entropy: float

    @classmethod
    def of(cls, probs: Sequence[float]) -> "Hesitation":
        """候補の分布から(和が 1 でなければ割って正規化。候補が 1 つなら差は 1・エントロピーは 0)。"""
        p = np.asarray(list(probs), dtype=np.float64)
        if p.ndim != 1 or p.size == 0 or not bool(np.all(np.isfinite(p))) or bool(np.any(p < 0)) or p.sum() <= 0:
            raise ValueError("迷いは有限で 0 以上・和が正の分布から")
        p = p / p.sum()
        top = np.sort(p)[::-1]
        margin = float(top[0] - (top[1] if top.size > 1 else 0.0))
        nz = p[p > 0]
        return cls(margin=margin, entropy=float(-(nz * np.log(nz)).sum()))


@dataclass(frozen=True, slots=True)
class Choice:
    """口の答え(``choose`` が返す)。驚き・迷い・連続値・ひと言は空(None)で始める(〔決定〕と 1-8b)。"""

    candidate_id: str
    number: int
    kind: str | None = None
    other_text: str | None = None
    surprise: int | None = None
    hesitation: Hesitation | None = None
    continuous: Mapping[str, float] | None = None
    reason: str | None = None
    reason_first: bool | None = None
    #: 「ひと言」(発話)の欄。〔1-8b〕会話の番の答えに ひと言(空と「なし」でない本文)があるときだけ実装が埋める(``ports._utterance_of``)。
    utterance: Any = None
    #: 口の後ろの今の道の結果(``LLMBridge`` の ``BridgeResult``)。刻みの中だけ(状態にも結果の箱にも残さない)。
    backend: Any = field(default=None, compare=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_id, str) or not self.candidate_id:
            raise ValueError("Choice.candidate_id は空でない文字列")
        if isinstance(self.number, bool) or not isinstance(self.number, int) or self.number < 1:
            raise ValueError(f"Choice.number は 1 以上の整数(いま {self.number!r})")
        if self.candidate_id == OTHER_ID:
            if self.kind is not None:
                raise ValueError("「その他」の答えは kind を持たない(中身は other_text)")
        elif self.other_text is not None:
            raise ValueError("other_text は「その他」の答えだけ")
        if self.surprise is not None and (isinstance(self.surprise, bool) or not isinstance(self.surprise, int)
                                          or not 0 <= self.surprise < len(SURPRISE_WORDS)):
            raise ValueError(f"Choice.surprise は 0〜{len(SURPRISE_WORDS) - 1} の整数か None(いま {self.surprise!r})")
        if self.continuous is not None:
            object.__setattr__(self, "continuous", MappingProxyType(
                {str(k): float(v) for k, v in dict(self.continuous).items()}))

    @property
    def is_other(self) -> bool:
        return self.candidate_id == OTHER_ID


@dataclass(frozen=True, slots=True)
class DecisionContext:
    """判断の入力(``perception.facts.PerceptCarrier`` の形)。口は値を解釈しない。

    ``percept``(今の観測)と ``prediction``(本人の予想=今は空)を並べて持つ(回答 10-13b §4-2 の 3)。驚くか・何をするか・
    よく考えるかは判断の側が決める。``request`` は口の後ろの今の道の前半(``LLMBridge.CallStart``)。
    """

    agent_id: int
    step: int
    t_ns: int
    wake_class: int
    condition: int
    cell: int
    call_id: str
    percept: Any = None
    prediction: Any = None
    memory: tuple[Any, ...] | None = None
    tools: tuple[Any, ...] | None = None
    inviter: int = -1
    last_action: int = -1
    request: Any = field(default=None, compare=False, repr=False)


def present_rng(seed: int | str, step_key: int, agent_id: int, n: int) -> np.random.Generator:
    """並べ替えの乱数(10c の counter の鍵=``core.rng.k19_counters``(刻みの鍵・体・候補の数))。"""
    return stream(seed, PRESENT_DOMAIN, *k19_counters(int(step_key), int(agent_id), int(n)))


def present(candidates: Sequence[Candidate], rng: np.random.Generator) -> tuple[Candidate, ...]:
    """候補を並べ替え、提示の番号(1〜n)を**最後に**振った写しを返す(C-2 の 1・Concordia の形)。

    並べ替えは渡された並びに乱数の置換をかける(並びを入れ替えて渡すと提示の番号も変わる=並べ替えの試験)。「その他」は
    ここに入れない(``options_text`` が最後に足す・番号は n+1)。id の重複は ``ValueError``。
    """
    cands = list(candidates)
    ids = [c.id for c in cands]
    if len(set(ids)) != len(ids):
        raise ValueError(f"候補の id が重なっている: {ids}")
    if any(c.number is not None for c in cands):
        raise ValueError("番号は提示で振る(作る側は number=None)")
    order = rng.permutation(len(cands)) if cands else np.zeros(0, dtype=np.int64)
    return tuple(_numbered(cands[int(j)], k + 1) for k, j in enumerate(order))


_CANDIDATE_FIELDS: Final[tuple[str, ...]] = ("id", "kind", "text", "source", "basis")


def _numbered(c: Candidate, number: int) -> Candidate:
    """番号を振った写し(欄は検査済みの ``c`` のまま=作り直しの検査を省く・番号は 1 以上の整数)。"""
    out = object.__new__(Candidate)
    for f in _CANDIDATE_FIELDS:
        object.__setattr__(out, f, getattr(c, f))
    object.__setattr__(out, "number", int(number))
    return out


def options_text(presented: Sequence[Candidate]) -> str:
    """提示の文(候補は「頭に浮かんだこと」として・番号つき・最後に「その他」)。C-2 の 3・4。"""
    lines = ["頭に浮かんだこと:"]
    for c in sorted(presented, key=lambda c: int(c.number or 0)):
        lines.append(f"{c.number}. {c.text}")
    lines.append(f"{len(presented) + 1}. {OTHER_TEXT}")
    return "\n".join(lines)


#: 長い版(LLM)だけに付ける指示(C-2 の 2: 理由を先に自由に書き、番号は最後)。
_LONG_INSTRUCTION: Final[str] = "先に理由を自由に書き、最後に番号をひとつ書く(その他なら番号のあとに中身)。"
#: 共通部分(同じ刻み・同じセルの全員で同じ=prefix を共有できる)と人ごとの部分の描画のブロック。
_COMMON_BLOCKS: Final[tuple[str, ...]] = ("B0", "B1", "B2", "B3", "B4", "B4b")
_INDIVIDUAL_BLOCKS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({"short": ("B6",), "long": ("B5", "B6")})


def compose(blocks: Mapping[str, str], presented: Sequence[Candidate], *, length: str) -> str:
    """判断の入力の文(DM4: 短い版と長い版を 1 つの仕組みで・共通部分を前に)。J0 では使わない(プロンプトは今のまま)。

    ``blocks`` は描画のブロックの文(``B0``〜``B6``)。並びは 共通(B0〜B4b)→ 人ごと(短い版 B6・長い版 B5+B6)→ 提示 →
    (長い版だけ)指示。同じ状態からは短い版と長い版の先頭(共通部分)が同じバイトになる。
    """
    if length not in LENGTHS:
        raise ValueError(f"length は {LENGTHS} のどれか(いま {length!r})")
    parts = [blocks[b] for b in _COMMON_BLOCKS if b in blocks]
    parts += [blocks[b] for b in _INDIVIDUAL_BLOCKS[length] if b in blocks]
    parts.append(options_text(presented))
    if length == "long":
        parts.append(_LONG_INSTRUCTION)
    return "\n".join(parts)


class DecisionPort:
    """候補の口(判断モデルと LLM で 1 つ)。実装は ``_answer`` だけを書く。

    Args:
        seed: 並べ替えの乱数の種(ランの seed=動きの側)。
        day_key0: 日の鍵(``core.rng.run_tick_key`` の ``day_key0``)。
        step_seconds: 刻みの幅(秒)。
    """

    #: 実装の名(manifest の ``decision_port.port``)。
    name: str = ""

    def __init__(self, *, seed: int | str, day_key0: int = 0, step_seconds: int = 60) -> None:
        self.seed = seed
        self.day_key0 = int(day_key0)
        self.step_seconds = int(step_seconds)

    def step_key(self, step: int) -> int:
        """並べ替えの鍵の時刻(10c の counter と同じ ``run_tick_key``)。"""
        return run_tick_key(self.day_key0, int(step), self.step_seconds)

    def choose(self, ctx: DecisionContext, candidates: Sequence[Candidate]) -> Choice:
        """候補を並べ替えて番号を振り、実装の答えを元の id に戻す(C-2 の 1)。"""
        presented = present(candidates, present_rng(self.seed, self.step_key(ctx.step), ctx.agent_id,
                                                     len(candidates)))
        cid, extra = self._answer(ctx, presented)
        if cid == OTHER_ID:
            return Choice(candidate_id=OTHER_ID, number=len(presented) + 1, kind=None, **extra)
        for c in presented:
            if c.id == cid:
                return Choice(candidate_id=c.id, number=int(c.number or 0), kind=c.kind, **extra)
        raise ValueError(f"実装 {self.name} が提示に無い候補 {cid!r} を返した")

    def _answer(self, ctx: DecisionContext, presented: tuple[Candidate, ...]) -> tuple[str, dict[str, Any]]:
        """提示した候補のどれか(id)か ``OTHER_ID`` と、``Choice`` の残りの欄を返す(実装が書く)。"""
        raise NotImplementedError
