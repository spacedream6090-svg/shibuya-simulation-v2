"""第 2 期 2-2(親の判断 10-14 の 1): 5,000 体・1 日の腕 distance で、気づく抽選の刻みあたりの時間を測る。

ランの中の ``ProximityRule.notice_u``(``philox_array`` で範囲の中の辺をまとめて引く)を包み、刻みごとに
(1) いまの形の時間 (2) 同じ組を 1 組ずつ ``stream`` で引く前の形の時間 を測り、値が全部同じことも確かめる。
壁時計は決定論でない(同じ PC・ほかの作業と同居)。絶対パスは書かない。

    PYTHONPATH=src python docs/bench/analysis/wallbounce-1012/prox22/tools/notice_cost.py --out <記録の置き場>/notice_cost.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

POLICY_KW = {"mock": {}, "classical": {"policy": "classical", "chooser": "classical"}}


def _q(v: list[float], p: float) -> float:
    return float(np.quantile(np.asarray(v, dtype=np.float64), p)) if v else 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--policies", default="mock,classical")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from shibuya import cli
    from shibuya.core.rng import k19_counters, stream
    from shibuya.engine import proximity as P

    P.set_arm("distance")
    P.set_d(2.0)
    orig = P.ProximityRule.notice_u
    rows = {}
    for pol in args.policies.split(","):
        rec: dict[int, list[float]] = {}

        def timed(self, T, a, b):
            t0 = time.perf_counter()
            out = orig(self, T, a, b)
            t1 = time.perf_counter()
            aa = np.atleast_1d(np.asarray(a, dtype=np.int64))
            bb = np.atleast_1d(np.asarray(b, dtype=np.int64))
            tk = self.time_key(T)
            t2 = time.perf_counter()
            ref = np.array([stream(self.seed, P.NOTICE_DOMAIN, *k19_counters(tk, int(x), int(y))).random()
                            for x, y in zip(aa.tolist(), bb.tolist())])  # 逐次: 組の数ぶん(前の形=計測)
            t3 = time.perf_counter()
            if not np.array_equal(out, ref):
                raise AssertionError(f"配列で引いた値と 1 組ずつの値が違う(刻み {T})")
            r = rec.setdefault(int(T), [0, 0.0, 0.0])
            r[0] += int(aa.size)
            r[1] += t1 - t0
            r[2] += t3 - t2
            return out

        P.ProximityRule.notice_u = timed  # type: ignore[method-assign]
        try:
            t0 = time.perf_counter()
            res = cli.run(n_agents=args.agents, seed=1, world_dir=args.world, vocab_version="v3", memory="on",
                          relations="on", **POLICY_KW[pol])
            wall = time.perf_counter() - t0
        finally:
            P.ProximityRule.notice_u = orig  # type: ignore[method-assign]
        n = [v[0] for v in rec.values()]
        vec = [1e3 * v[1] for v in rec.values()]
        loop = [1e3 * v[2] for v in rec.values()]
        rows[pol] = {
            "agents": args.agents, "final16": res.final_hash[:16], "llm_calls": int(res.llm_calls),
            "steps_with_draws": len(rec), "draws_total": int(sum(n)),
            "draws_per_step_mean": round(float(np.mean(n)) if n else 0.0, 1), "draws_per_step_max": int(max(n or [0])),
            "vector_ms_per_step_mean": round(float(np.mean(vec)) if vec else 0.0, 4),
            "vector_ms_per_step_p95": round(_q(vec, 0.95), 4), "vector_ms_per_step_max": round(max(vec or [0.0]), 4),
            "vector_s_per_day": round(sum(vec) / 1e3, 3),
            "loop_ms_per_step_mean": round(float(np.mean(loop)) if loop else 0.0, 4),
            "loop_ms_per_step_p95": round(_q(loop, 0.95), 4), "loop_ms_per_step_max": round(max(loop or [0.0]), 4),
            "loop_s_per_day": round(sum(loop) / 1e3, 3),
            "values_equal": True, "run_wall_s_nondeterministic": round(wall, 1),
        }
        print(pol, rows[pol], flush=True)
    doc = {"schema": "shibuya.bench/prox22/notice_cost/1",
           "note": "腕 distance・d=2 m・語彙 v3・記憶 on・関係 on・seed 1。vector=philox_array でまとめて引く(いまの形)・"
                   "loop=同じ組を 1 組ずつ stream で引く(前の形)。値は全刻みで同じ(違えば止まる)。壁時計は決定論でない",
           "rows": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
