"""金の台帳(U11)のテスト = 境界・経済設計書 §2.3 が要求する **pytest 8本**。

    「pytest 8本: transfer保存・列挙外科目拒否・行和列和0・純資産=実物資産・
      参入資本のtransfer由来・残差閾値・退蔵項計上・faucet/sink科目別集計」

+ ベクトル版(``transfer_many``)の重複支払者・残高不足・預金脚・成長宣言・決定論。
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from shibuya.core.growth import check_growth
from shibuya.economy import checks as CK
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.ledger import Ledger, growth_declarations
from shibuya.engine.ledger_api import EntityRef, TransferStatus

H, S, E, B, G, W = (
    Sector.HOUSEHOLD, Sector.STORE, Sector.EMPLOYER, Sector.BANK, Sector.GOVERNMENT, Sector.ROW
)


def _ledger(n_h: int = 8, n_s: int = 4, wallet: int = 10_000) -> Ledger:
    led = Ledger(n_h, n_s)
    led.endow_households(np.full(n_h, wallet, dtype=np.int64), tick=0)
    return led


def _total_cash(led: Ledger) -> int:
    return int(led.sector_totals(BalanceLine.CASH).sum())


# ================================================================ 1. transfer 保存
def test_transfer_conserves_cash_over_all_sectors_including_row():
    """1本目: transfer は**外界を含む全部門の現金合計**を変えない(faucet も sink も)。"""
    led = _ledger()
    before = _total_cash(led)
    assert led.transfer(EntityRef(H, 0), EntityRef(S, 1), 300, AccountCode.CONSUMPTION, 5) == 0
    assert led.transfer(EntityRef(S, 1), EntityRef(W, 0), 200, AccountCode.IMPORT_PURCHASE, 6) == 0
    assert led.transfer(EntityRef(H, 2), EntityRef(G, 0), 100, AccountCode.TAX, 7) == 0
    assert _total_cash(led) == before == 0  # 初期財布も外界からの transfer なので総和 0
    assert int(led.balance(BalanceLine.CASH, H)[0]) == 10_000 - 300


def test_insufficient_funds_is_a_return_value_not_an_exception():
    led = _ledger(wallet=100)
    st_code = led.transfer(EntityRef(H, 0), EntityRef(S, 0), 500, AccountCode.CONSUMPTION, 1)
    assert st_code == TransferStatus.INSUFFICIENT_FUNDS
    assert int(led.balance(BalanceLine.CASH, H)[0]) == 100


# ================================================================ 2. 列挙外科目の拒否
def test_unknown_and_forbidden_codes_are_rejected():
    """2本目: 列挙にない科目・表にない部門対の transfer は実行不能(§2.2)。"""
    led = _ledger()
    assert led.transfer(EntityRef(H, 0), EntityRef(S, 0), 100, 999, 1) == (
        TransferStatus.UNKNOWN_CODE
    )
    # 消費支出は世帯→店舗のみ(逆向きは表にない)
    assert led.transfer(EntityRef(S, 0), EntityRef(H, 0), 100, AccountCode.CONSUMPTION, 1) == (
        TransferStatus.FORBIDDEN_PAIR
    )
    # 退蔵項は測度なので transfer 不能
    assert led.transfer(EntityRef(H, 0), EntityRef(S, 0), 100, AccountCode.HOARD, 1) == (
        TransferStatus.UNKNOWN_CODE
    )
    assert led.transfer(EntityRef(H, 0), EntityRef(S, 0), 0, AccountCode.CONSUMPTION, 1) == (
        TransferStatus.BAD_AMOUNT
    )
    assert led.transfer(EntityRef(H, 99), EntityRef(S, 0), 10, AccountCode.CONSUMPTION, 1) == (
        TransferStatus.BAD_ENTITY
    )


# ================================================================ 3. 行和・列和 0
@settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    payers=st.lists(st.integers(0, 7), min_size=1, max_size=40),
    amounts=st.lists(st.integers(1, 900), min_size=1, max_size=40),
    seed=st.integers(0, 10_000),
)
def test_flow_matrix_rows_and_columns_are_balanced(payers, amounts, seed):
    """3本目: 四重記入(行和=科目ごとに 0・列和=部門ごとに Δ現金)。"""
    led = _ledger()
    rng = np.random.default_rng(seed)
    n = min(len(payers), len(amounts))
    p = np.asarray(payers[:n], dtype=np.int64)
    a = np.asarray(amounts[:n], dtype=np.int64)
    stores = rng.integers(0, 4, size=n)
    led.transfer_many(int(H), p, int(S), stores, a, int(AccountCode.CONSUMPTION), 10)
    led.transfer_many(int(S), stores, int(W), np.zeros(n, np.int64), a // 2,
                      int(AccountCode.IMPORT_PURCHASE), 11)
    rep = CK.flow_matrix_balanced(led)
    assert rep.rows_zero, rep.row_residual
    assert rep.cols_match_cash, rep.col_residual
    assert rep.deposit_legs_match


def test_row_column_check_catches_a_direct_balance_assignment():
    """列和検査は「残高の直接代入」(単一API迂回)を捕まえる=これが検算①の本体。"""
    led = _ledger()
    with led.unlocked():
        led.balance(BalanceLine.CASH, S)[0] += 1_000  # 禁じ手(テストのために故意に行う)
    rep = CK.flow_matrix_balanced(led)
    assert rep.rows_zero and not rep.cols_match_cash


# ================================================================ 4. 純資産 = 実物資産
def test_net_worth_equals_real_assets_after_purchases_and_wages():
    """4本目(主検算): Σ純資産 = Σ実物資産 ⟺ Σ金融純資産 = 0。"""
    led = _ledger()
    led.transfer_many(int(H), np.arange(4), int(S), np.zeros(4, np.int64),
                      np.full(4, 500), int(AccountCode.CONSUMPTION), 5)
    led.endow_stores(np.array([10_000, 0, 0, 0]), tick=1)
    led.transfer(EntityRef(S, 0), EntityRef(H, 0), 3_000, AccountCode.WAGE, 6)
    led.transfer(EntityRef(H, 1), EntityRef(B, 0), 2_000, AccountCode.DEPOSIT_NET, 7)
    with led.unlocked():
        led.revalue_inventory(int(S), np.array([50_000, 0, 0, 0], dtype=np.int64))
    rep = CK.net_worth_equals_real_assets(led)
    assert rep.ok, rep.as_text()
    assert rep.real_assets_total == 50_000
    assert rep.financial_net_total == 0


def test_deposit_creates_a_matching_bank_liability():
    led = _ledger()
    led.transfer(EntityRef(H, 0), EntityRef(B, 0), 4_000, AccountCode.DEPOSIT_NET, 1)
    assert int(led.balance(BalanceLine.DEPOSIT, H)[0]) == 4_000
    assert int(led.balance(BalanceLine.LOAN, B)[0]) == 4_000
    assert int(led.balance(BalanceLine.CASH, H)[0]) == 6_000
    # 引き出し(銀行→世帯)で脚が戻る
    led.transfer(EntityRef(B, 0), EntityRef(H, 0), 1_500, AccountCode.DEPOSIT_NET, 2)
    assert int(led.balance(BalanceLine.DEPOSIT, H)[0]) == 2_500
    assert int(led.balance(BalanceLine.LOAN, B)[0]) == 2_500
    assert CK.net_worth_equals_real_assets(led).ok


# ================================================================ 5. 参入資本の由来
def test_entry_capital_must_come_from_allowed_payers():
    """5本目: 参入資本は創業者預金・銀行貸出・外界からの transfer 由来のみ(ex nihilo 禁止)。"""
    led = _ledger()
    assert led.endow_stores(np.array([5_000]), tick=0, payer=Sector.ROW)[0] == 0
    assert led.transfer(EntityRef(B, 0), EntityRef(S, 1), 7_000, AccountCode.ENTRY_CAPITAL, 1) == 0
    assert led.transfer(EntityRef(H, 0), EntityRef(S, 2), 1_000, AccountCode.ENTRY_CAPITAL, 1) == 0
    # 政府・雇用主からの参入資本は表にない = EX_NIHILO
    assert led.transfer(EntityRef(G, 0), EntityRef(S, 3), 1_000, AccountCode.ENTRY_CAPITAL, 1) == (
        TransferStatus.EX_NIHILO
    )
    assert CK.ex_nihilo_ok(led)


# ================================================================ 6. 残差の閾値
def test_residual_threshold_gate():
    """6本目: 残差 > 閾値でゲート失敗(§2.4)。"""
    led = _ledger(n_h=8, wallet=1_000_000)
    ok, amount = CK.residual_gate(led)
    assert ok and amount == 0
    led.transfer(EntityRef(H, 0), EntityRef(S, 0), 900_000, AccountCode.RESIDUAL, 3)
    ok2, amount2 = CK.residual_gate(led)
    assert not ok2 and amount2 == 900_000
    rep = CK.check_all(led)
    assert not rep.ok and any("残差" in r for r in rep.reasons())


# ================================================================ 7. 退蔵項の計上
def test_hoard_is_reported_for_idle_balances():
    """7本目: 使われず溜まる現金/預金を退蔵項として計上する(§2.2 UO 教訓の監視点)。"""
    led = _ledger(n_h=4, wallet=5_000)
    led.transfer(EntityRef(H, 0), EntityRef(S, 0), 100, AccountCode.CONSUMPTION, 1)
    for d in range(40):
        led.on_day_end(d)
        if d == 20:  # 世帯 0 だけ動かし続ける
            led.transfer(EntityRef(H, 0), EntityRef(S, 0), 100, AccountCode.CONSUMPTION, 1)
    rep = CK.hoard_report(led, days=30)
    assert rep.n_entities >= 3
    assert rep.amount >= 3 * 5_000
    assert rep.by_sector["世帯"] > 0


# ================================================================ 8. faucet/sink 科目別集計
def test_faucet_sink_totals_by_account():
    """8本目: faucet/sink の科目別集計(月次 MER の素材)。"""
    led = Ledger(4, 2)
    led.endow_households(np.full(4, 8_000, dtype=np.int64), tick=0)  # faucet 来街者持込
    led.transfer_many(int(H), np.arange(4), int(S), np.zeros(4, np.int64),
                      np.full(4, 1_000), int(AccountCode.CONSUMPTION), 5)  # internal
    led.transfer(EntityRef(S, 0), EntityRef(W, 0), 2_000, AccountCode.IMPORT_PURCHASE, 6)  # sink
    led.transfer(EntityRef(H, 0), EntityRef(G, 0), 500, AccountCode.TAX, 7)  # sink
    led.transfer(EntityRef(W, 0), EntityRef(H, 1), 300, AccountCode.WAGE, 8)  # faucet
    tot = CK.faucet_sink_totals(led)
    assert tot["FAUCET"] == {"来街者持込": 32_000, "賃金": 300}
    assert tot["SINK"] == {"域外仕入": 2_000, "税": 500}
    assert tot["INTERNAL"] == {"消費支出": 4_000}


# ================================================================ ベクトル版・その他
def test_transfer_many_handles_duplicate_payers_in_row_order():
    """同一支払者の複数行は行順の前置和で判定する(残高を超えた行以降は不足)。"""
    led = Ledger(2, 1)
    led.endow_households(np.array([1_000, 1_000]), tick=0)
    status = led.transfer_many(
        int(H), np.array([0, 0, 0, 1]), int(S), np.zeros(4, np.int64),
        np.array([600, 300, 400, 200]), int(AccountCode.CONSUMPTION), 1,
    )
    assert list(status) == [0, 0, int(TransferStatus.INSUFFICIENT_FUNDS), 0]
    assert int(led.balance(BalanceLine.CASH, H)[0]) == 100
    assert int(led.balance(BalanceLine.CASH, H)[1]) == 800
    assert CK.flow_matrix_balanced(led).ok


def test_transfer_many_rejects_the_whole_batch_for_a_bad_pair():
    led = _ledger()
    status = led.transfer_many(
        int(S), np.zeros(3, np.int64), int(H), np.arange(3), np.full(3, 10),
        int(AccountCode.CONSUMPTION), 1,
    )
    assert set(status) == {int(TransferStatus.FORBIDDEN_PAIR)}
    assert led.rejections[int(TransferStatus.FORBIDDEN_PAIR)] == 3


def test_attached_household_cash_is_the_same_array():
    """世帯の現金は写しでなく採用(agents.money と同一配列)。"""
    money = np.zeros(5, dtype=np.int32)
    led = Ledger(5, 1)
    led.attach_household_cash(money)
    led.endow_households(np.full(5, 700, dtype=np.int64), tick=0)
    assert list(money) == [700] * 5
    assert led.balance(BalanceLine.CASH, H) is money


def test_frozen_arrays_reject_writes_outside_the_ledger():
    led = _ledger()
    with pytest.raises(ValueError):
        led.balance(BalanceLine.CASH, S)[0] = 1
    with pytest.raises(ValueError):
        np.asarray(led.flow)[0, 0, 0] = 1


def test_depreciation_reduces_fixed_assets_without_moving_cash():
    led = _ledger()
    with led.unlocked():
        led.balance(BalanceLine.FIXED_ASSET, S)[:] = 10_000
    before = _total_cash(led)
    led.depreciate(int(S), np.array([0, 1]), np.array([1_000, 500]), tick=9)
    assert list(led.balance(BalanceLine.FIXED_ASSET, S)[:2]) == [9_000, 9_500]
    assert _total_cash(led) == before
    assert CK.flow_matrix_balanced(led).ok
    assert CK.net_worth_equals_real_assets(led).ok


def test_raw_log_is_bounded_and_daily_aggregated():
    """D-R2-6: 生ログは保持窓 N 日+リングバッファで有界・日次で集約行へ畳む。"""
    led = Ledger(4, 2, raw_capacity=16, retention_days=1)
    led.endow_households(np.full(4, 50_000, dtype=np.int64), tick=0)
    for t in range(30):
        led.transfer(EntityRef(H, t % 4), EntityRef(S, 0), 10, AccountCode.CONSUMPTION, t)
    assert led.raw_rows().shape[0] <= 16
    assert led.n_raw_dropped > 0
    led.on_day_end(0)
    assert len(led.flow_daily) == 1
    led.transfer(EntityRef(H, 0), EntityRef(S, 0), 10, AccountCode.CONSUMPTION, 1_500)
    led.on_day_end(1)
    assert led.raw_rows().shape[0] <= 16
    assert int(np.stack(led.flow_daily).sum()) > 0


def test_growth_declarations_pass_the_gate():
    """成長宣言(5欄)が 24step→30日の外挿で cap 内。"""
    decls = growth_declarations()
    assert set(decls) == {"transfer_log", "flow_matrix_daily", "ledger_balances"}
    # 実測側に渡すのは**増分**(定常サイズは per_agent_bytes/per_cell_bytes 欄が持つ)
    measured = {
        "transfer_log": 5_000 * 3 * 24,  # 1 日ぶんの生ログ
        "flow_matrix_daily": 4_320,
        "ledger_balances": 0,  # 残高は日をまたいで伸びない
    }
    rep = check_growth(decls, measured, steps=1_440, minutes_per_step=1, n_entities=5_000)
    assert rep.ok, rep.as_text()


def test_employers_come_from_the_world_asset_or_a_synthetic_fallback():
    """雇用主 = W6 の組織台帳(``w6_org.parquet``)。無ければ合成。"""
    from pathlib import Path

    from shibuya.economy.ledger import DEFAULT_ASSETS_DIR, load_employers

    fallback = load_employers(path="does/not/exist", n_synthetic=3, employees=7)
    assert fallback.n == 3 and fallback.total_employees == 21
    assert fallback.source == "synthetic"
    if (Path(DEFAULT_ASSETS_DIR) / "w6_org.parquet").exists():
        real = load_employers()
        assert real.n > 1_000 and real.total_employees > real.n
        assert "w6_org.parquet" in real.source
        led = Ledger(4, 2, n_employers=real.n)
        assert led.sizes[int(E)] == real.n


def test_state_hash_is_deterministic():
    a, b = _ledger(), _ledger()
    assert a.state_hash() == b.state_hash()
    a.transfer(EntityRef(H, 0), EntityRef(S, 0), 100, AccountCode.CONSUMPTION, 1)
    assert a.state_hash() != b.state_hash()
