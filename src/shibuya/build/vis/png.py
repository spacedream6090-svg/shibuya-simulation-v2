"""最小の PNG 書き出し(zlib + PNG チャンクのみ・PIL/matplotlib 非依存)。

W20 検収パックの画像はここで書く。部品表(実装計画書 §2)に PIL/matplotlib は無いので
**自前**で PNG を組む。バイト決定論: フィルタは全行 0 固定・zlib は level と wbits を固定。

対応形式: 8bit グレースケール (H,W) と 8bit RGB (H,W,3)。
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

import numpy as np

__all__ = ["encode_png", "write_png", "Canvas", "GRAY_RAMP", "ramp_rgb"]

_SIG = b"\x89PNG\r\n\x1a\n"
#: zlib 圧縮水準(固定=再構築でバイト一致)。
_ZLEVEL = 6


def _chunk(tag: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + tag
        + payload
        + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
    )


def encode_png(image: np.ndarray) -> bytes:
    """(H,W) uint8 グレー or (H,W,3) uint8 RGB → PNG バイト列。"""
    arr = np.ascontiguousarray(image)
    if arr.dtype != np.uint8:
        raise TypeError(f"PNG は uint8 のみ: {arr.dtype}")
    if arr.ndim == 2:
        color_type = 0
        height, width = arr.shape
        stride = width
    elif arr.ndim == 3 and arr.shape[2] == 3:
        color_type = 2
        height, width = arr.shape[0], arr.shape[1]
        stride = width * 3
    else:
        raise ValueError(f"PNG は (H,W) か (H,W,3) のみ: {arr.shape}")
    if height == 0 or width == 0:
        raise ValueError("PNG は 0 画素にできない")

    raw = np.empty((height, stride + 1), dtype=np.uint8)
    raw[:, 0] = 0  # フィルタ種別 0 (None) 固定
    raw[:, 1:] = arr.reshape(height, stride)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    idat = zlib.compress(raw.tobytes(), _ZLEVEL)
    return _SIG + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")


def write_png(path: Path, image: np.ndarray) -> int:
    """PNG を書いてバイト数を返す。"""
    data = encode_png(image)
    Path(path).write_bytes(data)
    return len(data)


#: 連続量の配色(黒→青→緑→黄→白の5点線形・viridis 風の代替。装飾のみで判断には使わない)。
GRAY_RAMP: tuple[tuple[int, int, int], ...] = (
    (12, 12, 30),
    (34, 62, 130),
    (28, 140, 120),
    (215, 205, 60),
    (250, 250, 250),
)


def ramp_rgb(value: np.ndarray, ramp: tuple[tuple[int, int, int], ...] = GRAY_RAMP) -> np.ndarray:
    """0..1 の配列 → RGB uint8((...,3))。NaN は最初の色。"""
    v = np.clip(np.nan_to_num(np.asarray(value, dtype=np.float64), nan=0.0), 0.0, 1.0)
    stops = np.asarray(ramp, dtype=np.float64)
    n = stops.shape[0] - 1
    pos = v * n
    lo = np.clip(np.floor(pos).astype(np.int64), 0, n - 1)
    frac = (pos - lo)[..., None]
    out = stops[lo] * (1.0 - frac) + stops[lo + 1] * frac
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


class Canvas:
    """RGB キャンバス。世界ローカル平面 [m] → 画素(y は上が北)の写像つき。"""

    __slots__ = ("rgb", "x0", "y0", "m_per_px", "width", "height")

    def __init__(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        m_per_px: float,
        background: tuple[int, int, int] = (18, 18, 22),
    ) -> None:
        self.x0 = float(x0)
        self.y0 = float(y0)
        self.m_per_px = float(m_per_px)
        self.width = max(1, int(round((x1 - x0) / m_per_px)))
        self.height = max(1, int(round((y1 - y0) / m_per_px)))
        self.rgb = np.empty((self.height, self.width, 3), dtype=np.uint8)
        self.rgb[:, :] = np.asarray(background, dtype=np.uint8)

    def to_px(self, x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """平面座標 → 画素 (col, row)。範囲外も返す(呼び手が間引く)。"""
        col = np.floor((np.asarray(x, dtype=np.float64) - self.x0) / self.m_per_px).astype(np.int64)
        row = self.height - 1 - np.floor(
            (np.asarray(y, dtype=np.float64) - self.y0) / self.m_per_px
        ).astype(np.int64)
        return col, row

    def points(self, x: np.ndarray, y: np.ndarray, rgb: np.ndarray | tuple[int, int, int]) -> int:
        """点群を打つ。描けた画素数を返す。"""
        col, row = self.to_px(x, y)
        ok = (col >= 0) & (col < self.width) & (row >= 0) & (row < self.height)
        col, row = col[ok], row[ok]
        colors = np.asarray(rgb, dtype=np.uint8)
        if colors.ndim == 2:
            colors = colors[ok]
        self.rgb[row, col] = colors
        return int(col.shape[0])

    def square(self, x: float, y: float, half_px: int, rgb: tuple[int, int, int]) -> None:
        col, row = self.to_px(np.array([x]), np.array([y]))
        c, r = int(col[0]), int(row[0])
        c0, c1 = max(0, c - half_px), min(self.width, c + half_px + 1)
        r0, r1 = max(0, r - half_px), min(self.height, r + half_px + 1)
        if c1 > c0 and r1 > r0:
            self.rgb[r0:r1, c0:c1] = np.asarray(rgb, dtype=np.uint8)

    def line(self, xa: float, ya: float, xb: float, yb: float, rgb: tuple[int, int, int]) -> None:
        """線分(整数 Bresenham・端点含む)。"""
        (ca, ra), (cb, rb) = (
            [int(v[0]) for v in self.to_px(np.array([xa]), np.array([ya]))],
            [int(v[0]) for v in self.to_px(np.array([xb]), np.array([yb]))],
        )
        dc = abs(cb - ca)
        dr = -abs(rb - ra)
        sc = 1 if ca < cb else -1
        sr = 1 if ra < rb else -1
        err = dc + dr
        color = np.asarray(rgb, dtype=np.uint8)
        guard = dc - dr + 2
        while guard >= 0:
            guard -= 1
            if 0 <= ca < self.width and 0 <= ra < self.height:
                self.rgb[ra, ca] = color
            if ca == cb and ra == rb:
                break
            e2 = 2 * err
            if e2 >= dr:
                err += dr
                ca += sc
            if e2 <= dc:
                err += dc
                ra += sr

    def write(self, path: Path) -> int:
        return write_png(path, self.rgb)
