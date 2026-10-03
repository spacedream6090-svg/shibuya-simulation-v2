"""10c 試験 (iii)・(iv) の控え: 率を上げた合成世界で stateful と counter の件数の分布を 5 seed で比べる。

2 段で測る(どちらも GPU 不要・合成世界):
- ``process``: 過程だけ(``SalientProcess`` + ``PublicServiceDispatchProcess``・25 セル・1,000 体・1 日・体は動かない)。
  テスト ``tests/engine/processes/test_rng_scheme_10c.py::test_counts_have_the_same_order_under_a_x1000_rate`` と同じ形。
- ``run_day``: mock の 1 日ラン(合成世界 139 セル・2,000 体・``salient_rate_per_10k`` = 既定 3.0 の ×1000)。
- ``default_rate``: 既定の率(3/万/日)の合成世界のランで、seed 1〜5 の件数(実世界の seed 1 は byte-check の記録)。

判定(検収後の直し・テストと同じ):
- 主: tick ごとの件数(5 seed × 1,440 tick)を既知の答え(ポアソン・期待値 = 率 × 体数 / 1 日の tick 数)と比べる
  z 検定。合計の z と分散の指数の z がどちらも |z| ≤ 3。
- 副(記録だけ): 平均の差 ≤ 2 × (2 方式の seed 間の標準偏差の大きい方)・分散の比 ≤ 10。5 seed では誤報が約 5%・
  10% の率の違いを見逃す率が約 7 割と弱い(検収 T3)。

使い方: ``python docs/bench/analysis/wallbounce-1003/10c/count_dist_x1000.py --out <この置き場>/count_dist_x1000.json``
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO / "tests"))

SEEDS = (1, 2, 3, 4, 5)
RATE_X1000 = 3.0 * 1_000.0
MEAN_GAP_SD = 2.0
VAR_RATIO_MAX = 10.0
Z_MAX = 3.0


def poisson_z(x: np.ndarray, lam: float) -> tuple[float, float]:
    """tick ごとの件数 → (合計の z, 分散の指数の z)。テストの ``poisson_z`` と同じ式。"""
    x = np.asarray(x, dtype=np.float64).ravel()
    n = x.size
    z_sum = (x.sum() - n * lam) / np.sqrt(n * lam)
    m = x.mean()
    disp = float(((x - m) ** 2).sum() / m) if m > 0 else float("nan")
    return float(z_sum), float((disp - (n - 1)) / np.sqrt(2.0 * (n - 1)))


def _judge(a: list[float], b: list[float]) -> dict:
    ma, mb = float(np.mean(a)), float(np.mean(b))
    va, vb = float(np.var(a, ddof=1)), float(np.var(b, ddof=1))
    sd = float(max(np.sqrt(va), np.sqrt(vb)))
    ratio = float(max(va, vb) / max(min(va, vb), 1e-12))
    return {
        "stateful": a, "counter": b,
        "mean_stateful": round(ma, 3), "mean_counter": round(mb, 3),
        "var_stateful": round(va, 3), "var_counter": round(vb, 3),
        "mean_gap": round(abs(ma - mb), 3), "gap_line": round(MEAN_GAP_SD * sd, 3),
        "var_ratio": round(ratio, 3), "var_ratio_line": VAR_RATIO_MAX,
        "ok": bool(abs(ma - mb) <= MEAN_GAP_SD * sd and ratio <= VAR_RATIO_MAX),
    }


def process_level() -> dict:
    from engine.processes.conftest import make_agents, make_world
    from shibuya.engine.processes.civic import PublicServiceDispatchProcess
    from shibuya.engine.processes.salient import SalientProcess

    rows: dict[str, list[tuple[int, int, float]]] = {}
    ticks: dict[str, list[np.ndarray]] = {}
    for scheme in ("stateful", "counter"):
        rows[scheme] = []
        ticks[scheme] = []
        for seed in SEEDS:
            world = make_world(25, seed=seed)
            agents, _ = make_agents(world, 1_000, seed=seed)
            d = PublicServiceDispatchProcess(world, master_seed=seed, rng_scheme=scheme)
            sp = SalientProcess(world, agents, master_seed=seed, dispatch=d, rate_per_10k_per_day=RATE_X1000,
                                rng_scheme=scheme)
            per = np.zeros(1_440, dtype=np.int64)
            for t in range(1_440):
                before = sp.n_collapse
                sp.step(t)
                per[t] = sp.n_collapse - before
            ticks[scheme].append(per)
            rows[scheme].append((sp.n_collapse, d.n_dispatched, d.delay_minutes_total / max(1, d.n_dispatched)))
    lam = RATE_X1000 * (1_000 / 10_000.0) / 1_440
    main = {}
    for scheme in ("stateful", "counter"):
        x = np.concatenate(ticks[scheme])
        z_sum, z_disp = poisson_z(x, lam)
        main[scheme] = {
            "n_ticks": int(x.size), "total": int(x.sum()), "expected_total": round(lam * x.size, 3),
            "mean_per_tick": round(float(x.mean()), 5), "var_per_tick": round(float(x.var(ddof=1)), 5),
            "expected_per_tick": round(lam, 5),
            "z_sum": round(z_sum, 3), "z_dispersion": round(z_disp, 3),
            "ok": bool(abs(z_sum) <= Z_MAX and abs(z_disp) <= Z_MAX),
        }
    return {
        "main_poisson_z": main,
        "secondary_5seed": {
            name: _judge([float(r[j]) for r in rows["stateful"]], [float(r[j]) for r in rows["counter"]])
            for j, name in enumerate(("collapse", "dispatched", "mean_delay_min"))
        },
    }


def run_level(n_agents: int, rate: float | None) -> dict:
    from shibuya.engine.run import run_day

    rows: dict[str, list[dict]] = {}
    for scheme in ("stateful", "counter"):
        rows[scheme] = []
        for seed in SEEDS:
            t0 = time.perf_counter()
            res = run_day(n_agents=n_agents, seed=seed, n_cells=139, ticks=1_440, checkpoint_every=360,
                          salient_rate_per_10k=rate, rng_scheme=scheme)
            pc = res.process_counters
            rows[scheme].append({
                "seed": seed, "salient_events": int(res.salient_events), "collapse": int(pc["salient.collapse"]),
                "dispatches": int(res.dispatches), "arrived": int(pc["dispatch.arrived"]),
                "mean_delay_min": round(float(pc["dispatch.mean_delay_min"]), 3), "noticed": int(res.noticed),
                "calls": int(res.llm_calls), "final": res.final_hash[:16],
                "wall_s": round(time.perf_counter() - t0, 1),
            })
            print(scheme, seed, rows[scheme][-1], flush=True)
    keys = ("collapse", "dispatches", "salient_events", "noticed", "mean_delay_min", "calls")
    main = {}
    if rate is not None:
        # 1 日の合計(5 seed)を既知の答え(体数 × 率 / 10,000 × 5)と比べる z。引いた数は範囲の中の体の数で
        # 切られる(1 tick に引くのは 0〜数件なので、この規模では切られない見込み=宣言)
        exp = n_agents * rate / 10_000.0 * len(SEEDS)
        for scheme in ("stateful", "counter"):
            tot = sum(r["collapse"] for r in rows[scheme])
            z = (tot - exp) / np.sqrt(exp)
            main[scheme] = {"total": int(tot), "expected_total": exp, "z_sum": round(float(z), 3),
                            "ok": bool(abs(z) <= Z_MAX)}
    return {
        "main_poisson_z_total": main,
        "rows": rows,
        "judge": {k: _judge([float(r[k]) for r in rows["stateful"]], [float(r[k]) for r in rows["counter"]])
                  for k in keys},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--agents", type=int, default=2_000)
    args = ap.parse_args()
    doc = {
        "how": ("合成世界・GPU 不要。process=過程だけ(25 セル・1,000 体・体は動かない)/ run_day=mock の 1 日"
                f"(139 セル・{args.agents} 体)。率は既定 3.0/万/日の ×1000 と既定のまま。5 seed(1〜5)。"),
        "line_main": (f"主: tick ごとの件数をポアソン(期待値 = 率 × 体数 / 1,440)と比べ、合計の z と分散の指数の z が"
                      f" |z| ≤ {Z_MAX}(run_day の段は 1 日の合計の z だけ)"),
        "line_secondary": f"副(記録だけ): 平均の差 ≤ {MEAN_GAP_SD} × seed 間の標準偏差(2 方式の大きい方)・分散の比 ≤ {VAR_RATIO_MAX}",
        "process_x1000": process_level(),
    }
    doc["run_day_x1000"] = run_level(args.agents, RATE_X1000)
    doc["run_day_default_rate"] = run_level(args.agents, None)
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
