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
    # ---- C4(世界過程 第1陣)の追加資産 ----
    "PROCESS_FILES",
    "SHADOW_FRAMES_PER_DAY",
    "SHADOW_MINUTES_PER_FRAME",
    "HEAT_STAGE_ORDER",
    "RAILWAY_TO_LINE",
    "HOME_STATION_TITLE",
    "ProcessAssets",
    "load_process_assets",
    "load_process_assets_or_synthetic",
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
        poi_name: POI 名(W6 ``name`` 列)。合成世界は空タプル。**C9b G6 a′**
            (目印の対象解決 ``World.landmark_targets``)のためだけに持つ。
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
    #: POI 名(W6 ``name``)。**既定は空**=名前を持たない世界(合成)。
    poi_name: tuple[str, ...] = ()
    #: POI の平面座標 ``(n_poi, 2)`` float32(W6 ``x``/``y``)。``None``=資産が持たない
    #: (合成世界)→ ``poi_position()`` が最寄ノード座標で代用する。
    poi_xy: np.ndarray | None = None
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

    def poi_position(self) -> np.ndarray:
        """POI の平面座標 ``(n_poi, 2)``。資産が ``poi_xy`` を持たなければ**最寄ノード座標**。

        C9b G4(注意の焦点の距離判定)が読む 1 本。代用したときの誤差は「POI と最寄ノードの
        距離」で、W6 の POI は同一セル内の最近ノードに結ばれている(**expedient**)。
        """
        if self.poi_xy is not None:
            return self.poi_xy
        return self.node_xy[np.maximum(np.asarray(self.poi_node, dtype=np.int64), 0)]

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
        p / "w6_poi.parquet",
        # ``name`` は C9b G6 a′(目印の対象解決)のためだけに読む。数値配列は増えない。
        columns=["poi_id", "name", "cat", "place_id", "node_id", "x", "y"],
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
        poi_name=tuple(str(s) for s in poi["name"]),
        poi_xy=poi_xy,
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


# ==================================================================== C4: 世界過程が読む資産
#: 世界過程(C4 第1陣)が使う追加資産。1 つでも欠ければその過程だけ黙って休む。
PROCESS_FILES: Final[dict[str, str]] = {
    "weather_days": "w13_weather_days.parquet",
    "weather_hourly": "w13_weather_hourly.parquet",
    "timetables": "w12_timetables.parquet",
    "station_nodes": "w11_station_graph_nodes.parquet",
    "station_exits": "w11_station_exits.parquet",
    "external_nodes": "w12_external_nodes.parquet",
    "plan_spec": "w7_plan_spec.parquet",
    "street_points": "w10_street_points.parquet",
    "edges": "w1_edges.parquet",
    "poi": "w6_poi.parquet",
    "cells": "w2_cells.parquet",
}

#: OSM の街路施設(バス停・横断歩道等)。**世界資産の外**(``data/realworld/osm/``)に置かれた
#: 実データを、資産ディレクトリからの相対で探す(``data/world/v2`` → ``data/realworld/osm``)。
STREET_FEATURES_FILE: Final[str] = "street_features_overpass_20260907.json"
#: 座標系(W0)の凍結値を持つファイル(原点・m/度)。
WORLD_CRS_FILE: Final[str] = "world_crs.json"

#: 影グリッドの面数(D-W10 の 5 分刻み・288 面/日)。
SHADOW_FRAMES_PER_DAY: Final[int] = 288
#: 1 面あたりの分(= 1440 / 288)。
SHADOW_MINUTES_PER_FRAME: Final[int] = 5

#: W13 の暑さ段(境界=環境省/日本生気象学会 WBGT 21/25/28/31 に釘付け・語彙の割当は expedient)。
HEAT_STAGE_ORDER: Final[tuple[str, ...]] = (
    "快適",
    "やや暑い",
    "暑い",
    "厳しい暑さ",
    "危険な暑さ",
)

#: ODPT の railway id 末尾 → 時刻表(W12)の路線名。**W11 と W12 を突き合わせる唯一の表**。
#: 出所=``w11_station_graph_nodes.railway`` と ``w12_timetables.line`` の実値。
RAILWAY_TO_LINE: Final[dict[str, str]] = {
    "JR-East.Yamanote": "山手線",
    "JR-East.SaikyoKawagoe": "埼京線",
    "JR-East.ShonanShinjuku": "湘南新宿ライン",
    "Keio.Inokashira": "井の頭線",
    "TokyoMetro.Ginza": "銀座線",
    "TokyoMetro.Hanzomon": "半蔵門線",
    "TokyoMetro.Fukutoshin": "副都心線",
    "Tokyu.DenEnToshi": "田園都市線",
    "Tokyu.Toyoko": "東横線",
}

#: 舞台の中心駅(W11 の ``station_title``)。域外ノードはこの駅にぶら下がる(U10 §1.1)。
HOME_STATION_TITLE: Final[str] = "渋谷"


@dataclass(frozen=True)
class ProcessAssets:
    """世界過程(C4 第1陣)が読む静的資産。**全欄が空でも動く**(合成世界)。

    Attributes:
        source: 由来(資産ディレクトリ or ``"synthetic"``)。
        weather_dates: W13 の候補実日(昇順)。
        weather_stratum / weather_weekday_kind / weather_type: 日ごとの層(D-W15)。
        sunrise_min / sunset_min: 日の出・日の入(0 時からの分・欠測は NaN)。
        hourly_wbgt: ``(n_days, 24)`` の WBGT 推定値[℃]。
        hourly_heat_stage: ``(n_days, 24)`` の暑さ段(0-4・WBGT 21/25/28/31 に釘付け)。
        shadow_dates: ``w9_shadow_<date>.npy`` が実在する日。
        cell_street_point: ``(n_cells,)`` セル代表点に最も近い W10 街路点の索引(-1=無し)。
        n_street_points: W10 街路点の総数(ビット位置の範囲検査に使う)。
        tt_lines: 時刻表の路線名(昇順)。
        tt_line_idx / tt_calendar / tt_direction / tt_departure_min: 便ごとの列。
            ``tt_calendar`` は 0=平日 / 1=土休。``tt_departure_min`` は 0-1439(翌日跨ぎは剰余)。
        line_platform_cell: 路線索引 → 渋谷のホームが載るセル索引(-1=不明)。
        ext_node_line_idx: **方面ノード索引**(W12 ``w12_external_nodes`` の行順=W16
            ``direction_node``)→ ``tt_lines`` の路線索引(-1=非鉄道ゲート/時刻表に無い線)。
            複数線の方面(埼京線/湘南新宿ライン)は ``lines[0]`` に畳む(**expedient E2**)。
        station_exit_cell: W11 駅出口(45)のセル索引(昇順・重複あり。-1 は落とす)。
            計画実行層(D-66)の**降車セルの分散**に使う。
        plan_poi / plan_day / plan_start / plan_end: W7 営業時間の区間(分・``end`` は 1440 超あり)。
        edge_klass_code / edge_cell / edge_length_m: W1 の辺ごとの道路種別・所属セル・辺長。
        poi_cat_code / poi_cat_names: POI のカテゴリ(席数換算に使う)。
        bus_stop_cell: OSM ``highway=bus_stop`` をセル索引へ写像した列(§7.2 バス運行)。
        hotel_poi: ``cat == "hotel"`` の POI 索引(§7.2 ホテル客室在庫)。
    """

    source: str
    weather_dates: tuple[str, ...] = ()
    weather_stratum: tuple[str, ...] = ()
    weather_weekday_kind: tuple[str, ...] = ()
    weather_type: tuple[str, ...] = ()
    sunrise_min: np.ndarray | None = None
    sunset_min: np.ndarray | None = None
    hourly_wbgt: np.ndarray | None = None
    hourly_heat_stage: np.ndarray | None = None
    shadow_dates: tuple[str, ...] = ()
    shadow_dir: str = ""
    cell_street_point: np.ndarray | None = None
    n_street_points: int = 0
    tt_lines: tuple[str, ...] = ()
    tt_line_idx: np.ndarray | None = None
    tt_calendar: np.ndarray | None = None
    tt_direction: np.ndarray | None = None
    tt_departure_min: np.ndarray | None = None
    line_platform_cell: np.ndarray | None = None
    ext_node_line_idx: np.ndarray | None = None
    station_exit_cell: np.ndarray | None = None
    plan_poi: np.ndarray | None = None
    plan_day: np.ndarray | None = None
    plan_start: np.ndarray | None = None
    plan_end: np.ndarray | None = None
    edge_klass_code: np.ndarray | None = None
    edge_cell: np.ndarray | None = None
    edge_length_m: np.ndarray | None = None
    edge_klass_names: tuple[str, ...] = ()
    poi_cat_code: np.ndarray | None = None
    poi_cat_names: tuple[str, ...] = ()
    bus_stop_cell: np.ndarray | None = None
    hotel_poi: np.ndarray | None = None

    # ---- 有無の判定(過程ごとに独立して休める) ----
    @property
    def has_weather(self) -> bool:
        return bool(self.weather_dates) and self.hourly_wbgt is not None

    @property
    def has_shadow(self) -> bool:
        return bool(self.shadow_dates) and self.cell_street_point is not None

    @property
    def has_timetable(self) -> bool:
        return bool(self.tt_lines) and self.tt_departure_min is not None

    @property
    def has_plan_spec(self) -> bool:
        return self.plan_poi is not None and int(self.plan_poi.size) > 0

    @property
    def has_road(self) -> bool:
        return self.edge_klass_code is not None and int(self.edge_klass_code.size) > 0

    @property
    def has_bus_stops(self) -> bool:
        return self.bus_stop_cell is not None and int(self.bus_stop_cell.size) > 0

    def day_index_of(self, date: str) -> int:
        """日付文字列 → ``weather_dates`` の索引(無ければ -1)。"""
        try:
            return self.weather_dates.index(str(date))
        except ValueError:
            return -1

    def shadow_planes(self, date: str):
        """``w9_shadow_<date>.npy`` を memmap で開く(無ければ ``None``)。"""
        if not self.shadow_dir or str(date) not in self.shadow_dates:
            return None
        p = Path(self.shadow_dir) / f"w9_shadow_{date}.npy"
        if not p.exists():
            return None
        return np.load(p, mmap_mode="r")

    @classmethod
    def synthetic(cls) -> "ProcessAssets":
        """合成世界(資産なし)。全過程が「休む」形で成立する。"""
        return cls(source="synthetic")


def _hhmm_to_min(text: object) -> float:
    """``"04:45"`` → 285.0(空欄は NaN)。"""
    s = str(text or "").strip()
    if not s or ":" not in s:
        return float("nan")
    hh, mm = s.split(":", 1)
    try:
        return float(int(hh) * 60 + int(mm))
    except ValueError:
        return float("nan")


def _nearest_street_point_per_cell(
    path: Path,
    cell_centroid: np.ndarray,
    cell_ix: np.ndarray,
    cell_iy: np.ndarray,
    cell_band: np.ndarray,
) -> tuple[np.ndarray | None, int]:
    """セル代表点に最も近い W10 街路点(``(n_cells,)`` int32・-1=そのセルに点が無い)。

    逐次ループ宣言(P4): なし(格子キーの ``searchsorted`` と ``lexsort`` 各 1 本)。起動時 1 回。
    """
    import pyarrow.parquet as pq

    pts = path / PROCESS_FILES["street_points"]
    if not pts.exists():
        return None, 0
    d = pq.read_table(pts, columns=["x", "y", "band"]).to_pydict()
    sx = np.asarray(d["x"], dtype=np.float64)
    sy = np.asarray(d["y"], dtype=np.float64)
    sb = np.array([BAND_CODES[str(b)] for b in d["band"]], dtype=np.int8)
    ix = np.floor((sx - GRID_ORIGIN_XY[0]) / CELL_SIZE_M).astype(np.int32)
    iy = np.floor((sy - GRID_ORIGIN_XY[1]) / CELL_SIZE_M).astype(np.int32)
    keys = _cell_key(cell_ix, cell_iy, cell_band)
    order = np.argsort(keys, kind="stable")
    skeys = keys[order]
    q = _cell_key(ix, iy, sb)
    pos = np.clip(np.searchsorted(skeys, q), 0, max(0, skeys.size - 1))
    hit = skeys[pos] == q
    cell_of_point = np.where(hit, order[pos], -1)
    n_cells = int(cell_ix.size)
    out = np.full(n_cells, -1, dtype=np.int32)
    valid = np.flatnonzero(cell_of_point >= 0)
    if valid.size:
        c = cell_of_point[valid]
        dx = sx[valid] - cell_centroid[c, 0]
        dy = sy[valid] - cell_centroid[c, 1]
        d2 = dx * dx + dy * dy
        ordering = np.lexsort((valid, d2, c))  # セル昇順 → 距離昇順 → 点 id 昇順(決定論)
        cs = c[ordering]
        first = np.ones(cs.size, dtype=bool)
        first[1:] = cs[1:] != cs[:-1]
        out[cs[first]] = valid[ordering][first].astype(np.int32)
    return out, int(sx.size)


def _street_features_path(world_dir: Path) -> Path | None:
    """OSM 街路施設 JSON を探す(資産ディレクトリの中 → ``data/realworld/osm/``)。

    ``data/world/v2`` の 2 つ上が ``data`` なので ``data/realworld/osm/`` を見に行く。
    見つからなければ ``None``(バス運行が休む)。
    """
    candidates = [
        world_dir / STREET_FEATURES_FILE,
        world_dir.parent.parent / "realworld" / "osm" / STREET_FEATURES_FILE,
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def _bus_stop_cells(
    world_dir: Path,
    assets: WorldAssets,
    edge_cell: np.ndarray | None = None,
    edge_klass_code: np.ndarray | None = None,
    edge_len_m: np.ndarray | None = None,
    edge_klass_names: tuple[str, ...] = (),
) -> np.ndarray | None:
    """OSM ``highway=bus_stop`` → セル索引。

    **実データの欠落(親へ報告・黙って埋めない)**
        親が指した ``street_features_overpass_20260907.json`` は Overpass の ``out tags;``
        出力で、**要素に座標が無い**(``id``/``type``/``tags`` の3欄だけ)。127 件のバス停
        ノード id は ``shibuya_osm_wide_v8.json`` の ``nodes`` にも ``w1_nodes.parquet`` にも
        **1件も現れない**(歩行グラフに使われないノードだから)。よって座標から
        セルを決めることは、いま手元にあるデータでは**できない**(再取得は禁止)。

    実装(**expedient**・返済対象)
        実データとして使えるのは**件数 127** だけ。位置は「バス路線は幹線を走る」という
        一般則に従い、W1 の道路辺のうち ``primary``/``secondary`` の辺長が長いセルから
        件数ぶんを決定論で採る。座標が入手できたら(``lat``/``lon`` を持つ出力へ差し替えたら)
        本関数は自動的に座標側の経路を通る。

    Note:
        逐次ループ宣言(P4): OSM 要素数(2,009)ぶんの 1 本。**起動時 1 回**。
    """
    import json

    src = _street_features_path(world_dir)
    crs_file = world_dir / WORLD_CRS_FILE
    if src is None:
        return None
    payload = json.loads(src.read_text(encoding="utf-8"))
    lats: list[float] = []
    lons: list[float] = []
    n_stops = 0
    for el in payload.get("elements", ()):  # 逐次ループ宣言: OSM 要素数ぶん(起動時 1 回)
        tags = el.get("tags") or {}
        if tags.get("highway") != "bus_stop":
            continue
        n_stops += 1
        lat, lon = el.get("lat"), el.get("lon")
        if lat is not None and lon is not None:
            lats.append(float(lat))
            lons.append(float(lon))
    if n_stops == 0:
        return None

    if lats and crs_file.is_file():
        crs = json.loads(crs_file.read_text(encoding="utf-8"))
        olat, olon = (float(v) for v in crs["origin_latlon"])
        m_lat = float(crs["m_per_deg_lat"])
        m_lon = float(crs["m_per_deg_lon"])
        x = (np.asarray(lons, dtype=np.float64) - olon) * m_lon
        y = (np.asarray(lats, dtype=np.float64) - olat) * m_lat
        ix = np.floor(x / CELL_SIZE_M).astype(np.int64)
        iy = np.floor(y / CELL_SIZE_M).astype(np.int64)
        band = np.zeros(ix.size, dtype=np.int8)  # バス停は地上(GL)
        key = _cell_key(ix, iy, band)
        cell_keys = _cell_key(
            np.asarray(assets.cell_ix), np.asarray(assets.cell_iy), np.asarray(assets.cell_band)
        )
        order = np.argsort(cell_keys, kind="stable")
        pos = np.clip(np.searchsorted(cell_keys[order], key), 0, max(0, cell_keys.size - 1))
        hit = cell_keys[order][pos] == key
        return order[pos][hit].astype(np.int64)

    # ---- 座標が無い(いまのデータ): 幹線の長いセルへ件数ぶんを置く(expedient) ----
    if edge_cell is None or edge_klass_code is None or edge_len_m is None:
        return None
    arterial = {
        i for i, name in enumerate(edge_klass_names) if name in ("primary", "secondary")
    }
    code = np.asarray(edge_klass_code, dtype=np.int64)
    keep = np.isin(code, np.asarray(sorted(arterial), dtype=np.int64)) if arterial else None
    if keep is None or not keep.any():
        keep = np.ones(code.size, dtype=bool)
    cells = np.asarray(edge_cell, dtype=np.int64)[keep]
    lens = np.asarray(edge_len_m, dtype=np.float64)[keep]
    ok = (cells >= 0) & (cells < assets.n_cells)
    if not ok.any():
        return None
    per_cell = np.bincount(cells[ok], weights=lens[ok], minlength=assets.n_cells)
    live = np.flatnonzero(per_cell > 0)
    order = live[np.lexsort((live, -per_cell[live]))]
    if order.size == 0:
        return None
    take = np.arange(n_stops) % order.size  # 件数 > 候補セル数なら 1 セルに複数停留所
    return order[take].astype(np.int64)


def load_process_assets(path, assets: WorldAssets) -> ProcessAssets:
    """``data/world/v2`` から世界過程(C4 第1陣)の資産を読む。

    Args:
        path: 資産ディレクトリ。
        assets: 既に読んだ ``WorldAssets``(セル索引・ノード→セルを再利用する)。

    Returns:
        ``ProcessAssets``。読めなかった欄は空のまま(その過程が休む)。

    Note:
        逐次ループ宣言(P4): W7 の営業時間 JSON を PlanSpec 行(2,337)ぶん解く 1 本と、
        W11 のホーム行(12)ぶんの 1 本。**起動時 1 回**で tick には比例しない。
    """
    import json

    import pyarrow.parquet as pq

    p = Path(path)
    n_cells = assets.n_cells

    # ---- W2: place_id → セル索引 ----
    place_to_cell: dict[str, int] = {}
    if (p / PROCESS_FILES["cells"]).exists():
        cells = pq.read_table(p / PROCESS_FILES["cells"], columns=["place_id"]).to_pydict()
        place_to_cell = {str(pid): i for i, pid in enumerate(cells["place_id"])}

    # ---- W13: 気象(実日ブートストラップの候補集合) ----
    dates: tuple[str, ...] = ()
    stratum: tuple[str, ...] = ()
    wkind: tuple[str, ...] = ()
    wtype: tuple[str, ...] = ()
    sunrise = sunset = None
    hourly_wbgt = hourly_heat = None
    fd = p / PROCESS_FILES["weather_days"]
    fh = p / PROCESS_FILES["weather_hourly"]
    if fd.exists() and fh.exists():
        d = pq.read_table(fd).to_pydict()
        idx = sorted(range(len(d["date"])), key=lambda i: str(d["date"][i]))
        dates = tuple(str(d["date"][i]) for i in idx)
        stratum = tuple(str(d["stratum"][i]) for i in idx)
        wkind = tuple(str(d["weekday_kind"][i]) for i in idx)
        wtype = tuple(str(d["weather_type"][i]) for i in idx)
        sunrise = np.array([_hhmm_to_min(d["sunrise"][i]) for i in idx], dtype=np.float64)
        sunset = np.array([_hhmm_to_min(d["sunset"][i]) for i in idx], dtype=np.float64)
        pos = {dt: k for k, dt in enumerate(dates)}
        h = pq.read_table(fh, columns=["date", "hour", "wbgt_est", "heat_stage"]).to_pydict()
        hourly_wbgt = np.full((len(dates), 24), np.nan, dtype=np.float64)
        hourly_heat = np.zeros((len(dates), 24), dtype=np.int8)
        stage_names = list(HEAT_STAGE_ORDER)
        hd = np.array([pos.get(str(x), -1) for x in h["date"]], dtype=np.int64)
        hh = np.asarray(h["hour"], dtype=np.int64)
        hv = np.asarray(h["wbgt_est"], dtype=np.float64)
        hs = np.array(
            [stage_names.index(str(s)) if str(s) in stage_names else 0 for s in h["heat_stage"]],
            dtype=np.int8,
        )
        ok = (hd >= 0) & (hh >= 0) & (hh < 24)
        hourly_wbgt[hd[ok], hh[ok]] = hv[ok]
        hourly_heat[hd[ok], hh[ok]] = hs[ok]

    # ---- W9: 影グリッド(実在する日だけ) ----
    shadow_dates = tuple(
        sorted(f.name[len("w9_shadow_") : -len(".npy")] for f in p.glob("w9_shadow_*.npy"))
    )
    cell_point, n_points = _nearest_street_point_per_cell(
        p,
        assets.cell_centroid.astype(np.float64),
        np.asarray(assets.cell_ix),
        np.asarray(assets.cell_iy),
        np.asarray(assets.cell_band),
    )

    # ---- W12: 時刻表 ----
    tt_lines: tuple[str, ...] = ()
    tt_line_idx = tt_cal = tt_dir = tt_dep = None
    ft = p / PROCESS_FILES["timetables"]
    if ft.exists():
        t = pq.read_table(
            ft, columns=["line", "direction", "calendar", "departure_min"]
        ).to_pydict()
        tt_lines = tuple(sorted({str(x) for x in t["line"]}))
        lidx = {name: i for i, name in enumerate(tt_lines)}
        dirs = sorted({str(x) for x in t["direction"]})
        didx = {name: i for i, name in enumerate(dirs)}
        tt_line_idx = np.array([lidx[str(x)] for x in t["line"]], dtype=np.int16)
        tt_cal = np.array([1 if str(c) != "Weekday" else 0 for c in t["calendar"]], dtype=np.int8)
        tt_dir = np.array([didx[str(x)] for x in t["direction"]], dtype=np.int16)
        tt_dep = (np.asarray(t["departure_min"], dtype=np.int64) % 1_440).astype(np.int32)

    # ---- W11: 路線 → 渋谷のホームセル ----
    line_platform_cell = None
    fn = p / PROCESS_FILES["station_nodes"]
    if ft.exists() and fn.exists() and tt_lines:
        sg = pq.read_table(
            fn, columns=["kind", "station_title", "railway", "place_id"]
        ).to_pydict()
        line_platform_cell = np.full(len(tt_lines), -1, dtype=np.int32)
        # 逐次ループ宣言: ホーム行(12)ぶん
        for i in range(len(sg["kind"])):
            if str(sg["kind"][i]) != "platform":
                continue
            if str(sg["station_title"][i]) != HOME_STATION_TITLE:
                continue
            rid = str(sg["railway"][i]).split(":", 1)[-1]
            name = RAILWAY_TO_LINE.get(rid)
            if name is None or name not in tt_lines:
                continue
            cell = place_to_cell.get(str(sg["place_id"][i]), -1)
            if cell >= 0:
                line_platform_cell[tt_lines.index(name)] = int(cell)

    # ---- W12/W11: 方面ノード → 路線 / 駅出口 → セル(D-66 計画実行層) ----
    ext_node_line_idx = None
    fx = p / PROCESS_FILES["external_nodes"]
    if fx.exists() and tt_lines:
        ex = pq.read_table(fx, columns=["node_id", "kind", "lines"]).to_pydict()
        idx = np.full(len(ex["node_id"]), -1, dtype=np.int16)
        # 逐次ループ宣言: 方面ノード(10)ぶん。起動時 1 回。
        for i in range(len(ex["node_id"])):
            if str(ex["kind"][i]) != "rail":
                continue
            try:
                names = json.loads(str(ex["lines"][i]) or "[]")
            except ValueError:
                names = []
            for name in names:  # 先頭の線に畳む(expedient E2)
                if str(name) in tt_lines:
                    idx[i] = tt_lines.index(str(name))
                    break
        ext_node_line_idx = idx
    station_exit_cell = None
    fe = p / PROCESS_FILES["station_exits"]
    if fe.exists() and place_to_cell:
        exits = pq.read_table(fe, columns=["own_grid_place_id", "place_id"]).to_pydict()
        cells = [
            place_to_cell.get(
                str(exits["own_grid_place_id"][i]),
                place_to_cell.get(str(exits["place_id"][i]), -1),
            )
            for i in range(len(exits["place_id"]))
        ]
        arr = np.asarray([c for c in cells if 0 <= c < n_cells], dtype=np.int32)
        station_exit_cell = np.sort(arr)

    # ---- W6/W7: POI カテゴリと営業時間 PlanSpec ----
    plan_poi = plan_day = plan_start = plan_end = None
    poi_cat_code = None
    poi_cat_names: tuple[str, ...] = ()
    fp = p / PROCESS_FILES["plan_spec"]
    fpoi = p / PROCESS_FILES["poi"]
    if fpoi.exists():
        poi = pq.read_table(fpoi, columns=["poi_id", "cat"]).to_pydict()
        poi_index = {str(x): i for i, x in enumerate(poi["poi_id"])}
        poi_cat_names = tuple(sorted({str(c) for c in poi["cat"]}))
        cmap = {name: i for i, name in enumerate(poi_cat_names)}
        poi_cat_code = np.array([cmap[str(c)] for c in poi["cat"]], dtype=np.int16)
        if fp.exists():
            ps = pq.read_table(fp, columns=["poi_id", "kind", "content"]).to_pydict()
            rp: list[int] = []
            rd: list[int] = []
            rs: list[int] = []
            re_: list[int] = []
            # 逐次ループ宣言: PlanSpec 行(2,337)ぶん(JSON を解く)
            for i in range(len(ps["poi_id"])):
                if str(ps["kind"][i]) != "opening_hours":
                    continue
                j = poi_index.get(str(ps["poi_id"][i]), -1)
                if j < 0:
                    continue
                try:
                    week = json.loads(str(ps["content"][i]))
                except (ValueError, TypeError):
                    continue
                for day, spans in enumerate(list(week)[:7]):
                    for span in spans:
                        if len(span) != 2:
                            continue
                        rp.append(j)
                        rd.append(day)
                        rs.append(int(span[0]))
                        re_.append(int(span[1]))
            plan_poi = np.asarray(rp, dtype=np.int32)
            plan_day = np.asarray(rd, dtype=np.int8)
            plan_start = np.asarray(rs, dtype=np.int32)
            plan_end = np.asarray(re_, dtype=np.int32)

    # ---- W1: 道路の辺(断面自動車交通) ----
    edge_klass_code = edge_cell = edge_len = None
    edge_klass_names: tuple[str, ...] = ()
    fe = p / PROCESS_FILES["edges"]
    if fe.exists():
        e = pq.read_table(fe, columns=["u_idx", "klass", "length_m"]).to_pydict()
        edge_klass_names = tuple(sorted({str(k) for k in e["klass"]}))
        kmap = {name: i for i, name in enumerate(edge_klass_names)}
        edge_klass_code = np.array([kmap[str(k)] for k in e["klass"]], dtype=np.int16)
        u = np.clip(np.asarray(e["u_idx"], dtype=np.int64), 0, max(0, assets.n_nodes - 1))
        edge_cell = np.asarray(assets.node_cell, dtype=np.int32)[u]
        edge_len = np.asarray(e["length_m"], dtype=np.float64)

    return ProcessAssets(
        source=str(p),
        weather_dates=dates,
        weather_stratum=stratum,
        weather_weekday_kind=wkind,
        weather_type=wtype,
        sunrise_min=sunrise,
        sunset_min=sunset,
        hourly_wbgt=hourly_wbgt,
        hourly_heat_stage=hourly_heat,
        shadow_dates=shadow_dates,
        shadow_dir=str(p) if shadow_dates else "",
        cell_street_point=(
            cell_point if (cell_point is not None and int(cell_point.size) == n_cells) else None
        ),
        n_street_points=n_points,
        tt_lines=tt_lines,
        tt_line_idx=tt_line_idx,
        tt_calendar=tt_cal,
        tt_direction=tt_dir,
        tt_departure_min=tt_dep,
        line_platform_cell=line_platform_cell,
        ext_node_line_idx=ext_node_line_idx,
        station_exit_cell=station_exit_cell,
        plan_poi=plan_poi,
        plan_day=plan_day,
        plan_start=plan_start,
        plan_end=plan_end,
        edge_klass_code=edge_klass_code,
        edge_cell=edge_cell,
        edge_length_m=edge_len,
        edge_klass_names=edge_klass_names,
        poi_cat_code=poi_cat_code,
        poi_cat_names=poi_cat_names,
        bus_stop_cell=_bus_stop_cells(
            p, assets, edge_cell, edge_klass_code, edge_len, edge_klass_names
        ),
        hotel_poi=np.flatnonzero(
            np.asarray([str(c) == "hotel" for c in assets.poi_cat], dtype=bool)
        ).astype(np.int64),
    )


def load_process_assets_or_synthetic(path, assets: WorldAssets) -> ProcessAssets:
    """資産があれば読み、無ければ空の ``ProcessAssets``(全過程が休む)。"""
    if path is None:
        return ProcessAssets.synthetic()
    p = Path(path)
    if not p.is_dir():
        return ProcessAssets.synthetic()
    return load_process_assets(p, assets)
