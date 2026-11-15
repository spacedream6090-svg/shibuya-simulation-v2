"""economy.pricing — 行5 価格形成のエンジン側(内生フロアの係数 k・クリアリング)。

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

〔第347 注〕Calvo の改定(H-1)・r の適用(H-3)・逸脱比例コスト(H-5)と入口 ``propose_price`` は消した
(返事その 8 §1-3 の 2・仕様 EO-18=Calvo は結線しない・β を E7 で較正しない)。残すのは係数 k
(``goods.CATEGORY_K`` が原価=価格÷k と参入資本の原価率に使う=既定のランに効く)・``floor_price``・``clearing``。
型 ``PriceSector``・``PriceProposal`` はクラスの名の固定の表(``runtime/state/class_ids.py``)に行があるので残した。

**LLM はここに居ない**(原則2「LLM の出力は意図まで」)。本モジュールは**決定論的な算術**だけを持つ。

逐次ループ宣言(P4): なし(全てベクトル演算)。

expedient(本モジュール分)
- 店舗種別 → k の写像(H-2 自身が「店舗種別→k写像」を expedient と書いている)。
- 〔第347 で消した〕逸脱比例コストの係数 β = 0.5(H-5)。
- 〔第347 で消した〕Calvo 抽選の月次確率 → 日次確率の薄め方(H-1)。
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
    "floor_price",
    "clearing",
    "PriceProposal",
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
    """Calvo 改定確率の業種(H-1)。〔第347〕確率と抽選は消した。型はクラスの名の固定の表に行があるので残した。"""

    RETAIL = 0  # 小売(コンビニ・物販)
    FOOD = 1  # 飲食
    SERVICE = 2  # サービス


def floor_price(cost: np.ndarray | float, k: np.ndarray | float) -> np.ndarray:
    """内生フロア = 原価 × k(H-2)。円未満は切り上げ(フロアを割らない)。

    Example:
        >>> int(floor_price(100, K_AVERAGE))
        330
    """
    c = np.asarray(cost, dtype=np.float64)
    kk = np.asarray(k, dtype=np.float64)
    return np.ceil(c * kk).astype(np.int64)


def clearing(demand: np.ndarray | int, supply: np.ndarray | int) -> np.ndarray:
    """クリアリング(最小形): 成立数量 = min(需要, 供給)。"""
    return np.minimum(
        np.asarray(demand, dtype=np.int64), np.asarray(supply, dtype=np.int64)
    )


@dataclass(frozen=True)
class PriceProposal:
    """店主の r を当てた価格の提案(1 店舗ぶん)。〔第347〕作り手 ``propose_price`` は消した。型はクラスの名の固定の表に
    行があるので残した。"""

    price: int
    floor: int
    r_used: float
    clipped: bool
    fallback: bool
    deviation_cost: int
