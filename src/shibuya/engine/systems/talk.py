"""engine.systems.talk — 会話の系(relations_wake・conversation)(第 1 期 1-0)。

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

from shibuya.agents.state import Activity
from shibuya.agents.state import ResultCode
from shibuya.agents.state import WakeCondition
from shibuya.engine import commit as C
from shibuya.engine import resolve as R


def sys_relations_wake(ctx: Any, b: Any) -> None:
    """relations_wake(HEAD run.py の同じ区間・文は変えない)。"""
    agents = b.soa.agents
    e_agent = b.scratch.e_agent
    e_class = b.scratch.e_class
    e_cond = b.scratch.e_cond
    n_agents = b.cfg.n_agents
    outside_suppression = b.cfg.outside_suppression
    plan_exec_on = b.cfg.plan_exec_on
    rel_layer = b.layers.rel_layer
    sleep_suppression = b.cfg.sleep_suppression
    tick = ctx.T
    a_agent = None
    # 第 2 期 2-2 段 11a: 腕 --proximity distance のときだけ規則を渡す(同席=届く辺・知人出現=気づく確率)
    _pkw = {} if b.layers.proximity is None else {"proximity": b.layers.proximity.rule}
    if rel_layer is not None and (rel_layer.copresent_on or rel_layer.acq_wake_on):
        t0 = time.perf_counter()
        if rel_layer.copresent_on:
            rel_layer.copresent_step(agents, tick, **_pkw)
        if rel_layer.acq_wake_on:
            _elig = np.ones(n_agents, dtype=bool)
            if sleep_suppression:
                _elig &= np.asarray(agents.registry.activity) != int(Activity.SLEEPING)
            if outside_suppression and plan_exec_on:
                _elig &= np.asarray(agents.registry.transit_state) == 0
            a_agent, a_cond, a_class = rel_layer.acquaintance_candidates(agents, tick, _elig, **_pkw)
            if a_agent.size:
                rel_layer.stats["acq_agent_refractory"] += int(np.count_nonzero(
                    np.asarray(agents.registry.refractory_until)[a_agent, int(WakeCondition.ACQUAINTANCE)]
                    > int(tick)
                ))
        rel_layer.wall["detect"] += time.perf_counter() - t0
    if a_agent is not None and a_agent.size:
        e_agent = np.concatenate([e_agent, a_agent])
        e_cond = np.concatenate([e_cond, a_cond.astype(e_cond.dtype)])
        e_class = np.concatenate([e_class, a_class.astype(e_class.dtype)])
    b.scratch.e_agent = e_agent
    b.scratch.e_cond = e_cond
    b.scratch.e_class = e_class


def sys_conversation(ctx: Any, b: Any) -> None:
    """conversation(HEAD run.py の同じ区間・文は変えない)。"""
    agents = b.soa.agents
    applied_now = b.scratch.applied_now
    attention_on = b.cfg.attention_on
    conv = b.layers.conv
    leave_effect = b.cfg.leave_effect
    outcome = b.scratch.outcome
    plan = b.scratch.plan
    rel_layer = b.layers.rel_layer
    tick = ctx.T
    # 第 2 期 2-2 段 11a: 腕 --proximity distance の判定の規則(〔2-4 V2〕既定。切替口 cell は None=同じセル)
    prox_rule = None if b.layers.proximity is None else b.layers.proximity.rule
    # 第 2 期 2-3: 体の出来事の口(腕 --memory-store events と記録のあるランだけ・既定 None=今のまま)
    _mem = b.layers.mem_layer
    body_events = getattr(getattr(_mem, "memory_store", None), "body_events", None) if _mem is not None else None
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

        # ---- 9a(D-112 ④): 退去した会話中の体のセッションを閉じる(理由「退去」→ CLOSING → TERMINAL) ----
        if leave_effect and outcome.leave_conversing:
            for _lv in np.unique(np.concatenate(outcome.leave_conversing)).tolist():
                # 逐次ループ宣言: この刻みに退去した会話中の体の数ぶん(≤ 1 刻みの呼数)
                if conv.close_now(int(_lv), tick, "退去") is not None:
                    b.runstats.leave_closed += 1

        # ---- ② 新しい招待(resolve が通した 会話 を入口にする) ----
        talk = np.flatnonzero(plan.confirmed.action_code == C.ACT_TALK)
        if talk.size:
            inviters = plan.confirmed.agent_id[talk].astype(np.int64)
            invitees = plan.confirmed.target_id[talk].astype(np.int64)
            # 逐次ループ宣言3b: 会話成立数ぶん(≤ 1 刻みの呼数)。個体数に比例しない。
            for j in range(inviters.size):
                inviter = int(inviters[j])
                invitee = int(invitees[j])
                if invitee < 0 or invitee >= agents.n:
                    _revert(inviter)
                    continue
                if int(act_now[inviter]) != int(Activity.CONVERSING):
                    # C10 8a(D-93 (d)): 相手が会話中(PARTNER_BUSY)で、そのセッションに空きがあれば加わる
                    if (
                        conv.max_participants > 2
                        and int(agents.registry.last_result[inviter]) == int(ResultCode.PARTNER_BUSY)
                        and int(act_now[invitee]) == int(Activity.CONVERSING)
                        and not conv.is_busy(inviter)
                    ):
                        s_join = conv.session_of(invitee)
                        if s_join is not None and bool(R.talk_within_reach(
                            agents, np.int64(inviter), np.int64(invitee), by_distance=attention_on,
                            rule=prox_rule,
                        )) and conv.join(s_join, inviter, tick):
                            R.join_conversation(agents, np.array([inviter]), np.array([invitee]), tick)
                    continue  # resolve が失敗させた(相手が会話中/去った)
                same_cell = bool(
                    R.talk_within_reach(
                        agents,
                        np.int64(inviter),
                        np.int64(invitee),
                        by_distance=attention_on,
                        rule=prox_rule,
                    )
                )
                b_code, b_named = applied_now.get(invitee, (-1, -1))
                # C10 8b: 招待の起点(招待/偶然/知人出現)=commit の選び手が控えた値(関係 on のランだけ)
                origin = rel_layer.pop_origin(inviter) if rel_layer is not None else -1
                # **相互指名**= 相手も自分の呼で**こちらを名指しして** 会話 と答えた。
                # (エンジンが解決した対象ではなく LLM が書いた対象で見る=中-2)
                mutual = b_code == C.ACT_TALK and b_named == inviter
                if mutual and conv.invite_blocked_by_refractory(inviter, invitee, tick):
                    conv.n_invite_refractory_blocked += 1  # 軽-5: 相互指名も不応期の対象
                    conv.note_origin(origin, "rejected")
                    _revert(inviter)
                    continue
                if mutual:
                    # その場で成立。相手の意思は相手自身の呼に出ているので抽選は引かない。
                    conv.n_invites += 1
                    conv.note_origin(origin, "invites")
                    conv.stamp_invite_refractory(inviter, invitee, tick)
                    opened = conv.invite(
                        inviter, invitee, tick, int(cell_now[inviter]),
                        same_cell=same_cell, partner_idle=True, answered=True,
                    )
                    if opened is None:
                        conv.note_origin(origin, "rejected")
                        _revert(inviter)  # 内訳は ``conv.invite`` が数える
                    else:
                        conv.n_accepted += 1
                        conv.note_origin(origin, "accepted")
                        opened.origin = int(origin)
                        R.set_conversing(
                            agents,
                            np.array([inviter], dtype=np.int64),
                            np.array([invitee], dtype=np.int64),
                        )
                else:
                    # 相手はまだ**招待を見ていない**(この刻みの相手の応答は
                    # 招待の載っていないプロンプトへの答え)→ **次の刻みに被招待で
                    # 起こして本人に答えさせる**(知覚契約書 §6 起床(ii))。
                    # 招待側は CONVERSING のまま待つ。
                    if not conv.register_pending(
                        inviter, invitee, tick, int(cell_now[inviter]),
                        same_cell=same_cell, origin=origin,
                    ):
                        conv.note_origin(origin, "rejected")
                        _revert(inviter)
                    else:
                        conv.note_origin(origin, "invites")

        # ---- ③ 期限切れの返事待ち(「無視された」=呼を消費しない) ----
        for stale in conv.expire_pending(tick):
            _revert(stale)
        if rel_layer is not None:
            rel_layer.origin_of.clear()  # C10 8b: この刻みの起点の控えを捨てる(招待に使わなかった行)
        if reverted:
            R.revert_conversation(agents, np.array(sorted(set(reverted)), dtype=np.int64))
        finished = conv.step(
            tick,
            cell=agents.registry.cell,
            # C9b G7: 離脱は**実距離 3 m**(成立 2 m より広い=ヒステリシス)。
            xy=agents.registry.xy if attention_on else None,
            leave_distance_m=R.TALK_LEAVE_METERS if attention_on else None,
            # 第 2 期 2-2: 腕 distance の離脱=同じ層・距離 ≤ d+1 m、または同じ B5 の単位(既定 None=今のまま)
            near_fn=None if prox_rule is None else (lambda a_, b_: prox_rule.stay(agents, a_, b_)),
        )
        if finished and body_events is not None:
            # 第 2 期 2-3: 会話の終わり(参加者ごとに 1 行・原因=過程 conversation)を出来事の記録へ(腕のランだけ)
            body_events.conversation_end(finished, cell_now)
        if finished:
            # 終了したセッションの参加者を解放する(行動契約書 §3「終了はエンジン」)。
            # C3 では CLOSING→TERMINAL のあと ``activity`` が CONVERSING のまま残っていた
            # (退去でしか解けなかった)=会話状態の取り残し。書き手は resolve。
            done = np.array(
                sorted({int(p) for s in finished for p in s.participants}), dtype=np.int64
            )
            R.revert_conversation(agents, done)
        conv.purge_terminal()
        conv.purge_expired(tick)  # 10e(E2): 期限の切れた不応期・拒否の控えを落とす(挙動は不変・有界化)
