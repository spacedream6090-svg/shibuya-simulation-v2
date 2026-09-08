"""行動契約表とエンジンの**突合**(層をまたぐ検査)。

- ``llm.contract.ActionSpec.failure_codes`` の名前が ``agents.state.ResultCode`` に実在する。
- ``llm.contract.ACTION_CODES`` と ``engine.commit.ACTION_CODES`` が**同一**(二重定義がない)。
- ``engine.commit.parse_action`` が正典パーサ(``llm.parser``)へ委譲している。
- 契約表の12語が ``engine.resolve`` の適用分岐と1対1。

正典: 行動契約書 §2.1/§2.2・§2「共通の必須事項①効果は resolve でのみ適用/③失敗しない行動が
常に1つ以上(待機)」・知覚契約書 §2.5。
"""

from __future__ import annotations

import pytest

from shibuya.agents.state import ResultCode
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.llm.contract import (
    ACTION_CODES,
    ACTION_SPECS,
    ACTION_VOCAB_12,
    ROLE_ACTION_WORDS,
    UNDEFINED_ACTION,
    format_two_line,
)
from shibuya.llm.parser import parse_two_line


@pytest.mark.parametrize("word", sorted(ACTION_SPECS))
def test_failure_codes_exist_in_result_code(word):
    """契約表の失敗コード名は ``ResultCode`` に**実在**する(層をまたぐ文字列参照の検査)。"""
    for name in ACTION_SPECS[word].failure_codes:
        assert hasattr(ResultCode, name), f"{word}: ResultCode.{name} が無い"


def test_result_code_covers_the_never_fails_rule():
    """§2 共通必須事項③「失敗しない行動が常に1つ以上(待機)」。"""
    never = [w for w, s in ACTION_SPECS.items() if s.never_fails]
    assert "待機" in never


def test_engine_action_codes_come_from_the_contract():
    assert C.ACTION_CODES == dict(ACTION_CODES)
    assert C.ACTION_WORDS == ACTION_VOCAB_12
    assert C.UNDEFINED_ACTION == UNDEFINED_ACTION == -2


def test_resolve_has_one_branch_per_contract_word():
    """12 語 + エンジン継続 = 13 分岐(``engine.resolve._APPLY``)。"""
    codes = {c for c in R._APPLY if c >= 0}
    assert codes == set(ACTION_CODES.values())
    assert len(R._APPLY) == 13


@pytest.mark.parametrize("word", list(ACTION_VOCAB_12))
def test_parse_action_round_trips_every_contract_word(word):
    text = format_two_line("理由の文", word, "なし", "なし")
    assert C.parse_action(text) == ACTION_CODES[word]


@pytest.mark.parametrize("word", list(ROLE_ACTION_WORDS))
def test_role_words_are_parsed_but_are_not_engine_intents_yet(word):
    """役割語はパーサが読む(全員に見せる)が、``_APPLY`` に分岐が無いので未定義扱いに落とす。"""
    text = format_two_line("理由の文", word, "なし", "なし")
    assert parse_two_line(text).action == word
    assert C.parse_action(text) == UNDEFINED_ACTION


def test_parse_action_delegates_to_the_canonical_parser():
    """C2 の最小写像では読めなかった形(行内分割・箇条書き)も読める=委譲の証拠。"""
    packed = "理由: 用事 行動: 移動 対象: C-1 ひと言: なし"
    assert C.parse_action(packed) == ACTION_CODES["移動"]
    bulleted = "- 理由: 眠い\n- 行動: 就寝 対象: C-2 ひと言: なし"
    assert C.parse_action(bulleted) == ACTION_CODES["就寝"]


def test_parse_action_returns_undefined_for_non_contract_output():
    assert C.parse_action("これは2行形ではない") == UNDEFINED_ACTION
    assert C.parse_action("") == UNDEFINED_ACTION
    assert C.parse_action("理由: あ\n行動: 買う 対象: パン ひと言: なし") == UNDEFINED_ACTION


def test_contract_tags_are_declared_for_every_row():
    for word, spec in ACTION_SPECS.items():
        assert spec.tag in ("mechanism", "expedient"), word
        assert spec.section in ("2.1", "2.2"), word
