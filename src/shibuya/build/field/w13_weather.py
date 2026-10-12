"""W13 気象日再生(§1 W13・D-W15・知覚契約書 §3 B3 語彙)。

**実日ブートストラップ**(D-W15 推奨(c)): 乱択するのは「どの実日を引くか」だけで、
日内の推移は実測をそのまま使う。層=(曜日種別 × 天候型)。ランごとに manifest の seed で
層内から乱択する(``select_day``)。合成乱数気象は不採用。

〔改訂(第330 B5)・答え 10-12b 1-3〕**年間化**: 窓 :data:`WINDOW`(2025-09-01〜2026-08-31・365 日)を
定数で持ち、窓の外のファイルは読まない(旧の ``rglob`` をやめた=``data/realworld/amedas`` の
日次取得の日が黙って入らない)。入力は気象庁 etrn の東京(47662=アメダス 44132・北の丸公園)の
**10 分値**(主)と**時別値**(欠けの補完)の 2 本の CSV(``tools/realworld_fetch/jma_etrn.py``)。
祝日は内閣府の CSV(``data/calendar/syukujitsu.csv``)。季節(気象庁の区分)は**列に足さない**
(エンジンが日付から計算する=読み口の契約)。季節 × 平日/土休 × 天候型の日数の表は notes に載せる。
35 日(2026-07-28〜08-31)は etrn の 10 分値とアメダスの JSON を 10 分ごとに突き合わせて検算した
(気温・湿度・風速・降水は 3,219/3,219 一致・日照は etrn の夜の空欄=アメダスの 0 だけが違う=
10e の記録 ``b5_w13_amedas_crosscheck.json``)。

出力
  - ``w13_weather_days.parquet``: 日 → 曜日種別・天候型・層・日統計・日の出/日の入。
  - ``w13_weather_hourly.parquet``: 日×時 → 気温・湿度・降水・風・日照・WBGT推定+B3語彙。

expedient(すべて宣言)
  - 都市バイアス**無補正**(北の丸公園 ≠ 渋谷。移転の平年値差は台帳に置くだけ)。
  - WBGT=**推定式**(環境省 API 実況値は未取得)。日射量も日照時間からの推定。
  - 天候型・天候語彙・体感温度段階の境界(WBGT 境界のみ公的指針に釘付け)。
  - 10 分値の日照の空欄(夜)を 0 分として畳む(アメダスの JSON の慣行と同じ・空欄は夜にだけ出る)。
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
#: 1.1.0(第330 B5): 年間化(窓 365 日・etrn の 10 分値が主・時別値で補完・内閣府の祝日 CSV)。
STAGE_VERSION = "1.1.0"

#: 〔改訂(第330 B5)〕天気の再生の窓(両端を含む・答え 10-12b 1-3 (a))。窓の外のファイルは読まない。
WINDOW: tuple[str, str] = ("2025-09-01", "2026-08-31")
#: 気象庁 etrn の 10 分値(主)と時別値(欠けの補完)。東京 47662・``tools/realworld_fetch/jma_etrn.py`` の表。
ETRN_10MIN_CSV = ("realworld", "jma_etrn", f"tokyo47662_10min_{WINDOW[0]}_{WINDOW[1]}.csv")
ETRN_HOURLY_CSV = ("realworld", "jma_etrn", f"tokyo47662_hourly_{WINDOW[0]}_{WINDOW[1]}.csv")
#: 本段階が読む data 根の下のファイル(W19 の資産表はこれだけを載せる)。
INPUT_FILES: tuple[tuple[str, ...], ...] = (ETRN_10MIN_CSV, ETRN_HOURLY_CSV, C.HOLIDAY_CSV)
#: アメダス地点(親確認済み・_meta.station)。渋谷駅から約 5.76 km NE。
AMEDAS_STATION = {"id": "44132", "name": "東京", "site": "北の丸公園(千代田区)", "lat": 35.6917, "lon": 139.7506}

#: 世界原点(W0)。日の出・日の入はこの緯度経度で解く。
LAT = C.ORIGIN_LATLON[0]
LON = C.ORIGIN_LATLON[1]
TZ_OFFSET_MIN = 540  # JST

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


def weekday_kind(date: dt.date, holidays: dict[str, str]) -> str:
    """平日 / 土休(土日+国民の祝日=内閣府の CSV)。"""
    if date.isoformat() in holidays or date.weekday() >= 5:
        return "土休"
    return "平日"


def season_of(date: dt.date) -> str:
    """気象庁の季節の区分(春 3〜5・夏 6〜8・秋 9〜11・冬 12〜2)。列には入れない(notes の表だけ)。"""
    return C.SEASON_OF_MONTH[date.month]


def window_dates(window: tuple[str, str] = WINDOW) -> list[str]:
    a, b = dt.date.fromisoformat(window[0]), dt.date.fromisoformat(window[1])
    return [(a + dt.timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]


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


def _sun10_num(s: str) -> float | None:
    """10 分値の日照(分)。空欄=夜(日照の観測の外)は 0(アメダスの JSON の慣行と同じ・expedient)。"""
    if (s or "").strip() == "":
        return 0.0
    return _etrn_num(s)


def read_etrn_10min_csv(
    path: Path, window: tuple[str, str] = WINDOW
) -> tuple[dict[tuple[str, int], dict[str, float | None]], int]:
    """etrn 10 分値 CSV → ((日付, 時 0..23) → 時の集約値, 窓の外へ出た行の数)。

    時の分け方はアメダスの JSON の畳み方と同じ「観測の時刻の時」(``01:00`` は 1 時台・``00:10`` は 0 時台)。
    頁の ``24:00`` は翌日の 00:00(翌日の 0 時台)。気温・湿度・風速=平均・降水・日照=合計。
    """
    import csv

    lo, hi = window
    buckets: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    outside = 0
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            d = dt.date.fromisoformat(row["date"])
            hh, _mm = row["time"].split(":")
            h = int(hh)
            if h == 24:
                d, h = d + dt.timedelta(days=1), 0
            ds = d.isoformat()
            if not (lo <= ds <= hi):
                outside += 1
                continue
            buckets[(ds, h)].append(row)
    out: dict[tuple[str, int], dict[str, float | None]] = {}
    for key, rows in buckets.items():
        precip = [_etrn_num(r["precip_mm"]) for r in rows]
        sun = [_sun10_num(r["sunshine_min"]) for r in rows]
        out[key] = {
            "temp_c": _mean([_etrn_num(r["temp_c"]) for r in rows]),
            "rh": _mean([_etrn_num(r["rh_pct"]) for r in rows]),
            "wind_ms": _mean([_etrn_num(r["wind_ms"]) for r in rows]),
            "precip_mm": sum(v for v in precip if v is not None)
            if any(v is not None for v in precip)
            else None,
            "sunshine_h": (sum(v for v in sun if v is not None) / 60.0)
            if any(v is not None for v in sun)
            else None,
            "n_samples": float(len(rows)),
        }
    return out, outside


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
    tenmin_path = ctx.path(*ETRN_10MIN_CSV)
    hourly_path = ctx.path(*ETRN_HOURLY_CSV)
    holiday_path = ctx.path(*C.HOLIDAY_CSV)
    for p in (tenmin_path, hourly_path, holiday_path):
        if not p.exists():
            raise FileNotFoundError(f"W13 入力が無い: {p}")
    input_files = [tenmin_path, hourly_path, holiday_path]
    tenmin, tenmin_outside = read_etrn_10min_csv(tenmin_path, WINDOW)
    etrn = {k: v for k, v in read_etrn_csv(hourly_path).items() if WINDOW[0] <= k[0] <= WINDOW[1]}
    holidays_all = C.read_holidays_csv(holiday_path)
    if max(holidays_all) < WINDOW[1]:
        raise ValueError(f"祝日 CSV の範囲({max(holidays_all)} まで)が窓の終わり {WINDOW[1]} に届かない")
    holidays = {k: v for k, v in holidays_all.items() if WINDOW[0] <= k <= WINDOW[1]}

    days: list[dict[str, Any]] = []
    hourly_rows: list[dict[str, Any]] = []
    gaps: dict[str, list[int]] = {}
    etrn_filled: dict[str, list[int]] = {}
    etrn_filled_fields: dict[str, int] = defaultdict(int)
    _FIELDS = ("temp_c", "rh", "wind_ms", "precip_mm", "sunshine_h")

    for date_s in window_dates(WINDOW):
        hours: dict[int, dict[str, Any]] = {}
        for h in range(24):
            rec = tenmin.get((date_s, h))
            fill = etrn.get((date_s, h))
            if rec is None:
                if fill is None:
                    continue
                hours[h] = {**fill, "src": "etrn_hourly"}
                etrn_filled.setdefault(date_s, []).append(h)
                continue
            rec = {**rec, "src": "etrn_10min"}
            if fill is not None:
                for k in _FIELDS:
                    if rec[k] is None and fill[k] is not None:
                        rec[k] = fill[k]
                        rec["src"] = "etrn_10min+hourly"
                        etrn_filled_fields[k] += 1
                if rec["src"] != "etrn_10min":
                    etrn_filled.setdefault(date_s, []).append(h)
            hours[h] = rec
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
        wkind = weekday_kind(date, holidays)
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
                    "src": str(rec["src"]),
                }
            )
        days.append(
            {
                "date": date_s,
                "weekday": date.weekday(),
                "weekday_kind": wkind,
                "holiday_name": holidays.get(date_s, ""),
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

    weather_types = ("晴", "曇", "雨", "猛暑")
    season_table: dict[str, dict[str, dict[str, int]]] = {
        se: {k: {t: 0 for t in weather_types} for k in ("平日", "土休")} for se in C.SEASONS
    }
    for d in days:
        se = season_of(dt.date.fromisoformat(d["date"]))
        season_table[se][d["weekday_kind"]][d["weather_type"]] += 1
    missing_combos = [
        f"{se}|平日|{t}" for se in C.SEASONS for t in weather_types if season_table[se]["平日"][t] == 0
    ]

    params: dict[str, Any] = {
        "amedas_station": AMEDAS_STATION,
        "origin_latlon": list(C.ORIGIN_LATLON),
        "tz_offset_min": TZ_OFFSET_MIN,
        "window": list(WINDOW),
        "holidays_in_window": holidays,
        "season_of_month": {str(k): v for k, v in sorted(C.SEASON_OF_MONTH.items())},
        "tenmin_hour_bucket": "観測の時刻の時(01:00=1 時台・24:00=翌日の 0 時台)=アメダスの JSON の畳み方と同じ",
        "tenmin_blank_sunshine": "夜の空欄=0 分",
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
            "10分値 → 時別の畳み方(気温/湿度/風=平均・降水/日照=合計)",
            "10分値の欠け(時ごと・値ごと)は etrn 時別値で補完(時 h → h-1 時台・気温等は正時値・降水/日照は積算)",
            "10分値の日照の空欄(夜だけに出る)は 0 分(アメダスの JSON の慣行と同じ)",
            "窓の最初の日の 0 時台は 5 本(00:10〜00:50・前日の 24:00 は窓の外で読まない)",
        ],
        notes={
            "candidate_days": len(days),
            "window": list(WINDOW),
            "candidate_set_note": (
                f"候補集合は窓 {WINDOW[0]}〜{WINDOW[1]} の {len(days)} 日(第330 B5 で年間化)。"
                "主=etrn 10 分値・補完=etrn 時別値・祝日=内閣府 CSV。季節は列に入れない"
                "(エンジンが日付から気象庁の区分で計算する)。"
            ),
            "season_weekday_type_counts": season_table,
            "season_weekday_type_missing": missing_combos,
            "season_weekday_type_note": (
                "季節(気象庁の区分: 春 3〜5・夏 6〜8・秋 9〜11・冬 12〜2)× 平日/土休 × 天候型の日数。"
                "どの季節にも平日の各天候型が 1 日以上あるかは報告だけのゲート(落とさない)。"
            ),
            "input_files": [C.sha256_file(p)[:16] + "  " + "/".join(parts) for p, parts in zip(input_files, INPUT_FILES)],
            "tenmin_rows_outside_window": tenmin_outside,
            "etrn_filled_fields": dict(sorted(etrn_filled_fields.items())),
            "hours_missing_by_date": {k: v for k, v in sorted(gaps.items())},
            "etrn_filled_hours_by_date": {k: v for k, v in sorted(etrn_filled.items())},
            "etrn_filled_hours_total": sum(len(v) for v in etrn_filled.values()),
            "etrn_source": (
                "気象庁 過去の気象データ検索(etrn) 東京 47662 の 10 分値(主)と時別値(補完)"
                "(第330 B5 で取得・data/realworld/jma_etrn・頁ごとの md5 は MANIFEST_10min.tsv・MANIFEST_hourly.tsv)"
            ),
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
            "holidays_in_window": holidays,
            "sunrise_range": [days[0]["sunrise"], days[-1]["sunrise"]] if days else [],
            "sunset_range": [days[0]["sunset"], days[-1]["sunset"]] if days else [],
            "wbgt_source": "estimate (環境省 getSurveyData 実況値=未取得)",
            "usage_note_of_source": (
                "本段階は**構築(オフライン資産化)**でありラン時に data/realworld を読むことはない"
                "(資産は data/world/v2 に凍結)。data/realworld/amedas(35 日)と data/realworld_live は読まない"
                "(前者は 10e の記録の検算だけ・後者は検証専用)。"
            ),
        },
    )
    res.outputs.append(C.write_parquet(ctx.out, "w13_weather_days.parquet", day_cols))
    res.outputs.append(C.write_parquet(ctx.out, "w13_weather_hourly.parquet", hourly_cols))
    n_window = len(window_dates(WINDOW))
    by_date = {d["date"]: d for d in days}
    sr_min = min(days, key=lambda d: (d["sunrise"], d["date"]))
    sr_max = max(days, key=lambda d: (d["sunrise"], d["date"]))
    longest = max(days, key=lambda d: (d["possible_sunshine_h"], d["date"]))
    res.gates = [
        C.Gate("weather_days", len(days), n_window),
        C.Gate("days_with_full_24h", sum(1 for d in days if d["day_complete"]), None),
        C.Gate("days_with_missing_hours", len(gaps), 0, passed=len(gaps) == 0),
        C.Gate("strata_non_empty", len(strata), None, passed=len(strata) > 0),
        C.Gate("hourly_rows", len(hourly_rows), None),
        C.Gate("etrn_filled_hours", sum(len(v) for v in etrn_filled.values()), None),
        # 〔改訂(第330 B5)〕年間の窓では「先頭の日の出 < 末尾の日の出」は意味を失う(9/1 と 8/31 は
        # ほぼ同じ)。代わりに物理の検算: 日の出の最も早い日は 6 月・最も遅い日は 1 月・昼の最も長い日は
        # 夏至(6/21)の ±3 日の中。
        C.Gate("earliest_sunrise_month", sr_min["date"][:7], None, passed=sr_min["date"][5:7] == "06"),
        C.Gate("latest_sunrise_month", sr_max["date"][:7], None, passed=sr_max["date"][5:7] == "01"),
        C.Gate(
            "longest_day_near_june_solstice",
            longest["date"],
            None,
            passed="2026-06-18" <= longest["date"] <= "2026-06-24",
        ),
        C.Gate("window_first_day_present", WINDOW[0] in by_date, True),
        C.Gate("window_last_day_present", WINDOW[1] in by_date, True),
        # 報告だけ(落とさない): どの季節にも平日の各天候型が 1 日以上あるか
        C.Gate("every_season_has_each_weekday_type", len(missing_combos), None),
        C.Gate("stage_boundary_param_hash", C.param_hash(params)[:16], None),
    ]
    return res
