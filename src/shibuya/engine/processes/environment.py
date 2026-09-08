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
"""

from __future__ import annotations

import datetime as dt
from typing import Final

import numpy as np

from shibuya.agents.state import AgentState
from shibuya.core.hashing import blake3_hex
from shibuya.core.rng import stream
from shibuya.engine import resolve as R
from shibuya.world.assets import (
    HEAT_STAGE_ORDER,
    SHADOW_FRAMES_PER_DAY,
    SHADOW_MINUTES_PER_FRAME,
    ProcessAssets,
)
from shibuya.world.state import World

__all__ = [
    "DAYLIGHT_VOCAB",
    "HEAT_STAGE_TO_THERMAL",
    "SHADE_FACTOR",
    "THERMAL_STEP_MINUTES",
    "FALLBACK_THERMAL",
    "RNG_DOMAIN",
    "select_day",
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


def select_day(master_seed: int | str, stratum: str, strata: dict[str, list[str]]) -> str:
    """層 → 実日(決定論)。``build.field.w13_weather.select_day`` と同型。

    同じ ``(master_seed, stratum, 候補集合)`` は常に同じ日を返す。候補は日付昇順に固定。

    Args:
        master_seed: manifest の ``master_seed``。
        stratum: ``"平日|晴"`` のような層名。
        strata: 層 → 候補日のリスト。

    Returns:
        選ばれた実日(``"YYYY-MM-DD"``)。

    Raises:
        KeyError: 層に候補日が無い。
    """
    days = strata.get(stratum)
    if not days:
        raise KeyError(f"層に候補日が無い: {stratum!r}")
    counter = int(blake3_hex(stratum.encode("utf-8"))[:16], 16)
    rng = stream(master_seed, RNG_DOMAIN, counter)
    return sorted(days)[int(rng.integers(0, len(days)))]


class EnvironmentProcess:
    """昼夜(``daynight_solar``)+ 天候・体感温度(``weather``)。

    Args:
        world / agents: 世界・個体(**読むだけ**。書き込みは ``engine.resolve`` の口)。
        passets: ``world.assets.ProcessAssets``。
        master_seed: 実日の乱択に使う seed。
        day_index: 曜日(0=月曜)。
        tick_seconds: 1 tick の秒数。

    Attributes:
        replay_date: 再生する実日(資産が無ければ ``""``)。
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
        prefer_shadow_days: bool = True,
    ) -> None:
        self.prefer_shadow_days = bool(prefer_shadow_days)
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
        self._sunrise = 5.0 * 60.0
        self._sunset = 19.0 * 60.0
        self._cell_point: np.ndarray | None = None
        self._shade_cache_frame = -1
        self._shade: np.ndarray = np.zeros(world.n_cells, dtype=bool)
        self._pick_day()

    # ------------------------------------------------------------------ 実日の決定
    def _weekday_kind(self) -> str:
        """曜日(0=月曜)→ W13 の曜日種別。祝日は W13 側の欄が持つ(mock 日課は持たない)。"""
        return "土休" if self.day_index % 7 >= 5 else "平日"

    def _pick_day(self) -> None:
        a = self.assets
        if not a.has_weather:
            return
        kind = self._weekday_kind()
        strata: dict[str, list[str]] = {}
        for i, s in enumerate(a.weather_stratum):
            strata.setdefault(s, []).append(a.weather_dates[i])
        types = sorted({a.weather_type[i] for i in range(len(a.weather_dates))
                        if a.weather_weekday_kind[i] == kind})
        if not types:  # その曜日種別の候補日が無い → 全層から引く
            kind = a.weather_weekday_kind[0]
            types = sorted({a.weather_type[i] for i in range(len(a.weather_dates))
                            if a.weather_weekday_kind[i] == kind})
        if self.prefer_shadow_days and a.shadow_dates:
            # **expedient**: W9(影グリッド)は 1 再生日ぶんしか無い(D-W10 の容量宣言のため)。
            # 影のある日を引ける層に絞らないと日陰係数 0.86 が一度も効かない=憲法5 の
            # 「宣言した届き先が消える」再発。W9 を層別に増やしたら本分岐を外す。
            covered = sorted(
                {a.weather_type[i] for i in range(len(a.weather_dates))
                 if a.weather_weekday_kind[i] == kind and a.weather_dates[i] in a.shadow_dates}
            )
            if covered:
                types = covered
                strata = {
                    s: [d for d in days if d in a.shadow_dates]
                    for s, days in strata.items()
                    if any(d in a.shadow_dates for d in days)
                }
        rng = stream(self.master_seed, RNG_DOMAIN, 0)
        wtype = types[int(rng.integers(0, len(types)))]
        self.stratum = f"{kind}|{wtype}"
        self.replay_date = select_day(self.master_seed, self.stratum, strata)
        self._row = a.day_index_of(self.replay_date)
        if a.sunrise_min is not None and self._row >= 0:
            sr = float(a.sunrise_min[self._row])
            ss = float(a.sunset_min[self._row])
            if np.isfinite(sr):
                self._sunrise = sr
            if np.isfinite(ss):
                self._sunset = ss
        if a.has_shadow:
            self._planes = a.shadow_planes(self.replay_date)
            self._cell_point = a.cell_street_point
        if self._planes is None:
            self.shadow_missing = 1

    # ------------------------------------------------------------------ 1 tick
    def _minute_of_day(self, tick: int) -> int:
        return int(int(tick) * self.tick_seconds // 60) % 1_440

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
        hour = min(23, max(0, minute // 60))
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
