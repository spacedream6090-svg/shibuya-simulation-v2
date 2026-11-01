"""10b T7: 2 つのハッシュの費用の内訳(既定 v3 の構成・実資産・mock・seed 1・1 シミュ日)。

使い方(リポのルートで): ``python hash_cost.py <体数> <出力 JSON>``

最後の checkpoint の入力(agents・world・知覚 SoA・owners)を控え、ランの後に同じ入力で
今の final の SoA 部分・behavior-hash・full-hash(SoA 部分と外の状態の部分)・外の状態の行ごとの時間を
それぞれ 5 回測って中央値を出す(壁時計=決定論でない)。絶対パスは書かない。
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

import blake3

import shibuya.engine.run as RUN
from shibuya import cli
from shibuya.engine import state_hashes as SH
from shibuya.engine import state_ledger as SL


def _t(fn, k: int = 5) -> float:
    xs = []
    for _ in range(k):
        t0 = time.perf_counter()
        fn()
        xs.append(time.perf_counter() - t0)
    return statistics.median(xs)


def main(argv: list[str]) -> int:
    n = int(argv[1])
    seen = []
    real = RUN.full_state_hash

    def spy(*a, **k):
        seen.append(a)
        return real(*a, **k)

    RUN.full_state_hash = spy
    res = cli.run(n_agents=n, seed=1, world_dir="data/world/v2", vocab_version="v3", activity=True)
    agents, world, pstate, pop, sched, owners = seen[-1]
    rows = {}
    for key, path in tuple(dict.fromkeys(SL.full_items() + SL.behavior_items())):
        v = SH.resolve_item(owners, path)
        if v is SH._ABSENT:
            continue

        def one(v=v):
            f = SH._Feed(blake3.blake3())
            SH._feed(f, v)
        rows.setdefault(key, 0.0)
        rows[key] += _t(one)
    out = {
        "n_agents": n,
        "final_hash": res.final_hash[:16],
        "phase_checkpoint_s_4_checkpoints": round(res.phase_seconds["checkpoint"], 4),
        "per_checkpoint_s": {
            "final_soa(agents+world)": round(_t(lambda: (agents.state_hash(), world.state_hash())), 5),
            "behavior_hash_alone": round(_t(lambda: SH.behavior_hash(agents, world, pop, sched, "", owners)), 5),
            "full_hash_alone": round(_t(lambda: SH.full_hash(agents, world, pstate, pop, sched, owners)), 5),
            "both_with_memo(run_day の形)": round(_t(lambda: (lambda m: (
                SH.full_hash(agents, world, pstate, pop, sched, owners, memo=m),
                SH.behavior_hash(agents, world, pop, sched, "", owners, memo=m)))({})), 5),
            "full_external_only": round(_t(lambda: SH.external_digest(owners)), 5),
        },
        "external_bytes": int(sum(res.full_hash_bytes.values())),
        "external_rows_s_top": {k: round(v, 5) for k, v in sorted(rows.items(), key=lambda kv: -kv[1])[:12]},
        "external_rows_bytes_top": dict(sorted(res.full_hash_bytes.items(), key=lambda kv: -kv[1])[:12]),
    }
    Path(argv[2]).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
