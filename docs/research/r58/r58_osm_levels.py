"""R-58: 手元の OSM(Overpass 生データ 4 本+加工済み v8)の 3 次元タグを数える(読むだけ)。

入力: data/realworld/osm/{poi_tags_overpass_20260928, poi_opening_hours_overpass_20260907,
       street_features_overpass_20260907, road_names_overpass_20260928, station_entrances_overpass,
       shibuya_osm_wide_v8}.json
出力: docs/research/r58/r58_osm_levels.json(集計値のみ・OSM の生値=名前などは載せない)
全ファイルの取得範囲は W1 bbox(35.6505,139.6905,35.6685,139.7115)と同一。
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OSM = REPO / "data" / "realworld" / "osm"
OUT = Path(__file__).with_name("r58_osm_levels.json")
ORIGIN = (35.6595, 139.70062)
M_LAT = 111132.9
M_LON = 111320.0 * math.cos(math.radians(ORIGIN[0]))
KEYS = ["level", "level:ref", "addr:floor", "repeat_on", "indoor", "highway", "conveying", "tunnel",
        "bridge", "layer", "covered", "location", "min_level", "max_level", "building:levels", "building:levels:underground"]


def dist_band(lat: float, lon: float) -> str:
    d = math.hypot((lon - ORIGIN[1]) * M_LON, (lat - ORIGIN[0]) * M_LAT)
    return "<300m" if d < 300 else "300-700m" if d < 700 else ">=700m"


def raw(name: str) -> dict:
    d = json.loads((OSM / f"{name}.json").read_text(encoding="utf-8"))
    els = d.get("elements", [])
    key_counts = Counter()
    for e in els:
        for k in (e.get("tags") or {}):
            if k in KEYS:
                key_counts[k] += 1
    level_vals = Counter()
    level_band = Counter()
    for e in els:
        t = e.get("tags") or {}
        if "level" in t:
            level_vals[t["level"]] += 1
            lat = e.get("lat", (e.get("center") or {}).get("lat"))
            lon = e.get("lon", (e.get("center") or {}).get("lon"))
            if lat is not None:
                level_band[dist_band(lat, lon)] += 1
    all_band = Counter()
    for e in els:
        lat = e.get("lat", (e.get("center") or {}).get("lat"))
        lon = e.get("lon", (e.get("center") or {}).get("lon"))
        if lat is not None:
            all_band[dist_band(lat, lon)] += 1
    hw = Counter((e.get("tags") or {}).get("highway") for e in els if "highway" in (e.get("tags") or {}))
    return {
        "n_elements": len(els),
        "types": dict(Counter(e.get("type") for e in els)),
        "osm_base": (d.get("osm3s") or {}).get("timestamp_osm_base"),
        "tag_counts": dict(key_counts.most_common()),
        "level_values_top": dict(level_vals.most_common(20)),
        "level_nonzero": sum(v for k, v in level_vals.items() if k not in ("0",)),
        "level_by_distance_from_origin": dict(level_band),
        "all_by_distance_from_origin": dict(all_band),
        "highway_values": dict(hw.most_common(20)),
    }


def v8() -> dict:
    d = json.loads((OSM / "shibuya_osm_wide_v8.json").read_text(encoding="utf-8"))
    kl = Counter()
    ln = Counter()
    lay = Counter()
    for e in d["edges"]:
        kl[e["klass"]] += 1
        ln[e["klass"]] += e["length"]
        lay[str(e.get("layer"))] += e["length"]
    b = d["buildings"]
    lv = Counter(bb["levels"] for bb in b)
    return {
        "edges": len(d["edges"]),
        "edge_keys": sorted({k for e in d["edges"] for k in e}),
        "klass_count": dict(kl.most_common()),
        "klass_len_m": {k: round(v) for k, v in ln.most_common()},
        "layer_len_m": {k: round(v) for k, v in lay.most_common()},
        "buildings": len(b),
        "buildings_with_below": sum(1 for bb in b if "below" in bb),
        "building_levels_top": {str(k): v for k, v in lv.most_common(12)},
        "pois": len(d["pois"]),
        "pois_with_floor_field": sum(1 for p in d["pois"] if "floor" in p),
        "poi_floor_values": dict(Counter(str(p.get("floor")) for p in d["pois"] if "floor" in p).most_common(15)),
    }


def main() -> None:
    out = {n: raw(n) for n in ("poi_tags_overpass_20260928", "poi_opening_hours_overpass_20260907",
                                "street_features_overpass_20260907", "road_names_overpass_20260928",
                                "station_entrances_overpass")}
    out["shibuya_osm_wide_v8"] = v8()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
