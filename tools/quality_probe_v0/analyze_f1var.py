# -*- coding: utf-8 -*-
"""analyze_f1var.py — ① v0/v1変種の追試を集計(指標Bの制約半分)。
入力: results/quality_ledger.csv(原本 main 行) + results_f1var/quality_ledger_f1var.csv(v0/v1 行)
出力: Markdown(stdout)。違反率 main/v0/v1・対応ありΔ(v1−v0)のブートストラップ95%CI・不一致対の数・場面別の行動表・gold(F1-08)・過剰拒否(F1-04)。
"""
import csv, sys, os, random, statistics, collections
here = os.path.dirname(os.path.abspath(__file__))
old = os.path.join(here, "results", "quality_ledger.csv")
new = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "results_f1var", "quality_ledger_f1var.csv")
rows = list(csv.DictReader(open(old, encoding="utf-8"))) + list(csv.DictReader(open(new, encoding="utf-8")))
rows = [r for r in rows if r["family"] == "1"]
def var_of(r):
    pid = r["probe_id"]
    if pid.endswith("v0"): return "v0"
    if pid.endswith("v1"): return "v1"
    return "main"
def base_of(r): return r["probe_id"][:5]
models = sorted(set(r["model"] for r in rows))
random.seed(20260906)
print("| モデル | 違反率 main | 違反率 v0 | 違反率 v1 | Δ(v1−v0) 対応ありbootstrap 95%CI | 不一致対(v0≠v1の違反) | 行動一致 v0/v1 | gold F1-08 v0/v1 | 過剰拒否 F1-04 v0/v1 | prompt_tokens v0/v1 |")
print("|---|---|---|---|---|---|---|---|---|---|")
detail = []
for m in models:
    R = {v: {base_of(r): r for r in rows if r["model"] == m and var_of(r) == v} for v in ("main", "v0", "v1")}
    ids = sorted(set(R["v0"]) & set(R["v1"]))
    if not ids:
        print("| %s | (v0/v1 未測定) |" % m); continue
    viol = {v: {i: int(float(R[v][i]["n_violations"] or 0) > 0) for i in ids if i in R[v]} for v in R}
    rate = {v: (sum(viol[v].values()) / len(viol[v]) if viol[v] else float("nan")) for v in R}
    d = [viol["v1"][i] - viol["v0"][i] for i in ids]
    boots = []
    for _ in range(4000):
        s = [random.choice(d) for _ in d]; boots.append(sum(s) / len(s))
    boots.sort(); lo, hi = boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots)) - 1]
    disc = sum(1 for x in d if x != 0)
    agree = sum(1 for i in ids if (R["v0"][i]["action"] or "") == (R["v1"][i]["action"] or ""))
    g = lambda v: (R[v]["F1-08"]["gold_ok"] if "F1-08" in R[v] else "-")
    o = lambda v: (R[v]["F1-04"]["over_refusal"] if "F1-04" in R[v] else "-")
    pt = lambda v: round(statistics.mean(int(R[v][i]["prompt_tokens"]) for i in ids if R[v][i].get("prompt_tokens")))
    print("| %s | %.3f | %.3f | %.3f | %+.3f [%+.3f, %+.3f] | %d/%d | %d/%d | %s/%s | %s/%s | %d/%d |" % (
        m, rate["main"], rate["v0"], rate["v1"], sum(d) / len(d), lo, hi, disc, len(ids), agree, len(ids), g("v0"), g("v1"), o("v0"), o("v1"), pt("v0"), pt("v1")))
    for i in ids:
        detail.append((m, i, R["main"].get(i, {}).get("action", ""), R["v0"][i]["action"], R["v1"][i]["action"],
                       R["v0"][i]["violations"], R["v1"][i]["violations"]))
print("\n場面別(行動 main/v0/v1・違反 v0/v1):\n")
print("| モデル | 場面 | main | v0 | v1 | 違反v0 | 違反v1 |\n|---|---|---|---|---|---|---|")
for t in detail:
    print("| %s | %s | %s | %s | %s | %s | %s |" % t)
