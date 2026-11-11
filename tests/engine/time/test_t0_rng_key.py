"""第 1 期 1-1 時計 T0(TM7 (d) の準備): ``rng.time_key_from_t_ns`` は ``run_tick_key`` と同じ鍵の値(全刻み・2 日ぶん)。
〔v3-0a 案 A(指示書 11-04 §2-1)〕呼び手は棚卸し §1-1 の 18 か所だけ(``test_callers_are_the_plan_a_sites``)。
``rng.key_time_from_t_ns`` は今まで材料に入れていた刻みの番号と同じ整数(各か所の同値は ``test_v30a_key_sites.py``)。"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from shibuya.foundation import rng as RNG
from shibuya.foundation import time_consts as TC
from shibuya.runtime.systems import boxes as BX

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


#: 〔v3-0a 案 A〕世界の時刻から鍵・呼びの id・時間帯の材料を作る関数の呼び手(src/shibuya からの相対の道筋 → 呼びの数)。
#: 棚卸し(docs/bench/analysis/v3-2026-11/v30a/README.md §1-1)の 18 か所: #1・#2=decide(1 回の呼びを 2 か所が使う)・
#: #3=decision/port の ``time_key_at``(``time_key_from_t_ns`` を呼ぶ)と ``choose``・#4=decision/layer・#5〜#12=腕の口の
#: ``time_key_at`` 2 か所ずつ・#13=contact/layer の ``time_key_at``・#14〜#18=腕の層の呼びの id。core/rng の 1 本は
#: ``time_key_from_t_ns`` の中。v3-0b で呼び手を足すときはこの表を書き直す。
PLAN_A_CALLERS: dict[str, dict[str, int]] = {
    "key_time_from_t_ns": {
        "foundation/rng.py": 1,
        "runtime/systems/decide.py": 1,
        "mind/judge/decision/layer.py": 1,
        "engine/contact/layer.py": 2,
        "engine/calendar2/layer.py": 1,
        "engine/calendar3/layer.py": 1,
        "engine/duties/layer.py": 1,
    },
    "time_key_from_t_ns": {"foundation/ports/decision.py": 1},
    "time_key_at": {
        "foundation/ports/decision.py": 1,
        "mind/plan/contact_port.py": 2,
        "mind/plan/calendar2_port.py": 2,
        "mind/plan/calendar3_port.py": 2,
        "mind/plan/duties_port.py": 2,
        "engine/contact/layer.py": 1,
    },
    # 刻みの番号から鍵を作る旧の口(``DecisionPort.step_key``)は src から呼ばない(試験と比べる側だけ)
    "step_key": {},
}


def _callers() -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {k: {} for k in PLAN_A_CALLERS}
    base = ROOT / "src" / "shibuya"
    for p in sorted(base.rglob("*.py")):
        rel = p.relative_to(base).as_posix()
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Call):
                f = n.func
                name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
                if name in out:
                    out[name][rel] = out[name].get(rel, 0) + 1
    return out


def test_callers_are_the_plan_a_sites():
    """〔v3-0a 案 A〕呼び手は棚卸し §1-1 の 18 か所だけ(足すと落ちる・消しても落ちる)。"""
    assert _callers() == PLAN_A_CALLERS


def test_key_time_is_the_step_number():
    """〔v3-0a 案 A〕``key_time_from_t_ns`` は刻みの頭の時刻から今の刻みの番号を返す(全刻み・2 日ぶん・ほかの幅・刻みの中は床)。"""
    for T in range(2 * TC.STEPS_PER_DAY):
        c = BX.TickCtx.of(T, TC.STEPS_PER_DAY, 60)
        assert RNG.key_time_from_t_ns(c.t_ns, 60) == T
    for w in (1, 7, 30, 120, 300):
        tpd = TC.SECONDS_PER_DAY // w
        for T in (0, 1, tpd - 1, tpd, tpd + 1, 2 * tpd - 1, 2 * tpd, 3 * tpd + 5):
            assert RNG.key_time_from_t_ns(BX.TickCtx.of(T, tpd, w).t_ns, w) == T
    assert RNG.key_time_from_t_ns(5 * TC.NS_PER_STEP + TC.NS_PER_STEP - 1, 60) == 5
    assert RNG.key_time_from_t_ns(-1, 60) == -1  # 床(負の時刻は前の刻み=``core.types.split_t_sim_ns`` と同じ)
    for bad in (0, -60):
        with pytest.raises(ValueError):
            RNG.key_time_from_t_ns(0, bad)
