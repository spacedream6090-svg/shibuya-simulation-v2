"""C10 8a(関係辺の表と導出)の計測。

使い方(リポジトリの根から)::

    # τ_rel の逆算(W16+W17 の全母集団で機械的初期化 → 体ごとの 15 番目の辺の A の中央値)
    python docs/bench/analysis/c10-relations-2026-09-28/rel_measure.py tau \\
        --out docs/bench/analysis/c10-relations-2026-09-28/rel_tau.json
    # 既定の byte 一致(HEAD e392d19 の git archive と作業木)
    python docs/bench/analysis/c10-relations-2026-09-28/rel_measure.py bytecheck \\
        --head-src <HEAD を展開した src> --scratch <作業用の場所> \\
        --out docs/bench/analysis/c10-relations-2026-09-28/rel_byte_check.json
    # on の腕(1 構成=1 プロセス)
    python docs/bench/analysis/c10-relations-2026-09-28/rel_measure.py arms \\
        --out docs/bench/analysis/c10-relations-2026-09-28/rel_arms.json
    # 実 LLM テープ 17 本のリプレイ(会話の応答で相手 P-<id> → 1 日の辺の変化)
    python docs/bench/analysis/c10-relations-2026-09-28/rel_measure.py replay \\
        --out docs/bench/analysis/c10-relations-2026-09-28/rel_replay.json
    # B5 近接行の「(知人)」の印の出現(関係 on の mock / classical・描画ごと)
    python docs/bench/analysis/c10-relations-2026-09-28/rel_measure.py marks \\
        --out docs/bench/analysis/c10-relations-2026-09-28/rel_marks.json
    # 全母集団の初期網の監査(種別の内訳・体の種別ごとの次数・次数 0 の内訳)
    python docs/bench/analysis/c10-relations-2026-09-28/rel_measure.py audit-full \\
        --out docs/bench/analysis/c10-relations-2026-09-28/rel_audit_full.json

- ``tau``: 全母集団(390,067 体)と 5,000 体の抽出で ``relations.initial_edges(tau=None)`` → A(ラン開始時と 1 日の
  終わり)→ ``tau_from_edges``。τ ごとの「体あたりの辺の中央値・15 本の体の割合・5 本以上の割合」の曲線。
- ``bytecheck``: 構成 4 本(v3 既定・classical・記憶 on・classical+記憶 on=関係 off)+関係 on(mock v3)× 源 2 本。
- ``arms``: mock 5,000・seed 1・v3・energy・``--memory on`` の上で 関係 off / on / 密度 ×0.5・×2 / τ −1.6・−0.6 /
  d 0.25・0.75 / k 5・50 / 3 人会話。関係の 6 欄を混ぜない final が関係 off と一致するか(書くだけ)。
- ``audit-full``: 全母集団で ``initial_edges``(既定 τ −1.1)を 1 回 → 辺の種別の内訳・体の種別(W16 ``kind``)ごとの
  次数の分布・次数 0 の体の内訳(世帯の相手/組織/学校の有無)。
- ``marks``: ``Renderer._nearby_items`` を包み、(体, tick) ごとに近接行の人物の数と「(知人)」の数を数える
  (同じ (体, tick) の 2 回目の呼=顕著性の計算は数えない)。関係 off の腕=近接行の人物の数の基準。
- ``replay``: テープの応答(行動「会話」で対象が ``P-<id>``)を体 × 相手の組として数える(結果はテープに無い=符号は
  出さない・成立の数でなく「会話を向けた相手」の数)。

絶対パスは書かない。壁時計は決定論でない。
"""

from __future__ import annotations

import argparse
import glob
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
BASE = {"vocab_version": "v3", "memory": "on"}
ARMS: dict[str, dict[str, Any]] = {
    "relations_off": {},
    "relations_on": {"relations": "on"},
    "density_0.5": {"relations": "on", "rel_init_density": 0.5},
    "density_2.0": {"relations": "on", "rel_init_density": 2.0},
    "tau_-1.6": {"relations": "on", "rel_tau": -1.6},
    "tau_-0.6": {"relations": "on", "rel_tau": -0.6},
    "d_0.25": {"relations": "on", "rel_d": 0.25},
    "d_0.75": {"relations": "on", "rel_d": 0.75},
    "k_5": {"relations": "on", "rel_k": 5},
    "k_50": {"relations": "on", "rel_k": 50},
    "conv3_off": {"conv_max_participants": 3},
    "conv3_on": {"relations": "on", "conv_max_participants": 3},
    "classical_off": {"policy": "classical", "chooser": "classical"},
    "classical_on": {"relations": "on", "policy": "classical", "chooser": "classical"},
}
OFF_OF = {"conv3_on": "conv3_off", "classical_on": "classical_off"}
BYTE_CONFIGS: dict[str, dict[str, Any]] = {
    "v3_default": {"vocab_version": "v3"},
    "v3_classical": {"vocab_version": "v3", "policy": "classical", "chooser": "classical"},
    "v3_memory_on": {"vocab_version": "v3", "memory": "on"},
    "v3_classical_memory_on": {"vocab_version": "v3", "memory": "on", "policy": "classical", "chooser": "classical"},
    "v3_relations_on": {"vocab_version": "v3", "memory": "on", "relations": "on"},
}
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
    ex = tuple(getattr(S, "RELATION_FIELDS", ()))

    def patched(agent_state: Any) -> str:
        if getattr(agent_state, "relation_columns", False):
            rec.append(agent_state.registry.state_hash(exclude=ex))
        return orig(agent_state)

    S.AgentState.state_hash = patched  # type: ignore[method-assign]


# ------------------------------------------------------------------ tau
def cmd_tau(args: argparse.Namespace) -> int:
    from shibuya.agents.population import load_population, sample_population
    from shibuya.agents.weekly import load_weekly
    from shibuya.engine import relations as RL

    full = load_population(args.world, n=None, seed=1)
    wk = load_weekly(args.world)
    out: dict[str, Any] = {"schema": "shibuya.bench/c10-relations/tau/1", "rows": {}}
    for label, n in (("sample_5000_seed1", 5000), ("full_population", None)):
        pop = full if n is None else sample_population(full, n, 1)
        w = wk.restrict_to(pop.source_agent_id)
        t0 = time.perf_counter()
        init = RL.initial_edges(pop, w, pop.n, tau=None)
        secs = time.perf_counter() - t0
        row: dict[str, Any] = {"agents": int(pop.n), "edges_before_tau": int(init.u.size), "audit": init.audit,
                               "init_seconds_nondeterministic": round(secs, 1)}
        for when, tick in (("start_of_day", 0), ("end_of_day", 1439)):
            A = RL._activation(init.n, init.first, tick, 1.0, RL.REL_D)
            row[f"tau_{when}"] = RL.tau_from_edges(init.u, A, pop.n)
        A0 = RL._activation(init.n, init.first, 0, 1.0, RL.REL_D)
        vals, cnt = np.unique(np.round(A0, 4), return_counts=True)
        row["A_levels_start"] = {str(float(v)): int(c) for v, c in zip(vals[-12:], cnt[-12:])}
        row["n_levels"] = dict(Counter(np.asarray(init.n).tolist()).most_common(10))
        curve = {}
        for tau in (-3.0, -2.0, -1.6, -1.2, -1.1, -1.05, -1.0, -0.6):
            keep = A0 >= tau
            per = np.bincount(init.u[keep], minlength=pop.n)
            curve[str(tau)] = {"median_edges": float(np.median(per)), "share_15": round(float((per >= 15).mean()), 4),
                               "share_5": round(float((per >= 5).mean()), 4), "share_0": round(float((per == 0).mean()), 4)}
        row["curve_at_start"] = curve
        per = np.bincount(init.u, minlength=pop.n)
        row["edges_per_agent_hist"] = {str(i): int(c) for i, c in enumerate(np.bincount(per).tolist())}
        out["rows"][label] = row
        print(label, row["tau_start_of_day"]["tau"], row["tau_end_of_day"]["tau"], round(secs, 1), flush=True)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ bytecheck
def cmd_bytecheck_one(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from shibuya import cli

    rec: list[str] = []
    _patch_state_hash(rec)
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape,
                  **BYTE_CONFIGS[args.config])
    calls = pq.read_table(Path(args.tape) / "calls.parquet")
    blocks = pq.read_table(Path(args.tape) / "blocks.parquet")
    print(json.dumps({
        "config": args.config, "final": res.final_hash[:16], "final_wo_relations": _final_wo(res, rec)[:16],
        "calls": int(res.llm_calls), "blocks_rows": int(blocks.num_rows),
        "blocks_sha": _h({n: blocks.column(n).to_pylist() for n in blocks.column_names}),
        "calls_columns_sha": {n: _h(calls.column(n).to_pylist()) for n in calls.column_names},
    }, ensure_ascii=False))
    return 0


def cmd_bytecheck(args: argparse.Namespace) -> int:
    runs = []
    scratch = Path(args.scratch)
    for name in BYTE_CONFIGS:
        pair = {}
        for side, src in (("head_e392d19", args.head_src), ("working_tree_8a", "")):
            env = dict(os.environ)
            if src:
                env["PYTHONPATH"] = src
                env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"
            if src and "relations" in BYTE_CONFIGS[name]:
                pair[side] = None  # HEAD には関係の腕が無い
                continue
            cmd = [sys.executable, str(Path(__file__)), "bytecheck-one", "--config", name, "--world", args.world,
                   "--agents", str(args.agents), "--seed", str(args.seed), "--tape", str(scratch / f"{side}_{name}")]
            got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True, env=env)
            pair[side] = json.loads(got.stdout.strip().splitlines()[-1])
        h, w = pair["head_e392d19"], pair["working_tree_8a"]
        if h is None:
            ref = next(r for r in runs if r["run"] == "v3_memory_on")["head_e392d19"]
            diff = sorted(k for k in ref["calls_columns_sha"] if ref["calls_columns_sha"][k] != w["calls_columns_sha"][k])
            row = {"run": name, **pair, "compare_to": "HEAD v3_memory_on",
                   "final_wo_relations_equals_memory_on": w["final_wo_relations"] == ref["final"],
                   "calls_equal": w["calls"] == ref["calls"], "blocks_equal": w["blocks_sha"] == ref["blocks_sha"],
                   "calls_columns_differ": diff}
        else:
            diff = sorted(k for k in h["calls_columns_sha"] if h["calls_columns_sha"][k] != w["calls_columns_sha"][k])
            row = {"run": name, **pair, "final_equal": h["final"] == w["final"], "calls_equal": h["calls"] == w["calls"],
                   "blocks_equal": (h["blocks_sha"], h["blocks_rows"]) == (w["blocks_sha"], w["blocks_rows"]),
                   "calls_columns_equal": not diff, "calls_columns_differ": diff}
        runs.append(row)
        print(name, {k: v for k, v in row.items() if k.endswith(("equal", "differ", "memory_on"))}, flush=True)
    doc = {"schema": "shibuya.bench/c10-relations/byte-check/1",
           "how": ("same runs (mock 5,000, seed 1, vocab v3, energy) with the committed source (git archive of HEAD "
                   "e392d19) and the 8a working tree; tape = shared blocks and the 14 call columns. The relations-on "
                   "run (only in the working tree) is compared to HEAD's memory-on run: the final without the 6 "
                   "relation fields must match; prompts change (B5 near line gets the 知人 marks)."),
           "runs": runs}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ arms
def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli

    rec: list[str] = []
    _patch_state_hash(rec)
    kw = {**BASE, **ARMS[args.arm]}
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
    wall = time.perf_counter() - t0
    m = res.run_manifest_fields()
    cc = dict(res.conversation_counters)
    ms = m.get("memory_summary", {})
    print(json.dumps({
        "arm": args.arm, "args": kw, "final_hash": res.final_hash, "final_wo_relations": _final_wo(res, rec),
        "llm_calls": int(res.llm_calls), "relations": m.get("relations", {}),
        "conversation": {k: v for k, v in cc.items() if k.startswith(("sessions", "session_size", "conv_"))},
        "memory_talk_events": int(ms.get("counts", {}).get("events:talk", 0)),
        "agents_bytes_total": int(res.agents.bytes_total()),  # type: ignore[attr-defined]
        "agents_declared_bytes_per_agent": int(res.agents.declared_bytes_per_agent),  # type: ignore[attr-defined]
        "wall_seconds_nondeterministic": round(wall, 2),
    }, ensure_ascii=False))
    return 0


def cmd_arms(args: argparse.Namespace) -> int:
    rows = []
    for name in ARMS:
        cmd = [sys.executable, str(Path(__file__)), "one", "--arm", name, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed)]
        got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        row = json.loads(got.stdout.strip().splitlines()[-1])
        rows.append(row)
        rs = row["relations"]
        print(f"{name}: final {row['final_hash'][:8]} wo {row['final_wo_relations'][:8]} calls {row['llm_calls']:,} "
              f"辺/体 {rs.get('edges_live_per_agent', {}).get('mean')} wall {row['wall_seconds_nondeterministic']}s",
              flush=True)
    finals = {r["arm"]: r["final_hash"] for r in rows}
    for r in rows:
        if r["relations"]:
            base = OFF_OF.get(r["arm"], "relations_off")
            r["wo_relations_equals_off"] = r["final_wo_relations"] == finals[base]
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/c10-relations/arms/1", "base": BASE, "rows": rows},
                                         ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ audit-full
def cmd_audit_full(args: argparse.Namespace) -> int:
    from shibuya.agents.population import load_population
    from shibuya.agents.state import AgentKind
    from shibuya.agents.weekly import load_weekly
    from shibuya.engine import relations as RL

    pop = load_population(args.world, n=None, seed=1)
    w = load_weekly(args.world).restrict_to(pop.source_agent_id)
    t0 = time.perf_counter()
    init = RL.initial_edges(pop, w, pop.n)
    secs = time.perf_counter() - t0
    n = int(pop.n)
    deg = np.bincount(init.u, minlength=n)
    names = {int(k): k.name for k in AgentKind}
    kinds_inv = {v: k for k, v in RL.REL_KINDS.items()}
    hh = np.asarray(pop.household_id, dtype=np.int64)
    hh_size = np.zeros(n, dtype=np.int64)
    ok = hh >= 0
    if ok.any():
        _u, inv, cnt = np.unique(hh[ok], return_inverse=True, return_counts=True)
        hh_size[ok] = cnt[inv]
    has_hh_mate = hh_size >= 2
    has_org = np.asarray(pop.org_id) >= 0
    has_school = np.asarray(pop.school_cell) >= 0
    zero = deg == 0
    by_kind = {}
    for k in np.unique(pop.kind).tolist():
        m = np.asarray(pop.kind) == k
        dk = deg[m]
        by_kind[names.get(int(k), str(k))] = {
            "agents": int(m.sum()), "mean_degree": round(float(dk.mean()), 3), "median_degree": float(np.median(dk)),
            "share_0": round(float((dk == 0).mean()), 4), "share_5_or_more": round(float((dk >= 5).mean()), 4),
            "share_15": round(float((dk >= 15).mean()), 4)}
    zk = np.asarray(pop.kind)[zero]
    indeg = np.bincount(init.v, minlength=n)
    key = init.u.astype(np.int64) * (n + 1) + init.v.astype(np.int64)
    rkey = init.v.astype(np.int64) * (n + 1) + init.u.astype(np.int64)
    recip = np.isin(rkey, key)
    in_by_kind = {}
    for kd in np.unique(init.kind).tolist():  # 種別の数ぶん
        mk = init.kind == kd
        ind = np.bincount(init.v[mk], minlength=n)
        ind = ind[ind > 0]
        in_by_kind[kinds_inv[int(kd)]] = {
            "targets": int(ind.size), "p50": float(np.median(ind)), "p99": float(np.percentile(ind, 99)),
            "max": int(ind.max()), "reciprocated_share": round(float(recip[mk].mean()), 4)}
    doc = {
        "schema": "shibuya.bench/c10-relations/audit-full/1", "agents": n, "edges": int(init.u.size),
        "init_seconds_nondeterministic": round(secs, 1), "audit": init.audit,
        "edge_kinds": {kinds_inv[int(k)]: int(c) for k, c in zip(*np.unique(init.kind, return_counts=True))},
        "degree_hist": {str(i): int(c) for i, c in enumerate(np.bincount(deg).tolist())},
        "by_agent_kind": by_kind,
        "zero_degree": {
            "agents": int(zero.sum()),
            "by_agent_kind": {names.get(int(k), str(k)): int(c) for k, c in zip(*np.unique(zk, return_counts=True))},
            "no_household_mate_no_org_no_school": int((zero & ~has_hh_mate & ~has_org & ~has_school).sum()),
            "has_org_or_school_but_no_edge": int((zero & (has_org | has_school)).sum()),
            "has_household_mate_but_no_edge": int((zero & has_hh_mate).sum()),
        },
        "n_levels": {str(k): int(c) for k, c in Counter(np.asarray(init.n).tolist()).most_common(12)},
        # 入次数(自分を辺に持つ体の数)と相互性(u→v に対して v→u もあるか)=有向の表の偏り
        "in_degree": {
            "p50": float(np.median(indeg)), "p90": float(np.percentile(indeg, 90)),
            "p99": float(np.percentile(indeg, 99)), "p999": float(np.percentile(indeg, 99.9)),
            "max": int(indeg.max()), "agents_with_in_degree_over_100": int((indeg > 100).sum()),
            "share_of_edges_to_top_1pct": round(float(np.sort(indeg)[::-1][: max(1, n // 100)].sum() / max(1, indeg.sum())), 4),
        },
        "reciprocated_share": round(float(recip.mean()), 4),
        "in_degree_by_edge_kind": in_by_kind,
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n",
                              encoding="utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("agents", "edges", "edge_kinds", "zero_degree", "in_degree",
                                          "reciprocated_share", "in_degree_by_edge_kind")}, ensure_ascii=False))
    return 0


# ------------------------------------------------------------------ marks
MARK_ARMS = {"mock_off": {}, "mock_on": {"relations": "on"},
             "classical_off": {"policy": "classical", "chooser": "classical"},
             "classical_on": {"relations": "on", "policy": "classical", "chooser": "classical"}}


def cmd_marks_one(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.perception import renderer as RM
    from shibuya.perception import templates as T

    known_mark = f"({T.NEAR_PERSON_MARKS[1]})"
    seen: dict[tuple[int, int], tuple[int, int]] = {}
    orig = RM.Renderer._nearby_items

    def wrapped(self: Any, i: int, cell: int, tc: Any) -> list[tuple[str, float]]:
        out = orig(self, i, cell, tc)
        key = (int(i), int(tc.tick))
        if key not in seen:
            seen[key] = (len(out), sum(1 for s, _d in out if s.endswith(known_mark)))
        return out

    RM.Renderer._nearby_items = wrapped  # type: ignore[method-assign]
    kw = {**BASE, **MARK_ARMS[args.arm]}
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
    v = np.asarray(list(seen.values()), dtype=np.int64).reshape(-1, 2)
    n_items, n_known = v[:, 0], v[:, 1]
    print(json.dumps({
        "arm": args.arm, "args": kw, "final_hash": res.final_hash, "llm_calls": int(res.llm_calls),
        "renders": int(v.shape[0]),
        "renders_with_any_person": int((n_items > 0).sum()),
        "renders_with_known_mark": int((n_known > 0).sum()),
        "share_of_renders_with_known_mark": round(float((n_known > 0).mean()) if v.size else 0.0, 5),
        "share_of_person_renders_with_known_mark": round(
            float((n_known > 0).sum() / max(1, int((n_items > 0).sum()))), 5),
        "persons_total": int(n_items.sum()), "known_marks_total": int(n_known.sum()),
        "known_per_render_hist": {str(k): int(c) for k, c in enumerate(np.bincount(n_known).tolist())},
    }, ensure_ascii=False))
    return 0


def cmd_marks(args: argparse.Namespace) -> int:
    rows = []
    for name in MARK_ARMS:
        cmd = [sys.executable, str(Path(__file__)), "marks-one", "--arm", name, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed)]
        got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        row = json.loads(got.stdout.strip().splitlines()[-1])
        rows.append(row)
        print(name, row["renders"], row["renders_with_known_mark"], row["share_of_renders_with_known_mark"], flush=True)
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/c10-relations/marks/1", "base": BASE,
                                          "rows": rows}, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ replay
def cmd_replay(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from shibuya.core.types import EventClass
    from shibuya.llm.parser import parse_two_line

    unique = json.loads(UNIQUE.read_text(encoding="utf-8"))["unique"]["tapes"]
    rows = []
    tot: Counter = Counter()
    per_agent_new: list[int] = []
    for name in unique:
        run, arm = name.split("/")
        ver = "v2" if arm.endswith("_v2") else "v1"
        t = pq.read_table(Path(args.tape_root) / run / arm / "calls.parquet",
                          columns=["agent_id", "wake_class", "response", "deferred"]).to_pydict()
        seen: set[tuple[int, int]] = set()
        c: Counter = Counter()
        agents: set[int] = set()
        new_by_agent: Counter = Counter()
        for k in range(len(t["agent_id"])):  # 逐次: 呼ごと(計測の道具)
            if t["deferred"][k] or not t["response"][k]:
                continue
            aid = int(t["agent_id"][k])
            agents.add(aid)
            pr = parse_two_line(t["response"][k], ver)
            c["responses"] += 1
            if pr.action != "会話":
                continue
            c["talk_responses"] += 1
            m = PERSON_RE.match(str(getattr(pr.target, "raw", "") or "").strip())
            if not m:
                c["talk_without_person"] += 1
                continue
            pid = int(m.group(1))
            c["talk_to_person"] += 1
            c["talk_to_person_conversation_turn" if int(t["wake_class"][k]) == int(EventClass.CONVERSATION)
              else "talk_to_person_other"] += 1
            key = (aid, pid)
            if key in seen:
                c["edge_merge"] += 1
            else:
                seen.add(key)
                c["edge_new"] += 1
                new_by_agent[aid] += 1
        per = [new_by_agent[a] for a in agents]
        per_agent_new += per
        rows.append({"tape": name, "vocab": ver, "agents": len(agents), "counts": dict(c),
                     "new_edges_per_agent_mean": round(float(np.mean(per)) if per else 0.0, 4),
                     "talk_share_of_responses": round(c["talk_responses"] / max(1, c["responses"]), 5)})
        tot.update(c)
        print(name, dict(c), flush=True)
    a = np.asarray(per_agent_new, dtype=np.float64)
    doc = {"schema": "shibuya.bench/c10-relations/replay/1", "tapes": rows,
           "all": {"counts": dict(tot), "agent_days": int(a.size),
                   "new_edges_per_agent_day": {"mean": round(float(a.mean()), 4) if a.size else 0.0,
                                               "p99": float(np.percentile(a, 99)) if a.size else 0.0,
                                               "max": float(a.max()) if a.size else 0.0,
                                               "share_with_any": round(float((a > 0).mean()), 5) if a.size else 0.0},
                   "talk_share_of_responses": round(tot["talk_responses"] / max(1, tot["responses"]), 5)},
           "note": ("17 本(記憶 第 1 段と同じ内容で束ねた集合)。辺の変化=行動「会話」で対象が P-<id> の応答の体 × 相手の"
                    "組(初出=新しい辺・2 回目以降=統合)。結果(成立/断られた)はテープに無い=符号は出さない。")}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="C10 8a の計測")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("tau", "bytecheck", "bytecheck-one", "arms", "one", "replay", "marks", "marks-one", "audit-full"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        if name not in ("bytecheck-one", "one", "marks-one"):
            sp.add_argument("--out", required=True)
        if name == "bytecheck":
            sp.add_argument("--head-src", required=True)
            sp.add_argument("--scratch", required=True)
        if name == "bytecheck-one":
            sp.add_argument("--config", required=True, choices=tuple(BYTE_CONFIGS))
            sp.add_argument("--tape", required=True)
        if name == "one":
            sp.add_argument("--arm", required=True, choices=tuple(ARMS))
        if name == "marks-one":
            sp.add_argument("--arm", required=True, choices=tuple(MARK_ARMS))
        if name == "replay":
            sp.add_argument("--tape-root", default="data/tape")
    args = ap.parse_args(argv)
    return {"tau": cmd_tau, "bytecheck": cmd_bytecheck, "bytecheck-one": cmd_bytecheck_one, "arms": cmd_arms,
            "one": cmd_one, "replay": cmd_replay, "marks": cmd_marks, "marks-one": cmd_marks_one,
            "audit-full": cmd_audit_full}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
