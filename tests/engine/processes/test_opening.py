"""営業時間 PlanSpec と役割行動「開閉店」(D-R2-5 第1陣 6 行目)のテスト。

正典: 世界過程設計書 §1 D-R2-1(層2が正・conf 宣言つきフォールバック)・
行動契約書 §2.2(開閉店=従業者(権限)・失敗=権限なし)。
"""

from __future__ import annotations

import numpy as np

from shibuya.agents.state import AgentKind, ResultCode
from shibuya.engine import resolve as R
from shibuya.engine.processes.opening import OpeningProcess, build_open_matrix

from .conftest import fake_plan_assets, make_agents, make_world


def _process(rows, *, n_cells: int = 4, n_agents: int = 12):
    world = make_world(n_cells)
    agents, _ = make_agents(world, n_agents)
    pa = fake_plan_assets(rows)
    return world, agents, OpeningProcess(world, agents, pa, day_index=0)


# ================================================================= 開閉行列(W7)
def test_open_matrix_follows_the_intervals():
    m = build_open_matrix(2, *(np.asarray(x) for x in zip(*[(0, 0, 600, 1_320)])), 0)
    assert not m[0, 599]
    assert m[0, 600] and m[0, 1_319]
    assert not m[0, 1_320]
    assert not m[1].any()  # 区間の無い POI は終日閉


def test_open_matrix_wraps_intervals_past_midnight():
    """W7 の ``end`` は 1440 超(日跨ぎ)がある(実データで 1,918 区間)。"""
    rows = [(0, 0, 1_020, 1_740)]  # 17:00-翌 05:00
    m = build_open_matrix(1, *(np.asarray(x) for x in zip(*rows)), 0)
    assert m[0, 1_020] and m[0, 1_439]
    assert m[0, 0] and m[0, 299]
    assert not m[0, 300]
    assert not m[0, 1_019]


def test_open_matrix_selects_the_weekday():
    rows = [(0, 0, 600, 700), (0, 5, 800, 900)]
    mon = build_open_matrix(1, *(np.asarray(x) for x in zip(*rows)), 0)
    sat = build_open_matrix(1, *(np.asarray(x) for x in zip(*rows)), 5)
    assert mon[0, 650] and not mon[0, 850]
    assert sat[0, 850] and not sat[0, 650]


# ================================================================= フラグの反映
def test_flags_follow_the_plan_and_override_the_c2_default():
    world, agents, proc = _process([(0, 0, 600, 1_320)])
    assert proc.active
    proc.step(600)
    assert bool(world.open_mask(600)[0]) is True
    assert bool(world.open_mask(1_320)[0]) is True  # 上書き欄は「いまの値」を返す
    proc.step(1_320)
    assert bool(world.open_mask(1_320)[0]) is False


def test_engine_rule_fallback_is_counted():
    """§1 末尾のフォールバック台帳=``executor=engine_rule`` の行。"""
    world, agents, proc = _process([(0, 0, 600, 1_320)])
    proc.step(0)  # 担当従業者は自宅に居る → フォールバック
    assert proc.n_fallback > 0
    assert proc.n_fallback + proc.n_role_actions == proc.n_events


def test_role_action_is_used_when_the_staff_is_on_site():
    world, agents, proc = _process([(0, 0, 600, 1_320)], n_cells=4, n_agents=40)
    staff = int(proc.staff_of_poi[0])
    assert staff >= 0
    cell = int(world.pois.cell[0])
    R.rail_arrive(agents, world, np.array([staff]), np.array([cell]))
    proc.step(0)
    assert proc.n_role_actions >= 1


def test_inactive_without_a_plan_spec():
    world = make_world(4)
    agents, _ = make_agents(world, 8)
    from shibuya.world.assets import ProcessAssets

    proc = OpeningProcess(world, agents, ProcessAssets.synthetic())
    assert not proc.active
    proc.step(0)
    assert np.all(world.pois.open_now < 0)  # C2 の 10:00-22:00 既定に任せる


# ================================================================= 権限(契約書 §2.2)
def test_open_close_without_permission_returns_no_permission():
    world, agents, proc = _process([(0, 0, 600, 1_320)], n_agents=20)
    outsider = int(np.flatnonzero(agents.registry.field("kind") != int(AgentKind.WORKER))[0])
    code = R.request_open_close(
        agents, world, np.array([outsider]), np.array([0]), np.array([True]), 10
    )
    assert int(code[0]) == int(ResultCode.NO_PERMISSION)
    assert int(agents.last_result[outsider]) == int(ResultCode.NO_PERMISSION)


def test_has_permission_requires_staff_kind_and_same_cell():
    world, agents, proc = _process([(0, 0, 600, 1_320)], n_agents=40)
    staff = int(proc.staff_of_poi[0])
    cell = int(world.pois.cell[0])
    assert not bool(proc.has_permission([staff], [0])[0]) or int(agents.cell[staff]) == cell
    R.rail_arrive(agents, world, np.array([staff]), np.array([cell]))
    assert bool(proc.has_permission([staff], [0])[0])
    other = (staff + 1) % agents.n
    assert not bool(proc.has_permission([other], [0])[0])
