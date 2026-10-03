# -*- coding: utf-8 -*-
"""R-60「いまいる場所」の文の試作(読むだけ・未リサーチ=expedient の型)と、層ごとの被覆の実測。

W10 の街路点(歩ける面の標本)から無作為に 20,000 点を取り(seed 0)、各点について
  L1 = e-Stat 町丁目(渋谷区のみ・区外は空)
  L2 = 最寄りの name つき道路(OSM・線分距離)/ 名前つきノード・出口・公園・landmark(点距離)
  L3 = 最寄りの名前つき POI(W6)
を求め、半径 r(15/30/50 m)で層が埋まる割合と、文「いまいる場所: <L1>・<L2>・<L3>前」の字数を数える。
tok は本リポの見積り規約(字数÷2)による推定。
使い方: PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe docs/research/r60/r60_here_line.py docs/research/r60/r60_here_line.json
"""
import io
import json
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
nk = lambda s: unicodedata.normalize("NFKC", str(s or "")).strip()  # noqa: E731

sp = pq.read_table(W + "w10_street_points.parquet", columns=["x", "y", "band"]).to_pydict()
x = np.array(sp["x"])
y = np.array(sp["y"])
band = np.array(sp["band"])
rng = np.random.default_rng(0)
idx = rng.choice(np.flatnonzero(band == "GL"), 20000, replace=False)
px, py = x[idx], y[idx]

# L1
polys = [p.transformed(lambda lon, lat: ((lon - LON0) * MLON, (lat - LAT0) * MLAT))
         for p in SH.read_shp("data/realworld/estat/r2ka13113/r2ka13113.shp")]
dbf = SH.read_dbf("data/realworld/estat/r2ka13113/r2ka13113.dbf")
k1 = SH.assign_points_to_polygons(px, py, polys)
l1 = np.array([dbf[k]["S_NAME"] if k >= 0 else "" for k in k1])

# L2 道路(線分)
segs, snames = [], []
for w in json.load(open(OSM + "road_names_overpass_20260928.json", encoding="utf-8"))["elements"]:
    t = w.get("tags", {})
    nm = nk(t.get("name") or t.get("name:ja"))
    if not nm or t.get("highway") == "motorway" or nm.startswith("首都高速"):
        continue  # 高架の高速は歩く人の「いまいる通り」にならない(expedient)
    g = [((q["lon"] - LON0) * MLON, (q["lat"] - LAT0) * MLAT) for q in w["geometry"]]
    for a, b in zip(g, g[1:]):
        segs.append((a[0], a[1], b[0], b[1]))
        snames.append(nm)
S = np.array(segs)
snames = np.array(snames)


def seg_nearest(px, py):
    best_d = np.full(px.shape, np.inf)
    best_i = np.full(px.shape, -1)
    for s in range(0, len(S), 2000):
        A = S[s:s + 2000]
        ax, ay, bx, by = A[:, 0], A[:, 1], A[:, 2], A[:, 3]
        dx, dy = bx - ax, by - ay
        L2 = np.maximum(dx * dx + dy * dy, 1e-9)
        t = np.clip(((px[:, None] - ax) * dx + (py[:, None] - ay) * dy) / L2, 0, 1)
        qx, qy = ax + t * dx, ay + t * dy
        d = np.hypot(px[:, None] - qx, py[:, None] - qy)
        j = d.argmin(1)
        dj = d[np.arange(len(px)), j]
        m = dj < best_d
        best_d[m] = dj[m]
        best_i[m] = j[m] + s
    return best_d, best_i


rd, ri = seg_nearest(px, py)

# L2 点(W1 名前つきノード・出口・W6 landmark・公園)
pts, pn = [], []
n1 = pq.read_table(W + "w1_nodes.parquet", columns=["name", "x", "y"]).to_pydict()
for a, b, c in zip(n1["name"], n1["x"], n1["y"]):
    if a:
        pts.append((b, c)); pn.append(nk(a))
ex = pq.read_table(W + "w11_station_exits.parquet").to_pydict()
for a, st, b, c in zip(ex["exit_name"], ex["station_title"], ex["x"], ex["y"]):
    pts.append((b, c)); pn.append(nk(st) + "駅" + nk(a) if not nk(a).endswith("駅") else nk(a))
poi = pq.read_table(W + "w6_poi.parquet", columns=["name", "cat", "x", "y"]).to_pydict()
for a, cat, b, c in zip(poi["name"], poi["cat"], poi["x"], poi["y"]):
    if cat == "landmark" and nk(a):
        pts.append((b, c)); pn.append(nk(a))
P2 = np.array(pts)
pn = np.array(pn)
d2 = np.hypot(px[:, None] - P2[:, 0], py[:, None] - P2[:, 1])
p2i = d2.argmin(1)
p2d = d2[np.arange(len(px)), p2i]

# L3 POI(landmark 以外)
P3 = np.array([(b, c) for a, cat, b, c in zip(poi["name"], poi["cat"], poi["x"], poi["y"]) if cat != "landmark" and nk(a)])
n3 = np.array([nk(a) for a, cat in zip(poi["name"], poi["cat"]) if cat != "landmark" and nk(a)])
p3d = np.full(len(px), np.inf)
p3i = np.full(len(px), -1)
for s in range(0, len(px), 2000):
    d = np.hypot(px[s:s + 2000, None] - P3[:, 0], py[s:s + 2000, None] - P3[:, 1])
    j = d.argmin(1)
    p3i[s:s + 2000] = j
    p3d[s:s + 2000] = d[np.arange(len(j)), j]

res = {"n_points": int(len(px)), "l1_filled": round(float((l1 != "").mean()), 4), "radius": {}}
for r in (15, 30, 50):
    road = rd <= r
    pt2 = p2d <= r
    l2 = road | pt2
    l3 = p3d <= r
    lens = []
    for i in range(len(px)):
        parts = []
        if l1[i]:
            parts.append(l1[i])
        if road[i]:
            parts.append(snames[ri[i]])
        elif pt2[i]:
            parts.append(pn[p2i[i]])
        if l3[i]:
            parts.append(n3[p3i[i]] + "前")
        line = "[B2 場所] いまいる場所: " + ("・".join(parts) if parts else "名前のない場所") + "(地上)。"
        lens.append(len(line))
    lens = np.array(lens)
    res["radius"][str(r)] = {
        "l2_road": round(float(road.mean()), 4), "l2_point": round(float(pt2.mean()), 4),
        "l2_any": round(float(l2.mean()), 4), "l3": round(float(l3.mean()), 4),
        "all_three": round(float(((l1 != "") & l2 & l3).mean()), 4),
        "none_of_l2_l3": round(float((~l2 & ~l3).mean()), 4),
        "chars_mean": round(float(lens.mean()), 1), "chars_p95": int(np.percentile(lens, 95)), "chars_max": int(lens.max()),
        "tok_est_mean(chars/2)": round(float(lens.mean()) / 2, 1),
    }
res["current_line_example"] = "[B2 場所] 現在地はセルg-9_-4_GL(地上)です。"
res["current_line_chars"] = len(res["current_line_example"])
samp = rng.choice(len(px), 8, replace=False)
res["examples_r30"] = []
for i in samp:
    parts = [p for p in (l1[i], snames[ri[i]] if rd[i] <= 30 else (pn[p2i[i]] if p2d[i] <= 30 else ""),
                         (n3[p3i[i]] + "前") if p3d[i] <= 30 else "") if p]
    res["examples_r30"].append("いまいる場所: " + ("・".join(parts) if parts else "名前のない場所"))
json.dump(res, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
