"""templates: 文面凍結(§1 条5)・ブロック表(§2.2)・段階語彙の釘付け(§2.4 ⑤)。"""

from __future__ import annotations

import pytest

from shibuya.perception import templates as T
from shibuya.perception.channels import estimate_tokens

#: **凍結値**。この値が変わる変更 = 改版(delta+感度試験が要る・知覚契約書 §1 条5)。
FROZEN_TEMPLATE_SHA256 = "161fe181bc325f003d874fb5c91e6142c01449fb09ac5f8b377b715a945608de"


def test_template_sha256_is_frozen():
    """テンプレ版ハッシュが釘付け(改版は意図的にこの定数を書き換えること)。"""
    assert T.template_sha256() == FROZEN_TEMPLATE_SHA256
    assert T.TEMPLATE_VERSION == "v1"


def test_block_table_matches_contract_section_2_2():
    """§2.2 のブロック表(順序=変化率の昇順・予算 tok)と 1 対 1。"""
    assert T.BLOCK_IDS == ("B0", "B1", "B2", "B3", "B4", "B4b", "B5", "B6")
    assert dict(T.BLOCK_TOKEN_BUDGET) == {
        "B0": 300, "B1": 100, "B2": 150, "B3": 100,
        "B4": 60, "B4b": 40, "B5": 220, "B6": 80,
    }
    assert dict(T.GROUP_TOKEN_BUDGET) == {
        "shared_static": 750, "cell": 250, "individual": 300,
    }
    assert T.OUTPUT_TOKENS_DEFAULT == 64
    for b in T.BLOCK_IDS:
        assert T.block_group(b) in T.GROUP_TOKEN_BUDGET


def test_b0_keeps_the_ordinance_rules():
    """§2.5「B0 に**条例の適用規則を明記する方針を維持**」(v0 ③役割知識QAが不合格だった)。"""
    b0 = T.TEMPLATES["B0.system"]
    for needle in (
        "午後6時から翌朝5時",  # 路上飲酒の条例
        "客引き行為等防止啓発地区",
        "5万円の過料",
        "24時間以内",
        "7日以内",
        "午後11時から翌午前6時",  # 深夜営業の制限
    ):
        assert needle in b0, needle
    # 憲法 6 条が全部載っている
    assert b0.count("[憲法]") == 6


def test_b0_output_spec_is_the_two_line_form():
    """行動契約書 §1 の 2 行形(理由 / 行動・対象・ひと言)。旧「行き先」は使わない。"""
    spec = T.OUTPUT_SPEC
    assert "2行だけ書く" in spec
    assert "理由: <40字以内・1文>" in spec
    assert "対象: <セルID / 物のカテゴリ / 人ID / なし>" in spec
    assert "ひと言: <20字以内の発話、または なし>" in spec
    assert "行き先" not in spec
    for w in T.ACTION_WORDS_12:
        assert w in spec


def test_b0_over_block_budget_but_within_shared_static_group():
    """**解決した曖昧点**: B0 単体は 300 tok を超えるが、共有静的グループ ≤750 に収まる。"""
    b0 = estimate_tokens(T.TEMPLATES["B0.system"])
    b1 = estimate_tokens(T.TEMPLATES["B1.kind"].format(kind="来街者"))
    b3 = sum(
        estimate_tokens(T.TEMPLATES[k].format(hour="12", minute="40", weather="晴",
                                              daylight="日中", heat="やや暑い"))
        for k in ("B3.time", "B3.weather", "B3.heat")
    )
    assert b0 > T.BLOCK_TOKEN_BUDGET["B0"], "v0 文面を保つと B0 単体は 300 を超える(既知)"
    assert b0 + b1 + b3 <= T.GROUP_TOKEN_BUDGET["shared_static"]
    print(f"\n[B0] {b0} tok(単体予算 300・共有静的合計 {b0 + b1 + b3} / 750)")


def test_b1_has_no_individual_words():
    """§2.4 ⑧: B1 から v0 の年代・性別(個体依存語)を落とした。"""
    b1 = T.TEMPLATES["B1.kind"]
    assert "年代" not in b1 and "性別" not in b1
    assert set(T.KIND_WORDS) >= {"通勤者", "来街者", "従業者", "居住者"}


def test_density_stage_edges_are_pegged_to_fruin_los():
    """§2.4 ⑤: 密度段の境界は Fruin 歩行路 LOS(sq ft/人 の逆数)に釘付け。"""
    sqft = (35.0, 25.0, 15.0, 10.0, 5.0)
    m2 = 0.09290304
    expected = tuple(1.0 / (s * m2) for s in sqft)
    assert T.DENSITY_LOS_EDGES_PER_M2 == pytest.approx(expected, abs=1e-4)
    assert len(T.DENSITY_LOS_LETTERS) == len(T.DENSITY_LOS_EDGES_PER_M2) + 1 == 6


def test_noise_stage_bounds_are_pegged_to_environment_standard():
    """§2.4 ⑤: 騒音段の境界は環境基準(道路に面する地域)昼60/65/70・夜55/60/65。"""
    assert T.NOISE_STAGE_BOUNDS_DAY == (60.0, 65.0, 70.0)
    assert T.NOISE_STAGE_BOUNDS_NIGHT == (55.0, 60.0, 65.0)
    assert T.NOISE_STAGE_VOCAB == ("静か", "普通", "騒がしい", "うるさい")


def test_noise_vocab_matches_the_build_side_definition():
    """``build.field.w10_noise`` との二重定義が一致している(層契約で共有できないため)。"""
    w10 = pytest.importorskip("shibuya.build.field.w10_noise")
    assert tuple(w10.NOISE_STAGE_VOCAB) == T.NOISE_STAGE_VOCAB
    assert tuple(w10.NOISE_STAGE_BOUNDS_DAY) == T.NOISE_STAGE_BOUNDS_DAY
    assert tuple(w10.NOISE_STAGE_BOUNDS_NIGHT) == T.NOISE_STAGE_BOUNDS_NIGHT


def test_action_vocab_matches_llm_contract():
    """``llm.contract.ACTION_VOCAB_12`` との二重定義が一致している(同層で import 不可)。"""
    contract = pytest.importorskip("shibuya.llm.contract")
    assert tuple(contract.ACTION_VOCAB_12) == T.ACTION_WORDS_12


def test_wake_reason_text_covers_all_wake_conditions():
    """§6 不応期表の 11 行(``agents.state.WakeCondition``)と 1 対 1。"""
    from shibuya.agents.state import N_WAKE_CONDITIONS

    assert len(T.WAKE_REASON_TEXT) == N_WAKE_CONDITIONS == 11
    assert all(s.endswith("。") for s in T.WAKE_REASON_TEXT)


def test_every_template_line_is_one_fact_with_a_feature_tag():
    """§2.1「素性タグ付きの短い平叙文(1行1事実)」= B1-B6 の行は ``[Bn 名]`` で始まる。"""
    for key, tpl in T.TEMPLATES.items():
        if key == "B0.system":
            continue
        assert tpl.startswith("["), key
        assert "\n" not in tpl, f"{key} は 1 行でなければならない"


def test_default_options_always_contain_the_never_failing_action():
    """行動契約書 §2.1「失敗しない行動が常に1つ以上(待機)」。"""
    assert "待機" in T.DEFAULT_OPTIONS
