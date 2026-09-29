"""W6 再生成(段 1a・第281)の checkpoint 張り直しの計測手順(mock 5,000 体・seed 1・1 シミュ日)。

使い方(リポジトリの根から)::

    # 腕を回す(腕ごとに <out>/<腕>.checkpoints.json と <out>/<腕>.summary.json を書く)
    python docs/bench/analysis/w6-regen-2026-09-28/w6_regen_measure.py run \\
        --world data/world/v2 --out <出力先> [--only 腕,腕]
    # 腕ごとの要約を <out>/summary.json に束ねる
    python docs/bench/analysis/w6-regen-2026-09-28/w6_regen_measure.py collect --out <出力先>
    # 前後の比較表(final・呼数・行為の分布の JSD・購入/食事)
    python docs/bench/analysis/w6-regen-2026-09-28/w6_regen_measure.py compare \\
        --before <前の出力先> --after <後の出力先> --out <比較 JSON>

腕(``ARMS``)は [二層の記録 §0](../two-layer-2026-09-27/README.md) の呼び方をそのまま写した。
- 現行 7 種(+語彙 v3 の活動層 off): CLI の旗と同じ kwargs を ``shibuya.cli.run`` に渡す。
- 旧 6 種: 同じ 6 腕を ``report_precondition=False``(D-113 ② の切替口=第267 以前の通報)で。
- golden の帰無腕: ``tests/engine/test_presence_executor.py`` の ``W17_GOLDEN["null_arm_final"]``
  (``plan_executor=False``・``report_precondition=False``・ライブラリ既定の語彙 v1)。

**絶対パスは書かない**(世界資産は manifest の ``frozen_sources`` にファイル名と sha256 だけが
載る)。壁時計は決定論でないので JSON に入れない(標準出力だけ)。
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

#: 現行の腕(二層の記録 §0-1「現行の値」列+語彙 v3 の 2 行)。
CURRENT_ARMS: dict[str, dict[str, Any]] = {
    "v3_default": {"vocab_version": "v3", "activity": True},
    "v3_activity_off": {"vocab_version": "v3", "activity": False},
    "v1_default": {"vocab_version": "v1"},
    "v1_derive_v2_1": {"vocab_version": "v1", "derive_rule": "v2.1"},
    "v2": {"vocab_version": "v2"},
    "v1_edge": {"vocab_version": "v1", "geometry": "edge"},
    "v2_edge": {"vocab_version": "v2", "geometry": "edge"},
    "v1_edge_plateau": {"vocab_version": "v1", "geometry": "edge", "area_source": "plateau"},
}
#: 旧 6 種(D-113 ② 以前の値を ``--report-precondition off`` で再現する腕)。
OLD_ARMS: dict[str, dict[str, Any]] = {
    f"old_{k}": {**v, "report_precondition": False}
    for k, v in CURRENT_ARMS.items()
    if not k.startswith("v3_")
}
#: golden 表の帰無腕(``W17_GOLDEN["null_arm_final"]``)。
GOLDEN_ARMS: dict[str, dict[str, Any]] = {
    "golden_null_arm": {"plan_executor": False, "report_precondition": False},
}
ARMS: dict[str, dict[str, Any]] = {**CURRENT_ARMS, **OLD_ARMS, **GOLDEN_ARMS}

#: 行為の分布から外す鍵(経路の 1 歩=エンジン継続。LLM 由来の行為の分布を見るため)。
ENGINE_CONTINUE = "(エンジン継続)"


def summarize(name: str, kw: dict[str, Any], res: Any) -> dict[str, Any]:
    """1 腕の要約(決定論の値だけ)。二層の記録の ``summarize`` と同じ欄。"""
    calls = int(res.column("calls").sum()) if res.diagnostics.size else 0
    return {
        "arm": name,
        "args": dict(kw),
        "final_hash": res.final_hash,
        "checkpoints": {str(c.tick): c.combined for c in res.checkpoints},
        "llm_calls": calls,
        "llm_calls_result": int(res.llm_calls),
        "calls_per_agent_day": round(calls / max(1, res.n_agents), 4),
        "calls_by_condition": dict(res.calls_by_condition),
        "action_usage": dict(res.action_usage),
        "activity": bool(res.activity),
        "activity_kind_counts": dict(res.activity_kind_counts),
        "activity_counters": dict(res.activity_counters),
        "parse_error_rate": round(float(res.parse_error_rate), 6),
        "purchases": int(res.column("purchases").sum()) if res.diagnostics.size else 0,
        "meals": int(res.meals),
        "meal_yen": int(res.meal_yen),
        "presence_counters": dict(res.presence_counters),
        "conserved": bool(res.conserved),
        "frozen_sources": res.run_manifest_fields().get("frozen_sources"),
    }


def cmd_run(args: argparse.Namespace) -> int:
    from shibuya import cli

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    arms = dict(ARMS)
    if args.only:
        keep = [s.strip() for s in args.only.split(",") if s.strip()]
        unknown = [k for k in keep if k not in ARMS]
        if unknown:
            print(f"未知の腕: {unknown}", file=sys.stderr)
            return 2
        arms = {k: ARMS[k] for k in keep}
    for name, kw in arms.items():
        t0 = time.perf_counter()
        res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
        payload = cli.checkpoints_payload(res, run_id=name)
        (out / f"{name}.checkpoints.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8"
        )
        row = summarize(name, kw, res)
        (out / f"{name}.summary.json").write_text(
            json.dumps(row, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8"
        )
        print(f"{name}: final {res.final_hash[:16]}… calls {row['llm_calls']:,} "
              f"({time.perf_counter() - t0:.1f}s)", flush=True)
    return 0


def cmd_collect(args: argparse.Namespace) -> int:
    out = Path(args.out)
    rows = []
    for name in ARMS:
        p = out / f"{name}.summary.json"
        if p.exists():
            rows.append(json.loads(p.read_text(encoding="utf-8")))
    doc = {
        "schema": "shibuya.bench/w6-regen-2026-09-28/1",
        "n_agents": args.agents,
        "seed": args.seed,
        "arms": rows,
    }
    (out / "summary.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8"
    )
    print(f"{len(rows)} 腕を束ねた")
    return 0


def jsd_bits(p: dict[str, int], q: dict[str, int], drop: tuple[str, ...] = ()) -> float:
    """2 つの計数分布の Jensen–Shannon 距離の 2 乗(=JS divergence・底 2・0〜1)。"""
    keys = sorted((set(p) | set(q)) - set(drop))
    sp = sum(p.get(k, 0) for k in keys)
    sq = sum(q.get(k, 0) for k in keys)
    if sp == 0 or sq == 0:
        return float("nan")
    out = 0.0
    for k in keys:
        a = p.get(k, 0) / sp
        b = q.get(k, 0) / sq
        m = 0.5 * (a + b)
        if a > 0:
            out += 0.5 * a * math.log2(a / m)
        if b > 0:
            out += 0.5 * b * math.log2(b / m)
    return out


def cmd_compare(args: argparse.Namespace) -> int:
    def load(d: str) -> dict[str, dict[str, Any]]:
        doc = json.loads((Path(d) / "summary.json").read_text(encoding="utf-8"))
        return {r["arm"]: r for r in doc["arms"]}

    before, after = load(args.before), load(args.after)
    rows = []
    for name in ARMS:
        b, a = before.get(name), after.get(name)
        if b is None or a is None:
            continue
        rows.append(
            {
                "arm": name,
                "final_before": b["final_hash"],
                "final_after": a["final_hash"],
                "moved": b["final_hash"] != a["final_hash"],
                "calls_before": b["llm_calls"],
                "calls_after": a["llm_calls"],
                "purchases_before": b["purchases"],
                "purchases_after": a["purchases"],
                "meals_before": b["meals"],
                "meals_after": a["meals"],
                "jsd_actions_llm": round(
                    jsd_bits(b["action_usage"], a["action_usage"], (ENGINE_CONTINUE,)), 8
                ),
                "jsd_actions_all": round(jsd_bits(b["action_usage"], a["action_usage"]), 8),
                "jsd_wake_conditions": round(
                    jsd_bits(b["calls_by_condition"], a["calls_by_condition"]), 8
                ),
                "action_usage_delta": {
                    k: a["action_usage"].get(k, 0) - b["action_usage"].get(k, 0)
                    for k in sorted(set(a["action_usage"]) | set(b["action_usage"]))
                    if a["action_usage"].get(k, 0) != b["action_usage"].get(k, 0)
                },
                "conserved_after": a["conserved"],
            }
        )
    Path(args.out).write_text(
        json.dumps({"schema": "shibuya.bench/w6-regen-2026-09-28/compare/1", "rows": rows},
                   ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    for r in rows:
        print(f"{r['arm']:24s} {r['final_before'][:8]} → {r['final_after'][:8]} "
              f"calls {r['calls_before']:,} → {r['calls_after']:,} "
              f"JSD(llm) {r['jsd_actions_llm']:.2e}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--world", default="data/world/v2")
    r.add_argument("--agents", type=int, default=5_000)
    r.add_argument("--seed", type=int, default=1)
    r.add_argument("--out", required=True)
    r.add_argument("--only", default="", help="腕名をカンマ区切りで(既定=全部)")
    c = sub.add_parser("collect")
    c.add_argument("--out", required=True)
    c.add_argument("--agents", type=int, default=5_000)
    c.add_argument("--seed", type=int, default=1)
    k = sub.add_parser("compare")
    k.add_argument("--before", required=True)
    k.add_argument("--after", required=True)
    k.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"run": cmd_run, "collect": cmd_collect, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
