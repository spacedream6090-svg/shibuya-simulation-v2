"""10f の材料(K19): 実行時に ``core.rng.philox`` を包んで、1 本のランで作られた全部の Philox の流れについて
「何ブロック引いたか」と「同じ鍵の別の流れとブロックが重なったか」を数える(src は変えない=このプロセスの中で
関数を差し替えるだけ)。

数え方: numpy の Philox は 1 語目(カウンタの 0 語目)から 1 ずつ進む(10c §2・検収 §3 の実測)。作った時点の
0 語目を c0、ランの終わりの 0 語目を c1 とすると、使ったブロックは c0+1 .. c1(c1 − c0 個・1 ブロック=4 語)。
同じ (用途名, 1〜3 語目) の流れどうしで、このブロックの区間が重なれば「実際の重なり」。2 ブロック以上を引いた
流れは、0 語目が 1 大きい流れが同じランに無くても「重なりうる」と数える。0 語目の繰り上がり(2^64)は扱わない。

``stream()`` は ``philox`` をモジュールの名前で引くので、``shibuya.core.rng.philox`` の差し替えだけで
``from shibuya.core.rng import stream`` の呼び手も含めて全部を捕まえる。``philox`` を直に import した
呼び手(``agents/schedule.py``・``engine/processes/rail.py``)は、その名前も差し替える。

使い方::

    python docs/bench/analysis/wallbounce-1006/scripts/10f/stream_overlap_runtime.py --agents 5000 --seed 1 \
        --out <json> [--arm-json '{"vocab_version":"v3","activity":true}']
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--arm-json", default='{"vocab_version": "v3", "activity": true}')
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    import shibuya.core.rng as R

    orig = R.philox
    made: list[tuple[str, tuple[int, ...], int, object]] = []
    t_wrap = [0.0]

    def wrapped(master_seed, domain, *counters):  # noqa: ANN001
        t = time.perf_counter()
        bg = orig(master_seed, domain, *counters)
        c0 = int(bg.state["state"]["counter"][0])
        made.append((str(domain), tuple(int(c) for c in counters), c0, bg))
        t_wrap[0] += time.perf_counter() - t
        return bg

    R.philox = wrapped
    import shibuya.agents.schedule as SCH
    import shibuya.engine.processes.rail as RAIL

    for mod in (SCH, RAIL):
        if getattr(mod, "philox", None) is orig:
            mod.philox = wrapped

    from shibuya import cli

    kw = json.loads(a.arm_json)
    kw.update(n_agents=a.agents, seed=a.seed, world_dir=a.world)
    t0 = time.perf_counter()
    res = cli.run(**kw)
    wall = time.perf_counter() - t0

    t1 = time.perf_counter()
    by_dom: dict[str, dict] = defaultdict(lambda: {"streams": 0, "max_blocks": 0, "ge2": 0, "blocks_hist": defaultdict(int)})
    groups: dict[tuple, list[tuple[int, int, int]]] = defaultdict(list)
    same_key: dict[str, int] = defaultdict(int)
    seen_keys: dict[tuple, int] = {}
    for i, (dom, ctr, c0, bg) in enumerate(made):
        c1 = int(bg.state["state"]["counter"][0])
        blocks = c1 - c0
        d = by_dom[dom]
        d["streams"] += 1
        d["max_blocks"] = max(d["max_blocks"], blocks)
        d["ge2"] += int(blocks >= 2)
        d["blocks_hist"][min(blocks, 10)] += 1
        words = ctr + (0,) * (4 - len(ctr))
        key = (dom,) + tuple(words[1:])
        full = (dom,) + tuple(words)
        if full in seen_keys:
            same_key[dom] += 1  # 同じ鍵の作り直し(同じ乱数をもう一度使う)は重なりの数えから外す
            continue
        seen_keys[full] = i
        if blocks > 0:
            groups[key].append((c0 + 1, c1, i))
    overlaps: dict[str, int] = defaultdict(int)
    overlap_examples: dict[str, list] = defaultdict(list)
    for key, iv in groups.items():
        if len(iv) < 2:
            continue
        iv.sort()
        hi_end, hi_i = iv[0][1], iv[0][2]
        for s, e, i in iv[1:]:
            if s <= hi_end and made[i][1] != made[hi_i][1]:
                overlaps[key[0]] += 1
                if len(overlap_examples[key[0]]) < 3:
                    overlap_examples[key[0]].append({"a_counters": list(made[hi_i][1]), "b_counters": list(made[i][1])})
            if e > hi_end:
                hi_end, hi_i = e, i
    post = time.perf_counter() - t1
    doms = {}
    for dom, d in sorted(by_dom.items()):
        doms[dom] = {
            "streams": d["streams"], "max_blocks": d["max_blocks"], "streams_ge2_blocks": d["ge2"],
            "blocks_hist(10=10+)": {str(k): v for k, v in sorted(d["blocks_hist"].items())},
            "actual_block_overlaps": overlaps.get(dom, 0),
            "overlap_examples": overlap_examples.get(dom, []),
            "same_full_key_recreated": same_key.get(dom, 0),
        }
    out = {
        "schema": "10f/stream_overlap_runtime/1",
        "run": {"agents": a.agents, "seed": a.seed, "arm": kw, "final16": res.final_hash[:16],
                "llm_calls": int(res.llm_calls)},
        "n_streams": len(made),
        "wall_s_run_with_wrapper": round(wall, 2),
        "wrapper_s_inside_run": round(t_wrap[0], 2),
        "post_check_s": round(post, 2),
        "domains": doms,
        "note": ("blocks=作った時と終わりの 0 語目の差(1 ブロック=4 語)。actual_block_overlaps=同じ (用途名, 1〜3 語目) の"
                 "別の流れとブロックの区間が重なった回数。same_full_key_recreated=カウンタの全語が同じ流れを作り直した回数"
                 "(同じ乱数を 2 度使う)。"),
    }
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"n_streams": len(made), "wall_s": out["wall_s_run_with_wrapper"], "wrapper_s": out["wrapper_s_inside_run"],
                      "post_s": out["post_check_s"], "final16": out["run"]["final16"]}, ensure_ascii=False))
    for dom, d in doms.items():
        print(dom, d["streams"], d["max_blocks"], d["streams_ge2_blocks"], d["actual_block_overlaps"], d["same_full_key_recreated"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
