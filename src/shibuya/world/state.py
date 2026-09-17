"""world.state — セル/POI の状態レジストリ(SoA)と世界オブジェクト ``World``。

正典
- 実装計画書 §3: 「world: セル/POI/グラフ/可視性(mmap)/騒音場」。SoA・**セル(100m)を
  第一のチャンク**。
- 知覚契約書 §6 起床条件(i): 「所属セルの **B4 ハッシュ変化**(密度段階の跨ぎ・騒音段階・
  構造物・顕著行為の到達)」→ ``b4_hash`` をセル欄に持つ(``engine.change_detect`` が更新)。
- 行動契約書 §2.1「購入」: 前提=**営業中・在庫>0・所持金≧価格**、効果=
  在庫−1・所持金−価格・所持+1・**店の売上+同額(保存則)** → POI 側に
  ``stock`` / ``price`` / ``revenue`` を持つ。
- 運用設計書 §2.2 Phase C: 書き込み口は ``engine.resolve`` 一本 →
  ``freeze()``/``writable()`` で機械強制(``.writable(`` を書いてよいのは resolve.py だけ)。
- 予算宣言表: セル1つあたりのバイト上限行は**存在しない**(``core.soa`` の
  ``CELL_CAP_BUDGET_ROW = None``)ので cap は総額側(M8)で見る。

逐次ループ宣言(P4): ``freeze``/``thaw`` のフィールド数ぶんのみ。

expedient(本モジュール分)
- 密度段階 ``DENSITY_STAGE_EDGES``(人/セル)は自前。知覚契約書は「密度段階の跨ぎ」としか
  言わず段の刻みを与えていない(B4 の段は C3 のレンダラで確定する)。
- 騒音段階: 静的な W10 昼夜場は ``assets.noise_stage_day/night``(不変・セル別最頻値)に持ち、
  ``cells.noise_stage`` は**動的上書き欄**(0=上書きなし)として残す。どちらを読むかは
  ``noise_stage_for_tick`` が一本で決める(合成世界は全セル 0)。
- 営業時間は W7(PlanSpec)が資産に無いので POI 一律 10:00-22:00(``assets`` の既定値)。
- 書き込みガードの実装を agents.state と二重に持つ(層契約により共有モジュールを作れない)。
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Final, Iterator

import numpy as np

from shibuya.core.hashing import blake3_hex
from shibuya.core.soa import Registry
from shibuya.world.assets import WorldAssets, load_assets, synthetic_assets
from shibuya.world.graph import WalkGraph

__all__ = ["DENSITY_STAGE_EDGES", "DENSITY_STAGE_EDGES_PER_M2", "World"]

#: 密度段階の境界[人/セル](expedient・B4 の段は C3 のレンダラで確定する)。
#: **node 幾何(既定)専用**——``geometry="edge"`` では
#: ``DENSITY_STAGE_EDGES_PER_M2`` を使う(C9 §4 改訂)。
DENSITY_STAGE_EDGES: Final[tuple[int, ...]] = (1, 5, 20, 60, 150, 400, 1_000)

#: 密度段階の境界[**人/m²**](Fruin 1971 歩行路 LOS の A/B/C/D/E/F 境界)。
#: C9 決定アジェンダ §4 改訂: 「現行の密度段階(最上段 1,000 人/セル=0.238 人/m²)は
#: 7 段すべて Fruin LOS A の内側=**減速が実質 no-op**。段の刻みを人/m² で定義し直す」。
#: **mechanism**: 段の境界は LOS 定義に釘付け(``perception.templates.DENSITY_LOS_EDGES_PER_M2``
#: と同値。層契約により二重定義=テストが一致を機械検査)。分母(歩行可能面積)は expedient。
DENSITY_STAGE_EDGES_PER_M2: Final[tuple[float, ...]] = (
    0.30754, 0.43056, 0.71760, 1.07640, 2.15279,
)


class World:
    """世界状態(セル・POI)+不変資産(グラフ)。

    Example:
        >>> w = World.synthetic(n_cells=16, seed=1)
        >>> w.n_cells, w.n_poi
        (16, 32)
    """

    def __init__(self, assets: WorldAssets) -> None:
        self.assets = assets
        self.graph = WalkGraph(assets)
        n_cells = assets.n_cells
        n_poi = assets.n_poi

        self.cells = Registry.for_cells(n_cells)
        self.cells.declare("density", np.int32, byte_budget_per_agent=4, mechanism=True,
                           doc="セル在席人数(毎tick np.bincount で再計算・B4 密度段の素)")
        self.cells.declare("density_stage", np.uint8, byte_budget_per_agent=1, mechanism=False,
                           doc="密度段階(DENSITY_STAGE_EDGES・expedient=刻みは自前)")
        self.cells.declare("noise_stage", np.uint8, byte_budget_per_agent=1, mechanism=False,
                           doc="騒音段階の**動的上書き欄**(0=静的 W10 昼夜場を使う・"
                               "``noise_stage_for_tick`` が優先順を決める)")
        self.cells.declare("open_count", np.int32, byte_budget_per_agent=4, mechanism=True,
                           doc="そのセルで営業中の POI 数(B4 の構成要素)")
        self.cells.declare("b4_hash", np.uint64, byte_budget_per_agent=8, mechanism=True,
                           doc="セル動的ブロック B4 の xxh64(起床条件(i)・prefix鍵・三役)")

        self.pois = Registry.for_cells(n_poi)
        self.pois.declare("cell", np.int32, byte_budget_per_agent=4, mechanism=True,
                          doc="POI の所属セル索引")
        self.pois.declare("node", np.int32, byte_budget_per_agent=4, mechanism=True,
                          doc="POI の最寄ノード(セル代表ノードで代用)")
        self.pois.declare("stock", np.int32, byte_budget_per_agent=4, mechanism=True,
                          doc="棚在庫(購入で−1・補充行動は C4)")
        self.pois.declare("price", np.int32, byte_budget_per_agent=4, mechanism=True,
                          doc="価格[円](行動契約書 §2.1 購入)")
        self.pois.declare("revenue", np.int64, byte_budget_per_agent=8, mechanism=True,
                          doc="累計売上[円](保存則: Σmoney+Σrevenue が不変)")
        self.pois.declare("capacity", np.int32, byte_budget_per_agent=4, mechanism=False,
                          doc="1 tick に受け入れる客数(資源の容量・expedient)")
        self.pois.declare("open_from", np.int16, byte_budget_per_agent=2, mechanism=False,
                          doc="開店 tick(W7 PlanSpec が無いので既定 10:00)")
        self.pois.declare("open_to", np.int16, byte_budget_per_agent=2, mechanism=False,
                          doc="閉店 tick(W7 PlanSpec が無いので既定 22:00)")
        self.pois.declare("open_now", np.int8, byte_budget_per_agent=1, mechanism=True,
                          doc="営業フラグの**動的上書き欄**(-1=上書きなし / 0=閉 / 1=開)。"
                              "C4 の営業時間過程(W7 PlanSpec・複数区間・日跨ぎ)が書く。"
                              "``open_mask`` が優先順を決める(``noise_stage`` と同型)")

        self.pois.cell[:] = assets.poi_cell
        self.pois.node[:] = assets.poi_node
        self.pois.stock[:] = assets.poi_stock0
        self.pois.price[:] = assets.poi_price
        self.pois.capacity[:] = assets.poi_capacity
        self.pois.open_from[:] = assets.poi_open_from
        self.pois.open_to[:] = assets.poi_open_to
        self.pois.open_now[:] = -1  # 上書きなし(C2 と同じ 10:00-22:00 の既定へ落ちる)
        self._frozen = False
        #: 飲食店マスク(``eatery_mask`` の遅延キャッシュ)。**SoA の欄ではない**
        #: =``Registry.state_hash`` にも checkpoint にも入らない(既定のバイトは動かない)。
        self._eatery_mask: np.ndarray | None = None

    # ---- 生成 ----
    @classmethod
    def synthetic(cls, n_cells: int = 139, seed: int | str = 0) -> "World":
        """CI 用の合成小世界。"""
        return cls(synthetic_assets(n_cells=n_cells, seed=seed))

    @classmethod
    def load(cls, path) -> "World":
        """``data/world/v2`` の資産から作る。"""
        return cls(load_assets(path))

    @classmethod
    def load_or_synthetic(cls, path, *, n_cells: int = 139, seed: int | str = 0) -> "World":
        """資産があれば読み、無ければ合成世界へ落ちる(CLI の既定動作)。"""
        from shibuya.world.assets import assets_available

        if assets_available(path):
            return cls.load(path)
        return cls.synthetic(n_cells=n_cells, seed=seed)

    # ---- 規模 ----
    @property
    def n_cells(self) -> int:
        return self.assets.n_cells

    @property
    def n_poi(self) -> int:
        return self.assets.n_poi

    @property
    def n_nodes(self) -> int:
        return self.assets.n_nodes

    # ---- 素通し ----
    @property
    def density(self) -> np.ndarray:
        return self.cells.density

    @property
    def b4_hash(self) -> np.ndarray:
        return self.cells.b4_hash

    def route_next_node(self, node, target_node) -> np.ndarray:
        """``WalkGraph.route_next_node`` の委譲(ベクトル化 next-hop)。"""
        return self.graph.route_next_node(node, target_node)

    # ---- 純関数(書き込みは resolve が行う) ----
    def compute_density(self, agent_cell) -> np.ndarray:
        """個体のセル配列 → セル別在席数(``np.bincount``・毎tick 再計算=増分にしない)。"""
        c = np.asarray(agent_cell, dtype=np.int64).ravel()
        valid = c[(c >= 0) & (c < self.n_cells)]
        return np.bincount(valid, minlength=self.n_cells).astype(np.int32)

    def density_stage(self, density=None) -> np.ndarray:
        """密度 → 段階(``DENSITY_STAGE_EDGES`` の右側挿入位置)。"""
        d = self.cells.density if density is None else np.asarray(density)
        return np.searchsorted(np.asarray(DENSITY_STAGE_EDGES), d, side="right").astype(np.uint8)

    @property
    def eatery_mask(self) -> np.ndarray:
        """飲食店の POI マスク(``(n_poi,)`` bool)。**語彙 v2 の行動語「食事」の前提**。

        判定は ``world.assets.hash_free_cat_code(cat) == 1``(= 価格帯「飲食」)を**そのまま
        再利用**する。カテゴリ判定の表を 2 つ持たないための選択で、``economy.entry_capital``
        の価格帯・``economy.goods.CATEGORY_NAMES[1]``(飲食)と同じ線になる。

        Note:
            ``cat == "nightlife"``(バー・クラブ)は ``hash_free_cat_code`` が 2 を返すので
            **含まれない**(経済側では大分類 M=宿泊/飲食サービス業だが、価格帯は別)。
            この食い違いは ``hash_free_cat_code`` 由来で、本 property では直さない
            (直すならカテゴリ表そのものの改版=親判断)。

        逐次ループ宣言(P4): **初回の 1 回だけ** POI 数ぶんの Python ループ(カテゴリ名の
        文字列判定)。以後はキャッシュを返す。tick にも個体数にも比例しない。
        """
        if self._eatery_mask is None:
            from shibuya.world.assets import hash_free_cat_code

            cats = tuple(self.assets.poi_cat)
            self._eatery_mask = np.asarray(
                [hash_free_cat_code(c) == 1 for c in cats], dtype=bool
            )
        return self._eatery_mask

    def open_mask(self, tick: int) -> np.ndarray:
        """その tick に営業している POI の bool マスク(1 日 1,440 tick で剰余を取る)。

        優先順(``noise_stage_for_tick`` と同型・黙って一本化しない):
          1. ``pois.open_now`` に 0 以上がある → **C4 の営業時間過程による上書き**
             (W7 PlanSpec の複数区間・日跨ぎを 1 本の欄で表す)。
          2. それ以外 → C2 の単一区間 ``open_from``/``open_to``(既定 10:00-22:00)。
        """
        now = self.pois.open_now
        if now.size and bool(np.any(now >= 0)):
            return np.asarray(now > 0)
        t = int(tick) % 1_440
        return (self.pois.open_from <= t) & (t < self.pois.open_to)

    def open_count_per_cell(self, tick: int) -> np.ndarray:
        """セル別の営業中 POI 数(B4 の構成要素**ではない**=描画には出ない。C4 の在庫/混雑用)。"""
        m = self.open_mask(tick)
        cells = self.pois.cell[m].astype(np.int64)
        cells = cells[(cells >= 0) & (cells < self.n_cells)]
        return np.bincount(cells, minlength=self.n_cells).astype(np.int32)

    def noise_stage_for_tick(self, tick: int, tick_seconds: int = 60) -> np.ndarray:
        """その tick に使うセル別騒音段階(**W4-C3 結線の単一の出所**)。

        優先順(黙って一本化しない・親へ報告済みの決定):
          1. ``cells.noise_stage`` に 0 以外がある → **動的上書き**(C4 の世界過程が書く欄)。
          2. それ以外 → 資産 W10 の**静的昼夜場**(環境基準の昼 6-22 時 / 夜 22-6 時)。

        「2 本のセル配列を World に持ち、時刻でどちらを読むか決める」形を採った(親が挙げた
        2 案のうち**単純な方**)。``cells.noise_stage`` を 6:00/22:00 に書き換える案は
        resolve の書き込み窓を毎日 2 回開ける必要があり、静的資産のために単一書き手の
        規律を使うのは割に合わない。

        Args:
            tick: 現在 tick。
            tick_seconds: 1 tick の秒数(既定 60=1 分)。
        """
        dyn = self.cells.noise_stage
        if dyn.size and bool(np.any(dyn)):
            return np.asarray(dyn, dtype=np.uint8)
        hour = int(int(tick) * int(tick_seconds) // 3_600) % 24
        return self.assets.noise_stage_for_hour(hour)

    # ---- 書き込みガード ----
    @property
    def frozen(self) -> bool:
        return self._frozen

    def freeze(self) -> None:
        """セル・POI の全配列を読み取り専用にする(逐次ループ宣言: フィールド数ぶん)。"""
        for reg in (self.cells, self.pois):
            for arr in reg.arrays.values():
                arr.flags.writeable = False
        self._frozen = True

    def thaw(self) -> None:
        """全配列を書き込み可能に戻す(``writable`` 以外から呼ばない)。"""
        for reg in (self.cells, self.pois):
            for arr in reg.arrays.values():
                arr.flags.writeable = True
        self._frozen = False

    @contextmanager
    def writable(self) -> Iterator["World"]:
        """``with world.writable():`` の間だけ書ける。**呼んでよいのは engine/resolve.py だけ**。"""
        was_frozen = self._frozen
        if was_frozen:
            self.thaw()
        try:
            yield self
        finally:
            if was_frozen:
                self.freeze()

    # ---- 監査 ----
    def state_hash(self) -> str:
        """セル+POI の状態ハッシュ(2 本の ``Registry.state_hash`` を連結して blake3)。"""
        return blake3_hex(
            (self.cells.state_hash() + "\x1f" + self.pois.state_hash()).encode("utf-8")
        )

    def bytes_total(self) -> int:
        return self.cells.bytes_total() + self.pois.bytes_total()

    def summary(self) -> str:
        return self.assets.summary()
