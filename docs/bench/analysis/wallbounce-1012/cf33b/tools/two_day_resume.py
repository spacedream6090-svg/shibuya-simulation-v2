"""第 3 期 3-3b 既定のラン(申込書なし)の 2 日と再開=通しの確かめ(記録 ``../README.md`` §8)。

``side``: ``--src`` の木(HEAD の写しか作業木)で、世界資産 N 体・seed 1・2 日・語彙 v3 の (1) 通しのラン (2) 1 日目の終わり
(刻み 1,440)で止めて状態を書くラン (3) その状態から再開したラン を子プロセスで回し、final・呼数・全 checkpoint の
behavior/full のハッシュを JSON に書く。``compare``: 2 つの side の通しの final と checkpoint が同じか・各 side で再開=通しか。

使い方(リポの根で)::

    python <この道具> side --src <HEAD の写しの src> --label head --scratch <作業用> --out <…>/head.json
    python <この道具> side --src src --label cf33b --scratch <作業用> --out <…>/cf33b.json
    python <この道具> compare --a <…>/head.json --b <…>/cf33b.json --out <記録の JSON>

絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

KW = dict(seed=1, world_dir="data/world/v2", sim_days=2, vocab_version="v3", checkpoint_every=360)


def cmd_one(a: argparse.Namespace) -> int:
    from shibuya import cli

    kw = dict(KW, n_agents=int(a.agents))
    mode = a.mode
    t = time.perf_counter()
    if mode == "straight":
        res = cli.run(**kw)
    elif mode == "stop":
        res = cli.run(**kw, state_out=a.state, stop_at_tick=1440)
    else:
        res = cli.run(**kw, resume_from=str(Path(a.state) / "state-T00001440.npz"))
    cps = [[int(c.tick), c.behavior_hash, c.full_hash] for c in res.checkpoints]
    m = res.run_manifest_fields()
    print(json.dumps({"mode": mode, "final": res.final_hash, "calls": int(res.llm_calls), "checkpoints": cps,
                      "experiment": m.get("experiment"), "wall_s": round(time.perf_counter() - t, 1),
                      "src_is_worktree": Path(sys.modules["shibuya"].__file__).resolve().parents[1]
                      == Path("src").resolve()}, ensure_ascii=False))
    return 0


def cmd_side(a: argparse.Namespace) -> int:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONPATH=str(Path(a.src).resolve()))
    scratch = Path(a.scratch) / a.label
    scratch.mkdir(parents=True, exist_ok=True)
    out = {}
    for mode in ("straight", "stop", "resume"):
        cmd = [sys.executable, str(Path(__file__)), "one", "--mode", mode, "--agents", str(a.agents),
               "--state", str(scratch / "state")]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env)
        if r.returncode != 0:
            out[mode] = {"error": r.stderr[-2000:]}
            continue
        out[mode] = json.loads(r.stdout.strip().splitlines()[-1])
        print(a.label, mode, out[mode]["final"], out[mode]["wall_s"], flush=True)
    doc = {"label": a.label, "agents": a.agents, "kw": KW, "runs": out}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def _resume_equal(side: dict) -> dict:
    s, r = side["runs"]["straight"], side["runs"]["resume"]
    want = [c for c in s["checkpoints"] if c[0] >= 1440]
    return {"final_same": s["final"] == r["final"], "checkpoints_same": r["checkpoints"] == want,
            "checkpoints_compared": len(want)}


def cmd_compare(a: argparse.Namespace) -> int:
    x = json.loads(Path(a.a).read_text(encoding="utf-8"))
    y = json.loads(Path(a.b).read_text(encoding="utf-8"))
    sa, sb = x["runs"]["straight"], y["runs"]["straight"]
    doc = {"schema": "cf33b/two-day-resume/1", "agents": x["agents"], "kw": x["kw"],
           "a": {"label": x["label"], "final": sa["final"], "calls": sa["calls"], "src_is_worktree": sa["src_is_worktree"],
                 "resume": _resume_equal(x)},
           "b": {"label": y["label"], "final": sb["final"], "calls": sb["calls"], "src_is_worktree": sb["src_is_worktree"],
                 "resume": _resume_equal(y)},
           "straight_final_same": sa["final"] == sb["final"], "straight_calls_same": sa["calls"] == sb["calls"],
           "straight_checkpoints_same": sa["checkpoints"] == sb["checkpoints"],
           "checkpoints": len(sa["checkpoints"]), "experiment_null": [sa["experiment"], sb["experiment"]],
           "wall_s": {x["label"]: {k: v.get("wall_s") for k, v in x["runs"].items()},
                      y["label"]: {k: v.get("wall_s") for k, v in y["runs"].items()}}}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("straight_final_same", "straight_checkpoints_same")}, ensure_ascii=False),
          doc["a"]["resume"], doc["b"]["resume"])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    one = sub.add_parser("one")
    one.add_argument("--mode", choices=("straight", "stop", "resume"), required=True)
    one.add_argument("--agents", type=int, default=5000)
    one.add_argument("--state", required=True)
    side = sub.add_parser("side")
    side.add_argument("--src", required=True)
    side.add_argument("--label", required=True)
    side.add_argument("--scratch", required=True)
    side.add_argument("--out", required=True)
    side.add_argument("--agents", type=int, default=5000)
    cmp_ = sub.add_parser("compare")
    cmp_.add_argument("--a", required=True)
    cmp_.add_argument("--b", required=True)
    cmp_.add_argument("--out", required=True)
    a = ap.parse_args()
    return {"one": cmd_one, "side": cmd_side, "compare": cmd_compare}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
