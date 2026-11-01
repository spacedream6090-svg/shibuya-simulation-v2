"""第 6 期 6-5 記憶 MR の腕の測り(腕ごとの動いた量・性能・粒度の見積り・M1 と M0 の上位 k の比べ)。記録を出すだけ。

エンジンは変えない(M1 と M0 の比べは器の想起を包んで M0 の式でもう 1 回並べる=計数は戻す=ランを変えない)。

段(リポの根で・``PYTHONPATH`` に作業木の ``src``・``$W`` は作業用の置き場):

    python $D/arms_mr65.py side --configs v3_mem_store,v3_mem_rel,v3_classical_mem_rel,w6_v3_default \\
        --arms base,m1,embed,people,grain --scratch $W --out $W/arms_side.json --jobs 5
    python $D/arms_mr65.py compare --side $W/arms_side.json --base base --out $D/arms_moved.json
    python $D/arms_mr65.py side --configs v3_mem_rel --arms base,grain --days 2 --scratch $W --out $W/grain2.json
    python $D/arms_mr65.py estimate --side $W/grain2.json --out $D/grain_estimate.json

腕(``ARMS``=環境変数): ``default``=器なし(今の既定)・``base``=器 M0(``--memory-store events``・6-5 の腕は既定)・
``m1``・``embed``(``ngram-test``=試験用の代わり)・``people``(m1+人も記憶)・``grain``(粒度 day)。構成は byte-check の
``wave2_bytecheck.configs()``(5,000 体・seed 1・テープつき)。``one`` は byte-check の 25 欄のうち比べに使う欄と、manifest の
``memory_summary.memory_store``(``mr65`` を含む)・日ごとの出来事の記録の行・関係の要約の一部・壁時計を出す。

〔検収 L2〕``compare`` は M1 と M0 の上位 k の一致を「両方とも空」の想起を含む率と除いた率の両方で出す(``topk_shares``)。
〔検収 L6〕記憶 off の構成(``w6_v3_default`` など)に 6-5 の腕を立てると組み立てで止まる(前は何もしない=黙って効かない
ランだった)=腕の比べは記憶 on の構成で回す。

絶対パスは JSON に書かない。逐次ループ宣言: 構成 × 腕の数ぶん(子のプロセス)。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
WAVE2 = REPO / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"

ARMS: dict[str, dict[str, str]] = {
    "default": {},
    "base": {"SHIBUYA_MEMORY_STORE": "events"},
    "m1": {"SHIBUYA_MEMORY_STORE": "events", "SHIBUYA_MEMORY_MODEL": "m1"},
    "embed": {"SHIBUYA_MEMORY_STORE": "events", "SHIBUYA_MEMORY_CUE": "embed", "SHIBUYA_MEMORY_EMBED_MODEL": "ngram-test"},
    "people": {"SHIBUYA_MEMORY_STORE": "events", "SHIBUYA_MEMORY_MODEL": "m1", "SHIBUYA_MEMORY_PEOPLE": "memory"},
    "grain": {"SHIBUYA_MEMORY_STORE": "events", "SHIBUYA_MEMORY_GRAIN": "day"},
}
_ARM_VARS = ("SHIBUYA_MEMORY_STORE", "SHIBUYA_MEMORY_MODEL", "SHIBUYA_MEMORY_CUE", "SHIBUYA_MEMORY_EMBED_MODEL",
             "SHIBUYA_MEMORY_PEOPLE", "SHIBUYA_MEMORY_GRAIN")
#: 比べる欄(byte-check の欄の部分集合+テープの列ごとの sha)。
KEYS = ("final", "calls", "blocks_sha", "calls_column_names", "action_usage_sha", "behavior_last", "full_last",
        "salient_events", "noticed", "meals")


def _wave2() -> Any:
    spec = importlib.util.spec_from_file_location("wave2_bytecheck", WAVE2)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _h(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, default=str, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def _topk(tally: Counter) -> None:
    """器の想起を包み、M1 の腕なら同じ行を M0 の式でも並べて上位 k を比べる(計数を戻す=ランは変わらない)。"""
    from shibuya.engine.memory_store import MemoryStore

    orig = MemoryStore.recall

    def recall(self, agent, t_ns, k, **kw):  # noqa: ANN001
        got = orig(self, agent, t_ns, k, **kw)
        if self.m1 is None:
            return got
        last, stats = self._ms_last, Counter(self._ms_stats)
        m1 = self.m1
        object.__setattr__(self, "m1", None)
        try:
            m0 = orig(self, agent, t_ns, k, **kw)
        finally:
            object.__setattr__(self, "m1", m1)
            object.__setattr__(self, "_ms_last", last)
            self._ms_stats.clear()
            self._ms_stats.update(stats)
        a = [(v.row, v.kind) for v in got]
        b = [(v.row, v.kind) for v in m0]
        tally["calls"] += 1
        tally["same_order"] += int(a == b)
        tally["same_set"] += int(set(a) == set(b))
        tally["m1_fewer"] += int(len(a) < len(b))
        tally["m1_more"] += int(len(a) > len(b))
        tally["both_empty"] += int(not a and not b)
        tally["overlap_items"] += len(set(a) & set(b))
        tally["m1_items"] += len(a)
        tally["m0_items"] += len(b)
        return got

    MemoryStore.recall = recall  # type: ignore[assignment]


def cmd_one(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from shibuya import cli

    w2 = _wave2()
    kw = dict(w2.configs()[args.config])
    if int(args.days) > 1:
        kw["sim_days"] = int(args.days)
    tally: Counter = Counter()
    if args.topk:
        _topk(tally)
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape, **kw)
    wall = time.perf_counter() - t0
    calls = pq.read_table(Path(args.tape) / "calls.parquet")
    blocks = pq.read_table(Path(args.tape) / "blocks.parquet")
    man = res.run_manifest_fields()
    last = res.checkpoints[-1] if res.checkpoints else None
    au = {str(k): int(v) for k, v in dict(getattr(res, "action_usage", {}) or {}).items()}
    ms = (man.get("memory_summary") or {}).get("memory_store")
    rel = man.get("relations") or {}
    days = [{"rows": int((d.get("events") or {}).get("rows", 0)), "bytes": int((d.get("events") or {}).get("bytes", 0)),
             "live_rows": int((d.get("events") or {}).get("live_rows", 0)),
             "by_cause": (d.get("events") or {}).get("by_cause", {})} for d in (man.get("daily") or [])]
    steps = int(kw.get("ticks", 1440)) * int(kw.get("sim_days", 1))
    print(json.dumps({
        "config": args.config, "arm_env": {k: os.environ[k] for k in _ARM_VARS if k in os.environ},
        "final": res.final_hash[:16], "calls": int(res.llm_calls),
        "blocks_sha": _h({n: blocks.column(n).to_pylist() for n in blocks.column_names}),
        "calls_column_names": list(calls.column_names),
        "calls_columns_sha": {n: _h(calls.column(n).to_pylist()) for n in calls.column_names},
        "action_usage_sha": _h(au), "salient_events": int(getattr(res, "salient_events", 0)),
        "noticed": int(getattr(res, "noticed", 0)), "meals": int(getattr(res, "meals", 0)),
        "behavior_last": getattr(last, "behavior_hash", "") if last is not None else "",
        "full_last": getattr(last, "full_hash", "") if last is not None else "",
        "memory_store": ms, "events_days": days,
        "relations": {k: rel.get(k) for k in ("edges_live_total", "agents_with_edges", "kinds", "dunbar_layers",
                                               "edges_live_per_agent")} if rel else {},
        "recall": ((man.get("memory_summary") or {}).get("recall") or {}).get("counts", {}),
        "topk_m1_vs_m0": dict(tally),
        "wall_s": round(wall, 2), "steps": steps, "wall_ms_per_step": round(1000.0 * wall / max(1, steps), 3),
    }, ensure_ascii=False))
    return 0


def cmd_side(args: argparse.Namespace) -> int:
    scratch = Path(args.scratch)
    jobs = [(c, a) for a in args.arms.split(",") for c in args.configs.split(",") if c and a]

    def one(job: tuple[str, str]) -> dict[str, Any]:
        cfg, arm = job
        env = {k: v for k, v in os.environ.items() if k not in _ARM_VARS}
        env.update(ARMS[arm])
        env["PYTHONIOENCODING"] = "utf-8"
        cmd = [sys.executable, str(Path(__file__)), "one", "--config", cfg, "--world", args.world, "--agents",
               str(args.agents), "--seed", str(args.seed), "--days", str(args.days),
               "--tape", str(scratch / f"mr65_{arm}_{cfg}_d{args.days}")] + (["--topk"] if args.topk else [])
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            return {"config": cfg, "arm": arm, "error": r.stderr[-3000:]}
        row = json.loads(r.stdout.strip().splitlines()[-1])
        row["arm"] = arm
        return row

    got: dict[str, dict[str, Any]] = {}
    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        for row in ex.map(one, jobs):
            got.setdefault(row["arm"], {})[row["config"]] = row
            print(row["arm"], row["config"], row.get("final"), row.get("calls"), row.get("wall_s"),
                  (row.get("error") or "")[-300:], flush=True)
    doc = {"agents": args.agents, "seed": args.seed, "days": args.days, "runs": got}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def topk_shares(t: dict[str, int]) -> dict[str, float | None]:
    """〔検収 L2〕上位 k の一致の率(両方とも空の想起を含む率と除いた率)。"""
    calls, both = int(t.get("calls", 0)), int(t.get("both_empty", 0))
    if calls == 0:
        return {}
    rest = calls - both

    def share(k: str, *, drop_both: bool) -> float | None:
        v = int(t.get(k, 0))
        if drop_both:
            return round((v - both) / rest, 4) if rest > 0 else None
        return round(v / calls, 4)

    return {"same_order": share("same_order", drop_both=False),
            "same_order_excluding_both_empty": share("same_order", drop_both=True),
            "same_set": share("same_set", drop_both=False),
            "same_set_excluding_both_empty": share("same_set", drop_both=True),
            "both_empty": both, "calls": calls,
            "overlap_items_of_m0_items": (round(int(t.get("overlap_items", 0)) / int(t["m0_items"]), 4)
                                          if int(t.get("m0_items", 0)) else None)}


def cmd_compare(args: argparse.Namespace) -> int:
    doc = json.loads(Path(args.side).read_text(encoding="utf-8"))
    base = doc["runs"][args.base]
    out: dict[str, Any] = {"base": args.base, "agents": doc["agents"], "days": doc["days"], "arms": {}}
    for arm, rows in doc["runs"].items():
        if arm == args.base:
            continue
        per: dict[str, Any] = {}
        for cfg, rb in rows.items():
            ra = base.get(cfg, {})
            if "error" in ra or "error" in rb:
                per[cfg] = {"error": (rb.get("error") or ra.get("error") or "")[-300:]}
                continue
            moved = [k for k in KEYS if ra.get(k) != rb.get(k)]
            cols = sorted(set(ra["calls_columns_sha"]) | set(rb["calls_columns_sha"]))
            moved_cols = [c for c in cols if ra["calls_columns_sha"].get(c) != rb["calls_columns_sha"].get(c)]
            per[cfg] = {"moved": moved, "moved_tape_columns": moved_cols, "calls_delta": rb["calls"] - ra["calls"],
                        "final": [ra["final"], rb["final"]],
                        "events_rows": [sum(d["rows"] for d in ra["events_days"]),
                                        sum(d["rows"] for d in rb["events_days"])],
                        "wall_ms_per_step": [ra["wall_ms_per_step"], rb["wall_ms_per_step"]],
                        "mr65": (rb.get("memory_store") or {}).get("mr65"),
                        "topk_m1_vs_m0": rb.get("topk_m1_vs_m0") or {},
                        "topk_shares": topk_shares(rb.get("topk_m1_vs_m0") or {}),
                        "relations": [ra.get("relations"), rb.get("relations")]}
        out["arms"][arm] = per
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    for arm, per in out["arms"].items():
        for cfg, r in per.items():
            print(arm, cfg, r.get("moved"), r.get("moved_tape_columns"), r.get("calls_delta"))
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    """2 日の通しと、1 日目の終わり(日の境目)で保存 → 2 日目を再開の final・checkpoint を比べる(腕は環境変数=子で選ぶ)。"""
    from shibuya import cli
    from shibuya.core.time_consts import STEPS_PER_DAY

    w2 = _wave2()
    tpd = int(STEPS_PER_DAY)
    kw = dict(w2.configs()[args.config], n_agents=args.agents, seed=args.seed, sim_days=2, world_dir=args.world)
    base = Path(args.scratch) / f"resume_mr65_{args.config}"
    base.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    straight = cli.run(**kw)
    a = cli.run(**kw, state_out=str(base / "a"), stop_at_tick=tpd)
    sf = [f for f in a.resume["state_files"] if int(f.get("T", -1)) == tpd] or a.resume["state_files"][-1:]
    b = cli.run(**kw, resume_from=str(base / "a" / sf[-1]["file"]))
    cp = lambda r: [(int(c.tick), str(c.behavior_hash)[:16], str(c.full_hash)[:16])  # noqa: E731
                    for c in r.checkpoints if int(c.tick) >= tpd]
    doc = {"config": args.config, "arm_env": {k: os.environ[k] for k in _ARM_VARS if k in os.environ},
           "agents": args.agents, "seed": args.seed, "straight_final": str(straight.final_hash)[:16],
           "resumed_final": str(b.final_hash)[:16], "same_final": straight.final_hash == b.final_hash,
           "checkpoints_after_boundary_same": cp(straight) == cp(b), "n_checkpoints_compared": len(cp(b)),
           "calls": [int(straight.llm_calls), int(a.llm_calls) + int(b.llm_calls)],
           "wall_s_nondeterministic": round(time.perf_counter() - t0, 1)}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc, ensure_ascii=False))
    return 0 if doc["same_final"] and doc["checkpoints_after_boundary_same"] else 1


#: 39 万体(W16 の母集団の全員=390,067・relations.py の注)。
N_FULL = 390_067


def cmd_estimate(args: argparse.Namespace) -> int:
    """粒度の腕の見積り: 体あたり 1 日の出来事の行(と原因の表の行)→ 39 万体・保持窓 7 日のバイト(推測=線形の外挿)。"""
    from shibuya.engine.events.log import CAUSE_ROW_BYTES, RETENTION_DAYS, ROW_BYTES

    doc = json.loads(Path(args.side).read_text(encoding="utf-8"))
    world: list[dict[str, Any]] = []
    if args.world_run:  # 器の無い既定のランの日ごとの行(世界過程と区切り)=引いて体の出来事だけにする
        world = json.loads(Path(args.world_run).read_text(encoding="utf-8").strip().splitlines()[-1])["events_days"]
    out: dict[str, Any] = {"agents": doc["agents"], "days": doc["days"], "row_bytes": ROW_BYTES,
                           "cause_row_bytes": CAUSE_ROW_BYTES, "retention_days": RETENTION_DAYS, "n_full": N_FULL,
                           "declared_cap_bytes": 256 * 1024 * 1024, "world_rows_subtracted": bool(world),
                           "arms": {}}
    for arm, rows in doc["runs"].items():
        for cfg, r in rows.items():
            if "error" in r:
                continue
            ds = r["events_days"]
            rows_day = [d["rows"] - (world[j]["rows"] if world else 0) for j, d in enumerate(ds)]
            llm = [int(d["by_cause"].get("llm_call", 0)) - (int(world[j]["by_cause"].get("llm_call", 0)) if world else 0)
                   for j, d in enumerate(ds)]
            per_agent_day = sum(rows_day) / max(1, len(ds)) / doc["agents"]
            llm_share = sum(llm) / max(1, sum(rows_day))
            bytes_agent_day = per_agent_day * (ROW_BYTES + llm_share * CAUSE_ROW_BYTES)
            full7 = bytes_agent_day * N_FULL * RETENTION_DAYS
            out["arms"].setdefault(arm, {})[cfg] = {
                "rows_per_day": rows_day, "rows_per_agent_day": round(per_agent_day, 3),
                "llm_cause_share": round(llm_share, 4), "bytes_per_agent_day": round(bytes_agent_day, 1),
                "full_7d_bytes_estimate": int(full7), "full_7d_gib_estimate": round(full7 / 2**30, 3),
                "over_declared_cap": full7 > 256 * 1024 * 1024,
            }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out["arms"], ensure_ascii=False, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("one", "side"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        sp.add_argument("--days", type=int, default=1)
        sp.add_argument("--topk", action="store_true")
        if name == "one":
            sp.add_argument("--config", required=True)
            sp.add_argument("--tape", required=True)
        else:
            sp.add_argument("--configs", required=True)
            sp.add_argument("--arms", required=True)
            sp.add_argument("--scratch", required=True)
            sp.add_argument("--out", required=True)
            sp.add_argument("--jobs", type=int, default=4)
    sp = sub.add_parser("compare")
    sp.add_argument("--side", required=True)
    sp.add_argument("--base", default="base")
    sp.add_argument("--out", required=True)
    sp = sub.add_parser("estimate")
    sp.add_argument("--side", required=True)
    sp.add_argument("--world-run", default="", help="器の無い既定のランの one の出力(引けば体の出来事だけ)")
    sp.add_argument("--out", required=True)
    sp = sub.add_parser("resume")
    sp.add_argument("--config", default="v3_mem_rel")
    sp.add_argument("--world", default="data/world/v2")
    sp.add_argument("--agents", type=int, default=5_000)
    sp.add_argument("--seed", type=int, default=1)
    sp.add_argument("--scratch", required=True)
    sp.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side, "compare": cmd_compare, "estimate": cmd_estimate,
            "resume": cmd_resume}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
