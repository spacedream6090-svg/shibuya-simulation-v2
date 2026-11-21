"""行5 価格形成のエンジン側テスト(世界過程設計書 §4 行5 A案 + §8 H-2)。

内生フロア k の 3 値・クリアリング。**LLM はここに居ない**。
〔第347〕Calvo の改定・r のクリップとフォールバック・逸脱比例コスト・``propose_price`` は消した(返事その 8 §1-3 の 2)。
"""

from __future__ import annotations

import numpy as np

from shibuya.economy import pricing as P


def test_floor_k_has_the_three_values_from_h2():
    """H-2: k≈2.9(原価率35%・高級)/ 3.3(30%・平均)/ 5.0(20%・ドル箱)。"""
    assert (P.K_PREMIUM, P.K_AVERAGE, P.K_VOLUME) == (2.9, 3.3, 5.0)
    assert P.K_BY_KIND == (2.9, 3.3, 5.0)
    assert int(P.floor_price(1_000, P.K_AVERAGE)) == 3_300
    assert int(P.floor_price(200, P.K_VOLUME)) == 1_000
    # 原価率の逆数になっている(FL60+その他30+利益10 が閉じる水準)
    assert abs(1.0 / P.K_PREMIUM - 0.35) < 0.011
    assert abs(1.0 / P.K_AVERAGE - 0.30) < 0.011
    assert abs(1.0 / P.K_VOLUME - 0.20) < 1e-9


def test_clearing_is_the_minimum_of_demand_and_supply():
    assert list(P.clearing(np.array([5, 2, 0]), np.array([3, 9, 4]))) == [3, 2, 0]
