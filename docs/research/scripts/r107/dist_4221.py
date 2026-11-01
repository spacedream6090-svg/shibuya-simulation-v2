"""R-107: 全国家計構造調査 2024 第4-22-1表 から貯蓄現在高階級別の世帯分布(1万分比)と
各階級の平均の貯蓄・負債・保有率を出す(全世帯・世帯主の性別=平均)。

使い方: python dist_4221.py <CSV のパス>
"""
import csv
import io
import sys

raw = open(sys.argv[1], encoding="utf-8-sig").read()
body = raw[raw.find('"VALUE"'):].split("\n", 1)[1]
rows = list(csv.DictReader(io.StringIO(body)))
idx = {}
for r in rows:
    idx[(r["tab_code"], r["cat01_code"], r["cat04_code"], r["cat05_code"])] = r["value"]
classes = sorted({r["cat05_code"]: r["貯蓄現在高階級20区分"] for r in rows}.items())
for c1, name in [("0", "総世帯"), ("1", "二人以上"), ("2", "単身")]:
    print(f"## {name}")
    print("階級 | 集計世帯数 | 世帯数分布(1万分比) | 貯蓄(千円) | 負債(千円) | 負債保有率% | 通貨性預貯金(千円)")
    for code, nm in classes:
        g = lambda t, c4: idx.get((t, c1, c4, code), "")
        print(nm, "|", g("06-2024", "0"), "|", g("07-2024", "0"), "|", g("04-2024", "21"), "|", g("04-2024", "22"), "|", g("05-2024", "6"), "|", g("04-2024", "2111"))
    print("貯蓄保有率% 通貨性/定期性:", idx.get(("05-2024", c1, "51", "00")), idx.get(("05-2024", c1, "52", "00")), "負債保有率%:", idx.get(("05-2024", c1, "6", "00")))
