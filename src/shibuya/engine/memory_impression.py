"""engine.memory_impression — 記憶 M3 の器(印象の履歴と、本人が寝たときの書き直し・第 6 期 6-5)。

正: 決定 10-12 §4-6 MR3 (e)(会話の直後に短く履歴へ足し、本人が寝たときに今の印象を書き直す。履歴は足すだけで、古い要約も
残す。きっかけは実文の会話と、その人が知覚にある状態で LLM が呼ばれたとき。同席しただけなら印象は書かない)・MR13 (c)(昼の
LLM の結論はその場で意味の記憶に足す。まとめ直しと印象の書き直しは本人が寝たとき。出力長の上限 128 はやめ、中身の量で決めて
測る)・MR2 問い 3(印象に埋め込みを付ける)・MR11(根拠は住人に明示させない)。回答 10-12 の 6-2: M3 は GPU が要る=**器だけ**。

形(**器だけ=本段ではランに結線しない**。LLM の呼びは口の引数=試験は mock)
- :class:`ImpressionBook`: 体と相手の組ごとの履歴(:class:`ImpressionEntry` の列・足すだけ)と、体ごとの意味の記憶
  (昼の結論の列・足すだけ)。
  - :meth:`after_conversation`: 会話の直後に短く足す(原因=その会話の番の LLM の呼び ``LlmCall``・同席だけの書きは受けない)。
  - :meth:`on_sleep`: 本人が寝たときに、前の書き直しの後に足した履歴のある相手ごとに書き直しの口(``rewrite``=LLM の呼び)を
    呼び、書き直した印象を **足す**(古い要約も残る)。
  - :meth:`add_conclusion`: 昼の LLM の結論を意味の記憶に足す(原因つき)。
  - :meth:`current`: 今の印象(最後の書き直し・無ければ最後の会話の直後の文)。
- 文の長さは切らない(MR13=上限 128 をやめ中身の量で決めて測る=計器 ``chars``)。
- 印象の埋め込み(MR2 問い 3)は ``embed`` の口(``memory_embed.CueState.embed_rows`` と同じ形)を渡したときだけ。

**未リサーチ(expedient)**: 履歴の形(相手ごとの列)・書き直しの単位(前の書き直しの後に足した相手だけ)・意味の記憶の形
(体ごとの文の列)。

逐次ループ宣言(P4): ``on_sleep`` は寝た体の相手の数ぶん(LLM の呼びの数=書き直しの数)。ほかは 1 件ずつ(会話の番の数)。
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Final, NamedTuple, Sequence

from shibuya.engine.events.log import LlmCall

__all__ = ["KIND_AFTER_TALK", "KIND_SLEEP_REWRITE", "KINDS", "ImpressionEntry", "ImpressionBook"]

#: 履歴の種類(会話の直後の追記・寝たときの書き直し)。
KIND_AFTER_TALK: Final[str] = "after_talk"
KIND_SLEEP_REWRITE: Final[str] = "sleep_rewrite"
KINDS: Final[tuple[str, ...]] = (KIND_AFTER_TALK, KIND_SLEEP_REWRITE)


class ImpressionEntry(NamedTuple):
    """履歴の 1 件(足すだけ)。``cause`` は LLM の呼び(原因つき)。"""

    t_ns: int
    kind: str
    text: str
    cause: LlmCall


def _check_cause(cause: Any) -> LlmCall:
    if not isinstance(cause, LlmCall):
        raise TypeError("印象を書くのは LLM の呼び(原因 LlmCall)だけ=同席だけ・エンジンの規則では書かない(MR3)")
    return cause


class ImpressionBook:
    """印象の履歴と意味の記憶の器(M3)。書く口は :meth:`after_conversation`・:meth:`on_sleep`・:meth:`add_conclusion`。"""

    __slots__ = ("_hist", "_since", "_semantic", "_stats", "_embed")

    def __init__(self, *, embed: Callable[[Sequence[tuple[int, int]], Sequence[str]], None] | None = None) -> None:
        #: (体, 相手) → 履歴(足すだけ)。
        self._hist: dict[tuple[int, int], list[ImpressionEntry]] = {}
        #: 体 → 前の書き直しの後に会話の直後の追記があった相手(寝たときに書き直す相手)。
        self._since: dict[int, list[int]] = {}
        #: 体 → 意味の記憶(昼の結論の列・足すだけ)。
        self._semantic: dict[int, list[ImpressionEntry]] = {}
        self._stats: Counter = Counter()
        #: 印象の埋め込みの口(MR2 問い 3・任意)。
        self._embed = embed

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, name):
            raise AttributeError(f"印象の器の欄 {name} は付け替えられない")
        object.__setattr__(self, name, value)

    # ------------------------------------------------------------------ 書く口
    def after_conversation(self, agent: int, partner: int, text: str, t_ns: int, cause: Any) -> ImpressionEntry:
        """会話の直後に短く履歴へ足す(実文の会話の LLM の呼びが原因)。文が空なら ``ValueError``。"""
        c = _check_cause(cause)
        t = str(text or "").strip()
        if not t:
            raise ValueError("印象の文が空")
        if int(agent) == int(partner):
            raise ValueError("自分への印象は書かない")
        e = ImpressionEntry(int(t_ns), KIND_AFTER_TALK, t, c)
        self._hist.setdefault((int(agent), int(partner)), []).append(e)
        lst = self._since.setdefault(int(agent), [])
        if int(partner) not in lst:
            lst.append(int(partner))
        self._stats["after_talk"] += 1
        self._stats["chars"] += len(t)
        if self._embed is not None:
            self._embed([(int(agent), int(partner))], [t])
        return e

    def on_sleep(self, agent: int, t_ns: int,
                 rewrite: Callable[[int, int, tuple[ImpressionEntry, ...]], tuple[str, Any]]) -> list[ImpressionEntry]:
        """本人が寝たときの書き直し: 前の書き直しの後に追記のあった相手ごとに ``rewrite(体, 相手, 履歴)`` →
        ``(新しい印象の文, LlmCall)`` を呼び、書き直しを履歴に**足す**(古い要約は残る)→ 足した件。"""
        out: list[ImpressionEntry] = []
        for p in self._since.pop(int(agent), []):  # 逐次ループ宣言: 書き直す相手の数ぶん(=LLM の呼びの数)
            hist = tuple(self._hist.get((int(agent), p), ()))
            text, cause = rewrite(int(agent), p, hist)
            c = _check_cause(cause)
            t = str(text or "").strip()
            if not t:
                self._stats["sleep_rewrite_empty"] += 1
                continue
            e = ImpressionEntry(int(t_ns), KIND_SLEEP_REWRITE, t, c)
            self._hist[(int(agent), p)].append(e)
            out.append(e)
            self._stats["sleep_rewrite"] += 1
            self._stats["chars"] += len(t)
            if self._embed is not None:
                self._embed([(int(agent), p)], [t])
        return out

    def add_conclusion(self, agent: int, text: str, t_ns: int, cause: Any) -> ImpressionEntry:
        """昼の LLM の結論をその場で意味の記憶に足す(MR13 (c))。"""
        c = _check_cause(cause)
        t = str(text or "").strip()
        if not t:
            raise ValueError("結論の文が空")
        e = ImpressionEntry(int(t_ns), "conclusion", t, c)
        self._semantic.setdefault(int(agent), []).append(e)
        self._stats["conclusions"] += 1
        self._stats["chars"] += len(t)
        return e

    # ------------------------------------------------------------------ 読み口
    def history(self, agent: int, partner: int) -> tuple[ImpressionEntry, ...]:
        return tuple(self._hist.get((int(agent), int(partner)), ()))

    def current(self, agent: int, partner: int) -> str | None:
        """今の印象(最後の書き直し・無ければ最後の会話の直後の文・無ければ ``None``)。"""
        h = self._hist.get((int(agent), int(partner)), [])
        for e in reversed(h):  # 逐次ループ宣言: 履歴の長さぶん(後ろから)
            if e.kind == KIND_SLEEP_REWRITE:
                return e.text
        return h[-1].text if h else None

    def semantic(self, agent: int) -> tuple[ImpressionEntry, ...]:
        return tuple(self._semantic.get(int(agent), ()))

    def pending(self, agent: int) -> tuple[int, ...]:
        """寝たときに書き直す相手(前の書き直しの後に追記があった相手)。"""
        return tuple(self._since.get(int(agent), ()))

    def summary(self) -> dict[str, Any]:
        return {"pairs": len(self._hist), "agents_semantic": len(self._semantic),
                "entries": int(sum(len(v) for v in self._hist.values())), "counts": dict(sorted(self._stats.items()))}
