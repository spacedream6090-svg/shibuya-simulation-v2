"""build.space.sources — 段 1 のナビメッシュの材料を読む(手元のファイルだけ・ネットワークは使わない)。

材料(R-119 §1 A・B と段 0 の記録 ``docs/bench/analysis/spatial-2026-10/sp0/README.md``):

- PLATEAU 渋谷区 2025 の CityGML(``data/realworld/plateau_2025/13113_shibuya-ku_pref_2025_citygml_1_op/udx``):
  道路 ``tran``(``tran:Road`` の LOD1 の面・``tran:TrafficArea`` と ``tran:AuxiliaryTrafficArea`` の LOD2/3 の面)・
  都市設備 ``frn``(横断歩道 1110・地下出入口 4020)・地形 ``dem``(TIN)。座標は (緯度 経度 高さ)。
- 解析済みの PLATEAU(``data/plateau/``): 地下街 LOD4.1 の三角形 ``ubld_lod4_mesh.npz``(床の三角形・層の高さは
  ``ubld_lod4.json`` の ``layers``)・橋梁 LOD2 の三角形 ``extras.npz``(``brid_V``/``brid_F``/``brid_off``)。高さは
  ``ground0`` 15.18 m からの差 → 足して標高にする。
- OSM の歩行系 ``data/spatial/osm_walk/osm_walk_raw.json``(段 0 で取得・読むだけ)。
- 歩行空間ネットワーク 2020(``data/research_cache/r58/shibuyananbu_*_2020.geojson``)。
- W1(``w1_nodes``・``w1_edges``・``w1_edge_geometry.npz``)と W2(``w2_cells``)。

逐次ループ宣言(P4): 構築の 1 回だけ。地物の数・三角形の数ぶんの Python のループ(XML と JSON の読み)。
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import numpy as np

from shibuya.build.geo.common import GROUND0_M, M_PER_DEG_LAT, M_PER_DEG_LON, ORIGIN_LATLON

__all__ = [
    "PLATEAU_UDX_RELPATH",
    "Road",
    "read_tran_roads",
    "read_frn",
    "read_dem_triangles",
    "read_ubld_floor_triangles",
    "read_brid_triangles",
    "read_osm_walk",
    "read_hokoukukan_2020",
    "to_local",
]

#: PLATEAU の udx の置き場(データの根からの道筋)。
PLATEAU_UDX_RELPATH = "realworld/plateau_2025/13113_shibuya-ku_pref_2025_citygml_1_op/udx"

NS_TRAN = "{http://www.opengis.net/citygml/transportation/2.0}"
NS_GML = "{http://www.opengis.net/gml}"
NS_CORE = "{http://www.opengis.net/citygml/2.0}"
NS_URO = "{https://www.geospatial.jp/iur/uro/3.2}"
NS_FRN = "{http://www.opengis.net/citygml/cityfurniture/2.0}"


def to_local(lat: np.ndarray, lon: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """緯度経度 → 世界の平面座標 [m](W0 の CRS と同じ式)。"""
    x = (np.asarray(lon, dtype=np.float64) - ORIGIN_LATLON[1]) * M_PER_DEG_LON
    y = (np.asarray(lat, dtype=np.float64) - ORIGIN_LATLON[0]) * M_PER_DEG_LAT
    return x, y


def _poslist_xy(text: str) -> np.ndarray:
    v = np.array(text.split(), dtype=np.float64)
    if v.size < 9 or v.size % 3:
        return np.zeros((0, 3))
    v = v.reshape(-1, 3)
    x, y = to_local(v[:, 0], v[:, 1])
    return np.stack([x, y, v[:, 2]], axis=1)


def _rings_of(ms: ET.Element) -> list[tuple[np.ndarray, int]]:
    """MultiSurface の中の多角形 → (環 (n,3)=(x, y, 高さ), 符号 +1 外周 / -1 穴) の並び。"""
    out: list[tuple[np.ndarray, int]] = []
    for poly in ms.iter(f"{NS_GML}Polygon"):
        for kind, sign in (("exterior", 1), ("interior", -1)):
            for boundary in poly.findall(f"{NS_GML}{kind}"):
                for ring in boundary.iter(f"{NS_GML}LinearRing"):
                    pos = ring.find(f"{NS_GML}posList")
                    if pos is None or not pos.text:
                        continue
                    xy = _poslist_xy(pos.text)
                    if xy.shape[0] >= 3:
                        out.append((xy, sign))
    return out


@dataclass
class Road:
    """``tran:Road`` 1 つ(LOD1 の面と、子の交通領域の LOD2/3 の面)。"""

    gid: str
    function: int
    section: int
    lod1: list[tuple[np.ndarray, int]] = field(default_factory=list)
    #: (機能コード, LOD, 環の並び)
    areas: list[tuple[int, int, list[tuple[np.ndarray, int]]]] = field(default_factory=list)

    @property
    def detailed(self) -> bool:
        return bool(self.areas)

    @property
    def has_sidewalk(self) -> bool:
        return any(code in (2000, 2010, 2020) for code, _lod, _r in self.areas)


def _ring_bbox_hits(rings: list[tuple[np.ndarray, int]], bbox: tuple[float, float, float, float]) -> bool:
    x0, y0, x1, y1 = bbox
    for r, _s in rings:
        if r[:, 0].max() >= x0 and r[:, 0].min() <= x1 and r[:, 1].max() >= y0 and r[:, 1].min() <= y1:
            return True
    return False


def read_tran_roads(udx: Path, bbox: tuple[float, float, float, float]) -> tuple[list[Road], dict[str, Any]]:
    """``udx/tran/*.gml`` → 範囲 ``bbox`` に掛かる ``tran:Road`` の並び(ファイル名の順・ファイルの中の順=決定論)。"""
    roads: list[Road] = []
    n_seen = 0
    files = sorted((udx / "tran").glob("*.gml"))
    for path in files:
        for _ev, el in ET.iterparse(str(path), events=("end",)):
            if el.tag != f"{NS_CORE}cityObjectMember":
                continue
            rd = el.find(f"{NS_TRAN}Road")
            if rd is None:
                el.clear()
                continue
            n_seen += 1
            fn = rd.find(f"{NS_TRAN}function")
            st = None
            for s in rd.iter(f"{NS_URO}sectionType"):
                st = s
                break
            road = Road(
                gid=str(rd.get(f"{NS_GML}id") or ""),
                function=int(fn.text.strip()) if fn is not None and fn.text else -1,
                section=int(st.text.strip()) if st is not None and st.text else -1,
            )
            ms1 = rd.find(f"{NS_TRAN}lod1MultiSurface")
            if ms1 is not None:
                road.lod1 = _rings_of(ms1)
            for tag in ("trafficArea", "auxiliaryTrafficArea"):
                for holder in rd.findall(f"{NS_TRAN}{tag}"):
                    for ta in holder:
                        fcode = ta.find(f"{NS_TRAN}function")
                        if fcode is None or not fcode.text:
                            continue
                        code = int(fcode.text.strip())
                        for lod in (3, 2):
                            ms = ta.find(f"{NS_TRAN}lod{lod}MultiSurface")
                            if ms is None:
                                continue
                            rings = _rings_of(ms)
                            if rings:
                                road.areas.append((code, lod, rings))
                            break
            el.clear()
            if _ring_bbox_hits(road.lod1, bbox) or any(_ring_bbox_hits(r, bbox) for _c, _l, r in road.areas):
                roads.append(road)
    stats = {"n_files": len(files), "n_roads_in_files": n_seen, "n_roads_in_bbox": len(roads),
             "n_detailed": sum(1 for r in roads if r.detailed),
             "n_lod1_only": sum(1 for r in roads if not r.detailed and r.lod1)}
    return roads, stats


def read_frn(udx: Path, bbox: tuple[float, float, float, float]) -> tuple[list[np.ndarray], list[np.ndarray], dict]:
    """``udx/frn/*.gml`` → (横断歩道 1110 の頂点 (n,3) の並び, 地下出入口 4020 の頂点 (n,3) の並び, 統計)。"""
    crossings: list[np.ndarray] = []
    entrances: list[np.ndarray] = []
    files = sorted((udx / "frn").glob("*.gml"))
    for path in files:
        for _ev, el in ET.iterparse(str(path), events=("end",)):
            if el.tag != f"{NS_CORE}cityObjectMember":
                continue
            cf = el.find(f"{NS_FRN}CityFurniture")
            if cf is None:
                el.clear()
                continue
            fn = cf.find(f"{NS_FRN}function")
            code = int(fn.text.strip()) if fn is not None and fn.text else -1
            if code in (1110, 4020):
                pts = []
                for pos in cf.iter(f"{NS_GML}posList"):
                    if pos.text:
                        xy = _poslist_xy(pos.text)
                        if xy.shape[0]:
                            pts.append(xy)
                if pts:
                    v = np.concatenate(pts)
                    x0, y0, x1, y1 = bbox
                    c = v[:, :2].mean(axis=0)
                    if x0 <= c[0] <= x1 and y0 <= c[1] <= y1:
                        (crossings if code == 1110 else entrances).append(v)
            el.clear()
    return crossings, entrances, {"n_files": len(files), "n_crossing": len(crossings), "n_entrance": len(entrances)}


_POS_RE = re.compile(rb"<gml:posList>([^<]*)</gml:posList>")


def read_dem_triangles(udx: Path, bbox: tuple[float, float, float, float]) -> tuple[np.ndarray, dict]:
    """``udx/dem/*.gml`` の TIN の三角形 → (n, 3, 3) の (x, y, 標高)。``bbox`` に頂点の掛かるものだけ(先頭の点で粗く絞る)。"""
    x0, y0, x1, y1 = bbox
    lat0 = ORIGIN_LATLON[0] + y0 / M_PER_DEG_LAT
    lat1 = ORIGIN_LATLON[0] + y1 / M_PER_DEG_LAT
    lon0 = ORIGIN_LATLON[1] + x0 / M_PER_DEG_LON
    lon1 = ORIGIN_LATLON[1] + x1 / M_PER_DEG_LON
    pad_lat = 30.0 / M_PER_DEG_LAT
    pad_lon = 30.0 / M_PER_DEG_LON
    out: list[np.ndarray] = []
    n_all = 0
    files = sorted((udx / "dem").glob("*.gml"))
    for path in files:
        data = path.read_bytes()
        for m in _POS_RE.finditer(data):
            n_all += 1
            s = m.group(1)
            sp = s.split(None, 2)
            if len(sp) < 2:
                continue
            la = float(sp[0])
            lo = float(sp[1])
            if la < lat0 - pad_lat or la > lat1 + pad_lat or lo < lon0 - pad_lon or lo > lon1 + pad_lon:
                continue
            v = np.array(s.split(), dtype=np.float64)
            if v.size < 9:
                continue
            v = v[:9].reshape(3, 3)
            out.append(v)
        del data
    if not out:
        return np.zeros((0, 3, 3)), {"n_files": len(files), "n_triangles_in_files": n_all, "n_triangles": 0}
    a = np.stack(out)
    x, y = to_local(a[:, :, 0], a[:, :, 1])
    tri = np.stack([x, y, a[:, :, 2]], axis=2)
    return tri, {"n_files": len(files), "n_triangles_in_files": n_all, "n_triangles": int(tri.shape[0])}


def read_ubld_floor_triangles(plateau_dir: Path) -> tuple[np.ndarray, np.ndarray, dict]:
    """地下街 LOD4.1 の床の三角形 → ((n, 3, 3) の (x, y, 標高), 層の高さ[m 標高] の配列, 統計)。"""
    meta = json.loads((plateau_dir / "ubld_lod4.json").read_text(encoding="utf-8"))
    z = np.load(plateau_dir / "ubld_lod4_mesh.npz")
    xyz = (z["xyz"].astype(np.float64) + z["origin_q"].astype(np.float64)) * float(meta["params"]["quant_scale"])
    tri = z["tri"].astype(np.int64)
    kinds = [str(k) for k in z["kind_names"]]
    kfloor = kinds.index("floor")
    sel = z["tri_kind"] == kfloor
    t = xyz[tri[sel]]
    g0 = float(meta.get("ground0", GROUND0_M))
    t = t.copy()
    t[:, :, 2] += g0
    layers = np.asarray([float(l["z"]) + g0 for l in meta["layers"]], dtype=np.float64)
    return t, layers, {"n_floor_triangles": int(t.shape[0]), "layers_z_m": layers.round(3).tolist(),
                       "source_file": str(meta.get("source", {}).get("file", ""))}


def read_brid_triangles(plateau_dir: Path) -> tuple[list[np.ndarray], dict]:
    """橋梁 LOD2 の構造ごとの三角形 → [(n, 3, 3) の (x, y, 標高)] の並び。"""
    meta = json.loads((plateau_dir / "extras.json").read_text(encoding="utf-8"))
    z = np.load(plateau_dir / "extras.npz")
    V = z["brid_V"].astype(np.float64)
    F = z["brid_F"].astype(np.int64)
    off = z["brid_off"].astype(np.int64)
    g0 = float(meta.get("ground0", GROUND0_M))
    out = []
    for i in range(off.size - 1):
        t = V[F[off[i]:off[i + 1]]].copy()
        t[:, :, 2] += g0
        out.append(t)
    return out, {"n_structures": len(out)}


def read_osm_walk(path: Path) -> tuple[list[dict], list[dict]]:
    """OSM の歩行系の生データ → (線の並び, 点の並び)。線=dict(id, tags, xy (n,2))・点=dict(id, tags, x, y)。id の順。"""
    d = json.loads(path.read_text(encoding="utf-8"))
    ways, nodes = [], []
    for e in d.get("elements", []):
        if e.get("type") == "way" and e.get("geometry"):
            g = e["geometry"]
            lat = np.asarray([p["lat"] for p in g], dtype=np.float64)
            lon = np.asarray([p["lon"] for p in g], dtype=np.float64)
            x, y = to_local(lat, lon)
            ways.append({"id": int(e["id"]), "tags": dict(e.get("tags", {})), "xy": np.stack([x, y], axis=1)})
        elif e.get("type") == "node" and "lat" in e:
            x, y = to_local(np.asarray([e["lat"]]), np.asarray([e["lon"]]))
            nodes.append({"id": int(e["id"]), "tags": dict(e.get("tags", {})), "x": float(x[0]), "y": float(y[0])})
    ways.sort(key=lambda w: w["id"])
    nodes.sort(key=lambda n: n["id"])
    return ways, nodes


def read_hokoukukan_2020(r58_dir: Path) -> tuple[list[dict], dict[str, dict]]:
    """歩行空間ネットワーク 2020 → (リンクの並び=dict(props, xy), ノード id → dict(floor, x, y))。"""
    links = json.loads((r58_dir / "shibuyananbu_link_2020.geojson").read_text(encoding="utf-8"))["features"]
    nodes = json.loads((r58_dir / "shibuyananbu_node_2020.geojson").read_text(encoding="utf-8"))["features"]
    nd: dict[str, dict] = {}
    for f in nodes:
        p = f["properties"]
        x, y = to_local(np.asarray([p["lat"]]), np.asarray([p["lon"]]))
        nd[str(p["node_id"])] = {"floor": float(p.get("floor") or 0.0), "x": float(x[0]), "y": float(y[0])}
    out = []
    for f in links:
        g = f.get("geometry") or {}
        if g.get("type") != "LineString":
            continue
        c = np.asarray(g["coordinates"], dtype=np.float64)
        x, y = to_local(c[:, 1], c[:, 0])
        out.append({"props": dict(f["properties"]), "xy": np.stack([x, y], axis=1)})
    return out, nd


def iter_w1_edges(world_dir: Path) -> Iterator[dict]:
    """W1 の辺(番号の順)=dict(edge, u, v, klass, band_u, band_v, layer, xy (n,2))。"""
    import pyarrow.parquet as pq

    e = pq.read_table(world_dir / "w1_edges.parquet").to_pydict()
    g = np.load(world_dir / "w1_edge_geometry.npz")
    coords = g["coords"]
    for i in range(len(e["edge_idx"])):
        s = int(e["geom_start"][i])
        n = int(e["geom_count"][i])
        yield {"edge": int(e["edge_idx"][i]), "u": int(e["u_idx"][i]), "v": int(e["v_idx"][i]),
               "klass": str(e["klass"][i]), "band_u": str(e["band_u"][i]), "band_v": str(e["band_v"][i]),
               "layer": int(e["layer"][i]) if e["layer"][i] is not None else 0,
               "length_m": float(e["length_m"][i]), "xy": np.asarray(coords[s:s + n], dtype=np.float64)}
