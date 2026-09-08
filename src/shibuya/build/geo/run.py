"""build.geo.run — 段階を W 番号順に実行し、ヘッダと build_manifest.json を書く CLI。

    python -m shibuya.build.geo.run --out data/world/v2 [--stage W1 --stage W2] [--data data]

- 各段階は純関数(§0-1)。出力とヘッダ ``<stage>.header.json`` を ``--out`` に書く。
- ``build_manifest.json`` = {stages:[ヘッダ], build_hash}。
  ``build_hash`` = W 番号順に並べた**全出力の sha256 を連結**した文字列の sha256。
- ゲートが1つでも落ちたら終了コード 1。
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Callable

from . import STAGES, common as C
from . import (
    w0_crs,
    w1_walk_graph,
    w2_cells,
    w3_distances,
    w4_heights,
    w5_entrances,
    w6_poi_org,
    w11_station_exits,
)

__all__ = ["STAGE_FUNCS", "run_stages", "write_build_manifest", "main"]

STAGE_FUNCS: dict[str, Callable[[C.Ctx], C.StageResult]] = {
    "W0": w0_crs.run,
    "W1": w1_walk_graph.run,
    "W2": w2_cells.run,
    "W3": w3_distances.run,
    "W4": w4_heights.run,
    "W5": w5_entrances.run,
    "W6": w6_poi_org.run,
    "W11": w11_station_exits.run,
}

MANIFEST_NAME = "build_manifest.json"


def run_stages(ctx: C.Ctx, stages: list[str], verbose: bool = True) -> list[C.StageResult]:
    ctx.out.mkdir(parents=True, exist_ok=True)
    results: list[C.StageResult] = []
    for st in stages:
        t0 = time.perf_counter()
        res = STAGE_FUNCS[st](ctx)
        C.write_header(ctx.out, res)
        results.append(res)
        if verbose:
            dt = time.perf_counter() - t0
            print(f"[{st}] {dt:6.2f}s  outputs={len(res.outputs)}  gates_pass={res.all_passed}")
    return results


def write_build_manifest(ctx: C.Ctx) -> dict[str, Any]:
    """out ディレクトリに存在する段階ヘッダから manifest を組む(W 番号順)。"""
    headers: list[dict[str, Any]] = []
    digests: list[str] = []
    for st in STAGES:
        path = ctx.out / f"{st}.header.json"
        if not path.exists():
            continue
        header = C.load_json(path)
        headers.append(header)
        digests.extend(o["sha256"] for o in header["outputs"])
    manifest = {
        "schema": "shibuya.build.geo/build_manifest/1",
        "stage_order": [h["stage"] for h in headers],
        "stages": headers,
        "build_hash": C.sha256_bytes("".join(digests).encode("utf-8")),
    }
    path = ctx.out / MANIFEST_NAME
    path.write_bytes(C.canonical_json_bytes(manifest) + b"\n")
    return manifest


def print_gate_table(results: list[C.StageResult]) -> bool:
    rows: list[tuple[str, str, str, str, str]] = [("stage", "gate", "value", "expected", "pass")]
    ok_all = True
    for res in results:
        for g in res.gates:
            j = g.to_json()
            ok_all &= bool(j["pass"])
            rows.append(
                (
                    res.stage,
                    g.name,
                    str(j["value"]),
                    "-" if j["expected"] is None else str(j["expected"]),
                    "PASS" if j["pass"] else "FAIL",
                )
            )
    widths = [max(len(r[i]) for r in rows) for i in range(5)]
    for i, r in enumerate(rows):
        print(" | ".join(r[k].ljust(widths[k]) for k in range(5)))
        if i == 0:
            print("-+-".join("-" * w for w in widths))
    return ok_all


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m shibuya.build.geo.run")
    ap.add_argument("--out", required=True, type=Path, help="出力ディレクトリ(例 data/world/v2)")
    ap.add_argument("--data", type=Path, default=Path("data"), help="入力データ根(既定 data)")
    ap.add_argument(
        "--stage",
        action="append",
        choices=list(STAGES),
        help="実行する段階(繰り返し可・既定=全段階)",
    )
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    stages = [s for s in STAGES if args.stage is None or s in args.stage]
    ctx = C.Ctx(data=args.data.resolve(), out=args.out.resolve())
    if not ctx.data.exists():
        print(f"入力データ根が無い: {ctx.data}", file=sys.stderr)
        return 2

    results = run_stages(ctx, stages, verbose=not args.quiet)
    manifest = write_build_manifest(ctx)
    ok = print_gate_table(results)
    print(f"build_hash = {manifest['build_hash']}")
    print(f"stages     = {','.join(manifest['stage_order'])}")
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
