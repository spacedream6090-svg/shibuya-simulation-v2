"""W2 セル生成(§1 W2・D-W2)。

出力:
- ``w2_cells.parquet``      place_id = 100m格子(ix,iy)×層バンド。代表ノード・ブロック束ね付き。
- ``w2_blocks.parquet``     街区(=GL 街路網の平面面)。面積・周長・重心・帰属セル。
- ``w2_block_rings.npz``    街区外周の折れ線(coords, offsets)。

街区面の抽出(shapely 非導入のため自前・純粋な回転系走査)
- GL(エッジ layer=0)の**単純グラフ**(平行辺は先着1本・自己ループなし)を使う。
- 各ノードで出射ハーフエッジを最初の線分の方位角で反時計回りに整列 → ``next(h)`` =
  ``twin(h)`` の1つ手前(時計回り側)。この走査で得る面のうち符号付き面積が正のものが有界面。
- 面数の理論値(Euler)= E - V + C(単純GL グラフ)。仕様書の「街区面 1,242」はこの値。

expedient
- 格子原点・100m・層3値(D-W2 で宣言済み)。
- セルの ``n_edges`` = 端点の少なくとも一方がそのセルに属するエッジ数(重複計上あり)。
- セル代表ノード = セル内ノード重心に最も近いノード(同点は node_idx 最小)。
- 街区→セル写像 = 外周上の GL ノードが属するセルの集合(空にならないので全射が保証される)。
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np
import pyarrow as pa

from . import common as C

STAGE = "W2"
STAGE_VERSION = "1.0.0"

#: 世界カタログ #3(街区)の実数量。
EXPECTED_BLOCK_EULER = 1242
#: 世界カタログ #4(セル)の GL 格子数。
EXPECTED_CELLS_GL = 453
#: 4近傍セル対(GL格子)の期待値(§1 W2)。
EXPECTED_4NB_PAIRS_GL = 785


def _face_traversal(
    n_nodes: int, half: list[tuple[int, int, int]], starts: list[np.ndarray]
) -> list[list[int]]:
    """回転系による面走査。

    Args:
        n_nodes: ノード数。
        half: ハーフエッジ ``(origin, dest, edge_idx)``。``i^1`` が twin。
        starts: ハーフエッジ i の始点から最初の幾何点への方向ベクトル。

    Returns:
        面(ハーフエッジ添字の巡回列)のリスト。
    """
    out: dict[int, list[tuple[float, int]]] = defaultdict(list)
    for i, (u, _v, _e) in enumerate(half):
        ang = math.atan2(float(starts[i][1]), float(starts[i][0]))
        out[u].append((ang, i))
    pos_in_ring: dict[int, tuple[int, int]] = {}
    for u, lst in out.items():
        lst.sort()
        for p, (_a, i) in enumerate(lst):
            pos_in_ring[i] = (u, p)
    nxt = np.empty(len(half), dtype=np.int64)
    for i in range(len(half)):
        twin = i ^ 1
        u, p = pos_in_ring[twin]
        ring = out[u]
        nxt[i] = ring[(p - 1) % len(ring)][1]
    seen = np.zeros(len(half), dtype=bool)
    faces: list[list[int]] = []
    for i in range(len(half)):
        if seen[i]:
            continue
        cyc: list[int] = []
        j = i
        while not seen[j]:
            seen[j] = True
            cyc.append(int(j))
            j = int(nxt[j])
        faces.append(cyc)
    return faces


def _ring_stats(pts: np.ndarray) -> tuple[float, float, float, float]:
    """閉多角形(始点=終点を含まない)の (符号付き面積, 周長, cx, cy)。"""
    x = pts[:, 0]
    y = pts[:, 1]
    x1 = np.roll(x, -1)
    y1 = np.roll(y, -1)
    cross = x * y1 - x1 * y
    area2 = float(cross.sum())
    area = area2 / 2.0
    per = float(np.hypot(x1 - x, y1 - y).sum())
    if abs(area2) < 1e-12:
        return area, per, float(x.mean()), float(y.mean())
    cx = float(((x + x1) * cross).sum() / (3.0 * area2))
    cy = float(((y + y1) * cross).sum() / (3.0 * area2))
    return area, per, cx, cy


def _components(n: int, pairs: list[tuple[int, int]], members: set[int]) -> int:
    parent = {m: m for m in members}

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for u, v in pairs:
        if u in parent and v in parent:
            ru, rv = find(u), find(v)
            if ru != rv:
                parent[ru] = rv
    return len({find(m) for m in members})


def run(ctx: C.Ctx) -> C.StageResult:
    nodes_p = ctx.out / "w1_nodes.parquet"
    edges_p = ctx.out / "w1_edges.parquet"
    geom_p = ctx.out / "w1_edge_geometry.npz"
    for p in (nodes_p, edges_p, geom_p):
        if not p.exists():
            raise FileNotFoundError(f"W2 は W1 の出力を必要とする: {p}")

    nd = C.read_parquet_columns(nodes_p, ["node_idx", "node_id", "x", "y", "band"])
    ed = C.read_parquet_columns(
        edges_p, ["u_idx", "v_idx", "klass", "layer", "geom_start", "geom_count"]
    )
    with np.load(geom_p) as z:
        coords = z["coords"]

    nx = np.asarray(nd["x"])
    ny = np.asarray(nd["y"])
    nband = nd["band"]
    n_nodes = len(nband)

    # --- セル(格子×バンド)---
    ij = [C.grid_ij(float(nx[i]), float(ny[i])) for i in range(n_nodes)]
    node_place = [C.place_id(ij[i][0], ij[i][1], nband[i]) for i in range(n_nodes)]
    members: dict[str, list[int]] = defaultdict(list)
    for i, pid in enumerate(node_place):
        members[pid].append(i)

    cell_edges: dict[str, int] = defaultdict(int)
    for k in range(len(ed["u_idx"])):
        a = node_place[ed["u_idx"][k]]
        b = node_place[ed["v_idx"][k]]
        cell_edges[a] += 1
        if b != a:
            cell_edges[b] += 1

    # --- GL 単純グラフの街区面 ---
    gl = [k for k in range(len(ed["layer"])) if int(ed["layer"][k]) == 0]
    seen_pair: set[tuple[int, int]] = set()
    simple: list[int] = []
    for k in gl:
        u, v = int(ed["u_idx"][k]), int(ed["v_idx"][k])
        if u == v:
            continue
        key = (u, v) if u < v else (v, u)
        if key in seen_pair:
            continue
        seen_pair.add(key)
        simple.append(k)

    half: list[tuple[int, int, int]] = []
    half_pts: list[np.ndarray] = []
    starts: list[np.ndarray] = []
    for k in simple:
        u, v = int(ed["u_idx"][k]), int(ed["v_idx"][k])
        s = int(ed["geom_start"][k])
        c = int(ed["geom_count"][k])
        g = coords[s : s + c]
        half.append((u, v, k))
        half_pts.append(g)
        starts.append(g[1] - g[0])
        half.append((v, u, k))
        half_pts.append(g[::-1])
        starts.append(g[-2] - g[-1])

    faces = _face_traversal(n_nodes, half, starts)

    gl_nodes = {u for u, _v, _e in half}
    gl_pairs = [(int(ed["u_idx"][k]), int(ed["v_idx"][k])) for k in simple]
    gl_comp = _components(n_nodes, gl_pairs, gl_nodes)
    euler_faces = len(simple) - len(gl_nodes) + gl_comp

    ring_coords: list[np.ndarray] = []
    ring_off = [0]
    b_area: list[float] = []
    b_per: list[float] = []
    b_cx: list[float] = []
    b_cy: list[float] = []
    b_nedges: list[int] = []
    b_cells: list[list[str]] = []
    b_pid: list[str] = []
    n_outer = 0
    for cyc in faces:
        pts = np.concatenate([half_pts[j][:-1] for j in cyc], axis=0)
        area, per, cx, cy = _ring_stats(pts)
        if area <= 0.0:
            n_outer += 1
            continue
        cells = sorted({node_place[half[j][0]] for j in cyc})
        b_cells.append(cells)
        gi, gj = C.grid_ij(cx, cy)
        centroid_pid = C.place_id(gi, gj, "GL")
        b_pid.append(centroid_pid if centroid_pid in members else cells[0])
        b_area.append(round(area, 3))
        b_per.append(round(per, 3))
        b_cx.append(round(cx, 3))
        b_cy.append(round(cy, 3))
        b_nedges.append(len(cyc))
        ring_coords.append(pts)
        ring_off.append(ring_off[-1] + len(pts))

    n_blocks = len(b_area)
    cell_blocks: dict[str, list[int]] = defaultdict(list)
    for bi, cells in enumerate(b_cells):
        for pid in cells:
            cell_blocks[pid].append(bi)
    cell_block_area: dict[str, float] = defaultdict(float)
    for bi, pid in enumerate(b_pid):
        cell_block_area[pid] += b_area[bi]

    # --- セル表(place_id の辞書順で安定化)---
    pids = sorted(members)
    rows_ix: list[int] = []
    rows_iy: list[int] = []
    rows_band: list[str] = []
    rows_cx: list[float] = []
    rows_cy: list[float] = []
    rows_nn: list[int] = []
    rows_ne: list[int] = []
    rows_rep: list[int] = []
    rows_rep_id: list[str] = []
    rows_blocks: list[list[int]] = []
    for pid in pids:
        mem = members[pid]
        i0 = mem[0]
        rows_ix.append(ij[i0][0])
        rows_iy.append(ij[i0][1])
        rows_band.append(nband[i0])
        mx = float(np.mean(nx[mem]))
        my = float(np.mean(ny[mem]))
        rows_cx.append(round(mx, 3))
        rows_cy.append(round(my, 3))
        rows_nn.append(len(mem))
        rows_ne.append(cell_edges[pid])
        d2 = (nx[mem] - mx) ** 2 + (ny[mem] - my) ** 2
        rep = int(mem[int(np.argmin(d2))])
        rows_rep.append(rep)
        rows_rep_id.append(nd["node_id"][rep])
        rows_blocks.append(sorted(cell_blocks.get(pid, [])))

    # --- 4近傍セル対 ---
    pid_set = set(pids)
    xy_gl = {(rows_ix[i], rows_iy[i]) for i in range(len(pids)) if rows_band[i] == "GL"}
    pairs_gl = sum(
        1 for (a, b) in xy_gl for d in ((1, 0), (0, 1)) if (a + d[0], b + d[1]) in xy_gl
    )
    key_set = {(rows_ix[i], rows_iy[i], rows_band[i]) for i in range(len(pids))}
    pairs_band = sum(
        1
        for (a, b, bd) in key_set
        for d in ((1, 0), (0, 1))
        if (a + d[0], b + d[1], bd) in key_set
    )
    surjective = all(len(c) > 0 for c in b_cells) and all(p in pid_set for p in b_pid)

    params: dict[str, Any] = {
        "cell_m": C.CELL_M,
        "grid_origin_xy": [0.0, 0.0],
        "bands": list(C.BANDS),
        "block_graph": "GL edges (layer==0), simple (parallel edges deduplicated, no self loops)",
        "block_extraction": "rotation-system face traversal; bounded face = positive signed area",
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash([nodes_p, edges_p, geom_p]),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=["セル(場所100m+層)", "街区"],
        expedients=[
            "格子原点(0,0)・100m・層3値(D-W2)",
            "セル n_edges = 端点の一方でも属するエッジ数(重複計上)",
            "セル代表ノード = セル内ノード重心に最近のノード",
            "街区→セル = 外周上の GL ノードのセル集合",
        ],
        notes={
            "n_cells_by_band": {
                b: sum(1 for x in rows_band if x == b) for b in C.BANDS
            },
            "gl_simple_edges": len(simple),
            "gl_nodes": len(gl_nodes),
            "gl_components": gl_comp,
            "faces_traversed": len(faces),
            "faces_non_positive_area": n_outer,
            "block_polygons_vs_euler_diff": n_blocks - euler_faces,
            "spec_expected_place_id_range": "550-600 (D-W1 の見積り)",
            "block_area_m2_total": round(float(sum(b_area)), 1),
            "block_area_m2_median": round(float(np.median(b_area)), 1) if n_blocks else None,
        },
    )

    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w2_cells.parquet",
            {
                "place_id": pids,
                "ix": np.array(rows_ix, dtype=np.int32),
                "iy": np.array(rows_iy, dtype=np.int32),
                "band": rows_band,
                "centroid_x": np.array(rows_cx),
                "centroid_y": np.array(rows_cy),
                "n_nodes": np.array(rows_nn, dtype=np.int32),
                "n_edges": np.array(rows_ne, dtype=np.int32),
                "rep_node_idx": np.array(rows_rep, dtype=np.int32),
                "rep_node_id": rows_rep_id,
                "block_ids": pa.array(rows_blocks, type=pa.list_(pa.int32())),
                "area_m2": np.full(len(pids), C.CELL_M * C.CELL_M),
                "block_area_m2": np.array([round(cell_block_area.get(p, 0.0), 3) for p in pids]),
            },
        )
    )
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w2_blocks.parquet",
            {
                "block_id": np.arange(n_blocks, dtype=np.int32),
                "area_m2": np.array(b_area),
                "perimeter_m": np.array(b_per),
                "centroid_x": np.array(b_cx),
                "centroid_y": np.array(b_cy),
                "n_edges": np.array(b_nedges, dtype=np.int32),
                "place_id": b_pid,
                "place_ids": pa.array(b_cells, type=pa.list_(pa.string())),
            },
        )
    )
    res.outputs.append(
        C.write_npz(
            ctx.out,
            "w2_block_rings.npz",
            coords=(
                np.concatenate(ring_coords, axis=0)
                if ring_coords
                else np.zeros((0, 2), dtype=np.float64)
            ),
            offsets=np.asarray(ring_off, dtype=np.int32),
        )
    )

    res.gates = [
        C.Gate("n_place_ids", len(pids), None),
        C.Gate("n_cells_gl", sum(1 for b in rows_band if b == "GL"), EXPECTED_CELLS_GL),
        C.Gate("cell_4neighbour_pairs_gl", pairs_gl, EXPECTED_4NB_PAIRS_GL),
        C.Gate("cell_4neighbour_pairs_same_band", pairs_band, None),
        C.Gate("block_euler_count", euler_faces, EXPECTED_BLOCK_EULER),
        C.Gate("block_polygons", n_blocks, None),
        C.Gate("block_to_cell_surjective", bool(surjective), True),
    ]
    return res
