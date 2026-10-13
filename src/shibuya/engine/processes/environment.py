"""engine.processes.environment — 昼夜・天候・体感温度(D-R2-5 第1陣の 1-2 行目)。

正典
- 世界過程設計書 §6 D-R2-5: 「**第1陣**=昼夜(日照=B3)・天候(気象庁実測の**特定日を再生**
  =B3・体感温度)…」。台帳側の宣言は ``world.processes.first_batch`` の
  ``daynight_solar`` / ``weather``(reaches=内受容・人物③)。
- 世界データ構築仕様書 **D-W15**(気象再生日): 推奨(c)=**実日ブートストラップ**。
  「乱択するのは『どの実日を引くか』」「候補集合=季節×曜日種別×天候型の層別」
  「ランごとに manifest の seed で層内から乱択(再現可能)」「合成乱数気象は不採用」。
- 知覚契約書 §3 内受容: 「満腹・体力・**体感温度(0-10)**/源=エンジン算術+**影グリッド
  (係数0.86)**/B5(閾値割れ)/mechanism/台帳行=日陰0.86」。
- 同 §2.4 正規化規約⑨(5 分丸め)= D-W10 の影グリッド刻みと同一 → **5 分ごとに評価**。

**設計書との食い違い(親へ報告・解決しない)**
1. D-R2-5 は昼夜・天候を「B3」と書くが、知覚契約書 §3 の表に **B3 の行が無い**
   (``first_batch`` の PROPOSED と同じ指摘)。本モジュールは B3 を発明せず、
   届き先を**内受容**(体感温度)と**人物③**(``m_light`` の昼夜)に取る。
2. ``build.field.w13_weather.select_day`` と**同じ規則**が要るが、import-linter 契約
   「build は実行時に import されない」により再利用できない。よって本モジュールが
   同型の関数を持つ(**乱数ドメインは ``engine.processes.environment``** で構築段とは別)。
   同じ層・同じ seed でも構築段と同じ日が出るとは限らない=**expedient**。

expedient(本モジュール分)
- 暑さ段(WBGT 21/25/28/31 は公的指針=mechanism)→ 体感温度 0-10 の写像
  ``HEAT_STAGE_TO_THERMAL``(契約書は 0-10 のスケールだけを与え、写像を与えていない)。
- 日陰係数 0.86 の**掛け先**を「体感温度の生値」にした(契約書は係数の値だけを与える)。
- セルの日陰=**セル代表点に最も近い W10 街路点 1 点**の日陰ビット(セル内の分布は持たない)。
- 影グリッドが無い日(``w9_shadow_<date>.npy`` は 2026-07-28 の 1 日ぶんだけ実在)は
  **全セル日向**として扱い ``shadow_missing`` を計数する。
- 気象資産が無い世界(合成)は「穏やかな 1 日」= 体感温度 5 の固定値。

〔改訂(第330・10e B6・RET)〕天気の規則は ``calendar``(ユーザーの答え 1-3)。10e より前の ``legacy``(再生日を層から一様に
引き、影のある日に絞り、日の出と日の入りと影も再生日)と ``select_day``・``prefer_shadow_days`` は版上げ 1 回目の後に消した
(旧値の再現は第330 ACT の commit で記録):

1. 天気(雨・気温・湿度・天候型・WBGT の入力)は**再生日**の W13 の行から。日の出・日の入り・太陽高度・影は**暦の日付**
   (``calendar.date_of_day``)から計算する(``engine.solar``・影は ``w9_shadow_<暦の日付>.npy``)。WBGT は「再生日の
   気温・湿度・風・日照 × 暦の日付の太陽高度」で計算し直す(構築段と同じ式。再生日=暦の日付なら W13 の値と同じ)。
2. 再生日の既定は**その日の実際の天気**: 暦の日付が W13 の窓の中(行がある)なら再生日=暦の日付。
3. **揺らすとき**(``run_day(weather_perturb=True)``・``--weather-perturb``=``perturbed``。アンサンブルは環境の seed を
   変えて回す)と暦の日付が窓の外のときは、同じ**季節**
   (気象庁の区分)× **平日/土休** × **天候型**の層の中から、窓の中で実際に起きた日数の割合で引く(天候型を日数の
   割合で引き、その型の日を一様に引く)。層が空なら隣の季節へ広げ(次に全季節・最後に平日/土休を問わず)警告する
   (**expedient**・未リサーチ)。「再生日は影のある日に絞る」は使わない(影は暦の日付で引く)。
4. 暦の日付の影が無いときは止めずに、いちばん近い日付の影を読み(同じ近さなら前の日)、警告と manifest の記録
   (``weather.days[].shadow_fallback``)を残す(**expedient**)。
5. 描画の天気(B3)は ``b3_words`` で同じ規則から作る(天候の語=再生日の行・日照の語=暦の日付の日の出と日の入り・
   暑さの語=体感温度と同じ暑さ段)。
6. 複数日のランは日ごとに暦の日付が進み、その日の規則で引き直す(乱数の鍵は環境の seed と日番号)。
"""

from __future__ import annotations

import datetime as dt
import math
import warnings
from typing import Any, Final

import numpy as np

from shibuya.agents.state import AgentState
from shibuya.core.hashing import blake3_hex
from shibuya.core.rng import stream
from shibuya.engine import resolve as R
from shibuya.engine import solar as SOL
from shibuya.engine.calendar import SEASON_OF_MONTH, WEATHER_SCHEME, SimCalendar
from shibuya.world.assets import (
    HEAT_STAGE_ORDER,
    SHADOW_FRAMES_PER_DAY,
    SHADOW_MINUTES_PER_FRAME,
    ProcessAssets,
    file_sha256,
)
from shibuya.world.state import World
from shibuya.core.time_consts import MINUTES_PER_DAY, MINUTES_PER_HOUR, SECONDS_PER_MINUTE

__all__ = [
    "DAYLIGHT_VOCAB",
    "HEAT_STAGE_TO_THERMAL",
    "SHADE_FACTOR",
    "THERMAL_STEP_MINUTES",
    "FALLBACK_THERMAL",
    "RNG_DOMAIN",
    "SEASON_NEIGHBOURS",
    "WEATHER_EXPEDIENTS",
    "WeatherWarning",
    "calendar_candidates",
    "nearest_shadow_date",
    "sample_calendar_day",
    "EnvironmentProcess",
]

#: 日照の 3 値(W13/知覚契約書 §3 の「日照」欄と同じ並び)。
DAYLIGHT_VOCAB: Final[tuple[str, ...]] = ("夜明け前", "日中", "日没後")

#: 暑さ段(0-4)→ 体感温度(0-10)の写像。**expedient**(契約書はスケールだけを与える)。
HEAT_STAGE_TO_THERMAL: Final[tuple[int, ...]] = (2, 4, 6, 8, 10)

#: 日陰係数(知覚契約書 §3 内受容「係数0.86」・R3-2 決定)。**mechanism**。
SHADE_FACTOR: Final[float] = 0.86

#: 体感温度を評価する刻み[分](正規化規約⑨の 5 分丸め = D-W10 の影グリッド刻み)。
THERMAL_STEP_MINUTES: Final[int] = SHADOW_MINUTES_PER_FRAME

#: 気象資産が無い世界の体感温度(「穏やかな 1 日」= C2 の初期値と同値)。
FALLBACK_THERMAL: Final[int] = 5

#: 実日の乱択に使う乱数ドメイン(構築段 ``build.w13`` とは**別**=上記の食い違い 2)。
RNG_DOMAIN: Final[str] = "engine.processes.environment"

#: 10e(B6): 層が空のときに広げる隣の季節(気象庁の区分の前後)。
SEASON_NEIGHBOURS: Final[dict[str, tuple[str, str]]] = {
    "春": ("冬", "夏"), "夏": ("春", "秋"), "秋": ("夏", "冬"), "冬": ("秋", "春"),
}


#: 〔第330・ACT〕暦の規則(``calendar``)の expedient の宣言(親の決定 (3)=manifest と記録に書く)。manifest の
#: ``weather.expedients`` に載る(``calendar`` のランだけ)。どちらも未リサーチ。
WEATHER_EXPEDIENTS: Final[tuple[str, ...]] = (
    "天気の層が空のときに広げる順=隣の季節(前後 2 つ)→ 全季節 → 全季節で平日/土休を問わない(未リサーチ)",
    "暦の日付の影(W9)が無いときは、いちばん近い日付の影を読む・同じ近さなら前の日(未リサーチ)",
)


class WeatherWarning(UserWarning):
    """10e(B6): 天気の規則の警告(層を広げた・暦の日付の影が無く近い日の影を読んだ)。"""


def _season_of(iso: str) -> str:
    return SEASON_OF_MONTH[int(str(iso)[5:7])]


def calendar_candidates(passets: ProcessAssets, season: str, kind: str) -> tuple[list[int], str]:
    """10e(B6): 季節 × 平日/土休 の W13 の行(昇順の索引)と、広げた段(``""``=広げていない)。

    広げる順(層が空のとき・expedient): 隣の季節(前後 2 つ)→ 全季節 → 全季節で平日/土休を問わない。
    """
    a = passets
    seasons = [_season_of(d) for d in a.weather_dates]
    kinds = list(a.weather_weekday_kind)
    steps = (
        ("", {season}, True),
        ("隣の季節", {season, *SEASON_NEIGHBOURS[season]}, True),
        ("全季節", set(SEASON_NEIGHBOURS), True),
        ("全季節・平日/土休を問わず", set(SEASON_NEIGHBOURS), False),
    )
    for label, ss, same_kind in steps:  # 逐次ループ宣言: 段 4 つ × 行数(日の頭に 1 回)
        rows = [i for i in range(len(seasons)) if seasons[i] in ss and (not same_kind or kinds[i] == kind)]
        if rows:
            return rows, label
    return [], "候補なし"


def sample_calendar_day(
    master_seed: int | str, day: int, season: str, kind: str, passets: ProcessAssets
) -> tuple[str, str, str]:
    """10e(B6): 季節 × 平日/土休 × 天候型の層から、窓の中で実際に起きた日数の割合で再生日を引く。

    天候型を「その季節 × 平日/土休 の中の型ごとの日数」の割合で引き、その型の日を一様に引く(2 回の抽選・同じ
    Generator)。鍵は ``(環境の seed, RNG_DOMAIN, blake3("calendar|季節|平日/土休|日番号"))``。

    Returns:
        ``(再生日, 層の名前「季節|平日/土休|天候型」, 広げた段)``。
    """
    a = passets
    rows, widened = calendar_candidates(a, season, kind)
    if not rows:
        raise KeyError("W13 に候補日が無い")
    by_type: dict[str, list[str]] = {}
    for i in rows:
        by_type.setdefault(a.weather_type[i], []).append(a.weather_dates[i])
    types = sorted(by_type)
    counts = np.asarray([len(by_type[t]) for t in types], dtype=np.int64)
    key = f"calendar|{season}|{kind}|{int(day)}"
    rng = stream(master_seed, RNG_DOMAIN, int(blake3_hex(key.encode("utf-8"))[:16], 16))
    u = int(rng.integers(0, int(counts.sum())))
    wtype = types[int(np.searchsorted(np.cumsum(counts), u, side="right"))]
    days = sorted(by_type[wtype])
    date = days[int(rng.integers(0, len(days)))]
    i = a.day_index_of(date)
    return date, f"{_season_of(date)}|{a.weather_weekday_kind[i]}|{wtype}", widened


def nearest_shadow_date(dates: tuple[str, ...], target: str) -> str | None:
    """10e(B6): ``target`` にいちばん近い影の日(同じ近さなら前の日)。影が無ければ ``None``。"""
    if not dates:
        return None
    t = dt.date.fromisoformat(str(target))
    return min(dates, key=lambda d: (abs((dt.date.fromisoformat(d) - t).days), d))


class EnvironmentProcess:
    """昼夜(``daynight_solar``)+ 天候・体感温度(``weather``)。

    Args:
        world / agents: 世界・個体(**読むだけ**。書き込みは ``engine.resolve`` の口)。
        passets: ``world.assets.ProcessAssets``。
        master_seed: 実日の乱択に使う seed。
        day_index: 曜日(0=月曜)。``calendar`` が無いときだけ使う(旧い口)。
        tick_seconds: 1 tick の秒数。
        calendar: 暦の口(``engine.calendar.SimCalendar``・10a)。平日/土休はここから引く。

    Attributes:
        replay_date: 再生する実日(資産が無ければ ``""``)。
        shadow_sources: 10e(B0): 開いた影のファイル(``w9_shadow_<日付>.npy``)→ sha256。``engine.run`` が manifest の
            ``frozen_sources`` に ``process:`` を付けて写す(複数日のランでは日ごとに開いた全部)。
        daylight: 直近の日照 3 値(0=夜明け前 / 1=日中 / 2=日没後)。
        heat_stage: 直近の暑さ段(0-4)。
        wbgt: 直近の WBGT 推定値[℃](資産が無ければ NaN)。
    """

    #: 台帳(``world.processes.first_batch``)の対応行。
    process_ids: Final[tuple[str, ...]] = ("daynight_solar", "weather")

    def __init__(
        self,
        world: World,
        agents: AgentState,
        passets: ProcessAssets,
        *,
        master_seed: int | str = 1,
        day_index: int = 0,
        tick_seconds: int = 60,
        calendar: Any | None = None,
        perturbed: bool = False,
    ) -> None:
        #: 10e(B6): 天気の規則の名前(manifest の ``weather.scheme``=``calendar`` だけ)と、天気を揺らすか(``--weather-perturb``)
        self.weather_scheme = WEATHER_SCHEME
        self.perturbed = bool(perturbed)
        self.calendar = (
            calendar if calendar is not None
            else SimCalendar.default(int(day_index), tick_seconds=int(tick_seconds))
        )
        self.world = world
        self.agents = agents
        self.assets = passets
        self.master_seed = master_seed
        self.day_index = int(day_index)
        self.tick_seconds = int(tick_seconds)
        self.replay_date = ""
        self.stratum = ""
        self.daylight = 1
        self.heat_stage = 0
        self.wbgt = float("nan")
        self.n_updates = 0
        self.shadow_missing = 0
        self._planes = None
        self._row = -1
        self._sunrise = 5.0 * MINUTES_PER_HOUR
        self._sunset = 19.0 * MINUTES_PER_HOUR
        self._cell_point: np.ndarray | None = None
        self._shade_cache_frame = -1
        self._shade: np.ndarray = np.zeros(world.n_cells, dtype=bool)
        self.shadow_sources: dict[str, str] = {}
        #: 10e(B6): 暦の規則の時ごとの WBGT と暑さ段(``(24,)``・日の頭に作る)・暦の日付の日の出と日の入り(丸めない分)
        self._cal_wbgt: np.ndarray | None = None
        self._cal_stage: np.ndarray | None = None
        self._sun_exact: tuple[float | None, float | None] = (None, None)
        #: 10e(B6): 日ごとの天気の記録(manifest の ``weather.days``)と警告(``weather.warnings``)
        self.weather_days: dict[int, dict[str, Any]] = {}
        self.weather_warnings: list[str] = []
        self._pick_day()

    # ------------------------------------------------------------------ 実日の決定
    def _weekday_kind(self, day: int = 0) -> str:
        """日番号 → W13 の曜日種別(平日/土休)。暦の口の ``is_rest_day`` から引く(10a・#2)。

        ``day_index`` モード(既定)の暦は ``day_index % 7 >= 5`` と同じ値を返す(祝日を見ない)。
        """
        return "土休" if self.calendar.is_rest_day(int(day)) else "平日"

    def _pick_day(self, day: int = 0) -> None:
        """その日の再生日と太陽と影を決める(暦の規則=``_pick_day_calendar``)。"""
        self._pick_day_calendar(int(day))

    def _warn(self, msg: str) -> None:
        if msg not in self.weather_warnings:  # 再開で同じ日を引き直しても 1 回だけ記録する
            self.weather_warnings.append(msg)
        warnings.warn(msg, WeatherWarning, stacklevel=3)

    def _pick_day_calendar(self, day: int) -> None:
        """10e(B6): 天気=再生日の行・日の出と日の入りと太陽高度と影=暦の日付(モジュールの注の 1〜4)。"""
        a = self.assets
        cal_date = self.calendar.date_of_day(int(day))
        iso = cal_date.isoformat()
        self._sun_exact = SOL.sun_times(cal_date)
        self._sunrise, self._sunset = SOL.sun_minutes(cal_date)
        rec: dict[str, Any] = {"day": int(day), "calendar_date": iso, "replay_date": "", "stratum": "",
                               "how": "", "widened": "", "shadow_date": "", "shadow_fallback": False,
                               "sunrise_min": self._sunrise, "sunset_min": self._sunset}
        if a.has_weather:
            kind = self._weekday_kind(int(day))
            season = SEASON_OF_MONTH[cal_date.month]
            if not self.perturbed and iso in a.weather_dates:
                i = a.day_index_of(iso)
                replay, stratum, widened, how = iso, f"{season}|{a.weather_weekday_kind[i]}|{a.weather_type[i]}", "", "actual"
            else:
                replay, stratum, widened = sample_calendar_day(self.master_seed, int(day), season, kind, a)
                how = "sampled"
                if widened:
                    self._warn(f"天気の層 {season}|{kind} が W13 に無い({iso}): {widened}へ広げて引いた(expedient)")
            self.replay_date, self.stratum = replay, stratum
            self._row = a.day_index_of(replay)
            self._cal_heat(cal_date)
            rec.update(replay_date=replay, stratum=stratum, how=how, widened=widened)
        if a.has_shadow:
            sd = iso if iso in a.shadow_dates else nearest_shadow_date(a.shadow_dates, iso)
            if sd is not None:
                if sd != iso:
                    rec["shadow_fallback"] = True
                    self._warn(f"暦の日付 {iso} の影(W9)が無い: いちばん近い {sd} の影を読んだ(expedient)")
                self._planes = a.shadow_planes(sd)
                self._cell_point = a.cell_street_point
                self._note_shadow(sd)
                rec["shadow_date"] = sd if self._planes is not None else ""
        if self._planes is None:
            self.shadow_missing = 1
        self.weather_days[int(day)] = rec

    def _cal_heat(self, cal_date: dt.date) -> None:
        """10e(B6): 再生日の行の気象 × 暦の日付の太陽高度 → 時ごとの WBGT(2 桁に丸め=W13 と同じ)と暑さ段。

        WBGT の入力の列が無い資産は、再生日の行の WBGT と暑さ段をそのまま使う(警告)。
        """
        a = self.assets
        wbgt = np.full(24, np.nan, dtype=np.float64)
        stage = np.zeros(24, dtype=np.int8)
        r = self._row
        if r >= 0 and a.hourly_temp_c is not None and a.hourly_rh is not None:
            for h in range(24):  # 逐次ループ宣言: 24 時(日の頭に 1 回)
                w = SOL.hourly_wbgt(
                    cal_date, h, float(a.hourly_temp_c[r, h]), float(a.hourly_rh[r, h]),
                    float(a.hourly_wind_ms[r, h]) if a.hourly_wind_ms is not None else float("nan"),
                    float(a.hourly_sunshine_h[r, h]) if a.hourly_sunshine_h is not None else float("nan"),
                )
                if w is not None:
                    wbgt[h] = round(w, 2)
                    stage[h] = SOL.heat_stage(w)
        elif r >= 0:
            self._warn("W13 に WBGT の入力の列が無い: 再生日の行の WBGT と暑さ段をそのまま使う")
            wbgt[:] = a.hourly_wbgt[r]
            stage[:] = a.hourly_heat_stage[r]
        self._cal_wbgt, self._cal_stage = wbgt, stage

    def b3_sun_heat(self, hour: int) -> tuple[str, str]:
        """10e(B6): 描画の B3 の日照と暑さの語(時の中ほどを暦の日付の日の出・日の入りと比べる・暑さ=体感温度と同じ段)。"""
        h = min(23, max(0, int(hour)))
        sr, ss = self._sun_exact
        daylight = SOL.daylight_phase(h * MINUTES_PER_HOUR + 30.0, sr, ss)
        if self._cal_stage is None or self._cal_wbgt is None or not np.isfinite(self._cal_wbgt[h]):
            return daylight, ""
        return daylight, HEAT_STAGE_ORDER[int(self._cal_stage[h])]

    def weather_manifest(self) -> dict[str, Any]:
        """manifest の ``weather``(規則・揺らしたか・日ごとの暦の日付と再生日と層と影・警告)。"""
        out: dict[str, Any] = {
            "scheme": self.weather_scheme,
            "perturbed": bool(self.perturbed),
            "days": [dict(self.weather_days[d]) for d in sorted(self.weather_days)],
            "warnings": list(self.weather_warnings),
        }
        out["expedients"] = list(WEATHER_EXPEDIENTS)  # 〔第330・ACT〕expedient の宣言
        return out

    def _note_shadow(self, date: str) -> None:
        """10e(B0): 開いた影のファイルの sha256 を控える(同じ日は 1 回だけ読む)。"""
        if self._planes is None:
            return
        p = self.assets.shadow_path(date)
        if p is not None and p.name not in self.shadow_sources:
            self.shadow_sources[p.name] = file_sha256(p)

    def pick_day(self, day: int) -> None:
        """10d: 日の頭で ``day`` 日目の再生実日を引き直す(鍵は 10a の日番号つき・0 日目は起動時に引いた日)。

        日の出・日の入り・影の面はその日の実日から。日陰のキャッシュの印を戻す(次の更新で新しい面から作る)。
        直近の日照・暑さ段・WBGT・日陰の値は次の 5 分刻みの更新まで前の値のまま(更新の間も読まれる値=今と同じ扱い)。
        """
        self._planes = None
        self._cell_point = None
        self._row = -1
        self._sunrise = 5.0 * MINUTES_PER_HOUR
        self._sunset = 19.0 * MINUTES_PER_HOUR
        self._shade_cache_frame = -1
        self._pick_day(int(day))

    # ------------------------------------------------------------------ 1 tick
    def _minute_of_day(self, tick: int) -> int:
        return int(int(tick) * self.tick_seconds // SECONDS_PER_MINUTE) % MINUTES_PER_DAY

    def _shade_mask(self, minute: int) -> np.ndarray:
        """セル別の日陰フラグ(影グリッドが無ければ全て日向)。"""
        if self._planes is None or self._cell_point is None:
            return self._shade
        frame = (minute // SHADOW_MINUTES_PER_FRAME) % SHADOW_FRAMES_PER_DAY
        if frame == self._shade_cache_frame:
            return self._shade
        plane = np.asarray(self._planes[frame])
        p = np.asarray(self._cell_point, dtype=np.int64)
        ok = p >= 0
        out = np.zeros(self.world.n_cells, dtype=bool)
        if ok.any():
            idx = p[ok]
            byte = plane[idx >> 3]
            out[ok] = ((byte >> (7 - (idx & 7))) & 1).astype(bool)
        self._shade = out
        self._shade_cache_frame = frame
        return out

    def _heat_now(self, minute: int) -> tuple[int, float]:
        a = self.assets
        if not a.has_weather or self._row < 0:
            return -1, float("nan")
        hour = min(23, max(0, minute // MINUTES_PER_HOUR))
        if self._cal_stage is not None and self._cal_wbgt is not None:
            return int(self._cal_stage[hour]), float(self._cal_wbgt[hour])  # 10e(B6)
        stage = int(a.hourly_heat_stage[self._row, hour])
        return stage, float(a.hourly_wbgt[self._row, hour])

    def step(self, tick: int) -> None:
        """5 分刻みで日照・暑さ段・体感温度を更新する(ベクトル 1 本)。"""
        minute = self._minute_of_day(tick)
        if minute % THERMAL_STEP_MINUTES:
            return
        self.daylight = (
            1 if self._sunrise <= minute < self._sunset else (0 if minute < self._sunrise else 2)
        )
        stage, wbgt = self._heat_now(minute)
        self.wbgt = wbgt
        if stage < 0:
            # 合成世界: 穏やかな 1 日(固定)
            self.heat_stage = 0
            R.set_thermal(self.agents, np.full(self.agents.n, FALLBACK_THERMAL, dtype=np.uint8))
            self.n_updates += 1
            return
        self.heat_stage = stage
        base = float(HEAT_STAGE_TO_THERMAL[min(stage, len(HEAT_STAGE_TO_THERMAL) - 1)])
        shade = self._shade_mask(minute)
        per_cell = np.where(shade, base * SHADE_FACTOR, base)
        cell = self.agents.registry.cell.astype(np.int64)
        inside = (cell >= 0) & (cell < self.world.n_cells)
        value = np.where(inside, per_cell[np.maximum(cell, 0)], base)
        R.set_thermal(self.agents, np.rint(value).astype(np.int64))
        self.n_updates += 1

    # ------------------------------------------------------------------ 診断
    def is_night(self, tick: int | None = None) -> bool:
        """夜か(``p_notice`` の ``m_light`` 昼 1.0 / 夜 0.68・知覚契約書 §3.1)。

        ``daylight`` の 3 値(0=夜明け前 / 1=日中 / 2=日没後)のうち **1 以外**が夜。
        ``tick`` を渡すとその tick の分で判定する(``step`` を待たない)。
        """
        if tick is None:
            return self.daylight != 1
        minute = self._minute_of_day(int(tick))
        return not (self._sunrise <= minute < self._sunset)

    def counters(self) -> dict[str, float]:
        return {
            "replay_day_row": float(self._row),
            "updates": float(self.n_updates),
            "shadow_missing": float(self.shadow_missing),
            "shade_cells": float(int(self._shade.sum())),
            "daylight": float(self.daylight),
            "heat_stage": float(self.heat_stage),
            "wbgt": float(self.wbgt) if np.isfinite(self.wbgt) else 0.0,
        }

    def summary(self) -> str:
        name = HEAT_STAGE_ORDER[min(self.heat_stage, len(HEAT_STAGE_ORDER) - 1)]
        date = self.replay_date or "(合成・穏やかな1日)"
        return (
            f"環境: 再生日 {date} 層 {self.stratum or '-'} / "
            f"日照 {DAYLIGHT_VOCAB[self.daylight]} 暑さ {name} / 日陰セル {int(self._shade.sum())}"
        )

    @property
    def replay_datetime(self) -> dt.date | None:
        """再生日の ``datetime.date``(資産が無ければ ``None``)。"""
        if not self.replay_date:
            return None
        return dt.date.fromisoformat(self.replay_date)
