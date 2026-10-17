"""第 1 期 1-1 時計 T0: 時間の定数の値と関係・換算の関数・旧い名との同値(``core.time_consts``)。"""

from __future__ import annotations

import ast
import doctest
from pathlib import Path

import pytest

from shibuya.core import time_consts as TC
from shibuya.core import types as TY

ROOT = Path(__file__).resolve().parents[3]


def test_values():
    assert TC.NS_PER_SECOND == 1_000_000_000
    assert TC.SECONDS_PER_MINUTE == 60
    assert TC.MINUTES_PER_HOUR == 60
    assert TC.HOURS_PER_DAY == 24
    assert TC.SECONDS_PER_HOUR == 3_600
    assert TC.MINUTES_PER_DAY == 1_440
    assert TC.SECONDS_PER_DAY == 86_400
    assert TC.STEP_SECONDS == 60
    assert TC.STEPS_PER_HOUR == 60
    assert TC.STEPS_PER_DAY == 1_440
    assert TC.NS_PER_STEP == 60 * 10**9
    assert TC.CLOCK_KIND == "steps"
    for name in TC.__all__:
        v = getattr(TC, name)
        if not callable(v) and not isinstance(v, str):
            assert type(v) is int, name  # 整数だけ(float の定数を置かない=置き換えで型が変わらない)


def test_relations():
    assert TC.SECONDS_PER_HOUR == TC.SECONDS_PER_MINUTE * TC.MINUTES_PER_HOUR
    assert TC.MINUTES_PER_DAY == TC.MINUTES_PER_HOUR * TC.HOURS_PER_DAY
    assert TC.SECONDS_PER_DAY == TC.SECONDS_PER_HOUR * TC.HOURS_PER_DAY
    assert TC.STEPS_PER_DAY * TC.STEP_SECONDS == TC.SECONDS_PER_DAY
    assert TC.STEPS_PER_HOUR * TC.STEP_SECONDS == TC.SECONDS_PER_HOUR
    assert TC.NS_PER_STEP == TC.STEP_SECONDS * TC.NS_PER_SECOND
    assert TC.STEPS_PER_DAY == TC.STEPS_PER_HOUR * TC.HOURS_PER_DAY


def test_old_names_are_the_same_values():
    """``core.types`` の旧い名は残し、値は新しい定数と同じ(再輸出か同じ値の別名)。"""
    assert TY.DEFAULT_TICK_SECONDS == TC.STEP_SECONDS
    assert TY.MINUTES_PER_SIM_DAY == TC.STEPS_PER_DAY == TC.MINUTES_PER_DAY
    assert TY.NS_PER_SECOND is TC.NS_PER_SECOND or TY.NS_PER_SECOND == TC.NS_PER_SECOND
    assert TY.SECONDS_PER_MINUTE == TC.SECONDS_PER_MINUTE
    for name in ("DEFAULT_TICK_SECONDS", "MINUTES_PER_SIM_DAY", "NS_PER_SECOND", "SECONDS_PER_MINUTE", "SimTime"):
        assert name in TY.__all__, name
    assert TY.SimTime is int


def test_module_level_aliases_elsewhere_are_the_same_value():
    """置き換えで再輸出にした各モジュールの ``MINUTES_PER_DAY`` ほか(読み手が名で引く)は同じ値。"""
    import importlib

    weekly, growth, activity, growth_decl, scheduler, civic, goods_flow, logistics, opening, actual_log = (
        importlib.import_module(f"shibuya.{m}") for m in (
            "agents.weekly", "core.growth", "engine.activity", "engine.growth_decl", "engine.scheduler",
            "engine.processes.civic", "engine.processes.goods_flow", "engine.processes.logistics",
            "engine.processes.opening", "world.processes.actual_log"))

    for mod in (weekly, activity, civic, goods_flow, logistics, opening):
        assert mod.MINUTES_PER_DAY == TC.MINUTES_PER_DAY, mod.__name__
    assert growth.MINUTES_PER_SIM_DAY == TC.MINUTES_PER_DAY
    assert growth_decl.TICKS_PER_DAY == actual_log.TICKS_PER_DAY == TC.STEPS_PER_DAY
    assert scheduler.HORIZON_TICKS == TC.STEPS_PER_DAY


def test_seconds_to_steps_rounding_rule():
    """丸めの規則=床(その秒を含む刻み)。整数だけを受ける。"""
    assert TC.seconds_to_steps(0) == 0
    assert TC.seconds_to_steps(59) == 0
    assert TC.seconds_to_steps(60) == 1
    assert TC.seconds_to_steps(119) == 1
    assert TC.seconds_to_steps(86_400) == 1_440
    assert TC.seconds_to_steps(-1) == -1  # −∞ 側
    assert TC.seconds_to_steps(-60) == -1
    assert TC.seconds_to_steps(-61) == -2
    assert TC.seconds_to_steps(90, 30) == 3
    for s in range(-200, 200):
        for w in (1, 7, 30, 60):
            n = TC.seconds_to_steps(s, w)
            assert TC.steps_to_seconds(n, w) <= s < TC.steps_to_seconds(n + 1, w)
            assert TC.seconds_to_steps(TC.steps_to_seconds(n, w), w) == n  # 右逆
    import numpy as np

    assert TC.seconds_to_steps(np.int64(120)) == 2  # numpy の整数は受ける(operator.index)


@pytest.mark.parametrize("bad", [1.5, 60.0, "60", None])
def test_conversions_reject_non_integers(bad):
    with pytest.raises(TypeError):
        TC.seconds_to_steps(bad)
    with pytest.raises(TypeError):
        TC.steps_to_seconds(bad)


@pytest.mark.parametrize("w", [0, -60, True])
def test_conversions_reject_bad_width(w):
    with pytest.raises(ValueError):
        TC.seconds_to_steps(60, w)
    with pytest.raises(ValueError):
        TC.steps_to_seconds(1, w)


def test_doctests():
    assert doctest.testmod(TC).failed == 0


def test_time_consts_imports_only_the_standard_library():
    """層契約: 標準ライブラリだけ(core の最下層=誰からでも import できる)。"""
    tree = ast.parse((ROOT / "src" / "shibuya" / "core" / "time_consts.py").read_text(encoding="utf-8"))
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            mods.add((n.module or "").split(".")[0])
    assert mods <= {"__future__", "operator", "typing"}, mods
