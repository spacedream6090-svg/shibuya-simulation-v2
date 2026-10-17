"""R-109 A9 (iv): 令和2年国勢調査 第4表(東京都・従業地・通学地)から、渋谷区で従業・通学する人の
常住地(都道府県・市区町村)の分布を集計する。読むだけ。

入力: data/research_cache/r109/census2020_t04_13_workplace_by_residence.xlsx
      (e-Stat statInfId 000032214352・e04-13-01.xlsx・R-109 で取得)
出力: data/research_cache/r109/r109_census_inflow.json
実行: python docs/research/scripts/r109/r109_census_inflow.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "data/research_cache/r109/census2020_t04_13_workplace_by_residence.xlsx"
OUT = ROOT / "data/research_cache/r109/r109_census_inflow.json"


def num(v):
    return v if isinstance(v, (int, float)) else 0


def main() -> None:
    wb = openpyxl.load_workbook(SRC, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = []
    for r in ws.iter_rows(min_row=11, values_only=True):
        if r[3] and str(r[3]).startswith("13113_"):
            rows.append(r)
    # 列: 0 男女 / 3 地域名(従業地) / 4 階層 / 5 常住地の区分 / 6 識別 / 7 都道府県(常住地) / 8 地域名(常住地)
    #     9 総数 / 10 15歳以上就業者・通学者 / 11 15歳以上就業者 / 12 15歳以上通学者 / 13 15歳未満を含む通学者
    head = [list(r[4:14]) for r in rows[:40]]
    by_pref = defaultdict(lambda: [0, 0, 0])
    by_muni = []
    for r in rows:
        level, cat, ident, pref, muni = r[4], str(r[5]), r[6], str(r[7]), str(r[8])
        if muni.endswith("_全国") or not muni[:5].isdigit():
            continue
        code = muni[:5]
        if code.endswith("000") or str(ident) == "1":
            continue  # 都道府県の行と、特別区部・政令市の合計の行(識別 1)。識別 0=区・2=市・3=町村が末端
        by_muni.append({"cat": cat, "level": level, "ident": ident, "pref": pref, "muni": muni,
                        "total": num(r[9]), "worker15": num(r[11]), "student15": num(r[12]),
                        "student_all": num(r[13])})
    out = {"source": "e-Stat statInfId 000032214352 (令和2年国勢調査 第4表 東京都(従業地・通学地))",
           "head_rows_13113": head, "n_rows_13113": len(rows)}
    # 区分の行の合計(全国の行)
    top = [dict(cat=str(r[5]), level=r[4], pref=str(r[7]), muni=str(r[8]), total=num(r[9]),
                worker15=num(r[11]), student15=num(r[12]), student_all=num(r[13]))
           for r in rows if str(r[8]).endswith("_全国")]
    out["summary_rows"] = top
    # 市区町村ごと(区分は「他市区町村に常住」の下の行)。同じ市区町村が複数区分に出る場合は最大の区分だけを残す
    munis = sorted(by_muni, key=lambda m: -m["total"])
    out["by_municipality"] = munis
    for m in munis:
        by_pref[m["pref"]][0] += m["total"]
        by_pref[m["pref"]][1] += m["worker15"]
        by_pref[m["pref"]][2] += m["student_all"]
    out["by_prefecture_from_munis"] = {k: v for k, v in sorted(by_pref.items(), key=lambda x: -x[1][0])}
    tot = sum(m["total"] for m in munis)
    acc = 0
    cum = []
    for i, m in enumerate(munis):
        acc += m["total"]
        if i + 1 in (1, 5, 10, 20, 50, 100, 200):
            cum.append({"top_n": i + 1, "share": round(acc / tot, 4)})
    out["muni_total"] = tot
    out["n_munis"] = len(munis)
    out["cumulative_share"] = cum
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for t in top:
        print(t)
    print("n_munis", len(munis), "total", tot)
    print("prefs", json.dumps(out["by_prefecture_from_munis"], ensure_ascii=False))
    print("top20", [(m["muni"], m["total"]) for m in munis[:20]])
    print("cum", cum)


if __name__ == "__main__":
    main()
