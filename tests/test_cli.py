"""shibuya.cli(台帳つき実行入口)の検査。engine↛economy の層契約を守ったまま束ねる。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya import cli
from shibuya.economy import anchors as AN
from shibuya.economy import entry_capital as EC
from shibuya.economy.accounts import BalanceLine, Sector
from shibuya.world.state import World

WORLD_DIR = Path(__file__).resolve().parents[1] / "data" / "world" / "v2"
_HAS_POP = (WORLD_DIR / "w16_population.parquet").exists()


def test_cli_run_builds_ledger_and_census_on_synthetic_world():
    res = cli.run(n_agents=200, seed=3, world_dir=None, n_cells=16, ticks=120, checkpoint_every=60)
    assert res.ledger is not None
    assert res.conserved
    assert res.census_row is not None and res.census_pass
    lo, hi = res.waste_band
    assert 0.0 < lo < hi  # 区ごみ 119.6 t/日の band が報告される(台帳なしの run は (0,0))


def test_cli_main_parses_and_runs(capsys):
    rc = cli.main(["--agents", "100", "--seed", "1", "--world", "__no_such_dir__", "--cells", "9", "--ticks", "30"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "壁時計" in out
    assert "[参入資本]" in out  # D-13: 貨幣供給比の検算行が出る
    assert "[世帯財布]" in out  # C5-a 仕上げ: 世帯側の合計と貨幣供給比を併記


def test_cli_no_population_flag_is_the_lower_bound_control(capsys):
    """(軽-5) ``--no-population`` を cli にも用意する(engine.run と同じ意味)。"""
    rc = cli.main([
        "--agents", "100", "--seed", "1", "--world", "__no_such_dir__",
        "--cells", "9", "--ticks", "30", "--no-population",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "--no-population" in out and "mock 一様" in out


# ---------------------------------------------------------------- D-13 参入資本の按分
def test_default_store_capital_is_apportioned_not_flat():
    """既定は経済センサス按分=カテゴリごとに額が違う(一律 200,000 ではない)。"""
    world = World.synthetic(n_cells=16, seed=3)
    cap = cli.store_capital_array(world, n_agents=5_000)
    assert cap.shape == (world.n_poi,)
    assert len(set(cap.tolist())) >= 2  # 一律でない
    assert cli.STORE_ENTRY_CAPITAL_YEN not in set(cap.tolist())
    expected = EC.store_entry_capital(world.assets.poi_cat, n_agents=5_000)
    assert np.array_equal(cap, expected)


def test_explicit_store_capital_still_overrides_with_a_flat_value():
    world = World.synthetic(n_cells=16, seed=3)
    cap = cli.store_capital_array(world, n_agents=5_000, store_capital_yen=200_000)
    assert cap.tolist() == [200_000] * world.n_poi


def test_bundle_endows_stores_with_the_apportioned_amounts():
    """按分版でも注入は endow_stores(外界 → 店舗・ex nihilo 禁止)のまま。"""
    world = World.synthetic(n_cells=16, seed=3)
    bundle = cli.build_ledger_bundle(world, n_agents=5_000)
    led = bundle.money
    expected = int(cli.store_capital_array(world, n_agents=5_000).sum())
    cash = led.sector_totals(BalanceLine.CASH)
    assert int(cash[int(Sector.STORE)]) == expected
    assert int(cash[int(Sector.ROW)]) == -expected
    store, m, share = EC.ledger_entry_capital_share(led)
    assert store == expected and m == expected and share == 1.0  # 世帯はまだ 0 円


def test_store_capital_report_totals_match_the_array():
    world = World.synthetic(n_cells=16, seed=3)
    rep = cli.store_capital_report(world, n_agents=5_000, household_cash_yen=1_000_000)
    cap = cli.store_capital_array(world, n_agents=5_000)
    assert rep.total_yen == int(cap.sum())
    assert rep.n_stores == world.n_poi
    assert rep.money_supply_yen == rep.total_yen + 1_000_000
    assert 0.0 < rep.share_of_money_supply < 1.0


def test_apportioned_run_still_conserves_and_passes_the_census_gate():
    res = cli.run(n_agents=200, seed=3, world_dir=None, n_cells=16, ticks=120, checkpoint_every=60)
    assert res.conserved and res.census_pass
    assert res.census_row["residual"] == 0
    assert res.census_row["net_worth_ok"] and res.census_row["flow_ok"]
    assert res.census_row["ex_nihilo_ok"]


# ---------------------------------------------------------------- 世帯の初期財布(C5-a 仕上げ)
def test_no_population_keeps_the_mock_wallet_path():
    """母集団を使わないランは C4 と同じ ``Ledger``(mock の一様財布)。"""
    world = World.synthetic(n_cells=16, seed=3)
    assert cli.household_wallets(world, 200, 1, None) is None
    assert cli.household_wallets(world, 200, 1, str(WORLD_DIR), use_population=False) is None
    bundle = cli.build_ledger_bundle(world, 200, world_dir=None)
    assert not isinstance(bundle.money, cli._HouseholdWalletLedger)


def test_wallet_ledger_substitutes_the_amounts_but_keeps_the_transfer_path():
    """注入の経路(外界 → 世帯・科目 CARRY_IN)は変えず、金額だけ差し替える。"""
    wallets = np.array([50_000, 60_000, 70_000], dtype=np.int64)
    led = cli._HouseholdWalletLedger(4, 2, wallets)
    money = np.zeros(4, dtype=np.int64)
    led.attach_household_cash(money)
    led.endow_households(np.array([5_000, 5_000, 5_000, 5_000], dtype=np.int64), 0)
    # 先頭 3 体はアンカー由来・4 体目(母集団の外)は mock のまま
    assert money.tolist() == [50_000, 60_000, 70_000, 5_000]
    cash = led.sector_totals(BalanceLine.CASH)
    assert int(cash[int(Sector.HOUSEHOLD)]) == 185_000
    assert int(cash[int(Sector.ROW)]) == -185_000  # ex nihilo 禁止(外界からの transfer)
    assert int(cash.sum()) == 0


@pytest.mark.skipif(not _HAS_POP, reason="data/world/v2/w16_population.parquet が無い")
def test_wallets_come_from_the_anchor_table_and_are_deterministic():
    """W16 母集団の種別 → ``anchors.initial_wallets``(対数正規)・同 seed 同結果。"""
    world = World.load(WORLD_DIR)
    a = cli.household_wallets(world, 5_000, 1, str(WORLD_DIR))
    b = cli.household_wallets(world, 5_000, 1, str(WORLD_DIR))
    c = cli.household_wallets(world, 5_000, 2, str(WORLD_DIR))
    assert a is not None and a.size == 5_000
    assert np.array_equal(a, b) and not np.array_equal(a, c)
    # mock の一様 2,000〜10,001 円ではない(桁が違う・裾が長い)
    assert int(a.max()) > 10_001
    assert AN.WALLET_MIN <= int(a.min()) and int(a.max()) <= AN.WALLET_MAX
    assert int(np.median(a)) > 10_000


@pytest.mark.skipif(not _HAS_POP, reason="data/world/v2/w16_population.parquet が無い")
def test_wallets_are_not_used_for_a_synthetic_world():
    """実データの母集団を合成小世界へ載せない(engine の判断と同じ)。"""
    small = World.synthetic(n_cells=16, seed=3)
    assert cli.household_wallets(small, 200, 1, str(WORLD_DIR)) is None
