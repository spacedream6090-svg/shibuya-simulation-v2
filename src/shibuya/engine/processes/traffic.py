"""engine.processes.traffic — 断面自動車交通(C 類 + B 類域外発生・§7.2 初回実装)。

正典
- 世界過程設計書 §7.2 初回実装(第1陣): 「**断面自動車交通(C 類+B 類域外発生)**」・
  expedient 欄「**通過交通比率**」。台帳側は ``first_batch._TRAFFIC``
  (``kind=EXTERNAL_SYSTEM``・``executor=engine_rule``・conf 0.4・``AB-THROUGH-TRAFFIC-RATIO``・
  reaches=聴覚: 静的場 / contributes=**D5′・D5**)。
- 同 §1 B 類「**bbox の外**で進行する運行・供給」。断面を通過する車は bbox 外で発生する。
- 世界データ構築仕様書 **D-W11**: 道路交通センサス R3 の (23)昼間12h交通量・(24)24h・
  (27)大型車混入率・(32)旅行速度。「**tertiary 以下=距離減衰+既定交通量(expedient)**」。

入力
    W10(静的騒音場)の構築段が同じセンサス行から作った **klass 別既定**
    (``data/world/v2/W10.header.json`` の ``notes.census_defaults``)を定数表として持つ。
    ``build`` は実行時に import できない(層契約)ので**値を転記**する。転記の一致は
    ``tests/engine/processes/test_traffic.py`` がヘッダ JSON と突き合わせて機械検査する。

出力
    - ``edge_hourly``: ``(n_edges, 24)`` の断面交通量[台/時]。**Σ_h = 24 時間交通量**(検算)。
    - ``cell_vehicles``: ``(n_cells,)`` のいまの時間帯のセル別台数(騒音の動的項の素・第2陣)。
    - ``daily_vehicle_km``: 日次の車走行キロ(診断行)。

expedient(本モジュール分)
- 時間帯配分=昼間 12h(7-18 時)に Q12 を一様、残り 12h に (Q24−Q12) を一様(W10 と同じ)。
- **通過交通比率**(B 類 = bbox 外発生の割合)。センサスは OD を持たないので値は自前。
- 辺のセル=始点ノードのセル(辺が跨るセルへは配らない)。
"""

from __future__ import annotations

from typing import Final

import numpy as np

from shibuya.world.assets import ProcessAssets
from shibuya.world.state import World

__all__ = [
    "KLASS_Q12",
    "KLASS_Q24",
    "DAY12_HOURS",
    "THROUGH_TRAFFIC_RATIO",
    "TrafficProcess",
]

#: klass → 昼間 12 時間交通量[台](W10 の ``census_defaults.q12`` の転記)。
KLASS_Q12: Final[dict[str, float]] = {
    "primary": 24_245.0,
    "secondary": 11_899.0,
    "tertiary": 3_569.7,
    "residential": 1_189.9,
    "unclassified": 1_189.9,
    "living_street": 594.95,
    "service": 356.97,
}
#: klass → 24 時間交通量[台](W10 の ``census_defaults.q24`` の転記)。
KLASS_Q24: Final[dict[str, float]] = {
    "primary": 34_486.0,
    "secondary": 15_826.0,
    "tertiary": 4_747.8,
    "residential": 1_582.6,
    "unclassified": 1_582.6,
    "living_street": 791.3,
    "service": 474.78,
}
#: センサスの「昼間 12 時間」= 7-18 時(W10 の ``census_day12_hours``)。
DAY12_HOURS: Final[tuple[int, ...]] = tuple(range(7, 19))

#: 通過交通(B 類 = bbox 外で発生し断面を抜ける)の比率。**expedient・出典なし**。
THROUGH_TRAFFIC_RATIO: Final[float] = 0.55


class TrafficProcess:
    """断面自動車交通(時間帯別)。世界状態は書かず、場を持つだけ。

    Attributes:
        edge_hourly: ``(n_edges, 24)`` 台/時。
        cell_hourly: ``(n_cells, 24)`` 台/時(辺を始点セルへ集約)。
        cell_vehicles: いまの時間帯のセル別台数。
        daily_vehicle_km: 日次の車走行キロ[台·km]。
    """

    process_ids: Final[tuple[str, ...]] = ("vehicle_cross_section",)
    ablation_id: Final[str] = "AB-THROUGH-TRAFFIC-RATIO"

    def __init__(
        self,
        world: World,
        passets: ProcessAssets,
        *,
        tick_seconds: int = 60,
        through_ratio: float = THROUGH_TRAFFIC_RATIO,
    ) -> None:
        self.world = world
        self.assets = passets
        self.tick_seconds = int(tick_seconds)
        self.through_ratio = float(through_ratio)
        self.hour = -1
        n_cells = world.n_cells
        self.edge_hourly = np.zeros((0, 24), dtype=np.float64)
        self.cell_hourly = np.zeros((n_cells, 24), dtype=np.float64)
        self.cell_vehicles = np.zeros(n_cells, dtype=np.float64)
        self.daily_vehicle_km = 0.0
        self.q24 = np.zeros(0, dtype=np.float64)
        self._build()

    @property
    def active(self) -> bool:
        return self.edge_hourly.shape[0] > 0

    def _build(self) -> None:
        a = self.assets
        if not a.has_road:
            return
        names = a.edge_klass_names
        q12 = np.array([KLASS_Q12.get(n, 0.0) for n in names], dtype=np.float64)
        q24 = np.array([KLASS_Q24.get(n, 0.0) for n in names], dtype=np.float64)
        code = np.asarray(a.edge_klass_code, dtype=np.int64)
        e12 = q12[code]
        e24 = q24[code]
        night = np.maximum(e24 - e12, 0.0)
        hourly = np.empty((code.size, 24), dtype=np.float64)
        day_mask = np.zeros(24, dtype=bool)
        day_mask[list(DAY12_HOURS)] = True
        hourly[:, day_mask] = (e12 / float(len(DAY12_HOURS)))[:, None]
        hourly[:, ~day_mask] = (night / float(24 - len(DAY12_HOURS)))[:, None]
        self.edge_hourly = hourly
        self.q24 = e12 + night  # 検算の右辺(Σ_h hourly = q12 + (q24-q12))
        length_km = np.asarray(a.edge_length_m, dtype=np.float64) / 1_000.0
        self.daily_vehicle_km = float((self.q24 * length_km).sum())
        cell = np.asarray(a.edge_cell, dtype=np.int64)
        ok = (cell >= 0) & (cell < self.world.n_cells)
        agg = np.zeros((self.world.n_cells, 24), dtype=np.float64)
        if ok.any():
            for h in range(24):  # 逐次ループ宣言: 24 時間ぶん(起動時 1 回)
                agg[:, h] = np.bincount(
                    cell[ok], weights=hourly[ok, h], minlength=self.world.n_cells
                )[: self.world.n_cells]
        self.cell_hourly = agg

    def step(self, tick: int) -> None:
        """時間帯が変わったときだけ場を差し替える(tick あたり O(1))。"""
        if not self.active:
            return
        hour = int(int(tick) * self.tick_seconds // 3_600) % 24
        if hour == self.hour:
            return
        self.hour = hour
        self.cell_vehicles = self.cell_hourly[:, hour]

    # ------------------------------------------------------------------ 診断
    @property
    def through_vehicle_km(self) -> float:
        """B 類(域外発生)ぶんの車走行キロ[台·km](通過交通比率=expedient)。"""
        return self.daily_vehicle_km * self.through_ratio

    def counters(self) -> dict[str, float]:
        return {
            "road_edges": float(self.edge_hourly.shape[0]),
            "daily_vehicle_km": self.daily_vehicle_km,
            "through_vehicle_km": self.through_vehicle_km,
            "hour": float(self.hour),
            "cell_vehicles_now": float(self.cell_vehicles.sum()),
        }

    def summary(self) -> str:
        if not self.active:
            return "断面自動車交通: W1 道路が無い(合成世界)"
        return (
            f"断面自動車交通: 辺 {self.edge_hourly.shape[0]:,} / "
            f"車走行キロ {self.daily_vehicle_km:,.0f} 台·km/日 "
            f"(うち通過 {self.through_vehicle_km:,.0f}・比率 {self.through_ratio:.2f}=expedient)"
        )
