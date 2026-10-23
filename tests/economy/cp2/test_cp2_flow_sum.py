"""第 1 期 1-9: 1 日の締めの検算(新しい 1 本)=その日の transfer の額の和 = 流れの表 ``_flow`` の和。

四重記入の検算(既存の ``checks.flow_matrix_balanced``・日次センサスの ``flow_ok``)は今のまま通る(同じ試験の中で見る)。
計器は ``TransferMeter.close_day``(``Ledger.on_day_end`` が呼ぶ)・日次の記録の ``economy.flow_sum_ok``。

- 単体: 預金の 2 脚目・減価償却(自己ループ)・参入資本・複数日で成り立つ・transfer の外で流れの表を書くと落ちる
  (負の対照)・日の途中から再開した台帳(流れの表が戻ってから最初の transfer で起点を決める)。
- ラン: 合成の世界 2 日で毎日成り立つ・既存の四重記入の検算も通る・生ログの日の行の額の和とも合う。
"""

from __future__ import annotations

import numpy as np

from shibuya.economy import census as CS
from shibuya.economy import checks as CK
from shibuya.economy.accounts import AccountCode, Sector
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import Ledger
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.run import run_day
from shibuya.world.state import World

H, S, B, W = int(Sector.HOUSEHOLD), int(Sector.STORE), int(Sector.BANK), int(Sector.ROW)


def _day(led: Ledger, step: int) -> int:
    led.endow_households(np.full(4, 9_000), step)
    led.endow_stores(np.array([7_000, 0]), step)
    led.purchase_many(np.array([0, 1, 1]), np.array([0, 1, 1]), np.array([300, 200, 50]), step + 1)
    led.transfer_many(H, np.array([2]), B, np.zeros(1, np.int64), np.array([1_000]), int(AccountCode.DEPOSIT_NET),
                      step + 2)
    led.transfer_many(B, np.zeros(1, np.int64), H, np.array([2]), np.array([400]), int(AccountCode.DEPOSIT_NET), step + 3)
    led.depreciate(S, np.array([0, 1]), np.array([30, 0]), step + 4)  # 0 の行は口が落とす
    return 4 * 9_000 + 7_000 + 550 + 1_000 + 400 + 30


def test_transfer_sum_equals_the_flow_sum_each_day():
    led = Ledger(4, 2)
    for d in range(3):
        want = _day(led, d * 1_440)
        assert led.meter.day_amount == want == int(led.flow.sum())
        close = led.on_day_end(d)
        day = led.meter.last_day
        assert day["flow_sum_ok"] is True and day["amount"] == day["flow_sum"] == want == int(close.flow.sum())
        assert CK.flow_matrix_balanced(led, close).ok  # 既存の四重記入の検算も通る
    assert led.meter.amount == sum(int(f.sum()) for f in led.flow_daily)


def test_a_flow_write_outside_transfer_is_caught_at_the_close():
    """負の対照: transfer を通さず流れの表を書くと締めの検算が落ちる(計器だけ・締めは止めない)。"""
    led = Ledger(4, 2)
    _day(led, 0)
    led._flow[S, W, int(AccountCode.IMPORT_PURCHASE)] += 5  # transfer の外の書き(AST の試験が静的に禁じる形)
    led.on_day_end(0)
    day = led.meter.last_day
    assert day["flow_sum_ok"] is False and day["flow_sum"] == day["amount"] + 5
    _day(led, 1_440)  # 締めの後は起点が 0 に戻り、次の日は成り立つ
    led.on_day_end(1)
    assert led.meter.last_day["flow_sum_ok"] is True


def test_a_resumed_ledger_sets_the_base_at_the_first_transfer():
    """日の途中から再開した台帳: 流れの表が戻った後の最初の transfer で起点を決める(戻した分は起点に入る)。"""
    a = Ledger(4, 2)
    _day(a, 0)
    b = Ledger(4, 2)
    b._flow[...] = a._flow  # 再開の書き手(resolve.restore_items)が流れの表を戻すのと同じ
    assert b.meter.flow_base is None
    b.endow_households(np.full(4, 9_000), 600)
    b.on_day_end(0)
    assert b.meter.last_day["flow_sum_ok"] is True and b.meter.last_day["amount"] == 36_000


def test_runs_keep_the_check_and_match_the_raw_log():
    world = World.synthetic(n_cells=64, seed=2)
    led = Ledger(300, world.n_poi)
    goods = GoodsLedger.from_pois(np.arange(world.n_poi) % 3, np.asarray(world.pois.stock),
                                  np.asarray(world.pois.price), n_agents=300)
    bundle = LedgerBundle(money=led, goods=goods, census=lambda d: CS.daily_census(led, goods, day=d))
    res = run_day(n_agents=300, seed=2, world=world, ticks=1_440, sim_days=2, checkpoint_every=720, ledger=bundle)
    daily = res.run_manifest_fields()["daily"]
    assert len(daily) == 2
    for d in daily:
        assert d["economy"]["flow_sum_ok"] is True and d["economy"]["rows"] > 0
        assert d["census_row"]["flow_ok"] is True  # 既存の四重記入の検算(日次センサス)
    # 生ログ(保持窓 1 日=最後の日の行が残る)の額の和=最後の日の transfer の額の和
    rows = led.raw_rows()
    last = daily[-1]["economy"]
    assert led.meter.overflow == 0 and rows.shape[0] == last["rows"]
    assert int(rows[:, 5].sum()) == last["amount"] == last["flow_sum"]
