"""6 段目 6a(記憶 第 1 段の記録)の計測。

使い方(リポジトリの根から)::

    # 既定 15 腕の final が 5 段目の値のまま(=表は腕でだけ確保)
    python docs/bench/analysis/memory-stage1-2026-09-28/memory_measure.py arms15 \\
        --world data/world/v2 --out docs/bench/analysis/memory-stage1-2026-09-28/arms15.json
    # --memory on の腕(1 構成=1 プロセス・off/on N=128/64/256・+親しみの表・+顕著行為の発生率・classical)
    python docs/bench/analysis/memory-stage1-2026-09-28/memory_measure.py on \\
        --world data/world/v2 --out docs/bench/analysis/memory-stage1-2026-09-28/on_arms.json
    # 実 LLM テープのリプレイ(エンジンは回さない・1 日の事象の供給量)
    python docs/bench/analysis/memory-stage1-2026-09-28/memory_measure.py replay \\
        --world data/world/v2 --out docs/bench/analysis/memory-stage1-2026-09-28/replay.json

- ``arms15``: 15 腕([W6 再生成の計測](../w6-regen-2026-09-28/w6_regen_measure.py) の ``ARMS``)を既定(off)で
  回し、[5 段目の記録](../energy-classical-2026-09-28/arms15_energy.json) の final と突き合わせる。
- ``on``: 構成ごとに別プロセス。壁時計(``time.perf_counter``)とピークの作業セット(Windows
  ``K32GetProcessMemoryInfo``)と ``AgentState.bytes_total()``。on は各 checkpoint で記憶の 9 欄を混ぜない
  ハッシュも控え、off の final と一致するか(=記録は挙動を変えない)を見る。**壁時計と RSS は決定論でない**。
- ``replay``: テープ(open 腕を除く・内容で束ねる=段 2a と同じ)の呼ごとに、記憶の書き手が拾う事象の目安を
  体ごとに数える: 行動(購入/食事/並ぶ/移動/乗車/就寝/会話/通報/手伝い の応答=成否の 1 件)・会話(会話の
  応答=会話の行の上限)・気づき(B4 に顕著行為の行が出た呼=p_notice を掛ける前の上限)・強い看板(B2 に
  載った看板の POI の異なる数=初見の上限)。記憶アジェンダの見込み 8.9 件/体/日(呼 7.0+気づき 1.9)と並べる。

絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
W6 = HERE.parent / "w6-regen-2026-09-28" / "w6_regen_measure.py"
BEFORE = HERE.parent / "energy-classical-2026-09-28" / "arms15_energy.json"
PLACE_RE = re.compile(r"現在地はセル([^\s()()]+)")
SIGNAGE_SHOWN = "[B2 看板] 〔素性"
SALIENT_EMPTY = "目につく出来事はありません"
SALIENT_LINE = "[B4 行為] 目につく出来事:"
RECORDED_ACTIONS = ("購入", "食事", "並ぶ", "移動", "乗車", "就寝", "会話", "通報", "手伝い")
CONFIGS: dict[str, dict[str, Any]] = {
    "off": {"vocab_version": "v3"},
    "on_n128": {"vocab_version": "v3", "memory": "on"},
    "on_n64": {"vocab_version": "v3", "memory": "on", "memory_n": 64},
    "on_n256": {"vocab_version": "v3", "memory": "on", "memory_n": 256},
    "on_familiarity": {"vocab_version": "v3", "memory": "on", "familiarity": "on"},
    "on_salient_200": {"vocab_version": "v3", "memory": "on", "salient_rate_per_10k": 200.0},
    "off_salient_200": {"vocab_version": "v3", "salient_rate_per_10k": 200.0},
    "on_classical": {"vocab_version": "v3", "memory": "on", "policy": "classical",
                     "chooser": "classical"},
    "off_classical": {"vocab_version": "v3", "policy": "classical", "chooser": "classical"},
}


def _w6() -> Any:
    spec = importlib.util.spec_from_file_location("w6_regen_measure", W6)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _peak_working_set_bytes() -> int:
    try:
        import ctypes
        import ctypes.wintypes as wt

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
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


def _q(x: list[float]) -> dict[str, float]:
    if not x:
        return {}
    a = np.asarray(x, dtype=np.float64)
    return {p: round(float(np.percentile(a, float(p[1:]))), 3)
            for p in ("p10", "p50", "p90", "p99", "p100")} | {"mean": round(float(a.mean()), 3)}


# ------------------------------------------------------------------ arms15
def cmd_arms15(args: argparse.Namespace) -> int:
    from shibuya import cli

    w6 = _w6()
    before = {r["arm"]: (r["final_hash"], r["llm_calls"])
              for r in json.loads(BEFORE.read_text(encoding="utf-8"))["arms"]}
    rows = []
    for name, kw in w6.ARMS.items():
        res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
        calls = int(res.column("calls").sum()) if res.diagnostics.size else 0
        row = {"arm": name, "final_5th_stage": before.get(name, ("", 0))[0], "final": res.final_hash,
               "llm_calls": calls, "memory": bool(res.run_manifest_fields()["memory"])}
        row["unchanged"] = (row["final"], calls) == before.get(name)
        rows.append(row)
        print(f"{name}: {row['final_5th_stage'][:8]} → {row['final'][:8]} "
              f"{'=' if row['unchanged'] else '≠'}", flush=True)
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/memory-stage1/arms15/1",
                                          "arms": rows}, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ on(1 構成=1 プロセス)
def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.agents import state as S
    from shibuya.core.hashing import blake3_hex

    kw = dict(CONFIGS[args.config])
    rec: list[str] = []
    orig = S.AgentState.state_hash

    def patched(agent_state: Any) -> str:
        if getattr(agent_state, "memory_columns", False):
            rec.append(agent_state.registry.state_hash(exclude=S.MEMORY_FIELDS))
        return orig(agent_state)

    S.AgentState.state_hash = patched  # type: ignore[method-assign]
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
    wall = time.perf_counter() - t0
    wo = ""
    if rec and len(rec) == len(res.checkpoints):
        cp = res.checkpoints[-1]
        parts = [rec[-1], cp.world_hash, cp.population_hash, cp.schedule_hash]
        if cp.activity_hash:
            parts.append(cp.activity_hash)
        wo = blake3_hex("\x1f".join(parts).encode("utf-8"))
    m = res.run_manifest_fields()
    out = {
        "config": args.config, "args": kw, "final_hash": res.final_hash,
        "final_wo_memory": wo, "llm_calls": int(res.llm_calls),
        "salient_events": int(res.salient_events), "noticed": int(res.noticed),
        "agents_bytes_total": int(res.agents.bytes_total()),  # type: ignore[attr-defined]
        "agents_declared_bytes_per_agent": int(res.agents.declared_bytes_per_agent),  # type: ignore[attr-defined]
        "memory_summary": m.get("memory_summary", {}),
        "wall_seconds_nondeterministic": round(wall, 2),
        "peak_working_set_bytes_nondeterministic": _peak_working_set_bytes(),
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_on(args: argparse.Namespace) -> int:
    rows = []
    for name in CONFIGS:
        cmd = [sys.executable, str(Path(__file__)), "one", "--config", name, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed)]
        got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        row = json.loads(got.stdout.strip().splitlines()[-1])
        rows.append(row)
        print(f"{name}: final {row['final_hash'][:8]} wo {row['final_wo_memory'][:8]} calls "
              f"{row['llm_calls']:,} wall {row['wall_seconds_nondeterministic']}s peak WS "
              f"{row['peak_working_set_bytes_nondeterministic'] / 2**20:.1f} MiB", flush=True)
    finals = {r["config"]: r["final_hash"] for r in rows}
    for r in rows:
        base = {"on_n128": "off", "on_n64": "off", "on_n256": "off", "on_salient_200": "off_salient_200",
                "on_classical": "off_classical"}.get(r["config"])
        if base:
            r["wo_memory_equals_off"] = r["final_wo_memory"] == finals[base]
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/memory-stage1/on/1", "rows": rows},
                                         ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ replay
def cmd_replay(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from shibuya.llm.parser import parse_two_line
    from shibuya.perception.renderer import PerceptionAssets
    from shibuya.world.state import World

    world = World.load_or_synthetic(args.world, n_cells=139, seed=1)
    passets = PerceptionAssets.load_or_synthetic(args.world, world)
    place_ids = pq.read_table(Path(args.world) / "w2_cells.parquet", columns=["place_id"]).column(0).to_pylist()
    cell_of = {str(p): i for i, p in enumerate(place_ids)}
    sign_poi = np.full(world.n_cells, -1, dtype=np.int64)
    for c in range(world.n_cells):
        for j in passets.visible_poi[c]:
            if int(j) < world.n_poi:
                sign_poi[c] = int(j)
                break
    rows_out = []
    seen_sig: set[str] = set()
    uniq: dict[str, list] = defaultdict(list)
    for p in sorted(glob.glob(args.tapes)):
        pp = Path(p)
        arm, run = pp.parent.name, pp.parent.parent.name
        if "__open" in arm:
            continue
        ver = "v2" if arm.endswith("_v2") else "v1"
        blocks = pq.read_table(pp.parent / "blocks.parquet", columns=["block_id", "text"]).to_pydict()
        cell_by_block: dict[str, str] = {}
        sign_by_block: dict[str, bool] = {}
        salient_by_block: dict[str, bool] = {}
        for bid, tx in zip(blocks["block_id"], blocks["text"]):
            if "[B2 場所]" in tx:
                m = PLACE_RE.search(tx)
                if m:
                    cell_by_block[bid] = m.group(1)
                sign_by_block[bid] = SIGNAGE_SHOWN in tx
            if SALIENT_LINE in tx:
                salient_by_block[bid] = True
        t = pq.read_table(p, columns=["agent_id", "tick", "response", "deferred", "block_ids"]).to_pydict()
        actions: Counter = Counter()
        talks: Counter = Counter()
        salient: Counter = Counter()
        signs: dict[int, set[int]] = defaultdict(set)
        agents_seen: set[int] = set()
        by_action: Counter = Counter()
        for k in range(len(t["agent_id"])):  # 逐次: 呼ごと
            if t["deferred"][k] or not t["response"][k]:
                continue
            aid = int(t["agent_id"][k])
            agents_seen.add(aid)
            bids = t["block_ids"][k]
            b2 = next((b for b in bids if b in cell_by_block), None)
            cell = cell_of.get(cell_by_block[b2], -1) if b2 else -1
            if b2 and sign_by_block.get(b2) and cell >= 0 and sign_poi[cell] >= 0:
                signs[aid].add(int(sign_poi[cell]))
            if any(b in salient_by_block for b in bids):
                salient[aid] += 1
            pr = parse_two_line(t["response"][k], ver)
            if pr.action in RECORDED_ACTIONS:
                actions[aid] += 1
                by_action[pr.action] += 1
                if pr.action == "会話":
                    talks[aid] += 1
        ag = sorted(agents_seen)
        per = {
            "actions": [actions[a] for a in ag],
            "talks": [talks[a] for a in ag],
            "salient_upper": [salient[a] for a in ag],
            "signage_first_upper": [len(signs[a]) for a in ag],
        }
        per["total_upper"] = [x + y + z for x, y, z in zip(per["actions"], per["salient_upper"],
                                                             per["signage_first_upper"])]
        summ = {"agents_with_calls": len(ag), **{k: _q(v) for k, v in per.items()},
                "by_action": dict(by_action)}
        rows_out.append({"tape": f"{run}/{arm}", "vocab": ver, "summary": summ})
        sig = json.dumps({k: v for k, v in summ.items() if k != "by_action"}, sort_keys=True)
        if sig not in seen_sig:
            seen_sig.add(sig)
            uniq["tapes"].append(f"{run}/{arm}")
            for k, v in per.items():
                uniq[k] += v
        print(f"{run}/{arm}: 体 {len(ag)} 行動/体 {np.mean(per['actions']) if ag else 0:.2f} "
              f"気づき上限/体 {np.mean(per['salient_upper']) if ag else 0:.2f}", flush=True)
    doc = {
        "schema": "shibuya.bench/memory-stage1/replay/1",
        "tapes": rows_out,
        "unique": {"tapes": uniq["tapes"], "agent_days": len(uniq["actions"]),
                   **{k: _q(uniq[k]) for k in ("actions", "talks", "salient_upper",
                                                "signage_first_upper", "total_upper")}},
        "expected_per_agent_day": {"calls": 7.0, "noticed": 1.9, "total": 8.9,
                                   "source": "docs/design/v2-memory-stage1-implementation-agenda.md 冒頭の事実(R-48)"},
        "note": ("体=その日に呼の在った体。行動=記録する行為の応答(成否の 1 件の目安・移動は着いた/失敗の 1 件)。"
                 "会話=会話の応答(会話の行の上限)。気づき=B4 に顕著行為の行が出た呼(p_notice を掛ける前の上限)。"
                 "強い看板=B2 に載った看板の POI の異なる数(初見の上限)。"),
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="6 段目 6a の計測")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("arms15", "on", "one", "replay"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        if name != "one":
            sp.add_argument("--out", required=True)
        if name == "one":
            sp.add_argument("--config", required=True, choices=tuple(CONFIGS))
        if name == "replay":
            sp.add_argument("--tapes", default="data/tape/c8_*/*/calls.parquet")
    args = ap.parse_args(argv)
    return {"arms15": cmd_arms15, "on": cmd_on, "one": cmd_one, "replay": cmd_replay}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
