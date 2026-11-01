"""第 2 期 2-2 段 11a: 腕 distance の刻みごとの費用を 39 万体で測る(P4 の宣言の材料・アジェンダ §7・検収 M2)。

体の位置は世界資産(W1)の歩行グラフのノードの座標(と層)から引く(node の座標=立っている体はノードに重なる=いまの
位置の出どころと同じ)。2 つの置き方: ``uniform``(ノードを一様に)・``hub``(体の 2 割を上位 50 ノードに集める=駅前の
混み方の上側)。関係辺は体あたり 15 本(相手は一様に引く・1 割は空)。測るのは決定論でない壁時計(同じ PC・他の作業と
同居)。絶対パスは書かない。

測るもの: 索引の組み立て・B5 の近接行の問い合わせ(1 描画)・体 × k の辺の見え方(``ProximityRule.edge_view``=同席と
知人出現が共有する 1 回)・1 組の判定(``reach``=離脱・返事待ち・3 人会話の 1 組)・気づく抽選(範囲の中の辺を全部
``philox_array`` でまとめて引く=親の判断 10-14 の 1)。検収の前の形(同席が全辺に ``reach``・``_parts`` が全員の座標を
float64 に写す)と、1 組ずつ ``stream`` で引く前の形(2,000 組)も同じ配置で測って並べる。

    python docs/bench/analysis/wallbounce-1012/prox22/tools/index_cost.py --out <記録の置き場>/index_cost.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np


def _best(fn, reps: int = 3) -> tuple[float, object]:
    best, out = float("inf"), None
    for _ in range(reps):  # 逐次: 繰り返しの数ぶん(計測)
        t0 = time.perf_counter()
        out = fn()
        best = min(best, time.perf_counter() - t0)
    return best, out


def _old_parts_reach(ag, a, b, d):
    """検収の前の ``_parts``(全員の座標を float64 に写してから集める)で ``reach`` を引く(比べるためだけ)。"""
    r = ag.registry
    cell = np.asarray(r.cell)
    on = (cell[a] >= 0) & (cell[b] >= 0)
    band = np.asarray(r.band)
    xy = np.asarray(r.xy, dtype=np.float64)
    dd = xy[a] - xy[b]
    dist = np.sqrt((dd * dd).sum(axis=-1))
    unit = np.asarray(r.poi_ref)
    su = (unit[a] >= 0) & (unit[a] == unit[b])
    return on & (((band[a] == band[b]) & (dist <= d)) | su)


def _loop_u(rule, T, a, b):
    """1 組ずつ ``stream`` で引く前の形(比べるためだけ・値は ``notice_u`` と同じ=突き合わせる)。"""
    from shibuya.core.rng import k19_counters, stream

    from shibuya.engine import proximity as P

    tk = rule.time_key(T)
    return np.array([stream(rule.seed, P.NOTICE_DOMAIN, *k19_counters(tk, int(x), int(y))).random()
                     for x, y in zip(a.tolist(), b.tolist())])  # 逐次: 組の数ぶん(計測)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--agents", type=int, default=390_067)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from shibuya.engine import proximity as P
    from shibuya.world.assets import load_assets

    A = load_assets(args.world)
    nxy = np.asarray(A.node_xy, dtype=np.float32)
    nband = np.asarray(A.node_band, dtype=np.int8)
    ncell = np.asarray(A.node_cell, dtype=np.int32)
    rng = np.random.default_rng(args.seed)
    n = int(args.agents)
    rows = {}
    for layout in ("uniform", "hub"):
        node = rng.integers(0, nxy.shape[0], n)
        if layout == "hub":
            hubs = rng.choice(nxy.shape[0], 50, replace=False)
            sel = rng.random(n) < 0.2
            node[sel] = hubs[rng.integers(0, 50, int(sel.sum()))]
        unit = np.where(rng.random(n) < 0.15, rng.integers(0, 20_000, n), -1).astype(np.int32)
        reg = SimpleNamespace(xy=nxy[node].copy(), band=nband[node].copy(), cell=ncell[node].copy(), poi_ref=unit)
        ag = SimpleNamespace(registry=reg, n=n)
        # 単位の絞り(親の判断 10-14 の 2)の費用も入れる: POI 2 万の店のセル(費用だけを測る=どの体が単位に残るかは問わない)
        pcell = rng.integers(0, int(ncell.max()) + 1, 20_000)
        rule = P.ProximityRule(d=2.0, seed=7, poi_cell=pcell)
        lay = P.ProximityLayer(rule)
        t_build, idx = _best(lambda: lay.build_index(ag))
        nbytes = sum(int(getattr(idx, k).nbytes) for k in ("ids", "x", "y", "bands", "unit", "key", "pos"))
        q = rng.integers(0, n, 1000)
        q = q[reg.cell[q] >= 0]
        x64 = reg.xy.astype(np.float64)

        def b5_queries():
            tot = 0
            for i in q.tolist():  # 逐次: 描画の数ぶん(計測=1 描画 1 回の問い合わせ)
                _qq, ids, _d = idx.query_many(x64[i, 0], x64[i, 1], int(reg.band[i]), P.B5_RADIUS_M)
                tot += ids.size
            return tot

        t_b5, b5_tot = _best(b5_queries, reps=1)
        # 関係辺 15 本/体(1 割は空)
        k = 15
        partner = rng.integers(0, n, (n, k)).astype(np.int32)
        partner[rng.random((n, k)) < 0.1] = -1

        def edges():
            a, j = np.nonzero(partner != -1)
            v = partner[a, j].astype(np.int64)
            a = a.astype(np.int64)
            on = (reg.cell[a] >= 0) & (reg.cell[v] >= 0)
            return a[on], v[on]

        t_edges, (ea, ev) = _best(edges, reps=1)
        t_view, view = _best(lambda: rule.edge_view(ag, ea, ev), reps=2)
        inr, _dist, reach = view
        t_old_co, old_reach = _best(lambda: _old_parts_reach(ag, ea, ev, rule.d), reps=1)
        assert np.array_equal(old_reach, P.ProximityRule(d=2.0, seed=7).edge_view(ag, ea, ev)[2])  # 絞らない規則と同じ答え
        one_a, one_b = np.array([int(q[0])]), np.array([int(q[1])])
        t_pair, _ = _best(lambda: rule.reach(ag, one_a, one_b), reps=50)
        t_pair_old, _ = _best(lambda: _old_parts_reach(ag, one_a, one_b, rule.d), reps=50)
        fa, fb = ea[inr], ev[inr]
        t_draw, u_all = _best(lambda: rule.notice_u(100, fa, fb), reps=3)
        t_loop, u_loop = _best(lambda: _loop_u(rule, 100, fa[:2000], fb[:2000]), reps=1)
        assert np.array_equal(u_all[:2000], u_loop)
        rows[layout] = {
            "agents": n, "indexed": len(idx), "index_build_s": round(t_build, 4), "index_bytes": nbytes,
            "index_bytes_per_agent": round(nbytes / max(1, len(idx)), 1),
            "b5_queries": int(q.size), "b5_query_ms_mean": round(1000 * t_b5 / max(1, q.size), 3),
            "b5_candidates_mean": round(b5_tot / max(1, q.size), 1),
            "edges_on_stage": int(ea.size), "edge_gather_s": round(t_edges, 3),
            "edge_view_s(shared: notice range + copresent reach)": round(t_view, 3),
            "edges_in_notice_range": int(inr.sum()), "edges_reach": int(reach.sum()),
            "before_review_copresent_reach_all_edges_s": round(t_old_co, 3),
            "pair_reach_ms": round(1000 * t_pair, 4), "before_review_pair_reach_ms": round(1000 * t_pair_old, 4),
            "notice_draw_all_in_range_s": round(t_draw, 4),
            "notice_draw_us_per_pair": round(1e6 * t_draw / max(1, fa.size), 3),
            "before_notice_draw_us_per_pair_loop": round(1e6 * t_loop / 2000, 2),
        }
        print(layout, rows[layout], flush=True)
    doc = {"schema": "shibuya.bench/prox22/index_cost/3",
           "note": "壁時計は決定論でない(同じ PC・ほかの作業と同居)。位置=W1 のノードの座標。hub=体の 2 割を上位 50 ノード。"
                   "before_review_*=検収の前の形(同席が全辺に reach・_parts が全員の座標を float64 に写す)。"
                   "notice_draw_*=範囲の中の辺を全部 philox_array で引く・before_notice_draw_*=1 組ずつ stream で引く形"
                   "(2,000 組・値は同じ=突き合わせた)",
           "rows": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
