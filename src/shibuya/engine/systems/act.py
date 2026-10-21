"""engine.systems.act — 行為の解決の系(phase_a・phase_b・phase_c)(第 1 期 1-0)。

中身は HEAD ``ee3abc7`` の ``engine/run.py`` の ``run_day`` の同じ区間のまま。系の関数は ``(ctx, b)`` を受け取り、
区間の外から来る名前を箱から結ぶ前置き(局所の割り当ての表 ``local-assignment.json`` と同じ写像)と、
刻みの中の受け渡しを ``TickScratch`` へ書く後置きだけを足した(文は変えない・``box.`` は ``b.``)。
``engine.run`` で定義された補助(``_split_due`` など)は呼ぶ時に ``engine.run`` から引く(試験の差し替えが効く)。

逐次ループ宣言: 区間の中の宣言は HEAD のまま(各関数の中の注を見る)。ほかに新しい逐次ループは無い。
"""

from __future__ import annotations

import time
from typing import Any

from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.core.time_consts import HOURS_PER_DAY, SECONDS_PER_HOUR


def sys_phase_a(ctx: Any, b: Any) -> None:
    """phase_a(HEAD run.py の同じ区間・文は変えない)。"""
    from shibuya.engine import run as _RUN
    act_layer = b.layers.act_layer
    agents = b.soa.agents
    intent_layer = b.layers.intent_layer
    layer_counts = b.runstats.layer_counts
    llm_intents = b.scratch.llm_intents
    phase = b.runstats.phase
    space = b.fx.space
    tick = ctx.T
    tick_seconds = b.cfg.tick_seconds
    _ENTRANCE_EXPIRY = _RUN._ENTRANCE_EXPIRY
    t0 = time.perf_counter()
    # 二層の段 2: 「あたり」で着いた体の次の行き先(LLM 応答のある体は除く)
    wander_intents = (
        act_layer.wander_intents(agents, tick, exclude=llm_intents.agent_id)
        if act_layer is not None
        else C.IntentBatch.empty()
    )
    # 段 2c: 着いた体の意図の行為(LLM を呼ばない=System 1・この刻みに応答が来た体は除く)
    # (親決定 Q20: なし/待機/同じ行き先の移動は意図を保つ=着いた体のその応答の行は外して実行)
    if intent_layer is not None:
        arrival_intents, llm_intents = intent_layer.arrival_intents(
            agents, space, tick, llm=llm_intents
        )
        # 5b 層の記録: 着いた意図の行為はエンジンが実行する(System 1・入口=満了)
        layer_counts[(tick * tick_seconds // SECONDS_PER_HOUR) % HOURS_PER_DAY, 0, _ENTRANCE_EXPIRY] += len(
            arrival_intents
        )
    else:
        arrival_intents = C.IntentBatch.empty()
    intents = C.IntentBatch.concat(
        [llm_intents, wander_intents, arrival_intents,
         C.engine_continuations(agents, space, tick)]
        if act_layer is not None
        else [llm_intents, C.engine_continuations(agents, space, tick)]
    ).one_per_agent()
    b.runstats.peak_intents = max(b.runstats.peak_intents, len(intents))
    phase["phase_a"] += time.perf_counter() - t0
    b.scratch.intents = intents
    b.scratch.llm_intents = llm_intents


def sys_phase_b(ctx: Any, b: Any) -> None:
    """phase_b(HEAD run.py の同じ区間・文は変えない)。"""
    intents = b.scratch.intents
    phase = b.runstats.phase
    salt = b.cfg.salt
    space = b.fx.space
    tick = ctx.T
    world = b.soa.world
    t0 = time.perf_counter()
    plan = C.arbitrate_resources(
        intents, tick, salt, space, world.pois.stock, world.pois.capacity
    )
    phase["phase_b"] += time.perf_counter() - t0
    b.scratch.plan = plan


def sys_phase_c(ctx: Any, b: Any) -> None:
    """phase_c(HEAD run.py の同じ区間・文は変えない)。"""
    agents = b.soa.agents
    attention_on = b.cfg.attention_on
    energy_layer = b.layers.energy
    fam_layer = b.layers.fam_layer
    focus_request = b.buffers.focus_request
    geom = b.fx.geom
    leave_counts = b.runstats.leave_counts
    ledger = b.layers.ledger
    mem_layer = b.layers.mem_layer
    norm_meter = b.layers.norm_meter
    per_action_total = b.runstats.per_action_total
    phase = b.runstats.phase
    plan = b.scratch.plan
    proximity = b.layers.proximity  # 第 2 期 2-2: 腕 --proximity distance の層(〔2-4 V2〕既定。切替口 cell は None=同じセル)
    queue_service = b.cfg.queue_service
    report_precondition = b.cfg.report_precondition
    result = b.runstats.result
    runner = b.layers.runner
    schedule = b.fx.schedule
    tick = ctx.T
    vocab_version = b.cfg.vocab_version
    world = b.soa.world
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
        salient=None if runner is None or not runner.is_enabled("salient") else runner.salient,
        report_precondition=bool(report_precondition),
        queue_service=bool(queue_service),
        vocab_version=vocab_version,
        geometry=geom,
        focus_request=focus_request,
        talk_by_distance=attention_on,
        track_visits=(fam_layer is not None or mem_layer is not None),
        energy=energy_layer,
        track_events=mem_layer is not None,
        proximity=None if proximity is None else proximity.rule,
        seat_release_walk=(b.cfg.seat_release == "walk"),  # 〔第 2 期 2-4 V3〕既定 walk・切替口 legacy
    )
    phase["phase_c"] += time.perf_counter() - t0
    if norm_meter is not None:
        norm_meter.observe_results(tick)  # 第308 D-107 (a): 役割語の結果(読むだけ)
    phase["movement"] += outcome.movement_seconds
    phase["movement_cpu"] += outcome.movement_cpu_seconds
    b.runstats.geometry_hops += outcome.n_hops
    b.runstats.geometry_jammed += outcome.n_jammed
    result.fares_paid += outcome.fare_paid
    result.n_boarded += outcome.n_boarded
    result.n_alighted += outcome.n_alighted
    result.n_queued += outcome.n_queued
    result.n_board_waiting += outcome.n_board_waiting
    result.n_board_timeout += outcome.n_board_timeout
    result.meals += outcome.n_meals
    result.move_bad_target += outcome.n_move_bad_target
    result.move_unreachable += outcome.n_move_unreachable
    result.meal_yen += outcome.meal_yen
    # C9b(対象と注意)。腕が立っていないランでは 4 本とも 0 のまま。
    result.n_approach += outcome.n_approach
    result.n_approach_done += outcome.n_approach_done
    result.n_target_gone += outcome.n_target_gone
    result.n_focus += outcome.n_focus
    result.n_focus_lost += outcome.n_focus_lost
    result.n_talk_by_distance += outcome.n_talk_by_distance
    for _k in ("n_leave", "n_leave_indoor", "n_leave_queue", "n_leave_conversing"):  # 4 本
        leave_counts[_k] += int(getattr(outcome, _k))
    # 〔第 2 期 2-4 V3〕歩き出しで解いた在席の印の数(診断だけ・manifest の leave_effects.released_on_walk)
    leave_counts["n_seat_released_walk"] += int(outcome.n_seat_released_walk)
    result.n_report_ok += outcome.n_report_ok
    result.n_report_no_event += outcome.n_report_no_event
    result.n_served_from_queue += outcome.n_served_from_queue
    result.n_queue_closed += outcome.n_queue_closed
    # D-71 §3 J: 語ごとの使用件数(**解決後**=エンジンが適用した行動)。
    for _code, _n in outcome.per_action.items():
        per_action_total[int(_code)] = per_action_total.get(int(_code), 0) + int(_n)
    b.scratch.outcome = outcome
