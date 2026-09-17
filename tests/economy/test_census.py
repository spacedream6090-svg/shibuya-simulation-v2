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


# ------------------------------------------------------------------ 部門軸(第204・D-76 (a))
#: 固定表(``monthly_mer`` の戻り)のキー。部門軸(D-76 (a))・T3(D-85 (a))を足しても
#: **1 つも変えない**(足した鍵は下の比較で除く=固定表そのものは動いていない)。
_MER_FIXED_KEYS = frozenset({
    "month", "days", "faucet", "sink", "internal", "faucet_total", "sink_total",
    "money_supply", "residual", "hoard_entities", "hoard_amount", "per_account",
    "waste_tonnes", "waste_tonnes_per_day", "waste_band_ok", "waste_band",
})
#: 固定表 parquet の列(``write_monthly_mer``)。部門軸は**別ファイル**なのでここは不変。
_MER_FIXED_COLUMNS = [
    "month", "kind", "account", "amount", "money_supply", "residual", "hoard_amount",
]


def _sector_world():
    """faucet(来街者持込・域外雇用主の賃金)・sink(域外仕入・税・持ち出し)・
    internal(消費支出・預金純増)が全部立つ小世界。残差 0。"""
    led = Ledger(6, 3)
    led.endow_households(np.full(6, 20_000, dtype=np.int64), tick=0)
    for d in range(3):
        t = d * 1_440
        led.transfer(EntityRef(Sector.HOUSEHOLD, 0), EntityRef(Sector.STORE, 0),
                     700, AccountCode.CONSUMPTION, t)
        led.transfer(EntityRef(Sector.STORE, 0), EntityRef(Sector.ROW, 0),
                     200, AccountCode.IMPORT_PURCHASE, t + 5)
        led.transfer(EntityRef(Sector.STORE, 0), EntityRef(Sector.GOVERNMENT, 0),
                     50, AccountCode.TAX, t + 6)
        led.transfer(EntityRef(Sector.HOUSEHOLD, 1), EntityRef(Sector.BANK, 0),
                     1_000, AccountCode.DEPOSIT_NET, t + 7)
        led.transfer(EntityRef(Sector.ROW, 0), EntityRef(Sector.HOUSEHOLD, 2),
                     900, AccountCode.WAGE, t + 8)
        led.transfer(EntityRef(Sector.HOUSEHOLD, 3), EntityRef(Sector.ROW, 0),
                     300, AccountCode.CARRY_OUT, t + 9)
        led.on_day_end(d)
    return led


def test_the_sector_axis_comes_from_the_ledgers_own_sectors():
    """部門は**台帳が既に持っている属性**(取引フロー行列の軸 = ``accounts.Sector``)。

    新しい分類を発明していないこと = ``SECTORS`` が ``SECTOR_NAMES`` そのものであること。
    """
    from shibuya.economy.accounts import SECTOR_NAMES

    assert CS.SECTORS == SECTOR_NAMES
    assert len(CS.SECTORS) == len(Sector)
    # 擬似部門(境界の印)は実在の部門と衝突しない。
    assert CS.FAUCET_LABEL not in CS.SECTORS and CS.SINK_LABEL not in CS.SECTORS


def test_the_sector_axis_does_not_move_the_fixed_table(tmp_path):
    """§2.4 の固定表は 1 つも変わらない(キー・値・parquet の列と行順)。"""
    led, g = _world()
    for d in range(5):
        led.transfer(EntityRef(Sector.HOUSEHOLD, 0), EntityRef(Sector.STORE, 0),
                     700, AccountCode.CONSUMPTION, d * 1_440)
        led.transfer(EntityRef(Sector.STORE, 0), EntityRef(Sector.ROW, 0),
                     200, AccountCode.IMPORT_PURCHASE, d * 1_440 + 5)
        led.on_day_end(d)
        g.on_day_end(d)
    mer = CS.monthly_mer(led, g, month=0, days=5)
    assert set(mer) - {"per_sector", "flows", "t3_ok", "t3"} == _MER_FIXED_KEYS
    assert mer["faucet"]["来街者持込"] == 6 * 20_000
    assert mer["sink"]["域外仕入"] == 1_000
    assert mer["internal"]["消費支出"] == 3_500

    import pyarrow.parquet as pq

    t = pq.read_table(CS.write_monthly_mer(mer, tmp_path / "mer.parquet"))
    assert list(t.column_names) == _MER_FIXED_COLUMNS
    # 行順は faucet → sink → internal(科目名の昇順)のまま。
    assert t.column("account").to_pylist() == ["来街者持込", "域外仕入", "消費支出"]
    assert t.column("kind").to_pylist() == ["faucet", "sink", "internal"]


def test_monthly_mer_sectors_is_a_fixed_table(tmp_path):
    """部門軸の長い表(別ファイル)。列は ``SECTOR_FLOW_COLUMNS`` 固定。"""
    import pyarrow.parquet as pq

    led = _sector_world()
    mer = CS.monthly_mer(led, month=0, days=3)

    per = mer["per_sector"]
    assert list(per) == list(CS.SECTORS)  # 0 の部門も落とさない=表の形が動かない
    for v in per.values():
        assert set(v) == {"received", "paid", "net"}
        assert v["net"] == v["received"] - v["paid"]
    assert per["世帯"] == {"received": 122_700, "paid": 6_000, "net": 116_700}
    assert per["店舗"] == {"received": 2_100, "paid": 750, "net": 1_350}
    assert per["銀行"] == {"received": 3_000, "paid": 0, "net": 3_000}
    # 境界は擬似部門へ出したので、外界・政府は部門としては受け取らない。
    assert per["外界"]["net"] == 0 and per["政府"]["net"] == 0

    assert [tuple(r) for r in mer["flows"]] == [
        ("世帯", "店舗", "消費支出", 2_100),
        ("世帯", "銀行", "預金純増", 3_000),
        ("世帯", "sink", "持ち出し", 900),
        ("店舗", "sink", "税", 150),
        ("店舗", "sink", "域外仕入", 600),
        ("faucet", "世帯", "賃金", 2_700),
        ("faucet", "世帯", "来街者持込", 120_000),
    ]

    path = CS.write_monthly_mer_sectors(mer, tmp_path / "sectors.parquet")
    assert path.name == "sectors.parquet"
    t = pq.read_table(path)
    assert list(t.column_names) == list(CS.SECTOR_FLOW_COLUMNS)
    assert t.num_rows == len(mer["flows"])
    assert t.column("kind").to_pylist() == [
        "internal", "internal", "sink", "sink", "sink", "faucet", "faucet",
    ]
    assert t.column("from_sector").to_pylist()[-1] == "faucet"
    assert set(t.column("month").to_pylist()) == {0}
    assert sum(t.column("amount").to_pylist()) == sum(r[3] for r in mer["flows"])


def test_an_empty_sector_table_still_has_the_columns(tmp_path):
    """取引が 1 件も無い月でも列は落ちない(Parquet の追記が壊れないため)。"""
    import pyarrow.parquet as pq

    mer = CS.monthly_mer(Ledger(2, 1), month=3)
    assert mer["flows"] == []
    assert all(v["net"] == 0 for v in mer["per_sector"].values())
    t = pq.read_table(CS.write_monthly_mer_sectors(mer, tmp_path / "empty.parquet"))
    assert list(t.column_names) == list(CS.SECTOR_FLOW_COLUMNS) and t.num_rows == 0


def test_flow_rows_sum_to_the_faucet_sink_totals_per_kind():
    """検算: 区分ごとの ``flows`` 合計 = 科目別 faucet/sink/internal の合計。"""
    led = _sector_world()
    mer = CS.monthly_mer(led, month=0, days=3)
    by_kind: dict[str, dict[str, int]] = {}
    for src, dst, account, amount in mer["flows"]:
        kind = CS.flow_row_kind(src, dst, account)
        by_kind.setdefault(kind, {})
        by_kind[kind][account] = by_kind[kind].get(account, 0) + int(amount)
    assert by_kind["faucet"] == mer["faucet"]
    assert by_kind["sink"] == mer["sink"]
    assert by_kind["internal"] == mer["internal"]
    # 区分は台帳側の集計器と同じ答えになる(二重管理していない)。
    fs = CK.faucet_sink_totals(led, np.sum(np.stack(led.flow_daily), axis=0))
    for kind, table in by_kind.items():
        assert table == fs[kind.upper()]


def test_sector_net_sums_to_faucet_minus_sink():
    """検算: ``Σ_部門 net = faucet 合計 − sink 合計``(境界を擬似部門へ出したから成り立つ)。"""
    led = _sector_world()
    mer = CS.monthly_mer(led, month=0, days=3)
    total_net = sum(v["net"] for v in mer["per_sector"].values())
    assert total_net == mer["faucet_total"] - mer["sink_total"] == 121_050


def test_sector_net_total_equals_the_money_supply_increase():
    """検算: 残差 0 の台帳では ``Σ_部門 net`` = 貨幣供給量の増分。"""
    assert Ledger(6, 3).money_supply() == 0, "_sector_world は期首 M=0 の台帳から作る"
    led = _sector_world()
    mer = CS.monthly_mer(led, month=0, days=3)
    assert mer["residual"] == 0
    assert sum(v["net"] for v in mer["per_sector"].values()) == led.money_supply() == 121_050
