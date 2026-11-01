"""第 2 期 2-2 の検収の直しで見つけた穴の探り: 在席の印 poi_ref が付いたまま店のセルの外に居る体の数(腕 cell・5,000 体・1 日)。

    python docs/bench/analysis/wallbounce-1012/prox22/tools/probe_poi_ref.py cell   # 1 行の JSON を出す(記録 §2-1)
"""
import json
import sys

import numpy as np

sys.path.insert(0, 'src')
from shibuya import cli  # noqa: E402
from shibuya.agents.state import Activity  # noqa: E402
from shibuya.engine import proximity as P  # noqa: E402
from shibuya.engine.processes import crowd as C  # noqa: E402

P.set_arm(sys.argv[1] if len(sys.argv) > 1 else 'cell')
st = {"steps": 0, "seated": 0, "seated_moving": 0, "seated_other_cell": 0, "seated_not_shopping": 0,
      "max_seated_other_cell": 0, "pairs_same_unit": 0, "pairs_same_unit_other_cell": 0}
orig = C.CrowdProcess.step


def step(self, t):
    r = self.agents.registry
    pr = np.asarray(r.poi_ref).astype(np.int64)
    s = pr >= 0
    if s.any():
        pc = np.asarray(self.world.pois.cell, dtype=np.int64)
        cell = np.asarray(r.cell).astype(np.int64)
        act = np.asarray(r.activity)
        oc = s & (cell != pc[np.clip(pr, 0, None)])
        st["steps"] += 1
        st["seated"] += int(s.sum())
        st["seated_moving"] += int((s & (act == int(Activity.MOVING))).sum())
        st["seated_other_cell"] += int(oc.sum())
        st["seated_not_shopping"] += int((s & (act != int(Activity.SHOPPING))).sum())
        st["max_seated_other_cell"] = max(st["max_seated_other_cell"], int(oc.sum()))
        u, cnt = np.unique(pr[s], return_counts=True)
        st["pairs_same_unit"] += int((cnt * (cnt - 1) // 2).sum())
        ok = s & ~oc
        u2, cnt2 = np.unique(pr[ok], return_counts=True)
        st["pairs_same_unit_other_cell"] += int((cnt * (cnt - 1) // 2).sum() - (cnt2 * (cnt2 - 1) // 2).sum())
    return orig(self, t)


C.CrowdProcess.step = step
res = cli.run(n_agents=5000, seed=1, world_dir='data/world/v2', vocab_version='v3', memory='on')
st["final"] = res.final_hash[:16]
print(json.dumps(st))
