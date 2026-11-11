"""engine.spatial_index — 近傍の索引(第 2 期 2-2 段 11a・セル廃止の役割 ①「近傍の索引」の最初の部品)。

口: :class:`SpatialIndex`(``build(xy, band)``・``within(i, d)``・``query_many``・``pairs(d)``・B5 の単位の在室)。
層(``band``)ごとの格子(既定 2.5 m=知覚契約の可視性格子と同じ幅)に体を割り当て、格子の鍵の順に並べた配列を
``searchsorted`` で引く。刻みごとに作って捨てる(``TickScratch.near_index``・状態台帳の行 ``PX0``)。空間の段 1・2
(位置は (x, y, 階))でもそのまま使える(層を階に読み替える)。

距離は float64 の ``sqrt(dx² + dy²) ≤ d``(``engine.resolve.talk_within_reach`` と同じ比べ方・境を含む)。索引の配列は
組み立ての後は読むだけ(``setflags(write=False)``・属性の付け替えも断る)。

先例: 近接の読み直しの計器 ``docs/bench/analysis/proximity-edge-2026-09-30/proximity_measure.py`` の ``pairs_within``
(格子+``searchsorted``)を口にしたもの。scipy の cKDTree は依存に無い(足すには許可が要る)。

逐次ループ宣言(P4): なし(近傍は x の行ごとの 2r+1 個の範囲の ``searchsorted``=定数回・体数に比例する Python の
ループは無い)。
"""

from __future__ import annotations

import functools
import math
from typing import Any, Final

import numpy as np

__all__ = ["INDEX_CELL_M", "SpatialIndex", "expand_ranges"]

#: 近傍の索引の格子の幅[m](知覚契約の可視性格子と同じ幅・expedient=宣言は ``engine.proximity`` の見出し)。
INDEX_CELL_M: Final[float] = 2.5

_SHIFT: Final[int] = 1 << 21
_ROW: Final[int] = 1 << 22
_BAND_STRIDE: Final[int] = 1 << 44
#: 格子の番号の余白(近傍の行の範囲 ±r が隣の行・層へはみ出さない=r ≤ 1,024 格子=2.5 km まで)。
_MARGIN: Final[int] = 1 << 10


def _grid_keys(x: np.ndarray, y: np.ndarray, band: np.ndarray, cell_m: float) -> np.ndarray:
    gx = np.floor(x / cell_m).astype(np.int64) + _SHIFT
    gy = np.floor(y / cell_m).astype(np.int64) + _SHIFT
    lo, hi = _MARGIN, _ROW - _MARGIN
    if gx.size and (int(gx.min()) < lo or int(gx.max()) >= hi or int(gy.min()) < lo or int(gy.max()) >= hi):
        raise ValueError("近傍の索引: 座標が格子の範囲の外(±5,000 km 級)")
    return (np.asarray(band, dtype=np.int64) + 2) * _BAND_STRIDE + gx * _ROW + gy


@functools.lru_cache(maxsize=64)
def _row_spans(r: int, *, half: bool) -> tuple[np.ndarray, np.ndarray]:
    """格子の近傍を「x の行ごとの y の連続した範囲」で表した鍵の差 (下端, 上端)(両端を含む)。

    同じ層・同じ x の格子の鍵は y の順に連続する(鍵=層 × 2^44 + x × 2^22 + y)=近傍の (2r+1)² 個の格子を 2r+1 個の
    範囲で引ける。``half``=前向きの半分(x が同じ行は y が自分より上だけ・自分の格子は呼び手が別に数える)=組を 1 回ずつ。
    半径ごとに 1 回だけ作る(読むだけ)。
    """
    if not 0 < r <= _MARGIN:
        raise ValueError(f"近傍の索引: 半径の格子の数は 1〜{_MARGIN}(いま {r})")
    dx = np.arange(0 if half else -r, r + 1, dtype=np.int64)
    lo = dx * _ROW - r
    hi = dx * _ROW + r
    if half:
        lo[0] = 1  # x が同じ行は y が 1〜r だけ
    lo.setflags(write=False)
    hi.setflags(write=False)
    return lo, hi


def expand_ranges(lo: np.ndarray, hi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """範囲 ``[lo, hi)`` の並び → (範囲の番号, 位置)(``np.repeat`` の形・ループなし)。"""
    cnt = np.maximum(hi - lo, 0)
    s = int(cnt.sum())
    if s == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    which = np.repeat(np.arange(cnt.size, dtype=np.int64), cnt)
    first = np.cumsum(cnt) - cnt
    pos = np.repeat(lo, cnt) + (np.arange(s, dtype=np.int64) - np.repeat(first, cnt))
    return which, pos


def _frozen(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a)
    a.setflags(write=False)
    return a


class SpatialIndex:
    """近傍の索引(層ごとの ``cell_m`` の格子・刻みごとに作って捨てる・組み立ての後は読むだけ)。

    ``ids``(索引に入れた体)を格子の鍵の順に並べた配列と、その座標・層・B5 の単位を持つ。
    """

    __slots__ = ("cell_m", "ids", "x", "y", "bands", "unit", "key", "pos", "_u_sorted", "_u_ids")

    def __init__(self, cell_m: float, ids: np.ndarray, x: np.ndarray, y: np.ndarray, band: np.ndarray,
                 unit: np.ndarray, key: np.ndarray, pos: np.ndarray) -> None:
        u_order = np.argsort(unit, kind="stable")
        for name, val in (("cell_m", float(cell_m)), ("ids", _frozen(ids)), ("x", _frozen(x)), ("y", _frozen(y)),
                          ("bands", _frozen(band)), ("unit", _frozen(unit)), ("key", _frozen(key)),
                          ("pos", _frozen(pos)), ("_u_sorted", _frozen(unit[u_order])),
                          ("_u_ids", _frozen(ids[u_order]))):  # 逐次: 欄の数ぶん(10)
            object.__setattr__(self, name, val)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"近傍の索引の欄 {name} は付け替えられない(刻みごとに作り直す)")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"近傍の索引の欄 {name} は消せない")

    @classmethod
    def build(cls, xy: Any, band: Any, ids: Any = None, *, unit: Any = None, n_total: int | None = None,
              cell_m: float = INDEX_CELL_M) -> "SpatialIndex":
        """``xy`` ``(n, 2)``・``band`` ``(n,)``(全体の配列)のうち ``ids`` の体で索引を作る(``ids`` 省略=全員)。

        ``unit``=B5 の単位(``(n,)``・−1=単位なし。省略=全員なし)。``n_total``=体の id の上限(``pos`` の大きさ)。
        """
        xy_all = np.asarray(xy)
        n_all = int(xy_all.shape[0]) if n_total is None else int(n_total)
        sel = np.arange(xy_all.shape[0], dtype=np.int64) if ids is None else np.asarray(ids, dtype=np.int64)
        x = np.asarray(xy_all[sel, 0], dtype=np.float64)
        y = np.asarray(xy_all[sel, 1], dtype=np.float64)
        bd = np.asarray(band)[sel].astype(np.int64)
        un = (np.full(sel.size, -1, dtype=np.int64) if unit is None
              else np.asarray(unit)[sel].astype(np.int64))
        key = _grid_keys(x, y, bd, float(cell_m))
        order = np.argsort(key, kind="stable")
        ids_s = sel[order]
        pos = np.full(n_all, -1, dtype=np.int64)
        pos[ids_s] = np.arange(ids_s.size, dtype=np.int64)
        return cls(float(cell_m), ids_s, x[order], y[order], bd[order], un[order], key[order], pos)

    def __len__(self) -> int:
        return int(self.ids.size)

    # ---------------------------------------------------------- 点から引く
    def query_many(self, qx: Any, qy: Any, qband: Any, dist: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """問い合わせの点ごとに、同じ層で距離 ≤ ``dist`` の索引の体 → (問い合わせの番号, 体の id, 距離[m])。

        自分を外すのは呼び手(体の id で外す)。並び=問い合わせの番号の順・その中は格子の近傍の順。
        """
        qx = np.atleast_1d(np.asarray(qx, dtype=np.float64))
        qy = np.atleast_1d(np.asarray(qy, dtype=np.float64))
        qb = np.atleast_1d(np.asarray(qband)).astype(np.int64)
        empty = (np.zeros(0, np.int64), np.zeros(0, np.int64), np.zeros(0, np.float64))
        if qx.size == 0 or self.ids.size == 0:
            return empty
        r = int(math.floor(float(dist) / self.cell_m)) + 1
        slo, shi = _row_spans(r, half=False)
        base = _grid_keys(qx, qy, qb, self.cell_m)
        lo = np.searchsorted(self.key, (base[:, None] + slo[None, :]).ravel(), side="left")
        hi = np.searchsorted(self.key, (base[:, None] + shi[None, :]).ravel(), side="right")
        which, pos = expand_ranges(lo, hi)
        if pos.size == 0:
            return empty
        q = which // slo.size
        dx = self.x[pos] - qx[q]
        dy = self.y[pos] - qy[q]
        dd = np.sqrt(dx * dx + dy * dy)
        ok = dd <= float(dist)
        return q[ok], self.ids[pos[ok]], dd[ok]

    def within(self, i: int, dist: float, *, xy: Any = None, band: Any = None) -> np.ndarray:
        """体 ``i`` から同じ層で距離 ≤ ``dist`` の体の id(``i`` を除く・昇順)。

        ``xy``・``band`` を渡せばその点から引く(``i`` が索引に無いとき・いまの位置で引くとき)。渡さなければ索引の
        ``i`` の位置(``i`` が索引に無ければ空)。
        """
        if xy is None:
            p = int(self.pos[int(i)]) if 0 <= int(i) < self.pos.size else -1
            if p < 0:
                return np.zeros(0, dtype=np.int64)
            qx, qy, qb = self.x[p], self.y[p], self.bands[p]
        else:
            qx, qy, qb = float(xy[0]), float(xy[1]), int(band)
        _q, got, _d = self.query_many(qx, qy, qb, dist)
        return np.sort(got[got != int(i)])

    # ---------------------------------------------------------- B5 の単位
    def unit_members(self, u: int) -> np.ndarray:
        """B5 の単位 ``u`` に居る索引の体の id(``u < 0`` は空)。"""
        if int(u) < 0:
            return np.zeros(0, dtype=np.int64)
        lo = int(np.searchsorted(self._u_sorted, int(u), side="left"))
        hi = int(np.searchsorted(self._u_sorted, int(u), side="right"))
        return self._u_ids[lo:hi]

    def unit_members_many(self, units: Any) -> tuple[np.ndarray, np.ndarray]:
        """単位の並び → (並びの番号, その単位に居る索引の体の id)(単位 < 0 は何も返さない)。"""
        u = np.asarray(units, dtype=np.int64)
        lo = np.searchsorted(self._u_sorted, u, side="left")
        hi = np.where(u >= 0, np.searchsorted(self._u_sorted, u, side="right"), lo)
        which, pos = expand_ranges(lo, hi)
        return which, self._u_ids[pos]

    def unit_counts(self) -> np.ndarray:
        """B5 の単位ごとの在室人数(単位のある体だけ・単位の昇順)。"""
        u = self._u_sorted[self._u_sorted >= 0]
        if u.size == 0:
            return np.zeros(0, dtype=np.int64)
        _v, c = np.unique(u, return_counts=True)
        return c.astype(np.int64)

    # ---------------------------------------------------------- 組(試験と道具の口・ランでは使わない)
    def pairs(self, dist: float) -> tuple[np.ndarray, np.ndarray]:
        """同じ層で距離 ≤ ``dist`` の体の組(各組 1 回・``a < b`` とは限らない=索引の並びの順)。"""
        n = int(self.ids.size)
        if n < 2:
            return np.zeros(0, np.int64), np.zeros(0, np.int64)
        r = int(math.floor(float(dist) / self.cell_m)) + 1
        slo, shi = _row_spans(r, half=True)
        idx = np.arange(n, dtype=np.int64)
        # 自分の格子: 自分より後ろの位置だけ
        hi0 = np.searchsorted(self.key, self.key, side="right")
        w0, p0 = expand_ranges(idx + 1, hi0)
        lo = np.searchsorted(self.key, (self.key[:, None] + slo[None, :]).ravel(), side="left")
        hi = np.searchsorted(self.key, (self.key[:, None] + shi[None, :]).ravel(), side="right")
        w, p = expand_ranges(lo, hi)
        A = np.concatenate([w0, w // slo.size])
        B = np.concatenate([p0, p])
        dx = self.x[A] - self.x[B]
        dy = self.y[A] - self.y[B]
        ok = np.sqrt(dx * dx + dy * dy) <= float(dist)
        return self.ids[A[ok]], self.ids[B[ok]]
