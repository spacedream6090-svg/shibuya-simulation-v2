"""1-8b 発話の口の直し(口の約束 1-3 の (1)): 腕 ``--speech-port on`` の 5,000 体 1 日のランを 1 本回して JSON に書く(記録 on/off・新旧)。

使い方(リポの根か HEAD の写しの根で・その木の src を ``PYTHONPATH`` に・5,000 体のランは 1 本ずつ):

    python docs/bench/analysis/wallbounce-1012/s8b/tools/run_s8_onoff.py --events on  --label wt_on  --out <JSON>
    python docs/bench/analysis/wallbounce-1012/s8b/tools/run_s8_onoff.py --events off --label wt_off --out <JSON>
    python docs/bench/analysis/wallbounce-1012/s8b/tools/run_s8_onoff.py compare --a <JSON> --b <JSON> --out <JSON>

構成: 腕 ``--speech-port on``・記憶と関係 on(会話が起きる=発話の口が動く・byte-check の ``v3_mem_rel`` に腕を足した形)。
1 本: final・checkpoint の behavior-hash の列・発話の口の計器(記録の側の ``events`` を除く)・発話の出来事の行の数・原因の入力の
出来事 id の数・壁時計。``compare``: 2 本の final・checkpoint の列・計器が同じか。絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.engine.events import log as EV
    from shibuya.engine.speech import layer as SPL
    from shibuya.engine.speech.port import WHAT

    SPL.set_arm("on")
    EV.set_enabled(args.events == "on")
    t0 = time.perf_counter()
    r = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, vocab_version="v3", memory="on",
                relations="on")
    wall = time.perf_counter() - t0
    port = r.speech_layer
    evs = [e for e in r.event_log.events() if e.what == WHAT]
    log = r.event_log
    n_in = n_in_speech = 0
    for e in evs:
        for eid in getattr(e.cause, "input_event_ids", ()):
            n_in += 1
            if log.get(eid).what == WHAT:
                n_in_speech += 1
    meter = {k: v for k, v in port.meter.items() if k != "events"}
    doc: dict[str, Any] = {
        "label": args.label, "agents": args.agents, "seed": args.seed, "world": args.world, "events": args.events,
        "final": r.final_hash, "wall_s": round(wall, 1),
        "checkpoints_behavior": [[int(c.tick), c.behavior_hash] for c in r.checkpoints],
        "speech_rows": len(evs), "cause_inputs": n_in, "cause_inputs_speech": n_in_speech,
        "mark_table_rows_end": int(len(getattr(port, "_mark_event_of", {}))),
        "inbox_rows_end": int(sum(len(q) for q in port.inbox.values())),
        "meter": meter,
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                              newline="\n")
    print(doc["final"], doc["wall_s"], doc["speech_rows"], meter.get("said"))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    a = json.loads(Path(args.a).read_text(encoding="utf-8"))
    b = json.loads(Path(args.b).read_text(encoding="utf-8"))
    moved = {k: [a["meter"].get(k), b["meter"].get(k)] for k in sorted(set(a["meter"]) | set(b["meter"]))
             if a["meter"].get(k) != b["meter"].get(k)}
    doc = {
        "a": {k: a[k] for k in ("label", "events", "final", "speech_rows", "wall_s")},
        "b": {k: b[k] for k in ("label", "events", "final", "speech_rows", "wall_s")},
        "final_same": a["final"] == b["final"],
        "checkpoints_behavior_same": a["checkpoints_behavior"] == b["checkpoints_behavior"],
        "n_checkpoints": len(a["checkpoints_behavior"]),
        "first_checkpoint_differ": next((x[0] for x, y in zip(a["checkpoints_behavior"], b["checkpoints_behavior"])
                                         if x != y), None),
        "meter_same": not moved, "meter_moved": moved, "note": args.note,
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
