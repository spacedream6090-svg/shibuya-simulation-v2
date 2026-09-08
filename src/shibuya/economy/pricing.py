"""economy.pricing — 行5 価格形成のエンジン側(内生フロア・クリアリング・Calvo・逸脱比例コスト)。

正典(世界過程設計書 §4 行5 の D-R2-3(A案)+ §8 H-1〜H-5)
- 「エンジン=内生フロア(原価×k)+クリアリング+**逸脱比例コスト(sink登録)**+
  Calvo型改定確率 / LLM=店主の相対倍率スカラー r」。
- H-1 Calvo型改定確率(**業種別**): 小売(コンビニ・物販)= 月次 **20-30%**(Higo–Saita 財31.1%・
  Total 21.4%)/ **飲食 = 月次 5-10%**(Higo–Saita 外食 5.0% を下限・Ueda 2024 で上方)/
  サービス業 = **5%**。「既決の一律≈20%は飲食に対し約4倍速すぎるので改める」。
- H-2 内生フロア k: FL(材料費+人件費)60% + その他経費 30% + 営業利益 10% が閉じる水準
  = **k≈2.9(原価率35%・高級)/ 3.3(30%・平均)/ 5.0(20%・ドル箱)**。FL 制約は**店舗レベル**。
- H-3 r の出力仕様: **クリップ r∈[0.7, 1.5]**・パース失敗/拒否は**前期 r を維持**し計数。
- H-4 r スカラー化は expedient(ablation 義務)。
- H-5 逸脱比例コストは E7 アンカー未取得のため較正保留(β の値は暫定)。

**LLM はここに居ない**(原則2「LLM の出力は意図まで」)。r は C4 以降の bridge が運ぶ。
本モジュールは r を受け取ってからの**決定論的な算術**だけを持つ。

逐次ループ宣言(P4): なし(全てベクトル演算)。

expedient(本モジュール分)
- 店舗種別 → k の写像(H-2 自身が「店舗種別→k写像」を expedient と書いている)。
- 逸脱比例コストの係数 β = 0.5(E7 アンカー未取得のため較正できない・H-5「保留」)。
- Calvo 抽選は月次確率を**日次へ薄める**(1 − (1−p)^(1/30.44))形にした。設計書は
  月次改定頻度しか与えていない。
- ``clearing`` は「min(需要, 供給)」の最小形。待ち行列・優先順位は行2(施設の収容)側。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Final

import numpy as np

__all__ = [
    "K_PREMIUM",
    "K_AVERAGE",
    "K_VOLUME",
    "StoreKind",
    "K_BY_KIND",
    "PriceSector",
    "CALVO_MONTHLY",
    "R_MIN",
    "R_MAX",
    "DEVIATION_BETA",
    "DAYS_PER_MONTH",
    "floor_price",
    "calvo_daily_probability",
    "calvo_draw",
    "apply_r",
    "deviation_cost",
    "book_deviation_cost",
    "clearing",
    "PriceProposal",
    "propose_price",
]

#: 内生フロア k(H-2 の 3 値)。
K_PREMIUM: Final[float] = 2.9  # 原価率 35%(高級)
K_AVERAGE: Final[float] = 3.3  # 原価率 30%(平均)
K_VOLUME: Final[float] = 5.0  # 原価率 20%(ドル箱)


class StoreKind(IntEnum):
    """店舗の業態(k の 3 値と 1 対 1)。"""

    PREMIUM = 0  # 高級
    AVERAGE = 1  # 平均
    VOLUME = 2  # ドル箱


K_BY_KIND: Final[tuple[float, ...]] = (K_PREMIUM, K_AVERAGE, K_VOLUME)


class PriceSector(IntEnum):
    """Calvo 改定確率の業種(H-1)。"""

    RETAIL = 0  # 小売(コンビニ・物販)
    FOOD = 1  # 飲食
    SERVICE = 2  # サービス


#: 業種別の**月次**改定確率(H-1 の中点: 小売 20-30% → 0.25・飲食 5-10% → 0.075・サービス 5%)。
CALVO_MONTHLY: Final[tuple[float, ...]] = (0.25, 0.075, 0.05)
#: 1 月の日数(月次確率 → 日次確率の換算・expedient)。
DAYS_PER_MONTH: Final[float] = 30.44

#: r のクリップ(H-3)。
R_MIN: Final[float] = 0.7
R_MAX: Final[float] = 1.5
#: 逸脱比例コストの係数(H-5・E7 アンカー未取得のため暫定)。
DEVIATION_BETA: Final[float] = 0.5


def floor_price(cost: np.ndarray | float, k: np.ndarray | float) -> np.ndarray:
    """内生フロア = 原価 × k(H-2)。円未満は切り上げ(フロアを割らない)。

    Example:
        >>> int(floor_price(100, K_AVERAGE))
        330
    """
    c = np.asarray(cost, dtype=np.float64)
    kk = np.asarray(k, dtype=np.float64)
    return np.ceil(c * kk).astype(np.int64)


def calvo_daily_probability(sector: int | np.ndarray) -> np.ndarray:
    """月次改定確率 → 日次改定確率 ``1 − (1−p)^(1/30.44)``(expedient な薄め方)。"""
    s = np.clip(np.asarray(sector, dtype=np.int64), 0, len(CALVO_MONTHLY) - 1)
    p = np.asarray(CALVO_MONTHLY, dtype=np.float64)[s]
    return 1.0 - np.power(1.0 - p, 1.0 / DAYS_PER_MONTH)


def calvo_draw(
    sector: int | np.ndarray, rng: np.random.Generator, *, per: str = "month"
) -> np.ndarray:
    """Calvo 型の改定抽選(H-1)。``per='month'`` なら月次確率・``'day'`` なら日次確率。

    Args:
        sector: ``PriceSector``(スカラーか配列)。
        rng: ``core.rng.stream`` の Generator(決定論)。
        per: ``"month"`` / ``"day"``。

    Returns:
        改定するか否かの bool 配列。
    """
    s = np.atleast_1d(np.asarray(sector, dtype=np.int64))
    if per == "month":
        p = np.asarray(CALVO_MONTHLY, dtype=np.float64)[
            np.clip(s, 0, len(CALVO_MONTHLY) - 1)
        ]
    elif per == "day":
        p = calvo_daily_probability(s)
    else:
        raise ValueError(f"per は 'month' か 'day': {per!r}")
    return rng.random(p.shape) < p


def apply_r(
    prev_price: np.ndarray | int,
    r: np.ndarray | float | None,
    prev_r: np.ndarray | float = 1.0,
) -> tuple[np.ndarray, np.ndarray, int]:
    """LLM の相対倍率 r を価格へ適用する(H-3)。

    - r は ``[0.7, 1.5]`` にクリップ。
    - ``None`` / NaN(パース失敗・出力拒否)は**前期 r を維持**し計数する。

    Returns:
        ``(新価格, 実際に使った r, フォールバック件数)``。
    """
    p = np.atleast_1d(np.asarray(prev_price, dtype=np.float64))
    pr = np.broadcast_to(np.asarray(prev_r, dtype=np.float64), p.shape).astype(np.float64)
    if r is None:
        rr = np.full(p.shape, np.nan)
    else:
        rr = np.broadcast_to(np.asarray(r, dtype=np.float64), p.shape).astype(np.float64).copy()
    bad = ~np.isfinite(rr)
    n_fallback = int(bad.sum())
    rr[bad] = pr[bad]
    rr = np.clip(rr, R_MIN, R_MAX)
    return np.rint(p * rr).astype(np.int64), rr, n_fallback


def deviation_cost(
    price: np.ndarray | int, floor: np.ndarray | int, beta: float = DEVIATION_BETA
) -> np.ndarray:
    """逸脱比例コスト(H-5)= β × max(0, フロア − 価格) × 数量 1 個あたり。

    フロアを**下回った**ぶんに比例するコストを sink(店舗→政府・``AccountCode.DEVIATION_COST``)
    として計上する。フロア以上なら 0。
    """
    p = np.asarray(price, dtype=np.float64)
    f = np.asarray(floor, dtype=np.float64)
    return np.rint(float(beta) * np.maximum(0.0, f - p)).astype(np.int64)


def clearing(demand: np.ndarray | int, supply: np.ndarray | int) -> np.ndarray:
    """クリアリング(最小形): 成立数量 = min(需要, 供給)。"""
    return np.minimum(
        np.asarray(demand, dtype=np.int64), np.asarray(supply, dtype=np.int64)
    )


def book_deviation_cost(ledger, stores: np.ndarray, amounts: np.ndarray, tick: int) -> np.ndarray:
    """逸脱比例コストを **sink として台帳に登録**する(店舗→政府・§8 H-5)。

    「逸脱比例コスト(sink登録)」の実装形。科目は ``AccountCode.DEVIATION_COST``
    (12 科目には無い 15 番目の科目=expedient・親へ報告済みの食い違い#3)。
    """
    from shibuya.economy.accounts import AccountCode, Sector  # 循環を避けて遅延 import

    s = np.asarray(stores, dtype=np.int64).ravel()
    a = np.asarray(amounts, dtype=np.int64).ravel()
    return ledger.transfer_many(
        int(Sector.STORE), s, int(Sector.GOVERNMENT), np.zeros(s.size, dtype=np.int64),
        a, int(AccountCode.DEVIATION_COST), tick,
    )


@dataclass(frozen=True)
class PriceProposal:
    """``propose_price`` の結果(1 店舗ぶん)。"""

    price: int
    floor: int
    r_used: float
    clipped: bool
    fallback: bool
    deviation_cost: int


def propose_price(
    r: float | None,
    *,
    prev_price: int,
    cost: int,
    kind: int = int(StoreKind.AVERAGE),
    prev_r: float = 1.0,
    beta: float = DEVIATION_BETA,
) -> PriceProposal:
    """店主の r(LLM 出力)を受け取り、フロア・クリップ・逸脱コストまでを確定する入口。

    LLM 側(bridge)は「r をパースして渡す」だけ。ここから先は決定論。

    Example:
        >>> p = propose_price(1.2, prev_price=1000, cost=300, kind=int(StoreKind.AVERAGE))
        >>> p.price, p.floor
        (1200, 990)
    """
    floor = int(floor_price(cost, K_BY_KIND[int(kind)])[()])
    raw = float(r) if (r is not None and np.isfinite(r)) else float("nan")
    price_arr, r_arr, n_fb = apply_r(np.array([prev_price]), np.array([raw]), np.array([prev_r]))
    price = int(price_arr[0])
    used = float(r_arr[0])
    clipped = bool(
        (r is not None and np.isfinite(r)) and (float(r) < R_MIN or float(r) > R_MAX)
    )
    return PriceProposal(
        price=price,
        floor=floor,
        r_used=used,
        clipped=clipped,
        fallback=bool(n_fb),
        deviation_cost=int(deviation_cost(price, floor, beta)[()]),
    )
