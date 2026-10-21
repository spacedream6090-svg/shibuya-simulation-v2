"""engine.calendar2.recall — 頭の中の予定の思い出し(第 6 期 6-2 カレンダー 2・CA3「頭の中だけの予定もエンジンは保管し、本人には
記憶で思い出せたときだけ見せる」・AT1「頭の中=記憶で思い出せたとき」)。

形(記憶の強さは System 1 の数=決定 10-12 §4-6 MR-0・LLM には見せない): 頭の中の行は記憶の痕跡 ``trace``=``[回数 n,
最初の時刻, 直近の時刻 k 個]`` を持ち、強さ ``A = B + W_IMPORTANCE × 重要度`` の ``B`` は記憶 M1 の式(ACT-R の折衷形・秒・
``engine.memory_m1.base_level``=同じ関数)・忘れる速さ ``d = D_ACTR × 人ごとの倍率``(MR8=``memory_m1.forgetting_scale``=同じ
鍵の同じ値)・境目 ``τ`` は M1 の仮の値(``tau_from_m0(RECALL_TAU)``)。思い出す=``A ≥ τ``・目の前の手がかり(約束の相手が
同じ所に居る)があれば ``A + W_CUE ≥ τ``(MR4 の見覚えの形)。思い出した回は痕跡に 1 回足す(想起の練習)。

**読む側は記憶の腕の有無で分岐しない**: 層はいつもこの口を通して見る(記憶の器=1-6 の ``MemoryStore`` の有無・M1 の腕の有無に
依らず同じ式)。器(``--memory-store events``)に予定の行の種類を足すか(器の種類の表の版上げ)は親の判断(記録 §親に確かめて
ほしいこと)=器の無いランの形がこれ。行の目印は ``書いた`` の出来事の id(1-3)を持つ(MR11 (b) の「記憶の行は出来事ログへの
目印」と同じ形)。

**未リサーチ(expedient)**(つなぎの台帳 ``DOC-ca2-head-recall``): 重要度=会話の記憶と同じ値(会話 2+初回 1)・思い出す機会=
本人が考えたとき(判断の呼びのあった刻みの次の刻み=仲裁)・手がかり=約束の相手が同じセルに居る。

逐次ループ宣言: なし(1 行ずつの式=呼び手が行の数ぶん)。
"""

from __future__ import annotations

from typing import Any, Final

import numpy as np

from shibuya.engine import memory_m1 as _M1
from shibuya.engine.memory import IMPORTANCE, IMPORTANCE_MAX, RECALL_TAU

__all__ = ["IMPORTANCE_HEAD", "TAU", "HeadRecall"]

#: 頭の中の予定の重要度(会話の記憶と同じ=会話 2+初回 1)。
IMPORTANCE_HEAD: Final[int] = min(int(IMPORTANCE["talk"]) + int(IMPORTANCE["first_bonus"]), int(IMPORTANCE_MAX))
#: 境目 τ(記憶 M1 の仮の値=M0 の τ から)。
TAU: Final[float] = float(_M1.tau_from_m0(float(RECALL_TAU)))


class HeadRecall:
    """頭の中の予定の思い出しの口(参照=状態を持たない。痕跡は行の ``trace`` に置く)。"""

    def __init__(self, n_agents: int, population_seed: int | str) -> None:
        #: 人ごとの忘れる速さの倍率(MR8=記憶 M1 と同じ鍵の同じ値=母集団の seed と体の番号から作り直せる)。
        self.scale = _M1.forgetting_scale(population_seed, np.arange(int(n_agents), dtype=np.int64))
        self.tau = TAU
        self.k = int(_M1.K_RECENT)

    def new_trace(self, t_ns: int) -> list[int]:
        """書いた回の痕跡 ``[n=1, 最初の時刻, 直近の時刻 k 個]``(空きは ``NO_TIME``)。"""
        return [1, int(t_ns), int(t_ns)] + [int(_M1.NO_TIME)] * (self.k - 1)

    def strength(self, agent: int, trace: Any, now_ns: int) -> float:
        """強さ A(System 1 の数=LLM に見せない)。"""
        n, first, *recent = (int(x) for x in trace)
        d = float(_M1.D_ACTR) * float(self.scale[int(agent)])
        b = _M1.base_level(np.asarray([recent], dtype=np.int64), np.asarray([n]), np.asarray([first]), int(now_ns),
                           np.asarray([d]))
        return float(b[0]) + float(_M1.W_IMPORTANCE) * float(IMPORTANCE_HEAD)

    def recalled(self, agent: int, trace: Any, now_ns: int, *, cue: bool = False) -> bool:
        """思い出したか(``A ≥ τ``・手がかりがあれば ``A + W_CUE ≥ τ``)。"""
        a = self.strength(agent, trace, now_ns)
        return bool(a >= self.tau or (cue and a + float(_M1.W_CUE) >= self.tau))

    def touch(self, trace: Any, t_ns: int) -> list[int]:
        """思い出した回を痕跡に足す(新しい順に 1 つずらす)。同じ時刻に 2 回目は足さない(1 つの時刻に 1 回の符号化=書いた
        すぐ後の同じ刻みの想起で強さを水増ししない)。"""
        n, first, *recent = (int(x) for x in trace)
        if recent and int(recent[0]) == int(t_ns):
            return [n, first, *recent]
        return [n + 1, first, int(t_ns)] + recent[: self.k - 1]
