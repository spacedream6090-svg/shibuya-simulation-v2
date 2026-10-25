# -*- coding: utf-8 -*-
"""R-60 実 LLM テープの「対象」欄と「ひと言」欄の場所語の内訳と、機械的な地名帳の試作での解決率(読むだけ)。

材料: data/tape/c8_*/*/calls.parquet(C8 の実 LLM ラン・8B)。**(call_id, response) の集合が同一の calls は 1 本に数える**(基準腕の複製・並び順だけ違う)。
地名帳の試作 v0(未リサーチ=expedient・本スクリプトの中だけ):
  L1 町丁目   = e-Stat R2 小地域(渋谷区 80)の S_NAME+丁目を外した町名+表記ゆれ(ケ/ヶ・涛/濤・鴬/鶯)
  L2 通り等   = OSM の name つき道路(舞台の bbox 全体)+alt/official/short 名・W1 の名前つきノード 14・
                W11 の出口名・駅名・OSM の名前つき信号(交差点名)・leisure/tourism の名・W6 の landmark
  L3 施設・店 = W6 POI 名(+支店の接尾辞を外した名)・W4 建物名
正規化 = engine/wom.py の normalize_v0(NFKC・小文字・空白除去)。照合の段:
  1 完全一致 → 2 接尾辞/助詞を外して一致 → 3 地名帳の名(3 字以上)が対象に含まれる(最長) → 4 失敗
使い方(リポのルートで):
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe docs/research/r60/r60_tape_targets.py docs/research/r60/r60_tape_targets.json
"""
import collections
import glob
import hashlib
import io
import json
import re
import sys
import time
import unicodedata

import pyarrow.parquet as pq

sys.path.insert(0, "src")
from shibuya.build.pop import shapefile as SH  # noqa: E402
from shibuya.engine.wom import _branch_stripped, normalize_v0  # noqa: E402
from shibuya.llm.contract import TargetKind  # noqa: E402
from shibuya.llm.parser import parse_two_line  # noqa: E402

OUT = sys.argv[1]
t0 = time.time()
W = "data/world/v2/"
OSM = "data/realworld/osm/"


def nk(s):
    return unicodedata.normalize("NFKC", str(s or "")).strip()


# ============ 地名帳の試作 v0 ============
gaz = {}  # normalized name -> (layer, source, display)


def add(name, layer, src):
    n = normalize_v0(name)
    if len(n) < 2:
        return
    # 同じ名が複数層にあるときは粗い層を優先しない(先に入れた方=L1→L2→L3 の順で入れる)
    gaz.setdefault(n, (layer, src, nk(name)))


def variants(s):
    out = {s}
    for a, b in (("ケ", "ヶ"), ("涛", "濤"), ("鴬", "鶯"), ("ヶ", "ケ")):
        out |= {x.replace(a, b) for x in list(out)}
    return out


KANJI_NUM = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6"}
dbf = SH.read_dbf("data/realworld/estat/r2ka13113/r2ka13113.dbf")
for r in dbf:
    s = r["S_NAME"]
    for v in variants(s):
        add(v, "L1", "estat_chome")
        m = re.match(r"^(.*?)([一二三四五六])丁目$", v)
        if m:
            add(m.group(1), "L1", "estat_town")
            add(m.group(1) + KANJI_NUM[m.group(2)] + "丁目", "L1", "estat_chome_digit")
        elif v.endswith("町"):
            add(v[:-1], "L1", "estat_town_nocho")

roads = json.load(open(OSM + "road_names_overpass_20260928.json", encoding="utf-8"))["elements"]
for w in roads:
    t = w.get("tags", {})
    for k in ("name", "name:ja", "alt_name", "official_name", "short_name", "loc_name"):
        if t.get(k):
            for part in re.split(r"[;;]", t[k]):
                add(part, "L2", "osm_road")
                m = re.match(r"^(.*?)[((](.+?)[))]$", nk(part))  # 「青山通り(金王坂)」→ 両方
                if m:
                    add(m.group(1), "L2", "osm_road_paren")
                    add(m.group(2), "L2", "osm_road_paren")
n1 = pq.read_table(W + "w1_nodes.parquet", columns=["name"]).to_pydict()
for s in n1["name"]:
    if s:
        add(s, "L2", "w1_named_node")
ex = pq.read_table(W + "w11_station_exits.parquet").to_pydict()
for s, stt in zip(ex["exit_name"], ex["station_title"]):
    add(s, "L2", "w11_exit")
    add(nk(stt) + nk(s), "L2", "w11_exit_label")  # 描画の目印ラベル(renderer.exit_label=駅名+出口名)
st = pq.read_table(W + "w11_stations.parquet").to_pydict()
for s in st["title"]:
    add(s, "L2", "w11_station")
    add(nk(s) + "駅", "L2", "w11_station")
sf = json.load(open(OSM + "street_features_overpass_20260907.json", encoding="utf-8"))["elements"]
for el in sf:
    t = el.get("tags", {})
    if t.get("name") and (t.get("highway") == "traffic_signals" or t.get("leisure") in ("park", "garden")):
        add(t["name"], "L2", "osm_signal_or_park")
pt = json.load(open(OSM + "poi_tags_overpass_20260928.json", encoding="utf-8"))["elements"]
for el in pt:
    t = el.get("tags", {})
    if t.get("name") and (t.get("leisure") in ("park", "garden") or t.get("tourism") in ("attraction", "artwork", "museum")):
        add(t["name"], "L2", "osm_park_attraction")
poi = pq.read_table(W + "w6_poi.parquet", columns=["name", "cat"]).to_pydict()
for s, c in zip(poi["name"], poi["cat"]):
    if c == "landmark":
        add(s, "L2", "w6_landmark")
for s, c in zip(poi["name"], poi["cat"]):
    if c != "landmark":
        add(s, "L3", "w6_poi")
        b = _branch_stripped(s)
        if b:
            add(b, "L3", "w6_poi_brand")
bn = pq.read_table(W + "w4_buildings.parquet", columns=["name"]).to_pydict()
for s in bn["name"]:
    if s:
        add(s, "L3", "w4_building")
poi_name_n = collections.Counter(normalize_v0(x) for x in poi["name"])
for x in poi["name"]:
    b = _branch_stripped(x)
    if b:
        poi_name_n[b] += 0  # 鍵を作るだけ
brand_n = collections.Counter((_branch_stripped(x) or normalize_v0(x)) for x in poi["name"])
gaz_count = collections.Counter(v[0] for v in gaz.values())
gaz_src = collections.Counter(v[1] for v in gaz.values())
names_by_len = sorted((n for n in gaz if len(n) >= 3), key=len, reverse=True)
by_first = collections.defaultdict(list)
for n in names_by_len:
    by_first[n[0]].append(n)

# ============ 対象の分類 ============
SUFFIXES = ("の店頭", "の店内", "の店", "の前", "の近く", "の周辺", "の方", "店頭", "店内", "付近", "周辺", "近く",
            "あたり", "辺り", "方面", "方向", "前", "へ", "に", "まで", "で", "の")
PLACEHOLDER = {"目的地", "目的物", "目標", "目的場所", "目的", "目的の場所", "目的の店", "行き先", "購入", "食事", "移動",
               "目標地点", "目的地点", "対象", "場所", "予定地", "次の場所", "予定の場所", "目的店",
               "物のカテゴリ", "カテゴリ", "物のカテゴリー", "地点", "地域", "地物", "検索", "目的先", "セルid", "人id",
               "近接", "通報", "メニューカテゴリ"}
CELL_RE = re.compile(r"(セル|^g-?\d+_-?\d+|^c-\d+|_gl$|_ug$|_deck$)")
PERSON_RE = re.compile(r"^(p-\d+|人id)")
DIR_RE = re.compile(r"(近く|近所|周辺|付近|隣|向かい|あたり|辺り|方向|方面|東|西|南|北|奥|先|手前|反対|外|中心|中央)")
LAYER_WORDS = {"地上", "地下", "デッキ", "地下街", "ホーム", "改札", "駅構内", "駅", "駅前", "駅周辺", "屋外", "屋内", "店内", "路上",
               "歩道", "広場", "公園", "交差点", "通り", "街", "街中", "繁華街", "商店街", "自宅", "家", "職場", "会社", "学校",
               "オフィス", "ホテル", "宿", "寝床", "ベンチ", "休憩所", "トイレ"}
CAT_SUFFIX_RE = re.compile(r"(店|屋|場|所|館|施設|ストア|ショップ|カフェ|レストラン|食堂|コンビニ|スーパー|センター|売り場|売場)$")
generic_cat = {"飲食店", "食品", "食品カテゴリ", "食品カテゴリー", "食べ物", "食物", "食事場所", "物販店", "コンビニエンスストア",
               "コンビニ", "食品店", "食堂", "メニュー", "ラーメン", "カフェ", "飲み物", "飲料", "パン", "弁当", "おにぎり", "コーヒー",
               "書籍", "本", "服", "衣類", "雑貨", "薬", "日用品", "娯楽施設", "娯楽", "宿泊施設", "休憩場所"}


def strip_suffix(s):
    changed = True
    while changed:
        changed = False
        for suf in SUFFIXES:
            if s.endswith(suf) and len(s) > len(suf) + 1:
                s = s[: -len(suf)]
                changed = True
                break
    return s


def resolve(n):
    """正規化済みの対象 → (段, 名, 層)。"""
    if n in gaz:
        return ("1_exact", n, gaz[n][0])
    s = strip_suffix(n)
    if s in gaz:
        return ("2_suffix", s, gaz[s][0])
    best = None
    for i, ch in enumerate(n):
        for g in by_first.get(ch, ()):
            if n.startswith(g, i):
                if best is None or len(g) > len(best):
                    best = g
                break
    if best:
        return ("3_contains", best, gaz[best][0])
    return ("4_fail", None, None)


def classify(raw):
    n = normalize_v0(raw).strip("「」『』\"'。、.,")
    if n in ("", "なし", "無し", "none"):
        return "none", n
    if CELL_RE.search(n):
        return "cell", n
    if PERSON_RE.search(n):
        return "person", n
    if n in PLACEHOLDER or strip_suffix(n) in PLACEHOLDER:
        return "placeholder", n
    if re.match(r"^food\d+|^[a-z]+\d+$", n):
        return "id_like", n
    return "text", n


# ============ テープ ============
tapes = sorted(glob.glob("data/tape/c8_*/*/calls.parquet"))
seen_md5 = {}
uniq = []
for p in tapes:
    _t = pq.read_table(p, columns=["call_id", "response"]).to_pydict()
    h = hashlib.md5(repr(sorted(zip(_t["call_id"], _t["response"]))).encode("utf-8")).hexdigest()  # 並び順だけ違う複製を 1 本に
    if h in seen_md5:
        continue
    seen_md5[h] = p
    uniq.append(p)

agg = {  # 行動ごとの対象の型
    "kind": collections.Counter(),
    "text_res": collections.Counter(),
    "text_res_layer": collections.Counter(),
    "fail_top": collections.Counter(),
    "contains_top": collections.Counter(),
    "resolved_names": collections.Counter(),
    "text_fail_class": collections.Counter(),
    "l3_multi": collections.Counter(),
    "ph_top": collections.Counter(),
    "in_prompt": collections.Counter(),
}
comment_stats = collections.Counter()
comment_names = collections.Counter()
n_calls = 0
per_tape = {}
for p in uniq:
    arm = p.replace("\\", "/").split("/")[3]
    ver = "v2" if arm.endswith("_v2") else "v1"
    t = pq.read_table(p, columns=["response", "deferred", "agent_id", "block_ids"]).to_pydict()
    bl = pq.read_table(p.replace("calls.parquet", "blocks.parquet"), columns=["block_id", "text"]).to_pydict()
    btext = {b: normalize_v0(x) for b, x in zip(bl["block_id"], bl["text"])}
    k = 0
    for r, d, bids in zip(t["response"], t["deferred"], t["block_ids"]):
        if str(d) not in ("0", "False", "false", "") or not r:
            continue
        pr = parse_two_line(r, ver)
        n_calls += 1
        k += 1
        act = pr.action or "(未定義)"
        tg = pr.target
        cls, n = classify(tg.raw if tg is not None else "")
        if tg is not None and tg.kind == TargetKind.CELL:
            cls = "cell"
        if tg is not None and tg.kind == TargetKind.PERSON:
            cls = "person"
        grp = "移動" if act == "移動" else "その他"
        agg["kind"][(grp, cls)] += 1
        if cls in ("placeholder", "cell") and grp == "移動":
            agg["ph_top"][(cls, n if cls == "placeholder" else ("セル語" if "セル" in n else "格子id"))] += 1
        if cls == "text":
            stage, name, layer = resolve(n)
            agg["text_res"][(grp, stage)] += 1
            if layer:
                agg["text_res_layer"][(grp, stage, layer)] += 1
                agg["resolved_names"][(grp, name, layer)] += 1
                if layer == "L3":
                    nn = max(poi_name_n.get(name, 0), brand_n.get(name, 0))
                    agg["l3_multi"][(grp, "multi" if nn >= 2 else ("single" if nn == 1 else "building_or_brand"))] += 1
                ids = [x.strip(" '\"") for x in str(bids).strip("[]").split(",")]
                vis = any(name in btext.get(b, "") for b in ids)
                agg["in_prompt"][(grp, layer, vis)] += 1
                if stage == "3_contains":
                    agg["contains_top"][(n, name)] += 1
            else:
                fc = ("generic_cat" if (n in generic_cat or strip_suffix(n) in generic_cat) else
                      "layer_word" if (n in LAYER_WORDS or strip_suffix(n) in LAYER_WORDS or any(n.endswith(w) and len(n) <= len(w) + 3 for w in ("地上", "地下", "デッキ"))) else
                      "direction" if DIR_RE.search(n) else
                      "cat_suffix" if CAT_SUFFIX_RE.search(n) else "other")
                agg["text_fail_class"][(grp, fc)] += 1
                if grp == "移動":
                    agg["fail_top"][(n, fc)] += 1
        # ひと言欄の場所語(3 字以上の地名帳の名を含むか)
        c = normalize_v0(pr.raw_comment or "")
        if c and c not in ("なし", "無し"):
            comment_stats["comments"] += 1
            best = None
            for i, ch in enumerate(c):
                for g in by_first.get(ch, ()):
                    if c.startswith(g, i):
                        if best is None or len(g) > len(best):
                            best = g
                        break
            if best:
                lay = gaz[best][0]
                comment_stats["with_gaz_name"] += 1
                comment_stats[f"with_gaz_name_{lay}"] += 1
                comment_names[(best, lay)] += 1
    per_tape[p.replace("\\", "/")] = k
    print(p, k, f"{time.time()-t0:.0f}s", flush=True)


def ck(c, n=None):
    return [[list(k) if isinstance(k, tuple) else k, v] for k, v in c.most_common(n)]


res = {
    "note": "c8 実 LLM テープ(8B・語彙 v1/v2・open/hint 腕を含む)。(call_id, response) の集合が同一の calls は 1 本に数えた(基準腕の複製)。",
    "prompt_confound": "当時の B0 は「対象には観測に現れているセルID・物のカテゴリ・人ID、または、なし、だけを書きます」と指示していた=名指しを抑える指示の下での値",
    "tapes_total": len(tapes), "tapes_unique": len(uniq), "per_tape_calls": per_tape, "calls": n_calls,
    "gazetteer_v0": {"names": len(gaz), "by_layer": dict(gaz_count), "by_source": dict(gaz_src)},
    "target_kind": ck(agg["kind"]),
    "text_resolution": ck(agg["text_res"]),
    "text_resolution_layer": ck(agg["text_res_layer"]),
    "text_fail_class": ck(agg["text_fail_class"]),
    "move_fail_top60": ck(agg["fail_top"], 60),
    "contains_top40": ck(agg["contains_top"], 40),
    "resolved_names_top60": ck(agg["resolved_names"], 60),
    "l3_multi_poi": ck(agg["l3_multi"]),
    "move_placeholder_cell_top20": ck(agg["ph_top"], 20),
    "resolved_name_in_prompt": ck(agg["in_prompt"]),
    "comment": dict(comment_stats),
    "comment_names_top40": ck(comment_names, 40),
}
json.dump(res, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("per_tape_calls",)}, ensure_ascii=False)[:12000])
