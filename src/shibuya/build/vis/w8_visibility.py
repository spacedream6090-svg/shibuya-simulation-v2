"""W8 可視性テーブル(§1 W8・D-W9)。

D-W9 の決定: 街路面のみ(道路8mバッファ・2.5m格子)・**層別**グリッド・UG は地下街のみ・
眼高 1.5m + 地形 2.5D・T1 疎リスト + T2 セル→セル・M10 ≤512MB・ハッシュ三役。

視点 = W10 が書いた ``w10_street_points.parquet`` の点集合を**そのまま**使う
(W8/W9/W10 が同一の台を共有する=D-W9 の「239,028点」に対応する行)。

対象(target)
  1. POI 点(W6 ``w6_poi``・店先) 2. 駅出入口(W11 ``w11_station_exits``)
  3. 建物(W4 ``w4_buildings`` の重心・頂部 z=地盤+h)= 「その建物が見えるか」の判定

視線判定(2.5D)
  視点→対象を ``step_m`` 刻みで標本化し、標本位置の**建物頂部高さ場**が視線 z(端点間の線形補間)
  を超えたら遮蔽。高さ場は建物 footprint を 2.5m 格子へ走査線ラスタ化したもの
  (owner=その格子を占める建物・top_z=地盤+h)。建物の無い格子は DEM の地盤高
  (=地形遮蔽)。対象自身の建物が占める格子は地盤高で評価する(自分の建物で自分が隠れない)。
  視点から ``near_skip_m`` 以内の標本は評価しない(視点が庇・駅構内の格子に落ちる場合の自己遮蔽回避)。

**仕様との差分(宣言)**: 仕様原文は「標本が建物 footprint の内側か」を多角形内外判定で問う。
本実装は同じ判定を **2.5m 格子へラスタ化**して行う(横方向誤差 ≤1.25m = 標本刻みと同程度)。
理由は前計算 ≤5分(§1 W8 ゲート)。多角形内外判定を 6千万対×60標本に対して行うと桁で超過する。

expedient(すべて感度試験対象)
- 眼高 1.5m・道路8mバッファ・2.5D(D-W9 既決)。
- 最大視程 150m(視野角を持たない=全方位)。根拠なし=感度 100m/200m。
- 遮蔽の 2.5m ラスタ近似(上記の差分)。
- 建物の基準地盤高 = 重心の DEM 値(1棟1値)。
- DEM 範囲外(x>1003.7m 等)は端の値でクランプ。
- DECK 視点の眼高 = GL と同じ(デッキ床高のデータが無い)。
- UG は建物ラスタを適用しない(地下街の内部形状が無い)=距離のみで可視。
- T1 の1視点あたり上限 256 件(打ち切り件数をヘッダに出す)。
- T2 のセル対サンプル = 決定論的な粗サンプル(≤200 対/セル対)。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from numba import njit, prange

from ..geo import common as C

STAGE = "W8"
STAGE_VERSION = "1.0.0"

#: 眼高 [m](D-W9)。
EYE_M = 1.5
#: 視線標本の刻み [m](= 格子ピッチ)。
STEP_M = 2.5
#: 遮蔽ラスタのピッチ [m](= 街路格子ピッチ)。
RASTER_M = 2.5
#: 最大視程 [m](expedient)。
MAX_RANGE_M = 150.0
#: 視点近傍の遮蔽を見ない距離 [m]。
NEAR_SKIP_M = 2.5
#: 対象探索の bin 幅 [m](一様格子索引)。
TARGET_BIN_M = 50.0
#: 1視点あたりの可視対象の上限(T1 の行長)。
MAX_T1_PER_POINT = 256
#: T2 のセル対あたりの視点対サンプル上限。
T2_MAX_PAIRS = 200
#: T2 を評価するセル代表点間の最大距離 [m](超えたら 0 とみなす)。
T2_MAX_CELL_DIST_M = MAX_RANGE_M + 200.0
#: 視点をチャンクに切る幅(作業バッファの上限を決める)。
CHUNK = 20_000
#: 遮蔽ラスタの余白 [m]。
SCENE_MARGIN_M = 30.0

#: バンド → 見える対象のバンド(D-W9 の層分離)。
BAND_TARGETS: dict[str, tuple[str, ...]] = {
    "GL": ("GL", "DECK"),
    "DECK": ("GL", "DECK"),
    "UG": ("UG",),
}
#: 対象の種別コード(出力の ``kind_code``)。
TARGET_KINDS: tuple[str, ...] = ("poi", "exit", "building")


def _write_table(out_dir, name: str, table: pa.Table) -> dict[str, Any]:
    """Arrow テーブル → Parquet(``geo.common.write_parquet`` と同じ設定・list 列を通すため)。"""
    path = out_dir / name
    pq.write_table(table, path, **C._PARQUET_KW)
    return {
        "path": path.relative_to(out_dir).as_posix(),
        "sha256": C.sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": table.num_rows,
    }


# ------------------------------------------------------------------ 場面(高さ場)


@dataclass(frozen=True)
class Scene:
    """遮蔽ラスタ。``ground_z``/``top_z``/``owner`` は同じ (ny, nx) 格子。"""

    x0: float
    y0: float
    pitch: float
    nx: int
    ny: int
    ground_z: np.ndarray  # float32 (ny, nx) 地盤高 [m]
    top_z: np.ndarray  # float32 (ny, nx) 建物頂部高(建物が無ければ地盤高)
    owner: np.ndarray  # int32 (ny, nx) 建物 index(無ければ -1)
    max_top_z: float
    n_filled: int
    dem_clamped: int

    def sample_ground(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        ix = np.clip(((x - self.x0) / self.pitch).astype(np.int64), 0, self.nx - 1)
        iy = np.clip(((y - self.y0) / self.pitch).astype(np.int64), 0, self.ny - 1)
        return self.ground_z[iy, ix].astype(np.float64)


def _dem_sample(dem: np.ndarray, dx0: float, dy0: float, dcell: float, gx: np.ndarray, gy: np.ndarray) -> tuple[np.ndarray, int]:
    """DEM 最近傍サンプル。範囲外は端でクランプ(クランプ件数も返す)。"""
    ny, nx = dem.shape
    jx = np.floor((gx - dx0) / dcell + 0.5).astype(np.int64)
    jy = np.floor((gy - dy0) / dcell + 0.5).astype(np.int64)
    out_of_range = int(((jx < 0) | (jx >= nx) | (jy < 0) | (jy >= ny)).sum())
    np.clip(jx, 0, nx - 1, out=jx)
    np.clip(jy, 0, ny - 1, out=jy)
    return dem[jy, jx].astype(np.float32), out_of_range


@njit(cache=True, nogil=True)
def _rasterize(
    poly_start: np.ndarray,
    poly_count: np.ndarray,
    vx: np.ndarray,
    vy: np.ndarray,
    top: np.ndarray,
    x0: float,
    y0: float,
    pitch: float,
    nx: int,
    ny: int,
    top_z: np.ndarray,
    owner: np.ndarray,
) -> int:
    """建物 footprint を走査線で格子へ焼く(格子中心が多角形内なら占有)。

    重なりは **頂部が高い方**が勝つ(同値は先に処理した建物=index が小さい方)。
    """
    filled = 0
    xs = np.empty(64, dtype=np.float64)
    for b in range(poly_start.shape[0]):
        s = poly_start[b]
        n = poly_count[b]
        if n < 3:
            continue
        ymin = vy[s]
        ymax = vy[s]
        xmin = vx[s]
        xmax = vx[s]
        for k in range(s + 1, s + n):
            if vy[k] < ymin:
                ymin = vy[k]
            if vy[k] > ymax:
                ymax = vy[k]
            if vx[k] < xmin:
                xmin = vx[k]
            if vx[k] > xmax:
                xmax = vx[k]
        r0 = int(math.floor((ymin - y0) / pitch))
        r1 = int(math.ceil((ymax - y0) / pitch))
        if r0 < 0:
            r0 = 0
        if r1 > ny - 1:
            r1 = ny - 1
        zb = top[b]
        for r in range(r0, r1 + 1):
            yc = y0 + (r + 0.5) * pitch
            m = 0
            for k in range(s, s + n):
                k2 = k + 1 if k + 1 < s + n else s
                ay = vy[k]
                by = vy[k2]
                if (ay <= yc) != (by <= yc):
                    t = (yc - ay) / (by - ay)
                    if m < xs.shape[0]:
                        xs[m] = vx[k] + t * (vx[k2] - vx[k])
                        m += 1
            if m < 2:
                continue
            # 挿入ソート(m は小さい)
            for i in range(1, m):
                key = xs[i]
                j = i - 1
                while j >= 0 and xs[j] > key:
                    xs[j + 1] = xs[j]
                    j -= 1
                xs[j + 1] = key
            for i in range(0, m - 1, 2):
                cx0 = xs[i]
                cx1 = xs[i + 1]
                c0 = int(math.ceil((cx0 - x0) / pitch - 0.5))
                c1 = int(math.floor((cx1 - x0) / pitch - 0.5))
                if c0 < 0:
                    c0 = 0
                if c1 > nx - 1:
                    c1 = nx - 1
                for c in range(c0, c1 + 1):
                    if owner[r, c] < 0 or zb > top_z[r, c]:
                        if owner[r, c] < 0:
                            filled += 1
                        top_z[r, c] = zb
                        owner[r, c] = b
    return filled


def build_scene(
    footprints: list[np.ndarray],
    base_z: np.ndarray,
    heights: np.ndarray,
    dem: np.ndarray,
    dem_origin: tuple[float, float],
    dem_cell: float,
    bounds: tuple[float, float, float, float],
    pitch: float = RASTER_M,
) -> Scene:
    """建物 footprint + DEM → 遮蔽ラスタ(``Scene``)。"""
    x_lo, y_lo, x_hi, y_hi = bounds
    x0 = math.floor((x_lo - SCENE_MARGIN_M) / pitch) * pitch
    y0 = math.floor((y_lo - SCENE_MARGIN_M) / pitch) * pitch
    nx = int(math.ceil((x_hi + SCENE_MARGIN_M - x0) / pitch)) + 1
    ny = int(math.ceil((y_hi + SCENE_MARGIN_M - y0) / pitch)) + 1

    gx = x0 + (np.arange(nx, dtype=np.float64) + 0.5) * pitch
    gy = y0 + (np.arange(ny, dtype=np.float64) + 0.5) * pitch
    mx, my = np.meshgrid(gx, gy, indexing="xy")
    ground, clamped = _dem_sample(dem, dem_origin[0], dem_origin[1], dem_cell, mx, my)
    top_z = ground.copy()
    owner = np.full((ny, nx), -1, dtype=np.int32)

    counts = np.array([p.shape[0] for p in footprints], dtype=np.int64)
    starts = np.concatenate([[0], np.cumsum(counts)[:-1]]).astype(np.int64) if len(counts) else np.zeros(0, np.int64)
    flat = np.concatenate(footprints) if footprints else np.zeros((0, 2), np.float64)
    top = (base_z + heights).astype(np.float64)
    n_filled = _rasterize(
        starts,
        counts,
        np.ascontiguousarray(flat[:, 0]),
        np.ascontiguousarray(flat[:, 1]),
        top,
        x0,
        y0,
        pitch,
        nx,
        ny,
        top_z,
        owner,
    )
    return Scene(
        x0=x0,
        y0=y0,
        pitch=pitch,
        nx=nx,
        ny=ny,
        ground_z=ground,
        top_z=top_z,
        owner=owner,
        max_top_z=float(top_z.max()),
        n_filled=int(n_filled),
        dem_clamped=int(clamped),
    )


# ------------------------------------------------------------------ 視線カーネル


@njit(cache=True, nogil=True, inline="always")
def _los(
    px: float,
    py: float,
    pz: float,
    qx: float,
    qy: float,
    qz: float,
    q_owner: int,
    ground_z: np.ndarray,
    top_z: np.ndarray,
    owner: np.ndarray,
    x0: float,
    y0: float,
    pitch: float,
    nx: int,
    ny: int,
    step: float,
    near_skip: float,
) -> bool:
    """2.5D 視線(遮蔽が無ければ True)。"""
    dx = qx - px
    dy = qy - py
    dist = math.sqrt(dx * dx + dy * dy)
    if dist <= near_skip:
        return True
    n = int(dist / step)
    inv = 1.0 / dist
    ux = dx * inv
    uy = dy * inv
    for k in range(1, n + 1):
        s = k * step
        if s <= near_skip:
            continue
        if s >= dist:
            break
        sx = px + ux * s
        sy = py + uy * s
        c = int((sx - x0) / pitch)
        r = int((sy - y0) / pitch)
        if c < 0 or c >= nx or r < 0 or r >= ny:
            continue
        own = owner[r, c]
        if own == q_owner and own >= 0:
            zc = ground_z[r, c]
        else:
            zc = top_z[r, c]
        rz = pz + (qz - pz) * (s * inv)
        if zc > rz:
            return False
    return True


@njit(cache=True, parallel=True, nogil=True)
def _visible_targets(
    px: np.ndarray,
    py: np.ndarray,
    pz: np.ndarray,
    pgroup: np.ndarray,
    tx: np.ndarray,
    ty: np.ndarray,
    tz: np.ndarray,
    towner: np.ndarray,
    bin_start: np.ndarray,
    bin_ids: np.ndarray,
    bin_nx: int,
    bin_ny: int,
    bin_x0: float,
    bin_y0: float,
    bin_m: float,
    n_groups: int,
    ground_z: np.ndarray,
    top_z: np.ndarray,
    owner: np.ndarray,
    x0: float,
    y0: float,
    pitch: float,
    nx: int,
    ny: int,
    step: float,
    near_skip: float,
    max_range: float,
    cap: int,
    out_ids: np.ndarray,
    out_n: np.ndarray,
    out_trunc: np.ndarray,
) -> None:
    """視点チャンク × 対象 → 可視対象 id(``out_ids[i, :out_n[i]]``)。"""
    reach = int(max_range / bin_m) + 1
    for i in prange(px.shape[0]):
        g = pgroup[i]
        cnt = 0
        trunc = 0
        if g >= 0:
            bx = int((px[i] - bin_x0) / bin_m)
            by = int((py[i] - bin_y0) / bin_m)
            for jy in range(by - reach, by + reach + 1):
                if jy < 0 or jy >= bin_ny:
                    continue
                for jx in range(bx - reach, bx + reach + 1):
                    if jx < 0 or jx >= bin_nx:
                        continue
                    cell = (g * bin_ny + jy) * bin_nx + jx
                    for k in range(bin_start[cell], bin_start[cell + 1]):
                        t = bin_ids[k]
                        ddx = tx[t] - px[i]
                        ddy = ty[t] - py[i]
                        if ddx * ddx + ddy * ddy > max_range * max_range:
                            continue
                        if g == 1:
                            ok = True  # 地下街=遮蔽モデル無し(expedient)
                        else:
                            ok = _los(
                                px[i], py[i], pz[i],
                                tx[t], ty[t], tz[t], towner[t],
                                ground_z, top_z, owner,
                                x0, y0, pitch, nx, ny, step, near_skip,
                            )
                        if ok:
                            if cnt < cap:
                                out_ids[i, cnt] = t
                                cnt += 1
                            else:
                                trunc += 1
        out_n[i] = cnt
        out_trunc[i] = trunc


@njit(cache=True, parallel=True, nogil=True)
def _cell_pair_visibility(
    pair_a: np.ndarray,
    pair_b: np.ndarray,
    cell_start: np.ndarray,
    cell_pts: np.ndarray,
    px: np.ndarray,
    py: np.ndarray,
    pz: np.ndarray,
    ug: np.ndarray,
    ground_z: np.ndarray,
    top_z: np.ndarray,
    owner: np.ndarray,
    x0: float,
    y0: float,
    pitch: float,
    nx: int,
    ny: int,
    step: float,
    near_skip: float,
    max_range: float,
    max_pairs: int,
    out: np.ndarray,
) -> None:
    """セル対ごとの視点対サンプル → 見通し率。"""
    for p in prange(pair_a.shape[0]):
        ca = pair_a[p]
        cb = pair_b[p]
        a0 = cell_start[ca]
        na = cell_start[ca + 1] - a0
        b0 = cell_start[cb]
        nb = cell_start[cb + 1] - b0
        if na == 0 or nb == 0:
            out[p] = 0.0
            continue
        total = na * nb
        n_s = total if total < max_pairs else max_pairs
        hit = 0
        used = 0
        for k in range(n_s):
            i = cell_pts[a0 + (k * 7919) % na]
            j = cell_pts[b0 + (k * 104729) % nb]
            if i == j:
                continue
            ddx = px[j] - px[i]
            ddy = py[j] - py[i]
            used += 1
            if ddx * ddx + ddy * ddy > max_range * max_range:
                continue
            if ug[i] or ug[j]:
                if ug[i] and ug[j]:
                    hit += 1
                continue
            if _los(
                px[i], py[i], pz[i], px[j], py[j], pz[j], -1,
                ground_z, top_z, owner, x0, y0, pitch, nx, ny, step, near_skip,
            ):
                hit += 1
        out[p] = (hit / used) if used > 0 else 0.0


# ------------------------------------------------------------------ 段階本体


def _load_footprints(osm: dict) -> tuple[dict[str, int], list[np.ndarray]]:
    index: dict[str, int] = {}
    polys: list[np.ndarray] = []
    for b in osm["buildings"]:
        index[b["id"]] = len(polys)
        polys.append(np.asarray(b["footprint"], dtype=np.float64))
    return index, polys


def run(ctx: C.Ctx) -> C.StageResult:
    osm_p = ctx.osm()
    terrain_p = ctx.path("plateau", "terrain.npz")
    terrain_json_p = ctx.path("plateau", "terrain.json")
    b_p = ctx.out / "w4_buildings.parquet"
    poi_p = ctx.out / "w6_poi.parquet"
    exits_p = ctx.out / "w11_station_exits.parquet"
    pts_p = ctx.out / "w10_street_points.parquet"
    cells_p = ctx.out / "w2_cells.parquet"
    for p in (osm_p, terrain_p, terrain_json_p):
        if not p.exists():
            raise FileNotFoundError(f"W8 入力が無い: {p}")
    for p in (b_p, poi_p, exits_p, pts_p, cells_p):
        if not p.exists():
            raise FileNotFoundError(f"W8 は W2/W4/W6/W10/W11 の出力を必要とする: {p}")

    osm = C.load_json(osm_p)
    b_index, polys = _load_footprints(osm)
    tj = C.load_json(terrain_json_p)
    dem = np.load(terrain_p)["heights"]

    build = C.read_parquet_columns(b_p, ["building_id", "h_m", "centroid_x", "centroid_y"])
    order = [b_index[bid] for bid in build["building_id"]]
    fps = [polys[i] for i in order]
    bx = np.asarray(build["centroid_x"], dtype=np.float64)
    by = np.asarray(build["centroid_y"], dtype=np.float64)
    bh = np.asarray(build["h_m"], dtype=np.float64)

    pts = C.read_parquet_columns(pts_p, ["x", "y", "band"])
    vx = np.asarray(pts["x"], dtype=np.float64)
    vy = np.asarray(pts["y"], dtype=np.float64)
    vband = pts["band"]
    n_pts = vx.shape[0]
    #: 視点数の**独立な**読み(W10 の Parquet メタデータ行数)。T1 の行数ゲートの期待値に使う。
    n_viewpoints_w10 = int(pq.ParquetFile(pts_p).metadata.num_rows)

    bounds = (
        min(float(vx.min()), float(bx.min())),
        min(float(vy.min()), float(by.min())),
        max(float(vx.max()), float(bx.max())),
        max(float(vy.max()), float(by.max())),
    )
    # 建物の基準地盤高 = 重心の DEM 値(expedient)
    base_z, _ = _dem_sample(dem, tj["x0"], tj["y0"], tj["cell_m"], bx, by)
    scene = build_scene(
        fps, base_z.astype(np.float64), bh, dem, (tj["x0"], tj["y0"]), float(tj["cell_m"]), bounds
    )

    rastered = np.zeros(len(fps), dtype=bool)
    seen = np.unique(scene.owner)
    rastered[seen[seen >= 0]] = True
    buildings_not_rastered = int((~rastered).sum())

    vz = scene.sample_ground(vx, vy) + EYE_M
    band_arr = np.asarray(vband)
    is_ug = band_arr == "UG"
    pgroup = np.where(is_ug, 1, 0).astype(np.int32)

    # --- 対象表 ---
    poi = C.read_parquet_columns(poi_p, ["poi_id", "x", "y", "band", "building_id"])
    ex = C.read_parquet_columns(exits_p, ["exit_id", "x", "y", "band"])
    bid_to_idx = {bid: i for i, bid in enumerate(build["building_id"])}
    t_x: list[float] = []
    t_y: list[float] = []
    t_z: list[float] = []
    t_owner: list[int] = []
    t_kind: list[int] = []
    t_ref: list[str] = []
    t_band: list[str] = []
    for pid, x, y, band, bid in zip(
        poi["poi_id"], poi["x"], poi["y"], poi["band"], poi["building_id"]
    ):
        t_x.append(float(x))
        t_y.append(float(y))
        t_z.append(0.0)
        t_owner.append(bid_to_idx.get(bid, -1) if bid else -1)
        t_kind.append(0)
        t_ref.append(str(pid))
        t_band.append(str(band))
    for eid, x, y, band in zip(ex["exit_id"], ex["x"], ex["y"], ex["band"]):
        t_x.append(float(x))
        t_y.append(float(y))
        t_z.append(0.0)
        t_owner.append(-1)
        t_kind.append(1)
        t_ref.append(str(eid))
        t_band.append(str(band))
    n_pt_ex = len(t_x)
    for i, bid in enumerate(build["building_id"]):
        t_x.append(float(bx[i]))
        t_y.append(float(by[i]))
        t_z.append(0.0)
        t_owner.append(i)
        t_kind.append(2)
        t_ref.append(str(bid))
        t_band.append("GL")

    tx = np.asarray(t_x, dtype=np.float64)
    ty = np.asarray(t_y, dtype=np.float64)
    towner = np.asarray(t_owner, dtype=np.int32)
    tkind = np.asarray(t_kind, dtype=np.int8)
    tground = scene.sample_ground(tx, ty)
    tz = tground + EYE_M
    tz[n_pt_ex:] = (base_z[: bh.shape[0]].astype(np.float64) + bh)  # 建物=頂部 z
    n_targets = tx.shape[0]
    tband = np.asarray(t_band)
    tgroup = np.where(tband == "UG", 1, 0).astype(np.int32)

    # --- 対象の一様格子索引(グループ別)---
    bin_x0 = scene.x0
    bin_y0 = scene.y0
    bin_nx = int(math.ceil(scene.nx * scene.pitch / TARGET_BIN_M)) + 1
    bin_ny = int(math.ceil(scene.ny * scene.pitch / TARGET_BIN_M)) + 1
    n_groups = 2
    bx_i = np.clip(((tx - bin_x0) / TARGET_BIN_M).astype(np.int64), 0, bin_nx - 1)
    by_i = np.clip(((ty - bin_y0) / TARGET_BIN_M).astype(np.int64), 0, bin_ny - 1)
    cell_of = (tgroup.astype(np.int64) * bin_ny + by_i) * bin_nx + bx_i
    n_bins = n_groups * bin_ny * bin_nx
    counts = np.bincount(cell_of, minlength=n_bins)
    bin_start = np.concatenate([[0], np.cumsum(counts)]).astype(np.int64)
    order_ids = np.argsort(cell_of, kind="stable").astype(np.int32)
    bin_ids = order_ids

    # --- T1: 視点 → 可視対象 ---
    out_n = np.empty(n_pts, dtype=np.int32)
    out_trunc = np.empty(n_pts, dtype=np.int32)
    chunks_ids: list[np.ndarray] = []
    buf = np.empty((CHUNK, MAX_T1_PER_POINT), dtype=np.int32)
    nb = np.empty(CHUNK, dtype=np.int32)
    tb = np.empty(CHUNK, dtype=np.int32)
    for s in range(0, n_pts, CHUNK):
        e = min(s + CHUNK, n_pts)
        m = e - s
        _visible_targets(
            vx[s:e], vy[s:e], vz[s:e], pgroup[s:e],
            tx, ty, tz, towner,
            bin_start, bin_ids, bin_nx, bin_ny, bin_x0, bin_y0, TARGET_BIN_M, n_groups,
            scene.ground_z, scene.top_z, scene.owner,
            scene.x0, scene.y0, scene.pitch, scene.nx, scene.ny,
            STEP_M, NEAR_SKIP_M, MAX_RANGE_M, MAX_T1_PER_POINT,
            buf[:m], nb[:m], tb[:m],
        )
        out_n[s:e] = nb[:m]
        out_trunc[s:e] = tb[:m]
        for i in range(m):
            chunks_ids.append(buf[i, : nb[i]].copy())

    total_visible = int(out_n.sum())
    offsets = np.concatenate([[0], np.cumsum(out_n)]).astype(np.int64)
    values = np.concatenate(chunks_ids) if chunks_ids else np.zeros(0, np.int32)

    # --- セル写像(点 → w2_cells の行)---
    cells = C.read_parquet_columns(cells_p, ["place_id", "ix", "iy", "band", "centroid_x", "centroid_y"])
    cell_index = {pid: i for i, pid in enumerate(cells["place_id"])}
    n_cells = len(cells["place_id"])
    pt_cell = np.full(n_pts, -1, dtype=np.int32)
    for i in range(n_pts):
        ix, iy = C.grid_ij(float(vx[i]), float(vy[i]))
        pt_cell[i] = cell_index.get(C.place_id(ix, iy, vband[i]), -1)
    pts_without_cell = int((pt_cell < 0).sum())

    # --- T1 セル集約(セル → 可視対象 → 見えている視点数)---
    rep = np.repeat(pt_cell, out_n)
    keep = rep >= 0
    key = rep[keep].astype(np.int64) * n_targets + values[keep].astype(np.int64)
    uk, ucount = np.unique(key, return_counts=True)
    agg_cell = (uk // n_targets).astype(np.int32)
    agg_target = (uk % n_targets).astype(np.int32)

    # --- T2: セル → セル ---
    order_pt = np.argsort(pt_cell, kind="stable")
    valid = pt_cell[order_pt] >= 0
    cell_pts = order_pt[valid].astype(np.int32)
    cnt_cell = np.bincount(pt_cell[pt_cell >= 0], minlength=n_cells)
    cell_start = np.concatenate([[0], np.cumsum(cnt_cell)]).astype(np.int64)
    cxs = np.asarray(cells["centroid_x"], dtype=np.float64)
    cys = np.asarray(cells["centroid_y"], dtype=np.float64)
    d2 = (cxs[:, None] - cxs[None, :]) ** 2 + (cys[:, None] - cys[None, :]) ** 2
    ia, ib = np.nonzero(np.triu(d2 <= T2_MAX_CELL_DIST_M**2, k=0))
    pair_a = ia.astype(np.int32)
    pair_b = ib.astype(np.int32)
    t2_vals = np.zeros(pair_a.shape[0], dtype=np.float64)
    _cell_pair_visibility(
        pair_a, pair_b, cell_start, cell_pts, vx, vy, vz, is_ug,
        scene.ground_z, scene.top_z, scene.owner,
        scene.x0, scene.y0, scene.pitch, scene.nx, scene.ny,
        STEP_M, NEAR_SKIP_M, MAX_RANGE_M, T2_MAX_PAIRS, t2_vals,
    )
    t2 = np.zeros((n_cells, n_cells), dtype=np.float16)
    t2[pair_a, pair_b] = t2_vals.astype(np.float16)
    t2[pair_b, pair_a] = t2_vals.astype(np.float16)

    mean_visible = float(out_n.mean())
    zero_share = float((out_n == 0).mean())
    _vg = tgroup[values] if values.shape[0] else np.zeros(0, dtype=np.int32)
    _pg = np.repeat(pgroup, out_n)
    band_violations = int(np.count_nonzero(_vg != _pg))

    params: dict[str, Any] = {
        "eye_m": EYE_M,
        "step_m": STEP_M,
        "raster_pitch_m": RASTER_M,
        "max_range_m": MAX_RANGE_M,
        "near_skip_m": NEAR_SKIP_M,
        "target_bin_m": TARGET_BIN_M,
        "max_t1_per_point": MAX_T1_PER_POINT,
        "t2_max_pairs": T2_MAX_PAIRS,
        "t2_max_cell_dist_m": T2_MAX_CELL_DIST_M,
        "band_targets": {k: list(v) for k, v in sorted(BAND_TARGETS.items())},
        "target_kinds": list(TARGET_KINDS),
        "occlusion_model": "raster_2p5m_building_top_plus_dem",
        "view_angle_model": "omnidirectional(視野角なし)",
        "scene_margin_m": SCENE_MARGIN_M,
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash([osm_p, terrain_p, terrain_json_p, b_p, poi_p, exits_p, pts_p, cells_p]),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=["地形(起伏)", "建物", "街路(歩行グラフ)"],
        expedients=[
            "眼高 1.5m・道路8mバッファ・2.5D(D-W9 既決)",
            "最大視程 150m・視野角なし(全方位)",
            "遮蔽の 2.5m ラスタ近似(多角形内外判定の格子化=前計算5分の制約)",
            "建物の基準地盤高=重心の DEM 値(1棟1値)",
            "DEM 範囲外は端の値でクランプ",
            "DECK 視点の眼高=GL と同じ(デッキ床高が未取得)",
            "UG は建物ラスタを適用しない(地下街の内部形状が無い)",
            "T1 の1視点あたり上限 256 件",
            "T2 のセル対サンプル=決定論的な粗サンプル(≤200 対)",
        ],
        notes={
            "viewpoints": n_pts,
            "viewpoints_in_w10_street_points": n_viewpoints_w10,
            "viewpoints_by_band": {
                b: int((band_arr == b).sum()) for b in sorted(set(vband))
            },
            "targets_total": n_targets,
            "targets_by_kind": {
                TARGET_KINDS[k]: int((tkind == k).sum()) for k in range(len(TARGET_KINDS))
            },
            "targets_by_group": {"surface": int((tgroup == 0).sum()), "ug": int((tgroup == 1).sum())},
            "scene": {
                "nx": scene.nx,
                "ny": scene.ny,
                "pitch_m": scene.pitch,
                "cells_with_building": scene.n_filled,
                "max_top_z_m": round(scene.max_top_z, 2),
                "dem_out_of_range_cells": scene.dem_clamped,
                "buildings_without_raster_cell": buildings_not_rastered,
                "buildings_without_raster_cell_note": (
                    "2.5m 格子の中心を1つも含まない小さい建物は遮蔽に効かない(ラスタ近似の既知の穴)。"
                ),
            },
            "mean_visible_targets_per_viewpoint": round(mean_visible, 3),
            "median_visible_targets": int(np.median(out_n)),
            "share_viewpoints_zero_targets": round(zero_share, 5),
            "viewpoints_hitting_cap": int((out_trunc > 0).sum()),
            "truncated_pairs": int(out_trunc.sum()),
            "visible_pairs_total": total_visible,
            "points_without_cell": pts_without_cell,
            "t1_cell_rows": int(uk.shape[0]),
            "t2_pairs_evaluated": int(pair_a.shape[0]),
            "t2_mean_nonzero": round(float(t2_vals[t2_vals > 0].mean()) if (t2_vals > 0).any() else 0.0, 4),
            "spec_deviation": (
                "遮蔽判定を多角形内外判定ではなく 2.5m ラスタで行う(横方向誤差 ≤1.25m)。"
                "理由=前計算 ≤5分(§1 W8 ゲート)。"
            ),
        },
    )
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w8_targets.parquet",
            {
                "target_id": np.arange(n_targets, dtype=np.int32),
                "kind": [TARGET_KINDS[k] for k in tkind],
                "ref_id": t_ref,
                "x": tx.astype(np.float32),
                "y": ty.astype(np.float32),
                "z_m": tz.astype(np.float32),
                "band": list(tband),
                "building_idx": towner,
            },
        )
    )
    res.outputs.append(
        _write_table(
            ctx.out,
            "w8_t1.parquet",
            pa.table(
                {
                    "point_idx": pa.array(np.arange(n_pts, dtype=np.int32)),
                    "place_idx": pa.array(pt_cell),
                    "n_visible": pa.array(out_n),
                    "targets": pa.ListArray.from_arrays(
                        pa.array(offsets, type=pa.int32()), pa.array(values, type=pa.int32())
                    ),
                }
            ),
        )
    )
    # 書いた T1 を読み直して「W10 の視点が1つずつ・過不足なく載っているか」を検査する
    # (自明ゲートにしないため、期待値は入力=w10_street_points の行数から取る)。
    t1_written = np.asarray(
        C.read_parquet_columns(ctx.out / "w8_t1.parquet", ["point_idx"])["point_idx"],
        dtype=np.int64,
    )
    t1_rows_written = int(t1_written.shape[0])
    t1_each_viewpoint_once = bool(
        np.array_equal(np.sort(t1_written), np.arange(n_viewpoints_w10, dtype=np.int64))
    )
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w8_t1_cell.parquet",
            {
                "place_idx": agg_cell,
                "target_id": agg_target,
                "n_viewpoints": ucount.astype(np.int32),
            },
        )
    )
    res.outputs.append(C.write_npy(ctx.out, "w8_t2.npy", t2))
    total_bytes = sum(o["bytes"] for o in res.outputs)
    res.notes["output_bytes_total"] = total_bytes
    res.gates = [
        C.Gate("viewpoints", n_pts, None),
        C.Gate("targets", n_targets, None),
        C.Gate("output_bytes_le_m10_512mb", total_bytes, None, passed=total_bytes <= 512 * 1024 * 1024),
        C.Gate("mean_visible_targets_per_viewpoint", round(mean_visible, 3), None),
        C.Gate("share_viewpoints_zero_targets", round(zero_share, 5), None),
        C.Gate("t1_rows", t1_rows_written, n_viewpoints_w10),
        C.Gate("t1_each_viewpoint_index_once", t1_each_viewpoint_once, True),
        C.Gate("t2_shape", [int(t2.shape[0]), int(t2.shape[1])], [n_cells, n_cells]),
        C.Gate("t2_symmetric", bool(np.array_equal(t2, t2.T)), True),
        C.Gate("t2_in_unit_range", bool(((t2 >= 0) & (t2 <= 1)).all()), True),
        C.Gate("band_separation_violations", band_violations, 0),
    ]
    return res
