"""第 4 期 4-2 給与の天引きと店の預かり消費税(Q1)の台帳の動き(合成の台帳・組み立ての物は試験の代役)。

- 給料日: 雇用主 → 世帯の口座に額面・世帯の口座 → 政府に本人の分・雇用主 → 政府に雇用主の分・原資(外界 → 雇用主)は
  額面+雇用主の分。外の雇用主の体は外界が額面を払い本人の分だけ政府へ。保存則の残差 0(合成の 2 日)。
- 消費税: レジの税は店の預かり金に積む(政府は受け取らない)→ 申告の期限(2027-03-31)の日の締めに店 → 政府。店の現金が
  足りなければ移せない=残り、次の日に移す。積んだ − 移した = 残高(検算)。
- 組み立ての物に ``law`` が無い(腕 off)ときは 4-2 の前の値(天引き 0・税は売った時点で政府へ)。
"""

from __future__ import annotations

import datetime as dt
import types

import numpy as np

from shibuya.economy import stage2 as S2
from shibuya.economy import taxes as TX
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.checks import tax_deposit_check
from shibuya.economy.ledger import Ledger
from shibuya.engine import economy_rules as ER
from shibuya.engine.events import log as EV

H, S, E, B, G, W = (int(s) for s in Sector)
KINDS = np.array([0, 0, 2, 3])


def _inputs(n=4) -> ER.PayrollInputs:
    return ER.PayrollInputs(role_code=np.zeros(n, np.int16), role_vocab=("正社員",),
                            weekly_hours=np.full(n, 37.0, np.float32), employer_insured=np.full(n, 100, np.int32),
                            student=np.zeros(n, bool), age=np.array([45, 30, 45, 30][:n], np.int16), source="試験")


def _plan(*, law=True, dates=None, payday=None, employment=None, parts=S2.PARTS):
    dates = dates or {}
    return types.SimpleNamespace(
        parts=tuple(parts), kinds=KINDS, monthly_hours=None, hours_source="default", atms=None,
        cause=lambda name: EV.Process(name),
        date_of_step=lambda step: dates.get(int(step) // 1440, dt.date(2026, 8, 24)),
        date_of=lambda day: dates.get(int(day), dt.date(2026, 8, 24)),
        is_payday=(lambda day: False) if payday is None else payday, close_step=lambda day: 1440 * int(day) + 1439,
        employment=(lambda day: (np.zeros(0),) * 3) if employment is None else employment,
        record=lambda: {}, law=_inputs() if law else None,
    )


def _cash(led: Ledger, s: int) -> np.ndarray:
    return np.asarray(led.balance(BalanceLine.CASH, s), dtype=np.int64).copy()


def _dep(led: Ledger, s: int = H) -> np.ndarray:
    return np.asarray(led.balance(BalanceLine.DEPOSIT, s), dtype=np.int64).copy()


def _flow(led: Ledger, code: AccountCode, a: int, b: int) -> int:
    f = sum(np.asarray(x) for x in led.flow_daily) + np.asarray(led.flow)
    return int(f[a, b, int(code)])


def test_payday_deducts_the_employee_share_and_pays_the_employer_share():
    led = Ledger(4, 2, 3)
    led.attach_stage2(_plan(payday=lambda day: day == 1,
                            employment=lambda day: (np.array([0, 2, 3]), np.array([E, E, S]), np.array([2, 2, 1]))))
    led.endow_households(np.full(4, 1_000), 0)
    dep0 = _dep(led)
    led.on_day_end(0)
    led.on_day_end(1)
    s2 = led.stage2
    gross = int(round(S2.DEFAULT_MONTHLY_HOURS * 1_226))  # 合成の組み立ての物=賃金の腕 w17 の道(月 160 時間 × 最低賃金)
    t = TX.payroll_tables("2026-08-24")
    want = TX.deductions(np.full(3, gross), t, TX.enrollment(_inputs(), np.array([0, 2, 3]), t))
    emp, er = want.employee_total, want.employer_total
    assert list(_dep(led) - dep0) == [gross - int(emp[0]), 0, gross - int(emp[1]), gross - int(emp[2])]
    assert _flow(led, AccountCode.WAGE, E, H) == 2 * gross and _flow(led, AccountCode.WAGE, S, H) == gross
    assert _flow(led, AccountCode.TAX, H, G) == int(emp.sum())
    assert _flow(led, AccountCode.TAX, E, G) == int(er[:2].sum()) and _flow(led, AccountCode.TAX, S, G) == int(er[2])
    assert _flow(led, AccountCode.CONSUMPTION, W, E) == 2 * gross + int(er[:2].sum())  # 原資=額面+雇用主の分
    assert int(_cash(led, E)[2]) == 0 and int(_cash(led, S)[1]) == 0
    day = led.meter.last_day
    assert day["conservation"]["ok"] is True and day["conservation"]["residual"] == 0
    w = day["stage2"]["wages"]
    assert w["employee_amount"] == int(emp.sum()) and w["employer_share_amount"] == int(er.sum())
    assert w["net_amount"] == 3 * gross - int(emp.sum()) and w["enrolled_social"] == 3 and w["enrolled_care"] == 2
    assert sum(w[f"employee_{k}"] for k in TX.EMPLOYEE_ITEMS) == w["employee_amount"]
    assert sum(w[f"employer_{k}"] for k in TX.EMPLOYER_ITEMS) == w["employer_share_amount"]
    assert s2.s2_meter["rules"]["payroll_deductions"]["sources"]["income_tax"].startswith("rules:income_tax")


def test_outside_employer_pays_gross_from_the_outside_and_only_the_employee_share():
    led = Ledger(4, 2, 3)
    led.attach_stage2(_plan(payday=lambda day: True,
                            employment=lambda day: (np.array([1]), np.array([E]), np.array([S2.OUTSIDE_EMPLOYER_ORG]))))
    led.endow_households(np.full(4, 1_000), 0)
    led.on_day_end(0)
    gross = int(round(S2.DEFAULT_MONTHLY_HOURS * 1_226))
    assert _flow(led, AccountCode.WAGE, W, H) == gross
    assert _flow(led, AccountCode.TAX, H, G) > 0 and _flow(led, AccountCode.TAX, E, G) == 0
    w = led.meter.last_day["stage2"]["wages"]
    assert w["outside_employer_share_not_recorded"] > 0
    assert led.meter.last_day["conservation"]["ok"] is True


def _shop_led(dates) -> Ledger:
    led = Ledger(4, 2, 2)
    led.attach_stage2(_plan(dates=dates))
    led.endow_households(np.full(4, 50_000), 0)
    led.endow_stores(np.full(2, 10_000), 0)
    return led


def test_register_tax_goes_to_the_deposit_and_to_the_government_at_the_deadline():
    dates = {0: dt.date(2026, 8, 24), 1: dt.date(2027, 3, 30), 2: dt.date(2027, 3, 31), 3: dt.date(2027, 4, 1)}
    led = _shop_led(dates)
    gov0, store0 = int(_cash(led, G)[0]), _cash(led, S)
    st = led.purchase_many(np.array([0, 2, 3]), np.array([0, 1, 1]), np.array([1_100, 1_100, 1_500]), 7)
    assert list(st) == [0, 0, 0]
    tax = 100 + 100 + 136
    assert int(_cash(led, G)[0]) == gov0  # 政府は受け取らない
    assert list(_cash(led, S) - store0) == [1_100, 2_600]  # 店の現金は税込みのまま(預かり金を含む)
    dep = led.stage2.tax_deposit
    assert dep.held_total() == tax and dep.held[2026].tolist() == [100, 236]
    assert list(led.last_purchase_tax(3)) == [100, 100, 136]
    assert led.stage2.register_tax() == tax
    led.on_day_end(0)
    led.on_day_end(1)
    assert int(_cash(led, G)[0]) == gov0 and dep.held_total() == tax  # 期限の前の日
    led.on_day_end(2)
    assert int(_cash(led, G)[0]) - gov0 == tax and dep.held_total() == 0 and dep.held == {}
    assert _flow(led, AccountCode.TAX, S, G) == tax
    day = led.meter.last_day
    assert day["conservation"]["ok"] is True
    assert day["stage2"]["tax"]["remitted"] == tax and day["stage2"]["tax"]["held_balance"] == 0
    assert day["stage2"]["tax"]["deposit_check"]["ok"] is True
    rec = led.economy_record()["stage2"]["tax"]["deposit"]
    assert rec["collected"] == tax and rec["remitted"] == tax and rec["held"] == 0
    assert led.economy_record()["stage2"]["plan"]["rules_42"] == "on"


def test_a_short_store_pays_later_and_the_check_holds():
    dates = {0: dt.date(2026, 12, 30), 1: dt.date(2027, 3, 31), 2: dt.date(2027, 4, 1)}
    led = _shop_led(dates)
    led.purchase_many(np.array([0]), np.array([0]), np.array([11_000]), 7)  # 税 1,000
    dep = led.stage2.tax_deposit
    # 店 0 の現金を減らす(補充の代金=域外仕入=登録の sink)
    led.transfer_many(S, np.array([0]), W, np.array([0]), np.array([20_500]), int(AccountCode.IMPORT_PURCHASE), 8)
    led.on_day_end(0)
    led.on_day_end(1)
    assert dep.held_total() == 1_000 and dep.totals["unpaid_rows"] == 1
    assert led.meter.last_day["stage2"]["tax"]["deposit_check"]["ok"] is True
    led.endow_stores(np.array([5_000, 0]), 1440 * 2)
    led.on_day_end(2)
    assert dep.held_total() == 0 and dep.totals["remitted"] == 1_000
    assert tax_deposit_check(dep.totals["collected"], dep.totals["remitted"], dep.held_total())["residual"] == 0


def test_without_law_the_old_values_are_kept():
    led = Ledger(4, 2, 2)
    led.attach_stage2(_plan(law=False))
    led.endow_households(np.full(4, 50_000), 0)
    led.endow_stores(np.full(2, 10_000), 0)
    gov0 = int(_cash(led, G)[0])
    led.purchase_many(np.array([0]), np.array([0]), np.array([1_100]), 7)
    assert int(_cash(led, G)[0]) - gov0 == 100 and led.stage2.tax_deposit is None
    ded, table = S2.payroll_deductions(np.array([200_000]), "2026-08-25")
    assert list(ded) == [0] and table is None


def test_two_synthetic_days_conserve_with_law():
    dates = {0: dt.date(2026, 8, 24), 1: dt.date(2026, 8, 25)}
    led = Ledger(4, 2, 3)
    led.attach_stage2(_plan(dates=dates, payday=lambda day: day == 1,
                            employment=lambda day: (np.array([0, 1, 2, 3]), np.array([E, E, S, E]),
                                                    np.array([0, 1, 0, 2]))))
    led.endow_households(np.full(4, 30_000), 0)
    led.endow_stores(np.full(2, 10_000), 0)
    for day in (0, 1):
        led.purchase_many(np.array([0, 1]), np.array([0, 1]), np.array([2_200, 3_300]), 1440 * day + 10)
        led.on_day_end(day)
        c = led.meter.last_day["conservation"]
        assert c["ok"] is True and c["residual"] == 0 and c["unregistered"] == 0
        assert led.meter.last_day["stage2"]["tax"]["deposit_check"]["residual"] == 0
