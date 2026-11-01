"""第 5 期 空間の段 1: 受入の試験 3-4-5 の移動の 2 本(+面の外に居ない)を本物の世界のランで数える道具。

指示書 10-03 §8 3-4-5(物理的に不可能な行動を防ぐ試験)のうち移動の 2 本:

- (a) 刻みごと・全員: 位置の変化が歩く速さの上限(本人の速さ × 刻みの秒 × 坂の係数の最大)以内か、接続口を通ったもの
  (階が変わるのは接続口を通った刻みだけ)。移動の外で node が変わった体(乗車・降車・域外との出入り・初期配置)は理由
  ごとに数える(説明の付かない動きは 0 のはず)。
- (b) 同じ時刻に 2 か所にいない(状態の唯一性): 面の上の体(``nav_fi >= 0``)は車内・域外でない・セルが位置から導いた
  セルと同じ・node と位置の階の層が食い違わない。
- (c) 面の外に居ない: 面の上の体の (x, y, 階) がナビメッシュのランの中(建物の中は段 2 まで入口の点=節の点)。

〔段 1 の検収の直し〕(b) のセルの比べで -1 どうしを「一致」に数えない(面の上でセルが -1 の体は別の欄
``b_onmesh_cell_minus1``)。在不在の層が同じ刻みに退出と到着をした体(``presence.PlanExecutor._depart_now`` →
``_do_arrive``・M2=本段では直さない既存の穴)は「移動の外」に入れず別の欄 ``same_step_depart_arrive`` に数える(件数・
最大の距離・階が変わった数)。構成は v3 既定(``vocab_version="v3"``=19 構成の w6_v3_default と同じ)。

``engine.resolve.apply`` を包んで、刻みの前後の位置を見る(ランの結果は変えない=読むだけ)。

使い方(リポの根で・作業木の src を PYTHONPATH に):

    python docs/bench/analysis/spatial-2026-10/sp1/tools/accept_345.py --world data/world/v2_stage_5-1 \\
        --agents 5000 --ticks 1440 --out docs/bench/analysis/spatial-2026-10/sp1/accept_345.json

逐次ループ宣言: なし(刻みごとに全員の配列演算・ランの外の道具)。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="data/world/v2_stage_5-1")
    ap.add_argument("--agents", type=int, default=5000)
    ap.add_argument("--ticks", type=int, default=1440)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    from shibuya import cli
    from shibuya.engine import presence as PZ
    from shibuya.engine import resolve as R

    # M2: 在不在の層の退出と到着を、前の apply からの間で控える(読むだけ)
    io_dep: set[int] = set()
    prev_end: dict = {"xy": None, "fi": None}  # 前の刻みの終わりの位置(M2-r)
    io_arr: set[int] = set()
    orig_dep = PZ.PlanExecutor._depart_now
    orig_arr = PZ.PlanExecutor._do_arrive

    def dep_now(self, ids, *args_, **kw_):
        io_dep.update(np.asarray(ids, dtype=np.int64).tolist())
        return orig_dep(self, ids, *args_, **kw_)

    def do_arr(self, ids, *args_, **kw_):
        io_arr.update(np.asarray(ids, dtype=np.int64).tolist())
        return orig_arr(self, ids, *args_, **kw_)

    PZ.PlanExecutor._depart_now = dep_now
    PZ.PlanExecutor._do_arrive = do_arr

    orig = R.apply
    C = {"ticks": 0, "agent_ticks": 0, "walk_moves": 0, "walk_over_speed": 0, "floor_change": 0,
         "floor_change_via_link": 0, "floor_change_without_link": 0, "ext_moves": 0, "ext_by_reason": {},
         "unexplained_moves": 0, "max_walk_ratio": 0.0, "b_onmesh_riding_or_outside": 0, "b_cell_mismatch": 0,
         "b_band_mismatch": 0, "b_onmesh_cell_minus1": 0, "c_onmesh_agent_ticks": 0, "c_outside_surface": 0,
         "same_step_depart_arrive": 0, "same_step_depart_arrive_max_m": 0.0, "same_step_depart_arrive_floor_change": 0,
         "examples": []}

    def wrapped(plan_confirmed, losers, agents, world, tick, *args, **kw):
        geom = kw.get("geometry")
        nav = geom if getattr(geom, "is_nav", False) else None
        r = agents.registry
        if nav is None:
            return orig(plan_confirmed, losers, agents, world, tick, *args, **kw)
        both = io_dep & io_arr
        same = np.zeros(np.asarray(r.xy).shape[0], dtype=bool)
        if both:
            same[list(both)] = True
        io_dep.clear()
        io_arr.clear()
        xy0 = np.asarray(r.xy, dtype=np.float64).copy()
        fi0 = np.asarray(r.nav_fi).copy()
        node0 = np.asarray(r.node).copy()
        ts0 = np.asarray(r.transit_state).copy()
        nav_node0 = np.asarray(r.nav_node).copy()
        act0 = np.asarray(r.activity).copy()
        tgt0 = np.asarray(r.target_node).copy()
        ntgt0 = np.asarray(r.nav_tgt).copy()
        code_of = {}
        try:
            for a_, c_ in zip(np.asarray(plan_confirmed.agent_id).tolist(), np.asarray(plan_confirmed.action_code).tolist()):
                code_of[int(a_)] = int(c_)
        except Exception:  # noqa: BLE001
            pass
        links_seen: dict[int, int] = {}
        in_link: dict[int, bool] = {}
        # 刻みの初めに接続口の中に居た体(前の刻みから続く)
        P0 = nav.pool
        t_prev = np.asarray(r.nav_t, dtype=np.float64)
        was_in_link = np.zeros(t_prev.size, dtype=bool)
        for q in np.flatnonzero(np.asarray(r.nav_tgt) >= 0).tolist():
            st_, n_ = int(P0.r_start[q]), int(P0.r_len[q])
            if st_ >= 0 and n_ > 1:
                kk = int(np.searchsorted(P0.t[st_:st_ + n_], t_prev[q], side="right")) - 1
                if 0 <= kk < n_ - 1 and P0.link[st_ + kk] >= 0 and t_prev[q] > P0.t[st_ + kk] + 1e-9:
                    was_in_link[q] = True
        orig_adv = nav.advance

        def adv(aid, t_in, factor, wait, tk):
            res = orig_adv(aid, t_in, factor, wait, tk)
            P = nav.pool
            for q, k, tt in zip(np.asarray(aid).tolist(), np.asarray(res["links"]).tolist(),
                                np.asarray(res["t"]).tolist()):
                links_seen[q] = links_seen.get(q, 0) + int(k)
                # 刻みの終わりに接続口の中(区間の途中)に居る体=接続口を通っている(位置は接続口の両端の間の線の上)
                st_, n_ = int(P.r_start[q]), int(P.r_len[q])
                if st_ >= 0 and n_ > 1:
                    kk = int(np.searchsorted(P.t[st_:st_ + n_], tt, side="right")) - 1
                    if 0 <= kk < n_ - 1 and P.link[st_ + kk] >= 0 and tt > P.t[st_ + kk] + 1e-9:
                        in_link[q] = True
                    # 刻みの初めに接続口の中に居た体(前の刻みの続き)
            return res

        nav.advance = adv
        try:
            out = orig(plan_confirmed, losers, agents, world, tick, *args, **kw)
        finally:
            nav.advance = orig_adv
        xy1 = np.asarray(r.xy, dtype=np.float64)
        fi1 = np.asarray(r.nav_fi)
        node1 = np.asarray(r.node)
        ts1 = np.asarray(r.transit_state)
        C["ticks"] += 1
        n = xy1.shape[0]
        C["agent_ticks"] += n
        d = np.hypot(*(xy1 - xy0).T)
        moved = (d > 1e-6) | (fi1 != fi0)
        lk = np.zeros(n, dtype=np.int64)
        for q, k in links_seen.items():
            lk[q] = k
        walked = np.zeros(n, dtype=bool)
        walked[list(links_seen.keys())] = True
        for q in in_link:
            lk[q] += 1
        lk[was_in_link & walked] += 1
        C["agent_ticks_in_link"] = C.get("agent_ticks_in_link", 0) + int(len(in_link))
        vmax = nav.v_desired.astype(np.float64) * nav.tick_seconds * nav.factor_max + 1e-3
        # (a) 移動で動いた体
        wm = moved & walked
        C["walk_moves"] += int(wm.sum())
        ratio = np.where(wm, d / vmax, 0.0)
        C["max_walk_ratio"] = max(C["max_walk_ratio"], float(ratio.max()) if n else 0.0)
        over = wm & (d > vmax) & (lk == 0)
        C["walk_over_speed"] += int(over.sum())

        def ex(kind, idx):
            for q in np.flatnonzero(idx)[:3]:
                if sum(1 for e in C["examples"] if e["kind"] == kind) < 8:
                    C["examples"].append({"kind": kind, "tick": int(tick), "agent": int(q), "d_m": round(float(d[q]), 2),
                                          "node0": int(node0[q]), "node1": int(node1[q]), "fi0": int(fi0[q]),
                                          "fi1": int(fi1[q]), "act0": int(act0[q]), "act1": int(r.activity[q]),
                                          "tgt0": int(tgt0[q]), "tgt1": int(r.target_node[q]), "ntgt0": int(ntgt0[q]),
                                          "ntgt1": int(r.nav_tgt[q]), "code": code_of.get(int(q), -99),
                                          "ts0": int(ts0[q]), "ts1": int(ts1[q]), "links": int(lk[q])})
        ex("over_speed", over)
        fc = moved & (fi1 != fi0) & (fi0 >= 0) & (fi1 >= 0)
        C["floor_change"] += int(fc.sum())
        C["floor_change_via_link"] += int((fc & (lk > 0)).sum())
        C["floor_change_without_link"] += int((fc & (lk == 0) & walked).sum())
        ex("floor_change_without_link", fc & (lk == 0) & walked)
        # M2(〔再検収 M2-r〕刻みの終わりどうしで測る=退出と到着の xy は apply の外の rail_arrive が書く): 同じ刻みに退出と
        # 到着をした体(在不在の層)は別の欄(移動の外にも違反にも入れない)
        pe = prev_end["xy"]
        if pe is not None and pe.shape == xy1.shape:
            d_end = np.hypot(*(xy1 - pe).T)
            fi_end0 = prev_end["fi"]
        else:
            d_end, fi_end0 = d, fi0
        moved_end = (d_end > 1e-6) | (fi1 != fi_end0)
        ss = moved_end & same & ~walked
        C["same_step_depart_arrive"] += int(ss.sum())
        if ss.any():
            C["same_step_depart_arrive_max_m"] = max(C["same_step_depart_arrive_max_m"], round(float(d_end[ss].max()), 1))
        C["same_step_depart_arrive_floor_change"] += int((ss & (fi1 != fi_end0) & (fi_end0 >= 0) & (fi1 >= 0)).sum())
        ex("same_step_depart_arrive", ss)
        prev_end["xy"] = xy1.copy()
        prev_end["fi"] = np.asarray(fi1).copy()
        # 移動の外で動いた体(理由ごと)
        ext = moved & ~walked & ~same
        if ext.any():
            reasons = np.full(n, "unexplained", dtype=object)
            reasons[ext & (node0 < 0) & (node1 >= 0)] = "enter_from_outside_or_train"
            # 前の刻みの後(apply の外=域外・列車の過程)で node が書き換わり、この刻みの位置の確定で揃えた体
            reasons[ext & (nav_node0 != node0)] = "node_rewritten_between_steps(presence/rail)"
            reasons[ext & (node0 >= 0) & (node1 < 0)] = "leave_to_outside_or_train"
            # 経路の途中で新しい行動を選んで止まった体のうちスロープの中(線の上)に居た体は面の最も近い点へ寄せる(L3)
            snap = ext & (ntgt0 >= 0) & (np.asarray(r.nav_tgt) < 0) & (node0 >= 0) & (node1 >= 0) & (reasons == "unexplained")
            reasons[snap] = "stopped_in_ramp_snapped_to_surface"
            if snap.any():
                C["snap_max_m"] = max(C.get("snap_max_m", 0.0), round(float(d[snap].max()), 2))
            reasons[ext & (ts0 != ts1) & (reasons == "unexplained")] = "transit_state_change"
            reasons[ext & (node0 != node1) & (node1 >= 0) & (node0 >= 0) & (reasons == "unexplained")] = \
                "node_rewritten_by_engine(alight/rail/place)"
            reasons[ext & (nav_node0 < 0) & (reasons == "unexplained")] = "first_placement"
            for rsn in np.unique(reasons[ext]):
                C["ext_by_reason"][str(rsn)] = C["ext_by_reason"].get(str(rsn), 0) + int((reasons[ext] == rsn).sum())
            un = np.flatnonzero(ext & (reasons == "unexplained"))
            C["unexplained_moves"] += int(un.size)
            ex("unexplained", ext & (reasons == "unexplained"))
            C["ext_moves"] += int(ext.sum())
        # (b) 状態の唯一性
        on = fi1 >= 0
        C["b_onmesh_riding_or_outside"] += int((on & ((ts1 != 0) | (node1 < 0))).sum())
        ex("b_onmesh_riding_or_outside", on & ((ts1 != 0) | (node1 < 0)))
        cell_pos, band_pos = nav.cells(xy1[:, 0], xy1[:, 1], fi1)
        cell_now = np.asarray(r.cell)
        both_ok = (cell_pos >= 0) & (cell_now >= 0)
        C["b_cell_mismatch"] += int((on & (node1 >= 0) & both_ok & (cell_pos != cell_now)).sum())
        # -1 どうしを一致に数えない: 面の上の体でセルが -1(位置から導いたものか今のセルのどちらか)
        minus1 = on & (node1 >= 0) & ((cell_pos < 0) | (cell_now < 0))
        C["b_onmesh_cell_minus1"] += int(minus1.sum())
        ex("b_onmesh_cell_minus1", minus1)
        fb = np.where(on, nav.mesh.floor_band[np.maximum(fi1, 0)], 0)
        cb = np.where(cell_now >= 0, nav.cell_band[np.maximum(cell_now, 0)], 0)
        # 層の食い違い: 位置の階の層とセルの層が違う(その層のセルが無い列の地上への写しは除く=11c の形)
        C["b_band_mismatch"] += int((on & (cell_now >= 0) & (fb != cb) & (cb != 0)).sum())
        # (c) 面の外に居ない
        inl = np.zeros(n, dtype=bool)
        inl[list(in_link.keys())] = True
        C["c_skipped_in_link"] = C.get("c_skipped_in_link", 0) + int((on & inl).sum())
        idx = np.flatnonzero(on & ~inl)
        C["c_onmesh_agent_ticks"] += int(idx.size)
        m = nav.mesh
        bad = 0
        for q in idx:  # 逐次ループ宣言: 道具の検査だけ(面の上の体の数ぶん・ランの外)
            x, y, f = float(xy1[q, 0]), float(xy1[q, 1]), int(fi1[q])
            if m.locate(f, x, y) < 0 and not any(m.locate(f, x + dx, y + dy) >= 0 for dx in (-1e-3, 1e-3)
                                                 for dy in (-1e-3, 1e-3)):
                bad += 1
                if sum(1 for e in C["examples"] if e["kind"] == "c_outside") < 8:
                    r_, px_, py_, dd_ = m.nearest(f, x, y, 50.0)
                    C["examples"].append({"kind": "c_outside", "tick": int(tick), "agent": int(q), "x": round(x, 3),
                                          "y": round(y, 3), "fi": f, "node": int(node1[q]), "nav_tgt": int(r.nav_tgt[q]),
                                          "act": int(r.activity[q]), "walked": bool(walked[q]),
                                          "dist_to_surface_m": round(float(dd_), 3), "moved": bool(moved[q])})
        C["c_outside_surface"] += bad
        return out

    R.apply = wrapped
    t0 = time.perf_counter()
    try:
        res = cli.run(n_agents=a.agents, seed=a.seed, world_dir=a.world, ticks=a.ticks, tape_path=None, space="nav1",
                      vocab_version="v3")
    finally:
        R.apply = orig
        PZ.PlanExecutor._depart_now = orig_dep
        PZ.PlanExecutor._do_arrive = orig_arr
    C["wall_s"] = round(time.perf_counter() - t0, 1)
    C["final"] = res.final_hash[:16]
    C["space"] = res.run_manifest_fields()["space"]["meter"]
    Path(a.out).write_text(json.dumps(C, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in C.items() if k not in ("space",)}, ensure_ascii=False))
    return 0 if (C["walk_over_speed"] == 0 and C["floor_change_without_link"] == 0 and C["unexplained_moves"] == 0
                 and C["c_outside_surface"] == 0 and C["b_onmesh_riding_or_outside"] == 0
                 and C["b_onmesh_cell_minus1"] == 0 and C["b_cell_mismatch"] == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
