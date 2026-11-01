"""第 1 期 1-5: ``staff_of_poi`` の丸振りを権利台帳の ``employ`` の行からの読みに置き換えても、同じ割り当てを返す。

比べる相手は HEAD(``6b82be2``)の ``OpeningProcess._assign_staff`` の写し(下の ``head_assign_staff``=本体は消した)。
合成の世界の色々な体の組(従業者 0・POI より少ない・多い・POI 0)と、実データの 5,000 体の抽出(byte-check と同じ
seed 1)で、配列の値と型まで同じ。再開の作り直し(``rebuild_derived``)も同じ値で、補充の過程と同じ配列を持ち続ける。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import AgentKind, AgentState
from shibuya.agents.schedule import synthesize
from shibuya.engine import resolve as R
from shibuya.engine.processes.opening import OpeningProcess
from shibuya.engine.rights import initial as RI
from shibuya.engine.rights import ledger as L
from shibuya.world.assets import ProcessAssets
from shibuya.world.state import World


# ---- HEAD 6b82be2 src/shibuya/engine/processes/opening.py の OpeningProcess._assign_staff の写し(自由関数にした) ----
def head_assign_staff(world, agents) -> np.ndarray:
    """POI → 担当従業者(``kind=従業者`` を決定論で丸振り・expedient)。-1=担当なし。"""
    out = np.full(world.n_poi, -1, dtype=np.int64)
    if world.n_poi == 0:
        return out
    workers = np.flatnonzero(
        agents.registry.field("kind") == int(AgentKind.WORKER)
    ).astype(np.int64)
    if workers.size == 0:
        return out
    out[:] = workers[np.arange(world.n_poi) % workers.size]
    return out


def _world_agents(n_cells: int, n_agents: int, seed: int, kinds=None):
    world = World.synthetic(n_cells=n_cells, seed=seed)
    agents = AgentState(n_agents)
    schedule = synthesize(n_agents, seed, world.n_cells)
    if kinds is not None:
        import dataclasses

        schedule = dataclasses.replace(schedule, kind=np.asarray(kinds, dtype=np.int8))
    R.initialize(agents, world, schedule)
    agents.freeze()
    world.freeze()
    return world, agents


@pytest.mark.parametrize("n_cells, n_agents, seed", [(4, 12, 1), (9, 40, 2), (16, 7, 3), (25, 300, 4), (9, 1, 5)])
def test_same_assignment_on_synthetic_worlds(n_cells, n_agents, seed):
    world, agents = _world_agents(n_cells, n_agents, seed)
    want = head_assign_staff(world, agents)
    proc = OpeningProcess(world, agents, ProcessAssets.synthetic())
    assert proc.staff_of_poi.dtype == want.dtype == np.int64
    assert np.array_equal(proc.staff_of_poi, want)
    # 台帳の行から: 担当のいる店は担当の体 1 人だけが employ を持つ(値まで)
    for j in np.flatnonzero(want >= 0).tolist():
        assert proc.rights.holders_of((L.STORE, j), L.EMPLOY, 0) == ((L.AGENT, int(want[j])),)
    assert np.array_equal(RI.staff_assignment(agents.registry.field("kind"), world.n_poi), want)


@pytest.mark.parametrize("label, kinds", [
    ("従業者なし", [0, 1, 3, 1]),
    ("従業者 1 人", [0, 2, 1, 1, 0]),
    ("全員が従業者", [2] * 30),
])
def test_same_assignment_for_edge_kinds(label, kinds):
    world, agents = _world_agents(9, len(kinds), 7, kinds=kinds)
    want = head_assign_staff(world, agents)
    proc = OpeningProcess(world, agents, ProcessAssets.synthetic())
    assert np.array_equal(proc.staff_of_poi, want), label
    if not (np.asarray(kinds) == int(AgentKind.WORKER)).any():
        assert (want == -1).all() and proc.rights.tally()["by_source"].get(RI.SOURCE_STAFF, 0) == 0


def test_zero_pois():
    kind = np.asarray([2, 2, 0], dtype=np.int8)
    assert RI.staff_assignment(kind, 0).shape == (0,)
    led = RI.build_initial(kind, 0)
    assert len(led) == 0 and RI.staff_of_poi(led, 0, 0).shape == (0,)


def test_rebuild_keeps_the_values_and_the_shared_array():
    world, agents = _world_agents(9, 40, 2)
    proc = OpeningProcess(world, agents, ProcessAssets.synthetic(), org_of_agent=np.arange(40) % 3 - 1)
    arr = proc.staff_of_poi
    before = list(proc.rights)
    old_rights = proc.rights
    proc.rebuild_derived()
    assert proc.staff_of_poi is arr                          # 補充の過程が同じ配列を持つ
    assert np.array_equal(arr, head_assign_staff(world, agents))
    assert proc.rights is not old_rights and list(proc.rights) == before   # 作り直した台帳は同じ行(値まで)


def test_open_close_asks_the_ledger_and_stays_the_same():
    """開閉の役割行動の権利は台帳に聞く(担当は台帳から読んだ=全部 許可あり)。結果は HEAD と同じ形(OK と旗)。"""
    from tests.engine.processes.conftest import fake_plan_assets

    world, agents = _world_agents(4, 40, 1)
    proc = OpeningProcess(world, agents, fake_plan_assets([(0, 0, 600, 1_320)]), day_index=0)
    staff = int(proc.staff_of_poi[0])
    assert staff >= 0 and proc.rights.holds((L.AGENT, staff), L.EMPLOY, (L.STORE, 0), 0)
    R.rail_arrive(agents, world, np.array([staff]), np.array([int(world.pois.cell[0])]))
    proc.step(600)
    assert proc.n_role_actions >= 1 and int(agents.last_result[staff]) == 0
    assert bool(world.open_mask(600)[0]) is True


@pytest.mark.requires_data("world_v2:w16_population.parquet", "world_v2:w6_poi.parquet")
def test_same_assignment_on_the_real_population():
    """実データ(5,000 体の抽出・seed 1)の種別と POI の数。SoA は母集団の種別を写した形(組み立てと同じ)。"""
    import pyarrow.parquet as pq

    from shibuya.agents.population import load_population
    from shibuya.engine.systems.build import _org_of_agent

    world_dir = Path("data/world/v2")
    pop = load_population(world_dir, 5_000, 1)
    n_poi = pq.read_metadata(world_dir / "w6_poi.parquet").num_rows

    class _W:  # head_assign_staff が読むのは n_poi だけ
        pass

    class _A:
        class registry:  # noqa: N801
            @staticmethod
            def field(name):
                assert name == "kind"
                return np.asarray(pop.kind)

    w = _W()
    w.n_poi = n_poi
    want = head_assign_staff(w, _A())
    led = RI.build_initial(pop.kind, n_poi, _org_of_agent(pop, 5_000))
    got = RI.staff_of_poi(led, n_poi, 0)
    assert got.dtype == want.dtype and np.array_equal(got, want)
    assert int(np.count_nonzero(want >= 0)) == n_poi  # 実データには従業者がいる=全部の店に担当
