# -*- coding: utf-8 -*-
"""las_pointcloud_agg — 東京都 区部点群(航空レーザ 2023・LAS)→ 520 セルの床の高さ・坂・歩道の面の集計。

発注: 指示書 11-02 取得 1(集計=デッキと地下の床の高さ・坂の勾配・歩道の面)。従来の計画は R-119 #11(SR1)・
R-82 §3(Class 1〜3 だけ・DEM は Class 2・デッキの床は DSM−DEM・縁石は取れない見込み)・10-06 SR1/SR10/SR12。
記録: ``docs/bench/analysis/pointcloud-2026-11/README.md``。

流れ(1 図郭ずつ読む=メモリを抑える)
    1. zip の一覧を確かめる(.las 1 本だけ。ほかがあれば止まる)→ ``<raw>/las/<MESH>.las`` に展開(生データは残す)。
    2. LAS 1.2 PF3 を ``las_io``(標準ライブラリ+numpy)で読む。LAS の X=東・Y=北(第 9 系の y・x)を
       図郭の索引の経緯度の箱と突き合わせて確かめる(``axis_check``)。
    3. 第 9 系 → 経緯度(``jgd_plane``=国土地理院の式)→ 世界の平面(``shibuya.build.geo.common`` の原点と
       1 度あたりのメートル)。
    4. 0.25 m の格子(100 m セルごとに 400×400)へ: DEM=Class 2 の最低点・DSM=全点の最高点。図郭の境を
       またぐセルは図郭ごとの部分を min/max で合わせる。
    5. 全部の図郭の後に、セルごとの集計(``aggregate``)。

集計の定義(記録の README §3 に式)
    - 地面の高さ: 0.25 m の DEM の画素の中央値・5/95 分位(画素で重みづけ=点の数でなく面積)。
    - 勾配: 0.25 m と 2 m(0.25 m の画素の 8×8 の平均・有効 8 画素以上)の前進差分の大きさ |∇z|×100 [%]。
      地面の画素どうしだけ(穴は埋めない=建物の縁の偽の坂を作らない)。0.25 m は段差と点の雑音を含む。
    - セル間の坂: 隣(東西南北)のセルの地面の中央値との差 [m]・÷100 m=勾配 [%]。
    - DSM−DEM: DEM の穴を 1 m の全体のモザイクで押し引き(push-pull)の補間で埋め、各 DSM 画素の高さ h を出す。
      h が 3〜8 m の割合と 0.25 m 刻みの最頻値=デッキと歩道橋の床の候補(屋根・木・車を含む=建物の外形で除いた版と
      PLATEAU 橋梁 LOD2 の外形の中の版も出す)。
    - 歩道の面(**試み**): Class 2 の DEM で「平ら→0.10〜0.25 m の段→平ら」の辺を段差の候補とし、PLATEAU 道路
      LOD2/3 の歩道(2000・2010・2020)と車道(1000 番台)の境(歩道の中で車道から 0.5 m 以内)からの距離で割合を出す。
      格子は 0.25 m(発注)と 0.5 m(2×2 の平均=地盤点の抜けを減らした版)の 2 通り(欄の末尾 ``_025``・``_05``)。
    - 地下: 航空レーザは地下を測れない=**無いと宣言**(欄 ``ug_floor_status``・``ug_floor_reason``)。

逐次ループ宣言: 図郭ごと(≤62)・セルの柱ごと(≤453)・PLATEAU の多角形ごと(約 8 万=歩道 48,323+車道 31,185)の Python の繰り返し。点ごとの
繰り返しは無い(numpy の ufunc.at と bincount)。
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import re
import sys
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
for _p in (HERE, REPO / "src", REPO / "tools" / "instruments"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import jgd_plane as JP  # noqa: E402
import las_io as LI  # noqa: E402
from read_guard import SEALED_TOKENS, deny_hit  # noqa: E402
from shibuya.build.geo.common import CELL_M, M_PER_DEG_LAT, M_PER_DEG_LON, ORIGIN_LATLON  # noqa: E402

__all__ = [
    "RES", "TILE", "AggParams", "Grid", "parse_fetch_log", "load_mesh_index", "extract_las", "bin_mesh",
    "TileStore", "fill_push_pull", "fill_polygon_window", "sample_triangles", "aggregate", "run", "main",
    "local_to_latlon", "latlon_to_local_arr", "plane_to_local", "local_to_plane",
]

TOOL_VERSION = "pc-agg-0.1"
RES = 0.25
TILE = int(round(CELL_M / RES))  # 400
SIDEWALK_CODES = (2000, 2010, 2020)
UG_ABSENT_REASON = (
    "航空レーザ(上空からの計測)は地下の床に届かない=都の区部点群からは測れない。地下の床の高さは "
    "3dcel の地下点群の集計(別の段)と PLATEAU 地下街 LOD4 で出す"
)
EXPECTED_EPSG = 6677
MESH_RE = re.compile(r"^09LD\d{4}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class AggParams:
    res: float = RES
    step_min_m: float = 0.10
    step_max_m: float = 0.25
    flat_tol_m: float = 0.05
    near_px: int = 2                 # 0.5 m(歩道の縁からの距離・段差の近さ)
    deck_h_min_m: float = 3.0
    deck_h_max_m: float = 8.0
    mode_bin_m: float = 0.25
    slope2m_block: int = 8           # 0.25 m × 8 = 2 m
    slope2m_min_valid: int = 8       # 64 画素のうち有効がこれ以上
    fill_res_m: float = 1.0          # DEM の穴埋めのモザイク
    chunk_points: int = 2_000_000
    bldg_sample_m: float = 0.5
    brid_sample_m: float = 0.2
    brid_up_nz: float = 0.8

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


# ---------------------------------------------------------------------------------- 座標
def latlon_to_local_arr(lat, lon):
    """経緯度 → 世界の平面 (x=東, y=北) [m](common.latlon_to_local の配列版)。"""
    return ((np.asarray(lon, dtype=np.float64) - ORIGIN_LATLON[1]) * M_PER_DEG_LON,
            (np.asarray(lat, dtype=np.float64) - ORIGIN_LATLON[0]) * M_PER_DEG_LAT)


def local_to_latlon(x, y):
    return (ORIGIN_LATLON[0] + np.asarray(y, dtype=np.float64) / M_PER_DEG_LAT,
            ORIGIN_LATLON[1] + np.asarray(x, dtype=np.float64) / M_PER_DEG_LON)


def plane_to_local(east, north):
    """第 9 系 (東=LAS X, 北=LAS Y) → 世界の平面。"""
    lat, lon = JP.plane_to_latlon(north, east)
    return latlon_to_local_arr(lat, lon)


def local_to_plane(x, y):
    """世界の平面 → 第 9 系 (東, 北)(試験の合成と検算)。"""
    lat, lon = local_to_latlon(x, y)
    n, e = JP.latlon_to_plane(lat, lon)
    return e, n


# ---------------------------------------------------------------------------------- 入力
def _guard(path: Path) -> Path:
    hit = deny_hit(path, SEALED_TOKENS)
    if hit:
        raise PermissionError(f"封印の層の道筋は読まない: 語 {hit}")
    return Path(path)


def _rel(p: Path) -> str:
    """記録に書く道筋(リポの根からの相対・外ならファイル名だけ=絶対の道筋を書かない)。"""
    try:
        return Path(p).resolve().relative_to(REPO).as_posix()
    except ValueError:
        return Path(p).name


def parse_fetch_log(path: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    """``_fetch_log.tsv`` → ({図郭: 完了の行(最初のもの)}, 無視した行)。完了=sha256 が 64 桁・bytes=expected。

    raw の README の約束「最初の sha256 の行を正とする」に合わせる。同じ図郭の完了の行が複数あり sha256 が
    違えば止まる(``ValueError``)。
    """
    text = _guard(path).read_bytes().decode("utf-8", errors="replace")
    lines = [ln for ln in text.replace("\r\n", "\n").split("\n") if ln.strip()]
    if not lines:
        return {}, []
    head = lines[0].split("\t")
    done: dict[str, dict[str, Any]] = {}
    ignored: list[dict[str, str]] = []
    for ln in lines[1:]:
        row = dict(zip(head, ln.split("\t")))
        mesh = row.get("mesh", "")
        sha = (row.get("sha256") or "").strip().lower()
        ok_size = row.get("bytes") and row.get("bytes") == row.get("expected_bytes")
        if not MESH_RE.match(mesh):
            ignored.append({"mesh": mesh, "why": "図郭の名の形でない"})
            continue
        if not SHA_RE.match(sha) or not ok_size:
            continue
        if mesh in done:
            if done[mesh]["sha256"] != sha:
                raise ValueError(f"{mesh}: 取得ログの完了の行の sha256 が食い違う")
            done[mesh]["n_done_rows"] += 1
            continue
        done[mesh] = {"n_done_rows": 1, "sha256": sha, "bytes": int(row["bytes"]), "end_utc": row.get("end_utc", ""),
                      "url": row.get("url", ""), "last_modified": row.get("last_modified", ""),
                      "etag": row.get("etag", "")}
    return done, ignored


def load_mesh_index(path: Path) -> dict[str, dict[str, Any]]:
    """lp_mesh_selected_520cells.json → {図郭: {bbox_WSEN, url, ...}}。"""
    d = json.loads(_guard(path).read_bytes().decode("utf-8"))
    return {k: v for k, v in d.items() if MESH_RE.match(k)}


def mesh_local_rect(info: dict[str, Any]) -> tuple[float, float, float, float]:
    w, s, e, n = info["bbox_WSEN"]
    x0, y0 = latlon_to_local_arr(s, w)
    x1, y1 = latlon_to_local_arr(n, e)
    return float(x0), float(y0), float(x1), float(y1)


@dataclass
class Grid:
    """520 セルの (ix, iy) の柱(453)と、柱の番号の引き表。"""

    ix: np.ndarray
    iy: np.ndarray
    ix0: int
    iy0: int
    lut: np.ndarray  # (nix, niy) → 柱の番号 or -1

    @classmethod
    def from_pairs(cls, pairs: Iterable[tuple[int, int]]) -> "Grid":
        u = sorted(set((int(a), int(b)) for a, b in pairs))
        ix = np.array([a for a, _ in u], dtype=np.int32)
        iy = np.array([b for _, b in u], dtype=np.int32)
        ix0, iy0 = int(ix.min()), int(iy.min())
        lut = np.full((int(ix.max()) - ix0 + 1, int(iy.max()) - iy0 + 1), -1, dtype=np.int32)
        lut[ix - ix0, iy - iy0] = np.arange(ix.size, dtype=np.int32)
        return cls(ix=ix, iy=iy, ix0=ix0, iy0=iy0, lut=lut)

    @property
    def n(self) -> int:
        return int(self.ix.size)

    def col_of(self, cix: np.ndarray, ciy: np.ndarray) -> np.ndarray:
        a = np.asarray(cix, dtype=np.int64) - self.ix0
        b = np.asarray(ciy, dtype=np.int64) - self.iy0
        ok = (a >= 0) & (b >= 0) & (a < self.lut.shape[0]) & (b < self.lut.shape[1])
        out = np.full(a.shape, -1, dtype=np.int32)
        out[ok] = self.lut[a[ok], b[ok]]
        return out

    def col(self, cix: int, ciy: int) -> int:
        return int(self.col_of(np.array([cix]), np.array([ciy]))[0])

    def extent(self) -> tuple[float, float, float, float]:
        return (float(self.ix.min()) * CELL_M, float(self.iy.min()) * CELL_M,
                float(self.ix.max() + 1) * CELL_M, float(self.iy.max() + 1) * CELL_M)


def load_cells(path: Path) -> dict[str, np.ndarray]:
    t = pq.read_table(_guard(path), columns=["place_id", "ix", "iy", "band"]).to_pydict()
    return {k: np.asarray(v) for k, v in t.items()}


# ---------------------------------------------------------------------------------- 展開
def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def extract_las(zip_path: Path, las_dir: Path, mesh: str) -> tuple[Path, dict[str, Any]]:
    """zip の一覧を確かめてから ``las_dir/<MESH>.las`` に展開(既にあり大きさが同じなら使い回す)。"""
    zip_path = _guard(zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        return _extract_from(zf, las_dir, mesh)


def _extract_from(zf: zipfile.ZipFile, las_dir: Path, mesh: str) -> tuple[Path, dict[str, Any]]:
    infos = zf.infolist()
    names = [i.filename for i in infos]
    bad = [n for n in names if not n.lower().endswith(".las") or "/" in n or "\\" in n or ".." in n]
    if bad or len(infos) != 1:
        raise ValueError(f"{mesh}: zip の中身が .las 1 本でない: {names}")
    info = infos[0]
    if Path(info.filename).stem != mesh:
        raise ValueError(f"{mesh}: zip の中の名 {info.filename} が図郭と違う")
    las_dir.mkdir(parents=True, exist_ok=True)
    dst = las_dir / f"{mesh}.las"
    meta: dict[str, Any] = {"member": info.filename, "member_bytes": int(info.file_size),
                            "member_crc32": f"{info.CRC:08x}"}
    if dst.exists() and dst.stat().st_size == info.file_size:
        data = dst.read_bytes()
        meta["reused"] = True
    else:
        data = zf.read(info.filename)  # CRC を zipfile が確かめる
        tmp = las_dir / f"{mesh}.las.part"
        tmp.write_bytes(data)
        tmp.replace(dst)
        meta["reused"] = False
    meta["las_sha256"] = _sha256_bytes(data)
    meta["las_bytes"] = len(data)
    del data
    return dst, meta


# ---------------------------------------------------------------------------------- 図郭の読み
@dataclass
class MeshPartial:
    mesh: str
    cols: np.ndarray                    # 触れた柱の番号
    dem: np.ndarray                     # (k, TILE, TILE) float32 +inf=無し
    dsm: np.ndarray                     # (k, TILE, TILE) float32 -inf=無し
    cls_counts: np.ndarray              # (k, 32) int64
    stats: dict[str, Any] = field(default_factory=dict)


def _rect_iou(a, b) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def axis_check(h: LI.LasHeader, mesh_info: dict[str, Any] | None) -> dict[str, Any]:
    """LAS の X/Y が第 9 系の東/北か(箱の経緯度を図郭の索引と比べる)。"""
    bb = h.bbox
    epsg = h.geokeys.get(3072)
    out: dict[str, Any] = {"epsg_projected": epsg, "has_crs_vlr": bool(h.geokeys)}
    if h.geokeys and epsg != EXPECTED_EPSG:
        raise ValueError(f"座標系の VLR が EPSG {epsg}(期待は {EXPECTED_EPSG}=JGD2011 平面直角 第 9 系)")
    if mesh_info is None:
        return out
    w, s, e, n = mesh_info["bbox_WSEN"]
    ref = (w, s, e, n)
    la, lo = JP.plane_to_latlon([bb["min_y"], bb["max_y"]], [bb["min_x"], bb["max_x"]])
    c_east = (float(lo[0]), float(la[0]), float(lo[1]), float(la[1]))
    la2, lo2 = JP.plane_to_latlon([bb["min_x"], bb["max_x"]], [bb["min_y"], bb["max_y"]])
    c_north = (float(lo2[0]), float(la2[0]), float(lo2[1]), float(la2[1]))
    out["iou_las_x_is_east"] = round(_rect_iou(c_east, ref), 4)
    out["iou_las_x_is_north"] = round(_rect_iou(c_north, ref), 4)
    m_lat = M_PER_DEG_LAT
    m_lon = M_PER_DEG_LON
    out["corner_offset_m"] = {
        "west": round((c_east[0] - w) * m_lon, 3), "south": round((c_east[1] - s) * m_lat, 3),
        "east": round((c_east[2] - e) * m_lon, 3), "north": round((c_east[3] - n) * m_lat, 3),
    }
    return out


def bin_mesh(las_path: Path, mesh: str, grid: Grid, mesh_info: dict[str, Any] | None,
             params: AggParams = AggParams()) -> MeshPartial:
    """1 図郭の LAS → 柱ごとの 0.25 m の DEM(Class 2 の最低)・DSM(全点の最高)・Class の数。"""
    t0 = time.perf_counter()
    h, pts = LI.read_points(_guard(las_path))
    ax = axis_check(h, mesh_info)
    if mesh_info is not None and ax["iou_las_x_is_east"] < 0.9:
        raise ValueError(f"{mesh}: LAS の X=東 の前提が図郭の箱と合わない {ax}")
    sx, sy, sz = h.scale
    ox, oy, oz = h.offset
    n = h.n_points
    # 触れうる柱: 図郭の箱(局所)を 1 セル広げた範囲
    if mesh_info is not None:
        x0, y0, x1, y1 = mesh_local_rect(mesh_info)
        cand = []
        for cx in range(int(math.floor(x0 / CELL_M)) - 1, int(math.floor(x1 / CELL_M)) + 2):
            for cy in range(int(math.floor(y0 / CELL_M)) - 1, int(math.floor(y1 / CELL_M)) + 2):
                c = grid.col(cx, cy)
                if c >= 0:
                    cand.append(c)
        cand_cols = np.array(sorted(set(cand)), dtype=np.int32)
    else:
        cand_cols = np.arange(grid.n, dtype=np.int32)
    k = int(cand_cols.size)
    local_of = np.full(grid.n, -1, dtype=np.int32)
    local_of[cand_cols] = np.arange(k, dtype=np.int32)
    npx = TILE * TILE
    dem = np.full(k * npx, np.inf, dtype=np.float32)
    dsm = np.full(k * npx, -np.inf, dtype=np.float32)
    cls_counts = np.zeros(k * 32, dtype=np.int64)
    cls_all = np.zeros(32, dtype=np.int64)
    ret_num = np.zeros(8, dtype=np.int64)
    n_ret = np.zeros(8, dtype=np.int64)
    gps_min, gps_max = math.inf, -math.inf
    n_in = 0
    rgb_nonzero = 0
    z_min, z_max = math.inf, -math.inf
    has_gps = "gps_time" in pts.dtype.names
    has_rgb = "red" in pts.dtype.names
    t_read = 0.0
    t_bin = 0.0
    for a in range(0, n, params.chunk_points):
        ta = time.perf_counter()
        rec = np.asarray(pts[a: a + params.chunk_points])
        east = rec["X"].astype(np.float64) * sx + ox
        north = rec["Y"].astype(np.float64) * sy + oy
        z = (rec["Z"].astype(np.float64) * sz + oz)
        cls = (rec["classification"] & 31).astype(np.int64)
        fl = rec["flags"]
        ret_num += np.bincount(fl & 7, minlength=8)[:8]
        n_ret += np.bincount((fl >> 3) & 7, minlength=8)[:8]
        cls_all += np.bincount(cls, minlength=32)[:32]
        if has_gps:
            g = rec["gps_time"]
            gps_min = min(gps_min, float(g.min()))
            gps_max = max(gps_max, float(g.max()))
        if has_rgb:
            rgb_nonzero += int(((rec["red"] > 0) | (rec["green"] > 0) | (rec["blue"] > 0)).sum())
        z_min = min(z_min, float(z.min()))
        z_max = max(z_max, float(z.max()))
        x, y = plane_to_local(east, north)
        del rec, east, north
        t_read += time.perf_counter() - ta
        tb = time.perf_counter()
        cx = np.floor(x / CELL_M).astype(np.int64)
        cy = np.floor(y / CELL_M).astype(np.int64)
        col = grid.col_of(cx, cy)
        loc = np.where(col >= 0, local_of[np.maximum(col, 0)], -1)
        keep = loc >= 0
        n_in += int(keep.sum())
        px = np.clip(np.floor((x[keep] - cx[keep] * CELL_M) / params.res).astype(np.int64), 0, TILE - 1)
        py = np.clip(np.floor((y[keep] - cy[keep] * CELL_M) / params.res).astype(np.int64), 0, TILE - 1)
        lk = loc[keep].astype(np.int64)
        flat = lk * npx + py * TILE + px
        zk = z[keep].astype(np.float32)
        ck = cls[keep]
        np.maximum.at(dsm, flat, zk)
        gsel = ck == 2
        np.minimum.at(dem, flat[gsel], zk[gsel])
        cls_counts += np.bincount(lk * 32 + ck, minlength=k * 32)
        t_bin += time.perf_counter() - tb
    del pts
    dem = dem.reshape(k, TILE, TILE)
    dsm = dsm.reshape(k, TILE, TILE)
    cls_counts = cls_counts.reshape(k, 32)
    touched = np.nonzero(cls_counts.sum(axis=1) > 0)[0]
    bb = h.bbox
    area = (bb["max_x"] - bb["min_x"]) * (bb["max_y"] - bb["min_y"])
    stats = {
        "mesh": mesh, "header": h.as_dict(), "axis_check": ax,
        "n_points": int(n), "n_points_in_cells": n_in,
        "class_counts": {str(c): int(v) for c, v in enumerate(cls_all) if v},
        "return_number_counts": {str(c): int(v) for c, v in enumerate(ret_num) if v},
        "number_of_returns_counts": {str(c): int(v) for c, v in enumerate(n_ret) if v},
        "gps_time_range": [gps_min, gps_max] if has_gps else None,
        "rgb_nonzero_frac": (rgb_nonzero / n) if (has_rgb and n) else None,
        "z_range": [z_min, z_max], "bbox_area_m2": area,
        "density_pt_m2": (n / area) if area > 0 else None,
        "ground_density_pt_m2": (int(cls_all[2]) / area) if area > 0 else None,
        "n_cols_touched": int(touched.size),
        "sec_read_transform": round(t_read, 3), "sec_bin": round(t_bin, 3),
        "sec_total": round(time.perf_counter() - t0, 3),
    }
    return MeshPartial(mesh=mesh, cols=cand_cols[touched], dem=dem[touched], dsm=dsm[touched],
                       cls_counts=cls_counts[touched], stats=stats)


class TileStore:
    """柱ごとの 0.25 m の DEM/DSM(図郭をまたいで min/max で合わせる)。"""

    def __init__(self, grid: Grid):
        self.grid = grid
        self.dem: dict[int, np.ndarray] = {}
        self.dsm: dict[int, np.ndarray] = {}
        self.cls: dict[int, np.ndarray] = {}
        self.meshes_of: dict[int, list[str]] = {}

    def merge(self, part: MeshPartial) -> None:
        for j, c in enumerate(part.cols.tolist()):
            if c in self.dem:
                np.fmin(self.dem[c], part.dem[j], out=self.dem[c])
                np.fmax(self.dsm[c], part.dsm[j], out=self.dsm[c])
                self.cls[c] += part.cls_counts[j]
            else:
                self.dem[c] = part.dem[j].copy()
                self.dsm[c] = part.dsm[j].copy()
                self.cls[c] = part.cls_counts[j].copy()
            self.meshes_of.setdefault(c, []).append(part.mesh)

    def dem_nan(self, c: int) -> np.ndarray:
        a = self.dem[c].copy()
        a[~np.isfinite(a)] = np.nan
        return a

    def dsm_nan(self, c: int) -> np.ndarray:
        a = self.dsm[c].copy()
        a[~np.isfinite(a)] = np.nan
        return a


# ---------------------------------------------------------------------------------- 穴埋め・ラスタ化
def fill_push_pull(a: np.ndarray) -> np.ndarray:
    """NaN の穴を「押し引き」で埋める(2×2 の重みつき平均で粗くし、粗い値で細かい穴を埋める)。"""
    a = np.asarray(a, dtype=np.float64)
    w = np.isfinite(a).astype(np.float64)
    if w.sum() == 0:
        return a.astype(np.float32)
    v = np.where(w > 0, a, 0.0)
    levels = [(v, w)]
    while True:
        v, w = levels[-1]
        if w.min() > 0 or (v.shape[0] == 1 and v.shape[1] == 1):
            break
        ny, nx = v.shape
        py, px = ny % 2, nx % 2
        vv = np.pad(v * w, ((0, py), (0, px)))
        ww = np.pad(w, ((0, py), (0, px)))
        s = vv.reshape(vv.shape[0] // 2, 2, vv.shape[1] // 2, 2).sum(axis=(1, 3))
        sw = ww.reshape(ww.shape[0] // 2, 2, ww.shape[1] // 2, 2).sum(axis=(1, 3))
        v2 = np.where(sw > 0, s / np.maximum(sw, 1e-12), 0.0)
        w2 = np.minimum(sw, 1.0)
        levels.append((v2, w2))
    filled = levels[-1][0]
    for v, w in reversed(levels[:-1]):
        up = np.repeat(np.repeat(filled, 2, axis=0), 2, axis=1)[: v.shape[0], : v.shape[1]]
        filled = np.where(w > 0, v, up)
    return filled.astype(np.float32)


def fill_polygon_window(rings: Sequence[np.ndarray], x0: float, y0: float, res: float, nx: int,
                        ny: int) -> np.ndarray:
    """多角形(環の並び・偶奇則=穴を含む)→ 窓 (ny, nx) の中の画素の中心が内側か。"""
    out = np.zeros((ny, nx), dtype=bool)
    xa_l, ya_l, xb_l, yb_l = [], [], [], []
    for r in rings:
        r = np.asarray(r, dtype=np.float64)[:, :2]
        if r.shape[0] < 3:
            continue
        xa_l.append(r[:, 0])
        ya_l.append(r[:, 1])
        xb_l.append(np.roll(r[:, 0], -1))
        yb_l.append(np.roll(r[:, 1], -1))
    if not xa_l:
        return out
    xa = np.concatenate(xa_l)
    ya = np.concatenate(ya_l)
    xb = np.concatenate(xb_l)
    yb = np.concatenate(yb_l)
    nz = ya != yb
    xa, ya, xb, yb = xa[nz], ya[nz], xb[nz], yb[nz]
    ylo = np.minimum(ya, yb)
    yhi = np.maximum(ya, yb)
    j0 = np.clip(np.ceil((ylo - y0) / res - 0.5).astype(np.int64), 0, ny)
    j1 = np.clip(np.ceil((yhi - y0) / res - 0.5).astype(np.int64), 0, ny)
    cnt = j1 - j0
    m = cnt > 0
    if not m.any():
        return out
    xa, ya, xb, yb, j0, cnt = xa[m], ya[m], xb[m], yb[m], j0[m], cnt[m]
    e = np.repeat(np.arange(cnt.size), cnt)
    starts = np.repeat(np.cumsum(cnt) - cnt, cnt)
    j = j0[e] + (np.arange(e.size) - starts)
    yc = y0 + (j + 0.5) * res
    xint = xa[e] + (yc - ya[e]) * (xb[e] - xa[e]) / (yb[e] - ya[e])
    i0 = np.ceil((xint - x0) / res - 0.5).astype(np.int64)
    i0 = np.maximum(i0, 0)
    sel = i0 < nx
    tog = np.zeros((ny, nx + 1), dtype=np.int32)
    np.add.at(tog, (j[sel], i0[sel]), 1)
    out = (np.cumsum(tog, axis=1)[:, :nx] & 1).astype(bool)
    return out


def _polygons_of_rings(rings: Sequence[tuple[np.ndarray, int]]) -> list[list[np.ndarray]]:
    """(環, 符号) の並び → 多角形(外周 + 後に続く穴)の並び。"""
    polys: list[list[np.ndarray]] = []
    for r, s in rings:
        if s > 0 or not polys:
            polys.append([r])
        else:
            polys[-1].append(r)
    return polys


def rasterize_polygons(polys: Sequence[Sequence[np.ndarray]], grid: Grid, res: float = RES) -> dict[int, np.ndarray]:
    """多角形の並び → {柱: (TILE, TILE) bool}(内側の画素)。"""
    out: dict[int, np.ndarray] = {}
    for rings in polys:
        allp = np.concatenate([np.asarray(r)[:, :2] for r in rings])
        bx0, by0 = allp.min(axis=0)
        bx1, by1 = allp.max(axis=0)
        for cx in range(int(math.floor(bx0 / CELL_M)), int(math.floor(bx1 / CELL_M)) + 1):
            for cy in range(int(math.floor(by0 / CELL_M)), int(math.floor(by1 / CELL_M)) + 1):
                c = grid.col(cx, cy)
                if c < 0:
                    continue
                tx0, ty0 = cx * CELL_M, cy * CELL_M
                i_lo = max(0, int(math.floor((bx0 - tx0) / res)) - 1)
                i_hi = min(TILE, int(math.ceil((bx1 - tx0) / res)) + 1)
                j_lo = max(0, int(math.floor((by0 - ty0) / res)) - 1)
                j_hi = min(TILE, int(math.ceil((by1 - ty0) / res)) + 1)
                if i_hi <= i_lo or j_hi <= j_lo:
                    continue
                sub = fill_polygon_window(rings, tx0 + i_lo * res, ty0 + j_lo * res, res, i_hi - i_lo, j_hi - j_lo)
                if not sub.any():
                    continue
                if c not in out:
                    out[c] = np.zeros((TILE, TILE), dtype=bool)
                out[c][j_lo:j_hi, i_lo:i_hi] |= sub
    return out


def sample_triangles(tri: np.ndarray, step: float, max_k: int = 600,
                     batch_points: int = 2_000_000) -> Iterable[tuple[np.ndarray, np.ndarray]]:
    """三角形 (n, 3, 3) → 面の上の格子点 (m, 3) と三角形の番号 (m,) を束で返す(最長辺 / step の重心格子)。"""
    tri = np.asarray(tri, dtype=np.float64)
    if tri.shape[0] == 0:
        return
    e = np.stack([np.linalg.norm(tri[:, 1, :2] - tri[:, 0, :2], axis=1),
                  np.linalg.norm(tri[:, 2, :2] - tri[:, 1, :2], axis=1),
                  np.linalg.norm(tri[:, 0, :2] - tri[:, 2, :2], axis=1)], axis=1).max(axis=1)
    kk = np.clip(np.ceil(e / step).astype(np.int64), 1, max_k)
    for k in np.unique(kk).tolist():
        idx = np.nonzero(kk == k)[0]
        ii, jj = np.meshgrid(np.arange(k + 1), np.arange(k + 1), indexing="ij")
        sel = (ii + jj) <= k
        u = (ii[sel] / k)[None, :, None]
        v = (jj[sel] / k)[None, :, None]
        m = int(u.shape[1])
        per = max(1, batch_points // m)
        for a in range(0, idx.size, per):
            b = idx[a: a + per]
            A = tri[b, 0][:, None, :]
            B = tri[b, 1][:, None, :]
            C = tri[b, 2][:, None, :]
            p = A + u * (B - A) + v * (C - A)
            yield p.reshape(-1, 3), np.repeat(b, m)


def _tri_nz(tri: np.ndarray) -> np.ndarray:
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1)
    return np.where(ln > 0, n[:, 2] / np.maximum(ln, 1e-12), 0.0)


def _points_to_pixels(grid: Grid, x: np.ndarray, y: np.ndarray, res: float = RES):
    cx = np.floor(x / CELL_M).astype(np.int64)
    cy = np.floor(y / CELL_M).astype(np.int64)
    col = grid.col_of(cx, cy)
    k = col >= 0
    px = np.clip(np.floor((x[k] - cx[k] * CELL_M) / res).astype(np.int64), 0, TILE - 1)
    py = np.clip(np.floor((y[k] - cy[k] * CELL_M) / res).astype(np.int64), 0, TILE - 1)
    return k, col[k], py, px


def rasterize_building_mask(V: np.ndarray, F: np.ndarray, grid: Grid, params: AggParams) -> dict[int, np.ndarray]:
    """PLATEAU 建物の三角形(壁を除く)→ {柱: bool の外形(1 画素広げる)}。"""
    tri = V[F].astype(np.float64)
    tri = tri[np.abs(_tri_nz(tri)) >= 0.2]
    out: dict[int, np.ndarray] = {}
    for p, _t in sample_triangles(tri, params.bldg_sample_m):
        k, col, py, px = _points_to_pixels(grid, p[:, 0], p[:, 1], params.res)
        for c in np.unique(col).tolist():
            s = col == c
            if c not in out:
                out[c] = np.zeros((TILE, TILE), dtype=bool)
            out[c][py[s], px[s]] = True
    return {c: _dilate(m, 1) for c, m in out.items()}


def rasterize_bridges(structs: Sequence[np.ndarray], grid: Grid, params: AggParams):
    """PLATEAU 橋梁 LOD2 の構造ごとの三角形 → ({柱: 構造の番号 int16 (-1=無し)}, {柱: 上面の高さ float32})。"""
    ids: dict[int, np.ndarray] = {}
    top: dict[int, np.ndarray] = {}
    for sid, tri in enumerate(structs):
        tri = np.asarray(tri, dtype=np.float64)
        tri = tri[np.abs(_tri_nz(tri)) >= params.brid_up_nz]
        for p, _t in sample_triangles(tri, params.brid_sample_m):
            k, col, py, px = _points_to_pixels(grid, p[:, 0], p[:, 1], params.res)
            zz = p[k, 2].astype(np.float32)
            for c in np.unique(col).tolist():
                s = col == c
                if c not in ids:
                    ids[c] = np.full((TILE, TILE), -1, dtype=np.int16)
                    top[c] = np.full((TILE, TILE), -np.inf, dtype=np.float32)
                flat = py[s] * TILE + px[s]
                t_flat = top[c].reshape(-1)
                i_flat = ids[c].reshape(-1)
                cur = np.full(TILE * TILE, -np.inf, dtype=np.float32)
                np.maximum.at(cur, flat, zz[s])
                upd = cur > t_flat
                t_flat[upd] = cur[upd]
                i_flat[upd] = sid
    for c in top:
        top[c][~np.isfinite(top[c])] = np.nan
    return ids, top


def _dilate(m: np.ndarray, r: int) -> np.ndarray:
    out = m.copy()
    for _ in range(r):
        o = out.copy()
        o[1:, :] |= out[:-1, :]
        o[:-1, :] |= out[1:, :]
        o[:, 1:] |= out[:, :-1]
        o[:, :-1] |= out[:, 1:]
        out = o
    return out


# ---------------------------------------------------------------------------------- 集計
def _q(a: np.ndarray, q: float) -> float:
    return float(np.quantile(a, q)) if a.size else math.nan


def _stats(a: np.ndarray, prefix: str) -> dict[str, float]:
    a = a[np.isfinite(a)]
    return {f"{prefix}_mean": float(a.mean()) if a.size else math.nan, f"{prefix}_med": _q(a, 0.5),
            f"{prefix}_p95": _q(a, 0.95), f"{prefix}_max": float(a.max()) if a.size else math.nan}


def _grad_mag(z: np.ndarray, spacing: float) -> np.ndarray:
    gx = z[:-1, 1:] - z[:-1, :-1]
    gy = z[1:, :-1] - z[:-1, :-1]
    g = np.sqrt(gx * gx + gy * gy) / spacing * 100.0
    return g[np.isfinite(g)]


def _block_mean(z: np.ndarray, b: int, min_valid: int) -> np.ndarray:
    ny, nx = z.shape
    v = np.isfinite(z)
    zz = np.where(v, z, 0.0).reshape(ny // b, b, nx // b, b).sum(axis=(1, 3))
    nn = v.reshape(ny // b, b, nx // b, b).sum(axis=(1, 3))
    return np.where(nn >= min_valid, zz / np.maximum(nn, 1), np.nan)


def _mode(h: np.ndarray, lo: float, hi: float, bw: float) -> float:
    h = h[(h >= lo) & (h <= hi)]
    if h.size == 0:
        return math.nan
    nb = int(round((hi - lo) / bw))
    cnt, edges = np.histogram(h, bins=nb, range=(lo, hi))
    i = int(np.argmax(cnt))
    return float((edges[i] + edges[i + 1]) / 2)


def detect_steps(dem: np.ndarray, p: AggParams) -> tuple[np.ndarray, int, int]:
    """0.25 m の DEM の「平ら→段(0.10〜0.25 m)→平ら」→ (段の両側の画素の印, 段の辺の数, 判定できた辺の数)。"""
    mark = np.zeros(dem.shape, dtype=bool)
    n_step = 0
    n_eval = 0
    for axis in (1, 0):
        z = dem if axis == 1 else dem.T
        mk = mark if axis == 1 else mark.T
        a, b, c, d = z[:, :-3], z[:, 1:-2], z[:, 2:-1], z[:, 3:]
        ok = np.isfinite(a) & np.isfinite(b) & np.isfinite(c) & np.isfinite(d)
        s = np.abs(c - b)
        hit = ok & (s >= p.step_min_m) & (s <= p.step_max_m) & (np.abs(b - a) < p.flat_tol_m) & (
            np.abs(d - c) < p.flat_tol_m)
        n_step += int(hit.sum())
        n_eval += int(ok.sum())
        mk[:, 1:-2] |= hit
        mk[:, 2:-1] |= hit
    return mark, n_step, n_eval


CURB_COUNT_KEYS = ("n_step_px", "n_step_px_near", "n_ground_px", "n_ground_px_near", "n_curb_px_ground",
                   "n_curb_px_hit", "n_ground_px_hit")


def _curb_metrics(mark: np.ndarray, g: np.ndarray, curb: np.ndarray, near_px: int) -> dict[str, Any]:
    """段差の画素 ``mark``・地面の画素 ``g``・縁石の線の画素 ``curb`` → 近さの割合・濃さ・拾えた率。

    - step_near_frac: 段差の画素のうち縁石の線から near_px 以内の割合
    - ground_near_frac: 地面の画素のうち同じ帯の割合(偶然の基準)
    - enrichment = step_near_frac / ground_near_frac(1 なら偶然と同じ)
    - recall: 地面のある縁石の線の画素のうち near_px 以内に段差がある割合・recall_base: 地面の画素全体での同じ割合
    """
    near = _dilate(curb, near_px)
    stepnear = _dilate(mark, near_px)
    out: dict[str, Any] = {
        "n_step_px": int(mark.sum()), "n_step_px_near": int((mark & near).sum()), "n_ground_px": int(g.sum()),
        "n_ground_px_near": int((g & near).sum()), "n_curb_px_ground": int((curb & g).sum()),
        "n_curb_px_hit": int((curb & g & stepnear).sum()), "n_ground_px_hit": int((g & stepnear).sum()),
    }
    out.update(_curb_ratios(out))
    return out


def _curb_ratios(c: dict[str, int]) -> dict[str, float]:
    sn = c["n_step_px_near"] / c["n_step_px"] if c["n_step_px"] else math.nan
    gn = c["n_ground_px_near"] / c["n_ground_px"] if c["n_ground_px"] else math.nan
    return {"step_near_frac": sn, "ground_near_frac": gn,
            "enrichment": sn / gn if (math.isfinite(sn) and math.isfinite(gn) and gn > 0) else math.nan,
            "recall": c["n_curb_px_hit"] / c["n_curb_px_ground"] if c["n_curb_px_ground"] else math.nan,
            "recall_base": c["n_ground_px_hit"] / c["n_ground_px"] if c["n_ground_px"] else math.nan}


def _sample_grid(src: np.ndarray, ox: float, oy: float, res: float, cx: int, cy: int,
                 tres: float = RES) -> np.ndarray:
    """格子 src (ny, nx・画素の左下が (ox, oy)) を柱 (cx, cy) の 0.25 m 画素の中心で最近傍に引く。"""
    xc = cx * CELL_M + (np.arange(TILE) + 0.5) * tres
    yc = cy * CELL_M + (np.arange(TILE) + 0.5) * tres
    ii = np.floor((xc - ox) / res).astype(np.int64)
    jj = np.floor((yc - oy) / res).astype(np.int64)
    oki = (ii >= 0) & (ii < src.shape[1])
    okj = (jj >= 0) & (jj < src.shape[0])
    out = np.full((TILE, TILE), np.nan, dtype=np.float32)
    if oki.any() and okj.any():
        sub = src[np.clip(jj, 0, src.shape[0] - 1)][:, np.clip(ii, 0, src.shape[1] - 1)]
        sub = np.where(okj[:, None] & oki[None, :], sub, np.nan)
        out[:] = sub
    return out


def build_fill_mosaic(store: TileStore, grid: Grid,
                      res: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, float]]:
    """柱の DEM・DSM → 全体の res [m] のモザイク(DEM は穴を押し引きで埋めた版と生の版・DSM は最高)。"""
    X0, Y0, X1, Y1 = grid.extent()
    nx = int(round((X1 - X0) / res))
    ny = int(round((Y1 - Y0) / res))
    b = int(round(res / RES))
    raw = np.full((ny, nx), np.nan, dtype=np.float32)
    dsm = np.full((ny, nx), np.nan, dtype=np.float32)
    nt = TILE // b
    for c in store.dem:
        cx, cy = int(grid.ix[c]), int(grid.iy[c])
        i0 = int(round((cx * CELL_M - X0) / res))
        j0 = int(round((cy * CELL_M - Y0) / res))
        raw[j0:j0 + nt, i0:i0 + nt] = _block_mean(store.dem_nan(c), b, 1)
        ds = store.dsm_nan(c).reshape(nt, b, nt, b)
        with np.errstate(all="ignore"):
            mx = np.where(np.isfinite(ds).any(axis=(1, 3)), np.nanmax(np.where(np.isfinite(ds), ds, -np.inf),
                                                                       axis=(1, 3)), np.nan)
        dsm[j0:j0 + nt, i0:i0 + nt] = mx
    filled = fill_push_pull(raw)
    meta = {"ox": X0, "oy": Y0, "res": res, "nx": nx, "ny": ny}
    return raw, filled, dsm, meta


def aggregate(store: TileStore, grid: Grid, cells: dict[str, np.ndarray], mesh_rects: dict[str, tuple],
              done_meshes: Sequence[str], params: AggParams = AggParams(), *,
              nav_dem: tuple[np.ndarray, dict] | None = None, sidewalk: dict[int, np.ndarray] | None = None,
              roadway: dict[int, np.ndarray] | None = None, bldg: dict[int, np.ndarray] | None = None,
              bldg_rect: tuple[float, float, float, float] | None = None,
              brid: tuple[dict[int, np.ndarray], dict[int, np.ndarray]] | None = None,
              n_brid: int = 0) -> dict[str, Any]:
    """柱ごとの集計 → 520 セルの行・橋梁の構造ごとの行・全体の要約。"""
    p = params
    raw1, fill1, dsm1, m1 = build_fill_mosaic(store, grid, p.fill_res_m)
    done = set(done_meshes)
    col_rows: dict[int, dict[str, Any]] = {}
    curb_tot = {tag: dict({k: 0 for k in CURB_COUNT_KEYS}, n_step_edges=0, n_eval_edges=0) for tag in ("025", "05")}
    brid_acc: dict[int, dict[str, list]] = {}
    for c in range(grid.n):
        cx, cy = int(grid.ix[c]), int(grid.iy[c])
        cell_rect = (cx * CELL_M, cy * CELL_M, (cx + 1) * CELL_M, (cy + 1) * CELL_M)
        over = sorted(m for m, r in mesh_rects.items()
                      if min(r[2], cell_rect[2]) - max(r[0], cell_rect[0]) > 1e-6
                      and min(r[3], cell_rect[3]) - max(r[1], cell_rect[1]) > 1e-6)
        row: dict[str, Any] = {"meshes_overlap": ",".join(over),
                               "meshes_done": ",".join(m for m in over if m in done),
                               "complete": bool(over) and all(m in done for m in over)}
        if c not in store.dem:
            row["has_data"] = False
            col_rows[c] = row
            continue
        row["has_data"] = True
        dem = store.dem_nan(c)
        dsm = store.dsm_nan(c)
        cc = store.cls[c]
        g = np.isfinite(dem)
        cov = np.isfinite(dsm)
        row["coverage_frac"] = float(cov.mean())
        row["ground_px_frac"] = float(g.mean())
        row["n_pts"] = int(cc.sum())
        for k in (1, 2, 3):
            row[f"n_pts_c{k}"] = int(cc[k])
        row["n_pts_c_other"] = int(cc.sum() - cc[1] - cc[2] - cc[3])
        cov_area = float(cov.sum()) * p.res * p.res
        row["density_pt_m2"] = float(cc.sum()) / cov_area if cov_area > 0 else math.nan
        row["ground_density_pt_m2"] = float(cc[2]) / cov_area if cov_area > 0 else math.nan
        zg = dem[g]
        row["gl_z_med"] = _q(zg, 0.5)
        row["gl_z_p05"] = _q(zg, 0.05)
        row["gl_z_p95"] = _q(zg, 0.95)
        row["dsm_z_med"] = _q(dsm[cov], 0.5)
        row.update(_stats(_grad_mag(dem, p.res), "slope025_pct"))
        d2 = _block_mean(dem, p.slope2m_block, p.slope2m_min_valid)
        row.update(_stats(_grad_mag(d2, p.res * p.slope2m_block), "slope2m_pct"))
        # PLATEAU DEM(5 m TIN を 2 m に焼いた nav1_dem)との差
        if nav_dem is not None:
            nv, nm = nav_dem
            ns = _sample_grid(nv, nm["ox"], nm["oy"], nm["res"], cx, cy)
            ok = g & np.isfinite(ns)
            dd = dem[ok] - ns[ok]
            row["pc_minus_plateau_dem_med"] = _q(dd, 0.5)
            row["pc_minus_plateau_dem_p05"] = _q(dd, 0.05)
            row["pc_minus_plateau_dem_p95"] = _q(dd, 0.95)
            row["pc_minus_plateau_dem_mae"] = float(np.abs(dd).mean()) if dd.size else math.nan
        # DSM−DEM(埋めた 1 m の DEM)
        fz = _sample_grid(fill1, m1["ox"], m1["oy"], m1["res"], cx, cy)
        h = dsm - fz
        hv = cov & np.isfinite(h)
        hh = h[hv]
        inband = (hh >= p.deck_h_min_m) & (hh <= p.deck_h_max_m)
        row["h_px"] = int(hh.size)
        row["h3_8_frac"] = float(inband.mean()) if hh.size else math.nan
        row["h3_8_mode_m"] = _mode(hh, p.deck_h_min_m, p.deck_h_max_m, p.mode_bin_m)
        row["h_gt8_frac"] = float((hh > p.deck_h_max_m).mean()) if hh.size else math.nan
        row["h_lt05_frac"] = float((hh < 0.5).mean()) if hh.size else math.nan
        # 建物の外形を除いた版
        in_rect = math.nan
        if bldg_rect is not None:
            ix0 = max(cell_rect[0], bldg_rect[0])
            ix1 = min(cell_rect[2], bldg_rect[2])
            iy0 = max(cell_rect[1], bldg_rect[1])
            iy1 = min(cell_rect[3], bldg_rect[3])
            in_rect = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0) / (CELL_M * CELL_M)
        row["bldg_mask_cover"] = in_rect
        if bldg is not None and isinstance(in_rect, float) and in_rect >= 0.999:
            bm = bldg.get(c, np.zeros((TILE, TILE), dtype=bool))
            row["bldg_px_frac"] = float(bm.mean())
            hn = h[hv & ~bm]
            row["h3_8_frac_nobldg"] = float(((hn >= p.deck_h_min_m) & (hn <= p.deck_h_max_m)).mean()) if hn.size \
                else math.nan
            row["h3_8_mode_m_nobldg"] = _mode(hn, p.deck_h_min_m, p.deck_h_max_m, p.mode_bin_m)
        else:
            row["bldg_px_frac"] = math.nan
            row["h3_8_frac_nobldg"] = math.nan
            row["h3_8_mode_m_nobldg"] = math.nan
        # 橋梁の外形の中
        row["brid_px"] = 0
        for key in ("brid_dsm_z_med", "brid_plateau_top_z_med", "brid_h_med", "brid_h3_8_frac",
                    "brid_dsm_minus_top_med"):
            row[key] = math.nan
        if brid is not None and c in brid[0]:
            bid, btop = brid[0][c], brid[1][c]
            fp = bid >= 0
            row["brid_px"] = int(fp.sum())
            sel = fp & cov
            if sel.any():
                row["brid_dsm_z_med"] = _q(dsm[sel], 0.5)
                row["brid_plateau_top_z_med"] = _q(btop[fp], 0.5)
                hb = h[sel & np.isfinite(h)]
                row["brid_h_med"] = _q(hb, 0.5)
                row["brid_h3_8_frac"] = float(((hb >= p.deck_h_min_m) & (hb <= p.deck_h_max_m)).mean()) \
                    if hb.size else math.nan
                row["brid_dsm_minus_top_med"] = _q(dsm[sel] - btop[sel], 0.5)
            for sid in np.unique(bid[fp]).tolist():
                s = bid == sid
                acc = brid_acc.setdefault(int(sid), {"top": [], "dsm": [], "fill": [], "cols": []})
                acc["top"].append(btop[s])
                acc["dsm"].append(dsm[s])
                acc["fill"].append(fz[s])
                acc["cols"].append(c)
        # 段差と歩道の縁(試み)
        # 0.25 m(発注の格子)と 0.5 m(2×2 の平均=地盤点の抜けを減らした版)の 2 通り
        sw = None if sidewalk is None else sidewalk.get(c)
        rw = None if roadway is None else roadway.get(c)
        row["sidewalk_px"] = int(sw.sum()) if sw is not None else 0
        curb = None
        if sw is not None and rw is not None:
            curb = sw & _dilate(rw, p.near_px)
        row["curb_px"] = int(curb.sum()) if curb is not None else 0
        for tag, f in (("025", 1), ("05", 2)):
            zt = dem if f == 1 else _block_mean(dem, f, 1)
            mk, n_step, n_eval = detect_steps(zt, p)
            gt = np.isfinite(zt)
            if f > 1:
                mk = np.repeat(np.repeat(mk, f, axis=0), f, axis=1)
                gt = np.repeat(np.repeat(gt, f, axis=0), f, axis=1)
            tot = curb_tot[tag]
            row[f"n_step_edges_{tag}"] = n_step
            row[f"n_eval_edges_{tag}"] = n_eval
            row[f"step_edge_rate_{tag}"] = n_step / n_eval if n_eval else math.nan
            tot["n_step_edges"] += n_step
            tot["n_eval_edges"] += n_eval
            for key in ("curb_step_near_frac", "curb_ground_near_frac", "curb_enrichment", "curb_recall",
                        "curb_recall_base"):
                row[f"{key}_{tag}"] = math.nan
            if curb is None or not curb.any():
                continue
            m_ = _curb_metrics(mk, gt, curb, p.near_px)
            row[f"curb_step_near_frac_{tag}"] = m_["step_near_frac"]
            row[f"curb_ground_near_frac_{tag}"] = m_["ground_near_frac"]
            row[f"curb_enrichment_{tag}"] = m_["enrichment"]
            row[f"curb_recall_{tag}"] = m_["recall"]
            row[f"curb_recall_base_{tag}"] = m_["recall_base"]
            for k_ in CURB_COUNT_KEYS:
                tot[k_] += m_[k_]
        col_rows[c] = row
    # セル間の坂(東西南北)
    zmed = {c: r.get("gl_z_med", math.nan) for c, r in col_rows.items()}
    for c, r in col_rows.items():
        cx, cy = int(grid.ix[c]), int(grid.iy[c])
        z0 = zmed[c]
        dz = {}
        for name, (dx, dy) in (("east", (1, 0)), ("west", (-1, 0)), ("north", (0, 1)), ("south", (0, -1))):
            nb = grid.col(cx + dx, cy + dy)
            dz[name] = (zmed.get(nb, math.nan) - z0) if nb >= 0 else math.nan
        r["nb_dz_east_m"] = dz["east"]
        r["nb_dz_north_m"] = dz["north"]
        vals = [abs(v) for v in dz.values() if isinstance(v, float) and math.isfinite(v)]
        r["nb_grade_max_pct"] = (max(vals) / CELL_M * 100.0) if vals else math.nan
        r["nb_n"] = len(vals)
    # 520 セルの行
    rows = []
    for pid, cix, ciy, band in zip(cells["place_id"], cells["ix"], cells["iy"], cells["band"]):
        c = grid.col(int(cix), int(ciy))
        base = dict(col_rows.get(c, {"has_data": False}))
        r = {"place_id": str(pid), "ix": int(cix), "iy": int(ciy), "band": str(band),
             "values_from_gl_place_id": f"g{int(cix)}_{int(ciy)}_GL"}
        r.update(base)
        if band == "UG":
            r["layer_floor_z"] = math.nan
            r["layer_floor_source"] = "absent_declared"
            r["ug_floor_status"] = "absent_declared"
            r["ug_floor_reason"] = UG_ABSENT_REASON
            r["deck_floor_confidence"] = ""
        elif band == "DECK":
            gz = base.get("gl_z_med", math.nan)
            if base.get("brid_px", 0) > 0 and math.isfinite(base.get("brid_dsm_z_med", math.nan)):
                r["layer_floor_z"] = base["brid_dsm_z_med"]
                r["layer_floor_source"] = "dsm_in_plateau_brid_footprint"
            elif math.isfinite(base.get("h3_8_mode_m_nobldg", math.nan)) and math.isfinite(gz):
                r["layer_floor_z"] = gz + base["h3_8_mode_m_nobldg"]
                r["layer_floor_source"] = "gl_z_med+h3_8_mode_nobldg"
            elif math.isfinite(base.get("h3_8_mode_m", math.nan)) and math.isfinite(gz):
                r["layer_floor_z"] = gz + base["h3_8_mode_m"]
                r["layer_floor_source"] = "gl_z_med+h3_8_mode_all"
            else:
                r["layer_floor_z"] = math.nan
                r["layer_floor_source"] = "none"
            # 確からしさ: brid=PLATEAU 橋梁の外形の中の DSM(形の証拠がある)/ heuristic=h 3〜8 m の画素が
            # 1 つでもあれば最頻値が出る根拠の弱い推定(建物の外形の外の _all も値は残す=検収 M4・親の判断)
            r["deck_floor_confidence"] = {"dsm_in_plateau_brid_footprint": "brid",
                                          "gl_z_med+h3_8_mode_nobldg": "heuristic",
                                          "gl_z_med+h3_8_mode_all": "heuristic"}.get(r["layer_floor_source"], "none")
            r["ug_floor_status"] = ""
            r["ug_floor_reason"] = ""
        else:
            r["layer_floor_z"] = base.get("gl_z_med", math.nan)
            r["layer_floor_source"] = "gl_z_med" if base.get("has_data") else "none"
            r["deck_floor_confidence"] = ""
            r["ug_floor_status"] = ""
            r["ug_floor_reason"] = ""
        rows.append(r)
    # 橋梁の構造ごと
    brows = []
    for sid in range(n_brid):
        acc = brid_acc.get(sid)
        if acc is None:
            brows.append({"brid_idx": sid, "n_px": 0})
            continue
        top = np.concatenate(acc["top"])
        ds = np.concatenate(acc["dsm"])
        fl = np.concatenate(acc["fill"])
        ok = np.isfinite(ds) & np.isfinite(top)
        hh = (ds - fl)[ok & np.isfinite(fl)]
        cols = sorted(set(acc["cols"]))
        brows.append({
            "brid_idx": sid, "n_px": int(top.size), "n_px_with_dsm": int(ok.sum()),
            "plateau_top_z_med": _q(top[np.isfinite(top)], 0.5), "dsm_z_med": _q(ds[ok], 0.5),
            "dem_fill_z_med": _q(fl[ok & np.isfinite(fl)], 0.5), "h_med": _q(hh, 0.5),
            "h3_8_frac": float(((hh >= p.deck_h_min_m) & (hh <= p.deck_h_max_m)).mean()) if hh.size else math.nan,
            "dsm_minus_top_med": _q(ds[ok] - top[ok], 0.5),
            "plateau_top_minus_dem_med": _q((top - fl)[ok & np.isfinite(fl)], 0.5),
            "cells": ",".join(f"g{int(grid.ix[c])}_{int(grid.iy[c])}" for c in cols),
            "complete": all(col_rows.get(c, {}).get("complete", False) for c in cols),
        })
    return {"rows": rows, "brid_rows": brows, "curb_totals": curb_tot,
            "mosaic": {"raw": raw1, "filled": fill1, "dsm": dsm1, "meta": m1}}


# ---------------------------------------------------------------------------------- 性能
def peak_rss_bytes() -> dict[str, int | None]:
    """いまの作業集合と最大(Windows は psapi・ほかは resource)。"""
    try:
        if sys.platform == "win32":
            from ctypes import wintypes

            class PMC(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                            ("PeakPagefileUsage", ctypes.c_size_t)]

            pmc = PMC()
            pmc.cb = ctypes.sizeof(PMC)
            k32 = ctypes.WinDLL("kernel32")
            k32.GetCurrentProcess.restype = wintypes.HANDLE
            fn = k32.K32GetProcessMemoryInfo
            fn.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
            if fn(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
                return {"working_set": int(pmc.WorkingSetSize), "peak_working_set": int(pmc.PeakWorkingSetSize),
                        "peak_private": int(pmc.PeakPagefileUsage)}
        else:  # pragma: no cover
            import resource
            return {"working_set": None, "peak_working_set": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                    "peak_private": None}
    except Exception:  # pragma: no cover - 計器の失敗で集計を止めない
        pass
    return {"working_set": None, "peak_working_set": None, "peak_private": None}


# ---------------------------------------------------------------------------------- 通し
def _process_one(args: tuple) -> MeshPartial:
    las_path, mesh, grid, info, params = args
    return bin_mesh(las_path, mesh, grid, info, params)


def _finite_or_none(v):
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def _summ(a: Sequence[float]) -> dict[str, float | int | None]:
    x = np.array([v for v in a if v is not None and isinstance(v, (int, float)) and math.isfinite(v)], dtype=float)
    if x.size == 0:
        return {"n": 0}
    return {"n": int(x.size), "p05": float(np.quantile(x, 0.05)), "p25": float(np.quantile(x, 0.25)),
            "med": float(np.median(x)), "p75": float(np.quantile(x, 0.75)), "p95": float(np.quantile(x, 0.95)),
            "max": float(x.max())}


def load_plateau_inputs(udx: Path | None, plateau_dir: Path | None, grid: Grid, params: AggParams,
                        log=print) -> dict[str, Any]:
    """PLATEAU の道路の面(歩道・車道)・建物の外形・橋梁の外形 → 柱ごとの画素。無ければ空(記録に注)。"""
    out: dict[str, Any] = {"notes": {}}
    if udx is not None and Path(udx).exists():
        from shibuya.build.space import sources as S  # 読むだけ(src は触らない)

        t = time.perf_counter()
        X0, Y0, X1, Y1 = grid.extent()
        roads, st = S.read_tran_roads(_guard(Path(udx)), (X0, Y0, X1, Y1))
        swp, rwp = [], []
        for r in roads:
            for code, _lod, rings in r.areas:
                if code in SIDEWALK_CODES:
                    swp += _polygons_of_rings(rings)
                elif 1000 <= code < 2000:
                    rwp += _polygons_of_rings(rings)
        out["sidewalk"] = rasterize_polygons(swp, grid, params.res)
        out["roadway"] = rasterize_polygons(rwp, grid, params.res)
        out["notes"]["tran"] = dict(st, n_sidewalk_polygons=len(swp), n_roadway_polygons=len(rwp),
                                    sec=round(time.perf_counter() - t, 2))
        log(f"[pc-agg] 道路の面 歩道 {len(swp)}・車道 {len(rwp)} 多角形 ({time.perf_counter() - t:.1f} s)")
    else:
        out["notes"]["tran"] = "無し(道路の面を読まない=歩道の試みは空欄)"
    if plateau_dir is not None and Path(plateau_dir).exists():
        pdir = _guard(Path(plateau_dir))
        mesh_npz = pdir / "plateau_mesh.npz"
        idx_json = pdir / "plateau_index.json"
        if mesh_npz.exists() and idx_json.exists():
            t = time.perf_counter()
            z = np.load(mesh_npz)
            out["bldg"] = rasterize_building_mask(z["V"], z["F"], grid, params)
            bb = json.loads(idx_json.read_bytes().decode("utf-8"))["bbox"]
            out["bldg_rect"] = tuple(float(v) for v in bb)
            out["notes"]["bldg"] = {"n_triangles": int(z["F"].shape[0]), "rect_local": bb,
                                    "sec": round(time.perf_counter() - t, 2)}
            log(f"[pc-agg] 建物の外形 {len(out['bldg'])} 柱 ({time.perf_counter() - t:.1f} s)")
        if (pdir / "extras.npz").exists() and (pdir / "extras.json").exists():
            from shibuya.build.space import sources as S

            t = time.perf_counter()
            structs, st = S.read_brid_triangles(pdir)
            out["brid"] = rasterize_bridges(structs, grid, params)
            out["n_brid"] = len(structs)
            out["notes"]["brid"] = dict(st, n_cols=len(out["brid"][0]), sec=round(time.perf_counter() - t, 2))
            log(f"[pc-agg] 橋梁 {len(structs)} 構造 ({time.perf_counter() - t:.1f} s)")
    else:
        out["notes"]["plateau_dir"] = "無し"
    return out


def run(raw_dir: Path, cells_path: Path, out_dir: Path, *, meshes: Sequence[str] | None = None, jobs: int = 1,
        mesh_index: Path, nav_dem_path: Path | None = None, nav_meta_path: Path | None = None,
        plateau_udx: Path | None = None, plateau_dir: Path | None = None, params: AggParams = AggParams(),
        save_rasters: bool = True, log=print) -> dict[str, Any]:
    t_all = time.perf_counter()
    raw_dir = _guard(Path(raw_dir))
    out_dir = Path(out_dir)
    cells = load_cells(cells_path)
    grid = Grid.from_pairs(zip(cells["ix"].tolist(), cells["iy"].tolist()))
    index = load_mesh_index(mesh_index)
    done_log, ignored = parse_fetch_log(raw_dir / "_fetch_log.tsv") if (raw_dir / "_fetch_log.tsv").exists() \
        else ({}, [])
    want = list(meshes) if meshes else sorted(m for m in index if m in done_log)
    skipped: list[dict[str, str]] = []
    todo: list[tuple[str, Path]] = []
    for m in want:
        if m not in index:
            skipped.append({"mesh": m, "why": "図郭の索引に無い"})
            continue
        zp = raw_dir / f"{m}.zip"
        if not zp.exists():
            skipped.append({"mesh": m, "why": "zip が無い"})
            continue
        todo.append((m, zp))
    mesh_stats: dict[str, dict[str, Any]] = {}
    las_paths: list[tuple[str, Path]] = []
    for m, zp in todo:
        t = time.perf_counter()
        zb = zp.read_bytes()
        zsha = _sha256_bytes(zb)
        zlen = len(zb)
        del zb
        lg = done_log.get(m)
        if lg is not None and (lg["sha256"] != zsha or lg["bytes"] != zlen):
            skipped.append({"mesh": m, "why": "zip の sha256/大きさが取得ログと違う(取得の途中か)"})
            continue
        lp, meta = extract_las(zp, raw_dir / "las", m)
        meta.update({"zip": _rel(zp), "zip_bytes": zlen, "zip_sha256": zsha,
                     "zip_sha256_log": lg["sha256"] if lg else None,
                     "zip_sha256_match": (lg["sha256"] == zsha) if lg else None,
                     "fetch_end_utc": lg["end_utc"] if lg else None, "url": (lg or {}).get("url") or index[m]["url"],
                     "las": _rel(lp), "sec_extract": round(time.perf_counter() - t, 3)})
        mesh_stats[m] = meta
        las_paths.append((m, lp))
        log(f"[pc-agg] {m} 展開 {'使い回し' if meta['reused'] else '済'} ({meta['sec_extract']} s)")
    store = TileStore(grid)
    args = [(lp, m, grid, index.get(m), params) for m, lp in las_paths]
    if jobs > 1 and len(args) > 1:
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            parts = ex.map(_process_one, args)
            for part in parts:
                store.merge(part)
                mesh_stats[part.mesh].update(part.stats)
                mesh_stats[part.mesh]["rss_after"] = peak_rss_bytes()
                log(f"[pc-agg] {part.mesh} 点 {part.stats['n_points']:,} ({part.stats['sec_total']} s)")
                del part
    else:
        for a in args:
            part = _process_one(a)
            store.merge(part)
            mesh_stats[part.mesh].update(part.stats)
            mesh_stats[part.mesh]["rss_after"] = peak_rss_bytes()
            log(f"[pc-agg] {part.mesh} 点 {part.stats['n_points']:,} ({part.stats['sec_total']} s)")
            del part
    t_pl = time.perf_counter()
    pl = load_plateau_inputs(plateau_udx, plateau_dir, grid, params, log=log)
    sec_plateau = time.perf_counter() - t_pl
    nav = None
    if nav_dem_path is not None and Path(nav_dem_path).exists() and nav_meta_path is not None \
            and Path(nav_meta_path).exists():
        nv = np.load(_guard(Path(nav_dem_path)))
        nm = json.loads(_guard(Path(nav_meta_path)).read_bytes().decode("utf-8"))["dem"]
        nav = (nv, nm)
    t_ag = time.perf_counter()
    mesh_rects = {m: mesh_local_rect(v) for m, v in index.items()}
    res = aggregate(store, grid, cells, mesh_rects, [m for m, _ in las_paths], params, nav_dem=nav,
                    sidewalk=pl.get("sidewalk"), roadway=pl.get("roadway"), bldg=pl.get("bldg"),
                    bldg_rect=pl.get("bldg_rect"), brid=pl.get("brid"), n_brid=pl.get("n_brid", 0))
    sec_agg = time.perf_counter() - t_ag
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = res["rows"]
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    cols: dict[str, list] = {k: [r.get(k) for r in rows] for k in keys}
    tbl = pa.table({k: pa.array([_finite_or_none(v) if not isinstance(v, bool) else v for v in vs])
                    for k, vs in cols.items()})
    pq.write_table(tbl, out_dir / "pc_cells.parquet")
    if res["brid_rows"]:
        bkeys: list[str] = []
        for r in res["brid_rows"]:
            for k in r:
                if k not in bkeys:
                    bkeys.append(k)
        btbl = pa.table({k: pa.array([_finite_or_none(r.get(k)) for r in res["brid_rows"]]) for k in bkeys})
        pq.write_table(btbl, out_dir / "pc_brid_structures.parquet")
    mo = res["mosaic"]
    if save_rasters:
        np.save(out_dir / "pc_dem1m_raw.npy", mo["raw"])
        np.save(out_dir / "pc_dem1m_filled.npy", mo["filled"])
        np.save(out_dir / "pc_dsm1m.npy", mo["dsm"])
    # 要約
    def _band(b):
        return [r for r in rows if r["band"] == b]

    gl_full = [r for r in _band("GL") if r.get("complete") and r.get("has_data")]
    curb_sum: dict[str, Any] = {}
    for tag, ct in res["curb_totals"].items():
        d = dict(ct)
        d.update(_curb_ratios(ct))
        d["step_edge_rate"] = ct["n_step_edges"] / ct["n_eval_edges"] if ct["n_eval_edges"] else math.nan
        d["n_cols_with_curb"] = sum(1 for r in rows if r["band"] == "GL" and (r.get("curb_px") or 0) > 0)
        curb_sum[tag] = d
    deck = _band("DECK")
    summary = {
        "tool": TOOL_VERSION, "params": params.as_dict(),
        "inputs": {"raw_dir": _rel(raw_dir), "cells": _rel(cells_path), "mesh_index": _rel(mesh_index),
                   "nav_dem": _rel(nav_dem_path) if nav is not None else None,
                   "plateau_udx": _rel(plateau_udx) if plateau_udx else None,
                   "plateau_dir": _rel(plateau_dir) if plateau_dir else None},
        "n_meshes_index": len(index), "n_meshes_done": len(las_paths),
        "meshes_done": [m for m, _ in las_paths], "meshes_skipped": skipped, "fetch_log_ignored_rows": ignored,
        "meshes": mesh_stats,
        "cells": {
            "n_rows": len(rows), "by_band": {b: len(_band(b)) for b in ("GL", "DECK", "UG")},
            "n_cols": grid.n, "n_cols_with_data": len(store.dem),
            "n_cols_complete": len({(r["ix"], r["iy"]) for r in rows if r.get("complete")}),
            "gl_complete_with_data": len(gl_full),
            "gl_slope2m_med_pct": _summ([r.get("slope2m_pct_med") for r in gl_full]),
            "gl_slope2m_p95_pct": _summ([r.get("slope2m_pct_p95") for r in gl_full]),
            "gl_slope025_med_pct": _summ([r.get("slope025_pct_med") for r in gl_full]),
            "gl_nb_grade_max_pct": _summ([r.get("nb_grade_max_pct") for r in gl_full]),
            "gl_z_med": _summ([r.get("gl_z_med") for r in gl_full]),
            "gl_ground_density_pt_m2": _summ([r.get("ground_density_pt_m2") for r in gl_full]),
            "gl_coverage_frac": _summ([r.get("coverage_frac") for r in gl_full]),
            "pc_minus_plateau_dem_med": _summ([r.get("pc_minus_plateau_dem_med") for r in gl_full]),
            "pc_minus_plateau_dem_mae": _summ([r.get("pc_minus_plateau_dem_mae") for r in gl_full]),
            "gl_h3_8_frac": _summ([r.get("h3_8_frac") for r in gl_full]),
            "gl_h3_8_frac_nobldg": _summ([r.get("h3_8_frac_nobldg") for r in gl_full]),
            "deck_with_data": sum(1 for r in deck if r.get("has_data")),
            "deck_complete": sum(1 for r in deck if r.get("complete")),
            "deck_layer_floor_source": {s: sum(1 for r in deck if r.get("layer_floor_source") == s)
                                        for s in sorted(set(r.get("layer_floor_source", "") for r in deck))},
            "deck_floor_confidence": {s: sum(1 for r in deck if r.get("deck_floor_confidence") == s)
                                      for s in sorted(set(r.get("deck_floor_confidence", "") for r in deck))},
            "deck_floor_minus_gl_m": _summ([(r.get("layer_floor_z") - r.get("gl_z_med"))
                                            if r.get("has_data") and r.get("layer_floor_z") is not None
                                            and math.isfinite(r.get("layer_floor_z", math.nan))
                                            and math.isfinite(r.get("gl_z_med", math.nan)) else None
                                            for r in deck]),
            "deck_h3_8_mode_m": _summ([r.get("h3_8_mode_m") for r in deck if r.get("has_data")]),
            "deck_brid_h_med": _summ([r.get("brid_h_med") for r in deck if r.get("has_data")]),
            "ug_absent_declared": sum(1 for r in _band("UG") if r.get("ug_floor_status") == "absent_declared"),
        },
        "brid_structures": {"n": len(res["brid_rows"]),
                            "n_with_px": sum(1 for r in res["brid_rows"] if r.get("n_px", 0) > 0),
                            "h_med": _summ([r.get("h_med") for r in res["brid_rows"]]),
                            "dsm_minus_top_med": _summ([r.get("dsm_minus_top_med") for r in res["brid_rows"]])},
        "curb_trial": curb_sum,
        "plateau_notes": pl["notes"],
        "mosaic_1m": mo["meta"],
        "perf": {"sec_total": round(time.perf_counter() - t_all, 2), "sec_plateau": round(sec_plateau, 2),
                 "sec_aggregate": round(sec_agg, 2), "rss": peak_rss_bytes(), "jobs": jobs},
        "outputs": ["pc_cells.parquet"] + (["pc_brid_structures.parquet"] if res["brid_rows"] else [])
        + (["pc_dem1m_raw.npy", "pc_dem1m_filled.npy", "pc_dsm1m.npy"] if save_rasters else []),
    }
    (out_dir / "pc_summary.json").write_text(
        json.dumps(_clean(summary), ensure_ascii=False, indent=1, default=_json_default, allow_nan=False),
        encoding="utf-8", newline="\n")
    return summary


def _clean(o):
    """JSON に NaN/inf を書かない(None に)。"""
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (float, np.floating)):
        v = float(o)
        return v if math.isfinite(v) else None
    if isinstance(o, np.integer):
        return int(o)
    return o


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        v = float(o)
        return v if math.isfinite(v) else None
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, tuple):
        return list(o)
    return str(o)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--raw-dir", required=True, type=Path)
    ap.add_argument("--cells", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--meshes", default="", help="カンマ区切り。省けば取得ログで完了した全部")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--mesh-index", type=Path,
                    default=Path("data/spatial/tokyo_pointcloud_23ku/lp_mesh_selected_520cells.json"))
    ap.add_argument("--nav-dem", type=Path, default=Path("data/world/v2/nav1_dem.npy"))
    ap.add_argument("--nav-meta", type=Path, default=Path("data/world/v2/nav1_meta.json"))
    ap.add_argument("--plateau-udx", type=Path,
                    default=Path("data/realworld/plateau_2025/13113_shibuya-ku_pref_2025_citygml_1_op/udx"))
    ap.add_argument("--plateau-dir", type=Path, default=Path("data/plateau"))
    ap.add_argument("--no-rasters", action="store_true")
    a = ap.parse_args(argv)
    meshes = [m.strip() for m in a.meshes.split(",") if m.strip()] or None
    s = run(a.raw_dir, a.cells, a.out, meshes=meshes, jobs=a.jobs, mesh_index=a.mesh_index,
            nav_dem_path=a.nav_dem, nav_meta_path=a.nav_meta, plateau_udx=a.plateau_udx,
            plateau_dir=a.plateau_dir, save_rasters=not a.no_rasters)
    print(json.dumps({"n_meshes_done": s["n_meshes_done"], "skipped": s["meshes_skipped"],
                      "perf": s["perf"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
