"""p_notice: §3.1 の 2 段ヒル型(TTPF+社会伝播)・検算表・ablation A0-A4・P7 予算。"""

from __future__ import annotations

import time

import numpy as np
import pytest

from shibuya.perception import p_notice as P

#: §3.1 の検算表(d50=40 m・前方・昼・疎・手空き)。
CONTRACT_TABLE = {
    10: 0.9995, 20: 0.945, 40: 0.500, 60: 0.217, 80: 0.108, 100: 0.061, 200: 0.010,
}


def test_contract_table_is_reproduced():
    """§3.1「d50=40 mのP1: 10 m 0.9995 / … / 200 m 0.010(親再計算で一致)」。"""
    d = np.array(sorted(CONTRACT_TABLE), dtype=np.float64)
    got = P.p1_primary(d, P.D50_DEFAULT_M)
    want = np.array([CONTRACT_TABLE[int(x)] for x in d])
    assert np.allclose(got, want, atol=5e-4), dict(zip(d.tolist(), np.round(got, 4).tolist()))
    # 3 桁での一致(表の丸め幅)
    assert np.allclose(np.round(got, 3), np.round(want, 3), atol=1e-9)


def test_ttpf_formula_constants():
    """``s=d50/d``・``E=2.7+0.7s``・``P1=s^E/(1+s^E)``。"""
    d, d50 = 40.0, 40.0
    s = d50 / d
    e = 2.7 + 0.7 * s
    assert P.p1_primary(np.array([d]), d50)[0] == pytest.approx(s**e / (1 + s**e))
    assert P.TTPF_E_BASE == 2.7 and P.TTPF_E_SLOPE == 0.7


def test_coefficients_match_the_contract():
    assert P.D50_DEFAULT_M == 40.0
    assert P.CUTOFF_M == 80.0
    assert P.E2_DEG == 6.22 and P.ECC_CUTOFF_DEG == 110.0
    assert P.M_LIGHT_NIGHT == 0.68
    assert P.M_DENSITY == (1.0, 0.5, 0.2)
    assert P.M_LOAD == (1.0, 0.46, 1.0)  # 手空き / 歩きスマホ / 会話
    assert P.MOVING_D50_MULTIPLIER == 1.5
    assert P.SOCIAL_RADIUS_M == 15.0
    assert (P.SOCIAL_A, P.SOCIAL_B, P.SOCIAL_N50) == (0.92, 1.05, 1.2)
    assert P.A0_CONSTANT == 0.54
    assert P.MAX_EVENTS_PER_TICK == 200


def test_social_hill_curve():
    """``P2 = 0.92·N^1.05/(1.2^1.05+N^1.05)``・N=0 で 0・単調増加・上限 0.92。"""
    n = np.arange(0, 50)
    p2 = P.p2_social(n)
    assert p2[0] == 0.0
    assert np.all(np.diff(p2) > 0)
    assert p2[-1] < P.SOCIAL_A
    assert P.p2_social(1.2)[()] == pytest.approx(0.46, abs=0.01)  # N50 で約半分


def test_combination_rule():
    p1 = np.array([0.5, 0.0, 1.0])
    p2 = np.array([0.5, 0.4, 0.9])
    assert np.allclose(P.combine(p1, p2), [0.75, 0.4, 1.0])


def test_eccentricity_zero_behind_the_head():
    """``|E_ang|>110°`` は一次視覚ゼロ。"""
    xy = np.array([[0.0, 0.0]])
    # heading セクタ0 = +x。事象が −x 方向(180°)なら背後
    assert P.eccentricity_deg(xy, np.array([0], np.uint8), (-10.0, 0.0))[0] == pytest.approx(180.0)
    r = P.notice_event(
        event_xy=(-5.0, 0.0), agent_xy=xy, heading_u8=np.array([0], np.uint8),
        seed=1, event_id=1, tick=1, params=P.PNoticeParams(ablation=P.Ablation.A3_ECC_DENSITY),
    )
    assert r.p1[0] == 0.0


def test_cutoff_80m():
    xy = np.array([[0.0, 0.0], [79.0, 0.0], [81.0, 0.0]])
    r = P.notice_event(
        event_xy=(0.0, 0.0), agent_xy=xy, heading_u8=np.zeros(3, np.uint8),
        seed=1, event_id=1, tick=1,
    )
    assert list(r.index) == [0, 1]  # 81 m は候補から外れる


@pytest.mark.parametrize("ab", list(P.Ablation))
def test_ablation_arms_run_and_a0_is_the_constant(ab):
    xy = np.stack([np.linspace(1, 79, 200), np.zeros(200)], axis=1)
    r = P.notice_event(
        event_xy=(0.0, 0.0), agent_xy=xy, heading_u8=np.zeros(200, np.uint8),
        task_flag=P.TaskLoad.PHONE, density_class=P.DensityClass.DENSE, night=True,
        seed=3, event_id=2, tick=5, params=P.PNoticeParams(ablation=ab),
    )
    assert r.n_candidates == 200
    if ab == P.Ablation.A0_CONSTANT:
        assert np.allclose(r.p1, P.A0_CONSTANT)
        assert np.all(r.p2 == 0.0)
    if ab <= P.Ablation.A3_ECC_DENSITY:
        assert np.all(r.p2 == 0.0)  # 社会項は A4 でのみ入る


def test_ablation_arms_are_ordered_by_strength_at_a_fixed_distance():
    """A1(距離のみ)≥ A2(+夜/歩きスマホ)≥ A3(+偏心・密度)。"""
    xy = np.array([[20.0, 0.0]])
    h = np.array([8], np.uint8)  # 事象(原点)を正面に見る

    def p1(ab):
        return P.notice_event(
            event_xy=(0.0, 0.0), agent_xy=xy, heading_u8=h,
            task_flag=P.TaskLoad.PHONE, density_class=P.DensityClass.DENSE, night=True,
            seed=1, event_id=1, tick=1, params=P.PNoticeParams(ablation=ab),
        ).p1[0]

    assert p1(P.Ablation.A1_DISTANCE) >= p1(P.Ablation.A2_LOAD_LIGHT)
    assert p1(P.Ablation.A2_LOAD_LIGHT) >= p1(P.Ablation.A3_ECC_DENSITY)


def test_moving_event_is_easier_to_detect():
    xy = np.array([[60.0, 0.0]])
    h = np.array([8], np.uint8)  # セクタ8 = −x 方向 = 事象(原点)を正面に見る
    still = P.notice_event(event_xy=(0.0, 0.0), agent_xy=xy, heading_u8=h,
                           seed=1, event_id=1, tick=1, moving=False).p1[0]
    moving = P.notice_event(event_xy=(0.0, 0.0), agent_xy=xy, heading_u8=h,
                            seed=1, event_id=1, tick=1, moving=True).p1[0]
    assert moving > still


def test_social_counts_are_exact_within_radius():
    pts = np.array([[0.0, 0.0], [10.0, 0.0], [14.9, 0.0], [15.1, 0.0], [40.0, 0.0]])
    noticed = np.array([False, True, True, True, True])
    n = P.social_counts(pts, noticed, radius_m=15.0)
    assert list(n) == [2, 2, 2, 2, 0]


def test_social_term_lifts_probability():
    """A4 は A3 より p が高い(社会伝播が上乗せされる)。"""
    rng = np.random.default_rng(0)
    xy = rng.uniform(-30, 30, size=(500, 2))
    h = rng.integers(0, 16, size=500).astype(np.uint8)
    kw = dict(event_xy=(0.0, 0.0), agent_xy=xy, heading_u8=h, seed=9, event_id=1, tick=1)
    a3 = P.notice_event(params=P.PNoticeParams(ablation=P.Ablation.A3_ECC_DENSITY), **kw)
    a4 = P.notice_event(params=P.PNoticeParams(ablation=P.Ablation.A4_SOCIAL), **kw)
    assert a4.p.mean() > a3.p.mean()
    assert np.all(a4.p >= a3.p - 1e-12)


def test_determinism_same_seed_same_draw():
    rng = np.random.default_rng(1)
    xy = rng.uniform(-40, 40, size=(300, 2))
    h = rng.integers(0, 16, size=300).astype(np.uint8)
    kw = dict(event_xy=(0.0, 0.0), agent_xy=xy, heading_u8=h, event_id=7, tick=11)
    a = P.notice_event(seed=42, **kw)
    b = P.notice_event(seed=42, **kw)
    c = P.notice_event(seed=43, **kw)
    assert np.array_equal(a.noticed, b.noticed)
    assert not np.array_equal(a.noticed, c.noticed)


def test_event_budget_caps_at_200_per_tick():
    b = P.EventBudget()
    admitted = sum(1 for _ in range(250) if b.admit(tick=5))
    assert admitted == P.MAX_EVENTS_PER_TICK == 200
    assert b.counters.events == 200 and b.counters.events_over_cap == 50
    assert b.admit(tick=6) is True  # 次の tick でリセット


def test_p7_budget_26000_candidates(capsys):
    """§7 P7「0.26 MOPS/イベント」= 26,000 体規模を 1 イベント 1 回のベクトル演算で。"""
    rng = np.random.default_rng(0)
    n = 26_000
    xy = rng.uniform(0, 300, size=(n, 2))  # 9 セル(300 m 角)相当
    h = rng.integers(0, 16, size=n).astype(np.uint8)
    kw = dict(event_xy=(150.0, 150.0), agent_xy=xy, heading_u8=h,
              task_flag=0, density_class=2, seed=1, event_id=1, tick=1)

    def bench(params, reps=5):
        P.notice_event(params=params, **kw)  # warm-up
        t0 = time.perf_counter()
        for _ in range(reps):
            r = P.notice_event(params=params, **kw)
        return (time.perf_counter() - t0) / reps * 1000.0, r

    ms_a3, r3 = bench(P.PNoticeParams(ablation=P.Ablation.A3_ECC_DENSITY))
    ms_a4, r4 = bench(P.PNoticeParams(ablation=P.Ablation.A4_SOCIAL))
    with capsys.disabled():
        print(
            f"\n[P7] n={n} 候補={r4.n_candidates} "
            f"A3(一次のみ)={ms_a3:.3f} ms / A4(+社会項)={ms_a4:.3f} ms"
        )
    assert ms_a3 <= 5.0  # 一次検出は 0.26 MOPS 相当(参照実測は 1 ms 未満)
    assert ms_a4 <= 50.0  # 社会項の近傍計数を含めた上限(報告値)


def test_social_fallback_counter_fires_on_extreme_density():
    """対の総数が上限を超えると近似へ退避し、退避回数が counters に載る。"""
    rng = np.random.default_rng(2)
    xy = rng.uniform(0, 30, size=(3_000, 2))
    counters = P.Counters()
    P.notice_event(
        event_xy=(15.0, 15.0), agent_xy=xy,
        heading_u8=np.zeros(3_000, np.uint8), seed=1, event_id=1, tick=1,
        params=P.PNoticeParams(max_pairs=1_000), counters=counters,
    )
    assert counters.social_approx_fallbacks == 1
