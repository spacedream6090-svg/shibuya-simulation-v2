# -*- coding: utf-8 -*-
"""jgd_plane — 平面直角座標系(JGD2011)と緯度経度の換算(numpy だけ)。

式: 国土地理院「平面直角座標から緯度経度への換算」「緯度経度から平面直角座標への換算」の計算式
(河瀬 2011・Krüger 級数 n の 5〜6 次。GRS80・m0 0.9999)。座標系の原点は系ごとに違う(本書は第 9 系だけを持つ)。

軸の約束(測量の慣行): ``x`` = 北向き、``y`` = 東向き [m]。LAS の X(東)/Y(北)とは名前が逆になる
(``las_pointcloud_agg`` 側で東=LAS X・北=LAS Y と確かめてから渡す)。

検算(試験 ``tests/tools/test_las_pointcloud_agg.py``): 原点 (0, 0) → (北緯 36°, 東経 139°50′)・
国土地理院の換算サービス(2026-11-02 に読むだけ)の 2 点で 1 mm 未満。
"""

from __future__ import annotations

import math

import numpy as np

__all__ = ["GRS80_A", "GRS80_F", "M0", "ZONE9_ORIGIN_DEG", "plane_to_latlon", "latlon_to_plane"]

GRS80_A = 6378137.0
GRS80_F = 1.0 / 298.257222101
M0 = 0.9999
#: 第 9 系の原点(北緯 36°・東経 139°50′=139.8333…°)。EPSG 6677(JGD2011 / Japan Plane Rectangular CS IX)。
ZONE9_ORIGIN_DEG = (36.0, 139.0 + 50.0 / 60.0)

_n = GRS80_F / (2.0 - GRS80_F)  # = 1 / (2F - 1)。F は扁平率の逆数


def _coeffs(n: float) -> dict[str, list[float]]:
    A = [
        1 + n**2 / 4 + n**4 / 64,
        -3 / 2 * (n - n**3 / 8 - n**5 / 64),
        15 / 16 * (n**2 - n**4 / 4),
        -35 / 48 * (n**3 - 5 / 16 * n**5),
        315 / 512 * n**4,
        -693 / 1280 * n**5,
    ]
    alpha = [
        0.0,
        1 / 2 * n - 2 / 3 * n**2 + 5 / 16 * n**3 + 41 / 180 * n**4 - 127 / 288 * n**5,
        13 / 48 * n**2 - 3 / 5 * n**3 + 557 / 1440 * n**4 + 281 / 630 * n**5,
        61 / 240 * n**3 - 103 / 140 * n**4 + 15061 / 26880 * n**5,
        49561 / 161280 * n**4 - 179 / 168 * n**5,
        34729 / 80640 * n**5,
    ]
    beta = [
        0.0,
        1 / 2 * n - 2 / 3 * n**2 + 37 / 96 * n**3 - 1 / 360 * n**4 - 81 / 512 * n**5,
        1 / 48 * n**2 + 1 / 15 * n**3 - 437 / 1440 * n**4 + 46 / 105 * n**5,
        17 / 480 * n**3 - 37 / 840 * n**4 - 209 / 4480 * n**5,
        4397 / 161280 * n**4 - 11 / 504 * n**5,
        4583 / 161280 * n**5,
    ]
    delta = [
        0.0,
        2 * n - 2 / 3 * n**2 - 2 * n**3 + 116 / 45 * n**4 + 26 / 45 * n**5 - 2854 / 675 * n**6,
        7 / 3 * n**2 - 8 / 5 * n**3 - 227 / 45 * n**4 + 2704 / 315 * n**5 + 2323 / 945 * n**6,
        56 / 15 * n**3 - 136 / 35 * n**4 - 1262 / 105 * n**5 + 73814 / 2835 * n**6,
        4279 / 630 * n**4 - 332 / 35 * n**5 - 399572 / 14175 * n**6,
        4174 / 315 * n**5 - 144838 / 6237 * n**6,
        601676 / 22275 * n**6,
    ]
    return {"A": A, "alpha": alpha, "beta": beta, "delta": delta}


_C = _coeffs(_n)


def _s_bar(phi0: float) -> float:
    A = _C["A"]
    s = A[0] * phi0 + sum(A[j] * math.sin(2 * j * phi0) for j in range(1, 6))
    return M0 * GRS80_A / (1 + _n) * s


_A_BAR = M0 * GRS80_A / (1 + _n) * _C["A"][0]


def plane_to_latlon(x_north, y_east, origin_deg: tuple[float, float] = ZONE9_ORIGIN_DEG):
    """平面直角座標 (x=北, y=東) [m] → (緯度, 経度) [度]。配列可。"""
    phi0 = math.radians(origin_deg[0])
    lam0 = math.radians(origin_deg[1])
    x = np.asarray(x_north, dtype=np.float64)
    y = np.asarray(y_east, dtype=np.float64)
    xi = (x + _s_bar(phi0)) / _A_BAR
    eta = y / _A_BAR
    b = _C["beta"]
    xi2 = xi.copy()
    eta2 = eta.copy()
    for j in range(1, 6):
        xi2 = xi2 - b[j] * np.sin(2 * j * xi) * np.cosh(2 * j * eta)
        eta2 = eta2 - b[j] * np.cos(2 * j * xi) * np.sinh(2 * j * eta)
    chi = np.arcsin(np.sin(xi2) / np.cosh(eta2))
    d = _C["delta"]
    phi = chi.copy()
    for j in range(1, 7):
        phi = phi + d[j] * np.sin(2 * j * chi)
    lam = lam0 + np.arctan2(np.sinh(eta2), np.cos(xi2))
    return np.degrees(phi), np.degrees(lam)


def latlon_to_plane(lat_deg, lon_deg, origin_deg: tuple[float, float] = ZONE9_ORIGIN_DEG):
    """(緯度, 経度) [度] → 平面直角座標 (x=北, y=東) [m]。配列可(検算と試験の合成に使う)。"""
    phi0 = math.radians(origin_deg[0])
    lam0 = math.radians(origin_deg[1])
    phi = np.radians(np.asarray(lat_deg, dtype=np.float64))
    lam = np.radians(np.asarray(lon_deg, dtype=np.float64))
    k = 2 * math.sqrt(_n) / (1 + _n)
    t = np.sinh(np.arctanh(np.sin(phi)) - k * np.arctanh(k * np.sin(phi)))
    tb = np.sqrt(1 + t * t)
    lc = np.cos(lam - lam0)
    ls = np.sin(lam - lam0)
    xi2 = np.arctan2(t, lc)
    eta2 = np.arctanh(ls / tb)
    a = _C["alpha"]
    xs = xi2.copy()
    ys = eta2.copy()
    for j in range(1, 6):
        xs = xs + a[j] * np.sin(2 * j * xi2) * np.cosh(2 * j * eta2)
        ys = ys + a[j] * np.cos(2 * j * xi2) * np.sinh(2 * j * eta2)
    return _A_BAR * xs - _s_bar(phi0), _A_BAR * ys
