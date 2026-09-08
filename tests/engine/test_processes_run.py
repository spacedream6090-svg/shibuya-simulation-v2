"""C4 結線(世界過程 → run)の受入テスト。

正典
- 世界過程設計書 §6 D-R2-5(第1陣)・§5 D-R2-4(憲法5)・§2(ActualLog・遵守率)。
- 運用設計書 §1.4 **T2**(同一 manifest×2 で全 checkpoint ハッシュ一致)。
- 予算宣言表 **W2**(壁時計/シミュ日 ≤10 分。本サブの報告閾値は 60 s)。
- 境界・経済設計書 §2.3(transfer 単一API・全部門の現金合計が 0)。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya.economy import checks as CK
from shibuya.economy.accounts import BalanceLine, Sector
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import Ledger
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.run import run_day
from shibuya.world.state import World

WORLD_DIR = Path("data/world/v2")
W2_REPORT_SECONDS = 60.0
real_data = pytest.mark.skipif(
    not (WORLD_DIR / "w12_timetables.parquet").exists(), reason="実世界資産 data/world/v2 が無い"
)


def _bundle(world: World, n_agents: int) -> LedgerBundle:
    led = Ledger(n_agents, world.n_poi)
    cats = np.arange(world.n_poi) % 3
    goods = GoodsLedger.from_pois(
        cats, np.asarray(world.pois.stock), np.asarray(world.pois.price)
    )
    return LedgerBundle(money=led, goods=goods)


# ================================================================= 合成世界(CI 常時)
@pytest.fixture(scope="module")
def small():
    return run_day(n_agents=400, seed=3, ticks=480, checkpoint_every=240, n_cells=36)


def test_run_result_carries_the_world_process_fields(small):
    assert small.registry_hash and small.constitution_ok
    assert set(small.process_seconds) >= {"environment", "rail", "opening", "crowd", "traffic"}
    assert "crowd.balked" in small.process_counters


def test_processes_can_be_switched_off():
    off = run_day(n_agents=200, seed=3, ticks=120, n_cells=16, processes=False)
    assert off.registry_hash == "" and not off.constitution_ok
    assert off.conserved


def test_conservation_holds_with_fares_in_the_equation(small):
    assert small.conserved
    assert small.fares_paid >= 0
    assert small.min_stock >= 0


def test_flow_reaches_the_b4_field(small):
    """混雑場が作った流れが B4 描画欄に載る(人物①「密度・流れ」)。"""
    runner = small.runner  # type: ignore[attr-defined]
    assert runner.flow.shape == (small.n_cells,)
    assert int(np.count_nonzero(runner.flow)) > 0


def test_two_runs_with_the_same_seed_are_identical():
    """T2: エンジン層 bit 再現(世界過程を入れても崩れない)。"""
    a = run_day(n_agents=300, seed=9, ticks=240, checkpoint_every=120, n_cells=25)
    b = run_day(n_agents=300, seed=9, ticks=240, checkpoint_every=120, n_cells=25)
    assert [c.combined for c in a.checkpoints] == [c.combined for c in b.checkpoints]
    assert a.registry_hash == b.registry_hash
    assert a.replay_date == b.replay_date
    assert a.fares_paid == b.fares_paid


# ================================================================= 実資産(1 シミュ日)
@real_data
@pytest.mark.slow
def test_run_day_on_the_real_world_with_all_first_batch_processes(capsys):
    world = World.load(WORLD_DIR)
    bundle = _bundle(world, 5_000)
    res = run_day(
        n_agents=5_000, seed=1, world=world, ticks=1_440, checkpoint_every=360,
        world_dir=WORLD_DIR, ledger=bundle,
    )
    runner = res.runner  # type: ignore[attr-defined]
    with capsys.disabled():
        print("\n" + res.summary())
        print(runner.summary())

    # 台帳・門前条件
    assert res.registry_hash and res.constitution_ok
    assert res.replay_date and res.replay_date in runner.assets.weather_dates

    # 乗客の保存則(bbox 内 + 乗車中 + 域外滞在 = 個体数)
    inb, riding, outside = runner.rail.rider_census()
    assert inb + riding + outside == res.n_agents
    assert runner.rail.n_arrivals > 0, "域外からの到着が 1 件も無い"
    assert res.n_boarded > 0, "乗車が 1 件も成立しない"

    # 金の保存則(運賃の sink 込み・全部門の現金合計 0)
    assert res.conserved, (res.money_start, res.money_end, res.revenue_end, res.fares_paid)
    assert res.fares_paid > 0
    assert int(bundle.money.sector_totals(BalanceLine.CASH).sum()) == 0
    assert int(bundle.money.balance(BalanceLine.CASH, Sector.HOUSEHOLD).sum()) == res.money_end

    # ActualLog と遵守率
    assert res.actual_log_rows > 0
    assert 0.0 <= res.compliance_rate <= 1.0
    assert runner.opening.n_fallback > 0  # conf 宣言つきフォールバックが台帳に載る

    # ダイヤの本数(路線別)
    per_line = runner.rail.trains_per_line()
    assert sum(per_line.values()) == runner.rail.dep_tick.size > 3_000

    # W2(報告値)
    assert res.wall_seconds <= W2_REPORT_SECONDS
    assert res.growth_report is not None


@real_data
@pytest.mark.slow
def test_real_world_runs_are_bit_identical_for_the_same_seed():
    """T2: 実資産でも同一 seed で checkpoint ハッシュが一致する。"""
    kw = dict(n_agents=800, seed=4, ticks=360, checkpoint_every=180, world_dir=WORLD_DIR)
    a = run_day(world=World.load(WORLD_DIR), **kw)
    b = run_day(world=World.load(WORLD_DIR), **kw)
    assert [c.combined for c in a.checkpoints] == [c.combined for c in b.checkpoints]
    assert a.replay_date == b.replay_date == a.runner.environment.replay_date  # type: ignore[attr-defined]


# ================================================================= C4 後半(§7.2 初回実装)
C4B_PROCESS_IDS = (
    "shelf_stock_restock",
    "delivery_inbound",
    "waste_collection",
    "street_cleaning",
    "delivery_last_mile",
    "bus_taxi_operation",
    "public_service_dispatch",
    "infra_daily_load",
    "hotel_room_inventory",
    "road_works_occupancy",
    "press_official_release",
    "large_event",
)


def _bundle_c4b(world: World, n_agents: int) -> LedgerBundle:
    """C4 後半の束: 店舗へ参入資本を入れて域外仕入を払えるようにする(expedient・報告対象)。"""
    from shibuya.economy import census as CS
    from shibuya.world.assets import hash_free_cat_code

    led = Ledger(n_agents, world.n_poi)
    cats = np.array([hash_free_cat_code(c) for c in world.assets.poi_cat], dtype=np.int64)
    goods = GoodsLedger.from_pois(
        cats, np.asarray(world.pois.stock), np.asarray(world.pois.price)
    )
    led.endow_stores(np.full(world.n_poi, 200_000, dtype=np.int64), tick=0)
    return LedgerBundle(
        money=led, goods=goods, census=lambda d: CS.daily_census(led, goods, day=d)
    )


def test_all_declared_process_ids_have_an_implementation():
    """台帳 ⇄ 実装の双方向: 第1陣+前倒しの過程 id は全て実行器が名乗る。"""
    from shibuya.world.processes import first_batch as FB

    res = run_day(n_agents=100, seed=1, ticks=10, n_cells=16)
    runner = res.runner  # type: ignore[attr-defined]
    named = {
        pid for key in runner._procs for pid in getattr(runner._procs[key], "process_ids", ())
    }
    declared = {p.id for p in FB.DECLARATIONS + FB.PULLED_FORWARD_DECLARATIONS}
    # 実装のある行(``executor=none`` の集約行 3 本は他の過程の内数)
    missing = declared - named - {"goods_conservation", "daynight_solar", "weather"}
    assert missing <= {"static_noise_field"}, missing
    assert named <= declared, named - declared


def test_new_processes_are_ablatable_by_id():
    res = run_day(
        n_agents=100, seed=1, ticks=10, n_cells=16,
        processes_disabled=["AB-SHELF-REORDER", "delivery_last_mile"],
    )
    runner = res.runner  # type: ignore[attr-defined]
    assert not runner.is_enabled("shelf") and not runner.is_enabled("last_mile")
    assert runner.is_enabled("waste")
    assert "shelf_stock_restock" in res.run_manifest_fields()["ablations"]


def test_p_notice_ablation_can_be_selected():
    from shibuya.perception.p_notice import Ablation

    res = run_day(n_agents=80, seed=1, ticks=10, n_cells=9, p_notice_ablation="A1")
    assert res.runner.salient.ablation == Ablation.A1_DISTANCE  # type: ignore[attr-defined]


def test_deletion_candidates_stay_empty():
    """憲法5(D-R2-4): 届き先が消えた細部は 1 件も無い。"""
    res = run_day(n_agents=50, seed=1, ticks=5, n_cells=9)
    report = res.runner.constitution_report  # type: ignore[attr-defined]
    assert report.ok
    assert tuple(report.deletion_candidates) == ()


@real_data
@pytest.mark.slow
def test_c4_second_half_on_the_real_world(capsys):
    """受入: 実資産 5,000 体 × 1 日で C4 後半の全過程が回り、保存則・ゲートが立つ。"""
    world = World.load(WORLD_DIR)
    bundle = _bundle_c4b(world, 5_000)
    res = run_day(
        n_agents=5_000, seed=1, world=world, ticks=1_440, checkpoint_every=360,
        world_dir=WORLD_DIR, ledger=bundle,
    )
    runner = res.runner  # type: ignore[attr-defined]
    with capsys.disabled():
        print("\n" + res.summary())
        print(runner.summary())
        print(
            f"  [C4後半] 補充 {res.restocks:,} / 納品 {res.deliveries:,} / 宅配 {res.parcels:,} / "
            f"バス到着 {res.bus_arrivals:,} / 出動 {res.dispatches:,} / 気づき {res.noticed:,} / "
            f"ホテル泊 {res.hotel_checkins:,} / 廃棄 {res.waste_tonnes_per_day:.3f} t/日 "
            f"(band {res.waste_band[0]:.1f}-{res.waste_band[1]:.1f})"
        )

    # L4(呼数の硬い上限)
    from shibuya.engine.arbiter import call_budget_per_tick

    assert res.llm_calls <= int(call_budget_per_tick(5_000) * 1_440)

    # 金の保存則: 全部門(外界・銀行・政府を含む)の現金合計が 0
    assert int(bundle.money.sector_totals(BalanceLine.CASH).sum()) == 0
    assert res.conserved
    assert CK.net_worth_equals_real_assets(bundle.money, bundle.goods).ok

    # 物の保存則: SKU 別の期首+流入−流出+残差 = 期末
    assert bundle.goods.sku_balanced()
    assert np.array_equal(
        np.asarray(res.world.pois.stock, dtype=np.int64),  # type: ignore[attr-defined]
        bundle.goods.aggregate_stock(),
    )

    # 日次センサス+ゲート(失敗しても raise しない=診断の赤)
    assert res.census_row, "センサス行が RunResult に載っていない"
    assert res.census_pass, res.census_row

    # 乗客の保存則
    assert runner.riders_conserved()

    # 新過程の ActualLog 行(**件数が 0 でない**ことまで見る)
    for pid in ("shelf_stock_restock", "delivery_inbound", "waste_collection",
                "delivery_last_mile", "bus_taxi_operation", "road_works_occupancy",
                "press_official_release", "large_event", "hotel_room_inventory"):
        assert pid in runner.log.process_ids, pid
        assert runner.log.compliance_rate([pid]).n_total > 0, pid
    assert res.actual_log_rows > 0

    # 前倒し 9 本が「動いた」ことの正の証拠
    assert res.deliveries > 0 and res.parcels > 0 and res.bus_arrivals > 0
    assert runner.road_works.n_started > 0
    assert runner.press.n_releases == 3
    assert runner.large_event.n_in > 0
    assert runner.infra.counters()["power_kwh_day"] > 0
    assert runner.hotel.active

    # W2(報告値)と門前条件
    assert res.wall_seconds <= W2_REPORT_SECONDS
    assert res.constitution_ok and res.registry_hash
    fields = res.run_manifest_fields()
    assert fields["template_sha256"] and fields["catalog_sha16"]
    assert set(C4B_PROCESS_IDS) <= set(fields["process_ids"])


@real_data
@pytest.mark.slow
def test_c4_second_half_is_bit_identical_for_the_same_seed():
    """T2: 物・顕著行為・前倒しを入れても同一 seed で checkpoint ハッシュが一致する。"""
    def _run():
        world = World.load(WORLD_DIR)
        return run_day(
            n_agents=800, seed=4, world=world, ticks=360, checkpoint_every=180,
            world_dir=WORLD_DIR, ledger=_bundle_c4b(world, 800),
        )

    a, b = _run(), _run()
    assert [c.combined for c in a.checkpoints] == [c.combined for c in b.checkpoints]
    assert a.restocks == b.restocks and a.deliveries == b.deliveries
    assert a.noticed == b.noticed and a.dispatches == b.dispatches
