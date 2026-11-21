# -*- coding: utf-8 -*-
"""las_io — LAS 1.2(Point Data Format 0〜3)を標準ライブラリ+numpy で読む(laspy・PDAL を使わない)。

pip を足さない約束(指示書 11-02 の発注・CLAUDE.md §7「入れる前に聞く」)のため、ASPRS LAS 1.2 の仕様
(2008-09-02 版)のヘッダ 227 B・VLR・点の記録を ``struct`` と numpy の構造化 dtype で読む。
LAS 1.3/1.4 の拡張(波形・64 bit の点数)は扱わない=ヘッダの版が 1.2 以外なら止まる(``LasFormatError``)。

点は ``np.memmap``(読み取り専用)で写すので、1 図郭(約 6〜9 M 点 × 34 B)を全部はメモリに載せない。
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

__all__ = ["LasFormatError", "LasHeader", "POINT_DTYPES", "HEADER_SIZE_12", "parse_header", "read_points",
           "build_las_bytes"]

_HEADER_FMT = "<4sHH16sBB32s32sHHHLLBHL5L3d3d6d"
HEADER_SIZE_12 = struct.calcsize(_HEADER_FMT)  # 227

_BASE = [("X", "<i4"), ("Y", "<i4"), ("Z", "<i4"), ("intensity", "<u2"), ("flags", "u1"),
         ("classification", "u1"), ("scan_angle", "i1"), ("user_data", "u1"), ("point_source_id", "<u2")]
POINT_DTYPES: dict[int, np.dtype] = {
    0: np.dtype(_BASE),
    1: np.dtype(_BASE + [("gps_time", "<f8")]),
    2: np.dtype(_BASE + [("red", "<u2"), ("green", "<u2"), ("blue", "<u2")]),
    3: np.dtype(_BASE + [("gps_time", "<f8"), ("red", "<u2"), ("green", "<u2"), ("blue", "<u2")]),
}


class LasFormatError(ValueError):
    """LAS の形が想定(1.2・PF 0〜3・大きさの整合)と違う。"""


@dataclass
class LasHeader:
    version: tuple[int, int]
    system_id: str
    software: str
    creation: tuple[int, int]  # (年の通し日, 年)
    header_size: int
    offset_to_points: int
    n_vlr: int
    point_format: int
    record_length: int
    n_points: int
    n_by_return: list[int]
    scale: tuple[float, float, float]
    offset: tuple[float, float, float]
    bbox: dict[str, float]  # min_x max_x min_y max_y min_z max_z
    vlrs: list[dict[str, Any]] = field(default_factory=list)
    geokeys: dict[int, Any] = field(default_factory=dict)
    geo_ascii: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": f"{self.version[0]}.{self.version[1]}", "system_id": self.system_id,
            "software": self.software, "creation_doy_year": list(self.creation),
            "header_size": self.header_size, "offset_to_points": self.offset_to_points, "n_vlr": self.n_vlr,
            "point_format": self.point_format, "record_length": self.record_length, "n_points": self.n_points,
            "n_by_return": self.n_by_return, "scale": list(self.scale), "offset": list(self.offset),
            "bbox": self.bbox, "vlrs": self.vlrs,
            "geokeys": {str(k): (list(v) if isinstance(v, tuple) else v) for k, v in self.geokeys.items()},
            "geo_ascii": self.geo_ascii,
        }


def _cstr(b: bytes) -> str:
    return b.split(b"\x00", 1)[0].decode("ascii", errors="replace").strip()


def _parse_geokeys(payload: bytes) -> dict[int, Any]:
    """GeoKeyDirectoryTag(VLR 34735)→ {key id: 値}(値が short のものは int・参照は ('ref', tag, count, offset))。"""
    if len(payload) < 8:
        return {}
    vals = struct.unpack(f"<{len(payload) // 2}H", payload[: (len(payload) // 2) * 2])
    n_keys = vals[3]
    out: dict[int, Any] = {}
    for k in range(n_keys):
        base = 4 + 4 * k
        if base + 3 >= len(vals):
            break
        key_id, loc, count, v = vals[base: base + 4]
        out[int(key_id)] = int(v) if loc == 0 else ("ref", int(loc), int(count), int(v))
    return out


def parse_header(buf: bytes) -> LasHeader:
    """ファイルの先頭(ヘッダと VLR を含む長さ)→ ``LasHeader``。"""
    if len(buf) < HEADER_SIZE_12 or buf[:4] != b"LASF":
        raise LasFormatError("LASF の署名が無い")
    u = struct.unpack(_HEADER_FMT, buf[:HEADER_SIZE_12])
    (_sig, _src, _enc, _guid, vmaj, vmin, sysid, soft, doy, year, hsize, off_pts, n_vlr, pf, rlen, npts,
     r1, r2, r3, r4, r5, sx, sy, sz, ox, oy, oz, maxx, minx, maxy, miny, maxz, minz) = u
    if (vmaj, vmin) != (1, 2):
        raise LasFormatError(f"LAS {vmaj}.{vmin} は扱わない(1.2 だけ)")
    if pf not in POINT_DTYPES:
        raise LasFormatError(f"Point Data Format {pf} は扱わない")
    if rlen != POINT_DTYPES[pf].itemsize:
        raise LasFormatError(f"record の長さ {rlen} が PF{pf} の {POINT_DTYPES[pf].itemsize} と違う")
    h = LasHeader(
        version=(vmaj, vmin), system_id=_cstr(sysid), software=_cstr(soft), creation=(doy, year),
        header_size=hsize, offset_to_points=off_pts, n_vlr=n_vlr, point_format=pf, record_length=rlen,
        n_points=npts, n_by_return=[r1, r2, r3, r4, r5], scale=(sx, sy, sz), offset=(ox, oy, oz),
        bbox={"min_x": minx, "max_x": maxx, "min_y": miny, "max_y": maxy, "min_z": minz, "max_z": maxz},
    )
    pos = hsize
    for _ in range(n_vlr):
        if pos + 54 > len(buf):
            raise LasFormatError("VLR の頭がヘッダの読みの外")
        _res, uid, rid, rlen_after, desc = struct.unpack("<H16sHH32s", buf[pos: pos + 54])
        payload = buf[pos + 54: pos + 54 + rlen_after]
        h.vlrs.append({"user_id": _cstr(uid), "record_id": rid, "length": rlen_after, "description": _cstr(desc)})
        if _cstr(uid) == "LASF_Projection" and rid == 34735:
            h.geokeys = _parse_geokeys(payload)
        if _cstr(uid) == "LASF_Projection" and rid == 34737:
            h.geo_ascii = payload.replace(b"\x00", b" ").decode("ascii", errors="replace").strip()
        pos += 54 + rlen_after
    if pos > off_pts:
        raise LasFormatError("VLR が点の始まりを越える")
    return h


def read_points(path: Path) -> tuple[LasHeader, np.memmap]:
    """LAS のファイル → (ヘッダ, 点の memmap)。大きさ = offset + n × record を確かめる。"""
    path = Path(path)
    size = path.stat().st_size
    head = np.fromfile(path, dtype=np.uint8, count=min(size, 1 << 16)).tobytes()
    h = parse_header(head)
    expect = h.offset_to_points + h.n_points * h.record_length
    if size != expect:
        raise LasFormatError(f"ファイルの大きさ {size} が ヘッダの示す {expect} と違う")
    pts = np.memmap(path, dtype=POINT_DTYPES[h.point_format], mode="r", offset=h.offset_to_points,
                    shape=(h.n_points,))
    return h, pts


def build_las_bytes(x: np.ndarray, y: np.ndarray, z: np.ndarray, cls: np.ndarray, *, scale: float = 0.001,
                    point_format: int = 3, epsg: int | None = 6677, returns: np.ndarray | None = None,
                    gps_time: np.ndarray | None = None) -> bytes:
    """試験用: 点の配列 → LAS 1.2 のバイト列(ヘッダ 227 B + VLR(GeoKey)+ 点)。offset は 0。"""
    dt = POINT_DTYPES[point_format]
    n = int(np.asarray(x).size)
    rec = np.zeros(n, dtype=dt)
    rec["X"] = np.round(np.asarray(x) / scale).astype(np.int32)
    rec["Y"] = np.round(np.asarray(y) / scale).astype(np.int32)
    rec["Z"] = np.round(np.asarray(z) / scale).astype(np.int32)
    rec["classification"] = np.asarray(cls, dtype=np.uint8)
    rn = np.ones(n, dtype=np.uint8) if returns is None else np.asarray(returns, dtype=np.uint8)
    rec["flags"] = (rn & 7) | (1 << 3)
    if "gps_time" in dt.names:
        rec["gps_time"] = np.zeros(n) if gps_time is None else gps_time
    vlr = b""
    n_vlr = 0
    if epsg is not None:
        keys = [1, 1, 0, 2, 1024, 0, 1, 1, 3072, 0, 1, int(epsg)]
        payload = struct.pack(f"<{len(keys)}H", *keys)
        vlr = struct.pack("<H16sHH32s", 0, b"LASF_Projection", 34735, len(payload), b"GeoKeyDirectoryTag") + payload
        n_vlr = 1
    off = HEADER_SIZE_12 + len(vlr)
    xs = rec["X"] * scale
    ys = rec["Y"] * scale
    zs = rec["Z"] * scale
    by_ret = [int((rn == k).sum()) for k in range(1, 6)]
    head = struct.pack(
        _HEADER_FMT, b"LASF", 0, 0, b"\x00" * 16, 1, 2, b"synthetic", b"test", 1, 2026, HEADER_SIZE_12, off, n_vlr,
        point_format, dt.itemsize, n, *by_ret, scale, scale, scale, 0.0, 0.0, 0.0,
        float(xs.max()) if n else 0.0, float(xs.min()) if n else 0.0, float(ys.max()) if n else 0.0,
        float(ys.min()) if n else 0.0, float(zs.max()) if n else 0.0, float(zs.min()) if n else 0.0,
    )
    return head + vlr + rec.tobytes()
