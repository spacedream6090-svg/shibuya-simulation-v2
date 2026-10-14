"""engine.systems.body — 体の系(body・presence・plan_boundary・home_meal・activity_intent・energy_after)(第 1 期 1-0)。

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

from shibuya.agents.state import WAKE_CONDITION_CLASS
from shibuya.agents.state import WakeCondition
from shibuya.engine import resolve as R
from shibuya.engine.energy import DEFAULT_MEAL_SLEEP_DEFER
from shibuya.core.time_consts import HOURS_PER_DAY, SECONDS_PER_HOUR, SECONDS_PER_MINUTE


def sys_body(ctx: Any, b: Any) -> None:
    """body(HEAD run.py の同じ区間・文は変えない)。

    〔第 3 期 3-5〕体の自然変動の値は本人の体の層(``b.layers.body``=``engine.body.BodyModel``・持ち主 ``body``)が返す
    (腕 sweep=全員を見る・腕 reserve=TM5 の予約)。書くのは今までどおり ``resolve.advance_body``。
    """
    agents = b.soa.agents
    classical_policy = b.layers.classical
    energy_layer = b.layers.energy
    meal_sleep_defer = b.cfg.meal_sleep_defer
    tick = ctx.T
    R.advance_body(agents, tick, energy_layer, b.layers.body)
    if classical_policy is not None:  # 第2波 §2A 項 4: per_hour の門の「範囲内で起きていた分」(他の腕は no-op)
        classical_policy.accrue_awake()
    # ---- 5 段目 5a(K9 (a)): 範囲外の食事(W17 の食事行の開始・既定の時刻に域外に居る体) ----
    if energy_layer is not None and energy_layer.out_of_area is not None:
        if meal_sleep_defer == DEFAULT_MEAL_SLEEP_DEFER:
            _ea, _es, _ef = energy_layer.out_of_area.due(tick, agents.registry.transit_state)
            if _ea.size:
                R.energy_out_of_area_meal(agents, energy_layer, _ea, _es, _ef, tick)
        else:  # 第2波 §2B 項 1: 起床時に遅らせた既定の食事を含む
            _ea, _es, _ef, _ed = energy_layer.out_of_area.due_with_deferred(
                tick, agents.registry.transit_state
            )
            if _ea.size:
                R.energy_out_of_area_meal(agents, energy_layer, _ea, _es, _ef, tick, deferred=_ed)


def sys_presence(ctx: Any, b: Any) -> None:
    """presence(HEAD run.py の同じ区間・文は変えない)。"""
    from shibuya.engine import run as _RUN
    act_layer = b.layers.act_layer
    agents = b.soa.agents
    layer_counts = b.runstats.layer_counts
    phase = b.runstats.phase
    presence = b.layers.presence
    tick = ctx.T
    tick_seconds = b.cfg.tick_seconds
    _ENTRANCE_PLAN = _RUN._ENTRANCE_PLAN
    if presence is not None:
        t0 = time.perf_counter()
        _pres0 = int(presence.n_arrivals) + int(presence.n_departures)
        presence.step(tick)
        layer_counts[(tick * tick_seconds // SECONDS_PER_HOUR) % HOURS_PER_DAY, 0, _ENTRANCE_PLAN] += (
            int(presence.n_arrivals) + int(presence.n_departures) - _pres0
        )
        # 9a: 歩いて乗る退出の体の活動=目的地つき移動・到着まで(段 2c の意図と同じ形)
        if act_layer is not None and presence.walk_started_now.size:
            act_layer.force_arrival(agents, presence.walk_started_now, tick, count=False)
        phase["presence"] += time.perf_counter() - t0


def sys_plan_boundary(ctx: Any, b: Any) -> None:
    """plan_boundary(HEAD run.py の同じ区間・文は変えない)。"""
    from shibuya.engine import run as _RUN
    agents = b.soa.agents
    layer_counts = b.runstats.layer_counts
    phase = b.runstats.phase
    plan_sleep = b.cfg.plan_sleep
    presence = b.layers.presence
    schedule = b.fx.schedule
    sleep_counts = b.runstats.sleep_tally
    td = ctx.td
    tick = ctx.T
    tick_seconds = b.cfg.tick_seconds
    world = b.soa.world
    _ENTRANCE_PLAN = _RUN._ENTRANCE_PLAN
    lo, hi = int(b.day.b_start[td]), int(b.day.b_start[td + 1])  # 10a: 日の中の刻みで引く
    if hi > lo:
        p_agent = b.day.b_agent[lo:hi]
        p_cond = b.day.b_cond[lo:hi]
        # ---- D-62 (a): 就寝境界は**エンジンが実行する**(LLM を呼ばない) ----
        # 非就寝の境界は逆に「起こしてから呼ぶ」(呼が繰り延べ・抑止で落ちても起きる)。
        if plan_sleep:
            to_bed = p_cond == int(WakeCondition.PLAN_SLEEPING)
            # 5b 層の記録: 就寝境界はエンジンが実行する(System 1=予定で呼ばない)
            layer_counts[(tick * tick_seconds // SECONDS_PER_HOUR) % HOURS_PER_DAY, 0, _ENTRANCE_PLAN] += int(
                np.count_nonzero(to_bed)
            )
            if presence is not None:
                # **D-66**: 発火元は計画実行層(同じ位置・同じ resolve の口)。
                # 就寝地の既定は層が持つ ``home_cell``(域外常住は −1 のまま=職場で寝ない)。
                t0 = time.perf_counter()
                presence.step_plan_boundaries(tick)
                phase["presence"] += time.perf_counter() - t0
                if to_bed.any():
                    p_agent = p_agent[~to_bed]
                    p_cond = p_cond[~to_bed]
            else:
                if to_bed.any():
                    got = R.begin_planned_sleep(
                        agents, world, p_agent[to_bed], b.day.b_cell[lo:hi][to_bed], tick,
                        schedule=schedule,
                    )
                    for k, v in got.items():
                        sleep_counts[k] = sleep_counts.get(k, 0) + int(v)
                    p_agent = p_agent[~to_bed]
                    p_cond = p_cond[~to_bed]
                if p_agent.size:
                    sleep_counts["woke"] = sleep_counts.get("woke", 0) + R.wake_from_plan(
                        agents, p_agent
                    )
        p_class = np.fromiter(
            (int(WAKE_CONDITION_CLASS[int(c)]) for c in p_cond),
            dtype=np.int64,
            count=p_cond.size,
        )
    else:
        p_agent = np.empty(0, dtype=np.int64)
        p_cond = np.empty(0, dtype=np.int8)
        p_class = np.empty(0, dtype=np.int64)
    b.scratch.p_agent = p_agent
    b.scratch.p_cond = p_cond
    b.scratch.p_class = p_class


def sys_home_meal(ctx: Any, b: Any) -> None:
    """home_meal(HEAD run.py の同じ区間・文は変えない)。"""
    agents = b.soa.agents
    energy_layer = b.layers.energy
    tick = ctx.T
    if energy_layer is not None and energy_layer.home_meals is not None:
        _hr = agents.registry
        _ha, _hs = energy_layer.home_meals.due(tick, _hr.transit_state, _hr.cell, _hr.activity)
        if _ha.size:
            R.energy_home_meal(agents, energy_layer, _ha, _hs, tick)


def sys_energy_after(ctx: Any, b: Any) -> None:
    """energy_after(HEAD run.py の同じ区間・文は変えない)。"""
    agents = b.soa.agents
    energy_layer = b.layers.energy
    tick = ctx.T
    tick_seconds = b.cfg.tick_seconds
    if energy_layer is not None:
        energy_layer.after_tick(agents, tick, int(tick * tick_seconds // SECONDS_PER_MINUTE))


def sys_activity_intent(ctx: Any, b: Any) -> None:
    """activity_intent(HEAD run.py の同じ区間・文は変えない)。"""
    act_layer = b.layers.act_layer
    agents = b.soa.agents
    applied_activity = b.scratch.applied_activity
    conv = b.layers.conv
    intent_layer = b.layers.intent_layer
    tick = ctx.T
    if act_layer is not None:
        if applied_activity[0]:
            act_layer.after_resolve(agents, tick, *applied_activity)
        act_layer.settle_events(agents, tick, conv)
        if intent_layer is not None:
            # 段 2c: 実行した意図の結果・意図を立てる・掃除(TOO_FAR・計画境界)
            intent_layer.after_apply(
                agents, tick, act_layer, applied_activity if applied_activity[0] else None
            )
