"""第 6 期 6-6 ② 第 1 部: 店の仕事の腕(--duties arm)と既定 off の 5,000 体のラン(計器・監査・棚の減った時間の新旧・性能・2 日と
再開=通し)を回して JSON に書く(1 本ずつ)。

使い方(リポの根で・作業木の src を ``PYTHONPATH`` に):

    python docs/bench/analysis/wallbounce-1012/duties1/tools/run_du1.py one --arm arm --days 1 --scratch <git の外> --out <JSON>
    python docs/bench/analysis/wallbounce-1012/duties1/tools/run_du1.py one --arm off --days 1 --scratch <…> --out <JSON>
    python docs/bench/analysis/wallbounce-1012/duties1/tools/run_du1.py one --arm arm --days 2 --scratch <…> --out <JSON>
    python docs/bench/analysis/wallbounce-1012/duties1/tools/run_du1.py one --arm arm --days 1 --events off --scratch <…> --out <JSON>
    python docs/bench/analysis/wallbounce-1012/duties1/tools/run_du1.py resume --days 2 --stop 1440 --scratch <…> --out <JSON>

開始日は暦の既定(2026-07-13 月曜)=開始日の検査の印は使わない。棚の減った/空の店 × 分は、世界過程の 1 刻みの後に全部の店を数える
(腕に依らない同じ物差し=新旧)。性能は壁時計・1 刻み・最大の作業メモリ(Windows の PeakWorkingSetSize)。絶対パスは JSON に
書かない。
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

STEP_NS = 60 * 10**9
_SHELF: dict[str, int] = {}


def _peak_rss_mb() -> float | None:
    """最大の作業メモリ[MB](Windows の GetProcessMemoryInfo の PeakWorkingSetSize・ほかの OS は resource の ru_maxrss)。"""
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            class PMC(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

            pmc = PMC()
            pmc.cb = ctypes.sizeof(PMC)
            k32 = ctypes.WinDLL("kernel32")
            k32.GetCurrentProcess.restype = wintypes.HANDLE
            gpmi = ctypes.WinDLL("psapi").GetProcessMemoryInfo
            gpmi.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
            if not gpmi(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
                return None
            return round(pmc.PeakWorkingSetSize / 2**20, 1)
        import resource

        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    except Exception:  # noqa: BLE001
        return None


def _shelf_probe() -> None:
    """世界過程の 1 刻みの後に棚の減った/空の店 × 分を数える(腕に依らない物差し)。"""
    from shibuya.engine.processes import runner as RN

    real = RN.WorldProcessRunner.step

    def step(self, t):  # noqa: ANN001
        real(self, t)
        sh = self.shelf
        if not sh.active:
            return
        stock = np.asarray(sh.ledger.goods.aggregate_stock(), dtype=np.int64)
        lit = np.asarray(self.world.open_mask(t), dtype=bool)
        staffed = np.asarray(self.opening.staff_of_poi) >= 0
        for name, m in (("low", lit & (stock < np.asarray(sh.reorder_point))), ("empty", lit & (stock <= 0))):
            for side, s in (("staffed", staffed), ("unstaffed", ~staffed)):
                k = f"{name}:{side}"
                _SHELF[k] = _SHELF.get(k, 0) + int(np.count_nonzero(m & s))

    RN.WorldProcessRunner.step = step


def _set(arm: str, events: str) -> None:
    from shibuya.engine.duties import arm as AD
    from shibuya.engine.events import log as EV

    AD.set_arm(arm)
    EV.set_enabled(events == "on")


def _summary(r: Any, wall: float, steps: int) -> dict[str, Any]:
    m = r.run_manifest_fields()
    evs = list(r.event_log.events())
    duty = [e for e in evs if str(e.what).startswith("仕事:")]
    rn = r.runner
    out: dict[str, Any] = {
        "final": r.final_hash, "llm_calls": int(r.llm_calls), "wall_s": round(wall, 1),
        "ms_per_step": round(1000.0 * wall / max(1, steps), 2), "peak_rss_mb": _peak_rss_mb(),
        "calls_by_model": m.get("calls_by_model"),
        "events_by_what": dict(sorted(Counter(e.what for e in duty).items())),
        "event_log": {"rows": int(sum(r.event_log.what_counts().values())), "nbytes": int(r.event_log.nbytes),
                      "cause_nbytes": int(r.event_log.cause_nbytes), "duty_rows": len(duty)},
        "process_counters": {"opening": rn.opening.counters(), "shelf": rn.shelf.counters(),
                             "waste": rn.waste.counters()},
        "shelf_store_minutes": dict(sorted(_SHELF.items())),
        "staffed_stores": int(np.count_nonzero(np.asarray(rn.opening.staff_of_poi) >= 0)),
        "stores": int(rn.world.n_poi),
        "checkpoints_behavior": [[int(c.tick), c.behavior_hash] for c in r.checkpoints],
    }
    d = getattr(r, "duties_layer", None)
    if d is not None:
        from shibuya.engine.duties.layer import audit_causes

        out["audit"] = audit_causes(evs, step_ns=STEP_NS, issued=d.issued_keys(), role_ids=d.role_call_ids())
        dm = m["duties"]
        out["duties"] = {k: v for k, v in dm.items() if k != "meter"}
        out["meter"] = dm["meter"]
    return out


def _kw(args: argparse.Namespace) -> dict[str, Any]:
    kw: dict[str, Any] = dict(n_agents=args.agents, seed=args.seed, world_dir=args.world, vocab_version="v3")
    if args.days != 1:
        kw["sim_days"] = args.days
    return kw


def _machine() -> dict[str, Any]:
    return {"os": platform.platform(terse=True), "machine": platform.machine(), "python": platform.python_version()}


def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli

    _set(args.arm, args.events)
    _shelf_probe()
    t0 = time.perf_counter()
    r = cli.run(**_kw(args))
    wall = time.perf_counter() - t0
    doc = {"mode": "one", "arm": args.arm, "agents": args.agents, "seed": args.seed, "days": args.days,
           "events": args.events, "machine": _machine(), **_summary(r, wall, 1440 * args.days)}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                              newline="\n")
    print(doc["final"], doc["wall_s"], doc.get("audit"), doc.get("duties", {}).get("coverage"))
    return 0


def _cp(r: Any, stop: int) -> list[Any]:
    return [(int(c.tick), c.behavior_hash, c.full_hash) for c in r.checkpoints if int(c.tick) >= stop]


def cmd_resume(args: argparse.Namespace) -> int:
    from shibuya import cli

    _set("arm", "on")
    kw = dict(_kw(args), checkpoint_every=60)
    scratch = Path(args.scratch)
    t0 = time.perf_counter()
    straight = cli.run(**kw)
    w_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    a = cli.run(state_out=str(scratch / "state"), stop_at_tick=args.stop, **kw)
    path = scratch / "state" / a.resume["state_files"][-1]["file"]
    b = cli.run(resume_from=str(path), **kw)
    w_r = time.perf_counter() - t0
    ms, mb = straight.run_manifest_fields()["duties"], b.run_manifest_fields()["duties"]
    keys = ("meter", "decisions", "shop", "shelf", "waste", "coverage", "delay_minutes", "labor_over", "role_words",
            "calls")
    same = {k: ms[k] == mb[k] for k in keys}
    doc = {"mode": "resume", "agents": args.agents, "seed": args.seed, "days": args.days, "stop": args.stop,
           "state_file": path.name, "machine": _machine(),
           "straight": {"final": straight.final_hash, "wall_s": round(w_s, 1)},
           "resumed": {"final": b.final_hash, "wall_s": round(w_r, 1)},
           "final_same": straight.final_hash == b.final_hash,
           "checkpoints_after_stop_same": _cp(straight, args.stop) == _cp(b, args.stop),
           "n_checkpoints_after_stop": len(_cp(straight, args.stop)),
           "manifest_same": same}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                              newline="\n")
    print(doc["final_same"], doc["checkpoints_after_stop_same"], same)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("one", "resume"):
        sp = sub.add_parser(name)
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--days", type=int, default=1)
        sp.add_argument("--scratch", required=True)
        sp.add_argument("--out", required=True)
        if name == "one":
            sp.add_argument("--arm", default="arm", choices=("off", "arm"))
            sp.add_argument("--events", default="on", choices=("on", "off"))
        if name == "resume":
            sp.add_argument("--stop", type=int, default=1440)
    args = ap.parse_args(argv)
    return cmd_one(args) if args.cmd == "one" else cmd_resume(args)


if __name__ == "__main__":
    sys.exit(main())
