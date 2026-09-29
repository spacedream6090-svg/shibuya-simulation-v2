"""記憶 第 1 段 6b(想起)の計測。

使い方(リポジトリの根から)::

    # 既定(--memory off)の byte 一致: コミット済みの源(git archive HEAD を展開した src)と作業木で同じランを回し、
    # テープ(描画ブロック・呼の行)を列ごとにハッシュして突き合わせる
    python docs/bench/analysis/memory-stage1-2026-09-28/recall_measure.py bytecheck \\
        --head-src <HEAD を展開した src> --out docs/bench/analysis/memory-stage1-2026-09-28/memory_recall_byte_check.json
    # --memory on の腕(1 構成=1 プロセス・τ 4 点・+親しみの表・classical)
    python docs/bench/analysis/memory-stage1-2026-09-28/recall_measure.py on \\
        --out docs/bench/analysis/memory-stage1-2026-09-28/recall_on_arms.json
    # 実 LLM テープ 17 本(6a と同じ内容で束ねた集合)のリプレイ: 呼ごとに「想起があれば何が載るか」
    python docs/bench/analysis/memory-stage1-2026-09-28/recall_measure.py replay \\
        --out docs/bench/analysis/memory-stage1-2026-09-28/recall_replay.json

- ``bytecheck``: 構成 3 本(v3 既定・classical・親しみの表 on)× 源 2 本(HEAD 45d5e97 / 作業木)。
  比べるもの: final・呼数・``blocks.parquet`` の中身・``calls.parquet`` の版2 の 13 列(列ごと)・版3 の
  ``recalled_rows`` が全行空か。**壁時計は比べない**。
- ``on``: 構成ごとに別プロセス。壁時計・ピークの作業セット(Windows ``K32GetProcessMemoryInfo``)・想起と
  記憶の行の組み立てに掛かった時間(``perf_counter`` の積算)。記憶の 9 欄を混ぜない final が off と一致するか
  (mock は描画の本文を読まない=挙動は同じはず)。**壁時計と RSS と時間の積算は決定論でない**。
- ``replay``: テープの呼を tick 順に辿り、体ごとの記憶の表を応答から組み立てる(``engine.memory`` の表と
  ``MemoryLayer.recall`` をそのまま使う)。各呼で**先に想起**し(その呼の応答はまだ表に無い)、項を
  ``memory_item_text``/``compose_memory_line`` で組んで tok を数え、**後で**その呼の事象を書く。近似(宣言):
  結果は全部「成功」(テープに成否が無い)・相手=応答の対象が ``P-<id>``・対象=POI 名の完全一致・移動は
  いまのセル・気づき=B4 に顕著行為の行が出た呼(p_notice を掛ける前=上限)・看板=B2 に載った看板の POI の
  初見・会話の要旨=理由欄の先頭 40 字(v1/v2 は「ひと言」があればそれ)・q の相手=直前の会話の相手・
  q の対象=なし(テープに意図が無い)。k は ``wake_class``(会話=3・他=2)。個体枠 300 は B5/B6 の本文が
  テープに無いので測れない(行の tok だけ)。

絶対パスは書かない。
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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
TAUS = (-0.5, -1.0, -2.0, -2.5)
CONFIGS: dict[str, dict[str, Any]] = {
    "off": {"vocab_version": "v3"},
    "on_tau_-0.5": {"vocab_version": "v3", "memory": "on", "memory_tau": -0.5},
    "on_tau_-1.0": {"vocab_version": "v3", "memory": "on", "memory_tau": -1.0},
    "on_tau_-2.0": {"vocab_version": "v3", "memory": "on", "memory_tau": -2.0},
    "on_tau_-2.5": {"vocab_version": "v3", "memory": "on", "memory_tau": -2.5},
    "on_familiarity": {"vocab_version": "v3", "memory": "on", "familiarity": "on"},
    "off_familiarity": {"vocab_version": "v3", "familiarity": "on"},
    "on_classical": {"vocab_version": "v3", "memory": "on", "policy": "classical",
                     "chooser": "classical"},
    "off_classical": {"vocab_version": "v3", "policy": "classical", "chooser": "classical"},
}
BASE_OF = {"on_tau_-0.5": "off", "on_tau_-1.0": "off", "on_tau_-2.0": "off", "on_tau_-2.5": "off",
           "on_familiarity": "off_familiarity", "on_classical": "off_classical"}
BYTE_CONFIGS: dict[str, dict[str, Any]] = {
    "v3_default": {"vocab_version": "v3"},
    "v3_classical": {"vocab_version": "v3", "policy": "classical", "chooser": "classical"},
    "v3_familiarity": {"vocab_version": "v3", "familiarity": "on"},
}
V2_COLUMNS = ("call_id", "agent_id", "tick", "wake_class", "prompt_hash", "block_ids", "params_hash",
              "response", "tokens_in", "tokens_out", "deferred", "deferred_reason", "observed_tick")
PLACE_RE = re.compile(r"現在地はセル([^\s()()]+)")
SIGNAGE_SHOWN = "[B2 看板] 〔素性"
SALIENT_LINE = "[B4 行為] 目につく出来事:"
PERSON_RE = re.compile(r"^P-(\d+)$")
KIND_OF_ACTION = {"購入": "buy", "食事": "eat", "並ぶ": "queue", "移動": "move", "乗車": "board",
                  "就寝": "sleep", "会話": "talk", "通報": "report", "手伝い": "help"}


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
    cols = {n: _h(calls.column(n).to_pylist()) for n in V2_COLUMNS}
    new_col = None
    if "recalled_rows" in calls.column_names:
        rr = calls.column("recalled_rows").to_pylist()
        new_col = {"present": True, "all_empty": all(not x for x in rr)}
    meta = (calls.schema.metadata or {}).get(b"shibuya.tape.schema", b"").decode("utf-8")
    out = {
        "config": args.config, "final": res.final_hash[:16], "calls": int(res.llm_calls),
        "calls_rows": int(calls.num_rows), "blocks_rows": int(blocks.num_rows),
        "blocks_sha": _h({n: blocks.column(n).to_pylist() for n in blocks.column_names}),
        "calls_v2_columns_sha": cols, "recalled_rows": new_col,
        "schema_version_metadata": meta,
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_bytecheck(args: argparse.Namespace) -> int:
    runs = []
    scratch = Path(args.scratch)
    for name in BYTE_CONFIGS:
        pair = {}
        for side, src in (("head_45d5e97", args.head_src), ("working_tree_6b", "")):
            env = dict(os.environ)
            if src:
                env["PYTHONPATH"] = src
                env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"
            tape = scratch / f"{side}_{name}"
            cmd = [sys.executable, str(Path(__file__)), "bytecheck-one", "--config", name, "--world",
                   args.world, "--agents", str(args.agents), "--seed", str(args.seed), "--tape", str(tape)]
            got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True, env=env)
            pair[side] = json.loads(got.stdout.strip().splitlines()[-1])
        h, w = pair["head_45d5e97"], pair["working_tree_6b"]
        row = {"run": name, **pair,
               "final_equal": h["final"] == w["final"], "calls_equal": h["calls"] == w["calls"],
               "blocks_equal": (h["blocks_sha"], h["blocks_rows"]) == (w["blocks_sha"], w["blocks_rows"]),
               "calls_v2_columns_equal": h["calls_v2_columns_sha"] == w["calls_v2_columns_sha"],
               "recalled_rows_all_empty": bool(w["recalled_rows"] and w["recalled_rows"]["all_empty"])}
        runs.append(row)
        print(f"{name}: final {row['final_equal']} calls {row['calls_equal']} blocks {row['blocks_equal']} "
              f"v2 列 {row['calls_v2_columns_equal']} 新列空 {row['recalled_rows_all_empty']}", flush=True)
    doc = {"schema": "shibuya.bench/memory-recall-byte-check/1",
           "how": ("same runs (mock 5,000, seed 1, vocab v3, energy, --memory off) with the committed source "
                   "(git archive of HEAD 45d5e97) and with the 6b working tree; tape = shared prompt blocks "
                   "(blocks.parquet) and call rows (calls.parquet: the 13 version-2 columns hashed column by "
                   "column, the version-3 column recalled_rows must be empty on every row). prompt_hash is one "
                   "of the 13 columns = the whole prompt text (B0-B6) is byte-identical."),
           "runs": runs}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                              newline="\n")
    return 0


# ------------------------------------------------------------------ on(1 構成=1 プロセス)
def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.agents import state as S
    from shibuya.core.hashing import blake3_hex
    from shibuya.engine import memory as M
    from shibuya.perception import renderer as R

    kw = dict(CONFIGS[args.config])
    rec: list[str] = []
    orig = S.AgentState.state_hash

    def patched(agent_state: Any) -> str:
        if getattr(agent_state, "memory_columns", False):
            rec.append(agent_state.registry.state_hash(exclude=S.MEMORY_FIELDS))
        return orig(agent_state)

    S.AgentState.state_hash = patched  # type: ignore[method-assign]
    timers = {"recall_s": 0.0, "recall_calls": 0, "memory_line_s": 0.0, "memory_line_calls": 0}
    o_recall = M.MemoryLayer.recall
    o_line = R.Renderer._with_memory_line

    def t_recall(self: Any, *a: Any, **k: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return o_recall(self, *a, **k)
        finally:
            timers["recall_s"] += time.perf_counter() - t0
            timers["recall_calls"] += 1

    def t_line(self: Any, *a: Any, **k: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return o_line(self, *a, **k)
        finally:
            timers["memory_line_s"] += time.perf_counter() - t0
            timers["memory_line_calls"] += 1

    M.MemoryLayer.recall = t_recall  # type: ignore[method-assign]
    R.Renderer._with_memory_line = t_line  # type: ignore[method-assign]
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
    wall = time.perf_counter() - t0
    wo = ""
    if rec and len(rec) == len(res.checkpoints):
        cp = res.checkpoints[-1]
        parts = [rec[-1], cp.world_hash, cp.population_hash, cp.schedule_hash]
        if cp.activity_hash:
            parts.append(cp.activity_hash)
        wo = blake3_hex("\x1f".join(parts).encode("utf-8"))
    m = res.run_manifest_fields()
    ms = m.get("memory_summary", {})
    out = {
        "config": args.config, "args": kw, "final_hash": res.final_hash,
        "final_wo_memory": wo, "llm_calls": int(res.llm_calls),
        "agents_bytes_total": int(res.agents.bytes_total()),  # type: ignore[attr-defined]
        "memory_summary": ms,
        "time_in_recall_seconds_nondeterministic": round(timers["recall_s"], 3),
        "time_in_memory_line_seconds_nondeterministic": round(timers["memory_line_s"], 3),
        "recall_calls": int(timers["recall_calls"]),
        "us_per_recall_nondeterministic": (round(1e6 * timers["recall_s"] / timers["recall_calls"], 1)
                                           if timers["recall_calls"] else None),
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
        rc = row["memory_summary"].get("recall", {})
        print(f"{name}: final {row['final_hash'][:8]} wo {row['final_wo_memory'][:8]} calls "
              f"{row['llm_calls']:,} 想起/呼 {rc.get('recalled_rows_per_call')} 0 件 {rc.get('zero_recall_share')} "
              f"wall {row['wall_seconds_nondeterministic']}s", flush=True)
    finals = {r["config"]: r["final_hash"] for r in rows}
    for r in rows:
        base = BASE_OF.get(r["config"])
        if base:
            r["wo_memory_equals_off"] = r["final_wo_memory"] == finals[base]
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/memory-stage1/recall-on/1", "rows": rows},
                                         ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ replay
def cmd_replay(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from shibuya.agents.state import RESULT_TEXT, AgentState, ResultCode
    from shibuya.core.types import EventClass
    from shibuya.engine import commit as C
    from shibuya.engine import memory as M
    from shibuya.engine.familiarity import place_thing
    from shibuya.llm.parser import parse_two_line
    from shibuya.perception import normalize as N
    from shibuya.perception.channels import estimate_tokens
    from shibuya.perception.renderer import PerceptionAssets, compose_memory_line, memory_item_text
    from shibuya.world.state import World

    world = World.load_or_synthetic(args.world, n_cells=139, seed=1)
    passets = PerceptionAssets.load_or_synthetic(args.world, world)
    place_ids = [str(p) for p in passets.place_ids]
    cell_of = {p: i for i, p in enumerate(place_ids)}
    poi_names = list(passets.poi_name)
    poi_of = {str(n): j for j, n in enumerate(poi_names)}
    sign_poi = np.full(world.n_cells, -1, dtype=np.int64)
    for c in range(world.n_cells):
        for j in passets.visible_poi[c]:
            if int(j) < world.n_poi:
                sign_poi[c] = int(j)
                break
    act_code = {"buy": C.ACT_BUY, "eat": C.ACT_EAT, "queue": C.ACT_QUEUE, "move": C.ACT_MOVE,
                "board": C.ACT_BOARD, "sleep": C.ACT_SLEEP, "talk": C.ACT_TALK, "report": C.ACT_REPORT,
                "help": C.ACT_HELP}
    start = datetime(2026, 1, 1)
    unique = json.loads((HERE / "replay.json").read_text(encoding="utf-8"))["unique"]["tapes"]
    if args.limit_tapes:
        unique = unique[: args.limit_tapes]
    out_rows = []
    agg: dict[float, dict[str, Any]] = {
        tau: {"calls": 0, "calls_with_line": 0, "items": Counter(), "items_by_class": Counter(),
              "calls_by_class": Counter(), "kinds": Counter(), "line_tok": Counter(),
              "dropped_for_channel": 0, "filled_rows": 0, "calls_filled": 0}
        for tau in TAUS
    }
    for name in unique:
        run, arm = name.split("/")
        tdir = Path(args.tape_root) / run / arm
        ver = "v2" if arm.endswith("_v2") else "v1"
        blocks = pq.read_table(tdir / "blocks.parquet", columns=["block_id", "text"]).to_pydict()
        cell_by_block: dict[str, int] = {}
        sign_by_block: dict[str, bool] = {}
        salient_block: set[str] = set()
        for bid, tx in zip(blocks["block_id"], blocks["text"]):
            if "[B2 場所]" in tx:
                m = PLACE_RE.search(tx)
                if m and m.group(1) in cell_of:
                    cell_by_block[bid] = cell_of[m.group(1)]
                sign_by_block[bid] = SIGNAGE_SHOWN in tx
            if SALIENT_LINE in tx:
                salient_block.add(bid)
        t = pq.read_table(tdir / "calls.parquet",
                          columns=["agent_id", "tick", "wake_class", "response", "deferred",
                                   "block_ids"]).to_pydict()
        n_agents = int(max(t["agent_id"])) + 1
        a = AgentState(n_agents, memory_columns=True, memory_n=M.MEMORY_N)
        lay = M.MemoryLayer(n_agents, M.MEMORY_N, minutes_per_tick=1.0)
        seen_sign: set[tuple[int, int]] = set()
        last_partner: dict[int, int] = {}
        per: dict[float, dict[str, Any]] = {
            tau: {"calls": 0, "calls_with_line": 0, "items": 0, "kinds": Counter(), "line_tok": Counter(),
                  "items_per_call": Counter(), "by_class": Counter(), "calls_by_class": Counter()}
            for tau in TAUS
        }
        for k in range(len(t["agent_id"])):  # 逐次: 呼ごと(計測の道具・エンジンではない)
            if t["deferred"][k]:
                continue
            aid = int(t["agent_id"][k])
            tick = int(t["tick"][k])
            bids = t["block_ids"][k]
            b2 = next((b for b in bids if b in cell_by_block), None)
            cell = cell_by_block[b2] if b2 else -1
            cls = int(t["wake_class"][k])
            cond = 0 if cls == int(EventClass.CONVERSATION) else 3  # 会話=3 件・他=2 件(PLAN_GENERAL で代表)
            with a.writable():
                a.cell[aid] = cell
            inviter = last_partner.get(aid, -1) if cls == int(EventClass.CONVERSATION) else -1
            # ---- 先に想起(τ ごと) ----
            for tau in TAUS:
                lay.tau = tau
                lay.recall_stats = Counter()
                items = lay.recall(a, aid, tick, cond, inviter)
                agg[tau]["filled_rows"] += lay.recall_stats.get("filled_rows", 0)
                agg[tau]["calls_filled"] += lay.recall_stats.get("calls_filled", 0)
                texts = []
                for it in items:
                    h, mm = N.format_time(start + timedelta(minutes=int(it.last_tick)))
                    texts.append(memory_item_text(it, hhmm=f"{h}:{mm}", poi_names=poi_names,
                                                  place_ids=place_ids, result_text=RESULT_TEXT))
                line, n_keep = compose_memory_line(texts)
                p = per[tau]
                p["calls"] += 1
                p["calls_by_class"][cls] += 1
                p["items_per_call"][n_keep] += 1
                agg[tau]["calls"] += 1
                agg[tau]["calls_by_class"][cls] += 1
                agg[tau]["dropped_for_channel"] += len(texts) - n_keep
                if n_keep:
                    tok = estimate_tokens(line)
                    p["calls_with_line"] += 1
                    p["items"] += n_keep
                    p["by_class"][cls] += n_keep
                    p["line_tok"][tok] += 1
                    agg[tau]["calls_with_line"] += 1
                    agg[tau]["items_by_class"][cls] += n_keep
                    agg[tau]["line_tok"][tok] += 1
                    for it in items[:n_keep]:
                        kn = M.KIND_NAMES.get(int(it.kind), str(it.kind))
                        p["kinds"][kn] += 1
                        agg[tau]["kinds"][kn] += 1
            # ---- 後でこの呼の事象を書く ----
            resp = t["response"][k]
            ev: list[tuple[int, int, int, int]] = []  # (kind, partner, obj, cell)
            if resp:
                pr = parse_two_line(resp, ver)
                kn = KIND_OF_ACTION.get(pr.action)
                if kn:
                    tgt = str(pr.target or "")
                    mp = PERSON_RE.match(tgt)
                    partner = int(mp.group(1)) if mp else -1
                    obj = poi_of.get(tgt, -1) if partner < 0 else -1
                    if kn == "move":
                        obj = int(place_thing(cell)) if cell >= 0 else -1
                    ev.append((M.EVENT_KINDS[kn], partner, obj, cell))
                    with a.writable():
                        a.last_action[aid] = act_code[kn]
                        a.last_result[aid] = int(ResultCode.OK)
                    if kn == "talk" and partner >= 0:
                        last_partner[aid] = partner
                    if kn == "talk":
                        gist = str(getattr(pr, "comment", "") or "").strip()
                        if not gist or gist == "なし":
                            gist = str(getattr(pr, "reason", "") or "").strip()
                        ev[-1] = ev[-1] + (gist,)  # type: ignore[assignment]
            if any(b in salient_block for b in bids) and cell >= 0:
                ev.append((M.EVENT_KINDS["notice"], -1, int(place_thing(cell)), cell))
            if b2 and sign_by_block.get(b2) and cell >= 0 and sign_poi[cell] >= 0:
                key = (aid, int(sign_poi[cell]))
                if key not in seen_sign:
                    seen_sign.add(key)
                    ev.append((M.EVENT_KINDS["signage"], -1, int(sign_poi[cell]), cell))
            for e in ev:
                rows = lay.record(a, tick, np.asarray([aid]), np.asarray([e[0]]), np.asarray([e[1]]),
                                  np.asarray([e[2]]), np.asarray([int(ResultCode.OK)]), np.asarray([e[3]]))
                if len(e) > 4 and e[4] and (aid, int(rows[0])) not in lay.gist:
                    lay._put_gist(aid, int(rows[0]), str(e[4])[: M.GIST_CHARS])
        summ = {}
        for tau in TAUS:
            p = per[tau]
            summ[str(tau)] = {
                "calls": p["calls"],
                "share_with_line": round(p["calls_with_line"] / max(1, p["calls"]), 4),
                "items_per_call": round(p["items"] / max(1, p["calls"]), 4),
                "items_per_call_hist": {str(x): v for x, v in sorted(p["items_per_call"].items())},
                "items_per_call_by_class": {EventClass(c).name: round(p["by_class"][c] / max(1, n), 4)
                                            for c, n in sorted(p["calls_by_class"].items())},
                "kinds": dict(p["kinds"].most_common()),
                "line_tokens": _q(Counter(p["line_tok"]).elements()),
            }
        out_rows.append({"tape": name, "vocab": ver, "agents": n_agents, "by_tau": summ,
                         "memory_rows_end": int((a.mem_kind != 0).sum()),
                         "gists": len(lay.gist)})
        s1 = summ["-1.0"]
        print(f"{name}: 呼 {s1['calls']:,} 行あり {s1['share_with_line']} 項/呼 {s1['items_per_call']} "
              f"(τ −2.0: {summ['-2.0']['share_with_line']} / {summ['-2.0']['items_per_call']})", flush=True)
    doc = {
        "schema": "shibuya.bench/memory-stage1/recall-replay/1",
        "tapes": out_rows,
        "all": {
            str(tau): {
                "calls": g["calls"],
                "share_with_line": round(g["calls_with_line"] / max(1, g["calls"]), 4),
                "items_per_call": round(sum(g["items_by_class"].values()) / max(1, g["calls"]), 4),
                "items_per_call_by_class": {EventClass(c).name: round(g["items_by_class"][c] / max(1, n), 4)
                                            for c, n in sorted(g["calls_by_class"].items())},
                "kinds": dict(g["kinds"].most_common()),
                "line_tokens": _q(Counter(g["line_tok"]).elements()),
                "line_tokens_max": max(g["line_tok"]) if g["line_tok"] else 0,
                "items_dropped_for_channel": g["dropped_for_channel"],
                "filled_rows": g["filled_rows"], "calls_filled": g["calls_filled"],
            }
            for tau, g in agg.items()
        },
        "note": ("6a のリプレイと同じ 17 本(内容で束ねた集合)。各呼で先に想起・後でその呼の事象を書く。"
                 "結果は全部「成功」(テープに成否が無い)・気づきは上限(p_notice 前)・q の対象なし・"
                 "個体枠 300 は測れない(B5/B6 の本文はテープに無い)。"),
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="記憶 第 1 段 6b(想起)の計測")
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
