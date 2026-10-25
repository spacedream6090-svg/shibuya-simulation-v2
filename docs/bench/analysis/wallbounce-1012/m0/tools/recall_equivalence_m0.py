"""第 1 期 1-6 M0: 腕 on のランで、今の記憶の表の想起と記憶の器の想起を突き合わせた数を記録する道具。

試験 ``tests/engine/memory/test_m0_recall_equivalence.py`` と同じ突き合わせ(抜き取った刻みの全部の想起を、器を外した
今の表の道と器の道で引き、描き方に渡す ``RecallItem`` の列が同じか)を、世界資産 5,000 体・mock・1 日の記憶の構成で回し、
数(突き合わせた呼び出し・候補のあった呼び出し・項・店の行・刻み・食い違い)と final・器の計器を JSON に書く。

使い方(作業木の根で・``PYTHONPATH`` に作業木の ``src``):

    python docs/bench/analysis/wallbounce-1012/m0/tools/recall_equivalence_m0.py --out <JSON> [--every 7]

絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path

CONFIGS = {
    "v3_mem_rel": {"vocab_version": "v3", "memory": "on", "relations": "on"},
    "v3_mem_store": {"vocab_version": "v3", "memory": "on", "store_memory": "on"},
    "v3_classical_mem_rel": None,  # 下で wave2 の構成から取る(古典の方策の引数)
}


def _wave2_cfg(name: str) -> dict:
    import importlib.util
    import sys

    p = Path(__file__).resolve().parents[3] / "wave2-2026-09-30" / "wave2_bytecheck.py"  # analysis/wave2-…
    spec = importlib.util.spec_from_file_location("wave2_bytecheck_m0", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck_m0"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return dict(mod.configs()[name])


def run(cfg: str, kw: dict, every: int, agents: int, world: str) -> dict:
    from shibuya import cli
    from shibuya.engine.memory import MemoryLayer
    from shibuya.engine import memory_store as MS

    orig = MemoryLayer.recall
    pr = {"compared": 0, "nonempty": 0, "items": 0, "store_items": 0, "mismatch": 0, "steps": set()}

    def recall(self, agents_, agent_id, tick, condition, inviter=-1):  # noqa: ANN001, ANN202
        if self.memory_store is None or int(tick) % every:
            return orig(self, agents_, agent_id, tick, condition, inviter)
        ms = self.memory_store
        saved = Counter(self.recall_stats)
        self.memory_store = None
        try:
            ref = orig(self, agents_, agent_id, tick, condition, inviter)
        finally:
            self.memory_store = ms
        self.recall_stats = saved
        got = orig(self, agents_, agent_id, tick, condition, inviter)
        pr["compared"] += 1
        pr["steps"].add(int(tick))
        if got:
            pr["nonempty"] += 1
            pr["items"] += len(got)
            pr["store_items"] += sum(1 for it in got if it.row >= self.n_rows)
        pr["mismatch"] += int(list(ref) != list(got))
        return got

    base = dict(n_agents=agents, seed=1, world_dir=world, **kw)
    MS.set_arm("mem")
    t0 = time.perf_counter()
    off = cli.run(**base)
    t_off = time.perf_counter() - t0
    MemoryLayer.recall = recall
    MS.set_arm("events")
    try:
        t0 = time.perf_counter()
        on = cli.run(**base)
        t_on = time.perf_counter() - t0
    finally:
        MemoryLayer.recall = orig
        MS.set_arm("mem")
    return {
        "config": cfg, "agents": agents, "every": every,
        "steps_sampled": len(pr["steps"]), "calls_compared": pr["compared"], "calls_with_candidates": pr["nonempty"],
        "items_compared": pr["items"], "store_rows_items": pr["store_items"], "mismatches": pr["mismatch"],
        "final_off": off.final_hash[:16], "final_on": on.final_hash[:16], "final_same": off.final_hash == on.final_hash,
        "calls_off": int(off.llm_calls), "calls_on": int(on.llm_calls),
        "recall_counts_same": off.memory_summary["recall"] == on.memory_summary["recall"],
        "memory_store": on.memory_summary.get("memory_store", {}),
        "wall_s_off": round(t_off, 1), "wall_s_on_with_double_recall": round(t_on, 1),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--every", type=int, default=7)
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    names = [s for s in args.only.split(",") if s] or list(CONFIGS)
    rows = []
    for name in names:
        kw = CONFIGS[name] if CONFIGS[name] is not None else _wave2_cfg(name)
        r = run(name, kw, args.every, args.agents, args.world)
        print(json.dumps({k: v for k, v in r.items() if k != "memory_store"}, ensure_ascii=False), flush=True)
        rows.append(r)
    Path(args.out).write_text(json.dumps({"runs": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                              newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
