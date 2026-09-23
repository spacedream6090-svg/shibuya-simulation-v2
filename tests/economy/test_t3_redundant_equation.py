"""T3(SFC の冗長方程式)の毎期検算(D-85 (a)・ユーザー決定 2026-09-17)。

正典
- 境界・経済設計書 §2.3 の**空欄/残務**: 「U-B答申の保存則テスト5層のうち **T3(冗長方程式を
  実装せず『検算値』として毎期assert)は答申にあるが未実装**(``checks.py`` は検算①②の
  2本のみ)」。T3 は SFC 標準の検証法(Levy WP 745 付録「Equation (10) is the hidden equation」)。
- 同 §2.4 センサス: 月次 = MER の**固定表**。「固定表は列も行順もバイトも変えない」。

見るもの
(i) 綺麗な台帳では 3 検査が通り ``t3_ok=True``/
(ii) **残高の直接代入**(単一 API 迂回)を仕込むと列和の検査が落ちる。**部門間で相殺する**
     直接代入は検算②(Σ純資産=Σ実物資産)を素通りするが T3 は捕まえる=T3 を足した理由/
(iii) 預金脚(Δ預金 − Δ借入)の破れは、行和・列和が無事でも捕まる/
(iv) 月次センサスが立つ日(畳んだ日数が ``MONTH_DAYS`` の倍数)だけ走る/
(v) 検算①を**再実装していない**(同じ窓を渡せば ``flow_matrix_balanced`` と同じ答え)。
"""

from __future__ import annotations

import numpy as np

from shibuya.economy import census as CS
from shibuya.economy import checks as CK
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.ledger import Ledger
from shibuya.engine.ledger_api import EntityRef


def _world(n_h: int = 6, n_s: int = 3) -> Ledger:
    led = Ledger(n_h, n_s)
    led.endow_households(np.full(n_h, 20_000, dtype=np.int64), tick=0)
    return led


def _five_days(led: Ledger, days: int = 5) -> Ledger:
    """transfer 単一 API だけで動かした ``days`` 日ぶんの台帳(残差 0)。"""
    for d in range(days):
        t = d * 1_440
        led.transfer(EntityRef(Sector.HOUSEHOLD, 0), EntityRef(Sector.STORE, 0),
                     700, AccountCode.CONSUMPTION, t)
        led.transfer(EntityRef(Sector.STORE, 0), EntityRef(Sector.ROW, 0),
                     200, AccountCode.IMPORT_PURCHASE, t + 5)
        led.transfer(EntityRef(Sector.HOUSEHOLD, 1), EntityRef(Sector.BANK, 0),
                     1_000, AccountCode.DEPOSIT_NET, t + 7)
        led.on_day_end(d)
    return led


# ------------------------------------------------------------------ (i) 通る
def test_t3_passes_on_a_ledger_that_only_used_transfer():
    led = _five_days(_world())
    t3 = CK.t3_check(led)
    assert t3.ok
    assert (t3.rows_zero, t3.cols_match_cash, t3.deposit_legs_match) == (True, True, True)
    assert (t3.row_residual_max, t3.col_residual_max, t3.deposit_residual) == (0, 0, 0)
    assert t3.days == 5 and t3.scope == "cumulative"
    assert t3.reasons() == () and "PASS" in t3.as_text()


def test_the_monthly_mer_carries_t3_and_its_breakdown():
    """月次 MER の戻りに ``t3_ok`` と内訳が出る(**固定表 parquet の列は増えない**)。"""
    led = _five_days(_world())
    mer = CS.monthly_mer(led, month=0, days=5)
    assert mer["t3_ok"] is True
    assert set(mer["t3"]) == {
        "ok", "rows_zero", "cols_match_cash", "deposit_legs_match",
        "row_residual_max", "col_residual_max", "deposit_residual", "days", "scope",
    }
    assert mer["t3"]["ok"] is True and mer["t3"]["days"] == 5


def test_the_open_day_is_inside_the_window():
    """まだ畳んでいない当日の取引も窓に入る(締める前に走らせても答えが合う)。"""
    led = _five_days(_world())
    led.transfer(EntityRef(Sector.HOUSEHOLD, 2), EntityRef(Sector.STORE, 0),
                 500, AccountCode.CONSUMPTION, 5 * 1_440)
    t3 = CK.t3_check(led)
    assert t3.ok and t3.days == 5  # 畳んだ日は 5 日・当日ぶんは締めずに入っている


# --------------------------------------------- (ii) 残高の直接代入(単一API迂回)
def test_a_direct_balance_assignment_breaks_the_column_check():
    """列和(部門ごとの Σ科目)= Δ現金 が破れる。行和と預金脚は無事=どこが壊れたか分かる。"""
    led = _five_days(_world())
    with led.unlocked():
        led.balance(BalanceLine.CASH, Sector.HOUSEHOLD)[0] += 5_000  # 迂回
    t3 = CK.t3_check(led)
    assert t3.ok is False
    assert t3.cols_match_cash is False
    assert t3.rows_zero is True and t3.deposit_legs_match is True
    assert t3.col_residual_max == 5_000
    assert any("列和" in r for r in t3.reasons()) and "FAIL" in t3.as_text()
    assert CS.monthly_mer(led, month=0, days=5)["t3_ok"] is False


def test_offsetting_direct_assignments_slip_past_check2_but_not_t3():
    """**T3 を足した理由**: 検算②は集計の恒等式なので部門間で相殺すると通ってしまう。

    世帯の現金を +5,000・店舗の現金を −5,000 と直接代入すると Σ金融純資産は 0 のままで
    検算②は PASS。T3 は**部門ごと**に列和と Δ現金を突き合わせるので両方の部門で落ちる。
    """
    led = _five_days(_world())
    with led.unlocked():
        led.balance(BalanceLine.CASH, Sector.HOUSEHOLD)[0] += 5_000
        led.balance(BalanceLine.CASH, Sector.STORE)[0] -= 5_000
    assert CK.net_worth_equals_real_assets(led).ok is True  # 検算②は素通り
    t3 = CK.t3_check(led)
    assert t3.ok is False and t3.cols_match_cash is False
    assert t3.col_residual_max == 5_000


# ------------------------------------------------------------------ (iii) 預金脚
def test_a_broken_deposit_leg_is_caught_even_when_the_rows_and_columns_are_clean():
    led = _five_days(_world())
    with led.unlocked():
        led.balance(BalanceLine.DEPOSIT, Sector.HOUSEHOLD)[0] += 1_000  # 借入の相方が無い
    t3 = CK.t3_check(led)
    assert t3.ok is False
    assert t3.deposit_legs_match is False and t3.deposit_residual == 1_000
    assert t3.rows_zero is True and t3.cols_match_cash is True  # 現金は動いていない
    assert any("預金脚" in r for r in t3.reasons())


# ------------------------------------------------------------------ (iv) 月末だけ
def test_the_monthly_check_only_fires_at_the_month_break():
    assert CS.MONTH_DAYS == 30
    assert CS.is_month_end(0) is False and CS.is_month_end(1) is False
    assert CS.is_month_end(CS.MONTH_DAYS) is True
    assert CS.is_month_end(2 * CS.MONTH_DAYS) is True

    led = _world()
    fired: list[int] = []
    for d in range(CS.MONTH_DAYS):
        led.on_day_end(d)
        if CS.monthly_census_t3(led, d) is not None:
            fired.append(d)
    assert fired == [CS.MONTH_DAYS - 1]  # 30 日ぶん畳んだ日だけ
    row = CS.monthly_census_t3(led, CS.MONTH_DAYS - 1)
    assert row is not None and row["ok"] is True and row["days"] == CS.MONTH_DAYS
    assert row["day"] == CS.MONTH_DAYS - 1


def test_a_one_day_ledger_has_no_monthly_census():
    led = _five_days(_world(), days=1)
    assert CS.monthly_census_t3(led, 0) is None  # 未実行


# ------------------------------------------------------------------ (v) 再実装していない
def test_t3_goes_through_the_same_check1_function():
    """T3 は検算①の**窓違い**——同じ窓を渡せば ``flow_matrix_balanced`` と同じ答え。"""
    led = _five_days(_world())
    close = led.cumulative_close()
    fc = CK.flow_matrix_balanced(led, close)
    t3 = CK.t3_check(led)
    assert (fc.rows_zero, fc.cols_match_cash, fc.deposit_legs_match, fc.ok) == (
        t3.rows_zero, t3.cols_match_cash, t3.deposit_legs_match, t3.ok
    )
    # 窓を明示で渡すと ``scope`` がそう名乗る(既定は期首→現在)。
    assert CK.t3_check(led, close).scope == "window"
    # 窓の左端は**期首**(生成時=全部門 0 円)なので、Δ現金の合計は現在の現金合計に等しい。
    total_cash = sum(
        int(np.asarray(led.balance(BalanceLine.CASH, s)).astype(np.int64).sum())
        for s in Sector
    )
    assert int(close.d_cash.sum()) == total_cash
