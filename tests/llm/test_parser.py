"""llm.parser のテスト(ラベル基準の寛容行指向・**例外を投げない**・往復)。

正典: 知覚契約書 §2.5(寛容行指向・4行形と2行形を同じパーサで受理・ラベルを行内でも分割)・
行動契約書 §1(理由40字/ひと言20字)。
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from shibuya.llm.contract import (
    ALL_ACTION_WORDS,
    NO_TARGET,
    UNDEFINED_ACTION,
    TargetKind,
    format_two_line,
)
from shibuya.llm.parser import find_action_word, parse_two_line

TWO_LINE = "理由: 予定の時間になったから\n行動: 移動 対象: C-0117 ひと言: 少し急ごう"

FOUR_LINE_PROBE = (
    "理由: 目の前で人が倒れた\n"
    "行動: 通報\n"
    "行き先: なし\n"
    "ひと言: 誰か呼んで"
)


def test_strict_two_line_form():
    r = parse_two_line(TWO_LINE)
    assert r.action == "移動" and r.action_code == 0
    assert r.reason == "予定の時間になったから"
    assert r.comment == "少し急ごう"
    assert r.target.kind is TargetKind.CELL and r.target.cell_index == 117
    assert r.format_ok and r.strict_two_line and r.ok and r.errors == ()


def test_four_line_probe_form_is_accepted_and_行き先_maps_to_対象():
    r = parse_two_line(FOUR_LINE_PROBE)
    assert r.action == "通報" and r.format_ok
    assert r.labels["対象"] == NO_TARGET and r.target.is_none
    assert not r.strict_two_line  # 4行なので「厳密2行」ではない(指標は別)


def test_labels_packed_into_one_line_are_split():
    r = parse_two_line("理由: 腹が減った 行動: 購入 対象: おにぎり ひと言: いただきます")
    assert r.action == "購入" and r.format_ok
    assert r.reason == "腹が減った"
    assert r.target.kind is TargetKind.ITEM_CATEGORY and r.target.category == "おにぎり"


def test_fenced_and_bulleted_and_bold_output():
    text = (
        "```\n"
        "- **理由**: 疲れた\n"
        "* 行動: 休憩 対象: なし ひと言: ひと休み\n"
        "```"
    )
    r = parse_two_line(text)
    assert r.action == "休憩" and r.format_ok and r.reason == "疲れた"


def test_full_width_colon_and_brackets():
    r = parse_two_line("【理由】:眠い\n[行動]:就寝 [対象]:C-3 [ひと言]:おやすみ")
    assert r.action == "就寝" and r.target.cell_index == 3 and r.format_ok


def test_think_block_is_stripped():
    r = parse_two_line("<think>まず移動を考える…</think>\n理由: 腹が減った\n行動: 購入 対象: パン ひと言: なし")
    assert r.action == "購入" and r.format_ok


def test_particles_after_the_action_word():
    for tail in ("する", "します", "した", "しよう", "。"):
        r = parse_two_line(f"理由: 用事がある\n行動: 移動{tail} 対象: C-1 ひと言: なし")
        assert r.action == "移動", tail


def test_first_vocabulary_word_in_the_action_field_wins():
    r = parse_two_line("理由: 迷う\n行動: 会話してから移動 対象: P-2 ひと言: なし")
    assert r.action == "会話"


def test_role_word_is_recognised_and_flagged():
    r = parse_two_line("理由: 行列ができた\n行動: 接客 対象: P-9 ひと言: いらっしゃいませ")
    assert r.action == "接客" and r.is_role_action and r.action_code == 12 and r.format_ok


def test_unknown_action_word_is_not_guessed_when_the_label_exists():
    """行動ラベルがあるのに語彙外なら**拾わない**(=§7 段0 の辞書写像へ回す)。"""
    r = parse_two_line("理由: 腹が減った\n行動: 買う 対象: おにぎり ひと言: なし")
    assert r.action is None and r.action_code == UNDEFINED_ACTION
    assert r.raw_action == "買う"
    assert "unknown_action_word" in r.errors and not r.format_ok


def test_missing_action_label_falls_back_to_free_text():
    r = parse_two_line("理由: 眠い\nとりあえず休憩することにする")
    assert r.action == "休憩" and r.action_from_free_text
    assert not r.format_ok  # 書式順守ではない


def test_free_text_fallback_does_not_read_the_reason_field():
    """理由欄の中の語は拾わない(ラベル済みの範囲は走査対象外)。"""
    r = parse_two_line("理由: 移動したい気分だ\n対象: C-1\nひと言: なし")
    assert r.action is None


def test_truncation_is_a_flag_not_a_failure():
    long_reason = "あ" * 60
    long_comment = "い" * 30
    r = parse_two_line(f"理由: {long_reason}\n行動: 待機 対象: なし ひと言: {long_comment}")
    assert r.action == "待機" and r.format_ok
    assert len(r.reason) == 40 and len(r.comment) == 20
    assert r.reason_truncated and r.comment_truncated
    assert r.raw_reason == long_reason and r.raw_comment == long_comment


def test_duplicate_labels_keep_the_first_value():
    r = parse_two_line("理由: 一つ目\n理由: 二つ目\n行動: 待機 対象: なし ひと言: なし")
    assert r.reason == "一つ目"


@pytest.mark.parametrize(
    "text",
    ["", "   ", "\n\n", None, "```\n```", "{\"action\": \"移動\"}", "🙂🙂🙂"],
)
def test_degenerate_inputs_never_raise(text):
    r = parse_two_line(text)
    assert r is not None and isinstance(r.errors, tuple)


def test_find_action_word_prefers_the_earliest_then_longest():
    assert find_action_word("まず移動して会話する") == "移動"
    assert find_action_word("なにもない") is None


# ---------------------------------------------------------------- 性質テスト
_SAFE_CHARS = st.sampled_from(list("あいうえおかきくけこさしすせそたちつてとABCXYZ0123456789"))
_SAFE_TEXT = st.lists(_SAFE_CHARS, min_size=1, max_size=20).map("".join)
_TARGETS = st.sampled_from(["なし", "C-0117", "g12_34_GL", "P-204", "204", "おにぎり"])


@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
@given(st.text())
def test_random_junk_never_raises(text):
    r = parse_two_line(text)
    assert isinstance(r.errors, tuple)
    assert r.action is None or r.action in ALL_ACTION_WORDS


@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
@given(
    reason=_SAFE_TEXT,
    action=st.sampled_from(list(ALL_ACTION_WORDS)),
    target=_TARGETS,
    comment=_SAFE_TEXT,
)
def test_well_formed_output_round_trips_through_format_two_line(reason, action, target, comment):
    text = format_two_line(reason, action, target, comment)
    r = parse_two_line(text)
    assert r.format_ok and r.action == action
    assert r.reason == reason and r.comment == comment
    if target == NO_TARGET:
        assert r.target.is_none
    else:
        assert r.target.raw == target
