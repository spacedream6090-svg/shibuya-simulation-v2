"""日次(軽量)センサス・月次 MER・ゲートのテスト(境界・経済設計書 §2.4)。"""

from __future__ import annotations

import numpy as np

from shibuya.economy import census as CS
from shibuya.economy import checks as CK
from shibuya.economy.accounts import AccountCode, Sector
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import Ledger
from shibuya.engine.ledger_api import EntityRef


def _world(n_h: int = 6, n_s: int = 3):
    led = Ledger(n_h, n_s)
    led.endow_households(np.full(n_h, 20_000, dtype=np.int64), tick=0)
    g = GoodsLedger.from_pois(np.arange(n_s) % 3, np.full(n_s, 20), np.full(n_s, 500))
    return led, g


def test_light_census_has_only_residual_and_money_supply():
    """§2.4「日次(軽量): 残差・貨幣供給量のみ」。"""
    led, _ = _world()
    row = CS.daily_census(led, light=True)
    assert set(row) == set(CS.LIGHT_COLUMNS)
    assert row["money_supply"] == 6 * 20_000


def test_daily_census_row_has_the_fixed_columns():
    led, g = _world()
    led.transfer_many(int(Sector.HOUSEHOLD), np.arange(3), int(Sector.STORE),
                      np.zeros(3, np.int64), np.full(3, 500),
                      int(AccountCode.CONSUMPTION), 10)
    g.sell_many(np.arange(3) % 3, tick=10)
    row = CS.daily_census(led, g)
    assert set(row) == set(CS.DAILY_COLUMNS)
    assert row["gate_ok"] and row["net_worth_ok"] and row["flow_ok"] and row["goods_balanced"]
    assert row["faucet_total"] == 6 * 20_000  # 初期財布(来街者持込)
    assert row["shelf_units"] == 60 - 3


def test_gate_fails_on_a_large_residual():
    led, g = _world()
    led.transfer(EntityRef(Sector.HOUSEHOLD, 0), EntityRef(Sector.STORE, 0),
                 19_000, AccountCode.RESIDUAL, 5)
    rep = CK.check_all(led, g)
    gate = CS.census_gate(rep, g, day=0)
    assert not gate.ok
    assert any("残差" in r for r in gate.reasons)
    assert "FAIL" in gate.as_text()
    assert CS.daily_census(led, g)["gate_ok"] is False


def test_gate_fails_on_a_goods_stocktake_difference():
    led, g = _world()
    g.sell_many(np.array([0]), tick=1)
    g.stocktake(0, 0, -10, tick=2)
    gate = CS.census_gate(CK.check_all(led, g), g, day=0)
    assert not gate.ok and any("棚卸差異" in r for r in gate.reasons)


def test_daily_census_parquet_roundtrip(tmp_path):
    import pyarrow.parquet as pq

    led, g = _world()
    rows = []
    for d in range(3):
        led.transfer(EntityRef(Sector.HOUSEHOLD, d), EntityRef(Sector.STORE, 0),
                     500, AccountCode.CONSUMPTION, d * 1_440)
        g.sell_many(np.array([0]), tick=d * 1_440)
        close = led.on_day_end(d)
        g.on_day_end(d)
        rows.append(CS.daily_census(led, g, close=close, day=d))
    path = CS.write_daily_census(rows, tmp_path / "census" / "daily.parquet")
    table = pq.read_table(path)
    assert table.num_rows == 3
    assert list(table.column_names) == list(CS.DAILY_COLUMNS)
    assert table.column("day").to_pylist() == [0, 1, 2]


def test_monthly_mer_is_a_fixed_table(tmp_path):
    """§2.4 月次 = EVE 型 MER(科目別 faucet/sink・貨幣供給量・残差・退蔵残高)。"""
    led, g = _world()
    for d in range(5):
        led.transfer(EntityRef(Sector.HOUSEHOLD, 0), EntityRef(Sector.STORE, 0),
                     700, AccountCode.CONSUMPTION, d * 1_440)
        led.transfer(EntityRef(Sector.STORE, 0), EntityRef(Sector.ROW, 0),
                     200, AccountCode.IMPORT_PURCHASE, d * 1_440 + 5)
        g.to_bin_many(np.array([0]), np.array([1]), tick=d * 1_440 + 6)
        g.collect_waste(None, tick=d * 1_440 + 7)
        led.on_day_end(d)
        g.on_day_end(d)
    mer = CS.monthly_mer(led, g, month=0, days=5)
    assert mer["faucet"]["来街者持込"] == 6 * 20_000
    assert mer["sink"]["域外仕入"] == 1_000
    assert mer["internal"]["消費支出"] == 3_500
    assert mer["per_account"]["消費支出"] == 3_500
    assert mer["money_supply"] == led.money_supply()
    assert "waste_tonnes_per_day" in mer and mer["waste_band_ok"] is False  # 合成小世界なので band 外
    path = CS.write_monthly_mer(mer, tmp_path / "mer.parquet")
    import pyarrow.parquet as pq

    t = pq.read_table(path)
    assert set(t.column("kind").to_pylist()) <= {"faucet", "sink", "internal"}
    assert "来街者持込" in t.column("account").to_pylist()
