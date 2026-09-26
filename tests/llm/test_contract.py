"""llm.contract の**転記テスト**(行動契約書 §2.1/§2.2 の表が1行も欠けていないこと)。

正典: docs/design/v2-action-contract.md §1(出力形)・§2(語彙は全種別共通・上限24語)・
§2.1(種別横断12語)・§2.2(種別固有=権限保持者つき)。
"""

from __future__ import annotations

import pytest

from shibuya.llm.contract import (
    ACTION_CODES,
    ACTION_SPECS,
    ACTION_VOCAB_12,
    ALL_ACTION_WORDS,
    COMMENT_MAX_CHARS,
    NO_TARGET,
    REASON_MAX_CHARS,
    ROLE_ACTION_CODES,
    ROLE_ACTION_WORDS,
    ROLE_ACTIONS,
    TWO_LINE_RE,
    VOCAB_LIMIT_PER_KIND,
    ActionSpec,
    TargetKind,
    action_code_of,
    format_two_line,
    parse_target,
    spec_of,
)

# 契約書 §2.1 の表(行動語 → 対象の型)を**テスト側にも独立に書き写す**(片方だけ直せば落ちる)。
SECTION_2_1 = {
    "移動": TargetKind.CELL,
    "乗車": TargetKind.STATION_OR_VEHICLE,
    "降車": TargetKind.CELL,
    "購入": TargetKind.ITEM_CATEGORY,
    "待機": TargetKind.NONE,
    "会話": TargetKind.PERSON,
    "退去": TargetKind.NONE,
    "通報": TargetKind.EVENT,
    "手伝い": TargetKind.PERSON,
    "断る": TargetKind.PERSON,
    "休憩": TargetKind.NONE,
    "就寝": TargetKind.CELL,
}

# 契約書 §2.2「権限保持者」列。
SECTION_2_2 = {
    "接客": "従業者",
    "補充": "従業者",
    "開閉店": "従業者(権限)",
    "価格改定": "従業者(権限)/本部",
    "発車": "乗務員",
    "停車": "乗務員",
    "放送": "乗務員/駅員",
    "遅延報告": "乗務員",
    "計画改訂": "指令(権限)",
    "指示": "指令",
    "並ぶ": "全員",
    "撮影": "全員",
}

#: 契約書が「失敗しない」と明記した行。
NEVER_FAILS = {"待機", "退去", "断る", "休憩"}


def test_the_twelve_words_are_the_contract_table_in_order():
    assert ACTION_VOCAB_12 == tuple(SECTION_2_1)
    assert len(ACTION_VOCAB_12) == 12


@pytest.mark.parametrize("word", list(SECTION_2_1))
def test_every_2_1_word_has_a_spec_with_target_kind_and_failures(word):
    spec = spec_of(word)
    assert isinstance(spec, ActionSpec)
    assert spec.section == "2.1"
    assert spec.target_declared is True, "§2.1 の表には「対象」列がある"
    assert spec.target_kind is SECTION_2_1[word]
    assert spec.precondition_text and spec.effects and spec.failure_text
    if word in NEVER_FAILS:
        assert spec.never_fails and spec.failure_codes == ()
        assert "失敗しない" in spec.failure_text
    else:
        assert not spec.never_fails and spec.failure_codes


@pytest.mark.parametrize("word,holder", sorted(SECTION_2_2.items()))
def test_every_role_word_carries_its_permission_holder(word, holder):
    assert ROLE_ACTIONS[word] == holder
    spec = spec_of(word)
    assert spec is not None and spec.is_role and spec.section == "2.2"
    assert spec.permission_holder == holder
    assert spec.target_declared is False, "§2.2 の表に「対象」列は無い(推定=expedient)"
    assert spec.failure_text and spec.failure_codes


def test_role_words_split_from_the_shared_table_rows():
    """「発車/停車」「並ぶ/撮影」は表では1行=2語に割った(元の行名を残す)。"""
    assert spec_of("発車").table_row == "発車/停車" == spec_of("停車").table_row
    assert spec_of("並ぶ").table_row == "並ぶ/撮影" == spec_of("撮影").table_row


def test_expedient_rows_are_tagged_as_in_the_contract():
    """契約書がタグ **expedient** と書いた行(通報・手伝い・並ぶ/撮影)。"""
    expedient = {w for w, s in ACTION_SPECS.items() if s.tag == "expedient"}
    assert expedient == {"通報", "手伝い", "並ぶ", "撮影"}


def test_vocabulary_limit_of_the_contract_is_respected():
    """§2「種別あたりの語彙上限24語」。"""
    assert len(ALL_ACTION_WORDS) == len(set(ALL_ACTION_WORDS)) <= VOCAB_LIMIT_PER_KIND


def test_codes_are_stable_and_disjoint():
    assert list(ACTION_CODES.values()) == list(range(12))
    assert set(ROLE_ACTION_CODES.values()) == set(range(12, 12 + len(ROLE_ACTION_WORDS)))
    assert action_code_of("移動") == 0 and action_code_of("就寝") == 11
    assert action_code_of("接客") == 12
    assert action_code_of("存在しない語") == -2


def test_output_form_constants_match_section_1():
    assert (REASON_MAX_CHARS, COMMENT_MAX_CHARS) == (40, 20)
    text = format_two_line("予定の時間になったから", "移動", "C-0117", "急ごう")
    assert text.splitlines()[0] == "理由: 予定の時間になったから"
    m = TWO_LINE_RE.match(text)
    assert m and m.group("action") == "移動" and m.group("target") == "C-0117"


# ---------------------------------------------------------------- 対象の解釈
@pytest.mark.parametrize(
    "text,kind",
    [
        ("なし", TargetKind.NONE),
        ("", TargetKind.NONE),
        ("C-0117", TargetKind.CELL),
        ("C117", TargetKind.CELL),
        ("g12_34_GL", TargetKind.CELL),
        ("g-10_-1_UG", TargetKind.CELL),
        ("g0_0_DECK", TargetKind.CELL),
        ("セルg-1_0_GL", TargetKind.CELL),  # 第271: B2 の文の写し
        ("セルID: g3_-7_GL", TargetKind.CELL),
        ("セルID_g3_-7_GL", TargetKind.CELL),
        ("セルC-0117", TargetKind.CELL),
        ("セルID_コンビニエンスストア", TargetKind.ITEM_CATEGORY),  # 残りがセル ID でなければ従来どおり
        ("セルの飲食店", TargetKind.ITEM_CATEGORY),
        ("P-204", TargetKind.PERSON),
        ("204", TargetKind.PERSON),
        ("渋谷駅", TargetKind.STATION_OR_VEHICLE),
        ("おにぎり", TargetKind.ITEM_CATEGORY),
    ],
)
def test_parse_target_recognises_the_declared_surface_forms(text, kind):
    assert parse_target(text).kind is kind


def test_parse_target_keeps_the_raw_string_and_extracts_ids():
    t = parse_target("「C-0117」")
    assert t.raw == "C-0117" and t.cell_index == 117
    w2 = parse_target("g12_34_UG")
    assert w2.cell_id == "g12_34_UG" and w2.band == "UG" and w2.cell_index is None
    p = parse_target("P204")
    assert p.person_id == 204
    assert parse_target(None).is_none and str(parse_target(None)) == NO_TARGET


def test_parse_target_never_raises_on_odd_input():
    for bad in ("", "   ", "　", "🙂", "-", "C-" + "9" * 50, "g1_2_XX"):
        parse_target(bad)  # 例外を投げないことだけを見る


def test_target_placeholder_words_are_read_as_no_target_but_keep_raw():
    """第223(D-89): 観測テンプレートの欄説明語を写した応答は対象なし(raw は診断用に残す)。"""
    from shibuya.llm.contract import TargetKind, parse_target, NO_TARGET
    for w in ("物のカテゴリ", "セルID", "人ID", "<セルID / 物のカテゴリ / 人ID / なし>"):
        tg = parse_target(w)
        assert tg.kind is TargetKind.NONE, w
    assert parse_target("物のカテゴリ").raw == "物のカテゴリ" and parse_target("なし").raw == NO_TARGET


def test_cell_prefix_is_stripped_only_when_the_rest_is_a_cell_id():
    """第271: 「セルg-1_0_GL」(B2「現在地はセルg-1_0_GL」の写し)をセルとして読む。

    テープ 28 本で 移動 10,751 呼・食事 921 呼が自由記述に落ちていた。``raw`` は逐語のまま、
    ``cell_id`` は接頭辞を剥がした形。説明語「セルID」は NONE のまま(第223 の読みを動かさない)。
    """
    from shibuya.llm.contract import TargetKind, parse_target
    tg = parse_target("セルg-1_0_GL")
    assert tg.kind is TargetKind.CELL and tg.raw == "セルg-1_0_GL" and tg.cell_id == "g-1_0_GL" and tg.band == "GL"
    tg = parse_target("セルID: g0_-3_DECK")
    assert tg.kind is TargetKind.CELL and tg.cell_id == "g0_-3_DECK" and tg.band == "DECK"
    tg = parse_target("セルC-0117")
    assert tg.kind is TargetKind.CELL and tg.cell_id == "C-0117" and tg.cell_index == 117
    assert parse_target("セルID").kind is TargetKind.NONE
    assert parse_target("セル").kind is TargetKind.ITEM_CATEGORY
    assert parse_target("g-1_0_GL").cell_id == "g-1_0_GL"  # 接頭辞なしは不変


def test_target_category_suffix_is_stripped_before_parsing():
    """「食品のカテゴリ」→ 物カテゴリ「食品」。実在名・セル・人 ID の読み方は不変。"""
    from shibuya.llm.contract import TargetKind, parse_target
    tg = parse_target("食品のカテゴリ")
    assert tg.kind is TargetKind.ITEM_CATEGORY and tg.category == "食品"
    assert parse_target("C-0117").kind is TargetKind.CELL
    assert parse_target("P-204").kind is TargetKind.PERSON
    assert parse_target("渋谷駅").kind is TargetKind.STATION_OR_VEHICLE
