"""D-120 7c(想起優先の候補合成・B5 の店の項・N8 の計測と腕)の計測。

使い方(リポジトリの根から)::

    # 既定の byte 一致: コミット済みの源(HEAD 1c1d1a0 を git archive で展開した src)と作業木で同じランを回す
    python docs/bench/analysis/store-memory-2026-09-28/choice_measure.py bytecheck \\
        --head-src <HEAD を展開した src> --scratch <作業用の場所> \\
        --out docs/bench/analysis/store-memory-2026-09-28/choice_byte_check.json
    # N8 の腕(1 腕=1 プロセス)→ 集計
    python docs/bench/analysis/store-memory-2026-09-28/choice_measure.py arms \\
        --out docs/bench/analysis/store-memory-2026-09-28/choice_arms.json

- ``bytecheck``: 構成 5 本(v3 既定・classical・記憶 on(店 off)・classical+記憶 on(店 off)・mock v3 の店 on)×
  源 2 本。比べるもの: final・店の 7 欄を混ぜない final・呼数・``blocks.parquet``・``calls.parquet`` の 14 列(列ごと)。
  mock v3 の店 on は B5 に店の項(v1.3)が載る=prompt_hash が変わる(記録)・mock は描画を読まない=店を混ぜない
  final は同じはず。
- ``arms``: mock 5,000 × 方策 classical × 選び手 classical × ``--memory on --store-memory on``。腕=口コミ off/on ×
  看板 off/on × seed 1/2+σ の感度 2 点(1:1:1:1・1:4:16:4=σ の値)+τ の感度 2 点(−1.5・−2.5)+参照(店 off=
  想起優先なし)× seed 1/2。1 腕ごとに: 店ごとの訪問(購入/食事の成立)→ 業態別 Gini・上位 10 店の占有率・HHI
  (``classical_measure.py`` と同じ式)・決め手の内訳・初回率・店頭の割合・伝播(店を知る体=店の行がある体の数を
  1 時間ごと)・``wom``。集計で **不予測性 U**=seed 1/2 の店別占有率の差の平均(Salganik 2006)を腕ごとに。
- ``b5``: mock v3(選び手 nearest)・classical・classical の会話だけの腕で、B5 の想起に載った店の項の数と行の tok。
  **C1/C3/C4 の台帳行(holdout)には触れない**。

絶対パスは書かない。壁時計は決定論でない。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
BASE = {"vocab_version": "v3", "memory": "on", "policy": "classical", "chooser": "classical"}
ARMS: dict[str, dict[str, Any]] = {
    "ref_nostore_s1": {"seed": 1},
    "ref_nostore_s2": {"seed": 2},
    "base_s1": {"seed": 1, "store_memory": "on"},
    "base_s2": {"seed": 2, "store_memory": "on"},
    "nowom_s1": {"seed": 1, "store_memory": "on", "store_wom": "off"},
    "nowom_s2": {"seed": 2, "store_memory": "on", "store_wom": "off"},
    "nosign_s1": {"seed": 1, "store_memory": "on", "store_signage": "off"},
    "nosign_s2": {"seed": 2, "store_memory": "on", "store_signage": "off"},
    "nowom_nosign_s1": {"seed": 1, "store_memory": "on", "store_wom": "off", "store_signage": "off"},
    "nowom_nosign_s2": {"seed": 2, "store_memory": "on", "store_wom": "off", "store_signage": "off"},
    "sigma_1_1_1_1_s1": {"seed": 1, "store_memory": "on",
                         "store_sigma": '{"self": 1, "wom": 1, "signage": 1, "net": 1}'},
    "sigma_1_4_16_4_s1": {"seed": 1, "store_memory": "on",
                          "store_sigma": '{"self": 1, "wom": 4, "signage": 16, "net": 4}'},
    "tau_-1.5_s1": {"seed": 1, "store_memory": "on", "memory_tau": -1.5},
    "tau_-2.5_s1": {"seed": 1, "store_memory": "on", "memory_tau": -2.5},
}
PAIRS = {"ref_nostore": ("ref_nostore_s1", "ref_nostore_s2"), "base": ("base_s1", "base_s2"),
         "nowom": ("nowom_s1", "nowom_s2"), "nosign": ("nosign_s1", "nosign_s2"),
         "nowom_nosign": ("nowom_nosign_s1", "nowom_nosign_s2")}
BYTE_CONFIGS: dict[str, dict[str, Any]] = {
    "v3_default": {"vocab_version": "v3"},
    "v3_classical": {"vocab_version": "v3", "policy": "classical", "chooser": "classical"},
    "v3_memory_on": {"vocab_version": "v3", "memory": "on"},
    "v3_classical_memory_on": {"vocab_version": "v3", "policy": "classical", "chooser": "classical",
                               "memory": "on"},
    "v3_store_on_mock": {"vocab_version": "v3", "memory": "on", "store_memory": "on"},
}


def _h(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:16]


def _gini(x: np.ndarray) -> float:
    v = np.sort(np.asarray(x, dtype=np.float64))
    n = v.size
    if n == 0 or v.sum() <= 0:
        return 0.0
    cum = np.cumsum(v)
    return float((n + 1 - 2 * (cum / cum[-1]).sum()) / n)


def _concentration(visits: np.ndarray, cats: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    carr = np.asarray(cats)
    for c in ("food", "shop", "all"):
        v = visits if c == "all" else visits[carr == c]
        tot = int(v.sum())
        top = np.sort(v)[::-1][:10]
        out[c] = {"n_poi": int(v.size), "visits": tot, "poi_visited": int(np.count_nonzero(v)),
                  "gini": round(_gini(v), 4),
                  "top10_share": round(float(top.sum()) / tot, 4) if tot else 0.0,
                  "hhi": round(float(((v / tot) ** 2).sum()), 5) if tot else 0.0}
    return out


def _final_wo(res: Any, rec: list[str]) -> str:
    from shibuya.core.hashing import blake3_hex

    if not rec or len(rec) != len(res.checkpoints):
        return ""
    cp = res.checkpoints[-1]
    parts = [rec[-1], cp.world_hash, cp.population_hash, cp.schedule_hash]
    if cp.activity_hash:
        parts.append(cp.activity_hash)
    return blake3_hex("\x1f".join(parts).encode("utf-8"))


def _patch_state_hash(rec: list[str]) -> None:
    from shibuya.agents import state as S

    orig = S.AgentState.state_hash
    ex = tuple(getattr(S, "STORE_MEMORY_FIELDS", ()))

    def patched(agent_state: Any) -> str:
        if getattr(agent_state, "store_memory_columns", False):
            rec.append(agent_state.registry.state_hash(exclude=ex))
        return orig(agent_state)

    S.AgentState.state_hash = patched  # type: ignore[method-assign]


# ------------------------------------------------------------------ bytecheck
def cmd_bytecheck_one(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from shibuya import cli

    rec: list[str] = []
    _patch_state_hash(rec)
    kw = dict(BYTE_CONFIGS[args.config])
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape, **kw)
    calls = pq.read_table(Path(args.tape) / "calls.parquet")
    blocks = pq.read_table(Path(args.tape) / "blocks.parquet")
    out = {
        "config": args.config, "final": res.final_hash[:16], "final_wo_store": _final_wo(res, rec)[:16],
        "calls": int(res.llm_calls), "calls_rows": int(calls.num_rows), "blocks_rows": int(blocks.num_rows),
        "blocks_sha": _h({n: blocks.column(n).to_pylist() for n in blocks.column_names}),
        "calls_columns_sha": {n: _h(calls.column(n).to_pylist()) for n in calls.column_names},
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_bytecheck(args: argparse.Namespace) -> int:
    runs = []
    scratch = Path(args.scratch)
    for name in BYTE_CONFIGS:
        pair = {}
        for side, src in (("head_1c1d1a0", args.head_src), ("working_tree_7c", "")):
            env = dict(os.environ)
            if src:
                env["PYTHONPATH"] = src
                env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"
            tape = scratch / f"{side}_{name}"
            cmd = [sys.executable, str(Path(__file__)), "bytecheck-one", "--config", name, "--world",
                   args.world, "--agents", str(args.agents), "--seed", str(args.seed), "--tape", str(tape)]
            got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True, env=env)
            pair[side] = json.loads(got.stdout.strip().splitlines()[-1])
        h, w = pair["head_1c1d1a0"], pair["working_tree_7c"]
        diff_cols = sorted(k for k in h["calls_columns_sha"] if h["calls_columns_sha"][k] != w["calls_columns_sha"].get(k))
        row = {"run": name, **pair,
               "final_equal": h["final"] == w["final"],
               "final_wo_store_equal": h["final_wo_store"] == w["final_wo_store"],
               "calls_equal": h["calls"] == w["calls"],
               "blocks_equal": (h["blocks_sha"], h["blocks_rows"]) == (w["blocks_sha"], w["blocks_rows"]),
               "calls_columns_equal": not diff_cols, "calls_columns_differ": diff_cols}
        runs.append(row)
        print(f"{name}: final {row['final_equal']} 店なし {row['final_wo_store_equal']} calls {row['calls_equal']} "
              f"blocks {row['blocks_equal']} calls 列 {row['calls_columns_equal']} {diff_cols}", flush=True)
    doc = {"schema": "shibuya.bench/store-choice-byte-check/1",
           "how": ("same runs (mock 5,000, seed 1, vocab v3, energy) with the committed source (git archive of "
                   "HEAD 1c1d1a0) and with the 7c working tree; tape = shared prompt blocks and the 14 call "
                   "columns. The store-off runs must match everywhere. The mock store-on run gets the v1.3 store "
                   "items in B5 (prompt_hash moves) while the store-free final stays the same (mock does not read "
                   "the prompt; the nearest chooser does not use the recall-first path)."),
           "runs": runs}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                              newline="\n")
    return 0


# ------------------------------------------------------------------ arms
def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.engine import memory as M
    from shibuya.engine import resolve as R
    from shibuya.world.state import World

    kw = {**BASE, **ARMS[args.arm]}
    seed = int(kw.pop("seed"))
    visit_pois: list[np.ndarray] = []
    knowers: list[np.ndarray] = []
    world = World.load_or_synthetic(Path(args.world), n_cells=139, seed=seed)
    n_poi = int(world.n_poi)
    orig_apply = R.apply
    orig_after = M.MemoryLayer.after_tick

    def apply(*a: Any, **k: Any) -> Any:
        k["track_visits"] = True
        out = orig_apply(*a, **k)
        visit_pois.extend(np.asarray(p, dtype=np.int64) for p in out.visit_pois)
        return out

    def after_tick(self: Any, agents: Any, tick: int, **k: Any) -> Any:
        out = orig_after(self, agents, tick, **k)
        if int(tick) % 60 == 59 and self.store is not None:
            p = np.asarray(agents.registry.sm_poi, dtype=np.int64).ravel()
            knowers.append(np.bincount(p[p >= 0], minlength=n_poi)[:n_poi])
        return out

    R.apply = apply  # type: ignore[assignment]
    M.MemoryLayer.after_tick = after_tick  # type: ignore[method-assign]
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=seed, world_dir=args.world, **kw)
    wall = time.perf_counter() - t0
    R.apply = orig_apply  # type: ignore[assignment]
    M.MemoryLayer.after_tick = orig_after  # type: ignore[method-assign]
    visits = np.bincount(np.concatenate(visit_pois) if visit_pois else np.zeros(0, dtype=np.int64),
                         minlength=n_poi)[:n_poi]
    m = res.run_manifest_fields()
    kn = np.stack(knowers) if knowers else np.zeros((0, n_poi), dtype=np.int64)
    top20 = np.argsort(-kn[-1], kind="stable")[:20] if kn.size else np.zeros(0, dtype=np.int64)
    names = [str(x) for x in world.assets.poi_name]
    out = {
        "arm": args.arm, "seed": seed, "args": kw, "final_hash": res.final_hash, "llm_calls": int(res.llm_calls),
        "visits_by_poi": visits.tolist(),
        "concentration": _concentration(visits, [str(c) for c in world.assets.poi_cat]),
        "store_choice": m.get("store_choice", {}),
        "store_memory_summary": {k: v for k, v in m.get("store_memory_summary", {}).items()
                                 if k in ("counts", "rows_used_per_agent", "rows_with_source_bit", "valence_sign",
                                          "recallable_share", "distinct_pois_known")},
        "wom": {k: v for k, v in m.get("wom", {}).items() if k in ("counts", "unmatched_share")},
        "chooser_stats": m.get("chooser_stats", {}),
        "propagation": {"hours": list(range(1, kn.shape[0] + 1)),
                        "top20": [{"poi": int(j), "name": names[j] if j < len(names) else str(j),
                                   "knowers_by_hour": kn[:, j].tolist()} for j in top20.tolist()]},
        "wall_seconds_nondeterministic": round(wall, 2),
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return 0


def _u(v1: np.ndarray, v2: np.ndarray, mask: np.ndarray) -> float:
    a, b = v1[mask].astype(np.float64), v2[mask].astype(np.float64)
    if a.sum() <= 0 or b.sum() <= 0:
        return 0.0
    return float(np.abs(a / a.sum() - b / b.sum()).mean())


def cmd_arms(args: argparse.Namespace) -> int:
    from shibuya.world.state import World

    tmp = Path(args.scratch) if args.scratch else HERE / "_tmp_choice"
    tmp.mkdir(parents=True, exist_ok=True)
    rows: dict[str, Any] = {}
    for name in ARMS:
        path = tmp / f"{name}.json"
        cmd = [sys.executable, str(Path(__file__)), "one", "--arm", name, "--world", args.world,
               "--agents", str(args.agents), "--out", str(path)]
        subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        rows[name] = json.loads(path.read_text(encoding="utf-8"))
        r = rows[name]
        sc = r["store_choice"]
        print(f"{name}: final {r['final_hash'][:8]} calls {r['llm_calls']:,} Gini food "
              f"{r['concentration']['food']['gini']} 想起 {sc.get('counts', {}).get('recall:chosen', 0)} "
              f"初回 {sc.get('first_visit_no_self_share')} wall {r['wall_seconds_nondeterministic']}s", flush=True)
    world = World.load_or_synthetic(Path(args.world), n_cells=139, seed=1)
    cats = np.asarray([str(c) for c in world.assets.poi_cat])
    u = {}
    for arm, (a1, a2) in PAIRS.items():
        v1 = np.asarray(rows[a1]["visits_by_poi"])
        v2 = np.asarray(rows[a2]["visits_by_poi"])
        u[arm] = {c: round(_u(v1, v2, np.ones(cats.size, dtype=bool) if c == "all" else cats == c), 7)
                  for c in ("food", "shop", "all")}
    for r in rows.values():
        r.pop("visits_by_poi", None)
    doc = {"schema": "shibuya.bench/store-choice/arms/1", "base_args": BASE, "arms": rows,
           "unpredictability_U": u,
           "note": ("U=seed 1/2 の店別占有率(業態の中の訪問の割合)の差の絶対値の平均(Salganik 2006)。"
                    "初回率・店頭の割合は照合量(較正に使わない)。C1/C3/C4 には触れない。")}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                              newline="\n")
    return 0


def cmd_b5(args: argparse.Namespace) -> int:
    """B5 の店の項(v1.3): mock v3(選び手 nearest)と classical の店 on で、想起に載った店の項の数と行の tok。"""
    from shibuya import cli

    rows = {}
    for name, kw in (("mock_v3_store_on", {"vocab_version": "v3", "memory": "on", "store_memory": "on"}),
                     ("classical_store_on", {**BASE, "store_memory": "on"}),
                     ("classical_store_on_conversation_only", {**BASE, "store_memory": "on",
                                                               "store_recall_scope": "conversation"})):
        res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
        ms = res.run_manifest_fields()["memory_summary"]
        rc = ms["recall"]["counts"]
        rows[name] = {
            "final_hash": res.final_hash, "llm_calls": int(res.llm_calls),
            "recall": {k: v for k, v in ms["recall"].items() if k != "counts"},
            "recall_counts": {k: v for k, v in rc.items() if k.startswith(("recalled_kind:", "store_", "calls",
                                                                            "recalled_rows"))},
            "render": ms["render"],
        }
        print(name, res.final_hash[:8], rc.get("recalled_kind:store", 0), ms["render"]["line_tokens_max"], flush=True)
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/store-choice/b5/1", "rows": rows},
                                         ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="D-120 7c の計測")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("bytecheck", "bytecheck-one", "arms", "one", "b5"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        sp.add_argument("--out", required=name != "bytecheck-one")
        if name == "bytecheck":
            sp.add_argument("--head-src", required=True)
            sp.add_argument("--scratch", required=True)
        if name == "bytecheck-one":
            sp.add_argument("--config", required=True, choices=tuple(BYTE_CONFIGS))
            sp.add_argument("--tape", required=True)
        if name == "one":
            sp.add_argument("--arm", required=True, choices=tuple(ARMS))
        if name == "arms":
            sp.add_argument("--scratch", default="")
    args = ap.parse_args(argv)
    return {"bytecheck": cmd_bytecheck, "bytecheck-one": cmd_bytecheck_one, "arms": cmd_arms,
            "one": cmd_one, "b5": cmd_b5}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
