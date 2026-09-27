"""W10 の道路名の突合(段 1c・D-1 (a)・2026-09-28)。

W1 の歩行グラフの辺(``w1_edges.parquet``・OSM v8 由来)には道路名(name/ref)が無く、
道路交通センサス R3 の箇所別基本表(``kasyo13.csv``)には座標が無い。そこで Overpass で
取り直した道路の way(``road_names_overpass_20260928.json``・``out tags geom;``=タグと座標列)を
**橋**にして、辺 → way → センサス路線 の 2 段で対応表を作る。

1. **辺 → way**(:func:`match_edges_to_ways`): W1 の辺は OSM の way id を持たない(``u_id``/``v_id``
   は node id)し、Overpass 応答も node id を持たない(``out tags geom;``)ので、way id の一致は
   使えない。**幾何**で代える: 辺の折れ線の**弧長の中点**から、全 way の折れ線までの最短距離を
   取り、**最も近い way** を「その辺自身の way」とみなす(距離 ≤ :data:`MATCH_BUFFER_M`=8 m=
   D-W9 の街路格子のバッファと同値)。名前つきの way だけから探すと、名前の無い自分の way の
   隣を走る幹線の名前を拾う(実測: 住宅地の辺 34 本が国道・主要道の交通量を受ける)ので、
   **名前の有無に関わらず最も近い way** を採り、その way に name/ref があれば「名前が付いた」とする。
2. **way → センサス路線**(:func:`census_key`・:func:`sections_for_key`)。正規化の規則:
   - (a) ``field.common.normalize_jp``(NFKC=全角英数→半角・漢数字→算用数字・空白除去)。
   - (b) name/official_name に「区道」を含む → **区道**(センサスの対象外=突合しない)。
   - (c) name/official_name に「国道N号」 → **一般国道 N**(センサス道路種別 3・路線番号 N)。
     ``highway=trunk`` で ref が数字なら同じく一般国道 ref。
   - (d) ``highway=motorway`` → **高速**(W1 に motorway の辺は無い=数えるだけ)。
   - (e) ref の数字(``;``/``,`` 区切りは先頭から)→ **都道 N**(センサス道路種別 4=主要地方道・
     6=一般都道府県道 の路線番号 N。最初に見つかった番号)。
   - (f) ref が無く名前だけ → センサスの路線名(正規化)と完全一致すればその路線、無ければ
     「番号なし」(井ノ頭通り・神宮通りのような通称はセンサスの路線名と一致しない)。
   センサス区間の集合は、その路線の区間を市区町村の**優先順** :data:`CENSUS_WARDS` で探し、
   最初に区間がある区のものだけを採る(渋谷区 → bbox に接する目黒区・港区・世田谷区・新宿区 →
   都内全区間)。例: 淡島通り=都道 423 渋谷経堂線は渋谷区に区間が無く、目黒区の 2 区間
   (渋谷側の起点から 1・2 番目)を採る=較正点 No.61 の評価(点の区で絞る)と同じ区間になる。
3. **交通量**: 路線の使える区間の**列ごとの下側中央値**(``w10_noise.median_section``=較正点と
   同じ規則)を、その路線に突合した辺すべてに当てる。

**絞り込み(段 1c′・:func:`match_edges_to_ways` の ``require_named_same_class``/``require_same_band``)**
- Q7(階級): 候補の way を「**名前か ref があり**、way の ``highway`` の階級(:data:`CLASS_TIER`・
  trunk≒primary)が辺の ``klass`` の階級と同じもの」に限る。音源でない klass(歩道など)は候補が
  無い=対応づけない。
- Q9(層): 候補の way を「way の層(:func:`way_band`=``layer`` があればその値・無ければ
  ``tunnel``/``bridge``)が辺の ``band``(UG/GL/DECK)と同じもの」に限る。
どちらも**候補の制限**(食い違う way には対応づけない)で、その中の最も近い way(≤ 8 m)を採る。

expedient(すべて感度試験対象・notes に件数)
- 辺の中点 1 点で way を決める(辺の全長を見ない)。層(UG/GL/DECK)を見ない。
- 8 m の閾値(D-W9 のバッファと同値=新しい定数を作らない)。
- 路線内の区間の位置決めをしない(センサスに座標が無い。起終点の交差路線名で区間を並べれば
  辺ごとに区間を選べるが、本段ではしない)=路線の区間の中央値を路線全体に当てる。
- 区道・番号なしの通称・名前の無い way は従来の klass 既定表へ落ちる。
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from ..geo import common as G
from . import common as C

__all__ = [
    "ROAD_NAMES",
    "MATCH_BUFFER_M",
    "CENSUS_WARDS",
    "KEY_KINDS",
    "CLASS_TIER",
    "way_band",
    "edge_midpoints",
    "way_segments",
    "nearest_way",
    "census_key",
    "sections_for_key",
    "EdgeWayMatch",
    "match_edges_to_ways",
]

#: 道路名の生応答(2026-09-28 取得・``out tags geom;``・1,328 way)。
ROAD_NAMES: tuple[str, ...] = ("realworld", "osm", "road_names_overpass_20260928.json")
#: 辺の中点から way の折れ線までの距離の上限[m](D-W9 の街路格子のバッファと同値)。
MATCH_BUFFER_M: float = 8.0
#: センサス区間を探す市区町村の優先順(渋谷区 → bbox に接する区)。どこにも無ければ都内全区間。
#: **expedient**(区の並びは bbox に接する順の自前判断)。
CENSUS_WARDS: tuple[str, ...] = ("13113", "13110", "13103", "13112", "13104")
#: :func:`census_key` の種別(報告の並び順)。
KEY_KINDS: tuple[str, ...] = (
    "national", "prefectural", "named_route", "ward", "motorway", "unnumbered", "unnamed",
)

_NATIONAL = re.compile(r"国道(\d+)号")

#: 段 1c′ Q7: 辺の ``klass`` / way の ``highway`` → 階級。trunk と primary は同じ階級(W1 に trunk の
#: 辺が無い=国道の本線は primary で入っている)。表に無い値(footway 等)は階級なし=対応づけない。
CLASS_TIER: dict[str, str] = {
    "motorway": "motorway",
    "trunk": "primary",
    "primary": "primary",
    "secondary": "secondary",
    "tertiary": "tertiary",
    "unclassified": "minor",
    "residential": "minor",
    "living_street": "minor",
    "service": "service",
    "pedestrian": "pedestrian",
}


def way_band(tags: Mapping[str, Any]) -> str:
    """段 1c′ Q9: way の層 → ``UG``/``GL``/``DECK``(W1 の辺の ``band`` と同じ語)。

    ``layer`` があれば W1 と同じ規則(``geo.common.band_of_layer``・|layer|>2 は ±2 に丸める)。
    無ければ ``tunnel``(``building_passage`` は地上の通り抜け=GL)→ UG、``bridge`` → DECK、他は GL。

    Example:
        >>> way_band({"layer": "1", "bridge": "yes"}), way_band({"tunnel": "yes"}), way_band({})
        ('DECK', 'UG', 'GL')
        >>> way_band({"tunnel": "building_passage"}), way_band({"layer": "-3"})
        ('GL', 'UG')
    """
    layer = tags.get("layer")
    if layer is not None:
        try:
            lay = int(float(str(layer).split(";")[0]))
        except ValueError:
            lay = 0
        return G.band_of_layer(max(-2, min(2, lay)))
    tunnel = str(tags.get("tunnel") or "no")
    if tunnel not in ("no", "building_passage"):
        return "UG"
    if str(tags.get("bridge") or "no") != "no":
        return "DECK"
    return "GL"


def edge_midpoints(
    geom_start: Sequence[int], geom_count: Sequence[int], coords: np.ndarray
) -> np.ndarray:
    """辺の折れ線の**弧長の中点** ``(n, 2)``(世界ローカル m)。

    逐次ループ宣言(P4): 辺の数ぶん 1 本(構築時 1 回)。
    """
    n = len(geom_start)
    out = np.zeros((n, 2), dtype=np.float64)
    for i in range(n):
        s, c = int(geom_start[i]), int(geom_count[i])
        pts = np.asarray(coords[s : s + c, :2], dtype=np.float64)
        if pts.shape[0] == 0:
            out[i] = np.nan
            continue
        if pts.shape[0] == 1:
            out[i] = pts[0]
            continue
        seg = np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1]))
        half = float(seg.sum()) / 2.0
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        k = int(np.searchsorted(cum, half, side="right") - 1)
        k = min(max(k, 0), seg.size - 1)
        t = (half - cum[k]) / seg[k] if seg[k] > 0 else 0.0
        out[i] = pts[k] + t * (pts[k + 1] - pts[k])
    return out


def way_segments(elements: Iterable[Mapping[str, Any]]) -> tuple[np.ndarray, ...]:
    """Overpass の way(``geometry`` = ``[{lat, lon}, …]``)→ 線分の配列 ``(ax, ay, bx, by, owner)``。"""
    ax: list[float] = []
    ay: list[float] = []
    bx: list[float] = []
    by: list[float] = []
    owner: list[int] = []
    for wi, w in enumerate(elements):
        xy = [G.latlon_to_local(float(p["lat"]), float(p["lon"])) for p in (w.get("geometry") or []) if p]
        for a, b in zip(xy[:-1], xy[1:]):
            ax.append(a[0])
            ay.append(a[1])
            bx.append(b[0])
            by.append(b[1])
            owner.append(wi)
    return (
        np.asarray(ax, dtype=np.float64),
        np.asarray(ay, dtype=np.float64),
        np.asarray(bx, dtype=np.float64),
        np.asarray(by, dtype=np.float64),
        np.asarray(owner, dtype=np.int64),
    )


def nearest_way(points: np.ndarray, segs: tuple[np.ndarray, ...], chunk: int = 256) -> tuple[np.ndarray, np.ndarray]:
    """各点に最も近い way の索引と距離[m](同距離は線分の並びが先の way=決定論)。

    Note:
        逐次ループ宣言(P4): 点を ``chunk`` 件ずつ(構築時 1 回・点 × 線分のベクトル演算)。
    """
    ax, ay, bx, by, owner = segs
    n = int(points.shape[0])
    best_w = np.full(n, -1, dtype=np.int64)
    best_d = np.full(n, np.inf, dtype=np.float64)
    if ax.size == 0 or n == 0:
        return best_w, best_d
    dx = bx - ax
    dy = by - ay
    den = dx * dx + dy * dy
    den = np.where(den <= 0.0, 1.0, den)
    for lo in range(0, n, chunk):
        qx = points[lo : lo + chunk, 0][:, None]
        qy = points[lo : lo + chunk, 1][:, None]
        t = np.clip(((qx - ax) * dx + (qy - ay) * dy) / den, 0.0, 1.0)
        d = np.hypot(qx - (ax + t * dx), qy - (ay + t * dy))
        j = np.argmin(d, axis=1)
        rows = np.arange(d.shape[0])
        best_d[lo : lo + chunk] = d[rows, j]
        best_w[lo : lo + chunk] = owner[j]
    return best_w, best_d


def census_key(tags: Mapping[str, Any]) -> tuple[str, tuple[str, ...]]:
    """way のタグ → ``(種別, 路線番号の候補)``。種別は :data:`KEY_KINDS` のどれか。

    Example:
        >>> census_key({"highway": "trunk", "ref": "246", "official_name": "一般国道246号"})
        ('national', ('246',))
        >>> census_key({"highway": "primary", "ref": "305", "name": "明治通り"})
        ('prefectural', ('305',))
        >>> census_key({"highway": "tertiary", "ref": "870", "name": "渋谷区特別区道870号線"})
        ('ward', ())
        >>> census_key({"highway": "tertiary", "name": "井ノ頭通り"})
        ('unnumbered', ())
    """
    name = C.normalize_jp(str(tags.get("name") or ""))
    official = C.normalize_jp(str(tags.get("official_name") or ""))
    ref = C.normalize_jp(str(tags.get("ref") or ""))
    if not (name or official or ref):
        return "unnamed", ()
    if "区道" in name or "区道" in official:
        return "ward", ()
    m = _NATIONAL.search(official) or _NATIONAL.search(name)
    if m:
        return "national", (m.group(1),)
    refs = tuple(r for r in re.split(r"[;,]", ref) if r.isdigit())
    if tags.get("highway") == "motorway":
        return "motorway", refs
    if tags.get("highway") == "trunk" and refs:
        return "national", refs[:1]
    if refs:
        return "prefectural", refs
    return "unnumbered", ()


#: 種別 → センサスの道路種別(``道路種別`` 列の値)。
_KIND_TO_ROAD_KIND: dict[str, tuple[str, ...]] = {
    "national": ("3",),
    "prefectural": ("4", "6"),
}


def sections_for_key(
    sections: Sequence[Mapping[str, Any]],
    kind: str,
    numbers: Sequence[str],
    name: str = "",
    wards: Sequence[str] = CENSUS_WARDS,
) -> list[Mapping[str, Any]]:
    """種別+路線番号 → センサス区間(``wards`` の順に最初に区間がある区のもの・無ければ全区間)。

    ``kind="unnumbered"`` は路線名(正規化)の完全一致だけを見る(規則 (f))。
    """
    hits: list[Mapping[str, Any]] = []
    if kind in _KIND_TO_ROAD_KIND:
        kinds = set(_KIND_TO_ROAD_KIND[kind])
        for num in numbers:
            hits = [s for s in sections if s["road_kind"] in kinds and s["route_no"] == str(num)]
            if hits:
                break
    elif kind == "unnumbered" and name:
        key = C.normalize_jp(name)
        hits = [s for s in sections if s["route_key"] == key]
    for ward in wards:
        in_ward = [s for s in hits if s["city"] == ward]
        if in_ward:
            return in_ward
    return hits


@dataclass
class EdgeWayMatch:
    """辺 → way → センサス路線 の突合の結果(辺の並び=``w1_edges`` の行順)。"""

    way_index: np.ndarray
    distance_m: np.ndarray
    #: 辺ごとの種別(:data:`KEY_KINDS`・way が 8 m 以内に無い辺は ``"no_way"``)。
    key_kind: list[str]
    #: 辺ごとのセンサス路線ラベル(``"<道路種別>:<路線番号>:<路線名>"``・無ければ ``""``)。
    route: list[str]
    #: 路線ラベル → その路線のセンサス区間(使える区間に限らない)。
    route_sections: dict[str, list[Mapping[str, Any]]] = field(default_factory=dict)
    #: 辺ごとの way のタグ(name/ref/highway/official_name だけ・way が無ければ空)。
    way_tags: list[dict[str, str]] = field(default_factory=list)


def _nearest_restricted(
    midpoints: np.ndarray,
    segs: tuple[np.ndarray, ...],
    ways: Sequence[Mapping[str, Any]],
    edge_klass: Sequence[str] | None,
    edge_band: Sequence[str] | None,
    require_named_same_class: bool,
    require_same_band: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """候補の way を辺ごとに制限して最も近い way を探す(段 1c′)。辺は (階級, 層) の組で束ねる。

    逐次ループ宣言(P4): 組の数ぶん(≤ 階級 10 × 層 3・構築時 1 回)。
    """
    n = int(midpoints.shape[0])
    if require_named_same_class and edge_klass is None:
        raise ValueError("require_named_same_class には edge_klass が要る")
    if require_same_band and edge_band is None:
        raise ValueError("require_same_band には edge_band が要る")
    w_named = np.array(
        [bool((w.get("tags") or {}).get("name") or (w.get("tags") or {}).get("ref")) for w in ways],
        dtype=bool,
    )
    w_tier = np.array([CLASS_TIER.get(str((w.get("tags") or {}).get("highway") or ""), "") for w in ways])
    w_band = np.array([way_band(w.get("tags") or {}) for w in ways])
    e_tier = (
        np.array([CLASS_TIER.get(str(k), "") for k in edge_klass]) if require_named_same_class
        else np.full(n, "*")
    )
    e_band = np.array([str(b) for b in edge_band]) if require_same_band else np.full(n, "*")
    best_w = np.full(n, -1, dtype=np.int64)
    best_d = np.full(n, np.inf, dtype=np.float64)
    ax, ay, bx, by, owner = segs
    for tier, band in sorted(set(zip(e_tier.tolist(), e_band.tolist()))):
        rows = np.flatnonzero((e_tier == tier) & (e_band == band))
        ok = np.ones(len(ways), dtype=bool)
        if require_named_same_class:
            ok &= w_named & (w_tier == tier) & (tier != "")
        if require_same_band:
            ok &= w_band == band
        keep = ok[owner] if owner.size else np.zeros(0, dtype=bool)
        if not keep.any():
            continue
        sub = (ax[keep], ay[keep], bx[keep], by[keep], owner[keep])
        wi, di = nearest_way(midpoints[rows], sub)
        best_w[rows] = wi
        best_d[rows] = di
    return best_w, best_d


def match_edges_to_ways(
    midpoints: np.ndarray,
    ways: Sequence[Mapping[str, Any]],
    sections: Sequence[Mapping[str, Any]],
    buffer_m: float = MATCH_BUFFER_M,
    *,
    edge_klass: Sequence[str] | None = None,
    edge_band: Sequence[str] | None = None,
    require_named_same_class: bool = False,
    require_same_band: bool = False,
) -> EdgeWayMatch:
    """辺の中点 → 最も近い way(≤ ``buffer_m``)→ センサス路線。

    既定(絞り込みなし)は**名前の有無に関わらず最も近い way**。``require_named_same_class``(Q7)・
    ``require_same_band``(Q9)は候補の way を制限する(段 1c′・モジュール docstring)。
    """
    segs = way_segments(ways)
    if require_named_same_class or require_same_band:
        widx, dist = _nearest_restricted(
            midpoints, segs, ways, edge_klass, edge_band,
            require_named_same_class, require_same_band,
        )
    else:
        widx, dist = nearest_way(midpoints, segs)
    kinds: list[str] = []
    routes: list[str] = []
    tags_out: list[dict[str, str]] = []
    route_sections: dict[str, list[Mapping[str, Any]]] = {}
    cache: dict[int, tuple[str, str]] = {}
    for w, d in zip(widx.tolist(), dist.tolist()):  # 逐次: 辺の数ぶん(構築時 1 回)
        if w < 0 or not (d <= buffer_m):
            kinds.append("no_way")
            routes.append("")
            tags_out.append({})
            continue
        tags = ways[w].get("tags") or {}
        tags_out.append(
            {k: str(tags[k]) for k in ("highway", "name", "ref", "official_name") if tags.get(k)}
        )
        if w not in cache:
            kind, numbers = census_key(tags)
            label = ""
            hits = sections_for_key(sections, kind, numbers, str(tags.get("name") or ""))
            if hits:
                h0 = hits[0]
                label = f"{h0['road_kind']}:{h0['route_no']}:{h0['route_name']}"
                route_sections.setdefault(label, list(hits))
            cache[w] = (kind, label)
        kind, label = cache[w]
        kinds.append(kind)
        routes.append(label)
    return EdgeWayMatch(
        way_index=widx,
        distance_m=dist,
        key_kind=kinds,
        route=routes,
        route_sections=route_sections,
        way_tags=tags_out,
    )


def match_report(
    m: EdgeWayMatch, klass: Sequence[str], road_klasses: Sequence[str]
) -> dict[str, Any]:
    """klass 別の写像率・名寄せ率・路線ごとの辺数(W10 の notes 用・決定論)。"""
    by_klass: dict[str, dict[str, int]] = {}
    for k, kind, route in zip(klass, m.key_kind, m.route):
        row = by_klass.setdefault(
            str(k), {"edges": 0, "own_way_le_8m": 0, "named": 0, "census_matched": 0}
        )
        row["edges"] += 1
        if kind != "no_way":
            row["own_way_le_8m"] += 1
        if kind not in ("no_way", "unnamed"):
            row["named"] += 1
        if route:
            row["census_matched"] += 1
    road = set(road_klasses)
    road_rows = [by_klass[k] for k in by_klass if k in road]
    tot = {key: sum(r[key] for r in road_rows) for key in ("edges", "own_way_le_8m", "named", "census_matched")}
    kind_counts = Counter(kind for k, kind in zip(klass, m.key_kind) if k in road)
    route_counts = Counter(route for k, route in zip(klass, m.route) if k in road and route)
    unmatched_names = Counter(
        (t.get("ref", ""), t.get("name", ""))
        for k, kind, route, t in zip(klass, m.key_kind, m.route, m.way_tags)
        if k in road and not route and kind not in ("no_way", "unnamed")
    )
    agree = sum(
        1
        for k, t in zip(klass, m.way_tags)
        if k in road and t and (t.get("highway") == k or (k == "primary" and t.get("highway") == "trunk"))
    )
    with_way = sum(1 for k, t in zip(klass, m.way_tags) if k in road and t)
    return {
        "by_klass": dict(sorted(by_klass.items())),
        "road_edges": tot,
        "road_mapping_rate_own_way": round(tot["own_way_le_8m"] / tot["edges"], 4) if tot["edges"] else 0.0,
        "road_named_rate": round(tot["named"] / tot["edges"], 4) if tot["edges"] else 0.0,
        "road_census_match_rate_of_named": (
            round(tot["census_matched"] / tot["named"], 4) if tot["named"] else 0.0
        ),
        "road_census_match_rate_of_all": (
            round(tot["census_matched"] / tot["edges"], 4) if tot["edges"] else 0.0
        ),
        "road_key_kind_counts": {k: int(kind_counts.get(k, 0)) for k in (*KEY_KINDS, "no_way")},
        "road_edges_by_route": dict(sorted(route_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "road_klass_highway_agreement": {"agree": agree, "with_way": with_way},
        "road_unmatched_named_top": [
            {"ref": r, "name": n, "edges": c} for (r, n), c in unmatched_names.most_common(20)
        ],
    }
