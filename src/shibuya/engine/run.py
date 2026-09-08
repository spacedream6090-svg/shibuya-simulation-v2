"""engine.run — 1 シミュ日の mock ラン(予算行 **W2**)と CLI。

正典
- 予算宣言表 **W2**: 「壁時計/シミュ日(Phase 2・**5千体・CPU・mock LLM**)**≤10分**。
  mock は呼び出しコストゼロ級=**エンジン性能の検収値**」。
- 運用設計書 §2.2/§2.4: tick の骨格 =
  ① 前 tick までに届いた LLM 応答を **apply_key 昇順**で適用(=Phase A の intent 源)
  ② 変化検出(P6)→ 起床候補
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

expedient(本モジュール分)
- δ_think = 0(認知設計書 §1 の L1「出力64・思考0=2.6秒」を分tickへ切り上げると 1 tick)。
  よって ``t_apply = tick + 1``。L2/L3(2,048/7,500 tok)は C3 のレーン表で入る。
- プロンプトは ``[t<tick>|c<cell>|a<activity>|h<hunger>]`` の最小形。B0-B6 のレンダラは C3。
- 会話は「1呼=1発話ブロック」の**セッション生成まで**(継続ターン・終了判定は C3/C4)。
- 週の曜日は ``day_index``(既定 0=月曜)。週 7 日表は C4 の PlanSpec。
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import blake3 as _blake3
import numpy as np

from shibuya.agents.schedule import synthesize
from shibuya.agents.state import WAKE_CONDITION_CLASS, AgentState, WakeCondition
from shibuya.core.growth import GrowthReport, check_growth
from shibuya.core.hashing import apply_key_array, blake3_hex
from shibuya.core.types import DEFAULT_TICK_SECONDS, MINUTES_PER_SIM_DAY
from shibuya.engine import commit as C
from shibuya.engine import growth_decl as GD
from shibuya.engine import resolve as R
from shibuya.engine.arbiter import Arbiter, WakeCandidates, call_budget_per_tick
from shibuya.engine.change_detect import ChangeDetector
from shibuya.engine.scheduler import DIAG_COLUMNS
from shibuya.llm import LLMRequest
from shibuya.llm.mock import MockLLM
from shibuya.world.state import World

__all__ = [
    "DIAG_RUN_COLUMNS",
    "DELTA_THINK_TICKS",
    "Checkpoint",
    "RunResult",
    "run_salt_for",
    "run_day",
    "main",
]

#: δ_think(分tickへ切り上げ後)。L1 レーン=0 秒 → 次 tick 先頭(expedient)。
DELTA_THINK_TICKS: Final[int] = 1

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

    # ---- 便利参照 ----
    def column(self, name: str) -> np.ndarray:
        return self.diagnostics[:, DIAG_RUN_COLUMNS.index(name)]

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
        for col in DIAG_COLUMNS:
            lines.append(f"  診断 {col}: {int(self.column(col).sum()):,}")
        if self.growth_report is not None:
            lines.append("  " + self.growth_report.as_text().replace("\n", "\n  "))
        return "\n".join(lines)


def _prompt(tick: int, cell: int, activity: int, hunger: int) -> str:
    """最小プロンプト(B0-B6 のレンダラは C3)。"""
    return f"[t{tick}|c{cell}|a{activity}|h{hunger}]"


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

    Returns:
        ``RunResult``。
    """
    t_start = time.perf_counter()
    world = world if world is not None else World.synthetic(n_cells=n_cells, seed=seed)
    llm = llm if llm is not None else MockLLM(master_seed=seed)
    salt = run_salt_for(seed)
    agents = AgentState(n_agents)
    schedule = synthesize(n_agents, seed, world.n_cells)
    R.initialize(agents, world, schedule, day_index=day_index)
    agents.freeze()
    world.freeze()

    detector = ChangeDetector(n_agents, world.n_cells)
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
    )
    result.money_start = int(agents.registry.money.astype(np.int64).sum())
    phase = {k: 0.0 for k in ("detect", "arbiter", "llm", "phase_a", "phase_b", "phase_c",
                              "movement", "checkpoint")}
    diag_rows: list[tuple[int, ...]] = []
    pending: list[tuple[int, int, int, int, str]] = []  # (t_apply, class, agent, condition, text)
    peak_pending = 0
    peak_intents = 0
    peak_backlog = 0
    n_undefined_total = 0

    # 逐次ループ宣言1: tick 数ぶん
    for tick in range(ticks):
        R.advance_body(agents, tick)

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
                codes = np.fromiter(
                    (C.parse_action(due[int(i)][4]) for i in order),
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
        det = detector.detect(world, agents, tick)
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

        cands = WakeCandidates(
            np.concatenate([p_agent, d_agent]),
            np.concatenate([p_cond, d_cond.astype(np.int8)]),
            np.concatenate([p_class, d_class]),
            np.full(p_agent.size + d_agent.size, tick, dtype=np.int64),
        )

        # ---- ③ 繰り延べアービタ(§6) ----
        t0 = time.perf_counter()
        decision = arbiter.step(tick, cands, agents.registry.refractory_until)
        phase["arbiter"] += time.perf_counter() - t0

        # ---- ④ LLM 呼(応答は pending_apply へ) ----
        t0 = time.perf_counter()
        sel = decision.selected
        if len(sel):
            R.set_refractory(agents, sel.agent_id, sel.condition, tick)
            cell = agents.registry.cell
            act = agents.registry.activity
            hun = agents.registry.hunger
            t_apply_value = tick + DELTA_THINK_TICKS
            # 逐次ループ宣言2: 選抜された呼数ぶん(平均 35/tick)
            for i in range(len(sel)):
                a = int(sel.agent_id[i])
                cls = int(decision.selected_eff_class[i])
                resp = llm.complete(
                    LLMRequest(
                        agent_id=a,
                        tick=tick,
                        wake_class=cls,
                        prompt=_prompt(tick, int(cell[a]), int(act[a]), int(hun[a])),
                    )
                )
                pending.append((t_apply_value, cls, a, int(sel.condition[i]), resp.text))
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
        outcome = R.apply(plan.confirmed, plan.losers, agents, world, tick, schedule=schedule)
        phase["phase_c"] += time.perf_counter() - t0
        phase["movement"] += outcome.movement_seconds

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
            )
        )

        if checkpoint_every and ((tick + 1) % checkpoint_every == 0 or tick == ticks - 1):
            t0 = time.perf_counter()
            result.checkpoints.append(
                Checkpoint(tick, agents.state_hash(), world.state_hash())
            )
            phase["checkpoint"] += time.perf_counter() - t0

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
    )
    print(res.summary())
    return 0 if (res.conserved and res.min_stock >= 0) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
