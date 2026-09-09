"""W17 段2: 整合修復の 7 規則・骸格フォールバック・raking(答申 Q4-2 段2/段3)。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya.build.sched import vocab as V
from shibuya.build.sched import w17_schedule as W17


@pytest.fixture()
def facts(world_dir: Path, data_dir: Path) -> W17.AgentFacts:
    return W17.build_facts(world_dir, data_dir)


@pytest.fixture()
def share(world_dir: Path) -> np.ndarray:
    return W17.open_share(world_dir)


def _row(facts: W17.AgentFacts, agent_id: int) -> int:
    return int(np.flatnonzero(facts.agent_id == agent_id)[0])


# ---------------------------------------------------------------- 1/2 範囲・重なり
def test_overlap_is_resolved_by_shifting_the_later_block(facts, share):
    ctr = W17.RepairCounters()
    acts = [
        V.Act(0, 540, 720, V.ACT_WORK, V.PLACE_WORK),
        V.Act(0, 600, 780, V.ACT_MEAL, V.PLACE_FOOD),
    ]
    out, flags, dropped = W17.repair_day(acts, facts, _row(facts, 1), 0, share, ctr)
    assert len(flags) == len(out)
    starts = [a.start for a in out]
    assert starts == sorted(starts)
    for a, b in zip(out, out[1:]):
        assert a.end <= b.start
    assert any(flags) and ctr.counts.get("overlap_shifted", 0) >= 1


def test_zero_length_and_out_of_range_are_dropped(facts, share):
    ctr = W17.RepairCounters()
    acts = [V.Act(0, 1_430, 1_600, V.ACT_REST, V.PLACE_HOME)]
    out, flags, dropped = W17.repair_day(acts, facts, _row(facts, 1), 0, share, ctr)
    assert all(a.end <= V.MINUTES_PER_DAY for a in out)
    assert ctr.counts.get("clamped", 0) == 1


def test_too_many_activities_are_capped(facts, share):
    ctr = W17.RepairCounters()
    acts = [V.Act(0, 60 * i, 60 * i + 30, V.ACT_REST, V.PLACE_HOME) for i in range(14)]
    out, flags, dropped = W17.repair_day(acts, facts, _row(facts, 1), 0, share, ctr)
    assert len(out) <= W17.MAX_ACTS_PER_DAY + 1  # +1 = 就寝の補い
    assert ctr.counts.get("too_many", 0) > 0


# ---------------------------------------------------------------- 4 勤務窓
def test_duty_is_clamped_into_the_plan_spec_window(facts, share):
    """勤務は本人の勤務窓(PlanSpec/シフト)の中へ丸める。"""
    ctr = W17.RepairCounters()
    row = _row(facts, 1)  # 09:00-18:00 平日
    out, flags, dropped = W17.repair_day(
        [V.Act(0, 300, 1_380, V.ACT_WORK, V.PLACE_WORK)], facts, row, 0, share, ctr
    )
    work = [a for a in out if a.activity == V.ACT_WORK]
    assert work and work[0].start >= int(facts.work_open[row])
    assert work[0].end <= int(facts.work_close[row])
    assert ctr.counts.get("duty_clamped", 0) == 1


def test_duty_on_a_non_working_day_becomes_rest_at_home(facts, share):
    ctr = W17.RepairCounters()
    row = _row(facts, 1)
    out, flags, dropped = W17.repair_day(
        [V.Act(5, 540, 1_080, V.ACT_WORK, V.PLACE_WORK)], facts, row, 5, share, ctr
    )
    assert all(a.activity != V.ACT_WORK for a in out)
    assert ctr.counts.get("duty_off_day", 0) == 1


# ---------------------------------------------------------------- 5 営業エンベロープ
def test_leisure_outside_opening_hours_is_moved(facts, share):
    """閉店中(開店率 < 5%)に始まる店内活動は同じ日の最寄りの開店時間帯へ動く。"""
    ctr = W17.RepairCounters()
    row = _row(facts, 0)  # 非就業の居住者
    out, flags, dropped = W17.repair_day(
        [V.Act(0, 180, 240, V.ACT_LEISURE, V.PLACE_LEISURE)], facts, row, 0, share, ctr
    )
    moved = [a for a in out if a.activity == V.ACT_LEISURE]
    assert ctr.counts.get("closed_moved", 0) == 1
    assert moved and share[V.PLACE_LEISURE, 0, moved[0].start // 60] >= W17.OPEN_SHARE_MIN


def test_open_24h_shop_is_never_moved(facts, share):
    """24 時間営業のコンビニがある物販店は深夜でも動かさない(閾値の陰性側)。"""
    ctr = W17.RepairCounters()
    out, flags, dropped = W17.repair_day(
        [V.Act(0, 180, 240, V.ACT_SHOP, V.PLACE_SHOP)], facts, _row(facts, 0), 0, share, ctr
    )
    assert ctr.counts.get("closed_moved", 0) == 0
    assert any(a.activity == V.ACT_SHOP and a.start == 180 for a in out)


def test_open_share_is_built_from_plan_spec(world_dir: Path):
    sh = W17.open_share(world_dir)
    assert sh.shape == (len(V.PLACE_WORDS), 7, 24)
    assert sh[V.PLACE_SHOP, 0, 12] > 0  # 10-22 時の物販店 + 24h コンビニ
    assert sh[V.PLACE_FOOD, 0, 3] == 0  # 深夜の飲食店は無い
    assert sh[V.PLACE_LEISURE, 0, 3] == 0  # 娯楽施設は 12-23 時
    assert sh[V.PLACE_SHOP, 0, 3] > 0  # コンビニは終日


# ---------------------------------------------------------------- 6 来街者
def test_visitor_keeps_only_visit_days_with_entry_and_exit(facts, share):
    ctr = W17.RepairCounters()
    row = _row(facts, 4)
    visit = int(np.flatnonzero([(int(facts.visit_days[row]) >> d) & 1 for d in range(7)])[0])
    other = (visit + 1) % 7
    acts = [V.Act(visit, 660, 780, V.ACT_SHOP, V.PLACE_SHOP)]
    out, flags, dropped = W17.repair_day(acts, facts, row, visit, share, ctr)
    assert out[0].activity == V.ACT_RIDE and out[0].place == V.PLACE_STATION
    assert out[-1].place == V.PLACE_OUTSIDE
    empty, _, _ = W17.repair_day(
        [V.Act(other, 660, 780, V.ACT_SHOP, V.PLACE_SHOP)], facts, row, other, share, ctr
    )
    assert empty == []
    assert ctr.counts.get("visitor_non_visit_day", 0) >= 1


# ---------------------------------------------------------------- 7 就寝
#: 就寝を含まない「厚い」1 日(``_fill_day`` が働かない= 4 件以上)。
DAY_WITHOUT_SLEEP = [
    V.Act(0, 600, 660, V.ACT_PREP, V.PLACE_HOME),
    V.Act(0, 660, 780, V.ACT_MEAL, V.PLACE_FOOD),
    V.Act(0, 780, 900, V.ACT_SHOP, V.PLACE_SHOP),
    V.Act(0, 900, 1_000, V.ACT_REST, V.PLACE_HOME),
]


def test_sleep_is_inserted_for_residents(facts, share):
    ctr = W17.RepairCounters()
    row = _row(facts, 0)
    out, flags, dropped = W17.repair_day(list(DAY_WITHOUT_SLEEP), facts, row, 0, share, ctr)
    assert out[0].activity == V.ACT_SLEEP and out[0].start == 0
    assert ctr.counts.get("sleep_added", 0) == 1
    assert ctr.counts.get("day_underfilled", 0) == 0  # 厚い日は補わない


def test_sleep_is_not_forced_on_agents_without_a_home_in_the_world(facts, share):
    ctr = W17.RepairCounters()
    row = _row(facts, 2)  # 域外常住の通勤者
    out, flags, dropped = W17.repair_day(list(DAY_WITHOUT_SLEEP), facts, row, 0, share, ctr)
    assert ctr.counts.get("sleep_added", 0) == 0
    assert all(a.activity != V.ACT_SLEEP for a in out)
    assert len(out) == len(DAY_WITHOUT_SLEEP)


# ---------------------------------------------------------------- 8 薄すぎる日の穴埋め
def test_sleep_only_day_is_filled_from_the_skeleton(facts, share):
    """第1回パイロットの退化(23/300 が 7 日とも「就寝」だけ)への対処。"""
    ctr = W17.RepairCounters()
    row = _row(facts, 1)
    out, flags, dropped = W17.repair_day(
        [V.Act(0, 0, 420, V.ACT_SLEEP, V.PLACE_HOME)], facts, row, 0, share, ctr
    )
    assert len(out) >= W17.MIN_ACTS_PER_DAY
    assert ctr.counts.get("day_underfilled", 0) >= 1
    assert flags[0] is False and any(flags)  # LLM の 1 件は残り、足した分だけが修正
    for x, y in zip(out, out[1:]):
        assert x.end <= y.start


def test_fill_keeps_the_llm_activities(facts, share):
    ctr = W17.RepairCounters()
    row = _row(facts, 1)
    keep = V.Act(0, 660, 780, V.ACT_MEAL, V.PLACE_FOOD)
    out, flags, dropped = W17.repair_day([keep], facts, row, 0, share, ctr)
    assert keep in out
    assert len(out) >= W17.MIN_ACTS_PER_DAY


def test_fill_does_not_touch_non_visit_days_of_visitors(facts, share):
    ctr = W17.RepairCounters()
    row = _row(facts, 4)
    other = int(np.flatnonzero(
        [not ((int(facts.visit_days[row]) >> d) & 1) for d in range(7)]
    )[0])
    out, _, _ = W17.repair_day([], facts, row, other, share, ctr)
    assert out == []


# ---------------------------------------------------------------- 骸格フォールバック
@pytest.mark.parametrize("agent_id", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
def test_skeleton_is_valid_after_repair(facts, share, agent_id: int):
    """応答全滅の埋めは、修復を通したあと**そのまま凍結できる形**になっている。"""
    row = _row(facts, agent_id)
    acts, flags, _ = W17.repair(
        W17.skeleton(facts, row), facts, row, share, W17.RepairCounters()
    )
    assert len(flags) == len(acts)
    by_day: dict[int, list[V.Act]] = {}
    for a in acts:
        by_day.setdefault(a.day, []).append(a)
    for day, day_acts in by_day.items():
        assert len(day_acts) <= W17.MAX_ACTS_PER_DAY + 1
        for x, y in zip(day_acts, day_acts[1:]):
            assert x.end <= y.start
        for a in day_acts:
            assert 0 <= a.start < a.end <= V.MINUTES_PER_DAY
            assert 0 <= a.activity < len(V.ACTIVITY_WORDS)
            assert 0 <= a.place < len(V.PLACE_WORDS)
    if int(facts.visit_days[row]):
        assert set(by_day) == {d for d in range(7) if (int(facts.visit_days[row]) >> d) & 1}


# ---------------------------------------------------------------- raking
def test_raking_lowers_jsd_and_counts_moves():
    """全部 6 時始まりの勤務を、朝ピークのカーブへ寄せる。"""
    n = 600
    agent_row = np.arange(n, dtype=np.int64)
    day = np.zeros(n, dtype=np.int64)
    start = np.full(n, 360, dtype=np.int64)
    end = np.full(n, 900, dtype=np.int64)
    activity = np.full(n, V.ACT_WORK, dtype=np.int64)
    modified = np.zeros(n, dtype=bool)
    curve = np.zeros(24)
    curve[8] = 0.6
    curve[9] = 0.4
    rep = W17.rake(agent_row, day, start, end, activity, modified,
                   {"自宅－勤務": curve}, max_frac=1.0)
    assert rep.jsd_after["自宅－勤務"] < rep.jsd_before["自宅－勤務"]
    assert rep.n_moved == int(modified.sum()) > 0
    assert set(np.unique(start // 60)) <= {6, 8, 9}


def test_raking_respects_the_move_budget():
    n = 500
    agent_row = np.arange(n, dtype=np.int64)
    day = np.zeros(n, dtype=np.int64)
    start = np.full(n, 360, dtype=np.int64)
    end = np.full(n, 900, dtype=np.int64)
    activity = np.full(n, V.ACT_WORK, dtype=np.int64)
    modified = np.zeros(n, dtype=bool)
    curve = np.zeros(24)
    curve[9] = 1.0
    rep = W17.rake(agent_row, day, start, end, activity, modified,
                   {"自宅－勤務": curve}, max_frac=0.1)
    assert rep.n_moved <= int(0.1 * n)


def test_raking_never_creates_overlaps():
    """隣の活動の隙間の中でしか動かさない。"""
    agent_row = np.array([0, 0, 0], dtype=np.int64)
    day = np.zeros(3, dtype=np.int64)
    start = np.array([0, 360, 400], dtype=np.int64)
    end = np.array([360, 390, 1_000], dtype=np.int64)
    activity = np.array([V.ACT_SLEEP, V.ACT_WORK, V.ACT_REST], dtype=np.int64)
    modified = np.zeros(3, dtype=bool)
    curve = np.zeros(24)
    curve[20] = 1.0
    W17.rake(agent_row, day, start, end, activity, modified,
             {"自宅－勤務": curve}, max_frac=1.0)
    order = np.argsort(start)
    assert np.all(end[order][:-1] <= start[order][1:])


def test_jensen_shannon_bounds():
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 1.0])
    assert W17.jensen_shannon(a, a) == pytest.approx(0.0)
    assert W17.jensen_shannon(a, b) == pytest.approx(1.0)


def test_hour_curves_are_normalized(world_dir: Path):
    curves = W17.hour_curves(world_dir)
    assert set(curves) >= {"自宅－勤務", "自宅－通学", "私事"}
    for vec in curves.values():
        assert vec.shape == (24,)
        assert vec.sum() == pytest.approx(1.0)


def test_raking_rolls_back_when_it_would_make_things_worse():
    """全目的の JSD 最大値が下がらないときは丸ごと巻き戻す(較正の悪化を凍結しない)。"""
    n = 40
    agent_row = np.arange(n, dtype=np.int64)
    day = np.zeros(n, dtype=np.int64)
    start = np.full(n, 480, dtype=np.int64)
    end = np.full(n, 900, dtype=np.int64)
    activity = np.full(n, V.ACT_WORK, dtype=np.int64)
    modified = np.zeros(n, dtype=bool)
    curve = np.zeros(24)
    curve[8] = 1.0  # すでに一致している=動かす余地がない
    before = start.copy()
    rep = W17.rake(agent_row, day, start, end, activity, modified,
                   {"自宅－勤務": curve}, max_frac=1.0)
    assert rep.n_moved == 0
    assert np.array_equal(start, before)


def test_day_shift_clamps_the_first_and_last_block():
    """1 日の平行移動は先頭の開始を 0・末尾の終了を 1440 に切り詰める(範囲外にしない)。"""
    start = np.array([0, 480, 540, 1_380], dtype=np.int64)
    end = np.array([420, 540, 1_080, 1_440], dtype=np.int64)
    agent_row = np.zeros(4, dtype=np.int64)
    day = np.zeros(4, dtype=np.int64)
    activity = np.array(
        [V.ACT_SLEEP, V.ACT_MOVE, V.ACT_WORK, V.ACT_SLEEP], dtype=np.int64
    )
    modified = np.zeros(4, dtype=bool)
    curve = np.zeros(24)
    curve[8] = 1.0  # 勤務を 9 時 → 8 時へ(= 日を 60 分前へ)
    rep = W17.rake(agent_row, day, start, end, activity, modified,
                   {"自宅－勤務": curve}, max_frac=1.0)
    assert rep.n_moved == 4
    assert start[0] == 0 and end[3] <= V.MINUTES_PER_DAY
    assert start.min() >= 0 and end.max() <= V.MINUTES_PER_DAY
    assert np.all(end[:-1] <= start[1:])  # 並びと重なりは壊れない
    assert start[2] == 480  # 勤務が 8 時へ動いた


# ---------------------------------------------------------------- 適応予算(本番第1回の FAIL)
def test_rake_respects_an_explicit_row_budget():
    n = 700
    agent_row = np.arange(n, dtype=np.int32)
    day = np.zeros(n, dtype=np.int32)
    start = np.full(n, 360, dtype=np.int32)
    end = np.full(n, 900, dtype=np.int32)
    activity = np.full(n, V.ACT_WORK, dtype=np.int8)
    modified = np.zeros(n, dtype=bool)
    curve = np.zeros(24)
    curve[8] = 1.0
    rep = W17.rake(agent_row, day, start, end, activity, modified,
                   {"自宅－勤務": curve}, budget_rows=50)
    assert rep.budget_rows == 50
    assert 0 < rep.n_moved <= 50


def test_rake_does_nothing_when_the_budget_is_zero():
    """修復だけでゲートの枠を使い切ったら raking しない(JSD は据え置き・報告する)。"""
    n = 100
    agent_row = np.arange(n, dtype=np.int32)
    day = np.zeros(n, dtype=np.int32)
    start = np.full(n, 360, dtype=np.int32)
    end = np.full(n, 900, dtype=np.int32)
    activity = np.full(n, V.ACT_WORK, dtype=np.int8)
    modified = np.zeros(n, dtype=bool)
    before = start.copy()
    curve = np.zeros(24)
    curve[8] = 1.0
    rep = W17.rake(agent_row, day, start, end, activity, modified,
                   {"自宅－勤務": curve}, budget_rows=0)
    assert rep.n_moved == 0 and rep.budget_rows == 0
    assert not modified.any() and np.array_equal(start, before)
    assert rep.jsd_after == rep.jsd_before  # 報告値は前後同値で残る
    assert set(rep.jsd_before) == {"自宅－勤務"}


def test_negative_budget_is_clamped_to_zero():
    rep = W17.rake(np.zeros(1, np.int32), np.zeros(1, np.int32), np.full(1, 360, np.int32),
                   np.full(1, 900, np.int32), np.full(1, V.ACT_WORK, np.int8),
                   np.zeros(1, bool), {"自宅－勤務": np.eye(24)[8]}, budget_rows=-5)
    assert rep.budget_rows == 0 and rep.n_moved == 0
