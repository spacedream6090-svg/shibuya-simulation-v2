"""追加 A(指示書 2026-09-30 §1-2): 近接系の数値を node 幾何と edge 幾何で読み直す。

エンジン(src/shibuya)は変えない。関数を外から包んで数えるだけ(final は包まないランと同じになる=検算で確認)。

    D=docs/bench/analysis/proximity-edge-2026-09-30
    python $D/proximity_measure.py check --out $D/check.json          # 作業 1: 測り方の検算(合成の配列)
    python $D/proximity_measure.py runs --out $D/runs.json            # 作業 2: 12 本(方策 2 × 幾何 2 × 腕 3)
    python $D/proximity_measure.py summary --out $D/summary.json      # 表と率(node ÷ edge)
    python $D/proximity_measure.py one --policy mock --geometry edge --arm rel_on   # 1 本(JSON 1 行)

ランの共通: 層化抽出 5,000 体(C10 8b の標準=Q94/Q108・rel8b_measure.stratified_sample)・seed 1・語彙 v3・
空腹 energy・``--memory on``・呼数無制限(cli.run の既定)。腕: off / rel_on(``--relations on``)/
rel_copresent(``--relations on --rel-copresent on``)。classical=``--policy classical --chooser classical``。
絶対パスは書かない。壁時計は決定論でない。holdout(A1/A4・shibuya_jinryu・boundary_counts)は読まない。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
C10 = HERE.parent / "c10-relations-2026-09-28"
TWO_M = 2.0
PERSON_RE = re.compile(r"^P-(\d+)")
PAIR_CAP = 5_000_000
GRID_SHIFT = np.int64(1 << 20)
GRID_ROW = np.int64(1 << 21)

# ------------------------------------------------------------------ 測り方(検算の対象=ランでもこの関数だけを使う)


def pair_dist(xy: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """2 体の距離[m](float64 で計算)。"""
    x = np.asarray(xy, dtype=np.float64)
    d = x[np.asarray(a, dtype=np.int64)] - x[np.asarray(b, dtype=np.int64)]
    return np.sqrt((d * d).sum(axis=-1))


def within(xy: np.ndarray, a: np.ndarray, b: np.ndarray, r: float = TWO_M) -> np.ndarray:
    """距離 ≤ r(境界を含む=エンジンの ``talk_within_reach``・同席と同じ ``<=``)。"""
    return pair_dist(xy, a, b) <= r


def same_cell(cell: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """同じセル(かつ舞台の中=セル ≥ 0)。"""
    c = np.asarray(cell, dtype=np.int64)
    ca, cb = c[np.asarray(a, dtype=np.int64)], c[np.asarray(b, dtype=np.int64)]
    return (ca == cb) & (ca >= 0)


def pairs_within(xy: np.ndarray, ids: np.ndarray, r: float = TWO_M) -> tuple[np.ndarray, np.ndarray, bool]:
    """``ids`` の中の距離 ≤ r の組 (a, b)(a≠b・各組 1 回)。r の格子で自分+前向き 4 格子を突き合わせる。

    Returns: (a, b, 飛ばしたか)。候補が PAIR_CAP を超えたら空で返す(飛ばした=数える)。
    """
    ids = np.asarray(ids, dtype=np.int64)
    w = ids.size
    if w < 2:
        return np.zeros(0, np.int64), np.zeros(0, np.int64), False
    x = np.asarray(xy, dtype=np.float64)
    bx = np.floor(x[ids, 0] / r).astype(np.int64) + GRID_SHIFT
    by = np.floor(x[ids, 1] / r).astype(np.int64) + GRID_SHIFT
    key = bx * GRID_ROW + by
    order = np.argsort(key, kind="stable")
    ids, key = ids[order], key[order]
    pos = np.arange(w)
    ap_l, bp_l = [], []
    total = 0
    for dx, dy in ((0, 0), (1, -1), (1, 0), (1, 1), (0, 1)):  # 逐次: 近傍の格子 5 つ
        if (dx, dy) == (0, 0):
            lo = pos + 1
            hi = np.searchsorted(key, key, side="right")
        else:
            tk = key + dx * GRID_ROW + dy
            lo = np.searchsorted(key, tk, side="left")
            hi = np.searchsorted(key, tk, side="right")
        cnt = np.maximum(hi - lo, 0)
        s = int(cnt.sum())
        total += s
        if total > PAIR_CAP:
            return np.zeros(0, np.int64), np.zeros(0, np.int64), True
        if s:
            ap = np.repeat(pos, cnt)
            first = np.cumsum(cnt) - cnt
            bp = np.repeat(lo, cnt) + (np.arange(s) - np.repeat(first, cnt))
            ap_l.append(ap)
            bp_l.append(bp)
    if not ap_l:
        return np.zeros(0, np.int64), np.zeros(0, np.int64), False
    A = ids[np.concatenate(ap_l)]
    B = ids[np.concatenate(bp_l)]
    ok = within(x, A, B, r)
    return A[ok], B[ok], False


DIST_BINS = ("0m", "(0,2]", "(2,10]", "(10,50]", "(50,100]", ">100")


def dist_hist(d: np.ndarray) -> Counter:
    d = np.asarray(d, dtype=np.float64)
    c: Counter = Counter()
    c["0m"] += int((d < 1e-6).sum())
    c["(0,2]"] += int(((d >= 1e-6) & (d <= 2.0)).sum())
    c["(2,10]"] += int(((d > 2.0) & (d <= 10.0)).sum())
    c["(10,50]"] += int(((d > 10.0) & (d <= 50.0)).sum())
    c["(50,100]"] += int(((d > 50.0) & (d <= 100.0)).sum())
    c[">100"] += int((d > 100.0).sum())
    return c


def hist_share(c: Counter) -> dict[str, Any]:
    n = sum(c[k] for k in DIST_BINS)
    return {"n": n, **{k: int(c[k]) for k in DIST_BINS},
            "share": {k: round(c[k] / n, 4) if n else None for k in DIST_BINS},
            "share_le_2m": round((c["0m"] + c["(0,2]"]) / n, 4) if n else None,
            "share_le_10m": round((c["0m"] + c["(0,2]"] + c["(2,10]"]) / n, 4) if n else None,
            "share_gt_2m": round(1 - (c["0m"] + c["(0,2]"]) / n, 4) if n else None,
            "share_gt_10m": round((c["(10,50]"] + c["(50,100]"] + c[">100"]) / n, 4) if n else None}


def quant(x: list[float] | np.ndarray) -> dict[str, Any]:
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return {"n": 0}
    return {"n": int(x.size), "mean": round(float(x.mean()), 3),
            **{f"p{q}": round(float(np.percentile(x, q)), 3) for q in (10, 50, 90, 99)},
            "max": round(float(x.max()), 3)}


# ------------------------------------------------------------------ 作業 1: 検算
def cmd_check(args: argparse.Namespace) -> int:
    from shibuya.engine import resolve as R

    rows = []
    # (名前, A の xy, B の xy, A のセル, B のセル, 期待の距離, 期待の 2 m 内, 期待の同セル)
    cases = [
        ("1 m・同じセル", (0.0, 0.0), (1.0, 0.0), 7, 7, 1.0, True, True),
        ("3 m・同じセル", (0.0, 0.0), (3.0, 0.0), 7, 7, 3.0, False, True),
        ("同じ座標(0 m)・同じセル", (5.0, 5.0), (5.0, 5.0), 7, 7, 0.0, True, True),
        ("1 m・別のセル", (0.0, 0.0), (0.0, 1.0), 7, 8, 1.0, True, False),
        ("2 m ちょうど(境界)・同じセル", (0.0, 0.0), (2.0, 0.0), 7, 7, 2.0, True, True),
        ("3-4-5(斜め 5 m)", (0.0, 0.0), (3.0, 4.0), 7, 7, 5.0, False, True),
        ("格子をまたぐ 0.2 m(1.9 と 2.1)", (1.9, 0.0), (2.1, 0.0), 7, 7, 0.2, True, True),
        ("負の座標をまたぐ 0.2 m", (-0.1, -0.1), (0.1, -0.1), 7, 7, 0.2, True, True),
        ("舞台外(セル −1)の 0 m", (0.0, 0.0), (0.0, 0.0), -1, -1, 0.0, True, False),
    ]
    ok_all = True
    for name, pa, pb, ca, cb, ed, ew, ec in cases:
        xy = np.asarray([pa, pb], dtype=np.float32)  # SoA と同じ float32
        cell = np.asarray([ca, cb], dtype=np.int32)
        a, b = np.asarray([0]), np.asarray([1])
        d = float(pair_dist(xy, a, b)[0])
        w = bool(within(xy, a, b)[0])
        s = bool(same_cell(cell, a, b)[0])
        pa_, pb_, _sk = pairs_within(xy, np.asarray([0, 1]))
        enum = bool(pa_.size == 1)
        ag = SimpleNamespace(registry=SimpleNamespace(cell=cell, xy=xy))
        reach_cell = bool(R.talk_within_reach(ag, a, b, by_distance=False)[0])
        reach_dist = bool(R.talk_within_reach(ag, a, b, by_distance=True)[0])
        good = (abs(d - ed) < 1e-5 and w == ew and s == ec and enum == ew
                and reach_cell == ec and reach_dist == (ec and ew))
        ok_all &= good
        rows.append({"case": name, "A_xy": pa, "B_xy": pb, "A_cell": ca, "B_cell": cb,
                     "distance_m": round(d, 6), "expected_m": ed, "within_2m": w, "expected_within": ew,
                     "same_cell": s, "expected_same_cell": ec, "grid_enumerator_finds_pair": enum,
                     "engine_talk_within_reach_cell_proxy": reach_cell,
                     "engine_talk_within_reach_by_distance": reach_dist, "pass": good})
    # 格子の組の列挙 vs 総当たり(重なった点・格子の境の点を混ぜた 600 点)
    rng = np.random.default_rng(7)
    pts = np.concatenate([rng.uniform(-30, 30, (400, 2)), np.repeat(rng.uniform(-30, 30, (20, 2)), 5, axis=0),
                          np.column_stack([np.arange(100) * 2.0 - 100.0 + 1e-9, np.zeros(100)])]).astype(np.float32)
    ids = np.arange(pts.shape[0])
    A, B, _sk = pairs_within(pts, ids)
    got = {(min(a, b), max(a, b)) for a, b in zip(A.tolist(), B.tolist())}
    ii, jj = np.triu_indices(pts.shape[0], 1)
    brute = within(pts, ii, jj)
    want = {(int(a), int(b)) for a, b in zip(ii[brute].tolist(), jj[brute].tolist())}
    enum_ok = got == want and len(A) == len(got)
    ok_all &= enum_ok
    # 分布の箱の検算
    h = dist_hist(np.asarray([0.0, 1.0, 2.0, 2.0001, 10.0, 50.0, 100.0, 141.0]))
    hist_ok = [h[k] for k in DIST_BINS] == [1, 2, 2, 1, 1, 1]
    ok_all &= hist_ok
    doc = {"schema": "shibuya.bench/proximity-edge/check/1",
           "cases": rows,
           "grid_vs_bruteforce": {"points": int(pts.shape[0]), "pairs_grid": len(got), "pairs_bruteforce": len(want),
                                  "duplicates_in_grid": int(len(A) - len(got)), "equal": enum_ok,
                                  "note": "400 点一様+20 点×5 の重なり+2 m 間隔の格子の境の 100 点"},
           "hist_bins_check": {"input": [0.0, 1.0, 2.0, 2.0001, 10.0, 50.0, 100.0, 141.0],
                               "got": {k: h[k] for k in DIST_BINS}, "pass": hist_ok},
           "all_pass": bool(ok_all)}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"all_pass": ok_all, "enum_ok": enum_ok, "hist_ok": hist_ok}, ensure_ascii=False))
    return 0 if ok_all else 1


# ------------------------------------------------------------------ 作業 2: 1 本のラン
ARM_KW = {"off": {}, "rel_on": {"relations": "on"}, "rel_copresent": {"relations": "on", "rel_copresent": "on"}}
POLICY_KW = {"mock": {}, "classical": {"policy": "classical", "chooser": "classical"}}


def cmd_one(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(C10))
    import rel8b_measure as M  # type: ignore[import-not-found]  # 層化抽出(計測の口)を借りる

    from shibuya import cli
    from shibuya.agents.state import Activity
    from shibuya.engine import norm_meter as NM
    from shibuya.engine import relations as RL
    from shibuya.engine import resolve as R
    from shibuya.perception import renderer as RD

    M.use_sampler("stratified")
    if args.no_hooks:  # 検算: 包まないランの final・呼数(包んだランと一致すること=読むだけの証拠)
        from shibuya import cli as _cli
        kw0 = {"vocab_version": "v3", "memory": "on", "geometry": args.geometry,
               **POLICY_KW[args.policy], **ARM_KW[args.arm]}
        t0 = time.perf_counter()
        res0 = _cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, ticks=args.ticks, **kw0)
        print(json.dumps({"policy": args.policy, "geometry": args.geometry, "arm": args.arm, "no_hooks": True,
                          "final16": res0.final_hash[:16], "llm_calls": int(res0.llm_calls),
                          "wall_seconds_nondeterministic": round(time.perf_counter() - t0, 2)}))
        return 0
    st: dict[str, Any] = {
        "conv_open_dist": [], "conv_open_same_cell": 0, "conv_open_n": 0,
        "chance_dist": Counter(), "chance_rows": 0,
        "acq_dist": Counter(), "acq_dist_list": [],
        "co_active_slot_ticks": 0, "co_samecell_slot_ticks": 0, "co_active_dist": Counter(),
        "b5_calls": 0, "b5_items_hist": Counter(), "b5_dist": Counter(), "b5_dist_list_sample": [],
        "b5_dist_mismatch": 0, "b5_zero_calls": 0,
        "pairs_2m_total": 0, "pairs_2m_same_cell": 0, "pairs_2m_diff_cell": 0, "pairs_2m_diff_cell_awake": 0,
        "pairs_2m_zero_dist": 0, "pairs_2m_same_cell_awake": 0, "pair_ticks": 0, "pair_ticks_skipped": 0,
        "pairs_2m_diff_cell_max_tick": 0,
        "mv": 0, "mv_zero": 0, "mv_pos": 0, "mv_pos_disp_sum": 0.0, "mv_target": 0, "mv_target_zero": 0,
        "trip_starts": 0, "pairs_by_moving": Counter(), "conv_open_moving": Counter(),
    }
    prev = {"xy": None, "moving": None}

    # --- 会話の成立(set_conversing は成立の 2 か所=run.py の返事待ちの承諾と相互指名だけが呼ぶ)
    orig_sc = R.set_conversing

    def set_conversing(agents: Any, inviters: Any, invitees: Any) -> None:
        a = np.asarray(inviters, dtype=np.int64)
        b = np.asarray(invitees, dtype=np.int64)
        r = agents.registry
        st["conv_open_dist"] += pair_dist(r.xy, a, b).tolist()
        st["conv_open_same_cell"] += int(same_cell(r.cell, a, b).sum())
        st["conv_open_n"] += int(a.size)
        mv_ = np.asarray(r.activity) == int(Activity.MOVING)
        for x_, y_ in zip(mv_[a].tolist(), mv_[b].tolist()):  # 逐次: 成立の組の数ぶん(計測)
            st["conv_open_moving"][int(x_) + int(y_)] += 1
        return orig_sc(agents, inviters, invitees)

    R.set_conversing = set_conversing  # type: ignore[assignment]

    # --- 偶然(相手が 2 m 内の知人)の相手までの距離
    orig_choose = RL.RelationLayer.choose_talk_partners

    def choose(self: Any, agents: Any, tick: int, a: Any, fallback: Any, named_ok: Any, condition: Any,
               **k: Any) -> Any:
        out, origin = orig_choose(self, agents, tick, a, fallback, named_ok, condition, **k)
        sel = (np.asarray(origin) == 1) & (np.asarray(out) >= 0)
        if sel.any():
            aa = np.asarray(a, dtype=np.int64)[sel]
            bb = np.asarray(out, dtype=np.int64)[sel]
            st["chance_dist"].update(dist_hist(pair_dist(agents.registry.xy, aa, bb)))
            st["chance_rows"] += int(sel.sum())
        return out, origin

    RL.RelationLayer.choose_talk_partners = choose  # type: ignore[method-assign]

    # --- 同席(同セル ∧ 2 m 内の辺の欄)
    orig_co = RL.RelationLayer.copresent_step

    def co_step(self: Any, agents: Any, tick: int) -> None:
        orig_co(self, agents, tick)
        flat = self._co_active
        hits = self._hits if self._hits_tick == int(tick) else None
        if hits is not None:
            st["co_samecell_slot_ticks"] += int(hits[0].size)
        if flat is not None and flat.size:
            st["co_active_slot_ticks"] += int(flat.size)
            aa = flat // self.k
            jj = flat % self.k
            vv = np.asarray(agents.registry.rel_partner)[aa, jj].astype(np.int64)
            st["co_active_dist"].update(dist_hist(pair_dist(agents.registry.xy, aa, vv)))

    RL.RelationLayer.copresent_step = co_step  # type: ignore[method-assign]

    # --- 知人出現(同セルに現れた辺の相手)の距離
    orig_acq = RL.RelationLayer.acquaintance_candidates

    def acq(self: Any, agents: Any, tick: int, eligible: Any = None) -> Any:
        got = orig_acq(self, agents, tick, eligible)
        a_c, j_c = self._acq_pending
        if a_c.size:
            v = np.asarray(agents.registry.rel_partner)[a_c, j_c].astype(np.int64)
            d = pair_dist(agents.registry.xy, a_c, v)
            st["acq_dist"].update(dist_hist(d))
            st["acq_dist_list"] += d.tolist()
        return got

    RL.RelationLayer.acquaintance_candidates = acq  # type: ignore[method-assign]

    # --- B5 近接行(載った人と距離)
    orig_near = RD.Renderer._nearby_items

    def near(self: Any, i: int, cell: int, tc: Any) -> Any:
        items = orig_near(self, i, cell, tc)
        st["b5_calls"] += 1
        st["b5_items_hist"][len(items)] += 1
        if items:
            ids = np.asarray([int(PERSON_RE.match(t).group(1)) for t, _d in items], dtype=np.int64)
            d = pair_dist(self.agents.xy, np.full(ids.size, int(i)), ids)
            st["b5_dist"].update(dist_hist(d))
            # 描画の距離(max(d, 0.1))と再計算の一致(検算)
            rd = np.asarray([dv for _t, dv in items], dtype=np.float64)
            st["b5_dist_mismatch"] += int((np.abs(np.maximum(d, 0.1) - rd) > 1e-3).sum())
            if (d < 1e-6).all():
                st["b5_zero_calls"] += 1
        return items

    RD.Renderer._nearby_items = near  # type: ignore[method-assign]

    # --- 毎 tick(位置が確定した後=群・規範の計器の口): 2 m 内の組・歩行者の数え方(Q155)
    orig_obs = NM.GroupNormMeter.observe_tick

    def obs(self: Any, tick: int) -> None:
        orig_obs(self, tick)
        r = self.agents.registry
        xy = np.asarray(r.xy, dtype=np.float64)
        cell = np.asarray(r.cell, dtype=np.int64)
        act = np.asarray(r.activity)
        awake = act != int(Activity.SLEEPING)
        ids = np.flatnonzero(cell >= 0)
        A, B, skipped = pairs_within(xy, ids)
        st["pair_ticks"] += 1
        if skipped:
            st["pair_ticks_skipped"] += 1
        else:
            sc = cell[A] == cell[B]
            aw = awake[A] & awake[B]
            st["pairs_2m_total"] += int(A.size)
            st["pairs_2m_same_cell"] += int(sc.sum())
            st["pairs_2m_same_cell_awake"] += int((sc & aw).sum())
            st["pairs_2m_diff_cell"] += int((~sc).sum())
            st["pairs_2m_diff_cell_awake"] += int((~sc & aw).sum())
            st["pairs_2m_diff_cell_max_tick"] = max(st["pairs_2m_diff_cell_max_tick"], int((~sc).sum()))
            z0 = pair_dist(xy, A, B) < 1e-6
            st["pairs_2m_zero_dist"] += int(z0.sum())
            movst = act == int(Activity.MOVING)
            nm_ = movst[A].astype(np.int64) + movst[B].astype(np.int64)
            for lab_, k_ in (("both_stationary", 0), ("one_moving", 1), ("both_moving", 2)):  # 3 分類
                st["pairs_by_moving"][lab_] += int((nm_ == k_).sum())
                st["pairs_by_moving"][lab_ + "_zero_dist"] += int(((nm_ == k_) & z0).sum())
        # Q155: 歩行者の数え方(計器 norm_meter.py:234-235 の定義と、変位 0 を含めた数え方)
        mov = (act == int(Activity.MOVING)) & (cell >= 0) & (np.asarray(r.transit_state) == 0)
        tgt = np.asarray(r.target_node).astype(np.int64) >= 0
        if prev["xy"] is not None:
            disp = np.sqrt(((xy - prev["xy"]) ** 2).sum(axis=1))
            z = disp <= 1e-6
            st["mv"] += int(mov.sum())
            st["mv_zero"] += int((mov & z).sum())
            st["mv_pos"] += int((mov & ~z).sum())
            st["mv_pos_disp_sum"] += float(disp[mov & ~z].sum())
            st["mv_target"] += int((mov & tgt).sum())
            st["mv_target_zero"] += int((mov & tgt & z).sum())
            st["trip_starts"] += int((mov & ~prev["moving"]).sum())
        prev["xy"] = xy.copy()
        prev["moving"] = mov.copy()

    NM.GroupNormMeter.observe_tick = obs  # type: ignore[method-assign]

    kw = {"vocab_version": "v3", "memory": "on", "geometry": args.geometry,
          **POLICY_KW[args.policy], **ARM_KW[args.arm]}
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, ticks=args.ticks, **kw)
    wall = time.perf_counter() - t0
    m = res.run_manifest_fields()
    cc = dict(res.conversation_counters)
    rel = m.get("relations", {}) or {}
    counts = rel.get("counts", {}) if isinstance(rel, dict) else {}
    gn = m.get("group_norms", {}) or {}
    cod = np.asarray(st["conv_open_dist"], dtype=np.float64)
    b5_items = sum(st["b5_items_hist"].values())
    out = {
        "policy": args.policy, "geometry": args.geometry, "arm": args.arm, "args": kw,
        "final_hash": res.final_hash, "final16": res.final_hash[:16], "llm_calls": int(res.llm_calls),
        "wall_seconds_nondeterministic": round(wall, 2),
        "calls_by_condition": m.get("calls_by_condition", {}),
        "sessions_opened": cc.get("sessions_opened"),
        "conversation_counters": {k: v for k, v in cc.items() if k.startswith(("sessions", "conv_"))},
        "relations_counts": {k: v for k, v in counts.items()
                             if k.startswith(("acq_", "invite_", "copresent", "newcomer", "events"))},
        "relations_origins": rel.get("origins") if isinstance(rel, dict) else None,
        "chance": {"rows_origin_chance": st["chance_rows"], "partner_distance": hist_share(st["chance_dist"])},
        "acquaintance_appear_distance": {**hist_share(st["acq_dist"]), "quantiles": quant(st["acq_dist_list"])},
        "copresent": {"same_cell_edge_slot_ticks": st["co_samecell_slot_ticks"],
                      "active_2m_slot_ticks": st["co_active_slot_ticks"],
                      "active_2m_distance": hist_share(st["co_active_dist"]),
                      "events_written": counts.get("copresent_events")},
        "b5_near": {"renders": st["b5_calls"],
                    "items_per_render_hist": {str(k): v for k, v in sorted(st["b5_items_hist"].items())},
                    "items_per_render_mean": round(sum(k * v for k, v in st["b5_items_hist"].items()) / max(1, b5_items), 4),
                    "distance": hist_share(st["b5_dist"]),
                    "renders_all_listed_at_0m": st["b5_zero_calls"],
                    "check_render_distance_mismatch": st["b5_dist_mismatch"]},
        "conversation_open": {"pairs": st["conv_open_n"], "same_cell": st["conv_open_same_cell"],
                              "n_moving_in_pair_at_open": {str(k): v for k, v in sorted(st["conv_open_moving"].items())},
                              "distance": {**hist_share(dist_hist(cod)), "quantiles": quant(cod)}},
        "pairs_2m": {"ticks": st["pair_ticks"], "ticks_skipped": st["pair_ticks_skipped"],
                     "total": st["pairs_2m_total"], "zero_distance": st["pairs_2m_zero_dist"],
                     "same_cell": st["pairs_2m_same_cell"], "same_cell_both_awake": st["pairs_2m_same_cell_awake"],
                     "diff_cell": st["pairs_2m_diff_cell"], "diff_cell_both_awake": st["pairs_2m_diff_cell_awake"],
                     "diff_cell_per_tick": round(st["pairs_2m_diff_cell"] / max(1, st["pair_ticks"]), 3),
                     "diff_cell_both_awake_per_tick": round(st["pairs_2m_diff_cell_awake"] / max(1, st["pair_ticks"]), 3),
                     "diff_cell_max_tick": st["pairs_2m_diff_cell_max_tick"],
                     "by_moving_state": dict(st["pairs_by_moving"])},
        "q155_walkers": {"moving_in_stage_minutes": st["mv"], "moving_zero_disp": st["mv_zero"],
                         "moving_positive_disp(=meter walker def)": st["mv_pos"],
                         "mean_disp_m_per_walker_minute": round(st["mv_pos_disp_sum"] / max(1, st["mv_pos"]), 2),
                         "moving_with_target_minutes": st["mv_target"], "moving_with_target_zero_disp": st["mv_target_zero"],
                         "trip_starts": st["trip_starts"],
                         "minutes_per_trip": round(st["mv"] / max(1, st["trip_starts"]), 3)},
        "group_norms": {"instant_grouped_share": (gn.get("instant_group_walk") or {}).get("grouped_share"),
                        "instant_walker_minutes": (gn.get("instant_group_walk") or {}).get("walker_minutes"),
                        "cowalk_share": (gn.get("cowalk") or {}).get("cowalk_share_of_moving_minutes"),
                        "cowalk_episodes_5min": (gn.get("cowalk") or {}).get("episodes_5min"),
                        "cowalk_moving_minutes": (gn.get("cowalk") or {}).get("moving_agent_minutes")},
        "geometry_hops": int(getattr(res, "geometry_hops", 0)), "geometry_jammed": int(getattr(res, "geometry_jammed", 0)),
    }
    print(json.dumps(out, ensure_ascii=False, default=str))
    return 0


def cmd_runs(args: argparse.Namespace) -> int:
    combos = [(p, g, a) for p in ("mock", "classical") for a in ("off", "rel_on", "rel_copresent")
              for g in ("node", "edge")]
    if args.only:
        want = set(args.only.split(","))
        combos = [c for c in combos if f"{c[0]}:{c[1]}:{c[2]}" in want]

    def one(c: tuple[str, str, str]) -> dict[str, Any]:
        p, g, a = c
        cmd = [sys.executable, str(Path(__file__)), "one", "--policy", p, "--geometry", g, "--arm", a,
               "--world", args.world, "--agents", str(args.agents), "--seed", str(args.seed)]
        got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if got.returncode != 0:
            raise RuntimeError(f"{c}: {got.stderr[-3000:]}")
        row = json.loads(got.stdout.strip().splitlines()[-1])
        print(f"{p}/{g}/{a}: final {row['final16']} calls {row['llm_calls']:,} sessions {row['sessions_opened']} "
              f"wall {row['wall_seconds_nondeterministic']}s", flush=True)
        return row

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        rows = list(ex.map(one, combos))
    doc = {"schema": "shibuya.bench/proximity-edge/runs/1",
           "base": {"agents": args.agents, "seed": args.seed, "sample": "stratified (rel8b_measure.stratified_sample)",
                    "vocab": "v3", "memory": "on", "hunger": "energy (cli default)", "l4": "unlimited (cli default)"},
           "rows": rows}
    if args.merge and Path(args.out).exists():
        old = json.loads(Path(args.out).read_text(encoding="utf-8"))["rows"]
        keyf = lambda r: (r["policy"], r["geometry"], r["arm"])  # noqa: E731
        new = {keyf(r): r for r in rows}
        doc["rows"] = [new.pop(keyf(r), r) for r in old] + list(new.values())
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ 表と率(runs.json → summary.json)
def cmd_summary(args: argparse.Namespace) -> int:
    rows = json.loads(Path(args.runs).read_text(encoding="utf-8"))["rows"]
    R = {(r["policy"], r["geometry"], r["arm"]): r for r in rows}

    def g(r: dict, path: str) -> Any:
        x: Any = r
        for k in path.split("."):
            x = (x or {}).get(k) if isinstance(x, dict) else None
        return x

    items = {
        "chance_invites": ("relations_origins.chance.invites", "rel_on"),
        "chance_accepted": ("relations_origins.chance.accepted", "rel_on"),
        "chance_rows(origin=chance)": ("chance.rows_origin_chance", "rel_on"),
        "near_first_rows(2m acquaintance present)": ("relations_counts.invite_pick:near_first", "rel_on"),
        "chance_partner_share_0m": ("chance.partner_distance.share.0m", "rel_on"),
        "acq_wake_calls": ("calls_by_condition.ACQUAINTANCE", "rel_on"),
        "acq_appear": ("relations_counts.acq_appear", "rel_on"),
        "acq_appear_distance_p50": ("acquaintance_appear_distance.quantiles.p50", "rel_on"),
        "acq_appear_share_le_2m": ("acquaintance_appear_distance.share_le_2m", "rel_on"),
        "sessions_off": ("sessions_opened", "off"),
        "sessions_rel_on": ("sessions_opened", "rel_on"),
        "copresent_events_written": ("copresent.events_written", "rel_copresent"),
        "copresent_active_2m_slot_ticks": ("copresent.active_2m_slot_ticks", "rel_copresent"),
        "copresent_active_share_0m": ("copresent.active_2m_distance.share.0m", "rel_copresent"),
        "b5_items_per_render(rel_on)": ("b5_near.items_per_render_mean", "rel_on"),
        "b5_share_0m(rel_on)": ("b5_near.distance.share.0m", "rel_on"),
        "b5_share_gt_10m(rel_on)": ("b5_near.distance.share_gt_10m", "rel_on"),
        "b5_share_0m(off)": ("b5_near.distance.share.0m", "off"),
        "conv_open_share_gt_2m(off)": ("conversation_open.distance.share_gt_2m", "off"),
        "conv_open_share_gt_10m(off)": ("conversation_open.distance.share_gt_10m", "off"),
        "conv_open_p90_m(off)": ("conversation_open.distance.quantiles.p90", "off"),
        "conv_open_max_m(off)": ("conversation_open.distance.quantiles.max", "off"),
        "pairs_2m_diff_cell_per_tick(off)": ("pairs_2m.diff_cell_per_tick", "off"),
        "pairs_2m_share_0m(off)": (None, "off"),
        "walker_minutes(meter def)": ("q155_walkers.moving_positive_disp(=meter walker def)", "off"),
        "moving_minutes(incl. 0 disp)": ("q155_walkers.moving_in_stage_minutes", "off"),
        "moving_zero_disp": ("q155_walkers.moving_zero_disp", "off"),
        "mean_disp_m_per_walker_minute": ("q155_walkers.mean_disp_m_per_walker_minute", "off"),
        "minutes_per_trip": ("q155_walkers.minutes_per_trip", "off"),
        "instant_group_walk_share": ("group_norms.instant_grouped_share", "off"),
        "cowalk_5min_share": ("group_norms.cowalk_share", "off"),
        "wall_seconds(off)": ("wall_seconds_nondeterministic", "off"),
        "wall_seconds(rel_on)": ("wall_seconds_nondeterministic", "rel_on"),
        "wall_seconds(rel_copresent)": ("wall_seconds_nondeterministic", "rel_copresent"),
    }
    out: dict[str, Any] = {}
    for pol in ("mock", "classical"):
        tab = {}
        for name, (path, arm) in items.items():
            vals = {}
            for geo in ("node", "edge"):
                r = R[(pol, geo, arm)]
                if path is None:
                    p2 = r["pairs_2m"]
                    v = round(p2["zero_distance"] / max(1, p2["total"]), 5)
                else:
                    v = g(r, path)
                vals[geo] = v
            n, e = vals["node"], vals["edge"]
            ratio = round(n / e, 3) if isinstance(n, (int, float)) and isinstance(e, (int, float)) and e else None
            tab[name] = {**vals, "node_over_edge": ratio}
        s_n, s_e = tab["sessions_off"], tab["sessions_rel_on"]
        tab["session_increase_rel_on_over_off"] = {
            geo: round(s_e[geo] / s_n[geo] - 1, 4) for geo in ("node", "edge")}
        tab["checkpoints"] = {f"{geo}/{arm}": {"final16": R[(pol, geo, arm)]["final16"],
                                               "llm_calls": R[(pol, geo, arm)]["llm_calls"]}
                              for arm in ("off", "rel_on", "rel_copresent") for geo in ("node", "edge")}
        out[pol] = tab
    doc = {"schema": "shibuya.bench/proximity-edge/summary/1", "source": "runs.json", "by_policy": out}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="近接系の数値の node/edge 読み直し")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "one", "runs", "summary"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        if name in ("check", "runs", "summary"):
            sp.add_argument("--out", required=True)
        if name == "summary":
            sp.add_argument("--runs", default=str(HERE / "runs.json"))
        if name == "one":
            sp.add_argument("--policy", choices=tuple(POLICY_KW), required=True)
            sp.add_argument("--geometry", choices=("node", "edge"), required=True)
            sp.add_argument("--arm", choices=tuple(ARM_KW), required=True)
            sp.add_argument("--ticks", type=int, default=1440)
            sp.add_argument("--no-hooks", action="store_true")
        if name == "runs":
            sp.add_argument("--workers", type=int, default=2)
            sp.add_argument("--only", default="")
            sp.add_argument("--merge", action="store_true")
    args = ap.parse_args(argv)
    return {"check": cmd_check, "one": cmd_one, "runs": cmd_runs, "summary": cmd_summary}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
