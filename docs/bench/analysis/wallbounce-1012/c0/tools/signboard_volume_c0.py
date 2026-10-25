"""第 1 期 1-7(c0): 看板を読んだ出来事の腕(``SHIBUYA_TOOL_EVENTS``)を入れたときの行数と重さを、既定 v3 の構成で測る。

5,000 体・seed 1・1 日・mock(10e の byte-check の構成 ``w6_v3_default``)を腕 off と on で 1 本ずつ回し、final・呼数・
日次の記録の出来事の行数と ``道具:看板`` の行数・壁時計(目安)を出す。既定を on にするかの判断の材料(記録 c0/README.md §6)。

使い方(リポの根で・src を ``PYTHONPATH`` に): ``python <この置き場>/signboard_volume_c0.py [--out <json>] [--agents N]``。
絶対パスは出力に書かない。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
WAVE2 = REPO / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"


def _configs() -> dict:
    spec = importlib.util.spec_from_file_location("wave2_bytecheck", WAVE2)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.configs()


def main(argv: list[str] | None = None) -> int:
    from shibuya import cli
    from shibuya.engine.tools import record as TR

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--config", default="w6_v3_default")
    args = ap.parse_args(argv)
    kw = dict(_configs()[args.config])
    out: dict = {"config": args.config, "agents": args.agents, "seed": 1, "runs": {}}
    for arm in (False, True):
        TR.set_enabled(arm)
        t0 = time.perf_counter()
        res = cli.run(n_agents=args.agents, seed=1, world_dir="data/world/v2", **kw)
        wall = time.perf_counter() - t0
        m = res.run_manifest_fields()
        ev = [d["events"] for d in m["daily"]]
        out["runs"]["on" if arm else "off"] = {
            "final": res.final_hash[:16], "calls": int(res.llm_calls),
            "events_rows": [int(e["rows"]) for e in ev],
            "signboard_rows": [int(dict(e["by_what"]).get(TR.SIGNBOARD_WHAT, 0)) for e in ev],
            "events_bytes": [int(e["bytes"]) for e in ev],
            "manifest_read_events": m["tools"]["signboard"]["read_events"],
            "wall_seconds_nondeterministic": round(wall, 1),
        }
    TR.set_enabled(False)
    on, off = out["runs"]["on"], out["runs"]["off"]
    out["same_final_and_calls"] = (on["final"], on["calls"]) == (off["final"], off["calls"])
    txt = json.dumps(out, ensure_ascii=False, indent=1)
    print(txt)
    if args.out:
        Path(args.out).write_text(txt + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
