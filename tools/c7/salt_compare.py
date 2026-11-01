# -*- coding: utf-8 -*-
"""salt の比較の**読む役**(10f 第 2 段・R-71 の手順・K20 (a)・K21 (a))。

腕 A(基準)と腕 B を salt(動きの seed)ごとに回した結果(``salt_runs.py`` の索引と checkpoints の JSON、
または計器の値の組)を読み、指標ごとに次を出す。ランは回さない(回す役は ``salt_runs.py``)。関数はどれも純粋。

- **本数と出力の線**(R-71 §2-3・K20 (a)): 符号反転の並べ替え検定の p の下限は片側 1/2^n・両側 2/2^n。下限が
  その指標の受ける線(主要 α・副次 Holm の最小 α/k・探索 BH の α)以下のときだけ「検定」。片側は向きを事前登録した
  印(``preregistered: true`` と ``direction``)があるときだけ(無ければ両側として扱う)。届かなければ
  **「記述のみ(本数不足)」**。3 対は両側 0.25 なので必ず記述のみ・5 対は片側の事前登録で 1/32・6 対から両側 2/64。
- **差・幅・差 ÷ 幅**(設計書 再開と決定論 §5 の 3 列): 差=対の差の平均。幅=salt 間の幅(家族 95%)=
  t(1 − α/(2m), n−1)·s_D/√n(m=家族の指標の数・既定は指標の総数)。**幅に対の差の SD を使うのは実行役の構成
  (未リサーチ(expedient))**: R-71 §5-4 の「差を比べるときは各腕の CV ではなく対の差の SD」に合わせた。各腕の
  salt 間の幅(同じ式を各腕の SD で)も ``width_base``・``width_arm`` に並べる。
- **ρ の実測**(R-71 §1-1): Var(D)/(Var(基準)+Var(腕)) と ρ。5 対以上で読む(``rho_readable``)。比が 1 を
  超えたら警告(CRN で損をしている)。
- **D-46 の式の 2 通り**(R-71 §5-1): 相対の標準誤差を r にする N=ceil((CV/r)²) と、95% の区間の半幅を r にする
  最小の N(t_{N−1,0.975}·CV/√N ≤ r)。基準の腕の CV と、対の差の CV(s_D/|基準の平均|)の 2 つで出す。
- **区間**(R-71 §4-2): 対の差の t 区間(95%)と、符号反転の検定を反転した区間(到達できる水準 1 − 2k/2^n を明記)。
  百分位のブートストラップは使わない。
- **効果の大きさ**(R-71 §4-1): 生の差・比(腕 ÷ 基準)・差の SD・CRN の対の d_z(差の平均 ÷ 差の SD・CRN の無い
  比較と並べない)・d_av(差の平均 ÷ 2 腕の SD の平均)。
- **多重比較**(R-71 §6): 主要は 1 つ(事前登録)・副次は Holm・探索は BH。
- **CRN の健全性**(R-71 §1-6・§8-1): 入力の一致(manifest の**設定の節**の差が腕の欄だけ・母集団の seed と
  母集団と日課のハッシュが全部のランで同じ)・T0 より前の checkpoint の behavior-hash の一致・最初の食い違いの
  tick(``first_diff.py`` の ``compare`` を使う)・A/A(同じ設定を 2 回回して全 checkpoint と final が一致)。
  全体の ``ok`` は ``True``(全部確かめて通った)・``False``(落ちた)・``None``(``status: 未検査``=A/A が無い・T0 より前の
  checkpoint が無い)の 3 つ(検収 S2)。環境の seed(10f 第 2 段の直し S1)は対の間で同じこと、``fixed`` なら全部同じこと。

符号反転の検定は対の数 n ≤ 20 なら全部の符号の組(2^n)を数えて正確な p を出す。n > 20 は 2^20 回の無作為の
組(固定の種)で (b+1)/(M+1)。区間の反転は n ≤ 12 のときだけ(それより多いと t 区間だけ)。

終了コード: ``--runs`` のとき CRN の健全性が ok なら 0・fail なら 1・未検査なら 3(既存のファイルへの書き込みの拒否は 2)。
``--values`` のときは 0。

使い方::

    python tools/c7/salt_compare.py --runs runs.json --metrics metrics.json --out report.json
    python tools/c7/salt_compare.py --values values.json --metrics metrics.json --out report.json

``metrics.json`` の形::

    {"alpha": 0.05, "family_size": null,
     "primary": {"id": "calls", "path": "manifest.llm_calls_total", "direction": "greater", "preregistered": true},
     "secondary": [{"id": "...", "path": "..."}], "exploratory": [{"id": "...", "path": "..."}]}

``arm_keys_derived``(任意)は ``{設定の道筋: {"base": 値, "arm": 値, "reason": 理由}}``: 腕の引数から導かれて変わる
設定の欄の宣言(CRN の入力の一致で許す・実際の値が宣言と違えば落ちる・報告に残る=検収 S3-3)。``path`` は checkpoints の JSON の中の道筋(``a.b.c``)。``values.json`` は ``{"指標の id": {"base": [...], "arm": [...]}}``
(salt の順に並べた値の組)。出力は JSON(既存のファイルへは書かない)。絶対パスは書かない。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

SCHEMA = "shibuya.tools.c7/salt_compare/1"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FIRST_DIFF = REPO / "docs" / "bench" / "analysis" / "wallbounce-1003" / "10d" / "first_diff.py"

DESCRIPTIVE = "記述のみ(本数不足)"
#: 差 ÷ 幅の読み方(検収 S3-2)。
DIFF_OVER_WIDTH_READING = ("差 ÷ 幅は記述。幅に対の差の SD を使うので |差 ÷ 幅| > 1 は対の差の t 検定(正規の仮定)を "
                           "α/m で棄却するのと同じ意味になるが、K20 (a) の検定ではない(K20 (a) は符号反転と本数の線)")
TESTED = "検定"
#: 全部の符号の組を数える上限(2^20 で約 0.25 秒・10f の材料 §2-4)。
EXACT_MAX_N = 20
#: 並べ替えの反転区間を出す上限(区切りの点 2·2^n × 符号の組 2^n の計算)。
PERM_CI_MAX_N = 12
#: n > EXACT_MAX_N のときの無作為の組の数と種。
MC_DRAWS = 1 << 20
MC_SEED = 20261007
#: 浮動小数の同点の許し(差の絶対値の最大に掛ける)。
_REL_TOL = 1e-9


# ---------------------------------------------------------------- t 分布(scipy を使わない)
def _betacf(a: float, b: float, x: float) -> float:
    """不完全ベータ関数の連分数(Lentz 法)。"""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 400):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c if abs(c) > tiny else 1.0 + aa / tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c if abs(c) > tiny else 1.0 + aa / tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    """正則化した不完全ベータ関数 I_x(a, b)。"""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lbt) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbt) * _betacf(b, a, 1.0 - x) / b


def t_cdf(t: float, df: int) -> float:
    """Student の t 分布の累積分布関数。"""
    x = df / (df + t * t)
    tail = 0.5 * _betainc(df / 2.0, 0.5, x)
    return 1.0 - tail if t >= 0 else tail


def t_quantile(q: float, df: int) -> float:
    """t 分布の分位(2 分法・相対 1e-12)。``q`` は 0〜1、``df`` は 1 以上。"""
    if not (0.0 < q < 1.0) or df < 1:
        raise ValueError(f"t_quantile: q は 0〜1・df は 1 以上(いま q={q}・df={df})")
    if q == 0.5:
        return 0.0
    if q < 0.5:
        return -t_quantile(1.0 - q, df)
    lo, hi = 0.0, 1.0
    while t_cdf(hi, df) < q:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if t_cdf(mid, df) < q:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-12 * max(1.0, hi):
            break
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- D-46 の式の 2 通り(R-71 §5-1)
def n_relative_se(cv: float, r: float) -> int:
    """相対の標準誤差 CV/√N を r 以下にする最小の N = ceil((CV/r)²)(D-46 の式。半幅の式ではない)。"""
    if r <= 0:
        raise ValueError("r は正")
    return max(1, int(math.ceil((abs(cv) / r) ** 2 - 1e-12)))


def n_halfwidth95(cv: float, r: float, *, n_max: int = 100_000) -> int | None:
    """95% の区間の半幅 t_{N−1,0.975}·CV/√N を r 以下にする最小の N(N ≥ 2)。``n_max`` までに無ければ ``None``。"""
    if r <= 0:
        raise ValueError("r は正")
    cv = abs(cv)
    if cv == 0.0:
        return 2
    def ok(n: int) -> bool:
        return t_quantile(0.975, n - 1) * cv / math.sqrt(n) <= r

    # 半幅は N に対して単調に減る=倍々で上限を見つけてから 2 分探索(t 分位の計算を数十回に抑える)
    if ok(2):
        return 2
    hi = 4
    while not ok(hi):
        if hi >= n_max:
            return None
        hi = min(hi * 2, n_max)
    lo = hi // 2  # ok(lo) は偽
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi


# ---------------------------------------------------------------- 符号反転の並べ替え検定(R-71 §2)
def _sign_matrix(n: int) -> np.ndarray:
    """全部の符号の組(形 (2^n, n)・+1/−1)。"""
    if n == 0:
        return np.ones((1, 0))
    k = np.arange(1 << n, dtype=np.int64)[:, None]
    bits = (k >> np.arange(n, dtype=np.int64)[None, :]) & 1
    return np.where(bits == 1, -1.0, 1.0)


def _flip_means(x: np.ndarray) -> np.ndarray:
    """全部の符号の組(2^n 通り)の差の平均。組 k はビット i が立てば i 番目の符号を反転する。

    部分和を倍々に作る(大きさ 2^n の 1 本の配列だけ・n=20 で 8 MB)。平均 = (Σx − 2·反転した部分の和)/n。
    """
    sums = np.zeros(1, dtype=np.float64)
    for xi in x.tolist():
        sums = np.concatenate([sums, sums + xi])
    return (float(x.sum()) - 2.0 * sums) / float(x.size)


def p_floor(n: int, alternative: str = "two-sided") -> float:
    """その対の数で到達できる最小の p(片側 1/2^n・両側 2/2^n・R-71 §2-3)。"""
    if n < 1:
        return 1.0
    return (1.0 if alternative in ("greater", "less") else 2.0) / float(1 << n) if n <= 62 else 0.0


def sign_flip_p(d: Sequence[float], alternative: str = "two-sided") -> dict[str, Any]:
    """対の差 ``d`` の符号反転の検定(統計量=差の平均)。

    ``alternative``: ``two-sided``(|T*| ≥ |T|)・``greater``(腕 > 基準: T* ≥ T)・``less``(T* ≤ T)。
    n ≤ 20 は全部の組を数えた正確な p、n > 20 は 2^20 回の無作為の組で (b+1)/(M+1)。
    """
    if alternative not in ("two-sided", "greater", "less"):
        raise ValueError(f"alternative は two-sided/greater/less(いま {alternative!r})")
    x = np.asarray(d, dtype=np.float64)
    n = int(x.size)
    if n == 0:
        return {"p": 1.0, "n": 0, "method": "none", "permutations": 0}
    tol = _REL_TOL * max(1.0, float(np.max(np.abs(x))))
    t_obs = float(x.mean())
    if n <= EXACT_MAX_N:
        ts = _flip_means(x)
        m = int(ts.size)
        method = "exact"
    else:
        g = np.random.default_rng(MC_SEED)
        parts = []
        for _ in range(MC_DRAWS // 65536):  # 65,536 組ずつ(メモリを抑える)
            s = np.where(g.random((65536, n)) < 0.5, -1.0, 1.0)
            parts.append(s @ x / n)
        ts = np.concatenate(parts)
        m = int(ts.size)
        method = "monte-carlo"
    if alternative == "two-sided":
        hits = int(np.count_nonzero(np.abs(ts) >= abs(t_obs) - tol))
    elif alternative == "greater":
        hits = int(np.count_nonzero(ts >= t_obs - tol))
    else:
        hits = int(np.count_nonzero(ts <= t_obs + tol))
    p = hits / m if method == "exact" else (hits + 1) / (m + 1)
    return {"p": float(p), "n": n, "method": method, "permutations": m, "hits": hits}


def achievable_alpha(n: int, alpha: float, alternative: str = "two-sided") -> float:
    """符号反転で作れる有意水準のうち ``alpha`` 以下で最大のもの(両側 2k/2^n・片側 k/2^n)。作れなければ 0。"""
    m = 1 << n
    step = 2.0 if alternative == "two-sided" else 1.0
    k = int(math.floor(alpha * m / step + 1e-12))
    return k * step / m


def perm_ci(d: Sequence[float], level: float = 0.95) -> dict[str, Any]:
    """符号反転の検定(両側・差の平均)を反転した区間(R-71 §4-2・Ernst 2004 §4.1)。

    到達できる水準は 1 − 2k/2^n で飛び飛び。``level`` 以上で最小の水準の区間を出す。作れない(n が小さい)ときは
    ``interval=None`` とし、作れる最も高い水準(k=1)の区間を ``interval_below`` に添える。
    区間は「その Δ を引いた差で検定が棄却しない Δ の集合」の両端(集合が 1 つの区間でなければ ``convex=False``)。
    """
    x = np.asarray(d, dtype=np.float64)
    n = int(x.size)
    if n < 2:
        return {"n": n, "interval": None, "note": "対が 2 未満"}
    if n > PERM_CI_MAX_N:
        return {"n": n, "interval": None, "note": f"対が {PERM_CI_MAX_N} を超える(t 区間を使う)"}
    a_target = 1.0 - float(level)
    s = _sign_matrix(n)
    ms = s.mean(axis=1)
    ts = s @ x / n
    mean_d = float(x.mean())
    tol = _REL_TOL * max(1.0, float(np.max(np.abs(x))))
    with np.errstate(divide="ignore", invalid="ignore"):
        b1 = np.where(ms != 1.0, (mean_d - ts) / (1.0 - ms), np.nan)
        b2 = np.where(ms != -1.0, (ts + mean_d) / (1.0 + ms), np.nan)
    bp = np.unique(np.concatenate([b1[np.isfinite(b1)], b2[np.isfinite(b2)], [mean_d]]))
    span = float(bp.max() - bp.min()) if bp.size else 1.0
    pts = np.concatenate([bp, (bp[:-1] + bp[1:]) / 2.0, [bp.min() - span - 1.0, bp.max() + span + 1.0]])
    pts = np.unique(pts)

    def pvals(alpha_eff: float) -> np.ndarray:
        out = np.empty(pts.size)
        for i0 in range(0, pts.size, 512):
            dl = pts[i0:i0 + 512]
            stat = ts[None, :] - dl[:, None] * ms[None, :]
            obs = np.abs(mean_d - dl)
            out[i0:i0 + 512] = np.mean(np.abs(stat) >= obs[:, None] - tol, axis=1)
        return out

    def interval(alpha_eff: float) -> dict[str, Any]:
        p = pvals(alpha_eff)
        acc = p > alpha_eff + 1e-15
        if not acc.any():
            return {"lo": None, "hi": None, "convex": True}
        idx = np.flatnonzero(acc)
        lo_i, hi_i = int(idx.min()), int(idx.max())
        convex = bool(acc[lo_i:hi_i + 1].all())
        return {"lo": float(pts[lo_i]), "hi": float(pts[hi_i]), "convex": convex}

    a_eff = achievable_alpha(n, a_target, "two-sided")
    out: dict[str, Any] = {"n": n, "level_target": float(level)}
    if a_eff > 0:
        out["level_achieved"] = 1.0 - a_eff
        out["interval"] = interval(a_eff)
    else:
        a_low = 2.0 / (1 << n)
        out["level_achieved"] = None
        out["interval"] = None
        out["interval_below"] = {"level": 1.0 - a_low, **interval(a_low)}
        out["note"] = (f"{n} 対では {level:.0%} 以上の区間は作れない(到達できる水準は 1 − 2k/2^{n})。"
                       f"作れる最も高い水準 {1.0 - a_low:.4f} の区間を interval_below に添えた")
    return out


# ---------------------------------------------------------------- 多重比較(R-71 §6)
def holm(pvals: Sequence[float], alpha: float = 0.05) -> dict[str, Any]:
    """Holm の逐次棄却(Holm 1979)。調整済みの p(単調にした max_{j≤i} (m−j+1)p_(j)・1 で頭打ち)と棄却。"""
    p = [float(x) for x in pvals]
    m = len(p)
    order = sorted(range(m), key=lambda i: (p[i], i))
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        adj[i] = running
    reject = [False] * m
    for rank, i in enumerate(order):
        if p[i] <= alpha / (m - rank):
            reject[i] = True
        else:
            break
    return {"adjusted": adj, "reject": reject, "thresholds": [alpha / (m - r) for r in range(m)]}


def bh(pvals: Sequence[float], alpha: float = 0.05) -> dict[str, Any]:
    """Benjamini-Hochberg(k̂ = max{k: p_(k) ≤ kα/m} まで棄却・Storey 2002 式 (12))。q 値(min_{j≥i} m p_(j)/j)。"""
    p = [float(x) for x in pvals]
    m = len(p)
    order = sorted(range(m), key=lambda i: (p[i], i))
    q = [0.0] * m
    running = 1.0
    for rank in range(m - 1, -1, -1):
        i = order[rank]
        running = min(running, p[i] * m / (rank + 1))
        q[i] = min(1.0, running)
    k_hat = 0
    for rank, i in enumerate(order):
        if p[i] <= (rank + 1) * alpha / m:
            k_hat = rank + 1
    reject = [False] * m
    for rank, i in enumerate(order):
        reject[i] = rank < k_hat
    return {"q": q, "reject": reject, "k_hat": k_hat}


# ---------------------------------------------------------------- 1 つの指標の対の統計
def _sd(x: np.ndarray) -> float:
    return float(np.std(x, ddof=1)) if x.size >= 2 else float("nan")


def _num(v: float | None) -> float | None:
    """JSON に出せる数(nan・inf は None)。"""
    if v is None:
        return None
    v = float(v)
    return v if math.isfinite(v) else None


def paired_stats(base: Sequence[float], arm: Sequence[float], *, alpha: float = 0.05, family_size: int = 1,
                 r_targets: Sequence[float] = (0.02, 0.01)) -> dict[str, Any]:
    """salt の対(同じ順)の値から、差・幅・差 ÷ 幅・ρ・区間・効果の大きさ・D-46 の本数を出す(検定の判定はしない)。"""
    b = np.asarray(base, dtype=np.float64)
    a = np.asarray(arm, dtype=np.float64)
    if b.shape != a.shape or b.ndim != 1:
        raise ValueError(f"基準と腕の値の数が違う({b.shape} と {a.shape})")
    n = int(b.size)
    d = a - b
    mb, ma, md = float(b.mean()), float(a.mean()), float(d.mean())
    sb, sa, sdd = _sd(b), _sd(a), _sd(d)
    out: dict[str, Any] = {
        "n_pairs": n, "base": b.tolist(), "arm": a.tolist(), "diffs": d.tolist(),
        "mean_base": mb, "mean_arm": ma,
        # ---- 差・幅・差 ÷ 幅(設計書 §5 の 3 列) ----
        "diff": md,
    }
    m = max(1, int(family_size))
    if n >= 2:
        tf = t_quantile(1.0 - alpha / (2.0 * m), n - 1)
        width = tf * sdd / math.sqrt(n)
        out.update({
            "width": width, "width_t": tf, "family_size": m,
            "width_base": tf * sb / math.sqrt(n), "width_arm": tf * sa / math.sqrt(n),
        })
        if width > 0:
            out["diff_over_width"] = md / width
        else:
            out["diff_over_width"] = None
            out["diff_over_width_note"] = "幅 0(対の差が全部同じ)" + ("・差も 0" if md == 0 else "・差は 0 でない")
    else:
        out.update({"width": None, "diff_over_width": None, "family_size": m})
    # 検収 S3-2: 幅に対の差の SD を使うので、|差 ÷ 幅| > 1 は「対の差の t 検定を α/m で棄却」と同じ意味になる
    out["diff_over_width_reading"] = DIFF_OVER_WIDTH_READING
    # ---- 効果の大きさ(R-71 §4-1) ----
    out["effect"] = {
        "raw_diff": md,
        "ratio_arm_over_base": (ma / mb) if mb != 0 else None,
        "sd_diff": _num(sdd),
        "d_z_crn_pair": _num(md / sdd) if (n >= 2 and sdd > 0) else None,
        "d_av": _num(md / ((sb + sa) / 2.0)) if (n >= 2 and (sb + sa) > 0) else None,
        "note": "d_z は CRN の対の値(差の SD が CRN で縮むほど大きい)。CRN の無い比較の d とは並べない",
    }
    # ---- ρ の実測(R-71 §1-1) ----
    vb, va, vd = sb * sb, sa * sa, sdd * sdd
    ratio = (vd / (vb + va)) if (n >= 2 and (vb + va) > 0) else None
    rho = ((vb + va - vd) / (2.0 * sb * sa)) if (n >= 2 and sb > 0 and sa > 0) else None
    out["crn"] = {
        "var_diff": _num(vd), "var_base": _num(vb), "var_arm": _num(va),
        "var_ratio": _num(ratio), "rho": _num(rho),
        "rho_readable": n >= 5,
        # 検収 S3-5: 警告は 5 対以上だけ(5 対未満は比が 1 を超えても読まない=``ratio_over_1_unread``)
        "warn_ratio_over_1": bool(ratio is not None and ratio > 1.0 and n >= 5),
        "ratio_over_1_unread": bool(ratio is not None and ratio > 1.0 and n < 5),
        "note": "比 = Var(D)/(Var(基準)+Var(腕))。1 を超えたら CRN で損(独立に回すより差の分散が大きい)。5 対未満は読まない",
    }
    # ---- 区間(R-71 §4-2) ----
    if n >= 2:
        t975 = t_quantile(0.975, n - 1)
        hw = t975 * sdd / math.sqrt(n)
        out["ci_t95"] = {"lo": md - hw, "hi": md + hw, "half_width": hw, "t": t975}
    else:
        out["ci_t95"] = None
    out["ci_perm"] = perm_ci(d, 0.95)
    # ---- D-46 の式の 2 通り(R-71 §5-1) ----
    d46: dict[str, Any] = {"r_targets": [float(r) for r in r_targets]}
    if n >= 2 and mb != 0:
        cv_b = sb / abs(mb)
        cv_d = sdd / abs(mb)
        for name, cv in (("cv_base", cv_b), ("cv_diff", cv_d)):
            d46[name] = {
                "cv": cv,
                "relative_se_now": cv / math.sqrt(n),
                "halfwidth95_now": t_quantile(0.975, n - 1) * cv / math.sqrt(n),
                "n_relative_se": {str(r): n_relative_se(cv, r) for r in r_targets},
                "n_halfwidth95": {str(r): n_halfwidth95(cv, r) for r in r_targets},
            }
    else:
        d46["note"] = "対が 2 未満か基準の平均が 0(CV が定義できない)"
    d46["note_formula"] = ("n_relative_se=ceil((CV/r)^2) は相対の標準誤差を r にする本数(D-46 の式)。"
                           "n_halfwidth95 は 95% の区間の半幅を r にする本数(t を入れた式)。別の物")
    out["d46"] = d46
    return out


# ---------------------------------------------------------------- 指標の一覧と線
def _metric_list(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    prim = spec.get("primary")
    if isinstance(prim, list):
        if len(prim) != 1:
            raise ValueError(f"主要な指標は 1 つ(いま {len(prim)})")
        prim = prim[0]
    if prim:
        out.append({**prim, "role": "primary"})
    out += [{**m, "role": "secondary"} for m in spec.get("secondary", []) or []]
    out += [{**m, "role": "exploratory"} for m in spec.get("exploratory", []) or []]
    ids = [m.get("id") or m.get("path") for m in out]
    if len(set(ids)) != len(ids):
        raise ValueError(f"指標の id が重なる: {ids}")
    for m in out:
        m["id"] = m.get("id") or m.get("path")
    return out


def _alternative(metric: Mapping[str, Any]) -> tuple[str, str]:
    """(使う向き, 理由)。片側は事前登録の印と向きがあるときだけ。"""
    direction = metric.get("direction")
    if direction in ("greater", "less") and bool(metric.get("preregistered", False)):
        return str(direction), "片側(向きを事前登録)"
    if direction in ("greater", "less"):
        return "two-sided", "向きはあるが事前登録の印が無い=両側で扱う"
    return "two-sided", "両側"


def analyze(values: Mapping[str, Mapping[str, Sequence[float]]], spec: Mapping[str, Any]) -> dict[str, Any]:
    """指標ごとの値の組(``{id: {"base": [...], "arm": [...]}}``)と指標の一覧から、線・多重比較つきの表を作る。"""
    alpha = float(spec.get("alpha", 0.05))
    metrics = _metric_list(spec)
    fam = int(spec.get("family_size") or len(metrics) or 1)
    r_targets = tuple(float(r) for r in spec.get("r_targets", (0.02, 0.01)))
    rows: dict[str, dict[str, Any]] = {}
    for m in metrics:
        v = values.get(m["id"])
        if v is None:
            raise KeyError(f"指標 {m['id']!r} の値が無い")
        st = paired_stats(v["base"], v["arm"], alpha=alpha, family_size=fam, r_targets=r_targets)
        alt, why = _alternative(m)
        test = sign_flip_p(st["diffs"], alt)
        st["role"] = m["role"]
        st["path"] = m.get("path")
        st["alternative"] = alt
        st["alternative_reason"] = why
        st["p"] = test["p"]
        st["p_method"] = test["method"]
        st["p_floor"] = p_floor(st["n_pairs"], alt)
        st["p_two_sided"] = sign_flip_p(st["diffs"], "two-sided")["p"]
        rows[m["id"]] = st
    # ---- 線: その指標が受ける最も厳しい閾値に p の下限が届くか ----
    sec = [k for k, r in rows.items() if r["role"] == "secondary"]
    exp = [k for k, r in rows.items() if r["role"] == "exploratory"]
    for k, r in rows.items():
        if r["role"] == "primary":
            line = alpha
        elif r["role"] == "secondary":
            line = alpha / max(1, len(sec))  # Holm の最初の閾値
        else:
            line = alpha  # BH の最も緩い閾値(全部が小さいとき)
        r["line"] = line
        r["status"] = TESTED if r["p_floor"] <= line + 1e-15 else DESCRIPTIVE
        if r["status"] == DESCRIPTIVE:
            r["status_note"] = (f"{r['n_pairs']} 対の p の下限 {r['p_floor']:.4g}({r['alternative']})が線 {line:.4g} を超える。"
                                "検定はしない(差・幅・差 ÷ 幅は記述として読む。差 ÷ 幅が 1 を超えても K20 (a) の検定ではない)")
    # ---- 判定 ----
    for k, r in rows.items():
        if r["role"] == "primary":
            r["decision"] = (bool(r["p"] <= alpha) if r["status"] == TESTED else None)
    if sec:
        h = holm([rows[k]["p"] for k in sec], alpha)
        for i, k in enumerate(sec):
            rows[k]["p_holm"] = h["adjusted"][i]
            rows[k]["decision"] = h["reject"][i] if rows[k]["status"] == TESTED else None
    if exp:
        q = bh([rows[k]["p"] for k in exp], alpha)
        for i, k in enumerate(exp):
            rows[k]["q_bh"] = q["q"][i]
            rows[k]["decision"] = q["reject"][i] if rows[k]["status"] == TESTED else None
    n_set = sorted({r["n_pairs"] for r in rows.values()})
    return {
        "alpha": alpha, "family_size": fam, "n_pairs": n_set,
        "overall": (DESCRIPTIVE if any(r["status"] == DESCRIPTIVE for r in rows.values()) else TESTED),
        "metrics": rows,
        "rule": ("K20 (a): 3/5/3 本のまま。p の下限(片側 1/2^n・両側 2/2^n)が線に届かなければ記述のみ(本数不足)。"
                 "外に出す主張の前だけ 6 対(片側なら事前登録して 5 対)"),
    }


# ---------------------------------------------------------------- checkpoints の JSON からの値と CRN の健全性
def get_path(doc: Mapping[str, Any], path: str) -> Any:
    """``a.b.c`` の道筋で入れ子の辞書を引く(無ければ ``KeyError``)。"""
    cur: Any = doc
    for part in path.split("."):
        if isinstance(cur, Mapping) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(f"道筋 {path!r} が無い({part!r} で止まった)")
    return cur


def _load_module(path: Path, name: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _sx() -> Any:
    return _load_module(HERE / "seed_exchangeability.py", "seed_exchangeability")


def _fd() -> Any:
    return _load_module(FIRST_DIFF, "first_diff_10d")


def first_divergence(a: Mapping[str, Any], b: Mapping[str, Any], *, from_T: int = 0) -> dict[str, Any]:
    """2 本の checkpoints の JSON の最初に食い違う checkpoint(``first_diff.compare`` を使う)と、どの hash が違うか。"""
    fd = _fd()

    def as_dump(doc: Mapping[str, Any]) -> dict[str, Any]:
        return {"checkpoints": [[int(c["tick"]), c.get("combined"), c.get("behavior_hash"), c.get("full_hash")]
                                for c in doc.get("checkpoints", [])],
                "resume": {"start_T": int(from_T)}}

    rep = fd.compare(as_dump(a), [as_dump(b)], from_T=int(from_T))
    fm = rep.get("first_mismatch")
    out: dict[str, Any] = {"from_T": int(from_T), "checkpoints_compared": int(rep["checkpoints_compared"]),
                           "first_tick": (int(fm["tick"]) if fm else None)}
    if fm:
        ca = {int(c["tick"]): c for c in a["checkpoints"]}[int(fm["tick"])]
        cb = {int(c["tick"]): c for c in b["checkpoints"]}[int(fm["tick"])]
        out["hashes_differ"] = sorted(k for k in ("agents_hash", "world_hash", "activity_hash", "behavior_hash",
                                                  "full_hash", "combined", "population_hash", "schedule_hash")
                                      if ca.get(k) != cb.get(k))
        prev = [int(c["tick"]) for c in a["checkpoints"] if int(c["tick"]) < int(fm["tick"])]
        out["last_match_tick"] = max(prev) if prev else None
    return out


#: 環境の seed から導かれる設定の欄(気象の再生実日とそれに合わせた暦・10f 第 2 段の直し S1)。「天気も変える」
#: salt の比較(環境の seed が salt とともに違う)では、同じ腕の salt の間のこの欄の差を許して報告する。
ENVIRONMENT_DERIVED_PATHS: tuple[str, ...] = ("replay_date", "start_sim_datetime", "calendar")
UNCHECKED = "未検査"


def seed_key(v: Any) -> str:
    """seed の比べ方(検収 S3-8): 型も見る(``1`` と ``"1"`` は ``core.rng`` で別の鍵=``i:1`` と ``s:1``)。"""
    return "None" if v is None else f"{type(v).__name__}:{v}"


def pre_t0_match(a: Mapping[str, Any], b: Mapping[str, Any], t0: int) -> dict[str, Any]:
    """T0 より前の checkpoint(tick < T0)の behavior-hash が全部一致するか(R-71 §8-1 の 2)。

    T0 = 0 は対象外(腕は最初から違う=``ok: True``・``status: "対象外"``)。T0 > 0 なのに T0 より前の checkpoint が
    1 本も無いときは確かめていないので ``ok: None``・``status: "未検査"``(検収 S2)。
    """
    ca = {int(c["tick"]): c for c in a.get("checkpoints", [])}
    cb = {int(c["tick"]): c for c in b.get("checkpoints", [])}
    ticks = sorted(t for t in set(ca) & set(cb) if t < int(t0))
    bad = [t for t in ticks if ca[t].get("behavior_hash") != cb[t].get("behavior_hash")]
    out: dict[str, Any] = {"T0": int(t0), "checkpoints_before_T0": len(ticks), "first_bad_tick": (bad[0] if bad else None)}
    if int(t0) <= 0:
        out.update(ok=True, status="対象外", note="T0=0: T0 より前の checkpoint は無い(腕は最初から違う)")
    elif not ticks:
        out.update(ok=None, status=UNCHECKED, note="T0 > 0 なのに T0 より前の checkpoint が無い(checkpoint の間隔を狭める)")
    else:
        out.update(ok=not bad, status=("ok" if not bad else "fail"), note="")
    return out


def aa_match(a: Mapping[str, Any], b: Mapping[str, Any]) -> dict[str, Any]:
    """A/A: 同じ設定・同じ seed の 2 本が全 checkpoint(combined・behavior・full)と final で一致するか。"""
    ca = [[int(c["tick"]), c.get("combined"), c.get("behavior_hash"), c.get("full_hash")] for c in a.get("checkpoints", [])]
    cb = [[int(c["tick"]), c.get("combined"), c.get("behavior_hash"), c.get("full_hash")] for c in b.get("checkpoints", [])]
    fd = first_divergence(a, b) if ca and cb else {"first_tick": None}
    ok = ca == cb and a.get("final_hash") == b.get("final_hash")
    return {"ok": bool(ok), "checkpoints": len(ca), "final_same": a.get("final_hash") == b.get("final_hash"),
            "first_tick": fd.get("first_tick")}


def arm_keys_of(arm_a: Mapping[str, Any], arm_b: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    """腕の欄(検収 S3-4): 2 つの腕で値が違う引数(片方だけにある引数を含む)だけ。

    返り値は (腕の欄, 下の木も許す欄)。下の木を許すのは、値が辞書の引数(manifest で ``名前.鍵`` に開く)だけ。
    """
    keys, trees = [], []
    for k in sorted(set(arm_a) | set(arm_b)):
        va, vb = arm_a.get(k, _MISSING), arm_b.get(k, _MISSING)
        if va == vb:
            continue
        keys.append(str(k))
        if isinstance(va, Mapping) or isinstance(vb, Mapping):
            trees.append(str(k))
    return keys, trees


_MISSING = object()


def _check_derived(derived: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    """``arm_keys_derived`` の形(検収 S3-3): ``{道筋: {"base": 値, "arm": 値, "reason": 理由}}``。"""
    out: dict[str, dict[str, Any]] = {}
    for k, v in (derived or {}).items():
        if not isinstance(v, Mapping) or not {"base", "arm", "reason"} <= set(v):
            raise ValueError(f"arm_keys_derived の {k!r} は {{\"base\": 値, \"arm\": 値, \"reason\": 理由}} の形で書く"
                             "(期待する値を書かせる=検収 S3-3)")
        out[str(k)] = {"base": v["base"], "arm": v["arm"], "reason": str(v["reason"])}
    return out


def input_match(base_docs: Sequence[Mapping[str, Any]], arm_docs: Sequence[Mapping[str, Any]],
                arm_keys: Sequence[str], *, tree_keys: Sequence[str] = (),
                derived: Mapping[str, Any] | None = None,
                environment_mode: str | None = None) -> dict[str, Any]:
    """入力の一致(R-71 §8-1 の 1・K21 (a)・10f 第 2 段の直し S1)。

    - 対(同じ salt)の間: manifest の**設定の節**の差が、腕の欄(``arm_keys`` は道筋の完全一致・``tree_keys`` だけ
      下の木も)か、宣言した導かれる欄(``derived``・**宣言した値と実際の値が一致**)の中だけ。seed・母集団の seed・
      環境の seed が同じ。
    - salt の間(同じ腕): ``seed_exchangeability.compare`` が交換可能。``environment_mode="salt"`` で環境の seed が
      salt とともに違うときは、環境から導かれる欄(``ENVIRONMENT_DERIVED_PATHS``)の差を許して報告する。
    - 全部のラン: 母集団の seed が同じ・最初の checkpoint の母集団と日課のハッシュが同じ。``environment_mode="fixed"``
      なら環境の seed も全部同じ。
    """
    sx = _sx()
    dv = _check_derived(derived)
    keys = [str(k) for k in arm_keys]
    trees = [str(k) for k in tree_keys]

    def in_arm(path: str) -> bool:
        return path in keys or path in dv or any(path.startswith(k + ".") for k in trees)

    def mval(doc: Mapping[str, Any], name: str) -> Any:
        return (doc.get("manifest") or {}).get(name)

    pairs = []
    ok = True
    derived_bad: list[dict[str, Any]] = []
    for i, (b, a) in enumerate(zip(base_docs, arm_docs)):
        paths = sx._sections_paths([b, a])
        fb = sx.flatten({"manifest": b.get("manifest", {})})
        fa = sx.flatten({"manifest": a.get("manifest", {})})
        diff_cfg, outside, values = [], [], {}
        for k in sorted(set(fb) | set(fa)):
            if sx._norm(fb.get(k)) == sx._norm(fa.get(k)):
                continue
            sub = k[len("manifest."):]
            sec = sx.section_of(sub, paths) if paths is not None else "config"
            if sec in ("observed", "environment"):
                continue
            diff_cfg.append(sub)
            values[sub] = {"base": fb.get(k), "arm": fa.get(k)}
            if not in_arm(sub):
                outside.append(sub)
        for path, want in dv.items():
            got_b, got_a = fb.get("manifest." + path), fa.get("manifest." + path)
            if sx._norm(got_b) != sx._norm(want["base"]) or sx._norm(got_a) != sx._norm(want["arm"]):
                derived_bad.append({"pair": i, "path": path, "declared": {"base": want["base"], "arm": want["arm"]},
                                    "actual": {"base": got_b, "arm": got_a}})
        same_seed = seed_key(b.get("seed")) == seed_key(a.get("seed"))
        same_pop = seed_key(mval(b, "population_seed")) == seed_key(mval(a, "population_seed"))
        same_env = seed_key(mval(b, "environment_seed")) == seed_key(mval(a, "environment_seed"))
        row = {"pair": i, "seed": b.get("seed"), "same_seed": same_seed, "same_population_seed": same_pop,
               "same_environment_seed": same_env, "config_diffs": diff_cfg, "config_diff_values": values,
               "config_diffs_outside_arm": outside}
        pairs.append(row)
        ok = ok and same_seed and same_pop and same_env and not outside
    ok = ok and not derived_bad
    all_docs = list(base_docs) + list(arm_docs)
    env_seeds = {seed_key(mval(d, "environment_seed")) for d in all_docs}
    environment_fixed = len(env_seeds) == 1 and "None" not in env_seeds
    within = {}
    for label, docs in (("base", base_docs), ("arm", arm_docs)):
        if len(docs) >= 2:
            r = sx.compare(list(docs), [f"{label}{i}" for i in range(len(docs))])
            unexplained = [u["key"] for u in r["diff_unexplained"]]
            env_derived: list[str] = []
            if environment_mode == "salt" and r.get("environment_seed_varies"):
                env_derived = [k for k in unexplained
                               if any(k[len("manifest."):] == p or k[len("manifest."):].startswith(p + ".")
                                      for p in ENVIRONMENT_DERIVED_PATHS)]
                unexplained = [k for k in unexplained if k not in env_derived]
            exch = not r["must_match_failures"] and r["checkpoint_ticks_match"] and not unexplained
            within[label] = {"exchangeable": exch, "unexplained": unexplained,
                             "environment_derived_diffs": env_derived,
                             "population_seed_varies": r.get("population_seed_varies"),
                             "environment_seed_varies": r.get("environment_seed_varies"), "mode": r["mode"]}
            ok = ok and exch
    pop_seeds = {seed_key(mval(d, "population_seed")) for d in all_docs}
    first = [d["checkpoints"][0] for d in all_docs if d.get("checkpoints")]
    pop_hashes = {c.get("population_hash") for c in first}
    sched_hashes = {c.get("schedule_hash") for c in first}
    population_fixed = len(pop_seeds) == 1 and "None" not in pop_seeds
    inputs_same = len(pop_hashes) <= 1 and len(sched_hashes) <= 1
    ok = ok and population_fixed and inputs_same
    if environment_mode == "fixed":
        ok = ok and environment_fixed
    seen = {p for row in pairs for p in row["config_diffs"]}
    unseen = sorted(k for k in keys if not any(p == k or p.startswith(k + ".") for p in seen))
    return {"ok": bool(ok), "pairs": pairs, "within_arm": within,
            "population_seed": sorted(pop_seeds), "population_fixed": population_fixed,
            "environment_mode": environment_mode, "environment_seed": sorted(env_seeds),
            "environment_fixed": environment_fixed,
            "population_hash_same": len(pop_hashes) <= 1, "schedule_hash_same": len(sched_hashes) <= 1,
            "arm_keys": keys, "arm_tree_keys": trees,
            "arm_keys_derived": dv, "arm_keys_derived_mismatch": derived_bad,
            # 腕の欄のうち、どの対の設定の差にも出てこないもの(manifest に載っていない腕)=報告だけ
            "arm_keys_unseen": unseen}


def crn_health(index: Mapping[str, Any], payloads: Mapping[str, Mapping[str, Any]],
               derived_keys: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """``salt_runs.py`` の索引と読んだ checkpoints の JSON から CRN の健全性をまとめる。

    ``derived_keys``: 腕の引数から**導かれて**変わる設定の欄(例 語彙の版 → ``synonym_table_version``)を
    ``{道筋: {"base": 値, "arm": 値, "reason": 理由}}`` で宣言したもの。実際の値が宣言と違えば落ちる(検収 S3-3)。

    全体の ``ok`` は 3 つの値(検収 S2): ``True``=全部を確かめて全部通った / ``False``=どれかが落ちた /
    ``None``=落ちたものは無いが確かめていないものがある(A/A のランが無い・T0 > 0 で T0 より前の checkpoint が
    無い)。``status`` に ``ok``・``fail``・``未検査`` を、``unchecked`` に確かめていないものを書く。
    """
    runs = index["runs"]
    base, arm = index["base"], index["arm"]
    salts = list(index["salts"])
    by = {(r["arm"], r["salt"]): payloads[r["checkpoints"]] for r in runs if not r.get("aa")}
    bdocs = [by[(base, s)] for s in salts]
    adocs = [by[(arm, s)] for s in salts]
    keys, trees = arm_keys_of(index["arms"][base], index["arms"][arm])
    out: dict[str, Any] = {"input_match": input_match(bdocs, adocs, keys, tree_keys=trees, derived=derived_keys,
                                                      environment_mode=index.get("environment_mode"))}
    t0 = int(index.get("T0", 0))
    out["pre_t0"] = [dict(salt=s, **pre_t0_match(by[(base, s)], by[(arm, s)], t0)) for s in salts]
    out["first_divergence_coarse"] = [dict(salt=s, **first_divergence(by[(base, s)], by[(arm, s)])) for s in salts]
    fine = index.get("first_diff_fine") or {}
    out["first_divergence_fine"] = [dict(salt=int(k), **v) for k, v in sorted(fine.items(), key=lambda kv: int(kv[0]))]
    aa = [r for r in runs if r.get("aa")]
    out["aa"] = []
    for r in aa:
        twin = by[(r["arm"], r["salt"])]
        out["aa"].append(dict(arm=r["arm"], salt=r["salt"], **aa_match(twin, payloads[r["checkpoints"]])))
    failed = (not out["input_match"]["ok"] or any(x["ok"] is False for x in out["pre_t0"])
              or any(x["ok"] is False for x in out["aa"]))
    unchecked = []
    if not aa:
        unchecked.append("A/A のランが無い(salt_runs.py --aa で回す)")
    if any(x["ok"] is None for x in out["pre_t0"]):
        unchecked.append("T0 より前の checkpoint が無い対がある")
    out["unchecked"] = unchecked
    if failed:
        out["ok"], out["status"] = False, "fail"
    elif unchecked:
        out["ok"], out["status"] = None, UNCHECKED
    else:
        out["ok"], out["status"] = True, "ok"
    return out


def values_from_payloads(index: Mapping[str, Any], payloads: Mapping[str, Mapping[str, Any]],
                         metrics: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, list[float]]]:
    """索引の salt の順に、基準と腕の指標の値を集める。"""
    by = {(r["arm"], r["salt"]): payloads[r["checkpoints"]] for r in index["runs"] if not r.get("aa")}
    out: dict[str, dict[str, list[float]]] = {}
    for m in metrics:
        out[m["id"]] = {
            "base": [float(get_path(by[(index["base"], s)], m["path"])) for s in index["salts"]],
            "arm": [float(get_path(by[(index["arm"], s)], m["path"])) for s in index["salts"]],
        }
    return out


def report(index: Mapping[str, Any], payloads: Mapping[str, Mapping[str, Any]],
           spec: Mapping[str, Any]) -> dict[str, Any]:
    """索引+checkpoints の JSON+指標の一覧 → 報告(純関数)。"""
    metrics = _metric_list(spec)
    vals = values_from_payloads(index, payloads, metrics)
    res = analyze(vals, spec)
    return {"schema": SCHEMA, "base": index["base"], "arm": index["arm"], "salts": list(index["salts"]),
            "population_seed": index.get("population_seed"), "T0": int(index.get("T0", 0)),
            "environment_mode": index.get("environment_mode"), "environment_seed": index.get("environment_seed"),
            "analysis": res, "crn": crn_health(index, payloads, spec.get("arm_keys_derived")),
            "wall_seconds": index.get("wall_seconds")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--runs", help="salt_runs.py の索引(runs.json)")
    src.add_argument("--values", help="計器の値の組の JSON({id: {base: [...], arm: [...]}})")
    ap.add_argument("--metrics", required=True, help="指標の一覧(主要・副次・探索)の JSON")
    ap.add_argument("--out", required=True, help="報告の JSON(既存のファイルへは書かない)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists():
        print(f"refuse: {out.name} は既にある", file=sys.stderr)
        return 2
    spec = json.loads(Path(a.metrics).read_text(encoding="utf-8"))
    if a.runs:
        idx_path = Path(a.runs)
        index = json.loads(idx_path.read_text(encoding="utf-8"))
        payloads = {r["checkpoints"]: json.loads((idx_path.parent / r["checkpoints"]).read_text(encoding="utf-8"))
                    for r in index["runs"]}
        rep = report(index, payloads, spec)
    else:
        rep = {"schema": SCHEMA, "analysis": analyze(json.loads(Path(a.values).read_text(encoding="utf-8")), spec)}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    an = rep["analysis"]
    print(f"overall={an['overall']} n_pairs={an['n_pairs']}")
    for k, r in an["metrics"].items():
        dow = r.get("diff_over_width")
        print(f"  {r['role']:<11} {k}: n={r['n_pairs']} diff={r['diff']:.6g} width={r.get('width')} "
              f"diff/width={dow if dow is None else round(dow, 3)} p={r['p']:.4g}(floor {r['p_floor']:.4g}) "
              f"rho={r['crn']['rho']} status={r['status']}")
    if "crn" in rep:
        print(f"  crn ok={rep['crn']['ok']} status={rep['crn']['status']} input_match={rep['crn']['input_match']['ok']}"
              f" unchecked={rep['crn']['unchecked']}")
        return exit_code(rep["crn"])
    return 0


#: ``main`` の終了コード(再検収 T5): CRN の健全性が ok なら 0・fail なら 1・未検査なら 3(2 は既存のファイルの拒否)。
EXIT_OK, EXIT_FAIL, EXIT_REFUSE, EXIT_UNCHECKED = 0, 1, 2, 3


def exit_code(crn: Mapping[str, Any]) -> int:
    """CRN の健全性の ``status`` → 終了コード(``ok`` 0・``fail`` 1・``未検査`` 3)。"""
    return {"ok": EXIT_OK, "fail": EXIT_FAIL}.get(str(crn.get("status")), EXIT_UNCHECKED)


if __name__ == "__main__":
    raise SystemExit(main())
