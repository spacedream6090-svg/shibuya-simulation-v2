# -*- coding: utf-8 -*-
"""ablation1_fixed_vs_ranking.py — **ablation ①(義務)**「チャネル固定枠 vs 単一ランキング」。

正典
- 知覚契約書 §3.2「先行例は**チャネル別枠を持たない**。よって固定枠は独自設計=expedient、
  **「固定枠 vs 同一総トークンの単一ランキング(最近性×重要度×関連性)」の ablation を義務**
  とする(根拠なし行=470 tok 中約 130=28% が感度試験の範囲)」。
- 同 §8「第1陣(Phase 2・L2=総GPU時間20%の枠内)=6本: **①チャネル固定枠 vs 同一総トークンの
  単一ランキング(義務)**」。§9「完了条件(スケール前): 指標Bの事前登録つき再測+ablation①」。
- 同 §10.3 卒業条件「単一ランキングと**行動分布・違反率が同等**」。

本ツールがすること
    ① **切替口の実在確認**: ``perception.renderer.Renderer(budget_mode=…)`` を
       ``FIXED_SLOTS`` / ``SINGLE_RANKING`` で作り、同じ場面の描画バイトを突き合わせる。
       **バイトが同一なら切替は no-op = ablation ① は測定不成立**(下記)。
    ② 24step スモークを 2 構成で回し、行動分布 JSD・書式エラー率・呼あたりトークンを並べる。

**C6-b で判明(親判断待ち)**
    ``BudgetMode.SINGLE_RANKING`` は ``perception/channels.py`` に**枠(Enum)だけ**があり、
    ``Renderer`` は ``self.budget_mode`` を保持するだけで**どこでも読んでいない**
    (``grep budget_mode src/`` = 定義・引数・代入の 3 か所のみ)。したがって
    現状 ablation ① は「同じ描画を 2 回測る」ことしかできない。
    ``run_day`` / CLI 側にもモードのフラグは無い(レンダラは ``run_day`` 内部で
    ``AgentState`` を作ってから組むので、外から差し替える口も無い)。
    → **単一ランキングの実装**と **run_day/CLI のフラグ**は親判断待ち。

親がサーバーで叩く例::

    python tools/c6/ablation1_fixed_vs_ranking.py \
        --endpoints http://127.0.0.1:8000,http://127.0.0.1:8001 \
        --world data/world/v2 --agents 5000 --ticks 24 --out docs/bench/c6
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c6lib  # noqa: E402

NO_OP_NOTE = (
    "BudgetMode.SINGLE_RANKING は Renderer が読んでいない(枠だけ)。"
    "ablation ①(§3.2 の義務)は**切替の実装が入るまで測定不成立**=親判断待ち。"
)


def probe_switch(n_agents: int = 64, n_cells: int = 25, seed: int = 1, n_scenes: int = 24) -> dict:
    """2 つの ``BudgetMode`` で同じ場面を描き、バイト差分の有無を返す(**純関数寄り**)。

    レンダラだけを合成世界の上に組むので GPU も実資産も要らない。
    """
    from shibuya.agents.schedule import synthesize
    from shibuya.agents.state import AgentState
    from shibuya.engine import resolve as R
    from shibuya.perception import channels as ch
    from shibuya.perception.renderer import Renderer
    from shibuya.world.state import World

    def render_all(mode) -> list[str]:
        world = World.synthetic(n_cells=n_cells, seed=seed)
        agents = AgentState(n_agents)
        schedule = synthesize(n_agents, seed, world.n_cells)
        R.initialize(agents, world, schedule, day_index=0)
        r = Renderer(world, agents, seed=seed, budget_mode=mode)
        out: list[str] = []
        for k in range(n_scenes):
            tick = 60 * (k % 24)
            r.prepare_tick(tick)
            out.append(r.render(k % n_agents, tick=tick, wake_reason=3).text)
        return out

    fixed = render_all(ch.BudgetMode.FIXED_SLOTS)
    ranked = render_all(ch.BudgetMode.SINGLE_RANKING)
    n_diff = sum(1 for a, b in zip(fixed, ranked) if a != b)
    return {
        "n_scenes": len(fixed),
        "n_different": n_diff,
        "switch_effective": bool(n_diff > 0),
        "mean_chars_fixed": sum(len(t) for t in fixed) / max(1, len(fixed)),
        "mean_chars_ranking": sum(len(t) for t in ranked) / max(1, len(ranked)),
        "note": "" if n_diff else NO_OP_NOTE,
    }


def run_arm(args, tag: str, endpoints: list[str], tape_root: Path) -> dict:
    """1 構成のスモーク(budget_mode=tag を run_day へ渡す・09-09 切替口実装後)。"""
    client = (
        c6lib.build_fleet_client(
            endpoints,
            model=args.model,
            mode="ablation",
            run_id=args.run_id,
            run_seed=args.seed,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        if endpoints
        else None
    )
    try:
        res, route = c6lib.run_smoke(
            n_agents=args.agents,
            seed=args.seed,
            ticks=args.ticks,
            world_dir=c6lib.world_dir_of(args),
            tape_path=tape_root / tag,
            fleet=client,
            extra={"budget_mode": tag},  # 09-09 親: サブ R の切替口(fixed/ranking)を腕へ渡す
        )
    finally:
        if client is not None:
            client.close()
    from shibuya.engine.tape import Tape

    texts = [str(r.response) for r in Tape(tape_root / tag).rows()]
    sc = c6lib.score_texts(texts)
    rc = {k: float(v) for k, v in res.renderer_counters.items()}
    return {
        "arm": tag,
        "route": route,
        "llm_calls": int(res.llm_calls),
        "action_counts": sc["action_counts"],
        "format_error_rate": sc["format_error_rate"],
        "undefined_rate": sc["undefined_rate"],
        "role_action_rate": sc["role_action_rate"],
        "prompt_tokens_mean": rc.get("prompt_tokens_mean", float("nan")),
        "tokens_shared_static_mean": rc.get("tokens_shared_static_mean", float("nan")),
        "tokens_cell_mean": rc.get("tokens_cell_mean", float("nan")),
        "tokens_individual_mean": rc.get("tokens_individual_mean", float("nan")),
        "final_hash": res.final_hash,
    }


def main(argv: list[str] | None = None) -> int:
    ap = c6lib.common_parser("ablation ①: チャネル固定枠 vs 単一ランキング(§3.2 の義務)")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--tape-dir", default="", help="テープの置き場(既定=--out の下)")
    ap.add_argument("--probe-only", action="store_true", help="切替口の実在確認だけして終わる")
    args = ap.parse_args(argv)

    probe = probe_switch(seed=args.seed)
    payload: dict = {"test": "ablation_1", "switch_probe": probe}

    arms: list[dict] = []
    if not args.probe_only:
        endpoints = c6lib.endpoints_of(args)
        tape_root = Path(args.tape_dir) if args.tape_dir else Path(args.out) / "ab1_tapes"
        tape_root.mkdir(parents=True, exist_ok=True)
        for tag in ("fixed_slots", "single_ranking"):
            arms.append(run_arm(args, tag, endpoints, tape_root))
        payload["arms"] = arms
        if len(arms) == 2:
            payload["jsd_bits"] = c6lib.jsd_counts(
                arms[0]["action_counts"], arms[1]["action_counts"]
            )
            payload["identical_runs"] = arms[0]["final_hash"] == arms[1]["final_hash"]

    md = [
        "# ablation ① チャネル固定枠 vs 単一ランキング(知覚契約書 §3.2・義務)",
        "",
        "## ① 切替口の実在確認(レンダラ単体)",
        "",
        c6lib.markdown_table(
            ["項目", "値"],
            [
                ["描いた場面数", probe["n_scenes"]],
                ["バイトが違った場面", probe["n_different"]],
                ["平均文字数 固定枠 / 単一ランキング",
                 f"{probe['mean_chars_fixed']:.1f} / {probe['mean_chars_ranking']:.1f}"],
                ["切替は効いているか", "はい" if probe["switch_effective"] else "**いいえ(no-op)**"],
            ],
        ),
    ]
    if not probe["switch_effective"]:
        md += ["", f"> {NO_OP_NOTE}"]
    if arms:
        md += [
            "",
            "## ② 24step スモーク 2 構成",
            "",
            c6lib.markdown_table(
                ["構成", "呼数", "書式エラー率", "未定義率", "役割語率", "呼あたり tok(平均)"],
                [
                    [a["arm"], a["llm_calls"], f"{a['format_error_rate']:.4f}",
                     f"{a['undefined_rate']:.4f}", f"{a['role_action_rate']:.4f}",
                     f"{a['prompt_tokens_mean']:.1f}"]
                    for a in arms
                ],
            ),
            "",
            f"- 行動分布 JSD[bits] = {payload.get('jsd_bits', float('nan')):.4f}"
            f" / 2 ラン の final_hash 一致 = {payload.get('identical_runs')}",
        ]
    paths = c6lib.write_outputs(args.out, "ablation1_fixed_vs_ranking", payload, "\n".join(md))
    print(json.dumps({"switch_probe": probe, "out": paths}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
