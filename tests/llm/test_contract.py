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


# ================================================================ 語彙 v3(第274・D-116 行為と活動の二層)
# 正典: docs/design/v2-two-layer-implementation-agenda.md §1-1〜§1-3。
import inspect  # noqa: E402

from shibuya.agents.state import ResultCode  # noqa: E402
from shibuya.llm import contract as C  # noqa: E402

#: アジェンダ §1-1 の表(テスト側に独立に書き写す=片方だけ直せば落ちる)。
V3_CROSS = ("移動", "乗車", "購入", "食事", "会話", "退去", "通報", "手伝い", "断る", "就寝", "並ぶ", "なし")
V3_ROLE = ("接客", "補充", "開閉店", "価格改定", "発車", "停車", "放送", "遅延報告", "計画改訂", "指示", "撮影")
V3_REMOVED = ("待機", "休憩", "降車")
#: アジェンダ §1-1「行動コードは動かさない」(欠番 2・4・10)。
V3_CODES = {
    "移動": 0, "乗車": 1, "購入": 3, "会話": 5, "退去": 6, "通報": 7, "手伝い": 8, "断る": 9,
    "就寝": 11, "並ぶ": 22, "食事": 24, "なし": 25,
}


def test_v3_word_sets_follow_the_agenda_table():
    assert C.ACTION_VOCAB_V3 == V3_CROSS == C.cross_action_words("v3")
    assert C.ROLE_ACTION_WORDS_V3 == V3_ROLE == C.role_action_words("v3")
    assert C.action_words("v3") == V3_CROSS + V3_ROLE == C.ALL_ACTION_WORDS_V3
    assert C.REMOVED_ACTION_WORDS_V3 == V3_REMOVED
    assert not set(V3_REMOVED) & set(C.action_words("v3"))
    assert C.role_action_words("v1") is C.ROLE_ACTION_WORDS  # v1/v2 は同一オブジェクト
    assert C.role_action_words("v2") is C.ROLE_ACTION_WORDS
    assert C.DEFAULT_VOCAB_VERSION == "v1", "ライブラリの既定は v1 のまま"


def test_v3_codes_do_not_move_and_removed_words_are_vacant():
    """既存コードは 1 つも動かない・2/4/10 は欠番・なし は末尾の 25。"""
    assert C.NONE_ACTION_CODE == 25 and C.ACTION_WORD_NONE == "なし"
    for word, code in V3_CODES.items():
        assert C.action_code_of(word, "v3") == code, word
        if word not in ("食事", "なし"):
            assert C.action_code_of(word) == code, "v1 と同じ値"
    for word in V3_ROLE:
        assert C.action_code_of(word, "v3") == C.action_code_of(word) == C.ROLE_ACTION_CODES[word]
    for word in V3_REMOVED:
        assert C.action_code_of(word, "v3") == C.UNDEFINED_ACTION
        assert C.spec_of(word, "v3") is None
    used = {C.action_code_of(w, "v3") for w in C.action_words("v3")}
    assert used.isdisjoint({2, 4, 10}), "欠番のコードを誰も使わない"
    assert C.action_code_of("なし") == C.UNDEFINED_ACTION, "v1 では なし は語彙外(既定不変)"


def test_v3_engine_codes_are_the_cross_cutting_words():
    codes = C.engine_action_codes("v3")
    assert dict(codes) == V3_CODES
    assert "接客" not in codes, "役割語は効果先が C4=分岐が無い"
    assert C.engine_action_codes("v1") is C.ACTION_CODES


def test_v3_queue_is_cross_cutting_and_not_a_role_word():
    assert C.is_role_action("並ぶ") and not C.is_role_action("並ぶ", "v3")
    assert C.is_role_action("撮影", "v3") and C.is_role_action("接客", "v3")
    spec = C.spec_of("並ぶ", "v3")
    assert spec is not None and not spec.is_role and spec.permission_holder == ""
    assert spec.preconditions == C.spec_of("並ぶ").preconditions, "前提・効果の文面は v1 の行のまま"
    assert C.spec_of("並ぶ").is_role, "v1 の行は動かない"


def test_v3_none_is_the_never_failing_safety_valve():
    spec = C.spec_of("なし", "v3")
    assert spec is not None and spec.never_fails and spec.failure_codes == ()
    assert spec.target_kind is TargetKind.NONE and "失敗しない" in spec.failure_text
    assert C.safe_action_word("v3") == "なし"
    assert C.safe_action_word() == C.safe_action_word("v2") == "待機"
    assert C.safe_action_word("v3") in C.engine_action_codes("v3")


def test_v3_every_word_passes_the_gate_instead_of_a_count_limit():
    """D-92 (a): v3 の門は「契約行+コード」。上限 24 の assert は v3 に掛けない(v1 は残す)。"""
    for word in C.action_words("v3"):
        spec = C.spec_of(word, "v3")
        assert spec is not None and spec.word == word
        assert C.action_code_of(word, "v3") >= 0
        for name in spec.failure_codes:
            assert hasattr(ResultCode, name), name
    src = inspect.getsource(C)
    assert "ALL_ACTION_WORDS_V3) <= VOCAB_LIMIT_PER_KIND" not in src
    assert "assert len(ALL_ACTION_WORDS) <= VOCAB_LIMIT_PER_KIND" in src, "v1 の assert は残る"


def test_v3_compat_reads_both_directions():
    """VOCAB_COMPAT["v3"]: 待機/休憩 → なし(旧テープを v3 で読む)/ なし → 待機(v3 → 旧版)。"""
    assert C.VOCAB_COMPAT["v3"] == {"待機": "なし", "休憩": "なし", "降車": "なし", "なし": "待機"}
    assert C.compat_word("待機", "v1", "v3") == "なし"
    assert C.compat_word("休憩", "v2", "v3") == "なし"
    assert C.compat_word("なし", "v3", "v1") == "待機"
    assert C.compat_word("なし", "v3", "v2") == "待機"
    assert C.compat_word("降車", "v1", "v3") == "なし", "第275 #7: 欠番の語は安全弁へ"
    assert C.compat_word("食事", "v3", "v1") == "購入", "v2 の橋を通る"
    assert C.compat_word("食事", "v3", "v2") == "食事"
    for word in C.action_words("v3"):  # v3 の語は必ず v1 の語彙で読める
        assert C.compat_word(word, "v3", "v1") in C.ALL_ACTION_WORDS, word
    for word in C.ALL_ACTION_WORDS:  # 第275 #7 以後、v1 の語は全て v3 の語彙で読める
        assert C.compat_word(word, "v1", "v3") in C.action_words("v3"), word
    # 既定(v2 → v1)の読み替えは従来どおり
    assert C.compat_word("食事") == "購入" and C.compat_word("待機") == "待機"


def test_v3_target_wander_and_base_words():
    t = C.parse_target("あたり", vocab_version="v3")
    assert t.kind is TargetKind.ITEM_CATEGORY and t.category == "あたり" and t.wander
    v1 = C.parse_target("あたり")
    assert v1.kind is TargetKind.ITEM_CATEGORY and not v1.wander, "v1/v2 は現行のまま"
    assert not C.parse_target("あたり", vocab_version="v2").wander
    landmarks = {"渋谷区立神南小学校": 5}
    assert C.parse_target("学校", landmarks).poi_id == 5, "v1 は目印に解決する(現行)"
    s = C.parse_target("学校", landmarks, "v3")
    assert s.kind is TargetKind.ITEM_CATEGORY and s.category == "学校" and s.poi_id is None
    for w in ("自宅", "職場"):
        assert C.parse_target(w, vocab_version="v3").category == w


def test_v3_placeholders_are_read_as_no_target_only_in_v3():
    for w in ("名前かID", "店の種類", "店名", "駅名", "人のID", "<名前かID / 自宅 / 職場 / 学校 / あたり / なし>"):
        assert C.parse_target(w, vocab_version="v3").kind is TargetKind.NONE, w
    assert C.parse_target("店の種類").kind is TargetKind.ITEM_CATEGORY, "v1 は現行のまま"
    assert C.parse_target("物のカテゴリ", vocab_version="v3").kind is TargetKind.NONE


@pytest.mark.parametrize(
    "text,kind,value",
    [
        ("到着", C.UntilKind.ARRIVAL, 0),
        ("目的地に到着するまで", C.UntilKind.ARRIVAL, 0),
        ("相手", C.UntilKind.PARTNER, 0),
        ("30分", C.UntilKind.MINUTES, 30),
        ("30 分", C.UntilKind.MINUTES, 30),
        ("約15分間", C.UntilKind.MINUTES, 15),
        ("３０分", C.UntilKind.MINUTES, 30),
        ("600分", C.UntilKind.MINUTES, 480),
        ("99999999999分", C.UntilKind.MINUTES, 480),
        ("0分", C.UntilKind.MINUTES, 0),
        ("12:30", C.UntilKind.CLOCK, 750),
        ("１２：０５", C.UntilKind.CLOCK, 725),
        ("0:00", C.UntilKind.CLOCK, 0),
        ("23:59", C.UntilKind.CLOCK, 1439),
        ("次の予定", C.UntilKind.NEXT_SCHEDULE, 0),
        ("", C.UntilKind.DEFAULT, 60),
        ("なし", C.UntilKind.DEFAULT, 60),
        ("しばらく", C.UntilKind.DEFAULT, 60),
        ("N分", C.UntilKind.DEFAULT, 60),
        ("HH:MM", C.UntilKind.DEFAULT, 60),
        ("24:00", C.UntilKind.DEFAULT, 60),
        ("1時間30分", C.UntilKind.MINUTES, 90),  # 第275 #6
        ("1時間", C.UntilKind.MINUTES, 60),
        ("2 時間", C.UntilKind.MINUTES, 120),
        ("10時間", C.UntilKind.MINUTES, 480),
        ("１時間１５分", C.UntilKind.MINUTES, 75),
        ("12時30分", C.UntilKind.DEFAULT, 60),  # 時刻の漢字表記は 分 として読まない
    ],
)
def test_parse_until_reads_the_six_forms_and_the_default(text, kind, value):
    u = C.parse_until(text)
    assert (u.kind, u.value) == (kind, value)


def test_parse_until_constants_and_none():
    assert (C.UNTIL_DEFAULT_MINUTES, C.UNTIL_MAX_MINUTES, C.ACTIVITY_MAX_CHARS) == (60, 480, 10)
    assert C.parse_until(None) == C.DEFAULT_UNTIL == C.Until(C.UntilKind.DEFAULT, 60)
    for odd in ("🙂", "分", ":", "99:99", "-5分", "9" * 5000 + "分"):
        C.parse_until(odd)  # 例外を投げない


def test_v3_two_line_form_round_trips():
    text = C.format_two_line_v3("腹が減った", "食事", "カフェ", "昼を食べる", "30分")
    assert text == "理由: 腹が減った\n行動: 食事 対象: カフェ 活動: 昼を食べる まで: 30分"
    m = C.TWO_LINE_RE_V3.match(text)
    assert m and m.group("activity") == "昼を食べる" and m.group("until") == "30分"
    assert not C.TWO_LINE_RE.match(text), "v1 の厳密形とは別"
