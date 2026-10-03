"""10c の byte-check(既定 stateful が HEAD と 1 バイトも違わないこと)と、counter に切り替えたときに動く量の控え。

比べ方は [byte_check_10b.py](../10b/byte_check_10b.py) と同じ(wave2 の 19 構成=W6 の 15 腕+店の記憶・関係・古典・
古典+記憶+関係。mock/classical 5,000 体・seed 1・1 シミュ日・テープつき。final・呼数・blocks・calls の 14 列)。
本スクリプトの ``one`` は 10b の欄に加えて顕著行為と出動の件数(``salient_events``・``collapse``・``dispatches``・
``noticed``・平均の遅れ)を出し、``--rng-scheme`` を渡せる(HEAD の写しには渡さない=口が無い)。

使い方(リポのルートで・``$D`` = この置き場・``$W`` = 作業用の**短い**ディレクトリ):

    git archive HEAD src docs/bench/anchors docs/design/v2-budget-declaration.md \\
        docs/bench/analysis/w6-regen-2026-09-28 | tar -x -C $W/head_src
    python $D/byte_check_10c.py side --src $W/head_src/src --label head --scratch $W --out $W/head.json
    python $D/byte_check_10c.py side --label work --scratch $W --out $W/work.json
    python $D/byte_check_10c.py side --label counter --rng-scheme counter --scratch $W --out $W/counter.json
    python $D/byte_check_10c.py compare --head $W/head.json --work $W/work.json --counter $W/counter.json \\
        --head-label <HEAD> --out $D/byte_check.json

壁時計は決定論でないので比較に使わない。絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib.util
import json
import os
import subprocess
import sys
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


def _wave2() -> Any:
    return _load(B10, "byte_check_10b")._wave2()


def cmd_one(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    import shibuya
    from shibuya import cli

    w2 = _wave2()
    kw = dict(w2.configs()[args.config])
    if args.rng_scheme:
        kw["rng_scheme"] = args.rng_scheme
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape, **kw)
    calls = pq.read_table(Path(args.tape) / "calls.parquet")
    blocks = pq.read_table(Path(args.tape) / "blocks.parquet")
    src_root = Path(shibuya.__file__).resolve().parents[1]
    pc = dict(getattr(res, "process_counters", {}) or {})
    man = res.run_manifest_fields()
    print(json.dumps({
        "config": args.config,
        "src_is_worktree": src_root == (REPO / "src").resolve(),
        "rng_scheme": man.get("rng_scheme", "(欄なし)"),
        "final": res.final_hash[:16],
        "calls": int(res.llm_calls),
        "blocks_rows": int(blocks.num_rows),
        "blocks_sha": w2._h({n: blocks.column(n).to_pylist() for n in blocks.column_names}),
        "calls_columns_sha": {n: w2._h(calls.column(n).to_pylist()) for n in calls.column_names},
        # ---- 10c の欄: 顕著行為と出動の件数 ----
        "salient_events": int(res.salient_events),
        "collapse": int(pc.get("salient.collapse", -1)),
        "noticed": int(res.noticed),
        "dispatches": int(res.dispatches),
        "arrived": int(pc.get("dispatch.arrived", -1)),
        "mean_delay_min": float(pc.get("dispatch.mean_delay_min", -1.0)),
        "behavior_last": (res.checkpoints[-1].behavior_hash[:16]
                          if res.checkpoints and getattr(res.checkpoints[-1], "behavior_hash", "") else ""),
        "full_last": (res.checkpoints[-1].full_hash[:16]
                      if res.checkpoints and getattr(res.checkpoints[-1], "full_hash", "") else ""),
        "wall_s": round(time.perf_counter() - t0, 1),
    }, ensure_ascii=False))
    return 0


def cmd_side(args: argparse.Namespace) -> int:
    w2 = _wave2()
    scratch = Path(args.scratch)
    names = list(w2.configs()) if not args.only else [s for s in args.only.split(",") if s]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if args.src:
        env["PYTHONPATH"] = str(Path(args.src).resolve())
        env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"

    def one(name: str) -> dict[str, Any]:
        cmd = [sys.executable, str(Path(__file__)), "one", "--config", name, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed),
               "--tape", str(scratch / f"{args.label}_{name}")]
        if args.rng_scheme:
            cmd += ["--rng-scheme", args.rng_scheme]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            return {"config": name, "error": r.stderr[-2000:]}
        return json.loads(r.stdout.strip().splitlines()[-1])

    got: dict[str, Any] = {}
    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        for row in ex.map(one, names):
            got[row["config"]] = row
            print(row["config"], row.get("final"), row.get("calls"), row.get("salient_events"),
                  row.get("dispatches"), row.get("src_is_worktree"), (row.get("error") or "")[-300:], flush=True)
    doc = {"label": args.label, "rng_scheme": args.rng_scheme or "(既定)", "old": {}, "runs": got}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


COUNT_KEYS = ("salient_events", "collapse", "noticed", "dispatches", "arrived", "mean_delay_min")


def cmd_compare(args: argparse.Namespace) -> int:
    w2 = _wave2()
    ns = argparse.Namespace(head=args.head, work=args.work, work_old="", expect_moved="",
                            head_label=args.head_label, note=args.note, out=args.out)
    rc = w2.cmd_compare(ns)
    doc = json.loads(Path(args.out).read_text(encoding="utf-8"))
    head = json.loads(Path(args.head).read_text(encoding="utf-8"))["runs"]
    work = json.loads(Path(args.work).read_text(encoding="utf-8"))["runs"]
    ctr = json.loads(Path(args.counter).read_text(encoding="utf-8"))["runs"]
    doc["how"] += ("。10c: 既定(stateful)の作業木と HEAD の写しを 14 列で比べる(上の rows)。"
                   "counter の腕は作業木で --rng-scheme counter を渡して回し、stateful との差を counter_moves に書く")
    moves: dict[str, Any] = {}
    for name in work:
        w, c, h = work[name], ctr.get(name, {}), head.get(name, {})
        moves[name] = {
            "head_counts": {k: h.get(k) for k in COUNT_KEYS},
            "stateful_counts": {k: w.get(k) for k in COUNT_KEYS},
            "counter_counts": {k: c.get(k) for k in COUNT_KEYS},
            "stateful_final": w.get("final"), "counter_final": c.get("final"),
            "final_moved": w.get("final") != c.get("final"),
            "stateful_calls": w.get("calls"), "counter_calls": c.get("calls"),
            "calls_delta": (None if c.get("calls") is None or w.get("calls") is None
                            else int(c["calls"]) - int(w["calls"])),
            "blocks_rows_delta": (None if c.get("blocks_rows") is None or w.get("blocks_rows") is None
                                  else int(c["blocks_rows"]) - int(w["blocks_rows"])),
            "manifest_rng_scheme": {"stateful": w.get("rng_scheme"), "counter": c.get("rng_scheme")},
            "counter_error": (c.get("error") or "")[-500:],
        }
    doc["counter_moves"] = moves
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return rc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("one", "side"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        sp.add_argument("--rng-scheme", default="")
        if name == "one":
            sp.add_argument("--config", required=True)
            sp.add_argument("--tape", required=True)
        else:
            sp.add_argument("--src", default="")
            sp.add_argument("--label", required=True)
            sp.add_argument("--scratch", required=True)
            sp.add_argument("--out", required=True)
            sp.add_argument("--only", default="")
            sp.add_argument("--jobs", type=int, default=3)
    sp = sub.add_parser("compare")
    sp.add_argument("--head", required=True)
    sp.add_argument("--work", required=True)
    sp.add_argument("--counter", required=True)
    sp.add_argument("--head-label", required=True)
    sp.add_argument("--note", default="10c: --rng-scheme {stateful,counter}(既定 stateful=不変)")
    sp.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
