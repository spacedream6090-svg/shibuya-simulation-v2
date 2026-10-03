"""第 2 波 §2A の byte-check(HEAD b4c8b1c と作業木を同じランで比べる)。

使い方(リポのルートで・``$D`` = この置き場):

    # 1) HEAD の src を OS の一時ディレクトリへ展開(git archive HEAD src docs/bench/anchors
    #    docs/design/v2-budget-declaration.md docs/bench/analysis/w6-regen-2026-09-28)
    # 2) HEAD 側
    python $D/wave2_bytecheck.py side --src <展開した場所>/src --label head --scratch <作業用> --out <作業用>/head.json
    # 3) 作業木の既定 / 旧の切替口をすべて付けた側
    python $D/wave2_bytecheck.py side --label work --scratch <作業用> --out <作業用>/work.json
    python $D/wave2_bytecheck.py side --label work_old --old '<旧の切替口の JSON>' --scratch <作業用> --out <作業用>/work_old.json
    # 4) 比べる
    python $D/wave2_bytecheck.py compare --head <作業用>/head.json --work <作業用>/work.json \
        --work-old <作業用>/work_old.json --out $D/<名>.json

構成(``CONFIGS``): W6 再生成の 15 腕(``w6_regen_measure.ARMS``=既定で動いてはならない)+
本段で触る腕 4 本(店の記憶・関係・古典・古典+記憶+関係)。各ランは mock/classical 5,000 体・seed 1・
1 シミュ日・テープつき。比べる値: final・呼数・blocks(行数と全列の sha)・calls の 14 列の sha(prompt_hash を含む)。

- ``work`` は 15 腕すべてと「既定で動かない」と宣言した腕で HEAD と一致しなければならない。
- ``work_old``(旧の切替口をすべて付けた作業木)は**全構成**で HEAD と一致しなければならない。

壁時計は決定論でないので JSON の比較には使わない。絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
W6 = HERE.parent / "w6-regen-2026-09-28" / "w6_regen_measure.py"
CLS = {"policy": "classical", "chooser": "classical"}


def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def configs() -> dict[str, dict[str, Any]]:
    w6 = _load(W6, "w6_regen_measure")
    out = {f"w6_{k}": dict(v) for k, v in w6.ARMS.items()}
    out.update({
        # 本段で触る腕(既定では off の腕・古典)
        "v3_mem_store": {"vocab_version": "v3", "memory": "on", "store_memory": "on"},
        "v3_mem_rel": {"vocab_version": "v3", "memory": "on", "relations": "on"},
        "v3_classical": {"vocab_version": "v3", **CLS},
        "v3_classical_mem_rel": {"vocab_version": "v3", "memory": "on", "relations": "on", **CLS},
    })
    return out


def _h(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:16]


def cmd_one(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    import shibuya
    from shibuya import cli

    kw = dict(configs()[args.config])
    kw.update(json.loads(args.old or "{}"))
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape, **kw)
    calls = pq.read_table(Path(args.tape) / "calls.parquet")
    blocks = pq.read_table(Path(args.tape) / "blocks.parquet")
    src_root = Path(shibuya.__file__).resolve().parents[1]
    print(json.dumps({
        "config": args.config,
        "src_is_worktree": src_root == (REPO / "src").resolve(),
        "final": res.final_hash[:16],
        "calls": int(res.llm_calls),
        "blocks_rows": int(blocks.num_rows),
        "blocks_sha": _h({n: blocks.column(n).to_pylist() for n in blocks.column_names}),
        "calls_columns_sha": {n: _h(calls.column(n).to_pylist()) for n in calls.column_names},
        "wall_s": round(time.perf_counter() - t0, 1),
    }, ensure_ascii=False))
    return 0


def cmd_side(args: argparse.Namespace) -> int:
    scratch = Path(args.scratch)
    names = list(configs()) if not args.only else [s for s in args.only.split(",") if s]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if args.src:
        env["PYTHONPATH"] = str(Path(args.src).resolve())
        env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"

    def one(name: str) -> dict[str, Any]:
        cmd = [sys.executable, str(Path(__file__)), "one", "--config", name, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed),
               "--tape", str(scratch / f"{args.label}_{name}"), "--old", args.old or ""]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            return {"config": name, "error": r.stderr[-2000:]}
        return json.loads(r.stdout.strip().splitlines()[-1])

    got: dict[str, Any] = {}
    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        for row in ex.map(one, names):
            got[row["config"]] = row
            print(row["config"], row.get("final"), row.get("calls"), row.get("wall_s"),
                  row.get("src_is_worktree"), (row.get("error") or "")[-300:], flush=True)
    doc = {"label": args.label, "old": json.loads(args.old or "{}"), "runs": got}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def _eq(h: dict[str, Any], w: dict[str, Any]) -> dict[str, Any]:
    cols = sorted(h.get("calls_columns_sha", {}))
    diff = [k for k in cols if h["calls_columns_sha"][k] != w.get("calls_columns_sha", {}).get(k)]
    return {
        "final_equal": h.get("final") == w.get("final"),
        "calls_equal": h.get("calls") == w.get("calls"),
        "blocks_equal": (h.get("blocks_sha"), h.get("blocks_rows")) == (w.get("blocks_sha"), w.get("blocks_rows")),
        "calls_columns_differ": diff,
        "all_equal": (h.get("final") == w.get("final") and h.get("calls") == w.get("calls")
                      and (h.get("blocks_sha"), h.get("blocks_rows")) == (w.get("blocks_sha"), w.get("blocks_rows"))
                      and not diff),
    }


def cmd_compare(args: argparse.Namespace) -> int:
    head = json.loads(Path(args.head).read_text(encoding="utf-8"))
    work = json.loads(Path(args.work).read_text(encoding="utf-8"))
    old = json.loads(Path(args.work_old).read_text(encoding="utf-8")) if args.work_old else None
    moved = set(s for s in args.expect_moved.split(",") if s)
    rows = []
    ok = True
    # 検収後: HEAD 側が本当に HEAD の写しを読んだか(作業木の src を読んでいたら不一致として止める)・
    # 作業木側が作業木を読んだか・エラーの行が無いか
    src_errors: list[str] = []
    for side, doc_, want in (("head", head, False), ("work", work, True)) + ((("work_old", old, True),) if old else ()):
        for name, row in doc_["runs"].items():
            if row.get("error") or row.get("src_is_worktree") is not want:
                src_errors.append(f"{side}:{name}:src_is_worktree={row.get('src_is_worktree')}"
                                  + (":error" if row.get("error") else ""))
    if src_errors:
        ok = False
        print("SRC_MISMATCH", src_errors, flush=True)
    for name, h in head["runs"].items():
        w = work["runs"].get(name, {})
        row: dict[str, Any] = {"config": name, "head_final": h.get("final"), "head_calls": h.get("calls"),
                               "work_final": w.get("final"), "work_calls": w.get("calls"),
                               "default_may_move": name in moved, "work": _eq(h, w)}
        if name not in moved and not row["work"]["all_equal"]:
            ok = False
        if old is not None:
            o = old["runs"].get(name, {})
            row["work_old_final"] = o.get("final")
            row["work_old"] = _eq(h, o)
            ok = ok and row["work_old"]["all_equal"]
        rows.append(row)
        print(name, "work=" + ("=" if row["work"]["all_equal"] else "≠" + ("(想定)" if name in moved else "!!")),
              "old=" + (("=" if row["work_old"]["all_equal"] else "≠!!") if old is not None else "-"), flush=True)
    doc = {"schema": "shibuya.bench/wave2-2026-09-30/byte-check/1", "head": args.head_label,
           "note": args.note, "old_switches": (old or {}).get("old", {}), "expect_moved": sorted(moved),
           "how": ("mock/classical 5,000 体・seed 1・1 シミュ日・テープつき。HEAD(git archive の src)と作業木で同じ構成を回し、"
                   "final・呼数・blocks・calls 14 列の sha を比べる。work=作業木の既定・work_old=旧の切替口をすべて付けた作業木"),
           "src_checks": src_errors or "ok(HEAD 側=写し・作業木側=作業木・エラー行なし)",
           "all_ok": ok, "rows": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("ALL_OK" if ok else "MISMATCH")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("one", "side"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        sp.add_argument("--old", default="")
        if name == "one":
            sp.add_argument("--config", required=True)
            sp.add_argument("--tape", required=True)
        else:
            sp.add_argument("--src", default="")
            sp.add_argument("--label", required=True)
            sp.add_argument("--scratch", required=True)
            sp.add_argument("--out", required=True)
            sp.add_argument("--only", default="")
            sp.add_argument("--jobs", type=int, default=6)
    sp = sub.add_parser("compare")
    sp.add_argument("--head", required=True)
    sp.add_argument("--work", required=True)
    sp.add_argument("--work-old", default="")
    sp.add_argument("--head-label", default="b4c8b1c")
    sp.add_argument("--expect-moved", default="")
    sp.add_argument("--note", default="")
    sp.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
