"""W13 気象日再生(§1 W13・D-W15・知覚契約書 §3 B3 語彙)。

**実日ブートストラップ**(D-W15 推奨(c)): 乱択するのは「どの実日を引くか」だけで、
日内の推移は実測をそのまま使う。層=(曜日種別 × 天候型)。ランごとに manifest の seed で
層内から乱択する(``select_day``)。合成乱数気象は不採用。

入力: アメダス東京(点番号 44132・北の丸公園)の 10分値 JSON 35日分
(2026-07-28〜08-31)。**候補集合は 35日**であり、D-W15 が求める etrn 由来の
層別 ≈40日は**未取得(親レーン)**=ヘッダに宣言する(本段階は何も取りに行かない)。

出力
  - ``w13_weather_days.parquet``: 日 → 曜日種別・天候型・層・日統計・日の出/日の入。
  - ``w13_weather_hourly.parquet``: 日×時 → 気温・湿度・降水・風・日照・WBGT推定+B3語彙。

expedient(すべて宣言)
  - 都市バイアス**無補正**(北の丸公園 ≠ 渋谷。移転の平年値差は台帳に置くだけ)。
  - WBGT=**推定式**(環境省 API 実況値は未取得)。日射量も日照時間からの推定。
  - 天候型・天候語彙・体感温度段階の境界(WBGT 境界のみ公的指針に釘付け)。
  - 祝日表は 2026年7-8月のハードコード(内閣府の公式 CSV は未取得)。
"""

from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from shibuya.core.rng import stream

from . import common as C

STAGE = "W13"
STAGE_VERSION = "1.0.0"

AMEDAS_DIR = ("realworld", "amedas")
#: 気象庁 etrn 時別値(東京 47662・親レーン取得 2026-09-08・§7 公的ドメイン例外)。アメダス10分値の欠測時間を補完する。
ETRN_CSV = ("realworld", "jma_etrn", "tokyo47662_hourly_2026-07-28_2026-08-31.csv")
#: アメダス地点(親確認済み・_meta.station)。渋谷駅から約 5.76 km NE。
AMEDAS_STATION = {"id": "44132", "name": "東京", "site": "北の丸公園(千代田区)", "lat": 35.6917, "lon": 139.7506}

#: 世界原点(W0)。日の出・日の入はこの緯度経度で解く。
LAT = C.ORIGIN_LATLON[0]
LON = C.ORIGIN_LATLON[1]
TZ_OFFSET_MIN = 540  # JST

#: 内閣府「国民の祝日」(2026年・本段階の窓に掛かる分のみ。公式 CSV は未取得=expedient)。
HOLIDAYS_2026: dict[str, str] = {
    "2026-07-20": "海の日",
    "2026-08-11": "山の日",
}

#: B3 天候語彙(知覚契約書に語彙表が無いため本段階が定義=expedient)。
WEATHER_VOCAB: tuple[str, ...] = ("晴", "薄曇", "曇", "小雨", "雨")
#: B3 日照語彙(D-W15/知覚契約書 §3 の「日照」欄)。
DAYLIGHT_VOCAB: tuple[str, ...] = ("夜明け前", "日中", "日没後")
#: B3 体感温度段階。境界=環境省/日本生気象学会「暑さ指数(WBGT)に応じた注意事項」
#: 21/25/28/31 に釘付け(語彙の割当は expedient)。
HEAT_VOCAB: tuple[str, ...] = ("快適", "やや暑い", "暑い", "厳しい暑さ", "危険な暑さ")
HEAT_BOUNDS: tuple[float, ...] = (21.0, 25.0, 28.0, 31.0)

#: 日単位の天候型(D-W15 の層)。猛暑日=気象庁の定義(日最高気温 35℃以上)。
#: 降水日=気象庁の定義(日降水量 0.5mm 以上)。晴/曇の分割は日照率 0.4(expedient)。
MOSHO_TEMP_C = 35.0
RAIN_DAY_MM = 0.5
SUNNY_RATIO = 0.4

#: 時別の天候判定(expedient)。
RAIN_HOUR_MM = 0.5
SUN_RATIO_CLEAR = 0.6
SUN_RATIO_THIN = 0.2

#: WBGT 推定式(屋外・Ono & Tonouchi 2014 型)の係数。実況未取得時の代替=expedient。
WBGT_COEFF = {
    "ta": 0.735,
    "rh": 0.0374,
    "ta_rh": 0.00292,
    "sr": 7.619,
    "sr2": -4.557,
    "ws": -0.0572,
    "const": -4.064,
}
#: 日射量の推定(expedient): SR[kW/m^2] = max(sin(h),0) * SOLAR_CONST_KW * 日照率。
SOLAR_CONST_KW = 0.9


# --- 太陽位置(NOAA General Solar Position Calculations)------------------------------------
def _solar_terms(date: dt.date, hour_utc: float) -> tuple[float, float]:
    """(赤緯 [rad], 均時差 [min])。NOAA の低次近似(1901-2099 で ±1分級)。"""
    doy = date.timetuple().tm_yday
    gamma = 2.0 * math.pi / 365.0 * (doy - 1 + (hour_utc - 12.0) / 24.0)
    eqtime = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )
    decl = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma)
        + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma)
        + 0.00148 * math.sin(3 * gamma)
    )
    return decl, eqtime


def sun_times(
    date: dt.date, lat: float = LAT, lon: float = LON, tz_offset_min: int = TZ_OFFSET_MIN
) -> tuple[float | None, float | None]:
    """日の出・日の入(地方時の 0時からの分)。極夜・白夜は ``(None, None)``。

    天頂角 90.833°(大気差 34' + 太陽半径 16')を採る NOAA の標準定義。
    """
    decl, eqtime = _solar_terms(date, 12.0 - tz_offset_min / 60.0)
    lat_r = math.radians(lat)
    cos_ha = math.cos(math.radians(90.833)) / (math.cos(lat_r) * math.cos(decl)) - math.tan(
        lat_r
    ) * math.tan(decl)
    if cos_ha > 1.0 or cos_ha < -1.0:
        return None, None
    ha = math.degrees(math.acos(cos_ha))
    sunrise_utc = 720.0 - 4.0 * (lon + ha) - eqtime
    sunset_utc = 720.0 - 4.0 * (lon - ha) - eqtime
    return sunrise_utc + tz_offset_min, sunset_utc + tz_offset_min


def solar_elevation_deg(
    date: dt.date,
    local_min: float,
    lat: float = LAT,
    lon: float = LON,
    tz_offset_min: int = TZ_OFFSET_MIN,
) -> float:
    """地方時 ``local_min``(0時からの分)の太陽高度 [deg]。"""
    hour_utc = (local_min - tz_offset_min) / 60.0
    decl, eqtime = _solar_terms(date, hour_utc)
    true_solar_min = local_min + eqtime + 4.0 * lon - tz_offset_min
    ha = math.radians(true_solar_min / 4.0 - 180.0)
    lat_r = math.radians(lat)
    sin_h = math.sin(lat_r) * math.sin(decl) + math.cos(lat_r) * math.cos(decl) * math.cos(ha)
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_h))))


def daylight_phase(local_min: float, sunrise_min: float | None, sunset_min: float | None) -> str:
    """B3 日照語彙。"""
    if sunrise_min is None or sunset_min is None:
        return DAYLIGHT_VOCAB[1] if sunrise_min is None else DAYLIGHT_VOCAB[0]
    if local_min < sunrise_min:
        return DAYLIGHT_VOCAB[0]
    if local_min < sunset_min:
        return DAYLIGHT_VOCAB[1]
    return DAYLIGHT_VOCAB[2]


# --- WBGT ---------------------------------------------------------------------------------
def wbgt_estimate(temp_c: float, rh_pct: float, wind_ms: float, solar_kw: float) -> float:
    """WBGT 推定式(屋外・実況未取得時の代替=expedient)。"""
    k = WBGT_COEFF
    return (
        k["ta"] * temp_c
        + k["rh"] * rh_pct
        + k["ta_rh"] * temp_c * rh_pct
        + k["sr"] * solar_kw
        + k["sr2"] * solar_kw * solar_kw
        + k["ws"] * wind_ms
        + k["const"]
    )


def heat_stage(wbgt: float) -> int:
    for i, b in enumerate(HEAT_BOUNDS):
        if wbgt < b:
            return i
    return len(HEAT_BOUNDS)


def hour_weather(precip_mm: float, sunshine_ratio: float | None, day_type: str) -> str:
    """B3 天候語彙(時別)。夜間(日照が定義されない時間)は日単位の型へ落とす。"""
    if precip_mm >= RAIN_HOUR_MM:
        return "雨"
    if precip_mm > 0.0:
        return "小雨"
    if sunshine_ratio is None:
        return "晴" if day_type in ("晴", "猛暑") else "曇"
    if sunshine_ratio >= SUN_RATIO_CLEAR:
        return "晴"
    if sunshine_ratio >= SUN_RATIO_THIN:
        return "薄曇"
    return "曇"


def weekday_kind(date: dt.date) -> str:
    """平日 / 土休(土日+国民の祝日)。"""
    if date.isoformat() in HOLIDAYS_2026 or date.weekday() >= 5:
        return "土休"
    return "平日"


def day_weather_type(
    temp_max: float | None, precip_total: float, sunshine_h: float, possible_h: float
) -> str:
    """日単位の天候型(猛暑 > 雨 > 晴/曇)。"""
    if temp_max is not None and temp_max >= MOSHO_TEMP_C:
        return "猛暑"
    if precip_total >= RAIN_DAY_MM:
        return "雨"
    ratio = (sunshine_h / possible_h) if possible_h > 0 else 0.0
    return "晴" if ratio >= SUNNY_RATIO else "曇"


# --- アメダス 10分値 → 時別 ------------------------------------------------------------------
def _mean(values: Sequence[float]) -> float | None:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def read_amedas_day(path: Path) -> tuple[str, dict[int, dict[str, float | None]]]:
    """アメダス日ファイル → (日付, 時 → 集約値)。10分値を時単位へ畳む。"""
    doc = C.load_json(path)
    date = str(doc["_meta"]["date_jst"])
    buckets: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for rec in doc["data"]:
        hour = int(str(rec["obs_time_jst"])[11:13])
        buckets[hour].append(rec["values"])
    out: dict[int, dict[str, float | None]] = {}
    for hour, recs in buckets.items():
        precip = [r.get("precipitation10m") for r in recs]
        sun = [r.get("sun10m") for r in recs]
        out[hour] = {
            "temp_c": _mean([r.get("temp") for r in recs]),
            "rh": _mean([r.get("humidity") for r in recs]),
            "wind_ms": _mean([r.get("wind") for r in recs]),
            "precip_mm": sum(v for v in precip if v is not None) if any(
                v is not None for v in precip
            ) else None,
            "sunshine_h": (sum(v for v in sun if v is not None) / 60.0)
            if any(v is not None for v in sun)
            else None,
            "n_samples": float(len(recs)),
        }
    return date, out


def _etrn_num(s: str) -> float | None:
    """etrn の値記号: '--'=現象なし(0)・'×'=欠測・')'=準正常・']'=資料不足(値は採る)・空=None。"""
    s = (s or "").strip()
    if s in ("", "×", "///"):
        return None
    if s == "--":
        return 0.0
    s = s.rstrip(")]").strip()
    try:
        return float(s)
    except ValueError:
        return None


def read_etrn_csv(path: Path) -> dict[tuple[str, int], dict[str, float | None]]:
    """etrn 時別値 CSV → (日付, 時 0..23) → 集約値(アメダス畳み込みと同じキー)。

    etrn の「時 h(1..24)」は h 時までの1時間(降水・日照は積算、気温等は h 時の正時値)。
    本モジュールの時刻索引は「h 時台」なので h-1 へ写像する(expedient・正時値を時台代表とする)。
    """
    import csv

    out: dict[tuple[str, int], dict[str, float | None]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            h = int(row["hour"]) - 1
            out[(row["date"], h)] = {
                "temp_c": _etrn_num(row["temp_c"]),
                "rh": _etrn_num(row["rh_pct"]),
                "wind_ms": _etrn_num(row["wind_ms"]),
                "precip_mm": _etrn_num(row["precip_mm"]),
                "sunshine_h": _etrn_num(row["sunshine_h"]),
                "n_samples": 0.0,
            }
    return out


def select_day(master_seed: int | str, stratum: str, strata: dict[str, list[str]]) -> str:
    """層 → 実日(決定論)。``core.rng.stream(seed, "build.w13", ...)`` から引く。

    同じ (master_seed, stratum, 候補集合) は常に同じ日を返す。候補は日付昇順に固定。
    """
    days = strata.get(stratum)
    if not days:
        raise KeyError(f"層に候補日が無い: {stratum!r}")
    counter = int(C.sha256_bytes(stratum.encode("utf-8"))[:16], 16)
    rng = stream(master_seed, "build.w13", counter)
    return sorted(days)[int(rng.integers(0, len(days)))]


def run(ctx: C.Ctx) -> C.StageResult:
    root = ctx.path(*AMEDAS_DIR)
    if not root.exists():
        raise FileNotFoundError(f"W13 入力が無い: {root}")
    files = sorted(root.rglob("amedas_*.json"))
    if not files:
        raise FileNotFoundError(f"W13: アメダス日ファイルが無い: {root}")

    days: list[dict[str, Any]] = []
    hourly_rows: list[dict[str, Any]] = []
    gaps: dict[str, list[int]] = {}
    etrn_path = ctx.path(*ETRN_CSV)
    etrn = read_etrn_csv(etrn_path) if etrn_path.exists() else {}
    etrn_filled: dict[str, list[int]] = {}
    input_files = list(files) + ([etrn_path] if etrn_path.exists() else [])

    for path in files:
        date_s, hours = read_amedas_day(path)
        for h in range(24):
            if h not in hours and (date_s, h) in etrn:
                hours[h] = dict(etrn[(date_s, h)])
                etrn_filled.setdefault(date_s, []).append(h)
        date = dt.date.fromisoformat(date_s)
        sunrise, sunset = sun_times(date)
        possible_h = ((sunset - sunrise) / 60.0) if (sunrise is not None and sunset is not None) else 0.0
        present = sorted(hours)
        missing = [h for h in range(24) if h not in hours]
        if missing:
            gaps[date_s] = missing
        temps = [hours[h]["temp_c"] for h in present if hours[h]["temp_c"] is not None]
        precip_total = sum(
            hours[h]["precip_mm"] for h in present if hours[h]["precip_mm"] is not None
        )
        sunshine_total = sum(
            hours[h]["sunshine_h"] for h in present if hours[h]["sunshine_h"] is not None
        )
        wtype = day_weather_type(
            max(temps) if temps else None, precip_total, sunshine_total, possible_h
        )
        wkind = weekday_kind(date)
        wbgt_vals: list[float] = []
        for h in present:
            rec = hours[h]
            mid = h * 60 + 30.0
            elev = solar_elevation_deg(date, mid)
            ratio = rec["sunshine_h"] if rec["sunshine_h"] is not None else None
            solar_kw = max(math.sin(math.radians(elev)), 0.0) * SOLAR_CONST_KW * (ratio or 0.0)
            wbgt = None
            if rec["temp_c"] is not None and rec["rh"] is not None:
                wbgt = wbgt_estimate(
                    float(rec["temp_c"]),
                    float(rec["rh"]),
                    float(rec["wind_ms"] or 0.0),
                    solar_kw,
                )
                wbgt_vals.append(wbgt)
            hourly_rows.append(
                {
                    "date": date_s,
                    "hour": h,
                    "temp_c": rec["temp_c"],
                    "rh": rec["rh"],
                    "precip_mm": rec["precip_mm"],
                    "wind_ms": rec["wind_ms"],
                    "sunshine_h": rec["sunshine_h"],
                    "solar_elev_deg": round(elev, 3),
                    "solar_kw_est": round(solar_kw, 4),
                    "wbgt_est": None if wbgt is None else round(wbgt, 2),
                    "weather": hour_weather(float(rec["precip_mm"] or 0.0), ratio, wtype),
                    "daylight": daylight_phase(mid, sunrise, sunset),
                    "heat_stage": HEAT_VOCAB[heat_stage(wbgt)] if wbgt is not None else "",
                    "n_samples": int(rec["n_samples"]),
                    "src": "etrn" if int(rec["n_samples"]) == 0 else "amedas",
                }
            )
        days.append(
            {
                "date": date_s,
                "weekday": date.weekday(),
                "weekday_kind": wkind,
                "holiday_name": HOLIDAYS_2026.get(date_s, ""),
                "weather_type": wtype,
                "stratum": f"{wkind}|{wtype}",
                "hours_present": len(present),
                "day_complete": len(present) == 24,
                "temp_max_c": max(temps) if temps else None,
                "temp_min_c": min(temps) if temps else None,
                "precip_total_mm": round(precip_total, 2),
                "sunshine_total_h": round(sunshine_total, 3),
                "wbgt_max_est": round(max(wbgt_vals), 2) if wbgt_vals else None,
                "sunrise": C.min_to_hhmm(int(round(sunrise))) if sunrise is not None else "",
                "sunset": C.min_to_hhmm(int(round(sunset))) if sunset is not None else "",
                "possible_sunshine_h": round(possible_h, 3),
            }
        )

    days.sort(key=lambda d: d["date"])
    hourly_rows.sort(key=lambda r: (r["date"], r["hour"]))
    strata: dict[str, list[str]] = defaultdict(list)
    for d in days:
        strata[d["stratum"]].append(d["date"])

    day_cols = {
        "date": [d["date"] for d in days],
        "weekday": np.array([d["weekday"] for d in days], dtype=np.int8),
        "weekday_kind": [d["weekday_kind"] for d in days],
        "holiday_name": [d["holiday_name"] for d in days],
        "weather_type": [d["weather_type"] for d in days],
        "stratum": [d["stratum"] for d in days],
        "hours_present": np.array([d["hours_present"] for d in days], dtype=np.int8),
        "day_complete": [bool(d["day_complete"]) for d in days],
        "temp_max_c": np.array(
            [np.nan if d["temp_max_c"] is None else d["temp_max_c"] for d in days]
        ),
        "temp_min_c": np.array(
            [np.nan if d["temp_min_c"] is None else d["temp_min_c"] for d in days]
        ),
        "precip_total_mm": np.array([d["precip_total_mm"] for d in days]),
        "sunshine_total_h": np.array([d["sunshine_total_h"] for d in days]),
        "possible_sunshine_h": np.array([d["possible_sunshine_h"] for d in days]),
        "wbgt_max_est": np.array(
            [np.nan if d["wbgt_max_est"] is None else d["wbgt_max_est"] for d in days]
        ),
        "sunrise": [d["sunrise"] for d in days],
        "sunset": [d["sunset"] for d in days],
    }

    def _col(name: str) -> np.ndarray:
        return np.array(
            [np.nan if r[name] is None else float(r[name]) for r in hourly_rows], dtype=np.float64
        )

    hourly_cols = {
        "date": [r["date"] for r in hourly_rows],
        "hour": np.array([r["hour"] for r in hourly_rows], dtype=np.int8),
        "temp_c": _col("temp_c"),
        "rh": _col("rh"),
        "precip_mm": _col("precip_mm"),
        "wind_ms": _col("wind_ms"),
        "sunshine_h": _col("sunshine_h"),
        "solar_elev_deg": _col("solar_elev_deg"),
        "solar_kw_est": _col("solar_kw_est"),
        "wbgt_est": _col("wbgt_est"),
        "weather": [r["weather"] for r in hourly_rows],
        "daylight": [r["daylight"] for r in hourly_rows],
        "heat_stage": [r["heat_stage"] for r in hourly_rows],
        "n_samples": np.array([r["n_samples"] for r in hourly_rows], dtype=np.int16),
        "src": [r["src"] for r in hourly_rows],
    }

    params: dict[str, Any] = {
        "amedas_station": AMEDAS_STATION,
        "origin_latlon": list(C.ORIGIN_LATLON),
        "tz_offset_min": TZ_OFFSET_MIN,
        "holidays": HOLIDAYS_2026,
        "weather_vocab": list(WEATHER_VOCAB),
        "daylight_vocab": list(DAYLIGHT_VOCAB),
        "heat_vocab": list(HEAT_VOCAB),
        "heat_bounds": list(HEAT_BOUNDS),
        "day_type_rules": {
            "mosho_temp_c": MOSHO_TEMP_C,
            "rain_day_mm": RAIN_DAY_MM,
            "sunny_ratio": SUNNY_RATIO,
        },
        "hour_weather_rules": {
            "rain_hour_mm": RAIN_HOUR_MM,
            "sun_ratio_clear": SUN_RATIO_CLEAR,
            "sun_ratio_thin": SUN_RATIO_THIN,
        },
        "wbgt_coeff": WBGT_COEFF,
        "solar_const_kw": SOLAR_CONST_KW,
        "solar_algorithm": "NOAA General Solar Position Calculations (zenith 90.833deg)",
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash(input_files),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=["気象(日次・時別)", "日照・昼夜", "体感温度(内受容の入力)"],
        expedients=[
            "都市バイアス無補正(北の丸公園 ≠ 渋谷・移転の平年値差は台帳のみ)",
            "WBGT=推定式(環境省 API 実況値は未取得)",
            "日射量=日照率と太陽高度からの推定",
            "天候型・時別天候語彙・体感温度語彙の割当(WBGT 境界のみ公的指針に釘付け)",
            "祝日表=2026年7-8月のハードコード(内閣府 CSV は未取得)",
            "10分値 → 時別の畳み方(気温/湿度/風=平均・降水/日照=合計)",
            "アメダス欠測時間は etrn 時別値で補完(時 h → h-1 時台・気温等は正時値・降水/日照は積算)",
        ],
        notes={
            "candidate_days": len(days),
            "candidate_set_note": (
                "候補集合は手元の 35日(2026-07-28〜08-31)。D-W15 が求める etrn 由来の"
                "季節4×曜日2×天候型の層別 ≈40日は**未取得(親レーン)**。本段階は取得しない。"
            ),
            "hours_missing_by_date": {k: v for k, v in sorted(gaps.items())},
            "etrn_filled_hours_by_date": {k: v for k, v in sorted(etrn_filled.items())},
            "etrn_filled_hours_total": sum(len(v) for v in etrn_filled.values()),
            "etrn_source": "気象庁 過去の気象データ検索(etrn) 時別値 東京 47662(親レーン取得・data/realworld/jma_etrn)" if etrn else "未取得",
            "days_with_full_24h": sum(1 for d in days if d["day_complete"]),
            "hourly_rows": len(hourly_rows),
            "strata": {k: sorted(v) for k, v in sorted(strata.items())},
            "stratum_counts": {k: len(v) for k, v in sorted(strata.items())},
            "weather_type_counts": {
                t: sum(1 for d in days if d["weather_type"] == t) for t in ("晴", "曇", "雨", "猛暑")
            },
            "weekday_kind_counts": {
                t: sum(1 for d in days if d["weekday_kind"] == t) for t in ("平日", "土休")
            },
            "holidays_in_window": {
                k: v for k, v in HOLIDAYS_2026.items() if any(d["date"] == k for d in days)
            },
            "sunrise_range": [days[0]["sunrise"], days[-1]["sunrise"]] if days else [],
            "sunset_range": [days[0]["sunset"], days[-1]["sunset"]] if days else [],
            "wbgt_source": "estimate (環境省 getSurveyData 実況値=未取得)",
            "usage_note_of_source": (
                "data/realworld/amedas の usage_note は『較正と事後検証にのみ使う・"
                "シミュ本体(src/)は読まない』。本段階は**構築(オフライン資産化)**であり"
                "ラン時に data/realworld を読むことはない(資産は data/world/v2 に凍結)。"
            ),
        },
    )
    res.outputs.append(C.write_parquet(ctx.out, "w13_weather_days.parquet", day_cols))
    res.outputs.append(C.write_parquet(ctx.out, "w13_weather_hourly.parquet", hourly_cols))
    res.gates = [
        C.Gate("weather_days", len(days), 35),
        C.Gate("days_with_full_24h", sum(1 for d in days if d["day_complete"]), None),
        C.Gate("days_with_missing_hours", len(gaps), 0, passed=len(gaps) == 0),
        C.Gate("strata_non_empty", len(strata), None, passed=len(strata) > 0),
        C.Gate("hourly_rows", len(hourly_rows), None),
        C.Gate("etrn_filled_hours", sum(len(v) for v in etrn_filled.values()), None),
        C.Gate(
            "sunrise_monotone_in_window",
            days[0]["sunrise"] < days[-1]["sunrise"] if days else False,
            True,
        ),
        C.Gate("stage_boundary_param_hash", C.param_hash(params)[:16], None),
    ]
    return res
