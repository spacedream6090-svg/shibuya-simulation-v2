"""R-101: OSM の学校(amenity=school/university/college)を、世界の 453 セル(GL)の中か周辺かに分けて一覧にする。

読むだけ。入力:
  data/research_cache/r101/schools_overpass_20261006.json (Overpass・2026-10-06 取得)
  data/world/v2/w2_cells.parquet (GL セル。ix=floor(x/100), iy=floor(y/100))
  data/world/v2/world_crs.json (原点と m/度)
出力: 標準出力に TSV(答申の表の材料)。
"""
import json
import math
import sys
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[4]
crs = json.loads((ROOT / "data/world/v2/world_crs.json").read_text(encoding="utf-8"))
lat0, lon0 = crs["origin_latlon"]
mlat, mlon = crs["m_per_deg_lat"], crs["m_per_deg_lon"]
cells = {(r["ix"], r["iy"]) for r in pq.read_table(ROOT / "data/world/v2/w2_cells.parquet").to_pylist() if r["band"] == "GL"}

src = json.loads((ROOT / "data/research_cache/r101/schools_overpass_20261006.json").read_text(encoding="utf-8"))


def dist_to_range(x, y):
    """範囲(GL セルの和集合)の縁までの距離(m)。中なら 0。"""
    ix, iy = math.floor(x / 100), math.floor(y / 100)
    if (ix, iy) in cells:
        return 0.0
    best = 1e9
    for cx, cy in cells:
        dx = max(cx * 100 - x, 0, x - (cx + 1) * 100)
        dy = max(cy * 100 - y, 0, y - (cy + 1) * 100)
        best = min(best, math.hypot(dx, dy))
    return best


rows = []
for e in src["elements"]:
    t = e.get("tags", {})
    lat = e.get("lat", e.get("center", {}).get("lat"))
    lon = e.get("lon", e.get("center", {}).get("lon"))
    if lat is None:
        continue
    x, y = (lon - lon0) * mlon, (lat - lat0) * mlat
    d = dist_to_range(x, y)
    rows.append((round(d), t.get("amenity"), t.get("name", ""), t.get("operator", ""), t.get("operator:type", ""),
                 t.get("isced:level", ""), t.get("website", t.get("contact:website", "")),
                 f"{e['type'][0]}{e['id']}", round(lat, 5), round(lon, 5)))

rows.sort(key=lambda r: (r[0] > 0, r[0], r[1], r[2]))
out = sys.stdout
out.reconfigure(encoding="utf-8")
print("dist_m\tamenity\tname\toperator\toperator_type\tisced\twebsite\tosm\tlat\tlon", file=out)
for r in rows:
    print("\t".join(str(v) for v in r), file=out)
print(f"# total={len(rows)} in_range={sum(1 for r in rows if r[0] == 0)} "
      f"le800={sum(1 for r in rows if 0 < r[0] <= 800)} gt800={sum(1 for r in rows if r[0] > 800)}", file=out)
