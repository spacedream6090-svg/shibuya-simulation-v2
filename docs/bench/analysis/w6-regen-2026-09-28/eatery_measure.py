"""段 1b(D-96 nightlife (b))の計測: 飲食店の切替口 ``--eatery {food,place_food}`` の前後。

使い方(リポジトリの根から)::

    python docs/bench/analysis/w6-regen-2026-09-28/eatery_measure.py \\
        --world data/world/v2 --out docs/bench/analysis/w6-regen-2026-09-28/eatery_1b.json

測るもの(mock 5,000 体・seed 1・1 シミュ日)
- 構造: 飲食店マスクの件数と、**23 時以降に食事が成立しうる POI 数**(月曜の W7 営業行列で
  23:00 に開いている飲食店・23:00〜翌 5:00 のどこかで開いている飲食店)。
- ラン: final・呼数・食事の成立数(``meals``)・食事の試み(``_apply_eat`` に入った体の数=
  「並ぶ」からの委譲を含む)・失敗の内訳(飲食店でない/閉店/所持金不足)・時刻別の成立数・
  深夜(23:00〜翌 5:00)に成立した食事の数と店の数。

**計測だけの差し込み**: ``engine.resolve`` の ``_apply_eat``/``_complete_eat`` を数えるだけの
包みに差し替える(引数も戻り値も触らない)。包んだランの final が包まないランと同じであることを
``--check-instrumentation`` で確かめられる。絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

#: 腕(語彙版 × 飲食店の切替口)。v3 既定=CLI の既定。v1 は「食事」が無い=腕が効かない対照。
ARMS: dict[str, dict[str, Any]] = {
    "v3_food": {"vocab_version": "v3", "eatery": "food"},
    "v3_place_food": {"vocab_version": "v3", "eatery": "place_food"},
    "v2_food": {"vocab_version": "v2", "eatery": "food"},
    "v2_place_food": {"vocab_version": "v2", "eatery": "place_food"},
    "v1_food": {"vocab_version": "v1", "eatery": "food"},
    "v1_place_food": {"vocab_version": "v1", "eatery": "place_food"},
}
#: 深夜の時刻(時)。
LATE_HOURS: tuple[int, ...] = (23, 0, 1, 2, 3, 4)


class EatCounter:
    """``resolve._apply_eat``/``_complete_eat`` を数える包み(挙動は触らない)。"""

    def __init__(self) -> None:
        self.attempts_by_hour: Counter[int] = Counter()
        self.meals_by_hour: Counter[int] = Counter()
        self.fail: Counter[str] = Counter()
        self.late_meal_pois: set[int] = set()
        self._orig: dict[str, Any] = {}

    def install(self) -> None:
        from shibuya.engine import resolve as R

        orig_apply, orig_complete = R._apply_eat, R._complete_eat
        self._orig = {"apply": orig_apply, "complete": orig_complete}
        codes = {
            "not_in_eatery": int(R.ResultCode.NOT_IN_EATERY),
            "closed": int(R.ResultCode.CLOSED),
            "money_short": int(R.ResultCode.MONEY_SHORT),
        }
        counter = self

        def apply_eat(agents, world, aid, tgt, tick, out, schedule):
            hour = (int(tick) // 60) % 24
            counter.attempts_by_hour[hour] += int(np.asarray(aid).size)
            before = {k: out.per_result.get(c, 0) for k, c in codes.items()}
            orig_apply(agents, world, aid, tgt, tick, out, schedule)
            for k, c in codes.items():
                counter.fail[k] += out.per_result.get(c, 0) - before[k]

        def complete_eat(agents, world, eaters, shops, paid, tick, out):
            n0 = out.n_meals
            orig_complete(agents, world, eaters, shops, paid, tick, out)
            n = out.n_meals - n0
            hour = (int(tick) // 60) % 24
            counter.meals_by_hour[hour] += n
            if n and hour in LATE_HOURS:
                counter.late_meal_pois.update(int(s) for s in np.asarray(shops).tolist())

        R._apply_eat = apply_eat
        R._complete_eat = complete_eat
        for table in (R._APPLY_V2, R._APPLY_V3):
            table[R.ACT_EAT] = apply_eat

    def uninstall(self) -> None:
        from shibuya.engine import resolve as R

        R._apply_eat = self._orig["apply"]
        R._complete_eat = self._orig["complete"]
        for table in (R._APPLY_V2, R._APPLY_V3):
            table[R.ACT_EAT] = self._orig["apply"]


def structure(world_dir: str) -> dict[str, Any]:
    """飲食店マスクの件数と、23 時以降に開いている飲食店の数(月曜・W7 の営業行列)。"""
    from shibuya.engine.processes.opening import build_open_matrix
    from shibuya.world import assets as WA
    from shibuya.world.state import World

    w = World.load_or_synthetic(world_dir, n_cells=139, seed=1)
    pa = WA.load_process_assets(Path(world_dir), w.assets)
    m = build_open_matrix(w.n_poi, pa.plan_poi, pa.plan_day, pa.plan_start, pa.plan_end, 0)
    late = np.zeros(w.n_poi, dtype=bool)
    for h in LATE_HOURS:
        late |= m[:, h * 60 : h * 60 + 60].any(axis=1)
    out: dict[str, Any] = {}
    for mode in ("food", "place_food"):
        w.set_eatery_mode(mode)
        e = np.asarray(w.eatery_mask, dtype=bool)
        out[mode] = {
            "eatery_pois": int(e.sum()),
            "open_at_12": int((e & m[:, 12 * 60]).sum()),
            "open_at_19": int((e & m[:, 19 * 60]).sum()),
            "open_at_22": int((e & m[:, 22 * 60]).sum()),
            "open_at_23": int((e & m[:, 23 * 60]).sum()),
            "open_at_01": int((e & m[:, 1 * 60]).sum()),
            "open_any_23_to_05": int((e & late).sum()),
            "cells_with_eatery_open_at_23": int(np.unique(np.asarray(w.pois.cell)[e & m[:, 23 * 60]]).size),
        }
    return out


def run_arm(name: str, kw: dict[str, Any], world: str, agents: int, seed: int,
            instrument: bool = True) -> dict[str, Any]:
    from shibuya import cli

    c = EatCounter()
    if instrument:
        c.install()
    try:
        t0 = time.perf_counter()
        res = cli.run(n_agents=agents, seed=seed, world_dir=world, **kw)
        dt = time.perf_counter() - t0
    finally:
        if instrument:
            c.uninstall()
    attempts = sum(c.attempts_by_hour.values())
    late_meals = sum(c.meals_by_hour[h] for h in LATE_HOURS)
    row = {
        "arm": name,
        "args": dict(kw),
        "final_hash": res.final_hash,
        "checkpoints": {str(k.tick): k.combined for k in res.checkpoints},
        "llm_calls": int(res.column("calls").sum()) if res.diagnostics.size else 0,
        "meals": int(res.meals),
        "meal_yen": int(res.meal_yen),
        "purchases": int(res.column("purchases").sum()) if res.diagnostics.size else 0,
        "action_usage": dict(res.action_usage),
        "eatery": res.run_manifest_fields().get("eatery"),
        "conserved": bool(res.conserved),
    }
    if instrument:
        row.update(
            {
                "eat_attempts": attempts,
                "eat_fail": dict(c.fail),
                "meal_rate": round(int(res.meals) / attempts, 4) if attempts else None,
                "meals_by_hour": {str(h): int(c.meals_by_hour[h]) for h in range(24)},
                "attempts_by_hour": {str(h): int(c.attempts_by_hour[h]) for h in range(24)},
                "late_meals_23_to_05": int(late_meals),
                "late_meal_distinct_pois": len(c.late_meal_pois),
                "meals_counted_equals_result": sum(c.meals_by_hour.values()) == int(res.meals),
            }
        )
    print(f"{name}: final {res.final_hash[:16]}… meals {row['meals']:,} ({dt:.1f}s)", flush=True)
    return row


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--check-instrumentation", action="store_true",
                    help="v3_place_food を包まずにも回し、final が同じことを確かめる")
    args = ap.parse_args(argv)
    arms = dict(ARMS)
    if args.only:
        arms = {k: ARMS[k] for k in args.only.split(",") if k}
    doc: dict[str, Any] = {
        "schema": "shibuya.bench/w6-regen-2026-09-28/eatery-1b/1",
        "n_agents": args.agents,
        "seed": args.seed,
        "structure": structure(args.world),
        "arms": [run_arm(k, v, args.world, args.agents, args.seed) for k, v in arms.items()],
    }
    if args.check_instrumentation:
        plain = run_arm("v3_place_food(no-instrument)", ARMS["v3_place_food"], args.world,
                        args.agents, args.seed, instrument=False)
        inst = next((r for r in doc["arms"] if r["arm"] == "v3_place_food"), None)
        doc["instrumentation_is_transparent"] = (
            inst is not None and inst["final_hash"] == plain["final_hash"]
        )
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
