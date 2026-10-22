"""build.space.raster — 歩ける面の格子(0.5 m)に多角形・帯・三角形を塗る numba の部品(段 1・SR13=自前・依存を足さない)。

格子の約束: 原点 ``(ox, oy)``・目 ``res`` [m]・列 ``i``(東)・行 ``j``(北)。目 (i, j) は
``[ox+i·res, ox+(i+1)·res) × [oy+j·res, oy+(j+1)·res)`` で、**目の中心が図形の中にあるとき**塗る(境界の扱いは
中心の内外=決定論・浮動小数は float64)。配列は ``[j, i]``(行, 列)。

部品(どれも配列を受けて書き換える・返り値は塗った目の数):

- :func:`fill_polygon`: 多角形(外周と穴の辺を全部渡す=偶奇の走査線)。
- :func:`fill_capsule`: 線分から ``half_w`` 以内(端は丸い=折れ線は線分ごとに呼べば継ぎ目も丸い)。
- :func:`fill_triangles_z`: 三角形の中の目に重心座標で高さを書く(DEM の TIN・デッキの上面)。
- :func:`edt_inside`: 印の目から印の無い目までの距離[m](Felzenszwalb の二乗距離の変換を行と列に 2 回)。
- :func:`bfs_nearest_label`: 種の札を許す目の中で 4 近傍に広げる(最も近い種の札=道の種類の写し)。

逐次ループ宣言(P4): どれも構築の 1 回だけ(ランには入らない)。図形の数 × 外接矩形の目の数のループ(numba)。
"""

from __future__ import annotations

import math

import numba as nb
import numpy as np

__all__ = [
    "Grid",
    "fill_polygon",
    "fill_capsule",
    "fill_triangles_z",
    "edt_inside",
    "bfs_nearest_label",
    "MODE_IF_ZERO",
    "MODE_ALWAYS",
]

#: 書き方: 0 の目にだけ書く(先に書いたものが勝つ=出どころの優先順)。
MODE_IF_ZERO = 0
#: 書き方: いつも書く。
MODE_ALWAYS = 1


class Grid:
    """格子の原点・目・大きさ(``nx`` 列 × ``ny`` 行)。原点は ``res`` の倍数に丸めて置く(階をまたいで目がそろう)。"""

    __slots__ = ("ox", "oy", "res", "nx", "ny")

    def __init__(self, ox: float, oy: float, res: float, nx: int, ny: int) -> None:
        self.ox = float(ox)
        self.oy = float(oy)
        self.res = float(res)
        self.nx = int(nx)
        self.ny = int(ny)

    @classmethod
    def covering(cls, x0: float, y0: float, x1: float, y1: float, res: float) -> "Grid":
        """``[x0, x1) × [y0, y1)`` を覆う格子(原点は ``res`` の倍数に下へ丸める)。"""
        ox = math.floor(x0 / res) * res
        oy = math.floor(y0 / res) * res
        nx = int(math.ceil((x1 - ox) / res))
        ny = int(math.ceil((y1 - oy) / res))
        return cls(ox, oy, res, nx, ny)

    def as_tuple(self) -> tuple[float, float, float, int, int]:
        return (self.ox, self.oy, self.res, self.nx, self.ny)

    def col_of(self, x: float) -> int:
        return int(math.floor((x - self.ox) / self.res))

    def row_of(self, y: float) -> int:
        return int(math.floor((y - self.oy) / self.res))


@nb.njit(cache=True)
def fill_polygon(out, ox, oy, res, ex0, ey0, ex1, ey1, value, mode, allow):
    """偶奇の走査線で多角形を塗る。``allow`` が空(長さ 0)でなければ ``allow[j, i] != 0`` の目だけ。"""
    ny, nx = out.shape
    ne = ex0.shape[0]
    if ne == 0:
        return 0
    ymin = min(ey0.min(), ey1.min())
    ymax = max(ey0.max(), ey1.max())
    j0 = max(0, int(math.floor((ymin - oy) / res - 0.5)))
    j1 = min(ny - 1, int(math.ceil((ymax - oy) / res - 0.5)))
    xs = np.empty(ne, dtype=np.float64)
    use_allow = allow.shape[0] > 0
    n = 0
    for j in range(j0, j1 + 1):
        yc = oy + (j + 0.5) * res
        k = 0
        for e in range(ne):
            ya = ey0[e]
            yb = ey1[e]
            if (ya <= yc < yb) or (yb <= yc < ya):
                xs[k] = ex0[e] + (yc - ya) * (ex1[e] - ex0[e]) / (yb - ya)
                k += 1
        if k < 2:
            continue
        xk = np.sort(xs[:k])
        for p in range(0, k - 1, 2):
            xa = xk[p]
            xb = xk[p + 1]
            i0 = max(0, int(math.ceil((xa - ox) / res - 0.5)))
            i1 = min(nx - 1, int(math.floor((xb - ox) / res - 0.5)))
            for i in range(i0, i1 + 1):
                if use_allow and allow[j, i] == 0:
                    continue
                if mode == 0 and out[j, i] != 0:
                    continue
                out[j, i] = value
                n += 1
    return n


@nb.njit(cache=True)
def fill_capsule(out, ox, oy, res, x0, y0, x1, y1, half_w, value, mode, allow):
    """線分 (x0,y0)-(x1,y1) から ``half_w`` 以内の目を塗る。``allow`` は :func:`fill_polygon` と同じ。"""
    ny, nx = out.shape
    i0 = max(0, int(math.floor((min(x0, x1) - half_w - ox) / res)))
    i1 = min(nx - 1, int(math.floor((max(x0, x1) + half_w - ox) / res)))
    j0 = max(0, int(math.floor((min(y0, y1) - half_w - oy) / res)))
    j1 = min(ny - 1, int(math.floor((max(y0, y1) + half_w - oy) / res)))
    dx = x1 - x0
    dy = y1 - y0
    L2 = dx * dx + dy * dy
    hw2 = half_w * half_w
    use_allow = allow.shape[0] > 0
    n = 0
    for j in range(j0, j1 + 1):
        yc = oy + (j + 0.5) * res
        for i in range(i0, i1 + 1):
            xc = ox + (i + 0.5) * res
            if L2 > 0.0:
                t = ((xc - x0) * dx + (yc - y0) * dy) / L2
                if t < 0.0:
                    t = 0.0
                elif t > 1.0:
                    t = 1.0
            else:
                t = 0.0
            px = x0 + t * dx - xc
            py = y0 + t * dy - yc
            if px * px + py * py > hw2:
                continue
            if use_allow and allow[j, i] == 0:
                continue
            if mode == 0 and out[j, i] != 0:
                continue
            out[j, i] = value
            n += 1
    return n


@nb.njit(cache=True)
def fill_triangles_z(zout, ox, oy, res, tri, keep_max):
    """三角形 ``tri`` (n, 3, 3)=(x, y, z) の中の目に重心座標の高さを書く。``keep_max`` なら既にある値と大きい方。

    ``zout`` の未設定は NaN。返り値は書いた目の数。
    """
    ny, nx = zout.shape
    n = 0
    for t in range(tri.shape[0]):
        ax = tri[t, 0, 0]; ay = tri[t, 0, 1]; az = tri[t, 0, 2]
        bx = tri[t, 1, 0]; by = tri[t, 1, 1]; bz = tri[t, 1, 2]
        cx = tri[t, 2, 0]; cy = tri[t, 2, 1]; cz = tri[t, 2, 2]
        det = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if det == 0.0:
            continue
        i0 = max(0, int(math.floor((min(ax, bx, cx) - ox) / res - 0.5)))
        i1 = min(nx - 1, int(math.ceil((max(ax, bx, cx) - ox) / res - 0.5)))
        j0 = max(0, int(math.floor((min(ay, by, cy) - oy) / res - 0.5)))
        j1 = min(ny - 1, int(math.ceil((max(ay, by, cy) - oy) / res - 0.5)))
        for j in range(j0, j1 + 1):
            yc = oy + (j + 0.5) * res
            for i in range(i0, i1 + 1):
                xc = ox + (i + 0.5) * res
                l1 = ((by - cy) * (xc - cx) + (cx - bx) * (yc - cy)) / det
                l2 = ((cy - ay) * (xc - cx) + (ax - cx) * (yc - cy)) / det
                l3 = 1.0 - l1 - l2
                if l1 < -1e-12 or l2 < -1e-12 or l3 < -1e-12:
                    continue
                z = l1 * az + l2 * bz + l3 * cz
                cur = zout[j, i]
                if keep_max and not math.isnan(cur) and cur >= z:
                    continue
                zout[j, i] = z
                n += 1
    return n


@nb.njit(cache=True)
def _dt1d(f, n, d, v, z):
    """Felzenszwalb & Huttenlocher の 1 次元の二乗距離の変換(``f`` → ``d``)。"""
    k = 0
    v[0] = 0
    z[0] = -np.inf
    z[1] = np.inf
    for q in range(1, n):
        p = v[k]
        s = ((f[q] + q * q) - (f[p] + p * p)) / (2.0 * q - 2.0 * p)
        while s <= z[k]:
            k -= 1
            p = v[k]
            s = ((f[q] + q * q) - (f[p] + p * p)) / (2.0 * q - 2.0 * p)
        k += 1
        v[k] = q
        z[k] = s
        z[k + 1] = np.inf
    k = 0
    for q in range(n):
        while z[k + 1] < q:
            k += 1
        p = v[k]
        d[q] = (q - p) * (q - p) + f[p]


@nb.njit(cache=True)
def edt_inside(mask, res):
    """``mask != 0`` の目から ``mask == 0`` の目(の中心)までの距離[m](float32・印の無い目は 0)。

    印の無い目が 1 つも無い行と列は大きな値(1e15 の平方根)になる。
    """
    ny, nx = mask.shape
    big = 1e30
    g = np.empty((ny, nx), dtype=np.float64)
    m = max(nx, ny)
    f = np.empty(m, dtype=np.float64)
    d = np.empty(m, dtype=np.float64)
    v = np.empty(m, dtype=np.int64)
    z = np.empty(m + 1, dtype=np.float64)
    for i in range(nx):
        for j in range(ny):
            f[j] = big if mask[j, i] != 0 else 0.0
        _dt1d(f, ny, d, v, z)
        for j in range(ny):
            g[j, i] = d[j]
    out = np.empty((ny, nx), dtype=np.float32)
    for j in range(ny):
        for i in range(nx):
            f[i] = g[j, i]
        _dt1d(f, nx, d, v, z)
        for i in range(nx):
            out[j, i] = math.sqrt(min(d[i], 1e30)) * res
    return out


@nb.njit(cache=True)
def bfs_nearest_label(seed, allow):
    """``seed`` の 0 でない札を ``allow != 0`` の目の中で 4 近傍に広げる(先に届いた札が勝つ=幅優先・同じ段は行列の順)。

    返り値は札の配列(int16・届かない目は 0)と到達の段数(int32・届かない目は -1)。
    """
    ny, nx = seed.shape
    lab = np.zeros((ny, nx), dtype=np.int16)
    dist = np.full((ny, nx), -1, dtype=np.int32)
    q = np.empty(ny * nx, dtype=np.int64)
    head = 0
    tail = 0
    for j in range(ny):
        for i in range(nx):
            if seed[j, i] != 0 and allow[j, i] != 0:
                lab[j, i] = seed[j, i]
                dist[j, i] = 0
                q[tail] = j * nx + i
                tail += 1
    while head < tail:
        c = q[head]
        head += 1
        j = c // nx
        i = c - j * nx
        dd = dist[j, i] + 1
        lb = lab[j, i]
        if i > 0 and allow[j, i - 1] != 0 and dist[j, i - 1] < 0:
            dist[j, i - 1] = dd; lab[j, i - 1] = lb; q[tail] = c - 1; tail += 1
        if i < nx - 1 and allow[j, i + 1] != 0 and dist[j, i + 1] < 0:
            dist[j, i + 1] = dd; lab[j, i + 1] = lb; q[tail] = c + 1; tail += 1
        if j > 0 and allow[j - 1, i] != 0 and dist[j - 1, i] < 0:
            dist[j - 1, i] = dd; lab[j - 1, i] = lb; q[tail] = c - nx; tail += 1
        if j < ny - 1 and allow[j + 1, i] != 0 and dist[j + 1, i] < 0:
            dist[j + 1, i] = dd; lab[j + 1, i] = lb; q[tail] = c + nx; tail += 1
    return lab, dist


def polygon_edges(rings: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """環(外周と穴・閉じていてもいなくてもよい)の並び → 辺の 4 配列(:func:`fill_polygon` の入力)。"""
    xs0, ys0, xs1, ys1 = [], [], [], []
    for r in rings:
        a = np.asarray(r, dtype=np.float64)
        if a.shape[0] < 3:
            continue
        b = np.roll(a, -1, axis=0)
        xs0.append(a[:, 0]); ys0.append(a[:, 1]); xs1.append(b[:, 0]); ys1.append(b[:, 1])
    if not xs0:
        e = np.zeros(0, dtype=np.float64)
        return e, e, e, e
    return np.concatenate(xs0), np.concatenate(ys0), np.concatenate(xs1), np.concatenate(ys1)


NO_ALLOW = np.zeros((0, 0), dtype=np.uint8)
