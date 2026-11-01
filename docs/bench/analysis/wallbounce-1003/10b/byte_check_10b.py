"""10b の byte-check(HEAD の写しと作業木を同じランで比べる)+behavior-hash・full-hash・checkpoint の費用の控え。

比べ方は [wave2_bytecheck.py](../../../wave2-2026-09-30/wave2_bytecheck.py) と同じ(19 構成=W6 の 15 腕+店の記憶・関係・
古典・古典+記憶+関係。mock/classical 5,000 体・seed 1・1 シミュ日・テープつき。final・呼数・blocks・calls 14 列)。
本スクリプトは ``one`` で作業木の側だけ ``behavior_hash``・``full_hash``・checkpoint の時間・外の状態のバイトを足して
出す(HEAD の写しには欄が無い=空)。比べるのは wave2 の ``compare`` と同じ 14 列で、2 つのハッシュは比べない(新しい欄)。

使い方(リポのルートで・``$D`` = この置き場・``$W`` = 作業用の一時ディレクトリ):

    git archive HEAD src docs/bench/anchors docs/design/v2-budget-declaration.md \\
        docs/bench/analysis/w6-regen-2026-09-28 | tar -x -C $W/head_src
    python $D/byte_check_10b.py side --src $W/head_src/src --label head --scratch $W --out $W/head.json
    python $D/byte_check_10b.py side --label work --scratch $W --out $W/work.json
    python $D/byte_check_10b.py compare --head $W/head.json --work $W/work.json --head-label <HEAD> --out $D/byte_check.json

壁時計(``wall_s``・``checkpoint_s``)は決定論でないので比較には使わない。絶対パスは JSON に書かない。
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
WAVE2 = REPO / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"


def _wave2() -> Any:
    spec = importlib.util.spec_from_file_location("wave2_bytecheck", WAVE2)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def cmd_one(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    import shibuya
    from shibuya import cli

    w2 = _wave2()
    kw = dict(w2.configs()[args.config])
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape, **kw)
    calls = pq.read_table(Path(args.tape) / "calls.parquet")
    blocks = pq.read_table(Path(args.tape) / "blocks.parquet")
    src_root = Path(shibuya.__file__).resolve().parents[1]
    last = res.checkpoints[-1] if res.checkpoints else None
    print(json.dumps({
        "config": args.config,
        "src_is_worktree": src_root == (REPO / "src").resolve(),
        "final": res.final_hash[:16],
        "calls": int(res.llm_calls),
        "blocks_rows": int(blocks.num_rows),
        "blocks_sha": w2._h({n: blocks.column(n).to_pylist() for n in blocks.column_names}),
        "calls_columns_sha": {n: w2._h(calls.column(n).to_pylist()) for n in calls.column_names},
        # ---- 10b の欄(HEAD の写しでは空) ----
        "behavior": [getattr(c, "behavior_hash", "")[:16] for c in res.checkpoints],
        "full": [getattr(c, "full_hash", "")[:16] for c in res.checkpoints],
        "behavior_last_full": getattr(last, "behavior_hash", "") if last is not None else "",
        "full_last_full": getattr(last, "full_hash", "") if last is not None else "",
        "full_external_bytes": int(sum(getattr(res, "full_hash_bytes", {}).values())),
        "full_external_bytes_by_row": dict(getattr(res, "full_hash_bytes", {})),
        "end_of_day": dict(getattr(res, "state_hashes_end_of_day", {}) or {}),
        "checkpoint_max_s": round(max(getattr(res, "checkpoint_seconds", []) or [0.0]), 4),
        "checkpoint_s": round(float(res.phase_seconds.get("checkpoint", 0.0)), 4),
        "n_checkpoints": len(res.checkpoints),
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
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            return {"config": name, "error": r.stderr[-2000:]}
        return json.loads(r.stdout.strip().splitlines()[-1])

    got: dict[str, Any] = {}
    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        for row in ex.map(one, names):
            got[row["config"]] = row
            print(row["config"], row.get("final"), row.get("calls"), row.get("checkpoint_s"),
                  row.get("src_is_worktree"), (row.get("error") or "")[-300:], flush=True)
    doc = {"label": args.label, "old": {}, "runs": got}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    w2 = _wave2()
    ns = argparse.Namespace(head=args.head, work=args.work, work_old="", expect_moved="",
                            head_label=args.head_label, note=args.note, out=args.out)
    rc = w2.cmd_compare(ns)
    doc = json.loads(Path(args.out).read_text(encoding="utf-8"))
    work = json.loads(Path(args.work).read_text(encoding="utf-8"))["runs"]
    head = json.loads(Path(args.head).read_text(encoding="utf-8"))["runs"]
    doc["how"] += "。10b の欄(work だけ): checkpoint ごとの behavior/full の先頭 16 桁・最後の値の全桁・外の状態のバイト・checkpoint の時間"
    doc["state_hashes_10b"] = {
        name: {
            "behavior": w.get("behavior"), "full": w.get("full"),
            "behavior_last": w.get("behavior_last_full"), "full_last": w.get("full_last_full"),
            "full_external_bytes": w.get("full_external_bytes"),
            "checkpoint_s_work": w.get("checkpoint_s"), "checkpoint_s_head": head.get(name, {}).get("checkpoint_s"),
            "n_checkpoints": w.get("n_checkpoints"),
            "end_of_day": w.get("end_of_day"), "checkpoint_max_s_work": w.get("checkpoint_max_s"),
        }
        for name, w in work.items()
    }
    doc["full_external_bytes_by_row_v3_default"] = work.get("w6_v3_default", {}).get("full_external_bytes_by_row")
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
        if name == "one":
            sp.add_argument("--config", required=True)
            sp.add_argument("--tape", required=True)
        else:
            sp.add_argument("--src", default="")
            sp.add_argument("--label", required=True)
            sp.add_argument("--scratch", required=True)
            sp.add_argument("--out", required=True)
            sp.add_argument("--only", default="")
            sp.add_argument("--jobs", type=int, default=4)
    sp = sub.add_parser("compare")
    sp.add_argument("--head", required=True)
    sp.add_argument("--work", required=True)
    sp.add_argument("--head-label", required=True)
    sp.add_argument("--note", default="10b: 状態台帳・behavior-hash と full-hash(記録だけ)・保留の組の call_id")
    sp.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
