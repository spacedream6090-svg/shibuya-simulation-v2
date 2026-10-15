"""第 6 期 6-5 記憶 M1: 強さの式(ACT-R の折衷形・秒の時刻・+1 なし・d=0.5)と人ごとのばらつき 15%(Sense 2018)の単体。

- 既知の値: 1 回 100 秒前=−0.5·ln 100・2 回 100/400 秒前=ln(0.1+0.05)・+1 が無い(60 秒で −0.5·ln 60)。
- 折衷形: n ≤ k は正確な式と同じ・等間隔の古い回は正確な式に近い(Petrov 2006 の式 (3) の前提)。
- 単位: 正確な式も折衷形も、時刻の単位を c 倍にすると全部の強さが −d·ln c だけ同じにずれる(MR1=τ に吸収)。
- 最短の符号化時間: t=0 は ``T_MIN_S`` で切る(−inf にならない)。
- 人ごとの倍率: 同じ (seed, 体) は同じ値・体の数を変えても既存の体の値は同じ(カウンタの鍵)・変動係数 ≈ 15%・±3σ で切る。
- 境目 τ の仮の値: M0 の n=1 の行が τ_m0 を下回る時刻と、M1 の「n=1・初めての成功の行」が τ を下回る時刻が同じ。
- 思い浮かぶ/見覚え/忘れる/言葉の単体。M1 の状態の守り(付け替え・消去・読み取り専用の view)。
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from shibuya.core.time_consts import NS_PER_SECOND, SECONDS_PER_MINUTE
from shibuya.engine import memory_m1 as M1
from shibuya.engine.memory import RECALL_TAU, activation_rows

S = NS_PER_SECOND
NOW = 10**15
NT = M1.NO_TIME


def _row(*ago_s: float) -> list[int]:
    t = [NOW - int(a * S) for a in ago_s]
    return t + [NT] * (M1.K_RECENT - len(t))


def test_known_values_without_plus_one():
    B = M1.base_level([_row(100.0)], [1], [NOW - 100 * S], NOW, 0.5)
    assert B[0] == pytest.approx(-0.5 * math.log(100.0), abs=1e-12)
    B2 = M1.base_level([_row(100.0, 400.0)], [2], [NOW - 400 * S], NOW, 0.5)
    assert B2[0] == pytest.approx(math.log(0.1 + 0.05), abs=1e-12)
    # +1 をやめた: 60 秒前の 1 回は −0.5·ln 60(M0 の式なら ln 2 − 0.5·ln(1+1)=分の単位+1)
    B3 = M1.base_level([_row(60.0)], [1], [NOW - 60 * S], NOW, 0.5)
    assert B3[0] == pytest.approx(-0.5 * math.log(60.0), abs=1e-12)
    assert B3[0] != pytest.approx(-0.5 * math.log(61.0), abs=1e-6)


def test_hybrid_equals_exact_when_n_le_k_and_is_close_for_even_spacing():
    times = [NOW - int(x * S) for x in (30.0, 600.0, 7200.0)]
    exact = M1.exact_base_level(times, NOW, 0.5)
    hyb = M1.base_level([times], [3], [times[-1]], NOW, 0.5)[0]
    assert hyb == pytest.approx(exact, abs=1e-12)
    # 等間隔 50 回(1 時間おき)・直近 3 回だけ本当の時刻
    ts = [NOW - int(h * 3600 * S) for h in range(1, 51)]
    exact = M1.exact_base_level(ts, NOW, 0.5)
    hyb = M1.base_level([ts[:3]], [50], [ts[-1]], NOW, 0.5)[0]
    assert abs(hyb - exact) < 0.05, (hyb, exact)
    # k=0 相当(直近の時刻なし)=式 (2) の近似 n·t_n^(−d)/(1−d)
    k0 = M1.base_level([[NT] * M1.K_RECENT], [4], [NOW - 1000 * S], NOW, 0.5)[0]
    assert k0 == pytest.approx(math.log(4 * 1000.0 ** -0.5 / 0.5), abs=1e-12)


def test_units_shift_all_strengths_by_the_same_amount():
    """MR1: 単位を c 倍にすると全部の強さが −d·ln c だけ同じにずれる(+1 の無い式)=τ に吸収される。"""
    rows = [_row(100.0), _row(50.0, 3000.0), _row(10.0, 20.0, 99_000.0)]
    n = [1, 2, 7]
    first = [NOW - 100 * S, NOW - 3000 * S, NOW - 500_000 * S]
    B_s = M1.base_level(rows, n, first, NOW, 0.5, t_min_s=1e-9)
    c = float(SECONDS_PER_MINUTE)
    scaled = [[NOW - (NOW - t) * int(c) if t != NT else NT for t in r] for r in rows]
    first_c = [NOW - (NOW - f) * int(c) for f in first]
    B_c = M1.base_level(scaled, n, first_c, NOW, 0.5, t_min_s=1e-9)
    assert np.allclose(B_c - B_s, -0.5 * math.log(c), atol=1e-9)
    # 負の対照: M0 の式(+1 あり)は単位を分 → 秒に替えるとずれ方が行(経過)ごとに違う=τ に吸収されない
    L_min = np.asarray([1.0, 100.0])
    a_min = math.log(2.0) - 0.5 * np.log(L_min + 1.0)
    a_sec = math.log(2.0) - 0.5 * np.log(L_min * c + 1.0)
    diff = a_sec - a_min
    assert abs(diff[0] - diff[1]) > 0.1


def test_minimum_encoding_time_avoids_infinity():
    B = M1.base_level([[NOW, NT, NT]], [1], [NOW], NOW, 0.5)
    assert np.isfinite(B[0]) and B[0] == pytest.approx(-0.5 * math.log(M1.T_MIN_S))
    assert M1.base_level([[NT] * M1.K_RECENT], [0], [NOW], NOW, 0.5)[0] == -np.inf
    with pytest.raises(ValueError):
        M1.base_level([_row(1.0)], [1], [NOW], NOW, 1.0)


def test_forgetting_scale_is_deterministic_and_about_15_percent():
    s1 = M1.forgetting_scale(7, np.arange(100_000))
    s2 = M1.forgetting_scale(7, np.arange(100_000))
    assert np.array_equal(s1, s2)
    assert 0.995 < s1.mean() < 1.005 and 0.145 < s1.std() < 0.155
    assert s1.min() >= 1 - 3 * M1.CV_RATE - 1e-12 and s1.max() <= 1 + 3 * M1.CV_RATE + 1e-12
    # カウンタの鍵: 体の数を変えても既存の体の値は同じ・seed が違えば違う
    assert np.array_equal(M1.forgetting_scale(7, np.arange(10)), s1[:10])
    assert not np.array_equal(M1.forgetting_scale(8, np.arange(10)), s1[:10])
    assert M1.RATE_DOMAIN == "memory.forgetting_rate"


def test_tau_from_m0_matches_the_m0_crossing_time():
    tau1 = M1.tau_from_m0(RECALL_TAU)
    L_min = math.exp((math.log(2.0) - RECALL_TAU) / 0.5) - 1.0  # M0 の n=1 の行が τ_m0 に届く分
    assert activation_rows(np.asarray([1]), np.asarray([0]), 0, 1.0)[0] > RECALL_TAU
    a0 = math.log(2.0) - 0.5 * math.log(L_min + 1.0)
    assert a0 == pytest.approx(RECALL_TAU, abs=1e-9)
    t = NOW - int(L_min * SECONDS_PER_MINUTE * S)
    A1 = M1.base_level([[t, NT, NT]], [1], [t], NOW, 0.5)[0] + M1.W_IMPORTANCE * 2
    assert A1 == pytest.approx(tau1, abs=1e-6)
    assert tau1 == pytest.approx(-3.738025, abs=1e-5)


def test_touch_times_shifts_newest_first():
    rec = np.full((3, 3), NT, dtype=np.int64)
    M1.touch_times(rec, np.asarray([0, 2]), [5, 7])
    M1.touch_times(rec, np.asarray([0]), 9)
    M1.touch_times(rec, np.asarray([0]), 11)
    M1.touch_times(rec, np.asarray([0]), 13)
    assert rec[0].tolist() == [13, 11, 9] and rec[2].tolist() == [7, NT, NT] and rec[1].tolist() == [NT] * 3


def test_recall_recognize_forget_and_words():
    tau = -3.0
    assert M1.recall_mask([-2.9, -3.0, -3.1], tau).tolist() == [True, True, False]
    # 見覚え=手がかりを足すと超える(手がかりの無い行は偽)
    assert M1.recognize_mask([-3.5, -4.5, -3.5], tau, [True, True, False]).tolist() == [True, False, False]
    # 忘れる=手がかりがあっても見覚えに FORGET_MARGIN だけ届かない
    assert M1.forget_mask([-5.1, -4.9], tau).tolist() == [True, False]
    w = M1.clarity_words([-1.9, -2.5, -3.0, -3.5], tau)
    assert w.tolist() == [M1.WORD_CLEAR, M1.WORD_VAGUE, M1.WORD_VAGUE, ""]


def test_m1_state_guards():
    st = M1.M1State(4, 8, tau=-3.0, seed=1)
    with pytest.raises(AttributeError):
        st.tau = 0.0
    with pytest.raises(AttributeError):
        del st._t_ns
    v = st.scale
    with pytest.raises(ValueError):
        v[0] = 2.0
    r = st.recent_ns
    with pytest.raises(ValueError):
        r[0, 0] = 1
    st.place(np.asarray([1, 2]), np.asarray([True, False]), [100, 200])
    assert st.recent_ns[1].tolist() == [100, NT, NT] and st.recent_ns[2].tolist() == [200, NT, NT]
    st.grow(4, 2, 4)
    assert st.recent_ns.shape == (16, M1.K_RECENT)
    assert st.recent_ns[1].tolist() == [100, NT, NT]  # 体 0 の行 1 はそのまま
    assert st.recent_ns[4].tolist() == [200, NT, NT]  # 体 1 の行 0(前の番地 2)は新しい番地 4


def test_arm_switches_and_checks():
    prev = M1.arms()
    try:
        assert M1.arms()[:5] == ("m0", "id", "table", "ruri-v3-30m", "each") or M1.arms_on()
        M1.set_arm("model", "m1")
        assert M1.arms_on()
        with pytest.raises(ValueError, match="器のラン"):
            M1.check_arms(store_on=False)
        M1.set_arm("people", "memory")
        M1.set_arm("model", "m0")
        with pytest.raises(ValueError, match="m1 が前提"):
            M1.check_arms(store_on=True)
        with pytest.raises(ValueError):
            M1.set_arm("model", "m2")
        with pytest.raises(KeyError):
            M1.set_arm("nope", "x")
    finally:
        for k in ("model", "cue", "people", "embed_model", "grain"):
            M1.set_arm(k, getattr(prev, k))
