"""第 1 期 1-3(e13): 10f の manifest の 2 つの側(head=本体の src・e13=作業木の src)を比べる。

期待: 既存の欄は全部同じ(壁時計は除く)・足したのは日次の記録(``daily`` の各行)の ``events`` の下の葉だけ・一番上の
鍵の並びは同じ・``manifest_sections`` の表は同じ・環境の欄(git の commit と汚れ・env_id)だけが違う。

使い方(リポの根で・``$W`` は作業用の置き場・10f の道具で 2 つの側を回してから)::

    python docs/bench/analysis/wallbounce-1006/10f/manifest_check_10f.py side --src <本体>/src --label head --scratch $W
    python docs/bench/analysis/wallbounce-1006/10f/manifest_check_10f.py side --src <作業木>/src --label e13 --scratch $W
    python docs/bench/analysis/wallbounce-1012/e13/tools/manifest_check_e13.py $W docs/bench/analysis/wallbounce-1012/e13/manifest_check_e13.json

T0 の ``t0/tools/manifest_check_t0.py`` を写して、足してよい欄の規則だけを替えた。絶対パスは JSON に書かない。
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
    parts = strip(k).split(".")
    return parts[0] == "daily" and len(parts) >= 3 and parts[2] == "events"


rows, ok = [], True
for name, seed in RUNS:
    h = json.loads((scratch / f"man_head_{name}_s{seed}.json").read_text(encoding="utf-8"))
    w = json.loads((scratch / f"man_e13_{name}_s{seed}.json").read_text(encoding="utf-8"))
    fh = {k: v for k, v in flat(h).items() if not nondet(k)}
    fw = {k: v for k, v in flat(w).items() if not nondet(k)}
    only_w = sorted(set(fw) - set(fh))
    only_h = sorted(set(fh) - set(fw))
    moved = sorted(k for k in set(fh) & set(fw) if fh[k] != fw[k])
    env_moved = [k for k in moved if strip(k) in ENV]
    moved_other = [k for k in moved if strip(k) not in ENV]
    unexpected_add = [k for k in only_w if not expected_addition(k)]
    top_same = list(h["manifest"]) == list(w["manifest"])
    daily = w["manifest"].get("daily", [])
    ev = [d.get("events", {}) for d in daily]
    r = {"config": name, "seed": seed, "final_head": h["final_hash"][:16], "final_e13": w["final_hash"][:16],
         "fields_compared": len(set(fh) & set(fw)), "fields_differ": moved_other, "environment_fields_differ": env_moved,
         "added_fields": len(only_w), "unexpected_added": unexpected_add, "removed_fields": only_h,
         "top_level_keys_same": top_same,
         "events_daily": [{"on": e.get("on"), "rows": e.get("rows"), "bytes": e.get("bytes")} for e in ev]}
    rows.append(r)
    ok &= (h["final_hash"] == w["final_hash"] and not moved_other and not unexpected_add and not only_h and top_same)
doc = {"schema": "shibuya.bench/e13/manifest-check/1", "agents": 5000, "world": "data/world/v2",
       "how": "10f の manifest_check_10f.py side の 7 本(HEAD=本体の src・e13=作業木の src・両側 PYTHONHASHSEED=0)の "
              "checkpoints の JSON を平坦化して比べる(壁時計の欄は除く・daily の行は行ごとに平坦化)。足してよいのは daily の"
              "各行の events の下の葉だけ。一番上の鍵の並びと manifest_sections は同じ。環境の欄(git の commit と汚れ・"
              "env_id)は必ず違う",
       "all_ok": bool(ok), "rows": rows}
Path(sys.argv[2]).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"all_ok": ok, "rows": [(r["config"], r["seed"], r["fields_compared"], len(r["fields_differ"]),
                                          r["added_fields"], len(r["unexpected_added"])) for r in rows]},
                 ensure_ascii=False))
