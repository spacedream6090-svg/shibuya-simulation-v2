"""語彙 v2(横断語「食事」)の契約側 — D-71 §3 E/F/H(ユーザー決定 2026-09-17)。

見るもの
(i)  **v1 は 1 バイトも動かない**: ``ACTION_VOCAB_12``/``ALL_ACTION_WORDS``/``ACTION_CODES``/
     ``ACTION_SPECS`` は同一オブジェクトのまま・``action_words("v1") is ALL_ACTION_WORDS``/
(ii) v2 の語・コード・契約行(失敗コードは ``ResultCode`` に実在する)/
(iv) **段0 辞書 v3**: 食べる・飲む → 食事(v1 では 購入 のまま=辞書も版も動かない)/
(v)  **対応表**(F): ``compat_word("食事") == "購入"``= v1 の語彙で読むときの読み替え。
"""

from __future__ import annotations

import pytest

from shibuya.agents.state import ResultCode
from shibuya.llm.contract import (
    ACTION_CODES,
    ACTION_SPECS,
    ACTION_SPECS_V2,
    ACTION_VOCAB_12,
    ACTION_VOCAB_13,
    ACTION_WORD_EAT,
    ALL_ACTION_WORDS,
    ALL_ACTION_WORDS_V2,
    DEFAULT_VOCAB_VERSION,
    EAT_ACTION_CODE,
    VOCAB_COMPAT,
    VOCAB_LIMIT_PER_KIND,
    VOCAB_VERSIONS,
    action_code_of,
    action_words,
    check_vocab_version,
    compat_word,
    cross_action_words,
    engine_action_codes,
    spec_of,
)
from shibuya.llm.parser import find_action_word, parse_two_line
from shibuya.llm.undefined import (
    SYNONYM_TABLE_VERSION,
    SYNONYMS,
    SYNONYMS_V3,
    SYNONYMS_V3_DIFF,
    UndefinedActionRegistry,
    map_synonym,
    synonym_table,
    synonym_table_version,
)


# ------------------------------------------------------------------ (i) v1 のバイト不変
def test_v1_objects_are_untouched():
    """v1 の語彙・コード・契約表は**同一オブジェクト**(名前を足しただけ)。"""
    assert VOCAB_VERSIONS == ("v1", "v2") and DEFAULT_VOCAB_VERSION == "v1"
    assert action_words("v1") is ALL_ACTION_WORDS
    assert action_words() is ALL_ACTION_WORDS
    assert cross_action_words("v1") is ACTION_VOCAB_12
    assert engine_action_codes("v1") is ACTION_CODES
    assert len(ACTION_VOCAB_12) == 12 and len(ALL_ACTION_WORDS) == 24
    assert len(ACTION_SPECS) == 24 and ACTION_WORD_EAT not in ACTION_SPECS
    assert list(ACTION_CODES.values()) == list(range(12))


def test_eat_is_unknown_in_v1():
    """既定(v1)では「食事」は語彙外=未定義行動の経路へ行く。"""
    assert ACTION_WORD_EAT not in ALL_ACTION_WORDS
    assert action_code_of(ACTION_WORD_EAT) == -2
    assert spec_of(ACTION_WORD_EAT) is None
    assert find_action_word("食事する") is None


# ------------------------------------------------------------------ (ii) v2 の語とコード
def test_v2_appends_one_cross_cutting_word():
    assert ACTION_VOCAB_13 == ACTION_VOCAB_12 + (ACTION_WORD_EAT,)
    assert ALL_ACTION_WORDS_V2 == ALL_ACTION_WORDS + (ACTION_WORD_EAT,)
    assert action_words("v2") == ALL_ACTION_WORDS_V2
    assert len(set(ALL_ACTION_WORDS_V2)) == 25


def test_the_eat_code_is_appended_not_inserted():
    """既存コード(12 語 0..11・役割語 12..23)は 1 つも動かず、食事は**末尾の 24**。"""
    assert EAT_ACTION_CODE == 24 == len(ALL_ACTION_WORDS)
    assert action_code_of(ACTION_WORD_EAT, "v2") == 24
    assert action_code_of("移動", "v2") == 0 and action_code_of("就寝", "v2") == 11
    assert action_code_of("接客", "v2") == 12
    assert engine_action_codes("v2")[ACTION_WORD_EAT] == 24
    assert "接客" not in engine_action_codes("v2"), "役割語は effects 先が C4=分岐が無い"


def test_v2_vocabulary_exceeds_the_declared_limit_by_one():
    """§2「種別あたり 24 語」を **1 語超える**ことを機械で可視化する(封印は D-71 §3 J 待ち)。

    v1 側の上限は守られたまま。v2 は 25 語=**超過を隠さず宣言する**ための行。
    """
    assert len(ALL_ACTION_WORDS) <= VOCAB_LIMIT_PER_KIND
    assert len(ALL_ACTION_WORDS_V2) == VOCAB_LIMIT_PER_KIND + 1


def test_the_eat_contract_row_is_declared():
    spec = spec_of(ACTION_WORD_EAT, "v2")
    assert spec is not None and spec.word == ACTION_WORD_EAT
    assert spec.tag in ("mechanism", "expedient")
    assert spec.precondition_text and spec.effects and spec.failure_text
    for name in spec.failure_codes:
        assert hasattr(ResultCode, name), f"ResultCode.{name} が無い"
    assert set(spec.failure_codes) == {"NOT_IN_EATERY", "MONEY_SHORT", "CLOSED"}
    assert ACTION_SPECS_V2[ACTION_WORD_EAT] is spec
    assert len(ACTION_SPECS_V2) == 25


def test_unknown_vocab_version_is_refused():
    for bad in ("v3", "", "V1", None):
        with pytest.raises(ValueError):
            check_vocab_version(bad)


# ------------------------------------------------------------------ (iv) 段0 辞書 v3
def test_v1_dictionary_and_its_version_do_not_move():
    assert synonym_table("v1") is SYNONYMS
    assert synonym_table_version("v1") == SYNONYM_TABLE_VERSION == "undefined-synonyms-v2"
    assert SYNONYMS["食べる"] == "購入" and SYNONYMS["飲む"] == "購入"
    assert map_synonym("食べる")[0] == "購入"


@pytest.mark.parametrize("surface", ["食べる", "飲む", "飲食", "食事する", "食事を"])
def test_dictionary_v3_maps_the_eating_family_to_the_new_word(surface):
    assert map_synonym(surface, None, "v2")[0] == ACTION_WORD_EAT
    assert SYNONYMS_V3[surface] == ACTION_WORD_EAT


def test_dictionary_v3_is_only_a_diff_on_top_of_v1():
    """v3 = v1 の表 + 差分。**差分以外の行は 1 つも変わらない**。

    語彙 v2 が引く版は **C9b(2026-09-17・G5 対象ヒント)で v4 へ上がった**
    (``undefined-synonyms-v4`` = v3 + ``SYNONYMS_V4_DIFF``)。v3 の中身そのものは不変。
    """
    assert synonym_table_version("v2") == "undefined-synonyms-v4"
    changed = {k for k in SYNONYMS if SYNONYMS[k] != SYNONYMS_V3[k]}
    assert changed == {"食べる", "飲む"}, "v1 から写像先が動く行は★の 2 行だけ"
    assert set(SYNONYMS_V3) - set(SYNONYMS) == set(SYNONYMS_V3_DIFF) - set(SYNONYMS)
    assert set(SYNONYMS_V3_DIFF.values()) == {ACTION_WORD_EAT}


def test_the_registry_resolves_the_eating_family_in_v2():
    reg = UndefinedActionRegistry(vocab_version="v2")
    out = reg.observe("食べる", agent_id=1, tick=0)
    assert out.stage == 0 and out.word == ACTION_WORD_EAT and out.action_code == 24
    v1 = UndefinedActionRegistry()
    assert v1.observe("食べる", agent_id=1, tick=0).word == "購入"


def test_stage0_still_works_for_the_untouched_rows_in_v2():
    for surface, word in (("探索", "移動"), ("買う", "購入"), ("寝る", "就寝"), ("観察", "待機")):
        assert map_synonym(surface, None, "v2")[0] == word


# ------------------------------------------------------------------ (v) 旧版への対応表
def test_compat_table_reads_the_new_word_as_the_old_one():
    assert VOCAB_COMPAT == {"v2": {ACTION_WORD_EAT: "購入"}}
    assert compat_word(ACTION_WORD_EAT) == "購入"
    assert compat_word(ACTION_WORD_EAT, "v2", "v1") == "購入"
    assert compat_word(ACTION_WORD_EAT, "v2", "v2") == ACTION_WORD_EAT
    for word in ALL_ACTION_WORDS:  # v1 の語は 1 つも読み替わらない
        assert compat_word(word) == word


def test_compat_targets_are_words_of_the_old_vocabulary():
    """読み替え先は**必ず旧版に実在する語**(比較のための橋が壊れていないこと)。"""
    for new, old in VOCAB_COMPAT["v2"].items():
        assert new in ALL_ACTION_WORDS_V2 and old in ALL_ACTION_WORDS


# ------------------------------------------------------------------ パーサの版切替
def test_parser_reads_the_new_word_only_in_v2():
    text = "理由: 腹が減った\n行動: 食事 対象: 定食屋0007 ひと言: なし"
    v1 = parse_two_line(text)
    assert v1.action is None and not v1.format_ok
    v2 = parse_two_line(text, "v2")
    assert v2.action == ACTION_WORD_EAT and v2.action_code == 24 and v2.format_ok
    assert not v2.is_role_action


def test_parser_v1_results_are_unchanged_for_every_v1_word():
    for word in ALL_ACTION_WORDS:
        text = f"理由: 理由の文\n行動: {word} 対象: なし ひと言: なし"
        a = parse_two_line(text)
        b = parse_two_line(text, "v2")
        assert (a.action, a.action_code, a.format_ok) == (b.action, b.action_code, b.format_ok)
