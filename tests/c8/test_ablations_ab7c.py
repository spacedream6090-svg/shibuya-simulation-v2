"""腕 ``AB7c-VOCAB-V2``(語彙 v1 vs 語彙 v2)の腕定義行 — D-71 §3(2026-09-17 ユーザー決定)。

見るもの
(d1) ``ablations_v1.json`` の**末尾**に AB7c が足され(rank 9)、切替口つきで ready /
(d2) **既存 8 腕の定義はバイト不変**(``tests/c8/test_ablations_ab7.py`` の FROZEN が正典)/
(d3) ``runs`` の ``kwargs`` が ``intent_mode`` × ``vocab_version`` の 3 本で許可リストを通る/
(d4) ``kwargs`` が ``cli.run`` → ``run_day`` → run manifest まで往復し、**mock でも差が出る**
     (``mock_effective: true``=MockLLM の抽選語彙が版に従う)。
(d5) 予算の通算(totals)が算術と一致し、L2 を超えるなら note に宣言されている。
"""

from __future__ import annotations

import hashlib
import json

import pytest

ARM_ID = "AB7c-VOCAB-V2"

#: 腕定義のカノニカル JSON SHA256(2026-09-17 に凍結。**文面を変えたら必ずここが動く**)。
FROZEN_AB7C_SHA256 = "f5cd4a8a84172d379f84e03a3e7e0095847530b90558c3322635ffe0326b66b0"


@pytest.fixture(scope="module")
def table(c8lib):
    return c8lib.load_ablations()


def _canonical_sha256(arm) -> str:
    return hashlib.sha256(
        json.dumps(arm, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------- (d1)(d2) 腕定義表
def test_ab7c_is_the_last_arm_with_rank_9(ablation_runner, table):
    arm = ablation_runner.arm_by_id(table, ARM_ID)
    assert arm["rank"] == 9 and arm["index"] == "⑦c"
    assert table["arms"][-1]["id"] == ARM_ID
    assert ARM_ID not in ablation_runner.first_wave_ids(table), "第1陣は 6 本のまま"
    assert arm["design_source"].startswith("docs/design/v2-vocab-growth-design.md")
    assert arm["status"] == "ready"
    assert ablation_runner.validate_table(table) == []


def test_the_arm_definition_is_frozen(ablation_runner, table):
    assert _canonical_sha256(ablation_runner.arm_by_id(table, ARM_ID)) == FROZEN_AB7C_SHA256


# ---------------------------------------------------------------- (d3) 切替口と ラン
def test_ab7c_switch_and_runs(ablation_runner, table):
    arm = ablation_runner.arm_by_id(table, ARM_ID)
    sw = arm["switch"]
    assert sw["kind"] == "implemented_flag" and sw["implemented"] is True
    assert "--vocab-version" in sw["how"]
    assert sw["mock_effective"] is True, "mock の抽選語彙が版に従う=mock でも差が出る"
    assert [r["tag"] for r in arm["runs"]] == ["vocab_v1", "vocab_v2", "open_v2"]
    assert [r["kwargs"] for r in arm["runs"]] == [
        {"intent_mode": "vocab", "vocab_version": "v1"},
        {"intent_mode": "vocab", "vocab_version": "v2"},
        {"intent_mode": "open", "vocab_version": "v2"},
    ]
    assert arm["runs"][0]["is_baseline"] is True
    for r in arm["runs"][1:]:
        assert "is_baseline" not in r
    for r in arm["runs"]:
        assert set(r["kwargs"]) <= ablation_runner.ALLOWED_KWARGS
        assert not (set(r["kwargs"]) & ablation_runner.PENDING_KWARGS)


def test_vocab_version_is_on_the_allow_list(ablation_runner):
    assert "vocab_version" in ablation_runner.ALLOWED_KWARGS


# ---------------------------------------------------------------- (d4) kwargs の往復
def test_ab7c_kwargs_reach_run_day(ablation_runner, table, tmp_path):
    """腕定義の ``kwargs`` が ``cli.run`` → ``run_day`` までそのまま通る(mock・極小)。"""
    arm = dict(ablation_runner.arm_by_id(table, ARM_ID))
    out = ablation_runner.execute_arm(
        arm, agents=16, ticks=2, seed=1, world_dir=None,
        out_dir=tmp_path, fleet=None, tape_root=tmp_path / "t",
    )
    assert out["executed"] is True
    assert [r["tag"] for r in out["runs"]] == ["vocab_v1", "vocab_v2", "open_v2"]
    assert [r["vocab_version"] for r in out["runs"]] == ["v1", "v2", "v2"]
    assert [r["intent_mode"] for r in out["runs"]] == ["vocab", "vocab", "open"]
    fields = [r["run_manifest_fields"] for r in out["runs"]]
    assert [f["vocab_version"] for f in fields] == ["v1", "v2", "v2"]
    assert [f["synonym_table_version"] for f in fields] == [
        "undefined-synonyms-v2", "undefined-synonyms-v4", "undefined-synonyms-v4",
    ]
    for r in out["runs"]:
        assert "action_usage" in r and "meals" in r


# ---------------------------------------------------------------- (d5) 予算の通算
def test_the_totals_declare_the_l2_overrun(c8lib, table):
    t = table["totals"]
    assert t["gpu_hours_with_shared_baseline"] == pytest.approx(
        c8lib.gpu_hours_for_calls(t["calls_with_shared_baseline"]), abs=1e-3
    )
    assert t["within_l2"] is (
        t["gpu_hours_with_shared_baseline"] <= t["l2_reserve_hours"]
    )
    if not t["within_l2"]:
        assert "L2" in t["note"], "超過は totals.note に宣言する(黙って飲み込まない)"
