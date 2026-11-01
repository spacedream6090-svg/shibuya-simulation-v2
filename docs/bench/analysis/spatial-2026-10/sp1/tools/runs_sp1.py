"""第 5 期 空間の段 1: 動いた量と性能の控え(1 日と 2 日のラン・再開=通し・壁時計・1 刻み・最大の作業集合・呼数・移動の計器)。

``one`` は 1 本回して 1 行の JSON を出す(別のプロセス): final・呼数・壁時計・1 刻み・ピークの作業集合・manifest の
``space``(移動の計器)・行動の件数・セル間の移動の数(刻みごとにセルが変わった体の延べ=``engine.resolve.apply`` を包んで
数える)・checkpoint の列。``--stop``/``--resume`` で止めて書く・続きから回す(再開=通しの確かめ)。``side`` は ``--runs``
(label;world;days;space;stop をコンマで)を 1 本ずつ回す(5,000 体のランは同時に回さない)。絶対パスは書かない。

    python $D/runs_sp1.py side --runs "nav1_1d;data/world/v2_stage_5-1;1;nav1;" --scratch <作業用> --out $D/runs_sp1.json

逐次ループ宣言: ランの数ぶん(道具・ランの外)。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "pop43" / "tools"))


def _peak() -> int:
    from runs_pop43 import _peak_working_set_bytes  # noqa: PLC0415

    return _peak_working_set_bytes()


def cmd_one(a: argparse.Namespace) -> int:
    import numpy as np

    from shibuya import cli
    from shibuya.engine import resolve as R

    orig = R.apply
    moves = {"cell_changes": 0, "agent_ticks": 0, "density_stage_changes": 0, "density_stage_hist": {}}
    prev_stage: dict[str, Any] = {"v": None}

    def wrapped(plan_confirmed, losers, agents, world, tick, *args, **kw):
        c0 = np.asarray(agents.registry.cell).copy()
        out = orig(plan_confirmed, losers, agents, world, tick, *args, **kw)
        c1 = np.asarray(agents.registry.cell)
        moves["cell_changes"] += int(((c0 != c1) & (c0 >= 0) & (c1 >= 0)).sum())
        moves["agent_ticks"] += int(c1.size)
        # 〔段 1 の検収 M4〕密度の段の変化の数(セル × 刻み)と段の分布
        st = np.asarray(world.cells.density_stage).copy()
        if prev_stage["v"] is not None:
            moves["density_stage_changes"] += int((st != prev_stage["v"]).sum())
        prev_stage["v"] = st
        for k, v in zip(*np.unique(st, return_counts=True)):
            moves["density_stage_hist"][str(int(k))] = moves["density_stage_hist"].get(str(int(k)), 0) + int(v)
        return out

    R.apply = wrapped
    kw: dict[str, Any] = {"space": a.space, "vocab_version": "v3", "activity": True}
    if a.days > 1:
        kw["sim_days"] = int(a.days)
    if a.stop:
        kw["state_out"] = a.state
        kw["stop_at_tick"] = int(a.stop)
    if a.resume:
        kw["resume_from"] = a.resume
    t0 = time.perf_counter()
    res = cli.run(n_agents=a.agents, seed=a.seed, world_dir=a.world, **kw)
    wall = time.perf_counter() - t0
    R.apply = orig
    man = res.run_manifest_fields()
    steps = int(getattr(res, "ticks", 0) or 0)
    import platform

    out = {"label": a.label, "space": a.space, "days": a.days, "agents": a.agents, "seed": a.seed,
           "machine": f"{platform.system()} {platform.release()} {platform.machine()} cpu={os.cpu_count()}",
           "final": res.final_hash[:16],
           "checkpoints": [(int(c.tick), c.combined[:16]) for c in res.checkpoints],
           "calls": int(res.llm_calls), "wall_s": round(wall, 1),
           "run_wall_s": round(float(getattr(res, "wall_seconds", 0.0) or 0.0), 2),
           "ms_per_step": round(1000.0 * float(getattr(res, "wall_seconds", 0.0) or 0.0) / max(1, steps), 2),
           "steps": steps, "peak_rss_bytes": _peak(), "space_effective": man["space"]["effective"],
           "space_meter": man["space"]["meter"], "cell_changes": moves["cell_changes"],
           "agent_ticks": moves["agent_ticks"], "density_stage_changes": moves["density_stage_changes"],
           "density_stage_hist": moves["density_stage_hist"],
           "action_usage": {str(k): int(v) for k, v in dict(getattr(res, "action_usage", {}) or {}).items()},
           "movement_s": round(float(res.phase_seconds.get("movement", 0.0)), 2),
           "phase_c_s": round(float(res.phase_seconds.get("phase_c", 0.0)), 2),
           "resume_files": [f["file"] for f in (res.resume or {}).get("state_files", [])] if a.stop else []}
    print(json.dumps(out, ensure_ascii=False, default=str))
    return 0


def cmd_side(a: argparse.Namespace) -> int:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    rows = []
    for spec in [s for s in a.runs.split(",") if s]:
        label, world, days, space, stop = (spec.split(";") + ["", "", "", "", ""])[:5]
        cmd = [sys.executable, str(Path(__file__)), "one", "--label", label, "--world", world, "--days",
               days or "1", "--space", space or "nav1", "--agents", str(a.agents)]
        if stop:
            st = Path(a.scratch) / f"state_{label}"
            cmd += ["--stop", stop, "--state", str(st)]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            rows.append({"label": label, "error": r.stderr[-3000:]})
            continue
        row = json.loads(r.stdout.strip().splitlines()[-1])
        rows.append(row)
        if stop and row.get("resume_files"):
            st = Path(a.scratch) / f"state_{label}"
            cmd2 = [sys.executable, str(Path(__file__)), "one", "--label", label + "_resumed", "--world", world,
                    "--days", days or "1", "--space", space or "nav1", "--agents", str(a.agents), "--resume",
                    str(st / row["resume_files"][-1])]
            r2 = subprocess.run(cmd2, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
            rows.append(json.loads(r2.stdout.strip().splitlines()[-1]) if r2.returncode == 0
                        else {"label": label + "_resumed", "error": r2.stderr[-3000:]})
        print(rows[-1].get("label"), rows[-1].get("final"), rows[-1].get("wall_s"), flush=True)
    Path(a.out).write_text(json.dumps({"agents": a.agents, "runs": rows}, ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("--label", required=True)
    o.add_argument("--world", default="data/world/v2_stage_5-1")
    o.add_argument("--days", type=int, default=1)
    o.add_argument("--space", default="nav1")
    o.add_argument("--agents", type=int, default=5000)
    o.add_argument("--seed", type=int, default=1)
    o.add_argument("--stop", type=int, default=0)
    o.add_argument("--state", default="")
    o.add_argument("--resume", default="")
    s = sub.add_parser("side")
    s.add_argument("--runs", required=True)
    s.add_argument("--agents", type=int, default=5000)
    s.add_argument("--scratch", required=True)
    s.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
