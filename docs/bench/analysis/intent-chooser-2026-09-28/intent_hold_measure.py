"""段 2c(意図の保持・D-112 ①・D-114 案 A)の計測: 15 腕の前後と mock の腕。

使い方(リポジトリの根から)::

    # 15 腕(W6 再生成の腕の表そのもの)。前=段 2a/2b の値(summary_after.json)と突き合わせる
    python docs/bench/analysis/intent-chooser-2026-09-28/intent_hold_measure.py arms15 \\
        --world data/world/v2 --out docs/bench/analysis/intent-chooser-2026-09-28/intent_hold_arms15.json
    # mock の腕(語彙 v3 既定・out_of_cell_target_p と intent_max_ticks と 2c 無し)
    python docs/bench/analysis/intent-chooser-2026-09-28/intent_hold_measure.py mock \\
        --world data/world/v2 --out docs/bench/analysis/intent-chooser-2026-09-28/intent_hold_mock.json

15 腕: 各 checkpoint で**意図の 4 欄を混ぜないエージェントのハッシュ**(``Registry.state_hash(
exclude=INTENT_FIELDS)``)も記録し、同じ式で ``combined`` を組んだ final(``final_wo_intent``)を出す。
意図の層が働かない腕(v1/v2・``--activity off``・旧 6 種・帰無腕)は ``final_wo_intent`` が**前の final と
一致する**はず(=欄を足しただけで挙動は 1 バイトも変わっていない)。

mock の腕(mock 5,000・seed 1・語彙 v3・activity on)
- ``p0``(既定)/ ``p0.1`` / ``p0.5``: ``mock_out_of_cell_target_p``(購入/食事/並ぶの対象に B2 の見える名)。
- ``p0.5_max30`` / ``p0.5_max120``: ``intent_max_ticks`` の感度腕。
- ``*_2c_off``: 意図の層を作らない(``engine.run.IntentLayer`` を「None を返す」に差し替える=**計測だけの
  差し込み**・同じ mock 出力で段 2b の挙動)。

出力: final・呼数(起床条件別)・購入/食事・店の行為の成立率((購入+食事)/ 候補の解決に来た応答数)・
``intent``・``target_resolution.v_intent``・活動層の計数。絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
W6 = HERE.parent / "w6-regen-2026-09-28" / "w6_regen_measure.py"


def _w6() -> Any:
    spec = importlib.util.spec_from_file_location("w6_regen_measure", W6)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class _Recorder:
    """``AgentState.state_hash`` を包み、意図の欄を混ぜない値も checkpoint ごとに控える。"""

    def __init__(self) -> None:
        from shibuya.agents import state as S

        self.S = S
        self.orig = S.AgentState.state_hash
        self.wo: list[str] = []

    def __enter__(self) -> "_Recorder":
        rec = self
        S = self.S

        def patched(agent_state: Any) -> str:
            rec.wo.append(agent_state.registry.state_hash(exclude=S.INTENT_FIELDS))
            return rec.orig(agent_state)

        S.AgentState.state_hash = patched  # type: ignore[method-assign]
        return self

    def __exit__(self, *exc: Any) -> None:
        self.S.AgentState.state_hash = self.orig  # type: ignore[method-assign]


def _final_wo_intent(res: Any, wo: list[str]) -> str:
    from shibuya.core.hashing import blake3_hex

    if not res.checkpoints or len(wo) != len(res.checkpoints):
        return ""
    cp = res.checkpoints[-1]
    parts = [wo[-1], cp.world_hash, cp.population_hash, cp.schedule_hash]
    if cp.activity_hash:
        parts.append(cp.activity_hash)
    return blake3_hex("\x1f".join(parts).encode("utf-8"))


def _shop(res: Any) -> dict[str, Any]:
    tr = res.target_resolution or {}
    attempts = sum(int(v) for v in (tr.get("attempts") or {}).values())
    purchases = int(res.column("purchases").sum()) if res.diagnostics.size else 0
    meals = int(res.meals)
    return {
        "shop_responses": attempts,
        "purchases": purchases,
        "meals": meals,
        "shop_success_rate": round((purchases + meals) / attempts, 4) if attempts else 0.0,
    }


def cmd_arms15(args: argparse.Namespace) -> int:
    from shibuya import cli

    w6 = _w6()
    before_doc = json.loads((HERE / "summary_after.json").read_text(encoding="utf-8"))
    before = {r["arm"]: r for r in before_doc["arms"]}
    rows = []
    for name, kw in w6.ARMS.items():
        t0 = time.perf_counter()
        with _Recorder() as rec:
            res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
        row = w6.summarize(name, kw, res)
        row["final_wo_intent"] = _final_wo_intent(res, rec.wo)
        row["intent"] = dict(res.intent)
        row["v_intent"] = dict((res.target_resolution or {}).get("v_intent") or {})
        row.update(_shop(res))
        b = before.get(name, {})
        row["final_before"] = b.get("final_hash", "")
        row["llm_calls_before"] = b.get("llm_calls")
        row["purchases_before"] = b.get("purchases")
        row["meals_before"] = b.get("meals")
        row["moved"] = row["final_hash"] != row["final_before"]
        row["wo_intent_equals_before"] = row["final_wo_intent"] == row["final_before"]
        rows.append(row)
        print(f"{name}: {row['final_before'][:8]} → {row['final_hash'][:8]} "
              f"(欄を除く {row['final_wo_intent'][:8]} "
              f"{'=' if row['wo_intent_equals_before'] else '≠'} 前) "
              f"calls {row['llm_calls_before']} → {row['llm_calls']} "
              f"({time.perf_counter() - t0:.1f}s)", flush=True)
    Path(args.out).write_text(
        json.dumps({"schema": "shibuya.bench/intent-chooser-2026-09-28/intent-hold-arms15/1",
                    "n_agents": args.agents, "seed": args.seed, "arms": rows},
                   ensure_ascii=False, indent=1, default=str) + "\n",
        encoding="utf-8",
    )
    return 0


MOCK_ARMS: dict[str, dict[str, Any]] = {
    "p0": {"p": 0.0},
    "p0_2c_off": {"p": 0.0, "off": True},
    "p0.1": {"p": 0.1},
    "p0.1_2c_off": {"p": 0.1, "off": True},
    "p0.5": {"p": 0.5},
    "p0.5_2c_off": {"p": 0.5, "off": True},
    "p0.5_max30": {"p": 0.5, "max": 30},
    "p0.5_max120": {"p": 0.5, "max": 120},
}


def cmd_mock(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.engine import run as RUN

    rows = []
    for name, spec in MOCK_ARMS.items():
        orig = RUN.IntentLayer
        if spec.get("off"):
            RUN.IntentLayer = lambda *a, **k: None  # type: ignore[assignment,misc]
        t0 = time.perf_counter()
        try:
            res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world,
                          vocab_version="v3", mock_out_of_cell_target_p=float(spec["p"]),
                          intent_max_ticks=int(spec.get("max", 60)))
        finally:
            RUN.IntentLayer = orig  # type: ignore[assignment]
        calls = int(res.column("calls").sum()) if res.diagnostics.size else 0
        row = {
            "arm": name,
            "mock_out_of_cell_target_p": float(spec["p"]),
            "intent_layer": not spec.get("off", False),
            "intent_max_ticks": int(spec.get("max", 60)),
            "final_hash": res.final_hash,
            "llm_calls": calls,
            "calls_by_condition": dict(res.calls_by_condition),
            "action_usage": dict(res.action_usage),
            "intent": dict(res.intent),
            "v_intent": dict((res.target_resolution or {}).get("v_intent") or {}),
            "named_out_of_cell_detail": dict(
                (res.target_resolution or {}).get("named_out_of_cell_detail") or {}
            ),
            "iv_no_candidate": dict((res.target_resolution or {}).get("iv_no_candidate") or {}),
            "activity_counters": dict(res.activity_counters),
            "move_unreachable": int(res.move_unreachable),
            "conserved": bool(res.conserved),
            **_shop(res),
        }
        rows.append(row)
        it = row["intent"]
        print(f"{name}: final {res.final_hash[:8]} calls {calls:,} "
              f"set {it.get('set', 0)} arrived {it.get('arrived', 0)} done {it.get('done', 0)} "
              f"shop {row['shop_success_rate']} ({time.perf_counter() - t0:.1f}s)", flush=True)
    Path(args.out).write_text(
        json.dumps({"schema": "shibuya.bench/intent-chooser-2026-09-28/intent-hold-mock/1",
                    "n_agents": args.agents, "seed": args.seed, "arms": rows},
                   ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("arms15", "mock"):
        p = sub.add_parser(name)
        p.add_argument("--world", default="data/world/v2")
        p.add_argument("--agents", type=int, default=5_000)
        p.add_argument("--seed", type=int, default=1)
        p.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return cmd_arms15(args) if args.cmd == "arms15" else cmd_mock(args)


if __name__ == "__main__":
    sys.exit(main())
