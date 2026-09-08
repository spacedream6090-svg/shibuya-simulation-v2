"""第1陣の宣言(D-R2-5 / §7.1-7.2)が**実物の設計書 id**に対して憲法5 検査を通ること。"""

from __future__ import annotations

import pytest

from shibuya.manifest.world_catalog import load_world_catalog, verify_frozen
from shibuya.world.processes import constitution as C
from shibuya.world.processes import first_batch as FB
from shibuya.world.processes.records import Executor, ProcessKind
from shibuya.world.processes.relations import Realizes


@pytest.fixture(scope="module")
def reg():
    return FB.build_registry()


# ---------------------------------------------------------------- 憲法5(実 id で)
def test_declarations_pass_constitution5_against_the_real_docs(reg):
    """知覚契約書 §3 とパターン台帳を**その場で読み直した** id 集合で検査する。"""
    channels = C.parse_perception_channel_ids()
    ledger = C.parse_pattern_ledger_ids()
    report = C.check_constitution5(reg, channels, ledger.active, C.DIAGNOSTIC_OUTPUT_IDS)
    assert report.ok, report.as_text()
    assert report.deletion_candidates == ()


def test_no_proposed_channel_is_used_silently(reg):
    """PROPOSED(=§3 に無い提案 id)を宣言に紛れ込ませない。"""
    used = {c for p in reg.processes for c in p.reaches}
    used |= {c for d in reg.details for c in d.reaches}
    used |= {
        c for s in reg.plan_specs for c in tuple(s.reaches) + s.announcement_scope.channel_ids
    }
    assert not used & set(FB.PROPOSED_CHANNEL_IDS)
    assert used <= set(C.PERCEPTION_CHANNEL_IDS)


def test_no_sealed_or_suspended_target(reg):
    contributed = {c for p in reg.processes for c in p.contributes}
    contributed |= {c for s in reg.plan_specs for c in s.contributes}
    assert not contributed & set(C.SEALED_PATTERN_IDS)
    assert not contributed & set(C.DISCARDED_PATTERN_IDS)
    reached = {c for p in reg.processes for c in p.reaches}
    assert not reached & set(C.SUSPENDED_CHANNEL_IDS)


# ---------------------------------------------------------------- D-R2-5 の6本が揃っている
def test_first_batch_covers_the_six_of_d_r2_5():
    ids = {p.id for p in FB.DECLARATIONS}
    assert {
        "daynight_solar",  # 昼夜(日照)
        "weather",  # 天候
        "rail_operation_static",  # 鉄道運行(ODPT 静的ダイヤ)
        "crowd_field",  # 混雑場(密度段階)
        "store_opening",  # 営業時間(PlanSpec=看板(a))
        "static_noise_field",  # 静的騒音場
    } <= ids


def test_first_batch_covers_the_u_goods_skeleton():
    ids = {p.id for p in FB.DECLARATIONS}
    assert {
        "goods_conservation",  # 物の保存則骨格
        "shelf_stock_restock",  # 店舗補充・棚在庫
        "delivery_inbound",  # 納品
        "waste_collection",  # 廃棄物収集
        "indoor_occupancy",  # 屋内占有の集約
        "vehicle_cross_section",  # 断面自動車交通
    } <= ids


def test_pulled_forward_batch_matches_7_2():
    ids = {p.id for p in FB.PULLED_FORWARD_DECLARATIONS}
    assert ids == {
        "delivery_last_mile",
        "bus_taxi_operation",
        "public_service_dispatch",
        "street_cleaning",
        "infra_daily_load",
        "hotel_room_inventory",
        "road_works_occupancy",
        "press_official_release",
        "large_event",
    }
    assert all(p.batch == FB.BATCH_PULLED_FORWARD for p in FB.PULLED_FORWARD_DECLARATIONS)


# ---------------------------------------------------------------- 型レベルの規律
def test_only_actual_log_grows_with_time():
    """§2「**O(t) 成長する唯一の型**が ActualLog」——世界過程の状態は全て O(1)。"""
    for p in FB.DECLARATIONS + FB.PULLED_FORWARD_DECLARATIONS:
        assert p.growth.order == "O(1)", p.id
        assert p.growth.per_day_growth_coef == 0.0, p.id


def test_growth_declaration_names_are_unique():
    decls = FB.growth_declarations()
    assert len(decls) == len(FB.DECLARATIONS) + len(FB.PULLED_FORWARD_DECLARATIONS)


def test_every_process_declares_a_catalog_class_in_the_frozen_catalog():
    cat = load_world_catalog()
    verify_frozen(cat)
    known = {r["クラス"] for r in cat.rows}
    for p in FB.DECLARATIONS + FB.PULLED_FORWARD_DECLARATIONS:
        assert set(p.catalog_classes) <= known, p.id


def test_expedients_carry_sensitivity_and_repayment():
    for p in FB.DECLARATIONS + FB.PULLED_FORWARD_DECLARATIONS:
        if not p.mechanism:
            assert p.sensitivity_test_id and p.repayment_due, p.id


def test_engine_rule_rows_are_all_on_the_fallback_ledger(reg):
    rows = reg.fallback_ledger()
    engine_ids = {p.id for p in reg.processes if p.executor is Executor.ENGINE_RULE}
    assert engine_ids <= {r.subject_id for r in rows}
    assert all(r.repayment_due for r in rows)
    assert all(0.0 < r.conf <= 1.0 for r in rows)


def test_fallback_rows_are_marked_as_agent_fallback_or_external():
    """engine_rule は §1「エージェント化できるのに代替」か、bbox 外(B類)に限る。"""
    for p in FB.DECLARATIONS + FB.PULLED_FORWARD_DECLARATIONS:
        if p.executor is Executor.ENGINE_RULE:
            assert p.kind in (ProcessKind.AGENT_FALLBACK, ProcessKind.EXTERNAL_SYSTEM), p.id


def test_natural_processes_are_not_fallbacks():
    for p in FB.DECLARATIONS:
        if p.kind is ProcessKind.NATURAL:
            assert p.executor is Executor.NONE and p.conf is None, p.id


# ---------------------------------------------------------------- PlanSpec と関係
def test_plan_specs_are_announced_and_measured():
    for s in FB.PLAN_SPECS:
        assert not s.announcement_scope.is_empty
        assert s.compliance_field
        assert set(s.announcement_scope.blocks) <= {"B2", "B3"}


def test_rail_and_opening_are_realized_by_engine_rule_for_now(reg):
    rel = {
        (r.subject_id, r.plan_spec_id): r
        for r in reg.relations
        if isinstance(r, Realizes)
    }
    assert rel[("rail_operation_static", "plan.rail_timetable")].executor is Executor.ENGINE_RULE
    assert rel[("store_opening", "plan.opening_hours")].executor is Executor.ENGINE_RULE
    assert rel[("bus_taxi_operation", "plan.bus_timetable")].executor is Executor.LLM_AGENT


def test_registry_hash_is_stable_across_builds():
    assert FB.build_registry().registry_hash() == FB.build_registry().registry_hash()


def test_coverage_report_is_reportable(reg):
    rep = reg.coverage_report()
    assert rep.n_processes == len(FB.DECLARATIONS) + len(FB.PULLED_FORWARD_DECLARATIONS)
    assert rep.catalog_n_classes == 57
    assert rep.by_executor[Executor.LLM_AGENT.value] > 0
    assert rep.catalog_coverage > 0.3  # 世界側の枠(4-5割)への足掛かり


def test_build_without_pulled_forward():
    reg = FB.build_registry(include_pulled_forward=False)
    assert len(reg.processes) == len(FB.DECLARATIONS)
    assert all(s.batch == FB.BATCH_FIRST for s in reg.plan_specs)
