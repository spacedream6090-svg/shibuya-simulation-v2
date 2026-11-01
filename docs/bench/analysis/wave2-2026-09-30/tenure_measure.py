"""第 2 波 §2A 項 2: 初期辺の在職期間のハッシュ(v1=旧・v2=修正)の検算と τ_rel の再逆算。

使い方(リポのルートで・``$D`` = この置き場)::

    python $D/tenure_measure.py all --out $D/item2_tenure.json

中身(全母集団 390,067 体・W16+W17・既定の密度 1.0・k 15・上限 13 週):
- ``tau``: 8b′ と同じ手順(``initial_edges(tau=None)`` → ラン開始時の「体ごとの 15 番目の辺の A」の中央値 →
  小数 3 桁で切り下げ)を v1/v2 で。1 日の終わりの値・τ の曲線も。
- ``check``: 版ごとに、在職 2 週未満の辺の割合(種別 × 向き=元 id の大小)・在職期間の U と同点の順のハッシュの
  順位相関(Spearman)・u→v と v→u で在職期間が同じか・初期辺の本数と満杯(15 本)の体の数(各版の τ で)。

絶対パスは書かない。壁時計は JSON に入れない。
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = np.argsort(np.argsort(a, kind="stable"), kind="stable").astype(np.float64)
    rb = np.argsort(np.argsort(b, kind="stable"), kind="stable").astype(np.float64)
    ra -= ra.mean()
    rb -= rb.mean()
    return float((ra * rb).sum() / math.sqrt((ra * ra).sum() * (rb * rb).sum()))


def _floor3(x: float) -> float:
    return math.floor(float(x) * 1000.0) / 1000.0


def run(world: str) -> dict[str, Any]:
    from shibuya.agents.population import load_population
    from shibuya.agents.weekly import load_weekly
    from shibuya.engine import relations as RL

    pop = load_population(world, n=None, seed=1)
    w = load_weekly(world).restrict_to(pop.source_agent_id)
    m = int(pop.n)
    src = np.asarray(pop.source_agent_id, dtype=np.int64)
    doc: dict[str, Any] = {"schema": "shibuya.bench/wave2-2026-09-30/tenure/1", "agents": m,
                           "tenure_weeks_max": RL.REL_TENURE_WEEKS, "k": RL.REL_K, "d": RL.REL_D,
                           "uniform_share_T_lt_2w": round(1.0 / 12.0, 4), "versions": {}}
    for ver in ("v1", "v2"):
        allx = RL.initial_edges(pop, w, m, tau=None, tenure_hash=ver)
        A0 = RL._activation(allx.n, allx.first, 0, 1.0, RL.REL_D)
        A1 = RL._activation(allx.n, allx.first, 1439, 1.0, RL.REL_D)
        t0 = RL.tau_from_edges(allx.u, A0, m)
        t1 = RL.tau_from_edges(allx.u, A1, m)
        T = -allx.first.astype(np.float64) / 10080.0
        su, sv = src[allx.u], src[allx.v]
        by: dict[str, Any] = {}
        for k in (1, 2, 3):
            s = allx.kind == k
            by[RL.REL_KIND_NAMES[k]] = {
                name: {"edges": int((s & msk).sum()), "share_T_lt_2w": round(float((T[s & msk] < 2).mean()), 4),
                       "median_T_w": round(float(np.median(T[s & msk])), 3)}
                for name, msk in (("src_u<src_v", su < sv), ("src_u>src_v", su > sv)) if (s & msk).any()}
        unit = RL._tenure_unit(su, sv, ver)
        tie = RL._pair_mix(su, sv)
        rho_all = _spearman(unit, tie.astype(np.float64))
        lt = su < sv
        rho_lt = _spearman(unit[lt], tie[lt].astype(np.float64))
        sym = bool(np.array_equal(RL._tenure_weeks(su, sv, RL.REL_TENURE_WEEKS, ver),
                                  RL._tenure_weeks(sv, su, RL.REL_TENURE_WEEKS, ver)))
        tau_raw = float(t0["tau"])
        tau_decl = RL.REL_TAU_BY_TENURE_HASH[ver]
        rows = {}
        for label, tau in (("declared", tau_decl), ("rederived_floor3", _floor3(tau_raw))):
            live = A0 >= tau
            deg = np.bincount(allx.u[live], minlength=m)
            rows[label] = {"tau": tau, "edges": int(live.sum()), "dropped_by_tau": int((~live).sum()),
                           "full_agents_15": int((deg >= RL.REL_K).sum()),
                           "full_share": round(float((deg >= RL.REL_K).mean()), 4),
                           "median_edges": float(np.median(deg)), "zero_agents": int((deg == 0).sum()),
                           "by_kind": {RL.REL_KIND_NAMES[k]: int((live & (allx.kind == k)).sum()) for k in (1, 2, 3)}}
        grid = [round(tau_raw + x, 4) for x in (-0.5, -0.1, -0.02, 0.0, 0.02, 0.1, 0.5)]
        curve = {}
        for tau in grid:
            deg = np.bincount(allx.u[A0 >= tau], minlength=m)
            curve[f"{tau:.4f}"] = {"median_edges": float(np.median(deg)), "share_15": round(float((deg >= 15).mean()), 4)}
        doc["versions"][ver] = {
            "edges_before_tau": int(allx.u.size),
            "tau_start_of_day": t0, "tau_end_of_day": t1,
            "tau_rederived_floor3": _floor3(tau_raw), "tau_declared_in_code": tau_decl,
            "A_quantiles_start": {q: round(float(np.percentile(A0, q)), 4) for q in (0, 10, 50, 90, 100)},
            "share_T_lt_2w_by_kind_and_direction": by,
            "spearman_U_vs_tie_hash_all_edges": round(rho_all, 5),
            "spearman_U_vs_tie_hash_src_u_lt_src_v": round(rho_lt, 5),
            "tenure_symmetric_u_v": sym,
            "net": rows, "curve_at_start": curve,
        }
        print(ver, "tau", round(tau_raw, 4), "→", _floor3(tau_raw), "rho", round(rho_all, 4), round(rho_lt, 4),
              {k: {d: x["share_T_lt_2w"] for d, x in v.items()} for k, v in by.items()},
              rows["declared"]["edges"], rows["declared"]["full_agents_15"], flush=True)
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("all",))
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    doc = run(args.world)
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
