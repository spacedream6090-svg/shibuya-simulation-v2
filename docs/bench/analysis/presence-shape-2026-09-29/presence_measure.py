"""在圏の形 9a(退出を歩かせる D-115 ①+退去の効果 D-112 ④)の計測。

使い方(リポジトリの根から)::

    D=docs/bench/analysis/presence-shape-2026-09-29
    python $D/presence_measure.py arms15 --out $D/arms15_leave.json       # 15 腕: 退去の効果 on/off と欄ごとの差
    python $D/presence_measure.py bytecheck --head-src <HEAD e784f65 の src と docs/bench/anchors を展開した場所の src> \\
        --scratch <作業用の場所> --out $D/leave_byte_check.json          # 退去を選ばない構成・切替口 off の byte 一致
    python $D/presence_measure.py arms --scratch <作業用の場所> --out $D/exit_arms.json   # immediate / walk_to_platform

- ``arms15``: 15 腕(W6 再生成の計測の ``ARMS``)を ``leave_effect`` on(既定)と off で回す。off の final と呼数が
  5 段目の記録と一致すること(=動いたのは退去の効果だけ)と、on/off の終わりの SoA を欄ごとにハッシュして
  どの欄が動いたかを書く。
- ``bytecheck``: HEAD の git archive と作業木で同じラン(mock 5,000・seed 1)のテープを列ごとに突き合わせる。
  classical(退去を選ばない)と ``--leave-effect off`` は一致・mock の既定は動く(記録)。
- ``arms``: mock v3 と classical を ``--exit-mode immediate``/``walk_to_platform`` で回し、在圏 journal(毎正時)から
  5 エリアの時別在圏・central の形(ピーク時刻・深夜残存率)を出す。KDDI との比較は開封済みの記録
  (``docs/bench/c7/holdout/c7-day-4/c7_holdout_compare.json`` の obs のピーク時刻・深夜残存率)を**並べるだけ**
  (判定しない=事前登録 v2 で)。

絶対パスは書かない。壁時計は決定論でない。holdout の封印は開けない。
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
REPO = HERE.parents[3]
W6 = HERE.parent / "w6-regen-2026-09-28" / "w6_regen_measure.py"
BEFORE = HERE.parent / "energy-classical-2026-09-28" / "arms15_energy.json"
HOLDOUT_RECORD = REPO / "docs" / "bench" / "c7" / "holdout" / "c7-day-4" / "c7_holdout_compare.json"
CLS = {"policy": "classical", "chooser": "classical"}
BYTE_CONFIGS: dict[str, dict[str, Any]] = {
    "v3_default": {"vocab_version": "v3"},
    "v3_leave_off": {"vocab_version": "v3", "leave_effect": False},
    "v3_classical": {"vocab_version": "v3", **CLS},
    "v1_default": {"vocab_version": "v1"},
    "v1_leave_off": {"vocab_version": "v1", "leave_effect": False},
}
#: 作業木の構成 → HEAD の比較先(HEAD には ``leave_effect`` の口が無い=既定の構成と比べる)。
HEAD_OF = {"v3_leave_off": "v3_default", "v1_leave_off": "v1_default"}
EXIT_ARMS: dict[str, dict[str, Any]] = {
    "mock_immediate": {"vocab_version": "v3"},
    "mock_walk": {"vocab_version": "v3", "exit_mode": "walk_to_platform"},
    "mock_walk_leave_off": {"vocab_version": "v3", "exit_mode": "walk_to_platform", "leave_effect": False},
    "mock_walk_max30": {"vocab_version": "v3", "exit_mode": "walk_to_platform", "intent_max_ticks": 30},
    "classical_immediate": {"vocab_version": "v3", **CLS},
    "classical_walk": {"vocab_version": "v3", "exit_mode": "walk_to_platform", **CLS},
}


def _h(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:16]


def _w6() -> Any:
    import importlib.util

    spec = importlib.util.spec_from_file_location("w6_regen_measure", W6)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _field_hashes(res: Any) -> dict[str, str]:
    reg = res.agents.registry
    return {name: hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()[:16]
            for name, arr in sorted(reg.arrays.items())}


# ------------------------------------------------------------------ arms15
def cmd_arms15(args: argparse.Namespace) -> int:
    from shibuya import cli

    w6 = _w6()
    before = {r["arm"]: (r["final_hash"], r["llm_calls"])
              for r in json.loads(BEFORE.read_text(encoding="utf-8"))["arms"]}
    rows = []
    for name, kw in w6.ARMS.items():
        got = {}
        for side, le in (("on", True), ("off", False)):
            res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, leave_effect=le, **kw)
            calls = int(res.column("calls").sum()) if res.diagnostics.size else 0
            got[side] = {"final": res.final_hash, "llm_calls": calls, "fields": _field_hashes(res),
                         "leave_effects": res.run_manifest_fields().get("leave_effects", {}),
                         "closed_退去": int(dict(res.conversation_counters).get("closed_退去", 0))}
        on, off = got["on"], got["off"]
        diff = sorted(k for k in on["fields"] if on["fields"][k] != off["fields"].get(k))
        row = {"arm": name, "final_5th_stage": before.get(name, ("", 0))[0],
               "off_final": off["final"], "off_llm_calls": off["llm_calls"],
               "off_equals_5th_stage": (off["final"], off["llm_calls"]) == before.get(name),
               "on_final": on["final"], "on_llm_calls": on["llm_calls"],
               "on_changed": on["final"] != off["final"], "fields_changed_by_leave_effect": diff,
               "leave_effects": on["leave_effects"], "closed_退去_on": on["closed_退去"],
               "closed_退去_off": off["closed_退去"]}
        rows.append(row)
        print(f"{name}: off {off['final'][:8]} {'=' if row['off_equals_5th_stage'] else '≠'} 5th / on {on['final'][:8]} "
              f"calls {off['llm_calls']:,}→{on['llm_calls']:,} fields {diff}", flush=True)
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/presence-shape/arms15-leave/1", "arms": rows},
                                         ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ bytecheck
def cmd_bytecheck_one(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from shibuya import cli

    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape,
                  **BYTE_CONFIGS[args.config])
    calls = pq.read_table(Path(args.tape) / "calls.parquet")
    blocks = pq.read_table(Path(args.tape) / "blocks.parquet")
    print(json.dumps({
        "config": args.config, "final": res.final_hash[:16], "calls": int(res.llm_calls),
        "blocks_rows": int(blocks.num_rows),
        "blocks_sha": _h({n: blocks.column(n).to_pylist() for n in blocks.column_names}),
        "calls_columns_sha": {n: _h(calls.column(n).to_pylist()) for n in calls.column_names},
    }, ensure_ascii=False))
    return 0


def cmd_bytecheck(args: argparse.Namespace) -> int:
    runs = []
    scratch = Path(args.scratch)
    head: dict[str, Any] = {}
    work: dict[str, Any] = {}
    for name in BYTE_CONFIGS:
        for side, src in (("head", args.head_src), ("work", "")):
            if src and name in HEAD_OF:
                continue  # HEAD には切替口が無い
            env = dict(os.environ)
            if src:
                env["PYTHONPATH"] = src
                env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"
            cmd = [sys.executable, str(Path(__file__)), "bytecheck-one", "--config", name, "--world", args.world,
                   "--agents", str(args.agents), "--seed", str(args.seed), "--tape", str(scratch / f"{side}_{name}")]
            got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True, env=env)
            (head if side == "head" else work)[name] = json.loads(got.stdout.strip().splitlines()[-1])
    for name, w in work.items():
        h = head[HEAD_OF.get(name, name)]
        diff = sorted(k for k in h["calls_columns_sha"] if h["calls_columns_sha"][k] != w["calls_columns_sha"][k])
        row = {"run": name, "compare_to_head": HEAD_OF.get(name, name), "head": h, "work": w,
               "final_equal": h["final"] == w["final"], "calls_equal": h["calls"] == w["calls"],
               "blocks_equal": (h["blocks_sha"], h["blocks_rows"]) == (w["blocks_sha"], w["blocks_rows"]),
               "calls_columns_differ": diff}
        runs.append(row)
        print(name, {k: v for k, v in row.items() if k.endswith(("equal", "differ"))}, flush=True)
    doc = {"schema": "shibuya.bench/presence-shape/byte-check/1", "head": args.head_label,
           "how": ("same runs (mock 5,000, seed 1, energy) with the committed source (git archive) and the working "
                   "tree; tape = blocks and the 14 call columns. *_leave_off runs (only in the working tree) are "
                   "compared to HEAD's default run of the same vocabulary."),
           "runs": runs}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ exit arms
def _area_shapes(journal: Path, world: str) -> dict[str, Any]:
    sys.path.insert(0, str(REPO / "tools" / "c7"))
    import c7lib  # type: ignore[import-not-found]
    import occupancy_series as occ  # type: ignore[import-not-found]

    amap, _gate = occ.build_map(world)
    series = occ.load_journal(journal, amap)
    table = series.area_hour_table(amap)  # (24, 5)
    share = c7lib.hour_share(table)       # (5, 24)
    peaks = c7lib.peak_hours(share)
    night = c7lib.night_residual(share)
    rec = json.loads(HOLDOUT_RECORD.read_text(encoding="utf-8"))["metrics"] if HOLDOUT_RECORD.exists() else {}
    obs_peak = rec.get("H2", {}).get("obs_peak_hour", {})
    obs_night = rec.get("H3", {}).get("obs_night_residual", {})
    areas = list(c7lib.AREA_IDS)
    return {
        "area_hour_counts": {a: [round(float(v), 1) for v in table[:, i]] for i, a in enumerate(areas)},
        "central_hour_share": [round(float(v), 5) for v in share[areas.index("central")]],
        "sim_peak_hour": {a: int(peaks[i]) for i, a in enumerate(areas)},
        "sim_night_residual": {a: round(float(night[i]), 4) for i, a in enumerate(areas)},
        "recorded_obs_peak_hour_c7_day_4": obs_peak,
        "recorded_obs_night_residual_c7_day_4": obs_night,
        "note": "検証の記録=開封済みの obs(c7-day-4 の比較 JSON)を並べるだけ・判定しない",
    }


def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli

    kw = EXIT_ARMS[args.arm]
    journal = Path(args.scratch) / f"journal_{args.arm}.npz"
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, occupancy_every=60,
                  occupancy_path=str(journal), **kw)
    wall = time.perf_counter() - t0
    m = res.run_manifest_fields()
    cc = dict(res.conversation_counters)
    pc = dict(res.presence_counters)
    print(json.dumps({
        "arm": args.arm, "args": kw, "final_hash": res.final_hash, "llm_calls": int(res.llm_calls),
        "conserved": bool(res.conserved), "calls_by_condition": m.get("calls_by_condition", {}),
        "presence_exit": m.get("presence_exit", {}), "leave_effects": m.get("leave_effects", {}),
        "presence": {k: pc.get(k) for k in ("departures", "arrivals", "exit_deferred", "exit_forced", "plan_stranded_eod",
                                            "plan_match_in", "plan_match_out", "departed_by_llm", "in_area_03",
                                            "in_area_09", "in_area_12", "day_night_ratio_09_03")},
        "rail": {k: v for k, v in dict(res.process_counters).items()
                 if k.startswith(("rail.board", "rail.boarded", "rail.fare", "rail.left_behind", "rail.departed",
                                  "rail.return"))},
        "conversation_closed": {k: v for k, v in cc.items() if k.startswith("closed_")},
        "shapes": _area_shapes(journal, args.world),
        "wall_seconds_nondeterministic": round(wall, 2),
        "presence_phase_seconds_nondeterministic": round(float(res.phase_seconds.get("presence", 0.0)), 3),
    }, ensure_ascii=False, default=str))
    return 0


def cmd_arms(args: argparse.Namespace) -> int:
    rows = []
    for name in EXIT_ARMS:
        cmd = [sys.executable, str(Path(__file__)), "one", "--arm", name, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed), "--scratch", args.scratch]
        got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        row = json.loads(got.stdout.strip().splitlines()[-1])
        rows.append(row)
        ex = row["presence_exit"]
        print(name, row["final_hash"][:8], row["llm_calls"], ex.get("walk_started"), ex.get("walk_boarded"),
              row["shapes"]["sim_peak_hour"], row["wall_seconds_nondeterministic"], flush=True)
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/presence-shape/exit-arms/1", "rows": rows},
                                         ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="在圏の形 9a の計測")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("arms15", "bytecheck", "bytecheck-one", "arms", "one"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        if name not in ("bytecheck-one", "one"):
            sp.add_argument("--out", required=True)
        if name == "bytecheck":
            sp.add_argument("--head-src", required=True)
            sp.add_argument("--head-label", default="e784f65")
            sp.add_argument("--scratch", required=True)
        if name == "bytecheck-one":
            sp.add_argument("--config", required=True, choices=tuple(BYTE_CONFIGS))
            sp.add_argument("--tape", required=True)
        if name in ("arms", "one"):
            sp.add_argument("--scratch", required=True)
        if name == "one":
            sp.add_argument("--arm", required=True, choices=tuple(EXIT_ARMS))
    args = ap.parse_args(argv)
    return {"arms15": cmd_arms15, "bytecheck": cmd_bytecheck, "bytecheck-one": cmd_bytecheck_one,
            "arms": cmd_arms, "one": cmd_one}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
