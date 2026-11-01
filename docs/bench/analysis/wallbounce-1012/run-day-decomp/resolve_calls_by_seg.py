"""区間ごとに、実際に呼ばれた engine/resolve.py の関数(内側の _ で始まる口も)を数える(HEAD 0389689・読むだけ)。
使い方: python resolve_calls_by_seg.py <構成名> <体数> <日数> <出力 json>"""
from __future__ import annotations

import functools
import inspect
import json
import sys
from collections import defaultdict
from pathlib import Path

import shibuya.engine.run as RUN
from shibuya import cli
from shibuya.engine import resolve as R

HERE = Path(__file__).resolve().parent
src = (HERE / "dyn_writers.py").read_text(encoding="utf-8")
CONFIGS = eval(src.split("CONFIGS = ", 1)[1].split("\nBOUNDS", 1)[0])
BOUNDS = eval(src.split("BOUNDS = ", 1)[1].split("\nRUN_END", 1)[0])
LINE2SEG = {ln: s for s, ln in BOUNDS}
cfg, n, days, outp = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), Path(sys.argv[4])
st = {"cur": "S"}
calls: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
for name, fn in list(vars(R).items()):
    if inspect.isfunction(fn) and fn.__module__ == R.__name__:
        def mk(f, nm):
            @functools.wraps(f)
            def w(*a, **k):
                calls[st["cur"]][nm] += 1
                return f(*a, **k)
            return w
        setattr(R, name, mk(fn, name))
code = RUN.run_day.__code__
TOOL = sys.monitoring.PROFILER_ID


def on_line(c, line):
    if c is not code:
        return sys.monitoring.DISABLE
    seg = LINE2SEG.get(line)
    if seg is None:
        return sys.monitoring.DISABLE
    st["cur"] = seg
    return None


sys.monitoring.use_tool_id(TOOL, "rcalls")
sys.monitoring.register_callback(TOOL, sys.monitoring.events.LINE, on_line)
sys.monitoring.set_local_events(TOOL, code, sys.monitoring.events.LINE)
r = cli.run(n_agents=n, seed=1, sim_days=days, ticks=1440, **CONFIGS[cfg])
out = {"config": cfg, "final": r.final_hash[:16], "calls_llm": int(r.llm_calls),
       "by_segment": {s: dict(sorted(v.items())) for s, v in calls.items()}}
outp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(json.dumps({"config": cfg, "final": out["final"], "segments": len(out["by_segment"])}))
