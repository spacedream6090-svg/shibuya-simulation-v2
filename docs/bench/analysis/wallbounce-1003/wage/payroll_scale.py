"""5,000 体ランの月の賃金の規模を試算する(推測・src は読むだけ)。

- 雇用関係 = W16 母集団の org_id(>=0)→ w6_org の行(業種 industry_key)。
- 月の賃金の単価 = 賃金構造基本統計調査 令和7年 参考表2 東京都・男女計の所定内給与額[千円/月]
  (一般労働者のみ・賞与と超過勤務を含まない)。業種の対応は industry_key → 大分類(本スクリプトの置き方)。
- 出力: 同じフォルダの payroll_scale_<体数>_s<seed>.json
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from shibuya.agents.population import load_population, sample_population

N = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 1
# 参考表2 東京都 男女計 所定内給与額[千円/月](data/calib/wage/chinkou_r7_sanko2_pref_industry_kibokei.xlsx の 13 東京の行)
TOKYO_SHOTEINAI = {"D": 442.6, "E": 420.4, "G": 423.9, "H": 390.4, "I": 438.6, "J": 514.7, "K": 414.1,
                   "L": 514.2, "M": 334.0, "N": 338.4, "O": 421.4, "P": 369.8, "Q": 396.2, "R": 317.5}
# industry_key(w6_org)→ 大分類(w6_org の industry 列の名前から本スクリプトが置いた対応)
KEY_TO_MAJOR = {"CN": "D", "MF": "E", "IT": "G", "TR": "H", "WR": "I", "FI": "J", "RE": "K", "PS": "L",
                "FB": "M", "LS": "N", "AM": "N", "ED": "O", "MW": "P", "CS": "Q", "SV": "R"}
STORE_KEYS = {"WR", "FB", "LS", "AM"}  # w6_org の wage_tier が「店員」の業種

pop = sample_population(load_population("data/world/v2", n=None, seed=SEED), N, SEED)
org = np.asarray(pop.org_id, dtype=np.int64)
keys = pq.read_table("data/world/v2/w6_org.parquet", columns=["industry_key"]).column("industry_key").to_pylist()
emp = org[org >= 0]
k = [keys[i] for i in emp]
cnt = Counter(k)
monthly = {kk: round(c * TOKYO_SHOTEINAI[KEY_TO_MAJOR[kk]] * 1000) for kk, c in cnt.items()}
out = {
    "n_agents": N, "seed": SEED,
    "n_employed_in_area": int(emp.size),
    "n_orgs_with_sampled_employee": int(np.unique(emp).size),
    "employees_per_org_in_run": dict(Counter(Counter(emp.tolist()).values())),
    "by_industry_key": {kk: {"n": c, "monthly_yen_guess": monthly[kk]} for kk, c in sorted(cnt.items())},
    "monthly_payroll_guess_total": int(sum(monthly.values())),
    "monthly_payroll_guess_store_orgs": int(sum(v for kk, v in monthly.items() if kk in STORE_KEYS)),
    "monthly_payroll_guess_office_orgs": int(sum(v for kk, v in monthly.items() if kk not in STORE_KEYS)),
    "n_store_org_employees": int(sum(c for kk, c in cnt.items() if kk in STORE_KEYS)),
}
Path(__file__).with_name(f"payroll_scale_{N}_s{SEED}.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(json.dumps(out, ensure_ascii=False))
