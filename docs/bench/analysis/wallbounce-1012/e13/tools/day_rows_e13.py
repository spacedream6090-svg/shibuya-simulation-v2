"""第 1 期 1-3(e13): 出来事の記録の 1 日の行数とバイトの実測(mock 5,000 体・世界資産・既定 v3・1 シミュ日)。

語彙 v3(CLI の既定)。記録 on と off を同じ構成で 1 本ずつ回し、on の側の日次の記録(``daily[-1].events``)・ActualLog の行数と目印・記録の
列のバイト・名と原因の表の大きさ・壁時計(on/off・1 本ずつ=ばらつきは測っていない)を JSON に書く。final と呼数が
on/off で同じことも書く。

使い方(リポの根で・作業木の src を ``PYTHONPATH`` に)::

    PYTHONPATH=src python docs/bench/analysis/wallbounce-1012/e13/tools/day_rows_e13.py docs/bench/analysis/wallbounce-1012/e13/day_rows_e13.json

絶対パスは JSON に書かない。
"""
import json
import sys
import time
from pathlib import Path

from shibuya import cli
from shibuya.engine.events import log as EV

N, SEED, WORLD = 5_000, 1, "data/world/v2"


def one(flag: bool):
    prev = EV.enabled()
    EV.set_enabled(flag)
    try:
        t0 = time.perf_counter()
        res = cli.run(n_agents=N, seed=SEED, world_dir=WORLD, vocab_version="v3")
        return res, time.perf_counter() - t0
    finally:
        EV.set_enabled(prev)


on, wall_on = one(True)
off, wall_off = one(False)
log, al = on.event_log, on.runner.log
t, s = al.event_ids()
day = on.run_manifest_fields()["daily"][-1]["events"]
doc = {
    "schema": "shibuya.bench/e13/day-rows/1", "agents": N, "seed": SEED, "world": WORLD, "config": "cli.run・vocab_version=v3(CLI の既定と同じ・ほかは cli.run の既定=byte-check の w6_v3_default と同じ構成)",
    "final_on": on.final_hash[:16], "final_off": off.final_hash[:16], "calls_on": int(on.llm_calls),
    "calls_off": int(off.llm_calls), "same_final_and_calls": (on.final_hash, on.llm_calls) == (off.final_hash, off.llm_calls),
    "daily_events": day,
    "rows_per_agent_day": round(day["rows"] / N, 3),
    "row_bytes": EV.ROW_BYTES,
    "names_table": log.n_names, "causes_table": log.n_causes,
    "actual_log": {"rows": len(al), "appended": int(al.n_appended), "linked": int((s >= 0).sum()),
                   "link_bytes": int(len(al) * (t.itemsize + s.itemsize))},
    "wall_s": {"on": round(wall_on, 1), "off": round(wall_off, 1), "note": "1 本ずつ(ばらつきは測っていない)"},
}
Path(sys.argv[1]).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: doc[k] for k in ("same_final_and_calls", "rows_per_agent_day", "wall_s")}, ensure_ascii=False))
print(json.dumps(day, ensure_ascii=False))
