import sys, json, importlib.util
spec = importlib.util.spec_from_file_location("dw", sys.argv[0].replace("noprobe.py", "dyn_writers.py"))
src = open(spec.origin, encoding="utf-8").read()
CONFIGS = eval(src.split("CONFIGS = ", 1)[1].split("\nBOUNDS", 1)[0])
from shibuya import cli
c, n, d = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
r = cli.run(n_agents=n, seed=1, sim_days=d, ticks=1440, **CONFIGS[c])
print(json.dumps({"config": c, "final": r.final_hash[:16], "calls": int(r.llm_calls)}))
