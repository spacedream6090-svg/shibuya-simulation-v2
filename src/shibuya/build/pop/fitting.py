"""build.pop.fitting — IPF(raking)・整数配分・適合度指標(SRMSE / JSD)。

正典
- 決定台帳「母集団合成」④ 属性補正(raking): 年齢×性別を**国勢調査(住民)・経済センサス
  (従業者)**の周辺へ raking。合否 = SRMSE 性別 <0.01・年齢 <0.13。
- 母集団合成答申 Q1-1: SRMSE=**周辺分布**の一致 / JSD=**結合分布**の一致。
  合否ラインの出所は Jones, Dawson & Mills, PLoS One 2026(109か国の中央値)。

SRMSE の定義(本実装が採る形・答申の出典と同型)
    SRMSE = sqrt( Σ_k (p_sim,k − p_obs,k)² / K ) / ( Σ_k p_obs,k / K )
    p は**割合**(和 1)なので分母 = 1/K。したがって ``sqrt(K · Σ Δ²)``。
    性別(K=2)では片側 0.5 ポイントのズレで 0.01 ちょうど= 決定台帳のラインは厳しい側。

逐次ループ宣言(P4)
- ``ipf``: **反復回数**ぶんのループ(既定上限 200・収束で打ち切り)。表の大きさには比例しない。
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

__all__ = [
    "ipf",
    "srmse",
    "jsd",
    "largest_remainder",
    "IPFResult",
]


class IPFResult(tuple):
    """``(table, n_iter, max_residual)`` の名前つきタプル。"""

    __slots__ = ()

    def __new__(cls, table: np.ndarray, n_iter: int, max_residual: float):
        return super().__new__(cls, (table, n_iter, max_residual))

    @property
    def table(self) -> np.ndarray:
        return self[0]

    @property
    def n_iter(self) -> int:
        return self[1]

    @property
    def max_residual(self) -> float:
        return self[2]


def ipf(
    seed: np.ndarray,
    row_target: Sequence[float],
    col_target: Sequence[float],
    *,
    max_iter: int = 200,
    tol: float = 1e-9,
) -> IPFResult:
    """2 次元 IPF(iterative proportional fitting)。

    Args:
        seed: ``(R, C)`` の種表(標本の分割表)。負の要素は不可。
        row_target: 行の周辺目標(長さ R)。
        col_target: 列の周辺目標(長さ C)。和は ``row_target`` と一致していること。
        max_iter: 反復上限(逐次ループ宣言 P4)。
        tol: 収束判定(周辺の最大絶対残差 / 総和)。

    Returns:
        ``IPFResult(table, n_iter, max_residual)``。

    Note:
        種表の 0 セルは 0 のままになる(IPF の性質)。目標が正なのに種が全 0 の行/列は
        **一様種**で埋めてから合わせる(構造的ゼロと標本ゼロを区別できないため・expedient)。

    Example:
        >>> t = ipf(np.ones((2, 2)), [10, 30], [20, 20]).table
        >>> [round(v, 6) for v in t.ravel().tolist()]
        [5.0, 5.0, 15.0, 15.0]
    """
    a = np.asarray(seed, dtype=np.float64).copy()
    if (a < 0).any():
        raise ValueError("種表に負の要素")
    r = np.asarray(row_target, dtype=np.float64)
    c = np.asarray(col_target, dtype=np.float64)
    if a.shape != (r.size, c.size):
        raise ValueError(f"形が合わない: seed{a.shape} vs ({r.size},{c.size})")
    if (r < 0).any() or (c < 0).any():
        raise ValueError("目標に負の値")
    total = float(r.sum())
    if not np.isclose(total, float(c.sum()), rtol=1e-9, atol=1e-6):
        raise ValueError("行の目標和と列の目標和が違う")
    if total <= 0:
        return IPFResult(np.zeros_like(a), 0, 0.0)
    # 構造的に空の行/列は一様種で埋める(expedient・上の Note)
    empty_rows = (a.sum(axis=1) == 0) & (r > 0)
    a[empty_rows, :] = 1.0
    empty_cols = (a.sum(axis=0) == 0) & (c > 0)
    a[:, empty_cols] = 1.0
    a *= total / a.sum()

    resid = float("inf")
    it = 0
    for it in range(1, max_iter + 1):
        rs = a.sum(axis=1)
        scale = np.divide(r, rs, out=np.zeros_like(r), where=rs > 0)
        a *= scale[:, None]
        cs = a.sum(axis=0)
        scale = np.divide(c, cs, out=np.zeros_like(c), where=cs > 0)
        a *= scale[None, :]
        resid = max(
            float(np.abs(a.sum(axis=1) - r).max()), float(np.abs(a.sum(axis=0) - c).max())
        ) / total
        if resid <= tol:
            break
    return IPFResult(a, it, resid)


def srmse(sim: Sequence[float], obs: Sequence[float]) -> float:
    """標準化 RMSE。``sim``/``obs`` はカウントでも割合でもよい(内部で割合に直す)。

    Example:
        >>> round(srmse([50, 50], [50, 50]), 12)
        0.0
        >>> round(srmse([50.5, 49.5], [50, 50]), 4)   # 片側 0.5 ポイント
        0.01
    """
    s = np.asarray(sim, dtype=np.float64).ravel()
    o = np.asarray(obs, dtype=np.float64).ravel()
    if s.shape != o.shape:
        raise ValueError("長さが違う")
    ss, so = s.sum(), o.sum()
    if ss <= 0 or so <= 0:
        raise ValueError("和が 0 の分布は比較できない")
    p = s / ss
    q = o / so
    k = p.size
    return float(np.sqrt(k * float(((p - q) ** 2).sum())))


def jsd(p: Sequence[float], q: Sequence[float], *, base: float = 2.0) -> float:
    """Jensen-Shannon divergence(既定 log2 = 0..1 の範囲)。"""
    a = np.asarray(p, dtype=np.float64).ravel()
    b = np.asarray(q, dtype=np.float64).ravel()
    if a.shape != b.shape:
        raise ValueError("長さが違う")
    if a.sum() <= 0 or b.sum() <= 0:
        raise ValueError("和が 0 の分布は比較できない")
    a = a / a.sum()
    b = b / b.sum()
    m = 0.5 * (a + b)

    def _kl(x: np.ndarray, y: np.ndarray) -> float:
        mask = x > 0
        return float((x[mask] * (np.log(x[mask] / y[mask]) / np.log(base))).sum())

    return 0.5 * _kl(a, m) + 0.5 * _kl(b, m)


def largest_remainder(weights: Sequence[float], total: int) -> np.ndarray:
    """重み → 合計が厳密に ``total`` になる非負整数の配分(最大剰余法)。

    同点は**添字が小さい方**を先に切り上げる(決定論)。

    Example:
        >>> largest_remainder([1, 1, 1], 4).tolist()
        [2, 1, 1]
        >>> int(largest_remainder([0.5, 0.3, 0.2], 10).sum())
        10
    """
    w = np.asarray(weights, dtype=np.float64).ravel()
    total = int(total)
    if total < 0:
        raise ValueError("total は 0 以上")
    if w.size == 0:
        if total:
            raise ValueError("配分先が無いのに total>0")
        return np.zeros(0, dtype=np.int64)
    if (w < 0).any():
        raise ValueError("重みに負の値")
    s = w.sum()
    if s <= 0:
        w = np.ones_like(w)
        s = w.sum()
    exact = w * (total / s)
    base = np.floor(exact).astype(np.int64)
    rest = total - int(base.sum())
    if rest > 0:
        frac = exact - base
        order = np.lexsort((np.arange(w.size), -frac))
        base[order[:rest]] += 1
    return base
