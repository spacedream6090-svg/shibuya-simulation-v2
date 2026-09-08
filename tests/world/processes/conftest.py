"""world.processes のテスト用ファクトリ(最小の合法な宣言を作る)。"""

from __future__ import annotations

from typing import Any

import pytest

from shibuya.core.growth import GrowthDeclaration, Retention
from shibuya.manifest.world_catalog import WorldCatalog
from shibuya.world.processes.records import (
    AnnouncementScope,
    Clock,
    Executor,
    Modality,
    NormKind,
    PlanSpec,
    ProcessKind,
    Validity,
    Violability,
    WorldProcess,
)
from shibuya.world.processes.registry import WorldRegistry

#: テスト用の小さなカタログ(凍結カタログを読まずに済ませる)。
TEST_CATALOG_CLASSES = (
    "混雑場(密度)",
    "騒音場",
    "営業(開閉店)",
    "天候・気温(+生成器)",
    "ダイヤ・営業時間・価格表(PlanSpec)",
)


def make_growth(name: str = "g_test", **kw: Any) -> GrowthDeclaration:
    base: dict[str, Any] = dict(
        name=name,
        per_agent_bytes=0,
        per_cell_bytes=8,
        per_day_growth="O(1)",
        per_day_growth_coef=0.0,
        retention=Retention(None, ""),
        worst_case_ops_per_tick=100,
        cap=1024,
    )
    base.update(kw)
    return GrowthDeclaration(**base)


def make_process(pid: str = "p_test", **kw: Any) -> WorldProcess:
    base: dict[str, Any] = dict(
        id=pid,
        kind=ProcessKind.AGGREGATE,
        state_vars=("x",),
        update_rule="テスト用の更新規則",
        clock=Clock.PHYSICAL,
        modality=Modality.DERIVED_FROM_ACTIONS,
        executor=Executor.NONE,
        growth=make_growth(f"g_{pid}"),
        catalog_classes=("混雑場(密度)",),
        gate_condition="テスト用の門前条件(パターン照合1行)",
        reaches=("人物①",),
    )
    base.update(kw)
    return WorldProcess(**base)


def make_plan_spec(sid: str = "plan.test", **kw: Any) -> PlanSpec:
    base: dict[str, Any] = dict(
        id=sid,
        content="テスト用の計画内容",
        validity=Validity(0, None),
        version=1,
        revising_authority="店主エージェント",
        norm_kind=NormKind.REGULATIVE,
        violability=Violability.UNENFORCED,
        announcement_scope=AnnouncementScope(
            kinds=("住民",), cells=("*",), blocks=("B2",), channel_ids=("看板(a)",)
        ),
        compliance_field="test_compliance_rate",
        catalog_classes=("ダイヤ・営業時間・価格表(PlanSpec)",),
        gate_condition="テスト用の門前条件",
    )
    base.update(kw)
    return PlanSpec(**base)


@pytest.fixture()
def test_catalog() -> WorldCatalog:
    return WorldCatalog(
        version="test",
        sha16="0" * 16,
        columns=("クラス",),
        rows=tuple({"クラス": c} for c in TEST_CATALOG_CLASSES),
    )


@pytest.fixture()
def registry(test_catalog: WorldCatalog) -> WorldRegistry:
    return WorldRegistry("test-ledger", catalog=test_catalog)
