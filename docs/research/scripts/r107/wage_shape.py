"""R-107: 賃金構造基本統計調査 令和7年 職種第18表の分布特性値から、職種(大分類)ごとの
所定内給与額の対数の広がり(対数正規なら sigma)と、上下の非対称を出す。

sigma_D = ln(D9/D1)/(2*1.2816)、sigma_Q = ln(Q3/Q1)/(2*0.6745)、
非対称 = ln(D9/中位数) − ln(中位数/D1)(対数正規なら 0)。
使い方: python wage_shape.py <xlsx のパス>
"""
import math
import sys

import openpyxl

wb = openpyxl.load_workbook(sys.argv[1], read_only=True, data_only=True)
for ws in wb.worksheets:
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    head = [c for c in rows[7] if c is not None][1:]
    get = {}
    for r in rows:
        r = [c for c in r if c is not None]
        if r and isinstance(r[0], str):
            k = r[0].replace("\u3000", "").replace(" ", "")
            for key in ["第1・十分位数", "第1・四分位数", "中位数", "第3・四分位数", "第9・十分位数"]:
                if k.startswith(key) and key not in get:
                    get[key] = r[1:]
    print(f"## {ws.title}")
    print("職種 | D1 | 中位数 | D9 | sigma_D | sigma_Q | 非対称")
    for j, name in enumerate(head):
        try:
            d1, q1, md, q3, d9 = (float(get[k][j]) for k in ["第1・十分位数", "第1・四分位数", "中位数", "第3・四分位数", "第9・十分位数"])
        except (ValueError, IndexError, KeyError):
            continue
        sd = math.log(d9 / d1) / (2 * 1.2816)
        sq = math.log(q3 / q1) / (2 * 0.6745)
        asym = math.log(d9 / md) - math.log(md / d1)
        print(f"{name} | {d1} | {md} | {d9} | {sd:.3f} | {sq:.3f} | {asym:+.3f}")
