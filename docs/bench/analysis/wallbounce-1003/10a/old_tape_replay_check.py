"""10a(A9): 旧い実 LLM テープ(版 2・``observed_tick`` つき)の再生が、``--response-delay 2`` で HEAD と一致するかを見る。

使い方(リポのルートで・``$D`` = この置き場):

    # HEAD の写し(git archive HEAD src docs/bench/anchors docs/design/v2-budget-declaration.md)で
    python $D/old_tape_replay_check.py one --tape <テープ> --label head --src <写しの src> --out <作業用>/head_<名>.json
    # 作業木で(旧の +2 と新の +1)
    python $D/old_tape_replay_check.py one --tape <テープ> --label work2 --delay 2 --out <作業用>/work2_<名>.json
    python $D/old_tape_replay_check.py one --tape <テープ> --label work1 --delay 1 --out <作業用>/work1_<名>.json
    # 比べる
    python $D/old_tape_replay_check.py compare --head <..> --work2 <..> --work1 <..> --out $D/old_tape_replay_<名>.json

再生の構成は ``--config``(JSON・``cli.run`` の引数)で渡す。旧テープを録ったときの世界資産・コードとは今は違うので
テープ外(``tape_miss``)は出る。ここで見るのは「同じテープ・同じ構成で HEAD と作業木(+2)が 1 バイトも違わないか」と
「+1 にすると動くか(=再生の到着の経路を本当に通っているか)」だけ。壁時計は比べない。絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]


def _h(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:16]


def cmd_run(args: argparse.Namespace) -> int:
    """(子プロセス)1 本の再生を回して結果を 1 行の JSON で出す。"""
    import shibuya
    from shibuya import cli

    kw = json.loads(args.config or "{}")
    if args.delay:
        kw["response_delay"] = int(args.delay)
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, mode="replay",
                  replay=args.tape, **kw)
    src_root = Path(shibuya.__file__).resolve().parents[1]
    c = {k: float(v) for k, v in sorted(res.bridge_counters.items())}
    print(json.dumps({
        "src_is_worktree": src_root == (REPO / "src").resolve(),
        "final": res.final_hash[:16],
        "checkpoints": _h([x.combined for x in res.checkpoints]),
        "calls": int(res.llm_calls),
        "tape_miss": int(res.tape_miss_count),
        "fleet_drained_at_end": int(res.fleet_drained_at_end),
        "fleet_unanswered_at_end": int(res.fleet_unanswered_at_end),
        "bridge_counters": c,
        "wall_s": round(time.perf_counter() - t0, 1),
    }, ensure_ascii=False))
    return 0


def cmd_one(args: argparse.Namespace) -> int:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if args.src:
        env["PYTHONPATH"] = str(Path(args.src).resolve())
        env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"
    cmd = [sys.executable, str(Path(__file__)), "run", "--tape", args.tape, "--world", args.world,
           "--agents", str(args.agents), "--seed", str(args.seed), "--config", args.config or "",
           "--delay", str(args.delay or 0)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
    row: dict[str, Any] = {"label": args.label, "tape": Path(args.tape).name, "delay": int(args.delay or 0),
                           "config": json.loads(args.config or "{}")}
    if r.returncode != 0:
        row["error"] = r.stderr[-2000:]
    else:
        row.update(json.loads(r.stdout.strip().splitlines()[-1]))
    Path(args.out).write_text(json.dumps(row, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(row.get("final"), row.get("calls"), row.get("tape_miss"), row.get("src_is_worktree"),
          (row.get("error") or "")[-300:])
    return 0 if "error" not in row else 1


def cmd_compare(args: argparse.Namespace) -> int:
    head = json.loads(Path(args.head).read_text(encoding="utf-8"))
    work2 = json.loads(Path(args.work2).read_text(encoding="utf-8"))
    work1 = json.loads(Path(args.work1).read_text(encoding="utf-8")) if args.work1 else None
    keys = ("final", "checkpoints", "calls", "tape_miss", "fleet_drained_at_end", "fleet_unanswered_at_end",
            "bridge_counters")
    src_ok = (head.get("src_is_worktree") is False and work2.get("src_is_worktree") is True
              and (work1 is None or work1.get("src_is_worktree") is True)
              and not any("error" in d for d in (head, work2) + ((work1,) if work1 else ())))
    same2 = {k: head.get(k) == work2.get(k) for k in keys}
    doc = {
        "schema": "shibuya.bench/wallbounce-1003/10a/old-tape-replay/1",
        "head": args.head_label,
        "tape": head.get("tape"),
        "config": head.get("config"),
        "src_ok": src_ok,
        "head_vs_work_delay2": same2,
        "head_vs_work_delay2_all_equal": all(same2.values()),
        "head": {k: head.get(k) for k in keys if k != "bridge_counters"},
        "work_delay2": {k: work2.get(k) for k in keys if k != "bridge_counters"},
        "work_delay1": ({k: work1.get(k) for k in keys if k != "bridge_counters"} if work1 else None),
        "delay1_moves_the_run": (work1.get("final") != head.get("final")) if work1 else None,
        "replay_counters_head": {k: v for k, v in (head.get("bridge_counters") or {}).items()
                                 if k.startswith(("tape_", "fleet_"))},
    }
    ok = bool(src_ok and doc["head_vs_work_delay2_all_equal"])
    doc["all_ok"] = ok
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("ALL_OK" if ok else "MISMATCH", same2, "delay1_moves:", doc["delay1_moves_the_run"])
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "one"):
        sp = sub.add_parser(name)
        sp.add_argument("--tape", required=True)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        sp.add_argument("--config", default="")
        sp.add_argument("--delay", type=int, default=0)
        if name == "one":
            sp.add_argument("--label", required=True)
            sp.add_argument("--src", default="")
            sp.add_argument("--out", required=True)
    sp = sub.add_parser("compare")
    sp.add_argument("--head", required=True)
    sp.add_argument("--work2", required=True)
    sp.add_argument("--work1", default="")
    sp.add_argument("--head-label", default="a08109a")
    sp.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"run": cmd_run, "one": cmd_one, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
