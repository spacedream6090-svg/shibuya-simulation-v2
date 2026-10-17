"""第 2 期 2-1 経済の段階 2: 口座の方法(``ops.transfer`` の ``method``)・段階 2 の組・保存則の検算(全登録)の単体の試験。

- 口座の方法: 世帯の脚は預金・銀行の決済の行(預金純増)を 1 行足す・世帯の現金は動かない(書き込み窓の外でも書ける)・
  検算①(四重記入)・検算②(純資産=実物資産)・その日の transfer の額の和=流れの表の和(1-9)が成り立つ。
- 段階 2 の組(``accounts.STAGE2_PAIRS``)は腕を挿した台帳だけで許す。
- 保存則の検算(``checks.conservation_check``): 登録の faucet − sink = 部門の残高の合計の変化・残差 0。登録の無い流れ・
  登録を 1 行外すと落ちる(負の対照)。
"""

from __future__ import annotations

import types

import numpy as np
import pytest

from shibuya.economy import checks as CK
from shibuya.economy import ops as OPS
from shibuya.economy.accounts import (
    FLOW_REGISTRY,
    STAGE2_PAIRS,
    AccountCode,
    BalanceLine,
    FlowKind,
    Sector,
    faucet_sink_table,
    flow_kind,
    flow_registry_table,
    is_allowed,
    registered_cells,
)
from shibuya.economy.ledger import Ledger
from shibuya.engine.ledger_api import TransferStatus

H, S, E, B, G, W = (int(s) for s in Sector)


def _led(n_h: int = 4, n_s: int = 2, n_e: int = 3) -> Ledger:
    led = Ledger(n_h, n_s, n_e)
    led.endow_households(np.full(n_h, 10_000), 0)
    led.endow_stores(np.full(n_s, 50_000), 0)
    return led


def _deposit(led: Ledger, who: np.ndarray, amt: np.ndarray) -> None:
    st = led.transfer_many(W, np.zeros(len(who), np.int64), H, np.asarray(who), np.asarray(amt),
                           int(AccountCode.CARRY_IN), 0, method=OPS.METHOD_ACCOUNT)
    assert (st == 0).all()


def _bal(led: Ledger, line: BalanceLine, s: int) -> np.ndarray:
    return np.asarray(led.balance(line, s), dtype=np.int64).copy()


def _attach(led: Ledger, parts=("wages",)) -> None:
    """段階 2 の腕を挿す(組み立ての物は試験の代役=部品と体の種別だけ)。段階 2 の組はこれで許される(検収 L1)。"""
    led.attach_stage2(types.SimpleNamespace(parts=tuple(parts), kinds=np.zeros(led.sizes[0], dtype=np.int64)))


# ================================================================= 口座の方法
def test_account_payee_puts_the_money_in_the_deposit_and_leaves_cash_alone():
    led = _led()
    cash0, dep0 = _bal(led, BalanceLine.CASH, H), _bal(led, BalanceLine.DEPOSIT, H)
    first = led.raw_position()
    _deposit(led, [0, 2], [7_000, 3_000])
    assert (_bal(led, BalanceLine.CASH, H) == cash0).all()
    assert list(_bal(led, BalanceLine.DEPOSIT, H) - dep0) == [7_000, 0, 3_000, 0]
    assert int(_bal(led, BalanceLine.CASH, B)[0]) == 10_000 and int(_bal(led, BalanceLine.LOAN, B)[0]) == 10_000
    # 2 行(本体 → 決済)・方法の列は 1・本体の科目は来街者持込・決済は預金純増(世帯 → 銀行)
    rows = led.raw_rows()
    assert led.raw_position() - first == 4
    meth = led.raw_methods()[-4:]
    tail = led.raw_rows()[-4:]
    assert list(meth) == [1, 1, 1, 1]
    assert [int(x) for x in tail[:, 6]] == [int(AccountCode.CARRY_IN)] * 2 + [int(AccountCode.DEPOSIT_NET)] * 2
    assert [(int(r[1]), int(r[3])) for r in tail[2:]] == [(H, B), (H, B)]
    assert rows.shape[1] == 7  # 生ログの 7 列は変えない(方法は別の列)


def test_account_payer_pays_from_the_deposit_with_a_settlement_row():
    led = _led()
    _deposit(led, [1], [5_000])
    cash0 = _bal(led, BalanceLine.CASH, H)
    s0 = _bal(led, BalanceLine.CASH, S)
    st = led.transfer_many(H, np.array([1]), S, np.array([0]), np.array([1_200]), int(AccountCode.CONSUMPTION), 3,
                           method=OPS.METHOD_ACCOUNT)
    assert list(st) == [0]
    assert (_bal(led, BalanceLine.CASH, H) == cash0).all()
    assert int(_bal(led, BalanceLine.DEPOSIT, H)[1]) == 3_800
    assert int(_bal(led, BalanceLine.CASH, S)[0] - s0[0]) == 1_200
    tail = led.raw_rows()[-2:]
    assert [int(x) for x in tail[:, 6]] == [int(AccountCode.DEPOSIT_NET), int(AccountCode.CONSUMPTION)]
    assert (int(tail[0, 1]), int(tail[0, 3])) == (B, H)  # 決済=銀行 → 世帯(引き落とし)が本体の前
    assert led.flow[B, H, int(AccountCode.DEPOSIT_NET)] == 1_200 and led.flow[H, S, int(AccountCode.CONSUMPTION)] == 1_200


def test_account_payer_short_of_deposit_is_refused_and_counted():
    led = _led()
    _deposit(led, [0], [500])
    before = led.rejections[int(TransferStatus.INSUFFICIENT_FUNDS)]
    st = led.transfer_many(H, np.array([0, 1]), S, np.array([0, 0]), np.array([800, 100]),
                           int(AccountCode.CONSUMPTION), 0, method=OPS.METHOD_ACCOUNT)
    assert list(st) == [int(TransferStatus.INSUFFICIENT_FUNDS)] * 2  # 0 は預金 500 < 800・1 は預金 0
    assert led.rejections[int(TransferStatus.INSUFFICIENT_FUNDS)] == before + 2


def test_account_rows_keep_all_the_checks():
    led = _led()
    _deposit(led, [0, 1, 2, 3], [9_000, 9_000, 9_000, 9_000])
    led.transfer_many(H, np.array([0, 3]), S, np.array([1, 1]), np.array([1_100, 2_200]), int(AccountCode.CONSUMPTION),
                      5, method=OPS.METHOD_ACCOUNT)
    led.transfer_many(H, np.array([2]), S, np.array([0]), np.array([300]), int(AccountCode.CONSUMPTION), 5)
    close = led.on_day_end(0)
    fc = CK.flow_matrix_balanced(led, close)
    assert fc.ok, fc.as_text()
    assert CK.net_worth_equals_real_assets(led).ok
    assert led.meter.last_day["flow_sum_ok"] is True
    cons = led.meter.last_day["conservation"]
    assert cons["ok"] is True and cons["residual"] == 0 and cons["unregistered"] == 0


def test_account_method_works_outside_the_household_cash_window():
    """世帯の現金(agents.money)が読み取り専用でも、口座の脚だけの transfer(賃金=日の締め)は書ける。"""
    led = Ledger(3, 1, 2)
    money = np.zeros(3, dtype=np.int32)
    led.attach_household_cash(money)
    money.flags.writeable = False
    _attach(led)  # 雇用主の原資(外界 → 雇用主)は段階 2 の組=腕を挿した台帳だけ
    led.transfer_many(W, np.array([0]), E, np.array([1]), np.array([50_000]), int(AccountCode.CONSUMPTION), 0)
    st = led.transfer_many(E, np.array([1, 1]), H, np.array([0, 2]), np.array([20_000, 30_000]),
                           int(AccountCode.WAGE), 0, method=OPS.METHOD_ACCOUNT)
    assert list(st) == [0, 0]
    assert list(money) == [0, 0, 0]
    assert list(_bal(led, BalanceLine.DEPOSIT, H)) == [20_000, 0, 30_000]
    with pytest.raises(ValueError, match="読み取り専用"):  # 現金の脚は窓の外では書けない(今のまま)
        led.transfer_many(W, np.array([0]), H, np.array([0]), np.array([1]), int(AccountCode.CARRY_IN), 0)


@pytest.mark.parametrize("code,ps,qs", [
    (AccountCode.DEPOSIT_NET, H, B),       # 預金純増そのものには使わない
    (AccountCode.ENTRY_CAPITAL, W, S),     # 世帯の無い組
])
def test_account_method_is_refused_where_it_has_no_meaning(code, ps, qs):
    led = _led()
    with pytest.raises(ValueError, match="口座の方法"):
        OPS.transfer(led, (ps, np.array([0])), (qs, np.array([0])), np.array([10]), OPS.what_of(code), None, 0,
                     method=OPS.METHOD_ACCOUNT)


def test_cash_method_writes_zero_in_the_method_column():
    led = _led()
    assert (led.raw_methods() == 0).all() and led.raw_methods().size == led.raw_rows().shape[0]


# ================================================================= 金の語・段階 2 の組
def test_extra_money_words_map_to_deposit_net_and_are_in_the_vocab():
    from shibuya.engine.events import vocab as V

    assert tuple(w.split(":", 1)[1] for w in OPS.MONEY_EXTRA_WHAT) == V.MONEY_EXTRA_WORDS
    assert all(c == AccountCode.DEPOSIT_NET for c in OPS.MONEY_EXTRA_WHAT.values())
    assert all(w in V.VOCAB_CODES for w in OPS.MONEY_EXTRA_WHAT)
    # 〔第 3 期 3-3〕その後ろに実験の族の 2 語(版 events-vocab/3-3)=金の 2 語のコードは 58・59 のまま
    # 〔第 2 期 2-3〕その後ろに体の出来事の 3 語(版 events-vocab/2-3)と過程の名 2 つ(経済の過程の名の位置は動かない)
    assert V.VOCAB[58:60] == ("金:引き出し", "金:カード") and V.VOCAB_VERSION == "events-vocab/2-3"
    assert V.ECONOMY_PROCESSES == ("payroll", "atm", "register") and V.CAUSE_PROCESS_NAMES[-5:-2] == V.ECONOMY_PROCESSES
    led = _led()
    _deposit(led, [0], [5_000])
    st = led.transfer_many(B, np.array([0]), H, np.array([0]), np.array([2_000]), int(AccountCode.DEPOSIT_NET), 0,
                           what="金:引き出し")
    assert list(st) == [0]
    with pytest.raises(ValueError, match="合わない"):
        led.transfer_many(W, np.array([0]), H, np.array([0]), np.array([1]), int(AccountCode.CARRY_IN), 0,
                          what="金:引き出し")


def test_stage2_pairs_are_allowed_only_on_an_attached_ledger():
    assert is_allowed(AccountCode.CONSUMPTION, Sector.ROW, Sector.EMPLOYER) is False
    assert is_allowed(AccountCode.CONSUMPTION, Sector.ROW, Sector.EMPLOYER, stage2=True) is True
    led = _led()
    st = led.transfer_many(W, np.array([0]), E, np.array([0]), np.array([10]), int(AccountCode.CONSUMPTION), 0)
    assert list(st) == [int(TransferStatus.FORBIDDEN_PAIR)]
    with pytest.raises(AttributeError):  # 〔検収 L1〕組を許す印は書けない(挿したかから導く)
        led._stage2_pairs = True
    _attach(led)
    st = led.transfer_many(W, np.array([0]), E, np.array([0]), np.array([10]), int(AccountCode.CONSUMPTION), 0)
    assert list(st) == [0]
    # faucet/sink 表: 既定は腕の無いランで許された組だけ(検収 L6)・stage2=True で段階 2 の組を末尾に足す
    rows = faucet_sink_table(stage2=True)
    assert rows[-len(STAGE2_PAIRS[AccountCode.CONSUMPTION]):] == tuple(
        ("消費支出", "外界", p, "FAUCET", "段階 2:expedient") for p in ("店舗", "雇用主"))
    assert faucet_sink_table() == faucet_sink_table(stage2=False) == rows[: -2]


# ================================================================= 保存則の検算(全登録)
def test_registry_kinds_follow_the_flow_kind_rule_and_are_consistent():
    cells = registered_cells()
    for f in FLOW_REGISTRY:
        assert f.kind == flow_kind(f.code, f.payer, f.payee), f.name
        assert cells[(int(f.code), int(f.payer), int(f.payee))] == f.kind
    names = [r[0] for r in flow_registry_table()]
    for need in ("初期の財布", "初期の預金", "参入資本(外界)", "来街者の持ち込みの口座の分(預け入れ)", "賃金の原資(雇用主の外界の売上)",
                 "消費税", "運賃", "補充の代金(域外仕入)"):
        assert need in names, need
    assert {f.stage for f in FLOW_REGISTRY} == {"1", "2"}


def test_conservation_check_passes_and_names_the_residual():
    led = _led()
    led.transfer_many(H, np.array([0]), S, np.array([0]), np.array([300]), int(AccountCode.CONSUMPTION), 0)
    led.transfer_many(S, np.array([0]), W, np.array([0]), np.array([100]), int(AccountCode.IMPORT_PURCHASE), 0)
    close = led.on_day_end(0)
    got = CK.conservation_check(close)
    assert set(got) == {"faucet", "sink", "internal", "unregistered", "delta_money", "residual", "residual_code", "ok"}
    assert got["ok"] and got["residual"] == 0
    assert got["faucet"] == 4 * 10_000 + 2 * 50_000 and got["sink"] == 100 and got["internal"] == 300
    assert got["delta_money"] == got["faucet"] - got["sink"]


def test_negative_an_unregistered_flow_fails_the_check():
    """負の対照: 登録の無い流れ(銀行 → 世帯の利子=貨幣供給量を増やす)を足すと検算が落ちる。"""
    led = _led()
    led.transfer_many(B, np.array([0]), H, np.array([1]), np.array([77]), int(AccountCode.INTEREST), 0)
    led.on_day_end(0)
    cons = led.meter.last_day["conservation"]
    assert cons["ok"] is False and cons["unregistered"] == 77 and cons["residual"] == 77


def test_negative_dropping_a_registered_cell_fails_the_check():
    led = _led()
    close = led.on_day_end(0)
    cells = dict(registered_cells())
    assert CK.conservation_check(close, cells)["ok"] is True
    cells.pop((int(AccountCode.ENTRY_CAPITAL), W, S))
    got = CK.conservation_check(close, cells)
    assert got["ok"] is False and got["unregistered"] == 2 * 50_000


def test_the_check_runs_without_the_arm_and_lands_in_the_day_record():
    led = _led()
    assert led.stage2 is None and led.credit is None and led._stage2_pairs is False
    led.on_day_end(0)
    assert led.meter.last_day["conservation"]["ok"] is True
    assert "stage2" not in led.meter.last_day
    assert "stage2" not in led.economy_record()
