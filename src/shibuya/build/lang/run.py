"""build.lang.run — 静的言語化レーン(W14/W15)の段階を W 番号順に実行する CLI。

    python -m shibuya.build.lang.run --out data/world/v2 [--stage W14] [--data data]

- 各段階は純関数(§0-1)。出力とヘッダ ``<stage>.header.json`` を ``--out`` に書く。
- **LLM は呼ばない**。応答 jsonl(``w14_responses.jsonl``/``w15_responses.jsonl``)が
  ``--out`` に在れば取り込んで凍結し、無ければプロンプトだけ書いて「応答未取得」を報告する。
- 本 CLI は manifest を書かない(``python -m shibuya.build.run`` の仕事)。
- ゲートが1つでも落ちたら終了コード 1。

手順(親の運用):
  1. ``python -m shibuya.build.lang.run --out data/world/v2``         # プロンプト生成
  2. サーバー上で ``python3 tools/gen/fleet_gen.py --prompts w14_prompts.jsonl \\
       --out w14_responses.jsonl --endpoints http://127.0.0.1:8100,... --conc 8``
  3. 応答 jsonl を ``data/world/v2/`` へ置いて 1. をもう一度        # 検証・凍結
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Callable

from ..geo import common as C
from ..geo.run import print_gate_table
from . import STAGES
from . import w14_signage, w15_cell_static

__all__ = ["STAGE_FUNCS", "run_stages", "main"]

#: 段階名 → 段階関数(``build.run`` が引く)。
STAGE_FUNCS: dict[str, Callable[[C.Ctx], C.StageResult]] = {
    "W14": w14_signage.run,
    "W15": w15_cell_static.run,
}


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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m shibuya.build.lang.run")
    ap.add_argument("--out", required=True, type=Path, help="出力ディレクトリ(例 data/world/v2)")
    ap.add_argument("--data", type=Path, default=Path("data"), help="入力データ根(既定 data)")
    ap.add_argument("--stage", action="append", choices=list(STAGES), help="実行する段階")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    stages = [s for s in STAGES if args.stage is None or s in args.stage]
    ctx = C.Ctx(data=args.data.resolve(), out=args.out.resolve())
    if not ctx.data.exists():
        print(f"入力データ根が無い: {ctx.data}", file=sys.stderr)
        return 2

    results = run_stages(ctx, stages, verbose=not args.quiet)
    return 0 if print_gate_table(results) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
