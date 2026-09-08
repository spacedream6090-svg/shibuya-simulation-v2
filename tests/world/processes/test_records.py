"""レコード型3(D-R2-2)の検査。"""

from __future__ import annotations

import pytest

from shibuya.world.processes.records import (
    ANNOUNCEMENT_BLOCKS,
    DEVIATION_BY_CODE,
    DEVIATION_CODES,
    ActualLogEntry,
    AnnouncementScope,
    Clock,
    DetailDeclaration,
    DeviationVocab,
    Executor,
    Modality,
    NormKind,
    ProcessKind,
    Validity,
    Violability,
)
from tests.world.processes.conftest import make_growth, make_plan_spec, make_process


# ---------------------------------------------------------------- WorldProcess
def test_minimal_process_is_valid():
    p = make_process()
    assert p.tag == "mechanism"
    assert p.is_fallback is False
    assert p.targets == ("人物①",)


@pytest.mark.parametrize(
    "kw, msg",
    [
        ({"gate_condition": "  "}, "門前条件"),
        ({"state_vars": ()}, "状態の定義"),
        ({"update_rule": ""}, "更新規則"),
        ({"catalog_classes": ()}, "catalog_classes"),
    ],
)
def test_required_fields(kw, msg):
    with pytest.raises(ValueError, match=msg):
        make_process(**kw)


def test_growth_declaration_is_required_by_type():
    """§3 実装原則2「状態成長の宣言を必須化」——型で強制する。"""
    with pytest.raises(TypeError, match="GrowthDeclaration"):
        make_process(growth="O(1)")  # type: ignore[arg-type]


def test_expedient_needs_sensitivity_and_repayment():
    with pytest.raises(ValueError, match="感度試験"):
        make_process(mechanism=False)
    ok = make_process(
        mechanism=False, sensitivity_test_id="AB-X", repayment_due="Phase 3"
    )
    assert ok.tag == "expedient"


def test_engine_rule_needs_conf_coverage_repayment():
    with pytest.raises(ValueError, match="conf"):
        make_process(executor=Executor.ENGINE_RULE)
    with pytest.raises(ValueError, match="カバー率"):
        make_process(executor=Executor.ENGINE_RULE, conf=0.5)
    p = make_process(
        executor=Executor.ENGINE_RULE,
        conf=0.5,
        coverage="全 POI",
        repayment_due="Phase 3",
    )
    assert p.is_fallback


def test_conf_only_on_engine_rule():
    with pytest.raises(ValueError, match="engine_rule"):
        make_process(executor=Executor.LLM_AGENT, conf=0.5)


def test_duplicate_ids_in_reaches_rejected():
    with pytest.raises(ValueError, match="重複"):
        make_process(reaches=("人物①", "人物①"))


def test_enum_fields_are_typed():
    with pytest.raises(TypeError, match="kind"):
        make_process(kind="A")  # type: ignore[arg-type]


def test_process_as_dict_is_json_ready():
    d = make_process().as_dict()
    assert d["kind"] == ProcessKind.AGGREGATE.value
    assert d["clock"] == Clock.PHYSICAL.value
    assert d["modality"] == Modality.DERIVED_FROM_ACTIONS.value
    assert d["norm_kind"] == NormKind.BRUTE_PHYSICAL.value
    assert d["violability"] == Violability.REGIMENTED.value
    assert isinstance(d["growth"], dict) and d["growth"]["per_day_growth"] == "O(1)"


def test_growth_name_is_free_but_declaration_shape_is_fixed():
    g = make_growth("g_x", per_day_growth="O(N)", per_day_growth_coef=12.0)
    assert g.order == "O(N)"
    assert g.declared_bytes_per_simday(n_entities=10) == 120.0


# ---------------------------------------------------------------- PlanSpec
def test_plan_spec_requires_announcement_scope():
    """D-R2-4「公示されない計画は(a)を満たさず作れない」。"""
    with pytest.raises(ValueError, match="公示範囲が空"):
        make_plan_spec(announcement_scope=AnnouncementScope())
    with pytest.raises(ValueError, match="公示範囲が空"):
        make_plan_spec(announcement_scope=AnnouncementScope(kinds=("住民",)))


def test_plan_spec_requires_compliance_field():
    with pytest.raises(ValueError, match="遵守率"):
        make_plan_spec(compliance_field="")


def test_announcement_blocks_are_b2_b3_only():
    assert ANNOUNCEMENT_BLOCKS == ("B2", "B3")
    with pytest.raises(ValueError, match="block"):
        AnnouncementScope(kinds=("住民",), blocks=("B5",))
    ok = AnnouncementScope(kinds=("住民",), blocks=("B3",))
    assert not ok.is_empty


def test_plan_spec_revision_bumps_version_and_transaction_time():
    s = make_plan_spec()
    s2 = s.revised(content="新しい内容", at_tick=100, authority="店主エージェント")
    assert (s2.version, s2.transaction_tick) == (2, 100)
    assert s.version == 1 and s.transaction_tick == 0  # 不変(旧版は残る)


def test_plan_spec_revision_rejects_wrong_authority():
    s = make_plan_spec()
    with pytest.raises(PermissionError, match="改訂権者"):
        s.revised(content="x", at_tick=1, authority="通行人")


def test_validity_covers():
    v = Validity(10, 20)
    assert not v.covers(9)
    assert v.covers(10) and v.covers(19)
    assert not v.covers(20)
    with pytest.raises(ValueError):
        Validity(10, 10)


# ---------------------------------------------------------------- ActualLogEntry
def test_deviation_codes_are_frozen_and_bijective():
    assert DEVIATION_CODES[DeviationVocab.SCHEDULED] == 0
    assert set(DEVIATION_BY_CODE) == set(range(len(DeviationVocab)))
    assert all(DEVIATION_BY_CODE[v] == k for k, v in DEVIATION_CODES.items())


def test_delay_minutes_iff_delay():
    e = ActualLogEntry(0, 1, "p", 5, DeviationVocab.DELAY, 3)
    assert e.delay_minutes == 3 and not e.is_compliant
    with pytest.raises(ValueError, match="DELAY"):
        ActualLogEntry(0, 1, "p", 5, DeviationVocab.DELAY, 0)
    with pytest.raises(ValueError, match="delay_minutes"):
        ActualLogEntry(0, 1, "p", 5, DeviationVocab.CANCELED, 3)


def test_scheduled_is_the_compliance_numerator():
    assert ActualLogEntry(0, 1, "p", 5, DeviationVocab.SCHEDULED).is_compliant
    assert not ActualLogEntry(0, 1, "p", 5, DeviationVocab.SKIPPED).is_compliant


# ---------------------------------------------------------------- DetailDeclaration
def test_detail_requires_description():
    with pytest.raises(ValueError, match="description"):
        DetailDeclaration(id="d", owner_process_id="p", description=" ")
    d = DetailDeclaration(
        id="d", owner_process_id="p", description="影グリッド", reaches=("内受容",)
    )
    assert d.targets == ("内受容",)
