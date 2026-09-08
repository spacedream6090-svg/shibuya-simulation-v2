"""行5 価格形成のエンジン側テスト(世界過程設計書 §4 行5 A案 + §8 H-1〜H-5)。

内生フロア k の 3 値・Calvo 改定確率の業種別・r のクリップとフォールバック・
逸脱比例コスト・クリアリング。**LLM はここに居ない**(r は外から来るスカラー)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.core.rng import stream
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


def test_calvo_monthly_probabilities_are_by_sector():
    """H-1: 小売 20-30%・飲食 5-10%・サービス 5%(一律 20% を改める)。"""
    assert P.CALVO_MONTHLY[int(P.PriceSector.RETAIL)] == 0.25
    assert 0.05 <= P.CALVO_MONTHLY[int(P.PriceSector.FOOD)] <= 0.10
    assert P.CALVO_MONTHLY[int(P.PriceSector.SERVICE)] == 0.05
    daily = P.calvo_daily_probability(np.array([0, 1, 2]))
    assert (daily > 0).all() and (daily < np.asarray(P.CALVO_MONTHLY)).all()


def test_calvo_draw_is_deterministic_and_frequencies_match():
    a = P.calvo_draw(np.zeros(5_000, dtype=int), stream(7, "economy.calvo"))
    b = P.calvo_draw(np.zeros(5_000, dtype=int), stream(7, "economy.calvo"))
    assert np.array_equal(a, b)
    assert abs(a.mean() - P.CALVO_MONTHLY[0]) < 0.02
    food = P.calvo_draw(np.ones(5_000, dtype=int), stream(7, "economy.calvo"))
    assert abs(food.mean() - P.CALVO_MONTHLY[1]) < 0.02
    with pytest.raises(ValueError):
        P.calvo_draw(0, stream(1, "x"), per="year")


def test_r_is_clipped_to_the_declared_range():
    """H-3: r∈[0.7, 1.5] にクリップ(構造的上限)。"""
    price, used, n_fb = P.apply_r(np.array([1_000, 1_000, 1_000]), np.array([0.1, 1.2, 9.9]))
    assert list(price) == [700, 1_200, 1_500]
    assert list(np.round(used, 3)) == [0.7, 1.2, 1.5]
    assert n_fb == 0


def test_parse_failure_keeps_the_previous_r_and_is_counted():
    """H-3: 出力拒否/パース失敗は**前期 r を維持**し計数する(診断行)。"""
    price, used, n_fb = P.apply_r(np.array([1_000, 2_000]), np.array([np.nan, 1.1]),
                                  prev_r=np.array([0.9, 1.0]))
    assert list(price) == [900, 2_200]
    assert n_fb == 1
    price2, used2, n_fb2 = P.apply_r(np.array([1_000]), None, prev_r=1.25)
    assert list(price2) == [1_250] and n_fb2 == 1


def test_deviation_cost_is_proportional_to_the_gap_below_the_floor():
    """H-5: 逸脱比例コストはフロアを下回ったぶんに比例(sink 登録)。"""
    assert int(P.deviation_cost(900, 1_000, beta=0.5)) == 50
    assert int(P.deviation_cost(1_200, 1_000)) == 0
    assert list(P.deviation_cost(np.array([500, 1_000]), np.array([1_000, 1_000]), 1.0)) == [
        500, 0
    ]


def test_deviation_cost_is_booked_as_a_sink_to_the_government():
    """H-5「逸脱比例コスト(sink登録)」= 店舗→政府の transfer として台帳に載る。"""
    from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
    from shibuya.economy.checks import faucet_sink_totals, flow_matrix_balanced
    from shibuya.economy.ledger import Ledger

    led = Ledger(1, 2)
    led.endow_stores(np.array([10_000, 10_000]), tick=0)
    status = P.book_deviation_cost(led, np.array([0, 1]), np.array([300, 100]), tick=5)
    assert list(status) == [0, 0]
    assert int(led.balance(BalanceLine.CASH, Sector.GOVERNMENT)[0]) == 400
    assert faucet_sink_totals(led)["SINK"]["逸脱比例コスト"] == 400
    assert flow_matrix_balanced(led).ok
    assert int(np.asarray(led.flow)[
        int(Sector.STORE), int(Sector.GOVERNMENT), int(AccountCode.DEVIATION_COST)
    ]) == 400


def test_clearing_is_the_minimum_of_demand_and_supply():
    assert list(P.clearing(np.array([5, 2, 0]), np.array([3, 9, 4]))) == [3, 2, 0]


def test_propose_price_is_the_single_entry_point_for_the_llm_scalar():
    """LLM の r → フロア・クリップ・逸脱コストまでを決定論で確定する入口。"""
    p = P.propose_price(1.2, prev_price=1_000, cost=300, kind=int(P.StoreKind.AVERAGE))
    assert (p.price, p.floor, p.clipped, p.fallback) == (1_200, 990, False, False)
    assert p.deviation_cost == 0
    clipped = P.propose_price(3.0, prev_price=1_000, cost=300)
    assert clipped.price == 1_500 and clipped.clipped
    fallback = P.propose_price(None, prev_price=1_000, cost=300, prev_r=0.8)
    assert fallback.price == 800 and fallback.fallback
    below = P.propose_price(0.7, prev_price=1_000, cost=400, kind=int(P.StoreKind.PREMIUM))
    assert below.floor == 1_160 and below.deviation_cost > 0
