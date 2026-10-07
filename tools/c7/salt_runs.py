# -*- coding: utf-8 -*-
"""salt の比較の**回す役**(10f 第 2 段・K21 (a))。読む役は ``salt_compare.py``。

腕 A(基準)と腕 B を、母集団の seed を固定したまま salt(動きの seed)ごとに回し、checkpoints の JSON と索引
(``runs.json``)を書く。エンジンの処理は足さない: 1 本ずつ別のプロセスで既存の入口 ``shibuya.cli.run`` を呼び、
``shibuya.cli.checkpoints_payload`` をそのまま書くだけ(``byte_check_10c.py`` の ``one`` と同じ形)。

- ``--environment-mode``(10f 第 2 段の直し・S1): ``fixed``(既定)=天気は同じで動きだけ変える(環境の seed を
  ``--environment-seed``(省略=母集団の seed)に固定)/ ``salt``=天気も変える(環境の seed を salt と同じ値にする)。
- ``--aa``: 基準の腕を最初の salt でもう 1 本回す(A/A=全 checkpoint と final の一致を読む役が確かめる)。
- ``--first-diff``: 対ごとに最初に食い違う tick を探す(アジェンダ §3 の親の宣言=expedient): 普通の
  checkpoint(既定 60 tick ごと)で最初に食い違った区間 (t_p, t_m] だけを毎 tick で回し直す。区間の前までは
  ``stop_at_tick`` で止めて状態を書き(10d)、そこから ``resume_from`` で再開して毎 tick の checkpoint を取る。
  最初の区間(t_p が無い)は 0 から毎 tick で回す。比べるのは ``first_diff.py`` の ``compare``。

使い方::

    python tools/c7/salt_runs.py plan --arms '{"base": {...}, "arm": {...}}' --base base --arm arm \\
        --salts 1,2,3 --population-seed 1 --agents 5000 --world data/world/v2 --scratch $W --out $W/runs.json \\
        [--aa] [--first-diff] [--jobs 3] [--T0 0]

``runs.json`` の中のパスは ``runs.json`` の置き場からの相対(ファイル名だけ)。絶対パスは書かない。壁時計は
``wall_seconds`` に入れる(決定論ではないので読む役は比べない)。
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
REPO = HERE.parents[1]
SCHEMA = "shibuya.tools.c7/salt_runs/1"
#: 腕の引数に書けない名前(道具が渡す seed の 3 つ・再検収 T5)。
SEED_ARGS: tuple[str, ...] = ("seed", "population_seed", "environment_seed")


def cmd_one(args: argparse.Namespace) -> int:
    """1 本を回して checkpoints の JSON を書く(``shibuya.cli.run`` を呼ぶだけ)。"""
    from shibuya import cli

    kw = dict(json.loads(args.kwargs or "{}"))
    for k in ("stop_at_tick", "state_out", "resume_from"):
        v = getattr(args, k)
        if v not in (None, ""):
            kw[k] = int(v) if k == "stop_at_tick" else v
    t0 = time.perf_counter()
    env = None if args.environment_seed in (None, "") else int(args.environment_seed)
    res = cli.run(n_agents=int(args.agents), seed=int(args.seed), population_seed=int(args.population_seed),
                  environment_seed=env, world_dir=args.world, checkpoint_every=int(args.checkpoint_every), **kw)
    wall = time.perf_counter() - t0
    payload = cli.checkpoints_payload(res)
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, default=str) + "\n",
                              encoding="utf-8", newline="\n")
    print(json.dumps({"out": Path(args.out).name, "final": res.final_hash[:16], "calls": int(res.llm_calls),
                      "wall_s": round(wall, 2)}, ensure_ascii=False))
    return 0


def _run_one(args: argparse.Namespace, kwargs: dict[str, Any], seed: int, out: Path, *,
             checkpoint_every: int, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    cmd = [sys.executable, str(Path(__file__)), "one", "--kwargs", json.dumps(kwargs, ensure_ascii=False),
           "--seed", str(seed), "--population-seed", str(args.population_seed),
           "--environment-seed", str(_environment_seed(args, seed)), "--agents", str(args.agents),
           "--world", args.world, "--checkpoint-every", str(checkpoint_every), "--out", str(out)]
    for k, v in (extra or {}).items():
        cmd += [f"--{k.replace('_', '-')}", str(v)]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
    wall = time.perf_counter() - t0
    if r.returncode != 0:
        raise RuntimeError(f"{out.name}: {r.stderr[-3000:]}")
    row = json.loads(r.stdout.strip().splitlines()[-1])
    row["wall_s_process"] = round(wall, 2)
    return row


def _environment_seed(args: argparse.Namespace, salt: int) -> int:
    """10f(S1): そのランの環境の seed。``fixed`` は固定の値(省略=母集団の seed)・``salt`` は salt と同じ値。"""
    if args.environment_mode == "salt":
        return int(salt)
    return int(args.population_seed if args.environment_seed is None else args.environment_seed)


def _first_mismatch(a: dict[str, Any], b: dict[str, Any], from_T: int = 0) -> dict[str, Any]:
    sys.path.insert(0, str(HERE))
    import salt_compare as sc  # noqa: E402

    return sc.first_divergence(a, b, from_T=from_T)


def _fine_first_diff(args: argparse.Namespace, arms: dict[str, Any], salt: int, coarse: dict[str, Any],
                     scratch: Path) -> dict[str, Any]:
    """粗い checkpoint で最初に食い違った区間だけを毎 tick で回し直し、最初の tick を出す。"""
    t_m = coarse.get("first_tick")
    if t_m is None:
        return {"coarse_first_tick": None, "first_tick": None, "note": "粗い checkpoint で食い違いなし"}
    t_p = coarse.get("last_match_tick")
    start = 0 if t_p is None else int(t_p) + 1
    stop = int(t_m) + 1
    total = int(args.ticks_total)
    docs: dict[str, dict[str, Any]] = {}
    walls: dict[str, float] = {}
    for name in (args.base, args.arm):
        d = scratch / f"fine_{name}_s{salt}"
        if d.exists() and any(d.iterdir()):  # 検収 S3-6: 前のランの状態のファイルを拾わない
            raise RuntimeError(f"{d.name} が空でない(前のランの残り)。新しい --scratch で回す")
        d.mkdir(parents=True, exist_ok=True)
        extra: dict[str, Any] = {}
        t0 = time.perf_counter()
        if start > 0:
            # 区間の前まで(毎 tick にしない)回して状態を書く=10d の止める口
            _run_one(args, arms[name], salt, d / "head.json", checkpoint_every=int(args.checkpoint_every),
                     extra={"stop_at_tick": start, "state_out": str(d / "state_head")})
            states = sorted((d / "state_head").glob(f"state-T{start:08d}*.npz"))
            if not states:
                raise RuntimeError(f"状態のファイルが無い({d.name}/state_head・T={start})")
            extra["resume_from"] = str(states[-1])
        if stop < total:
            extra["stop_at_tick"] = stop
            extra["state_out"] = str(d / "state_tail")
        _run_one(args, arms[name], salt, d / "fine.json", checkpoint_every=1, extra=extra)
        walls[name] = round(time.perf_counter() - t0, 2)
        docs[name] = json.loads((d / "fine.json").read_text(encoding="utf-8"))
    fine = _first_mismatch(docs[args.base], docs[args.arm], from_T=start)
    return {"coarse_first_tick": int(t_m), "interval": [start, int(t_m)], "first_tick": fine.get("first_tick"),
            "hashes_differ": fine.get("hashes_differ"), "checkpoints_compared": fine.get("checkpoints_compared"),
            "wall_s": walls}


def cmd_plan(args: argparse.Namespace) -> int:
    arms = json.loads(args.arms)
    if args.base not in arms or args.arm not in arms:
        raise SystemExit(f"--base/--arm は --arms の鍵({sorted(arms)})")
    for name, kw in arms.items():  # 再検収 T5: seed の 3 つは道具が渡す(腕の引数に書くと cli.run の引数が重なる)
        bad = sorted(set(kw) & set(SEED_ARGS))
        if bad:
            raise SystemExit(f"腕 {name!r} の引数に {bad} がある。seed は --salts・--population-seed・"
                             "--environment-mode/--environment-seed で渡す")
    salts = [int(s) for s in args.salts.split(",") if s.strip()]
    scratch = Path(args.scratch)
    if scratch.exists() and any(scratch.iterdir()):
        # 検収 S3-6: 前のランの checkpoints や状態のファイルを拾わない(置き場は毎回新しく)
        print(f"refuse: --scratch {scratch.name} が空でない(新しい置き場で回す)", file=sys.stderr)
        return 2
    scratch.mkdir(parents=True, exist_ok=True)
    out = Path(args.out)
    if out.exists():
        print(f"refuse: {out.name} は既にある", file=sys.stderr)
        return 2
    jobs: list[tuple[str, int, bool]] = [(a, s, False) for a in (args.base, args.arm) for s in salts]
    if args.aa:
        jobs.append((args.base, salts[0], True))
    t_all = time.perf_counter()
    rows: list[dict[str, Any]] = []

    def go(job: tuple[str, int, bool]) -> dict[str, Any]:
        name, s, aa = job
        fn = scratch / f"{name}_s{s}{'_aa' if aa else ''}.json"
        r = _run_one(args, arms[name], s, fn, checkpoint_every=int(args.checkpoint_every))
        return {"arm": name, "salt": s, "aa": aa, "checkpoints": fn.name, "final": r["final"], "calls": r["calls"],
                "wall_s": r["wall_s"], "wall_s_process": r["wall_s_process"]}

    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        for row in ex.map(go, jobs):
            rows.append(row)
            print(row["arm"], row["salt"], "aa" if row["aa"] else "", row["final"], row["calls"], row["wall_s"],
                  flush=True)
    t_runs = time.perf_counter() - t_all
    index: dict[str, Any] = {
        "schema": SCHEMA, "arms": arms, "base": args.base, "arm": args.arm, "salts": salts,
        "population_seed": int(args.population_seed), "agents": int(args.agents),
        "environment_mode": args.environment_mode,
        "environment_seed": (None if args.environment_mode == "salt" else _environment_seed(args, salts[0])),
        "world": Path(args.world).as_posix() if not Path(args.world).is_absolute() else Path(args.world).name,
        "checkpoint_every": int(args.checkpoint_every), "T0": int(args.T0), "jobs": int(args.jobs), "runs": rows,
    }
    wall: dict[str, Any] = {"runs": round(t_runs, 1)}
    if args.first_diff:
        t_fd = time.perf_counter()
        fine: dict[str, Any] = {}
        for s in salts:
            a = json.loads((scratch / f"{args.base}_s{s}.json").read_text(encoding="utf-8"))
            b = json.loads((scratch / f"{args.arm}_s{s}.json").read_text(encoding="utf-8"))
            args.ticks_total = int(a.get("ticks", 1440))
            coarse = _first_mismatch(a, b)
            fine[str(s)] = _fine_first_diff(args, arms, s, coarse, scratch)
            print("first_diff", s, fine[str(s)], flush=True)
        index["first_diff_fine"] = fine
        wall["first_diff"] = round(time.perf_counter() - t_fd, 1)
    index["wall_seconds"] = wall
    index["note"] = "wall_seconds・wall_s は壁時計(決定論ではない)。パスは runs.json の置き場からの相対"
    out.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out.name} runs={len(rows)} wall={wall}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one", help="1 本(内部用)")
    o.add_argument("--kwargs", default="{}")
    o.add_argument("--seed", type=int, required=True)
    o.add_argument("--population-seed", type=int, required=True)
    o.add_argument("--environment-seed", default=None)
    o.add_argument("--agents", type=int, default=5000)
    o.add_argument("--world", default="data/world/v2")
    o.add_argument("--checkpoint-every", type=int, default=60)
    o.add_argument("--stop-at-tick", type=int, default=None)
    o.add_argument("--state-out", default="")
    o.add_argument("--resume-from", default="")
    o.add_argument("--out", required=True)
    p = sub.add_parser("plan", help="腕 × salt を回して索引を書く")
    p.add_argument("--arms", required=True, help='JSON {"名前": {cli.run の引数}}')
    p.add_argument("--base", required=True)
    p.add_argument("--arm", required=True)
    p.add_argument("--salts", default="1,2,3", help="動きの seed(salt)の一覧")
    p.add_argument("--population-seed", type=int, default=1, help="母集団の seed(全部のランで同じ)")
    p.add_argument("--environment-mode", choices=("fixed", "salt"), default="fixed",
                   help="fixed=天気は同じで動きだけ変える / salt=天気も変える(環境の seed を salt と同じに)")
    p.add_argument("--environment-seed", type=int, default=None,
                   help="fixed のときの環境の seed(省略=母集団の seed)")
    p.add_argument("--agents", type=int, default=5000)
    p.add_argument("--world", default="data/world/v2")
    p.add_argument("--checkpoint-every", type=int, default=60)
    p.add_argument("--T0", type=int, default=0, help="改変の時刻(腕が最初から違うなら 0)")
    p.add_argument("--aa", action="store_true", help="基準の腕を最初の salt でもう 1 本(A/A)")
    p.add_argument("--first-diff", action="store_true", help="対ごとに最初に食い違う tick を探す")
    p.add_argument("--jobs", type=int, default=1)
    p.add_argument("--scratch", required=True)
    p.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return cmd_one(args) if args.cmd == "one" else cmd_plan(args)


if __name__ == "__main__":
    raise SystemExit(main())
