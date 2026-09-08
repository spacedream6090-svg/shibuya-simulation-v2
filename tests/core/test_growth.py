"""core.growth のテスト: **D-R2-6 の 5 欄が正典**+24step→1日/30日外挿。

正典: 世界過程設計書 §6 D-R2-6(per_agent_bytes / per_cell_bytes / per_day_growth /
retention(保持日数+圧縮先) / worst_case_ops_per_tick)。
"""

from __future__ import annotations

import pytest

from shibuya.core import growth as G

#: 24 step × 1 分 = 1/60 シミュ日。
STEPS = G.DEFAULT_SMOKE_STEPS
SIM_DAYS = STEPS / G.MINUTES_PER_SIM_DAY


def _decl(**kw) -> G.GrowthDeclaration:
    base = dict(
        name="actual_log",
        per_agent_bytes=0,
        per_cell_bytes=0,
        per_day_growth="O(1)",
        per_day_growth_coef=100_000.0,
        retention=G.Retention(days=None, target=""),
        worst_case_ops_per_tick=453,
        cap=10_000_000,
    )
    base.update(kw)
    return G.GrowthDeclaration(**base)


# ---------------------------------------------------------------- 必須欄(D-R2-6)
def test_five_canonical_fields_are_required():
    """D-R2-6 の 5 欄はキーワード必須(欠けたら TypeError)。"""
    for missing in (
        "per_agent_bytes",
        "per_cell_bytes",
        "per_day_growth",
        "per_day_growth_coef",
        "retention",
        "worst_case_ops_per_tick",
    ):
        kw = dict(
            name="x",
            per_agent_bytes=0,
            per_cell_bytes=0,
            per_day_growth="O(1)",
            per_day_growth_coef=1.0,
            retention=G.Retention(days=None),
            worst_case_ops_per_tick=1,
            cap=10,
        )
        kw.pop(missing)
        with pytest.raises(TypeError):
            G.GrowthDeclaration(**kw)


def test_old_fields_are_now_optional_records():
    """旧必須欄(unit/bytes_per_unit/growth_per_simday)は任意の記録欄に降格。"""
    d = _decl()
    assert d.unit == "" and d.bytes_per_unit == 0 and d.growth_per_simday == 0.0
    d2 = _decl(unit="record", bytes_per_unit=100, growth_per_simday=1_000)
    row = d2.to_yaml_row()
    assert row["unit"] == "record" and row["bytes_per_unit"] == 100


def test_yaml_row_has_exactly_the_five_canonical_keys():
    row = _decl(per_agent_bytes=12, per_cell_bytes=8, cap_budget_row="S1").to_yaml_row()
    for key in (
        "per_agent_bytes",
        "per_cell_bytes",
        "per_day_growth",
        "retention",
        "worst_case_ops_per_tick",
    ):
        assert key in row, key
    assert row["retention"] == {"days": None, "target": ""}
    assert row["tag"] == "mechanism"
    assert row["cap_budget_row"] == "S1"


def test_retention_requires_a_target_when_bounded():
    """D-R2-6「生ログ保持日数**と圧縮先**」——日数だけの宣言は不完全。"""
    with pytest.raises(ValueError):
        G.Retention(days=7)
    with pytest.raises(ValueError):
        G.Retention(days=0, target="daily_agg")
    r = G.Retention(days=7, target="daily_agg")
    assert "7日" in str(r)


def test_growth_order_validation():
    with pytest.raises(ValueError):
        _decl(per_day_growth="O(N^3)")
    # 併記係数と per_day_growth_coef の食い違いを検出
    with pytest.raises(ValueError):
        _decl(per_day_growth="O(N)+2.5", per_day_growth_coef=1.0, note="x")
    d = _decl(per_day_growth="O(N)+2.5", per_day_growth_coef=2.5)
    assert d.order == "O(N)"


def test_on_t_declaration_requires_a_reason_it_cannot_be_aggregated():
    """D-R2-6「O(N·t) 以上は宣言必須+なぜ集約できないかを記す」。"""
    with pytest.raises(ValueError):
        _decl(per_day_growth="O(N·t)", per_day_growth_coef=1.0)
    ok = _decl(
        per_day_growth="O(N·t)",
        per_day_growth_coef=1.0,
        note="読み出しが全履歴走査(集約不能)",
        cap=10**12,
    )
    assert ok.order == "O(N·t)"


# ---------------------------------------------------------------- 宣言側の外挿
def test_declared_projection_by_order():
    n, days = 1_000, 30
    assert _decl(per_day_growth="O(1)", per_day_growth_coef=10).declared_projected_bytes(
        days, n
    ) == pytest.approx(10 * 30)
    assert _decl(per_day_growth="O(t)", per_day_growth_coef=10).declared_projected_bytes(
        days, n
    ) == pytest.approx(10 * 30 * 31 / 2)
    assert _decl(per_day_growth="O(N)", per_day_growth_coef=10).declared_projected_bytes(
        days, n
    ) == pytest.approx(10 * 1_000 * 30)
    quad = _decl(
        per_day_growth="O(N·t)", per_day_growth_coef=10, note="集約不能の理由", cap=10**15
    )
    assert quad.declared_projected_bytes(days, n) == pytest.approx(10 * 1_000 * 30 * 31 / 2)


def test_declared_over_cap_fails_without_any_measurement():
    """宣言だけで cap を食い破る設計は実測を待たずに落ちる。"""
    decl = _decl(per_day_growth="O(N)", per_day_growth_coef=1_000, cap=1_000)
    rep = G.check_growth((decl,), {"actual_log": 0}, steps=STEPS, n_entities=5_000)
    assert not rep.ok and rep.declared_over_cap == ("actual_log",)
    assert "宣言だけで cap 超過" in rep.as_text()


def test_steady_bytes():
    d = _decl(per_agent_bytes=91, per_cell_bytes=16)
    assert d.steady_bytes(n_agents=5_000, n_cells=139) == 91 * 5_000 + 16 * 139


# ---------------------------------------------------------------- 実測側の外挿(既存の性質)
def test_extrapolation_arithmetic_is_linear():
    """実測 1,666B/24step → 100,000B/日 → 30日 3,000,000B(cap 10MB 内)。"""
    decl = _decl()
    measured = int(round(100_000 * SIM_DAYS))  # ちょうど 100,000B/日 になる実測
    rep = G.check_growth((decl,), {"actual_log": measured}, steps=STEPS, minutes_per_step=1)
    row = rep.rows[0]
    assert rep.sim_days_measured == pytest.approx(SIM_DAYS)
    assert row.measured_bytes_per_simday == pytest.approx(100_000, rel=1e-3)
    assert row.projected_bytes == pytest.approx(3_000_000, rel=1e-3)
    assert row.within_cap and rep.ok
    assert row.measured_over_declared == pytest.approx(1.0, rel=1e-3)


def test_over_cap_fails():
    """二乗爆発(runB 教訓)の検出: 1日 1GB は 30日で cap 10MB を必ず超える。"""
    decl = _decl()
    measured = int(1_000_000_000 * SIM_DAYS)
    rep = G.check_growth((decl,), {"actual_log": measured}, steps=STEPS, minutes_per_step=1)
    assert not rep.ok
    assert rep.over_cap == ("actual_log",)
    assert not rep.rows[0].within_cap
    assert rep.rows[0].headroom_bytes < 0
    assert "NG" in rep.as_text()


def test_retention_window_caps_the_horizon():
    """保持窓 7 日なら 30 日外挿でも 7 日分しか積まない(D-R2-6 の日次集約+保持窓)。"""
    decl = _decl(retention=G.Retention(days=7, target="daily_agg"), cap=1_000_000)
    measured = int(100_000 * SIM_DAYS)  # 100,000B/日 → 7日で 700,000B < cap
    rep = G.check_growth((decl,), {"actual_log": measured}, steps=STEPS, minutes_per_step=1)
    assert rep.rows[0].effective_days == 7
    assert rep.rows[0].projected_bytes == pytest.approx(700_000, rel=1e-3)
    assert rep.ok


def test_missing_and_unknown_measurements_fail():
    decl = _decl()
    rep = G.check_growth((decl,), {}, steps=STEPS)
    assert not rep.ok and rep.missing == ("actual_log",)
    rep2 = G.check_growth((decl,), {"actual_log": 1, "surprise": 2}, steps=STEPS)
    assert not rep2.ok and rep2.unknown == ("surprise",)


def test_over_declared_is_reported_but_not_a_failure():
    """実測が宣言を超えたら「delta 改訂が要る」印だけ立てる(cap 内なら失敗にしない)。"""
    decl = _decl(per_day_growth_coef=1_000)  # 宣言 1,000B/日
    measured = int(100_000 * SIM_DAYS)  # 実測 100,000B/日 = 宣言の 100 倍
    rep = G.check_growth((decl,), {"actual_log": measured}, steps=STEPS)
    assert rep.ok
    assert rep.over_declared == ("actual_log",)
    assert rep.rows[0].measured_over_declared == pytest.approx(100.0, rel=1e-3)


def test_declaration_validation():
    with pytest.raises(ValueError):
        _decl(cap=0)
    with pytest.raises(ValueError):
        _decl(per_agent_bytes=-1)
    with pytest.raises(ValueError):
        _decl(worst_case_ops_per_tick=-1)
    with pytest.raises(TypeError):
        _decl(retention=7)


def test_bad_steps_rejected():
    with pytest.raises(ValueError):
        G.check_growth((_decl(),), {"actual_log": 1}, steps=0)
    with pytest.raises(ValueError):
        G.check_growth((_decl(),), {"actual_log": 1}, n_entities=0)
