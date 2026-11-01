"""第 6 期 6-2 カレンダー 2: 腕 arm の 5,000 体のラン(計器・監査・2 日と再開=通し)を回して JSON に書く(1 本ずつ)。

使い方(リポの根で・作業木の src を ``PYTHONPATH`` に):

    python docs/bench/analysis/wallbounce-1012/ca2/tools/run_ca2.py one --scratch <git の外> --out <JSON>
    python docs/bench/analysis/wallbounce-1012/ca2/tools/run_ca2.py one --contact c1 --scratch <…> --out <JSON>
    python docs/bench/analysis/wallbounce-1012/ca2/tools/run_ca2.py resume --days 2 --stop 1440 --scratch <…> --out <JSON>
    python docs/bench/analysis/wallbounce-1012/ca2/tools/run_ca2.py resume --days 1 --stop 720 --scratch <…> --out <JSON>

``one``: 1 日のラン 1 本(final・呼数・壁時計・manifest の ``calendar_2`` の計器・出来事の記録の約束の族の数・監査)。
``--events off`` は出来事の記録を外したラン(記録の有無で final と checkpoint の behavior-hash が同じかを比べる=checkpoint の
behavior-hash の列を JSON に出す)・``--calendar1b`` は腕 ``--calendar 1b`` と束ねたラン(W20 の週の表は ``SHIBUYA_CALENDAR_W20``・
既定 ``data/world/v2_stage_3-1/w20_calendar_1a.parquet``)。
``resume``: 通し 1 本と、``--stop`` で止めて状態のファイルから再開した 1 本を回し、final と ``--stop`` より後の checkpoint の
2 つのハッシュ・manifest の計器を比べる。絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

STEP_NS = 60 * 10**9


def _arm(contact: str, *, events: str = "on", calendar1b: bool = False) -> None:
    import os

    from shibuya.engine import calendar_self as C1B
    from shibuya.engine.calendar2 import arm as A
    from shibuya.engine.contact import arm as AC
    from shibuya.engine.events import log as EV

    A.set_arm("arm")
    AC.set_arm(contact)
    EV.set_enabled(events == "on")
    if calendar1b:
        os.environ.setdefault("SHIBUYA_CALENDAR_W20", "data/world/v2_stage_3-1/w20_calendar_1a.parquet")
        C1B.set_arm("1b")


def _summary(r: Any, wall: float) -> dict[str, Any]:
    from shibuya.engine.calendar2.layer import audit_causes

    m = r.run_manifest_fields()
    cc = m["calendar_2"]
    evs = [e for e in r.event_log.events() if str(e.what).startswith("約束:")]
    au = audit_causes(r.event_log.events(), step_ns=STEP_NS, issued=r.calendar2_layer.issued_keys())
    cp = [[int(c.tick), c.behavior_hash] for c in r.checkpoints]
    return {
        "final": r.final_hash, "llm_calls": int(r.llm_calls), "wall_s": round(wall, 1),
        "calls_by_model": m.get("calls_by_model"),
        "calendar2_calls": dict(zip(("judge_model", "llm"), r.calendar2_layer.model_calls())),
        "events_by_what": dict(sorted(Counter(e.what for e in evs).items())),
        "events_by_via": dict(sorted(Counter(e.via for e in evs).items())),
        "audit": au,
        "event_log": {"rows": int(sum(r.event_log.what_counts().values())), "nbytes": int(r.event_log.nbytes),
                      "cause_nbytes": int(r.event_log.cause_nbytes), "promise_rows": len(evs)},
        "calendar_2": {k: v for k, v in cc.items() if k not in ("meter",)},
        "meter": cc["meter"],
        "checkpoints_behavior": cp,
        "calendar_1b": {k: m["calendar_1b"][k] for k in ("totals", "checks")} if "calendar_1b" in m else None,
    }


def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli

    _arm(args.contact, events=args.events, calendar1b=args.calendar1b)
    t0 = time.perf_counter()
    r = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, vocab_version="v3")
    doc = {"mode": "one", "agents": args.agents, "seed": args.seed, "contact": args.contact, "events": args.events,
           "calendar1b": bool(args.calendar1b),
           **_summary(r, time.perf_counter() - t0)}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                              newline="\n")
    print(doc["final"], doc["wall_s"], doc["audit"])
    return 0


def _cp(r: Any, stop: int) -> list[Any]:
    return [(int(c.tick), c.behavior_hash, c.full_hash) for c in r.checkpoints if int(c.tick) >= stop]


def cmd_resume(args: argparse.Namespace) -> int:
    from shibuya import cli

    _arm(args.contact)
    kw = dict(n_agents=args.agents, seed=args.seed, world_dir=args.world, vocab_version="v3", sim_days=args.days,
              checkpoint_every=60)
    scratch = Path(args.scratch)
    t0 = time.perf_counter()
    straight = cli.run(**kw)
    w_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    a = cli.run(state_out=str(scratch / "state"), stop_at_tick=args.stop, **kw)
    path = scratch / "state" / a.resume["state_files"][-1]["file"]
    b = cli.run(resume_from=str(path), **kw)
    w_r = time.perf_counter() - t0
    ms, mb = straight.run_manifest_fields()["calendar_2"], b.run_manifest_fields()["calendar_2"]
    same = {k: ms[k] == mb[k] for k in ("promises", "responses", "arrival", "forgot", "plan_match", "impossible",
                                         "outside_plan", "intentions", "changes")}
    doc = {"mode": "resume", "agents": args.agents, "seed": args.seed, "days": args.days, "stop": args.stop,
           "contact": args.contact, "state_file": path.name,
           "straight": {"final": straight.final_hash, "wall_s": round(w_s, 1)},
           "resumed": {"final": b.final_hash, "wall_s": round(w_r, 1)},
           "final_same": straight.final_hash == b.final_hash,
           "checkpoints_after_stop_same": _cp(straight, args.stop) == _cp(b, args.stop),
           "n_checkpoints_after_stop": len(_cp(straight, args.stop)),
           "manifest_same": same,
           "straight_summary": _summary(straight, w_s)}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                              newline="\n")
    print(doc["final_same"], doc["checkpoints_after_stop_same"], same)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("one", "resume"):
        sp = sub.add_parser(name)
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--contact", default="off", choices=("off", "c1"))
        sp.add_argument("--scratch", required=True)
        sp.add_argument("--out", required=True)
        if name == "one":
            sp.add_argument("--events", default="on", choices=("on", "off"))
            sp.add_argument("--calendar1b", action="store_true")
        if name == "resume":
            sp.add_argument("--days", type=int, default=2)
            sp.add_argument("--stop", type=int, default=1440)
    args = ap.parse_args(argv)
    return cmd_one(args) if args.cmd == "one" else cmd_resume(args)


if __name__ == "__main__":
    sys.exit(main())
