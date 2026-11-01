"""R-107: Overpass の取得物(渋谷区の宿泊施設と payment:* タグを持つ要素)を数える。

使い方: python count_payment.py <json のパス>
"""
import collections
import json
import sys

js = json.load(open(sys.argv[1], encoding="utf-8"))
els = js["elements"]
print("osm_base", js["osm3s"]["timestamp_osm_base"], "要素数", len(els))
lodg = [e for e in els if e.get("tags", {}).get("tourism") in ("hotel", "hostel", "guest_house", "motel", "apartment")]
print("宿泊施設:", len(lodg), collections.Counter(e["tags"]["tourism"] for e in lodg))
lp = [e for e in lodg if any(k.startswith("payment:") for k in e["tags"])]
print("  うち payment:* を持つ:", len(lp))
pay = [e for e in els if any(k.startswith("payment:") for k in e.get("tags", {}))]
print("payment:* を持つ要素:", len(pay))
kinds = collections.Counter()
for e in pay:
    t = e["tags"]
    kinds[t.get("amenity") or t.get("shop") and "shop=" + t["shop"] or t.get("tourism") and "tourism=" + t["tourism"] or "その他"] += 1
print("  種類の上位:", kinds.most_common(12))
keys = collections.Counter()
vals = collections.defaultdict(collections.Counter)
for e in pay:
    for k, v in e["tags"].items():
        if k.startswith("payment:"):
            keys[k] += 1
            vals[k][v] += 1
for k, n in keys.most_common(20):
    print(f"  {k}: {n} {dict(vals[k])}")
