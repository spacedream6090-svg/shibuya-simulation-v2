"""build.field.run — 場・境界レーンの段階を W 番号順に実行する CLI。

    python -m shibuya.build.field.run --out data/world/v2 [--stage W7 --stage W10] [--data data]

- 各段階は純関数(§0-1)。出力とヘッダ ``<stage>.header.json`` を ``--out`` に書く。
- 本 CLI は **manifest を書かない**(build_hash は地理レーン込みの
  ``python -m shibuya.build.run`` が全段階分をまとめて書く)。
- ゲートが1つでも落ちたら終了コード 1。
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Callable

from ..geo.run import print_gate_table
from . import STAGES, common as C
from . import w7_planspec, w10_noise, w12_external_nodes, w13_weather

__all__ = ["STAGE_FUNCS", "run_stages", "main"]

STAGE_FUNCS: dict[str, Callable[[C.Ctx], C.StageResult]] = {
    "W7": w7_planspec.run,
    "W10": w10_noise.run,
    "W12": w12_external_nodes.run,
    "W13": w13_weather.run,
}


def run_stages(ctx: C.Ctx, stages: list[str], verbose: bool = True) -> list[C.StageResult]:
    """段階を順に実行してヘッダを書く(geo.run.run_stages と同形・段階表だけが違う)。"""
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m shibuya.build.field.run")
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
    ok = print_gate_table(results)
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
