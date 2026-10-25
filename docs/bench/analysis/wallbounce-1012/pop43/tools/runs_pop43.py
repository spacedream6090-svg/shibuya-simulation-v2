"""第 4 期 4-3 段 10 差し替え: 動いた量の控え(2 日のラン・性能・母集団の形と計器)。

``one`` は 1 本回して 1 行の JSON を出す(別のプロセスで・``--src`` で HEAD の写しの src を PYTHONPATH に): final・呼数・
壁時計・1 刻み・最大の作業集合(ピークの RSS)・ランの体の種別の内訳・在圏の計器(計画実行層の要約と時別の起きている割合)・
行動の件数・店の選び方の要約・食事・会話・日ごとの経済の保存則の残差・賃金の計器(払った体と出どころ)・権利台帳の行の分布。
``side`` は ``--runs`` の並び(label;world;days;start;config をコンマで)を 1 本ずつ回し(5,000 体のランは同時に回さない)、``--out`` に
書く。``compare`` は 2 つの side を label の対で比べる。絶対パスは書かない。

    python $D/runs_pop43.py side --runs "head_1d;data/world/v2;1;;" --src <HEAD の写し>/src --out head.json
    python $D/runs_pop43.py side --runs "wt_1d;data/world/v2_stage_4-3;1;;" --out wt.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
W2 = REPO / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"


def _peak_working_set_bytes() -> int:
    """Windows のピーク作業セット(RSS 相当)。取れなければ -1(energy_measure.py と同じ読み方)。"""
    try:
        import ctypes
        import ctypes.wintypes as wt

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.GetCurrentProcess.restype = wt.HANDLE
        f = k32.K32GetProcessMemoryInfo
        f.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
        f.restype = wt.BOOL
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        if not f(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
            return -1
        return int(pmc.PeakWorkingSetSize)
    except Exception:  # noqa: BLE001
        return -1


def _configs() -> dict[str, dict[str, Any]]:
    import importlib.util

    spec = importlib.util.spec_from_file_location("wave2_bytecheck", W2)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.configs()


def cmd_one(a: argparse.Namespace) -> int:
    import numpy as np

    from shibuya import cli
    from shibuya.agents.population import load_population

    kw = dict(_configs()[a.config])
    if a.days > 1:
        kw["sim_days"] = int(a.days)
    if a.start:
        kw["start_sim_datetime"] = a.start
    t0 = time.perf_counter()
    res = cli.run(n_agents=a.agents, seed=a.seed, world_dir=a.world, **kw)
    wall = time.perf_counter() - t0
    peak = _peak_working_set_bytes()
    man = res.run_manifest_fields()
    pop = load_population(a.world, n=a.agents, seed=a.seed)
    kinds = {}
    roles = {}
    if pop is not None:
        k, c = np.unique(np.asarray(pop.kind), return_counts=True)
        kinds = {str(int(x)): int(y) for x, y in zip(k, c)}
        if pop.duty_role is not None:
            r, rc = np.unique(np.asarray(pop.duty_role, dtype=object).astype(str), return_counts=True)
            roles = {str(x): int(y) for x, y in zip(r, rc) if x}
    daily = man.get("daily", []) or []
    cons = [{"ok": d.get("economy", {}).get("conservation", {}).get("ok"),
             "residual": d.get("economy", {}).get("conservation", {}).get("residual")} for d in daily]
    st2 = None
    led = getattr(res, "ledger", None)
    try:
        st2 = led.money.stage2.s2_meter if led is not None and led.money is not None and led.money.stage2 else None
    except AttributeError:
        st2 = None
    eco = man.get("economy", {}) or {}
    wage_build = ((eco.get("stage2") or {}).get("rules") or {}).get("wage_build")
    sc = dict(getattr(res, "store_choice", {}) or {})
    steps = int(getattr(res, "ticks", 0) or 0)  # ランの刻みの数(日の数を含む)
    out = {
        "label": a.label, "config": a.config, "days": int(a.days), "start": a.start or "",
        "world_build_hash": json.loads((Path(a.world) / "build_manifest.json").read_text(encoding="utf-8"))["build_hash"][:16],
        "src_is_worktree": Path(sys.modules["shibuya"].__file__).resolve().parents[1] == (REPO / "src").resolve(),
        "final": res.final_hash[:16], "calls": int(res.llm_calls), "wall_s": round(wall, 1),
        "run_wall_s": round(float(getattr(res, "wall_seconds", 0.0) or 0.0), 2),
        "ms_per_step": round(1000.0 * float(getattr(res, "wall_seconds", 0.0) or 0.0) / max(1, steps), 2),
        "peak_rss_bytes": peak, "kinds": kinds, "duty_roles": roles,
        "presence_summary": getattr(res, "presence_summary", ""),
        "presence_counters": {k: v for k, v in dict(getattr(res, "presence_counters", {}) or {}).items()},
        "wake_rate_in_area_by_hour": [round(float(x), 4) for x in (getattr(res, "wake_rate_in_area_by_hour", []) or [])],
        "action_usage": {str(k): int(v) for k, v in dict(getattr(res, "action_usage", {}) or {}).items()},
        "calls_by_condition": {str(k): int(v) for k, v in dict(getattr(res, "calls_by_condition", {}) or {}).items()},
        "meals": int(getattr(res, "meals", 0)), "conversation_counters": dict(getattr(res, "conversation_counters", {}) or {}),
        "store_choice": {k: v for k, v in sc.items() if not isinstance(v, (list, dict)) or len(json.dumps(v)) < 2000},
        "economy_conservation": cons, "wage_build": wage_build,
        "wages_meter": (st2 or {}).get("run", {}).get("wages") if isinstance(st2, dict) else None,
        "rights": man.get("rights"), "salient_events": int(getattr(res, "salient_events", 0)),
        "dispatches": int(getattr(res, "dispatches", 0)), "noticed": int(getattr(res, "noticed", 0)),
    }
    print(json.dumps(out, ensure_ascii=False, default=str))
    return 0


def cmd_side(a: argparse.Namespace) -> int:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if a.src:
        env["PYTHONPATH"] = str(Path(a.src).resolve())
        env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"
    got = []
    for spec in a.runs.split(","):  # 逐次: ランの数(1 本ずつ)
        label, world, days, start, *rest = spec.split(";")
        config = rest[0] if rest and rest[0] else "w6_v3_default"
        cmd = [sys.executable, str(Path(__file__)), "one", "--label", label, "--world", world, "--days", days or "1",
               "--start", start, "--config", config, "--agents", str(a.agents), "--seed", str(a.seed)]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            got.append({"label": label, "error": r.stderr[-3000:]})
        else:
            got.append(json.loads(r.stdout.strip().splitlines()[-1]))
        print(label, got[-1].get("final"), got[-1].get("calls"), got[-1].get("wall_s"), (got[-1].get("error") or "")[-200:],
              flush=True)
    Path(a.out).write_text(json.dumps({"src": "写し" if a.src else "作業木", "agents": a.agents, "seed": a.seed,
                                       "runs": got}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("one")
    sp.add_argument("--label", required=True)
    sp.add_argument("--world", required=True)
    sp.add_argument("--days", type=int, default=1)
    sp.add_argument("--start", default="")
    sp.add_argument("--config", default="w6_v3_default")
    sp.add_argument("--agents", type=int, default=5_000)
    sp.add_argument("--seed", type=int, default=1)
    sp = sub.add_parser("side")
    sp.add_argument("--runs", required=True, help="label;world;days;start;config をコンマで(start と config は空でよい)")
    sp.add_argument("--src", default="")
    sp.add_argument("--agents", type=int, default=5_000)
    sp.add_argument("--seed", type=int, default=1)
    sp.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
