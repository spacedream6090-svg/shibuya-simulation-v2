"""10d の ``resume == straight`` の記録(mock 5,000 体・世界資産あり・2 日)。

1 つの構成について:

1. 通しのラン(2 日・``checkpoint_every`` ごとに 3 つのハッシュ・テープつき)。
2. 止める時刻ごとに「止めたラン(``stop_at_tick``・状態を書く)」→「再開のラン(``resume_from``)」。
3. ``first_diff.compare`` で、再開の時刻から後の全 checkpoint・tick ごとの呼数・日の締めの後の 2 つのハッシュと
   日次センサスの行・テープの呼ごとの prompt_hash を通しと比べる。
4. ``--fresh-process`` の止める時刻は、再開を**別のプロセス**で回す(numba のキャッシュの置き場も空にする)
   =プロセスの中に残るキャッシュを持ち越さない再開(試験 iii)。

使い方(リポのルートで・``$W`` は作業用の**短い**ディレクトリ・検収の後に親が消す)::

    python docs/bench/analysis/wallbounce-1003/10d/resume_check_10d.py run --config w6_v3_default \\
        --stops 420,750,1320,1440 --fresh-process 1440 --scratch $W/rc --out $W/rc_v3.json

保存の範囲は状態台帳(10d 版)の範囲だけ(親の答え 1)。通しも止めたランも再開のランもテープを書く(テープの共有
ブロックの印 O85 が full-hash に入るため・親の答え 3)。
壁時計は決定論でないので比べない(記録だけ)。絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
B10 = REPO / "docs" / "bench" / "analysis" / "wallbounce-1003" / "10b" / "byte_check_10b.py"


def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


FD = _load(HERE / "first_diff.py", "first_diff_10d")


def configs() -> dict[str, dict[str, Any]]:
    out = dict(_load(B10, "byte_check_10b")._wave2().configs())
    out["v3_counter_x1000"] = {"vocab_version": "v3", "activity": True, "rng_scheme": "counter",
                               "salient_rate_per_10k": 3000.0}
    return out


def _kw(args: argparse.Namespace) -> dict[str, Any]:
    kw = dict(configs()[args.config])
    kw.update(n_agents=int(args.agents), seed=int(args.seed), world_dir=args.world, sim_days=2,
              checkpoint_every=int(args.checkpoint_every), checkpoint_detail=bool(args.detail))
    return kw


def _ledger_version() -> str:
    from shibuya.engine.state_ledger import LEDGER_VERSION

    return LEDGER_VERSION


def cmd_one(args: argparse.Namespace) -> int:
    """1 本のラン(``run`` が別のプロセスで呼ぶ口)。結果は ``--dump`` へ。"""
    from shibuya import cli

    kw = _kw(args)
    if args.resume_from:
        kw["resume_from"] = args.resume_from
    if args.stop:
        kw.update(stop_at_tick=int(args.stop), state_out=args.state_out)
    t0 = time.perf_counter()
    res = cli.run(tape_path=args.tape, **kw)
    FD.dump(res, args.dump, label=args.label, tape=args.tape)
    print(json.dumps({"label": args.label, "wall_s": round(time.perf_counter() - t0, 1)}, ensure_ascii=False))
    return 0


def _sub(args: argparse.Namespace, label: str, scratch: Path, *, stop: int = 0, resume_from: str = "",
         fresh: bool = False) -> tuple[dict[str, Any], float]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if fresh:
        env["NUMBA_CACHE_DIR"] = tempfile.mkdtemp(prefix="nb_", dir=str(scratch))
    cmd = [sys.executable, str(Path(__file__)), "one", "--config", args.config, "--agents", str(args.agents),
           "--seed", str(args.seed), "--world", args.world, "--checkpoint-every", str(args.checkpoint_every),
           "--label", label, "--tape", str(scratch / f"tape_{label}"), "--dump", str(scratch / f"{label}.json")]
    if args.detail:
        cmd.append("--detail")
    if stop:
        cmd += ["--stop", str(stop), "--state-out", str(scratch / f"state_{label}")]
    if resume_from:
        cmd += ["--resume-from", resume_from]
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
    if r.returncode != 0:
        raise RuntimeError(f"{label}: {r.stderr[-3000:]}")
    return json.loads((scratch / f"{label}.json").read_text(encoding="utf-8")), time.perf_counter() - t0


def cmd_run(args: argparse.Namespace) -> int:
    scratch = Path(args.scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    stops = [int(x) for x in args.stops.split(",") if x]
    fresh = {int(x) for x in args.fresh_process.split(",") if x}
    straight, wall_s = _sub(args, "straight", scratch)
    print("straight", straight["final"][:16], straight["llm_calls"], round(wall_s, 1), flush=True)
    rows = []
    for stop in stops:
        a, wall_a = _sub(args, f"stop{stop}", scratch, stop=stop)
        f = a["state_files"][-1]
        state = scratch / f"state_stop{stop}" / f["file"]
        b, wall_b = _sub(args, f"resume{stop}", scratch, resume_from=str(state), fresh=stop in fresh)
        rep = FD.compare(straight, [a, b])
        rows.append({
            "stop_T": stop, "fresh_process": stop in fresh, "state_file": f["file"],
            "state_bytes": int(f["bytes"]), "state_full_hash": f["full_hash"][:16],
            "calls": {"straight": straight["llm_calls"], "stop+resume": a["llm_calls"] + b["llm_calls"]},
            "compare": rep, "wall_s": {"stop": round(wall_a, 1), "resume": round(wall_b, 1)},
        })
        print(stop, "ok" if rep["ok"] else "NG", rep["checkpoints_compared"], rep["mismatched_checkpoints"],
              rep["first_mismatch"], rep.get("tape"), flush=True)
    doc = {
        "schema": "shibuya.bench/10d/resume-check/1",
        "config": args.config, "agents": int(args.agents), "seed": int(args.seed), "sim_days": 2,
        "checkpoint_every": int(args.checkpoint_every), "ledger_version": _ledger_version(),
        "straight": {"final": straight["final"][:16], "llm_calls": straight["llm_calls"],
                     "daily": straight["daily"], "day_heads": straight["day_heads"],
                     "state_files": straight["state_files"], "wall_s": round(wall_s, 1)},
        "stops": rows,
        "all_ok": all(r["compare"]["ok"] for r in rows),
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("all_ok", doc["all_ok"])
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "one"):
        sp = sub.add_parser(name)
        sp.add_argument("--config", required=True)
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--checkpoint-every", type=int, default=1)
        sp.add_argument("--detail", action="store_true")
        if name == "run":
            sp.add_argument("--stops", default="420,750,1320,1440")
            sp.add_argument("--fresh-process", default="")
            sp.add_argument("--scratch", required=True)
            sp.add_argument("--out", required=True)
        else:
            sp.add_argument("--label", required=True)
            sp.add_argument("--tape", required=True)
            sp.add_argument("--dump", required=True)
            sp.add_argument("--stop", type=int, default=0)
            sp.add_argument("--state-out", default="")
            sp.add_argument("--resume-from", default="")
    args = ap.parse_args(argv)
    return cmd_run(args) if args.cmd == "run" else cmd_one(args)


if __name__ == "__main__":
    raise SystemExit(main())
