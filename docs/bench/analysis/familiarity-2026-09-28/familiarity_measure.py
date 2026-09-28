"""4 段目(記憶の先行部品=M13 訪問カウンタ+M17 露出カウンタ・親しみの表)の計測。

使い方(リポジトリの根から)::

    # 既定 15 腕の final が 3 段目の値のまま(=表は腕でだけ確保)
    python docs/bench/analysis/familiarity-2026-09-28/familiarity_measure.py arms15 \\
        --world data/world/v2 --out docs/bench/analysis/familiarity-2026-09-28/arms15.json
    # --familiarity on の腕(v3 既定・K=32/64/128・off との壁時計/RSS・表の要約)=腕ごとに別プロセス
    python docs/bench/analysis/familiarity-2026-09-28/familiarity_measure.py on \\
        --world data/world/v2 --out docs/bench/analysis/familiarity-2026-09-28/on_arms.json
    # 実 LLM テープ 17 本のリプレイ(エンジンは回さない・件数の目安)
    python docs/bench/analysis/familiarity-2026-09-28/familiarity_measure.py replay \\
        --world data/world/v2 --out docs/bench/analysis/familiarity-2026-09-28/replay.json
    # 近似式と厳密式の差(例)
    python docs/bench/analysis/familiarity-2026-09-28/familiarity_measure.py approx \\
        --out docs/bench/analysis/familiarity-2026-09-28/approx.json

- ``arms15``: [W6 再生成の計測](../w6-regen-2026-09-28/w6_regen_measure.py) の 15 腕を既定(off)で回し、
  [3 段目の記録](../l4-unlimited-2026-09-28/l4_arms15.json) の ``unlimited`` の final と突き合わせる。
- ``on``: v3 既定(mock 5,000・seed 1)を off / on(K=64)/ on(K=32)/ on(K=128)で**別プロセス**に回し、
  壁時計(``time.perf_counter``)と**ピークの作業セット**(Windows ``K32GetProcessMemoryInfo`` の
  ``PeakWorkingSetSize``=RSS 相当)と ``AgentState.bytes_total()`` を取る。on は各 checkpoint で
  表の 5 欄を混ぜないハッシュも控え、off の final と一致するか(=表は挙動を変えない)を見る。
  **壁時計と RSS は決定論でない**(同じ PC の 1 回の値)。
- ``replay``: テープ(open 腕を除く 23 本・内容で束ねて 17 本=段 2a と同じ)の呼ごとに、(i) 購入/食事で
  段 2a の候補の解決が営業中の店に当たった呼=訪問の目安(所持金・在庫・席は見ない)(ii) B2 に看板行が
  載った呼=看板の露出(その呼のセルの看板の POI)(iii) 同じ体の呼の間でセルが変わった回=場所の入場の
  **下限**(呼の無い間の移動は見えない)を体ごとに数え、表の行数の下限(異なるもの の数)を出す。
- ``approx``: 最適化学習の近似 ``ln(n/(1−d)) − d·ln(L+1)`` と厳密式 ``ln Σ(Δt+1)^−d`` の差の例。

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
L4 = HERE.parent / "l4-unlimited-2026-09-28" / "l4_arms15.json"
PLACE_RE = re.compile(r"現在地はセル([^\s()()]+)")
SIGNAGE_SHOWN = "[B2 看板] 〔素性"


def _w6() -> Any:
    spec = importlib.util.spec_from_file_location("w6_regen_measure", W6)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _peak_working_set_bytes() -> int:
    """Windows のピーク作業セット(RSS 相当)。取れなければ -1。"""
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
    except Exception:  # noqa: BLE001 - Windows 以外
        return -1


# ------------------------------------------------------------------ arms15
def cmd_arms15(args: argparse.Namespace) -> int:
    from shibuya import cli

    w6 = _w6()
    before = {r["arm"]: r["unlimited"]["final_hash"]
              for r in json.loads(L4.read_text(encoding="utf-8"))["arms"]}
    rows = []
    for name, kw in w6.ARMS.items():
        res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
        row = {"arm": name, "final_stage3": before.get(name, ""), "final": res.final_hash,
               "llm_calls": int(res.llm_calls),
               "familiarity": bool(res.run_manifest_fields()["familiarity"])}
        row["unchanged"] = row["final"] == row["final_stage3"]
        rows.append(row)
        print(f"{name}: {row['final_stage3'][:8]} → {row['final'][:8]} "
              f"{'=' if row['unchanged'] else '≠'}", flush=True)
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/familiarity-2026-09-28/arms15/1",
                                          "arms": rows}, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8")
    return 0


# ------------------------------------------------------------------ on(1 腕=1 プロセス)
def cmd_one(args: argparse.Namespace) -> int:
    """子プロセスの本体: 1 構成を回して JSON を標準出力の最終行に出す。"""
    from shibuya import cli
    from shibuya.agents import state as S
    from shibuya.core.hashing import blake3_hex

    rec: list[str] = []
    orig = S.AgentState.state_hash

    def patched(agent_state: Any) -> str:
        if getattr(agent_state, "familiarity_columns", False):
            rec.append(agent_state.registry.state_hash(exclude=S.FAMILIARITY_FIELDS))
        return orig(agent_state)

    S.AgentState.state_hash = patched  # type: ignore[method-assign]
    fam = args.familiarity == "on"
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, vocab_version="v3",
                  familiarity=args.familiarity, familiarity_k=args.k)
    wall = time.perf_counter() - t0
    wo = ""
    if fam and rec and len(rec) == len(res.checkpoints):
        cp = res.checkpoints[-1]
        parts = [rec[-1], cp.world_hash, cp.population_hash, cp.schedule_hash]
        if cp.activity_hash:
            parts.append(cp.activity_hash)
        wo = blake3_hex("\x1f".join(parts).encode("utf-8"))
    out = {
        "familiarity": args.familiarity, "k": args.k if fam else 0,
        "final_hash": res.final_hash, "final_wo_familiarity": wo,
        "llm_calls": int(res.llm_calls),
        "agents_bytes_total": int(res.agents.bytes_total()),  # type: ignore[attr-defined]
        "wall_seconds_nondeterministic": round(wall, 2),
        "peak_working_set_bytes_nondeterministic": _peak_working_set_bytes(),
        "summary": dict(res.familiarity_summary),
        "top3_examples": [],
    }
    if fam:
        from shibuya.engine.familiarity import FamiliarityLayer

        lay = FamiliarityLayer(res.n_agents, args.k)
        r = res.agents.registry  # type: ignore[attr-defined]
        rows_used = (r.fam_thing != -1).sum(axis=1)
        for aid in np.argsort(-rows_used, kind="stable")[:3].tolist():
            out["top3_examples"].append({"agent": int(aid), "rows": int(rows_used[aid]),
                                         "top3": lay.top_k(res.agents, aid, res.ticks - 1)})
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_on(args: argparse.Namespace) -> int:
    configs = [("off", 64), ("on", 64), ("on", 32), ("on", 128)]
    rows = []
    for fam, k in configs:
        cmd = [sys.executable, str(Path(__file__)), "one", "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed),
               "--familiarity", fam, "--k", str(k)]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        row = json.loads(proc.stdout.strip().splitlines()[-1])
        rows.append(row)
        print(f"{fam} K={k}: final {row['final_hash'][:8]} wall {row['wall_seconds_nondeterministic']}s "
              f"peakWS {row['peak_working_set_bytes_nondeterministic'] / 1e6:.1f} MB "
              f"agents {row['agents_bytes_total'] / 1e6:.2f} MB", flush=True)
    off = rows[0]
    for row in rows[1:]:
        row["wo_familiarity_equals_off"] = row["final_wo_familiarity"] == off["final_hash"]
        row["d_agents_bytes"] = row["agents_bytes_total"] - off["agents_bytes_total"]
        row["d_peak_working_set_bytes_nondeterministic"] = (
            row["peak_working_set_bytes_nondeterministic"] - off["peak_working_set_bytes_nondeterministic"]
        )
        row["d_wall_seconds_nondeterministic"] = round(
            row["wall_seconds_nondeterministic"] - off["wall_seconds_nondeterministic"], 2
        )
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/familiarity-2026-09-28/on/1",
                                          "n_agents": args.agents, "seed": args.seed,
                                          "arms": rows}, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8")
    return 0


# ------------------------------------------------------------------ replay
class _Reg:
    def __init__(self, cell: np.ndarray) -> None:
        self.cell = cell
        self.node = np.zeros(cell.size, dtype=np.int64)
        self.hunger = np.zeros(cell.size, dtype=np.int64)


class _Agents:
    def __init__(self, cell: np.ndarray) -> None:
        self.registry = _Reg(cell)


def _q(x: list[int] | np.ndarray) -> dict[str, float]:
    a = np.asarray(x, dtype=np.float64)
    if a.size == 0:
        return {}
    return {p: round(float(np.percentile(a, float(p[1:]))), 2)
            for p in ("p10", "p50", "p90", "p99", "p100")} | {"mean": round(float(a.mean()), 3)}


def cmd_replay(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from shibuya.engine import commit as C
    from shibuya.engine.chooser import NearestChooser
    from shibuya.engine.familiarity import place_thing
    from shibuya.engine.poi_target import TargetResolver
    from shibuya.engine.processes.opening import build_open_matrix
    from shibuya.llm.parser import parse_two_line
    from shibuya.perception.renderer import PerceptionAssets
    from shibuya.world import assets as WA
    from shibuya.world.state import World

    world = World.load_or_synthetic(args.world, n_cells=139, seed=1)
    passets = PerceptionAssets.load_or_synthetic(args.world, world)
    pa_ = WA.load_process_assets(Path(args.world), world.assets)
    openm = build_open_matrix(world.n_poi, pa_.plan_poi, pa_.plan_day, pa_.plan_start, pa_.plan_end, 0)
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
        for bid, tx in zip(blocks["block_id"], blocks["text"]):
            if "[B2 場所]" in tx:
                m = PLACE_RE.search(tx)
                if m:
                    cell_by_block[bid] = m.group(1)
                sign_by_block[bid] = SIGNAGE_SHOWN in tx
        t = pq.read_table(p, columns=["agent_id", "tick", "response", "deferred", "block_ids"]).to_pydict()
        res = TargetResolver(world=world, chooser=NearestChooser(), seed=1)
        visits: Counter = Counter()
        signage: Counter = Counter()
        entries: Counter = Counter()
        things: dict[int, set[int]] = defaultdict(set)
        last_cell: dict[int, int] = {}
        order = np.lexsort((np.asarray(t["agent_id"]), np.asarray(t["tick"])))
        with world.writable():
            for k in order.tolist():  # 逐次: 呼ごと(tick 順)
                if t["deferred"][k] or not t["response"][k]:
                    continue
                aid = int(t["agent_id"][k])
                tick = int(t["tick"][k])
                bids = t["block_ids"][k]
                b2 = next((b for b in bids if b in cell_by_block), None)
                cell = cell_of.get(cell_by_block[b2], -1) if b2 else -1
                if cell < 0:
                    continue
                if last_cell.get(aid) != cell:
                    entries[aid] += 1
                    things[aid].add(int(place_thing(cell)))
                    last_cell[aid] = cell
                if b2 and sign_by_block.get(b2) and sign_poi[cell] >= 0:
                    signage[aid] += 1
                    things[aid].add(int(sign_poi[cell]))
                pr = parse_two_line(t["response"][k], ver)
                if pr.action in ("購入", "食事"):
                    eat = pr.action == "食事"
                    world.pois.open_now[:] = openm[:, tick % 1440].astype(np.int8)
                    poi = int(res.resolve(_Agents(np.array([cell])), tick, np.array([0]),
                                          np.array([C.ACT_EAT if eat else C.ACT_BUY]), [pr.target],
                                          is_eat=np.array([eat]), is_buy_like=np.array([not eat]))[0])
                    if poi >= 0 and bool(world.open_mask(tick)[poi]):
                        visits[aid] += 1
                        things[aid].add(poi)
            world.pois.open_now[:] = -1
        agents_seen = sorted(set(last_cell))
        summ = {
            "agents_with_calls": len(agents_seen),
            "visits_per_agent": _q([visits[a] for a in agents_seen]),
            "signage_exposures_per_agent": _q([signage[a] for a in agents_seen]),
            "place_entries_lower_bound_per_agent": _q([entries[a] for a in agents_seen]),
            "distinct_things_lower_bound_per_agent": _q([len(things[a]) for a in agents_seen]),
            "agents_over_k64": int(sum(1 for a in agents_seen if len(things[a]) > 64)),
            "agents_over_k32": int(sum(1 for a in agents_seen if len(things[a]) > 32)),
            "totals": {"visits": int(sum(visits.values())), "signage": int(sum(signage.values())),
                       "place_entries": int(sum(entries.values()))},
        }
        rows_out.append({"tape": f"{run}/{arm}", "vocab": ver, "summary": summ})
        sig = json.dumps(summ, sort_keys=True)
        if sig not in seen_sig:
            seen_sig.add(sig)
            uniq["tapes"].append(f"{run}/{arm}")
            uniq["visits"] += [visits[a] for a in agents_seen]
            uniq["signage"] += [signage[a] for a in agents_seen]
            uniq["entries"] += [entries[a] for a in agents_seen]
            uniq["things"] += [len(things[a]) for a in agents_seen]
        print(f"{run}/{arm}: 体 {len(agents_seen)} 訪問 {summ['totals']['visits']} 看板 "
              f"{summ['totals']['signage']} 入場(下限) {summ['totals']['place_entries']} "
              f"K64 超 {summ['agents_over_k64']}", flush=True)
    doc = {
        "schema": "shibuya.bench/familiarity-2026-09-28/replay/1",
        "tapes": rows_out,
        "unique": {
            "tapes": uniq["tapes"],
            "agent_days": len(uniq["things"]),
            "visits_per_agent": _q(uniq["visits"]),
            "signage_exposures_per_agent": _q(uniq["signage"]),
            "place_entries_lower_bound_per_agent": _q(uniq["entries"]),
            "distinct_things_lower_bound_per_agent": _q(uniq["things"]),
            "agents_over_k64": int(sum(1 for x in uniq["things"] if x > 64)),
            "agents_over_k32": int(sum(1 for x in uniq["things"] if x > 32)),
        },
        "note": ("体=その日に呼の在った体(呼の無い体は数えない)。訪問=段 2a の候補の解決が営業中の店に"
                 "当たった購入/食事の呼(所持金・在庫・席は見ない=目安)。看板=B2 に看板行が載った呼。"
                 "入場=同じ体の呼の間でセルが変わった回(下限)。もの=POI と場所の異なる数(下限)。"),
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


# ------------------------------------------------------------------ approx
def cmd_approx(args: argparse.Namespace) -> int:
    from shibuya.engine.familiarity import activation_approx, activation_exact

    examples = []

    def add(name: str, ages: list[float]) -> None:
        n = len(ages)
        L = max(ages)
        ex = activation_exact(ages)
        ap = float(activation_approx(n, L)[()])
        examples.append({"case": name, "n": n, "L_min": L, "exact": round(ex, 4),
                         "approx": round(ap, 4), "approx_minus_exact": round(ap - ex, 4)})

    add("1 回・いま(L=0)", [0.0])
    add("1 回・10 時間前", [600.0])
    add("10 回・等間隔 60 分(最後がいま)", [60.0 * i for i in range(10)])
    add("10 回・等間隔 60 分(最後が 60 分前)", [60.0 * (i + 1) for i in range(10)])
    add("10 回・最初にまとめて(10 時間前に 10 分で)", [600.0 - i for i in range(10)])
    add("10 回・最近にまとめて(最初が 10 時間前・残り 9 回はこの 10 分)", [600.0] + [float(i) for i in range(9)])
    add("60 回・等間隔 24 分(1 日)", [24.0 * i for i in range(60)])
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/familiarity-2026-09-28/approx/1",
                                          "d": 0.5, "examples": examples},
                                         ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for e in examples:
        print(e, flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("arms15", "on", "replay", "approx", "one"):
        p = sub.add_parser(name)
        p.add_argument("--world", default="data/world/v2")
        p.add_argument("--agents", type=int, default=5_000)
        p.add_argument("--seed", type=int, default=1)
        p.add_argument("--out", default="")
        p.add_argument("--tapes", default="data/tape/c8_*/*/calls.parquet")
        p.add_argument("--familiarity", default="on")
        p.add_argument("--k", type=int, default=64)
    args = ap.parse_args(argv)
    return {"arms15": cmd_arms15, "on": cmd_on, "replay": cmd_replay, "approx": cmd_approx,
            "one": cmd_one}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
