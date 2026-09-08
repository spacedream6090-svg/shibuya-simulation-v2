"""1 シミュ日 mock ランのテスト: **W2**(≤10分)・**P2**(≤5ms/frame)・保存則・診断行・成長宣言。

正典: 予算宣言表 W2「壁時計/シミュ日(Phase 2・5千体・CPU・mock LLM)≤10分」・
P2「≤5ms/フレーム@5千体」・L4「平均10呼/体/日」・§7-5(診断行4列)・D-R2-6(状態成長宣言)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import Activity, ResultCode
from shibuya.engine import growth_decl as GD
from shibuya.engine.run import DIAG_RUN_COLUMNS, main, run_day
from shibuya.engine.scheduler import DIAG_COLUMNS

W2_LIMIT_SECONDS = 600.0
P2_LIMIT_MS = 5.0


# ---------------------------------------------------------------- 小さいラン(CI 常時)
@pytest.fixture(scope="module")
def small_run():
    return run_day(n_agents=500, seed=2, ticks=360, checkpoint_every=120, n_cells=64)


def test_diagnostics_table_has_the_four_required_columns(small_run):
    """T9: 診断行4列(繰り延べ/昇格/縮退/抑止)が全ランに存在する。"""
    assert small_run.diagnostics.shape == (360, len(DIAG_RUN_COLUMNS))
    for col in DIAG_COLUMNS:
        assert col in DIAG_RUN_COLUMNS
        assert small_run.column(col).sum() >= 0
    assert set(small_run.arbiter_counters) == set(DIAG_COLUMNS)


def test_conservation_of_money_and_revenue(small_run):
    """保存則: Σ所持金 + Σ売上 が 1 日を通して不変・在庫は非負。"""
    assert small_run.conserved, (small_run.money_start, small_run.money_end, small_run.revenue_end)
    assert small_run.min_stock >= 0


def test_state_growth_declaration_passes(small_run):
    """D-R2-6: 24step→1日/30日 外挿が予算 M 行の内側。"""
    rep = small_run.growth_report
    assert rep is not None and rep.ok, rep.as_text()
    assert set(small_run.growth_measured) == set(GD.declarations())


def test_engine_actually_moves_and_wakes(small_run):
    assert small_run.llm_calls > 0
    assert int(small_run.column("moved").sum()) > 0
    assert int(small_run.column("candidates").sum()) > 0
    assert int(small_run.column("intents").sum()) > 0


def test_no_undefined_actions_from_the_mock(small_run):
    """MockLLM は必ず 2 行形を返す(B11 実測=書式順守 1.000 の再現)。"""
    assert int(small_run.column("undefined_actions").sum()) == 0


def test_agents_end_in_valid_states(small_run):
    a = small_run.agents  # type: ignore[attr-defined]
    assert np.all((a.cell >= -1) & (a.cell < small_run.n_cells))
    assert np.all((a.activity >= 0) & (a.activity <= int(Activity.RIDING)))
    assert np.all((a.hunger <= 10) & (a.fatigue <= 10) & (a.thermal <= 10))
    assert np.all(a.money >= 0)
    assert np.all(a.last_result <= int(ResultCode.BAD_TARGET))


def test_state_stays_frozen_outside_resolve(small_run):
    a = small_run.agents  # type: ignore[attr-defined]
    w = small_run.world  # type: ignore[attr-defined]
    assert a.frozen and w.frozen
    with pytest.raises(ValueError):
        a.money[0] = 0


def test_cli_runs_and_falls_back_to_a_synthetic_world(capsys, tmp_path):
    rc = main(["--agents", "200", "--seed", "1", "--ticks", "120",
               "--world", str(tmp_path / "missing"), "--cells", "16",
               "--checkpoint-every", "60"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "world=synthetic" in out and "保存則" in out


def test_cli_can_emit_the_growth_yaml(capsys):
    assert main(["--growth-yaml"]) == 0
    out = capsys.readouterr().out
    for key in ("per_agent_bytes", "per_cell_bytes", "per_day_growth",
                "retention", "worst_case_ops_per_tick"):
        assert key in out


# ---------------------------------------------------------------- W2 本番(5,000体×1,440tick)
@pytest.mark.slow
def test_w2_five_thousand_agents_one_sim_day_under_ten_minutes():
    res = run_day(n_agents=5_000, seed=1, ticks=1_440, checkpoint_every=360, n_cells=139)
    print("\n" + res.summary())
    print("  位相[s]: " + ", ".join(f"{k}={v:.3f}" for k, v in res.phase_seconds.items()))
    calls_per_agent = res.llm_calls / res.n_agents
    print(f"  [W2] {res.wall_seconds:.2f}s / 600s ・ [P2] {res.movement_ms_per_tick:.3f} ms/tick "
          f"/ 5 ms ・ [L4] {calls_per_agent:.2f} 呼/体/日 / 10")
    assert res.wall_seconds <= W2_LIMIT_SECONDS
    assert res.movement_ms_per_tick <= P2_LIMIT_MS
    assert res.conserved and res.min_stock >= 0
    assert res.growth_report is not None and res.growth_report.ok
    # L4: 平均 10 呼/体/日 の制御目標(超過しない)
    assert calls_per_agent <= 10.0 + 1e-6
    assert len(res.checkpoints) == 4


@pytest.mark.slow
def test_p2_movement_and_density_under_5ms_at_5000_agents():
    res = run_day(n_agents=5_000, seed=2, ticks=480, checkpoint_every=480, n_cells=139)
    print(f"\n[P2] 移動+密度更新 {res.movement_ms_per_tick:.4f} ms/tick @5,000体 (上限 5 ms)")
    assert res.movement_ms_per_tick <= P2_LIMIT_MS
