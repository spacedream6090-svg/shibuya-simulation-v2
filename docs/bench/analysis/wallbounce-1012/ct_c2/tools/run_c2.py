"""第 6 期 6-4 C2(連絡の道具の残り): 腕 c1 の 5,000 体のランを 1 本回して JSON に書く(習慣 off/on・1 日/2 日・記録 on/off・
再開)。

使い方(リポの根で・その木の src を ``PYTHONPATH`` に・5,000 体のランは 1 本ずつ):

    python docs/bench/analysis/wallbounce-1012/ct_c2/tools/run_c2.py one --habit off --days 1 --out <JSON>
    python docs/bench/analysis/wallbounce-1012/ct_c2/tools/run_c2.py one --habit on --days 2 --out <JSON>
    python docs/bench/analysis/wallbounce-1012/ct_c2/tools/run_c2.py one --habit on --days 1 --events off --out <JSON>
    python docs/bench/analysis/wallbounce-1012/ct_c2/tools/run_c2.py resume --habit on --days 2 --stop 2160 --scratch <git の外> --out <JSON>

段 B(系の宣言の外の書き込み)は ``SHIBUYA_SYSTEMS_CHECK=1`` を付けて回す(宣言の外があればランが止まる)。1 本: final・
checkpoint の behavior-hash・連絡の出来事の行の数(語ごと)・監査(発行した呼びとの突き合わせつき)・manifest の ``contact_c1`` の
内訳(習慣・交換・充電・ビデオ・道具)・calls_by_model・壁時計。絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

STEP_NS = 60 * 10**9


def _arm(habit: str, events: str) -> None:
    from shibuya.engine.contact import arm as AC
    from shibuya.engine.events import log as EV

    AC.set_arm("c1")
    AC.set_habit(habit)
    EV.set_enabled(events == "on")


def _kw(args: argparse.Namespace) -> dict[str, Any]:
    kw: dict[str, Any] = dict(n_agents=args.agents, seed=args.seed, world_dir=args.world, vocab_version="v3")
    if args.days != 1:
        kw["sim_days"] = args.days
    return kw


def _doc(r: Any, wall: float) -> dict[str, Any]:
    from shibuya.engine.contact.layer import audit_causes

    m = r.run_manifest_fields()
    cc = m["contact_c1"]
    evs = [e for e in r.event_log.events() if str(e.what).startswith("連絡:")]
    lay = r.contact_layer
    au = audit_causes(r.event_log.events(), step_ns=STEP_NS, issued=lay.issued_keys())
    return {
        "final": r.final_hash, "wall_s": round(wall, 1),
        "checkpoints_behavior": [[int(c.tick), c.behavior_hash] for c in r.checkpoints],
        "contact_rows": len(evs), "contact_rows_by_what": dict(sorted(Counter(e.what for e in evs).items())),
        "via": dict(sorted(Counter(e.via for e in evs).items())),
        "audit": au, "issued": int(len(lay.issued_keys())),
        "calls_by_model": m.get("calls_by_model"),
        "c2": {k: cc[k] for k in ("c2", "habit", "exchange", "charge", "video", "devices")},
        "meter_c1": {k: v for k, v in cc["meter"].items() if not str(k).startswith("events:")},
        "tools": m["tools"]["names"],
        "systems_check": os.environ.get("SHIBUYA_SYSTEMS_CHECK", ""),
    }


def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli

    _arm(args.habit, args.events)
    t0 = time.perf_counter()
    r = cli.run(**_kw(args))
    doc = {"mode": "one", "agents": args.agents, "seed": args.seed, "world": args.world, "days": args.days,
           "habit": args.habit, "events": args.events, **_doc(r, time.perf_counter() - t0)}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                              newline="\n")
    print(doc["final"], doc["wall_s"], doc["audit"]["violations"], doc["contact_rows"])
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    from shibuya import cli

    _arm(args.habit, args.events)
    kw = _kw(args)
    scratch = Path(args.scratch)
    t0 = time.perf_counter()
    straight = cli.run(**kw)
    w_s = time.perf_counter() - t0
    a = cli.run(state_out=str(scratch / "state"), stop_at_tick=args.stop, **kw)
    path = scratch / "state" / a.resume["state_files"][-1]["file"]
    t0 = time.perf_counter()
    b = cli.run(resume_from=str(path), **kw)
    w_r = time.perf_counter() - t0

    def cp(r: Any) -> list[Any]:
        return [(int(c.tick), c.behavior_hash, c.full_hash) for c in r.checkpoints if int(c.tick) >= args.stop]

    ms, mb = straight.run_manifest_fields()["contact_c1"], b.run_manifest_fields()["contact_c1"]
    # 状態(習慣の表・宛先の帳・道具・届いた箱・生きているチャット)は通しと同じ。計器(meter)は再開から数え直す(行 CT1M=捨ててよい)
    same = {"habit.book": (ms["habit"] or {}).get("book") == (mb["habit"] or {}).get("book"),
            "exchange.book": ms["exchange"]["book"] == mb["exchange"]["book"],
            "devices": ms["devices"] == mb["devices"], "mail": ms["mail"] == mb["mail"],
            "chats.live": ms["chats"].get("live") == mb["chats"].get("live"),
            "charge.plugged_now": ms["charge"]["plugged_now"] == mb["charge"]["plugged_now"]}
    doc = {"mode": "resume", "agents": args.agents, "seed": args.seed, "days": args.days, "habit": args.habit,
           "stop": args.stop, "state_file": path.name,
           "straight": {"final": straight.final_hash, "wall_s": round(w_s, 1)},
           "resumed": {"final": b.final_hash, "wall_s": round(w_r, 1)},
           "final_same": straight.final_hash == b.final_hash,
           "checkpoints_after_stop_same": cp(straight) == cp(b), "n_checkpoints_after_stop": len(cp(straight)),
           "manifest_same": same}
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
        sp.add_argument("--days", type=int, default=1)
        sp.add_argument("--habit", default="off", choices=("off", "on"))
        sp.add_argument("--events", default="on", choices=("on", "off"))
        sp.add_argument("--out", required=True)
        if name == "resume":
            sp.add_argument("--stop", type=int, default=2160)
            sp.add_argument("--scratch", required=True)
    args = ap.parse_args(sys.argv[1:] if argv is None else argv)
    return cmd_one(args) if args.cmd == "one" else cmd_resume(args)


if __name__ == "__main__":
    sys.exit(main())
