"""段 2c(意図の保持・D-112 ①・D-114 案 A・第288): 欄・立つ条件・着いたら実行・失敗と TOO_FAR・
計画で捨てる・CELL_BLOCK の抑止・B5 の 1 行・manifest・mock の口・Q18(人 → その人のセル)・
親決定 Q20(なし/待機/同じ行き先の移動は意図と歩みを保つ)・Q21(名指しの店の営業中を立てる時点で見る)・
Q22(計画就寝の意図と排他)。

正典: ``docs/design/v2-intent-chooser-implementation-agenda.md`` §3。
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.schedule import synthesize
from shibuya.agents.state import (
    INTENT_FIELDS,
    INTENT_NONE,
    RESULT_TEXT,
    Activity,
    ActivityKind,
    AgentState,
    IntentKind,
    ResultCode,
    WakeCondition,
)
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.activity import ActivityLayer, ActivityPayload
from shibuya.engine.chooser import NearestChooser
from shibuya.engine.intent import (
    INTENT_ACTIONS,
    INTENT_MAX_TICKS,
    INTENT_MAX_TICKS_ARMS,
    IntentLayer,
    intent_summary,
)
from shibuya.engine.poi_target import MOVE_BAD_TARGET, TargetResolver, resolution_summary
from shibuya.engine.run import run_day
from shibuya.llm import LLMRequest
from shibuya.llm.contract import ACTION_CODES, UntilKind, parse_target
from shibuya.llm.mock import MockLLM
from shibuya.perception import renderer as PR
from shibuya.perception.renderer import Renderer

from tests.engine.test_move_destination import NOON, _world

SALT = b"s" * 16
WORLD_DIR = Path("data/world/v2")


# ------------------------------------------------------------------ 道具
def _setup(n=3, cells=(0, 0, 0), max_ticks=INTENT_MAX_TICKS, visible=None):
    """4 セルの小世界(test_move_destination と同じ)+ 活動層 + 意図の層。体は IDLE で ``cells`` に立つ。"""
    w = _world(visible=visible)
    ag = AgentState(n, activity_columns=True)
    sched = synthesize(n, 1, w.n_cells)
    R.initialize(ag, w, sched)
    with ag.writable():
        ag.registry.cell[:] = np.asarray(cells)
        ag.registry.node[:] = w.assets.cell_rep_node[np.asarray(cells)]
        ag.registry.activity[:] = int(Activity.IDLE)
        ag.registry.money[:] = 10_000
    ag.freeze()
    act = ActivityLayer(n, w, SALT)
    il = IntentLayer(n, w, max_ticks=max_ticks)
    space = C.ResourceSpace(w.n_poi, n, w.n_cells)
    res = TargetResolver(world=w, chooser=NearestChooser(), seed=1)
    return w, ag, act, il, space, res


def _payload(text="食事", kind=UntilKind.MINUTES, value=30):
    return ActivityPayload(text, int(kind), int(value), False)


def _tick(w, ag, act, il, space, t, llm_batch=None, applied=None):
    """1 tick ぶんの Phase A(応答+着いた体+継続)→ B → C → 活動層 → 意図の層。"""
    llm_batch = llm_batch if llm_batch is not None else C.IntentBatch.empty()
    arr, llm_batch = il.arrival_intents(ag, space, t, llm=llm_batch)
    intents = C.IntentBatch.concat(
        [llm_batch, arr, C.engine_continuations(ag, space, t)]
    ).one_per_agent()
    plan = C.arbitrate_resources(intents, t, SALT, space, w.pois.stock, w.pois.capacity)
    R.apply(plan.confirmed, plan.losers, ag, w, t, vocab_version="v3")
    if applied is not None:
        act.after_resolve(ag, t, *applied)
    act.settle_events(ag, t)
    il.after_apply(ag, t, act, applied)
    return arr


def _respond(w, ag, space, res, il, t, agent, code, target, *, home=None):
    return C.intents_from_responses(
        ag, w, space, t, np.array([agent]), np.array([3]), np.array([code]),
        home_cell=home, targets=[None if target is None else parse_target(target)],
        poi_resolver=res, intent_hold=il, vocab_version="v3", run_salt=SALT,
        target_person=np.array([-1 if target is None or not target.startswith("P-")
                                else int(target[2:])]),
    )


# ------------------------------------------------------------------ 欄・コード
def test_intent_fields_are_allocated_by_default_with_none_values_and_ten_bytes():
    a = AgentState(3)
    assert a.intent_action.tolist() == [INTENT_NONE] * 3
    assert a.intent_target.tolist() == [-1] * 3
    assert a.intent_kind.tolist() == [int(IntentKind.NONE)] * 3
    assert a.intent_since.tolist() == [-1] * 3
    rep = {f.name: f for f in a.budget_report().fields}
    assert sum(rep[n].declared_bytes_per_entity for n in INTENT_FIELDS) == 10
    # 監査口: 欄を混ぜないハッシュは欄を足す前の宣言列と同じ形
    assert a.registry.state_hash(exclude=INTENT_FIELDS) != a.registry.state_hash()


def test_too_far_is_a_new_code_with_text_and_options():
    assert int(ResultCode.TOO_FAR) == 21 and int(ResultCode.TARGET_GONE) == 20
    assert RESULT_TEXT[ResultCode.TOO_FAR] == "遠すぎて時間切れ"
    assert RESULT_TEXT[ResultCode.TOO_FAR] != RESULT_TEXT[ResultCode.UNREACHABLE]
    assert PR.RESULT_OPTIONS[ResultCode.TOO_FAR] == ("移動", "待機", "休憩")
    assert PR.RESULT_OPTIONS_V3[ResultCode.TOO_FAR] == ("移動", "なし")


def test_intent_actions_and_the_renderer_words_match_the_contract():
    assert set(INTENT_ACTIONS) == {C.ACT_BUY, C.ACT_EAT, C.ACT_QUEUE, C.ACT_TALK, C.ACT_SLEEP}
    for code, word in PR.INTENT_ACTION_WORDS.items():
        if word == "食事":
            assert code == C.ACT_EAT
        elif word == "並ぶ":
            assert code == C.ACT_QUEUE
        else:
            assert ACTION_CODES[word] == code
    assert INTENT_MAX_TICKS == 60 and INTENT_MAX_TICKS_ARMS == (30, 60, 120)


# ------------------------------------------------------------------ いつ立つか(候補の解決)
def test_resolver_named_out_of_cell_becomes_an_intent_only_when_visible_and_fit():
    w = _world(visible={0: [(4, 30)]})
    res = TargetResolver(world=w, chooser=NearestChooser(), seed=1)
    ag = _agents0(w)
    io: dict[int, tuple[int, int]] = {}
    out = res.resolve(ag, NOON, np.array([0]), np.array([C.ACT_EAT]),
                      [parse_target("カフェ・ベローチェ")], is_eat=np.array([True]),
                      is_buy_like=np.array([False]), intent_out=io)
    assert out.tolist() == [-1] and io == {0: (4, int(IntentKind.POI_NAMED))}
    # 見えない(W8 に無い)名指しは意図にならない=段 2a の失敗のまま
    w2 = _world()
    res2 = TargetResolver(world=w2, chooser=NearestChooser(), seed=1)
    io2: dict[int, tuple[int, int]] = {}
    res2.resolve(_agents0(w2), NOON, np.array([0]), np.array([C.ACT_EAT]),
                 [parse_target("カフェ・ベローチェ")], is_eat=np.array([True]),
                 is_buy_like=np.array([False]), intent_out=io2)
    s = resolution_summary(res2.stats, res2.entropy_sum)
    assert io2 == {} and s["named_out_of_cell_detail"]["not_visible"] == 1
    assert s["iv_no_candidate"]["named_out_of_cell"] == 1
    # 意図に合わない(食事なのに物販店)名指しも意図にならない
    io3: dict[int, tuple[int, int]] = {}
    res.resolve(ag, NOON, np.array([0]), np.array([C.ACT_EAT]), [parse_target("花屋C")],
                is_eat=np.array([True]), is_buy_like=np.array([False]), intent_out=io3)
    assert io3 == {} and res.stats["named_out_of_cell:not_fit"] == 1


def test_resolver_category_without_an_open_candidate_in_the_cell_searches_nearby():
    w = _world()
    res = TargetResolver(world=w, chooser=NearestChooser(), seed=1)
    io: dict[int, tuple[int, int]] = {}
    out = res.resolve(_agents0(w), NOON, np.array([0]), np.array([C.ACT_EAT]),
                      [parse_target("飲食店")], is_eat=np.array([True]),
                      is_buy_like=np.array([False]), intent_out=io)
    # セル 0 に food なし → 近い順(セル 1 の food 2=150 m)
    assert out.tolist() == [-1] and io == {0: (2, int(IntentKind.POI_CATEGORY))}
    s = resolution_summary(res.stats, res.entropy_sum)
    assert s["v_intent"] == {"named": 0, "category": 1, "category_none_nearby": 0}
    # 「なし」の対象は意図にしない(どこへ行くかを言っていない)
    io2: dict[int, tuple[int, int]] = {}
    res.resolve(_agents0(w), NOON, np.array([0]), np.array([C.ACT_EAT]), [None],
                is_eat=np.array([True]), is_buy_like=np.array([False]), intent_out=io2)
    assert io2 == {}


def test_named_visible_but_closed_returns_closed_now_without_walking_q21():
    """親決定 Q21: 立てる時点で営業中・在庫を見る。閉店なら歩かずに CLOSED を即時に。"""
    w = _world(visible={0: [(4, 30), (7, 5)]})
    with w.writable():
        w.pois.open_now[:] = 1
        w.pois.open_now[4] = 0
        w.pois.stock[7] = 0
    res = TargetResolver(world=w, chooser=NearestChooser(), seed=1)
    io: dict[int, tuple[int, int]] = {}
    out = res.resolve(_agents0(w, 2), NOON, np.arange(2), np.array([C.ACT_EAT, C.ACT_BUY]),
                      [parse_target("カフェ・ベローチェ"), parse_target("花屋C")],
                      is_eat=np.array([True, False]), is_buy_like=np.array([False, True]),
                      intent_out=io)
    assert io == {} and out.tolist() == [4, 7]  # 代表 1 件=resolve が CLOSED/OUT_OF_STOCK を付ける
    s = resolution_summary(res.stats, res.entropy_sum)
    assert s["named_out_of_cell_detail"]["closed"] == 1
    assert s["named_out_of_cell_detail"]["out_of_stock"] == 1
    assert s["iv_by_kind"]["named"]["closed"] == 1 and s["iv_by_kind"]["named"]["out_of_stock"] == 1


def test_bed_intent_is_exclusive_with_the_planned_sleep_q22():
    w, ag, act, il, space, res = _setup(n=2, cells=(0, 0))
    with ag.writable():
        ag.registry.sleep_pending[0] = 1
    b = C.intents_from_responses(
        ag, w, space, NOON, np.array([0, 1]), np.full(2, 3), np.full(2, C.ACT_SLEEP),
        home_cell=np.array([2, 2]), targets=[None, None], poi_resolver=res, intent_hold=il,
        vocab_version="v3",
    )
    # 計画就寝の意図が立っている体 0 は寝床の意図にしない(就寝のまま=NO_BED)・体 1 は自宅へ歩く
    assert b.action_code.tolist() == [C.ACT_SLEEP, C.ACT_MOVE]
    assert list(il._proposals) == [1]
    assert il.counters()["bed_skipped_sleep_pending"] == 1


def test_resolver_without_intent_out_is_unchanged():
    w = _world(visible={0: [(4, 30)]})
    a = TargetResolver(world=w, chooser=NearestChooser(), seed=1)
    b = TargetResolver(world=w, chooser=NearestChooser(), seed=1)
    tg = [parse_target("カフェ・ベローチェ"), parse_target("飲食店"), None]
    args = (_agents0(w, 3), NOON, np.arange(3), np.full(3, C.ACT_EAT), tg)
    kw = dict(is_eat=np.ones(3, dtype=bool), is_buy_like=np.zeros(3, dtype=bool))
    assert a.resolve(*args, **kw).tolist() == b.resolve(*args, **kw, intent_out=None).tolist()
    assert a.stats == b.stats


def _agents0(w, n=1):
    ag = AgentState(n)
    ag.registry.cell[:] = 0
    ag.registry.node[:] = int(w.assets.cell_rep_node[0])
    return ag


def test_commit_turns_out_of_cell_targets_into_moves_and_proposes_the_intent():
    w, ag, act, il, space, res = _setup(n=3, cells=(0, 0, 3), visible={0: [(4, 30)]})
    home = np.array([2, 0, 3])
    batch = C.intents_from_responses(
        ag, w, space, NOON, np.array([0, 1, 2]), np.full(3, 3),
        np.array([C.ACT_EAT, C.ACT_TALK, C.ACT_SLEEP]),
        home_cell=home, targets=[parse_target("カフェ・ベローチェ"), parse_target("P-2"), None],
        target_person=np.array([-1, 2, -1]),
        poi_resolver=res, intent_hold=il, vocab_version="v3", run_salt=SALT,
    )
    # 食事(名指し・見える店)→ セル 2・会話(相手 P-2 はセル 3)→ セル 3・就寝(自宅 3=今いるセル)→ そのまま
    assert batch.action_code.tolist() == [C.ACT_MOVE, C.ACT_MOVE, C.ACT_SLEEP]
    assert batch.target_id.tolist() == [2, 3, 3]
    assert batch.resource_id.tolist()[:2] == [-1, -1]
    assert il._proposals == {
        0: (C.ACT_EAT, 4, int(IntentKind.POI_NAMED), 2),
        1: (C.ACT_TALK, 2, int(IntentKind.PERSON), 3),
    }
    # 就寝: 自宅が別セル → 自宅へ
    il2 = IntentLayer(3, w)
    b2 = C.intents_from_responses(
        ag, w, space, NOON, np.array([0]), np.array([3]), np.array([C.ACT_SLEEP]),
        home_cell=np.array([2, 0, 3]), targets=[None], poi_resolver=res, intent_hold=il2,
        vocab_version="v3",
    )
    assert b2.action_code.tolist() == [C.ACT_MOVE] and b2.target_id.tolist() == [2]
    assert il2._proposals == {0: (C.ACT_SLEEP, 2, int(IntentKind.BED), 2)}
    # 意図の層が無ければ従来どおり(食事=候補 0・会話=フォールバック・就寝=自宅)
    b3 = C.intents_from_responses(
        ag, w, space, NOON, np.array([0, 1]), np.full(2, 3),
        np.array([C.ACT_EAT, C.ACT_TALK]), home_cell=home,
        targets=[parse_target("カフェ・ベローチェ"), parse_target("P-2")],
        target_person=np.array([-1, 2]), poi_resolver=res, vocab_version="v3", run_salt=SALT,
    )
    assert b3.action_code.tolist() == [C.ACT_EAT, C.ACT_TALK]


# ------------------------------------------------------------------ 着いたら実行
def test_intent_is_set_walks_arrives_and_executes_without_an_llm_call():
    w, ag, act, il, space, res = _setup(n=2, cells=(0, 0), visible={0: [(4, 30)]})
    t = NOON
    batch = _respond(w, ag, space, res, il, t, 0, C.ACT_EAT, "カフェ・ベローチェ")
    applied = ([0], [C.ACT_EAT], [_payload()])
    _tick(w, ag, act, il, space, t, batch, applied)
    r = ag.registry
    assert int(r.intent_action[0]) == C.ACT_EAT and int(r.intent_target[0]) == 4
    assert int(r.intent_kind[0]) == int(IntentKind.POI_NAMED) and int(r.intent_since[0]) == t
    assert int(r.activity[0]) == int(Activity.MOVING)
    assert int(r.activity_kind[0]) == int(ActivityKind.MOVE_TO)
    assert int(act.until_kind[0]) == int(UntilKind.ARRIVAL)
    # 歩く(1 ホップ)→ 着いた tick に到着満了(t+2)が立つが、意図を持つ体は起こさない
    _tick(w, ag, act, il, space, t + 1)
    assert int(r.cell[0]) == 2 and int(r.activity[0]) == int(Activity.IDLE)
    a_, c_, k_ = act.expiry_candidates(ag, t + 2)
    kept, _, _ = il.suppress_wakes(ag, t + 2, a_, c_, k_)
    assert 0 in a_.tolist() and 0 not in kept.tolist()
    # 次の tick に LLM を呼ばずエンジンが食事を実行する
    arr = _tick(w, ag, act, il, space, t + 2)
    assert arr.agent_id.tolist() == [0] and arr.action_code.tolist() == [C.ACT_EAT]
    assert int(r.last_action[0]) == C.ACT_EAT and int(r.last_result[0]) == int(ResultCode.OK)
    assert int(r.intent_action[0]) == INTENT_NONE
    # 活動は LLM が言った活動(食事・30 分)に**実行の tick から**戻る
    assert int(r.activity_kind[0]) == int(ActivityKind.IN_SHOP)
    assert int(r.activity_until[0]) == t + 2 + 30
    s = il.counters()
    assert s["set"] == 1 and s["arrived"] == 1 and s["done"] == 1 and s["failed"] == 0
    assert s["expiry_suppressed"] == 1 and s["mean_ticks"] == 2.0
    assert s["set_by_action"] == {"食事": 1} and s["done_by_action"] == {"食事": 1}


def test_failure_on_arrival_writes_the_code_and_the_fail_immediate_rule_holds():
    # 立てたときは営業中・歩いている途中で閉店 → 着いて CLOSED・活動なし → 次 tick に満了
    w, ag, act, il, space, res = _setup(n=1, cells=(0,), visible={0: [(4, 30)]})
    t = NOON
    batch = _respond(w, ag, space, res, il, t, 0, C.ACT_EAT, "カフェ・ベローチェ")
    applied = ([0], [C.ACT_EAT], [_payload(text="なし")])
    _tick(w, ag, act, il, space, t, batch, applied)
    _tick(w, ag, act, il, space, t + 1)
    with w.writable():
        w.pois.open_now[:] = 1
        w.pois.open_now[4] = 0
    _tick(w, ag, act, il, space, t + 2)
    r = ag.registry
    assert int(r.last_result[0]) == int(ResultCode.CLOSED) and int(r.last_action[0]) == C.ACT_EAT
    assert int(r.intent_action[0]) == INTENT_NONE
    assert int(r.activity_until[0]) == t + 3  # 失敗∧活動なし → 次 tick 満了(規則はそのまま)
    s = il.counters()
    assert s["failed"] == 1 and s["failed_by_result"] == {"closed": 1}


def test_too_far_stops_the_walk_and_writes_the_new_code():
    w, ag, act, il, space, res = _setup(n=1, cells=(0,))
    t = NOON
    # セル 3(2 ホップ)へ歩いている体に、立てたのがずっと前の意図を持たせる
    b = C.IntentBatch(np.array([0]), np.array([C.ACT_MOVE], dtype=np.int8), np.array([3], np.int32),
                      np.array([-1], np.int32), np.array([C.tick_start_ns(t)]))
    R.apply(b, C.IntentBatch.empty(), ag, w, t, vocab_version="v3")
    R.set_intent(ag, np.array([0]), [C.ACT_BUY], [7], [int(IntentKind.POI_NAMED)],
                 t - INTENT_MAX_TICKS - 1)
    il.after_apply(ag, t, act, None)
    r = ag.registry
    assert int(r.last_result[0]) == int(ResultCode.TOO_FAR)
    assert int(r.last_action[0]) == C.ACT_BUY
    assert int(r.activity[0]) == int(Activity.IDLE) and int(r.target_node[0]) == -1
    assert int(r.intent_action[0]) == INTENT_NONE
    assert int(r.activity_until[0]) == t + 1  # 次 tick に考え直す
    assert il.counters()["too_far"] == 1


def test_no_route_at_set_time_is_unreachable_with_the_intended_action_as_subject(monkeypatch):
    w, ag, act, il, space, res = _setup(n=1, cells=(0,), visible={0: [(4, 30)]})
    t = NOON
    batch = _respond(w, ag, space, res, il, t, 0, C.ACT_EAT, "カフェ・ベローチェ")
    monkeypatch.setattr(type(w.graph), "route_next_node",
                        lambda self, node, dest: np.full(np.asarray(node).shape, -1))
    _tick(w, ag, act, il, space, t, batch, ([0], [C.ACT_EAT], [_payload()]))
    r = ag.registry
    assert int(r.last_result[0]) == int(ResultCode.UNREACHABLE)
    assert int(r.last_action[0]) == C.ACT_EAT and int(r.intent_action[0]) == INTENT_NONE
    s = il.counters()
    assert s["set"] == 0 and s["set_failed"] == 1 and s["set_failed_by_result"] == {"unreachable": 1}


# ------------------------------------------------------------------ 計画・上書き・起床
def test_plan_boundary_depart_and_sleep_drop_the_intent():
    w, ag, act, il, space, res = _setup(n=2, cells=(0, 0), visible={0: [(4, 30)]})
    t = NOON
    for a in (0, 1):
        batch = _respond(w, ag, space, res, il, t, a, C.ACT_EAT, "カフェ・ベローチェ")
        _tick(w, ag, act, il, space, t, batch, ([a], [C.ACT_EAT], [_payload()]))
    assert ag.registry.intent_action.tolist() == [C.ACT_EAT, C.ACT_EAT]
    R.rail_depart(ag, np.array([0]), np.array([0]))            # DEPART(域外へ)
    with ag.writable():
        ag.registry.sleep_pending[1] = 1                        # SLEEP(就寝の意図)
    il.after_apply(ag, t + 1, act, None)
    assert ag.registry.intent_action.tolist() == [INTENT_NONE, INTENT_NONE]
    assert il.counters()["dropped"] == {"plan_depart": 1, "plan_sleep": 1}


def _row(t, code, target=-1):
    return C.IntentBatch(np.array([0]), np.array([code], dtype=np.int8),
                         np.array([target], np.int32), np.array([-1], np.int32),
                         np.array([C.tick_start_ns(t)]))


def _walk_to_cell3(t):
    """セル 0 → セル 3(2 ホップ)の店(おむすび権米衛=POI 6)へ食事の意図で歩き出した体。"""
    w, ag, act, il, space, res = _setup(n=1, cells=(0,), visible={0: [(6, 10)]})
    batch = _respond(w, ag, space, res, il, t, 0, C.ACT_EAT, "おむすび権米衛")
    _tick(w, ag, act, il, space, t, batch, ([0], [C.ACT_EAT], [_payload()]))
    assert int(ag.registry.intent_action[0]) == C.ACT_EAT
    assert int(ag.registry.activity[0]) == int(Activity.MOVING)
    return w, ag, act, il, space, res


def test_a_world_touching_response_supersedes_the_intent():
    t = NOON
    w, ag, act, il, space, res = _walk_to_cell3(t)
    _tick(w, ag, act, il, space, t + 1, _row(t + 1, C.ACT_TALK),
          ([0], [C.ACT_TALK], [_payload(text="話す")]))
    assert int(ag.registry.intent_action[0]) == INTENT_NONE
    assert il.counters()["dropped"] == {"superseded": 1}


def test_none_and_wait_keep_the_intent_and_the_walk_q20():
    """親決定 Q20: なし(と 待機)は「新しい行為が無い」=意図を上書きせず歩みも止めない。"""
    t = NOON
    w, ag, act, il, space, res = _walk_to_cell3(t)
    r = ag.registry
    _tick(w, ag, act, il, space, t + 1, _row(t + 1, C.ACT_NONE),
          ([0], [C.ACT_NONE], [_payload(text="休む")]))
    assert int(r.intent_action[0]) == C.ACT_EAT
    assert int(r.activity[0]) == int(Activity.MOVING)          # 歩みを止めない
    assert int(r.activity_kind[0]) == int(ActivityKind.MOVE_TO)  # 活動は目的地つき移動に戻す
    assert int(act.until_kind[0]) == int(UntilKind.ARRIVAL)
    _tick(w, ag, act, il, space, t + 2, _row(t + 2, C.ACT_WAIT))
    assert int(r.intent_action[0]) == C.ACT_EAT and int(r.activity[0]) == int(Activity.MOVING)
    for k in range(3, 8):
        _tick(w, ag, act, il, space, t + k)
        if int(r.intent_action[0]) == INTENT_NONE:
            break
    assert int(r.last_action[0]) == C.ACT_EAT and int(r.last_result[0]) == int(ResultCode.OK)
    s = il.counters()
    assert s["kept"]["none_or_wait"] == 2 and s["done"] == 1 and "superseded" not in s["dropped"]


def test_a_move_to_the_same_destination_keeps_and_a_different_one_supersedes_q20():
    t = NOON
    w, ag, act, il, space, res = _walk_to_cell3(t)
    _tick(w, ag, act, il, space, t + 1, _row(t + 1, C.ACT_MOVE, 3))
    assert int(ag.registry.intent_action[0]) == C.ACT_EAT
    assert il.counters()["kept"] == {"same_dest_move": 1}
    _tick(w, ag, act, il, space, t + 2, _row(t + 2, C.ACT_MOVE, 1))
    assert int(ag.registry.intent_action[0]) == INTENT_NONE
    assert il.counters()["dropped"] == {"superseded": 1}


def test_a_none_response_of_an_arrived_agent_is_dropped_and_the_intent_executes_q20():
    w, ag, act, il, space, res = _setup(n=1, cells=(0,), visible={0: [(4, 30)]})
    t = NOON
    batch = _respond(w, ag, space, res, il, t, 0, C.ACT_EAT, "カフェ・ベローチェ")
    _tick(w, ag, act, il, space, t, batch, ([0], [C.ACT_EAT], [_payload()]))
    _tick(w, ag, act, il, space, t + 1)
    assert int(ag.registry.cell[0]) == 2 and int(ag.registry.activity[0]) == int(Activity.IDLE)
    arr = _tick(w, ag, act, il, space, t + 2, _row(t + 2, C.ACT_NONE),
                ([0], [C.ACT_NONE], [_payload(text="休む")]))
    assert arr.action_code.tolist() == [C.ACT_EAT]
    assert int(ag.registry.last_action[0]) == C.ACT_EAT
    assert il.counters()["kept"] == {"due_response_dropped": 1, "none_or_wait": 1}


def test_suppress_wakes_drops_cell_block_and_expiry_only_for_holders():
    w, ag, act, il, space, res = _setup(n=2, cells=(0, 0))
    R.set_intent(ag, np.array([0]), [C.ACT_BUY], [7], [int(IntentKind.POI_NAMED)], NOON)
    agent = np.array([0, 0, 0, 1, 1])
    cond = np.array([int(WakeCondition.CELL_BLOCK), int(WakeCondition.ACTIVITY_EXPIRY),
                     int(WakeCondition.INTEROCEPTION), int(WakeCondition.CELL_BLOCK),
                     int(WakeCondition.ACTIVITY_EXPIRY)], dtype=np.int8)
    cls = np.zeros(5, dtype=np.int64)
    a2, c2, _ = il.suppress_wakes(ag, NOON, agent, cond, cls)
    assert a2.tolist() == [0, 1, 1]
    assert c2.tolist() == [int(WakeCondition.INTEROCEPTION), int(WakeCondition.CELL_BLOCK),
                           int(WakeCondition.ACTIVITY_EXPIRY)]
    s = il.counters()
    assert s["cell_block_suppressed"] == 1 and s["expiry_suppressed"] == 1


# ------------------------------------------------------------------ Q18: 人 → その人のセル
def test_move_to_a_person_goes_to_that_persons_cell_q18():
    w = _world()
    ag = AgentState(4)
    ag.registry.cell[:] = np.array([0, 3, -1, 0])
    res = TargetResolver(world=w, chooser=NearestChooser(), seed=1)
    tg = [parse_target(s) for s in ("P-1", "P-0", "P-2", "P-99")]
    out = res.resolve_move(ag, NOON, np.array([0, 0, 3, 3]), np.full(4, C.ACT_MOVE), tg,
                           np.ones(4, dtype=bool))
    # 体 0→P-1(セル 3)/ 体 0→自分(今いるセル)/ 体 3→P-2(域外)/ 体 3→存在しない人
    assert out.tolist() == [3, 0, MOVE_BAD_TARGET, MOVE_BAD_TARGET]
    ms = res.move_stats
    assert ms["person"] == 1 and ms["person_self"] == 1
    assert ms["bad_target:person_offmap"] == 1 and ms["bad_target:person_unknown"] == 1


# ------------------------------------------------------------------ B5 の 1 行
def test_b5_intent_line_only_for_holders_within_15_tokens():
    w = _world()
    a = AgentState(2)
    with a.writable():
        a.cell[:] = 0
        a.money[:] = 1_000
        a.last_result_tick[:] = -1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=3, vocab_version="v3")
    r.prepare_tick(700)
    before = [r.render(i, tick=700, wake_reason=3) for i in (0, 1)]
    R.set_intent(a, np.array([0]), [C.ACT_EAT], [4], [int(IntentKind.POI_NAMED)], 690)
    after = [r.render(i, tick=700, wake_reason=3) for i in (0, 1)]
    b5 = after[0].blocks["B5"].decode("utf-8")
    line = next(x for x in b5.split("\n") if x.startswith("[B5 意図]"))
    assert line.startswith("[B5 意図] いま食事のため") and line.endswith("へ向かっている。")
    name = str(r.assets.poi_name[4])  # 描画側の名(合成世界は cat+索引の合成名)
    assert PR.intent_line("食事", name) == line and len(line) // 2 <= PR.INTENT_LINE_MAX_TOKENS
    rows = b5.split("\n")
    assert rows.index(line) == next(i for i, x in enumerate(rows) if x.startswith("[B5 直近]")) + 1
    # 意図の無い体の prompt は 1 バイトも変わらない・持つ体だけ動く
    assert after[1].prompt_hash == before[1].prompt_hash
    assert after[0].prompt_hash != before[0].prompt_hash
    assert r.intent_lines == 1
    # 会話・就寝の対象の語
    assert PR.intent_line("会話", PR.person_word(17)) == "[B5 意図] いま会話のためP-17へ向かっている。"
    assert PR.intent_line("就寝", PR.INTENT_BED_WORD) == "[B5 意図] いま就寝のため自宅へ向かっている。"
    long = PR.intent_line("購入", "とても長い名前のお店の本店ビルディング")
    assert len(long) // 2 <= PR.INTENT_LINE_MAX_TOKENS
    assert PR.intent_line("購入", "ほかほか弁当") == "[B5 意図] いま購入のため目的の場所へ向かっている。"


# ------------------------------------------------------------------ mock の口
def test_mock_out_of_cell_knob_is_off_by_default_and_prefers_names_in_brackets():
    req = LLMRequest(agent_id=7, tick=3, wake_class=1,
                     prompt="[B2 可視] 見えるもの: 地上に街区があり、飲食店(pioppino)、飲食店(いちのや)が見られる。")
    base = MockLLM(1, vocab=("購入",), form="v3").render(req)
    assert MockLLM(1, vocab=("購入",), form="v3", out_of_cell_target_p=0.0).render(req) == base
    got = set()
    for tick in range(40):
        r = LLMRequest(agent_id=7, tick=tick, wake_class=1, prompt=req.prompt)
        txt = MockLLM(1, vocab=("購入",), form="v3", out_of_cell_target_p=1.0).render(r)
        got.add(re.search(r"対象: (\S+)", txt).group(1))
    assert got == {"pioppino", "いちのや"}
    syn = LLMRequest(agent_id=7, tick=3, wake_class=1,
                     prompt="[B2 可視] 見えるもの: スターバックスの店頭、書店Bの店頭。")
    txt = MockLLM(1, vocab=("食事",), form="v3", out_of_cell_target_p=1.0).render(syn)
    assert re.search(r"対象: (\S+)", txt).group(1) in ("スターバックス", "書店B")
    with pytest.raises(ValueError):
        MockLLM(1, form="v3", out_of_cell_target_p=1.5)


# ------------------------------------------------------------------ manifest・run_day
def test_manifest_intent_and_the_layer_is_off_outside_v3_activity_candidates():
    res = run_day(n_agents=40, seed=1, ticks=30, renderer="stub", vocab_version="v3",
                  checkpoint_every=30)
    m = res.run_manifest_fields()
    assert m["intent_max_ticks"] == 60 and m["mock_out_of_cell_target_p"] == 0.0
    assert set(m["intent"]) == set(intent_summary({}, 0, 0)) | {"b5_lines", "b5_lines_over_budget"}
    assert {"kept", "bed_skipped_sleep_pending"} <= set(m["intent"])
    for kw in ({"vocab_version": "v1"}, {"vocab_version": "v3", "activity": False},
               {"vocab_version": "v3", "poi_target": "legacy"}):
        r2 = run_day(n_agents=20, seed=1, ticks=10, renderer="stub", checkpoint_every=10, **kw)
        assert r2.intent == {}
    with pytest.raises(ValueError):
        run_day(n_agents=10, seed=1, ticks=2, renderer="stub", intent_max_ticks=0)
    with pytest.raises(ValueError):
        run_day(n_agents=10, seed=1, ticks=2, renderer="stub", mock_out_of_cell_target_p=2.0)


@pytest.mark.skipif(not (WORLD_DIR / "w8_t1_cell.parquet").exists(), reason="実世界資産が無い")
def test_mock_arm_sets_arrives_and_executes_intents_on_the_real_world():
    from shibuya.cli import run as cli_run

    res = cli_run(n_agents=1_000, seed=1, world_dir=str(WORLD_DIR), vocab_version="v3",
                  mock_out_of_cell_target_p=0.5)
    it = res.intent
    assert it["set"] > 0 and it["arrived"] > 0 and it["done"] > 0
    assert it["proposed_by_kind"].get("poi_named", 0) > 0
    assert it["cell_block_suppressed"] > 0 and it["expiry_suppressed"] > 0
    assert res.target_resolution["v_intent"]["named"] > 0
    assert res.conserved


# ------------------------------------------------------------------ 第288 で見つけた欠陥(保存則)
class _FakeMoney:
    def __init__(self, agents):
        self.agents = agents

    def purchase_many(self, buyers, stores, amounts, tick):
        r = self.agents.registry
        r.money[buyers] = (r.money[buyers].astype(np.int64) - amounts).astype(np.int32)
        return np.zeros(np.asarray(buyers).size, dtype=np.int64)


class _FakeGoods:
    def __init__(self, stock):
        self.stock = np.asarray(stock, dtype=np.int64).copy()

    def can_sell(self, stores):
        return self.stock[np.asarray(stores)] > 0

    def sell_many(self, stores, tick):
        ok = []
        for s_ in np.asarray(stores).tolist():
            ok.append(bool(self.stock[s_] > 0))
            if ok[-1]:
                self.stock[s_] -= 1
        return np.asarray(ok, dtype=bool)

    def aggregate_stock(self, stores=None):
        return self.stock if stores is None else self.stock[np.asarray(stores)]


def test_buyers_beyond_the_shelf_fail_before_paying_so_money_is_conserved():
    """満席の列の捌きが棚 1 個の店へ同じ tick に 2 人を入れると、2 人目は支払いだけ済んで品が出ず
    代金が消えていた(v3 既定の mock 5,000・tick 856 で発見)。超えた分は支払いの前に OUT_OF_STOCK。"""
    from types import SimpleNamespace

    w = _world()
    ag = AgentState(3)
    with ag.writable(), w.writable():
        ag.registry.money[:] = 10_000
        w.pois.stock[7] = 1
        total0 = int(ag.registry.money.astype(np.int64).sum()) + int(w.pois.revenue.sum())
        led = SimpleNamespace(money=_FakeMoney(ag), goods=_FakeGoods(w.pois.stock))
        out = R.ResolveOutcome(tick=NOON, ledger=led)
        R._complete_buy(ag, w, np.array([0, 1]), np.array([7, 7]), np.array([800, 800]), NOON, out)
        total1 = int(ag.registry.money.astype(np.int64).sum()) + int(w.pois.revenue.sum())
    r = ag.registry
    assert int(r.last_result[0]) == int(ResultCode.OK)
    assert int(r.last_result[1]) == int(ResultCode.OUT_OF_STOCK)
    assert int(r.money[1]) == 10_000 and int(r.money[0]) == 9_200
    assert total1 == total0 and out.n_buy_over_stock == 1

