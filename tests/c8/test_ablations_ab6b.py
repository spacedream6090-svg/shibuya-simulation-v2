"""腕 ``AB6b-AD-NOTICE``(看板の注視ゲート較正)の腕定義行 — D-59 (b)(ユーザー決定 2026-09-17)。

出典
    PENDING D-59 (b)「注意ゲートの較正(広告への注視確率を実測帯 0.14-0.79 の下側へ)を
    C8 内で 1 回」+ 知覚契約書 §4 段1(p_see)・§3.2(B2.signage 25 tok)・§8 第1陣 ⑥。

見るもの
(d1) ``ablations_v1.json`` の**末尾**に AB6b が足され(rank 10・index ⑥b)、切替口つきで ready /
(d2) **既存 9 腕の定義はバイト不変**(``tests/c8/test_ablations_ab7.py`` の FROZEN が正典)/
(d3) ``runs`` が 4 本(baseline 1.0 / ad_zero / 0.30 / 0.14)で許可リストを通る・
     指標は ⑥ と**同じ 5 本** /
(d4) ``kwargs`` が ``cli.run`` → ``run_day`` → run manifest まで往復し、**mock では
     checkpoint が動かない**(プロンプト本文しか変えない腕)/
(d5) 予算の通算(totals)が算術と一致し、L2 を超えるなら note に宣言されている。
"""

from __future__ import annotations

import hashlib
import json

import pytest

ARM_ID = "AB6b-AD-NOTICE"
#: ⑥(広告ゼロ)= この腕の親。**同じ指標で比べる**ことを機械で守るための参照。
AD_ZERO_ID = "AB6-AD-ZERO"
#: 腕が回す較正値(実測帯 0.14-0.79 の下側・知覚契約書 §4 段1 の中小媒体帯 0.14-0.40 の内側)。
ARM_P_SEE = (1.0, 0.3, 0.14)


@pytest.fixture(scope="module")
def table(c8lib):
    return c8lib.load_ablations()


def _canonical_sha256(arm) -> str:
    return hashlib.sha256(
        json.dumps(arm, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------- (d1) 腕定義表
def test_ab6b_is_the_last_arm_with_rank_10(ablation_runner, table):
    """2026-09-19: AB6b の**後ろに** AB8(L4 の感度)と AB6c(⑥b の無制限版)を足した。

    腕そのものは rank 10・index ⑥b のまま(定義はバイト不変=``test_ablations_ab8`` の
    FROZEN が見る)。ここが見るのは「AB6b の位置が動いていないこと」に変わった。
    """
    arm = ablation_runner.arm_by_id(table, ARM_ID)
    assert arm["rank"] == 10 and arm["index"] == "⑥b"
    ids = [a["id"] for a in table["arms"]]
    # 2026-09-22: さらに AB7d(語彙の無制限版)・AB1b(固定枠の無制限版)が末尾に付いた
    assert ids[-5:] == [ARM_ID, "AB8-L4-SCALE", "AB6c-AD-NOTICE-UNCAPPED", "AB7d-VOCAB-UNCAPPED", "AB1b-BUDGET-MODE-UNCAPPED"]
    assert ARM_ID not in ablation_runner.first_wave_ids(table), "第1陣は 6 本のまま"
    assert arm["design_source"].startswith("PENDING D-59 (b)")
    assert arm["status"] == "ready"
    assert ablation_runner.validate_table(table) == []


def test_ab6_still_resolves_by_exact_match(ablation_runner, table):
    """``AB6`` の前方一致が 2 本に当たるようになったが、**完全一致が優先**される。"""
    assert ablation_runner.arm_by_id(table, AD_ZERO_ID)["rank"] == 6
    assert ablation_runner.arm_by_id(table, "ab6b")["id"] == ARM_ID
    assert ablation_runner.arm_by_id(table, "⑥b")["id"] == ARM_ID
    assert ablation_runner.arm_by_id(table, "⑥")["id"] == AD_ZERO_ID


# ---------------------------------------------------------------- (d3) 切替口とラン
def test_ab6b_switch(ablation_runner, table):
    sw = ablation_runner.arm_by_id(table, ARM_ID)["switch"]
    assert sw["kind"] == "implemented_flag" and sw["implemented"] is True
    assert "--signage-p-see" in sw["how"]
    assert sw["mock_effective"] is False, "MockLLM はプロンプトを読まない=mock では差が出ない"
    assert "perception.attention.p_see" in sw["verified"]
    assert "(tick, agent_id, poi_id)" in sw["verified"]


def test_ab6b_runs_are_the_four_arms(ablation_runner, table):
    arm = ablation_runner.arm_by_id(table, ARM_ID)
    assert [r["tag"] for r in arm["runs"]] == [
        "p_see_1_00", "ad_zero", "p_see_0_30", "p_see_0_14",
    ]
    assert [r["kwargs"] for r in arm["runs"]] == [
        {"signage_p_see": 1.0},
        {"signage": False},
        {"signage_p_see": 0.3},
        {"signage_p_see": 0.14},
    ]
    assert arm["runs"][0]["is_baseline"] is True
    for r in arm["runs"][1:]:
        assert "is_baseline" not in r
    for r in arm["runs"]:
        assert set(r["kwargs"]) <= ablation_runner.ALLOWED_KWARGS
        assert not (set(r["kwargs"]) & ablation_runner.PENDING_KWARGS)
    # 較正値は帯の下側(0.30 / 0.14)。baseline は現行の 1.0。
    got = tuple(
        r["kwargs"].get("signage_p_see") for r in arm["runs"] if "signage_p_see" in r["kwargs"]
    )
    assert got == ARM_P_SEE


def test_signage_p_see_is_on_the_allow_list(ablation_runner):
    assert "signage_p_see" in ablation_runner.ALLOWED_KWARGS


def test_ab6b_uses_the_same_metrics_as_ad_zero(ablation_runner, table):
    """比較指標は ⑥ と**同じ**(腕をまたいで同じ物差しで読むため)。"""
    a = ablation_runner.arm_by_id(table, ARM_ID)
    b = ablation_runner.arm_by_id(table, AD_ZERO_ID)
    assert a["metrics"] == b["metrics"]
    for m in a["metrics"]:
        assert m in table["metrics"]


def test_ab6b_declares_the_ad_zero_arm_inside_itself(ablation_runner, table):
    """``ad_zero`` ランは ⑥ の ``signage_off`` と**同一構成**(共有できる=note に宣言)。"""
    a = ablation_runner.arm_by_id(table, ARM_ID)
    b = ablation_runner.arm_by_id(table, AD_ZERO_ID)
    ad_zero = next(r for r in a["runs"] if r["tag"] == "ad_zero")
    signage_off = next(r for r in b["runs"] if r["tag"] == "signage_off")
    assert ad_zero["kwargs"] == signage_off["kwargs"]
    assert "signage_off" in a["cost"]["note"] or "同一構成" in table["totals"]["note"]


# ---------------------------------------------------------------- (d2) 既存腕の不変
def test_the_ad_zero_arm_is_untouched(table):
    """⑥ の腕定義は 1 バイトも動かない(golden は AB7 のテストが持つ値)。"""
    from tests.c8.test_ablations_ab7 import FROZEN_ARM_SHA256

    arm = next(a for a in table["arms"] if a["id"] == AD_ZERO_ID)
    assert _canonical_sha256(arm) == FROZEN_ARM_SHA256[AD_ZERO_ID]


# ---------------------------------------------------------------- (d4) kwargs の往復
def test_ab6b_kwargs_reach_run_day(ablation_runner, table, tmp_path):
    """腕定義の ``kwargs`` が ``cli.run`` → ``run_day`` → manifest まで通る(mock・極小)。"""
    arm = dict(ablation_runner.arm_by_id(table, ARM_ID))
    out = ablation_runner.execute_arm(
        arm, agents=16, ticks=2, seed=1, world_dir=None,
        out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
    )
    assert out["executed"] is True
    assert [r["tag"] for r in out["runs"]] == [
        "p_see_1_00", "ad_zero", "p_see_0_30", "p_see_0_14",
    ]
    fields = [r["run_manifest_fields"] for r in out["runs"]]
    assert [f["signage_p_see"] for f in fields] == [1.0, 1.0, 0.3, 0.14]
    assert [f["signage"] for f in fields] == [True, False, True, True]
    assert [r["signage_p_see"] for r in out["runs"]] == [1.0, 1.0, 0.3, 0.14]
    # mock では本文を読まないので checkpoint は動かない(=腕の差は実 LLM でしか出ない)
    assert all(c["identical_final_hash"] for c in out["comparisons"])
    assert any("実 LLM 必須" in n for n in out["notes"])
    # baseline との差の欄(p_see の差そのもの)が出る
    assert [c["d_signage_p_see"] for c in out["comparisons"]] == [0.0, -0.7, -0.86]


def test_the_markdown_carries_the_gate_section(ablation_runner, table, tmp_path):
    """``arm_markdown`` に ``signage_p_see`` の節が出る(看板の腕だけ)。"""
    arm = dict(ablation_runner.arm_by_id(table, ARM_ID))
    out = ablation_runner.execute_arm(
        arm, agents=16, ticks=2, seed=1, world_dir=None,
        out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
    )
    md = ablation_runner.arm_markdown(out)
    assert "看板の注視ゲート" in md
    assert "p_see" in md
    # Markdown の表は**1 つの表の中で**列数が揃っていること(表ごとに列数は違ってよい)
    block: list[str] = []
    blocks: list[list[str]] = []
    for ln in md.splitlines():
        if ln.startswith("|"):
            block.append(ln)
        elif block:
            blocks.append(block)
            block = []
    if block:
        blocks.append(block)
    assert len(blocks) >= 2, "実測表と注視ゲート表の 2 つは出るはず"
    for b in blocks:
        ncol = {ln.replace("\\|", "").count("|") for ln in b}
        assert len(ncol) == 1, (ncol, b[0])


def test_other_arms_keep_their_markdown(ablation_runner, table, tmp_path):
    """**看板を触らない腕の Markdown には節が出ない**(列追加のみの規律)。"""
    arm = dict(ablation_runner.arm_by_id(table, "AB7-OPEN-INTENT"))
    out = ablation_runner.execute_arm(
        arm, agents=16, ticks=2, seed=1, world_dir=None,
        out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
    )
    assert "看板の注視ゲート" not in ablation_runner.arm_markdown(out)


# ---------------------------------------------------------------- (d5) 予算の通算
def test_the_cost_and_totals_are_arithmetic(c8lib, table, ablation_runner):
    arm = ablation_runner.arm_by_id(table, ARM_ID)
    c = arm["cost"]
    assert c["runs"] == 4 and c["calls"] == 200_000
    assert c["calls_with_shared_baseline"] == 150_000
    assert c["gpu_hours"] == pytest.approx(c8lib.gpu_hours_for_calls(c["calls"]), abs=1e-3)
    assert c["gpu_hours_with_shared_baseline"] == pytest.approx(
        c8lib.gpu_hours_for_calls(c["calls_with_shared_baseline"]), abs=1e-3
    )
    t = table["totals"]
    assert t["runs_if_independent"] == sum(a["cost"]["runs"] for a in table["arms"])
    assert t["within_l2"] is (
        t["gpu_hours_with_shared_baseline"] <= t["l2_reserve_hours"]
    )
    if not t["within_l2"]:
        assert "L2" in t["note"], "超過は totals.note に宣言する(黙って飲み込まない)"


def test_the_open_question_declares_the_expedients(table):
    """0.30/0.14 の選び方と規約⑧ の但し書きを**親判断待ちとして残す**(黙って決めない)。"""
    qs = [q for q in table["open_questions"] if ARM_ID in q]
    assert len(qs) == 1
    assert "expedient" in qs[0] and "⑧" in qs[0]
