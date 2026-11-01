"""段 5-1b 第 2 段階: 張り替える golden の新しい値を 1 本ずつ回して集める(道具・リポの根で回す)。

    python docs/bench/analysis/spatial-2026-10/sp1b/tools/collect_goldens.py one <名前>   # 1 本(別のプロセス)
    python docs/bench/analysis/spatial-2026-10/sp1b/tools/collect_goldens.py all <出力>   # 全部を 1 本ずつ

逐次ループ宣言: ランの数ぶん(道具・ランの外)。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

W = "data/world/v2"
RUNS = {
    "null": dict(n_agents=5000, seed=1, world_dir=W, plan_executor=False, report_precondition=False),
    "v3": dict(n_agents=5000, seed=1, world_dir=W, vocab_version="v3"),
    "null_l4x1": dict(n_agents=5000, seed=1, world_dir=W, l4_scale=1.0, hunger_model="v1", plan_executor=False,
                      report_precondition=False),
    "v3_l4x1": dict(n_agents=5000, seed=1, world_dir=W, l4_scale=1.0, hunger_model="v1", vocab_version="v3"),
    "null_hunger_v1": dict(n_agents=5000, seed=1, world_dir=W, hunger_model="v1", plan_executor=False,
                           report_precondition=False),
    "v3_hunger_v1": dict(n_agents=5000, seed=1, world_dir=W, hunger_model="v1", vocab_version="v3"),
    "prox300": dict(n_agents=300, seed=1, world_dir=W, ticks=1440, vocab_version="v3", memory="on", relations="on",
                    rel_copresent="on"),
    "near_first1500": dict(n_agents=1500, seed=1, world_dir=W, vocab_version="v3", policy="classical",
                           chooser="classical", classical_social="near_first"),
    "rel5000": dict(n_agents=5000, seed=1, world_dir=W, vocab_version="v3", memory="on", relations="on"),
    "classical1500": dict(n_agents=1500, seed=1, world_dir=W, vocab_version="v3", policy="classical",
                          chooser="classical"),
    "v3_cell": dict(n_agents=5000, seed=1, world_dir=W, vocab_version="v3", _env={"SHIBUYA_NAV1_DENSITY": "cell"}),
    "v3_unscaled": dict(n_agents=5000, seed=1, world_dir=W, vocab_version="v3",
                        _env={"SHIBUYA_NAV1_DENSITY": "unscaled"}),
}


def one(name: str) -> None:
    from shibuya import cli

    kw = dict(RUNS[name])
    kw.pop("_env", None)
    r = cli.run(**kw)
    sp = r.run_manifest_fields()["space"]
    print(json.dumps({"name": name, "final": r.final_hash, "calls": int(r.llm_calls), "effective": sp["effective"],
                      "density_mode": (sp.get("navmesh") or {}).get("density_mode")}, ensure_ascii=False))


def main() -> int:
    if sys.argv[1] == "one":
        one(sys.argv[2])
        return 0
    out = Path(sys.argv[2])
    got = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    for name, kw in RUNS.items():
        if name in got:
            continue
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env.pop("SHIBUYA_SPACE", None)
        env.pop("SHIBUYA_NAV1_DENSITY", None)
        env.update(kw.get("_env", {}))
        r = subprocess.run([sys.executable, __file__, "one", name], capture_output=True, text=True, encoding="utf-8",
                           env=env)
        got[name] = json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else {"error": r.stderr[-2000:]}
        print(name, got[name].get("final", "ERR")[:16], got[name].get("calls"), flush=True)
        out.write_text(json.dumps(got, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
