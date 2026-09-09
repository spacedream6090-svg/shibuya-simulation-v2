"""応答の採点・違反判定・出力(Markdown/JSON)と、各ツールの純関数部分。

正典: 実装計画書 §9.1 C6 受入「書式エラー率 ≤0.10(温度0.7・実LLM・n≥59)・役割語率の再測」・
知覚契約書 §8 指標B。採点の定義は ``shibuya.llm.parser``(2行形)に一本化する。
"""

from __future__ import annotations

import json

import pytest

from shibuya.llm.contract import ROLE_ACTION_WORDS, format_two_line

GOOD = "理由: 予定の時間になったから\n行動: 移動 対象: C-0001 ひと言: なし"
BAD = "うーん、なんとも言えませんね。"
ROLE = "理由: 棚が空いたから\n行動: 補充 対象: 弁当 ひと言: なし"
UNKNOWN = "理由: 迷った\n行動: 瞑想 対象: なし ひと言: なし"
#: 段0 辞書(``llm.undefined.SYNONYMS_C6``)で「移動」へ救える語。
RESCUED = "理由: 見て回る\n行動: 探索 対象: なし ひと言: なし"


# ---------------------------------------------------------------- score_texts
def test_score_texts_counts_format_errors_and_actions(c6lib):
    s = c6lib.score_texts([GOOD, GOOD, BAD, ROLE, UNKNOWN])
    assert s["n"] == 5
    assert s["format_error_rate"] == pytest.approx(2 / 5)  # BAD と UNKNOWN
    assert s["action_counts"]["移動"] == 2
    assert s["action_counts"]["補充"] == 1
    assert s["action_counts"]["(未定義)"] == 2  # BAD も UNKNOWN も辞書で救えない
    assert s["undefined_rate"] == pytest.approx(2 / 5)
    assert s["dictionary_mapped_rate"] == 0.0
    assert s["role_action_rate"] == pytest.approx(1 / 5)
    assert s["role_action_counts"] == {"補充": 1}
    assert set(s["role_vocab"]) == set(ROLE_ACTION_WORDS)


def test_undefined_rate_excludes_words_the_stage0_dictionary_rescues(c6lib):
    """段0 辞書(``map_synonym``)で救えた語は未定義に数えず、写像先の契約語として数える。"""
    from shibuya.llm.undefined import map_synonym

    assert map_synonym("探索")[0] == "移動"  # 前提(サブ Q の段0 辞書拡張)
    s = c6lib.score_texts([GOOD, RESCUED, UNKNOWN])
    assert s["undefined_rate"] == pytest.approx(1 / 3)  # UNKNOWN だけ
    assert s["dictionary_mapped"] == 1 and s["dictionary_mapped_rate"] == pytest.approx(1 / 3)
    assert s["action_counts"]["移動"] == 2  # GOOD + 救われた 探索
    assert s["action_counts"]["(未定義)"] == 1
    # 書式エラー率は辞書の救済とは別勘定(語彙一致していないので実効でもエラー)
    assert s["format_error_rate"] == pytest.approx(2 / 3)


def test_format_error_rate_is_reported_both_effective_and_strict(c6lib):
    """C6 のラベル別名を許した実効と、許さない厳密の二重(親判断 D-28)。

    C6 追加別名(``LABEL_ALIASES_C6``)だけで書けた応答は **実効=合格・厳密=エラー**になる。
    """
    from shibuya.llm.parser import LABEL_ALIASES_C6, parse_two_line

    c6_only = [
        t
        for surface, canonical in LABEL_ALIASES_C6.items()
        for t in [GOOD.replace(canonical + ":", surface + ":")]
        if parse_two_line(t).format_ok and not parse_two_line(t).strict_format_ok
    ]
    assert c6_only, "C6 追加別名が 1 つも効いていない(二重判定の意味が消える)"
    s = c6lib.score_texts(c6_only)
    assert s["format_error_rate"] == 0.0
    assert s["format_error_rate_strict"] == 1.0
    assert s["alias_used_rate"] == 1.0

    plain = c6lib.score_texts([GOOD] * 3)
    assert plain["alias_used_rate"] == 0.0 and plain["alias_surfaces"] == {}
    assert plain["format_error_rate"] == plain["format_error_rate_strict"] == 0.0


def test_alias_usage_is_counted_and_broken_down(c6lib):
    """英語ラベル(C6 以前からある別名)でも ``alias_used`` は立つ=内訳が出る。"""
    text = "reason: x\naction: 移動 destination: C-1 comment: なし"
    s = c6lib.score_texts([text, GOOD])
    assert s["alias_used_rate"] == pytest.approx(0.5)
    assert set(s["alias_surfaces"]) >= {"reason", "action"}
    assert s["format_error_rate"] == 0.0 and s["format_error_rate_strict"] == 0.0


def test_format_error_gate_needs_both_the_rate_and_the_sample_size(c6lib):
    assert c6lib.FORMAT_ERROR_MAX == 0.10 and c6lib.FORMAT_ERROR_MIN_N == 59
    small = c6lib.score_texts([GOOD] * 10)
    assert small["format_error_rate"] == 0.0 and not small["format_error_ok"]  # n<59
    big = c6lib.score_texts([GOOD] * 59)
    assert big["format_error_ok"]
    over = c6lib.score_texts([GOOD] * 50 + [BAD] * 9)
    assert over["format_error_rate"] > 0.10 and not over["format_error_ok"]


def test_score_texts_uses_the_canonical_two_line_writer(c6lib):
    text = format_two_line("腹が減った", "購入", "弁当", "なし")
    s = c6lib.score_texts([text])
    assert s["format_error_rate"] == 0.0 and s["strict_two_line_rate"] == 1.0
    assert s["action_counts"] == {"購入": 1}


# ---------------------------------------------------------------- 違反判定
def _scene(c6lib, kind):
    return c6lib.Scene(agent_id=0, tick=0, wake_class=3, prompt="", constraint=kind)


def test_violation_flags_use_the_banned_action_table(c6lib):
    scenes = [_scene(c6lib, "closed"), _scene(c6lib, "closed"), _scene(c6lib, "train_full")]
    texts = [
        format_two_line("店は閉まっている", "購入", "弁当", "なし"),  # 違反
        format_two_line("開くまで待つ", "待機", "なし", "なし"),  # 遵守
        format_two_line("次の電車に乗る", "乗車", "なし", "なし"),  # 違反
    ]
    assert c6lib.violation_flags(scenes, texts) == [1, 0, 1]


def test_kinds_outside_the_table_are_never_flagged(c6lib):
    scenes = [_scene(c6lib, "bad_target"), _scene(c6lib, "")]
    texts = [format_two_line("もう一度", "移動", "なし", "なし")] * 2
    assert c6lib.violation_flags(scenes, texts) == [0, 0]


# ---------------------------------------------------------------- 出力
def test_markdown_table_shape(c6lib):
    md = c6lib.markdown_table(["a", "b"], [[1, 2], [3, None]])
    lines = md.splitlines()
    assert lines[0] == "| a | b |" and lines[1] == "|---|---|"
    assert lines[2] == "| 1 | 2 |" and lines[3] == "| 3 |  |"


def test_write_outputs_writes_both_files(c6lib, tmp_path):
    paths = c6lib.write_outputs(tmp_path / "d", "x", {"k": [1, "あ"]}, "# t")
    assert json.loads(open(paths["json"], encoding="utf-8").read()) == {"k": [1, "あ"]}
    assert open(paths["md"], encoding="utf-8").read() == "# t\n"


def test_common_parser_has_the_five_required_flags(c6lib):
    ap = c6lib.common_parser("x")
    args = ap.parse_args(
        ["--endpoints", "http://a:1, http://b:2", "--world", "w", "--agents", "7",
         "--ticks", "3", "--out", "o"]
    )
    assert c6lib.endpoints_of(args) == ["http://a:1", "http://b:2"]
    assert args.world == "w" and args.agents == 7 and args.ticks == 3 and args.out == "o"


def test_world_dir_of_returns_none_for_a_missing_path(c6lib, tmp_path):
    ap = c6lib.common_parser("x")
    assert c6lib.world_dir_of(ap.parse_args(["--world", str(tmp_path / "nope")])) is None
    assert c6lib.world_dir_of(ap.parse_args(["--world", str(tmp_path)])) == tmp_path


def test_split_prompt_cuts_at_the_first_individual_block(c6lib):
    system, user = c6lib.split_prompt("役割\n出力規約: …\n[B1 種別] あなたは来街者です。\n[B6 問い] ")
    assert system.endswith("出力規約: …") and user.startswith("[B1 種別]")
    assert c6lib.split_prompt("何も無い") == ("", "何も無い")


# ---------------------------------------------------------------- ツールの純関数
def test_t6_compare_tapes_detects_a_single_mismatch():
    import t6_bit_reproduce as t6

    a = {(1, 0, 3, "p"): ("同じ", "c0"), (2, 0, 3, "q"): ("A", "c1")}
    b = {(1, 0, 3, "p"): ("同じ", "c0"), (2, 0, 3, "q"): ("B", "c1")}
    r = t6.compare_tapes(a, b)
    assert r["n_common"] == 2 and r["n_mismatch"] == 1 and not r["ok"]
    assert r["match_rate"] == pytest.approx(0.5) and r["mismatch_call_ids"] == ["c1"]
    assert t6.compare_tapes(a, a)["ok"]


def test_t6_flags_calls_present_in_only_one_tape():
    import t6_bit_reproduce as t6

    r = t6.compare_tapes({(1, 0, 3, "p"): ("x", "c0")}, {})
    assert r["n_common"] == 0 and r["n_only_a"] == 1 and not r["ok"]


def test_t6_manifest_note_says_it_does_not_claim_bit_reproduction():
    import t6_bit_reproduce as t6

    note = t6.MANIFEST_NOTE_NG.format(n=100, n_diff=4, rate=0.96)
    assert "bit 再現を主張しない" in note
    assert "bit 再現を主張する" in t6.MANIFEST_NOTE_OK.format(n=100, engine="fleet")


def test_t7_distribution_report_carries_jsd_null_and_chi2():
    import t7_distribution as t7

    r = t7.distribution_report({"移動": 50, "待機": 50}, {"移動": 52, "待機": 48}, "行動語", 1)
    assert r["label"] == "行動語" and r["n_a"] == 100 and r["n_b"] == 100
    assert 0.0 <= r["jsd_bits"] < 0.05
    assert r["null_p50"] < r["null_p95"]
    assert r["chi2"]["p"] > 0.05


def test_t7_gate_is_declared_undecided():
    import t7_distribution as t7

    assert "親判断待ち" in t7.T7_GATE_NOTE and "D-25" in t7.T7_GATE_NOTE


def test_metric_b_compare_passes_reports_both_halves(c6lib):
    import metric_b_rerun as mb

    scenes = [_scene(c6lib, "closed") for _ in range(40)]
    keep = format_two_line("待つ", "待機", "なし", "なし")
    viol = format_two_line("買う", "購入", "弁当", "なし")
    a = mb.score_pass(scenes, [keep] * 40)
    b = mb.score_pass(scenes, [keep] * 38 + [viol] * 2)
    cmp_ = mb.compare_passes(a, b, None, seed=1)
    assert a["violation_rate"] == 0.0 and b["violation_rate"] == pytest.approx(0.05)
    assert cmp_["delta_violation_rate"] == pytest.approx(0.05)
    assert cmp_["discordant_pairs"] == {"a_only": 0, "b_only": 2}
    assert cmp_["violation_gate"] == 0.05
    assert "jsd_bits" in cmp_ and "null_bootstrap_p95" in cmp_


def test_metric_b_null_pass_is_reported_when_given(c6lib):
    import metric_b_rerun as mb

    scenes = [_scene(c6lib, "closed") for _ in range(20)]
    keep = format_two_line("待つ", "待機", "なし", "なし")
    a = mb.score_pass(scenes, [keep] * 20)
    cmp_ = mb.compare_passes(a, a, a, seed=1)
    assert cmp_["null_same_model_jsd_bits"] == pytest.approx(0.0)
    assert cmp_["distribution_ok"]


def test_ablation1_probe_detects_that_the_switch_is_effective(capsys):
    """§3.2 の義務 ablation の切替口が**効いている**ことを固定する(C6 で実装)。

    C6-b では ``BudgetMode.SINGLE_RANKING`` が枠(Enum)だけで no-op だった。切替の実装
    (``Renderer(budget_mode=…)`` → 単一ランキング)が入ったので期待を反転させる。
    レンダラ側の中身は ``tests/perception/test_ablation1.py``。
    """
    import ablation1_fixed_vs_ranking as ab1

    probe = ab1.probe_switch(n_agents=16, n_cells=9, seed=1, n_scenes=6)
    with capsys.disabled():
        print(f"\n[ablation①] 描画差 {probe['n_different']}/{probe['n_scenes']} 場面")
    assert probe["n_scenes"] == 6
    assert probe["switch_effective"], probe
    assert probe["n_different"] == 6 and probe["note"] == ""


def test_format_role_acceptance_rows_render_the_c6_table(c6lib):
    import format_role_rates as fr

    score = c6lib.score_texts([GOOD] * 59 + [ROLE])
    rows = fr.acceptance_rows(score, {"deferred": 12, "promoted": 0, "degraded": 3, "suppressed": 1})
    names = [r[0] for r in rows]
    assert names[0] == "書式エラー率(実効・主)" and names[1] == "書式エラー率(厳密・併記)"
    assert "ラベル別名率" in names and "役割語率(全12語)" in names
    assert "未定義行動率(段0 辞書で救えず)" in names and "段0 辞書で救えた率" in names
    assert all(f"　役割語 {w}" in names for w in fr.WATCHED_ROLE_WORDS)
    assert [n for n in names if n.startswith("診断行 ")] == [
        "診断行 deferred", "診断行 promoted", "診断行 degraded", "診断行 suppressed"
    ]
    assert rows[0][4] == rows[1][4] == "合格"  # n=60 ≥ 59・エラー 0


def test_format_role_marks_a_small_sample_as_insufficient(c6lib):
    import format_role_rates as fr

    rows = fr.acceptance_rows(c6lib.score_texts([GOOD] * 10), None)
    assert rows[0][4] == "標本不足" and rows[1][4] == "標本不足"


def test_format_role_table_separates_effective_and_strict_verdicts(c6lib):
    """実効は合格・厳密は不合格、という組み合わせが表に出る(D-28 の読み分け)。"""
    import format_role_rates as fr
    from shibuya.llm.parser import LABEL_ALIASES_C6, parse_two_line

    c6_only = next(
        t
        for surface, canonical in LABEL_ALIASES_C6.items()
        for t in [GOOD.replace(canonical + ":", surface + ":")]
        if parse_two_line(t).format_ok and not parse_two_line(t).strict_format_ok
    )
    rows = fr.acceptance_rows(c6lib.score_texts([c6_only] * 60), None)
    assert rows[0][4] == "合格" and rows[1][4] == "不合格"
