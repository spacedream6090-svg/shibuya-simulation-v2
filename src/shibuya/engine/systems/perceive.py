"""engine.systems.perceive — 知覚の系(perceive_prepare・detect)(第 1 期 1-0)。

中身は HEAD ``ee3abc7`` の ``engine/run.py`` の ``run_day`` の同じ区間のまま。系の関数は ``(ctx, b)`` を受け取り、
区間の外から来る名前を箱から結ぶ前置き(局所の割り当ての表 ``local-assignment.json`` と同じ写像)と、
刻みの中の受け渡しを ``TickScratch`` へ書く後置きだけを足した(文は変えない・``box.`` は ``b.``)。
``engine.run`` で定義された補助(``_split_due`` など)は呼ぶ時に ``engine.run`` から引く(試験の差し替えが効く)。

逐次ループ宣言: 区間の中の宣言は HEAD のまま(各関数の中の注を見る)。ほかに新しい逐次ループは無い。
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from shibuya.engine import resolve as R


def sys_perceive_prepare(ctx: Any, b: Any) -> None:
    """perceive_prepare(HEAD run.py の同じ区間・文は変えない)。"""
    act_layer = b.layers.act_layer
    agents = b.soa.agents
    perception = b.fx.perception
    runner = b.layers.runner
    tick = ctx.T
    tick_seconds = b.cfg.tick_seconds
    world = b.soa.world
    field_rows = None
    # 第 2 期 2-2 段 11a: 腕 --proximity distance のときだけ、この刻みの近傍の索引を作る(刻みの頭で捨てる=
    # ``TickScratch.near_index``・状態台帳の行 PX0)。B5 の近接行は描画の前計算に渡す(既定の腕 cell では作らない=None)
    proximity = b.layers.proximity
    near_index = None if proximity is None else proximity.build_index(agents)
    if perception is not None:
        perception.prepare_tick(
            tick,
            salient_events=None if runner is None else runner.salient_events,
            flow=None if runner is None else runner.flow,
            noise_stage=world.noise_stage_for_tick(tick, tick_seconds),
            queues=None if runner is None else runner.queue_rows(3),
            # 二層の段 2: 同セルの活動の 1 行の材料(層が無いランでは渡さない=バイト不変)
            **(
                {"activity_rows": act_layer.cell_rows(agents, tick)}
                if act_layer is not None
                else {}
            ),
            **({} if near_index is None else {"near": proximity.view(agents, near_index)}),
            # 〔段 5-1b〕nav1 のランは B4 の密度の段を位置の確定で書いた段(NavSpace.per_m2 の推定)から=密度を 1 つに
            **({"los_stage": world.cells.density_stage} if getattr(b.fx.geom, "is_nav", False) else {}),
        )
        field_rows = perception.b4_field_rows
    b.scratch.field_rows = field_rows
    b.scratch.near_index = near_index


def sys_detect(ctx: Any, b: Any) -> None:
    """detect(HEAD run.py の同じ区間・文は変えない)。"""
    from shibuya.engine import run as _RUN
    act_layer = b.layers.act_layer
    agents = b.soa.agents
    detector = b.layers.detector
    field_rows = b.scratch.field_rows
    intent_layer = b.layers.intent_layer
    intero_cross = b.runstats.intero_cross
    phase = b.runstats.phase
    tick = ctx.T
    world = b.soa.world
    _count_intero_crossings = _RUN._count_intero_crossings
    t0 = time.perf_counter()
    step_scope = getattr(b.layers, "step_scope", None)  # 〔第 6 期 6-3 T3〕腕 --step-scope changed のランだけ(既定 None=全員を毎回見る版)
    if step_scope is None:
        det = detector.detect(world, agents, tick, field_rows=field_rows)
    else:  # 内受容の段の跨ぎは変化の印の体だけ(結果は全員を見る版と同じ)
        det = step_scope.detect(detector, world, agents, tick, field_rows=field_rows)
    _count_intero_crossings(det, agents, intero_cross)
    R.apply_detection(agents, world, det)
    if step_scope is not None:
        step_scope.after_detection(agents, det)
    d_agent, d_cond, d_class = det.candidates()
    # ---- 二層の段 2: 活動中は場所の変化で起こさない+満了入口 ----
    if act_layer is not None:
        if intent_layer is not None:
            # 段 2c: 意図を持つ体(歩いている・着いた)は場所の変化で起こさない(件数を数える)
            d_agent, d_cond, d_class = intent_layer.suppress_wakes(
                agents, tick, d_agent, d_cond, d_class
            )
        d_agent, d_cond, d_class = act_layer.suppress_cell_block(
            agents, tick, d_agent, d_cond, d_class
        )
        e_agent, e_cond, e_class = act_layer.expiry_candidates(agents, tick)
        if intent_layer is not None:
            # 段 2c: 着いた体の到着満了は LLM を呼ばない(エンジンが意図の行為を実行する)
            e_agent, e_cond, e_class = intent_layer.suppress_wakes(
                agents, tick, e_agent, e_cond, e_class
            )
    else:
        e_agent = np.empty(0, dtype=np.int64)
        e_cond = np.empty(0, dtype=np.int8)
        e_class = np.empty(0, dtype=np.int64)
    phase["detect"] += time.perf_counter() - t0
    b.scratch.det_agent = d_agent
    b.scratch.det_cond = d_cond
    b.scratch.det_class = d_class
    b.scratch.e_agent = e_agent
    b.scratch.e_cond = e_cond
    b.scratch.e_class = e_class
