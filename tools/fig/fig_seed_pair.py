# -*- coding: utf-8 -*-
"""図 4: 同一構成 × seed 違い(c7-day-4 seed 1 vs seed 2・390,067 体)の在圏 24 時間と seed 間の変動係数。

D-46(アンサンブルの規模)・D-70(次のゲート)・G-8(初回 8 seed=expedient)を数字で決めるための図。
数え方は図 1 と同じ(``occupancy_series.build_map`` → ``c7lib.OccupancySeries.area_hour_table``)で、
本スクリプトは 2 ランの差と CV を出して描くだけ。holdout は開けない・使わない。

再現: ``python tools/fig/fig_seed_pair.py --out docs/bench/figures``
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "c7"))
import _style as st  # noqa: E402
import occupancy_series as occ  # noqa: E402

STEM = "fig4_seed_pair"
DEFAULT_RUNS = {
    "seed 1": "data/server_retrieval/2026-09-16/v2_data/runs/c7-day-4/occupancy.npz",
    "seed 2": "data/server_retrieval/2026-09-17/runs/c7-day-4-s2/occupancy.npz",
}


def load_pair(runs: Mapping[str, str] = DEFAULT_RUNS, world: str = "data/world/v2",
              axes: str = "tools/c7/area_axes_v0.json") -> dict[str, Any]:
    """2 ランの 時×エリア表を読み、合計・相対差・CV(n=2)・エリア別 24h シェアの JSD を出す。"""
    amap, _gate = occ.build_map(world, axes)
    tables = {}
    for label, path in runs.items():
        s = occ.load_journal(path)
        tables[label] = np.asarray(s.area_hour_table(amap), dtype=np.float64)  # (24, n_area)
    (l1, t1), (l2, t2) = list(tables.items())
    return summarize(l1, t1, l2, t2, {k: st.rel(v) for k, v in runs.items()})


def summarize(l1: str, t1: np.ndarray, l2: str, t2: np.ndarray, inputs: Mapping[str, str]) -> dict[str, Any]:
    """数値だけの要約(描画から分離=テスト用)。"""
    five1, five2 = t1.sum(axis=1), t2.sum(axis=1)
    mu = (five1 + five2) / 2.0
    sd = np.abs(five1 - five2) / math.sqrt(2.0)
    cv = np.where(mu > 0, sd / np.maximum(mu, 1e-9), 0.0)
    rel = np.where(five1 > 0, (five2 - five1) / np.maximum(five1, 1e-9), 0.0)

    def jsd(p: np.ndarray, q: np.ndarray) -> float:
        p = p / p.sum(); q = q / q.sum(); m = (p + q) / 2.0
        def kl(a, b):
            mask = a > 0
            return float(np.sum(a[mask] * np.log2(a[mask] / b[mask])))
        return 0.5 * kl(p, m) + 0.5 * kl(q, m)

    n_area = t1.shape[1]
    per_area_jsd = [jsd(t1[:, j], t2[:, j]) for j in range(n_area)]
    area_cv_median = []
    for j in range(n_area):
        a, b = t1[:, j], t2[:, j]
        m = (a + b) / 2.0
        c = np.abs(a - b) / math.sqrt(2.0) / np.maximum(m, 1e-9)
        area_cv_median.append(float(np.median(c)))
    cv_med, cv_max = float(np.median(cv)), float(cv.max())
    return {
        "schema": "shibuya.tools.fig/seed_pair/1",
        "figure": STEM,
        "what": "同一構成 × seed 1/2(390,067 体×1 シミュ日)の 5 エリア合計在圏と seed 間 CV。holdout 未使用。",
        "inputs": dict(inputs),
        "labels": [l1, l2],
        "hours": list(range(24)),
        "five_area": {l1: five1.tolist(), l2: five2.tolist()},
        "rel_diff": rel.tolist(),
        "cv_hour": cv.tolist(),
        "cv_hour_median": cv_med,
        "cv_hour_max": cv_max,
        "cv_hour_argmax": int(cv.argmax()),
        "area_cv_median": area_cv_median,
        "per_area_share_jsd_bits": per_area_jsd,
        "per_area_share_jsd_mean": float(np.mean(per_area_jsd)),
        "prereg_h1_line_bits": 0.0122,
        "n_needed": {
            "formula": "N=(CV/r)^2 (L-B 答申 §5)・d8=83.6*CV",
            "median": {f"r={r}": (cv_med / r) ** 2 for r in (0.01, 0.02, 0.05)},
            "max": {f"r={r}": (cv_max / r) ** 2 for r in (0.01, 0.02, 0.05)},
            "d8_median_pct": 83.6 * cv_med,
            "d8_max_pct": 83.6 * cv_max,
        },
    }


def draw(d: Mapping[str, Any]):
    """データ dict → Figure(上: 在圏 2 本・中: 相対差・下: CV)。"""
    import matplotlib.pyplot as plt

    st.use_style()
    from matplotlib.ticker import FuncFormatter
    fmt = FuncFormatter(lambda v, _pos: st.thousands(v))
    accent = st.CAT[0]
    l1, l2 = d["labels"]
    hours = np.asarray(d["hours"])
    y1, y2 = np.asarray(d["five_area"][l1]), np.asarray(d["five_area"][l2])
    fig, axes = plt.subplots(3, 1, figsize=(10.5, 9.2), sharex=True,
                             gridspec_kw={"height_ratios": [3.2, 1.3, 1.3]})
    ax = axes[0]
    ax.plot(hours, y1, color=st.ORDINAL_BLUE3[2], lw=2.2, label=l1)
    ax.plot(hours, y2, color=st.ORDINAL_BLUE3[0], lw=1.8, ls="--", label=l2)
    ax.set_ylabel(st.T("在圏(人・5 エリア合計)", "presence (5 areas)"))
    ax.yaxis.set_major_formatter(fmt)
    ax.legend(loc="upper left", frameon=False)
    ax.set_title(st.T("図4 同一構成 × seed 1 / seed 2 の在圏 24 時間(390,067 体)",
                      "Fig. 4 Same configuration, seed 1 vs seed 2 (390,067 agents)"), loc="left")

    ax = axes[1]
    rel = np.asarray(d["rel_diff"]) * 100.0
    ax.bar(hours, rel, color=[accent if abs(v) >= 2 else st.MUTED for v in rel], width=0.7)
    ax.axhline(0, color=st.MUTED, lw=0.8)
    ax.set_ylabel(st.T("相対差 seed2−seed1 (%)", "rel. diff (%)"))
    ax.annotate(st.T(f"最大 {rel[np.abs(rel).argmax()]:+.2f}% @{int(np.abs(rel).argmax()):02d}時・中央値 {np.median(np.abs(rel)):.2f}%",
                     f"max {rel[np.abs(rel).argmax()]:+.2f}% @{int(np.abs(rel).argmax()):02d}h"),
                xy=(0.99, 0.9), xycoords="axes fraction", ha="right", va="top", fontsize=8.5, color=st.MUTED)

    ax = axes[2]
    cv = np.asarray(d["cv_hour"]) * 100.0
    ax.plot(hours, cv, color=accent, marker="o", ms=3.5, lw=1.4)
    ax.set_ylabel(st.T("CV(n=2)(%)", "CV (n=2) (%)"))
    ax.set_xlabel(st.T("世界内の時刻(時)", "hour"))
    ax.set_xticks(range(0, 24, 3))
    nn = d["n_needed"]
    ax.annotate(st.T(f"CV 中央値 {d['cv_hour_median']*100:.2f}%・最大 {d['cv_hour_max']*100:.2f}% @{d['cv_hour_argmax']:02d}時 → "
                     f"N(r=2%)= {nn['median']['r=0.02']:.2f}(中央値)/ {nn['max']['r=0.02']:.1f}(最大)",
                     f"CV median {d['cv_hour_median']*100:.2f}%, max {d['cv_hour_max']*100:.2f}%"),
                xy=(0.99, 0.9), xycoords="axes fraction", ha="right", va="top", fontsize=8.5, color=st.MUTED)

    st.note(fig, [
        st.T("同一構成(390,067 体・v2.1・attendance 1.0・7×Qwen3-8B INT8・温度 0.7)・seed だけ違う 2 ラン。5 エリア写像 area_axes_v0 は expedient。",
             "Same configuration, seeds differ. area map is expedient."),
        st.T(f"エリア別 24h シェアの seed 間 JSD 平均 {d['per_area_share_jsd_mean']:.6f} bits(事前登録 H1 の線 0.0122 の 1/{0.0122/max(d['per_area_share_jsd_mean'],1e-12):.0f})。"
             "N=(CV/r)² は L-B 答申 §5。KDDI holdout は未開封・未使用。数値は fig4_seed_pair.json。",
             "Seed JSD vs prereg H1 line. Holdout unused."),
    ])
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    return fig


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="図 4: seed 1 vs seed 2 の在圏と seed 間 CV")
    ap.add_argument("--out", default="docs/bench/figures")
    ap.add_argument("--run1", default=DEFAULT_RUNS["seed 1"])
    ap.add_argument("--run2", default=DEFAULT_RUNS["seed 2"])
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--axes", default="tools/c7/area_axes_v0.json")
    args = ap.parse_args(argv)
    d = load_pair({"seed 1": args.run1, "seed 2": args.run2}, args.world, args.axes)
    fig = draw(d)
    paths = st.save(fig, args.out, STEM)
    d["outputs"] = paths
    st.write_sidecar(args.out, STEM, d)
    print(f"cv_median={d['cv_hour_median']:.4f} cv_max={d['cv_hour_max']:.4f}@{d['cv_hour_argmax']:02d} "
          f"jsd_mean={d['per_area_share_jsd_mean']:.6f} -> {paths['png']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
