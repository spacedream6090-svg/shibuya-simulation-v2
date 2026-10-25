"""RET: 旧値の再現の試験を「今の値」に張り替えるための値(写しの木=RET のコード+ACT の資産)。python ret_goldens.py <name>"""
import json
import sys

from shibuya import cli

W = "data/world/v2"
B = dict(n_agents=5_000, seed=1, world_dir=W)
RUNS = {
    "null_l4x1": dict(B, plan_executor=False, report_precondition=False, l4_scale=1.0, hunger_model="v1", leave_effect=False),
    "v3_l4x1": dict(B, vocab_version="v3", l4_scale=1.0, hunger_model="v1", leave_effect=False),
    "null_hunger_v1": dict(B, plan_executor=False, report_precondition=False, hunger_model="v1", leave_effect=False),
    "v3_hunger_v1": dict(B, vocab_version="v3", hunger_model="v1", leave_effect=False),
    "null_leave_off": dict(B, plan_executor=False, report_precondition=False, leave_effect=False),
    "v3_leave_off": dict(B, vocab_version="v3", leave_effect=False),
    "q13_v3": dict(B, vocab_version="v3", poi_target="legacy", l4_scale=1.0, hunger_model="v1", leave_effect=False),
    "q13_null": dict(B, plan_executor=False, report_precondition=False, poi_target="legacy", l4_scale=1.0,
                     hunger_model="v1", leave_effect=False),
    "rel_v1": dict(B, vocab_version="v3", memory="on", relations="on", rel_tenure_hash="v1"),
}
NT = dict(n_agents=1500, seed=1, world_dir=W, vocab_version="v3", policy="classical", chooser="classical",
          classical_social="near_first")
RUNS.update({"nt_hash": dict(NT), "nt_order_id": dict(NT, near_order="id"),
             "nt_tie_id": dict(NT, near_tiebreak="id", near_order="id")})

name = sys.argv[1]
r = cli.run(**RUNS[name])
print(json.dumps({"name": name, "final": r.final_hash, "calls": int(r.llm_calls)}))
