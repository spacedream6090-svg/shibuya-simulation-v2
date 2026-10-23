"""R-107: 全国家計構造調査 2024 第4-4表 から 世帯の種類 × 世帯主の性別 × 年齢(10 歳階級2)別の
貯蓄・負債・通貨性預貯金・保有率を出す(全世帯)。

使い方: python age_44.py <CSV のパス>
"""
import csv
import io
import sys

raw = open(sys.argv[1], encoding="utf-8-sig").read()
body = raw[raw.find('"VALUE"'):].split("\n", 1)[1]
rows = list(csv.DictReader(io.StringIO(body)))
v = {(r["tab_code"], r["cat01_code"], r["cat03_code"], r["cat04_code"], r["cat05_code"]): r["value"] for r in rows}
ages = ["000", "301", "302", "303", "304", "305", "306", "307"]
an = {r["cat05_code"]: r["世帯主の年齢階級32区分"] for r in rows}
for c1, n1 in [("0", "総世帯"), ("1", "二人以上"), ("2", "単身")]:
    for c3, n3 in [("0", "平均"), ("1", "男"), ("2", "女")]:
        print(f"## {n1} 世帯主={n3}")
        print("年齢 | 推計世帯数 | 貯蓄(千円) | 通貨性(千円) | 負債(千円) | 純金融(千円) | 貯蓄保有率% | 通貨性保有率% | 負債保有率%")
        for a in ages:
            g = lambda t, c4: v.get((t, c1, c3, c4, a), "")
            print(an.get(a), "|", g("07-2024", "21") or g("07-2024", "0"), "|", g("04-2024", "21"), "|", g("04-2024", "2111"), "|", g("04-2024", "22"), "|", g("04-2024", "2"), "|", g("05-2024", "5"), "|", g("05-2024", "51"), "|", g("05-2024", "6"))
