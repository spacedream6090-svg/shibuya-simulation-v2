"""engine.resolve のテスト: 行動契約書 §2.1 の 12 語(前提・効果・失敗の意味論)と保存則。"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.agents.state import Activity, AgentState, ResultCode
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.change_detect import ChangeDetector
from shibuya.world.state import World

OPEN_TICK = 700  # 既定営業時間(10:00-22:00)の内側
CLOSED_TICK = 100


def _setup(n_agents=6, n_cells=9, seed=1, money=10_000):
    w = World.synthetic(n_cells=n_cells, seed=seed)
    a = AgentState(n_agents)
    a.registry.cell[:] = np.arange(n_agents) % n_cells
    a.registry.node[:] = a.registry.cell
    a.registry.money[:] = money
    a.registry.activity[:] = int(Activity.IDLE)
    a.registry.hunger[:] = 8
    a.registry.fatigue[:] = 8
    a.freeze()
    w.freeze()
    return w, a


def _intents(agent_id, action, target=-1, resource=-1, tick=0):
    ids = np.atleast_1d(np.asarray(agent_id, dtype=np.int64))
    n = ids.size
    return C.IntentBatch(
        ids,
        np.full(n, action, dtype=np.int8),
        np.full(n, target, dtype=np.int32) if np.isscalar(target)
        else np.asarray(target, dtype=np.int32),
        np.full(n, resource, dtype=np.int32) if np.isscalar(resource)
        else np.asarray(resource, dtype=np.int32),
        np.full(n, C.tick_start_ns(tick), dtype=np.int64),
    )


def _apply(agents, world, intents, tick=0, losers=None, schedule=None):
    return R.apply(intents, losers or C.IntentBatch.empty(), agents, world, tick, schedule=schedule)


# ---------------------------------------------------------------- 移動・エンジン継続
def test_move_sets_target_and_engine_step_advances():
    w, a = _setup()
    out = _apply(a, w, _intents(0, C.ACT_MOVE, target=8))
    assert int(a.activity[0]) == int(Activity.MOVING)
    assert int(a.target_node[0]) == 8
    assert int(a.last_result[0]) == int(ResultCode.OK)
    assert out.per_action[C.ACT_MOVE] == 1
    # 1 tick = 1 ノード
    before = int(a.node[0])
    _apply(a, w, _intents(0, C.ENGINE_STEP, target=8), tick=1)
    assert int(a.node[0]) != before


def test_move_to_the_current_cell_is_immediate():
    w, a = _setup()
    _apply(a, w, _intents(3, C.ACT_MOVE, target=3))
    assert int(a.activity[3]) == int(Activity.IDLE)
    assert int(a.target_node[3]) == -1
    assert int(a.last_result[3]) == int(ResultCode.OK)


def test_move_to_an_invalid_cell_fails_unreachable():
    w, a = _setup()
    _apply(a, w, _intents(1, C.ACT_MOVE, target=999))
    assert int(a.last_result[1]) == int(ResultCode.UNREACHABLE)
    assert int(a.fail_streak[1]) == 1


def test_engine_step_arrival_returns_to_idle_and_updates_cell():
    w, a = _setup(n_agents=1, n_cells=4)
    _apply(a, w, _intents(0, C.ACT_MOVE, target=3))
    for tick in range(1, 12):
        _apply(a, w, _intents(0, C.ENGINE_STEP, target=int(a.target_node[0])), tick=tick)
        if int(a.activity[0]) == int(Activity.IDLE):
            break
    assert int(a.cell[0]) == 3 and int(a.target_node[0]) == -1


# ---------------------------------------------------------------- 購入(保存則)
def test_buy_moves_money_to_revenue_and_decrements_stock():
    w, a = _setup()
    poi = int(np.flatnonzero(w.pois.cell == 0)[0])
    price = int(w.pois.price[poi])
    stock0, money0 = int(w.pois.stock[poi]), int(a.money[0])
    total0 = int(a.money.astype(np.int64).sum()) + int(w.pois.revenue.sum())
    out = _apply(a, w, _intents(0, C.ACT_BUY, target=poi), tick=OPEN_TICK)
    assert int(w.pois.stock[poi]) == stock0 - 1
    assert int(a.money[0]) == money0 - price
    assert int(w.pois.revenue[poi]) == price
    assert int(a.holdings[0]) == 1
    assert int(a.activity[0]) == int(Activity.SHOPPING)
    assert out.n_purchases == 1 and out.revenue_delta == price
    # 保存則: Σ所持金 + Σ売上 が不変
    assert int(a.money.astype(np.int64).sum()) + int(w.pois.revenue.sum()) == total0


def test_buy_outside_opening_hours_fails_closed():
    w, a = _setup()
    poi = int(np.flatnonzero(w.pois.cell == 0)[0])
    _apply(a, w, _intents(0, C.ACT_BUY, target=poi), tick=CLOSED_TICK)
    assert int(a.last_result[0]) == int(ResultCode.CLOSED)
    assert int(w.pois.revenue.sum()) == 0


def test_buy_without_stock_fails_and_stock_never_goes_negative():
    w, a = _setup()
    poi = int(np.flatnonzero(w.pois.cell == 0)[0])
    with w.writable():
        w.pois.stock[poi] = 0
    _apply(a, w, _intents(0, C.ACT_BUY, target=poi), tick=OPEN_TICK)
    assert int(a.last_result[0]) == int(ResultCode.OUT_OF_STOCK)
    assert int(w.pois.stock[poi]) == 0
    assert int(w.pois.stock.min()) >= 0


def test_buy_without_money_fails():
    w, a = _setup(money=1)
    poi = int(np.flatnonzero(w.pois.cell == 0)[0])
    _apply(a, w, _intents(0, C.ACT_BUY, target=poi), tick=OPEN_TICK)
    assert int(a.last_result[0]) == int(ResultCode.MONEY_SHORT)
    assert int(a.money[0]) == 1


def test_buy_without_a_target_fails_bad_target():
    w, a = _setup()
    _apply(a, w, _intents(0, C.ACT_BUY, target=-1), tick=OPEN_TICK)
    assert int(a.last_result[0]) == int(ResultCode.BAD_TARGET)


def test_two_buyers_of_the_same_poi_both_decrement():
    w, a = _setup()
    poi = int(np.flatnonzero(w.pois.cell == 0)[0])
    a.thaw()
    a.registry.cell[:2] = 0
    a.freeze()
    stock0 = int(w.pois.stock[poi])
    _apply(a, w, _intents([0, 1], C.ACT_BUY, target=poi), tick=OPEN_TICK)
    assert int(w.pois.stock[poi]) == stock0 - 2


# ---------------------------------------------------------------- 失敗しない行動
@pytest.mark.parametrize(
    "action,activity",
    [
        (C.ACT_WAIT, Activity.WAITING),
        (C.ACT_REST, Activity.RESTING),
        (C.ACT_LEAVE, Activity.IDLE),
    ],
)
def test_actions_that_never_fail(action, activity):
    w, a = _setup()
    _apply(a, w, _intents(2, action))
    assert int(a.last_result[2]) == int(ResultCode.OK)
    assert int(a.activity[2]) == int(activity)


def test_rest_recovers_fatigue():
    w, a = _setup()
    before = int(a.fatigue[2])
    _apply(a, w, _intents(2, C.ACT_REST))
    assert int(a.fatigue[2]) == before - R.REST_FATIGUE_RELIEF


def test_report_and_refuse_are_recorded_without_failing():
    w, a = _setup()
    _apply(a, w, _intents([1, 2], C.ACT_REPORT))
    _apply(a, w, _intents([3], C.ACT_REFUSE))
    assert int(a.last_result[1]) == int(ResultCode.OK)
    assert int(a.last_result[3]) == int(ResultCode.OK)


# ---------------------------------------------------------------- 乗車・降車(C2 は列車なし)
@pytest.mark.parametrize(
    "action, code",
    [(C.ACT_BOARD, ResultCode.NO_TRAIN), (C.ACT_ALIGHT, ResultCode.NO_STOP)],
)
def test_boarding_and_alighting_fail_per_contract(action, code):
    """行動契約書 §2.1: 乗車の失敗=列車なし・降車の失敗=その駅には止まらない。"""
    w, a = _setup()
    _apply(a, w, _intents(4, action, target=0))
    assert int(a.last_result[4]) == int(code)


# ---------------------------------------------------------------- 会話
def test_talk_creates_a_session_when_partner_is_idle_in_the_same_cell():
    w, a = _setup()
    a.thaw()
    a.registry.cell[:2] = 0
    a.registry.node[:2] = 0
    a.freeze()
    out = _apply(a, w, _intents(0, C.ACT_TALK, target=1))
    assert int(a.activity[0]) == int(Activity.CONVERSING)
    assert int(a.talk_partner[0]) == 1
    assert out.n_conversations == 1
    assert int(a.last_result[0]) == int(ResultCode.OK)


def test_talk_to_a_busy_partner_fails():
    w, a = _setup()
    a.thaw()
    a.registry.cell[:2] = 0
    a.registry.activity[1] = int(Activity.CONVERSING)
    a.freeze()
    _apply(a, w, _intents(0, C.ACT_TALK, target=1))
    assert int(a.last_result[0]) == int(ResultCode.PARTNER_BUSY)


def test_talk_to_someone_in_another_cell_fails():
    w, a = _setup()
    _apply(a, w, _intents(0, C.ACT_TALK, target=5))
    assert int(a.last_result[0]) == int(ResultCode.PARTNER_GONE)


def test_talk_without_a_partner_fails_bad_target():
    w, a = _setup()
    _apply(a, w, _intents(0, C.ACT_TALK, target=-1))
    assert int(a.last_result[0]) == int(ResultCode.BAD_TARGET)


# ---------------------------------------------------------------- 手伝い(C2 は必ず失敗)
def test_help_always_fails_in_c2():
    w, a = _setup()
    _apply(a, w, _intents(0, C.ACT_HELP, target=1))
    assert int(a.last_result[0]) == int(ResultCode.BAD_TARGET)


# ---------------------------------------------------------------- 就寝(T2 内省の発火)
def test_sleep_at_home_sets_sleeping_and_records_a_reflection():
    w, a = _setup()
    sched = SimpleNamespace(home_cell=np.arange(a.n) % w.n_cells)
    out = _apply(a, w, _intents(2, C.ACT_SLEEP, target=2), schedule=sched)
    assert int(a.activity[2]) == int(Activity.SLEEPING)
    assert out.n_reflections == 1
    assert int(a.last_result[2]) == int(ResultCode.OK)


def test_sleep_away_from_home_fails_no_bed():
    w, a = _setup()
    sched = SimpleNamespace(home_cell=np.full(a.n, 7))
    _apply(a, w, _intents(2, C.ACT_SLEEP, target=7), schedule=sched)
    assert int(a.last_result[2]) == int(ResultCode.NO_BED)
    assert int(a.activity[2]) != int(Activity.SLEEPING)


# ---------------------------------------------------------------- 未定義行動(§7 段1)
def test_undefined_action_falls_back_to_wait():
    w, a = _setup()
    code = C.parse_action("これは2行形ではない")
    assert code == C.UNDEFINED_ACTION
    batch = C.intents_from_responses(
        a, w, C.ResourceSpace(w.n_poi, a.n, w.n_cells), 0,
        np.array([0]), np.array([3]), np.array([code]),
    )
    assert int(batch.action_code[0]) == C.ACT_WAIT
    _apply(a, w, batch)
    assert int(a.activity[0]) == int(Activity.WAITING)


def test_all_twelve_words_parse():
    for word in C.ACTION_WORDS:
        text = f"理由: テスト\n行動: {word} 対象: なし ひと言: なし"
        assert C.parse_action(text) == C.ACTION_CODES[word]


# ---------------------------------------------------------------- 密度・不応期・身体
def test_density_is_recomputed_每tick():
    w, a = _setup(n_agents=6, n_cells=3)
    _apply(a, w, _intents([0, 1, 2], C.ACT_WAIT))
    assert int(w.cells.density.sum()) == a.n
    assert w.cells.density.tolist() == np.bincount(a.cell, minlength=3).tolist()


def test_set_refractory_uses_the_section6_table():
    w, a = _setup()
    R.set_refractory(a, [0], [int(10)], tick=5)  # CELL_BLOCK=30 分
    assert int(a.refractory_until[0, 10]) == 35
    R.set_refractory(a, [0], [int(0)], tick=5)  # 会話ターン=0
    assert int(a.refractory_until[0, 0]) == 5


def test_advance_body_only_moves_on_its_period():
    w, a = _setup()
    h0 = int(a.hunger[0])
    R.advance_body(a, tick=1)
    assert int(a.hunger[0]) == h0
    R.advance_body(a, tick=R.BODY_TICK_PERIOD)
    assert int(a.hunger[0]) == min(10, h0 + 1)


def test_apply_detection_writes_hashes_and_stages():
    w, a = _setup(n_agents=20, n_cells=8)
    det = ChangeDetector(a.n, w.n_cells)
    res = det.detect(w, a, 0)
    R.apply_detection(a, w, res)
    assert int(np.count_nonzero(w.cells.b4_hash)) > 0
    assert a.frozen and w.frozen


def test_initialize_places_agents_at_home():
    w = World.synthetic(n_cells=16, seed=2)
    a = AgentState(32)
    sched = SimpleNamespace(
        home_cell=np.arange(32) % 16,
        kind=np.zeros(32, dtype=np.int8),
        initial_money=np.full(32, 5_000),
    )
    R.initialize(a, w, sched)
    assert a.cell.tolist() == (np.arange(32) % 16).tolist()
    assert int(a.money.sum()) == 32 * 5_000
    assert int(w.cells.density.sum()) == 32
    assert np.all(a.activity == int(Activity.SLEEPING))
