"""4-2b: 給料日を含む 2 日のラン(08-24 から・5,000 体・1 本ずつ)の動いた量・体ごとの検算・性能を 1 つの JSON に(使い捨て)。

    python runs_rules42b.py <out.json> [--config w6_v3_default] [--stop N --state DIR] [--verify]

PYTHONPATH で src を選ぶ(作業木の src か f27377a の写しの src)・腕は環境変数 ``SHIBUYA_RULES_42B``・記録は ``SHIBUYA_EVENTS``。

- 給料日の天引きの入力と結果を ``economy.stage2.payroll_deductions`` の口で控える(額は変えない)。
- ``--verify``(腕 on): 控えた行ごとに、規則の表の JSON を直に読んだ別の実装(Python の整数・行ごと=分析の道具の中だけ)で
  本人の分 6 項目と雇用主の分 5 項目を出し直し、食い違いの行の数を数える(加入の材料の判定=4-2 のコードの判定は使う・年齢の
  上限・控除・非課税・拠出金はこの道具の中で出し直す)。
- ``--stop N --state DIR``: 刻み N で止めて状態を書き、そこから再開したランの final を出す(通しとの比べは記録の側)。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[6]
W2 = REPO / "docs/bench/analysis/wave2-2026-09-30/wave2_bytecheck.py"
sys.path.insert(0, str(REPO / "docs/bench/analysis/wallbounce-1012/pop43/tools"))
from runs_pop43 import _peak_working_set_bytes  # noqa: E402

CAPTURE: list[dict] = []


def _install_capture() -> None:
    from shibuya.economy import stage2 as S2

    real = S2.payroll_deductions

    def wrapped(gross, asof, *, inputs=None, agents=None, assume_full_time=None):  # noqa: ANN001
        tot, ded = real(gross, asof, inputs=inputs, agents=agents, assume_full_time=assume_full_time)
        if inputs is not None and ded is not None:
            CAPTURE.append({"gross": np.asarray(gross, dtype=np.int64).copy(), "asof": str(asof),
                            "agents": np.asarray(agents, dtype=np.int64).copy(),
                            "outside": None if assume_full_time is None else np.asarray(assume_full_time, bool).copy(),
                            "inputs": inputs, "ded": ded})
        return tot, ded

    S2.payroll_deductions = wrapped


# ================================================================ 規則の表を直に読む別の実装(行ごと・整数)
def _rules_json() -> dict:
    import shibuya

    root = Path(shibuya.__file__).resolve().parents[2]
    return json.loads((root / "docs/design/rules-table.json").read_text(encoding="utf-8"))


def _row(tab: dict, rid: str, day: str) -> dict | None:
    vs = sorted((r for r in tab["rules"] if r["id"] == rid and r["asof"] <= day), key=lambda r: r["asof"])
    return vs[-1]["params"] if vs else None


def _fr(x) -> Fraction:  # noqa: ANN001
    return Fraction(str(x))


def _std(g: int, grades: list) -> int:
    for gr in grades:
        if g >= gr["from_incl"] and (gr["to_excl"] is None or g < gr["to_excl"]):
            return int(gr["standard"])
    return int(grades[0]["standard"])


def _half(base: int, rate: Fraction) -> tuple[int, int]:
    p, q = rate.numerator, rate.denominator
    full = base * p
    d = 2 * q
    emp = full // d + (1 if 2 * (full - (full // d) * d) > d else 0)
    return emp, max(full // q - emp, 0)


def _band(x: int, bands: list, ceil: bool) -> int:
    for b in bands:
        if x >= b["from"] and (b["to"] is None or x <= b["to"]):
            if "fixed" in b:
                return int(b["fixed"])
            if "amount" in b:
                return int(b["amount"])
            r = _fr(b["rate"])
            v = -((-x * r.numerator) // r.denominator) if ceil else (x * r.numerator) // r.denominator
            return v + int(b["add"])
    return 0


def _withholding(a: int, it: dict) -> int:
    x = max(a, 0)
    if x < it["kou_zero_below_yen"]:
        return 0
    b = max(x - _band(x, it["employment_income_deduction"], True) - _band(x, it["basic_deduction"], True), 0)
    for band in it["tax_on_taxable"]:
        if b >= band["from"] and (band["to"] is None or b <= band["to"]):
            r = _fr(band["rate"])
            q = r.denominator
            num = b * r.numerator - band["minus"] * q
            return max(((num + 5 * q) // (10 * q)) * 10, 0)
    return 0


def _resident(g: int, si: int, age: int, day: str, tab: dict, it: dict) -> tuple[int, bool]:
    rt = _row(tab, "resident_tax.special_collection_tokyo_ward", day)
    if rt is None or g <= 0:
        return 0, False
    bd = _row(tab, "resident_tax.basic_deduction", day)
    ac = _row(tab, "resident_tax.adjustment_credit_tokyo_ward", day)
    nt = _row(tab, "resident_tax.non_taxable_tokyo_ward", day)
    total = max(g - _band(g, it["employment_income_deduction"], True), 0) * 12
    basic = 0
    for b in bd["bands"]:
        if b["total_income_to_incl"] is None or total <= b["total_income_to_incl"]:
            basic = b["deduction_yen"]
            break
    taxable = max(total - si * 12 - basic, 0)
    rate = _fr(rt["income_levy_rate_metro"]) + _fr(rt["income_levy_rate_ward"])
    levy = taxable * rate.numerator // rate.denominator
    diff, th = ac["personal_deduction_difference_no_dependents_yen"], ac["taxable_income_threshold_yen"]
    base = min(diff, taxable) if taxable <= th else max(diff - (taxable - th), ac["floor_base_yen"])
    cr = _fr(ac["rate_metro"]) + _fr(ac["rate_ward"])
    credit = 0 if total > ac["not_applied_total_income_over_yen"] else base * cr.numerator // cr.denominator
    levy = max(levy - credit, 0)
    exempt = total <= nt["no_dependents_total_income_max_yen"] or (
        0 <= age < nt["minor_age_below"] and total <= nt["special_total_income_max_yen"])
    if exempt:
        return 0, True
    annual = levy + rt["per_capita_metro_yen"] + rt["per_capita_ward_yen"] + rt["forest_environment_tax_yen"]
    return annual // 12, False


def _verify(cap: dict, tab: dict) -> dict:
    """控えた 1 回の給料日の行ごとの出し直しと食い違いの数。"""
    from shibuya.economy import taxes as TX

    day = cap["asof"][:10]
    g_all, agents, inp, ded = cap["gross"], cap["agents"], cap["inputs"], cap["ded"]
    # 加入の材料の判定(時間・役割・学生・被保険者の数)は 4-2 のコードの判定=年齢の上限なしの値を基にする
    t_old = TX.payroll_tables(day, r42b=False)
    base_en = TX.enrollment(inp, agents, t_old, assume_full_time=cap["outside"])
    hi, cs, pe = _row(tab, "health_insurance.kyoukai_tokyo", day), _row(tab, "child_support_levy.rate", day), \
        _row(tab, "pension.employees_rate", day)
    ei, it, cc = _row(tab, "employment_insurance.rate_general", day), _row(tab, "income_tax.withholding_monthly", day), \
        _row(tab, "child_care_contribution.rate", day)
    ages = np.asarray(inp.age, dtype=np.int64)[agents]
    bad = {k: 0 for k in (*TX.EMPLOYEE_ITEMS, *(f"er_{k}" for k in TX.EMPLOYER_ITEMS))}
    exempt_n = 0
    emp_sum = er_sum = 0
    for i in range(g_all.size):  # 分析の道具の中の行ごとの出し直し(エンジンの逐次ループではない)
        g, age = int(max(g_all[i], 0)), int(ages[i])
        basis = bool(base_en.social[i])
        social = basis and age < hi["age_max_exclusive"]
        pension = basis and age < pe["age_max_exclusive"]
        e, r = {k: 0 for k in TX.EMPLOYEE_ITEMS}, {k: 0 for k in TX.EMPLOYER_ITEMS}
        if social:
            hstd = _std(g, hi["grades"])
            rate = _fr(hi["rate"]) + (_fr(hi["care_rate_age_40_64"]) if 40 <= age <= 64 else 0)
            e["health"], r["health"] = _half(hstd, rate)
            e["child_support"], r["child_support"] = _half(hstd, _fr(cs["rate"]))
        if pension:
            pstd = _std(g, pe["grades"])
            e["pension"], r["pension"] = _half(pstd, _fr(pe["rate"]))
            c = _fr(cc["rate"])
            r["child_care_contribution"] = pstd * c.numerator // c.denominator
        if bool(base_en.employment[i]):
            re_, rr = _fr(ei["employee_rate"]), _fr(ei["employer_rate"])
            num, den = g * re_.numerator, re_.denominator
            e["employment"] = num // den + (1 if 2 * (num - (num // den) * den) > den else 0)
            r["employment"] = g * rr.numerator // rr.denominator
        si = e["health"] + e["child_support"] + e["pension"] + e["employment"]
        over = si > g
        taxed = bool(base_en.taxed[i]) and not over
        if taxed:
            e["income_tax"] = _withholding(g - si, it)
            rt, ex = _resident(g, si, age, day, tab, it)
            exempt_n += int(ex)
            e["resident_tax"] = min(rt, max(g - si - e["income_tax"], 0))
        if over:
            e = {k: 0 for k in e}
            r = {k: 0 for k in r}
        for k in TX.EMPLOYEE_ITEMS:
            bad[k] += int(e[k] != int(ded.employee[k][i]))
        for k in TX.EMPLOYER_ITEMS:
            bad[f"er_{k}"] += int(r[k] != int(ded.employer[k][i]))
        emp_sum += sum(e.values())
        er_sum += sum(r.values())
    outside = cap["outside"] if cap["outside"] is not None else np.zeros(g_all.size, bool)
    pos = g_all > 0
    basis = np.asarray(base_en.social, bool)
    return {
        "asof": day, "rows": int(g_all.size), "mismatch_rows_by_item": bad, "mismatch_total": int(sum(bad.values())),
        "recomputed_employee_total": int(emp_sum), "recomputed_employer_total": int(er_sum),
        "code_employee_total": int(ded.employee_total.sum()), "code_employer_total": int(ded.employer_total.sum()),
        "code_employee_total_paid_rows": int(ded.employee_total[pos].sum()),
        "code_employer_total_inside_paid_rows": int(ded.employer_total[pos & ~outside].sum()),
        "code_employer_total_outside_paid_rows": int(ded.employer_total[pos & outside].sum()),
        "child_care_total": int(np.asarray(ded.employer["child_care_contribution"]).sum()),
        "child_care_rows": int((np.asarray(ded.employer["child_care_contribution"]) > 0).sum()),
        "resident_exempt_recomputed": exempt_n,
        "resident_exempt_code": int(np.asarray(ded.resident_exempt).sum()) if ded.resident_exempt is not None else None,
        "age_dist": {"unknown": int((ages < 0).sum()), "lt18": int(((ages >= 0) & (ages < 18)).sum()),
                     "18_39": int(((ages >= 18) & (ages < 40)).sum()), "40_64": int(((ages >= 40) & (ages < 65)).sum()),
                     "65_69": int(((ages >= 65) & (ages < 70)).sum()), "70_74": int(((ages >= 70) & (ages < 75)).sum()),
                     "75_plus": int((ages >= 75).sum())},
        "affected": {"pension_age_out": int((basis & (ages >= pe["age_max_exclusive"])).sum()),
                     "health_age_out": int((basis & (ages >= hi["age_max_exclusive"])).sum()),
                     "minors_paid": int((pos & (ages >= 0) & (ages < 18)).sum())},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--config", default="w6_v3_default")
    ap.add_argument("--stop", type=int, default=0)
    ap.add_argument("--state", default="")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    spec = importlib.util.spec_from_file_location("wave2_bytecheck", W2)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck"] = mod
    spec.loader.exec_module(mod)
    kw = dict(mod.configs()[args.config])
    kw.update(sim_days=2, start_sim_datetime="2026-08-24")
    import shibuya
    from shibuya import cli
    from shibuya.economy.accounts import AccountCode, BalanceLine, Sector

    _install_capture()
    t0 = time.perf_counter()
    if args.stop:
        first = cli.run(n_agents=5_000, seed=1, world_dir="data/world/v2", state_out=args.state,
                        stop_at_tick=args.stop, **kw)
        res = cli.run(n_agents=5_000, seed=1, world_dir="data/world/v2",
                      resume_from=str(Path(args.state) / first.resume["state_files"][-1]["file"]), **kw)
    else:
        res = cli.run(n_agents=5_000, seed=1, world_dir="data/world/v2", **kw)
    wall = time.perf_counter() - t0
    peak = _peak_working_set_bytes()
    led = res.ledger.money
    s2 = led.stage2
    f = sum(np.asarray(x) for x in led.flow_daily)

    def fl(code, a, b):  # noqa: ANN001
        return int(f[int(a), int(b), int(code)])

    H, S, E, G, W = Sector.HOUSEHOLD, Sector.STORE, Sector.EMPLOYER, Sector.GOVERNMENT, Sector.ROW
    run = s2.s2_meter["run"]
    m = res.run_manifest_fields()
    days = [{"day": d["day"], "conservation": d["economy"]["conservation"],
             "deposit_check": d["economy"]["stage2"]["tax"].get("deposit_check")} for d in m["daily"]]
    st = m["economy"]["stage2"]
    doc = {
        "config": args.config, "rules_42b": os.environ.get("SHIBUYA_RULES_42B", "(既定)"),
        "events": os.environ.get("SHIBUYA_EVENTS", "(既定)"), "resume_stop": args.stop or None,
        "final": res.final_hash[:16], "final_full": res.final_hash,
        "src_is_worktree": Path(shibuya.__file__).resolve().parents[1] == (REPO / "src").resolve(),
        "checkpoints_behavior": [c.behavior_hash[:16] for c in res.checkpoints],
        "checkpoints_full": [c.full_hash[:16] for c in res.checkpoints],
        "llm_calls": int(res.llm_calls), "wall_s": round(wall, 1), "peak_rss_bytes": peak,
        "run_wall_s": round(float(getattr(res, "wall_seconds", 0.0) or 0.0), 2),
        "wages": {k: int(v) for k, v in run["wages"].items()},
        "flows": {"wage_E_H": fl(AccountCode.WAGE, E, H), "wage_S_H": fl(AccountCode.WAGE, S, H),
                  "wage_W_H": fl(AccountCode.WAGE, W, H), "funding_W_E": fl(AccountCode.CONSUMPTION, W, E),
                  "funding_W_S": fl(AccountCode.CONSUMPTION, W, S), "tax_H_G": fl(AccountCode.TAX, H, G),
                  "tax_E_G": fl(AccountCode.TAX, E, G), "tax_S_G": fl(AccountCode.TAX, S, G)},
        "government_cash": int(np.asarray(led.balance(BalanceLine.CASH, G))[0]),
        "household_deposit_total": int(np.asarray(led.balance(BalanceLine.DEPOSIT, H)).sum()),
        "rules": {k: v for k, v in s2.s2_meter["rules"].items() if k in ("payroll_deductions",)},
        "plan_rules_42b": st["plan"].get("rules_42b"),
        "days": days, "conserved": bool(res.conserved),
        "phase_seconds": {k: round(float(v), 2) for k, v in (res.phase_seconds or {}).items()
                          if isinstance(v, (int, float))},
        "paydays_captured": len(CAPTURE),
    }
    if args.verify and CAPTURE:
        tab = _rules_json()
        doc["verify"] = [_verify(c, tab) for c in CAPTURE]
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                              newline="\n")
    print(doc["final"], doc["wall_s"], doc["flows"], doc.get("verify", [{}])[0].get("mismatch_total"))


if __name__ == "__main__":
    main()
