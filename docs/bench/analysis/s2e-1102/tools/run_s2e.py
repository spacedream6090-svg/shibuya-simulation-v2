"""11-02r §1 #7: 「無い」の過程 5 件を止める版上げの前後の 5,000 体 × 1 日 mock の比べと性能の記録(10-13b §0-7)。

使い方(リポの根で・PYTHONPATH に比べたい版の src・1 本ずつ別のプロセスで):
    python docs/bench/analysis/s2e-1102/tools/run_s2e.py --label stopped --out 出力.json [--absent-processes legacy]
        [--rate-rules legacy]

``cli.main`` を ``--llm mock`` だけで回し(他は CLI の既定・seed 1)、``cli.run`` の結果を受け取って数える。
``--absent-processes`` は本段の版だけが持つ切替口(前の版のコードでは渡さない)。出力は JSON(絶対パスを書かない)。

数えるもの: final(behavior-hash の先頭)・呼数・壁時計・1 刻みあたり(壁時計 ÷ 実際に進めた刻みの数=実行器の ``n_steps``・
刻みの数は世界の時間 ÷ 刻みの幅と突き合わせる=刻みの番号を決め打ちしない)・最大の作業集合(Windows の peak working set)・
5 件の過程の件数(収集・掃除・工事・出動・電気と水)と、正しい不合格の計器(街路に残るごみ・倒れた数と運ばれた数)・
ActualLog の行・manifest の ``absent_processes``(本段の版だけ)。

時間の方針(11-02r §2-2): 本道具は刻みの番号を持たない(世界の時間は結果の刻みの幅 × 刻みの数から求める)。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def _peak_working_set_bytes() -> int:
    """このプロセスの最大の作業集合[B](Windows の PROCESS_MEMORY_COUNTERS.PeakWorkingSetSize)。"""
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
    psapi = ctypes.WinDLL("psapi")
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
    if not psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
        raise OSError("GetProcessMemoryInfo に失敗")
    return int(pmc.PeakWorkingSetSize)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--absent-processes", default=None, choices=("stopped", "legacy"))
    ap.add_argument("--rate-rules", default=None, choices=("off", "legacy"))
    a = ap.parse_args()

    from shibuya import cli
    from shibuya.core.time_consts import SECONDS_PER_DAY

    box: dict = {}
    real = cli.run

    def _keep(*args, **kw):
        box["res"] = real(*args, **kw)
        return box["res"]

    cli.run = _keep
    argv = ["--llm", "mock"]
    if a.absent_processes:
        argv += ["--absent-processes", a.absent_processes]
    if a.rate_rules:
        argv += ["--rate-rules", a.rate_rules]
    t0 = time.perf_counter()
    cli.main(argv)
    wall = time.perf_counter() - t0
    peak = _peak_working_set_bytes()
    res = box["res"]
    runner = res.runner
    steps = int(runner.n_steps)
    world_seconds = float(steps) * float(res.tick_seconds)
    pc = dict(res.process_counters)
    keys = ("waste.stops", "waste.collected_g", "waste.consumed", "waste.consumed_g", "waste.day_waste_g",
            "waste.to_bin_rows", "street_cleaning.swept_cells", "street_cleaning.swept_g",
            "street_cleaning.litter_generated_g", "street_cleaning.litter_now_g", "road_works.started",
            "road_works.finished", "road_works.blocked_cells", "dispatch.dispatched", "dispatch.arrived",
            "salient.collapse", "salient.events", "infra.power_kwh_day", "infra.water_m3_day", "actual_log.rows",
            "actual_log.appended")
    out: dict = {
        "label": a.label,
        "argv": argv,
        "final_hash16": str(res.final_hash)[:16],
        "llm_calls": int(res.llm_calls),
        "wall_s": round(wall, 1),
        "steps": steps,
        "world_days": round(world_seconds / SECONDS_PER_DAY, 6),
        "ms_per_step": round(wall / max(1, steps) * 1_000, 1),
        "peak_mb": round(peak / 1e6, 1),
        "counters": {k: pc.get(k) for k in keys},
    }
    try:
        out["waste_t_per_day"] = round(float(runner.projected_waste_tonnes_per_day()), 6)
    except Exception as e:  # 前の版でも同じ口(報告だけ)
        out["waste_t_per_day"] = f"n/a: {type(e).__name__}"
    m = res.run_manifest_fields()
    out["manifest_absent_processes"] = m.get("absent_processes")
    out["manifest_rate_rules_mode"] = (m.get("rate_rules") or {}).get("mode")
    out["manifest_tail_keys"] = list(m)[-3:]
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("RUN " + json.dumps({k: out[k] for k in ("label", "final_hash16", "llm_calls", "wall_s", "steps",
                                                   "ms_per_step", "peak_mb")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
