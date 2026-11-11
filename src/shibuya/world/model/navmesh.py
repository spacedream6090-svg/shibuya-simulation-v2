"""world.navmesh — 段 1 のナビメッシュ(多層の歩ける面)の資産と、その上の問い合わせ(numba・SR13=自前)。

正: 空間の設計の下書き ``docs/design/v2-spatial-design-round-draft.md`` §4 段 1・SR13 (a)「溶接・接続・A*・funnel を
numba で自前」・§1-1 の 3-1(位置は (x, y, 階) の連続値)・3-2 (c)(ナビメッシュの上を衝突なしで進む)。作り手は
``shibuya.build.space.navmesh1``(構築側)。資産は世界の置き場の ``nav1_*.parquet``・``nav1_dem.npy``・``nav1_meta.json``。

**面の形**(構築の記録 ``docs/bench/analysis/spatial-2026-10/sp1/README.md`` §1): 歩ける面は階ごとの 0.5 m の格子に
塗った目の集まりで、行ごとの連なり(**ラン**=横 1 行の長方形=凸)に分ける。ランは上下の行のランと重なる区間で
つながる(**門**=水平の線分)。上下に 1 対 1 でつながるランの縦の鎖を **帯**(strip)にまとめ、A* は帯の上で引き、
funnel(string pulling)は帯の中の行ごとの門まで含めた門の列で引く=**ランの和の中で最短の折れ線**(角は格子の
角)。階の間は **接続口**(Detour の off-mesh 接続と同じ形=両端の点・階・種類・長さ・速さ・容量・待ち)。

問い合わせ(どれも純関数・決定論=同点は番号の小さい方・float64・``fastmath`` なし):

- :meth:`NavMesh.locate`: (x, y, 階) → ラン(無ければ -1)。
- :meth:`NavMesh.nearest`: 階の中で最も近い歩ける点(半径の中)。
- :func:`astar_strips`: 帯の A*(重み=距離+上りの重み×上り[m]・接続口は時間を距離に直した重み)。通り道の印
  (``allow``=刻印)で探索を絞れる。
- :func:`funnel_points`: 帯の列 → 門の列 → 折れ線(Mononen 2010 の simple stupid funnel の形=R-59 で検算した移植)。

逐次ループ宣言(P4): 問い合わせの中のループは探索の展開数・門の数・行の数ぶん(numba)。体ごとの Python のループは無い
(呼び手=``engine.space.nav1`` が経路を引く体だけを回す=宣言はそちら)。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Mapping

import numba as nb
import numpy as np

__all__ = [
    "NAV1_FILES",
    "NAV1_META",
    "LINK_KINDS",
    "LINK_STAIRS",
    "LINK_ESCALATOR",
    "LINK_ELEVATOR",
    "LINK_RAMP",
    "SOURCE_CODES",
    "NavMesh",
    "navmesh_available",
    "load_navmesh",
    "locate_run",
    "nearest_point",
    "dem_z",
    "astar_strips",
    "corridor_portals",
    "funnel_points",
    "w1_turn_dijkstra",
    "cell_lookup_table",
    "cell_of",
    "area_by_cell",
]

#: 資産のファイル(``nav1_meta.json`` に各ファイルの sha256 を書く)。
NAV1_META: Final[str] = "nav1_meta.json"
NAV1_FILES: Final[tuple[str, ...]] = (
    "nav1_runs.parquet",
    "nav1_strips.parquet",
    "nav1_portals.parquet",
    "nav1_links.parquet",
    "nav1_anchors.parquet",
    "nav1_corridor.parquet",
    "nav1_dem.npy",
)

#: 接続口の種類(``link_kind``)。
LINK_STAIRS: Final[int] = 0
LINK_ESCALATOR: Final[int] = 1
LINK_ELEVATOR: Final[int] = 2
LINK_RAMP: Final[int] = 3
LINK_KINDS: Final[tuple[str, ...]] = ("stairs", "escalator", "elevator", "ramp")

#: 面の出どころの札(``strip_src`` と構築の記録の内訳)。0=歩けない。
SOURCE_CODES: Final[dict[int, str]] = {
    1: "plateau_sidewalk",        # PLATEAU 道路 LOD2/3 の歩道部 2000・島 3000
    2: "plateau_frn_crossing",    # PLATEAU 都市設備 横断歩道 1110 の外接矩形
    3: "plateau_shared_roadway",  # PLATEAU LOD2/3 の車道部(歩道の無い細い道=SR10)
    4: "plateau_lod1_shared",     # PLATEAU LOD1 の面全体(住宅街の細い道=SR10)
    5: "default_trunk_edge_2m",   # LOD1 しか無い幹線の両端 2.0 m(仮・SR10)
    6: "osm_crossing_way",        # OSM の footway=crossing の線の帯
    7: "osm_crossing_node",       # OSM の highway=crossing の点から道に直交する帯
    8: "osm_line_width",          # OSM の歩行系の線(width のタグあり)
    9: "osm_line_default",        # OSM の歩行系の線(道の種類の既定幅)
    10: "hokoukukan_width",       # 歩行空間ネットワークの幅員 4 区分(デッキ)
    11: "w1_line_default",        # W1 の辺の線(既定幅=OSM の取り直しに無い線)
    12: "bridge_w1",              # つなぎ: W1 では行けるのに面が切れていた所の帯
    13: "plateau_ubld_floor",     # PLATEAU 地下街 LOD4.1 の床
    14: "plateau_brid_deck",      # PLATEAU 橋梁 LOD2 の上面(歩く人の居るデッキと歩道橋)
    15: "anchor_stub",            # つなぎ: W1 の節から面までの短い帯(面から遠い節)
    16: "gap_fill",               # つなぎ: 塗りの閉じ(幅 1 m 以下の隙間・角だけで触れる所)
    17: "implied_short_gap",      # つなぎ: 細い道の口の短い切れ目(W1 の住宅街の型の線の上・12 m 以下)
}


@dataclass(frozen=True)
class NavMesh:
    """段 1 のナビメッシュ(不変)。配列は numba にそのまま渡す。"""

    res: float
    floor_code: np.ndarray      # (F,) int8 階の番号(0=地上・負=地下・正=デッキ)
    floor_band: np.ndarray      # (F,) int8 セルの層(-1/0/1)
    floor_ox: np.ndarray        # (F,) float64
    floor_oy: np.ndarray        # (F,) float64
    floor_nx: np.ndarray        # (F,) int64
    floor_ny: np.ndarray        # (F,) int64
    row_base: np.ndarray        # (F,) int64(row_ptr の中の階の頭)
    row_ptr: np.ndarray         # (ΣNY+F,) int64
    run_x0: np.ndarray          # (R,) int32 列の始まり
    run_x1: np.ndarray          # (R,) int32 列の終わり(含まない)
    run_row: np.ndarray         # (R,) int32
    run_floor: np.ndarray       # (R,) int8 階の添字
    run_strip: np.ndarray       # (R,) int32
    strip_floor: np.ndarray     # (S,) int8 階の添字
    strip_run_ptr: np.ndarray   # (S+1,) int64
    strip_runs: np.ndarray      # (R,) int32(帯ごとに行の順)
    strip_z: np.ndarray         # (S,) float32 帯の高さ[m](標高・地上の帯は DEM の平均)
    strip_cx: np.ndarray        # (S,) float64
    strip_cy: np.ndarray        # (S,) float64
    strip_area_m2: np.ndarray   # (S,) float64
    strip_src: np.ndarray       # (S,) uint8(最も多い出どころ)
    adj_ptr: np.ndarray         # (S+1,) int64
    adj_to: np.ndarray          # (A,) int32
    adj_kind: np.ndarray        # (A,) int8 0=門 1=接続口
    adj_ref: np.ndarray         # (A,) int32 門の番号 / 接続口の番号
    adj_dir: np.ndarray         # (A,) int8 接続口の向き(0=a→b・1=b→a)
    portal_lo_run: np.ndarray   # (P,) int32 下の行のラン
    portal_hi_run: np.ndarray   # (P,) int32 上の行のラン
    portal_y: np.ndarray        # (P,) float64 境の y
    portal_x0: np.ndarray       # (P,) float64
    portal_x1: np.ndarray       # (P,) float64
    link_kind: np.ndarray       # (L,) int8(LINK_KINDS)
    link_ax: np.ndarray
    link_ay: np.ndarray
    link_afi: np.ndarray        # (L,) int8 階の添字
    link_astrip: np.ndarray     # (L,) int32
    link_bx: np.ndarray
    link_by: np.ndarray
    link_bfi: np.ndarray
    link_bstrip: np.ndarray
    link_rise_m: np.ndarray     # (L,) float32 b の高さ − a の高さ
    link_len_m: np.ndarray      # (L,) float32 水平の長さ
    link_width_m: np.ndarray    # (L,) float32 幅(階段の容量の素)
    link_cap_per_min: np.ndarray  # (L,) float32 1 分あたりの人数(SR11 (a))
    link_wait_s: np.ndarray     # (L,) float32 待ち(エレベーター=間隔の半分・SR11 (d))
    link_src: np.ndarray        # (L,) int8 出どころ(構築の記録)
    link_w1_edge: np.ndarray    # (L,) int32 対応する W1 の辺(無ければ -1)
    anchor_x: np.ndarray        # (N,) float64 W1 の節ごとの面の上の点
    anchor_y: np.ndarray
    anchor_fi: np.ndarray       # (N,) int8
    anchor_run: np.ndarray      # (N,) int32
    anchor_dist_m: np.ndarray   # (N,) float32 節から点までの距離
    corr_ptr: np.ndarray        # (E+1,) int64 W1 の辺 → 近くの帯
    corr_strips: np.ndarray     # (C,) int32
    dem_ox: float
    dem_oy: float
    dem_res: float
    dem_z: np.ndarray           # (ny, nx) float32 標高[m]
    meta: Mapping[str, Any] = field(default_factory=dict)
    sources: Mapping[str, str] = field(default_factory=dict)

    @property
    def n_floors(self) -> int:
        return int(self.floor_code.size)

    @property
    def run_count(self) -> int:
        return int(self.run_x0.size)

    @property
    def n_strips(self) -> int:
        return int(self.strip_floor.size)

    @property
    def n_links(self) -> int:
        return int(self.link_kind.size)

    def fi_of_code(self, code: int) -> int:
        """階の番号 → 添字(無ければ -1)。"""
        hit = np.flatnonzero(self.floor_code == int(code))
        return int(hit[0]) if hit.size else -1

    def locate(self, fi: int, x: float, y: float) -> int:
        return int(locate_run(self.row_base, self.row_ptr, self.run_x0, self.run_x1, self.floor_ox, self.floor_oy,
                              self.floor_nx, self.floor_ny, self.res, int(fi), float(x), float(y)))

    def nearest(self, fi: int, x: float, y: float, rmax: float) -> tuple[int, float, float, float]:
        r, px, py, d = nearest_point(self.row_base, self.row_ptr, self.run_x0, self.run_x1, self.run_row,
                                     self.floor_ox, self.floor_oy, self.floor_ny, self.res, int(fi), float(x),
                                     float(y), float(rmax))
        return int(r), float(px), float(py), float(d)

    def z_at(self, fi: int, x: float, y: float) -> float:
        """高さ[m]: 地上の階は DEM、ほかの階は帯の高さ。"""
        if int(self.floor_code[fi]) == 0:
            return float(dem_z(self.dem_z, self.dem_ox, self.dem_oy, self.dem_res, float(x), float(y)))
        r = self.locate(fi, x, y)
        if r < 0:
            return float("nan")
        return float(self.strip_z[self.run_strip[r]])

    def cell_area_m2(self, lut: np.ndarray, cx0: int, cy0: int, n_cells: int, cell_m: float = 100.0) -> np.ndarray:
        """セルごとの歩ける面積[m²](:func:`area_by_cell`)。"""
        return area_by_cell(lut, int(cx0), int(cy0), float(cell_m), self.run_floor, self.run_row, self.run_x0,
                            self.run_x1, self.floor_band, self.floor_ox, self.floor_oy, self.res, int(n_cells))


def navmesh_available(world_dir: str | Path | None) -> bool:
    """置き場にナビメッシュの資産が全部あるか。"""
    if world_dir is None:
        return False
    p = Path(world_dir)
    return p.is_dir() and (p / NAV1_META).exists() and all((p / f).exists() for f in NAV1_FILES)


def _sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_navmesh(world_dir: str | Path, *, verify: bool = True) -> NavMesh:
    """``nav1_*`` を読む。``verify`` なら ``nav1_meta.json`` の sha256 と照らす(違えば ``ValueError``)。"""
    import pyarrow.parquet as pq

    p = Path(world_dir)
    if not navmesh_available(p):
        missing = [f for f in (NAV1_META,) + NAV1_FILES if not (p / f).exists()]
        raise FileNotFoundError(f"ナビメッシュの資産が足りない: {p} に {missing}(build.space.navmesh1 で作る)")
    meta = json.loads((p / NAV1_META).read_text(encoding="utf-8"))
    sources: dict[str, str] = {}
    for f in NAV1_FILES:
        sha = _sha256(p / f)
        want = dict(meta.get("files", {})).get(f, {}).get("sha256")
        if verify and want is not None and want != sha:
            raise ValueError(f"{f} の sha256 が nav1_meta.json と違う(資産が壊れたか組み直しの途中)")
        sources[f] = sha
    sources[NAV1_META] = _sha256(p / NAV1_META)

    def col(t, name, dtype):
        return np.ascontiguousarray(np.asarray(t.column(name).to_numpy(zero_copy_only=False), dtype=dtype))

    runs = pq.read_table(p / "nav1_runs.parquet")
    strips = pq.read_table(p / "nav1_strips.parquet")
    portals = pq.read_table(p / "nav1_portals.parquet")
    links = pq.read_table(p / "nav1_links.parquet")
    anchors = pq.read_table(p / "nav1_anchors.parquet")
    corr = pq.read_table(p / "nav1_corridor.parquet")
    floors = meta["floors"]
    res = float(meta["res_m"])
    fcode = np.asarray([f["code"] for f in floors], dtype=np.int8)
    fband = np.asarray([f["band"] for f in floors], dtype=np.int8)
    fox = np.asarray([f["ox"] for f in floors], dtype=np.float64)
    foy = np.asarray([f["oy"] for f in floors], dtype=np.float64)
    fnx = np.asarray([f["nx"] for f in floors], dtype=np.int64)
    fny = np.asarray([f["ny"] for f in floors], dtype=np.int64)

    run_x0 = col(runs, "x0", np.int32)
    run_x1 = col(runs, "x1", np.int32)
    run_row = col(runs, "row", np.int32)
    run_floor = col(runs, "floor", np.int8)
    run_strip = col(runs, "strip", np.int32)
    # 行の CSR(階ごと・ランは (階, 行, 列) の順に並んでいる=構築の約束)
    row_base = np.zeros(fcode.size, dtype=np.int64)
    acc = 0
    for f in range(fcode.size):
        row_base[f] = acc
        acc += int(fny[f]) + 1
    # 行 j の範囲 = [row_ptr[b+j], row_ptr[b+j+1])(階ごとに末尾に空の番兵の行=次の階の頭と同じ値)
    flat = row_base[run_floor.astype(np.int64)] + run_row.astype(np.int64)
    if flat.size and np.any(np.diff(flat) < 0):
        raise ValueError("nav1_runs が (階, 行, 列) の順に並んでいない")
    counts = np.bincount(flat, minlength=acc)
    row_ptr = np.concatenate([[0], np.cumsum(counts)[:-1]]).astype(np.int64)
    s_order = np.lexsort((run_row, run_strip))
    strip_floor = col(strips, "floor", np.int8)
    n_s = strip_floor.size
    strip_counts = np.bincount(run_strip, minlength=n_s)
    strip_run_ptr = np.concatenate([[0], np.cumsum(strip_counts)]).astype(np.int64)

    a_from = col(strips, "strip", np.int64)
    if not np.array_equal(a_from, np.arange(n_s)):
        raise ValueError("nav1_strips.strip が 0..S-1 の連番でない")

    # 隣接の CSR(門=両向き・接続口=向きごとの行)
    p_lo = col(portals, "lo_run", np.int32)
    p_hi = col(portals, "hi_run", np.int32)
    sa = run_strip[p_lo].astype(np.int64)
    sb = run_strip[p_hi].astype(np.int64)
    pid = np.arange(p_lo.size, dtype=np.int64)
    l_as = col(links, "a_strip", np.int64)
    l_bs = col(links, "b_strip", np.int64)
    lid = np.arange(l_as.size, dtype=np.int64)
    src = np.concatenate([sa, sb, l_as, l_bs])
    dst = np.concatenate([sb, sa, l_bs, l_as])
    kind = np.concatenate([np.zeros(2 * pid.size, np.int8), np.ones(2 * lid.size, np.int8)])
    ref = np.concatenate([pid, pid, lid, lid])
    ldir = np.concatenate([np.zeros(2 * pid.size, np.int8), np.zeros(lid.size, np.int8), np.ones(lid.size, np.int8)])
    o = np.lexsort((ref, kind, dst, src))
    src, dst, kind, ref, ldir = src[o], dst[o], kind[o], ref[o], ldir[o]
    adj_ptr = np.concatenate([[0], np.cumsum(np.bincount(src, minlength=n_s))]).astype(np.int64)

    dem = np.load(p / "nav1_dem.npy")
    dmeta = meta["dem"]
    c_edge = col(corr, "edge", np.int64)
    c_strip = col(corr, "strip", np.int32)
    n_e = int(meta["n_w1_edges"])
    corr_ptr = np.concatenate([[0], np.cumsum(np.bincount(c_edge, minlength=n_e))]).astype(np.int64)

    return NavMesh(
        res=res, floor_code=fcode, floor_band=fband, floor_ox=fox, floor_oy=foy, floor_nx=fnx, floor_ny=fny,
        row_base=row_base, row_ptr=row_ptr, run_x0=run_x0, run_x1=run_x1, run_row=run_row, run_floor=run_floor,
        run_strip=run_strip, strip_floor=strip_floor, strip_run_ptr=strip_run_ptr,
        strip_runs=np.ascontiguousarray(s_order.astype(np.int32)),
        strip_z=col(strips, "z", np.float32), strip_cx=col(strips, "cx", np.float64),
        strip_cy=col(strips, "cy", np.float64), strip_area_m2=col(strips, "area_m2", np.float64),
        strip_src=col(strips, "src", np.uint8), adj_ptr=adj_ptr, adj_to=dst.astype(np.int32),
        adj_kind=kind.astype(np.int8), adj_ref=ref.astype(np.int32), adj_dir=ldir.astype(np.int8),
        portal_lo_run=p_lo, portal_hi_run=p_hi, portal_y=col(portals, "y", np.float64),
        portal_x0=col(portals, "x0", np.float64), portal_x1=col(portals, "x1", np.float64),
        link_kind=col(links, "kind", np.int8), link_ax=col(links, "a_x", np.float64),
        link_ay=col(links, "a_y", np.float64), link_afi=col(links, "a_floor", np.int8),
        link_astrip=col(links, "a_strip", np.int32), link_bx=col(links, "b_x", np.float64),
        link_by=col(links, "b_y", np.float64), link_bfi=col(links, "b_floor", np.int8),
        link_bstrip=col(links, "b_strip", np.int32), link_rise_m=col(links, "rise_m", np.float32),
        link_len_m=col(links, "len_m", np.float32), link_width_m=col(links, "width_m", np.float32),
        link_cap_per_min=col(links, "cap_per_min", np.float32), link_wait_s=col(links, "wait_s", np.float32),
        link_src=col(links, "src", np.int8), link_w1_edge=col(links, "w1_edge", np.int32),
        anchor_x=col(anchors, "x", np.float64), anchor_y=col(anchors, "y", np.float64),
        anchor_fi=col(anchors, "floor", np.int8), anchor_run=col(anchors, "run", np.int32),
        anchor_dist_m=col(anchors, "dist_m", np.float32), corr_ptr=corr_ptr, corr_strips=c_strip,
        dem_ox=float(dmeta["ox"]), dem_oy=float(dmeta["oy"]), dem_res=float(dmeta["res"]),
        dem_z=np.ascontiguousarray(dem.astype(np.float32)), meta=meta, sources=sources,
    )


# ====================================================================== numba の問い合わせ
@nb.njit(cache=True)
def locate_run(row_base, row_ptr, run_x0, run_x1, floor_ox, floor_oy, floor_nx, floor_ny, res, fi, x, y):
    """(階の添字, x, y) → ラン(無ければ -1)。行の中は二分探索。"""
    if fi < 0 or fi >= floor_ox.shape[0]:
        return -1
    j = int(math.floor((y - floor_oy[fi]) / res))
    i = int(math.floor((x - floor_ox[fi]) / res))
    if j < 0 or j >= floor_ny[fi] or i < 0 or i >= floor_nx[fi]:
        return -1
    b = row_base[fi] + j
    lo = row_ptr[b]
    hi = row_ptr[b + 1]
    # x0 <= i の最後のラン
    a = lo
    c = hi
    while a < c:
        m = (a + c) // 2
        if run_x0[m] <= i:
            a = m + 1
        else:
            c = m
    r = a - 1
    if r >= lo and run_x0[r] <= i < run_x1[r]:
        return r
    return -1


@nb.njit(cache=True)
def nearest_point(row_base, row_ptr, run_x0, run_x1, run_row, floor_ox, floor_oy, floor_ny, res, fi, x, y, rmax):
    """階の中で (x, y) に最も近い歩ける点(ランの長方形を目の幅の 1/1000 だけ内へ寄せた中)。

    返り値 ``(ラン, px, py, 距離)``。半径 ``rmax`` の中に無ければ ``(-1, x, y, inf)``。同点はランの番号の小さい方。
    """
    if fi < 0 or fi >= floor_ox.shape[0]:
        return -1, x, y, np.inf
    ox = floor_ox[fi]
    oy = floor_oy[fi]
    eps = res * 1e-3
    j0 = max(0, int(math.floor((y - rmax - oy) / res)))
    j1 = min(floor_ny[fi] - 1, int(math.floor((y + rmax - oy) / res)))
    best = -1
    bd = np.inf
    bx = x
    by = y
    for j in range(j0, j1 + 1):
        b = row_base[fi] + j
        ylo = oy + j * res + eps
        yhi = oy + (j + 1) * res - eps
        py = min(max(y, ylo), yhi)
        dy = py - y
        if dy * dy > bd * bd:
            continue
        for r in range(row_ptr[b], row_ptr[b + 1]):
            xlo = ox + run_x0[r] * res + eps
            xhi = ox + run_x1[r] * res - eps
            px = min(max(x, xlo), xhi)
            dx = px - x
            d = math.sqrt(dx * dx + dy * dy)
            if d < bd:
                bd = d
                best = r
                bx = px
                by = py
    if best < 0 or bd > rmax:
        return -1, x, y, np.inf
    return best, bx, by, bd


@nb.njit(cache=True)
def dem_z(z, ox, oy, res, x, y):
    """DEM の格子から双線形で標高[m](格子の外は端の値)。"""
    ny, nx = z.shape
    fx = (x - ox) / res - 0.5
    fy = (y - oy) / res - 0.5
    i = int(math.floor(fx))
    j = int(math.floor(fy))
    tx = fx - i
    ty = fy - j
    i0 = min(max(i, 0), nx - 1)
    i1 = min(max(i + 1, 0), nx - 1)
    j0 = min(max(j, 0), ny - 1)
    j1 = min(max(j + 1, 0), ny - 1)
    return ((1 - tx) * (1 - ty) * z[j0, i0] + tx * (1 - ty) * z[j0, i1]
            + (1 - tx) * ty * z[j1, i0] + tx * ty * z[j1, i1])


@nb.njit(cache=True)
def _less(fa, ia, fb, ib):
    return fa < fb or (fa == fb and ia < ib)


@nb.njit(cache=True)
def _push(hf, hi, size, f, i):
    k = size
    hf[k] = f
    hi[k] = i
    while k > 0:
        p = (k - 1) // 2
        if _less(hf[k], hi[k], hf[p], hi[p]):
            tf = hf[k]; hf[k] = hf[p]; hf[p] = tf
            ti = hi[k]; hi[k] = hi[p]; hi[p] = ti
            k = p
        else:
            break
    return size + 1


@nb.njit(cache=True)
def _pop(hf, hi, size):
    f = hf[0]
    i = hi[0]
    size -= 1
    hf[0] = hf[size]
    hi[0] = hi[size]
    k = 0
    while True:
        l = 2 * k + 1
        r = l + 1
        m = k
        if l < size and _less(hf[l], hi[l], hf[m], hi[m]):
            m = l
        if r < size and _less(hf[r], hi[r], hf[m], hi[m]):
            m = r
        if m == k:
            break
        tf = hf[k]; hf[k] = hf[m]; hf[m] = tf
        ti = hi[k]; hi[k] = hi[m]; hi[m] = ti
        k = m
    return f, i, size


@nb.njit(cache=True)
def _point_z(fi_code, sz, dem, dox, doy, dres, x, y):
    if fi_code == 0:
        return dem_z(dem, dox, doy, dres, x, y)
    return sz


@nb.njit(cache=True)
def astar_strips(adj_ptr, adj_to, adj_kind, adj_ref, adj_dir, portal_y, portal_x0, portal_x1,
                 link_ax, link_ay, link_bx, link_by, link_cost_ab, link_cost_ba,
                 strip_floor, floor_code, strip_z, dem, dox, doy, dres,
                 s_start, sx, sy, s_goal, gx, gy, climb_w, allow, stamp, use_allow,
                 g, parent, via_kind, via_ref, via_dir, ex, ey, closed, cstamp, hf, hi):
    """帯の A*(入った点から次の門の中点までの距離+``climb_w``×上り)。

    ``allow[s] == stamp``(``use_allow`` のとき)の帯だけを展開する(通り道の印)。返り値=(見つかったか, 展開数)。
    経路は ``parent``・``via_*`` を ``s_goal`` から辿る。``ex, ey`` は帯に入った点。
    """
    size = 0
    g[s_start] = 0.0
    parent[s_start] = -1
    via_kind[s_start] = -1
    ex[s_start] = sx
    ey[s_start] = sy
    closed[s_start] = -cstamp
    h = math.sqrt((sx - gx) ** 2 + (sy - gy) ** 2)
    size = _push(hf, hi, size, h, s_start)
    expanded = 0
    while size > 0:
        f, u, size = _pop(hf, hi, size)
        if closed[u] == cstamp:
            continue
        closed[u] = cstamp
        expanded += 1
        if u == s_goal:
            return True, expanded
        px = ex[u]
        py = ey[u]
        fu = floor_code[strip_floor[u]]
        pz = _point_z(fu, strip_z[u], dem, dox, doy, dres, px, py)
        for k in range(adj_ptr[u], adj_ptr[u + 1]):
            v = adj_to[k]
            if closed[v] == cstamp:
                continue
            if use_allow and allow[v] != stamp:
                continue
            if adj_kind[k] == 0:
                q = adj_ref[k]
                ny_ = portal_y[q]
                nx_ = 0.5 * (portal_x0[q] + portal_x1[q])
                d = math.sqrt((nx_ - px) ** 2 + (ny_ - py) ** 2)
                nz = _point_z(fu, strip_z[v], dem, dox, doy, dres, nx_, ny_)
                rise = nz - pz
                w = d + (climb_w * rise if rise > 0.0 else 0.0)
            else:
                q = adj_ref[k]
                if adj_dir[k] == 0:
                    ax = link_ax[q]; ay = link_ay[q]; nx_ = link_bx[q]; ny_ = link_by[q]; lc = link_cost_ab[q]
                else:
                    ax = link_bx[q]; ay = link_by[q]; nx_ = link_ax[q]; ny_ = link_ay[q]; lc = link_cost_ba[q]
                d = math.sqrt((ax - px) ** 2 + (ay - py) ** 2)
                az = _point_z(fu, strip_z[u], dem, dox, doy, dres, ax, ay)
                rise = az - pz
                w = d + (climb_w * rise if rise > 0.0 else 0.0) + lc
            ng = g[u] + w
            if closed[v] != -cstamp or ng < g[v]:
                g[v] = ng
                parent[v] = u
                via_kind[v] = adj_kind[k]
                via_ref[v] = adj_ref[k]
                via_dir[v] = adj_dir[k]
                ex[v] = nx_
                ey[v] = ny_
                closed[v] = -cstamp
                hv = math.sqrt((nx_ - gx) ** 2 + (ny_ - gy) ** 2)
                size = _push(hf, hi, size, ng + hv, v)
    return False, expanded


@nb.njit(cache=True)
def _cross(ox, oy, ax, ay, bx, by):
    return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)


@nb.njit(cache=True)
def funnel_points(lx, ly, rx, ry, m, sx, sy, tx, ty, out):
    """simple stupid funnel(R-59 ``measure_navmesh.funnel`` の核を門の配列で受ける形に移した)。

    門 1..m の左右の点(歩く向きから見た左=``l``・右=``r``)と出発・目的の点 → 折れ線 ``out``(点数を返す)。
    ``_cross(o,a,b) > 0`` は「b が a より左」。
    """
    n_p = m + 2
    PLx = np.empty(n_p); PLy = np.empty(n_p); PRx = np.empty(n_p); PRy = np.empty(n_p)
    PLx[0] = sx; PLy[0] = sy; PRx[0] = sx; PRy[0] = sy
    for i in range(m):
        PLx[i + 1] = lx[i]; PLy[i + 1] = ly[i]; PRx[i + 1] = rx[i]; PRy[i + 1] = ry[i]
    PLx[m + 1] = tx; PLy[m + 1] = ty; PRx[m + 1] = tx; PRy[m + 1] = ty
    out[0, 0] = sx
    out[0, 1] = sy
    n_out = 1
    apx = sx; apy = sy; llx = sx; lly = sy; rrx = sx; rry = sy
    api = 0; li = 0; ri = 0
    i = 1
    while i < n_p:
        nlx = PLx[i]; nly = PLy[i]; nrx = PRx[i]; nry = PRy[i]
        if _cross(apx, apy, rrx, rry, nrx, nry) >= 0.0:
            if (apx == rrx and apy == rry) or _cross(apx, apy, llx, lly, nrx, nry) < 0.0:
                rrx = nrx; rry = nry; ri = i
            else:
                apx = llx; apy = lly; api = li
                if not (out[n_out - 1, 0] == apx and out[n_out - 1, 1] == apy):
                    out[n_out, 0] = apx; out[n_out, 1] = apy; n_out += 1
                llx = apx; lly = apy; rrx = apx; rry = apy; li = api; ri = api
                i = api + 1
                continue
        if _cross(apx, apy, llx, lly, nlx, nly) <= 0.0:
            if (apx == llx and apy == lly) or _cross(apx, apy, rrx, rry, nlx, nly) > 0.0:
                llx = nlx; lly = nly; li = i
            else:
                apx = rrx; apy = rry; api = ri
                if not (out[n_out - 1, 0] == apx and out[n_out - 1, 1] == apy):
                    out[n_out, 0] = apx; out[n_out, 1] = apy; n_out += 1
                llx = apx; lly = apy; rrx = apx; rry = apy; li = api; ri = api
                i = api + 1
                continue
        i += 1
    if not (out[n_out - 1, 0] == tx and out[n_out - 1, 1] == ty):
        out[n_out, 0] = tx
        out[n_out, 1] = ty
        n_out += 1
    return n_out


@nb.njit(cache=True)
def _add_portal(lx, ly, rx, ry, m, y, xa, xb, going_up):
    """水平の門(y・区間 [xa, xb])を歩く向きに合わせて左右の点にして足す(上へ=左が x の小さい方)。"""
    if going_up:
        lx[m] = xa; ly[m] = y; rx[m] = xb; ry[m] = y
    else:
        lx[m] = xb; ly[m] = y; rx[m] = xa; ry[m] = y
    return m + 1


@nb.njit(cache=True)
def corridor_portals(strip_seq, entry_run, exit_run, n_seq, strip_run_ptr, strip_runs, run_row, run_x0, run_x1,
                     run_floor, floor_ox, floor_oy, res, inter_y, inter_x0, inter_x1, lx, ly, rx, ry):
    """同じ階の帯の列(``strip_seq[0..n_seq)``)→ 門の左右の点の列(帯の中の行ごとの門+帯と帯の間の門)。

    ``entry_run[k]``・``exit_run[k]``=帯 k に入るラン・出るラン(最初は出発のラン・最後は目的のラン)。帯と帯の間の門は
    ``inter_*[k]``(帯 k と k+1 の間)。返り値=門の数。
    """
    m = 0
    for k in range(n_seq):
        s = strip_seq[k]
        a = entry_run[k]
        b = exit_run[k]
        ra = run_row[a]
        rb = run_row[b]
        fi = run_floor[a]
        ox = floor_ox[fi]
        oy = floor_oy[fi]
        lo = strip_run_ptr[s]
        # 帯の中のランは行の順(ra の位置を探す)
        ia = lo
        while strip_runs[ia] != a:
            ia += 1
        ib = lo
        while strip_runs[ib] != b:
            ib += 1
        if ib > ia:
            for t in range(ia, ib):
                p = strip_runs[t]
                q = strip_runs[t + 1]
                xa = ox + max(run_x0[p], run_x0[q]) * res
                xb = ox + min(run_x1[p], run_x1[q]) * res
                y = oy + (run_row[p] + 1) * res
                m = _add_portal(lx, ly, rx, ry, m, y, xa, xb, True)
        elif ib < ia:
            for t in range(ia, ib, -1):
                p = strip_runs[t]
                q = strip_runs[t - 1]
                xa = ox + max(run_x0[p], run_x0[q]) * res
                xb = ox + min(run_x1[p], run_x1[q]) * res
                y = oy + run_row[p] * res
                m = _add_portal(lx, ly, rx, ry, m, y, xa, xb, False)
        if k < n_seq - 1:
            nb_ = entry_run[k + 1]
            up = run_row[nb_] > rb
            m = _add_portal(lx, ly, rx, ry, m, inter_y[k], inter_x0[k], inter_x1[k], up)
        _ = ra
    return m


@nb.njit(cache=True)
def w1_turn_dijkstra(n_dir, out_ptr, out_to, dir_len, dir_rise, dir_head_out, dir_head_in, dir_end,
                     start_ptr_lo, start_ptr_hi, start_dirs, target_node, turn_w, climb_w, cos_turn,
                     dist, parent, done, stamp, hf, hi):
    """W1 の向きつきの辺(状態)の Dijkstra(重み=長さ+``climb_w``×上り+曲がる 1 回 ``turn_w``)。

    「曲がる」=前の辺の入りの向きと次の辺の出の向きの間の角が ``acos(cos_turn)`` 以上(R-61 SF の定義=45°)。
    出発の節の出る辺 ``start_dirs[start_ptr_lo:start_ptr_hi]`` から。返り値=目的の節に着いた最初の向きつきの辺(無ければ -1)。
    """
    size = 0
    for k in range(start_ptr_lo, start_ptr_hi):
        d = start_dirs[k]
        w = dir_len[d] + (climb_w * dir_rise[d] if dir_rise[d] > 0.0 else 0.0)
        if done[d] != -stamp or w < dist[d]:
            dist[d] = w
            parent[d] = -1
            done[d] = -stamp
            size = _push(hf, hi, size, w, d)
    while size > 0:
        f, u, size = _pop(hf, hi, size)
        if done[u] == stamp:
            continue
        done[u] = stamp
        v = dir_end[u]
        if v == target_node:
            return u
        hx = dir_head_in[u, 0]
        hy = dir_head_in[u, 1]
        for k in range(out_ptr[v], out_ptr[v + 1]):
            e = out_to[k]
            if done[e] == stamp:
                continue
            c = hx * dir_head_out[e, 0] + hy * dir_head_out[e, 1]
            w = dir_len[e] + (climb_w * dir_rise[e] if dir_rise[e] > 0.0 else 0.0)
            if c < cos_turn:
                w += turn_w
            ng = dist[u] + w
            if done[e] != -stamp or ng < dist[e]:
                dist[e] = ng
                parent[e] = u
                done[e] = -stamp
                size = _push(hf, hi, size, ng, e)
    return -1


# ====================================================================== セルの対応(不変の写し)
def cell_lookup_table(cell_ix, cell_iy, cell_band, *, fill_nearest: bool = False) -> tuple[np.ndarray, int, int]:
    """W2 のセル → 引き表 ``lut[iy-cy0, ix-cx0, band+1]``(セルの番号・無ければ -1)と原点 ``(cx0, cy0)``。

    ``fill_nearest``=〔段 1 の検収 M3〕W2 のセルの無い 100 m の升の地上の欄を、最も近い(升の中心の距離・同じなら番号の
    小さい)地上のセルで埋める(つなぎの帯=範囲の外をつなぐ帯の上の体のセルを -1 にしない・帯でない面は構築で切る)。
    """
    ix = np.asarray(cell_ix, dtype=np.int64)
    iy = np.asarray(cell_iy, dtype=np.int64)
    b = np.asarray(cell_band, dtype=np.int64)
    cx0, cy0 = int(ix.min()), int(iy.min())
    lut = np.full((int(iy.max()) - cy0 + 1, int(ix.max()) - cx0 + 1, 3), -1, dtype=np.int32)
    lut[iy - cy0, ix - cx0, b + 1] = np.arange(ix.size, dtype=np.int32)
    if fill_nearest:
        gl = np.argwhere(lut[:, :, 1] >= 0)
        if gl.size:
            ids = lut[gl[:, 0], gl[:, 1], 1]
            for j, i in np.argwhere(lut[:, :, 1] < 0).tolist():  # 逐次ループ宣言: セルの無い升の数ぶん(読み込みの 1 回)
                d2 = (gl[:, 0] - j) ** 2 + (gl[:, 1] - i) ** 2
                best = np.flatnonzero(d2 == d2.min())
                lut[j, i, 1] = int(ids[best].min())
    return lut, cx0, cy0


@nb.njit(cache=True)
def cell_of(lut, cx0, cy0, cell_m, x, y, band):
    """(x, y, 層) → セルの番号。その層のセルが無ければ地上のセル・それも無ければ -1(11c の ``cell_band`` の向きの逆)。"""
    ix = int(math.floor(x / cell_m)) - cx0
    iy = int(math.floor(y / cell_m)) - cy0
    if iy < 0 or iy >= lut.shape[0] or ix < 0 or ix >= lut.shape[1]:
        return -1
    c = lut[iy, ix, band + 1]
    if c < 0:
        c = lut[iy, ix, 1]
    return c


@nb.njit(cache=True)
def area_by_cell(lut, cx0, cy0, cell_m, run_floor, run_row, run_x0, run_x1, floor_band, floor_ox, floor_oy, res,
                 n_cells):
    """セルごとの歩ける面積[m²](ランを 100 m の列の境で切って足す=重ならない)。"""
    out = np.zeros(n_cells, dtype=np.float64)
    for r in range(run_x0.shape[0]):
        f = run_floor[r]
        ox = floor_ox[f]
        y = floor_oy[f] + (run_row[r] + 0.5) * res
        xa = ox + run_x0[r] * res
        xb = ox + run_x1[r] * res
        x = xa
        while x < xb:
            nxt = (math.floor(x / cell_m) + 1.0) * cell_m
            hi = min(nxt, xb)
            c = cell_of(lut, cx0, cy0, cell_m, 0.5 * (x + hi), y, floor_band[f])
            if c >= 0:
                out[c] += (hi - x) * res
            x = hi
    return out
