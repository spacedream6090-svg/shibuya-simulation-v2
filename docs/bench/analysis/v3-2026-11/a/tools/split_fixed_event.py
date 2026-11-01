"""R-130 (a) 系ごとの時間を「刻みに比例する分」と「事象に比例する分」に分ける(measure_core.py の出力を読むだけ)。

方法(親の確認用に明記):
1. 系ごと・刻みごとの秒 t_s(T) を、その刻みの事象の数 x(T)(診断の列 calls・intents・moved・arrived・purchases・
   conversations)で最小二乗にかける: t_s(T) = a_s + b_s・x(T)。切片 a_s=事象が 0 の刻みでも払う秒=「刻みに比例する分」。
   係数は負にならないように、負になった列を外して解き直す(非負の最小二乗の簡易版)。
2. 検算: 事象のほぼ無い刻み(calls=0 かつ intents=0)の中央値=床 floor_s。
3. 体数 N を変えた 2〜3 点の a_s から、a_s(N) = c0 + c1・N を当てる(線形の仮定)。

使い方: python split_fixed_event.py data/bench/v3-2026-11-a n500_t60 n1500_t60 n5000_t60 > out.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REGS = ("calls", "intents", "moved", "arrived", "purchases", "conversations")


def nnls_simple(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """切片(列 0)は常に残し、ほかの係数が負なら外して解き直す。"""
    keep = list(range(X.shape[1]))
    while True:
        coef, *_ = np.linalg.lstsq(X[:, keep], y, rcond=None)
        neg = [keep[i] for i, c in enumerate(coef) if c < 0 and keep[i] != 0]
        if not neg:
            full = np.zeros(X.shape[1])
            full[keep] = coef
            return full
        keep = [k for k in keep if k not in neg]


def split(dir_: Path, label: str) -> dict:
    z = np.load(dir_ / f"{label}.ticks.npz", allow_pickle=False)
    names = [str(s) for s in z["systems"]]
    per = z["per_tick"]
    cols = [str(c) for c in z["diag_cols"]]
    diag = z["diag"]
    meta = json.loads((dir_ / f"{label}.json").read_text(encoding="utf-8"))
    T = per.shape[0]
    X = np.ones((T, 1 + len(REGS)))
    for i, r in enumerate(REGS):
        X[:, 1 + i] = diag[:T, cols.index(r)]
    idle = (diag[:T, cols.index("calls")] == 0) & (diag[:T, cols.index("intents")] == 0)
    out = {"label": label, "agents": meta["agents"], "ticks": T, "idle_ticks": int(idle.sum()), "systems": {}}
    tot_fixed = tot_all = 0.0
    for j, n in enumerate(names):
        y = per[:, j]
        coef = nnls_simple(X, y)
        a = float(coef[0])
        if a < 0:
            a = 0.0
        total = float(y.sum())
        fixed = min(total, a * T)
        floor = float(np.median(y[idle])) if idle.any() else float("nan")
        out["systems"][n] = {
            "total_s": round(total, 4), "ms_per_tick": round(total / T * 1e3, 4),
            "fixed_ms_per_tick": round(a * 1e3, 4), "fixed_share": round(fixed / total, 4) if total else 0.0,
            "floor_ms_idle_median": round(floor * 1e3, 4),
            "coef_ms_per_event": {r: round(float(coef[1 + i]) * 1e3, 6) for i, r in enumerate(REGS) if coef[1 + i] > 0},
        }
        tot_fixed += fixed
        tot_all += total
    out["sum_total_s"] = round(tot_all, 3)
    out["sum_fixed_s"] = round(tot_fixed, 3)
    out["fixed_share"] = round(tot_fixed / tot_all, 4)
    out["sum_fixed_ms_per_tick"] = round(tot_fixed / T * 1e3, 3)
    out["sum_ms_per_tick"] = round(tot_all / T * 1e3, 3)
    tick_sum = per.sum(axis=1)
    out["tick_sum_idle_median_ms"] = round(float(np.median(tick_sum[idle])) * 1e3, 3) if idle.any() else None
    out["tick_sum_p50_ms"] = round(float(np.median(tick_sum)) * 1e3, 3)
    out["tick_sum_max_ms"] = round(float(tick_sum.max()) * 1e3, 3)
    return out


def main() -> int:
    d = Path(sys.argv[1])
    res = [split(d, lb) for lb in sys.argv[2:]]
    # 体数への比例(固定費の a_s(N) = c0 + c1・N)
    fit = {}
    if len(res) >= 2:
        Ns = np.array([r["agents"] for r in res], dtype=float)
        sysnames = sorted(set().union(*[r["systems"].keys() for r in res]))
        for n in sysnames + ["__sum__"]:
            if n == "__sum__":
                ys = np.array([r["sum_fixed_ms_per_tick"] for r in res])
            else:
                ys = np.array([r["systems"].get(n, {}).get("fixed_ms_per_tick", 0.0) for r in res])
            A = np.vstack([np.ones_like(Ns), Ns]).T
            c, *_ = np.linalg.lstsq(A, ys, rcond=None)
            fit[n] = {"c0_ms": round(float(c[0]), 4), "c1_ms_per_agent": round(float(c[1]), 8),
                      "at_350k_ms": round(float(c[0] + c[1] * 350_000), 2),
                      "at_390067_ms": round(float(c[0] + c[1] * 390_067), 2), "points": ys.round(4).tolist()}
    print(json.dumps({"runs": res, "fixed_vs_N": fit}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
