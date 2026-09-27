"""二層の実装 段 3 の計測手順(mock 5,000 体・seed 1・1 シミュ日)。

使い方(リポジトリの根から・書き出し先は既定でこのフォルダ)::

    python docs/bench/analysis/two-layer-2026-09-27/two_layer_measure.py \\
        --world data/world/v2 --agents 5000 --seed 1

腕(``ARMS``)ごとに ``shibuya.cli.run``(台帳つきの標準入口=CLI と同じ経路)を 1 回回し、
``<腕>.checkpoints.json``(``shibuya.cli.checkpoints_payload`` と同じ形)と、全腕の要約
``summary.json`` を書く。**絶対パスは書かない**(世界資産は manifest の ``frozen_sources`` に
ファイル名と sha256 だけが載る)。壁時計は決定論でないので JSON には入れない(標準出力だけ)。

腕
- 計測 3 本(二層の実装アジェンダ §3): (a) v3+activity on(CLI の新しい既定)/(b) v3+activity off/
  (c) v1+activity off(=D-113 以後の v1 既定 2f3969cf の不変の確認)。
- 版の台帳(§0)用: 旧 6 種の既定の腕を**現行コード**で回した値(v1 既定・読み口 v2.1・語彙 v2・
  edge・edge+語彙 v2・edge+plateau)。``--ledger`` のときだけ回す。
- 旧値の再現(§0): 同じ 6 腕を ``report_precondition=False``(D-113 ② の切替口=第267 以前の
  通報)で回し、final_hash だけを ``summary.json`` の ``ledger_report_precondition_off`` に書く。
  ``--ledger-old`` のときだけ回す(checkpoint JSON は書かない)。

起床の内訳の束ね(expedient・README §2 の注記):
  場所=CELL_BLOCK(顕著行為の到達も同じ条件)/ 体=INTEROCEPTION・ACQUAINTANCE・PROXIMITY_SWAP・
  BEING_WATCHED・OVERHEARD / 日課=PLAN_SLEEPING・PLAN_WORKING・PLAN_GENERAL・PLAN_TRANSIT /
  会話=CONVERSATION_TURN / 満了=ACTIVITY_EXPIRY。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent

#: 計測 3 本(アジェンダ §3)。
ARMS: dict[str, dict[str, Any]] = {
    "a_v3_activity_on": {"vocab_version": "v3", "activity": True},
    "b_v3_activity_off": {"vocab_version": "v3", "activity": False},
    "c_v1_activity_off": {"vocab_version": "v1", "activity": False},
}
#: 版の台帳(旧 6 種の既定の腕を現行コードで)。
LEDGER_ARMS: dict[str, dict[str, Any]] = {
    "ledger_v1_default": {"vocab_version": "v1"},
    "ledger_v1_derive_v2_1": {"vocab_version": "v1", "derive_rule": "v2.1"},
    "ledger_v2": {"vocab_version": "v2"},
    "ledger_v1_edge": {"vocab_version": "v1", "geometry": "edge"},
    "ledger_v2_edge": {"vocab_version": "v2", "geometry": "edge"},
    "ledger_v1_edge_plateau": {"vocab_version": "v1", "geometry": "edge", "area_source": "plateau"},
}
#: 起床の内訳の束ね(条件名 → 群)。
WAKE_GROUPS: dict[str, str] = {
    "CELL_BLOCK": "place",
    "INTEROCEPTION": "body",
    "ACQUAINTANCE": "body",
    "PROXIMITY_SWAP": "body",
    "BEING_WATCHED": "body",
    "OVERHEARD": "body",
    "PLAN_SLEEPING": "plan",
    "PLAN_WORKING": "plan",
    "PLAN_GENERAL": "plan",
    "PLAN_TRANSIT": "plan",
    "CONVERSATION_TURN": "conversation",
    "ACTIVITY_EXPIRY": "expiry",
}


def summarize(name: str, kw: dict[str, Any], res: Any) -> dict[str, Any]:
    """1 腕の要約(決定論の値だけ)。"""
    calls = int(res.column("calls").sum()) if res.diagnostics.size else 0
    groups: dict[str, int] = {g: 0 for g in ("place", "body", "plan", "conversation", "expiry")}
    for cond, n in res.calls_by_condition.items():
        groups[WAKE_GROUPS[cond]] += int(n)
    return {
        "arm": name,
        "args": dict(kw),
        "final_hash": res.final_hash,
        "checkpoints": {str(c.tick): c.combined for c in res.checkpoints},
        "llm_calls": calls,
        "calls_per_agent_day": round(calls / max(1, res.n_agents), 4),
        "wake_groups": groups,
        "calls_by_condition": dict(res.calls_by_condition),
        "action_usage": dict(res.action_usage),
        "activity": bool(res.activity),
        "activity_kind_counts": dict(res.activity_kind_counts),
        "activity_counters": dict(res.activity_counters),
        "parse_error_rate": round(float(res.parse_error_rate), 6),
        "parse_error_rate_strict": round(float(res.parse_error_rate_strict), 6),
        "purchases": int(res.column("purchases").sum()) if res.diagnostics.size else 0,
        "meals": int(res.meals),
        "meal_yen": int(res.meal_yen),
        "undefined_actions": int(res.undefined_action_count),
        "conserved": bool(res.conserved),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=str(HERE))
    ap.add_argument("--ledger", action="store_true", help="版の台帳の 6 腕も回す")
    ap.add_argument("--only", default="", help="腕名をカンマ区切りで(既定=全部)")
    ap.add_argument("--ledger-old", action="store_true",
                    help="旧 6 腕を report_precondition=False で回して final だけ記録する")
    args = ap.parse_args(argv)

    from shibuya import cli

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    summary_path = out / "summary.json"
    if args.ledger_old:
        doc = json.loads(summary_path.read_text(encoding="utf-8"))
        old: dict[str, str] = {}
        for name, kw in LEDGER_ARMS.items():
            res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world,
                          report_precondition=False, **kw)
            old[name] = res.final_hash
            print(f"{name} (report_precondition off): {res.final_hash[:16]}…", flush=True)
        doc["ledger_report_precondition_off"] = old
        summary_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                                encoding="utf-8")
        return 0
    arms = dict(ARMS)
    if args.ledger:
        arms.update(LEDGER_ARMS)
    if args.only:
        keep = {s.strip() for s in args.only.split(",") if s.strip()}
        arms = {k: v for k, v in arms.items() if k in keep}
    rows = []
    for name, kw in arms.items():
        t0 = time.perf_counter()
        res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
        payload = cli.checkpoints_payload(res, run_id=name)
        (out / f"{name}.checkpoints.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8"
        )
        rows.append(summarize(name, kw, res))
        print(f"{name}: final {res.final_hash[:16]}… calls {rows[-1]['llm_calls']:,} "
              f"({time.perf_counter() - t0:.1f}s)", flush=True)
    prev: dict[str, Any] = {}
    if summary_path.exists():  # 腕を分けて回したときに前の結果を残す(上書きは腕ごと)
        prev = {r["arm"]: r for r in json.loads(summary_path.read_text(encoding="utf-8"))["arms"]}
    for r in rows:
        prev[r["arm"]] = r
    order = list(ARMS) + list(LEDGER_ARMS)
    doc = {
        "schema": "shibuya.bench/two-layer-2026-09-27/1",
        "n_agents": args.agents,
        "seed": args.seed,
        "world": Path(args.world).as_posix(),
        "arms": [prev[k] for k in order if k in prev],
    }
    if summary_path.exists():
        old_doc = json.loads(summary_path.read_text(encoding="utf-8"))
        if "ledger_report_precondition_off" in old_doc:
            doc["ledger_report_precondition_off"] = old_doc["ledger_report_precondition_off"]
    summary_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
