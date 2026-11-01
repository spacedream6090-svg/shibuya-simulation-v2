"""engine.events.body — 体の出来事を出来事の記録(1-3)に書く口(第 2 期 2-3・腕 ``--memory-store events`` のランだけ)。

計画 2-3(10g の前の配線)・1-6 の記録 m0/README.md §5(体の出来事が記録に無い=記憶の器の目印の先が 100% 仮の行)。
記憶の書き手(``engine.memory.MemoryLayer``)が書く体の出来事(行為の成否・移動の到着・会話の始まりと番・顕著行為への気づき・
強い看板の初見)と、会話の終わり(会話の系の締め)を、``Event`` 1 行ずつ ``EventLog.append`` に通す。書く口は
:meth:`BodyEventLink.write`(記憶の行の配列 → 出来事の行の配列)と :meth:`BodyEventLink.conversation_end`(会話の終わり)の
2 つの入口で、どちらも 1 つの組み立て :meth:`BodyEventLink._event` を通る(=口は 1 つ)。

出来事の形(5W1H・**未リサーチ(expedient)**=親の仮採用の候補・記録 md23/README.md)
    - ``who``=体・``whom``=相手(会話・手伝い・会話の始まりと終わり・無ければ ``None``)。
    - ``what``: 行為の成否・移動の到着・会話の番=行為 12 語(記憶の種類 → 語彙 v3 の語=:data:`KIND_ACT_WORD`・会話の番は
      ``行為:会話``)・会話の始まり=``行為:会話の始まり``・会話の終わり=``行為:会話の終わり``・気づき=``知覚:気づき``・
      強い看板の初見=``道具:看板``(1-7 の「看板を読んだ」と同じ語と同じ欄=作り物の印 ``signboard:synthetic``)。
    - ``how_much``: 行為の語の行だけ結果の番号(``ResultCode``・0=成功)。ほかは ``None``。
    - ``where``: 記憶の対象が POI(0 以上)なら ``("poi", 対象)``・ほかは体のセル ``("cell", セル)``(無ければ ``None``)。
      移動の失敗の行き先のセル(記憶の対象=場所の符号)は出来事に載らない(記憶の器の中身の写しに残る)。
    - ``via``: 会話の語(会話・会話の始まり・会話の終わり)は ``対面``・ほかは ``無し``。
    - 原因(CP12=3 種類だけ): 行為の成否と会話の始まりは、**この刻みに適用した判断の呼**があればその呼
      ``LlmCall(call_id)``(テープの call_id と同じ値)・無ければ ``Process("resolve")``(行為の解決=エンジンの続き)と
      ``Process("conversation")``(会話の門)。会話の番は発話の呼 ``LlmCall(call_id)``。移動の到着は ``Process("resolve")``。
      気づきと看板は ``Process("perception")``(System 1 の知覚=1-7 と同じ)。会話の終わりは ``Process("conversation")``。
    - 1-7 の腕(``SHIBUYA_TOOL_EVENTS``)も立っているランでは、看板の初見は 1-7 の口が同じ刻みに書いた行を目印にする
      (同じ読みを 2 行にしない=:meth:`EventLog.find`)。見つからなければこの口が書く。

約束: 記録は結果を変えない(状態台帳の行 ``E``=軸 1 diag・軸 2 discardable)。既定の腕(``--memory-store mem``)では作らない
(記録も記憶も 1 バイトも変わらない)。書く系は memory(この刻みの出来事)・decide と llm_receive(会話の番)・conversation
(会話の終わり)=``writes.paths`` の ``E:events.*``。

逐次ループ宣言: :meth:`BodyEventLink.write` は行の数ぶん(``EventLog.append`` を 1 行ずつ=記憶が書く出来事の数=5,000 体の
1 日で約 7 万行)。:meth:`BodyEventLink.conversation_end` は閉じたセッションの参加者の数ぶん。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

import numpy as np

from shibuya.engine.events import vocab as V
from shibuya.engine.events.log import Event, EventLog, LlmCall, Process
from shibuya.engine.tools.record import SIGNBOARD_CAUSE, SIGNBOARD_ORIGIN, SIGNBOARD_WHAT

__all__ = [
    "SRC_ACT", "SRC_ARRIVE", "SRC_TALK_OPEN", "SRC_TURN", "SRC_NOTICE", "SRC_SIGNAGE", "SOURCES",
    "KIND_ACT_WORD", "WHAT_TALK_OPEN", "WHAT_TALK_END", "WHAT_NOTICE", "WHAT_SIGNAGE", "ACT_FAMILY_WORDS",
    "BodyEventLink", "kind_of_what",
]

#: 記憶の書き手の出どころ(どの書き手の行か)。
SRC_ACT: Final[int] = 0        # (a) 行為の成否(その刻みに結果が書かれた体)
SRC_ARRIVE: Final[int] = 1     # (a′) 移動の到着(エンジンの続き)
SRC_TALK_OPEN: Final[int] = 2  # (b) 会話の始まり(開いたセッションの参加者・3 人目の参加)
SRC_TURN: Final[int] = 3       # 会話の番(発話ごとの会話の行)
SRC_NOTICE: Final[int] = 4     # (c) 顕著行為への気づき
SRC_SIGNAGE: Final[int] = 5    # (d) 強い看板の初見
SOURCES: Final[tuple[str, ...]] = ("act", "arrive", "talk_open", "turn", "notice", "signage")

#: 記憶の種類(``engine.memory.EVENT_KINDS`` の番号)→ 行為の語(語彙 v3=``vocab.ACT_WORDS``)。試験が両方の表と突き合わせる。
KIND_ACT_WORD: Final[Mapping[int, str]] = MappingProxyType({
    1: "購入", 2: "食事", 3: "並ぶ", 4: "移動", 5: "乗車", 6: "就寝", 7: "会話", 8: "通報", 9: "手伝い",
})
_KIND_NOTICE: Final[int] = 10
_KIND_SIGNAGE: Final[int] = 11
_KIND_TALK: Final[int] = 7
WHAT_TALK_OPEN: Final[str] = V.word(V.FAMILY_ACT, V.CONVERSATION_WORDS[0])
WHAT_TALK_END: Final[str] = V.word(V.FAMILY_ACT, V.CONVERSATION_WORDS[1])
WHAT_NOTICE: Final[str] = V.word(V.FAMILY_PERCEPT, V.PERCEPT_WORDS[0])
WHAT_SIGNAGE: Final[str] = SIGNBOARD_WHAT
#: 行為の語の行(``how_much``=結果の番号)。
ACT_FAMILY_WORDS: Final[frozenset[str]] = frozenset(V.word(V.FAMILY_ACT, w) for w in KIND_ACT_WORD.values())
_WHAT_OF_KIND: Final[Mapping[int, str]] = MappingProxyType(
    {k: V.word(V.FAMILY_ACT, w) for k, w in KIND_ACT_WORD.items()})
_TALK_WORDS: Final[frozenset[str]] = frozenset({_WHAT_OF_KIND[_KIND_TALK], WHAT_TALK_OPEN, WHAT_TALK_END})
#: 原因の名(既定の過程)。
_P_RESOLVE: Final[Process] = Process("resolve")
_P_CONV: Final[Process] = Process("conversation")
_VIA_FACE: Final[str] = V.VIA_WORDS[0]


def kind_of_what(what_code: int) -> int:
    """出来事の語のコード → 記憶の種類(記憶の器の中身の写像の検査=``MemoryStore.remember``)。表の外は ``0``。"""
    w = V.VOCAB[int(what_code)]
    if w in (WHAT_TALK_OPEN, WHAT_TALK_END):
        return _KIND_TALK
    if w == WHAT_NOTICE:
        return _KIND_NOTICE
    if w == WHAT_SIGNAGE:
        return _KIND_SIGNAGE
    for k, ww in _WHAT_OF_KIND.items():
        if ww == w:
            return int(k)
    return 0


class BodyEventLink:
    """体の出来事の口(記憶の器が持つ=``MemoryStore.body_events``・組み立てが腕のランだけ作る)。

    Args:
        log: 出来事の記録。
        signboard_reads: 1-7 の「看板を読んだ」口が立っているランか(真なら看板の初見はその行を目印にする)。
    """

    __slots__ = ("log", "signboard_reads")

    def __init__(self, log: EventLog, *, signboard_reads: bool = False) -> None:
        if type(log) is not EventLog:
            raise TypeError("BodyEventLink は EventLog に書く")
        self.log = log
        self.signboard_reads = bool(signboard_reads)

    def __setattr__(self, name: str, value: Any) -> None:
        # 〔2-3 の検収 L4〕欄は組み立ての 1 回だけ置ける(記録の付け替えで別の記録へ書く抜け道を閉じる)
        if not hasattr(self, name):
            object.__setattr__(self, name, value)
            return
        raise AttributeError(f"体の出来事の口の欄 {name} は付け替えられない")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"体の出来事の口の欄 {name} は消せない")

    @property
    def enabled(self) -> bool:
        return bool(self.log.enabled)

    # ------------------------------------------------------------------ 組み立て(口は 1 つ)
    def _event(self, t: int, who: int, what: str, whom: int, where: tuple[str, int] | None, how_much: int | None,
               cause: Any) -> Event:
        if what == WHAT_SIGNAGE:
            return Event(t_ns=t, who=who, what=what, where=where, via=V.VIA_NONE, received_ns=t, read_ns=t,
                         origin=SIGNBOARD_ORIGIN, cause=SIGNBOARD_CAUSE)
        return Event(t_ns=t, who=who, what=what, whom=None if whom < 0 else whom, where=where, how_much=how_much,
                     via=_VIA_FACE if what in _TALK_WORDS else V.VIA_NONE, cause=cause)

    @staticmethod
    def _what(src: int, kind: int) -> str:
        if src == SRC_TALK_OPEN:
            return WHAT_TALK_OPEN
        if src == SRC_NOTICE:
            return WHAT_NOTICE
        if src == SRC_SIGNAGE:
            return WHAT_SIGNAGE
        w = _WHAT_OF_KIND.get(int(kind))
        if w is None:
            raise ValueError(f"体の出来事の種類が行為の語の表の外: 種類 {kind}・出どころ {SOURCES[src]}")
        return w

    @staticmethod
    def _cause(src: int, call_id: Any) -> Any:
        cid = "" if call_id is None else str(call_id)
        if src in (SRC_NOTICE, SRC_SIGNAGE):
            return SIGNBOARD_CAUSE  # 知覚(System 1)=Process("perception")
        if src == SRC_ARRIVE:
            return _P_RESOLVE
        if cid.strip():
            return LlmCall(cid)
        return _P_CONV if src in (SRC_TALK_OPEN, SRC_TURN) else _P_RESOLVE

    # ------------------------------------------------------------------ 入口 1: 記憶の行の配列 → 出来事の行
    def write(self, who: np.ndarray, kind: np.ndarray, partner: np.ndarray, obj: np.ndarray, result: np.ndarray,
              cell: np.ndarray, src: np.ndarray, call_ids: Sequence[Any] | None = None) -> tuple[np.ndarray, np.ndarray]:
        """記憶が書く体の出来事(入力の並び)を 1 行ずつ書き、id の 2 列 ``(t_ns, seq)`` を返す(時刻は記録の時計=刻みの頭)。

        記録が off のランでは呼ばない(呼び手が ``enabled`` を見る)。書けなかった行があれば ``RuntimeError``(記憶の器の目印は
        記録にある出来事だけ)。
        """
        m = int(np.asarray(who).size)
        t = int(self.log.now_ns)
        ts = np.full(m, t, dtype=np.int64)
        seqs = np.full(m, -1, dtype=np.int64)
        w_, k_, p_, o_, r_, c_, s_ = (np.asarray(x, dtype=np.int64).ravel() for x in
                                      (who, kind, partner, obj, result, cell, src))
        for j in range(m):  # 逐次ループ宣言: 記憶が書く出来事の数ぶん
            sj = int(s_[j])
            what = self._what(sj, int(k_[j]))
            o, c = int(o_[j]), int(c_[j])
            where = ("poi", o) if o >= 0 else (("cell", c) if c >= 0 else None)
            if sj == SRC_SIGNAGE and self.signboard_reads:
                got = self.log.find(t, int(w_[j]), WHAT_SIGNAGE, where)
                if got >= 0:
                    seqs[j] = got
                    continue
            how = int(r_[j]) if what in ACT_FAMILY_WORDS else None
            eid = self.log.append(self._event(t, int(w_[j]), what, int(p_[j]), where, how,
                                              self._cause(sj, None if call_ids is None else call_ids[j])))
            if eid is None:
                raise RuntimeError("体の出来事を記録に書けなかった(記録が off のランでは呼ばない)")
            seqs[j] = int(eid[1])
        return ts, seqs

    # ------------------------------------------------------------------ 入口 2: 会話の終わり
    def conversation_end(self, sessions: Sequence[Any], cell: np.ndarray) -> int:
        """この刻みに閉じたセッション(``ConversationManager.step`` の戻り)の参加者ごとに ``行為:会話の終わり`` を 1 行
        (相手=ほかの参加者の最初・場所=セッションのセル)→ 書いた行の数。"""
        if not self.log.enabled:
            return 0
        t = int(self.log.now_ns)
        n = 0
        for s in sessions:  # 逐次ループ宣言: 閉じたセッションの数 × 参加者(≤ 3)
            ps = [int(p) for p in s.participants]
            sc = int(getattr(s, "cell", -1))
            for p in ps:
                other = next((q for q in ps if q != p), -1)
                c = sc if sc >= 0 else (int(cell[p]) if 0 <= p < len(cell) else -1)
                eid = self.log.append(self._event(t, p, WHAT_TALK_END, other, ("cell", c) if c >= 0 else None, None,
                                                  _P_CONV))
                n += int(eid is not None)
        return n
