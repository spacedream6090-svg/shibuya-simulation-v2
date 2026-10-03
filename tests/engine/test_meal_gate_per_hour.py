"""第2波 §2A 項 4: 古典の腕の**食事の門を時間あたりに**(Q48 (a)・指示書 §0-2・§8-2)のテスト。

旧(``per_wake``・既定のまま)は門を起床のたびに引くので、起床の頻度に比例して食べる。``per_hour`` は語 × カレンダー ×
周囲の値を 1 時間あたりの確率 p_h と読み、前回の門からの経過分 Δt で ``1 − (1 − p_h)^(Δt/60)`` に換算する。
見るもの: (a) 分け方に依らない(1 分ずつ 60 回 vs 60 分後に 1 回=1 回以上通る確率 0.1・多数の体の頻度)
(b) 起床の頻度を 2 倍にしても 1 日の食事の回数の期待値がほぼ変わらない(旧は変わる)(c) 方策の中=**第2波 §2B の親の決定でハザードの積算に置き換えた**(各 tick の語の段の p_h で H を積算・満腹・睡眠・範囲外を数えない)
(d) 既定は per_wake=旧の値・切替口・manifest。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import Activity, AgentKind, AgentState
from shibuya.engine import classical as CL
from shibuya.world.state import World

DOC, MD5 = CL.load_activity_prior()
SRC = Path("src/shibuya")


# ================================================================= (a) 分け方に依らない
def test_one_minute_sixty_times_equals_one_hour_once():
    p_h = 0.1
    q = CL.meal_gate_interval_p(p_h, 1.0)
    assert 1.0 - (1.0 - q) ** 60 == pytest.approx(p_h, abs=1e-12)          # 手計算: 60 回で 0.1
    assert CL.meal_gate_interval_p(p_h, 60.0) == pytest.approx(p_h, abs=1e-12)
    assert CL.meal_gate_interval_p(p_h, 0.0) == 0.0 and CL.meal_gate_interval_p(1.0, 5.0) == 1.0
    assert CL.meal_gate_interval_p(0.0, 600.0) == 0.0
    # 多数の体の頻度: 200,000 体 × (1 分 × 60 回)と (60 分 × 1 回)。標準誤差 √(0.1·0.9/2e5)=0.00067 → 許容 ±0.003
    rng = np.random.default_rng(7)
    n = 200_000
    per_min = (rng.random((n, 60)) < q).any(axis=1).mean()
    once = (rng.random(n) < CL.meal_gate_interval_p(p_h, 60.0)).mean()
    assert per_min == pytest.approx(0.1, abs=0.003) and once == pytest.approx(0.1, abs=0.003)
    # 不揃いの間隔(1〜29 分)でも 60 分ぶんで 0.1
    gaps = [1, 7, 29, 3, 20]
    assert 1.0 - np.prod([1.0 - CL.meal_gate_interval_p(p_h, g) for g in gaps]) == pytest.approx(p_h, abs=1e-12)


# ================================================================= (b) 起床の頻度を 2 倍に
def _meals_per_day(gate: str, wake_every_min: int, p_h: float, n: int, seed: int) -> float:
    """合成の 1 日(起きている 16 時間): 起床ごとに門を引く・通ったら食べて 3 時間は満腹(p=0・門は引く)。"""
    rng = np.random.default_rng(seed)
    full_until = np.full(n, -1)
    meals = np.zeros(n, dtype=np.int64)
    for t in range(wake_every_min, 16 * 60 + 1, wake_every_min):  # 起床の回数ぶん(≤ 96)
        hungry = full_until <= t
        p = CL.meal_gate_interval_p(p_h, wake_every_min) if gate == "per_hour" else p_h
        eat = hungry & (rng.random(n) < p)
        meals += eat
        full_until = np.where(eat, t + 180, full_until)
    return float(meals.mean())


def test_doubling_the_wake_frequency_keeps_the_expected_meals():
    """起床 20 分ごと → 10 分ごと。per_hour: 1 日の食事の回数の期待値の差 < 3%(残りは門を引く時刻の離散化=
    Δt の半分の遅れ)/ per_wake: 大きく増える(旧の欠陥)。100,000 体。"""
    n = 100_000
    a = _meals_per_day("per_hour", 20, 0.6, n, 1)
    b = _meals_per_day("per_hour", 10, 0.6, n, 2)
    assert b / a == pytest.approx(1.0, abs=0.03), (a, b)
    c = _meals_per_day("per_wake", 20, 0.6, n, 1)
    d = _meals_per_day("per_wake", 10, 0.6, n, 2)
    assert d / c > 1.08, (c, d)
    # 満腹の戻りが無い形(門を通った回数の期待値)は手計算: 16 時間 × (T/Δ)·(1 − 0.9^(Δ/60))
    exp20 = 48 * CL.meal_gate_interval_p(0.1, 20.0)
    exp10 = 96 * CL.meal_gate_interval_p(0.1, 10.0)
    assert exp10 / exp20 == pytest.approx(1.0, abs=0.01) and 48 * 0.1 * 2 == pytest.approx(96 * 0.1)


# ================================================================= (c) 方策の中
def _bound(meal_gate: str, n: int = 4, hunger=(1, 5, 8, 10), energy: bool = False) -> CL.ClassicalPolicy:
    w = World.synthetic(n_cells=9, seed=1)
    a = AgentState(n, energy_columns=energy)
    with a.writable():
        a.cell[:] = 0
        a.hunger[:] = hunger
        a.age[:] = 30
        a.kind[:] = AgentKind.VISITOR
        a.activity[:] = int(Activity.IDLE)
    pol = CL.ClassicalPolicy(seed=1, prior=CL.ActivityPrior(DOC, "weekday", "kanto"), prior_md5=MD5,
                             meal_gate=meal_gate)
    pol.bind(agents=a, world=w, home_cell=np.full(n, 1), work_cell=np.full(n, 2), school_cell=np.full(n, -1),
             has_work=np.zeros(n, dtype=bool), boundary_agent=np.zeros(0, dtype=np.int64),
             boundary_tick=np.zeros(0, dtype=np.int64))
    return pol


def _factor(pol: CL.ClassicalPolicy, aid: int, tick: int) -> float:
    """その体・時刻のカレンダー × 周囲の係数(``base=1`` のときの門の値=上限 1 の前に 1 を超えない場面で使う)。"""
    return pol._meal_p_word(aid, tick, base=1.0)[0]


def _run(pol: CL.ClassicalPolicy, minutes: int, *, hunger=None, aid: int = 0, sleeping=False, away=False):
    """``minutes`` 分ぶん accrue する(1 tick=1 分)。体 ``aid`` の段・就寝・範囲外をその間だけ置く。"""
    r = pol.agents.registry
    with pol.agents.writable():
        if hunger is not None:
            r.hunger[aid] = hunger
        r.activity[aid] = int(Activity.SLEEPING if sleeping else Activity.IDLE)
        r.transit_state[aid] = 2 if away else 0
    for _ in range(minutes):  # テストの道具
        pol.accrue_awake()


def test_policy_hazard_accrual_by_the_word_stage_of_each_minute():
    """第2波 §2B の親の決定(ハザードの積算): H += −ln(1 − p_h(その tick の段)) × 分/60・門で 1 − exp(−H)。
    (i) ふつう 60 分 → 0.1 (ii) 満腹 120 分のあと ふつう 60 分 → 0.1(1 − 0.9^3 ではない)
    (iii) 空腹 30 分+とても空腹 30 分 → 1 − 0.4^0.5 × 0.1^0.5 (iv) 8 時間眠って起床直後 → 睡眠を数えない
    (v) 範囲外の時間を数えない (vii) per_wake は配列を持たない。係数(カレンダー × 周囲)は旧と同じ順序で掛ける。"""
    old = _bound("per_wake", n=1, hunger=(5,))
    new = _bound("per_hour", n=1, hunger=(5,))
    # (vii) per_wake は配列を持たない・accrue は何もしない・門の値は旧のまま
    assert old._gate_hazard is None and not hasattr(old, "_gate_awake_min")
    old.accrue_awake()
    assert old.meal_probability(0, 700)[0] == pytest.approx(0.1 * _factor(old, 0, 700))
    assert new._gate_hazard.dtype == np.float32 and new._gate_hazard.nbytes == 4   # 4 B/体
    f = _factor(new, 0, 700)
    assert 0.0 < f <= 1.0
    # 最初の門(ラン開始から 0 分)→ 0
    assert new.meal_probability(0, 0)[0] == 0.0
    # (i) ふつう 60 分
    _run(new, 60, hunger=5)
    assert new.meal_probability(0, 700)[0] == pytest.approx(0.1 * f, rel=1e-5)
    assert float(new._gate_hazard[0]) == 0.0                                  # 門で 0 に戻す
    # (ii) 満腹 120 分のあと ふつう 60 分 → 0.1(旧の規則なら 1 − 0.9^3)
    _run(new, 120, hunger=1)
    assert float(new._gate_hazard[0]) == 0.0                                  # 満腹は足さない
    _run(new, 60, hunger=5)
    got = new.meal_probability(0, 700)[0]
    assert got == pytest.approx(0.1 * f, rel=1e-5) and got != pytest.approx((1 - 0.9 ** 3) * f, rel=1e-3)
    # (iii) 空腹 30 分+とても空腹 30 分(段は評価時に「とても空腹」)
    _run(new, 30, hunger=8)
    _run(new, 30, hunger=10)
    want = 1.0 - (0.4 ** 0.5) * (0.1 ** 0.5)
    got, stage = new.meal_probability(0, 700)
    assert stage == 3 and got == pytest.approx(min(1.0, want * f), rel=1e-5)
    # (iv) 8 時間眠って、起床直後(起きて 5 分・ふつう)
    _run(new, 480, hunger=10, sleeping=True)
    assert float(new._gate_hazard[0]) == 0.0
    _run(new, 5, hunger=5)
    assert new.meal_probability(0, 700)[0] == pytest.approx((1 - 0.9 ** (5 / 60)) * f, rel=1e-4)
    # (v) 範囲外に 3 時間いて戻った直後(戻って 1 分)
    _run(new, 180, hunger=10, away=True)
    assert float(new._gate_hazard[0]) == 0.0
    _run(new, 1, hunger=5)
    assert new.meal_probability(0, 700)[0] == pytest.approx((1 - 0.9 ** (1 / 60)) * f, rel=1e-3)
    # 表: 段 → −ln(1 − p)(満腹 0)
    np.testing.assert_allclose(CL._HAZARD_PER_HOUR, -np.log1p(-np.asarray(CL.MEAL_WORD_P)))
    assert CL._HAZARD_PER_HOUR[0] == 0.0
    with pytest.raises(ValueError):
        _bound("per_day")


def _meals_per_day_hazard(wake_every_min: int, n: int, seed: int) -> float:
    """合成の 16 時間: 段は食後 0〜120 分=満腹・〜240 分=ふつう・〜360 分=空腹・以後とても空腹(毎分 H を積算)。
    起床ごとに門(1 − exp(−H))・H を 0 に戻す・通ったら食べる。実装と同じ表 ``_HAZARD_PER_HOUR`` を使う。"""
    rng = np.random.default_rng(seed)
    since = np.full(n, 300)
    H = np.zeros(n)
    meals = np.zeros(n, dtype=np.int64)
    for t in range(1, 16 * 60 + 1):  # テストの道具(分ぶん)
        stage = np.searchsorted([120, 240, 360], since, side="right")
        H += CL._HAZARD_PER_HOUR[stage] / 60.0
        since += 1
        if t % wake_every_min == 0:
            eat = rng.random(n) < -np.expm1(-H)
            H[:] = 0.0
            meals += eat
            since = np.where(eat, 0, since)
    return float(meals.mean())


def test_hazard_rule_keeps_expected_meals_when_waking_twice_as_often():
    """(vi) 起床 20 分ごと → 10 分ごと: 1 日の食事の回数の期待値の差 < 3%(20,000 体)。"""
    a = _meals_per_day_hazard(20, 20_000, 1)
    b = _meals_per_day_hazard(10, 20_000, 2)
    assert b / a == pytest.approx(1.0, abs=0.03), (a, b)


# ================================================================= Q-2B-6(親の決定)
def _energy_policy():
    from shibuya.engine import energy as E
    from shibuya.engine import resolve as R

    pol = _bound("per_hour", n=1, hunger=(8,), energy=True)
    anc, md5 = E.load_anchors()
    lay = E.EnergyLayer(model=E.EnergyModel(anc, md5), n_agents=1)
    lay.poi_intake = np.array([E.INTAKE_SNACK], dtype=np.int8)
    lay.meal_reset = pol.meal_reset_array()
    a = pol.agents
    with a.writable():
        a.age[:] = 30
        a.sex[:] = 0
        a.eer_kcal[:] = 2400.0
        a.since_meal_kcal[:] = 1500.0
    return pol, lay, R


def test_a_meal_resets_the_hazard_but_a_snack_does_not():
    """(a) 空腹で 60 分積んだ後に自宅の食事(予定の実行)→ H=0(次の門は 0 から)。飲食店・範囲外の食事も同じ
    ``resolve._energy_meal`` を通る(``since_meal=0`` の摂取)。(c) 軽食(``since_meal`` を減らすだけ)では H は戻らない。"""
    pol, lay, R = _energy_policy()
    _run(pol, 60, hunger=8)
    h60 = float(pol._gate_hazard[0])
    assert h60 == pytest.approx(-np.log(0.4), rel=1e-5)
    # (c) 軽食: H はそのまま
    with pol.agents.writable():
        R._energy_snack(pol.agents.registry, np.array([0]), np.array([0]), 600, lay)
    assert float(pol._gate_hazard[0]) == pytest.approx(h60) and lay.counts["snacks"] == 1
    # (a) 自宅の食事 → 0
    R.energy_home_meal(pol.agents, lay, np.array([0]), np.array([0]), 600)
    assert float(pol._gate_hazard[0]) == 0.0
    # 範囲外の食事・飲食店の食事でも 0
    for how in ("out", "in"):
        _run(pol, 30, hunger=8)
        assert float(pol._gate_hazard[0]) > 0.0
        if how == "out":
            R.energy_out_of_area_meal(pol.agents, lay, np.array([0]), np.array([1]), np.array([False]), 700)
        else:
            with pol.agents.writable():
                R._energy_meal(pol.agents.registry, np.array([0]), 700, lay, kind="meal_in")
        assert float(pol._gate_hazard[0]) == 0.0
    # per_wake は配列を持たない=戻す先が無い
    assert _bound("per_wake", n=1, hunger=(8,)).meal_reset_array() is None


def test_b_a_full_body_at_the_gate_gets_zero_and_the_hazard_is_cleared():
    """(b) 空腹で 60 分積んだ後、評価の時点で満腹 → p=0・H=0。"""
    pol = _bound("per_hour", n=1, hunger=(8,))
    _run(pol, 60, hunger=8)
    assert float(pol._gate_hazard[0]) > 0.0
    with pol.agents.writable():
        pol.agents.registry.hunger[0] = 1
    p, stage = pol.meal_probability(0, 700)
    assert (p, stage) == (0.0, 0) and float(pol._gate_hazard[0]) == 0.0


@pytest.mark.skipif(not Path("data/world/v2/w17_schedule.parquet").exists(), reason="実資産が無い")
def test_e_no_gate_pass_while_full_in_a_real_per_hour_run():
    """(e) 実資産の classical per_hour のラン(1,500 体)で満腹の段で門を通った回数が 0(5,000 体は記録の計測)。"""
    from shibuya import cli

    res = cli.run(n_agents=1500, seed=1, world_dir="data/world/v2", vocab_version="v3", policy="classical",
                  chooser="classical", meal_gate="per_hour")
    c = res.run_manifest_fields()["classical"]["counts"]
    assert int(c.get("meal", 0)) > 0 and int(c.get("meal_stage:0", 0)) == 0


# ================================================================= (d) ラン
def test_default_is_per_wake_and_the_switch_is_on_the_cli():
    from shibuya.engine.run import run_day

    kw = dict(n_agents=100, seed=2, ticks=1440, vocab_version="v3", policy="classical", chooser="classical",
              hunger_model="energy")
    base = run_day(**kw)
    old = run_day(meal_gate="per_wake", **kw)
    new = run_day(meal_gate="per_hour", **kw)
    assert base.final_hash == old.final_hash and base.llm_calls == old.llm_calls
    # (v) per_hour はランの結果を実際に変える(経路が切れていないこと)
    assert new.final_hash != base.final_hash
    mw = base.run_manifest_fields()["classical"]["counts"].get("meal", 0)
    mh = new.run_manifest_fields()["classical"]["counts"].get("meal", 0)
    assert mw != mh, (mw, mh)
    assert base.run_manifest_fields()["classical"]["meal_gate"]["mode"] == "per_wake"
    assert new.run_manifest_fields()["classical"]["meal_gate"]["mode"] == "per_hour"
    assert list(new.run_manifest_fields()["classical"]["meal_gate"]["word_p"]) == list(CL.MEAL_WORD_P)  # 定数は不変
    with pytest.raises(ValueError):
        run_day(meal_gate="hourly", **{**kw, "ticks": 2})
    assert CL.DEFAULT_MEAL_GATE == "per_wake" and CL.MEAL_GATES == ("per_wake", "per_hour")
    src = (SRC / "cli.py").read_text(encoding="utf-8")
    assert '"--meal-gate"' in src and "meal_gate=str(args.meal_gate)" in src
