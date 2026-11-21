# -*- coding: utf-8 -*-
"""S46 の計測: 出発点の座標の float32 への丸めで道が変わる件数(返事その 8 §3 の S46・§6-1 の 7・記録 2-60)。

標準のラン(byte-check の構成 ``w6_v3_default``=既定・mock・5,000 体・seed 1・1 日・テープつき)を 1 本回し、関数を包んで
読むだけ(戻り値も状態も変えない)で、実際に問い合わされた道の組(出発点・階・行き先・曲がる重み)と、そのとき出発点に
なった位置の「丸める前の float64 の値」を集める。ランの後に、同じ組を丸めた座標と丸めない座標で道の計算
(``NavPlanner.plan``・控えを通らない)に当て直して比べる。

丸めの場所(src は変えない・場所は ``world/model/space/nav1.py`` と ``engine/resolve.py`` の今の道):

- 位置の欄 ``xy`` と出発点の欄 ``nav_ox``・``nav_oy`` が float32(``agents/state.py`` の宣言)。位置を書く所で丸める:
  ``_nav_step`` の ``r.xy[go] = res["x"].astype(np.float32)``(進んだ位置)・``_nav_positions`` の節の点への置き直しと面への
  寄せ・``_nav_stop`` の面への寄せ。
- ``NavSpace.ensure_routes`` が出発点を ``np.asarray(x, dtype=np.float32)`` で持ち、``NavSpace._shape`` が鍵
  ``np.float32(ox).tobytes()`` と道の計算 ``planner.plan(float(np.float32(ox)), ...)`` の両方に同じ丸めを掛ける。
- 丸めを外す口はコードに無い。ここでは「丸める前の float64」を、位置を書いた関数の直前の値として包んだ関数で控える:
  ``NavSpace.advance`` の戻り値(進んだ位置)/``_nav_positions`` で節の点に置き直された体=``nav1_anchors`` の float64 の点/
  面へ寄せた体=``NavSpace.onto_surface`` の float64 の戻り値(寄せる前の float32 の位置に当て直す)。問い合わせのときに
  ``float32(控えた値) == 渡された位置`` を確かめ、合わなければ節の点(float64)・W1 の節の点(資産が float32=丸めなし)の順に
  照らし、どれでもなければ「分からない」と数えて比べない。

数えるもの: (i) 選ばれた通りの列(``RouteGeom.w1_path``=W1 の節の列)が変わった件数・出発の節が変わった件数・通る接続口の
列が変わった件数/(ii) 線の点の列(``pts``)が 1 バイトでも変わった件数・点の数が変わった件数・始点(出発点そのもの)を除いて
変わった件数・点の最大のずれ(添字どうしで比べたずれと、2 本の折れ線の離れ方=:func:`line_gap`。一直線の上の点が 1 つ
増えたり減ったりすると添字がずれるので、形の違いは折れ線の離れ方で読む)/(iii) 道の長さ(歩く区間)の差の分布
(中央値・最大ほか)。数は重ならない組(丸めない座標の
組)と、問い合わせの延べ回数の両方で出す。あわせて、ランで控えから返った線と、ランの後に控えを通らず計算し直した線が
1 バイト一致するか(実データの規模での控えの有り無しの照合)も数える。

使い方(cwd はリポの根・PYTHONPATH はリポの src・PYTHONHASHSEED=0=byte-check と同じ・SHIBUYA_ の環境変数は置かない):
    python measure_rounding.py --tape <テープの置き場> --out <出力の JSON>
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

#: 位置を最後に書いた所の種類(控えた float64 の出どころ)
K_NONE, K_ADVANCE, K_ANCHOR, K_SURFACE = 0, 1, 2, 3
KIND_NAMES = {K_ADVANCE: "advance", K_ANCHOR: "anchor", K_SURFACE: "onto_surface"}

S: dict = {"space": None, "sh": None, "kind": None, "orig": None, "orig_kind": None, "reg": None, "log": None,
           "cache_max": 0, "queries": [], "src_counts": Counter(), "writes": Counter(), "write_unmatched": 0,
           "pts_examples": [], "same_count_examples": []}


def route_bytes(r):
    if r is None:
        return None
    out = []
    for f in dataclasses.fields(r):
        v = getattr(r, f.name)
        if isinstance(v, np.ndarray):
            out.append((f.name, v.dtype.str, v.shape, v.tobytes()))
        else:
            out.append((f.name, type(v).__name__, repr(v)))
    return tuple(out)


def digest(r) -> str:
    b = route_bytes(r)
    if b is None:
        return "none"
    h = hashlib.sha256()
    for item in b:
        for part in item:
            h.update(part if isinstance(part, bytes) else repr(part).encode("utf-8"))
            h.update(b"|")
    return h.hexdigest()


def _install() -> None:
    from shibuya.engine import resolve as R
    from shibuya.world.model.space import nav1 as NAV

    _init = NAV.NavSpace.__init__

    def init(self, *a, **k):  # noqa: ANN001
        _init(self, *a, **k)
        S["space"] = self
        S["sh"] = np.full((self.n_agents, 2), np.nan)
        S["kind"] = np.zeros(self.n_agents, dtype=np.int8)
        S["orig"] = np.full((self.n_agents, 2), np.nan)
        S["orig_kind"] = np.full(self.n_agents, "", dtype=object)

    NAV.NavSpace.__init__ = init  # type: ignore[method-assign]

    _adv = NAV.NavSpace.advance

    def advance(self, aid, t_in, factor, nav_wait, tick):  # noqa: ANN001
        res = _adv(self, aid, t_in, factor, nav_wait, tick)
        a = np.asarray(aid, dtype=np.int64)
        S["sh"][a, 0] = res["x"]
        S["sh"][a, 1] = res["y"]
        S["kind"][a] = K_ADVANCE
        S["writes"]["advance"] += int(a.size)
        return res

    NAV.NavSpace.advance = advance  # type: ignore[method-assign]

    def after_write(r, nav, before, before_fi, label):  # noqa: ANN001
        moved = np.flatnonzero(np.any(r.xy != before, axis=1))
        if moved.size == 0:
            return
        node = np.asarray(r.node[moved], dtype=np.int64)
        ax, ay, af = nav.anchor_of(node)
        at_anchor = ((node >= 0) & (ax.astype(np.float32) == r.xy[moved, 0]) & (ay.astype(np.float32) == r.xy[moved, 1])
                     & (af == r.nav_fi[moved]))
        m = moved[at_anchor]
        S["sh"][m, 0] = ax[at_anchor]
        S["sh"][m, 1] = ay[at_anchor]
        S["kind"][m] = K_ANCHOR
        S["writes"][f"{label}:anchor"] += int(m.size)
        rest = moved[~at_anchor]
        if rest.size:
            sx, sy = nav.onto_surface(before[rest, 0], before[rest, 1], before_fi[rest])
            ok = (sx.astype(np.float32) == r.xy[rest, 0]) & (sy.astype(np.float32) == r.xy[rest, 1])
            S["sh"][rest[ok], 0] = sx[ok]
            S["sh"][rest[ok], 1] = sy[ok]
            S["kind"][rest[ok]] = K_SURFACE
            S["sh"][rest[~ok]] = np.nan
            S["kind"][rest[~ok]] = K_NONE
            S["writes"][f"{label}:onto_surface"] += int(ok.sum())
            S["write_unmatched"] += int((~ok).sum())

    _pos = R._nav_positions

    def nav_positions(agents, world, nav):  # noqa: ANN001
        r = agents.registry
        before = r.xy.copy()
        before_fi = r.nav_fi.copy()
        _pos(agents, world, nav)
        after_write(r, nav, before, before_fi, "positions")

    R._nav_positions = nav_positions

    _stop = R._nav_stop

    def nav_stop(agents, nav, act):  # noqa: ANN001
        r = agents.registry
        before = r.xy.copy()
        before_fi = r.nav_fi.copy()
        _stop(agents, nav, act)
        after_write(r, nav, before, before_fi, "stop")

    R._nav_stop = nav_stop

    _step = R._nav_step

    def nav_step(agents, world, aid, tgt, tick, out, nav):  # noqa: ANN001
        S["reg"] = agents.registry
        S["node_xy"] = world.assets.node_xy
        return _step(agents, world, aid, tgt, tick, out, nav)

    R._nav_step = nav_step

    _shp = NAV.NavSpace._shape

    def shape(self, ox, oy, ofi, target, turn_w):  # noqa: ANN001
        r = _shp(self, ox, oy, ofi, target, turn_w)
        if S["log"] is not None:
            S["log"].append(r)
        S["cache_max"] = max(S["cache_max"], len(self._shape_cache))
        return r

    NAV.NavSpace._shape = shape  # type: ignore[method-assign]

    _ens = NAV.NavSpace.ensure_routes

    def ensure_routes(self, aid, x, y, fi, target, route_tgt, ox, oy, of_):  # noqa: ANN001
        a_ = np.asarray(aid, dtype=np.int64)
        tgt = np.asarray(target, dtype=np.int64)
        changed = np.asarray(route_tgt, dtype=np.int64) != tgt
        need = changed | ~self.pool.has(a_)
        x32 = np.asarray(x, dtype=np.float32)
        y32 = np.asarray(y, dtype=np.float32)
        S["log"] = []
        res = _ens(self, aid, x, y, fi, target, route_tgt, ox, oy, of_)
        log, S["log"] = S["log"], None
        _ch, nox, noy, nof, _ok = res
        qs = np.flatnonzero(need)
        assert len(log) == qs.size, (len(log), qs.size)
        reg = S["reg"]
        for j, q in enumerate(qs.tolist()):
            a = int(a_[q])
            if changed[q]:
                sh = S["sh"][a]
                kind = ""
                o64 = (np.nan, np.nan)
                if np.isfinite(sh).all() and np.float32(sh[0]) == x32[q] and np.float32(sh[1]) == y32[q]:
                    o64, kind = (float(sh[0]), float(sh[1])), KIND_NAMES[int(S["kind"][a])]
                elif reg is not None and int(reg.node[a]) >= 0:
                    nd = int(reg.node[a])
                    m = self.mesh
                    if (nd < m.anchor_x.size and np.float32(m.anchor_x[nd]) == x32[q]
                            and np.float32(m.anchor_y[nd]) == y32[q]):
                        o64, kind = (float(m.anchor_x[nd]), float(m.anchor_y[nd])), "anchor_at_query"
                    elif (S["node_xy"][nd, 0] == x32[q]) and (S["node_xy"][nd, 1] == y32[q]):
                        o64, kind = (float(x32[q]), float(y32[q])), "node_xy_float32_asset"
                if not kind:
                    kind = "unknown"
                S["orig"][a] = o64
                S["orig_kind"][a] = kind
            else:  # 置き場が空の体(再開の引き直し): 出発点は前に控えた値
                o = S["orig"][a]
                if np.isfinite(o).all() and np.float32(o[0]) == nox[q] and np.float32(o[1]) == noy[q]:
                    o64, kind = (float(o[0]), float(o[1])), "replan:" + str(S["orig_kind"][a])
                else:
                    o64, kind = (np.nan, np.nan), "replan:unknown"
            S["src_counts"][kind] += 1
            S["queries"].append((np.float32(nox[q]).tobytes(), np.float32(noy[q]).tobytes(), int(nof[q]), int(tgt[q]),
                                 float(self.turn_w[a]), o64[0], o64[1], kind, digest(log[j])))
        return res

    NAV.NavSpace.ensure_routes = ensure_routes  # type: ignore[method-assign]


def _pct(v: np.ndarray, qs=(50, 90, 99)) -> dict:
    if v.size == 0:
        return {"n": 0}
    out = {"n": int(v.size), "max": float(v.max())}
    for q in qs:
        out[f"p{q}"] = float(np.percentile(v, q))
    out["median"] = out.pop("p50")
    return out


def _seg_dist(p: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """点の並び p (n, 2) から線分 a-b までの距離。"""
    ab = b - a
    L2 = float(ab @ ab)
    if L2 == 0.0:
        return np.hypot(*(p - a).T)
    t = np.clip(((p - a) @ ab) / L2, 0.0, 1.0)
    q = a + t[:, None] * ab
    return np.hypot(*(p - q).T)


def line_gap(P: np.ndarray, Q: np.ndarray) -> float:
    """2 本の折れ線の離れ方[m]: 各頂点から相手の折れ線までの最短距離の最大(両向き・頂点で測る近似)。"""
    def one(A, B):
        if B.shape[0] == 1:
            return float(np.hypot(*(A - B[0]).T).max())
        d = np.full(A.shape[0], np.inf)
        for k in range(B.shape[0] - 1):
            d = np.minimum(d, _seg_dist(A, B[k], B[k + 1]))
        return float(d.max())
    return max(one(P, Q), one(Q, P))


def analyse() -> dict:
    space = S["space"]
    pl = space.planner
    cw = float(space.climb_w)
    qs = S["queries"]
    # ---- 控えの有り無し(実データの規模): ランで返った線 = 控えを通らず計算し直した線か
    by32: dict[tuple, set] = {}
    for q in qs:
        by32.setdefault(q[:5], set()).add(q[8])
    plan32: dict[tuple, object] = {}
    t0 = time.perf_counter()
    for k in sorted(by32, key=lambda k: (k[3], k[2], k[0], k[1], k[4]), reverse=True):  # ランと違う順で
        x = float(np.frombuffer(k[0], dtype=np.float32)[0])
        y = float(np.frombuffer(k[1], dtype=np.float32)[0])
        plan32[k] = pl.plan(x, y, k[2], k[3], turn_w=k[4], climb_w=cw)
    t32 = time.perf_counter() - t0
    run_vs_fresh = {"keys": len(by32), "keys_with_more_than_one_line_in_run": sum(len(v) > 1 for v in by32.values()),
                    "keys_fresh_ne_run": sum(digest(plan32[k]) not in v or len(v) != 1 for k, v in by32.items()),
                    "recompute_seconds": round(t32, 1)}
    # ---- 丸めない座標(float64)で計算し直す
    by64: dict[tuple, list] = {}
    for q in qs:
        if np.isfinite(q[5]) and np.isfinite(q[6]):
            by64.setdefault((q[5], q[6], q[2], q[3], q[4]), []).append(q[:5])
    rows = []
    t0 = time.perf_counter()
    for k64, k32s in by64.items():
        k32 = k32s[0]
        r32 = plan32[k32]
        r64 = pl.plan(k64[0], k64[1], k64[2], k64[3], turn_w=k64[4], climb_w=cw)
        x32 = float(np.frombuffer(k32[0], dtype=np.float32)[0])
        y32 = float(np.frombuffer(k32[1], dtype=np.float32)[0])
        row = {"n_queries": len(k32s), "dx": abs(k64[0] - x32), "dy": abs(k64[1] - y32),
               "exact": (k64[0] == x32 and k64[1] == y32)}
        row["none_changed"] = (r32 is None) != (r64 is None)
        row["both_none"] = r32 is None and r64 is None
        if r32 is not None and r64 is not None:
            row["bytes_same"] = route_bytes(r32) == route_bytes(r64)
            row["w1_changed"] = not np.array_equal(r32.w1_path, r64.w1_path)
            sn32 = pl.nearest_node(x32, y32, k64[2])
            sn64 = pl.nearest_node(k64[0], k64[1], k64[2])
            row["start_node_changed"] = sn32 != sn64
            row["links_changed"] = not np.array_equal(r32.seg_link[r32.seg_link >= 0], r64.seg_link[r64.seg_link >= 0])
            row["mode_changed"] = r32.mode != r64.mode
            row["pts_bytes_changed"] = r32.pts.tobytes() != r64.pts.tobytes()
            row["n_pts_changed"] = r32.pts.shape != r64.pts.shape
            if r32.pts.shape == r64.pts.shape:
                d = np.abs(r32.pts - r64.pts)
                row["pts_max_shift"] = float(d.max())
                row["pts_after_first_changed"] = r32.pts[1:].tobytes() != r64.pts[1:].tobytes()
                row["pts_after_first_max_shift"] = float(d[1:].max()) if d.shape[0] > 1 else 0.0
            else:
                row["pts_after_first_changed"] = True
            if row["pts_bytes_changed"]:
                row["line_gap"] = line_gap(r32.pts, r64.pts)
                if (not row["n_pts_changed"] and row["pts_after_first_changed"]
                        and len(S["same_count_examples"]) < 10):
                    d_idx = np.hypot(*(r32.pts - r64.pts).T)
                    big = np.flatnonzero(d_idx > 1e-3)
                    S["same_count_examples"].append({
                        "n_pts": int(r32.pts.shape[0]), "index_shift_max_m": float(d_idx.max()),
                        "indices_shifted_gt_1mm": big.tolist()[:10], "line_gap_m": row["line_gap"],
                        "len_diff_m": float(r64.length_m - r32.length_m),
                        "pts32_near": np.round(r32.pts[max(0, (big[0] if big.size else 0) - 1):
                                                       (big[-1] if big.size else 0) + 2] - r32.pts[0], 6).tolist(),
                        "pts64_near": np.round(r64.pts[max(0, (big[0] if big.size else 0) - 1):
                                                       (big[-1] if big.size else 0) + 2] - r32.pts[0], 6).tolist()})
                if row["n_pts_changed"] and len(S["pts_examples"]) < 3:
                    o = r32.pts[0]
                    S["pts_examples"].append({
                        "note": "点の座標は 32 側の始点からの差[m]・小数 6 桁",
                        "pts32": np.round(r32.pts - o, 6).tolist(), "pts64": np.round(r64.pts - o, 6).tolist()})
            row["len_diff"] = r64.length_m - r32.length_m
            row["len32"] = r32.length_m
            row["k"] = (round(x32, 4), round(y32, 4), k64[2], k64[3], k64[4], len(r32.w1_path), len(r64.w1_path))
        rows.append(row)
    t64 = time.perf_counter() - t0
    both = [r for r in rows if "bytes_same" in r]

    def cnt(key, weight=False):
        return int(sum((r["n_queries"] if weight else 1) for r in both if r.get(key)))

    ld = np.array([abs(r["len_diff"]) for r in both])
    ld_ne = ld[ld > 0]
    sh = np.array([max(r["dx"], r["dy"]) for r in rows])
    changed_examples = sorted((r for r in both if r["w1_changed"] or r["n_pts_changed"] or r.get("pts_after_first_changed")),
                              key=lambda r: -abs(r["len_diff"]))[:20]
    return {
        "run_vs_fresh_recompute": run_vs_fresh,
        "float64_recompute": {
            "distinct_float64_keys": len(rows),
            "distinct_float32_keys_among_them": len({tuple(v[0]) for v in by64.values()}),
            "queries_with_known_float64_origin": int(sum(r["n_queries"] for r in rows)),
            "origin_exactly_float32": int(sum(r["exact"] for r in rows)),
            "origin_rounding_shift_m": _pct(sh),
            "both_none": int(sum(r["both_none"] for r in rows)),
            "none_changed": int(sum(r["none_changed"] for r in rows)),
            "both_routes": len(both),
            "recompute_seconds": round(t64, 1),
            "i_w1_path_changed": {"keys": cnt("w1_changed"), "queries": cnt("w1_changed", True)},
            "i_start_node_changed": {"keys": cnt("start_node_changed"), "queries": cnt("start_node_changed", True)},
            "i_links_changed": {"keys": cnt("links_changed"), "queries": cnt("links_changed", True)},
            "mode_changed": {"keys": cnt("mode_changed"), "queries": cnt("mode_changed", True)},
            "ii_route_bytes_changed": {"keys": len(both) - cnt("bytes_same"),
                                       "queries": int(sum(r["n_queries"] for r in both if not r["bytes_same"]))},
            "ii_pts_bytes_changed": {"keys": cnt("pts_bytes_changed"), "queries": cnt("pts_bytes_changed", True)},
            "ii_n_pts_changed": {"keys": cnt("n_pts_changed"), "queries": cnt("n_pts_changed", True)},
            "ii_pts_after_first_changed": {"keys": cnt("pts_after_first_changed"),
                                           "queries": cnt("pts_after_first_changed", True)},
            "ii_pts_max_shift_m_same_count": _pct(np.array([r["pts_max_shift"] for r in both if "pts_max_shift" in r])),
            "ii_pts_after_first_max_shift_m_same_count": _pct(np.array(
                [r["pts_after_first_max_shift"] for r in both if "pts_after_first_max_shift" in r])),
            "ii_line_gap_m_where_pts_changed": _pct(np.array([r["line_gap"] for r in both if "line_gap" in r])),
            "ii_line_gap_m_where_n_pts_changed": _pct(np.array(
                [r["line_gap"] for r in both if "line_gap" in r and r["n_pts_changed"]])),
            "ii_line_gap_counts": {"gt_1mm": int(sum(r.get("line_gap", 0.0) > 1e-3 for r in both)),
                                   "gt_1cm": int(sum(r.get("line_gap", 0.0) > 1e-2 for r in both)),
                                   "gt_1m": int(sum(r.get("line_gap", 0.0) > 1.0 for r in both))},
            "ii_n_pts_changed_examples": S["pts_examples"],
            "ii_same_count_but_shifted_examples": S["same_count_examples"],
            "iii_abs_length_diff_m_all": _pct(ld),
            "iii_abs_length_diff_m_nonzero": _pct(ld_ne),
            "iii_length_diff_counts": {"gt_0": int((ld > 0).sum()), "gt_1mm": int((ld > 1e-3).sum()),
                                       "gt_1cm": int((ld > 1e-2).sum()), "gt_1m": int((ld > 1.0).sum()),
                                       "gt_10m": int((ld > 10.0).sum())},
            "iii_signed_length_diff_m_sum": float(sum(r["len_diff"] for r in both)),
            "iii_relative_abs_length_diff_max": float(max((abs(r["len_diff"]) / max(r["len32"], 1e-9) for r in both),
                                                          default=0.0)),
            "iii_relative_abs_length_diff_max_len_ge_1m": float(max(
                (abs(r["len_diff"]) / r["len32"] for r in both if r["len32"] >= 1.0), default=0.0)),
            "iii_routes_shorter_than_1m": int(sum(r["len32"] < 1.0 for r in both)),
            "examples_largest_changes": [
                {"origin32": list(r["k"][:2]), "floor": r["k"][2], "target": r["k"][3], "turn_w": r["k"][4],
                 "w1_len_32": r["k"][5], "w1_len_64": r["k"][6], "w1_changed": r["w1_changed"],
                 "n_pts_changed": r["n_pts_changed"], "len32_m": round(r["len32"], 3),
                 "len_diff_m": round(r["len_diff"], 6), "n_queries": r["n_queries"]} for r in changed_examples],
        },
    }


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip()
    except Exception as e:  # pragma: no cover
        return f"(git error {type(e).__name__})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="w6_v3_default")
    ap.add_argument("--tape", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--ticks", type=int, default=None, help="試走だけ(省略=1 日=標準のラン)")
    args = ap.parse_args()

    sys.path.insert(0, os.getcwd())
    from tools.bytecheck import configs as BC

    _install()
    from shibuya import cli

    kwd = dict(BC.configs()[args.config])
    extra = {} if args.ticks is None else {"ticks": int(args.ticks)}
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape, **kwd, **extra)
    wall = time.perf_counter() - t0
    man = res.run_manifest_fields()
    sp = S["space"]
    payload = {
        "what": "S46 道の線の控えと座標の丸め(float32)の計測",
        "config": args.config, "kw": kwd, "agents": args.agents, "seed": args.seed, "ticks": args.ticks,
        "world": str(args.world).replace("\\", "/"),
        "git_head": _git("rev-parse", "HEAD"),
        "git_src_dirty": _git("status", "--porcelain", "--", "src").splitlines(),
        "pythonhashseed": os.environ.get("PYTHONHASHSEED"),
        "shibuya_env": sorted(k for k in os.environ if k.startswith("SHIBUYA_")),
        "final16": res.final_hash[:16], "llm_calls": int(res.llm_calls), "wall_s": round(wall, 1),
        "space_effective": man["space"]["effective"],
        "meter": {k: v for k, v in sp.nav_meter.as_dict().items() if k.startswith("routes") or k == "replans_on_resume"},
        "cache_cap": int(sp._shape_cache_cap), "cache_max_size": int(S["cache_max"]),
        "cache_size_at_end": len(sp._shape_cache),
        "queries_total": len(S["queries"]),
        "origin_source_counts": dict(sorted(S["src_counts"].items())),
        "position_writes_seen": dict(sorted(S["writes"].items())),
        "position_writes_unmatched": int(S["write_unmatched"]),
    }
    payload.update(analyse())
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    f64 = payload["float64_recompute"]
    print(json.dumps({"final16": payload["final16"], "calls": payload["llm_calls"], "queries": payload["queries_total"],
                      "run_vs_fresh": payload["run_vs_fresh_recompute"],
                      "w1_changed": f64["i_w1_path_changed"], "pts_after_first_changed": f64["ii_pts_after_first_changed"],
                      "len_diff": f64["iii_abs_length_diff_m_all"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
