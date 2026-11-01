"""第 3 期 3-2(tm32): 性能の前後(刻みあたりの時間=予算 P4 の読み)と窓の待ち行列だけの手間。

``run``: 10e の ``byte_check_10e.py one --config w6_v3_default``(5,000 体・seed 1・1 日・テープつき)を、HEAD の写しの src と
作業木の src(既定 W=60・腕 W=5)で交互に ``--reps`` 回ずつ 1 本ずつ順に回し(並べない)、ランの壁時計 ``run_wall_s`` を
集める。刻みあたり = run_wall_s ÷ 1,440。``queue``: 窓の待ち行列だけ(系を呼ばない空の刻みの事象)で 1 日ぶんの窓を回した
時間(幅ごと)。絶対パスは書かない。

    python $D/perf_tm32.py run --head-src <HEAD の写しの src> --reps 3 --scratch $W/perf --out $D/../perf_tm32.json
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
BC = REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "10e" / "byte_check_10e.py"
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from shibuya.core.time_consts import NS_PER_STEP, STEPS_PER_DAY  # noqa: E402

STEPS = STEPS_PER_DAY


def _one(src: Path, width: str, tape: Path) -> dict:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONPATH=str(src))
    env.pop("SHIBUYA_BATCH_WIDTH_S", None)
    if width:
        env["SHIBUYA_BATCH_WIDTH_S"] = width
    if src != REPO / "src":
        env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"
    r = subprocess.run([sys.executable, str(BC), "one", "--config", "w6_v3_default", "--tape", str(tape)],
                       capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:])
    d = json.loads(r.stdout.strip().splitlines()[-1])
    return {"final": d["final"], "calls": d["calls"], "run_wall_s": d["run_wall_s"], "wall_s": d["wall_s"]}


def cmd_run(a: argparse.Namespace) -> int:
    sides = {"head": (Path(a.head_src).resolve(), ""), "w60": (REPO / "src", ""), "w5": (REPO / "src", "5")}
    sc = Path(a.scratch)
    rows: dict[str, list[dict]] = {k: [] for k in sides}
    for i in range(int(a.reps)):
        for name, (src, w) in sides.items():  # 交互に(同じ時間帯の負荷を等しく受ける)
            rows[name].append(_one(src, w, sc / f"{name}_{i}"))
            print(name, i, rows[name][-1], flush=True)
    summ = {}
    for name, rs in rows.items():
        ws = [r["run_wall_s"] for r in rs]
        summ[name] = {"run_wall_s": ws, "median_s": statistics.median(ws),
                      "ms_per_step_median": statistics.median(ws) * 1000.0 / STEPS,
                      "finals": sorted({r["final"] for r in rs}), "calls": sorted({r["calls"] for r in rs})}
    base = summ["head"]["median_s"]
    for name in summ:
        summ[name]["vs_head_pct"] = (summ[name]["median_s"] / base - 1.0) * 100.0
    doc = {"schema": "shibuya.bench/tm32/perf/1", "config": "w6_v3_default(5,000 体・seed 1・1 日・テープつき)",
           "how": "byte_check_10e.py one を 1 本ずつ順に(並べない)・head/w60/w5 を交互に reps 回。刻みあたり=run_wall_s ÷ 1,440",
           "reps": int(a.reps), "summary": summ, "queue": queue_only()}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summ, ensure_ascii=False))
    return 0


def queue_only() -> dict:
    """窓の待ち行列だけの手間(空の刻みの事象で 1 日ぶん・幅ごと)。"""
    from shibuya.engine import batching as BA

    out = {}
    for w in (60, 30, 10, 5, 1):
        q = BA.WindowQueue(width_s=w, start_ns=0)
        end = STEPS * NS_PER_STEP

        def step(t, a, sq, q=q, end=end):  # noqa: ANN001, ANN202
            if t + NS_PER_STEP < end:
                q.schedule(t + NS_PER_STEP, BA.WORLD, BA.KIND_STEP)

        q.register(0, "step", step)
        q.schedule(0, BA.WORLD, 0)
        t0 = time.perf_counter()
        while q.head_ns < end:
            q.run_window()
        dt = time.perf_counter() - t0
        out[str(w)] = {"day_ms": round(dt * 1e3, 1), "us_per_step": round(dt / STEPS * 1e6, 1),
                       "windows": q.window_counts["windows"]}
    return out


def main(argv=None) -> int:  # noqa: ANN001
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("run")
    sp.add_argument("--head-src", required=True)
    sp.add_argument("--reps", type=int, default=3)
    sp.add_argument("--scratch", required=True)
    sp.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"run": cmd_run}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
