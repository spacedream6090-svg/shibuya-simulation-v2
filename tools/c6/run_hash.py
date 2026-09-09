# -*- coding: utf-8 -*-
"""run_hash.py — 1 ランの checkpoint ハッシュだけを JSON で吐く(**T3 の子プロセス**)。

運用設計書 §1.4 **T3 並列不変性**「スレッド 1/8/32 で同一結果」。
エンジンは単一プロセス・``prange`` を持たない(``engine.change_detect`` の numba カーネルは
``nogil`` の逐次ループ)ので、**並列度の口はコード側に無い**。代わりに numba / OpenMP /
MKL のスレッド数を環境変数で変えた 2 プロセスを突き合わせる。

使い方(親がサーバー/ローカルで)::

    NUMBA_NUM_THREADS=1 python tools/c6/run_hash.py --agents 5000 --ticks 24 --world data/world/v2
    NUMBA_NUM_THREADS=8 python tools/c6/run_hash.py --agents 5000 --ticks 24 --world data/world/v2
    # 出力の final_hash / checkpoints が一致すれば T3 合格

``--threads N`` を渡すと本プロセス内で ``numba.set_num_threads(N)`` も試みる
(numba が無い環境では黙って飛ばす)。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c6lib  # noqa: E402  (sys.path 調整のあと)


def main(argv: list[str] | None = None) -> int:
    ap = c6lib.common_parser("T3: 1 ランの checkpoint ハッシュを JSON で出す")
    ap.add_argument("--cells", type=int, default=139, help="合成世界のセル数")
    ap.add_argument("--threads", type=int, default=0, help="numba.set_num_threads(N)(0=触らない)")
    ap.add_argument("--no-ledger", action="store_true", help="台帳なし(engine.run.run_day 直呼び)")
    args = ap.parse_args(argv)

    if args.threads > 0:
        try:  # pragma: no cover - numba の有無に依存
            import numba

            numba.set_num_threads(int(args.threads))
        except Exception:
            pass

    from shibuya.engine.run import run_day
    from shibuya.world.state import World

    world_dir = c6lib.world_dir_of(args)
    world = World.load_or_synthetic(world_dir, n_cells=args.cells, seed=args.seed) if world_dir else None
    if args.no_ledger:
        res = run_day(
            n_agents=args.agents,
            seed=args.seed,
            world=world,
            ticks=args.ticks,
            checkpoint_every=max(1, args.ticks // 2),
            n_cells=args.cells,
            world_dir=world_dir,
        )
    else:
        res, _ = c6lib.run_smoke(
            n_agents=args.agents,
            seed=args.seed,
            ticks=args.ticks,
            world_dir=world_dir,
            checkpoint_every=max(1, args.ticks // 2),
        )

    payload = {
        "final_hash": res.final_hash,
        "checkpoints": [c.combined for c in res.checkpoints],
        "agents_hashes": [c.agents_hash for c in res.checkpoints],
        "world_hashes": [c.world_hash for c in res.checkpoints],
        "llm_calls": int(res.llm_calls),
        "conserved": bool(res.conserved),
        "diagnostics_day": {k: float(v) for k, v in res.diagnostics_day().items()},
        "env": {
            "NUMBA_NUM_THREADS": os.environ.get("NUMBA_NUM_THREADS", ""),
            "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS", ""),
            "MKL_NUM_THREADS": os.environ.get("MKL_NUM_THREADS", ""),
            "set_num_threads": int(args.threads),
        },
        "config": {
            "agents": int(args.agents),
            "ticks": int(args.ticks),
            "seed": int(args.seed),
            "cells": int(args.cells),
            "world": str(world_dir) if world_dir else "",
            "ledger": not args.no_ledger,
        },
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
