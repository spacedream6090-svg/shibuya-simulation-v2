"""R-58: 歩行空間ネットワークデータ(G空間情報センター dataset 0401)の渋谷 2 地区を数える。

入力(gitignore 下・読むだけ): data/research_cache/r58/
  shibuya_link_2017.geojson / shibuya_node_2017.geojson / shibuya_facility_2017.geojson
  shibuyananbu_link_2020.geojson / shibuyananbu_node_2020.geojson
出力: docs/research/r58/r58_hokoukukan.json(集計値のみ・生値なし)

舞台(W1)= OSM v8 meta.bbox (35.6505, 139.6905, 35.6685, 139.7115)。
座標は GeoJSON の [lon, lat]。ローカル平面は src/shibuya/build/geo/common.py と同じ式。
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "data" / "research_cache" / "r58"
OUT = Path(__file__).with_name("r58_hokoukukan.json")
BBOX = (35.6505, 139.6905, 35.6685, 139.7115)
ORIGIN = (35.6595, 139.70062)
M_LAT = 111132.9
M_LON = 111320.0 * math.cos(math.radians(ORIGIN[0]))


def in_w1(lat: float, lon: float) -> bool:
    return BBOX[0] <= lat <= BBOX[2] and BBOX[1] <= lon <= BBOX[3]


def seg_len(coords: list) -> float:
    s = 0.0
    for (x0, y0, *_), (x1, y1, *_) in zip(coords, coords[1:]):
        s += math.hypot((x1 - x0) * M_LON, (y1 - y0) * M_LAT)
    return s


def flat_lines(geom: dict) -> list:
    t = geom.get("type")
    if t == "LineString":
        return [geom["coordinates"]]
    if t == "MultiLineString":
        return list(geom["coordinates"])
    return []


def fill_rates(feats: list) -> dict:
    keys: Counter = Counter()
    filled: Counter = Counter()
    for f in feats:
        for k, v in (f.get("properties") or {}).items():
            keys[k] += 1
            if v not in (None, "", "99", 99):
                filled[k] += 1
    n = len(feats)
    return {k: {"present": keys[k], "filled_not_99": filled[k], "share_filled": round(filled[k] / n, 4) if n else None} for k in keys}


def value_hist(feats: list, key: str) -> dict:
    return dict(Counter(str((f.get("properties") or {}).get(key)) for f in feats).most_common(30))


def analyse_links(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    feats = d["features"]
    geom_types = Counter((f.get("geometry") or {}).get("type") for f in feats)
    tot_len = 0.0
    w1_len = 0.0
    n_w1 = 0
    lat_rng = [90.0, -90.0]
    lon_rng = [180.0, -180.0]
    for f in feats:
        for line in flat_lines(f.get("geometry") or {}):
            L = seg_len(line)
            tot_len += L
            mid = line[len(line) // 2]
            lon, lat = mid[0], mid[1]
            lat_rng = [min(lat_rng[0], lat), max(lat_rng[1], lat)]
            lon_rng = [min(lon_rng[0], lon), max(lon_rng[1], lon)]
            if in_w1(lat, lon):
                w1_len += L
                n_w1 += 1
    w1_len_by = {k: Counter() for k in ("rt_struct", "route_type", "width", "vtcl_slope", "lev_diff", "roof", "elevator")}
    for f in feats:
        p = f.get("properties") or {}
        for line in flat_lines(f.get("geometry") or {}):
            mid = line[len(line) // 2]
            if in_w1(mid[1], mid[0]):
                L = seg_len(line)
                for k in w1_len_by:
                    if k in p:
                        w1_len_by[k][str(p[k])] += L
    props = fill_rates(feats)
    hist_keys = [k for k in ("rt_struct", "route_type", "direction", "width", "vtcl_slope", "lev_diff",
                             "tfc_signal", "brail_tile", "elevator", "roof", "tfc_restr", "w_min",
                             "vSlope_max", "stair", "handrail", "floor", "door_type", "condition")
                 if k in props]
    return {
        "file": path.name,
        "crs": (d.get("crs") or {}).get("properties"),
        "n_features": len(feats),
        "geometry_types": dict(geom_types),
        "total_length_m": round(tot_len, 1),
        "midpoint_lat_range": [round(v, 5) for v in lat_rng],
        "midpoint_lon_range": [round(v, 5) for v in lon_rng],
        "n_features_midpoint_in_w1": n_w1,
        "length_in_w1_m": round(w1_len, 1),
        "property_fill": props,
        "value_hist": {k: value_hist(feats, k) for k in hist_keys},
        "w1_length_m_by_value": {k: {c: round(v) for c, v in sorted(cnt.items())} for k, cnt in w1_len_by.items() if cnt},
        "w1_count_by_route_type": dict(Counter(str((f.get("properties") or {}).get("route_type")) for f in feats
                                               for line in flat_lines(f.get("geometry") or {})[:1]
                                               if in_w1(line[len(line) // 2][1], line[len(line) // 2][0]))),
    }


def analyse_nodes(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    feats = d["features"]
    n_w1 = 0
    for f in feats:
        c = (f.get("geometry") or {}).get("coordinates") or [None, None]
        if c[0] is not None and in_w1(c[1], c[0]):
            n_w1 += 1
    props = fill_rates(feats)
    return {
        "file": path.name,
        "n_features": len(feats),
        "n_in_w1": n_w1,
        "property_fill": props,
        "value_hist": {k: value_hist(feats, k) for k in ("floor", "in_out") if k in props},
    }


def analyse_facility(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    feats = d["features"]
    return {"file": path.name, "n_features": len(feats), "property_keys": sorted(fill_rates(feats))}


def local_pts(path: Path, step_m: float = 5.0) -> list[tuple[float, float]]:
    """リンクを step_m 間隔で標本化したローカル座標点(被覆と重なりの計算用)。"""
    d = json.loads(path.read_text(encoding="utf-8"))
    pts: list[tuple[float, float]] = []
    for f in d["features"]:
        for line in flat_lines(f.get("geometry") or {}):
            xy = [((c[0] - ORIGIN[1]) * M_LON, (c[1] - ORIGIN[0]) * M_LAT) for c in line]
            for (x0, y0), (x1, y1) in zip(xy, xy[1:]):
                n = max(1, int(math.hypot(x1 - x0, y1 - y0) // step_m))
                for i in range(n):
                    t = i / n
                    pts.append((x0 + t * (x1 - x0), y0 + t * (y1 - y0)))
    return pts


def coverage(pts_a: list, pts_b: list) -> dict:
    """100 m 格子(W1 内)で触れたセル数と、A の標本点のうち B から 5 m 以内の割合。"""
    x_min = (BBOX[1] - ORIGIN[1]) * M_LON
    x_max = (BBOX[3] - ORIGIN[1]) * M_LON
    y_min = (BBOX[0] - ORIGIN[0]) * M_LAT
    y_max = (BBOX[2] - ORIGIN[0]) * M_LAT
    nx = int(math.ceil((x_max - x_min) / 100.0))
    ny = int(math.ceil((y_max - y_min) / 100.0))

    def cells(pts: list) -> set:
        s = set()
        for x, y in pts:
            if x_min <= x < x_max and y_min <= y < y_max:
                s.add((int((x - x_min) // 100), int((y - y_min) // 100)))
        return s

    ca, cb = cells(pts_a), cells(pts_b)
    grid_b = {}
    for x, y in pts_b:
        grid_b.setdefault((int(x // 5), int(y // 5)), []).append((x, y))
    near = 0
    for x, y in pts_a:
        gx, gy = int(x // 5), int(y // 5)
        hit = False
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for bx, by in grid_b.get((gx + dx, gy + dy), ()):
                    if (bx - x) ** 2 + (by - y) ** 2 <= 25.0:
                        hit = True
                        break
                if hit:
                    break
            if hit:
                break
        near += hit
    rows = []
    for j in range(ny - 1, -1, -1):  # 北が上。A だけ=a / B だけ=b / 両方=# / なし=.
        rows.append("".join("#" if (i, j) in ca and (i, j) in cb else "a" if (i, j) in ca else "b" if (i, j) in cb else "." for i in range(nx)))
    return {
        "w1_grid_100m": [nx, ny, nx * ny],
        "cells_touched_2017": len(ca),
        "cells_touched_2020": len(cb),
        "cells_touched_union": len(ca | cb),
        "cells_touched_both": len(ca & cb),
        "share_2017_samples_within_5m_of_2020": round(near / max(1, len(pts_a)), 4),
        "map_north_up_a2017_b2020": rows,
    }


def main() -> None:
    cov = coverage(local_pts(SRC / "shibuya_link_2017.geojson"), local_pts(SRC / "shibuyananbu_link_2020.geojson"))
    out = {
        "coverage": cov,
        "bbox_w1": BBOX,
        "shibuya_2017": {
            "link": analyse_links(SRC / "shibuya_link_2017.geojson"),
            "node": analyse_nodes(SRC / "shibuya_node_2017.geojson"),
            "facility": analyse_facility(SRC / "shibuya_facility_2017.geojson"),
        },
        "shibuyananbu_2020": {
            "link": analyse_links(SRC / "shibuyananbu_link_2020.geojson"),
            "node": analyse_nodes(SRC / "shibuyananbu_node_2020.geojson"),
        },
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:12000])


if __name__ == "__main__":
    main()
