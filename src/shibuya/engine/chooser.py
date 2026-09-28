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

**5 段目 5b(D-119 L3/L8・第292)** :class:`ClassicalChooser`(``--chooser classical``)=古典的選択
モデルの店選び(DestinationChooser): (i) **習慣**=親しみの表(``--familiarity on`` のときだけ・off なら
この項は飛ばす=宣言)で訪問回数が最大の候補があれば確率 ``p_h`` でそこ (ii) **満足化**=願望水準
(空腹の語で動く・Simon 1956)を満たす候補に可視順の揺らぎ ``P(k) ∝ exp(−rank_k/τ)``。距離減衰は
入れない(rank は可視順=距離と相関する=宣言)。分布を返し、抽選は既存の :func:`draw_index`。

逐次ループ宣言(P4): なし(1 回の選択は候補数ぶんの配列演算)。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Final, Protocol, runtime_checkable

import numpy as np

from shibuya.core.rng import stream

__all__ = [
    "HABIT_P",
    "RANK_TAU",
    "ClassicalChooser",
    "hunger_stage_of",
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

#: 選び手の名前(CLI ``--chooser``・manifest ``chooser``)。``classical``=D-119 の DestinationChooser(5b)。
CHOOSER_NAMES: Final[tuple[str, ...]] = ("nearest", "classical")
#: 習慣の確率 p_h(宣言・expedient・感度 0.25/0.75・Rhee & Bell の「主店に約 3/4」を上限の目安)。
HABIT_P: Final[float] = 0.5
#: 満足化の走査順の揺らぎ τ(宣言・expedient・感度 0.5/2.0・τ→0 で one-hot・τ→∞ で一様)。
RANK_TAU: Final[float] = 1.0
#: 内受容の段の刻み(``engine.change_detect.INTERO_UP_EDGES`` と同値=空腹の語の段 0〜3 を写しから読む)。
_INTERO_UP_EDGES: Final[tuple[int, ...]] = (4, 7, 9)
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


def hunger_stage_of(hunger: int) -> int:
    """``hunger`` → 空腹の語の段 0〜3(energy は写し 1/5/8/10・v1 は 0〜10 を同じ刻みで読む=宣言)。"""
    return sum(1 for e in _INTERO_UP_EDGES if int(hunger) >= e)


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


class ClassicalChooser:
    """D-119 の DestinationChooser(5b・L3 (a)+L8 (a))。分布を返す(one-hot ではない)。

    1. **可視順**: 候補を可視(視点数)の降順 → POI 索引の昇順に並べた順位 rank(0 起点)。
    2. **願望水準**(L8 (α)・Simon 1956 の可変願望水準・宣言): 食事(``context.food``)のとき空腹の語の段で
       とても空腹(3)=条件なし(最初に見えた飲食店)/ 空腹(2)=予算内(価格 ≤ 所持金)/ ふつう(1)・満腹(0)
       =予算内 ∧ カテゴリ一致(候補はカテゴリ語なら既に一致=予算内と同じになる・満腹は食事の門を通らない
       のが本則で、来てしまったらふつうと同じ)。食事以外(購入・並ぶ・移動)は予算内。満たす候補が無ければ
       願望水準を下げて全候補(宣言)。
    3. **走査順の揺らぎ**(L8 (β)): 満たす候補の中の可視順 r(0 起点)に ``exp(−r/τ)``。
    4. **習慣**(L3 (i)): ``context.visits`` が空でなく最大が 1 以上なら、最大の候補(同数は可視順)に
       ``p_h``・満足化に ``1 − p_h``。習慣は願望水準を見ない(宣言)。

    Example:
        >>> ctx = ChoiceContext(0, 0, 0, 0, 24, "none", "", 8,
        ...                     visibility=np.array([5, 9, 1]), distance_m=np.zeros(3),
        ...                     price=np.array([900, 900, 900]), money=5000, food=True)
        >>> p = ClassicalChooser().probs(np.array([40, 12, 7]), ctx)
        >>> [round(float(x), 3) for x in p]
        [0.245, 0.665, 0.09]
    """

    name: str = "classical"

    def __init__(self, p_h: float = HABIT_P, tau: float = RANK_TAU) -> None:
        if not (0.0 <= float(p_h) <= 1.0):
            raise ValueError("p_h は 0.0〜1.0")
        if not (float(tau) > 0.0):
            raise ValueError("tau は正")
        self.p_h = float(p_h)
        self.tau = float(tau)
        #: 計数(manifest ``chooser_stats``): 選択の回数・習慣が効いた回・願望水準を下げた回・段ごとの回数。
        self.stats: dict[str, int] = {}
        #: D-120 7c(決め手の記録): 直前の ``probs`` で習慣の候補だった添字(無ければ −1)。挙動には効かない。
        self.last_habit = -1

    def _count(self, key: str) -> None:
        self.stats[key] = self.stats.get(key, 0) + 1

    def probs(self, candidates: np.ndarray, context: ChoiceContext) -> np.ndarray:
        cand = np.asarray(candidates, dtype=np.int64)
        n = int(cand.size)
        out = np.zeros(n, dtype=np.float64)
        self.last_habit = -1
        if n == 0:
            return out
        vis = np.asarray(context.visibility, dtype=np.int64)
        if vis.size != n:
            vis = np.zeros(n, dtype=np.int64)
        order = np.lexsort((cand, -vis))  # 可視の降順 → 索引
        rank = np.empty(n, dtype=np.int64)
        rank[order] = np.arange(n)
        stage = hunger_stage_of(context.hunger)
        price = np.asarray(context.price, dtype=np.int64)
        budget = (
            price <= int(context.money)
            if (price.size == n and int(context.money) >= 0)
            else np.ones(n, dtype=bool)
        )
        if context.food:
            mask = np.ones(n, dtype=bool) if stage >= 3 else budget
            self._count(f"food_stage:{stage}")
        else:
            mask = budget
        self._count("decisions")
        if not mask.any():
            mask = np.ones(n, dtype=bool)  # 願望水準を下げる(宣言)
            self._count("aspiration_lowered")
        sub = np.flatnonzero(mask)
        r = np.empty(sub.size, dtype=np.float64)
        r[np.argsort(rank[sub], kind="stable")] = np.arange(sub.size, dtype=np.float64)
        w = np.exp(-r / self.tau)
        sat = np.zeros(n, dtype=np.float64)
        sat[sub] = w / w.sum()
        visits = np.asarray(context.visits, dtype=np.int64)
        if visits.size == n and int(visits.max(initial=0)) >= 1 and self.p_h > 0.0:
            best = visits.max()
            hs = np.flatnonzero(visits == best)
            h = int(hs[np.argmin(rank[hs])])
            out[:] = (1.0 - self.p_h) * sat
            out[h] += self.p_h
            self.last_habit = h
            self._count("habit_available")
        else:
            out[:] = sat
        return out


def check_chooser(name: str) -> str:
    """選び手の名前を検査して返す。"""
    n = str(name)
    if n not in CHOOSER_NAMES:
        raise ValueError(f"chooser は {CHOOSER_NAMES} のどれか(いま {name!r})")
    return n


def make_chooser(name: str, *, p_h: float = HABIT_P, tau: float = RANK_TAU) -> Chooser:
    """名前 → 選び手(``classical`` は p_h・τ を取る)。"""
    n = check_chooser(name)
    if n == "nearest":
        return NearestChooser()
    if n == "classical":
        return ClassicalChooser(p_h=p_h, tau=tau)
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
