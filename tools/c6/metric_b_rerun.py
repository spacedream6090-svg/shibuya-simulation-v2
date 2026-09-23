# -*- coding: utf-8 -*-
"""metric_b_rerun.py — **指標B の事前登録つき再測**(Phase 2 実データ場面)。

正典(知覚契約書 §8「指標Bの事前登録(決定09-06・Phase 2の実データ場面)」逐語)
    「**制約種ごとにn≥50(5種=250場面)+「答えが決まる場面」100場面**。閾値を事前登録:
    分布=**JSD(v0,v1)≤帰無95%点**(同分布2標本のブートストラップ)・制約=**|Δ違反率|の
    95%CI上限≤0.05**。採点器の除外パターン(「言うな」型の否定命令)を修正。**TP1で実行**
    (32B AWQ TP4は温度0でも4.1%非再現)。検出可能差0.35→0.15。」
    採点の定義は ``tools/quality_probe_v0/scorer.py``(制約違反率・行動分布 JSD[bits]・
    帰無参照つき)に合わせる。

3 段構え
    ① **収集**: mock LLM のスモークを ``RecordingLLM`` で包んで回し、プロンプト全文つきの
       ``scenes.jsonl`` を作る。**録画テープには B5/B6(個体固有)が入らない**ので
       (``engine.llm_bridge.SHARED_BLOCK_IDS``)、テープ単独では場面を再呼できない。
    ② **抽出**(純関数 ``c6lib.select_metric_b_scenes``): 制約種ごと 50・決まる場面 100。
    ③ **再呼と採点**: 2 モデル(T1 8B・対照 14B INT8)へ同一プロンプトを温度 0・seed 固定で。
       帰無参照 = **同モデル seed 違い**の 1 パス。

親がサーバーで叩く例::

    # ① 収集だけ(GPU 不要・ローカルで可)
    python tools/c6/metric_b_rerun.py --world data/world/v2 --agents 5000 --ticks 1440 \
        --collect-only --out docs/bench/c6

    # ③ 2 モデルへ再呼(8B=:8000 / 14B=:8001)
    python tools/c6/metric_b_rerun.py --world data/world/v2 \
        --scenes docs/bench/c6/scenes.jsonl \
        --endpoints http://127.0.0.1:8000,http://127.0.0.1:8001 \
        --models Qwen3-8B-INT8,Qwen3-14B-INT8 --out docs/bench/c6
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c6lib  # noqa: E402


def collect_scenes(args) -> tuple[list, Path, dict]:
    """mock ランを回して ``scenes.jsonl``(プロンプト全文)を作る。"""
    from shibuya.llm.mock import MockLLM

    rec = c6lib.RecordingLLM(MockLLM(master_seed=args.seed))
    res, route = c6lib.run_smoke(
        n_agents=args.agents,
        seed=args.seed,
        ticks=args.ticks,
        world_dir=c6lib.world_dir_of(args),
        llm=rec,
        checkpoint_every=max(1, args.ticks),
    )
    path = rec.dump(Path(args.out) / "scenes.jsonl")
    scenes = [c6lib.scene_from_record(r) for r in rec.records]
    meta = {
        "route": route,
        "llm_calls": int(res.llm_calls),
        "n_records": len(rec.records),
        "final_hash": res.final_hash,
        "scenes_path": str(path),
    }
    return scenes, path, meta


def rerun_scenes(scenes, endpoint: str, model: str, seed: int, args) -> list[str]:
    """1 モデルへ全場面を投げて応答本文を返す(逐次・24step スモーク規模の想定)。"""
    out: list[str] = []
    for i, s in enumerate(scenes):
        system, user = c6lib.split_prompt(s.prompt)
        r = c6lib.chat_once(
            endpoint,
            model,
            system,
            user,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            seed=seed,
        )
        out.append(r["text"])
    return out


def score_pass(scenes, texts) -> dict:
    """1 パスの採点(違反フラグ・行動分布・書式)。"""
    flags = c6lib.violation_flags(scenes, texts)
    sc = c6lib.score_texts(texts)
    return {
        "n": len(texts),
        "violations": flags,
        "violation_rate": (sum(flags) / len(flags)) if flags else 0.0,
        "action_counts": sc["action_counts"],
        "format_error_rate": sc["format_error_rate"],
        "undefined_rate": sc["undefined_rate"],
        "role_action_rate": sc["role_action_rate"],
    }


def compare_passes(a: dict, b: dict, null: dict | None, seed: int) -> dict:
    """指標B の 2 半分(制約違反率の差 + 行動分布 JSD)。**純関数**。"""
    diffs = [int(y) - int(x) for x, y in zip(a["violations"], b["violations"])]
    point, lo, hi = c6lib.bootstrap_mean_ci(diffs, seed=seed) if diffs else (0.0, 0.0, 0.0)
    pooled = dict(a["action_counts"])
    for k, v in b["action_counts"].items():
        pooled[k] = pooled.get(k, 0) + v
    boot_null = c6lib.null_jsd_reference(
        pooled, sum(a["action_counts"].values()), sum(b["action_counts"].values()), seed=seed
    )
    out = {
        "delta_violation_rate": point,
        "delta_ci95": [lo, hi],
        "delta_ci_upper_abs": max(abs(lo), abs(hi)),
        "violation_gate": c6lib.METRIC_B_VIOLATION_CI_MAX,
        "violation_ok": bool(max(abs(lo), abs(hi)) <= c6lib.METRIC_B_VIOLATION_CI_MAX),
        "discordant_pairs": {
            "a_only": sum(1 for d in diffs if d < 0),
            "b_only": sum(1 for d in diffs if d > 0),
        },
        "jsd_bits": c6lib.jsd_counts(a["action_counts"], b["action_counts"]),
        "null_bootstrap_p50": boot_null["p50"],
        "null_bootstrap_p95": boot_null["p95"],
    }
    if null is not None:
        out["null_same_model_jsd_bits"] = c6lib.jsd_counts(
            a["action_counts"], null["action_counts"]
        )
    out["distribution_ok"] = bool(out["jsd_bits"] <= boot_null["p95"])
    return out


def main(argv: list[str] | None = None) -> int:
    ap = c6lib.common_parser("指標B: 事前登録つき再測(制約種 n≥50 × 5 + 決まる場面 100)")
    ap.add_argument("--scenes", default="", help="既存の scenes.jsonl(空なら収集から)")
    ap.add_argument("--tape", default="", help="録画テープ(診断用。B5/B6 が無いので再呼は不可)")
    ap.add_argument("--collect-only", action="store_true", help="収集と在庫表だけ出して終わる")
    ap.add_argument("--models", default="", help="endpoints と同順のモデル名(カンマ区切り)")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--null-seed-offset", type=int, default=1, help="帰無参照(同モデル seed 違い)")
    ap.add_argument("--per-kind", type=int, default=c6lib.METRIC_B_PER_KIND)
    ap.add_argument("--determined", type=int, default=c6lib.METRIC_B_DETERMINED)
    ap.add_argument(
        "--kinds",
        default=",".join(c6lib.CONSTRAINT_KINDS),
        help="事前登録する制約種(カンマ区切り・既定=" + ",".join(c6lib.CONSTRAINT_KINDS) + ")",
    )
    args = ap.parse_args(argv)
    kinds = tuple(k.strip() for k in args.kinds.split(",") if k.strip())
    unknown = [k for k in kinds if k not in c6lib.FAILURE_WORD_BY_KIND]
    if unknown:
        ap.error(f"未知の制約種: {unknown}(候補={sorted(c6lib.FAILURE_WORD_BY_KIND)})")

    meta: dict = {}
    if args.scenes:
        scenes = c6lib.scenes_from_jsonl(args.scenes)
        meta["scenes_path"] = args.scenes
    elif args.tape:
        scenes = c6lib.scenes_from_tape(args.tape)
        meta["scenes_path"] = args.tape
        meta["warning"] = (
            "テープ由来の場面は共有ブロック(B0-B4b)だけで B5/B6 が無い=再呼はできない"
        )
    else:
        scenes, path, meta = collect_scenes(args)

    inventory = c6lib.scene_inventory(scenes, kinds, args.per_kind, args.determined)
    picked = c6lib.select_metric_b_scenes(scenes, args.per_kind, args.determined, kinds)
    selected = [s for k in sorted(picked) for s in picked[k]]
    selection = {k: len(v) for k, v in sorted(picked.items())}

    payload: dict = {
        "test": "metric_B",
        "meta": meta,
        "inventory": inventory,
        "selection": selection,
        "n_selected": len(selected),
        "preregistration": {
            "kinds": list(kinds),
            "per_kind": args.per_kind,
            "determined": args.determined,
            "violation_ci_upper_max": c6lib.METRIC_B_VIOLATION_CI_MAX,
            "distribution": "JSD(A,B) ≤ 帰無95%点(同分布2標本のブートストラップ)",
            "null_reference": "同モデル seed 違いの 1 パス + ブートストラップ帰無",
        },
    }

    endpoints = c6lib.endpoints_of(args)
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if args.collect_only or not endpoints or not selected:
        payload["status"] = "collected"  # 再呼はしていない
    else:
        while len(models) < len(endpoints):
            models.append(c6lib.discover_model(endpoints[len(models)]))
        passes = []
        for i, (ep, mdl) in enumerate(zip(endpoints[:2], models[:2])):
            texts = rerun_scenes(selected, ep, mdl, args.seed, args)
            passes.append({"endpoint": ep, "model": mdl, **score_pass(selected, texts)})
        null_pass = None
        if endpoints:
            null_texts = rerun_scenes(
                selected, endpoints[0], models[0], args.seed + args.null_seed_offset, args
            )
            null_pass = {"model": models[0], **score_pass(selected, null_texts)}
        payload["passes"] = passes
        payload["null_pass"] = null_pass
        if len(passes) >= 2:
            payload["comparison"] = compare_passes(passes[0], passes[1], null_pass, args.seed)
        payload["status"] = "scored"

    rows = [
        ["制約種 " + k, inventory["per_kind"][k], args.per_kind, selection.get(k, 0)]
        for k in sorted(kinds)
    ]
    rows.append(
        ["答えが決まる場面", inventory["n_determined"], args.determined, selection.get("determined", 0)]
    )
    md_parts = [
        "# 指標B 事前登録つき再測(C6-b)",
        "",
        f"- 場面の出どころ: {meta.get('scenes_path', '(収集)')}"
        f" / 全 {inventory['n_scenes']:,} 呼(うち部分プロンプト {inventory['n_partial']:,})",
        f"- 事前登録: 制約種ごと n≥{args.per_kind}(5種)+ 決まる場面 {args.determined}"
        f" / |Δ違反率| の 95%CI 上限 ≤ {c6lib.METRIC_B_VIOLATION_CI_MAX}"
        " / JSD ≤ 帰無95%点",
        "",
        c6lib.markdown_table(["区分", "在庫", "必要", "採用"], rows),
        "",
        "## 失敗種の在庫(全 18 種・事前登録の見直し材料)",
        "",
        c6lib.markdown_table(
            ["失敗種", "語(RESULT_TEXT)", "件数"],
            [
                [k, c6lib.FAILURE_WORD_BY_KIND.get(k, ""), v]
                for k, v in sorted(
                    inventory["per_failure_kind_all"].items(), key=lambda kv: (-kv[1], kv[0])
                )
            ],
        ),
    ]
    if payload.get("comparison"):
        c = payload["comparison"]
        p = payload["passes"]
        md_parts += [
            "",
            "## 2 モデルの突合",
            "",
            c6lib.markdown_table(
                ["モデル", "n", "違反率", "書式エラー率", "未定義率"],
                [
                    [x["model"], x["n"], f"{x['violation_rate']:.4f}",
                     f"{x['format_error_rate']:.4f}", f"{x['undefined_rate']:.4f}"]
                    for x in p
                ],
            ),
            "",
            c6lib.markdown_table(
                ["指標", "値", "閾値", "判定"],
                [
                    ["Δ違反率(B−A)", f"{c['delta_violation_rate']:+.4f}", "—", "—"],
                    ["Δ 95%CI", f"[{c['delta_ci95'][0]:+.4f}, {c['delta_ci95'][1]:+.4f}]",
                     f"|上限| ≤ {c['violation_gate']}", "合格" if c["violation_ok"] else "不合格"],
                    ["行動分布 JSD[bits]", f"{c['jsd_bits']:.4f}",
                     f"帰無95th {c['null_bootstrap_p95']:.4f}",
                     "合格" if c["distribution_ok"] else "不合格"],
                    ["帰無(同モデル seed 違い) JSD",
                     f"{c.get('null_same_model_jsd_bits', float('nan')):.4f}", "—", "—"],
                ],
            ),
        ]
    else:
        md_parts += [
            "",
            f"> 状態: {payload['status']}(再呼していない)。"
            "`--endpoints` と `--models` を与えると 2 モデルへ再呼して採点する。",
        ]
    if inventory["shortfall_per_kind"] or inventory["determined_shortfall"]:
        md_parts += [
            "",
            "> **事前登録の在庫不足**: "
            f"{inventory['shortfall_per_kind']} / 決まる場面 不足 {inventory['determined_shortfall']}。"
            "ラン長(--ticks)か個体数を増やすこと。",
        ]
    paths = c6lib.write_outputs(args.out, "metric_b_rerun", payload, "\n".join(md_parts))
    print(json.dumps({"inventory": inventory, "selection": selection, "out": paths}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
