"""presence.py の到着セル(W11 駅出口)どうしの距離を測る(11-02・標準ライブラリ+pyarrow+numpy)。

使い方: python exit_distance_1102.py <世界資産の dir(data/world/v2)> [出力 JSON]

到着セルの集合は ``world.assets.load_process_assets`` と同じ写し方で作る
(``own_grid_place_id`` を先に引き、無ければ ``place_id``・範囲外は落とす・``np.unique``=``PlanExecutor._exit_cells``)。
座標は 2 通り: (a) w2_cells の centroid_x/centroid_y(W0 の原点・m/度で作ったローカル平面 m)
(b) ``rail_arrive`` が書く xy = w1_nodes の (x, y) をセル代表ノード(rep_node_idx)で引いたもの。
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq


def main() -> int:
    p = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    cells = pq.read_table(p / "w2_cells.parquet").to_pydict()
    nodes = pq.read_table(p / "w1_nodes.parquet", columns=["node_idx", "x", "y"]).to_pydict()
    exits = pq.read_table(p / "w11_station_exits.parquet").to_pydict()
    ext = pq.read_table(p / "w12_external_nodes.parquet").to_pydict()
    pid = [str(x) for x in cells["place_id"]]
    p2c = {s: i for i, s in enumerate(pid)}
    n_cells = len(pid)
    cen = np.stack([np.asarray(cells["centroid_x"], float), np.asarray(cells["centroid_y"], float)], 1)
    nxy = np.stack([np.asarray(nodes["x"], float), np.asarray(nodes["y"], float)], 1)
    rep = np.asarray(cells["rep_node_idx"], np.int64)
    repxy = nxy[rep]
    # 検算: centroid が格子 (ix, iy) の 100 m 升に入るか(ローカル平面 m の確認)
    ix = np.asarray(cells["ix"], float)
    iy = np.asarray(cells["iy"], float)
    in_box = ((cen[:, 0] >= ix * 100 - 1e-6) & (cen[:, 0] <= ix * 100 + 100 + 1e-6)
              & (cen[:, 1] >= iy * 100 - 1e-6) & (cen[:, 1] <= iy * 100 + 100 + 1e-6))
    raw = [p2c.get(str(exits["own_grid_place_id"][i]), p2c.get(str(exits["place_id"][i]), -1))
           for i in range(len(exits["place_id"]))]
    ex_rows = [c for c in raw if 0 <= c < n_cells]
    ex = np.unique(np.asarray(ex_rows, np.int64))

    def pair_max(xy, a, b):
        d = np.hypot(xy[a][:, None, 0] - xy[b][None, :, 0], xy[a][:, None, 1] - xy[b][None, :, 1])
        i, j = np.unravel_index(int(np.argmax(d)), d.shape)
        return float(d[i, j]), int(a[i]), int(b[j]), d

    res: dict = {
        "n_exit_rows": len(exits["place_id"]), "n_exit_rows_with_cell": len(ex_rows),
        "n_exit_cells_unique": int(ex.size), "exit_cells": [pid[c] for c in ex],
        "centroid_in_grid_box": int(in_box.sum()), "n_cells": n_cells,
    }
    # 駅名ごとのセル(到着セルに表参道・明治神宮前の出口が入っているか)
    by_station: dict[str, list[str]] = {}
    for i, c in enumerate(raw):
        if 0 <= c < n_cells:
            by_station.setdefault(str(exits["station_title"][i]), []).append(pid[c])
    res["exit_cells_by_station_title"] = {k: sorted(set(v)) for k, v in by_station.items()}
    for name, xy in (("centroid", cen), ("rep_node_xy", repxy)):
        m, a, b, d = pair_max(xy, ex, ex)
        res[f"exit_to_exit_max_m_{name}"] = round(m, 1)
        res[f"exit_to_exit_pair_{name}"] = [pid[a], pid[b]]
        # 1,355 m に近い対(±15 m)
        near = []
        for i in range(ex.size):
            for j in range(i + 1, ex.size):
                if abs(d[i, j] - 1355.0) <= 15.0:
                    near.append([pid[ex[i]], pid[ex[j]], round(float(d[i, j]), 1)])
        res[f"exit_pairs_near_1355_{name}"] = near
        allc = np.arange(n_cells)
        m2, a2, b2, _ = pair_max(xy, allc, ex)
        res[f"any_cell_to_exit_max_m_{name}"] = round(m2, 1)
        res[f"any_cell_to_exit_pair_{name}"] = [pid[a2], pid[b2]]
        # 渋谷の出口だけ(station_title == 渋谷)に限った場合
        sh = np.unique(np.asarray([c for i, c in enumerate(raw) if 0 <= c < n_cells
                                   and str(exits["station_title"][i]) == "渋谷"], np.int64))
        m3, a3, b3, _ = pair_max(xy, sh, sh)
        res[f"shibuya_exit_to_exit_max_m_{name}"] = round(m3, 1)
        res[f"shibuya_exit_to_exit_pair_{name}"] = [pid[a3], pid[b3]]
        # 方面 8・9 の門のセル(W12 attached_place_ids)から最も遠い到着セル(門の体が「門ではなく駅の出口」に現れる距離)
        for k in (8, 9):
            g = np.asarray([p2c[s] for s in json.loads(ext["attached_place_ids"][k]) if s in p2c], np.int64)
            dg = np.hypot(xy[g][:, None, 0] - xy[ex][None, :, 0], xy[g][:, None, 1] - xy[ex][None, :, 1])
            res[f"gate{k}_{ext['node_id'][k]}_n_cells"] = int(g.size)
            res[f"gate{k}_to_exit_max_m_{name}"] = round(float(dg.max()), 1)
            res[f"gate{k}_to_nearest_exit_median_m_{name}"] = round(float(np.median(dg.min(1))), 1)
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    print(txt)
    if out:
        out.write_text(txt + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
