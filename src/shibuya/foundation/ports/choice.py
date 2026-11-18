"""foundation.ports.choice — 割る段で ``engine/chooser.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``mind/judge/chooser.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Final, Protocol, runtime_checkable
import numpy as np
from shibuya.foundation.rng import stream

__all__ = [
    "CHOOSER_RNG_DOMAIN", "ChoiceContext", "Chooser", "draw_index", "entropy_bits",
]


#: 抽選の乱数の用途名(``core.rng.stream`` の domain)。
CHOOSER_RNG_DOMAIN: Final[str] = "engine.chooser"


@dataclass(frozen=True)
class ChoiceContext:
    """1 回の選択の文脈(選び手が読んでよいものだけ)。

    Attributes:
        agent_id / tick / cell / node: 選ぶ体と時刻・現在セル・現在ノード。
        action_code: 行為コード(購入/食事/並ぶ)。
        target_kind: 対象の種類(``"named"``/``"category"``/``"none"``)。
        target_text: 「対象」欄の文字列(NFKC 済み・無ければ ``""``)。
        hunger: 空腹の段(``registry.hunger``)。D-118 energy の語が入ればここを差し替える。
        visibility: 候補ごとの可視の強さ(W8 の視点数)。候補と同じ長さ。
        distance_m: 候補ごとの距離[m](W3 ``cell_dist``・同じセルは 0)。候補と同じ長さ。
        price: 候補ごとの価格[円](5b・``world.pois.price``)。空なら予算を見ない。
        money: 体の所持金[円](5b)。``-1``=見ない。
        visits: 候補ごとの訪問回数(5b・親しみの表 ``fam_visits``)。空=表が無い(習慣の項を飛ばす)。
        food: 食事の選択か(5b・願望水準を空腹の語で動かすのは食事だけ=宣言)。
    """

    agent_id: int
    tick: int
    cell: int
    node: int
    action_code: int
    target_kind: str
    target_text: str
    hunger: int
    visibility: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))
    distance_m: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.float64))
    price: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))
    money: int = -1
    visits: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))
    food: bool = False


@runtime_checkable
class Chooser(Protocol):
    """選択器の口。``probs`` は候補と同じ長さの確率(和 1・候補が空なら空)を返す。"""

    name: str

    def probs(self, candidates: np.ndarray, context: ChoiceContext) -> np.ndarray: ...


def draw_index(p: np.ndarray, seed: int | str, tick: int, agent_id: int) -> int:
    """確率 ``p`` から 1 つ引く(``core.rng.stream(seed, "engine.chooser", tick, agent_id)``)。

    one-hot でも同じ経路を通す。``p`` が空なら ``-1``。

    Example:
        >>> draw_index(np.array([0.0, 1.0, 0.0]), 1, 10, 7)
        1
        >>> draw_index(np.zeros(0), 1, 10, 7)
        -1
    """
    q = np.asarray(p, dtype=np.float64)
    if q.size == 0:
        return -1
    total = float(q.sum())
    if not (total > 0.0) or not math.isfinite(total):
        raise ValueError("chooser の確率の和が正でない")
    u = float(stream(seed, CHOOSER_RNG_DOMAIN, int(tick), int(agent_id)).random()) * total
    cum = np.cumsum(q)
    k = int(np.searchsorted(cum, u, side="right"))
    if k >= q.size:  # 丸めで末尾を越えたら、確率が正の最後の要素
        k = int(np.flatnonzero(q > 0)[-1])
    return k


def entropy_bits(p: np.ndarray) -> float:
    """分布のエントロピー[bit](one-hot なら 0)。"""
    q = np.asarray(p, dtype=np.float64)
    q = q[q > 0]
    if q.size == 0:
        return 0.0
    q = q / q.sum()
    return float(-(q * np.log2(q)).sum())
