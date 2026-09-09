"""**T9 診断行**(運用設計書 §1.4「診断行 4 列(繰り延べ/昇格/縮退/抑止)+ **保存則 2 検算**の
存在(全ラン)」・§1.2 出力節「診断行4列+保存則2検算がなければ較正・holdoutに使わない」)。

固定するのは**存在と数値が入ること**であって、値そのものではない。列名は既存の正典
(``manifest.schema.DIAG_COLUMNS`` / ``CONSERVATION_CHECKS``)をそのまま使う。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya import cli
from shibuya.engine.run import DIAG_DAY_ROWS, DIAG_RUN_COLUMNS, run_day
from shibuya.manifest.schema import CONSERVATION_CHECKS, DIAG_COLUMNS
from shibuya.world.state import World

from .conftest import WORLD_DIR, real_data


def test_t9_the_four_diagnostic_columns_exist_in_the_run_table():
    res = run_day(n_agents=800, seed=2, ticks=60, checkpoint_every=60, n_cells=25)
    assert DIAG_COLUMNS == ("deferred", "promoted", "degraded", "suppressed")
    for col in DIAG_COLUMNS:
        assert col in DIAG_RUN_COLUMNS
        assert col in DIAG_DAY_ROWS
        assert res.column(col).shape == (res.ticks,)
        assert np.issubdtype(res.column(col).dtype, np.integer)
    day = res.diagnostics_day()
    assert all(col in day for col in DIAG_COLUMNS)
    # アービタ側(クラス別)にも同じ 4 列が立っている
    assert set(res.arbiter_counters) == set(DIAG_COLUMNS)
    for col, per_class in res.arbiter_counters.items():
        assert sum(int(v) for v in per_class.values()) == int(res.column(col).sum()), col


def test_t9_the_four_columns_actually_carry_numbers():
    """「存在するが常にゼロ」を弾く: 需要 > 予算のランでは繰り延べ・縮退が立つ。"""
    res = run_day(n_agents=5_000, seed=1, ticks=120, checkpoint_every=120, n_cells=139)
    day = res.diagnostics_day()
    assert day["deferred"] > 0, day
    assert day["degraded"] > 0, day
    assert set(DIAG_DAY_ROWS) <= set(day)


def test_t9_two_conservation_checks_are_present_and_pass():
    """保存則 2 検算 = 取引残差(``residual``)と在庫残差(``goods_residual_units``)。"""
    assert CONSERVATION_CHECKS == (
        "conservation_transfer_residual",
        "conservation_stock_residual",
    )
    res = cli.run(n_agents=400, seed=3, world_dir=None, n_cells=16, ticks=120, checkpoint_every=60)
    assert res.conserved, (res.money_start, res.money_end, res.revenue_end, res.fares_paid)
    row = res.census_row
    assert row, "センサス行が無い(保存則検算が記録されていない)"
    assert "residual" in row and "goods_residual_units" in row
    assert int(row["residual"]) == 0
    assert int(row["goods_residual_units"]) == 0
    assert res.census_pass


@real_data
@pytest.mark.slow
def test_t9_on_the_real_world_smoke(capsys):
    res = cli.run(
        n_agents=5_000, seed=1, world_dir=WORLD_DIR, ticks=24, checkpoint_every=24
    )
    day = res.diagnostics_day()
    with capsys.disabled():
        print("\n[T9 実データ] " + " ".join(f"{k}={day[k]:,.0f}" for k in DIAG_COLUMNS))
    assert all(k in day for k in DIAG_COLUMNS)
    assert res.conserved
    assert res.census_row and res.census_pass
    assert int(res.census_row["residual"]) == 0


def test_t9_manifest_fields_survive_for_the_run_record():
    """診断行と一緒に manifest へ載る同定欄(§1.2 出力節)。"""
    res = run_day(n_agents=200, seed=5, ticks=30, checkpoint_every=30, n_cells=9)
    fields = res.run_manifest_fields()
    for key in ("registry_hash", "template_sha256", "catalog_sha16", "process_ids"):
        assert key in fields, fields
