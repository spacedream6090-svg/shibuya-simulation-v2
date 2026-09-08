"""W1 歩行グラフ(§1 W1・D-W3・D-W4)。

入力: OSM v8(nodes 3,499 / edges 4,944)+ floorguide connections 22。
出力:
- ``w1_nodes.parquet``     ノード(層・バンド・次数・pendant 判定)
- ``w1_edges.parquet``     エッジ(層・バンド・長さ・層間リンク判定)
- ``w1_edge_geometry.npz`` エッジ折れ線(coords, offsets)= W2 の街区面抽出が使う
- ``w1_floorguide_links.parquet`` floorguide connections 22 本(**別レイヤ**・mechanism)

規則(D-W3)
- エッジ層 = OSM ``layer`` 素値(未タグは 0)。
- ノード層 = 接続エッジ層の多数決(同数なら 0 優先 → |layer| 最小)。
- バンド UG={-2,-1} / GL={0} / DECK={+1,+2}。
- 層間リンク = ``klass ∈ {steps, elevator, corridor}`` かつ両端ノードのバンドが異なるエッジ。
- 縮約しない(D-W4)。pendant 除去は**ゲート計算のみ**で、資産は全ノード・全エッジを保持する。

expedient
- OSM ``layer`` は描画順タグであって物理階層ではない(D-W3 で宣言済み)。
- pendant 連鎖の定義 = 「次数1のノードとその唯一の接続エッジを、次数1が無くなるまで反復除去」。
  行き止まりの枝は連結性に寄与しないので、連結成分ゲートはこの中核グラフで測る。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa

from . import common as C

STAGE = "W1"
STAGE_VERSION = "1.0.0"

INPUT_FILES: tuple[tuple[str, ...], ...] = (
    ("realworld", "osm", "shibuya_osm_wide_v8.json"),
    ("realworld", "osm", "floorguide_shibuya.json"),
)

#: 層間リンクになりうる klass(D-W3)。
INTERBAND_KLASS: frozenset[str] = frozenset({"steps", "elevator", "corridor"})

#: 総延長ゲートの期待値 [m](§1 W1)。
EXPECTED_TOTAL_LENGTH_M = 186741.0


def prune_pendants(n_nodes: int, edges: list[tuple[int, int]]) -> tuple[set[int], set[int]]:
    """次数1のノードとその接続エッジを反復除去する(ゲート用の中核グラフ)。

    Returns:
        (残るノード集合, 残るエッジ添字集合)
    """
    alive_e = set(range(len(edges)))
    inc: dict[int, set[int]] = defaultdict(set)
    for i, (u, v) in enumerate(edges):
        inc[u].add(i)
        inc[v].add(i)
    deg = {n: len(inc[n]) for n in range(n_nodes)}
    stack = [n for n in range(n_nodes) if deg[n] == 1]
    dead_n: set[int] = set()
    while stack:
        n = stack.pop()
        if deg.get(n, 0) != 1 or n in dead_n:
            continue
        (ei,) = tuple(inc[n])
        u, v = edges[ei]
        other = v if u == n else u
        dead_n.add(n)
        alive_e.discard(ei)
        inc[n].discard(ei)
        inc[other].discard(ei)
        deg[n] = 0
        deg[other] -= 1
        if deg[other] == 1:
            stack.append(other)
    alive_n = {n for n in range(n_nodes) if n not in dead_n and deg.get(n, 0) > 0}
    return alive_n, alive_e


def count_components(nodes: set[int], edges: list[tuple[int, int]], alive_e: set[int]) -> int:
    """与えられたノード集合・エッジ部分集合の連結成分数(孤立ノードも 1 成分)。"""
    parent = {n: n for n in nodes}

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i in alive_e:
        u, v = edges[i]
        if u not in parent or v not in parent:
            continue
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
    return len({find(n) for n in nodes})


def _match_floorguide(fg_buildings: list[dict], osm_buildings: list[dict]) -> dict[str, str | None]:
    """floorguide の ``match`` 別名リスト → OSM building id(完全一致 → 部分一致)。"""
    by_name: dict[str, str] = {}
    for b in osm_buildings:
        nm = (b.get("name") or "").strip()
        if nm and nm not in by_name:
            by_name[nm] = b["id"]
    out: dict[str, str | None] = {}
    for fb in fg_buildings:
        aliases = fb["match"]
        hit: str | None = None
        for alias in aliases:
            if alias in by_name:
                hit = by_name[alias]
                break
        if hit is None:
            for alias in aliases:
                cands = sorted(bid for nm, bid in by_name.items() if alias and alias in nm)
                if cands:
                    hit = cands[0]
                    break
        out[aliases[0]] = hit
    return out


def run(ctx: C.Ctx) -> C.StageResult:
    paths = [ctx.path(*parts) for parts in INPUT_FILES]
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"W1 入力が無い: {p}")
    osm = C.load_json(paths[0])
    fg = C.load_json(paths[1])

    nodes = osm["nodes"]
    edges = osm["edges"]
    node_idx = {n["id"]: i for i, n in enumerate(nodes)}

    # --- ノード層 = 接続エッジ層の多数決 ---
    incident: dict[int, list[int]] = defaultdict(list)
    for e in edges:
        lay = int(e.get("layer") or 0)
        incident[node_idx[e["u"]]].append(lay)
        incident[node_idx[e["v"]]].append(lay)
    node_layer = np.array(
        [C.node_layer_from_incident(incident[i]) for i in range(len(nodes))], dtype=np.int8
    )
    node_band = [C.band_of_layer(int(lay)) for lay in node_layer]
    degree = np.array([len(incident[i]) for i in range(len(nodes))], dtype=np.int16)

    # ノード側 layer タグは検証のみ(D-W3)
    tag_agree = 0
    tag_total = 0
    for i, n in enumerate(nodes):
        if "layer" in n:
            tag_total += 1
            tag_agree += int(int(n["layer"]) == int(node_layer[i]))

    # --- pendant 除去(ゲート用)---
    uv = [(node_idx[e["u"]], node_idx[e["v"]]) for e in edges]
    alive_n, alive_e = prune_pendants(len(nodes), uv)
    comp_full = count_components(set(range(len(nodes))), uv, set(range(len(uv))))
    comp_core = count_components(alive_n, uv, alive_e) if alive_n else 0

    # --- エッジ表 ---
    coords: list[tuple[float, float]] = []
    offsets = np.zeros(len(edges) + 1, dtype=np.int32)
    e_klass: list[str] = []
    e_len: list[float] = []
    e_layer: list[int] = []
    e_band: list[str] = []
    e_bu: list[str] = []
    e_bv: list[str] = []
    e_inter: list[bool] = []
    for i, e in enumerate(edges):
        g = e["geometry"]
        coords.extend((float(p[0]), float(p[1])) for p in g)
        offsets[i + 1] = len(coords)
        lay = int(e.get("layer") or 0)
        bu = node_band[node_idx[e["u"]]]
        bv = node_band[node_idx[e["v"]]]
        e_klass.append(e["klass"])
        e_len.append(float(e["length"]))
        e_layer.append(lay)
        e_band.append(C.band_of_layer(lay))
        e_bu.append(bu)
        e_bv.append(bv)
        e_inter.append(bool(e["klass"] in INTERBAND_KLASS and bu != bv))

    total_len = round(float(sum(e_len)), 3)
    steps_cross = sum(
        1 for i, e in enumerate(edges) if e["klass"] == "steps" and e_bu[i] != e_bv[i]
    )
    band_diff_all = sum(1 for i in range(len(edges)) if e_bu[i] != e_bv[i])
    interband = int(sum(e_inter))

    # --- floorguide connections(別レイヤ)---
    fgb = fg["buildings"]
    name_to_bid = _match_floorguide(fgb, osm["buildings"])
    link_a: list[str] = []
    link_a_bid: list[str | None] = []
    link_b: list[str] = []
    link_b_bid: list[str | None] = []
    link_via: list[str] = []
    link_level: list[int] = []
    for fb in fgb:
        a_name = fb["match"][0]
        for con in fb.get("connections", []):
            to_name = con["to_building"]
            link_a.append(a_name)
            link_a_bid.append(name_to_bid.get(a_name))
            link_b.append(to_name)
            b_hit = name_to_bid.get(to_name)
            if b_hit is None:
                for fb2 in fgb:
                    if to_name in fb2["match"]:
                        b_hit = name_to_bid.get(fb2["match"][0])
                        break
            link_b_bid.append(b_hit)
            link_via.append(con["via"])
            link_level.append(int(con["level"]))

    params: dict[str, Any] = {
        "interband_klass": sorted(INTERBAND_KLASS),
        "band_of_layer": {str(k): v for k, v in C.BAND_OF_LAYER.items()},
        "contraction": "none",
        "pendant_rule": "iteratively drop degree-1 nodes and their single incident edge",
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash(paths),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=["街路(歩行グラフ)", "地下街・デッキ・歩道橋"],
        expedients=[
            "OSM layer→物理層バンドの写像(描画順タグ・D-W3)",
            "pendant 連鎖の定義(次数1の反復除去)= 連結成分ゲートの中核グラフ",
            "floorguide の建物名→OSM building id 照合(完全一致→部分一致)",
        ],
        notes={
            "edge_klass_counts": dict(sorted(Counter(e_klass).items())),
            "edge_layer_counts": {str(k): v for k, v in sorted(Counter(e_layer).items())},
            "node_band_counts": dict(sorted(Counter(node_band).items())),
            "pendant_nodes_removed": len(nodes) - len(alive_n),
            "pendant_edges_removed": len(uv) - len(alive_e),
            "node_layer_tag_total": tag_total,
            "node_layer_tag_agree": tag_agree,
            "band_diff_edges_all_klass": band_diff_all,
            "floorguide_buildings_matched": sum(1 for v in name_to_bid.values() if v),
            "floorguide_buildings_total": len(name_to_bid),
            "total_edge_length_diff_m": round(total_len - EXPECTED_TOTAL_LENGTH_M, 3),
        },
    )

    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w1_nodes.parquet",
            {
                "node_idx": np.arange(len(nodes), dtype=np.int32),
                "node_id": [n["id"] for n in nodes],
                "x": np.array([float(n["x"]) for n in nodes]),
                "y": np.array([float(n["y"]) for n in nodes]),
                "layer": node_layer,
                "band": node_band,
                "degree": degree,
                "pendant": np.array([i not in alive_n for i in range(len(nodes))], dtype=bool),
                "osm_layer_tag": pa.array(
                    [int(n["layer"]) if "layer" in n else None for n in nodes], type=pa.int8()
                ),
                "name": [n.get("name") or "" for n in nodes],
                "is_gateway": np.array([bool(n.get("gateway")) for n in nodes], dtype=bool),
                "is_poi": np.array([bool(n.get("poi")) for n in nodes], dtype=bool),
            },
        )
    )
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w1_edges.parquet",
            {
                "edge_idx": np.arange(len(edges), dtype=np.int32),
                "u_idx": np.array([a for a, _ in uv], dtype=np.int32),
                "v_idx": np.array([b for _, b in uv], dtype=np.int32),
                "u_id": [e["u"] for e in edges],
                "v_id": [e["v"] for e in edges],
                "klass": e_klass,
                "length_m": np.array(e_len),
                "layer": np.array(e_layer, dtype=np.int8),
                "band": e_band,
                "band_u": e_bu,
                "band_v": e_bv,
                "interband": np.array(e_inter, dtype=bool),
                "geom_start": offsets[:-1].copy(),
                "geom_count": np.diff(offsets).astype(np.int32),
            },
        )
    )
    res.outputs.append(
        C.write_npz(
            ctx.out,
            "w1_edge_geometry.npz",
            coords=np.asarray(coords, dtype=np.float64),
            offsets=offsets,
        )
    )
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w1_floorguide_links.parquet",
            {
                "link_idx": np.arange(len(link_a), dtype=np.int32),
                "a_name": link_a,
                "a_building_id": pa.array(link_a_bid, type=pa.string()),
                "b_name": link_b,
                "b_building_id": pa.array(link_b_bid, type=pa.string()),
                "via": link_via,
                "level": np.array(link_level, dtype=np.int8),
            },
        )
    )

    res.gates = [
        C.Gate("n_nodes", len(nodes), 3499),
        C.Gate("n_edges", len(edges), 4944),
        C.Gate("components_full_graph", comp_full, 1),
        C.Gate("components_after_pendant_prune", comp_core, 1),
        C.Gate("total_edge_length_m", total_len, EXPECTED_TOTAL_LENGTH_M),
        C.Gate("steps_edges_crossing_bands", steps_cross, None),
        C.Gate("interband_links", interband, None),
        C.Gate("floorguide_connections", len(link_a), 22),
    ]
    return res
