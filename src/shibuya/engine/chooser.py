"""engine.chooser — 選択器の口 ``Chooser.probs``(段 2a・D-114 (a)・2026-09-28)。

正典: 実装アジェンダ ``docs/design/v2-intent-chooser-implementation-agenda.md`` §1-1/§1-2。
ユーザー決定(09-25〜26 D-114): **エンジンは候補を絞るだけ・選ぶのはエージェント**。選び手は
System 1.5(候補一覧から分布で選ぶ)=この口に差し込む(D-119 の ``classical``・GPU 後の
``logprob`` はここに増える)。ハフ型(魅力度 ÷ 距離^λ)はエンジンに入れない。

契約
- ``Chooser.probs(candidates, context) -> np.ndarray``: 候補(POI 索引の 1 次元配列)と同じ長さの
  確率(和 1)。候補が空なら空。
- 抽選は :func:`draw_index` =``core.rng.stream(seed, "engine.chooser", tick, agent_id)`` の
  決定論。**分布が one-hot でも抽選を通す**(口を同じにする=選び手を差し替えても経路が変わらない)。

既定の選び手 :class:`NearestChooser`(**憲法⑥の宣言つき暫定**=「最寄り」は本来 System 1.5 の
選び手の仕事): 距離(W3 ``cell_dist``)の昇順 → 可視順(W8 の視点数の降順=満足化の「見えている順」)
→ POI 索引 の最初の 1 件に 1.0。同じセル内は距離 0 なので可視順 → POI 索引で決まる。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Final, Protocol, runtime_checkable

import numpy as np

from shibuya.core.rng import stream

__all__ = [
    "CHOOSER_NAMES",
    "DEFAULT_CHOOSER",
    "CHOOSER_RNG_DOMAIN",
    "ChoiceContext",
    "Chooser",
    "NearestChooser",
    "check_chooser",
    "make_chooser",
    "draw_index",
    "entropy_bits",
]

#: 選び手の名前(CLI ``--chooser``・manifest ``chooser``)。D-119 の ``classical`` はここに増える。
CHOOSER_NAMES: Final[tuple[str, ...]] = ("nearest",)
DEFAULT_CHOOSER: Final[str] = CHOOSER_NAMES[0]
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


@runtime_checkable
class Chooser(Protocol):
    """選択器の口。``probs`` は候補と同じ長さの確率(和 1・候補が空なら空)を返す。"""

    name: str

    def probs(self, candidates: np.ndarray, context: ChoiceContext) -> np.ndarray: ...


class NearestChooser:
    """既定の選び手(**憲法⑥の宣言つき暫定**・expedient)。

    距離の昇順 → 可視(視点数)の降順 → POI 索引の昇順 の最初の 1 件に確率 1.0(one-hot)。

    Example:
        >>> ctx = ChoiceContext(0, 0, 0, 0, 3, "none", "", 0,
        ...                     visibility=np.array([5, 9, 9]), distance_m=np.array([0.0, 0.0, 0.0]))
        >>> NearestChooser().probs(np.array([40, 12, 7]), ctx).tolist()
        [0.0, 0.0, 1.0]
    """

    name: str = "nearest"

    def probs(self, candidates: np.ndarray, context: ChoiceContext) -> np.ndarray:
        cand = np.asarray(candidates, dtype=np.int64)
        n = int(cand.size)
        out = np.zeros(n, dtype=np.float64)
        if n == 0:
            return out
        vis = np.asarray(context.visibility, dtype=np.int64)
        dist = np.asarray(context.distance_m, dtype=np.float64)
        if vis.size != n:
            vis = np.zeros(n, dtype=np.int64)
        if dist.size != n:
            dist = np.zeros(n, dtype=np.float64)
        order = np.lexsort((cand, -vis, dist))  # 最後の鍵が主キー: 距離 → 可視(降順)→ 索引
        out[int(order[0])] = 1.0
        return out


def check_chooser(name: str) -> str:
    """選び手の名前を検査して返す。"""
    n = str(name)
    if n not in CHOOSER_NAMES:
        raise ValueError(f"chooser は {CHOOSER_NAMES} のどれか(いま {name!r})")
    return n


def make_chooser(name: str) -> Chooser:
    """名前 → 選び手。"""
    n = check_chooser(name)
    if n == "nearest":
        return NearestChooser()
    raise ValueError(n)  # pragma: no cover - CHOOSER_NAMES と揃える


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
