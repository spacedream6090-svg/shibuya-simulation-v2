"""R-58: 手元の PLATEAU 渋谷区 2025 年度版(CityGML)を地物ごとに数える(読むだけ)。

入力(gitignore 下・書き換えない):
  data/realworld/plateau_2025/13113_shibuya-ku_pref_2025_citygml_1_op/{udx,codelists}
  data/realworld/osm/shibuya_osm_wide_v8.json・floorguide_shibuya.json・station_entrances_overpass.json
  data/plateau/terrain.npz・terrain.json(DEM 由来の 2 m 格子・v1 派生)
出力: docs/research/r58/r58_plateau_inventory.json(集計値のみ)

使い方: python r58_plateau_inventory.py [bldg|brid|ubld|tran|dem|all]

舞台(W1)= OSM v8 meta.bbox (35.6505, 139.6905, 35.6685, 139.7115)。W1 に掛かる 3 次メッシュは
53393585/86/95/96 と 53394505/06(北端の帯)。ローカル平面は src/shibuya/build/geo/common.py と同式。
"""
from __future__ import annotations

import json
import math
import re
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
PL = REPO / "data" / "realworld" / "plateau_2025" / "13113_shibuya-ku_pref_2025_citygml_1_op"
UDX = PL / "udx"
CODEL = PL / "codelists"
OSM = REPO / "data" / "realworld" / "osm"
OUT = Path(__file__).with_name("r58_plateau_inventory.json")

BBOX = (35.6505, 139.6905, 35.6685, 139.7115)
ORIGIN = (35.6595, 139.70062)
M_LAT = 111132.9
M_LON = 111320.0 * math.cos(math.radians(ORIGIN[0]))
GROUND0 = 15.18
W1_MESH = ("53393585", "53393586", "53393595", "53393596", "53394505", "53394506")
X_MIN = (BBOX[1] - ORIGIN[1]) * M_LON
X_MAX = (BBOX[3] - ORIGIN[1]) * M_LON
Y_MIN = (BBOX[0] - ORIGIN[0]) * M_LAT
Y_MAX = (BBOX[2] - ORIGIN[0]) * M_LAT

NS = {
    "gml": "{http://www.opengis.net/gml}",
    "core": "{http://www.opengis.net/citygml/2.0}",
    "bldg": "{http://www.opengis.net/citygml/building/2.0}",
    "brid": "{http://www.opengis.net/citygml/bridge/2.0}",
    "tran": "{http://www.opengis.net/citygml/transportation/2.0}",
    "uro": "{https://www.geospatial.jp/iur/uro/3.2}",
    "grp": "{http://www.opengis.net/citygml/cityobjectgroup/2.0}",
}


def T(q: str) -> str:
    p, n = q.split(":")
    return NS[p] + n


def local(lat, lon):
    return (np.asarray(lon) - ORIGIN[1]) * M_LON, (np.asarray(lat) - ORIGIN[0]) * M_LAT


def in_w1_xy(x, y) -> bool:
    return X_MIN <= x <= X_MAX and Y_MIN <= y <= Y_MAX


def poslist(el) -> np.ndarray:
    v = np.array(el.text.split(), dtype=np.float64)
    return v.reshape(-1, 3)


def codelist(name: str) -> dict:
    t = (CODEL / f"{name}.xml").read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"<gml:Definition.*?</gml:Definition>", t, re.S):
        b = m.group(0)
        d = re.search(r"<gml:description>(.*?)</gml:description>", b, re.S)
        n = re.search(r"<gml:name>(.*?)</gml:name>", b, re.S)
        if n:
            out[n.group(1).strip()] = d.group(1).strip() if d else ""
    return out


def txt(el, q):
    e = el.find(T(q))
    return e.text.strip() if e is not None and e.text else None


def first_txt(el, q):
    for e in el.iter(T(q)):
        if e.text:
            return e.text.strip()
    return None


def members(path: Path):
    """core:cityObjectMember の直下の地物を 1 つずつ返し、返した後に clear する。"""
    for _, el in ET.iterparse(str(path), events=("end",)):
        if el.tag == T("core:cityObjectMember"):
            kids = list(el)
            if kids:
                yield kids[0]
            el.clear()


def shoelace(x, y) -> float:
    return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y)) * 0.5)


def pip(px: float, py: float, poly: list) -> bool:
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi + 1e-300) + xi:
            inside = not inside
        j = i
    return inside


def load_osm():
    return json.loads((OSM / "shibuya_osm_wide_v8.json").read_text(encoding="utf-8"))


# ============================================================ bldg
def run_bldg() -> dict:
    usage_cl = codelist("Building_usage")
    class_cl = codelist("Building_class")
    files = [UDX / "bldg" / f"{m}_bldg_6697_op.gml" for m in W1_MESH]
    recs = []
    per_file = {}
    geom_tags = ["lod0RoofEdge", "lod0FootPrint", "lod1Solid", "lod2Solid", "lod2MultiSurface",
                 "lod3Solid", "lod3MultiSurface", "lod4Solid", "lod4MultiSurface", "interiorRoom",
                 "BuildingPart", "Door", "Window", "IntBuildingInstallation"]
    for f in files:
        n = 0
        for el in members(f):
            if el.tag != T("bldg:Building"):
                continue
            n += 1
            ring = None
            for tag in ("bldg:lod0RoofEdge", "bldg:lod0FootPrint", "bldg:lod1Solid"):
                g = el.find(T(tag))
                if g is not None:
                    pl = next(g.iter(T("gml:posList")), None)
                    if pl is not None:
                        ring = poslist(pl)
                        break
            if ring is None:
                continue
            x, y = local(ring[:, 0], ring[:, 1])
            cx, cy = float(x.mean()), float(y.mean())
            flags = {t: any(True for _ in el.iter(T("bldg:" + t))) for t in geom_tags}
            recs.append({
                "x": cx, "y": cy, "area": shoelace(x, y), "file": f.name[:8],
                "name": txt(el, "gml:name"), "class": txt(el, "bldg:class"), "usage": txt(el, "bldg:usage"),
                "sa": txt(el, "bldg:storeysAboveGround"), "sb": txt(el, "bldg:storeysBelowGround"),
                "h": txt(el, "bldg:measuredHeight"), "lodType": first_txt(el, "uro:lodType"),
                "detailedUsage": first_txt(el, "uro:detailedUsage"), "flags": flags,
            })
        per_file[f.name] = n
        print("bldg", f.name, n, flush=True)
    w1 = [r for r in recs if in_w1_xy(r["x"], r["y"])]

    def num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def lod_level(r):
        fl = r["flags"]
        if fl["lod4Solid"] or fl["lod4MultiSurface"] or fl["interiorRoom"]:
            return "lod4"
        if fl["lod3Solid"] or fl["lod3MultiSurface"]:
            return "lod3"
        if fl["lod2Solid"] or fl["lod2MultiSurface"]:
            return "lod2_" + str(r["lodType"])
        return "lod1_only"

    sa = [num(r["sa"]) for r in w1]
    sb = [num(r["sb"]) for r in w1]
    summary = {
        "files": per_file,
        "n_buildings_all_files": len(recs),
        "n_in_w1": len(w1),
        "lod_in_w1": dict(Counter(lod_level(r) for r in w1)),
        "lodType_values_in_w1": dict(Counter(str(r["lodType"]) for r in w1)),
        "flags_true_in_w1": {t: sum(1 for r in w1 if r["flags"][t]) for t in geom_tags},
        "storeysAbove_hist_in_w1": dict(Counter(str(r["sa"]) for r in w1).most_common(25)),
        "storeysAbove_valid_1_to_200": sum(1 for v in sa if v is not None and 1 <= v <= 200),
        "storeysBelow_hist_in_w1": dict(Counter(str(r["sb"]) for r in w1).most_common(15)),
        "storeysBelow_valid_ge1_le20": sum(1 for v in sb if v is not None and 1 <= v <= 20),
        "measuredHeight_present_in_w1": sum(1 for r in w1 if num(r["h"]) is not None and num(r["h"]) > 0),
        "usage_in_w1": {f"{k} {usage_cl.get(k, '?')}": v for k, v in Counter(str(r["usage"]) for r in w1).most_common(20)},
        "class_in_w1": {f"{k} {class_cl.get(k, '?')}": v for k, v in Counter(str(r["class"]) for r in w1).most_common()},
        "named_in_w1": sorted(
            [{"name": r["name"], "lod": lod_level(r), "sa": r["sa"], "sb": r["sb"], "h": r["h"],
              "usage": f"{r['usage']} {usage_cl.get(str(r['usage']), '?')}"} for r in w1 if r["name"]],
            key=lambda d: d["name"]),
    }
    # 主要施設(フロアガイドの 10 施設)を OSM の足跡で PLATEAU 建物に結ぶ
    osm = load_osm()
    fg = json.loads((OSM / "floorguide_shibuya.json").read_text(encoding="utf-8"))
    fac = []
    for b in fg["buildings"]:
        aliases = b["match"]
        cands = [ob for ob in osm["buildings"] if ob["name"] and ob["name"] in aliases]
        if not cands:
            cands = [ob for ob in osm["buildings"] if ob["name"] and any(a in ob["name"] for a in aliases if len(a) >= 4)]
        hits = []
        for ob in cands:
            poly = ob["footprint"]
            for r in w1:
                if pip(r["x"], r["y"], poly):
                    hits.append(r)
        fg_floors = [fl["f"] for fl in b.get("floors", [])]
        fac.append({
            "facility": aliases[0],
            "osm_buildings": [ob["name"] for ob in cands][:6],
            "plateau_buildings_centroid_in_osm_footprint": len(hits),
            "plateau": [{"name": r["name"], "lod": lod_level(r), "lodType": r["lodType"], "sa": r["sa"], "sb": r["sb"],
                         "h": r["h"], "usage": f"{r['usage']} {usage_cl.get(str(r['usage']), '?')}",
                         "footprint_m2": round(r["area"])} for r in sorted(hits, key=lambda r: -r["area"])[:4]],
            "floorguide_floor_range": [min(fg_floors), max(fg_floors)] if fg_floors else None,
        })
    summary["facilities"] = fac
    return summary


# ============================================================ brid
def run_brid() -> dict:
    fn_cl = codelist("Bridge_function")
    osm = load_osm()
    ped = {"footway", "pedestrian", "steps", "path", "corridor", "elevator"}
    elev_edges = [e for e in osm["edges"] if (e.get("layer") or 0) >= 1]
    rails = [r for r in osm["railways"] if r.get("kind") != "subway"]
    out = []
    files = sorted((UDX / "brid").glob("*.gml"))
    for f in files:
        for el in members(f):
            if el.tag != T("brid:Bridge"):
                continue
            pts = [poslist(p) for p in el.iter(T("gml:posList"))]
            if not pts:
                continue
            a = np.vstack(pts)
            x, y = local(a[:, 0], a[:, 1])
            cx, cy = float(x.mean()), float(y.mean())
            bb = (float(x.min()) - 3, float(y.min()) - 3, float(x.max()) + 3, float(y.max()) + 3)

            def inside(px, py):
                return bb[0] <= px <= bb[2] and bb[1] <= py <= bb[3]

            k = Counter()
            for e in elev_edges:
                if any(inside(px, py) for px, py in e["geometry"]):
                    k[e["klass"]] += 1
            nr = sum(1 for r in rails if any(inside(px, py) for px, py in r["geometry"]))
            has_ped = any(c in ped for c in k)
            has_road = any(c not in ped for c in k)
            guess = ("rail" if nr and not k else "pedestrian" if has_ped and not has_road else
                     "road" if has_road and not has_ped else "mixed" if k else ("rail?" if nr else "none"))
            fcode = txt(el, "brid:function")
            out.append({
                "file": f.name[:8], "in_w1": in_w1_xy(cx, cy), "function": f"{fcode} {fn_cl.get(str(fcode), '?')}",
                "lodType": first_txt(el, "uro:lodType"), "name": txt(el, "gml:name"),
                "x": round(cx, 1), "y": round(cy, 1), "size_m": [round(bb[2] - bb[0] - 6, 1), round(bb[3] - bb[1] - 6, 1)],
                "h_range_m": [round(float(a[:, 2].min()), 2), round(float(a[:, 2].max()), 2)],
                "osm_layer_ge1_edges_in_bbox": dict(k), "osm_rail_in_bbox": nr, "guess_osm": guess,
            })
        print("brid", f.name, flush=True)
    w1 = [b for b in out if b["in_w1"]]
    return {
        "n_all_files": len(out), "n_files": len(files), "n_in_w1": len(w1),
        "function_in_w1": dict(Counter(b["function"] for b in w1)),
        "lodType_in_w1": dict(Counter(str(b["lodType"]) for b in w1)),
        "named_in_w1": sum(1 for b in w1 if b["name"]),
        "guess_osm_in_w1": dict(Counter(b["guess_osm"] for b in w1)),
        "cross_function_x_guess_in_w1": dict(Counter(f"{b['function']} | {b['guess_osm']}" for b in w1)),
        "bridges_in_w1": w1,
    }


# ============================================================ ubld
def ring_key(a: np.ndarray):
    q = np.round(a * 1e7).astype(np.int64)
    if len(q) > 1 and (q[0] == q[-1]).all():
        q = q[:-1]
    return tuple(sorted(map(tuple, q.tolist())))


def run_ubld() -> dict:
    f = UDX / "ubld" / "53393596_ubld_6697_op.gml"
    tree = ET.parse(str(f))
    root = tree.getroot()
    ub = next(root.iter(T("uro:UndergroundBuilding")))
    grp = next(root.iter(T("grp:CityObjectGroup")), None)
    rooms = list(ub.iter(T("bldg:Room")))
    res = {
        "name": txt(ub, "gml:name"),
        "group_name": txt(grp, "gml:name") if grp is not None else None,
        "n_rooms": len(rooms),
        "lodType": first_txt(ub, "uro:lodType"),
        "src_codes": {q: first_txt(ub, "uro:" + q) for q in ("geometrySrcDescLod4", "srcScaleLod4", "publicSurveySrcDescLod4", "thematicSrcDesc")},
        "src_decoded": {
            "geometrySrcDescLod4": codelist("DataQualityAttribute_geometrySrcDesc").get(str(first_txt(ub, "uro:geometrySrcDescLod4"))),
            "srcScaleLod4": codelist("PublicSurveyDataQualityAttribute_srcScale").get(str(first_txt(ub, "uro:srcScaleLod4"))),
            "publicSurveySrcDescLod4": codelist("PublicSurveyDataQualityAttribute_geometrySrcDesc").get(str(first_txt(ub, "uro:publicSurveySrcDescLod4"))),
        },
        "attributes_on_rooms_doors_installations": sorted({c.tag.split("}")[1] for r in rooms for c in r if "lod4" not in c.tag and "boundedBy" not in c.tag and "Installation" not in c.tag}),
    }
    # 面(FloorSurface)を部屋ごと・高さごとに(同一環は畳む)
    seen = set()
    floor_rings = []  # (room_idx, x, y, z_abs_mean, area)
    for ri, room in enumerate(rooms):
        for fs in room.iter(T("bldg:FloorSurface")):
            for pl in fs.iter(T("gml:posList")):
                a = poslist(pl)
                k = ring_key(a)
                if k in seen:
                    continue
                seen.add(k)
                x, y = local(a[:, 0], a[:, 1])
                floor_rings.append((ri, x, y, float(a[:, 2].mean()), shoelace(x, y)))
    res["floor_rings_unique"] = len(floor_rings)
    res["floor_area_unique_m2_by_room"] = {str(ri): round(sum(r[4] for r in floor_rings if r[0] == ri), 1) for ri in range(len(rooms))}
    res["floor_area_unique_m2_total"] = round(sum(r[4] for r in floor_rings), 1)
    # 高さ(絶対・0.5 m 刻み)ごとの床面積
    zh = defaultdict(float)
    for r in floor_rings:
        zh[round(r[3] * 2) / 2] += r[4]
    res["floor_area_by_abs_height_0p5m"] = {f"{k:.1f}": round(v, 1) for k, v in sorted(zh.items()) if v >= 50}
    res["room_z_abs"] = {str(ri): [round(min(r[3] for r in floor_rings if r[0] == ri), 2), round(max(r[3] for r in floor_rings if r[0] == ri), 2)] for ri in range(len(rooms)) if any(r[0] == ri for r in floor_rings)}
    # 扉・閉鎖面・設備
    doors_ext = sum(1 for w in ub.iter(T("bldg:WallSurface")) for _ in w.iter(T("bldg:Door")))
    doors_int = sum(1 for w in ub.iter(T("bldg:InteriorWallSurface")) for _ in w.iter(T("bldg:Door")))
    res["doors"] = {"total": sum(1 for _ in ub.iter(T("bldg:Door"))), "in_WallSurface": doors_ext, "in_InteriorWallSurface": doors_int}
    res["closure_surfaces"] = sum(1 for _ in ub.iter(T("bldg:ClosureSurface")))
    res["int_installations"] = sum(1 for _ in ub.iter(T("bldg:IntBuildingInstallation")))
    # 地上との接続: DEM(terrain.npz・ground0 相対)に対して高さが地表 -1.0 m 以上に届く頂点を 10 m で束ねる
    terr = json.loads((REPO / "data" / "plateau" / "terrain.json").read_text(encoding="utf-8"))
    H = np.load(REPO / "data" / "plateau" / "terrain.npz")["heights"]

    def ground_abs(x, y):
        i = int((x - terr["x0"]) / terr["cell_m"])
        j = int((y - terr["y0"]) / terr["cell_m"])
        if 0 <= j < H.shape[0] and 0 <= i < H.shape[1]:
            return float(H[j, i]) + GROUND0
        return None

    res["terrain_check_origin_abs_m"] = ground_abs(0.0, 0.0)
    all_pts = []
    for pl in ub.iter(T("gml:posList")):
        a = poslist(pl)
        x, y = local(a[:, 0], a[:, 1])
        all_pts.append(np.column_stack([x, y, a[:, 2]]))
    P = np.vstack(all_pts)
    res["extent_local_m"] = [round(float(P[:, 0].min()), 1), round(float(P[:, 1].min()), 1), round(float(P[:, 0].max()), 1), round(float(P[:, 1].max()), 1)]
    res["z_abs_range"] = [round(float(P[:, 2].min()), 2), round(float(P[:, 2].max()), 2)]
    top = []
    for x, y, z in P[:: max(1, len(P) // 200000)]:
        g = ground_abs(x, y)
        if g is not None and z >= g - 1.0:
            top.append((x, y))
    clusters = []
    for x, y in top:
        for c in clusters:
            if (c[0] - x) ** 2 + (c[1] - y) ** 2 <= 100.0:
                c[2] += 1
                break
        else:
            clusters.append([x, y, 1])
    res["near_ground_vertex_clusters_10m"] = len(clusters)
    # OSM 駅出入口(45)のうち、地下街の床の 15 m 以内にあるもの
    ent = json.loads((OSM / "station_entrances_overpass.json").read_text(encoding="utf-8"))
    els = ent.get("elements", ent)
    fl_pts = np.vstack([np.column_stack([r[1], r[2]]) for r in floor_rings])
    near_ent = []
    for e in els:
        ex, ey = local(e["lat"], e["lon"])
        dmin = float(np.sqrt(((fl_pts[:, 0] - ex) ** 2 + (fl_pts[:, 1] - ey) ** 2).min()))
        if dmin <= 15.0:
            tg = e.get("tags", {})
            near_ent.append({"ref": tg.get("ref"), "name": tg.get("name"), "kind": tg.get("railway"), "d_m": round(dmin, 1)})
    res["osm_station_entrances_total"] = len(els)
    res["osm_station_entrances_within_15m_of_floor"] = len(near_ent)
    res["osm_station_entrances_near_list"] = near_ent
    # 床の上にある OSM 名前つき建物(床の格子 2 m と足跡の重なり)
    osm = load_osm()
    grid = set()
    for r in floor_rings:
        x, y = r[1], r[2]
        for gx in range(int(x.min() // 2), int(x.max() // 2) + 1):
            for gy in range(int(y.min() // 2), int(y.max() // 2) + 1):
                if pip(gx * 2 + 1, gy * 2 + 1, list(zip(x, y))):
                    grid.add((gx, gy))
    res["floor_union_footprint_m2_2m_grid"] = len(grid) * 4
    # 高さの帯ごとの床の格子と、その上を通る名前つき道路(Overpass road_names・同 bbox)
    bands = {"abs<3m": (-99, 3), "3-7m": (3, 7), "7-12m": (7, 12), "12m+": (12, 99)}
    rn = json.loads((OSM / "road_names_overpass_20260928.json").read_text(encoding="utf-8"))
    band_info = {}
    for bname, (lo, hi) in bands.items():
        g2 = set()
        for r in floor_rings:
            if not (lo <= r[3] < hi):
                continue
            x, y = r[1], r[2]
            poly = list(zip(x, y))
            for gx in range(int(x.min() // 2), int(x.max() // 2) + 1):
                for gy in range(int(y.min() // 2), int(y.max() // 2) + 1):
                    if pip(gx * 2 + 1, gy * 2 + 1, poly):
                        g2.add((gx, gy))
        names = Counter()
        for w in rn.get("elements", []):
            nm = (w.get("tags") or {}).get("name")
            if not nm:
                continue
            for p in w.get("geometry", []):
                px, py = local(p["lat"], p["lon"])
                if (int(float(px) // 2), int(float(py) // 2)) in g2:
                    names[nm] += 1
        xs = [gx * 2 for gx, _ in g2] or [0]
        ys = [gy * 2 for _, gy in g2] or [0]
        band_info[bname] = {"footprint_m2": len(g2) * 4, "extent_local_m": [min(xs), min(ys), max(xs), max(ys)],
                            "named_roads_over_floor": dict(names.most_common(8))}
    res["floor_by_height_band"] = band_info
    over = []
    for ob in osm["buildings"]:
        fp = ob["footprint"]
        xs = [p[0] for p in fp]
        ys = [p[1] for p in fp]
        if max(xs) < res["extent_local_m"][0] or min(xs) > res["extent_local_m"][2] or max(ys) < res["extent_local_m"][1] or min(ys) > res["extent_local_m"][3]:
            continue
        n = sum(1 for (gx, gy) in grid if min(xs) <= gx * 2 + 1 <= max(xs) and min(ys) <= gy * 2 + 1 <= max(ys) and pip(gx * 2 + 1, gy * 2 + 1, fp))
        if n:
            over.append({"osm_name": ob["name"] or "(無名)", "kind": ob["kind"], "overlap_m2": n * 4})
    over.sort(key=lambda d: -d["overlap_m2"])
    res["osm_buildings_above_floor_top15"] = over[:15]
    res["floor_under_osm_buildings_m2"] = sum(d["overlap_m2"] for d in over)
    # OSM の地下(layer<0)の辺のうち、床の格子に載る長さの割合
    ug_len = ug_in = 0.0
    for e in osm["edges"]:
        if (e.get("layer") or 0) < 0:
            g = e["geometry"]
            for (x0, y0), (x1, y1) in zip(g, g[1:]):
                L = math.hypot(x1 - x0, y1 - y0)
                n = max(1, int(L // 2))
                for i in range(n):
                    t = (i + 0.5) / n
                    px, py = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
                    ug_len += L / n
                    if (int(px // 2), int(py // 2)) in grid or any((int(px // 2) + dx, int(py // 2) + dy) in grid for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                        ug_in += L / n
    res["osm_underground_edges_len_m"] = round(ug_len, 1)
    res["osm_underground_edges_len_on_ubld_floor_m"] = round(ug_in, 1)
    subs = [r for r in osm["railways"] if r.get("kind") == "subway"]
    res["osm_subway_lines_touching_floor"] = sorted({r["name"] for r in subs if any((int(px // 2), int(py // 2)) in grid for px, py in r["geometry"])})
    return res


# ============================================================ tran
def fill_ring(mask: np.ndarray, gx: np.ndarray, gy: np.ndarray) -> None:
    """格子座標の環を走査線で塗る(画素中心が内側なら True・和集合)。"""
    ny, nx = mask.shape
    j0 = max(0, int(math.floor(gy.min())))
    j1 = min(ny - 1, int(math.ceil(gy.max())))
    if j1 < j0:
        return
    x0, y0 = gx, gy
    x1, y1 = np.roll(gx, -1), np.roll(gy, -1)
    yc = np.arange(j0, j1 + 1) + 0.5
    Y = yc[:, None]
    cond = ((y0[None, :] <= Y) & (y1[None, :] > Y)) | ((y1[None, :] <= Y) & (y0[None, :] > Y))
    with np.errstate(divide="ignore", invalid="ignore"):
        X = x0[None, :] + (Y - y0[None, :]) * (x1 - x0)[None, :] / (y1 - y0)[None, :]
    for r in range(len(yc)):
        xs = np.sort(X[r][cond[r]])
        for a, b in zip(xs[0::2], xs[1::2]):
            i0 = max(0, int(math.ceil(a - 0.5)))
            i1 = min(nx - 1, int(math.floor(b - 0.5)))
            if i1 >= i0:
                mask[j0 + r, i0:i1 + 1] = True


def distance_steps(mask: np.ndarray, max_steps: int = 80) -> np.ndarray:
    """侵食の回数(4 近傍と 8 近傍を交互=八角形距離・Euclid の近似)。境界の画素が 1。"""
    d = np.zeros(mask.shape, dtype=np.uint16)
    cur = mask.copy()
    k = 0
    while cur.any() and k < max_steps:
        k += 1
        d[cur] = k
        nxt = cur.copy()
        nxt[1:, :] &= cur[:-1, :]
        nxt[:-1, :] &= cur[1:, :]
        nxt[:, 1:] &= cur[:, :-1]
        nxt[:, :-1] &= cur[:, 1:]
        if k % 2 == 0:
            nxt[1:, 1:] &= cur[:-1, :-1]
            nxt[1:, :-1] &= cur[:-1, 1:]
            nxt[:-1, 1:] &= cur[1:, :-1]
            nxt[:-1, :-1] &= cur[1:, 1:]
        nxt[0, :] = nxt[-1, :] = False
        nxt[:, 0] = nxt[:, -1] = False
        cur = nxt
    return d


def ridge_widths(d: np.ndarray, res: float) -> np.ndarray:
    """尾根(8 近傍の最大以上)の画素の幅の推定 = (2d-1)·res [m]。"""
    m = d > 0
    mx = np.zeros_like(d)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            s = np.roll(np.roll(d, dy, axis=0), dx, axis=1)
            mx = np.maximum(mx, s)
    r = m & (d >= mx)
    return (2.0 * d[r].astype(np.float64) - 1.0) * res


def selftest_width(res: float = 0.25) -> dict:
    out = {}
    for w in (1.0, 2.0, 3.0, 5.0, 8.0):
        for ang in (0, 30, 45):
            n = 400
            mask = np.zeros((n, n), dtype=bool)
            L = 60.0
            c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            pts = [(-L / 2, -w / 2), (L / 2, -w / 2), (L / 2, w / 2), (-L / 2, w / 2)]
            gx = np.array([(n * res / 2 + px * c - py * s) / res for px, py in pts])
            gy = np.array([(n * res / 2 + px * s + py * c) / res for px, py in pts])
            fill_ring(mask, gx, gy)
            wd = ridge_widths(distance_steps(mask), res)
            out[f"w{w}_a{ang}"] = round(float(np.median(wd)), 2)
    return out


def run_tran() -> dict:
    fn_ta = codelist("TrafficArea_function")
    fn_aux = codelist("AuxiliaryTrafficArea_function")
    sec_cl = codelist("RoadStructureAttribute_sectionType")
    files = [UDX / "tran" / f"{m}_tran_6697_op.gml" for m in W1_MESH]
    area = defaultdict(float)
    nfeat = Counter()
    rings_by = defaultdict(list)  # "side"/"road"/"all" -> list of (x,y)
    road_lod = Counter()
    road_sec = Counter()
    seen = set()
    width_attr = 0
    for f in files:
        for el in members(f):
            if el.tag != T("tran:Road"):
                continue
            pl = next(el.iter(T("gml:posList")), None)
            if pl is not None:
                a = poslist(pl)[:1]
                x, y = local(a[:, 0], a[:, 1])
                if in_w1_xy(float(x[0]), float(y[0])):
                    road_lod[str(first_txt(el, "uro:lodType"))] += 1
                    s = first_txt(el, "uro:sectionType")
                    road_sec[f"{s} {sec_cl.get(str(s), '?')}"] += 1
            width_attr += sum(1 for c in el.iter() if c.tag.endswith("}width"))
            for ta in list(el.iter(T("tran:TrafficArea"))) + list(el.iter(T("tran:AuxiliaryTrafficArea"))):
                aux = ta.tag == T("tran:AuxiliaryTrafficArea")
                code = txt(ta, "tran:function")
                lod = None
                for L in (3, 2, 1):
                    ms = ta.find(T(f"tran:lod{L}MultiSurface"))
                    if ms is not None:
                        lod = L
                        break
                if lod is None:
                    continue
                key = f"{'aux' if aux else 'ta'}:{code} {(fn_aux if aux else fn_ta).get(str(code), '?')}|lod{lod}"
                got = False
                for poly in ms.iter(T("gml:Polygon")):
                    ext = poly.find(T("gml:exterior"))
                    if ext is None:
                        continue
                    pl = next(ext.iter(T("gml:posList")), None)
                    if pl is None:
                        continue
                    a = poslist(pl)
                    k = ring_key(a[:, :2])
                    if k in seen:
                        continue
                    seen.add(k)
                    x, y = local(a[:, 0], a[:, 1])
                    if not in_w1_xy(float(x.mean()), float(y.mean())):
                        continue
                    got = True
                    area[key] += shoelace(x, y)
                    cls = "side" if (not aux and str(code) in ("2000", "2010", "2020")) else "road" if (not aux and str(code) in ("1000", "1020")) else "other"
                    rings_by[cls].append((x, y))
                if got:
                    nfeat[key] += 1
        print("tran", f.name, flush=True)
    out = {
        "files": [f.name for f in files],
        "road_lodType_in_w1": dict(road_lod),
        "road_sectionType_in_w1": dict(road_sec),
        "width_like_elements": width_attr,
        "traffic_area_unique_rings_area_m2_in_w1": {k: round(v, 1) for k, v in sorted(area.items())},
        "traffic_area_features_in_w1": dict(sorted(nfeat.items())),
        "note": "ring dedup = 同一頂点列(緯度経度 1e-7 度)の環を全ファイル通しで 1 枚に畳む。LOD2 と LOD3 の同じ歩道の重なりは畳めない(頂点が違う)→ 面積は重なり込み。和集合の面積は下の raster_union を見る",
    }
    # ---- 0.25 m の和集合ラスタ(W1)
    res = 0.25
    nx = int(math.ceil((X_MAX - X_MIN) / res))
    ny = int(math.ceil((Y_MAX - Y_MIN) / res))
    t0 = time.time()
    masks = {}
    for cls in ("side", "road", "other"):
        m = np.zeros((ny, nx), dtype=bool)
        for x, y in rings_by[cls]:
            fill_ring(m, (x - X_MIN) / res, (y - Y_MIN) / res)
        masks[cls] = m
    out["raster_res_m"] = res
    out["raster_union_m2"] = {k: round(float(v.sum()) * res * res, 1) for k, v in masks.items()}
    allm = masks["side"] | masks["road"] | masks["other"]
    out["raster_union_all_m2"] = round(float(allm.sum()) * res * res, 1)
    out["w1_area_m2"] = round((X_MAX - X_MIN) * (Y_MAX - Y_MIN), 1)
    print("raster", round(time.time() - t0, 1), "s", flush=True)
    # ---- 幅
    out["width_selftest_median_m"] = selftest_width(res)
    bins = [0, 1, 2, 3, 4, 6, 10, 20, 1e9]
    for cls, m in (("sidewalk_2000", masks["side"]), ("roadway_1000_1020", masks["road"])):
        d = distance_steps(m, 160)
        w = ridge_widths(d, res)
        h = np.histogram(w, bins=bins)[0]
        out[f"width_{cls}"] = {
            "n_ridge_px": int(w.size), "ridge_len_m_approx": round(w.size * res, 1),
            "quantiles_m": {q: round(float(np.quantile(w, q / 100)), 2) for q in (10, 25, 50, 75, 90)},
            "hist_share": {f"{bins[i]}-{bins[i+1] if bins[i+1] < 1e8 else 'inf'}": round(float(h[i] / max(1, w.size)), 4) for i in range(len(h))},
        }
        if cls == "sidewalk_2000":
            dside = d
        print("width", cls, round(time.time() - t0, 1), "s", flush=True)
    # ---- OSM の線が PLATEAU の面に載るか(1 m 格子に落として正方の膨張)
    k = int(round(1.0 / res))
    ny1, nx1 = ny // k, nx // k

    def down(m):
        return m[: ny1 * k, : nx1 * k].reshape(ny1, k, nx1, k).any(axis=(1, 3))

    def dilate(m, r):
        c = np.pad(m.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
        J, I = np.mgrid[0:m.shape[0], 0:m.shape[1]]
        j0, j1 = np.clip(J - r, 0, m.shape[0]), np.clip(J + r + 1, 0, m.shape[0])
        i0, i1 = np.clip(I - r, 0, m.shape[1]), np.clip(I + r + 1, 0, m.shape[1])
        return (c[j1, i1] - c[j0, i1] - c[j1, i0] + c[j0, i0]) > 0

    all1 = dilate(down(allm), 3)
    side1 = dilate(down(masks["side"]), 12)
    osm = load_osm()
    tot = Counter()
    on_surface = Counter()
    near_side = Counter()
    for e in osm["edges"]:
        if e.get("layer"):
            continue
        g = e["geometry"]
        for (x0, y0), (x1, y1) in zip(g, g[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            n = max(1, int(L // 2))
            for i in range(n):
                t = (i + 0.5) / n
                px, py = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
                if not in_w1_xy(px, py):
                    continue
                ii, jj = int((px - X_MIN)), int((py - Y_MIN))
                if not (0 <= jj < ny1 and 0 <= ii < nx1):
                    continue
                tot[e["klass"]] += L / n
                if all1[jj, ii]:
                    on_surface[e["klass"]] += L / n
                    if side1[jj, ii]:
                        near_side[e["klass"]] += L / n
    out["osm_GL_edges_len_m_in_w1"] = {c: round(v) for c, v in tot.most_common()}
    out["osm_GL_edges_share_on_plateau_tran_surface_3m"] = {c: round(on_surface[c] / v, 3) for c, v in tot.most_common()}
    out["osm_GL_edges_share_on_surface_and_sidewalk_within_12m"] = {c: round(near_side[c] / v, 3) for c, v in tot.most_common()}
    out["osm_GL_all_len_m"] = round(sum(tot.values()))
    out["osm_GL_share_on_surface_all"] = round(sum(on_surface.values()) / max(1, sum(tot.values())), 3)
    # ---- 歩行空間ネットワーク(2020)の幅員区分と PLATEAU 実測幅の突き合わせ
    link_p = REPO / "data" / "research_cache" / "r58" / "shibuyananbu_link_2020.geojson"
    if link_p.exists():
        lk = json.loads(link_p.read_text(encoding="utf-8"))
        cross = defaultdict(list)
        for ft in lk["features"]:
            p = ft.get("properties") or {}
            if str(p.get("rt_struct")) != "1":
                continue
            co = (ft.get("geometry") or {}).get("coordinates") or []
            if len(co) < 2:
                continue
            mid = co[len(co) // 2]
            mx, my = local(mid[1], mid[0])
            ii, jj = int((float(mx) - X_MIN) / res), int((float(my) - Y_MIN) / res)
            r = int(4.0 / res)
            if not (r <= jj < ny - r and r <= ii < nx - r):
                continue
            win = dside[jj - r: jj + r + 1, ii - r: ii + r + 1]
            if win.max() == 0:
                cross[str(p.get("width"))].append(None)
            else:
                cross[str(p.get("width"))].append((2.0 * float(win.max()) - 1.0) * res)
        out["hokoukukan2020_width_class_vs_plateau_width"] = {
            c: {"n": len(v), "no_plateau_sidewalk_within_4m": sum(1 for z in v if z is None),
                "plateau_width_median_m": round(float(np.median([z for z in v if z is not None])), 2) if any(z is not None for z in v) else None,
                "plateau_width_p25_p75": [round(float(np.quantile([z for z in v if z is not None], q)), 2) for q in (0.25, 0.75)] if sum(1 for z in v if z is not None) >= 4 else None}
            for c, v in sorted(cross.items())
        }
    return out


# ============================================================ dem
def run_dem() -> dict:
    rx = re.compile(rb"<gml:posList>([^<]*)</gml:posList>")
    out = {}
    verts = set()
    edges = []
    slopes = []
    areas = []
    decimals = Counter()
    ntri = 0
    for name in ("533935_dem_6697_op.gml", "533945_dem_6697_op.gml"):
        p = UDX / "dem" / name
        head = p.open("rb").read(200000).decode("utf-8", "ignore")
        out[name] = {"src": {q: (re.search(rf"<uro:{q}[^>]*>([^<]*)<", head) or [None, None])[1] for q in ("geometrySrcDescLod1", "publicSurveySrcDescLod1", "srcScaleLod1", "thematicSrcDesc")}}
        n_all = 0
        buf = b""
        with p.open("rb") as fh:
            while True:
                chunk = fh.read(1 << 24)
                if not chunk:
                    break
                buf += chunk
                last = buf.rfind(b"</gml:posList>")
                if last < 0:
                    continue
                cut = last + len(b"</gml:posList>")
                for m in rx.finditer(buf, 0, cut):
                    n_all += 1
                    s = m.group(1).split()
                    lat0, lon0 = float(s[0]), float(s[1])
                    if not (BBOX[0] <= lat0 <= BBOX[2] and BBOX[1] <= lon0 <= BBOX[3]):
                        continue
                    v = np.array(s, dtype=np.float64).reshape(-1, 3)[:3]
                    if ntri < 2000:
                        decimals[len(s[2].split(b".")[1]) if b"." in s[2] else 0] += 1
                    ntri += 1
                    x, y = local(v[:, 0], v[:, 1])
                    z = v[:, 2]
                    for i in range(3):
                        verts.add((round(float(x[i]), 2), round(float(y[i]), 2)))
                        j = (i + 1) % 3
                        edges.append(math.hypot(x[j] - x[i], y[j] - y[i]))
                    ux, uy, uz = x[1] - x[0], y[1] - y[0], z[1] - z[0]
                    vx, vy, vz = x[2] - x[0], y[2] - y[0], z[2] - z[0]
                    nx_, ny_, nz_ = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
                    a2 = abs(nz_)
                    areas.append(a2 / 2)
                    if a2 > 0:
                        slopes.append(math.hypot(nx_, ny_) / a2 * 100.0)
                buf = buf[cut:]
        out[name]["n_triangles_all"] = n_all
        print("dem", name, n_all, flush=True)
    e = np.array(edges)
    s = np.array(slopes)
    a = np.array(areas)
    out["w1"] = {
        "n_triangles": ntri, "n_unique_vertices": len(verts),
        "vertex_density_per_100m2": round(len(verts) / ((X_MAX - X_MIN) * (Y_MAX - Y_MIN)) * 100, 3),
        "edge_len_m_quantiles": {q: round(float(np.quantile(e, q / 100)), 2) for q in (10, 50, 90, 99)},
        "tri_area_m2_quantiles": {q: round(float(np.quantile(a, q / 100)), 1) for q in (10, 50, 90)},
        "slope_pct_quantiles_by_triangle": {q: round(float(np.quantile(s, q / 100)), 2) for q in (50, 75, 90, 95, 99)},
        "slope_share_area_weighted": {f">{t}%": round(float(a[s > t].sum() / a.sum()), 4) for t in (2, 5, 8, 12)} if len(s) == len(a) else None,
        "z_decimals_sample": dict(decimals),
    }
    cl1 = codelist("PublicSurveyDataQualityAttribute_geometrySrcDesc")
    cl2 = codelist("PublicSurveyDataQualityAttribute_srcScale")
    for name in ("533935_dem_6697_op.gml", "533945_dem_6697_op.gml"):
        sc = out[name]["src"]
        sc["publicSurveySrcDescLod1_decoded"] = cl1.get(str(sc.get("publicSurveySrcDescLod1")))
        sc["srcScaleLod1_decoded"] = cl2.get(str(sc.get("srcScaleLod1")))
    # OSM 地上の辺ごとの勾配(派生 terrain.npz 2 m 格子で端点の高さ)
    terr = json.loads((REPO / "data" / "plateau" / "terrain.json").read_text(encoding="utf-8"))
    H = np.load(REPO / "data" / "plateau" / "terrain.npz")["heights"]

    def hz(x, y):
        i = int((x - terr["x0"]) / terr["cell_m"])
        j = int((y - terr["y0"]) / terr["cell_m"])
        if 0 <= j < H.shape[0] and 0 <= i < H.shape[1]:
            return float(H[j, i])
        return None

    osm = load_osm()
    grades = []
    lens = []
    for ed in osm["edges"]:
        if ed.get("layer"):
            continue
        g = ed["geometry"]
        z0, z1 = hz(*g[0]), hz(*g[-1])
        if z0 is None or z1 is None or ed["length"] < 10:
            continue
        grades.append(abs(z1 - z0) / ed["length"] * 100)
        lens.append(ed["length"])
    gr = np.array(grades)
    ln = np.array(lens)
    out["osm_GL_edge_grade_endpoints"] = {
        "n_edges_ge10m": int(gr.size),
        "grade_pct_quantiles": {q: round(float(np.quantile(gr, q / 100)), 2) for q in (50, 75, 90, 95, 99)},
        "len_share": {f">{t}%": round(float(ln[gr > t].sum() / ln.sum()), 4) for t in (2, 5, 8, 12)},
        "terrain_grid": {k: terr[k] for k in ("x0", "y0", "cell_m", "nx", "ny", "n_tin_points", "n_tin_triangles", "z_min_m", "z_max_m")},
    }
    return out



def _scrub_osm_raw(x, under_osm=False):
    """OSM の生値(名前・ref)を出力から落とす(ライセンス台帳の設計原則 ②=出力に OSM 生値を載せない・第312 親)。

    ``osm_`` で始まる鍵の下では、辞書の ``name``/``osm_name``/``ref`` を消し、文字列の並びは件数に置き換える。
    """
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            osm = under_osm or str(k).startswith("osm_")
            if osm and k in ("name", "osm_name", "ref"):
                continue
            if osm and isinstance(v, list) and v and all(isinstance(e, str) for e in v):
                out[str(k) + "_n"] = len(v)
                continue
            out[k] = _scrub_osm_raw(v, osm)
        return out
    if isinstance(x, list):
        return [_scrub_osm_raw(e, under_osm) for e in x]
    return x


def main() -> None:
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    prev = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    runs = {"bldg": run_bldg, "brid": run_brid, "ubld": run_ubld, "tran": run_tran, "dem": run_dem}
    for k, fn in runs.items():
        if what in (k, "all"):
            t0 = time.time()
            prev[k] = fn()
            prev[k]["_seconds"] = round(time.time() - t0, 1)
            OUT.write_text(json.dumps(_scrub_osm_raw(prev), ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    prev["_meta"] = {"bbox_w1": BBOX, "w1_mesh": W1_MESH, "origin": ORIGIN, "ground0": GROUND0}
    OUT.write_text(json.dumps(_scrub_osm_raw(prev), ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
