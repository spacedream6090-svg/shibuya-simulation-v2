"""tools/build_geo/walkable_area.py — C9c-1 歩行可能面積の実測化(セル別 ``walkable_m2``)。

正典
- 決定: ``docs/design/v2-c9-geometry-agenda.md`` §5(C9c の実装順)・§6「C9c の範囲(G8 (b))」
  = 「歩道部の面積(PLATEAU tran 歩道部 897,556 m²)で街路点の面積を置換」。
- 手順: ``docs/research/v2-c9-geometry-capacity-research.md`` **§2-1 S1〜S7**(入力→計算→
  出力列・ゲート 3 つ)。既定幅員の法的根拠は同 §1-1 a1〜a3(道路構造令 第11条3項 /
  第10条の2 2項 / 第5条4〜5項)。
- 置換前の式: ``perception/renderer.py`` の ``max(街路点数 × 6.25 m², 1,500 m²)``
  (= 6.25 は 2.5 m 格子の目の面積・実測ではない=同 §1-1 a12)。

**この道具は世界資産を上書きしない**。新しい parquet(既定 ``c9c_walkable_area.parquet``)と
ヘッダ JSON(``c9c_walkable_area.header.json``)を書くだけで、既存の W* 資産には触らない。

入力(手元のみ・Web からは取らない)
- ``--source gml``(**既定**): ``data/realworld/plateau_2025/13113_shibuya-ku_pref_2025_citygml_1_op/
  udx/tran/*.gml``(30 ファイル・184 MB・ライセンス台帳 L23)。**S1 の原文どおり**、
  ``tran:TrafficArea`` / ``tran:AuxiliaryTrafficArea`` を走査し、**1 地物(``gml:id``)につき
  LOD3 → LOD2 → LOD1 の順で最初に在る幾何 1 つ**だけを採る(= 二重計上しない)。
  ``gml:posList`` は **(緯度 経度 高さ)** 順・``gml:exterior`` 加算 / ``gml:interior`` 減算の
  shoelace。区全域が対象(clip 無し)。
- ``--source npz``: 解析済みの ``data/plateau/tran_lod3.npz``(**LOD3 かつ clip_rect
  2.882 km² 内だけ**の部分集合・同じ三角形が 2〜6 回入っている)。GML が無い環境用に残す。
- 共通: ``data/world/v2/world_crs.json``(m/deg)・``w2_cells.parquet``(セル 520)・
  ``w1_edges.parquet`` + ``w1_edge_geometry.npz``(OSM 線)・``w10_street_points.parquet``
  (現行式の検算=S7 (i))。

**npz についての確定事実**(``--source npz`` を選んだときだけ効く)
- ``poly_offsets`` は全て 3 頂点刻み=三角形分割済み(79,673 枚)。``poly_class`` uint8 =
  ``0:walk / 1:road / 2:island``。``poly_code`` uint16 = function コードで、**実在するのは
  2000 / 1000 / 1020 / 3000 の 4 つだけ**。
- **同じ三角形が 2〜6 回入っている**(頂点の量子化整数が完全一致・z も一致)。歩道部は
  47,023 枚のうち一意 18,794 枚(244,131 → 103,103 m²)。``tran_lod3.json`` の
  ``area_m2_by_class`` も重複込み。``--dedup xy``(既定)で畳む。

expedient(この道具の分・登録簿へ)
1. PLATEAU の面は **band=GL のセルにだけ**入れる(S6: DECK は ``w1_edges`` の DECK 線・
   UG は W11/ubld 依存で面が無い。``udx/ubld/`` は手元に在るが本実装の範囲外)。
2. S7 (i) の合否帯は ``[0.5, 2.0]``(答申の再計算 1.125 を含む帯)。答申は帯を書いていない。
3. S7 (ii) は**中央値**が 0.05〜0.45 に入るかで判定し、帯の外に出たセルの割合は報告のみ。
4. ``steps`` 1.5 m・``elevator`` 0.0 m は答申 S4 の指定そのままだが**法的根拠なし**。
5. OSM 線のセル配分は折れ線をセル境界で切って長さ按分し、**その比で ``length_m``
   (W1 の街路長)を割る**(折れ線長と ``length_m`` は一致しない=W1 の実測比 p50 1.0007)。
6. ``width_rule`` 列はセル内で**最も長さを稼いだ klass** の規則名 1 つ(全 klass の内訳は
   ヘッダの ``notes.osm_length_by_klass`` に出す)。
7. **被覆の判定は被覆率**(``--covered-min-frac`` 既定 0.5): PLATEAU の道路面(歩道部+
   車道部+交差部)が、そのセルの OSM 規則による道路面推定の何割あるか。半端なセルは
   分子が物理的に不完全なので ``osm`` へ倒す(``mixed`` にしない)。0.5 という線は自前。
8. ``ROAD_SURFACE_WIDTH_M``(被覆率の分母)の車線数を**上下 1 車線ずつの 2 車線**と置いた
   (W1 は ``lanes`` タグを保持していない=答申 §1-1 a13)。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Final, Iterator

import numpy as np
import pyarrow as pa

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from shibuya.build.geo.common import (  # noqa: E402
    CELL_M,
    Gate,
    StageResult,
    input_hash,
    param_hash,
    sha256_file,
    write_header,
    write_parquet,
)

__all__ = [
    "STAGE",
    "STAGE_VERSION",
    "SOURCE_MODES",
    "DEDUP_MODES",
    "SIDEWALK_FUNCTION_CODES",
    "ROADWAY_FUNCTION_CODES",
    "WIDTH_RULES",
    "ROAD_SURFACE_WIDTH_M",
    "DISTRICT_SIDEWALK_TOTAL_M2",
    "ADVISORY_AREA_M2",
    "ADVISORY_FEATURE_COUNTS",
    "GATE_I_RATIO_BAND",
    "GATE_II_FRACTION_BAND",
    "DEFAULT_COVERED_MIN_FRAC",
    "DEFAULT_SIDEWALK_MIN_SHARE",
    "LOD_MERGE_MODES",
    "RING_DEDUP_MODES",
    "LOD_PREFERENCE",
    "merge_cell_areas_by_lod",
    "clip_polygon_to_rect",
    "polygon_area",
    "signed_ring_area",
    "unique_triangle_mask",
    "triangle_cell_areas",
    "ring_cell_areas",
    "polyline_cell_lengths",
    "width_for_klass",
    "road_surface_width_for_klass",
    "read_gml_features",
    "gate_values",
    "build",
    "main",
]

STAGE: Final[str] = "c9c_walkable_area"
STAGE_VERSION: Final[str] = "2.0.0"

#: 面の出所。``gml``=生 CityGML(S1 の原文どおり・区全域・1 地物 1 LOD)/``npz``=解析済み。
SOURCE_MODES: Final[tuple[str, ...]] = ("gml", "npz")
#: ``--source npz`` のときの重複三角形の扱い(``xy``=頂点一致を 1 枚に畳む)。
DEDUP_MODES: Final[tuple[str, ...]] = ("xy", "none")

#: S1: 歩行可能面をなす TrafficArea の function コード(codelists/TrafficArea_function.xml)。
#: 2000 歩道部 / 2010 自転車歩行者道 / 2020 歩道。**渋谷区の GML に在るのは 2000 だけ**。
SIDEWALK_FUNCTION_CODES: Final[tuple[int, ...]] = (2000, 2010, 2020)
#: S2: 検算用の車道面(1000 車道部 / 1020 車道交差部)。
ROADWAY_FUNCTION_CODES: Final[tuple[int, ...]] = (1000, 1020)

#: S4: OSM klass → (**歩行可能**幅員[m], 規則名)。**すべて道路構造令**(答申 §1-1 a1〜a3)。
#: - 第十一条第3項「その他の道路にあつては二メートル以上」= 歩道 2.0 m
#: - 第十条の二第2項「その他の道路にあつては三メートル以上」= 自転車歩行者道 3.0 m
#: - 第五条第5項「第三種第五級の普通道路の車道…四メートル」= 歩車共存の細街路 4.0 m
#: - 幹線(tertiary/secondary/primary)は**両側歩道** 2 × 2.0 m
#: ``steps`` 1.5 m と ``elevator`` 0.0 m は答申 S4 の指定(**法的根拠なし=expedient**)。
WIDTH_RULES: Final[dict[str, tuple[float, str]]] = {
    "footway": (2.0, "doro11-3_sidewalk_2.0"),
    "pedestrian": (2.0, "doro11-3_sidewalk_2.0"),
    "path": (2.0, "doro11-3_sidewalk_2.0"),
    "corridor": (2.0, "doro11-3_sidewalk_2.0"),
    "cycleway": (3.0, "doro10-2-2_cycleped_3.0"),
    "residential": (4.0, "doro5-5_shared_roadway_4.0"),
    "service": (4.0, "doro5-5_shared_roadway_4.0"),
    "unclassified": (4.0, "doro5-5_shared_roadway_4.0"),
    "tertiary": (4.0, "doro11-3_sidewalk_both_2x2.0"),
    "secondary": (4.0, "doro11-3_sidewalk_both_2x2.0"),
    "primary": (4.0, "doro11-3_sidewalk_both_2x2.0"),
    "steps": (1.5, "expedient_steps_1.5"),
    "elevator": (0.0, "expedient_elevator_0.0"),
}
#: 表に無い klass の既定(= 歩道の下限)。現データ(W1 13 klass)では 1 本も落ちない。
DEFAULT_WIDTH: Final[tuple[float, str]] = (2.0, "doro11-3_sidewalk_2.0")

#: **被覆率の分母**: OSM klass → 道路面(車道+歩道)の全幅[m]。PLATEAU の分子が
#: 「歩道部+車道部+交差部」なので、分母も車道込みでないと比較にならない。
#: 車線幅員は道路構造令 第五条第4項の表(第四種第一級 **3.25** / 第二級・第三級 **3.0**)、
#: 歩道は第十一条第3項 2.0 m(両側)、細街路は第五条第5項の車道全幅 4.0 m(答申 §1-1 a3/a1)。
#: **車線数 2(上下 1 車線ずつ)は自前=expedient**(W1 は ``lanes`` タグを持たない・a13)。
ROAD_SURFACE_WIDTH_M: Final[dict[str, float]] = {
    "primary": 3.25 * 2 + 2.0 * 2,      # 10.5
    "secondary": 3.0 * 2 + 2.0 * 2,     # 10.0
    "tertiary": 3.0 * 2 + 2.0 * 2,      # 10.0
    "residential": 4.0,
    "service": 4.0,
    "unclassified": 4.0,
    "footway": 2.0,
    "pedestrian": 2.0,
    "path": 2.0,
    "corridor": 2.0,
    "cycleway": 3.0,
    "steps": 1.5,
    "elevator": 0.0,
}
DEFAULT_ROAD_SURFACE_WIDTH_M: Final[float] = 4.0

#: S5: PLATEAU 被覆セルで**OSM 側から足してよい** klass(tran に面が無い歩行者専用路)。
PEDESTRIAN_ONLY_KLASS: Final[tuple[str, ...]] = ("footway", "pedestrian", "steps")

#: S7 (iii): 区全域の歩道部総面積[m²](答申 §1-1 a9・親再計算済)。
#: **この値は ``--ring-dedup none --lod-merge feature`` でのみ再現する**(本実装で 897,556.07 を
#: 確認)。既定(重複を畳む)では **331,434 m²** になる=答申の値は重複計上込み。
DISTRICT_SIDEWALK_TOTAL_M2: Final[float] = 897_556.0
#: 答申 §1-1 a9 の 4 値(地物単位・重複込み)。本実装が再現した値=突き合わせの記録。
ADVISORY_AREA_M2: Final[dict[str, float]] = {
    "2000_sidewalk": 897_556.0,
    "1000_roadway": 1_643_132.0,
    "1020_crossing": 394_352.0,
    "3000_island": 57_996.0,
}
#: 答申 §1-1 a8 の地物数(本実装が再現した値)。
ADVISORY_FEATURE_COUNTS: Final[dict[str, int]] = {
    "2000_sidewalk": 3_505,
    "1000_roadway": 3_461,
    "1020_crossing": 1_900,
    "3000_island": 622,
}
#: S7 (i): 被覆セルでの (歩道部+車道部) / 現行式 の比の中央値が入るべき帯(**expedient**)。
GATE_I_RATIO_BAND: Final[tuple[float, float]] = (0.5, 2.0)
#: S7 (ii): ``walkable_m2 / 10000`` の中央値が入るべき帯(答申 S7 の指定値)。
GATE_II_FRACTION_BAND: Final[tuple[float, float]] = (0.05, 0.45)
#: 被覆と呼ぶ被覆率の下限(**expedient**・親指示 2026-09-17)。
DEFAULT_COVERED_MIN_FRAC: Final[float] = 0.5

#: 現行式(置換される側)。``perception.renderer.STREET_POINT_AREA_M2`` / ``WALKABLE_FRACTION``。
LEGACY_POINT_AREA_M2: Final[float] = 6.25
LEGACY_FLOOR_M2: Final[float] = 1_500.0

# CityGML 2.0 の名前空間(渋谷区 2025 op 版の実測)
NS_TRAN: Final[str] = "{http://www.opengis.net/citygml/transportation/2.0}"
NS_GML: Final[str] = "{http://www.opengis.net/gml}"
NS_CORE: Final[str] = "{http://www.opengis.net/citygml/2.0}"
#: 1 地物から幾何を選ぶ順(S1「LOD3 → LOD2 → LOD1 の順で最初に在るもの」)。
LOD_PREFERENCE: Final[tuple[int, ...]] = (3, 2, 1)
#: **LOD の重なりをどこで落とすか**。渋谷区 2025 の tran は、同じ歩道・車道を
#: **LOD2 の地物(``tran_*``・z=0)と LOD3 の地物(``traf_*``・実 z)に二重に持っている**
#: (歩道部: LOD3 791 地物 571,208 m² / LOD2 2,714 地物 326,348 m²・**LOD3 のあるセル 312 の
#: うち 304 セルに LOD2 も在る**=重なりの下限 226,530 m²)。``gml:id`` が違うので S1 の
#: 「1 地物 1 LOD」では落ちない。
#: - ``cell``(**既定**): セル × function コードごとに ``LOD_PREFERENCE`` の最初に在る LOD
#:   だけ採る=二重計上を落とす。**物理検査: どのセルも 10,000 m²(セル面積)を超えない**。
#: - ``feature``: 地物単位の 1 地物 1 LOD だけ(= 答申 a9 の 897,556 m² を再現する数え方)。
LOD_MERGE_MODES: Final[tuple[str, ...]] = ("cell", "feature")
#: **1 地物の中の環の重複**の扱い。渋谷区 2025 の LOD3 TrafficArea は、
#: **同じ三角形をそっくり 6 回繰り返して格納している**(実測: 地物
#: ``traf_3c0280f7-…`` は環 1,986 枚のうち**一意 331 枚・多重度は全て 6**・
#: 面積 22,795.8 → 3,799.3 m²)。``tran_lod3.npz`` の 2〜6 重登録はこれが根。
#: - ``exact``(**既定**): 頂点列が完全一致する環を 1 枚に畳む。
#: - ``none``: 畳まない(``tran_lod3.json`` の ``area_m2_by_class`` と答申 a9 の数え方)。
RING_DEDUP_MODES: Final[tuple[str, ...]] = ("exact", "none")
#: PLATEAU が「このセルに歩道は無い」と言っているとみなす歩道率の下限(``sidewalk /
#: (sidewalk + roadway)``)。**既定 0.0 = 親指示の被覆率ルールそのまま**(この検査は働かない)。
#: 正の値にすると、歩道の無い被覆セルは 道路構造令 第五条第5項(歩車共存=車道全幅が
#: 歩行空間)に従って OSM 側の推定へ倒す。**自前の線=expedient**。
#: 歩道率(歩道部 / (歩道部+車道部+交差部))がこれ未満のセルは「歩道の無い道路」= OSM 側の推定(道路構造令 5 条 5 項:
#: 歩車共存の細街路は車道全幅が歩行空間)に倒す。0.15 は親判断の expedient(第219): 0.0 だと PLATEAU が
#: 「車道のみ・歩道なし」と言うセルが 0.40 m² になり 22 人/m² の詰まりを生む(mock 5,000 体)。0.0 で検査を切れる。
DEFAULT_SIDEWALK_MIN_SHARE: Final[float] = 0.15


# --------------------------------------------------------------- 幾何(自前・shapely 不要)
def clip_polygon_to_rect(
    poly: list[tuple[float, float]], xmin: float, ymin: float, xmax: float, ymax: float
) -> list[tuple[float, float]]:
    """Sutherland–Hodgman で凸矩形にクリップ(venv に shapely が無いので自前)。

    Args:
        poly: 頂点列(閉じていなくてよい)。
        xmin/ymin/xmax/ymax: 矩形。

    Returns:
        クリップ後の頂点列(空なら交差なし)。

    >>> clip_polygon_to_rect([(0, 0), (2, 0), (2, 2), (0, 2)], 0, 0, 1, 1)
    [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    """
    out = [(float(px), float(py)) for px, py in poly]
    # (axis, value, side): side=+1 は「座標 >= value を残す」
    for axis, value, side in ((0, xmin, 1), (0, xmax, -1), (1, ymin, 1), (1, ymax, -1)):
        if not out:
            return []
        nxt: list[tuple[float, float]] = []
        prev = out[-1]
        p_in = (prev[axis] - value) * side >= 0.0
        for cur in out:
            c_in = (cur[axis] - value) * side >= 0.0
            if c_in != p_in:
                denom = cur[axis] - prev[axis]
                t = 0.0 if denom == 0.0 else (value - prev[axis]) / denom
                nxt.append((prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1])))
            if c_in:
                nxt.append(cur)
            prev, p_in = cur, c_in
        out = nxt
    return out


def polygon_area(poly: list[tuple[float, float]]) -> float:
    """shoelace の絶対値[m²](向きは問わない)。

    >>> polygon_area([(0, 0), (2, 0), (2, 3), (0, 3)])
    6.0
    """
    n = len(poly)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x0, y0 = poly[i - 1]
        x1, y1 = poly[i]
        s += x0 * y1 - x1 * y0
    return abs(s) * 0.5


def signed_ring_area(ring: np.ndarray) -> float:
    """環 ``(n, 2)`` の shoelace の絶対値[m²](向きは問わない)。

    >>> float(signed_ring_area(np.array([[0.0, 0.0], [2.0, 0.0], [2.0, 3.0], [0.0, 3.0]])))
    6.0
    """
    p = np.asarray(ring, dtype=np.float64)
    if p.shape[0] < 3:
        return 0.0
    x, y = p[:, 0], p[:, 1]
    return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y)) * 0.5)


def unique_triangle_mask(tri_q: np.ndarray) -> np.ndarray:
    """量子化整数の三角形 ``(n, 3, 2)`` → **最初の出現だけ True** の真偽配列。

    頂点の並び順に依存しないよう、3 頂点を ``x * 100000 + y`` の値で整列してから比較する
    (PLATEAU の npz は同じ面を 2〜6 回持つ=S1「1 地物 1 LOD=二重計上しない」の実体)。

    >>> t = np.array([[[0, 0], [1, 0], [0, 1]], [[1, 0], [0, 1], [0, 0]]])
    >>> unique_triangle_mask(t).tolist()
    [True, False]
    """
    q = np.asarray(tri_q, dtype=np.int64)
    if q.size == 0:
        return np.zeros(q.shape[0], dtype=bool)
    key = np.sort(q[:, :, 0] * 100_000 + q[:, :, 1], axis=1)
    _, first = np.unique(key, axis=0, return_index=True)
    mask = np.zeros(q.shape[0], dtype=bool)
    mask[first] = True
    return mask


def triangle_cell_areas(tri: np.ndarray, cell_m: float = CELL_M) -> dict[tuple[int, int], float]:
    """三角形群 ``(n, 3, 2)`` → ``(ix, iy)`` ごとの面積[m²](S3・**セル境界でクリップ**)。

    セルを跨がない三角形(圧倒的多数)は shoelace そのまま、跨ぐものだけ
    Sutherland–Hodgman に回す。合計は保存する(クリップは面積を分割するだけ)。

    Note:
        逐次ループ宣言: **跨ぐ三角形の数**ぶんの Python ループ 1 本(ビルド時・1 回きり)。
    """
    if tri.size == 0:
        return {}
    xy = np.asarray(tri, dtype=np.float64)
    x, y = xy[:, :, 0], xy[:, :, 1]
    a = 0.5 * np.abs(
        (x[:, 1] - x[:, 0]) * (y[:, 2] - y[:, 0]) - (x[:, 2] - x[:, 0]) * (y[:, 1] - y[:, 0])
    )
    ix0 = np.floor(x.min(axis=1) / cell_m).astype(np.int64)
    ix1 = np.floor(x.max(axis=1) / cell_m).astype(np.int64)
    iy0 = np.floor(y.min(axis=1) / cell_m).astype(np.int64)
    iy1 = np.floor(y.max(axis=1) / cell_m).astype(np.int64)
    single = (ix0 == ix1) & (iy0 == iy1)

    out: dict[tuple[int, int], float] = {}
    # ---- 速い道: セル内に収まる三角形は bincount 1 本 ----
    s = np.flatnonzero(single)
    if s.size:
        gx0, gy0 = int(ix0[s].min()), int(iy0[s].min())
        nx = int(ix0[s].max()) - gx0 + 1
        key = (ix0[s] - gx0) + (iy0[s] - gy0) * nx
        tot = np.bincount(key, weights=a[s])
        for k in np.flatnonzero(tot):
            out[(int(k % nx) + gx0, int(k // nx) + gy0)] = float(tot[k])
    # ---- 遅い道: 跨ぐ三角形だけ厳密クリップ ----
    for i in np.flatnonzero(~single):
        poly = [(float(x[i, j]), float(y[i, j])) for j in range(3)]
        for cx in range(int(ix0[i]), int(ix1[i]) + 1):
            for cy in range(int(iy0[i]), int(iy1[i]) + 1):
                piece = clip_polygon_to_rect(
                    poly, cx * cell_m, cy * cell_m, (cx + 1) * cell_m, (cy + 1) * cell_m
                )
                ar = polygon_area(piece)
                if ar > 0.0:
                    out[(cx, cy)] = out.get((cx, cy), 0.0) + ar
    return out


def ring_cell_areas(
    rings: "list[tuple[np.ndarray, int]]", out: "dict[tuple[int, int], float] | None" = None,
    cell_m: float = CELL_M,
) -> dict[tuple[int, int], float]:
    """符号つき環の列 → ``(ix, iy)`` ごとの面積[m²](S3・**セル境界でクリップ**)。

    Args:
        rings: ``(環 (n,2), 符号)`` の列。``+1``=``gml:exterior``・``-1``=``gml:interior``。
        out: 足し込み先(``None``なら新規)。
        cell_m: セルの一辺。

    穴(``interior``)は外環と同じ矩形へクリップしてから引く。穴は外環の内側にあるので、
    クリップ後も「穴 ⊂ 外環」の関係は保たれる。

    >>> r = [(np.array([[0.0, 0.0], [200.0, 0.0], [200.0, 100.0], [0.0, 100.0]]), 1)]
    >>> sorted(ring_cell_areas(r).items())
    [((0, 0), 10000.0), ((1, 0), 10000.0)]
    """
    acc: dict[tuple[int, int], float] = {} if out is None else out
    for ring, sign in rings:
        p = np.asarray(ring, dtype=np.float64)
        if p.shape[0] < 3:
            continue
        ix0 = int(np.floor(p[:, 0].min() / cell_m))
        ix1 = int(np.floor(p[:, 0].max() / cell_m))
        iy0 = int(np.floor(p[:, 1].min() / cell_m))
        iy1 = int(np.floor(p[:, 1].max() / cell_m))
        if ix0 == ix1 and iy0 == iy1:  # 速い道: セル内に収まる環
            acc[(ix0, iy0)] = acc.get((ix0, iy0), 0.0) + sign * signed_ring_area(p)
            continue
        poly = [(float(vx), float(vy)) for vx, vy in p]
        for cx in range(ix0, ix1 + 1):
            for cy in range(iy0, iy1 + 1):
                piece = clip_polygon_to_rect(
                    poly, cx * cell_m, cy * cell_m, (cx + 1) * cell_m, (cy + 1) * cell_m
                )
                ar = polygon_area(piece)
                if ar > 0.0:
                    acc[(cx, cy)] = acc.get((cx, cy), 0.0) + sign * ar
    return acc


def polyline_cell_lengths(
    coords: np.ndarray, cell_m: float = CELL_M
) -> dict[tuple[int, int], float]:
    """折れ線 ``(m, 2)`` → ``(ix, iy)`` ごとの長さ[m](セル境界で切る)。

    >>> d = polyline_cell_lengths(np.array([[0.0, 50.0], [200.0, 50.0]]))
    >>> [(k, round(v, 6)) for k, v in sorted(d.items())]
    [((0, 0), 100.0), ((1, 0), 100.0)]
    """
    pts = np.asarray(coords, dtype=np.float64)
    out: dict[tuple[int, int], float] = {}
    for i in range(pts.shape[0] - 1):
        x0, y0 = float(pts[i, 0]), float(pts[i, 1])
        x1, y1 = float(pts[i + 1, 0]), float(pts[i + 1, 1])
        seg = float(np.hypot(x1 - x0, y1 - y0))
        if seg <= 0.0:
            continue
        ts = {0.0, 1.0}
        for p0, p1 in ((x0, x1), (y0, y1)):
            if p0 == p1:
                continue
            lo, hi = (p0, p1) if p0 < p1 else (p1, p0)
            k0 = int(np.floor(lo / cell_m)) + 1
            k1 = int(np.floor(hi / cell_m))
            for k in range(k0, k1 + 1):
                ts.add((k * cell_m - p0) / (p1 - p0))
        order = sorted(t for t in ts if 0.0 <= t <= 1.0)
        for t0, t1 in zip(order, order[1:]):
            if t1 <= t0:
                continue
            tm = 0.5 * (t0 + t1)
            cx = int(np.floor((x0 + tm * (x1 - x0)) / cell_m))
            cy = int(np.floor((y0 + tm * (y1 - y0)) / cell_m))
            out[(cx, cy)] = out.get((cx, cy), 0.0) + seg * (t1 - t0)
    return out


def width_for_klass(klass: str) -> tuple[float, str]:
    """OSM klass → (歩行可能幅員[m], 規則名)。表に無い klass は歩道の下限へ。"""
    return WIDTH_RULES.get(str(klass), DEFAULT_WIDTH)


def road_surface_width_for_klass(klass: str) -> float:
    """OSM klass → **道路面の全幅**[m](被覆率の分母)。表に無い klass は細街路の 4.0 m。"""
    return ROAD_SURFACE_WIDTH_M.get(str(klass), DEFAULT_ROAD_SURFACE_WIDTH_M)


# --------------------------------------------------------------------- S1/S2 生 GML
def read_gml_features(
    gml_dir: Path,
    origin_latlon: tuple[float, float],
    m_per_deg: tuple[float, float],
    ring_dedup: str = RING_DEDUP_MODES[0],
) -> tuple[dict[tuple[int, int], list[tuple[np.ndarray, int]]], dict[str, Any]]:
    """``udx/tran/*.gml`` → function コード別の符号つき環(S1/S2 の原文どおり)。

    ``tran:TrafficArea`` と ``tran:AuxiliaryTrafficArea`` を走査し、**1 地物につき
    ``LOD_PREFERENCE``(3→2→1)の順で最初に在る ``lodNMultiSurface`` 1 つ**だけを採る。
    ``gml:posList`` は (緯度 経度 高さ) の三つ組。``gml:exterior``=+1 / ``gml:interior``=-1。

    Args:
        gml_dir: ``udx/tran``。
        origin_latlon: ``world_crs.json`` の ``origin_latlon``。
        m_per_deg: ``(m_per_deg_lat, m_per_deg_lon)``。

    LOD を鍵に残すのは、**同じ歩道が LOD2 の地物と LOD3 の地物に二重に入っている**ため
    (``LOD_MERGE_MODES`` の ``cell`` がセル単位で片方を落とす)。地物単位の「1 地物 1 LOD」
    だけでは ``gml:id`` が違うので落ちない(LOD2 は ``tran_*``・LOD3 は ``traf_*``)。

    Returns:
        ``({(function コード, LOD): [(環 (n,2) float64, 符号), …]}, 統計)``。

    Note:
        逐次ループ宣言: 地物数(9,488)ぶんのループ 1 本。**ビルド時・1 回きり**で
        ラン(P2/P4)には触れない。``core:cityObjectMember`` ごとに ``clear()`` するので
        RSS はファイル 1 本ぶんに収まる。
    """
    if str(ring_dedup) not in RING_DEDUP_MODES:
        raise ValueError(f"ring_dedup は {RING_DEDUP_MODES} のどれか(いま {ring_dedup!r})")
    lat0, lon0 = float(origin_latlon[0]), float(origin_latlon[1])
    m_lat, m_lon = float(m_per_deg[0]), float(m_per_deg[1])
    n_rings_raw = 0
    n_features_with_repeats = 0
    by_key: dict[tuple[int, int], list[tuple[np.ndarray, int]]] = {}
    n_by_code: dict[int, int] = {}
    lod_by_code: dict[int, dict[int, int]] = {}
    prefix_by_lod: dict[int, dict[str, int]] = {}
    n_no_geom = 0
    n_rings = 0
    files = sorted(Path(gml_dir).glob("*.gml"))
    for path in files:
        for el in _iter_traffic_areas(path):
            fn = el.find(f"{NS_TRAN}function")
            if fn is None or fn.text is None:
                continue
            code = int(fn.text.strip())
            lod_used = -1
            rings: list[tuple[np.ndarray, int]] = []
            for lod in LOD_PREFERENCE:
                ms = el.find(f"{NS_TRAN}lod{lod}MultiSurface")
                if ms is None:
                    continue
                lod_used = lod
                for poly in ms.iter(f"{NS_GML}Polygon"):
                    for kind, sign in (("exterior", 1), ("interior", -1)):
                        for boundary in poly.findall(f"{NS_GML}{kind}"):
                            for ring in boundary.iter(f"{NS_GML}LinearRing"):
                                pos = ring.find(f"{NS_GML}posList")
                                if pos is None or not pos.text:
                                    continue
                                v = np.fromstring(pos.text, sep=" ")
                                if v.size < 9 or v.size % 3:
                                    continue
                                v = v.reshape(-1, 3)
                                xy = np.empty((v.shape[0], 2), dtype=np.float64)
                                xy[:, 0] = (v[:, 1] - lon0) * m_lon  # 経度 → x(東)
                                xy[:, 1] = (v[:, 0] - lat0) * m_lat  # 緯度 → y(北)
                                rings.append((xy, sign))
                break
            if lod_used < 0:
                n_no_geom += 1
                continue
            n_rings_raw += len(rings)
            if str(ring_dedup) == "exact":
                kept = _unique_rings(rings)
                if len(kept) != len(rings):
                    n_features_with_repeats += 1
                rings = kept
            n_rings += len(rings)
            by_key.setdefault((code, lod_used), []).extend(rings)
            n_by_code[code] = n_by_code.get(code, 0) + 1
            lod_by_code.setdefault(code, {})
            lod_by_code[code][lod_used] = lod_by_code[code].get(lod_used, 0) + 1
            gid = str(el.get(f"{NS_GML}id") or "")
            prefix_by_lod.setdefault(lod_used, {})
            pref = gid.split("_")[0]
            prefix_by_lod[lod_used][pref] = prefix_by_lod[lod_used].get(pref, 0) + 1
    stats = {
        "n_files": len(files),
        "n_features_by_code": {str(k): v for k, v in sorted(n_by_code.items())},
        "lod_used_by_code": {
            str(k): {str(lod): n for lod, n in sorted(v.items())}
            for k, v in sorted(lod_by_code.items())
        },
        "gml_id_prefix_by_lod": {
            str(k): dict(sorted(v.items())) for k, v in sorted(prefix_by_lod.items())
        },
        "n_features_without_geometry": n_no_geom,
        "ring_dedup": str(ring_dedup),
        "n_rings_raw": n_rings_raw,
        "n_rings": n_rings,
        "n_features_with_repeated_rings": n_features_with_repeats,
        # **地物単位の合計**(= 答申 a9 の再計算と同じ数え方。LOD2/LOD3 の重なりを含む)
        "area_m2_by_code_feature_sum": _area_by_code(by_key),
        "area_m2_by_code_lod": {
            f"{c}/lod{lod}": round(sum(g * signed_ring_area(r) for r, g in v), 2)
            for (c, lod), v in sorted(by_key.items())
        },
    }
    return by_key, stats


def _unique_rings(
    rings: "list[tuple[np.ndarray, int]]", tol_mm: float = 1.0
) -> "list[tuple[np.ndarray, int]]":
    """1 地物の中の**完全に同じ環**を 1 枚に畳む(順序は保つ=決定論)。

    鍵は「頂点を ``tol_mm`` ミリに丸め、閉じ点を落とし、並びを正規化した多重集合」+ 符号。
    向きの違う同一環も 1 枚に畳む(同じ面を 2 度数えないため)。

    >>> r = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
    >>> out = _unique_rings([(r, 1), (r[::-1].copy(), 1), (r * 2.0, 1)])
    >>> len(out)
    2
    """
    seen: set[tuple[Any, ...]] = set()
    out: list[tuple[np.ndarray, int]] = []
    scale = 1000.0 / float(tol_mm)
    for xy, sign in rings:
        q = np.round(np.asarray(xy, dtype=np.float64) * scale).astype(np.int64)
        if q.shape[0] > 1 and (q[0] == q[-1]).all():
            q = q[:-1]
        key = (int(sign),) + tuple(sorted(map(tuple, q.tolist())))
        if key in seen:
            continue
        seen.add(key)
        out.append((xy, sign))
    return out


def _area_by_code(
    by_key: "dict[tuple[int, int], list[tuple[np.ndarray, int]]]",
) -> dict[str, float]:
    """``(code, lod)`` 別の環 → code 別の合計面積[m2](LOD をまたいで足す=重なり込み)。"""
    out: dict[int, float] = {}
    for (code, _lod), rings in by_key.items():
        out[code] = out.get(code, 0.0) + sum(g * signed_ring_area(r) for r, g in rings)
    return {str(k): round(v, 2) for k, v in sorted(out.items())}


def merge_cell_areas_by_lod(
    per_lod: dict[int, dict[tuple[int, int], float]], mode: str
) -> dict[tuple[int, int], float]:
    """同じ function コードの LOD 別セル面積 -> セルごとに 1 つの LOD を選んで束ねる。

    Args:
        per_lod: ``{LOD: {(ix, iy): 面積}}``。
        mode: ``"cell"``=セルごとに ``LOD_PREFERENCE`` の最初に在る LOD だけ採る
            (**既定**・LOD2/LOD3 の二重計上を落とす)/ ``"feature"``=全 LOD を足す
            (地物単位の「1 地物 1 LOD」だけ=答申 a9 と同じ数え方)。

    >>> merge_cell_areas_by_lod({3: {(0, 0): 10.0}, 2: {(0, 0): 4.0, (1, 0): 7.0}}, "cell")
    {(0, 0): 10.0, (1, 0): 7.0}
    >>> merge_cell_areas_by_lod({3: {(0, 0): 10.0}, 2: {(0, 0): 4.0}}, "feature")
    {(0, 0): 14.0}
    """
    if str(mode) not in LOD_MERGE_MODES:
        raise ValueError(f"lod_merge は {LOD_MERGE_MODES} のどれか(いま {mode!r})")
    out: dict[tuple[int, int], float] = {}
    if str(mode) == "feature":
        for d in per_lod.values():
            for k, v in d.items():
                out[k] = out.get(k, 0.0) + v
        return out
    keys: set[tuple[int, int]] = set()
    for d in per_lod.values():
        keys |= set(d)
    for k in sorted(keys):
        for lod in LOD_PREFERENCE:
            d = per_lod.get(lod)
            if d is not None and k in d:
                out[k] = d[k]
                break
    return out


def _iter_traffic_areas(path: Path) -> Iterator[ET.Element]:
    """1 ファイルの ``tran:TrafficArea`` / ``tran:AuxiliaryTrafficArea`` を順に返す。

    ``core:cityObjectMember`` の終端で ``clear()`` して RSS を抑える(184 MB を 1 パス)。
    """
    for _, el in ET.iterparse(str(path), events=("end",)):
        if el.tag in (f"{NS_TRAN}TrafficArea", f"{NS_TRAN}AuxiliaryTrafficArea"):
            yield el
        elif el.tag == f"{NS_CORE}cityObjectMember":
            el.clear()


# --------------------------------------------------------------------- S7 ゲート
def gate_values(
    sidewalk: np.ndarray,
    roadway: np.ndarray,
    walkable: np.ndarray,
    legacy: np.ndarray,
    covered: np.ndarray,
) -> dict[str, Any]:
    """S7 の 3 ゲートを数える(純関数・テストから直接呼ぶ)。

    Args:
        sidewalk/roadway/walkable/legacy: セル別[m²]。``legacy`` は現行式
            ``max(街路点数 × 6.25, 1500)``。
        covered: PLATEAU 被覆セルの真偽。

    Returns:
        ``{"i": {...}, "ii": {...}, "iii": {...}}``。各々 ``value`` と ``pass``。
    """
    cov = np.asarray(covered, dtype=bool)
    lg = np.asarray(legacy, dtype=np.float64)
    ratio = np.divide(
        np.asarray(sidewalk, np.float64)[cov] + np.asarray(roadway, np.float64)[cov],
        np.maximum(lg[cov], 1.0),
    )
    med_ratio = float(np.median(ratio)) if ratio.size else float("nan")
    frac = np.asarray(walkable, np.float64) / (CELL_M * CELL_M)
    med_frac = float(np.median(frac)) if frac.size else float("nan")
    in_band = (
        float(np.mean((frac >= GATE_II_FRACTION_BAND[0]) & (frac <= GATE_II_FRACTION_BAND[1])))
        if frac.size
        else float("nan")
    )
    total = float(np.asarray(sidewalk, np.float64).sum())
    return {
        "i": {
            "name": "plateau_vs_legacy_ratio_median",
            "value": med_ratio,
            "band": list(GATE_I_RATIO_BAND),
            "reference": 1.125,
            "n_cells": int(cov.sum()),
            "pass": bool(GATE_I_RATIO_BAND[0] <= med_ratio <= GATE_I_RATIO_BAND[1]),
        },
        "ii": {
            "name": "walkable_fraction_median",
            "value": med_frac,
            "band": list(GATE_II_FRACTION_BAND),
            "cells_in_band_share": in_band,
            "min": float(frac.min()) if frac.size else float("nan"),
            "max": float(frac.max()) if frac.size else float("nan"),
            "pass": bool(GATE_II_FRACTION_BAND[0] <= med_frac <= GATE_II_FRACTION_BAND[1]),
        },
        "iii": {
            "name": "plateau_sidewalk_total_m2",
            "value": total,
            "limit": DISTRICT_SIDEWALK_TOTAL_M2,
            "pass": bool(total <= DISTRICT_SIDEWALK_TOTAL_M2),
        },
    }


# --------------------------------------------------------------------- 本体
def build(
    plateau_dir: Path,
    world_dir: Path,
    out_dir: Path,
    *,
    out_name: str = "c9c_walkable_area.parquet",
    source: str = SOURCE_MODES[0],
    gml_dir: "Path | None" = None,
    dedup: str = DEDUP_MODES[0],
    lod_merge: str = LOD_MERGE_MODES[0],
    ring_dedup: str = RING_DEDUP_MODES[0],
    covered_min_frac: float = DEFAULT_COVERED_MIN_FRAC,
    covered_min_m2: float = 0.0,
    sidewalk_min_share: float = DEFAULT_SIDEWALK_MIN_SHARE,
) -> dict[str, Any]:
    """S1〜S7 を通してセル別 ``walkable_m2`` の parquet + ヘッダを書く。

    **既存資産は上書きしない**(``out_name`` が既に在れば ``FileExistsError``)。
    """
    import pyarrow.parquet as pq

    if str(source) not in SOURCE_MODES:
        raise ValueError(f"source は {SOURCE_MODES} のどれか(いま {source!r})")
    if str(dedup) not in DEDUP_MODES:
        raise ValueError(f"dedup は {DEDUP_MODES} のどれか(いま {dedup!r})")
    if str(lod_merge) not in LOD_MERGE_MODES:
        raise ValueError(f"lod_merge は {LOD_MERGE_MODES} のどれか(いま {lod_merge!r})")
    plateau_dir, world_dir, out_dir = Path(plateau_dir), Path(world_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / out_name
    if target.exists():
        raise FileExistsError(f"既存ファイルは上書きしない: {target}")

    crs_path = world_dir / "world_crs.json"
    cells_path = world_dir / "w2_cells.parquet"
    edges_path = world_dir / "w1_edges.parquet"
    egeom_path = world_dir / "w1_edge_geometry.npz"
    points_path = world_dir / "w10_street_points.parquet"
    common_inputs = [crs_path, cells_path, edges_path, egeom_path, points_path]

    if str(source) == "gml":
        gdir = Path(gml_dir) if gml_dir is not None else _default_gml_dir()
        face_inputs = sorted(gdir.glob("*.gml"))
        if not face_inputs:
            raise FileNotFoundError(f"GML が無い: {gdir}")
    else:
        face_inputs = [plateau_dir / "tran_lod3.npz", plateau_dir / "tran_lod3.json"]
    inputs = face_inputs + common_inputs
    for p in inputs:
        if not p.exists():
            raise FileNotFoundError(f"入力が無い: {p}")

    crs = json.loads(crs_path.read_text(encoding="utf-8"))
    origin = (float(crs["origin_latlon"][0]), float(crs["origin_latlon"][1]))
    m_per_deg = (float(crs["m_per_deg_lat"]), float(crs["m_per_deg_lon"]))

    t0 = time.perf_counter()
    if str(source) == "gml":
        by_key, face_stats = read_gml_features(gdir, origin, m_per_deg, ring_dedup=ring_dedup)
        # S3: (function コード, LOD) ごとにセル境界でクリップし、**セル × コード**単位で
        # LOD を 1 つに畳む(LOD2 と LOD3 の二重計上を落とす=上の LOD_MERGE_MODES)。
        per_code_lod: dict[int, dict[int, dict[tuple[int, int], float]]] = {}
        for (code, lod), rings in by_key.items():
            per_code_lod.setdefault(code, {})[lod] = ring_cell_areas(rings)
        side_by_cell: dict[tuple[int, int], float] = {}
        road_by_cell: dict[tuple[int, int], float] = {}
        for code, per_lod in per_code_lod.items():
            merged = merge_cell_areas_by_lod(per_lod, lod_merge)
            dst = (
                side_by_cell
                if code in SIDEWALK_FUNCTION_CODES
                else (road_by_cell if code in ROADWAY_FUNCTION_CODES else None)
            )
            if dst is None:
                continue
            for k, v in merged.items():
                dst[k] = dst.get(k, 0.0) + v
        face_stats["lod_merge"] = str(lod_merge)
        face_stats["area_m2_by_code_after_lod_merge"] = {
            str(code): round(sum(merge_cell_areas_by_lod(per_lod, lod_merge).values()), 2)
            for code, per_lod in sorted(per_code_lod.items())
        }
    else:
        side_by_cell, road_by_cell, face_stats = _npz_cell_areas(
            plateau_dir / "tran_lod3.npz", plateau_dir / "tran_lod3.json", dedup
        )
    face_seconds = time.perf_counter() - t0

    # ---- セル台帳(W2) ----
    cd = pq.read_table(cells_path, columns=["place_id", "ix", "iy", "band"]).to_pydict()
    pids = [str(v) for v in cd["place_id"]]
    cix = np.asarray(cd["ix"], dtype=np.int64)
    ciy = np.asarray(cd["iy"], dtype=np.int64)
    cband = [str(v) for v in cd["band"]]
    n_cells = len(pids)
    index_of = {(int(cix[i]), int(ciy[i]), cband[i]): i for i in range(n_cells)}

    sidewalk = np.zeros(n_cells, dtype=np.float64)
    roadway = np.zeros(n_cells, dtype=np.float64)
    dropped_side = dropped_road = 0.0
    for (ix, iy), val in side_by_cell.items():  # S6: PLATEAU の面は GL だけ
        j = index_of.get((ix, iy, "GL"))
        if j is None:
            dropped_side += val
        else:
            sidewalk[j] += val
    for (ix, iy), val in road_by_cell.items():
        j = index_of.get((ix, iy, "GL"))
        if j is None:
            dropped_road += val
        else:
            roadway[j] += val

    # ---- S4 OSM 線 × 道路構造令の既定幅員(+ 被覆率の分母=道路面の全幅) ----
    ed = pq.read_table(
        edges_path, columns=["klass", "length_m", "band", "geom_start", "geom_count"]
    ).to_pydict()
    eg = np.load(egeom_path)
    coords = np.asarray(eg["coords"], dtype=np.float64)
    osm_area = np.zeros(n_cells, dtype=np.float64)
    osm_area_ped = np.zeros(n_cells, dtype=np.float64)  # 歩行者専用路だけの内訳(S5)
    osm_road_surface = np.zeros(n_cells, dtype=np.float64)  # 被覆率の分母
    rule_len: list[dict[str, float]] = [dict() for _ in range(n_cells)]
    osm_len_by_klass: dict[str, float] = {}
    n_edges_outside = 0
    for e in range(len(ed["klass"])):
        klass = str(ed["klass"][e])
        width, rule = width_for_klass(klass)
        full = road_surface_width_for_klass(klass)
        g0 = int(ed["geom_start"][e])
        g1 = g0 + int(ed["geom_count"][e])
        per_cell = polyline_cell_lengths(coords[g0:g1])
        poly_len = sum(per_cell.values())
        if poly_len <= 0.0:
            continue
        scale = float(ed["length_m"][e]) / poly_len  # 街路長へ按分(expedient 5)
        band = str(ed["band"][e])
        ped_only = klass in PEDESTRIAN_ONLY_KLASS
        placed = False
        for (ix, iy), ln in per_cell.items():
            j = index_of.get((ix, iy, band))
            if j is None:
                continue
            placed = True
            length = ln * scale
            osm_area[j] += length * width
            osm_road_surface[j] += length * full
            if ped_only:
                osm_area_ped[j] += length * width
            rule_len[j][rule] = rule_len[j].get(rule, 0.0) + length
            osm_len_by_klass[klass] = osm_len_by_klass.get(klass, 0.0) + length
        if not placed:
            n_edges_outside += 1

    # ---- S5 合成(**被覆率**で判定・親指示 2026-09-17) ----
    # 分子 = PLATEAU の道路面(歩道部+車道部+交差部)/ 分母 = OSM 規則の道路面推定。
    # 半端に被覆されたセルは分子が物理的に不完全なので ``osm`` へ倒す(``mixed`` にしない)。
    coverage = (sidewalk + roadway) / np.maximum(osm_road_surface, 1e-9)
    # 歩道率: PLATEAU が「このセルに歩道は無い」と言っているセルを見分ける。既定 0.0 では
    # 働かない(= 親指示の被覆率ルールそのまま)。
    sidewalk_share = sidewalk / np.maximum(sidewalk + roadway, 1e-9)
    covered = (
        (coverage >= float(covered_min_frac))
        & (sidewalk > float(covered_min_m2))
        & (sidewalk_share >= float(sidewalk_min_share))
    )
    walkable = np.where(covered, sidewalk + osm_area_ped, osm_area)
    source_col = np.where(
        covered & (osm_area_ped > 0.0), "mixed", np.where(covered, "plateau", "osm")
    )
    width_rule = [
        (max(rule_len[i].items(), key=lambda kv: (kv[1], kv[0]))[0] if rule_len[i] else "")
        for i in range(n_cells)
    ]

    # ---- S7 (i) の分母: 現行式 max(街路点数 × 6.25, 1500) ----
    legacy = _legacy_area(points_path, index_of, n_cells)
    gates = gate_values(sidewalk, roadway, walkable, legacy, covered)

    # ---- 出力 ----
    rec = write_parquet(
        out_dir,
        out_name,
        {
            "cell_id": pids,
            "band": cband,
            "walkable_m2": [round(float(v), 4) for v in walkable],
            "plateau_sidewalk_m2": [round(float(v), 4) for v in sidewalk],
            "plateau_roadway_m2": [round(float(v), 4) for v in roadway],
            "osm_walkable_m2": [round(float(v), 4) for v in osm_area],
            "width_rule": width_rule,
            "source": [str(v) for v in source_col],
        },
        schema=pa.schema(
            [
                ("cell_id", pa.string()),
                ("band", pa.string()),
                ("walkable_m2", pa.float64()),
                ("plateau_sidewalk_m2", pa.float64()),
                ("plateau_roadway_m2", pa.float64()),
                ("osm_walkable_m2", pa.float64()),
                ("width_rule", pa.string()),
                ("source", pa.string()),
            ]
        ),
    )
    params = {
        "cell_m": CELL_M,
        "source": str(source),
        "dedup": str(dedup) if str(source) == "npz" else "n/a",
        "lod_preference": list(LOD_PREFERENCE),
        "lod_merge": str(lod_merge),
        "ring_dedup": str(ring_dedup),
        "covered_min_frac": float(covered_min_frac),
        "covered_min_m2": float(covered_min_m2),
        "sidewalk_min_share": float(sidewalk_min_share),
        "sidewalk_function_codes": list(SIDEWALK_FUNCTION_CODES),
        "roadway_function_codes": list(ROADWAY_FUNCTION_CODES),
        "width_rules": {k: list(v) for k, v in sorted(WIDTH_RULES.items())},
        "road_surface_width_m": dict(sorted(ROAD_SURFACE_WIDTH_M.items())),
        "pedestrian_only_klass": list(PEDESTRIAN_ONLY_KLASS),
        "clip": "sutherland-hodgman per 100m cell (no centroid assignment)",
        "plateau_band": "GL only (S6)",
        "legacy_formula": f"max(n_street_points * {LEGACY_POINT_AREA_M2}, {LEGACY_FLOOR_M2})",
    }
    src_by = {s: int(np.count_nonzero(source_col == s)) for s in ("plateau", "osm", "mixed")}
    result = StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=input_hash(inputs),
        param_hash=param_hash(params),
        params=params,
        outputs=[rec],
        gates=[
            Gate(
                "S7_i_plateau_vs_legacy_ratio_median",
                gates["i"]["value"],
                expected=None,
                passed=gates["i"]["pass"],
            ),
            Gate(
                "S7_ii_walkable_fraction_median",
                gates["ii"]["value"],
                expected=None,
                passed=gates["ii"]["pass"],
            ),
            Gate(
                "S7_iii_plateau_sidewalk_total_m2",
                gates["iii"]["value"],
                expected=None,
                passed=gates["iii"]["pass"],
            ),
        ],
        catalog_classes=["セル(場所100m+層)", "街路(歩行グラフ)"],
        expedients=[
            "PLATEAU の面は band=GL のセルにだけ入れる(S6・DECK/UG は OSM 線のみ)",
            "S7 (i) の合否帯 [0.5, 2.0] は自前(答申は帯を書いていない)",
            "S7 (ii) は中央値で判定・帯外セルの割合は報告のみ",
            "steps 1.5 m / elevator 0.0 m は法的根拠なし(答申 S4 の指定)",
            "OSM 線は折れ線をセル境界で切り、その比で W1 の length_m を按分",
            "width_rule 列はセル内で最長の klass の規則名 1 つ",
            f"被覆の判定は被覆率 ≥ {float(covered_min_frac)}(自前の線・半端なセルは osm へ倒す)",
            f"LOD の重なりを落とす粒度 lod_merge={lod_merge}(cell=セル×コードで LOD3 優先)",
            f"地物内の環の重複 ring_dedup={ring_dedup}(LOD3 は同じ三角形を 6 回持つ)",
            f"歩道率の下限 {float(sidewalk_min_share)}(0.0 = 検査しない)",
            "被覆率の分母 ROAD_SURFACE_WIDTH_M の車線数=上下 1 車線ずつ(W1 に lanes 無し)",
        ],
        notes={
            "inputs_sha256": {p.name: sha256_file(p) for p in inputs},
            "face_source_stats": face_stats,
            "face_read_seconds": round(face_seconds, 2),
            "plateau_sidewalk_m2_total": round(float(sidewalk.sum()), 2),
            "plateau_roadway_m2_total": round(float(roadway.sum()), 2),
            "osm_walkable_m2_total": round(float(osm_area.sum()), 2),
            "osm_road_surface_m2_total": round(float(osm_road_surface.sum()), 2),
            "walkable_m2_total": round(float(walkable.sum()), 2),
            "area_outside_world_cells_m2": {
                "sidewalk": round(dropped_side, 2),
                "roadway": round(dropped_road, 2),
            },
            "n_cells": n_cells,
            "n_cells_covered": int(covered.sum()),
            "n_cells_uncovered": int((~covered).sum()),
            "source_counts": src_by,
            "coverage_median": round(float(np.median(coverage)), 4),
            "coverage_p90": round(float(np.percentile(coverage, 90)), 4),
            "n_cells_over_cell_area": int(
                np.count_nonzero(sidewalk + roadway > CELL_M * CELL_M)
            ),
            "n_cells_plateau_no_sidewalk": int(
                np.count_nonzero((roadway > 0.0) & (sidewalk_share < 0.05))
            ),
            "n_cells_zero_walkable": int(np.count_nonzero(walkable <= 0.0)),
            "n_cells_walkable_lt_100m2": int(np.count_nonzero(walkable < 100.0)),
            "n_cells_walkable_lt_500m2": int(np.count_nonzero(walkable < 500.0)),
            "n_cells_covered_below_osm": int(np.count_nonzero(covered & (walkable < osm_area))),
            "walkable_m2_min": round(float(walkable.min()), 4),
            "walkable_m2_p05": round(float(np.percentile(walkable, 5)), 4),
            "walkable_m2_median": round(float(np.median(walkable)), 4),
            "walkable_m2_p95": round(float(np.percentile(walkable, 95)), 4),
            "walkable_m2_max": round(float(walkable.max()), 4),
            "legacy_m2_median": round(float(np.median(legacy)), 4),
            "legacy_m2_total": round(float(legacy.sum()), 2),
            "osm_length_by_klass": {k: round(v, 1) for k, v in sorted(osm_len_by_klass.items())},
            "n_edges_outside_world_cells": n_edges_outside,
            "advisory_reconciliation": {
                "advisory_area_m2": dict(ADVISORY_AREA_M2),
                "advisory_feature_counts": dict(ADVISORY_FEATURE_COUNTS),
                "reproduced_with": "--source gml --ring-dedup none --lod-merge feature",
                "note": (
                    "地物数 4 種と面積 4 種は答申 a8/a9 と 1 m² 以内で一致した。ただし"
                    "その数え方は重複計上込み: (1) **LOD3 の TrafficArea は同じ三角形を 6 回**"
                    "持つ(例 traf_3c0280f7…: 環 1,986 のうち一意 331・面積 22,795.8 → "
                    "3,799.3 m²)。(2) **同じ歩道を LOD2 の地物(tran_*・z=0)と LOD3 の地物"
                    "(traf_*・実 z)が二重に持つ**(歩道部 LOD3 の 312 セルのうち 304 セルに"
                    "LOD2 も在る)。gml:id が違うので S1 の「1 地物 1 LOD」では落ちない。"
                    "既定(ring_dedup=exact + lod_merge=cell)の区全域 歩道部は 331,434 m²。"
                    "物証: 答申の数え方では 100 m セルの面積 10,000 m² を超えるセルが 32 個"
                    "出るが、既定では 0 個。"
                ),
            },
            "gates": gates,
        },
    )
    write_header(out_dir, result)
    return {"output": rec, "gates": gates, "notes": result.notes}


def _default_gml_dir() -> Path:
    return (
        _REPO / "data" / "realworld" / "plateau_2025"
        / "13113_shibuya-ku_pref_2025_citygml_1_op" / "udx" / "tran"
    )


def _npz_cell_areas(
    npz_path: Path, meta_path: Path, dedup: str
) -> tuple[dict[tuple[int, int], float], dict[tuple[int, int], float], dict[str, Any]]:
    """``--source npz``: 解析済み三角形 → セル別面積(LOD3 + clip_rect の部分集合)。"""
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    z = np.load(npz_path)
    quant = float(meta["quant_scale"])
    origin_q = np.asarray(z["origin_q"], dtype=np.float64)
    xy_m = (np.asarray(z["xy"], dtype=np.float64) + origin_q) * quant
    offs = np.asarray(z["poly_offsets"], dtype=np.int64)
    code = np.asarray(z["poly_code"], dtype=np.int64)
    n_poly = int(code.size)
    if not np.all(np.diff(offs) == 3):
        raise ValueError("tran_lod3.npz の poly_offsets が 3 頂点刻みでない(三角形前提が崩れた)")
    vidx = offs[:-1][:, None] + np.arange(3)[None, :]
    tri = xy_m[vidx].reshape(n_poly, 3, 2)
    tri_q = np.asarray(z["xy"], dtype=np.int64)[vidx].reshape(n_poly, 3, 2)
    walk_mask = np.isin(code, np.asarray(SIDEWALK_FUNCTION_CODES))
    road_mask = np.isin(code, np.asarray(ROADWAY_FUNCTION_CODES))
    n_walk_raw, n_road_raw = int(walk_mask.sum()), int(road_mask.sum())
    if str(dedup) == "xy":  # S1「1 地物 1 LOD=二重計上しない」の代用
        for mask in (walk_mask, road_mask):
            sel = np.flatnonzero(mask)
            keep = sel[unique_triangle_mask(tri_q[sel])]
            mask[:] = False
            mask[keep] = True
    stats = {
        "mode": "npz",
        "dedup": str(dedup),
        "n_triangles_total": n_poly,
        "n_triangles_sidewalk": int(walk_mask.sum()),
        "n_triangles_sidewalk_raw": n_walk_raw,
        "n_triangles_roadway": int(road_mask.sum()),
        "n_triangles_roadway_raw": n_road_raw,
        "function_codes_present": sorted(int(c) for c in np.unique(code)),
    }
    return triangle_cell_areas(tri[walk_mask]), triangle_cell_areas(tri[road_mask]), stats


def _legacy_area(
    points_path: Path, index_of: dict[tuple[int, int, str], int], n_cells: int
) -> np.ndarray:
    """現行式 ``max(街路点数 × 6.25, 1500)``[m²](``renderer._street_aggregate`` と同式)。"""
    import pyarrow.parquet as pq

    d = pq.read_table(points_path, columns=["x", "y", "band"]).to_pydict()
    sx = np.asarray(d["x"], dtype=np.float64)
    sy = np.asarray(d["y"], dtype=np.float64)
    ix = np.floor(sx / CELL_M).astype(np.int64)
    iy = np.floor(sy / CELL_M).astype(np.int64)
    counts = np.zeros(n_cells, dtype=np.float64)
    bands = [str(b) for b in d["band"]]
    for i in range(ix.size):
        j = index_of.get((int(ix[i]), int(iy[i]), bands[i]))
        if j is not None:
            counts[j] += 1.0
    return np.maximum(counts * LEGACY_POINT_AREA_M2, LEGACY_FLOOR_M2)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="C9c-1 歩行可能面積の実測化(S1〜S7)")
    ap.add_argument("--plateau", default=str(_REPO / "data" / "plateau"))
    ap.add_argument("--world", default=str(_REPO / "data" / "world" / "v2"))
    ap.add_argument("--out", default=str(_REPO / "data" / "world" / "v2"))
    ap.add_argument("--name", default="c9c_walkable_area.parquet")
    ap.add_argument(
        "--source",
        choices=SOURCE_MODES,
        default=SOURCE_MODES[0],
        help="面の出所。gml=生 CityGML(既定・区全域・1 地物 1 LOD=S1 の原文どおり)/"
        "npz=解析済み tran_lod3.npz(LOD3 + clip_rect の部分集合)",
    )
    ap.add_argument("--gml-dir", default=str(_default_gml_dir()))
    ap.add_argument(
        "--dedup",
        choices=DEDUP_MODES,
        default=DEDUP_MODES[0],
        help="`--source npz` のときだけ効く。xy=頂点一致の三角形を 1 枚に畳む(既定)/"
        "none=畳まない(tran_lod3.json の area_m2_by_class と一致)",
    )
    ap.add_argument(
        "--lod-merge",
        choices=LOD_MERGE_MODES,
        default=LOD_MERGE_MODES[0],
        help="LOD の重なりを落とす粒度。cell=セル × function コードごとに LOD3→LOD2→LOD1 の"
        "最初の 1 つだけ採る(既定)/ feature=地物単位の 1 地物 1 LOD だけ(答申 a9 の数え方)",
    )
    ap.add_argument(
        "--ring-dedup",
        choices=RING_DEDUP_MODES,
        default=RING_DEDUP_MODES[0],
        help="1 地物の中で同じ環が繰り返されているときの扱い。exact=1 枚に畳む(既定・"
        "渋谷区 2025 の LOD3 は同じ三角形を 6 回持つ)/ none=畳まない(答申 a9 の数え方)",
    )
    ap.add_argument(
        "--sidewalk-min-share",
        type=float,
        default=DEFAULT_SIDEWALK_MIN_SHARE,
        help="被覆と呼ぶ歩道率 sidewalk/(sidewalk+roadway) の下限(既定 0.0=検査しない)",
    )
    ap.add_argument(
        "--covered-min-frac",
        type=float,
        default=DEFAULT_COVERED_MIN_FRAC,
        help="PLATEAU 被覆と呼ぶ被覆率の下限(既定 0.5・PLATEAU 道路面 / OSM 道路面推定)",
    )
    ap.add_argument(
        "--covered-min-m2",
        type=float,
        default=0.0,
        help="被覆と呼ぶ歩道部面積の下限[m²](診断用・既定 0.0=歩道部が 1 m² でもあれば可)",
    )
    args = ap.parse_args(argv)
    res = build(
        Path(args.plateau),
        Path(args.world),
        Path(args.out),
        out_name=str(args.name),
        source=str(args.source),
        gml_dir=Path(args.gml_dir),
        dedup=str(args.dedup),
        lod_merge=str(args.lod_merge),
        ring_dedup=str(args.ring_dedup),
        covered_min_frac=float(args.covered_min_frac),
        covered_min_m2=float(args.covered_min_m2),
        sidewalk_min_share=float(args.sidewalk_min_share),
    )
    print(json.dumps(res, ensure_ascii=False, indent=1, default=float))
    return 0 if all(g["pass"] for g in res["gates"].values()) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
