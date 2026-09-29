"""3 段目(呼数の上限を無制限に・D-99 (a′)・D-110)の計測: 15 腕を上限あり(``--l4-scale 1``=旧挙動)と
既定(無制限)で回して前後を比べる。

使い方(リポジトリの根から)::

    python docs/bench/analysis/l4-unlimited-2026-09-28/l4_measure.py \\
        --world data/world/v2 --out docs/bench/analysis/l4-unlimited-2026-09-28/l4_arms15.json

腕の表は [W6 再生成の計測](../w6-regen-2026-09-28/w6_regen_measure.py) の ``ARMS`` をそのまま使う
(mock 5,000 体・seed 1・1 シミュ日)。各腕を 2 回回す:

- ``x1``: ``l4_scale=1.0``(L4 按分 34.72 呼/tick・持ち越し 2 tick=段 2c までの既定=旧挙動)。
- ``unlimited``: 既定(``cli.CLI_DEFAULT_L4_SCALE``=0=1 tick の上限を体数に置く)。

加えて照合腕 ``v3_default_x1_q24off``(v3 既定・``l4_scale=1.0``・Q24 の「最新の応答の活動」を切る
=``IntentLayer._absorb_latest`` を空にする**計測だけの差し込み**)で、段 2c の検収値 ``6845e3ac`` を
再現するかを見る(=x1 の v3 既定の差が Q24 だけであることの確認)。

出力(腕ごと): final・呼数・呼/体/日・起床入口別の呼(場所/体/日課/会話/満了/社会)・繰り延べ/昇格/縮退/
不応期抑止/就寝抑止/域外抑止の件数(診断列の和)・購入/食事・行為の件数・x1 と無制限の行為分布の JSD・
manifest の L4 監査欄。**壁時計は決定論でないので JSON に入れない**(標準出力だけ)。絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
W6 = HERE.parent / "w6-regen-2026-09-28" / "w6_regen_measure.py"
ENGINE_CONTINUE = "(エンジン継続)"

#: 起床条件 → 入口(知覚契約書 §6 の条件をユーザー向けの 6 つに束ねる)。
ENTRANCES: dict[str, tuple[str, ...]] = {
    "場所": ("CELL_BLOCK",),
    "体": ("INTEROCEPTION",),
    "日課": ("PLAN_SLEEPING", "PLAN_WORKING", "PLAN_GENERAL", "PLAN_TRANSIT"),
    "会話": ("CONVERSATION_TURN",),
    "満了": ("ACTIVITY_EXPIRY",),
    "社会": ("ACQUAINTANCE", "PROXIMITY_SWAP", "BEING_WATCHED", "OVERHEARD"),
}
DIAG = ("deferred", "promoted", "degraded", "suppressed", "sleep_suppressed", "outside_suppressed")


def _w6() -> Any:
    spec = importlib.util.spec_from_file_location("w6_regen_measure", W6)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def jsd_bits(p: dict[str, int], q: dict[str, int], drop: tuple[str, ...] = ()) -> float:
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


def summarize(res: Any) -> dict[str, Any]:
    cbc = dict(res.calls_by_condition)
    ent = {k: int(sum(cbc.get(c, 0) for c in v)) for k, v in ENTRANCES.items()}
    diag = {c: int(res.column(c).sum()) if res.diagnostics.size else 0 for c in DIAG}
    calls = int(res.column("calls").sum()) if res.diagnostics.size else 0
    m = res.run_manifest_fields()
    return {
        "final_hash": res.final_hash,
        "llm_calls": calls,
        "llm_calls_per_agent_day": round(calls / max(1, res.n_agents), 4),
        "calls_by_entrance": ent,
        "calls_by_condition": cbc,
        "diag": diag,
        "purchases": int(res.column("purchases").sum()) if res.diagnostics.size else 0,
        "meals": int(res.meals),
        "action_usage": dict(res.action_usage),
        "budget_per_tick": float(res.budget_per_tick),
        "l4_scale": float(res.l4_scale),
        "l4_audit": {k: m[k] for k in ("llm_calls_total", "llm_calls_per_agent_day", "l4_line",
                                       "l4_exceeded", "l4_notes")},
        "intent": {k: res.intent.get(k) for k in ("set", "arrived", "done", "latest_activity_used")}
        if res.intent else {},
        "conserved": bool(res.conserved),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="", help="腕名をカンマ区切りで(既定=全部)")
    args = ap.parse_args(argv)

    from shibuya import cli
    from shibuya.engine import intent as INT

    w6 = _w6()
    before_doc = json.loads(
        (HERE.parent / "intent-chooser-2026-09-28" / "intent_hold_arms15.json").read_text(
            encoding="utf-8"
        )
    )
    committed = {r["arm"]: r["final_hash"] for r in before_doc["arms"]}
    arms = dict(w6.ARMS)
    if args.only:
        keep = [s.strip() for s in args.only.split(",") if s.strip()]
        arms = {k: arms[k] for k in keep}
    rows = []
    for name, kw in arms.items():
        row: dict[str, Any] = {"arm": name, "args": dict(kw),
                               "final_committed_2c": committed.get(name, "")}
        for label, extra in (("x1", {"l4_scale": 1.0}), ("unlimited", {})):
            t0 = time.perf_counter()
            res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw, **extra)
            row[label] = summarize(res)
            print(f"{name} {label}: final {res.final_hash[:8]} calls {row[label]['llm_calls']:,} "
                  f"({row[label]['llm_calls_per_agent_day']}/体/日) wall {time.perf_counter() - t0:.1f}s",
                  flush=True)
        row["x1_equals_committed_2c"] = row["x1"]["final_hash"] == row["final_committed_2c"]
        row["jsd_actions_llm"] = round(jsd_bits(row["x1"]["action_usage"],
                                                row["unlimited"]["action_usage"],
                                                (ENGINE_CONTINUE,)), 8)
        row["jsd_actions_all"] = round(jsd_bits(row["x1"]["action_usage"],
                                                row["unlimited"]["action_usage"]), 8)
        row["jsd_wake_conditions"] = round(jsd_bits(row["x1"]["calls_by_condition"],
                                                    row["unlimited"]["calls_by_condition"]), 8)
        rows.append(row)
    # 照合腕: x1 の v3 既定から Q24 を切ると段 2c の検収値に戻るか
    check: dict[str, Any] = {}
    if "v3_default" in arms:
        orig = INT.IntentLayer._absorb_latest
        INT.IntentLayer._absorb_latest = lambda self, agents, applied: None  # type: ignore[method-assign]
        try:
            res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world,
                          **w6.ARMS["v3_default"], l4_scale=1.0)
        finally:
            INT.IntentLayer._absorb_latest = orig  # type: ignore[method-assign]
        check = {"arm": "v3_default_x1_q24off", "final_hash": res.final_hash,
                 "equals_committed_2c": res.final_hash == committed.get("v3_default", ""),
                 "llm_calls": int(res.llm_calls)}
        print(f"v3_default_x1_q24off: final {res.final_hash[:8]} "
              f"(= 2c 検収値 {check['equals_committed_2c']})", flush=True)
    Path(args.out).write_text(
        json.dumps({"schema": "shibuya.bench/l4-unlimited-2026-09-28/1", "n_agents": args.agents,
                    "seed": args.seed, "arms": rows, "check_q24off": check},
                   ensure_ascii=False, indent=1, default=str) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
