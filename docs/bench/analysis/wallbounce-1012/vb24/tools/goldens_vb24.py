"""第 2 期 2-4: 既定を変えた段で落ちる golden(final と呼数)の値を、試験と同じ引数で集める(段ごとに張り替える材料)。

    python docs/bench/analysis/wallbounce-1012/vb24/tools/goldens_vb24.py all --world data/world/v2_stage_2-4 \
        --out <作業用>/goldens_V1.json [--env SHIBUYA_PROXIMITY=cell ...] [--jobs 6]

構成の名と引数は試験の写し(下の ``CONFIGS``=どの試験のどの定数か)。1 構成 1 子プロセス(腕のモジュールの状態を持ち越さない)。
``env`` の欄は構成ごとに固定で置く腕(試験の中で腕を明示している構成)。``--env`` はすべての構成に足す(旧値の再現の確かめ用)。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parents[6]

_5K = dict(n_agents=5_000, seed=1)
_NULL = dict(plan_executor=False, report_precondition=False)
_V3 = dict(vocab_version="v3")
CONFIGS: dict[str, dict[str, Any]] = {
    # tests/engine/test_presence_executor.py の W17_GOLDEN(行 3113e9ba7abb)
    "pe_null": {"kw": {**_5K, **_NULL}, "test": "test_presence_executor null_arm_final/llm_calls"},
    "pe_v3": {"kw": {**_5K, **_V3}, "test": "test_presence_executor v3_default_final/llm_calls・T7_V3_FINAL・K19_V3_FINAL_COUNTER"},
    "pe_null_l4x1": {"kw": {**_5K, **_NULL, "l4_scale": 1.0, "hunger_model": "v1", "leave_effect": False},
                     "test": "test_presence_executor null_arm_final_l4x1"},
    "pe_v3_l4x1": {"kw": {**_5K, **_V3, "l4_scale": 1.0, "hunger_model": "v1", "leave_effect": False},
                   "test": "test_presence_executor v3_default_final_l4x1"},
    "pe_null_hv1": {"kw": {**_5K, **_NULL, "hunger_model": "v1", "leave_effect": False},
                    "test": "test_presence_executor null_arm_final_hunger_v1"},
    "pe_v3_hv1": {"kw": {**_5K, **_V3, "hunger_model": "v1", "leave_effect": False},
                  "test": "test_presence_executor v3_default_final_hunger_v1"},
    "pe_null_leave": {"kw": {**_5K, **_NULL, "leave_effect": False}, "test": "test_presence_executor null_arm_final_leave_off"},
    "pe_v3_leave": {"kw": {**_5K, **_V3, "leave_effect": False}, "test": "test_presence_executor v3_default_final_leave_off"},
    # tests/engine/test_intent_chooser.py::test_poi_target_legacy_reproduces_the_pre_2a_checkpoints_q13
    "q13_v3": {"kw": {**_5K, **_V3, "poi_target": "legacy", "l4_scale": 1.0, "hunger_model": "v1", "leave_effect": False},
               "test": "test_intent_chooser q13 v3"},
    "q13_null": {"kw": {**_5K, **_NULL, "poi_target": "legacy", "l4_scale": 1.0, "hunger_model": "v1",
                        "leave_effect": False}, "test": "test_intent_chooser q13 null"},
    # tests/engine/proximity/test_runs.py::HEAD_GOLDEN(腕 cell を明示)
    "prox_cell300": {"kw": {"n_agents": 300, "seed": 1, "ticks": 1440, "vocab_version": "v3", "memory": "on",
                            "relations": "on", "rel_copresent": "on"}, "env": {"SHIBUYA_PROXIMITY": "cell"},
                     "test": "proximity/test_runs HEAD_GOLDEN"},
    # tests/perception/test_near_tiebreak.py::CLASSICAL_1500_GOLDEN
    "nt_hash": {"kw": {"n_agents": 1500, "seed": 1, **_V3, "policy": "classical", "chooser": "classical",
                       "classical_social": "near_first"}, "test": "test_near_tiebreak hash"},
    "nt_mid": {"kw": {"n_agents": 1500, "seed": 1, **_V3, "policy": "classical", "chooser": "classical",
                      "classical_social": "near_first", "near_order": "id"}, "test": "test_near_tiebreak hash_order_id"},
    "nt_old": {"kw": {"n_agents": 1500, "seed": 1, **_V3, "policy": "classical", "chooser": "classical",
                      "classical_social": "near_first", "near_tiebreak": "id", "near_order": "id"},
               "test": "test_near_tiebreak classical_tie_id"},
    # tests/engine/test_classical_social.py::CLASSICAL_1500_GOLDEN_ACQ
    "cs_acq": {"kw": {"n_agents": 1500, "seed": 1, **_V3, "policy": "classical", "chooser": "classical"},
               "test": "test_classical_social CLASSICAL_1500_GOLDEN_ACQ"},
    # tests/engine/test_relations_tenure.py::REL_ON_5000_GOLDEN
    "rel_v1": {"kw": {**_5K, **_V3, "memory": "on", "relations": "on", "rel_tenure_hash": "v1"},
               "test": "test_relations_tenure (v1, behavior)"},
    "rel_v2": {"kw": {**_5K, **_V3, "memory": "on", "relations": "on", "rel_tenure_hash": "v2"},
               "test": "test_relations_tenure (v2, behavior)"},
}


def cmd_one(a: argparse.Namespace) -> int:
    from shibuya import cli

    spec = CONFIGS[a.name]
    res = cli.run(world_dir=a.world, **spec["kw"])
    print(json.dumps({"name": a.name, "final": res.final_hash, "final16": res.final_hash[:16],
                      "calls": int(res.llm_calls), "conserved": bool(res.conserved)}, ensure_ascii=False))
    return 0


def cmd_all(a: argparse.Namespace) -> int:
    extra = dict(kv.split("=", 1) for kv in a.env)
    names = [s for s in a.only.split(",") if s] or list(CONFIGS)

    def run(name: str) -> dict[str, Any]:
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env.update(CONFIGS[name].get("env", {}))
        env.update(extra)
        r = subprocess.run([sys.executable, str(HERE), "one", "--name", name, "--world", a.world],
                           capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            return {"name": name, "error": r.stderr[-2000:]}
        return json.loads(r.stdout.strip().splitlines()[-1])

    out: dict[str, Any] = {}
    with cf.ThreadPoolExecutor(max_workers=int(a.jobs)) as ex:
        for row in ex.map(run, names):
            out[row["name"]] = {**row, "test": CONFIGS[row["name"]]["test"]}
            print(row["name"], row.get("final16"), row.get("calls"), (row.get("error") or "")[-200:], flush=True)
    Path(a.out).write_text(json.dumps({"env": extra, "runs": out}, ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("one")
    sp.add_argument("--name", required=True)
    sp.add_argument("--world", default="data/world/v2")
    sp = sub.add_parser("all")
    sp.add_argument("--world", default="data/world/v2")
    sp.add_argument("--out", required=True)
    sp.add_argument("--env", action="append", default=[])
    sp.add_argument("--only", default="")
    sp.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args(argv)
    return {"one": cmd_one, "all": cmd_all}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
