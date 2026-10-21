"""第 6 期 6-4 C1 の直し(口の約束 1-3 の (1)): 腕 c1 の 5,000 体 1 日のランを 1 本回して JSON に書く(記録 on/off の比べ・新旧の比べ)。

使い方(リポの根か HEAD の写しの根で・その木の src を ``PYTHONPATH`` に・5,000 体のランは 1 本ずつ):

    python docs/bench/analysis/wallbounce-1012/ct_c1/tools/run_c1_onoff.py --events on  --label wt_on  --out <JSON>
    python docs/bench/analysis/wallbounce-1012/ct_c1/tools/run_c1_onoff.py --events off --label wt_off --out <JSON>
    python docs/bench/analysis/wallbounce-1012/ct_c1/tools/run_c1_onoff.py compare --a <JSON> --b <JSON> --out <JSON>

1 本: final・checkpoint の behavior-hash の列・連絡の出来事の行の数(語ごと)・監査(発行した呼びとの突き合わせつき)・
manifest の ``contact_c1`` の計器(``events:`` の計数を除く=記録の有無で数が違うのは記録の側の数)・壁時計。
``compare``: 2 本の final・checkpoint の列・計器が同じかと前後の値。絶対パスは JSON に書かない。
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


def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.engine.contact import arm as AC
    from shibuya.engine.contact.layer import audit_causes
    from shibuya.engine.events import log as EV

    AC.set_arm("c1")
    EV.set_enabled(args.events == "on")
    t0 = time.perf_counter()
    r = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, vocab_version="v3")
    wall = time.perf_counter() - t0
    m = r.run_manifest_fields()
    cc = m["contact_c1"]
    evs = [e for e in r.event_log.events() if str(e.what).startswith("連絡:")]
    lay = r.contact_layer
    au = audit_causes(r.event_log.events(), step_ns=STEP_NS, issued=lay.issued_keys())
    meter = {k: v for k, v in cc["meter"].items() if not str(k).startswith("events:")}
    doc = {
        "label": args.label, "agents": args.agents, "seed": args.seed, "world": args.world, "events": args.events,
        "final": r.final_hash, "wall_s": round(wall, 1),
        "checkpoints_behavior": [[int(c.tick), c.behavior_hash] for c in r.checkpoints],
        "contact_rows": len(evs), "contact_rows_by_what": dict(sorted(Counter(e.what for e in evs).items())),
        "audit": au, "issued": int(len(lay.issued_keys())),
        "event_id_tables": {"ct_event_of_rows": int(sum(len(v) for v in getattr(lay, "_ct_event_of", {}).values())),
                            "speech_event_of_rows": int(len(getattr(lay.speech, "_mark_event_of", {})))},
        "inbox_row_lengths": sorted({len(x) for v in lay.mail._inbox.values() for x in v}),
        "calls_by_model": m.get("calls_by_model"),
        "meter": meter,
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                              newline="\n")
    print(doc["final"], doc["wall_s"], au["violations"], doc["contact_rows"])
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    a = json.loads(Path(args.a).read_text(encoding="utf-8"))
    b = json.loads(Path(args.b).read_text(encoding="utf-8"))
    mk = set(a["meter"]) | set(b["meter"])
    moved = {k: [a["meter"].get(k), b["meter"].get(k)] for k in sorted(mk) if a["meter"].get(k) != b["meter"].get(k)}
    doc = {
        "a": {k: a[k] for k in ("label", "events", "final", "contact_rows", "wall_s")},
        "b": {k: b[k] for k in ("label", "events", "final", "contact_rows", "wall_s")},
        "final_same": a["final"] == b["final"],
        "checkpoints_behavior_same": a["checkpoints_behavior"] == b["checkpoints_behavior"],
        "n_checkpoints": len(a["checkpoints_behavior"]),
        "first_checkpoint_differ": next((x[0] for x, y in zip(a["checkpoints_behavior"], b["checkpoints_behavior"])
                                         if x != y), None),
        "meter_same": not moved, "meter_moved": moved,
        "audit": {"a": a["audit"]["violations"], "b": b["audit"]["violations"]},
        "note": args.note,
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                              newline="\n")
    print(doc["final_same"], doc["checkpoints_behavior_same"], doc["meter_same"], doc["first_checkpoint_differ"])
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "compare":
        ap = argparse.ArgumentParser()
        ap.add_argument("--a", required=True)
        ap.add_argument("--b", required=True)
        ap.add_argument("--note", default="")
        ap.add_argument("--out", required=True)
        return cmd_compare(ap.parse_args(argv[1:]))
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--events", default="on", choices=("on", "off"))
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    return cmd_one(ap.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
