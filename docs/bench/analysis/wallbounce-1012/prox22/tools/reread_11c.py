"""第 2 期 2-2 段 11c: 近接系の読み直し(計測だけ・判定しない)。

正: 実装アジェンダ ``docs/design/v2-proximity-distance-implementation-agenda.md`` §4(段 11c)・§1-2 の表・決定 10-03 §4
(B5 の単位あたりの在室人数の分布=特に最大・屋内の体の会話が何件失われるか)。前の読み直し
``docs/bench/analysis/proximity-edge-2026-09-30/proximity_measure.py`` と同じ測り方(関数を外から包んで数えるだけ=final は
包まないランと同じ)に、11c の量(B5 の単位の在室人数・屋内の会話の損失・腕 distance の不変条件)を足した。

    D=docs/bench/analysis/wallbounce-1012/prox22
    python $D/tools/reread_11c.py check --out $D/check_11c.json                 # 測り方の検算(合成の配列)
    python $D/tools/reread_11c.py runs --label wt --modes cell,distance --out <scratch>/wt.json
    python $D/tools/reread_11c.py runs --label head --src <HEAD の src の写し> --modes cell --out <scratch>/head.json
    python $D/tools/reread_11c.py table --runs <scratch>/head.json <scratch>/wt.json --out $D/reread_11c.json

ランの共通(前の読み直しと同じ): 層化抽出 5,000 体(C10 8b の標準=``rel8b_measure.stratified_sample``)・seed 1・語彙 v3・
空腹 energy・``--memory on``・呼数無制限(``cli.run`` の既定)・1 日。腕: off / rel_on / rel_copresent × 方策 mock・classical
× 幾何 node(edge は ``--geometry``)× 判定 cell(HEAD・作業木)・distance(作業木・d=2 m)。
**判定の腕は環境変数ではなく** ``engine.proximity.set_arm``(作業木の src だけ)。HEAD の写しには腕が無い=cell だけ。
絶対パスは書かない。壁時計は決定論でない。holdout は読まない。
"""

from __future__ import annotations

import argparse
import json
import os
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
REPO = HERE.parents[5]
C10 = REPO / "docs" / "bench" / "analysis" / "c10-relations-2026-09-28"
TWO_M = 2.0
PERSON_RE = re.compile(r"^P-(\d+)")
PAIR_CAP = 5_000_000
GRID_SHIFT = np.int64(1 << 20)
GRID_ROW = np.int64(1 << 21)
OCC_BINS = ((1, 1), (2, 4), (5, 9), (10, 49), (50, 99), (100, 499), (500, 999), (1000, 1 << 40))
CATS = ("in_store", "at_home", "at_work", "at_school", "stationary_other", "moving", "off_stage")
INDOOR = frozenset({"in_store", "at_home", "at_work", "at_school"})


# ------------------------------------------------------------------ 測り方(前の読み直しと同じ関数)
#: B5 の単位の絞り(親の判断 10-14 の 2): POI ごとのセル(``world.pois.cell``)。組み立ての後に置く。None=絞らない。
_UNIT_CTX: dict[str, Any] = {"pcell": None}


def unit_of(r: Any, ids: np.ndarray) -> np.ndarray:
    """体 ``ids`` の B5 の単位=在席の印があり、その店のセルの中に居る体だけ(作業木の ``ProximityRule._unit_at`` の写し)。"""
    ids = np.asarray(ids, dtype=np.int64)
    u = np.asarray(r.poi_ref)[ids].astype(np.int64)
    pc = _UNIT_CTX.get("pcell")
    if pc is None:
        return u
    ok = (u >= 0) & (u < pc.size)
    c = np.asarray(r.cell)[ids].astype(np.int64)
    ok &= c == pc[np.where(ok, u, 0)]
    return np.where(ok, u, -1)


def pair_dist(xy: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    x = np.asarray(xy, dtype=np.float64)
    d = x[np.asarray(a, dtype=np.int64)] - x[np.asarray(b, dtype=np.int64)]
    return np.sqrt((d * d).sum(axis=-1))


def pairs_within(xy: np.ndarray, ids: np.ndarray, r: float = TWO_M) -> tuple[np.ndarray, np.ndarray, bool]:
    """``ids`` の中の距離 ≤ r の組(各組 1 回)。r の格子で自分+前向き 4 格子(前の読み直しの関数と同じ)。"""
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
            first = np.cumsum(cnt) - cnt
            ap_l.append(np.repeat(pos, cnt))
            bp_l.append(np.repeat(lo, cnt) + (np.arange(s) - np.repeat(first, cnt)))
    if not ap_l:
        return np.zeros(0, np.int64), np.zeros(0, np.int64), False
    A = ids[np.concatenate(ap_l)]
    B = ids[np.concatenate(bp_l)]
    ok = pair_dist(x, A, B) <= r
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
    le2 = c["0m"] + c["(0,2]"]
    return {"n": n, **{k: int(c[k]) for k in DIST_BINS},
            "share_0m": round(c["0m"] / n, 4) if n else None,
            "share_le_2m": round(le2 / n, 4) if n else None,
            "share_gt_2m": round(1 - le2 / n, 4) if n else None,
            "share_gt_10m": round((c["(10,50]"] + c["(50,100]"] + c[">100"]) / n, 4) if n else None}


def quant(x: list[float] | np.ndarray) -> dict[str, Any]:
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return {"n": 0}
    return {"n": int(x.size), "mean": round(float(x.mean()), 3),
            **{f"p{q}": round(float(np.percentile(x, q)), 3) for q in (10, 50, 90, 99)},
            "max": round(float(x.max()), 3)}


def occ_label(lo: int, hi: int) -> str:
    return f"{lo}" if lo == hi else (f"{lo}+" if hi >= (1 << 39) else f"{lo}-{hi}")


def reach_d(r: Any, a: np.ndarray, b: np.ndarray, d: float) -> tuple[np.ndarray, np.ndarray]:
    """腕 distance の判定(同じ層・距離 ≤ d、または同じ B5 の単位・舞台の中)と、そのうち単位だけで届く組。

    作業木の ``engine.proximity.ProximityRule.reach`` と同じ式を、HEAD の写しでも測れるように計器の側に写した(検算で一致)。
    """
    cell = np.asarray(r.cell)
    on = (cell[a] >= 0) & (cell[b] >= 0)
    band = np.asarray(r.band)
    sb = band[a] == band[b]
    dist = pair_dist(r.xy, a, b)
    ua = unit_of(r, a)
    su = (ua >= 0) & (ua == unit_of(r, b))
    near = sb & (dist <= d)
    return on & (near | su), on & su & ~near


def categories(r: Any, ids: np.ndarray, sched: Any) -> list[str]:
    """体 → 屋内の種類(在店=B5 の単位・自宅・職場・学校のセルに止まっている・ほかに止まっている・移動中・舞台の外)。"""
    from shibuya.agents.state import Activity

    ids = np.asarray(ids, dtype=np.int64)
    cell = np.asarray(r.cell)[ids].astype(np.int64)
    act = np.asarray(r.activity)[ids]
    unit = unit_of(r, ids)
    mv = act == int(Activity.MOVING)

    def col(name: str) -> np.ndarray:
        v = getattr(sched, name, None) if sched is not None else None
        return np.full(ids.size, -9, np.int64) if v is None else np.asarray(v, dtype=np.int64)[ids]

    home, work, school = col("home_cell"), col("work_cell"), col("school_cell")
    out = []
    for k in range(ids.size):  # 逐次: 会話の成立の数ぶん(計測)
        if cell[k] < 0:
            out.append("off_stage")
        elif unit[k] >= 0:
            out.append("in_store")
        elif mv[k]:
            out.append("moving")
        elif cell[k] == home[k]:
            out.append("at_home")
        elif cell[k] == work[k]:
            out.append("at_work")
        elif cell[k] == school[k]:
            out.append("at_school")
        else:
            out.append("stationary_other")
    return out


def pair_class(ca: str, cb: str) -> str:
    n = int(ca in INDOOR) + int(cb in INDOOR)
    return ("both_indoor", "one_indoor", "outdoor")[2 - n] if n else "outdoor"


# ------------------------------------------------------------------ 検算
def cmd_check(args: argparse.Namespace) -> int:
    ok_all = True
    rng = np.random.default_rng(7)
    pts = np.concatenate([rng.uniform(-30, 30, (400, 2)), np.repeat(rng.uniform(-30, 30, (20, 2)), 5, axis=0),
                          np.column_stack([np.arange(100) * 2.0 - 100.0 + 1e-9, np.zeros(100)])]).astype(np.float32)
    A, B, _sk = pairs_within(pts, np.arange(pts.shape[0]))
    got = {(min(a, b), max(a, b)) for a, b in zip(A.tolist(), B.tolist())}
    ii, jj = np.triu_indices(pts.shape[0], 1)
    want = {(int(a), int(b)) for a, b, w in zip(ii.tolist(), jj.tolist(), (pair_dist(pts, ii, jj) <= 2.0).tolist())
            if w}
    enum_ok = got == want and len(A) == len(got) == 781
    ok_all &= enum_ok
    # 計器の側の判定の写しと、作業木の規則(engine.proximity)が同じ答え(体 300・層 2・単位あり)
    rule_ok = None
    try:
        from shibuya.engine import proximity as P

        n = 300
        reg = SimpleNamespace(xy=rng.uniform(0, 8, (n, 2)).astype(np.float32),
                              cell=rng.integers(-1, 3, n).astype(np.int32), band=rng.integers(0, 2, n).astype(np.int8),
                              poi_ref=np.where(rng.random(n) < 0.3, rng.integers(0, 4, n), -1).astype(np.int32))
        ii2, jj2 = np.triu_indices(n, 1)
        pcell = np.array([0, 1, 2, 0], dtype=np.int64)          # 合成の POI のセル(単位の絞りも突き合わせる)
        _UNIT_CTX["pcell"] = pcell
        try:
            mine, mine_u = reach_d(reg, ii2, jj2, 2.0)
        finally:
            _UNIT_CTX["pcell"] = None
        rule = P.ProximityRule(d=2.0, poi_cell=pcell)
        ag = SimpleNamespace(registry=reg, n=n)
        rule_ok = bool(np.array_equal(mine, rule.reach(ag, ii2, jj2))
                       and np.array_equal(mine_u, rule.by_unit(ag, ii2, jj2)))
        ok_all &= rule_ok
    except ImportError:
        pass
    h = dist_hist(np.asarray([0.0, 1.0, 2.0, 2.0001, 10.0, 50.0, 100.0, 141.0]))
    hist_ok = [h[k] for k in DIST_BINS] == [1, 2, 2, 1, 1, 1]
    ok_all &= hist_ok
    doc = {"schema": "shibuya.bench/prox22/check/1",
           "grid_vs_bruteforce": {"points": int(pts.shape[0]), "pairs": len(got), "equal": enum_ok},
           "reach_copy_equals_engine_rule": rule_ok, "hist_bins": hist_ok, "all_pass": bool(ok_all)}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc, ensure_ascii=False))
    return 0 if ok_all else 1


# ------------------------------------------------------------------ 1 本のラン
ARM_KW = {"off": {}, "rel_on": {"relations": "on"}, "rel_copresent": {"relations": "on", "rel_copresent": "on"}}
POLICY_KW = {"mock": {}, "classical": {"policy": "classical", "chooser": "classical"}}


def cmd_one(args: argparse.Namespace) -> int:  # noqa: C901 (計器を 1 か所に並べる)
    sys.path.insert(0, str(C10))
    import rel8b_measure as M8  # type: ignore[import-not-found]

    from shibuya import cli
    from shibuya.agents.state import Activity
    from shibuya.engine import norm_meter as NM
    from shibuya.engine import relations as RL
    from shibuya.engine import resolve as R
    from shibuya.engine.systems import build as BLD
    from shibuya.perception import renderer as RD

    M8.use_sampler("stratified")
    has_prox = True
    try:
        from shibuya.engine import proximity as P
    except ImportError:
        has_prox = False
        P = None  # type: ignore[assignment]
    if args.mode != "cell":
        if not has_prox:
            raise SystemExit("この src には腕 distance が無い")
        P.set_arm(args.mode)
        P.set_d(args.d)
    elif has_prox:
        P.set_arm("cell")
    D = float(args.d)
    st: dict[str, Any] = {
        "open_dist": [], "open_same_cell": 0, "open_n": 0, "open_reach_d": 0, "open_by_unit": 0,
        "open_class": Counter(), "open_lost_class": Counter(), "open_lost_cats": Counter(), "open_cats": Counter(),
        "open_over_d_not_unit": 0, "join_n": 0, "join_bad": 0,
        "chance_dist": Counter(), "chance_rows": 0, "acq_dist": Counter(), "acq_dist_list": [],
        "co_active_slot_ticks": 0, "co_active_dist": Counter(),
        "b5_calls": 0, "b5_items_hist": Counter(), "b5_dist": Counter(), "b5_acq": 0, "b5_items": 0, "b5_gt_radius": 0,
        "pair_ticks": 0, "pairs_2m_total": 0, "pairs_2m_zero": 0, "pairs_2m_diff_cell": 0,
        "pairs_2m_diff_cell_awake": 0, "pairs_2m_diff_band": 0, "pairs_2m_diff_cell_max_tick": 0, "pairs_skipped": 0,
        "occ_hist": Counter(), "occ_max": 0, "occ_max_poi": -1, "occ_max_tick": -1, "occ_units_max": 0,
        "occ_max_raw": 0, "occ_out_of_cell": 0, "occ_seated": 0,
        "occ_poi_max": {}, "same_xy_max": 0, "same_xy_max_tick": -1,
    }
    box_holder: dict[str, Any] = {}

    orig_build = BLD.build

    def build(call_args: Any) -> Any:
        box = orig_build(call_args)
        box_holder["box"] = box
        _UNIT_CTX["pcell"] = np.asarray(box.soa.world.pois.cell, dtype=np.int64)
        return box

    BLD.build = build  # type: ignore[assignment]

    def sched() -> Any:
        b = box_holder.get("box")
        return None if b is None else b.fx.schedule

    orig_sc = R.set_conversing

    def set_conversing(agents: Any, inviters: Any, invitees: Any) -> None:
        a = np.asarray(inviters, dtype=np.int64)
        b = np.asarray(invitees, dtype=np.int64)
        r = agents.registry
        d = pair_dist(r.xy, a, b)
        st["open_dist"] += d.tolist()
        cell = np.asarray(r.cell, dtype=np.int64)
        st["open_same_cell"] += int(((cell[a] == cell[b]) & (cell[a] >= 0)).sum())
        st["open_n"] += int(a.size)
        ok, by_u = reach_d(r, a, b, D)
        st["open_reach_d"] += int(ok.sum())
        st["open_by_unit"] += int(by_u.sum())
        st["open_over_d_not_unit"] += int(((d > D) & ~by_u).sum())
        ca, cb = categories(r, a, sched()), categories(r, b, sched())
        for k in range(a.size):  # 逐次: 成立の組の数ぶん(計測)
            pc = pair_class(ca[k], cb[k])
            key = "|".join(sorted((ca[k], cb[k])))
            st["open_class"][pc] += 1
            st["open_cats"][key] += 1
            if not bool(ok[k]):
                st["open_lost_class"][pc] += 1
                st["open_lost_cats"][key] += 1
        return orig_sc(agents, inviters, invitees)

    R.set_conversing = set_conversing  # type: ignore[assignment]

    orig_join = R.join_conversation

    def join_conversation(agents: Any, joiners: Any, hosts: Any, tick: Any) -> Any:
        a = np.asarray(joiners, dtype=np.int64)
        b = np.asarray(hosts, dtype=np.int64)
        ok, _u = reach_d(agents.registry, a, b, D)
        st["join_n"] += int(a.size)
        st["join_bad"] += int((~ok).sum())
        return orig_join(agents, joiners, hosts, tick)

    R.join_conversation = join_conversation  # type: ignore[assignment]

    orig_choose = RL.RelationLayer.choose_talk_partners

    def choose(self: Any, agents: Any, tick: int, a: Any, *rest: Any, **kw: Any) -> Any:
        out, origin = orig_choose(self, agents, tick, a, *rest, **kw)
        sel = (np.asarray(origin) == 1) & (np.asarray(out) >= 0)
        if sel.any():
            aa = np.asarray(a, dtype=np.int64)[sel]
            bb = np.asarray(out, dtype=np.int64)[sel]
            st["chance_dist"].update(dist_hist(pair_dist(agents.registry.xy, aa, bb)))
            st["chance_rows"] += int(sel.sum())
        return out, origin

    RL.RelationLayer.choose_talk_partners = choose  # type: ignore[method-assign]

    orig_co = RL.RelationLayer.copresent_step

    def co_step(self: Any, agents: Any, tick: int, *rest: Any, **kw: Any) -> None:
        orig_co(self, agents, tick, *rest, **kw)
        flat = self._co_active
        if flat is not None and flat.size:
            st["co_active_slot_ticks"] += int(flat.size)
            aa = flat // self.k
            vv = np.asarray(agents.registry.rel_partner)[aa, flat % self.k].astype(np.int64)
            st["co_active_dist"].update(dist_hist(pair_dist(agents.registry.xy, aa, vv)))

    RL.RelationLayer.copresent_step = co_step  # type: ignore[method-assign]

    orig_acq = RL.RelationLayer.acquaintance_candidates

    def acq(self: Any, agents: Any, tick: int, *rest: Any, **kw: Any) -> Any:
        got = orig_acq(self, agents, tick, *rest, **kw)
        a_c, j_c = self._acq_pending
        if a_c.size:
            v = np.asarray(agents.registry.rel_partner)[a_c, j_c].astype(np.int64)
            d = pair_dist(agents.registry.xy, a_c, v)
            st["acq_dist"].update(dist_hist(d))
            st["acq_dist_list"] += d.tolist()
        return got

    RL.RelationLayer.acquaintance_candidates = acq  # type: ignore[method-assign]

    # B5 の近接行(見えた人): 第 1 期 1-2 の後は描画の本体が ``_nearby_people``(``_nearby_items`` は単一ランキングの
    # 腕だけ)=こちらを包む。距離はいまの座標から計り直す(前の読み直しと同じ)
    orig_near = RD.Renderer._nearby_people

    def near(self: Any, i: int, cell: int, tc: Any) -> Any:
        people = orig_near(self, i, cell, tc)
        st["b5_calls"] += 1
        st["b5_items_hist"][len(people)] += 1
        if people:
            ids = np.asarray([int(sp.id) for sp in people], dtype=np.int64)
            d = pair_dist(self.agents.xy, np.full(ids.size, int(i)), ids)
            st["b5_dist"].update(dist_hist(d))
            st["b5_acq"] += int(sum(bool(sp.acquainted) for sp in people))
            st["b5_items"] += int(ids.size)
            st["b5_gt_radius"] += int((d > 10.3).sum())
        return people

    RD.Renderer._nearby_people = near  # type: ignore[method-assign]

    orig_obs = NM.GroupNormMeter.observe_tick

    def obs(self: Any, tick: int) -> None:
        orig_obs(self, tick)
        r = self.agents.registry
        xy = np.asarray(r.xy, dtype=np.float64)
        cell = np.asarray(r.cell, dtype=np.int64)
        band = np.asarray(r.band, dtype=np.int64)
        awake = np.asarray(r.activity) != int(Activity.SLEEPING)
        ids = np.flatnonzero(cell >= 0)
        A, B, skipped = pairs_within(xy, ids)
        st["pair_ticks"] += 1
        if skipped:
            st["pairs_skipped"] += 1
        else:
            sc = cell[A] == cell[B]
            st["pairs_2m_total"] += int(A.size)
            st["pairs_2m_zero"] += int((pair_dist(xy, A, B) < 1e-6).sum())
            st["pairs_2m_diff_cell"] += int((~sc).sum())
            st["pairs_2m_diff_cell_awake"] += int((~sc & awake[A] & awake[B]).sum())
            st["pairs_2m_diff_band"] += int((band[A] != band[B]).sum())
            st["pairs_2m_diff_cell_max_tick"] = max(st["pairs_2m_diff_cell_max_tick"], int((~sc).sum()))
        # B5 の単位(在席中の POI の区画・その店のセルの中の体だけ=親の判断 10-14 の 2)の在室人数
        raw = np.asarray(r.poi_ref, dtype=np.int64)[ids]
        raw = raw[raw >= 0]
        if raw.size:
            st["occ_max_raw"] = max(st["occ_max_raw"], int(np.unique(raw, return_counts=True)[1].max()))
        unit = unit_of(r, ids)
        st["occ_out_of_cell"] += int(raw.size - int((unit >= 0).sum()))
        st["occ_seated"] += int(raw.size)
        unit = unit[unit >= 0]
        if unit.size:
            u, c = np.unique(unit, return_counts=True)
            for lo, hi in OCC_BINS:  # 逐次: 箱の数ぶん(8)
                st["occ_hist"][occ_label(lo, hi)] += int(((c >= lo) & (c <= hi)).sum())
            k = int(np.argmax(c))
            if int(c[k]) > st["occ_max"]:
                st["occ_max"], st["occ_max_poi"], st["occ_max_tick"] = int(c[k]), int(u[k]), int(tick)
            st["occ_units_max"] = max(st["occ_units_max"], int(u.size))
            top = np.argsort(-c)[:5]
            for kk in top.tolist():  # 逐次: 上位 5 つ
                p = int(u[kk])
                st["occ_poi_max"][p] = max(st["occ_poi_max"].get(p, 0), int(c[kk]))
        # 同じ座標(node)に重なった体の数の最大(参考=ハブの大きさ)
        if ids.size:
            _v, cnt = np.unique(xy[ids], axis=0, return_counts=True)
            m = int(cnt.max())
            if m > st["same_xy_max"]:
                st["same_xy_max"], st["same_xy_max_tick"] = m, int(tick)

    NM.GroupNormMeter.observe_tick = obs  # type: ignore[method-assign]

    kw = {"vocab_version": "v3", "memory": "on", "geometry": args.geometry, **POLICY_KW[args.policy],
          **ARM_KW[args.arm]}
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, ticks=args.ticks, **kw)
    wall = time.perf_counter() - t0
    m = res.run_manifest_fields()
    cc = dict(res.conversation_counters)
    rel = m.get("relations", {}) or {}
    counts = rel.get("counts", {}) if isinstance(rel, dict) else {}
    gn = m.get("group_norms", {}) or {}
    cod = np.asarray(st["open_dist"], dtype=np.float64)
    b5n = sum(st["b5_items_hist"].values())
    top_units = sorted(st["occ_poi_max"].items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    box = box_holder.get("box")
    unit_info = []
    if box is not None:
        w = box.soa.world
        cap = np.asarray(w.pois.capacity)
        pcell = np.asarray(w.pois.cell)
        eat = getattr(w, "eatery_mask", None)
        for p, mx in top_units:
            unit_info.append({"poi": int(p), "max_in_room": int(mx), "capacity": int(cap[p]), "cell": int(pcell[p]),
                              "eatery": (bool(np.asarray(eat)[p]) if eat is not None else None)})
    out = {
        "policy": args.policy, "arm": args.arm, "geometry": args.geometry, "mode": args.mode, "d": D,
        "args": kw, "final_hash": res.final_hash, "final16": res.final_hash[:16], "llm_calls": int(res.llm_calls),
        "wall_seconds_nondeterministic": round(wall, 2),
        "calls_by_condition": m.get("calls_by_condition", {}),
        "sessions_opened": cc.get("sessions_opened"),
        "relations_counts": {k: v for k, v in counts.items()
                             if k.startswith(("acq_", "invite_", "copresent", "events"))},
        "relations_origins": rel.get("origins") if isinstance(rel, dict) else None,
        "proximity_manifest": m.get("proximity"),
        "conversation_open": {
            "pairs": st["open_n"], "same_cell": st["open_same_cell"], "reach_under_distance_d": st["open_reach_d"],
            "reach_by_unit_only": st["open_by_unit"], "over_d_and_not_same_unit": st["open_over_d_not_unit"],
            "distance": {**hist_share(dist_hist(cod)), "quantiles": quant(cod)},
            "by_pair_class": dict(st["open_class"]), "lost_under_distance_by_pair_class": dict(st["open_lost_class"]),
            "by_categories": dict(st["open_cats"]), "lost_under_distance_by_categories": dict(st["open_lost_cats"]),
            "joins": st["join_n"], "joins_not_reachable": st["join_bad"]},
        "chance": {"rows_origin_chance": st["chance_rows"], "partner_distance": hist_share(st["chance_dist"])},
        "acquaintance_appear_distance": {**hist_share(st["acq_dist"]), "quantiles": quant(st["acq_dist_list"])},
        "copresent": {"active_slot_ticks": st["co_active_slot_ticks"],
                      "active_distance": hist_share(st["co_active_dist"]),
                      "events_written": counts.get("copresent_events")},
        "b5_near": {"renders": st["b5_calls"],
                    "items_per_render_mean": round(sum(k * v for k, v in st["b5_items_hist"].items()) / max(1, b5n), 4),
                    "items_per_render_hist": {str(k): v for k, v in sorted(st["b5_items_hist"].items())},
                    "distance": hist_share(st["b5_dist"]), "items": st["b5_items"],
                    "acquainted_items": st["b5_acq"], "items_beyond_10_3m": st["b5_gt_radius"]},
        "pairs_2m": {"ticks": st["pair_ticks"], "ticks_skipped": st["pairs_skipped"], "total": st["pairs_2m_total"],
                     "zero_distance": st["pairs_2m_zero"], "diff_cell": st["pairs_2m_diff_cell"],
                     "diff_cell_per_tick": round(st["pairs_2m_diff_cell"] / max(1, st["pair_ticks"]), 3),
                     "diff_cell_both_awake_per_tick": round(st["pairs_2m_diff_cell_awake"] / max(1, st["pair_ticks"]),
                                                            3),
                     "diff_cell_max_tick": st["pairs_2m_diff_cell_max_tick"],
                     "diff_band": st["pairs_2m_diff_band"]},
        "b5_unit_occupancy": {"unit_ticks_hist": dict(st["occ_hist"]), "max_in_room": st["occ_max"],
                              "max_poi": st["occ_max_poi"], "max_tick": st["occ_max_tick"],
                              "units_occupied_max": st["occ_units_max"], "top_units": unit_info,
                              "max_in_room_raw_poi_ref": st["occ_max_raw"],
                              "seated_agent_ticks": st["occ_seated"],
                              "seated_out_of_store_cell_agent_ticks": st["occ_out_of_cell"]},
        "same_xy_max": {"agents_at_one_point_max": st["same_xy_max"], "tick": st["same_xy_max_tick"]},
        "group_norms": {"instant_grouped_share": (gn.get("instant_group_walk") or {}).get("grouped_share"),
                        "cowalk_share": (gn.get("cowalk") or {}).get("cowalk_share_of_moving_minutes"),
                        "cowalk_episodes_5min": (gn.get("cowalk") or {}).get("episodes_5min")},
    }
    print(json.dumps(out, ensure_ascii=False, default=str))
    return 0


def cmd_runs(args: argparse.Namespace) -> int:
    modes = [m for m in args.modes.split(",") if m]
    combos = [(p, a, g, mo) for mo in modes for p in ("mock", "classical") for a in ("off", "rel_on", "rel_copresent")
              for g in args.geometries.split(",")]
    if args.only:
        want = set(args.only.split(","))
        combos = [c for c in combos if ":".join(c) in want]
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("SHIBUYA_PROXIMITY", None)
    env.pop("SHIBUYA_PROXIMITY_D", None)
    if args.src:
        env["PYTHONPATH"] = str(Path(args.src).resolve())

    def one(c: tuple[str, str, str, str]) -> dict[str, Any]:
        p, a, g, mo = c
        cmd = [sys.executable, str(Path(__file__)), "one", "--policy", p, "--arm", a, "--geometry", g, "--mode", mo,
               "--d", str(args.d), "--world", args.world, "--agents", str(args.agents), "--seed", str(args.seed)]
        got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if got.returncode != 0:
            return {"policy": p, "arm": a, "geometry": g, "mode": mo, "error": got.stderr[-3000:]}
        row = json.loads(got.stdout.strip().splitlines()[-1])
        print(f"{args.label} {mo}/{p}/{a}/{g}: final {row['final16']} calls {row['llm_calls']:,} "
              f"sessions {row['sessions_opened']} wall {row['wall_seconds_nondeterministic']}s", flush=True)
        return row

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        rows = list(ex.map(one, combos))
    doc = {"schema": "shibuya.bench/prox22/runs/1", "label": args.label, "src": "写し" if args.src else "作業木",
           "base": {"agents": args.agents, "seed": args.seed, "sample": "stratified (rel8b_measure.stratified_sample)",
                    "vocab": "v3", "memory": "on", "hunger": "energy (cli default)", "l4": "unlimited (cli default)",
                    "d": args.d},
           "rows": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ 表(§1-2 の量)
#: 比べない葉(壁時計と腕の manifest の節=HEAD に無い)。
_SKIP = ("wall_seconds_nondeterministic", "proximity_manifest")


def _get(r: dict, path: str) -> Any:
    x: Any = r
    for k in path.split("."):
        x = (x or {}).get(k) if isinstance(x, dict) else None
    return x


TABLE = {
    "conv_open_share_gt_2m": ("conversation_open.distance.share_gt_2m", None),
    "conv_open_share_gt_10m": ("conversation_open.distance.share_gt_10m", None),
    "conv_open_max_m": ("conversation_open.distance.quantiles.max", None),
    "conv_open_pairs": ("conversation_open.pairs", None),
    "pairs_2m_diff_cell_per_tick": ("pairs_2m.diff_cell_per_tick", None),
    "chance_near_first_rows": ("relations_counts.invite_pick:near_first", "rel_on"),
    "chance_partner_share_0m": ("chance.partner_distance.share_0m", "rel_on"),
    "acq_wake_calls": ("calls_by_condition.ACQUAINTANCE", "rel_on"),
    "acq_appear_distance_p50": ("acquaintance_appear_distance.quantiles.p50", "rel_on"),
    "sessions_off": ("sessions_opened", "off"),
    "sessions_rel_on": ("sessions_opened", "rel_on"),
    "copresent_events_written": ("copresent.events_written", "rel_copresent"),
    "copresent_active_share_0m": ("copresent.active_distance.share_0m", "rel_copresent"),
    "instant_group_walk_share": ("group_norms.instant_grouped_share", "off"),
    "cowalk_5min_share": ("group_norms.cowalk_share", "off"),
    "b5_items_per_render(rel_on)": ("b5_near.items_per_render_mean", "rel_on"),
    "b5_share_le_2m(rel_on)": ("b5_near.distance.share_le_2m", "rel_on"),
    "b5_share_gt_10m(rel_on)": ("b5_near.distance.share_gt_10m", "rel_on"),
    "b5_acquainted_items(rel_on)": ("b5_near.acquainted_items", "rel_on"),
    "b5_unit_max_in_room": ("b5_unit_occupancy.max_in_room", None),
    "b5_unit_max_in_room_raw": ("b5_unit_occupancy.max_in_room_raw_poi_ref", None),
    "b5_seated_out_of_store_cell": ("b5_unit_occupancy.seated_out_of_store_cell_agent_ticks", None),
    "same_xy_max": ("same_xy_max.agents_at_one_point_max", None),
    "conv_lost_under_distance": ("conversation_open.lost_under_distance_by_pair_class", None),
}


def _strip(r: dict) -> dict:
    return {k: v for k, v in r.items() if k not in _SKIP}


def cmd_table(args: argparse.Namespace) -> int:
    docs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in args.runs]
    rows: dict[tuple, dict] = {}
    for d in docs:
        for r in d["rows"]:
            if "error" in r:
                continue
            rows[(d["label"], r["mode"], r["policy"], r["arm"], r["geometry"])] = r
    # 検算: cell の腕は HEAD と作業木で同じ計器の値(壁時計と腕の節を除く全部)
    check = {}
    for (lab, mo, p, a, g), r in rows.items():
        if lab == "head":
            w = rows.get(("wt", "cell", p, a, g))
            check[f"{p}/{a}/{g}"] = None if w is None else (_strip(r) == _strip(w))
    out: dict[str, Any] = {}
    for (lab, mo, p, a, g), r in rows.items():
        if lab == "head":
            continue
        out.setdefault(f"{mo}/{g}", {}).setdefault(p, {})[a] = r
    table: dict[str, Any] = {}
    for key, by_pol in out.items():
        for p, by_arm in by_pol.items():
            t: dict[str, Any] = {}
            for name, (path, arm_pref) in TABLE.items():
                arms = [arm_pref] if arm_pref else list(by_arm)
                t[name] = {a: _get(by_arm[a], path) for a in arms if a in by_arm}
            if "off" in by_arm and "rel_on" in by_arm:
                s0, s1 = by_arm["off"]["sessions_opened"], by_arm["rel_on"]["sessions_opened"]
                t["session_increase_rel_on_over_off"] = round(s1 / s0 - 1, 4) if s0 else None
            t["checkpoints"] = {a: {"final16": r["final16"], "llm_calls": r["llm_calls"],
                                    "sessions": r["sessions_opened"]} for a, r in by_arm.items()}
            t["b5_unit_occupancy"] = {a: r["b5_unit_occupancy"] for a, r in by_arm.items()}
            t["conversation_lost_detail"] = {a: {
                "pairs": r["conversation_open"]["pairs"],
                "by_pair_class": r["conversation_open"]["by_pair_class"],
                "lost_under_distance_by_pair_class": r["conversation_open"]["lost_under_distance_by_pair_class"],
                "lost_under_distance_by_categories": r["conversation_open"]["lost_under_distance_by_categories"],
                "over_d_and_not_same_unit": r["conversation_open"]["over_d_and_not_same_unit"],
                "reach_by_unit_only": r["conversation_open"]["reach_by_unit_only"],
                "joins": r["conversation_open"]["joins"], "joins_not_reachable": r["conversation_open"]["joins_not_reachable"],
            } for a, r in by_arm.items()}
            table.setdefault(key, {})[p] = t
    doc = {"schema": "shibuya.bench/prox22/reread_11c/1", "source": [Path(p).name for p in args.runs],
           "check_cell_head_equals_worktree": check,
           "check_all_equal": bool(check) and all(v is True for v in check.values()),
           "tables": table}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"check": check}, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="第 2 期 2-2 段 11c の読み直し")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "one", "runs", "table"):
        sp = sub.add_parser(name)
        if name in ("one", "runs"):
            sp.add_argument("--world", default="data/world/v2")
            sp.add_argument("--agents", type=int, default=5_000)
            sp.add_argument("--seed", type=int, default=1)
            sp.add_argument("--d", type=float, default=2.0)
        if name in ("check", "runs", "table"):
            sp.add_argument("--out", required=True)
        if name == "one":
            sp.add_argument("--policy", choices=tuple(POLICY_KW), required=True)
            sp.add_argument("--arm", choices=tuple(ARM_KW), required=True)
            sp.add_argument("--geometry", choices=("node", "edge"), default="node")
            sp.add_argument("--mode", choices=("cell", "distance"), default="cell")
            sp.add_argument("--ticks", type=int, default=1440)
        if name == "runs":
            sp.add_argument("--label", required=True)
            sp.add_argument("--src", default="")
            sp.add_argument("--modes", default="cell")
            sp.add_argument("--geometries", default="node")
            sp.add_argument("--workers", type=int, default=3)
            sp.add_argument("--only", default="")
        if name == "table":
            sp.add_argument("--runs", nargs="+", required=True)
    args = ap.parse_args(argv)
    return {"check": cmd_check, "one": cmd_one, "runs": cmd_runs, "table": cmd_table}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
