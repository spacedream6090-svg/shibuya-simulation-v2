"""engine.memory_trace — 注意を向けずに見ていた人の浅い痕跡(第 6 期 6-5・MR6 の後段「注意を向けずに見ていた人が話題に出たとき」)。

正: 決定 10-12 §4-6(1. 注意を向けなかった知覚も浅い痕跡として残る。保存はせず、手がかりが来たときに共有の出来事ログから
「その時、視野のどこに、どれだけいたか」を組み立てる/2. 話し手の発話に、話し手が指した相手の ID を見えない欄で付け、聞き手の
記憶を引く手がかりにする=``perception.facts.Percept.heard_referents``/3. 聞き手に見せるのは、注意を向けた記憶なら普通に、
浅い痕跡だけなら「見たような気もする」、何も無ければ何も無し/4. 会話そのものは「A から聞いた」の出どころつきの新しい記憶/
5. LLM が覚えていないのに話を合わせた割合を計器で数える)・MR11(記憶の行は出来事ログへの目印だけ)。回答 10-12 の 6-2: M5
(同席と浅い痕跡)は GPU 要・目の向きと空間の段が先=**口だけ**。

形(**読むだけ・状態を持たない**)
- :func:`shallow_trace`: 共有の出来事ログ(``engine.events.log.EventLog``)から、手がかりの人 ``target`` と聞き手 ``viewer`` の
  行を時刻の窓で引き、同じ場所(``where``)に近い時刻(``co_window_ns``)で居た回を組み立てる(:class:`TraceView`=回数・最初と
  最後の時刻・場所)。ログに居場所が載るのは体の出来事の腕(``--memory-store events``=2-3 の腕 a)のランだけ=それ以外は空。
  視野(目の向き)は空間の段の後=今は「同じ場所に近い時刻」で近似(expedient)。
- :func:`trace_word`: 見せる言葉(注意を向けた記憶=空文字=普通に描く/浅い痕跡だけ=「見たような気もする」/何も無い=空文字)。
- :func:`played_along_share`: 計器「LLM が覚えていないのに話を合わせた割合」(行=(聞き手の記憶に指された相手があったか,
  聞き手が話を合わせたか)・値は実 LLM の後=今のランでは呼ばない)。

**未リサーチ(expedient)**: 同じ場所の近い時刻の窓(既定 1 刻み=60 秒)・場所の同一視(``where`` の (種類, id) が同じ)。

逐次ループ宣言(P4): ``shallow_trace`` は窓の中の 2 人の行の数ぶん(行を ``Event`` に戻す=診断と手がかりの時だけ)。
"""

from __future__ import annotations

from typing import Any, Final, Iterable, NamedTuple

import numpy as np

from shibuya.core.time_consts import NS_PER_STEP
from shibuya.engine.memory_m1 import WORD_TRACE

__all__ = ["CO_WINDOW_NS", "TraceView", "shallow_trace", "trace_word", "played_along_share"]

#: 同じ場所の「近い時刻」の窓(expedient=1 刻み)。
CO_WINDOW_NS: Final[int] = int(NS_PER_STEP)


class TraceView(NamedTuple):
    """浅い痕跡(保存しない=手がかりが来たときに組み立てる)。``places`` は ``(場所の種類, id, 回数)`` の組。"""

    seen: int
    first_ns: int
    last_ns: int
    places: tuple[tuple[str, int, int], ...]


_EMPTY: Final[TraceView] = TraceView(0, -1, -1, ())


def shallow_trace(log: Any, viewer: int, target: int, *, t0_ns: int, t1_ns: int,
                  co_window_ns: int = CO_WINDOW_NS) -> TraceView:
    """出来事の記録から ``viewer`` が ``target`` を同じ場所の近い時刻で見ていた回を組み立てる(読むだけ)。"""
    if log is None or len(log) == 0:
        return _EMPTY
    t, _seq = log.ids()
    pos = np.flatnonzero((t >= int(t0_ns)) & (t <= int(t1_ns)))
    if pos.size == 0:
        return _EMPTY
    who, _what = log.who_what(pos)
    who = who.astype(np.int64)
    vp = pos[who == int(viewer)]
    tp = pos[who == int(target)]
    if vp.size == 0 or tp.size == 0:
        return _EMPTY

    def rows(ps: np.ndarray) -> list[tuple[int, tuple[str, int]]]:
        out = []
        for i in ps.tolist():  # 逐次ループ宣言: 窓の中の 2 人の行の数ぶん
            ev = log.event(int(i))
            if ev.where is not None:
                out.append((int(ev.t_ns), (str(ev.where[0]), int(ev.where[1]))))
        return out

    v_rows = rows(vp)
    hits: dict[tuple[str, int], int] = {}
    times: list[int] = []
    for tt, wh in rows(tp):  # 逐次ループ宣言: 手がかりの人の行の数ぶん × 聞き手の行
        if any(w2 == wh and abs(t2 - tt) <= int(co_window_ns) for t2, w2 in v_rows):
            hits[wh] = hits.get(wh, 0) + 1
            times.append(tt)
    if not times:
        return _EMPTY
    places = tuple((k[0], k[1], c) for k, c in sorted(hits.items()))
    return TraceView(len(times), min(times), max(times), places)


def trace_word(attended: bool, trace: TraceView) -> str:
    """聞き手に見せる言葉: 注意を向けた記憶=空文字(普通に描く)・浅い痕跡だけ=「見たような気もする」・何も無い=空文字。"""
    if attended:
        return ""
    return WORD_TRACE if int(trace.seen) > 0 else ""


def played_along_share(rows: Iterable[tuple[bool, bool]]) -> float | None:
    """「LLM が覚えていないのに話を合わせた割合」=聞き手の記憶に指された相手が無い行のうち、話を合わせた行の割合
    (無い行が 0 なら ``None``)。値は実 LLM の後(話を合わせたかの判定は発話の文の分析=MR11 のラン後の突き合わせ)。"""
    missing = [bool(engaged) for had, engaged in rows if not bool(had)]
    if not missing:
        return None
    return round(sum(missing) / len(missing), 6)
