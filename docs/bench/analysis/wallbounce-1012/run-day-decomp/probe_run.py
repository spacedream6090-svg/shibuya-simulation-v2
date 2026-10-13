"""1-0: 系ごとの全欄の差と指紋を 1 本のランで取る(``engine.systems.probe``)。HEAD の基準と 1-0 の値を同じ形で出す。

- ``--head``: HEAD(切る前)の ``run_day`` に ``sys.monitoring`` の LINE 事象を張り、系の先頭の行(``BOUNDS_HEAD``・
  HEAD ``ee3abc7`` の ``engine/run.py``)に来るたびに ``probe.snapshot`` を取る(コードは変えない)。``PYTHONPATH`` を
  HEAD の src にして回す。
- 既定(1-0): 作業木の進行役が置く境目(``engine.systems.probe.ACTIVE``)で取る。

どちらも 1 本のランの ``Probe.to_json()``(系ごとの指紋・(T, 系, 変わった欄の digest, 変わった欄))を JSON に書く。
``compare`` で 2 本を並べ、最初に食い違った (T, 系, 欄) と指紋の一致を出す。

使い方(リポの根で)::

    python $D/probe_run.py run --head --config v3_default --agents 1000 --days 2 --out <置き場>/head_v3_default.json
    python $D/probe_run.py run --config v3_default --agents 1000 --days 2 --out <置き場>/c_v3_default.json
    python $D/probe_run.py compare --a head_v3_default.json --b c_v3_default.json

構成は試作の 6 構成(``dyn_writers.py`` と同じ)。壁時計は比べない。絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

CONFIGS = {
    "v3_default": {"vocab_version": "v3", "activity": True},
    "v3_mem_rel_store": {"vocab_version": "v3", "memory": "on", "relations": "on", "store_memory": "on",
                         "rel_copresent": "on"},
    "v3_classical_mem_rel": {"vocab_version": "v3", "memory": "on", "relations": "on",
                             "policy": "classical", "chooser": "classical"},
    "v1_edge": {"vocab_version": "v1", "geometry": "edge"},
    "v2_edge_attention": {"vocab_version": "v2", "geometry": "edge"},
    "golden_null_arm": {"plan_executor": False, "report_precondition": False},
}
#: (系, 先頭の行) HEAD ``ee3abc7`` の ``engine/run.py``(草案 §2-2 の系の境目。llm_receive は 2 つの位置)。
BOUNDS_HEAD = [
    ("day_head", 3607), ("body", 3610), ("world", 3629), ("presence", 3633), ("perceive_prepare", 3649),
    ("llm_receive", 3668), ("apply_responses", 3671), ("detect", 3788), ("plan_boundary", 3816),
    ("home_meal", 3863), ("wake_sources", 3870), ("llm_receive", 3890), ("wake_filter", 3894),
    ("relations_wake", 3929), ("wake_assemble", 3952), ("arbiter", 3981), ("decide", 4002),
    ("phase_a", 4130), ("phase_b", 4159), ("phase_c", 4166), ("conversation", 4229),
    ("activity_intent", 4360), ("memory", 4369), ("familiarity", 4395), ("energy_after", 4400),
    ("observe", 4403), ("checkpoint", 4452), ("day_close", 4497),
    ("drain", 4503), ("close_final", 4551), ("report", 4593), ("END", 4966),
]
RUN_END = {"drain", "close_final", "report", "END"}


HERE = Path(__file__).resolve().parent
_PROBE_FILE = HERE.parents[4] / "src" / "shibuya" / "engine" / "systems" / "probe.py"


_MOD = []


def _probe_mod():
    """1-0 の ``probe`` を作業木のファイルから読む(HEAD の src には無いため。HEAD の側は shibuya を HEAD から読む)。1 回だけ読む。"""
    if _MOD:
        return _MOD[0]
    _MOD.append(_load_probe())
    return _MOD[0]


def _load_probe():
    try:
        from shibuya.engine.systems import probe as P  # 作業木(1-0)
        return P
    except ImportError:
        import importlib.util

        spec = importlib.util.spec_from_file_location("probe_1_0", _PROBE_FILE)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["probe_1_0"] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod


def _head_view(loc):
    P = _probe_mod()

    tally = {nm: loc[nm] for nm in P.STATS_NAMES if nm in loc}
    return P.View(agents=loc["agents"], world=loc["world"], pstate=loc["_pst_now"](), owners=loc["_hash_owners"](),
                  tally=tally, result=loc.get("result"), buffers={"focus_request": loc.get("focus_request")})


def cmd_run(args: argparse.Namespace) -> int:
    from shibuya import cli

    P = _probe_mod()
    pr = P.Probe(families=tuple(args.families.split(",")))  # 段 FIX: --families soa,ext,stats,buffers,scratch
    kw = dict(CONFIGS[args.config])
    t0 = time.perf_counter()
    if args.head:
        import shibuya.engine.run as RUN

        code = RUN.run_day.__code__
        line2 = {ln: s for s, ln in BOUNDS_HEAD}
        tool = sys.monitoring.PROFILER_ID

        def on_line(c, line):
            if c is not code:
                return sys.monitoring.DISABLE
            name = line2.get(line)
            if name is None:
                return sys.monitoring.DISABLE
            fr = sys._getframe(1)
            loc = fr.f_locals
            view = _head_view(loc)
            if name == "END":
                pr.end(view)
            else:
                pr.point(name, None if name in RUN_END else int(loc["tick"]), view)
            return None

        sys.monitoring.use_tool_id(tool, "probe-head")
        sys.monitoring.register_callback(tool, sys.monitoring.events.LINE, on_line)
        sys.monitoring.set_local_events(tool, code, sys.monitoring.events.LINE)
        res = cli.run(n_agents=args.agents, seed=1, sim_days=args.days, ticks=1440, **kw)
        sys.monitoring.set_local_events(tool, code, 0)
        sys.monitoring.free_tool_id(tool)
    else:
        from shibuya.engine.systems.conductor import declared_check
        from shibuya.engine.systems.table import SPECS

        pr.check = declared_check(SPECS)  # 段 B: 変わった欄 ⊆ 宣言の書く欄
        P.ACTIVE = pr
        try:
            res = cli.run(n_agents=args.agents, seed=1, sim_days=args.days, ticks=1440, **kw)
        finally:
            P.ACTIVE = None
    wall = time.perf_counter() - t0
    P.save(pr, args.out, config=args.config, kw=kw, n_agents=args.agents, sim_days=args.days, seed=1,
           side="head" if args.head else "worktree", final=res.final_hash[:16], calls=int(res.llm_calls),
           wall_seconds=round(wall, 1))
    print(json.dumps({"config": args.config, "final": res.final_hash[:16], "calls": int(res.llm_calls),
                      "entries": len(pr.entries), "snapshots": pr.n_snap, "wall_s": round(wall, 1),
                      "violations": len(pr.violations)},
                     ensure_ascii=False))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    P = _probe_mod()

    a = json.loads(Path(args.a).read_text(encoding="utf-8"))
    b = json.loads(Path(args.b).read_text(encoding="utf-8"))
    fd = P.first_diff(a, b)
    systems = sorted(set(a["fp"]) | set(b["fp"]))
    doc = {"a": {k: a.get(k) for k in ("side", "config", "final", "calls")},
           "b": {k: b.get(k) for k in ("side", "config", "final", "calls")},
           "entries": [len(a["entries"]), len(b["entries"])],
           "fp_same": {s: a["fp"].get(s) == b["fp"].get(s) for s in systems},
           "all_same": fd is None and a["fp"] == b["fp"], "first_diff": fd}
    print(json.dumps(doc, ensure_ascii=False, indent=1))
    if args.out:
        Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0 if doc["all_same"] else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--head", action="store_true")
    r.add_argument("--config", required=True)
    r.add_argument("--agents", type=int, default=1000)
    r.add_argument("--days", type=int, default=1)
    r.add_argument("--out", required=True)
    r.add_argument("--families", default="soa,ext,stats,buffers")
    c = sub.add_parser("compare")
    c.add_argument("--a", required=True)
    c.add_argument("--b", required=True)
    c.add_argument("--out", default="")
    args = ap.parse_args(argv)
    return {"run": cmd_run, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
