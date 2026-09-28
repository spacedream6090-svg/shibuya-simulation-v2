"""C10 8b(会話の起点と相手選択+8a の直し)の計測。

使い方(リポジトリの根から)::

    D=docs/bench/analysis/c10-relations-2026-09-28
    python $D/rel8b_measure.py tau --out $D/rel8b_tau.json            # τ の再逆算(全母集団・5,000 体 2 通り)
    python $D/rel8b_measure.py audit-sample --out $D/rel8b_audit_sample.json   # 5,000 体の網(既定/層化)
    python $D/rel8b_measure.py bytecheck --head-src <HEAD 3505a0f を展開した src> --scratch <作業用の場所> \\
        --out $D/rel8b_byte_check.json
    python $D/rel8b_measure.py arms --out $D/rel8b_arms.json          # on の腕(層化 5,000 体・1 構成=1 プロセス)
    python $D/rel8b_measure.py detect-cost --out $D/rel8b_detect_cost.json      # 全母集団の検出の費用
    python $D/rel8b_measure.py replay --out $D/rel8b_replay.json      # 実 LLM テープ 17 本
    python $D/rel8b_measure.py lifetimes --out $D/rel8bp_lifetimes.json   # 8b′: 辺の寿命の表(τ ごと)

8b′(第300 訂正=n の単位を「共在のあった日数」に)の記録は同じ道具で ``rel8bp_*.json`` に書く(腕の τ は 8b′ の値)。

- **層化抽出(Q94・計測の口)**: ``stratified_sample`` を ``agents.population.sample_population`` と
  ``engine.run.sample_population`` に差し込む(母集団のモジュールは触らない)。定員先取り層は既定と同じ・
  残りは体の主な組(組織 → 学校セル → 世帯(2 人以上)→ 単独)で束ね、16 人より大きい組は seed つきの順で
  16 人ずつの塊に切り、塊を seed つきの順に 5,000 体まで取る(最後の塊は途中で切る=宣言)。
- ``tau``: ``initial_edges(tau=None)`` → 体ごとの 15 番目の辺の A の中央値。τ の前後の曲線(崖でないこと)。
- ``arms``: 層化 5,000 体・seed 1・v3・energy・``--memory on``。mock と classical。呼ごとの相手選びを包んで
  T5(相手に選ばれた回数と ID の層内相関・セル内の ID 順位)・会話の終わりを包んで A1/A4 の分布を取る。
- ``detect-cost``: 全母集団で関係の表を作り、セルを動かしながら知人出現の検出と同席の書き手の 1 tick の費用。
- ``replay``: テープの「会話 → P-<id>」が初期網(ラン開始時に生きている辺)の相手だった割合。

絶対パスは書かない。壁時計は決定論でない。holdout(A1/A4)は分布を書くだけ=判定しない。
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
REPO = HERE.parents[3]
UNIQUE = HERE.parent / "memory-stage1-2026-09-28" / "replay.json"
BASE = {"vocab_version": "v3", "memory": "on"}
CLS = {"policy": "classical", "chooser": "classical"}
REL_8A = {"relations": "on", "rel_invite": "off", "rel_acq_wake": "off"}
ARMS: dict[str, tuple[str, dict[str, Any]]] = {
    # 名前: (抽出, 引数)
    "off": ("stratified", {}),
    "rel_8a_mode": ("stratified", REL_8A),
    "rel_on": ("stratified", {"relations": "on"}),
    "rel_invite_only": ("stratified", {"relations": "on", "rel_acq_wake": "off"}),
    "rel_acq_only": ("stratified", {"relations": "on", "rel_invite": "off"}),
    "rel_copresent": ("stratified", {"relations": "on", "rel_copresent": "on"}),
    # 8b′: 26 週の腕は 26 週の再逆算 −2.336・τ ±0.5=−2.846/−1.846(8b は 0.798・0.204/1.204 で回した)
    "rel_tenure26": ("stratified", {"relations": "on", "rel_tenure_weeks": 26.0, "rel_tau": -2.336}),
    "rel_tau_-0.5": ("stratified", {"relations": "on", "rel_tau": -2.846}),
    "rel_tau_+0.5": ("stratified", {"relations": "on", "rel_tau": -1.846}),
    "off_default_sample": ("default", {}),
    "rel_on_default_sample": ("default", {"relations": "on"}),
    "classical_off": ("stratified", CLS),
    "classical_8a_mode": ("stratified", {**CLS, **REL_8A}),
    "classical_on": ("stratified", {**CLS, "relations": "on"}),
    "classical_copresent": ("stratified", {**CLS, "relations": "on", "rel_copresent": "on"}),
}
WRITE_ONLY_OF = {"rel_8a_mode": "off", "classical_8a_mode": "classical_off"}
BYTE_CONFIGS: dict[str, dict[str, Any]] = {
    "v3_default": {"vocab_version": "v3"},
    "v3_classical": {"vocab_version": "v3", **CLS},
    "v3_memory_on": {"vocab_version": "v3", "memory": "on"},
    "v3_classical_memory_on": {"vocab_version": "v3", "memory": "on", **CLS},
    "v3_relations_8a_mode": {"vocab_version": "v3", "memory": "on", **REL_8A},
}
PERSON_RE = re.compile(r"^P-(\d+)$")
STRAT_CHUNK = 16


def _h(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:16]


# ------------------------------------------------------------------ 層化抽出(Q94)
def stratified_sample(pop: Any, n: int, seed: int | str = 1) -> Any:
    """世帯・組織ごとの抽出(計測の口・宣言)。同 seed 同結果・``agent_id`` 昇順。"""
    from shibuya.core.rng import stream

    n = int(n)
    if n >= pop.n:
        return pop
    reserved = np.flatnonzero(pop.reserved_mask)
    if n <= reserved.size:
        order = stream(seed, "w16.sample.reserved").permutation(reserved.size)[:n]
        return pop.take(np.sort(reserved[order]))
    rest = np.flatnonzero(~pop.reserved_mask)
    want = n - int(reserved.size)
    hh = np.asarray(pop.household_id, dtype=np.int64)
    hh_size = np.zeros(pop.n, dtype=np.int64)
    ok = hh >= 0
    if ok.any():
        _u, inv, cnt = np.unique(hh[ok], return_inverse=True, return_counts=True)
        hh_size[ok] = cnt[inv]
    org = np.asarray(pop.org_id, dtype=np.int64)[rest]
    sc = np.asarray(pop.school_cell, dtype=np.int64)[rest]
    big = np.int64(1) << np.int64(40)
    gkey = np.where(org >= 0, org, np.where(sc >= 0, big + sc,
                                             np.where(hh_size[rest] >= 2, 2 * big + hh[rest], 3 * big + rest)))
    perm = stream(seed, "rel8b.stratified.within").permutation(rest.size)
    order = np.lexsort((perm, gkey))
    sg = gkey[order]
    starts = np.flatnonzero(np.concatenate(([True], sg[1:] != sg[:-1])))
    rank = np.arange(sg.size) - np.repeat(starts, np.diff(np.append(starts, sg.size)))
    chunk = rank // STRAT_CHUNK
    ckey_new = np.concatenate(([True], (sg[1:] != sg[:-1]) | (chunk[1:] != chunk[:-1])))
    cid = np.cumsum(ckey_new) - 1
    crank = stream(seed, "rel8b.stratified.clusters").permutation(int(cid.max()) + 1)
    by_cluster = np.lexsort((rank, crank[cid]))
    picked = rest[order][by_cluster[:want]]
    return pop.take(np.sort(np.concatenate([reserved, picked])))


def use_sampler(kind: str) -> None:
    if kind != "stratified":
        return
    import shibuya.agents.population as POP
    import shibuya.engine.run as RUN

    POP.sample_population = stratified_sample  # type: ignore[assignment]
    RUN.sample_population = stratified_sample  # type: ignore[assignment]


def _population(world: str, n: int | None, seed: int, sample: str) -> Any:
    from shibuya.agents.population import load_population, sample_population

    full = load_population(world, n=None, seed=seed)
    if n is None:
        return full
    return stratified_sample(full, n, seed) if sample == "stratified" else sample_population(full, n, seed)


# ------------------------------------------------------------------ tau
def _curve(init: Any, n: int, A0: np.ndarray, taus: list[float]) -> dict[str, Any]:
    out = {}
    for tau in taus:
        keep = A0 >= tau
        per = np.bincount(init.u[keep], minlength=n)
        out[f"{tau:.4f}"] = {"median_edges": float(np.median(per)), "share_15": round(float((per >= 15).mean()), 4),
                             "share_5": round(float((per >= 5).mean()), 4), "share_0": round(float((per == 0).mean()), 4)}
    return out


def cmd_tau(args: argparse.Namespace) -> int:
    from shibuya.agents.weekly import load_weekly
    from shibuya.engine import relations as RL

    wk = load_weekly(args.world)
    doc: dict[str, Any] = {"schema": "shibuya.bench/c10-relations/tau-8b/1", "rows": {}}
    for label, n, sample, tw in (("full_population_13w", None, "default", 13.0),
                                 ("full_population_26w", None, "default", 26.0),
                                 ("default_sample_5000_13w", 5000, "default", 13.0),
                                 ("stratified_sample_5000_13w", 5000, "stratified", 13.0)):
        pop = _population(args.world, n, 1, sample)
        w = wk.restrict_to(pop.source_agent_id)
        t0 = time.perf_counter()
        init = RL.initial_edges(pop, w, pop.n, tau=None, tenure_weeks=tw)
        secs = time.perf_counter() - t0
        A0 = RL._activation(init.n, init.first, 0, 1.0, RL.REL_D)
        A1 = RL._activation(init.n, init.first, 1439, 1.0, RL.REL_D)
        t_start = RL.tau_from_edges(init.u, A0, pop.n)
        t_end = RL.tau_from_edges(init.u, A1, pop.n)
        tau0 = t_start["tau"]
        grid = [tau0 + x for x in (-1.0, -0.5, -0.2, -0.1, -0.05, -0.02, 0.0, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0)] \
            if np.isfinite(tau0) else \
            [RL.REL_TAU + x for x in (-1.0, -0.5, 0.0, 0.5, 1.0)]
        per_all = np.bincount(init.u, minlength=pop.n)
        row = {"agents": int(pop.n), "tenure_weeks": tw, "sample": sample, "edges_before_tau": int(init.u.size),
               "init_seconds_nondeterministic": round(secs, 1),
               "tau_start_of_day": t_start, "tau_end_of_day": t_end,
               "A_distinct_levels_4dp": int(np.unique(np.round(A0, 4)).size),
               "A_quantiles_start": {q: round(float(np.percentile(A0, q)), 4) for q in (0, 10, 25, 50, 75, 90, 100)},
               "n_distinct": int(np.unique(init.n).size),
               "curve_at_start": _curve(init, pop.n, A0, grid),
               "curve_at_declared_tau": _curve(init, pop.n, A0, [RL.REL_TAU]),
               "edges_per_agent_hist_before_tau": {str(i): int(c) for i, c in enumerate(np.bincount(per_all))}}
        doc["rows"][label] = row
        print(label, round(float(tau0), 4), round(float(t_end["tau"]), 4), t_start["share_with_k_edges"],
              row["A_distinct_levels_4dp"], round(secs, 1), flush=True)
    doc["declared_tau"] = RL.REL_TAU
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ audit-sample
def cmd_audit_sample(args: argparse.Namespace) -> int:
    from shibuya.agents.state import AgentKind
    from shibuya.agents.weekly import load_weekly
    from shibuya.engine import relations as RL

    wk = load_weekly(args.world)
    names = {int(k): k.name for k in AgentKind}
    inv = {v: k for k, v in RL.REL_KINDS.items()}
    doc: dict[str, Any] = {"schema": "shibuya.bench/c10-relations/audit-sample-8b/1", "rows": {}}
    for label, n, sample in (("full_population", None, "default"), ("default_sample_5000", 5000, "default"),
                             ("stratified_sample_5000", 5000, "stratified")):
        pop = _population(args.world, n, 1, sample)
        w = wk.restrict_to(pop.source_agent_id)
        init = RL.initial_edges(pop, w, pop.n)
        deg = np.bincount(init.u, minlength=pop.n)
        kinds = np.asarray(pop.kind)
        by_kind = {}
        for k in np.unique(kinds).tolist():
            m = kinds == k
            dk = deg[m]
            by_kind[names.get(int(k), str(k))] = {
                "agents": int(m.sum()), "share_of_agents": round(float(m.mean()), 4),
                "mean_degree": round(float(dk.mean()), 3), "share_0": round(float((dk == 0).mean()), 4),
                "share_15": round(float((dk >= 15).mean()), 4)}
        hh = np.asarray(pop.household_id, dtype=np.int64)
        doc["rows"][label] = {
            "agents": int(pop.n), "edges": int(init.u.size), "audit": init.audit,
            "edge_kinds": {inv[int(k)]: int(c) for k, c in zip(*np.unique(init.kind, return_counts=True))},
            "degree": {"mean": round(float(deg.mean()), 3), "median": float(np.median(deg)),
                       "share_0": round(float((deg == 0).mean()), 4), "share_5": round(float((deg >= 5).mean()), 4),
                       "share_15": round(float((deg >= 15).mean()), 4)},
            "degree_hist": {str(i): int(c) for i, c in enumerate(np.bincount(deg))},
            "households_with_2_or_more": int((np.unique(hh[hh >= 0], return_counts=True)[1] >= 2).sum()),
            "by_agent_kind": by_kind,
        }
        print(label, doc["rows"][label]["edges"], doc["rows"][label]["degree"], flush=True)
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ bytecheck
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
        pair: dict[str, Any] = {}
        for side, src in ((f"head_{args.head_label}", args.head_src), ("working_tree", "")):
            env = dict(os.environ)
            if src:
                env["PYTHONPATH"] = src
                env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"
            if src and "rel_invite" in BYTE_CONFIGS[name]:
                pair[side] = None  # HEAD には 8b の腕の口が無い
                continue
            cmd = [sys.executable, str(Path(__file__)), "bytecheck-one", "--config", name, "--world", args.world,
                   "--agents", str(args.agents), "--seed", str(args.seed), "--tape", str(scratch / f"{side}_{name}")]
            got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True, env=env)
            pair[side] = json.loads(got.stdout.strip().splitlines()[-1])
        h, w = pair[f"head_{args.head_label}"], pair["working_tree"]
        if h is None:
            ref = next(r for r in runs if r["run"] == "v3_memory_on")[f"head_{args.head_label}"]
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
    doc = {"schema": "shibuya.bench/c10-relations/byte-check-8b/1",
           "how": ("same runs (mock 5,000, seed 1, vocab v3, energy, default sampling) with the committed source "
                   f"(git archive of HEAD {args.head_label}) and the working tree; tape = shared blocks and the 14 call "
                   "columns. The relations-on run in the 8a mode (rel_invite off, rel_acq_wake off; only in the "
                   "working tree) is compared to HEAD's memory-on run: the final without the 6 relation fields must "
                   "match; prompts change (B5 near line gets the 知人 marks)."),
           "runs": runs}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ arms
def _q(x: Any) -> dict[str, float]:
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return {"n": 0}
    return {f"p{q}": round(float(np.percentile(x, q)), 3) for q in (0, 10, 50, 90, 99, 100)} | {
        "mean": round(float(x.mean()), 4), "n": int(x.size)}


def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.agents.state import AgentKind
    from shibuya.engine import conversation as CV
    from shibuya.engine import memory as MEM
    from shibuya.engine import relations as RL

    sample, extra = ARMS[args.arm]
    use_sampler(sample)
    rec: list[str] = []
    _patch_state_hash(rec)
    got: dict[str, Any] = {"layer": None, "agents": None}
    picks: list[tuple[int, int, int, float, bool]] = []  # (tick, 体, 相手, セル内の ID 順位(0..1), 辺の相手か)
    closes: list[tuple[int, int, int, int]] = []           # (開いた tick, 閉じた tick, 人数, 起点)
    talk_min: Counter = Counter()

    orig_enable = MEM.MemoryLayer.enable_relations

    def enable(self: Any, *a: Any, **k: Any) -> Any:
        layer = orig_enable(self, *a, **k)
        got["layer"] = layer
        return layer

    MEM.MemoryLayer.enable_relations = enable  # type: ignore[method-assign]
    orig_choose = RL.RelationLayer.choose_talk_partners

    def choose(self: Any, agents: Any, tick: int, a: Any, fallback: Any, named_ok: Any, condition: Any,
               **k: Any) -> Any:
        out, origin = orig_choose(self, agents, tick, a, fallback, named_ok, condition, **k)
        got["agents"] = agents
        cell = np.asarray(agents.registry.cell, dtype=np.int64)
        aa = np.asarray(a, dtype=np.int64)
        nk = np.asarray(named_ok, dtype=bool)
        for i in np.flatnonzero(~nk & (out >= 0)).tolist():  # 逐次: 名指しの無い会話の行の数ぶん(計測の道具)
            members = np.flatnonzero(cell == cell[aa[i]])
            members = members[members != aa[i]]
            if members.size <= 1:
                continue
            rnk = float(np.searchsorted(members, out[i])) / float(members.size - 1)
            edge = bool((agents.registry.rel_partner[aa[i]] == out[i]).any())
            picks.append((int(tick), int(aa[i]), int(out[i]), rnk, edge))
        return out, origin

    RL.RelationLayer.choose_talk_partners = choose  # type: ignore[method-assign]
    # classical の従来の相手選び(近接行の最初の人)=関係 off/8a の腕の基準の T5(同じ道具で数える)
    from shibuya.engine import classical as CL

    orig_first = CL._first_near_person

    def first_near(prompt: str, aid: int) -> str:
        who = orig_first(prompt, aid)
        ag = got.get("cl_agents")
        if who and ag is not None:
            pid = int(who[2:])
            cell = np.asarray(ag.registry.cell, dtype=np.int64)
            members = np.flatnonzero(cell == cell[int(aid)])
            members = members[members != int(aid)]
            if members.size > 1:
                rnk = float(np.searchsorted(members, pid)) / float(members.size - 1)
                picks.append((-1, int(aid), pid, rnk, False))
        return who

    CL._first_near_person = first_near  # type: ignore[assignment]
    orig_cl_init = CL.ClassicalPolicy.__init__ if hasattr(CL, "ClassicalPolicy") else None
    orig_bind = getattr(CL.ClassicalPolicy, "bind", None)
    if orig_bind is not None:
        def bind(self: Any, *a: Any, **k: Any) -> Any:
            out = orig_bind(self, *a, **k)
            got["cl_agents"] = getattr(self, "agents", None)
            return out

        CL.ClassicalPolicy.bind = bind  # type: ignore[method-assign]
    del orig_cl_init
    orig_close = CV.ConversationManager._close

    def close(self: Any, s: Any, tick: int, reason: str) -> None:
        if s.state not in (CV.ConvState.CLOSING, CV.ConvState.TERMINAL):
            dur = max(0, int(tick) - int(s.opened_tick))
            closes.append((int(s.opened_tick), int(tick), len(s.participants), int(getattr(s, "origin", -1))))
            for p in s.participants:
                talk_min[int(p)] += dur
        orig_close(self, s, tick, reason)

    CV.ConversationManager._close = close  # type: ignore[method-assign]
    kw = {**BASE, **extra}
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
    wall = time.perf_counter() - t0
    m = res.run_manifest_fields()
    cc = dict(res.conversation_counters)
    ms = m.get("memory_summary", {})
    n = int(res.agents.n)  # type: ignore[attr-defined]
    kinds = np.asarray(res.agents.registry.field("kind"), dtype=np.int64)  # type: ignore[attr-defined]
    # ---- T5(相手に選ばれた回数と ID・種別の層内=C6 と同じ道具)----
    t5: dict[str, Any] = {"picks": len(picks)}
    if picks:
        sys.path.insert(0, str(REPO / "tools" / "c6"))
        import c6lib  # type: ignore[import-not-found]

        sel = [(p, max(0, t)) for t, _a, p, _r, _e in picks]
        rep = c6lib.stratified_order_bias_report(n, kinds, sel, None, labels={int(k): k.name for k in AgentKind})
        ranks = np.asarray([r for *_x, r, _e in picks])
        t5 |= {"chosen_count_vs_id": {"weighted_abs_rho": rep["weighted_abs_rho"].get("selected_count"),
                                      "partial": rep["partial"].get("selected_count"),
                                      "largest_stratum": {"name": rep["largest_stratum"]["name"],
                                                          "rho": rep["largest_stratum"].get("selected_count")},
                                      "raw_spearman": rep["raw"]["selected_count"]["spearman"]},
               "within_cell_id_rank": {"mean": round(float(ranks.mean()), 4),
                                       "expected_if_unbiased": 0.5,
                                       "pearson_with_uniform_null": round(
                                           float(np.corrcoef(ranks, np.linspace(0, 1, ranks.size))[0, 1])
                                           if ranks.size > 2 else 0.0, 4),
                                       "se": round(float(ranks.std() / max(1.0, np.sqrt(ranks.size))), 4)},
               "edge_partner_share": round(float(np.mean([e for *_x, e in picks])), 4)}
    # ---- A1(大きさ)・A4(交際時間)=holdout=分布の記録だけ ----
    mpt = 1.0
    per_agent = np.asarray([talk_min.get(i, 0) for i in range(n)], dtype=np.float64) * mpt
    dur_by_origin: dict[str, list[int]] = defaultdict(list)
    for o_t, c_t, _sz, org in closes:
        dur_by_origin[RL.REL_ORIGINS[org] if 0 <= org < len(RL.REL_ORIGINS) else "untracked"].append(c_t - o_t)
    lay = got["layer"]
    chosen = lay.chosen_count if (lay is not None and lay.chosen_count is not None) else None
    print(json.dumps({
        "arm": args.arm, "sample": sample, "args": kw, "final_hash": res.final_hash,
        "final_wo_relations": _final_wo(res, rec), "llm_calls": int(res.llm_calls),
        "calls_by_condition": m.get("calls_by_condition", {}),
        "l4": {k: m.get(k) for k in ("l4_conversation_share", "l4_conversation_line", "l4_conversation_exceeded",
                                     "llm_calls_per_agent_day")},
        "relations": m.get("relations", {}),
        "conversation": {k: v for k, v in cc.items() if k.startswith(("sessions", "session_size", "conv_"))},
        "memory_talk_events": int(ms.get("counts", {}).get("events:talk", 0)),
        "a1_session_size": dict(Counter(sz for *_x, sz, _o in closes)),
        "a4_talk_minutes_per_agent_day": {"all_agents": _q(per_agent), "agents_with_talk": _q(per_agent[per_agent > 0]),
                                          "share_with_talk": round(float((per_agent > 0).mean()), 4)},
        "session_minutes_by_origin": {k: _q(v) for k, v in sorted(dur_by_origin.items())},
        "t5": t5,
        "chosen_count_nonzero": int((chosen > 0).sum()) if chosen is not None else None,
        "agents_bytes_total": int(res.agents.bytes_total()),  # type: ignore[attr-defined]
        "agents_declared_bytes_per_agent": int(res.agents.declared_bytes_per_agent),  # type: ignore[attr-defined]
        "kinds_in_sample": {AgentKind(int(k)).name: int(c) for k, c in zip(*np.unique(kinds, return_counts=True))},
        "wall_seconds_nondeterministic": round(wall, 2),
    }, ensure_ascii=False, default=str))
    return 0


def cmd_arms(args: argparse.Namespace) -> int:
    rows = []
    names = args.only.split(",") if args.only else list(ARMS)
    for name in names:
        cmd = [sys.executable, str(Path(__file__)), "one", "--arm", name, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed)]
        got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        row = json.loads(got.stdout.strip().splitlines()[-1])
        rows.append(row)
        rs = row["relations"]
        print(f"{name}: final {row['final_hash'][:8]} wo {row['final_wo_relations'][:8]} calls {row['llm_calls']:,} "
              f"sessions {row['conversation'].get('sessions_opened')} acq {row['calls_by_condition'].get('ACQUAINTANCE')} "
              f"辺/体 {rs.get('edges_live_per_agent', {}).get('mean')} wall {row['wall_seconds_nondeterministic']}s",
              flush=True)
    finals = {r["arm"]: r["final_hash"] for r in rows}
    for r in rows:
        base = WRITE_ONLY_OF.get(r["arm"])
        if base and base in finals:
            r["wo_relations_equals_off"] = r["final_wo_relations"] == finals[base]
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/c10-relations/arms-8b/1", "base": BASE,
                                          "rows": rows}, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ detect-cost
def cmd_detect_cost(args: argparse.Namespace) -> int:
    from shibuya.agents.population import load_population
    from shibuya.agents.state import AgentState
    from shibuya.agents.weekly import load_weekly
    from shibuya.engine import relations as RL

    pop = load_population(args.world, n=None, seed=1)
    w = load_weekly(args.world).restrict_to(pop.source_agent_id)
    n = int(pop.n)
    t0 = time.perf_counter()
    init = RL.initial_edges(pop, w, n)
    t_init = time.perf_counter() - t0
    a = AgentState(n, memory_columns=True, memory_n=1, relation_columns=True, rel_k=RL.REL_K)
    rng = np.random.default_rng(1)
    home = np.asarray(pop.home_cell, dtype=np.int64)
    n_cells = int(max(home.max(), np.asarray(pop.work_cell).max())) + 1
    with a.writable():
        a.cell[:] = np.where(home >= 0, home, rng.integers(0, n_cells, n)).astype(np.int32)
        a.xy[:] = rng.uniform(0.0, 50.0, size=(n, 2)).astype(np.float32)
    lay = RL.RelationLayer(n, RL.REL_K)
    lay.seed_initial(a, init)
    lay.enable_acquaintance_wake()
    lay.enable_copresent()
    t_acq: list[float] = []
    t_co: list[float] = []
    cands: list[int] = []
    work = np.asarray(pop.work_cell, dtype=np.int64)
    for tick in range(args.ticks):  # 逐次: 計測の tick の数ぶん
        with a.writable():
            mv = rng.random(n) < args.move_share
            dest = np.where(work >= 0, work, rng.integers(0, n_cells, n))
            a.cell[mv] = dest[mv].astype(np.int32)
        t1 = time.perf_counter()
        got = lay.acquaintance_candidates(a, tick)
        t_acq.append(time.perf_counter() - t1)
        cands.append(int(got[0].size))
        t1 = time.perf_counter()
        lay.copresent_step(a, tick)
        t_co.append(time.perf_counter() - t1)
    doc = {"schema": "shibuya.bench/c10-relations/detect-cost-8b/1", "agents": n, "k": RL.REL_K,
           "edges": int(init.u.size), "init_seconds_nondeterministic": round(t_init, 1),
           "ticks": args.ticks, "move_share_per_tick": args.move_share,
           "acquaintance_ms_per_tick": _q(np.asarray(t_acq[1:]) * 1000.0),
           "copresent_ms_per_tick": _q(np.asarray(t_co[1:]) * 1000.0),
           "acquaintance_candidates_per_tick": _q(cands[1:]),
           "note": ("synthetic moves: each tick a share of agents jumps to its work cell (or a random cell); "
                    "positions random in a 50 m box; all agents eligible (no sleep/outside filter) = upper bound")}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("acquaintance_ms_per_tick", "copresent_ms_per_tick")}))
    return 0


# ------------------------------------------------------------------ replay
def cmd_replay(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from shibuya.agents.weekly import load_weekly
    from shibuya.engine import relations as RL
    from shibuya.llm.parser import parse_two_line
    from shibuya.perception import templates as T

    unique = json.loads(UNIQUE.read_text(encoding="utf-8"))["unique"]["tapes"]
    wk = load_weekly(args.world)
    nets: dict[int, tuple[set[tuple[int, int]], set[tuple[int, int]], Any]] = {}
    rows = []
    tot: Counter = Counter()
    for name in unique:
        run, arm = name.split("/")
        seed = 2 if run.endswith("_s2") else 1
        if seed not in nets:
            pop = _population(args.world, 5000, seed, "default")
            init = RL.initial_edges(pop, wk.restrict_to(pop.source_agent_id), pop.n, tau=None)
            A0 = RL._activation(init.n, init.first, 0, 1.0, RL.REL_D)
            live = A0 >= RL.REL_TAU
            nets[seed] = ({(int(u), int(v)) for u, v in zip(init.u[live], init.v[live])},
                          {(int(u), int(v)) for u, v in zip(init.u, init.v)}, pop)
        live_e, all_e, pop = nets[seed]
        ver = "v2" if arm.endswith("_v2") else "v1"
        tab = pq.read_table(Path(args.tape_root) / run / arm / "calls.parquet",
                            columns=["agent_id", "response", "deferred", "block_ids"]).to_pydict()
        blocks = pq.read_table(Path(args.tape_root) / run / arm / "blocks.parquet").to_pydict()
        text_of = dict(zip(blocks["block_id"], blocks["text"]))
        c: Counter = Counter()
        kind_seen: dict[int, str] = {}
        for k in range(len(tab["agent_id"])):  # 逐次: 呼ごと(計測の道具)
            aid = int(tab["agent_id"][k])
            if aid not in kind_seen:
                b1 = next((text_of.get(b, "") for b in tab["block_ids"][k] if "[B1" in text_of.get(b, "")), "")
                kind_seen[aid] = b1
            if tab["deferred"][k] or not tab["response"][k]:
                continue
            pr = parse_two_line(tab["response"][k], ver)
            if pr.action != "会話":
                continue
            mm = PERSON_RE.match(str(getattr(pr.target, "raw", "") or "").strip())
            if not mm:
                continue
            pid = int(mm.group(1))
            c["talk_to_person"] += 1
            c["partner_is_live_initial_edge"] += int((aid, pid) in live_e)
            c["partner_is_initial_edge_any"] += int((aid, pid) in all_e)
            c["partner_is_live_edge_either_direction"] += int((aid, pid) in live_e or (pid, aid) in live_e)
        # 体の種別の突き合わせ(テープの B1 の語 ↔ 母集団の種別 → 語)
        match = 0
        for aid, b1 in kind_seen.items():
            kd = int(pop.kind[aid]) if aid < pop.n else -1
            word = T.KIND_WORDS[kd] if 0 <= kd < len(T.KIND_WORDS) else T.KIND_WORDS[1]
            match += int(f"あなたは{word}" in b1)
        c["agents_checked_kind"] = len(kind_seen)
        c["agents_kind_match"] = match
        rows.append({"tape": name, "seed": seed, "counts": dict(c)})
        tot.update(c)
        print(name, dict(c), flush=True)
    n_t = max(1, tot["talk_to_person"])
    doc = {"schema": "shibuya.bench/c10-relations/replay-8b/1", "tapes": rows, "all": dict(tot),
           "shares": {"live_initial_edge": round(tot["partner_is_live_initial_edge"] / n_t, 4),
                      "initial_edge_any": round(tot["partner_is_initial_edge_any"] / n_t, 4),
                      "live_edge_either_direction": round(tot["partner_is_live_edge_either_direction"] / n_t, 4),
                      "kind_match": round(tot["agents_kind_match"] / max(1, tot["agents_checked_kind"]), 4)},
           "note": ("tapes are 5,000-agent runs (seed 1 or 2 from the run name); the population is re-sampled "
                    "with today's sampler and W16 file, and the id mapping is checked by the B1 kind word "
                    "(5 words: 通勤者/来街者/従業者/居住者/指令). Initial network = 8b initial_edges (τ 0.704).")}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ lifetimes(8b′)
def _life_minutes(n: float, tau: float, d: float = 0.5) -> float:
    """n 本・相互作用なしの辺が τ を下回るまでの L[分](A=ln(n/(1−d))−d·ln(L+1) ≥ τ の上端)。"""
    import math

    return max(0.0, math.exp((math.log(n / (1.0 - d)) - tau) / d) - 1.0)


def cmd_lifetimes(args: argparse.Namespace) -> int:
    from shibuya.agents.population import load_population
    from shibuya.agents.weekly import load_weekly
    from shibuya.engine import relations as RL

    pop = load_population(args.world, n=None, seed=1)
    w = load_weekly(args.world).restrict_to(pop.source_agent_id)
    init = RL.initial_edges(pop, w, pop.n)
    L0 = -init.first.astype(np.float64)  # ラン開始時の L[分]
    n = init.n.astype(np.float64)
    tau = RL.REL_TAU
    with np.errstate(over="ignore"):
        rem = (np.exp((np.log(n / (1.0 - RL.REL_D)) - tau) / RL.REL_D) - 1.0 - L0) / 1440.0
    med_n = float(np.median(n))
    i_med = int(np.argsort(n, kind="stable")[n.size // 2])
    fresh = {}
    for label, tv in (("8a_-1.1", -1.1), ("8b_0.704", 0.704), ("8bp", tau), ("8bp_tau-0.5", tau - 0.5),
                      ("8bp_tau+0.5", tau + 0.5)):
        fresh[label] = {f"n{k}_minutes": round(_life_minutes(k, tv), 1) for k in (1, 2, 3, 5)}
    doc = {"schema": "shibuya.bench/c10-relations/lifetimes-8bp/1", "tau": tau, "d": RL.REL_D,
           "fresh_edges_minutes_until_below_tau": fresh,
           "initial_edges_full_population": {
               "edges": int(n.size), "n_quantiles": {q: float(np.percentile(n, q)) for q in (0, 10, 50, 90, 100)},
               "median_n": med_n, "tenure_weeks_of_a_median_n_edge": round(float(L0[i_med]) / 10080.0, 2),
               "remaining_days_quantiles": {q: round(float(np.percentile(rem, q)), 2) for q in (0, 10, 50, 90, 100)},
               "share_below_1_day": round(float((rem < 1.0).mean()), 4),
               "share_below_7_days": round(float((rem < 7.0).mean()), 4)},
           "compare": {"8a": "fresh n=1: 35 min / initial n=65 (92%): 14.9 days",
                       "8b": "fresh n=1: below τ from birth (ln 2 < 0.704) / initial remaining median 609 days"}}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="C10 8b の計測")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("tau", "audit-sample", "bytecheck", "bytecheck-one", "arms", "one", "detect-cost", "replay",
                 "lifetimes"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        if name not in ("bytecheck-one", "one"):
            sp.add_argument("--out", required=True)
        if name == "bytecheck":
            sp.add_argument("--head-src", required=True)
            sp.add_argument("--scratch", required=True)
            sp.add_argument("--head-label", default="3505a0f")
        if name == "bytecheck-one":
            sp.add_argument("--config", required=True, choices=tuple(BYTE_CONFIGS))
            sp.add_argument("--tape", required=True)
        if name == "one":
            sp.add_argument("--arm", required=True, choices=tuple(ARMS))
        if name == "arms":
            sp.add_argument("--only", default="")
        if name == "detect-cost":
            sp.add_argument("--ticks", type=int, default=21)
            sp.add_argument("--move-share", type=float, default=0.05)
        if name == "replay":
            sp.add_argument("--tape-root", default="data/tape")
    args = ap.parse_args(argv)
    return {"tau": cmd_tau, "audit-sample": cmd_audit_sample, "bytecheck": cmd_bytecheck,
            "bytecheck-one": cmd_bytecheck_one, "arms": cmd_arms, "one": cmd_one, "detect-cost": cmd_detect_cost,
            "replay": cmd_replay, "lifetimes": cmd_lifetimes}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
