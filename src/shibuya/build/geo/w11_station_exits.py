"""W11 駅・出口(§1 W11・D-W13)。

入力: ODPT stations(9路線ファイル)+ 駅出入口 45(W5)+ floorguide connections 22(W1)。
出力:
- ``w11_stations.parquet``            世界 bbox 内の ODPT 駅(路線ごとに1行)
- ``w11_station_exits.parquet``       駅→出口→セル表(``place_id``=最寄りノードのセル・
  ``own_grid_place_id``=出口自身の座標が落ちる格子セル)
- ``w11_station_graph_nodes.parquet`` 駅構内グラフのノード(ホーム/改札/出口)
- ``w11_station_graph_edges.parquet`` 同エッジ(**長さ = 幾何距離 × 1.3** = D-W13 の初期値)
- ``w11_floorguide_connections.parquet`` floorguide 直結 22 本(駅直結の印つき)

D-W13: 出口は配分しない。出口別の利用数はエンジンの経路探索の**結果**として出る。ここで作るのは
その探索が使う最小の構内グラフ(ホーム→改札→出口)だけ。

expedient
- 構内経路長 = 幾何距離 × 1.3(D-W13 の初期値・昇格条件=公式構内図からの実測)。
- ホーム位置 = ODPT の駅代表点(路線ごと)。改札は駅ごとに1つ、その駅に割り当てた出口の重心。
- 出口→駅の割当 = 名称一致(駅名を含む)優先、無ければ最近傍駅。
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

import numpy as np
import pyarrow as pa

from . import common as C

STAGE = "W11"
STAGE_VERSION = "1.0.0"

#: 世界範囲(OSM v8 meta.bbox)。ODPT 駅の絞り込みに使う。
BBOX = (35.6505, 139.6905, 35.6685, 139.7115)
#: bbox の外側マージン [m](expedient)。出口は bbox 内でもホームが bbox の外に出る駅
#: (表参道など)を取りこぼさないため。
BBOX_MARGIN_M = 300.0
#: D-W13 の構内経路長係数(expedient)。
INDOOR_PATH_FACTOR = 1.3
EXPECTED_EXITS = 45
EXPECTED_FLOORGUIDE_LINKS = 22

ODPT_STATION_FILES: tuple[str, ...] = (
    "stations_jr_yamanote.json",
    "stations_jr_saikyo.json",
    "stations_jr_shonanshinjuku.json",
    "stations_keio_inokashira.json",
    "stations_metro_ginza.json",
    "stations_metro_hanzomon.json",
    "stations_metro_fukutoshin.json",
    "stations_tokyu_denentoshi.json",
    "stations_tokyu_toyoko.json",
)


def _normalize_station_name(name: str) -> str:
    """駅名の表記ゆれを均す(``〈…〉`` の除去・末尾「駅」の除去)。"""
    out = re.sub(r"〈[^〉]*〉", "", name)
    return out.replace("駅", "").strip()


def run(ctx: C.Ctx) -> C.StageResult:
    odpt_paths = [ctx.path("odpt", name) for name in ODPT_STATION_FILES]
    for p in odpt_paths:
        if not p.exists():
            raise FileNotFoundError(f"W11 入力が無い: {p}")
    ent_p = ctx.out / "w5_entrances.parquet"
    fg_p = ctx.out / "w1_floorguide_links.parquet"
    cells_p = ctx.out / "w2_cells.parquet"
    for p in (ent_p, fg_p, cells_p):
        if not p.exists():
            raise FileNotFoundError(f"W11 は W1/W2/W5 の出力を必要とする: {p}")

    cells = set(C.read_parquet_columns(cells_p, ["place_id"])["place_id"])
    ent = C.read_parquet_columns(ent_p)
    fg = C.read_parquet_columns(fg_p)

    exit_rows = [i for i, k in enumerate(ent["kind"]) if k == "station_exit"]

    # --- bbox 内の ODPT 駅 ---
    # ODPT で geo:lat/long を持つのは東京メトロだけ(F5/F10 と整合: JR・東急・京王は座標なし)。
    # 座標を持つ駅で bbox 内に入ったものを基準にし、**同名の座標なし駅**は同名基準点の重心へ置く
    # (expedient)。これで渋谷駅の9路線ホームが揃う。
    raw: list[dict[str, Any]] = []
    n_stations_total = 0
    for p in odpt_paths:
        payload = C.load_json(p)
        for s in payload["data"]:
            n_stations_total += 1
            raw.append(s)

    dlat = BBOX_MARGIN_M / C.M_PER_DEG_LAT
    dlon = BBOX_MARGIN_M / C.M_PER_DEG_LON

    def in_box(lat: float, lon: float) -> bool:
        return (
            BBOX[0] - dlat <= lat <= BBOX[2] + dlat
            and BBOX[1] - dlon <= lon <= BBOX[3] + dlon
        )

    based: list[tuple[dict[str, Any], float, float]] = []
    for s in raw:
        lat = s.get("geo:lat")
        lon = s.get("geo:long")
        if lat is None or lon is None:
            continue
        if not in_box(float(lat), float(lon)):
            continue
        based.append((s, float(lat), float(lon)))

    title_anchor: dict[str, tuple[float, float]] = {}
    for s, lat, lon in based:
        t = s.get("dc:title") or ""
        title_anchor.setdefault(t, (0.0, 0.0))
    for t in list(title_anchor):
        pts = [(lat, lon) for s, lat, lon in based if (s.get("dc:title") or "") == t]
        title_anchor[t] = (
            sum(a for a, _ in pts) / len(pts),
            sum(b for _, b in pts) / len(pts),
        )

    st_id: list[str] = []
    st_title: list[str] = []
    st_operator: list[str] = []
    st_railway: list[str] = []
    st_code: list[str] = []
    st_lat: list[float] = []
    st_lon: list[float] = []
    st_x: list[float] = []
    st_y: list[float] = []
    st_pos_src: list[str] = []
    n_title_centroid = 0
    for s in raw:
        title = s.get("dc:title") or ""
        lat = s.get("geo:lat")
        lon = s.get("geo:long")
        if lat is not None and lon is not None:
            if not in_box(float(lat), float(lon)):
                continue
            plat, plon, src = float(lat), float(lon), "odpt"
        else:
            if title not in title_anchor:
                continue
            plat, plon = title_anchor[title]
            src = "title_centroid"
            n_title_centroid += 1
        x, y = C.latlon_to_local(plat, plon)
        st_id.append(s["owl:sameAs"])
        st_title.append(title)
        st_operator.append(s.get("odpt:operator") or "")
        st_railway.append(s.get("odpt:railway") or "")
        st_code.append(s.get("odpt:stationCode") or "")
        st_lat.append(round(plat, 7))
        st_lon.append(round(plon, 7))
        st_x.append(round(x, 3))
        st_y.append(round(y, 3))
        st_pos_src.append(src)

    order = sorted(range(len(st_id)), key=lambda i: st_id[i])
    st_id = [st_id[i] for i in order]
    st_title = [st_title[i] for i in order]
    st_operator = [st_operator[i] for i in order]
    st_railway = [st_railway[i] for i in order]
    st_code = [st_code[i] for i in order]
    st_lat = [st_lat[i] for i in order]
    st_lon = [st_lon[i] for i in order]
    st_x = [st_x[i] for i in order]
    st_y = [st_y[i] for i in order]
    st_pos_src = [st_pos_src[i] for i in order]

    # 駅名(タイトル)単位で「駅」を束ねる(路線ごとに1行=ホーム1本)
    titles = sorted(set(st_title))

    sx = np.asarray(st_x)
    sy = np.asarray(st_y)

    # --- 出口 → 駅(名称一致優先・無ければ最近傍)---
    ex_station_title: list[str] = []
    ex_rule: list[str] = []
    for i in exit_rows:
        name = _normalize_station_name(ent["name"][i] or "")
        hit = None
        for t in titles:
            tn = _normalize_station_name(t)
            if tn and tn in name:
                hit = t
                break
        if hit is not None:
            ex_station_title.append(hit)
            ex_rule.append("name")
        else:
            d2 = (sx - float(ent["x"][i])) ** 2 + (sy - float(ent["y"][i])) ** 2
            ex_station_title.append(st_title[int(np.argmin(d2))])
            ex_rule.append("nearest")

    exits_by_title: dict[str, list[int]] = defaultdict(list)
    for k, i in enumerate(exit_rows):
        exits_by_title[ex_station_title[k]].append(i)

    # 出口が W2 のセルに載っているかは **出口自身の格子セル**で問う(最寄りノードのセルを
    # 引くと、W2 が歩行グラフから作られている以上ほぼ自明に真になる)。
    exit_own_cell = {
        i: C.place_id(*C.grid_ij(float(ent["x"][i]), float(ent["y"][i])), ent["band"][i])
        for i in exit_rows
    }
    exit_cells_known = sum(1 for i in exit_rows if exit_own_cell[i] in cells)
    exit_own_cells_missing = len(exit_rows) - exit_cells_known
    exit_ids_unique = len({ent["ref"][i] for i in exit_rows})

    # --- 構内グラフ ---
    sg_id: list[str] = []
    sg_kind: list[str] = []
    sg_station: list[str] = []
    sg_railway: list[str] = []
    sg_x: list[float] = []
    sg_y: list[float] = []
    sg_place: list[str] = []

    gate_xy: dict[str, tuple[float, float]] = {}
    for t in titles:
        rows = exits_by_title.get(t, [])
        if rows:
            gx = float(np.mean([float(ent["x"][i]) for i in rows]))
            gy = float(np.mean([float(ent["y"][i]) for i in rows]))
        else:
            k = st_title.index(t)
            gx, gy = st_x[k], st_y[k]
        gate_xy[t] = (round(gx, 3), round(gy, 3))
        sg_id.append(f"gate::{t}")
        sg_kind.append("gate")
        sg_station.append(t)
        sg_railway.append("")
        sg_x.append(round(gx, 3))
        sg_y.append(round(gy, 3))
        pid = C.place_id(*C.grid_ij(gx, gy), "GL")
        sg_place.append(pid if pid in cells else "")

    for i, sid in enumerate(st_id):
        sg_id.append(f"platform::{sid}")
        sg_kind.append("platform")
        sg_station.append(st_title[i])
        sg_railway.append(st_railway[i])
        sg_x.append(st_x[i])
        sg_y.append(st_y[i])
        pid = C.place_id(*C.grid_ij(st_x[i], st_y[i]), "UG")
        sg_place.append(pid if pid in cells else "")

    for k, i in enumerate(exit_rows):
        sg_id.append(f"exit::{ent['ref'][i]}")
        sg_kind.append("exit")
        sg_station.append(ex_station_title[k])
        sg_railway.append("")
        sg_x.append(float(ent["x"][i]))
        sg_y.append(float(ent["y"][i]))
        sg_place.append(ent["place_id"][i])

    e_from: list[str] = []
    e_to: list[str] = []
    e_kind: list[str] = []
    e_geom: list[float] = []
    e_len: list[float] = []

    def add_edge(a: str, b: str, kind: str, ax: float, ay: float, bx: float, by: float) -> None:
        g = round(float(np.hypot(bx - ax, by - ay)), 3)
        e_from.append(a)
        e_to.append(b)
        e_kind.append(kind)
        e_geom.append(g)
        e_len.append(round(g * INDOOR_PATH_FACTOR, 3))

    for i, sid in enumerate(st_id):
        t = st_title[i]
        gx, gy = gate_xy[t]
        add_edge(f"platform::{sid}", f"gate::{t}", "platform_gate", st_x[i], st_y[i], gx, gy)
    for k, i in enumerate(exit_rows):
        t = ex_station_title[k]
        gx, gy = gate_xy[t]
        add_edge(
            f"gate::{t}",
            f"exit::{ent['ref'][i]}",
            "gate_exit",
            gx,
            gy,
            float(ent["x"][i]),
            float(ent["y"][i]),
        )

    factor_ok = all(
        abs(l - round(g * INDOOR_PATH_FACTOR, 3)) < 1e-9 for g, l in zip(e_geom, e_len)
    )

    # --- floorguide connections(駅直結の印)---
    fg_is_station = [bool(name and "駅" in name) for name in fg["b_name"]]

    params: dict[str, Any] = {
        "bbox": list(BBOX),
        "bbox_margin_m": BBOX_MARGIN_M,
        "indoor_path_factor": INDOOR_PATH_FACTOR,
        "exit_assignment": "name match first, else nearest ODPT station",
        "platform_node": "ODPT station representative point (per railway)",
        "gate_node": "centroid of that station's exits",
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash([*odpt_paths, ent_p, fg_p, cells_p]),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=["駅・出口", "建物内フロア・区画"],
        expedients=[
            "構内経路長 = 幾何距離 × 1.3(D-W13 の初期値)",
            "ホーム=ODPT 駅代表点・改札=出口重心(公式構内図の手入力で昇格予定)",
            "出口→駅の割当(名称一致→最近傍)",
            "ODPT 駅の抽出 = bbox+300m(ホームが範囲外に出る駅を拾う)",
            "座標を持たない駅(JR・東急・京王)は同名駅の重心へ置く",
        ],
        notes={
            "odpt_station_rows_scanned": n_stations_total,
            "stations_in_bbox": len(st_id),
            "stations_pos_src_counts": dict(sorted(Counter(st_pos_src).items())),
            "stations_with_odpt_coords": int(sum(1 for v in st_pos_src if v == "odpt")),
            "station_titles": titles,
            "exit_assign_rule_counts": dict(sorted(Counter(ex_rule).items())),
            "exit_own_grid_cell_missing": exit_own_cells_missing,
            "exit_own_grid_cells_missing_ids": sorted(
                {exit_own_cell[i] for i in exit_rows if exit_own_cell[i] not in cells}
            ),
            "exits_per_station": {t: len(exits_by_title.get(t, [])) for t in titles},
            "station_graph_nodes": len(sg_id),
            "station_graph_edges": len(e_from),
            "floorguide_station_links": int(sum(fg_is_station)),
        },
    )
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w11_stations.parquet",
            {
                "station_id": st_id,
                "title": st_title,
                "operator": st_operator,
                "railway": st_railway,
                "station_code": st_code,
                "lat": np.array(st_lat),
                "lon": np.array(st_lon),
                "x": np.array(st_x),
                "y": np.array(st_y),
                "pos_src": st_pos_src,
            },
        )
    )
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w11_station_exits.parquet",
            {
                "exit_id": [ent["ref"][i] for i in exit_rows],
                "exit_name": [ent["name"][i] for i in exit_rows],
                "station_title": ex_station_title,
                "assign_rule": ex_rule,
                "x": np.array([float(ent["x"][i]) for i in exit_rows]),
                "y": np.array([float(ent["y"][i]) for i in exit_rows]),
                "node_id": [ent["node_id"][i] for i in exit_rows],
                "place_id": [ent["place_id"][i] for i in exit_rows],
                "own_grid_place_id": [exit_own_cell[i] for i in exit_rows],
                "band": [ent["band"][i] for i in exit_rows],
            },
        )
    )
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w11_station_graph_nodes.parquet",
            {
                "sg_node_id": sg_id,
                "kind": sg_kind,
                "station_title": sg_station,
                "railway": sg_railway,
                "x": np.array(sg_x),
                "y": np.array(sg_y),
                "place_id": sg_place,
            },
        )
    )
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w11_station_graph_edges.parquet",
            {
                "from_node": e_from,
                "to_node": e_to,
                "kind": e_kind,
                "geom_dist_m": np.array(e_geom),
                "length_m": np.array(e_len),
            },
        )
    )
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w11_floorguide_connections.parquet",
            {
                "link_idx": np.asarray(fg["link_idx"], dtype=np.int32),
                "a_name": fg["a_name"],
                "a_building_id": pa.array(fg["a_building_id"], type=pa.string()),
                "b_name": fg["b_name"],
                "b_building_id": pa.array(fg["b_building_id"], type=pa.string()),
                "via": fg["via"],
                "level": np.asarray(fg["level"], dtype=np.int8),
                "is_station_link": np.array(fg_is_station, dtype=bool),
            },
        )
    )
    res.gates = [
        C.Gate("station_exits", len(exit_rows), EXPECTED_EXITS),
        C.Gate("exit_ids_unique", exit_ids_unique, EXPECTED_EXITS),
        C.Gate("exits_mapped_to_known_cell", exit_cells_known, EXPECTED_EXITS),
        C.Gate("exit_own_grid_cell_missing", exit_own_cells_missing, 0),
        C.Gate("floorguide_connections", len(fg["link_idx"]), EXPECTED_FLOORGUIDE_LINKS),
        C.Gate("indoor_length_factor_applied", bool(factor_ok), True),
        C.Gate("stations_in_bbox", len(st_id), None),
    ]
    return res
