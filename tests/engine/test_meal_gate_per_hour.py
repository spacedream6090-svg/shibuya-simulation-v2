"""第2波 §2A 項 4: 古典の腕の**食事の門を時間あたりに**(Q48 (a)・指示書 §0-2・§8-2)のテスト。

旧(``per_wake``・既定のまま)は門を起床のたびに引くので、起床の頻度に比例して食べる。``per_hour`` は語 × カレンダー ×
周囲の値を 1 時間あたりの確率 p_h と読み、前回の門からの経過分 Δt で ``1 − (1 − p_h)^(Δt/60)`` に換算する。
見るもの: (a) 分け方に依らない(1 分ずつ 60 回 vs 60 分後に 1 回=1 回以上通る確率 0.1・多数の体の頻度)
(b) 起床の頻度を 2 倍にしても 1 日の食事の回数の期待値がほぼ変わらない(旧は変わる)(c) 方策の中の Δt=範囲内で起きていた分(睡眠・範囲外を数えない)
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
def _bound(meal_gate: str, n: int = 4, hunger=(1, 5, 8, 10)) -> CL.ClassicalPolicy:
    w = World.synthetic(n_cells=9, seed=1)
    a = AgentState(n)
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


def test_policy_counts_only_minutes_awake_in_area():
    """検収後の規則: Δt=前回の門の後に**範囲内で起きていた分**。(i) 60 分起きて 1 回 → p_h (ii) 8 時間眠って起床直後
    → 起床からの分だけ (iii) 範囲外に 3 時間いて戻った直後 → 範囲外を数えない。最初の門もラン開始からの同じ積算。"""
    old = _bound("per_wake")
    new = _bound("per_hour")
    assert old._gate_awake_min is None
    assert new._gate_awake_min.dtype == np.float32 and new._gate_awake_min.nbytes == 4 * 4   # 4 B/体
    old.accrue_awake()                                                    # per_wake は何もしない
    p_word = [old.meal_probability(i, 700)[0] for i in range(4)]
    assert [old.meal_probability(i, 760)[0] for i in range(4)] == p_word  # 旧=語 × 周囲(毎回同じ)
    r = new.agents.registry
    # 最初の門: ラン開始から 0 分 → p=0(任意の定数を置かない)
    assert new.meal_probability(2, 0)[0] == 0.0
    # (i) 60 分起きていて 1 回
    for _ in range(60):
        new.accrue_awake()
    assert new.meal_probability(2, 60)[0] == pytest.approx(CL.meal_gate_interval_p(p_word[2], 60.0))
    assert float(new._gate_awake_min[2]) == 0.0                            # 門を引いたら 0 に戻す
    # (ii) 8 時間眠って、起床直後(起きて 5 分)
    with new.agents.writable():
        r.activity[2] = int(Activity.SLEEPING)
    for _ in range(480):
        new.accrue_awake()
    with new.agents.writable():
        r.activity[2] = int(Activity.IDLE)
    for _ in range(5):
        new.accrue_awake()
    assert float(new._gate_awake_min[2]) == 5.0
    assert new.meal_probability(2, 600)[0] == pytest.approx(CL.meal_gate_interval_p(p_word[2], 5.0))
    # (iii) 範囲外に 3 時間いて戻った直後(戻って 1 分)
    with new.agents.writable():
        r.transit_state[2] = 2
    for _ in range(180):
        new.accrue_awake()
    with new.agents.writable():
        r.transit_state[2] = 0
    new.accrue_awake()
    assert float(new._gate_awake_min[2]) == 1.0
    assert new.meal_probability(2, 800)[0] == pytest.approx(CL.meal_gate_interval_p(p_word[2], 1.0))
    # 満腹(p_h=0)でも門を引けば積算は 0 に戻る
    for _ in range(30):
        new.accrue_awake()
    assert new.meal_probability(0, 900)[0] == 0.0 and float(new._gate_awake_min[0]) == 0.0
    with pytest.raises(ValueError):
        _bound("per_day")


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
