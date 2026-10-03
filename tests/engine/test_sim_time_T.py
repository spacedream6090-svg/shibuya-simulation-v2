"""10a(指示書 10-03 §3-1 A1): 通しの時刻 T(T = 日 × 1 日の tick 数 + 日の中の tick)の既知の答え。

見るもの(アジェンダ §4・指示 §1)
- 0 日目は今と同じ: 2 日のランの 0 日目の checkpoint が 1 日のランと一致する(既定の腕と全腕)。
- (i) 1 日目 23:50 に張った 20 分の不応期が 2 日目 0:10 に切れる(0:09 はまだ抑止)。
- (ii) 1 日目 23:00 の会話の辺の経過時間が 2 日目 1:00 に 120 分になる。
- (iii) 2 日目の同じ tick・同じ体の乱数が 1 日目と違う(mock の応答・選び手・適用順・call_id)。
- (iv) 経過時間が負にならない: tick を値に持つ SoA の 15 列と SoA の外の行を、全腕の 2 日ランの**毎 tick** に
  検査する(「〜から」の列は T 以下・「〜まで」の列は T + 上限 以下)。
- 型: tick を持つ 15 列の型が 30 日ぶんの T(43,200)を表せる。
- 日の中の時刻で引く表(計画境界・食事の予定)は ``T % 1 日の tick 数`` で引く。
- 複数日の口の制限(合成世界・台帳なし・艦隊なし・再生でない・ticks=1 日)。

ラン(小さい合成世界・mock)は 1 日 2〜5 秒。
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pytest

from shibuya.agents.state import N_WAKE_CONDITIONS, AgentState, ResultCode, WakeCondition
from shibuya.core.hashing import apply_key_array
from shibuya.core.types import EventClass
from shibuya.engine import resolve as R
from shibuya.engine import run as RUN
from shibuya.engine.activity import UNTIL_MAX_MINUTES, ActivityLayer
from shibuya.engine.arbiter import Arbiter, WakeCandidates
from shibuya.engine.calendar import SimCalendar
from shibuya.engine.chooser import draw_index
from shibuya.engine.energy import EnergyModel, OutOfAreaMeals, load_anchors
from shibuya.engine.relations import RelationLayer
from shibuya.engine.run import run_day, run_salt_for
from shibuya.engine.tape import Tape
from shibuya.llm import LLMRequest
from shibuya.llm.mock import MockLLM
from shibuya.world.state import World

N = 100
CELLS = 16
TPD = 1_440
#: 全腕(語彙 v3・活動・記憶・関係(同席・知人出現)・店の記憶・親しみ・エネルギー)。
ALL_ARMS = dict(vocab_version="v3", memory="on", relations="on", store_memory="on", familiarity="on",
                hunger_model="energy", rel_copresent="on")
#: 方策 classical(選び手 classical=想起優先の候補合成 ``StoreChoice`` が立つ)+全腕。
CLASSICAL_ARMS = dict(ALL_ARMS, policy="classical", chooser="classical")
#: SoA の「〜から」の列(値 ≤ T)。``rel_first`` の初期辺は負の過去 tick(≤ T)。
SINCE_COLUMNS = ("last_result_tick", "intent_since", "poi_since", "queue_since", "board_since",
                 "mem_tick", "mem_last", "fam_first", "fam_last", "sm_first", "sm_last",
                 "rel_first", "rel_last")
#: SoA の「〜まで」の列(値 ≤ T + 上限)。
UNTIL_COLUMNS = ("refractory_until", "activity_until")
#: tick を値に持つ SoA の 15 列(棚卸し 表 4-b)。
TICK_COLUMNS = SINCE_COLUMNS + UNTIL_COLUMNS


def _run(days: int, **kw):
    return run_day(n_agents=N, seed=1, n_cells=CELLS, ticks=TPD, sim_days=days, checkpoint_every=360,
                   budget=float(N), **kw)


# ================================================================= 0 日目は今と同じ
@pytest.mark.parametrize("arms", [{}, ALL_ARMS, CLASSICAL_ARMS], ids=["default", "all_arms", "classical"])
def test_day0_of_a_two_day_run_is_the_one_day_run(arms):
    one = _run(1, **arms)
    two = _run(2, **arms)
    assert one.llm_calls > 0
    day0 = [c for c in two.checkpoints if c.tick < TPD]
    assert [c.combined for c in day0] == [c.combined for c in one.checkpoints]
    assert [c.tick for c in two.checkpoints][-1] == 2 * TPD - 1
    assert two.ticks == 2 * TPD and two.sim_days == 2
    assert two.llm_calls > one.llm_calls  # 2 日目も呼が立つ(計画境界を日の中の tick で引いている)
    # 2 日目の朝(6〜12 時)にも呼がある(計画境界の起床=日の中の tick で引く表)
    t = two.column("tick")
    calls = two.column("calls")
    assert int(calls[(t >= TPD + 6 * 60) & (t < TPD + 12 * 60)].sum()) > 0


def test_tape_and_call_keys_use_T(tmp_path):
    res = _run(2, tape_path=tmp_path / "tape")
    rows = list(Tape(tmp_path / "tape").rows())
    assert len(rows) == res.llm_calls
    ticks = np.asarray([r.tick for r in rows])
    assert ticks.max() >= TPD and ticks.min() < TPD           # テープの tick 欄は T
    keys = {(r.agent_id, r.tick, r.wake_class) for r in rows}
    assert len(keys) == len(rows)                              # 2 日で鍵が衝突しない
    assert len({r.call_id for r in rows}) == len(rows)
    day1 = [r for r in rows if r.tick >= TPD]
    assert all(r.call_id.startswith(f"{r.tick}:") for r in day1)


# ================================================================= (i) 不応期
def test_refractory_set_at_2350_expires_at_0010_next_day():
    cal = SimCalendar(datetime(2026, 7, 27))
    t_set = cal.to_T(0, 23 * 60 + 50)           # 1 日目 23:50
    cond = int(WakeCondition.CELL_BLOCK)
    table = np.zeros(N_WAKE_CONDITIONS, dtype=np.int32)
    table[cond] = 20                              # 20 分の不応期
    agents = AgentState(2)
    agents.freeze()
    R.set_refractory(agents, np.array([0]), np.array([cond]), t_set, table)
    assert int(agents.registry.refractory_until[0, cond]) == cal.to_T(1, 10)   # 2 日目 0:10

    def selected(T: int) -> bool:
        arb = Arbiter(2, run_salt_for(1), 10.0)
        cands = WakeCandidates(np.array([0]), np.array([cond], dtype=np.int8),
                               np.array([int(EventClass.INDIVIDUAL)]), np.array([T]))
        return 0 in arb.step(T, cands, agents.registry.refractory_until).selected.agent_id.tolist()

    assert not selected(cal.to_T(1, 9))           # 2 日目 0:09 はまだ抑止
    assert selected(cal.to_T(1, 10))              # 2 日目 0:10 に切れる
    assert not selected(cal.to_T(0, 23 * 60 + 59))


# ================================================================= (ii) 会話の辺の経過時間
def test_conversation_edge_age_is_120_minutes_across_midnight():
    cal = SimCalendar(datetime(2026, 7, 27))
    agents = AgentState(3, memory_columns=True, relation_columns=True, rel_k=4)
    agents.freeze()
    rel = RelationLayer(3, 4, minutes_per_tick=1.0)
    t23 = cal.to_T(0, 23 * 60)                    # 1 日目 23:00
    t01 = cal.to_T(1, 60)                         # 2 日目 1:00
    rel.on_episodes(agents, t23, np.array([0]), np.array([7]), np.array([1]), np.array([int(ResultCode.OK)]))
    r = agents.registry
    slot = int(np.flatnonzero(r.rel_partner[0] == 1)[0])
    assert int(r.rel_last[0, slot]) == t23 and int(r.rel_first[0, slot]) == t23
    assert (t01 - int(r.rel_last[0, slot])) * rel.minutes_per_tick == 120.0
    A = rel.activation(agents, np.array([0]), t01)[0, slot]
    assert A == pytest.approx(np.log(1.0 / (1.0 - rel.d)) - rel.d * np.log(120.0 + 1.0))


# ================================================================= (iii) 2 日目の乱数
def test_day2_draws_differ_from_day1_for_the_same_tick_and_agent():
    t = 9 * 60
    T2 = t + TPD
    mock = MockLLM(1)
    diff = 0
    for a in range(50):
        req1 = LLMRequest(prompt="x", agent_id=a, tick=t, wake_class=int(EventClass.INDIVIDUAL))
        req2 = LLMRequest(prompt="x", agent_id=a, tick=T2, wake_class=int(EventClass.INDIVIDUAL))
        diff += mock._draws(req1) != mock._draws(req2)  # noqa: SLF001 - 乱数の鍵だけを見る
    assert diff == 50
    p = np.full(7, 1.0 / 7)
    picks = [(draw_index(p, 1, t, a), draw_index(p, 1, T2, a)) for a in range(200)]
    assert sum(x != y for x, y in picks) > 100     # 選び手の乱数(同じなら 0)
    salt = run_salt_for(1)
    ag = np.arange(100)
    k1 = apply_key_array(salt, np.full(100, t), ag)
    k2 = apply_key_array(salt, np.full(100, T2), ag)
    assert not np.array_equal(np.argsort(k1), np.argsort(k2))   # 適用順の鍵
    assert np.all(k1 != k2)


# ================================================================= (iv) 経過時間が負にならない
def test_no_negative_elapsed_time_in_any_tick_column_every_tick(monkeypatch):
    seen: dict[str, object] = {}
    orig_conv = RUN.ConversationManager
    orig_arb = RUN.Arbiter
    orig_runner = RUN.WorldProcessRunner
    orig_enable = RUN.MemoryLayer.enable_relations

    def conv_factory(*a, **k):
        seen["conv"] = obj = orig_conv(*a, **k)
        return obj

    def arb_factory(*a, **k):
        seen["arb"] = obj = orig_arb(*a, **k)
        return obj

    def runner_factory(*a, **k):
        seen["runner"] = obj = orig_runner(*a, **k)
        return obj

    def enable(self, *a, **k):
        seen["rel"] = obj = orig_enable(self, *a, **k)
        return obj

    monkeypatch.setattr(RUN, "ConversationManager", conv_factory)
    monkeypatch.setattr(RUN, "Arbiter", arb_factory)
    monkeypatch.setattr(RUN, "WorldProcessRunner", runner_factory)
    monkeypatch.setattr(RUN.MemoryLayer, "enable_relations", enable)

    refr_max = int(np.max(R.refractory_ticks()))
    until_cap = int(np.ceil(UNTIL_MAX_MINUTES)) + 1
    orig_advance = R.advance_body
    checked = {"ticks": 0}

    def check(agents, T: int) -> None:
        r = agents.registry
        for name in SINCE_COLUMNS:
            v = np.asarray(getattr(r, name), dtype=np.int64)
            assert int(v.max(initial=-1)) <= T, (name, T)
        assert int(np.asarray(r.refractory_until).max()) <= T + refr_max
        assert int(np.asarray(r.activity_until).max()) <= T + until_cap
        # SoA の外: 会話の不応期・返事待ち・セッション・アービタの保留・同席・知人出現・顕著行為を見た tick
        conv = seen["conv"]
        assert all(s.opened_tick <= T and s.last_utterance_tick <= T for s in conv.sessions.values())
        assert all(p.tick <= T for p in conv.pending_invites.values())
        assert all(u <= T + conv.refusal_memory_ticks + 60 for u in conv._refusal_until.values())  # noqa: SLF001
        pend = seen["arb"].pending
        assert int(np.asarray(pend.since_tick, dtype=np.int64).max(initial=-1)) <= T
        rel = seen["rel"]
        assert int(np.asarray(rel._co_since, dtype=np.int64).max(initial=-1)) <= T            # noqa: SLF001
        assert int(np.asarray(rel._co_day, dtype=np.int64).max(initial=-1)) <= T // TPD        # noqa: SLF001
        assert int(np.asarray(rel._acq_until, dtype=np.int64).max(initial=-1)) <= T + 60       # noqa: SLF001
        sal = seen["runner"].salient
        assert int(np.asarray(sal.event_seen_tick, dtype=np.int64).max(initial=-1)) <= T

    def advance(agents, tick, energy_layer=None):
        # tick の頭=前の tick の書き込みが済んだ時点(値は T−1 以下のはず・T 以下で見る)
        check(agents, int(tick))
        checked["ticks"] += 1
        return orig_advance(agents, tick, energy_layer)

    monkeypatch.setattr(R, "advance_body", advance)
    res = _run(2, rel_acq_wake="on", **ALL_ARMS)
    check(res.agents, 2 * TPD - 1)
    assert checked["ticks"] == 2 * TPD
    r = res.agents.registry
    # 2 日目にも各列が書かれている(検査が空回りしていない)
    assert int(np.asarray(r.last_result_tick).max()) >= TPD
    assert int(np.asarray(r.mem_tick).max()) >= TPD and int(np.asarray(r.rel_last).max()) >= TPD
    # 同席の「1 日 1 本」が 2 日目にも書かれる(日番号が T から出る=常に 0 日目、の穴が無い)
    assert int(np.asarray(seen["rel"]._co_day).max()) == 1  # noqa: SLF001


# ================================================================= 型
def test_tick_columns_can_hold_30_days_of_T():
    agents = AgentState(2, plan_columns=True, edge_columns=True, attention_columns=True, activity_columns=True,
                        familiarity_columns=True, energy_columns=True, memory_columns=True,
                        store_memory_columns=True, relation_columns=True)
    r = agents.registry
    T30 = 30 * TPD
    assert T30 == 43_200
    for name in TICK_COLUMNS:
        dt = np.asarray(getattr(r, name)).dtype
        info = np.iinfo(dt)
        assert info.max >= T30 + 10 * TPD and info.min < 0, (name, dt)   # 30 日+先の時刻・負の過去
    # SoA の外の numpy の行も同じ
    rel = RelationLayer(2, 4)
    rel.enable_copresent()
    rel.enable_acquaintance_wake()
    assert np.iinfo(rel._co_since.dtype).max >= T30         # noqa: SLF001
    assert np.iinfo(rel._co_day.dtype).max >= 30             # noqa: SLF001
    assert np.iinfo(rel._acq_until.dtype).max >= T30         # noqa: SLF001
    from shibuya.agents.schedule import synthesize
    from shibuya.engine.processes.runner import WorldProcessRunner

    w = World.synthetic(n_cells=9, seed=1)
    runner = WorldProcessRunner(world=w, agents=agents, seed=1, schedule=synthesize(2, 1, w.n_cells))
    assert np.iinfo(runner.salient.event_seen_tick.dtype).max >= T30


# ================================================================= 日の中の時刻で引く表
def test_next_boundary_tables_are_read_by_tick_of_day():
    w = World.synthetic(n_cells=9, seed=1)
    layer = ActivityLayer(2, w, run_salt_for(1), tick_seconds=60,
                          boundary_agent=np.array([0, 0]), boundary_tick=np.array([420, 1_200]))
    assert layer._next_boundary(0, 600) == 1_200                     # noqa: SLF001 - 0 日目は今と同じ値
    assert layer._next_boundary(0, TPD + 600) == TPD + 1_200         # noqa: SLF001 - 2 日目はその日の頭を足す
    assert layer._next_boundary(0, TPD + 1_300) == -1                # noqa: SLF001 - その日の中に無ければ −1
    assert layer._next_boundary(1, TPD + 600) == -1                  # noqa: SLF001


def test_classical_and_store_choice_read_the_next_plan_by_tick_of_day():
    from shibuya.engine import classical as CL
    from shibuya.engine.store_choice import StoreChoice

    doc, md5 = CL.load_activity_prior()
    w = World.synthetic(n_cells=9, seed=1)
    a = AgentState(2)
    pol = CL.ClassicalPolicy(seed=1, prior=CL.ActivityPrior(doc, "weekday", "kanto"), prior_md5=md5)
    pol.bind(agents=a, world=w, home_cell=np.full(2, 1), work_cell=np.full(2, 2), school_cell=np.full(2, -1),
             has_work=np.zeros(2, dtype=bool), boundary_agent=np.array([0, 0]),
             boundary_tick=np.array([420, 1_200]))
    assert pol._next_plan_minutes(0, 600) == 600                       # noqa: SLF001 - 0 日目(今と同じ)
    assert pol._next_plan_minutes(0, TPD + 600) == 600                 # noqa: SLF001 - 2 日目も同じ間隔
    assert pol._next_plan_minutes(0, TPD + 1_300) == 10_000            # noqa: SLF001
    sc = StoreChoice.__new__(StoreChoice)          # 表の引き当てだけを見る(記憶の表は要らない)
    sc._b_off = np.array([0, 2, 2])                                    # noqa: SLF001
    sc._b_tick = np.array([420, 1_200])                                # noqa: SLF001
    sc._tpd = TPD                                                      # noqa: SLF001
    assert sc.ticks_to_next_plan(0, 600) == sc.ticks_to_next_plan(0, TPD + 600) == 600
    assert sc.ticks_to_next_plan(0, TPD + 1_300) == 1 << 30


def test_out_of_area_meals_repeat_by_tick_of_day():
    anc, md5 = load_anchors()
    model = EnergyModel(anc, md5, minutes_per_tick=1.0)
    meals = OutOfAreaMeals(model, 4, TPD)
    ts = np.full(4, 2, dtype=np.int8)                 # 全員域外
    for t in (int(model.default_meal_min["breakfast"]), int(model.default_meal_min["dinner"])):
        a0, s0, _ = meals.due(t, ts)
        a1, s1, _ = meals.due(t + TPD, ts)
        assert a0.size == 4 and np.array_equal(a0, a1) and np.array_equal(s0, s1)


# ================================================================= 口の制限と manifest
def test_multi_day_mouth_refuses_what_needs_the_day_head():
    with pytest.raises(ValueError, match="1 日の tick 数"):
        run_day(n_agents=10, n_cells=9, ticks=600, sim_days=2)
    with pytest.raises(ValueError, match="sim_days で"):
        run_day(n_agents=10, n_cells=9, ticks=TPD + 1)
    with pytest.raises(ValueError, match="世界資産"):
        run_day(n_agents=10, n_cells=9, ticks=TPD, sim_days=2, world_dir="data/world/v2")
    with pytest.raises(ValueError, match="再生"):
        run_day(n_agents=10, n_cells=9, ticks=TPD, sim_days=2, mode="replay", replay=None)
    with pytest.raises(ValueError):
        run_day(n_agents=10, n_cells=9, ticks=TPD, sim_days=0)


def test_manifest_records_tick_seconds_and_start():
    res = run_day(n_agents=20, seed=1, n_cells=9, ticks=30, checkpoint_every=10)
    m = res.run_manifest_fields()
    assert m["tick_seconds"] == 60
    assert m["start_sim_datetime"] == "2026-07-28T00:00:00"     # 合成世界=気象の再生実日なし=既定の開始日
    assert m["sim_days"] == 1 and m["response_delay"] == 1
    cal = m["calendar"]
    assert cal["calendar_weekday"] == "day_index" and cal["day_index"] == 0
    assert cal["days"][0]["weekday"] == 0 and cal["start_check"] == []
    assert "holiday_csv" in cal and "holiday_csv_md5" in cal


def test_real_calendar_run_needs_a_valid_start(tmp_path):
    from tests.engine.test_calendar import write_csv

    csv = write_csv(tmp_path / "h.csv")
    with pytest.raises(ValueError, match="開始日"):
        run_day(n_agents=10, n_cells=9, ticks=10, calendar_weekday="real", holiday_csv=csv)
    with pytest.raises(ValueError, match="祝日"):
        run_day(n_agents=10, n_cells=9, ticks=10, calendar_weekday="real", holiday_csv=csv,
                start_sim_datetime="2026-07-20")
    res = run_day(n_agents=10, n_cells=9, ticks=10, calendar_weekday="real", holiday_csv=csv,
                  start_sim_datetime="2026-08-03")
    m = res.run_manifest_fields()
    assert m["start_sim_datetime"] == "2026-08-03T00:00:00"
    assert m["calendar"]["calendar_weekday"] == "real" and m["calendar"]["days"][0]["weekday"] == 0


def test_start_date_moves_the_prompt_clock(tmp_path):
    """開始日を渡すとプロンプトの日付(世界内日時)がその日になる。渡さないランは今の日付のまま。"""
    from shibuya.perception.renderer import Renderer as PR

    seen = []
    orig = PR.__init__

    def init(self, *a, **k):
        orig(self, *a, **k)
        seen.append(self)

    mp = pytest.MonkeyPatch()
    mp.setattr(PR, "__init__", init)
    try:
        run_day(n_agents=10, n_cells=9, ticks=5, start_sim_datetime="2026-08-03")
        run_day(n_agents=10, n_cells=9, ticks=5)
    finally:
        mp.undo()
    assert seen[0].clock_fn(TPD + 90) == datetime(2026, 8, 4, 1, 30)
    assert seen[1].clock_fn(90) == datetime(2026, 7, 28, 1, 30)


def test_school_holiday_in_day_index_mode_only_warns():
    from shibuya.engine.calendar import CalendarWarning

    with pytest.warns(CalendarWarning, match="学校の長期休み"):
        res = run_day(n_agents=10, n_cells=9, ticks=5, school_holidays="2026-07-21:2026-08-31")
    assert res.run_manifest_fields()["calendar"]["school_holidays"] == [["2026-07-21", "2026-08-31"]]
    assert res.run_manifest_fields()["calendar"]["start_check"]
