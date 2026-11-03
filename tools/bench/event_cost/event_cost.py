# -*- coding: utf-8 -*-
"""事象 1 件あたりの Python の固定費を測る小さな道具(指示書 11-03 §6-1・v3 の核の材料)。

R-133 §1〜§3 の事象駆動の核で「事象の数に比例する費用」の係数(ns/事象)を出す。src/ は読まない・使わない
(合成の列と配列だけで測る)。測るもの(それぞれ別の数字):

  (1) heapq の pop と push。鍵は ``(t_ns, 種類の順位, ハッシュ, 体)`` のタプル。列の大きさを一定に保つ
      hold の形(1 件を取り出し、同じ体の次の事象を 1 件入れる)。時刻は ns の連続値と 1 秒の格子の 2 通り。
  (2) 種類での振り分け。dict の表引きで関数を呼ぶ(5 種・10 種)。比較として直の呼び出し・list の表引き。
  (3) 小さな束の NumPy 演算。同じ時刻に束ねた k 件を 1 回の配列の演算で処理する(k=1・16・256)。
  (4) (1)〜(3) を合わせた事象 1 件の往復。列から k 件を取り出し → 種類で振り分け → 配列の演算 → 次の事象を
      k 件入れる。束の中の種類が 1 つの形と、混ざっていて Python で種類ごとに分ける形。k=1 は Python の
      スカラの処理(NumPy を使わない)も測る。
  (5) R-133 §1-3 (Q3) の形。体ごとの ``next_t_ns`` の配列から argmin で次の 1 件を取る形と、1 秒の窓ごとに
      ``flatnonzero(next_t_ns < 窓の終わり)`` で窓に入る体を引く形(窓 1 つの費用)。

1 日の固定費の見積り: R-130 §4 の 35 万体 1 日の事象数(``event_table.json``)× 係数。比較に R-130 raw・
独立の読み §4 の「事象の無い刻みの床」約 2.0 ms/刻み × 刻みの数。

使い方(既定は 1 万件・3 回で小さく回る):
  python tools/bench/event_cost/event_cost.py --counts 10000,100000 --repeats 3 --out out.json --md out.md
"""
from __future__ import annotations

import argparse
import ctypes
import gc
import heapq
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EVENT_TABLE = ROOT / "docs" / "bench" / "analysis" / "v3-2026-11" / "a" / "raw" / "event_table.json"

AGENTS_350K = 345_858          # R-130 の 35 万体(345,858 体)
POOL = 1 << 16                 # 乱数の表の長さ(輪で使い回す・メモリを件数に比例させない)
MASK = POOL - 1
STRIDE = 1024                  # (1) の pop と push を分けて測る塊の大きさ(計時の費用を均す)
DAY_NS = 86_400 * 10**9
SEC_NS = 10**9
ROUND_KINDS = 8                # (4) の種類の数(5〜10 の間・expedient)
FLOOR_MS_DEFAULT = 2.0         # 独立の読み §4・R-130 raw の「事象の無い刻みの床」
STEPS_PER_DAY = {"1 分の刻み(1,440)": 1_440, "1 秒の刻み(86,400)": 86_400}

# R-130 §4 の行のうち、1 日の合計に入れないもの(内訳・参考)。
BREAKDOWN_PREFIX = "llm_calls_"          # llm_calls_mock_x69 の内訳(予定/反応/会話の番)
BREAKDOWN_KEEP = "llm_calls_mock_x69"
REFERENCE_KEYS = ("intents_mock_x69",)   # 行為の解決に入る件(今の作りの中間の数)
REFERENCE_PREFIX = "walker_"             # 歩く体 × 分(今は刻みごとに位置を進める=事象にしない前提の参考)


# ---------------------------------------------------------------- 機械の情報(機械名は入れない)

def _cpu_brand() -> str:
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                return str(winreg.QueryValueEx(key, "ProcessorNameString")[0]).strip()
        except OSError:
            pass
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def _ram_gb() -> float | None:
    if sys.platform == "win32":
        class _MemStatus(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        st = _MemStatus()
        st.dwLength = ctypes.sizeof(_MemStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
            return round(st.ullTotalPhys / 2**30, 1)
        return None
    try:
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30, 1)
    except (ValueError, OSError, AttributeError):
        return None


def machine_info() -> dict:
    return {
        "cpu": _cpu_brand(),
        "logical_cpus": os.cpu_count(),
        "ram_gb": _ram_gb(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "python_impl": platform.python_implementation(),
        "numpy": np.__version__,
        "gc_enabled": gc.isenabled(),
        "perf_counter_resolution_s": time.get_clock_info("perf_counter").resolution,
    }


# ---------------------------------------------------------------- 乱数の表

class Pools:
    """輪で使い回す乱数の表(Python の int の list)。件数に比例するメモリを持たない。"""

    def __init__(self, seed: int, agents: int, grain_ns: int = 1) -> None:
        rng = np.random.default_rng(seed)
        dt = rng.integers(SEC_NS, 3_600 * SEC_NS, size=POOL, dtype=np.int64)  # 次の事象まで 1 秒〜1 時間
        if grain_ns > 1:
            dt = (dt // grain_ns) * grain_ns
        self.dt = dt.tolist()
        self.rank = rng.integers(0, 10, size=POOL).tolist()
        self.hash = rng.integers(0, 2**63 - 1, size=POOL, dtype=np.int64).tolist()  # blake3 の 63 ビットの代わり
        self.agent = rng.integers(0, agents, size=POOL).tolist()


def build_heap(size: int, agents: int, seed: int, grain_ns: int = 1) -> list:
    rng = np.random.default_rng(seed + 1)
    t = rng.integers(0, DAY_NS, size=size, dtype=np.int64)
    if grain_ns > 1:
        t = (t // grain_ns) * grain_ns
    rank = rng.integers(0, 10, size=size).tolist()
    hsh = rng.integers(0, 2**63 - 1, size=size, dtype=np.int64).tolist()
    ag = (np.arange(size) % max(agents, 1)).tolist()
    heap = list(zip(t.tolist(), rank, hsh, ag))
    heapq.heapify(heap)
    return heap


# ---------------------------------------------------------------- (1) heapq

def measure_heap(n: int, heap_size: int, agents: int, seed: int, grain_ns: int) -> dict:
    pools = Pools(seed, agents, grain_ns)
    dts, ranks, hashes = pools.dt, pools.rank, pools.hash
    heap = build_heap(heap_size, agents, seed, grain_ns)
    popped = [None] * STRIDE
    pc = time.perf_counter_ns
    pop_ns = push_ns = base_pop_ns = base_push_ns = 0
    done = 0
    cyc = 0
    hpop, hpush = heapq.heappop, heapq.heappush
    stride = min(STRIDE, len(heap))  # 列が塊より小さいときは列の大きさで割る
    while done < n:
        b = min(stride, n - done)
        t0 = pc()
        for j in range(b):
            popped[j] = hpop(heap)
        t1 = pc()
        for j in range(b):
            t, _r, _h, a = popped[j]
            c = (cyc + j) & MASK
            hpush(heap, (t + dts[c], ranks[c], hashes[c], a))
        t2 = pc()
        pop_ns += t1 - t0
        push_ns += t2 - t1
        # 同じ形の輪で heap の操作だけを抜いた基準(輪・添字・タプルを作る費用)
        top = heap[0]
        t3 = pc()
        for j in range(b):
            popped[j] = top
        t4 = pc()
        for j in range(b):
            t, _r, _h, a = popped[j]
            c = (cyc + j) & MASK
            _x = (t + dts[c], ranks[c], hashes[c], a)
        t5 = pc()
        base_pop_ns += t4 - t3
        base_push_ns += t5 - t4
        # 基準の輪で popped を top で上書きしたので、取り出した中身は push の輪で既に戻してある
        done += b
        cyc = (cyc + b) & MASK
    return {
        "pop_gross": pop_ns / n, "push_gross": push_ns / n,
        "pop_base": base_pop_ns / n, "push_base": base_push_ns / n,
        "pop_net": (pop_ns - base_pop_ns) / n, "push_net": (push_ns - base_push_ns) / n,
        "pair_gross": (pop_ns + push_ns) / n,
        "pair_net": (pop_ns + push_ns - base_pop_ns - base_push_ns) / n,
        "heap_len_end": len(heap),
    }


# ---------------------------------------------------------------- (2) 振り分け

def _make_handler(k: int):
    def handle(a):
        return a + k
    return handle


def measure_dispatch(n: int, kinds: int, agents: int, seed: int) -> dict:
    pools = Pools(seed, agents)
    kp = [r % kinds for r in pools.rank]
    ap = pools.agent
    table = {k: _make_handler(k) for k in range(kinds)}
    table_list = [table[k] for k in range(kinds)]
    direct = table[0]
    pc = time.perf_counter_ns

    t0 = pc()
    for i in range(n):
        c = i & MASK
        kp[c]
        ap[c]
    t1 = pc()
    for i in range(n):
        c = i & MASK
        kp[c]
        direct(ap[c])
    t2 = pc()
    for i in range(n):
        c = i & MASK
        table[kp[c]](ap[c])
    t3 = pc()
    for i in range(n):
        c = i & MASK
        table_list[kp[c]](ap[c])
    t4 = pc()
    base = (t1 - t0) / n
    return {
        "loop_base": base,
        "direct_gross": (t2 - t1) / n, "dict_gross": (t3 - t2) / n, "list_gross": (t4 - t3) / n,
        "direct_net": (t2 - t1) / n - base, "dict_net": (t3 - t2) / n - base,
        "list_net": (t4 - t3) / n - base,
    }


# ---------------------------------------------------------------- (3) 小さな束の NumPy

class SoA:
    """体の配列(35 万体ぶん)。束の演算の相手。"""

    def __init__(self, agents: int, seed: int) -> None:
        rng = np.random.default_rng(seed + 2)
        self.energy = rng.random(agents)
        self.next_t_ns = rng.integers(0, DAY_NS, size=agents, dtype=np.int64)
        self.cell = rng.integers(0, 520, size=agents, dtype=np.int32)
        self.dwell = rng.integers(SEC_NS, 3_600 * SEC_NS, size=agents, dtype=np.int64)


def batch_kernel(s: SoA, idx: np.ndarray, t_now: int) -> np.ndarray:
    """束の 1 回の処理(expedient=未リサーチの代表の形): 読み → 算術 → 書き → 次の時刻。NumPy の呼び 6 回。"""
    e = s.energy[idx]
    np.subtract(e, 0.01, out=e)
    s.energy[idx] = e
    nt = s.dwell[idx]
    nt += t_now
    s.next_t_ns[idx] = nt
    return nt


def measure_batch(n: int, k: int, agents: int, seed: int) -> dict:
    s = SoA(agents, seed)
    rng = np.random.default_rng(seed + 3)
    npool = 64
    idx_pool = [rng.choice(agents, size=min(k, agents), replace=False).astype(np.intp) for _ in range(npool)]
    batches = -(-n // k)
    pc = time.perf_counter_ns
    t_now = 0
    t0 = pc()
    for b in range(batches):
        batch_kernel(s, idx_pool[b & (npool - 1)], t_now)
        t_now += SEC_NS
    t1 = pc()
    events = batches * k
    return {"per_event": (t1 - t0) / events, "per_batch": (t1 - t0) / batches,
            "batches": batches, "events": events}


# ---------------------------------------------------------------- (4) 往復

def measure_round(n: int, k: int, heap_size: int, agents: int, seed: int, mode: str) -> dict:
    """mode: 'single'=束の種類が 1 つ / 'mixed'=束の中で種類が混ざり Python で分ける / 'scalar'=k=1 の Python。"""
    pools = Pools(seed, agents)
    ranks, hashes = pools.rank, pools.hash
    if k > heap_size:
        raise ValueError(f"束の大きさ k={k} が列の大きさ {heap_size} を超える")
    heap = build_heap(heap_size, agents, seed)
    for i in range(len(heap)):  # 体の番号を SoA の大きさに収め、種類を ROUND_KINDS にそろえる
        t, r, h, a = heap[i]
        heap[i] = (t, r % ROUND_KINDS, h, a % agents)
    heapq.heapify(heap)
    s = SoA(agents, seed)
    dwell_list = s.dwell.tolist()
    energy_list = s.energy.tolist()
    hpop, hpush = heapq.heappop, heapq.heappush
    asarray = np.asarray
    intp = np.intp

    def make_np_handler(kind):
        def handle(ag_list, t_now):
            idx = asarray(ag_list, dtype=intp)
            return batch_kernel(s, idx, t_now).tolist()
        return handle

    def make_py_handler(kind):
        def handle(a, t_now):
            energy_list[a] -= 0.01
            return t_now + dwell_list[a]
        return handle

    table = {kd: (make_py_handler(kd) if mode == "scalar" else make_np_handler(kd)) for kd in range(ROUND_KINDS)}
    pc = time.perf_counter_ns
    done = 0
    cyc = 0
    calls = 0
    t0 = pc()
    if mode == "scalar":
        while done < n:
            t, r, _h, a = hpop(heap)
            nt = table[r](a, t)
            c = cyc & MASK
            hpush(heap, (nt, ranks[c] % ROUND_KINDS, hashes[c], a))
            cyc += 1
            done += 1
        calls = n
    elif mode == "single":
        ag = []
        while done < n:
            b = min(k, n - done)
            ag.clear()
            t = r = 0
            for _ in range(b):
                t, r, _h, a = hpop(heap)
                ag.append(a)
            nts = table[r](ag, t)
            calls += 1
            for j in range(b):
                c = (cyc + j) & MASK
                hpush(heap, (nts[j], ranks[c] % ROUND_KINDS, hashes[c], ag[j]))
            cyc += b
            done += b
    elif mode == "mixed":
        buckets = [[] for _ in range(ROUND_KINDS)]
        while done < n:
            b = min(k, n - done)
            t = 0
            for _ in range(b):
                t, r, _h, a = hpop(heap)
                buckets[r].append(a)
            for kd in range(ROUND_KINDS):
                bk = buckets[kd]
                if bk:
                    nts = table[kd](bk, t)
                    calls += 1
                    for j in range(len(bk)):
                        c = (cyc + j) & MASK
                        hpush(heap, (nts[j], ranks[c] % ROUND_KINDS, hashes[c], bk[j]))
                    cyc += len(bk)
                    bk.clear()
            done += b
    else:
        raise ValueError(mode)
    t1 = pc()
    return {"per_event": (t1 - t0) / n, "handler_calls": calls, "heap_len_end": len(heap)}


# ---------------------------------------------------------------- (5) 体ごとの next_t_ns

def measure_argmin(n: int, agents: int, seed: int) -> dict:
    s = SoA(agents, seed)
    nt = s.next_t_ns
    dts = Pools(seed, agents).dt
    pc = time.perf_counter_ns
    t0 = pc()
    for i in range(n):
        j = int(nt.argmin())
        nt[j] += dts[i & MASK]
    t1 = pc()
    return {"per_event": (t1 - t0) / n}


def measure_window_scan(windows: int, agents: int, seed: int) -> dict:
    s = SoA(agents, seed)
    nt = s.next_t_ns
    pc = time.perf_counter_ns
    hits = 0
    t_end = SEC_NS
    t0 = pc()
    for _ in range(windows):
        idx = np.flatnonzero(nt < t_end)
        hits += idx.size
        t_end += SEC_NS
    t1 = pc()
    per_window = (t1 - t0) / windows
    return {"per_window": per_window, "day_s_86400_windows": per_window * 86_400 / 1e9,
            "mean_hits_per_window": hits / windows}


# ---------------------------------------------------------------- 1 日の見積り

def load_event_rows(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    rows = {}
    for key, v in d["rows"].items():
        total = v["total"] if isinstance(v, dict) else int(v)
        if key.startswith(BREAKDOWN_PREFIX) and key != BREAKDOWN_KEEP:
            role = "breakdown"
        elif key in REFERENCE_KEYS or key.startswith(REFERENCE_PREFIX):
            role = "reference"
        else:
            role = "sum"
        rows[key] = {"per_day": int(total), "role": role}
    return {"N": d.get("N"), "rows": rows}


def day_estimate(rows: dict, coefs: dict, floor_ms: float) -> dict:
    """coefs: 名前 → ns/事象。各行の 1 日の秒と、合計の行の和。"""
    out_rows = {}
    sum_events = 0
    for key, r in rows.items():
        out_rows[key] = {"per_day": r["per_day"], "role": r["role"],
                         "seconds": {c: r["per_day"] * v / 1e9 for c, v in coefs.items()}}
        if r["role"] == "sum":
            sum_events += r["per_day"]
    totals = {c: sum_events * v / 1e9 for c, v in coefs.items()}
    floor = {label: steps * floor_ms / 1e3 for label, steps in STEPS_PER_DAY.items()}
    return {"rows": out_rows, "sum_events": sum_events, "sum_seconds": totals,
            "step_floor_ms": floor_ms, "step_floor_seconds_per_day": floor}


# ---------------------------------------------------------------- 走らせる

def _median(xs: list[float]) -> float:
    return float(statistics.median(xs))


def _collect(fn, reps: int) -> dict:
    runs = [fn() for _ in range(reps)]
    keys = [k for k, v in runs[0].items() if isinstance(v, (int, float))]
    return {"runs": runs, "median": {k: _median([r[k] for r in runs]) for k in keys}, "repeats": reps}


def run(counts: list[int], repeats: int, single_from: int, heap_size: int, agents: int, kinds: list[int],
        batch_sizes: list[int], argmin_max: int, windows: int, seed: int, event_table: Path | None,
        floor_ms: float, coef_count: int | None, heap_sweep: list[int] | None = None, log=print) -> dict:
    res: dict = {"heap": {}, "dispatch": {}, "batch": {}, "round": {}, "argmin": {}, "window_scan": None,
                 "heap_size_sweep": {}}
    for n in counts:
        reps = 1 if n >= single_from else repeats
        key = str(n)
        log(f"[n={n:,} reps={reps}]")
        res["heap"][key] = {
            "ns_grain": _collect(lambda: measure_heap(n, heap_size, agents, seed, 1), reps),
            "sec_grain": _collect(lambda: measure_heap(n, heap_size, agents, seed, SEC_NS), reps),
        }
        log("  heap done")
        res["dispatch"][key] = {str(kd): _collect(lambda kd=kd: measure_dispatch(n, kd, agents, seed), reps)
                                for kd in kinds}
        log("  dispatch done")
        res["batch"][key] = {str(k): _collect(lambda k=k: measure_batch(n, k, agents, seed), reps)
                             for k in batch_sizes}
        log("  batch done")
        rd = {"scalar_k1": _collect(lambda: measure_round(n, 1, heap_size, agents, seed, "scalar"), reps)}
        for k in batch_sizes:
            rd[f"single_k{k}"] = _collect(lambda k=k: measure_round(n, k, heap_size, agents, seed, "single"), reps)
            if k > 1:
                rd[f"mixed_k{k}"] = _collect(lambda k=k: measure_round(n, k, heap_size, agents, seed, "mixed"), reps)
        res["round"][key] = rd
        log("  round done")
        if n <= argmin_max:
            res["argmin"][key] = _collect(lambda: measure_argmin(n, agents, seed), reps)
            log("  argmin done")
    res["window_scan"] = _collect(lambda: measure_window_scan(windows, agents, seed), repeats)
    # 列の大きさの感度((1) を 1 つの件数の点で・列に体ぶんの事象を全部持つか、世界の事象だけかの違い)
    multi_all = [n for n in counts if n < single_from]
    sweep_n = max(multi_all) if multi_all else min(counts)
    for hs in heap_sweep or []:
        res["heap_size_sweep"][str(hs)] = _collect(lambda hs=hs: measure_heap(sweep_n, hs, agents, seed, 1), repeats)
    res["heap_size_sweep_n"] = sweep_n
    if heap_sweep:
        log("  heap size sweep done")

    # 係数の代表: coef_count(無ければ 3 回測った最大の件数、それも無ければ最大の件数)
    multi = [n for n in counts if n < single_from]
    cn = coef_count if coef_count in counts else (max(multi) if multi else max(counts))
    ck = str(cn)
    coefs = {"heap_pair_net": res["heap"][ck]["ns_grain"]["median"]["pair_net"],
             "dispatch_dict_net": res["dispatch"][ck][str(max(kinds))]["median"]["dict_net"]}
    for name, v in res["round"][ck].items():
        coefs[f"round_{name}"] = v["median"]["per_event"]
    summary = {"coef_count": cn, "coefs_ns_per_event": coefs}
    if event_table is not None and event_table.exists():
        rows = load_event_rows(event_table)
        summary["day_estimate"] = day_estimate(rows["rows"], coefs, floor_ms)
        summary["event_table_N"] = rows["N"]
        summary["window_scan_day_s"] = res["window_scan"]["median"]["day_s_86400_windows"]
    return {"results": res, "summary": summary}


def _fmt(x: float, nd: int = 1) -> str:
    return f"{x:,.{nd}f}"


def to_markdown(doc: dict) -> str:
    p = doc["params"]
    r = doc["results"]
    lines = []
    counts = [str(n) for n in p["counts"]]
    hdr = "| 項 | " + " | ".join(f"{int(c):,} 件" for c in counts) + " |"
    sep = "|---|" + "---:|" * len(counts)

    def row(label, getter):
        cells = []
        for c in counts:
            try:
                cells.append(_fmt(getter(c)))
            except KeyError:
                cells.append("—")
        return f"| {label} | " + " | ".join(cells) + " |"

    lines += ["### 表 1 係数(ns/事象・各点の中央値)", "", hdr, sep]
    for g, gl in (("ns_grain", "ns の連続値"), ("sec_grain", "1 秒の格子")):
        for m, ml in (("pop_net", "pop(純)"), ("push_net", "push(純)"), ("pair_net", "pop+push(純)"),
                      ("pair_gross", "pop+push(輪こみ)")):
            lines.append(row(f"(1) heapq {ml}・{gl}", lambda c, g=g, m=m: r["heap"][c][g]["median"][m]))
    for kd in p["kinds"]:
        for m, ml in (("dict_net", "dict で引いて呼ぶ(純)"), ("list_net", "list で引いて呼ぶ(純)"),
                      ("direct_net", "直に呼ぶ(純)")):
            lines.append(row(f"(2) {kd} 種・{ml}", lambda c, kd=kd, m=m: r["dispatch"][c][str(kd)]["median"][m]))
    lines.append(row("(2) 輪の基準(添字 2 回)", lambda c: r["dispatch"][c][str(p["kinds"][0])]["median"]["loop_base"]))
    for k in p["batch_sizes"]:
        lines.append(row(f"(3) NumPy の束 k={k}(1 件あたり)", lambda c, k=k: r["batch"][c][str(k)]["median"]["per_event"]))
    for k in p["batch_sizes"]:
        lines.append(row(f"(3) NumPy の束 k={k}(1 束あたり)", lambda c, k=k: r["batch"][c][str(k)]["median"]["per_batch"]))
    names = ["scalar_k1"] + [f"single_k{k}" for k in p["batch_sizes"]] + \
            [f"mixed_k{k}" for k in p["batch_sizes"] if k > 1]
    labels = {"scalar_k1": "(4) 往復 k=1・Python のスカラ"}
    for k in p["batch_sizes"]:
        labels[f"single_k{k}"] = f"(4) 往復 k={k}・束の種類 1 つ・NumPy"
        labels[f"mixed_k{k}"] = f"(4) 往復 k={k}・種類 {ROUND_KINDS} が混ざる・NumPy"
    for nm in names:
        lines.append(row(labels[nm], lambda c, nm=nm: r["round"][c][nm]["median"]["per_event"]))
    lines.append(row(f"(5) argmin で次の 1 件({p['agents']:,} 体の配列)", lambda c: r["argmin"][c]["median"]["per_event"]))
    lines.append("")
    ws = r["window_scan"]["median"]
    lines.append(f"(5) 1 秒の窓に入る体を引く(`flatnonzero(next_t_ns < 窓の終わり)`・{p['agents']:,} 体): "
                 f"窓 1 つ {_fmt(ws['per_window'] / 1e3, 1)} µs・86,400 窓で {_fmt(ws['day_s_86400_windows'], 2)} 秒/日"
                 f"(窓あたりの平均の件数 {_fmt(ws['mean_hits_per_window'], 1)})。")
    lines.append("")
    sw = r.get("heap_size_sweep") or {}
    if sw:
        lines += [f"### 表 1b 列の大きさの感度((1) heapq・ns の連続値・{int(r['heap_size_sweep_n']):,} 件・ns/事象)", "",
                  "| 列の大きさ | pop(純) | push(純) | pop+push(純) | pop+push(輪こみ) |", "|---:|---:|---:|---:|---:|"]
        for hs, v in sw.items():
            m = v["median"]
            lines.append(f"| {int(hs):,} | {_fmt(m['pop_net'])} | {_fmt(m['push_net'])} | {_fmt(m['pair_net'])} | "
                         f"{_fmt(m['pair_gross'])} |")
        lines.append("")
    s = doc["summary"]
    if "day_estimate" in s:
        de = s["day_estimate"]
        coefs = s["coefs_ns_per_event"]
        cols = list(coefs)
        lines += [f"### 表 2 1 日の固定費の見積り(秒・35 万体 1 日の事象数 × {int(s['coef_count']):,} 件の点の係数)", ""]
        lines.append("| 係数の名前 | ns/事象 |")
        lines.append("|---|---:|")
        for cname in cols:
            lines.append(f"| {cname} | {_fmt(coefs[cname])} |")
        lines.append("")
        lines.append("| R-130 §4 の行 | 役 | 1 日の件数 | " + " | ".join(cols) + " |")
        lines.append("|---|---|---:|" + "---:|" * len(cols))
        for key, v in de["rows"].items():
            lines.append(f"| `{key}` | {v['role']} | {v['per_day']:,} | " +
                         " | ".join(_fmt(v["seconds"][c], 2) for c in cols) + " |")
        lines.append(f"| **合計(役 sum)** | — | **{de['sum_events']:,}** | " +
                     " | ".join(f"**{_fmt(de['sum_seconds'][c], 2)}**" for c in cols) + " |")
        lines.append("")
        lines.append("比較(事象の無い刻みの床 "
                     f"{de['step_floor_ms']} ms/刻み × 刻みの数): " +
                     "・".join(f"{lab} {_fmt(v, 1)} 秒/日" for lab, v in de["step_floor_seconds_per_day"].items()) +
                     f"。(5) の窓の走査は 86,400 窓で {_fmt(s['window_scan_day_s'], 2)} 秒/日。")
    return "\n".join(lines) + "\n"


def _ints(s: str) -> list[int]:
    return [int(x.replace("_", "")) for x in s.split(",") if x.strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--counts", default="10000", help="事象の件数の一覧(カンマ区切り・既定 10000)")
    ap.add_argument("--repeats", type=int, default=3, help="各点の繰り返し(中央値を取る)")
    ap.add_argument("--single-from", type=int, default=5_000_000, help="この件数以上は 1 回だけ測る")
    ap.add_argument("--heap-size", type=int, default=AGENTS_350K, help="(1)(4) の列の大きさ(既定=35 万体に 1 件ずつ)")
    ap.add_argument("--agents", type=int, default=AGENTS_350K, help="(3)(4)(5) の体の配列の大きさ")
    ap.add_argument("--kinds", default="5,10", help="(2) の種類の数の一覧")
    ap.add_argument("--batch-sizes", default="1,16,256", help="(3)(4) の束の大きさ k の一覧")
    ap.add_argument("--argmin-max", type=int, default=100_000, help="(5) argmin を測る件数の上限(1 件が O(体数))")
    ap.add_argument("--windows", type=int, default=2_000, help="(5) の窓の走査を測る窓の数")
    ap.add_argument("--heap-sweep", default="", help="(1) の列の大きさの感度の一覧(任意・例 1000,30000,345858)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--event-table", default=str(DEFAULT_EVENT_TABLE), help="R-130 §4 の event_table.json")
    ap.add_argument("--floor-ms", type=float, default=FLOOR_MS_DEFAULT, help="事象の無い刻みの床(ms/刻み)")
    ap.add_argument("--coef-count", type=int, default=None, help="1 日の見積りに使う係数の件数の点")
    ap.add_argument("--out", default=None, help="生の値の JSON の出力先(無ければ標準出力)")
    ap.add_argument("--md", default=None, help="表の Markdown の出力先(任意)")
    ap.add_argument("--no-gc", action="store_true", help="測る間 gc を止める(既定は止めない=実際の核に近い)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    counts = _ints(a.counts)
    kinds = _ints(a.kinds)
    batch_sizes = _ints(a.batch_sizes)
    if not counts or min(counts) <= 0 or a.repeats <= 0 or not kinds or not batch_sizes:
        ap.error("件数・繰り返し・種類・束は正の値")
    et = Path(a.event_table) if a.event_table else None
    log = (lambda *_x, **_y: None) if a.quiet else (lambda m: print(m, file=sys.stderr, flush=True))
    if a.no_gc:
        gc.disable()
    t0 = time.perf_counter()
    body = run(counts, a.repeats, a.single_from, a.heap_size, a.agents, kinds, batch_sizes, a.argmin_max,
               a.windows, a.seed, et, a.floor_ms, a.coef_count, heap_sweep=_ints(a.heap_sweep), log=log)
    try:
        et_label = et.resolve().relative_to(ROOT).as_posix() if et else None
    except ValueError:
        et_label = et.name if et else None
    doc = {
        "tool": "tools/bench/event_cost/event_cost.py",
        "units": "ns per event unless noted",
        "machine": machine_info(),
        "params": {"counts": counts, "repeats": a.repeats, "single_from": a.single_from,
                   "heap_size": a.heap_size, "agents": a.agents, "kinds": kinds, "batch_sizes": batch_sizes,
                   "round_kinds": ROUND_KINDS, "argmin_max": a.argmin_max, "windows": a.windows, "seed": a.seed,
                   "event_table": et_label, "floor_ms": a.floor_ms,
                   "heap_sweep": _ints(a.heap_sweep), "gc_disabled_during_run": a.no_gc, "pool": POOL, "stride": STRIDE},
        "wall_s": None,
        **body,
    }
    doc["wall_s"] = round(time.perf_counter() - t0, 2)
    text = json.dumps(doc, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text + "\n", encoding="utf-8", newline="\n")
    else:
        print(text)
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text(to_markdown(doc), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
