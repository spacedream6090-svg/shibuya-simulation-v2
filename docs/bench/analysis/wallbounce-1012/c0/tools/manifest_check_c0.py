"""第 1 期 1-7(c0): 10f の manifest の 2 つの側(head=本体の HEAD の src の写し・c0=作業木の src)を比べる。

期待: 既存の欄は全部同じ(壁時計は除く)。足したのは一番上の ``tools``(末尾)とその中の欄・節の表の 1 行
(``manifest_sections.paths.tools``)だけ。値が変わってよいのは ``bridges_count``(一番上と日次の各行=つなぎの台帳に
1-7 の 2 行を足した=282 → 284)と ``bridges_version``(台帳の sha)だけ。環境の欄(git の commit と汚れ・env_id)は
必ず違う。看板を読んだ出来事は腕(既定 off)なので、日次の記録の ``events`` は動かない。

使い方(リポの根で・``$W`` は作業用の置き場・両側 ``PYTHONHASHSEED=0``・10f の道具で 2 つの側を回してから)::

    python docs/bench/analysis/wallbounce-1006/10f/manifest_check_10f.py side --src <HEAD の写し>/src --label head --scratch $W
    python docs/bench/analysis/wallbounce-1006/10f/manifest_check_10f.py side --src src --label c0 --scratch $W
    python docs/bench/analysis/wallbounce-1012/c0/tools/manifest_check_c0.py $W docs/bench/analysis/wallbounce-1012/c0/manifest_check_c0.json

r15 の ``r15/tools/manifest_check_r15.py`` を写して、足してよい欄と動いてよい欄の規則だけを替えた。絶対パスは JSON に書かない。
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
C0_TOP = ["tools"]
BRIDGES = (282, 284)


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
    s = strip(k)
    return s == "tools" or s.startswith("tools.") or s == "manifest_sections.paths.tools"


def expected_move(k):
    parts = strip(k).split(".")
    return (parts in (["bridges_count"], ["bridges_version"])
            or (parts[0] == "daily" and len(parts) == 3 and parts[2] == "bridges_count"))


rows, ok = [], True
for name, seed in RUNS:
    h = json.loads((scratch / f"man_head_{name}_s{seed}.json").read_text(encoding="utf-8"))
    w = json.loads((scratch / f"man_c0_{name}_s{seed}.json").read_text(encoding="utf-8"))
    fh = {k: v for k, v in flat(h).items() if not nondet(k)}
    fw = {k: v for k, v in flat(w).items() if not nondet(k)}
    only_w = sorted(set(fw) - set(fh))
    only_h = sorted(set(fh) - set(fw))
    moved = sorted(k for k in set(fh) & set(fw) if fh[k] != fw[k])
    env_moved = [k for k in moved if strip(k) in ENV]
    exp_moved = {k: {"head": json.loads(fh[k]), "c0": json.loads(fw[k])} for k in moved if expected_move(k)}
    moved_other = [k for k in moved if strip(k) not in ENV and not expected_move(k)]
    unexpected_add = [k for k in only_w if not expected_addition(k)]
    top_h, top_w = list(h["manifest"]), list(w["manifest"])
    top_same = top_w[: len(top_h)] == top_h and top_w[len(top_h):] == C0_TOP
    m = w["manifest"]
    tools = m.get("tools") or {}
    r = {"config": name, "seed": seed, "final_head": h["final_hash"][:16], "final_c0": w["final_hash"][:16],
         "fields_compared": len(set(fh) & set(fw)), "fields_differ": moved_other, "environment_fields_differ": env_moved,
         "expected_moves": exp_moved, "added_fields_count": len(only_w), "unexpected_added": unexpected_add,
         "removed_fields": only_h, "top_level_keys_existing_same_and_c0_at_end": top_same,
         "c0": {"bridges_count": m.get("bridges_count"), "n_tools": tools.get("n_tools"),
                "groups": {k: (tools.get("groups") or {}).get(k) for k in ("rows", "family", "workplace", "members")},
                "contact_flags": (tools.get("contact_flags") or {}).get("edges_with_contact"),
                "contact_flags_by_kind": (tools.get("contact_flags") or {}).get("by_kind"),
                "phone_table_rows": (tools.get("phone_table") or {}).get("rows"),
                "signboard": tools.get("signboard")}}
    rows.append(r)
    counts_ok = all(
        (k.endswith("bridges_version") and v["head"] != v["c0"])
        or (v["head"] == BRIDGES[0] and v["c0"] == BRIDGES[1]) for k, v in exp_moved.items())
    ok &= (h["final_hash"] == w["final_hash"] and not moved_other and not unexpected_add and not only_h and top_same
           and counts_ok)
doc = {"schema": "shibuya.bench/c0/manifest-check/1", "agents": 5000, "world": "data/world/v2",
       "how": "10f の manifest_check_10f.py side の 7 本(HEAD=本体の HEAD の src の写し・c0=作業木の src・両側 "
              "PYTHONHASHSEED=0)の checkpoints の JSON を平坦化して比べる(壁時計の欄は除く・daily の行は行ごとに平坦化)。"
              "足してよいのは一番上の tools(末尾)とその中・節の表の 1 行。動いてよいのは bridges_count(一番上と daily の"
              "各行・282 → 284)と bridges_version だけ。環境の欄は必ず違う",
       "all_ok": bool(ok), "rows": rows}
Path(sys.argv[2]).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"all_ok": ok, "rows": [(r["config"], r["seed"], r["fields_compared"], len(r["fields_differ"]),
                                          r["added_fields_count"], len(r["unexpected_added"]), r["c0"]["groups"]["rows"],
                                          r["c0"]["contact_flags"]) for r in rows]}, ensure_ascii=False))
