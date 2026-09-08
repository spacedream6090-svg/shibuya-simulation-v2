"""台帳(U11 金・U-Goods 物)を resolve/run へ結線したときのテスト。

正典
- 境界・経済設計書 §2.3: transfer 単一API・検算②が**毎期**成立。§2.4 日次ゲート。
- 世界過程設計書 §7.1: move_goods 単一API・SKU 別収支。
- 運用設計書 §1.4 T2(録画リプレイ回帰=同じ入力なら同じ状態ハッシュ)・予算行 W2。

**設計上の要**: 台帳を注入しても**状態ハッシュが変わらない**こと。世帯の現金は
``agents.money`` そのものであり、台帳は帳簿(取引行列・部門別残高)を足すだけだから。
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from shibuya.agents.schedule import synthesize
from shibuya.agents.state import AgentState
from shibuya.economy import census as CS
from shibuya.economy import checks as CK
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import Ledger
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.run import run_day
from shibuya.world.state import World

W2_REPORT_SECONDS = 60.0


def _bundle(world: World, n_agents: int) -> LedgerBundle:
    """合成世界 + 個体数から台帳2本を作る(POI のカテゴリは索引で回す=expedient)。"""
    led = Ledger(n_agents, world.n_poi)
    cats = np.arange(world.n_poi) % 3
    goods = GoodsLedger.from_pois(
        cats, np.asarray(world.pois.stock), np.asarray(world.pois.price)
    )
    return LedgerBundle(money=led, goods=goods)


@pytest.fixture(scope="module")
def wired():
    world = World.synthetic(n_cells=64, seed=2)
    bundle = _bundle(world, 500)
    res = run_day(n_agents=500, seed=2, world=world, ticks=1_440, checkpoint_every=360,
                  ledger=bundle)
    return res, bundle


# ---------------------------------------------------------------- 決定論(T2)
def test_wiring_does_not_change_the_state_hashes(wired):
    """台帳を注入しても checkpoint ハッシュは同じ(帳簿を足すだけで世界は変えない)。"""
    res, _ = wired
    plain = run_day(n_agents=500, seed=2, ticks=1_440, checkpoint_every=360, n_cells=64)
    assert [c.combined for c in res.checkpoints] == [c.combined for c in plain.checkpoints]
    assert res.money_end == plain.money_end and res.revenue_end == plain.revenue_end
    assert int(res.column("purchases").sum()) == int(plain.column("purchases").sum())


def test_two_wired_runs_are_identical():
    world_a = World.synthetic(n_cells=32, seed=5)
    world_b = World.synthetic(n_cells=32, seed=5)
    a = run_day(n_agents=300, seed=5, world=world_a, ticks=1_440, ledger=_bundle(world_a, 300))
    b = run_day(n_agents=300, seed=5, world=world_b, ticks=1_440, ledger=_bundle(world_b, 300))
    assert a.final_hash == b.final_hash
    led_a = a.ledger.money  # type: ignore[attr-defined]
    led_b = b.ledger.money  # type: ignore[attr-defined]
    assert led_a.state_hash() == led_b.state_hash()


# ---------------------------------------------------------------- 保存則・検算
def test_conservation_over_all_sectors_including_row(wired):
    """外界を含む全部門の現金合計は 0 のまま(初期財布も transfer で入れるため)。"""
    res, bundle = wired
    led = bundle.money
    assert int(led.sector_totals(BalanceLine.CASH).sum()) == 0
    # 世帯の現金 = agents.money(写しでない)
    agents = res.agents  # type: ignore[attr-defined]
    assert int(led.balance(BalanceLine.CASH, Sector.HOUSEHOLD).sum()) == res.money_end
    assert led.balance(BalanceLine.CASH, Sector.HOUSEHOLD) is agents.registry.money
    # 店舗の現金 = 売上(第1陣は店舗が支出しないので売上と一致する)
    assert int(led.balance(BalanceLine.CASH, Sector.STORE).sum()) == res.revenue_end
    assert res.conserved


def test_purchases_are_booked_as_consumption(wired):
    res, bundle = wired
    led = bundle.money
    total = int(
        np.stack(led.flow_daily).sum(axis=0)[
            int(Sector.HOUSEHOLD), int(Sector.STORE), int(AccountCode.CONSUMPTION)
        ]
    )
    assert total == res.revenue_end > 0
    assert led.n_transfers >= int(res.column("purchases").sum())


def test_check_two_holds_after_the_run(wired):
    res, bundle = wired
    rep = CK.net_worth_equals_real_assets(bundle.money, bundle.goods)
    assert rep.ok, rep.as_text()
    assert CK.flow_matrix_balanced(bundle.money, close=None).ok


def test_census_gate_passes_for_a_wired_day(wired):
    res, bundle = wired
    row = CS.daily_census(bundle.money, bundle.goods)
    assert row["gate_ok"], row
    assert row["net_worth_ok"] and row["flow_ok"] and row["goods_balanced"]
    assert row["money_supply"] > 0


def test_world_stock_is_a_mirror_of_the_shelf(wired):
    """``world.pois.stock`` は棚(SKU 別)の写し。真値は物の台帳にある。"""
    res, bundle = wired
    world = res.world  # type: ignore[attr-defined]
    assert np.array_equal(
        np.asarray(world.pois.stock, dtype=np.int64), bundle.goods.aggregate_stock()
    )
    assert bundle.goods.sku_balanced()


# ---------------------------------------------------------------- 検算②を checkpoint ごとに
def test_check_two_holds_at_every_checkpoint():
    """検算②(主検算)は**毎期**成立する(§2.3)——手回しの tick ループで確認する。"""
    world = World.synthetic(n_cells=16, seed=7)
    agents = AgentState(200)
    bundle = _bundle(world, 200)
    bundle.money.attach_household_cash(agents.registry.money)
    schedule = synthesize(200, 7, world.n_cells)
    R.initialize(agents, world, schedule, ledger=bundle)
    agents.freeze()
    world.freeze()
    space = C.ResourceSpace(world.n_poi, agents.n, world.n_cells)
    rng = np.random.default_rng(7)
    checkpoints = 0
    for tick in range(600, 780):
        n = 20
        ids = rng.choice(agents.n, size=n, replace=False).astype(np.int64)
        pois = rng.integers(0, world.n_poi, size=n)
        intents = C.IntentBatch(
            agent_id=ids,
            action_code=np.full(n, C.ACT_BUY, dtype=np.int8),
            target_id=pois.astype(np.int32),
            resource_id=space.poi(pois),
            t_notice_ns=np.full(n, C.tick_start_ns(tick), dtype=np.int64),
        )
        plan = C.arbitrate_resources(
            intents, tick, b"salt-ledger", space, world.pois.stock, world.pois.capacity
        )
        R.apply(plan.confirmed, plan.losers, agents, world, tick, schedule=schedule,
                ledger=bundle)
        if tick % 20 == 0:
            checkpoints += 1
            assert CK.net_worth_equals_real_assets(bundle.money, bundle.goods).ok
            assert CK.flow_matrix_balanced(bundle.money).ok
            assert bundle.goods.sku_balanced()
            assert int(bundle.money.sector_totals(BalanceLine.CASH).sum()) == 0
    assert checkpoints == 9
    assert int(np.asarray(bundle.money.flow)[
        int(Sector.HOUSEHOLD), int(Sector.STORE), int(AccountCode.CONSUMPTION)
    ]) > 0
    assert np.array_equal(
        np.asarray(world.pois.stock, dtype=np.int64), bundle.goods.aggregate_stock()
    )


# ---------------------------------------------------------------- 物の操作(§7.2)
def test_restock_through_resolve_pays_and_updates_the_mirror():
    """補充は resolve 経由で ``world.pois.stock``(写し)を更新し、域外仕入を計上する。"""
    world = World.synthetic(n_cells=16, seed=11)
    bundle = _bundle(world, 10)
    world.freeze()
    bundle.money.endow_stores(np.full(world.n_poi, 100_000, dtype=np.int64), tick=0)
    before = int(world.pois.stock[3])
    ok = R.restock(world, bundle, np.array([3]), np.array([6]), tick=100)
    assert list(ok) == [True]
    assert int(world.pois.stock[3]) == before + 6
    assert int(bundle.goods.aggregate_stock()[3]) == before + 6
    cost = int(bundle.goods.unit_cost[3]) * 6
    assert int(bundle.money.balance(BalanceLine.CASH, Sector.STORE)[3]) == 100_000 - cost
    assert int(np.asarray(bundle.money.flow)[
        int(Sector.STORE), int(Sector.ROW), int(AccountCode.IMPORT_PURCHASE)
    ]) == cost
    assert world.frozen  # 窓は閉じて戻る


def test_collect_waste_through_resolve():
    world = World.synthetic(n_cells=16, seed=12)
    bundle = _bundle(world, 10)
    world.freeze()
    bundle.goods.to_bin_many(np.array([0, 1]), np.array([3, 2]), tick=1)
    grams = R.collect_waste(world, bundle, None, tick=2)
    assert grams > 0
    assert int(bundle.goods.bins.sum()) == 0
    assert bundle.goods.sku_balanced()


def test_consume_moves_holdings_into_the_sink():
    """消費は世帯の所持を減らし SKU 別 sink に落ちる(検算①は閉じたまま)。"""
    world = World.synthetic(n_cells=16, seed=14)
    agents = AgentState(5)
    bundle = _bundle(world, 5)
    bundle.money.attach_household_cash(agents.registry.money)
    goods = bundle.goods
    goods.sell_many(np.array([0, 0, 1]), tick=1)  # 世帯合計へ 3 個
    with agents.writable():
        agents.registry.holdings[:3] = 1
    agents.freeze()
    sku0 = int(goods.poi_sku[0, 0])
    sku1 = int(goods.poi_sku[1, 0])
    ok = R.consume(agents, bundle, np.array([0, 1, 4]), np.array([sku0, sku1, sku0]),
                   np.array([1, 1, 1]), tick=2)
    assert list(ok) == [True, True, False]  # 個体4 は所持なし
    assert list(agents.registry.holdings[:3]) == [0, 0, 1]
    assert goods.sku_balanced()
    assert int(goods.sku_balance()["outflow"].sum()) == 2


def test_restock_requires_a_goods_ledger():
    world = World.synthetic(n_cells=8, seed=13)
    with pytest.raises(ValueError):
        R.restock(world, LedgerBundle(), np.array([0]), np.array([1]), tick=0)


# ---------------------------------------------------------------- W2(5,000体)
@pytest.mark.slow
def test_w2_five_thousand_agents_with_the_ledger_wired():
    """W2: 台帳を結線しても 1 シミュ日の壁時計が予算内(報告値つき)。"""
    world = World.synthetic(n_cells=139, seed=1)
    bundle = _bundle(world, 5_000)
    t0 = time.perf_counter()
    res = run_day(n_agents=5_000, seed=1, world=world, ticks=1_440, checkpoint_every=360,
                  ledger=bundle)
    wall = time.perf_counter() - t0
    plain = run_day(n_agents=5_000, seed=1, ticks=1_440, checkpoint_every=360, n_cells=139)
    print(
        f"\n[W2 台帳あり] {res.wall_seconds:.2f}s / 台帳なし {plain.wall_seconds:.2f}s "
        f"(上限 600s・報告閾値 {W2_REPORT_SECONDS}s)"
    )
    print("  " + bundle.money.summary())
    print("  " + bundle.goods.summary())
    assert res.final_hash == plain.final_hash  # T2: 台帳はハッシュを変えない
    assert wall <= W2_REPORT_SECONDS
    assert res.conserved and res.min_stock >= 0
    assert int(bundle.money.sector_totals(BalanceLine.CASH).sum()) == 0
    assert CK.net_worth_equals_real_assets(bundle.money, bundle.goods).ok
    assert CS.daily_census(bundle.money, bundle.goods)["gate_ok"]
    assert res.growth_report is not None and res.growth_report.ok
