# -*- coding: utf-8 -*-
"""c7lib — C7(40万体×1シミュ日・本番相当)受入計器の純関数。

位置づけ
    ``tools/c7/*.py`` の 3 本(在圏時系列・holdout 照合・受入表)が共有する
    「計算の部分」だけを集めた。**実サーバー接続も乱数の副作用も置かない**。
    ``tests/c7`` がこのモジュールをモック入力・**合成 holdout**で検査する。
    数値ユーティリティ(JSD・相関・表・出力)は ``tools/c6/c6lib`` を再利用する
    (新規依存を作らないため。c6lib は標準ライブラリ + numpy のみ)。

正典(数値・規則の出どころ)
- 実装計画書 §9.1 **C7**「サーバーで1日ラン(週7日表・第1陣全部)・壁時計≤24h・
  M8≤24GB・S1≤5GB・診断行・**holdout照合は事後1回のみ**(KDDI形状5指標)/
  検収=予算全行・決定論(同seed再ラン=T2)・被覆指標WC-6」。
- 予算宣言表 **W1**(≤24時間/シミュ日)・**M8**(RSS ≤24GB)・**S1**(恒久記録 ≤5GB/シミュ日)・
  **P2**(移動+密度 ≤5ms/フレーム)・**L4**(呼数)。行の文面は Markdown 側が正典
  (``shibuya.core.budget`` で読む=数値をここに複製しない)。
- 境界・経済設計書 **§1.4**「検証専用(触らない)= KDDI滞在人口の**形状5指標
  (相関・ピーク時刻・平日休日比・エリア構成・属性構成)**」= holdout。
- パターン台帳 **D1′**「判定=(i)エリア別24時間シェアのJSD (ii)ピーク時刻の順序関係
  (iii)深夜残存率の順序関係。**閾値根拠=実測の年次変動JSD 0.0001-0.0012**。
  値は**形状と比のみ**(絶対水準不使用)」。
- 世界データ構築仕様書 **§0-5 / D-W13**「KDDI形状5指標…は構築に**一切使わない**
  (総量1スカラーのみ)」。
- 方法論「世界被覆指標」**WC-5(過剰)/WC-6(孤児)のみゲート**。
- 5エリアの区分と分割線: 渋谷駅中心地区まちづくり指針2010 p.11-12/p.17-18 と
  ``docs/research/v2-area-boundary-definition.md`` / ``v2-area-boundary-map-reading.md``。

自前の細部(expedient・実装計画書 §8 登録簿へ写した)
- **セル→5エリア写像**: 公的なポリゴンが存在しないため ``area_axes_v0.json`` の
  折れ線 3 本 + 中心矩形 + 外縁楕円で近似する(E-C7-2)。
- **形状5指標の操作定義と合格線**: §1.4 は 5 つの**名前**しか与えていないので、
  計算式と合格線は本モジュールの提案(``PREREG_V0``)= **事前登録案**(親判断待ち)。
- **平日休日比は測定不能**: KDDI 6 レイヤに曜日軸が無い(d1_reacquisition 結論3)。
  代替として D1′ の**深夜残存率の順序**を置く(``H3`` の ``substituted=True``)。
- **種別→KDDI属性の写像**(``KIND_TO_ATTR``)。
- **JSD の底**: ``c6lib.jsd`` の既定 base=2(bits)。D1′ の閾値 0.0001-0.0012 が
  どの底で算出されたかは答申に書かれていない=**親の確認事項**(自然対数なら ×ln2)。
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

# ---------------------------------------------------------------- 経路(src と c6lib を見つける)

_HERE = Path(os.path.abspath(__file__)).parent
REPO_ROOT = _HERE.parent.parent
_SRC = REPO_ROOT / "src"
_TOOLS_C6 = REPO_ROOT / "tools" / "c6"
for _p in (str(_SRC), str(_TOOLS_C6)):
    if _p not in sys.path:  # pragma: no cover - 実行時の経路
        sys.path.insert(0, _p)

import c6lib  # noqa: E402  (sys.path 調整のあと)

jsd = c6lib.jsd
pearson = c6lib.pearson
spearman = c6lib.spearman
markdown_table = c6lib.markdown_table
write_outputs = c6lib.write_outputs

# ---------------------------------------------------------------- 5エリア

#: 5 エリアの id(SCJ 01-05 = 指針2010 エリア⑤④①②③)。**順序は固定**(表・ベクトルの列順)。
AREA_IDS: tuple[str, ...] = ("central", "northwest", "northeast", "southeast", "southwest")
#: 公式表記(渋谷区オープンデータ「滞在人口は以下の5エリアを対象としています」)。
AREA_JA: dict[str, str] = {
    "central": "渋谷駅中心エリア",
    "northwest": "渋谷駅北西エリア",
    "northeast": "渋谷駅北東エリア",
    "southeast": "渋谷駅南東エリア",
    "southwest": "渋谷駅南西エリア",
}
#: 5 エリアの外(bbox は 139ha 区域の約2.7倍ある)。
OUTSIDE: int = -1

#: KDDI の時間帯区分(**5時〜28時 = 24 区分**・d1_reacquisition §3-3)。
KDDI_HOUR_BINS: tuple[int, ...] = tuple(range(5, 29))

#: KDDI「渋谷との関係」の 3 属性。
ATTR_IDS: tuple[str, ...] = ("worker", "resident", "visitor")
ATTR_JA: dict[str, str] = {"worker": "勤務者", "resident": "居住者", "visitor": "来街者"}

#: ``agents.state.AgentKind`` → KDDI 属性(**expedient**: KDDI は自宅/勤務地の推定で
#: 3 分類する。舞台内に住み舞台内で働く WORKER は「居住者」側に置く。STUDENT は
#: 域外常住なので「来街者」側。感度は ``--attr-map`` で差し替えて測る)。
KIND_TO_ATTR: dict[int, str] = {
    0: "worker",     # COMMUTER   域外常住・舞台内勤務
    1: "visitor",    # VISITOR
    2: "resident",   # WORKER     舞台に常住し舞台内に勤める
    3: "resident",   # RESIDENT
    4: "worker",     # DISPATCHER 指令
    5: "visitor",    # STUDENT    域外常住・舞台内通学
    6: "visitor",    # REGULAR_VISITOR
    7: "visitor",    # FOREIGN_VISITOR
    8: "worker",     # CREW       乗務員・職務者
}

#: 深夜帯(D1b/D1′ の「深夜残存率」= 1時台〜4時台)。
NIGHT_HOURS: tuple[int, ...] = (1, 2, 3, 4)

DEFAULT_AXES_PATH = _HERE / "area_axes_v0.json"


# ---------------------------------------------------------------- 幾何(local-m 平面)


@dataclass(frozen=True)
class LocalPlane:
    """PLATEAU 原点の局所平面(A7「座標系=PLATEAU原点の局所平面を全データで共有」)。"""

    origin_lat: float
    origin_lon: float
    m_per_deg_lat: float
    m_per_deg_lon: float

    @classmethod
    def from_crs_json(cls, path: str | Path) -> "LocalPlane":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        lat, lon = d["origin_latlon"]
        return cls(float(lat), float(lon), float(d["m_per_deg_lat"]), float(d["m_per_deg_lon"]))

    @classmethod
    def from_axes(cls, axes: Mapping[str, Any]) -> "LocalPlane":
        lat, lon = axes["origin_latlon"]
        return cls(
            float(lat), float(lon),
            float(axes["m_per_deg_lat"]), float(axes["m_per_deg_lon"]),
        )

    def to_xy(self, lat: float, lon: float) -> tuple[float, float]:
        return (
            (float(lon) - self.origin_lon) * self.m_per_deg_lon,
            (float(lat) - self.origin_lat) * self.m_per_deg_lat,
        )

    def many(self, latlon: Sequence[Sequence[float]]) -> np.ndarray:
        return np.array([self.to_xy(a, b) for a, b in latlon], dtype=np.float64)


def polyline_side(px: np.ndarray, py: np.ndarray, line: np.ndarray) -> np.ndarray:
    """折れ線に対する点の**符号つき側**(最近傍セグメントの外積の符号)。

    Args:
        px / py: 点の座標 ``(n,)``[m]。
        line: 折れ線 ``(k, 2)``(順序が向き=左右の定義)。

    Returns:
        ``(n,)`` float。>0 = 進行方向の左、<0 = 右。0 は線上。

    Note:
        「最近傍セグメント」で決めるので、折れ線が大きく折り返す形だと不定になる。
        本用途(JR線・幹線道路の緩い折れ線)では安全側。
    """
    p = np.stack([np.asarray(px, dtype=np.float64), np.asarray(py, dtype=np.float64)], axis=1)
    a = line[:-1]
    b = line[1:]
    seg = b - a                                        # (k-1, 2)
    seg_len2 = np.maximum((seg ** 2).sum(axis=1), 1e-9)
    w = p[:, None, :] - a[None, :, :]                  # (n, k-1, 2)
    t = np.clip((w * seg[None, :, :]).sum(axis=2) / seg_len2[None, :], 0.0, 1.0)
    foot = a[None, :, :] + t[:, :, None] * seg[None, :, :]
    d2 = ((p[:, None, :] - foot) ** 2).sum(axis=2)     # (n, k-1)
    best = np.argmin(d2, axis=1)
    sx, sy = seg[best, 0], seg[best, 1]
    wx = p[:, 0] - a[best, 0]
    wy = p[:, 1] - a[best, 1]
    return sx * wy - sy * wx


def load_axes(path: str | Path | None = None) -> dict[str, Any]:
    """``area_axes_v0.json`` を読む(素の dict・改変しない)。"""
    return json.loads(Path(path or DEFAULT_AXES_PATH).read_text(encoding="utf-8"))


def classify_cells(
    cx: Sequence[float],
    cy: Sequence[float],
    axes: Mapping[str, Any],
    *,
    dilate_m: float = 0.0,
) -> np.ndarray:
    """セル代表点 → 5エリア索引(``AREA_IDS`` の位置)/ ``OUTSIDE``。**純関数**。

    規則(``area_axes_v0.json`` の宣言をそのまま実行する):
      1. 外縁楕円の外 → ``OUTSIDE``
      2. 中心矩形の中 → ``central``
      3. それ以外 → JR 線の西/東 × (西なら玉川通り・東なら六本木通り)の北/南

    Args:
        cx / cy: セル代表点[m](local-m)。
        axes: ``load_axes()`` の戻り。
        dilate_m: 外縁楕円と中心矩形を膨張(正)/収縮(負)させる量[m]。
            地図読み取り誤差の感度試験(±50m)用。

    Returns:
        ``(n,)`` int8。
    """
    plane = LocalPlane.from_axes(axes)
    x = np.asarray(cx, dtype=np.float64)
    y = np.asarray(cy, dtype=np.float64)
    out = np.full(x.size, OUTSIDE, dtype=np.int8)

    outer = axes["outer"]
    ox, oy = plane.to_xy(*outer["center_latlon"])
    a, b = (float(v) + float(dilate_m) for v in outer["semi_axis_m"])
    inside_outer = ((x - ox) / a) ** 2 + ((y - oy) / b) ** 2 <= 1.0

    cen = axes["central"]
    kx, ky = plane.to_xy(*cen["center_latlon"])
    hx, hy = (float(v) + float(dilate_m) for v in cen["half_size_m"])
    inside_central = (np.abs(x - kx) <= hx) & (np.abs(y - ky) <= hy)

    ns = plane.many(axes["axes"]["ns_jr"]["waypoints_latlon"])
    ew_w = plane.many(axes["axes"]["ew_west_r246"]["waypoints_latlon"])
    ew_e = plane.many(axes["axes"]["ew_east_roppongi"]["waypoints_latlon"])

    # ns_jr は北→南の順 = 進行方向の右が西 → cross < 0 が西。
    west = polyline_side(x, y, ns) < 0.0
    # ew_* は西→東の順 = 進行方向の左が北 → cross > 0 が北。
    north_w = polyline_side(x, y, ew_w) > 0.0
    north_e = polyline_side(x, y, ew_e) > 0.0
    north = np.where(west, north_w, north_e)

    idx = {name: i for i, name in enumerate(AREA_IDS)}
    quad = np.where(
        west,
        np.where(north, idx["northwest"], idx["southwest"]),
        np.where(north, idx["northeast"], idx["southeast"]),
    ).astype(np.int8)

    out[inside_outer] = quad[inside_outer]
    out[inside_outer & inside_central] = idx["central"]
    return out


# ---------------------------------------------------------------- セル→エリア表


@dataclass
class AreaMap:
    """セル索引 → 5エリア。エンジンのセル順(``w2_cells.parquet`` の行順)に一致する。"""

    place_ids: tuple[str, ...]
    area_of_cell: np.ndarray            # (n_cells,) int8・OUTSIDE=-1
    cell_x: np.ndarray                  # (n_cells,) float64[m]
    cell_y: np.ndarray
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def n_cells(self) -> int:
        return int(self.area_of_cell.size)

    def counts(self) -> dict[str, int]:
        """エリア別のセル数(``outside`` を含む)。"""
        out = {name: int((self.area_of_cell == i).sum()) for i, name in enumerate(AREA_IDS)}
        out["outside"] = int((self.area_of_cell == OUTSIDE).sum())
        return out

    def area_ha(self, cell_m: float = 100.0) -> dict[str, float]:
        """エリア別の面積[ha]。**地表(GL)だけを数える**(UG/DECK は同じ地面の重複)。

        ``place_id`` の末尾が band なので ``_GL`` で終わるセルだけを数える。
        """
        cell_ha = (cell_m * cell_m) / 10_000.0
        gl = np.array([pid.endswith("_GL") for pid in self.place_ids], dtype=bool)
        return {
            name: round(float(((self.area_of_cell == i) & gl).sum()) * cell_ha, 3)
            for i, name in enumerate(AREA_IDS)
        }

    def to_json(self) -> dict[str, Any]:
        return {
            "schema": "shibuya.tools.c7/area_map/1",
            "n_cells": self.n_cells,
            "area_ids": list(AREA_IDS),
            "place_ids": list(self.place_ids),
            "area_of_cell": [int(v) for v in self.area_of_cell.tolist()],
            "counts": self.counts(),
            "area_ha": self.area_ha(),
            "meta": self.meta,
        }

    @classmethod
    def from_json(cls, doc: Mapping[str, Any]) -> "AreaMap":
        n = int(doc["n_cells"])
        meta = dict(doc.get("meta", {}))
        xy = meta.get("cell_xy")
        if xy:
            arr = np.asarray(xy, dtype=np.float64)
            cx, cy = arr[:, 0], arr[:, 1]
        else:
            cx = cy = np.zeros(n, dtype=np.float64)
        return cls(
            place_ids=tuple(doc["place_ids"]),
            area_of_cell=np.asarray(doc["area_of_cell"], dtype=np.int8),
            cell_x=cx,
            cell_y=cy,
            meta=meta,
        )


def build_area_map(
    place_ids: Sequence[str],
    ix: Sequence[int],
    iy: Sequence[int],
    axes: Mapping[str, Any],
    *,
    cell_m: float = 100.0,
    grid_origin_xy: tuple[float, float] = (0.0, 0.0),
    dilate_m: float = 0.0,
) -> AreaMap:
    """W2 セル(格子索引)→ ``AreaMap``。**純関数**(parquet も IO も触らない)。

    代表点は**格子中心**((ix+0.5)·cell_m)。``centroid_x/y`` はノード配置に依存して
    セル内で偏るので、境界判定には格子中心を使う(``occupancy_series.py --use-centroid``
    で切り替えられる)。
    """
    gx = (np.asarray(ix, dtype=np.float64) + 0.5) * cell_m + grid_origin_xy[0]
    gy = (np.asarray(iy, dtype=np.float64) + 0.5) * cell_m + grid_origin_xy[1]
    area = classify_cells(gx, gy, axes, dilate_m=dilate_m)
    meta = {
        "axes_version": axes.get("version"),
        "axes_status": axes.get("status"),
        "dilate_m": float(dilate_m),
        "rep_point": "grid_center",
        "cell_m": float(cell_m),
    }
    return AreaMap(tuple(place_ids), area, gx, gy, meta)


def area_ha_gate(amap: AreaMap, axes: Mapping[str, Any]) -> dict[str, Any]:
    """写像の自己検査: エリア別面積が地図読み取りの目安帯に入るか。

    公的ポリゴンが無い以上「正解との一致」は測れない。代わりに**独立に読み取られた
    面積の目安**(北西≈50-60ha 等)を帯にして、写像が破綻していないことだけ見る。
    """
    ha = amap.area_ha(float(amap.meta.get("cell_m", 100.0)))
    bands = axes.get("area_ha_bands", {})
    rows = []
    ok_all = True
    for name in AREA_IDS:
        lo, hi = bands.get(name, (0.0, math.inf))
        ok = float(lo) <= ha[name] <= float(hi)
        ok_all = ok_all and ok
        rows.append({"area": name, "ha": ha[name], "band": [lo, hi], "ok": bool(ok)})
    total = round(sum(ha.values()), 3)
    return {
        "per_area": rows,
        "total_ha": total,
        "total_band": [110.0, 170.0],
        "total_ok": bool(110.0 <= total <= 170.0),
        "ok": bool(ok_all and 110.0 <= total <= 170.0),
    }


# ---------------------------------------------------------------- 在圏時系列


@dataclass
class OccupancySeries:
    """ランから作った在圏時系列(**形状のみ**を後段へ渡す)。"""

    #: 標本の tick(昇順)。
    ticks: np.ndarray
    #: ``(n_samples, n_cells)`` int32 のセル別在圏数。
    cell_counts: np.ndarray
    #: ``(n_samples, 5, 3)`` int32 のエリア×属性別在圏数(取れないランは空)。
    area_attr: np.ndarray | None = None
    #: 1 tick の秒数(既定 60)。
    tick_seconds: int = 60
    #: シミュ日の開始時刻(時)。``run_day`` は 00:00 開始。
    start_hour: int = 0
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def n_samples(self) -> int:
        return int(self.ticks.size)

    def hour_of_sample(self) -> np.ndarray:
        """標本 → 世界内の時(0-23)。"""
        minutes = self.ticks.astype(np.int64) * self.tick_seconds // 60
        return ((minutes // 60) + self.start_hour) % 24

    def by_area(self, amap: AreaMap) -> np.ndarray:
        """``(n_samples, 5)`` のエリア別在圏数(``OUTSIDE`` は落とす)。"""
        if self.cell_counts.shape[1] != amap.n_cells:
            raise ValueError(
                f"セル数が違う: series {self.cell_counts.shape[1]} vs map {amap.n_cells}"
            )
        out = np.zeros((self.n_samples, len(AREA_IDS)), dtype=np.int64)
        for i in range(len(AREA_IDS)):
            sel = amap.area_of_cell == i
            if sel.any():
                out[:, i] = self.cell_counts[:, sel].sum(axis=1)
        return out

    def area_hour_table(self, amap: AreaMap) -> np.ndarray:
        """``(24, 5)`` の**時×エリア**在圏数(同じ時の標本は平均)。行索引=世界内の時 0-23。"""
        per_area = self.by_area(amap).astype(np.float64)
        hours = self.hour_of_sample()
        table = np.zeros((24, len(AREA_IDS)), dtype=np.float64)
        n = np.zeros(24, dtype=np.float64)
        np.add.at(table, hours, per_area)
        np.add.at(n, hours, 1.0)
        return table / np.maximum(n, 1.0)[:, None]

    def attr_table(self) -> np.ndarray | None:
        """``(5, 3)`` のエリア×属性 在圏数(1日合計)。取れないランは None。"""
        if self.area_attr is None:
            return None
        return np.asarray(self.area_attr, dtype=np.float64).sum(axis=0)

    def to_json(self, amap: AreaMap | None = None) -> dict[str, Any]:
        doc: dict[str, Any] = {
            "schema": "shibuya.tools.c7/occupancy/1",
            "n_samples": self.n_samples,
            "n_cells": int(self.cell_counts.shape[1]),
            "tick_seconds": self.tick_seconds,
            "start_hour": self.start_hour,
            "ticks": [int(t) for t in self.ticks.tolist()],
            "meta": self.meta,
        }
        if amap is not None:
            tbl = self.area_hour_table(amap)
            doc["area_ids"] = list(AREA_IDS)
            doc["area_hour_counts"] = [[round(float(v), 3) for v in row] for row in tbl]
            doc["area_hour_share"] = [
                [round(float(v), 8) for v in row] for row in hour_share(tbl)
            ]
            at = self.attr_table()
            if at is not None:
                doc["attr_ids"] = list(ATTR_IDS)
                doc["area_attr_counts"] = [[float(v) for v in row] for row in at]
        return doc


def sample_ticks(ticks: int, every: int) -> np.ndarray:
    """標本 tick(``every`` の倍数・最終 tick を必ず含めない=時×24 を崩さないため)。"""
    if every <= 0:
        raise ValueError("every は正")
    return np.arange(0, int(ticks), int(every), dtype=np.int64)


def counts_to_area_attr(
    cell: np.ndarray, kind: np.ndarray, amap: AreaMap, attr_map: Mapping[int, str] | None = None
) -> np.ndarray:
    """個体の (cell, kind) → ``(5, 3)`` エリア×属性 在圏数。**純関数**。"""
    m = dict(KIND_TO_ATTR if attr_map is None else attr_map)
    attr_idx = {name: i for i, name in enumerate(ATTR_IDS)}
    lut = np.full(max(m) + 1 if m else 1, -1, dtype=np.int8)
    for k, a in m.items():
        lut[int(k)] = attr_idx[a]
    c = np.asarray(cell, dtype=np.int64)
    k = np.clip(np.asarray(kind, dtype=np.int64), 0, lut.size - 1)
    ok = (c >= 0) & (c < amap.n_cells)
    area = np.full(c.size, OUTSIDE, dtype=np.int64)
    area[ok] = amap.area_of_cell[c[ok]]
    a = lut[k].astype(np.int64)
    sel = (area >= 0) & (a >= 0)
    flat = np.bincount(
        area[sel] * len(ATTR_IDS) + a[sel], minlength=len(AREA_IDS) * len(ATTR_IDS)
    )
    return flat[: len(AREA_IDS) * len(ATTR_IDS)].reshape(len(AREA_IDS), len(ATTR_IDS)).astype(
        np.int64
    )


# ---------------------------------------------------------------- 形状の量


def hour_share(table: np.ndarray) -> np.ndarray:
    """``(24, 5)`` の在圏数 → ``(5, 24)`` の**エリアごとに正規化した時刻シェア**。

    D1′「値は**形状と比のみ**(絶対水準不使用)」の実装点。
    """
    t = np.asarray(table, dtype=np.float64)
    col = t.sum(axis=0)
    col = np.where(col > 0.0, col, 1.0)
    return (t / col[None, :]).T


def area_share(table: np.ndarray) -> np.ndarray:
    """``(24, 5)`` → ``(5,)`` の 1 日合計のエリア構成シェア。"""
    t = np.asarray(table, dtype=np.float64).sum(axis=0)
    s = t.sum()
    return t / s if s > 0 else np.full(t.size, 1.0 / max(1, t.size))


def peak_hours(share: np.ndarray, hours: Sequence[int] | None = None) -> np.ndarray:
    """``(5, 24)`` シェア → 各エリアのピーク時刻(0-23)。"""
    h = np.arange(24) if hours is None else np.asarray(hours)
    return h[np.argmax(np.asarray(share, dtype=np.float64), axis=1)]


def night_residual(share: np.ndarray, night: Sequence[int] = NIGHT_HOURS) -> np.ndarray:
    """``(5, 24)`` シェア → 深夜残存率 = 深夜帯の平均シェア ÷ 終日平均シェア(=1/24)。"""
    s = np.asarray(share, dtype=np.float64)
    return s[:, list(night)].mean(axis=1) * 24.0


def kendall_tau(a: Sequence[float], b: Sequence[float]) -> float:
    """タウ-b(同順位を扱う・SciPy なし)。順序関係の一致を測る(D1′ (ii)(iii))。"""
    x = np.asarray(a, dtype=np.float64)
    y = np.asarray(b, dtype=np.float64)
    n = x.size
    if n < 2 or y.size != n:
        return float("nan")
    conc = disc = tx = ty = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            dx = np.sign(x[i] - x[j])
            dy = np.sign(y[i] - y[j])
            if dx == 0 and dy == 0:
                tx += 1
                ty += 1
            elif dx == 0:
                tx += 1
            elif dy == 0:
                ty += 1
            elif dx * dy > 0:
                conc += 1
            else:
                disc += 1
    n0 = n * (n - 1) / 2.0
    den = math.sqrt(max(n0 - tx, 0.0) * max(n0 - ty, 0.0))
    return float((conc - disc) / den) if den > 0 else float("nan")


# ---------------------------------------------------------------- 形状5指標(事前登録案)

#: **事前登録案 v0**(親判断待ち)。境界・経済設計書 §1.4 の 5 つの名前に、計算式と合格線を当てた。
#:
#: 合格線の根拠:
#:   - ``jsd_reject``  = 0.0122 = **v1 テンプレ(破棄済みの旧 D1 基盤)と KDDI 実測の JSD**
#:     (d1_reacquisition ①結論2 の表: 2024 比較で 0.01225)。「捨てた基盤より良いこと」が
#:     最低条件=**下限対照**。これを超えたら不合格。
#:   - ``jsd_target`` = 0.0012 = **KDDI 実測の年次変動 JSD の上端**(D1′ の閾値根拠)。
#:     データ側のノイズ床=到達目標(合格線ではない)。
#:   - ピーク時刻 ±1h・順序 τ≥0.6・シェア差 ≤0.05 等は**自前(expedient・根拠なし)**。
PREREG_V0: dict[str, Any] = {
    "version": "v0-proposal",
    "status": "事前登録案(親判断待ち)",
    "jsd_base": 2.0,
    "jsd_reject": 0.0122,
    "jsd_target": 0.0012,
    "H1": {"name": "相関", "jsd_area_hour_mean_max": 0.0122, "pearson_min": 0.80},
    "H2": {"name": "ピーク時刻", "abs_hour_diff_max": 1, "n_within_min": 5, "tau_min": 0.60},
    "H3": {
        "name": "平日休日比",
        "substituted": True,
        "substitute": "深夜残存率(1-4時平均÷終日平均)の値と順序",
        "abs_diff_max": 0.05,
        "tau_min": 0.60,
        "reason": "KDDI 6レイヤに曜日軸が無い(d1_reacquisition 結論3・④未発見1)=測定不能",
    },
    "H4": {"name": "エリア構成", "jsd_max": 0.0122, "abs_share_diff_max": 0.05},
    "H5": {"name": "属性構成", "jsd_mean_max": 0.02, "abs_share_diff_max": 0.10},
}


def _pass(value: float, limit: float, *, upper: bool = True) -> bool:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return False
    return bool(value <= limit) if upper else bool(value >= limit)


def five_metrics(
    sim_table: np.ndarray,
    obs_share: np.ndarray,
    *,
    sim_attr: np.ndarray | None = None,
    obs_attr: np.ndarray | None = None,
    obs_area_share: np.ndarray | None = None,
    prereg: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """**形状5指標**(境界・経済設計書 §1.4)を計算する。**純関数**。

    Args:
        sim_table: ラン側 ``(24, 5)`` の在圏数(時×エリア)。
        obs_share: holdout 側 ``(5, 24)`` の時刻シェア(**形状のみ**)。
        sim_attr / obs_attr: ``(5, 3)`` のエリア×属性 在圏数/シェア(None なら H5 は未測定)。
        obs_area_share: holdout 側 ``(5,)`` のエリア構成シェア(None なら H4 は未測定)。
        prereg: 合格線(既定 ``PREREG_V0``)。

    Returns:
        ``{"H1": {...}, ..., "pass": bool, "n_measured": int}``。
        **絶対水準は一切返さない**(シェア・順位・差だけ)。
    """
    pr = dict(PREREG_V0 if prereg is None else prereg)
    base = float(pr.get("jsd_base", 2.0))
    sim_share = hour_share(sim_table)
    obs = np.asarray(obs_share, dtype=np.float64)
    if obs.shape != sim_share.shape:
        raise ValueError(f"形が違う: sim {sim_share.shape} vs obs {obs.shape}")

    # --- H1 相関 -------------------------------------------------
    per_area_jsd = [float(jsd(sim_share[i], obs[i], base=base)) for i in range(len(AREA_IDS))]
    r = float(pearson(sim_share.ravel().tolist(), obs.ravel().tolist()))
    h1_lim = pr["H1"]
    h1 = {
        "name": h1_lim["name"],
        "per_area_jsd": {AREA_IDS[i]: round(v, 6) for i, v in enumerate(per_area_jsd)},
        "jsd_mean": round(float(np.mean(per_area_jsd)), 6),
        "jsd_max": round(float(np.max(per_area_jsd)), 6),
        "pearson_r": round(r, 6),
        "limit": {
            "jsd_mean_max": h1_lim["jsd_area_hour_mean_max"],
            "pearson_min": h1_lim["pearson_min"],
        },
        "pass": bool(
            _pass(float(np.mean(per_area_jsd)), float(h1_lim["jsd_area_hour_mean_max"]))
            and _pass(r, float(h1_lim["pearson_min"]), upper=False)
        ),
        "measured": True,
    }

    # --- H2 ピーク時刻 -------------------------------------------
    sp = peak_hours(sim_share)
    op = peak_hours(obs)
    # 時刻の差は 24 時周期(0時と23時は 1 時間差)。
    diff = np.minimum(np.abs(sp - op), 24 - np.abs(sp - op))
    h2_lim = pr["H2"]
    tau2 = kendall_tau(sp.tolist(), op.tolist())
    h2 = {
        "name": h2_lim["name"],
        "sim_peak_hour": {AREA_IDS[i]: int(sp[i]) for i in range(len(AREA_IDS))},
        "obs_peak_hour": {AREA_IDS[i]: int(op[i]) for i in range(len(AREA_IDS))},
        "abs_hour_diff": {AREA_IDS[i]: int(diff[i]) for i in range(len(AREA_IDS))},
        "n_within": int((diff <= int(h2_lim["abs_hour_diff_max"])).sum()),
        "kendall_tau": None if math.isnan(tau2) else round(tau2, 6),
        # 全エリアが同順位だと τ-b の分母が 0 になる(=順序で分化していない)。
        # 判定は FAIL のままにするが、**理由が「不一致」でなく「順序が定義できない」**ことを残す。
        "tau_undefined": bool(math.isnan(tau2)),
        "limit": {k: h2_lim[k] for k in ("abs_hour_diff_max", "n_within_min", "tau_min")},
        "pass": bool(
            int((diff <= int(h2_lim["abs_hour_diff_max"])).sum()) >= int(h2_lim["n_within_min"])
            and _pass(tau2, float(h2_lim["tau_min"]), upper=False)
        ),
        "measured": True,
    }

    # --- H3 平日休日比(測定不能)→ 深夜残存率で代替 ----------------
    sn = night_residual(sim_share)
    on = night_residual(obs)
    h3_lim = pr["H3"]
    tau3 = kendall_tau(sn.tolist(), on.tolist())
    h3 = {
        "name": h3_lim["name"],
        "substituted": True,
        "substitute": h3_lim["substitute"],
        "reason": h3_lim["reason"],
        "sim_night_residual": {AREA_IDS[i]: round(float(sn[i]), 4) for i in range(len(AREA_IDS))},
        "obs_night_residual": {AREA_IDS[i]: round(float(on[i]), 4) for i in range(len(AREA_IDS))},
        "abs_diff_max": round(float(np.max(np.abs(sn - on))), 4),
        "kendall_tau": None if math.isnan(tau3) else round(tau3, 6),
        "tau_undefined": bool(math.isnan(tau3)),
        "limit": {k: h3_lim[k] for k in ("abs_diff_max", "tau_min")},
        "pass": bool(
            _pass(float(np.max(np.abs(sn - on))), float(h3_lim["abs_diff_max"]))
            and _pass(tau3, float(h3_lim["tau_min"]), upper=False)
        ),
        "measured": True,
    }

    # --- H4 エリア構成 -------------------------------------------
    h4_lim = pr["H4"]
    if obs_area_share is None:
        h4 = {"name": h4_lim["name"], "measured": False, "pass": None,
              "reason": "holdout 側のエリア構成が未供給"}
    else:
        sa = area_share(sim_table)
        oa = np.asarray(obs_area_share, dtype=np.float64)
        oa = oa / oa.sum() if oa.sum() > 0 else oa
        d4 = float(jsd(sa, oa, base=base))
        m4 = float(np.max(np.abs(sa - oa)))
        h4 = {
            "name": h4_lim["name"],
            "sim_share": {AREA_IDS[i]: round(float(sa[i]), 6) for i in range(len(AREA_IDS))},
            "obs_share": {AREA_IDS[i]: round(float(oa[i]), 6) for i in range(len(AREA_IDS))},
            "jsd": round(d4, 6),
            "abs_share_diff_max": round(m4, 6),
            "limit": {k: h4_lim[k] for k in ("jsd_max", "abs_share_diff_max")},
            "pass": bool(
                _pass(d4, float(h4_lim["jsd_max"]))
                and _pass(m4, float(h4_lim["abs_share_diff_max"]))
            ),
            "measured": True,
        }

    # --- H5 属性構成 ---------------------------------------------
    h5_lim = pr["H5"]
    if sim_attr is None or obs_attr is None:
        h5 = {"name": h5_lim["name"], "measured": False, "pass": None,
              "reason": "ラン側または holdout 側の属性構成が未供給"}
    else:
        s5 = np.asarray(sim_attr, dtype=np.float64)
        o5 = np.asarray(obs_attr, dtype=np.float64)
        s5 = s5 / np.maximum(s5.sum(axis=1, keepdims=True), 1e-12)
        o5 = o5 / np.maximum(o5.sum(axis=1, keepdims=True), 1e-12)
        per = [float(jsd(s5[i], o5[i], base=base)) for i in range(len(AREA_IDS))]
        m5 = float(np.max(np.abs(s5 - o5)))
        h5 = {
            "name": h5_lim["name"],
            "attr_ids": list(ATTR_IDS),
            "sim_share": {AREA_IDS[i]: [round(float(v), 4) for v in s5[i]]
                          for i in range(len(AREA_IDS))},
            "obs_share": {AREA_IDS[i]: [round(float(v), 4) for v in o5[i]]
                          for i in range(len(AREA_IDS))},
            "per_area_jsd": {AREA_IDS[i]: round(per[i], 6) for i in range(len(AREA_IDS))},
            "jsd_mean": round(float(np.mean(per)), 6),
            "abs_share_diff_max": round(m5, 6),
            "limit": {k: h5_lim[k] for k in ("jsd_mean_max", "abs_share_diff_max")},
            "pass": bool(
                _pass(float(np.mean(per)), float(h5_lim["jsd_mean_max"]))
                and _pass(m5, float(h5_lim["abs_share_diff_max"]))
            ),
            "measured": True,
        }

    metrics = {"H1": h1, "H2": h2, "H3": h3, "H4": h4, "H5": h5}
    measured = [m for m in metrics.values() if m.get("measured")]
    return {
        **metrics,
        "prereg": pr,
        "n_measured": len(measured),
        "n_pass": sum(1 for m in measured if m.get("pass")),
        "pass": bool(measured) and all(bool(m.get("pass")) for m in measured),
    }


def metrics_markdown(res: Mapping[str, Any]) -> str:
    """5指標を 1 表に。"""
    rows = []
    for key in ("H1", "H2", "H3", "H4", "H5"):
        m = res[key]
        if not m.get("measured"):
            rows.append([key, m["name"], "測定不能", m.get("reason", ""), "—"])
            continue
        if key == "H1":
            val = f"JSD平均 {m['jsd_mean']:.5f} / 最大 {m['jsd_max']:.5f} / r {m['pearson_r']:.3f}"
            lim = f"JSD平均 ≤{m['limit']['jsd_mean_max']} ・ r ≥{m['limit']['pearson_min']}"
        elif key == "H2":
            val = f"±1h一致 {m['n_within']}/5 ・ τ {m['kendall_tau']}"
            lim = f"≥{m['limit']['n_within_min']}/5 ・ τ ≥{m['limit']['tau_min']}"
        elif key == "H3":
            val = f"Δ絶対値の最大 {m['abs_diff_max']:.4f} ・ τ {m['kendall_tau']}(代替指標)"
            lim = f"≤{m['limit']['abs_diff_max']} ・ τ ≥{m['limit']['tau_min']}"
        elif key == "H4":
            val = f"JSD {m['jsd']:.5f} ・ Δ絶対値の最大 {m['abs_share_diff_max']:.4f}"
            lim = f"≤{m['limit']['jsd_max']} ・ ≤{m['limit']['abs_share_diff_max']}"
        else:
            val = f"JSD平均 {m['jsd_mean']:.5f} ・ Δ絶対値の最大 {m['abs_share_diff_max']:.4f}"
            lim = f"≤{m['limit']['jsd_mean_max']} ・ ≤{m['limit']['abs_share_diff_max']}"
        rows.append([key, m["name"], val, lim, "PASS" if m["pass"] else "FAIL"])
    return markdown_table(["#", "指標(§1.4)", "実測", "事前登録の合格線(案)", "判定"], rows)


# ---------------------------------------------------------------- ラン要約ログの読み取り

_SUMMARY_PATTERNS: dict[str, tuple[str, type]] = {
    "n_agents": (r"\[run\]\s+n=(\d+)", int),
    "n_cells": (r"\[run\][^\n]*cells=(\d+)", int),
    "ticks": (r"\[run\][^\n]*ticks=(\d+)", int),
    "wall_seconds": (r"壁時計\s+([0-9.]+)s", float),
    "movement_ms_per_tick": (r"移動\+密度\s+([0-9.]+)\s*ms/tick", float),
    "llm_calls": (r"LLM呼\s+([0-9,]+)", int),
    "calls_per_agent": (r"=\s*([0-9.]+)\s*呼/体/日", float),
    "parse_error_rate": (r"書式エラー率\s+実効\s+([0-9.]+)", float),
    "parse_error_rate_strict": (r"書式エラー率[^\n]*厳密\s+([0-9.]+)", float),
    "min_stock": (r"最小在庫\s+(-?\d+)", int),
    "n_checkpoints": (r"checkpoint\s+(\d+)\s*点", int),
    "final_hash": (r"checkpoint[^\n]*最終\s+([0-9a-f]+)", str),
    "census_residual": (r"日次センサス[^\n]*残差\s+(-?[0-9,]+)", int),
    "waste_tonnes_per_day": (r"廃棄\s+([0-9.]+)\s*t/日", float),
}

_DIAG_RE = re.compile(r"^\s*診断\s+(\w+):\s*([0-9,]+)\s*$", re.M)
_DIAG_RATE_RE = re.compile(
    r"診断\s+parse_error_rate:\s*([0-9.]+)\s*/\s*undefined_action_count:\s*([0-9,]+)"
    r"\s*/\s*tape_miss_count:\s*([0-9,]+)\s*/\s*conversation_sessions:\s*([0-9,]+)"
)


def parse_run_summary(text: str) -> dict[str, Any]:
    """``RunResult.summary()`` の標準出力 → 数値辞書。**純関数**。

    ラン本体は親がサーバーで回すので、受入表はその**標準出力**と manifest だけから
    組み立てる(エンジンを再実行しない)。読めなかった欄は ``None`` で残す
    (**推測で埋めない**=CLAUDE.md §5)。
    """
    out: dict[str, Any] = {}
    for key, (pat, cast) in _SUMMARY_PATTERNS.items():
        m = re.search(pat, text)
        if m is None:
            out[key] = None
            continue
        raw = m.group(1)
        out[key] = cast(raw.replace(",", "")) if cast is not str else raw
    out["conserved"] = None
    m = re.search(r"保存則[^\n]*\)\s*(OK|NG)", text)
    if m:
        out["conserved"] = m.group(1) == "OK"
    m = re.search(r"ゲート\s+(PASS|FAIL)", text)
    out["census_gate"] = (m.group(1) == "PASS") if m else None
    m = re.search(r"憲法5\s+(OK|NG)", text)
    out["constitution_ok"] = (m.group(1) == "OK") if m else None
    m = re.search(r"band\s+[0-9.]+-[0-9.]+\)\s*(OK|NG)", text)
    out["waste_band_ok"] = (m.group(1) == "OK") if m else None

    diag = {k: int(v.replace(",", "")) for k, v in _DIAG_RE.findall(text)}
    m = _DIAG_RATE_RE.search(text)
    if m:
        diag["parse_error_rate"] = float(m.group(1))
        diag["undefined_action_count"] = int(m.group(2).replace(",", ""))
        diag["tape_miss_count"] = int(m.group(3).replace(",", ""))
        diag["conversation_sessions"] = int(m.group(4).replace(",", ""))
    out["diagnostics"] = diag
    return out


#: C7 受入で「必ず出ていること」を確認する診断行(実装計画書 §9.1 C7「診断行」)。
REQUIRED_DIAG_ROWS: tuple[str, ...] = ("deferred", "promoted", "degraded", "suppressed")


def parse_time_v(text: str) -> dict[str, Any]:
    """``/usr/bin/time -v`` の出力 → RSS ほか。**純関数**。"""
    out: dict[str, Any] = {"max_rss_kb": None, "elapsed_seconds": None}
    m = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", text)
    if m:
        out["max_rss_kb"] = int(m.group(1))
    m = re.search(r"Elapsed \(wall clock\) time.*?:\s*(\d[\d:.]*)\s*$", text, re.M)
    if m:
        parts = [float(p) for p in m.group(1).split(":")]
        secs = 0.0
        for p in parts:
            secs = secs * 60.0 + p
        out["elapsed_seconds"] = secs
    return out


def dir_bytes(path: str | Path, patterns: Sequence[str] = ("*",)) -> int:
    """S1(恒久記録)のバイト数=対象ディレクトリのファイル合計。"""
    root = Path(path)
    if root.is_file():
        return root.stat().st_size
    seen: dict[Path, int] = {}
    for pat in patterns:
        for p in root.rglob(pat):
            if p.is_file():
                seen[p.resolve()] = p.stat().st_size
    return int(sum(seen.values()))


# ---------------------------------------------------------------- 予算行


def budget_limits(ids: Iterable[str] = ("W1", "M8", "S1", "P2", "M1", "L4", "L6")) -> dict[str, Any]:
    """予算宣言表から上限を読む(**Markdown が正典**・複製しない)。"""
    from shibuya.core.budget import budget_by_id, load_budget_table, parse_limit

    rows = budget_by_id(load_budget_table())
    out: dict[str, Any] = {}
    for rid in ids:
        row = rows.get(rid)
        if row is None:
            out[rid] = None
            continue
        lim = parse_limit(row.declared)
        out[rid] = {
            "item": row.item,
            "declared": row.declared,
            "limit": None if lim is None else lim[0],
            "unit": None if lim is None else lim[1],
        }
    return out
