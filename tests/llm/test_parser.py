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
from shibuya.llm.parser import (
    CANONICAL_LABELS,
    LABEL_ALIASES,
    LABEL_ALIASES_C6,
    LABEL_ALIASES_V0,
    find_action_word,
    parse_two_line,
)

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


# ---------------------------------------------------------------- C6 パーサ許容(2026-09-09)
# 初回実LLMスモーク(5,000体×24tick・Qwen3-8B INT8・温度0)のテープに実際に出た3例。
# 契約書の決定項(2行形・12語+役割語)は不変で、**パーサ側の許容**として受ける。
SMOKE_目的地 = "理由: 飲食店が近くにあるため  \n行動: 乗車 目的地: 飲食店 ひと言: なにが売ってますか"
SMOKE_目的 = "理由: 飲食店を探すため  \n行動: 移動 目的: 飲食店 ひと言: どこで食べられるか探してみる"
SMOKE_観察 = "理由: 深夜営業時間外の飲食店を確認  \n行動: 観察 対象: 物のカテゴリ ひと言: なし"


def test_c6_smoke_目的地_is_read_as_対象():
    r = parse_two_line(SMOKE_目的地)
    assert r.action == "乗車" and r.ok and r.format_ok
    assert r.target.kind is TargetKind.ITEM_CATEGORY and r.target.category == "飲食店"
    assert r.reason == "飲食店が近くにあるため"  # 行末の空白を吸収
    assert r.comment == "なにが売ってますか"
    assert r.alias_used and r.label_alias_used and r.alias_surfaces == ("目的地",)
    assert not r.strict_format_ok, "受入指標(従来定義)は別名を数えない"
    assert r.errors == ()


def test_c6_smoke_目的_is_read_as_対象():
    r = parse_two_line(SMOKE_目的)
    assert r.action == "移動" and r.format_ok and not r.strict_format_ok
    assert r.target.category == "飲食店" and r.alias_surfaces == ("目的",)
    assert r.reason == "飲食店を探すため"


def test_c6_smoke_観察_is_a_vocabulary_problem_not_a_label_problem():
    """3例目はラベルは正しく**行動語だけが語彙外**=書式は落ちたまま §7 段0 へ回る。"""
    r = parse_two_line(SMOKE_観察)
    assert r.action is None and r.action_code == UNDEFINED_ACTION
    assert r.raw_action == "観察" and "unknown_action_word" in r.errors
    assert not r.alias_used and not r.format_ok and not r.strict_format_ok
    assert not r.dictionary_mapped


def test_c6_dictionary_mapping_is_carried_on_the_parse_result():
    """段0 の写像は ``undefined`` の仕事。パーサは**結果を載せる口**だけ持つ。"""
    r = parse_two_line(SMOKE_観察).with_dictionary_mapping("待機")
    assert r.action == "待機" and r.action_code == 4 and r.dictionary_mapped
    assert r.raw_action == "観察"
    # 生の応答の記述(書式・errors)は書き換えない
    assert not r.format_ok and not r.strict_format_ok
    assert "unknown_action_word" in r.errors


def test_c6_dictionary_mapping_keeps_role_word_flag():
    r = parse_two_line(SMOKE_観察).with_dictionary_mapping("接客")
    assert r.action == "接客" and r.is_role_action and r.action_code == 12


@pytest.mark.parametrize(
    "surface,canonical",
    sorted((s, c) for s, c in LABEL_ALIASES_C6.items()),
)
def test_c6_every_new_alias_is_accepted_and_flagged(surface, canonical):
    fields = {"理由": "あああ", "行動": "待機", "対象": "なし", "ひと言": "いいい"}
    fields.pop(canonical)
    body = " ".join(f"{k}: {v}" for k, v in fields.items())
    text = f"{body} {surface}: {'待機' if canonical == '行動' else 'ううう'}"
    r = parse_two_line(text)
    assert canonical in r.labels
    assert r.format_ok and not r.strict_format_ok
    assert r.alias_used and surface in r.alias_surfaces


def test_v0_aliases_stay_inside_the_old_acceptance_metric():
    """``行き先``/``一言`` は C6 以前からの別名=``strict_format_ok`` は**真のまま**。"""
    r = parse_two_line("理由: 眠い\n行動: 就寝 行き先: C-3 一言: おやすみ")
    assert r.format_ok and r.strict_format_ok
    assert r.alias_used and r.alias_surfaces == ("行き先", "一言")


def test_canonical_labels_are_not_counted_as_aliases():
    r = parse_two_line(TWO_LINE)
    assert not r.alias_used and r.alias_surfaces == ()
    assert r.format_ok and r.strict_format_ok


def test_c6_full_width_colon_and_full_width_space_with_aliases():
    r = parse_two_line("理由：眠い\n行動：就寝　場所：C-3　コメント：おやすみ")
    assert r.action == "就寝" and r.target.cell_index == 3 and r.comment == "おやすみ"
    assert r.format_ok and not r.strict_format_ok
    assert r.alias_surfaces == ("場所", "コメント")


def test_c6_spaces_around_the_label_are_absorbed():
    r = parse_two_line("理由 :  眠い\n行動  :  就寝  目的地 : C-3   ひと言 :  おやすみ  ")
    assert r.action == "就寝" and r.target.cell_index == 3
    assert r.reason == "眠い" and r.comment == "おやすみ" and r.format_ok


def test_c6_escaped_newline_is_read_as_a_line_break():
    """テープに ``ため  \\n行動:`` の形(literal backslash-n)で残った応答も読む。"""
    text = "理由: 飲食店が近くにあるため  \\n行動: 乗車 目的地: 飲食店 ひと言: なし"
    assert "\n" not in text  # 実改行は無い
    r = parse_two_line(text)
    assert r.action == "乗車" and r.format_ok
    assert r.reason == "飲食店が近くにあるため"


def test_c6_trailing_escaped_newline_inside_a_value_is_dropped():
    r = parse_two_line("理由: あああ\\n\n行動: 待機 対象: なし ひと言: なし")
    assert r.reason == "あああ" and r.action == "待機" and r.format_ok


def test_c6_first_occurrence_wins_when_both_対象_and_目的地_appear():
    r = parse_two_line("理由: あああ\n行動: 移動 対象: C-1 目的地: C-2 ひと言: なし")
    assert r.labels["対象"] == "C-1" and r.target.cell_index == 1


# ---------------------------------------------------------------- C6 位置引数(2026-09-09 夕)
# `--fleet-debug-dir` 60tick/2,083呼の失敗 531 の内訳: missing_label:対象 226・対象+ひと言 78・
# ひと言 6 = **ラベルを省いて値だけを契約の順序で並べた**形。欄順は §1 で固定なので位置で読む。
def test_c6_positional_both_values_after_the_action_word():
    r = parse_two_line("理由: 予定の時間\n行動: 移動 なし なし")
    assert r.action == "移動" and r.ok and r.format_ok
    assert r.target.is_none and r.comment == NO_TARGET
    assert r.positional_used and not r.strict_format_ok
    assert r.raw_action == "移動", "raw_action は語彙語だけ(「移動 なし」ではない)"
    assert r.alias_surfaces == ("positional",) and not r.alias_used
    assert {"positional:対象", "positional:ひと言"} <= set(r.errors)
    assert {"missing_label:対象", "missing_label:ひと言"} <= set(r.errors), "生の欠落は記録に残す"


def test_c6_positional_only_対象_is_missing():
    r = parse_two_line("理由: 予定の時間\n行動: 待機 なし ひと言: なし")
    assert r.action == "待機" and r.format_ok and not r.strict_format_ok
    assert r.target.is_none and r.comment == NO_TARGET
    assert r.positional_used and r.errors.count("positional:対象") == 1
    assert "positional:ひと言" not in r.errors


def test_c6_positional_without_a_second_value_defaults_ひと言_to_なし():
    r = parse_two_line("理由: 腹が減った\n行動: 購入 物のカテゴリ")
    assert r.action == "購入" and r.format_ok and not r.strict_format_ok
    assert r.target.kind is TargetKind.ITEM_CATEGORY and r.target.category == "物のカテゴリ"
    assert r.comment == NO_TARGET and "comment_defaulted" in r.errors


def test_c6_positional_ひと言_pushed_into_the_対象_field():
    r = parse_two_line("理由: 予定の時間\n行動: 待機 対象: なし なし")
    assert r.action == "待機" and r.format_ok and not r.strict_format_ok
    assert r.target.is_none and r.comment == NO_TARGET
    assert r.positional_used and "positional:ひと言" in r.errors


def test_c6_positional_ひと言_keeps_its_spaces():
    """対象は1トークン・ひと言は**残り全部**(自由文なので落とさない)。"""
    r = parse_two_line("理由: 話したい\n行動: 会話 P-204 こんにちは 元気ですか")
    assert r.action == "会話" and r.format_ok
    assert r.target.kind is TargetKind.PERSON and r.target.person_id == 204
    assert r.comment == "こんにちは 元気ですか"


def test_c6_positional_values_are_free_text_and_are_not_rejected():
    """対象/ひと言は自由文=意味不明でも落とさない(切り詰め規則は従来どおり)。"""
    r = parse_two_line(f"理由: あああ\n行動: 待機 ???? {'い' * 30}")
    assert r.action == "待機" and r.format_ok
    assert r.target.raw == "????" and len(r.comment) == 20 and r.comment_truncated


def test_c6_positional_with_a_label_alias_in_the_same_line():
    r = parse_two_line("理由: あああ\n行動: 移動 目的: C-1 なし")
    assert r.action == "移動" and r.format_ok and not r.strict_format_ok
    assert r.target.cell_index == 1 and r.comment == NO_TARGET
    assert r.alias_used and r.positional_used
    assert r.alias_surfaces == ("目的", "positional")


def test_c6_positional_does_not_fire_when_the_action_word_is_not_the_first_token():
    """「行動: すぐに 移動 なし」型は位置で読める形ではない=触らない(誤読の予防)。"""
    r = parse_two_line("理由: 眠い\n行動: すぐに 移動 なし")
    assert r.action == "移動" and not r.positional_used
    assert not r.format_ok and "missing_label:対象" in r.errors
    assert r.raw_action == "すぐに 移動 なし"


def test_c6_positional_does_not_fire_without_a_spare_token():
    r = parse_two_line("理由: 眠い\n行動: 就寝 ひと言: おやすみ")
    assert not r.positional_used and not r.format_ok


def test_c6_positional_with_an_unknown_action_word_still_recovers_the_slots():
    r = parse_two_line("理由: 気分\n行動: 探索 飲食店 みつけたい")
    assert r.action is None and r.raw_action == "探索"
    assert r.positional_used and r.target.category == "飲食店" and r.comment == "みつけたい"
    assert not r.format_ok, "語彙外は書式順守にしない(親決定 09-09)"
    assert r.dictionary_candidate == "移動"


# ---- 段0 で救える語かどうかの診断(写像そのものは undefined 側の仕事) ----
@pytest.mark.parametrize(
    "word,candidate",
    [("探索", "移動"), ("通勤", "移動"), ("観察", "待機"), ("調査", "待機"), ("ジャンプ", None)],
)
def test_c6_dictionary_candidate_is_reported_at_the_first_judgement(word, candidate):
    r = parse_two_line(f"理由: あああ\n行動: {word} 対象: なし ひと言: なし")
    assert r.action is None and r.dictionary_candidate == candidate
    assert not r.format_ok and not r.dictionary_mapped


def test_c6_dictionary_candidate_is_empty_when_the_word_is_in_the_vocabulary():
    r = parse_two_line(TWO_LINE)
    assert r.action == "移動" and r.dictionary_candidate is None


# ---- 陰性(別名の許容が「何でも通す」に変わっていないこと) ----
def test_c6_a_missing_label_is_still_a_format_error():
    r = parse_two_line("理由: 眠い\n行動: 就寝 ひと言: おやすみ")
    assert not r.format_ok and not r.strict_format_ok
    assert "missing_label:対象" in r.errors and not r.alias_used


def test_c6_three_lines_with_free_prose_is_still_a_format_error():
    r = parse_two_line("理由: 眠い\n行動: 就寝\nおやすみなさい")
    assert not r.format_ok and not r.strict_format_ok
    assert {"missing_label:対象", "missing_label:ひと言"} <= set(r.errors)


def test_c6_out_of_vocabulary_and_out_of_dictionary_word_stays_undefined():
    """語彙外かつ辞書外は**拾わない**(=§7 段1 へ。段0 の表は undefined 側のテスト)。"""
    r = parse_two_line("理由: 気分だ\n行動: ジャンプ 目的地: C-1 ひと言: なし")
    assert r.action is None and r.raw_action == "ジャンプ"
    assert not r.format_ok and "unknown_action_word" in r.errors
    assert r.alias_used  # ラベル別名は効いているが、それだけでは ok にならない
    assert not r.ok


def test_c6_alias_table_shapes():
    assert set(LABEL_ALIASES) == set(LABEL_ALIASES_V0) | set(LABEL_ALIASES_C6)
    assert not (set(LABEL_ALIASES_V0) & set(LABEL_ALIASES_C6)), "V0 と C6 は重ならない"
    assert set(LABEL_ALIASES.values()) == set(CANONICAL_LABELS)


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


#: 各正準ラベルの表層(正準 + C6 で許容した別名)。
_SURFACES = {
    canonical: (canonical, *sorted(s for s, c in LABEL_ALIASES_C6.items() if c == canonical))
    for canonical in CANONICAL_LABELS
}


@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
@given(
    action=st.sampled_from(list(ALL_ACTION_WORDS)),
    target=_TARGETS,
    order=st.permutations(CANONICAL_LABELS),
    surface_pick=st.tuples(*(st.sampled_from(_SURFACES[c]) for c in CANONICAL_LABELS)),
    packed=st.booleans(),
)
def test_label_order_and_alias_choice_do_not_change_the_reading(
    action, target, order, surface_pick, packed
):
    """ラベルの**順序**と**表層の選び方**を変えても、読み取り結果は変わらない。"""
    surface = dict(zip(CANONICAL_LABELS, surface_pick))
    value = {"理由": "あああ", "行動": action, "対象": target, "ひと言": "いいい"}
    parts = [f"{surface[c]}: {value[c]}" for c in order]
    text = " ".join(parts) if packed else "\n".join(parts)
    r = parse_two_line(text)
    assert r.action == action
    assert r.reason == "あああ" and r.comment == "いいい"
    assert r.format_ok and r.ok
    assert r.alias_used == any(surface[c] != c for c in CANONICAL_LABELS)
    if target == NO_TARGET:
        assert r.target.is_none
    else:
        assert r.target.raw == target
