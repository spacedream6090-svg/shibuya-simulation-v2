"""W3 全点対距離(§1 W3・D-W4)。

出力:
- ``w3_cell_dist.npy``   セル→セル最短距離 [m] uint16(対称・65535=到達不能)
- ``w3_next_hop.npy``    道路ノード next-hop 表 int32(3,499² ≈ 49MB・memmap 可)
- ``w3_cell_reps.parquet`` セル代表ノード表

器: 縮約なし・全点対前計算(D-W4)。scipy は環境に無いので numba の二分ヒープ Dijkstra を
全ノード source で回す(`prange` 並列・source ごとは逐次=決定論)。

expedient
- セル間距離 = 代表ノード間の最短経路長(セル内は道路グラフに委ねる=D-W4 の粗経路)。
- uint16 への丸め(四捨五入)。三角不等式ゲートはこの丸め誤差 ±0.5m を許容して 1m 公差で測る。
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numba import njit, prange

from shibuya.core import rng

from . import common as C

STAGE = "W3"
STAGE_VERSION = "1.0.0"

#: 三角不等式の抽出検査に使う三つ組の数(§1 W3 のゲート)。
N_TRIANGLE_SAMPLES = 10_000
#: 乱数の master seed(構築は決定論・ドメイン分離は core.rng)。
BUILD_SEED = 20260908
#: uint16 の到達不能センチネル。
UNREACHABLE = 65535


@njit(cache=True, parallel=True, nogil=True)
def _all_pairs(
    indptr: np.ndarray,
    indices: np.ndarray,
    weights: np.ndarray,
    rep_of: np.ndarray,
    n_reps: int,
) -> tuple[np.ndarray, np.ndarray]:
    """全ノード source の Dijkstra。next-hop 表と代表ノード行の距離を返す。"""
    n = indptr.shape[0] - 1
    m = indices.shape[0]
    nexth = np.empty((n, n), dtype=np.int32)
    dist_rep = np.empty((n_reps, n), dtype=np.float64)
    for s in prange(n):
        d = np.full(n, np.inf)
        fs = np.full(n, -1, dtype=np.int32)
        hn = np.empty(m + 1, dtype=np.int32)
        hk = np.empty(m + 1, dtype=np.float64)
        size = 0
        d[s] = 0.0
        hn[0] = s
        hk[0] = 0.0
        size = 1
        while size > 0:
            u = hn[0]
            key = hk[0]
            size -= 1
            hn[0] = hn[size]
            hk[0] = hk[size]
            i = 0
            while True:
                left = 2 * i + 1
                right = left + 1
                sm = i
                if left < size and hk[left] < hk[sm]:
                    sm = left
                if right < size and hk[right] < hk[sm]:
                    sm = right
                if sm == i:
                    break
                tn = hn[i]
                tk = hk[i]
                hn[i] = hn[sm]
                hk[i] = hk[sm]
                hn[sm] = tn
                hk[sm] = tk
                i = sm
            if key > d[u]:
                continue
            for e in range(indptr[u], indptr[u + 1]):
                v = indices[e]
                nd = key + weights[e]
                if nd < d[v]:
                    d[v] = nd
                    if u == s:
                        fs[v] = v
                    else:
                        fs[v] = fs[u]
                    hn[size] = v
                    hk[size] = nd
                    j = size
                    size += 1
                    while j > 0:
                        par = (j - 1) // 2
                        if hk[par] <= hk[j]:
                            break
                        tn = hn[par]
                        tk = hk[par]
                        hn[par] = hn[j]
                        hk[par] = hk[j]
                        hn[j] = tn
                        hk[j] = tk
                        j = par
        for t in range(n):
            nexth[s, t] = fs[t]
        nexth[s, s] = np.int32(s)
        r = rep_of[s]
        if r >= 0:
            for t in range(n):
                dist_rep[r, t] = d[t]
    return nexth, dist_rep


def build_csr(
    n_nodes: int, u: np.ndarray, v: np.ndarray, w: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """無向辺(平行辺は最小長を採用・自己ループ除去)→ CSR 有向弧。"""
    best: dict[tuple[int, int], float] = {}
    for k in range(len(u)):
        a, b = int(u[k]), int(v[k])
        if a == b:
            continue
        key = (a, b) if a < b else (b, a)
        length = float(w[k])
        if key not in best or length < best[key]:
            best[key] = length
    deg = np.zeros(n_nodes + 1, dtype=np.int64)
    for a, b in best:
        deg[a + 1] += 1
        deg[b + 1] += 1
    indptr = np.cumsum(deg).astype(np.int64)
    cursor = indptr[:-1].copy()
    m = int(indptr[-1])
    indices = np.empty(m, dtype=np.int64)
    weights = np.empty(m, dtype=np.float64)
    for (a, b), length in sorted(best.items()):
        indices[cursor[a]] = b
        weights[cursor[a]] = length
        cursor[a] += 1
        indices[cursor[b]] = a
        weights[cursor[b]] = length
        cursor[b] += 1
    return indptr, indices, weights


def run(ctx: C.Ctx) -> C.StageResult:
    nodes_p = ctx.out / "w1_nodes.parquet"
    edges_p = ctx.out / "w1_edges.parquet"
    cells_p = ctx.out / "w2_cells.parquet"
    for p in (nodes_p, edges_p, cells_p):
        if not p.exists():
            raise FileNotFoundError(f"W3 は W1/W2 の出力を必要とする: {p}")

    nd = C.read_parquet_columns(nodes_p, ["node_idx", "node_id"])
    ed = C.read_parquet_columns(edges_p, ["u_idx", "v_idx", "length_m"])
    cd = C.read_parquet_columns(cells_p, ["place_id", "rep_node_idx", "rep_node_id"])

    n_nodes = len(nd["node_idx"])
    indptr, indices, weights = build_csr(
        n_nodes,
        np.asarray(ed["u_idx"]),
        np.asarray(ed["v_idx"]),
        np.asarray(ed["length_m"], dtype=np.float64),
    )

    reps = np.asarray(cd["rep_node_idx"], dtype=np.int64)
    rep_of = np.full(n_nodes, -1, dtype=np.int64)
    for k, s in enumerate(reps):
        rep_of[int(s)] = k
    n_reps = len(reps)

    nexth, dist_rep = _all_pairs(indptr, indices, weights, rep_of, n_reps)

    sub = dist_rep[:, reps]
    # 同じ実距離を2回(i→j と j→i)独立に Dijkstra で足し上げるので、浮動小数の加算順序の差で
    # 1e-9 級の非対称が出る。エッジ長が 0.1m 刻み=和が丁度 x.5 に乗ることが多く、そのまま丸めると
    # 1m の非対称になる。対称行列は数学的性質なので、丸め前に要素ごと最小で対称化する。
    float_asym = float(np.nanmax(np.abs(np.where(np.isfinite(sub), sub, 0.0) - np.where(np.isfinite(sub.T), sub.T, 0.0)))) if n_reps else 0.0
    sub = np.minimum(sub, sub.T)
    finite = np.isfinite(sub)
    cell = np.full((n_reps, n_reps), UNREACHABLE, dtype=np.uint16)
    cell[finite] = np.minimum(np.rint(sub[finite]), UNREACHABLE - 1).astype(np.uint16)

    asym = int(np.count_nonzero(cell != cell.T))
    n_unreachable = int(np.count_nonzero(~finite))

    # 三角不等式(§1 W3): 10,000 三つ組を決定論の乱数で抽出
    gen = rng.stream(BUILD_SEED, "build.W3", 0)
    tri = gen.integers(0, n_reps, size=(N_TRIANGLE_SAMPLES, 3), dtype=np.int64)
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    ok = (cell[a, b] != UNREACHABLE) & (cell[b, c] != UNREACHABLE) & (cell[a, c] != UNREACHABLE)
    lhs = cell[a, c][ok].astype(np.int64)
    rhs = cell[a, b][ok].astype(np.int64) + cell[b, c][ok].astype(np.int64)
    viol_tol1 = int(np.count_nonzero(lhs > rhs + 1))
    viol_tol0 = int(np.count_nonzero(lhs > rhs))

    # next-hop の健全性: 代表ノード対 200 件で経路を辿り直して長さ一致を確認
    check_pairs = gen.integers(0, n_reps, size=(200, 2), dtype=np.int64)
    walk_bad = 0
    for s_i, t_i in check_pairs:
        s = int(reps[s_i])
        t = int(reps[t_i])
        if s == t:
            continue
        total = 0.0
        cur = s
        steps = 0
        while cur != t and steps <= n_nodes:
            nxt = int(nexth[cur, t])
            if nxt < 0:
                break
            lo, hi = indptr[cur], indptr[cur + 1]
            seg = np.inf
            for e in range(lo, hi):
                if indices[e] == nxt:
                    seg = float(weights[e])
                    break
            total += seg
            cur = nxt
            steps += 1
        if cur != t or abs(total - float(dist_rep[s_i, t])) > 1e-6:
            walk_bad += 1

    params: dict[str, Any] = {
        "weight": "OSM edge length_m (parallel edges: min)",
        "dtype_cell": "uint16 metres (rint)",
        "dtype_next_hop": "int32",
        "unreachable": UNREACHABLE,
        "seed": BUILD_SEED,
        "n_triangle_samples": N_TRIANGLE_SAMPLES,
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash([nodes_p, edges_p, cells_p]),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=["街路(歩行グラフ)", "セル(場所100m+層)"],
        expedients=[
            "セル間距離 = 代表ノード間の最短経路長",
            "uint16 メートル丸め(三角不等式は 1m 公差で検査)",
            "丸め前に min(D, Dᵀ) で対称化(浮動小数の加算順序差 1e-9 級を吸収)",
        ],
        notes={
            "n_nodes": n_nodes,
            "n_directed_arcs": int(indices.shape[0]),
            "n_cells": n_reps,
            "cell_dist_max_m": int(cell[cell != UNREACHABLE].max()) if n_reps else None,
            "cell_dist_mean_m": (
                round(float(cell[cell != UNREACHABLE].mean()), 2) if n_reps else None
            ),
            "next_hop_bytes": int(nexth.nbytes),
            "triangle_violations_tol0": viol_tol0,
            "triangle_samples_evaluated": int(ok.sum()),
            "float_asymmetry_max_m_before_symmetrize": float(f"{float_asym:.3e}"),
        },
    )

    out_cell = C.write_npy(ctx.out, "w3_cell_dist.npy", cell)
    out_next = C.write_npy(ctx.out, "w3_next_hop.npy", nexth)
    res.outputs.append(out_cell)
    res.outputs.append(out_next)
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w3_cell_reps.parquet",
            {
                "cell_idx": np.arange(n_reps, dtype=np.int32),
                "place_id": cd["place_id"],
                "rep_node_idx": np.asarray(cd["rep_node_idx"], dtype=np.int32),
                "rep_node_id": cd["rep_node_id"],
            },
        )
    )

    res.gates = [
        C.Gate("cell_matrix_symmetric", asym, 0),
        C.Gate("triangle_violations", viol_tol1, 0),
        C.Gate("unreachable_cell_pairs", n_unreachable, 0),
        C.Gate("next_hop_walk_mismatch", walk_bad, 0),
        C.Gate("next_hop_shape", list(nexth.shape), [n_nodes, n_nodes]),
        C.Gate("cell_dist_sha256", out_cell["sha256"], None),
        C.Gate("next_hop_sha256", out_next["sha256"], None),
    ]
    return res
