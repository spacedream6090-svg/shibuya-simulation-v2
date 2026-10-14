"""engine.decision.sources — 候補を 5 つの源から作る(第 1 期 1-8 J0・DM-0)。

正典: 決定 10-12 §4-7 DM-0(候補は設計者の一覧ではなく 5 つの源=本人の経験・周りが示す「できること」・近い予定・今の行動を
続ける・よく考える。並び順は毎回入れ替えて記録する)。口の約束 1-8(候補の源のどれから来たかを記録)。

J0 の作り(結果不変=腕 ``--decision-port port`` でも mock の行為は今と同じ番号):

1. 続ける(``continue``): その版の安全弁の語(語彙 v3 の「なし」・v1/v2 の「待機」=今の過ごし方のまま)。
2. 近い予定(``plan``): 知覚の事実の今の意図(``Percept.intent`` の行為)。
3. 本人の経験(``experience``): 想起した記憶(``Percept.memories``)の種類を行為の語に戻した物(記憶の表の
   ``engine.memory.ACTION_KIND`` の逆=新しい表は作らない)。元の出来事 id(1-6 の器の行で出どころが記録の物)を ``basis`` に。
4. 周りが示すできること(``affordance``): 場所の種類と営業時間と知覚の読みと、1-7 の道具の台帳(道具 → 語の表=今は空)
   から作る(``engine.decision.layer.DecisionLayer.affordance_words``)。
5. よく考える(``deliberate``): 1 つ(行為の語ではない=エンジンは実行しない)。

どの源も出さなかった語彙の語は ``vocab``(つなぎの印=今の道の設計者の一覧)で残す(mock が今と同じ語から引くため)。同じ語を
2 つの源が出したら上の順で先の源の 1 つだけ。並びは 1 → 2 → 3 → 4 → 語彙の残り(語彙の順)→ 5(並べ替えは口の
``present`` が行う)。

逐次ループ宣言(P4): ``build_candidates`` は語彙の語の数(≤ 13)と想起の行の数(≤ 3)ぶん。

expedient(候補の見せ方と源の決め方=判断モデルの評価の段 6-1 で測る)
- 見せ方の文は「語(源の注)」の形(``SOURCE_NOTES``)。候補をメニューでなく頭に浮かんだこととして見せる言い方は R108-7 の空欄
  (評価セットの腕で測る)。
- 続ける=安全弁の語・近い予定=今の意図だけ(カレンダーの予定は 3-1 の後)・同じ語は先の源の 1 つだけ。
"""

from __future__ import annotations

import functools
from types import MappingProxyType
from typing import Any, Callable, Final, Iterable, Mapping, Sequence

from shibuya.engine.decision.port import (
    DELIBERATE_KIND,
    SOURCE_AFFORDANCE,
    SOURCE_CONTINUE,
    SOURCE_DELIBERATE,
    SOURCE_EXPERIENCE,
    SOURCE_PLAN,
    SOURCE_VOCAB,
    Candidate,
    DecisionContext,
)

__all__ = ["SOURCE_NOTES", "DELIBERATE_ID", "build_candidates", "memory_kind_words"]

#: 見せ方の注(源 → 語の後ろの括弧の中)。語彙の残りは注なし。
SOURCE_NOTES: Final[Mapping[str, str]] = MappingProxyType({
    SOURCE_CONTINUE: "このまま続ける",
    SOURCE_PLAN: "予定",
    SOURCE_EXPERIENCE: "前にもした",
    SOURCE_AFFORDANCE: "ここでできる",
})
DELIBERATE_ID: Final[str] = "deliberate"


def memory_kind_words(word_of_code: Mapping[int, str]) -> Mapping[int, str]:
    """記憶の種類 → 行為の語(``engine.memory.ACTION_KIND``=行動コード → 種類 の逆)。"""
    from shibuya.engine.memory import ACTION_KIND

    out: dict[int, str] = {}
    for code, kind in ACTION_KIND.items():
        w = word_of_code.get(int(code))
        if w is not None and int(kind) not in out:
            out[int(kind)] = w
    return MappingProxyType(out)


@functools.lru_cache(maxsize=256)
def _plain(source: str, word: str) -> Candidate:
    """元の出来事の無い候補(凍結=使い回してよい・源と語の組で決まる)。"""
    note = SOURCE_NOTES.get(source)
    text = f"{word}({note})" if note else word
    return Candidate(id=f"{source}:{word}", kind=word, text=text, source=source)


def _cand(source: str, word: str, basis: Iterable[tuple[int, int]] = ()) -> Candidate:
    basis = tuple(basis)
    c = _plain(source, word)
    return c if not basis else Candidate(id=c.id, kind=c.kind, text=c.text, source=c.source, basis=basis)


def _memory_items(percept: Any) -> Sequence[Any]:
    mem = getattr(percept, "memories", None) if percept is not None else None
    return () if mem is None else tuple(mem)


def build_candidates(
    ctx: DecisionContext,
    *,
    vocab: Sequence[str],
    continue_word: str,
    word_of_code: Mapping[int, str],
    kind_words: Mapping[int, str],
    affordance_words: Callable[[DecisionContext, Sequence[str]], Sequence[str]] | None = None,
) -> tuple[Candidate, ...]:
    """5 つの源と語彙の残りから候補の列を作る(作る側は番号を振らない=``present`` が振る)。読むだけ。"""
    vocab = tuple(vocab)
    vset = frozenset(vocab)
    out: list[Candidate] = []
    taken: set[str] = set()

    def take(source: str, word: str, basis: Iterable[tuple[int, int]] = ()) -> None:
        if word in vset and word not in taken:
            taken.add(word)
            out.append(_cand(source, word, basis))

    take(SOURCE_CONTINUE, continue_word)
    p = ctx.percept
    intent = getattr(p, "intent", None) if p is not None else None
    if intent is not None:
        w = word_of_code.get(int(intent.action))
        if w is not None:
            take(SOURCE_PLAN, w)
    by_word: dict[str, list[tuple[int, int]]] = {}
    order: list[str] = []
    for it in _memory_items(p):  # 逐次ループ宣言: 想起の行の数(≤ 3)
        w = kind_words.get(int(getattr(it, "kind", -1)))
        if w is None:
            continue
        if w not in by_word:
            by_word[w] = []
            order.append(w)
        eid = getattr(it, "event_id", None)
        if eid is not None and getattr(it, "origin", None) == "log":
            by_word[w].append((int(eid[0]), int(eid[1])))
    for w in order:
        take(SOURCE_EXPERIENCE, w, by_word[w])
    if affordance_words is not None:
        for w in affordance_words(ctx, vocab):
            take(SOURCE_AFFORDANCE, w)
    for w in vocab:  # 逐次ループ宣言: 語彙の語の数
        take(SOURCE_VOCAB, w)
    out.append(_DELIBERATE)
    return tuple(out)


_DELIBERATE: Final[Candidate] = Candidate(id=DELIBERATE_ID, kind=DELIBERATE_KIND, text=DELIBERATE_KIND,
                                          source=SOURCE_DELIBERATE)
