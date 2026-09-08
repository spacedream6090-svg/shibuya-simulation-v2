"""台帳(名前空間1つ)の登録検査・被覆報告・決定論 JSON/ハッシュ。"""

from __future__ import annotations

import json

import pytest

from shibuya.manifest.world_catalog import WorldCatalog
from shibuya.world.processes.records import DetailDeclaration, Executor
from shibuya.world.processes.registry import WorldRegistry
from shibuya.world.processes.relations import Realizes, Records, Revises, SubjectType
from tests.world.processes.conftest import make_plan_spec, make_process


def test_add_process_and_lookup(registry: WorldRegistry):
    p = registry.add_process(make_process("a"))
    assert registry.process("a") is p
    assert registry.processes == (p,)


def test_duplicate_process_id_rejected(registry: WorldRegistry):
    registry.add_process(make_process("a"))
    with pytest.raises(ValueError, match="重複"):
        registry.add_process(make_process("a"))


def test_unknown_catalog_class_rejected(registry: WorldRegistry):
    with pytest.raises(ValueError, match="世界カタログ"):
        registry.add_process(make_process("a", catalog_classes=("存在しないクラス",)))


def test_add_process_runs_constitution_check(registry: WorldRegistry):
    """reaches も contributes も空の過程は登録できない(D-R2-4)。"""
    with pytest.raises(ValueError, match="憲法5"):
        registry.add_process(make_process("a", reaches=(), contributes=()))


def test_add_process_rejects_unknown_target(registry: WorldRegistry):
    with pytest.raises(ValueError, match="C5-UNKNOWN-TARGET"):
        registry.add_process(make_process("a", reaches=("存在しないチャネル",)))


def test_non_strict_registry_collects_instead_of_raising(test_catalog: WorldCatalog):
    reg = WorldRegistry("lax", catalog=test_catalog, strict=False)
    reg.add_process(make_process("a", reaches=(), contributes=()))
    report = reg.check_constitution5()
    assert not report.ok
    assert {v.code for v in report.violations} == {"C5-EMPTY"}


def test_detail_needs_registered_owner(registry: WorldRegistry):
    with pytest.raises(ValueError, match="未登録の世界過程"):
        registry.add_detail(
            DetailDeclaration(id="d", owner_process_id="nope", description="x", reaches=("人物①",))
        )
    registry.add_process(make_process("a"))
    d = registry.add_detail(
        DetailDeclaration(id="d", owner_process_id="a", description="x", reaches=("人物①",))
    )
    assert registry.details == (d,)


def test_relation_targets_must_exist(registry: WorldRegistry):
    registry.add_process(make_process("a"))
    with pytest.raises(ValueError, match="未登録の PlanSpec"):
        registry.add_relation(
            Realizes("a", SubjectType.WORLD_PROCESS, "plan.missing", Executor.LLM_AGENT)
        )
    registry.add_plan_spec(make_plan_spec("plan.x"))
    with pytest.raises(ValueError, match="未登録の世界過程"):
        registry.add_relation(
            Realizes("zzz", SubjectType.WORLD_PROCESS, "plan.x", Executor.LLM_AGENT)
        )
    registry.add_relation(
        Realizes("a", SubjectType.WORLD_PROCESS, "plan.x", Executor.LLM_AGENT)
    )
    registry.add_relation(Records("log", "a", SubjectType.WORLD_PROCESS))
    registry.add_relation(Revises("店主エージェント", "plan.x", 10, 2))
    assert len(registry.relations) == 3


def test_fallback_ledger_covers_relations_and_planless_processes(registry: WorldRegistry):
    registry.add_process(make_process("a"))
    registry.add_process(
        make_process(
            "b",
            executor=Executor.ENGINE_RULE,
            conf=0.4,
            coverage="全断面",
            repayment_due="第3陣",
        )
    )
    registry.add_plan_spec(make_plan_spec("plan.x"))
    registry.add_relation(
        Realizes(
            "a",
            SubjectType.WORLD_PROCESS,
            "plan.x",
            Executor.ENGINE_RULE,
            conf=0.6,
            coverage="全便",
            repayment_due="第2陣",
        )
    )
    rows = registry.fallback_ledger()
    assert {(r.subject_id, r.plan_spec_id) for r in rows} == {("a", "plan.x"), ("b", "")}
    assert all(r.repayment_due for r in rows)  # 返済期限が空の行は無い


def test_coverage_report_shares(registry: WorldRegistry):
    registry.add_process(make_process("a"))
    registry.add_process(make_process("b", executor=Executor.LLM_AGENT))
    registry.add_process(
        make_process(
            "c",
            executor=Executor.ENGINE_RULE,
            conf=0.5,
            coverage="x",
            repayment_due="y",
            catalog_classes=("騒音場",),
        )
    )
    rep = registry.coverage_report()
    assert rep.n_processes == 3
    assert rep.by_executor == {"llm_agent": 1, "engine_rule": 1, "none": 1}
    assert abs(sum(rep.share_by_executor.values()) - 1.0) < 1e-9
    assert rep.n_fallback_processes == 1
    assert set(rep.catalog_classes_covered) == {"混雑場(密度)", "騒音場"}
    assert 0.0 < rep.catalog_coverage <= 1.0
    assert "カタログ被覆" in rep.as_text()


def test_to_json_is_deterministic_and_hash_stable(test_catalog: WorldCatalog):
    def build(order):
        reg = WorldRegistry("t", catalog=test_catalog)
        for pid in order:
            reg.add_process(make_process(pid))
        return reg

    a = build(["a", "b", "c"])
    b = build(["c", "b", "a"])
    assert a.to_json() == b.to_json()
    assert a.registry_hash() == b.registry_hash()
    assert len(a.registry_hash()) == 64
    payload = json.loads(a.to_json())
    assert [p["id"] for p in payload["processes"]] == ["a", "b", "c"]
    assert payload["catalog"]["version"] == "test"


def test_registry_hash_changes_with_content(test_catalog: WorldCatalog):
    a = WorldRegistry("t", catalog=test_catalog)
    a.add_process(make_process("a"))
    b = WorldRegistry("t", catalog=test_catalog)
    b.add_process(make_process("a", note="差分"))
    assert a.registry_hash() != b.registry_hash()
