"""第 1 期 1-8 J0: 腕 legacy と port を同じ構成で 1 本ずつ回し、判断の番号列・final・呼数・壁時計・口の計器を比べる。

判断の番号列=呼ごとの (刻み・体・適用した行動のコード)(今の道は ``LLMBridge.call`` の結果・口の道は
``DecisionLayer.decide_one`` の結果を包んで集める=試験 ``tests/engine/decision/test_j0_mock_equivalence.py`` と同じ形)。
構成は byte-check(``10e/byte_check_10e.py``)と同じ表(``wave2_bytecheck.configs``・mock/classical 5,000 体・seed 1・
1 シミュ日・世界資産)。テープは書かない(テープの列の一致は byte-check で見る)。

使い方(リポの根で・作業木の src を ``PYTHONPATH`` に)::

    PYTHONPATH=src python docs/bench/analysis/wallbounce-1012/j0/tools/arm_pair.py <out.json> w6_v3_default v3_classical_mem_rel

絶対パスは JSON に書かない。壁時計は 1 本ずつ(ばらつきは測っていない)。
"""

from __future__ import annotations

import hashlib
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


def one(name: str, kw: dict, arm: str) -> dict:
    from shibuya import cli
    from shibuya.engine.decision import layer as DL
    from shibuya.engine.llm_bridge import LLMBridge

    seq: list = []
    real_call, real_one = LLMBridge.call, DL.DecisionLayer.decide_one

    def call(self, agent_id, tick, wake_class, condition=0, **k):  # noqa: ANN001
        res = real_call(self, agent_id, tick, wake_class, condition, **k)
        seq.append((int(tick), int(agent_id), int(res.action_code)))
        return res

    def dec(self, bridge, agent_id, step, wake_class, condition, **k):  # noqa: ANN001
        res, p = real_one(self, bridge, agent_id, step, wake_class, condition, **k)
        seq.append((int(step), int(agent_id), int(res.action_code)))
        return res, p

    LLMBridge.call, DL.DecisionLayer.decide_one = call, dec  # type: ignore[method-assign]
    prev = DL.arm()
    DL.set_arm(arm)
    try:
        t0 = time.perf_counter()
        res = cli.run(n_agents=5_000, seed=1, world_dir="data/world/v2", **kw)
        wall = time.perf_counter() - t0
    finally:
        DL.set_arm(prev)
        LLMBridge.call, DL.DecisionLayer.decide_one = real_call, real_one  # type: ignore[method-assign]
    man = res.run_manifest_fields()
    daily_ev = man["daily"][-1]["events"]
    return {
        "final": res.final_hash[:16], "calls": int(res.llm_calls), "wall_s": round(wall, 1),
        "llm_phase_s": round(float(res.phase_seconds.get("llm", 0.0)), 2),
        "sequence_len": len(seq),
        "sequence_sha": hashlib.sha256(json.dumps(seq).encode()).hexdigest()[:16],
        "decision_port": man["decision_port"],
        "events_by_cause": daily_ev.get("by_cause"), "events_rows_last_day": daily_ev.get("rows"),
    }


def main(argv: list[str]) -> int:
    out = Path(argv[1])
    names = argv[2:]
    cfg = _configs()
    rows = {}
    for name in names:
        a = one(name, dict(cfg[name]), "legacy")
        b = one(name, dict(cfg[name]), "port")
        rows[name] = {"kw": dict(cfg[name]), "legacy": a, "port": b,
                      "same_final": a["final"] == b["final"], "same_calls": a["calls"] == b["calls"],
                      "same_sequence": (a["sequence_sha"], a["sequence_len"]) == (b["sequence_sha"], b["sequence_len"])}
        print(name, rows[name]["same_final"], rows[name]["same_sequence"], a["wall_s"], b["wall_s"], flush=True)
    doc = {"schema": "shibuya.bench/j0/arm-pair/1", "agents": 5_000, "seed": 1, "world": "data/world/v2", "rows": rows}
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
