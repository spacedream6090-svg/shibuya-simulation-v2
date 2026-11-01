"""〔第 2 期 2-4 V3〕在席の印を歩き出しで解く(``engine.seat_release``・``resolve._apply_move``)。

既定 walk=移動の意図で歩き出した体(行き先のノードへ向かう=MOVING)の ``poi_ref``/``poi_since`` を解く。到着済み(行き先の
ノードに居る=IDLE)・移動しない体・行けない体は解かない。``resolve.apply`` の既定(``seat_release_walk=False``=直に呼ぶ
試験と切替口 legacy)は 2-4 より前の挙動。記録 ``docs/bench/analysis/wallbounce-1012/vb24/README.md`` の V3。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import Activity, AgentState
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine import seat_release as SR
from shibuya.world.state import World


def _world_agents(n: int = 4):
    world = World.synthetic(n_cells=9, seed=1)
    agents = AgentState(n)
    rep = np.asarray(world.assets.cell_rep_node)
    with agents.writable():
        r = agents.registry
        node0 = int(rep[0])
        r.node[:] = node0
        r.cell[:] = world.assets.node_cell[node0]
        r.activity[:] = int(Activity.SHOPPING)
        r.poi_ref[:] = 0
        r.poi_since[:] = 5
    agents.freeze()
    world.freeze()
    return world, agents


def _move(agent_ids, cells):
    n = len(agent_ids)
    return C.IntentBatch(
        agent_id=np.asarray(agent_ids, dtype=np.int64),
        action_code=np.full(n, C.ACT_MOVE, dtype=np.int8),
        target_id=np.asarray(cells, dtype=np.int32),
        resource_id=np.full(n, -1, dtype=np.int32),
        t_notice_ns=np.zeros(n, dtype=np.int64),
    )


def _far_cell(world) -> int:
    rep = np.asarray(world.assets.cell_rep_node)
    for c in range(1, world.n_cells):
        nxt = world.graph.route_next_node(np.array([rep[0]]), np.array([rep[c]]))
        if int(nxt[0]) >= 0 and int(rep[c]) != int(rep[0]):
            return c
    raise AssertionError("歩ける行き先のセルが無い")


@pytest.mark.parametrize("walk", [True, False])
def test_walkers_release_the_seat_only_with_the_walk_arm(walk):
    world, agents = _world_agents()
    far = _far_cell(world)
    # 体 0: 別のセルへ歩き出す / 体 1: 行き先=今のセル(到着済み=歩かない)/ 体 2・3: 移動の意図なし
    out = R.apply(_move([0, 1], [far, 0]), C.IntentBatch.empty(), agents, world, 10, seat_release_walk=walk)
    r = agents.registry
    assert int(r.activity[0]) == int(Activity.MOVING) and int(r.activity[1]) == int(Activity.IDLE)
    if walk:
        assert int(r.poi_ref[0]) == -1 and int(r.poi_since[0]) == -1
        assert out.n_seat_released_walk == 1
    else:
        assert int(r.poi_ref[0]) == 0 and int(r.poi_since[0]) == 5
        assert out.n_seat_released_walk == 0
    # 歩かない体の印は腕によらずそのまま
    assert r.poi_ref[1:].tolist() == [0, 0, 0] and r.poi_since[1:].tolist() == [5, 5, 5]


def test_unseated_walkers_are_not_counted():
    world, agents = _world_agents()
    with agents.writable():
        agents.registry.poi_ref[0] = -1
    out = R.apply(_move([0], [_far_cell(world)]), C.IntentBatch.empty(), agents, world, 10, seat_release_walk=True)
    assert out.n_seat_released_walk == 0 and int(agents.registry.poi_ref[0]) == -1


def test_arm_default_header_and_resume_check(monkeypatch):
    assert SR.DEFAULT_MODE == SR.MODE_WALK
    monkeypatch.setattr(SR, "_ARM", SR.MODE_WALK)
    assert SR.arm() == "walk" and SR.is_walk()
    assert SR.header_fields("walk") == {"mode": "walk"} and SR.header_fields("legacy") is None
    SR.check_resume({"mode": "walk"})
    with pytest.raises(ValueError):
        SR.check_resume(None)  # 見出しに無い=legacy(2-4 より前のラン)
    monkeypatch.setattr(SR, "_ARM", SR.MODE_LEGACY)
    SR.check_resume(None)
    with pytest.raises(ValueError):
        SR.check_resume({"mode": "walk"})
    with pytest.raises(ValueError):
        SR.set_arm("sometimes")


def test_run_manifest_reports_the_arm_and_the_count(monkeypatch):
    """合成の世界のランの manifest の ``leave_effects`` に腕と解いた数が出る(legacy は 0)。"""
    from shibuya.engine.run import run_day

    got = {}
    for mode in ("walk", "legacy"):
        monkeypatch.setattr(SR, "_ARM", mode)
        res = run_day(n_agents=60, seed=1, ticks=240, renderer="stub", vocab_version="v3", checkpoint_every=240)
        le = res.run_manifest_fields()["leave_effects"]
        got[mode] = (le["seat_release"], le["released_on_walk"])
    assert got["walk"][0] == "walk" and got["legacy"] == ("legacy", 0)


@pytest.mark.parametrize("first,second", [("walk", "legacy"), ("legacy", "walk")])
def test_resume_with_another_seat_arm_is_refused(tmp_path, monkeypatch, first, second):
    """腕は設定の指紋に入れない=状態のファイルの見出しの ``seat_release``(walk だけ書く)と今の腕を突き合わせる。"""
    from shibuya.engine import resume as RS
    from shibuya.engine.run import run_day

    kw = dict(n_agents=40, seed=1, n_cells=9, ticks=240, budget=40.0, vocab_version="v3")
    monkeypatch.setattr(SR, "_ARM", first)
    a = run_day(state_out=tmp_path / "st", stop_at_tick=120, **kw)
    f = tmp_path / "st" / a.resume["state_files"][-1]["file"]
    head = RS.read_state(f).header
    assert ("seat_release" in head) == (first == "walk")
    monkeypatch.setattr(SR, "_ARM", second)
    with pytest.raises(ValueError, match="在席の印の腕"):
        run_day(resume_from=f, **kw)
    monkeypatch.setattr(SR, "_ARM", first)
    run_day(resume_from=f, **kw)  # 同じ腕は通る
