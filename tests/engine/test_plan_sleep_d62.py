"""D-62「就寝は計画の実行」(ユーザー決定 (a)+(b)・2026-09-10)のテスト。

正典・根拠
- PENDING D-62 / 答申 ``docs/research/v2-c7-fix-research.md`` §2。D-56(就寝抑止)を入れても
  深夜の呼が 10% しか減らなかった原因=**``activity`` を ``SLEEPING`` にする口が 2 つしか
  無い**(``resolve.initialize`` の tick 0 一括代入・LLM が「就寝」と答えたとき)。W17 週次表の
  就寝境界は起床候補(``WakeCondition.PLAN_SLEEPING``)を出すだけで ``activity`` を書かない。
- 決定 (a): 就寝境界に達した個体は**エンジンが**寝かせる(その境界で LLM を呼ばない)。
  起床は次の計画境界(``PLAN_WORKING``/``PLAN_GENERAL``/``PLAN_TRANSIT``)か顕著行為
  (D-56 の例外)。判断そのものは週次表=その個体が LLM で生成した計画なので、
  **判断 1 回・実行は世界**(D-51 乗車の意図保持と同じ形)。
- 決定 (b): tick 0 の ``activity`` は W17 の**その日 0:00 時点の活動**から立てる。
  週次表の無い合成世界/mock 日課は**従来どおり**(全員 ``SLEEPING``)。
- 東京都 平日の起床率 a(h)(令和 3 年社会生活基本調査 第 4-1 表): 0 時 20.5% / 3 時 3.5 /
  5 時 15.3 / 12〜19 時 97.8〜98.9。**一律に掛けない**(照合の材料であって目標値ではない)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents import weekly as W
from shibuya.agents.state import Activity, AgentState, WakeCondition
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.run import run_day
from shibuya.world.state import World

# ================================================================= 道具


def _world_agents(n_agents: int = 8, n_cells: int = 9, seed: int = 1):
    """個体を ``cell == agent_id % n_cells`` に置いた小さな世界。"""
    w = World.synthetic(n_cells=n_cells, seed=seed)
    a = AgentState(n_agents)
    a.registry.cell[:] = np.arange(n_agents) % n_cells
    a.registry.node[:] = w.assets.cell_rep_node[a.registry.cell]
    a.registry.activity[:] = int(Activity.IDLE)
    a.freeze()
    w.freeze()
    return w, a


def _cell_of(world, node) -> int:
    return int(np.asarray(world.assets.node_cell)[int(node)])


def _weekly(rows: list[tuple[int, int, int, int, int, int]]) -> W.WeeklySchedule:
    """``(agent_id, day, start, end, activity_code, target_cell)`` から週次表を組む。

    行は ``(agent_id, day, start)`` 昇順で渡すこと(W17 の出力仕様)。
    """
    agents = sorted({r[0] for r in rows})
    idx = {a: i for i, a in enumerate(agents)}
    counts = np.zeros(len(agents) * W.N_DAYS, dtype=np.int64)
    for aid, day, *_ in rows:
        counts[idx[aid] * W.N_DAYS + day] += 1
    offset = np.zeros(counts.size + 1, dtype=np.int64)
    np.cumsum(counts, out=offset[1:])
    return W.WeeklySchedule(
        source=None,
        agent_id=np.asarray(agents, dtype=np.int64),
        day_offset=offset,
        start_min=np.asarray([r[2] for r in rows], dtype=np.int16),
        end_min=np.asarray([r[3] for r in rows], dtype=np.int16),
        activity=np.asarray([r[4] for r in rows], dtype=np.int8),
        place_kind=np.zeros(len(rows), dtype=np.int8),
        target_cell=np.asarray([r[5] for r in rows], dtype=np.int32),
        seq=np.asarray([i for i in range(len(rows))], dtype=np.int16),
    )


ACT_SLEEP_W = W.ACTIVITY_WORDS.index("就寝")
ACT_WORK_W = W.ACTIVITY_WORDS.index("勤務")
ACT_MOVE_W = W.ACTIVITY_WORDS.index("移動")
ACT_REST_W = W.ACTIVITY_WORDS.index("休憩")

# 小さな mock ラン(合成世界・stub レンダラ)。深夜だけを回さない=1 日通す。
# ``budget`` を明示するのは、L4 按分(4M 呼/日 ÷ 390,067 体)だと 60 体では
# **1 tick あたり 0.43 呼**しか出ず、境界の tick に呼が出るかを見られないため。
DAY = dict(n_agents=60, ticks=1_440, n_cells=9, renderer="stub", processes=False,
           conversations=False, checkpoint_every=0, seed=7, budget=200)


# ================================================================= (i) 就寝境界


def test_sleep_boundary_puts_the_agent_to_bed_without_an_llm_call():
    """就寝地に居る個体は境界でそのまま ``SLEEPING``(呼は要らない)。"""
    w, a = _world_agents()
    cells = np.asarray(a.registry.cell, dtype=np.int64)
    got = R.begin_planned_sleep(a, w, np.arange(4), cells[:4], tick=10)
    assert got["slept"] == 4 and got["walking"] == 0
    assert np.all(np.asarray(a.registry.activity)[:4] == int(Activity.SLEEPING))
    assert np.all(np.asarray(a.registry.sleep_pending)[:4] == 0)
    # 触っていない個体は起きたまま
    assert int(a.registry.activity[5]) == int(Activity.IDLE)


def test_sleep_boundary_walks_home_and_sleeps_on_arrival():
    """就寝地に居ない個体は歩き出し(``sleep_pending``)、着いた tick に寝る。"""
    w, a = _world_agents()
    home = np.asarray([_cell_of(w, w.assets.cell_rep_node[3])], dtype=np.int64)
    got = R.begin_planned_sleep(a, w, np.array([0]), home, tick=10)
    assert got["walking"] == 1 and got["slept"] == 0
    assert int(a.registry.activity[0]) == int(Activity.MOVING)
    assert int(a.registry.sleep_pending[0]) == 1
    # エンジン継続で歩かせる(到着まで最大 n_cells 歩)
    for t in range(11, 60):
        if int(a.registry.activity[0]) == int(Activity.SLEEPING):
            break
        intents = C.engine_continuations(a, C.ResourceSpace(w.n_poi, a.n, w.n_cells), t)
        R.apply(intents, C.IntentBatch.empty(), a, w, t)
    assert int(a.registry.activity[0]) == int(Activity.SLEEPING)
    assert int(a.registry.sleep_pending[0]) == 0
    assert int(a.registry.cell[0]) == int(home[0])


def test_sleep_boundary_skips_riding_conversing_and_already_sleeping():
    """乗車中・域外滞在・会話中・就寝済は触らない(理由が計数に出る)。"""
    w, a = _world_agents()
    cells = np.asarray(a.registry.cell, dtype=np.int64)
    with a.writable():
        a.registry.transit_state[0] = 1  # 乗車中
        a.registry.transit_state[1] = 2  # 域外滞在
        a.registry.activity[2] = int(Activity.CONVERSING)
        a.registry.activity[3] = int(Activity.SLEEPING)
    got = R.begin_planned_sleep(a, w, np.arange(5), cells[:5], tick=10)
    assert got == {
        "slept": 1, "walking": 0, "riding": 1, "outside": 1,
        "conversing": 1, "asleep": 1, "unreachable": 0,
    }
    assert int(a.registry.activity[0]) == int(Activity.IDLE)      # 乗車中は触らない
    assert int(a.registry.activity[2]) == int(Activity.CONVERSING)
    assert int(a.registry.activity[4]) == int(Activity.SLEEPING)  # 4 だけ寝た


def test_choosing_another_action_drops_the_sleep_intent():
    """就寝地へ歩いている途中で別の行動を選んだら意図は落ちる(幽霊を残さない)。"""
    w, a = _world_agents()
    home = np.asarray([_cell_of(w, w.assets.cell_rep_node[4])], dtype=np.int64)
    R.begin_planned_sleep(a, w, np.array([0]), home, tick=1)
    assert int(a.registry.sleep_pending[0]) == 1
    intents = C.IntentBatch(
        np.array([0], dtype=np.int64),
        np.array([C.ACT_REST], dtype=np.int8),
        np.array([-1], dtype=np.int32),
        np.array([-1], dtype=np.int32),
        np.array([C.tick_start_ns(2)], dtype=np.int64),
    )
    R.apply(intents, C.IntentBatch.empty(), a, w, 2)
    assert int(a.registry.sleep_pending[0]) == 0
    assert int(a.registry.activity[0]) == int(Activity.RESTING)


# ================================================================= (ii) 起床境界


def test_wake_from_plan_wakes_only_sleepers():
    """非就寝の計画境界は ``SLEEPING`` を ``IDLE`` に戻し、就寝の意図も落とす。"""
    w, a = _world_agents()
    cells = np.asarray(a.registry.cell, dtype=np.int64)
    R.begin_planned_sleep(a, w, np.arange(3), cells[:3], tick=1)
    with a.writable():
        a.registry.sleep_pending[4] = 1
    n = R.wake_from_plan(a, np.array([0, 1, 4, 5]))
    assert n == 2  # 0,1 が寝ていた(4,5 は起きている)
    assert int(a.registry.activity[0]) == int(Activity.IDLE)
    assert int(a.registry.activity[2]) == int(Activity.SLEEPING)  # 呼ばれていない体は寝たまま
    assert int(a.registry.sleep_pending[4]) == 0


def test_sleep_boundary_makes_no_call_and_wake_boundary_does(monkeypatch):
    """1 日ラン: 就寝境界の tick では呼が出ず、起床境界の tick では出る(mock 日課)。

    mock 日課の第 5 境界(slot 4)=就寝。``plan_sleep`` を切ると同じ tick に呼が出る
    =**この差が D-62 (a) の効果**。
    """
    on = run_day(**DAY)
    off = run_day(**DAY, plan_sleep=False)
    calls_on = on.column("calls")
    calls_off = off.column("calls")
    from shibuya.agents.schedule import synthesize

    sched = synthesize(DAY["n_agents"], DAY["seed"], DAY["n_cells"])
    bed = np.unique(sched.base_ticks[:, 4])
    # 就寝境界の tick に出た呼は減る(帰無腕より少ない)
    assert int(calls_on[bed].sum()) < int(calls_off[bed].sum())
    # 起床境界(第 1 境界)では呼が出る
    up = np.unique(sched.base_ticks[:, 0])
    assert int(calls_on[up].sum()) > 0
    # 就寝させた体が実在する(計数が出ている)
    assert on.planned_sleep_counts.get("slept", 0) > 0
    assert off.planned_sleep_counts == {}


# ================================================================= (iii) 顕著行為


def test_salient_wake_is_still_exempt_while_asleep():
    """D-56 の例外(顕著行為は寝ていても起こす)は D-62 の後も生きている。"""
    from shibuya.engine.arbiter import arbitrate

    from .test_sleep_suppression_d56 import SALT, _asleep, _cands

    c = _cands([0, 1], [int(WakeCondition.CELL_BLOCK)] * 2, exempt=[True, False])
    d = arbitrate(c, tick=5, budget=10, run_salt=SALT, asleep=_asleep(0, 1))
    assert d.n_calls == 1 and d.n_sleep_suppressed == 1
    assert int(d.selected.agent_id[0]) == 0


# ================================================================= (iv) tick 0 の活動


def test_initial_activity_reflects_the_plan_at_midnight():
    """0:00 の活動が ``Activity`` に写る(就寝 / 勤務 / 移動 の 3 例)。"""
    wk = _weekly([
        (10, 0, 0, 400, ACT_SLEEP_W, 1),    # 就寝 → SLEEPING
        (11, 0, 0, 400, ACT_WORK_W, 2),     # 勤務 → IDLE(対応する Activity が無い)
        (12, 0, 0, 400, ACT_MOVE_W, 3),     # 移動 → MOVING
        (13, 0, 0, 400, ACT_REST_W, 4),     # 休憩 → RESTING
        (14, 0, 30, 400, ACT_WORK_W, 5),    # 0:00 は隙間 → fallback
    ])
    got = wk.initial_activity(0)
    assert list(got) == [
        int(Activity.SLEEPING), int(Activity.IDLE), int(Activity.MOVING),
        int(Activity.RESTING), int(Activity.SLEEPING),  # 隙間の既定 = SLEEPING(D-62 前と同じ)
    ]
    assert list(wk.initial_activity(0, fallback=int(Activity.IDLE)))[4] == int(Activity.IDLE)
    # 活動語コードそのものも引ける(-1=隙間)
    assert list(wk.activity_at(0, 0)) == [ACT_SLEEP_W, ACT_WORK_W, ACT_MOVE_W, ACT_REST_W, -1]
    assert list(wk.activity_at(0, 30))[4] == ACT_WORK_W
    assert list(wk.activity_at(0, 500)) == [-1] * 5  # 全員の活動が終わっている


def test_activity_to_state_covers_the_vocabulary():
    assert len(W.ACTIVITY_TO_STATE) == len(W.ACTIVITY_WORDS)
    assert W.ACTIVITY_TO_STATE[W.SLEEP_ACTIVITY_CODE] == int(Activity.SLEEPING)
    assert W.ACTIVITY_WORDS[W.SLEEP_ACTIVITY_CODE] == "就寝"
    assert W.ACTIVITY_TO_WAKE[W.SLEEP_ACTIVITY_CODE] == int(WakeCondition.PLAN_SLEEPING)


def test_set_initial_activity_keeps_the_rail_preassignment():
    """域外滞在・乗車中(``transit_state != 0``)は書き換えない(rail の事前割当が正)。"""
    w, a = _world_agents(n_agents=4)
    with a.writable():
        a.registry.transit_state[1] = 2
        a.registry.activity[1] = int(Activity.WAITING)
        a.registry.transit_state[2] = 1
        a.registry.activity[2] = int(Activity.RIDING)
    n = R.set_initial_activity(a, np.full(4, int(Activity.SLEEPING), dtype=np.int8))
    assert n == 2
    assert int(a.registry.activity[0]) == int(Activity.SLEEPING)
    assert int(a.registry.activity[1]) == int(Activity.WAITING)
    assert int(a.registry.activity[2]) == int(Activity.RIDING)
    with pytest.raises(ValueError):
        R.set_initial_activity(a, np.zeros(3, dtype=np.int8))


def test_boundary_events_full_agrees_with_boundary_events():
    """``boundary_events`` は ``boundary_events_full`` の薄い包み(並びが一致)。"""
    wk = _weekly([
        (10, 0, 0, 400, ACT_SLEEP_W, 1),
        (10, 0, 400, 600, ACT_WORK_W, 2),
        (11, 0, 60, 400, ACT_MOVE_W, -1),
    ])
    rows, cond, tick = wk.boundary_events(0)
    rows2, cond2, tick2, cell2 = wk.boundary_events_full(0)
    assert np.array_equal(rows, rows2) and np.array_equal(cond, cond2)
    assert np.array_equal(tick, tick2)
    assert list(cell2) == [1, -1, 2]  # tick 昇順(0, 60, 400)
    assert cond2[0] == int(WakeCondition.PLAN_SLEEPING)


# ================================================================= (v) 合成世界


def test_synthetic_world_still_starts_with_everyone_asleep():
    """週次表の無いランは tick 0 で全員 ``SLEEPING``(D-62 前と同じ=帰無の担保)。"""
    res = run_day(n_agents=40, ticks=1, n_cells=9, renderer="stub", processes=False,
                  conversations=False, checkpoint_every=0, seed=3)
    assert res.wake_rate_by_hour[0] == 0.0  # tick 0 の時点で誰も起きていない
    assert sum(res.calls_by_hour) == res.llm_calls


def test_wake_rate_by_hour_is_a_fraction_and_prints():
    res = run_day(**DAY)
    assert len(res.wake_rate_by_hour) == 24
    assert all(0.0 <= v <= 1.0 for v in res.wake_rate_by_hour)
    text = res.wake_rate_by_hour_text()
    assert text.startswith("起床率/時 00:")
    assert len(text.split()) == 25
    assert "起床率/時" in res.summary()
    assert res.run_manifest_fields()["plan_sleep"] is True
    assert run_day(**DAY, plan_sleep=False).run_manifest_fields()["plan_sleep"] is False


# ================================================================= (vi) 決定論


def test_same_seed_gives_the_same_run():
    a = run_day(**DAY)
    b = run_day(**DAY)
    assert a.final_hash == b.final_hash
    assert a.llm_calls == b.llm_calls
    assert a.wake_rate_by_hour == b.wake_rate_by_hour
    assert a.planned_sleep_counts == b.planned_sleep_counts
