"""W4 建物・高さ(§1 W4・D-W5)。

規則: ``h = PLATEAU(IoU≥0.4) else (levels×h_floor if levels≠2) else kind既定``。
- PLATEAU の高さ = ``plateau_index.height - plateau_index.base``(= zmax−zmin。屋根頂部の
  標高ではなく建物そのものの高さ)を 0.1m に丸める(§0-1 の丸め規約)。
- ``h_floor = 3.0 m``(OSM Wiki Key:building:levels の既定・親実読)。
- OSM の ``levels`` は全 7,210 棟に入っており、うち 6,203 棟が既定値 2 = 実測ではない。
  よって「levels≠2 のときだけ levels を信じる」(D-W5)。

出力: ``w4_buildings.parquet``(building_id, h_m, src, levels, kind, area_m2, 重心, gml_id, iou)。

expedient
- kind→既定階数表(下表)。PLATEAU 実測との突合は notes の ``plateau_median_h_by_kind`` に
  出すだけで、表そのものは事前宣言のまま動かさない(較正はしていない)。
- levels 推定(levels×3.0)。
"""

from __future__ import annotations

import statistics
from collections import Counter
from typing import Any

import numpy as np
import pyarrow as pa

from . import common as C

STAGE = "W4"
STAGE_VERSION = "1.0.0"

INPUT_FILES: tuple[tuple[str, ...], ...] = (
    ("realworld", "osm", "shibuya_osm_wide_v8.json"),
    ("plateau", "plateau_index.json"),
    ("plateau", "plateau_match.json"),
    ("realworld", "osm", "building_heights_shibuya.json"),
)

#: 1階あたりの高さ [m](OSM Wiki の既定値)。
H_FLOOR_M = 3.0
#: IoU の下限(plateau_match.params.iou_min と同値)。
IOU_MIN = 0.4
#: kind → 既定階数(expedient・事前宣言)。表に無い kind は 2 階。
KIND_DEFAULT_FLOORS: dict[str, int] = {
    "house?": 2,
    "residential": 3,
    "generic": 3,
    "retail": 2,
    "office": 5,
    "public": 3,
    "hotel": 6,
    "station": 3,
}
KIND_DEFAULT_FALLBACK_FLOORS = 2


def kind_default_h(kind: str) -> float:
    """kind → 既定高さ [m](expedient)。"""
    floors = KIND_DEFAULT_FLOORS.get(kind, KIND_DEFAULT_FALLBACK_FLOORS)
    return round(floors * H_FLOOR_M, 1)


def height_of(
    kind: str, levels: int | None, plateau_h: float | None
) -> tuple[float, str]:
    """D-W5 の高さ規則。戻り値 = (h_m, src)。"""
    if plateau_h is not None:
        return round(float(plateau_h), 1), "plateau"
    if levels is not None and int(levels) != 2:
        return round(int(levels) * H_FLOOR_M, 1), "levels"
    return kind_default_h(kind), "kind_default"


def run(ctx: C.Ctx) -> C.StageResult:
    paths = [ctx.path(*parts) for parts in INPUT_FILES]
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"W4 入力が無い: {p}")
    osm = C.load_json(paths[0])
    index = C.load_json(paths[1])
    match = C.load_json(paths[2])
    v1_heights = C.load_json(paths[3])["heights"]

    by_gml = {b["gml_id"]: b for b in index["buildings"]}
    matches = match["matches"]

    bids: list[str] = []
    hs: list[float] = []
    srcs: list[str] = []
    levels_col: list[int | None] = []
    kinds: list[str] = []
    areas: list[float] = []
    cxs: list[float] = []
    cys: list[float] = []
    gmls: list[str | None] = []
    ious: list[float | None] = []
    names: list[str] = []
    n_below: list[int | None] = []

    plateau_h_by_kind: dict[str, list[float]] = {}
    for b in osm["buildings"]:
        bid = b["id"]
        kind = b["kind"]
        lv = b.get("levels")
        m = matches.get(bid)
        ph: float | None = None
        gml: str | None = None
        iou: float | None = None
        if m is not None and float(m["iou"]) >= IOU_MIN:
            pb = by_gml.get(m["gml_id"])
            if pb is not None:
                ph = float(pb["height"]) - float(pb["base"])
                gml = m["gml_id"]
                iou = float(m["iou"])
        h, src = height_of(kind, lv, ph)
        if src == "plateau":
            plateau_h_by_kind.setdefault(kind, []).append(h)
        bids.append(bid)
        hs.append(h)
        srcs.append(src)
        levels_col.append(int(lv) if lv is not None else None)
        kinds.append(kind)
        areas.append(float(b["area"]))
        cxs.append(float(b["cx"]))
        cys.append(float(b["cy"]))
        gmls.append(gml)
        ious.append(iou)
        names.append(b.get("name") or "")
        n_below.append(int(b["below"]) if b.get("below") is not None else None)

    src_counts = dict(sorted(Counter(srcs).items()))
    p_h = [h for h, s in zip(hs, srcs) if s == "plateau"]
    n_matched = len(p_h)
    med = round(statistics.median(p_h), 3) if p_h else None
    mx = max(p_h) if p_h else None

    agree = sum(
        1
        for bid, h, s in zip(bids, hs, srcs)
        if s == "plateau" and v1_heights.get(bid, {}).get("h") == h
    )

    params: dict[str, Any] = {
        "h_floor_m": H_FLOOR_M,
        "iou_min": IOU_MIN,
        "plateau_height_def": "plateau_index.height - plateau_index.base",
        "round_m": 0.1,
        "kind_default_floors": dict(sorted(KIND_DEFAULT_FLOORS.items())),
        "kind_default_fallback_floors": KIND_DEFAULT_FALLBACK_FLOORS,
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash(paths),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=["建物"],
        expedients=[
            "kind→既定階数表(事前宣言・PLATEAU で較正していない)",
            "levels×3.0 の高さ推定(levels≠2 のときのみ)",
        ],
        notes={
            "src_counts": src_counts,
            "kind_counts": dict(sorted(Counter(kinds).items())),
            "plateau_median_h_by_kind": {
                k: round(statistics.median(v), 1) for k, v in sorted(plateau_h_by_kind.items())
            },
            "plateau_n_by_kind": {k: len(v) for k, v in sorted(plateau_h_by_kind.items())},
            "h_median_all": round(statistics.median(hs), 3),
            "h_max_all": max(hs),
            "levels_ne_2": sum(1 for lv in levels_col if lv is not None and lv != 2),
            "cross_check_v1_building_heights_agree": agree,
        },
    )
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w4_buildings.parquet",
            {
                "building_id": bids,
                "h_m": np.array(hs),
                "src": srcs,
                "levels": pa.array(levels_col, type=pa.int16()),
                "kind": kinds,
                "area_m2": np.array(areas),
                "centroid_x": np.array(cxs),
                "centroid_y": np.array(cys),
                "gml_id": pa.array(gmls, type=pa.string()),
                "iou": pa.array(ious, type=pa.float64()),
                "name": names,
                "levels_below": pa.array(n_below, type=pa.int16()),
            },
        )
    )
    res.gates = [
        C.Gate("n_buildings", len(bids), 7210),
        C.Gate("plateau_matched", n_matched, 3531),
        C.Gate("plateau_h_median_m", med, 14.3),
        C.Gate("plateau_h_max_m", mx, 231.0),
        C.Gate("src_plateau", src_counts.get("plateau", 0), None),
        C.Gate("src_levels", src_counts.get("levels", 0), None),
        C.Gate("src_kind_default", src_counts.get("kind_default", 0), None),
        C.Gate("cross_check_v1_heights", agree, n_matched),
    ]
    return res
