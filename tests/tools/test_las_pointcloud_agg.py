# -*- coding: utf-8 -*-
"""tools/spatial/las_pointcloud_agg(都の区部点群の集計・指示書 11-02 取得 1)の試験。実データは読まない。

- 座標: 第 9 系の原点 (0, 0) → (36°, 139°50′)・国土地理院の換算サービスの 2 点(2026-11-02 に読むだけ)で 1 mm 未満・
  世界の平面 ↔ 第 9 系の往復。
- LAS: 合成の LAS 1.2 PF3(ヘッダ 227 B・GeoKey の VLR・数百点)を読む・版と大きさの食い違いで止まる。
- 集計(合成の 3 セル+DECK+UG): DEM=Class 2 の最低・DSM=全点の最高・4% の坂(0.25 m と 2 m)・0.15 m の段・
  DSM−DEM の 3〜8 m・隣のセルとの差・PLATEAU DEM との差・地下の「無いと宣言」・DECK/UG に地上の値・図郭の完了。
- 部品: 押し引きの穴埋め・多角形の塗り(穴つき)・縁石の割合・図郭をまたぐ min/max・zip と取得ログの検査。
- 守り: 識別子に禁じた語が無い・要約に絶対の道筋が無い。
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[2]
_SP = ROOT / "tools" / "spatial"
if str(_SP) not in sys.path:
    sys.path.insert(0, str(_SP))

import jgd_plane as JP  # noqa: E402
import las_io as LI  # noqa: E402
import las_pointcloud_agg as AG  # noqa: E402

BANNED_WORDS = ("op" + "en", "t" + "ick")


# ---------------------------------------------------------------------- 座標
def test_zone9_origin():
    lat, lon = JP.plane_to_latlon(0.0, 0.0)
    assert lat == pytest.approx(36.0, abs=1e-12)
    assert lon == pytest.approx(139.0 + 50.0 / 60.0, abs=1e-12)
    x, y = JP.latlon_to_plane(36.0, 139.0 + 50.0 / 60.0)
    assert abs(x) < 1e-6 and abs(y) < 1e-6


def test_gsi_service_points():
    # 国土地理院 測量計算サイト bl2xy / xy2bl(JGD2011・第 9 系)の出力(2026-11-02 に読むだけ・保存しない)
    x, y = JP.latlon_to_plane(35.658034, 139.701636)  # 渋谷駅の付近
    assert x == pytest.approx(-37931.3401, abs=1e-3)
    assert y == pytest.approx(-11924.1805, abs=1e-3)
    lat, lon = JP.plane_to_latlon(-36150.0, -13000.0)
    assert lat == pytest.approx(35.67407691, abs=1e-8)  # 1e-8 度 ≈ 1 mm
    assert lon == pytest.approx(139.68972533, abs=1e-8)


def test_local_plane_roundtrip():
    xs = np.array([-1000.0, 0.0, 123.4, 1300.0])
    ys = np.array([-1400.0, 0.0, -56.7, 1500.0])
    e, n = AG.local_to_plane(xs, ys)
    x2, y2 = AG.plane_to_local(e, n)
    assert np.max(np.abs(x2 - xs)) < 1e-6 and np.max(np.abs(y2 - ys)) < 1e-6
    # 世界の原点は第 9 系で北 約 −37.8 km・東 約 −12.0 km(LAS X=東・Y=北)
    e0, n0 = AG.local_to_plane(0.0, 0.0)
    assert -37_900 < n0 < -37_600 and -12_100 < e0 < -11_800


# ---------------------------------------------------------------------- LAS
def test_las_roundtrip(tmp_path):
    rng = np.random.default_rng(0)
    x = rng.uniform(-13200, -12800, 300)
    y = rng.uniform(-36300, -36000, 300)
    z = rng.uniform(15, 80, 300)
    c = rng.integers(1, 4, 300)
    p = tmp_path / "t.las"
    p.write_bytes(LI.build_las_bytes(x, y, z, c, returns=rng.integers(1, 3, 300)))
    h, pts = LI.read_points(p)
    assert h.version == (1, 2) and h.point_format == 3 and h.record_length == 34 and h.header_size == 227
    assert h.n_points == 300 and h.geokeys.get(3072) == 6677
    assert np.allclose(pts["X"] * h.scale[0], x, atol=6e-4)
    assert np.allclose(pts["Z"] * h.scale[2], z, atol=6e-4)
    assert np.array_equal(pts["classification"] & 31, c)
    assert h.bbox["min_x"] == pytest.approx(x.min(), abs=1e-3) and h.bbox["max_y"] == pytest.approx(y.max(), abs=1e-3)
    assert sum(h.n_by_return) == 300
    del pts


def test_las_rejects_bad(tmp_path):
    b = bytearray(LI.build_las_bytes(np.zeros(3), np.zeros(3), np.zeros(3), np.ones(3)))
    p = tmp_path / "short.las"
    p.write_bytes(bytes(b[:-5]))
    with pytest.raises(LI.LasFormatError):
        LI.read_points(p)
    b2 = bytearray(b)
    b2[25] = 4  # 版 1.4
    with pytest.raises(LI.LasFormatError):
        LI.parse_header(bytes(b2))
    with pytest.raises(LI.LasFormatError):
        LI.parse_header(b"XXXX" + bytes(b[4:]))


# ---------------------------------------------------------------------- 合成の世界
MESH = "09LD9001"


def _pts_patch(x0, y0, nx, ny, zfun, cls):
    """世界の平面で 0.25 m 画素の中心に 1 点ずつ。"""
    ii, jj = np.meshgrid(np.arange(nx), np.arange(ny), indexing="xy")
    x = x0 + (ii + 0.5) * 0.25
    y = y0 + (jj + 0.5) * 0.25
    z = zfun(x, y)
    return x.ravel(), y.ravel(), np.round(z.ravel(), 3), np.full(x.size, cls)


B_X = [50.1, 50.2, 50.15]
B_Y = [12.3, 12.35, 12.3]
NAV_OX, NAV_OY, NAV_RES = -100.0, -100.0, 2.0


def _nav_value(x, y):
    """合成の PLATEAU DEM: 北へ 2 m ごとに 0.1 m 上がる(行の番号=北向きに増える)。"""
    j = np.floor((np.asarray(y) - NAV_OY) / NAV_RES)
    return 20.0 + 0.1 * j


def _world(tmp_path, *, with_log=True, bad_sha=False, epsg=6677, swap_xy=False):
    raw = tmp_path / "raw"
    raw.mkdir()
    parts = [
        # A: 4% の坂(x 方向)の地面 24×24 画素(画素 40〜63 = 2 m の区画にそろえる)
        _pts_patch(10.0, 10.0, 24, 24, lambda x, y: 20.0 + 0.04 * (x - 10.0), 2),
        # C: デッキ(Class 1 だけ・高さ 25 m)8×8 画素
        _pts_patch(60.0, 60.0, 8, 8, lambda x, y: np.full_like(x, 25.0), 1),
        # D: セル (1, 0) の平らな地面と 0.15 m の段(x=115 m)
        _pts_patch(110.0, 10.0, 40, 8, lambda x, y: np.where(x < 115.0, 21.0, 21.15), 2),
    ]
    xs = [p[0] for p in parts]
    ys = [p[1] for p in parts]
    zs = [p[2] for p in parts]
    cs = [p[3] for p in parts]
    # B: 1 画素に地面 2 点と非地面 1 点(DEM=最低・DSM=最高)。x≠y=転置と上下反転を見分ける(検収 M1)
    xs.append(np.array(B_X))
    ys.append(np.array(B_Y))
    zs.append(np.array([21.0, 21.3, 30.0]))
    cs.append(np.array([2, 2, 1]))
    x = np.concatenate(xs)
    y = np.concatenate(ys)
    z = np.concatenate(zs)
    c = np.concatenate(cs)
    e, n = AG.local_to_plane(x, y)
    # 図郭の四隅(セルの外=集計に入らない点)
    e0, n0 = AG.local_to_plane(-5.0, -5.0)
    e1, n1 = AG.local_to_plane(205.0, 205.0)
    ce = np.array([e0, e1, e0, e1]).ravel()
    cn = np.array([n0, n0, n1, n1]).ravel()
    e = np.concatenate([e, ce])
    n = np.concatenate([n, cn])
    z = np.concatenate([z, np.full(4, 20.0)])
    c = np.concatenate([c, np.ones(4, dtype=int)])
    las = LI.build_las_bytes(n, e, z, c, epsg=epsg) if swap_xy else LI.build_las_bytes(e, n, z, c, epsg=epsg)
    zp = raw / f"{MESH}.zip"
    with zipfile.ZipFile(zp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{MESH}.las", las)
    sha = hashlib.sha256(zp.read_bytes()).hexdigest()
    if bad_sha:
        sha = "0" * 64
    size = zp.stat().st_size
    if with_log:
        log = ["mesh\turl\tstart_utc\tend_utc\thttp\tbytes\texpected_bytes\tsha256\tlast_modified\tetag",
               f"{MESH}\thttps://example.invalid/{MESH}.zip\tx\tx\t200\t{size}\t{size}\tFAIL_try1\t\t",
               f"{MESH}\thttps://example.invalid/{MESH}.zip\tx\t2026-11-02T00:00:00Z\t200\t{size}\t{size}\t{sha}\t\t",
               f"9001\thttps://example.invalid/{MESH}.zip\tx\tx\t200\t{size}\t{size}\t{sha}\t\t"]
        (raw / "_fetch_log.tsv").write_bytes(("\n".join(log) + "\n").encode("utf-8"))
    la0, lo0 = JP.plane_to_latlon(min(n0, n1), min(e0, e1))
    la1, lo1 = JP.plane_to_latlon(max(n0, n1), max(e0, e1))
    idx = {MESH: {"url": f"https://example.invalid/{MESH}.zip", "bbox_WSEN": [float(lo0), float(la0), float(lo1),
                                                                              float(la1)]}}
    (tmp_path / "idx.json").write_text(json.dumps(idx), encoding="utf-8")
    cells = pa.table({"place_id": ["g0_0_GL", "g1_0_GL", "g0_1_GL", "g0_0_DECK", "g1_0_UG"],
                      "ix": pa.array([0, 1, 0, 0, 1], pa.int32()), "iy": pa.array([0, 0, 1, 0, 0], pa.int32()),
                      "band": ["GL", "GL", "GL", "DECK", "UG"]})
    pq.write_table(cells, tmp_path / "cells.parquet")
    jj = np.arange(150, dtype=np.float64)
    nav = np.repeat((20.0 + 0.1 * jj)[:, None], 150, axis=1).astype(np.float32)  # 行 j = 南から j 番目
    np.save(tmp_path / "nav.npy", nav)
    (tmp_path / "nav_meta.json").write_text(json.dumps({"dem": {"ox": NAV_OX, "oy": NAV_OY, "res": NAV_RES,
                                                                 "nx": 150, "ny": 150}}), encoding="utf-8")
    return raw


def _run(tmp_path, **kw):
    raw = _world(tmp_path, **{k: kw.pop(k) for k in ("with_log", "bad_sha", "epsg", "swap_xy") if k in kw})
    return AG.run(raw, tmp_path / "cells.parquet", tmp_path / "out", mesh_index=tmp_path / "idx.json",
                  nav_dem_path=tmp_path / "nav.npy", nav_meta_path=tmp_path / "nav_meta.json",
                  plateau_udx=None, plateau_dir=None, log=lambda *_: None, **kw)


def _rows(tmp_path):
    return {r["place_id"]: r for r in pq.read_table(tmp_path / "out" / "pc_cells.parquet").to_pylist()}


def test_run_synthetic_world(tmp_path):
    s = _run(tmp_path)
    assert s["meshes_done"] == [MESH] and s["n_meshes_done"] == 1
    m = s["meshes"][MESH]
    assert m["n_points"] == 576 + 64 + 320 + 3 + 4 and m["n_points_in_cells"] == 576 + 64 + 320 + 3
    assert m["class_counts"] == {"1": 64 + 1 + 4, "2": 576 + 320 + 2}
    assert m["axis_check"]["epsg_projected"] == 6677
    assert m["axis_check"]["iou_las_x_is_east"] > 0.99 and m["axis_check"]["iou_las_x_is_north"] == 0.0
    assert m["zip_sha256_match"] is True and len(m["las_sha256"]) == 64
    assert (tmp_path / "raw" / "las" / f"{MESH}.las").exists()  # 生データは残す
    assert s["fetch_log_ignored_rows"] == [{"mesh": "9001", "why": "図郭の名の形でない"}]
    r = _rows(tmp_path)
    a = r["g0_0_GL"]
    assert a["has_data"] and a["complete"]
    # 4% の坂
    assert a["slope025_pct_med"] == pytest.approx(4.0, abs=0.05)
    assert a["slope2m_pct_med"] == pytest.approx(4.0, abs=0.05) and a["slope2m_pct_max"] == pytest.approx(4.0, abs=0.05)
    zA = np.round(20.0 + 0.04 * (10.0 + (np.arange(24) + 0.5) * 0.25 - 10.0), 3)
    zall = np.concatenate([np.repeat(zA, 24), [21.0]])
    assert a["gl_z_med"] == pytest.approx(float(np.median(zall)), abs=1e-3)
    assert a["n_pts_c2"] == 576 + 2 and a["n_pts_c1"] == 64 + 1
    # DSM−DEM: デッキの 25 m と埋めた地面(20〜21 m)の差 → 3〜8 m の帯
    assert a["h3_8_frac"] > 0 and 3.0 <= a["h3_8_mode_m"] <= 8.0
    # PLATEAU DEM(北へ上がる面)との差=画素の中心で引いた値と比べる(転置・上下反転なら外れる)
    yA = 10.0 + (np.arange(24) + 0.5) * 0.25
    dA = (np.repeat(zA, 24) - np.tile(_nav_value(0.0, yA), 24))
    dB = 21.0 - float(_nav_value(0.0, 12.3))
    assert a["pc_minus_plateau_dem_med"] == pytest.approx(float(np.median(np.concatenate([dA, [dB]]))), abs=1e-3)
    # 0.15 m の段(セル (1, 0)・x=115 m の 8 行)
    b = r["g1_0_GL"]
    assert b["n_step_edges_025"] == 8
    assert b["n_step_edges_05"] == 4  # 2×2 の平均=行が半分
    assert b["slope025_pct_max"] == pytest.approx(60.0, abs=0.5)  # 0.15 m / 0.25 m
    # セル (1, 0) の地面は y 10〜12 m=nav の行 55(25.5 m)。x を行に使う転置なら 30.5〜31 m になる
    assert b["pc_minus_plateau_dem_med"] == pytest.approx(21.075 - 25.5, abs=1e-3)
    # 隣のセルとの差
    assert a["nb_dz_east_m"] == pytest.approx(b["gl_z_med"] - a["gl_z_med"], abs=1e-6)
    assert a["nb_grade_max_pct"] == pytest.approx(abs(b["gl_z_med"] - a["gl_z_med"]), abs=1e-6)
    # 点の無いセル
    c = r["g0_1_GL"]
    assert c["has_data"] is False and c["complete"] is True
    # DECK と UG は地上の値を付ける・地下は「無いと宣言」
    d = r["g0_0_DECK"]
    assert d["values_from_gl_place_id"] == "g0_0_GL" and d["gl_z_med"] == a["gl_z_med"]
    assert d["layer_floor_source"] == "gl_z_med+h3_8_mode_all" and d["deck_floor_confidence"] == "heuristic"
    assert a["deck_floor_confidence"] == "" and s["cells"]["deck_floor_confidence"] == {"heuristic": 1}
    assert d["layer_floor_z"] == pytest.approx(a["gl_z_med"] + a["h3_8_mode_m"], abs=1e-6)
    u = r["g1_0_UG"]
    assert u["ug_floor_status"] == "absent_declared" and u["layer_floor_z"] is None
    assert "航空レーザ" in u["ug_floor_reason"] and u["gl_z_med"] == b["gl_z_med"]
    assert s["cells"]["ug_absent_declared"] == 1 and s["cells"]["by_band"] == {"GL": 3, "DECK": 1, "UG": 1}
    # 出力と要約
    out = tmp_path / "out"
    for f in ("pc_cells.parquet", "pc_summary.json", "pc_dem1m_filled.npy", "pc_dsm1m.npy"):
        assert (out / f).exists()
    txt = (out / "pc_summary.json").read_bytes().decode("utf-8")
    assert "\r\n" not in txt and "NaN" not in txt
    assert not re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/]|/Users/|/home/", txt)
    filled = np.load(out / "pc_dem1m_filled.npy")
    assert np.isfinite(filled).all()


def test_dem_min_dsm_max_in_one_pixel(tmp_path):
    _run(tmp_path)
    s = json.loads((tmp_path / "out" / "pc_summary.json").read_bytes().decode("utf-8"))
    dsm = np.load(tmp_path / "out" / "pc_dsm1m.npy")
    raw = np.load(tmp_path / "out" / "pc_dem1m_raw.npy")
    mo = s["mosaic_1m"]
    j = int((12.3 - mo["oy"]) // mo["res"])  # 行=北向きに増える
    i = int((50.1 - mo["ox"]) // mo["res"])
    assert dsm[j, i] == pytest.approx(30.0, abs=1e-3)
    assert raw[j, i] == pytest.approx(21.0, abs=1e-3)  # 2 点のうち低い方(1 m の中の画素は 1 つだけ)
    assert np.isnan(raw[i, j]) and np.isnan(dsm[i, j])  # 転置の位置には何も無い
    assert np.isnan(raw[raw.shape[0] - 1 - j, i])  # 上下反転の位置にも無い


def test_sha_mismatch_is_skipped(tmp_path):
    s = _run(tmp_path, bad_sha=True)
    assert s["n_meshes_done"] == 0
    assert s["meshes_skipped"][0]["mesh"] == MESH and "sha256" in s["meshes_skipped"][0]["why"]
    assert not (tmp_path / "raw" / "las" / f"{MESH}.las").exists()


def test_without_log_only_named_meshes(tmp_path):
    s = _run(tmp_path, with_log=False)
    assert s["n_meshes_done"] == 0 and s["meshes_skipped"] == []  # 取得ログで完了した図郭が無い
    s2 = AG.run(tmp_path / "raw", tmp_path / "cells.parquet", tmp_path / "out2", meshes=[MESH, "09LD0000"],
                mesh_index=tmp_path / "idx.json", log=lambda *_: None)
    assert s2["n_meshes_done"] == 1 and s2["meshes"][MESH]["zip_sha256_log"] is None
    assert s2["meshes_skipped"] == [{"mesh": "09LD0000", "why": "図郭の索引に無い"}]


def test_swapped_axes_are_refused(tmp_path):
    raw = _world(tmp_path, swap_xy=True)
    las_path, _meta = AG.extract_las(raw / f"{MESH}.zip", raw / "las", MESH)
    cells = AG.load_cells(tmp_path / "cells.parquet")
    grid = AG.Grid.from_pairs(zip(cells["ix"].tolist(), cells["iy"].tolist()))
    info = AG.load_mesh_index(tmp_path / "idx.json")[MESH]
    with pytest.raises(ValueError, match="X=東"):
        AG.bin_mesh(las_path, MESH, grid, info)
    with pytest.raises(ValueError):
        AG.run(raw, tmp_path / "cells.parquet", tmp_path / "out", mesh_index=tmp_path / "idx.json",
               log=lambda *_: None)


def test_las_without_crs_vlr_passes_by_bbox(tmp_path):
    s = _run(tmp_path, epsg=None)
    m = s["meshes"][MESH]
    assert s["n_meshes_done"] == 1 and m["axis_check"]["epsg_projected"] is None
    assert m["axis_check"]["has_crs_vlr"] is False and m["axis_check"]["iou_las_x_is_east"] > 0.99
    assert m["header"]["n_vlr"] == 0


def test_wrong_epsg_is_refused(tmp_path):
    raw = _world(tmp_path, epsg=6668)
    with pytest.raises(ValueError, match="EPSG 6668"):
        AG.run(raw, tmp_path / "cells.parquet", tmp_path / "out", mesh_index=tmp_path / "idx.json",
               log=lambda *_: None)


def test_fetch_log_first_row_and_conflict(tmp_path):
    head = "mesh\turl\tstart_utc\tend_utc\thttp\tbytes\texpected_bytes\tsha256\tlast_modified\tetag\n"
    p = tmp_path / "log.tsv"
    p.write_bytes((head + "09LD0003\tu\ts\tfirst\t200\t10\t10\t" + "b" * 64 + "\t\t\n"
                   + "09LD0003\tu\ts\tsecond\t200\t10\t10\t" + "b" * 64 + "\t\t\n").encode("utf-8"))
    done, _ = AG.parse_fetch_log(p)
    assert done["09LD0003"]["end_utc"] == "first" and done["09LD0003"]["n_done_rows"] == 2
    p.write_bytes((head + "09LD0003\tu\ts\te\t200\t10\t10\t" + "b" * 64 + "\t\t\n"
                   + "09LD0003\tu\ts\te\t200\t10\t10\t" + "c" * 64 + "\t\t\n").encode("utf-8"))
    with pytest.raises(ValueError, match="食い違う"):
        AG.parse_fetch_log(p)


# ---------------------------------------------------------------------- PLATEAU の入力(橋梁・建物・道路の面)
def _square_tris(x0, y0, x1, y1, z):
    a, b, c, d = [x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z]
    return np.array([[a, b, c], [a, c, d]], dtype=np.float64)


def _tile_store(grid, dem_fn, dsm_fn):
    st = AG.TileStore(grid)
    T = AG.TILE
    for c in range(grid.n):
        cx, cy = int(grid.ix[c]), int(grid.iy[c])
        xc = cx * 100.0 + (np.arange(T) + 0.5) * 0.25
        yc = cy * 100.0 + (np.arange(T) + 0.5) * 0.25
        X, Y = np.meshgrid(xc, yc, indexing="xy")
        dem = dem_fn(X, Y).astype(np.float32)[None]
        dsm = np.maximum(dsm_fn(X, Y), dem_fn(X, Y)).astype(np.float32)[None]
        cc = np.zeros((1, 32), dtype=np.int64)
        cc[0, 2] = T * T
        st.merge(AG.MeshPartial(mesh="m", cols=np.array([c]), dem=dem, dsm=dsm, cls_counts=cc))
    return st


def test_plateau_inputs_deck_sources_and_curb(tmp_path):
    p = AG.AggParams()
    grid = AG.Grid.from_pairs([(0, 0), (1, 0), (2, 0)])
    cells = {"place_id": np.array(["g0_0_GL", "g1_0_GL", "g2_0_GL", "g0_0_DECK", "g1_0_DECK", "g2_0_DECK"]),
             "ix": np.array([0, 1, 2, 0, 1, 2]), "iy": np.array([0, 0, 0, 0, 0, 0]),
             "band": np.array(["GL", "GL", "GL", "DECK", "DECK", "DECK"])}

    def dem_fn(X, Y):
        # セル (0, 0) の y≥50 m は 0.15 m 高い歩道(y=50 m に段)
        return np.where((X < 100.0) & (Y >= 50.0), 20.15, 20.0)

    def dsm_fn(X, Y):
        z = np.full(X.shape, -np.inf)
        z = np.where((X >= 10) & (X < 30) & (Y >= 10) & (Y < 30), 26.0, z)        # 橋(0, 0)
        z = np.where((X >= 110) & (X < 130) & (Y >= 10) & (Y < 30), 25.0, z)      # デッキ(1, 0)・h 5 m
        z = np.where((X >= 150) & (X < 190) & (Y >= 10) & (Y < 90), 24.0, z)      # 建物(1, 0)・h 4 m・広い
        z = np.where((X >= 210) & (X < 230) & (Y >= 10) & (Y < 30), 27.0, z)      # デッキ(2, 0)・h 7 m
        return z

    st = _tile_store(grid, dem_fn, dsm_fn)
    # PLATEAU の入力を合成のファイルで(load_plateau_inputs の plateau_dir の道)
    pdir = tmp_path / "plateau"
    pdir.mkdir()
    bt = _square_tris(150.0, 10.0, 190.0, 90.0, 4.0)
    V = bt.reshape(-1, 3).astype(np.float32)
    F = np.arange(V.shape[0], dtype=np.int32).reshape(-1, 3)
    np.savez(pdir / "plateau_mesh.npz", V=V, F=F, building_offsets=np.array([0, 2], dtype=np.int32))
    (pdir / "plateau_index.json").write_text(json.dumps({"bbox": [-1.0, -1.0, 201.0, 101.0]}), encoding="utf-8")
    br = _square_tris(10.0, 10.0, 30.0, 30.0, 26.0 - 15.18)  # extras は ground0 を引いた高さ
    np.savez(pdir / "extras.npz", brid_V=br.reshape(-1, 3), brid_F=np.arange(6).reshape(-1, 3),
             brid_off=np.array([0, 2]))
    (pdir / "extras.json").write_text(json.dumps({"ground0": 15.18}), encoding="utf-8")
    pl = AG.load_plateau_inputs(None, pdir, grid, p, log=lambda *_: None)
    assert pl["n_brid"] == 1 and set(pl["brid"][0]) == {0}
    ids, top = pl["brid"]
    assert 80 * 80 <= int((ids[0] == 0).sum()) <= 81 * 81 and np.nanmax(top[0]) == pytest.approx(26.0, abs=1e-6)
    assert set(pl["bldg"]) == {1} and int(pl["bldg"][1].sum()) >= 160 * 320  # 1 画素広げた外形
    # 歩道(y 50〜60)と車道(y 40〜50)の面
    sw = AG.rasterize_polygons([[np.array([[0, 50], [100, 50], [100, 60], [0, 60]], dtype=float)]], grid)
    rw = AG.rasterize_polygons([[np.array([[0, 40], [100, 40], [100, 50], [0, 50]], dtype=float)]], grid)
    assert int(sw[0].sum()) == 400 * 40 and int(rw[0].sum()) == 400 * 40
    rects = {"m": (0.0, 0.0, 300.0, 100.0)}
    res = AG.aggregate(st, grid, cells, rects, ["m"], p, sidewalk=sw, roadway=rw, bldg=pl["bldg"],
                       bldg_rect=pl["bldg_rect"], brid=pl["brid"], n_brid=pl["n_brid"])
    r = {x["place_id"]: x for x in res["rows"]}
    d0, d1, d2 = r["g0_0_DECK"], r["g1_0_DECK"], r["g2_0_DECK"]
    assert d0["layer_floor_source"] == "dsm_in_plateau_brid_footprint" and d0["deck_floor_confidence"] == "brid"
    assert d0["layer_floor_z"] == pytest.approx(26.0, abs=1e-4) and 80 * 80 <= d0["brid_px"] <= 81 * 81  # 標本の端=1 列の余り
    assert d0["brid_dsm_minus_top_med"] == pytest.approx(0.0, abs=1e-4)
    assert d1["layer_floor_source"] == "gl_z_med+h3_8_mode_nobldg" and d1["deck_floor_confidence"] == "heuristic"
    assert d1["h3_8_mode_m"] == pytest.approx(4.125)  # 建物の方が広い=全部の最頻値は 4 m 台
    assert d1["layer_floor_z"] == pytest.approx(20.0 + 5.125)  # 建物を除くとデッキの 5 m 台
    assert d2["layer_floor_source"] == "gl_z_med+h3_8_mode_all" and d2["deck_floor_confidence"] == "heuristic"
    assert d2["bldg_mask_cover"] < 0.999 and d2["layer_floor_z"] == pytest.approx(20.0 + 7.125)
    assert res["brid_rows"][0]["n_px"] == d0["brid_px"] and res["brid_rows"][0]["h_med"] == pytest.approx(6.0, abs=1e-4)
    # 縁石: 歩道の中で車道から L1 で 2 画素以内=y 50〜50.5 の 2 行。段は y=50 の境(400 列)
    g0 = r["g0_0_GL"]
    assert g0["curb_px"] == 800 and g0["sidewalk_px"] == 400 * 40
    assert g0["n_step_edges_025"] == 400 and g0["n_step_edges_05"] == 200
    assert g0["curb_recall_025"] == 1.0 and g0["curb_step_near_frac_025"] == 1.0
    assert g0["curb_enrichment_025"] == pytest.approx(1.0 / (400 * 6 / (400 * 400)))
    assert r["g1_0_GL"]["curb_px"] == 0 and r["g1_0_GL"]["curb_recall_025"] != r["g1_0_GL"]["curb_recall_025"]


def test_load_plateau_inputs_reads_tran_gml(tmp_path):
    grid = AG.Grid.from_pairs([(0, 0)])
    udx = tmp_path / "udx"
    (udx / "tran").mkdir(parents=True)

    def poslist(pts):
        la, lo = AG.local_to_latlon(np.array([q[0] for q in pts]), np.array([q[1] for q in pts]))
        return " ".join(f"{a:.10f} {b:.10f} 20.0" for a, b in zip(la, lo))

    def area(code, pts):
        return (f"<tran:trafficArea><tran:TrafficArea><tran:function>{code}</tran:function><tran:lod2MultiSurface>"
                f"<gml:MultiSurface><gml:surfaceMember><gml:Polygon><gml:exterior><gml:LinearRing><gml:posList>"
                f"{poslist(pts)}</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></gml:surfaceMember>"
                f"</gml:MultiSurface></tran:lod2MultiSurface></tran:TrafficArea></tran:trafficArea>")

    sw = [(0, 50), (100, 50), (100, 60), (0, 60), (0, 50)]
    rw = [(0, 40), (100, 40), (100, 50), (0, 50), (0, 40)]
    gml = ('<?xml version="1.0" encoding="UTF-8"?><core:CityModel xmlns:core="http://www.opengis.net/citygml/2.0" '
           'xmlns:tran="http://www.opengis.net/citygml/transportation/2.0" xmlns:gml="http://www.opengis.net/gml">'
           '<core:cityObjectMember><tran:Road gml:id="r1"><tran:function>1</tran:function>'
           + area(2000, sw) + area(1000, rw) + "</tran:Road></core:cityObjectMember></core:CityModel>")
    (udx / "tran" / "t_tran_6697_op.gml").write_text(gml, encoding="utf-8")
    pl = AG.load_plateau_inputs(udx, None, grid, AG.AggParams(), log=lambda *_: None)
    assert pl["notes"]["tran"]["n_sidewalk_polygons"] == 1 and pl["notes"]["tran"]["n_roadway_polygons"] == 1
    assert abs(int(pl["sidewalk"][0].sum()) - 400 * 40) <= 400 and abs(int(pl["roadway"][0].sum()) - 400 * 40) <= 400


# ---------------------------------------------------------------------- 部品
def test_extract_rejects_other_members(tmp_path):
    zp = tmp_path / f"{MESH}.zip"
    with zipfile.ZipFile(zp, "w") as zf:
        zf.writestr(f"{MESH}.las", b"x")
        zf.writestr("readme.txt", b"y")
    with pytest.raises(ValueError):
        AG.extract_las(zp, tmp_path / "las", MESH)
    zp2 = tmp_path / "09LD9002.zip"
    with zipfile.ZipFile(zp2, "w") as zf:
        zf.writestr("09LD0000.las", b"x")
    with pytest.raises(ValueError):
        AG.extract_las(zp2, tmp_path / "las", "09LD9002")
    assert not (tmp_path / "las" / f"{MESH}.las").exists()


def test_parse_fetch_log(tmp_path):
    p = tmp_path / "log.tsv"
    p.write_bytes(("mesh\turl\tstart_utc\tend_utc\thttp\tbytes\texpected_bytes\tsha256\tlast_modified\tetag\n"
                   "09LD0001\tu\ts\te\t200\t10\t10\tFAIL_try1\t\t\n"
                   "09LD0002\tu\ts\te\t200\t9\t10\t" + "a" * 64 + "\t\t\n"
                   "09LD0003\tu\ts\te\t200\t10\t10\t" + "b" * 64 + "\t\t\n"
                   "0003\tu\ts\te\t200\t10\t10\t" + "b" * 64 + "\t\t\n").encode("utf-8"))
    done, ignored = AG.parse_fetch_log(p)
    assert list(done) == ["09LD0003"] and done["09LD0003"]["bytes"] == 10
    assert ignored == [{"mesh": "0003", "why": "図郭の名の形でない"}]


def test_tilestore_merge_min_max():
    grid = AG.Grid.from_pairs([(0, 0), (1, 0)])
    st = AG.TileStore(grid)
    T = AG.TILE

    def part(name, zdem, zdsm):
        dem = np.full((1, T, T), np.inf, dtype=np.float32)
        dsm = np.full((1, T, T), -np.inf, dtype=np.float32)
        dem[0, 5, 5] = zdem
        dsm[0, 5, 5] = zdsm
        cc = np.zeros((1, 32), dtype=np.int64)
        cc[0, 2] = 1
        return AG.MeshPartial(mesh=name, cols=np.array([0]), dem=dem, dsm=dsm, cls_counts=cc)

    st.merge(part("a", 20.0, 25.0))
    st.merge(part("b", 19.5, 24.0))
    assert st.dem_nan(0)[5, 5] == pytest.approx(19.5) and st.dsm_nan(0)[5, 5] == pytest.approx(25.0)
    assert np.isnan(st.dem_nan(0)[0, 0]) and st.cls[0][2] == 2 and st.meshes_of[0] == ["a", "b"]


def test_fill_push_pull():
    yy, xx = np.mgrid[0:64, 0:64].astype(float)
    a = 10.0 + 0.1 * xx
    b = a.copy()
    b[20:40, 20:40] = np.nan
    f = AG.fill_push_pull(b)
    assert np.isfinite(f).all()
    assert np.allclose(f[~np.isnan(b)], a[~np.isnan(b)], atol=1e-5)
    assert f[20:40, 20:40].min() >= a.min() - 1e-5 and f[20:40, 20:40].max() <= a.max() + 1e-5  # 周りの値の範囲
    assert np.isnan(AG.fill_push_pull(np.full((4, 4), np.nan))).all()


def test_fill_polygon_window_with_hole():
    outer = np.array([[0, 0], [2, 0], [2, 2], [0, 2]], dtype=float)
    hole = np.array([[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5]], dtype=float)
    m = AG.fill_polygon_window([outer], 0.0, 0.0, 0.25, 12, 12)
    assert m.sum() == 64 and m[:8, :8].all() and not m[8:, :].any()
    m2 = AG.fill_polygon_window([outer, hole], 0.0, 0.0, 0.25, 12, 12)
    assert m2.sum() == 64 - 16 and not m2[2:6, 2:6].any()
    # 窓が多角形の途中から始まる(左の交わりは窓の外)
    m3 = AG.fill_polygon_window([outer], 1.0, 0.0, 0.25, 8, 8)
    assert m3[:, :4].all() and not m3[:, 4:].any()


def test_polygons_of_rings_and_rasterize():
    grid = AG.Grid.from_pairs([(0, 0), (1, 0)])
    sq = np.array([[95, 10, 0], [105, 10, 0], [105, 20, 0], [95, 20, 0]], dtype=float)
    hole = np.array([[99, 14, 0], [101, 14, 0], [101, 16, 0], [99, 16, 0]], dtype=float)
    polys = AG._polygons_of_rings([(sq, 1), (hole, -1)])
    assert len(polys) == 1 and len(polys[0]) == 2
    out = AG.rasterize_polygons(polys, grid)
    tot = sum(int(v.sum()) for v in out.values())
    assert set(out) == {0, 1} and tot == (40 * 40) - (8 * 8)


def test_detect_steps_and_curb_metrics():
    p = AG.AggParams()
    z = np.full((10, 12), 20.0)
    z[:, 6:] = 20.2  # 0.2 m の段
    mark, n_step, n_eval = AG.detect_steps(z, p)
    assert n_step == 10 and n_eval == 10 * 9 + 7 * 12
    assert mark[:, 5].all() and mark[:, 6].all() and mark.sum() == 20
    z2 = z.copy()
    z2[:, 6:] = 20.4  # 0.4 m は段差の候補の外
    assert AG.detect_steps(z2, p)[1] == 0
    g = np.ones_like(z, dtype=bool)
    curb = np.zeros_like(g)
    curb[:, 6] = True
    m = AG._curb_metrics(mark, g, curb, 2)
    assert m["step_near_frac"] == 1.0 and m["recall"] == 1.0
    assert m["enrichment"] == pytest.approx(1.0 / (50 / 120))


def test_mode_and_block_mean():
    h = np.array([3.1, 5.05, 5.1, 5.2, 7.9, 9.0, 1.0])
    assert AG._mode(h, 3.0, 8.0, 0.25) == pytest.approx(5.125)
    assert math.isnan(AG._mode(np.array([1.0, 9.0]), 3.0, 8.0, 0.25))
    z = np.full((8, 8), np.nan)
    z[0, 0] = 1.0
    z[0, 1] = 3.0
    assert AG._block_mean(z, 4, 1)[0, 0] == pytest.approx(2.0)
    assert np.isnan(AG._block_mean(z, 4, 3)[0, 0])


def test_sealed_paths_are_refused(tmp_path):
    with pytest.raises(PermissionError):
        AG.parse_fetch_log(tmp_path / "jinryu" / "_fetch_log.tsv")
    with pytest.raises(PermissionError):
        AG.load_mesh_index(tmp_path / "boundary_counts.json")


# ---------------------------------------------------------------------- 守り
def _banned_identifiers(source: str) -> list[str]:
    found = []
    for node in ast.walk(ast.parse(source)):
        names: list[str] = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, ast.arg):
            names.append(node.arg)
        elif isinstance(node, ast.alias):
            names.append(node.asname or node.name)
        elif isinstance(node, ast.keyword) and node.arg:
            names.append(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.append(node.name)
        found += [n for n in names if any(w in n.lower() for w in BANNED_WORDS)]
    return found


def test_identifier_names_avoid_banned_words():
    files = sorted(_SP.glob("*.py"))
    assert {f.name for f in files} >= {"jgd_plane.py", "las_io.py", "las_pointcloud_agg.py"}
    bad = {f.name: _banned_identifiers(f.read_text(encoding="utf-8")) for f in files}
    assert all(v == [] for v in bad.values()), bad
    assert _banned_identifiers(Path(__file__).read_text(encoding="utf-8")) == []
    planted = "def " + BANNED_WORDS[0] + "_x(): pass\n"
    assert _banned_identifiers(planted) != []


def test_sources_have_no_absolute_paths_or_crlf():
    for f in sorted(_SP.glob("*.py")) + [Path(__file__)]:
        b = f.read_bytes()
        assert b"\r\n" not in b, f.name
        assert not re.search(rb"[A-Za-z]:\\Users|/Users/[^/\s]+/Desktop", b), f.name
