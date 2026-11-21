"""A48(天気の語の最頻値の補いを消す版上げ)の前後の性能の記録(10-13b §0-7)。

使い方(比べたい版の木の根で・PYTHONPATH にその木の src・1 本ずつ別のプロセスで):
    python perf_a48.py --label base --mode default --out 出力.json
    python perf_a48.py --label work --mode noproc --out 出力.json

mode:
    default = ``cli.main(["--llm", "mock"])``(CLI の既定・5,000 体・1 日・seed 1・世界過程あり)
    noproc  = ``run_day(n_agents=5000, seed=1, world_dir="data/world/v2", processes=False)``(世界過程の無いラン・ライブラリの既定)

測り方は docs/bench/analysis/s2e-1102/README.md §6 と同じ: 壁時計=ランの前後・刻みあたり=壁時計 ÷ 実行器の ``n_steps``・
最大メモリ=Windows の最大の作業集合(PeakWorkingSetSize・10^6 B を MB)・呼数は LLM の呼数(判断モデルは 0=mock)。
出力の JSON に絶対パスは書かない。時間の方針: 刻みの番号を持たない(刻みの数は実行器から読む)。
"""
from __future__ import annotations

import argparse
import ctypes
import json
import sys
import time
from pathlib import Path


def _peak_working_set_bytes() -> int:
    """このプロセスの最大の作業集合[B](Windows の PROCESS_MEMORY_COUNTERS.PeakWorkingSetSize)。"""
    if sys.platform != "win32":
        import resource

        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024

    class PMC(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                    ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

    pmc = PMC()
    pmc.cb = ctypes.sizeof(PMC)
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(PMC), ctypes.c_ulong]
    if not psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
        raise OSError(ctypes.get_last_error())
    return int(pmc.PeakWorkingSetSize)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--mode", required=True, choices=("default", "noproc"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    if a.mode == "default":
        from shibuya import cli

        box: dict = {}
        real = cli.run

        def _keep(*args, **kw):
            box["res"] = real(*args, **kw)
            return box["res"]

        cli.run = _keep
        t0 = time.perf_counter()
        cli.main(["--llm", "mock"])
        wall = time.perf_counter() - t0
        res = box["res"]
    else:
        from shibuya.engine.run import World, run_day

        world_dir = "data/world/v2"
        world = World.load_or_synthetic(Path(world_dir), n_cells=139, seed=1)
        t0 = time.perf_counter()
        res = run_day(n_agents=5_000, seed=1, world=world, world_dir=world_dir, processes=False)
        wall = time.perf_counter() - t0
    peak = _peak_working_set_bytes()
    steps = int(res.runner.n_steps) if getattr(res, "runner", None) is not None else int(res.ticks)
    m = res.run_manifest_fields()
    wx = m.get("weather") or {}
    out = {
        "label": a.label,
        "mode": a.mode,
        "final_hash16": str(res.final_hash)[:16],
        "llm_calls": int(res.llm_calls),
        "wall_s": round(wall, 1),
        "steps": steps,
        "ms_per_step": round(wall / max(1, steps) * 1_000, 1),
        "peak_mb": round(peak / 1e6, 1),
        "replay_date": m.get("replay_date"),
        "weather_days": len(wx.get("days") or []) if isinstance(wx, dict) else None,
        "weather_declared": bool(isinstance(wx, dict) and wx.get("declared")),
    }
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("RUN " + json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
