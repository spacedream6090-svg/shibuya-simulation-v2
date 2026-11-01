"""第 6 期 6-5 検収 M2: 上限なしの腕(人も記憶の一つ=``--memory-people memory``+``--memory-model m1``)の器の太り方を測る。

5,000 体・seed 1・mock・複数日の通しで、日の締めごとに器の行・器の行の幅・体あたりの出来事と人の行の最大・消えた行(忘れた/
上限で A の一番低い行)・店の行の表(幅・行・上書き)・最大の作業集合(Windows の PeakWorkingSetSize=決定論でない)を控え、
39 万体のバイトの見積り(器の行の幅 × 行のバイト × 体の数=推測)を出す。記録を出すだけ(エンジンは変えない=器の口を包んで
控えるだけ)。

使い方(リポの根で・``PYTHONPATH`` に作業木の ``src``):

    python docs/bench/analysis/wallbounce-1012/mr65/tools/capacity_mr65.py --days 7 --out <置き場>/capacity_7d.json

構成は byte-check の ``v3_mem_rel``(記憶+関係)に店の記憶 on を足した物(店の行の表も測る)。7 日は土日を含む=開始日の
検査の規則の違反(連続する平日に収まらない)を止めずに記録の ``start_check_waived`` に写す(2-3 の ``--allow-rest-days`` と同じ
包み方・付録=test_only・止める違反は止める)。絶対パスは JSON に書かない。
逐次ループ宣言: 日の数ぶん(日の締めの控え)。
"""

from __future__ import annotations

import argparse
import ctypes
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
#: 39 万体(W16 の母集団の全員=390,067)。
N_FULL = 390_067


def _peak_ws() -> int:
    """このプロセスの最大の作業集合(PeakWorkingSetSize・バイト=決定論でない・Windows だけ・取れなければ −1)。"""
    try:
        from ctypes import wintypes as wt

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


def _snap(ms: Any, day: int, t0: float) -> dict[str, Any]:
    from shibuya.engine import memory_m1 as M1
    from shibuya.engine import memory_store as MS

    used = ms._ms_origin >= 0
    kind = ms._lg_kind.astype(np.int64)
    N = int(ms.n_rows)
    person = (used & (kind == M1.PERSON_KIND)).reshape(ms.n, N).sum(axis=1)
    episode = (used & (kind != M1.PERSON_KIND)).reshape(ms.n, N).sum(axis=1)
    st = ms._ms_stats
    row_bytes = MS.ROW_BYTES + MS.LEGACY_BYTES + MS.LOG_SEQ_BYTES + (8 * int(ms.m1.k) if ms.m1 is not None else 0)
    out: dict[str, Any] = {
        "day": int(day), "width": N, "width_max": int(ms.max_width), "rows": int(used.sum()),
        "episode_rows": int(episode.sum()), "person_rows": int(person.sum()),
        "episode_per_agent_max": int(episode.max()), "person_per_agent_max": int(person.max()),
        "episode_per_agent_p99": float(np.percentile(episode, 99)), "person_per_agent_p99": float(np.percentile(person, 99)),
        "rows_resized": int(st.get("rows_resized", 0)), "forgotten": int(st.get("forgotten", 0)),
        "evicted_by_a": int(st.get("evicted_by_a", 0)), "annotations": int(len(ms._ms_note)),
        "store_bytes_rows": int(N * ms.n * row_bytes), "row_bytes": int(row_bytes),
        "peak_ws_bytes_nondeterministic": _peak_ws(), "wall_s_nondeterministic": round(time.perf_counter() - t0, 1),
    }
    if ms.m1 is not None:
        out["m1_counts"] = dict(ms.m1._m1_stats)
    if ms.shops is not None:
        out["shops"] = ms.shops.summary()
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    from shibuya import cli
    from shibuya.core.time_consts import STEPS_PER_DAY
    from shibuya.engine import calendar as CAL
    from shibuya.engine import memory_m1 as M1
    from shibuya.engine import memory_store as MS
    from shibuya.engine.events.log import EventLog
    from shibuya.engine.memory_store import MemoryStore

    MS.set_arm(MS.ARM_EVENTS)
    M1.set_arm("model", "m1")
    M1.set_arm("people", "memory")
    box: dict[str, Any] = {"ms": None, "days": []}
    t0 = time.perf_counter()
    orig_enable = MemoryStore.enable_arms

    def enable(self: MemoryStore, **kw: Any) -> None:
        orig_enable(self, **kw)
        box["ms"] = self

    orig_close = EventLog.close_day

    def close(self: EventLog, day: int) -> dict[str, Any]:
        got = orig_close(self, day)
        if box["ms"] is not None:
            box["days"].append(_snap(box["ms"], day, t0))
            print(json.dumps(box["days"][-1], ensure_ascii=False), flush=True)
        return got

    waived: list[str] = []

    def _check_start(self: Any, sim_days: int = 1) -> list[str]:  # 規則の違反だけを記録に写す(止める違反は止める)
        fatal, rule = self.start_problems(sim_days)
        if fatal:
            raise ValueError("開始日の検査で止めた: " + " / ".join(fatal))
        waived.extend(rule)
        return []

    CAL.SimCalendar.check_start = _check_start  # type: ignore[method-assign]
    MemoryStore.enable_arms = enable  # type: ignore[assignment]
    EventLog.close_day = close  # type: ignore[assignment]
    kw = dict(vocab_version="v3", memory="on", relations="on", store_memory="on")
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, ticks=int(STEPS_PER_DAY),
                  sim_days=int(args.days), **kw)
    ms = box["ms"]
    last = _snap(ms, int(args.days), t0)
    caps = dict(ms.caps)
    rb = last["row_bytes"]
    shop_rb = int(last.get("shops", {}).get("row_bytes", 23))
    budget = {
        "n_full": N_FULL,
        "by_kind_max_width": {
            "episode": {"max_rows": caps["episode"], "row_bytes": rb, "bytes_390k": caps["episode"] * rb * N_FULL},
            "person": {"max_rows": caps["person"], "row_bytes": rb, "bytes_390k": caps["person"] * rb * N_FULL},
            "shop": {"max_rows": caps["shop"], "row_bytes": shop_rb, "bytes_390k": caps["shop"] * shop_rb * N_FULL},
        },
        "store_width_max_bytes_390k": int(ms.max_width) * rb * N_FULL,
        "measured_width_bytes_390k": int(last["width"]) * rb * N_FULL,
        "measured_shop_width_bytes_390k": int(last.get("shops", {}).get("width", 0)) * shop_rb * N_FULL,
        "per_agent_scale_bytes_390k": 8 * N_FULL,
    }
    doc = {"config": "v3_mem_rel+store_memory", "arms": {"model": "m1", "people": "memory"}, "agents": args.agents,
           "seed": args.seed, "days": args.days, "final": str(res.final_hash)[:16], "calls": int(res.llm_calls),
           "start_check_waived": waived, "test_only": True,
           "per_day": box["days"], "end": last, "budget_estimate": budget,
           "note": "39 万体の見積りは器の行の幅 × 行のバイト × 体の数(注釈・埋め込み・Python の dict の重さは含まない=推測)"}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"final": doc["final"], "calls": doc["calls"], "end": last}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
