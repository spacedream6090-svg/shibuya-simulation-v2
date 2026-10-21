"""第 4 期 4-2 給与の天引き(R-118 §2-6・§7-1・PENDING 仮-40 の Q4・Q7): 1 人の月の計算を手計算と突き合わせる。

手計算(額面 300,000 円・45 歳・週 37 時間・雇用主の被保険者 100 人・令和 8 年 8 月 25 日の給料日):

- 標準報酬月額: 健保 300,000(22 級 290,000〜310,000)・厚年 300,000(19 級)。
- 健保+介護 11.47%(9.85+1.62)=34,410 → 折半 17,205(本人)・17,205(雇用主)。支援金 0.23%=690 → 345・345。
  厚年 18.3%=54,900 → 27,450・27,450。雇用保険 本人 5/1,000=1,500・雇用主 8.5/1,000=2,550。
- 社会保険料等 46,500 → A=253,500。給与所得控除=253,500 × 30% + 6,667=82,717・基礎控除 48,334 → B=122,449 →
  × 5.105%=6,251.0 → 10 円未満の四捨五入=6,250。
- 住民税(〔検収 M1〕給与所得控除と社会保険料控除を入れた): 所得割の元=(300,000 − 給与所得控除 96,667 − 社会保険料 46,500)
  × 12=1,881,996 → × 10%=188,199 → +均等割 5,000=193,199 ÷ 12=16,099(1 円未満の切り捨て)。前(控除なし)は 30,416。
- 本人の分の合計 68,849・手取り 231,151・雇用主の分の合計 47,550。

源泉の特例の式と月額表(R-118 §1-2 #9 の 105,000〜107,000 円の区分=甲欄 扶養 0 人 170 円): 区分の下の端 105,000 円で
特例 130 円(差 40)・区分の中央 106,000 円で 180 円(差 10=答申の「中央で 0〜10 円」)。〔親の判断(問い 3)〕105,000 円未満は
月額表の甲欄どおり 0 円(特例の式なら 102,599 円から正)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.economy import taxes as TX
from shibuya.engine import economy_rules as ER

ASOF = "2026-08-25"


def _inputs(hours, age, insured=100, roles=None, student=None) -> ER.PayrollInputs:
    n = len(hours)
    vocab = ("パート・アルバイト", "業主", "正社員")
    rc = np.array([vocab.index(r) if r else -1 for r in (roles or ["正社員"] * n)], dtype=np.int16)
    return ER.PayrollInputs(role_code=rc, role_vocab=vocab, weekly_hours=np.asarray(hours, dtype=np.float32),
                            employer_insured=np.full(n, insured, np.int32) if np.ndim(insured) == 0
                            else np.asarray(insured, np.int32),
                            student=np.zeros(n, bool) if student is None else np.asarray(student, bool),
                            age=np.asarray(age, np.int16), source="試験")


def _ded(gross, inp):
    t = TX.payroll_tables(ASOF)
    g = np.asarray(gross, dtype=np.int64)
    return TX.deductions(g, t, TX.enrollment(inp, np.arange(g.size), t))


def test_one_person_month_matches_the_hand_calculation():
    d = _ded([300_000], _inputs([37.0], [45]))
    emp = {k: int(v[0]) for k, v in d.employee.items()}
    er = {k: int(v[0]) for k, v in d.employer.items()}
    assert emp == {"health": 17_205, "child_support": 345, "pension": 27_450, "employment": 1_500, "income_tax": 6_250,
                   "resident_tax": 16_099}
    assert er == {"health": 17_205, "child_support": 345, "pension": 27_450, "employment": 2_550}
    assert int(d.employee_total[0]) == 68_849 and 300_000 - 68_849 == 231_151
    assert int(d.employer_total[0]) == 47_550
    assert bool(d.enrollment.care[0]) and not bool(d.over_gross[0])


def test_the_care_rate_is_only_for_ages_40_to_64():
    d = _ded([300_000] * 4, _inputs([37.0] * 4, [39, 40, 64, 65]))
    h = d.employee["health"].tolist()
    assert h == [14_775, 17_205, 17_205, 14_775]  # 9.85% の折半=14,775・11.47% の折半=17,205


def test_special_formula_versus_the_monthly_table_bracket():
    t = TX.payroll_tables(ASOF)
    got = TX.income_tax_withholding(np.array([105_000, 106_000, 107_000 - 1]), t).tolist()
    table = 170  # 月額表 甲欄 105,000〜107,000 円未満・扶養 0 人(R-118 §1-2 #9・付属の行の note)
    assert got[0] == 130 and got[1] == 180
    assert abs(got[1] - table) <= 10  # 区分の中央の差は 0〜10 円(R-118 §2-6)
    assert max(abs(x - table) for x in got) <= 60  # 区分の端で最大 60 円(R-118 §0 の 4)
    # 〔親の判断(問い 3)〕105,000 円未満は月額表の甲欄どおり 0 円(特例の式なら 102,599 円から正=最大 130 円)
    assert TX.income_tax_withholding(np.array([0, 102_501, 102_599, 104_999]), t).tolist() == [0, 0, 0, 0]
    assert int(t.income_tax.params["kou_zero_below_yen"]) == 105_000


def test_the_50_sen_rule():
    # 50 銭以下は切り捨て・50 銭を超えれば切り上げ(額表の注)。額 = num / den
    assert TX.share_50sen(np.array([2_8565, 2_8566, 2_8564, 2_8500]), 10).tolist() == [2_856, 2_857, 2_856, 2_850]
    # 1 級 58,000 円・健保 9.85%=5,713.0 → 折半 2,856.5 → 2,856(雇用主 2,857)・支援金 133.4 → 66.7 → 67(雇用主 66)
    d = _ded([58_000], _inputs([37.0], [30]))
    assert int(d.employee["health"][0]) == 2_856 and int(d.employer["health"][0]) == 2_857
    assert int(d.employee["child_support"][0]) == 67 and int(d.employer["child_support"][0]) == 66


def test_enrollment_by_hours_employer_size_students_roles_and_missing_basis():
    hours = [37.0, 25.0, 25.0, 25.0, 15.0, 20.0, np.nan, 37.0]
    insured = [100, 60, 40, 60, 100, 60, 100, 100]
    student = [False, False, False, True, False, False, False, False]
    roles = ["正社員", "パート・アルバイト", "パート・アルバイト", "パート・アルバイト", "パート・アルバイト",
             "パート・アルバイト", "", "業主"]
    t = TX.payroll_tables(ASOF)
    en = TX.enrollment(_inputs(hours, [30] * 8, insured, roles, student), np.arange(8), t)
    assert en.social.tolist() == [True, True, False, False, False, True, False, False]
    assert en.employment.tolist() == [True, True, True, True, False, True, False, False]
    assert en.no_basis.tolist() == [False] * 6 + [True, False]
    assert en.taxed.tolist() == [True] * 7 + [False]  # 業主は雇われる側でない=何も天引きしない
    d = TX.deductions(np.full(8, 200_000), t, en)
    assert int(d.employee_total[7]) == 0 and int(d.employer_total[7]) == 0
    assert int(d.employee["income_tax"][6]) > 0 and int(d.employee["pension"][6]) == 0  # 材料なし=税だけ


def test_without_inputs_nothing_is_enrolled_but_taxes_apply():
    t = TX.payroll_tables(ASOF)
    en = TX.enrollment(None, np.arange(2), t)
    assert not en.social.any() and en.taxed.all()


def test_rows_not_in_force_give_zero():
    t = TX.payroll_tables("2026-05-25")  # 住民税の令和 8 年度の行は 6 月から
    assert int(TX.resident_tax_monthly(np.array([300_000]), t)[0]) == 0
    # 〔検収 L5〕雇用保険の率の適用期間(〜2027-03-31)の後は黙って 0 にせず止まる
    from shibuya.engine.rules import table as RT

    with pytest.raises(RT.RuleNotInForce):
        TX.payroll_tables("2027-04-25")


def test_social_insurance_over_the_gross_takes_nothing():
    d = _ded([10_000], _inputs([37.0], [45]))
    assert bool(d.over_gross[0]) and int(d.employee_total[0]) == 0 and int(d.employer_total[0]) == 0


def test_full_time_hours_are_the_same_in_engine_and_economy():
    assert ER.FULL_TIME_WEEKLY_HOURS == TX.FULL_TIME_BASE_HOURS * 3 / 4 == 30.0


@pytest.mark.parametrize("gross", [0, 1, 88_000, 1_500_000])
def test_employee_total_never_exceeds_gross(gross):
    d = _ded([gross], _inputs([37.0], [50]))
    assert 0 <= int(d.employee_total[0]) <= gross


def test_resident_tax_takes_the_two_deductions():
    """〔検収 M1〕所得割の元=額面 − 給与所得控除(別表第一)− 社会保険料(本人の分)の 12 か月分。"""
    t = TX.payroll_tables(ASOF)
    g = np.array([300_000, 300_000, 50_000])
    got = TX.resident_tax_monthly(g, t, social=np.array([46_500, 0, 0])).tolist()
    assert got[0] == (((300_000 - 96_667 - 46_500) * 12) // 10 + 5_000) // 12 == 16_099
    assert got[1] == (((300_000 - 96_667) * 12) // 10 + 5_000) // 12
    assert got[2] == 5_000 // 12  # 給与所得控除 54,167 円で所得割の元は 0=均等割だけ(非課税の限度は入れていない)


def test_outside_employer_rows_are_enrolled_as_full_time():
    """〔検収 M2〕材料の無い行でも外の雇用主の行は「51 人以上の事業所の正社員」とみなす。"""
    t = TX.payroll_tables(ASOF)
    inp = _inputs([np.nan, np.nan], [45, 30], insured=-1, roles=["", ""])
    en = TX.enrollment(inp, np.arange(2), t, assume_full_time=np.array([True, False]))
    assert en.social.tolist() == [True, False] and en.employment.tolist() == [True, False]
    assert en.care.tolist() == [True, False] and en.no_basis.tolist() == [False, True]


def test_lower_bound_rows_stop_before_the_bound():
    """〔検収 L5〕下限の印の行を下限より前に引くと止まる(施行の前の普通の行は None のまま)。"""
    from shibuya.engine.rules import table as RT

    with pytest.raises(RT.RuleNotInForce):
        TX.total_volume_cap("2020-01-01")
    with pytest.raises(RT.RuleNotInForce):
        TX.filing_deadline(2025)
    assert TX.payroll_tables("2025-12-25").income_tax is None  # 源泉の令和 8 年分の行は in_force=施行の前は無い
