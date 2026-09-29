"""D-120 7b(会話からの店の抽出)の計測。

使い方(リポジトリの根から)::

    # 既定の byte 一致: コミット済みの源(HEAD 9e08d4a を git archive で展開した src)と作業木で同じランを回す
    python docs/bench/analysis/store-memory-2026-09-28/wom_measure.py bytecheck \\
        --head-src <HEAD を展開した src> --scratch <作業用の場所> \\
        --out docs/bench/analysis/store-memory-2026-09-28/wom_byte_check.json
    # mock / classical の店の記憶 on の腕(抽出 0 件の記録・7a の数値の変化=Q77)
    python docs/bench/analysis/store-memory-2026-09-28/wom_measure.py on \\
        --out docs/bench/analysis/store-memory-2026-09-28/wom_on_arms.json
    # 実 LLM テープ 17 本(記憶 第 1 段と同じ内容で束ねた集合)のリプレイ
    python docs/bench/analysis/store-memory-2026-09-28/wom_measure.py replay \\
        --out docs/bench/analysis/store-memory-2026-09-28/wom_replay.json

- ``bytecheck``: 構成 4 本(v3 既定・classical・記憶 on(店 off)・**店 on**)× 源 2 本(HEAD 9e08d4a / 作業木)。
  比べるもの: final・店の 7 欄を混ぜない final・呼数・``blocks.parquet``・``calls.parquet`` の 14 列(列ごと)。店 on は
  Q77(並ぶの成功=向き 0)で店の欄の値が変わる=final は変わり、店を混ぜない final とテープは同じはず。
- ``on``: 構成ごとに別プロセス。manifest ``wom``(mock/classical は店名を書かない=抽出 0 件)と ``store_memory_summary``。
- ``replay``: テープの応答から、エンジンと同じ ``engine.wom.WomExtractor``(W6 の店の名・評価語の辞書 v0)で抽出する。
  範囲 3 つ: (A) 会話ターンの呼(``wake_class``=会話=エンジンが ``_utter`` で抽出する呼)(B) 行動「会話」で対象が
  ``P-<id>`` の応答(C) 全部の応答(参考)。欄 2 つ: 「ひと言」(v1/v2 の規則)/ 理由+対象(v3 の規則をこの
  テープに当てた代理=v3 の実テープは無い)。話し手のセル=B2 のセル(チェーンの近い順)。聞き手の行は書かない
  (抽出の量だけ)。

絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
UNIQUE = HERE.parent / "memory-stage1-2026-09-28" / "replay.json"
CONFIGS: dict[str, dict[str, Any]] = {
    "memory_on": {"vocab_version": "v3", "memory": "on"},
    "store_on": {"vocab_version": "v3", "memory": "on", "store_memory": "on"},
    "memory_classical": {"vocab_version": "v3", "memory": "on", "policy": "classical",
                         "chooser": "classical"},
    "store_classical": {"vocab_version": "v3", "memory": "on", "store_memory": "on", "policy": "classical",
                        "chooser": "classical"},
}
BYTE_CONFIGS: dict[str, dict[str, Any]] = {
    "v3_default": {"vocab_version": "v3"},
    "v3_classical": {"vocab_version": "v3", "policy": "classical", "chooser": "classical"},
    "v3_memory_on": {"vocab_version": "v3", "memory": "on"},
    "v3_store_on": {"vocab_version": "v3", "memory": "on", "store_memory": "on"},
}
PLACE_RE = re.compile(r"現在地はセル([^\s()()]+)")
PERSON_RE = re.compile(r"^P-(\d+)$")


def _h(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:16]


def _final_wo(res: Any, rec: list[str]) -> str:
    from shibuya.core.hashing import blake3_hex

    if not rec or len(rec) != len(res.checkpoints):
        return ""
    cp = res.checkpoints[-1]
    parts = [rec[-1], cp.world_hash, cp.population_hash, cp.schedule_hash]
    if cp.activity_hash:
        parts.append(cp.activity_hash)
    return blake3_hex("\x1f".join(parts).encode("utf-8"))


def _patch_state_hash(rec: list[str]) -> None:
    from shibuya.agents import state as S

    orig = S.AgentState.state_hash
    ex = tuple(getattr(S, "STORE_MEMORY_FIELDS", ()))

    def patched(agent_state: Any) -> str:
        if getattr(agent_state, "store_memory_columns", False):
            rec.append(agent_state.registry.state_hash(exclude=ex))
        return orig(agent_state)

    S.AgentState.state_hash = patched  # type: ignore[method-assign]


# ------------------------------------------------------------------ bytecheck
def cmd_bytecheck_one(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from shibuya import cli

    rec: list[str] = []
    _patch_state_hash(rec)
    kw = dict(BYTE_CONFIGS[args.config])
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape, **kw)
    calls = pq.read_table(Path(args.tape) / "calls.parquet")
    blocks = pq.read_table(Path(args.tape) / "blocks.parquet")
    out = {
        "config": args.config, "final": res.final_hash[:16], "final_wo_store": _final_wo(res, rec)[:16],
        "calls": int(res.llm_calls), "calls_rows": int(calls.num_rows), "blocks_rows": int(blocks.num_rows),
        "blocks_sha": _h({n: blocks.column(n).to_pylist() for n in blocks.column_names}),
        "calls_columns_sha": {n: _h(calls.column(n).to_pylist()) for n in calls.column_names},
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_bytecheck(args: argparse.Namespace) -> int:
    runs = []
    scratch = Path(args.scratch)
    for name in BYTE_CONFIGS:
        pair = {}
        for side, src in (("head_9e08d4a", args.head_src), ("working_tree_7b", "")):
            env = dict(os.environ)
            if src:
                env["PYTHONPATH"] = src
                env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"
            tape = scratch / f"{side}_{name}"
            cmd = [sys.executable, str(Path(__file__)), "bytecheck-one", "--config", name, "--world",
                   args.world, "--agents", str(args.agents), "--seed", str(args.seed), "--tape", str(tape)]
            got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True, env=env)
            pair[side] = json.loads(got.stdout.strip().splitlines()[-1])
        h, w = pair["head_9e08d4a"], pair["working_tree_7b"]
        row = {"run": name, **pair,
               "final_equal": h["final"] == w["final"],
               "final_wo_store_equal": h["final_wo_store"] == w["final_wo_store"],
               "calls_equal": h["calls"] == w["calls"],
               "blocks_equal": (h["blocks_sha"], h["blocks_rows"]) == (w["blocks_sha"], w["blocks_rows"]),
               "calls_columns_equal": h["calls_columns_sha"] == w["calls_columns_sha"]}
        runs.append(row)
        print(f"{name}: final {row['final_equal']} 店なし {row['final_wo_store_equal']} calls {row['calls_equal']} "
              f"blocks {row['blocks_equal']} calls 列 {row['calls_columns_equal']}", flush=True)
    doc = {"schema": "shibuya.bench/wom-byte-check/1",
           "how": ("same runs (mock 5,000, seed 1, vocab v3, energy) with the committed source (git archive of "
                   "HEAD 9e08d4a) and with the 7b working tree; tape = shared prompt blocks (blocks.parquet) and "
                   "call rows (calls.parquet: all 14 columns hashed column by column). final_wo_store = the final "
                   "hash with the 7 store-memory fields left out (only for runs that allocate them). The store-on "
                   "run changes its store fields by the Q77 fix (queue success = valence 0), so its final moves "
                   "while the store-free final and the tape stay the same."),
           "runs": runs}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                              newline="\n")
    return 0


# ------------------------------------------------------------------ on
def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli

    rec: list[str] = []
    _patch_state_hash(rec)
    kw = dict(CONFIGS[args.config])
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
    wall = time.perf_counter() - t0
    m = res.run_manifest_fields()
    out = {"config": args.config, "args": kw, "final_hash": res.final_hash,
           "final_wo_store": _final_wo(res, rec), "llm_calls": int(res.llm_calls),
           "wom": m.get("wom", {}), "store_memory_summary": m.get("store_memory_summary", {}),
           "memory_counts": m.get("memory_summary", {}).get("counts", {}),
           "wall_seconds_nondeterministic": round(wall, 2)}
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_on(args: argparse.Namespace) -> int:
    rows = []
    for name in CONFIGS:
        cmd = [sys.executable, str(Path(__file__)), "one", "--config", name, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed)]
        got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        row = json.loads(got.stdout.strip().splitlines()[-1])
        rows.append(row)
        c = row["wom"].get("counts", {})
        print(f"{name}: final {row['final_hash'][:8]} wo_store {row['final_wo_store'][:8]} calls "
              f"{row['llm_calls']:,} 発話 {c.get('utterances')} 抽出 {c.get('wom_extracted', 0)} "
              f"wall {row['wall_seconds_nondeterministic']}s", flush=True)
    finals = {r["config"]: r["final_hash"] for r in rows}
    for r in rows:
        base = {"store_on": "memory_on", "store_classical": "memory_classical"}.get(r["config"])
        if base:
            r["wo_store_equals_memory_on"] = r["final_wo_store"] == finals[base]
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/wom/on/1", "rows": rows},
                                         ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ replay
def cmd_replay(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from shibuya.core.types import EventClass
    from shibuya.engine.wom import WomExtractor
    from shibuya.llm.parser import parse_two_line
    from shibuya.perception.renderer import PerceptionAssets
    from shibuya.world.state import World

    world = World.load_or_synthetic(args.world, n_cells=139, seed=1)
    passets = PerceptionAssets.load_or_synthetic(args.world, world)
    cell_of = {str(p): i for i, p in enumerate(passets.place_ids)}
    names = tuple(str(n) for n in world.assets.poi_name)
    unique = json.loads(UNIQUE.read_text(encoding="utf-8"))["unique"]["tapes"]
    if args.limit_tapes:
        unique = unique[: args.limit_tapes]
    scopes = ("conversation_turn", "talk_to_person", "all")
    fields = ("comment", "reason_target")
    exs: dict[tuple[str, str, str], WomExtractor] = {}

    def ex_for(ver: str, scope: str, field: str) -> WomExtractor:
        k = (ver, scope, field)
        if k not in exs:
            exs[k] = WomExtractor.from_world(world)
        return exs[k]

    per_tape = []
    t_total = 0.0
    n_total = 0
    for name in unique:
        run, arm = name.split("/")
        tdir = Path(args.tape_root) / run / arm
        ver = "v2" if arm.endswith("_v2") else "v1"
        blocks = pq.read_table(tdir / "blocks.parquet", columns=["block_id", "text"]).to_pydict()
        cell_by_block: dict[str, int] = {}
        for bid, tx in zip(blocks["block_id"], blocks["text"]):
            if "[B2 場所]" in tx:
                m = PLACE_RE.search(tx)
                if m and m.group(1) in cell_of:
                    cell_by_block[bid] = cell_of[m.group(1)]
        t = pq.read_table(tdir / "calls.parquet",
                          columns=["wake_class", "response", "deferred", "block_ids"]).to_pydict()
        c: Counter = Counter()
        for k in range(len(t["response"])):  # 逐次: 呼ごと(計測の道具・エンジンではない)
            if t["deferred"][k] or not t["response"][k]:
                continue
            pr = parse_two_line(t["response"][k], ver)
            b2 = next((b for b in t["block_ids"][k] if b in cell_by_block), None)
            cell = cell_by_block[b2] if b2 else -1
            tgt = str(getattr(pr.target, "raw", "") or "")
            in_scope = {
                "conversation_turn": int(t["wake_class"][k]) == int(EventClass.CONVERSATION),
                "talk_to_person": pr.action == "会話" and bool(PERSON_RE.match(tgt.strip())),
                "all": True,
            }
            texts = {}
            for f in fields:
                e0 = ex_for(ver, "all", f)
                texts[f] = e0.utterance_text("v2" if f == "comment" else "v3",
                                             comment=str(pr.raw_comment or pr.comment or ""),
                                             reason=str(pr.raw_reason or pr.reason or ""), target=tgt)
            for f in fields:
                t0 = time.perf_counter()
                res = ex_for(ver, "all", f).extract(texts[f], cell)
                t_total += time.perf_counter() - t0
                n_total += 1
                for s in scopes:
                    if in_scope[s]:
                        ex_for(ver, s, f).observe(res)
                        c[f"{s}:{f}:calls"] += 1
                        c[f"{s}:{f}:empty"] += int(not texts[f])
        per_tape.append({"tape": name, "vocab": ver, "counts": dict(c)})
        print(f"{name}: 会話ターン {c['conversation_turn:comment:calls']:,} 呼", flush=True)
    out: dict[str, Any] = {}
    for (ver, scope, f), e in sorted(exs.items()):
        out.setdefault(ver, {}).setdefault(scope, {})[f] = e.summary(names)
    doc = {
        "schema": "shibuya.bench/wom/replay/1",
        "by_vocab_scope_field": out,
        "tapes": per_tape,
        "us_per_extraction_nondeterministic": round(1e6 * t_total / max(1, n_total), 2),
        "note": ("記憶 第 1 段のリプレイと同じ 17 本(v1 15 本・v2 2 本)。範囲: conversation_turn=会話ターンの呼"
                 "(エンジンが抽出する呼)・talk_to_person=行動「会話」で対象が P-<id>・all=全部の応答。欄: comment="
                 "「ひと言」(v1/v2 の規則)・reason_target=理由+対象(v3 の規則をこのテープに当てた代理)。"
                 "発話の割合の分母=その範囲・その欄の呼(欄が空/「なし」の呼を含む)。"),
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                              newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="D-120 7b(会話からの店の抽出)の計測")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("bytecheck", "bytecheck-one", "on", "one", "replay"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        if name in ("bytecheck", "on", "replay"):
            sp.add_argument("--out", required=True)
        if name == "bytecheck":
            sp.add_argument("--head-src", required=True)
            sp.add_argument("--scratch", required=True)
        if name == "bytecheck-one":
            sp.add_argument("--config", required=True, choices=tuple(BYTE_CONFIGS))
            sp.add_argument("--tape", required=True)
        if name == "one":
            sp.add_argument("--config", required=True, choices=tuple(CONFIGS))
        if name == "replay":
            sp.add_argument("--tape-root", default="data/tape")
            sp.add_argument("--limit-tapes", type=int, default=0)
    args = ap.parse_args(argv)
    return {"bytecheck": cmd_bytecheck, "bytecheck-one": cmd_bytecheck_one, "on": cmd_on, "one": cmd_one,
            "replay": cmd_replay}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
