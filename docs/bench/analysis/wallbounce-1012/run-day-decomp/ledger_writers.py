"""状態台帳 189 行 × 書き手(区間→系・resolve の口)の表を作る(HEAD 0389689・読むだけ)。
入力: dyn_agg.json(6 構成の動的な差)・soa_writers_ast.json(静的)・proc_*.json(世界過程ごと)。出力: ledger_writers.md / .json"""
import glob, json, sys
from collections import defaultdict
from pathlib import Path
from shibuya.engine import state_ledger as SL
HERE = Path(sys.argv[1])
# 〔改訂(第330)〕dyn_agg.json の鍵は区間でなく系の名(草案 §2-2)。区間と系の対応は草案 §1-2・§2-2。
agg = json.loads((HERE / "dyn_agg.json").read_text(encoding="utf-8"))
st = json.loads((HERE / "soa_writers_ast.json").read_text(encoding="utf-8"))
dyn = defaultdict(list)
for s, v in agg["segments"].items():
    for k in v["soa"]: dyn[k].append(s)
    for k in v["ext"]: dyn[k].append(s)
proc = defaultdict(set)
for f in glob.glob(str(HERE / "proc_*.json")):
    d = json.loads(Path(f).read_text(encoding="utf-8"))
    for p, v in d["procs"].items():
        for k in v["changed"]:
            proc[k.split(":")[0] if ":" in k else k].add(p)
rows = []
for r in SL.LEDGER:
    key = f"{r.place}.{r.name}" if r.is_soa else r.key
    segs = dyn.get(key, [])
    sysn = sorted(segs)
    sw = []
    if r.is_soa:
        sw = sorted({k.split(":", 1)[1] for k in st["columns"].get(r.name, {}).get("writers", {})
                     if k.startswith("engine/resolve.py")})
    rows.append({"key": r.key, "name": r.name, "place": r.place, "behavior": r.behavior, "restore": r.restore,
                 "dead": r.dead, "systems": sysn, "world_subsystems": sorted(proc.get(key, ())),
                 "resolve_writers": sw})
(HERE / "ledger_writers.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
n_dyn = sum(1 for x in rows if x["systems"])
out = ["# 状態台帳 189 行 × 書き手(HEAD `0389689`・mock/classical の 6 構成・1,000 体・窓の tick・〔改訂(第330)〕系の単位)", "",
       f"- 行 {len(rows)}・動的に書き手が見えた行 {n_dyn}(見えない行=この 6 構成・窓では値が変わらなかった行。書き手が無いとは限らない)。",
       "- 系の名は草案 §2-2(〔改訂(第330)〕測りの境目を系に合わせた)。世界過程は `proc_*.json`(3 構成)。resolve の口は AST の静的な書き(SoA だけ)。",
       "- 作り方: `ledger_writers.py`(同じ置き場)。", "",
       "| 鍵 | 名前 | 置き場 | 軸1 | 軸2 | 系(動的に書いた) | 世界過程 | resolve の口(静的) |", "|---|---|---|---|---|---|---|---|"]
for x in rows:
    out.append(f"| {x['key']} | {x['name'][:40].replace('|', '/')} | {x['place']} | {x['behavior']} | {x['restore']} | "
               f"{', '.join(x['systems'])} | {', '.join(x['world_subsystems'])} | "
               f"{', '.join(x['resolve_writers'][:6])}{' …' if len(x['resolve_writers']) > 6 else ''} |")
(HERE / "ledger_writers.md").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print(len(rows), n_dyn, sum(1 for x in rows if x["place"] == "external" and x["systems"]), sum(1 for x in rows if x["place"] != "external" and x["systems"]))
