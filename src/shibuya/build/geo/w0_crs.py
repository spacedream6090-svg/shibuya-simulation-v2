"""W0 原点・座標系凍結(§1 W0)。

出力: ``world_crs.json``(原点・ground0・m/度の換算定数・格子・層バンド表)。
ゲート: PLATEAU / OSM / terrain の各ファイルが持つ origin・ground0 が一致すること。

**どのファイルが何を持つか**(親検収で確認・実データ由来):

===================================== ============ =========
ファイル                               origin_latlon ground0
===================================== ============ =========
realworld/osm/shibuya_osm_wide_v8.json  meta にあり   なし
plateau/plateau_index.json              params にあり あり
plateau/terrain.json                    なし          あり
plateau/extras.json                     なし          あり
plateau/tran_lod3.json                  あり          あり
===================================== ============ =========

origin を持たないファイル(terrain.json・extras.json)は ground0 のみで照合する。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import common as C

STAGE = "W0"
STAGE_VERSION = "1.0.0"

#: 入力(input_hash の固定順)。
INPUT_FILES: tuple[tuple[str, ...], ...] = (
    ("realworld", "osm", "shibuya_osm_wide_v8.json"),
    ("plateau", "plateau_index.json"),
    ("plateau", "terrain.json"),
    ("plateau", "extras.json"),
    ("plateau", "tran_lod3.json"),
)


def _probe(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """1ファイルから origin_latlon / ground0 を取り出す(無ければ None)。"""
    origin = payload.get("origin_latlon")
    if origin is None:
        meta = payload.get("meta")
        if isinstance(meta, dict):
            origin = meta.get("origin_latlon")
    if origin is None:
        params = payload.get("params")
        if isinstance(params, dict):
            origin = params.get("origin_latlon")
    ground0 = payload.get("ground0")
    if ground0 is None:
        meta = payload.get("meta")
        if isinstance(meta, dict):
            ground0 = meta.get("ground0")
    return {
        "file": name,
        "origin_latlon": list(origin) if origin is not None else None,
        "ground0": float(ground0) if ground0 is not None else None,
    }


def run(ctx: C.Ctx) -> C.StageResult:
    paths = [ctx.path(*parts) for parts in INPUT_FILES]
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"W0 入力が無い: {p}")

    probes = [_probe(p.name, C.load_json(p)) for p in paths]
    origins = [tuple(pr["origin_latlon"]) for pr in probes if pr["origin_latlon"] is not None]
    grounds = [pr["ground0"] for pr in probes if pr["ground0"] is not None]

    params: dict[str, Any] = {
        "origin_latlon": list(C.ORIGIN_LATLON),
        "ground0_m": C.GROUND0_M,
        "cell_m": C.CELL_M,
        "band_of_layer": {str(k): v for k, v in C.BAND_OF_LAYER.items()},
    }

    crs = {
        "crs": "local-m",
        "axes": "X=east,Y=north,Z=up",
        "origin_latlon": list(C.ORIGIN_LATLON),
        "ground0_m": C.GROUND0_M,
        "m_per_deg_lat": C.M_PER_DEG_LAT,
        "m_per_deg_lon": C.M_PER_DEG_LON,
        "m_per_deg_lon_formula": "111320 * cos(radians(origin_lat))",
        "cell_m": C.CELL_M,
        "bands": list(C.BANDS),
        "band_of_layer": {str(k): v for k, v in C.BAND_OF_LAYER.items()},
        "sources": probes,
    }

    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash(paths),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=[],
        expedients=[],
        notes={
            "origin_carriers": [pr["file"] for pr in probes if pr["origin_latlon"] is not None],
            "ground0_carriers": [pr["file"] for pr in probes if pr["ground0"] is not None],
            "no_origin_files": [pr["file"] for pr in probes if pr["origin_latlon"] is None],
        },
    )
    res.outputs.append(C.write_json(ctx.out, "world_crs.json", crs))
    res.gates = [
        C.Gate("origin_files_agree", len(set(origins)), 1),
        C.Gate("origin_equals_frozen", list(origins[0]) if origins else None, list(C.ORIGIN_LATLON)),
        C.Gate("ground0_files_agree", len(set(grounds)), 1),
        C.Gate("ground0_equals_frozen", grounds[0] if grounds else None, C.GROUND0_M),
        C.Gate("n_files_with_origin", len(origins), 3),
        C.Gate("n_files_with_ground0", len(grounds), 4),
    ]
    return res
