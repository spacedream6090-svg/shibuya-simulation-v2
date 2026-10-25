"""R-107: Overpass の取得物(渋谷区の ATM・銀行・コンビニ・郵便局)を数え、タグの充実度を出す。

使い方: python count_atm.py <json のパス>
"""
import collections
import json
import sys

js = json.load(open(sys.argv[1], encoding="utf-8"))
els = js["elements"]
print("osm_base", js["osm3s"]["timestamp_osm_base"], "要素数", len(els))


def kind(t):
    if t.get("amenity") == "atm":
        return "amenity=atm"
    if t.get("amenity") == "bank":
        return "amenity=bank"
    if t.get("amenity") == "post_office":
        return "amenity=post_office"
    if t.get("shop") == "convenience":
        return "shop=convenience"
    return "その他(atm=yes のみ)"


groups = collections.defaultdict(list)
for e in els:
    groups[kind(e.get("tags", {}))].append(e)
keys = ["opening_hours", "operator", "brand", "name", "atm", "cash_in", "fee", "network", "level", "indoor", "wheelchair"]
for k, lst in groups.items():
    print(f"## {k}: {len(lst)} 件(node {sum(e['type']=='node' for e in lst)}・way {sum(e['type']=='way' for e in lst)}・relation {sum(e['type']=='relation' for e in lst)})")
    for key in keys:
        n = sum(1 for e in lst if key in e.get("tags", {}))
        print(f"   {key}: {n} ({n/len(lst)*100:.0f}%)")
    vals = collections.Counter(e.get("tags", {}).get("atm", "(なし)") for e in lst)
    print("   atm の値:", dict(vals))
    if k in ("amenity=atm", "shop=convenience", "amenity=bank"):
        ops = collections.Counter(e.get("tags", {}).get("operator") or e.get("tags", {}).get("brand") or "(なし)" for e in lst)
        print("   operator/brand 上位:", ops.most_common(12))
