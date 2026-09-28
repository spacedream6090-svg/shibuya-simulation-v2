"""行為と活動の二層 — 段 2(エンジンの活動層・D-116・第276)。

正典: ``docs/design/v2-two-layer-implementation-agenda.md`` §2(段 2 の決め)+ §6(第275 親の決め)。

見るもの(アジェンダ §2 のテスト行)
(a) 満了で起床する(``activity_until == tick`` の体が ``ACTIVITY_EXPIRY`` の候補になり、呼まで届く)
(b) 活動中は場所の変化(CELL_BLOCK)で起きない(内受容は従来どおり)
(c) ``--activity off`` で現行どおり(欄なし・満了なし)/v1 は on/off で checkpoint 同一
(d) 「あたり」の歩行が半径内・決定論(域外は対象不正)
(e) B4b の 1 行が同セルの 2 体でバイト一致
(f) checkpoint に活動文が効く(活動層の無いランの ``combined`` は従来の式のまま)
(g) 第275 親の決め: 休んでいる体の疲労回復・並ぶ=食事/購入へ委譲・未定義→なし
(h) 満了入口は不応期表の外(アービタ・``set_refractory`` が表の外の条件で落ちない)
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.schedule import synthesize
from shibuya.agents.state import (
    N_WAKE_CONDITIONS,
    WAKE_CONDITION_CLASS,
    Activity,
    ActivityKind,
    AgentState,
    ResultCode,
    WakeCondition,
)
from shibuya.core.types import EventClass
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.activity import (
    ActivityLayer,
    ActivityPayload,
    activity_kind_of,
    displayable_activity,
)
from shibuya.engine.arbiter import Arbiter, WakeCandidates
from shibuya.engine.run import Checkpoint, run_day
from shibuya.core.hashing import blake3_hex
from shibuya.llm import LLMResponse
from shibuya.llm.contract import (
    NONE_ACTION_CODE,
    UNDEFINED_ACTION,
    UntilKind,
    compat_word,
    format_two_line_v3,
)
from shibuya.perception import renderer as PR
from shibuya.perception import templates as T
from shibuya.perception.renderer import Renderer
from shibuya.world.state import World

SALT = b"s" * 16


class V3LLM:
    """語彙 v3 の 5 ラベル形を返す台本 mock(行動・対象・活動・まで を固定)。"""

    def __init__(self, action: str, target: str = "なし", activity: str = "休む",
                 until: str = "30分") -> None:
        self.text = format_two_line_v3("台本の理由", action, target, activity, until)
        self.n_calls = 0

    def complete(self, request):
        self.n_calls += 1
        return LLMResponse(text=self.text, source="scripted")


#: 起きている時間帯を含む短い窓(就寝抑止を切って呼を出す)。
SMALL = dict(n_agents=120, seed=7, ticks=240, checkpoint_every=80, n_cells=25,
             sleep_suppression=False)


def _layer(n: int = 6, n_cells: int = 49, activity_columns: bool = True):
    w = World.synthetic(n_cells=n_cells, seed=1)
    a = AgentState(n, activity_columns=activity_columns)
    R.initialize(a, w, synthesize(n, 1, w.n_cells))
    a.freeze()
    return w, a, ActivityLayer(n, w, SALT)


def _payload(text="休む", kind=UntilKind.MINUTES, value=30, wander=False):
    return ActivityPayload(text, int(kind), int(value), wander)


# ------------------------------------------------------------------ (a) 満了
def test_expiry_candidate_at_the_until_tick():
    w, a, layer = _layer()
    layer.after_resolve(a, 10, [0, 1], [NONE_ACTION_CODE, NONE_ACTION_CODE],
                        [_payload(value=30), _payload(value=5)])
    assert a.activity_until[0] == 40 and a.activity_until[1] == 15
    assert a.activity_kind[0] == int(ActivityKind.IN_PLACE)
    ag, cond, cls = layer.expiry_candidates(a, 15)
    assert ag.tolist() == [1] and cond.tolist() == [int(WakeCondition.ACTIVITY_EXPIRY)]
    assert cls.tolist() == [int(EventClass.PLAN_BOUNDARY)]
    assert layer.expiry_candidates(a, 39)[0].size == 0
    assert layer.expiry_candidates(a, 40)[0].tolist() == [0]


def test_expiry_wakes_agents_in_a_v3_run():
    llm = V3LLM("なし", "なし", "休む", "10分")
    res = run_day(llm=llm, vocab_version="v3", **SMALL)
    assert res.activity is True
    assert res.calls_by_condition["ACTIVITY_EXPIRY"] > 0, "満了入口から呼が出る"
    assert res.activity_counters["expiry_candidates"] >= res.calls_by_condition["ACTIVITY_EXPIRY"]
    assert res.run_manifest_fields()["activity"] is True
    assert res.activity_kind_counts["in_place"] > 0


# ------------------------------------------------------------------ (b) 抑止
def test_cell_block_wakes_are_suppressed_during_an_activity():
    w, a, layer = _layer()
    layer.after_resolve(a, 0, [0], [NONE_ACTION_CODE], [_payload(value=60)])
    agent = np.array([0, 0, 1], dtype=np.int64)
    cond = np.array([int(WakeCondition.CELL_BLOCK), int(WakeCondition.INTEROCEPTION),
                     int(WakeCondition.CELL_BLOCK)], dtype=np.int8)
    cls = np.zeros(3, dtype=np.int64)
    ag, co, _ = layer.suppress_cell_block(a, 5, agent, cond, cls)
    assert list(zip(ag.tolist(), co.tolist())) == [
        (0, int(WakeCondition.INTEROCEPTION)), (1, int(WakeCondition.CELL_BLOCK)),
    ], "活動中の体の CELL_BLOCK だけ落ちる(内受容と活動の無い体は残る)"
    assert layer.n_cell_suppressed == 1
    # 満了後は落とさない
    ag2, _, _ = layer.suppress_cell_block(a, 60, agent, cond, cls)
    assert ag2.size == 3


# ------------------------------------------------------------------ (c) off / v1
def test_activity_off_is_the_current_behaviour():
    llm = V3LLM("なし", "なし", "休む", "10分")
    res = run_day(llm=llm, vocab_version="v3", activity=False, **SMALL)
    assert res.activity is False and res.activity_counters == {}
    assert res.calls_by_condition["ACTIVITY_EXPIRY"] == 0
    with pytest.raises(AttributeError):
        res.agents.activity_until  # 欄を確保しない
    assert all(c.activity_hash == "" for c in res.checkpoints)


def test_v1_ignores_the_activity_switch():
    on = run_day(**SMALL)
    off = run_day(activity="off", **SMALL)
    assert on.final_hash == off.final_hash and on.llm_calls == off.llm_calls
    assert on.activity is False and "activity_until" not in on.agents.registry.arrays


# ------------------------------------------------------------------ (d) あたり
def test_wander_destinations_are_within_the_radius_and_deterministic():
    w, a, layer = _layer(n=40, n_cells=49)  # 7×7 の格子
    ids = np.arange(40, dtype=np.int64)
    centre = 24  # (3, 3)
    cells = np.full(40, centre, dtype=np.int64)
    d1 = layer.wander_destinations(ids, cells, 100)
    d2 = layer.wander_destinations(ids, cells, 100)
    assert np.array_equal(d1, d2), "同じ salt・tick・体なら同じ行き先"
    ix, iy = w.assets.cell_ix, w.assets.cell_iy
    assert np.all(d1 != centre)
    assert np.all(np.abs(ix[d1] - ix[centre]) <= 2) and np.all(np.abs(iy[d1] - iy[centre]) <= 2)
    assert len(set(d1.tolist())) > 1, "候補の中で散る"
    d3 = layer.wander_destinations(ids, cells, 101)
    assert not np.array_equal(d1, d3)
    bad = layer.wander_destinations(np.array([0]), np.array([-1]), 100)
    assert bad.tolist() == [C.WANDER_BAD_TARGET]


def test_wander_bad_target_fails_as_bad_target():
    w = World.synthetic(n_cells=16, seed=1)
    a = AgentState(2)
    R.initialize(a, w, synthesize(2, 1, w.n_cells))
    a.freeze()
    out = R.ResolveOutcome(tick=5)
    with a.writable(), w.writable():
        R._apply_move(a, w, np.array([0, 1]), np.array([C.WANDER_BAD_TARGET, 3]), 5, out, None)
    assert a.last_result[0] == int(ResultCode.BAD_TARGET)
    assert a.last_result[1] == int(ResultCode.OK)


def test_wander_run_walks_near_and_keeps_walking():
    llm = V3LLM("移動", "あたり", "散歩", "60分")
    res = run_day(llm=llm, vocab_version="v3", **SMALL)
    assert res.activity_kind_counts["wander"] > 0
    assert res.activity_counters["wander_steps"] > 0, "着いたら次を選ぶ"


# ------------------------------------------------------------------ (e) B4b の 1 行
def _render_pair(rows):
    w = World.synthetic(n_cells=9, seed=2)
    a = AgentState(4)
    with a.writable():
        a.cell[:] = 4
        a.xy[:] = 50.0
        a.money[:] = 1_000
        a.last_result_tick[:] = -1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=3, vocab_version="v3", role_words=True)
    r.prepare_tick(700, activity_rows=rows)
    return r.render(0, tick=700, wake_reason=3), r.render(1, tick=700, wake_reason=3)


def test_b4b_activity_line_is_byte_identical_in_a_cell():
    x, y = _render_pair({4: (("散歩", 3), ("店を見る", 1))})
    assert x.blocks["B4b"] == y.blocks["B4b"]
    line = x.blocks["B4b"].decode("utf-8")
    assert line == "[B4b 活動] 近くの人: 散歩が3人・店を見るが1人。"
    assert T.template_sha256() == "ea204a66ad13af47024baa2ab51ca7ad0063f8318dd870662682b66c556eb2b0"  # v1.3(旧 v1.2 = 1f6c7d62…・v1.1 = 8f2959d0…)


def test_activity_line_budget_and_filters():
    assert PR.activity_line([]) == ""
    long = PR.activity_line([("とても長い活動の文章", 3), ("散歩", 2)])
    assert T.TEMPLATES["B4b.near"] not in long
    from shibuya.perception.channels import estimate_tokens

    assert estimate_tokens(long) <= PR.ACTIVITY_LINE_MAX_TOKENS
    assert PR.activity_line([("P-3を待つ", 2)]) == "", "個体依存語は出さない(規約⑧)"
    assert PR.activity_line([("戦略を練る", 2)]) == "", "省略記法の語を含む文は出さない(⑥)"
    assert not displayable_activity("なし") and displayable_activity("散歩")


def test_cell_rows_count_everyone_in_the_cell_top_two():
    w, a, layer = _layer(n=6)
    with a.writable():
        a.cell[:] = np.array([3, 3, 3, 3, 5, 5])
    texts = ["散歩", "散歩", "店を見る", "待つ", "散歩", "なし"]
    layer.after_resolve(a, 0, list(range(6)), [NONE_ACTION_CODE] * 6,
                        [_payload(text=t, value=60) for t in texts])
    rows = layer.cell_rows(a, 1)
    assert rows[3] == (("散歩", 2), ("店を見る", 1)), "人数降順→文字列順・上位 2"
    assert rows[5] == (("散歩", 1),), "なし は出さない"
    assert layer.cell_rows(a, 61) == {}, "満了後は出さない"


# ------------------------------------------------------------------ (f) checkpoint
def test_checkpoint_includes_the_activity_text():
    w, a, layer = _layer()
    h0 = layer.state_hash()
    layer.after_resolve(a, 0, [0], [NONE_ACTION_CODE], [_payload(text="散歩")])
    h1 = layer.state_hash()
    layer.after_resolve(a, 1, [0], [NONE_ACTION_CODE], [_payload(text="休む")])
    assert len({h0, h1, layer.state_hash()}) == 3
    base = Checkpoint(0, "a", "w", "p", "s")
    assert base.combined == blake3_hex("\x1f".join(("a", "w", "p", "s")).encode("utf-8")), (
        "活動層の無い checkpoint は従来の式のまま"
    )
    assert Checkpoint(0, "a", "w", "p", "s", h1).combined != base.combined


def test_v3_run_checkpoints_carry_the_activity_hash_and_are_deterministic():
    llm1, llm2 = V3LLM("なし", "なし", "休む", "10分"), V3LLM("なし", "なし", "休む", "10分")
    r1 = run_day(llm=llm1, vocab_version="v3", **SMALL)
    r2 = run_day(llm=llm2, vocab_version="v3", **SMALL)
    assert r1.final_hash == r2.final_hash
    assert all(c.activity_hash for c in r1.checkpoints)
    r3 = run_day(llm=V3LLM("なし", "なし", "散歩", "10分"), vocab_version="v3", **SMALL)
    assert r3.final_hash != r1.final_hash, "活動文だけが違うランは checkpoint が違う"


# ------------------------------------------------------------------ 「まで」の解決
def test_until_resolution_rules():
    w, a, layer = _layer(n=4)
    ids = np.arange(4, dtype=np.int64)
    kinds = np.array([UntilKind.CLOCK, UntilKind.CLOCK, UntilKind.PARTNER, UntilKind.ARRIVAL])
    vals = np.array([12 * 60 + 30, 8 * 60, 0, 0])
    tick = 12 * 60  # 12:00
    got = layer.resolve_until(ids, kinds, vals, tick)
    assert got[0] == tick + 30, "12:30 は同じ日の 30 分後"
    assert got[1] == tick + 480, "08:00 は過去=翌日だが上限 480 分で切る"
    assert got[2] == tick + 60, "相手の上限 60 分"
    assert got[3] == tick + 480, "到着は事象で満了(上限は 480 分)"
    assert layer.resolve_until(ids[:1], np.array([UntilKind.MINUTES]), np.array([0]), 5)[0] == 6


def test_next_schedule_uses_the_plan_boundary_table():
    w = World.synthetic(n_cells=9, seed=1)
    layer = ActivityLayer(3, w, SALT, boundary_agent=np.array([1, 1, 2]),
                          boundary_tick=np.array([100, 300, 50]))
    ids = np.arange(3, dtype=np.int64)
    got = layer.resolve_until(ids, np.full(3, int(UntilKind.NEXT_SCHEDULE)), np.zeros(3), 120)
    assert got.tolist() == [180, 300, 180], "次の予定が無ければ既定 60 分"


def test_arrival_and_failure_settle_the_activity():
    w, a, layer = _layer(n=3)
    with a.writable():
        a.activity[:] = np.array([int(Activity.MOVING), int(Activity.IDLE), int(Activity.IDLE)])
        a.last_result[2] = int(ResultCode.CLOSED)
        a.last_result_tick[2] = 10
    layer.after_resolve(
        a, 10, [0, 1, 2], [C.ACT_MOVE, C.ACT_MOVE, C.ACT_BUY],
        [_payload("なし", UntilKind.ARRIVAL, 0), _payload("なし", UntilKind.ARRIVAL, 0),
         _payload("なし", UntilKind.MINUTES, 30)],
    )
    assert a.activity_until[2] == 11, "失敗+活動なし=次の tick に満了"
    layer.settle_events(a, 10)
    assert a.activity_until[1] == 11, "もう移動していない=到着で満了"
    assert a.activity_until[0] > 11, "移動中はまだ"


def test_activity_kind_mapping():
    codes = np.array([C.ACT_MOVE, C.ACT_MOVE, C.ACT_BOARD, C.ACT_BUY, C.ACT_EAT, C.ACT_QUEUE,
                      C.ACT_SLEEP, NONE_ACTION_CODE, C.ACT_TALK, UNDEFINED_ACTION])
    wander = np.array([False, True] + [False] * 8)
    got = activity_kind_of(codes, wander).tolist()
    K = ActivityKind
    assert got == [K.MOVE_TO, K.WANDER, K.MOVE_TO, K.IN_SHOP, K.IN_SHOP, K.IN_SHOP,
                   K.NONE, K.IN_PLACE, K.IN_PLACE, K.IN_PLACE]


# ------------------------------------------------------------------ (g) 第275 の決め
def test_resting_bodies_recover_fatigue_every_ten_ticks():
    w, a, layer = _layer(n=3)
    with a.writable():
        a.fatigue[:] = 5
        a.activity[:] = int(Activity.IDLE)
    layer.after_resolve(a, 0, [0, 1, 2], [NONE_ACTION_CODE, C.ACT_BUY, C.ACT_MOVE],
                        [_payload(value=60)] * 3)
    R.advance_body(a, 10)
    assert a.fatigue.tolist() == [4, 4, 5], "その場・在店は −1・移動の活動は回復しない"
    R.advance_body(a, 70)
    assert a.fatigue.tolist() == [4, 4, 5], "満了後は回復しない"
    v1 = AgentState(1)
    with v1.writable():
        v1.fatigue[:] = 5
    R.advance_body(v1, 10)
    assert v1.fatigue.tolist() == [5], "活動層の無い体は従来どおり(30 tick 周期だけ)"


def _one_tick(action_code: int, target_cat: str):
    w = World.synthetic(n_cells=16, seed=1)
    a = AgentState(1)
    R.initialize(a, w, synthesize(1, 1, w.n_cells))
    mask = np.asarray(w.eatery_mask, dtype=bool)
    # 対象は「セルの最小 id の POI」(購入と同じ走査)なので、その POI が狙いの種類のセルを選ぶ
    first: dict[int, int] = {}
    for p, c in enumerate(np.asarray(w.pois.cell).tolist()):
        if c >= 0 and c not in first:
            first[c] = p
    want_eatery = target_cat == "eatery"
    cell = next(c for c, p in sorted(first.items()) if bool(mask[p]) is want_eatery)
    with a.writable():
        a.registry.node[:] = w.assets.cell_rep_node[cell]
        a.registry.cell[:] = cell
        a.registry.money[:] = 100_000
    tick = 700
    space = C.ResourceSpace(w.n_poi, a.n, w.n_cells)
    batch = C.intents_from_responses(
        a, w, space, tick, np.array([0]), np.zeros(1, dtype=np.int64),
        np.array([action_code]), vocab_version="v3",
    )
    plan = C.arbitrate_resources(batch, tick, SALT, space, w.pois.stock, w.pois.capacity)
    out = R.apply(plan.confirmed, plan.losers, a, w, tick, vocab_version="v3")
    return a, w, batch, out


@pytest.mark.parametrize("cat,counter", [("eatery", "n_queue_to_eat"), ("other", "n_queue_to_buy")])
def test_queue_delegates_to_eat_or_buy(cat, counter):
    a, w, batch, out = _one_tick(C.ACT_QUEUE, cat)
    assert getattr(out, counter) == 1
    assert out.per_action.get(C.ACT_QUEUE) == 1 and a.last_action[0] == C.ACT_QUEUE


def test_undefined_falls_back_to_none_in_v3():
    a, w, batch, out = _one_tick(UNDEFINED_ACTION, "other")
    assert batch.action_code.tolist() == [NONE_ACTION_CODE]
    assert a.last_result[0] == int(ResultCode.OK), "なし は失敗しない"
    w1 = World.synthetic(n_cells=16, seed=1)
    a1 = AgentState(1)
    R.initialize(a1, w1, synthesize(1, 1, w1.n_cells))
    space = C.ResourceSpace(w1.n_poi, 1, w1.n_cells)
    b1 = C.intents_from_responses(a1, w1, space, 5, np.array([0]), np.zeros(1, dtype=np.int64),
                                  np.array([UNDEFINED_ACTION]))
    assert b1.action_code.tolist() == [C.ACT_WAIT], "v1 は待機のまま"


def test_queue_without_a_poi_is_bad_target():
    w = World.synthetic(n_cells=16, seed=1)
    a = AgentState(1)
    R.initialize(a, w, synthesize(1, 1, w.n_cells))
    out = R.ResolveOutcome(tick=5)
    with a.writable(), w.writable():
        R._apply_queue(a, w, np.array([0]), np.array([-1]), 5, out, None)
    assert a.last_result[0] == int(ResultCode.BAD_TARGET)


# ------------------------------------------------------------------ (h) 満了入口は不応期表の外
def test_expiry_condition_is_outside_the_refractory_table():
    assert int(WakeCondition.ACTIVITY_EXPIRY) == N_WAKE_CONDITIONS == 11
    assert WAKE_CONDITION_CLASS[int(WakeCondition.ACTIVITY_EXPIRY)] == EventClass.PLAN_BOUNDARY
    a = AgentState(3)
    a.freeze()
    R.set_refractory(a, np.array([0, 1]), np.array([int(WakeCondition.ACTIVITY_EXPIRY),
                                                    int(WakeCondition.CELL_BLOCK)]), 10)
    assert a.refractory_until.shape == (3, N_WAKE_CONDITIONS)
    assert a.refractory_until[1, int(WakeCondition.CELL_BLOCK)] == 40
    arb = Arbiter(3, SALT, 10.0)
    cands = WakeCandidates(
        np.array([0, 1]), np.array([int(WakeCondition.ACTIVITY_EXPIRY), int(WakeCondition.CELL_BLOCK)],
                                   dtype=np.int8),
        np.array([int(EventClass.PLAN_BOUNDARY), int(EventClass.CELL)]),
        np.array([20, 20]), np.array([False, False]),
    )
    dec = arb.step(20, cands, a.refractory_until)
    assert sorted(dec.selected.agent_id.tolist()) == [0], "満了は抑止されず、CELL_BLOCK は不応期中"


# ------------------------------------------------------------------ 描画の v3 表
def test_v3_option_and_word_tables_are_the_compat_reading():
    for code, words in PR.RESULT_OPTIONS.items():
        want = tuple(dict.fromkeys(compat_word(w, "v1", "v3") for w in words))
        assert PR.RESULT_OPTIONS_V3[code] == want
    assert PR.DEFAULT_OPTIONS_V3 == tuple(
        dict.fromkeys(compat_word(w, "v1", "v3") for w in T.DEFAULT_OPTIONS)
    )
    assert PR.ACTIVITY_WORDS_V3 == tuple(compat_word(w, "v1", "v3") for w in PR.ACTIVITY_WORDS)
    from shibuya.agents import weekly as W

    assert W.ACTIVITY_TO_ACTION_V3 == {
        k: compat_word(v, "v1", "v3") for k, v in W.ACTIVITY_TO_ACTION.items()
    }
    assert W.activity_to_action("v1") is W.ACTIVITY_TO_ACTION


def test_renderer_v3_expiry_reason_and_failure_options():
    w = World.synthetic(n_cells=9, seed=2)
    a = AgentState(2)
    with a.writable():
        a.cell[:] = 4
        a.last_result[:] = int(ResultCode.MONEY_SHORT)
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=3, vocab_version="v3")
    r.prepare_tick(700)
    b6 = r.render(0, tick=700, wake_reason=int(WakeCondition.ACTIVITY_EXPIRY)).blocks["B6"]
    txt = b6.decode("utf-8")
    assert PR.ACTIVITY_EXPIRY_REASON in txt
    assert "いま可能: 移動、なし" in txt and "待機" not in txt
    r1 = Renderer(w, a, seed=3)
    r1.prepare_tick(700)
    assert "待機" in r1.render(0, tick=700, wake_reason=3).blocks["B6"].decode("utf-8")


# ------------------------------------------------------------------ bridge(役割語・対象ヒント)
def test_bridge_role_words_fall_back_to_none_and_hints_carry_in_v3():
    from shibuya.engine.llm_bridge import LLMBridge

    class Fixed:
        def __init__(self, text):
            self.text = text

        def complete(self, request):
            return LLMResponse(text=self.text, source="scripted")

    b = LLMBridge(Fixed(format_two_line_v3("r", "接客", "なし", "仕事", "30分")),
                  vocab_version="v3")
    res = b.call(0, 0, 1, 3)
    assert res.role_action and res.action_code == NONE_ACTION_CODE
    b2 = LLMBridge(Fixed(format_two_line_v3("r", "移動", "職場", "なし", "到着")),
                   vocab_version="v3")
    res2 = b2.call(0, 0, 1, 3)
    assert res2.target_hint == "work"
