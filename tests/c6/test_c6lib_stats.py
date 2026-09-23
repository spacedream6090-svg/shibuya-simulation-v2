"""``tools/c6/c6lib`` の統計(相関・KS・JSD・帰無参照・ブートストラップ・χ²)。

scipy を使わずに書いたので、**既知解**と**性質**の両方で固定する。
"""

from __future__ import annotations

import math

import numpy as np
import pytest


# ---------------------------------------------------------------- 順位・相関
def test_rankdata_averages_ties(c6lib):
    assert list(c6lib.rankdata([10, 20, 20, 30])) == [1.0, 2.5, 2.5, 4.0]
    assert list(c6lib.rankdata([3, 1, 2])) == [3.0, 1.0, 2.0]


def test_pearson_matches_numpy_and_guards_degenerate_input(c6lib):
    rng = np.random.default_rng(7)
    x = rng.normal(size=200)
    y = 0.4 * x + rng.normal(size=200)
    assert c6lib.pearson(x, y) == pytest.approx(float(np.corrcoef(x, y)[0, 1]), abs=1e-12)
    assert c6lib.pearson([1, 1, 1, 1], [1, 2, 3, 4]) == 0.0  # 分散 0 → 0
    assert c6lib.pearson([1, 2], [1, 2]) == 0.0  # n<3 → 0


def test_spearman_is_one_for_a_monotone_nonlinear_map(c6lib):
    x = np.arange(1, 51, dtype=float)
    assert c6lib.spearman(x, np.exp(x / 10.0)) == pytest.approx(1.0, abs=1e-12)
    assert c6lib.spearman(x, -x) == pytest.approx(-1.0, abs=1e-12)


def test_nan_rows_are_dropped_before_correlating(c6lib):
    x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    y = np.array([np.nan, 1.0, 2.0, 3.0, 4.0])
    assert c6lib.pearson(x, y) == pytest.approx(1.0, abs=1e-12)


# ---------------------------------------------------------------- KS
def test_ks_2samp_is_zero_for_identical_samples(c6lib):
    x = np.arange(100, dtype=float)
    d, p = c6lib.ks_2samp(x, x)
    assert d == 0.0 and p == 1.0


def test_ks_2samp_separates_shifted_distributions(c6lib):
    rng = np.random.default_rng(1)
    a = rng.normal(0, 1, 500)
    b = rng.normal(3, 1, 500)
    d, p = c6lib.ks_2samp(a, b)
    assert d > 0.7 and p < 1e-6
    d2, p2 = c6lib.ks_2samp(a, rng.normal(0, 1, 500))
    assert p2 > 0.05


# ---------------------------------------------------------------- JSD
def test_jsd_is_zero_for_equal_and_one_bit_for_disjoint(c6lib):
    assert c6lib.jsd([1, 1, 1], [2, 2, 2]) == pytest.approx(0.0, abs=1e-12)
    assert c6lib.jsd([1, 0], [0, 1]) == pytest.approx(1.0, abs=1e-12)  # bits


def test_jsd_counts_aligns_missing_keys(c6lib):
    a = {"移動": 10, "待機": 10}
    b = {"移動": 10, "購入": 10}
    assert c6lib.jsd_counts(a, a) == pytest.approx(0.0, abs=1e-12)
    assert 0.0 < c6lib.jsd_counts(a, b) < 1.0
    keys, va, vb = c6lib.align_counts(a, b)
    assert set(keys) == {"待機", "移動", "購入"}
    assert keys == sorted(keys)  # 鍵の並びは決定論(和集合の昇順)
    assert va.sum() == 20 and vb.sum() == 20


def test_null_jsd_reference_brackets_the_observed_value_for_same_distribution(c6lib):
    counts = {"a": 40, "b": 30, "c": 20, "d": 10}
    null = c6lib.null_jsd_reference(counts, 100, 100, reps=300, seed=3)
    assert 0.0 < null["p50"] < null["p95"] < 0.2
    # 同分布から引いた実際の 2 標本は 95%点の下に来やすい
    rng = np.random.default_rng(11)
    p = np.array([40, 30, 20, 10], dtype=float) / 100.0
    hits = sum(
        1
        for _ in range(50)
        if c6lib.jsd(rng.multinomial(100, p), rng.multinomial(100, p)) <= null["p95"]
    )
    assert hits >= 40


# ---------------------------------------------------------------- ブートストラップ・Wilson
def test_bootstrap_mean_ci_contains_the_point_estimate(c6lib):
    diffs = [0] * 90 + [1] * 10
    point, lo, hi = c6lib.bootstrap_mean_ci(diffs, reps=1000, seed=5)
    assert point == pytest.approx(0.10)
    assert lo <= point <= hi and hi - lo < 0.2


def test_bootstrap_is_deterministic_for_a_fixed_seed(c6lib):
    v = [1, 0, 1, 1, 0, 0, 1]
    assert c6lib.bootstrap_mean_ci(v, reps=200, seed=9) == c6lib.bootstrap_mean_ci(
        v, reps=200, seed=9
    )


def test_wilson_ci_known_values(c6lib):
    lo, hi = c6lib.wilson_ci(0, 59)
    assert lo == 0.0 and hi == pytest.approx(0.0613, abs=5e-4)  # B11(n=59・エラー0)
    lo2, hi2 = c6lib.wilson_ci(5, 10)
    assert lo2 < 0.5 < hi2


# ---------------------------------------------------------------- χ²
def test_chi2_sf_matches_textbook_critical_values(c6lib):
    assert c6lib.chi2_sf(3.8415, 1) == pytest.approx(0.05, abs=1e-4)
    assert c6lib.chi2_sf(5.9915, 2) == pytest.approx(0.05, abs=1e-4)
    assert c6lib.chi2_sf(11.0705, 5) == pytest.approx(0.05, abs=1e-4)
    assert c6lib.chi2_sf(0.0, 3) == 1.0


def test_chi2_2sample_detects_a_shifted_categorical(c6lib):
    same = c6lib.chi2_2sample({"a": 50, "b": 50}, {"a": 52, "b": 48})
    assert same["dof"] == 1 and same["p"] > 0.05
    diff = c6lib.chi2_2sample({"a": 90, "b": 10}, {"a": 10, "b": 90})
    assert diff["p"] < 1e-6


def test_chi2_2sample_drops_all_zero_columns(c6lib):
    r = c6lib.chi2_2sample({"a": 10, "b": 10, "z": 0}, {"a": 10, "b": 10})
    assert r["k"] == 2 and r["dof"] == 1


# ---------------------------------------------------------------- 個体別集計・順序バイアス
def test_per_agent_call_stats_counts_and_means(c6lib):
    cnt, mean = c6lib.per_agent_call_stats([(0, 2), (0, 4), (2, 10)], 3)
    assert list(cnt) == [2.0, 0.0, 1.0]
    assert mean[0] == 3.0 and math.isnan(mean[1]) and mean[2] == 10.0


def test_order_bias_report_flags_a_planted_id_bias(c6lib):
    n = 500
    biased = [(i, 0) for i in range(n) for _ in range(1 + i // 100)]
    rep = c6lib.order_bias_report(n, biased)
    assert not rep["ok"] and rep["max_abs_r"] > 0.05
    flat = [(i, i % 24) for i in range(n)]
    rep2 = c6lib.order_bias_report(n, flat)
    assert rep2["rows"]["selected_count"]["pearson"] == 0.0  # 全員 1 回 = 分散 0


# ---------------------------------------------------------------- 層内(実データ用)
def _kind_blocks(sizes: dict[int, int]) -> np.ndarray:
    """W16 と同じ「種別ごとの塊」で並んだ層の配列を作る。"""
    return np.concatenate([np.full(v, k, dtype=np.int64) for k, v in sizes.items()])


def test_stratified_report_separates_composition_from_processing_order(c6lib):
    """**種別構成の差**は層内では消える(W16 の ID が塊で並ぶことへの対処)。

    層 A は 1 体 2 呼・層 B は 1 体 0 呼。ID 順では強い負の相関が出るが、
    層内では ID と呼数が無相関(どの体も同じ回数)。
    """
    strata = _kind_blocks({0: 400, 1: 600})
    n = strata.size
    calls = [(i, 0) for i in range(400) for _ in range(2)]  # 層 0 だけが呼ばれる
    rep = c6lib.stratified_order_bias_report(n, strata, calls, labels={0: "A", 1: "B"})
    assert rep["raw"]["selected_count"]["spearman"] < -0.8  # 生は強い相関
    assert rep["weighted_abs_rho"]["selected_count"] == 0.0  # 層内はゼロ
    assert rep["largest_stratum"]["name"] == "B" and rep["largest_stratum"]["n"] == 600
    assert abs(rep["partial"]["selected_count"]) < 1e-9  # kind を統制すると消える
    assert rep["ok"]


def test_stratified_report_still_catches_a_within_stratum_bias(c6lib):
    """層の中に処理順バイアスを植えたら検出する(層化しても盲目にならない)。"""
    strata = _kind_blocks({0: 500, 1: 500})
    n = strata.size
    calls = [(i, 0) for i in range(n) for _ in range(1 + (i % 500) // 100)]
    rep = c6lib.stratified_order_bias_report(n, strata, calls, labels={0: "A", 1: "B"})
    assert rep["weighted_abs_rho"]["selected_count"] > 0.05
    assert abs(rep["largest_stratum"]["selected_count"]) > 0.05
    assert not rep["ok"]


def test_stratified_report_reports_per_stratum_size_and_calls(c6lib):
    strata = _kind_blocks({7: 3, 9: 2})
    rep = c6lib.stratified_order_bias_report(
        5, strata, [(0, 1), (0, 3), (4, 2)], labels={7: "七", 9: "九"}
    )
    assert rep["strata"]["七"]["n"] == 3 and rep["strata"]["七"]["n_calls"] == 2.0
    assert rep["strata"]["九"]["n"] == 2 and rep["strata"]["九"]["n_calls"] == 1.0
    assert rep["metrics"] == ["mean_wake_tick", "selected_count"]
    assert rep["n_reports"] == 1


def test_stratified_report_rejects_a_mismatched_strata_length(c6lib):
    with pytest.raises(ValueError, match="strata"):
        c6lib.stratified_order_bias_report(10, [0, 1, 2], [(0, 0)])


def test_weights_are_call_counts_not_head_counts(c6lib):
    """加重平均の重みは**呼数**(呼がほぼ 0 の層に平均を薄めさせない・親指示 09-09)。

    大きいが呼ばれない層 B(ρ=0)と、小さいが呼ばれる層 A(ρ が立つ)を並べる。
    体数重みなら平均は薄まるが、呼数重みなら A の値がそのまま出る。
    """
    strata = _kind_blocks({0: 100, 1: 900})
    n = strata.size
    calls = [(i, 0) for i in range(100) for _ in range(1 + i // 25)]  # 層 A だけ・ID 順バイアス
    rep = c6lib.stratified_order_bias_report(n, strata, calls, labels={0: "A", 1: "B"})
    assert rep["strata"]["B"]["w_selected_count"] == 0.0
    assert rep["weights"]["selected_count"] == float(len(calls))
    rho_a = abs(rep["strata"]["A"]["selected_count"])
    assert rep["weighted_abs_rho"]["selected_count"] == pytest.approx(rho_a, abs=1e-12)
    # 体数重みだったら 100/1000 に薄まっていた
    assert rho_a * 0.1 < rep["weighted_abs_rho"]["selected_count"]


def test_gate_fails_on_the_partial_correlation_alone(c6lib):
    """層ごとの ρ が小さくても、**全層に同じ向き**で乗るバイアスは部分相関が捕まえる。

    各層の中で「若い ID ほど呼ばれる」を弱く仕込むと、層内 ρ は閾値近くでも
    kind を統制した部分相関が 0.05 を超えて主判定が落ちる。
    """
    strata = _kind_blocks({0: 1_000, 1: 1_000})
    n = strata.size
    rng = np.random.default_rng(5)
    calls: list[tuple[int, int]] = []
    for i in range(n):
        within = i % 1_000
        p = 0.60 - 0.20 * (within / 999.0)  # 層内で単調に減る = 同じ向きのバイアス
        if rng.random() < p:
            calls.append((i, 0))
    rep = c6lib.stratified_order_bias_report(n, strata, calls, labels={0: "A", 1: "B"})
    assert abs(rep["partial"]["selected_count"]) > 0.05
    assert not rep["ok"]


def test_reversal_symmetry_accepts_a_sign_flip_and_rejects_a_persistent_bias(c6lib):
    """副判定 ``|ρ_順 + ρ_逆| ≤ 0.05``。"""
    def fake(rho_sel: float, rho_tick: float) -> dict:
        return {
            "metrics": ["mean_wake_tick", "selected_count"],
            "raw": {
                "mean_wake_tick": {"spearman": rho_tick, "pearson": rho_tick},
                "selected_count": {"spearman": rho_sel, "pearson": rho_sel},
            },
        }

    flipped = c6lib.reversal_symmetry(fake(-0.1243, 0.0300), fake(0.1434, -0.0066))
    assert flipped["ok"] and flipped["max_residual"] == pytest.approx(0.0234, abs=1e-3)
    persistent = c6lib.reversal_symmetry(fake(-0.12, 0.0), fake(-0.12, 0.0))
    assert not persistent["ok"]  # 反転しても同じ向き = 処理順のバイアス
    assert persistent["rows"]["selected_count"]["residual"] == pytest.approx(0.24)


def test_average_stratified_reports_shrinks_the_sampling_noise(c6lib):
    """seed ごとに符号が飛ぶ ρ は平均するとゼロへ寄る(閾値を当てるのは平均側)。"""
    strata = _kind_blocks({0: 200, 1: 200})
    n = strata.size
    rng = np.random.default_rng(3)
    reports = []
    for _ in range(9):
        calls = [(int(i), 0) for i in rng.choice(n, size=120, replace=False)]
        reports.append(c6lib.stratified_order_bias_report(n, strata, calls))
    singles = [abs(r["largest_stratum"]["selected_count"]) for r in reports]
    avg = c6lib.average_stratified_reports(reports)
    assert avg["n_reports"] == 9
    assert abs(avg["largest_stratum"]["selected_count"]) < max(singles)
    assert avg["strata"].keys() == reports[0]["strata"].keys()


def test_average_stratified_reports_keeps_a_real_bias(c6lib):
    """本物のバイアスは平均しても残る(平均が甘くならない)。"""
    strata = _kind_blocks({0: 500, 1: 500})
    n = strata.size
    calls = [(i, 0) for i in range(n) for _ in range(1 + (i % 500) // 100)]
    reports = [c6lib.stratified_order_bias_report(n, strata, calls) for _ in range(3)]
    avg = c6lib.average_stratified_reports(reports)
    assert not avg["ok"]
    assert avg["largest_stratum"]["selected_count"] == pytest.approx(
        reports[0]["largest_stratum"]["selected_count"], abs=1e-9
    )


def test_average_stratified_reports_refuses_mismatched_strata(c6lib):
    a = c6lib.stratified_order_bias_report(4, [0, 0, 1, 1], [(0, 0)])
    b = c6lib.stratified_order_bias_report(4, [0, 0, 0, 2], [(0, 0)])
    with pytest.raises(ValueError, match="揃っていない"):
        c6lib.average_stratified_reports([a, b])
    with pytest.raises(ValueError, match="空"):
        c6lib.average_stratified_reports([])
