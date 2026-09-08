"""engine.processes.goods_flow — 物の流れ(§7.2 初回実装の後半 + 前倒し 1 本)。

担当する台帳行(``world.processes.first_batch``)
- ``shelf_stock_restock``(第1陣・``executor=llm_agent``・``AB-SHELF-REORDER``)
  = **店員 T0 行動**「補充」(行動契約書 §2.2「補充 | 従業者(権限) | 在庫置場>0・営業中 |
  棚在庫+ | **バックヤードに在庫なし** | mechanism」)。
- ``delivery_inbound``(第1陣・``executor=llm_agent``・``AB-DELIVERY-FREQ``)
  = **納品ドライバー行動**(早朝帯)。
- ``waste_collection``(第1陣・``executor=llm_agent``・``AB-WASTE-ROUTE``)
  = **清掃員行動 + C 類排出**。検算②(廃棄 sink の t/日 band)の駆動源。
- ``street_cleaning``(前倒し・``executor=llm_agent``・``AB-CLEANING-RATE``)= 街路清掃。

**バックヤードの表し方(expedient・設計書との食い違いを黙って埋めない)**
    §7.2 は「納品(外界→**在庫置場**)」と「補充(在庫置場→棚)」を分ける。ところが物の台帳
    (``economy.goods``)の節点は **棚 / 廃棄ビン / 世帯 / 外界 / 廃棄** の5つで、
    **在庫置場(バックヤード)の節点が無い**。economy は本サブの読み取り専用領域なので節点を
    増やさず、次の形にした:

      納品 = 早朝帯にドライバーが着けた**未陳列の納品枠**(``backroom``)が積まれる(物は動かない)
      補充 = 店員がその枠を消費して ``restock_many(外界→棚)`` を起こす(**ここで代金を払う**)

    物の保存則(検算①)は「棚+ビン+世帯 = 期首+流入−流出」で閉じたまま(枠は物ではない)。
    **親指示との差分(黙って埋めない)**: 親は「納品時に域外仕入で払う」としたが、金の台帳の
    Protocol(``engine.ledger_api.MoneyLedger``)には店舗→外界の域外仕入を**単独で**立てる口が
    無く、``GoodsLedger.restock_many(money=…)`` の中にしか無い(economy は本サブの読み取り専用
    領域)。よって支払いは**棚入れの瞬間**(検収時払い)になる。物と金の対応は保たれる。
    **返済**: 台帳に在庫置場の節点と単独の域外仕入口を足したら、着荷時払いへ戻す(Phase 3)。

expedient(本モジュール分・全て「返済対象」)
- 補充点 = 棚容量の 80%・補充ロット = 満杯までの差(「棚は常に満杯を目指す」小売の実務形)。
  設計書 §7.2 の expedient 欄「SKU粒度・棚卸閾値・初期在庫・**補充閾値/ロット**」そのもの。
- 補充の評価間隔 5 分(正規化規約⑨と同じ刻み)。
- 納品の時間帯 **05:00-08:00**(親指示の窓)・1 店 1 日 1 便・ロット = 補充ロット × 2。
- 納品の遅延 = 15% の便が 1-30 分(幾何分布・平均 ≈ 6 分)。実データは空欄。
- 収集の時間帯 **06:00-10:00**・セル順のルート・1 tick 1 セル分の店舗を回る。
- 売れ残り → ビン: 1 日 1 回(閉店帯)に SKU 別 ``waste_rate`` を棚へ掛ける。
- 世帯の消費(C 類排出): 1 日 1 回、所持のある個体が 1 個消費する(``resolve.consume``)。
- 街路ごみ: 1 人 1 tick あたり ``LITTER_G_PER_PERSON_TICK`` [g]。**SKU を持たない**ので
  物の台帳(SKU 別)へは載せず、質量だけを本過程が持つ(band の内訳としては別に足す)。
"""

from __future__ import annotations

from typing import Final

import numpy as np

from shibuya.agents.state import AgentKind, AgentState
from shibuya.core.rng import stream
from shibuya.engine import resolve as R
from shibuya.world.processes.records import DEVIATION_CODES, DeviationVocab
from shibuya.world.state import World

__all__ = [
    "REORDER_FILL_RATIO",
    "RESTOCK_STEP_MINUTES",
    "RESTOCK_FALLBACK_MINUTE",
    "DELIVERY_WINDOW",
    "DELIVERY_LOT_FACTOR",
    "DELIVERY_DELAY_SHARE",
    "COLLECT_WINDOW",
    "WASTE_TO_BIN_MINUTE",
    "HOUSEHOLD_CONSUME_MINUTE",
    "LITTER_G_PER_PERSON_TICK",
    "CLEANING_WINDOWS",
    "ShelfRestockProcess",
    "DeliveryInboundProcess",
    "WasteCollectionProcess",
    "StreetCleaningProcess",
]

_SCHEDULED: Final[int] = DEVIATION_CODES[DeviationVocab.SCHEDULED]
_REPLACEMENT: Final[int] = DEVIATION_CODES[DeviationVocab.REPLACEMENT]
_SKIPPED: Final[int] = DEVIATION_CODES[DeviationVocab.SKIPPED]
_DELAY: Final[int] = DEVIATION_CODES[DeviationVocab.DELAY]

MINUTES_PER_DAY: Final[int] = 1_440

#: 補充点 = 棚容量のこの割合を割ったら補充する(expedient)。
#: 小売の実務は「棚は満杯を目指す」(発注点は満杯の直下)なので 0.95 を置く。
#: **感度が高い**: 0.80 にすると 5,000 体・1 日では補充が 1 件も立たない
#: (5,000 体 = 実渋谷の昼間人口の約 1%=購買による棚の減りが小さすぎる)。``AB-SHELF-REORDER``。
REORDER_FILL_RATIO: Final[float] = 0.95
#: 補充を評価する刻み[分](expedient・正規化規約⑨と同じ)。
RESTOCK_STEP_MINUTES: Final[int] = 5
#: engine_rule フォールバックを回す時刻[分](10:00・expedient)。
#: 行動契約書 §2.2 の補充は前提に「**営業中**」を含むので、開店前(05:00)に置くと
#: ``open_mask`` で全件落ちて 1 件も動かない。既定の開店時刻に合わせた。
RESTOCK_FALLBACK_MINUTE: Final[int] = 10 * 60
#: フォールバックの conf(台帳の ``shelf_stock_restock`` は executor=llm_agent で conf 欄が空。
#: 「担い手が居ないときエンジンが代打する」行が台帳に無い=**設計の欠落として親へ報告**。
#: 値は ``store_opening`` の 0.5 に揃えた=expedient)。
RESTOCK_FALLBACK_CONF: Final[float] = 0.5

#: 納品の時間帯[分](05:00-08:00・expedient)。
DELIVERY_WINDOW: Final[tuple[int, int]] = (5 * 60, 8 * 60)
#: 納品ロット = 補充ロットの何倍か(expedient)。
DELIVERY_LOT_FACTOR: Final[int] = 2
#: 遅延する便の割合(expedient)。
DELIVERY_DELAY_SHARE: Final[float] = 0.15
#: 遅延[分]の幾何分布のパラメータ(平均 ≈ 1/p 分・expedient)。
DELIVERY_DELAY_P: Final[float] = 1.0 / 6.0
DELIVERY_DELAY_MAX_MIN: Final[int] = 30

#: 廃棄物収集の時間帯[分](06:00-10:00・expedient)。
COLLECT_WINDOW: Final[tuple[int, int]] = (6 * 60, 10 * 60)
#: 売れ残りをビンへ落とす時刻[分](05:00・expedient)。
#: 収集の窓(06:00-10:00)より**前**に置く——実務でも廃棄は朝の収集便に合わせて出す。
#: 23:00(閉店時)に置くと 1 日ランでは翌朝まで回収されず、検算②の当日 sink が常に 0 になる。
WASTE_TO_BIN_MINUTE: Final[int] = 5 * 60
#: 世帯が所持を消費する時刻[分](19:00・expedient)。
HOUSEHOLD_CONSUME_MINUTE: Final[int] = 19 * 60

#: 街路ごみの発生[g/人/tick](expedient・原単位は空欄)。
LITTER_G_PER_PERSON_TICK: Final[float] = 0.05
#: 街路清掃のシフト[分](早朝と昼過ぎ・expedient)。
CLEANING_WINDOWS: Final[tuple[tuple[int, int], ...]] = ((5 * 60, 7 * 60), (13 * 60, 15 * 60))
#: 1 tick に掃くセル数(expedient)。
CELLS_PER_SWEEP_TICK: Final[int] = 8


def _minute(tick: int, tick_seconds: int) -> int:
    return int(int(tick) * int(tick_seconds) // 60) % MINUTES_PER_DAY


def _best_slot(shelf: np.ndarray, poi_sku: np.ndarray, stores: np.ndarray) -> np.ndarray:
    """補充先スロット = **その店で一番減っている有効スロット**(決定論・同数は小さい索引)。"""
    s = np.asarray(stores, dtype=np.int64)
    if s.size == 0:
        return np.zeros(0, dtype=np.int64)
    qty = np.asarray(shelf[s], dtype=np.float64)
    valid = np.asarray(poi_sku[s]) >= 0
    qty = np.where(valid, qty, np.inf)
    return np.argmin(qty, axis=1).astype(np.int64)


class ShelfRestockProcess:
    """店舗補充・棚在庫(**店員 T0 行動** + conf 宣言つき engine_rule フォールバック)。

    Attributes:
        backroom: ``(n_poi,)`` 未陳列の納品枠[個](``DeliveryInboundProcess`` が積む)。
        capacity: ``(n_poi,)`` 棚容量[個](初期在庫を容量とみなす=expedient)。
        n_role_actions / n_fallback / n_no_backroom: 診断。
    """

    process_ids: Final[tuple[str, ...]] = ("shelf_stock_restock",)
    ablation_id: Final[str] = "AB-SHELF-REORDER"

    def __init__(
        self,
        world: World,
        agents: AgentState,
        *,
        ledger=None,
        staff_of_poi: np.ndarray | None = None,
        tick_seconds: int = 60,
        actual_log=None,
        fill_ratio: float = REORDER_FILL_RATIO,
    ) -> None:
        self.world = world
        self.agents = agents
        self.ledger = ledger
        self.tick_seconds = int(tick_seconds)
        self.log = actual_log
        self.fill_ratio = float(fill_ratio)
        n = world.n_poi
        self.capacity = np.asarray(world.pois.stock, dtype=np.int64).copy()
        self.reorder_point = np.maximum(1, np.floor(self.capacity * self.fill_ratio)).astype(
            np.int64
        )
        self.backroom = np.zeros(n, dtype=np.int64)
        self.staff_of_poi = (
            np.full(n, -1, dtype=np.int64) if staff_of_poi is None
            else np.asarray(staff_of_poi, dtype=np.int64)
        )
        self.n_role_actions = 0
        self.n_fallback = 0
        self.n_no_backroom = 0
        self.n_rejected = 0
        self.units_restocked = 0
        self.yen_paid = 0
        self._acted_today = np.zeros(n, dtype=bool)

    @property
    def active(self) -> bool:
        return self.ledger is not None and self.ledger.goods is not None and self.world.n_poi > 0

    # ------------------------------------------------------------------ 権限(行動契約書 §2.2)
    def has_permission(self, agent_ids, poi_ids) -> np.ndarray:
        """「従業者」かつ「その POI の担当」かつ「同一セル」かつ「営業中」。

        **step から呼ばれる**(層2レビュー指摘の固定: 以前は step が同じ条件を手書きで
        再実装していて本メソッドはテストからしか呼ばれない死んだ枝だった)。``step`` は
        営業中の店 (``open_mask``) に絞ってからここへ入るので、残りの3条件を見る。

        Note:
            LLM の役割語「補充」を直接ここへ流す配線は**まだ無い**。``llm.contract`` の
            ROLE_ACTION_WORDS は ``engine.llm_bridge`` が「待機+権限検査待ち」へ落とすので
            (``ROLE_ACTION_CODES`` の注記)、役割語が intent になるところまで届いていない。
            配線には llm_bridge / commit の改修が要る=**本サブの範囲外**(親へ申し送り)。
            それまでは担い手の在店(=この権限検査)を起点に engine_rule として補充する。
        """
        a = np.asarray(agent_ids, dtype=np.int64).ravel()
        p = np.asarray(poi_ids, dtype=np.int64).ravel()
        out = np.zeros(a.shape, dtype=bool)
        ok = (a >= 0) & (a < self.agents.n) & (p >= 0) & (p < self.world.n_poi)
        if not ok.any():
            return out
        kind = self.agents.registry.field("kind")[a[ok]] == int(AgentKind.WORKER)
        mine = self.staff_of_poi[p[ok]] == a[ok]
        same = self.agents.registry.cell[a[ok]] == self.world.pois.cell[p[ok]]
        out[ok] = kind & mine & same
        return out

    # ------------------------------------------------------------------ 1 tick
    def step(self, tick: int) -> None:
        if not self.active:
            return
        minute = _minute(tick, self.tick_seconds)
        if minute == 0:
            self._acted_today[:] = False
        fallback_now = minute == RESTOCK_FALLBACK_MINUTE
        if minute % RESTOCK_STEP_MINUTES and not fallback_now:
            return
        goods = self.ledger.goods
        stock = goods.aggregate_stock()
        open_mask = self.world.open_mask(tick)
        low = np.flatnonzero((stock < self.reorder_point) & open_mask)
        if low.size == 0:
            return

        # 権限検査(行動契約書 §2.2)は **1 か所** = ``has_permission``。
        # ``low`` は既に ``open_mask`` で営業中に絞ってある。
        present = self.has_permission(self.staff_of_poi[low], low)
        # フォールバック時刻には「今日まだ担い手が動いていない店」をエンジンが代打する
        engine_rows = (~present) & (~self._acted_today[low]) if fallback_now else np.zeros(
            low.size, dtype=bool
        )
        act = present | engine_rows
        rows = low[act]
        if rows.size == 0:
            return

        want = np.maximum(0, self.capacity[rows] - stock[rows])
        qty = np.minimum(want, self.backroom[rows])
        empty = qty <= 0
        if empty.any():
            # 行動契約書 §2.2 の失敗語彙「**バックヤードに在庫なし**」
            self.n_no_backroom += int(empty.sum())
            if self.log is not None:
                self.log.append_many(
                    self.process_ids[0], rows[empty],
                    np.full(int(empty.sum()), int(tick), dtype=np.int64),
                    np.full(int(empty.sum()), _SKIPPED, dtype=np.int8),
                )
        live = ~empty
        if not live.any():
            return
        stores = rows[live]
        q = qty[live]
        slot = _best_slot(goods.shelf, goods.poi_sku, stores)
        cost = np.asarray(goods.unit_cost, dtype=np.int64)[stores] * q
        ok = np.asarray(
            R.restock(self.world, self.ledger, stores, q, int(tick), slot=slot), dtype=bool
        )
        self.n_rejected += int((~ok).sum())  # 店舗の現金不足(域外仕入が払えない)
        if ok.any():
            self.yen_paid += int(cost[ok].sum())
            done = stores[ok]
            self.backroom[done] -= q[ok]
            self.units_restocked += int(q[ok].sum())
            self._acted_today[done] = True
            by_staff = present[act][live][ok]
            self.n_role_actions += int(np.count_nonzero(by_staff))
            self.n_fallback += int(np.count_nonzero(~by_staff))
            if self.log is not None:
                self.log.append_many(
                    self.process_ids[0], done,
                    np.full(done.size, int(tick), dtype=np.int64),
                    np.where(by_staff, _SCHEDULED, _REPLACEMENT).astype(np.int8),
                )

    # ------------------------------------------------------------------ 診断
    def counters(self) -> dict[str, float]:
        return {
            "role_actions": float(self.n_role_actions),
            "fallback": float(self.n_fallback),
            "no_backroom": float(self.n_no_backroom),
            "rejected": float(self.n_rejected),
            "units": float(self.units_restocked),
            "yen": float(self.yen_paid),
            "backroom_now": float(int(self.backroom.sum())),
        }

    def summary(self) -> str:
        if not self.active:
            return "店舗補充: 物の台帳が無い(休む)"
        return (
            f"店舗補充: 役割行動 {self.n_role_actions:,} / フォールバック {self.n_fallback:,} "
            f"(conf {RESTOCK_FALLBACK_CONF}) / バックヤード切れ {self.n_no_backroom:,} / "
            f"資金不足 {self.n_rejected:,} / 補充 {self.units_restocked:,} 個 "
            f"域外仕入 {self.yen_paid:,} 円 (残枠 {int(self.backroom.sum()):,})"
        )


class DeliveryInboundProcess:
    """納品(早朝帯・**納品ドライバー行動**)。未陳列の納品枠(バックヤード)を積む。

    ``executor`` は台帳では ``llm_agent``。C4 ではドライバー個体を立てないので、
    実行主体は**エンジン規則の代打**(ActualLog は ``REPLACEMENT``)として記録し、
    遵守率がそのまま「層2で回せていない割合」になるようにする。
    """

    process_ids: Final[tuple[str, ...]] = ("delivery_inbound",)
    ablation_id: Final[str] = "AB-DELIVERY-FREQ"
    plan_spec_id: Final[str] = ""

    def __init__(
        self,
        world: World,
        *,
        ledger=None,
        shelf: ShelfRestockProcess | None = None,
        master_seed: int | str = 1,
        day_index: int = 0,
        tick_seconds: int = 60,
        actual_log=None,
    ) -> None:
        self.world = world
        self.ledger = ledger
        self.shelf = shelf
        self.tick_seconds = int(tick_seconds)
        self.log = actual_log
        self.day_index = int(day_index)
        n = world.n_poi
        g = stream(master_seed, "world.delivery_inbound", int(day_index))
        lo, hi = DELIVERY_WINDOW
        self.plan_minute = (
            g.integers(lo, hi, size=n).astype(np.int64) if n else np.zeros(0, np.int64)
        )
        delayed = g.random(n) < DELIVERY_DELAY_SHARE if n else np.zeros(0, bool)
        draw = np.minimum(
            g.geometric(DELIVERY_DELAY_P, size=n) if n else np.zeros(0, np.int64),
            DELIVERY_DELAY_MAX_MIN,
        )
        self.delay_minute = np.where(delayed, draw, 0).astype(np.int64)
        self.n_runs = 0
        self.n_delayed = 0
        self.units_delivered = 0

    @property
    def active(self) -> bool:
        return self.shelf is not None and self.world.n_poi > 0

    def step(self, tick: int) -> None:
        if not self.active:
            return
        minute = _minute(tick, self.tick_seconds)
        due = np.flatnonzero((self.plan_minute + self.delay_minute) == minute)
        if due.size == 0:
            return
        cap = self.shelf.capacity[due]
        lot = np.maximum(
            1, (cap * (1.0 - REORDER_FILL_RATIO)).astype(np.int64)
        ) * DELIVERY_LOT_FACTOR
        self.shelf.backroom[due] += lot
        self.n_runs += int(due.size)
        self.units_delivered += int(lot.sum())
        if self.log is not None:
            delay = self.delay_minute[due]
            codes = np.where(delay > 0, _DELAY, _REPLACEMENT).astype(np.int8)
            delays = np.where(codes == _DELAY, delay, 0).astype(np.int16)
            self.n_delayed += int(np.count_nonzero(codes == _DELAY))
            self.log.append_many(
                self.process_ids[0], due,
                np.full(due.size, int(tick), dtype=np.int64), codes, delays,
            )

    def counters(self) -> dict[str, float]:
        return {
            "runs": float(self.n_runs),
            "delayed": float(self.n_delayed),
            "units": float(self.units_delivered),
        }

    def summary(self) -> str:
        if not self.active:
            return "納品: 補充過程が無い(休む)"
        return (
            f"納品: 便 {self.n_runs:,}(遅延 {self.n_delayed:,}) / 入荷枠 "
            f"{self.units_delivered:,} 個 "
            f"(窓 {DELIVERY_WINDOW[0] // 60:02d}:00-{DELIVERY_WINDOW[1] // 60:02d}:00=expedient)"
        )


class WasteCollectionProcess:
    """廃棄物収集(店舗ビン → bbox 外)+ C 類排出(売れ残り・世帯消費)。

    Attributes:
        route: セル順の収集ルート(``(n_cells,)`` セル索引)。
        waste_g_collected: 搬出した質量[g]の累計。
    """

    process_ids: Final[tuple[str, ...]] = ("waste_collection",)
    ablation_id: Final[str] = "AB-WASTE-ROUTE"

    def __init__(
        self,
        world: World,
        agents: AgentState,
        *,
        ledger=None,
        tick_seconds: int = 60,
        actual_log=None,
        master_seed: int | str = 1,
    ) -> None:
        self.world = world
        self.agents = agents
        self.ledger = ledger
        self.tick_seconds = int(tick_seconds)
        self.log = actual_log
        self.master_seed = master_seed
        self.route = np.argsort(
            np.asarray(world.pois.cell, dtype=np.int64), kind="stable"
        ).astype(np.int64)
        self.waste_g_collected = 0.0
        self.n_stops = 0
        self.n_bin_rows = 0
        self.n_consumed = 0
        self._cursor = 0

    @property
    def active(self) -> bool:
        return self.ledger is not None and self.ledger.goods is not None

    def step(self, tick: int) -> None:
        if not self.active:
            return
        minute = _minute(tick, self.tick_seconds)
        if minute == WASTE_TO_BIN_MINUTE:
            self._sell_leftovers_to_bin(int(tick))
        if minute == HOUSEHOLD_CONSUME_MINUTE:
            self._household_consumption(int(tick))
        lo, hi = COLLECT_WINDOW
        if minute == lo:
            self._cursor = 0
        if lo <= minute < hi:
            self._collect_batch(int(tick), minute - lo, hi - lo)

    # ---- C 類排出: 売れ残り → ビン ----
    def _sell_leftovers_to_bin(self, tick: int) -> None:
        goods = self.ledger.goods
        shelf = np.asarray(goods.shelf, dtype=np.int64)
        if shelf.size == 0:
            return
        rate = np.asarray(goods.sku.waste_rate, dtype=np.float64)
        sku = np.asarray(goods.poi_sku, dtype=np.int64)
        per = np.where(sku >= 0, rate[np.maximum(sku, 0)], 0.0)
        qty = np.floor(shelf * per).astype(np.int64)
        rows, cols = np.nonzero(qty > 0)
        if rows.size == 0:
            return
        ok = R.discard_to_bin(
            self.world, self.ledger, rows, qty[rows, cols], tick, slot=cols
        )
        self.n_bin_rows += int(np.count_nonzero(np.asarray(ok)))

    # ---- C 類排出: 世帯の消費(所持 → sink) ----
    def _household_consumption(self, tick: int) -> None:
        goods = self.ledger.goods
        holders = np.flatnonzero(np.asarray(self.agents.registry.holdings) > 0)
        if holders.size == 0:
            return
        # SKU は「世帯合計」しか無い(§7.1「個体 M1 に載せない」)ので、在庫のある SKU へ
        # 決定論で割り当てる(expedient)。
        have = np.asarray(goods.inside_stock_by_sku(), dtype=np.int64) - np.asarray(
            goods.stock_by_sku(), dtype=np.int64
        )
        live = np.flatnonzero(have > 0)
        if live.size == 0:
            return
        sku = live[np.arange(holders.size) % live.size]
        ok = R.consume(
            self.agents, self.ledger, holders, sku,
            np.ones(holders.size, dtype=np.int64), tick,
        )
        self.n_consumed += int(np.count_nonzero(np.asarray(ok)))

    # ---- 収集ルート ----
    def _collect_batch(self, tick: int, step: int, span: int) -> None:
        n = self.route.size
        if n == 0:
            return
        per = max(1, int(np.ceil(n / max(1, span))))
        lo = min(n, self._cursor)
        hi = min(n, lo + per)
        if hi <= lo:
            return
        stores = self.route[lo:hi]
        self._cursor = hi
        grams = float(R.collect_waste(self.world, self.ledger, stores, tick))
        if grams <= 0.0:
            return
        self.waste_g_collected += grams
        self.n_stops += 1
        if self.log is not None:
            self.log.append_many(
                self.process_ids[0], np.array([int(stores[0])], dtype=np.int64),
                np.array([int(tick)], dtype=np.int64),
                np.array([_REPLACEMENT], dtype=np.int8),
            )

    # ---- 検算②(W1 band) ----
    def projected_tonnes_per_day(self, extra_g: float = 0.0) -> float:
        """その日の廃棄 sink[t/日](物の台帳の総量 + 街路清掃ぶん)。

        月次 band(W1・119.6 t/日 ±30%)を **1 日ランの射影値**として評価するための欄。
        ``GoodsLedger.waste_band`` 側の総量を使うので、日次の畳み込み
        (``on_day_end`` が ``day_waste_g`` を 0 に戻す)の前後どちらでも同じ値になる。
        """
        if not self.active:
            return 0.0
        return float(self.ledger.goods.waste_band(days=1).tonnes) + float(extra_g) / 1_000_000.0

    def counters(self) -> dict[str, float]:
        return {
            "stops": float(self.n_stops),
            "collected_g": float(self.waste_g_collected),
            "to_bin_rows": float(self.n_bin_rows),
            "consumed": float(self.n_consumed),
            "day_waste_g": float(self.ledger.goods.day_waste_g) if self.active else 0.0,
        }

    def summary(self) -> str:
        if not self.active:
            return "廃棄物収集: 物の台帳が無い(休む)"
        return (
            f"廃棄物収集: 停車 {self.n_stops:,} / 搬出 {self.waste_g_collected / 1e6:.3f} t / "
            f"ビン投入 {self.n_bin_rows:,} 行 / 世帯消費 {self.n_consumed:,} / "
            f"当日 sink {self.projected_tonnes_per_day():.3f} t"
        )


class StreetCleaningProcess:
    """街路清掃(セル別のごみストックが密度で増え、シフトで掃かれる)。

    Note:
        B4 に清掃の行はまだ無い(知覚契約書 §3 のチャネル表に「街路のごみ」の行が無い)ので
        **描画には出さない**(親指示どおり)。回収質量は W1 band の内訳として別に足す。
    """

    process_ids: Final[tuple[str, ...]] = ("street_cleaning",)
    ablation_id: Final[str] = "AB-CLEANING-RATE"

    def __init__(self, world: World, agents: AgentState, *, tick_seconds: int = 60) -> None:
        self.world = world
        self.agents = agents
        self.tick_seconds = int(tick_seconds)
        self.litter_g = np.zeros(world.n_cells, dtype=np.float64)
        self.swept_g = 0.0
        self.n_swept_cells = 0
        self._cursor = 0

    @property
    def active(self) -> bool:
        return self.world.n_cells > 0

    def step(self, tick: int) -> None:
        if not self.active:
            return
        self.litter_g += (
            np.asarray(self.world.cells.density, dtype=np.float64) * LITTER_G_PER_PERSON_TICK
        )
        minute = _minute(tick, self.tick_seconds)
        if not any(lo <= minute < hi for lo, hi in CLEANING_WINDOWS):
            return
        n = self.world.n_cells
        idx = (self._cursor + np.arange(CELLS_PER_SWEEP_TICK)) % n
        self._cursor = int((self._cursor + CELLS_PER_SWEEP_TICK) % n)
        self.swept_g += float(self.litter_g[idx].sum())
        self.n_swept_cells += int(idx.size)
        self.litter_g[idx] = 0.0

    def counters(self) -> dict[str, float]:
        return {
            "litter_now_g": float(self.litter_g.sum()),
            "swept_g": float(self.swept_g),
            "swept_cells": float(self.n_swept_cells),
        }

    def summary(self) -> str:
        return (
            f"街路清掃: 回収 {self.swept_g / 1e6:.4f} t / 掃いたセル延べ "
            f"{self.n_swept_cells:,} / 残 {self.litter_g.sum() / 1e3:.1f} kg"
        )
