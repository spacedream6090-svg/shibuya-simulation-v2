"""world.assets — 世界データ資産(W1/W2/W3/W6)の読み込みと、CI 用の合成小世界。

正典
- 実装計画書 §5: 「世界データ台帳=Parquet(不変・ハッシュ)→実行時 NumPy。
  可視性=生バイナリ+``numpy.memmap``(ラン間共有)」。
- 世界データ構築仕様書 W2 実測ヘッダ: ``place_id`` = **520**(GL 453 + DECK 39 + UG 28)、
  格子原点 (0,0)・セル 100 m・層 3 値 ``UG/GL/DECK``。
- W3: ``w3_next_hop.npy``(node×node の next-hop 表)・``w3_cell_dist.npy``(cell×cell 距離)。

**設計書との食い違い(親へ報告・解決しない)**
    セル数が 3 つの値で書かれている: 予算行 P6「≤2 ms/tick@40万体・**139セル**」/
    実装計画書 §3「セル(100m・**453**)を第一のチャンク」「xxhash で **453 回**」/
    W2 実測ヘッダ「``n_place_ids`` = **520**」(GL だけなら 453)。
    139 は世界データ構築仕様書 §D-W1 の「核±600m=143セル(設計書『約139』の出所)」で、
    **広域 453 が採用された後も P6 の行に残っている**。本モジュールは値を決め打ちせず
    ``n_cells`` を引数にし、ベンチは 453(実装計画書の値)で回して数値を報告する。

逐次ループ宣言(P4)
1. ``load_assets``: POI 数(2,337)ぶんの ``place_id`` 文字列→セル索引の辞書引き。
2. ``synthetic_assets``: セル数ぶんの BFS(next-hop 表の構築・139/453 規模)。
3. ``_noise_stage_per_cell``: **昼/夜の 2 回**(W10 街路点 356,732 点の集約は ``bincount`` 1 本)。
いずれも個体数・tick 数には比例しない。

expedient(本モジュール分)
- 合成世界は **1 セル=1 ノードの 4 近傍格子**。1 tick=1 ノード前進が 100 m/分=6 km/h と
  歩行速度に一致するのが唯一の根拠(実世界資産では W1 のノード間隔が 100 m より密なので
  1 tick=1 ノードは歩行より遅い=U15 群衆物理で置き換わるまでの暫定)。
- 合成 POI: 1 セルあたり 2 件・カテゴリ 3 種・価格 300/800/1,500 円・在庫 32-96・
  同時受け入れ 4 件/tick。すべて自前(実データの店舗密度・客単価に寄せていない)。
- ノード→セルは格子式 ``floor(x/100)``(W2 の格子原点・セル辺と同じ規約)で写す。
  W1 は ``place_id`` 欄を持たないため(W2 側にしかない)。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np

from shibuya.core.rng import stream

__all__ = [
    "BAND_CODES",
    "CELL_SIZE_M",
    "GRID_ORIGIN_XY",
    "NOISE_DAY_HOURS",
    "N_NOISE_STAGES",
    "WorldAssets",
    "assets_available",
    "load_assets",
    "synthetic_assets",
]

#: 層名 → コード(UG=-1 / GL=0 / DECK=1。W2 の 3 値)。
BAND_CODES: Final[dict[str, int]] = {"UG": -1, "GL": 0, "DECK": 1}
#: セルの一辺[m](W2 params ``cell_m``)。
CELL_SIZE_M: Final[float] = 100.0
#: 格子原点(W2 params ``grid_origin_xy``)。
GRID_ORIGIN_XY: Final[tuple[float, float] ] = (0.0, 0.0)

_REQUIRED_FILES: Final[tuple[str, ...]] = (
    "w1_nodes.parquet",
    "w1_edges.parquet",
    "w2_cells.parquet",
    "w3_next_hop.npy",
    "w3_cell_dist.npy",
    "w6_poi.parquet",
)

#: 合成 POI のカテゴリと価格[円](expedient)。
SYNTHETIC_POI_CATS: Final[tuple[str, ...]] = ("コンビニ", "飲食", "物販")
SYNTHETIC_POI_PRICES: Final[tuple[int, ...]] = (300, 800, 1_500)
#: 合成 POI の 1 tick あたり受け入れ数(資源の容量・expedient)。
SYNTHETIC_POI_CAPACITY: Final[int] = 4
#: 合成 POI の営業時間(W7 PlanSpec が無いときの既定・10:00-22:00)。
DEFAULT_OPEN_FROM_TICK: Final[int] = 600
DEFAULT_OPEN_TO_TICK: Final[int] = 1_320

#: 騒音の「昼」時間帯(環境基準の昼 6:00-22:00 / 夜 22:00-6:00)。**mechanism**(法定)。
NOISE_DAY_HOURS: Final[tuple[int, int]] = (6, 22)
#: 騒音段階の段数(``perception.templates.NOISE_STAGE_VOCAB`` と同じ 4 段)。
N_NOISE_STAGES: Final[int] = 4


@dataclass(frozen=True)
class WorldAssets:
    """実行時 NumPy に落とした世界資産(不変)。

    Attributes:
        source: 由来(資産ディレクトリのパス、または ``"synthetic"``)。
        node_xy: ``(n_nodes, 2)`` float32 の平面座標[m]。
        node_band: ``(n_nodes,)`` int8(UG=-1/GL=0/DECK=1)。
        node_cell: ``(n_nodes,)`` int32(所属セル索引。-1=該当セルなし)。
        edge_u / edge_v / edge_len_m: 歩行グラフの辺。
        next_hop: ``(n_nodes, n_nodes)`` int32。``next_hop[u, v]`` = u から v へ向かう次ノード。
            資産版は ``mmap_mode="r"``(ラン間共有・M8 非算入)。
        cell_dist: ``(n_cells, n_cells)`` uint16 のセル間距離[m]。
        cell_ix / cell_iy / cell_band: セルの格子座標と層。
        cell_centroid: ``(n_cells, 2)`` float32。
        cell_rep_node: ``(n_cells,)`` int32(セル代表ノード)。
        poi_cell / poi_node: POI の所属セル・最寄ノード。
        poi_price / poi_stock0 / poi_capacity: 価格[円]・初期在庫・1 tick 受け入れ数。
        poi_open_from / poi_open_to: 営業 tick 帯(W7 が無いので既定値)。
        poi_cat: カテゴリ名(POI ごと)。
    """

    source: str
    node_xy: np.ndarray
    node_band: np.ndarray
    node_cell: np.ndarray
    edge_u: np.ndarray
    edge_v: np.ndarray
    edge_len_m: np.ndarray
    next_hop: np.ndarray
    cell_dist: np.ndarray
    cell_ix: np.ndarray
    cell_iy: np.ndarray
    cell_band: np.ndarray
    cell_centroid: np.ndarray
    cell_rep_node: np.ndarray
    poi_cell: np.ndarray
    poi_node: np.ndarray
    poi_price: np.ndarray
    poi_stock0: np.ndarray
    poi_capacity: np.ndarray
    poi_open_from: np.ndarray
    poi_open_to: np.ndarray
    poi_cat: tuple[str, ...]
    #: セル別の静的騒音段階(W10 街路点の**最頻値**・昼 6-22 時)。資産に無ければ ``None``。
    noise_stage_day: np.ndarray | None = None
    #: 同 夜(22-6 時)。
    noise_stage_night: np.ndarray | None = None

    @property
    def has_noise_field(self) -> bool:
        """W10 の静的騒音場(セル別・昼夜)を持っているか。"""
        return (
            self.noise_stage_day is not None
            and self.noise_stage_night is not None
            and int(self.noise_stage_day.size) == self.n_cells
        )

    def noise_stage_for_hour(self, hour: int) -> np.ndarray:
        """世界内の**時**(0-23)→ セル別騒音段階(環境基準の昼 6-22 時 / 夜 22-6 時)。

        資産に W10 が無ければ全セル 0(=「静か」)。
        """
        if not self.has_noise_field:
            return np.zeros(self.n_cells, dtype=np.uint8)
        lo, hi = NOISE_DAY_HOURS
        day = lo <= int(hour) < hi
        return self.noise_stage_day if day else self.noise_stage_night  # type: ignore[return-value]

    @property
    def n_nodes(self) -> int:
        return int(self.node_xy.shape[0])

    @property
    def n_cells(self) -> int:
        return int(self.cell_ix.shape[0])

    @property
    def n_poi(self) -> int:
        return int(self.poi_cell.shape[0])

    def summary(self) -> str:
        return (
            f"[world:{self.source}] nodes={self.n_nodes} cells={self.n_cells} "
            f"poi={self.n_poi} edges={self.edge_u.size}"
        )


def assets_available(path: str | Path | None) -> bool:
    """資産ディレクトリに必要な 6 ファイルが揃っているか。"""
    if path is None:
        return False
    p = Path(path)
    return p.is_dir() and all((p / f).exists() for f in _REQUIRED_FILES)


def _cell_key(ix: np.ndarray, iy: np.ndarray, band: np.ndarray) -> np.ndarray:
    """(ix, iy, band) → 一意な int64 鍵(``searchsorted`` 用)。"""
    return (
        (ix.astype(np.int64) + 1_000_000) * 8_000_000
        + (iy.astype(np.int64) + 1_000_000) * 4
        + (band.astype(np.int64) + 1)
    )


def load_assets(path: str | Path) -> WorldAssets:
    """``data/world/v2`` の資産を読む(W1/W2/W3/W6)。

    Raises:
        FileNotFoundError: 必要ファイルが欠けている。
    """
    import pyarrow.parquet as pq  # 資産がある時だけ要る(合成世界は pyarrow 不要)

    p = Path(path)
    if not assets_available(p):
        missing = [f for f in _REQUIRED_FILES if not (p / f).exists()]
        raise FileNotFoundError(f"世界資産が足りない: {p} に {missing}")

    nodes = pq.read_table(p / "w1_nodes.parquet", columns=["node_idx", "x", "y", "band"]).to_pydict()
    node_idx = np.asarray(nodes["node_idx"], dtype=np.int64)
    if not np.array_equal(node_idx, np.arange(node_idx.size)):
        raise ValueError("w1_nodes.node_idx が 0..n-1 の連番でない(索引としてそのまま使えない)")
    node_xy = np.stack(
        [np.asarray(nodes["x"], dtype=np.float32), np.asarray(nodes["y"], dtype=np.float32)], axis=1
    )
    node_band = np.array([BAND_CODES[b] for b in nodes["band"]], dtype=np.int8)

    edges = pq.read_table(
        p / "w1_edges.parquet", columns=["u_idx", "v_idx", "length_m"]
    ).to_pydict()
    edge_u = np.asarray(edges["u_idx"], dtype=np.int32)
    edge_v = np.asarray(edges["v_idx"], dtype=np.int32)
    edge_len = np.asarray(edges["length_m"], dtype=np.float32)

    cells = pq.read_table(
        p / "w2_cells.parquet",
        columns=["place_id", "ix", "iy", "band", "centroid_x", "centroid_y", "rep_node_idx"],
    ).to_pydict()
    cell_ix = np.asarray(cells["ix"], dtype=np.int32)
    cell_iy = np.asarray(cells["iy"], dtype=np.int32)
    cell_band = np.array([BAND_CODES[b] for b in cells["band"]], dtype=np.int8)
    cell_centroid = np.stack(
        [
            np.asarray(cells["centroid_x"], dtype=np.float32),
            np.asarray(cells["centroid_y"], dtype=np.float32),
        ],
        axis=1,
    )
    cell_rep_node = np.asarray(cells["rep_node_idx"], dtype=np.int32)
    place_to_cell = {pid: i for i, pid in enumerate(cells["place_id"])}

    # ノード → セル(格子式・W2 と同じ原点/辺長)
    keys = _cell_key(cell_ix, cell_iy, cell_band)
    order = np.argsort(keys, kind="stable")
    skeys = keys[order]
    nix = np.floor((node_xy[:, 0] - GRID_ORIGIN_XY[0]) / CELL_SIZE_M).astype(np.int32)
    niy = np.floor((node_xy[:, 1] - GRID_ORIGIN_XY[1]) / CELL_SIZE_M).astype(np.int32)
    nkeys = _cell_key(nix, niy, node_band)
    pos = np.searchsorted(skeys, nkeys)
    pos_clipped = np.clip(pos, 0, skeys.size - 1)
    hit = skeys[pos_clipped] == nkeys
    node_cell = np.where(hit, order[pos_clipped], -1).astype(np.int32)

    next_hop = np.load(p / "w3_next_hop.npy", mmap_mode="r")
    cell_dist = np.load(p / "w3_cell_dist.npy", mmap_mode="r")

    poi = pq.read_table(
        p / "w6_poi.parquet", columns=["poi_id", "cat", "place_id", "node_id", "x", "y"]
    ).to_pydict()
    # 逐次ループ宣言1: POI 数(2,337)ぶんの辞書引き
    poi_cell = np.array([place_to_cell.get(pid, -1) for pid in poi["place_id"]], dtype=np.int32)
    poi_xy = np.stack(
        [np.asarray(poi["x"], dtype=np.float32), np.asarray(poi["y"], dtype=np.float32)], axis=1
    )
    poi_node = _nearest_node_in_cell(poi_cell, poi_xy, node_cell, node_xy, cell_rep_node)
    cats = tuple(str(c) for c in poi["cat"])
    n_poi = poi_cell.size
    cat_code = np.array(
        [hash_free_cat_code(c) for c in cats], dtype=np.int64
    )  # 決定論(文字列 → 0..2)
    poi_price = np.array([SYNTHETIC_POI_PRICES[c] for c in cat_code], dtype=np.int32)
    poi_stock0 = np.full(n_poi, 64, dtype=np.int32)
    poi_capacity = np.full(n_poi, SYNTHETIC_POI_CAPACITY, dtype=np.int32)
    poi_open_from = np.full(n_poi, DEFAULT_OPEN_FROM_TICK, dtype=np.int16)
    poi_open_to = np.full(n_poi, DEFAULT_OPEN_TO_TICK, dtype=np.int16)

    ns_day, ns_night = _noise_stage_per_cell(p, cell_ix, cell_iy, cell_band)

    return WorldAssets(
        source=str(p),
        node_xy=node_xy,
        node_band=node_band,
        node_cell=node_cell,
        edge_u=edge_u,
        edge_v=edge_v,
        edge_len_m=edge_len,
        next_hop=next_hop,
        cell_dist=cell_dist,
        cell_ix=cell_ix,
        cell_iy=cell_iy,
        cell_band=cell_band,
        cell_centroid=cell_centroid,
        cell_rep_node=cell_rep_node,
        poi_cell=poi_cell,
        poi_node=poi_node,
        poi_price=poi_price,
        poi_stock0=poi_stock0,
        poi_capacity=poi_capacity,
        poi_open_from=poi_open_from,
        poi_open_to=poi_open_to,
        poi_cat=cats,
        noise_stage_day=ns_day,
        noise_stage_night=ns_night,
    )


def _noise_stage_per_cell(
    path: Path, cell_ix: np.ndarray, cell_iy: np.ndarray, cell_band: np.ndarray
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """W10(街路点 2.5 m 格子)の騒音段階 → セル別の**最頻値**(昼/夜)。

    ``perception.renderer._street_aggregate`` と**同じ集約規則**(セル×段の度数の argmax=
    同数なら小さい段)を使う。層契約(perception → world の一方向)により共有関数を作れないので
    二重定義になる。一致は ``tests/engine/test_renderer_wiring.py`` が実データで機械検査する。

    Returns:
        ``(昼, 夜)``。W10 が無ければ ``(None, None)``。

    Note:
        逐次ループ宣言(P4): **昼/夜の 2 回**のループのみ(点数 356,732 の集約は ``bincount``
        1 本=ベクトル演算)。起動時 1 回。
    """
    import pyarrow.parquet as pq

    pts = path / "w10_street_points.parquet"
    files = ("w10_noise_stage_day.npy", "w10_noise_stage_night.npy")
    if not pts.exists() or not all((path / f).exists() for f in files):
        return None, None

    d = pq.read_table(pts, columns=["x", "y", "band"]).to_pydict()
    sx = np.asarray(d["x"], dtype=np.float64)
    sy = np.asarray(d["y"], dtype=np.float64)
    sb = np.array([BAND_CODES[str(b)] for b in d["band"]], dtype=np.int8)
    ix = np.floor((sx - GRID_ORIGIN_XY[0]) / CELL_SIZE_M).astype(np.int32)
    iy = np.floor((sy - GRID_ORIGIN_XY[1]) / CELL_SIZE_M).astype(np.int32)

    n_cells = int(cell_ix.size)
    keys = _cell_key(cell_ix, cell_iy, cell_band)
    order = np.argsort(keys, kind="stable")
    skeys = keys[order]
    q = _cell_key(ix, iy, sb)
    pos = np.clip(np.searchsorted(skeys, q), 0, max(0, skeys.size - 1))
    hit = skeys[pos] == q
    cell_of_point = np.where(hit, order[pos], -1)
    valid = cell_of_point >= 0

    out: list[np.ndarray] = []
    for name in files:  # 逐次ループ宣言: 昼/夜の 2 回
        stage = np.load(path / name)
        flat = cell_of_point[valid] * N_NOISE_STAGES + np.clip(
            stage[valid].astype(np.int64), 0, N_NOISE_STAGES - 1
        )
        tab = np.bincount(flat, minlength=n_cells * N_NOISE_STAGES).reshape(
            n_cells, N_NOISE_STAGES
        )
        out.append(tab.argmax(axis=1).astype(np.uint8))
    return out[0], out[1]


def hash_free_cat_code(cat: str) -> int:
    """カテゴリ名 → 0..2 の価格帯コード(**決定論・ハッシュを使わない**)。

    値の割り当ては expedient(実データの客単価に寄せていない)。
    """
    c = str(cat)
    if "conv" in c or "コンビニ" in c or "shop" in c:
        return 0
    if "food" in c or "飲食" in c or "restaurant" in c or "cafe" in c:
        return 1
    return 2


def _nearest_node_in_cell(
    poi_cell: np.ndarray,
    poi_xy: np.ndarray,
    node_cell: np.ndarray,
    node_xy: np.ndarray,
    cell_rep_node: np.ndarray,
) -> np.ndarray:
    """POI の最寄ノード。セル代表ノードで代用する(expedient・C2 は店内位置を持たない)。"""
    out = np.where(
        poi_cell >= 0, cell_rep_node[np.clip(poi_cell, 0, cell_rep_node.size - 1)], -1
    ).astype(np.int32)
    return out


# ------------------------------------------------------------------ 合成世界(CI 用)
def _grid_next_hop(side: int, n_cells: int, neighbours: list[np.ndarray]) -> np.ndarray:
    """全点対の next-hop を BFS で作る(合成世界専用)。

    逐次ループ宣言2: セル数ぶんの BFS(139/453 規模)。
    """
    n = n_cells
    nh = np.full((n, n), -1, dtype=np.int32)
    for target in range(n):
        # target から逆向きに BFS(無向なので同じ)。dist[u] を確定した順に next_hop を決める。
        prev = np.full(n, -1, dtype=np.int32)
        seen = np.zeros(n, dtype=bool)
        seen[target] = True
        prev[target] = target
        frontier = [target]
        while frontier:
            nxt: list[int] = []
            for u in frontier:
                for v in neighbours[u].tolist():
                    if not seen[v]:
                        seen[v] = True
                        prev[v] = u  # v から target へ行く次の一歩は u
                        nxt.append(v)
            frontier = nxt
        nh[:, target] = prev
    return nh


def synthetic_assets(n_cells: int = 139, seed: int | str = 0) -> WorldAssets:
    """CI 用の合成小世界(1 セル=1 ノードの 4 近傍格子)。

    Args:
        n_cells: セル数(=ノード数)。
        seed: 合成の親シード(POI 配置・在庫)。

    Returns:
        ``WorldAssets``(``source="synthetic"``)。
    """
    if n_cells <= 0:
        raise ValueError("n_cells は正")
    side = int(np.ceil(np.sqrt(n_cells)))
    ix = (np.arange(n_cells) % side).astype(np.int32)
    iy = (np.arange(n_cells) // side).astype(np.int32)
    band = np.zeros(n_cells, dtype=np.int8)  # 合成世界は GL のみ
    xy = np.stack(
        [(ix.astype(np.float32) + 0.5) * CELL_SIZE_M, (iy.astype(np.float32) + 0.5) * CELL_SIZE_M],
        axis=1,
    ).astype(np.float32)

    # 4 近傍(格子内かつ n_cells 未満のものだけ)
    idx = -np.ones((side, side), dtype=np.int64)
    idx[iy, ix] = np.arange(n_cells)
    us: list[int] = []
    vs: list[int] = []
    for dy, dx in ((0, 1), (1, 0)):
        a = idx[: side - dy, : side - dx]
        b = idx[dy:, dx:]
        m = (a >= 0) & (b >= 0)
        us.extend(a[m].tolist())
        vs.extend(b[m].tolist())
    edge_u = np.asarray(us, dtype=np.int32)
    edge_v = np.asarray(vs, dtype=np.int32)
    edge_len = np.full(edge_u.size, CELL_SIZE_M, dtype=np.float32)

    adj: list[list[int]] = [[] for _ in range(n_cells)]
    for u, v in zip(edge_u.tolist(), edge_v.tolist()):
        adj[u].append(v)
        adj[v].append(u)
    neighbours = [np.asarray(sorted(a), dtype=np.int64) for a in adj]
    next_hop = _grid_next_hop(side, n_cells, neighbours)

    dx = ix[:, None].astype(np.int32) - ix[None, :].astype(np.int32)
    dy = iy[:, None].astype(np.int32) - iy[None, :].astype(np.int32)
    cell_dist = np.clip(
        (np.abs(dx) + np.abs(dy)).astype(np.int64) * int(CELL_SIZE_M), 0, 65_535
    ).astype(np.uint16)

    g = stream(seed, "world.synthetic")
    n_poi = 2 * n_cells
    poi_cell = np.repeat(np.arange(n_cells, dtype=np.int32), 2)
    poi_node = poi_cell.copy()
    cat_code = g.integers(0, len(SYNTHETIC_POI_CATS), size=n_poi)
    poi_price = np.asarray(SYNTHETIC_POI_PRICES, dtype=np.int32)[cat_code]
    poi_stock0 = g.integers(32, 97, size=n_poi).astype(np.int32)
    poi_capacity = np.full(n_poi, SYNTHETIC_POI_CAPACITY, dtype=np.int32)
    poi_open_from = np.full(n_poi, DEFAULT_OPEN_FROM_TICK, dtype=np.int16)
    poi_open_to = np.full(n_poi, DEFAULT_OPEN_TO_TICK, dtype=np.int16)

    return WorldAssets(
        source="synthetic",
        node_xy=xy,
        node_band=band,
        node_cell=np.arange(n_cells, dtype=np.int32),
        edge_u=edge_u,
        edge_v=edge_v,
        edge_len_m=edge_len,
        next_hop=next_hop,
        cell_dist=cell_dist,
        cell_ix=ix,
        cell_iy=iy,
        cell_band=band,
        cell_centroid=xy,
        cell_rep_node=np.arange(n_cells, dtype=np.int32),
        poi_cell=poi_cell,
        poi_node=poi_node,
        poi_price=poi_price,
        poi_stock0=poi_stock0,
        poi_capacity=poi_capacity,
        poi_open_from=poi_open_from,
        poi_open_to=poi_open_to,
        poi_cat=tuple(SYNTHETIC_POI_CATS[c] for c in cat_code.tolist()),
    )
