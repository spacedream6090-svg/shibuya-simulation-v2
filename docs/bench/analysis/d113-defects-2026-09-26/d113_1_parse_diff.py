# -*- coding: utf-8 -*-
"""before/after のパース結果を call_id で突き合わせ、欄ごとの変化を数える(D-113 ① の計測)。"""
import os, sys, json, io, collections
import pyarrow.parquet as pq
SP = os.path.dirname(os.path.abspath(__file__))
def load(tag):
    t = pq.read_table(os.path.join(SP, f"d113_parse_{tag}.parquet")).to_pydict()
    return {(a, b): i for i, (a, b) in enumerate(zip(t["tape"], t["call_id"]))}, t
kb, tb = load("before"); ka, ta = load("after")
assert kb.keys() == ka.keys(), "call_id 集合が違う"
out = {}
for tape in sorted(set(tb["tape"])):
    c = collections.Counter(); ex = []
    tgt_from = collections.Counter(); tgt_to = collections.Counter()
    for key, i in kb.items():
        if key[0] != tape: continue
        j = ka[key]; c["n"] += 1
        for col in ("action", "target_raw", "format_ok", "strict_format_ok", "positional_used", "comment", "reason"):
            if tb[col][i] != ta[col][j]: c[f"changed:{col}"] += 1
        if tb["target_raw"][i] != ta["target_raw"][j]:
            tgt_from[tb["target_raw"][i]] += 1; tgt_to[ta["target_raw"][j]] += 1
            if len(ex) < 3: ex.append({"call_id": key[1], "before": tb["target_raw"][i], "after": ta["target_raw"][j], "errors_after": ta["errors"][j]})
        if tb["format_ok"][i] != ta["format_ok"][j]: c["format_ok:" + ("F->T" if ta["format_ok"][j] else "T->F")] += 1
        if tb["strict_format_ok"][i] != ta["strict_format_ok"][j]: c["strict:" + ("F->T" if ta["strict_format_ok"][j] else "T->F")] += 1
        if "unknown_label:" in ta["errors"][j]: c["after:unknown_label_calls"] += 1
    out[tape] = {"counts": dict(c), "target_before_top": tgt_from.most_common(6), "target_after_top": tgt_to.most_common(8), "examples": ex}
json.dump(out, io.open(os.path.join(SP, "d113_parse_diff.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for tape, v in out.items():
    print(tape, v["counts"])
    print("   after top:", v["target_after_top"][:6])
