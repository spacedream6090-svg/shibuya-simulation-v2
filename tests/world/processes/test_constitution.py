"""憲法5 の機械検査(D-R2-4)と、id 集合の凍結写し ↔ Markdown の一致。"""

from __future__ import annotations

import pytest

from shibuya.manifest.world_catalog import WorldCatalog
from shibuya.world.processes import constitution as C
from shibuya.world.processes.records import AnnouncementScope, DetailDeclaration
from shibuya.world.processes.registry import WorldRegistry
from tests.world.processes.conftest import make_plan_spec, make_process


# ---------------------------------------------------------------- 凍結写し ↔ Markdown
def test_perception_channel_ids_match_the_contract():
    """知覚契約書 §3 の表を読み直して凍結写しと一致することを見る(正典は Markdown)。"""
    assert C.parse_perception_channel_ids() == C.PERCEPTION_CHANNEL_IDS


def test_pattern_ledger_ids_match_the_frozen_list():
    parsed = C.parse_pattern_ledger_ids()
    assert parsed.active == C.PATTERN_IDS
    assert parsed.sealed == C.SEALED_PATTERN_IDS
    assert parsed.discarded == C.DISCARDED_PATTERN_IDS


def test_suspended_channel_is_in_the_table_but_not_usable():
    assert set(C.SUSPENDED_CHANNEL_IDS) <= set(C.PERCEPTION_CHANNEL_IDS)


def test_proposed_channel_ids_are_not_in_the_contract():
    """PROPOSED は「まだ §3 に無い」もの。既定の検査集合にも入っていない。"""
    assert not set(C.PROPOSED_CHANNEL_IDS) & set(C.PERCEPTION_CHANNEL_IDS)


def test_parsers_accept_explicit_paths(tmp_path):
    md = tmp_path / "p.md"
    md.write_text(
        "| チャネル | 要素 |\n|---|---|\n| 可視性 | x |\n| 人物① | y |\n",
        encoding="utf-8",
    )
    assert C.parse_perception_channel_ids(md) == ("可視性", "人物①")
    md2 = tmp_path / "l.md"
    md2.write_text("| ID | パターン |\n|---|---|\n| A1 | x |\n| ~~D2~~ | y |\n", encoding="utf-8")
    ids = C.parse_pattern_ledger_ids(md2)
    assert ids.active == ("A1",) and ids.discarded == ("D2",)


# ---------------------------------------------------------------- check_declaration
def _decl(reaches=(), contributes=()):
    return C.check_declaration(
        "world_process",
        "p",
        reaches,
        contributes,
        channel_ids=C.PERCEPTION_CHANNEL_IDS,
        pattern_ids=C.PATTERN_IDS,
        output_ids=C.DIAGNOSTIC_OUTPUT_IDS,
    )


def test_positive_declaration_passes():
    v, vanished = _decl(reaches=("人物①",), contributes=("D1′",))
    assert v == () and vanished == ()


def test_output_ids_satisfy_b():
    v, _ = _decl(contributes=("cog_lane_coverage",))
    assert v == ()


def test_empty_declaration_is_a_violation():
    v, _ = _decl()
    assert [x.code for x in v] == ["C5-EMPTY"]


def test_unknown_ids_are_violations():
    v, vanished = _decl(reaches=("嗅覚未満",), contributes=("Z99",))
    assert [x.code for x in v] == ["C5-UNKNOWN-TARGET", "C5-UNKNOWN-TARGET"]
    assert set(vanished) == {"嗅覚未満", "Z99"}


def test_suspended_channel_is_rejected():
    v, _ = _decl(reaches=("嗅覚",))
    assert [x.code for x in v] == ["C5-SUSPENDED-CHANNEL"]


def test_sealed_pattern_is_rejected():
    """パターン台帳 §2 運用規則5「以後の設計議論で言及・参照しない」。"""
    v, _ = _decl(contributes=("S3",))
    assert [x.code for x in v] == ["C5-SEALED-PATTERN"]


def test_discarded_pattern_is_rejected():
    v, _ = _decl(contributes=("D2",))
    assert [x.code for x in v] == ["C5-DISCARDED-PATTERN"]


def test_slots_are_not_interchangeable():
    """パターン id を reaches に書くのは違反(スロットが違う)。"""
    v, _ = _decl(reaches=("D1′",))
    assert [x.code for x in v] == ["C5-UNKNOWN-TARGET"]


# ---------------------------------------------------------------- check_constitution5
def _registry(test_catalog: WorldCatalog) -> WorldRegistry:
    return WorldRegistry("t", catalog=test_catalog, strict=False)


def test_report_ok_for_a_good_ledger(test_catalog):
    reg = _registry(test_catalog)
    reg.add_process(make_process("a", reaches=("人物①",), contributes=("D1′",)))
    reg.add_plan_spec(make_plan_spec("plan.x"))
    reg.add_detail(
        DetailDeclaration(id="d", owner_process_id="a", description="x", reaches=("人物②",))
    )
    rep = C.check_constitution5(reg)
    assert rep.ok
    assert (rep.n_processes, rep.n_plan_specs, rep.n_details) == (1, 1, 1)
    assert rep.deletion_candidates == ()
    assert "OK" in rep.as_text()


def test_vanished_target_becomes_a_deletion_candidate(test_catalog):
    """「宣言した届き先が消えた細部は、削除候補として台帳に自動的に載る」(§5)。"""
    reg = _registry(test_catalog)
    reg.add_process(make_process("a", reaches=(), contributes=("D1′",)))
    # 台帳から D1′ が消えた世界を模す
    rep = C.check_constitution5(reg, pattern_ids=[p for p in C.PATTERN_IDS if p != "D1′"])
    assert not rep.ok
    assert [c.subject_id for c in rep.deletion_candidates] == ["a"]
    assert rep.deletion_candidates[0].vanished_targets == ("D1′",)
    assert "削除候補" in rep.as_text()


def test_partially_vanished_target_is_not_a_deletion_candidate(test_catalog):
    reg = _registry(test_catalog)
    reg.add_process(make_process("a", reaches=("人物①",), contributes=("D1′",)))
    rep = C.check_constitution5(reg, pattern_ids=[p for p in C.PATTERN_IDS if p != "D1′"])
    assert not rep.ok  # 参照先が1本消えたので違反ではある
    assert rep.deletion_candidates == ()  # だが「全部消えた」ではない


def test_undeclared_detail_becomes_a_deletion_candidate(test_catalog):
    """知覚契約書 §1 不変条件2「宣言のない細部は削除候補として台帳に自動掲載」。"""
    reg = _registry(test_catalog)
    reg.add_process(make_process("a"))
    reg.add_detail(DetailDeclaration(id="d", owner_process_id="a", description="x"))
    rep = C.check_constitution5(reg)
    assert [c.subject_id for c in rep.deletion_candidates] == ["d"]
    assert "宣言もない" in rep.deletion_candidates[0].reason


def test_plan_spec_scope_violation_is_reported(test_catalog):
    """型を迂回して作られた PlanSpec(公示範囲が空)も検査で捕まる。"""
    s = make_plan_spec("plan.x")
    object.__setattr__(s, "announcement_scope", AnnouncementScope())
    reg = _registry(test_catalog)
    reg._plan_specs[s.id] = s  # noqa: SLF001 — 型検査を迂回した壊れた台帳を作る
    rep = C.check_constitution5(reg)
    codes = {v.code for v in rep.violations}
    assert "C5-PLANSPEC-SCOPE" in codes


def test_plan_spec_compliance_field_violation_is_reported(test_catalog):
    s = make_plan_spec("plan.x")
    object.__setattr__(s, "compliance_field", "")
    reg = _registry(test_catalog)
    reg._plan_specs[s.id] = s  # noqa: SLF001
    rep = C.check_constitution5(reg)
    assert "C5-PLANSPEC-COMPLIANCE" in {v.code for v in rep.violations}


def test_detected_at_is_optional_and_deterministic(test_catalog):
    reg = _registry(test_catalog)
    reg.add_process(make_process("a"))
    reg.add_detail(DetailDeclaration(id="d", owner_process_id="a", description="x"))
    assert C.check_constitution5(reg).deletion_candidates[0].detected_at == ""
    stamped = C.check_constitution5(reg, detected_at="2026-09-08")
    assert stamped.deletion_candidates[0].detected_at == "2026-09-08"


def test_missing_doc_raises(monkeypatch, tmp_path):
    missing = tmp_path / "no-such.md"
    with pytest.raises(FileNotFoundError):
        C.parse_perception_channel_ids(missing)
