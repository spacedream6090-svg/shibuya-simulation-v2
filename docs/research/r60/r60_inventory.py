# -*- coding: utf-8 -*-
"""R-60 地名帳の材料の実測(読むだけ)。

手元の OSM(Overpass の生データ)・世界資産 W1/W2/W4/W5/W6/W11・e-Stat 小地域境界(R2 国勢調査・渋谷区)から、
地名帳の層ごとの「名前のある地物」の件数・延長・重複を数える。資産は 1 バイトも変えない。

使い方(リポのルートで):
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe docs/research/r60/r60_inventory.py docs/research/r60/r60_inventory.json
"""
import collections
import io
import json
import math
import sys
import unicodedata

import numpy as np
import pyarrow.parquet as pq

sys.path.insert(0, "src")
from shibuya.build.pop import shapefile as SH  # noqa: E402

OUT = sys.argv[1]
W = "data/world/v2/"
OSM = "data/realworld/osm/"
crs = json.load(open(W + "world_crs.json", encoding="utf-8"))
LAT0, LON0 = crs["origin_latlon"]
MLAT, MLON = crs["m_per_deg_lat"], crs["m_per_deg_lon"]


def to_xy(lat, lon):
    return (lon - LON0) * MLON, (lat - LAT0) * MLAT


def nk(s):
    return unicodedata.normalize("NFKC", str(s or "")).strip()


# ---- 舞台 = W2 の GL セル(100 m 格子)
cells = pq.read_table(W + "w2_cells.parquet").to_pydict()
gl = {(ix, iy) for ix, iy, b in zip(cells["ix"], cells["iy"], cells["band"]) if b == "GL"}
all_cells = {(ix, iy) for ix, iy in zip(cells["ix"], cells["iy"])}


def in_stage(x, y):
    return (math.floor(x / 100.0), math.floor(y / 100.0)) in gl


res = {"stage_gl_cells": len(gl), "stage_cells_all_bands": len(cells["place_id"])}

# ---- 1. 道路(name つき way の本数と延長)
roads = json.load(open(OSM + "road_names_overpass_20260928.json", encoding="utf-8"))["elements"]
by_cls = collections.defaultdict(lambda: {"ways": 0, "len_m": 0.0, "named_ways": 0, "named_len_m": 0.0})
name_len = collections.Counter()
variant_tags = collections.Counter()
for w in roads:
    t = w.get("tags", {})
    g = w.get("geometry") or []
    cls = t.get("highway", "?")
    L = Ln = 0.0
    for a, b in zip(g, g[1:]):
        x1, y1 = to_xy(a["lat"], a["lon"])
        x2, y2 = to_xy(b["lat"], b["lon"])
        if not in_stage((x1 + x2) / 2, (y1 + y2) / 2):
            continue
        L += math.hypot(x2 - x1, y2 - y1)
    if L <= 0:
        continue
    r = by_cls[cls]
    r["ways"] += 1
    r["len_m"] += L
    nm = nk(t.get("name") or t.get("name:ja"))
    if nm:
        r["named_ways"] += 1
        r["named_len_m"] += L
        name_len[nm] += L
        for k in ("alt_name", "old_name", "official_name", "short_name", "loc_name", "name:ja-Hira", "name:en", "ref"):
            if k in t:
                variant_tags[k] += 1
tot = {k: sum(v[k] for v in by_cls.values()) for k in ("ways", "len_m", "named_ways", "named_len_m")}
res["roads"] = {
    "by_class": {k: {kk: round(vv, 1) for kk, vv in v.items()} for k, v in sorted(by_cls.items(), key=lambda kv: -kv[1]["len_m"])},
    "total": {k: round(v, 1) for k, v in tot.items()},
    "named_len_share": round(tot["named_len_m"] / tot["len_m"], 4),
    "distinct_names": len(name_len),
    "top_names_by_len": [[n, round(L, 1)] for n, L in name_len.most_common(40)],
    "variant_tag_ways": dict(variant_tags),
}
# 歩行網(W1)の総延長との比(W1 は footway 等を含む=OSM の問い合わせより広い)
e = pq.read_table(W + "w1_edges.parquet", columns=["length_m", "band", "klass"]).to_pydict()
res["roads"]["w1_walk_graph_len_m"] = round(sum(e["length_m"]), 1)
res["roads"]["w1_walk_graph_len_by_class"] = {
    k: round(v, 1) for k, v in collections.Counter(
        {kk: 0 for kk in set(e["klass"])}).items()}
kl = collections.Counter()
for L, k in zip(e["length_m"], e["klass"]):
    kl[k] += L
res["roads"]["w1_walk_graph_len_by_class"] = {k: round(v, 1) for k, v in kl.most_common()}
res["roads"]["named_len_over_w1_len"] = round(tot["named_len_m"] / sum(e["length_m"]), 4)

# ---- 2. 通りの付属(交差点名=名前つき信号・バス停・公園 ほか)
sf = json.load(open(OSM + "street_features_overpass_20260907.json", encoding="utf-8"))["elements"]
node_ll = {}
sig_names = collections.Counter()
sig_in = sig_all = 0
kinds = collections.Counter()
for el in sf:
    t = el.get("tags", {})
    if el["type"] == "node":
        x, y = to_xy(el["lat"], el["lon"]) if "lat" in el else (None, None)
    else:
        c = el.get("center") or {}
        x, y = to_xy(c["lat"], c["lon"]) if c else (None, None)
    ins = x is not None and in_stage(x, y)
    nm = nk(t.get("name") or t.get("name:ja"))
    key = next((f"{a}={t[a]}" for a in ("highway", "leisure", "amenity", "railway", "place", "tourism", "man_made") if a in t), "other")
    kinds[(key, bool(nm), ins)] += 1
    if t.get("highway") == "traffic_signals" and nm:
        sig_all += 1
        if ins:
            sig_in += 1
            sig_names[nm] += 1
res["street_features"] = {
    "named_traffic_signals_all": sig_all,
    "named_traffic_signals_in_stage": sig_in,
    "distinct_signal_names_in_stage": len(sig_names),
    "signal_names_sample": sorted(sig_names)[:80],
    "kinds_named_in_stage": {k[0]: v for k, v in sorted(kinds.items(), key=lambda kv: -kv[1]) if k[1] and k[2]},
}

# ---- 3. OSM の POI の生タグ(公園・広場・place=* の有無)
pt = json.load(open(OSM + "poi_tags_overpass_20260928.json", encoding="utf-8"))["elements"]
pk = collections.Counter()
for el in pt:
    t = el.get("tags", {})
    if not nk(t.get("name")):
        continue
    for a in ("leisure", "tourism", "place"):
        if a in t:
            pk[f"{a}={t[a]}"] += 1
    if t.get("amenity") in ("marketplace",) or t.get("highway") == "pedestrian":
        pk[f"special:{t.get('amenity') or t.get('highway')}"] += 1
res["poi_tags_named_leisure_tourism_place"] = dict(pk.most_common(40))
res["note_place_tags"] = "Overpass の手元データは place=* (neighbourhood/quarter/square) を問い合わせていない=件数は 0 でも不在の証拠ではない"

# ---- 4. W6 の POI(店・施設)
poi = pq.read_table(W + "w6_poi.parquet").to_pydict()
names = [nk(n) for n in poi["name"]]
named = [n for n in names if len(n) >= 2]
cnt = collections.Counter(named)
cat_named = collections.Counter(c for n, c in zip(names, poi["cat"]) if len(n) >= 2)
sys.path.insert(0, "src")
from shibuya.engine.wom import _branch_stripped, normalize_v0  # noqa: E402
brand = collections.Counter((_branch_stripped(n) or normalize_v0(n)) for n in named)
res["w6_poi"] = {
    "total": len(names),
    "named_ge2": len(named),
    "distinct_names": len(cnt),
    "names_used_ge2_times": sum(1 for v in cnt.values() if v >= 2),
    "pois_sharing_a_name": sum(v for v in cnt.values() if v >= 2),
    "distinct_brand_after_branch_strip": len(brand),
    "pois_sharing_brand": sum(v for v in brand.values() if v >= 2),
    "top_shared_names": cnt.most_common(25),
    "top_shared_brands": brand.most_common(25),
    "named_by_cat": dict(cat_named.most_common()),
    "landmark_names": sorted({n for n, c in zip(names, poi["cat"]) if c == "landmark" and len(n) >= 2}),
}

# ---- 5. 駅の出口・入口・建物名
ex = pq.read_table(W + "w11_station_exits.parquet").to_pydict()
exn = collections.Counter(nk(n) for n in ex["exit_name"])
res["w11_station_exits"] = {"total": len(ex["exit_name"]), "distinct_names": len(exn),
                            "dup_names": {k: v for k, v in exn.items() if v >= 2},
                            "by_station": dict(collections.Counter(ex["station_title"]))}
ent = pq.read_table(W + "w5_entrances.parquet", columns=["kind", "name"]).to_pydict()
res["w5_entrances"] = {"by_kind": dict(collections.Counter(ent["kind"])),
                       "named_by_kind": dict(collections.Counter(k for k, n in zip(ent["kind"], ent["name"]) if nk(n)))}
b = pq.read_table(W + "w4_buildings.parquet", columns=["name", "centroid_x", "centroid_y"]).to_pydict()
bn = [nk(n) for n in b["name"]]
res["w4_buildings"] = {"total": len(bn), "named": sum(1 for n in bn if n),
                       "named_in_stage": sum(1 for n, x, y in zip(bn, b["centroid_x"], b["centroid_y"]) if n and in_stage(x, y)),
                       "distinct_names": len({n for n in bn if n})}

# ---- 6. 町丁目(e-Stat R2 小地域)と セル 520・街区 1,227 の対応
shp = "data/realworld/estat/r2ka13113/r2ka13113"
polys_ll = SH.read_shp(shp + ".shp")
dbf = SH.read_dbf(shp + ".dbf")
polys = [p.transformed(lambda lon, lat: ((lon - LON0) * MLON, (lat - LAT0) * MLAT)) for p in polys_ll]
cx = np.array(cells["centroid_x"])
cy = np.array(cells["centroid_y"])
ci = SH.assign_points_to_polygons(cx, cy, polys)
# 格子標本 10 m でセルごとの町丁目の混在(何町丁目にまたがるか)
mix = []
for ix, iy in zip(cells["ix"], cells["iy"]):
    xs = ix * 100 + 5 + np.arange(10) * 10.0
    ys = iy * 100 + 5 + np.arange(10) * 10.0
    gx, gy = np.meshgrid(xs, ys)
    k = SH.assign_points_to_polygons(gx.ravel(), gy.ravel(), polys)
    k = k[k >= 0]
    mix.append(len(set(k.tolist())))
cell_per_chome = collections.Counter(dbf[i]["S_NAME"] for i in ci if i >= 0)
bl = pq.read_table(W + "w2_blocks.parquet").to_pydict()
bi = SH.assign_points_to_polygons(np.array(bl["centroid_x"]), np.array(bl["centroid_y"]), polys)
blk_per_chome = collections.Counter(dbf[i]["S_NAME"] for i in bi if i >= 0)
# 町の名(丁目を外す)
def town(s):
    for suf in ("一丁目", "二丁目", "三丁目", "四丁目", "五丁目", "六丁目"):
        if s.endswith(suf):
            return s[: -len(suf)]
    return s
res["chome"] = {
    "estat_records": len(dbf),
    "chome_with_cell_centroid": len(cell_per_chome),
    "towns_with_cell_centroid": len({town(k) for k in cell_per_chome}),
    "cells_outside_ward": int((ci < 0).sum()),
    "cells_per_chome": dict(cell_per_chome.most_common()),
    "cells_by_n_chome_mixed": dict(collections.Counter(mix)),
    "blocks_total": len(bl["block_id"]),
    "blocks_with_chome": int((bi >= 0).sum()),
    "chome_with_block": len(blk_per_chome),
    "blocks_area_m2_quantiles": [round(float(q), 1) for q in np.quantile(np.array(bl["area_m2"]), [0.1, 0.5, 0.9])],
    "w16_note": "W16 の被覆率>0 の町丁目は 42/80(v2-world-data-build-spec 記載)",
}
json.dump(res, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in list(v.items())[:12]}) for k, v in res.items()}, ensure_ascii=False, indent=1)[:9000])
