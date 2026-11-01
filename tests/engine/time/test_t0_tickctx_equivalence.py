"""第 1 期 1-1 時計 T0: ``TickCtx`` の ``t_ns``・``tod_s`` と 1-0 の ``T``・``td``・``day`` の同値(全刻み・2 日ぶん)と、
進行役がランの設定の幅を渡していること。"""

from __future__ import annotations

import pytest

from shibuya.core import time_consts as TC
from shibuya.core import types as TY
from shibuya.engine.systems import boxes as BX

TPD = TC.STEPS_PER_DAY


def test_all_steps_of_two_days():
    for T in range(2 * TPD):
        c = BX.TickCtx.of(T, TPD, 60)
        assert c.T == T and c.td == T % 1440 and c.day == T // 1440
        assert c.tod_s == c.td * 60
        assert c.t_ns == T * 60 * 10**9
        assert TY.t_sim_ns(T) == c.t_ns  # core.types の時刻の型と同じ値
        assert TY.split_t_sim_ns(c.t_ns) == (T, 0)
        assert 0 <= c.tod_s < TC.SECONDS_PER_DAY


def test_default_width_and_the_old_call_form():
    """1-0 の呼び口 ``TickCtx.of(T, tpd)`` は残る(幅の既定は 60 秒=``STEP_SECONDS``)。1-0 の欄の値は前と同じ。"""
    c = BX.TickCtx.of(1441, 1440)
    assert (c.T, c.td, c.day) == (1441, 1, 1)
    assert (c.t_ns, c.tod_s) == (1441 * TC.NS_PER_STEP, 60)
    assert BX.TickCtx(T=None).t_ns is None and BX.TickCtx(T=None).tod_s is None


@pytest.mark.parametrize("w", [1, 30, 60, 300])
def test_other_widths_keep_the_relations(w):
    tpd = TC.SECONDS_PER_DAY // w
    for T in (0, 1, tpd - 1, tpd, 2 * tpd + 7):
        c = BX.TickCtx.of(T, tpd, w)
        assert c.tod_s == c.td * w and c.t_ns == T * w * TC.NS_PER_SECOND
        assert TY.t_sim_ns(T, tick_seconds=w) == c.t_ns


def test_the_conductor_passes_the_run_width(monkeypatch):
    """進行役(``conductor``)は ``RunConfig.tick_seconds`` を幅として渡す(合成の世界・20 体・30 刻み)。"""
    from shibuya.engine.run import run_day

    seen = []
    real = BX.TickCtx.of

    def spy(T, tpd, step_seconds=TC.STEP_SECONDS):  # noqa: ANN001, ANN202
        c = real(T, tpd, step_seconds)
        seen.append((c, int(tpd), int(step_seconds)))
        return c

    monkeypatch.setattr(BX.TickCtx, "of", staticmethod(spy))
    res = run_day(n_agents=20, n_cells=9, ticks=30, seed=1, renderer="stub")
    assert len(seen) == 30
    assert {(tpd, w) for _, tpd, w in seen} == {(TPD, int(res.tick_seconds))} == {(1440, 60)}
    for c, _, _ in seen:
        assert c.t_ns == TY.t_sim_ns(c.T) and c.tod_s == c.td * 60
