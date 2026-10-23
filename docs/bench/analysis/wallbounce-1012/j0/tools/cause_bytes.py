"""第 1 期 1-8 J0(1-3 の検収 M2): 出来事の記録の「原因の表」が LLM の呼び出し 1 つあたりに持つバイトの実測。

1-3 の原因の表は呼び出しごとに Python の物(``LlmCall``・call_id の文字列・入力の id の組・dict の行)を 1 つ持った。
J0 で表を列(SoA)に直した。同じ道具を HEAD の src と作業木の src で回し、1 呼び出しあたりの保持バイトを比べる。

測り方: ``EventLog(capacity=N)`` を先に作り(出来事の行の列は伸びない)、``tracemalloc`` の現在量を基準にして、
呼び出しごとに違う ``LlmCall``(call_id は ``"{T}:{体}:{級}"``=テープの形・入力の出来事 id を k 個)の行を N 行書き、
GC の後の増分を N で割る。書いた ``Event`` は捨てる(表に残る物だけが数に入る)。k=0・2・8 の 3 通り。
39 万体 7 日(保持窓)の見積りは mock の 13.1 呼/体/日(1-3 の検収 M2 の前提)で掛ける。

使い方(リポの根で)::

    PYTHONPATH=<src> python docs/bench/analysis/wallbounce-1012/j0/tools/cause_bytes.py <label> <out.json>

絶対パスは JSON に書かない。
"""

from __future__ import annotations

import gc
import json
import sys
import tracemalloc
from pathlib import Path

from shibuya.core.time_consts import NS_PER_STEP
from shibuya.engine.events import log as EV

N = 20_000
CALLS_PER_AGENT_DAY = 13.1
AGENTS = 390_000
DAYS = 7


def per_cause(k: int) -> dict:
    gc.collect()
    tracemalloc.start()
    log = EV.EventLog(capacity=N + 16)
    log.begin_step(0)
    gc.collect()
    base = tracemalloc.get_traced_memory()[0]
    t = 5 * NS_PER_STEP
    log.begin_step(t)
    for i in range(N):
        ids = tuple((j * NS_PER_STEP, i % 7) for j in range(k))
        cause = EV.LlmCall(f"{1000 + i // 50}:{i}:3", ids)
        log.append(EV.Event(t_ns=t, who=i, what="行為:移動", where=("cell", i % 97), cause=cause))
    gc.collect()
    held = tracemalloc.get_traced_memory()[0] - base
    tracemalloc.stop()
    back = log.event(N - 1).cause
    assert back == EV.LlmCall(f"{1000 + (N - 1) // 50}:{N - 1}:3",
                              tuple((j * NS_PER_STEP, (N - 1) % 7) for j in range(k)))
    b = held / N
    return {"inputs": k, "bytes_per_call": round(b, 1), "n_causes": log.n_causes,
            "gb_390k_7days": round(b * CALLS_PER_AGENT_DAY * AGENTS * DAYS / 1e9, 2)}


def main(argv: list[str]) -> int:
    label, out = argv[1], Path(argv[2])
    rows = [per_cause(k) for k in (0, 2, 8)]
    doc = {"schema": "shibuya.bench/j0/cause-bytes/1", "label": label, "n": N,
           "calls_per_agent_day": CALLS_PER_AGENT_DAY, "agents": AGENTS, "days": DAYS,
           "row_bytes_event": EV.ROW_BYTES, "rows": rows,
           "note": "保持バイト=原因の表(と名の表)の増分。出来事の行の列(ROW_BYTES × 行)は先に確保したので入らない"}
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(rows, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
