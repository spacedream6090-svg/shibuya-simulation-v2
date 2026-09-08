"""世界過程の実行器(台帳 → 実装の橋)のテスト。

正典: 世界過程設計書 §2(門前条件の二重化)・§5 D-R2-4(憲法5 のビルド時検査)・
§3 実装原則3(書き込み口は resolve 一本)・方法論(ablation)。
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from shibuya.engine.processes.runner import PROCESS_ORDER, WorldProcessRunner
from shibuya.world.processes.first_batch import build_registry

from .conftest import fake_timetable_assets, make_agents, make_world

SRC = Path("src/shibuya/engine/processes")


def _runner(**kw):
    world = make_world(9)
    agents, schedule = make_agents(world, 20)
    return WorldProcessRunner(world=world, agents=agents, seed=1, schedule=schedule, **kw)


# ================================================================= 門前条件・同定
def test_registry_hash_is_exposed_and_stable():
    a = _runner()
    b = _runner()
    assert a.registry_hash and a.registry_hash == b.registry_hash
    assert a.registry_hash == build_registry().registry_hash()


def test_constitution_check_runs_at_construction():
    r = _runner()
    assert r.constitution_ok
    assert r.constitution_report.ok


def test_a_registry_that_fails_constitution_5_cannot_run():
    """届き先(reaches/contributes)の実在検査に落ちる台帳では過程を動かせない。"""
    reg = build_registry(channel_ids=(), pattern_ids=(), output_ids=(), strict=False)
    world = make_world(9)
    agents, _ = make_agents(world, 8)
    with pytest.raises(ValueError, match="憲法5"):
        WorldProcessRunner(registry=reg, world=world, agents=agents, seed=1)


def test_every_declared_process_id_exists_in_the_ledger():
    """実装が名乗る過程 id は全て台帳(first_batch)に実在する。"""
    r = _runner()
    known = {p.id for p in r.registry.processes}
    for key in PROCESS_ORDER:
        for pid in r._procs[key].process_ids:
            assert pid in known, (key, pid)


# ================================================================= ablation(トグル)
def test_processes_can_be_disabled_by_process_id():
    r = _runner(disabled=["rail_operation_static"])
    assert not r.is_enabled("rail")
    assert r.is_enabled("crowd")


def test_processes_can_be_disabled_by_ablation_id():
    r = _runner(disabled=["AB-OCCUPANCY-CAPACITY"])
    assert not r.is_enabled("crowd")


def test_enabled_selects_only_the_named_processes():
    r = _runner(enabled=["environment", "traffic"])
    assert r.enabled == {"environment", "traffic"}
    r.step(0)
    assert r.phase_seconds["rail"] == 0.0


# ================================================================= 書き込み口(§3 原則3)
def test_process_modules_never_open_a_write_window():
    """``.writable(`` / ``.thaw(`` を呼ぶのは resolve だけ(世界過程も例外にしない)。"""
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"writable", "thaw"}, (path, node.lineno)


def test_process_modules_do_not_import_build_or_economy():
    """層契約: engine → world/agents/perception/llm/core/manifest。build/economy は不可。"""
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "shibuya.build" not in text.replace("``shibuya.build``", "")
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("shibuya.economy"), (path, node.module)
                assert not node.module.startswith("shibuya.build"), (path, node.module)


# ================================================================= 実行
def test_step_accumulates_per_process_wall_time_and_counters():
    r = _runner()
    for t in range(10):
        r.step(t)
    assert r.n_steps == 10
    assert set(r.phase_seconds) == set(PROCESS_ORDER)
    c = r.counters()
    assert "crowd.balked" in c and "rail.trains" in c and "actual_log.rows" in c


def test_riders_are_conserved_from_the_start():
    r = _runner()
    assert r.riders_conserved()
    for t in range(30):
        r.step(t)
        assert r.riders_conserved()


def test_actual_log_records_departures_and_compliance_is_computable():
    world = make_world(9)
    agents, schedule = make_agents(world, 20)
    r = WorldProcessRunner(
        world=world, agents=agents, assets=fake_timetable_assets(), seed=1, schedule=schedule
    )
    for t in range(320):
        r.step(t)
    rate = r.compliance()
    assert rate.n_total > 0
    assert 0.0 <= rate.rate <= 1.0
    assert r.log.n_appended == rate.n_total


def test_flow_is_exposed_for_the_renderer():
    r = _runner()
    r.step(0)
    assert r.flow.shape == (r.world.n_cells,)
    assert r.flow.dtype == np.uint8
