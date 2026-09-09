# -*- coding: utf-8 -*-
"""t7_distribution.py — **T7 LLM 層 分布同値**(本番構成・温度 0.7)。

正典
- 運用設計書 §1.3/§1.4 **T7**「LLM層分布同値(本番構成)。同一manifest・同一機・同一vLLM版・
  **温度0.7**・DP7。行動分布 JSD ≤ 帰無95th・制約違反率差の95%CI上限 ≤ 0.05(指標Bの装置)」。

やること
    seed だけ違う 2 ランを回し、**行動語の分布 / ResultCode の分布 / 呼数**を突き合わせて
    JSD[bits] と χ² を出す。行動分布の JSD は**帰無参照**(同一分布から同じ標本数を 2 本引いた
    ときの JSD の 95%点)と並べて読む。

合格線について(**親判断待ち = D-25**)
    §1.3 の「JSD ≤ 帰無95th」は**指標B(v0 vs v1 の観測削減)**の閾値であって、
    「seed 違い 2 ラン」の合格線は設計書に書かれていない(2 ランは定義上同分布なので、
    帰無参照そのものが期待値になる)。本ツールは**報告値**として JSD・帰無95th・χ² p を出し、
    合否は付けない。合格線の決定は親へ。

親がサーバーで叩く例::

    python tools/c6/t7_distribution.py \
        --endpoints http://127.0.0.1:8000,http://127.0.0.1:8001 \
        --world data/world/v2 --agents 5000 --ticks 24 \
        --temperature 0.7 --seed 1 --seed-b 2 --out docs/bench/c6
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c6lib  # noqa: E402

T7_GATE_NOTE = (
    "T7 の合格線は設計書に無い(§1.3 の「JSD ≤ 帰無95th」は指標B=観測削減の閾値)。"
    "seed 違い 2 ランの合否は **D-25 として親判断待ち**。本表は報告値。"
)


def result_code_counts(agents: object) -> dict[str, int]:
    """個体 SoA の ``last_result`` → ``ResultCode`` 名の度数。"""
    import numpy as np

    from shibuya.agents.state import ResultCode

    arr = np.asarray(getattr(agents, "registry").field("last_result")).ravel()
    names = {int(c): c.name for c in ResultCode}
    vals, cnt = np.unique(arr, return_counts=True)
    return {names.get(int(v), f"CODE_{int(v)}"): int(c) for v, c in zip(vals.tolist(), cnt.tolist())}


def action_counts_from_tape(tape_dir: Path) -> dict[str, int]:
    """テープの応答本文 → 行動語の度数(``llm.parser`` で解釈)。"""
    from shibuya.engine.tape import Tape

    texts = [str(r.response) for r in Tape(tape_dir).rows()]
    return {k: int(v) for k, v in c6lib.score_texts(texts)["action_counts"].items()}


def distribution_report(a: dict[str, int], b: dict[str, int], label: str, seed: int) -> dict:
    """2 分布の JSD・χ²・帰無参照を 1 まとめに(**純関数**)。"""
    pooled = Counter(a)
    pooled.update(b)
    n_a, n_b = sum(a.values()), sum(b.values())
    null = c6lib.null_jsd_reference(pooled, n_a, n_b, seed=seed)
    return {
        "label": label,
        "n_a": n_a,
        "n_b": n_b,
        "jsd_bits": c6lib.jsd_counts(a, b),
        "null_p50": null["p50"],
        "null_p95": null["p95"],
        "chi2": c6lib.chi2_2sample(a, b),
        "counts_a": dict(sorted(a.items())),
        "counts_b": dict(sorted(b.items())),
    }


def main(argv: list[str] | None = None) -> int:
    ap = c6lib.common_parser("T7: LLM 層 分布同値(seed 違い 2 ラン)")
    ap.add_argument("--seed-b", type=int, default=2, help="2 本目の master_seed")
    ap.add_argument("--mode", default="production")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--temperature", type=float, default=0.7, help="本番構成は 0.7")
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--tape-dir", default="", help="テープの置き場(既定=--out の下)")
    args = ap.parse_args(argv)

    endpoints = c6lib.endpoints_of(args)
    tape_root = Path(args.tape_dir) if args.tape_dir else Path(args.out) / "t7_tapes"
    tape_root.mkdir(parents=True, exist_ok=True)

    runs = []
    for tag, seed in (("a", args.seed), ("b", args.seed_b)):
        client = (
            c6lib.build_fleet_client(
                endpoints,
                model=args.model,
                mode=args.mode,
                run_id=args.run_id,
                run_seed=seed,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            )
            if endpoints
            else None
        )
        try:
            res, route = c6lib.run_smoke(
                n_agents=args.agents,
                seed=seed,
                ticks=args.ticks,
                world_dir=c6lib.world_dir_of(args),
                tape_path=tape_root / tag,
                fleet=client,
            )
        finally:
            if client is not None:
                client.close()
        runs.append(
            {
                "tag": tag,
                "seed": seed,
                "route": route,
                "llm_calls": int(res.llm_calls),
                "actions": action_counts_from_tape(tape_root / tag),
                "result_codes": result_code_counts(res.agents),
                "parse_error_rate": float(res.parse_error_rate),
                "diagnostics_day": {k: float(v) for k, v in res.diagnostics_day().items()},
            }
        )

    reports = [
        distribution_report(runs[0]["actions"], runs[1]["actions"], "行動語", args.seed),
        distribution_report(
            runs[0]["result_codes"], runs[1]["result_codes"], "ResultCode", args.seed + 1
        ),
    ]
    calls = {"a": runs[0]["llm_calls"], "b": runs[1]["llm_calls"]}
    calls["ratio"] = (calls["b"] / calls["a"]) if calls["a"] else float("nan")

    payload = {
        "test": "T7",
        "endpoints": endpoints,
        "temperature": args.temperature,
        "runs": runs,
        "distributions": reports,
        "calls": calls,
        "gate_note": T7_GATE_NOTE,
    }
    md = "\n".join(
        [
            "# T7 LLM 層 分布同値(本番構成・seed 違い 2 ラン)",
            "",
            f"- 構成: endpoints={endpoints or '(mock)'} / 温度={args.temperature}"
            f" / {args.agents:,}体 × {args.ticks} tick / seed {args.seed} vs {args.seed_b}",
            f"- 経路: {runs[0]['route']}",
            "",
            c6lib.markdown_table(
                ["分布", "n(a/b)", "JSD[bits]", "帰無 p50", "帰無 p95", "χ²", "dof", "χ² p"],
                [
                    [
                        r["label"],
                        f"{r['n_a']} / {r['n_b']}",
                        f"{r['jsd_bits']:.4f}",
                        f"{r['null_p50']:.4f}",
                        f"{r['null_p95']:.4f}",
                        f"{r['chi2']['chi2']:.2f}",
                        r["chi2"]["dof"],
                        f"{r['chi2']['p']:.4f}",
                    ]
                    for r in reports
                ],
            ),
            "",
            c6lib.markdown_table(
                ["項目", "a", "b", "比"],
                [["呼数", calls["a"], calls["b"], f"{calls['ratio']:.4f}"]],
            ),
            "",
            f"> {T7_GATE_NOTE}",
        ]
    )
    paths = c6lib.write_outputs(args.out, "t7_distribution", payload, md)
    print(json.dumps({"distributions": [
        {k: r[k] for k in ("label", "jsd_bits", "null_p95")} for r in reports
    ], "calls": calls, "out": paths}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
