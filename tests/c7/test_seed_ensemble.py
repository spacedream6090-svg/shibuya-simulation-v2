# -*- coding: utf-8 -*-
"""``tools/c7/seed_ensemble.py``(N seed の帰無参照・prereg v1.3 §7)の検収。実データは読まない。"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "c7"))
import seed_ensemble as se  # noqa: E402


def _tables(n: int, noise: float = 0.01) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(0)
    base = rng.uniform(1_000, 5_000, size=(24, 5))
    return {f"seed {i + 1}": base * (1.0 + rng.normal(0.0, noise, size=(24, 5))) for i in range(n)}


def test_two_seeds_reproduce_fig_seed_pair_cv():
    """n=2 の ddof=1 標本 SD は |a−b|/√2=fig_seed_pair.summarize と同じ CV。"""
    tabs = _tables(2)
    d = se.summarize_ensemble(tabs)
    (_, t1), (_, t2) = tabs.items()
    f1, f2 = t1.sum(axis=1), t2.sum(axis=1)
    expect = np.abs(f1 - f2) / math.sqrt(2.0) / ((f1 + f2) / 2.0)
    assert np.allclose(d["cv_hour"], expect)
    assert d["n_seeds"] == 2 and d["n_pairs"] == 1
    assert d["pairs"][0]["jsd_area_mean_bits"] == d["null_reference_jsd_bits"]


def test_three_seeds_cv_and_pairwise_null_reference():
    tabs = _tables(3)
    d = se.summarize_ensemble(tabs)
    F = np.stack([t.sum(axis=1) for t in tabs.values()])
    assert np.allclose(d["cv_hour"], F.std(axis=0, ddof=1) / F.mean(axis=0))
    assert d["n_pairs"] == 3 and [p["pair"] for p in d["pairs"]] == [
        ["seed 1", "seed 2"], ["seed 1", "seed 3"], ["seed 2", "seed 3"]]
    pair_means = [p["jsd_area_mean_bits"] for p in d["pairs"]]
    assert math.isclose(d["null_reference_jsd_bits"], float(np.mean(pair_means)))
    assert d["null_reference_jsd_bits_max_pair"] == max(pair_means)
    assert math.isclose(d["raw_crps_inflation_if_calibrated"], 4.0 / 3.0)  # (1+1/M)
    assert math.isclose(d["fair_crps_spread_term_factor"], 1.5)  # M/(M−1)
    # 家族 95%(5 指標・α=0.01)は t(0.995, 2)=9.925 → 半幅 = 9.925·CV/√3
    fam = d["family95"]
    assert math.isclose(fam["t_quantile"], 9.925, rel_tol=1e-3)
    assert math.isclose(fam["day"]["half_width_pct_median"],
                        100.0 * 9.925 / math.sqrt(3.0) * fam["day"]["cv_median"], rel_tol=1e-3)
    assert fam["day"]["hours"] == list(range(6, 24)) and fam["night"]["hours"] == list(range(0, 6))


def test_identical_seeds_give_zero_spread():
    t = _tables(1)["seed 1"]
    d = se.summarize_ensemble({"a": t, "b": t.copy(), "c": t.copy()})
    assert max(d["cv_hour"]) <= 1e-12  # 3 個の同値の平均は丸めで 1 ulp ずれうる
    assert d["null_reference_jsd_bits"] <= 1e-12
    assert d["family95"]["night"]["half_width_pct_max"] <= 1e-9


def test_r25_parent_recomputation_reproduces():
    """第209 の親再計算: 3 seed・CV 0.0038(昼中央値)→ ±2.2% / 0.0325(深夜最大)→ ±18.6%。"""
    assert math.isclose(se.family_half_width_pct(0.0038, 3), 2.18, abs_tol=0.02)
    assert math.isclose(se.family_half_width_pct(0.0325, 3), 18.6, abs_tol=0.1)


def test_jsd_is_symmetric_bounded_and_zero_on_equal():
    p = np.array([1.0, 2.0, 3.0, 4.0]); q = np.array([4.0, 3.0, 2.0, 1.0])
    assert se.jsd_bits(p, p) == 0.0
    assert math.isclose(se.jsd_bits(p, q), se.jsd_bits(q, p))
    assert 0.0 < se.jsd_bits(p, q) <= 1.0
    assert se.jsd_bits(np.zeros(4), q) == 0.0  # 空エリアは 0(落ちない)


def test_cli_refuses_to_overwrite_existing_output(tmp_path: Path):
    out = tmp_path / "x.json"; out.write_text("{}", encoding="utf-8")
    assert se.main(["--out", str(out)]) == 2
    assert out.read_text(encoding="utf-8") == "{}"


def test_cli_run_argument_needs_label_equals_path():
    import pytest
    with pytest.raises(SystemExit):
        se._parse_runs(["no-equals"])
    assert se._parse_runs(["a=x.npz", "b=y.npz"]) == {"a": "x.npz", "b": "y.npz"}
