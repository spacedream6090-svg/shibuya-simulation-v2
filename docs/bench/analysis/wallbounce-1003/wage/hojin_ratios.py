"""法人企業統計(年次別・時系列 0003060791)から手元資金の比率を出す(読むだけ・推測なし)。

入力: data/calib/wage/hojin_nenji_fy2023_2025_cash_sales_labor.csv(e-Stat getSimpleStatsData)
出力: 同じフォルダの hojin_ratios_fy2025.json

比率の定義(本スクリプトの置き方・出典は表の値そのもの)
- 人件費 = 役員給与 + 役員賞与 + 従業員給与 + 従業員賞与 + 福利厚生費(財務総研の定義と同じ足し方)
- 現金・預金 / 月の人件費 [月] = 現金・預金(期末) ÷ (人件費 ÷ 12)
- 現金・預金 / 月商 [月]       = 現金・預金(期末) ÷ (売上高 ÷ 12)
- 1 人あたり人件費[円/月]      = 人件費 ÷ 期中平均従業員数 ÷ 12(役員分を含む点に注意)
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SRC = ROOT / "data/calib/wage/hojin_nenji_fy2023_2025_cash_sales_labor.csv"
YEAR = sys.argv[1] if len(sys.argv) > 1 else "2025年度"
rows = list(csv.reader(SRC.open(encoding="utf-8")))
start = next(i for i, r in enumerate(rows) if r and r[0] == "cat01_code") + 1
v = defaultdict(dict)
units = {}
for r in rows[start:]:
    if len(r) < 10 or r[7] != YEAR:
        continue
    try:
        val = float(r[9])
    except ValueError:
        continue
    v[(r[3], r[5])][r[1]] = val
    units[r[1]] = r[8]
LABOR = ["役員給与(当期末)", "役員賞与(当期末)", "従業員給与(当期末)", "従業員賞与(当期末)", "福利厚生費(当期末)"]
out = {"source_table": "e-Stat 0003060791 法人企業統計調査 時系列データ 金融業、保険業以外の業種(原数値)",
       "year": YEAR, "units": units, "rows": []}
for (ind, size), d in sorted(v.items()):
    if "現金・預金(当期末流動資産)" not in d or not all(k in d for k in LABOR) or "売上高(当期末)" not in d:
        continue
    labor = sum(d[k] for k in LABOR)
    cash = d["現金・預金(当期末流動資産)"]
    sales = d["売上高(当期末)"]
    emp = d.get("期中平均従業員数(当期末)")
    out["rows"].append({
        "industry": ind, "size": size,
        "cash_mil": cash, "sales_mil": sales, "labor_mil": labor,
        "cash_months_of_labor": round(cash / (labor / 12), 2) if labor else None,
        "cash_months_of_sales": round(cash / (sales / 12), 2) if sales else None,
        "labor_share_of_sales": round(labor / sales, 4) if sales else None,
        "labor_per_employee_yen_month": round(labor * 1e6 / emp / 12) if emp else None,
        "employees": emp,
    })
dst = Path(__file__).with_name(f"hojin_ratios_{YEAR.replace('年度', '')}.json")
dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
pick = {"全産業（除く金融保険業）", "情報通信業", "卸売業", "小売業", "飲食サービス業", "宿泊業", "生活関連サービス業",
        "娯楽業", "不動産業", "その他の学術研究、専門・技術サービス業", "広告業", "建設業", "製造業", "医療、福祉業",
        "教育、学習支援業", "その他のサービス業", "運輸業、郵便業(集約)", "職業紹介・労働者派遣業"}
for r in out["rows"]:
    if r["industry"] in pick:
        print(r["industry"], r["size"], "現金/月人件費", r["cash_months_of_labor"], "現金/月商", r["cash_months_of_sales"],
              "人件費/売上", r["labor_share_of_sales"], "1人月", r["labor_per_employee_yen_month"], "units", units.get("期中平均従業員数(当期末)"))
