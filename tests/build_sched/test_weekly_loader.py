"""``agents.weekly``: 語彙の二重定義一致・往復・計画境界の取り出し・バイト予算。

対応する仕様行
- 予算 M1(個体状態 ≤30KB/体)/M3(T0 習慣スロット表 ≤12.8KB/体)
- 知覚契約書 §6「計画境界起床(タスク終了時に次を推論)」
- 層契約(``agents`` は ``build`` を import しない=語彙は二重定義・ここで機械検査)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya.agents import weekly as W
from shibuya.agents.state import WakeCondition
from shibuya.build.sched import vocab as V
from shibuya.build.sched import w17_schedule as W17

from .conftest import AGENTS, mock_week, response_row, write_responses


# ---------------------------------------------------------------- 二重定義の一致
def test_vocabulary_double_definition_agrees():
    """``build.sched.vocab`` と ``agents.weekly`` の語彙・写像が一致する。"""
    assert W.ACTIVITY_WORDS == V.ACTIVITY_WORDS
    assert W.PLACE_WORDS == V.PLACE_WORDS
    assert W.ACTIVITY_TO_ACTION == V.ACTIVITY_TO_ACTION
    assert W.ACTIVITY_TO_WAKE == V.ACTIVITY_TO_WAKE
    assert W.N_DAYS == V.N_DAYS
    assert W.MINUTES_PER_DAY == V.MINUTES_PER_DAY
    assert W.CELL_UNRESOLVED == W17.CELL_UNRESOLVED
    assert W.WEEKLY_FILE == W17.SCHEDULE_NAME


def test_wake_conditions_are_plan_boundaries():
    plan = {
        int(WakeCondition.PLAN_SLEEPING), int(WakeCondition.PLAN_WORKING),
        int(WakeCondition.PLAN_GENERAL), int(WakeCondition.PLAN_TRANSIT),
    }
    assert set(W.ACTIVITY_TO_WAKE) <= plan
    assert W.ACTIVITY_TO_WAKE[V.ACT_SLEEP] == int(WakeCondition.PLAN_SLEEPING)
    assert W.ACTIVITY_TO_WAKE[V.ACT_WORK] == int(WakeCondition.PLAN_WORKING)
    assert W.ACTIVITY_TO_WAKE[V.ACT_RIDE] == int(WakeCondition.PLAN_TRANSIT)


# ---------------------------------------------------------------- 往復
@pytest.fixture()
def frozen(world_dir: Path, data_dir: Path) -> tuple[Path, W17.AgentFacts]:
    facts = W17.build_facts(world_dir, data_dir)
    write_responses(
        world_dir / "w17_responses.jsonl",
        [response_row(int(a), mock_week(facts, i)) for i, a in enumerate(facts.agent_id)],
    )
    _, cols = W17.ingest(world_dir, data_dir, facts=facts)
    W17.write_schedule(world_dir, cols)
    return world_dir, facts


def test_load_weekly_roundtrip(frozen):
    world_dir, facts = frozen
    wk = W.load_weekly(world_dir)
    assert wk is not None
    assert wk.n_agents == facts.n
    assert wk.day_offset.size == facts.n * W.N_DAYS + 1
    assert int(wk.day_offset[-1]) == wk.n_activities
    assert np.array_equal(wk.agent_id, np.sort(facts.agent_id))
    # O(1) 参照が実データと一致する
    for row in range(wk.n_agents):
        for d in range(W.N_DAYS):
            lo, hi = wk.day_span(row, d)
            acts = wk.activities_of(row, d)
            assert acts["start_min"].size == hi - lo
            if hi > lo:
                assert np.all(np.diff(acts["start_min"]) > 0)
                assert np.all(acts["end_min"] > acts["start_min"])


def test_load_weekly_returns_none_without_asset(tmp_path: Path):
    assert W.weekly_available(tmp_path) is False
    assert W.load_weekly(tmp_path) is None
    assert W.load_weekly(None) is None


def test_boundary_events_replace_the_mock_five_slot_table(frozen):
    """``events_of_day`` の差し替え: tick 昇順・条件は活動語から決まる。"""
    world_dir, _ = frozen
    wk = W.load_weekly(world_dir)
    for day in range(W.N_DAYS):
        agent, cond, tick = wk.boundary_events(day)
        assert agent.size == cond.size == tick.size
        assert np.all(np.diff(tick) >= 0)  # tick 昇順(engine が searchsorted する形)
        assert np.all((tick >= 0) & (tick < W.MINUTES_PER_DAY))
        assert set(np.unique(cond)) <= set(W.ACTIVITY_TO_WAKE)
        # その日に活動を持つ体の集合と一致
        assert set(np.unique(agent)) == set(wk.agent_rows_of_day(day).tolist())


def test_target_cell_at_uses_the_table_then_the_fallback(frozen):
    world_dir, facts = frozen
    wk = W.load_weekly(world_dir)
    fallback = np.full(wk.n_agents, -7, dtype=np.int32)
    cells = wk.target_cell_at(0, 3 * 60, fallback)  # 03:00=大半が就寝(自宅)
    assert cells.shape == (wk.n_agents,)
    home = {int(a): int(c) for a, c in zip(facts.agent_id, facts.home_cell)}
    for row, aid in enumerate(wk.agent_id):
        if home[int(aid)] >= 0:
            assert cells[row] in (home[int(aid)], -7)
    # 誰も活動していない曜日/時刻では fallback がそのまま返る
    empty = wk.target_cell_at(0, 3 * 60, np.full(wk.n_agents, -3, dtype=np.int32))
    assert set(np.unique(empty)) <= set(np.unique(cells).tolist() + [-3])


def test_restrict_to_reorders_and_rejects_unknown_ids(frozen):
    world_dir, facts = frozen
    wk = W.load_weekly(world_dir)
    want = np.array([int(facts.agent_id[2]), int(facts.agent_id[0])], dtype=np.int64)
    sub = wk.restrict_to(want)
    assert np.array_equal(sub.agent_id, want)
    assert sub.n_agents == 2
    for i, aid in enumerate(want):
        src = int(np.flatnonzero(wk.agent_id == aid)[0])
        for d in range(W.N_DAYS):
            a, b = wk.day_span(src, d)
            c, e = sub.day_span(i, d)
            assert np.array_equal(wk.start_min[a:b], sub.start_min[c:e])
    with pytest.raises(KeyError):
        wk.restrict_to(np.array([10**9], dtype=np.int64))


def test_schedule_hash_is_stable_and_sensitive(frozen):
    world_dir, _ = frozen
    a = W.load_weekly(world_dir)
    b = W.load_weekly(world_dir)
    assert a.schedule_hash() == b.schedule_hash()
    import dataclasses

    c = dataclasses.replace(a, start_min=a.start_min + np.int16(1))
    assert c.schedule_hash() != a.schedule_hash()


def test_apply_to_mock_schedule_overwrites_the_bases(frozen):
    """結線用の変換関数: 合成日課の拠点セルを W17 の当日の行き先で置き換える。"""
    from shibuya.agents.schedule import synthesize

    world_dir, facts = frozen
    wk = W.load_weekly(world_dir).restrict_to(np.sort(facts.agent_id))
    mock = synthesize(wk.n_agents, "seed", n_cells=8)
    out = W.apply_to_mock_schedule(mock, wk, day_index=0)
    assert out.home_cell.shape == mock.home_cell.shape
    assert np.any(out.home_cell != mock.home_cell) or np.any(out.work_cell != mock.work_cell)


# ---------------------------------------------------------------- バイト予算
def test_bytes_per_agent_within_the_budget(frozen, capsys):
    """M1(≤30KB/体)・M3(T0 習慣 ≤12.8KB/体)の内側にあることを実測して報告する。"""
    world_dir, _ = frozen
    wk = W.load_weekly(world_dir)
    per_act = (
        wk.start_min.itemsize + wk.end_min.itemsize + wk.activity.itemsize
        + wk.place_kind.itemsize + wk.target_cell.itemsize + wk.seq.itemsize
    )
    assert per_act == 12  # 2+2+1+1+4+2
    assert wk.bytes_per_agent < 12_800  # M3
    print(
        f"\n[W17 loader] 体数={wk.n_agents} 活動={wk.n_activities} "
        f"({wk.n_activities / wk.n_agents:.1f}/体) {per_act} B/活動 "
        f"合計={wk.nbytes:,} B = {wk.bytes_per_agent:.0f} B/体 "
        f"(M3 12,800 B/体 の {wk.bytes_per_agent / 12_800:.1%})"
    )


def test_projected_bytes_at_full_scale():
    """39 万体・週 42 活動での投影値(実資産が無くても数えられる形で報告)。"""
    n_agents, per_agent_acts = 390_188, 42
    per_act, per_day_index = 12, 8
    total = n_agents * (per_agent_acts * per_act + (W.N_DAYS + 1) * per_day_index) + n_agents * 8
    per = total / n_agents
    assert per < 12_800
    print(f"\n[W17 投影] {n_agents:,}体 × {per_agent_acts}活動 = {total / 2**20:.0f} MiB "
          f"= {per:.0f} B/体(M3 12,800 B/体 の {per / 12_800:.1%})")
