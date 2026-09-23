# -*- coding: utf-8 -*-
"""事前登録 **v1.3**(seed アンサンブル判定)の検収。**本物の holdout も本物の occupancy も読まない**。

検査するもの
- 同値検定の 3 値(全部内側=pass / 線をまたぐ=undecided / 全部外側=fail)
- 家族 95% の半幅 = t(0.995, 2)·SD/√3(5 指標 Bonferroni・α=0.01/指標)
- 「この SD で undecided を解くのに要る seed 数」
- H3 の格下げ(``n_measured`` に数えない)と H1 の昼窓(6〜23 時)
- GET 包絡が「**検定ではない**」と report に出ること
- fair CRPS の第 2 項比 = M/(M−1)
- **既定(v1.2・1 ラン)の report と結果 dict が従来と完全一致**
- CLI の版と本数の整合(v1.3 で occupancy 1 本 → 明示エラー)
"""

from __future__ import annotations

import copy
import math

import numpy as np
import pytest

T995_DF2 = 9.925  # t(0.995, 2)(seed_ensemble の表)


@pytest.fixture(scope="session")
def v13():
    import prereg_v13 as _m  # tests/c7/conftest.py が tools/c7 を sys.path に入れている

    return _m


# ---------------------------------------------------------------- 合成の five_metrics 結果


def _limits(c7lib, metric: str) -> dict:
    """``five_metrics`` が各指標に入れる ``limit`` 辞書と同じ形(鍵名まで同じ)。"""
    pr = c7lib.PREREG_V0
    if metric == "H1":
        return {"jsd_mean_max": pr["H1"]["jsd_area_hour_mean_max"],
                "pearson_min": pr["H1"]["pearson_min"]}
    if metric == "H2":
        return {k: pr["H2"][k] for k in ("abs_hour_diff_max", "n_within_min", "tau_min")}
    if metric == "H3":
        return {k: pr["H3"][k] for k in ("abs_diff_max", "tau_min")}
    if metric == "H4":
        return {k: pr["H4"][k] for k in ("jsd_max", "abs_share_diff_max")}
    return {k: pr["H5"][k] for k in ("jsd_mean_max", "abs_share_diff_max")}


_DEFAULTS = {
    "H1": {"jsd_mean": 0.0010, "pearson_r": 0.95},
    "H2": {"n_within": 5, "kendall_tau": 1.0},
    "H3": {"abs_diff_max": 0.010, "kendall_tau": 0.90},
    "H4": {"jsd": 0.0010, "abs_share_diff_max": 0.010},
    "H5": {"jsd_mean": 0.0050, "abs_share_diff_max": 0.020},
}


def _fake_result(c7lib, **over) -> dict:
    """``c7lib.five_metrics`` と同じ形の合成結果(``over`` は ``H4={"jsd": ...}`` の形)。"""
    res: dict = {}
    for m in ("H1", "H2", "H3", "H4", "H5"):
        vals = dict(_DEFAULTS[m])
        vals.update(over.get(m, {}))
        res[m] = {"name": c7lib.PREREG_V0[m]["name"], "measured": True, "pass": True,
                  "limit": _limits(c7lib, m), **vals}
    res["prereg"] = c7lib.PREREG_V0
    res["n_measured"] = 5
    res["n_pass"] = 5
    res["pass"] = True
    return res


def _seeds(c7lib, per_seed_over: list[dict]) -> list[dict]:
    return [_fake_result(c7lib, **o) for o in per_seed_over]


# ---------------------------------------------------------------- (a) 全部内側 → pass


def test_a_all_inside_with_small_sd_passes(v13, c7lib):
    seeds = _seeds(c7lib, [
        {"H4": {"jsd": 0.0010}}, {"H4": {"jsd": 0.0011}}, {"H4": {"jsd": 0.0012}}])
    got = v13.ensemble_verdict(seeds)
    assert got["n_seeds"] == 3
    assert got["n_measured"] == 4              # H3 は判定対象外
    assert got["n_pass"] == 4 and got["n_undecided"] == 0 and got["n_fail"] == 0
    assert got["pass"] is True
    for m in ("H1", "H2", "H4", "H5"):
        assert got["metrics"][m]["verdict"] == "pass", (m, got["metrics"][m])


# ---------------------------------------------------------------- (b) 線の近く+SD 大 → undecided


#: 平均 0.0112・SD(ddof=1) 0.0004・線 0.0122 → 距離 0.0010・距離/SD = 2.5。
#: n=3 は 9.925/√3=5.73 で足りず、n=4 は 5.841/2=2.92 でも足りず、n=5 で 4.604/√5=2.06 ≤ 2.5。
_NEAR_LINE = [0.0108, 0.0112, 0.0116]


def test_b_near_the_line_with_large_sd_is_undecided_and_needs_more_seeds(v13, c7lib):
    seeds = _seeds(c7lib, [{"H4": {"jsd": v}} for v in _NEAR_LINE])
    got = v13.ensemble_verdict(seeds)
    st = got["metrics"]["H4"]["stats"]["jsd"]
    assert st["verdict"] == "undecided"
    assert got["metrics"]["H4"]["verdict"] == "undecided"
    assert got["pass"] is False
    assert got["n_undecided"] == 1 and got["n_pass"] == 3
    # 「この SD で undecided を解くのに要る seed 数」は 3 より大きい
    assert st["n_needed"] is not None and st["n_needed"] > 3
    assert st["n_needed"] == 5
    # 区間が線をまたいでいる(= 検出力不足であって不合格ではない)
    lo, hi = st["interval"]
    assert lo < 0.0122 < hi
    assert st["alpha_per_metric"] == pytest.approx(0.01)


def test_b_unsolvable_when_the_mean_sits_on_the_line(v13, c7lib):
    """平均が線ちょうど=距離 0 は seed をいくら足しても解けない(None)。"""
    seeds = _seeds(c7lib, [{"H4": {"jsd": v}} for v in (0.0112, 0.0122, 0.0132)])
    st = v13.ensemble_verdict(seeds)["metrics"]["H4"]["stats"]["jsd"]
    assert st["verdict"] == "undecided" and st["n_needed"] is None


# ---------------------------------------------------------------- (c) 全部外側 → fail


def test_c_all_outside_fails(v13, c7lib):
    seeds = _seeds(c7lib, [{"H4": {"jsd": v}} for v in (0.050, 0.051, 0.052)])
    got = v13.ensemble_verdict(seeds)
    st = got["metrics"]["H4"]["stats"]["jsd"]
    assert st["verdict"] == "fail" and st["interval"][0] > 0.0122
    assert got["metrics"]["H4"]["verdict"] == "fail"
    assert got["n_fail"] == 1 and got["pass"] is False


def test_c_lower_bound_line_fails_when_entirely_below(v13, c7lib):
    """下限の線(Pearson r ≥ 0.80)は区間が全部下なら fail。"""
    seeds = _seeds(c7lib, [{"H1": {"pearson_r": v}} for v in (0.40, 0.41, 0.42)])
    got = v13.ensemble_verdict(seeds)
    assert got["metrics"]["H1"]["stats"]["pearson_r"]["verdict"] == "fail"
    assert got["metrics"]["H1"]["verdict"] == "fail"


def test_c_fail_beats_undecided_inside_one_metric(v13, c7lib):
    """1 統計量が fail・もう 1 つが undecided なら指標は fail(1 ラン版の AND と同じ向き)。"""
    seeds = _seeds(c7lib, [
        {"H4": {"jsd": a, "abs_share_diff_max": b}}
        for a, b in zip((0.050, 0.051, 0.052), _NEAR_LINE)])
    got = v13.ensemble_verdict(seeds)
    stats = got["metrics"]["H4"]["stats"]
    assert stats["jsd"]["verdict"] == "fail"
    assert stats["abs_share_diff_max"]["verdict"] == "pass"  # 線は 0.05 なので内側
    assert got["metrics"]["H4"]["verdict"] == "fail"


# ---------------------------------------------------------------- (d) H3 の格下げ


def test_d_h3_is_descriptive_and_not_counted(v13, c7lib):
    # H3 を派手に落としても総合は変わらない(=判定に使っていない)
    seeds = _seeds(c7lib, [{"H3": {"abs_diff_max": 9.9, "kendall_tau": -1.0}}] * 3)
    got = v13.ensemble_verdict(seeds)
    assert "H3" not in got["judged_metrics"]
    assert got["descriptive_metrics"] == ["H3"]
    assert got["metrics"]["H3"]["judged"] is False
    assert "深夜" in got["metrics"]["H3"]["demoted_reason"]
    assert got["n_measured"] == 4           # H3 を数えない
    assert got["n_pass"] == 4 and got["pass"] is True
    # 記述としては計算されている(値と参考判定は残る)
    assert got["metrics"]["H3"]["stats"]["abs_diff_max"]["verdict"] == "fail"
    # Bonferroni の分母は 5 のまま(事前登録の家族を事後に縮めない)
    assert got["family"]["size"] == 5
    assert got["family"]["alpha_family"] == pytest.approx(0.05)


# ---------------------------------------------------------------- (e) 家族 95% の半幅


def test_e_family95_half_width_matches_t995_df2(v13, c7lib):
    seeds = _seeds(c7lib, [{"H4": {"jsd": v}} for v in _NEAR_LINE])
    st = v13.ensemble_verdict(seeds)["metrics"]["H4"]["stats"]["jsd"]
    sd = float(np.std(_NEAR_LINE, ddof=1))
    assert st["sd_ddof1"] == pytest.approx(sd)
    assert st["half_width"] == pytest.approx(T995_DF2 * sd / math.sqrt(3.0), rel=1e-9)
    assert st["interval"] == pytest.approx([st["mean"] - st["half_width"],
                                            st["mean"] + st["half_width"]])
    assert st["interval_kind"] == "family95_t"
    assert st["t_quantile"] == pytest.approx(T995_DF2, rel=1e-3)
    assert v13.family_half_width(sd, 3) == pytest.approx(T995_DF2 * sd / math.sqrt(3.0))


def test_e_alpha_other_than_001_is_refused(v13):
    with pytest.raises(ValueError, match="0.01"):
        v13.family_half_width(0.1, 3, alpha_per_metric=0.05)


def test_e_integer_statistic_uses_min_max(v13, c7lib):
    """H2 の ``n_within`` は整数なので区間は seed ごとの最小/最大。"""
    seeds = _seeds(c7lib, [{"H2": {"n_within": n}} for n in (4, 5, 5)])
    st = v13.ensemble_verdict(seeds)["metrics"]["H2"]["stats"]["n_within"]
    assert st["interval_kind"] == "min_max"
    assert st["interval"] == [4.0, 5.0]
    assert st["half_width"] is None
    assert st["verdict"] == "undecided"     # 線 5 をまたぐ
    assert "最小/最大" in st["interval_note"]


def test_e_undefined_tau_is_failed_not_hidden(v13, c7lib):
    """τ-b が 1 本でも未定義なら fail に倒し、理由を残す(推測で埋めない)。"""
    seeds = _seeds(c7lib, [{"H2": {"kendall_tau": 1.0}}, {"H2": {"kendall_tau": None}},
                           {"H2": {"kendall_tau": 1.0}}])
    st = v13.ensemble_verdict(seeds)["metrics"]["H2"]["stats"]["kendall_tau"]
    assert st["verdict"] == "fail" and "未定義" in st["reason"]
    assert "mean" not in st


def test_e_unmeasured_metric_is_not_counted(v13, c7lib):
    seeds = _seeds(c7lib, [{}] * 3)
    for r in seeds:
        r["H5"] = {"name": "属性構成", "measured": False, "pass": None,
                   "reason": "ラン側または holdout 側の属性構成が未供給"}
    got = v13.ensemble_verdict(seeds)
    assert got["metrics"]["H5"]["measured"] is False
    assert got["metrics"]["H5"]["verdict"] is None
    assert got["n_measured"] == 3


def test_e_mixed_lines_across_seeds_raise(v13, c7lib):
    seeds = _seeds(c7lib, [{}] * 3)
    seeds[1]["H4"]["limit"] = {"jsd_max": 0.9, "abs_share_diff_max": 0.05}
    with pytest.raises(ValueError, match="prereg が混ざっている"):
        v13.ensemble_verdict(seeds)


def test_e_one_seed_is_refused(v13, c7lib):
    with pytest.raises(ValueError, match="2 本以上"):
        v13.ensemble_verdict(_seeds(c7lib, [{}]))


def test_interval_verdict_three_values(v13):
    assert v13.interval_verdict(0.1, 0.2, upper=0.3) == "pass"
    assert v13.interval_verdict(0.4, 0.5, upper=0.3) == "fail"
    assert v13.interval_verdict(0.2, 0.4, upper=0.3) == "undecided"
    assert v13.interval_verdict(0.9, 1.0, lower=0.8) == "pass"
    assert v13.interval_verdict(0.1, 0.2, lower=0.8) == "fail"
    assert v13.interval_verdict(0.7, 0.9, lower=0.8) == "undecided"
    # 両側
    assert v13.interval_verdict(0.4, 0.6, lower=0.3, upper=0.7) == "pass"
    assert v13.interval_verdict(0.8, 0.9, lower=0.3, upper=0.7) == "fail"
    assert v13.interval_verdict(0.6, 0.9, lower=0.3, upper=0.7) == "undecided"
    with pytest.raises(ValueError, match="線が 1 本も無い"):
        v13.interval_verdict(0.0, 1.0)


def test_seeds_needed_search_is_monotone_and_bounded(v13):
    assert v13.seeds_needed(0.0, 0.5) == 3          # SD 0 なら最小本数
    assert v13.seeds_needed(1.0, 0.0) is None       # 距離 0 は解けない
    assert v13.seeds_needed(0.001, 0.0005) is None  # 10 本でも足りない
    assert v13.seeds_needed(0.0004, 0.0010) == 5


# ---------------------------------------------------------------- H1 の昼窓(6〜23 時)


def test_h1_day_window_slices_and_renormalises(v13, c7lib, hold, synth_holdout):
    path, _ = synth_holdout
    obs = hold.read_holdout(path)
    share = obs["obs_hour_share"]
    sim = (share * (obs["obs_area_share"] * 5)[:, None]).T * 1000.0
    h1 = v13.h1_day_window(sim, share)
    assert h1["window"] == "06-23" and h1["hours"] == list(range(6, 24))
    # 完全一致なら窓を切っても JSD 0・r 1(観測側の再正規化が効いている)
    assert h1["jsd_mean"] == pytest.approx(0.0, abs=1e-9)
    assert h1["pearson_r"] == pytest.approx(1.0, abs=1e-9)
    assert h1["pass"] is True


def test_h1_judged_on_day_window_and_24h_kept_as_description(v13, c7lib):
    seeds = _seeds(c7lib, [{"H1": {"jsd_mean": 0.050}}] * 3)          # 24 h 版は線の外
    day = [dict(r["H1"], jsd_mean=0.0010) for r in seeds]             # 昼だけなら内側
    got = v13.ensemble_verdict(seeds, per_seed_h1_day=day)
    assert got["metrics"]["H1"]["window"] == "06-23"
    assert got["metrics"]["H1"]["verdict"] == "pass"
    d24 = got["metrics"]["H1"]["descriptive_24h"]
    assert d24["judged"] is False
    assert d24["stats"]["jsd_mean"]["verdict"] == "fail"
    assert got["n_pass"] == 4 and got["pass"] is True


def test_h1_without_day_window_says_so(v13, c7lib):
    got = v13.ensemble_verdict(_seeds(c7lib, [{}] * 3))
    assert got["metrics"]["H1"]["window"] == "00-23"
    assert "欠落" in got["metrics"]["H1"]["window_note"]


def test_h1_day_window_length_mismatch_raises(v13, c7lib):
    seeds = _seeds(c7lib, [{}] * 3)
    with pytest.raises(ValueError, match="本数が合わない"):
        v13.ensemble_verdict(seeds, per_seed_h1_day=[seeds[0]["H1"]])


# ---------------------------------------------------------------- GET 包絡


def _shares(n_seeds: int, jitter: float = 0.0, seed: int = 7) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    base = rng.uniform(0.5, 1.5, size=(5, 24))
    base = base / base.sum(axis=1, keepdims=True)
    out = []
    for _ in range(n_seeds):
        x = base * (1.0 + rng.normal(0.0, jitter, size=base.shape)) if jitter else base.copy()
        out.append(x / x.sum(axis=1, keepdims=True))
    return out


def test_get_envelope_counts_and_is_not_a_test(v13):
    sims = _shares(3, jitter=0.05)
    obs = np.mean(np.stack(sims), axis=0)     # 平均は必ず min/max の内側
    env = v13.get_envelope(sims, obs)
    assert env["is_test"] is False
    assert env["p_floor"] == pytest.approx(1.0 / 3.0)
    assert "検定ではない" in env["note"]
    assert env["n_cells"] == 120 and env["n_inside_total"] == 120
    assert set(env["per_area"]) == set(v13.c7lib.AREA_IDS)


def test_get_envelope_detects_outside_hours(v13):
    sims = _shares(3, jitter=0.02)
    obs = np.mean(np.stack(sims), axis=0).copy()
    obs[0, 3] = 1.0                            # 明らかに包絡の外
    env = v13.get_envelope(sims, obs)
    assert env["n_inside_total"] == 119
    assert env["per_area"]["central"]["hours_outside"] == [3]


def test_get_envelope_shape_mismatch_raises(v13):
    with pytest.raises(ValueError, match="形が違う"):
        v13.get_envelope(_shares(3), np.zeros((5, 12)))


# ---------------------------------------------------------------- (f) fair CRPS


def test_f_fair_crps_second_term_ratio_is_m_over_m_minus_1(v13):
    d = v13.crps_fair_terms([1.0, 2.0, 4.0], 2.5)
    assert d["m"] == 3.0
    assert d["fair_factor"] == pytest.approx(3.0 / 2.0)
    assert d["term2_fair"] / d["term2_raw"] == pytest.approx(1.5)
    assert d["crps"] == pytest.approx(d["term1"] - d["term2_raw"])
    assert d["crps_fair"] == pytest.approx(d["term1"] - d["term2_fair"])
    assert d["crps_fair"] < d["crps"]          # fair は小アンサンブルの罰を外すので小さい


def test_f_fair_crps_reuses_c8_estimator(v13):
    import ensemble as c8_ensemble

    d = v13.crps_fair_terms([0.0, 1.0, 2.0], 1.0)
    assert d["crps"] == pytest.approx(c8_ensemble.crps_ensemble([0.0, 1.0, 2.0], 1.0))


def test_f_fair_crps_table_over_area_hour_cells(v13):
    sims = _shares(3, jitter=0.05)
    obs = np.mean(np.stack(sims), axis=0)
    tab = v13.fair_crps_table(sims, obs)
    assert tab["m"] == 3 and tab["n_cells"] == 120
    assert tab["fair_factor"] == pytest.approx(1.5)
    assert tab["term2_ratio"] == pytest.approx(1.5)
    assert tab["term2_fair_mean"] == pytest.approx(1.5 * tab["term2_raw_mean"])
    assert tab["crps_fair_mean"] < tab["crps_mean"]
    assert set(tab["per_area_crps_fair"]) == set(v13.c7lib.AREA_IDS)


def test_f_fair_crps_needs_two_members(v13):
    with pytest.raises(ValueError, match="2 本以上"):
        v13.crps_fair_terms([1.0], 1.0)


def test_f_deterministic_ensemble_crps_is_absolute_error(v13):
    d = v13.crps_fair_terms([2.0, 2.0, 2.0], 5.0)
    assert d["crps"] == pytest.approx(3.0) and d["crps_fair"] == pytest.approx(3.0)


# ---------------------------------------------------------------- (g) report


def test_g_report_declares_get_is_not_a_test(v13, c7lib):
    seeds = _seeds(c7lib, [{"H4": {"jsd": v}} for v in _NEAR_LINE])
    got = v13.ensemble_verdict(seeds, labels=["s1", "s2", "s3"])
    sims = _shares(3, jitter=0.03)
    obs = np.mean(np.stack(sims), axis=0)
    md = v13.report_v13(got, v13.get_envelope(sims, obs), v13.fair_crps_table(sims, obs))
    assert "検定ではない" in md
    assert "GET 包絡" in md
    assert "fair CRPS" in md
    assert "同値検定" in md
    assert "UNDECIDED(検出力不足)" in md
    assert "開封後に seed を足しても主張を変えない(追加 seed は記述の更新のみ)" in md
    assert "α=0.01" in md
    # 総合は「pass の数 / 判定対象数(H3 除く 4)」と undecided の数
    assert "3/4 合格" in md and "undecided 1" in md
    # H3 は記述欄にだけ出る
    assert "記述(判定に使わない)" in md
    assert "H3 深夜残存率" in md


def test_g_report_without_optional_blocks(v13, c7lib):
    md = v13.report_v13(v13.ensemble_verdict(_seeds(c7lib, [{}] * 3)))
    assert "GET 包絡" not in md and "fair CRPS" not in md
    assert "4/4 合格" in md and "**PASS**" in md


# ---------------------------------------------------------------- (h) 既定(v1.2)の不変


def test_h_default_report_is_byte_for_byte_the_v12_text(hold, c7lib, synth_holdout):
    """``report`` の既定(``v13_section=None``)は v1.2 の文面そのまま。"""
    path, _ = synth_holdout
    obs = hold.read_holdout(path)
    sim = (obs["obs_hour_share"] * (obs["obs_area_share"] * 5)[:, None]).T * 1000.0
    res = hold.compare(sim, obs, sim_attr=obs["obs_attr_share"])
    seal = {"layer": "kddi_la", "member_hash": "0123456789abcdef0123", "ok": True,
            "sealed_utc": "2026-09-08T00:00:00Z"}
    md = hold.report(res, seal, obs["meta"])
    expected = "\n".join([
        "# C7 holdout 照合(KDDI 形状5指標・**事後1回のみ**)",
        "",
        "- 封印層: `kddi_la` / member_hash `0123456789abcdef…` / 封印時刻 "
        "2026-09-08T00:00:00Z / sha256 一致 OK",
        f"- holdout 年: 2024 / 使用レコード {obs['meta']['hour']['n_used']}"
        f"(時間帯表 {obs['meta']['n_hour_rows']} 行)",
        "- 出力は**シェア・順位・比のみ**(D1′「値は形状と比のみ」)。",
        "",
        c7lib.metrics_markdown(res),
        "",
        f"総合: {res['n_pass']}/{res['n_measured']} 合格 → **PASS**",
    ])
    assert md == expected
    assert md == hold.report(res, seal, obs["meta"], None)
    assert "v1.3" not in md and "アンサンブル" not in md


def test_h_v12_result_dict_is_plain_five_metrics(hold, c7lib, synth_holdout):
    """``compare`` は ``five_metrics`` そのまま=v1.3 の追加で結果 dict が変わらない。"""
    path, _ = synth_holdout
    obs = hold.read_holdout(path)
    sim = (obs["obs_hour_share"] * (obs["obs_area_share"] * 5)[:, None]).T * 1000.0
    got = hold.compare(sim, obs, sim_attr=obs["obs_attr_share"])
    want = c7lib.five_metrics(sim, obs["obs_hour_share"], sim_attr=obs["obs_attr_share"],
                              obs_attr=obs["obs_attr_share"],
                              obs_area_share=obs["obs_area_share"])
    assert got == want
    assert set(got) == {"H1", "H2", "H3", "H4", "H5", "prereg",
                        "n_measured", "n_pass", "pass"}


def test_h_ensemble_verdict_does_not_mutate_inputs(v13, c7lib):
    seeds = _seeds(c7lib, [{"H4": {"jsd": v}} for v in _NEAR_LINE])
    before = copy.deepcopy(seeds)
    v13.ensemble_verdict(seeds)
    assert seeds == before


def test_h_cli_default_prereg_version_is_v12(hold):
    assert hold.validate_prereg_version("v1.2", ["one.json"]) == "v1.2"
    # 既定値そのものを固定(--prereg-version を書かなければ v1.2)
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg-version", choices=hold.PREREG_VERSIONS, default="v1.2")
    assert ap.parse_args([]).prereg_version == "v1.2"
    assert hold.PREREG_VERSIONS == ("v1.2", "v1.3")


# ---------------------------------------------------------------- (i) CLI の版と本数


def test_i_v13_with_one_occupancy_is_an_explicit_error(hold):
    with pytest.raises(ValueError, match="2 本以上必要"):
        hold.validate_prereg_version("v1.3", ["only.json"])


def test_i_v12_with_many_occupancy_is_an_explicit_error(hold):
    with pytest.raises(ValueError, match="v1.3"):
        hold.validate_prereg_version("v1.2", ["a.json", "b.json"])


def test_i_unknown_version_and_empty_list(hold):
    with pytest.raises(ValueError, match="prereg-version"):
        hold.validate_prereg_version("v9", ["a.json"])
    with pytest.raises(ValueError, match="1 本も無い"):
        hold.validate_prereg_version("v1.3", [])


def test_i_main_refuses_before_touching_the_seal(hold, tmp_path, capsys):
    """版と本数の不整合は**封印に触る前**に落ちる(``--open-seal`` は一切渡さない)。"""
    missing = tmp_path / "nowhere"
    with pytest.raises(SystemExit) as exc:
        hold.main(["--occupancy", "one.json", "--prereg-version", "v1.3",
                   "--world", str(missing), "--data-root", str(missing),
                   "--record", str(tmp_path / "rec.json")])
    assert exc.value.code == 2                      # argparse の使い方エラー
    assert "2 本以上必要" in capsys.readouterr().err
    assert not (tmp_path / "rec.json").exists()     # 開封記録も書かれていない


def test_i_v13_accepts_two_or_more(hold):
    assert hold.validate_prereg_version("v1.3", ["a.json", "b.json"]) == "v1.3"
    assert hold.validate_prereg_version("v1.3", ["a.json", "b.json", "c.json"]) == "v1.3"


def test_j_apply_ensemble_verdict_moves_ensemble_to_top_level_and_keeps_seed1(v13):
    """第216(親): v1.3 ではトップレベル n_pass/n_measured/pass がアンサンブル判定。seed 1 の点判定は seed1_v12 に残る。入力は壊さない。"""
    payload = {"schema": "x", "n_pass": 5, "n_measured": 5, "pass": True, "other": 1}
    before = dict(payload)
    ens = {"n_pass": 3, "n_measured": 4, "n_undecided": 1, "n_fail": 0, "pass": False}
    out = v13.apply_ensemble_verdict(payload, ens)
    assert payload == before
    assert (out["n_pass"], out["n_measured"], out["pass"]) == (3, 4, False)
    assert out["seed1_v12"] == {"n_pass": 5, "n_measured": 5, "pass": True}
    assert "v1.3" in out["verdict_source"] and out["other"] == 1
