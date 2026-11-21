"""11-01 段 2 の 4: 版上げの性能の記録(10-13b §0-7)=5,000 体 × 1 日・mock・seed 1・CLI の既定を 1 本ずつ単独で回す。

使い方(リポの根で・PYTHONPATH に比べたい版の src・1 本ずつ別のプロセスで):
    python docs/bench/analysis/s2-rates-1101/tools/perf_s2rates.py --label off [--rate-rules legacy]

測るもの: 壁時計(``cli.main`` の前後)・1 刻みあたり(壁時計 ÷ 1,440 刻み)・最大の作業集合(Windows の peak working set・
``GetProcessMemoryInfo`` を ctypes で読む=追加のパッケージなし)・呼数・final。出力は 1 行の JSON(標準出力)。
"""

from __future__ import annotations

import argparse
import json
import sys
import time


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
    ap.add_argument("--rate-rules", default=None, choices=("off", "legacy"))
    a = ap.parse_args()
    from shibuya import cli

    box: dict = {}
    real = cli.run

    def _keep(*args, **kw):
        box["res"] = real(*args, **kw)
        return box["res"]

    cli.run = _keep
    argv = ["--llm", "mock"] + (["--rate-rules", a.rate_rules] if a.rate_rules else [])
    t0 = time.perf_counter()
    cli.main(argv)
    wall = time.perf_counter() - t0
    res = box["res"]
    peak = _peak_working_set_bytes()
    out = {"label": a.label, "wall_s": round(wall, 1), "ms_per_step": round(wall / 1_440 * 1_000, 1),
           "peak_mb": round(peak / 1e6, 1), "llm_calls": int(res.llm_calls), "final16": str(res.final_hash)[:16]}
    print("PERF " + json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
