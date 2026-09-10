"""engine.processes.civic — 公共サービス出動・報道/公式発信・大規模イベント・ホテル・インフラ。

担当する台帳行(``world.processes.first_batch.PULLED_FORWARD_DECLARATIONS``)
- ``public_service_dispatch``(``AB-DISPATCH-DELAY``・reaches=**人物③**・contributes=W3)
  「§3 人物③『顕著な行為(倒れる・叫び・警察)』=出動そのものが到達チャネルを持つ」。
- ``press_official_release``(``AB-PRESS-REACH``・contributes=C1)。
- ``large_event``(``AB-EVENT-DELTA``・``executor=engine_rule``・conf 0.3・contributes=D1′/D4′)。
- ``hotel_room_inventory``(``AB-HOTEL-ROOMS``・``executor=engine_rule``・conf 0.4・contributes=W6)。
- ``infra_daily_load``(``AB-INFRA-INTENSITY``・``executor=none``・contributes=W5)。

**報道・公式発信のチャネル(親へ報告・黙って解決しない)**
    D-R2-5/§7.2 は公式発信を「B3 級の大事件」として扱いたいが、知覚契約書 §3 のチャネル仕様表に
    **B3 の行が1つも無い**(``first_batch`` の冒頭 PROPOSED 注記と同じ問題)。本モジュールは
    チャネルを発明せず、**人物③(顕著行為)と同じ経路**=セル共有の B4「目につく出来事」へ
    素性タグ ``〔素性: 放送・世界内テキスト・命令文除去済〕`` つきで載せる。
    注意ゲート段2(顕著行為 上位1-2 = ``channels.B4.salient`` の ``max_items=2``)がそのまま効く。

expedient(本モジュール分・全て「返済対象」)
- 出動の遅延 = **対数正規(中央値 8 分)**(親指示)。σ は 0.5(自前)。上限 60 分。
- 倒れる事象への出動率 100%(通報の規則ゲートは「同一セルに誰か居ること」だけ)。
- 発信時刻 07:00 / 12:00 / 18:00 の 3 本。到達範囲=**全セル**(§7.2「到達範囲の較正後に返済」)。
- ホテル: 客室数 = **1 POI あたり 120 室**(実データ空欄)。チェックイン 21:00・アウト 09:00。
- インフラ原単位: 電力 0.35 kWh/人/時・水 0.012 m³/人/時(**出典なし**・W5 の実数は空欄)。
- 大規模イベント: 18:00-21:00 に外界から ``EVENT_VISITOR_DELTA`` 人を会場セルへ入れる。
"""

from __future__ import annotations

from typing import Final

import numpy as np

from shibuya.agents.state import AgentKind, AgentState
from shibuya.core.rng import stream
from shibuya.engine import resolve as R
from shibuya.perception import attention as AT
from shibuya.world.assets import ProcessAssets
from shibuya.world.processes.records import DEVIATION_CODES, DeviationVocab
from shibuya.world.state import World

__all__ = [
    "DISPATCH_MEDIAN_MIN",
    "DISPATCH_SIGMA",
    "PRESS_MINUTES",
    "HOTEL_ROOMS_PER_POI",
    "HOTEL_CHECKIN_MINUTE",
    "HOTEL_CHECKOUT_MINUTE",
    "POWER_KWH_PER_PERSON_HOUR",
    "WATER_M3_PER_PERSON_HOUR",
    "EVENT_WINDOW",
    "EVENT_VISITOR_DELTA",
    "PublicServiceDispatchProcess",
    "PressProcess",
    "HotelProcess",
    "InfraLoadProcess",
    "LargeEventProcess",
]

_SCHEDULED: Final[int] = DEVIATION_CODES[DeviationVocab.SCHEDULED]
_REPLACEMENT: Final[int] = DEVIATION_CODES[DeviationVocab.REPLACEMENT]
_DELAY: Final[int] = DEVIATION_CODES[DeviationVocab.DELAY]
MINUTES_PER_DAY: Final[int] = 1_440

#: 出動の到着遅延[分]の中央値(親指示・対数正規)。
DISPATCH_MEDIAN_MIN: Final[float] = 8.0
#: 同 σ(expedient)。
DISPATCH_SIGMA: Final[float] = 0.5
DISPATCH_MAX_MIN: Final[int] = 60

#: 公式発信の時刻[分](expedient)。
PRESS_MINUTES: Final[tuple[int, ...]] = (7 * 60, 12 * 60, 18 * 60)
#: 公式発信の本文(命令文なし・世界内テキスト)。
PRESS_BODY: Final[str] = "鉄道各線は平常どおり運行しています"

#: ホテル 1 POI あたりの客室数(expedient・実データ空欄)。
HOTEL_ROOMS_PER_POI: Final[int] = 120
HOTEL_CHECKIN_MINUTE: Final[int] = 21 * 60
HOTEL_CHECKOUT_MINUTE: Final[int] = 9 * 60

#: インフラ原単位(expedient・出典なし)。
POWER_KWH_PER_PERSON_HOUR: Final[float] = 0.35
WATER_M3_PER_PERSON_HOUR: Final[float] = 0.012

#: 大規模イベントの窓[分]と来街増分(expedient)。
EVENT_WINDOW: Final[tuple[int, int]] = (18 * 60, 21 * 60)
EVENT_VISITOR_DELTA: Final[int] = 200


def _minute(tick: int, tick_seconds: int) -> int:
    return int(int(tick) * int(tick_seconds) // 60) % MINUTES_PER_DAY


class PublicServiceDispatchProcess:
    """公共サービス出動(救急・警察)。「倒れる」事象を受けて出動し、到着で解消する。

    Attributes:
        pending: 到着待ちの ``(到着 tick, セル, x, y)``。
        n_dispatched / n_arrived: 診断。
    """

    process_ids: Final[tuple[str, ...]] = ("public_service_dispatch",)
    ablation_id: Final[str] = "AB-DISPATCH-DELAY"

    def __init__(
        self,
        world: World,
        *,
        master_seed: int | str = 1,
        day_index: int = 0,
        tick_seconds: int = 60,
        actual_log=None,
    ) -> None:
        self.world = world
        self.tick_seconds = int(tick_seconds)
        self.log = actual_log
        self.rng = stream(master_seed, "world.public_service_dispatch", int(day_index))
        self.pending: list[tuple[int, int, float, float]] = []
        self.n_dispatched = 0
        self.n_arrived = 0
        self.delay_minutes_total = 0

    @property
    def active(self) -> bool:
        return True

    def request(self, tick: int, cell: int, xy: tuple[float, float]) -> int:
        """通報を受けて出動する。到着 tick を返す(規則ゲート=セルが実在すること)。"""
        if not (0 <= int(cell) < self.world.n_cells):
            return -1
        delay = float(
            np.clip(
                self.rng.lognormal(mean=np.log(DISPATCH_MEDIAN_MIN), sigma=DISPATCH_SIGMA),
                1.0, float(DISPATCH_MAX_MIN),
            )
        )
        minutes = int(round(delay))
        arrive = int(tick) + max(1, minutes * 60 // max(1, self.tick_seconds))
        self.pending.append((arrive, int(cell), float(xy[0]), float(xy[1])))
        self.n_dispatched += 1
        self.delay_minutes_total += minutes
        if self.log is not None:
            self.log.append_many(
                self.process_ids[0], np.array([int(cell)], dtype=np.int64),
                np.array([int(tick)], dtype=np.int64),
                np.array([_DELAY], dtype=np.int8),
                np.array([minutes], dtype=np.int16),
            )
        return arrive

    def arrivals(self, tick: int) -> list[tuple[int, float, float]]:
        """この tick に到着する隊(セル・座標)。到着した事案は解消する。"""
        if not self.pending:
            return []
        done = [row for row in self.pending if row[0] <= int(tick)]
        if not done:
            return []
        self.pending = [row for row in self.pending if row[0] > int(tick)]
        self.n_arrived += len(done)
        if self.log is not None:
            self.log.append_many(
                self.process_ids[0],
                np.array([r[1] for r in done], dtype=np.int64),
                np.full(len(done), int(tick), dtype=np.int64),
                np.full(len(done), _SCHEDULED, dtype=np.int8),
            )
        return [(r[1], r[2], r[3]) for r in done]

    def step(self, tick: int) -> None:
        """出動そのものは ``request``/``arrivals`` で駆動する(実行器が呼ぶ)。"""
        return None

    def counters(self) -> dict[str, float]:
        return {
            "dispatched": float(self.n_dispatched),
            "arrived": float(self.n_arrived),
            "pending": float(len(self.pending)),
            "mean_delay_min": float(
                self.delay_minutes_total / max(1, self.n_dispatched)
            ),
        }

    def summary(self) -> str:
        return (
            f"公共サービス出動: 出動 {self.n_dispatched:,} / 到着 {self.n_arrived:,} / "
            f"平均遅延 {self.delay_minutes_total / max(1, self.n_dispatched):.1f} 分 "
            f"(対数正規 中央値 {DISPATCH_MEDIAN_MIN:.0f} 分=expedient)"
        )


class PressProcess:
    """報道・公式発信(固定時刻の放送)。全セルへ届く 1 行を作る。"""

    process_ids: Final[tuple[str, ...]] = ("press_official_release",)
    ablation_id: Final[str] = "AB-PRESS-REACH"

    def __init__(self, world: World, *, tick_seconds: int = 60, actual_log=None) -> None:
        self.world = world
        self.tick_seconds = int(tick_seconds)
        self.log = actual_log
        self.n_releases = 0
        self.line = AT.feature_tag("broadcast") + PRESS_BODY
        self.strip = AT.strip_imperatives(PRESS_BODY)

    @property
    def active(self) -> bool:
        return self.world.n_cells > 0

    def due(self, tick: int) -> bool:
        return _minute(tick, self.tick_seconds) in PRESS_MINUTES

    def step(self, tick: int) -> None:
        if not (self.active and self.due(tick)):
            return
        self.n_releases += 1
        if self.log is not None:
            self.log.append_many(
                self.process_ids[0], np.array([0], dtype=np.int64),
                np.array([int(tick)], dtype=np.int64),
                np.array([_SCHEDULED], dtype=np.int8),
            )

    def counters(self) -> dict[str, float]:
        return {
            "releases": float(self.n_releases),
            "imperatives_removed": float(self.strip.n_removed),
        }

    def summary(self) -> str:
        return (
            f"報道・公式発信: {self.n_releases} 本 / 到達=全 {self.world.n_cells} セル"
            "(B3 のチャネル行が無いので B4 顕著行為へ載せる=親へ報告済み)"
        )


class HotelProcess:
    """ホテル客室在庫(来街者のチェックイン・アウト)。

    Attributes:
        rooms_total / rooms_occupied: ``(n_hotel,)``。
        bed_cell: ``(n_agents,)`` チェックイン中のセル(-1=無し)。
    """

    process_ids: Final[tuple[str, ...]] = ("hotel_room_inventory",)
    ablation_id: Final[str] = "AB-HOTEL-ROOMS"

    def __init__(
        self,
        world: World,
        agents: AgentState,
        passets: ProcessAssets,
        *,
        external_home: np.ndarray | None = None,
        tick_seconds: int = 60,
        actual_log=None,
        rooms_per_poi: int = HOTEL_ROOMS_PER_POI,
    ) -> None:
        self.world = world
        self.agents = agents
        self.tick_seconds = int(tick_seconds)
        self.log = actual_log
        pois = getattr(passets, "hotel_poi", None)
        self.hotel_poi = (
            np.zeros(0, dtype=np.int64) if pois is None
            else np.asarray(pois, dtype=np.int64)
        )
        self.hotel_cell = (
            np.asarray(world.pois.cell, dtype=np.int64)[self.hotel_poi]
            if self.hotel_poi.size else np.zeros(0, dtype=np.int64)
        )
        self.rooms_total = np.full(self.hotel_poi.size, int(rooms_per_poi), dtype=np.int64)
        self.rooms_occupied = np.zeros(self.hotel_poi.size, dtype=np.int64)
        # セル → そのセルの最初のホテル索引(同一セルに複数あれば先頭へ寄せる=expedient)
        self.hotel_of_cell = np.full(world.n_cells, -1, dtype=np.int64)
        for k in range(self.hotel_poi.size - 1, -1, -1):  # 逐次: ホテル数(89)ぶん・起動時1回
            c = int(self.hotel_cell[k])
            if 0 <= c < world.n_cells:
                self.hotel_of_cell[c] = k
        self.bed_cell = np.full(agents.n, -1, dtype=np.int64)
        self.external_home = (
            np.zeros(agents.n, dtype=bool) if external_home is None
            else np.asarray(external_home, dtype=bool)
        )
        self.n_checkin = 0
        self.n_no_bed = 0
        self.n_checkout = 0

    @property
    def active(self) -> bool:
        return self.hotel_poi.size > 0

    def has_bed(self, agent_ids, cells) -> np.ndarray:
        """``resolve._apply_sleep`` が呼ぶ: その個体はそのセルで寝てよいか。"""
        a = np.asarray(agent_ids, dtype=np.int64).ravel()
        c = np.asarray(cells, dtype=np.int64).ravel()
        if a.size == 0 or not self.active:
            return np.zeros(a.shape, dtype=bool)
        return (self.bed_cell[a] >= 0) & (self.bed_cell[a] == c)

    def step(self, tick: int) -> None:
        if not self.active:
            return
        minute = _minute(tick, self.tick_seconds)
        if minute == HOTEL_CHECKOUT_MINUTE:
            self.n_checkout += int(np.count_nonzero(self.bed_cell >= 0))
            self.bed_cell[:] = -1
            self.rooms_occupied[:] = 0
        if minute != HOTEL_CHECKIN_MINUTE:
            return
        r = self.agents.registry
        want = np.flatnonzero(
            (r.field("kind") == int(AgentKind.VISITOR))
            & self.external_home
            & (r.transit_state == 0)
            & (self.bed_cell < 0)
        )
        if want.size == 0:
            return
        cell = np.asarray(r.cell, dtype=np.int64)[want]
        hotel = np.where(
            (cell >= 0) & (cell < self.world.n_cells), self.hotel_of_cell[np.maximum(cell, 0)], -1
        )
        has = hotel >= 0
        if not has.any():
            return
        idx = want[has]
        h = hotel[has]
        # 同じホテルに来た順(agent_id 昇順)で部屋を割る=決定論
        order = np.argsort(h, kind="stable")
        hs = h[order]
        starts = np.flatnonzero(np.concatenate(([True], hs[1:] != hs[:-1])))
        counts = np.diff(np.append(starts, hs.size))
        rank_sorted = np.arange(hs.size, dtype=np.int64) - np.repeat(starts, counts)
        rank = np.empty(hs.size, dtype=np.int64)
        rank[order] = rank_sorted
        room = (self.rooms_occupied[h] + rank) < self.rooms_total[h]
        got = idx[room]
        if got.size:
            self.bed_cell[got] = np.asarray(self.agents.registry.cell, dtype=np.int64)[got]
            np.add.at(self.rooms_occupied, h[room], 1)
            self.n_checkin += int(got.size)
        self.n_no_bed += int(np.count_nonzero(~room))
        if self.log is not None and got.size:
            uniq = np.unique(h[room])
            self.log.append_many(
                self.process_ids[0], uniq,
                np.full(uniq.size, int(tick), dtype=np.int64),
                np.full(uniq.size, _REPLACEMENT, dtype=np.int8),
            )

    def counters(self) -> dict[str, float]:
        return {
            "hotels": float(self.hotel_poi.size),
            "rooms": float(int(self.rooms_total.sum())),
            "checkin": float(self.n_checkin),
            "checkout": float(self.n_checkout),
            "no_bed": float(self.n_no_bed),
            "occupancy": float(
                int(self.rooms_occupied.sum()) / max(1, int(self.rooms_total.sum()))
            ),
        }

    def summary(self) -> str:
        if not self.active:
            return "ホテル客室在庫: ホテル POI が無い(休む)"
        return (
            f"ホテル客室在庫: {self.hotel_poi.size} 軒 × {HOTEL_ROOMS_PER_POI} 室"
            f"(=expedient) / チェックイン {self.n_checkin:,} ・満室 {self.n_no_bed:,} / "
            f"稼働 {int(self.rooms_occupied.sum()) / max(1, int(self.rooms_total.sum())):.3f}"
        )


class InfraLoadProcess:
    """インフラ日負荷(電力・水)の集約。**報告のみ**(網は持たない)。"""

    process_ids: Final[tuple[str, ...]] = ("infra_daily_load",)
    ablation_id: Final[str] = "AB-INFRA-INTENSITY"

    def __init__(self, world: World, agents: AgentState, *, tick_seconds: int = 60) -> None:
        self.world = world
        self.agents = agents
        self.tick_seconds = int(tick_seconds)
        self.power_kwh = np.zeros(24, dtype=np.float64)
        self.water_m3 = np.zeros(24, dtype=np.float64)

    @property
    def active(self) -> bool:
        return True

    def step(self, tick: int) -> None:
        hour = int(int(tick) * self.tick_seconds // 3_600) % 24
        inside = float(int(np.count_nonzero(np.asarray(self.agents.registry.cell) >= 0)))
        frac = float(self.tick_seconds) / 3_600.0
        self.power_kwh[hour] += inside * POWER_KWH_PER_PERSON_HOUR * frac
        self.water_m3[hour] += inside * WATER_M3_PER_PERSON_HOUR * frac

    def counters(self) -> dict[str, float]:
        return {
            "power_kwh_day": float(self.power_kwh.sum()),
            "water_m3_day": float(self.water_m3.sum()),
            "peak_hour": float(int(np.argmax(self.power_kwh))),
        }

    def summary(self) -> str:
        return (
            f"インフラ日負荷: 電力 {self.power_kwh.sum():,.0f} kWh / 水 "
            f"{self.water_m3.sum():,.0f} m³ / ピーク {int(np.argmax(self.power_kwh))} 時"
            "(原単位=expedient・W5 の実数は空欄)"
        )


class LargeEventProcess:
    """大規模イベント(外界からの来街増分を窓の間だけ入れる)。

    ``executor=engine_rule``・conf 0.3(``first_batch``)。主催者・参加者はエージェント化しない。
    """

    process_ids: Final[tuple[str, ...]] = ("large_event",)
    ablation_id: Final[str] = "AB-EVENT-DELTA"

    def __init__(
        self,
        world: World,
        agents: AgentState,
        *,
        rail=None,
        master_seed: int | str = 1,
        day_index: int = 0,
        tick_seconds: int = 60,
        actual_log=None,
        visitor_delta: int = EVENT_VISITOR_DELTA,
    ) -> None:
        self.world = world
        self.agents = agents
        self.rail = rail
        self.tick_seconds = int(tick_seconds)
        self.log = actual_log
        self.visitor_delta = int(visitor_delta)
        g = stream(master_seed, "world.large_event", int(day_index))
        n = world.n_cells
        self.venue_cells = (
            np.sort(g.choice(n, size=min(3, n), replace=False)).astype(np.int64)
            if n else np.zeros(0, dtype=np.int64)
        )
        self.n_in = 0
        self.n_out = 0
        self._inside = np.zeros(0, dtype=np.int64)

    @property
    def active(self) -> bool:
        return self.venue_cells.size > 0

    def step(self, tick: int) -> None:
        if not self.active:
            return
        minute = _minute(tick, self.tick_seconds)
        lo, hi = EVENT_WINDOW
        if minute == lo:
            self._arrive(int(tick))
        elif minute == hi:
            self._leave(int(tick))

    def _arrive(self, tick: int) -> None:
        r = self.agents.registry
        outside = np.flatnonzero(np.asarray(r.transit_state) == 2)
        if outside.size == 0:
            return
        take = outside[: self.visitor_delta]
        cells = self.venue_cells[np.arange(take.size) % self.venue_cells.size]
        R.rail_arrive(self.agents, self.world, take, cells)
        # **D-61 追補**: 引き込んだ体が鉄道の「帰りの便」を待っていたら、その予約を外す
        # (外さないと、退場して再び域外に居るときに古い割当が発火して**別の理由で**戻る)。
        if self.rail is not None:
            self.rail.drop_from_return_queue(take)
        self._inside = take
        self.n_in += int(take.size)
        if self.log is not None:
            self.log.append_many(
                self.process_ids[0], self.venue_cells,
                np.full(self.venue_cells.size, int(tick), dtype=np.int64),
                np.full(self.venue_cells.size, _SCHEDULED, dtype=np.int8),
            )

    def _leave(self, tick: int) -> None:
        if self._inside.size == 0:
            return
        ref = np.asarray(self.agents.registry.transit_ref, dtype=np.int64)[self._inside]
        R.rail_depart(self.agents, self._inside, np.maximum(ref, 0))
        # **D-61 追補**: この過程は鉄道の発車ブロックを通らずに域外へ出すので、帰りの便を
        # 自分で頼む(渋谷に家がある体は、次の域内活動に最も近い便で戻る)。
        if self.rail is not None:
            self.rail.assign_return_trains(self._inside, int(tick))
        self.n_out += int(self._inside.size)
        self._inside = np.zeros(0, dtype=np.int64)
        if self.log is not None:
            self.log.append_many(
                self.process_ids[0], self.venue_cells,
                np.full(self.venue_cells.size, int(tick), dtype=np.int64),
                np.full(self.venue_cells.size, _SCHEDULED, dtype=np.int8),
            )

    def counters(self) -> dict[str, float]:
        return {
            "venues": float(self.venue_cells.size),
            "arrived": float(self.n_in),
            "left": float(self.n_out),
            "inside_now": float(self._inside.size),
        }

    def summary(self) -> str:
        if not self.active:
            return "大規模イベント: セルが無い(休む)"
        return (
            f"大規模イベント: 会場 {self.venue_cells.size} セル / 来街増分 "
            f"{self.n_in:,} 人(窓 {EVENT_WINDOW[0] // 60:02d}:00-"
            f"{EVENT_WINDOW[1] // 60:02d}:00・conf 0.3=expedient)"
        )
