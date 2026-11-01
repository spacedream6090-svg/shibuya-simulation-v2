"""第 1 期 1-1 時計 T0(TM7 (d) の準備): ``rng.time_key_from_t_ns`` は ``run_tick_key`` と同じ鍵の値(全刻み・2 日ぶん)。
呼び手はまだ無い(鍵の材料は 10c の counter のまま=結果不変)。"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from shibuya.core import rng as RNG
from shibuya.core import time_consts as TC
from shibuya.engine.systems import boxes as BX

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("day_key0", [0, 1, 20_000])
def test_same_key_for_every_step_of_two_days(day_key0):
    for T in range(2 * TC.STEPS_PER_DAY):
        c = BX.TickCtx.of(T, TC.STEPS_PER_DAY, 60)
        assert RNG.time_key_from_t_ns(day_key0, c.t_ns, 60) == RNG.run_tick_key(day_key0, T, 60)


def test_inside_a_step_maps_to_the_step_that_contains_it():
    t = 5 * TC.NS_PER_STEP
    assert RNG.time_key_from_t_ns(0, t + TC.NS_PER_STEP - 1, 60) == RNG.run_tick_key(0, 5, 60)
    assert RNG.time_key_from_t_ns(0, t + 1, 60) == RNG.run_tick_key(0, 5, 60)


@pytest.mark.parametrize("w", [30, 120])
def test_other_widths(w):
    tpd = TC.SECONDS_PER_DAY // w
    for T in (0, 1, tpd - 1, tpd, 3 * tpd):
        assert RNG.time_key_from_t_ns(3, T * w * TC.NS_PER_SECOND, w) == RNG.run_tick_key(3, T, w)


def test_bad_width():
    with pytest.raises(ValueError):
        RNG.time_key_from_t_ns(0, 0, 0)


def test_no_caller_yet():
    """T0 では呼び手を変えない(鍵の値は不変)=src に呼び手が無い。"""
    hits = []
    for p in (ROOT / "src" / "shibuya").rglob("*.py"):
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Call):
                f = n.func
                name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
                if name == "time_key_from_t_ns":
                    hits.append(p.name)
    assert hits == []
