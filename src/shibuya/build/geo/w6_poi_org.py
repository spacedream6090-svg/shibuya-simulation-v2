"""W6 POI・組織の束縛(§1 W6・D-W7)。

- POI 2,337(OSM v8・``poi_patch_shibuya.json`` は v8 生成時に取り込み済み=版の証跡として
  input_hash にだけ含める)。
- 組織台帳は **census 版 9,872**(wide11k は廃止・D-W7)。census ファイルが各社に
  ``workplace_poi.building`` を持つので、その建物割当を**そのまま使う**(v1 の手続き生成規則を
  再実行しない=決定論と再現性のため)。配分則そのものは v1 由来の expedient。
- **subcat は生タグから引き直す**(2026-09-17 改訂・:mod:`.poi_class`)。v8 の ``pois`` は
  生タグを落としているので、リポに残る Overpass の 2 文書(``poi_opening_hours_…`` /
  ``street_features_…``)で ``poi_id`` を突き合わせ、当たった POI は **OSM タグを一次根拠**に
  subcat を決める。当たらない POI は v8 の subcat、それも無ければ名前一致(expedient)。
  **cat は 1 件も動かさない**。

出力: ``w6_poi.parquet`` / ``w6_org.parquet``。

expedient
- 組織の建物配分則(v1 手続き生成・census ファイルに凍結済み)。
- POI/組織のセル = 自身の座標の格子 × 束縛ノードのバンド。その place_id がセル表に無いときだけ
  ノードのセルへ落とす(件数を notes に出す)。
- subcat の名前一致層(:data:`.poi_class.NAME_SUBCAT_RULES`)。生タグがどの文書にも無い
  POI にだけ掛かる。切替口 = :data:`USE_NAME_SUBCAT_RULES`。
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
import pyarrow as pa

from . import common as C
from . import poi_class as PC

STAGE = "W6"
STAGE_VERSION = "1.1.0"

INPUT_FILES: tuple[tuple[str, ...], ...] = (
    ("realworld", "osm", "shibuya_osm_wide_v8.json"),
    ("realworld", "osm", "poi_patch_shibuya.json"),
    ("realworld", "osm", "organizations_shibuya_census.json"),
    # subcat の一次根拠(OSM 生タグ)。v8 の pois には生タグが残っていない。
    ("realworld", "osm", "poi_opening_hours_overpass_20260907.json"),
    ("realworld", "osm", "street_features_overpass_20260907.json"),
)

#: 切替口(expedient の名前一致層)。False にすると subcat は生タグと v8 の値だけで決まる。
USE_NAME_SUBCAT_RULES: bool = True

EXPECTED_POI = 2337
EXPECTED_ORGS = 9872
EXPECTED_POI_BINDING_RATE = 0.688
#: 生タグで決めた subcat が v8 の subcat と食い違った件数(=0 でなければ規則の移植が壊れている)。
EXPECTED_SUBCAT_TAG_VS_FROZEN_MISMATCH = 0
#: 生タグの subcat が cat と矛盾して捨てられた件数(対の閉包を守る不変条件)。
EXPECTED_SUBCAT_TOPCAT_CONFLICT = 0
#: ``PLACE_PARK``(場所語「公園」)へ写る POI。改訂前は **0 件**(語彙の孤児)だった。
EXPECTED_SUBCAT_PARK = 27


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
    tags_by_poi = PC.tag_index(C.load_json(paths[3]), C.load_json(paths[4]))
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

    # --- subcat を引き直す(一次=OSM 生タグ・控え=v8 の値・最後の手段=名前) ---
    p_subcat: list[str | None] = []
    subcat_source = Counter()
    tag_vs_frozen_mismatch = 0
    topcat_conflict = 0
    for p in pois:
        cat = str(p["cat"])
        frozen = p.get("subcat")
        tags = tags_by_poi.get(str(p["id"]))
        if tags:
            raw = PC.poi_subcategory(tags)
            if raw is not None:
                if PC.SUBCAT_TOPCAT[raw] != cat:
                    topcat_conflict += 1
                elif frozen and str(frozen) != raw:
                    tag_vs_frozen_mismatch += 1
        sub, source = PC.resolve_subcat(
            cat,
            str(p.get("name") or ""),
            frozen,
            tags,
            use_name_rules=USE_NAME_SUBCAT_RULES,
        )
        p_subcat.append(sub)
        subcat_source[source] += 1
    catsub_pairs = Counter((str(p["cat"]), s or "") for p, s in zip(pois, p_subcat))
    subcat_counts_park = sum(1 for s in p_subcat if s == "park")

    poi_cols = {
        "poi_id": [p["id"] for p in pois],
        "name": [p.get("name") or "" for p in pois],
        "cat": [p["cat"] for p in pois],
        "subcat": pa.array(p_subcat, type=pa.string()),
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
        "subcat_rule": "osm raw tags (primary) > v8 frozen subcat > POI name (expedient)",
        "subcat_name_rules": bool(USE_NAME_SUBCAT_RULES),
        "subcat_vocab": sorted(PC.SUBCAT_TOPCAT),
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
            "subcat の名前一致層(poi_class.NAME_SUBCAT_RULES・生タグが無い POI のみ)",
        ],
        notes={
            "poi_cat_counts": dict(sorted(Counter(p["cat"] for p in pois).items())),
            "poi_subcat_counts": dict(sorted(Counter(s for s in p_subcat if s).items())),
            "poi_subcat_frozen_counts": dict(
                sorted(Counter(p["subcat"] for p in pois if p.get("subcat")).items())
            ),
            "poi_subcat_source_counts": dict(sorted(subcat_source.items())),
            "poi_catsub_pairs": {f"{c}|{s}": n for (c, s), n in sorted(catsub_pairs.items())},
            "poi_raw_tags_matched": sum(1 for p in pois if str(p["id"]) in tags_by_poi),
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
        # subcat の引き直し(2026-09-17 改訂)
        C.Gate(
            "poi_subcat_tag_vs_frozen_mismatch",
            tag_vs_frozen_mismatch,
            EXPECTED_SUBCAT_TAG_VS_FROZEN_MISMATCH,
        ),
        C.Gate("poi_subcat_topcat_conflict", topcat_conflict, EXPECTED_SUBCAT_TOPCAT_CONFLICT),
        C.Gate("poi_subcat_park", subcat_counts_park, EXPECTED_SUBCAT_PARK),
        C.Gate("poi_subcat_total", sum(1 for s in p_subcat if s), None),
        C.Gate("poi_subcat_from_name", subcat_source["name"], None),
        C.Gate(
            "poi_catsub_pairs_in_closure",
            all(
                (c, s) in set(PC.CATSUB_PAIRS) for (c, s) in catsub_pairs if s
            ),
            True,
        ),
    ]
    return res
