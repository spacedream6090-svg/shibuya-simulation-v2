"""第 6 期 6-2 カレンダー 1b の計器の表(既定 w17 と腕 1b・5,000 体・1 日・合否なし)を作る道具。

使い方(リポの根で・``SHIBUYA_CALENDAR_W20`` に W20 の週の表=組んだ資産 data/world/v2_stage_3-1 の
w20_calendar_1a.parquet・世界資産は data/world/v2):

    python docs/bench/analysis/wallbounce-1012/ca1b/tools/run_ca1b.py --out docs/bench/analysis/wallbounce-1012/ca1b/ca1b_1d.json

構成は byte-check の w6_v3_default(語彙 v3・活動層)。``--classical`` で古典の方策(v3_classical)の 1b も回す(仮のモデル=古典)。
出力は manifest の ``calendar_1b``(日ごとの記録・合計・検査)と、既定との差の要約(final・呼数・計画実行層の計数・就寝の事象の
数・正時の在圏)。壁時計は参考(同じ機械で別の作業木が並行して動く)。絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

from shibuya import cli
from shibuya.engine import calendar_self as CS1

CLS = {"policy": "classical", "chooser": "classical"}
#: 就寝の境界の事象の内訳(``resolve.begin_planned_sleep`` の 7 つ・``woke`` と ``arrived`` は体の居場所で変わる=事象の数ではない)。
SLEEP_EVENT_KEYS = ("slept", "walking", "riding", "outside", "conversing", "asleep", "unreachable")


def _one(mode: str, kw: dict[str, Any]) -> dict[str, Any]:
    prev = CS1.arm()
    CS1.set_arm(mode)
    try:
        t0 = time.perf_counter()
        res = cli.run(**kw)
        wall = time.perf_counter() - t0
    finally:
        CS1.set_arm(prev)
    man = res.run_manifest_fields()
    sleep = {k: int(v) for k, v in dict(res.planned_sleep_counts).items()}
    return {
        "mode": mode, "final": res.final_hash[:16], "calls": int(res.llm_calls), "wall_s": round(wall, 1),
        "presence": {k: float(v) for k, v in dict(res.presence_counters).items()},
        "sleep_counts": sleep, "sleep_events": int(sum(sleep.get(k, 0) for k in SLEEP_EVENT_KEYS)),
        "calendar_1b": man.get(CS1.MANIFEST_KEY),
        "bridges_count": man.get("bridges_count"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--classical", action="store_true")
    a = ap.parse_args()
    if not os.environ.get("SHIBUYA_CALENDAR_W20"):
        os.environ["SHIBUYA_CALENDAR_W20"] = "data/world/v2_stage_3-1/w20_calendar_1a.parquet"
    kw = dict(n_agents=a.agents, seed=a.seed, world_dir=a.world, vocab_version="v3", activity=True)
    out: dict[str, Any] = {"config": "w6_v3_default", "agents": a.agents, "seed": a.seed, "days": 1,
                           "w20": os.environ["SHIBUYA_CALENDAR_W20"].replace("\\", "/").split("data/", 1)[-1]}
    out["w17"] = _one(CS1.MODE_W17, kw)
    out["1b"] = _one(CS1.MODE_1B, kw)
    if a.classical:
        kc = {**kw, **CLS}
        out["w17_classical"] = _one(CS1.MODE_W17, kc)
        out["1b_classical"] = _one(CS1.MODE_1B, kc)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: {kk: v.get(kk) for kk in ("final", "calls", "wall_s", "sleep_events")}
                      for k, v in out.items() if isinstance(v, dict) and "final" in v}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
