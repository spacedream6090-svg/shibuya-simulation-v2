# -*- coding: utf-8 -*-
"""D-114 の (i)/(ii)/(iii) の実測割合(語彙腕 vocab+hint の 購入/食事/移動)と、名指しの店の所在。"""
import sys, io, json, re, collections
d = json.load(io.open(sys.argv[1], encoding="utf-8"))
ID_RE = re.compile(r"^(food|shop|service|office|hotel|school|landmark|leisure|hall|attraction|cinema|nightlife|education)\d{4}$")
CAT_WORDS = ("飲食", "食品", "食堂", "食べ物", "食物", "食料", "食事", "コンビニ", "カフェ", "喫茶", "レストラン", "物販", "サービス店", "薬局", "ドラッグ",
             "飲料", "ドリンク", "ラーメン", "フード", "メニュー", "娯楽", "カラオケ", "デリバリー", "デリカ", "学校", "事務所", "駅", "バス", "店", "ショップ",
             "おむすび", "おにぎり", "お好み焼き", "おでん", "水", "お茶", "コーヒー", "スーパー", "商店", "売店", "屋台", "公園", "ホテル", "書店", "本屋")
# 名指し(店名)= target_named。腕は arm_list で判定(vocab/hint のみ)。
def is_vocab_arm(arms):
    return any(("__vocab" in a or "__hint" in a or "AB6" in a or "AB8" in a) for a in arms)
share = {act: collections.Counter() for act in ("購入", "食事", "移動")}
where = {act: collections.Counter() for act in ("購入", "食事", "移動")}
for r in d["target_named"]:
    act, nm, wh = r["key"].split(" | ")
    if act not in share: continue
    arms = [a for a in r["arm_list"] if "__open" not in a]
    if not arms: continue
    # open 腕を除くため calls は腕数比で按分(概算)
    c = r["calls"] * len(arms) / max(1, len(r["arm_list"]))
    share[act]["(i) 店名を名指し"] += c
    where[act][wh] += c
for r in d["target_free"]:
    act, tg = r["key"].split(" | ", 1)
    if act not in share: continue
    arms = [a for a in r["arm_list"] if "__open" not in a]
    if not arms: continue
    c = r["calls"] * len(arms) / max(1, len(r["arm_list"]))
    if ID_RE.match(tg):
        share[act]["(i′) カテゴリ+番号で名指し"] += c; where[act]["id_ref"] += c
    elif tg.startswith("セルg") or tg.startswith("セル g"):
        share[act]["(iv) セルID(セル接頭辞つき=未解釈)"] += c
    elif any(w in tg for w in CAT_WORDS):
        share[act]["(ii) カテゴリ語"] += c
    else:
        share[act]["(iii) その他の自由記述"] += c
for r in d["target_kinds"]:
    if r["mode"] == "open" or r["action"] not in share: continue
    if r["kind"] == "NONE":
        share[r["action"]]["(iii) なし/説明語"] += r["calls"]
    elif r["kind"] == "CELL":
        share[r["action"]]["セルID(解釈済み)"] += r["calls"]
    elif r["kind"] == "PERSON":
        share[r["action"]]["人ID"] += r["calls"]
    elif r["kind"] == "STATION_OR_VEHICLE":
        share[r["action"]]["駅名"] += r["calls"]
for act in share:
    tot = sum(share[act].values())
    print(f"== {act}: total {tot:,.0f}")
    for k, v in share[act].most_common():
        print(f"   {v:9,.0f} {v/tot*100:5.1f}%  {k}")
    print("   名指しの所在:", {k: f"{v:,.0f}" for k, v in where[act].most_common()})
