"""D-120 7a(店の評価の記憶)の計測。

使い方(リポジトリの根から)::

    # 既定(--store-memory off)の byte 一致: コミット済みの源(git archive HEAD を展開した src)と作業木で
    # 同じランを回し、テープ(描画ブロック・呼の行)を列ごとにハッシュして突き合わせる
    python docs/bench/analysis/store-memory-2026-09-28/store_measure.py bytecheck \\
        --head-src <HEAD を展開した src> --scratch <作業用の場所> \\
        --out docs/bench/analysis/store-memory-2026-09-28/store_byte_check.json
    # on の腕(1 構成=1 プロセス)
    python docs/bench/analysis/store-memory-2026-09-28/store_measure.py on \\
        --out docs/bench/analysis/store-memory-2026-09-28/store_on_arms.json
    # 実 LLM テープ 17 本(記憶 第 1 段と同じ内容で束ねた集合)のリプレイ
    python docs/bench/analysis/store-memory-2026-09-28/store_measure.py replay \\
        --out docs/bench/analysis/store-memory-2026-09-28/store_replay.json

- ``bytecheck``: 構成 4 本(v3 既定・classical・親しみの表 on・**記憶 on**(店は off))× 源 2 本(HEAD 1ec86fd /
  作業木)。比べるもの: final・呼数・``blocks.parquet`` の中身・``calls.parquet`` の 14 列(列ごと)。
- ``on``: 構成ごとに別プロセス。final と、店の 7 欄を混ぜない final(=記憶 on の腕と同じはず)と、記憶の 9 欄
  と店の 7 欄を混ぜない final(=off と同じはず)。壁時計・ピークの作業セット(Windows ``K32GetProcessMemoryInfo``)・
  店の書き手に掛かった時間(``perf_counter`` の積算)。**壁時計と RSS と時間の積算は決定論でない**。
- ``replay``: テープの呼を tick 順に辿り、店の評価の表(``engine.store_memory.StoreMemory`` をそのまま使う)を
  応答から組み立てる。自分の訪問=購入/食事/並ぶの応答の対象を**エンジンと同じ段 2a の解決**
  (``engine.poi_target.TargetResolver.resolve``・既定の選び手 nearest・現在セル=B2 のセル)で店に直す。
  近似(宣言): **結果はテープに無い**ので、解決できた店は +1(満席の落選・遠すぎは見えない=+1 側に寄る)・
  セルの候補が全部閉店/在庫切れで代表の店を返した行は −1(閉店・在庫切れ)・候補の無い行(対象不正・
  飲食店にいない・名指しの店がセル外=段 2c の歩く意図は再現しない)は行を作らない・営業時間は W7 の単一区間・
  在庫は初期値。看板=B2 に載った看板の POI の初見(記憶の表の初見と同じ=1 日では追い出しが無い)。

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

import numpy as np

HERE = Path(__file__).resolve().parent
UNIQUE = HERE.parent / "memory-stage1-2026-09-28" / "replay.json"
CONFIGS: dict[str, dict[str, Any]] = {
    "off": {"vocab_version": "v3"},
    "memory_on": {"vocab_version": "v3", "memory": "on"},
    "store_on": {"vocab_version": "v3", "memory": "on", "store_memory": "on"},
    "store_n16": {"vocab_version": "v3", "memory": "on", "store_memory": "on", "store_memory_n": 16},
    "store_n64": {"vocab_version": "v3", "memory": "on", "store_memory": "on", "store_memory_n": 64},
    "store_sigma_1_1_1_1": {"vocab_version": "v3", "memory": "on", "store_memory": "on",
                            "store_sigma": '{"self": 1, "wom": 1, "signage": 1, "net": 1}'},
    "store_sigma_1_4_16_4": {"vocab_version": "v3", "memory": "on", "store_memory": "on",
                             "store_sigma": '{"self": 1, "wom": 4, "signage": 16, "net": 4}'},
    "store_decay_ga": {"vocab_version": "v3", "memory": "on", "store_memory": "on", "store_decay": "ga"},
    "store_decay_citysim": {"vocab_version": "v3", "memory": "on", "store_memory": "on",
                            "store_decay": "citysim"},
    "store_familiarity": {"vocab_version": "v3", "memory": "on", "store_memory": "on", "familiarity": "on"},
    "memory_classical": {"vocab_version": "v3", "memory": "on", "policy": "classical",
                         "chooser": "classical"},
    "store_classical": {"vocab_version": "v3", "memory": "on", "store_memory": "on", "policy": "classical",
                        "chooser": "classical"},
    "off_classical": {"vocab_version": "v3", "policy": "classical", "chooser": "classical"},
}
#: 店の欄を混ぜない final が一致すべき腕(記憶 on・店 off)と、記憶も店も混ぜない final が一致すべき腕(off)。
MEMORY_BASE = {"store_classical": "memory_classical"}
OFF_BASE = {"store_classical": "off_classical", "memory_classical": "off_classical"}
BYTE_CONFIGS: dict[str, dict[str, Any]] = {
    "v3_default": {"vocab_version": "v3"},
    "v3_classical": {"vocab_version": "v3", "policy": "classical", "chooser": "classical"},
    "v3_familiarity": {"vocab_version": "v3", "familiarity": "on"},
    "v3_memory_on": {"vocab_version": "v3", "memory": "on"},
}
PLACE_RE = re.compile(r"現在地はセル([^\s()()]+)")
SIGNAGE_SHOWN = "[B2 看板] 〔素性"
SHOP_ACTIONS = ("購入", "食事", "並ぶ")


def _peak_working_set_bytes() -> int:
    try:
        import ctypes
        import ctypes.wintypes as wt

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.GetCurrentProcess.restype = wt.HANDLE
        f = k32.K32GetProcessMemoryInfo
        f.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
        f.restype = wt.BOOL
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        if not f(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
            return -1
        return int(pmc.PeakWorkingSetSize)
    except Exception:  # noqa: BLE001
        return -1


def _q(x: Any) -> dict[str, float]:
    a = np.asarray(list(x), dtype=np.float64)
    if a.size == 0:
        return {}
    return {p: round(float(np.percentile(a, float(p[1:]))), 3)
            for p in ("p10", "p50", "p90", "p99", "p100")} | {"mean": round(float(a.mean()), 3)}


def _h(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:16]


# ------------------------------------------------------------------ bytecheck
def cmd_bytecheck_one(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from shibuya import cli

    kw = dict(BYTE_CONFIGS[args.config])
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape, **kw)
    calls = pq.read_table(Path(args.tape) / "calls.parquet")
    blocks = pq.read_table(Path(args.tape) / "blocks.parquet")
    out = {
        "config": args.config, "final": res.final_hash[:16], "calls": int(res.llm_calls),
        "calls_rows": int(calls.num_rows), "blocks_rows": int(blocks.num_rows),
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
        for side, src in (("head_1ec86fd", args.head_src), ("working_tree_7a", "")):
            env = dict(os.environ)
            if src:
                env["PYTHONPATH"] = src
                env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"
            tape = scratch / f"{side}_{name}"
            cmd = [sys.executable, str(Path(__file__)), "bytecheck-one", "--config", name, "--world",
                   args.world, "--agents", str(args.agents), "--seed", str(args.seed), "--tape", str(tape)]
            got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True, env=env)
            pair[side] = json.loads(got.stdout.strip().splitlines()[-1])
        h, w = pair["head_1ec86fd"], pair["working_tree_7a"]
        row = {"run": name, **pair,
               "final_equal": h["final"] == w["final"], "calls_equal": h["calls"] == w["calls"],
               "blocks_equal": (h["blocks_sha"], h["blocks_rows"]) == (w["blocks_sha"], w["blocks_rows"]),
               "calls_columns_equal": h["calls_columns_sha"] == w["calls_columns_sha"]}
        runs.append(row)
        print(f"{name}: final {row['final_equal']} calls {row['calls_equal']} blocks {row['blocks_equal']} "
              f"calls 列 {row['calls_columns_equal']}", flush=True)
    doc = {"schema": "shibuya.bench/store-memory-byte-check/1",
           "how": ("same runs (mock 5,000, seed 1, vocab v3, energy, --store-memory off) with the committed "
                   "source (git archive of HEAD 1ec86fd) and with the 7a working tree; tape = shared prompt "
                   "blocks (blocks.parquet) and call rows (calls.parquet: all 14 columns hashed column by "
                   "column; prompt_hash = the whole prompt text B0-B6). The memory-on arm (store off) is "
                   "included: the store table must not touch the episode table, the prompts or the tape."),
           "runs": runs}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                              newline="\n")
    return 0


# ------------------------------------------------------------------ on(1 構成=1 プロセス)
def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.agents import state as S
    from shibuya.core.hashing import blake3_hex
    from shibuya.engine import store_memory as SM

    kw = dict(CONFIGS[args.config])
    rec_store: list[str] = []
    rec_all: list[str] = []
    orig = S.AgentState.state_hash

    def patched(agent_state: Any) -> str:
        if getattr(agent_state, "memory_columns", False):
            ex = S.STORE_MEMORY_FIELDS if getattr(agent_state, "store_memory_columns", False) else ()
            rec_store.append(agent_state.registry.state_hash(exclude=ex))
            rec_all.append(agent_state.registry.state_hash(exclude=S.MEMORY_FIELDS + ex))
        return orig(agent_state)

    S.AgentState.state_hash = patched  # type: ignore[method-assign]
    timers = {"store_s": 0.0, "store_calls": 0}
    o_ep = SM.StoreMemory.on_episodes

    def t_ep(self: Any, *a: Any, **k: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return o_ep(self, *a, **k)
        finally:
            timers["store_s"] += time.perf_counter() - t0
            timers["store_calls"] += 1

    SM.StoreMemory.on_episodes = t_ep  # type: ignore[method-assign]
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
    wall = time.perf_counter() - t0

    def final_of(rec: list[str]) -> str:
        if not rec or len(rec) != len(res.checkpoints):
            return ""
        cp = res.checkpoints[-1]
        parts = [rec[-1], cp.world_hash, cp.population_hash, cp.schedule_hash]
        if cp.activity_hash:
            parts.append(cp.activity_hash)
        return blake3_hex("\x1f".join(parts).encode("utf-8"))

    m = res.run_manifest_fields()
    ms = m.get("memory_summary", {})
    out = {
        "config": args.config, "args": kw, "final_hash": res.final_hash,
        "final_wo_store": final_of(rec_store), "final_wo_memory_and_store": final_of(rec_all),
        "llm_calls": int(res.llm_calls),
        "agents_bytes_total": int(res.agents.bytes_total()),  # type: ignore[attr-defined]
        "agents_declared_bytes_per_agent": int(res.agents.declared_bytes_per_agent),  # type: ignore[attr-defined]
        "store_memory_summary": m.get("store_memory_summary", {}),
        "memory_counts": ms.get("counts", {}),
        "time_in_store_writer_seconds_nondeterministic": round(timers["store_s"], 3),
        "store_writer_calls": int(timers["store_calls"]),
        "wall_seconds_nondeterministic": round(wall, 2),
        "peak_working_set_bytes_nondeterministic": _peak_working_set_bytes(),
    }
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
        s = row["store_memory_summary"]
        print(f"{name}: final {row['final_hash'][:8]} wo_store {row['final_wo_store'][:8]} "
              f"wo_all {row['final_wo_memory_and_store'][:8]} calls {row['llm_calls']:,} "
              f"行/体 {s.get('rows_used_per_agent', {}).get('mean')} wall {row['wall_seconds_nondeterministic']}s",
              flush=True)
    finals = {r["config"]: r["final_hash"] for r in rows}
    for r in rows:
        if r["config"].startswith("store_"):
            mb = MEMORY_BASE.get(r["config"], "memory_on")
            if r["config"] == "store_familiarity":
                mb = ""  # 親しみの表つきの記憶 on の腕は回していない(off 側だけ比べる)
            if mb:
                r["wo_store_equals_memory_on"] = r["final_wo_store"] == finals[mb]
            ob = OFF_BASE.get(r["config"], "off")
            if r["config"] != "store_familiarity":
                r["wo_memory_and_store_equals_off"] = r["final_wo_memory_and_store"] == finals[ob]
        elif r["config"] in ("memory_on", "memory_classical"):
            r["wo_memory_equals_off"] = r["final_wo_memory_and_store"] == finals[OFF_BASE.get(r["config"], "off")]
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/store-memory/on/1", "rows": rows},
                                         ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ replay
def cmd_replay(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from types import SimpleNamespace

    from shibuya.agents.state import AgentState
    from shibuya.engine import commit as C
    from shibuya.engine import store_memory as SM
    from shibuya.engine.chooser import NearestChooser
    from shibuya.engine.poi_target import TargetResolver
    from shibuya.llm.parser import parse_two_line
    from shibuya.perception.renderer import PerceptionAssets
    from shibuya.world.state import World

    world = World.load_or_synthetic(args.world, n_cells=139, seed=1)
    passets = PerceptionAssets.load_or_synthetic(args.world, world)
    place_ids = [str(p) for p in passets.place_ids]
    cell_of = {p: i for i, p in enumerate(place_ids)}
    sign_poi = np.full(world.n_cells, -1, dtype=np.int64)
    for c in range(world.n_cells):
        for j in passets.visible_poi[c]:
            if int(j) < world.n_poi:
                sign_poi[c] = int(j)
                break
    code_of = {"購入": C.ACT_BUY, "食事": C.ACT_EAT, "並ぶ": C.ACT_QUEUE}
    unique = json.loads(UNIQUE.read_text(encoding="utf-8"))["unique"]["tapes"]
    if args.limit_tapes:
        unique = unique[: args.limit_tapes]
    out_rows = []
    agg: dict[str, list[float]] = defaultdict(list)
    agg_c: Counter = Counter()
    for name in unique:
        run, arm = name.split("/")
        tdir = Path(args.tape_root) / run / arm
        ver = "v2" if arm.endswith("_v2") else "v1"
        blocks = pq.read_table(tdir / "blocks.parquet", columns=["block_id", "text"]).to_pydict()
        cell_by_block: dict[str, int] = {}
        sign_by_block: dict[str, bool] = {}
        for bid, tx in zip(blocks["block_id"], blocks["text"]):
            if "[B2 場所]" in tx:
                m = PLACE_RE.search(tx)
                if m and m.group(1) in cell_of:
                    cell_by_block[bid] = cell_of[m.group(1)]
                sign_by_block[bid] = SIGNAGE_SHOWN in tx
        t = pq.read_table(tdir / "calls.parquet",
                          columns=["agent_id", "tick", "response", "deferred", "block_ids"]).to_pydict()
        n_agents = int(max(t["agent_id"])) + 1
        a = AgentState(n_agents, store_memory_columns=True, store_memory_n=SM.STORE_MEMORY_N)
        st = SM.StoreMemory(n_agents, SM.STORE_MEMORY_N, minutes_per_tick=1.0)
        resolver = TargetResolver(world, NearestChooser(), seed=1)
        fake = SimpleNamespace(registry=SimpleNamespace(
            cell=np.full(n_agents, -1, dtype=np.int64), node=np.full(n_agents, -1, dtype=np.int64),
            hunger=np.full(n_agents, 5, dtype=np.int64), arrays={}))
        seen_sign: set[tuple[int, int]] = set()
        agents_seen: set[int] = set()
        c: Counter = Counter()
        for k in range(len(t["agent_id"])):  # 逐次: 呼ごと(計測の道具・エンジンではない)
            if t["deferred"][k]:
                continue
            aid = int(t["agent_id"][k])
            tick = int(t["tick"][k])
            agents_seen.add(aid)
            bids = t["block_ids"][k]
            b2 = next((b for b in bids if b in cell_by_block), None)
            cell = cell_by_block[b2] if b2 else -1
            ev_a: list[int] = []
            ev_p: list[int] = []
            ev_v: list[int] = []
            ev_b: list[int] = []
            resp = t["response"][k]
            if resp:
                pr = parse_two_line(resp, ver)
                if pr.action in SHOP_ACTIONS and cell >= 0:
                    c["shop_responses"] += 1
                    fake.registry.cell[aid] = cell
                    code = int(code_of[pr.action])
                    before = Counter(resolver.stats)
                    j = int(resolver.resolve(
                        fake, tick, np.asarray([aid]), np.asarray([code]), [pr.target],
                        is_eat=np.asarray([pr.action == "食事"]),
                        is_buy_like=np.asarray([pr.action != "食事"]),
                    )[0])
                    diff = Counter(resolver.stats) - before
                    c["shop_named_target"] += int(diff.get("attempts:named", 0) > 0)
                    if j >= 0:
                        fail = diff.get("no_candidate:closed", 0) + diff.get("no_candidate:out_of_stock", 0)
                        c["shop_resolved_failure" if fail else "shop_resolved_ok"] += 1
                        ev_a.append(aid)
                        ev_p.append(j)
                        ev_v.append(-1 if fail else 1)
                        ev_b.append(SM.STORE_SOURCE_BIT["self"])
                    else:
                        c["shop_no_candidate"] += 1
                        for kk, vv in diff.items():
                            if kk.startswith("no_candidate:"):
                                c["shop_" + kk] += int(vv)
            if b2 and sign_by_block.get(b2) and cell >= 0 and sign_poi[cell] >= 0:
                key = (aid, int(sign_poi[cell]))
                if key not in seen_sign:
                    seen_sign.add(key)
                    c["signage_first"] += 1
                    ev_a.append(aid)
                    ev_p.append(int(sign_poi[cell]))
                    ev_v.append(0)
                    ev_b.append(SM.STORE_SOURCE_BIT["signage"])
            if ev_a:
                st.write(a, tick, np.asarray(ev_a), np.asarray(ev_p), np.asarray(ev_v), np.asarray(ev_b))
        ag = np.asarray(sorted(agents_seen), dtype=np.int64)
        summ = st.summary(a, 1_439, -2.0)
        used = a.sm_poi[ag] != -1
        src = a.sm_source[ag].astype(np.int64)
        sign = np.sign(a.sm_valence[ag])
        per = {
            "rows": used.sum(axis=1),
            "rows_self": (used & ((src & 1) > 0)).sum(axis=1),
            "rows_signage_only": (used & (src == 4)).sum(axis=1),
            "rows_valence+1": (used & (sign > 0)).sum(axis=1),
            "rows_valence-1": (used & (sign < 0)).sum(axis=1),
            "rows_valence0": (used & (sign == 0)).sum(axis=1),
        }
        row = {"tape": name, "vocab": ver, "agents_with_calls": int(ag.size), "counts": dict(c),
               "per_agent_day": {k: _q(v.tolist()) for k, v in per.items()},
               "rows_by_source": summ["rows_by_source"], "valence_sign": summ["valence_sign"],
               "precision": summ["precision"], "recallable_share_end_of_day": summ["recallable_share"],
               "distinct_pois_known": summ["distinct_pois_known"], "full_agents": summ["full_agents"],
               "evictions": summ["counts"].get("evictions", 0)}
        out_rows.append(row)
        for kk, v in per.items():
            agg[kk] += v.tolist()
        agg_c.update(c)
        print(f"{name}: 体 {ag.size} 行/体 {per['rows'].mean():.2f}(自分 {per['rows_self'].mean():.2f}・"
              f"看板だけ {per['rows_signage_only'].mean():.2f})店に直せた {c['shop_resolved_ok']}+"
              f"{c['shop_resolved_failure']}/{c['shop_responses']}", flush=True)
    doc = {
        "schema": "shibuya.bench/store-memory/replay/1",
        "tapes": out_rows,
        "all": {"agent_days": len(agg["rows"]), "counts": dict(agg_c),
                "shop_resolved_share": round((agg_c["shop_resolved_ok"] + agg_c["shop_resolved_failure"])
                                             / max(1, agg_c["shop_responses"]), 4),
                "shop_failure_share_of_resolved": round(
                    agg_c["shop_resolved_failure"]
                    / max(1, agg_c["shop_resolved_ok"] + agg_c["shop_resolved_failure"]), 4),
                **{k: _q(v) for k, v in agg.items()}},
        "note": ("記憶 第 1 段のリプレイと同じ 17 本(内容で束ねた集合)。体=その日に呼の在った体。自分の訪問="
                 "購入/食事/並ぶの応答の対象をエンジンと同じ段 2a の解決(TargetResolver・nearest・B2 のセル)で店に"
                 "直したもの。向き=結果はテープに無い=解決できた店は +1・候補が全部閉店/在庫切れで代表を返した行は"
                 " −1・候補なしは行を作らない(段 2c の歩く意図は再現しない)。看板=B2 に載った看板の POI の初見。"
                 "τ=−2.0 で 1 日の終わり(tick 1,439)に想起できる割合。"),
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="D-120 7a(店の評価の記憶)の計測")
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
