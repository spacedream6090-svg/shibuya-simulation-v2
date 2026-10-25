"""10f の材料: mock 5,000 体の 1 日ランを回して、壁時計・checkpoints の JSON・状態のファイルを一時ディレクトリに書く。

src は変えない(読むだけ)。出力はすべて ``--scratch`` の下(リポの data/ には書かない)。

使い方(リポのルートで・``$W`` は短い一時ディレクトリ)::

    python docs/bench/analysis/wallbounce-1006/scripts/10f/probe_runs.py one --arm v3_default --seed 1 \
        --scratch $W --state --tape
    python docs/bench/analysis/wallbounce-1006/scripts/10f/probe_runs.py one --arm v3_default --seed 2 --scratch $W

``--state`` を付けると 2 日のランを日の境目(T=1440)で止めて状態のファイルを書く(10d §5 の 4.3 MB と同じ形)。
付けなければ 1 日のラン。どちらも 1,440 tick を回す。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ARMS = {
    "v3_default": {"vocab_version": "v3", "activity": True},
    "v3_mem_rel": None,  # 10b の byte-check の構成から引く
}


def _arm_kwargs(name: str) -> dict:
    if ARMS.get(name) is not None:
        return dict(ARMS[name])
    import importlib.util

    p = Path(__file__).resolve().parents[3] / "wallbounce-1003" / "10b" / "byte_check_10b.py"
    spec = importlib.util.spec_from_file_location("byte_check_10b", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["byte_check_10b"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return dict(mod._wave2().configs()[name])


def cmd_one(a: argparse.Namespace) -> int:
    t_imp = time.perf_counter()
    from shibuya import cli

    imp_s = time.perf_counter() - t_imp
    scratch = Path(a.scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    kw = _arm_kwargs(a.arm)
    kw.update(n_agents=int(a.agents), seed=int(a.seed), world_dir=a.world)
    tag = f"{a.arm}_s{a.seed}"
    if a.tape:
        kw["tape_path"] = str(scratch / f"tape_{tag}")
    if a.state:
        kw.update(sim_days=2, stop_at_tick=1440, state_out=str(scratch / f"state_{tag}"))
    t0 = time.perf_counter()
    res = cli.run(**kw)
    wall = time.perf_counter() - t0
    payload = cli.checkpoints_payload(res, run_id=tag)
    payload["probe"] = {
        "arm": a.arm, "seed": int(a.seed), "n_agents": int(a.agents), "wall_s": round(wall, 2),
        "import_s": round(imp_s, 2), "state": bool(a.state), "tape": bool(a.tape),
        "llm_calls": int(res.llm_calls),
        "calls_total": int(res.column("calls").sum()) if res.diagnostics.size else 0,
        "action_usage": dict(res.action_usage),
        "calls_by_condition": dict(res.calls_by_condition),
        "meals": int(res.meals),
        "purchases": int(res.column("purchases").sum()) if res.diagnostics.size else 0,
    }
    out = scratch / f"ckpt_{tag}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"tag": tag, "wall_s": round(wall, 2), "import_s": round(imp_s, 2),
                      "final": res.final_hash[:16], "calls": payload["probe"]["llm_calls"]}, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    o = sp.add_parser("one")
    o.add_argument("--arm", default="v3_default")
    o.add_argument("--seed", type=int, default=1)
    o.add_argument("--agents", type=int, default=5000)
    o.add_argument("--world", default="data/world/v2")
    o.add_argument("--scratch", required=True)
    o.add_argument("--state", action="store_true")
    o.add_argument("--tape", action="store_true")
    a = ap.parse_args(argv)
    return cmd_one(a)


if __name__ == "__main__":
    raise SystemExit(main())
