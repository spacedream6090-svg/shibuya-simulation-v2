"""第 5 期 空間の段 1 の診断(検収 M4 (a) の後): 指定の刻みの速さ 0 のセルと、上位のセルの体の内訳(面の上/建物の中/移動中)・
面積・人/m²(数えるだけ・ランは変えない)。

    python $D/tools/diag_density_sp1.py data/world/v2_stage_5-1 480,720,1080

逐次ループ宣言: なし(道具・ランの外)。
"""
import json
import sys

import numpy as np

from shibuya import cli
from shibuya.agents.state import Activity
from shibuya.engine import resolve as R

orig = R.apply
snap = {}
TICKS = tuple(int(x) for x in (sys.argv[2].split(",") if len(sys.argv) > 2 else ["720"]))


def wrapped(plan_confirmed, losers, agents, world, tick, *a, **kw):
    out = orig(plan_confirmed, losers, agents, world, tick, *a, **kw)
    geom = kw.get("geometry")
    if int(tick) in TICKS and getattr(geom, "is_nav", False):
        r = agents.registry
        cell = np.asarray(r.cell, dtype=np.int64)
        act = np.asarray(r.activity)
        allc = np.asarray(world.cells.density, dtype=np.float64)
        surf = geom.surface_counts(r)
        rho = surf / geom.density_area_m2
        fac = geom.kladek_factor(np.arange(surf.size), surf)
        on = cell >= 0
        moving = act == int(Activity.MOVING)
        stage = np.asarray(world.cells.density_stage)
        top = np.argsort(-rho)[:8]
        snap[int(tick)] = {
            "scale": geom.population_scale, "cells_speed0": int((fac <= 0.0).sum()),
            "speed_factor_min": round(float(fac.min()), 3),
            "stage_hist": {str(int(k)): int(v) for k, v in zip(*np.unique(stage, return_counts=True))},
            "rho_p50_p90_max_occupied": np.percentile(rho[surf > 0], [50, 90, 100]).round(3).tolist() if (surf > 0).any() else [],
            "agents_on_stage": int(on.sum()), "agents_counted_on_surface": int(surf.sum()),
            "top_cells": [{"cell": int(c), "walkable_m2": round(float(geom.walkable_area_raw_m2[c]), 1),
                           "band": int(geom.cell_band[c]), "all": int(allc[c]), "on_surface": int(surf[c]),
                           "inside": int(allc[c] - surf[c]), "moving": int((on & moving & (cell == c)).sum()),
                           "rho": round(float(rho[c]), 2), "speed_factor": round(float(fac[c]), 3)} for c in top.tolist()]}
    return out


R.apply = wrapped
res = cli.run(n_agents=5000, seed=1, ticks=max(TICKS) + 1, world_dir=sys.argv[1], space="nav1", vocab_version="v3")
print(json.dumps(snap, ensure_ascii=False, indent=1))
