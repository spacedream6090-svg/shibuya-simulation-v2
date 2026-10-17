"""1-2: byte-check の 19 構成で、ランの中の描画を全部 HEAD の描画の写し(双子)と比べ、構成ごとの件数を出す(作業用)。

``tests/perception/facts/test_render_from_percept_bytes.py`` の (B) と同じ比べ方(双子は 1-2 の描画と同じ物・同じ前計算の
材料・同じ描画の引数・想起は 1-2 の側が引いた行)。体の数と刻みの数を引数で変えられる(試験は 300 体・1,032 刻み)。
出すのは構成ごとの比べた描画の数・描画のあった刻みの数・代表の窓(朝・昼・夕)に入った刻み・違った描画(あれば先頭 5 件)。
絶対パスは書かない。

使い方(リポの根で・``PYTHONPATH=src``): ``python docs/bench/analysis/wallbounce-1012/p12/tools/shadow_counts.py --out <json>``
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))

import pytest  # noqa: E402

from tests.perception.facts import test_render_from_percept_bytes as M  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", type=int, default=M.N_AGENTS)
    ap.add_argument("--ticks", type=int, default=M.WINDOWS[-1][1])
    ap.add_argument("--only", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    from shibuya import cli

    configs = M._wave2_configs()
    names = [s for s in args.only.split(",") if s] or list(M.CONFIG_NAMES)
    rows = {}
    for name in names:
        mp = pytest.MonkeyPatch()
        try:
            stats = M._shadow(mp)
            t0 = time.perf_counter()
            with tempfile.TemporaryDirectory() as td:
                cli.run(n_agents=args.agents, seed=1, world_dir=str(REPO / "data" / "world" / "v2"), ticks=args.ticks,
                        tape_path=Path(td) / "tape", **dict(configs[name]))
            wall = time.perf_counter() - t0
        finally:
            mp.undo()
        ticks = sorted(stats["ticks"])
        rows[name] = {
            "renders_compared": int(stats["n"]),
            "steps_with_renders": len(ticks),
            "windows": {f"{lo}-{hi}": sum(1 for t in ticks if lo <= t < hi) for lo, hi in M.WINDOWS},
            "mismatches": len(stats["bad"]),
            "mismatch_head": [list(map(str, b)) for b in stats["bad"][:5]],
            "wall_s": round(wall, 1),
        }
        print(name, rows[name]["renders_compared"], rows[name]["steps_with_renders"], rows[name]["mismatches"],
              flush=True)
    doc = {"agents": args.agents, "ticks": args.ticks, "seed": 1, "rows": rows,
           "total_renders_compared": sum(r["renders_compared"] for r in rows.values()),
           "total_mismatches": sum(r["mismatches"] for r in rows.values())}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
