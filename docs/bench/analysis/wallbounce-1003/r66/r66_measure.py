"""R-66: セルの廃止(知覚の個人化)で処理量がどれだけ変わるかの計測。

使い方(リポのルートで・src は `git archive HEAD` の写しを PYTHONPATH の先頭に置く):

    python r66_measure.py run   --arm default       --tape <作業用>/t_def --out <出力>/run_default.json
    python r66_measure.py run   --arm mem_rel_store --tape <作業用>/t_mem --out <出力>/run_mem.json
    python r66_measure.py tape  --tape <c7-day-4 のテープの dir> --out <出力>/tape_c7d4.json
    python r66_measure.py fit   --ledger docs/bench/bench_ledger.csv --out <出力>/bn_fit.json
    python r66_measure.py p6    --out <出力>/p6_bench.json
    python r66_measure.py model --run <run_default.json> --run <run_mem.json> --tape <tape_c7d4.json>
                                --fit <bn_fit.json> --out <出力>/model.json

やること:
- run: mock 5,000 体 1 日(seed 1)を回し、描画ごとに B0〜B6 の文字数・バイト数・概算トークン
  (renderer と同じ「文字数 // 2」)・ブロックのハッシュを控える。知覚の前計算
  (``Renderer.prepare_tick``)・描画(``Renderer.render``)・変化検出(``ChangeDetector.detect``)
  の時間と、変化したセル数・セルの変化で起きた体の数を控える。ランの後で、セルのキャッシュを
  毎回空にした描画(=個人ごとの描画の近似)の時間を測る。src は編集しない(包みは値を読むだけ)。
- tape: c7-day-4(39 万体・実 LLM)のテープを読み、共有ブロック(B0〜B4b)の概算トークンと
  実際の入力トークン(tokens_in)から「実トークン / 概算トークン」を回帰で求め、艦隊の振り分け
  (``xxh64(call_id) % 7``)で GPU ごとの呼の列を作って、prefix の再利用を窓 K 呼で数える。
  設計は 4 通り(今 / セル廃止で並びそのまま / セル廃止で B3 を前へ / セル廃止で B3 を前へ+
  場所の定型文 B2 を共有)。
- fit: ベンチ台帳の BN-2・BN-2C(単 GPU・c64・o128・139 セル)の行から、1 呼の時間
  = a + b×(キャッシュに当たらない入力トークン) + c×(当たった入力トークン) を最小二乗で合わせる。
- p6: 40 万体で、本人の位置の場の値を引いて段の跨ぎを調べる配列演算(セル無しの変化検出の近似)
  の時間を測る。
- model: 上の 4 つから、セル廃止の 2 案(a 同じ長さ / b 視野で短く)× 既定 / 記憶 ON の
  処理量の変化を出す(推測)。

絶対パスは JSON に書かない。壁時計は参考の値。
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

ARMS: dict[str, dict[str, Any]] = {
    "default": {"vocab_version": "v3", "activity": True},
    "mem_rel_store": {"vocab_version": "v3", "activity": True, "memory": "on",
                      "relations": "on", "store_memory": "on"},
}
BLOCKS = ("B0", "B1", "B2", "B3", "B4", "B4b", "B5", "B6")
CELL_BLOCKS = ("B2", "B4", "B4b")
SHARED_STATIC = ("B0", "B1", "B3")
INDIVIDUAL = ("B5", "B6")
# 視野(R-62 §1): 検出の外周 片側 107°(左右 214°)。再認(文字)は直径 46°。
FOV_DETECT = 214.0 / 360.0
FOV_RECOG = 46.0 / 360.0
# 視野で絞れる行(列挙の行)。残りの行(場所・路面・密度・騒音)は本人の位置でも同じ長さ。
LIST_LINE_TAGS = ("[B2 可視]", "[B2 看板]", "[B2 地物]", "[B4 顕著]", "[B4b")


def _w(path: str, doc: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                          newline="\n")


def _dist(a: np.ndarray) -> dict[str, float]:
    a = np.asarray(a, dtype=np.float64)
    if a.size == 0:
        return {"n": 0}
    return {"n": int(a.size), "mean": round(float(a.mean()), 2), "p50": float(np.percentile(a, 50)),
            "p95": float(np.percentile(a, 95)), "max": float(a.max()), "sum": float(a.sum())}


def _list_share(text: str) -> tuple[int, int]:
    """(列挙の行の文字数, 全体の文字数)。行の区切りの改行は全体に含める。"""
    lst = 0
    for line in text.split("\n"):
        if line.startswith(LIST_LINE_TAGS):
            lst += len(line)
    return lst, len(text)


# --------------------------------------------------------------------------- run
def cmd_run(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.engine import change_detect as cd
    from shibuya.perception import renderer as R

    n_b = len(BLOCKS)
    rec_chars: list[list[int]] = []
    rec_bytes: list[list[int]] = []
    rec_hash: list[list[int]] = []
    rec_meta: list[tuple[int, int, int, int]] = []  # tick, agent, cell, kind
    rec_list: list[tuple[int, int]] = []  # セル部分の列挙の行の文字数・セル部分の文字数
    t_render: list[float] = []
    t_prep: list[tuple[int, float]] = []
    det_rows: list[tuple[int, float, int, int]] = []  # tick, 秒, 変化セル数, セル起床の体数
    holder: dict[str, Any] = {}

    orig_render = R.Renderer.render
    orig_prep = R.Renderer.prepare_tick
    orig_det = cd.ChangeDetector.detect

    def render(self: Any, agent_id: int, tick: int, *a: Any, **k: Any) -> Any:
        t0 = time.perf_counter()
        out = orig_render(self, agent_id, tick, *a, **k)
        t_render.append(time.perf_counter() - t0)
        holder["renderer"] = self
        i = int(agent_id)
        rec_meta.append((int(tick), i, int(self.agents.cell[i]), int(self.agents.kind[i])))
        ch = [len(out.blocks[b].decode("utf-8")) for b in BLOCKS]
        rec_chars.append(ch)
        rec_bytes.append([len(out.blocks[b]) for b in BLOCKS])
        rec_hash.append([int(out.block_hashes[b]) & 0x7FFF_FFFF_FFFF_FFFF for b in BLOCKS])
        cell_text = "\n".join(out.blocks[b].decode("utf-8") for b in CELL_BLOCKS)
        rec_list.append(_list_share(cell_text))
        return out

    def prep(self: Any, tick: int, **kw: Any) -> Any:
        t0 = time.perf_counter()
        r = orig_prep(self, tick, **kw)
        t_prep.append((int(tick), time.perf_counter() - t0))
        return r

    def det(self: Any, world: Any, agents: Any, tick: int, *a: Any, **k: Any) -> Any:
        t0 = time.perf_counter()
        r = orig_det(self, world, agents, tick, *a, **k)
        det_rows.append((int(tick), time.perf_counter() - t0, int(r.changed_cells.size),
                         int(r.cell_wake_agents.size)))
        return r

    R.Renderer.render = render  # type: ignore[method-assign]
    R.Renderer.prepare_tick = prep  # type: ignore[method-assign]
    cd.ChangeDetector.detect = det  # type: ignore[method-assign]

    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape,
                  **ARMS[args.arm])
    wall = time.perf_counter() - t0
    R.Renderer.render = orig_render  # type: ignore[method-assign]

    chars = np.asarray(rec_chars, dtype=np.int64)
    byts = np.asarray(rec_bytes, dtype=np.int64)
    est = np.maximum(1, chars // 2)  # renderer と同じ概算(ブロックごと)
    hashes = np.asarray(rec_hash, dtype=np.int64)
    meta = np.asarray(rec_meta, dtype=np.int64)
    n = chars.shape[0]
    tot_est = est.sum(axis=1)

    per_block = {}
    for j, b in enumerate(BLOCKS):
        per_block[b] = {
            "chars_mean": round(float(chars[:, j].mean()), 2),
            "bytes_mean": round(float(byts[:, j].mean()), 2),
            "est_tok_mean": round(float(est[:, j].mean()), 2),
            "est_tok_share": round(float(est[:, j].sum() / tot_est.sum()), 4),
            "distinct": int(np.unique(hashes[:, j]).size),
        }

    def gshare(group: tuple[str, ...]) -> dict[str, float]:
        idx = [BLOCKS.index(b) for b in group]
        return {
            "est_tok_mean": round(float(est[:, idx].sum(axis=1).mean()), 2),
            "chars_mean": round(float(chars[:, idx].sum(axis=1).mean()), 2),
            "est_tok_share": round(float(est[:, idx].sum() / tot_est.sum()), 4),
            "chars_share": round(float(chars[:, idx].sum() / chars.sum()), 4),
        }

    groups = {"shared_static": gshare(SHARED_STATIC), "cell": gshare(CELL_BLOCKS),
              "individual": gshare(INDIVIDUAL)}

    # 同じ tick の中で prefix(B0〜B4b)が何呼に共有されているか(理想のキャッシュ=1 tick 窓)
    key = np.zeros(n, dtype=np.uint64)
    fan: dict[str, Any] = {}
    for d in range(1, 7):
        h = hashes[:, d - 1].astype(np.uint64)
        key = (key * np.uint64(1_000_003)) ^ h
        k2 = np.stack([meta[:, 0].astype(np.uint64), key], axis=1)
        _, inv, cnt = np.unique(k2, axis=0, return_inverse=True, return_counts=True)
        inv = np.asarray(inv).ravel()
        first = np.zeros(cnt.size, dtype=bool)
        seen = np.zeros(n, dtype=bool)
        # 同じ鍵の 2 回目以降=再利用できる呼
        order = np.argsort(inv, kind="stable")
        sinv = inv[order]
        rep = np.ones(n, dtype=bool)
        rep[0] = False
        rep[1:] = sinv[1:] == sinv[:-1]
        seen[order] = rep
        del first
        fan[f"depth{d}_{BLOCKS[d - 1]}"] = {
            "distinct_per_tick_mean": round(float(cnt.size / max(1, np.unique(meta[:, 0]).size)), 2),
            "reuse_rate_within_tick": round(float(seen.mean()), 4),
        }

    lst = np.asarray(rec_list, dtype=np.int64)
    tr = np.asarray(t_render)
    tp = np.asarray([x[1] for x in t_prep])
    dr = np.asarray([[x[1], x[2], x[3]] for x in det_rows], dtype=np.float64)

    # ---- ランの後: セルのキャッシュを毎回空にした描画(=個人ごとの描画の近似)
    micro: dict[str, Any] = {}
    rnd = holder.get("renderer")
    if rnd is not None:
        last_tick = int(meta[-1, 0])
        rng = np.random.default_rng(0)
        cells = np.asarray(rnd.agents.cell)
        cand = np.flatnonzero(cells >= 0)
        pick = rng.choice(cand, size=min(args.micro, cand.size), replace=False)
        rnd.prepare_tick(last_tick)

        def bench(clear: bool) -> np.ndarray:
            out = np.empty(pick.size)
            for j, i in enumerate(pick):
                if clear:
                    rnd._b2_cache.clear()
                    rnd._b4_cache.clear()
                t = time.perf_counter()
                rnd.render(int(i), last_tick)
                out[j] = time.perf_counter() - t
            return out

        bench(False)  # 温め
        warm = bench(False)
        cold = bench(True)
        # セル部分だけ(B2+B4)の組み立て
        tc = rnd._tickc
        cb = np.empty(pick.size)
        for j, i in enumerate(pick):
            rnd._b2_cache.clear()
            rnd._b4_cache.clear()
            c = int(cells[i])
            t = time.perf_counter()
            rnd._b2(c, [], True)
            rnd._b4(c, tc, [])
            cb[j] = time.perf_counter() - t
        t = time.perf_counter()
        for _ in range(20):
            rnd.prepare_tick(last_tick)
        prep_once = (time.perf_counter() - t) / 20
        micro = {
            "n": int(pick.size),
            "render_cached_us": _dist(warm * 1e6),
            "render_uncached_cell_us": _dist(cold * 1e6),
            "cell_part_build_us": _dist(cb * 1e6),
            "prepare_tick_ms_repeat": round(prep_once * 1e3, 3),
        }

    calls_per_tick = np.bincount(meta[:, 0])
    doc = {
        "schema": "shibuya.bench/wallbounce-1003/r66-run/1",
        "arm": args.arm,
        "args": ARMS[args.arm],
        "agents": args.agents,
        "seed": args.seed,
        "final_hash": res.final_hash[:16],
        "llm_calls": int(res.llm_calls),
        "renders": int(n),
        "token_rule": "renderer の概算(ブロックごとに 文字数 // 2・最低 1)。tokenizer は使っていない",
        "per_block": per_block,
        "groups": groups,
        "prompt_est_tok": _dist(tot_est),
        "prompt_chars": _dist(chars.sum(axis=1) + (n_b - 1)),
        "cell_list_lines": {
            "list_chars_mean": round(float(lst[:, 0].mean()), 2),
            "cell_chars_mean": round(float(lst[:, 1].mean()), 2),
            "list_fraction": round(float(lst[:, 0].sum() / max(1, lst[:, 1].sum())), 4),
            "tags": list(LIST_LINE_TAGS),
        },
        "prefix_within_tick": fan,
        "timing": {
            "render_us": _dist(tr * 1e6),
            "render_s_total": round(float(tr.sum()), 3),
            "prepare_tick_ms": _dist(tp * 1e3),
            "prepare_tick_s_total": round(float(tp.sum()), 3),
            "detect_ms": _dist(dr[:, 0] * 1e3) if dr.size else {},
            "calls_per_tick": _dist(calls_per_tick),
            "note": "壁時計は参考(Windows の手元機・他のプロセスと同居)",
        },
        "change_detect": {
            "ticks": int(dr.shape[0]),
            "changed_cells_per_tick": _dist(dr[:, 1]) if dr.size else {},
            "cell_wake_agents_per_tick": _dist(dr[:, 2]) if dr.size else {},
            "ticks_with_change": int((dr[:, 1] > 0).sum()) if dr.size else 0,
        },
        "micro_after_run": micro,
        "wall_s_reference": round(wall, 1),
    }
    _w(args.out, doc)
    if args.samples:
        idx = np.linspace(0, n - 1, num=4, dtype=int)
        lines = []
        rnd = holder.get("renderer")
        for i in idx:
            lines.append(f"--- 描画 {int(i)}(tick {int(meta[i,0])}・体 {int(meta[i,1])}) "
                         f"概算 tok: " + " ".join(f"{b}={int(est[i,j])}" for j, b in enumerate(BLOCKS)))
        Path(args.samples).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("arm", "final_hash", "llm_calls", "renders", "groups")},
                     ensure_ascii=False))
    return 0


# --------------------------------------------------------------------------- tape
def cmd_tape(args: argparse.Namespace) -> int:
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    from shibuya.core.hashing import xxh64

    tdir = Path(args.tape)
    blocks = pq.read_table(tdir / "blocks.parquet").to_pydict()
    bid2i = {b: i for i, b in enumerate(blocks["block_id"])}
    btxt = blocks["text"]
    b_est = np.asarray(blocks["tokens"], dtype=np.int64)
    b_chars = np.asarray([len(t) for t in btxt], dtype=np.int64)
    b_list = np.asarray([_list_share(t)[0] for t in btxt], dtype=np.int64)

    cols = ["call_id", "tick", "block_ids", "tokens_in", "tokens_out", "deferred"]
    t = pq.read_table(tdir / "calls.parquet", columns=cols)
    t = t.filter(pc.equal(t["deferred"], 0))
    n = t.num_rows
    flat = pc.list_flatten(t["block_ids"]).to_pylist()
    ids = np.fromiter((bid2i[x] for x in flat), dtype=np.int64, count=len(flat)).reshape(n, 6)
    del flat
    tick = t["tick"].to_numpy()
    tin = t["tokens_in"].to_numpy().astype(np.float64)
    tout = t["tokens_out"].to_numpy().astype(np.float64)
    call_ids = t["call_id"].to_pylist()
    rep = np.fromiter((xxh64(c.encode("utf-8")) % args.replicas for c in call_ids), dtype=np.int64,
                      count=n)
    del call_ids
    shared_ids = ("B0", "B1", "B2", "B3", "B4", "B4b")
    est = b_est[ids]  # (n, 6)
    chs = b_chars[ids]
    lst = b_list[ids]

    # 何の block か(列の位置で決まる)。同じ本文が別の列に出ないことを確かめる
    col_sets = [set(np.unique(ids[:, j]).tolist()) for j in range(6)]
    overlap = sum(len(col_sets[a] & col_sets[b]) for a in range(6) for b in range(a + 1, 6))

    # ---- 実トークン / 概算トークン の回帰(tokens_in ~ 1 + 各列の概算 tok)
    X = np.column_stack([np.ones(n)] + [est[:, j] for j in range(1, 6)])
    coef, *_ = np.linalg.lstsq(X, tin, rcond=None)
    Xc = np.column_stack([np.ones(n), chs[:, [2, 4, 5]].sum(axis=1), chs[:, [1, 3]].sum(axis=1)])
    coef_c, *_ = np.linalg.lstsq(Xc, tin, rcond=None)
    Xg = np.column_stack([np.ones(n), est[:, [2, 4, 5]].sum(axis=1), est[:, [1, 3]].sum(axis=1)])
    coef_g, *_ = np.linalg.lstsq(Xg, tin, rcond=None)

    per_block = {}
    for j, b in enumerate(shared_ids):
        per_block[b] = {"est_tok_mean": round(float(est[:, j].mean()), 2),
                        "chars_mean": round(float(chs[:, j].mean()), 2),
                        "distinct": int(np.unique(ids[:, j]).size)}
    cell_est = est[:, [2, 4, 5]].sum(axis=1)
    cell_list_chars = lst[:, [2, 4, 5]].sum(axis=1)
    cell_chars = chs[:, [2, 4, 5]].sum(axis=1)

    # ---- prefix の再利用(GPU ごとの呼の列・窓 K 呼)
    if args.shuffle:
        # 対照: 同じ tick の中の順をでたらめにする(テープの並びがセル順に寄っていても効かないように)
        tie = np.random.default_rng(args.shuffle).permutation(n)
    else:
        tie = np.arange(n)
    order = np.lexsort((tie, tick))  # tick 順(同 tick はテープの順 or でたらめ)
    # セルへの集中: 各 tick で、呼の多い上位 10 セル(B2)が呼の何割か
    k_tb = tick.astype(np.int64) * 10_000 + ids[:, 2]
    u, cnt_tb = np.unique(k_tb, return_counts=True)
    t_of = u // 10_000
    top10 = []
    for tt in np.unique(t_of):
        c = np.sort(cnt_tb[t_of == tt])[::-1]
        top10.append(c[:10].sum() / c.sum())
    conc = {"top10_cells_share_of_calls_per_tick": _dist(np.asarray(top10)),
            "distinct_b2_per_tick": _dist(np.bincount(t_of))}
    designs = {
        # 鍵の列(前から)。"U" = 呼ごとに違う(共有されない)
        "now": ["B0", "B1", "B2", "B3", "B4", "B4b"],
        "abolish_keep_order": ["B0", "B1", "U"],
        "abolish_b3_first": ["B0", "B1", "B3", "U"],
        "abolish_b3_first_place_shared": ["B0", "B1", "B3", "B2", "U"],
    }
    windows = [int(x) for x in args.windows.split(",")]
    sims: dict[str, Any] = {}
    # 呼ごとの位置(GPU の中での通し番号)
    pos = np.empty(n, dtype=np.int64)
    rep_o = rep[order]
    for r in range(args.replicas):
        m = rep_o == r
        pos[order[m]] = np.arange(int(m.sum()))
    for name, seq in designs.items():
        depth_gap: list[np.ndarray] = []
        depth_cols: list[int] = []
        key = np.zeros(n, dtype=np.uint64)
        for b in seq:
            if b == "U":
                break
            j = shared_ids.index(b)
            depth_cols.append(j)
            key = (key * np.uint64(1_000_003)) ^ ids[:, j].astype(np.uint64)
            # 同じ GPU・同じ鍵の 1 つ前の呼との距離(呼の数)
            o = np.lexsort((pos, key, rep))
            k_o, r_o, p_o = key[o], rep[o], pos[o]
            same = np.zeros(n, dtype=bool)
            same[1:] = (k_o[1:] == k_o[:-1]) & (r_o[1:] == r_o[:-1])
            gap = np.full(n, np.iinfo(np.int64).max, dtype=np.int64)
            g = np.empty(n, dtype=np.int64)
            g[0] = 0
            g[1:] = p_o[1:] - p_o[:-1]
            gap_o = np.where(same, g, np.iinfo(np.int64).max)
            gap[o] = gap_o
            depth_gap.append(gap)
        res: dict[str, Any] = {}
        for K in windows + [0]:
            # 0 = 窓なし(同じ GPU で前に一度でも出ていれば当たる=理想)
            cached_est = np.zeros(n, dtype=np.float64)
            ok = np.ones(n, dtype=bool)
            for dg, j in zip(depth_gap, depth_cols):
                hit = dg < np.iinfo(np.int64).max if K == 0 else dg <= K
                ok &= hit
                cached_est += np.where(ok, est[:, j], 0)
            hit_by_block = {}
            ok = np.ones(n, dtype=bool)
            for dg, j in zip(depth_gap, depth_cols):
                hit = dg < np.iinfo(np.int64).max if K == 0 else dg <= K
                ok &= hit
                hit_by_block[shared_ids[j]] = round(float(ok.mean()), 4)
            res["inf" if K == 0 else str(K)] = {
                "cached_est_tok_mean": round(float(cached_est.mean()), 2),
                "hit_rate_by_block_depth": hit_by_block,
            }
        sims[name] = res

    calls_per_tick = np.bincount(tick)
    doc = {
        "schema": "shibuya.bench/wallbounce-1003/r66-tape/1",
        "tape": "c7-day-4(39 万体・実 LLM Qwen3-8B INT8×7・繰り延べ行を除く)",
        "rows_used": int(n),
        "replicas": args.replicas,
        "routing": "xxh64(call_id) % replicas(fleet.route_primary と同じ。least-in-flight の振り替えは無視)",
        "column_overlap_blocks": int(overlap),
        "tokens_in": _dist(tin),
        "tokens_out": _dist(tout),
        "per_block_shared": per_block,
        "cell_est_tok": _dist(cell_est),
        "cell_list_fraction_chars": round(float(cell_list_chars.sum() / max(1, cell_chars.sum())), 4),
        "regression_tokens_in_on_est": {
            "cols": ["const", "B1", "B2", "B3", "B4", "B4b"],
            "coef": [round(float(c), 4) for c in coef],
        },
        "regression_tokens_in_on_est_groups": {
            "cols": ["const", "cell(B2+B4+B4b)", "B1+B3"],
            "coef": [round(float(c), 4) for c in coef_g],
        },
        "regression_tokens_in_on_chars_groups": {
            "cols": ["const", "cell(B2+B4+B4b) 文字", "B1+B3 文字"],
            "coef": [round(float(c), 4) for c in coef_c],
        },
        "calls_per_tick": _dist(calls_per_tick),
        "prefix_sim": sims,
        "shuffle_within_tick_seed": int(args.shuffle),
        "concentration": conc,
        "windows_calls": windows,
    }
    _w(args.out, doc)
    print(json.dumps({"rows": n, "coef_groups": doc["regression_tokens_in_on_est_groups"]},
                     ensure_ascii=False))
    return 0


# --------------------------------------------------------------------------- fit
def cmd_fit(args: argparse.Namespace) -> int:
    rows = []
    with open(args.ledger, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            bid = r["bench_id"]
            if not (bid.startswith("BN2-") or bid.startswith("BN2C-")):
                continue
            notes = r["notes"]
            kv = dict(x.split("=", 1) for x in notes.split(";") if "=" in x)
            req_s = float(kv["req_s"])
            hit = float(kv["pc_hit"].rstrip("%")) / 100.0
            tin = float(r["input_len"])
            rows.append({"id": bid, "req_s": req_s, "in": tin, "hit": hit,
                         "shared": float(kv.get("shared_tok", "nan")),
                         "indiv": float(kv.get("indiv_tok", "nan")),
                         "cells": int(kv.get("cells", "0")), "b_cell": kv.get("b_cell", "")})
    # 1 呼の時間 = a + b×未命中 + c×命中(単 GPU・c64 一定なので 1/req_s を時間とみなす)
    y = np.asarray([1.0 / r["req_s"] for r in rows])
    miss = np.asarray([r["in"] * (1 - r["hit"]) for r in rows])
    hitt = np.asarray([r["in"] * r["hit"] for r in rows])
    X = np.column_stack([np.ones(len(rows)), miss, hitt])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    # 個体長だけの 3 点(共有 1000)の 1/req_s の傾き
    ind = [r for r in rows if r["id"].startswith("BN2-s1000")]
    ind.sort(key=lambda r: r["indiv"])
    slope_ind = np.polyfit([r["indiv"] for r in ind], [1 / r["req_s"] for r in ind], 1).tolist()
    rule = {
        "i300_req_s": ind[0]["req_s"], "i800_req_s": ind[-1]["req_s"],
        "drop_300_to_800": round(1 - ind[-1]["req_s"] / ind[0]["req_s"], 4),
        "per_100tok_linear": round((1 - ind[-1]["req_s"] / ind[0]["req_s"]) / 5, 4),
    }
    doc = {
        "schema": "shibuya.bench/wallbounce-1003/r66-fit/1",
        "source": "docs/bench/bench_ledger.csv の BN2-*・BN2C-* 行(2026-09-03・単 GPU・Qwen3-8B INT8・c64・o128)",
        "rows": rows,
        "model": "1/req_s = a + b×(input×(1−pc_hit)) + c×(input×pc_hit)",
        "coef": {"a": float(coef[0]), "b_miss": float(coef[1]), "c_hit": float(coef[2])},
        "fit_resid_rel": [round(float((p - t) / t), 4) for p, t in zip(pred, y)],
        "indiv_sweep_inverse_slope": {"slope_s_per_tok": slope_ind[0], "intercept_s": slope_ind[1]},
        "rule_8pct": rule,
    }
    _w(args.out, doc)
    print(json.dumps(doc["coef"]), json.dumps(rule))
    return 0


# --------------------------------------------------------------------------- p6
def cmd_p6(args: argparse.Namespace) -> int:
    rng = np.random.default_rng(1)
    n = args.agents
    # 本人の位置の場(2.5 m 格子相当。渋谷の 139 ha を 2.5 m で割ると約 22 万格子)の段を引く
    g = 222_400
    field = rng.integers(0, 6, size=(g, 4), dtype=np.int8)
    pos = rng.integers(0, g, size=n, dtype=np.int64)
    prev = field[pos].copy()
    res: dict[str, Any] = {}
    for name, frac_move in (("move_10pct", 0.10), ("move_50pct", 0.50)):
        ts = []
        for _ in range(args.reps):
            mv = rng.random(n) < frac_move
            pos2 = pos.copy()
            pos2[mv] = (pos2[mv] + rng.integers(1, 3, size=int(mv.sum()))) % g
            t0 = time.perf_counter()
            cur = field[pos2]  # 4 欄の gather
            changed = np.flatnonzero((cur != prev).any(axis=1))
            prev = cur
            ts.append(time.perf_counter() - t0)
            pos = pos2
        res[name] = {"ms": _dist(np.asarray(ts) * 1e3), "changed_last": int(changed.size)}
    # 近くの人数(半径の近傍)を 1 tick に 1 回数える近似: 格子ごとの人数の bincount と gather
    ts = []
    for _ in range(args.reps):
        t0 = time.perf_counter()
        cnt = np.bincount(pos // 16, minlength=g // 16 + 1)  # 10 m 角の格子の人数
        mine = cnt[pos // 16]
        _ = np.flatnonzero(mine > 5)
        ts.append(time.perf_counter() - t0)
    res["count_near_10m_grid"] = {"ms": _dist(np.asarray(ts) * 1e3)}
    doc = {"schema": "shibuya.bench/wallbounce-1003/r66-p6/1", "agents": n, "grid_cells": g,
           "note": "合成の場と位置。今の P6(定常 1.07〜1.44 ms・セル 10% 変化 1.62〜2.32 ms・D-48)と同じ手元機ではない",
           "results": res}
    _w(args.out, doc)
    print(json.dumps(res, ensure_ascii=False))
    return 0


# --------------------------------------------------------------------------- model
def cmd_model(args: argparse.Namespace) -> int:
    """セル廃止の処理量の見込み(推測)。

    1 呼の入力を「概算 tok(文字数 // 2)× 換算 k」で実トークンにし、prefix に当たる分と
    当たらない分に分けて、BN-2/BN-2C の当てはめ 1 呼の時間 = a + b×未命中 + c×命中 に入れる。
    当たる率は c7-day-4 の GPU ごとの呼の列で数えた値(窓 K 呼)。ブロックの長さは HEAD の mock。
    """
    fit = json.loads(Path(args.fit).read_text(encoding="utf-8"))
    tape = json.loads(Path(args.tape).read_text(encoding="utf-8"))
    runs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in args.run]
    a, b, c = fit["coef"]["a"], fit["coef"]["b_miss"], fit["coef"]["c_hit"]
    rule = fit["rule_8pct"]["per_100tok_linear"]
    ks = [float(x) for x in args.k.split(",")]
    sims = tape["prefix_sim"]
    b2_fixed_frac = float(args.b2_fixed_frac)
    rows = []
    for run in runs:
        E = {bk: run["per_block"][bk]["est_tok_mean"] for bk in BLOCKS}
        cellE = E["B2"] + E["B4"] + E["B4b"]
        listE = cellE * run["cell_list_lines"]["list_fraction"]
        b2fix = E["B2"] * b2_fixed_frac
        total = sum(E.values())
        for K in args.windows.split(","):
            hn = sims["now"][K]["hit_rate_by_block_depth"]
            cached_now = E["B0"] * hn["B0"] + E["B1"] * hn["B1"] + sum(
                E[x] * hn[x] for x in ("B2", "B3", "B4", "B4b"))
            for scen, f in (("a_same_length", 1.0), ("b_fov_214deg", FOV_DETECT),
                            ("b_fov_46deg", FOV_RECOG)):
                for dname in ("abolish_keep_order", "abolish_b3_first",
                              "abolish_b3_first_place_shared"):
                    ha = sims[dname][K]["hit_rate_by_block_depth"]
                    if dname == "abolish_b3_first_place_shared":
                        personal = (cellE - b2fix - listE) + listE * f
                        shared_part = b2fix
                    else:
                        personal = (cellE - listE) + listE * f
                        shared_part = 0.0
                    total_aft = total - cellE + personal + shared_part
                    cached_aft = E["B0"] * ha["B0"] + E["B1"] * ha["B1"]
                    if "B3" in ha:
                        cached_aft += E["B3"] * ha["B3"]
                    if "B2" in ha:
                        cached_aft += shared_part * ha["B2"]
                    for k in ks:
                        t_now, t_aft = total * k, total_aft * k
                        h_now, h_aft = cached_now * k, cached_aft * k
                        m_now, m_aft = t_now - h_now, t_aft - h_aft
                        s_now = a + b * m_now + c * h_now
                        s_aft = a + b * m_aft + c * h_aft
                        rows.append({
                            "arm": run["arm"], "K": K, "k_real_per_est": k, "scenario": scen,
                            "design": dname,
                            "cell_share_est_now": round(cellE / total, 4),
                            "input_real_now": round(t_now, 1), "input_real_after": round(t_aft, 1),
                            "cached_real_now": round(h_now, 1), "cached_real_after": round(h_aft, 1),
                            "uncached_increase_real": round(m_aft - m_now, 1),
                            "throughput_change_fit": round(s_now / s_aft - 1, 4),
                            "throughput_change_rule8": round(-rule * (m_aft - m_now) / 100, 4),
                            "prefix_gain_now": round((a + b * t_now) / s_now, 3),
                            "prefix_gain_after": round((a + b * t_aft) / s_aft, 3),
                        })
    # 指示書の見込みの再現: セル部分(概算 147.5 tok・c7-day-4)が全部共有→全部個人 × 8.1%/100tok
    instr = {"cell_est_c7d4": 147.5, "rule": rule, "drop": round(147.5 * rule / 100, 4)}
    doc = {"schema": "shibuya.bench/wallbounce-1003/r66-model/1", "fit": fit["coef"],
           "rule_per_100tok": rule, "k_values": ks, "b2_fixed_frac": b2_fixed_frac,
           "fov": {"detect_214deg": FOV_DETECT, "recog_46deg": FOV_RECOG},
           "instruction_reproduction": instr, "rows": rows,
           "note": "全部 推測。BN の当てはめは単 GPU・c64・o128・合成コーパス。当たる率は c7-day-4 の呼の列"}
    _w(args.out, doc)
    print(len(rows))
    return 0


def cmd_b2split(args: argparse.Namespace) -> int:
    """B2 の行の内訳(場所・路面=場所の定型文 / 可視・看板・地物=列挙)を c7-day-4 の呼の重みで。"""
    import collections

    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    tdir = Path(args.tape)
    b = pq.read_table(tdir / "blocks.parquet").to_pydict()
    txt = dict(zip(b["block_id"], b["text"]))
    t = pq.read_table(tdir / "calls.parquet", columns=["block_ids", "deferred"])
    t = t.filter(pc.equal(t["deferred"], 0))
    cnt = collections.Counter(pc.list_element(t["block_ids"], 2).to_pylist())
    fixed = lst = tot = 0
    for k, n in cnt.items():
        lines = txt[k].split("\n")
        fixed += n * sum(len(x) for x in lines if x.startswith(("[B2 場所]", "[B2 路面]")))
        lst += n * sum(len(x) for x in lines if x.startswith(("[B2 可視]", "[B2 看板]", "[B2 地物]")))
        tot += n * len(txt[k])
    doc = {"schema": "shibuya.bench/wallbounce-1003/r66-b2split/1", "calls": int(sum(cnt.values())),
           "b2_fixed_frac_chars": round(fixed / tot, 4), "b2_list_frac_chars": round(lst / tot, 4)}
    _w(args.out, doc)
    print(doc)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("run")
    sp.add_argument("--arm", choices=sorted(ARMS), required=True)
    sp.add_argument("--tape", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--samples", default="")
    sp.add_argument("--world", default="data/world/v2")
    sp.add_argument("--agents", type=int, default=5_000)
    sp.add_argument("--seed", type=int, default=1)
    sp.add_argument("--micro", type=int, default=2_000)
    st = sub.add_parser("tape")
    st.add_argument("--tape", required=True)
    st.add_argument("--out", required=True)
    st.add_argument("--replicas", type=int, default=7)
    st.add_argument("--windows", default="16,64,256")
    st.add_argument("--shuffle", type=int, default=0, help="0=テープの順・正の値=その seed で tick 内をでたらめに")
    sf = sub.add_parser("fit")
    sf.add_argument("--ledger", required=True)
    sf.add_argument("--out", required=True)
    s6 = sub.add_parser("p6")
    s6.add_argument("--out", required=True)
    s6.add_argument("--agents", type=int, default=400_000)
    s6.add_argument("--reps", type=int, default=50)
    sm = sub.add_parser("model")
    sm.add_argument("--run", action="append", required=True)
    sm.add_argument("--tape", required=True)
    sm.add_argument("--fit", required=True)
    sm.add_argument("--out", required=True)
    sm.add_argument("--windows", default="16,64,256,inf")
    sm.add_argument("--k", default="1.24,1.55", help="実トークン / 概算トークン(c7-day-4 の回帰の傾き,全体の比)")
    sm.add_argument("--b2-fixed-frac", default="0.30", help="B2 のうち場所・路面の行の割合(c7-day-4 の呼の重み)")
    sb = sub.add_parser("b2split")
    sb.add_argument("--tape", required=True)
    sb.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"b2split": cmd_b2split, "run": cmd_run, "tape": cmd_tape, "fit": cmd_fit, "p6": cmd_p6, "model": cmd_model}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
