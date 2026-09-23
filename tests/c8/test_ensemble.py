"""アンサンブル運用(R14 G-4/G-5/G-8)の設計器と面2の計器(純関数)。"""

from __future__ import annotations

import numpy as np
import pytest

SHA = "d41d8cd98f00b204e9800998ecf8427e"


# ------------------------------------------------------------------ G-5 seed 写像
def test_run_seed_is_deterministic(ensemble):
    assert ensemble.run_seed(SHA, 3) == ensemble.run_seed(SHA, 3)


def test_run_seed_differs_by_index_and_manifest(ensemble):
    """『異なる run_index で RNG 状態が衝突しない』(R14 G-5)。"""
    seeds = [ensemble.run_seed(SHA, i) for i in range(64)]
    assert len(set(seeds)) == 64
    assert ensemble.run_seed(SHA, 0) != ensemble.run_seed(SHA[::-1], 0)


def test_run_seed_is_a_positive_63bit_int(ensemble):
    s = ensemble.run_seed(SHA, 7)
    assert 0 <= s < (1 << 63)
    assert isinstance(s, int)


def test_run_seed_rejects_negative_index(ensemble):
    with pytest.raises(ValueError):
        ensemble.run_seed(SHA, -1)


def test_run_seed_feeds_core_rng(ensemble):
    """出た seed が実際に ``core.rng`` の鍵導出に通ること(型の相性)。"""
    from shibuya.core.rng import stream

    a = stream(ensemble.run_seed(SHA, 0), "test.domain")
    b = stream(ensemble.run_seed(SHA, 1), "test.domain")
    assert a is not None and b is not None


# ------------------------------------------------------------------ G-4 EnsembleSpec
def test_spec_varies_only_master_seed(ensemble):
    """決定台帳「アンサンブル=**master_seed のみ変更**」。"""
    spec = ensemble.ensemble_spec(SHA, n_runs=4, agents=1000, ticks=1440)
    assert spec["type"] == "EnsembleSpec"
    assert spec["varies"] == ["master_seed"]
    assert set(spec["fixed"]) == {"agents", "ticks", "world_dir"}
    assert len({r["master_seed"] for r in spec["runs"]}) == 4
    assert all(r["state"] == "queued" and r["attempts"] == 0 for r in spec["runs"])


def test_spec_default_is_eight_runs(ensemble):
    """R14 G-8「初回=seed 群 8 本」(expedient)。"""
    assert ensemble.DEFAULT_N_RUNS == 8
    assert ensemble.ensemble_spec(SHA)["repetitions"] == 8


def test_spec_budget_scales_with_runs(ensemble):
    a = ensemble.ensemble_spec(SHA, n_runs=1, agents=5_000)["budget"]
    b = ensemble.ensemble_spec(SHA, n_runs=8, agents=5_000)["budget"]
    assert b["calls_total"] == 8 * a["calls_total"]
    assert b["gpu_hours_total"] == pytest.approx(8 * a["gpu_hours_per_run"])


def test_spec_flags_w1_overrun(ensemble):
    """1 ラン単体で W1(24 h)を超える規模は open_questions に出る。"""
    big = ensemble.ensemble_spec(SHA, agents=390_067, ticks=1440)
    assert big["budget"]["w1_exceeded"] is True
    assert any("W1" in q for q in big["open_questions"])
    small = ensemble.ensemble_spec(SHA, agents=5_000, ticks=1440)
    assert small["budget"]["w1_exceeded"] is False
    assert not any(q.startswith("**1 ラン") for q in small["open_questions"])


def test_spec_reporters_are_face_scoped(ensemble):
    """reporters は面1/面2 の指標だけ(R14 G-4)。"""
    spec = ensemble.ensemble_spec(SHA, n_runs=2)
    assert spec["reporters"]["face2"] == ["H1", "H2", "H3", "H4", "H5"]
    assert "action_distribution" in spec["reporters"]["face1"]


def test_spec_run_table_has_resume_key(ensemble):
    """G-6「``(manifest_sha256, run_index)`` を主キーとする完了済みラン表」。"""
    spec = ensemble.ensemble_spec(SHA, n_runs=2)
    names = [c["name"] for c in spec["run_table_columns"]]
    assert names[:2] == ["manifest_sha256", "run_index"]
    assert spec["resume"]["key"] == ["manifest_sha256", "run_index"]
    assert "checkpoint_path" in names and "journal_path" in names


def test_spec_face2_gate_is_implausibility(ensemble):
    g = ensemble.ensemble_spec(SHA, n_runs=2)["face2_gate"]
    assert g["limit"] == 3.0 and g["aggregate"] == "I_M = max_i I_i"
    assert g["var_disc_initial"] == 0.0
    assert "片側" in g["one_sided"] or "通っても合格とは言わない" in g["one_sided"]


def test_spec_markdown_tables_well_formed(ensemble):
    md = ensemble.spec_markdown(ensemble.ensemble_spec(SHA, n_runs=3))
    ncol = None
    for line in md.splitlines():
        if not line.startswith("|"):
            ncol = None
            continue
        n = line.replace("\\|", "").count("|")
        ncol = n if ncol is None else ncol
        assert n == ncol, line


# ------------------------------------------------------------------ G-8 計器
def test_crps_of_deterministic_forecast_is_absolute_error(ensemble):
    assert ensemble.crps_ensemble([2.0, 2.0, 2.0], 5.0) == pytest.approx(3.0)


def test_crps_rewards_a_well_placed_spread(ensemble):
    """観測を含む幅の方が、外した決定論予測より CRPS が小さい。"""
    spread = ensemble.crps_ensemble([0.0, 1.0, 2.0], 1.0)
    point = ensemble.crps_ensemble([2.0] * 3, 1.0)
    assert spread < point


def test_crps_empty(ensemble):
    with pytest.raises(ValueError):
        ensemble.crps_ensemble([], 1.0)


def test_spread_skill_ratio_about_one_when_calibrated(ensemble):
    """**観測もメンバーの 1 本**であるとき(完全に信頼できるアンサンブル)比は 1 の近く。

    共通の真値 ``mu`` の周りに観測もメンバーも同じ分布で散る、という置き方をする
    (観測をメンバーの中心に置くと比は sqrt(m) 倍に膨らむ=幅の検査にならない)。
    """
    rng = np.random.default_rng(0)
    mu = rng.normal(size=400)
    truth = mu + rng.normal(size=400)
    members = mu[:, None] + rng.normal(size=(400, 16))
    out = ensemble.spread_skill_ratio(members, truth)
    assert out["n_cases"] == 400 and out["n_members"] == 16
    assert 0.8 < out["ratio"] < 1.2


def test_spread_skill_ratio_detects_underdispersion(ensemble):
    """幅が狭すぎる(自信過剰)アンサンブルは比が 1 を大きく下回る。"""
    rng = np.random.default_rng(1)
    truth = rng.normal(size=200)
    members = truth[:, None] + rng.normal(scale=0.01, size=(200, 8)) + 2.0
    out = ensemble.spread_skill_ratio(members, truth)
    assert out["ratio"] < 0.1


def test_spread_skill_ratio_shape_checks(ensemble):
    with pytest.raises(ValueError):
        ensemble.spread_skill_ratio([[1.0, 2.0]], [1.0, 2.0])
    with pytest.raises(ValueError):
        ensemble.spread_skill_ratio([[1.0]], [1.0])


def test_implausibility(ensemble):
    assert ensemble.implausibility(1.0, 1.0, 0.25) == pytest.approx(0.0)
    assert ensemble.implausibility(2.0, 1.0, 1.0, 0.0, 0.0) == pytest.approx(1.0)
    # 観測誤差とモデル不一致項を足すと I は下がる(G-2 の分母)
    assert ensemble.implausibility(2.0, 1.0, 1.0, 1.0, 2.0) < 1.0
    with pytest.raises(ValueError):
        ensemble.implausibility(1.0, 0.0, 0.0)
