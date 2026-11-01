"""段 5-1b 検収 M2: 19 構成を 2 日回して進めない体刻み(Kladek の係数 0 で動けなかった移動中の体 × 刻み)を日ごとに数える
(道具・ランの外・読むだけの包み=結果は変えない)。

    python docs/bench/analysis/spatial-2026-10/sp1b/tools/sp1b_2day.py side --out <出力>   # 19 構成を 1 本ずつ(別のプロセス)
    python docs/bench/analysis/spatial-2026-10/sp1b/tools/sp1b_2day.py one --config w6_golden_null_arm

腕は環境変数(SHIBUYA_SPACE・SHIBUYA_NAV1_DENSITY)。逐次ループ宣言: 構成の数ぶん(道具・ランの外)。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4].parent
WAVE2 = REPO / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"
STEPS_PER_DAY = 1440


def _configs() -> dict[str, dict[str, Any]]:
    spec = importlib.util.spec_from_file_location("wave2_bytecheck", WAVE2)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.configs()


def cmd_one(a: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.engine import resolve as R
    from shibuya.engine.space import nav1 as N

    st: dict[str, Any] = {"tick": -1, "by_day": {}, "by_cell_day": {}, "max_conc": {}, "jam_steps": {}}
    orig_apply = R.apply

    def apply(plan_confirmed, losers, agents, world, tick, *aa, **kw):  # noqa: ANN001
        st["tick"] = int(tick)
        return orig_apply(plan_confirmed, losers, agents, world, tick, *aa, **kw)

    R.apply = apply
    orig_k = N.NavSpace.kladek_factor

    def kf(self, cell, density):  # noqa: ANN001
        fac = orig_k(self, cell, density)
        jam = np.asarray(fac) <= 0.0
        n = int(jam.sum())
        if n:
            day = str(int(st["tick"]) // STEPS_PER_DAY)
            st["by_day"][day] = st["by_day"].get(day, 0) + n
            st["max_conc"][day] = max(st["max_conc"].get(day, 0), n)
            st["jam_steps"][day] = st["jam_steps"].get(day, 0) + 1
            cc, nn = np.unique(np.asarray(cell, dtype=np.int64)[jam], return_counts=True)
            d = st["by_cell_day"].setdefault(day, {})
            for c, k in zip(cc.tolist(), nn.tolist()):
                d[str(c)] = d.get(str(c), 0) + int(k)
        return fac

    N.NavSpace.kladek_factor = kf
    kw = dict(_configs()[a.config])
    t0 = time.perf_counter()
    res = cli.run(n_agents=a.agents, seed=a.seed, world_dir=a.world, sim_days=2, **kw)
    sp = res.run_manifest_fields()["space"]
    top = {day: sorted(d.items(), key=lambda kv: -kv[1])[:3] for day, d in st["by_cell_day"].items()}
    print(json.dumps({"config": a.config, "space": sp["effective"],
                      "density_mode": (sp.get("navmesh") or {}).get("density_mode"),
                      "final": res.final_hash[:16], "calls": int(res.llm_calls),
                      "jam_meter": (sp.get("meter") or {}).get("jammed_agent_steps"),
                      "jam_by_day": st["by_day"], "jam_max_concurrent_by_day": st["max_conc"],
                      "jam_steps_by_day": st["jam_steps"], "jam_top_cells_by_day": top,
                      "wall_s": round(time.perf_counter() - t0, 1)}, ensure_ascii=False))
    return 0


def cmd_side(a: argparse.Namespace) -> int:
    names = [s for s in a.only.split(",") if s] if a.only else list(_configs())
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    out = Path(a.out)
    runs: dict[str, Any] = json.loads(out.read_text(encoding="utf-8"))["runs"] if out.exists() else {}
    for name in names:
        if name in runs and "error" not in runs[name]:
            continue
        r = subprocess.run([sys.executable, str(Path(__file__)), "one", "--config", name, "--world", a.world,
                            "--agents", str(a.agents), "--seed", str(a.seed)],
                           capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        runs[name] = json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else {"error": r.stderr[-2000:]}
        print(name, runs[name].get("final"), runs[name].get("jam_by_day"), flush=True)
        doc = {"agents": a.agents, "seed": a.seed, "days": 2,
               "env": {k: env[k] for k in ("SHIBUYA_SPACE", "SHIBUYA_NAV1_DENSITY") if k in env}, "runs": runs}
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("one", "side"):
        s = sub.add_parser(name)
        s.add_argument("--world", default="data/world/v2")
        s.add_argument("--agents", type=int, default=5000)
        s.add_argument("--seed", type=int, default=1)
        if name == "one":
            s.add_argument("--config", required=True)
        else:
            s.add_argument("--only", default="")
            s.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
