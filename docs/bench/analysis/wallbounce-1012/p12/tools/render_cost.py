"""1-2: 描画 1 回の時間を「状態 → Percept → 文」(作業木)と 1-2 の前の描画(HEAD の写し)で比べる(作業用の道具)。

合成の世界(セル 139・体 5,000)で、同じ体の並び・同じ刻みの描画を交互の順に回し、1 回あたりの µs の中央値を出す
(``perceive`` と ``render_percept`` の内訳も)。絶対パスは書かない。

使い方(リポの根で): ``python docs/bench/analysis/wallbounce-1012/p12/tools/render_cost.py --out <json>``
(``PYTHONPATH=src``=作業木の src。HEAD の写しは ``tests/perception/facts/head_renderer_136fdbb.py``)
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))

from shibuya.perception import renderer as R  # noqa: E402
from tests.perception.facts.scenes import build, twin  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--cells", type=int, default=139)
    ap.add_argument("--renders", type=int, default=4_000)
    ap.add_argument("--rounds", type=int, default=7)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    w, a = build(n_agents=args.agents, n_cells=args.cells, seed=21)
    r = R.Renderer(w, a, seed=7)
    h = twin(r)
    ids = list(range(0, args.agents, max(1, args.agents // args.renders)))[: args.renders]
    res: dict[str, list[float]] = {"new": [], "head": [], "perceive": [], "render_percept": []}
    for k in range(args.rounds):
        t = 600 + k
        r.prepare_tick(t)
        h.prepare_tick(t)
        order = (("new", r), ("head", h)) if k % 2 == 0 else (("head", h), ("new", r))
        for name, obj in order:
            t0 = time.perf_counter()
            for i in ids:
                obj.render(i, tick=t, wake_reason=3)
            res[name].append((time.perf_counter() - t0) / len(ids) * 1e6)
        t0 = time.perf_counter()
        ps = [r.perceive(i, t, wake_reason=3) for i in ids]
        res["perceive"].append((time.perf_counter() - t0) / len(ids) * 1e6)
        t0 = time.perf_counter()
        for p in ps:
            r.render_percept(p)
        res["render_percept"].append((time.perf_counter() - t0) / len(ids) * 1e6)
    doc = {
        "agents": args.agents, "cells": args.cells, "renders_per_round": len(ids), "rounds": args.rounds,
        "median_us": {k: round(statistics.median(v), 2) for k, v in res.items()},
        "all_us": {k: [round(x, 2) for x in v] for k, v in res.items()},
    }
    doc["delta_us_new_minus_head"] = round(doc["median_us"]["new"] - doc["median_us"]["head"], 2)
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc["median_us"], ensure_ascii=False), doc["delta_us_new_minus_head"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
