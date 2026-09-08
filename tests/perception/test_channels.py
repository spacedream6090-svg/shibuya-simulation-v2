"""channels: §3.2 チャネル別トークン上限表・根拠等級・有界化(行を割らない切り詰め)。"""

from __future__ import annotations

import pytest

from shibuya.perception import channels as C
from shibuya.perception.templates import BLOCK_TOKEN_BUDGET


def test_channel_table_matches_contract_section_3_2():
    """§3.2 の表(内訳 → tok・等級)を逐語で持っている。"""
    expected = {
        "B5.near_person": (100, C.Grade.A),
        "B5.intero": (40, C.Grade.C),
        "B5.self": (65, C.Grade.E),
        "B5.watched": (15, C.Grade.E),
        "B2.ground": (40, C.Grade.A),
        "B2.visible": (60, C.Grade.C),
        "B2.signage": (25, C.Grade.C),
        "B2.landmark": (25, C.Grade.E),
        "B4.density": (25, C.Grade.A),
        "B4.noise": (10, C.Grade.D),
        "B4.salient": (25, C.Grade.B),
        "B4b.near": (40, C.Grade.C),
    }
    got = {c.channel_id: (c.tokens, c.grade) for c in C.CHANNEL_LIMITS}
    assert got == expected


def test_channel_totals_equal_the_block_budgets():
    """縦計が §2.2 のブロック予算に一致(B5 220 / B2 150 / B4 60 / B4b 40)。"""
    for block in ("B5", "B2", "B4", "B4b"):
        assert C.block_channel_total(block) == BLOCK_TOKEN_BUDGET[block], block


def test_grades_map_to_mechanism_or_expedient():
    assert C.Grade.A.mechanism and C.Grade.B.mechanism
    assert not C.Grade.C.mechanism and not C.Grade.D.mechanism and not C.Grade.E.mechanism
    for c in C.CHANNEL_LIMITS:
        assert c.tag in ("mechanism", "expedient")


def test_intentional_distortion_note_is_present():
    """§3.2 の「反対証拠の明記」はコードに残す(消したら契約違反)。"""
    assert "意図的な歪み" in C.INTENTIONAL_DISTORTION_NOTE
    assert "Fotios 2014" in C.INTENTIONAL_DISTORTION_NOTE


def test_estimate_tokens_matches_the_llm_side_convention():
    """``llm.estimate_tokens``(文字数÷2・最低1)との二重定義が一致している。"""
    llm = pytest.importorskip("shibuya.llm")
    for s in ("", "a", "あ" * 7, "[B4 密度] 歩行者密度は段階Cです。", "x" * 1000):
        assert C.estimate_tokens(s) == llm.estimate_tokens(s), s


def test_truncation_never_splits_a_line():
    lines = ["あ" * 30, "い" * 30, "う" * 30]  # 各 15 tok
    kept, rep = C.truncate_lines(lines, "B4.salient", limit_tokens=25, max_items=None)
    assert kept == [lines[0]]  # 15 は入り 30 は入らない → 1 行だけ
    assert all(k in lines for k in kept)  # 行の途中では切らない
    assert rep.dropped == 2 and rep.truncated
    assert rep.tokens_after <= 25


def test_truncation_respects_item_count_cap():
    lines = ["a", "b", "c", "d", "e"]
    kept, rep = C.truncate_lines(lines, "B2.visible")  # max_items=3
    assert len(kept) == 3 and rep.dropped == 2


def test_truncation_reports_no_truncation_when_it_fits():
    kept, rep = C.truncate_lines(["a"], "B4.noise")
    assert kept == ["a"] and not rep.truncated and rep.dropped == 0


def test_unknown_channel_requires_explicit_limit():
    with pytest.raises(KeyError):
        C.truncate_lines(["a"], "B9.nope")
    kept, _ = C.truncate_lines(["a"], "B9.nope", limit_tokens=10)
    assert kept == ["a"]


def test_budget_mode_has_the_mandatory_ablation_arm():
    """§3.2 の**義務 ablation**「固定枠 vs 単一ランキング」の枠がある。"""
    assert C.BudgetMode.FIXED_SLOTS.value == "fixed_slots"
    assert C.BudgetMode.SINGLE_RANKING.value == "single_ranking"
