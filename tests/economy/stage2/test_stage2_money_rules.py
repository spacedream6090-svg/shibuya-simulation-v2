"""第 2 期 2-1 経済の段階 2: 本人の判断の代役の規則(mock と古典=expedient)と口の単体の試験(組み立ての物は試験の代役)。

- 支払いの方法: 財布が足りれば現金・足りなければ口座・どちらも足りなければ今の結果コード(残高不足)のまま。
- レジの消費税: 税込の額 × 10/110 の切り捨てを店 → 政府(原因 ``Process("register")``)。
- 引き出し: 財布 < 1 日の消費 のとき・額=min(預金, 1 日の消費 × 3) の千円単位。預金が無ければ下ろさない。
- 運賃: IC(口座)が既定・口座が足りなければ現金(``RailProcess.pay_fares`` の口から)。
- 初期の預金: 来街者でない体=1 日の消費 × 30 日・来街者=持ち込み(初期の財布)の 0.5 を財布から預け入れ(visitors の部品のときだけ・合計は不変)。
"""

from __future__ import annotations

import datetime as dt
import types

import numpy as np
import pytest

from shibuya.economy import anchors as AN
from shibuya.economy import stage2 as S2
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.ledger import Ledger
from shibuya.engine.events import log as EV
from shibuya.engine.ledger_api import TransferStatus

H, S, E, B, G, W = (int(s) for s in Sector)
KINDS = np.array([0, 1, 3, 7])  # 通勤者・来街者・居住者・訪日来街者


def _plan(parts=S2.PARTS, kinds=KINDS):
    cal_day = dt.date(2026, 8, 24)
    return types.SimpleNamespace(
        parts=tuple(parts), kinds=kinds, monthly_hours=None, hours_source="default", atms=None,
        cause=lambda name: EV.Process(name), date_of_step=lambda step: cal_day, date_of=lambda day: cal_day,
        is_payday=lambda day: False, close_step=lambda day: 1439, employment=lambda day: (np.zeros(0),) * 3,
        record=lambda: {},
    )


def _led(parts=S2.PARTS, wallets=(1_000, 1_000, 1_000, 1_000)) -> Ledger:
    led = Ledger(len(wallets), 2, 2)
    led.attach_stage2(_plan(parts))
    led.endow_households(np.asarray(wallets), 0)
    led.endow_stores(np.full(2, 10_000), 0)
    return led


def _dep(led: Ledger) -> np.ndarray:
    return np.asarray(led.balance(BalanceLine.DEPOSIT, H), dtype=np.int64).copy()


def _cash(led: Ledger, s: int = H) -> np.ndarray:
    return np.asarray(led.balance(BalanceLine.CASH, s), dtype=np.int64).copy()


def test_initial_deposits_and_visitor_accounts():
    led = _led()
    daily = AN.daily_spending(KINDS)
    want = np.rint(daily * S2.DEPOSIT_DAYS).astype(np.int64)
    # 〔検収 L2〕来街者は持ち込み(=初期の財布 1,000)を分ける: 財布 × 0.5 を預け入れ=現金 500・預金 500(合計は不変)
    share = int(np.floor(1_000 * S2.VISITOR_ACCOUNT_SHARE))
    want[[1, 3]] = share
    assert list(_dep(led)) == list(want)
    assert list(_cash(led)) == [1_000, 1_000 - share, 1_000, 1_000 - share]
    assert list((_cash(led) + _dep(led))[[1, 3]]) == [1_000, 1_000]  # 来街者の合計(現金+預金)は持ち込みのまま
    run = led.stage2.s2_meter["run"]["endow"]
    assert run["visitor_rows"] == 2 and run["visitor_amount"] == 2 * share
    led2 = _led(parts=("wages", "withdraw", "payment", "tax"))  # visitors を止める=来街者の口座は 0・財布はそのまま
    assert list(_dep(led2)[[1, 3]]) == [0, 0] and list(_dep(led2)[[0, 2]]) == list(want[[0, 2]])
    assert list(_cash(led2)) == [1_000] * 4
    led.on_day_end(0)
    assert led.meter.last_day["conservation"]["ok"] is True


def test_payment_method_rule_and_register_tax():
    led = _led(wallets=(5_000, 100, 100, 4_000))  # 来街者 3 は 現金 2,000・預金 2,000 に分かれる
    dep0, cash0 = _dep(led), _cash(led)
    gov0 = int(_cash(led, G)[0])
    st = led.purchase_many(np.array([0, 2, 3]), np.array([0, 1, 1]), np.array([1_100, 1_100, 1_500]), 7)
    assert list(st) == [0, 0, 0]
    # 0: 財布 5,000 ≥ 1,100 → 現金・2: 財布 100 < 1,100 → 口座・3: 財布 2,000 ≥ 1,500 → 現金
    assert list(_cash(led) - cash0) == [-1_100, 0, 0, -1_500]
    assert list(dep0 - _dep(led)) == [0, 0, 1_100, 0]
    st = led.purchase_many(np.array([3]), np.array([1]), np.array([1_100]), 8)  # 財布 500 < 1,100 → 口座
    assert list(st) == [0]
    assert list(dep0 - _dep(led)) == [0, 0, 1_100, 1_100]
    tax = 100 + 100 + 136 + 100  # 税込 × 10/110 の切り捨て(1,500 → 136)
    assert int(_cash(led, G)[0]) - gov0 == tax
    m = led.stage2.s2_meter["run"]
    assert m["payment"]["cash_rows"] == 2 and m["payment"]["account_rows"] == 2 and m["tax"]["amount"] == tax
    led.on_day_end(0)
    assert led.meter.last_day["conservation"]["ok"] is True


def test_payment_falls_back_to_the_old_result_when_neither_suffices():
    led = _led(parts=("payment",), wallets=(100, 100, 100, 100))
    st = led.purchase_many(np.array([2]), np.array([0]), np.array([10_000_000]), 0)
    assert list(st) == [int(TransferStatus.INSUFFICIENT_FUNDS)]
    assert bool(led.can_pay_many(np.array([2]), np.array([10_000_000]))[0]) is False
    assert bool(led.can_pay_many(np.array([2]), np.array([5_000]))[0]) is True   # 口座で足りる
    led_off = _led(parts=("tax",), wallets=(100, 100, 100, 100))                 # payment を止める=現金だけ
    assert bool(led_off.can_pay_many(np.array([2]), np.array([5_000]))[0]) is False


def test_negative_deposit_short_card_falls_back_to_cash():
    """負の対照: 預金が足りなければカードでなく現金に戻る(財布で足りる額)。"""
    led = _led(parts=("payment",), wallets=(3_000, 3_000, 3_000, 3_000))
    # 来街者 1 は visitors を止めたので預金 0: 財布 3,000 < 4,000 で口座も 0 → 却下(今の結果コード)
    assert list(led.purchase_many(np.array([1]), np.array([0]), np.array([4_000]), 0)) == [
        int(TransferStatus.INSUFFICIENT_FUNDS)]
    # 財布が足りる額は現金(口座は使わない)
    dep0 = _dep(led)
    assert list(led.purchase_many(np.array([1]), np.array([0]), np.array([2_000]), 0)) == [0]
    assert list(_dep(led)) == list(dep0) and int(_cash(led)[1]) == 1_000


def test_withdraw_rule_amount_and_cause():
    log = EV.EventLog()
    led = _led(wallets=(1_000, 50_000, 999, 20_000))
    from shibuya.engine.events.links import MoneyEventLink

    led.attach_events(MoneyEventLink(log), step_seconds=60)
    dep0, cash0 = _dep(led), _cash(led)
    got = led.withdraw_many(np.array([0, 1, 2, 3, 0]), 5)
    daily = AN.daily_spending(KINDS)
    # 0: 財布 1,000 < 5,700 → min(預金 171,000, 17,100) を千円単位 → 17,000(2 度目の 0 は 1 回だけ)
    # 1: 来街者の財布 50,000 → 分けて 25,000 ≥ 14,200 → 下ろさない・2: 居住者 999 < 10,300 → 30,900 → 30,000・
    # 3: 訪日の持ち込み 20,000 → 財布 10,000 < 14,200 → min(預金 10,000, 42,600) → 10,000(検収 L2=持ち込みを分ける)
    assert list(got) == [17_000, 0, 30_000, 10_000, 0]
    assert list(_cash(led) - cash0) == [17_000, 0, 30_000, 10_000]
    assert list(dep0 - _dep(led)) == [17_000, 0, 30_000, 10_000]
    assert int(daily[0]) * 3 == 17_100
    whats = log.what_counts()
    assert whats.get("金:引き出し") == 3 and log.cause_counts().get("process", 0) >= 3
    m = led.stage2.s2_meter["run"]["withdraw"]
    assert m["count"] == 3 and m["amount"] == 57_000 and m["wallet_ok"] == 1


def test_withdraw_needs_a_deposit_and_the_part():
    led = _led(parts=("payment",), wallets=(10, 10, 10, 10))
    assert list(led.withdraw_many(np.array([0, 1]), 0)) == [0, 0]  # withdraw の部品が無い
    led2 = _led(parts=("withdraw",), wallets=(10, 10, 10, 10))
    got = led2.withdraw_many(np.array([1]), 0)  # 来街者(visitors を止めた)=預金 0
    assert list(got) == [0] and led2.stage2.s2_meter["run"]["withdraw"]["no_deposit"] == 1


def test_ic_fares_from_the_account_and_cash_fallback_through_the_rail_port():
    from shibuya.engine.processes.rail import RailProcess

    led = _led(parts=("payment",), wallets=(500, 500, 500, 500))  # visitors を止めた=来街者 1 の口座は 0
    stub = types.SimpleNamespace(n_fare_rejected=0)
    dep0, cash0 = _dep(led), _cash(led)
    st = RailProcess.pay_fares(stub, led, np.array([0, 1]), 170, 3)
    assert list(st) == [0, 0]
    assert int(dep0[0] - _dep(led)[0]) == 170 and int(cash0[0] - _cash(led)[0]) == 0  # IC
    assert int(cash0[1] - _cash(led)[1]) == 170  # 口座が足りない → 現金
    m = led.stage2.s2_meter["run"]["payment"]
    assert m["fare_ic_rows"] == 1 and m["fare_cash_rows"] == 1 and stub.n_fare_rejected == 0


def test_payroll_pays_into_the_account_with_exogenous_funding():
    led = Ledger(4, 2, 3)
    plan = _plan()
    plan.is_payday = lambda day: day == 1
    plan.employment = lambda day: (np.array([0, 2, 3]), np.array([E, E, S]), np.array([2, 2, 1]))
    led.attach_stage2(plan)
    led.endow_households(np.full(4, 1_000), 0)
    dep0 = _dep(led)
    led.on_day_end(0)
    assert list(_dep(led)) == list(dep0)  # 給料日でない
    led.on_day_end(1)
    pay = int(round(S2.DEFAULT_MONTHLY_HOURS * 1_226))
    assert list(_dep(led) - dep0) == [pay, 0, pay, pay]
    assert int(_cash(led, E)[2]) == 0 and int(_cash(led, S)[1]) == 0  # 原資は外界の売上=払う額と同じ(外生)
    day = led.meter.last_day
    assert day["conservation"]["ok"] is True and day["stage2"]["payday"] is True
    assert day["stage2"]["wages"]["paid"] == 3 and day["stage2"]["wages"]["funding"] == 3 * pay
    rules = led.stage2.s2_meter["rules"]["minimum_wage"]
    assert rules == {"asof": "2026-08-24", "yen_per_hour": 1_226, "source": "rules:minimum_wage.tokyo@2025-10-03"}


def test_payroll_part_off_pays_nothing():
    led = Ledger(4, 2, 3)
    plan = _plan(parts=("withdraw",))
    plan.is_payday = lambda day: True
    plan.employment = lambda day: (np.array([0]), np.array([E]), np.array([1]))
    led.attach_stage2(plan)
    led.on_day_end(0)
    assert int(led.flow_daily[-1][:, :, int(AccountCode.WAGE)].sum()) == 0


def test_attach_twice_is_refused_and_unknown_parts_are_refused():
    led = _led()
    with pytest.raises(ValueError, match="もう挿して"):
        led.attach_stage2(_plan())
    with pytest.raises(ValueError, match="部品"):
        Ledger(2, 1).attach_stage2(_plan(parts=("wages", "bonus")))
