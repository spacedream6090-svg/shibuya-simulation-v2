"""街路面 2.5m 格子(D-W9「道路8mバッファ・2.5m格子」・W8/W9/W10 の共有台)。

定義(``street_points`` の docstring が正典):
  世界ローカル平面に**世界原点を格子原点とする pitch_m 間隔の格子**を敷き、
  歩行グラフの各エッジ折線から ``buffer_m`` 以内の格子点を採る。
  同一 (格子点, バンド) は1点に畳み、その点に最も近いエッジを ``nearest_edge_idx`` に持つ。
  → **層(バンド)別**なので、同じ平面座標でも GL と DECK では別の点になる。

W10(静的騒音場)は本格子の各点で LAeq を評価する。W8(可視性)・W9(影)も同じ格子を使う
(仕様書 §1: 239,028点×… の「点」)。仕様書の 239,028 は v1 の klass 集合での実測値であり、
本実装は**現行 w1_edges の全 klass**を使うので点数は一致しない可能性がある(調整はしない・
実測値をヘッダの notes に出す)。

expedient: バッファ幅 8m・格子ピッチ 2.5m(D-W9 既決・感度=6m/10m 対照)。
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np

__all__ = ["StreetPoints", "street_points", "segment_arrays"]


class StreetPoints:
    """街路格子。SoA(列ごとの numpy 配列)。"""

    __slots__ = ("x", "y", "band", "nearest_edge_idx", "pitch_m", "buffer_m", "klasses")

    def __init__(
        self,
        x: np.ndarray,
        y: np.ndarray,
        band: list[str],
        nearest_edge_idx: np.ndarray,
        pitch_m: float,
        buffer_m: float,
        klasses: tuple[str, ...],
    ) -> None:
        self.x = x
        self.y = y
        self.band = band
        self.nearest_edge_idx = nearest_edge_idx
        self.pitch_m = pitch_m
        self.buffer_m = buffer_m
        self.klasses = klasses

    def __len__(self) -> int:
        return int(self.x.shape[0])


def segment_arrays(
    edge_idx: Sequence[int],
    geom_start: Sequence[int],
    geom_count: Sequence[int],
    coords: np.ndarray,
    keep: Iterable[int] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """エッジ折線 → 線分配列 (ax, ay, bx, by, owner_edge_idx)。

    ``keep`` を渡すと、その edge_idx 集合の線分だけを返す。
    """
    keep_set = None if keep is None else set(int(k) for k in keep)
    ax: list[float] = []
    ay: list[float] = []
    bx: list[float] = []
    by: list[float] = []
    own: list[int] = []
    for e, s, n in zip(edge_idx, geom_start, geom_count):
        if keep_set is not None and int(e) not in keep_set:
            continue
        for i in range(int(s), int(s) + int(n) - 1):
            ax.append(float(coords[i, 0]))
            ay.append(float(coords[i, 1]))
            bx.append(float(coords[i + 1, 0]))
            by.append(float(coords[i + 1, 1]))
            own.append(int(e))
    return (
        np.asarray(ax, dtype=np.float64),
        np.asarray(ay, dtype=np.float64),
        np.asarray(bx, dtype=np.float64),
        np.asarray(by, dtype=np.float64),
        np.asarray(own, dtype=np.int32),
    )


def _dist_point_segments(
    px: np.ndarray, py: np.ndarray, ax: float, ay: float, bx: float, by: float
) -> np.ndarray:
    """点群 → 1線分の距離。"""
    dx = bx - ax
    dy = by - ay
    den = dx * dx + dy * dy
    if den <= 0.0:
        return np.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / den
    np.clip(t, 0.0, 1.0, out=t)
    return np.hypot(px - (ax + t * dx), py - (ay + t * dy))


def street_points(
    edges: dict[str, list],
    geometry: np.ndarray,
    buffer_m: float = 8.0,
    pitch_m: float = 2.5,
    klasses: tuple[str, ...] | None = None,
) -> StreetPoints:
    """歩行グラフ → 街路面格子点(層バンド別)。

    Args:
        edges: ``w1_edges.parquet`` の列辞書(``edge_idx``・``klass``・``band``・
            ``geom_start``・``geom_count`` を使う)。
        geometry: ``w1_edge_geometry.npz`` の ``coords`` 配列((N,2) 平面座標 [m])。
        buffer_m: エッジからの採用半径 [m](既定 8.0 = D-W9)。
        pitch_m: 格子ピッチ [m](既定 2.5 = D-W9)。格子原点=世界原点 (0,0)。
        klasses: 採用する klass。``None`` なら **edges に現れる全 klass**。

    Returns:
        StreetPoints。点は (band 昇順, iy 昇順, ix 昇順) の安定順に並ぶ。
    """
    coords = geometry
    use = set(edges["klass"]) if klasses is None else set(klasses)
    # (band, ix, iy) → (最小距離, edge_idx)
    best: dict[tuple[str, int, int], tuple[float, int]] = {}
    r = float(buffer_m)
    for e, klass, band, s, n in zip(
        edges["edge_idx"], edges["klass"], edges["band"], edges["geom_start"], edges["geom_count"]
    ):
        if klass not in use:
            continue
        s = int(s)
        n = int(n)
        for i in range(s, s + n - 1):
            ax, ay = float(coords[i, 0]), float(coords[i, 1])
            bx, by = float(coords[i + 1, 0]), float(coords[i + 1, 1])
            lo_x = min(ax, bx) - r
            hi_x = max(ax, bx) + r
            lo_y = min(ay, by) - r
            hi_y = max(ay, by) + r
            ix0 = int(math.ceil(lo_x / pitch_m))
            ix1 = int(math.floor(hi_x / pitch_m))
            iy0 = int(math.ceil(lo_y / pitch_m))
            iy1 = int(math.floor(hi_y / pitch_m))
            if ix1 < ix0 or iy1 < iy0:
                continue
            gx = np.arange(ix0, ix1 + 1, dtype=np.int64)
            gy = np.arange(iy0, iy1 + 1, dtype=np.int64)
            mx, my = np.meshgrid(gx, gy, indexing="xy")
            px = mx.ravel() * pitch_m
            py = my.ravel() * pitch_m
            d = _dist_point_segments(px, py, ax, ay, bx, by)
            hit = d <= r
            if not hit.any():
                continue
            for kx, ky, kd in zip(mx.ravel()[hit], my.ravel()[hit], d[hit]):
                key = (band, int(kx), int(ky))
                prev = best.get(key)
                if prev is None or kd < prev[0] or (kd == prev[0] and int(e) < prev[1]):
                    best[key] = (float(kd), int(e))

    keys = sorted(best.keys(), key=lambda k: (k[0], k[2], k[1]))
    xs = np.empty(len(keys), dtype=np.float32)
    ys = np.empty(len(keys), dtype=np.float32)
    ne = np.empty(len(keys), dtype=np.int32)
    bands: list[str] = []
    for i, key in enumerate(keys):
        band, kx, ky = key
        xs[i] = kx * pitch_m
        ys[i] = ky * pitch_m
        ne[i] = best[key][1]
        bands.append(band)
    return StreetPoints(xs, ys, bands, ne, pitch_m, buffer_m, tuple(sorted(use)))
