"""engine.processes.logistics — 宅配ラストマイル・バス/タクシー・道路工事(§7.2 前倒し)。

担当する台帳行(``world.processes.first_batch.PULLED_FORWARD_DECLARATIONS``)
- ``delivery_last_mile``(``AB-PARCEL-ALLOCATION``・contributes=**W2**)
  「日次個数が全国50億3,147万個の区按分(W2・≈2.7万個/日)の上界 band に収まる」。
- ``bus_taxi_operation``(``AB-DISPATCH``・PlanSpec ``plan.bus_timetable``・contributes=D6/D7)。
- ``road_works_occupancy``(``AB-ROADWORK-FREQ``・PlanSpec ``plan.road_works``)。

expedient(本モジュール分・全て「返済対象」)
- 宅配: 区按分 **27,000 個/日** をさらに **bbox 面積比**(セル数×1万 m² ÷ 渋谷区 15.11 km²)で
  按分する。セルへの配分は**世帯数(mock 日課の自宅セル度数)**に比例。実データ(区別実績)は空欄。
- 宅配の時間帯カーブ(08-21 時の 14 段)は自前。再配達(``attempt_count``)は C4 では立てない。
- バス: ODPT GTFS が未取得なので **PlanSpec は等間隔(06:00-23:00・10 分間隔)** で合成する。
  停留所は OSM ``highway=bus_stop``(127 点)をセルへ写像した実データ。
  **乗降は C4 では作らない**(台帳 ``occupancy`` は 0 のまま)=「運行が可視物として起きる」だけ。
- 道路工事: 夜間(22:00-05:00)に辺を無作為に占用する。**歩行グラフの next-hop は前計算表
  (W3)なので迂回は作らない**——占用は「通れなくなった辺」の記録と、その辺が載るセルの
  ``blocked_cells`` フラグまで。迂回は Phase 3(動的経路)へ返済。
"""

from __future__ import annotations

from typing import Final

import numpy as np

from shibuya.core.rng import stream
from shibuya.world.assets import ProcessAssets
from shibuya.world.processes.records import DEVIATION_CODES, DeviationVocab
from shibuya.world.state import World

__all__ = [
    "PARCELS_PER_DAY_WARD",
    "SHIBUYA_WARD_AREA_M2",
    "CELL_AREA_M2",
    "PARCEL_HOUR_CURVE",
    "BUS_HEADWAY_MIN",
    "BUS_SERVICE_WINDOW",
    "ROADWORK_WINDOW",
    "ROADWORKS_PER_NIGHT",
    "LastMileProcess",
    "BusTaxiProcess",
    "RoadWorksProcess",
]

_SCHEDULED: Final[int] = DEVIATION_CODES[DeviationVocab.SCHEDULED]
_REPLACEMENT: Final[int] = DEVIATION_CODES[DeviationVocab.REPLACEMENT]
MINUTES_PER_DAY: Final[int] = 1_440

#: 渋谷区への按分後の宅配個数[個/日](台帳 W2 の「≈2.7万個/日」・expedient)。
PARCELS_PER_DAY_WARD: Final[int] = 27_000
#: 渋谷区の面積[m²](15.11 km²)。
SHIBUYA_WARD_AREA_M2: Final[float] = 15.11e6
#: セル 1 つの面積[m²](W2 の 100 m 格子)。
CELL_AREA_M2: Final[float] = 100.0 * 100.0
#: 配達の時間帯カーブ(08-21 時の相対重み・expedient)。
PARCEL_HOUR_CURVE: Final[tuple[tuple[int, float], ...]] = (
    (8, 0.04), (9, 0.08), (10, 0.10), (11, 0.10), (12, 0.06), (13, 0.08), (14, 0.09),
    (15, 0.09), (16, 0.08), (17, 0.07), (18, 0.07), (19, 0.07), (20, 0.05), (21, 0.02),
)

#: バスの運行間隔[分](expedient)。
BUS_HEADWAY_MIN: Final[int] = 10
#: バスの運行帯[分](06:00-23:00・expedient)。
BUS_SERVICE_WINDOW: Final[tuple[int, int]] = (6 * 60, 23 * 60)

#: 道路占用の時間帯[分](22:00-05:00・expedient)。
ROADWORK_WINDOW: Final[tuple[int, int]] = (22 * 60, 5 * 60)
#: 1 晩に立つ工事件数(expedient)。
ROADWORKS_PER_NIGHT: Final[int] = 6


def _minute(tick: int, tick_seconds: int) -> int:
    return int(int(tick) * int(tick_seconds) // 60) % MINUTES_PER_DAY


class LastMileProcess:
    """宅配ラストマイル(世帯数按分 × 時間帯カーブ)。

    Attributes:
        parcels_per_cell: ``(n_cells,)`` その日の予定個数。
        delivered: ``(n_cells,)`` 配達済み個数。
    """

    process_ids: Final[tuple[str, ...]] = ("delivery_last_mile",)
    ablation_id: Final[str] = "AB-PARCEL-ALLOCATION"

    def __init__(
        self,
        world: World,
        *,
        household_per_cell: np.ndarray | None = None,
        master_seed: int | str = 1,
        day_index: int = 0,
        tick_seconds: int = 60,
        actual_log=None,
    ) -> None:
        self.world = world
        self.tick_seconds = int(tick_seconds)
        self.log = actual_log
        n = world.n_cells
        self.bbox_share = min(
            1.0, float(n) * CELL_AREA_M2 / SHIBUYA_WARD_AREA_M2
        )
        self.parcels_today = int(round(PARCELS_PER_DAY_WARD * self.bbox_share))
        w = (
            np.ones(n, dtype=np.float64) if household_per_cell is None
            else np.asarray(household_per_cell, dtype=np.float64)[:n]
        )
        if w.size < n:
            w = np.pad(w, (0, n - w.size))
        total = float(w.sum())
        share = w / total if total > 0 else np.full(n, 1.0 / max(1, n))
        raw = share * self.parcels_today
        self.parcels_per_cell = np.floor(raw).astype(np.int64)
        # 端数はセル索引の昇順で決定論に配る(乱数を使わない)
        rest = self.parcels_today - int(self.parcels_per_cell.sum())
        if rest > 0 and n:
            order = np.argsort(-(raw - np.floor(raw)), kind="stable")[:rest]
            self.parcels_per_cell[order] += 1
        self.delivered = np.zeros(n, dtype=np.int64)
        self.n_batches = 0
        self._hours = {h: w_ for h, w_ in PARCEL_HOUR_CURVE}
        self._cum = 0
        _ = stream(master_seed, "world.delivery_last_mile", int(day_index))  # 予約(再配達=Phase 3)

    @property
    def active(self) -> bool:
        return self.parcels_today > 0 and self.world.n_cells > 0

    def step(self, tick: int) -> None:
        if not self.active:
            return
        minute = _minute(tick, self.tick_seconds)
        hour = minute // 60
        weight = self._hours.get(hour)
        if weight is None or minute % 60:
            return
        want = np.floor(self.parcels_per_cell * float(weight)).astype(np.int64)
        room = np.maximum(0, self.parcels_per_cell - self.delivered)
        qty = np.minimum(want, room)
        live = np.flatnonzero(qty > 0)
        if live.size == 0:
            return
        self.delivered[live] += qty[live]
        self.n_batches += int(live.size)
        if self.log is not None:
            self.log.append_many(
                self.process_ids[0], live,
                np.full(live.size, int(tick), dtype=np.int64),
                np.full(live.size, _REPLACEMENT, dtype=np.int8),
            )

    def counters(self) -> dict[str, float]:
        return {
            "planned": float(self.parcels_today),
            "delivered": float(int(self.delivered.sum())),
            "batches": float(self.n_batches),
            "bbox_share": float(self.bbox_share),
        }

    def summary(self) -> str:
        if not self.active:
            return "宅配ラストマイル: 対象セルなし(休む)"
        return (
            f"宅配ラストマイル: 予定 {self.parcels_today:,} 個 "
            f"(区 {PARCELS_PER_DAY_WARD:,} × bbox 面積比 {self.bbox_share:.3f}=expedient) / "
            f"配達 {int(self.delivered.sum()):,} 個 / 便 {self.n_batches:,}"
        )


class BusTaxiProcess:
    """バス・タクシー運行(等間隔 PlanSpec + 停留所への到着イベント)。

    Attributes:
        stop_cell: ``(n_stops,)`` 停留所のセル索引。
        n_arrivals: 到着イベント数。
    """

    process_ids: Final[tuple[str, ...]] = ("bus_taxi_operation",)
    ablation_id: Final[str] = "AB-DISPATCH"
    plan_spec_id: Final[str] = "plan.bus_timetable"

    def __init__(
        self,
        world: World,
        passets: ProcessAssets,
        *,
        tick_seconds: int = 60,
        actual_log=None,
        headway_min: int = BUS_HEADWAY_MIN,
    ) -> None:
        self.world = world
        self.assets = passets
        self.tick_seconds = int(tick_seconds)
        self.log = actual_log
        self.headway = max(1, int(headway_min))
        cells = getattr(passets, "bus_stop_cell", None)
        self.stop_cell = (
            np.zeros(0, dtype=np.int64) if cells is None
            else np.asarray(cells, dtype=np.int64)
        )
        self.stop_cell = self.stop_cell[
            (self.stop_cell >= 0) & (self.stop_cell < max(1, world.n_cells))
        ]
        # 等間隔ダイヤ(停留所ごとにセル索引で位相をずらす=同時到着を作らない)
        self.phase = (
            (self.stop_cell % self.headway).astype(np.int64) if self.stop_cell.size
            else np.zeros(0, dtype=np.int64)
        )
        self.n_arrivals = 0
        self.n_departures_planned = self._planned_per_stop() * int(self.stop_cell.size)

    def _planned_per_stop(self) -> int:
        lo, hi = BUS_SERVICE_WINDOW
        return max(0, (hi - lo) // self.headway)

    @property
    def active(self) -> bool:
        return self.stop_cell.size > 0

    def step(self, tick: int) -> None:
        if not self.active:
            return
        minute = _minute(tick, self.tick_seconds)
        lo, hi = BUS_SERVICE_WINDOW
        if not (lo <= minute < hi):
            return
        due = np.flatnonzero(((minute - lo - self.phase) % self.headway) == 0)
        if due.size == 0:
            return
        self.n_arrivals += int(due.size)
        if self.log is not None:
            self.log.append_many(
                self.process_ids[0], due,
                np.full(due.size, int(tick), dtype=np.int64),
                np.full(due.size, _SCHEDULED, dtype=np.int8),
            )

    def counters(self) -> dict[str, float]:
        return {
            "stops": float(self.stop_cell.size),
            "arrivals": float(self.n_arrivals),
            "planned": float(self.n_departures_planned),
            "boardings": 0.0,  # C4 では乗降を作らない(返済対象)
        }

    def summary(self) -> str:
        if not self.active:
            return "バス・タクシー: 停留所データが無い(休む)"
        return (
            f"バス・タクシー: 停留所 {self.stop_cell.size} / 到着 {self.n_arrivals:,} "
            f"(等間隔 {self.headway} 分・{BUS_SERVICE_WINDOW[0] // 60:02d}:00-"
            f"{BUS_SERVICE_WINDOW[1] // 60:02d}:00=expedient・乗降なし)"
        )


class RoadWorksProcess:
    """道路工事・占用(夜間の PlanSpec)。

    Attributes:
        blocked_cells: ``(n_cells,)`` bool。占用中の辺が載るセル。
        occupied_edges: いま塞いでいる辺の索引。
    """

    process_ids: Final[tuple[str, ...]] = ("road_works_occupancy",)
    ablation_id: Final[str] = "AB-ROADWORK-FREQ"
    plan_spec_id: Final[str] = "plan.road_works"

    def __init__(
        self,
        world: World,
        passets: ProcessAssets,
        *,
        master_seed: int | str = 1,
        day_index: int = 0,
        tick_seconds: int = 60,
        actual_log=None,
        n_works: int = ROADWORKS_PER_NIGHT,
    ) -> None:
        self.world = world
        self.assets = passets
        self.tick_seconds = int(tick_seconds)
        self.log = actual_log
        self.blocked_cells = np.zeros(world.n_cells, dtype=bool)
        self.occupied_edges = np.zeros(0, dtype=np.int64)
        self.n_started = 0
        self.n_finished = 0
        edge_cell = getattr(passets, "edge_cell", None)
        n_edges = 0 if edge_cell is None else int(np.asarray(edge_cell).size)
        g = stream(master_seed, "world.road_works", int(day_index))
        k = min(int(n_works), n_edges)
        self.planned_edges = (
            np.sort(g.choice(n_edges, size=k, replace=False)).astype(np.int64)
            if k > 0 else np.zeros(0, dtype=np.int64)
        )
        self.edge_cell = (
            np.zeros(0, dtype=np.int64) if edge_cell is None
            else np.asarray(edge_cell, dtype=np.int64)
        )

    @property
    def active(self) -> bool:
        return self.planned_edges.size > 0

    def step(self, tick: int) -> None:
        if not self.active:
            return
        minute = _minute(tick, self.tick_seconds)
        lo, hi = ROADWORK_WINDOW
        night = (minute >= lo) or (minute < hi)  # 日跨ぎの窓
        if night and self.occupied_edges.size == 0:
            self.occupied_edges = self.planned_edges
            cells = self.edge_cell[self.occupied_edges]
            cells = cells[(cells >= 0) & (cells < self.world.n_cells)]
            self.blocked_cells[:] = False
            self.blocked_cells[cells] = True
            self.n_started += int(self.occupied_edges.size)
            if self.log is not None:
                self.log.append_many(
                    self.process_ids[0], self.occupied_edges,
                    np.full(self.occupied_edges.size, int(tick), dtype=np.int64),
                    np.full(self.occupied_edges.size, _SCHEDULED, dtype=np.int8),
                )
        elif (not night) and self.occupied_edges.size:
            self.n_finished += int(self.occupied_edges.size)
            self.occupied_edges = np.zeros(0, dtype=np.int64)
            self.blocked_cells[:] = False

    def counters(self) -> dict[str, float]:
        return {
            "started": float(self.n_started),
            "finished": float(self.n_finished),
            "occupied_now": float(self.occupied_edges.size),
            "blocked_cells": float(int(self.blocked_cells.sum())),
        }

    def summary(self) -> str:
        if not self.active:
            return "道路工事・占用: 道路データが無い(休む)"
        return (
            f"道路工事・占用: 着手 {self.n_started:,} / 撤去 {self.n_finished:,} / "
            f"いま占用 {self.occupied_edges.size} 辺・{int(self.blocked_cells.sum())} セル"
            "(迂回は作らない=記録のみ)"
        )
