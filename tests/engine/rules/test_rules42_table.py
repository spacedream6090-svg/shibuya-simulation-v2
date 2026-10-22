"""第 4 期 4-2 規則の表の中身(R-118 §7-1 の 4-3 に束ねる分・PENDING 仮-40 の Q2・Q6): 19 行+申告の期限の 1 行。

- 19 行は付属 ``v2-r118-rules-rows-draft.json`` の写し(id・kind・asof・出典・値。値は足した欄=健保と厚年の等級表・加入の範囲・
  雇用保険の時間の外は同じ)で、世界の時点 2026-07-13 にどれも効いている版が引ける。
- 形式の版 2: ``kind`` に ``norm``(罰則の無い決まり)・``asof_basis``(``lower_bound``=読んだ版の施行日を下限に置いた行=Q6)。
- 既存の 6 行の値(params)は不変。出典の版は §5 ② の 2 行だけ世界の時点の版に直した。表の sha は
  ``4dda40d8f83d6a3f``(4-2 の前)→ 4-2 の後の値(記録 rules42/README.md)。
- machine の行は読み手と一緒に入れた(``economy.taxes.READ_RULES``・最低賃金と標準税率は ``economy.anchors``)。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shibuya.engine.rules import table as RT

ROOT = Path(__file__).resolve().parents[3]
DRAFT = json.loads((ROOT / "docs/research/v2-r118-rules-rows-draft.json").read_text(encoding="utf-8"))
GRADES = json.loads((ROOT / "docs/research/v2-r118-standard-remuneration-grades.json").read_text(encoding="utf-8"))
R118 = (ROOT / "docs/research/v2-r118-rights-and-rules-contents.md").read_text(encoding="utf-8")
WORLD = "2026-07-13"
#: 4-2 で 19 行に足した値の欄(読み手が引く欄=答申の本文と付属の等級表から)。
ADDED_PARAMS = {
    # 〔第 4 期 4-2b〕年齢の上限と出典(R-118 §10-2)を健保と厚年の行に足した
    "health_insurance.kyoukai_tokyo": {"grades", "full_time_share", "short_time_coverage", "age_max_exclusive",
                                       "age_max_exclusive_source"},
    "pension.employees_rate": {"grades", "age_max_exclusive", "age_max_exclusive_source"},
    "employment_insurance.rate_general": {"min_weekly_hours"},
    "income_tax.withholding_monthly": {"kou_zero_below_yen"},  # 〔親の判断(問い 3)〕月額表の甲欄の 105,000 円未満 0 円
}
#: 4-2 の前の 6 行の値(params)=不変の確かめ。
OLD_PARAMS = {
    ("consumption_tax.standard_rate", "2019-10-01"): {"national_rate": 0.078, "local_tax_ratio": [22, 78],
                                                      "combined_rate": 0.1},
    ("minimum_wage.tokyo", "2024-10-01"): {"yen_per_hour": 1163, "area": "東京都"},
    ("minimum_wage.tokyo", "2025-10-03"): {"yen_per_hour": 1226, "area": "東京都"},
    ("minimum_wage.tokyo", "2026-10-01"): {"yen_per_hour": 1280, "area": "東京都"},
    ("late_night_alcohol.residential_ban", "2025-11-28"): {
        "business": "深夜における酒類提供飲食店営業(風営法 33 条 1 項)", "area": "住居集合地域", "closed_from": "00:00",
        "closed_until": "06:00"},
    ("labor.weekly_rest_day", "1947-09-01"): {"min_rest_days_per_week": 1,
                                              "applies_to_status": ["無期雇用者", "有期雇用者", "臨時雇用者"]},
}
LOWER_BOUND = {"food_business.licence", "building_lease.termination_notice", "labor.statutory_hours",
               "labor.overtime_premium", "road_use.police_permit", "outdoor_ad.tokyo_permit", "credit.total_volume_cap",
               "credit.interest_cap", "late_night_alcohol.residential_ban", "consumption_tax.filing_deadline",
               # 〔第 4 期 4-2b〕住民税の年度の始まり・年金機構の頁の年度の始まりを下限に置いた 4 行
               "resident_tax.basic_deduction", "resident_tax.adjustment_credit_tokyo_ward",
               "resident_tax.non_taxable_tokyo_ward", "child_care_contribution.rate"}


def _thaw(v):
    return RT._thaw(v)


def test_the_19_rows_are_the_draft_rows_and_in_force_on_the_world_date():
    rules = RT.default_rules()
    assert len(DRAFT["rules"]) == 19
    for d in DRAFT["rules"]:
        r = rules.get(d["id"], WORLD)
        assert r.asof == d["asof"] and r.kind == d["kind"], d["id"]
        assert [s.as_dict() for s in r.source] == d["source"], d["id"]
        got = _thaw(r.params)
        extra = set(got) - set(d["params"])
        assert extra == ADDED_PARAMS.get(d["id"], set()), d["id"]
        assert {k: got[k] for k in d["params"]} == d["params"], d["id"]
        # 〔検収 L8〕足した欄のある行は note の末尾に 1 文(付属の JSON の note はそのまま前に)
        if d["id"] in ADDED_PARAMS:
            assert r.note.startswith(d["note"]) and "付属の JSON の行に足した欄" in r.note[len(d["note"]):], d["id"]
        else:
            assert r.note == d["note"], d["id"]
        assert len(rules.versions(d["id"])) == 1
    assert len(rules) == 6 + 19 + 1 + 4 and len(rules.ids()) == 4 + 19 + 1 + 4  # 〔4-2b〕空欄 3 件の 4 行


def test_the_grade_tables_are_the_research_copies():
    rules = RT.default_rules()
    h = _thaw(rules.get("health_insurance.kyoukai_tokyo", WORLD).params)
    p = _thaw(rules.get("pension.employees_rate", WORLD).params)
    assert h["grades"] == GRADES["health_insurance"]["grades"] and len(h["grades"]) == 50
    assert p["grades"] == GRADES["pension"]["grades"] and len(p["grades"]) == 32
    # 加入の範囲は答申 §2-3(年金機構 #5)と行の note の値
    assert h["short_time_coverage"] == {"employer_min_insured": 51, "min_weekly_hours": 20, "students_excluded": True,
                                        "employer_min_insured_from_2027_10": 36}
    assert h["full_time_share"] == [3, 4]
    assert "51 人以上" in R118 and "36 人以上" in R118 and "週 20 時間以上" in R118 and "4 分の 3 未満" in R118
    assert _thaw(rules.get("employment_insurance.rate_general", WORLD).params)["min_weekly_hours"] == 20


def test_the_filing_deadline_row_is_from_r106_and_used_at_the_period_end():
    rules = RT.default_rules()
    with pytest.raises(RT.RuleNotInForce):
        rules.get("consumption_tax.filing_deadline", WORLD)  # 読んだ版(2026-10-01)が下限=世界の時点には無い
    r = rules.get("consumption_tax.filing_deadline", "2026-12-31")
    assert r.kind == "human" and r.asof_is_lower_bound  # 〔検収 L1〕人の手続き=human・移す機械の側はつなぎ
    assert _thaw(r.params) == {"corporation_due_months_after_period_end": 2, "sole_proprietor_period": "暦年",
                               "sole_proprietor_due_month": 3, "sole_proprietor_due_day": 31}
    r106 = (ROOT / "docs/research/v2-r106-rights-institutions-tax-credit.md").read_text(encoding="utf-8")
    assert "課税期間の末日の翌日から 2 か月以内(法人)。個人事業者は翌年 3 月 31 日" in r106


def test_existing_rows_keep_their_values():
    rules = RT.default_rules()
    for (rid, asof), params in OLD_PARAMS.items():
        r = [x for x in rules.versions(rid) if x.asof == asof]
        assert len(r) == 1 and _thaw(r[0].params) == params, rid


def test_the_two_rows_now_cite_the_world_date_versions():
    """R-118 §5 ②: 出典の版を世界の時点の版に(値は不変)。"""
    rules = RT.default_rules()
    tax = rules.get("consumption_tax.standard_rate", WORLD)
    assert [(s.law_id, s.version) for s in tax.source] == [("363AC0000000108", "2026-04-01"),
                                                           ("325AC0000000226", "2026-06-05")]
    rest = rules.get("labor.weekly_rest_day", WORLD)
    assert [(s.law_id, s.version) for s in rest.source] == [("322AC0000000049", "2026-06-24")]
    for s in (*tax.source, *rest.source):
        assert s.url.endswith(f"?asof={WORLD}") and s.retrieved == "2026-10-18"


def test_lower_bound_rows_are_marked():
    rules = RT.default_rules()
    marked = {r.id for r in rules if r.asof_is_lower_bound}
    assert marked == LOWER_BOUND
    # 印の根拠: 行の note が「下限」と書く 8 行+note が「asof は読んだ版(e-Gov の版)の施行日」と書く 2 行
    # (credit.interest_cap=平成 18 年改正の施行日・labor.overtime_premium=労基法の 2026-06-24 の版=どちらも条の施行の初日では
    # ない=Q6 で下限の印)
    for r in rules:
        if r.id in LOWER_BOUND:
            assert "下限" in r.note or r.asof == r.source[0].version, r.id
    d = rules.get("credit.total_volume_cap", WORLD).as_dict()
    assert d["asof_basis"] == "lower_bound" and RT.Rule.from_dict(d).asof_is_lower_bound
    d2 = rules.get("income_tax.withholding_monthly", WORLD).as_dict()
    assert "asof_basis" not in d2 and RT.Rule.from_dict(d2).asof_basis == RT.ASOF_IN_FORCE


def _src() -> RT.Source:
    return RT.Source(law="渋谷区安全で快適なまちづくりに関する条例", article="(例)", version="仮", url="https://example.invalid/x")


def test_norm_kind_and_schema_2(tmp_path):
    assert RT.SCHEMA == "shibuya.rules-table/2" and RT.KINDS == ("machine", "human", "norm")
    r = RT.Rule(id="street_drinking.shibuya_ban", kind=RT.KIND_NORM, source=(_src(),), asof="2026-01-01",
                params={"penalty": None})
    assert r.kind == "norm"
    p = tmp_path / "t.json"
    p.write_text(json.dumps({"schema": RT.SCHEMA, "rules": [r.as_dict()]}, ensure_ascii=False), encoding="utf-8")
    got = RT.load(p)
    assert got.get("street_drinking.shibuya_ban", "2026-07-13").kind == "norm"
    p.write_text(json.dumps({"schema": "shibuya.rules-table/1", "rules": [r.as_dict()]}, ensure_ascii=False),
                 encoding="utf-8")
    with pytest.raises(ValueError):
        RT.load(p)
    with pytest.raises(ValueError):
        RT.Rule(id="x.y", kind="norm", source=(_src(),), asof="2026-01-01", asof_basis="guess")


def test_every_machine_row_has_a_reader():
    """machine の行は読み手と一緒に(読み手の無い machine の行を残さない): economy.taxes が読む行と anchors の 2 行。"""
    from shibuya.economy import anchors as AN
    from shibuya.economy import taxes as TX

    machine = {r.id for r in RT.default_rules() if r.kind == RT.KIND_MACHINE}
    readers = set(TX.READ_RULES) | {AN.MIN_WAGE_RULE_ID, AN.CONSUMPTION_TAX_RULE_ID}
    assert machine == readers
    src = (ROOT / "src/shibuya/economy/taxes.py").read_text(encoding="utf-8")
    for rid in TX.READ_RULES + TX.BRIDGE_READ_RULES:
        assert f'"{rid}"' in src
    # 〔検収 L1〕つなぎで読む行は human だけ(つなぎの台帳 DOC-rules42-tax-remit-machine)
    assert {RT.default_rules().get(rid, "2026-12-31").kind for rid in TX.BRIDGE_READ_RULES} == {RT.KIND_HUMAN}
    with pytest.raises(ValueError):
        TX._bridge_row(TX.INCOME_TAX_RULE_ID, "2026-07-13")
    with pytest.raises(ValueError):
        TX._row(TX.DEADLINE_RULE_ID, "2026-12-31")


def test_r118_law_sources_match_the_research_table():
    """写し検査: R-118 の e-Gov の出典は答申 §1-1 の表の同じ行(law_id と 7-13 の版)にあり、URL は asof=2026-07-13。"""
    rows = {}
    for line in R118.splitlines():
        cells = [c.strip() for c in line.split("|")]
        if line.startswith("| ") and len(cells) > 4 and cells[2].isalnum() and len(cells[2]) == 15:
            rows[cells[2]] = cells[3]
    assert len(rows) == 21
    n = 0
    for r in RT.default_rules():
        for s in r.source:
            if s.law_id and s.url.endswith(f"?asof={WORLD}"):
                assert s.law_id in rows, (r.id, s.law_id)
                assert rows[s.law_id].startswith(s.version), (r.id, s.law_id, s.version, rows[s.law_id])
                assert s.url == f"https://laws.e-gov.go.jp/api/2/law_data/{s.law_id}?asof={WORLD}"
                n += 1
    assert n >= 20
