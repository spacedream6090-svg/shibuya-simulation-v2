"""第 4 期 4-2b 給料日の台帳の動き(合成の台帳)と、合成の世界の 2 日のラン(腕 SHIBUYA_RULES_42B の on/off)。

- 給料日: 子ども・子育て拠出金は雇用主の分に足して「給与の天引き(雇用主 → 政府)」で移す・原資(外界 → 雇用主)=額面+
  雇用主の分・保存則の残差 0・4 本の流れの検算 0。70 歳以上は厚年と拠出金 0・75 歳以上は健保と支援金 0。
- 腕 off(``PayrollInputs.rules_42b=False``)=4-2 の値(雇用主の分 4 項目・計器に拠出金の鍵なし)。
- 再開: 見出しの ``rules_42b`` と今の腕が違えば止める。
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import types

import numpy as np
import pytest

from shibuya.economy import census as CS
from shibuya.economy import stage2 as S2
from shibuya.economy import taxes as TX
from shibuya.economy.accounts import AccountCode, Sector
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import Ledger
from shibuya.engine import economy_rules as ER
from shibuya.engine import economy_stage2 as ES2
from shibuya.engine.events import log as EV
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.run import run_day
from shibuya.world.state import World

H, S, E, B, G, W = (int(s) for s in Sector)
KINDS = np.array([0, 0, 2, 3, 0, 0])
AGES = np.array([45, 69, 70, 74, 75, 30], np.int16)


def _inputs(r42b=True) -> ER.PayrollInputs:
    n = AGES.size
    return ER.PayrollInputs(role_code=np.zeros(n, np.int16), role_vocab=("正社員",),
                            weekly_hours=np.full(n, 37.0, np.float32), employer_insured=np.full(n, 100, np.int32),
                            student=np.zeros(n, bool), age=AGES, source="試験", rules_42b=r42b)


def _plan(r42b=True, who=np.array([0, 1, 2, 3, 4, 5])):
    return types.SimpleNamespace(
        parts=S2.PARTS, kinds=KINDS, monthly_hours=None, hours_source="default", atms=None,
        cause=lambda name: EV.Process(name),
        date_of_step=lambda step: dt.date(2026, 8, 25), date_of=lambda day: dt.date(2026, 8, 25),
        is_payday=lambda day: True, close_step=lambda day: 1440 * int(day) + 1439,
        employment=lambda day: (who, np.full(who.size, E), np.array([0, 0, 1, 1, 2, 2])[: who.size]),
        record=lambda: {}, law=_inputs(r42b))


def _flow(led: Ledger, code: AccountCode, a: int, b: int) -> int:
    f = sum(np.asarray(x) for x in led.flow_daily) + np.asarray(led.flow)
    return int(f[a, b, int(code)])


def _payday(r42b):
    led = Ledger(6, 2, 3)
    led.attach_stage2(_plan(r42b))
    led.endow_households(np.full(6, 1_000), 0)
    led.on_day_end(0)
    gross = int(round(S2.DEFAULT_MONTHLY_HOURS * 1_226))  # 合成の組み立ての物=月 160 時間 × 最低賃金
    t = TX.payroll_tables("2026-08-25", r42b=r42b)
    want = TX.deductions(np.full(6, gross), t, TX.enrollment(_inputs(r42b), np.arange(6), t))
    return led, gross, want


def test_payday_moves_the_child_care_contribution_with_the_employer_share():
    led, gross, want = _payday(True)
    emp, er = want.employee_total, want.employer_total
    cc = want.employer["child_care_contribution"]
    assert cc.tolist()[:2] == [int(cc[0])] * 2 and int(cc[0]) > 0 and cc.tolist()[2:5] == [0, 0, 0]  # 70 歳以上は 0
    assert want.employer["health"].tolist()[4] == 0 and want.employer["pension"].tolist()[2] == 0
    # 4 本の流れの検算(賃金・本人 → 政府・雇用主 → 政府・原資)
    assert _flow(led, AccountCode.WAGE, E, H) == 6 * gross
    assert _flow(led, AccountCode.TAX, H, G) == int(emp.sum())
    assert _flow(led, AccountCode.TAX, E, G) == int(er.sum())
    assert _flow(led, AccountCode.CONSUMPTION, W, E) == 6 * gross + int(er.sum())
    day = led.meter.last_day
    assert day["conservation"]["ok"] is True and day["conservation"]["residual"] == 0
    assert day["conservation"]["unregistered"] == 0
    w = day["stage2"]["wages"]
    assert w["employer_child_care_contribution"] == int(cc.sum())
    assert sum(w[f"employer_{k}"] for k in TX.EMPLOYER_ITEMS) == w["employer_share_amount"] == int(er.sum())
    assert sum(w[f"employee_{k}"] for k in TX.EMPLOYEE_ITEMS) == w["employee_amount"] == int(emp.sum())
    assert w["enrolled_pension"] == 3 and w["enrolled_social"] == 5 and w["age_70_plus"] == 3 and w["age_75_plus"] == 1
    assert w["minors"] == 0 and w["resident_non_taxable"] == 0
    rec = led.stage2.s2_meter["rules"]["payroll_deductions"]
    assert rec["sources"]["child_care_contribution"].startswith("rules:child_care_contribution.rate")
    assert rec["age_max_exclusive"] == {"pension": 70, "health": 75}
    assert led.economy_record()["stage2"]["plan"]["rules_42b"] == "on"


def test_off_keeps_the_4_2_values_and_records():
    led, gross, want = _payday(False)
    w = led.meter.last_day["stage2"]["wages"]
    assert "employer_child_care_contribution" not in w and "enrolled_pension" not in w
    assert tuple(want.employer) == TX.EMPLOYER_ITEMS_42
    assert _flow(led, AccountCode.TAX, E, G) == int(want.employer_total.sum()) == w["employer_share_amount"]
    assert want.employee["pension"].tolist() == [want.employee["pension"].tolist()[0]] * 6  # 年齢の上限なし
    rec = led.stage2.s2_meter["rules"]["payroll_deductions"]
    assert set(rec) == {"asof", "sources"} and len(rec["sources"]) == 6
    assert "rules_42b" not in led.economy_record()["stage2"]["plan"]
    assert led.meter.last_day["conservation"]["ok"] is True


def test_on_minus_off_is_the_contribution_and_the_age_caps():
    _, _, on = _payday(True)
    _, _, off = _payday(False)
    d_er = on.employer_total - off.employer_total
    want = (on.employer["child_care_contribution"] - (off.employer["pension"] - on.employer["pension"])
            - (off.employer["health"] - on.employer["health"]) - (off.employer["child_support"] - on.employer["child_support"]))
    assert d_er.tolist() == want.tolist()


# ================================================================ 再開の見出し
def test_resume_refuses_a_different_rules_42b_arm(monkeypatch):
    monkeypatch.setattr(ES2, "_ARM", ES2.ARM_ON)
    monkeypatch.setattr(ER, "_ARM", ER.ARM_ON)
    monkeypatch.setattr(ER, "_ARM_42B", ER.ARM_ON)
    on = ES2.header_fields(types.SimpleNamespace(parts=ES2.PARTS, wage_model=ES2.wage_arm(), law=_inputs(True)))
    off = ES2.header_fields(types.SimpleNamespace(parts=ES2.PARTS, wage_model=ES2.wage_arm(), law=_inputs(False)))
    assert on["rules_42b"] == "on" and "rules_42b" not in off and off["rules_42"] == "on"
    ES2.check_resume(on)
    with pytest.raises(ValueError, match="空欄 3 件の腕"):
        ES2.check_resume(off)
    ER.set_arm_42b(ER.ARM_OFF)
    ES2.check_resume(off)
    with pytest.raises(ValueError, match="空欄 3 件の腕"):
        ES2.check_resume(on)


def test_the_arm_is_read_from_the_environment_name():
    assert ER.ENV_42B == "SHIBUYA_RULES_42B" and ER.DEFAULT_ARM_42B == ER.ARM_ON
    with pytest.raises(ValueError):
        ER.set_arm_42b("maybe")


# ================================================================ 合成の世界の 2 日(給料日 2026-08-25 をまたぐ)
N = 300


@pytest.fixture
def law(monkeypatch):
    monkeypatch.setattr(ES2, "_ARM", ES2.ARM_ON)
    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)
    monkeypatch.setattr(ES2, "_ATM_OVERRIDE", None)
    monkeypatch.setattr(ER, "_ARM", ER.ARM_ON)
    monkeypatch.setattr(ER, "_ARM_42B", ER.ARM_ON)
    return ER.set_arm_42b


def _run(sim_days: int = 2):
    world = World.synthetic(n_cells=64, seed=2)
    led = Ledger(N, world.n_poi)
    goods = GoodsLedger.from_pois(np.arange(world.n_poi) % 3, np.asarray(world.pois.stock),
                                  np.asarray(world.pois.price), n_agents=N)
    bundle = LedgerBundle(money=led, goods=goods, census=lambda d: CS.daily_census(led, goods, day=d))
    res = run_day(n_agents=N, seed=2, world=world, ticks=1_440, sim_days=sim_days, checkpoint_every=720,
                  ledger=bundle, start_sim_datetime="2026-08-24")
    return res, led


def test_two_synthetic_days_on_and_off(law):
    on, led_on = _run()
    law(ER.ARM_OFF)
    off, led_off = _run()
    r_on, r_off = led_on.stage2.s2_meter["run"]["wages"], led_off.stage2.s2_meter["run"]["wages"]
    assert led_on.stage2.law.rules_42b is True and led_off.stage2.law.rules_42b is False
    assert r_on["paid"] == r_off["paid"] > 0 and r_on["amount"] == r_off["amount"]
    # 合成の世界は加入の判定の材料なし=源泉と住民税だけ・住民税は基礎控除と調整控除と非課税の分だけ小さい
    assert r_on["employee_income_tax"] == r_off["employee_income_tax"]
    assert 0 <= r_on["employee_resident_tax"] < r_off["employee_resident_tax"]
    assert r_on["employer_share_amount"] == r_off["employer_share_amount"] == 0
    for res in (on, off):
        assert res.conserved
        for d in res.run_manifest_fields()["daily"]:
            c = d["economy"]["conservation"]
            assert c["ok"] is True and c["residual"] == 0 and c["unregistered"] == 0
    assert on.run_manifest_fields()["economy"]["stage2"]["plan"]["rules_42b"] == "on"
    assert "rules_42b" not in off.run_manifest_fields()["economy"]["stage2"]["plan"]
    # 給料日の前(1 日目)までは同じ=腕は天引きの額だけを変える
    assert on.llm_calls == off.llm_calls


def test_payroll_inputs_carry_the_arm_at_build_time(law):
    law(ER.ARM_OFF)
    assert ER.payroll_inputs(None, None, 3, np.zeros(3)).rules_42b is False
    law(ER.ARM_ON)
    inp = ER.payroll_inputs(None, None, 3, np.zeros(3))
    assert inp.rules_42b is True and "rules_42b" not in inp.record()  # 設定の節 plan.law は 4-2 のまま
    assert dataclasses.replace(inp, rules_42b=False).rules_42b is False


@pytest.mark.slow  # 合成 80 体・2 日・全部の刻みで段 B(約 5 分)
def test_stage_b_payday_has_no_undeclared_writes(law, monkeypatch):
    """段 B(系の前後で変わった欄 ⊆ 宣言・``SHIBUYA_SYSTEMS_CHECK=1``): 給料日(2026-08-25 の締め)を含む合成の 2 日で宣言の外 0。"""
    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "1")
    world = World.synthetic(n_cells=64, seed=2)
    n = 80
    led = Ledger(n, world.n_poi)
    goods = GoodsLedger.from_pois(np.arange(world.n_poi) % 3, np.asarray(world.pois.stock),
                                  np.asarray(world.pois.price), n_agents=n)
    bundle = LedgerBundle(money=led, goods=goods, census=lambda d: CS.daily_census(led, goods, day=d))
    res = run_day(n_agents=n, seed=2, world=world, ticks=1_440, sim_days=2, checkpoint_every=720, ledger=bundle,
                  start_sim_datetime="2026-08-24")
    w = led.stage2.s2_meter["run"]["wages"]
    assert w["paydays"] == 1 and w["paid"] > 0 and w["employee_amount"] > 0 and res.conserved
