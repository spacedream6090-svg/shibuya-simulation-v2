"""templates: 文面凍結(§1 条5)・ブロック表(§2.2)・段階語彙の釘付け(§2.4 ⑤)。"""

from __future__ import annotations

import pytest

from shibuya.perception import templates as T
from shibuya.perception.channels import estimate_tokens

#: **凍結値**。この値が変わる変更 = 改版(delta+感度試験が要る・知覚契約書 §1 条5)。
#: v1.1(5 段目 5a・D-118 K2・第291): B5 の空腹の語の項 ``HUNGER_ITEM_TEMPLATE`` と ``HUNGER_WORDS`` を足した。
#: 旧 v1 の凍結値 = 161fe181bc325f003d874fb5c91e6142c01449fb09ac5f8b377b715a945608de
#: v1.2(記憶 第 1 段 6b・M4・第295): B5「記憶」の行 ``B5.memory`` と項の定型・事象の語を足した。
#: 旧 v1.1 の凍結値 = 8f2959d0d3fbe75ee0ca5a634425447bb316baaa6b36af9c570fa34eeb5617ef(6b で v1.2 へ張り替え)
#: v1.3(D-120 7c・第298): 記憶の行の項に店の評価の定型(store/store_known/store_heard)を足した。
#: 旧 v1.2 の凍結値 = 1f6c7d6227a11de049dde39d43728fa5919ccf263a0165ea5273b0d052150560(7c で v1.3 へ張り替え)
#: v1.4(C10 8a・第299): B5 近接行の人物の印「(知人)/(未知)」を定数 NEAR_PERSON_MARKS へ(文面は同じ)。
#: 旧 v1.3 の凍結値 = ea204a66ad13af47024baa2ab51ca7ad0063f8318dd870662682b66c556eb2b0(8a で v1.4 へ張り替え)
FROZEN_TEMPLATE_SHA256 = "40af870ea9cfbceefbe86765fba6e4844537111b3217ada42181bd60b82a20ed"


def test_template_sha256_is_frozen():
    """テンプレ版ハッシュが釘付け(改版は意図的にこの定数を書き換えること)。"""
    assert T.template_sha256() == FROZEN_TEMPLATE_SHA256
    assert T.TEMPLATE_VERSION == "v1.4"


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


# ---------------------------------------------------------------- D-113 ④ 役割語の提示(第269)
def test_role_words_match_llm_contract():
    """``llm.contract.ROLE_ACTION_WORDS`` との二重定義が一致している(同層で import 不可)。"""
    from shibuya.llm import contract

    assert tuple(contract.ROLE_ACTION_WORDS) == T.ROLE_WORDS_12
    assert len(T.ROLE_WORDS_12) == 12


def test_b0_with_role_words_appends_one_line_and_keeps_the_frozen_base_d113_4():
    base = T.b0_system()
    assert base is T.TEMPLATES["B0.system"], "既定は同一オブジェクト(凍結)"
    rw = T.b0_system("vocab", "v1", True)
    assert rw == base + "\n" + T.ROLE_WORDS_LINE
    last = rw.split("\n")[-1]
    assert last.startswith("[出力規約] 役割語: ")
    for w in T.ROLE_WORDS_12:
        assert w in last
    assert "権限" in last
    # どの腕・版でも同じ 1 行(第274: 語彙 v3 は 11 語の行・v3 は vocab 腕だけ)
    for mode in T.INTENT_MODES:
        for ver in T.VOCAB_VERSIONS:
            if ver == "v3" and mode != "vocab":
                continue
            line = T.role_words_line(ver)
            assert line == (T.ROLE_WORDS_LINE_V3 if ver == "v3" else T.ROLE_WORDS_LINE)
            assert T.b0_system(mode, ver, True) == T.b0_system(mode, ver) + "\n" + line
            assert T.b0_system(mode, ver, "on") == T.b0_system(mode, ver, True)
            assert T.b0_system(mode, ver, "off") is T.b0_system(mode, ver)
    # 指紋: 無し(既定)は従来どおり・有りは別の値
    assert T.b0_sha256("vocab", "v1", False) == T.b0_sha256()
    assert T.b0_sha256("vocab", "v1", True) != T.b0_sha256()
    assert T.check_role_words("on") is True and T.check_role_words("off") is False
    with pytest.raises(ValueError):
        T.check_role_words("maybe")


def test_b0_with_role_words_stays_within_the_shared_static_group_budget():
    b0 = estimate_tokens(T.b0_system("vocab", "v2", True))
    b1 = estimate_tokens(T.TEMPLATES["B1.kind"].format(kind="来街者"))
    b3 = sum(
        estimate_tokens(T.TEMPLATES[k].format(hour="12", minute="40", weather="晴",
                                              daylight="日中", heat="やや暑い"))
        for k in ("B3.time", "B3.weather", "B3.heat")
    )
    assert b0 + b1 + b3 <= T.GROUP_TOKEN_BUDGET["shared_static"]
    print(f"\n[B0+役割語] {b0} tok(共有静的合計 {b0 + b1 + b3} / {T.GROUP_TOKEN_BUDGET['shared_static']})")



# ---------------------------------------------------------------- 語彙 v3(第274・D-116・アジェンダ §1-2)
#: **語彙 v3 の B0 の指紋**(2026-09-27 に凍結)。v3 の文面・語の並びを変えたら必ずここが動く。
B0_SHA256_VOCAB_V3 = "3acf644965580f6c666bb7e3d073425e5e3ced932ab8da77860fb0a83ad2c3c7"
#: 同(役割語の 1 行つき=ランの既定 ``role_words=True``)。
B0_SHA256_VOCAB_V3_ROLE = "1fe90d13d0878c6ee7916c4f272d7229e8a118b4dcc2a4eca20263d34279ec58"


def _shared_static_tokens(b0: str) -> int:
    b1 = estimate_tokens(T.TEMPLATES["B1.kind"].format(kind="来街者"))
    b3 = sum(
        estimate_tokens(T.TEMPLATES[k].format(hour="12", minute="40", weather="晴",
                                              daylight="日中", heat="やや暑い"))
        for k in ("B3.time", "B3.weather", "B3.heat")
    )
    return estimate_tokens(b0) + b1 + b3


def test_v3_b0_fingerprint_and_the_frozen_v1():
    assert T.template_sha256() == FROZEN_TEMPLATE_SHA256, "v1.1 の凍結 SHA は不変"
    assert T.b0_system() is T.TEMPLATES["B0.system"]
    assert T.b0_system("vocab", "v3") == T.B0_SYSTEM_V3
    assert T.b0_sha256("vocab", "v3") == B0_SHA256_VOCAB_V3
    assert T.b0_sha256("vocab", "v3", True) == B0_SHA256_VOCAB_V3_ROLE


def test_v3_b0_stays_within_the_shared_static_group_budget():
    for rw in (False, True):
        total = _shared_static_tokens(T.b0_system("vocab", "v3", rw))
        assert total <= T.GROUP_TOKEN_BUDGET["shared_static"], (rw, total)
    print(f"\n[B0 v3+役割語] 共有静的合計 {total} / {T.GROUP_TOKEN_BUDGET['shared_static']}")


def test_v3_b0_drops_the_placeholder_words_d89():
    """D-89 (i)(b): 「物のカテゴリ」「セルID」を書かせない(v1 の B0 は不変)。"""
    assert "物のカテゴリ" not in T.B0_SYSTEM_V3 and "セルID" not in T.B0_SYSTEM_V3
    assert "物のカテゴリ" in T.B0_SYSTEM and "セルID" in T.B0_SYSTEM


def test_v3_output_spec_has_the_five_slots_and_the_note():
    spec = T.OUTPUT_SPEC_V3
    line2 = [ln for ln in spec.split("\n") if ln.startswith("行動:")]
    assert len(line2) == 1
    for label in ("行動: <", " 対象: <", " 活動: <", " まで: <"):
        assert label in line2[0], label
    assert "ひと言" not in spec
    assert "まで: <到着 / 相手 / N分 / HH:MM / 次の予定>" in line2[0]
    assert "あたり" in line2[0] and "自宅 / 職場 / 学校" in line2[0]
    assert "活動: は世界を変えない過ごし方。まで: は次に考え直す目安。途中で驚くことがあれば早く考え直す" in spec
    for w in T.ACTION_WORDS_V3:
        assert w in line2[0]
    for w in ("待機", "休憩", "降車"):
        assert w not in line2[0]


def test_v3_b0_differs_only_in_the_target_knowledge_and_the_output_spec():
    v1 = T.B0_SYSTEM.split("\n")
    v3 = T.B0_SYSTEM_V3.split("\n")
    n_spec = len(T.OUTPUT_SPEC.split("\n"))
    assert len(v3) == len(v1) + 1, "1 行説明の分だけ増える"
    head_v1, head_v3 = v1[:-n_spec], v3[: len(v1) - n_spec]
    diff = [i for i, (a, b) in enumerate(zip(head_v1, head_v3)) if a != b]
    assert len(diff) == 1
    assert head_v1[diff[0]].startswith("[役割知識] 対象") and head_v3[diff[0]].startswith("[役割知識] 対象")
    assert v1[-n_spec:-1] == v3[-n_spec - 1:-2], "出力規約の 1〜3 行目は同文"


def test_v3_vocab_twins_match_llm_contract():
    from shibuya.llm import contract

    assert T.VOCAB_VERSIONS == contract.VOCAB_VERSIONS
    assert T.ACTION_WORDS_V3 == contract.ACTION_VOCAB_V3
    assert T.ROLE_WORDS_V3 == contract.ROLE_ACTION_WORDS_V3
    assert len(T.ROLE_WORDS_V3) == 11 and "並ぶ" not in T.ROLE_WORDS_LINE_V3
    for w in T.ROLE_WORDS_V3:
        assert w in T.ROLE_WORDS_LINE_V3
    assert T.role_words_line("v1") is T.role_words_line("v2") is T.ROLE_WORDS_LINE


def test_v3_is_the_vocab_arm_only():
    for mode in ("open", "hint"):
        with pytest.raises(ValueError):
            T.b0_system(mode, "v3")
        with pytest.raises(ValueError):
            T.b0_sha256(mode, "v3")


def test_renderer_v3_changes_only_the_b0_block():
    """共有ブロックの差は B0 だけ。個体ブロック(B5/B6)は段 2(第276)で v1 の語(待機/休憩)を
    v3 の語彙へ読み替えた(``renderer.ACTIVITY_WORDS_V3``/``RESULT_OPTIONS_V3``)。"""
    import numpy as np

    from shibuya.agents.state import AgentKind, AgentState
    from shibuya.perception.renderer import Renderer
    from shibuya.world.state import World

    def render(ver: str):
        w = World.synthetic(n_cells=9, seed=2)
        a = AgentState(12)
        g = np.random.default_rng(11)
        with a.writable():
            a.cell[:] = g.integers(0, 9, size=12)
            a.xy[:] = g.uniform(0.0, 80.0, size=(12, 2))
            a.kind[:] = AgentKind.VISITOR
            a.money[:] = 5_000
            a.hunger[:] = 6
            a.last_result_tick[:] = 1
        w.cells.density[:] = w.compute_density(a.cell)
        r = Renderer(w, a, seed=13, vocab_version=ver, role_words=True)
        r.prepare_tick(750)
        return r.render(0, tick=750, wake_reason=3)

    v1, v3 = render("v1"), render("v3")
    assert v1.blocks["B0"] != v3.blocks["B0"] and v1.prompt_hash != v3.prompt_hash
    for bid in ("B1", "B2", "B3", "B4", "B4b"):
        assert v1.blocks[bid] == v3.blocks[bid], bid
    for bid in ("B5", "B6"):
        text = v3.blocks[bid].decode("utf-8")
        assert "待機" not in text and "休憩" not in text, (bid, text)
