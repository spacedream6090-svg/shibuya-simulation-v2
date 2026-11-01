"""R-106: 渋谷の世界に関わる法律 13 本の改正履歴(e-Gov API v2)から、公布から施行までの日数の分布を出す(読むだけ)。
対象は施行日が 2015-01-01 以降の改正。同じ改正法の同じ施行日は 1 件に数える(法律をまたいでも 1 件)。"""
import json, urllib.request, datetime as dt, statistics as st
LAWS = {"322AC0000000049": "労働基準法", "129AC0000000089": "民法", "403AC0000000090": "借地借家法",
        "322AC0000000233": "食品衛生法", "323AC0000000122": "風営法", "335AC0000000105": "道路交通法",
        "327AC1000000180": "道路法", "363AC0000000108": "消費税法", "340AC0000000033": "所得税法",
        "358AC1000000032": "貸金業法", "361AC0000000092": "鉄道事業法", "211AC0000000070": "健康保険法",
        "334AC0000000137": "最低賃金法"}
seen = {}
for lid, name in LAWS.items():
    with urllib.request.urlopen(f"https://laws.e-gov.go.jp/api/2/law_revisions/{lid}", timeout=60) as r:
        d = json.load(r)
    for rv in d.get("revisions", []):
        e, p, n = rv.get("amendment_enforcement_date"), rv.get("amendment_promulgate_date"), rv.get("amendment_law_num")
        if not (e and p and n) or e < "2015-01-01": continue
        key = (n, e)
        days = (dt.date.fromisoformat(e) - dt.date.fromisoformat(p)).days
        seen.setdefault(key, {"days": days, "laws": set(), "title": rv.get("amendment_law_title") or ""})["laws"].add(name)
vals = sorted(v["days"] for v in seen.values())
pos = [x for x in vals if x > 0]
q = lambda xs, f: xs[min(len(xs) - 1, int(f * len(xs)))]
print("件数(改正法×施行日):", len(vals), " うち公布日に施行(0 日):", len(vals) - len(pos))
print("0 日を除く: 中央値", st.median(pos), "日 / 25%", q(pos, .25), "/ 75%", q(pos, .75), "/ 90%", q(pos, .9), "/ 最大", max(pos))
for lo, hi in [(1, 30), (31, 90), (91, 180), (181, 365), (366, 730), (731, 10000)]:
    print(f"  {lo}〜{hi} 日: {sum(lo <= x <= hi for x in pos)}")
for (n, e), v in sorted(seen.items(), key=lambda kv: -kv[1]["days"])[:5]:
    print("  長い例:", v["days"], "日", n, e, "/".join(sorted(v["laws"])), v["title"][:40])
