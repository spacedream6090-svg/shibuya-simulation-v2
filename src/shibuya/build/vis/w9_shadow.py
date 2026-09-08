"""W9 影グリッド(§1 W9・D-W10「5分刻み」)。

再生日1日ぶんについて、**5分刻み288面**の影ビットセットを街路格子点(=W8/W10 と同一の点集合)
の上に作る。``in_shadow=1`` は次のいずれか:
  (a) 太陽高度 ≤ 0(夜・薄明を含む=日照ゼロ) → その面は全ビット1
  (b) 点の眼位置(地盤+1.5m)から太陽方向へ伸ばした半直線が建物に当たる
  (c) バンドが UG(地下街)= 常に日陰(expedient)

出力は ``np.packbits`` した (288, ceil(N/8)) uint8。D-W10 の宣言予算は **≤10MB/再生日**。

太陽位置は W13(``field.w13_weather``)の NOAA 近似を**そのまま輸入**する
(``_solar_terms`` から赤緯・均時差を取り、同じ時角の式で高度と方位を出す)。
高度は ``w13_weather.solar_elevation_deg`` と一致することを単体テストで固定する。

expedient
- 影の最大追跡距離 300m(高さ231mの建物は低仰角でこれを超える影を落とすが打ち切る)。
- UG は常時日陰・DECK は GL と同じ扱い(デッキ床高が未取得)。
- 遮蔽は W8 と同じ 2.5m ラスタ(建物頂部高さ場)。
- 大気差・地形の遠方遮蔽(尾根越し)は見ない(ラスタ内の地盤高だけを見る)。
- 再生日 = W13 ``w13_weather_days.parquet`` の**先頭日**(D-W15 の再生候補日の選定は未決)。
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Any

import numpy as np
from numba import njit, prange

from ..field.w13_weather import LAT, LON, TZ_OFFSET_MIN, _solar_terms, solar_elevation_deg
from ..geo import common as C
from .w8_visibility import EYE_M, RASTER_M, STEP_M, _dem_sample, build_scene

STAGE = "W9"
STAGE_VERSION = "1.0.0"

#: 1日の面数(5分刻み=D-W10)。
N_PLANES = 288
#: 刻み [分]。
PLANE_MIN = 5
#: 影の最大追跡距離 [m](expedient)。
SHADOW_MAX_M = 300.0
#: D-W10 の宣言予算 [byte/再生日]。
BUDGET_BYTES_PER_DAY = 10_000_000


def sun_vector(date: dt.date, local_min: float) -> tuple[float, float, float]:
    """(高度 [deg], 方位 [deg・北から時計回り], 単位水平方向の x 成分…) ではなく
    ``(elevation_deg, azimuth_deg_from_north, tan_elevation)`` を返す。

    W13 の ``_solar_terms`` をそのまま使う(赤緯・均時差の定義を1本にする)。
    """
    hour_utc = (local_min - TZ_OFFSET_MIN) / 60.0
    decl, eqtime = _solar_terms(date, hour_utc)
    true_solar_min = local_min + eqtime + 4.0 * LON - TZ_OFFSET_MIN
    ha = math.radians(true_solar_min / 4.0 - 180.0)
    lat_r = math.radians(LAT)
    sin_h = math.sin(lat_r) * math.sin(decl) + math.cos(lat_r) * math.cos(decl) * math.cos(ha)
    elev = math.degrees(math.asin(max(-1.0, min(1.0, sin_h))))
    az = math.degrees(
        math.atan2(math.sin(ha), math.cos(ha) * math.sin(lat_r) - math.tan(decl) * math.cos(lat_r))
    ) + 180.0
    return elev, az % 360.0, math.tan(math.radians(elev))


def all_shadow_plane(n_points: int) -> np.ndarray:
    """全点日陰の1面(``np.packbits`` 互換・端数ビットは 0 で埋める)。"""
    plane = np.full((n_points + 7) // 8, 0xFF, dtype=np.uint8)
    rem = n_points % 8
    if rem and plane.shape[0]:
        plane[-1] = np.uint8((0xFF << (8 - rem)) & 0xFF)
    return plane


@njit(cache=True, parallel=True, nogil=True)
def _shadow_plane(
    px: np.ndarray,
    py: np.ndarray,
    pz: np.ndarray,
    forced: np.ndarray,
    ux: float,
    uy: float,
    tan_elev: float,
    ground_z: np.ndarray,
    top_z: np.ndarray,
    owner: np.ndarray,
    x0: float,
    y0: float,
    pitch: float,
    nx: int,
    ny: int,
    step: float,
    max_dist: float,
    max_top_z: float,
    out: np.ndarray,
) -> None:
    """1面ぶんの影判定(``out[i]=1`` が日陰)。``forced`` は無条件で日陰にする点。"""
    n_steps = int(max_dist / step)
    for i in prange(px.shape[0]):
        if forced[i]:
            out[i] = 1
            continue
        shadow = 0
        z0 = pz[i]
        for k in range(1, n_steps + 1):
            s = k * step
            rz = z0 + tan_elev * s
            if rz > max_top_z:
                break
            c = int((px[i] + ux * s - x0) / pitch)
            r = int((py[i] + uy * s - y0) / pitch)
            if c < 0 or c >= nx or r < 0 or r >= ny:
                break
            if top_z[r, c] > rz:
                shadow = 1
                break
        out[i] = shadow


def run(ctx: C.Ctx) -> C.StageResult:
    osm_p = ctx.osm()
    terrain_p = ctx.path("plateau", "terrain.npz")
    terrain_json_p = ctx.path("plateau", "terrain.json")
    b_p = ctx.out / "w4_buildings.parquet"
    pts_p = ctx.out / "w10_street_points.parquet"
    days_p = ctx.out / "w13_weather_days.parquet"
    for p in (osm_p, terrain_p, terrain_json_p):
        if not p.exists():
            raise FileNotFoundError(f"W9 入力が無い: {p}")
    for p in (b_p, pts_p, days_p):
        if not p.exists():
            raise FileNotFoundError(f"W9 は W4/W10/W13 の出力を必要とする: {p}")

    osm = C.load_json(osm_p)
    b_index = {b["id"]: i for i, b in enumerate(osm["buildings"])}
    polys = [np.asarray(b["footprint"], dtype=np.float64) for b in osm["buildings"]]
    tj = C.load_json(terrain_json_p)
    dem = np.load(terrain_p)["heights"]

    build = C.read_parquet_columns(b_p, ["building_id", "h_m", "centroid_x", "centroid_y"])
    fps = [polys[b_index[bid]] for bid in build["building_id"]]
    bx = np.asarray(build["centroid_x"], dtype=np.float64)
    by = np.asarray(build["centroid_y"], dtype=np.float64)
    bh = np.asarray(build["h_m"], dtype=np.float64)

    pts = C.read_parquet_columns(pts_p, ["x", "y", "band"])
    vx = np.asarray(pts["x"], dtype=np.float64)
    vy = np.asarray(pts["y"], dtype=np.float64)
    band = np.asarray(pts["band"])
    n_pts = vx.shape[0]

    bounds = (
        min(float(vx.min()), float(bx.min())),
        min(float(vy.min()), float(by.min())),
        max(float(vx.max()), float(bx.max())),
        max(float(vy.max()), float(by.max())),
    )
    base_z, _ = _dem_sample(dem, tj["x0"], tj["y0"], tj["cell_m"], bx, by)
    scene = build_scene(
        fps, base_z.astype(np.float64), bh, dem, (tj["x0"], tj["y0"]), float(tj["cell_m"]), bounds
    )
    vz = scene.sample_ground(vx, vy) + EYE_M
    forced_ug = (band == "UG").astype(np.uint8)

    days = C.read_parquet_columns(days_p, ["date", "weather_type", "stratum"])
    date_str = str(days["date"][0])
    date = dt.date.fromisoformat(date_str)

    planes = np.zeros((N_PLANES, (n_pts + 7) // 8), dtype=np.uint8)
    flags = np.empty(n_pts, dtype=np.uint8)
    elevations: list[float] = []
    azimuths: list[float] = []
    fractions: list[float] = []
    n_night = 0
    for p in range(N_PLANES):
        local_min = p * PLANE_MIN + PLANE_MIN / 2.0
        elev, az, tan_e = sun_vector(date, local_min)
        elevations.append(round(elev, 3))
        azimuths.append(round(az, 3))
        if elev <= 0.0:
            planes[p] = all_shadow_plane(n_pts)
            fractions.append(1.0)
            n_night += 1
            continue
        az_r = math.radians(az)
        ux = math.sin(az_r)
        uy = math.cos(az_r)
        _shadow_plane(
            vx, vy, vz, forced_ug, ux, uy, tan_e,
            scene.ground_z, scene.top_z, scene.owner,
            scene.x0, scene.y0, scene.pitch, scene.nx, scene.ny,
            STEP_M, SHADOW_MAX_M, scene.max_top_z, flags,
        )
        planes[p] = np.packbits(flags)
        fractions.append(float(flags.mean()))

    noon_plane = (12 * 60) // PLANE_MIN
    day_planes = [i for i, e in enumerate(elevations) if e > 0.0]

    params: dict[str, Any] = {
        "n_planes": N_PLANES,
        "plane_minutes": PLANE_MIN,
        "eye_m": EYE_M,
        "step_m": STEP_M,
        "raster_pitch_m": RASTER_M,
        "shadow_max_m": SHADOW_MAX_M,
        "budget_bytes_per_day": BUDGET_BYTES_PER_DAY,
        "sun_model": "NOAA low-order (field.w13_weather._solar_terms)",
        "lat": LAT,
        "lon": LON,
        "tz_offset_min": TZ_OFFSET_MIN,
        "ug_always_shadow": True,
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash([osm_p, terrain_p, terrain_json_p, b_p, pts_p, days_p]),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=["昼夜・日照・影", "地形(起伏)"],
        expedients=[
            "影の最大追跡距離 300m(高い建物の低仰角の影を打ち切る)",
            "UG は常時日陰・DECK は GL と同じ扱い(デッキ床高が未取得)",
            "遮蔽は W8 と同じ 2.5m ラスタ(建物頂部高さ場)",
            "大気差・遠方地形の尾根越し遮蔽を見ない",
            "再生日=W13 の先頭日(D-W15 の候補日選定は未決)",
        ],
        notes={
            "replay_date": date_str,
            "replay_day_weather_type": str(days["weather_type"][0]),
            "replay_day_stratum": str(days["stratum"][0]),
            "points": n_pts,
            "points_by_band": {b: int((band == b).sum()) for b in sorted(set(band.tolist()))},
            "planes_night_all_shadow": n_night,
            "planes_daylight": len(day_planes),
            "solar_elev_max_deg": max(elevations),
            "solar_elev_at_noon_deg": elevations[noon_plane],
            "solar_azimuth_at_noon_deg": azimuths[noon_plane],
            "shadow_fraction_noon": round(fractions[noon_plane], 5),
            "shadow_fraction_daylight_mean": round(
                float(np.mean([fractions[i] for i in day_planes])) if day_planes else 1.0, 5
            ),
            "shadow_fraction_min": round(min(fractions), 5),
            "bytes_per_plane": int(planes.shape[1]),
            "spec_reference_points": (
                "D-W10 の 8.6MB/日 は 239,028点での値。本実装の点集合は W10 と同じ "
                f"{n_pts}点なので {N_PLANES}×{planes.shape[1]}B になる(点数を減らして予算に合わせることはしない)。"
            ),
        },
    )
    res.outputs.append(C.write_npy(ctx.out, f"w9_shadow_{date_str}.npy", planes))
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w9_shadow_planes.parquet",
            {
                "plane_idx": np.arange(N_PLANES, dtype=np.int16),
                "local_min": np.array([p * PLANE_MIN + PLANE_MIN / 2.0 for p in range(N_PLANES)], dtype=np.float32),
                "solar_elev_deg": np.array(elevations, dtype=np.float32),
                "solar_azimuth_deg": np.array(azimuths, dtype=np.float32),
                "shadow_fraction": np.array(fractions, dtype=np.float32),
            },
        )
    )
    shadow_bytes = res.outputs[0]["bytes"]
    night_ok = all(
        int(np.unpackbits(planes[p])[:n_pts].sum()) == n_pts
        for p, e in enumerate(elevations)
        if e <= 0.0
    )
    res.gates = [
        C.Gate("replay_date", date_str, None),
        C.Gate("planes", int(planes.shape[0]), N_PLANES),
        C.Gate("bits_per_plane_cover_points", int(planes.shape[1]) * 8 >= n_pts, True),
        C.Gate("night_planes_all_shadow", night_ok, True),
        C.Gate(
            "shadow_bytes_per_day_le_10mb",
            int(shadow_bytes),
            BUDGET_BYTES_PER_DAY,
            passed=shadow_bytes <= BUDGET_BYTES_PER_DAY,
        ),
        C.Gate("shadow_fraction_noon", round(fractions[noon_plane], 5), None),
        C.Gate("daylight_planes", len(day_planes), None),
    ]
    return res
