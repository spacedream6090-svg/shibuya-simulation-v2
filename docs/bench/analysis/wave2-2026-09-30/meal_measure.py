"""第 2 波 §2A 項 4: 古典の腕の食事の門 per_wake(既定=旧)と per_hour を並べる(計測だけ・判定しない)。

使い方(リポのルートで): ``python $D/meal_measure.py --out $D/item4_meal.json``

構成: classical(``--policy classical --chooser classical``)・語彙 v3・空腹 energy(CLI 既定)・5,000 体・seed 1・1 シミュ日。
交際の相手は既定(acquaintance)と旧(near_first)の 2 通り(項 3-1 の後の既定と、energy-classical §5b-7 の条件)。
量: 食事の回数(範囲内)・門を通った件数と段・食事の回数/体の分布・朝食の欠食率(20 代)・エネルギー収支/体・合成の
起床頻度 2 倍の感度(下)。壁時計は JSON に入れない。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def one(meal_gate: str, social: str) -> dict[str, Any]:
    from shibuya import cli

    res = cli.run(n_agents=5000, seed=1, world_dir="data/world/v2", vocab_version="v3", policy="classical",
                  chooser="classical", meal_gate=meal_gate, classical_social=social)
    m = res.run_manifest_fields()
    c = m["classical"]["counts"]
    e = dict(res.energy)
    return {
        "meal_gate": meal_gate, "classical_social": social,
        "final": res.final_hash[:16], "calls": int(res.llm_calls),
        "meals_in_area": int(res.meals),
        "gate_passed": int(c.get("meal", 0)),
        "gate_passed_by_stage": {k.split(":")[1]: int(v) for k, v in sorted(c.items()) if k.startswith("meal_stage:")},
        "meals_per_agent": e.get("meals_per_agent"),
        "breakfast_skip": e.get("breakfast_skip"),
        "balance_kcal": e.get("balance_kcal"),
        "census_per_agent": e.get("census_per_agent"),
        "stage_time_share": e.get("stage_time_share"),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    rows = []
    for social in ("acquaintance", "near_first"):
        for gate in ("per_wake", "per_hour"):
            r = one(gate, social)
            rows.append(r)
            print(json.dumps({k: r[k] for k in ("meal_gate", "classical_social", "final", "calls", "meals_in_area",
                                                "gate_passed", "gate_passed_by_stage", "balance_kcal")},
                             ensure_ascii=False), flush=True)
    doc = {"schema": "shibuya.bench/wave2-2026-09-30/meal-gate/1",
           "how": "classical 5,000 体・seed 1・v3・energy・1 シミュ日。per_wake=既定(旧)・per_hour=Q48 (a)。判定しない",
           "rows": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
