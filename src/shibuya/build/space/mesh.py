"""build.space.mesh — 塗った格子 → ラン・門・帯(ナビメッシュの形・numba・SR13=自前)。

- **ラン**: 行ごとの歩ける目の連なり(横 1 行の長方形=凸)。``(行, 列の始まり x0, 列の終わり x1)``。
- **門**: 行 j のランと行 j+1 のランが列で重なる区間(長さ > 0)。境の y は ``oy + (j+1)·res``。
- **帯**: 上下に 1 対 1 でつながるランの縦の鎖(A* の節)。分かれ目・合わさり目で帯が切れる。

決定論: ランは (行, 列) の順・門は (下のラン, 上のラン) の順・帯の番号は最初のランの順。

逐次ループ宣言(P4): 構築の 1 回だけ(行 × ランの数ぶんの numba のループ)。
"""

from __future__ import annotations

import numba as nb
import numpy as np

__all__ = ["extract_runs", "run_overlaps", "build_strips", "union_find_components", "nearest_point_in_comp"]


@nb.njit(cache=True)
def _count_runs(label):
    ny, nx = label.shape
    n = 0
    for j in range(ny):
        prev = False
        for i in range(nx):
            cur = label[j, i] != 0
            if cur and not prev:
                n += 1
            prev = cur
    return n


@nb.njit(cache=True)
def extract_runs(label, n_codes):
    """``label != 0`` の行ごとの連なり → (行, x0, x1, 最も多い札) の 4 配列と、行ごとの頭の索引 ``row_ptr`` (ny+1)。"""
    ny, nx = label.shape
    n = _count_runs(label)
    row = np.empty(n, dtype=np.int32)
    x0 = np.empty(n, dtype=np.int32)
    x1 = np.empty(n, dtype=np.int32)
    src = np.empty(n, dtype=np.uint8)
    row_ptr = np.zeros(ny + 1, dtype=np.int64)
    cnt = np.zeros(n_codes, dtype=np.int64)
    k = 0
    for j in range(ny):
        row_ptr[j] = k
        i = 0
        while i < nx:
            if label[j, i] == 0:
                i += 1
                continue
            s = i
            for c in range(n_codes):
                cnt[c] = 0
            while i < nx and label[j, i] != 0:
                c = label[j, i]
                if c < n_codes:
                    cnt[c] += 1
                i += 1
            best = 1
            for c in range(1, n_codes):
                if cnt[c] > cnt[best]:
                    best = c
            row[k] = j
            x0[k] = s
            x1[k] = i
            src[k] = best
            k += 1
    row_ptr[ny] = k
    return row, x0, x1, src, row_ptr


@nb.njit(cache=True)
def run_overlaps(row_ptr, x0, x1):
    """行 j と j+1 のランの重なり → (下のラン, 上のラン, 重なりの x0, 重なりの x1) の 4 配列(列の単位)。"""
    ny = row_ptr.shape[0] - 1
    # 数える
    n = 0
    for j in range(ny - 1):
        a = row_ptr[j]
        b = row_ptr[j + 1]
        c = row_ptr[j + 1]
        d = row_ptr[j + 2]
        p = a
        q = c
        while p < b and q < d:
            lo = max(x0[p], x0[q])
            hi = min(x1[p], x1[q])
            if hi > lo:
                n += 1
            if x1[p] < x1[q]:
                p += 1
            else:
                q += 1
    lo_r = np.empty(n, dtype=np.int32)
    hi_r = np.empty(n, dtype=np.int32)
    ox0 = np.empty(n, dtype=np.int32)
    ox1 = np.empty(n, dtype=np.int32)
    k = 0
    for j in range(ny - 1):
        a = row_ptr[j]
        b = row_ptr[j + 1]
        c = row_ptr[j + 1]
        d = row_ptr[j + 2]
        p = a
        q = c
        while p < b and q < d:
            lo = max(x0[p], x0[q])
            hi = min(x1[p], x1[q])
            if hi > lo:
                lo_r[k] = p
                hi_r[k] = q
                ox0[k] = lo
                ox1[k] = hi
                k += 1
            if x1[p] < x1[q]:
                p += 1
            else:
                q += 1
    return lo_r, hi_r, ox0, ox1


@nb.njit(cache=True)
def build_strips(n_runs, lo_r, hi_r):
    """1 対 1 でつながるランの縦の鎖 → ランごとの帯の番号(最初のランの順)と、帯をまたぐ門の印。"""
    up = np.zeros(n_runs, dtype=np.int32)
    down = np.zeros(n_runs, dtype=np.int32)
    up_to = np.full(n_runs, -1, dtype=np.int64)
    for k in range(lo_r.shape[0]):
        up[lo_r[k]] += 1
        down[hi_r[k]] += 1
        up_to[lo_r[k]] = hi_r[k]
    strip = np.full(n_runs, -1, dtype=np.int32)
    s = 0
    for r in range(n_runs):
        if strip[r] >= 0:
            continue
        strip[r] = s
        cur = r
        while up[cur] == 1:
            nxt = up_to[cur]
            if down[nxt] != 1 or strip[nxt] >= 0:
                break
            strip[nxt] = s
            cur = nxt
        s += 1
    cross = np.empty(lo_r.shape[0], dtype=np.bool_)
    for k in range(lo_r.shape[0]):
        cross[k] = strip[lo_r[k]] != strip[hi_r[k]]
    return strip, s, cross


@nb.njit(cache=True)
def _find(parent, a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


@nb.njit(cache=True)
def union_find_components(n, ea, eb):
    """節 n 個・辺 (ea, eb) → 連結成分の番号(各成分の最小の節の番号を代表=決定論)。"""
    parent = np.arange(n)
    for k in range(ea.shape[0]):
        a = _find(parent, ea[k])
        b = _find(parent, eb[k])
        if a != b:
            if a < b:
                parent[b] = a
            else:
                parent[a] = b
    comp = np.empty(n, dtype=np.int64)
    for i in range(n):
        comp[i] = _find(parent, i)
    return comp


@nb.njit(cache=True)
def nearest_point_in_comp(row_ptr, x0, x1, run_comp, ox, oy, ny, res, x, y, rmax, comp):
    """1 つの階の格子で、成分 ``comp`` のランの中の (x, y) に最も近い点(:func:`world.navmesh.nearest_point` と同じ寄せ方)。"""
    eps = res * 1e-3
    j0 = max(0, int(np.floor((y - rmax - oy) / res)))
    j1 = min(ny - 1, int(np.floor((y + rmax - oy) / res)))
    best = -1
    bd = np.inf
    bx = x
    by = y
    for j in range(j0, j1 + 1):
        ylo = oy + j * res + eps
        yhi = oy + (j + 1) * res - eps
        py = min(max(y, ylo), yhi)
        dy = py - y
        if abs(dy) > bd:
            continue
        for r in range(row_ptr[j], row_ptr[j + 1]):
            if run_comp[r] != comp:
                continue
            xlo = ox + x0[r] * res + eps
            xhi = ox + x1[r] * res - eps
            px = min(max(x, xlo), xhi)
            dx = px - x
            d = np.sqrt(dx * dx + dy * dy)
            if d < bd:
                bd = d
                best = r
                bx = px
                by = py
    if best < 0 or bd > rmax:
        return -1, x, y, np.inf
    return best, bx, by, bd
