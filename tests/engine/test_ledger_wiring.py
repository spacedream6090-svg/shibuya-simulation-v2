"""台帳(U11 金・U-Goods 物)を resolve/run へ結線したときのテスト。

正典
- 境界・経済設計書 §2.3: transfer 単一API・検算②が**毎期**成立。§2.4 日次ゲート。
- 世界過程設計書 §7.1: move_goods 単一API・SKU 別収支。
- 運用設計書 §1.4 T2(録画リプレイ回帰=同じ入力なら同じ状態ハッシュ)・予算行 W2。

**C3 まで成り立っていた不変(C4 後半で条件つきになった)**: 「台帳を注入しても状態ハッシュが
変わらない」。C4 後半で **物の世界過程**(補充・納品・廃棄物収集)が入り、これらは物の台帳が
無いと動かない=台帳の有無が世界を変える。したがって不変は
「**物の過程を切れば**ハッシュは変わらない」に狭まる(``GOODS_PROCESS_IDS`` を ablate)。
物の過程を入れると棚在庫が動くことは ``test_goods_processes_change_the_world`` が正の側から押さえる。
世帯の現金が ``agents.money`` そのもの(写しでない)ことは変わらない。

〔第347・検収 M2〕同じ確かめを台帳の 2 つの形(``KINDS``)で回す: 段階 2 の外(基準の口=前の切替口 off と同じ値)と
段階 2 on(今のランが通る道)。段階 2 on で値が違う所(レジの税・部品が動かす世帯の現金)は、各試験の注に取り直した値を書いた。
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from tests import _time_gates as TG

from shibuya.world.facts.mock_schedule import synthesize
from shibuya.world.model.agent_table import AgentState
from shibuya.economy import census as CS
from shibuya.economy import checks as CK
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy import stage2_bind as ES2
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import Ledger
# 〔割る段 5b の G1〕別名 C を割り先ごとに分けた(C=act.commit・CW=act.intake.from_words・CV=foundation.vocab.act_codes の名)
from shibuya.act import commit as C
from shibuya.foundation.vocab import act_codes as CV
# 〔割る段 6 の S6-G0〕別名 R を割り先ごとに分けた(R=act/ops/law_writes・R_APPLY=act/apply・R_INIT=act/ops/init_writes。割る前は全部 resolve)
from shibuya.act.ops import law_writes as R
from shibuya.act import apply as R_APPLY
from shibuya.act.ops import init_writes as R_INIT
from shibuya.foundation.ports.ledger import LedgerBundle
from shibuya.runtime.run import run_day
from shibuya.world.model.state import World
from tests import golden_env as GE
from tests.economy import _stage2_outside as SO

W2_REPORT_SECONDS = 60.0

#: 物の台帳が無いと動かない世界過程(C4 後半)。ハッシュ不変の比較ではこれを切る。
GOODS_PROCESS_IDS = (
    "shelf_stock_restock",
    "delivery_inbound",
    "waste_collection",
    "street_cleaning",
)


#: 〔第347・検収 M2〕台帳の 2 つの形。``outside``=段階 2 の外(基準の口=試験の中だけの束・前の切替口 off と同じ値)/
#: ``stage2``=段階 2 on(今のランが通る道)。ランでは組み立てが段階 2 を挿す(素の ``Ledger``・部品は全部)。組み立てを通らない
#: 試験では、試験の代役の組み立ての物で挿す(``_attach_stage2_by_hand``)。
KINDS = ("outside", "stage2")


def _bundle(world: World, n_agents: int, kind: str = "outside") -> LedgerBundle:
    """合成世界 + 個体数から台帳2本を作る(POI のカテゴリは索引で回す=expedient)。

    ``census`` も注入する(``cli.build_ledger_bundle`` と同じ形)。``RunResult.census_row``
    が締めた日の実数を持つことを押さえるのに要る。

    〔第 2 期 2-4 V4〕経済の段階 2 が既定 on になった=本ファイル(台帳の配線=段階 2 の外の C4 の帳簿)は段階 2 の外で見る
    (段階 2 の帳簿・語・保存則は ``tests/economy/stage2``)。〔第347 止めた切替口の削除〕前はモジュールの autouse で切替口を off に
    した=台帳を段階 2 の口を持たない型(試験の中だけの束 ``tests/economy/_stage2_outside.py``)で作る(手順 0 で off と同じ値を
    確かめた=記録 ``docs/bench/analysis/switch-removal-347/README.md``)。〔第347・検収 M2〕``kind="stage2"`` は素の ``Ledger``
    (段階 2 の口を持つ=今のランの道)。同じ確かめを両方の形で回す(段階 2 on で値が違う所は期待値を取り直した=各試験の注)。
    """
    assert kind in KINDS, kind
    led = (SO.outside(Ledger) if kind == "outside" else Ledger)(n_agents, world.n_poi)
    cats = np.arange(world.n_poi) % 3
    goods = GoodsLedger.from_pois(
        cats, np.asarray(world.pois.stock), np.asarray(world.pois.price)
    )
    return LedgerBundle(
        money=led, goods=goods, census=lambda d: CS.daily_census(led, goods, day=d)
    )


def _pin_stage2(mp: pytest.MonkeyPatch, parts: tuple[str, ...] | None = None) -> None:
    """段階 2 の部品と ATM の表をモジュールの既定に押さえる(ほかの試験の漏れに依らない)。``parts`` で部品を選ぶ。"""
    mp.setattr(ES2, "_PARTS", ES2.PARTS if parts is None else tuple(parts))
    mp.setattr(ES2, "_ATM_OVERRIDE", None)


def _attach_stage2_by_hand(bundle: LedgerBundle, n_agents: int) -> None:
    """組み立てを通らない試験で段階 2 を挿す(部品は全部・体は全員 種別 0)。組み立ての物は試験の代役(共有の助け
    ``tests/economy/stage2/_plans.py::stage2_plan``=〔第347・検収 F-4〕前は別の試験のモジュールの非公開の ``_plan`` を読んでいた。
    本物の ``Stage2Plan`` と違う所は助けの docstring)。世帯と店の初期の財布より前に呼ぶ。"""
    from tests.economy.stage2._plans import stage2_plan

    bundle.money.attach_stage2(stage2_plan(kinds=np.zeros(n_agents, dtype=np.int64)))
    assert bundle.money.stage2 is not None


def _register_tax(led: Ledger) -> int:
    """段階 2 on はレジの消費税を店の預かり金に積む(店の現金に残る・売上の写し ``revenue_end`` は税抜き)。段階 2 の外は 0。"""
    return int(led.stage2.register_tax()) if led.stage2 is not None else 0


@pytest.fixture(scope="module", params=KINDS)
def wired(request):
    world = World.synthetic(n_cells=64, seed=2)
    bundle = _bundle(world, 500, request.param)
    with pytest.MonkeyPatch.context() as mp:
        _pin_stage2(mp)
        res = run_day(n_agents=500, seed=2, world=world, ticks=1_440, checkpoint_every=360,
                      ledger=bundle)
    # どちらの道を通ったか(段階 2 が挿さったか)を全部の試験の前に確かめる
    assert (bundle.money.stage2 is not None) == (request.param == "stage2")
    return res, bundle


# ---------------------------------------------------------------- 決定論(T2)
@pytest.mark.parametrize("kind", ["outside", "stage2_parts_none"])
def test_wiring_does_not_change_the_state_hashes_when_goods_processes_are_off(kind):
    """物の過程を切れば、台帳を注入しても checkpoint ハッシュは同じ(帳簿を足すだけ)。

    〔第347・検収 M2〕段階 2 on の道では、部品が全部のとき引き出し・口座の支払い・レジの税で世帯の現金と購入が動く(取り直した
    値: 500 体の 1 日で購入 168 対 169・世帯の現金 3,622,366 対 3,351,439)=「帳簿を足すだけ」は段階 2 on・部品 none
    (初期の預金だけが入る=手順 0 で体の動きが off と同じと確かめた形)で見る。
    """
    world = World.synthetic(n_cells=64, seed=2)
    bundle = _bundle(world, 500, "outside" if kind == "outside" else "stage2")
    kw = dict(ticks=1_440, checkpoint_every=360, processes_disabled=GOODS_PROCESS_IDS)
    with pytest.MonkeyPatch.context() as mp:
        _pin_stage2(mp, parts=() if kind == "stage2_parts_none" else None)
        res = run_day(n_agents=500, seed=2, world=world, ledger=bundle, **kw)
    if kind == "stage2_parts_none":
        assert bundle.money.stage2 is not None and bundle.money.stage2.s2_meter["run"]["endow"]["deposit_rows"] > 0
    else:
        assert bundle.money.stage2 is None
    plain = run_day(n_agents=500, seed=2, n_cells=64, **kw)
    # 10e(E1): 既定の final(behavior-hash)は台帳の外の状態の行(金と物の台帳)を含むので台帳の有無で違う。
    # 「帳簿を足すだけ」は SoA の全列の組み立て(10e より前の final=legacy_combined)で見る
    # 〔第330・RET〕legacy_combined は消した=同じ式を試験の側で組む(GE.soa_combined)
    assert [GE.soa_combined(c) for c in res.checkpoints] == [GE.soa_combined(c) for c in plain.checkpoints]
    assert res.money_end == plain.money_end and res.revenue_end == plain.revenue_end
    assert int(res.column("purchases").sum()) == int(plain.column("purchases").sum())


def test_goods_processes_change_the_world(wired):
    """逆向き: 物の過程を入れると棚が動く(=台帳の有無が世界を変える・C4 後半)。"""
    res, bundle = wired
    runner = res.runner  # type: ignore[attr-defined]
    assert runner.delivery_inbound.n_runs > 0  # 納品便が立つ
    assert runner.waste.n_bin_rows == 0  # 〔11-01 段 2 の 4〕売れ残りの廃棄率は外した(前: 売れ残りがビンへ落ちる)
    assert int(bundle.goods.aggregate_stock().sum()) != int(
        np.asarray(res.world.assets.poi_stock0, dtype=np.int64).sum()  # type: ignore[attr-defined]
    )


@pytest.mark.parametrize("kind", KINDS)
def test_two_wired_runs_are_identical(kind):
    world_a = World.synthetic(n_cells=32, seed=5)
    world_b = World.synthetic(n_cells=32, seed=5)
    with pytest.MonkeyPatch.context() as mp:
        _pin_stage2(mp)
        a = run_day(n_agents=300, seed=5, world=world_a, ticks=1_440, ledger=_bundle(world_a, 300, kind))
        b = run_day(n_agents=300, seed=5, world=world_b, ticks=1_440, ledger=_bundle(world_b, 300, kind))
    assert a.final_hash == b.final_hash
    led_a = a.ledger.money  # type: ignore[attr-defined]
    led_b = b.ledger.money  # type: ignore[attr-defined]
    assert (led_a.stage2 is not None) == (kind == "stage2")
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
    # 店舗の現金 = 売上 − 域外仕入(補充の代金は店舗→外界の sink)。
    # **D-56(就寝抑止)で軌道が変わり、この fixture で初めて 補充 が 1 件成立した**ため、
    # 「店舗は支出しないので売上と一致」は成り立たなくなった。等式を科目で閉じる形に直す
    # (第1陣で店舗が現金を出す口は 域外仕入 だけ=下の科目一覧が証拠)。
    imports = 0
    for f in led.flow_daily:
        imports += led.account_totals(f)["域外仕入"]
    imports += led.account_totals()["域外仕入"]  # 締めていない当日ぶん
    # 〔第347・検収 M2〕段階 2 on はレジの税が店の現金に残り、売上の写しは税抜き=店の現金 = 売上 + 税 − 域外仕入
    # (取り直した値: 500 体の 1 日で 店の現金 134,800 = 売上 122,616 + 税 12,184 − 域外仕入 0)
    tax = _register_tax(led)
    assert (tax > 0) == (led.stage2 is not None)
    assert int(led.balance(BalanceLine.CASH, Sector.STORE).sum()) == res.revenue_end + tax - imports
    assert res.conserved


def test_purchases_are_booked_as_consumption(wired):
    res, bundle = wired
    led = bundle.money
    total = int(
        np.stack(led.flow_daily).sum(axis=0)[
            int(Sector.HOUSEHOLD), int(Sector.STORE), int(AccountCode.CONSUMPTION)
        ]
    )
    # 〔第347・検収 M2〕段階 2 on の消費支出(世帯 → 店)は税込み=売上の写し(税抜き)+ レジの税
    assert total == res.revenue_end + _register_tax(led) > 0
    assert led.n_transfers >= int(res.column("purchases").sum())


def test_check_two_holds_after_the_run(wired):
    res, bundle = wired
    rep = CK.net_worth_equals_real_assets(bundle.money, bundle.goods)
    assert rep.ok, rep.as_text()
    assert CK.flow_matrix_balanced(bundle.money, close=None).ok


def test_census_gate_passes_for_a_wired_day(wired):
    """日次センサスは**締めた日**(day 0)を評価する。

    層2レビュー指摘の固定: ``run_day`` は ``end_of_day`` で日を畳んでからセンサスを回す。
    畳むと取引フロー行列も当日の廃棄も 0 に戻るので、締め後に「現在値」を読むと
    faucet/sink/廃棄が全部 0 の**空虚な行**になりゲートが素通りしていた。``day=0`` を渡すと
    台帳の ``close_for(0)`` から締めが引かれ、締めた日の実数が出る。
    """
    res, bundle = wired
    row = CS.daily_census(bundle.money, bundle.goods, day=res.day_closed)
    assert res.day_closed == 0
    assert row["gate_ok"], row
    assert row["net_worth_ok"] and row["flow_ok"] and row["goods_balanced"]
    assert row["money_supply"] > 0
    # 締めた日の実数が載っている(0 の空虚な行ではない)
    assert row["faucet_total"] > 0
    assert row["waste_g"] > 0


def test_run_result_census_row_is_the_closed_day(wired):
    """``RunResult.census_row`` = 締めた日の行(faucet/sink/廃棄が実数)。"""
    res, bundle = wired
    row = res.census_row
    assert row and res.census_pass, row
    assert int(row["day"]) == res.day_closed == 0
    close = bundle.money.close_for(0)
    goods_close = bundle.goods.close_for(0)
    assert close is not None and goods_close is not None
    # faucet = 来街者持込 + 参入資本(まっさらなランの初日)/ sink = 域外仕入 + 持ち出し
    fs = CK.faucet_sink_totals(bundle.money, close.flow)
    assert row["faucet_total"] == int(sum(fs["FAUCET"].values())) > 0
    assert row["sink_total"] == int(sum(fs["SINK"].values()))
    assert set(fs["FAUCET"]) <= {"来街者持込", "参入資本"}, fs["FAUCET"]
    assert set(fs["SINK"]) <= {"域外仕入", "持ち出し"}, fs["SINK"]
    # 廃棄はその日の搬出質量(締めた瞬間に凍らせた値 = _waste_g_daily の末尾)
    assert row["waste_g"] == float(goods_close["waste_g"]) > 0
    assert row["waste_g"] == bundle.goods.waste_band(days=1).tonnes * 1_000_000.0
    # 締め後に現在値で読むと 0 の空虚な行になる(=固定前の挙動)。同じ関数で再現できる。
    stale = CS.daily_census(bundle.money, bundle.goods)
    assert stale["faucet_total"] == 0 and stale["waste_g"] == 0.0


def test_o_t_logs_of_both_ledgers_are_measured(wired):
    """D-R2-6: 台帳の O(t) ログ(取引ログ・納品ログ)が成長ゲートの実測に載る。"""
    res, _ = wired
    m = res.growth_measured
    for name in ("transfer_log", "delivery_log", "actual_log_raw"):
        assert name in m and m[name] > 0, (name, m)
    assert res.growth_report is not None
    assert {"transfer_log", "delivery_log"} <= {r.name for r in res.growth_report.rows}
    assert not res.growth_report.missing and not res.growth_report.unknown


def test_the_bundle_declaration_survives_the_c7_scale(wired):
    """D-53: **本番規模(390,067 体)でも宣言だけで cap を超えない**(ランは要らない)。

    C7 本番はここで落ちた(``declared_over_cap = ['transfer_log', 'delivery_log']``)——
    リング容量が固定で N に比例せず、宣言投影 28.1 MB / 12.5 MB が cap 6.29 MB / 2.10 MB を
    超えたため。容量を N 比例にした後は cap = 宣言投影で通る。
    """
    from shibuya.foundation.growth import check_growth

    n = 390_067
    led = Ledger(n, 8)
    goods = GoodsLedger.from_pois(
        np.zeros(8, dtype=np.int64), np.full(8, 5), np.full(8, 300), n_agents=n
    )
    decls, measured = LedgerBundle(money=led, goods=goods).growth_parts()
    rep = check_growth(decls, measured, steps=1_440, minutes_per_step=1, n_entities=n)
    assert rep.declared_over_cap == (), rep.as_text()
    assert rep.ok, rep.as_text()
    caps = {r.name: r.cap for r in rep.rows}
    # 〔1-9・K17〕金の輪の係数 3.0 → 6.5 行/体/日: 容量 ceil(6.5 × 390,067)=2,535,436 行 × 24 B(前は 28,084,824)。
    # 目印の列(12 B/行)は別の宣言(金・物とも輪と同じ容量)
    assert caps["transfer_log"] == 60_850_464 and caps["delivery_log"] == 12_482_144
    assert caps["transfer_log_event_ids"] == 30_425_232 and caps["delivery_log_event_ids"] == 9_361_608
    # 小さいラン(``wired`` = 500 体×1 日)も同じ宣言で通る(下限容量の側)
    res, bundle = wired
    assert res.growth_report is not None and res.growth_report.declared_over_cap == ()
    assert bundle.money.n_raw_dropped == 0  # リングが一周していない = 生ログを捨てていない


def test_world_stock_is_a_mirror_of_the_shelf(wired):
    """``world.pois.stock`` は棚(SKU 別)の写し。真値は物の台帳にある。"""
    res, bundle = wired
    world = res.world  # type: ignore[attr-defined]
    assert np.array_equal(
        np.asarray(world.pois.stock, dtype=np.int64), bundle.goods.aggregate_stock()
    )
    assert bundle.goods.sku_balanced()


# ---------------------------------------------------------------- 検算②を checkpoint ごとに
@pytest.mark.parametrize("kind", KINDS)
def test_check_two_holds_at_every_checkpoint(kind):
    """検算②(主検算)は**毎期**成立する(§2.3)——手回しの tick ループで確認する。

    〔第347・検収 M2〕組み立てを通らない=段階 2 on の形は試験の代役の組み立ての物で挿す(``_attach_stage2_by_hand``)。
    """
    world = World.synthetic(n_cells=16, seed=7)
    agents = AgentState(200)
    bundle = _bundle(world, 200, kind)
    if kind == "stage2":
        _attach_stage2_by_hand(bundle, 200)
    bundle.money.attach_household_cash(agents.registry.money)
    schedule = synthesize(200, 7, world.n_cells)
    R_INIT.initialize(agents, world, schedule, ledger=bundle)
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
            action_code=np.full(n, CV.ACT_BUY, dtype=np.int8),
            target_id=pois.astype(np.int32),
            resource_id=space.poi(pois),
            t_notice_ns=np.full(n, C.tick_start_ns(tick), dtype=np.int64),
        )
        plan = C.arbitrate_resources(
            intents, tick, b"salt-ledger", space, world.pois.stock, world.pois.capacity
        )
        R_APPLY.apply(plan.confirmed, plan.losers, agents, world, tick, schedule=schedule,
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
    if kind == "stage2":  # 段階 2 が働いた(初期の預金・レジの税)=空振りしない
        run = bundle.money.stage2.s2_meter["run"]
        assert run["endow"]["deposit_rows"] > 0 and run["tax"]["amount"] > 0, run["tax"]


# ---------------------------------------------------------------- 物の操作(§7.2)
@pytest.mark.parametrize("kind", KINDS)
def test_restock_through_resolve_pays_and_updates_the_mirror(kind):
    """補充は resolve 経由で ``world.pois.stock``(写し)を更新し、域外仕入を計上する。"""
    world = World.synthetic(n_cells=16, seed=11)
    bundle = _bundle(world, 10, kind)
    if kind == "stage2":
        _attach_stage2_by_hand(bundle, 10)
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


@pytest.mark.parametrize("kind", KINDS)
def test_collect_waste_through_resolve(kind):
    world = World.synthetic(n_cells=16, seed=12)
    bundle = _bundle(world, 10, kind)
    if kind == "stage2":
        _attach_stage2_by_hand(bundle, 10)
    world.freeze()
    bundle.goods.to_bin_many(np.array([0, 1]), np.array([3, 2]), tick=1)
    grams = R.collect_waste(world, bundle, None, tick=2)
    assert grams > 0
    assert int(bundle.goods.bins.sum()) == 0
    assert bundle.goods.sku_balanced()


@pytest.mark.parametrize("kind", KINDS)
def test_consume_moves_holdings_into_the_sink(kind):
    """消費は世帯の所持を減らし SKU 別 sink に落ちる(検算①は閉じたまま)。"""
    world = World.synthetic(n_cells=16, seed=14)
    agents = AgentState(5)
    bundle = _bundle(world, 5, kind)
    if kind == "stage2":
        _attach_stage2_by_hand(bundle, 5)
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
@pytest.mark.parametrize("kind", KINDS)
def test_w2_five_thousand_agents_with_the_ledger_wired(kind, monkeypatch):
    """W2: 台帳を結線しても 1 シミュ日の壁時計が予算内(報告値つき)。

    〔第347・検収 M2〕``stage2``=段階 2 on(部品は全部)のラン。T2 の不変は段階 2 on・部品 none で見る(上の試験と同じ理由)。
    """
    _pin_stage2(monkeypatch)
    world = World.synthetic(n_cells=139, seed=1)
    bundle = _bundle(world, 5_000, kind)
    t0 = time.perf_counter()
    res = run_day(n_agents=5_000, seed=1, world=world, ticks=1_440, checkpoint_every=360,
                  ledger=bundle)
    wall = time.perf_counter() - t0
    assert (bundle.money.stage2 is not None) == (kind == "stage2")
    plain = run_day(n_agents=5_000, seed=1, ticks=1_440, checkpoint_every=360, n_cells=139)
    print(
        f"\n[W2 台帳あり] {res.wall_seconds:.2f}s / 台帳なし {plain.wall_seconds:.2f}s "
        f"(上限 600s・報告閾値 {W2_REPORT_SECONDS}s)"
    )
    print("  " + bundle.money.summary())
    print("  " + bundle.goods.summary())
    # T2: **物の過程を切れば**台帳はハッシュを変えない(C4 後半で条件つきになった)
    if kind == "stage2":
        _pin_stage2(monkeypatch, parts=())
    w_goods = World.synthetic(n_cells=139, seed=1)
    b_goods = _bundle(w_goods, 5_000, kind)
    plain_goods = run_day(
        n_agents=5_000, seed=1, world=w_goods, ticks=1_440,
        checkpoint_every=360, ledger=b_goods,
        processes_disabled=GOODS_PROCESS_IDS,
    )
    assert (b_goods.money.stage2 is not None) == (kind == "stage2")
    plain_off = run_day(
        n_agents=5_000, seed=1, ticks=1_440, checkpoint_every=360, n_cells=139,
        processes_disabled=GOODS_PROCESS_IDS,
    )
    assert GE.soa_combined(plain_goods.checkpoints[-1]) == GE.soa_combined(plain_off.checkpoints[-1])  # 10e(E1)・〔第330・RET〕
    assert TG.check(wall <= W2_REPORT_SECONDS, f"W2 台帳あり {wall:.2f}s(報告閾値 {W2_REPORT_SECONDS}s)")
    assert res.conserved and res.min_stock >= 0
    assert int(bundle.money.sector_totals(BalanceLine.CASH).sum()) == 0
    assert CK.net_worth_equals_real_assets(bundle.money, bundle.goods).ok
    assert CS.daily_census(bundle.money, bundle.goods, day=res.day_closed)["gate_ok"]
    assert res.census_pass and res.census_row["faucet_total"] > 0
    assert res.growth_report is not None and res.growth_report.ok
