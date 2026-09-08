"""normalize: バイト一致の正規化規約 9 項(知覚契約書 §2.4)。hypothesis の性質テストつき。"""

from __future__ import annotations

from datetime import datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shibuya.perception import normalize as N
from shibuya.perception.templates import DENSITY_LOS_EDGES_PER_M2


# ---------------------------------------------------------------- ⑨ 5分丸め
@pytest.mark.parametrize(
    "minute,expected", [(0, 0), (1, 0), (4, 0), (5, 5), (31, 30), (34, 30), (59, 55)]
)
def test_rule9_time_is_floored_to_5min(minute, expected):
    assert N.round_time_5min(datetime(2026, 7, 28, 12, minute)) == (12, expected)


def test_rule9_1231_and_1234_are_the_same_band():
    a = datetime(2026, 7, 28, 12, 31)
    b = datetime(2026, 7, 28, 12, 34)
    assert N.format_time(a) == N.format_time(b) == ("12", "30")
    assert N.time_band(a) == N.time_band(b)


def test_rule9_rejects_bad_round_width():
    with pytest.raises(ValueError):
        N.round_time_5min(datetime(2026, 7, 28, 12, 0), minutes=7)


# ---------------------------------------------------------------- ② ID 昇順
def test_rule2_sorts_numeric_then_string():
    assert N.sort_ids([10, 2, "b", "a"]) == ["2", "10", "a", "b"]


@given(st.lists(st.integers(min_value=0, max_value=10_000), max_size=30))
def test_rule2_sorting_is_permutation_invariant(ids):
    """入力の並び順を変えても結果は同じ(=列挙は ID 昇順で正準化される)。"""
    assert N.sort_ids(ids) == N.sort_ids(sorted(ids, reverse=True))


# ---------------------------------------------------------------- ③ 空白・改行
@given(st.text(max_size=200))
@settings(max_examples=200)
def test_rule3_whitespace_canonicalization_is_idempotent(s):
    once = N.canonical_whitespace(s)
    assert N.canonical_whitespace(once) == once


@given(st.text(max_size=200))
@settings(max_examples=200)
def test_rule3_canonical_form_has_no_stray_whitespace(s):
    out = N.canonical_whitespace(s)
    assert "\r" not in out
    assert "\t" not in out
    assert "　" not in out  # 全角空白は NFKC で半角へ
    for line in out.split("\n"):
        assert line == line.strip()
        assert "  " not in line


def test_rule3_join_lines_drops_blank_lines_and_uses_lf():
    assert N.join_lines(["a", "", "  ", "b"]) == "a\nb"


# ---------------------------------------------------------------- ①④ 数値・単位
def test_rule1_and_4_fixed_units():
    assert N.format_money(1200) == "1,200円"
    assert N.format_minutes(15) == "15分"
    assert N.format_meters(25.0) == "25メートル"
    assert N.UNITS["distance"] == "メートル"


# ---------------------------------------------------------------- ⑤ 段階の釘付け
def test_rule5_peg_stage_on_los_edges():
    assert N.peg_stage(0.0, DENSITY_LOS_EDGES_PER_M2) == 0  # LOS A
    assert N.peg_stage(0.30754, DENSITY_LOS_EDGES_PER_M2) == 1  # 境界は上の段
    assert N.peg_stage(0.6, DENSITY_LOS_EDGES_PER_M2) == 2
    assert N.peg_stage(9.9, DENSITY_LOS_EDGES_PER_M2) == 5  # LOS F


def test_rule5_peg_stage_array_matches_scalar():
    import numpy as np

    vals = np.array([0.0, 0.31, 0.5, 0.8, 1.5, 3.0])
    arr = N.peg_stage_array(vals, DENSITY_LOS_EDGES_PER_M2)
    assert list(arr) == [N.peg_stage(float(v), DENSITY_LOS_EDGES_PER_M2) for v in vals]


def test_rule5_rejects_non_monotone_edges():
    with pytest.raises(ValueError):
        N.peg_stage(1.0, (2.0, 1.0))


# ---------------------------------------------------------------- ⑥ 省略記法
def test_rule6_detects_abbreviations_in_enumerations():
    N.assert_no_abbreviation("見えるもの: 定食店A、コンビニ。")
    with pytest.raises(ValueError):
        N.assert_no_abbreviation("見えるもの: 定食店A、コンビニなど。")


# ---------------------------------------------------------------- ⑦ 空要素
def test_rule7_empty_phrase():
    assert N.or_empty([], "なし") == "なし"
    assert N.or_empty(["a", "b"], "なし") == "a、b"


# ---------------------------------------------------------------- ⑧ 個体依存語
@pytest.mark.parametrize(
    "text",
    [
        "[B2 可視] 見えるもの: P-12の店頭。",
        "[B4 行為] 所持金は1,200円です。",
        "[B4 行為] 空腹は8で閾値を超えています。",
        "[B2 場所] あなたを見ている人が1人います。",
        "[B2 場所] 直近の行動は移動です。",
    ],
)
def test_rule8_guard_catches_agent_dependent_words(text):
    with pytest.raises(N.AgentDependentWordError):
        N.assert_no_agent_dependent_words(text)


def test_rule8_guard_accepts_the_frozen_b0_prose():
    """B0 の散文(「所持金を超える支払い」「空腹・体力・体感温度は0から10」)は個体依存語ではない。"""
    from shibuya.perception.templates import TEMPLATES

    N.assert_no_agent_dependent_words(N.canonical_whitespace(TEMPLATES["B0.system"]))
