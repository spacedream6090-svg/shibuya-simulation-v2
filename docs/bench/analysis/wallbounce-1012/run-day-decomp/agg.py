"""dyn_*.json(系ごとの全欄の差)を 6 構成で束ねる。〔改訂(第330)〕区間でなく系の名で束ね、診断の積算(stats)も出す。"""
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(sys.argv[1])
src = (HERE / "dyn_writers.py").read_text(encoding="utf-8")
BOUNDS = eval(src.split("BOUNDS = ", 1)[1].split("\nRUN_END", 1)[0])
order = [s for s, _ in BOUNDS]
files = sorted(f for f in glob.glob(str(HERE / "dyn_*.json")) if "dyn_agg" not in f)
seg = {k: defaultdict(set) for k in ("soa", "ext", "stats")}
seg = defaultdict(lambda: {"soa": defaultdict(set), "ext": defaultdict(set), "stats": defaultdict(set)})
col_w, row_w = defaultdict(set), defaultdict(set)
cfgs = []
for f in files:
    d = json.loads(Path(f).read_text(encoding="utf-8"))
    c = d["config"]
    cfgs.append(c)
    for s, v in d["segments"].items():
        for k in v["soa"]:
            seg[s]["soa"][k].add(c); col_w[k].add(s)
        for k in v["external"]:
            rk = k.split(":")[0]
            seg[s]["ext"][rk].add(c); row_w[rk].add(s)
        for k in v.get("stats", {}):
            seg[s]["stats"][k].add(c)
agg = {"configs": cfgs, "order": order, "segments": {}}
for s in order:
    if s == "END":
        continue
    agg["segments"][s] = {"soa": sorted(seg[s]["soa"]), "ext": sorted(seg[s]["ext"]),
                          "ext_paths": sorted({k for f in files for k in json.loads(Path(f).read_text(encoding="utf-8"))["segments"].get(s, {}).get("external", {})}),
                          "stats": sorted(seg[s]["stats"])}
agg["soa_multi_segment"] = {k: sorted(v, key=order.index) for k, v in col_w.items() if len(v) > 1}
agg["ext_multi_segment"] = {k: sorted(v, key=order.index) for k, v in row_w.items() if len(v) > 1}
agg["n_soa_written"], agg["n_ext_written"] = len(col_w), len(row_w)
(HERE / "dyn_agg.json").write_text(json.dumps(agg, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
for s in order[:-1]:
    v = agg["segments"][s]
    print(s, "soa", len(v["soa"]), "ext", len(v["ext"]), "paths", len(v["ext_paths"]), "stats", [x[6:] for x in v["stats"]])
print("totals", agg["n_soa_written"], agg["n_ext_written"], "multi", len(agg["soa_multi_segment"]), len(agg["ext_multi_segment"]))
