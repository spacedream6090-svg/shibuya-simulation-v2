"""9a: 退出を歩かせる(D-115 ①・``--exit-mode walk_to_platform``)+退去の効果(D-112 ④)。

正典: ``docs/design/v2-presence-shape-implementation-agenda.md`` §1(9a の 1〜6)。
- 歩いて乗る退出: DEPART でその体の路線のホームへ乗車の意図(D-51 ``board_line``)→ 着けば受容関数で乗る
- 会話中は繰り延べ・買物/列は解いてから・非鉄道ゲートは即時・上限超過(TOO_FAR)と意図が落ちたら即時
- 列車で出た計画の退出は LLM の乗車と分ける(帰りの便を付けない・張り直さない)
- 歩いている体は場所の変化・到着満了・計画境界で起こさない・待機/なしで歩みを止めない
- 退去=所属解除(在店・列・会話)・活動欄「なし」なら次の tick に満了・切替口 ``leave_effect``
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.agents.state import Activity, AgentState, ResultCode, WakeCondition
from shibuya.engine import resolve as R
from shibuya.engine.presence import EXIT_WALK_MAX_TICKS, PlanExecutor
from shibuya.engine.processes.rail import RailProcess

from .test_presence_executor import (
    ACT_WORK,
    PK_WORK,
    WORLD_DIR,
    census,
    fake_assets,
    make_weekly,
    make_world_agents,
    real_data,
)


def walk_layer(weekly, *, n: int, home_cell, direction=None, ticks: int = 1_440, departures=(300, 360, 420, 480)):
    w, a = make_world_agents(n, home_cell=home_cell)
    pa = fake_assets(departures=departures)
    rail = RailProcess(w, a, pa, master_seed=1, day_index=0, plan_executor=True)
    layer = PlanExecutor(
        w, a, weekly, day_index=0, home_cell=home_cell,
        direction_node=np.zeros(n, dtype=np.int64) if direction is None else direction,
        kind=np.zeros(n, dtype=np.int64), agent_id=np.arange(n, dtype=np.int64), rail=rail, assets=pa,
        ticks=ticks, exit_mode="walk_to_platform",
    )
    rail.presence = layer
    return w, a, rail, layer


# ================================================================= (a) 歩き出し
def test_walk_mode_is_accepted_and_board_intent_stays_reserved():
    wk = make_weekly([(0, 0, 100, ACT_WORK, PK_WORK, 3)], 1)
    w, a = make_world_agents(1)
    with pytest.raises(NotImplementedError):
        PlanExecutor(w, a, wk, home_cell=np.array([-1]), exit_mode="board_intent")
    lay = PlanExecutor(w, a, wk, home_cell=np.array([-1]), exit_mode="walk_to_platform")
    assert lay.exit_mode == "walk_to_platform" and lay.walk_max_ticks == EXIT_WALK_MAX_TICKS == 60


def test_depart_walks_to_the_line_platform_instead_of_vanishing():
    rows = [(0, 0, 330, ACT_WORK, PK_WORK, 3), (1, 0, 330, ACT_WORK, PK_WORK, 0), (2, 0, 330, ACT_WORK, PK_WORK, 3)]
    wk = make_weekly(rows, 3)
    home = np.array([-1, -1, -1])
    direction = np.array([0, 0, 1])                       # 体 2 は非鉄道ゲート(線 −1)
    w, a, rail, layer = walk_layer(wk, n=3, home_cell=home, direction=direction)
    layer.initialize()
    with a.writable():
        a.registry.cell[:] = np.array([3, 0, 3])
        a.registry.node[:] = w.assets.cell_rep_node[np.array([3, 0, 3])]
        a.registry.poi_ref[0] = 2
        a.registry.activity[0] = int(Activity.SHOPPING)
    layer.step(330)
    r = a.registry
    assert census(a) == (2, 0, 1)                         # ゲートの体 2 だけ即時に出る
    assert layer.n_exit_gate_immediate == 1 and layer.n_exit_walk_started == 2
    assert int(r.board_line[0]) == 0 and int(r.activity[0]) == int(Activity.MOVING)
    assert int(r.target_node[0]) == int(w.assets.cell_rep_node[0])         # 路線 0 のホーム(セル 0)
    assert int(r.poi_ref[0]) == -1 and layer.n_shopping_interrupted == 1   # 買物は解いてから歩く
    assert int(r.activity[1]) == int(Activity.WAITING) and int(r.board_since[1]) == 330   # ホームに居た=待ちへ
    assert layer.n_exit_walk_waiting_at_start == 1
    assert (np.asarray(r.plan_flags)[[0, 1]] & R.EXIT_WALK_FLAG).all()
    assert set(layer.walk_started_now.tolist()) == {0, 1}
    assert layer.plan_exit_mask(np.array([0, 1, 2])).tolist() == [True, True, False]


def test_walker_boarding_then_train_departure_is_a_plan_exit_not_llm():
    wk = make_weekly([(0, 0, 330, ACT_WORK, PK_WORK, 0)], 1)
    w, a, rail, layer = walk_layer(wk, n=1, home_cell=np.array([-1]))
    layer.initialize()
    with a.writable():
        a.registry.cell[0] = 0
        a.registry.node[0] = int(w.assets.cell_rep_node[0])
    layer.step(330)
    with a.writable():                                    # 列車に乗った(受容関数は resolve の役目)
        a.registry.transit_state[0] = 1
        a.registry.board_line[0] = -1
    layer.step(335)
    assert layer.n_exit_walk_boarded == 1 and layer.walk_minutes == [5]
    before = layer.n_departed_by_llm
    layer.notify_departed_by_plan(np.array([0]), 360)
    assert layer.n_exit_walk_departed == 1 and layer.n_departed_by_llm == before
    assert not layer.plan_exit_mask(np.array([0]))[0]


def test_too_far_and_lost_intent_fall_back_to_immediate():
    rows = [(0, 0, 330, ACT_WORK, PK_WORK, 3), (1, 0, 330, ACT_WORK, PK_WORK, 3), (2, 0, 330, ACT_WORK, PK_WORK, 3)]
    wk = make_weekly(rows, 3)
    w, a, rail, layer = walk_layer(wk, n=3, home_cell=np.array([-1, -1, -1]))
    layer.initialize()
    with a.writable():
        a.registry.cell[:] = 3
        a.registry.node[:] = int(w.assets.cell_rep_node[3])
    layer.step(330)
    assert layer.n_exit_walk_started == 3
    with a.writable():
        a.registry.board_line[1] = -1                     # 運賃不足/待ちの打ち切り=エンジン側の理由
        a.registry.last_result[1] = int(ResultCode.NO_TRAIN)
        a.registry.board_line[2] = -1
        a.registry.last_result[2] = int(ResultCode.NO_TRAIN)
        a.registry.activity[2] = int(Activity.CONVERSING)  # 会話中なら繰り延べてから
    layer.step(331)
    assert census(a) == (2, 0, 1) and layer.n_exit_lost == 2 and layer.n_exit_lost_deferred == 1
    assert layer.n_exit_rewalk_queued == 0                # エンジン側の理由は歩き直さない
    with a.writable():
        a.registry.activity[2] = int(Activity.IDLE)
    layer.step(332)
    assert census(a) == (1, 0, 2)
    for t in range(333, 330 + EXIT_WALK_MAX_TICKS + 1):  # 体 0 は歩き続けて上限を超える
        with a.writable():
            a.registry.transit_state[0] = 0
        layer.step(t)
    assert census(a) == (0, 0, 3) and layer.n_exit_too_far == 1
    assert int(a.registry.board_line[0]) == -1
    assert layer.n_departures == 3                        # DEPART は歩き出しで 1 回ずつ(二重に数えない)


def test_conversing_depart_is_deferred_then_walks():
    wk = make_weekly([(0, 0, 330, ACT_WORK, PK_WORK, 3)], 1)
    w, a, rail, layer = walk_layer(wk, n=1, home_cell=np.array([-1]))
    layer.initialize()
    with a.writable():
        a.registry.cell[0] = 3
        a.registry.node[0] = int(w.assets.cell_rep_node[3])
        a.registry.activity[0] = int(Activity.CONVERSING)
    layer.step(330)
    assert layer.n_exit_deferred == 1 and layer.n_exit_walk_started == 0
    with a.writable():
        a.registry.activity[0] = int(Activity.IDLE)
    layer.step(331)
    assert layer.n_exit_walk_started == 1 and int(a.registry.board_line[0]) == 0


def test_walker_wakes_are_suppressed_but_surprises_are_not():
    lay = SimpleNamespace(exit_mode="walk_to_platform", _walk_since=np.array([5, -1, -1]),
                          _plan_rider=np.array([False, False, True]), n_walk_wakes_suppressed=0)
    agent = np.array([0, 0, 0, 0, 1, 2])
    cond = np.array([int(WakeCondition.CELL_BLOCK), int(WakeCondition.ACTIVITY_EXPIRY),
                     int(WakeCondition.PLAN_GENERAL), int(WakeCondition.INTEROCEPTION),
                     int(WakeCondition.CELL_BLOCK), int(WakeCondition.PLAN_TRANSIT)])
    cls = np.zeros(6, dtype=np.int64)
    a2, c2, _ = PlanExecutor.suppress_walker_wakes(lay, agent, cond, cls)
    assert a2.tolist() == [0, 1] and c2.tolist() == [int(WakeCondition.INTEROCEPTION), int(WakeCondition.CELL_BLOCK)]
    assert lay.n_walk_wakes_suppressed == 4
    lay.exit_mode = "immediate"
    a3, _, _ = PlanExecutor.suppress_walker_wakes(lay, agent, cond, cls)
    assert a3.size == 6                                   # 既定(immediate)は 1 件も落とさない


def test_wait_keeps_a_plan_exit_walker_moving():
    w, a = make_world_agents(2)
    with a.writable():
        a.registry.activity[:] = int(Activity.MOVING)
        a.registry.plan_flags[0] = np.int8(R.EXIT_WALK_FLAG)
    out = R.ResolveOutcome(tick=5)
    with a.writable():
        R._apply_wait(a, w, np.array([0, 1]), np.array([-1, -1]), 5, out, None)
    assert int(a.registry.activity[0]) == int(Activity.MOVING)
    assert int(a.registry.activity[1]) == int(Activity.WAITING)


# ================================================================= (b) 退去の効果
def test_leave_releases_store_queue_and_marks_conversation():
    w, a = make_world_agents(4)
    with a.writable():
        a.registry.poi_ref[0] = 2
        a.registry.activity[0] = int(Activity.SHOPPING)
        a.registry.queue_poi[1] = 3
        a.registry.queue_since[1] = 1
        a.registry.activity[2] = int(Activity.CONVERSING)
        a.registry.talk_partner[2] = 3
        a.registry.fail_streak[:] = 2
    out = R.ResolveOutcome(tick=9)
    with a.writable():
        R._apply_leave(a, w, np.array([0, 1, 2]), np.array([-1, -1, -1]), 9, out, None)
    r = a.registry
    assert int(r.poi_ref[0]) == -1 and int(r.queue_poi[1]) == -1
    assert (np.asarray(r.activity)[[0, 1, 2]] == int(Activity.IDLE)).all() and int(r.talk_partner[2]) == -1
    assert (np.asarray(r.last_result)[[0, 1, 2]] == int(ResultCode.OK)).all()
    assert (np.asarray(r.fail_streak)[[0, 1, 2]] == 0).all()           # 失敗しない行動
    assert (out.n_leave, out.n_leave_indoor, out.n_leave_queue, out.n_leave_conversing) == (3, 1, 1, 1)
    assert np.concatenate(out.leave_conversing).tolist() == [2]
    # 切替口 off=第301 以前(所属は残る)
    w2, b = make_world_agents(1)
    with b.writable():
        b.registry.poi_ref[0] = 2
    off = R.ResolveOutcome(tick=9, leave_effect=False)
    with b.writable():
        R._apply_leave(b, w2, np.array([0]), np.array([-1]), 9, off, None)
    assert int(b.registry.poi_ref[0]) == 2 and off.n_leave == 0


def test_leave_with_no_activity_expires_next_tick():
    from shibuya.engine import commit as C
    from shibuya.engine.activity import ActivityLayer, ActivityPayload
    from shibuya.llm.contract import NO_TARGET, UNTIL_DEFAULT_MINUTES, UntilKind

    from shibuya.world.state import World

    w = World.synthetic(n_cells=9, seed=1)
    a = AgentState(2, activity_columns=True)
    lay = ActivityLayer(2, w, b"s", tick_seconds=60, boundary_agent=np.zeros(0, dtype=np.int64),
                        boundary_tick=np.zeros(0, dtype=np.int64))
    none = ActivityPayload(text=NO_TARGET, until_kind=int(UntilKind.DEFAULT), until_value=UNTIL_DEFAULT_MINUTES,
                           wander=False)
    with a.writable():
        a.registry.last_result[:] = int(ResultCode.OK)
        a.registry.last_result_tick[:] = 10
    lay.after_resolve(a, 10, [0, 1], [C.ACT_LEAVE, C.ACT_WAIT], [none, none])
    until = np.asarray(a.registry.activity_until)
    assert int(until[0]) == 11 and int(until[1]) > 11 and lay.n_leave_expired == 1
    lay.leave_effect = False
    lay.after_resolve(a, 20, [0], [C.ACT_LEAVE], [none])
    assert int(np.asarray(a.registry.activity_until)[0]) > 21


# ================================================================= (c) ラン
@real_data
def test_run_walk_mode_accounts_for_every_exit_and_leave_switch_reproduces_the_old_golden():
    from shibuya import cli

    kw = dict(n_agents=1500, seed=1, world_dir=str(WORLD_DIR), vocab_version="v3")
    walk = cli.run(exit_mode="walk_to_platform", **kw)
    ex = walk.run_manifest_fields()["presence_exit"]
    assert ex["exit_mode"] == "walk_to_platform" and ex["walk_started"] > 0 and ex["walk_boarded"] > 0
    # 歩き(最初+歩き直し)の行き先の恒等式・歩き直しの行き先の恒等式(第302 Q117 (b))
    assert ex["walk_started"] + ex["rewalk_started"] == (
        ex["walk_boarded"] + ex["too_far_immediate"] + ex["intent_lost"] + ex["still_walking_at_end"]
        + ex["walk_gone_other"] + ex["walk_restarted"])
    assert ex["rewalk_queued"] == (ex["rewalk_started"] + ex["rewalk_forced_immediate"] + ex["rewalk_gone_other"]
                                   + ex["rewalk_waiting_at_end"])
    assert ex["intent_lost"] == ex["rewalk_queued"] + ex["intent_lost_immediate"] and ex["rewalk_started"] > 0
    assert ex["fare_exempt"] is True
    assert ex["walk_departed_by_train"] + ex["boarded_waiting_train_at_end"] == ex["walk_boarded"]
    assert walk.conserved
    # 第302 Q119 (b): 計画の退出=運賃なし(運賃は LLM の乗車だけ・計画の退出の乗車は分けて数える)
    from shibuya.engine.processes.rail import FARE_YEN

    pc = dict(walk.process_counters)
    assert pc["rail.boarded_plan_exit"] == ex["walk_boarded"]
    assert walk.fares_paid == int(FARE_YEN) * int(pc["rail.boarded_from_queue"])
    assert walk.money_start == walk.money_end + walk.revenue_end + walk.fares_paid
    again = cli.run(exit_mode="walk_to_platform", **kw)
    assert again.final_hash == walk.final_hash and again.llm_calls == walk.llm_calls
    imm = cli.run(**kw)
    m = imm.run_manifest_fields()
    assert m["presence_exit"]["exit_mode"] == "immediate" and m["leave_effects"]["enabled"] is True
    assert m["leave_effects"]["leave"] > 0
    old = cli.run(leave_effect=False, **kw)
    assert old.run_manifest_fields()["leave_effects"]["enabled"] is False
    assert old.final_hash != imm.final_hash                # mock v3 は退去を選ぶ=既定が動く


def test_cli_has_the_9a_flags():
    from pathlib import Path

    text = Path("src/shibuya/cli.py").read_text(encoding="utf-8")
    assert '"--leave-effect"' in text and '"walk_to_platform"' in text


def test_rewalk_once_after_an_llm_action_then_immediate():
    """第302 Q117 (b): LLM の別の行為で意図が落ちたら、その行為の後に 1 回だけ歩き直す・2 回目は即時。"""
    wk = make_weekly([(0, 0, 330, ACT_WORK, PK_WORK, 3)], 1)
    w, a, rail, layer = walk_layer(wk, n=1, home_cell=np.array([-1]))
    layer.initialize()
    with a.writable():
        a.registry.cell[0] = 3
        a.registry.node[0] = int(w.assets.cell_rep_node[3])
    layer.step(330)
    with a.writable():                                    # LLM が「購入」を選んで店に入った(意図が落ちた)
        a.registry.board_line[0] = -1
        a.registry.last_result[0] = int(ResultCode.OK)
        a.registry.poi_ref[0] = 2
        a.registry.activity[0] = int(Activity.SHOPPING)
    layer.step(331)
    assert census(a) == (1, 0, 0) and layer.n_exit_rewalk_queued == 1
    layer.step(332)                                       # まだ店の中=待つ
    assert layer.n_exit_rewalk_started == 0
    with a.writable():
        a.registry.poi_ref[0] = -1
        a.registry.activity[0] = int(Activity.IDLE)
    layer.step(333)                                       # 行為が終わった=歩き直す
    assert layer.n_exit_rewalk_started == 1 and int(a.registry.board_line[0]) == 0
    assert set(layer.walk_started_now.tolist()) == {0} and layer.n_departures == 1
    with a.writable():                                    # 2 回目の上書き=即時
        a.registry.board_line[0] = -1
        a.registry.last_result[0] = int(ResultCode.OK)
    layer.step(334)
    assert census(a) == (0, 0, 1) and layer.n_exit_lost_final == 1


def test_plan_exit_riders_do_not_pay_the_fare():
    """第302 Q119 (b): 計画の退出で歩いて乗る体は運賃を払わない・LLM の乗車は払う(分けて数える)。"""
    w, a = make_world_agents(2)
    pa = fake_assets()
    rail = RailProcess(w, a, pa, master_seed=1, day_index=0, plan_executor=True)
    with a.writable():
        a.registry.money[:] = 1_000
        a.registry.plan_flags[0] = np.int8(R.EXIT_WALK_FLAG)
    out = R.ResolveOutcome(tick=5, rail=rail)
    with a.writable():
        R._board_riders(a, w, [(0, np.array([0, 1]))], 5, out)
    m = np.asarray(a.registry.money)
    assert int(m[0]) == 1_000 and int(m[1]) == 1_000 - int(rail.fare_yen)
    assert out.fare_paid == int(rail.fare_yen)
    assert rail.n_boarded_plan_exit == 1 and rail.n_boarded_from_queue == 1
    assert (np.asarray(a.registry.transit_state) == 1).all()
