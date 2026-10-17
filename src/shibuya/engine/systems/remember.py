"""engine.systems.remember — 記憶の系(memory・familiarity)(第 1 期 1-0)。

中身は HEAD ``ee3abc7`` の ``engine/run.py`` の ``run_day`` の同じ区間のまま。系の関数は ``(ctx, b)`` を受け取り、
区間の外から来る名前を箱から結ぶ前置き(局所の割り当ての表 ``local-assignment.json`` と同じ写像)と、
刻みの中の受け渡しを ``TickScratch`` へ書く後置きだけを足した(文は変えない・``box.`` は ``b.``)。
``engine.run`` で定義された補助(``_split_due`` など)は呼ぶ時に ``engine.run`` から引く(試験の差し替えが効く)。

逐次ループ宣言: 区間の中の宣言は HEAD のまま(各関数の中の注を見る)。ほかに新しい逐次ループは無い。
"""

from __future__ import annotations

from typing import Any


def sys_memory(ctx: Any, b: Any) -> None:
    """memory(HEAD run.py の同じ区間・文は変えない)。"""
    _fam_renderer = b.layers.renderer
    agents = b.soa.agents
    conv = b.layers.conv
    fam_layer = b.layers.fam_layer
    mem_layer = b.layers.mem_layer
    outcome = b.scratch.outcome
    plan = b.scratch.plan
    runner = b.layers.runner
    tick = ctx.T
    _exp = None
    if (fam_layer is not None or mem_layer is not None) and _fam_renderer is not None and getattr(
        _fam_renderer, "signage_exposures", None
    ):
        _exp = list(_fam_renderer.signage_exposures)
        _fam_renderer.signage_exposures.clear()
    # ---- 6 段目 6a: 記憶の記録(行動の成否・会話・気づき・強い看板)。親しみの表の**前**
    # (看板の初見=親しみの表にまだその POI の行が無い、をこの刻みの書き込みの前に見る) ----
    if mem_layer is not None:
        mem_layer.after_tick(
            agents, tick,
            applied=(
                (plan.confirmed.agent_id, plan.confirmed.target_id),
                (plan.losers.agent_id, plan.losers.target_id),
            ),
            visits=(outcome.visit_agents, outcome.visit_pois),
            arrived=outcome.arrived_agents,
            conv=conv,
            salient_events=(
                getattr(runner.salient, "events", ())
                if (runner is not None and runner.is_enabled("salient"))
                else ()
            ),
            signage=_exp,
            # 第 2 期 2-3: この刻みに適用した意図の呼の id(体の出来事の口のあるランだけ読む=行為の成否・会話の始まりの原因)
            calls=(
                (plan.confirmed.agent_id, plan.confirmed.call_id),
                (plan.losers.agent_id, plan.losers.call_id),
            ),
        )
    b.scratch.exposures = _exp


def sys_familiarity(ctx: Any, b: Any) -> None:
    """familiarity(HEAD run.py の同じ区間・文は変えない)。"""
    _exp = b.scratch.exposures
    agents = b.soa.agents
    fam_layer = b.layers.fam_layer
    outcome = b.scratch.outcome
    tick = ctx.T
    if fam_layer is not None:
        fam_layer.after_tick(
            agents, tick, (outcome.visit_agents, outcome.visit_pois), _exp
        )
