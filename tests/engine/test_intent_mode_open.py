"""AB7 自由意図の腕の切替口 — エンジン側(``docs/design/v2-open-intent-arm-spec.md`` §4 (c))。

見るもの
(c) **段0 辞書写像(行動契約書 §7)は既定でも open/hint 腕でも同じに効く**
    (「探索」→「移動」・「買う」→「購入」…)。プロンプトの差は接地の経路を変えない/
    ``intent_mode`` が ``run_day`` → レンダラ → run manifest まで往復する(3 腕とも)/
    既定(vocab)の checkpoint・呼数は open/hint 腕と**同じ**(MockLLM は本文を読まない)。

台本 mock の書き方は ``tests/engine/test_undefined_action.py`` から流用(同じ ``WordLLM``)。
"""

from __future__ import annotations

import pytest

from shibuya.engine.run import run_day
from shibuya.llm import LLMResponse, format_two_line
from shibuya.llm.contract import ACTION_CODES, action_code_of
from shibuya.llm.undefined import map_synonym
from shibuya.perception.templates import INTENT_MODES


class WordLLM:
    """常に同じ行動語(表層形)を返す台本 mock(``test_undefined_action.WordLLM`` と同じ)。"""

    def __init__(self, word: str) -> None:
        self.word = word
        self.n_calls = 0

    def complete(self, request):
        self.n_calls += 1
        return LLMResponse(
            text=format_two_line("台本の理由", self.word, "なし", "なし"), source="scripted"
        )


#: ``test_undefined_action.SMALL`` と同じ窓(D-56 の最初の計画境界を跨ぐ)。
SMALL = dict(n_agents=300, seed=4, ticks=540, checkpoint_every=540, n_cells=16)


# ------------------------------------------------------------------ (c) 段0 は両腕で効く
@pytest.mark.parametrize("intent_mode", INTENT_MODES)
@pytest.mark.parametrize("surface,word", [("探索", "移動"), ("買う", "購入"), ("寝る", "就寝")])
def test_stage0_dictionary_works_in_both_intent_modes(intent_mode, surface, word):
    """語彙を見せない腕でも、語彙外の表層は段0 辞書でエンジンの行動コードになる。"""
    res = run_day(llm=WordLLM(surface), intent_mode=intent_mode, **SMALL)
    assert res.intent_mode == intent_mode
    assert res.undefined_action_count == 0, "段0 で救えているので未定義行動は増えない"
    assert res.bridge_counters["undefined_mapped"] == res.llm_calls > 0
    assert res.bridge_counters["undefined_records"] == 0
    assert res.undefined_registry.counters()["dictionary_mapped"] == res.llm_calls
    # 写像先は腕に依らない(段0 は純関数)=エンジンの行動コードも同じ
    assert map_synonym(surface)[0] == word
    assert action_code_of(word) == ACTION_CODES[word]
    assert res.conserved and res.min_stock >= 0


@pytest.mark.parametrize("intent_mode", INTENT_MODES)
def test_stage1_records_the_word_in_both_intent_modes(intent_mode):
    """段0 で写せない語は、どちらの腕でも段1(記録+待機)に落ちる。"""
    res = run_day(llm=WordLLM("空を飛ぶ"), intent_mode=intent_mode, **SMALL)
    reg = res.undefined_registry
    assert reg.counts["空を飛ぶ"] == res.llm_calls > 0
    assert reg.counters()["undefined_records"] == res.llm_calls
    assert reg.distinct_agents("空を飛ぶ") > 1
    assert reg.top_words(3)[0][0] == "空を飛ぶ"
    assert res.undefined_action_count > 0
    assert res.conserved, "未定義行動が出ても保存則は破れない"


# ------------------------------------------------------------------ 往復と既定のバイト不変
def test_intent_mode_round_trips_into_the_run_manifest():
    for mode in INTENT_MODES:
        res = run_day(intent_mode=mode, **SMALL)
        assert res.intent_mode == mode
        assert res.run_manifest_fields()["intent_mode"] == mode


def test_default_is_vocab_and_the_mock_actions_do_not_move():
    """既定は vocab。mock は本文を読まないので open/hint 腕でも checkpoint・呼数は同じ。"""
    base = run_day(**SMALL)
    vocab = run_day(intent_mode="vocab", **SMALL)
    open_ = run_day(intent_mode="open", **SMALL)
    hint = run_day(intent_mode="hint", **SMALL)
    assert base.intent_mode == "vocab"
    assert base.llm_calls > 0
    assert base.final_hash == vocab.final_hash == open_.final_hash == hint.final_hash
    assert base.llm_calls == vocab.llm_calls == open_.llm_calls == hint.llm_calls


def test_unknown_intent_mode_is_refused():
    with pytest.raises(ValueError):
        run_day(intent_mode="free", **SMALL)


# ------------------------------------------------------------------ D-113 ④ 役割語の提示(第269)
def test_role_words_default_on_and_round_trips_into_the_run_manifest():
    """ランの既定は役割語あり(契約書 §2.2)。off は第268 以前の B0(prompt_hash が違う)。"""
    from shibuya.perception import templates as T

    on = run_day(**SMALL)
    off = run_day(role_words=False, **SMALL)
    assert on.role_words is True and off.role_words is False
    assert on.run_manifest_fields()["role_words"] is True
    assert off.run_manifest_fields()["role_words"] is False
    assert on.conserved and off.conserved
    # checkpoint(mock は B0 を読まない)は同じ・B0 の指紋だけ違う
    assert on.final_hash == off.final_hash
    assert T.b0_sha256("vocab", "v1", True) != T.b0_sha256("vocab", "v1", False)
