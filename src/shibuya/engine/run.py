"""engine.run — 1 シミュ日の mock ラン(予算行 **W2**)と CLI。

正典
- 予算宣言表 **W2**: 「壁時計/シミュ日(Phase 2・**5千体・CPU・mock LLM**)**≤10分**。
  mock は呼び出しコストゼロ級=**エンジン性能の検収値**」。
- 運用設計書 §2.2/§2.4: tick の骨格 =
  ① 前 tick までに届いた LLM 応答を **apply_key 昇順**で適用(=Phase A の intent 源)
  ⓪ 知覚の tick 前計算(``Renderer.prepare_tick``・**B4 描画欄はここで 1 本作る**)
  ② 変化検出(P6)→ 起床候補(⓪ の欄をそのまま読む=描画と検出が同じ 1 本)
  ③ 繰り延べアービタ(§6)→ 呼ぶ個体
  ④ LLM 呼(応答は ``pending_apply`` へ・t_apply=起床+δ_perc+δ_think を分tickへ切り上げ)
  ⑤ Phase A(LLM 由来 intent + エンジン継続)→ ⑥ Phase B(資源裁定)→ ⑦ Phase C(resolve)
- 運用設計書 §1.4 T1/T2: 「同一 manifest×2 で**全 checkpoint ハッシュ一致**」。
- 運用設計書 §1.4 T4: 「n=5,000 と 5,001 で既存個体の乱数列が不変」(``agents.schedule``)。
- 世界過程設計書 §6 D-R2-6: 状態成長宣言の 24step→1日/30日 外挿ゲート。

**run_salt**(親の指定): ``blake3(master_seed の正規表現 ‖ 0x1f ‖ "engine")`` の先頭 16 バイト。
**RNG カウンタの class_rank**: ``class_rank + 1``(INSTITUTION −1 → 0)。

逐次ループ宣言(P4)
1. ``run_day``: **tick 数**ぶんのループ(1,440)。1 tick の中身は全て配列演算。
2. ``_call_llm``: **選抜された呼数**ぶんのループ(平均 35/tick・L4 の制御目標)。
   LLM クライアントは 1 呼=1 関数呼び出しの契約(``llm.LLMClient``)なので束ねられない。
   実艦隊では httpx の並行発射(C6)に置き換わる。

**C3 の結線(第3弾)**
- LLM 呼は ``engine.llm_bridge.LLMBridge`` 一本を通る(録画テープ・δ_think レーン・
  2行形パース・未定義行動5段が1か所に集まる)。``mode="replay"`` はテープ完全一致で回し、
  テープ外は**計数して待機へ落とす**(実LLMへは落とさない=運用設計書 §2.5)。
- 会話は ``engine.conversation.ConversationManager``(行動契約書 §3)。resolve が作った
  会話成立を招待として受け、話者に**会話ターン起床(不応期0)**を毎tick出す。終了はエンジン。

expedient(本モジュール分)
- δ_think は認知設計書 §1 のレーン表を分tickへ切り上げ(L1=**1 tick**=2.6秒の切り上げ)。
  既存定数 ``DELTA_THINK_TICKS=1`` と同値。①(応答適用)が④(LLM呼)より前にあるため
  ``t_apply=tick`` と ``tick+1`` は同じ tick で適用される(親指示「L1=0 tick」との差分を報告済み)。
- プロンプトは既定で**本物の ``perception.renderer.Renderer``**(B0-B6)。``renderer="stub"``
  で ``StubRenderer``(``[a<agent>|c<cell>|t5<tick//5>|w<class>]``)へ落とせる(安いテスト用)。
- 世界内日時は ``DEFAULT_START_DATETIME + day_index 日 + tick 分``(manifest の
  ``start_sim_datetime`` を run_day が受けていないため・expedient)。
- 顕著行為(B4 の「顕著行為の到達」)は C3 では**常に空**(世界過程が C4)。流れも 0。
- 会話の招待は「resolve が ``会話`` を成立させた対」を入口にする(契約書 §3 の順序
  「招待→応答判定」の応答判定を resolve の直後に置いた)。相手側の ``activity`` は
  resolve が変えないため、相手の離脱は ``cell`` 監視で検出する。
- 週の曜日は ``day_index``(既定 0=月曜)。週 7 日表は C4 の PlanSpec。
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Final

import blake3 as _blake3
import numpy as np

import dataclasses

from shibuya.agents.population import Population, load_population, sample_population
from shibuya.agents.schedule import synthesize
from shibuya.agents.state import (
    WAKE_CONDITION_CLASS,
    Activity,
    AgentState,
    WakeCondition,
)
from shibuya.core.growth import GrowthReport, check_growth
from shibuya.core.hashing import apply_key_array, blake3_hex
from shibuya.core.types import DEFAULT_TICK_SECONDS, MINUTES_PER_SIM_DAY
from shibuya.engine import commit as C
from shibuya.engine import growth_decl as GD
from shibuya.engine import resolve as R
from shibuya.engine.arbiter import Arbiter, WakeCandidates, call_budget_per_tick
from shibuya.engine.change_detect import ChangeDetector
from shibuya.engine.conversation import ConversationManager
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.processes.runner import WorldProcessRunner
from shibuya.engine.llm_bridge import (
    DEFAULT_LANE,
    LLMBridge,
    PerceptionRendererAdapter,
    StubRenderer,
    delta_think_ticks,
)
from shibuya.engine.scheduler import DIAG_COLUMNS
from shibuya.engine.tape import TapeWriter
from shibuya.llm.mock import MockLLM
from shibuya.perception.renderer import (
    DEFAULT_START_DATETIME,
    PerceptionAssets,
    Renderer as PerceptionRenderer,
)
from shibuya.world.assets import load_process_assets_or_synthetic
from shibuya.world.state import World

__all__ = [
    "DIAG_RUN_COLUMNS",
    "DIAG_DAY_ROWS",
    "DELTA_THINK_TICKS",
    "Checkpoint",
    "RunResult",
    "run_salt_for",
    "run_day",
    "main",
]

#: δ_think(分tickへ切り上げ後)。既定レーン L1=2.6 秒 → 1 tick(認知設計書 §1)。
DELTA_THINK_TICKS: Final[int] = delta_think_ticks(DEFAULT_LANE, DEFAULT_TICK_SECONDS)

#: 診断表の列(``DIAG_COLUMNS`` の 4 列 + 運用列)。
DIAG_RUN_COLUMNS: Final[tuple[str, ...]] = (
    "tick",
    *DIAG_COLUMNS,
    "merged",
    "candidates",
    "calls",
    "pending_wakes",
    "pending_apply",
    "intents",
    "conflicts",
    "unresolved",
    "moved",
    "arrived",
    "purchases",
    "conversations",
    "reflections",
    "undefined_actions",
    "parse_errors",
    "tape_misses",
    "conversations_opened",
)

#: 診断行「シミュ日あたり」の必須行(§9.1 C3 受け入れ「診断行5本」+ 運用列)。
DIAG_DAY_ROWS: Final[tuple[str, ...]] = (
    *DIAG_COLUMNS,  # 繰り延べ / 昇格 / 縮退 / 抑止
    "parse_error_rate",
    "undefined_action_count",
    "tape_miss_count",
    "conversation_sessions",
)


def run_salt_for(master_seed: int | str) -> bytes:
    """``blake3(master_seed ‖ 0x1f ‖ "engine")`` の先頭 16 バイト(親の指定)。"""
    text = f"i:{int(master_seed)}" if not isinstance(master_seed, str) else f"s:{master_seed}"
    return _blake3.blake3(f"{text}\x1fengine".encode("utf-8")).digest(length=16)


@dataclass(frozen=True)
class Checkpoint:
    """checkpoint 1 点の状態ハッシュ(T1/T2 の一致判定)。"""

    tick: int
    agents_hash: str
    world_hash: str
    #: W16 母集団の同定ハッシュ(母集団なしのランは ``""``)。T1/T2 の一致判定に混ぜる。
    population_hash: str = ""

    @property
    def combined(self) -> str:
        return blake3_hex(
            "\x1f".join(
                (self.agents_hash, self.world_hash, self.population_hash)
            ).encode("utf-8")
        )


@dataclass
class RunResult:
    """1 ランの結果。"""

    n_agents: int
    n_cells: int
    seed: int | str
    ticks: int
    world_source: str
    checkpoints: list[Checkpoint] = field(default_factory=list)
    diagnostics: np.ndarray = field(default_factory=lambda: np.zeros((0, len(DIAG_RUN_COLUMNS)), dtype=np.int64))
    phase_seconds: dict[str, float] = field(default_factory=dict)
    wall_seconds: float = 0.0
    llm_calls: int = 0
    arbiter_counters: dict[str, Any] = field(default_factory=dict)
    money_start: int = 0
    money_end: int = 0
    revenue_end: int = 0
    min_stock: int = 0
    growth_report: GrowthReport | None = None
    growth_measured: dict[str, int] = field(default_factory=dict)
    #: ``engine.llm_bridge.LLMBridge.counters()``(書式エラー率・テープ外率・未定義行動)。
    bridge_counters: dict[str, float] = field(default_factory=dict)
    #: ``engine.conversation.ConversationManager.counters()``(会話セッションの開閉)。
    conversation_counters: dict[str, int] = field(default_factory=dict)
    #: 知覚レンダラの診断(キャッシュ命中率・グループ別平均トークン・切り詰め数)。
    renderer_counters: dict[str, float] = field(default_factory=dict)
    #: 使ったレンダラの名前(``perception.Renderer`` / ``StubRenderer`` / 注入クラス名)。
    renderer_name: str = ""
    #: 録画テープの置き場(記録したときだけ)。
    tape_path: str = ""
    #: ``record`` / ``replay``。
    mode: str = "record"
    # ---- C4: 世界過程(第1陣) ----
    #: 世界側台帳の blake3(manifest の同定欄・``WorldRegistry.registry_hash``)。
    registry_hash: str = ""
    #: 憲法5(D-R2-4)のビルド時検査を通ったか。
    constitution_ok: bool = False
    #: 気象の再生実日(D-W15 実日ブートストラップ)。世界過程が無ければ空。
    replay_date: str = ""
    #: 過程別の壁時計[秒]。
    process_seconds: dict[str, float] = field(default_factory=dict)
    #: 過程別の診断カウンタ(``<過程>.<欄>``)。
    process_counters: dict[str, float] = field(default_factory=dict)
    #: 支払われた運賃の合計[円](世帯→外界の sink)。
    fares_paid: int = 0
    #: 乗車・降車・待ち行列の件数。
    n_boarded: int = 0
    n_alighted: int = 0
    n_queued: int = 0
    #: PlanSpec の遵守率(``ActualLog`` の SCHEDULED 率)。
    compliance_rate: float = float("nan")
    #: ``ActualLog`` の追記総件数。
    actual_log_rows: int = 0
    # ---- C4 後半 ----
    #: 日次センサスの 1 行(``economy.census.daily_census``。注入されたときだけ埋まる)。
    #: **締めた日の実数**(faucet/sink/廃棄は締める前の当日値)。
    census_row: dict[str, Any] = field(default_factory=dict)
    #: ``census_row`` が指す日(``LedgerBundle.end_of_day`` で畳んだ日)。-1=台帳なし。
    day_closed: int = -1
    #: 日次ゲートの合否(§2.4「残差>閾値・純資産≠実物資産はゲート失敗」)。**例外にしない**。
    census_pass: bool = False
    #: 顕著行為(人物③)の件数と、``p_notice`` で気づいた延べ人数。
    salient_events: int = 0
    noticed: int = 0
    #: 公共サービスの出動件数。
    dispatches: int = 0
    #: 補充・納品・宅配・バス到着・ホテル泊の件数(受入報告の数値欄)。
    restocks: int = 0
    deliveries: int = 0
    parcels: int = 0
    bus_arrivals: int = 0
    hotel_checkins: int = 0
    #: その日の廃棄 sink[t/日](物の台帳 + 街路清掃)と W1 band。
    waste_tonnes_per_day: float = 0.0
    waste_band: tuple[float, float] = (0.0, 0.0)

    # ---- 便利参照 ----
    def column(self, name: str) -> np.ndarray:
        return self.diagnostics[:, DIAG_RUN_COLUMNS.index(name)]

    @property
    def parse_error_rate(self) -> float:
        """書式エラー率(``format_ok`` が偽だった呼の割合)。MockLLM なら 0.0。"""
        calls = int(self.column("calls").sum()) if self.diagnostics.size else 0
        errs = int(self.column("parse_errors").sum()) if self.diagnostics.size else 0
        return (errs / calls) if calls else 0.0

    @property
    def tape_miss_count(self) -> int:
        return int(self.column("tape_misses").sum()) if self.diagnostics.size else 0

    @property
    def undefined_action_count(self) -> int:
        return int(self.column("undefined_actions").sum()) if self.diagnostics.size else 0

    @property
    def conversation_sessions(self) -> int:
        return int(self.column("conversations_opened").sum()) if self.diagnostics.size else 0

    def diagnostics_day(self) -> dict[str, float]:
        """シミュ日あたりの診断行(``DIAG_DAY_ROWS`` を必ず全て含む)。"""
        out: dict[str, float] = {
            col: float(self.column(col).sum()) if self.diagnostics.size else 0.0
            for col in DIAG_COLUMNS
        }
        out["parse_error_rate"] = self.parse_error_rate
        out["undefined_action_count"] = float(self.undefined_action_count)
        out["tape_miss_count"] = float(self.tape_miss_count)
        out["conversation_sessions"] = float(self.conversation_sessions)
        return out

    @property
    def final_hash(self) -> str:
        return self.checkpoints[-1].combined if self.checkpoints else ""

    @property
    def waste_band_ok(self) -> bool:
        lo, hi = self.waste_band
        return bool(hi > 0.0 and lo <= self.waste_tonnes_per_day <= hi)

    def run_manifest_fields(self) -> dict[str, Any]:
        """ラン manifest の同定欄(C6 が読む)。

        Returns:
            ``registry_hash``(世界側台帳)・``replay_date``(D-W15 の実日)・
            ``template_sha256``(知覚テンプレ v1 の凍結ハッシュ)・
            ``catalog_sha16``(世界カタログ v0.2 の凍結 SHA)・
            ``process_ids``(実際に回した過程 id の昇順)・``ablations``(切った過程/感度試験 id)。
        """
        from shibuya.perception import templates as _T

        runner = getattr(self, "runner", None)
        catalog_sha16 = ""
        process_ids: tuple[str, ...] = ()
        ablations: tuple[str, ...] = ()
        if runner is not None:
            catalog_sha16 = str(getattr(runner.registry.catalog, "sha16", ""))
            process_ids = tuple(
                sorted(
                    {
                        pid
                        for key in runner.enabled
                        for pid in getattr(runner._procs[key], "process_ids", ())
                    }
                )
            )
            ablations = tuple(sorted(runner.disabled_ids))
        return {
            "registry_hash": self.registry_hash,
            "replay_date": self.replay_date,
            "template_sha256": _T.template_sha256(),
            "catalog_sha16": catalog_sha16,
            "process_ids": process_ids,
            "ablations": ablations,
        }

    @property
    def conserved(self) -> bool:
        """保存則: Σ所持金 + Σ売上 + **Σ運賃(外界への sink)** が不変。

        運賃は境界・経済設計書 §2.2 の sink(世帯→外界・科目「持ち出し」)なので、
        bbox 内の現金合計からは正しく消える。C4 以前(列車なし)は ``fares_paid=0`` で
        C2 の等式そのまま。
        """
        return self.money_start == self.money_end + self.revenue_end + self.fares_paid

    @property
    def movement_ms_per_tick(self) -> float:
        """予算行 P2(移動+密度更新)の実測[ms/tick]。"""
        return self.phase_seconds.get("movement", 0.0) / max(1, self.ticks) * 1_000.0

    def summary(self) -> str:
        calls = self.column("calls").sum() if self.diagnostics.size else 0
        lines = [
            f"[run] n={self.n_agents} cells={self.n_cells} seed={self.seed} "
            f"ticks={self.ticks} world={self.world_source}",
            f"  壁時計 {self.wall_seconds:.2f}s (W2 上限 600s) / "
            f"移動+密度 {self.movement_ms_per_tick:.3f} ms/tick (P2 上限 5 ms)",
            f"  LLM呼 {int(calls):,} = {calls / max(1, self.n_agents):.2f} 呼/体/日 "
            f"(L4 制御目標 10)",
            f"  保存則 Σmoney {self.money_end:,} + Σrevenue {self.revenue_end:,} "
            f"+ Σ運賃 {self.fares_paid:,} "
            f"= {self.money_end + self.revenue_end + self.fares_paid:,} "
            f"(初期 {self.money_start:,}) "
            f"{'OK' if self.conserved else 'NG'} / 最小在庫 {self.min_stock}",
            f"  checkpoint {len(self.checkpoints)} 点 最終 {self.final_hash[:16]}…",
        ]
        if self.registry_hash:
            lines.append(
                f"  世界過程 台帳 {self.registry_hash[:16]}… 憲法5 "
                f"{'OK' if self.constitution_ok else 'NG'} / 再生日 "
                f"{self.replay_date or '(合成)'} / 乗車 {self.n_boarded:,} 降車 "
                f"{self.n_alighted:,} 待ち行列 {self.n_queued:,} 乗り残し "
                f"{int(self.process_counters.get('rail.left_behind', 0)):,}"
                f"({self.process_counters.get('rail.left_behind_rate', 0.0):.4f}) / ActualLog "
                f"{self.actual_log_rows:,} 行 遵守率 {self.compliance_rate:.3f}"
            )
            lines.append(
                f"  C4後半: 補充 {self.restocks:,} / 納品 {self.deliveries:,} / 宅配 "
                f"{self.parcels:,} / バス到着 {self.bus_arrivals:,} / ホテル泊 "
                f"{self.hotel_checkins:,} / 顕著行為 {self.salient_events:,}(気づき "
                f"{self.noticed:,}・出動 {self.dispatches:,}) / 廃棄 "
                f"{self.waste_tonnes_per_day:.3f} t/日 (band {self.waste_band[0]:.1f}-"
                f"{self.waste_band[1]:.1f}) {'OK' if self.waste_band_ok else 'NG'}"
            )
            if self.census_row:
                lines.append(
                    f"  日次センサス(§2.4・締めた day={self.day_closed}): 残差 "
                    f"{self.census_row.get('residual', 0):,} / 貨幣供給 "
                    f"{self.census_row.get('money_supply', 0):,} / faucet "
                    f"{self.census_row.get('faucet_total', 0):,} / sink "
                    f"{self.census_row.get('sink_total', 0):,} / 棚卸差異 "
                    f"{self.census_row.get('goods_residual_units', 0):,} / 廃棄 "
                    f"{self.census_row.get('waste_g', 0.0):,.0f}g / ゲート "
                    f"{'PASS' if self.census_pass else 'FAIL(診断の赤)'}"
                )
            lines.append(
                "  過程別[s]: "
                + ", ".join(f"{k}={v:.3f}" for k, v in sorted(self.process_seconds.items()))
            )
        if self.renderer_counters:
            c = self.renderer_counters
            lines.append(
                f"  レンダラ {self.renderer_name}: 描画 {int(c.get('render_calls', 0)):,} "
                f"命中率 {c.get('render_cache_hit_rate', 0.0):.3f} / "
                f"平均tok 共有静的 {c.get('tokens_shared_static_mean', 0.0):.1f}/750 "
                f"セル {c.get('tokens_cell_mean', 0.0):.1f}/250 "
                f"個体 {c.get('tokens_individual_mean', 0.0):.1f}/300 "
                f"(合計 {c.get('prompt_tokens_mean', 0.0):.1f}) "
                f"切り詰め {int(c.get('render_truncations', 0)):,}"
            )
        for col in DIAG_COLUMNS:
            lines.append(f"  診断 {col}: {int(self.column(col).sum()):,}")
        lines.append(
            f"  診断 parse_error_rate: {self.parse_error_rate:.4f} / "
            f"undefined_action_count: {self.undefined_action_count:,} / "
            f"tape_miss_count: {self.tape_miss_count:,} / "
            f"conversation_sessions: {self.conversation_sessions:,}"
        )
        if self.growth_report is not None:
            lines.append("  " + self.growth_report.as_text().replace("\n", "\n  "))
        return "\n".join(lines)


def _resolve_population(
    population: "Population | bool | None",
    world_dir: str | Path | None,
    n_agents: int,
    seed: int | str,
    n_cells: int,
) -> "Population | None":
    """``population`` 引数 → 実体(``None``=資産が無い/切っている)。

    ``False`` は「母集団を使わない」の明示。``None``(既定)は ``world_dir`` に W16 の
    出力があれば読む。既に ``Population`` なら体数だけ合わせる(二層抽出)。
    """
    if population is False:
        return None
    if isinstance(population, Population):
        pop = population
        _check_population_fits(pop, n_cells)
    else:
        if world_dir is None:
            return None
        pop = load_population(world_dir, n=None, seed=seed)
        if pop is None:
            return None
        if not _population_fits(pop, n_cells):
            # ``world_dir`` は知覚資産の置き場として渡されているが、世界そのものは
            # 合成小世界(セル数が違う)。**自動読み込みは黙って見送る**
            # (明示的に population= を渡したときだけ食い違いを例外にする)。
            return None
    if pop.n > n_agents:
        pop = sample_population(pop, n_agents, seed)
    return pop


def _population_fits(pop: "Population", n_cells: int) -> bool:
    """母集団のセル索引が世界のセル数に収まるか。"""
    for arr in (pop.home_cell, pop.work_cell, pop.school_cell):
        if arr.size and int(arr.max()) >= int(n_cells):
            return False
    return True


def _check_population_fits(pop: "Population", n_cells: int) -> None:
    if not _population_fits(pop, n_cells):
        raise ValueError(
            f"母集団のセル索引が世界のセル数({n_cells})を超える。世界資産と母集団の版が違う"
        )


def _schedule_with_population(schedule, pop: "Population", n_cells: int):
    """mock 日課の拠点・種別を **W16 母集団**で置き換える(時刻帯は W17 まで mock のまま)。

    体数が母集団より多いときは、足りない分は mock の合成個体のまま残す(縮小ランの保険)。
    ``home_cell`` を持たない体(域外常住)は ``Population.start_cell`` の規約で置く
    (勤務→通学→mock の自宅セル)=W17 が入るまでの繋ぎ・expedient。
    """
    n = int(schedule.n_agents)
    m = min(n, pop.n)
    home = np.asarray(schedule.home_cell).copy()
    work = np.asarray(schedule.work_cell).copy()
    kind = np.asarray(schedule.kind).copy()
    age = np.zeros(n, dtype=np.uint8)
    sex = np.full(n, -1, dtype=np.int8)
    direction = np.full(n, -1, dtype=np.int32)
    start = pop.start_cell(fallback=-1)[:m]
    home[:m] = np.where(start >= 0, start, home[:m])
    pw = pop.work_cell[:m]
    work[:m] = np.where(pw >= 0, pw, work[:m])
    kind[:m] = pop.kind[:m]
    age[:m] = pop.age[:m]
    sex[:m] = pop.sex[:m]
    direction[:m] = pop.direction_node[:m]
    return dataclasses.replace(
        schedule,
        home_cell=np.clip(home, 0, n_cells - 1).astype(np.int32),
        work_cell=np.clip(work, 0, n_cells - 1).astype(np.int32),
        kind=kind,
        age=age,
        sex=sex,
        direction_node=direction,
        population_hash=pop.population_hash(),
    )


def run_day(
    n_agents: int = 5_000,
    seed: int | str = 1,
    world: World | None = None,
    *,
    tick_seconds: int = DEFAULT_TICK_SECONDS,
    ticks: int = MINUTES_PER_SIM_DAY,
    llm: Any | None = None,
    checkpoint_every: int = 360,
    day_index: int = 0,
    budget: float | None = None,
    n_cells: int = 139,
    mode: str = "record",
    tape_path: str | Path | None = None,
    replay: Any | None = None,
    renderer: Any | None = None,
    world_dir: str | Path | None = None,
    conversations: bool = True,
    lane: str = DEFAULT_LANE,
    ledger: "LedgerBundle | None" = None,
    processes: bool = True,
    processes_enabled: "list[str] | tuple[str, ...] | None" = None,
    processes_disabled: "list[str] | tuple[str, ...] | None" = None,
    p_notice_ablation: str | int = "A4",
    salient_rate_per_10k: float | None = None,
    population: "Population | bool | None" = None,
) -> RunResult:
    """1 シミュ日(既定 1,440 tick)の mock ランを回す。

    Args:
        n_agents: 個体数。
        seed: manifest の ``master_seed``。
        world: 世界(None なら ``World.synthetic(n_cells, seed)``)。
        tick_seconds: 1 tick の秒数。
        ticks: tick 数。
        llm: ``LLMClient``(None なら ``MockLLM(seed)``)。
        checkpoint_every: checkpoint 間隔[tick]。
        day_index: 曜日(0=月曜)。
        budget: 1 tick の呼数上限(None なら L4 按分)。
        n_cells: 合成世界を作るときのセル数。
        mode: ``"record"``(``llm`` を呼ぶ)/ ``"replay"``(テープ完全一致・テープ外は計数)。
        tape_path: 録画テープの出力先(None なら記録しない)。
        replay: ``mode="replay"`` のときのテープ(``Replay`` かパス)。
        renderer: プロンプト生成。**None なら本物の ``perception.renderer.Renderer``**
            (C3 結線)。``"stub"`` で ``StubRenderer``(安い決定論テスト用)。
        world_dir: 世界資産ディレクトリ(``PerceptionAssets.load`` の入口。None または
            資産が無ければ ``PerceptionAssets.synthetic`` へ落ちる)。
        conversations: 会話プロトコル(行動契約書 §3)を回すか。
        lane: δ_think のレーン(認知設計書 §1)。
        ledger: 金/物の台帳(``engine.ledger_api.LedgerBundle``・economy が実装を注入する)。
            ``None`` なら C2 と同じ直接更新の経路。世帯の現金は**個体 SoA の ``money``
            そのもの**を採用するので、run は ``AgentState`` を作った直後に
            ``attach_household_cash`` を呼ぶ(台帳の世帯数は ``n_agents`` と一致が必要)。
        processes: 世界過程(C4 第1陣)を回すか(既定 True)。資産が無い合成世界では
            混雑場だけが動き、他の過程は「休む」。
        processes_enabled / processes_disabled: 過程 id か感度試験 id(``AB-*``)で
            過程単位に切る(ablation)。
        p_notice_ablation: 顕著行為の到達 ``p_notice`` の ablation(知覚契約書 §3.1 の
            ``A0``-``A4``。既定 ``A4``=完成形)。``processes_enabled`` に
            ``AB-PNOTICE-A2`` のように書いても効く。
        population: W16 母集団(``agents.population.Population``)。``None``(既定)は
            **``world_dir`` に ``w16_population.parquet`` があれば自動で読む**
            (``n_agents`` 体へ二層抽出)。``False`` で明示的に切る(合成個体のまま)。
            資産が無ければ静かに合成個体へ落ちる。
        salient_rate_per_10k: 「倒れる」の発生率[件/10,000体/日](``None`` で既定
            ``salient.COLLAPSE_PER_10K_PER_DAY``=3.0)。5,000 体・1 日では期待値 1.5 件なので
            **引かない日がある**(P(0)=22%)。感度試験・結線テストで上げるための口。

    Returns:
        ``RunResult``。
    """
    t_start = time.perf_counter()
    world = world if world is not None else World.synthetic(n_cells=n_cells, seed=seed)
    llm = llm if llm is not None else MockLLM(master_seed=seed)
    salt = run_salt_for(seed)
    tape_writer = TapeWriter(Path(tape_path)) if tape_path is not None else None
    conv = ConversationManager(seed) if conversations else None
    agents = AgentState(n_agents)
    if ledger is not None and ledger.money is not None:
        # 世帯の現金行 = 個体 SoA の money(写しを作らない・台帳の書き込み窓は resolve が持つ)
        ledger.money.attach_household_cash(agents.registry.money)
    schedule = synthesize(n_agents, seed, world.n_cells)
    pop = _resolve_population(population, world_dir, n_agents, seed, world.n_cells)
    if pop is not None:
        schedule = _schedule_with_population(schedule, pop, world.n_cells)
    R.initialize(agents, world, schedule, day_index=day_index, ledger=ledger)
    agents.freeze()
    world.freeze()

    # ---- ⓪a 世界過程(C4 第1陣・世界過程設計書 §3 実装原則3=書き込みは resolve 経由) ----
    runner: WorldProcessRunner | None = None
    if processes:
        runner = WorldProcessRunner(
            world=world,
            agents=agents,
            assets=load_process_assets_or_synthetic(world_dir, world.assets),
            seed=seed,
            day_index=day_index,
            tick_seconds=tick_seconds,
            schedule=schedule,
            ledger=ledger,
            enabled=processes_enabled,
            disabled=processes_disabled,
            p_notice_ablation=p_notice_ablation,
            salient_rate_per_10k=salient_rate_per_10k,
        )

    # ---- 知覚レンダラ(C3 結線・B0-B6 の本物) ----
    perception: PerceptionRendererAdapter | None = None
    if renderer is None:
        assets = PerceptionAssets.load_or_synthetic(world_dir, world)
        # 世界内日時 = 気象の再生実日(D-W15)。世界過程が無ければ既定の開始日 + day_index。
        start = DEFAULT_START_DATETIME + timedelta(days=int(day_index))
        if runner is not None and runner.replay_date:
            start = datetime.fromisoformat(runner.replay_date)
        perception = PerceptionRendererAdapter(
            PerceptionRenderer(
                world, agents, assets,
                clock_fn=lambda t: start + timedelta(minutes=int(t)),
                seed=seed,
            )
        )
        renderer_obj: Any = perception
        walkable = assets.walkable_area_m2
    elif isinstance(renderer, str):
        if renderer != "stub":
            raise ValueError("renderer は None / 'stub' / Renderer 実装")
        renderer_obj = StubRenderer()
        walkable = None
    else:
        renderer_obj = renderer
        # 注入されたものが本物のアダプタなら、前計算(⓪)と B4 欄の受け渡しも同じ道を通す
        perception = renderer if isinstance(renderer, PerceptionRendererAdapter) else None
        walkable = getattr(getattr(renderer, "assets", None), "walkable_area_m2", None)

    bridge = LLMBridge(
        llm,
        renderer=renderer_obj,
        tape=tape_writer,
        mode=mode,
        replay=replay,
        lane=lane,
        tick_seconds=tick_seconds,
        params={"max_tokens": 64, "temperature": 0.0},
    )

    detector = ChangeDetector(n_agents, world.n_cells, walkable_area_m2=walkable)
    arbiter = Arbiter(
        n_agents, salt, budget if budget is not None else call_budget_per_tick(n_agents)
    )
    space = C.ResourceSpace(world.n_poi, n_agents, world.n_cells)

    # 計画境界(mock 日課)を tick でスライスできる形に平坦化
    b_agent, b_slot, b_tick = schedule.events_of_day(day_index)
    b_start = np.searchsorted(b_tick, np.arange(ticks + 1), side="left")
    boundary_condition = np.array(
        [
            int(WakeCondition.PLAN_GENERAL),
            int(WakeCondition.PLAN_TRANSIT),
            int(WakeCondition.PLAN_GENERAL),
            int(WakeCondition.PLAN_TRANSIT),
            int(WakeCondition.PLAN_SLEEPING),
        ],
        dtype=np.int8,
    )

    result = RunResult(
        n_agents=n_agents,
        n_cells=world.n_cells,
        seed=seed,
        ticks=ticks,
        world_source=world.assets.source,
        tape_path=str(tape_path) if tape_path is not None else "",
        mode=mode,
    )
    result.money_start = int(agents.registry.money.astype(np.int64).sum())
    phase = {k: 0.0 for k in ("detect", "arbiter", "llm", "phase_a", "phase_b", "phase_c",
                              "movement", "checkpoint")}
    diag_rows: list[tuple[int, ...]] = []
    # (t_apply, class, agent, condition, text, action_code)
    pending: list[tuple[int, int, int, int, str, int]] = []
    prev_tape_misses = 0
    prev_sessions = 0
    peak_pending = 0
    peak_intents = 0
    peak_backlog = 0
    n_undefined_total = 0

    # 逐次ループ宣言1: tick 数ぶん
    for tick in range(ticks):
        R.advance_body(agents, tick)

        # ---- ⓪a 世界過程(昼夜・天候・鉄道・営業時間・混雑場・断面交通) ----
        # 流れ(B4 の「流れ方向」欄)を作るのが混雑場なので、**⓪ の前**に置く。
        # 親指示は「⓪ の直後」だったが、それだと同じ tick の流れが描画に載らない(報告済み)。
        if runner is not None:
            runner.step(tick)

        # ---- ⓪ 知覚の tick 前計算(セル配列+B4 描画欄・**1 tick 1 回**) ----
        # 顕著行為(salient_events)は人物③(第2陣)が入るまで空。騒音段は
        # ``world.noise_stage_for_tick``(W10 静的昼夜場 or 動的上書き)を**1 本**渡し、
        # 描画と変化検出が同じ値を見るようにする。
        field_rows = None
        if perception is not None:
            perception.prepare_tick(
                tick,
                salient_events=None if runner is None else runner.salient_events,
                flow=None if runner is None else runner.flow,
                noise_stage=world.noise_stage_for_tick(tick, tick_seconds),
                queues=None if runner is None else runner.queue_rows(3),
            )
            field_rows = perception.b4_field_rows

        # ---- ① 前 tick までに届いた応答を apply_key 昇順で適用(§2.4) ----
        t0 = time.perf_counter()
        llm_intents = C.IntentBatch.empty()
        n_undefined = 0
        if pending:
            due = [p for p in pending if p[0] <= tick]
            pending = [p for p in pending if p[0] > tick]
            if due:
                t_apply = np.fromiter((p[0] for p in due), dtype=np.int64, count=len(due))
                ev_class = np.fromiter((p[1] for p in due), dtype=np.int64, count=len(due))
                ag = np.fromiter((p[2] for p in due), dtype=np.int64, count=len(due))
                cond = np.fromiter((p[3] for p in due), dtype=np.int64, count=len(due))
                ak = apply_key_array(salt, t_apply, ag)
                order = np.lexsort((ag, ak, ev_class, t_apply))
                # 行動コードは④(呼の時点)で正典パーサが決めている(二重パースしない)
                codes = np.fromiter(
                    (due[int(i)][5] for i in order),
                    dtype=np.int64,
                    count=order.size,
                )
                n_undefined = int(np.count_nonzero(codes == C.UNDEFINED_ACTION))
                n_undefined_total += n_undefined
                llm_intents = C.intents_from_responses(
                    agents, world, space, tick, ag[order], cond[order], codes,
                    home_cell=schedule.home_cell, work_cell=schedule.work_cell,
                )
        phase["phase_a"] += time.perf_counter() - t0

        # ---- ② 変化検出(P6) ----
        t0 = time.perf_counter()
        det = detector.detect(world, agents, tick, field_rows=field_rows)
        R.apply_detection(agents, world, det)
        d_agent, d_cond, d_class = det.candidates()
        phase["detect"] += time.perf_counter() - t0

        # ---- 計画境界の起床候補 ----
        lo, hi = int(b_start[tick]), int(b_start[tick + 1])
        if hi > lo:
            p_agent = b_agent[lo:hi]
            p_cond = boundary_condition[b_slot[lo:hi]]
            p_class = np.fromiter(
                (int(WAKE_CONDITION_CLASS[int(c)]) for c in p_cond),
                dtype=np.int64,
                count=p_cond.size,
            )
        else:
            p_agent = np.empty(0, dtype=np.int64)
            p_cond = np.empty(0, dtype=np.int8)
            p_class = np.empty(0, dtype=np.int64)

        # ---- 会話ターン起床(行動契約書 §3・不応期0)----
        if conv is not None:
            c_agent, c_cond, c_class = conv.wake_candidates(tick)
        else:
            c_agent = np.empty(0, dtype=np.int64)
            c_cond = np.empty(0, dtype=np.int8)
            c_class = np.empty(0, dtype=np.int64)

        # ---- 顕著行為の到達(起床条件 (i)・知覚契約書 §6)----
        # **アービタを通す**=顕著行為由来の呼も L4 の予算の中に入る(呼の抜け道を作らない)。
        if runner is not None:
            s_agent, s_cond, s_class = runner.salient_wake_candidates(tick)
        else:
            s_agent = np.empty(0, dtype=np.int64)
            s_cond = np.empty(0, dtype=np.int8)
            s_class = np.empty(0, dtype=np.int64)

        cands = WakeCandidates(
            np.concatenate([p_agent, d_agent, c_agent, s_agent]),
            np.concatenate([p_cond, d_cond.astype(np.int8), c_cond, s_cond]),
            np.concatenate([p_class, d_class, c_class, s_class]),
            np.full(
                p_agent.size + d_agent.size + c_agent.size + s_agent.size,
                tick, dtype=np.int64,
            ),
        )

        # ---- ③ 繰り延べアービタ(§6) ----
        t0 = time.perf_counter()
        decision = arbiter.step(tick, cands, agents.registry.refractory_until)
        phase["arbiter"] += time.perf_counter() - t0

        # ---- ④ LLM 呼(応答は pending_apply へ) ----
        t0 = time.perf_counter()
        sel = decision.selected
        n_parse_errors = 0
        if len(sel):
            R.set_refractory(agents, sel.agent_id, sel.condition, tick)
            cell = agents.registry.cell
            act = agents.registry.activity
            hun = agents.registry.hunger
            last_act = agents.registry.last_action
            # 逐次ループ宣言2: 選抜された呼数ぶん(平均 35/tick)
            for i in range(len(sel)):
                a = int(sel.agent_id[i])
                cls = int(decision.selected_eff_class[i])
                cond = int(sel.condition[i])
                res = bridge.call(
                    a, tick, cls, cond,
                    cell=int(cell[a]), activity=int(act[a]), hunger=int(hun[a]),
                    last_action=int(last_act[a]),
                )
                pending.append((res.t_apply, cls, a, cond, res.text, res.action_code))
                if not res.format_ok:
                    n_parse_errors += 1
                if conv is not None and cond == int(WakeCondition.CONVERSATION_TURN):
                    # 会話ターンの応答は**発話ブロック**(1呼=1ブロック・§3)
                    conv.utterance(a, tick, action=res.parse.action, comment=res.parse.comment)
            result.llm_calls += len(sel)
        peak_pending = max(peak_pending, len(pending))
        peak_backlog = max(peak_backlog, arbiter.n_pending())
        phase["llm"] += time.perf_counter() - t0

        # ---- ⑤ Phase A(エンジン継続との合流) ----
        t0 = time.perf_counter()
        intents = C.IntentBatch.concat(
            [llm_intents, C.engine_continuations(agents, space, tick)]
        ).one_per_agent()
        peak_intents = max(peak_intents, len(intents))
        phase["phase_a"] += time.perf_counter() - t0

        # ---- ⑥ Phase B(資源裁定) ----
        t0 = time.perf_counter()
        plan = C.arbitrate_resources(
            intents, tick, salt, space, world.pois.stock, world.pois.capacity
        )
        phase["phase_b"] += time.perf_counter() - t0

        # ---- ⑦ Phase C(resolve=唯一の書き手) ----
        t0 = time.perf_counter()
        outcome = R.apply(
            plan.confirmed,
            plan.losers,
            agents,
            world,
            tick,
            schedule=schedule,
            ledger=ledger,
            rail=None if runner is None or not runner.is_enabled("rail") else runner.rail,
            crowd=None if runner is None or not runner.is_enabled("crowd") else runner.crowd,
            hotel=None if runner is None or not runner.is_enabled("hotel") else runner.hotel,
        )
        phase["phase_c"] += time.perf_counter() - t0
        phase["movement"] += outcome.movement_seconds
        result.fares_paid += outcome.fare_paid
        result.n_boarded += outcome.n_boarded
        result.n_alighted += outcome.n_alighted
        result.n_queued += outcome.n_queued

        # ---- 会話セッション(行動契約書 §3): resolve の会話成立を招待として受ける ----
        if conv is not None:
            talk = np.flatnonzero(plan.confirmed.action_code == C.ACT_TALK)
            if talk.size:
                inviters = plan.confirmed.agent_id[talk].astype(np.int64)
                invitees = plan.confirmed.target_id[talk].astype(np.int64)
                cell_now = agents.registry.cell
                act_now = agents.registry.activity
                reverted: list[int] = []
                # 逐次ループ宣言3: 会話成立数ぶん(≤ 1 tick の呼数)。個体数に比例しない。
                for j in range(inviters.size):
                    inviter = int(inviters[j])
                    invitee = int(invitees[j])
                    if invitee < 0 or invitee >= agents.n:
                        reverted.append(inviter)
                        continue
                    if int(act_now[inviter]) != int(Activity.CONVERSING):
                        continue  # resolve が失敗させた(相手が会話中/去った)
                    # 「相手idle」は resolve が §2.1 の前提として**適用時に**検査済み
                    # (CONVERSING に変えたのは resolve 自身)。ここで再検査すると
                    # 相互招待が必ず落ちるので、ゲートには通過済みとして渡す。
                    opened = conv.invite(
                        inviter, invitee, tick, int(cell_now[inviter]),
                        same_cell=bool(cell_now[inviter] == cell_now[invitee]),
                        partner_idle=True,
                    )
                    if opened is None:
                        # 不応答(§3「無視された」)/ゲート却下 → 招待側を IDLE へ戻す(層2指摘)
                        reverted.append(inviter)
                if reverted:
                    R.revert_conversation(agents, np.array(reverted, dtype=np.int64))
            finished = conv.step(tick, cell=agents.registry.cell)
            if finished:
                # 終了したセッションの参加者を解放する(行動契約書 §3「終了はエンジン」)。
                # C3 では CLOSING→TERMINAL のあと ``activity`` が CONVERSING のまま残っていた
                # (退去でしか解けなかった)=会話状態の取り残し。書き手は resolve。
                done = np.array(
                    sorted({int(p) for s in finished for p in s.participants}), dtype=np.int64
                )
                R.revert_conversation(agents, done)
            conv.purge_terminal()

        diag_rows.append(
            (
                tick,
                *(int(decision.diag[r].sum()) for r in range(len(DIAG_COLUMNS))),
                int(decision.merged_per_class.sum()),
                len(cands),
                decision.n_calls,
                arbiter.n_pending(),
                len(pending),
                len(intents),
                plan.n_conflicts,
                plan.n_unresolved,
                outcome.n_moved,
                outcome.n_arrived,
                outcome.n_purchases,
                outcome.n_conversations,
                outcome.n_reflections,
                n_undefined,
                n_parse_errors,
                bridge.n_tape_misses - prev_tape_misses,
                (conv.n_opened - prev_sessions) if conv is not None else 0,
            )
        )
        prev_tape_misses = bridge.n_tape_misses
        prev_sessions = conv.n_opened if conv is not None else 0

        if checkpoint_every and ((tick + 1) % checkpoint_every == 0 or tick == ticks - 1):
            t0 = time.perf_counter()
            result.checkpoints.append(
                Checkpoint(
                    tick, agents.state_hash(), world.state_hash(),
                    schedule.population_hash,
                )
            )
            phase["checkpoint"] += time.perf_counter() - t0

    bridge.close()
    result.runner = runner  # type: ignore[attr-defined]
    if runner is not None:
        # D-R2-6: ActualLog は O(t) が本質 → 保持窓を過ぎた生ログを日次集約行へ畳む
        runner.end_of_day(max(0, ticks - 1))
        result.registry_hash = runner.registry_hash
        result.constitution_ok = runner.constitution_ok
        result.replay_date = runner.replay_date
        result.process_seconds = dict(runner.phase_seconds)
        result.process_counters = runner.counters()
        result.actual_log_rows = int(runner.log.n_appended)
        result.compliance_rate = float(runner.compliance().rate)
        result.salient_events = int(runner.salient.n_events)
        result.noticed = int(runner.salient.n_noticed)
        result.dispatches = int(runner.dispatch.n_dispatched)
        result.restocks = int(runner.shelf.n_role_actions + runner.shelf.n_fallback)
        result.deliveries = int(runner.delivery_inbound.n_runs)
        result.parcels = int(runner.last_mile.delivered.sum())
        result.bus_arrivals = int(runner.bus_taxi.n_arrivals)
        result.hotel_checkins = int(runner.hotel.n_checkin)
        result.waste_tonnes_per_day = float(runner.projected_waste_tonnes_per_day())
        band = runner.waste_band_report()
        if band is not None:
            result.waste_band = (float(band.low), float(band.high))
    ledger_growth: tuple[dict[str, Any], dict[str, int]] = ({}, {})
    if ledger is not None:
        # 日次の畳み込み(D-R2-6: 生ログは保持窓・取引行列は日次集約行へ)。
        # **締めを捨てない**——締めると取引行列も当日の廃棄も 0 に戻るので、締めたあとに
        # 現在値でセンサスを回すと faucet/sink/廃棄が全部 0 の空虚な行になり、ゲートが
        # 素通りする(層2レビュー指摘)。``daily_census`` は ``day_index`` の締めを読む。
        closes = ledger.end_of_day(day_index)
        result.day_closed = int(closes.day)
        ledger_growth = ledger.growth_parts()
        # 日次(軽量)センサス+ゲート(境界・経済設計書 §2.4)。
        # engine は economy を import できない(層契約)ので、行の作り手は
        # ``LedgerBundle.census``(economy 側が注入する呼び出し可能)。**失敗しても raise しない**
        # =診断の赤(§2.4「ゲート失敗=較正・holdout 照合に使わない」)。
        row = ledger.daily_census(day_index)
        if row is not None:
            result.census_row = dict(row)
            result.census_pass = bool(row.get("gate_ok", False))
    result.bridge_counters = dict(bridge.counters())
    result.conversation_counters = dict(conv.counters()) if conv is not None else {}
    if conv is not None:
        # 層2指摘の固定: 日末に CONVERSING の個体は活動セッションの参加者だけ(被招待側は C4 まで IDLE)
        result.conversation_counters["conversing_agents_end"] = int(
            np.count_nonzero(agents.registry.activity == int(Activity.CONVERSING))
        )
    result.renderer_counters = dict(perception.counters()) if perception is not None else {}
    result.renderer_name = (
        "perception.Renderer" if perception is not None else type(renderer_obj).__name__
    )
    result.diagnostics = np.asarray(diag_rows, dtype=np.int64).reshape(-1, len(DIAG_RUN_COLUMNS))
    result.phase_seconds = phase
    result.wall_seconds = time.perf_counter() - t_start
    result.arbiter_counters = {k: dict(v) for k, v in arbiter.counters().items()}
    result.money_end = int(agents.registry.money.astype(np.int64).sum())
    result.revenue_end = int(world.pois.revenue.astype(np.int64).sum())
    result.min_stock = int(world.pois.stock.min()) if world.n_poi else 0

    # ---- 状態成長宣言の検査(D-R2-6) ----
    # エンジンの 5 バッファ + **O(t) ログ本体**(ActualLog・取引ログ・納品ログ)。
    # 層2レビュー指摘: 5 バッファだけを外挿しても、D-R2-6 が名指しした「O(t) が本質」の
    # ログ(ActualLog と同型)は 1 バイトも測っていなかった。診断表(``diagnostics_rows``)は
    # 元から測っている(tick あたり 1 行)。
    declarations: dict[str, Any] = dict(GD.declarations())
    measured: dict[str, int] = {
        "pending_apply": peak_pending * GD.PENDING_APPLY_ROW_BYTES,
        "arbiter_backlog": peak_backlog * GD.ARBITER_PENDING_ROW_BYTES,
        "intent_buffer": peak_intents * GD.INTENT_ROW_BYTES,
        "diagnostics_rows": len(diag_rows) * GD.DIAG_ROW_BYTES,
        "tape_rows": result.llm_calls * GD.TAPE_ROW_BYTES,
    }
    if runner is not None:
        log_decls = dict(runner.log.growth_declarations())
        raw = log_decls.get(f"{runner.log.log_id}_raw")
        agg = log_decls.get(f"{runner.log.log_id}_daily")
        raw_bytes = len(runner.log) * int(raw.bytes_per_unit) if raw is not None else 0
        if raw is not None:
            declarations[raw.name] = raw
            measured[raw.name] = raw_bytes
        if agg is not None:
            # ``ActualLog.nbytes`` = 生ログ+索引+日次集約行。生ログぶんを引けば畳み先の実測。
            declarations[agg.name] = agg
            measured[agg.name] = max(0, int(runner.log.nbytes) - raw_bytes)
    led_decls, led_measured = ledger_growth
    declarations.update(led_decls)
    measured.update(led_measured)
    result.growth_measured = measured
    result.growth_report = check_growth(
        declarations,
        measured,
        steps=ticks,
        minutes_per_step=max(1, tick_seconds // 60),
        n_entities=n_agents,
    )
    result.agents = agents  # type: ignore[attr-defined]
    result.world = world  # type: ignore[attr-defined]
    result.schedule = schedule  # type: ignore[attr-defined]
    result.ledger = ledger  # type: ignore[attr-defined]
    return result


# ------------------------------------------------------------------ CLI
def main(argv: list[str] | None = None) -> int:
    """``python -m shibuya.engine.run --agents 5000 --seed 1 --world data/world/v2``。"""
    ap = argparse.ArgumentParser(description="C2 エンジンの 1 シミュ日 mock ラン(予算行 W2)")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--world", type=str, default="data/world/v2",
                    help="世界資産ディレクトリ(無ければ合成小世界へ落ちる)")
    ap.add_argument("--cells", type=int, default=139, help="合成世界のセル数")
    ap.add_argument("--ticks", type=int, default=MINUTES_PER_SIM_DAY)
    ap.add_argument("--checkpoint-every", type=int, default=360)
    ap.add_argument("--day", type=int, default=0, help="曜日(0=月曜)")
    ap.add_argument("--growth-yaml", action="store_true", help="状態成長宣言 YAML を出力して終了")
    ap.add_argument("--no-processes", action="store_true",
                    help="世界過程(C4 第1陣)を止める(ablation の下限対照)")
    ap.add_argument("--no-population", action="store_true",
                    help="W16 母集団を使わず合成個体で回す(下限対照)")
    ap.add_argument("--ablate", action="append", default=[],
                    help="止める過程(過程 id か AB-* の感度試験 id・複数可)")
    args = ap.parse_args(argv)

    if args.growth_yaml:
        print(GD.to_yaml())
        return 0

    world = World.load_or_synthetic(Path(args.world), n_cells=args.cells, seed=args.seed)
    res = run_day(
        n_agents=args.agents,
        seed=args.seed,
        world=world,
        ticks=args.ticks,
        checkpoint_every=args.checkpoint_every,
        day_index=args.day,
        world_dir=args.world,
        processes=not args.no_processes,
        processes_disabled=tuple(args.ablate) or None,
        population=False if args.no_population else None,
    )
    print(res.summary())
    return 0 if (res.conserved and res.min_stock >= 0) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
