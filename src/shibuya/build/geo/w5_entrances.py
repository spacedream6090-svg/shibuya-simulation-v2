"""W5 入口点(§1 W5・D-W6)。

- 駅出入口 45(Overpass 2026-09-07・``station_entrances_overpass.json``)= **mechanism**
- 建物の実入口 16 棟(OSM ``entrances`` の実座標)= **mechanism**
- 残り 7,194 棟 = 建物重心から最寄り道路ノードへの決定論射影 = **expedient**

出力: ``w5_entrances.parquet``(entrance_id, kind, ref, name, x, y, node_idx, node_id,
dist_to_node_m, place_id, own_grid_place_id, band)。
``place_id`` = 最寄りノードのセル(エンジンが歩行グラフ上で使う)・``own_grid_place_id`` =
入口自身の座標が落ちる格子セル(W2 の被覆検査に使う)。

ゲート: 全入口ノードが歩行グラフのノード集合に入ること・駅出口45が**自分の格子セル**で
W2 のセル集合に載っていること(``station_exit_own_grid_cell_missing`` = 0)。

expedient
- 入口→道路ノードの割り当ては「ユークリッド最寄りノード」(層を問わない)。
- 建物入口の射影点は建物重心(footprint 頂点ではない)。v8 が持つ既存の ``entrance`` 欄との
  一致率を notes に出す(v1 規則の再現度の点検であって、規則の較正ではない)。
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np

from . import common as C

STAGE = "W5"
STAGE_VERSION = "1.0.0"

INPUT_FILES: tuple[tuple[str, ...], ...] = (
    ("realworld", "osm", "shibuya_osm_wide_v8.json"),
    ("realworld", "osm", "station_entrances_overpass.json"),
)

EXPECTED_STATION_EXITS = 45


def nearest_node(
    px: np.ndarray, py: np.ndarray, nx: np.ndarray, ny: np.ndarray, chunk: int = 512
) -> tuple[np.ndarray, np.ndarray]:
    """点群 → 最寄りノード添字と距離(同点は添字の小さい方)。"""
    idx = np.empty(len(px), dtype=np.int64)
    dist = np.empty(len(px), dtype=np.float64)
    for a in range(0, len(px), chunk):
        b = min(a + chunk, len(px))
        d2 = (nx[None, :] - px[a:b, None]) ** 2 + (ny[None, :] - py[a:b, None]) ** 2
        k = np.argmin(d2, axis=1)
        idx[a:b] = k
        dist[a:b] = np.sqrt(d2[np.arange(b - a), k])
    return idx, dist


def _exit_name(tags: dict[str, str]) -> str:
    for key in ("name:ja", "name", "ref"):
        if tags.get(key):
            return str(tags[key])
    return ""


def run(ctx: C.Ctx) -> C.StageResult:
    paths = [ctx.path(*parts) for parts in INPUT_FILES]
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"W5 入力が無い: {p}")
    nodes_p = ctx.out / "w1_nodes.parquet"
    cells_p = ctx.out / "w2_cells.parquet"
    for p in (nodes_p, cells_p):
        if not p.exists():
            raise FileNotFoundError(f"W5 は W1/W2 の出力を必要とする: {p}")

    osm = C.load_json(paths[0])
    exits = C.load_json(paths[1])["elements"]
    nd = C.read_parquet_columns(nodes_p, ["node_idx", "node_id", "x", "y", "band"])
    cells = set(C.read_parquet_columns(cells_p, ["place_id"])["place_id"])

    nx = np.asarray(nd["x"])
    ny = np.asarray(nd["y"])
    nband = nd["band"]
    nid = nd["node_id"]

    kinds: list[str] = []
    refs: list[str] = []
    names: list[str] = []
    xs: list[float] = []
    ys: list[float] = []

    for el in exits:
        x, y = C.latlon_to_local(float(el["lat"]), float(el["lon"]))
        kinds.append("station_exit")
        refs.append(f"n{el['id']}")
        names.append(_exit_name(el.get("tags", {})))
        xs.append(round(x, 3))
        ys.append(round(y, 3))
    n_exits = len(exits)

    v8_entrance: list[str] = []
    for b in osm["buildings"]:
        pts = b.get("entrances")
        if pts:
            for pt in pts:
                kinds.append("osm_entrance")
                refs.append(b["id"])
                names.append(b.get("name") or "")
                xs.append(float(pt["x"]))
                ys.append(float(pt["y"]))
                v8_entrance.append("")
        else:
            kinds.append("projected")
            refs.append(b["id"])
            names.append(b.get("name") or "")
            xs.append(float(b["cx"]))
            ys.append(float(b["cy"]))
            v8_entrance.append(b["entrance"])

    px = np.asarray(xs)
    py = np.asarray(ys)
    node_i, node_d = nearest_node(px, py, nx, ny)

    place_ids: list[str] = []
    bands: list[str] = []
    own_place_ids: list[str] = []
    own_grid_missing = 0
    for k in range(len(px)):
        i = int(node_i[k])
        band = nband[i]
        bands.append(band)
        place_ids.append(
            C.place_id(*C.grid_ij(float(nx[i]), float(ny[i])), band)
        )
        # 入口**自身**の座標が落ちる格子セル(最寄りノードのセルとは別物)。
        own = C.place_id(*C.grid_ij(float(px[k]), float(py[k])), band)
        own_place_ids.append(own)
        if kinds[k] == "station_exit" and own not in cells:
            own_grid_missing += 1

    # v8 の既存 entrance 欄との一致(射影規則の再現度の点検)
    proj_rows = [k for k in range(len(px)) if kinds[k] == "projected"]
    v8_map = {b["id"]: b["entrance"] for b in osm["buildings"] if not b.get("entrances")}
    agree = sum(1 for k in proj_rows if nid[int(node_i[k])] == v8_map.get(refs[k]))

    exit_rows = [k for k in range(len(px)) if kinds[k] == "station_exit"]
    # 駅出口が「自分の格子セル」で W2 のセル集合に載っているか。最寄りノードのセルを引くと
    # W2 が歩行グラフのノードから作られている以上ほぼ自明に真になるので、**出口自身の格子**で問う。
    exits_with_own_cell = sum(1 for k in exit_rows if own_place_ids[k] in cells)
    all_nodes_ok = bool(np.all((node_i >= 0) & (node_i < len(nid))))

    kind_counts = dict(sorted(Counter(kinds).items()))
    params: dict[str, Any] = {
        "projection": "nearest walk-graph node (euclidean, ties -> smallest node_idx)",
        "building_projection_point": "footprint centroid (cx, cy)",
        "station_exit_source": "station_entrances_overpass.json (attic 2026-09-07)",
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash([*paths, nodes_p, cells_p]),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=["駅・出口", "建物"],
        expedients=[
            "残り 7,194 棟の入口 = 建物重心から最寄り道路ノードへの射影(D-W6)",
            "入口→セルは最寄りノードのセルを採る(格子そのものではない)",
        ],
        notes={
            "kind_counts": kind_counts,
            "projected_agree_with_v8_entrance": agree,
            "projected_rows": len(proj_rows),
            "station_exit_own_grid_cell_missing": own_grid_missing,
            "station_exit_own_grid_cells_missing_ids": sorted(
                {own_place_ids[k] for k in exit_rows if own_place_ids[k] not in cells}
            ),
            "dist_to_node_median_m": round(float(np.median(node_d)), 2),
            "dist_to_node_max_m": round(float(node_d.max()), 2),
            "exit_dist_to_node_max_m": round(float(node_d[exit_rows].max()), 2),
            "exit_band_counts": dict(sorted(Counter(bands[k] for k in exit_rows).items())),
        },
    )
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w5_entrances.parquet",
            {
                "entrance_idx": np.arange(len(px), dtype=np.int32),
                "kind": kinds,
                "ref": refs,
                "name": names,
                "x": px,
                "y": py,
                "node_idx": node_i.astype(np.int32),
                "node_id": [nid[int(i)] for i in node_i],
                "dist_to_node_m": np.round(node_d, 3),
                "place_id": place_ids,
                "own_grid_place_id": own_place_ids,
                "band": bands,
            },
        )
    )
    res.gates = [
        C.Gate("station_exits", n_exits, EXPECTED_STATION_EXITS),
        C.Gate("station_exits_in_banded_cell", exits_with_own_cell, EXPECTED_STATION_EXITS),
        C.Gate("station_exit_own_grid_cell_missing", own_grid_missing, 0),
        C.Gate("all_entrance_nodes_in_walk_graph", all_nodes_ok, True),
        C.Gate("entrances_total", len(px), None),
        C.Gate("kind_osm_entrance", kind_counts.get("osm_entrance", 0), None),
        C.Gate("kind_projected", kind_counts.get("projected", 0), None),
    ]
    return res
