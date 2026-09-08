"""economy.goods — 物の保存則(U-Goods)。``move_goods`` **単一API**と SKU 別収支。

正典(世界過程設計書 §7.1・決定(仮)2026-09-07)
- 「``move_goods(from, to, qty, sku, account_code)`` **単一API**・在庫の直接代入は静的禁止。
  faucet=域外仕入(RoW→店舗)・持込物/sink=消費(世帯)・廃棄搬出(区の収集→bbox外)・
  返品/域外出荷。残差科目=**棚卸差異**(閾値超でゲート失敗)・退蔵項=売れ残り在庫・退蔵耐久財。
  検算①=全SKUで**期首在庫+流入−流出=期末在庫**(O(N)総和・日次)
  ②=**廃棄sinkの月次総量≈渋谷区ごみ実数(119.6 t/日)のband**(新規台帳行W1)。
  **SKU別在庫は店舗POI側(per_cell_bytes)に置き個体M1には載せない**。」
- §7.2 初回実装(第1陣): 物の保存則骨格 / 店舗補充・棚在庫 / 納品 / 廃棄物収集。
  本モジュールが持つのは**エンジンから呼べる操作**まで(それを起動する店員・納品ドライバー・
  清掃員の行動は C4-subH の担当)。
- §7.2 「O(t)ログ(納品・配達・収集・出動)は状態成長宣言(D-R2-6)を型レベルで強制」
  → ``delivery_log`` はリングバッファ+保持窓+日次集約(``growth_declarations``)。
- CLAUDE.md §3「棚が減る=店員が補充する」が**閉じた収支として検証可能**になる。

**世帯側を SKU 別に持たない設計**(設計書「個体M1には載せない」の実装形)
    世帯の所持は個体 SoA の ``holdings``(個数・uint8)のまま。SKU 別の保有は
    **全世帯の合計**(``household_sku``・``(n_sku,)``)だけを持つ。これで検算①(SKU別の
    期首+流入−流出=期末)は閉じるが、「誰が何を持っているか」は答えられない
    (第2陣以降の課題として登録)。

逐次ループ宣言(P4)
1. ``SkuRegistry.for_categories``: **カテゴリ数**(3)ぶん。POI 数には比例しない。
2. ``__init__`` / ``freeze``: 配列本数ぶん(10 本前後)。
3. ``on_day_end``: SKU 数ぶんの NumPy 総和(Python ループ無し)。
販売・補充・収集は全て ``np.add.at`` のベクトル演算(個体・POI 数ぶんの Python ループ無し)。

expedient(本モジュール分)
- SKU 粒度(カテゴリあたり 1-3 品目)・質量[g]・標準原価。設計書 §7.2 が「SKU粒度・棚卸閾値・
  初期在庫・補充閾値/ロット」を expedient に挙げている通り、出典は無い。
- 販売時の払い出し規則 = **最初の非空スロット**(スロット選択の根拠は無い)。
- 在庫評価は**標準原価**(移動平均法ではない)。原価 = 価格 ÷ k(内生フロア・§8 H-2)。
- 棚卸差異の閾値 = 流量の 1%(``STOCKTAKE_THRESHOLD_RATIO``)。
- 退蔵(売れ残り)の判定日数 = 14 日。
- 廃棄 band の幅 = ±30%(``anchors.WASTE_BAND_RATIO``)。
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import IntEnum
from typing import Final, Iterator, Mapping, Sequence

import numpy as np

from shibuya.core.growth import GrowthDeclaration, Retention
from shibuya.economy import pricing
from shibuya.economy.accounts import AccountCode, FlowKind, Sector
from shibuya.economy.anchors import WASTE_BAND_RATIO, WASTE_TONNES_PER_DAY

__all__ = [
    "GoodsCode",
    "NodeKind",
    "GoodsRef",
    "GOODS_FAUCET_SINK",
    "goods_is_allowed",
    "goods_flow_kind",
    "SkuRegistry",
    "GoodsLedger",
    "WasteBand",
    "growth_declarations",
]


class NodeKind(IntEnum):
    """物の置き場(``move_goods`` の from / to)。"""

    STORE_SHELF = 0  # 店舗の棚(POI 側・per_cell_bytes)
    STORE_BIN = 1  # 店舗の廃棄ビン(収集待ち)
    HOUSEHOLD = 2  # 世帯(合計のみ・個体別には持たない)
    ROW = 3  # 外界(bbox 外)
    WASTE = 4  # 区の収集(bbox 外へ搬出)


class GoodsCode(IntEnum):
    """物の科目(§7.1 の faucet/sink 列挙 + 内部移動 + 残差)。"""

    RESTOCK_FROM_ROW = 0  # faucet: 域外仕入(RoW→店舗)
    CARRY_IN = 1  # faucet: 持込物(RoW→世帯)
    SALE = 2  # internal: 販売(棚→世帯)
    TO_BIN = 3  # internal: 店舗が廃棄ビンへ出す(棚→ビン)
    CONSUME = 4  # sink: 消費(世帯)
    WASTE_OUT = 5  # sink: 廃棄搬出(区の収集→bbox外)
    RETURN_OUT = 6  # sink: 返品/域外出荷
    STOCKTAKE = 7  # 残差: 棚卸差異(閾値超でゲート失敗)


GOODS_CODE_NAMES: Final[tuple[str, ...]] = (
    "域外仕入", "持込物", "販売", "廃棄ビンへ", "消費", "廃棄搬出", "返品/域外出荷", "棚卸差異",
)
assert len(GOODS_CODE_NAMES) == len(GoodsCode)

_SHELF = NodeKind.STORE_SHELF
_BIN = NodeKind.STORE_BIN
_HH = NodeKind.HOUSEHOLD
_ROW = NodeKind.ROW
_WASTE = NodeKind.WASTE

#: 物の faucet/sink 表(**GoodsCode の列挙と 1 対 1**・列挙にない科目の move_goods は実行不能)。
GOODS_FAUCET_SINK: Final[Mapping[GoodsCode, tuple[tuple[NodeKind, NodeKind], ...]]] = {
    GoodsCode.RESTOCK_FROM_ROW: ((_ROW, _SHELF),),
    GoodsCode.CARRY_IN: ((_ROW, _HH),),
    GoodsCode.SALE: ((_SHELF, _HH),),
    GoodsCode.TO_BIN: ((_SHELF, _BIN),),
    GoodsCode.CONSUME: ((_HH, _WASTE),),
    GoodsCode.WASTE_OUT: ((_BIN, _WASTE), (_HH, _WASTE)),
    GoodsCode.RETURN_OUT: ((_SHELF, _ROW),),
    GoodsCode.STOCKTAKE: ((_SHELF, _WASTE), (_ROW, _SHELF)),
}
assert set(GOODS_FAUCET_SINK) == set(GoodsCode), "物の faucet/sink 表は列挙と 1 対 1"


def goods_is_allowed(code: int, src_kind: int, dst_kind: int) -> bool:
    """(科目, 置き場, 置き場)が物の faucet/sink 表にあるか。"""
    try:
        c = GoodsCode(int(code))
        a = NodeKind(int(src_kind))
        b = NodeKind(int(dst_kind))
    except ValueError:
        return False
    return (a, b) in GOODS_FAUCET_SINK[c]


def goods_flow_kind(code: int) -> FlowKind:
    """faucet / sink / internal の判定(§7.1 の列挙をそのまま規則化)。"""
    c = GoodsCode(int(code))
    if c in (GoodsCode.RESTOCK_FROM_ROW, GoodsCode.CARRY_IN):
        return FlowKind.FAUCET
    if c in (GoodsCode.CONSUME, GoodsCode.WASTE_OUT, GoodsCode.RETURN_OUT):
        return FlowKind.SINK
    if c == GoodsCode.STOCKTAKE:
        return FlowKind.MEASURE  # 残差(棚卸差異)
    return FlowKind.INTERNAL


class GoodsRef(tuple):
    """物の参照 = (置き場, 索引)。索引の意味: 店舗=poi_id・世帯/外界/収集=0。"""

    __slots__ = ()

    def __new__(cls, kind: int, index: int = 0) -> "GoodsRef":
        return super().__new__(cls, (int(kind), int(index)))

    @property
    def kind(self) -> int:
        return self[0]

    @property
    def index(self) -> int:
        return self[1]


# ---------------------------------------------------------------- SKU 登録簿
#: カテゴリ番号(``world.assets.hash_free_cat_code`` と同じ 0=コンビニ/1=飲食/2=物販)。
CATEGORY_NAMES: Final[tuple[str, ...]] = ("コンビニ", "飲食", "物販")
#: カテゴリ → (SKU 名, 質量[g], 廃棄率) の並び(**expedient**: 出典なし)。
CATEGORY_SKUS: Final[tuple[tuple[tuple[str, int, float], ...], ...]] = (
    (("弁当", 350, 0.05), ("飲料", 500, 0.01), ("日用品", 200, 0.00)),
    (("定食", 400, 0.08), ("ドリンク", 300, 0.02)),
    (("衣料", 300, 0.00),),
)
#: 業態(価格帯)→ 内生フロア k(§8 H-2 の 3 値)。カテゴリへの写像は expedient。
CATEGORY_K: Final[tuple[float, ...]] = (
    pricing.K_VOLUME,  # コンビニ = ドル箱(原価率 20%)
    pricing.K_AVERAGE,  # 飲食 = 平均(30%)
    pricing.K_PREMIUM,  # 物販 = 高級(35%)
)


@dataclass(frozen=True)
class SkuRegistry:
    """SKU 登録簿(全世界で 1 つ)。

    Attributes:
        name: SKU 名。
        category: 属するカテゴリ番号。
        mass_g: 1 個の質量[g](廃棄 band の換算に使う)。
        waste_rate: 1 日あたりの廃棄率(売れ残り→ビン・expedient)。
        slots: カテゴリ → そのカテゴリの SKU id 列。
    """

    name: tuple[str, ...]
    category: np.ndarray
    mass_g: np.ndarray
    waste_rate: np.ndarray
    slots: tuple[tuple[int, ...], ...]

    @property
    def n_sku(self) -> int:
        return len(self.name)

    @property
    def max_slots(self) -> int:
        return max(len(s) for s in self.slots)

    @classmethod
    def default(cls) -> "SkuRegistry":
        """カテゴリ 3 種 × 1-3 SKU の既定登録簿(expedient)。

        逐次ループ宣言1: カテゴリ数(3)ぶん。
        """
        names: list[str] = []
        cat: list[int] = []
        mass: list[float] = []
        rate: list[float] = []
        slots: list[tuple[int, ...]] = []
        for c, skus in enumerate(CATEGORY_SKUS):
            ids: list[int] = []
            for nm, m, wr in skus:
                ids.append(len(names))
                names.append(f"{CATEGORY_NAMES[c]}/{nm}")
                cat.append(c)
                mass.append(float(m))
                rate.append(float(wr))
            slots.append(tuple(ids))
        return cls(
            name=tuple(names),
            category=np.asarray(cat, dtype=np.int32),
            mass_g=np.asarray(mass, dtype=np.float64),
            waste_rate=np.asarray(rate, dtype=np.float64),
            slots=tuple(slots),
        )


@dataclass(frozen=True)
class WasteBand:
    """廃棄 sink の band 判定(検算②・台帳行 W1)。"""

    days: int
    tonnes: float
    tonnes_per_day: float
    low: float
    high: float

    @property
    def ok(self) -> bool:
        return self.low <= self.tonnes_per_day <= self.high

    def as_text(self) -> str:
        return (
            f"[W1] 廃棄 {self.tonnes:.2f} t / {self.days}日 = {self.tonnes_per_day:.2f} t/日 "
            f"(band {self.low:.1f}-{self.high:.1f} t/日・アンカー {WASTE_TONNES_PER_DAY} t/日) "
            f"{'OK' if self.ok else 'NG'}"
        )


#: 棚卸差異の閾値(その日の流量に対する比・expedient)。
STOCKTAKE_THRESHOLD_RATIO: Final[float] = 0.01
#: 退蔵(売れ残り)と見なす棚滞留日数(expedient)。
HOARD_SHELF_DAYS: Final[int] = 14
#: 納品ログ 1 行のバイト(tick4+poi4+slot1+qty4+kind1 → 16 に切り上げ)。
DELIVERY_ROW_BYTES: Final[int] = 16
DEFAULT_DELIVERY_CAPACITY: Final[int] = 131_072


class GoodsLedger:
    """SKU 別の棚在庫・廃棄ビン・世帯合計・外界(bbox 外)を持つ物の台帳。

    Example:
        >>> g = GoodsLedger.from_pois(np.array([0, 1]), np.array([10, 5]), np.array([300, 800]))
        >>> int(g.aggregate_stock().sum())
        15
        >>> bool(g.sell_many(np.array([0]), tick=0)[0])
        True
        >>> int(g.aggregate_stock().sum())
        14
    """

    def __init__(
        self,
        cat_codes: np.ndarray,
        stock0: np.ndarray,
        unit_cost: np.ndarray,
        *,
        registry: SkuRegistry | None = None,
        delivery_capacity: int = DEFAULT_DELIVERY_CAPACITY,
        retention_days: int = 1,
    ) -> None:
        """
        Args:
            cat_codes: POI ごとのカテゴリ番号(0-2)。
            stock0: POI ごとの初期在庫合計[個]。
            unit_cost: POI ごとの標準原価[円/個](価格 ÷ k)。
            registry: SKU 登録簿(既定 = ``SkuRegistry.default()``)。
            delivery_capacity: 納品ログのリングバッファ容量[行]。
            retention_days: 生ログの保持窓[日](D-R2-6)。
        """
        self.sku = registry if registry is not None else SkuRegistry.default()
        cats = np.clip(np.asarray(cat_codes, dtype=np.int64).ravel(), 0, len(CATEGORY_SKUS) - 1)
        self.n_poi = int(cats.size)
        self.slots = int(self.sku.max_slots)
        self.cat = cats.astype(np.int32)

        # POI × スロット → 大域 SKU id(-1 = 未使用スロット)
        table = np.full((len(CATEGORY_SKUS), self.slots), -1, dtype=np.int32)
        for c, ids in enumerate(self.sku.slots):
            table[c, : len(ids)] = np.asarray(ids, dtype=np.int32)
        self.poi_sku = table[cats]  # (n_poi, slots)
        self._n_slots_used = np.asarray(
            [len(s) for s in self.sku.slots], dtype=np.int64
        )[cats]

        # 在庫の配分(初期在庫を使用スロットへ均等割り・端数は先頭スロット)
        s0 = np.asarray(stock0, dtype=np.int64).ravel()
        if s0.size != self.n_poi:
            raise ValueError(f"stock0 の長さ {s0.size} が POI 数 {self.n_poi} と違う")
        base = s0 // np.maximum(self._n_slots_used, 1)
        shelf = np.zeros((self.n_poi, self.slots), dtype=np.int32)
        valid = self.poi_sku >= 0
        shelf[valid] = np.repeat(base, self.slots).reshape(self.n_poi, self.slots)[valid]
        rest = s0 - shelf.sum(axis=1)
        shelf[:, 0] += rest.astype(np.int32)
        self._shelf = shelf
        self._bin = np.zeros((self.n_poi, self.slots), dtype=np.int32)
        self._shelf_age = np.zeros((self.n_poi, self.slots), dtype=np.int16)
        self._sold_today = np.zeros((self.n_poi, self.slots), dtype=bool)

        n_sku = self.sku.n_sku
        self._household_sku = np.zeros(n_sku, dtype=np.int64)
        self._row_sku = np.zeros(n_sku, dtype=np.int64)  # 負 = bbox へ供給した総量
        self._waste_sku = np.zeros(n_sku, dtype=np.int64)  # bbox 外へ出た総量(累計)
        self._inflow = np.zeros(n_sku, dtype=np.int64)  # 当日の流入(faucet)
        self._outflow = np.zeros(n_sku, dtype=np.int64)  # 当日の流出(sink)
        self._residual = np.zeros(n_sku, dtype=np.int64)  # 当日の棚卸差異
        self._open_stock = self.inside_stock_by_sku()
        self._day_waste_g = 0.0
        self._waste_g_daily: list[float] = []

        self.unit_cost = np.asarray(unit_cost, dtype=np.int64).ravel()
        if self.unit_cost.size != self.n_poi:
            raise ValueError("unit_cost の長さが POI 数と違う")

        # 納品ログ(O(t) → リングバッファ+保持窓・D-R2-6)
        cap = max(1, int(delivery_capacity))
        self._dl_tick = np.zeros(cap, dtype=np.int32)
        self._dl_poi = np.zeros(cap, dtype=np.int32)
        self._dl_slot = np.zeros(cap, dtype=np.int8)
        self._dl_qty = np.zeros(cap, dtype=np.int32)
        self._dl_code = np.zeros(cap, dtype=np.int8)
        self._dl_pos = 0
        self._dl_head = 0
        self._dl_marks: list[tuple[int, int]] = [(0, 0)]
        self.n_delivery_dropped = 0
        self.retention_days = int(retention_days)

        self._day = 0
        self._depth = 0
        self.n_moves = 0
        self.rejections = 0
        self.freeze()

    # ---------------------------------------------------------------- 生成
    @classmethod
    def from_pois(
        cls,
        cat_codes: np.ndarray,
        stock0: np.ndarray,
        price: np.ndarray,
        **kw,
    ) -> "GoodsLedger":
        """POI の(カテゴリ・初期在庫・価格)から作る。原価 = 価格 ÷ k(§8 H-2)。"""
        cats = np.clip(np.asarray(cat_codes, dtype=np.int64).ravel(), 0, len(CATEGORY_K) - 1)
        k = np.asarray(CATEGORY_K, dtype=np.float64)[cats]
        cost = np.maximum(1, np.rint(np.asarray(price, dtype=np.float64).ravel() / k))
        return cls(cats, stock0, cost.astype(np.int64), **kw)

    # ---------------------------------------------------------------- 書き込みガード
    @property
    def frozen(self) -> bool:
        return self._depth == 0

    def freeze(self) -> None:
        """台帳の配列を読み取り専用にする(逐次ループ宣言2)。"""
        for arr in self._guarded():
            arr.flags.writeable = False

    def _guarded(self) -> tuple[np.ndarray, ...]:
        return (
            self._shelf, self._bin, self._shelf_age, self._sold_today,
            self._household_sku, self._row_sku, self._waste_sku,
            self._inflow, self._outflow, self._residual,
        )

    @contextmanager
    def _open(self) -> Iterator["GoodsLedger"]:
        """在庫を書ける窓(再入可)。**呼んでよいのは本ファイルだけ**(AST 検査)。"""
        if self._depth == 0:
            for arr in self._guarded():
                arr.flags.writeable = True
        self._depth += 1
        try:
            yield self
        finally:
            self._depth -= 1
            if self._depth == 0:
                self.freeze()

    @contextmanager
    def unlocked(self) -> Iterator["GoodsLedger"]:
        """外部(resolve)が窓を開けたまま複数回呼ぶための公開版。"""
        with self._open():
            yield self

    # ---------------------------------------------------------------- 参照
    @property
    def shelf(self) -> np.ndarray:
        return self._shelf

    @property
    def bins(self) -> np.ndarray:
        return self._bin

    @property
    def day_waste_g(self) -> float:
        """その日にまだ畳んでいない廃棄搬出の質量[g]。"""
        return self._day_waste_g

    @property
    def day(self) -> int:
        return self._day

    def aggregate_stock(self, stores: np.ndarray | None = None) -> np.ndarray:
        """店舗の棚在庫合計[個](``world.pois.stock`` はこの写し)。"""
        total = self._shelf.sum(axis=1, dtype=np.int64)
        if stores is None:
            return total
        return total[np.asarray(stores, dtype=np.int64)]

    def stock_by_sku(self) -> np.ndarray:
        """棚+ビンの SKU 別在庫 ``(n_sku,)``。"""
        w = np.bincount(
            np.maximum(self.poi_sku.ravel(), 0),
            weights=(self._shelf + self._bin).ravel().astype(np.float64)
            * (self.poi_sku.ravel() >= 0),
            minlength=self.sku.n_sku,
        )
        return np.rint(w).astype(np.int64)

    def inside_stock_by_sku(self) -> np.ndarray:
        """bbox 内の SKU 別在庫(棚+ビン+世帯合計)。検算①の期首/期末。"""
        return self.stock_by_sku() + self._household_sku

    def inventory_value(self) -> np.ndarray:
        """POI ごとの在庫評価額[円](標準原価×棚数量。金の台帳の在庫行へ入れる)。"""
        return self._shelf.sum(axis=1, dtype=np.int64) * self.unit_cost

    def can_sell(self, stores: np.ndarray) -> np.ndarray:
        """店舗ごとに売れる棚があるか。"""
        s = np.asarray(stores, dtype=np.int64)
        return self._shelf[s].sum(axis=1) > 0

    def _first_nonempty_slot(self, stores: np.ndarray) -> np.ndarray:
        """払い出しスロット = **最初の非空スロット**(expedient)。"""
        have = self._shelf[stores] > 0
        return np.argmax(have, axis=1)

    # ---------------------------------------------------------------- 単一API
    def move_goods(
        self,
        src: GoodsRef | Sequence[int],
        dst: GoodsRef | Sequence[int],
        qty: int,
        sku: int,
        code: int,
        tick: int,
    ) -> bool:
        """**単一API**(§7.1)。1件の物の移動。成功したら True。

        店舗側は (POI, スロット) で指す必要があるので、``src``/``dst`` の索引に POI id を、
        ``sku`` に**大域 SKU id** を渡す(スロットは POI×SKU から解決する)。
        """
        sk, si = int(src[0]), int(src[1])
        dk, di = int(dst[0]), int(dst[1])
        if not goods_is_allowed(code, sk, dk) or int(qty) <= 0:
            self.rejections += 1
            return False
        c = GoodsCode(int(code))
        s_slot = self._slot_of(si, sku) if sk in (int(_SHELF), int(_BIN)) else -1
        d_slot = self._slot_of(di, sku) if dk in (int(_SHELF), int(_BIN)) else -1
        if (sk in (int(_SHELF), int(_BIN)) and s_slot < 0) or (
            dk in (int(_SHELF), int(_BIN)) and d_slot < 0
        ):
            self.rejections += 1
            return False
        q = int(qty)
        # 在庫不足の検査(bbox 外=ROW は無制限)
        if sk == int(_SHELF) and int(self._shelf[si, s_slot]) < q:
            self.rejections += 1
            return False
        if sk == int(_BIN) and int(self._bin[si, s_slot]) < q:
            self.rejections += 1
            return False
        if sk == int(_HH) and int(self._household_sku[int(sku)]) < q:
            self.rejections += 1
            return False
        with self._open():
            self._apply_move(sk, si, s_slot, dk, di, d_slot, q, int(sku), c)
            self._log(int(tick), si if sk == int(_SHELF) else di, max(s_slot, d_slot, 0), q, c)
        return True

    def _slot_of(self, poi: int, sku: int) -> int:
        if not (0 <= poi < self.n_poi):
            return -1
        hit = np.flatnonzero(self.poi_sku[poi] == int(sku))
        return int(hit[0]) if hit.size else -1

    def _apply_move(
        self,
        sk: int, si: int, s_slot: int,
        dk: int, di: int, d_slot: int,
        qty: int, sku: int, code: GoodsCode,
    ) -> None:
        """**唯一の在庫書き込み点**。"""
        if sk == int(_SHELF):
            self._shelf[si, s_slot] -= qty
            self._sold_today[si, s_slot] = True
        elif sk == int(_BIN):
            self._bin[si, s_slot] -= qty
        elif sk == int(_HH):
            self._household_sku[sku] -= qty
        elif sk == int(_ROW):
            self._row_sku[sku] -= qty

        if dk == int(_SHELF):
            self._shelf[di, d_slot] += qty
            self._shelf_age[di, d_slot] = 0
        elif dk == int(_BIN):
            self._bin[di, d_slot] += qty
        elif dk == int(_HH):
            self._household_sku[sku] += qty
        elif dk == int(_WASTE):
            self._waste_sku[sku] += qty
            self._day_waste_g += float(self.sku.mass_g[sku]) * qty

        kind = goods_flow_kind(code)
        if kind == FlowKind.FAUCET:
            self._inflow[sku] += qty
        elif kind == FlowKind.SINK:
            self._outflow[sku] += qty
        elif code == GoodsCode.STOCKTAKE:
            self._residual[sku] += qty if dk == int(_SHELF) else -qty
        self.n_moves += 1

    # ---------------------------------------------------------------- ベクトル版の操作
    def sell_many(self, stores: np.ndarray, tick: int) -> np.ndarray:
        """販売(棚→世帯・1 行 1 個)。行ごとの成否 bool。

        同一 POI が複数行に現れる場合は**行順の前置数**で在庫を割り当てる(決定論)。
        """
        s = np.asarray(stores, dtype=np.int64).ravel()
        out = np.zeros(s.size, dtype=bool)
        if s.size == 0:
            return out
        valid = (s >= 0) & (s < self.n_poi)
        slot = np.zeros(s.size, dtype=np.int64)
        slot[valid] = self._first_nonempty_slot(s[valid])
        have = np.zeros(s.size, dtype=np.int64)
        have[valid] = self._shelf[s[valid], slot[valid]].astype(np.int64)
        # 同一(POI, スロット)の重複は**行順の前置数**で消化する(決定論)
        key = s * self.slots + slot
        order = np.argsort(key, kind="stable")
        sorted_key = key[order]
        start = np.searchsorted(sorted_key, sorted_key, side="left")
        rank_sorted = np.arange(key.size, dtype=np.int64) - start
        rank = np.empty_like(rank_sorted)
        rank[order] = rank_sorted
        ok = valid & (have > rank)
        if not ok.any():
            return out
        with self._open():
            np.add.at(self._shelf, (s[ok], slot[ok]), -1)
            self._sold_today[s[ok], slot[ok]] = True
            sku_ids = self.poi_sku[s[ok], slot[ok]].astype(np.int64)
            np.add.at(self._household_sku, sku_ids, 1)
            self.n_moves += int(ok.sum())
            self._log_many(int(tick), s[ok], slot[ok],
                           np.ones(int(ok.sum()), dtype=np.int64), GoodsCode.SALE)
        out[ok] = True
        return out

    def restock_many(
        self,
        stores: np.ndarray,
        qty: np.ndarray,
        tick: int,
        *,
        money=None,
        slot: np.ndarray | None = None,
    ) -> np.ndarray:
        """補充(外界→棚・faucet 域外仕入)。``money`` を渡すと**代金も** transfer する。

        代金 = 標準原価(価格 ÷ k)× 数量 を **店舗 → 外界**(域外仕入 sink)で払う。
        支払えない行は補充しない(不可逆な資源移動はエンジン=線引き原則1)。
        """
        s = np.asarray(stores, dtype=np.int64).ravel()
        q = np.asarray(qty, dtype=np.int64).ravel()
        out = np.zeros(s.size, dtype=bool)
        if s.size == 0:
            return out
        sl = (
            np.zeros(s.size, dtype=np.int64)
            if slot is None
            else np.asarray(slot, dtype=np.int64).ravel()
        )
        ok = (s >= 0) & (s < self.n_poi) & (q > 0) & (sl >= 0) & (sl < self.slots)
        ok &= self.poi_sku[np.clip(s, 0, self.n_poi - 1), np.clip(sl, 0, self.slots - 1)] >= 0
        if money is not None and ok.any():
            cost = self.unit_cost[s] * q
            status = money.transfer_many(
                int(Sector.STORE), s[ok], int(Sector.ROW), np.zeros(int(ok.sum()), dtype=np.int64),
                cost[ok], int(AccountCode.IMPORT_PURCHASE), tick,
            )
            paid = np.zeros(s.size, dtype=bool)
            paid[np.flatnonzero(ok)] = status == 0
            ok = paid
        if not ok.any():
            return out
        with self._open():
            np.add.at(self._shelf, (s[ok], sl[ok]), q[ok].astype(np.int32))
            self._shelf_age[s[ok], sl[ok]] = 0
            sku_ids = self.poi_sku[s[ok], sl[ok]].astype(np.int64)
            np.add.at(self._row_sku, sku_ids, -q[ok])
            np.add.at(self._inflow, sku_ids, q[ok])
            self.n_moves += int(ok.sum())
            self._log_many(int(tick), s[ok], sl[ok], q[ok], GoodsCode.RESTOCK_FROM_ROW)
        out[ok] = True
        return out

    def deliver(self, stores: np.ndarray, qty: np.ndarray, tick: int, *, money=None,
                slot: np.ndarray | None = None) -> np.ndarray:
        """納品(``restock_many`` の別名・納品便として記録する)。

        設計書 §7.2 の「納品(納品ドライバー行動・早朝帯)」のエンジン側。誰が運ぶかは C4-subH。
        """
        return self.restock_many(stores, qty, tick, money=money, slot=slot)

    def to_bin_many(self, stores: np.ndarray, qty: np.ndarray, tick: int,
                    slot: np.ndarray | None = None) -> np.ndarray:
        """売れ残りを廃棄ビンへ(棚→ビン・internal)。"""
        s = np.asarray(stores, dtype=np.int64).ravel()
        q = np.asarray(qty, dtype=np.int64).ravel()
        sl = (
            np.zeros(s.size, dtype=np.int64)
            if slot is None
            else np.asarray(slot, dtype=np.int64).ravel()
        )
        out = np.zeros(s.size, dtype=bool)
        ok = (s >= 0) & (s < self.n_poi) & (q > 0) & (sl >= 0) & (sl < self.slots)
        if ok.any():
            ok &= self._shelf[np.clip(s, 0, self.n_poi - 1), np.clip(sl, 0, self.slots - 1)] >= q
        if not ok.any():
            return out
        with self._open():
            np.add.at(self._shelf, (s[ok], sl[ok]), -q[ok].astype(np.int32))
            np.add.at(self._bin, (s[ok], sl[ok]), q[ok].astype(np.int32))
            self.n_moves += int(ok.sum())
            self._log_many(int(tick), s[ok], sl[ok], q[ok], GoodsCode.TO_BIN)
        out[ok] = True
        return out

    def collect_waste(self, stores: np.ndarray | None, tick: int) -> float:
        """廃棄物収集(ビン→bbox 外・sink)。搬出した質量[g]を返す。

        設計書 §7.2 の「廃棄物収集(清掃員行動+C類排出)」のエンジン側。
        """
        s = (
            np.arange(self.n_poi, dtype=np.int64)
            if stores is None
            else np.asarray(stores, dtype=np.int64).ravel()
        )
        s = s[(s >= 0) & (s < self.n_poi)]
        if s.size == 0:
            return 0.0
        qty = self._bin[s].astype(np.int64)  # (k, slots)
        if int(qty.sum()) == 0:
            return 0.0
        sku_ids = self.poi_sku[s].astype(np.int64)
        flat_ok = (sku_ids >= 0) & (qty > 0)
        ids = sku_ids[flat_ok]
        q = qty[flat_ok]
        with self._open():
            self._bin[s] = 0
            np.add.at(self._waste_sku, ids, q)
            np.add.at(self._outflow, ids, q)
            mass = float((self.sku.mass_g[ids] * q).sum())
            self._day_waste_g += mass
            self.n_moves += int(ids.size)
            rows = np.flatnonzero(flat_ok.ravel())
            self._log_many(
                int(tick),
                np.repeat(s, self.slots)[rows],
                (np.tile(np.arange(self.slots), s.size))[rows],
                q, GoodsCode.WASTE_OUT,
            )
        return mass

    def consume_many(self, sku_ids: np.ndarray, qty: np.ndarray, tick: int) -> np.ndarray:
        """消費(世帯→sink)。世帯側は**合計だけ**を持つ(個体 M1 に載せない)。"""
        ids = np.asarray(sku_ids, dtype=np.int64).ravel()
        q = np.asarray(qty, dtype=np.int64).ravel()
        out = np.zeros(ids.size, dtype=bool)
        ok = (ids >= 0) & (ids < self.sku.n_sku) & (q > 0)
        if ok.any():
            demand = np.bincount(ids[ok], weights=q[ok].astype(np.float64),
                                 minlength=self.sku.n_sku)
            enough = self._household_sku >= np.rint(demand).astype(np.int64)
            ok &= enough[np.clip(ids, 0, self.sku.n_sku - 1)]
        if not ok.any():
            return out
        with self._open():
            np.add.at(self._household_sku, ids[ok], -q[ok])
            np.add.at(self._waste_sku, ids[ok], q[ok])
            np.add.at(self._outflow, ids[ok], q[ok])
            self._day_waste_g += float((self.sku.mass_g[ids[ok]] * q[ok]).sum())
            self.n_moves += int(ok.sum())
        out[ok] = True
        return out

    def stocktake(self, store: int, slot: int, delta: int, tick: int) -> bool:
        """棚卸差異(残差科目)。実棚と帳簿の差を ``STOCKTAKE`` で計上する。"""
        if not (0 <= int(store) < self.n_poi and 0 <= int(slot) < self.slots):
            return False
        sku = int(self.poi_sku[int(store), int(slot)])
        if sku < 0 or int(delta) == 0:
            return False
        d = int(delta)
        with self._open():
            self._shelf[int(store), int(slot)] += d
            self._residual[sku] += d
            self.n_moves += 1
            self._log_many(int(tick), np.array([store]), np.array([slot]),
                           np.array([abs(d)]), GoodsCode.STOCKTAKE)
        return True

    # ---------------------------------------------------------------- 検算
    def sku_balance(self) -> dict[str, np.ndarray]:
        """検算①: 期首 + 流入 − 流出 + 残差 = 期末(SKU 別・O(n_sku) 総和)。"""
        close = self.inside_stock_by_sku()
        expect = self._open_stock + self._inflow - self._outflow + self._residual
        return {
            "open": self._open_stock.copy(),
            "inflow": self._inflow.copy(),
            "outflow": self._outflow.copy(),
            "residual": self._residual.copy(),
            "close": close,
            "diff": close - expect,
        }

    def sku_balanced(self) -> bool:
        """検算①が全 SKU で成立しているか。"""
        return bool((self.sku_balance()["diff"] == 0).all())

    def stocktake_gate(self) -> tuple[bool, float]:
        """棚卸差異が閾値内か(その日の流量比・閾値超でゲート失敗)。"""
        throughput = int(self._inflow.sum() + self._outflow.sum())
        resid = int(np.abs(self._residual).sum())
        ratio = (resid / throughput) if throughput else (0.0 if resid == 0 else 1.0)
        return (ratio <= STOCKTAKE_THRESHOLD_RATIO, ratio)

    def hoard_report(self, days: int = HOARD_SHELF_DAYS) -> dict[str, int]:
        """退蔵項: ``days`` 日以上動いていない棚在庫(売れ残り)。"""
        old = (self._shelf_age >= int(days)) & (self._shelf > 0)
        return {
            "hoard_slots": int(old.sum()),
            "hoard_units": int(self._shelf[old].sum()),
            "hoard_value": int((self._shelf * old).sum(axis=1) @ self.unit_cost),
        }

    def waste_band(self, days: int | None = None) -> WasteBand:
        """検算②: 廃棄 sink の総量を 119.6 t/日の band と突き合わせる(台帳行 W1)。"""
        grams = sum(self._waste_g_daily) + self._day_waste_g
        n = int(days) if days is not None else max(1, len(self._waste_g_daily))
        tonnes = grams / 1_000_000.0
        return WasteBand(
            days=n,
            tonnes=tonnes,
            tonnes_per_day=tonnes / max(1, n),
            low=WASTE_TONNES_PER_DAY * (1.0 - WASTE_BAND_RATIO),
            high=WASTE_TONNES_PER_DAY * (1.0 + WASTE_BAND_RATIO),
        )

    # ---------------------------------------------------------------- 日次
    def on_day_end(self, day: int | None = None) -> dict[str, object]:
        """日次: 検算①を確定し、期首を更新し、棚の滞留日数を進める(逐次ループ宣言3)。"""
        d = self._day if day is None else int(day)
        bal = self.sku_balance()
        gate_ok, ratio = self.stocktake_gate()
        out = {
            "day": d,
            "sku_balanced": bool((bal["diff"] == 0).all()),
            "stocktake_ok": gate_ok,
            "stocktake_ratio": ratio,
            "inflow": int(bal["inflow"].sum()),
            "outflow": int(bal["outflow"].sum()),
            "waste_g": self._day_waste_g,
            "delivery_rows_kept": int(self._dl_pos - self._dl_head),
        }
        with self._open():
            self._shelf_age += 1
            self._shelf_age[self._sold_today] = 0
            self._sold_today[:] = False
            self._inflow[:] = 0
            self._outflow[:] = 0
            self._residual[:] = 0
        self._open_stock = self.inside_stock_by_sku()
        self._waste_g_daily.append(self._day_waste_g)
        self._day_waste_g = 0.0
        self._day = d + 1
        self._dl_marks.append((self._day, self._dl_pos))
        cutoff = self._day - max(0, self.retention_days)
        for marked_day, marked_pos in self._dl_marks:
            if marked_day <= cutoff and marked_pos > self._dl_head:
                self.n_delivery_dropped += int(marked_pos - self._dl_head)
                self._dl_head = marked_pos
        self._dl_marks = [m for m in self._dl_marks if m[0] > cutoff]
        return out

    # ---------------------------------------------------------------- 納品ログ
    def _log(self, tick: int, poi: int, slot: int, qty: int, code: GoodsCode) -> None:
        self._log_many(tick, np.array([poi]), np.array([slot]), np.array([qty]), code)

    def _log_many(
        self, tick: int, poi: np.ndarray, slot: np.ndarray, qty: np.ndarray, code: GoodsCode
    ) -> None:
        k = int(np.asarray(qty).size)
        if k == 0:
            return
        cap = self._dl_tick.size
        pos = self._dl_pos + np.arange(k, dtype=np.int64)
        s = pos % cap
        self._dl_tick[s] = np.int32(tick)
        self._dl_poi[s] = np.asarray(poi, dtype=np.int32)
        self._dl_slot[s] = np.asarray(slot, dtype=np.int8)
        self._dl_qty[s] = np.asarray(qty, dtype=np.int32)
        self._dl_code[s] = np.int8(int(code))
        self._dl_pos += k
        if self._dl_pos - self._dl_head > cap:
            dropped = (self._dl_pos - self._dl_head) - cap
            self._dl_head += dropped
            self.n_delivery_dropped += int(dropped)

    def delivery_rows(self) -> np.ndarray:
        """保持窓内の納品/移動ログ ``(n, 5)``(tick・POI・スロット・数量・科目)。"""
        cap = self._dl_tick.size
        n = int(self._dl_pos - self._dl_head)
        if n <= 0:
            return np.zeros((0, 5), dtype=np.int64)
        s = (self._dl_head + np.arange(n, dtype=np.int64)) % cap
        return np.stack(
            [
                self._dl_tick[s].astype(np.int64),
                self._dl_poi[s].astype(np.int64),
                self._dl_slot[s].astype(np.int64),
                self._dl_qty[s].astype(np.int64),
                self._dl_code[s].astype(np.int64),
            ],
            axis=1,
        )

    # ---------------------------------------------------------------- 監査
    def summary(self) -> str:
        bal = self.sku_balance()
        return (
            f"[goods] POI {self.n_poi:,} × SKU {self.sku.n_sku} / 棚 {int(self._shelf.sum()):,}個 "
            f"ビン {int(self._bin.sum()):,}個 世帯 {int(self._household_sku.sum()):,}個 / "
            f"流入 {int(bal['inflow'].sum()):,} 流出 {int(bal['outflow'].sum()):,} "
            f"検算① {'OK' if (bal['diff'] == 0).all() else 'NG'}"
        )

    def bytes_total(self) -> int:
        own = sum(int(a.nbytes) for a in self._guarded())
        own += int(self.poi_sku.nbytes) + int(self.unit_cost.nbytes)
        own += self._dl_tick.size * DELIVERY_ROW_BYTES
        return own


def growth_declarations(
    *, delivery_capacity: int = DEFAULT_DELIVERY_CAPACITY, retention_days: int = 1, slots: int = 3
) -> Mapping[str, GrowthDeclaration]:
    """物の台帳の状態成長宣言(D-R2-6 の 5 欄)。

    §7.2「O(t)ログ(納品・配達・収集・出動)は状態成長宣言を**型レベルで強制**」への対応。
    """
    rows = (
        GrowthDeclaration(
            name="delivery_log",
            per_agent_bytes=0,
            per_cell_bytes=0,
            per_day_growth="O(N)",
            per_day_growth_coef=float(2.0 * DELIVERY_ROW_BYTES),
            retention=Retention(days=retention_days, target="日次の SKU 別収支行(sku_balance)へ集約"),
            worst_case_ops_per_tick=0,
            cap=int(delivery_capacity) * DELIVERY_ROW_BYTES,
            cap_budget_row="S1(親が割当・要 delta)",
            mechanism=True,
            note=(
                "世界過程設計書 §7.2 の納品・収集ログ(ActualLog と同型の O(t))。"
                "リングバッファ+保持窓 N 日+日次集約で有界化する。"
            ),
            unit="move",
            bytes_per_unit=DELIVERY_ROW_BYTES,
            growth_per_simday=2.0,
        ),
        GrowthDeclaration(
            name="shelf_stock",
            per_agent_bytes=0,
            per_cell_bytes=int(slots) * (4 + 4 + 2 + 1) + 4,  # 棚+ビン+滞留日数+売れたか+SKU表
            per_day_growth="O(1)",
            per_day_growth_coef=0.0,
            retention=Retention(days=None),
            worst_case_ops_per_tick=0,
            cap=64_000_000,
            cap_budget_row="M8(親が割当・要 delta)",
            mechanism=True,
            note=(
                "SKU 別在庫は**店舗 POI 側**(per_cell_bytes)に置き個体 M1 には載せない"
                "(設計書 §7.1)。日をまたいで伸びない。"
            ),
            unit="poi",
            bytes_per_unit=int(slots) * 11,
        ),
    )
    return {d.name: d for d in rows}
