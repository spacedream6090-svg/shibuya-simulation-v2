"""§2.5 の金額アンカー(公的値)と初期財布・月次賃金のテスト。

アンカーの**値そのもの**を設計書の表と突き合わせる(数字が黙って変わらないための門)。
"""

from __future__ import annotations

import numpy as np

from shibuya.core.rng import stream
from shibuya.economy import anchors as A
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.ledger import Ledger


def test_anchor_values_match_the_design_table():
    """§2.5 の表の値(家計調査2025・最低賃金・経済センサス2021・区ごみ)。"""
    assert A.SPEND_MULTI_PERSON_PER_DAY == 10_300
    assert A.SPEND_SINGLE_PER_DAY == 5_700
    assert A.SPEND_TOTAL_PER_MONTH == 259_880
    assert A.CONSUMPTION_PROPENSITY == 0.65
    assert A.SAVINGS_PER_MONTH == 177_061
    assert A.VISITOR_CARRY_IN == 71_000
    assert A.MIN_WAGE_HOURLY == 1_226
    assert A.SALES_PER_ESTABLISHMENT["宿泊・飲食"] == 85_320_000
    assert A.SALES_PER_ESTABLISHMENT["卸売・小売"] == 131_520_000
    assert A.SALES_PER_ESTABLISHMENT["生活関連・娯楽"] == 22_530_000
    assert A.EMPLOYEES_SHIBUYA == 516_541
    assert A.ESTABLISHMENTS_SHIBUYA == 27_624
    assert A.WASTE_TONNES_PER_DAY == 119.6
    assert A.WASTE_TONNES_PER_YEAR == 43_663


def test_monthly_figures_are_consistent_with_the_daily_ones():
    """親検算: 314,001円/月 ÷ 30.44 ≈ 10,300円/日・173,042 ÷ 30.44 ≈ 5,700円/日。"""
    assert abs(314_001 / 30.44 - A.SPEND_MULTI_PERSON_PER_DAY) < 350
    assert abs(173_042 / 30.44 - A.SPEND_SINGLE_PER_DAY) < 60
    # 区ごみ 43,663 t/年度 ÷ 365 = 119.6 t/日
    assert abs(A.WASTE_TONNES_PER_YEAR / 365.0 - A.WASTE_TONNES_PER_DAY) < 0.7


def test_every_anchor_carries_a_source_string():
    assert len(A.ANCHORS) >= 12
    for a in A.ANCHORS:
        assert a.source and a.unit and a.value > 0
        assert a.grade == "A"


def test_initial_wallets_are_deterministic_and_kind_dependent():
    kinds = np.array([int(A.WalletKind.RESIDENT)] * 2_000 + [int(A.WalletKind.COMMUTER)] * 2_000)
    w1 = A.initial_wallets(kinds.size, kinds, stream(3, "economy.wallet"))
    w2 = A.initial_wallets(kinds.size, kinds, stream(3, "economy.wallet"))
    assert np.array_equal(w1, w2)
    assert (w1 >= A.WALLET_MIN).all() and (w1 <= A.WALLET_MAX).all()
    # 居住者(二人以上相当)の方が通勤者(単身相当)より中央値が大きい
    assert np.median(w1[:2_000]) > np.median(w1[2_000:])
    assert abs(np.median(w1[:2_000]) / (A.SPEND_MULTI_PERSON_PER_DAY * A.WALLET_DAYS) - 1) < 0.1


def test_monthly_wage_amounts_use_the_minimum_wage_floor():
    hours = np.array([0, 100, 160.5])
    amounts = A.monthly_wage_amounts(hours)
    assert list(amounts) == [0, 122_600, int(round(160.5 * 1_226))]
    assert list(A.monthly_wage_amounts(np.array([100]), premium=1.2)) == [147_120]


def test_monthly_wages_move_money_from_employers_to_households():
    led = Ledger(3, 1, n_employers=2)
    # 雇用主に外界から参入資本を入れてから賃金を払う(ex nihilo 禁止)
    led.transfer_many(
        int(Sector.ROW), np.zeros(2, dtype=np.int64), int(Sector.EMPLOYER), np.arange(2),
        np.full(2, 1_000_000), int(AccountCode.ENTRY_CAPITAL), 0,
    )
    status = A.monthly_wages(
        led, employers=np.array([0, 0, 1]), households=np.arange(3),
        hours=np.array([160, 80, 160]), tick=10,
    )
    assert list(status) == [0, 0, 0]
    cash = led.balance(BalanceLine.CASH, Sector.HOUSEHOLD)
    assert int(cash[0]) == 160 * A.MIN_WAGE_HOURLY
    assert int(cash[1]) == 80 * A.MIN_WAGE_HOURLY
    assert int(np.asarray(led.flow)[
        int(Sector.EMPLOYER), int(Sector.HOUSEHOLD), int(AccountCode.WAGE)
    ]) == int(cash.sum())


def test_wages_from_outside_employers_are_a_faucet():
    led = Ledger(2, 1)
    status = A.monthly_wages(
        led, employers=None, households=np.arange(2), hours=np.array([100, 100]),
        tick=1, from_row=True,
    )
    assert list(status) == [0, 0]
    assert int(led.balance(BalanceLine.CASH, Sector.ROW)[0]) == -2 * 100 * A.MIN_WAGE_HOURLY
