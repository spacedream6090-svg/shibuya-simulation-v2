# -*- coding: utf-8 -*-
"""t6_bit_reproduce.py — **T6 LLM 層 bit 再現**(検証ラン構成)。

正典
- 運用設計書 §1.4 **T6**「LLM層bit再現(検証ラン構成・**不一致なら「この機・この版では
  bit再現を主張しない」と記録**)」。§1.3「検証ラン(mode: holdout)=BATCH_INVARIANT=1・TP1・
  温度0・固定ルーティング・sha256_cbor で LLM 層の bit 再現もあり得るが、**本番(温度0.7)では
  主張しない**」。
- 先行実測 = ``docs/bench/b14_batch_invariance/README.md``(A5000/CC 8.6 で 32/32 一致)。

やること
    同一 manifest(同 seed・同 ``--mode``)で 24step スモークを **2 回**回し、録画テープの
    ``(agent_id, tick, wake_class, prompt_hash)`` を鍵に応答本文を突き合わせる。
    一致率・不一致 call_id・manifest 注記の文面を出す。

親がサーバーで叩く例::

    python tools/c6/t6_bit_reproduce.py \
        --endpoints http://127.0.0.1:8000,http://127.0.0.1:8001 \
        --world data/world/v2 --agents 5000 --ticks 24 --mode calibration \
        --out docs/bench/c6

    # 艦隊なしで配管だけ確かめる(mock LLM・CI/ローカル)
    python tools/c6/t6_bit_reproduce.py --world data/world/v2 --agents 500 --ticks 24 --out /tmp/c6

環境(検証ランの前提・親がサーバー側で立てる)::

    VLLM_BATCH_INVARIANT=1 VLLM_MARLIN_USE_ATOMIC_ADD=0 (TP1・温度0)
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c6lib  # noqa: E402

MANIFEST_NOTE_OK = (
    "T6: 同一 manifest 2 ラン ({n} 呼) の応答本文が **全一致**。"
    "この機・この版(engine={engine})で LLM 層の bit 再現を主張する。"
)
MANIFEST_NOTE_NG = (
    "T6: 同一 manifest 2 ラン ({n} 呼) のうち {n_diff} 呼が不一致(一致率 {rate:.4f})。"
    "**この機・この版では LLM 層の bit 再現を主張しない**(運用設計書 §1.4 T6)。"
    "エンジン層の bit 再現(T2)とテープリプレイは影響を受けない。"
)


def _tape_map(path: Path) -> dict[tuple[int, int, int, str], tuple[str, str]]:
    """テープ → ``鍵 → (応答本文, call_id)``。"""
    from shibuya.engine.tape import Tape

    out: dict[tuple[int, int, int, str], tuple[str, str]] = {}
    for row in Tape(path).rows():
        out[row.key] = (str(row.response), str(row.call_id))
    return out


def compare_tapes(a: dict, b: dict) -> dict:
    """2 本のテープの応答本文を突合(**純関数**・テストはモック辞書で)。"""
    keys_a, keys_b = set(a), set(b)
    common = sorted(keys_a & keys_b)
    diffs = [k for k in common if a[k][0] != b[k][0]]
    n = len(common)
    return {
        "n_common": n,
        "n_only_a": len(keys_a - keys_b),
        "n_only_b": len(keys_b - keys_a),
        "n_mismatch": len(diffs),
        "match_rate": (1.0 - len(diffs) / n) if n else 0.0,
        "mismatch_call_ids": [a[k][1] for k in diffs[:200]],
        "mismatch_keys": [list(k) for k in diffs[:50]],
        "ok": bool(n > 0 and not diffs and not (keys_a ^ keys_b)),
    }


def main(argv: list[str] | None = None) -> int:
    ap = c6lib.common_parser("T6: LLM 層 bit 再現(同一 manifest 2 ラン の応答突合)")
    ap.add_argument("--mode", default="calibration", help="smoke/calibration/holdout/ablation/production")
    ap.add_argument("--run-id", default="", help="manifest の自己ハッシュ(cache_salt の第2要素)")
    ap.add_argument("--temperature", type=float, default=0.0, help="検証ランは 0")
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--tape-dir", default="", help="テープの置き場(既定=一時ディレクトリ)")
    args = ap.parse_args(argv)

    endpoints = c6lib.endpoints_of(args)
    tape_root = Path(args.tape_dir) if args.tape_dir else Path(tempfile.mkdtemp(prefix="c6_t6_"))
    tape_root.mkdir(parents=True, exist_ok=True)

    runs = []
    for i in (1, 2):
        client = (
            c6lib.build_fleet_client(
                endpoints,
                model=args.model,
                mode=args.mode,
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
                tape_path=tape_root / f"run{i}",
                fleet=client,
            )
        finally:
            if client is not None:
                client.close()
        runs.append(
            {
                "route": route,
                "final_hash": res.final_hash,
                "llm_calls": int(res.llm_calls),
                "bridge_counters": {k: float(v) for k, v in res.bridge_counters.items()},
                "tape": str(tape_root / f"run{i}"),
            }
        )

    cmp_ = compare_tapes(_tape_map(tape_root / "run1"), _tape_map(tape_root / "run2"))
    engine = "fleet" if endpoints else "mock"
    note = (
        MANIFEST_NOTE_OK.format(n=cmp_["n_common"], engine=engine)
        if cmp_["ok"]
        else MANIFEST_NOTE_NG.format(
            n=cmp_["n_common"], n_diff=cmp_["n_mismatch"], rate=cmp_["match_rate"]
        )
    )
    payload = {
        "test": "T6",
        "endpoints": endpoints,
        "mode": args.mode,
        "temperature": args.temperature,
        "runs": runs,
        "comparison": cmp_,
        "engine_layer_hash_match": runs[0]["final_hash"] == runs[1]["final_hash"],
        "manifest_note": note,
    }
    md = "\n".join(
        [
            "# T6 LLM 層 bit 再現(同一 manifest 2 ラン)",
            "",
            f"- 構成: endpoints={endpoints or '(mock)'} / mode={args.mode} / 温度={args.temperature}"
            f" / {args.agents:,}体 × {args.ticks} tick / seed={args.seed}",
            f"- 経路: {runs[0]['route']}",
            "",
            c6lib.markdown_table(
                ["項目", "値"],
                [
                    ["突合できた呼数", cmp_["n_common"]],
                    ["片側にしかない呼(run1/run2)", f"{cmp_['n_only_a']} / {cmp_['n_only_b']}"],
                    ["不一致", cmp_["n_mismatch"]],
                    ["一致率", f"{cmp_['match_rate']:.4f}"],
                    ["エンジン層 final_hash 一致(T2)", payload["engine_layer_hash_match"]],
                    ["判定", "合格" if cmp_["ok"] else "不合格 → manifest 注記"],
                ],
            ),
            "",
            "## manifest 注記",
            "",
            f"> {note}",
        ]
    )
    paths = c6lib.write_outputs(args.out, "t6_bit_reproduce", payload, md)
    print(json.dumps({**cmp_, "out": paths}, ensure_ascii=False))
    return 0 if cmp_["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
