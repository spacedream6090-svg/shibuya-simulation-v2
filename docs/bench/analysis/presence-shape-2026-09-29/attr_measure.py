"""在圏の形 9b(KDDI 写像の感度腕・D-115 ③)+9a の小修正 2 件(Q117 (b)・Q119 (b))の計測。

使い方(リポジトリの根から)::

    D=docs/bench/analysis/presence-shape-2026-09-29
    python $D/attr_measure.py arms --scratch <作業用の場所> --out $D/attr_arms.json
    python $D/attr_measure.py bytecheck --head-src <HEAD e23df65 を git archive で展開した場所の src> \\
        --scratch <作業用の場所> --out $D/fix_byte_check.json

- ``arms``: mock v3 と classical を ``--exit-mode immediate`` / ``walk_to_platform`` で回し(5,000・seed 1)、
  体の journal(``tools/c7/attr_arms.py`` の ``AgentCellRecorder``=``resolve.apply`` を包んで毎 tick の ``cell`` を控える・
  ソース非改変)から 写像 3 × 滞在 0/30 × 20 歳未満 off/on の 12 腕の H2〜H5 を出す。既定腕(kind・滞在 0・
  20 歳未満を含む)がエンジンの在圏 journal と一致することを数で示す。実 LLM の c7-day-4 の在圏 journal が
  あれば、そこから出せる 2 腕(kind / kind_student_worker)も出す。
- ``bytecheck``: HEAD(9a のコミット)と作業木で同じラン(mock 5,000・seed 1)のテープを列ごとに突き合わせる。
  即時の退出(既定)は全構成で一致・walk_to_platform は歩き直しと運賃免除で動く(記録)。

KDDI 側は開封済みの記録(``docs/bench/c7/holdout/c7-day-4/c7_holdout_compare.json`` の obs)を**並べるだけ**
(判定しない)。絶対パスは書かない。壁時計は決定論でない。holdout の封印は開けない。
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
#: 実 LLM の c7-day-4(39 万体)の在圏 journal(s1 = data/runs・s2/s3 = サーバーからの回収)。比較記録の metrics は s1。
C7_DAY4_JOURNALS: dict[str, str] = {
    "s1": "data/runs/c7-day-4/occupancy.npz",
    "s2": "data/server_retrieval/2026-09-17/runs/c7-day-4-s2/occupancy.npz",
    "s3": "data/server_retrieval/2026-09-17/runs/c7-day-4-s3/occupancy.npz",
}
CLS = {"policy": "classical", "chooser": "classical"}
ARMS: dict[str, dict[str, Any]] = {
    "mock_immediate": {"vocab_version": "v3"},
    "mock_walk": {"vocab_version": "v3", "exit_mode": "walk_to_platform"},
    "classical_immediate": {"vocab_version": "v3", **CLS},
    "classical_walk": {"vocab_version": "v3", "exit_mode": "walk_to_platform", **CLS},
}
BYTE_CONFIGS: dict[str, dict[str, Any]] = {
    "v3_default": {"vocab_version": "v3"},
    "v3_leave_off": {"vocab_version": "v3", "leave_effect": False},
    "v3_classical": {"vocab_version": "v3", **CLS},
    "v1_default": {"vocab_version": "v1"},
    "v1_leave_off": {"vocab_version": "v1", "leave_effect": False},
    "v3_walk": {"vocab_version": "v3", "exit_mode": "walk_to_platform"},
    "v3_classical_walk": {"vocab_version": "v3", "exit_mode": "walk_to_platform", **CLS},
}
#: 既定(即時の退出)の構成=一致するはず。walk_to_platform の構成=動くはず(記録)。
EXPECT_EQUAL = ("v3_default", "v3_leave_off", "v3_classical", "v1_default", "v1_leave_off")


def _c7() -> Any:
    sys.path.insert(0, str(REPO / "tools" / "c7"))
    import attr_arms  # type: ignore[import-not-found]

    return attr_arms


def _h(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:16]


def _money(res: Any) -> dict[str, Any]:
    """金の保存の記録(``money_start == money_end + revenue_end + fares_paid``)と運賃の内訳。

    第302 Q119 (b): **計画の退出=運賃なし**。``fares_paid`` は LLM の乗車(``boarded_from_queue``)だけの運賃。
    """
    pc = dict(res.process_counters)
    return {"money_start": int(res.money_start), "money_end": int(res.money_end),
            "revenue_end": int(res.revenue_end), "fares_paid": int(res.fares_paid),
            "conserved": bool(res.conserved),
            "boarded_from_queue": pc.get("rail.boarded_from_queue"),
            "boarded_plan_exit": pc.get("rail.boarded_plan_exit")}


# ------------------------------------------------------------------ arms
def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli

    A = _c7()
    kw = ARMS[args.arm]
    scratch = Path(args.scratch)
    journal = scratch / f"journal_{args.arm}.npz"
    rec = A.AgentCellRecorder(every=1).attach()
    t0 = time.perf_counter()
    try:
        res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, occupancy_every=60,
                      occupancy_path=str(journal), **kw)
    finally:
        rec.detach()
    wall = time.perf_counter() - t0
    agent_journal = A.save_agent_journal(scratch / f"agent_journal_{args.arm}.npz", rec, n_agents=args.agents,
                                         seed=args.seed, tick_seconds=60, start_hour=0, arm=args.arm)
    amap, _gate = A.occ.build_map(args.world)
    area_of_cell = np.asarray(amap.area_of_cell, dtype=np.int64)
    obs = A.recorded_obs()
    j = A.load_agent_journal(agent_journal)
    pop = A.population_for(args.world, args.agents, args.seed)
    axes = A.agent_axes(pop, area_of_cell, kind=j["kind"])
    rows = A.arms_grid(j["ticks"], j["cells"], axes, area_of_cell, obs)
    # 既定腕(kind・滞在 0・20 歳未満を含む)= エンジンの在圏 journal と同じか
    base = A.area_attr_hour(j["ticks"], j["cells"], area_of_cell, A.attr_matrix(axes, "kind"))
    with np.load(journal, allow_pickle=False) as z:
        eng = A.kind_journal_table(np.asarray(z["ticks"]), np.asarray(z["kind_cell_counts"]), amap, "kind")
    # 舞台外(乗車中/域外)なのにセルを持つ体(正時の標本)=エンジンの journal も数えている(従来どおり)
    on = (j["ticks"] % 60) == 0
    cells_on, tr_on = j["cells"][on], j["transit"][on]
    area_on = A.cells_to_area(cells_on, area_of_cell)
    m = res.run_manifest_fields()
    print(json.dumps({
        "arm": args.arm, "args": kw, "final_hash": res.final_hash, "llm_calls": int(res.llm_calls),
        "conserved": bool(res.conserved), "money": _money(res), "presence_exit": m.get("presence_exit", {}),
        "rail": {k: v for k, v in dict(res.process_counters).items()
                 if k.startswith(("rail.board", "rail.boarded", "rail.fare", "rail.left_behind"))},
        "n_agents_registry": int(j["kind"].size), "n_ticks_recorded": int(j["ticks"].size),
        "default_arm_equals_engine_journal": bool(np.array_equal(base, eng)),
        "default_arm_max_abs_diff_vs_engine_journal": float(np.max(np.abs(base - eng))),
        "offstage_with_cell_on_hour": {
            "in_5_areas": int(((tr_on != 0) & (area_on >= 0)).sum()),
            "any_cell": int(((tr_on != 0) & (cells_on >= 0)).sum()),
            "note": "transit_state != 0 でセルを持つ体の延べ数(24 標本)=従来の journal も在圏に数える"},
        "axes": {"n": int(axes.kind.size),
                 "home_in_5_areas": int((axes.home_area >= 0).sum()),
                 "work_in_5_areas": int((axes.work_area >= 0).sum()),
                 "school_in_5_areas": int((axes.school_area >= 0).sum()),
                 "under20": int((axes.age < A.UNDER20_AGE).sum())},
        "rows": rows,
        "wall_seconds_nondeterministic": round(wall, 2),
    }, ensure_ascii=False, default=str))
    return 0


def cmd_arms(args: argparse.Namespace) -> int:
    A = _c7()
    out: dict[str, Any] = {
        "schema": "shibuya.bench/presence-shape/attr-arms/1",
        "declared": {
            "dwell_0": "毎正時の標本(従来の journal と同じ)",
            "dwell_30": "時間帯(その 1 時間)の中で同じエリアに連続 30 tick(=30 分)以上居た体を 1 と数える",
            "area_axes": "W16 の home_cell / work_cell / school_cell を 5 エリア写像で判定・5 エリア外は −1",
            "obs": "c7-day-4 の開封済み比較記録(H2 ピーク時刻・H3 深夜残存率・H4 エリア構成・H5 属性構成)",
            "H1": "obs の時刻シェアが記録に無い=空欄(封印は開けない)",
            "floor": "PT 2018 の日中ピーク 所属なし/勤務通学 0.16(業務を足して 0.27)vs KDDI 1.66(sub_e §2-3)",
        },
        "runs": [],
    }
    for name in ARMS:
        cmd = [sys.executable, str(Path(__file__)), "one", "--arm", name, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed), "--scratch", args.scratch]
        got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        row = json.loads(got.stdout.strip().splitlines()[-1])
        out["runs"].append(row)
        print(name, row["final_hash"][:8], row["llm_calls"], "default==engine", row["default_arm_equals_engine_journal"],
              row["wall_seconds_nondeterministic"], flush=True)
    amap, _gate = A.occ.build_map(args.world)
    out["c7_day_4"] = {}
    for seed, rel in C7_DAY4_JOURNALS.items():
        path = REPO / rel
        out["c7_day_4"][seed] = ({"journal": rel, "present": True, **A.kind_journal_rows(path, amap, A.recorded_obs())}
                                 if path.exists() else {"journal": rel, "present": False})
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ bytecheck
def cmd_bytecheck_one(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from shibuya import cli

    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape,
                  **BYTE_CONFIGS[args.config])
    calls = pq.read_table(Path(args.tape) / "calls.parquet")
    blocks = pq.read_table(Path(args.tape) / "blocks.parquet")
    m = res.run_manifest_fields()
    print(json.dumps({
        "config": args.config, "final": res.final_hash[:16], "calls": int(res.llm_calls),
        "blocks_rows": int(blocks.num_rows),
        "blocks_sha": _h({n: blocks.column(n).to_pylist() for n in blocks.column_names}),
        "calls_columns_sha": {n: _h(calls.column(n).to_pylist()) for n in calls.column_names},
        "presence_exit": m.get("presence_exit", {}),
        "money": _money(res),
        "rail": {k: v for k, v in dict(res.process_counters).items()
                 if k.startswith(("rail.board", "rail.boarded", "rail.fare"))},
    }, ensure_ascii=False, default=str))
    return 0


def cmd_bytecheck(args: argparse.Namespace) -> int:
    scratch = Path(args.scratch)
    got: dict[str, dict[str, Any]] = {"head": {}, "work": {}}
    for name in BYTE_CONFIGS:
        for side, src in (("head", args.head_src), ("work", "")):
            env = dict(os.environ)
            if src:
                env["PYTHONPATH"] = src
                env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"
            cmd = [sys.executable, str(Path(__file__)), "bytecheck-one", "--config", name, "--world", args.world,
                   "--agents", str(args.agents), "--seed", str(args.seed), "--tape", str(scratch / f"{side}_{name}")]
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True, env=env)
            got[side][name] = json.loads(r.stdout.strip().splitlines()[-1])
    runs = []
    for name in BYTE_CONFIGS:
        h, w = got["head"][name], got["work"][name]
        diff = sorted(k for k in h["calls_columns_sha"] if h["calls_columns_sha"][k] != w["calls_columns_sha"][k])
        row = {"run": name, "expect_equal": name in EXPECT_EQUAL, "head": h, "work": w,
               "final_equal": h["final"] == w["final"], "calls_equal": h["calls"] == w["calls"],
               "blocks_equal": (h["blocks_sha"], h["blocks_rows"]) == (w["blocks_sha"], w["blocks_rows"]),
               "calls_columns_differ": diff}
        runs.append(row)
        print(name, {k: v for k, v in row.items() if k.endswith(("equal", "differ"))}, flush=True)
    doc = {"schema": "shibuya.bench/presence-shape/fix-byte-check/1", "head": args.head_label,
           "how": ("same runs (mock 5,000, seed 1, energy) with the committed source (git archive) and the working "
                   "tree; tape = blocks and the call columns. Immediate exit (default) configs are expected equal; "
                   "walk_to_platform configs move by the rewalk (Q117 (b)) and the fare exemption (Q119 (b))."),
           "runs": runs}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="在圏の形 9b の計測")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("arms", "one", "bytecheck", "bytecheck-one"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        if name in ("arms", "bytecheck"):
            sp.add_argument("--out", required=True)
        if name in ("arms", "one", "bytecheck"):
            sp.add_argument("--scratch", required=True)
        if name == "one":
            sp.add_argument("--arm", required=True, choices=tuple(ARMS))
        if name == "bytecheck":
            sp.add_argument("--head-src", required=True)
            sp.add_argument("--head-label", default="e23df65")
        if name == "bytecheck-one":
            sp.add_argument("--config", required=True, choices=tuple(BYTE_CONFIGS))
            sp.add_argument("--tape", required=True)
    args = ap.parse_args(argv)
    return {"arms": cmd_arms, "one": cmd_one, "bytecheck": cmd_bytecheck,
            "bytecheck-one": cmd_bytecheck_one}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
