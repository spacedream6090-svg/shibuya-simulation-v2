"""build.pop.shapefile — ESRI Shapefile(.shp/.dbf)の最小パーサと点包含・被覆率。

なぜ自前か: 部品表(実装計画書 §2)に geopandas / pyshp / shapely は無い。国勢調査 2020 の
小地域境界(e-Stat r2ka13113)は **shapeType 5(Polygon)・1 ポリゴン=1 リング**だけなので、
標準ライブラリ(struct)+ NumPy で読める範囲に収まる。

対応範囲(意図的に狭い・範囲外は例外)
- .shp: shapeType **0(Null)と 5(Polygon)のみ**。マルチパート(穴・飛び地)はパート単位の
  リングとして読み、点包含は「全パートの交差数の総和が奇数」で判定する(ESRI の規約=外環が
  時計回り・穴が反時計回り、でも交差数の偶奇は同じ答えになる)。
- .dbf: dBASE III(version 0x03)・文字型 C と数値型 N のみ。**符号化は cp932 固定**
  (e-Stat の小地域境界は cp932)。削除フラグ ``*`` の行は落とす。

座標は .shp のまま(このモジュールは投影しない)。世界ローカル m への変換は呼び出し側が
``build.geo.common.latlon_to_local`` で行う(W0 の CRS が唯一の正典)。

逐次ループ宣言(P4)
- ``points_in_ring``: **リングの辺数**ぶんのループ(点数には比例しない=1 辺あたり NumPy 1 発)。
- ``read_shp`` / ``read_dbf``: **レコード数**ぶんのループ(80 行・可変長レコードのため)。
- ``assign_points_to_polygons``: **ポリゴン数**ぶんのループ(80)。
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np

__all__ = [
    "DBF_ENCODING",
    "Polygon",
    "read_shp",
    "read_dbf",
    "points_in_ring",
    "points_in_polygon",
    "assign_points_to_polygons",
    "ring_area",
    "polygon_area",
    "coverage_fraction",
]

#: .dbf の符号化(e-Stat 小地域境界は cp932 固定)。
DBF_ENCODING = "cp932"

_SHP_FILE_CODE = 9994
_SHAPE_NULL = 0
_SHAPE_POLYGON = 5


@dataclass(frozen=True)
class Polygon:
    """1 レコード=1 ポリゴン(複数リング可)。

    Attributes:
        parts: 各リングの開始添字(``points`` へのオフセット・長さ=リング数)。
        points: ``(n, 2)`` float64。列は .shp のまま(通常は経度・緯度)。
        bbox: ``(xmin, ymin, xmax, ymax)``。
    """

    parts: np.ndarray
    points: np.ndarray
    bbox: tuple[float, float, float, float]

    @property
    def n_rings(self) -> int:
        return int(self.parts.size)

    def rings(self) -> list[np.ndarray]:
        """リングごとの ``(m, 2)`` 配列。"""
        out: list[np.ndarray] = []
        n = int(self.points.shape[0])
        for k in range(self.n_rings):
            a = int(self.parts[k])
            b = int(self.parts[k + 1]) if k + 1 < self.n_rings else n
            out.append(self.points[a:b])
        return out

    def transformed(self, fn) -> "Polygon":
        """点を ``fn(x, y) -> (x', y')`` で写した新しい Polygon(投影に使う)。"""
        x, y = fn(self.points[:, 0], self.points[:, 1])
        pts = np.stack([np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)], axis=1)
        return Polygon(self.parts, pts, _bbox_of(pts))


def _bbox_of(pts: np.ndarray) -> tuple[float, float, float, float]:
    if pts.size == 0:
        return (0.0, 0.0, 0.0, 0.0)
    return (
        float(pts[:, 0].min()),
        float(pts[:, 1].min()),
        float(pts[:, 0].max()),
        float(pts[:, 1].max()),
    )


def read_shp(path: str | Path) -> list[Polygon]:
    """.shp → Polygon のリスト(レコード順)。

    Raises:
        ValueError: ファイルコード不一致・未対応の shapeType。
    """
    blob = Path(path).read_bytes()
    if len(blob) < 100 or struct.unpack(">i", blob[:4])[0] != _SHP_FILE_CODE:
        raise ValueError("shapefile のファイルコードが 9994 でない")
    file_len = struct.unpack(">i", blob[24:28])[0] * 2  # 16bit ワード → バイト
    end = min(len(blob), file_len)
    out: list[Polygon] = []
    off = 100
    while off + 8 <= end:
        _rec_no, clen = struct.unpack(">ii", blob[off : off + 8])
        off += 8
        body = blob[off : off + clen * 2]
        off += clen * 2
        shape_type = struct.unpack("<i", body[:4])[0]
        if shape_type == _SHAPE_NULL:
            empty = np.zeros((0, 2), dtype=np.float64)
            out.append(Polygon(np.zeros(0, dtype=np.int64), empty, (0.0, 0.0, 0.0, 0.0)))
            continue
        if shape_type != _SHAPE_POLYGON:
            raise ValueError(f"未対応の shapeType={shape_type}(本パーサは 0/5 のみ)")
        bbox = struct.unpack("<4d", body[4:36])
        n_parts, n_points = struct.unpack("<ii", body[36:44])
        p0 = 44
        parts = np.frombuffer(body[p0 : p0 + 4 * n_parts], dtype="<i4").astype(np.int64)
        p1 = p0 + 4 * n_parts
        pts = np.frombuffer(body[p1 : p1 + 16 * n_points], dtype="<f8").reshape(n_points, 2).copy()
        out.append(Polygon(parts, pts, (bbox[0], bbox[1], bbox[2], bbox[3])))
    return out


def read_dbf(path: str | Path, encoding: str = DBF_ENCODING) -> list[dict[str, Any]]:
    """.dbf → レコード辞書のリスト(フィールド順は宣言順・値は str または float/int)。

    数値型 ``N`` は小数桁 0 なら int、それ以外は float。空欄は ``None``。
    """
    blob = Path(path).read_bytes()
    n_rec = struct.unpack("<I", blob[4:8])[0]
    header_len = struct.unpack("<H", blob[8:10])[0]
    rec_len = struct.unpack("<H", blob[10:12])[0]
    fields: list[tuple[str, str, int, int]] = []
    off = 32
    while blob[off] != 0x0D:
        fd = blob[off : off + 32]
        name = fd[:11].split(b"\x00")[0].decode(encoding)
        fields.append((name, chr(fd[11]), fd[16], fd[17]))
        off += 32
    rows: list[dict[str, Any]] = []
    for i in range(n_rec):
        base = header_len + i * rec_len
        rec = blob[base : base + rec_len]
        if not rec or rec[0:1] == b"*":  # 削除フラグ
            continue
        pos = 1
        row: dict[str, Any] = {}
        for name, typ, length, dec in fields:
            raw = rec[pos : pos + length].decode(encoding).strip()
            pos += length
            if typ == "N":
                row[name] = None if raw == "" else (float(raw) if dec else int(raw))
            else:
                row[name] = raw
        rows.append(row)
    return rows


def points_in_ring(px: np.ndarray, py: np.ndarray, ring: np.ndarray) -> np.ndarray:
    """レイキャスティング(crossing number)の**交差の偶奇**を bool で返す。

    逐次ループ宣言(P4): リングの辺数ぶん。1 辺あたり NumPy 1 発なので点数には比例しない。

    Example:
        >>> sq = np.array([[0.0, 0.0], [2.0, 0.0], [2.0, 2.0], [0.0, 2.0]])
        >>> points_in_ring(np.array([1.0, 3.0]), np.array([1.0, 1.0]), sq).tolist()
        [True, False]
    """
    px = np.asarray(px, dtype=np.float64)
    py = np.asarray(py, dtype=np.float64)
    if ring.shape[0] < 3:
        return np.zeros(px.shape, dtype=bool)
    x1 = ring[:, 0]
    y1 = ring[:, 1]
    x2 = np.roll(x1, -1)
    y2 = np.roll(y1, -1)
    inside = np.zeros(px.shape, dtype=bool)
    for i in range(x1.size):
        cross = (y1[i] > py) != (y2[i] > py)
        if not cross.any():
            continue
        dy = y2[i] - y1[i]
        if dy == 0.0:
            continue
        x_int = (x2[i] - x1[i]) * (py - y1[i]) / dy + x1[i]
        inside ^= cross & (px < x_int)
    return inside


def points_in_polygon(px: np.ndarray, py: np.ndarray, poly: Polygon) -> np.ndarray:
    """全パートの交差数の総和の偶奇(穴つきポリゴンでも正しい)。"""
    px = np.asarray(px, dtype=np.float64)
    py = np.asarray(py, dtype=np.float64)
    inside = np.zeros(px.shape, dtype=bool)
    for ring in poly.rings():
        inside ^= points_in_ring(px, py, ring)
    return inside


def assign_points_to_polygons(
    px: np.ndarray, py: np.ndarray, polys: Sequence[Polygon]
) -> np.ndarray:
    """点 → 最初に包含したポリゴンの添字(見つからなければ −1)。

    ポリゴンは互いに素(行政界)なので「最初に見つけた1つ」で十分。bbox で候補を絞る。

    逐次ループ宣言(P4): ポリゴン数ぶん(80)。
    """
    px = np.asarray(px, dtype=np.float64)
    py = np.asarray(py, dtype=np.float64)
    out = np.full(px.shape, -1, dtype=np.int64)
    for k, poly in enumerate(polys):
        if poly.points.shape[0] == 0:
            continue
        xmin, ymin, xmax, ymax = _bbox_of(poly.points)
        cand = np.flatnonzero(
            (out < 0) & (px >= xmin) & (px <= xmax) & (py >= ymin) & (py <= ymax)
        )
        if cand.size == 0:
            continue
        hit = points_in_polygon(px[cand], py[cand], poly)
        out[cand[hit]] = k
    return out


def ring_area(ring: np.ndarray) -> float:
    """符号つき面積(反時計回りが正)。"""
    if ring.shape[0] < 3:
        return 0.0
    x = ring[:, 0]
    y = ring[:, 1]
    return float((x * np.roll(y, -1) - np.roll(x, -1) * y).sum()) / 2.0


def polygon_area(poly: Polygon) -> float:
    """パートの符号つき面積の総和の絶対値(穴は符号が逆なので引かれる)。"""
    return abs(sum(ring_area(r) for r in poly.rings()))


def coverage_fraction(
    poly: Polygon, inside_fn, step: float
) -> tuple[float, float]:
    """ポリゴンを固定格子で標本化し、``inside_fn(x, y) -> bool 配列`` が真の面積割合を返す。

    格子はワールド原点に釘付け(``floor(v/step)*step + step/2``)なので、同じ入力なら
    同じ標本点=決定論(乱数を使わない)。

    Returns:
        ``(被覆率, 標本化で測った面積[入力座標の単位の二乗])``。ポリゴン内に標本点が
        1 つも無いときは ``(0.0, 0.0)``。
    """
    xmin, ymin, xmax, ymax = _bbox_of(poly.points)
    if poly.points.shape[0] == 0:
        return (0.0, 0.0)
    gx = np.arange(np.floor(xmin / step) * step + step / 2.0, xmax + step, step)
    gy = np.arange(np.floor(ymin / step) * step + step / 2.0, ymax + step, step)
    if gx.size == 0 or gy.size == 0:
        return (0.0, 0.0)
    mx, my = np.meshgrid(gx, gy)
    mx = mx.ravel()
    my = my.ravel()
    ins = points_in_polygon(mx, my, poly)
    n_in = int(ins.sum())
    if n_in == 0:
        return (0.0, 0.0)
    covered = np.asarray(inside_fn(mx[ins], my[ins]), dtype=bool)
    return (float(covered.sum()) / n_in, n_in * step * step)
