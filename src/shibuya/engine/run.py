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
from datetime import timedelta
from pathlib import Path
from typing import Any, Final

import blake3 as _blake3
import numpy as np

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

    @property
    def combined(self) -> str:
        return blake3_hex((self.agents_hash + "\x1f" + self.world_hash).encode("utf-8"))


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
    def conserved(self) -> bool:
        """保存則: Σ所持金 + Σ売上 が不変。"""
        return self.money_start == self.money_end + self.revenue_end

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
            f"= {self.money_end + self.revenue_end:,} (初期 {self.money_start:,}) "
            f"{'OK' if self.conserved else 'NG'} / 最小在庫 {self.min_stock}",
            f"  checkpoint {len(self.checkpoints)} 点 最終 {self.final_hash[:16]}…",
        ]
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
    R.initialize(agents, world, schedule, day_index=day_index, ledger=ledger)
    agents.freeze()
    world.freeze()

    # ---- 知覚レンダラ(C3 結線・B0-B6 の本物) ----
    perception: PerceptionRendererAdapter | None = None
    if renderer is None:
        assets = PerceptionAssets.load_or_synthetic(world_dir, world)
        # 世界内日時 = 既定の開始日 + day_index 日 + tick 分(決定論・expedient)
        start = DEFAULT_START_DATETIME + timedelta(days=int(day_index))
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

        # ---- ⓪ 知覚の tick 前計算(セル配列+B4 描画欄・**1 tick 1 回**) ----
        # 顕著行為(salient_events)は C4(世界過程)が入るまで空。騒音段は
        # ``world.noise_stage_for_tick``(W10 静的昼夜場 or 動的上書き)を**1 本**渡し、
        # 描画と変化検出が同じ値を見るようにする。
        field_rows = None
        if perception is not None:
            perception.prepare_tick(
                tick, salient_events=None, noise_stage=world.noise_stage_for_tick(tick, tick_seconds)
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

        cands = WakeCandidates(
            np.concatenate([p_agent, d_agent, c_agent]),
            np.concatenate([p_cond, d_cond.astype(np.int8), c_cond]),
            np.concatenate([p_class, d_class, c_class]),
            np.full(p_agent.size + d_agent.size + c_agent.size, tick, dtype=np.int64),
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
            plan.confirmed, plan.losers, agents, world, tick, schedule=schedule, ledger=ledger
        )
        phase["phase_c"] += time.perf_counter() - t0
        phase["movement"] += outcome.movement_seconds

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
            conv.step(tick, cell=agents.registry.cell)
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
                Checkpoint(tick, agents.state_hash(), world.state_hash())
            )
            phase["checkpoint"] += time.perf_counter() - t0

    bridge.close()
    if ledger is not None:
        # 日次の畳み込み(D-R2-6: 生ログは保持窓・取引行列は日次集約行へ)
        ledger.end_of_day(day_index)
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
    measured = {
        "pending_apply": peak_pending * GD.PENDING_APPLY_ROW_BYTES,
        "arbiter_backlog": peak_backlog * GD.ARBITER_PENDING_ROW_BYTES,
        "intent_buffer": peak_intents * GD.INTENT_ROW_BYTES,
        "diagnostics_rows": len(diag_rows) * GD.DIAG_ROW_BYTES,
        "tape_rows": result.llm_calls * GD.TAPE_ROW_BYTES,
    }
    result.growth_measured = measured
    result.growth_report = check_growth(
        GD.declarations(),
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
    )
    print(res.summary())
    return 0 if (res.conserved and res.min_stock >= 0) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
