"""R-82 追加: PLATEAU 道路 LOD1(区の全域・tran:Road の lod1MultiSurface)が「面の無い道」をどこまで覆うかと、その面の幅。

R-58 と r82_surface_gap.py は TrafficArea(LOD2/LOD3 の歩道部・車道部)だけを塗った。区の README は道路 LOD1 を
「15.11km2(区内全域)」としているので、Road 自体の LOD1 の面(歩道と車道の区別なし)を別に塗って数える。
出力: r82_lod1_road.json(集計値のみ)。使い方: python r82_lod1_road.py
"""
from __future__ import annotations

import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO / "docs" / "research" / "r58"))
sys.path.insert(0, str(HERE))
import r58_plateau_inventory as R  # noqa: E402
from r82_surface_gap import dilate, down, sample_points, tran_masks  # noqa: E402

OUT = HERE / "r82_lod1_road.json"
RES = 0.25


def lod1_mask():
    files = [R.UDX / "tran" / f"{m}_tran_6697_op.gml" for m in R.W1_MESH]
    nx = int(math.ceil((R.X_MAX - R.X_MIN) / RES))
    ny = int(math.ceil((R.Y_MAX - R.Y_MIN) / RES))
    m = np.zeros((ny, nx), dtype=bool)
    seen = set()
    n_road, n_with = 0, 0
    for f in files:
        for el in R.members(f):
            if el.tag != R.T("tran:Road"):
                continue
            ms = el.find(R.T("tran:lod1MultiSurface"))
            n_road += 1
            if ms is None:
                continue
            n_with += 1
            for poly in ms.iter(R.T("gml:Polygon")):
                ext = poly.find(R.T("gml:exterior"))
                if ext is None:
                    continue
                pl = next(ext.iter(R.T("gml:posList")), None)
                if pl is None:
                    continue
                a = R.poslist(pl)
                k = R.ring_key(a[:, :2])
                if k in seen:
                    continue
                seen.add(k)
                x, y = R.local(a[:, 0], a[:, 1])
                if x.max() < R.X_MIN or x.min() > R.X_MAX or y.max() < R.Y_MIN or y.min() > R.Y_MAX:
                    continue
                R.fill_ring(m, (x - R.X_MIN) / RES, (y - R.Y_MIN) / RES)
                # 穴(interior)は道路の中の島などなので抜く
                for itr in poly.findall(R.T("gml:interior")):
                    pli = next(itr.iter(R.T("gml:posList")), None)
                    if pli is None:
                        continue
                    b = R.poslist(pli)
                    xi, yi = R.local(b[:, 0], b[:, 1])
                    hole = np.zeros_like(m)
                    R.fill_ring(hole, (xi - R.X_MIN) / RES, (yi - R.Y_MIN) / RES)
                    m &= ~hole
        print("lod1", f.name, flush=True)
    return m, n_road, n_with


def main() -> None:
    t0 = time.time()
    out: dict = {"script": "r82_lod1_road.py"}
    L1, n_road, n_with = lod1_mask()
    out["roads_in_6_files"] = n_road
    out["roads_with_lod1MultiSurface"] = n_with
    out["lod1_union_m2_in_w1"] = round(float(L1.sum()) * RES * RES)
    out["w1_area_m2"] = round((R.X_MAX - R.X_MIN) * (R.Y_MAX - R.Y_MIN))
    masks, ny, nx = tran_masks()
    z = np.zeros((ny, nx), dtype=bool)
    lod23 = z.copy()
    for v in masks.values():
        lod23 |= v
    del masks
    out["lod2or3_trafficarea_union_m2"] = round(float(lod23.sum()) * RES * RES)
    out["lod1_and_lod23_overlap_m2"] = round(float((L1 & lod23).sum()) * RES * RES)
    out["lod23_outside_lod1_m2"] = round(float((lod23 & ~L1).sum()) * RES * RES)

    # LOD1 の面の幅(距離の段数)を 0.25 m のまま
    d = R.distance_steps(L1, 160)
    k = int(round(1.0 / RES))
    ny1, nx1 = ny // k, nx // k
    A23 = dilate(down(lod23, k, ny1, nx1), 3)
    A1 = dilate(down(L1, k, ny1, nx1), 3)
    # 1 m のセルの中の d の最大(=その点での面の半幅の段数の目安)
    dmax = d[: ny1 * k, : nx1 * k].reshape(ny1, k, nx1, k).max(axis=(1, 3))
    # 3 m 窓の最大
    from numpy.lib.stride_tricks import sliding_window_view as swv
    dpad = np.pad(dmax, 3)
    dwin = swv(dpad, (7, 7)).max(axis=(2, 3))
    # 照合用: LOD2/3 の面(歩道部+車道部+交差部+その他の和集合)の幅も同じ方法で
    d23 = R.distance_steps(lod23, 160)
    d23max = d23[: ny1 * k, : nx1 * k].reshape(ny1, k, nx1, k).max(axis=(1, 3))
    d23win = swv(np.pad(d23max, 3), (7, 7)).max(axis=(2, 3))
    pair = defaultdict(list)
    osm = R.load_osm()
    gl = [(e["klass"], e["geometry"]) for e in osm["edges"] if not e.get("layer")]
    tot, no23, no23_on1 = Counter(), Counter(), Counter()
    wid = defaultdict(list)
    for c, px, py, ii, jj, w, ux, uy in sample_points(gl, ny1, nx1):
        tot[c] += w
        if A23[jj, ii] and dwin[jj, ii] > 0 and d23win[jj, ii] > 0:
            pair[c].append(((2.0 * float(dwin[jj, ii]) - 1.0) * RES, (2.0 * float(d23win[jj, ii]) - 1.0) * RES))
        if not A23[jj, ii]:
            no23[c] += w
            if A1[jj, ii]:
                no23_on1[c] += w
                if dwin[jj, ii] > 0:
                    wid[c].append((2.0 * float(dwin[jj, ii]) - 1.0) * RES)
    T = sum(tot.values())
    out["osm_GL_len_m_total"] = round(T)
    out["no_lod23_surface_m"] = round(sum(no23.values()))
    out["no_lod23_but_on_lod1_m"] = round(sum(no23_on1.values()))
    out["share_of_no_lod23_covered_by_lod1"] = round(sum(no23_on1.values()) / max(1, sum(no23.values())), 4)
    out["by_klass"] = {c: {"len_m": round(v), "no_lod23_m": round(no23[c]), "no_lod23_on_lod1_m": round(no23_on1[c]),
                           "lod1_width_m_on_no_lod23": ({"n": len(wid[c]), "p10": round(float(np.quantile(wid[c], .1)), 2),
                                                          "p50": round(float(np.median(wid[c])), 2), "p90": round(float(np.quantile(wid[c], .9)), 2)}
                                                         if len(wid[c]) >= 10 else {"n": len(wid[c])})}
                       for c, v in tot.most_common()}
    out["known_answer_lod1_vs_lod23_width_on_covered"] = {
        c: {"n": len(v), "lod1_p50": round(float(np.median([a for a, b in v])), 2), "lod23_p50": round(float(np.median([b for a, b in v])), 2),
            "ratio_p10_p50_p90": [round(float(np.quantile([a / b for a, b in v], q)), 2) for q in (0.1, 0.5, 0.9)],
            "abs_diff_le_1m_share": round(sum(1 for a, b in v if abs(a - b) <= 1.0) / len(v), 3)}
        for c, v in pair.items() if len(v) >= 30}
    out["width_note"] = ("幅=辺の点から 3 m 窓の中の LOD1 の面の距離段数の最大から (2d-1)x0.25 m。八角形距離の近似で R-58 の自己検定は -0.25 m の系統誤差(本表は未補正)。"
                         "交差点や面の合流で広めに出る")
    out["elapsed_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("done", out["elapsed_s"])


if __name__ == "__main__":
    main()
