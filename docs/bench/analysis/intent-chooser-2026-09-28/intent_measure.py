"""段 2a(候補の絞り込み+選択器の口)の計測: 購入/食事の試み・成立・落選の理由の前後(mock 5,000・seed 1)。

使い方(リポジトリの根から)::

    python docs/bench/analysis/intent-chooser-2026-09-28/intent_measure.py \\
        --world data/world/v2 --out <出力 JSON> [--only v3_default,v1_default]

**計測だけの差し込み**: ``engine.resolve`` の ``_apply_buy``/``_apply_eat`` と ``_complete_buy``/
``_complete_eat`` を数えるだけの包みに差し替える(引数も戻り値も触らない)。並ぶ→購入/食事の委譲も
同じ関数を通るので数に入る。列から席へ入れた体(D-113 ③)も ``_complete_*`` を通るので成立に入る。
``--check-instrumentation`` で包まないランと final が同じことを確かめる。絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

ARMS: dict[str, dict[str, Any]] = {
    "v3_default": {"vocab_version": "v3", "activity": True},
    "v1_default": {"vocab_version": "v1"},
    "v2": {"vocab_version": "v2"},
    "golden_null_arm": {"plan_executor": False, "report_precondition": False},
}
FAIL_CODES = ("BAD_TARGET", "CLOSED", "OUT_OF_STOCK", "NOT_IN_EATERY", "MONEY_SHORT", "LOST_ARBITRATION")


class Counters:
    """``resolve`` の購入/食事の入口と完了を数える(挙動は触らない)。"""

    def __init__(self) -> None:
        self.attempts: Counter[str] = Counter()
        self.done: Counter[str] = Counter()
        self.fail: dict[str, Counter[str]] = {"buy": Counter(), "eat": Counter()}
        self._orig: dict[str, Any] = {}

    def install(self) -> None:
        from shibuya.engine import resolve as R

        codes = {name: int(getattr(R.ResultCode, name)) for name in FAIL_CODES}
        self._orig = {
            "_apply_buy": R._apply_buy, "_apply_eat": R._apply_eat,
            "_complete_buy": R._complete_buy, "_complete_eat": R._complete_eat,
        }
        c = self

        def wrap_apply(kind: str, orig):
            def f(agents, world, aid, tgt, tick, out, schedule):
                c.attempts[kind] += int(np.asarray(aid).size)
                before = {k: out.per_result.get(v, 0) for k, v in codes.items()}
                orig(agents, world, aid, tgt, tick, out, schedule)
                for k, v in codes.items():
                    c.fail[kind][k] += out.per_result.get(v, 0) - before[k]
            return f

        def wrap_complete(kind: str, orig, attr: str):
            def f(agents, world, a, b, paid, tick, out):
                n0 = getattr(out, attr)
                orig(agents, world, a, b, paid, tick, out)
                c.done[kind] += getattr(out, attr) - n0
            return f

        R._apply_buy = wrap_apply("buy", self._orig["_apply_buy"])
        R._apply_eat = wrap_apply("eat", self._orig["_apply_eat"])
        R._complete_buy = wrap_complete("buy", self._orig["_complete_buy"], "n_purchases")
        R._complete_eat = wrap_complete("eat", self._orig["_complete_eat"], "n_meals")
        for table in (R._APPLY, R._APPLY_V2, R._APPLY_V3):
            if R.ACT_BUY in table:
                table[R.ACT_BUY] = R._apply_buy
            if R.ACT_EAT in table:
                table[R.ACT_EAT] = R._apply_eat

    def uninstall(self) -> None:
        from shibuya.engine import resolve as R

        for k, v in self._orig.items():
            setattr(R, k, v)
        for table in (R._APPLY, R._APPLY_V2, R._APPLY_V3):
            if R.ACT_BUY in table:
                table[R.ACT_BUY] = self._orig["_apply_buy"]
            if R.ACT_EAT in table:
                table[R.ACT_EAT] = self._orig["_apply_eat"]


def run_arm(name: str, kw: dict[str, Any], world: str, agents: int, seed: int,
            instrument: bool = True) -> dict[str, Any]:
    from shibuya import cli

    c = Counters()
    if instrument:
        c.install()
    try:
        t0 = time.perf_counter()
        res = cli.run(n_agents=agents, seed=seed, world_dir=world, **kw)
        dt = time.perf_counter() - t0
    finally:
        if instrument:
            c.uninstall()
    man = res.run_manifest_fields()
    row: dict[str, Any] = {
        "arm": name,
        "args": dict(kw),
        "final_hash": res.final_hash,
        "checkpoints": {str(k.tick): k.combined for k in res.checkpoints},
        "llm_calls": int(res.column("calls").sum()) if res.diagnostics.size else 0,
        "purchases_diag": int(res.column("purchases").sum()) if res.diagnostics.size else 0,
        "meals": int(res.meals),
        "action_usage": dict(res.action_usage),
        "chooser": man.get("chooser"),
        "target_resolution": man.get("target_resolution"),
        "conserved": bool(res.conserved),
    }
    if instrument:
        for kind in ("buy", "eat"):
            att = int(c.attempts[kind])
            done = int(c.done[kind])
            row[kind] = {
                "attempts": att,
                "done": done,
                "rate": round(done / att, 4) if att else None,
                "fail": {k: int(v) for k, v in c.fail[kind].items()},
            }
    print(f"{name}: final {res.final_hash[:16]}… calls {row['llm_calls']:,} ({dt:.1f}s)", flush=True)
    return row


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--check-instrumentation", action="store_true")
    args = ap.parse_args(argv)
    arms = dict(ARMS) if not args.only else {k: ARMS[k] for k in args.only.split(",") if k}
    rows = [run_arm(k, v, args.world, args.agents, args.seed) for k, v in arms.items()]
    doc: dict[str, Any] = {"schema": "shibuya.bench/intent-chooser-2026-09-28/1",
                           "n_agents": args.agents, "seed": args.seed, "arms": rows}
    if args.check_instrumentation:
        first = next(iter(arms))
        plain = run_arm(first, arms[first], args.world, args.agents, args.seed, instrument=False)
        doc["instrumentation_is_transparent"] = plain["final_hash"] == rows[0]["final_hash"]
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
