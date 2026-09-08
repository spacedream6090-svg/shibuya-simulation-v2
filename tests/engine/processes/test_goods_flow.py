"""物の流れ(補充・納品・廃棄物収集・街路清掃)のテスト。

正典: 世界過程設計書 §7.1/§7.2(U-Goods 初回実装)・行動契約書 §2.2(補充の権限と失敗語彙)・
境界・経済設計書 §2.3(検算②)・§2.4(日次ゲート)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import AgentKind
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import Ledger
from shibuya.engine import resolve as R
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.processes.goods_flow import (
    CLEANING_WINDOWS,
    COLLECT_WINDOW,
    DELIVERY_WINDOW,
    HOUSEHOLD_CONSUME_MINUTE,
    REORDER_FILL_RATIO,
    RESTOCK_FALLBACK_MINUTE,
    WASTE_TO_BIN_MINUTE,
    DeliveryInboundProcess,
    ShelfRestockProcess,
    StreetCleaningProcess,
    WasteCollectionProcess,
)

from .conftest import make_agents, make_world


def _bundle(world, n_agents: int, *, store_cash: int = 1_000_000) -> LedgerBundle:
    led = Ledger(n_agents, world.n_poi)
    cats = np.arange(world.n_poi) % 3
    goods = GoodsLedger.from_pois(
        cats, np.asarray(world.pois.stock), np.asarray(world.pois.price)
    )
    if store_cash:
        led.endow_stores(np.full(world.n_poi, store_cash, dtype=np.int64), tick=0)
    return LedgerBundle(money=led, goods=goods)


def _setup(n_agents: int = 20, n_cells: int = 9, **kw):
    world = make_world(n_cells)
    agents, schedule = make_agents(world, n_agents)
    bundle = _bundle(world, n_agents, **kw)
    return world, agents, bundle


def _deplete(world, bundle, store: int, keep: int = 2) -> None:
    """棚を ``keep`` 個だけ残して廃棄ビンへ落とす(補充点を確実に割らせる)。"""
    shelf = np.asarray(bundle.goods.shelf[store], dtype=np.int64)
    for slot in range(shelf.size):  # スロット数(3)ぶん
        qty = int(shelf[slot]) - (keep if slot == 0 else 0)
        if qty > 0:
            R.discard_to_bin(
                world, bundle, np.array([store]), np.array([qty]), tick=0,
                slot=np.array([slot]),
            )


def _staffed(world, agents):
    """POI → 担当従業者(``OpeningProcess`` と同じ丸振り)。"""
    from shibuya.engine.processes.opening import OpeningProcess

    from shibuya.world.assets import ProcessAssets

    return OpeningProcess(world, agents, ProcessAssets.synthetic()).staff_of_poi


# ================================================================= 補充(店員 T0 行動)
def test_restock_needs_backroom_stock():
    """行動契約書 §2.2 の失敗語彙「バックヤードに在庫なし」が立つ。"""
    world, agents, bundle = _setup()
    shelf = ShelfRestockProcess(world, agents, ledger=bundle)
    R.set_open_flags(world, np.ones(world.n_poi, dtype=np.int8))
    # 棚を減らして補充点を割らせる(バックヤードは空のまま)
    _deplete(world, bundle, 0)
    shelf.step(RESTOCK_FALLBACK_MINUTE)
    assert shelf.n_no_backroom > 0
    assert shelf.units_restocked == 0


def test_restock_moves_goods_and_pays_the_import_leg():
    world, agents, bundle = _setup()
    shelf = ShelfRestockProcess(world, agents, ledger=bundle)
    R.set_open_flags(world, np.ones(world.n_poi, dtype=np.int8))
    _deplete(world, bundle, 0)
    shelf.backroom[0] = 100
    before = int(bundle.goods.aggregate_stock()[0])
    cash0 = int(bundle.money.balance(BalanceLine.CASH, Sector.STORE)[0])
    shelf.step(RESTOCK_FALLBACK_MINUTE)
    after = int(bundle.goods.aggregate_stock()[0])
    assert after > before
    assert int(world.pois.stock[0]) == after  # 写しが同期している
    assert int(bundle.money.balance(BalanceLine.CASH, Sector.STORE)[0]) < cash0
    assert int(np.asarray(bundle.money.flow)[
        int(Sector.STORE), int(Sector.ROW), int(AccountCode.IMPORT_PURCHASE)
    ]) > 0
    assert bundle.goods.sku_balanced()
    assert shelf.n_fallback > 0 and shelf.n_role_actions == 0


def test_restock_permission_is_staff_in_the_same_cell():
    world, agents, bundle = _setup()
    shelf = ShelfRestockProcess(
        world, agents, ledger=bundle, staff_of_poi=_staffed(world, agents)
    )
    workers = np.flatnonzero(agents.registry.field("kind") == int(AgentKind.WORKER))
    if workers.size == 0:
        pytest.skip("合成世界に従業者が居ない")
    a = int(workers[0])
    mine = np.flatnonzero(shelf.staff_of_poi == a)
    assert mine.size > 0, "担当 POI が 1 つも割り振られていない"
    poi = int(mine[0])
    # 権限 = 担当 かつ 同一セル
    assert bool(shelf.has_permission([a], [poi])[0]) == bool(
        agents.registry.cell[a] == world.pois.cell[poi]
    )
    # 担当でない POI では必ず権限なし
    other = int(np.flatnonzero(shelf.staff_of_poi != a)[0])
    assert not shelf.has_permission([a], [other])[0]
    # 従業者でない個体は常に権限なし
    non = np.flatnonzero(agents.registry.field("kind") != int(AgentKind.WORKER))
    if non.size:
        assert not shelf.has_permission([int(non[0])], [poi])[0]


def test_reorder_point_is_the_declared_fill_ratio():
    world, agents, bundle = _setup()
    shelf = ShelfRestockProcess(world, agents, ledger=bundle)
    assert np.all(
        shelf.reorder_point == np.maximum(1, np.floor(shelf.capacity * REORDER_FILL_RATIO))
    )


def test_shelf_rests_without_a_goods_ledger():
    world, agents, _ = _setup()
    shelf = ShelfRestockProcess(world, agents, ledger=None)
    assert not shelf.active
    shelf.step(100)  # 落ちない
    assert shelf.counters()["units"] == 0.0


# ================================================================= 納品(早朝帯)
def test_delivery_runs_once_per_store_inside_the_window():
    world, agents, bundle = _setup()
    shelf = ShelfRestockProcess(world, agents, ledger=bundle)
    dl = DeliveryInboundProcess(world, ledger=bundle, shelf=shelf, master_seed=1)
    lo, hi = DELIVERY_WINDOW
    assert bool(((dl.plan_minute >= lo) & (dl.plan_minute < hi)).all())
    for t in range(lo, hi + 40):
        dl.step(t)
    assert dl.n_runs == world.n_poi
    assert int(shelf.backroom.sum()) == dl.units_delivered > 0


def test_delivery_delay_is_recorded_as_a_deviation():
    world, agents, bundle = _setup(n_cells=25)
    shelf = ShelfRestockProcess(world, agents, ledger=bundle)

    class _Log:
        def __init__(self):
            self.rows = []

        def append_many(self, pid, subj, ticks, codes, delays=None):
            self.rows.append((pid, np.asarray(codes), delays))
            return len(subj)

    log = _Log()
    dl = DeliveryInboundProcess(
        world, ledger=bundle, shelf=shelf, master_seed=7, actual_log=log
    )
    lo, hi = DELIVERY_WINDOW
    for t in range(lo, hi + 40):
        dl.step(t)
    assert log.rows, "ActualLog に 1 行も出ていない"
    assert dl.n_delayed == int((dl.delay_minute > 0).sum())


# ================================================================= 廃棄物収集
def test_leftovers_go_to_the_bin_then_out_of_the_bbox():
    world, agents, bundle = _setup(n_agents=30, n_cells=16)
    waste = WasteCollectionProcess(world, agents, ledger=bundle)
    waste.step(WASTE_TO_BIN_MINUTE)
    assert int(bundle.goods.bins.sum()) > 0
    lo, hi = COLLECT_WINDOW
    for t in range(lo, hi):
        waste.step(t)
    assert int(bundle.goods.bins.sum()) == 0
    assert waste.waste_g_collected > 0
    assert bundle.goods.sku_balanced()


def test_household_consumption_lands_in_the_sink():
    world, agents, bundle = _setup(n_agents=12, n_cells=9)
    bundle.goods.sell_many(np.array([0, 0, 1, 1]), tick=1)
    with agents.writable():
        agents.registry.holdings[:4] = 1
    waste = WasteCollectionProcess(world, agents, ledger=bundle)
    waste.step(HOUSEHOLD_CONSUME_MINUTE)
    assert waste.n_consumed > 0
    assert int(bundle.goods.sku_balance()["outflow"].sum()) > 0
    assert bundle.goods.sku_balanced()


def test_waste_band_is_reported_even_when_out_of_band():
    world, agents, bundle = _setup(n_agents=20, n_cells=16)
    waste = WasteCollectionProcess(world, agents, ledger=bundle)
    waste.step(WASTE_TO_BIN_MINUTE)
    lo, hi = COLLECT_WINDOW
    for t in range(lo, hi):
        waste.step(t)
    band = bundle.goods.waste_band(days=1)
    t_per_day = waste.projected_tonnes_per_day()
    assert t_per_day > 0.0
    # 合成小世界は実渋谷の 1/100 以下なので band(83.7-155.5 t/日)には入らない=**報告する**
    assert band.low > t_per_day


# ================================================================= 街路清掃
def test_litter_rises_with_density_and_is_swept_on_the_shift():
    world, agents, _ = _setup(n_agents=40, n_cells=9)
    clean = StreetCleaningProcess(world, agents)
    for t in range(0, 60):
        clean.step(t)
    assert clean.litter_g.sum() > 0
    lo, _hi = CLEANING_WINDOWS[0]
    for t in range(lo, lo + 30):
        clean.step(t)
    assert clean.swept_g > 0
    assert clean.n_swept_cells > 0
