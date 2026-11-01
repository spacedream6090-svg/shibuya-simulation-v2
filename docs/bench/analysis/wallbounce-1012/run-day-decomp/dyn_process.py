"""世界過程 18 本の step(と計画実行層)ごとに、実際に値が変わった状態を測る(HEAD 0389689・読むだけ)。
使い方: python dyn_process.py <構成名> <体数> <出力 json>"""
import json, sys, time
from collections import defaultdict
from pathlib import Path
import shibuya.engine.run as RUN
from shibuya import cli
from shibuya.engine.processes import runner as PR
from shibuya.engine import presence as PRES
src = open(sys.argv[0].replace("dyn_process.py", "dyn_writers.py"), encoding="utf-8").read()
CONFIGS = eval(src.split("CONFIGS = ", 1)[1].split("\nBOUNDS", 1)[0])
ns = {}
exec(src.split("def _h(arr)", 1)[0].split("LINE2SEG = ", 1)[0].split("import shibuya.engine.run as RUN", 1)[0], ns)
import blake3, numpy as np
from shibuya.engine import state_hashes as SH
from shibuya.engine import state_ledger as SL
ext_rows = [(r.key, p) for r in SL.external_rows() for p in r.items]
def _h(a):
    a = np.ascontiguousarray(np.asarray(a)); return blake3.blake3(a.view(np.uint8).reshape(-1) if a.size else b"").hexdigest()[:24] + str(a.shape)
code = RUN.run_day.__code__
def rd_frame():
    f = sys._getframe(2)
    while f is not None and f.f_code is not code: f = f.f_back
    return f
def snap(fr):
    loc = fr.f_locals; ag, w = loc["agents"], loc["world"]; pst = loc["_pst_now"](); own = loc["_hash_owners"]()
    o = {}
    for pl, reg in (("agents", ag.registry), ("cells", w.cells), ("pois", w.pois), ("perception", None if pst is None else pst.registry)):
        if reg is None: continue
        for n, a in reg.arrays.items(): o[f"{pl}.{n}"] = _h(a)
    for k, p in ext_rows:
        try: o[f"{k}:{p}"] = SH.item_digest(own, k, p)[0].hex()[:24]
        except Exception as e: o[f"{k}:{p}"] = "ERR"
    return o
WIN = set()
for a, b in ((0, 3), (420, 440), (720, 740), (1080, 1100), (1437, 1440)): WIN |= set(range(a, b))
changes = defaultdict(lambda: defaultdict(int)); visits = defaultdict(int)
def wrap(cls, meth, label):
    orig = getattr(cls, meth)
    def w(self, *a, **k):
        tick = int(a[0]) if a else -1
        if tick not in WIN: return orig(self, *a, **k)
        fr = rd_frame()
        if fr is None or "_hash_owners" not in fr.f_locals: return orig(self, *a, **k)
        s0 = snap(fr); r = orig(self, *a, **k); s1 = snap(fr)
        visits[label] += 1
        for kk, v in s1.items():
            if s0.get(kk) != v: changes[label][kk] += 1
        return r
    setattr(cls, meth, w)
probe = PR.WorldProcessRunner.__init__
seen = set()
def init_wrap(self, *a, **k):
    probe(self, *a, **k)
    for key in PR.PROCESS_ORDER:
        cls = type(self._procs[key])
        if cls not in seen:
            seen.add(cls); wrap(cls, "step", key)
PR.WorldProcessRunner.__init__ = init_wrap
wrap(PRES.PlanExecutor, "step", "presence.step")
wrap(PRES.PlanExecutor, "step_plan_boundaries", "presence.step_plan_boundaries")
c, n, out = sys.argv[1], int(sys.argv[2]), Path(sys.argv[3])
r = cli.run(n_agents=n, seed=1, sim_days=1, ticks=1440, **CONFIGS[c])
res = {"config": c, "n_agents": n, "final": r.final_hash[:16], "calls": int(r.llm_calls),
       "procs": {k: {"visits": visits[k], "changed": dict(sorted(v.items()))} for k, v in changes.items()},
       "no_change": sorted(set(visits) - set(changes))}
out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(json.dumps({"config": c, "final": res["final"], "calls": res["calls"], "procs": len(res["procs"])}))
