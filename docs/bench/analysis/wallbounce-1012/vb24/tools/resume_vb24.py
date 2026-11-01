"""第 2 期 2-4: 再開=通し(5,000 体・2 日・日の境目=1 日目の終わりで保存 → 2 日目を再開)。md23 の ``resume`` と同じ形で、
腕は**今の既定**のまま(``--proximity`` などを渡したときだけ置く=旧値の切替口の確かめ)。

    python docs/bench/analysis/wallbounce-1012/vb24/tools/resume_vb24.py --world data/world/v2_stage_2-4 \
        --scratch <作業用> --label V2 --out <作業用>/resume_V2.json

土台は byte-check の ``v3_mem_rel``(語彙 v3・記憶 on・関係 on=md23 と同じ)と ``w6_v3_default``(語彙 v3 だけ)の 2 つ
(``--base``)。比べるもの: final・日の境目の後の checkpoint(behavior/full)・呼数。終了コード 0=全部同じ。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

BASES: dict[str, dict[str, Any]] = {
    "v3_mem_rel": {"vocab_version": "v3", "memory": "on", "relations": "on"},
    "w6_v3_default": {"vocab_version": "v3"},
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--base", choices=tuple(BASES), default="v3_mem_rel")
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--proximity", default="")
    ap.add_argument("--economy-stage2", default="")
    ap.add_argument("--seat-release", default="")
    a = ap.parse_args(argv)
    from shibuya import cli
    from shibuya.core.time_consts import STEPS_PER_DAY
    from shibuya.engine import economy_stage2 as ES2
    from shibuya.engine import proximity as PX

    if a.proximity:
        PX.set_arm(a.proximity)
    if a.economy_stage2:
        ES2.set_arm(a.economy_stage2)
    arms = {"proximity": PX.arm(), "economy_stage2": ES2.arm()}
    try:
        from shibuya.engine import seat_release as SR

        if a.seat_release:
            SR.set_arm(a.seat_release)
        arms["seat_release"] = SR.arm()
    except ImportError:
        arms["seat_release"] = "(口なし)"
    tpd = int(STEPS_PER_DAY)
    kw: dict[str, Any] = dict(BASES[a.base], n_agents=a.agents, seed=a.seed, sim_days=2, world_dir=a.world)
    base = Path(a.scratch) / f"resume_vb24_{a.label}_{a.base}"
    base.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    straight = cli.run(**kw)
    first = cli.run(**kw, state_out=str(base / "a"), stop_at_tick=tpd)
    sf = [f for f in first.resume["state_files"] if int(f.get("T", -1)) == tpd] or first.resume["state_files"][-1:]
    resumed = cli.run(**kw, resume_from=str(base / "a" / sf[-1]["file"]))

    def cp(r: Any) -> list:
        return [(int(c.tick), str(c.behavior_hash)[:16], str(c.full_hash)[:16]) for c in r.checkpoints if int(c.tick) >= tpd]

    doc = {"label": a.label, "base": a.base, "arms": arms, "agents": a.agents, "seed": a.seed,
           "straight_final": str(straight.final_hash)[:16], "resumed_final": str(resumed.final_hash)[:16],
           "same_final": straight.final_hash == resumed.final_hash,
           "checkpoints_after_boundary_same": cp(straight) == cp(resumed), "n_checkpoints_compared": len(cp(resumed)),
           "calls": [int(straight.llm_calls), int(first.llm_calls) + int(resumed.llm_calls)],
           "wall_s_nondeterministic": round(time.perf_counter() - t0, 1)}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc, ensure_ascii=False))
    return 0 if doc["same_final"] and doc["checkpoints_after_boundary_same"] else 1


if __name__ == "__main__":
    sys.exit(main())
