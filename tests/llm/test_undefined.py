"""llm.undefined のテスト(行動契約書 §7「未定義行動の受理」5段)。

段0 辞書写像(ゼロ呼)/段1 レコード+失敗フィードバック+計数/段2 閾値Nで裁定LLM 1呼/
段3 保存則・性能予算に触れる行は NEEDS_PARENT_REVIEW(自動採用しない)/段4 採用=判例化。
"""

from __future__ import annotations

import pytest

from shibuya.llm import LLMRequest, LLMResponse, MockLLM
from shibuya.llm.contract import ACTION_CODES, TargetKind, ActionSpec
from shibuya.llm.undefined import (
    ADJUDICATION_TEMPLATE,
    DEFAULT_THRESHOLD_AGENTS,
    SYNONYM_TABLE_VERSION,
    SYNONYMS,
    SYNONYMS_C6,
    Proposal,
    ProposalStatus,
    UndefinedActionRegistry,
    map_synonym,
    undefined_feedback,
)


class ScriptedLLM:
    """裁定LLMの差し替え(``LLMClient`` 契約・呼数を数える)。"""

    def __init__(self, text: str) -> None:
        self.text = text
        self.requests: list[LLMRequest] = []

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(text=self.text, source="scripted")


CLEAN_ROW = (
    "前提: 同一セルに階段がある\n効果: 位置=上階のセルへ\nコスト: 時間\n"
    "失敗: 階段がない\n台帳照合: 縦動線の利用率\n"
)
CONSERVATION_ROW = (
    "前提: 所持金≧価格\n効果: 在庫−1・所持金−価格(保存則の対象)\nコスト: 価格\n"
    "失敗: 所持金不足\n台帳照合: 小売の売上\n"
)


# ---------------------------------------------------------------- 段0
def test_stage0_dictionary_maps_without_any_llm_call():
    llm = ScriptedLLM(CLEAN_ROW)
    reg = UndefinedActionRegistry(adjudicator=llm)
    for surface, canonical in [
        ("歩く", "移動"), ("買う", "購入"), ("話す", "会話"), ("待つ", "待機"),
        ("休む", "休憩"), ("寝る", "就寝"), ("座る", "休憩"), ("立ち去る", "退去"),
    ]:
        out = reg.observe(surface, agent_id=1, tick=0)
        assert out.stage == 0 and out.word == canonical and out.source == "dictionary"
        assert out.action_code == ACTION_CODES[canonical]
    assert llm.requests == [], "段0 は**ゼロ呼**"
    assert reg.counters()["undefined_records"] == 0


def test_stage0_target_is_the_engines_job_for_帰る():
    """「帰る」は移動へ写すが、対象(=自宅セル)は**エンジンが決める**=ヒントだけ返す。"""
    reg = UndefinedActionRegistry()
    out = reg.observe("帰る", agent_id=1, tick=0)
    assert out.word == "移動" and out.target_hint == "home"


def test_stage0_partial_match_prefers_the_longest_surface():
    assert map_synonym("急いで歩いていく")[0] == "移動"
    assert map_synonym("店員に話しかける")[0] == "会話"
    assert map_synonym("まったく知らない語")[0] is None


def test_synonym_table_is_versioned():
    assert SYNONYM_TABLE_VERSION.startswith("undefined-synonyms-")
    assert SYNONYM_TABLE_VERSION == "undefined-synonyms-v2", "表を変えたら版を上げる"


# ---------------------------------------------------------------- 段0(C6 追加・2026-09-09)
@pytest.mark.parametrize(
    "surface,canonical",
    [
        # 初回実LLMスモークで出た語彙外の行動語(未定義行動 43 件の中身)
        ("探索", "移動"), ("探す", "移動"), ("観察", "待機"), ("調査", "待機"), ("調べる", "待機"),
        # 同じ方針の近縁語
        ("見回る", "移動"), ("歩き回る", "移動"), ("散策", "移動"),
        ("確認", "待機"), ("眺める", "待機"), ("チェック", "待機"),
        # 活用形は部分一致で拾う
        ("飲食店を探す", "移動"), ("探して", "移動"), ("周囲を観察する", "待機"),
        ("調べて", "待機"), ("状況を確認する", "待機"),
    ],
)
def test_c6_stage0_maps_the_search_and_look_words_without_any_llm_call(surface, canonical):
    llm = ScriptedLLM(CLEAN_ROW)
    reg = UndefinedActionRegistry(adjudicator=llm)
    out = reg.observe(surface, agent_id=1, tick=0)
    assert out.stage == 0 and out.word == canonical and out.source == "dictionary"
    assert out.action_code == ACTION_CODES[canonical]
    assert out.action_from_dictionary and out.mapped
    assert out.target_hint == "", "対象の決定はエンジンの仕事(探索にヒントは付けない)"
    assert llm.requests == [] and reg.counters()["undefined_records"] == 0
    assert reg.counters()["dictionary_mapped"] == 1


def test_c6_stage0_policy_locomotion_vs_stationary():
    """方針: 移動を伴う探索→移動 / その場の観察・確認→待機(既存「様子を見る→待機」に接続)。"""
    assert map_synonym("様子を見る")[0] == "待機"  # v0 の方針アンカー
    assert {SYNONYMS_C6[w] for w in ("探す", "探索", "見回る")} == {"移動"}
    assert {SYNONYMS_C6[w] for w in ("観察", "確認", "調べる", "調査")} == {"待機"}
    assert set(SYNONYMS_C6.values()) <= {"移動", "待機"}
    assert SYNONYMS == {**SYNONYMS, **SYNONYMS_C6}


def test_c6_additions_do_not_shadow_the_existing_table():
    """既存の写像は C6 追加後も変わらない(部分一致の最長優先が壊れていない)。"""
    for surface, canonical in [
        ("歩く", "移動"), ("買う", "購入"), ("話す", "会話"), ("待つ", "待機"),
        ("休む", "休憩"), ("寝る", "就寝"), ("様子を見る", "待機"), ("立ち去る", "退去"),
        ("写真を撮る", "撮影"), ("帰る", "移動"),
    ]:
        assert map_synonym(surface)[0] == canonical, surface
    assert map_synonym("帰る")[1] == "home"


@pytest.mark.parametrize(
    "surface",
    ["通勤", "通学", "出勤", "退勤", "出社", "登校", "進入", "電車で通勤する", "出勤して"],
)
def test_c6_stage0_maps_the_commute_words_to_移動(surface):
    """``--fleet-debug-dir`` 実測の ``unknown_action_word`` 96 の第2群(通勤 16)。"""
    reg = UndefinedActionRegistry()
    out = reg.observe(surface, agent_id=1, tick=0)
    assert out.stage == 0 and out.word == "移動" and out.action_from_dictionary
    assert out.target_hint == "", "職場セルの印は未定義(対象の決定はエンジン・親判断待ち)"


def test_c6_vocabulary_words_are_not_in_the_dictionary():
    """``通報``/``退去``/``購入`` は §2.1 の12語=語彙一致で通るので辞書に入れない。"""
    for word in ("通報", "退去", "購入", "移動", "会話"):
        assert word in ACTION_CODES
        assert word not in SYNONYMS_C6
    assert not (set(SYNONYMS) & set(ACTION_CODES)), "辞書のキーが語彙語と衝突していない"


def test_c6_words_outside_both_the_vocabulary_and_the_dictionary_reach_stage1():
    reg = UndefinedActionRegistry()
    out = reg.observe("瞑想", agent_id=3, tick=1)
    assert out.stage == 1 and out.word is None and not out.action_from_dictionary
    assert out.feedback == undefined_feedback("瞑想")
    assert reg.counters()["dictionary_mapped"] == 0 and reg.counters()["undefined_records"] == 1


def test_c6_precedent_is_not_reported_as_a_dictionary_mapping():
    """段4(判例)は ``source="precedent"``=辞書写像とは別に数える。"""
    reg = UndefinedActionRegistry()
    reg.observe("跳ぶ", agent_id=0, tick=1)
    reg.adopt("跳ぶ", _spec("移動"))
    out = reg.observe("跳ぶ", agent_id=1, tick=2)
    assert out.stage == 4 and out.mapped and not out.action_from_dictionary


# ---------------------------------------------------------------- 段1
def test_stage1_records_counts_and_returns_the_failure_feedback():
    reg = UndefinedActionRegistry()
    out = reg.observe("ジャンプ", agent_id=7, tick=42, context_hash="abc")
    assert out.stage == 1 and out.word is None
    assert out.feedback == "未定義の行動『ジャンプ』。いま可能な行動: 待機/休憩/移動"
    assert out.feedback == undefined_feedback("ジャンプ")
    rec = reg.log[-1]
    assert (rec.raw_word, rec.agent_id, rec.tick, rec.context_hash) == ("ジャンプ", 7, 42, "abc")
    assert reg.counts["ジャンプ"] == 1 and reg.distinct_agents("ジャンプ") == 1


def test_stage1_log_is_bounded():
    reg = UndefinedActionRegistry(log_limit=8)
    for i in range(30):
        reg.observe(f"未知{i}", agent_id=i, tick=i)
    assert len(reg.log) == 8 and reg.n_dropped_records == 22
    assert reg.counters()["undefined_records"] == 30


# ---------------------------------------------------------------- 段2
def test_stage2_fires_once_at_the_threshold_of_n_distinct_agents():
    llm = ScriptedLLM(CLEAN_ROW)
    reg = UndefinedActionRegistry(adjudicator=llm, threshold_agents=DEFAULT_THRESHOLD_AGENTS)
    for agent in range(DEFAULT_THRESHOLD_AGENTS - 1):
        out = reg.observe("ジャンプ", agent_id=agent, tick=agent)
        assert out.stage == 1 and out.proposal is None
    assert llm.requests == []
    out = reg.observe("ジャンプ", agent_id=DEFAULT_THRESHOLD_AGENTS - 1, tick=99)
    assert out.stage == 2 and out.proposal is not None
    assert len(llm.requests) == 1, "契約書「1呼で契約行」"
    assert out.proposal.status is ProposalStatus.PROPOSED
    assert out.proposal.n_agents == DEFAULT_THRESHOLD_AGENTS
    # 同じ語で何度観測してもそれ以上呼ばない
    reg.observe("ジャンプ", agent_id=999, tick=100)
    assert len(llm.requests) == 1


def test_stage2_repeats_from_the_same_agent_do_not_reach_the_threshold():
    llm = ScriptedLLM(CLEAN_ROW)
    reg = UndefinedActionRegistry(adjudicator=llm, threshold_agents=3)
    for tick in range(20):
        reg.observe("ジャンプ", agent_id=1, tick=tick)
    assert llm.requests == [] and reg.distinct_agents("ジャンプ") == 1


def test_stage2_prompt_asks_for_the_five_contract_fields():
    llm = ScriptedLLM(CLEAN_ROW)
    reg = UndefinedActionRegistry(adjudicator=llm, threshold_agents=1)
    reg.observe("ジャンプ", agent_id=0, tick=1)
    prompt = llm.requests[0].prompt
    for field_name in ("前提:", "効果:", "コスト:", "失敗:", "台帳照合:"):
        assert field_name in prompt
    assert "ジャンプ" in prompt and ADJUDICATION_TEMPLATE


def test_no_adjudicator_means_no_stage2():
    reg = UndefinedActionRegistry(threshold_agents=1)
    out = reg.observe("ジャンプ", agent_id=0, tick=1)
    assert out.stage == 1 and reg.proposals == {}


# ---------------------------------------------------------------- 段3
def test_stage3_rows_touching_conservation_need_parent_review():
    llm = ScriptedLLM(CONSERVATION_ROW)
    reg = UndefinedActionRegistry(adjudicator=llm, threshold_agents=1)
    out = reg.observe("値切る", agent_id=0, tick=1)
    p = out.proposal
    assert p is not None and p.status is ProposalStatus.NEEDS_PARENT_REVIEW
    assert set(p.keywords_hit) >= {"保存則", "在庫", "所持金"}
    assert reg.counters()["needs_parent_review"] == 1
    # **自動採用しない**: 語彙は増えていない
    assert reg.vocabulary_extension == {} and reg.precedents == {}


def test_stage3_clean_rows_stay_merely_proposed():
    llm = ScriptedLLM(CLEAN_ROW)
    reg = UndefinedActionRegistry(adjudicator=llm, threshold_agents=1)
    out = reg.observe("上る", agent_id=0, tick=1)
    assert out.proposal.status is ProposalStatus.PROPOSED
    assert reg.vocabulary_extension == {}


# ---------------------------------------------------------------- 段4
def _spec(word: str) -> ActionSpec:
    return ActionSpec(
        word=word,
        target_kind=TargetKind.CELL,
        preconditions=("stairs_exist",),
        precondition_text="同一セルに階段がある",
        effects="位置=上階のセルへ",
        cost="時間",
        failure_text="階段がない",
        failure_codes=("UNREACHABLE",),
        tag="expedient",
        section="2.1",
    )


def test_stage4_adoption_makes_the_second_occurrence_deterministic():
    llm = ScriptedLLM(CLEAN_ROW)
    reg = UndefinedActionRegistry(adjudicator=llm, threshold_agents=1)
    reg.observe("跳ぶ", agent_id=0, tick=1)
    assert len(llm.requests) == 1
    proposal = reg.adopt("跳ぶ", _spec("移動"))
    assert proposal.status is ProposalStatus.ADOPTED
    out = reg.observe("跳ぶ", agent_id=5, tick=2)
    assert out.stage == 4 and out.word == "移動" and out.source == "precedent"
    assert len(llm.requests) == 1, "判例化のあとは**呼ゼロ**"


def test_stage4_can_add_a_brand_new_word_to_the_runtime_vocabulary():
    reg = UndefinedActionRegistry()
    reg.observe("献血", agent_id=0, tick=1)
    reg.adopt("献血", _spec("献血"))
    assert "献血" in reg.vocabulary_extension
    out = reg.observe("献血", agent_id=1, tick=2)
    assert out.stage == 4 and out.word == "献血"


def test_stage4_needs_parent_review_rows_are_only_adopted_explicitly():
    llm = ScriptedLLM(CONSERVATION_ROW)
    reg = UndefinedActionRegistry(adjudicator=llm, threshold_agents=1)
    reg.observe("値切る", agent_id=0, tick=1)
    assert reg.observe("値切る", agent_id=1, tick=2).stage == 1  # まだ写らない
    reg.adopt("値切る", _spec("購入"))  # ← 親の明示行為
    assert reg.observe("値切る", agent_id=2, tick=3).word == "購入"


def test_reject_keeps_the_word_out_of_the_vocabulary():
    llm = ScriptedLLM(CLEAN_ROW)
    reg = UndefinedActionRegistry(adjudicator=llm, threshold_agents=1)
    reg.observe("瞬間移動", agent_id=0, tick=1)
    p = reg.reject("瞬間移動", "物理的に不可能")
    assert p.status is ProposalStatus.REJECTED
    assert reg.observe("瞬間移動", agent_id=1, tick=2).stage == 1


def test_adopt_requires_an_action_spec():
    reg = UndefinedActionRegistry()
    with pytest.raises(TypeError):
        reg.adopt("ジャンプ", "移動")  # type: ignore[arg-type]


def test_registry_works_with_the_project_mock_llm():
    """裁定側に ``MockLLM`` を挿しても契約(1呼・状態遷移)は壊れない。"""
    reg = UndefinedActionRegistry(adjudicator=MockLLM(master_seed=7), threshold_agents=2)
    reg.observe("ジャンプ", agent_id=0, tick=1)
    out = reg.observe("ジャンプ", agent_id=1, tick=2)
    assert isinstance(out.proposal, Proposal)
    assert reg.n_adjudication_calls == 1
