"""R-130 (a) いまの核の計測: mock のランを 1 本回し、系ごと・刻みごとの壁時計と刻みごとの診断(事象の数)を集める。

src は書き換えない。進行役 ``engine.systems.conductor`` のモジュールの名 ``run_system`` を、計時を足した包みに差し替える
(包みは元の関数を呼ぶだけ=結果は変わらない。系ごとの合計は進行役の ``RunStats.system_seconds`` と同じ量を測る)。
刻みの幅を変える腕は CLI に無いので、``--tick-seconds`` はこの道具が ``cli.run`` の引数 ``tick_seconds``(``run_day`` の
既存の引数)を足して渡す(参考の計測=系の多くは 60 秒の刻みを前提に書かれている。意味の正しさは保証しない)。

使い方(リポの根で・PYTHONPATH=src):
    python docs/bench/analysis/v3-2026-11/a/tools/measure_core.py --label n5000 --agents 5000 --ticks 1440 \
        --out-dir data/bench/v3-2026-11-a [--tick-seconds 1] [--profile] [--cli-arg=--batch-width-s=1 ...]

出力: ``<out-dir>/<label>.json``(集計)・``<label>.ticks.npz``(刻み × 系の秒・刻み × 診断の列)・``<label>.summary.txt``
(``RunResult.summary()``)・``--profile`` のとき ``<label>.pstats`` と ``<label>.profile.txt``。標準出力に 1 行の要約。
"""

from __future__ import annotations

import argparse
import cProfile
import io
import json
import pstats
import re
import sys
import time
from pathlib import Path


def _peak_working_set_bytes() -> int:
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
        return -1
    return int(pmc.PeakWorkingSetSize)


def _jsonable(v):  # noqa: ANN001, ANN202
    if isinstance(v, (int, float, str, bool)) or v is None:
        return v
    try:
        return float(v)
    except Exception:  # noqa: BLE001
        return str(v)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--agents", type=int, default=5000)
    ap.add_argument("--ticks", type=int, default=1440)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--tick-seconds", type=int, default=None)
    ap.add_argument("--profile", action="store_true")
    ap.add_argument("--out-dir", default="data/bench/v3-2026-11-a")
    ap.add_argument("--cli-arg", action="append", default=[], help="CLI に足す引数(--cli-arg=--batch-width-s=1 の形)")
    a = ap.parse_args()

    import numpy as np

    from shibuya import cli
    from shibuya.engine import run as RUN
    from shibuya.engine.systems import conductor as COND

    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- 系ごと・刻みごとの計時(包みは元を呼ぶだけ) ----
    rec_T: list[int] = []
    rec_name: list[str] = []
    rec_dt: list[float] = []
    real_rs = COND.run_system

    def timed_run_system(spec, ctx, box):  # noqa: ANN001, ANN202
        t0 = time.perf_counter()
        out = real_rs(spec, ctx, box)
        rec_dt.append(time.perf_counter() - t0)
        rec_name.append(spec.name)
        rec_T.append(-1 if ctx is None else int(ctx.T))
        return out

    COND.run_system = timed_run_system

    box_res: dict = {}
    real_run = cli.run

    def keep(*args, **kw):  # noqa: ANN002, ANN003, ANN202
        if a.tick_seconds is not None:
            kw["tick_seconds"] = int(a.tick_seconds)
        box_res["res"] = real_run(*args, **kw)
        return box_res["res"]

    cli.run = keep
    argv = ["--llm", "mock", "--agents", str(a.agents), "--ticks", str(a.ticks), "--seed", str(a.seed)]
    for extra in a.cli_arg:
        argv += extra.split("=", 1) if (extra.startswith("--") and "=" in extra) else [extra]

    prof = cProfile.Profile() if a.profile else None
    buf = io.StringIO()
    real_stdout = sys.stdout
    sys.stdout = buf
    t0 = time.perf_counter()
    try:
        if prof is not None:
            prof.enable()
        cli.main(argv)
    finally:
        if prof is not None:
            prof.disable()
        sys.stdout = real_stdout
    wall = time.perf_counter() - t0
    res = box_res["res"]
    peak = _peak_working_set_bytes()
    (out_dir / f"{a.label}.summary.txt").write_text(buf.getvalue(), encoding="utf-8")

    # ---- 集計 ----
    names = sorted(set(rec_name))
    T_arr = np.asarray(rec_T, dtype=np.int64)
    dt_arr = np.asarray(rec_dt, dtype=np.float64)
    nm_arr = np.asarray(rec_name)
    ticks = int(res.ticks)
    per_tick = np.zeros((ticks, len(names)), dtype=np.float64)
    run_level: dict[str, float] = {}
    for j, n in enumerate(names):
        m = nm_arr == n
        tt = T_arr[m]
        dd = dt_arr[m]
        inside = (tt >= 0) & (tt < ticks)
        if inside.any():
            np.add.at(per_tick[:, j], tt[inside], dd[inside])
        if (~inside).any():
            run_level[n] = float(dd[~inside].sum())
    diag = np.asarray(res.diagnostics)
    cols = list(RUN.DIAG_RUN_COLUMNS)
    tick_seconds = int(a.tick_seconds or 60)
    tph = max(1, 3600 // tick_seconds)
    n_hours = (ticks + tph - 1) // tph
    by_hour_sys = {n: [round(float(per_tick[h * tph:(h + 1) * tph, j].sum()), 5) for h in range(n_hours)]
                   for j, n in enumerate(names)}
    by_hour_diag: dict = {}
    if diag.size:
        for k, c in enumerate(cols):
            if c == "tick":
                continue
            v = diag[:, k]
            by_hour_diag[c] = [int(v[h * tph:(h + 1) * tph].sum()) for h in range(n_hours)]
    out = {
        "label": a.label, "argv": argv, "tick_seconds": tick_seconds, "agents": int(a.agents), "ticks": ticks,
        "seed": a.seed, "profiled": bool(a.profile), "wall_s": round(wall, 3),
        "ms_per_tick": round(wall / max(1, ticks) * 1e3, 3),
        "engine_wall_s": round(float(res.wall_seconds), 3), "peak_mb": round(peak / 1e6, 1),
        "llm_calls": int(res.llm_calls), "final16": str(res.final_hash)[:16],
        "system_total_s": {n: round(float(per_tick[:, j].sum()) + run_level.get(n, 0.0), 4)
                           for j, n in enumerate(names)},
        "system_tick_s": {n: round(float(per_tick[:, j].sum()), 4) for j, n in enumerate(names)},
        "system_run_level_s": {k: round(v, 4) for k, v in run_level.items()},
        "system_calls": {n: int((nm_arr == n).sum()) for n in names},
        "phase_seconds": {k: round(float(v), 4) for k, v in dict(res.phase_seconds).items()},
        "process_seconds": {k: round(float(v), 4) for k, v in dict(getattr(res, "process_seconds", {}) or {}).items()},
        "diag_totals": ({c: int(diag[:, k].sum()) for k, c in enumerate(cols) if c != "tick"} if diag.size else {}),
        "by_hour_system_s": by_hour_sys, "by_hour_diag": by_hour_diag,
        "presence_counters": {k: _jsonable(v) for k, v in dict(getattr(res, "presence_counters", {}) or {}).items()},
        "presence_exit": {k: _jsonable(v) for k, v in dict(getattr(res, "presence_exit", {}) or {}).items()},
        "calls_by_hour": [int(x) for x in list(getattr(res, "calls_by_hour", []) or [])],
    }
    np.savez_compressed(out_dir / f"{a.label}.ticks.npz", systems=np.asarray(names), per_tick=per_tick,
                        diag_cols=np.asarray(cols), diag=diag)
    (out_dir / f"{a.label}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    if prof is not None:
        prof.dump_stats(str(out_dir / f"{a.label}.pstats"))
        s = io.StringIO()
        st = pstats.Stats(prof, stream=s)
        st.sort_stats("tottime").print_stats(80)
        st.sort_stats("cumulative").print_stats(120)
        txt = s.getvalue()
        # 絶対パスを落とす(記録に残さない): リポの根・src/shibuya・Lib から後だけにする
        txt = txt.replace(str(Path.cwd()) + "\\", "")
        txt = re.sub(r"[A-Za-z]:\\\S*?\\(src\\shibuya\\)", r"\1", txt)
        txt = re.sub(r"[A-Za-z]:\\\S*?\\(Lib\\)", r"\1", txt)
        txt = re.sub(r"[A-Za-z]:\\\S*?\\(site-packages\\)", r"\1", txt)
        (out_dir / f"{a.label}.profile.txt").write_text(txt, encoding="utf-8")
    print("R130 " + json.dumps({k: out[k] for k in ("label", "tick_seconds", "agents", "ticks", "wall_s", "ms_per_tick",
                                                   "engine_wall_s", "peak_mb", "llm_calls", "final16")},
                               ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
