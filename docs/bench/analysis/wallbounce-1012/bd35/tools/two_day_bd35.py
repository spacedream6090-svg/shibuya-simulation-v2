"""第 3 期 3-5: 2 日のランと再開=通し(世界資産・5,000 体・seed 1)を体の予約の腕 sweep と reserve で。

土台は vb24 の再開の道具と同じ 2 つ(``v3_mem_rel``=語彙 v3・記憶 on・関係 on/``w6_v3_default``=語彙 v3 だけ)。1 つの土台に
次の 4 本(どれも 2 日・テープなし・checkpoint は既定の間隔):

- ``straight_sweep``: 通し(既定の腕 sweep)。
- ``straight_reserve``: 通し(腕 reserve)=final・全 checkpoint・呼数・段の境目の列が ``straight_sweep`` と同じ。
- ``split_<T>``: 腕 sweep で刻み ``T`` に止めて状態を書き、腕 reserve で再開(予約の列は状態から引き直す)=刻み ``T`` から後の
  checkpoint と final が通しと同じ・呼数の和が通しと同じ。``T`` は日の境目 1,440 と日の中 750。

    PYTHONPATH=src python $D/tools/two_day_bd35.py all --base v3_mem_rel --scratch $W --out $D/two_day_v3_mem_rel.json

各本は別のプロセス(並べて回す)。絶対パスは JSON に書かない。逐次ループ宣言: 本数ぶん(道具)。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
BASES: dict[str, dict[str, Any]] = {
    "v3_mem_rel": {"vocab_version": "v3", "memory": "on", "relations": "on"},
    "w6_v3_default": {"vocab_version": "v3"},
}
STOPS = (1440, 750)


def _sig(res: Any) -> dict[str, Any]:
    m = res.run_manifest_fields()["body"]
    return {"final": res.final_hash, "calls": int(res.llm_calls),
            "checkpoints": [[int(c.tick), c.behavior_hash, c.full_hash] for c in res.checkpoints],
            "body_arm": m["arm"], "boundary_digest": m["boundary_digest"], "boundaries": m["boundaries"],
            "agent_evals": m["agent_evals"], "felt_evals": m["felt_evals"], "reservations": m["reservations"],
            "felt_reservations": m["felt_reservations"], "felt_tables": m["felt_tables"]}


def cmd_one(a: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.engine import body as B

    kw: dict[str, Any] = dict(BASES[a.base], n_agents=a.agents, seed=a.seed, sim_days=2, world_dir=a.world)
    work = Path(a.scratch) / f"two_day_bd35_{a.base}_{a.case}"
    work.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    if a.case.startswith("straight_"):
        B.set_arm(a.case.split("_", 1)[1])
        out = {"run": _sig(cli.run(**kw))}
    else:
        stop = int(a.case.split("_", 1)[1])
        B.set_arm("sweep")
        first = cli.run(state_out=work / "state", stop_at_tick=stop, **kw)
        f = first.resume["state_files"][-1]
        B.set_arm("reserve")
        second = cli.run(resume_from=work / "state" / f["file"], **kw)
        out = {"stop": stop, "first": {"calls": int(first.llm_calls), "body_arm": first.run_manifest_fields()["body"]["arm"]},
               "run": _sig(second), "state_T": int(f["T"])}
    out["wall_s"] = round(time.perf_counter() - t0, 1)
    print(json.dumps(out))
    return 0


def cmd_all(a: argparse.Namespace) -> int:
    cases = ["straight_sweep", "straight_reserve"] + [f"split_{s}" for s in STOPS]
    # 〔3-5 検収 L6〕段の境目の列を比べるので計器を数える(既定のランは数えない)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONPATH=str(REPO / "src"), SHIBUYA_BODY_BOUNDARY_GAUGE="1")

    def one(case: str) -> tuple[str, Any]:
        cmd = [sys.executable, str(Path(__file__)), "one", "--case", case, "--base", a.base, "--world", a.world,
               "--agents", str(a.agents), "--seed", str(a.seed), "--scratch", a.scratch]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            return case, {"error": r.stderr[-3000:]}
        return case, json.loads(r.stdout.strip().splitlines()[-1])

    with cf.ThreadPoolExecutor(max_workers=len(cases)) as ex:
        got = dict(ex.map(one, cases))
    s = got["straight_sweep"]["run"]
    checks: dict[str, Any] = {}
    r = got["straight_reserve"]["run"]
    checks["straight_reserve_equals_sweep"] = {
        k: r[k] == s[k] for k in ("final", "calls", "checkpoints", "boundary_digest", "boundaries")}
    for stop in STOPS:
        g = got[f"split_{stop}"]
        b = g["run"]
        want = [c for c in s["checkpoints"] if c[0] >= stop]
        have = [c for c in b["checkpoints"] if c[0] >= stop]
        checks[f"split_{stop}_equals_straight"] = {
            "final": b["final"] == s["final"], "checkpoints_after_stop": have == want and len(want) > 0,
            "calls_sum": g["first"]["calls"] + b["calls"] == s["calls"], "first_arm": g["first"]["body_arm"],
            "resume_arm": b["body_arm"], "n_checkpoints_after_stop": len(want)}
    ok = all(all(v for k, v in c.items() if isinstance(v, bool)) for c in checks.values())
    doc = {"base": a.base, "kw": BASES[a.base], "agents": a.agents, "seed": a.seed, "sim_days": 2, "ok": ok,
           "checks": checks,
           "runs": {k: ({kk: vv for kk, vv in v.items() if kk != "run"}
                        | {"run": {kk: vv for kk, vv in v["run"].items() if kk != "checkpoints"}} if "run" in v else v)
                    for k, v in got.items()},
           "final": s["final"][:16], "n_checkpoints": len(s["checkpoints"])}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(checks, ensure_ascii=False))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("one", "all"):
        sp = sub.add_parser(name)
        sp.add_argument("--base", choices=tuple(BASES), default="v3_mem_rel")
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        sp.add_argument("--scratch", required=True)
        if name == "one":
            sp.add_argument("--case", required=True)
        else:
            sp.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"one": cmd_one, "all": cmd_all}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
