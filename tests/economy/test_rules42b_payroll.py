"""第 4 期 4-2b 規則の表の空欄 3 件を埋めた値(R-118 §10-2=親の一次確認)の天引きを手計算と突き合わせる。

手計算(額面 300,000 円・45 歳・週 37 時間・雇用主の被保険者 100 人・令和 8 年 8 月 25 日の給料日・扶養 0):

- 健保+介護 17,205・支援金 345・厚年 27,450・雇用保険 1,500・源泉所得税 6,250 は 4-2 と同じ(本人の社会保険料等 46,500)。
- 住民税: 合計所得=(300,000 − 給与所得控除 96,667)× 12=2,439,996(2,400 万円以下=基礎控除 430,000)。
  課税所得=2,439,996 − 社会保険料控除 558,000(46,500 × 12)− 430,000=1,451,996 → × 10%=145,199(1 円未満の切り捨て)。
  調整控除=課税所得 200 万円以下=min(50,000, 1,451,996)× 5%=2,500 → 所得割 142,699 → +均等割 5,000=147,699 ÷ 12=12,308
  (4-2 の値は 16,099)。
- 子ども・子育て拠出金(事業主だけ)=厚年の標準報酬 300,000 × 0.36%=1,080(本人 0)。
- 本人の分の合計 65,058(4-2 は 68,849)・手取り 234,942・雇用主の分の合計 48,630(4-2 は 47,550)。
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import numpy as np
import pytest

from shibuya.economy import taxes as TX
from shibuya.engine import economy_rules as ER
from shibuya.engine.rules import table as RT

ASOF = "2026-08-25"
ROOT = Path(__file__).resolve().parents[2]


def _inputs(hours, age, insured=100) -> ER.PayrollInputs:
    n = len(hours)
    return ER.PayrollInputs(role_code=np.zeros(n, np.int16), role_vocab=("正社員",),
                            weekly_hours=np.asarray(hours, dtype=np.float32), employer_insured=np.full(n, insured, np.int32),
                            student=np.zeros(n, bool), age=np.asarray(age, np.int16), source="試験")


def _ded(gross, age, *, r42b=True, asof=ASOF):
    t = TX.payroll_tables(asof, r42b=r42b)
    g = np.asarray(gross, dtype=np.int64)
    return TX.deductions(g, t, TX.enrollment(_inputs([37.0] * g.size, age), np.arange(g.size), t))


def _eid(g):
    t = TX.payroll_tables(ASOF)
    return TX._bands_value(np.asarray(g, dtype=np.int64), t.income_tax.params["employment_income_deduction"], ceil=True)


# ================================================================ 手計算
def test_one_person_month_matches_the_hand_calculation():
    d = _ded([300_000], [45])
    emp = {k: int(v[0]) for k, v in d.employee.items()}
    er = {k: int(v[0]) for k, v in d.employer.items()}
    total = (300_000 - 96_667) * 12
    assert int(_eid([300_000])[0]) == 96_667 and total == 2_439_996
    taxable = total - 46_500 * 12 - 430_000
    assert taxable == 1_451_996
    levy = taxable // 10 - min(50_000, taxable) * 5 // 100
    assert (levy + 5_000) // 12 == 12_308
    assert emp == {"health": 17_205, "child_support": 345, "pension": 27_450, "employment": 1_500, "income_tax": 6_250,
                   "resident_tax": 12_308}
    assert er == {"health": 17_205, "child_support": 345, "pension": 27_450, "employment": 2_550,
                  "child_care_contribution": 1_080}
    assert int(d.employee_total[0]) == 65_058 and 300_000 - 65_058 == 234_942
    assert int(d.employer_total[0]) == 48_630 == 47_550 + 1_080
    assert not bool(d.resident_exempt[0])


def test_off_reproduces_the_4_2_values():
    """腕 off(``r42b=False``)=4-2 の値(f27377a の手計算)・雇用主の分は 4 項目・記録に年齢の欄なし。"""
    d = _ded([300_000], [45], r42b=False)
    assert int(d.employee["resident_tax"][0]) == 16_099 and int(d.employee_total[0]) == 68_849
    assert tuple(d.employer) == TX.EMPLOYER_ITEMS_42 and int(d.employer_total[0]) == 47_550
    assert d.resident_exempt is None
    t = TX.payroll_tables(ASOF, r42b=False)
    assert set(t.record()) == {"asof", "sources"} and len(t.sources) == 6 and t.employer_items == TX.EMPLOYER_ITEMS_42
    # 70 歳・75 歳も 4-2 の値では加入のまま(年齢の上限なし)
    old = _ded([300_000] * 2, [70, 75], r42b=False)
    assert old.employee["pension"].tolist() == [27_450, 27_450] and old.employee["health"].tolist() == [14_775, 14_775]


# ================================================================ 住民税
def _rows(asof=ASOF):
    t = TX.payroll_tables(asof)
    return t.basic_deduction, t.adjustment_credit, t.non_taxable


def test_basic_deduction_bands_at_the_borders():
    bd, _, _ = _rows()
    totals = np.array([0, 24_000_000, 24_000_001, 24_500_000, 24_500_001, 25_000_000, 25_000_001, 60_000_000])
    assert TX._basic_deduction(totals, bd).tolist() == [430_000, 430_000, 290_000, 290_000, 150_000, 150_000, 0, 0]
    assert TX._basic_deduction(totals, None).tolist() == [0] * 8  # 行が無ければ 0


def test_adjustment_credit_border_and_floor():
    _, ac, _ = _rows()
    taxable = np.array([0, 12_345, 30_000, 50_000, 2_000_000, 2_000_001, 2_030_000, 5_000_000, 5_000_000, 5_000_000])
    total = np.array([0, 500_000, 600_000, 800_000, 3_000_000, 3_000_000, 3_000_000, 24_000_000, 25_000_000,
                      25_000_001])
    got = TX._adjustment_credit(total, taxable, ac).tolist()
    # 200 万円以下=min(5 万円, 課税所得)× 5%(1 円未満の切り捨て)・200 万円超=max(5 万円 − 超えた分, 5 万円)× 5%=2,500
    assert got[:4] == [0, 617, 1_500, 2_500]
    assert got[4:9] == [2_500] * 5
    assert got[9] == 0  # 合計所得 2,500 万円超は適用なし
    assert TX._adjustment_credit(total, taxable, None).tolist() == [0] * 10


def test_non_taxable_limits_and_minor():
    _, _, nt = _rows()
    total = np.array([450_000, 450_001, 1_350_000, 1_350_001, 1_000_000, 1_000_000, 1_000_000])
    age = np.array([45, 45, 17, 17, 18, -1, 0])
    assert TX.resident_non_taxable(total, age, nt).tolist() == [True, False, True, False, False, False, True]
    assert not TX.resident_non_taxable(total, age, None).any()


def test_non_taxable_end_to_end_both_levies_are_zero():
    """合計所得 45 万円以下は均等割も所得割も 0(境の上下を月の額面で)。未成年者は 135 万円以下で 0。"""
    t = TX.payroll_tables(ASOF)
    g = np.arange(80_000, 200_001, dtype=np.int64)
    total = np.maximum(g - _eid(g), 0) * 12
    lo = g[total <= 450_000].max()
    hi = g[total > 450_000].min()
    rt = TX.resident_tax_monthly(np.array([lo, hi]), t, social=np.zeros(2, np.int64), age=np.array([45, 45]))
    assert rt.tolist()[0] == 0 and rt.tolist()[1] >= 5_000 // 12
    lo_m = g[total <= 1_350_000].max()
    hi_m = g[total > 1_350_000].min()
    rt_m = TX.resident_tax_monthly(np.array([lo_m, hi_m, lo_m]), t, social=np.zeros(3, np.int64),
                                   age=np.array([17, 17, 18]))
    assert rt_m.tolist()[0] == 0 and rt_m.tolist()[1] > 0 and rt_m.tolist()[2] > 0


def test_resident_tax_is_zero_before_the_fiscal_year_row():
    t = TX.payroll_tables("2026-05-25")  # 住民税の令和 8 年度の行は 6 月から=控除の 3 行は引かない(下限の印でも止まらない)
    assert t.resident_tax is None and t.basic_deduction is None and t.non_taxable is None
    assert int(TX.resident_tax_monthly(np.array([300_000]), t)[0]) == 0


def test_rows_absent_from_the_table_give_zero():
    """表に 4-2b の行が無い写し(行の無い項目は 0=控除なし・非課税なし・拠出金 0・年齢の上限なし)。"""
    keep = [r for r in RT.default_rules() if r.id not in {TX.BASIC_DEDUCTION_RULE_ID, TX.ADJUSTMENT_RULE_ID,
                                                          TX.NON_TAXABLE_RULE_ID, TX.CHILD_CARE_RULE_ID}]
    rules = RT.Rules(keep)
    t = TX.payroll_tables(ASOF, rules)
    assert t.r42b and t.basic_deduction is None and t.child_care is None
    g = np.array([300_000])
    d = TX.deductions(g, t, TX.enrollment(_inputs([37.0], [45]), np.arange(1), t))
    assert int(d.employer["child_care_contribution"][0]) == 0
    base = (300_000 - 96_667) * 12 - 46_500 * 12
    assert int(d.employee["resident_tax"][0]) == (base // 10 + 5_000) // 12  # 4-2 の式と同じ額(控除の行が無い)


def test_child_care_row_before_its_lower_bound_stops():
    with pytest.raises(RT.RuleNotInForce):
        TX.payroll_tables("2025-03-25")  # 拠出金の行の asof 2025-04-01 は下限の印=前は分からない=止める


# ================================================================ 年齢の上限
def test_pension_stops_at_70_and_health_at_75():
    d = _ded([300_000] * 5, [64, 69, 70, 74, 75])
    assert d.employee["pension"].tolist() == [27_450, 27_450, 0, 0, 0]
    assert d.employer["pension"].tolist() == [27_450, 27_450, 0, 0, 0]
    assert d.employer["child_care_contribution"].tolist() == [1_080, 1_080, 0, 0, 0]
    assert d.employee["health"].tolist() == [17_205, 14_775, 14_775, 14_775, 0]  # 64 歳は介護あり
    assert d.employer["health"].tolist() == [17_205, 14_775, 14_775, 14_775, 0]
    assert d.employee["child_support"].tolist() == [345, 345, 345, 345, 0]
    assert d.employer["child_support"].tolist() == [345, 345, 345, 345, 0]
    assert d.employee["employment"].tolist() == [1_500] * 5  # 雇用保険は年齢の上限なし
    en = d.enrollment
    assert en.pension.tolist() == [True, True, False, False, False]
    assert en.social.tolist() == [True, True, True, True, False]
    t = TX.payroll_tables(ASOF)
    assert (t.pension_age_max, t.health_age_max) == (70, 75)
    assert t.record()["age_max_exclusive"] == {"pension": 70, "health": 75}


def test_unknown_age_stays_inside_the_caps():
    d = _ded([300_000], [-1])
    assert int(d.employee["pension"][0]) == 27_450 and int(d.employee["health"][0]) == 14_775


# ================================================================ 子ども・子育て拠出金
@pytest.mark.parametrize("gross", [58_000, 88_000, 93_000, 300_000, 620_000, 650_000, 1_000_000])
def test_child_care_contribution_is_the_pension_grade_times_rate_employer_only(gross):
    t = TX.payroll_tables(ASOF)
    d = _ded([gross], [45])
    std = int(TX.standard_monthly(np.array([gross]), t.pension_grades)[0])
    assert int(d.employer["child_care_contribution"][0]) == std * 36 // 10_000
    assert "child_care_contribution" not in d.employee  # 本人の分は無い
    off = _ded([gross], [45], r42b=False)
    for k in TX.EMPLOYEE_ITEMS[:4]:  # 社会保険の本人の分は拠出金で動かない
        assert int(d.employee[k][0]) == int(off.employee[k][0]), k
    assert int(d.employer_total[0]) - int(off.employer_total[0]) == std * 36 // 10_000


def test_child_care_contribution_is_not_the_child_support_levy():
    """子ども・子育て拠出金(0.36%・事業主だけ・厚年の標準報酬)と子ども・子育て支援金(0.23%・折半・健保の標準報酬)は別の行。"""
    t = TX.payroll_tables(ASOF)
    assert t.child_care.id == "child_care_contribution.rate" and t.child_support.id == "child_support_levy.rate"
    assert float(t.child_care.params["rate"]) == 0.0036 and float(t.child_care.params["employee_share"]) == 0
    assert float(t.child_support.params["rate"]) == 0.0023 and float(t.child_support.params["employee_share"]) == 0.5
    d = _ded([1_000_000], [45])  # 健保の標準報酬 980,000・厚年の標準報酬 650,000(上限)
    assert int(d.employer["child_care_contribution"][0]) == 650_000 * 36 // 10_000 == 2_340
    assert int(d.employee["child_support"][0]) + int(d.employer["child_support"][0]) == 980_000 * 23 // 10_000


# ================================================================ 全体
@pytest.mark.parametrize("gross", [0, 1, 50_000, 88_000, 91_668, 300_000, 1_500_000, 3_000_000])
@pytest.mark.parametrize("age", [17, 45, 70, 80])
def test_employee_total_never_exceeds_gross(gross, age):
    d = _ded([gross], [age])
    assert 0 <= int(d.employee_total[0]) <= gross


def test_no_hard_coded_ages_or_amounts_in_the_reader():
    """AST: 年齢の上限・控除の額・率・限度は規則の表から(読み手の taxes.py に直書きが無い)。"""
    src = (ROOT / "src/shibuya/economy/taxes.py").read_text(encoding="utf-8")
    banned = {70, 75, 18, 430_000, 290_000, 150_000, 50_000, 2_000_000, 24_000_000, 24_500_000, 25_000_000, 450_000,
              1_350_000, 0.0036, 0.02, 0.03, 0.05, 36}
    found = [n.value for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Constant)
             and isinstance(n.value, (int, float)) and not isinstance(n.value, bool) and n.value in banned]
    assert found == []
    for rid in (TX.BASIC_DEDUCTION_RULE_ID, TX.ADJUSTMENT_RULE_ID, TX.NON_TAXABLE_RULE_ID, TX.CHILD_CARE_RULE_ID):
        assert rid in TX.READ_RULES and f'"{rid}"' in src


def test_the_rows_are_the_r118_10_2_values():
    """写し検査: 表の値は R-118 §10-2 の表の値(43/29/15 万円・2,400/2,450/2,500 万円・5%・200 万円・2,500 円・45 万円・
    135 万円・70 歳・75 歳・0.36%)。"""
    r118 = (ROOT / "docs/research/v2-r118-rights-and-rules-contents.md").read_text(encoding="utf-8")
    sec = r118.split("### §10-2", 1)[1]
    for s in ("2,400 万円以下 43 万円", "2,450 万円以下 29 万円", "2,500 万円以下 15 万円", "2,500 万円超は 0",
              "200 万円", "2,500 円未満は 2,500 円", "扶養なしは 45 万円", "135 万円以下", "七十歳未満", "七十五歳以上",
              "千分の三・六", "0.36%"):
        assert s in sec, s
    rules = RT.default_rules()
    bd = RT._thaw(rules.get(TX.BASIC_DEDUCTION_RULE_ID, ASOF).params)["bands"]
    assert [(b["total_income_to_incl"], b["deduction_yen"]) for b in bd] == [
        (24_000_000, 430_000), (24_500_000, 290_000), (25_000_000, 150_000), (None, 0)]
    ac = RT._thaw(rules.get(TX.ADJUSTMENT_RULE_ID, ASOF).params)
    assert (ac["rate_metro"], ac["rate_ward"], ac["taxable_income_threshold_yen"], ac["floor_base_yen"],
            ac["not_applied_total_income_over_yen"], ac["personal_deduction_difference_no_dependents_yen"]) == (
        0.02, 0.03, 2_000_000, 50_000, 25_000_000, 50_000)
    nt = RT._thaw(rules.get(TX.NON_TAXABLE_RULE_ID, ASOF).params)
    assert (nt["no_dependents_total_income_max_yen"], nt["special_total_income_max_yen"], nt["minor_age_below"]) == (
        450_000, 1_350_000, 18)
    assert rules.get(TX.PENSION_RULE_ID, ASOF).params["age_max_exclusive"] == 70
    assert rules.get(TX.HEALTH_RULE_ID, ASOF).params["age_max_exclusive"] == 75
    cc = rules.get(TX.CHILD_CARE_RULE_ID, ASOF)
    assert cc.kind == "machine" and cc.asof == "2025-04-01" and cc.asof_is_lower_bound
    for rid in (TX.BASIC_DEDUCTION_RULE_ID, TX.ADJUSTMENT_RULE_ID, TX.NON_TAXABLE_RULE_ID):
        r = rules.get(rid, ASOF)
        assert r.kind == "machine" and r.asof == "2026-06-01" and r.asof_is_lower_bound
    # 年齢の上限の出典(欄の隣)=§10-2 の条と読んだ版
    for rid, laws in ((TX.PENSION_RULE_ID, ("厚生年金保険法",)),
                      (TX.HEALTH_RULE_ID, ("健康保険法", "高齢者の医療の確保に関する法律"))):
        src = RT._thaw(rules.get(rid, ASOF).params)["age_max_exclusive_source"]
        assert tuple(s["law"] for s in src) == laws
        for s in src:
            # 〔検収 低 1〕親は asof なしで条を指して読んだ=URL は ?elm=MainProvision-Article_<条>・版は文(施行日と取得日)
            m = re.search(r"(\d{4}-\d{2}-\d{2}) 施行の版\(2026-10-22 取得\)$", s["version"])
            assert m and s["law"] in sec and f"{m.group(1)} 施行の版" in sec
            assert re.match(rf"^https://laws\.e-gov\.go\.jp/api/2/law_data/{s['law_id']}\?elm=MainProvision-Article_\d+$",
                            s["url"]), s["url"]
