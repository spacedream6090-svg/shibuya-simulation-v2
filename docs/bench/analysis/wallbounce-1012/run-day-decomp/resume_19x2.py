"""1-0: 再開の 19×2(10f の ``resume_19x2_stage3.json`` と同じ形)。状態の保存と復元を動かして「再開=通し」を確かめる。

byte-check の 19 構成(wave2)× 世界資産 300 体・seed 1・2 日・checkpoint 60 ごと・テープつき。止める時刻 T=750・1440 で
状態を書き(``stop_at_tick``・``state_out``)、再開のラン(``resume_from``)の T 以後の checkpoint(tick・behavior-hash・full-hash)
が通しと同じか(``equal``)・呼数の合計(止めたラン+再開のラン)が通しと同じか(``calls_equal``)・final が同じか。
``--head`` の側(``PYTHONPATH`` を HEAD の src に)と 1-0 の側で同じものを回し、通しの final と呼数も突き合わせる(``compare``)。

使い方(リポの根で・``$W`` は作業用の短い置き場)::

    python $D/resume_19x2.py side --label c10 --scratch $W --out $W/resume_10.json --jobs 6
    python $D/resume_19x2.py compare --a $W/resume_head.json --b $W/resume_10.json --out $D/resume_19x2.json

絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
WAVE2 = REPO / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"
STOPS = (750, 1440)


def _wave2() -> Any:
    spec = importlib.util.spec_from_file_location("wave2_bytecheck", WAVE2)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _ck(res: Any) -> list[list[Any]]:
    return [[int(c.tick), c.behavior_hash, c.full_hash] for c in res.checkpoints]


def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli

    kw = dict(_wave2().configs()[args.config])
    base = dict(n_agents=args.agents, seed=1, world_dir=args.world, sim_days=2, checkpoint_every=60, **kw)
    scratch = Path(args.scratch)
    st = cli.run(tape_path=str(scratch / "straight"), **base)
    row: dict[str, Any] = {"config": args.config, "final": st.final_hash[:16], "calls": int(st.llm_calls)}
    ck = _ck(st)
    for T in STOPS:
        sd = scratch / f"state{T}"
        a = cli.run(tape_path=str(scratch / f"stop{T}"), stop_at_tick=T, state_out=str(sd), **base)
        files = sorted(p for p in sd.glob("state-T*.npz") if p.name == f"state-T{T:08d}.npz")
        if not files:
            row[f"stop{T}"] = {"error": "状態のファイルが無い"}
            continue
        b = cli.run(tape_path=str(scratch / f"resume{T}"), resume_from=str(files[0]), **base)
        ckb = _ck(b)
        want = [c for c in ck if c[0] >= T]
        row[f"stop{T}"] = {"file": files[0].name, "bytes": int(files[0].stat().st_size), "equal": ckb == want,
                           "n_checkpoints": len(ckb), "final_equal": b.final_hash == st.final_hash,
                           "calls_equal": int(a.llm_calls) + int(b.llm_calls) == int(st.llm_calls)}
    print(json.dumps(row, ensure_ascii=False))
    return 0


def cmd_side(args: argparse.Namespace) -> int:
    names = list(_wave2().configs()) if not args.only else [s for s in args.only.split(",") if s]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if args.src:
        env["PYTHONPATH"] = str(Path(args.src).resolve())

    def one(name: str) -> dict[str, Any]:
        cmd = [sys.executable, str(Path(__file__)), "one", "--config", name, "--world", args.world,
               "--agents", str(args.agents), "--scratch", str(Path(args.scratch) / f"{args.label}_{name}")]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            return {"config": name, "error": r.stderr[-2000:]}
        return json.loads(r.stdout.strip().splitlines()[-1])

    rows = []
    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        for row in ex.map(one, names):
            rows.append(row)
            print(row.get("config"), row.get("final"), {k: v for k, v in row.items() if k.startswith("stop")},
                  (row.get("error") or "")[-300:], flush=True)
    doc = {"schema": "shibuya.bench/1-0/resume-19x2/1", "label": args.label, "src": "写し" if args.src else "作業木",
           "how": "byte-check の 19 構成 × 世界資産 300 体・seed 1・2 日・checkpoint 60 ごと・テープつき。T=750・1440 で止めて再開",
           "rows": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    a = {r["config"]: r for r in json.loads(Path(args.a).read_text(encoding="utf-8"))["rows"]}
    b = {r["config"]: r for r in json.loads(Path(args.b).read_text(encoding="utf-8"))["rows"]}
    rows = []
    for k in a:
        ra, rb = a[k], b.get(k, {})
        ok_b = all(rb.get(f"stop{T}", {}).get(x) for T in STOPS for x in ("equal", "calls_equal", "final_equal"))
        rows.append({"config": k, "straight_final_same": ra.get("final") == rb.get("final"),
                     "straight_calls_same": ra.get("calls") == rb.get("calls"), "final": rb.get("final"),
                     "resume_equals_straight_b": ok_b,
                     "state_bytes_same": all(ra.get(f"stop{T}", {}).get("bytes") == rb.get(f"stop{T}", {}).get("bytes")
                                             for T in STOPS)})
    doc = {"a": args.a and Path(args.a).name, "b": args.b and Path(args.b).name, "rows": rows,
           "all_ok": all(r["straight_final_same"] and r["straight_calls_same"] and r["resume_equals_straight_b"]
                         for r in rows)}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"all_ok": doc["all_ok"], "n": len(rows)}, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("--config", required=True)
    o.add_argument("--world", default="data/world/v2")
    o.add_argument("--agents", type=int, default=300)
    o.add_argument("--scratch", required=True)
    s = sub.add_parser("side")
    s.add_argument("--label", required=True)
    s.add_argument("--src", default="")
    s.add_argument("--world", default="data/world/v2")
    s.add_argument("--agents", type=int, default=300)
    s.add_argument("--scratch", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--only", default="")
    s.add_argument("--jobs", type=int, default=6)
    c = sub.add_parser("compare")
    c.add_argument("--a", required=True)
    c.add_argument("--b", required=True)
    c.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
