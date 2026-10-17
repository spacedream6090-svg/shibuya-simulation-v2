"""W10 の物差し(W10 の Q6・2026-09-30): 較正点に町丁目の代表点の座標を付け、
「点の近くの騒音場の値 − 実測」を測る。

なぜ要るか: :func:`w10_noise.calibrate` は R5 の CSV の各点の路線名・車線数・車道端距離で
センサスを引いて式を評価するだけで、**辺も騒音場も通らない**(点に座標が無い)。したがって
道路名の突合(段 1c/1c′)の良し悪しは、いまの残差では測れない。本モジュールは騒音場そのもの
(``w10_noise_day.npy``/``w10_noise_night.npy``・街路 2.5 m 格子)を点の近くで読む。

**本モジュールは W10 の段(``w10_noise.run``)に組み込まない**(W10 の出力とヘッダを 1 バイトも
動かさないため)。計測の道具(``docs/bench/analysis/wave2-2026-09-30/w10_ruler_measure.py``)と
テストから呼ぶ。

座標の材料(リポと ``data/`` の中だけ)
- 町丁目の境界 = 国勢調査 2020 小地域境界(e-Stat ``r2ka13113``・W16 が読むもの)。**渋谷区だけ**。
  R5 の 7 点のうち目黒区(No.61)・世田谷区(No.75)の 2 点は境界が無い=座標を付けない
  (要るもの: 目黒区 ``r2ka13110``・世田谷区 ``r2ka13112`` の小地域境界)。さらに渋谷区の 5 点の
  うち No.80 広尾五丁目・No.81 本町一丁目は**世界の範囲の外**(町丁目に街路格子が 1 点も無い)=
  騒音場で測れるのは No.78・79・82 の 3 点だけ(No.61 青葉台四丁目が世界の中かは境界が無く未確認)。
- 住所 → 小地域名(:func:`parse_address`): 丁目の番号だけを漢数字に直す(町名の中の漢数字=三田・
  六本木・四谷 などには触らない)。突合できない点は例外ではなく理由コードの行で返す
  (:data:`STATUSES`)。
- 代表点(2 通り・どちらも**未リサーチ(expedient)**の自前の構成):
  - ``estat``: 小地域境界の .dbf の ``X_CODE``/``Y_CODE``(e-Stat が各小地域に付けた代表点の経緯度)。
  - ``road_facing``: 町丁目の中の地上(GL)の街路格子点のうち、最寄りの辺が「測った道路の階級」
    (:data:`MEASURED_ROAD_KLASSES`)のもので、``estat`` の点に最も近いもの(=町丁目の中で
    測った階級の道路に面した点)。同距離は格子の番号の小さい方。候補が無ければ ``None``。

物差し(:func:`measure_near`・**未リサーチ(expedient)**)
- 半径 r(:data:`RADII_M`)の中の GL の街路格子点について、代表値を 2 通り:
  - ``max``: 最大値(昼・夜それぞれ)。
  - ``road``: 「道路に最も近い格子」の値=測った階級の辺までの距離が最小の格子点の値。同距離は
    格子の番号の小さい方=**昼と夜は同じ格子点**から読む。距離(``road_dist_m``)を必ず併記し、
    騒音場の格子の幅(辺の中心線から :data:`ROAD_BAND_M`=8 m・D-W9)を超えるものに
    ``road_beyond_band=True`` の印を付ける(値は消さない=道路の値ではなく近くの別の道の値)。
- 差 = 代表値 − 実測(昼・夜)。騒音場は uint8 に丸めた dB(±0.5 dB の量子化)。
- 値・距離に NaN があれば :class:`ValueError`(いまの資産は uint8 なので起きない)。

物差しの誤差の見積り(:func:`ruler_error`)
- 町丁目の等価半径 √(面積/π)・``estat`` 点と面積重心の距離・``estat`` 点と ``road_facing`` 点の距離。
- 町丁目の中の「測った階級の道路の格子点」の値の散らばり(5/50/95 % 点)=実際の測定点が
  町丁目のどこにあっても取りうる値の幅。
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from ..geo import common as G
from ..pop import shapefile as SH
from . import common as C
from . import w10_noise as W
from .street_grid import segment_arrays

__all__ = [
    "BOUNDARY_SHP",
    "BOUNDARY_DBF",
    "RADII_M",
    "REPRESENTATIVES",
    "STATISTICS",
    "STATUSES",
    "ROAD_BAND_M",
    "MEASURED_ROAD_KLASSES",
    "measured_klasses",
    "parse_address",
    "chome_name_from_address",
    "Chome",
    "load_chome",
    "polygon_centroid",
    "points_to_segments_min_dist",
    "measure_near",
    "road_facing_point",
    "ruler_error",
    "ruler_rows",
    "ruler_from_world",
    "summarize_diffs",
]

#: 小地域境界(W16 と同じファイル・渋谷区だけ)。
BOUNDARY_SHP: tuple[str, ...] = ("realworld", "estat", "r2ka13113", "r2ka13113.shp")
BOUNDARY_DBF: tuple[str, ...] = ("realworld", "estat", "r2ka13113", "r2ka13113.dbf")
#: 半径 r [m](3 通り・expedient)。
RADII_M: tuple[float, ...] = (25.0, 50.0, 100.0)
#: 代表点の決め方(2 通り・expedient)。
REPRESENTATIVES: tuple[str, ...] = ("estat", "road_facing")
#: 代表値の取り方(2 通り・expedient)。
STATISTICS: tuple[str, ...] = ("max", "road")
#: 騒音場の格子の帯の幅 [m](辺の中心線から・D-W9 の街路格子のバッファ=``street_points`` の既定)。
#: ``road`` の距離がこれを超えたら「道路の値」ではない印を付ける(新しい定数ではなく D-W9 の値)。
ROAD_BAND_M: float = 8.0

#: 点の行の状態(理由コード)。
#: OK / NO_BOUNDARY=区の境界が無い / NAME_NOT_FOUND=区の境界はあるが町名が突合できない /
#: AMBIGUOUS_NO_CHOME=「神宮前5-53-1」のような丁目の無い書き方で、その町に丁目がある /
#: UNPARSEABLE=区が読めない / OUTSIDE_WORLD=町丁目に街路格子が 1 点も無い。
STATUSES: tuple[str, ...] = (
    "OK", "NO_BOUNDARY", "NAME_NOT_FOUND", "AMBIGUOUS_NO_CHOME", "UNPARSEABLE", "OUTSIDE_WORLD",
)

#: R5 の CSV の「道路種別」→ 測った道路の階級(辺の klass・**expedient**)。
#: 1/2=高速(歩行グラフに motorway の辺が無い=空)・3/4/6=国道/主要地方道/一般都道(幹線)・
#: それ以外(5=区道 等)=音源の klass 全部。
MEASURED_ROAD_KLASSES: dict[str, tuple[str, ...]] = {
    "1": (),
    "2": (),
    "3": ("primary", "secondary"),
    "4": ("primary", "secondary"),
    "6": ("primary", "secondary"),
}

_KANJI = "〇一二三四五六七八九"
_KANJI_NUM = "一二三四五六七八九十"


def measured_klasses(road_kind: str) -> tuple[str, ...]:
    """R5 の道路種別 → 測った道路の階級(:data:`MEASURED_ROAD_KLASSES`・表に無ければ音源全部)。"""
    return MEASURED_ROAD_KLASSES.get(str(road_kind).strip(), tuple(W.ROAD_KLASSES))


def _kanji_number(n: int) -> str:
    """1..99 → 漢数字(十の位つき)。"""
    if not 1 <= n <= 99:
        raise ValueError(f"丁目の番号が範囲外: {n}")
    tens, ones = divmod(n, 10)
    head = "" if tens == 0 else ("十" if tens == 1 else _KANJI[tens] + "十")
    return head + (_KANJI[ones] if ones else "")


def _parse_kanji_number(s: str) -> int:
    """漢数字(一〜九十九)→ 整数。"""
    if "十" in s:
        a, _, b = s.partition("十")
        tens = 1 if a == "" else _KANJI.index(a)
        return tens * 10 + (0 if b == "" else _KANJI.index(b))
    return _KANJI.index(s)


def parse_address(address: str) -> dict[str, Any]:
    """R5 の所在地 → ``{"ward", "name", "code"}``。**例外を投げない**。

    - 全体に NFKC(全角数字 → 半角)と空白除去だけを掛ける。**町名の中の漢数字は変えない**。
    - ``<町名><番号>丁目``(番号は算用数字か漢数字)→ ``code="CHOME"``・``name=<町名><漢数字>丁目``。
    - 丁目が無く ``<町名><数字>-…``(「神宮前5-53-1」)→ ``code="NO_CHOME_HYPHEN"``・``name=<町名>``
      (丁目の番号か番地か決められない)。
    - 丁目が無く ``<町名><数字>`` か ``<町名>`` だけ(「鉢山町14」)→ ``code="TOWN"``・``name=<町名>``。
    - 区が読めない → ``code="UNPARSEABLE"``・``ward=None``。

    Example:
        >>> parse_address("渋谷区神宮前5丁目53-1")["name"], parse_address("目黒区三田1丁目2")["name"]
        ('神宮前五丁目', '三田一丁目')
        >>> parse_address("渋谷区神宮前5-53-1")["code"], parse_address("渋谷区鉢山町14")["code"]
        ('NO_CHOME_HYPHEN', 'TOWN')
    """
    text = "".join(unicodedata.normalize("NFKC", str(address)).split())
    m = re.match(r"^(?:東京都)?(.+?区)(.*)$", text)
    if not m:
        return {"ward": None, "name": None, "code": "UNPARSEABLE"}
    ward, rest = m.group(1), m.group(2)
    m2 = re.match(rf"^(.+?)(\d+|[{_KANJI_NUM}]+)丁目", rest)
    if m2:
        num = m2.group(2)
        n = int(num) if num.isdigit() else _parse_kanji_number(num)
        if 1 <= n <= 99:
            return {"ward": ward, "name": f"{m2.group(1)}{_kanji_number(n)}丁目", "code": "CHOME"}
    m3 = re.match(r"^(.+?)(\d+)-", rest)
    if m3:
        return {"ward": ward, "name": m3.group(1), "code": "NO_CHOME_HYPHEN"}
    m4 = re.match(r"^(.+?)(\d.*)?$", rest)
    if m4 and m4.group(1):
        return {"ward": ward, "name": m4.group(1), "code": "TOWN"}
    return {"ward": ward, "name": None, "code": "UNPARSEABLE"}


def chome_name_from_address(address: str) -> tuple[str, str]:
    """(互換)R5 の所在地 → (区, 小地域名)。読めなければ :class:`ValueError`(行の処理は
    :func:`parse_address` を使い、例外にしない)。

    Example:
        >>> chome_name_from_address("渋谷区神宮前5丁目53-1")
        ('渋谷区', '神宮前五丁目')
        >>> chome_name_from_address("渋谷区鉢山町14")
        ('渋谷区', '鉢山町')
    """
    p = parse_address(address)
    if p["code"] == "UNPARSEABLE" or p["name"] is None:
        raise ValueError(f"住所が読めない: {address!r}")
    return p["ward"], p["name"]


@dataclass(frozen=True)
class Chome:
    """小地域 1 つ(世界ローカル m)。"""

    key_code: str
    s_name: str
    poly: SH.Polygon
    estat_xy: tuple[float, float]
    area_m2: float


def _lonlat_to_local(lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """.shp の (経度, 緯度) → 世界ローカル m(正典 ``geo.common.latlon_to_local`` をそのまま呼ぶ)。"""
    x, y = G.latlon_to_local(np.asarray(lat, dtype=np.float64), np.asarray(lon, dtype=np.float64))
    return np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)


def load_chome(shp, dbf) -> dict[str, Chome]:
    """小地域境界 → ``{S_NAME: Chome}``(同名が複数あれば例外=曖昧な代表点を作らない)。"""
    polys = SH.read_shp(shp)
    rows = SH.read_dbf(dbf)
    if len(polys) != len(rows):
        raise ValueError(".shp と .dbf の件数が違う")
    out: dict[str, Chome] = {}
    for p, r in zip(polys, rows):
        name = str(r["S_NAME"])
        if name in out:
            raise ValueError(f"小地域名が重複: {name}")
        loc = p.transformed(_lonlat_to_local)
        ex, ey = _lonlat_to_local(np.array([float(r["X_CODE"])]), np.array([float(r["Y_CODE"])]))
        out[name] = Chome(
            key_code=str(r["KEY_CODE"]),
            s_name=name,
            poly=loc,
            estat_xy=(float(ex[0]), float(ey[0])),
            area_m2=SH.polygon_area(loc),
        )
    return out


def polygon_centroid(poly: SH.Polygon) -> tuple[float, float]:
    """面積重心(全リングの符号つき面積で重み付け=穴は引かれる)。

    Example:
        >>> sq = SH.Polygon(np.array([0]), np.array([[0.0, 0.0], [4.0, 0.0], [4.0, 2.0], [0.0, 2.0]]), (0, 0, 4, 2))
        >>> polygon_centroid(sq)
        (2.0, 1.0)
    """
    a_sum = cx_sum = cy_sum = 0.0
    for ring in poly.rings():
        if ring.shape[0] < 3:
            continue
        x, y = ring[:, 0], ring[:, 1]
        x2, y2 = np.roll(x, -1), np.roll(y, -1)
        cross = x * y2 - x2 * y
        a = float(cross.sum()) / 2.0
        if a == 0.0:
            continue
        a_sum += a
        cx_sum += float(((x + x2) * cross).sum()) / 6.0
        cy_sum += float(((y + y2) * cross).sum()) / 6.0
    if a_sum == 0.0:
        raise ValueError("面積 0 のポリゴン")
    return (cx_sum / a_sum, cy_sum / a_sum)


def points_to_segments_min_dist(
    px: np.ndarray, py: np.ndarray, segs: tuple[np.ndarray, ...]
) -> np.ndarray:
    """各点から線分群までの最短距離 [m](線分が無ければ inf)。

    逐次ループ宣言(P4): 点を 512 件ずつ(計測時のみ・点 × 線分のベクトル演算)。
    """
    ax, ay, bx, by = segs[:4]
    px = np.asarray(px, dtype=np.float64)
    py = np.asarray(py, dtype=np.float64)
    out = np.full(px.shape[0], np.inf, dtype=np.float64)
    if ax.size == 0 or px.size == 0:
        return out
    dx = bx - ax
    dy = by - ay
    den = np.where(dx * dx + dy * dy <= 0.0, 1.0, dx * dx + dy * dy)
    for lo in range(0, px.shape[0], 512):
        qx = px[lo : lo + 512, None]
        qy = py[lo : lo + 512, None]
        t = np.clip(((qx - ax) * dx + (qy - ay) * dy) / den, 0.0, 1.0)
        out[lo : lo + 512] = np.hypot(qx - (ax + t * dx), qy - (ay + t * dy)).min(axis=1)
    return out


def measure_near(
    cx: float,
    cy: float,
    px: np.ndarray,
    py: np.ndarray,
    values: Mapping[str, np.ndarray],
    road_dist: np.ndarray,
    radius_m: float,
) -> dict[str, Any]:
    """点 (cx, cy) から半径 ``radius_m`` の中の格子点の代表値(``max``・``road``)。

    Args:
        px, py: 格子点(呼び出し側で GL だけに絞る・格子の番号順)。
        values: 名前(``"day"``/``"night"`` 等)→ 各格子点の値 [dB]。
        road_dist: 各格子点から「測った階級の辺」までの距離 [m](辺が無ければ inf)。

    Returns:
        ``{"n", "max": {名前: 値|None}, "road": {名前: 値|None}, "road_index": 添字|None,
        "road_dist_m": 距離|None, "road_beyond_band": bool|None}``。``road`` は半径内で
        ``road_dist`` が最小の格子点(同距離は**添字の小さい方**)=全ての名前で同じ格子点の値。

    Raises:
        ValueError: 値か距離に NaN がある(距離の inf は「辺なし」として許す)。
    """
    px = np.asarray(px, dtype=np.float64)
    py = np.asarray(py, dtype=np.float64)
    road_dist = np.asarray(road_dist, dtype=np.float64)
    vals = {k: np.asarray(v, dtype=np.float64) for k, v in values.items()}
    if np.isnan(road_dist).any():
        raise ValueError("物差し: 道路までの距離に NaN がある")
    for k, v in vals.items():
        if not np.isfinite(v).all():
            raise ValueError(f"物差し: 騒音場の値({k})に NaN/inf がある")
    inside = np.flatnonzero(np.hypot(px - cx, py - cy) <= radius_m)
    n = int(inside.size)
    out: dict[str, Any] = {
        "n": n,
        "max": {k: None for k in vals},
        "road": {k: None for k in vals},
        "road_index": None,
        "road_dist_m": None,
        "road_beyond_band": None,
    }
    if n == 0:
        return out
    out["max"] = {k: float(v[inside].max()) for k, v in vals.items()}
    rd = road_dist[inside]
    if np.isfinite(rd).any():
        j = int(inside[int(np.argmin(rd))])  # argmin=同距離は最初(添字の小さい方)
        dmin = float(road_dist[j])
        out["road"] = {k: float(v[j]) for k, v in vals.items()}
        out["road_index"] = j
        out["road_dist_m"] = round(dmin, 3)
        out["road_beyond_band"] = bool(dmin > ROAD_BAND_M)
    return out


def ruler_error(
    chome: Chome,
    road_facing_xy: tuple[float, float] | None,
    px: np.ndarray,
    py: np.ndarray,
    day: np.ndarray,
    night: np.ndarray,
    on_measured_road: np.ndarray,
) -> dict[str, Any]:
    """物差しの誤差の見積り(町丁目の大きさ・代表点のずれ・町丁目の中の値の散らばり)。

    Args:
        px, py, day, night: GL の格子点と値。
        on_measured_road: 各格子点の最寄りの辺が測った階級か(bool)。
    """
    cxy = polygon_centroid(chome.poly)
    ex, ey = chome.estat_xy
    inside = SH.points_in_polygon(px, py, chome.poly)
    sel = inside & np.asarray(on_measured_road, dtype=bool)

    def pct(a: np.ndarray) -> dict[str, float] | None:
        if a.size == 0:
            return None
        return {str(p): round(float(np.percentile(a, p)), 1) for p in (5, 50, 95)}

    return {
        "area_m2": round(chome.area_m2, 1),
        "equivalent_radius_m": round(float(np.sqrt(chome.area_m2 / np.pi)), 1),
        "estat_to_centroid_m": round(float(np.hypot(ex - cxy[0], ey - cxy[1])), 1),
        "estat_inside_polygon": bool(
            SH.points_in_polygon(np.array([ex]), np.array([ey]), chome.poly)[0]
        ),
        "estat_to_road_facing_m": (
            None if road_facing_xy is None
            else round(float(np.hypot(ex - road_facing_xy[0], ey - road_facing_xy[1])), 1)
        ),
        "gl_points_in_chome": int(inside.sum()),
        "measured_road_points_in_chome": int(sel.sum()),
        "measured_road_day_pct": pct(np.asarray(day)[sel]),
        "measured_road_night_pct": pct(np.asarray(night)[sel]),
    }


def road_facing_point(
    chome: Chome,
    px: np.ndarray,
    py: np.ndarray,
    on_measured_road: np.ndarray,
) -> tuple[float, float] | None:
    """町丁目の中で最寄りの辺が測った階級の GL 格子点のうち、``estat`` 点に最も近いもの。

    同距離は格子の番号の小さい方(``argmin`` の最初=格子の並び band, iy, ix の安定順)=決定論。
    """
    inside = SH.points_in_polygon(px, py, chome.poly) & np.asarray(on_measured_road, dtype=bool)
    idx = np.flatnonzero(inside)
    if idx.size == 0:
        return None
    ex, ey = chome.estat_xy
    d = np.hypot(px[idx] - ex, py[idx] - ey)
    k = int(idx[int(np.argmin(d))])
    return (float(px[k]), float(py[k]))


def _resolve_chome(parsed: Mapping[str, Any], chome: Mapping[str, Chome], ward: str) -> tuple[str, str | None]:
    """住所の解析結果 → (状態, 小地域名)。"""
    code, name = parsed["code"], parsed["name"]
    if code == "UNPARSEABLE":
        return "UNPARSEABLE", None
    if parsed["ward"] != ward:
        return "NO_BOUNDARY", None
    if code == "CHOME":
        return ("OK", name) if name in chome else ("NAME_NOT_FOUND", None)
    # 丁目の無い書き方: 町そのものが小地域なら採る(鉢山町)。町に丁目があれば曖昧。
    if name in chome and code == "TOWN":
        return "OK", name
    if any(k.startswith(str(name)) and k.endswith("丁目") and k[len(name):-2] and
           all(ch in _KANJI_NUM for ch in k[len(name):-2]) for k in chome):
        return "AMBIGUOUS_NO_CHOME", None
    if name in chome:  # NO_CHOME_HYPHEN だが町に丁目が無い
        return "OK", name
    return "NAME_NOT_FOUND", None


def ruler_rows(
    points: Sequence[Mapping[str, Any]],
    chome: Mapping[str, Chome],
    gx: np.ndarray,
    gy: np.ndarray,
    gday: np.ndarray,
    gnight: np.ndarray,
    gklass: Sequence[str],
    segs_of: Callable[[tuple[str, ...]], tuple[np.ndarray, ...]],
    ward: str = "渋谷区",
    radii: Sequence[float] = RADII_M,
) -> list[dict[str, Any]]:
    """R5 の点ごとに物差しを測る(計測の道具とテストが同じ関数を通る)。

    Args:
        points: :func:`w10_noise.read_r5_points` の行(``address``・``road_kind``・実測)。
        chome: :func:`load_chome` の結果(``ward`` の区のもの)。
        gx, gy, gday, gnight: **GL の**街路格子点とその騒音場の値 [dB](格子の番号順)。
        gklass: 各格子点の最寄りの辺の klass。
        segs_of: 階級の組 → その辺の線分 ``(ax, ay, bx, by, owner)``。

    Returns:
        点ごとの行。``status`` は :data:`STATUSES`(例外にしない)。差は ``diff[rep][stat][r]`` =
        ``[昼, 夜]``(値 − 実測・値が無ければ None)。``road`` の距離と印は
        ``road_dist_m[rep][r]``・``road_beyond_band[rep][r]``。
    """
    gx = np.asarray(gx, dtype=np.float64)
    gy = np.asarray(gy, dtype=np.float64)
    gday = np.asarray(gday, dtype=np.float64)
    gnight = np.asarray(gnight, dtype=np.float64)
    gk = np.asarray(list(gklass))
    rows: list[dict[str, Any]] = []
    rmax = float(max(radii))
    for p in points:
        parsed = parse_address(p["address"])
        status, name = _resolve_chome(parsed, chome, ward)
        klasses = measured_klasses(p["road_kind"])
        row: dict[str, Any] = {
            "no": p["no"],
            "status": status,
            "address_form": parsed["code"],
            "chome": name,
            "ward": parsed["ward"],
            "road_kind": p["road_kind"],
            "measured_klasses": list(klasses),
            "measured_day_db": p["measured_day_db"],
            "measured_night_db": p["measured_night_db"],
        }
        if status != "OK":
            rows.append(row)
            continue
        ch = chome[name]
        row["estat_xy"] = [round(ch.estat_xy[0], 1), round(ch.estat_xy[1], 1)]
        if not SH.points_in_polygon(gx, gy, ch.poly).any():
            row["status"] = "OUTSIDE_WORLD"  # 町丁目に街路格子が 1 点も無い(世界の範囲の外)
            rows.append(row)
            continue
        on_road = np.isin(gk, list(klasses)) if klasses else np.zeros(gk.shape, dtype=bool)
        rf = road_facing_point(ch, gx, gy, on_road)
        reps: dict[str, tuple[float, float] | None] = {"estat": ch.estat_xy, "road_facing": rf}
        segs = segs_of(tuple(klasses))
        row["rep_xy"] = {k: (None if v is None else [round(v[0], 1), round(v[1], 1)]) for k, v in reps.items()}
        row["values"] = {}
        row["diff"] = {}
        row["road_dist_m"] = {}
        row["road_beyond_band"] = {}
        for rep, xy in reps.items():
            row["values"][rep] = {}
            row["diff"][rep] = {s: {} for s in STATISTICS}
            row["road_dist_m"][rep] = {}
            row["road_beyond_band"][rep] = {}
            if xy is None:
                continue
            near = np.flatnonzero(np.hypot(gx - xy[0], gy - xy[1]) <= rmax)  # 昇順=格子の番号順
            rd = points_to_segments_min_dist(gx[near], gy[near], segs)
            for r in radii:
                key = str(int(r))
                m = measure_near(xy[0], xy[1], gx[near], gy[near],
                                 {"day": gday[near], "night": gnight[near]}, rd, r)
                row["values"][rep][key] = {
                    "n": m["n"], "road_dist_m": m["road_dist_m"], "road_beyond_band": m["road_beyond_band"],
                    **{f"{s}_{t}": m[s][t] for s in STATISTICS for t in ("day", "night")},
                }
                row["road_dist_m"][rep][key] = m["road_dist_m"]
                row["road_beyond_band"][rep][key] = m["road_beyond_band"]
                for s in STATISTICS:
                    d, nt = m[s]["day"], m[s]["night"]
                    row["diff"][rep][s][key] = (
                        None if d is None or nt is None
                        else [round(d - p["measured_day_db"], 1), round(nt - p["measured_night_db"], 1)]
                    )
        row["error"] = ruler_error(ch, rf, gx, gy, gday, gnight, on_road)
        rows.append(row)
    return rows


def ruler_from_world(world_dir: Path, data_dir: Path) -> list[dict[str, Any]]:
    """世界ディレクトリ(W10 の出力と W1 の辺)+ 入力データ根 → :func:`ruler_rows` の行。

    読むもの: ``w10_street_points.parquet``・``w10_noise_day.npy``・``w10_noise_night.npy``・
    ``w1_edges.parquet``・``w1_edge_geometry.npz``・小地域境界・R5 の CSV。
    """
    import pyarrow.parquet as pq

    world_dir = Path(world_dir)
    data_dir = Path(data_dir)
    d = pq.read_table(world_dir / "w10_street_points.parquet").to_pydict()
    gl = np.asarray([b == "GL" for b in d["band"]], dtype=bool)
    edges = C.read_parquet_columns(world_dir / "w1_edges.parquet", ["edge_idx", "klass", "geom_start", "geom_count"])
    coords = np.load(world_dir / "w1_edge_geometry.npz")["coords"]
    klass_of = {int(e): k for e, k in zip(edges["edge_idx"], edges["klass"])}
    gk = [klass_of[int(e)] for e in np.asarray(d["nearest_edge_idx"])[gl]]
    day = np.load(world_dir / "w10_noise_day.npy").astype(np.float64)[gl]
    night = np.load(world_dir / "w10_noise_night.npy").astype(np.float64)[gl]
    cache: dict[tuple[str, ...], tuple[np.ndarray, ...]] = {}

    def segs_of(klasses: tuple[str, ...]) -> tuple[np.ndarray, ...]:
        if klasses not in cache:
            want = set(klasses)
            keep = [int(e) for e, k in zip(edges["edge_idx"], edges["klass"]) if k in want]
            cache[klasses] = segment_arrays(edges["edge_idx"], edges["geom_start"], edges["geom_count"], coords, keep=keep)
        return cache[klasses]

    chome = load_chome(data_dir.joinpath(*BOUNDARY_SHP), data_dir.joinpath(*BOUNDARY_DBF))
    pts = W.read_r5_points(data_dir.joinpath(*W.R5_POINTS))
    return ruler_rows(
        pts, chome, np.asarray(d["x"], np.float64)[gl], np.asarray(d["y"], np.float64)[gl], day, night, gk, segs_of
    )


def summarize_diffs(diffs: Sequence[Sequence[float] | None]) -> dict[str, Any]:
    """点ごとの差(``[昼, 夜]`` or None)→ 平均・平均絶対値(評価できた点だけ)。"""
    vals = [v for v in diffs if v is not None]
    if not vals:
        return {"n": 0, "mean_day": None, "mean_night": None, "mean_abs_day": None, "mean_abs_night": None}
    d = np.array([v[0] for v in vals], dtype=np.float64)
    n = np.array([v[1] for v in vals], dtype=np.float64)
    return {
        "n": len(vals),
        "mean_day": round(float(d.mean()), 2),
        "mean_night": round(float(n.mean()), 2),
        "mean_abs_day": round(float(np.abs(d).mean()), 2),
        "mean_abs_night": round(float(np.abs(n).mean()), 2),
    }
