"""段 2b(行き先を対象欄から・D-112 ②)の腕の計測: mock の移動の対象にカテゴリ語/見えている名を出す。

使い方(リポジトリの根から)::

    python docs/bench/analysis/intent-chooser-2026-09-28/move_measure.py \\
        --world data/world/v2 --out docs/bench/analysis/intent-chooser-2026-09-28/move_arms.json

腕(mock 5,000・seed 1・語彙 v3)
- ``p0``: 既定(``mock_move_target_p=0``=移動の対象は なし/あたり だけ=既定 checkpoint)。
- ``p0.1`` / ``p0.5``: 移動(あたりでない行)の対象を確率 p でカテゴリ語か B2 に見えている名にする。
- 各 p に **2b 無し**の比較腕(``..._2b_off``): ``TargetResolver.resolve_move`` を「全行 -1=従来の既定」
  に差し替える(**計測だけの差し込み**・同じ mock の出力で行き先の決め方だけが違う)。

出力: final・呼数・``move_resolution``・移動の失敗(対象不正/経路なし)・購入/食事・行為の件数。
絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

PS: tuple[float, ...] = (0.0, 0.1, 0.5)


def run_arm(name: str, p: float, world: str, agents: int, seed: int, off: bool) -> dict[str, Any]:
    from shibuya import cli
    from shibuya.engine import poi_target as PT

    orig = PT.TargetResolver.resolve_move
    if off:
        def no_move(self, agents_, tick, agent_ids, action_code, targets, rows):  # noqa: ARG001
            return np.full(np.asarray(agent_ids).size, -1, dtype=np.int64)
        PT.TargetResolver.resolve_move = no_move  # type: ignore[method-assign]
    try:
        t0 = time.perf_counter()
        res = cli.run(n_agents=agents, seed=seed, world_dir=world, vocab_version="v3",
                      mock_move_target_p=p)
        dt = time.perf_counter() - t0
    finally:
        PT.TargetResolver.resolve_move = orig  # type: ignore[method-assign]
    row = {
        "arm": name,
        "mock_move_target_p": p,
        "resolve_move": not off,
        "final_hash": res.final_hash,
        "llm_calls": int(res.llm_calls),
        "move_resolution": dict(res.move_resolution),
        "move_bad_target": int(res.move_bad_target),
        "move_unreachable": int(res.move_unreachable),
        "moves_applied": int(res.action_usage.get("移動", 0)),
        "engine_steps": int(res.action_usage.get("(エンジン継続)", 0)),
        "purchases": int(res.column("purchases").sum()) if res.diagnostics.size else 0,
        "meals": int(res.meals),
        "conserved": bool(res.conserved),
    }
    print(f"{name}: final {res.final_hash[:16]}… calls {row['llm_calls']:,} ({dt:.1f}s)", flush=True)
    return row


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    rows = []
    for p in PS:
        rows.append(run_arm(f"p{p}", p, args.world, args.agents, args.seed, off=False))
        rows.append(run_arm(f"p{p}_2b_off", p, args.world, args.agents, args.seed, off=True))
    Path(args.out).write_text(
        json.dumps({"schema": "shibuya.bench/intent-chooser-2026-09-28/move/1",
                    "n_agents": args.agents, "seed": args.seed, "arms": rows},
                   ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
