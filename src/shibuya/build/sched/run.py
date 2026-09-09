"""build.sched.run — スケジュール生成レーン(W17)の段階を実行する CLI。

    python -m shibuya.build.sched.run --out data/world/v2 [--data data] [--shard 0/8]

- 段階は純関数(§0-1)。出力とヘッダ ``W17.header.json`` を ``--out`` に書く。
- **LLM は呼ばない**。応答 jsonl(``w17_responses*.jsonl``)が ``--out`` に在れば取り込んで
  凍結し、無ければプロンプトだけ書いて「応答未取得」を報告する。
- 本 CLI は manifest を書かない(``python -m shibuya.build.run`` の仕事)。
- ゲートが1つでも落ちたら終了コード 1。

手順(親の運用):
  1. ``python -m shibuya.build.sched.run --out data/world/v2 --shard 0/8``  # プロンプト生成
     (シャードを分けると ``w17_prompts.0of8.jsonl`` … が出る。艦隊のノードに配る)
  2. サーバー上で ``python3 tools/gen/fleet_gen.py --prompts w17_prompts.0of8.jsonl \\
       --out w17_responses.0of8.jsonl --endpoints http://127.0.0.1:8100,... --conc 8``
  3. 応答 jsonl を ``data/world/v2/`` へ置いて ``--shard`` なしでもう一度   # 検証・凍結

パイロット(本番 39 万呼の前に種別横断で書式・語彙・出力長を測る):
  1. ``python -m shibuya.build.sched.run --out data/world/v2 --pilot 40``
     → ``w17_pilot_prompts.jsonl``(9 種別 × 40 体・決定論)
  2. ``python3 tools/gen/fleet_gen.py --prompts w17_pilot_prompts.jsonl \\
       --out w17_pilot_responses.jsonl --endpoints … --conc 8``
  3. ``python -m shibuya.build.sched.run --out data/world/v2 --pilot 40 --pilot-ingest``
     → 取り込んで**報告だけ**する(parquet も W17.header.json も書かない)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Callable

from ..geo import common as C
from ..geo.run import print_gate_table
from . import STAGES, w17_schedule

__all__ = ["STAGE_FUNCS", "run_stages", "parse_shard", "run_pilot", "main"]

STAGE_FUNCS: dict[str, Callable[[C.Ctx], C.StageResult]] = {"W17": w17_schedule.run}


def parse_shard(spec: str | None) -> tuple[int, int]:
    """``"0/8"`` → ``(0, 8)``。``None`` は ``(0, 1)``(分割なし)。

    Example:
        >>> parse_shard(None), parse_shard("2/8")
        ((0, 1), (2, 8))
    """
    if not spec:
        return (0, 1)
    a, _, b = str(spec).partition("/")
    shard, n = int(a), int(b or 1)
    if n < 1 or not (0 <= shard < n):
        raise ValueError("--shard は i/n(0 <= i < n)")
    return shard, n


def run_stages(
    ctx: C.Ctx, stages: list[str], verbose: bool = True, *, shard: int = 0, n_shards: int = 1
) -> list[C.StageResult]:
    """段階を順に実行してヘッダを書く(``geo.run.run_stages`` と同形)。"""
    ctx.out.mkdir(parents=True, exist_ok=True)
    results: list[C.StageResult] = []
    for st in stages:
        t0 = time.perf_counter()
        res = w17_schedule.run(ctx, shard=shard, n_shards=n_shards)
        C.write_header(ctx.out, res)
        results.append(res)
        if verbose:
            dt = time.perf_counter() - t0
            print(f"[{st}] {dt:6.2f}s  outputs={len(res.outputs)}  gates_pass={res.all_passed}")
    return results


def run_pilot(ctx: C.Ctx, per_kind: int, *, ingest: bool = False) -> int:
    """パイロット標本を書く(+ 応答があれば取り込んで報告する)。**段階ヘッダは書かない**。

    ``--pilot N`` は「種別ごとに N 体」= 9 種別で 9N 体。本番 39 万呼の前に、種別を
    またいで書式・語彙・出力長を測るための標本(決定論・seed 固定)。
    ``--pilot-ingest`` は ``w17_pilot_responses.jsonl`` を取り込んで**報告だけ**する
    (parquet も ``W17.header.json`` も書かない=本番の資産を汚さない)。
    """
    facts = w17_schedule.build_facts(ctx.out, ctx.data)
    rec = w17_schedule.write_pilot_prompts(ctx.out, facts, per_kind)
    print(
        f"[W17 pilot] {rec['path']} rows={rec['rows']} "
        f"({per_kind}/種別) sha256={rec['sha256'][:16]}… "
        f"bytes={rec['bytes']:,} 入力tok 平均={rec['prompt_tokens_mean']} "
        f"最大={rec['prompt_tokens_max']}"
    )
    print(f"[W17 pilot] 種別内訳 {rec['kinds']}")
    if not ingest:
        return 0
    resp = ctx.out / w17_schedule.PILOT_RESPONSES_NAME
    if not resp.exists():
        print(f"応答が無い: {resp}", file=sys.stderr)
        return 2
    report, _ = w17_schedule.ingest(ctx.out, ctx.data, facts=facts, responses=[resp])
    body = report.to_json()
    for key in ("n_with_response", "n_skeleton_fallback", "n_activities",
                "activities_per_agent", "modified_rate", "parse_fail_rate",
                "parse_reasons", "repair_rules", "completion_tokens"):
        print(f"[W17 pilot] {key} = {body[key]}")
    print(f"[W17 pilot] raking = {body['raking']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m shibuya.build.sched.run")
    ap.add_argument("--out", required=True, type=Path, help="出力ディレクトリ(例 data/world/v2)")
    ap.add_argument("--data", type=Path, default=Path("data"), help="入力データ根(既定 data)")
    ap.add_argument("--stage", action="append", choices=list(STAGES), help="実行する段階")
    ap.add_argument("--shard", default="", help="プロンプトの分割 i/n(既定=分割なし)")
    ap.add_argument(
        "--pilot", type=int, default=0,
        help="種別ごとに N 体のパイロット用プロンプトだけを書く(w17_pilot_prompts.jsonl)",
    )
    ap.add_argument(
        "--pilot-ingest", action="store_true",
        help="w17_pilot_responses.jsonl を取り込んで報告だけする(資産は書かない)",
    )
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    stages = [s for s in STAGES if args.stage is None or s in args.stage]
    ctx = C.Ctx(data=args.data.resolve(), out=args.out.resolve())
    if not ctx.data.exists():
        print(f"入力データ根が無い: {ctx.data}", file=sys.stderr)
        return 2
    if args.pilot or args.pilot_ingest:
        return run_pilot(ctx, max(1, args.pilot), ingest=args.pilot_ingest)
    try:
        shard, n_shards = parse_shard(args.shard)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    results = run_stages(ctx, stages, verbose=not args.quiet, shard=shard, n_shards=n_shards)
    return 0 if print_gate_table(results) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
