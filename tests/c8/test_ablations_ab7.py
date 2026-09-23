"""腕 ``AB7-OPEN-INTENT`` / ``AB7b-HINT-INTENT`` の腕定義行と、M1〜M3 の集計
(open-intent 仕様書 §1・§4 (d))。

見るもの
(d1) ``ablations_v1.json`` に AB7 が増え(rank 7)、その後ろに **AB7b が足された**
     (rank 8・末尾・切替口つき)/
(d2) **既存 7 腕の定義はバイト不変**(``json.dumps(sort_keys=True)`` の SHA256 が
     追加前の値のまま)。ここが動いたら既存の腕の意味が変わっている=止まる/
(d3) ``runs`` の ``kwargs`` が ``intent_mode`` の 2 本で、許可リストを通る/
(d4) ``run_metrics`` が M1(2 段接地率)・M2(未定義率)・M3(上位未定義語)を出し、
     **既存腕の出力は列追加のみ**(既存の値は動かない)。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

import pytest

ARM_ID = "AB7-OPEN-INTENT"
#: ヒント腕(2026-09-17・ユーザー決定「24 語を例として見せつつ自由文も許す」)。
ARM_B_ID = "AB7b-HINT-INTENT"

#: 腕定義のカノニカル JSON SHA256(第1陣 6 本は AB7 追加前・AB7 は AB7b 追加前の値)。
#: ``hashlib.sha256(json.dumps(arm, sort_keys=True, ensure_ascii=False).encode()).hexdigest()``。
FROZEN_ARM_SHA256 = {
    "AB1-BUDGET-MODE": "06e6ca1f1a734210fc7732ed21d0c9390f11c28a270ce5cd9349c15105c9f4d2",
    "AB2-PNOTICE-D50": "65a62c39a941c700c1b7ed8e66602db29ff6aeaecea8298d25e56da5265fc79e",
    "AB3-REFRACTORY-PROX": "7ce6da150d4031001491cd4221ceb50abeeac86931acd8318dc2f437c6ffadee",
    "AB4-HEARING-SNR": "a5767a3178a2eec2ada6c54225c68b7747367ae47513a5b0d137da2a0f6dcfcd",
    "AB5-INTROSPECTION": "bc969f25382f5ac88d295a5639d348a58cc18130bdab86c0a13eb517a71d0146",
    "AB6-AD-ZERO": "0b53c0308f45ab27a098ca03ce43bce42039eb7e4ac3ffa93816253aabbe0507",
    # AB7b を足しても AB7 の定義は 1 バイトも動かない(2026-09-17 に凍結)。
    "AB7-OPEN-INTENT": "be19b47185476fdd2e5154f61ce5fa31818811a11510f43be738b8af764dde7d",
    # AB7c(語彙 v2)を足しても AB7b の定義は 1 バイトも動かない(2026-09-17 に凍結)。
    "AB7b-HINT-INTENT": "e53d363aa18533228c0e9754d0a287ccd617937347cce3cd8af3113a88a3d7f0",
    # AB6b(看板の注視ゲート・D-59 (b))を足しても AB7c の定義は 1 バイトも動かない。
    "AB7c-VOCAB-V2": "f5cd4a8a84172d379f84e03a3e7e0095847530b90558c3322635ffe0326b66b0",
}

#: 語彙 v2 の腕(``tests/c8/test_ablations_ab7c.py`` が本体を見る。ここでは**並び**だけ)。
ARM_C_ID = "AB7c-VOCAB-V2"
#: 看板の注視ゲートの腕(``tests/c8/test_ablations_ab6b.py`` が本体を見る・2026-09-17 D-59 (b))。
ARM_AD_NOTICE_ID = "AB6b-AD-NOTICE"


@pytest.fixture(scope="module")
def table(c8lib):
    return c8lib.load_ablations()


def _canonical_sha256(arm) -> str:
    return hashlib.sha256(
        json.dumps(arm, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------- (d1)(d2) 腕定義表
def test_ab7_is_appended_to_the_table(ablation_runner, table):
    arms = table["arms"]
    ids = [a["id"] for a in arms]
    # AB7 の後ろに AB7b・AB7c(語彙 v2)、その後ろに AB6b(注視ゲート)を足した。
    # 2026-09-19: さらに AB8(L4 の感度)と AB6c(⑥b の無制限版)が末尾に付いた。
    # 2026-09-22: AB7d(語彙の無制限版)・AB1b(固定枠の無制限版)も末尾に付いた。
    assert ids[-8:] == [
        ARM_ID, ARM_B_ID, ARM_C_ID, ARM_AD_NOTICE_ID,
        "AB8-L4-SCALE", "AB6c-AD-NOTICE-UNCAPPED", "AB7d-VOCAB-UNCAPPED", "AB1b-BUDGET-MODE-UNCAPPED",
    ]
    assert len(arms) == len(FROZEN_ARM_SHA256) + 5
    arm = ablation_runner.arm_by_id(table, ARM_ID)
    assert arm["rank"] == 7 and arm["index"] == "⑦"
    assert arm["design_source"].startswith("docs/design/v2-open-intent-arm-spec.md")
    assert ARM_ID not in ablation_runner.first_wave_ids(table)
    assert ablation_runner.validate_table(table) == []


def test_the_existing_arms_are_byte_identical(table):
    """**後から腕を足しても既存の腕の定義は 1 バイトも動かない**(golden は追加前の値)。

    2026-09-17 の AB6b(看板の注視ゲート・D-59 (b))追加で AB7c も凍結側に入った
    =いま凍らせていないのは末尾の AB6b 1 本だけ。
    """
    got = {a["id"]: _canonical_sha256(a) for a in table["arms"] if a["id"] in FROZEN_ARM_SHA256}
    assert got == FROZEN_ARM_SHA256


def test_ab7_switch_and_runs(ablation_runner, table):
    arm = ablation_runner.arm_by_id(table, ARM_ID)
    sw = arm["switch"]
    assert sw["kind"] == "implemented_flag"
    assert sw["implemented"] is True
    assert sw["mock_effective"] is False, "MockLLM はプロンプトを読まない=mock では差が出ない"
    assert "--intent-mode" in sw["how"]
    assert [r["tag"] for r in arm["runs"]] == ["vocab", "open"]
    assert [r["kwargs"] for r in arm["runs"]] == [
        {"intent_mode": "vocab"}, {"intent_mode": "open"}
    ]
    assert arm["runs"][0]["is_baseline"] is True
    assert "is_baseline" not in arm["runs"][1]
    for r in arm["runs"]:
        assert set(r["kwargs"]) <= ablation_runner.ALLOWED_KWARGS
        assert not (set(r["kwargs"]) & ablation_runner.PENDING_KWARGS)


def test_ab7_kwargs_reach_run_day(ablation_runner, table, tmp_path):
    """腕定義の ``kwargs`` が ``cli.run`` → ``run_day`` までそのまま通る(mock・極小)。"""
    arm = dict(ablation_runner.arm_by_id(table, ARM_ID))
    out = ablation_runner.execute_arm(
        arm, agents=16, ticks=2, seed=1, world_dir=None,
        out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
    )
    assert out["executed"] is True
    assert [r["tag"] for r in out["runs"]] == ["vocab", "open"]
    assert [r["intent_mode"] for r in out["runs"]] == ["vocab", "open"]
    assert [r["run_manifest_fields"]["intent_mode"] for r in out["runs"]] == ["vocab", "open"]
    # mock では本文を読まないので checkpoint は動かない(=腕の差は実 LLM でしか出ない)
    assert out["comparisons"][0]["identical_final_hash"] is True
    assert any("実 LLM 必須" in n for n in out["notes"])


# ---------------------------------------------------------------- AB7b ヒント腕
def test_ab7b_keeps_rank_8(ablation_runner, table):
    arm = ablation_runner.arm_by_id(table, ARM_B_ID)
    assert arm["rank"] == 8 and arm["index"] == "⑦b"
    # 2026-09-17: AB7c(語彙 v2)・AB6b(注視ゲート)を後ろに足し、
    # 2026-09-19: さらに AB8(L4 の感度)・AB6c(⑥b の無制限版)を足した=**末尾の 4 つ手前**
    # 2026-09-22: AB7d・AB1b が末尾に付いた=**末尾の 6 つ手前**
    assert table["arms"][-7]["id"] == ARM_B_ID
    assert ARM_B_ID not in ablation_runner.first_wave_ids(table), "第1陣は 6 本のまま"
    assert arm["design_source"].startswith("docs/design/v2-open-intent-arm-spec.md")
    assert arm["status"] == "ready"


def test_ab7b_switch_and_runs(ablation_runner, table):
    arm = ablation_runner.arm_by_id(table, ARM_B_ID)
    sw = arm["switch"]
    assert sw["kind"] == "implemented_flag" and sw["implemented"] is True
    assert sw["mock_effective"] is False, "MockLLM はプロンプトを読まない=mock では差が出ない"
    assert "--intent-mode hint" in sw["how"]
    assert [r["tag"] for r in arm["runs"]] == ["vocab", "hint"]
    assert [r["kwargs"] for r in arm["runs"]] == [
        {"intent_mode": "vocab"}, {"intent_mode": "hint"}
    ]
    assert arm["runs"][0]["is_baseline"] is True
    assert "is_baseline" not in arm["runs"][1]
    for r in arm["runs"]:
        assert set(r["kwargs"]) <= ablation_runner.ALLOWED_KWARGS
        assert not (set(r["kwargs"]) & ablation_runner.PENDING_KWARGS)
    # vocab 対照は AB7 の vocab ランと**同一構成**=共有できる(表の control に明記)
    ab7 = ablation_runner.arm_by_id(table, ARM_ID)
    assert arm["runs"][0]["kwargs"] == ab7["runs"][0]["kwargs"]
    assert "共有" in arm["control"]


def test_ab7b_freezes_the_hint_b0_sha256(table, ablation_runner):
    """腕定義に書いた B0 の指紋が**実装の値と一致する**(文面を変えたら両方が動く)。"""
    from shibuya.perception.templates import b0_sha256

    arm = ablation_runner.arm_by_id(table, ARM_B_ID)
    assert b0_sha256("hint") in arm["switch"]["verified"]
    assert b0_sha256("vocab")[:8] in arm["switch"]["verified"]


def test_ab7b_kwargs_reach_run_day(ablation_runner, table, tmp_path):
    """腕定義の ``kwargs`` が ``cli.run`` → ``run_day`` までそのまま通る(mock・極小)。"""
    arm = dict(ablation_runner.arm_by_id(table, ARM_B_ID))
    out = ablation_runner.execute_arm(
        arm, agents=16, ticks=2, seed=1, world_dir=None,
        out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
    )
    assert out["executed"] is True
    assert [r["tag"] for r in out["runs"]] == ["vocab", "hint"]
    assert [r["intent_mode"] for r in out["runs"]] == ["vocab", "hint"]
    assert [r["run_manifest_fields"]["intent_mode"] for r in out["runs"]] == ["vocab", "hint"]
    # mock では本文を読まないので checkpoint は動かない(=腕の差は実 LLM でしか出ない)
    assert out["comparisons"][0]["identical_final_hash"] is True
    assert any("実 LLM 必須" in n for n in out["notes"])


# ---------------------------------------------------------------- (d4) M1〜M3 の集計
@dataclass
class _Registry:
    """``UndefinedActionRegistry`` の M2/M3 に要る面だけを持つスタブ。"""

    threshold_agents: int = 10
    words: dict = field(default_factory=lambda: {"待ち合わせ": 40, "見る": 7})
    agents: dict = field(default_factory=lambda: {"待ち合わせ": 12, "見る": 3})

    def counters(self):
        return {
            "undefined_records": sum(self.words.values()),
            "undefined_words": len(self.words),
            "undefined_dropped": 0,
            "dictionary_mapped": 53,
            "proposals": 0,
            "needs_parent_review": 0,
            "adopted": 0,
            "adjudication_calls": 0,
        }

    def top_words(self, k: int = 10):
        return sorted(self.words.items(), key=lambda kv: -kv[1])[:k]

    def distinct_agents(self, word: str) -> int:
        return int(self.agents.get(word, 0))


@dataclass
class _Res:
    n_agents: int = 100
    llm_calls: int = 1000
    renderer_counters: dict = field(default_factory=dict)
    bridge_counters: dict = field(default_factory=lambda: {"llm_calls": 1000.0})
    undefined_registry: object = field(default_factory=_Registry)
    intent_mode: str = "open"
    final_hash: str = "h"

    def diagnostics_day(self):
        return {}


def test_m2_m3_from_the_registry(ablation_runner):
    """M2 未定義率=undefined_records ÷ 解釈まで進んだ呼・M3=top_words+distinct agents。"""
    m = ablation_runner.run_metrics(_Res(), None)
    reg = m["undefined_registry"]
    assert m["intent_mode"] == "open"
    assert reg["n_calls"] == 1000
    assert reg["undefined_rate"] == pytest.approx(47 / 1000)  # 40 + 7
    assert reg["dictionary_rate"] == pytest.approx(53 / 1000)
    assert reg["grounded_direct"] == pytest.approx((1000 - 47 - 53) / 1000)
    assert reg["threshold_agents"] == 10 and reg["top_k"] == ablation_runner.M3_TOP_K
    assert [w["word"] for w in reg["top_words"]] == ["待ち合わせ", "見る"]
    assert reg["top_words"][0]["distinct_agents"] == 12
    assert reg["top_words"][0]["reached_threshold"] is True  # N=10 到達=§7 段2 の起草材料
    assert reg["top_words"][1]["reached_threshold"] is False
    assert reg["n_reached_threshold"] == 1


def test_registry_absent_leaves_the_column_empty(ablation_runner):
    """台帳が無い結果では**空辞書**(推測で埋めない)。"""
    m = ablation_runner.run_metrics(_Res(undefined_registry=None), None)
    assert m["undefined_registry"] == {}


def test_m1_two_stage_grounding_is_recomputable(ablation_runner):
    """M1 は 3 つの排他な件数 ÷ 非繰り延べ行数。3 つの和は厳密に n。"""
    sc = {
        "n": 200,
        "dictionary_mapped": 30,
        "action_counts": {"移動": 100, "待機": 50, "購入": 20, "(未定義)": 30},
    }
    g = ablation_runner._grounding(sc)
    assert g["n"] == 200
    assert g["n_direct"] + g["n_dictionary"] + g["n_undefined"] == 200
    assert g["n_direct"] == 140 and g["n_dictionary"] == 30 and g["n_undefined"] == 30
    assert g["grounded_direct"] == pytest.approx(0.70)
    assert g["grounded_dictionary"] == pytest.approx(0.15)
    assert g["grounded_total"] == pytest.approx(0.85)
    assert g["undefined_rate"] == pytest.approx(0.15)
    assert g["grounded_total"] + g["undefined_rate"] == pytest.approx(1.0)


def test_grounding_matches_score_texts_on_real_texts(ablation_runner, tmp_path):
    """テープの本文から出す道筋が ``c6lib.score_texts`` と同じ分母・分子であること。"""
    from c8lib import c6lib
    from shibuya.llm import format_two_line

    texts = (
        [format_two_line("理由", "移動", "なし", "なし")] * 5      # 24 語に直接一致
        + [format_two_line("理由", "接客", "なし", "なし")] * 2    # 役割語も 24 語のうち
        + [format_two_line("理由", "探索", "なし", "なし")] * 2    # 段0 辞書 → 移動
        + [format_two_line("理由", "空を飛ぶ", "なし", "なし")]     # 未定義
    )
    sc = c6lib.score_texts(texts)
    g = ablation_runner._grounding(sc)
    assert g["n"] == 10
    assert (g["n_direct"], g["n_dictionary"], g["n_undefined"]) == (7, 2, 1)
    assert g["grounded_total"] == pytest.approx(0.9)
    assert g["undefined_rate"] == pytest.approx(sc["undefined_rate"])
    assert g["grounded_dictionary"] == pytest.approx(sc["dictionary_mapped_rate"])


def test_arm_markdown_renders_m1_and_m3(ablation_runner):
    """M1/M3 の節が**列数の揃った** Markdown 表になる(閾値到達語に ★)。"""
    run = {
        "tag": "open", "llm_calls": 10, "calls_per_agent_day": 0.1,
        "format_error_rate": 0.0, "prompt_tokens_mean": 900.0, "notice_reach": 0.0,
        "conserved": True, "final_hash": "h" * 64,
        "grounding": ablation_runner._grounding(
            {"n": 10, "dictionary_mapped": 2, "action_counts": {"移動": 7, "(未定義)": 1}}
        ),
        "undefined_registry": ablation_runner.run_metrics(_Res(), None)["undefined_registry"],
    }
    md = ablation_runner.arm_markdown(
        {"arm": ARM_ID, "index": "⑦", "name": "n", "design_source": "d",
         "switch": {"implemented": True, "how": "h"}, "scale": {}, "route": "mock",
         "notes": [], "runs": [run]}
    )
    assert "## M1 接地率(2 段)・M2 未定義率" in md
    assert "## M3 上位未定義語" in md and "待ち合わせ" in md and "★" in md
    # 表ごとに列数が揃っている(``test_table_markdown_is_a_valid_table`` と同じ物差し)
    block: list[str] = []
    for line in md.splitlines() + [""]:
        if line.startswith("|"):
            block.append(line)
            continue
        if block:
            ncol = block[0].count("|")
            assert all(ln.replace("\\|", "").count("|") == ncol for ln in block), block
            assert len(block) >= 3  # 見出し + 区切り + 1 行以上
            block = []


def test_existing_arm_output_only_gains_columns(ablation_runner, table, tmp_path):
    """既存腕(AB6)の出力 JSON は**列が増えるだけ**で、既存の列の値は動かない。"""
    arm = dict(ablation_runner.arm_by_id(table, "AB6-AD-ZERO"))
    out = ablation_runner.execute_arm(
        arm, agents=16, ticks=2, seed=1, world_dir=None,
        out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
    )
    on, off = out["runs"]
    assert on["tag"] == "signage_on" and off["tag"] == "signage_off"
    # 新しい列(AB7 で足した分)
    assert set(on) >= {"intent_mode", "undefined_registry", "grounding"}
    assert on["intent_mode"] == "vocab" == off["intent_mode"]  # 既定の腕は動いていない
    # 既存の列は AB7 の導入で意味が変わらない: 接地率と既存の未定義率が同じ分母を指す
    assert on["grounding"]["n"] == on["n_texts"]
    assert on["grounding"]["undefined_rate"] == pytest.approx(on["undefined_rate"])
