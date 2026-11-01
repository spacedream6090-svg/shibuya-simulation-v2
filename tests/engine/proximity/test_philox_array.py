"""第 2 期 2-2(親の判断 10-14 の 1): 配列で回す Philox ``core.rng.philox_array`` が numpy の ``np.random.Philox`` と同じ出力。

- 同じ鍵(``derive_key(seed, 用途名)``)・同じカウンタで、1 万行の 1〜9 語が ``philox(…).random_raw(語数)`` と全部一致
  (0 語目・1 語目の繰り上がりの境を含む)。``np.random.Philox(key=…, counter=…)`` を直に作った値とも一致。
- ``unit_float`` は ``Generator.random()`` と同じ写し方(1 万行)。
- ``k19_counter_array`` は ``k19_counters`` の語の並び(0 語目を空ける)のまま。
- 行を抜き出して引いても同じ値(状態を持たない=規模に依らない)。入力の検査。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.core import rng as R

N = 10_000


def _counters(seed: int, n: int = N) -> np.ndarray:
    g = np.random.default_rng(seed)
    c = (g.integers(0, 1 << 62, (n, 4), dtype=np.int64).astype(np.uint64) * np.uint64(4)
         + g.integers(0, 4, (n, 4)).astype(np.uint64))
    top = np.uint64((1 << 64) - 1)
    c[:40, 0] = top                     # 0 語目の繰り上がり
    c[:15, 1] = top                     # 1 語目まで繰り上がる
    c[40:60, 0] = top - np.uint64(2)    # 数ブロック先で繰り上がる
    c[60:80] = 0                        # 全部 0
    return c


@pytest.mark.parametrize("words", [1, 2, 4, 5, 8, 9])
def test_philox_array_equals_numpy_philox_on_10000_rows(words):
    seed, dom = 20261014, "test.philox_array"
    c = _counters(words)
    got = R.philox_array(seed, dom, c, words=words)
    assert got.shape == (N, words) and got.dtype == np.uint64
    key = np.array(R.derive_key(seed, dom), dtype=np.uint64)
    for i in range(N):  # 逐次: 行の数ぶん(試験)
        row = [int(v) for v in c[i]]
        want = np.atleast_1d(R.philox(seed, dom, *row).random_raw(words))
        assert np.array_equal(got[i], want), (i, row)
        if i % 97 == 0:  # 直に作った numpy の Philox とも
            bg = np.random.Philox(key=key, counter=c[i].copy())
            assert np.array_equal(got[i], np.atleast_1d(bg.random_raw(words)))


def test_unit_float_equals_generator_random_and_k19_layout():
    seed, dom = 7, "proximity.notice"
    g = np.random.default_rng(1)
    tk = g.integers(0, 1 << 40, N)
    a = g.integers(0, 400_000, N)
    b = g.integers(0, 400_000, N)
    ctr = R.k19_counter_array(tk, a, b)
    assert ctr.shape == (N, 4) and not ctr[:, 0].any()
    for i in range(0, N, 251):
        assert tuple(int(v) for v in ctr[i]) == R.k19_counters(int(tk[i]), int(a[i]), int(b[i]))
    u = R.unit_float(R.philox_array(seed, dom, ctr)[:, 0])
    want = np.array([R.stream(seed, dom, *R.k19_counters(int(x), int(y), int(z))).random()
                     for x, y, z in zip(tk.tolist(), a.tolist(), b.tolist())])
    assert np.array_equal(u, want) and np.all((u >= 0) & (u < 1))
    # 状態を持たない: 行を抜き出して引いても同じ値
    sel = np.array([3, 17, 9_999, 4_200])
    assert np.array_equal(R.unit_float(R.philox_array(seed, dom, ctr[sel])[:, 0]), u[sel])
    # 鍵の列の 1 つが定数(放送)
    one = R.k19_counter_array(np.uint64(5), a[:10], b[:10])
    assert np.array_equal(one[:, 1], np.full(10, 5, dtype=np.uint64))


def test_philox_array_input_checks():
    with pytest.raises(ValueError):
        R.philox_array(1, "x", np.zeros((3, 5), dtype=np.uint64))
    with pytest.raises(ValueError):
        R.philox_array(1, "x", np.zeros(3, dtype=np.uint64))
    with pytest.raises(ValueError):
        R.philox_array(1, "x", np.array([[1, -1]]))
    with pytest.raises(TypeError):
        R.philox_array(1, "x", np.zeros((2, 2), dtype=np.float64))
    with pytest.raises(ValueError):
        R.philox_array(1, "x", np.zeros((2, 2), dtype=np.uint64), words=0)
    with pytest.raises(ValueError):
        R.k19_counter_array(1, 2, 3, 4)
    with pytest.raises(ValueError):
        R.k19_counter_array(np.array([-1]))
    assert R.philox_array(1, "x", np.zeros((0, 4), dtype=np.uint64), words=3).shape == (0, 3)
    # 語の足りないカウンタは 0 で詰める(philox と同じ)
    assert np.array_equal(R.philox_array(1, "x", np.array([[5, 6]], dtype=np.uint64), words=2)[0],
                          R.philox(1, "x", 5, 6).random_raw(2))
