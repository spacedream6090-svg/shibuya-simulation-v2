"""関係4本(§2)と conf宣言つきフォールバック台帳(§1 末尾)の検査。"""

from __future__ import annotations

import pytest

from shibuya.world.processes.records import Executor
from shibuya.world.processes.relations import (
    CountsAs,
    Realizes,
    Records,
    Revises,
    SubjectType,
    fallback_ledger,
)


def _realizes(**kw):
    base = dict(
        subject_id="p1",
        subject_type=SubjectType.WORLD_PROCESS,
        plan_spec_id="plan.x",
        executor=Executor.LLM_AGENT,
    )
    base.update(kw)
    return Realizes(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------- realizes
def test_realizes_requires_executor_attribute():
    """§2「realizes … 属性 executor: {llm_agent | engine_rule | none}」。"""
    with pytest.raises(TypeError, match="executor"):
        _realizes(executor="engine_rule")


def test_engine_rule_realizes_needs_conf_coverage_repayment():
    with pytest.raises(ValueError, match="conf"):
        _realizes(executor=Executor.ENGINE_RULE)
    with pytest.raises(ValueError, match="カバー率"):
        _realizes(executor=Executor.ENGINE_RULE, conf=0.7)
    r = _realizes(
        executor=Executor.ENGINE_RULE, conf=0.7, coverage="全便", repayment_due="第2陣"
    )
    assert r.is_fallback


def test_conf_rejected_on_non_engine_rule():
    with pytest.raises(ValueError, match="conf"):
        _realizes(executor=Executor.NONE, conf=0.7)


def test_conf_range():
    with pytest.raises(ValueError):
        _realizes(executor=Executor.ENGINE_RULE, conf=1.5, coverage="x", repayment_due="y")
    with pytest.raises(ValueError):
        _realizes(executor=Executor.ENGINE_RULE, conf=0.0, coverage="x", repayment_due="y")


def test_agent_action_subject_is_allowed():
    r = _realizes(subject_id="agent.crew.drive", subject_type=SubjectType.AGENT_ACTION)
    assert r.subject_type is SubjectType.AGENT_ACTION
    assert not r.is_fallback


# ---------------------------------------------------------------- fallback ledger
def test_fallback_ledger_lists_only_engine_rule_rows():
    rels = [
        _realizes(subject_id="a", plan_spec_id="plan.b", executor=Executor.LLM_AGENT),
        _realizes(
            subject_id="c",
            plan_spec_id="plan.a",
            executor=Executor.ENGINE_RULE,
            conf=0.5,
            coverage="全 POI",
            coverage_ratio=1.0,
            repayment_due="Phase 3",
        ),
        Records("log", "a", SubjectType.WORLD_PROCESS),
        CountsAs("x", "y", "c"),
    ]
    rows = fallback_ledger(rels)
    assert [r.subject_id for r in rows] == ["c"]
    assert rows[0].conf == 0.5
    assert rows[0].repayment_due == "Phase 3"
    assert rows[0].coverage_ratio == 1.0


def test_fallback_ledger_is_sorted():
    def eng(sid, pid):
        return _realizes(
            subject_id=sid,
            plan_spec_id=pid,
            executor=Executor.ENGINE_RULE,
            conf=0.5,
            coverage="x",
            repayment_due="y",
        )

    rows = fallback_ledger([eng("z", "plan.b"), eng("a", "plan.b"), eng("m", "plan.a")])
    assert [(r.plan_spec_id, r.subject_id) for r in rows] == [
        ("plan.a", "m"),
        ("plan.b", "a"),
        ("plan.b", "z"),
    ]


# ---------------------------------------------------------------- records / revises / counts_as
def test_records_requires_target_type():
    with pytest.raises(TypeError, match="target_type"):
        Records("log", "p", "world_process")  # type: ignore[arg-type]


def test_revises_version_must_be_a_revision():
    with pytest.raises(ValueError, match="new_version"):
        Revises("指令A", "plan.rail", 100, 1)
    r = Revises("指令A", "plan.rail", 100, 2, reason="運転整理")
    assert r.as_dict()["new_version"] == 2


def test_counts_as_requires_context():
    with pytest.raises(ValueError, match="文脈"):
        CountsAs("制服を着た者", "駅員", "  ")
    c = CountsAs("制服を着た者", "駅員", "駅構内・営業時間内")
    assert c.as_dict()["kind"] == "counts_as"
