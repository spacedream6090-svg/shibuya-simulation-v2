"""build.space.navmesh1 — 第 5 期 空間の段 1: 多層の歩ける面のナビメッシュを組む(脇の段・``build.run`` の段の外)。

正: 空間の設計の下書き ``docs/design/v2-spatial-design-round-draft.md`` §4 段 1・SR10 (a)・SR11 (a)+(d)・SR12 (a)+(d)・
SR13 (a)・SR17 (b)+(c)/指示書 10-06 §2 SR10〜SR13・SR17/指示書 10-03 §8 3-1・3-2 (c)・3-3。記録
``docs/bench/analysis/spatial-2026-10/sp1/README.md``。

**作り方**(SR13 (a)=numba で自前・shapely や laspy は使わない): 歩ける面を階ごとの 0.5 m の格子に塗り(出どころの札つき=
先に塗ったものが勝つ)、行ごとのラン → 門 → 帯に分ける(``build.space.mesh``)。PLATEAU の三角形をそのまま溶接する代わりに
格子に塗るので、地物の継ぎ目(T 字・重なり・LOD の重複)は塗りの和で溶ける。

地上(階 0)の塗りの順(先が勝つ):

1. PLATEAU 道路 LOD2/3 の歩道部 2000・島 3000(高架 2・アンダーパス 5・トンネル 6 の区間と都市高速 5 は地上に入れない)。
2. PLATEAU 都市設備の横断歩道 1110(縞の頂点の外接矩形=最小の面積の向き)。
3. **SR10**: 歩道部の無い LOD2/3 の道の車道部は、近い W1 の辺の種類が住宅街の型(``RESIDENTIAL_KLASS``)なら全部。
4. **SR10**: LOD1 しか無い道は、住宅街の型なら面全体・幹線の型(``TRUNK_KLASS``)なら道の外の縁から 2.0 m(仮)だけ。
5. 横断の帯: OSM の ``footway=crossing`` の線(幅は OSM の ``width``・無ければ 4.0 m 仮)と、線の無い ``highway=crossing``
   の点から近い車の道の辺に直交する帯(道の外の縁 +1 m まで)。
6. OSM の歩行系の線(``width`` があればそれ・無ければ道の種類の既定幅 ``LINE_WIDTH_M``)・W1 の歩行系の辺の線(既定幅)。

デッキ(階 1・2)と地下(階 -1〜-4): W1 の層の辺と OSM の層つきの線の帯(幅は歩行空間ネットワークの幅員 4 区分の中央が
近くにあればそれ・無ければ既定)・PLATEAU 橋梁 LOD2 の上面(帯から 6 m の中だけ=歩く人の居るデッキ)・PLATEAU 地下街
LOD4.1 の床(層の高さで 4 つの階に分ける)。

**つなぎ**(W1 で行けるのに面が切れている所): W1 の辺の両端の点が別の塊にあれば、辺の近くで 2 つの塊の最も近い 2 点を
帯(幅 2 m)で結ぶ(``bridge_w1``)。W1 の節から 30 m の中に面が無ければ、節から面までの短い帯(``anchor_stub``)。
数と長さは見出しの ``notes`` に出す=範囲の外と面の切れ目の宣言。

上下の接続口(Detour の off-mesh 接続と同じ形): W1 の階をまたぐ辺(steps=階段・elevator=EV・ほか=スロープ)・PLATEAU
の地下出入口 4020(属性に種類が無い=階段と置く)・歩行空間ネットワーク 2020 の階段 6・EV 4・ES 5・スロープ 7 で
階の違うリンク。値は SR11 (a)+(d)(``LINK_VALUES``)。

使い方(リポの根で・作業木の ``src`` を ``PYTHONPATH`` に):

    python -m shibuya.build.space.navmesh1 --data data --world data/world/v2 --out data/world/v2_stage_5-1

逐次ループ宣言(P4): 構築の 1 回だけ(地物・線・節・辺の数ぶんの Python のループと、格子の numba のループ)。ランには
入らない。
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Final

import numba as nb
import numpy as np

from shibuya.build.geo.common import (
    CELL_M,
    Gate,
    StageResult,
    canonical_json_bytes,
    param_hash,
    sha256_file,
    write_header,
    write_npy,
    write_parquet,
)
from shibuya.build.space import mesh as M
from shibuya.core.time_consts import SECONDS_PER_MINUTE
from shibuya.build.space import raster as R
from shibuya.build.space import sources as S
from shibuya.world import navmesh as NV

__all__ = [
    "STAGE",
    "STAGE_VERSION",
    "DEFAULT_PARAMS",
    "RESIDENTIAL_KLASS",
    "TRUNK_KLASS",
    "TRUNK_FUNCTIONS",
    "LINE_WIDTH_M",
    "LINK_VALUES",
    "NAVMESH1_EXPEDIENTS",
    "build",
    "main",
]

STAGE: Final[str] = "navmesh1"
STAGE_VERSION: Final[str] = "1.1.0"  # 〔段 1 の検収の直し〕M1・M3・B9

#: 住宅街の型(歩道の無い細い道=車道の面全体を歩ける=道路構造令 第 5 条 5 項の歩車共存・SR10 (a))。
RESIDENTIAL_KLASS: Final[tuple[str, ...]] = (
    "residential", "service", "unclassified", "living_street", "footway", "pedestrian", "path", "steps",
    "cycleway", "corridor", "track")
#: 幹線の型(LOD1 しか無ければ両端 2.0 m だけ=SR10 (a))。
TRUNK_KLASS: Final[tuple[str, ...]] = ("tertiary", "secondary", "primary", "trunk", "tertiary_link",
                                       "secondary_link", "primary_link", "trunk_link")
#: つなぎの帯(``world.navmesh.SOURCE_CODES`` の bridge_w1)の札=セルで切らず最も近い W2 のセルへ倒す(段 1 の検収 M3)。
BRIDGE_W1_LABEL: Final[int] = 12
#: 幹線の型にする PLATEAU の道の機能(tran:function 2 一般国道・3 都道府県道)。不明(9020)ほかは W1 の最も近い車の辺から写す。
TRUNK_FUNCTIONS: Final[tuple[int, ...]] = (2, 3)
#: OSM と W1 の線の既定幅[m](``tools/build_geo/walkable_area.py`` の ``WIDTH_RULES`` と同じ値=道路構造令 第 11 条 3 項の
#: 歩道 2.0・第 10 条の 2 第 2 項の自転車歩行者道 3.0・階段 1.5 は答申 S4 の指定=法的根拠なし)。
LINE_WIDTH_M: Final[dict[str, float]] = {
    "footway": 2.0, "pedestrian": 2.0, "path": 2.0, "corridor": 2.0, "cycleway": 3.0, "steps": 1.5,
    "living_street": 4.0, "residential": 4.0, "service": 4.0, "unclassified": 4.0, "track": 2.0,
    "tertiary": 4.0, "secondary": 4.0, "primary": 4.0, "trunk": 4.0,
}
#: 歩行空間ネットワークの幅員の区分 → 幅[m](仕様書 2024-07 の 1: 1.0 m 未満・2: 1.0〜2.0・3: 2.0〜3.0・4: 3.0 以上 の
#: 区間の中央・4 は下限)。
HOKOUKUKAN_WIDTH_M: Final[dict[int, float]] = {1: 0.75, 2: 1.5, 3: 2.5, 4: 3.0}
#: 歩行空間ネットワーク 2020 の route_type → 接続口の種類(4 EV・5 ES・6 階段・7 スロープ)。
HOKOUKUKAN_ROUTE_LINK: Final[dict[int, int]] = {4: NV.LINK_ELEVATOR, 5: NV.LINK_ESCALATOR, 6: NV.LINK_STAIRS,
                                                7: NV.LINK_RAMP}

#: SR11 の値(容量=(a) 実測の許容量・R-64 §1-1/§5・待ち=(d) 運行の間隔の半分(間隔は仮))。
LINK_VALUES: Final[dict[str, float]] = {
    "stairs_cap_per_min_per_m": 65.7,      # 階段(上り)の許容量 人/分・m(鈴木ほか 2012・R-64 §1-1)
    "escalator_cap_per_min": 95.3,         # 30 m/分のエスカレーターの許容量 人/分(同)
    "elevator_capacity_persons": 11.0,     # かご 140×135 cm=11 人(R-64 §1-7・バリアフリー基準)
    "elevator_interval_s": 60.0,           # 運行の間隔(仮・駅の実測は空欄=R-64 §1-7)
    "stairs_width_default_m": 2.0,         # 幅の分からない階段の幅(仮)
}

DEFAULT_PARAMS: Final[dict[str, Any]] = {
    "res_m": 0.5,
    "trunk_edge_band_m": 2.0,          # SR10 (a) 幹線の両端の歩ける帯(仮)
    "crossing_width_m": 4.0,           # 横断の帯の幅(仮・未リサーチ)
    "crossing_node_extra_m": 1.0,      # 点の横断の帯を道の外の縁からはみ出させる長さ
    "crossing_node_max_half_m": 20.0,  # 点の横断の帯の半分の長さの上限
    "crossing_way_near_m": 6.0,        # これより近くに横断の線があれば点の帯は作らない
    "w1_line_width_m": 2.0,            # W1 の線の既定幅
    "anchor_radius_m": 30.0,           # 節の点を探す半径
    "stub_radius_m": 300.0,            # 面から遠い節の短い帯を探す半径
    "bridge_buffer_m": 30.0,           # つなぎの帯を探す辺の近さ
    "bridge_width_m": 2.0,             # つなぎの帯の幅
    "bridge_rounds": 3,                # つなぎの回数の上限
    "corridor_radius_m": 40.0,         # 通り道の印(W1 の辺の近くの帯・全部の階)
    "deck_height_m": 5.0,              # デッキの既定の高さ(地面から・仮)
    "ug_depth_m": 5.0,                 # 地下の既定の深さ(1 階あたり・仮)
    "brid_keep_m": 6.0,                # 橋梁の上面を残す帯からの距離
    "brid_up_nz": 0.8,                 # 上面とみなす法線の z
    "link_snap_m": 15.0,               # 接続口の端を面に寄せる半径
    "frn_entrance_ground_m": 20.0,     # 地下出入口の地上の端を探す半径
    "frn_entrance_ug_m": 40.0,         # 地下出入口の地下の端を探す半径
    "dem_res_m": 2.0,                  # 標高の格子
    "link_dedup_m": 5.0,               # 同じ種類・同じ階の組の接続口をまとめる距離
    "hokoukukan_near_m": 5.0,          # 線の幅を歩行空間ネットワークから取る近さ
    "close_gap_cells": 1,              # 塗りの閉じの半径(目の数=0.5 m・幅 1 m 以下の隙間を埋める)
    "short_gap_m": 12.0,               # 細い道の口の短い切れ目を埋める長さの上限(仮・未リサーチ)
    "ramp_max_grade": 1.0 / 12.0,      # これより急な階をまたぐスロープは階段と置く(傾斜路の勾配の上限 1/12・R-64 §4)
    "ramp_small_rise_m": 0.16,         # 高さがこれ以下なら勾配の上限は下の値(R-64 §4 の 16 cm 以下の例外)
    "ramp_small_rise_grade": 0.125,    # 高さ 16 cm 以下の傾斜路の勾配の上限 1/8(R-64 §4)
    "flat_interband_grade": 0.01,      # 階をまたぐのにこれより緩い W1 の辺は層の付け違いの疑い(数えるだけ・DOC の台帳の行)
    "no_surface_min_m": 3.0,           # 面の無い車の道の区間とみなす長さの下限
    "clip_to_cells": True,             # 面を W2 のセルの被覆で切る(段 1 の検収 M3・False は診断用)
    "no_surface_trunk_width_m": 4.0,   # 面の無い幹線の帯の幅(両側の歩道 2.0 m × 2 の合計=WIDTH_RULES と同じ・仮)
}

#: つなぎの台帳の行(``docs/design/bridging-ledger.json``・外す段つき)。
NAVMESH1_EXPEDIENTS: Final[tuple[str, ...]] = (
    "LOD1 しか無い幹線(tertiary 以上)は道の外の縁から 2.0 m(仮)だけを歩ける帯にする(SR10 (a)・外す段: 点群・基盤地図情報・"
    "航空写真で実際の幅が分かった区間から置き換え=SR1 の承認の後)",
    "どの面にも載らない道の幅は OSM の width(付与 0.3%)→ 道の種類の既定幅(LINE_WIDTH_M)・横断の帯は幅 4.0 m(仮)"
    "(SR10 (a)・外す段: 実際の幅のデータの後)",
    "道の種類は PLATEAU の tran:function の 2(一般国道)・3(都道府県道)を幹線の型とし、不明(9020)ほかの地物だけ格子の目ごとに"
    "最も近い W1 の車の辺の種類を写す(住宅街の型/幹線の型の 2 つ・地物ごとに多い方)",
    "W1 で行けるのに面が切れている所は、辺の近くの 2 つの塊の最も近い 2 点を幅 2 m の帯で結ぶ(つなぎ=bridge_w1)・面から "
    "30 m より遠い W1 の節は面までの短い帯(anchor_stub)(外す段: 実際の横断と通路のデータ=5-2 以降)",
    "デッキの高さは橋梁の上面が無い所で地面 + 5.0 m(仮)・地下は 1 階あたり 5.0 m(仮)(外す段: 5-2 の建物の中と縦の照合)",
    "PLATEAU の地下出入口 4020 は種類の属性が無いので階段と置く・幅の分からない階段は 2.0 m(仮)(外す段: 5-4 駅の構内)",
    "エレベーターの運行の間隔 60 s(仮)=待ち 30 s(SR11 (d))・定員 11 人(R-64)(外す段: 5-5 の物理でかごを動かす=SR11 (f))",
    "地下街の床は層の高さの近い方の階に割り当て、階の間の階段・斜路は W1 と歩行空間ネットワークの接続口だけでつなぐ"
    "(外す段: 5-2 の建物の中・5-4 駅の構内)",
    "W1 の階をまたぐ辺で種類の分からないもの(steps・elevator 以外)と歩行空間 NW のスロープは、勾配が 1/12 以下(高さ 16 cm "
    "以下は 1/8 以下=R-64 §4)ならスロープ(歩く・中に居る間は両端を結ぶ線の上・線が W2 のセルの外を通るものは端の点)、超えれば"
    "階段と置く・辺の形は面に塗らず接続口 1 本(外す段: 5-2・5-4)",
    "細い道の口の短い切れ目(W1 の住宅街の型の線の上で両側が歩ける面)は 12 m(仮)以下なら埋める・塗りの閉じは幅 1 m 以下の"
    "隙間と角だけで触れる所(外す段: 実際の幅のデータ=SR1 の承認の後)",
    "接続口の端は 15 m(地下出入口は地上 20 m・地下 40 m)の中の面に寄せる・面から遠い W1 の節の短い帯は 300 m の中の面まで"
    "(外す段: 5-2・5-4 の構内と建物の中)",
    "経路の回廊は W1 の道筋の辺から 40 m(仮・全部の階)の帯(外す段: 回廊の幅の感度=5,000 体のスクリーニングの後)",
    "歩ける面は W2 のセルの被覆で切る(セルの無い 100 m の升の面を消す・範囲の外は今のセル)。ただしつなぎの帯(bridge_w1)は"
    "切らず、その上の体のセルは最も近い W2 のセル(升の中心の距離)に倒す=範囲の外をつなぐ帯(外す段: W2 のセルの範囲の見直し)",
)

_NO_ALLOW = np.zeros((0, 0), dtype=np.uint8)


# ====================================================================== 小さな部品
def _klass_code(k: str) -> int:
    if k in TRUNK_KLASS:
        return 2
    return 1


@nb.njit(cache=True)
def _fill_nan_nearest(z):
    """NaN の目を 4 近傍の幅優先で最も近い値で埋める(DEM の区外)。"""
    ny, nx = z.shape
    q = np.empty(ny * nx, dtype=np.int64)
    seen = np.zeros((ny, nx), dtype=np.bool_)
    head = 0
    tail = 0
    for j in range(ny):
        for i in range(nx):
            if not math.isnan(z[j, i]):
                seen[j, i] = True
                q[tail] = j * nx + i
                tail += 1
    while head < tail:
        c = q[head]
        head += 1
        j = c // nx
        i = c - j * nx
        v = z[j, i]
        for dj, di in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            jj = j + dj
            ii = i + di
            if 0 <= jj < ny and 0 <= ii < nx and not seen[jj, ii]:
                seen[jj, ii] = True
                z[jj, ii] = v
                q[tail] = jj * nx + ii
                tail += 1
    return tail


@nb.njit(cache=True)
def _feature_klass(fid, klass, n_feat):
    """道の地物ごとに、面の中の目の道の種類(1 住宅街の型・2 幹線の型)の多い方(同数と 0 は 1)。"""
    cnt = np.zeros((n_feat + 1, 3), dtype=np.int64)
    ny, nx = fid.shape
    for j in range(ny):
        for i in range(nx):
            f = fid[j, i]
            if f > 0:
                cnt[f, klass[j, i]] += 1
    out = np.ones(n_feat + 1, dtype=np.int8)
    for f in range(1, n_feat + 1):
        if cnt[f, 2] > cnt[f, 1]:
            out[f] = 2
    return out


@nb.njit(cache=True)
def _feature_has_seed(fid, seed, code, n_feat):
    """道の地物ごとに、面の中に札 ``code`` の種(W1 の線)の目があるか。"""
    out = np.zeros(n_feat + 1, dtype=np.bool_)
    ny, nx = fid.shape
    for j in range(ny):
        for i in range(nx):
            f = fid[j, i]
            if f > 0 and seed[j, i] == code:
                out[f] = True
    return out


@nb.njit(cache=True)
def _apply_road_rules(label, fid_nosw, fid_l1, fklass, dist_nonroad, band_m):
    """SR10: 歩道の無い詳細の道の車道部(地物が住宅街の型)=3・LOD1 だけの道(住宅街の型)=4・LOD1 だけの幹線の外の縁=5。"""
    ny, nx = label.shape
    n3 = 0
    n4 = 0
    n5 = 0
    for j in range(ny):
        for i in range(nx):
            if label[j, i] != 0:
                continue
            f = fid_nosw[j, i]
            if f > 0 and fklass[f] == 1:
                label[j, i] = 3
                n3 += 1
                continue
            f = fid_l1[j, i]
            if f > 0:
                if fklass[f] == 1:
                    label[j, i] = 4
                    n4 += 1
                elif dist_nonroad[j, i] <= band_m:
                    label[j, i] = 5
                    n5 += 1
    return n3, n4, n5


@nb.njit(cache=True)
def _mask_columns(label, ox, oy, res, col_ok, cx0, cy0):
    """セルの無い 100 m の列の目を消す(範囲=W2 のセル)。``col_ok[iy-cy0, ix-cx0]``。"""
    ny, nx = label.shape
    n = 0
    for j in range(ny):
        yc = oy + (j + 0.5) * res
        iy = int(math.floor(yc / 100.0)) - cy0
        for i in range(nx):
            if label[j, i] == 0:
                continue
            xc = ox + (i + 0.5) * res
            ix = int(math.floor(xc / 100.0)) - cx0
            if iy < 0 or iy >= col_ok.shape[0] or ix < 0 or ix >= col_ok.shape[1] or col_ok[iy, ix] == 0:
                label[j, i] = 0
                n += 1
    return n


def _function_first(fklass: np.ndarray, func: np.ndarray) -> np.ndarray:
    """〔段 1 の検収 M1〕地物の道の種類: tran:function が 2・3(一般国道・都道府県道)なら幹線の型(2)・ほかは W1 の写しのまま。"""
    return np.where(np.isin(np.asarray(func), TRUNK_FUNCTIONS), 2, np.asarray(fklass)).astype(np.int8)


def _ramp_or_stairs(P: dict, kind: int, rise: float, horiz: float) -> int:
    """〔段 1 の検収 問い 2〕スロープの勾配の上限(R-64 §4: 傾斜路 1/12・高さ 16 cm 以下は 1/8)を超えるスロープは階段と置く。"""
    if kind != NV.LINK_RAMP:
        return kind
    small = abs(rise) <= float(P["ramp_small_rise_m"])
    gmax = float(P["ramp_small_rise_grade"]) if small else float(P["ramp_max_grade"])
    return NV.LINK_STAIRS if abs(rise) / max(float(horiz), 0.1) > gmax else kind


@nb.njit(cache=True)
def _mask_by_cells(label, ox, oy, res, lut, cx0, cy0, cell_m, band, removed, keep_label):
    """W2 のセルの無い所の目を消す(``world.navmesh.cell_of`` が -1 の目=その層のセルも地上のセルも無い)。``removed[札]`` に足す。
    札 ``keep_label``(つなぎの帯 bridge_w1)は消さない(範囲の外をつなぐ帯=体のセルは最も近い W2 のセルに倒す)。"""
    ny, nx = label.shape
    for j in range(ny):
        yc = oy + (j + 0.5) * res
        for i in range(nx):
            v = label[j, i]
            if v == 0 or v == keep_label:
                continue
            xc = ox + (i + 0.5) * res
            if NV.cell_of(lut, cx0, cy0, cell_m, xc, yc, band) < 0:
                label[j, i] = 0
                removed[v] += 1


@nb.njit(cache=True)
def _dilate_mask(mask, r_cells):
    """正方形の近傍で膨らませる(行と列の 2 回の走り=距離は Chebyshev)。"""
    ny, nx = mask.shape
    tmp = np.zeros((ny, nx), dtype=np.uint8)
    for j in range(ny):
        last = -10 ** 9
        for i in range(nx):
            if mask[j, i] != 0:
                last = i
            if i - last <= r_cells:
                tmp[j, i] = 1
        last = 10 ** 9
        for i in range(nx - 1, -1, -1):
            if mask[j, i] != 0:
                last = i
            if last - i <= r_cells:
                tmp[j, i] = 1
    out = np.zeros((ny, nx), dtype=np.uint8)
    for i in range(nx):
        last = -10 ** 9
        for j in range(ny):
            if tmp[j, i] != 0:
                last = j
            if j - last <= r_cells:
                out[j, i] = 1
        last = 10 ** 9
        for j in range(ny - 1, -1, -1):
            if tmp[j, i] != 0:
                last = j
            if last - j <= r_cells:
                out[j, i] = 1
    return out


@nb.njit(cache=True)
def _close_gaps(label, r_cells, code):
    """塗りの閉じ(膨らませて同じだけ削る=正方形の近傍)で、幅 2r 以下の隙間と角だけで触れる所を埋める。

    埋めた目は札 ``code``(つなぎ)。返り値は埋めた目の数。
    """
    ny, nx = label.shape
    mask = np.zeros((ny, nx), dtype=np.uint8)
    for j in range(ny):
        for i in range(nx):
            if label[j, i] != 0:
                mask[j, i] = 1
    dil = _dilate_mask(mask, r_cells)
    # 削る: 正方形の近傍が全部 dil の目だけ残す(行と列の 2 回の走りで最小)
    tmp = np.zeros((ny, nx), dtype=np.uint8)
    for j in range(ny):
        run = 0
        cnt = np.zeros(nx, dtype=np.int64)
        for i in range(nx):
            run = run + 1 if dil[j, i] != 0 else 0
            cnt[i] = run
        for i in range(nx):
            lo = i - r_cells
            hi = i + r_cells
            if lo < 0 or hi >= nx:
                continue
            if cnt[hi] >= 2 * r_cells + 1:
                tmp[j, i] = 1
    n = 0
    for i in range(nx):
        run = 0
        cnt = np.zeros(ny, dtype=np.int64)
        for j in range(ny):
            run = run + 1 if tmp[j, i] != 0 else 0
            cnt[j] = run
        for j in range(ny):
            lo = j - r_cells
            hi = j + r_cells
            if lo < 0 or hi >= ny:
                continue
            if cnt[hi] >= 2 * r_cells + 1 and mask[j, i] == 0:
                label[j, i] = code
                n += 1
    return n


def _trim_from_start(xy: np.ndarray, length: float) -> np.ndarray:
    """折れ線の始まりから ``length`` [m] までの部分。"""
    out = [xy[0]]
    acc = 0.0
    for k in range(xy.shape[0] - 1):
        L = float(np.hypot(*(xy[k + 1] - xy[k])))
        if acc + L >= length and L > 0:
            out.append(xy[k] + (xy[k + 1] - xy[k]) * ((length - acc) / L))
            return np.asarray(out)
        out.append(xy[k + 1])
        acc += L
    return np.asarray(out)


def _no_surface_runs(road_any, label, ox, oy, res, xy, step, min_len):
    """折れ線のうち道の面にも歩ける面にも載らない区間(長さ ``min_len`` 以上)→ [(ax, ay, bx, by, 長さ)]。"""
    pts = []
    for k in range(xy.shape[0] - 1):
        L = float(np.hypot(*(xy[k + 1] - xy[k])))
        m = max(1, int(math.ceil(L / step)))
        for t in range(m):
            pts.append(xy[k] + (xy[k + 1] - xy[k]) * (t / m))
    pts.append(xy[-1])
    P_ = np.asarray(pts)
    ny, nx = label.shape
    ii = np.floor((P_[:, 0] - ox) / res).astype(np.int64)
    jj = np.floor((P_[:, 1] - oy) / res).astype(np.int64)
    ok = (ii >= 0) & (ii < nx) & (jj >= 0) & (jj < ny)
    bare = np.zeros(P_.shape[0], dtype=bool)
    bare[ok] = (road_any[jj[ok], ii[ok]] == 0) & (label[jj[ok], ii[ok]] == 0)
    out = []
    k = 0
    n = bare.size
    while k < n:
        if not bare[k]:
            k += 1
            continue
        a = k
        while k < n and bare[k]:
            k += 1
        b = k - 1
        L = float(np.hypot(*np.diff(P_[a:b + 1], axis=0).T).sum()) if b > a else 0.0
        if L >= min_len:
            for q in range(a, b):
                out.append((float(P_[q, 0]), float(P_[q, 1]), float(P_[q + 1, 0]), float(P_[q + 1, 1]),
                            float(np.hypot(*(P_[q + 1] - P_[q])))))
    return out


def _short_gaps(label, ox, oy, res, xy, max_gap, step):
    """折れ線を ``step`` ごとに見て、歩けない区間の両側が歩ける面で長さが ``max_gap`` 以下の所 → [(ax, ay, bx, by)]。"""
    pts = []
    for k in range(xy.shape[0] - 1):
        L = float(np.hypot(*(xy[k + 1] - xy[k])))
        m = max(1, int(math.ceil(L / step)))
        for t in range(m):
            pts.append(xy[k] + (xy[k + 1] - xy[k]) * (t / m))
    pts.append(xy[-1])
    P = np.asarray(pts)
    ny, nx = label.shape
    ii = np.floor((P[:, 0] - ox) / res).astype(np.int64)
    jj = np.floor((P[:, 1] - oy) / res).astype(np.int64)
    ok = (ii >= 0) & (ii < nx) & (jj >= 0) & (jj < ny)
    walk = np.zeros(P.shape[0], dtype=bool)
    walk[ok] = label[jj[ok], ii[ok]] != 0
    out = []
    k = 0
    n = walk.size
    while k < n:
        if walk[k]:
            k += 1
            continue
        a = k
        while k < n and not walk[k]:
            k += 1
        b = k  # walk[b] は歩ける(b < n のとき)
        if a == 0 or b >= n:
            continue
        L = float(np.hypot(*(P[b] - P[a - 1])))
        if L <= max_gap:
            out.append((float(P[a - 1, 0]), float(P[a - 1, 1]), float(P[b, 0]), float(P[b, 1])))
    return out


def _min_area_rect(pts: np.ndarray) -> np.ndarray:
    """点の集まりの最小の面積の外接矩形(凸包の辺の向きを全部試す)→ 4 頂点 (4, 2)。"""
    p = np.unique(np.round(pts[:, :2], 3), axis=0)
    if p.shape[0] < 3:
        c = p.mean(axis=0)
        return np.array([c + [-1, -1], c + [1, -1], c + [1, 1], c + [-1, 1]], dtype=np.float64)
    # 凸包(Andrew の単調連鎖)
    p = p[np.lexsort((p[:, 1], p[:, 0]))]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for q in p:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in p[::-1]:
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    hull = np.asarray(lower[:-1] + upper[:-1])
    best = None
    for k in range(hull.shape[0]):
        e = hull[(k + 1) % hull.shape[0]] - hull[k]
        L = math.hypot(e[0], e[1])
        if L == 0:
            continue
        u = e / L
        v = np.array([-u[1], u[0]])
        a = hull @ u
        b = hull @ v
        area = (a.max() - a.min()) * (b.max() - b.min())
        if best is None or area < best[0] - 1e-12:
            best = (area, u, v, a.min(), a.max(), b.min(), b.max())
    _, u, v, a0, a1, b0, b1 = best
    return np.array([u * a0 + v * b0, u * a1 + v * b0, u * a1 + v * b1, u * a0 + v * b1])


def _parse_width(tags: dict) -> float | None:
    w = tags.get("width")
    if w is None:
        return None
    try:
        v = float(str(w).replace("m", "").strip().split(";")[0])
    except ValueError:
        return None
    return v if 0.3 <= v <= 30.0 else None


def _osm_floor(tags: dict) -> int | None:
    """OSM の線 → 階(0 地上・正 デッキ・負 地下・None=入れない=建物の中の階)。"""
    if tags.get("indoor") in ("yes", "room", "area"):
        return None
    lay = tags.get("layer")
    try:
        layer = int(str(lay).split(";")[0]) if lay is not None else None
    except ValueError:
        layer = None
    if layer is None:
        if tags.get("bridge") not in (None, "no"):
            layer = 1
        elif tags.get("tunnel") in ("yes",):
            layer = -1
        else:
            layer = 0
    lvl = tags.get("level")
    if lvl is not None and layer == 0 and str(lvl).strip() not in ("0", ""):
        return None
    return max(-2, min(2, layer))


# ====================================================================== 階の格子
class FloorRaster:
    """1 つの階の塗り(札 uint8)と高さ(float32・NaN=未設定)。"""

    def __init__(self, code: int, band: int, grid: R.Grid) -> None:
        self.code = int(code)
        self.band = int(band)
        self.grid = grid
        self.label = np.zeros((grid.ny, grid.nx), dtype=np.uint8)
        self.z = np.full((grid.ny, grid.nx), np.nan, dtype=np.float32)

    def capsule(self, x0, y0, x1, y1, half_w, value, allow=_NO_ALLOW) -> int:
        g = self.grid
        return int(R.fill_capsule(self.label, g.ox, g.oy, g.res, float(x0), float(y0), float(x1), float(y1),
                                  float(half_w), int(value), R.MODE_IF_ZERO, allow))

    def polyline(self, xy: np.ndarray, half_w: float, value: int, allow=_NO_ALLOW) -> int:
        n = 0
        for k in range(xy.shape[0] - 1):
            n += self.capsule(xy[k, 0], xy[k, 1], xy[k + 1, 0], xy[k + 1, 1], half_w, value, allow)
        if xy.shape[0] == 1:
            n += self.capsule(xy[0, 0], xy[0, 1], xy[0, 0], xy[0, 1], half_w, value, allow)
        return n

    def polygon(self, rings: list[np.ndarray], value: int, out: np.ndarray | None = None,
                mode: int = R.MODE_IF_ZERO, allow=_NO_ALLOW) -> int:
        g = self.grid
        ex0, ey0, ex1, ey1 = R.polygon_edges([r[:, :2] for r in rings])
        tgt = self.label if out is None else out
        return int(R.fill_polygon(tgt, g.ox, g.oy, g.res, ex0, ey0, ex1, ey1, int(value), int(mode), allow))


def _sub_grid(full: R.Grid, x0: float, y0: float, x1: float, y1: float, margin: float) -> R.Grid:
    res = full.res
    gx0 = max(full.ox, math.floor((x0 - margin) / res) * res)
    gy0 = max(full.oy, math.floor((y0 - margin) / res) * res)
    gx1 = min(full.ox + full.nx * res, math.ceil((x1 + margin) / res) * res)
    gy1 = min(full.oy + full.ny * res, math.ceil((y1 + margin) / res) * res)
    return R.Grid(gx0, gy0, res, max(1, int(round((gx1 - gx0) / res))), max(1, int(round((gy1 - gy0) / res))))


# ====================================================================== 本体
def build(data_root: Path, world_dir: Path, out_dir: Path, *, params: dict[str, Any] | None = None,
          log=print) -> StageResult:
    """材料を読んで ``out_dir`` に ``nav1_*`` と ``navmesh1.header.json`` を書く(既存の世界の資産は書き換えない)。"""
    import pyarrow.parquet as pq

    P = dict(DEFAULT_PARAMS)
    if params:
        P.update(params)
    data_root, world_dir, out_dir = Path(data_root), Path(world_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t_all = time.perf_counter()
    res = float(P["res_m"])
    notes: dict[str, Any] = {}

    # ---------------- W1・W2
    nodes = pq.read_table(world_dir / "w1_nodes.parquet", columns=["node_idx", "x", "y", "band", "layer"]).to_pydict()
    n_nodes = len(nodes["node_idx"])
    node_xy = np.stack([np.asarray(nodes["x"], np.float64), np.asarray(nodes["y"], np.float64)], axis=1)
    band_code = {"UG": -1, "GL": 0, "DECK": 1}
    node_band = np.asarray([band_code[b] for b in nodes["band"]], dtype=np.int8)
    node_layer = np.asarray([0 if v is None else int(v) for v in nodes["layer"]], dtype=np.int64)
    node_floor = np.where(node_band == 0, 0, np.clip(node_layer, -2, 2)).astype(np.int64)
    node_floor = np.where((node_band == 1) & (node_floor <= 0), 1, node_floor)
    node_floor = np.where((node_band == -1) & (node_floor >= 0), -1, node_floor)
    edges = list(S.iter_w1_edges(world_dir))
    n_edges = len(edges)
    cells = pq.read_table(world_dir / "w2_cells.parquet", columns=["ix", "iy", "band"]).to_pydict()
    cix = np.asarray(cells["ix"], np.int64)
    ciy = np.asarray(cells["iy"], np.int64)
    cband = np.asarray([band_code[b] for b in cells["band"]], dtype=np.int8)
    cx0, cx1 = int(cix.min()), int(cix.max())
    cy0, cy1 = int(ciy.min()), int(ciy.max())
    full = R.Grid.covering(cx0 * CELL_M, cy0 * CELL_M, (cx1 + 1) * CELL_M, (cy1 + 1) * CELL_M, res)
    col_ok_gl = np.zeros((cy1 - cy0 + 1, cx1 - cx0 + 1), dtype=np.uint8)
    col_ok_any = np.zeros_like(col_ok_gl)
    for ix, iy, b in zip(cix, ciy, cband):
        col_ok_any[iy - cy0, ix - cx0] = 1
        if b == 0:
            col_ok_gl[iy - cy0, ix - cx0] = 1
    bbox = (full.ox, full.oy, full.ox + full.nx * res, full.oy + full.ny * res)
    notes["grid"] = {"res_m": res, "ox": full.ox, "oy": full.oy, "nx": full.nx, "ny": full.ny,
                     "cells": len(cix), "cell_columns_gl": int(col_ok_gl.sum())}

    # ---------------- 材料
    udx = data_root / S.PLATEAU_UDX_RELPATH
    t0 = time.perf_counter()
    roads, st_tran = S.read_tran_roads(udx, bbox)
    crossings_frn, entrances_frn, st_frn = S.read_frn(udx, bbox)
    dem_tri, st_dem = S.read_dem_triangles(udx, bbox)
    ubld_tri, ubld_layers, st_ubld = S.read_ubld_floor_triangles(data_root / "plateau")
    brid_list, st_brid = S.read_brid_triangles(data_root / "plateau")
    osm_ways, osm_nodes = S.read_osm_walk(data_root / "spatial" / "osm_walk" / "osm_walk_raw.json")
    nw_links, nw_nodes = S.read_hokoukukan_2020(data_root / "research_cache" / "r58")
    t_read = round(time.perf_counter() - t0, 1)
    notes["sources"] = {"tran": st_tran, "frn": st_frn, "dem": st_dem, "ubld": st_ubld, "brid": st_brid,
                        "osm_walk": {"ways": len(osm_ways), "nodes": len(osm_nodes)},
                        "hokoukukan_2020": {"links": len(nw_links), "nodes": len(nw_nodes)}}
    log(f"[navmesh1] 材料 {t_read} s・道 {st_tran['n_roads_in_bbox']}・DEM {st_dem['n_triangles']}")

    # ---------------- DEM(2 m)
    dgrid = R.Grid.covering(bbox[0], bbox[1], bbox[2], bbox[3], float(P["dem_res_m"]))
    dem = np.full((dgrid.ny, dgrid.nx), np.nan, dtype=np.float32)
    R.fill_triangles_z(dem, dgrid.ox, dgrid.oy, dgrid.res, dem_tri, False)
    n_dem_nan = int(np.isnan(dem).sum())
    _fill_nan_nearest(dem)
    notes["dem"] = {"res_m": dgrid.res, "nx": dgrid.nx, "ny": dgrid.ny, "filled_from_nearest_cells": n_dem_nan}

    def dem_at(x, y):
        return float(NV.dem_z(dem, dgrid.ox, dgrid.oy, dgrid.res, float(x), float(y)))

    # ---------------- 地上(階 0)
    gl = FloorRaster(0, 0, full)
    ground_roads = [r for r in roads if r.function != 5 and r.section not in (2, 5, 6)]
    road_any = np.zeros_like(gl.label)
    fid_nosw = np.zeros(gl.label.shape, dtype=np.int32)
    fid_l1 = np.zeros(gl.label.shape, dtype=np.int32)
    for r in ground_roads:
        outer = [ring for ring, s in r.lod1]
        if outer:
            gl.polygon(outer, 1, out=road_any, mode=R.MODE_ALWAYS)
        for code, _lod, rings in r.areas:
            gl.polygon([ring for ring, _s in rings], 1, out=road_any, mode=R.MODE_ALWAYS)
    n_sw = 0
    for r in ground_roads:
        for code, _lod, rings in r.areas:
            if code in (2000, 2010, 2020, 3000, 3010, 3020):
                n_sw += gl.polygon([ring for ring, _s in rings], 1)
    n_frn = 0
    for v in crossings_frn:
        n_frn += gl.polygon([_min_area_rect(v)], 2)
    # 道の地物の番号(1 から)=SR10 の規則を地物ごとの道の種類で当てる
    for k, r in enumerate(ground_roads, start=1):
        if r.detailed and not r.has_sidewalk:
            for code, _lod, rings in r.areas:
                if code in (1000, 1020):
                    gl.polygon([ring for ring, _s in rings], k, out=fid_nosw, mode=R.MODE_ALWAYS)
        elif not r.detailed and r.lod1:
            gl.polygon([ring for ring, _s in r.lod1], k, out=fid_l1, mode=R.MODE_ALWAYS)
    # 道の種類の写し(W1 の辺の線 → 道の面の中で最も近い線の種類 → 地物ごとに多い方)
    seed = np.zeros(gl.label.shape, dtype=np.int16)
    car = [e for e in edges if e["klass"] not in ("footway", "pedestrian", "path", "steps", "corridor", "elevator",
                                                   "cycleway") and e["band_u"] == "GL" and e["band_v"] == "GL"]
    # 幹線は上書き・住宅街の型は空いた目だけ
    for e in edges:
        if e["band_u"] != "GL" or e["band_v"] != "GL" or e["klass"] == "elevator":
            continue
        code = _klass_code(e["klass"])
        xy = e["xy"]
        for k in range(xy.shape[0] - 1):
            R.fill_capsule(seed, full.ox, full.oy, res, xy[k, 0], xy[k, 1], xy[k + 1, 0], xy[k + 1, 1], 0.5,
                           code, R.MODE_ALWAYS if code == 2 else R.MODE_IF_ZERO, _NO_ALLOW)
    klass, kdist = R.bfs_nearest_label(seed, road_any)
    del kdist
    fk_nosw = _feature_klass(fid_nosw, klass, len(ground_roads))
    fk_l1 = _feature_klass(fid_l1, klass, len(ground_roads))
    # 交差部(sectionType 4)の地物は、住宅街の型の線が中を通れば住宅街の型(細い道どうしの交差点は全部歩ける)
    sect4 = np.asarray([0] + [1 if r.section == 4 else 0 for r in ground_roads], dtype=np.int8)
    rs_nosw = _feature_has_seed(fid_nosw, seed, 1, len(ground_roads))
    rs_l1 = _feature_has_seed(fid_l1, seed, 1, len(ground_roads))
    fk_nosw = np.where((sect4 == 1) & rs_nosw, 1, fk_nosw).astype(np.int8)
    fk_l1 = np.where((sect4 == 1) & rs_l1, 1, fk_l1).astype(np.int8)
    del seed
    # 地物の値は面を持つ方の数え(歩道の無い詳細の道の車道部か LOD1)
    has_nosw = np.zeros(len(ground_roads) + 1, dtype=bool)
    has_l1 = np.zeros(len(ground_roads) + 1, dtype=bool)
    has_nosw[np.unique(fid_nosw)] = True
    has_l1[np.unique(fid_l1)] = True
    fklass = np.where(has_nosw, fk_nosw, np.where(has_l1, fk_l1, 1)).astype(np.int8)
    # 〔段 1 の検収 M1〕道の種類は PLATEAU の tran:function を先に決める(2 一般国道・3 都道府県道=幹線の型)。不明(9020)ほかの
    # 地物だけ上の W1 の写しを使う(W1 は幹線の中心線を持たない区間が多く、国道・都道の車道が住宅街の型で塗られていた)
    func = np.asarray([0] + [int(r.function) for r in ground_roads], dtype=np.int64)
    fklass = _function_first(fklass, func)
    by_func: dict[str, dict[str, int]] = {}
    for f in np.unique(func[1:]).tolist():
        sel = func == f
        by_func[str(f)] = {"nosw_residential": int((sel & has_nosw & (fklass == 1)).sum()),
                           "nosw_trunk": int((sel & has_nosw & (fklass == 2)).sum()),
                           "lod1_residential": int((sel & has_l1 & (fklass == 1)).sum()),
                           "lod1_trunk": int((sel & has_l1 & (fklass == 2)).sum())}
    notes["road_features_by_function"] = by_func
    dist_nonroad = R.edt_inside(road_any, res)
    n3, n4, n5 = _apply_road_rules(gl.label, fid_nosw, fid_l1, fklass, dist_nonroad, float(P["trunk_edge_band_m"]))
    notes["road_features_klass"] = {"nosw_residential": int((has_nosw & (fklass == 1)).sum()) - int(has_nosw[0]),
                                    "nosw_trunk": int((has_nosw & (fklass == 2)).sum()),
                                    "lod1_residential": int((has_l1 & (fklass == 1)).sum()) - int(has_l1[0]),
                                    "lod1_trunk": int((has_l1 & (fklass == 2)).sum())}
    del fid_nosw, fid_l1, klass
    # 横断の帯(OSM の線)
    gl_ways = [w for w in osm_ways if _osm_floor(w["tags"]) == 0]
    cross_ways = [w for w in gl_ways if w["tags"].get("footway") == "crossing"]
    n6 = 0
    for w in cross_ways:
        wd = _parse_width(w["tags"]) or float(P["crossing_width_m"])
        n6 += gl.polyline(w["xy"], 0.5 * wd, 6)
    # 横断の帯(点)
    cw_pts = np.concatenate([w["xy"] for w in cross_ways]) if cross_ways else np.zeros((0, 2))
    car_seg = []
    for e in car:
        xy = e["xy"]
        for k in range(xy.shape[0] - 1):
            car_seg.append((xy[k, 0], xy[k, 1], xy[k + 1, 0], xy[k + 1, 1]))
    car_seg_a = np.asarray(car_seg, dtype=np.float64) if car_seg else np.zeros((0, 4))
    n7 = 0
    n7_nodes = 0
    for nd in osm_nodes:
        if nd["tags"].get("highway") != "crossing":
            continue
        x, y = nd["x"], nd["y"]
        if cw_pts.shape[0] and np.min(np.hypot(cw_pts[:, 0] - x, cw_pts[:, 1] - y)) <= float(P["crossing_way_near_m"]):
            continue
        if car_seg_a.shape[0] == 0:
            continue
        ax, ay, bx, by = car_seg_a[:, 0], car_seg_a[:, 1], car_seg_a[:, 2], car_seg_a[:, 3]
        dx, dy = bx - ax, by - ay
        L2 = np.maximum(dx * dx + dy * dy, 1e-12)
        t = np.clip(((x - ax) * dx + (y - ay) * dy) / L2, 0, 1)
        d = np.hypot(ax + t * dx - x, ay + t * dy - y)
        k = int(np.argmin(d))
        if d[k] > 15.0:
            continue
        L = math.sqrt(L2[k])
        ux, uy = -dy[k] / L, dx[k] / L
        jj, ii = full.row_of(y), full.col_of(x)
        half = 0.0
        if 0 <= jj < full.ny and 0 <= ii < full.nx:
            half = float(dist_nonroad[jj, ii])
        half = min(half + float(P["crossing_node_extra_m"]), float(P["crossing_node_max_half_m"]))
        if half <= 0.5:
            continue
        n7 += gl.capsule(x - ux * half, y - uy * half, x + ux * half, y + uy * half,
                         0.5 * float(P["crossing_width_m"]), 7)
        n7_nodes += 1
    del dist_nonroad
    # OSM の歩行系の線
    ped = ("footway", "pedestrian", "path", "steps", "corridor", "cycleway", "track", "living_street")
    n8 = n9 = 0
    for w in gl_ways:
        hw = w["tags"].get("highway")
        if hw not in ped or w["tags"].get("footway") == "crossing":
            continue
        wd = _parse_width(w["tags"])
        if wd is not None:
            n8 += gl.polyline(w["xy"], 0.5 * wd, 8)
        else:
            n9 += gl.polyline(w["xy"], 0.5 * LINE_WIDTH_M.get(hw, 2.0), 9)
    # W1 の歩行系の辺(地上)
    n11 = 0
    for e in edges:
        if e["klass"] in ped and e["band_u"] == "GL" and e["band_v"] == "GL":
            n11 += gl.polyline(e["xy"], 0.5 * float(P["w1_line_width_m"]), 11)
    # 面の無い W1 の車の道(SR10 (a): どの面にも載らない道=道の種類の既定幅の帯・OSM の width は車の道に無い)
    n_nos = 0
    n_nos_m = 0.0
    for e in edges:
        if e["band_u"] != "GL" or e["band_v"] != "GL" or e["klass"] in ped or e["klass"] == "elevator":
            continue
        xy = np.ascontiguousarray(e["xy"], dtype=np.float64)
        wd = LINE_WIDTH_M.get(e["klass"], float(P["no_surface_trunk_width_m"]))
        for (ax, ay, bx, by, L) in _no_surface_runs(road_any, gl.label, full.ox, full.oy, res, xy, 0.5,
                                                    float(P["no_surface_min_m"])):
            n_nos += gl.capsule(ax, ay, bx, by, 0.5 * wd, 11)
            n_nos_m += L
    notes["w1_car_no_surface"] = {"cells": n_nos, "length_m": round(n_nos_m, 1)}
    # 細い道の口の短い切れ目(W1 の住宅街の型の車の辺の線の上で、両側が歩ける面で間が short_gap_m 以下の所)
    n17 = 0
    n17_gaps = 0
    for e in edges:
        if e["band_u"] != "GL" or e["band_v"] != "GL" or e["klass"] in ped or e["klass"] == "elevator":
            continue
        if _klass_code(e["klass"]) != 1:
            continue
        xy = np.ascontiguousarray(e["xy"], dtype=np.float64)
        gaps = _short_gaps(gl.label, full.ox, full.oy, res, xy, float(P["short_gap_m"]), 0.25)
        for (ax, ay, bx, by) in gaps:
            n17 += gl.capsule(ax, ay, bx, by, 0.5 * float(P["bridge_width_m"]), 17)
            n17_gaps += 1
    # 節を通り抜ける 2 本の組(細い道が幹線を渡る交差点)
    inc: dict[int, list[tuple[int, np.ndarray]]] = {}
    for e in edges:
        if e["band_u"] != "GL" or e["band_v"] != "GL" or e["klass"] in ped or e["klass"] == "elevator":
            continue
        if _klass_code(e["klass"]) != 1:
            continue
        xy = np.asarray(e["xy"], dtype=np.float64)
        if np.hypot(*(xy[0] - node_xy[e["u"]])) > np.hypot(*(xy[-1] - node_xy[e["u"]])):
            xy = xy[::-1]
        inc.setdefault(e["u"], []).append((e["edge"], xy))          # u から出る向き
        inc.setdefault(e["v"], []).append((e["edge"], xy[::-1]))    # v から出る向き
    for nd in sorted(inc):
        lst = inc[nd]
        for a in range(len(lst)):
            for b in range(a + 1, len(lst)):
                pa = _trim_from_start(lst[a][1], 20.0)[::-1]
                pb = _trim_from_start(lst[b][1], 20.0)
                xy = np.ascontiguousarray(np.concatenate([pa, pb[1:]]))
                for (ax, ay, bx, by) in _short_gaps(gl.label, full.ox, full.oy, res, xy, float(P["short_gap_m"]),
                                                    0.25):
                    n17 += gl.capsule(ax, ay, bx, by, 0.5 * float(P["bridge_width_m"]), 17)
                    n17_gaps += 1
    del road_any
    n_masked = int(_mask_columns(gl.label, full.ox, full.oy, res, col_ok_gl, cx0, cy0))
    notes["ground_cells_written"] = {"plateau_sidewalk": n_sw, "plateau_frn_crossing": n_frn,
                                     "plateau_shared_roadway": int(n3), "plateau_lod1_shared": int(n4),
                                     "default_trunk_edge_2m": int(n5), "osm_crossing_way": n6,
                                     "osm_crossing_node": n7, "osm_crossing_nodes_used": n7_nodes,
                                     "osm_line_width": n8, "osm_line_default": n9, "w1_line_default": n11,
                                     "implied_short_gap": n17, "implied_short_gap_count": n17_gaps,
                                     "masked_outside_cells": n_masked}
    log(f"[navmesh1] 地上を塗った {time.perf_counter() - t_all:.1f} s")

    # ---------------- 地下とデッキ
    floors: dict[int, FloorRaster] = {0: gl}
    # 地下街の床を層に分ける(上から -1, -2, …)
    order = np.argsort(-ubld_layers)
    layer_floor = {int(li): -(rank + 1) for rank, li in enumerate(order)}
    tri_z = ubld_tri[:, :, 2].mean(axis=1)
    tri_layer = np.argmin(np.abs(tri_z[:, None] - ubld_layers[None, :]), axis=1)
    ug_w1 = [e for e in edges if e["band_u"] == "UG" and e["band_v"] == "UG"]
    dk_w1 = [e for e in edges if e["band_u"] == "DECK" and e["band_v"] == "DECK"]
    ug_osm = [w for w in osm_ways if (_osm_floor(w["tags"]) or 0) < 0]
    dk_osm = [w for w in osm_ways if (_osm_floor(w["tags"]) or 0) > 0]
    nw_deck = [l for l in nw_links if all(nw_nodes.get(str(l["props"].get(k)), {}).get("floor", 0.0) >= 0.5
                                          for k in ("start_id", "end_id"))]

    def floor_bbox(xys: list[np.ndarray]) -> tuple[float, float, float, float] | None:
        if not xys:
            return None
        a = np.concatenate([x.reshape(-1, x.shape[-1])[:, :2] for x in xys])
        return float(a[:, 0].min()), float(a[:, 1].min()), float(a[:, 0].max()), float(a[:, 1].max())

    ug_codes = sorted(set(layer_floor.values()) | {int(c) for c in node_floor[node_band == -1]})
    dk_codes = sorted({int(c) for c in node_floor[node_band == 1]} | {1})
    ug_counts: dict[str, dict[str, int]] = {}
    for code in ug_codes:
        src_xy = [ubld_tri[tri_layer == li] for li, f in layer_floor.items() if f == code]
        src_xy += [e["xy"] for e in ug_w1 if int(node_floor[e["u"]]) == code]
        src_xy += [w["xy"] for w in ug_osm if _osm_floor(w["tags"]) == code]
        bb = floor_bbox([s for s in src_xy if s.size])
        if bb is None:
            continue
        fr = FloorRaster(code, -1, _sub_grid(full, *bb, margin=40.0))
        g = fr.grid
        c = {"plateau_ubld_floor": 0, "w1_line_default": 0, "osm_line_width": 0, "osm_line_default": 0}
        for li, f in layer_floor.items():
            if f != code:
                continue
            t = ubld_tri[tri_layer == li]
            if t.shape[0]:
                zz = np.full(fr.label.shape, np.nan, dtype=np.float32)
                R.fill_triangles_z(zz, g.ox, g.oy, g.res, t, True)
                m = ~np.isnan(zz) & (fr.label == 0)
                fr.label[m] = 13
                fr.z[m] = zz[m]
                c["plateau_ubld_floor"] += int(m.sum())
        for w in ug_osm:
            if _osm_floor(w["tags"]) != code or w["tags"].get("highway") not in ped:
                continue
            wd = _parse_width(w["tags"])
            if wd is not None:
                c["osm_line_width"] += fr.polyline(w["xy"], 0.5 * wd, 8)
            else:
                c["osm_line_default"] += fr.polyline(w["xy"], 0.5 * LINE_WIDTH_M.get(w["tags"]["highway"], 2.0), 9)
        for e in ug_w1:
            if int(node_floor[e["u"]]) == code or int(node_floor[e["v"]]) == code:
                c["w1_line_default"] += fr.polyline(e["xy"], 0.5 * float(P["w1_line_width_m"]), 11)
        _mask_columns(fr.label, g.ox, g.oy, res, col_ok_any, cx0, cy0)
        floors[code] = fr
        ug_counts[str(code)] = c
    # デッキ
    nw_w = []
    for l in nw_deck:
        wc = int(l["props"].get("width") or 99)
        nw_w.append(HOKOUKUKAN_WIDTH_M.get(wc))
    dk_counts: dict[str, dict[str, int]] = {}
    brid_used: list[int] = []
    for code in dk_codes:
        src_xy = [e["xy"] for e in dk_w1 if int(node_floor[e["u"]]) == code or int(node_floor[e["v"]]) == code]
        src_xy += [w["xy"] for w in dk_osm if _osm_floor(w["tags"]) == code]
        if code == 1:
            src_xy += [l["xy"] for l in nw_deck]
        bb = floor_bbox([s for s in src_xy if s.size])
        if bb is None:
            continue
        fr = FloorRaster(code, 1, _sub_grid(full, *bb, margin=40.0))
        g = fr.grid
        c = {"hokoukukan_width": 0, "w1_line_default": 0, "osm_line_width": 0, "osm_line_default": 0,
             "plateau_brid_deck": 0}
        if code == 1:
            for l, wd in zip(nw_deck, nw_w):
                if wd is not None:
                    c["hokoukukan_width"] += fr.polyline(l["xy"], 0.5 * wd, 10)
        for w in dk_osm:
            if _osm_floor(w["tags"]) != code or w["tags"].get("highway") not in ped:
                continue
            wd = _parse_width(w["tags"])
            if wd is not None:
                c["osm_line_width"] += fr.polyline(w["xy"], 0.5 * wd, 8)
            else:
                c["osm_line_default"] += fr.polyline(w["xy"], 0.5 * LINE_WIDTH_M.get(w["tags"]["highway"], 2.0), 9)
        for e in dk_w1:
            if int(node_floor[e["u"]]) == code or int(node_floor[e["v"]]) == code:
                c["w1_line_default"] += fr.polyline(e["xy"], 0.5 * float(P["w1_line_width_m"]), 11)
        # 橋梁の上面(帯から brid_keep_m の中だけ)
        lines = (fr.label != 0).astype(np.uint8)
        keep = _dilate_mask(lines, int(math.ceil(float(P["brid_keep_m"]) / res)))
        for si, t in enumerate(brid_list):
            a = t[:, 1] - t[:, 0]
            b = t[:, 2] - t[:, 0]
            nrm = np.cross(a, b)
            nz = nrm[:, 2] / (np.linalg.norm(nrm, axis=1) + 1e-12)
            up = t[nz > float(P["brid_up_nz"])]
            if up.shape[0] == 0:
                continue
            zz = np.full(fr.label.shape, np.nan, dtype=np.float32)
            R.fill_triangles_z(zz, g.ox, g.oy, g.res, up, True)
            m = ~np.isnan(zz) & (keep != 0)
            if int(m.sum()) * res * res < 20.0:
                continue
            new = m & (fr.label == 0)
            fr.label[new] = 14
            fr.z[m] = np.where(np.isnan(fr.z[m]), zz[m], np.maximum(fr.z[m], zz[m]))
            c["plateau_brid_deck"] += int(new.sum())
            brid_used.append(si)
        _mask_columns(fr.label, g.ox, g.oy, res, col_ok_any, cx0, cy0)
        floors[code] = fr
        dk_counts[str(code)] = c
    notes["ug_cells_written"] = ug_counts
    notes["deck_cells_written"] = dk_counts
    notes["brid_structures_used"] = sorted(set(brid_used))
    codes = sorted(floors)
    fi_of = {c: i for i, c in enumerate(codes)}

    outputs, stats, final = _finish(P, floors, codes, edges, node_xy, node_floor, entrances_frn, nw_links, nw_nodes,
                                    dem, dgrid, cix, ciy, cband, out_dir, notes, log)
    build_s = round(time.perf_counter() - t_all, 1)  # 壁時計は見出しに入れない(見出しも 2 回組んで同じ=§0-1)
    in_paths = [world_dir / "w1_nodes.parquet", world_dir / "w1_edges.parquet", world_dir / "w1_edge_geometry.npz",
                world_dir / "w2_cells.parquet", data_root / "plateau" / "ubld_lod4_mesh.npz",
                data_root / "plateau" / "extras.npz", data_root / "spatial" / "osm_walk" / "osm_walk_raw.json",
                data_root / "research_cache" / "r58" / "shibuyananbu_link_2020.geojson",
                data_root / "research_cache" / "r58" / "shibuyananbu_node_2020.geojson"]
    in_paths += sorted((udx / "tran").glob("*.gml")) + sorted((udx / "frn").glob("*.gml")) + sorted(
        (udx / "dem").glob("*.gml"))
    gates = _gates(stats, final, res)
    result = StageResult(
        stage=STAGE, stage_version=STAGE_VERSION, input_hash=_input_hash(in_paths, data_root),
        param_hash=param_hash(P), params=P, outputs=outputs + [{"path": NV.NAV1_META,
                                                               "sha256": sha256_file(out_dir / NV.NAV1_META),
                                                               "bytes": (out_dir / NV.NAV1_META).stat().st_size,
                                                               "rows": None}],
        gates=gates, catalog_classes=["WalkableSurface", "VerticalConnector"], expedients=list(NAVMESH1_EXPEDIENTS),
        notes=_jsonable(notes))
    write_header(out_dir, result)
    log(f"[navmesh1] 終わり {build_s} s・門 {'合格' if result.all_passed else '不合格'}")
    return result


def _finish(P, floors, codes, edges, node_xy, node_floor, entrances_frn, nw_links, nw_nodes, dem, dgrid, cix, ciy,
            cband, out_dir, notes, log):
    """塗り終えた階 → 高さの既定・分ける・接続口・つなぎ(回す)・仕上げ・書く・記録(合成の小さな面の試験もここを通す)。"""
    fi_of = {c: i for i, c in enumerate(codes)}
    res = floors[codes[0]].grid.res
    n_nodes = int(node_xy.shape[0])
    lut, lcx0, lcy0 = NV.cell_lookup_table(cix, ciy, cband)
    clipped = np.zeros(len(NV.SOURCE_CODES) + 2, dtype=np.int64)
    n_edges = len(edges)

    def dem_at(x, y):
        return float(NV.dem_z(dem, dgrid.ox, dgrid.oy, dgrid.res, float(x), float(y)))

    # ---------------- 高さの既定(DEM・デッキ・地下)
    def fill_floor_z(fr: FloorRaster) -> None:
        if fr.code == 0:
            return
        g = fr.grid
        js, is_ = np.nonzero((fr.label != 0) & np.isnan(fr.z))
        if js.size == 0:
            return
        xc = g.ox + (is_ + 0.5) * g.res
        yc = g.oy + (js + 0.5) * g.res
        base = np.asarray([dem_at(x, y) for x, y in zip(xc, yc)], dtype=np.float32) if js.size < 2_000_000 else None
        if fr.code > 0:
            fr.z[js, is_] = base + float(P["deck_height_m"]) * fr.code
        else:
            fr.z[js, is_] = base - float(P["ug_depth_m"]) * (-fr.code)

    for fr in floors.values():
        fill_floor_z(fr)

    # ---------------- 分けて、接続口を引き、つなぐ(回す)
    rounds = []
    gap_cells = {str(c): 0 for c in codes}
    for rnd in range(int(P["bridge_rounds"]) + 1):
        for c in codes:
            gap_cells[str(c)] += int(_close_gaps(floors[c].label, int(P["close_gap_cells"]), 16))
            # 〔段 1 の検収 M3〕W2 のセルの無い所(その層のセルも地上のセルも無い 100 m の升)の目は消す=面の上の体のセルは -1 にならない
            g = floors[c].grid
            if P.get("clip_to_cells", True):
                _mask_by_cells(floors[c].label, g.ox, g.oy, g.res, lut, lcx0, lcy0, float(CELL_M),
                               int(floors[c].band), clipped, BRIDGE_W1_LABEL)
        mesh_parts = _decompose(floors, codes)
        links = _make_links(P, mesh_parts, floors, codes, fi_of, edges, node_xy, node_floor, entrances_frn,
                            nw_links, nw_nodes, dem_at)
        comp = _components(mesh_parts, links)
        anchors = _anchors(P, mesh_parts, floors, codes, fi_of, node_xy, node_floor)
        need_stub = [i for i in range(n_nodes) if anchors["run"][i] < 0]
        bridges = _bridge_candidates(P, mesh_parts, floors, codes, fi_of, comp, anchors, edges, node_floor)
        info = {"round": rnd, "runs": int(mesh_parts["n_runs"]), "strips": int(mesh_parts["n_strips"]),
                "links": int(links["n"]), "components": int(np.unique(comp).size),
                "w1_nodes_far": len(need_stub), "w1_edges_split": len(bridges)}
        rounds.append(info)
        log(f"[navmesh1] 回 {rnd}: {info}")
        if rnd == int(P["bridge_rounds"]) or (not need_stub and not bridges):
            break
        for i in need_stub:
            if int(node_floor[i]) not in floors:
                continue
            fr = floors[int(node_floor[i])]
            r, px, py, d = _nearest_any(mesh_parts, fi_of[int(node_floor[i])], node_xy[i, 0], node_xy[i, 1],
                                        float(P["stub_radius_m"]))
            if r >= 0:
                fr.capsule(node_xy[i, 0], node_xy[i, 1], px, py, 0.5 * float(P["bridge_width_m"]), 15)
            else:
                fr.capsule(node_xy[i, 0], node_xy[i, 1], node_xy[i, 0], node_xy[i, 1], 1.0, 15)
        for (code, ax, ay, bx, by) in bridges:
            floors[code].capsule(ax, ay, bx, by, 0.5 * float(P["bridge_width_m"]), 12)
        for fr in floors.values():
            fill_floor_z(fr)
    notes["rounds"] = rounds
    notes["clipped_outside_cells_m2_by_source"] = {
        NV.SOURCE_CODES[k]: round(float(clipped[k]) * res * res, 1) for k in NV.SOURCE_CODES if clipped[k] > 0}
    notes["w1_interband_flat"] = links.get("flat_w1", [])
    notes["gap_fill_cells"] = gap_cells

    # ---------------- 仕上げ(帯の属性・通り道の印)
    final = _finalize(P, mesh_parts, floors, codes, dem_at)
    corridor = _corridor(P, mesh_parts, floors, codes, fi_of, edges, node_floor, links)

    # ---------------- 書く
    outputs = []
    outputs.append(write_parquet(out_dir, "nav1_runs.parquet", {
        "floor": final["run_floor"], "row": final["run_row"], "x0": final["run_x0"], "x1": final["run_x1"],
        "strip": final["run_strip"], "src": final["run_src"]}))
    outputs.append(write_parquet(out_dir, "nav1_strips.parquet", {
        "strip": np.arange(final["n_strips"], dtype=np.int32), "floor": final["strip_floor"],
        "z": final["strip_z"], "cx": final["strip_cx"], "cy": final["strip_cy"],
        "area_m2": final["strip_area"], "src": final["strip_src"], "comp": final["strip_comp_of"](comp)}))
    outputs.append(write_parquet(out_dir, "nav1_portals.parquet", {
        "lo_run": final["p_lo"], "hi_run": final["p_hi"], "y": final["p_y"], "x0": final["p_x0"],
        "x1": final["p_x1"]}))
    outputs.append(write_parquet(out_dir, "nav1_links.parquet", {k: links[k] for k in (
        "kind", "a_x", "a_y", "a_floor", "a_strip", "b_x", "b_y", "b_floor", "b_strip", "rise_m", "len_m",
        "width_m", "cap_per_min", "wait_s", "src", "w1_edge")}))
    outputs.append(write_parquet(out_dir, "nav1_anchors.parquet", {
        "node": np.arange(n_nodes, dtype=np.int32), "x": anchors["x"], "y": anchors["y"],
        "floor": anchors["fi"], "run": anchors["run"], "dist_m": anchors["dist"]}))
    outputs.append(write_parquet(out_dir, "nav1_corridor.parquet", {"edge": corridor[0], "strip": corridor[1]}))
    outputs.append(write_npy(out_dir, "nav1_dem.npy", dem))
    floors_meta = [{"code": int(c), "band": int(floors[c].band), "ox": floors[c].grid.ox, "oy": floors[c].grid.oy,
                    "nx": floors[c].grid.nx, "ny": floors[c].grid.ny} for c in codes]
    meta = {"schema": "shibuya.nav1/1", "stage_version": STAGE_VERSION, "res_m": res, "floors": floors_meta,
            "dem": {"ox": dgrid.ox, "oy": dgrid.oy, "res": dgrid.res, "nx": dgrid.nx, "ny": dgrid.ny},
            "n_w1_nodes": n_nodes, "n_w1_edges": n_edges, "params": P,
            "source_codes": {str(k): v for k, v in NV.SOURCE_CODES.items()},
            "link_kinds": list(NV.LINK_KINDS),
            "files": {o["path"]: {"sha256": o["sha256"], "bytes": o["bytes"], "rows": o["rows"]} for o in outputs}}
    (out_dir / NV.NAV1_META).write_bytes(canonical_json_bytes(meta) + b"\n")

    # ---------------- 門と記録
    stats = _stats(final, links, anchors, comp, floors, codes, res, edges, node_floor)
    notes.update(stats)
    fband = np.asarray([floors[c].band for c in codes], dtype=np.int8)
    fox = np.asarray([floors[c].grid.ox for c in codes], dtype=np.float64)
    foy = np.asarray([floors[c].grid.oy for c in codes], dtype=np.float64)
    # 〔段 1 の検収 M3〕セルの面積は体のセルと同じ引き表(つなぎの帯は最も近い W2 のセルへ倒す)で数える
    lut_f, _fx0, _fy0 = NV.cell_lookup_table(cix, ciy, cband, fill_nearest=True)
    cell_area = NV.area_by_cell(lut_f, lcx0, lcy0, float(CELL_M), final["run_floor"], final["run_row"],
                                final["run_x0"], final["run_x1"], fband, fox, foy, res, int(cix.size))
    # 帯でない面のうち W2 のセルの外にある目(門=0)と、最も近いセルへ倒したつなぎの帯の目(塗りの格子で数える)
    out_nb = np.zeros(len(NV.SOURCE_CODES) + 2, dtype=np.int64)
    out_all = np.zeros(len(NV.SOURCE_CODES) + 2, dtype=np.int64)
    for c in codes:
        g = floors[c].grid
        _mask_by_cells(floors[c].label.copy(), g.ox, g.oy, g.res, lut, lcx0, lcy0, float(CELL_M), int(floors[c].band),
                       out_nb, BRIDGE_W1_LABEL)
        _mask_by_cells(floors[c].label.copy(), g.ox, g.oy, g.res, lut, lcx0, lcy0, float(CELL_M), int(floors[c].band),
                       out_all, -1)
    stats["cell_area_m2_max"] = round(float(cell_area.max()), 1)
    stats["cells_with_walkable_area"] = int((cell_area > 0).sum())
    stats["cells_over_cell_area"] = int((cell_area > CELL_M * CELL_M + 1e-6).sum())
    stats["area_outside_cells_m2"] = round(float(out_nb.sum()) * res * res, 1)
    stats["bridge_area_outside_cells_to_nearest_m2"] = round(float(out_all[BRIDGE_W1_LABEL]) * res * res, 1)
    stats["cell_area_m2_p50"] = round(float(np.median(cell_area[cell_area > 0])), 1) if (cell_area > 0).any() else 0.0
    notes.update({k: stats[k] for k in ("cell_area_m2_max", "cells_with_walkable_area", "cells_over_cell_area",
                                       "cell_area_m2_p50", "area_outside_cells_m2",
                                       "bridge_area_outside_cells_to_nearest_m2")})
    return outputs, stats, final


def _input_hash(paths: list[Path], root: Path) -> str:
    """入力ファイルの (名, sha256) の列のハッシュ(置き場の道筋を入れない=別の置き場に組んでも同じ)。"""
    import hashlib

    rows = [f"{p.name}:{sha256_file(p)}" for p in paths]
    return hashlib.sha256(chr(10).join(rows).encode("utf-8")).hexdigest()


def _jsonable(o: Any) -> Any:
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return _jsonable(o.tolist())
    return o


# ====================================================================== 分ける
def _decompose(floors: dict[int, FloorRaster], codes: list[int]) -> dict[str, Any]:
    """全部の階の塗り → ラン・門・帯(階の順・行の順)。"""
    run_parts = []
    base = 0
    for fi, code in enumerate(codes):
        fr = floors[code]
        row, x0, x1, src, row_ptr = M.extract_runs(fr.label, 32)
        lo, hi, ox0, ox1 = M.run_overlaps(row_ptr, x0, x1)
        run_parts.append({"fi": fi, "row": row, "x0": x0, "x1": x1, "src": src, "row_ptr": row_ptr,
                          "lo": lo.astype(np.int64) + base, "hi": hi.astype(np.int64) + base, "ox0": ox0,
                          "ox1": ox1, "base": base})
        base += row.size
    n_runs = base
    run_row = np.concatenate([p["row"] for p in run_parts]).astype(np.int32)
    run_x0 = np.concatenate([p["x0"] for p in run_parts]).astype(np.int32)
    run_x1 = np.concatenate([p["x1"] for p in run_parts]).astype(np.int32)
    run_src = np.concatenate([p["src"] for p in run_parts]).astype(np.uint8)
    run_floor = np.concatenate([np.full(p["row"].size, p["fi"], np.int8) for p in run_parts])
    p_lo = np.concatenate([p["lo"] for p in run_parts])
    p_hi = np.concatenate([p["hi"] for p in run_parts])
    p_ox0 = np.concatenate([p["ox0"] for p in run_parts])
    p_ox1 = np.concatenate([p["ox1"] for p in run_parts])
    strip, n_strips, cross = M.build_strips(n_runs, p_lo, p_hi)
    return {"grids": [floors[c].grid for c in codes], "n_runs": n_runs, "run_row": run_row, "run_x0": run_x0, "run_x1": run_x1, "run_src": run_src,
            "run_floor": run_floor, "parts": run_parts, "p_lo": p_lo, "p_hi": p_hi, "p_ox0": p_ox0, "p_ox1": p_ox1,
            "strip": strip, "n_strips": int(n_strips), "cross": cross}


def _nearest_any(mp: dict, fi: int, x: float, y: float, rmax: float) -> tuple[int, float, float, float]:
    part = mp["parts"][fi]
    # 階の格子(parts に原点が無いので floors から渡す代わりに、_grid に控えた値を使う)
    g = mp["grids"][fi]
    comp = np.zeros(part["row"].size, dtype=np.int64)
    r, px, py, d = M.nearest_point_in_comp(part["row_ptr"], part["x0"], part["x1"], comp, g.ox, g.oy, g.ny, g.res,
                                           float(x), float(y), float(rmax), 0)
    return (int(r) + part["base"] if r >= 0 else -1), float(px), float(py), float(d)


def _make_links(P, mp, floors, codes, fi_of, edges, node_xy, node_floor, entrances_frn, nw_links, nw_nodes, dem_at):
    """接続口(W1 の階をまたぐ辺・PLATEAU の地下出入口・歩行空間ネットワークの階の違うリンク)。"""
    snap = float(P["link_snap_m"])
    rows: list[dict] = []
    flat_w1: list[dict] = []  # 階をまたぐのに勾配がほぼ 0 の W1 の辺(層の付け違いの疑い・数えるだけ)

    def z_of(code: int, x: float, y: float) -> float:
        fr = floors[code]
        if code == 0:
            return dem_at(x, y)
        g = fr.grid
        j, i = g.row_of(y), g.col_of(x)
        if 0 <= j < g.ny and 0 <= i < g.nx and not math.isnan(fr.z[j, i]):
            return float(fr.z[j, i])
        base = dem_at(x, y)
        return base + (float(P["deck_height_m"]) * code if code > 0 else -float(P["ug_depth_m"]) * (-code))

    def add(kind, ca, ax, ay, cb, bx, by, length, width, src, w1e, ra=snap, rb=snap):
        if ca not in fi_of or cb not in fi_of:
            return False
        fa, fb = fi_of[ca], fi_of[cb]
        r1, px, py, _d1 = _nearest_any(mp, fa, ax, ay, ra)
        r2, qx, qy, _d2 = _nearest_any(mp, fb, bx, by, rb)
        if r1 < 0 or r2 < 0:
            return False
        za = z_of(ca, px, py)
        zb = z_of(cb, qx, qy)
        horiz = max(float(length), math.hypot(qx - px, qy - py), 0.1)
        rise = abs(zb - za)
        kind = _ramp_or_stairs(P, kind, rise, horiz)  # 勾配が傾斜路の上限(1/12・16 cm 以下は 1/8)を超えるスロープは階段
        if src == 0 and rise / horiz < float(P["flat_interband_grade"]):
            flat_w1.append({"edge": int(w1e), "len_m": round(horiz, 1), "rise_m": round(rise, 2)})
        rows.append({"kind": kind, "a_x": px, "a_y": py, "a_floor": fa, "a_run": r1, "b_x": qx, "b_y": qy,
                     "b_floor": fb, "b_run": r2, "rise_m": zb - za,
                     "len_m": max(float(length), math.hypot(qx - px, qy - py)), "width_m": width, "src": src,
                     "w1_edge": w1e})
        return True

    n_w1 = 0
    for e in edges:
        fu, fv = int(node_floor[e["u"]]), int(node_floor[e["v"]])
        if fu == fv:
            continue
        k = e["klass"]
        kind = NV.LINK_STAIRS if k == "steps" else (NV.LINK_ELEVATOR if k == "elevator" else NV.LINK_RAMP)
        if add(kind, fu, node_xy[e["u"], 0], node_xy[e["u"], 1], fv, node_xy[e["v"], 0], node_xy[e["v"], 1],
               e["length_m"], float(LINK_VALUES["stairs_width_default_m"]), 0, e["edge"],
               ra=float(P["anchor_radius_m"]), rb=float(P["anchor_radius_m"])):
            n_w1 += 1
    n_frn = 0
    ug_top = max([c for c in codes if c < 0], default=None)
    for v in entrances_frn:
        if ug_top is None:
            break
        c = v[:, :2].mean(axis=0)
        if add(NV.LINK_STAIRS, 0, c[0], c[1], ug_top, c[0], c[1], 0.0, float(LINK_VALUES["stairs_width_default_m"]),
               1, -1, ra=float(P["frn_entrance_ground_m"]), rb=float(P["frn_entrance_ug_m"])):
            n_frn += 1
    n_nw = 0
    for l in nw_links:
        rt = int(l["props"].get("route_type") or 1)
        if rt not in HOKOUKUKAN_ROUTE_LINK:
            continue
        a = nw_nodes.get(str(l["props"].get("start_id")))
        b = nw_nodes.get(str(l["props"].get("end_id")))
        if a is None or b is None:
            continue

        def fcode(fl: float) -> int:
            return 0 if fl == 0.0 else (1 if fl > 0 else -1)

        ca, cb = fcode(a["floor"]), fcode(b["floor"])
        if ca == cb:
            continue
        wd = HOKOUKUKAN_WIDTH_M.get(int(l["props"].get("width") or 99), float(LINK_VALUES["stairs_width_default_m"]))
        xy = l["xy"]
        length = float(np.hypot(*np.diff(xy, axis=0).T).sum()) if xy.shape[0] > 1 else 0.0
        if add(HOKOUKUKAN_ROUTE_LINK[rt], ca, a["x"], a["y"], cb, b["x"], b["y"], length, wd, 2, -1):
            n_nw += 1
    # まとめる(同じ種類・同じ階の組・両端が近い=先に入れた方を残す)
    keep = []
    dd = float(P["link_dedup_m"])
    for r in rows:
        dup = False
        for q in keep:
            if q["kind"] == r["kind"] and {q["a_floor"], q["b_floor"]} == {r["a_floor"], r["b_floor"]}:
                if q["a_floor"] == r["a_floor"]:
                    d1 = math.hypot(q["a_x"] - r["a_x"], q["a_y"] - r["a_y"])
                    d2 = math.hypot(q["b_x"] - r["b_x"], q["b_y"] - r["b_y"])
                else:
                    d1 = math.hypot(q["a_x"] - r["b_x"], q["a_y"] - r["b_y"])
                    d2 = math.hypot(q["b_x"] - r["a_x"], q["b_y"] - r["a_y"])
                if d1 <= dd and d2 <= dd and q["w1_edge"] < 0 and r["w1_edge"] < 0:
                    dup = True
                    break
        if not dup:
            keep.append(r)
    n = len(keep)
    strip = mp["strip"]
    out = {"n": n, "n_by_src": {"w1": n_w1, "plateau_frn_entrance": n_frn, "hokoukukan_2020": n_nw,
                                "kept_after_dedup": n}, "flat_w1": flat_w1}
    cap = []
    wait = []
    for r in keep:
        if r["kind"] == NV.LINK_STAIRS:
            cap.append(float(LINK_VALUES["stairs_cap_per_min_per_m"]) * r["width_m"])
            wait.append(0.0)
        elif r["kind"] == NV.LINK_ESCALATOR:
            cap.append(float(LINK_VALUES["escalator_cap_per_min"]))
            wait.append(0.0)
        elif r["kind"] == NV.LINK_ELEVATOR:
            iv = float(LINK_VALUES["elevator_interval_s"])
            cap.append(float(LINK_VALUES["elevator_capacity_persons"]) * float(SECONDS_PER_MINUTE) / iv)
            wait.append(0.5 * iv)
        else:
            cap.append(0.0)
            wait.append(0.0)
    out.update({
        "kind": np.asarray([r["kind"] for r in keep], dtype=np.int8),
        "a_x": np.asarray([r["a_x"] for r in keep], dtype=np.float64),
        "a_y": np.asarray([r["a_y"] for r in keep], dtype=np.float64),
        "a_floor": np.asarray([r["a_floor"] for r in keep], dtype=np.int8),
        "a_strip": np.asarray([strip[r["a_run"]] for r in keep], dtype=np.int32),
        "b_x": np.asarray([r["b_x"] for r in keep], dtype=np.float64),
        "b_y": np.asarray([r["b_y"] for r in keep], dtype=np.float64),
        "b_floor": np.asarray([r["b_floor"] for r in keep], dtype=np.int8),
        "b_strip": np.asarray([strip[r["b_run"]] for r in keep], dtype=np.int32),
        "rise_m": np.asarray([r["rise_m"] for r in keep], dtype=np.float32),
        "len_m": np.asarray([r["len_m"] for r in keep], dtype=np.float32),
        "width_m": np.asarray([r["width_m"] for r in keep], dtype=np.float32),
        "cap_per_min": np.asarray(cap, dtype=np.float32),
        "wait_s": np.asarray(wait, dtype=np.float32),
        "src": np.asarray([r["src"] for r in keep], dtype=np.int8),
        "w1_edge": np.asarray([r["w1_edge"] for r in keep], dtype=np.int32),
    })
    return out


def _components(mp: dict, links: dict) -> np.ndarray:
    """ランの連結成分(門と接続口で)→ ランごとの成分(代表=最小のラン)。"""
    n = mp["n_runs"]
    strip = mp["strip"]
    # 接続口の両端のランは帯の最初のランで代える(帯の中はつながっている)
    first_run = np.full(mp["n_strips"], -1, dtype=np.int64)
    for r in range(n - 1, -1, -1):
        first_run[strip[r]] = r
    la = first_run[np.asarray(links["a_strip"], dtype=np.int64)] if links["n"] else np.zeros(0, np.int64)
    lb = first_run[np.asarray(links["b_strip"], dtype=np.int64)] if links["n"] else np.zeros(0, np.int64)
    ea = np.concatenate([mp["p_lo"], la]).astype(np.int64)
    eb = np.concatenate([mp["p_hi"], lb]).astype(np.int64)
    return M.union_find_components(n, ea, eb)


def _anchors(P, mp, floors, codes, fi_of, node_xy, node_floor) -> dict[str, np.ndarray]:
    """W1 の節ごとの面の上の点(同じ階の半径の中・無ければ同じ層のほかの階)。"""
    n = node_xy.shape[0]
    ax = node_xy[:, 0].copy()
    ay = node_xy[:, 1].copy()
    afi = np.full(n, -1, dtype=np.int8)
    arun = np.full(n, -1, dtype=np.int32)
    adist = np.full(n, np.inf, dtype=np.float32)
    rr = float(P["anchor_radius_m"])
    for i in range(n):
        code = int(node_floor[i])
        cands = [code] + [c for c in codes if c != code and (c > 0) == (code > 0) and (c < 0) == (code < 0)]
        for c in cands:
            if c not in fi_of:
                continue
            r, px, py, d = _nearest_any(mp, fi_of[c], node_xy[i, 0], node_xy[i, 1], rr)
            if r >= 0:
                ax[i], ay[i], afi[i], arun[i], adist[i] = px, py, fi_of[c], r, d
                break
    return {"x": ax, "y": ay, "fi": afi, "run": arun, "dist": adist}


def _bridge_candidates(P, mp, floors, codes, fi_of, comp, anchors, edges, node_floor):
    """W1 の同じ階の辺の両端が別の成分 → (階, ax, ay, bx, by)=辺の近くの 2 つの成分の最も近い 2 点。"""
    out = []
    buf = float(P["bridge_buffer_m"])
    seen_pairs = set()
    for e in edges:
        u, v = e["u"], e["v"]
        if anchors["run"][u] < 0 or anchors["run"][v] < 0:
            continue
        if anchors["fi"][u] != anchors["fi"][v]:
            continue
        ca, cb = int(comp[anchors["run"][u]]), int(comp[anchors["run"][v]])
        if ca == cb or (ca, cb) in seen_pairs:
            continue
        fi = int(anchors["fi"][u])
        part = mp["parts"][fi]
        g = mp["grids"][fi]
        rc = comp[part["base"]:part["base"] + part["row"].size]
        xy = e["xy"]
        # 線を 1 m ごとに区切って、両方の成分の最も近い点の和が最も小さい所
        pts = [xy[0]]
        for k in range(xy.shape[0] - 1):
            L = float(np.hypot(*(xy[k + 1] - xy[k])))
            m = max(1, int(L))
            for t in range(1, m + 1):
                pts.append(xy[k] + (xy[k + 1] - xy[k]) * t / m)
        best = None
        for p in pts:
            r1, ax, ay, d1 = M.nearest_point_in_comp(part["row_ptr"], part["x0"], part["x1"], rc, g.ox, g.oy, g.ny,
                                                     g.res, float(p[0]), float(p[1]), buf, ca)
            if r1 < 0:
                continue
            r2, bx, by, d2 = M.nearest_point_in_comp(part["row_ptr"], part["x0"], part["x1"], rc, g.ox, g.oy, g.ny,
                                                     g.res, float(p[0]), float(p[1]), buf, cb)
            if r2 < 0:
                continue
            gap = math.hypot(ax - bx, ay - by)
            if best is None or gap < best[0] - 1e-9:
                best = (gap, ax, ay, bx, by)
        if best is None:
            # 辺の近くに片方の成分が無い=両端の点を直に結ぶ
            best = (0.0, anchors["x"][u], anchors["y"][u], anchors["x"][v], anchors["y"][v])
        seen_pairs.add((ca, cb))
        seen_pairs.add((cb, ca))
        out.append((codes[fi], best[1], best[2], best[3], best[4]))
    return out


def _finalize(P, mp, floors, codes, dem_at) -> dict[str, Any]:
    """帯の属性(高さ・中心・面積・出どころ)と門の座標。"""
    strip = mp["strip"]
    ns = mp["n_strips"]
    res = floors[codes[0]].grid.res
    fi = mp["run_floor"].astype(np.int64)
    gox = np.asarray([floors[c].grid.ox for c in codes])
    goy = np.asarray([floors[c].grid.oy for c in codes])
    xc = gox[fi] + 0.5 * (mp["run_x0"] + mp["run_x1"]) * res
    yc = goy[fi] + (mp["run_row"] + 0.5) * res
    w = (mp["run_x1"] - mp["run_x0"]).astype(np.float64)
    area = np.bincount(strip, weights=w * res * res, minlength=ns)
    cx = np.bincount(strip, weights=w * xc, minlength=ns) / np.maximum(np.bincount(strip, weights=w, minlength=ns),
                                                                         1e-12)
    cy = np.bincount(strip, weights=w * yc, minlength=ns) / np.maximum(np.bincount(strip, weights=w, minlength=ns),
                                                                         1e-12)
    sfloor = np.zeros(ns, dtype=np.int8)
    sfloor[strip] = mp["run_floor"]
    # 高さ: 地上は DEM、ほかは階の高さの格子(ランの中心)
    zr = np.empty(mp["n_runs"], dtype=np.float64)
    for f, code in enumerate(codes):
        sel = np.flatnonzero(fi == f)
        if code == 0:
            zr[sel] = [dem_at(x, y) for x, y in zip(xc[sel], yc[sel])]
        else:
            fr = floors[code]
            jj = mp["run_row"][sel]
            ii = ((mp["run_x0"][sel] + mp["run_x1"][sel]) // 2)
            zz = fr.z[jj, ii].astype(np.float64)
            zr[sel] = zz
    zr = np.where(np.isnan(zr), np.nanmean(zr) if np.isfinite(zr).any() else 0.0, zr)
    sz = (np.bincount(strip, weights=w * zr, minlength=ns) / np.maximum(np.bincount(strip, weights=w, minlength=ns),
                                                                         1e-12)).astype(np.float32)
    # 出どころ: 帯の中で最も目の多い札
    src_cnt = np.zeros((ns, 32), dtype=np.float64)
    np.add.at(src_cnt, (strip, mp["run_src"].astype(np.int64)), w)
    ssrc = np.argmax(src_cnt, axis=1).astype(np.uint8)
    # 門(帯をまたぐものだけを書く=帯の中の門はランから作り直せる)
    cross = mp["cross"]
    lo = mp["p_lo"][cross]
    hi = mp["p_hi"][cross]
    pf = mp["run_floor"][lo].astype(np.int64)
    py = goy[pf] + (mp["run_row"][lo].astype(np.float64) + 1.0) * res
    px0 = gox[pf] + mp["p_ox0"][cross].astype(np.float64) * res
    px1 = gox[pf] + mp["p_ox1"][cross].astype(np.float64) * res

    def strip_comp_of(comp):
        out = np.zeros(ns, dtype=np.int64)
        out[strip] = comp
        return out

    return {"n_strips": ns, "run_floor": mp["run_floor"], "run_row": mp["run_row"], "run_x0": mp["run_x0"],
            "run_x1": mp["run_x1"], "run_strip": strip.astype(np.int32), "run_src": mp["run_src"],
            "strip_floor": sfloor, "strip_z": sz, "strip_cx": cx, "strip_cy": cy, "strip_area": area,
            "strip_src": ssrc, "p_lo": lo.astype(np.int32), "p_hi": hi.astype(np.int32), "p_y": py, "p_x0": px0,
            "p_x1": px1, "strip_comp_of": strip_comp_of, "src_area_m2": np.bincount(
                mp["run_src"].astype(np.int64), weights=w * res * res, minlength=32)}


@nb.njit(cache=True)
def _strips_near_polyline(row_ptr, x0, x1, strip, base, ox, oy, ny, res, xs, ys, radius, mark, stamp, out, n_out):
    """折れ線から ``radius`` の中に掛かるランの帯(``mark`` で重複を除く)を ``out`` に足す。"""
    xmin = xs.min() - radius
    xmax = xs.max() + radius
    j0 = max(0, int(math.floor((ys.min() - radius - oy) / res)))
    j1 = min(ny - 1, int(math.floor((ys.max() + radius - oy) / res)))
    r2 = radius * radius
    for j in range(j0, j1 + 1):
        yc = oy + (j + 0.5) * res
        for r in range(row_ptr[j], row_ptr[j + 1]):
            xa = ox + x0[r] * res
            xb = ox + x1[r] * res
            if xb < xmin or xa > xmax:
                continue
            s = strip[base + r]
            if mark[s] == stamp:
                continue
            # ランの線分(y=yc・[xa, xb])と折れ線の最短距離
            hit = False
            for k in range(xs.shape[0] - 1):
                ax_ = xs[k]; ay_ = ys[k]; bx_ = xs[k + 1]; by_ = ys[k + 1]
                # 折れ線の線分上の点をランの線分に寄せた距離を、両端と交差で調べる(粗い: 線分を 1 m で区切る)
                L = math.sqrt((bx_ - ax_) ** 2 + (by_ - ay_) ** 2)
                m = max(1, int(L))
                for t in range(m + 1):
                    px = ax_ + (bx_ - ax_) * t / m
                    py = ay_ + (by_ - ay_) * t / m
                    cx = min(max(px, xa), xb)
                    d2 = (cx - px) ** 2 + (yc - py) ** 2
                    if d2 <= r2:
                        hit = True
                        break
                if hit:
                    break
            if hit:
                mark[s] = stamp
                out[n_out] = s
                n_out += 1
    return n_out


def _corridor(P, mp, floors, codes, fi_of, edges, node_floor, links) -> tuple[np.ndarray, np.ndarray]:
    """W1 の辺 → 近くの帯(全部の階=デッキと地下も・階をまたぐ辺は接続口の帯も)。(辺, 帯) の昇順。

    W1 の車の道の中心の線の上を人は歩けない所(デッキで渡る交差点など)があるので、通り道の印はどの階の帯も含める。
    """
    radius = float(P["corridor_radius_m"])
    strip = mp["strip"].astype(np.int64)
    mark = np.zeros(mp["n_strips"], dtype=np.int64)
    buf = np.empty(mp["n_strips"], dtype=np.int64)
    ce, cs = [], []
    stamp = 0
    link_by_edge: dict[int, list[int]] = {}
    for li, we in enumerate(np.asarray(links.get("w1_edge", np.zeros(0)), dtype=np.int64)):
        if we >= 0:
            link_by_edge.setdefault(int(we), []).append(li)
    for e in edges:
        stamp += 1
        n_out = 0
        for code in codes:
            fi = fi_of[code]
            part = mp["parts"][fi]
            g = mp["grids"][fi]
            xy = e["xy"]
            n_out = _strips_near_polyline(part["row_ptr"], part["x0"], part["x1"], strip, part["base"], g.ox, g.oy,
                                          g.ny, g.res, np.ascontiguousarray(xy[:, 0]),
                                          np.ascontiguousarray(xy[:, 1]), radius, mark, stamp, buf, n_out)
        for li in link_by_edge.get(e["edge"], []):
            for s in (int(links["a_strip"][li]), int(links["b_strip"][li])):
                if mark[s] != stamp:
                    mark[s] = stamp
                    buf[n_out] = s
                    n_out += 1
        if n_out:
            s_sorted = np.sort(buf[:n_out])
            ce.append(np.full(n_out, e["edge"], dtype=np.int32))
            cs.append(s_sorted.astype(np.int32))
    if not ce:
        return np.zeros(0, np.int32), np.zeros(0, np.int32)
    return np.concatenate(ce), np.concatenate(cs)


# ====================================================================== 記録と門
def _stats(final, links, anchors, comp, floors, codes, res, edges, node_floor) -> dict[str, Any]:
    src_area = final["src_area_m2"]
    by_src = {NV.SOURCE_CODES[k]: round(float(src_area[k]), 1) for k in NV.SOURCE_CODES if src_area[k] > 0}
    groups = {"plateau": (1, 2, 3, 4, 13, 14), "hokoukukan": (10,), "osm": (6, 8), "default": (5, 7, 9, 11),
              "bridge": (12, 15, 16, 17)}
    by_group = {g: round(float(sum(src_area[k] for k in ks)), 1) for g, ks in groups.items()}
    fl = final["run_floor"].astype(np.int64)
    w = (final["run_x1"] - final["run_x0"]).astype(np.float64) * res * res
    area_by_floor = {str(codes[f]): round(float(w[fl == f].sum()), 1) for f in range(len(codes))}
    runs_by_floor = {str(codes[f]): int((fl == f).sum()) for f in range(len(codes))}
    strips_by_floor = {str(codes[f]): int((final["strip_floor"] == f).sum()) for f in range(len(codes))}
    kinds = {NV.LINK_KINDS[k]: int((links["kind"] == k).sum()) for k in range(len(NV.LINK_KINDS))} if links["n"] else {}
    comp_size = np.bincount(np.unique(comp, return_inverse=True)[1], weights=w)
    big = float(comp_size.max()) if comp_size.size else 0.0
    # W1 の辺で両端の点が同じ成分か(同じ階の辺)
    n_same = n_split = 0
    for e in edges:
        ru, rv = anchors["run"][e["u"]], anchors["run"][e["v"]]
        if ru < 0 or rv < 0:
            continue
        if comp[ru] == comp[rv]:
            n_same += 1
        else:
            n_split += 1
    main = int(np.argmax(comp_size)) if comp_size.size else -1
    uniq = np.unique(comp)
    main_comp = int(uniq[main]) if main >= 0 else -1
    anc_ok = anchors["run"] >= 0
    in_main = int(np.sum(comp[anchors["run"][anc_ok]] == main_comp))
    return {
        "area_m2_by_source": by_src, "area_m2_by_group": by_group, "area_m2_by_floor": area_by_floor,
        "runs_by_floor": runs_by_floor, "strips_by_floor": strips_by_floor, "n_runs": int(final["run_x0"].size),
        "n_strips": int(final["n_strips"]), "n_portals_between_strips": int(final["p_lo"].size),
        "links_by_kind": kinds, "links_by_source": links.get("n_by_src", {}), "n_links": int(links["n"]),
        "n_components": int(uniq.size), "largest_component_area_share": round(big / max(float(w.sum()), 1e-9), 4),
        "w1_nodes_anchored": int(anc_ok.sum()), "w1_nodes_in_largest": in_main,
        "w1_anchor_dist_m_p50_p95_max": np.percentile(anchors["dist"][anc_ok], [50, 95, 100]).round(2).tolist()
        if anc_ok.any() else [],
        "w1_edges_same_component": n_same, "w1_edges_split_component": n_split,
    }


def _gates(stats: dict, final: dict, res: float) -> list[Gate]:
    """資産の門(範囲・面積の上限=セル面積の超過なし=第219 の教訓・つながり)。"""
    gates = []
    # セルの面積の超過: 1 つの 100 m の列・1 つの階の歩ける面積は 10,000 m² を超えない(格子の目は重ならない)
    fl = final["run_floor"].astype(np.int64)
    gates.append(Gate("runs_positive_width", bool(np.all(final["run_x1"] > final["run_x0"])), True))
    gates.append(Gate("strips_cover_runs", int(final["run_strip"].max()) + 1 == int(final["n_strips"]), True))
    gates.append(Gate("w1_nodes_all_anchored", stats["w1_nodes_anchored"], None))
    gates.append(Gate("w1_edges_split_component", stats["w1_edges_split_component"], None))
    gates.append(Gate("largest_component_area_share", stats["largest_component_area_share"], None))
    gates.append(Gate("floor_count", len(stats["area_m2_by_floor"]), None))
    gates.append(Gate("cells_over_cell_area", stats.get("cells_over_cell_area", 0), 0))
    # 〔段 1 の検収 M3〕面はどこも W2 のセルの中(面の上の体のセルは -1 にならない)
    gates.append(Gate("area_outside_cells_m2", stats.get("area_outside_cells_m2", 0.0), 0.0))
    _ = fl
    return gates


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="段 1 ナビメッシュの構築(脇の段)")
    ap.add_argument("--data", default="data")
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--out", required=True)
    ap.add_argument("--params", default="", help="既定の値を上書きする JSON")
    args = ap.parse_args(argv)
    params = json.loads(args.params) if args.params else None
    res = build(Path(args.data), Path(args.world), Path(args.out), params=params)
    return 0 if res.all_passed else 3


if __name__ == "__main__":
    sys.exit(main())
