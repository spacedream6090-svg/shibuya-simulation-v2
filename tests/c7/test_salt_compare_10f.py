# -*- coding: utf-8 -*-
"""10f 第 2 段 T2: salt の道具の読む役(``tools/c7/salt_compare.py``)を既知の答えで確かめる(純関数・ランを回さない)。

手計算の値はテストの中に式で書く(道具の関数を使わずに出す)。
"""
from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "c7"))
import salt_compare as sc  # noqa: E402

#: t 分布の分位の表(Abramowitz & Stegun 表 26.10 の値・小数 3 桁)。
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 9: 2.262, 12: 2.179}
T995 = {2: 9.925, 4: 4.604, 10: 3.169}


def test_t_quantile_matches_the_table():
    for df, v in T975.items():
        assert sc.t_quantile(0.975, df) == pytest.approx(v, abs=6e-4), df
    for df, v in T995.items():
        assert sc.t_quantile(0.995, df) == pytest.approx(v, abs=6e-4), df
    assert sc.t_quantile(0.025, 4) == pytest.approx(-2.776, abs=6e-4)
    # 1 自由度は Cauchy: 分位 = tan(π(q − 1/2))
    assert sc.t_quantile(0.9, 1) == pytest.approx(math.tan(math.pi * 0.4), rel=1e-9)


def test_d46_two_formulas_match_r71():
    """R-71 §5-1: CV 0.0325 で 2% は (CV/r)²→3 本・半幅なら 13 本、1% は 11 本・44 本。"""
    cv = 0.0325
    assert sc.n_relative_se(cv, 0.02) == 3 and sc.n_relative_se(cv, 0.01) == 11
    assert sc.n_halfwidth95(cv, 0.02) == 13 and sc.n_halfwidth95(cv, 0.01) == 44
    # 13 本は満たし 12 本は満たさない(手の式)
    assert sc.t_quantile(0.975, 12) * cv / math.sqrt(13) <= 0.02 < sc.t_quantile(0.975, 11) * cv / math.sqrt(12)


@pytest.mark.parametrize("n", [3, 4, 5, 6, 7, 8])
def test_p_floor_table(n):
    """R-71 §2-3 の表: 片側 1/2^n・両側 2/2^n。全部同じ向きの差で下限に届く。"""
    d = np.arange(1, n + 1, dtype=float)
    assert sc.p_floor(n, "two-sided") == 2 / 2 ** n
    assert sc.p_floor(n, "greater") == 1 / 2 ** n
    assert sc.sign_flip_p(d)["p"] == 2 / 2 ** n
    assert sc.sign_flip_p(d, "greater")["p"] == 1 / 2 ** n
    assert sc.sign_flip_p(-d, "less")["p"] == 1 / 2 ** n


def test_six_pairs_reach_2_over_64():
    assert sc.sign_flip_p([0.5, 1.0, 1.5, 2.0, 2.5, 3.0])["p"] == 2 / 64 == sc.p_floor(6)


def test_sign_flip_matches_brute_force():
    """全部の符号の組を itertools で数えた p と一致(0 と同点を含む)。"""
    rng = np.random.default_rng(3)
    for d in (rng.normal(0.3, 1.0, 7), np.array([0.0, 1.0, -2.0, 2.0, 0.5]), np.array([0.0, 1.0, 2.0])):
        t = d.mean()
        flips = [np.mean(np.array(s) * d) for s in itertools.product((1.0, -1.0), repeat=d.size)]
        p2 = np.mean([abs(f) >= abs(t) - 1e-12 for f in flips])
        pg = np.mean([f >= t - 1e-12 for f in flips])
        pl = np.mean([f <= t + 1e-12 for f in flips])
        assert sc.sign_flip_p(d)["p"] == pytest.approx(p2)
        assert sc.sign_flip_p(d, "greater")["p"] == pytest.approx(pg)
        assert sc.sign_flip_p(d, "less")["p"] == pytest.approx(pl)
    assert sc.sign_flip_p([0.0, 1.0, 2.0])["p"] == 0.5  # 0 の差は反転しても同じ=同点(手計算 4/8)


def test_known_two_arms_three_pairs_hand_values():
    """既知の 2 腕(差が分かっている合成の例)。基準 10,12,14・腕 11,15,16 → 差 1,3,2。"""
    base, arm = [10.0, 12.0, 14.0], [11.0, 15.0, 16.0]
    st = sc.paired_stats(base, arm, alpha=0.05, family_size=1)
    # 差の平均 2・差の SD 1・基準の SD 2・腕の SD √7
    assert st["diff"] == 2.0 and st["effect"]["sd_diff"] == pytest.approx(1.0)
    t = 4.302652729749752  # t(0.975, 2)
    assert st["width"] == pytest.approx(t * 1.0 / math.sqrt(3), rel=1e-9)
    assert st["diff_over_width"] == pytest.approx(2.0 / (t / math.sqrt(3)), rel=1e-9)
    assert st["width_base"] == pytest.approx(t * 2.0 / math.sqrt(3), rel=1e-9)
    assert st["width_arm"] == pytest.approx(t * math.sqrt(7.0) / math.sqrt(3), rel=1e-9)
    # ρ: Var(D)=1・Var(基準)=4・Var(腕)=7 → 比 1/11・ρ = (4+7−1)/(2·2·√7)
    assert st["crn"]["var_ratio"] == pytest.approx(1.0 / 11.0)
    assert st["crn"]["rho"] == pytest.approx(10.0 / (4.0 * math.sqrt(7.0)))
    assert st["crn"]["rho"] == pytest.approx(float(np.corrcoef(base, arm)[0, 1]))  # ピアソンの相関と同じ
    assert st["crn"]["rho_readable"] is False and st["crn"]["warn_ratio_over_1"] is False
    # 効果の大きさ: 比 14/12(腕の平均 14・基準の平均 12)・d_z = 2/1・d_av = 2/((2+√7)/2)
    assert st["effect"]["ratio_arm_over_base"] == pytest.approx(14.0 / 12.0)
    assert st["effect"]["d_z_crn_pair"] == pytest.approx(2.0)
    assert st["effect"]["d_av"] == pytest.approx(2.0 / ((2.0 + math.sqrt(7.0)) / 2.0))
    # t 区間 2 ± t·1/√3
    assert st["ci_t95"]["lo"] == pytest.approx(2.0 - t / math.sqrt(3)) and st["ci_t95"]["hi"] == pytest.approx(2.0 + t / math.sqrt(3))
    # 並べ替えの反転: 3 対では 95% は作れない・k=1 の 75% は [最小, 最大] = [1, 3]
    ci = st["ci_perm"]
    assert ci["interval"] is None and ci["interval_below"]["level"] == 0.75
    assert ci["interval_below"]["lo"] == pytest.approx(1.0) and ci["interval_below"]["hi"] == pytest.approx(3.0)
    # 家族の幅: m=5 なら t(1 − 0.05/10, 2)
    st5 = sc.paired_stats(base, arm, alpha=0.05, family_size=5)
    assert st5["width_t"] == pytest.approx(sc.t_quantile(0.995, 2)) and st5["width_t"] == pytest.approx(9.925, abs=6e-4)


def test_three_pairs_say_descriptive_only():
    spec = {"alpha": 0.05, "primary": {"id": "x", "path": "x", "direction": "greater", "preregistered": True}}
    r = sc.analyze({"x": {"base": [10, 12, 14], "arm": [11, 15, 16]}}, spec)
    row = r["metrics"]["x"]
    assert row["status"] == sc.DESCRIPTIVE == "記述のみ(本数不足)" and r["overall"] == sc.DESCRIPTIVE
    assert row["p_floor"] == 1 / 8 and row["p"] == 1 / 8 and row["decision"] is None
    assert "記述" in row["status_note"]


def test_five_pairs_need_a_preregistered_direction_and_six_pairs_test_two_sided():
    base = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
    arm = [b + 1.0 + 0.1 * i for i, b in enumerate(base)]
    pre = {"alpha": 0.05, "primary": {"id": "x", "path": "x", "direction": "greater", "preregistered": True}}
    no_pre = {"alpha": 0.05, "primary": {"id": "x", "path": "x", "direction": "greater"}}
    r5 = sc.analyze({"x": {"base": base[:5], "arm": arm[:5]}}, pre)["metrics"]["x"]
    assert r5["alternative"] == "greater" and r5["p_floor"] == 1 / 32 and r5["status"] == sc.TESTED and r5["decision"] is True
    r5n = sc.analyze({"x": {"base": base[:5], "arm": arm[:5]}}, no_pre)["metrics"]["x"]
    assert r5n["alternative"] == "two-sided" and r5n["p_floor"] == 2 / 32 and r5n["status"] == sc.DESCRIPTIVE
    r6 = sc.analyze({"x": {"base": base, "arm": arm}}, no_pre)["metrics"]["x"]
    assert r6["p_floor"] == 2 / 64 and r6["p"] == 2 / 64 and r6["status"] == sc.TESTED and r6["decision"] is True


def test_holm_and_bh_known_example():
    """手計算: p = 0.01, 0.04, 0.03, 0.005(α=0.05)。

    Holm: 昇順 0.005·4=0.02 / 0.01·3=0.03 / 0.03·2=0.06 / 0.04·1 → 単調化で 0.06。棄却は 0.005 ≤ 0.0125・0.01 ≤ 0.0167
    の 2 つ(0.03 > 0.025 で止まる)。BH: q = min_{j≥i} p_(j)·m/j → 0.02, 0.02, 0.04, 0.04。k̂=4(0.04 ≤ 0.05)で全部棄却。
    """
    p = [0.01, 0.04, 0.03, 0.005]
    h = sc.holm(p, 0.05)
    assert h["adjusted"] == pytest.approx([0.03, 0.06, 0.06, 0.02])
    assert h["reject"] == [True, False, False, True]
    b = sc.bh(p, 0.05)
    assert b["q"] == pytest.approx([0.02, 0.04, 0.04, 0.02]) and b["k_hat"] == 4 and all(b["reject"])
    # BH が一部だけ棄却する例: p = 0.001, 0.02, 0.04, 0.3 → 閾値 0.0125, 0.025, 0.0375, 0.05 → k̂=2
    b2 = sc.bh([0.04, 0.001, 0.3, 0.02], 0.05)
    assert b2["k_hat"] == 2 and b2["reject"] == [False, True, False, True]
    assert b2["q"] == pytest.approx([0.04 * 4 / 3, 0.004, 0.3, 0.04])


def test_holm_family_of_five_needs_eight_pairs():
    """R-71 §2-3: Holm で 5 本なら最小の線は 0.01 → 両側 7 対(2/128=0.0156)では届かず 8 対(0.0078)で届く。"""
    def spec(k):
        return {"alpha": 0.05, "primary": {"id": "p", "path": "p"},
                "secondary": [{"id": f"s{i}", "path": f"s{i}"} for i in range(k)]}
    for n, want in ((7, sc.DESCRIPTIVE), (8, sc.TESTED)):
        base = list(np.arange(n, dtype=float))
        arm = [b + 1.0 + 0.01 * i for i, b in enumerate(base)]
        vals = {"p": {"base": base, "arm": arm}, **{f"s{i}": {"base": base, "arm": arm} for i in range(5)}}
        r = sc.analyze(vals, spec(5))
        assert all(r["metrics"][f"s{i}"]["status"] == want for i in range(5)), n
        assert r["metrics"]["p"]["status"] == sc.TESTED and r["metrics"]["s0"]["line"] == pytest.approx(0.01)
        if want == sc.TESTED:
            assert r["metrics"]["s0"]["p_holm"] == pytest.approx(min(1.0, 5 * 2 / 2 ** n))


def test_perm_ci_six_pairs_is_min_max_at_96_9_percent():
    ci = sc.perm_ci([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], 0.95)
    assert ci["level_achieved"] == pytest.approx(1 - 2 / 64)
    assert ci["interval"]["lo"] == pytest.approx(1.0) and ci["interval"]["hi"] == pytest.approx(6.0)
    assert ci["interval"]["convex"] is True
    # 8 対では 1 − 2k/256 ≥ 0.95 で最小の水準は k=6 → 1 − 12/256
    assert sc.perm_ci(list(range(1, 9)), 0.95)["level_achieved"] == pytest.approx(1 - 12 / 256)


def test_crn_ratio_warns_when_negatively_correlated():
    st = sc.paired_stats([1, 2, 3, 4, 5], [5, 4, 3, 2, 1.5])
    assert st["crn"]["rho"] < 0 and st["crn"]["var_ratio"] > 1 and st["crn"]["warn_ratio_over_1"] is True
    assert st["crn"]["rho_readable"] is True and st["crn"]["ratio_over_1_unread"] is False
    # 検収 S3-5: 5 対未満は比が 1 を超えても警告しない(読まない印だけ)
    st3 = sc.paired_stats([1, 2, 3], [3, 2, 1.5])
    assert st3["crn"]["var_ratio"] > 1 and st3["crn"]["warn_ratio_over_1"] is False
    assert st3["crn"]["ratio_over_1_unread"] is True and st3["crn"]["rho_readable"] is False


def test_diff_over_width_is_labelled_as_descriptive():
    """検収 S3-2: 差 ÷ 幅の読み方の注記が全部の行に付き、記述のみの行の注記にも書かれる。"""
    r = sc.analyze({"x": {"base": [10, 12, 14], "arm": [11, 15, 16]}}, {"primary": {"id": "x", "path": "x"}})
    row = r["metrics"]["x"]
    assert row["diff_over_width"] > 0.8 and row["diff_over_width_reading"] == sc.DIFF_OVER_WIDTH_READING
    assert "K20 (a) の検定ではない" in row["diff_over_width_reading"] and "K20 (a) の検定ではない" in row["status_note"]


def test_primary_must_be_one():
    with pytest.raises(ValueError):
        sc.analyze({"a": {"base": [1, 2], "arm": [2, 3]}, "b": {"base": [1, 2], "arm": [2, 3]}},
                   {"primary": [{"id": "a", "path": "a"}, {"id": "b", "path": "b"}]})


# ---------------------------------------------------------------- CRN の健全性(合成の checkpoints)
def _doc(seed, *, pop=1, env=1, arm_val=0.0, beh=None, final=None, extra_cfg=None, ticks=(59, 119, 179)):
    beh = beh or ["b0", "b1", "b2"][: len(ticks)]
    man = {"population_seed": pop, "environment_seed": env, "attendance_rate": 1.0, "salient": arm_val,
           "replay_date": "2026-07-28", "llm_calls_total": 100 + seed,
           "manifest_sections": {"schema": "x", "rule": "longest-prefix",
                                 "paths": {"population_seed": "config", "environment_seed": "config",
                                           "attendance_rate": "config", "salient": "config", "replay_date": "config",
                                           "llm_calls_total": "observed", "manifest_sections": "config"}}}
    man.update(extra_cfg or {})
    return {"schema": "shibuya.cli/checkpoints/1", "seed": seed, "n_agents": 10, "ticks": 180, "run_id": "",
            "final_hash": final or f"f{seed}",
            "checkpoints": [{"tick": t, "combined": h + "c", "behavior_hash": h, "full_hash": h + "f",
                             "population_hash": f"P{pop}", "schedule_hash": "S"} for t, h in zip(ticks, beh)],
            "manifest": man}


def test_pre_t0_first_divergence_and_aa_synthetic():
    a = _doc(1)
    b = _doc(1, arm_val=1.0, beh=["b0", "b1", "XX"])
    assert sc.pre_t0_match(a, b, 120)["ok"] is True
    bad = sc.pre_t0_match(a, b, 180)
    assert bad["ok"] is False and bad["first_bad_tick"] == 179
    fd = sc.first_divergence(a, b)
    assert fd["first_tick"] == 179 and fd["last_match_tick"] == 119 and "behavior_hash" in fd["hashes_differ"]
    assert sc.aa_match(a, _doc(1))["ok"] is True
    assert sc.aa_match(a, _doc(1, final="other"))["ok"] is False


def test_pre_t0_without_checkpoints_is_unchecked():
    """検収 S2: T0 > 0 で T0 より前の checkpoint が 0 本なら「未検査」(ok は None)。T0 = 0 は対象外で True。"""
    a, b = _doc(1, ticks=(179,), beh=["b2"]), _doc(1, arm_val=1.0, ticks=(179,), beh=["XX"])
    r = sc.pre_t0_match(a, b, 120)
    assert r["ok"] is None and r["status"] == sc.UNCHECKED and r["checkpoints_before_T0"] == 0
    assert sc.pre_t0_match(a, b, 0)["ok"] is True and sc.pre_t0_match(a, b, 0)["status"] == "対象外"


def _index(aa=True, t0=0, mode="fixed"):
    salts = [1, 2, 3]
    runs = [{"arm": "base", "salt": s, "checkpoints": f"base{s}"} for s in salts]
    runs += [{"arm": "arm", "salt": s, "checkpoints": f"arm{s}"} for s in salts]
    pay = {f"base{s}": _doc(s) for s in salts}
    pay.update({f"arm{s}": _doc(s, arm_val=1.0) for s in salts})
    if aa:
        runs.append({"arm": "base", "salt": 1, "checkpoints": "aa", "aa": True})
        pay["aa"] = _doc(1)
    idx = {"base": "base", "arm": "arm", "salts": salts, "runs": runs, "T0": t0, "environment_mode": mode,
           "arms": {"base": {"salient": 0.0}, "arm": {"salient": 1.0}}}
    return idx, pay


def test_crn_health_three_values():
    """検収 S2: A/A が無いと ok=None(未検査)・全部通れば True・落ちれば False(未検査より落ちたが先)。"""
    idx, pay = _index(aa=True)
    r = sc.crn_health(idx, pay)
    assert r["ok"] is True and r["status"] == "ok" and r["unchecked"] == []
    idx, pay = _index(aa=False)
    r = sc.crn_health(idx, pay)
    assert r["ok"] is None and r["status"] == sc.UNCHECKED and "A/A" in r["unchecked"][0]
    idx, pay = _index(aa=True, t0=30)  # T0 より前の checkpoint が 0 本(最初は 59)
    r = sc.crn_health(idx, pay)
    assert r["ok"] is None and r["status"] == sc.UNCHECKED
    idx, pay = _index(aa=False)
    pay["arm2"] = _doc(2, arm_val=1.0, extra_cfg={"attendance_rate": 0.5})
    r = sc.crn_health(idx, pay)
    assert r["ok"] is False and r["status"] == "fail"


def test_arm_keys_only_differing_values_and_trees_only_for_dicts():
    """検収 S3-4: 両方の腕で同じ値の引数は腕の欄にしない・下の木を許すのは値が辞書の引数だけ。"""
    keys, trees = sc.arm_keys_of({"vocab_version": "v3", "activity": True, "refractory_scale": {}},
                                 {"vocab_version": "v3", "plan_executor": False, "refractory_scale": {"X": 2.0}})
    assert keys == ["activity", "plan_executor", "refractory_scale"] and trees == ["refractory_scale"]
    base = [_doc(s) for s in (1, 2)]
    arm = [_doc(s, arm_val=1.0, extra_cfg={"activity": {"x": 1}}) for s in (1, 2)]
    for d in base + arm:
        d["manifest"]["manifest_sections"]["paths"]["activity"] = "config"
    base2 = [_doc(s, extra_cfg={"activity": {"x": 0}}) for s in (1, 2)]
    for d in base2:
        d["manifest"]["manifest_sections"]["paths"]["activity"] = "config"
    # 接頭辞は「下の木を許す欄」だけ: 腕の欄 activity(辞書でない)では activity.x の差は外
    r = sc.input_match(base2, arm, ["salient", "activity"])
    assert r["ok"] is False and r["pairs"][0]["config_diffs_outside_arm"] == ["activity.x"]
    r2 = sc.input_match(base2, arm, ["salient", "activity"], tree_keys=["activity"])
    assert r2["ok"] is True


def test_input_match_synthetic():
    base = [_doc(s) for s in (1, 2, 3)]
    arm = [_doc(s, arm_val=1.0) for s in (1, 2, 3)]
    r = sc.input_match(base, arm, ["salient"], environment_mode="fixed")
    assert r["ok"] is True and r["population_fixed"] is True and r["environment_fixed"] is True
    assert r["pairs"][0]["config_diffs"] == ["salient"] and r["arm_keys_unseen"] == []
    assert r["pairs"][0]["config_diff_values"] == {"salient": {"base": 0.0, "arm": 1.0}}
    # 腕の欄の外の設定の差(出勤率)は落ちる
    arm2 = [_doc(s, arm_val=1.0, extra_cfg={"attendance_rate": 0.8} if s == 2 else None) for s in (1, 2, 3)]
    r2 = sc.input_match(base, arm2, ["salient"])
    assert r2["ok"] is False and r2["pairs"][1]["config_diffs_outside_arm"] == ["attendance_rate"]
    # 母集団の seed が salt で変わる(K21 の前の salt)と落ちる
    r3 = sc.input_match([_doc(s, pop=s) for s in (1, 2, 3)], [_doc(s, pop=s, arm_val=1.0) for s in (1, 2, 3)], ["salient"])
    assert r3["ok"] is False and r3["population_fixed"] is False
    # 対の seed が違うと落ちる
    r4 = sc.input_match(base, [_doc(s + 1, arm_val=1.0) for s in (1, 2, 3)], ["salient"])
    assert r4["ok"] is False and r4["pairs"][0]["same_seed"] is False
    # 腕の欄が manifest の設定に見えない(manifest に載っていない腕)は報告する(落とさない)
    r5 = sc.input_match(base, [_doc(s) for s in (1, 2, 3)], ["salient_rate_per_10k"])
    assert r5["ok"] is True and r5["arm_keys_unseen"] == ["salient_rate_per_10k"]


def test_seed_type_matters():
    """検収 S3-8: 1 と "1" は core.rng で別の鍵=同じ母集団の seed とみなさない。"""
    assert sc.seed_key(1) != sc.seed_key("1") and sc.seed_key(1) == sc.seed_key(1)
    r = sc.input_match([_doc(1, pop=1), _doc(2, pop=1)], [_doc(1, pop="1", arm_val=1.0), _doc(2, pop="1", arm_val=1.0)],
                       ["salient", "population_seed"])
    assert r["ok"] is False and r["population_fixed"] is False and r["pairs"][0]["same_population_seed"] is False


def test_derived_keys_need_declared_values():
    """検収 S3-3: 導かれる欄は {base, arm, reason} で宣言し、実際の値と違えば落ちる。理由だけの古い形は止める。"""
    base = [_doc(s, extra_cfg={"syn": "v2"}) for s in (1, 2)]
    arm = [_doc(s, arm_val=1.0, extra_cfg={"syn": "v5"}) for s in (1, 2)]
    for d in base + arm:
        d["manifest"]["manifest_sections"]["paths"]["syn"] = "config"
    r0 = sc.input_match(base, arm, ["salient"])
    assert r0["ok"] is False and r0["pairs"][0]["config_diffs_outside_arm"] == ["syn"]
    good = {"syn": {"base": "v2", "arm": "v5", "reason": "語彙の版から決まる"}}
    r1 = sc.input_match(base, arm, ["salient"], derived=good)
    assert r1["ok"] is True and r1["arm_keys_derived"]["syn"]["reason"] == "語彙の版から決まる"
    wrong = {"syn": {"base": "v2", "arm": "v9", "reason": "書き違い"}}
    r2 = sc.input_match(base, arm, ["salient"], derived=wrong)
    assert r2["ok"] is False and r2["arm_keys_derived_mismatch"][0]["actual"] == {"base": "v2", "arm": "v5"}
    with pytest.raises(ValueError):
        sc.input_match(base, arm, ["salient"], derived={"syn": "理由だけ"})


def test_environment_seed_modes():
    """10f 第 2 段の直し(S1): 対の間で環境の seed が違えば落ちる・fixed で salt ごとに違えば落ちる・salt なら許し、
    環境から導かれる欄(replay_date)の salt の間の差も許して報告する。"""
    base = [_doc(s, env=s, extra_cfg={"replay_date": f"d{s}"}) for s in (1, 2, 3)]
    arm = [_doc(s, env=s, arm_val=1.0, extra_cfg={"replay_date": f"d{s}"}) for s in (1, 2, 3)]
    rs = sc.input_match(base, arm, ["salient"], environment_mode="salt")
    assert rs["ok"] is True and rs["environment_fixed"] is False
    assert rs["within_arm"]["base"]["environment_derived_diffs"] == ["manifest.replay_date"]
    rf = sc.input_match(base, arm, ["salient"], environment_mode="fixed")
    assert rf["ok"] is False
    rp = sc.input_match(base, [_doc(s, env=9, arm_val=1.0) for s in (1, 2, 3)], ["salient"], environment_mode="salt")
    assert rp["ok"] is False and rp["pairs"][0]["same_environment_seed"] is False


def test_main_exit_codes(tmp_path):
    """再検収 T5: ``main`` の終了コードは CRN の健全性が ok なら 0・fail なら 1・未検査なら 3。"""
    import json as _json

    spec = tmp_path / "m.json"
    spec.write_text(_json.dumps({"primary": {"id": "c", "path": "manifest.llm_calls_total"}}), encoding="utf-8")
    want = {"ok": 0, "unchecked": 3, "fail": 1}
    for name in want:
        idx, pay = _index(aa=(name != "unchecked"))
        if name == "fail":
            pay["arm2"] = _doc(2, arm_val=1.0, extra_cfg={"attendance_rate": 0.5})
        d = tmp_path / name
        d.mkdir()
        for k, v in pay.items():
            (d / k).write_text(_json.dumps(v), encoding="utf-8")
        (d / "runs.json").write_text(_json.dumps(idx), encoding="utf-8")
        rc = sc.main(["--runs", str(d / "runs.json"), "--metrics", str(spec), "--out", str(d / "rep.json")])
        assert rc == want[name], name
    assert sc.exit_code({"status": "ok"}) == 0 and sc.exit_code({"status": sc.UNCHECKED}) == 3
