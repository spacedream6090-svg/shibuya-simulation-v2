"""T0: compare the 10f manifest sides (head = main src, t0 = worktree src). Expect: every existing field equal (wall clock
excluded), the only additions are the TM9 fields (top level + daily rows) and the 4 new paths of manifest_sections, env fields
differ (git commit/dirty).

usage: manifest_check_t0.py <scratch> <out.json>
"""
import json
import sys
from pathlib import Path

scratch = Path(sys.argv[1])
RUNS = (("w6_v3_default", 1), ("w6_v3_default", 2), ("w6_golden_null_arm", 1), ("v3_mem_rel", 1), ("v3_mem_rel", 2),
        ("v3_classical_mem_rel", 1), ("v3_classical_mem_rel", 2))
NONDET_PREFIX = ("relations.wall_seconds_nondeterministic", "relations.init.init_seconds_nondeterministic")
ENV = ("env_id", "environment.code.git_commit", "environment.code.git_diff_sha256", "environment.code.git_dirty",
       "environment.env_id")
TM9 = ("calls_by_model", "clock_kind", "step_seconds", "bridges_count")


def flat(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flat(v, f"{prefix}{k}."))
    elif isinstance(d, list) and d and all(isinstance(x, dict) for x in d):
        for i, x in enumerate(d):
            out.update(flat(x, f"{prefix}{i}."))
    else:
        out[prefix[:-1]] = json.dumps(d, ensure_ascii=False, sort_keys=True)
    return out


def strip(k):
    return k[len("manifest."):] if k.startswith("manifest.") else k


def nondet(k):
    k = strip(k)
    last = k.rsplit(".", 1)[-1]
    return (any(k.startswith(p) for p in NONDET_PREFIX) or "seconds" in last and last != "step_seconds"
            or last in ("wall_s", "tick_ms_max") or k.startswith("phase_seconds") or k.startswith("process_seconds")
            or k.startswith("resume.read_seconds") or k.startswith("resume.restore_seconds"))


def expected_addition(k):
    k = strip(k)
    parts = k.split(".")
    if parts[0] in TM9:
        return True
    if parts[0] == "daily" and len(parts) >= 3 and parts[2] in TM9:
        return True
    if k.startswith("manifest_sections.paths.") and k.split("manifest_sections.paths.", 1)[1] in TM9:
        return True
    return False


rows, ok = [], True
for name, seed in RUNS:
    h = json.loads((scratch / f"man_head_{name}_s{seed}.json").read_text(encoding="utf-8"))
    w = json.loads((scratch / f"man_t0_{name}_s{seed}.json").read_text(encoding="utf-8"))
    fh = {k: v for k, v in flat(h).items() if not nondet(k)}
    fw = {k: v for k, v in flat(w).items() if not nondet(k)}
    only_w = sorted(set(fw) - set(fh))
    only_h = sorted(set(fh) - set(fw))
    moved = sorted(k for k in set(fh) & set(fw) if fh[k] != fw[k])
    env_moved = [k for k in moved if strip(k) in ENV]
    moved_other = [k for k in moved if strip(k) not in ENV]
    unexpected_add = [k for k in only_w if not expected_addition(k)]
    top_h, top_w = list(h["manifest"]), list(w["manifest"])
    order_ok = top_w[: len(top_h)] == top_h and top_w[len(top_h):] == list(TM9)
    r = {"config": name, "seed": seed, "final_head": h["final_hash"][:16], "final_t0": w["final_hash"][:16],
         "fields_compared": len(set(fh) & set(fw)), "fields_differ": moved_other, "environment_fields_differ": env_moved,
         "added_fields": len(only_w), "unexpected_added": unexpected_add, "removed_fields": only_h,
         "top_level_order_old_then_tm9": order_ok}
    rows.append(r)
    ok &= (h["final_hash"] == w["final_hash"] and not moved_other and not unexpected_add and not only_h and order_ok)
doc = {"schema": "shibuya.bench/t0/manifest-check/1", "agents": 5000, "world": "data/world/v2",
       "how": "10f の manifest_check_10f.py side の 7 本(HEAD=本体の src・t0=作業木の src・両側 PYTHONHASHSEED=0)の "
              "checkpoints の JSON を平坦化して比べる(壁時計の欄は除く・daily の行は行ごとに平坦化)。足してよいのは TM9 の欄"
              "(一番上・daily の行)と manifest_sections の表の TM9 の 4 行だけ。環境の欄(git の commit と汚れ・env_id)は必ず違う",
       "all_ok": bool(ok), "rows": rows}
Path(sys.argv[2]).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"all_ok": ok, "rows": [(r["config"], r["seed"], r["fields_compared"], len(r["fields_differ"]),
                                          r["added_fields"], len(r["unexpected_added"])) for r in rows]}, ensure_ascii=False))
