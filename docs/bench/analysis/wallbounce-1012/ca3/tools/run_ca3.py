"""第 6 期 6-2 カレンダー 3: 腕 arm(+C1+カレンダー 2)の 5,000 体のラン(計器・監査・2 日と再開=通し)を回して JSON に書く(1 本ずつ)。

使い方(リポの根で・作業木の src を ``PYTHONPATH`` に):

    python docs/bench/analysis/wallbounce-1012/ca3/tools/run_ca3.py one --start 2026-07-26 --days 1 --scratch <git の外> --out <JSON>
    python docs/bench/analysis/wallbounce-1012/ca3/tools/run_ca3.py one --start 2026-07-26 --days 2 --activity off --scratch <…> --out <JSON>
    python docs/bench/analysis/wallbounce-1012/ca3/tools/run_ca3.py one --start 2026-07-19 --days 2 --activity off --scratch <…> --out <JSON>
    python docs/bench/analysis/wallbounce-1012/ca3/tools/run_ca3.py resume --start 2026-07-26 --days 2 --stop 1440 --activity off --scratch <…> --out <JSON>

どのランも腕 ``--calendar-3 arm``・``--contact c1``・``--calendar-2 arm`` と試験用の印(``SHIBUYA_CALENDAR_3_TRIAL=on``=日曜始まり・
祝日を含むランを分析に使わない印で回す)。``--events off`` は出来事の記録を外したラン(記録の有無で final と checkpoint の
behavior-hash が同じかを比べる)。``--activity off`` は活動層を外したラン(日曜 → 月曜の日の頭で計画境界の表が変わる=活動層の
あるランは K9 の張り直しの外で止まる=記録 §限界)。絶対パスは JSON に書かない。
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


def _arm(*, events: str = "on") -> None:
    from shibuya.engine.calendar2 import arm as A2
    from shibuya.engine.calendar3 import arm as A3
    from shibuya.engine.contact import arm as AC
    from shibuya.engine.events import log as EV

    A2.set_arm("arm")
    AC.set_arm("c1")
    A3.set_arm("arm")
    A3.set_trial("on")
    EV.set_enabled(events == "on")


def _summary(r: Any, wall: float) -> dict[str, Any]:
    from shibuya.engine.calendar2.layer import audit_causes as au2
    from shibuya.engine.calendar3.layer import audit_causes as au3
    from shibuya.engine.contact.layer import audit_causes as au1

    m = r.run_manifest_fields()
    cc = m["calendar_3"]
    evs = list(r.event_log.events())
    work = [e for e in evs if str(e.what).startswith("勤務:")]
    cp = [[int(c.tick), c.behavior_hash] for c in r.checkpoints]
    return {
        "final": r.final_hash, "llm_calls": int(r.llm_calls), "wall_s": round(wall, 1),
        "calls_by_model": m.get("calls_by_model"),
        "events_by_what": dict(sorted(Counter(e.what for e in work).items())),
        "audit": {"calendar_3": au3(evs, step_ns=STEP_NS, issued=r.calendar3_layer.issued_keys()),
                  "contact_c1": au1(evs, step_ns=STEP_NS, issued=r.contact_layer.issued_keys()),
                  "calendar_2": au2(evs, step_ns=STEP_NS, issued=r.calendar2_layer.issued_keys())},
        "event_log": {"rows": int(sum(r.event_log.what_counts().values())), "nbytes": int(r.event_log.nbytes),
                      "cause_nbytes": int(r.event_log.cause_nbytes), "work_rows": len(work)},
        "calendar_3": {k: v for k, v in cc.items() if k not in ("meter",)},
        "meter": cc["meter"],
        "calendar_days": [{k: d[k] for k in ("date", "weekday", "holiday", "rest_day")}
                          for d in m.get("calendar", {}).get("days", [])] if isinstance(m.get("calendar"), dict) else None,
        "checkpoints_behavior": cp,
    }


def _kw(args: argparse.Namespace) -> dict[str, Any]:
    kw: dict[str, Any] = dict(n_agents=args.agents, seed=args.seed, world_dir=args.world, vocab_version="v3",
                              start_sim_datetime=args.start)
    if args.days != 1:
        kw["sim_days"] = args.days
    if args.activity == "off":
        kw["activity"] = "off"
    return kw


def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli

    _arm(events=args.events)
    t0 = time.perf_counter()
    r = cli.run(**_kw(args))
    doc = {"mode": "one", "agents": args.agents, "seed": args.seed, "start": args.start, "days": args.days,
           "activity": args.activity, "events": args.events, **_summary(r, time.perf_counter() - t0)}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                              newline="\n")
    print(doc["final"], doc["wall_s"], doc["audit"])
    return 0


def _cp(r: Any, stop: int) -> list[Any]:
    return [(int(c.tick), c.behavior_hash, c.full_hash) for c in r.checkpoints if int(c.tick) >= stop]


def cmd_resume(args: argparse.Namespace) -> int:
    from shibuya import cli

    _arm()
    kw = dict(_kw(args), checkpoint_every=60)
    scratch = Path(args.scratch)
    t0 = time.perf_counter()
    straight = cli.run(**kw)
    w_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    a = cli.run(state_out=str(scratch / "state"), stop_at_tick=args.stop, **kw)
    path = scratch / "state" / a.resume["state_files"][-1]["file"]
    b = cli.run(resume_from=str(path), **kw)
    w_r = time.perf_counter() - t0
    ms, mb = straight.run_manifest_fields()["calendar_3"], b.run_manifest_fields()["calendar_3"]
    same = {k: ms[k] == mb[k] for k in ("roster", "composed", "work_days_per_week", "rest", "contacts", "rows", "late",
                                         "labor_over", "holiday", "live", "calls")}
    doc = {"mode": "resume", "agents": args.agents, "seed": args.seed, "start": args.start, "days": args.days,
           "stop": args.stop, "activity": args.activity, "state_file": path.name,
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
        sp.add_argument("--start", default="2026-07-26")
        sp.add_argument("--days", type=int, default=1)
        sp.add_argument("--activity", default="on", choices=("on", "off"))
        sp.add_argument("--scratch", required=True)
        sp.add_argument("--out", required=True)
        if name == "one":
            sp.add_argument("--events", default="on", choices=("on", "off"))
        if name == "resume":
            sp.add_argument("--stop", type=int, default=1440)
    args = ap.parse_args(argv)
    return cmd_one(args) if args.cmd == "one" else cmd_resume(args)


if __name__ == "__main__":
    sys.exit(main())
