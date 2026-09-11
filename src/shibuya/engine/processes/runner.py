"""engine.processes.runner — 世界過程の実行器(台帳 → 実装の唯一の橋)。

正典
- 世界過程設計書 §2「門前条件の二重化(**台帳に対応行のない実体は作れない**)は3レコード型
  すべてに適用」→ 本実行器は ``world.processes.first_batch.build_registry()`` を受け取り、
  **憲法5 検査(D-R2-4)を起動時に走らせて落ちる**(fail fast)。
- 同 §3 実装原則3「世界状態への書き込み口は1本(resolve 経由)。**世界過程も例外にしない**」
  → 各過程は ``engine.resolve`` の口だけを呼ぶ(本ファイルは状態を触らない)。
- 同 §2 ``ActualLog``「追記専用・不変」+ D-R2-6「保持窓 N 日で退避」→ 実行器が 1 本持ち、
  過程はそこへ追記する。PlanSpec の遵守率は ``compliance()`` が返す。
- 運用設計書 §1.2 「データ資産…ライセンス台帳行と1対1」/ manifest の同定欄 →
  ``registry_hash`` を ``RunResult`` に載せる。
- 方法論「ablation はスケール前の完了条件」→ ``enabled``/``disabled`` に台帳の**過程 id** か
  **感度試験 id(AB-*)** を渡して過程単位で切れる。

逐次ループ宣言(P4)
- ``step``: **過程数**(18)ぶんのループ 1 本。個体数・セル数には比例しない。

**C4 後半で足した過程**(§7.2 初回実装の後半 + 前倒し 9 本)
    補充・納品・廃棄物収集・街路清掃(``goods_flow``)/ 宅配・バス・道路工事(``logistics``)/
    出動・報道・ホテル・インフラ・大規模イベント(``civic``)/ 顕著行為 + p_notice(``salient``)。
    ``salient`` は台帳行を持たない**結線器**(事象を出すのは出動・報道と「倒れる」の生成)で、
    ``PROCESS_ORDER`` の**最後**に置く(同じ tick に起きた事象を全部拾ってから判定するため)。
"""

from __future__ import annotations

import time
from typing import Any, Final, Iterable

import numpy as np

from shibuya.agents.state import AgentState
from shibuya.engine import resolve as R
from shibuya.engine.processes.civic import (
    HotelProcess,
    InfraLoadProcess,
    LargeEventProcess,
    PressProcess,
    PublicServiceDispatchProcess,
)
from shibuya.engine.processes.crowd import CrowdProcess
from shibuya.engine.processes.environment import EnvironmentProcess
from shibuya.engine.processes.goods_flow import (
    DeliveryInboundProcess,
    ShelfRestockProcess,
    StreetCleaningProcess,
    WasteCollectionProcess,
)
from shibuya.engine.processes.logistics import (
    BusTaxiProcess,
    LastMileProcess,
    RoadWorksProcess,
)
from shibuya.engine.processes.opening import OpeningProcess
from shibuya.engine.processes.rail import RailProcess
from shibuya.engine.processes.salient import ABLATION_IDS as PNOTICE_ABLATION_IDS
from shibuya.engine.processes.salient import SalientProcess
from shibuya.engine.processes.traffic import TrafficProcess
from shibuya.world.assets import ProcessAssets
from shibuya.world.processes.actual_log import ActualLog
from shibuya.world.processes.first_batch import build_registry
from shibuya.world.state import World

__all__ = ["PROCESS_ORDER", "WorldProcessRunner"]


def _p_notice_ablation(default: str | int, enabled: Iterable[str] | None) -> str | int:
    """``enabled`` に ``AB-PNOTICE-A<k>`` があればそれを採る(§3.1 の ablation A0-A4)。

    ``enabled`` は過程トグルと共用の集合なので、p_notice の ablation id は
    **過程の選抜には効かせない**(``_resolve_toggles`` は ``salient`` の
    ``ablation_id`` = ``AB-PNOTICE-A4`` としか照合しない)。
    """
    if not enabled:
        return default
    names = {str(x).upper() for x in enabled}
    for k, ab in enumerate(PNOTICE_ABLATION_IDS):
        if ab in names or f"A{k}" in names:
            return ab
    return default

#: 実行器が回す過程(名前 → クラス)。台帳の id は各クラスの ``process_ids`` が持つ。
PROCESS_ORDER: Final[tuple[str, ...]] = (
    "environment",
    "rail",
    "opening",
    "crowd",
    "traffic",
    # ---- C4 後半: 物の流れ(§7.2 初回実装) ----
    "delivery_inbound",
    "shelf",
    "waste",
    "street_cleaning",
    # ---- C4 後半: 前倒し(§7.2 第2陣分) ----
    "last_mile",
    "bus_taxi",
    "road_works",
    "hotel",
    "infra",
    "press",
    "large_event",
    "dispatch",
    # ---- 結線器(台帳行を持たない・最後に回す) ----
    "salient",
)


class WorldProcessRunner:
    """世界過程 第1陣(前半)の実行器。

    Args:
        registry: ``world.processes.registry.WorldRegistry``
            (``None`` なら ``first_batch.build_registry()``)。
        world / agents: 状態。
        assets: ``world.assets.ProcessAssets``(``None`` なら合成=全過程が休む)。
        master_seed: 実日の乱択・域外居住の抽選に使う seed。
        day_index: 曜日(0=月曜)。
        tick_seconds: 1 tick の秒数。
        schedule: mock 日課(鉄道の到着便割り当てに使う)。
        ledger: 金/物の台帳(運賃の脚に使う。``None`` 可)。
        enabled / disabled: 過程 id か感度試験 id(``AB-*``)の集合。
        retention_days: ``ActualLog`` の保持窓(D-R2-6)。

    Attributes:
        registry_hash: 台帳の blake3(manifest の同定欄へ)。
        constitution_ok: 憲法5 検査(D-R2-4)の結果。
        replay_date: 気象の再生実日(D-W15)。
        phase_seconds: 過程別の壁時計[秒]。
    """

    def __init__(
        self,
        registry=None,
        world: World | None = None,
        agents: AgentState | None = None,
        assets: ProcessAssets | None = None,
        clock: Any | None = None,
        seed: int | str = 1,
        ledger: Any | None = None,
        *,
        master_seed: int | str | None = None,
        day_index: int = 0,
        tick_seconds: int = 60,
        schedule: Any | None = None,
        enabled: Iterable[str] | None = None,
        disabled: Iterable[str] | None = None,
        retention_days: int = 7,
        prefer_shadow_days: bool = True,
        p_notice_ablation: str | int = "A4",
        p_notice_d50_scale: float = 1.0,
        salient_rate_per_10k: float | None = None,
        plan_executor: bool = False,
    ) -> None:
        if world is None or agents is None:
            raise ValueError("WorldProcessRunner は world と agents を要る")
        self.registry = registry if registry is not None else build_registry()
        self.world = world
        self.agents = agents
        self.assets = assets if assets is not None else ProcessAssets.synthetic()
        self.clock = clock
        self.master_seed = seed if master_seed is None else master_seed
        self.day_index = int(day_index)
        self.tick_seconds = int(tick_seconds)
        self.ledger = ledger
        #: **D-66 計画実行層**のラン(``engine.presence.PlanExecutor`` が在圏の出入りを持つ)。
        #: rail の乱数 12% と D-61 帰りの便を止め、起動時の域外配置も層に任せる。
        self.plan_executor = bool(plan_executor)
        #: 層の実体(``attach_presence`` で後から挿す。``None``=帰無腕)。
        self.presence: Any | None = None

        # ---- 門前条件: 憲法5(D-R2-4)を起動時に通す(通らなければ動かさない) ----
        report = self.registry.check_constitution5()
        self.constitution_report = report
        self.constitution_ok = bool(report.ok)
        if not self.constitution_ok:
            raise ValueError(
                "憲法5(D-R2-4)検査に落ちた台帳では世界過程を動かせない: "
                + " / ".join(str(v) for v in report.violations[:5])
            )
        self.registry_hash = self.registry.registry_hash()

        self.log = ActualLog(
            "actual_log",
            retention_days=int(retention_days),
            ticks_per_day=max(1, 86_400 // max(1, self.tick_seconds)),
        )

        self.environment = EnvironmentProcess(
            world, agents, self.assets,
            master_seed=self.master_seed, day_index=self.day_index, tick_seconds=self.tick_seconds,
            prefer_shadow_days=prefer_shadow_days,
        )
        self.rail = RailProcess(
            world, agents, self.assets,
            master_seed=self.master_seed, day_index=self.day_index,
            schedule=schedule, actual_log=self.log,
            plan_executor=self.plan_executor,
        )
        self.opening = OpeningProcess(
            world, agents, self.assets,
            day_index=self.day_index, tick_seconds=self.tick_seconds, actual_log=self.log,
        )
        self.crowd = CrowdProcess(world, agents, tick_seconds=self.tick_seconds)
        self.traffic = TrafficProcess(world, self.assets, tick_seconds=self.tick_seconds)

        # ---- C4 後半: 物の流れ(補充 → 納品 → 収集 → 街路清掃) ----
        self.shelf = ShelfRestockProcess(
            world, agents, ledger=ledger, staff_of_poi=self.opening.staff_of_poi,
            tick_seconds=self.tick_seconds, actual_log=self.log,
        )
        self.delivery_inbound = DeliveryInboundProcess(
            world, ledger=ledger, shelf=self.shelf, master_seed=self.master_seed,
            day_index=self.day_index, tick_seconds=self.tick_seconds, actual_log=self.log,
        )
        self.waste = WasteCollectionProcess(
            world, agents, ledger=ledger, tick_seconds=self.tick_seconds,
            actual_log=self.log, master_seed=self.master_seed,
        )
        self.street_cleaning = StreetCleaningProcess(
            world, agents, tick_seconds=self.tick_seconds
        )

        # ---- C4 後半: 前倒し 9 本 ----
        home = getattr(schedule, "home_cell", None)
        household = (
            None if home is None
            else np.bincount(
                np.asarray(home, dtype=np.int64)[
                    (np.asarray(home, dtype=np.int64) >= 0)
                    & (np.asarray(home, dtype=np.int64) < world.n_cells)
                ],
                minlength=world.n_cells,
            )
        )
        self.last_mile = LastMileProcess(
            world, household_per_cell=household, master_seed=self.master_seed,
            day_index=self.day_index, tick_seconds=self.tick_seconds, actual_log=self.log,
        )
        self.bus_taxi = BusTaxiProcess(
            world, self.assets, tick_seconds=self.tick_seconds, actual_log=self.log
        )
        self.road_works = RoadWorksProcess(
            world, self.assets, master_seed=self.master_seed, day_index=self.day_index,
            tick_seconds=self.tick_seconds, actual_log=self.log,
        )
        self.hotel = HotelProcess(
            world, agents, self.assets,
            external_home=(self.rail.external_line >= 0),
            tick_seconds=self.tick_seconds, actual_log=self.log,
        )
        self.infra = InfraLoadProcess(world, agents, tick_seconds=self.tick_seconds)
        self.press = PressProcess(
            world, tick_seconds=self.tick_seconds, actual_log=self.log
        )
        self.large_event = LargeEventProcess(
            world, agents, rail=self.rail, master_seed=self.master_seed,
            day_index=self.day_index, tick_seconds=self.tick_seconds, actual_log=self.log,
        )
        self.dispatch = PublicServiceDispatchProcess(
            world, master_seed=self.master_seed, day_index=self.day_index,
            tick_seconds=self.tick_seconds, actual_log=self.log,
        )
        self.salient = SalientProcess(
            world, agents, master_seed=self.master_seed, day_index=self.day_index,
            tick_seconds=self.tick_seconds, dispatch=self.dispatch, press=self.press,
            environment=self.environment,
            ablation=_p_notice_ablation(p_notice_ablation, enabled),
            rate_per_10k_per_day=salient_rate_per_10k,
            d50_scale=p_notice_d50_scale,
        )

        self._procs: dict[str, Any] = {
            "environment": self.environment,
            "rail": self.rail,
            "opening": self.opening,
            "crowd": self.crowd,
            "traffic": self.traffic,
            "delivery_inbound": self.delivery_inbound,
            "shelf": self.shelf,
            "waste": self.waste,
            "street_cleaning": self.street_cleaning,
            "last_mile": self.last_mile,
            "bus_taxi": self.bus_taxi,
            "road_works": self.road_works,
            "hotel": self.hotel,
            "infra": self.infra,
            "press": self.press,
            "large_event": self.large_event,
            "dispatch": self.dispatch,
            "salient": self.salient,
        }
        self.enabled = self._resolve_toggles(enabled, disabled)
        self.phase_seconds: dict[str, float] = {k: 0.0 for k in PROCESS_ORDER}
        self.n_steps = 0

        # 域外に住む個体をランの最初に外へ置く(U10 §1.1・書き込みは resolve の口)。
        # **計画実行層のラン**では母数も配置も層が決める(``PlanExecutor.initialize``)。
        if not self.plan_executor and self.is_enabled("rail") and self.rail.active:
            ext = self.rail.external_home_agents()
            if ext.size:
                R.place_at_external(agents, ext, self.rail.external_line[ext])

    # ------------------------------------------------------------------ 計画実行層(D-66)
    def attach_presence(self, presence: Any) -> None:
        """計画実行層を挿す(``engine.run`` が週次表を読んだ後に 1 回だけ呼ぶ)。

        層が持つ ``home_out``(域外居住)を**ホテル**へ渡し(母数 12% → 88.8%)、
        **大規模イベント**へ層そのものを渡す(引き込み候補と I4 の通知)。
        """
        self.presence = presence
        self.hotel.external_home = np.asarray(presence.home_out, dtype=bool)
        self.large_event.presence = presence

    # ------------------------------------------------------------------ トグル
    def _names_of(self, key: str) -> tuple[str, ...]:
        p = self._procs[key]
        names = (key,) + tuple(getattr(p, "process_ids", ())) + (
            (getattr(p, "ablation_id", ""),) if getattr(p, "ablation_id", "") else ()
        )
        if key == "salient":
            names = names + PNOTICE_ABLATION_IDS  # A0-A4 のどれでも「顕著行為を回す」意味
        return names

    def _resolve_toggles(
        self, enabled: Iterable[str] | None, disabled: Iterable[str] | None
    ) -> set[str]:
        want = set(PROCESS_ORDER)
        if enabled is not None:
            names = {str(x) for x in enabled}
            want = {k for k in PROCESS_ORDER if names & set(self._names_of(k))}
        if disabled:
            names = {str(x) for x in disabled}
            want -= {k for k in PROCESS_ORDER if names & set(self._names_of(k))}
        return want

    def is_enabled(self, key: str) -> bool:
        return key in self.enabled

    @property
    def disabled_ids(self) -> tuple[str, ...]:
        """止めた過程の台帳 id + 感度試験 id(ラン manifest の ``ablations`` 欄)。"""
        out: list[str] = []
        for key in PROCESS_ORDER:
            if key in self.enabled:
                continue
            p = self._procs[key]
            out += list(getattr(p, "process_ids", ()))
            ab = getattr(p, "ablation_id", "")
            if ab:
                out.append(ab)
        return tuple(sorted(set(out)))

    # ------------------------------------------------------------------ 1 tick
    def step(self, tick: int) -> None:
        """有効な過程を順に 1 tick 進める(過程数ぶんのループ 1 本)。"""
        for key in PROCESS_ORDER:  # 逐次ループ宣言: 過程数(5)ぶん
            if key not in self.enabled:
                continue
            t0 = time.perf_counter()
            self._procs[key].step(int(tick))
            self.phase_seconds[key] += time.perf_counter() - t0
        self.n_steps += 1

    def end_of_day(self, tick: int) -> int:
        """日末の締め: 最終 tick に発車する便を流し切り、``ActualLog`` を畳む(D-R2-6)。"""
        if self.is_enabled("rail") and self.rail.active:
            self.rail.step(int(tick) + 1)  # 発車は 1 tick 遅れで処理する(rail.step 参照)
        return int(self.log.evict_expired(int(tick)))

    # ------------------------------------------------------------------ 観測・検算
    @property
    def flow(self) -> np.ndarray:
        """B4「密度スカラー+流れ方向」の流れ側(3 値)。``renderer.prepare_tick(flow=…)`` へ。"""
        return self.crowd.flow

    @property
    def salient_events(self) -> dict[int, tuple[str, ...]]:
        """B4「目につく出来事」のセル別行(``renderer.prepare_tick(salient_events=…)`` へ)。"""
        if not self.is_enabled("salient"):
            return {}
        return self.salient.cell_lines

    @property
    def noticed_agents(self) -> np.ndarray:
        """この tick に顕著行為へ気づいた個体(起床条件 (i)・**呼はアービタを通る**)。"""
        if not self.is_enabled("salient"):
            return np.zeros(0, dtype=np.int64)
        return self.salient.noticed_agents

    def salient_wake_candidates(self, tick: int):
        """起床条件 (i)「顕著行為の到達」の候補 3 本組。"""
        if not self.is_enabled("salient"):
            return (
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.int8),
                np.empty(0, dtype=np.int64),
            )
        return self.salient.wake_candidates(int(tick))

    def queue_rows(self, k: int = 1):
        """B4b「行列」の材料(``renderer.prepare_tick(queues=…)`` へ)。"""
        if not self.is_enabled("crowd"):
            return ()
        return self.crowd.queue_rows(int(k))

    def waste_band_report(self):
        """検算②(W1 band)の材料。物の台帳が無ければ ``None``。"""
        if self.ledger is None or getattr(self.ledger, "goods", None) is None:
            return None
        return self.ledger.goods.waste_band(days=1)

    def projected_waste_tonnes_per_day(self) -> float:
        """その日の廃棄 sink[t/日](物の台帳 + 街路清掃の回収分)。"""
        if not self.is_enabled("waste"):
            return 0.0
        extra = self.street_cleaning.swept_g if self.is_enabled("street_cleaning") else 0.0
        return self.waste.projected_tonnes_per_day(extra_g=extra)

    @property
    def replay_date(self) -> str:
        return self.environment.replay_date

    def riders_conserved(self) -> bool:
        """乗客の保存則: bbox 内 + 乗車中 + 域外滞在 = 個体数。"""
        inb, riding, outside = self.rail.rider_census()
        return (inb + riding + outside) == self.agents.n

    def compliance(self, window_ticks: int | None = None):
        """PlanSpec の遵守率(``ActualLog`` の SCHEDULED 率・§2「遵守率の観測欄」)。"""
        ids = [pid for key in self.enabled for pid in getattr(self._procs[key], "process_ids", ())]
        return self.log.compliance_rate(sorted(set(ids)))

    def counters(self) -> dict[str, float]:
        """過程別の診断カウンタを 1 枚に畳む(``<過程>.<欄>``)。"""
        out: dict[str, float] = {}
        for key in PROCESS_ORDER:
            p = self._procs[key]
            for k, v in p.counters().items():
                out[f"{key}.{k}"] = float(v)
        out["actual_log.rows"] = float(len(self.log))
        out["actual_log.appended"] = float(self.log.n_appended)
        return out

    def summary(self) -> str:
        lines = [
            f"[世界過程] 台帳 {self.registry_hash[:16]}… 憲法5 "
            f"{'OK' if self.constitution_ok else 'NG'} / 有効 "
            f"{','.join(sorted(self.enabled))}",
        ]
        for key in PROCESS_ORDER:
            if key in self.enabled:
                lines.append("  " + self._procs[key].summary())
        rate = self.compliance()
        lines.append(
            f"  ActualLog {self.log.n_appended:,} 行 / 遵守率 "
            f"{rate.rate:.3f}(n={rate.n_total:,}・SCHEDULED {rate.n_scheduled:,})"
        )
        band = self.waste_band_report()
        if band is not None:
            lines.append(
                f"  廃棄 sink(検算②): {self.projected_waste_tonnes_per_day():.4f} t/日 "
                f"(band {band.low:.1f}-{band.high:.1f} t/日) "
                f"{'OK' if band.low <= self.projected_waste_tonnes_per_day() <= band.high else 'NG'}"
            )
        lines.append(
            "  過程別[s]: "
            + ", ".join(
                f"{k}={self.phase_seconds[k]:.3f}"
                for k in PROCESS_ORDER
                if self.phase_seconds[k] >= 0.001
            )
        )
        return "\n".join(lines)
