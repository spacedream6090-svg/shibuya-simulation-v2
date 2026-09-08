"""W6 POI・組織の束縛(§1 W6・D-W7)。

- POI 2,337(OSM v8・``poi_patch_shibuya.json`` は v8 生成時に取り込み済み=版の証跡として
  input_hash にだけ含める)。
- 組織台帳は **census 版 9,872**(wide11k は廃止・D-W7)。census ファイルが各社に
  ``workplace_poi.building`` を持つので、その建物割当を**そのまま使う**(v1 の手続き生成規則を
  再実行しない=決定論と再現性のため)。配分則そのものは v1 由来の expedient。

出力: ``w6_poi.parquet`` / ``w6_org.parquet``。

expedient
- 組織の建物配分則(v1 手続き生成・census ファイルに凍結済み)。
- POI/組織のセル = 自身の座標の格子 × 束縛ノードのバンド。その place_id がセル表に無いときだけ
  ノードのセルへ落とす(件数を notes に出す)。
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
import pyarrow as pa

from . import common as C

STAGE = "W6"
STAGE_VERSION = "1.0.0"

INPUT_FILES: tuple[tuple[str, ...], ...] = (
    ("realworld", "osm", "shibuya_osm_wide_v8.json"),
    ("realworld", "osm", "poi_patch_shibuya.json"),
    ("realworld", "osm", "organizations_shibuya_census.json"),
)

EXPECTED_POI = 2337
EXPECTED_ORGS = 9872
EXPECTED_POI_BINDING_RATE = 0.688


def run(ctx: C.Ctx) -> C.StageResult:
    paths = [ctx.path(*parts) for parts in INPUT_FILES]
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"W6 入力が無い: {p}")
    nodes_p = ctx.out / "w1_nodes.parquet"
    cells_p = ctx.out / "w2_cells.parquet"
    bld_p = ctx.out / "w4_buildings.parquet"
    for p in (nodes_p, cells_p, bld_p):
        if not p.exists():
            raise FileNotFoundError(f"W6 は W1/W2/W4 の出力を必要とする: {p}")

    osm = C.load_json(paths[0])
    census = C.load_json(paths[2])
    nd = C.read_parquet_columns(nodes_p, ["node_id", "x", "y", "band"])
    cells = set(C.read_parquet_columns(cells_p, ["place_id"])["place_id"])
    known_buildings = set(C.read_parquet_columns(bld_p, ["building_id"])["building_id"])

    node_pos = {nid: (x, y, b) for nid, x, y, b in zip(nd["node_id"], nd["x"], nd["y"], nd["band"])}

    fallback = 0

    def cell_of(x: float, y: float, node_id: str | None) -> tuple[str, str]:
        nonlocal fallback
        band = "GL"
        if node_id is not None and node_id in node_pos:
            band = node_pos[node_id][2]
        pid = C.place_id(*C.grid_ij(x, y), band)
        if pid in cells:
            return pid, band
        if node_id is not None and node_id in node_pos:
            nxp, nyp, nb = node_pos[node_id]
            alt = C.place_id(*C.grid_ij(nxp, nyp), nb)
            if alt in cells:
                fallback += 1
                return alt, nb
        fallback += 1
        return pid, band

    # --- POI ---
    pois = osm["pois"]
    p_place: list[str] = []
    p_band: list[str] = []
    for p in pois:
        pid, band = cell_of(float(p["x"]), float(p["y"]), p.get("node"))
        p_place.append(pid)
        p_band.append(band)
    poi_fallback = fallback

    p_building = [p.get("building") or None for p in pois]
    n_bound = sum(1 for b in p_building if b)
    bind_rate = round(n_bound / len(pois), 3) if pois else 0.0
    poi_unknown_building = sum(1 for b in p_building if b and b not in known_buildings)

    poi_cols = {
        "poi_id": [p["id"] for p in pois],
        "name": [p.get("name") or "" for p in pois],
        "cat": [p["cat"] for p in pois],
        "subcat": pa.array([p.get("subcat") for p in pois], type=pa.string()),
        "floor": pa.array(
            [int(p["floor"]) if p.get("floor") is not None else None for p in pois], type=pa.int16()
        ),
        "building_id": pa.array(p_building, type=pa.string()),
        "node_id": [p["node"] for p in pois],
        "x": np.array([float(p["x"]) for p in pois]),
        "y": np.array([float(p["y"]) for p in pois]),
        "place_id": p_place,
        "band": p_band,
    }

    # --- 組織(census 版・companies 9,872)---
    fallback = 0
    companies = census["companies"]
    o_building: list[str | None] = []
    o_floor: list[int | None] = []
    o_node: list[str | None] = []
    o_x: list[float] = []
    o_y: list[float] = []
    o_place: list[str] = []
    o_band: list[str] = []
    for c in companies:
        wp = c.get("workplace_poi") or {}
        bid = wp.get("building")
        node = wp.get("node")
        x = float(wp.get("x", 0.0))
        y = float(wp.get("y", 0.0))
        pid, band = cell_of(x, y, node)
        o_building.append(bid)
        o_floor.append(int(wp["floor"]) if wp.get("floor") is not None else None)
        o_node.append(node)
        o_x.append(x)
        o_y.append(y)
        o_place.append(pid)
        o_band.append(band)
    org_fallback = fallback

    n_org_bound = sum(1 for b in o_building if b)
    distinct_buildings = len({b for b in o_building if b})
    org_unknown_building = sum(1 for b in o_building if b and b not in known_buildings)

    org_cols = {
        "org_id": [c["id"] for c in companies],
        "name": [c.get("name") or "" for c in companies],
        "industry": [c.get("industry") or "" for c in companies],
        "industry_key": [c.get("industry_key") or "" for c in companies],
        "sector_detail": [c.get("sector_detail") or "" for c in companies],
        "employees": np.array(
            [int((c.get("size") or {}).get("employees", 0)) for c in companies], dtype=np.int32
        ),
        "size_band": [(c.get("size") or {}).get("band", "") for c in companies],
        "wage_tier": [c.get("wage_tier") or "" for c in companies],
        "building_id": pa.array(o_building, type=pa.string()),
        "floor": pa.array(o_floor, type=pa.int16()),
        "node_id": pa.array(o_node, type=pa.string()),
        "x": np.array(o_x),
        "y": np.array(o_y),
        "place_id": o_place,
        "band": o_band,
    }

    params: dict[str, Any] = {
        "org_ledger": "organizations_shibuya_census.json (companies)",
        "org_building_assignment": "census file's own workplace_poi.building",
        "poi_source": "shibuya_osm_wide_v8.json pois (poi_patch already merged upstream)",
        "cell_rule": "grid(self xy) x band(bound node); fallback = cell of bound node",
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash([*paths, nodes_p, cells_p, bld_p]),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=["POI/店舗", "事業所(組織)", "建物内フロア・区画"],
        expedients=[
            "組織の建物配分則(v1 手続き生成・census ファイルに凍結済み)",
            "POI/組織のセル決定(自身の格子×束縛ノードのバンド・欠けたらノードのセル)",
        ],
        notes={
            "poi_cat_counts": dict(sorted(Counter(p["cat"] for p in pois).items())),
            "poi_subcat_counts": dict(
                sorted(Counter(p["subcat"] for p in pois if p.get("subcat")).items())
            ),
            "poi_with_building": n_bound,
            "poi_cell_fallback": poi_fallback,
            "poi_building_id_not_in_w4": poi_unknown_building,
            "org_cell_fallback": org_fallback,
            "org_building_id_not_in_w4": org_unknown_building,
            "org_industry_counts": dict(
                sorted(Counter(c.get("industry_key") or "" for c in companies).items())
            ),
            "schools_in_census_file_not_in_org_table": len(census.get("schools", [])),
            "org_employees_total": int(org_cols["employees"].sum()),
        },
    )
    res.outputs.append(C.write_parquet(ctx.out, "w6_poi.parquet", poi_cols))
    res.outputs.append(C.write_parquet(ctx.out, "w6_org.parquet", org_cols))
    res.gates = [
        C.Gate("poi_total", len(pois), EXPECTED_POI),
        C.Gate("poi_building_binding_rate", bind_rate, EXPECTED_POI_BINDING_RATE),
        C.Gate("orgs_total", len(companies), EXPECTED_ORGS),
        C.Gate("orgs_bound_to_building", n_org_bound, EXPECTED_ORGS),
        C.Gate("org_distinct_buildings", distinct_buildings, None),
        C.Gate("poi_cells_all_known", all(p in cells for p in p_place), True),
        C.Gate("org_cells_all_known", all(p in cells for p in o_place), True),
    ]
    return res
