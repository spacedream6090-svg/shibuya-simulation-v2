"""合成の小さな面のナビメッシュ(段 1 の試験の材料・データ不要)。

200 m × 200 m の舞台・地上のセル 4 つとデッキのセル 1 つ・地上(階 0)と デッキ(階 1)の 2 階:

- 地上: L 字の帯(y 10〜14 の横の帯 x 5〜150 + x 146〜150 の縦の帯 y 10〜150)と、離れた島(x 5〜20・y 100〜110)。
- デッキ: y 16〜19・x 20〜120 の帯。
- W1 の節: n0 (7, 12)・n1 (148, 12)・n2 (148, 148)・n3 (25, 17.5) デッキ・n4 (100, 17.5) デッキ・n5 (12, 105) 島・
  n6 (25, 12)。辺: n0–n6・n6–n1・n1–n2(地上)・n3–n4(デッキ)・n6–n3(階段=階をまたぐ)・n0–n5(島へ=つなぎの帯が要る)。
- DEM: x に沿って 2% の上り(z = 0.02 x)。

``build_synth(out_dir)`` は ``build.space.navmesh1._finish`` を通して ``nav1_*`` を書き、(メッシュの置き場, 材料) を返す。
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np

from shibuya.build.space import navmesh1 as N1
from shibuya.build.space import raster as R

NODES = np.array([[7.0, 12.0], [148.0, 12.0], [148.0, 148.0], [25.0, 17.5], [100.0, 17.5], [12.0, 105.0],
                  [25.0, 12.0]])
#: 節の階(0 地上・1 デッキ)と層の名
NODE_FLOOR = np.array([0, 0, 0, 1, 1, 0, 0])
NODE_BAND = ["GL", "GL", "GL", "DECK", "DECK", "GL", "GL"]
#: 辺 (u, v, klass)
EDGES = [(0, 6, "footway"), (6, 1, "footway"), (1, 2, "footway"), (3, 4, "footway"), (6, 3, "steps"),
         (0, 5, "footway")]


def edges_list() -> list[dict]:
    out = []
    for k, (u, v, kl) in enumerate(EDGES):
        xy = np.stack([NODES[u], NODES[v]])
        out.append({"edge": k, "u": u, "v": v, "klass": kl, "band_u": NODE_BAND[u], "band_v": NODE_BAND[v],
                    "layer": int(NODE_FLOOR[u]), "length_m": float(np.hypot(*(NODES[v] - NODES[u]))), "xy": xy})
    return out


def floors() -> tuple[dict, list[int]]:
    full = R.Grid.covering(0.0, 0.0, 200.0, 200.0, 0.5)
    gl = N1.FloorRaster(0, 0, full)
    sq = lambda x0, y0, x1, y1: np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], dtype=np.float64)  # noqa: E731
    gl.polygon([sq(5, 10, 150, 14)], 1)
    gl.polygon([sq(146, 10, 150, 150)], 1)
    gl.polygon([sq(5, 100, 20, 110)], 4)
    dk = N1.FloorRaster(1, 1, N1._sub_grid(full, 20, 16, 120, 19, 10.0))
    dk.polygon([sq(20, 16, 120, 19)], 14)
    dk.z[dk.label != 0] = 8.0
    return {0: gl, 1: dk}, [0, 1]


def cells() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    cix = np.array([0, 1, 0, 1, 0])
    ciy = np.array([0, 0, 1, 1, 0])
    cband = np.array([0, 0, 0, 0, 1], dtype=np.int8)
    return cix, ciy, cband


def dem() -> tuple[np.ndarray, R.Grid]:
    g = R.Grid.covering(0.0, 0.0, 200.0, 200.0, 2.0)
    xs = g.ox + (np.arange(g.nx) + 0.5) * g.res
    z = np.tile(0.02 * xs, (g.ny, 1)).astype(np.float32)
    return z, g


def build_synth(out_dir: Path, params: dict | None = None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    P = dict(N1.DEFAULT_PARAMS)
    if params:
        P.update(params)
    fl, codes = floors()
    z, g = dem()
    cix, ciy, cband = cells()
    notes: dict = {}
    outputs, stats, final = N1._finish(P, fl, codes, edges_list(), NODES, NODE_FLOOR, [], [], {}, z, g, cix, ciy,
                                       cband, out_dir, notes, lambda *_a, **_k: None)
    # 経路の道具が読む W1 の辺の形
    coords = np.concatenate([e["xy"] for e in edges_list()])
    offsets = np.concatenate([[0], np.cumsum([e["xy"].shape[0] for e in edges_list()])]).astype(np.int32)
    with open(out_dir / "w1_edge_geometry.npz", "wb") as fh:
        np.savez(fh, coords=coords, offsets=offsets)
    return out_dir, {"outputs": outputs, "stats": stats, "final": final, "notes": notes}


def fake_assets() -> SimpleNamespace:
    """``engine.space.nav1.NavSpace`` が読む資産の形(W1 と W2 の一部)。"""
    cix, ciy, cband = cells()
    eu = np.array([e[0] for e in EDGES], dtype=np.int32)
    ev = np.array([e[1] for e in EDGES], dtype=np.int32)
    el = np.array([np.hypot(*(NODES[v] - NODES[u])) for u, v, _k in EDGES], dtype=np.float32)
    return SimpleNamespace(node_xy=NODES.astype(np.float32), edge_u=eu, edge_v=ev, edge_len_m=el, cell_ix=cix,
                           cell_iy=ciy, cell_band=cband, n_cells=int(cix.size))
