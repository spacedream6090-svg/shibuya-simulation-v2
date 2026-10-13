"""engine.systems.decide — 判断の系 decide(④ LLM の呼・会話ターンの発話)(第 1 期 1-0)。

中身は HEAD ``ee3abc7`` の ``engine/run.py`` の ``run_day`` の同じ区間のまま。系の関数は ``(ctx, b)`` を受け取り、
区間の外から来る名前を箱から結ぶ前置き(局所の割り当ての表 ``local-assignment.json`` と同じ写像)と、
tick の中の受け渡しを ``TickScratch`` へ書く後置きだけを足した(文は変えない・``box.`` は ``b.``)。
``engine.run`` で定義された補助(``_split_due`` など)は呼ぶ時に ``engine.run`` から引く(試験の差し替えが効く)。

逐次ループ宣言: 区間の中の宣言は HEAD のまま(各関数の中の注を見る)。ほかに新しい逐次ループは無い。
"""

from __future__ import annotations

import functools
import time
from typing import Any

import numpy as np

from shibuya.agents.state import N_WAKE_CONDITIONS_ALL
from shibuya.agents.state import WakeCondition
from shibuya.engine import resolve as R
from shibuya.engine.systems import llm_io as _LLM_IO
from shibuya.llm.fleet import LLMCall
from shibuya.llm.fleet import split_system_user


def sys_decide(ctx: Any, b: Any) -> None:
    """decide(HEAD run.py の同じ区間・文は変えない)。"""
    from shibuya.engine import run as _RUN
    _call_layer = b.cfg.call_layer
    _utter = functools.partial(_LLM_IO.utter, b)
    agents = b.soa.agents
    arbiter = b.layers.arbiter
    calls_by_cond = b.runstats.calls_by_cond  # np の配列への += は同じ物を書き換える(HEAD と同じ)
    bridge = b.layers.bridge
    classical_policy = b.layers.classical
    conv = b.layers.conv
    decision = b.scratch.decision
    fleet_bridge = b.layers.fleet_bridge
    fleet_deferred = b.llm.fleet_deferred
    fleet_inflight = b.llm.fleet_inflight
    fleet_waiting = b.llm.fleet_waiting
    lane = b.cfg.lane
    layer_counts = b.runstats.layer_counts
    n_parse_errors_fleet = b.scratch.n_parse_errors_fleet
    outside_now = b.scratch.outside_now
    phase = b.runstats.phase
    presence = b.layers.presence
    refractory_table = b.cfg.refractory_table
    rel_layer = b.layers.rel_layer
    replay_inbox = b.llm.replay_inbox
    result = b.runstats.result
    td = ctx.td
    tick = ctx.T
    tick_seconds = b.cfg.tick_seconds
    TIME_BUCKET_TICKS = _RUN.TIME_BUCKET_TICKS
    _ENTRANCE_OF_CONDITION = _RUN._ENTRANCE_OF_CONDITION
    _call_ref = _RUN._call_ref
    _inviter_of = _RUN._inviter_of
    _pending_extra = _RUN._pending_extra
    _target_person = _RUN._target_person
    t0 = time.perf_counter()
    sel = decision.selected
    # D-66 の監査点: **実際に発射した呼**のうち舞台に居ない体宛てだった数
    # (抑止が効いていれば 0。帰無腕では 53% 前後まで上がる=層2 指摘の実測)。
    if len(sel):
        b.runstats.n_outside_calls += int(
            np.count_nonzero(outside_now[sel.agent_id.astype(np.int64)])
        )
    n_parse_errors = 0
    if presence is not None and presence.exit_mode == "walk_to_platform" and len(sel):
        presence.note_calls(sel.agent_id)
    if rel_layer is not None and rel_layer.acq_wake_on and len(sel):
        _acq_sel = np.asarray(sel.condition, dtype=np.int64) == int(WakeCondition.ACQUAINTANCE)
        if bool(_acq_sel.any()):
            rel_layer.stamp_acquaintance(np.asarray(sel.agent_id, dtype=np.int64)[_acq_sel], tick)
    if len(sel):
        R.set_refractory(agents, sel.agent_id, sel.condition, tick, refractory_table)
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
                if classical_policy is not None:
                    classical_policy.set_call(a, cond, _inviter_of(conv, a, cond))
                res = bridge.call(
                    a, tick, cls, cond,
                    cell=int(cell[a]), activity=int(act[a]), hunger=int(hun[a]),
                    last_action=int(last_act[a]),
                    inviter=_inviter_of(conv, a, cond),
                )
                if res.deferred or res.observed_tick >= 0:
                    # 艦隊で録ったテープの再生(D-58)。本番と同じ「発射→後で届く」形に戻す。
                    if a in fleet_waiting:
                        b.runstats.n_fleet_resent += 1
                    fleet_waiting.add(a)
                    if res.deferred:
                        item = (a, cond, cls, int(sel.since_tick[i]))
                        if res.observed_tick > tick:
                            # タイムアウト等=**観測した tick** の ④′ で再投入される
                            replay_inbox.setdefault(res.observed_tick, []).append((True, item))
                        else:
                            # キュー満杯=発射のその場で判明 → 翌 tick の再投入枠へ
                            fleet_deferred.append(item)
                        continue
                    if res.observed_tick > tick:
                        replay_inbox.setdefault(res.observed_tick, []).append((False, res))
                        continue
                    fleet_waiting.discard(a)  # 同 tick で届いた=待ちにならない
                b.llm.pending.append((
                    res.t_apply, cls, a, cond, res.text, res.action_code,
                    _target_person(res.target), *_pending_extra(res), *_call_ref(res),
                ))
                if not res.format_ok:
                    n_parse_errors += 1
                if conv is not None and cond == int(WakeCondition.CONVERSATION_TURN):
                    # 会話ターンの応答は**発話ブロック**(1呼=1ブロック・§3)
                    _utter(a, tick, res.parse.action, res.parse.comment, res.parse.reason,
                           res.parse)
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
                    b.runstats.n_fleet_resent += 1
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
                        recalled_rows=tuple(getattr(rendered, "recalled_rows", ())),
                        # 10e(E5・A8・K1): テープ版 4 の列の材料
                        recalled_first_tick=tuple(getattr(rendered, "recalled_first_tick", ())),
                        recalled_kind=tuple(getattr(rendered, "recalled_kind", ())),
                        recalled_object=tuple(getattr(rendered, "recalled_object", ())),
                        acquaintance_ids=tuple(getattr(rendered, "acquaintance_ids", ())),
                        b5_text=str(getattr(rendered, "b5_text", "")),
                        b6_text=str(getattr(rendered, "b6_text", "")),
                    )
                )
            # 発射は**非ブロッキング**。返るのは「キューに入らなかった」分だけ。
            for c_ in calls:  # 10d: 出したが返っていない呼の控え
                fleet_inflight[str(c_.call_id)] = c_
            for d in fleet_bridge.submit(calls, now_tick=tick):
                fleet_inflight.pop(str(d.call.call_id), None)
                fleet_deferred.append(
                    (int(d.call.agent_id), int(d.call.condition),
                     int(d.call.wake_class), int(d.call.wake_since))
                )
        result.llm_calls += len(sel)  # L4 の呼数=**発射数**(再送も 1 呼・親決定 09-09)
        calls_by_cond += np.bincount(
            np.asarray(sel.condition, dtype=np.int64), minlength=N_WAKE_CONDITIONS_ALL
        )[:N_WAKE_CONDITIONS_ALL]
        result.calls_by_hour[(td // 60) % 24] += len(sel)  # D-56 の検証欄(10a: 日の中の tick から)
        # 5b 層の記録: 発射した呼=System 1.5(方策 classical)か 2(LLM/mock)× 起床入口
        np.add.at(
            layer_counts[(tick * tick_seconds // 3600) % 24, _call_layer],
            _ENTRANCE_OF_CONDITION[np.asarray(sel.condition, dtype=np.int64)],
            1,
        )
    # 艦隊経路の書式エラーは ④′(到着時)で数える=選抜が 0 の tick でも計上する
    n_parse_errors += n_parse_errors_fleet
    b.runstats.peak_pending = max(b.runstats.peak_pending, len(b.llm.pending))
    b.runstats.peak_backlog = max(b.runstats.peak_backlog, arbiter.n_pending())
    phase["llm"] += time.perf_counter() - t0
    b.scratch.parse_errors = n_parse_errors
