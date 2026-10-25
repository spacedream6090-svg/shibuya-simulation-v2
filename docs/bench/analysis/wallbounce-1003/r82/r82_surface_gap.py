"""R-82: 面の無い道の実態を手元のデータで数える(読むだけ)。

入力(gitignore 下・書き換えない):
  data/realworld/plateau_2025/13113_shibuya-ku_pref_2025_citygml_1_op/udx/{tran,frn}
  data/realworld/osm/shibuya_osm_wide_v8.json・road_names_overpass_20260928.json・street_features_overpass_20260907.json
  data/research_cache/r58/shibuyananbu_link_2020.geojson
出力: 同じフォルダの r82_surface_gap.json(集計値のみ・OSM の生の値は載せない)

方法は R-58(docs/research/r58/r58_plateau_inventory.py の run_tran)と同じ:
PLATEAU tran の面を 0.25 m で塗り、1 m に落として 3 m 膨らませ、OSM v8 の地上の辺(layer 無し)を 2 m 刻みの点で調べる。
加えて LOD3 だけの面・歩行空間 2020 のリンク(5 m 膨張)・OSM 建物の足跡のあいだの幅(道の横断方向に建物まで)を数える。
使い方: python r82_surface_gap.py
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
import r58_plateau_inventory as R  # noqa: E402

OUT = HERE / "r82_surface_gap.json"
RES = 0.25


def tran_masks():
    """(cls, lod) ごとの面を 0.25 m で塗る。cls は side(歩道部)/road(車道部+交差部)/other。"""
    files = [R.UDX / "tran" / f"{m}_tran_6697_op.gml" for m in R.W1_MESH]
    rings = defaultdict(list)
    seen = set()
    for f in files:
        for el in R.members(f):
            if el.tag != R.T("tran:Road"):
                continue
            for ta in list(el.iter(R.T("tran:TrafficArea"))) + list(el.iter(R.T("tran:AuxiliaryTrafficArea"))):
                aux = ta.tag == R.T("tran:AuxiliaryTrafficArea")
                code = R.txt(ta, "tran:function")
                ms, lod = None, None
                for L in (3, 2, 1):
                    ms = ta.find(R.T(f"tran:lod{L}MultiSurface"))
                    if ms is not None:
                        lod = L
                        break
                if ms is None:
                    continue
                cls = "side" if (not aux and str(code) in ("2000", "2010", "2020")) else "road" if (not aux and str(code) in ("1000", "1020")) else "other"
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
                    if not R.in_w1_xy(float(x.mean()), float(y.mean())):
                        continue
                    rings[(cls, lod)].append((x, y))
        print("tran", f.name, flush=True)
    nx = int(math.ceil((R.X_MAX - R.X_MIN) / RES))
    ny = int(math.ceil((R.Y_MAX - R.Y_MIN) / RES))
    masks = {}
    for key, rs in rings.items():
        m = np.zeros((ny, nx), dtype=bool)
        for x, y in rs:
            R.fill_ring(m, (x - R.X_MIN) / RES, (y - R.Y_MIN) / RES)
        masks[key] = m
    return masks, ny, nx


def down(m, k, ny1, nx1):
    return m[: ny1 * k, : nx1 * k].reshape(ny1, k, nx1, k).any(axis=(1, 3))


def dilate(m, r):
    c = np.pad(m.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    J, I = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    j0, j1 = np.clip(J - r, 0, m.shape[0]), np.clip(J + r + 1, 0, m.shape[0])
    i0, i1 = np.clip(I - r, 0, m.shape[1]), np.clip(I + r + 1, 0, m.shape[1])
    return (c[j1, i1] - c[j0, i1] - c[j1, i0] + c[j0, i0]) > 0


def raster_lines(lines, ny1, nx1):
    m = np.zeros((ny1, nx1), dtype=bool)
    for g in lines:
        for (x0, y0), (x1, y1) in zip(g, g[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            n = max(1, int(L / 0.5))
            for i in range(n + 1):
                t = i / n
                ii, jj = int(x0 + t * (x1 - x0) - R.X_MIN), int(y0 + t * (y1 - y0) - R.Y_MIN)
                if 0 <= jj < ny1 and 0 <= ii < nx1:
                    m[jj, ii] = True
    return m


def sample_points(lines_with_tag, ny1, nx1):
    """2 m 刻みの点(重み=長さ)を返す。"""
    for tag, g in lines_with_tag:
        for (x0, y0), (x1, y1) in zip(g, g[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            if L <= 0:
                continue
            n = max(1, int(L // 2))
            ux, uy = (x1 - x0) / L, (y1 - y0) / L
            for i in range(n):
                t = (i + 0.5) / n
                px, py = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
                if not R.in_w1_xy(px, py):
                    continue
                ii, jj = int(px - R.X_MIN), int(py - R.Y_MIN)
                if not (0 <= jj < ny1 and 0 <= ii < nx1):
                    continue
                yield tag, px, py, ii, jj, L / n, ux, uy


def main() -> None:
    t0 = time.time()
    out: dict = {"script": "r82_surface_gap.py"}
    masks, ny, nx = tran_masks()
    print("masks", round(time.time() - t0, 1), flush=True)
    k = int(round(1.0 / RES))
    ny1, nx1 = ny // k, nx // k
    z = np.zeros((ny, nx), dtype=bool)

    def get(cls, lod):
        return masks.get((cls, lod), z)

    all_any = get("side", 3) | get("road", 3) | get("other", 3) | get("side", 2) | get("road", 2) | get("other", 2)
    all_l3 = get("side", 3) | get("road", 3) | get("other", 3)
    side_any = get("side", 3) | get("side", 2)
    out["raster_union_m2"] = {
        "all_lod2or3": round(float(all_any.sum()) * RES * RES),
        "lod3_layer_only": round(float(all_l3.sum()) * RES * RES),
        "sidewalk_lod2or3": round(float(side_any.sum()) * RES * RES),
        "sidewalk_lod3": round(float(get("side", 3).sum()) * RES * RES),
    }
    A = dilate(down(all_any, k, ny1, nx1), 3)
    A3 = dilate(down(all_l3, k, ny1, nx1), 3)
    S12 = dilate(down(side_any, k, ny1, nx1), 12)
    del masks, all_any, all_l3, side_any

    # 歩行空間 2020
    lk = json.loads((REPO / "data" / "research_cache" / "r58" / "shibuyananbu_link_2020.geojson").read_text(encoding="utf-8"))
    hk = []
    for ft in lk["features"]:
        co = (ft.get("geometry") or {}).get("coordinates") or []
        if len(co) < 2:
            continue
        xs, ys = R.local(np.array([c[1] for c in co]), np.array([c[0] for c in co]))
        hk.append((int((ft.get("properties") or {}).get("rt_struct", 99)), list(zip(xs.tolist(), ys.tolist()))))
    H5 = dilate(raster_lines([g for _, g in hk], ny1, nx1), 5)

    # OSM の建物の足跡を 1 m 格子に
    osm = R.load_osm()
    B = np.zeros((ny1, nx1), dtype=bool)
    for b in osm["buildings"]:
        fp = b["footprint"]
        if isinstance(fp, str):
            fp = json.loads(fp)
        if len(fp) < 3:
            continue
        a = np.array(fp, dtype=float)
        R.fill_ring(B, a[:, 0] - R.X_MIN, a[:, 1] - R.Y_MIN)
    print("aux rasters", round(time.time() - t0, 1), flush=True)

    def gap_width(px, py, ux, uy, half_cap=20.0):
        """辺に垂直な両方向で建物の画素に当たるまでの距離の和(0.5 m 刻み)。片側でも当たらなければ None。"""
        nxv, nyv = -uy, ux
        tot = 0.0
        for s in (1, -1):
            d = 0.5
            hit = False
            while d <= half_cap:
                ii, jj = int(px + s * nxv * d - R.X_MIN), int(py + s * nyv * d - R.Y_MIN)
                if not (0 <= jj < ny1 and 0 <= ii < nx1):
                    return None
                if B[jj, ii]:
                    hit = True
                    break
                d += 0.5
            if not hit:
                return None
            tot += d
        return tot

    tot, on_any, on_l3, nos_hk, near_side = Counter(), Counter(), Counter(), Counter(), Counter()
    band_c = defaultdict(Counter)
    gaps = defaultdict(list)
    rng = np.random.default_rng(82)
    gl = [(e["klass"], e["geometry"]) for e in osm["edges"] if not e.get("layer")]
    for c, px, py, ii, jj, w, ux, uy in sample_points(gl, ny1, nx1):
        tot[c] += w
        cov = bool(A[jj, ii])
        r0 = math.hypot(px, py)
        band = "0-300m" if r0 < 300 else "300-700m" if r0 < 700 else "700m+"
        band_c[band]["covered" if cov else "no_surface"] += w
        if cov:
            on_any[c] += w
            if S12[jj, ii]:
                near_side[c] += w
        elif H5[jj, ii]:
            nos_hk[c] += w
        if A3[jj, ii]:
            on_l3[c] += w
        if c in ("residential", "service", "unclassified", "tertiary", "footway", "pedestrian") and rng.random() < 0.15:
            gaps[(c, cov)].append(gap_width(px, py, ux, uy))
    T = sum(tot.values())
    out["osm_GL_len_m_total"] = round(T)
    out["share_on_plateau_any_lod_3m"] = round(sum(on_any.values()) / T, 4)
    out["share_on_plateau_lod3_layer_3m"] = round(sum(on_l3.values()) / T, 4)
    out["by_klass"] = {
        c: {"len_m": round(v), "no_surface_m": round(v - on_any[c]), "no_surface_share": round(1 - on_any[c] / v, 3),
            "on_lod3_layer_share": round(on_l3[c] / v, 3), "covered_and_sidewalk_12m_share": round(near_side[c] / v, 3),
            "no_surface_but_hokoukukan2020_within5m_m": round(nos_hk[c])}
        for c, v in tot.most_common()
    }
    NS = T - sum(on_any.values())
    out["no_surface_total_m"] = round(NS)
    out["no_surface_share"] = round(NS / T, 4)
    out["no_surface_hokoukukan2020_within5m_m"] = round(sum(nos_hk.values()))
    out["by_distance_from_origin"] = {b: {k2: round(v2) for k2, v2 in c2.items()} for b, c2 in sorted(band_c.items())}

    def q(v):
        vv = [x for x in v if x is not None]
        d = {"n_sample": len(v), "none_share": round(sum(1 for x in v if x is None) / max(1, len(v)), 3)}
        if len(vv) >= 5:
            d.update({"p10": round(float(np.quantile(vv, .1)), 1), "p50": round(float(np.median(vv)), 1), "p90": round(float(np.quantile(vv, .9)), 1)})
        return d
    out["building_gap_width_m"] = {f"{c}|{'covered' if cov else 'no_surface'}": q(v) for (c, cov), v in sorted(gaps.items())}
    out["building_gap_note"] = ("辺の 2 m 点の 15% 標本。辺に垂直な両方向で OSM 建物の足跡(1 m 格子)に当たるまでの距離の和。"
                                "片側 20 m 以内に当たらなければ None。道路の幅ではなく建物どうしの空き(前庭・駐車場・塀の内側を含む)=上限の目安")

    # 歩行空間 2020 のうち PLATEAU の面に載らない長さ
    hk_tot, hk_off = Counter(), Counter()
    for s, px, py, ii, jj, w, ux, uy in sample_points(hk, ny1, nx1):
        hk_tot[s] += w
        if not A[jj, ii]:
            hk_off[s] += w
    out["hokoukukan2020_in_w1_by_rt_struct_m"] = {str(s): {"len_m": round(v), "off_plateau_surface_m": round(hk_off[s])} for s, v in sorted(hk_tot.items())}
    out["hokoukukan2020_in_w1_total_m"] = round(sum(hk_tot.values()))
    out["hokoukukan2020_off_plateau_m"] = round(sum(hk_off.values()))

    # OSM の幅・歩道のタグ(車道系 highway の生のタグ・2026-09-28 取得)
    rn = json.loads((R.OSM / "road_names_overpass_20260928.json").read_text(encoding="utf-8"))["elements"]
    tag_len = defaultdict(Counter)
    sw_vals = Counter()
    for el in rn:
        tg = el.get("tags") or {}
        geo = el.get("geometry") or []
        Lw = 0.0
        for p0, p1 in zip(geo, geo[1:]):
            xa, ya = R.local(p0["lat"], p0["lon"])
            xb, yb = R.local(p1["lat"], p1["lon"])
            if R.in_w1_xy(float((xa + xb) / 2), float((ya + yb) / 2)):
                Lw += math.hypot(float(xb - xa), float(yb - ya))
        if Lw <= 0:
            continue
        h = tg.get("highway")
        tag_len[h]["ways"] += 1
        tag_len[h]["len_m"] += Lw
        for key in ("width", "est_width", "sidewalk", "lanes", "maxwidth"):
            has = (key in tg) or (key == "sidewalk" and any(t.startswith("sidewalk:") for t in tg))
            if has:
                tag_len[h][f"{key}_ways"] += 1
                tag_len[h][f"{key}_len_m"] += Lw
        if "sidewalk" in tg:
            sw_vals[tg["sidewalk"]] += 1
    out["osm_road_tags_in_w1"] = {h: {kk: round(vv) for kk, vv in c.items()} for h, c in sorted(tag_len.items(), key=lambda kv: -kv[1]["len_m"])}
    out["osm_sidewalk_values"] = dict(sw_vals)

    # 横断歩道(OSM の node・2026-09-07 取得・座標なし=件数だけ)
    sf = json.loads((R.OSM / "street_features_overpass_20260907.json").read_text(encoding="utf-8"))["elements"]
    cr = [e for e in sf if (e.get("tags") or {}).get("highway") == "crossing"]
    out["osm_highway_crossing_nodes"] = len(cr)
    out["osm_crossing_tag_values"] = dict(Counter((e["tags"].get("crossing") or "(none)") for e in cr))
    out["osm_crossing_markings_values"] = dict(Counter((e["tags"].get("crossing:markings") or "(none)") for e in cr))

    # PLATEAU 都市設備 frn(W1 の 2 メッシュ)の function
    fn = R.codelist("CityFurniture_function")
    fr = {}
    for m in ("53393586", "53393596"):
        p = R.UDX / "frn" / f"{m}_frn_6697_op.gml"
        cnt_w1, geom = Counter(), Counter()
        for el in R.members(p):
            if not el.tag.endswith("}CityFurniture"):
                continue
            f = None
            for c in el:
                if c.tag.endswith("}function") and c.text:
                    f = c.text.strip()
                    break
            pl = next(el.iter(R.T("gml:posList")), None)
            if pl is None:
                continue
            a = R.poslist(pl)[:1]
            x, y = R.local(a[:, 0], a[:, 1])
            if not R.in_w1_xy(float(x[0]), float(y[0])):
                continue
            cnt_w1[f"{f} {fn.get(str(f), '?')}"] += 1
            for c in el:
                tg = c.tag.split("}")[1]
                if tg.startswith("lod"):
                    geom[f"{f}:{tg}"] += 1
        fr[m] = {"in_w1_by_function": dict(cnt_w1.most_common()), "geometry_props": dict(geom.most_common())}
    out["plateau_frn"] = fr
    out["elapsed_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("done", out["elapsed_s"])


if __name__ == "__main__":
    main()
