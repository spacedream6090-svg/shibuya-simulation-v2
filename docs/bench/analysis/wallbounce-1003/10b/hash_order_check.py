"""10b の準備: 「behavior-hash を既定にしてから死蔵の列を消せば final が動かない」ことを、ハッシュの関数の上で確かめる。

使い方(リポのルートで):

    python hash_order_check.py <src の根> <出力 JSON>

やること(src は編集しない・答えの分かっている場面):
1. 全腕の AgentState(2,000 体)を作り、全列を決まった乱数で埋める。
2. 同じ宣言から「消す列」を除いた Registry を作り、同じ中身を写す(列を消した後の世界の代わり)。
3. (a) 元の ``state_hash(exclude=消す列)`` と、消した後の ``state_hash()`` が一致するか
   (b) 元の ``state_hash()``(今の final の定義)は消した後と食い違うか
   (c) 除外した列を書き換えても behavior-hash は動かないか(陰性対照)
   (d) 除外していない列を 1 要素だけ書き換えると behavior-hash が動くか(陽性対照)
   を、消す列の組 3 通り(Q9 の死蔵 3 列 / 軸 1 で「挙動に効かない」agents の 9 列 / 1 列も消さない)で見る。

絶対パスは JSON に書かない。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

DEAD3 = ("plan_cursor", "invocation_distance", "wake_pending_class")
NON_BEHAVIOR_AGENTS = ("band", "plan_cursor", "invocation_distance", "wake_pending_class", "fail_streak",
                       "plan_activity", "fam_last", "rel_last", "energy_balance")


def fill(reg, seed: int) -> None:
    g = np.random.Generator(np.random.Philox(seed))
    for d in reg.decls:
        a = reg._arrays[d.name]
        a.setflags(write=True)
        raw = g.integers(0, 256, size=a.nbytes, dtype=np.uint8)
        a.view(np.uint8).reshape(-1)[:] = raw


def clone_without(reg, drop: tuple[str, ...]):
    from shibuya.core.soa import Registry

    out = Registry(reg.n_entities, kind=reg.kind, per_entity_byte_cap=None)
    for d in reg.decls:
        if d.name in drop:
            continue
        arr = out.declare(d.name, d.dtype, d.shape_per_entity, byte_budget_per_agent=d.byte_budget_per_entity,
                          mechanism=d.mechanism, doc=d.doc or "x")
        arr.setflags(write=True)
        np.copyto(arr, reg._arrays[d.name])
    return out


def main(argv: list[str]) -> int:
    sys.path.insert(0, argv[1])
    from shibuya.agents.state import AgentState

    a = AgentState(2_000, plan_columns=True, edge_columns=True, attention_columns=True, activity_columns=True,
                   familiarity_columns=True, energy_columns=True, memory_columns=True,
                   store_memory_columns=True, relation_columns=True)
    reg = a.registry
    fill(reg, 7)
    full_before = reg.state_hash()
    results = {}
    for label, drop in (("dead3", DEAD3), ("non_behavior_agents9", NON_BEHAVIOR_AGENTS), ("none", ())):
        after = clone_without(reg, drop)
        beh_before = reg.state_hash(exclude=drop)
        r = {
            "dropped": list(drop),
            "a_behavior_before_eq_after_delete": beh_before == after.state_hash(),
            "b_full_before_ne_after_delete": full_before != after.state_hash(),
        }
        if drop:
            x = reg._arrays[drop[0]]
            keep = x.copy()
            x.view(np.uint8).reshape(-1)[:] ^= 0xFF
            r["c_neg_control_excluded_change_keeps_hash"] = reg.state_hash(exclude=drop) == beh_before
            np.copyto(x, keep)
        y = reg._arrays["hunger"]
        old = int(y[0])
        y[0] = (old + 1) % 256
        r["d_pos_control_hunger_change_moves_hash"] = reg.state_hash(exclude=drop) != beh_before
        y[0] = old
        results[label] = r
    out = {"schema": "shibuya.bench/wallbounce-1003/10b-hash-order/1", "agents": 2_000,
           "columns_all_arms": len(reg.decls), "results": results}
    Path(argv[2]).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(results, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
