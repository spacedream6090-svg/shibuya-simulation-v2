"""第 3 期 3-5: ③ の 3 件(D8 空腹と疲れ・A2 体感温度・D9 倒れる)と D18 を体の層へ移しただけ=同じ値(HEAD の式の写しと比べる)。

- 体の刻み: ``engine.body.rules.interoception``(=``BodyModel.step("interoception")`` の sweep・``resolve.advance_body`` が
  書く値)が HEAD の ``advance_body`` と、v1/エネルギー収支 × 二層の段 2 あり/なし × 体の刻み/休みの刻み/ほかの刻みで同じ。
- 体感温度: ``felt_temperature`` が HEAD の写像と、暑さ段 −1〜5・日陰の有無・舞台の外の体で同じ。
- 倒れる: ``collapse_draw`` が HEAD の乱数の引き方と同じ列(同じ流れから)。
- 刻み 0: ``initial_values``・``initial_energy_values`` が HEAD の ``initialize``・``initialize_energy`` の値と同じ。
- 名の写し: ``resolve``・``processes/environment.py``・``processes/salient.py`` の前の名が同じ値を指す(読み手の import は不変)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.engine import resolve as R
from shibuya.engine.body import BodyModel
from shibuya.engine.body import rules as BR
from shibuya.engine.processes import environment as ENV
from shibuya.engine.processes import salient as SAL

from tests.engine.body.body_fixtures import (
    StubModel,
    apply_update,
    copy_registry,
    fake_registry,
    head_advance_body,
    head_collapse,
    head_felt,
    head_stage,
    stub_energy,
)

FIELDS = ("hunger", "fatigue", "since_meal_kcal", "energy_balance")


@pytest.mark.parametrize("energy", [False, True], ids=["v1", "energy"])
@pytest.mark.parametrize("ac", [False, True], ids=["no_activity", "activity"])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_interoception_equals_head_over_a_day(energy, ac, seed):
    rng = np.random.default_rng(seed)
    r_head = fake_registry(400, rng, energy=energy, activity_columns=ac)
    r_new = copy_registry(r_head)
    en = stub_energy() if energy else None
    for t in range(0, 181):  # 体の刻み(0・30・…)・休みの刻み(10・20・…)・ほかの刻みを全部通る
        head_advance_body(r_head, t, en, ac)
        apply_update(r_new, BR.interoception(r_new, t, energy=en, activity_columns=ac))
        for f in FIELDS:
            if hasattr(r_head, f):
                assert np.array_equal(getattr(r_head, f), getattr(r_new, f)), (t, f)
                assert getattr(r_head, f).dtype == getattr(r_new, f).dtype
        if t % 7 == 3:  # 外の書き手(活動の変化・食事・休憩)を混ぜる
            k = rng.integers(0, 400, 25)
            for rr in (r_head, r_new):
                rr.activity[k] = (rr.activity[k] + 1) % 8
                rr.fatigue[k[:5]] = np.maximum(rr.fatigue[k[:5]].astype(np.int16) - 3, 0).astype(np.uint8)
                if energy:
                    rr.since_meal_kcal[k[5:10]] = 0.0
                    rr.hunger[k[5:10]] = 1


def test_the_sweep_model_writes_the_same_as_the_pure_rule():
    """``BodyModel(arm="sweep").step`` は純関数の値をそのまま返す(計器を数えるだけ)。"""
    rng = np.random.default_rng(5)
    r = fake_registry(300, rng, energy=True, activity_columns=True)
    bm = BodyModel(300, arm="sweep")
    for t in (0, 10, 29, 30):
        a = BR.interoception(r, t, energy=stub_energy(), activity_columns=True)
        b = bm.step("interoception", r, t, energy=stub_energy(), activity_columns=True)
        for f in ("fatigue", "hunger", "since_meal", "spent", "fatigue_ids", "hunger_ids"):
            x, y = getattr(a, f), getattr(b, f)
            assert (x is None and y is None) or np.array_equal(x, y), (t, f)


@pytest.mark.parametrize("stage", [-1, 0, 1, 2, 3, 4, 5])
def test_felt_temperature_equals_head(stage):
    rng = np.random.default_rng(stage + 10)
    n_cells = 40
    shade = rng.random(n_cells) < 0.4
    cell = rng.integers(-1, n_cells, 2_000).astype(np.int32)
    got = BodyModel.felt_temperature(stage, None if stage < 0 else shade, cell, n_cells)
    assert got.dtype == np.uint8
    assert np.array_equal(got, head_felt(stage, shade, cell, n_cells))
    cells = BodyModel.felt_cells(stage, None if stage < 0 else shade, n_cells)
    assert cells.shape == (n_cells + 1,) and np.array_equal(cells[BR.felt_columns(cell, n_cells)], got)


def test_collapse_draw_equals_head_on_the_same_stream():
    from shibuya.core.rng import run_tick_key, stream

    rng = np.random.default_rng(4)
    cell = rng.integers(-1, 30, 5_000).astype(np.int32)
    hits = 0
    for t in range(0, 1440):
        key = run_tick_key(0, t, 60)
        a = head_collapse(stream(1, "world.salient.counter", 0, key), 50.0, 5_000, 60, cell)
        b = BodyModel.collapse_draw(stream(1, "world.salient.counter", 0, key), 50.0, 5_000, 60, cell)
        assert np.array_equal(a, b), t
        hits += int(a.size)
    assert hits > 10  # 負の対照: 引いた(空の列どうしだけを比べていない)


def test_initial_values_equal_head():
    init = BodyModel(7).initial(7)
    for name, want in (("hunger", 2), ("fatigue", 2), ("thermal", 5)):
        v = getattr(init, name)
        assert v.dtype == np.uint8 and np.array_equal(v, np.full(7, want, dtype=np.uint8))
        assert np.array_equal(init.stages[f"{name}_stage"], head_stage(v))
    rng = np.random.default_rng(8)
    eer = rng.uniform(800, 3000, 50).astype(np.float32)
    m = StubModel()
    e = BodyModel(50).initial(energy=stub_energy(), eer=eer)
    since = m.initial_since_meal(eer)
    assert np.array_equal(e.since_meal, since)
    want_h = m.hunger_copy(m.stage_of(since, eer))
    assert np.array_equal(e.hunger, want_h) and np.array_equal(e.stages["hunger_stage"], head_stage(want_h))


def test_moved_names_point_to_the_same_values():
    """前の場所の名(``resolve``・``environment``・``salient``)は体の層の値を写して出す(読み手の import は変えない)。"""
    assert (R.BODY_TICK_PERIOD, R.SLEEP_FATIGUE_RELIEF, R.ACTIVITY_REST_PERIOD_TICKS, R.ACTIVITY_REST_FATIGUE_RELIEF) \
        == (30, 2, 10, 1) == (BR.BODY_TICK_PERIOD, BR.SLEEP_FATIGUE_RELIEF, BR.ACTIVITY_REST_PERIOD_TICKS,
                              BR.ACTIVITY_REST_FATIGUE_RELIEF)
    assert (R.REST_FATIGUE_RELIEF, R.BUY_HUNGER_RELIEF) == (3, 4)  # 行為の効果は resolve に残した
    assert ENV.HEAT_STAGE_TO_THERMAL == (2, 4, 6, 8, 10) == BR.HEAT_STAGE_TO_THERMAL
    assert ENV.SHADE_FACTOR == 0.86 == BR.SHADE_FACTOR and ENV.FALLBACK_THERMAL == 5 == BR.FALLBACK_THERMAL
    assert SAL.COLLAPSE_PER_10K_PER_DAY == 3.0 == BR.COLLAPSE_PER_10K_PER_DAY
    for mod, names in ((R, ("BODY_TICK_PERIOD", "SLEEP_FATIGUE_RELIEF", "ACTIVITY_REST_PERIOD_TICKS",
                            "ACTIVITY_REST_FATIGUE_RELIEF")),
                       (ENV, ("HEAT_STAGE_TO_THERMAL", "SHADE_FACTOR", "FALLBACK_THERMAL")),
                       (SAL, ("COLLAPSE_PER_10K_PER_DAY",))):
        assert set(names) <= set(mod.__all__), mod.__name__


def test_negative_a_changed_rule_is_seen_by_the_ruler(monkeypatch):
    """負の対照: 体の規則の値を 1 つ変えると HEAD の写しと食い違う(物差しが空回りしていない)。"""
    monkeypatch.setattr(BR, "SLEEP_FATIGUE_RELIEF", 3)
    rng = np.random.default_rng(1)
    r_head = fake_registry(400, rng, energy=False, activity_columns=False)
    r_new = copy_registry(r_head)
    head_advance_body(r_head, 30)
    apply_update(r_new, BR.interoception(r_new, 30))
    assert not np.array_equal(r_head.fatigue, r_new.fatigue)
