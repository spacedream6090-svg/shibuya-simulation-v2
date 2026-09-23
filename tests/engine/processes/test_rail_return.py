"""D-61 域内居住者の帰りの便(2026-09-10・ユーザー決定 (a))のテスト。

規則(``engine.processes.rail.RailProcess._assign_return``)
- 発車で域外へ出た乗客のうち**渋谷に家がある個体**(``external_line < 0``)に、
  週次表(W17)の「その tick より後の最初の域内活動(``target_cell >= 0``)」の開始分
  ``want`` を引き、**ホームへ入る時刻 ``dep_tick - dwell + 1`` が ``want`` 以上で最も早い便**を
  割り当てる(線は選ばない=渋谷は 1 駅・同着は便索引の昇順)。
- 次の域内活動が無い / ``want`` 以降の便が無い(終電後)= **その日は戻らない**。
"""

from __future__ import annotations

import numpy as np

from shibuya.agents.schedule import synthesize
from shibuya.agents.weekly import (
    N_DAYS,
    PLACE_KIND_OUTSIDE,
    PLACE_WORDS,
    WeeklySchedule,
    apply_to_mock_schedule,
)
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.processes.civic import EVENT_WINDOW, LargeEventProcess
from shibuya.engine.processes.rail import RailProcess

from .conftest import fake_timetable_assets, make_agents, make_world


# ------------------------------------------------------------------ フィクスチャ
def _weekly(n_agents: int, acts: dict, day: int = 0):
    """手書きの週次表。``acts[i]`` = 体 ``i`` の ``day`` の ``(開始分, 終了分, 行き先セル[, 場所])``。

    場所は ``PLACE_WORDS`` の索引(既定 0=自宅)。**D-61 追補**で「域内活動」の定義は
    ``place_kind != 域外`` になったので、行き先セル ``-1`` でも域外でなければ数える。
    """
    starts: list[int] = []
    ends: list[int] = []
    cells: list[int] = []
    places: list[int] = []
    seqs: list[int] = []
    counts = np.zeros(n_agents * N_DAYS, dtype=np.int64)
    for i in range(n_agents):
        rows = acts.get(i, ())
        counts[i * N_DAYS + day] = len(rows)
        for s, row in enumerate(rows):
            st, en, cell = row[0], row[1], row[2]
            starts.append(st)
            ends.append(en)
            cells.append(cell)
            places.append(row[3] if len(row) > 3 else 0)
            seqs.append(s)
    offset = np.zeros(n_agents * N_DAYS + 1, dtype=np.int64)
    np.cumsum(counts, out=offset[1:])
    m = len(starts)
    return WeeklySchedule(
        source=None,
        agent_id=np.arange(n_agents, dtype=np.int64),
        day_offset=offset,
        start_min=np.asarray(starts, dtype=np.int16).reshape(m),
        end_min=np.asarray(ends, dtype=np.int16).reshape(m),
        activity=np.zeros(m, dtype=np.int8),
        place_kind=np.asarray(places, dtype=np.int8).reshape(m),
        target_cell=np.asarray(cells, dtype=np.int32).reshape(m),
        seq=np.asarray(seqs, dtype=np.int16).reshape(m),
    )


def _rail(n_agents: int = 20, *, weekly=None, departures=(100, 200, 300)):
    """1 路線(山手線・通過型 1 tick)の最小ダイヤ。便 k のホーム在線 tick = ``departures[k]``。"""
    world = make_world(9)
    agents, schedule = make_agents(world, n_agents)
    pa = fake_timetable_assets(platform_cell=0, departures=departures, lines=("山手線",))
    rail = RailProcess(
        world, agents, pa, master_seed=1, day_index=0, schedule=schedule, weekly=weekly
    )
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


def _board(world, agents, rail, ids, tick: int) -> None:
    """ホームへ置いて乗車させる(``resolve`` の口を通す)。"""
    a = np.asarray(ids, dtype=np.int64)
    R.rail_arrive(agents, world, a, np.zeros(a.size, dtype=np.int64))
    R.apply(_intents(a, C.ACT_BOARD), C.IntentBatch.empty(), agents, world, tick, rail=rail)


def _domestic(rail, k: int = 1) -> np.ndarray:
    """域内に家がある体を ``k`` 人(``external_line < 0``)。"""
    return np.flatnonzero(rail.external_line < 0)[:k]


# ================================================================= (i) 帰りの便で戻る
def test_home_in_bbox_rider_returns_on_the_first_train_after_the_next_activity():
    """次の域内活動が 250 分 → ``enter_tick >= 250`` の最初の便(300)で降りる。"""
    world, agents, rail = _rail()
    a0 = _domestic(rail)
    rail.attach_weekly(_weekly(20, {int(a0[0]): ((250, 400, 3),)}))
    _board(world, agents, rail, a0, 100)
    assert agents.registry.transit_state[a0[0]] == 1  # 乗車中

    rail.step(101)  # 便 0(dep 100)が発車 → 域外へ + 帰りの便を割り当て
    assert agents.registry.transit_state[a0[0]] == 2
    assert rail.n_return_scheduled == 1 and rail.n_no_return == 0
    assert int(rail.arrival_train[a0[0]]) == 2  # 便 2 = dep 300(enter 300 >= 250)

    for t in range(102, 300):
        rail.step(t)
        assert agents.registry.transit_state[a0[0]] == 2, f"tick {t} で早く戻った"
    rail.step(300)  # 便 2 がホームへ入る tick
    assert agents.registry.transit_state[a0[0]] == 0
    assert int(agents.registry.cell[a0[0]]) == 0  # ホームのセル
    assert rail.n_return_arrived == 1 and rail.n_arrivals == 1
    assert rail.counters()["return_scheduled"] == 1.0
    assert rail.counters()["return_arrived"] == 1.0
    assert "帰りの便 1" in rail.summary()


def test_the_train_chosen_is_the_earliest_one_at_or_after_the_activity_start():
    """開始 200 ちょうど → ``enter_tick == 200`` の便(その時刻の便を飛ばさない)。"""
    world, agents, rail = _rail()
    a0 = _domestic(rail)
    rail.attach_weekly(_weekly(20, {int(a0[0]): ((200, 400, 3),)}))
    _board(world, agents, rail, a0, 100)
    rail.step(101)
    assert int(rail.arrival_train[a0[0]]) == 1  # 便 1 = dep 200
    rail.step(200)
    assert agents.registry.transit_state[a0[0]] == 0
    assert rail.n_return_arrived == 1


def test_unresolved_cell_activities_still_call_the_rider_back():
    """**(vi) D-61 追補**: ``target_cell < 0`` でも ``place_kind != 域外`` なら域内活動。

    W17 の「自宅」の 84% はセル未解決なので、逐語定義(``target_cell >= 0``)だと
    27.8% しか戻らなかった(登録簿 §8 D-61 の所見)。
    """
    world, agents, rail = _rail()
    a0 = _domestic(rail)
    # 200 分に「駅」(セル未解決)・250 分に「自宅」(セル解決)→ **200 の方**で呼び戻す
    rail.attach_weekly(
        _weekly(20, {int(a0[0]): ((200, 240, -1, PLACE_WORDS.index("駅")), (250, 400, 3))})
    )
    _board(world, agents, rail, a0, 100)
    rail.step(101)
    assert int(rail.arrival_train[a0[0]]) == 1  # 便 1 = dep 200(未解決セルの活動で戻る)
    rail.step(200)
    assert agents.registry.transit_state[a0[0]] == 0
    assert rail.n_return_arrived == 1


def test_activities_outside_the_bbox_do_not_call_the_rider_back():
    """``place_kind == 域外`` の活動は域内活動ではない(域外に居たままでよい)。"""
    world, agents, rail = _rail()
    a0 = _domestic(rail)
    out = PLACE_WORDS.index("域外")
    rail.attach_weekly(
        _weekly(20, {int(a0[0]): ((150, 180, -1, out), (250, 400, -1, out))})
    )
    _board(world, agents, rail, a0, 100)
    rail.step(101)
    assert rail.n_return_scheduled == 0 and rail.n_no_return == 1


# ================================================================= (ii) 戻らない
def test_rider_without_a_next_in_bbox_activity_stays_outside():
    world, agents, rail = _rail()
    a0 = _domestic(rail)
    rail.attach_weekly(_weekly(20, {int(a0[0]): ((30, 90, 3),)}))  # 発車より前の活動しか無い
    _board(world, agents, rail, a0, 100)
    rail.step(101)
    assert rail.n_return_scheduled == 0
    assert rail.n_no_return == 1 and rail.n_return_no_train == 0
    for t in range(102, 1_000):
        rail.step(t)
    assert agents.registry.transit_state[a0[0]] == 2  # その日は戻らない(保存則の分母)
    assert rail.counters()["no_return"] == 1.0


def test_rider_whose_activity_is_after_the_last_train_stays_outside():
    """終電後(``want`` 以降にホームへ入る便が無い)も戻らない=``return_no_train``。"""
    world, agents, rail = _rail()
    a0 = _domestic(rail)
    rail.attach_weekly(_weekly(20, {int(a0[0]): ((1_200, 1_300, 3),)}))  # 最終便 300 より後
    _board(world, agents, rail, a0, 100)
    rail.step(101)
    assert rail.n_return_scheduled == 0
    assert rail.n_no_return == 1 and rail.n_return_no_train == 1
    for t in range(102, 1_000):
        rail.step(t)
    assert agents.registry.transit_state[a0[0]] == 2


def test_without_a_weekly_table_nobody_comes_back():
    """週次表の無いラン(合成世界・``--no-population``)= D-61 前の挙動のまま。"""
    world, agents, rail = _rail()
    a0 = _domestic(rail)
    _board(world, agents, rail, a0, 100)
    rail.step(101)
    assert rail.n_return_scheduled == 0 and rail.n_no_return == 1
    for t in range(102, 400):
        rail.step(t)
    assert agents.registry.transit_state[a0[0]] == 2


# ================================================================= (iii) 事前割当が壊れない
def test_the_static_pre_assignment_of_external_residents_still_works():
    """域外居住者の**事前割当**(``_arr_order``/``_arr_start``)は帰りの便と混ざらない。"""
    world, agents, rail = _rail(n_agents=60)
    ext = rail.external_home_agents()
    assert ext.size > 0
    served = ext[rail.arrival_train[ext] >= 0]
    assert served.size > 0
    rail.attach_weekly(_weekly(60, {int(i): ((250, 400, 3),) for i in range(60)}))
    R.place_at_external(agents, ext, rail.external_line[ext])
    for t in range(0, 400):
        rail.step(t)
    assert rail.n_arrivals == int(served.size)
    assert rail.n_return_arrived == 0  # 域外居住者は帰りの便の対象外
    assert rail.n_return_scheduled == 0
    assert np.all(agents.registry.transit_state[served] == 0)


def test_external_residents_are_never_assigned_a_return_train():
    """域外居住者が乗って出ても、帰りの便は**割り当てない**(事前割当の便で戻る)。"""
    world, agents, rail = _rail(n_agents=60)
    ext = rail.external_home_agents()[:2]
    rail.attach_weekly(_weekly(60, {int(i): ((250, 400, 3),) for i in range(60)}))
    _board(world, agents, rail, ext, 100)
    before = rail.arrival_train[ext].copy()
    rail.step(101)
    assert rail.n_return_scheduled == 0 and rail.n_no_return == 0
    assert np.array_equal(rail.arrival_train[ext], before)  # 事前割当を上書きしない


# ================================================================= (iv) 乗客の保存則
def test_rider_conservation_holds_on_every_tick():
    """在圏 + 乗車中 + 域外 = 個体数(全 tick)。"""
    world, agents, rail = _rail(n_agents=60)
    ext = rail.external_home_agents()
    R.place_at_external(agents, ext, rail.external_line[ext])
    dom = _domestic(rail, 5)
    rail.attach_weekly(_weekly(60, {int(i): ((250, 400, 3),) for i in dom.tolist()}))
    for t in range(0, 400):
        if t == 100:
            _board(world, agents, rail, dom, 100)
        rail.step(t)
        inb, riding, outside = rail.rider_census()
        assert inb + riding + outside == agents.n, f"tick {t} で保存則が破れた"
    assert rail.n_return_arrived == int(dom.size)


# ================================================================= (v) 決定論
def test_two_identical_runs_agree_bit_for_bit():
    def run():
        world, agents, rail = _rail(n_agents=60)
        ext = rail.external_home_agents()
        R.place_at_external(agents, ext, rail.external_line[ext])
        dom = _domestic(rail, 5)
        rail.attach_weekly(
            _weekly(
                60, {int(i): ((150 + 20 * k, 400, 3),) for k, i in enumerate(dom.tolist())}
            )
        )
        trace: list[tuple[int, int, int]] = []
        for t in range(0, 400):
            if t == 100:
                _board(world, agents, rail, dom, 100)
            rail.step(t)
            trace.append(rail.rider_census())
        return trace, rail.counters(), rail.arrival_train.copy()

    t1, c1, a1 = run()
    t2, c2, a2 = run()
    assert t1 == t2
    assert c1 == c2
    assert np.array_equal(a1, a2)


# ============================================== (vii) 大規模イベントの迂回を塞ぐ(D-61 追補)
def _event(world, agents, rail, *, visitors: int = 5):
    return LargeEventProcess(
        world, agents, rail=rail, master_seed=1, day_index=0, visitor_delta=visitors
    )


def test_event_leavers_get_a_return_train():
    """21:00 の退場(``rail_depart`` 直呼び)にも帰りの便が付く。"""
    lo, hi = EVENT_WINDOW
    world, agents, rail = _rail(n_agents=40, departures=(hi + 40, hi + 90))
    ext = rail.external_home_agents()
    R.place_at_external(agents, ext, rail.external_line[ext])
    dom_out = _domestic(rail, 5)  # 域外に居る**域内居住者**(会場へ引き込む在庫)
    R.place_at_external(agents, dom_out, np.zeros(dom_out.size, dtype=np.int64))
    rail.attach_weekly(_weekly(40, {int(i): ((hi + 30, 1_400, 3),) for i in range(40)}))
    ev = _event(world, agents, rail)
    ev.step(lo)  # 18:00 入場
    assert ev.counters()["arrived"] > 0
    inside = ev._inside.copy()
    ev.step(hi)  # 21:00 退場 → 帰りの便を頼む
    assert np.all(agents.registry.transit_state[inside] == 2)
    dom = inside[rail.external_line[inside] < 0]
    assert dom.size > 0
    assert rail.n_return_scheduled == int(dom.size)
    for t in range(hi + 1, hi + 120):
        rail.step(t)
    assert np.all(agents.registry.transit_state[dom] == 0)  # ホームへ降りて在圏
    assert rail.n_return_arrived == int(dom.size)
    inb, riding, outside = rail.rider_census()
    assert inb + riding + outside == agents.n


def test_event_arrivals_are_dropped_from_the_return_queue():
    """18:00 に会場へ引き込まれた体の**古い割当**は発火しない(二重到着・早戻りなし)。"""
    lo, hi = EVENT_WINDOW
    # 便: 100(乗る)/ 1_290(古い割当が発火しうる時刻)
    world, agents, rail = _rail(n_agents=40, departures=(100, hi + 30))
    a0 = _domestic(rail, 3)
    # 次の域内活動 = 21:10 → 便 1(dep 1_290)を予約する
    rail.attach_weekly(_weekly(40, {int(i): ((hi + 10, 1_400, 3),) for i in a0.tolist()}))
    _board(world, agents, rail, a0, 100)
    rail.step(101)
    assert rail.n_return_scheduled == int(a0.size)
    assert np.all(rail.arrival_train[a0] == 1)
    ev = _event(world, agents, rail, visitors=40)
    ev.step(lo)  # 18:00: 域外の体を会場へ(予約が外れる)
    assert np.all(rail.arrival_train[a0] == -1)
    assert np.all(agents.registry.transit_state[a0] == 0)
    # 会場から出さずに便 1 の到着 tick を跨いでも、二重到着も保存則の崩れも起きない
    for t in range(lo + 1, hi + 40):
        rail.step(t)
        inb, riding, outside = rail.rider_census()
        assert inb + riding + outside == agents.n
    assert rail.n_return_arrived == 0


# ================================================================= 週次表側の索引
def test_inbound_starts_skips_only_outside_activities_and_orders_by_minute():
    """**D-61 追補**: 落とすのは ``place_kind == 域外`` の行だけ(未解決セルは残す)。"""
    w = _weekly(
        3,
        {
            0: ((100, 200, 5), (400, 500, -1, PLACE_KIND_OUTSIDE), (600, 700, 7)),
            2: ((50, 60, -1, PLACE_WORDS.index("飲食店")),),
        },
    )
    idx = w.inbound_starts(0)
    assert idx.n_starts == 3  # 域外の 1 行だけ入らない(未解決セルの飲食店は入る)
    assert idx.offset.tolist() == [0, 2, 2, 3]
    assert idx.next_after([0, 0, 0, 1, 2], [0, 100, 600, 0, 0]).tolist() == [100, 600, -1, -1, 50]
    # 範囲外の体行・別の曜日は -1
    assert idx.next_after([3, -1], 0).tolist() == [-1, -1]
    assert w.inbound_starts(1).n_starts == 0


def test_apply_to_mock_schedule_attaches_the_weekly_table_for_the_rail_process():
    """D-61 の結線: ``run.py`` を変えずに鉄道へ週次表を届ける口。"""
    mock = synthesize(4, 1, 9)
    w = _weekly(4, {0: ((100, 200, 5),)})
    out = apply_to_mock_schedule(mock, w, 0)
    assert getattr(mock, "weekly", None) is w  # runner が握っている**置き換え前**の実体
    assert getattr(out, "weekly", None) is w
