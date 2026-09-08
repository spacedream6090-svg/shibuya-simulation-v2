"""科目の列挙と faucet/sink 表のテスト(境界・経済設計書 §2.1-2.2)。

「**account_code の列挙型と1対1**・列挙にない科目の transfer は**実行不能**」の機械検査。
"""

from __future__ import annotations

import pytest

from shibuya.agents.state import AgentKind
from shibuya.economy.accounts import (
    ACCOUNT_NAMES,
    ACCOUNTS,
    BALANCE_LINE_NAMES,
    ENTRY_CAPITAL_PAYERS,
    NON_TRANSFERABLE,
    SECTOR_NAMES,
    STORED_LINES,
    AccountCode,
    BalanceLine,
    FlowKind,
    Sector,
    faucet_sink_table,
    flow_kind,
    is_allowed,
)
from shibuya.economy.anchors import WalletKind
from shibuya.engine import ledger_api as api


def test_six_sectors_match_the_design():
    """§2.1: 世帯・店舗・雇用主・銀行・政府・外界の6部門。"""
    assert [s.name for s in Sector] == [
        "HOUSEHOLD", "STORE", "EMPLOYER", "BANK", "GOVERNMENT", "ROW"
    ]
    assert SECTOR_NAMES == ("世帯", "店舗", "雇用主", "銀行", "政府", "外界")


def test_sector_codes_match_engine_api():
    """依存逆転の境界: economy の Sector と engine.ledger_api の部門番号が一致する。"""
    assert (int(Sector.HOUSEHOLD), int(Sector.STORE), int(Sector.EMPLOYER)) == (
        api.SECTOR_HOUSEHOLD, api.SECTOR_STORE, api.SECTOR_EMPLOYER
    )
    assert (int(Sector.BANK), int(Sector.GOVERNMENT), int(Sector.ROW)) == (
        api.SECTOR_BANK, api.SECTOR_GOVERNMENT, api.SECTOR_ROW
    )
    assert len(Sector) == api.N_SECTORS


def test_balance_sheet_has_six_lines_and_net_worth_is_derived():
    """§2.2: 貸借対照表6行。純資産だけは導出(実配列を持たない)。"""
    assert len(BalanceLine) == len(BALANCE_LINE_NAMES) == 6
    assert BalanceLine.NET_WORTH not in STORED_LINES
    assert len(STORED_LINES) == 5


def test_twelve_flow_accounts_plus_residual_hoard_and_deviation_cost():
    """§2.2 の 12 科目 + 残差 + 退蔵(+ §8 H-5 の逸脱比例コスト)。"""
    twelve = [
        "消費支出", "賃金", "域外仕入", "税", "利子", "家賃", "預金純増",
        "来街者持込", "持ち出し", "参入資本", "配当/内部留保", "減価償却",
    ]
    assert list(ACCOUNT_NAMES[:12]) == twelve
    assert ACCOUNT_NAMES[12:] == ("残差科目", "退蔵項", "逸脱比例コスト")
    assert len(AccountCode) == 15


def test_faucet_sink_table_is_one_to_one_with_the_enum():
    """faucet/sink 表は account_code の列挙と 1 対 1(全科目に行がある)。"""
    assert set(ACCOUNTS) == set(AccountCode)
    names = {row[0] for row in faucet_sink_table()}
    assert names == set(ACCOUNT_NAMES)


def test_unknown_code_is_impossible():
    """列挙にない科目は許可されない(=transfer 実行不能)。"""
    assert not is_allowed(999, Sector.HOUSEHOLD, Sector.STORE)
    assert not is_allowed(-1, Sector.HOUSEHOLD, Sector.STORE)


def test_hoard_is_a_measure_not_a_flow():
    """退蔵項はストックの測度。どの部門対でも transfer できない。"""
    assert AccountCode.HOARD in NON_TRANSFERABLE
    for a in Sector:
        for b in Sector:
            assert not is_allowed(AccountCode.HOARD, a, b)
    assert flow_kind(AccountCode.HOARD, Sector.HOUSEHOLD, Sector.HOUSEHOLD) == FlowKind.MEASURE


def test_faucet_and_sink_classification():
    """faucet=来街者持込・域外雇用主の賃金/sink=域外仕入・税・持ち出し(§2.2)。"""
    assert flow_kind(AccountCode.CARRY_IN, Sector.ROW, Sector.HOUSEHOLD) == FlowKind.FAUCET
    assert flow_kind(AccountCode.WAGE, Sector.ROW, Sector.HOUSEHOLD) == FlowKind.FAUCET
    assert flow_kind(AccountCode.WAGE, Sector.EMPLOYER, Sector.HOUSEHOLD) == FlowKind.INTERNAL
    assert flow_kind(AccountCode.IMPORT_PURCHASE, Sector.STORE, Sector.ROW) == FlowKind.SINK
    assert flow_kind(AccountCode.TAX, Sector.HOUSEHOLD, Sector.GOVERNMENT) == FlowKind.SINK
    assert flow_kind(AccountCode.CARRY_OUT, Sector.HOUSEHOLD, Sector.ROW) == FlowKind.SINK
    assert flow_kind(
        AccountCode.DEVIATION_COST, Sector.STORE, Sector.GOVERNMENT
    ) == FlowKind.SINK
    assert flow_kind(
        AccountCode.CONSUMPTION, Sector.HOUSEHOLD, Sector.STORE
    ) == FlowKind.INTERNAL


def test_consumption_is_household_to_store_only():
    assert is_allowed(AccountCode.CONSUMPTION, Sector.HOUSEHOLD, Sector.STORE)
    for a in Sector:
        for b in Sector:
            if (a, b) != (Sector.HOUSEHOLD, Sector.STORE):
                assert not is_allowed(AccountCode.CONSUMPTION, a, b)


def test_entry_capital_payers_are_restricted_ex_nihilo():
    """§2.3: 参入資本は創業者預金・銀行貸出・外界からのみ。"""
    assert ENTRY_CAPITAL_PAYERS == frozenset({Sector.HOUSEHOLD, Sector.BANK, Sector.ROW})
    for payer in Sector:
        allowed_any = any(
            is_allowed(AccountCode.ENTRY_CAPITAL, payer, payee) for payee in Sector
        )
        assert allowed_any == (payer in ENTRY_CAPITAL_PAYERS)


def test_depreciation_is_a_self_loop():
    """減価償却は相手方が無い(設計書との食い違い#1)ので自己ループとして受理する。"""
    assert is_allowed(AccountCode.DEPRECIATION, Sector.STORE, Sector.STORE)
    assert not is_allowed(AccountCode.DEPRECIATION, Sector.STORE, Sector.HOUSEHOLD)
    assert flow_kind(AccountCode.DEPRECIATION, Sector.STORE, Sector.STORE) == FlowKind.BOOK


def test_wallet_kind_matches_agent_kind():
    """層契約で economy から agents を import できないので**値の写し**が一致することを検査。"""
    assert [k.name for k in WalletKind] == [k.name for k in AgentKind]
    assert [int(k) for k in WalletKind] == [int(k) for k in AgentKind]


def test_flow_kind_rejects_unknown_code():
    with pytest.raises(ValueError):
        flow_kind(999, Sector.HOUSEHOLD, Sector.STORE)
