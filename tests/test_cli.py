"""shibuya.cli(台帳つき実行入口)の検査。engine↛economy の層契約を守ったまま束ねる。"""

from __future__ import annotations

import numpy as np

from shibuya import cli
from shibuya.economy import entry_capital as EC
from shibuya.economy.accounts import BalanceLine, Sector
from shibuya.world.state import World


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
