"""engine.solar — 太陽の位置(日の出・日の入り・太陽高度)と WBGT の推定(10e B6・第330)。

ユーザーの答え 1-3(2026-10-12):「影・日の出・日の入り・太陽の高さは、シミュレーション内の暦の日付から計算する
(太陽の位置は暦で決まる=物理に合う)。天気(雨・気温・湿度など)だけを再生日から取る」。天気の規則
``--weather-scheme calendar``(``engine.processes.environment``)がこのモジュールを使う。

**構築段 ``build.field.w13_weather`` と同じ式の写し**(import-linter の契約「build は実行時に import されない」のため
再利用できない=``engine.processes.environment.select_day`` と同じ扱い)。式・定数・演算の順は構築段と同じにして、
同じ日付・同じ入力なら**同じ浮動小数**を返す(``tests/engine/test_weather_calendar_10e.py`` が構築段の関数と突き合わせる)。

- 太陽の位置: NOAA General Solar Position Calculations の低次近似(1901〜2099 年で ±1 分級)。天頂角 90.833°
  (大気差 34' と太陽の半径 16')で日の出・日の入り(**mechanism**)。地点は世界の原点(W0 の ``origin_latlon``)。
- 日照の 3 値(夜明け前・日中・日没後): 時の中ほど(``h × 60 + 30`` 分)を日の出・日の入りと比べる(W13 の
  ``daylight`` 列と同じ規則)。
- WBGT の推定(屋外・Ono & Tonouchi 2014 型)と日射量の推定(``max(sin h, 0) × 0.9 × 日照率``)は構築段の
  **expedient** のまま(実況の WBGT・日射量は未取得)。暑さ段の境界 21/25/28/31 は環境省・日本生気象学会の指針
  (**mechanism**)。

逐次ループ宣言(P4): なし(日 1 回・時 24 回の算術。日の頭に 1 回)。
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Final

from shibuya.core.time_consts import HOURS_PER_DAY, MINUTES_PER_HOUR

__all__ = [
    "DAYLIGHT_VOCAB",
    "HEAT_BOUNDS",
    "LAT",
    "LON",
    "SOLAR_CONST_KW",
    "TZ_OFFSET_MIN",
    "WBGT_COEFF",
    "daylight_phase",
    "heat_stage",
    "hourly_wbgt",
    "solar_elevation_deg",
    "sun_minutes",
    "sun_times",
    "wbgt_estimate",
]

#: 世界の原点の緯度・経度(W0 ``world_crs.json`` の ``origin_latlon`` と ``build.geo.common.ORIGIN_LATLON``)。
LAT: Final[float] = 35.6595
LON: Final[float] = 139.70062
#: 日本標準時(分)。
TZ_OFFSET_MIN: Final[int] = 540
#: 日照の 3 値(W13・知覚契約書 §3 の「日照」欄と同じ並び)。
DAYLIGHT_VOCAB: Final[tuple[str, ...]] = ("夜明け前", "日中", "日没後")
#: 暑さ段の境界(WBGT ℃・環境省/日本生気象学会の指針)。
HEAT_BOUNDS: Final[tuple[float, ...]] = (21.0, 25.0, 28.0, 31.0)
#: WBGT 推定式の係数(構築段と同じ・expedient)。
WBGT_COEFF: Final[dict[str, float]] = {
    "ta": 0.735,
    "rh": 0.0374,
    "ta_rh": 0.00292,
    "sr": 7.619,
    "sr2": -4.557,
    "ws": -0.0572,
    "const": -4.064,
}
#: 日射量の推定の定数(kW/m²・構築段と同じ・expedient)。
SOLAR_CONST_KW: Final[float] = 0.9


def _solar_terms(date: dt.date, hour_utc: float) -> tuple[float, float]:
    """(赤緯 [rad], 均時差 [min])。"""
    doy = date.timetuple().tm_yday
    gamma = 2.0 * math.pi / 365.0 * (doy - 1 + (hour_utc - 12.0) / HOURS_PER_DAY)
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
    """日の出・日の入り(地方時の 0 時からの分)。極夜・白夜は ``(None, None)``。"""
    decl, eqtime = _solar_terms(date, 12.0 - tz_offset_min / MINUTES_PER_HOUR)
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


def sun_minutes(date: dt.date) -> tuple[float, float]:
    """日の出・日の入りを**分に丸めた値**(W13 の ``sunrise``/``sunset`` 列の ``HH:MM`` と同じ丸め=``round``)。

    極夜・白夜(この緯度では起きない)は今の既定と同じ 5:00/19:00。
    """
    sr, ss = sun_times(date)
    if sr is None or ss is None:
        return 5.0 * MINUTES_PER_HOUR, 19.0 * MINUTES_PER_HOUR
    return float(int(round(sr))), float(int(round(ss)))


def solar_elevation_deg(
    date: dt.date,
    local_min: float,
    lat: float = LAT,
    lon: float = LON,
    tz_offset_min: int = TZ_OFFSET_MIN,
) -> float:
    """地方時 ``local_min``(0 時からの分)の太陽高度 [deg]。"""
    hour_utc = (local_min - tz_offset_min) / MINUTES_PER_HOUR
    decl, eqtime = _solar_terms(date, hour_utc)
    true_solar_min = local_min + eqtime + 4.0 * lon - tz_offset_min
    ha = math.radians(true_solar_min / 4.0 - 180.0)
    lat_r = math.radians(lat)
    sin_h = math.sin(lat_r) * math.sin(decl) + math.cos(lat_r) * math.cos(decl) * math.cos(ha)
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_h))))


def daylight_phase(local_min: float, sunrise_min: float | None, sunset_min: float | None) -> str:
    """日照の 3 値(構築段の ``daylight_phase`` と同じ規則)。"""
    if sunrise_min is None or sunset_min is None:
        return DAYLIGHT_VOCAB[1] if sunrise_min is None else DAYLIGHT_VOCAB[0]
    if local_min < sunrise_min:
        return DAYLIGHT_VOCAB[0]
    if local_min < sunset_min:
        return DAYLIGHT_VOCAB[1]
    return DAYLIGHT_VOCAB[2]


def wbgt_estimate(temp_c: float, rh_pct: float, wind_ms: float, solar_kw: float) -> float:
    """WBGT の推定式(屋外・実況が無いときの代わり=expedient)。"""
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
    """WBGT → 暑さ段(0〜4)。"""
    for i, b in enumerate(HEAT_BOUNDS):
        if wbgt < b:
            return i
    return len(HEAT_BOUNDS)


def hourly_wbgt(
    date: dt.date, hour: int, temp_c: float, rh: float, wind_ms: float, sunshine_h: float
) -> float | None:
    """``date`` の太陽高度(時の中ほど)と、その時の気象(再生日の行)から WBGT の推定値(丸めない)。

    構築段の 1 時間分の計算と同じ(気温か湿度が欠けていれば ``None``・風と日照の欠けは 0)。NaN は欠けとして扱う。
    """
    if temp_c is None or rh is None or math.isnan(temp_c) or math.isnan(rh):
        return None
    mid = hour * MINUTES_PER_HOUR + 30.0
    elev = solar_elevation_deg(date, mid)
    ratio = None if (sunshine_h is None or math.isnan(sunshine_h)) else sunshine_h
    solar_kw = max(math.sin(math.radians(elev)), 0.0) * SOLAR_CONST_KW * (ratio or 0.0)
    wind = 0.0 if (wind_ms is None or math.isnan(wind_ms)) else wind_ms
    return wbgt_estimate(float(temp_c), float(rh), float(wind or 0.0), solar_kw)
