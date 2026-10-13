"""engine.systems.observe — 計器の系 observe(L21+L22)と checkpoint(L23)(第 1 期 1-0・段 B)。

中身は HEAD ``ee3abc7`` の ``engine/run.py`` の ``run_day`` の同じ区間のまま(局所の名を箱から結ぶ・文は変えない)。

- observe: 診断の行(``RunStats.diag_rows``)・診断の差分の基準(``prev_tape_misses``・``prev_sessions``)・計画の就寝の数え・
  在圏の標本(``presence.sample``=O70)・規範の計器(``norm_meter.observe_tick``=O34)・在圏 journal(``occ_*``)。
- checkpoint: behavior-hash と full-hash(``state_io.full_state_hash`` を通す)と checkpoint の記録(読むだけ。
  活動層の文の digest のキャッシュ O2 を書く)。

逐次ループ宣言: なし(配列演算・tick に 1 回)。
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from shibuya.core.hashing import blake3_hex
from shibuya.engine.scheduler import DIAG_COLUMNS
from shibuya.engine.systems import state_io as SIO

__all__ = ["observe", "checkpoint"]


def observe(ctx: Any, b: Any) -> None:
    """L21+L22: 診断の行・在圏の標本・規範の計器・在圏 journal(HEAD run.py:4403-4451)。"""
    tick = ctx.T
    sc, rs, L = b.scratch, b.runstats, b.layers
    agents, world = b.soa.agents, b.soa.world
    bridge, conv, arbiter, presence, norm_meter = L.bridge, L.conv, L.arbiter, L.presence, L.norm_meter
    decision, cands, intents, plan, outcome = sc.decision, sc.cands, sc.intents, sc.plan, sc.outcome
    n_undefined, n_parse_errors = sc.n_undefined, sc.parse_errors
    diag_rows, sleep_counts = rs.diag_rows, rs.sleep_tally
    occupancy_every = b.cfg.occupancy_every
    occ_ticks, occ_counts, occ_kind, occ_transit = rs.occ_ticks, rs.occ_counts, rs.occ_kind, rs.occ_transit

    diag_rows.append(
        (
            tick,
            *(int(decision.diag[r].sum()) for r in range(len(DIAG_COLUMNS))),
            int(decision.merged_per_class.sum()),
            len(cands),
            decision.n_calls,
            arbiter.n_pending(),
            len(b.llm.pending),
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
            bridge.n_tape_misses - rs.prev_tape_misses,
            (conv.n_opened - rs.prev_sessions) if conv is not None else 0,
            decision.n_sleep_suppressed,  # D-56
            decision.n_outside_suppressed,  # D-66
        )
    )
    rs.prev_tape_misses = bridge.n_tape_misses
    rs.prev_sessions = conv.n_opened if conv is not None else 0
    if outcome.n_planned_sleep:  # 就寝地へ着いて寝たぶん(D-62 意図の保持)
        sleep_counts["arrived"] = (
            sleep_counts.get("arrived", 0) + int(outcome.n_planned_sleep)
        )

    if presence is not None:
        presence.sample(tick)  # 正時の在圏・計画一致率(在圏 journal と同じ位置)
    if norm_meter is not None:
        norm_meter.observe_tick(tick)  # 第308 D-107 (a): 同行の検出(位置が確定した後・読むだけ)
    if occupancy_every and tick % occupancy_every == 0:
        occ_ticks.append(int(tick))
        occ_counts.append(np.asarray(world.cells.density, dtype=np.int32).copy())
        _k = np.asarray(agents.registry.field("kind"), dtype=np.int64)
        _c = np.asarray(agents.registry.cell, dtype=np.int64)
        _ok = (_c >= 0) & (_c < world.n_cells)
        _kc = np.bincount(_k[_ok] * world.n_cells + _c[_ok], minlength=9 * world.n_cells)[: 9 * world.n_cells]
        occ_kind.append(_kc.reshape(9, world.n_cells).astype(np.int32))
        # D-66: 種別 × 在圏/乗車中/域外(9×3)。**既存キーは 1 本も変えない**
        # (``tools/c7`` は無改造で読める=知らないキーは無視される)。
        _ts = np.clip(np.asarray(agents.registry.transit_state, dtype=np.int64), 0, 2)
        _tk = np.bincount(_k * 3 + _ts, minlength=27)[:27]
        occ_transit.append(_tk.reshape(9, 3).astype(np.int32))


def checkpoint(ctx: Any, b: Any) -> None:
    """L23: checkpoint の 3 本のハッシュ(HEAD run.py:4452-4495)。"""
    from shibuya.engine.run import Checkpoint

    tick = ctx.T
    cfg, L, rs = b.cfg, b.layers, b.runstats
    checkpoint_every, total_ticks, checkpoint_detail = cfg.checkpoint_every, cfg.total_ticks, cfg.checkpoint_detail
    agents, world = b.soa.agents, b.soa.world
    act_layer, intent_layer, runner = L.act_layer, L.intent_layer, L.runner
    schedule, schedule_hash = b.fx.schedule, b.fx.schedule_hash
    result, phase = rs.result, rs.phase

    if checkpoint_every and ((tick + 1) % checkpoint_every == 0 or tick == total_ticks - 1):
        t0 = time.perf_counter()
        _act_hash = (
            (
                act_layer.state_hash()
                if intent_layer is None
                else blake3_hex(
                    f"{act_layer.state_hash()}\x1f{intent_layer.state_hash()}".encode()
                )
            )
            if act_layer is not None
            else ""
        )
        # ---- 10b(A2・A3): behavior-hash と full-hash を**別に**計算して記録に足す(final は今の定義) ----
        # 読むだけ(乱数を引かない・状態を書かない)。外の状態の持ち主は状態台帳の ``items`` の根の鍵。
        _owners = SIO.hash_owners(b)
        _memo: dict[str, tuple[bytes, int]] = {}  # 同じ属性を 2 本のハッシュで 2 度直列化しない
        _full, _full_bytes = SIO.full_state_hash(
            agents, world,
            runner.salient.pstate if runner is not None else None,
            schedule.population_hash, schedule_hash, _owners, memo=_memo,
        )
        result.full_hash_bytes = _full_bytes
        _agents_h = agents.state_hash()
        result.checkpoints.append(
            Checkpoint(
                tick, _agents_h, world.state_hash(),
                schedule.population_hash,
                schedule_hash,
                _act_hash,
                behavior_hash=SIO.behavior_state_hash(
                    agents, world, schedule.population_hash, schedule_hash, _act_hash, _owners,
                    memo=_memo,
                ),
                full_hash=_full,
            )
        )
        _dt_ckpt = time.perf_counter() - t0
        phase["checkpoint"] += _dt_ckpt
        result.checkpoint_seconds.append(_dt_ckpt)
        if checkpoint_detail:  # 10d: 食い違いの場所を探す道具の材料(既定 off)
            result.checkpoint_details.append(
                {"tick": int(tick), **SIO.component_digests(agents, world, SIO.pst_now(b), _owners)}
            )
