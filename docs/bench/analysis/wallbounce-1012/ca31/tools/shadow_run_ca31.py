# -*- coding: utf-8 -*-
"""ca31(第 3 期 3-1 暦 1a 影)の記録の道具: 腕 1a のランの影の計器(manifest の ``calendar_shadow``)を控える。

- ``one``: 1 本のラン(既定 5,000 体・seed 1・語彙 v3 の既定・世界資産は組んだ資産 ``data/world/v2_stage_3-1``)を腕
  ``--calendar-shadow 1a``(``--arm``)で回し、``calendar_shadow`` の節と final・呼数・計画実行層の計数を JSON に書く。
  ``--days`` で複数日(開始日の検査 A1-3=連続する平日の範囲=07-13 の月曜から 5 日まで。週末は回さない=CA10)。
  25 欄の動いた量は 10e の byte-check の道具(``byte_check_10e.py side`` に ``SHIBUYA_CALENDAR_SHADOW=1a``)で取る。

使い方(リポの根で・作業木の src=``PYTHONPATH``):
    python docs/bench/analysis/wallbounce-1012/ca31/tools/shadow_run_ca31.py one --out <置き場>/shadow_1d.json
    python docs/bench/analysis/wallbounce-1012/ca31/tools/shadow_run_ca31.py one --days 5 --out <置き場>/shadow_5d.json

絶対パスは JSON に書かない。壁時計は記録だけ(比べない)。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]


def _summary(res: Any) -> dict[str, Any]:
    m = res.run_manifest_fields()
    cs = m["calendar_shadow"]
    days = []
    for d in cs.get("days") or []:
        days.append({k: d[k] for k in ("day", "date", "weekday", "table_weekday", "holiday", "week", "week_wrapped",
                                       "agents", "shadows", "blanks", "next_day_end", "commute_min", "place_kind",
                                       "recurrence", "depart_hist15", "start_hist15", "end_hist15", "return_hist15",
                                       "actor_rate15")}
                    | ({"w17_ref": d["w17_ref"]} if "w17_ref" in d else {}))
    return {
        "final": res.final_hash[:16], "calls": int(res.llm_calls),
        "behavior_last": res.checkpoints[-1].behavior_hash if res.checkpoints else "",
        "presence_counters": dict(res.presence_counters), "run_kind": m.get("run_kind"),
        "calendar_shadow": {k: cs[k] for k in ("schema", "source", "w20", "weeks", "shadows", "blanks")},
        "days": days,
    }


def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.engine import calendar_shadow as CS

    CS.set_arm(args.arm)
    kw: dict[str, Any] = {"vocab_version": "v3"}
    if args.days > 1:
        kw["sim_days"] = int(args.days)
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
    out = {"arm": args.arm, "agents": args.agents, "seed": args.seed, "days": args.days,
           "world": Path(args.world).as_posix(), "kw": kw, **_summary(res),
           "wall_s_nondeterministic": round(time.perf_counter() - t0, 1),
           "src_is_worktree": Path(__import__("shibuya").__file__).resolve().parents[1] == (REPO / "src").resolve()}
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(out["final"], out["calls"], out["calendar_shadow"]["shadows"], out["wall_s_nondeterministic"])
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("one")
    sp.add_argument("--arm", default="1a", choices=("w17", "1a"))
    sp.add_argument("--agents", type=int, default=5_000)
    sp.add_argument("--seed", type=int, default=1)
    sp.add_argument("--days", type=int, default=1)
    from shibuya.engine.calendar_shadow import STAGE_DIR

    sp.add_argument("--world", default=STAGE_DIR)
    sp.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    return {"one": cmd_one}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
