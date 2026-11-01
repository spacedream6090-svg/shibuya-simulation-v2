"""engine.systems.judge — 判断の系(apply_responses・wake_sources・wake_filter・wake_assemble・arbiter)(第 1 期 1-0)。

中身は HEAD ``ee3abc7`` の ``engine/run.py`` の ``run_day`` の同じ区間のまま。系の関数は ``(ctx, b)`` を受け取り、
区間の外から来る名前を箱から結ぶ前置き(局所の割り当ての表 ``local-assignment.json`` と同じ写像)と、
刻みの中の受け渡しを ``TickScratch`` へ書く後置きだけを足した(文は変えない・``box.`` は ``b.``)。
``engine.run`` で定義された補助(``_split_due`` など)は呼ぶ時に ``engine.run`` から引く(試験の差し替えが効く)。

逐次ループ宣言: 区間の中の宣言は HEAD のまま(各関数の中の注を見る)。ほかに新しい逐次ループは無い。
"""

from __future__ import annotations

import dataclasses
import time
from typing import Any

import numpy as np

from shibuya.agents.state import Activity
from shibuya.agents.state import FOCUS_NONE
from shibuya.agents.state import WakeCondition
from shibuya.core.hashing import apply_key_array
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.arbiter import WakeCandidates
from shibuya.core.time_consts import HOURS_PER_DAY, STEPS_PER_HOUR


def sys_arbiter(ctx: Any, b: Any) -> None:
    """arbiter(HEAD run.py の同じ区間・文は変えない)。"""
    agents = b.soa.agents
    arbiter = b.layers.arbiter
    awake_sum = b.runstats.awake_sum
    awake_ticks = b.runstats.awake_ticks
    cands = b.scratch.cands
    n_agents = b.cfg.n_agents
    outside_suppression = b.cfg.outside_suppression
    phase = b.runstats.phase
    plan_exec_on = b.cfg.plan_exec_on
    sleep_suppression = b.cfg.sleep_suppression
    td = ctx.td
    tick = ctx.T
    t0 = time.perf_counter()
    asleep_now = np.asarray(agents.registry.activity) == int(Activity.SLEEPING)
    # ---- 起床率/時 の計測(D-62 の検証欄・a(h) との照合用) ----
    # 測る場所は**アービタの直前**(この刻みの候補を絞る時点の「起きている割合」)。
    _h = (td // STEPS_PER_HOUR) % HOURS_PER_DAY  # 10a: 日の中の刻みから(1 日のランでは今と同じ)
    awake_sum[_h] += n_agents - int(np.count_nonzero(asleep_now))
    awake_ticks[_h] += 1
    asleep = asleep_now if sleep_suppression else None
    # D-66 域外抑止: 舞台に居ない体(域外滞在 2 / 乗車中 1)は呼ばない
    outside_now = np.asarray(agents.registry.transit_state) != 0
    # **層が立つランだけ**効かせる(帰無腕 ``--no-plan-executor`` は現行挙動のまま=
    # rail の乱数 12% で外に居る 600 体にも従来どおり呼が出る。checkpoint 不変の約束)。
    outside_mask = outside_now if (outside_suppression and plan_exec_on) else None
    decision = arbiter.step(
        tick, cands, agents.registry.refractory_until, asleep=asleep,
        outside=outside_mask,
    )

    phase["arbiter"] += time.perf_counter() - t0
    b.scratch.outside_now = outside_now
    b.scratch.decision = decision


def sys_apply_responses(ctx: Any, b: Any) -> None:
    """apply_responses(HEAD run.py の同じ区間・文は変えない)。"""
    from shibuya.engine import run as _RUN
    act_layer = b.layers.act_layer
    agents = b.soa.agents
    attention_on = b.cfg.attention_on
    conv = b.layers.conv
    focus_request = b.buffers.focus_request
    intent_layer = b.layers.intent_layer
    norm_meter = b.layers.norm_meter
    phase = b.runstats.phase
    poi_resolver = b.layers.poi_resolver
    rel_layer = b.layers.rel_layer
    # 第 2 期 2-2 段 11a: 腕 --proximity distance の判定の規則(〔2-4 V2〕既定。切替口 cell は None=同じセル)
    prox_rule = None if b.layers.proximity is None else b.layers.proximity.rule
    salt = b.cfg.salt
    schedule = b.fx.schedule
    space = b.fx.space
    talk_stats = b.runstats.talk_stats
    tick = ctx.T
    v3_hints = b.cfg.v3_hints
    vocab_version = b.cfg.vocab_version
    world = b.soa.world
    _settle_pending_invites = _RUN._settle_pending_invites
    _split_due = _RUN._split_due
    t0 = time.perf_counter()
    llm_intents = C.IntentBatch.empty()
    n_undefined = 0
    applied_activity = ([], [], [])
    if b.llm.pending:
        due, b.llm.pending = _split_due(b.llm.pending, tick)
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
            b.runstats.n_undefined_total += n_undefined
            tgt_person = np.fromiter(
                (due[int(i)][6] for i in order), dtype=np.int64, count=order.size
            )
            # C9b: 対象ヒント(辞書 v4)と目印 POI。腕が立っていないランでは
            # 全行 0 / -1 なので ``intents_from_responses`` へは渡さない(=バイト不変)。
            tgt_hint = np.fromiter(
                (due[int(i)][7] for i in order), dtype=np.int64, count=order.size
            )
            tgt_poi = np.fromiter(
                (due[int(i)][8] for i in order), dtype=np.int64, count=order.size
            )
            agents_in_order = ag[order]
            if norm_meter is not None:
                norm_meter.observe_actions(tick, agents_in_order, codes)  # 第308 D-107 (a)(読むだけ)
            # 二層の段 2: 活動(v3 の応答だけ)と「あたり」の行き先
            payloads = [due[int(i)][9] for i in order]
            # 段 2a: 対象(``Target``)=購入/食事/並ぶの候補の絞り込みが読む
            parsed_targets = [due[int(i)][10] for i in order]
            move_dest: np.ndarray | None = None
            if act_layer is not None:
                applied_activity = (
                    agents_in_order.tolist(), codes.tolist(), payloads
                )
                wmask = np.fromiter(
                    (p is not None and p.wander for p in payloads),
                    dtype=bool, count=order.size,
                ) & (codes == C.ACT_MOVE)
                if wmask.any():
                    move_dest = np.full(order.size, -1, dtype=np.int64)
                    move_dest[wmask] = act_layer.wander_destinations(
                        agents_in_order[wmask],
                        np.asarray(agents.registry.cell)[agents_in_order[wmask]],
                        tick,
                    )
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
                conv, agents, tick, agents_in_order, codes, tgt_person, R, np,
                attention_on, **({} if prox_rule is None else {"rule": prox_rule}),
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
                school_cell=(
                    getattr(schedule, "school_cell", None)
                    if (attention_on or v3_hints)
                    else None
                ),
                target_person=tgt_person[keep],
                # 語彙 v3 は「対象: 自宅/職場/学校」の対象ヒントを運ぶ(v1/v2 は従来どおり)
                target_hint=tgt_hint[keep] if (attention_on or v3_hints) else None,
                target_poi=tgt_poi[keep] if attention_on else None,
                stats=talk_stats, run_salt=salt,
                vocab_version=vocab_version,
                move_dest=None if move_dest is None else move_dest[keep],
                targets=[t for t, k in zip(parsed_targets, keep.tolist()) if k],
                poi_resolver=poi_resolver,
                intent_hold=intent_layer,
                talk_chooser=rel_layer,
                **({} if prox_rule is None else {"proximity": prox_rule}),
            )
            # 〔第 2 期 2-1・検収 A1〕経済の段階 2 の腕のランだけ: 行ごとの呼の id(保留の組の call_id)と段階 2 の印
            # (口の答え=お金を下ろす・支払いの方法/LLM の答えの行為が金に触れる=購入・食事・並ぶ)を意図に付ける。
            # 金の行の原因 LlmCall(call_id) になる(既定=腕の無いランは付けない=意図の形は今のまま)。
            if _stage2_on(b) and len(llm_intents) == int(keep.sum()):
                llm_intents = _with_stage2_calls(llm_intents, due, order, codes, keep)
            elif _body_events_on(b) and len(llm_intents) == int(keep.sum()):
                # 〔第 2 期 2-3〕体の出来事の口の腕(--memory-store events+記録)のランだけ: 行ごとの呼の id だけを付ける
                # (行為の成否と会話の始まりの出来事の原因 LlmCall(call_id)・段階 2 の印は付けない=経済の腕の外は今のまま)
                llm_intents = _with_calls(llm_intents, due, order, keep)
            # ---- C9b G3/G4: 焦点の要求を 1 本のバッファへ散らす ----
            if focus_request is not None:
                focus_request[:] = int(FOCUS_NONE)
                kept_agents = agents_in_order[keep]
                if kept_agents.size:
                    focus_request[kept_agents] = C.focus_codes(
                        tgt_hint[keep], tgt_person[keep], tgt_poi[keep], int(agents.n)
                    )
        else:
            applied_now = {}
            if focus_request is not None:
                focus_request[:] = int(FOCUS_NONE)
    else:
        applied_now = {}
        if focus_request is not None:
            focus_request[:] = int(FOCUS_NONE)
    phase["phase_a"] += time.perf_counter() - t0
    b.scratch.llm_intents = llm_intents
    b.scratch.n_undefined = n_undefined
    b.scratch.applied_activity = applied_activity
    b.scratch.applied_now = applied_now


def _stage2_on(b: Any) -> bool:
    """〔2-1〕経済の段階 2 の腕を挿した台帳か(``Ledger.stage2``・腕の無いランは偽)。"""
    led = b.layers.ledger
    money = getattr(led, "money", None) if led is not None else None
    return getattr(money, "stage2", None) is not None


def _body_events_on(b: Any) -> bool:
    """〔2-3〕記憶の器に体の出来事の口を挿したランか(腕 ``--memory-store events`` と出来事の記録・既定は偽)。"""
    mem = b.layers.mem_layer
    ms = getattr(mem, "memory_store", None) if mem is not None else None
    link = getattr(ms, "body_events", None) if ms is not None else None
    return link is not None and bool(link.enabled)


def _with_calls(intents: Any, due: list, order: np.ndarray, keep: np.ndarray) -> Any:
    """〔2-3〕LLM の意図の行に呼の id(保留の組の 12 番=``run._call_ref``)だけを付ける(体の出来事の原因)。意図の形・印は
    今のまま(``s2_flags`` は付けない)。逐次ループ宣言: この刻みに適用する応答の数ぶん(≤ 1 刻みの呼数)。"""
    rows = [due[int(i)] for i in order]
    cid = np.array([r[12] if len(r) > 12 else None for r in rows], dtype=object)
    return dataclasses.replace(intents, call_id=cid[keep])


def _with_stage2_calls(intents: Any, due: list, order: np.ndarray, codes: np.ndarray, keep: np.ndarray) -> Any:
    """〔2-1・検収 A1〕LLM の意図の行に呼の id(保留の組の 12 番=``run._call_ref``)と段階 2 の印(13 番=口の答え+
    金に触れる行為の印)を付ける。逐次ループ宣言: この刻みに適用する応答の数ぶん(≤ 1 刻みの呼数)。"""
    rows = [due[int(i)] for i in order]
    cid = np.array([r[12] if len(r) > 12 else None for r in rows], dtype=object)
    flg = np.fromiter((int(r[13]) if len(r) > 13 else 0 for r in rows), dtype=np.int64, count=len(rows))
    money = np.isin(codes, (C.ACT_BUY, C.ACT_EAT, C.ACT_QUEUE))
    flg = flg | np.where(money, C.S2_MONEY_ACT, 0)
    return dataclasses.replace(intents, call_id=cid[keep], s2_flags=flg[keep].astype(np.int8))


def sys_wake_sources(ctx: Any, b: Any) -> None:
    """wake_sources(HEAD run.py の同じ区間・文は変えない)。"""
    conv = b.layers.conv
    runner = b.layers.runner
    tick = ctx.T
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
    b.scratch.c_agent = c_agent
    b.scratch.c_cond = c_cond
    b.scratch.c_class = c_class
    b.scratch.s_agent = s_agent
    b.scratch.s_cond = s_cond
    b.scratch.s_class = s_class


def sys_wake_filter(ctx: Any, b: Any) -> None:
    """wake_filter(HEAD run.py の同じ区間・文は変えない)。"""
    agents = b.soa.agents
    d_agent = b.scratch.det_agent
    d_class = b.scratch.det_class
    d_cond = b.scratch.det_cond
    e_agent = b.scratch.e_agent
    e_class = b.scratch.e_class
    e_cond = b.scratch.e_cond
    fleet_deferred = b.llm.fleet_deferred
    p_agent = b.scratch.p_agent
    p_class = b.scratch.p_class
    p_cond = b.scratch.p_cond
    presence = b.layers.presence
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
        b.runstats.n_fleet_reinjected += len(fleet_deferred)
        fleet_deferred.clear()
    else:
        f_agent = np.empty(0, dtype=np.int64)
        f_cond = np.empty(0, dtype=np.int8)
        f_class = np.empty(0, dtype=np.int64)
        f_since = np.empty(0, dtype=np.int64)

    # ---- 就寝抑止の例外印(D-56・ユーザー決定 (a)・09-10) ----
    # **源で決める**(条件では区別できない: 顕著行為も変化検出も ``CELL_BLOCK``)。
    # 計画境界 p / 会話 c / 顕著行為 s = 通す・変化検出 d = 落とす。
    # 艦隊の再投入 f は源を持ち帰れないので**条件**で判定する(会話ターン 0 と
    # ``PLAN_*`` 1-4 は通す)。顕著行為由来の再投入は ``CELL_BLOCK`` なので
    # 就寝中なら落ちる(**過剰抑止をここに明記**・実害は「答えの返らなかった呼を
    # 寝ている間は蒸し返さない」だけ)。
    f_exempt = f_cond.astype(np.int64) <= int(WakeCondition.PLAN_TRANSIT)

    # ---- 9a: 歩いて乗る退出の体は場所の変化・到着満了・計画境界で起こさない(意図保持と同じ・既定は通らない) ----
    # 〔第 6 期 6-2〕カレンダー 1b の口のあるラン(腕 --calendar 1b)でも、本人が決めた出入りの歩きの途中の体に同じ扱い
    if presence is not None and (presence.exit_mode == "walk_to_platform"
                                 or getattr(presence, "io_hook", None) is not None):
        d_agent, d_cond, d_class = presence.suppress_walker_wakes(d_agent, d_cond, d_class)
        p_agent, p_cond, p_class = presence.suppress_walker_wakes(p_agent, p_cond, p_class)
        e_agent, e_cond, e_class = presence.suppress_walker_wakes(e_agent, e_cond, e_class)
    b.scratch.f_agent = f_agent
    b.scratch.f_cond = f_cond
    b.scratch.f_class = f_class
    b.scratch.f_since = f_since
    b.scratch.f_exempt = f_exempt
    b.scratch.det_agent = d_agent
    b.scratch.det_cond = d_cond
    b.scratch.det_class = d_class
    b.scratch.e_agent = e_agent
    b.scratch.e_cond = e_cond
    b.scratch.e_class = e_class
    b.scratch.p_agent = p_agent
    b.scratch.p_cond = p_cond
    b.scratch.p_class = p_class


def sys_wake_assemble(ctx: Any, b: Any) -> None:
    """wake_assemble(HEAD run.py の同じ区間・文は変えない)。"""
    c_agent = b.scratch.c_agent
    c_class = b.scratch.c_class
    c_cond = b.scratch.c_cond
    d_agent = b.scratch.det_agent
    d_class = b.scratch.det_class
    d_cond = b.scratch.det_cond
    e_agent = b.scratch.e_agent
    e_class = b.scratch.e_class
    e_cond = b.scratch.e_cond
    f_agent = b.scratch.f_agent
    f_class = b.scratch.f_class
    f_cond = b.scratch.f_cond
    f_exempt = b.scratch.f_exempt
    f_since = b.scratch.f_since
    p_agent = b.scratch.p_agent
    p_class = b.scratch.p_class
    p_cond = b.scratch.p_cond
    s_agent = b.scratch.s_agent
    s_class = b.scratch.s_class
    s_cond = b.scratch.s_cond
    tick = ctx.T
    cands = WakeCandidates(
        np.concatenate([p_agent, d_agent, c_agent, s_agent, f_agent, e_agent]),
        np.concatenate(
            [p_cond, d_cond.astype(np.int8), c_cond, s_cond, f_cond, e_cond]
        ),
        np.concatenate([p_class, d_class, c_class, s_class, f_class, e_class]),
        np.concatenate(
            [
                np.full(
                    p_agent.size + d_agent.size + c_agent.size + s_agent.size,
                    tick, dtype=np.int64,
                ),
                f_since,  # 再投入は**元の待ち始め**を保つ(昇格が巻き戻らない)
                np.full(e_agent.size, tick, dtype=np.int64),  # 満了入口(二層の段 2)
            ]
        ),
        np.concatenate(
            [
                np.ones(p_agent.size, dtype=bool),    # 計画境界(眠りから覚める境界を含む)
                np.zeros(d_agent.size, dtype=bool),   # 変化検出(内受容・セル変化)
                np.ones(c_agent.size, dtype=bool),    # 会話ターン
                np.ones(s_agent.size, dtype=bool),    # 顕著行為
                f_exempt,                             # 艦隊の再投入
                np.zeros(e_agent.size, dtype=bool),   # 満了入口(就寝中は起こさない)
            ]
        ),
    )
    b.scratch.cands = cands
