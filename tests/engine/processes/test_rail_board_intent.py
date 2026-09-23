"""D-51 乗車の意図保持(2026-09-10・ユーザー決定 (c))のテスト。

正典/根拠
- 行動契約書 §2.1「乗車」の前提「同一セルに停車中」を**満たすまで世界が運ぶ**へ広げた
  (意味の拡張は実装計画書 §8「D-51 乗車の意図保持」に登録・設計書本文は不変)。
- 答申 ``docs/research/v2-c7-fix-research.md`` §3-1(停車時分・待ち時間・深夜 0 本)。

ここで固定するもの
  (i)   ホーム外で乗車 → 移動 → 到着 → 待ち → 停車で乗車成立(**tick 列で固定**)
  (ii)  停車時の FIFO(``board_since`` 昇順 → agent_id 昇順)と受容 quota
  (iii) 待ちの打ち切り(``BOARD_WAIT_LIMIT_TICKS``)
  (iv)  乗客の保存則(3 値の和 = 個体数)と **RIDING の取り残し 0**
  (v)   意図の落ち方(別行動を選んだ・歩みが止まった・運賃を払えない)
  (vi)  決定論(同じ手順を 2 回で ``state_hash`` 一致)
"""

from __future__ import annotations

import numpy as np

from shibuya.agents.state import Activity, ResultCode
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.processes.rail import RailProcess

from .conftest import fake_timetable_assets, make_agents, make_world

EMPTY = C.IntentBatch.empty()
#: 合成世界(3×3 格子)でホーム(セル 0)から最も遠いセル=4 ホップ。
FAR_CELL = 8
HOPS_TO_PLATFORM = 4


def _rail(n_agents: int = 8, *, departures=(100, 200), lines=("山手線",)):
    world = make_world(9)
    agents, schedule = make_agents(world, n_agents)
    pa = fake_timetable_assets(platform_cell=0, departures=departures, lines=lines)
    rail = RailProcess(world, agents, pa, master_seed=1, day_index=0, schedule=schedule)
    return world, agents, rail


def _intents(agent_ids, code):
    a = np.asarray(agent_ids, dtype=np.int64)
    return C.IntentBatch(
        agent_id=a,
        action_code=np.full(a.size, code, dtype=np.int8),
        target_id=np.full(a.size, -1, dtype=np.int32),
        resource_id=np.full(a.size, -1, dtype=np.int32),
        t_notice_ns=np.zeros(a.size, dtype=np.int64),
    )


def _place(agents, world, ids, cell: int) -> None:
    R.rail_arrive(agents, world, np.asarray(ids, dtype=np.int64),
                  np.full(len(ids), cell, dtype=np.int64))


# ================================================================= (i) 意図の保持
def test_off_platform_board_walks_waits_and_boards_on_the_fixed_tick_sequence():
    """ホーム外で乗車 → 4 tick 歩く → 待つ → 発車 tick に乗る(tick 列を固定)。"""
    world, agents, rail = _rail(n_agents=6, departures=(100,))
    ids = np.arange(2, dtype=np.int64)
    _place(agents, world, ids, FAR_CELL)

    # t=90: 判断は 1 回。世界が最寄りホームへの移動を組む。
    out = R.apply(_intents(ids, C.ACT_BOARD), EMPTY, agents, world, 90, rail=rail)
    assert out.n_boarded == 0 and out.n_board_waiting == 0
    assert np.all(agents.activity[ids] == int(Activity.MOVING))
    assert np.all(agents.registry.board_line[ids] >= 0)
    assert rail.n_board_intent == 2 and rail.n_board_walking == 2

    # t=91..94: エンジン継続で 1 tick 1 ノード。94 tick 目に到着して**待ち**へ入る。
    arrived_at = -1
    for t in range(91, 100):
        out = R.apply(C.engine_continuations(agents, None, t), EMPTY, agents, world, t, rail=rail)
        if arrived_at < 0 and int(agents.registry.board_since[ids[0]]) >= 0:
            arrived_at = t
    assert arrived_at == 90 + HOPS_TO_PLATFORM
    assert np.all(agents.activity[ids] == int(Activity.WAITING))
    assert np.all(agents.registry.board_since[ids] == arrived_at)
    assert np.all(agents.cell[ids] == 0)
    assert np.all(agents.registry.transit_state[ids] == 0)  # 待ちは在圏(3 値を増やさない)

    # t=100: 発車 tick に列車が居る → 待ち行列から乗る。
    out = R.apply(EMPTY, EMPTY, agents, world, 100, rail=rail)
    assert out.n_boarded == 2
    assert np.all(agents.registry.transit_state[ids] == 1)
    assert np.all(agents.activity[ids] == int(Activity.RIDING))
    assert np.all(agents.registry.board_line[ids] == -1)  # 意図は成立して消える
    assert rail.n_boarded_from_queue == 2
    assert rail.counters()["board_success_rate"] == 1.0


def test_the_walk_is_deterministic_for_the_same_situation():
    """同じ状況を 2 回作ると ``state_hash`` が一致する(T2・決定論)。"""

    def _run() -> str:
        world, agents, rail = _rail(n_agents=6, departures=(100,))
        ids = np.arange(4, dtype=np.int64)
        _place(agents, world, ids[:2], FAR_CELL)
        _place(agents, world, ids[2:], 4)
        for t in range(90, 105):
            batch = (
                _intents(ids, C.ACT_BOARD)
                if t == 90
                else C.engine_continuations(agents, None, t)
            )
            R.apply(batch, EMPTY, agents, world, t, rail=rail)
        return agents.state_hash()

    assert _run() == _run()


# ================================================================= (ii) FIFO と quota
def test_queue_is_served_fifo_and_capped_by_the_accept_quota():
    """``board_since`` 昇順 → agent_id 昇順。乗れなかった体は**待ち続ける**。"""
    world, agents, rail = _rail(n_agents=10, departures=(100,))
    early = np.array([5, 3], dtype=np.int64)
    late = np.array([1, 2], dtype=np.int64)
    _place(agents, world, np.concatenate([early, late]), 0)
    R.apply(_intents(early, C.ACT_BOARD), EMPTY, agents, world, 80, rail=rail)
    R.apply(_intents(late, C.ACT_BOARD), EMPTY, agents, world, 90, rail=rail)
    assert np.all(agents.registry.board_since[early] == 80)
    assert np.all(agents.registry.board_since[late] == 90)

    rail.capacity100[0] = 0.5  # 実効容量 = 定員×2.0 = 1 人
    out = R.apply(EMPTY, EMPTY, agents, world, 100, rail=rail)
    assert out.n_boarded == 1
    assert int(agents.registry.transit_state[3]) == 1  # 早い方の、id の小さい方
    rest = np.array([5, 1, 2], dtype=np.int64)
    assert np.all(agents.registry.transit_state[rest] == 0)
    assert np.all(agents.last_result[rest] == int(ResultCode.TRAIN_FULL))
    assert np.all(agents.registry.board_line[rest] >= 0)  # 意図は消えない=待ち続ける
    assert np.all(agents.registry.board_since[rest] == [80, 90, 90])


def test_the_rest_of_the_queue_boards_the_next_train():
    world, agents, rail = _rail(n_agents=10, departures=(100, 110))
    ids = np.array([1, 2, 3], dtype=np.int64)
    _place(agents, world, ids, 0)
    R.apply(_intents(ids, C.ACT_BOARD), EMPTY, agents, world, 90, rail=rail)
    rail.capacity100[0] = 0.5  # 1 本目は 1 人しか乗れない
    R.apply(EMPTY, EMPTY, agents, world, 100, rail=rail)
    assert int(np.count_nonzero(agents.registry.transit_state[ids] == 1)) == 1
    out = R.apply(EMPTY, EMPTY, agents, world, 110, rail=rail)  # 2 本目(定員は既定)
    assert out.n_boarded == 2
    assert np.all(agents.registry.transit_state[ids] == 1)


# ================================================================= (iii) 打ち切り
def test_waiting_is_cut_off_after_the_limit_and_returns_no_train():
    world, agents, rail = _rail(departures=(1_000,))
    ids = np.arange(2, dtype=np.int64)
    _place(agents, world, ids, 0)
    R.apply(_intents(ids, C.ACT_BOARD), EMPTY, agents, world, 100, rail=rail)
    for t in range(101, 100 + R.BOARD_WAIT_LIMIT_TICKS):
        out = R.apply(EMPTY, EMPTY, agents, world, t, rail=rail)
        assert out.n_board_timeout == 0
    out = R.apply(EMPTY, EMPTY, agents, world, 100 + R.BOARD_WAIT_LIMIT_TICKS, rail=rail)
    assert out.n_board_timeout == 2 and rail.n_board_timeout == 2
    assert np.all(agents.registry.board_line[ids] == -1)
    assert np.all(agents.registry.board_since[ids] == -1)
    assert np.all(agents.activity[ids] == int(Activity.IDLE))
    assert np.all(agents.last_result[ids] == int(ResultCode.NO_TRAIN))


# ================================================================= (iv) 乗客の保存則
def test_riders_are_conserved_and_no_one_is_left_riding():
    """3 値の和 = 個体数(毎 tick)・最終発車のあと **RIDING は 0**。"""
    world, agents, rail = _rail(n_agents=40, departures=(100, 200))
    ext = rail.external_home_agents()
    if ext.size:
        R.place_at_external(agents, ext, rail.external_line[ext])
    r = agents.registry
    for t in range(0, 400):
        rail.step(t)
        # 在圏で手が空いている体は毎 tick 乗車を選ぶ(歩いている体には邪魔をしない)
        want = np.flatnonzero(
            (r.transit_state == 0) & (r.board_line < 0) & (r.activity != int(Activity.MOVING))
        )
        batch = C.IntentBatch.concat(
            [_intents(want, C.ACT_BOARD), C.engine_continuations(agents, None, t)]
        ).one_per_agent()
        R.apply(batch, EMPTY, agents, world, t, rail=rail)
        inb, riding, outside = rail.rider_census()
        assert inb + riding + outside == agents.n, (t, inb, riding, outside)
    assert rail.n_boarded_from_queue > 0
    inb, riding, outside = rail.rider_census()
    assert riding == 0, "最終発車のあとも車内に残っている体がいる"
    assert outside > 0


# ================================================================= (v) 意図の落ち方
def test_another_action_drops_the_intent_but_wait_keeps_it():
    world, agents, rail = _rail(departures=(1_000,))
    ids = np.arange(2, dtype=np.int64)
    _place(agents, world, ids, 0)
    R.apply(_intents(ids, C.ACT_BOARD), EMPTY, agents, world, 10, rail=rail)
    R.apply(_intents(ids, C.ACT_WAIT), EMPTY, agents, world, 11, rail=rail)
    assert np.all(agents.registry.board_line[ids] >= 0)  # 待機=ホームで待ち続ける
    assert np.all(agents.registry.board_since[ids] == 10)  # FIFO の鍵は動かない
    R.apply(_intents(ids, C.ACT_REST), EMPTY, agents, world, 12, rail=rail)
    assert np.all(agents.registry.board_line[ids] == -1)
    assert np.all(agents.registry.board_since[ids] == -1)


def test_an_intent_that_stopped_walking_is_swept():
    """自分の行動以外(会話に引き込まれた等)で歩みが止まった意図は掃除される。"""
    world, agents, rail = _rail(departures=(1_000,))
    ids = np.arange(2, dtype=np.int64)
    _place(agents, world, ids, FAR_CELL)
    R.apply(_intents(ids, C.ACT_BOARD), EMPTY, agents, world, 10, rail=rail)
    assert np.all(agents.activity[ids] == int(Activity.MOVING))
    R.set_conversing(agents, ids[:1], ids[1:])
    R.apply(EMPTY, EMPTY, agents, world, 11, rail=rail)
    assert np.all(agents.registry.board_line[ids] == -1)
    assert rail.n_board_dropped == 2


def test_fare_short_drops_the_intent():
    world, agents, rail = _rail(departures=(100,))
    ids = np.arange(2, dtype=np.int64)
    _place(agents, world, ids, 0)
    R.apply(_intents(ids, C.ACT_BOARD), EMPTY, agents, world, 50, rail=rail)
    rail.fare_yen = 10**9
    R.apply(EMPTY, EMPTY, agents, world, 100, rail=rail)
    assert np.all(agents.last_result[ids] == int(ResultCode.FARE_SHORT))
    assert np.all(agents.registry.board_line[ids] == -1)
    assert np.all(agents.registry.transit_state[ids] == 0)


def test_board_without_rail_is_no_train_c2_compatible():
    world, agents, _ = _rail()
    ids = np.arange(2, dtype=np.int64)
    R.apply(_intents(ids, C.ACT_BOARD), EMPTY, agents, world, 10)
    assert np.all(agents.last_result[ids] == int(ResultCode.NO_TRAIN))
    assert np.all(agents.registry.board_line[ids] == -1)


def test_riding_agents_cannot_board_again():
    world, agents, rail = _rail(departures=(100, 200))
    ids = np.arange(2, dtype=np.int64)
    _place(agents, world, ids, 0)
    R.apply(_intents(ids, C.ACT_BOARD), EMPTY, agents, world, 100, rail=rail)
    assert np.all(agents.registry.transit_state[ids] == 1)
    R.apply(_intents(ids, C.ACT_BOARD), EMPTY, agents, world, 101, rail=rail)
    assert np.all(agents.last_result[ids] == int(ResultCode.NO_TRAIN))
    assert np.all(agents.registry.board_line[ids] == -1)
