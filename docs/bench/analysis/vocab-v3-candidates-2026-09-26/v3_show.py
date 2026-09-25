# -*- coding: utf-8 -*-
import sys, io, json, collections
d = json.load(io.open(sys.argv[1], encoding="utf-8"))
sec = sys.argv[2]; top = int(sys.argv[3]) if len(sys.argv) > 3 else 60
if sec == "target_free_by_target":
    agg = collections.defaultdict(lambda: {"calls": 0, "agents": 0, "arms": 0, "acts": collections.Counter(), "samples": []})
    for r in d["target_free"]:
        act, tg = r["key"].split(" | ", 1)
        a = agg[tg]; a["calls"] += r["calls"]; a["agents"] = max(a["agents"], r["agents"]); a["arms"] = max(a["arms"], r["arms"]); a["acts"][act] += r["calls"]
        if len(a["samples"]) < 2: a["samples"] += r["samples"][:1]
    rows = sorted(agg.items(), key=lambda kv: (-kv[1]["agents"], -kv[1]["calls"]))
    print("n_distinct_targets", len(rows))
    for tg, a in rows[:top]:
        print(f"{a['agents']:6d} {a['calls']:7d} {a['arms']:2d} | {tg[:40]} | {dict(a['acts'].most_common(3))}")
elif sec == "target_named_by_where":
    agg = collections.Counter(); agg_a = collections.Counter()
    for r in d["target_named"]:
        act, nm, where = r["key"].split(" | ")
        agg[(act, where)] += r["calls"]
    for k, v in sorted(agg.items(), key=lambda kv: -kv[1])[:40]:
        print(k, v)
    print("== top names")
    byname = collections.defaultdict(lambda: collections.Counter())
    for r in d["target_named"]:
        act, nm, where = r["key"].split(" | ")
        byname[nm][where] += r["calls"]
    for nm, c in sorted(byname.items(), key=lambda kv: -sum(kv[1].values()))[:top]:
        print(nm, dict(c))
elif sec == "target_kinds":
    for r in d["target_kinds"][:top]:
        print(r)
elif sec == "per_arm":
    for k, v in d["per_arm"].items():
        print(k, v)
else:
    rows = d[sec]
    print("n_rows", len(rows))
    for r in rows[:top]:
        s = " || ".join(x.replace("\n", "⏎")[:70] for x in r.get("samples", [])[:2])
        print(f"{r['agents']:6d} {r['calls']:7d} {r['arms']:2d} | {str(r['key'])[:44]} | {s}")
