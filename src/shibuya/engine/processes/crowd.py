"""engine.processes.crowd — 混雑場・流れ・屋内占有・待ち行列(D-R2-5 第1陣 + §7.2 初回実装)。

正典
- 世界過程設計書 §6 D-R2-5: 「混雑場(密度段階=B4・人物①)」。台帳側は ``first_batch._CROWD``
  (reaches=人物①・聴覚: 密度項/contributes=D1′・D4′)と ``first_batch._INDOOR``
  (state_vars=``seats_total``/``seats_used``/``queue_len``/``balk_threshold``・
  reaches=人物②・contributes=D8・``AB-OCCUPANCY-CAPACITY``)。
- 同 §7.2 初回実装(第1陣): 「**屋内占有の集約(在席・待ち行列)**」。
- 同 §4 16行表 行2「施設の収容・占有・待ち行列」: 「エンジン全部(容量 c・**M/M/c 近似**・
  離脱閾値)。**席数換算式・回転率・離脱閾値=全部 expedient**(渋谷の実店舗席数は空欄)」。
- 知覚契約書 §3: 人物①「密度・**流れ**(Fruin LOS 型段階)/源=混雑場(C 類)/B4」・
  人物②「行列・人だかり・グループ(上位 k)/B4」。§3.2 B4「密度スカラー+流れ方向 25 tok」。

**設計書との食い違い(親へ報告・解決しない)**
    親指示は流れを「8 方位に量子化(または none)」とするが、知覚レンダラ(C3・凍結対象)の
    ``FLOW_WORDS`` は **3 値**(「一定です / 滞留気味です / 一方向に流れています」)で、
    方位語を持たない。よって B4 へ渡すのは **3 値の一貫性(coherence)側**にし、
    8 方位は ``flow_dir8`` として診断・将来のチャネル用に**併置**する(描画は変えない)。

**B4b への配線(配線済み・2026-09-08 更新)**
    ``queue_rows(k)`` が返す「行列: <店名>に<人数>人」の材料は、``engine.run`` が
    ``Renderer.prepare_tick(queues=runner.queue_rows(3))`` として毎 tick 渡している
    (``perception.renderer`` 側に差し込み口が付いた)。C3 当時の「B4b は固定文言・
    差し込み口が無い」という記述はもう成り立たない。本モジュールは材料を作るだけで、
    どう書くか(語彙・上位 k・トークン上限)は知覚契約書 §3.2 の管轄。

expedient(本モジュール分)
- 席数換算: カテゴリ別の**想定床面積**(実測なし)÷ 1 席あたり面積(飲食 2 m²・その他 4 m²)。
- 回転率: 在席の上限滞在 ``DWELL_MAX_TICKS``。
- 離脱閾値: ``WAIT_MAX_TICKS`` を超えたら並ぶのをやめる(``INTERRUPTED``)。
- 流れの 3 値化しきい値(``STILL_SHARE`` / ``COHERENT``)。
- M/M/c の平均待ちは**近似式の指標値**であって行動は駆動しない(観測欄のみ)。
"""

from __future__ import annotations

from typing import Final

import numpy as np

from shibuya.agents.state import Activity, AgentState
from shibuya.engine import resolve as R
from shibuya.world.state import World

__all__ = [
    "SEAT_AREA_M2",
    "FLOOR_AREA_M2_BY_CAT",
    "DEFAULT_FLOOR_AREA_M2",
    "DWELL_MAX_TICKS",
    "WAIT_MAX_TICKS",
    "STILL_SHARE",
    "COHERENT",
    "FLOW_NONE",
    "seats_for_categories",
    "CrowdProcess",
]

#: 1 席あたりの床面積[m²](expedient・16行表 行2「席数換算式=expedient」)。
SEAT_AREA_M2: Final[dict[str, float]] = {"food": 2.0, "nightlife": 2.0}
#: それ以外(物販・サービス等)の 1 席あたり面積[m²]。
DEFAULT_SEAT_AREA_M2: Final[float] = 4.0

#: カテゴリ別の**想定床面積**[m²](expedient・実測は空欄)。
FLOOR_AREA_M2_BY_CAT: Final[dict[str, float]] = {
    "food": 60.0,
    "nightlife": 80.0,
    "shop": 100.0,
    "service": 60.0,
    "office": 200.0,
    "hotel": 400.0,
    "school": 500.0,
    "education": 300.0,
    "leisure": 150.0,
    "hall": 300.0,
    "cinema": 200.0,
    "attraction": 200.0,
    "landmark": 150.0,
    # 合成世界のカテゴリ
    "コンビニ": 80.0,
    "飲食": 60.0,
    "物販": 100.0,
}
DEFAULT_FLOOR_AREA_M2: Final[float] = 80.0

#: 在席の上限滞在[tick](回転率・expedient)。
DWELL_MAX_TICKS: Final[int] = 30
#: 待ち行列の離脱閾値[tick](expedient)。
WAIT_MAX_TICKS: Final[int] = 15

#: 「滞留気味」と見なす移動者の割合の下限(expedient)。
STILL_SHARE: Final[float] = 0.20
#: 「一方向に流れている」と見なす合成ベクトルの一貫性(expedient)。
COHERENT: Final[float] = 0.50
#: 8 方位に量子化できないとき(移動者ゼロ)の値。
FLOW_NONE: Final[int] = 8


def seats_for_categories(cats) -> np.ndarray:
    """POI カテゴリ列 → 席数(容量 c)。**全部 expedient**(16行表 行2)。"""
    out = np.empty(len(cats), dtype=np.int64)
    for i, c in enumerate(cats):
        name = str(c)
        area = FLOOR_AREA_M2_BY_CAT.get(name, DEFAULT_FLOOR_AREA_M2)
        per = SEAT_AREA_M2.get(name, DEFAULT_SEAT_AREA_M2)
        out[i] = max(1, int(area // per))
    return out


class CrowdProcess:
    """密度・流れ(人物①)と屋内占有・待ち行列(人物②)の集約。

    Attributes:
        flow: ``(n_cells,)`` uint8 の 3 値(レンダラ ``FLOW_WORDS`` と同じ並び)。
        flow_dir8: ``(n_cells,)`` uint8 の 8 方位(``FLOW_NONE``=移動者なし)。診断・将来用。
        occupancy: ``(n_poi,)`` の在席数。
        queue_len: ``(n_poi,)`` の待ち人数。
        seats: ``(n_poi,)`` の容量 c。
    """

    process_ids: Final[tuple[str, ...]] = ("crowd_field", "indoor_occupancy")
    ablation_id: Final[str] = "AB-OCCUPANCY-CAPACITY"

    def __init__(self, world: World, agents: AgentState, *, tick_seconds: int = 60) -> None:
        self.world = world
        self.agents = agents
        self.tick_seconds = int(tick_seconds)
        n = world.n_cells
        self.flow = np.zeros(n, dtype=np.uint8)
        self.flow_dir8 = np.full(n, FLOW_NONE, dtype=np.uint8)
        self.coherence = np.zeros(n, dtype=np.float64)
        self.seats = seats_for_categories(world.assets.poi_cat)
        self.occupancy = np.zeros(world.n_poi, dtype=np.int64)
        self.admitted_this_tick = np.zeros(world.n_poi, dtype=np.int64)
        self.queue_len = np.zeros(world.n_poi, dtype=np.int64)
        self.n_released = 0
        self.n_balked = 0
        self.peak_queue = 0
        self.peak_occupancy = 0

    # ------------------------------------------------------------------ resolve から見た口
    def can_admit(self, poi_ids) -> np.ndarray:
        """その POI にいま入れるか(容量 c の空き)。満席なら購入は待ち行列へ回る。

        **同じ呼びの中の複数行**は行順で席を詰める(群内順位を席数と比べる)。行順は
        Phase B が確定した intent の並び=決定論。席の割り当てを pk 昇順(§2.2)でなく
        行順にしたのは expedient(席は Phase B の資源名前空間に無い)。
        """
        p = np.asarray(poi_ids, dtype=np.int64)
        out = np.zeros(p.shape, dtype=bool)
        idx = np.flatnonzero((p >= 0) & (p < self.occupancy.size))
        if idx.size == 0:
            return out
        pi = p[idx]
        order = np.argsort(pi, kind="stable")
        ps = pi[order]
        starts = np.flatnonzero(np.concatenate(([True], ps[1:] != ps[:-1])))
        counts = np.diff(np.append(starts, ps.size))
        rank_sorted = np.arange(ps.size, dtype=np.int64) - np.repeat(starts, counts)
        rank = np.empty(ps.size, dtype=np.int64)
        rank[order] = rank_sorted
        used = self.occupancy[pi] + self.admitted_this_tick[pi]
        out[idx] = (used + rank) < self.seats[pi]
        return out

    def on_admit(self, poi_ids) -> None:
        """在席の登録(**この tick 内の重複受け入れを防ぐ**)。"""
        p = np.asarray(poi_ids, dtype=np.int64)
        if p.size:
            np.add.at(self.admitted_this_tick, p, 1)

    # ------------------------------------------------------------------ 1 tick
    def step(self, tick: int) -> None:
        r = self.agents.registry
        t = int(tick)
        self.admitted_this_tick[:] = 0

        # ---- 回転率: 滞在上限を超えた在席を解く(expedient) ----
        poi_ref = r.poi_ref.astype(np.int64)
        seated = poi_ref >= 0
        if seated.any():
            stale = np.flatnonzero(seated & (r.poi_since.astype(np.int64) + DWELL_MAX_TICKS <= t))
            if stale.size:
                R.release_indoor(self.agents, stale)
                self.n_released += int(stale.size)
                poi_ref = r.poi_ref.astype(np.int64)

        # ---- 離脱閾値: 待ちすぎた個体は並ぶのをやめる(``INTERRUPTED``) ----
        q = r.queue_poi.astype(np.int64)
        waiting = q >= 0
        if waiting.any():
            gone = np.flatnonzero(
                waiting & (r.queue_since.astype(np.int64) + WAIT_MAX_TICKS <= t)
            )
            if gone.size:
                R.balk_queue(self.agents, gone, t)
                self.n_balked += int(gone.size)
                q = r.queue_poi.astype(np.int64)

        # ---- 在席・待ち行列の集約(ベクトル 2 本) ----
        n_poi = self.world.n_poi
        live = poi_ref[poi_ref >= 0]
        self.occupancy = np.bincount(live, minlength=n_poi).astype(np.int64)[:n_poi]
        qq = q[q >= 0]
        self.queue_len = np.bincount(qq, minlength=n_poi).astype(np.int64)[:n_poi]
        self.peak_queue = max(self.peak_queue, int(self.queue_len.max()) if n_poi else 0)
        self.peak_occupancy = max(
            self.peak_occupancy, int(self.occupancy.max()) if n_poi else 0
        )

        # ---- 流れ(人物①「密度・流れ」)----
        self._update_flow()

    def _update_flow(self) -> None:
        r = self.agents.registry
        n = self.world.n_cells
        cell = r.cell.astype(np.int64)
        moving = (r.activity == int(Activity.MOVING)) & (r.target_node >= 0) & (cell >= 0)
        self.flow[:] = 0
        self.flow_dir8[:] = FLOW_NONE
        self.coherence[:] = 0.0
        density = np.asarray(self.world.cells.density, dtype=np.float64)
        if not moving.any():
            self.flow[:] = np.where(density > 0, 1, 0).astype(np.uint8)  # 全員静止=滞留気味
            return
        idx = np.flatnonzero(moving)
        c = cell[idx]
        dest = r.target_node[idx].astype(np.int64)
        vec = self.world.assets.node_xy[dest].astype(np.float64) - r.xy[idx].astype(np.float64)
        norm = np.hypot(vec[:, 0], vec[:, 1])
        good = norm > 1e-6
        ux = np.where(good, vec[:, 0] / np.maximum(norm, 1e-9), 0.0)
        uy = np.where(good, vec[:, 1] / np.maximum(norm, 1e-9), 0.0)
        n_move = np.bincount(c, minlength=n).astype(np.float64)[:n]
        sx = np.bincount(c, weights=ux, minlength=n)[:n]
        sy = np.bincount(c, weights=uy, minlength=n)[:n]
        res = np.hypot(sx, sy)
        coh = np.where(n_move > 0, res / np.maximum(n_move, 1.0), 0.0)
        self.coherence = coh
        share = np.where(density > 0, n_move / np.maximum(density, 1.0), 0.0)
        flow = np.zeros(n, dtype=np.uint8)
        flow[(density > 0) & (share < STILL_SHARE)] = 1  # 滞留気味
        flow[(share >= STILL_SHARE) & (coh >= COHERENT)] = 2  # 一方向に流れている
        self.flow = flow
        # 8 方位(北=0 から時計回り 45°刻み。描画には出さない=上記の食い違い)
        ang = np.degrees(np.arctan2(sy, sx))
        sector = np.rint(((90.0 - ang) % 360.0) / 45.0).astype(np.int64) % 8
        self.flow_dir8 = np.where(n_move > 0, sector, FLOW_NONE).astype(np.uint8)

    # ------------------------------------------------------------------ 観測材料
    def mean_wait_ticks(self) -> np.ndarray:
        """M/M/c の平均待ち時間の近似(**観測欄のみ**・行動は駆動しない・expedient)。

        到着率 λ を「並んでいる人数 / 待ち上限」、サービス率 μ を「1/滞在上限」とみなし、
        ``Wq ≈ Lq / λ``(Little の公式)を使う。λ=0 の店は 0。
        """
        lam = self.queue_len / float(WAIT_MAX_TICKS)
        return np.where(lam > 0, self.queue_len / np.maximum(lam, 1e-9), 0.0)

    def queue_rows(self, k: int = 3) -> tuple[tuple[int, str, int], ...]:
        """待ち行列の上位 k(``(POI, 表示名, 人数)``)。B4b へ差し込むための材料。

        Note:
            レンダラ側に B4b の差し込み口が無いので**配線していない**(モジュール docstring)。
        """
        if self.queue_len.size == 0:
            return ()
        top = np.argsort(-self.queue_len, kind="stable")[: max(0, int(k))]
        cats = self.world.assets.poi_cat
        return tuple(
            (int(j), f"{cats[int(j)]}{int(j):04d}", int(self.queue_len[int(j)]))
            for j in top
            if self.queue_len[int(j)] > 0
        )

    def counters(self) -> dict[str, float]:
        return {
            "released": float(self.n_released),
            "balked": float(self.n_balked),
            "queued_now": float(int(self.queue_len.sum())),
            "occupied_now": float(int(self.occupancy.sum())),
            "peak_queue": float(self.peak_queue),
            "peak_occupancy": float(self.peak_occupancy),
            "seats_total": float(int(self.seats.sum())),
            "cells_flowing": float(int(np.count_nonzero(self.flow == 2))),
            "cells_still": float(int(np.count_nonzero(self.flow == 1))),
        }

    def summary(self) -> str:
        rows = self.queue_rows(1)
        head = f"行列: {rows[0][1]}に{rows[0][2]}人" if rows else "行列なし"
        return (
            f"混雑場: 流れ 一方向 {int(np.count_nonzero(self.flow == 2))} / "
            f"滞留 {int(np.count_nonzero(self.flow == 1))} セル / "
            f"在席 {int(self.occupancy.sum()):,} (席数 {int(self.seats.sum()):,}) / "
            f"離脱 {self.n_balked:,} / {head}"
        )
