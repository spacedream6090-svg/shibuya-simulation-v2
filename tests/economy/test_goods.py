"""物の保存則(U-Goods)のテスト = 世界過程設計書 §7.1。

検算①(全SKUで期首+流入−流出=期末)・②(廃棄 sink の t/日 band = 台帳行 W1)・
``move_goods`` 単一API の列挙外拒否・棚卸差異ゲート・退蔵(売れ残り)・
補充が**金の台帳**へ域外仕入を立てること。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.core.growth import check_growth
from shibuya.economy import checks as CK
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.anchors import WASTE_TONNES_PER_DAY
from shibuya.economy.goods import (
    GOODS_FAUCET_SINK,
    GoodsCode,
    GoodsLedger,
    GoodsRef,
    NodeKind,
    SkuRegistry,
    goods_flow_kind,
    goods_is_allowed,
    growth_declarations,
)
from shibuya.economy.ledger import Ledger


def _goods(n_poi: int = 6, stock: int = 12) -> GoodsLedger:
    cats = np.arange(n_poi) % 3
    price = np.array([300, 800, 1_500] * n_poi, dtype=np.int64)[:n_poi]
    return GoodsLedger.from_pois(cats, np.full(n_poi, stock), price)


def test_sku_registry_is_one_to_three_per_category():
    reg = SkuRegistry.default()
    assert reg.n_sku == 6
    assert [len(s) for s in reg.slots] == [3, 2, 1]
    assert (reg.mass_g > 0).all()


def test_goods_faucet_sink_table_is_one_to_one_with_the_enum():
    """§7.1 の faucet/sink 列挙と 1 対 1(列挙にない科目の move_goods は実行不能)。"""
    assert set(GOODS_FAUCET_SINK) == set(GoodsCode)
    assert goods_flow_kind(GoodsCode.RESTOCK_FROM_ROW).name == "FAUCET"
    assert goods_flow_kind(GoodsCode.CARRY_IN).name == "FAUCET"
    for sink in (GoodsCode.CONSUME, GoodsCode.WASTE_OUT, GoodsCode.RETURN_OUT):
        assert goods_flow_kind(sink).name == "SINK"
    assert goods_flow_kind(GoodsCode.SALE).name == "INTERNAL"
    assert not goods_is_allowed(999, NodeKind.ROW, NodeKind.STORE_SHELF)
    assert not goods_is_allowed(GoodsCode.SALE, NodeKind.HOUSEHOLD, NodeKind.STORE_SHELF)


def test_move_goods_rejects_disallowed_pairs_and_shortages():
    g = _goods()
    assert g.move_goods(GoodsRef(NodeKind.ROW), GoodsRef(NodeKind.STORE_SHELF, 0),
                        5, 0, GoodsCode.RESTOCK_FROM_ROW, tick=0)
    assert not g.move_goods(GoodsRef(NodeKind.STORE_SHELF, 0), GoodsRef(NodeKind.HOUSEHOLD),
                            10_000, 0, GoodsCode.SALE, tick=0)  # 在庫不足
    assert not g.move_goods(GoodsRef(NodeKind.HOUSEHOLD), GoodsRef(NodeKind.STORE_SHELF, 0),
                            1, 0, GoodsCode.SALE, tick=0)  # 表にない向き
    assert not g.move_goods(GoodsRef(NodeKind.ROW), GoodsRef(NodeKind.STORE_SHELF, 0),
                            1, 0, 999, tick=0)  # 列挙外
    assert g.rejections == 3


def test_shelf_arrays_are_frozen_outside_the_ledger():
    g = _goods()
    with pytest.raises(ValueError):
        g.shelf[0, 0] = 999


def test_per_sku_balance_holds_across_sale_restock_waste_and_consume():
    """検算①: 期首 + 流入 − 流出 + 残差 = 期末(全 SKU・日次)。"""
    g = _goods()
    assert g.sku_balanced()
    g.sell_many(np.array([0, 0, 1, 2, 3]), tick=10)
    g.restock_many(np.array([0, 1]), np.array([7, 3]), tick=11)
    g.to_bin_many(np.array([0]), np.array([2]), tick=12)
    g.collect_waste(np.array([0]), tick=13)
    g.consume_many(np.array([0]), np.array([1]), tick=14)
    bal = g.sku_balance()
    assert (bal["diff"] == 0).all(), bal
    assert g.sku_balanced()
    assert int(bal["inflow"].sum()) == 10
    assert int(bal["outflow"].sum()) == 3  # 廃棄 2 + 消費 1


def test_sale_moves_units_from_shelf_to_households():
    g = _goods(n_poi=3, stock=6)
    before = int(g.aggregate_stock().sum())
    ok = g.sell_many(np.array([0, 0, 1]), tick=5)
    assert list(ok) == [True, True, True]
    assert int(g.aggregate_stock().sum()) == before - 3
    assert int(g.inside_stock_by_sku().sum()) == before  # 世帯へ移っただけ(bbox 内で保存)


def test_sale_respects_shelf_depth_for_duplicate_stores():
    g = GoodsLedger.from_pois(np.array([2]), np.array([2]), np.array([1_500]))  # 1 スロット 2 個
    ok = g.sell_many(np.array([0, 0, 0]), tick=1)
    assert list(ok) == [True, True, False]
    assert int(g.aggregate_stock()[0]) == 0


def test_restock_pays_the_money_ledger_as_an_import_purchase():
    """補充は**金の台帳**へ域外仕入(店舗→外界 sink)を立てる。払えない店は補充されない。"""
    g = _goods(n_poi=2, stock=1)
    led = Ledger(1, 2)
    led.endow_stores(np.array([10_000, 0]), tick=0)
    ok = g.restock_many(np.array([0, 1]), np.array([5, 5]), tick=1, money=led)
    assert list(ok) == [True, False]  # 店舗1 は現金 0 なので補充できない
    cost = int(g.unit_cost[0]) * 5
    assert int(led.balance(BalanceLine.CASH, Sector.STORE)[0]) == 10_000 - cost
    assert int(np.asarray(led.flow)[
        int(Sector.STORE), int(Sector.ROW), int(AccountCode.IMPORT_PURCHASE)
    ]) == cost
    assert CK.flow_matrix_balanced(led).ok


def test_inventory_value_feeds_the_money_ledger_and_check_two_still_holds():
    g = _goods(n_poi=2, stock=4)
    led = Ledger(2, 2)
    led.endow_stores(np.array([50_000, 50_000]), tick=0)
    g.restock_many(np.array([0]), np.array([10]), tick=1, money=led)
    with led.unlocked():
        led.revalue_inventory(int(Sector.STORE), g.inventory_value())
    rep = CK.net_worth_equals_real_assets(led, g)
    assert rep.ok, rep.as_text()
    assert rep.real_assets_total == int(g.inventory_value().sum())


def test_stocktake_residual_gate():
    """棚卸差異は残差科目。閾値(流量比 1%)超でゲート失敗。"""
    g = _goods(n_poi=2, stock=100)
    g.sell_many(np.arange(2), tick=1)
    assert g.stocktake_gate()[0]
    assert g.stocktake(0, 0, -50, tick=2)
    ok, ratio = g.stocktake_gate()
    assert not ok and ratio > 0.01
    assert g.sku_balanced()  # 差異は残差として計上されるので収支は閉じたまま


def test_hoard_counts_unsold_shelf_stock():
    """退蔵項 = 売れ残り在庫(滞留日数で判定)。"""
    g = _goods(n_poi=2, stock=5)
    for d in range(20):
        g.on_day_end(d)
    rep = g.hoard_report(days=14)
    assert rep["hoard_slots"] > 0 and rep["hoard_units"] > 0 and rep["hoard_value"] > 0
    # 売れた棚は滞留日数が 0 に戻る
    g.sell_many(np.array([0]), tick=1)
    g.on_day_end(20)
    assert g.hoard_report(days=14)["hoard_units"] < rep["hoard_units"]


def test_waste_band_against_the_w1_anchor():
    """検算②: 廃棄 sink の月次総量 ≈ 渋谷区ごみ 119.6 t/日 の band(±30%)。"""
    reg = SkuRegistry.default()
    # 1 個 = 350 g の SKU を 1 日あたり band 中央になる個数だけ捨てる合成月
    per_day = int(WASTE_TONNES_PER_DAY * 1_000_000 / reg.mass_g[0])
    n_poi = 400
    g = GoodsLedger.from_pois(
        np.zeros(n_poi, dtype=np.int64),
        np.full(n_poi, per_day // n_poi + 2),
        np.full(n_poi, 300),
    )
    days = 30
    for d in range(days):
        qty = np.full(n_poi, per_day // n_poi, dtype=np.int64)
        g.restock_many(np.arange(n_poi), qty, tick=d * 1_440)
        g.to_bin_many(np.arange(n_poi), qty, tick=d * 1_440 + 1)
        g.collect_waste(None, tick=d * 1_440 + 2)
        g.on_day_end(d)
    band = g.waste_band(days=days)
    print("\n" + band.as_text())
    assert band.ok, band.as_text()
    assert band.low < WASTE_TONNES_PER_DAY < band.high
    # 桁が 1 つ違えば band から外れる(band が検査として効いていることの確認)
    g2 = GoodsLedger.from_pois(np.zeros(2, dtype=np.int64), np.full(2, 10), np.full(2, 300))
    g2.to_bin_many(np.arange(2), np.full(2, 5), tick=0)
    g2.collect_waste(None, tick=1)
    g2.on_day_end(0)
    assert not g2.waste_band(days=1).ok


def test_delivery_log_is_bounded_and_declared():
    """§7.2「O(t)ログは状態成長宣言を型レベルで強制」。"""
    g = GoodsLedger.from_pois(
        np.zeros(2, dtype=np.int64), np.full(2, 5), np.full(2, 300),
        delivery_capacity=8, retention_days=1,
    )
    for t in range(20):
        g.restock_many(np.array([0]), np.array([1]), tick=t)
    assert g.delivery_rows().shape[0] <= 8
    assert g.n_delivery_dropped > 0
    decls = growth_declarations()
    rep = check_growth(
        decls,
        {"delivery_log": 5_000 * 2 * 16, "shelf_stock": 0},
        steps=1_440, minutes_per_step=1, n_entities=5_000,
    )
    assert rep.ok, rep.as_text()


def test_deliver_is_an_alias_of_restock():
    g = _goods(n_poi=1, stock=0)
    assert list(g.deliver(np.array([0]), np.array([4]), tick=0)) == [True]
    assert int(g.aggregate_stock()[0]) == 4


# ---------------------------------------------------------------- sell_many のスロット跨ぎ
def test_sell_many_dispenses_across_all_slots():
    """回帰: 先頭スロットの残りを超えても、他スロットに在庫があれば売れる。

    バグ(C4 前半): ``_first_nonempty_slot`` の**先頭スロットだけ**から払い出していたため、
    同一 tick に同一 POI へ来た客が先頭スロットの残数を超えると、店の棚合計(``can_sell``)は
    足りているのに ``OUT_OF_STOCK`` になっていた。``engine.resolve._apply_buy`` が
    ≤8 回のスロット再試行で埋め合わせていた(保険としては残す)。
    """
    g = _goods(n_poi=1, stock=0)
    # コンビニ(3 SKU)の棚を 2 / 3 / 1 に作る
    for slot, qty in enumerate((2, 3, 1)):
        assert g.restock_many(np.array([0]), np.array([qty]), tick=0,
                              slot=np.array([slot]))[0]
    assert int(g.aggregate_stock()[0]) == 6
    ok = g.sell_many(np.zeros(6, dtype=np.int64), tick=1)
    assert list(ok) == [True] * 6, "スロットを跨いで払い出せていない"
    assert int(g.aggregate_stock()[0]) == 0
    assert g.sku_balanced()
    # 世帯側は SKU 別に 2/3/1 で増えている(スロット順=決定論)
    hh = g.inside_stock_by_sku() - g.stock_by_sku()
    assert list(hh[:3]) == [2, 3, 1]


def test_sell_many_still_refuses_when_the_whole_shelf_is_empty():
    g = _goods(n_poi=1, stock=0)
    assert g.restock_many(np.array([0]), np.array([2]), tick=0, slot=np.array([1]))[0]
    ok = g.sell_many(np.zeros(4, dtype=np.int64), tick=1)
    assert list(ok) == [True, True, False, False]
    assert int(g.aggregate_stock()[0]) == 0


def test_sell_many_is_row_order_deterministic_across_slots():
    g = _goods(n_poi=2, stock=0)
    for slot, qty in enumerate((1, 1, 1)):
        g.restock_many(np.array([0]), np.array([qty]), tick=0, slot=np.array([slot]))
    g.restock_many(np.array([1]), np.array([2]), tick=0, slot=np.array([0]))
    stores = np.array([0, 1, 0, 1, 0, 1], dtype=np.int64)
    ok = g.sell_many(stores, tick=2)
    assert list(ok) == [True, True, True, True, True, False]
    assert int(g.aggregate_stock().sum()) == 0


def test_sell_many_ignores_out_of_range_rows_without_shifting_the_rank():
    g = _goods(n_poi=1, stock=0)
    g.restock_many(np.array([0]), np.array([2]), tick=0, slot=np.array([0]))
    ok = g.sell_many(np.array([-1, 0, 99, 0], dtype=np.int64), tick=1)
    assert list(ok) == [False, True, False, True]
    assert int(g.aggregate_stock()[0]) == 0
