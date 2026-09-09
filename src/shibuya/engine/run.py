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
from shibuya.agents.weekly import apply_to_mock_schedule, load_weekly
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
from shibuya.engine.tape import TapeRow, TapeWriter
from shibuya.llm.contract import TargetKind
from shibuya.llm.fleet import (
    Deferred as FleetDeferred,
    FleetBridge,
    FleetClient,
    LLMCall,
    split_system_user,
)
from shibuya.llm.mock import MockLLM
from shibuya.perception.channels import BudgetMode
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
    "add_fleet_args",
    "fleet_from_args",
    "main",
]

#: δ_think(分tickへ切り上げ後)。既定レーン L1=2.6 秒 → 1 tick(認知設計書 §1)。
DELTA_THINK_TICKS: Final[int] = delta_think_ticks(DEFAULT_LANE, DEFAULT_TICK_SECONDS)

#: 診断表の列(``DIAG_COLUMNS`` の 4 列 + 運用列)。
#: 艦隊の順序制御グループ「時間帯」の刻み[tick](知覚契約書 §2.4 ⑨「時刻表記は5分丸め」)。
#: 同一(セル, 5分帯)の呼は同時に発射し、同一 GPU に寄せない(実装計画書 §7・BN-4)。
TIME_BUCKET_TICKS: Final[int] = 5

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
    #: W17 週次表の同定ハッシュ(週次表なしのランは ``""``)。版の取り違え検出用。
    schedule_hash: str = ""

    @property
    def combined(self) -> str:
        return blake3_hex(
            "\x1f".join(
                (self.agents_hash, self.world_hash, self.population_hash, self.schedule_hash)
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
    #: 知覚のトークン配分(知覚契約書 §3.2 の義務 ablation ①)。``fixed_slots`` / ``single_ranking``。
    budget_mode: str = BudgetMode.FIXED_SLOTS.value
    #: 凍結静的文の版(W14/W15 の parquet: ファイル名→sha256)。凍結文なしのランは空(層2 指摘 09-09)。
    frozen_sources: dict[str, str] = field(default_factory=dict)
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
    # ---- C6-a 実艦隊 ----
    #: ``llm.fleet.FleetConfig.manifest_fields()``(``cache_salt``・``prefix_caching_hash_algo``・
    #: ルーティング規則・in-flight 上限)。**ランが導出して押す**(親決定 09-09)。
    fleet_fields: dict[str, Any] = field(default_factory=dict)
    #: ラン終端の ``drain`` で拾った件数(=最後の tick 以降に届いた応答)。
    fleet_drained_at_end: int = 0
    #: ラン終端でも答えが返らなかった呼(**次ランへ持ち越す=破棄しない**の監査点)。
    fleet_unanswered_at_end: int = 0

    # ---- 便利参照 ----
    def column(self, name: str) -> np.ndarray:
        return self.diagnostics[:, DIAG_RUN_COLUMNS.index(name)]

    @property
    def parse_error_rate(self) -> float:
        """**実効**書式エラー率(``format_ok`` が偽だった呼の割合)。MockLLM なら 0.0。

        C6(09-09)で ``llm.parser`` にラベル別名(「目的地:」「目的:」等)の許容が入った。
        本欄は**別名を許容した後**の率=世界に実際に届いた intent の書式健全性。
        受入指標の定義を動かさない側は ``parse_error_rate_strict``。
        """
        calls = int(self.column("calls").sum()) if self.diagnostics.size else 0
        errs = int(self.column("parse_errors").sum()) if self.diagnostics.size else 0
        return (errs / calls) if calls else 0.0

    @property
    def parse_error_rate_strict(self) -> float:
        """**厳密**書式エラー率(C6 以前の別名表だけで見た判定=B11 と同じ物差し)。

        知覚契約書 §2 卒業条件表の「書式エラー率 ≤0.10」は**この物差しで定義された**ので、
        受入判定は実効を主・厳密を併記で読む(親判断 D-28・PENDING)。
        """
        c = self.bridge_counters
        return float(c.get("parse_error_rate_strict", c.get("parse_error_rate", 0.0)))

    @property
    def label_alias_rate(self) -> float:
        """C6 ラベル別名で読めた応答の割合(別名許容が実際に効いた量)。"""
        return float(self.bridge_counters.get("label_alias_rate", 0.0)) or float(
            self.bridge_counters.get("fleet_label_alias_rate", 0.0)
        )

    @property
    def positional_rate(self) -> float:
        """ラベルを省いた並びを**位置**で読んだ応答の割合(``positional_used``)。"""
        return float(self.bridge_counters.get("positional_rate", 0.0)) or float(
            self.bridge_counters.get("fleet_positional_rate", 0.0)
        )

    @property
    def dictionary_mapped_rate(self) -> float:
        """語彙外の行動語を §7 段0 の辞書写像で救えた割合。"""
        return float(self.bridge_counters.get("dictionary_mapped_rate", 0.0)) or float(
            self.bridge_counters.get("fleet_dictionary_mapped_rate", 0.0)
        )

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
            ``budget_mode``(知覚契約書 §3.2 ablation ① の腕)・
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
            "budget_mode": self.budget_mode,
            "catalog_sha16": catalog_sha16,
            "process_ids": process_ids,
            "ablations": ablations,
            "frozen_sources": dict(self.frozen_sources),
            # 実艦隊(C6-a)。mock/tape ランでは空 dict(欄は常にある)。
            "fleet": dict(self.fleet_fields),
        }

    @property
    def conserved(self) -> bool:
        """保存則: Σ所持金 + Σ売上 + **Σ運賃(外界への sink)** が不変。

        運賃は境界・経済設計書 §2.2 の sink(世帯→外界・科目「持ち出し」)なので、
        bbox 内の現金合計からは正しく消える。C4 以前(列車なし)は ``fares_paid=0`` で
        C2 の等式そのまま。
        """
        return self.money_start == self.money_end + self.revenue_end + self.fares_paid

    #: ``phase_seconds`` を要約行に出す順(大きい順ではなく **tick の骨格の順**)。
    PHASE_ORDER: tuple[str, ...] = (
        "phase_a", "detect", "fleet_wait", "llm", "arbiter", "phase_b", "phase_c",
        "movement", "checkpoint",
    )  # ``movement_cpu`` は壁時計の内訳ではないので別行(下の summary)に出す

    def phase_breakdown(self) -> str:
        """位相別の壁時計[ms/tick](P2 の切り分け=どこに時間が入ったか)。

        ``fleet_wait`` は ``--fleet-wait-s`` の待ちで、``llm``(描画+発射+到着処理)とは
        別に数える。``movement`` は ``resolve`` の「位置確定+密度」区間(予算行 P2)。
        """
        n = max(1, self.ticks)
        parts = [
            f"{k} {self.phase_seconds.get(k, 0.0) / n * 1000.0:.2f}"
            for k in self.PHASE_ORDER
            if self.phase_seconds.get(k, 0.0) > 0.0
        ]
        return " / ".join(parts) + f" / 合計 {self.wall_seconds / n * 1000.0:.2f}"

    @property
    def movement_ms_per_tick(self) -> float:
        """予算行 P2(移動+密度更新)の実測[ms/tick]。**壁時計**。"""
        return self.phase_seconds.get("movement", 0.0) / max(1, self.ticks) * 1_000.0

    @property
    def movement_cpu_ms_per_tick(self) -> float:
        """同区間の**スレッド CPU 時間**[ms/tick](``time.thread_time``)。

        ``movement_ms_per_tick`` との差が大きい = **仕事が増えたのではなく待たされた**
        (艦隊クライアントの asyncio スレッドとの GIL 競合)。実装計画書 §4 の
        「httpx イベントループと計算の干渉が出たら LLM クライアントを別プロセスへ」の判定材料。
        """
        return self.phase_seconds.get("movement_cpu", 0.0) / max(1, self.ticks) * 1_000.0

    @property
    def movement_gil_wait_ratio(self) -> float:
        """movement 区間の「待ち」割合 = 1 − CPU/壁時計(0 なら純粋に計算だけ)。"""
        wall = self.phase_seconds.get("movement", 0.0)
        if wall <= 0.0:
            return 0.0
        return max(0.0, 1.0 - self.phase_seconds.get("movement_cpu", 0.0) / wall)

    def summary(self) -> str:
        calls = self.column("calls").sum() if self.diagnostics.size else 0
        lines = [
            f"[run] n={self.n_agents} cells={self.n_cells} seed={self.seed} "
            f"ticks={self.ticks} world={self.world_source}",
            f"  壁時計 {self.wall_seconds:.2f}s (W2 上限 600s) / "
            f"移動+密度 {self.movement_ms_per_tick:.3f} ms/tick (P2 上限 5 ms)",
            f"  LLM呼 {int(calls):,} = {calls / max(1, self.n_agents):.2f} 呼/体/日 "
            f"(L4 制御目標 10)",
            f"  書式エラー率 実効 {self.parse_error_rate:.3f} / 厳密 "
            f"{self.parse_error_rate_strict:.3f} (受入 ≤0.10) ・別名 "
            f"{self.label_alias_rate:.3f} ・位置読み {self.positional_rate:.3f}"
            f" ・辞書写像 {self.dictionary_mapped_rate:.3f}",
            f"  保存則 Σmoney {self.money_end:,} + Σrevenue {self.revenue_end:,} "
            f"+ Σ運賃 {self.fares_paid:,} "
            f"= {self.money_end + self.revenue_end + self.fares_paid:,} "
            f"(初期 {self.money_start:,}) "
            f"{'OK' if self.conserved else 'NG'} / 最小在庫 {self.min_stock}",
            f"  checkpoint {len(self.checkpoints)} 点 最終 {self.final_hash[:16]}…",
            "  内訳[ms/tick] " + self.phase_breakdown(),
            f"  movement 壁 {self.movement_ms_per_tick:.3f} / CPU "
            f"{self.movement_cpu_ms_per_tick:.3f} ms/tick (P2 上限 5) ・待ち割合 "
            f"{self.movement_gil_wait_ratio:.2f}",
        ]
        if self.frozen_sources:
            lines.append("  凍結静的文 " + " ".join(f"{k}={v[:16]}" for k, v in sorted(self.frozen_sources.items())))
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


def _settle_pending_invites(conv, agents, tick, agent_ids, codes, named, R, np) -> set[int]:
    """返事待ちの招待を**Phase C の前に**確定する(層2 中-1・09-09)。

    正典
    - 行動契約書 §1-2 対象スロット: 承諾は「行動: 会話 **対象: 招待者**」。
    - 同 §6「直前の結果」: 承諾を intent のまま Phase C へ流すと、招待者は待ちで
      CONVERSING なので ``resolve._apply_talk`` が ``PARTNER_BUSY`` を書き、被招待の
      B6 に**偽の失敗**が載る(層2 再現: 51 セッション中 45 件)。ここで消費して防ぐ。

    承諾の規則(中-2・**expedient**: 契約書に承諾の対象規則は無い)
      - 返事が **会話** かつ 対象が **招待者 A**(または **名指しなし**)→ **承諾**。
      - 返事が 会話 でも 対象が **第三者 C** → A へは**拒否**。B の行は intent に残し、
        C への新しい招待として通す。
      - それ以外の行動 → 拒否。

    Returns:
        **intent から外す**個体(=承諾した被招待。承諾は新しい招待ではない)。
    """
    if conv is None or not conv.pending_invites:
        return set()
    cell = agents.registry.cell
    consumed: set[int] = set()
    accepted: list[tuple[int, int]] = []
    reverted: list[int] = []
    # 逐次ループ宣言: この tick に応答した個体のうち返事待ちの数ぶん(≤ 1 tick の呼数)。
    for k in range(int(agent_ids.size)):
        b = int(agent_ids[k])
        if b not in conv.pending_invites:
            continue
        a = conv.pending_inviter_of(b)
        same_cell = bool(a >= 0 and cell[a] == cell[b] and cell[b] >= 0)
        aimed_at_inviter = int(named[k]) in (a, -1)
        ok = bool(codes[k] == C.ACT_TALK) and aimed_at_inviter and same_cell
        opened = conv.resolve_pending(b, tick, accepted=ok)
        if opened is not None:
            accepted.append((a, b))
            consumed.add(b)  # 承諾は新しい招待ではない=intent から外す
        elif a >= 0 and not conv.is_busy(a):
            reverted.append(a)
    if accepted:
        R.set_conversing(
            agents,
            np.array([x for x, _ in accepted], dtype=np.int64),
            np.array([y for _, y in accepted], dtype=np.int64),
        )
    if reverted:
        R.revert_conversation(agents, np.array(sorted(set(reverted)), dtype=np.int64))
    return consumed


def _inviter_of(conv: Any, agent_id: int, condition: int = -1) -> int:
    """**返事待ちの招待**があれば招待者の個体 id、無ければ -1(知覚契約書 §6 起床(ii))。

    起床条件では絞らない(``condition`` は診断用に受けるだけ)。``_settle_pending_invites``
    は**その tick に答えた全員**の中から返事待ちを拾うので、被招待が別の条件
    (一般活動など)で起きた呼も承諾/拒否として消費される。会話ターン起床に限ると
    その分の呼に招待者が載らず、**答えようがないのに拒否と数えられる**(実測: 200体600tick で
    招待文が載った呼は 4 件しかなかった)。

    会話ターン起床には「セッションの話者」と「返事待ちの被招待」の 2 種類が同じ
    ``WakeCondition.CONVERSATION_TURN`` で来る(``conversation.wake_candidates``)が、
    話者には返事待ちが無いので ``pending_inviter_of`` が -1 を返して切り分けになる。
    """
    if conv is None:
        return -1
    return int(conv.pending_inviter_of(int(agent_id)))


def _target_person(target: Any) -> int:
    """``llm.contract.Target`` → 個体 id(``P-nnn`` 以外は ``-1``)。

    行動契約書 §1-2 の「対象: <セルID|物カテゴリ|**個体ID**>」を会話の相手として使う
    (C6・09-09)。パーサは素の整数も PERSON と読むので、そのまま個体 id にする。
    """
    kind = getattr(target, "kind", None)
    if kind is None or int(kind) != int(TargetKind.PERSON):
        return -1
    pid = getattr(target, "person_id", None)
    return -1 if pid is None else int(pid)


def run_day(
    n_agents: int = 5_000,
    seed: int | str = 1,
    world: World | None = None,
    *,
    tick_seconds: int = DEFAULT_TICK_SECONDS,
    ticks: int = MINUTES_PER_SIM_DAY,
    llm: Any | None = None,
    fleet: "FleetClient | None" = None,
    fleet_wait_s: float = 0.0,
    fleet_debug_dir: str | Path | None = None,
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
    budget_mode: str | BudgetMode = BudgetMode.FIXED_SLOTS,
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
        fleet: 実 vLLM 艦隊(``llm.fleet.FleetClient``)。**渡すと LLM 経路が非同期になる**:
            ④ で 1 tick 分をまとめて発射(非ブロッキング)し、④′ で届いた分を拾う。
            繰り延べ(タイムアウト・キュー満杯・接続エラー枯渇)は**次 tick の起床候補へ
            再投入**する(不応期は免除=``resolve.clear_refractory``)。``None`` なら従来の
            同期 1 呼経路(``llm``=mock/tape)で、**挙動は 1 バイトも変わらない**。
        fleet_wait_s: ④′ で未応答が残っているとき**最大この秒数だけ待つ**。既定 0.0=
            純非ブロッキング。本番(予算行 W1: 1 シミュ日 ≤24 h ⇒ 1 tick ≈ 37 秒の壁時計)
            では LLM の往復(数秒)が 1 tick の壁時計に収まるので 0 でよい。**スモークや
            テストのようにエンジンが LLM より桁違いに速いラン**では、0 のままだと応答が
            全部ラン終端に届き δ_think の契約(``t_apply``=起床+δ_perc+δ_think)が
            観測できないので、ここで艦隊に歩調を合わせる(**expedient**・本番経路は変えない)。
        fleet_debug_dir: 書式の原因分析用 jsonl の置き場(``None``=off が既定)。初回パースが
            落ちた呼だけ {プロンプト・初回の生応答・再生成の生応答・実効/厳密の判定・理由} を
            1 行 1 呼で落とす。**テープ形式は変えない**(テープは最終応答 1 行のまま)。
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
        budget_mode: 知覚契約書 §3.2 の**義務 ablation ①**「チャネル固定枠 vs 同一総トークンの
            単一ランキング」の腕。``"fixed"``(既定=現行の描画・1 バイトも変わらない)/
            ``"ranking"``(チャネル別の上限表を使わず群予算だけを守る)。
            ``renderer`` を明示注入したランでは**このフラグは効かない**(注入側が持つ)。
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
    budget_mode_enum = BudgetMode.parse(budget_mode)
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
    frozen_sources_map: dict[str, str] = {}
    if renderer is None:
        assets = PerceptionAssets.load_or_synthetic(world_dir, world)
        frozen_sources_map = dict(getattr(assets, "frozen_sources", {}) or {})
        # 世界内日時 = 気象の再生実日(D-W15)。世界過程が無ければ既定の開始日 + day_index。
        start = DEFAULT_START_DATETIME + timedelta(days=int(day_index))
        if runner is not None and runner.replay_date:
            start = datetime.fromisoformat(runner.replay_date)
        perception = PerceptionRendererAdapter(
            PerceptionRenderer(
                world, agents, assets,
                clock_fn=lambda t: start + timedelta(minutes=int(t)),
                seed=seed,
                budget_mode=budget_mode_enum,
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

    # ---- 実艦隊(C6-a)。テープ・未定義行動台帳・デコード設定は bridge と**同じものを共有** ----
    # ``params``(=テープ列 ``params_hash``)は**艦隊の実デコード設定**から作る
    # (``FleetBridge`` の既定)。mock の {max_tokens:64, temperature:0.0} を引きずらない。
    fleet_bridge = (
        FleetBridge(
            fleet,
            tape=tape_writer,
            tape_row_factory=TapeRow,
            undefined=bridge.undefined,
            debug_dir=fleet_debug_dir,
        )
        if fleet is not None
        else None
    )
    #: 艦隊で繰り延べになった呼 ``(agent, condition, class_rank, since_tick)``。
    #: 次 tick の起床候補へ**そのまま再投入**する(破棄禁止=憲法1)。
    fleet_deferred: list[tuple[int, int, int, int]] = []
    n_fleet_reinjected = 0
    n_fleet_resent = 0
    #: 繰り延べ中の個体(再送を数えるためだけの集合。呼数 L4 は**発射数**で数える)。
    fleet_waiting: set[int] = set()

    detector = ChangeDetector(n_agents, world.n_cells, walkable_area_m2=walkable)
    arbiter = Arbiter(
        n_agents, salt, budget if budget is not None else call_budget_per_tick(n_agents)
    )
    space = C.ResourceSpace(world.n_poi, n_agents, world.n_cells)

    # 計画境界。W17 週次表(w17_schedule.parquet)があればそれを使い、無ければ mock 日課の 5 境界へ落ちる
    # (C5-b 結線・09-09)。mock 経路は --no-population と合成世界の下限対照としてそのまま残す。
    weekly = load_weekly(world_dir) if (world_dir is not None and pop is not None) else None
    if weekly is not None:
        weekly = weekly.restrict_to(pop.source_agent_id)
        b_agent, b_cond, b_tick = weekly.boundary_events(day_index)
        schedule = apply_to_mock_schedule(schedule, weekly, day_index)  # 拠点セル(自宅/職場)の上書き
    else:
        b_agent, b_slot, b_tick = schedule.events_of_day(day_index)
        b_cond = np.array(
            [
                int(WakeCondition.PLAN_GENERAL),
                int(WakeCondition.PLAN_TRANSIT),
                int(WakeCondition.PLAN_GENERAL),
                int(WakeCondition.PLAN_TRANSIT),
                int(WakeCondition.PLAN_SLEEPING),
            ],
            dtype=np.int8,
        )[b_slot]
    b_start = np.searchsorted(b_tick, np.arange(ticks + 1), side="left")
    schedule_hash = weekly.schedule_hash() if weekly is not None else ""

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
    # ``fleet_wait`` は ``--fleet-wait-s`` の待ち(``llm`` から分離して数える=P2 の切り分け用)。
    # ``movement_cpu`` は movement 区間の**スレッド CPU 時間**(壁時計との差=GIL 待ち)。
    phase = {k: 0.0 for k in ("detect", "arbiter", "llm", "fleet_wait", "phase_a", "phase_b",
                              "phase_c", "movement", "movement_cpu", "checkpoint")}
    diag_rows: list[tuple[int, ...]] = []
    # (t_apply, class, agent, condition, text, action_code, target_person)
    # ``target_person`` = LLM が「対象」欄に書いた個体 id(-1=名指しなし・C6 09-09)。
    pending: list[tuple[int, int, int, int, str, int, int]] = []
    #: この tick に応答を適用した個体 → 行動コード(会話の被招待の返事を読むのに使う)。
    applied_now: dict[int, int] = {}
    #: 会話の相手の由来(``conv_*`` 診断行の素材)。
    talk_stats: dict[str, int] = {}
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
                tgt_person = np.fromiter(
                    (due[int(i)][6] for i in order), dtype=np.int64, count=order.size
                )
                agents_in_order = ag[order]
                # 個体 → (行動コード, **LLM が名指しした**対象)。会話の承諾/相互指名の判定に使う
                # (エンジンが解決した対象ではない=「誰に向けた返事か」は名指しにしか無い)。
                applied_now = {
                    int(agents_in_order[k]): (int(codes[k]), int(tgt_person[k]))
                    for k in range(order.size)
                }
                # ---- ①-b 会話: **返事待ちの解決を Phase C より前に**(層2 中-1) ----
                # 被招待 B の承諾「会話 対象: P-A」を intent のまま Phase C へ流すと、
                # A は招待して CONVERSING なので ``_apply_talk`` が PARTNER_BUSY を書き、
                # B の「直前の結果」(B6)に**偽の失敗**が載る。承諾はここで消費し、
                # B の行を intent から外す(承諾は新しい招待ではない)。
                consumed = _settle_pending_invites(
                    conv, agents, tick, agents_in_order, codes, tgt_person, R, np
                )
                keep = (
                    np.array(
                        [int(a) not in consumed for a in agents_in_order.tolist()], dtype=bool
                    )
                    if consumed
                    else np.ones(order.size, dtype=bool)
                )
                llm_intents = C.intents_from_responses(
                    agents, world, space, tick, agents_in_order[keep], cond[order][keep],
                    codes[keep],
                    home_cell=schedule.home_cell, work_cell=schedule.work_cell,
                    target_person=tgt_person[keep], stats=talk_stats, run_salt=salt,
                )
            else:
                applied_now = {}
        else:
            applied_now = {}
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
            p_cond = b_cond[lo:hi]
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

        # ---- ④′ 艦隊からの到着(前 tick 以前に発射した分)・**非ブロッキング** ----
        # ③ の前に置く: 繰り延べになった呼をこの tick の起床候補へ合流させるため。
        n_parse_errors_fleet = 0
        if fleet_bridge is not None:
            t0 = time.perf_counter()
            if fleet_wait_s > 0.0 and fleet_bridge.client.outstanding:
                fleet_bridge.client.wait_idle(timeout=fleet_wait_s)
                phase["fleet_wait"] += time.perf_counter() - t0
                t0 = time.perf_counter()
            for res in fleet_bridge.poll():
                if isinstance(res, FleetDeferred):
                    fleet_deferred.append(
                        (
                            int(res.call.agent_id),
                            int(res.call.condition),
                            int(res.call.wake_class),
                            int(res.call.wake_since),
                        )
                    )
                    continue
                fleet_waiting.discard(int(res.agent_id))
                # t_apply = 起床 + δ_perc + δ_think(§2.4)。到着が遅れたぶんは
                # **破棄せず**この tick 以降へ(締切超過=繰り延べアービタの趣旨)。
                t_apply = res.tick + delta_think_ticks(res.lane, tick_seconds)
                pending.append((
                    max(t_apply, tick + 1), res.wake_class, res.agent_id,
                    res.condition, res.text, res.action_code, _target_person(res.target),
                ))
                if not res.format_ok:
                    n_parse_errors_fleet += 1
                if conv is not None and res.condition == int(WakeCondition.CONVERSATION_TURN):
                    conv.utterance(
                        res.agent_id, tick, action=res.parse.action, comment=res.parse.comment
                    )
            phase["llm"] += time.perf_counter() - t0

        # ---- 艦隊の繰り延べを起床候補へ再投入(不応期は免除・親決定 (a)・09-09) ----
        if fleet_deferred:
            f_agent = np.fromiter((x[0] for x in fleet_deferred), dtype=np.int64,
                                  count=len(fleet_deferred))
            f_cond = np.fromiter((x[1] for x in fleet_deferred), dtype=np.int8,
                                 count=len(fleet_deferred))
            f_class = np.fromiter((x[2] for x in fleet_deferred), dtype=np.int64,
                                  count=len(fleet_deferred))
            f_since = np.fromiter((x[3] for x in fleet_deferred), dtype=np.int64,
                                  count=len(fleet_deferred))
            # 「答えが来なかった」呼は起床の抑止対象ではない=張った不応期を戻す。
            R.clear_refractory(agents, f_agent, f_cond)
            n_fleet_reinjected += len(fleet_deferred)
            fleet_deferred.clear()
        else:
            f_agent = np.empty(0, dtype=np.int64)
            f_cond = np.empty(0, dtype=np.int8)
            f_class = np.empty(0, dtype=np.int64)
            f_since = np.empty(0, dtype=np.int64)

        cands = WakeCandidates(
            np.concatenate([p_agent, d_agent, c_agent, s_agent, f_agent]),
            np.concatenate([p_cond, d_cond.astype(np.int8), c_cond, s_cond, f_cond]),
            np.concatenate([p_class, d_class, c_class, s_class, f_class]),
            np.concatenate(
                [
                    np.full(
                        p_agent.size + d_agent.size + c_agent.size + s_agent.size,
                        tick, dtype=np.int64,
                    ),
                    f_since,  # 再投入は**元の待ち始め**を保つ(昇格が巻き戻らない)
                ]
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
            if fleet_bridge is None:
                # 逐次ループ宣言2: 選抜された呼数ぶん(平均 35/tick)
                for i in range(len(sel)):
                    a = int(sel.agent_id[i])
                    cls = int(decision.selected_eff_class[i])
                    cond = int(sel.condition[i])
                    res = bridge.call(
                        a, tick, cls, cond,
                        cell=int(cell[a]), activity=int(act[a]), hunger=int(hun[a]),
                        last_action=int(last_act[a]),
                        inviter=_inviter_of(conv, a, cond),
                    )
                    pending.append((
                        res.t_apply, cls, a, cond, res.text, res.action_code,
                        _target_person(res.target),
                    ))
                    if not res.format_ok:
                        n_parse_errors += 1
                    if conv is not None and cond == int(WakeCondition.CONVERSATION_TURN):
                        # 会話ターンの応答は**発話ブロック**(1呼=1ブロック・§3)
                        conv.utterance(a, tick, action=res.parse.action, comment=res.parse.comment)
            else:
                # 逐次ループ宣言2′: 同じ呼数ぶん(描画は同じ・往復だけ非同期になる)
                calls: list[LLMCall] = []
                for i in range(len(sel)):
                    a = int(sel.agent_id[i])
                    cls = int(decision.selected_eff_class[i])
                    cond = int(sel.condition[i])
                    rendered = bridge.renderer.render(
                        agent_id=a, tick=tick, cell=int(cell[a]), activity=int(act[a]),
                        hunger=int(hun[a]), wake_class=cls, condition=cond,
                        last_action=int(last_act[a]),
                        inviter=_inviter_of(conv, a, cond),
                    )
                    sys_txt, usr_txt = split_system_user(
                        rendered.text, rendered.blocks[0][1] if rendered.blocks else ""
                    )
                    if a in fleet_waiting:
                        n_fleet_resent += 1
                    fleet_waiting.add(a)
                    calls.append(
                        LLMCall(
                            call_id=f"{tick}:{a}:{cls}",
                            agent_id=a, tick=tick, wake_class=cls, condition=cond,
                            prompt=rendered.text, system=sys_txt, user=usr_txt,
                            blocks=rendered.blocks, lane=lane, cell=int(cell[a]),
                            time_bucket=tick // TIME_BUCKET_TICKS,
                            since_tick=int(sel.since_tick[i]),
                            prompt_hash_hint=rendered.prompt_hash,
                        )
                    )
                # 発射は**非ブロッキング**。返るのは「キューに入らなかった」分だけ。
                for d in fleet_bridge.submit(calls):
                    fleet_deferred.append(
                        (int(d.call.agent_id), int(d.call.condition),
                         int(d.call.wake_class), int(d.call.wake_since))
                    )
            result.llm_calls += len(sel)  # L4 の呼数=**発射数**(再送も 1 呼・親決定 09-09)
        # 艦隊経路の書式エラーは ④′(到着時)で数える=選抜が 0 の tick でも計上する
        n_parse_errors += n_parse_errors_fleet
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
        phase["movement_cpu"] += outcome.movement_cpu_seconds
        result.fares_paid += outcome.fare_paid
        result.n_boarded += outcome.n_boarded
        result.n_alighted += outcome.n_alighted
        result.n_queued += outcome.n_queued

        # ---- 会話セッション(行動契約書 §3・C6 で設計準拠化 09-09) ----
        # ①返事待ちの被招待が答えていれば成立/不成立を確定 → ②新しい招待を捌く
        # → ③期限切れの返事待ちを落とす。相手は **LLM が「対象」欄で名指しした個体**
        # (``C.talk_partners``)。相手が同じ適用バッチに居なければ次 tick に
        # ``WakeCondition.CONVERSATION_TURN`` で起こして本人の呼で答えさせる。
        if conv is not None:
            cell_now = agents.registry.cell
            act_now = agents.registry.activity
            reverted: list[int] = []

            def _revert(a: int) -> None:
                """招待が流れた側を IDLE へ戻す候補に積む。

                **すでに別のセッションに入っている個体は戻さない**(相互招待で
                A→B と B→C が同時に立つと、B の招待が流れたときに B が A との
                セッションから引き剥がされて片側だけ CONVERSING が残る)。
                """
                if a >= 0 and not conv.is_busy(int(a)):
                    reverted.append(int(a))

            # ①(返事待ちの解決)は **Phase C の前**に済んでいる(``_settle_pending_invites``)。

            # ---- ② 新しい招待(resolve が通した 会話 を入口にする) ----
            talk = np.flatnonzero(plan.confirmed.action_code == C.ACT_TALK)
            if talk.size:
                inviters = plan.confirmed.agent_id[talk].astype(np.int64)
                invitees = plan.confirmed.target_id[talk].astype(np.int64)
                # 逐次ループ宣言3b: 会話成立数ぶん(≤ 1 tick の呼数)。個体数に比例しない。
                for j in range(inviters.size):
                    inviter = int(inviters[j])
                    invitee = int(invitees[j])
                    if invitee < 0 or invitee >= agents.n:
                        _revert(inviter)
                        continue
                    if int(act_now[inviter]) != int(Activity.CONVERSING):
                        continue  # resolve が失敗させた(相手が会話中/去った)
                    same_cell = bool(cell_now[inviter] == cell_now[invitee])
                    b_code, b_named = applied_now.get(invitee, (-1, -1))
                    # **相互指名**= 相手も自分の呼で**こちらを名指しして** 会話 と答えた。
                    # (エンジンが解決した対象ではなく LLM が書いた対象で見る=中-2)
                    mutual = b_code == C.ACT_TALK and b_named == inviter
                    if mutual and conv.invite_blocked_by_refractory(inviter, invitee, tick):
                        conv.n_invite_refractory_blocked += 1  # 軽-5: 相互指名も不応期の対象
                        _revert(inviter)
                        continue
                    if mutual:
                        # その場で成立。相手の意思は相手自身の呼に出ているので抽選は引かない。
                        conv.n_invites += 1
                        conv.stamp_invite_refractory(inviter, invitee, tick)
                        opened = conv.invite(
                            inviter, invitee, tick, int(cell_now[inviter]),
                            same_cell=same_cell, partner_idle=True, answered=True,
                        )
                        if opened is None:
                            _revert(inviter)  # 内訳は ``conv.invite`` が数える
                        else:
                            conv.n_accepted += 1
                            R.set_conversing(
                                agents,
                                np.array([inviter], dtype=np.int64),
                                np.array([invitee], dtype=np.int64),
                            )
                    else:
                        # 相手はまだ**招待を見ていない**(この tick の相手の応答は
                        # 招待の載っていないプロンプトへの答え)→ **次 tick に被招待で
                        # 起こして本人に答えさせる**(知覚契約書 §6 起床(ii))。
                        # 招待側は CONVERSING のまま待つ。
                        if not conv.register_pending(
                            inviter, invitee, tick, int(cell_now[inviter]),
                            same_cell=same_cell,
                        ):
                            _revert(inviter)

            # ---- ③ 期限切れの返事待ち(「無視された」=呼を消費しない) ----
            for stale in conv.expire_pending(tick):
                _revert(stale)
            if reverted:
                R.revert_conversation(agents, np.array(sorted(set(reverted)), dtype=np.int64))
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
                    schedule_hash,
                )
            )
            phase["checkpoint"] += time.perf_counter() - t0

    # ---- 艦隊の残りを吸い切る(**捨てない**)。テープを閉じる前に置く ----
    if fleet_bridge is not None:
        n_late = 0
        for res in fleet_bridge.drain():
            if isinstance(res, FleetDeferred):
                fleet_deferred.append(
                    (int(res.call.agent_id), int(res.call.condition),
                     int(res.call.wake_class), int(res.call.wake_since))
                )
                continue
            n_late += 1
            pending.append((
                res.tick + delta_think_ticks(res.lane, tick_seconds), res.wake_class,
                res.agent_id, res.condition, res.text, res.action_code,
                _target_person(res.target),
            ))
        result.fleet_drained_at_end = n_late
        # ラン終端でも答えが返らなかった呼(**次ランへ持ち越す**の監査点。0 が正常)
        result.fleet_unanswered_at_end = len(fleet_deferred)
        fleet_bridge.close()

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
    if fleet_bridge is not None:
        result.bridge_counters.update(fleet_bridge.counters())
        result.bridge_counters["fleet_reinjected"] = float(n_fleet_reinjected)
        result.bridge_counters["fleet_resent"] = float(n_fleet_resent)
        result.fleet_fields = dict(fleet.config.manifest_fields())
    result.conversation_counters = dict(conv.counters()) if conv is not None else {}
    if conv is not None:
        # 会話の相手の由来(行動契約書 §1-2 の対象スロットが効いているかの監査点)。
        result.conversation_counters["conv_target_named"] = int(talk_stats.get("talk_named", 0))
        result.conversation_counters["conv_fallback_same_batch"] = int(
            talk_stats.get("talk_fallback", 0)
        )
        result.conversation_counters["conv_target_absent"] = int(talk_stats.get("talk_absent", 0))
    if conv is not None:
        # 層2指摘の固定: 日末に CONVERSING の個体は活動セッションの参加者だけ(被招待側は C4 まで IDLE)
        result.conversation_counters["conversing_agents_end"] = int(
            np.count_nonzero(agents.registry.activity == int(Activity.CONVERSING))
        )
    result.renderer_counters = dict(perception.counters()) if perception is not None else {}
    result.frozen_sources = frozen_sources_map
    result.renderer_name = (
        "perception.Renderer" if perception is not None else type(renderer_obj).__name__
    )
    # 実際に描いた腕(注入レンダラなら**そちらの値**が正)。§3.2 ablation ① の同定欄。
    result.budget_mode = BudgetMode.parse(
        getattr(getattr(perception, "renderer", None), "budget_mode", budget_mode_enum)
        if perception is not None
        else budget_mode_enum
    ).value
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
def add_fleet_args(ap: "argparse.ArgumentParser") -> None:
    """実艦隊の共通引数(``engine.run`` と ``shibuya.cli`` で同じ綴りにするため 1 か所に置く)。

    ``--mode`` は **run manifest の実行モード**(smoke/calibration/holdout/ablation/production・
    運用設計書 §1.2)であって、``run_day(mode=...)`` の record/replay ではない。
    ``cache_salt`` の勘定分離(較正と holdout が prefix キャッシュを共有しない)に効く。
    """
    from shibuya.llm.fleet import DEFAULT_T1_MAX_TOKENS, DEFAULT_TEMPERATURE
    from shibuya.manifest.schema import Mode as _Mode

    ap.add_argument("--llm", choices=("mock", "fleet"), default="mock",
                    help="LLM 経路(fleet=実 vLLM 艦隊・--endpoints 必須)")
    ap.add_argument("--endpoints", type=str, default="",
                    help="カンマ区切り http://host:port(既定艦隊は 7 本=xxhash(call_id) mod 7)")
    ap.add_argument("--model", type=str, default="",
                    help="served-model-name(空なら /v1/models の先頭)")
    ap.add_argument("--mode", choices=[m.value for m in _Mode], default="smoke",
                    help="実行モード(cache_salt の勘定分離・record/replay とは別物)")
    ap.add_argument("--run-id", type=str, default="",
                    help="manifest の run_id(cache_salt の第2要素)")
    ap.add_argument("--tape", type=str, default="", help="録画テープの出力先ディレクトリ")
    ap.add_argument(
        "--temperature", type=float, default=DEFAULT_TEMPERATURE,
        help=("T1 の温度(既定 0.7=知覚契約書 §2.5/卒業条件表・運用設計書 §1.3 の本番値。"
              "運用設計書 §1.2 の設定節は欄形だけで数値を持たない)"),
    )
    ap.add_argument(
        "--max-tokens", type=int, default=DEFAULT_T1_MAX_TOKENS,
        help="T1 の max_tokens(既定 96=2 行形の最大 ≒70 tok に余裕・expedient)",
    )
    ap.add_argument(
        "--fleet-debug-dir", type=str, default="",
        help=("書式の原因分析用 jsonl の置き場(既定 off・診断のみ)。初回パースが落ちた呼の "
              "プロンプト/初回の生応答/再生成の生応答/実効・厳密の判定/理由 を 1 行 1 呼で書く"),
    )
    ap.add_argument("--fleet-wait-s", type=float, default=0.0,
                    help="④′ で未応答が残るとき tick ごとに最大この秒数だけ艦隊を待つ(既定 0=純非ブロッキング・スモーク用)")


def fleet_from_args(args: Any, ap: "argparse.ArgumentParser | None" = None) -> FleetClient | None:
    """``add_fleet_args`` の結果 → ``FleetClient``(``--llm mock`` なら ``None``)。"""
    from shibuya.llm.fleet import FleetConfig
    from shibuya.manifest.schema import Mode as _Mode

    if getattr(args, "llm", "mock") != "fleet":
        return None
    eps = tuple(e.strip() for e in str(args.endpoints).split(",") if e.strip())
    if not eps:
        msg = "--llm fleet には --endpoints(カンマ区切り http://host:port)が要る"
        if ap is not None:
            ap.error(msg)
        raise SystemExit(msg)
    from shibuya.llm.fleet import DEFAULT_T1_MAX_TOKENS, DEFAULT_TEMPERATURE

    return FleetClient(
        FleetConfig(
            endpoints=eps,
            model=str(args.model),
            mode=_Mode(args.mode),
            run_id=str(getattr(args, "run_id", "")),
            run_seed=int(getattr(args, "seed", 0)),
            temperature=float(getattr(args, "temperature", DEFAULT_TEMPERATURE)),
            t1_max_tokens=int(getattr(args, "max_tokens", DEFAULT_T1_MAX_TOKENS)),
        )
    )


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
    add_fleet_args(ap)
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
        fleet=fleet_from_args(args, ap),
        fleet_wait_s=float(args.fleet_wait_s),
        fleet_debug_dir=args.fleet_debug_dir or None,
        tape_path=args.tape or None,
        processes=not args.no_processes,
        processes_disabled=tuple(args.ablate) or None,
        population=False if args.no_population else None,
    )
    print(res.summary())
    return 0 if (res.conserved and res.min_stock >= 0) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
