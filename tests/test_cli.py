"""shibuya.cli(台帳つき実行入口)の検査。engine↛economy の層契約を守ったまま束ねる。"""

from __future__ import annotations

from shibuya import cli


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
