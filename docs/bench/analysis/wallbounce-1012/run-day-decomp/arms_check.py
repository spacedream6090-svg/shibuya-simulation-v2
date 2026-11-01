"""1-0 T5 の追加: byte-check の 19 構成に無い腕(6 構成でも立たない腕)を、書きの検査(段 A・C)+段 B+番兵(T4)を入れて
回す(``SHIBUYA_SYSTEMS_CHECK``)。世界資産・300 体・seed 1・1 日(``--days 2`` で 2 日)。1 行の JSON を出す。

使い方: ``SHIBUYA_SYSTEMS_CHECK=3 python $D/arms_check.py <腕の名> [--days 2]``
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

ARMS = {
    "walk_exit": {"vocab_version": "v3", "exit_mode": "walk_to_platform"},
    "familiarity": {"vocab_version": "v3", "familiarity": "on"},
    "home_meal_plan": {"vocab_version": "v3", "home_meal": "plan", "meal_sleep_defer": "on"},
    "conv3": {"vocab_version": "v3", "memory": "on", "relations": "on", "conv_max_participants": 3},
    "attendance": {"vocab_version": "v3", "attendance_rate": 0.7},
    "store_wom": {"vocab_version": "v3", "memory": "on", "store_memory": "on", "wom_source": "reason-target"},
    "classical_per_hour": {"vocab_version": "v3", "policy": "classical", "chooser": "classical", "meal_gate": "per_hour"},
    "move_target": {"vocab_version": "v3", "mock_move_target_p": 0.3, "mock_out_of_cell_target_p": 0.3},
    "v2_edge_plateau": {"vocab_version": "v2", "geometry": "edge", "area_source": "plateau"},
    "no_presence": {"vocab_version": "v3", "plan_executor": False},
    "delay2": {"vocab_version": "v3", "response_delay": 2},
    "census": {"vocab_version": "v3", "census_out": "data/runs/1-0_final/census_arm"},
}


def main(argv: list[str]) -> int:
    from shibuya import cli

    name = argv[0]
    days = int(argv[argv.index("--days") + 1]) if "--days" in argv else 1
    out = {"arm": name, "kw": ARMS[name], "sim_days": days}
    t0 = time.perf_counter()
    try:
        r = cli.run(n_agents=300, seed=1, sim_days=days, ticks=1440, **ARMS[name])
        out.update({"ok": True, "final": r.final_hash[:16], "calls": int(r.llm_calls)})
    except Exception as e:  # noqa: BLE001 — 記録(書きの検査・段 B の落ち)
        tb = traceback.extract_tb(e.__traceback__)
        out.update({"ok": False, "error": f"{type(e).__name__}: {str(e)[:160]}",
                    "where": [f"{Path(f.filename).name}:{f.lineno}:{f.name}" for f in tb[-4:]]})
    out["wall_s"] = round(time.perf_counter() - t0, 1)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
