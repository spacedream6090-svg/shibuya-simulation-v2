"""R-59 計測: PLATEAU 道路 LOD3 の三角形をそのままナビメッシュとして使ったときの規模と 1 回の探索の費用。

読むだけ(手元の data/plateau/tran_lod3.npz)。書くのは --out の小さな JSON だけ。
新しい依存なし(numpy・numba は .venv に既存)。scipy・shapely は .venv に無いので使わない。

測るもの
1. 三角形の数(重複を畳んだ後)・面積・辺の共有(内部辺/境界辺/3 枚以上で共有)・連結成分。
   溶接の許容差(0.05 m=量子化そのまま / 0.10 / 0.20 / 0.50 m)ごとの成分数も数える
   (PLATEAU の面は地物ごとに作られ、隣の地物と頂点を共有しない所がある=どこで切れるかを見る)。
2. 三角形の双対グラフ上の A*(重心間距離・同点は三角形番号で決める=決定論)+ funnel
   (string pulling)で 1 回の探索の時間。200 m 四方の窓と、区画全体の 2 通り。
3. 目的地 1 つから全三角形への距離場(Dijkstra)の時間とメモリ=流れ場/目的地ごとの表の費用。
4. 全組の next-hop 表のメモリ(三角形数^2)。

検算(第 0-1 規律「答えの分かっている場面で先に」): 合成の L 字通路で funnel の経路長が
解析解(角を回る 2 線分の和)と一致するか、障害のない帯で直線距離と一致するかを最初に確かめる。

使い方:
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe docs/research/r59/measure_navmesh.py \
      --out docs/research/r59/measure_navmesh.json
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numba as nb
import numpy as np

REPO = Path(__file__).resolve().parents[3]
NPZ = REPO / "data" / "plateau" / "tran_lod3.npz"
QUANT = 0.05  # tran_lod3.json quant_scale


# ------------------------------------------------------------------ 読み込み・溶接
def load_triangles(codes: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """量子化整数の三角形 (n,3,2) int64・function コード・z を返す(完全一致の重複は畳む)。
    codes は PLATEAU の function コード(npz に在るのは 1000 車道部・1020 車道交差部・2000 歩道部・3000 島)。"""
    z = np.load(NPZ)
    xy = z["xy"].astype(np.int64) + z["origin_q"].astype(np.int64)  # 量子化整数(0.05 m 刻み)
    off = z["poly_offsets"]
    assert np.all(np.diff(off) == 3), "三角形分割済みの前提が崩れた"
    tri = xy[off[0] : off[-1]].reshape(-1, 3, 2)
    cls = z["poly_code"].astype(np.int64)
    pz = z["poly_z"][:, 0].astype(np.float64)
    keep = np.isin(cls, codes)
    tri, cls, pz = tri[keep], cls[keep], pz[keep]
    # 重複を畳む(頂点順に依存しない鍵)
    key = np.sort(tri[:, :, 0] * 1_000_000 + tri[:, :, 1], axis=1)
    _, first = np.unique(key, axis=0, return_index=True)
    first = np.sort(first)  # 元の順を保つ=決定論
    return tri[first], cls[first], pz[first]


def weld(tri_q: np.ndarray, tol_m: float) -> tuple[np.ndarray, np.ndarray]:
    """頂点を tol_m の格子に丸めて溶接。返り値=(頂点座標 m (V,2), 三角形の頂点番号 (n,3))。"""
    step = max(1, int(round(tol_m / QUANT)))
    snapped = np.floor_divide(tri_q + step // 2, step) * step  # 格子に丸め
    flat = snapped.reshape(-1, 2)
    keys = flat[:, 0] * 10_000_000 + flat[:, 1]
    uniq, inv = np.unique(keys, return_inverse=True)  # 並べ替え済み=決定論
    verts = np.empty((uniq.size, 2), dtype=np.float64)
    verts[inv, 0] = flat[:, 0] * QUANT
    verts[inv, 1] = flat[:, 1] * QUANT
    faces = inv.reshape(-1, 3).astype(np.int64)
    # 丸めで潰れた三角形(同じ頂点が 2 回)を除く
    ok = (faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 0] != faces[:, 2])
    return verts, faces[ok]


def build_adjacency(faces: np.ndarray) -> dict:
    """辺の共有から双対グラフ(CSR)を作る。辺の並びは(小さい頂点, 大きい頂点, 三角形番号)で整列。"""
    n = faces.shape[0]
    e = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]], axis=0)
    owner = np.concatenate([np.arange(n)] * 3)
    a = np.minimum(e[:, 0], e[:, 1])
    b = np.maximum(e[:, 0], e[:, 1])
    order = np.lexsort((owner, b, a))
    a, b, owner = a[order], b[order], owner[order]
    new = np.ones(a.size, dtype=bool)
    new[1:] = (a[1:] != a[:-1]) | (b[1:] != b[:-1])
    gid = np.cumsum(new) - 1
    counts = np.bincount(gid)
    n_boundary = int((counts == 1).sum())
    n_interior = int((counts == 2).sum())
    n_nonmanifold = int((counts >= 3).sum())
    # 2 枚以上で共有する辺は全ての組を隣接にする(非多様体も通す)
    starts = np.flatnonzero(new)
    src, dst, ea, eb = [], [], [], []
    for s, c in zip(starts, counts):
        if c < 2:
            continue
        ids = owner[s : s + c]
        for i in range(c):
            for j in range(c):
                if i != j:
                    src.append(ids[i]); dst.append(ids[j]); ea.append(a[s]); eb.append(b[s])
    src = np.asarray(src, dtype=np.int64); dst = np.asarray(dst, dtype=np.int64)
    ea = np.asarray(ea, dtype=np.int64); eb = np.asarray(eb, dtype=np.int64)
    o = np.lexsort((dst, src))
    src, dst, ea, eb = src[o], dst[o], ea[o], eb[o]
    indptr = np.zeros(n + 1, dtype=np.int64)
    np.add.at(indptr, src + 1, 1)
    indptr = np.cumsum(indptr)
    return dict(indptr=indptr, nbr=dst, pa=ea, pb=eb, n_boundary=n_boundary,
                n_interior=n_interior, n_nonmanifold=n_nonmanifold)


@nb.njit(cache=False)
def components(indptr, nbr, n):
    comp = -np.ones(n, dtype=np.int64)
    stack = np.empty(n, dtype=np.int64)
    c = 0
    for s in range(n):
        if comp[s] >= 0:
            continue
        top = 0; stack[0] = s; comp[s] = c
        while top >= 0:
            u = stack[top]; top -= 1
            for k in range(indptr[u], indptr[u + 1]):
                v = nbr[k]
                if comp[v] < 0:
                    comp[v] = c; top += 1; stack[top] = v
        c += 1
    return comp, c


# ------------------------------------------------------------------ 二分ヒープ(同点は番号で決める)
@nb.njit(cache=False)
def _less(fa, ia, fb, ib):
    return fa < fb or (fa == fb and ia < ib)


@nb.njit(cache=False)
def heap_push(hf, hi, size, f, i):
    k = size
    hf[k] = f; hi[k] = i
    while k > 0:
        p = (k - 1) // 2
        if _less(hf[k], hi[k], hf[p], hi[p]):
            hf[k], hf[p] = hf[p], hf[k]; hi[k], hi[p] = hi[p], hi[k]; k = p
        else:
            break
    return size + 1


@nb.njit(cache=False)
def heap_pop(hf, hi, size):
    f = hf[0]; i = hi[0]
    size -= 1
    hf[0] = hf[size]; hi[0] = hi[size]
    k = 0
    while True:
        l = 2 * k + 1; r = l + 1; m = k
        if l < size and _less(hf[l], hi[l], hf[m], hi[m]):
            m = l
        if r < size and _less(hf[r], hi[r], hf[m], hi[m]):
            m = r
        if m == k:
            break
        hf[k], hf[m] = hf[m], hf[k]; hi[k], hi[m] = hi[m], hi[k]; k = m
    return f, i, size


@nb.njit(cache=False)
def astar(indptr, nbr, cen, s, t, g, parent, closed, stamp, hf, hi):
    """重心間距離の A*。g/parent/closed は使い回し(stamp で初期化を省く)。返り値=(展開数, 見つかったか)。"""
    size = 0
    g[s] = 0.0; parent[s] = -1; closed[s] = -stamp  # -stamp=開いた, stamp=閉じた
    h = math.hypot(cen[s, 0] - cen[t, 0], cen[s, 1] - cen[t, 1])
    size = heap_push(hf, hi, size, h, s)
    expanded = 0
    while size > 0:
        f, u, size = heap_pop(hf, hi, size)
        if closed[u] == stamp:
            continue
        closed[u] = stamp
        expanded += 1
        if u == t:
            return expanded, True
        for k in range(indptr[u], indptr[u + 1]):
            v = nbr[k]
            if closed[v] == stamp:
                continue
            w = g[u] + math.hypot(cen[u, 0] - cen[v, 0], cen[u, 1] - cen[v, 1])
            if closed[v] != -stamp or w < g[v]:
                g[v] = w; parent[v] = u; closed[v] = -stamp
                hv = math.hypot(cen[v, 0] - cen[t, 0], cen[v, 1] - cen[t, 1])
                size = heap_push(hf, hi, size, w + hv, v)
    return expanded, False


@nb.njit(cache=False)
def dijkstra_all(indptr, nbr, cen, t, dist, parent, hf, hi):
    """目的地 t から全三角形への距離場(重心間距離)。parent=次に進む三角形(=next-hop)。"""
    n = dist.shape[0]
    for i in range(n):
        dist[i] = np.inf; parent[i] = -1
    dist[t] = 0.0
    size = heap_push(hf, hi, 0, 0.0, t)
    while size > 0:
        d, u, size = heap_pop(hf, hi, size)
        if d > dist[u]:
            continue
        for k in range(indptr[u], indptr[u + 1]):
            v = nbr[k]
            w = d + math.hypot(cen[u, 0] - cen[v, 0], cen[u, 1] - cen[v, 1])
            if w < dist[v]:
                dist[v] = w; parent[v] = u
                size = heap_push(hf, hi, size, w, v)


@nb.njit(cache=False)
def _cross(ox, oy, ax, ay, bx, by):
    return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)


@nb.njit(cache=False)
def funnel(path, npath, indptr, nbr, pa, pb, verts, cen, sx, sy, tx, ty, out):
    """simple stupid funnel(Mononen 2010 の形を移植)。門 0=出発点・門 1..m=共有辺・門 m+1=目的点。
    _cross(o,a,b) > 0 は「b が a より左回り(左)」。out に経由点を書き、点数を返す。"""
    m = npath - 1
    P = np.empty((m + 2, 4))  # (Lx, Ly, Rx, Ry)
    P[0, 0] = sx; P[0, 1] = sy; P[0, 2] = sx; P[0, 3] = sy
    for i in range(m):
        u = path[i]; v = path[i + 1]
        a = -1; b = -1
        for k in range(indptr[u], indptr[u + 1]):
            if nbr[k] == v:
                a = pa[k]; b = pb[k]; break
        ax, ay = verts[a, 0], verts[a, 1]
        bx, by = verts[b, 0], verts[b, 1]
        mx = 0.5 * (ax + bx); my = 0.5 * (ay + by)
        if _cross(cen[u, 0], cen[u, 1], mx, my, ax, ay) > 0.0:
            P[i + 1, 0] = ax; P[i + 1, 1] = ay; P[i + 1, 2] = bx; P[i + 1, 3] = by
        else:
            P[i + 1, 0] = bx; P[i + 1, 1] = by; P[i + 1, 2] = ax; P[i + 1, 3] = ay
    P[m + 1, 0] = tx; P[m + 1, 1] = ty; P[m + 1, 2] = tx; P[m + 1, 3] = ty
    n_out = 0
    out[0, 0] = sx; out[0, 1] = sy; n_out = 1
    apx = sx; apy = sy; lx = sx; ly = sy; rx = sx; ry = sy
    api = 0; li = 0; ri = 0
    i = 1
    while i < m + 2:
        nlx = P[i, 0]; nly = P[i, 1]; nrx = P[i, 2]; nry = P[i, 3]
        # 右の縁: 新しい右が内側(左回り)なら締める
        if _cross(apx, apy, rx, ry, nrx, nry) >= 0.0:
            if (apx == rx and apy == ry) or _cross(apx, apy, lx, ly, nrx, nry) < 0.0:
                rx = nrx; ry = nry; ri = i
            else:
                apx = lx; apy = ly; api = li
                if not (out[n_out - 1, 0] == apx and out[n_out - 1, 1] == apy):
                    out[n_out, 0] = apx; out[n_out, 1] = apy; n_out += 1
                lx = apx; ly = apy; rx = apx; ry = apy; li = api; ri = api
                i = api + 1
                continue
        # 左の縁: 新しい左が内側(右回り)なら締める
        if _cross(apx, apy, lx, ly, nlx, nly) <= 0.0:
            if (apx == lx and apy == ly) or _cross(apx, apy, rx, ry, nlx, nly) > 0.0:
                lx = nlx; ly = nly; li = i
            else:
                apx = rx; apy = ry; api = ri
                if not (out[n_out - 1, 0] == apx and out[n_out - 1, 1] == apy):
                    out[n_out, 0] = apx; out[n_out, 1] = apy; n_out += 1
                lx = apx; ly = apy; rx = apx; ry = apy; li = api; ri = api
                i = api + 1
                continue
        i += 1
    if not (out[n_out - 1, 0] == tx and out[n_out - 1, 1] == ty):
        out[n_out, 0] = tx; out[n_out, 1] = ty; n_out += 1
    return n_out


def centroids(verts, faces):
    return verts[faces].mean(axis=1)


class Mesh:
    def __init__(self, verts, faces):
        self.verts, self.faces = verts, faces
        self.cen = centroids(verts, faces)
        adj = build_adjacency(faces)
        self.__dict__.update(adj)
        n = faces.shape[0]
        self.g = np.zeros(n); self.parent = np.zeros(n, dtype=np.int64)
        self.closed = np.zeros(n, dtype=np.int64); self.stamp = 0
        self.hf = np.zeros(max(16, 8 * n)); self.hi = np.zeros(max(16, 8 * n), dtype=np.int64)
        self.out = np.zeros((n + 2, 2))

    def query(self, s, t, sp, tp):
        self.stamp += 1
        exp, ok = astar(self.indptr, self.nbr, self.cen, s, t, self.g, self.parent, self.closed,
                        self.stamp, self.hf, self.hi)
        if not ok:
            return exp, None
        path = [t]
        while path[-1] != s:
            path.append(int(self.parent[path[-1]]))
        path = np.asarray(path[::-1], dtype=np.int64)
        k = funnel(path, path.size, self.indptr, self.nbr, self.pa, self.pb, self.verts, self.cen,
                   sp[0], sp[1], tp[0], tp[1], self.out)
        return exp, self.out[:k].copy()


def plen(p):
    return float(np.hypot(*np.diff(p, axis=0).T).sum())


# ------------------------------------------------------------------ 検算(答えの分かる場面)
def synthetic_mesh(inside) -> tuple[np.ndarray, np.ndarray]:
    verts = {}
    faces = []
    def vid(x, y):
        if (x, y) not in verts:
            verts[(x, y)] = len(verts)
        return verts[(x, y)]
    for x in range(10):
        for y in range(10):
            if inside(x + 0.5, y + 0.5):
                a, b, c, d = vid(x, y), vid(x + 1, y), vid(x + 1, y + 1), vid(x, y + 1)
                faces += [(a, b, c), (a, c, d)]
    V = np.zeros((len(verts), 2))
    for (x, y), i in verts.items():
        V[i] = (x, y)
    return V, np.asarray(faces, dtype=np.int64)


def locate(mesh, p):
    """点を含む三角形(総当たり・検算用)。"""
    v = mesh.verts[mesh.faces]
    a, b, c = v[:, 0], v[:, 1], v[:, 2]
    def cr(o, q):
        return (q[:, 0] - o[:, 0]) * (p[1] - o[:, 1]) - (q[:, 1] - o[:, 1]) * (p[0] - o[:, 0])
    s1, s2, s3 = cr(a, b), cr(b, c), cr(c, a)
    ins = ((s1 >= 0) & (s2 >= 0) & (s3 >= 0)) | ((s1 <= 0) & (s2 <= 0) & (s3 <= 0))
    idx = np.flatnonzero(ins)
    return int(idx[0])


def self_check() -> dict:
    """検算。(A) 通路が一意(幅 1 の帯=双対グラフが一本道)なら funnel は解析解と一致するはず。
    (B) 通路が一意でない広い面では、重心間 A* が選ぶ通路が最短の通路と限らない=その差を報告だけする
    (Path-Finder の README が「最適は保証しない」と書く性質・JuPedSim の TA* は複数候補の funnel 長で選び直す)。"""
    res = {"funnel_exact_when_corridor_unique": {}, "centroid_astar_gap_on_open_meshes": {}}
    cases_a = {
        # 幅 1 の直線の帯: (0.5,0.3)→(9.5,0.8) は直線
        "strip": (lambda x, y: y < 1, (0.5, 0.3), (9.5, 0.8), math.hypot(9.0, 0.5)),
        # 幅 1 の L 字: 角 (1,1) を回る
        "L_width1": (lambda x, y: x < 1 or y < 1, (0.5, 9.5), (9.5, 0.5),
                     math.hypot(0.5, 8.5) + math.hypot(8.5, 0.5)),
        # 幅 1 の U 字(外周の帯): 角 (1,1)・(9,1) を回る
        "U_width1": (lambda x, y: x < 1 or y < 1 or x > 9, (0.5, 9.5), (9.5, 9.5),
                     math.hypot(0.5, 8.5) * 2 + 8.0),
    }
    ok = True
    for name, (inside, s, t, exact) in cases_a.items():
        V, F = synthetic_mesh(inside)
        m = Mesh(V, F)
        s, t = np.asarray(s, float), np.asarray(t, float)
        _, p = m.query(locate(m, s), locate(m, t), s, t)
        d = plen(p)
        res["funnel_exact_when_corridor_unique"][name] = dict(
            funnel_len=round(d, 9), exact=round(exact, 9), points=p.round(3).tolist())
        ok = ok and abs(d - exact) < 1e-9
    cases_b = {
        "open_square": (lambda x, y: True, (0.3, 0.7), (9.6, 8.2), math.hypot(9.3, 7.5)),
        "L_width2": (lambda x, y: x < 2 or y < 2, (1.0, 9.0), (9.0, 1.0), 2 * math.hypot(1, 7)),
        "U_open": (lambda x, y: not (3 < x < 7 and y > 3), (1.5, 9.0), (8.5, 9.0),
                   2 * math.hypot(1.5, 6) + 4),
    }
    for name, (inside, s, t, exact) in cases_b.items():
        V, F = synthetic_mesh(inside)
        m = Mesh(V, F)
        s, t = np.asarray(s, float), np.asarray(t, float)
        _, p = m.query(locate(m, s), locate(m, t), s, t)
        res["centroid_astar_gap_on_open_meshes"][name] = dict(
            funnel_len=round(plen(p), 6), exact=round(exact, 6), ratio=round(plen(p) / exact, 4))
    res["all_ok"] = ok
    return res


# ------------------------------------------------------------------ 本計測
def mesh_stats(verts, faces, zc=None):
    v = verts[faces]
    area = 0.5 * np.abs((v[:, 1, 0] - v[:, 0, 0]) * (v[:, 2, 1] - v[:, 0, 1])
                        - (v[:, 2, 0] - v[:, 0, 0]) * (v[:, 1, 1] - v[:, 0, 1]))
    el = np.concatenate([np.hypot(*(v[:, 1] - v[:, 0]).T), np.hypot(*(v[:, 2] - v[:, 1]).T),
                         np.hypot(*(v[:, 0] - v[:, 2]).T)])
    return dict(n_tri=int(faces.shape[0]), n_vert=int(verts.shape[0]), area_m2=round(float(area.sum()), 1),
                tri_area_m2_p5_p50_p95=np.percentile(area, [5, 50, 95]).round(3).tolist(),
                edge_len_m_p5_p50_p95=np.percentile(el, [5, 50, 95]).round(3).tolist())


def time_queries(mesh, comp, rng, n_q, window=None):
    """出発と目的は同じ連結成分から選ぶ。窓があるときは「窓の中に三角形が最も多い成分」の、窓の中の三角形から
    (経路は窓の外へ出てよい)。"""
    if window is None:
        big = int(np.bincount(comp).argmax())
        cand = np.flatnonzero(comp == big)
    else:
        (x0, y0, x1, y1) = window
        c = mesh.cen
        inw = np.flatnonzero((c[:, 0] >= x0) & (c[:, 0] < x1) & (c[:, 1] >= y0) & (c[:, 1] < y1))
        big = int(np.bincount(comp[inw]).argmax())
        cand = inw[comp[inw] == big]
    ss = rng.choice(cand, n_q); tt = rng.choice(cand, n_q)
    mesh.query(ss[0], tt[0], mesh.cen[ss[0]], mesh.cen[tt[0]])  # JIT を温める
    times, exps, lens, straight, npts = [], [], [], [], []
    for s, t in zip(ss, tt):
        t0 = time.perf_counter()
        exp, p = mesh.query(int(s), int(t), mesh.cen[s], mesh.cen[t])
        times.append((time.perf_counter() - t0) * 1e3)
        exps.append(exp)
        if p is not None:
            lens.append(plen(p)); straight.append(float(np.hypot(*(mesh.cen[t] - mesh.cen[s]))))
            npts.append(len(p))
    times = np.asarray(times); exps = np.asarray(exps)
    lens = np.asarray(lens); straight = np.asarray(straight)
    detour = lens[straight > 1] / straight[straight > 1]
    return dict(n_queries=n_q, n_candidate_tri=int(cand.size), component_size=int((comp == big).sum()),
                ms_p50_p95_max=np.percentile(times, [50, 95, 100]).round(4).tolist(),
                ms_mean=round(float(times.mean()), 4),
                expanded_p50_p95=np.percentile(exps, [50, 95]).astype(int).tolist(),
                path_len_m_p50_p95=np.percentile(lens, [50, 95]).round(1).tolist(),
                detour_ratio_p50_p95=np.percentile(detour, [50, 95]).round(3).tolist(),
                waypoints_p50_p95=np.percentile(npts, [50, 95]).astype(int).tolist())


def determinism_check(mesh, comp, rng_seed):
    rng = np.random.default_rng(rng_seed)
    big = np.bincount(comp).argmax(); cand = np.flatnonzero(comp == big)
    ss = rng.choice(cand, 200); tt = rng.choice(cand, 200)
    runs = []
    for _ in range(2):
        acc = []
        for s, t in zip(ss, tt):
            _, p = mesh.query(int(s), int(t), mesh.cen[s], mesh.cen[t])
            acc.append(p.tobytes() if p is not None else b"")
        runs.append(acc)
    return all(a == b for a, b in zip(*runs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-queries", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=59)
    args = ap.parse_args()
    out_path = Path(args.out)
    if out_path.exists():
        raise FileExistsError(out_path)
    rep = {"script": "docs/research/r59/measure_navmesh.py", "numba": nb.__version__, "numpy": np.__version__}
    t0 = time.perf_counter(); rep["self_check"] = self_check()
    rep["self_check_s"] = round(time.perf_counter() - t0, 2)
    assert rep["self_check"]["all_ok"], rep["self_check"]

    rng = np.random.default_rng(args.seed)
    variants = (("sidewalk_2000", (2000,)),
                ("sidewalk_intersection_island", (2000, 1020, 3000)),
                ("all_tran_1000_1020_2000_3000", (1000, 1020, 2000, 3000)))
    for label, codes in variants:
        tri_q, cls, pz = load_triangles(codes)
        block = {"function_codes": list(codes), "n_unique_tri_before_weld": int(tri_q.shape[0])}
        weld_sweep = {}
        for tol in (0.05, 0.10, 0.20, 0.50):
            verts, faces = weld(tri_q, tol)
            t1 = time.perf_counter(); adj = build_adjacency(faces); tb = time.perf_counter() - t1
            comp, nc = components(adj["indptr"], adj["nbr"], faces.shape[0])
            sizes = np.sort(np.bincount(comp))[::-1]
            weld_sweep[f"{tol:.2f}"] = dict(
                n_tri=int(faces.shape[0]), n_components=int(nc),
                largest_component_share=round(float(sizes[0] / faces.shape[0]), 4),
                top5_component_sizes=sizes[:5].tolist(),
                n_edge_interior=adj["n_interior"], n_edge_boundary=adj["n_boundary"],
                n_edge_nonmanifold=adj["n_nonmanifold"], adjacency_build_s=round(tb, 2))
        block["weld_sweep"] = weld_sweep
        # 以降は 0.10 m 溶接で測る(expedient: 量子化 0.05 m の 2 倍)
        verts, faces = weld(tri_q, 0.10)
        block["stats_weld_0.10"] = mesh_stats(verts, faces)
        t1 = time.perf_counter(); mesh = Mesh(verts, faces); block["mesh_build_s"] = round(time.perf_counter() - t1, 2)
        comp, _ = components(mesh.indptr, mesh.nbr, faces.shape[0])
        cx, cy = mesh.cen[:, 0], mesh.cen[:, 1]
        block["extent_m"] = [round(float(cx.min()), 1), round(float(cy.min()), 1),
                             round(float(cx.max()), 1), round(float(cy.max()), 1)]
        block["query_window_200m"] = time_queries(mesh, comp, rng, args.n_queries, (-100, -100, 100, 100))
        block["query_full"] = time_queries(mesh, comp, rng, args.n_queries)
        block["deterministic_repeat_200"] = determinism_check(mesh, comp, args.seed)
        # 距離場(目的地 1 つ → 全三角形)
        n = faces.shape[0]
        dist = np.zeros(n); par = np.zeros(n, dtype=np.int64)
        dijkstra_all(mesh.indptr, mesh.nbr, mesh.cen, 0, dist, par, mesh.hf, mesh.hi)
        ts = []
        for t in rng.choice(n, 20):
            t1 = time.perf_counter()
            dijkstra_all(mesh.indptr, mesh.nbr, mesh.cen, int(t), dist, par, mesh.hf, mesh.hi)
            ts.append((time.perf_counter() - t1) * 1e3)
        block["distance_field_one_target_ms_p50_max"] = np.percentile(ts, [50, 100]).round(2).tolist()
        block["distance_field_bytes_per_target"] = dict(float32_dist=4 * n, int32_nexthop=4 * n,
                                                         both=8 * n)
        block["all_pairs_nexthop_bytes_int32"] = 4 * n * n
        rep[label] = block
    out_path.write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
