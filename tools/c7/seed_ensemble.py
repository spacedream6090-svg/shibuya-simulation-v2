# -*- coding: utf-8 -*-
"""seed アンサンブル(N 本)の帰無参照 — prereg v1.3 §7「3 本の対ごとの平均」と家族 95% 区間(第215)。

``occupancy.npz``(毎正時×520 セル)を ``area_axes_v0`` で 5 エリアに畳み、時×エリア表を
**seed 同士で**比べる(holdout には触らない)。2 本のときの CV は ``tools/fig/fig_seed_pair.summarize``
と同じ値になる(ddof=1 の標本 SD ÷ 平均)。

出すもの
- 時ごとの CV(5 エリア合計)とエリアごとの CV 中央値
- 対ごとのエリア別 24 h シェア JSD(bits)→ **全対の平均=帰無参照**(v1.2 の 0.000162 は 1 対)
- 家族 95%(5 指標・Bonferroni α=0.01/指標・両側)の平均の区間半幅 = t(0.995, n−1)·CV/√n
  を 昼(6〜23 時・CV 中央値)と 深夜(0〜5 時・CV 最大)で(第209 の親再計算と同じ式)
- raw CRPS の期待膨張 (1+1/M) と fair CRPS の広がり項係数 M/(M−1)・N=(CV/r)²(L-B 答申 §5)
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import occupancy_series as occ  # noqa: E402

SCHEMA = "shibuya.tools.c7/seed_ensemble/1"
DEFAULT_RUNS = {
    "seed 1": "data/server_retrieval/2026-09-16/v2_data/runs/c7-day-4/occupancy.npz",
    "seed 2": "data/server_retrieval/2026-09-17/runs/c7-day-4-s2/occupancy.npz",
    "seed 3": "data/server_retrieval/2026-09-17/runs/c7-day-4-s3/occupancy.npz",
}
DAY_HOURS = tuple(range(6, 24))
NIGHT_HOURS = tuple(range(0, 6))
#: 5 指標を家族 95% で扱う=指標あたり α=0.01(両側)→ 分位 0.995
FAMILY_ALPHA_PER_METRIC = 0.01
#: scipy が無いときの t(0.995, df) の表(df=1..10・Abramowitz & Stegun 表 26.10)
_T995 = {1: 63.657, 2: 9.925, 3: 5.841, 4: 4.604, 5: 4.032, 6: 3.707, 7: 3.499, 8: 3.355, 9: 3.250, 10: 3.169}


def t_quantile_995(df: int) -> float:
    """両側 99%(=片側 0.995)の t 分位。scipy があれば計算・無ければ表。"""
    try:
        from scipy.stats import t as _t  # type: ignore

        return float(_t.ppf(1.0 - FAMILY_ALPHA_PER_METRIC / 2.0, df))
    except Exception:  # noqa: BLE001 — 表で代替
        if df not in _T995:
            raise ValueError(f"t 分位の表は df 1..10 のみ(df={df})。scipy を入れる")
        return _T995[df]


def family_half_width_pct(cv: float, n_seeds: int) -> float:
    """平均の家族 95% 区間半幅(%)= t(0.995, n−1)·CV/√n·100。n=3・CV 0.0038 → 2.2 / 0.0325 → 18.6(第209)。"""
    return 100.0 * t_quantile_995(n_seeds - 1) * cv / math.sqrt(n_seeds)


def jsd_bits(p: np.ndarray, q: np.ndarray) -> float:
    """24 h シェアの Jensen–Shannon 距離²(bits)。fig_seed_pair と同じ定義。"""
    p = np.asarray(p, dtype=np.float64); q = np.asarray(q, dtype=np.float64)
    if p.sum() <= 0 or q.sum() <= 0:
        return 0.0
    p = p / p.sum(); q = q / q.sum(); m = (p + q) / 2.0

    def kl(a, b):
        mask = a > 0
        return float(np.sum(a[mask] * np.log2(a[mask] / b[mask])))

    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def load_tables(runs: Mapping[str, str] = DEFAULT_RUNS, world: str = "data/world/v2",
                axes: str = "tools/c7/area_axes_v0.json") -> dict[str, np.ndarray]:
    """ラベル → (24, n_area) の時×エリア表。"""
    amap, _gate = occ.build_map(world, axes)
    out: dict[str, np.ndarray] = {}
    for label, path in runs.items():
        s = occ.load_journal(path)
        out[label] = np.asarray(s.area_hour_table(amap), dtype=np.float64)
    return out


def summarize_ensemble(tables: Mapping[str, np.ndarray], inputs: Mapping[str, str] | None = None) -> dict[str, Any]:
    """数値だけの要約(描画・IO から分離=テスト用)。"""
    labels = list(tables.keys())
    n = len(labels)
    if n < 2:
        raise ValueError("seed は 2 本以上")
    stack = np.stack([np.asarray(tables[k], dtype=np.float64) for k in labels])  # (n, 24, n_area)
    five = stack.sum(axis=2)  # (n, 24)
    mu = five.mean(axis=0)
    sd = five.std(axis=0, ddof=1)
    cv = np.where(mu > 0, sd / np.maximum(mu, 1e-9), 0.0)
    n_area = stack.shape[2]

    # エリアごとの時別 CV → 中央値
    area_cv_median = []
    for j in range(n_area):
        a = stack[:, :, j]
        m = a.mean(axis=0)
        c = np.where(m > 0, a.std(axis=0, ddof=1) / np.maximum(m, 1e-9), 0.0)
        area_cv_median.append(float(np.median(c)))

    # 対ごとのエリア別シェア JSD
    pairs = []
    for i, k in itertools.combinations(range(n), 2):
        per_area = [jsd_bits(stack[i, :, j], stack[k, :, j]) for j in range(n_area)]
        pairs.append({
            "pair": [labels[i], labels[k]],
            "per_area_share_jsd_bits": per_area,
            "jsd_area_mean_bits": float(np.mean(per_area)),
            "five_area_rel_diff_max": float(np.max(np.abs(five[k] - five[i]) / np.maximum(five[i], 1e-9))),
        })
    pair_means = np.array([p["jsd_area_mean_bits"] for p in pairs])

    tq = t_quantile_995(n - 1)
    day_cv = cv[list(DAY_HOURS)]
    night_cv = cv[list(NIGHT_HOURS)]
    family = {
        "alpha_per_metric": FAMILY_ALPHA_PER_METRIC,
        "t_quantile": tq,
        "formula": "half_width_pct = 100 * t(0.995, n-1) * CV / sqrt(n)(第209 親再計算・5 指標 Bonferroni)",
        "day": {
            "hours": list(DAY_HOURS),
            "cv_median": float(np.median(day_cv)),
            "half_width_pct_median": family_half_width_pct(float(np.median(day_cv)), n),
            "cv_max": float(day_cv.max()),
            "half_width_pct_max": family_half_width_pct(float(day_cv.max()), n),
        },
        "night": {
            "hours": list(NIGHT_HOURS),
            "cv_median": float(np.median(night_cv)),
            "half_width_pct_median": family_half_width_pct(float(np.median(night_cv)), n),
            "cv_max": float(night_cv.max()),
            "half_width_pct_max": family_half_width_pct(float(night_cv.max()), n),
        },
    }
    cv_med, cv_max = float(np.median(cv)), float(cv.max())
    return {
        "schema": SCHEMA,
        "what": f"同一構成 × {n} seed の 5 エリア合計在圏の seed 間分散(帰無参照)。holdout 未使用。",
        "inputs": dict(inputs or {}),
        "labels": labels,
        "n_seeds": n,
        "n_pairs": len(pairs),
        "hours": list(range(24)),
        "five_area": {k: five[i].tolist() for i, k in enumerate(labels)},
        "five_area_mean": mu.tolist(),
        "five_area_sd_ddof1": sd.tolist(),
        "cv_hour": cv.tolist(),
        "cv_hour_median": cv_med,
        "cv_hour_max": cv_max,
        "cv_hour_argmax": int(cv.argmax()),
        "area_cv_median": area_cv_median,
        "pairs": pairs,
        "null_reference_jsd_bits": float(pair_means.mean()),
        "null_reference_jsd_bits_max_pair": float(pair_means.max()),
        "prereg_h1_line_bits": 0.0122,
        "family95": family,
        # 較正済みアンサンブルの raw CRPS は期待値で (1+1/M) 倍に膨らむ(Ferro 2008・M=3 で +33.3%)。
        # fair CRPS はその補正=広がり項に M/(M−1) を掛ける(Ferro 2014・tools/c7/prereg_v13.crps_fair_terms)。
        "raw_crps_inflation_if_calibrated": 1.0 + 1.0 / n,
        "fair_crps_spread_term_factor": n / (n - 1.0),
        "n_needed": {
            "formula": "N=(CV/r)^2 (L-B 答申 §5)",
            "median": {f"r={r}": (cv_med / r) ** 2 for r in (0.01, 0.02, 0.05)},
            "max": {f"r={r}": (cv_max / r) ** 2 for r in (0.01, 0.02, 0.05)},
        },
    }


def _parse_runs(items: list[str] | None) -> dict[str, str]:
    if not items:
        return dict(DEFAULT_RUNS)
    out: dict[str, str] = {}
    for it in items:
        label, _, path = it.partition("=")
        if not path:
            raise SystemExit(f"--run は label=path の形: {it!r}")
        out[label] = path
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", action="append", help="label=occupancy.npz(省略時は DEFAULT_RUNS の 3 seed)")
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--axes", default="tools/c7/area_axes_v0.json")
    ap.add_argument("--out", required=True, help="JSON の出力先(既存ファイルへは書かない)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists():
        print(f"refuse: {out} は既にある(既存の成果物を上書きしない)", file=sys.stderr)
        return 2
    runs = _parse_runs(a.run)
    tables = load_tables(runs, a.world, a.axes)
    d = summarize_ensemble(tables, {k: str(Path(v).as_posix()) for k, v in runs.items()})
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    f = d["family95"]
    print(f"seeds={d['n_seeds']} pairs={d['n_pairs']} cv_median={d['cv_hour_median']:.4f} "
          f"cv_max={d['cv_hour_max']:.4f}@{d['cv_hour_argmax']:02d}h "
          f"null_jsd={d['null_reference_jsd_bits']:.6f} (max pair {d['null_reference_jsd_bits_max_pair']:.6f}) "
          f"family95 day ±{f['day']['half_width_pct_median']:.2f}% night ±{f['night']['half_width_pct_max']:.1f}% "
          f"rawCRPS inflation x{d['raw_crps_inflation_if_calibrated']:.3f} (fair spread factor x{d['fair_crps_spread_term_factor']:.2f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
