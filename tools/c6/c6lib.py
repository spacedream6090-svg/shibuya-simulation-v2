# -*- coding: utf-8 -*-
"""c6lib — C6-b 検証ハーネスの純関数と共通部品(標準ライブラリ + numpy/httpx)。

位置づけ
    ``tools/c6/*.py`` の 5 本のツール(T6/T7/指標B/ablation①/書式・役割語率)が共有する
    「計算の部分」だけを集めた。**ここには実サーバーへの接続も乱数の副作用も置かない**
    (HTTP は ``chat_once`` 一本・呼び出し側が endpoint を渡したときだけ動く)。
    ``tests/c6`` がこのモジュールをモック入力で検査する。

正典(数値・規則の出どころ)
- 運用設計書 §1.4 **T3**(並列不変性=スレッド 1/8/32 で同一結果)・**T5**(順序バイアス=
  24step スモークで個体 ID 順との相関 **|r| ≤ 0.05**)・**T6**(LLM 層 bit 再現・不一致なら
  「この機・この版では bit 再現を主張しない」と記録)・**T7**(LLM 層分布同値)・**T9**
  (診断行 4 列 + 保存則 2 検算の存在)。
- 知覚契約書 §8「指標Bの事前登録」= **制約種ごと n≥50(5種=250場面)+「答えが決まる場面」
  100 場面**・閾値 **JSD(v0,v1) ≤ 帰無95%点**(同分布2標本のブートストラップ)・
  **|Δ違反率| の 95%CI 上限 ≤ 0.05**。
- 知覚契約書 §2.5 / 実装計画書 §9.1 C6: **書式エラー率 ≤ 0.10**(温度 0.7・実 LLM・n≥59)。
- 予算宣言表 **L4**(上限 400 万呼/日・平均 10 呼/体/日)・**L6**(64 in-flight/GPU)。
- 品質プローブv0 ``tools/quality_probe_v0/scorer.py``: 制約違反率と行動分布の測り方
  (JSD は bits・帰無参照は同分布 2 標本・ブートストラップは場面の復元抽出)。

自前の細部(expedient・登録簿 §8 へ写す)
- ``classify_scene`` の「答えが決まる場面」判定 = **駆動因が 1 つ以上ある場面**
  (①内受容の閾値割れが B5 に出ている ②起床が計画境界クラス ③直前の結果が失敗)。
  品質プローブv0 の mid 層(閉店間際・段階・条例=駆動因を必ず 1 つ入れた場面)の
  実データ版としてエンジン側の観測だけで決まる規則にした。文献根拠は無い。
- 制約種 = ``agents.state.ResultCode`` の失敗系のうち **5 種**
  (営業時間外 CLOSED / 所持金不足 MONEY_SHORT / 満員 TRAIN_FULL / 移動不能 UNREACHABLE /
  会話拒否 REFUSED)。契約書 §8 は「制約種ごと n≥50(5種)」としか書いていないので、
  どの 5 種かは本モジュールの選択(親判断待ちで登録)。
- 場面の抽出順 = ``blake3`` ではなく ``hashlib.sha256(agent_id, tick, wake_class)`` の昇順
  (ツール側は世界の乱数系に混ざらないので core.rng を使わない)。
- 帰無参照の標本数 ``NULL_REPS=2000``・ブートストラップ ``BOOT_REPS=4000``
  (品質プローブv0 の 2,000/4,000 に合わせた)。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np

# ---------------------------------------------------------------- ブートストラップ(src を見つける)

_HERE = Path(os.path.abspath(__file__)).parent
REPO_ROOT = _HERE.parent.parent
_SRC = REPO_ROOT / "src"
if str(_SRC) not in sys.path:  # pragma: no cover - 実行時の経路
    sys.path.insert(0, str(_SRC))

#: 帰無参照(同分布 2 標本)の反復数。
NULL_REPS: int = 2_000
#: ブートストラップの反復数。
BOOT_REPS: int = 4_000
#: T5 の相関の上限(運用設計書 §1.4 T5「|r| ≤ 0.05」)。
T5_MAX_ABS_R: float = 0.05
#: 書式エラー率の上限(知覚契約書 §10.3 / 実装計画書 §9.1 C6)。
FORMAT_ERROR_MAX: float = 0.10
#: 書式エラー率の最小標本数(B11 実測の n=59 に合わせる)。
FORMAT_ERROR_MIN_N: int = 59
#: 指標B の事前登録(知覚契約書 §8)。
METRIC_B_PER_KIND: int = 50
METRIC_B_DETERMINED: int = 100
METRIC_B_VIOLATION_CI_MAX: float = 0.05


# ================================================================ 統計(純関数)


def rankdata(x: Sequence[float]) -> np.ndarray:
    """同順位を平均順位にする順位付け(scipy を使わない)。"""
    a = np.asarray(x, dtype=np.float64)
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(a.size, dtype=np.float64)
    ranks[order] = np.arange(1, a.size + 1, dtype=np.float64)
    # 同値の平均化
    sorted_a = a[order]
    i = 0
    while i < a.size:
        j = i
        while j + 1 < a.size and sorted_a[j + 1] == sorted_a[i]:
            j += 1
        if j > i:
            ranks[order[i : j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return ranks


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    """Pearson の r(片側の分散が 0 なら 0.0=「相関を検出しない」)。"""
    a = np.asarray(x, dtype=np.float64)
    b = np.asarray(y, dtype=np.float64)
    m = np.isfinite(a) & np.isfinite(b)
    a, b = a[m], b[m]
    if a.size < 3 or float(np.std(a)) == 0.0 or float(np.std(b)) == 0.0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    """Spearman の ρ(順位相関)。"""
    a = np.asarray(x, dtype=np.float64)
    b = np.asarray(y, dtype=np.float64)
    m = np.isfinite(a) & np.isfinite(b)
    a, b = a[m], b[m]
    if a.size < 3:
        return 0.0
    return pearson(rankdata(a), rankdata(b))


def ks_2samp(x: Sequence[float], y: Sequence[float]) -> tuple[float, float]:
    """2 標本 Kolmogorov-Smirnov(D と漸近 p 値)。

    p = 2 Σ_{j≥1} (−1)^{j−1} exp(−2 j² λ²)、λ=(√n_e + 0.12 + 0.11/√n_e) D。
    """
    a = np.sort(np.asarray(x, dtype=np.float64))
    b = np.sort(np.asarray(y, dtype=np.float64))
    if a.size == 0 or b.size == 0:
        return 0.0, 1.0
    allv = np.concatenate([a, b])
    cdf1 = np.searchsorted(a, allv, side="right") / a.size
    cdf2 = np.searchsorted(b, allv, side="right") / b.size
    d = float(np.max(np.abs(cdf1 - cdf2)))
    en = math.sqrt(a.size * b.size / (a.size + b.size))
    lam = (en + 0.12 + 0.11 / en) * d
    if lam < 0.2:  # 交代級数が収束しない領域(D≈0)。Q_KS(λ→0)=1。
        return d, 1.0
    p = 2.0 * sum((-1) ** (j - 1) * math.exp(-2.0 * j * j * lam * lam) for j in range(1, 101))
    return d, float(min(max(p, 0.0), 1.0))


def _kl(p: np.ndarray, q: np.ndarray, base: float) -> float:
    m = p > 0
    return float(np.sum(p[m] * np.log(p[m] / q[m]) / math.log(base)))


def jsd(p: Sequence[float], q: Sequence[float], base: float = 2.0) -> float:
    """Jensen-Shannon divergence(既定 bits・品質プローブv0 と同じ単位)。"""
    a = np.asarray(p, dtype=np.float64)
    b = np.asarray(q, dtype=np.float64)
    sa, sb = a.sum(), b.sum()
    if sa <= 0 or sb <= 0:
        return 0.0
    a, b = a / sa, b / sb
    m = 0.5 * (a + b)
    return 0.5 * _kl(a, m, base) + 0.5 * _kl(b, m, base)


def align_counts(
    a: Mapping[str, float], b: Mapping[str, float], keys: Sequence[str] | None = None
) -> tuple[list[str], np.ndarray, np.ndarray]:
    """2 つの計数辞書を同じ鍵の並び(既定=和集合の昇順)へ揃える。"""
    ks = list(keys) if keys is not None else sorted(set(a) | set(b))
    va = np.array([float(a.get(k, 0.0)) for k in ks], dtype=np.float64)
    vb = np.array([float(b.get(k, 0.0)) for k in ks], dtype=np.float64)
    return ks, va, vb


def jsd_counts(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    """計数辞書 2 本の JSD[bits]。"""
    _, va, vb = align_counts(a, b)
    return jsd(va, vb)


def null_jsd_reference(
    counts: Mapping[str, float], n_a: int, n_b: int, reps: int = NULL_REPS, seed: int = 20260909
) -> dict[str, float]:
    """**帰無参照**: 同一分布から n_a / n_b 件ずつ引いた 2 標本の JSD 分布。

    知覚契約書 §8「JSD(v0,v1) ≤ 帰無95%点(同分布2標本のブートストラップ)」の分母。
    """
    _, p, _ = align_counts(counts, counts)
    total = p.sum()
    if total <= 0 or n_a <= 0 or n_b <= 0:
        return {"p50": 0.0, "p95": 0.0, "reps": 0}
    p = p / total
    rng = np.random.default_rng(seed)
    vals = np.empty(reps, dtype=np.float64)
    for i in range(reps):
        vals[i] = jsd(rng.multinomial(n_a, p), rng.multinomial(n_b, p))
    return {
        "p50": float(np.percentile(vals, 50)),
        "p95": float(np.percentile(vals, 95)),
        "reps": int(reps),
    }


def bootstrap_mean_ci(
    values: Sequence[float], reps: int = BOOT_REPS, seed: int = 20260909, alpha: float = 0.05
) -> tuple[float, float, float]:
    """平均のブートストラップ CI(復元抽出)。返り値 = (点推定, 下限, 上限)。"""
    v = np.asarray(values, dtype=np.float64)
    if v.size == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = v[rng.integers(0, v.size, size=(reps, v.size))].mean(axis=1)
    lo = float(np.percentile(means, 100 * alpha / 2))
    hi = float(np.percentile(means, 100 * (1 - alpha / 2)))
    return float(v.mean()), lo, hi


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """二項比率の Wilson 信頼区間(品質プローブv0 の ``wilson_ci`` と同定義)。"""
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - r) / d), min(1.0, (c + r) / d)


# ---- χ²(自前の不完全ガンマ関数。scipy 非依存) ----


def _gammln(x: float) -> float:
    cof = (
        76.18009172947146, -86.50532032941677, 24.01409824083091,
        -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5,
    )
    y = x
    tmp = x + 5.5
    tmp -= (x + 0.5) * math.log(tmp)
    ser = 1.000000000190015
    for c in cof:
        y += 1.0
        ser += c / y
    return -tmp + math.log(2.5066282746310005 * ser / x)


def _gser(a: float, x: float) -> float:
    ap = a
    s = 1.0 / a
    d = s
    for _ in range(1000):
        ap += 1.0
        d *= x / ap
        s += d
        if abs(d) < abs(s) * 1e-14:
            break
    return s * math.exp(-x + a * math.log(x) - _gammln(a))


def _gcf(a: float, x: float) -> float:
    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-14:
            break
    return math.exp(-x + a * math.log(x) - _gammln(a)) * h


def gammq(a: float, x: float) -> float:
    """正則化上側不完全ガンマ Q(a,x)。"""
    if x < 0 or a <= 0:
        raise ValueError("gammq: a>0 かつ x>=0")
    if x == 0:
        return 1.0
    if x < a + 1.0:
        return 1.0 - _gser(a, x)
    return _gcf(a, x)


def chi2_sf(x: float, df: int) -> float:
    """χ² 分布の上側確率(自由度 df)。"""
    if df <= 0:
        return 1.0
    if x <= 0:
        return 1.0
    return float(gammq(df / 2.0, x / 2.0))


def chi2_2sample(a: Mapping[str, float], b: Mapping[str, float]) -> dict[str, float]:
    """2 標本の同質性 χ² 検定(2×k 分割表)。度数 0 の列は落とす。"""
    keys, va, vb = align_counts(a, b)
    keep = (va + vb) > 0
    va, vb = va[keep], vb[keep]
    kept = [k for k, f in zip(keys, keep) if f]
    n = va.sum() + vb.sum()
    if va.sum() <= 0 or vb.sum() <= 0 or len(kept) < 2:
        return {"chi2": 0.0, "dof": 0, "p": 1.0, "k": len(kept)}
    col = va + vb
    ea = col * (va.sum() / n)
    eb = col * (vb.sum() / n)
    chi2 = float(np.sum((va - ea) ** 2 / ea) + np.sum((vb - eb) ** 2 / eb))
    dof = len(kept) - 1
    return {"chi2": chi2, "dof": dof, "p": chi2_sf(chi2, dof), "k": len(kept)}


# ================================================================ 個体別の統計(T5)


def per_agent_call_stats(
    calls: Sequence[tuple[int, int]], n_agents: int
) -> tuple[np.ndarray, np.ndarray]:
    """``(agent_id, tick)`` の並び → (個体別の呼数, 個体別の呼ばれた tick の平均)。

    呼ばれなかった個体の平均 tick は ``nan``(相関の対象から外れる)。
    """
    cnt = np.zeros(int(n_agents), dtype=np.float64)
    acc = np.zeros(int(n_agents), dtype=np.float64)
    for agent_id, tick in calls:
        i = int(agent_id)
        if 0 <= i < cnt.size:
            cnt[i] += 1.0
            acc[i] += float(tick)
    mean_tick = np.where(cnt > 0, acc / np.maximum(cnt, 1.0), np.nan)
    return cnt, mean_tick


def _t5_metrics(
    n_agents: int,
    selected_calls: Sequence[tuple[int, int]],
    wake_calls: Sequence[tuple[int, int]] | None,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """T5 の 3 量を個体別の配列にする(``mean_wake_tick`` は未呼び出しが ``nan``)。

    Returns:
        ``(指標 → 値の配列, 指標 → 重みの配列)``。重みは**その指標に情報を寄せた呼数**
        (``selected_count``/``wake_count`` は呼数そのもの、``mean_wake_tick`` は
        値を持つ体数=呼ばれた体の数)。層の加重平均に使う。
    """
    sel_cnt, sel_tick = per_agent_call_stats(selected_calls, n_agents)
    values = {"selected_count": sel_cnt, "mean_wake_tick": sel_tick}
    weights = {
        "selected_count": sel_cnt,
        "mean_wake_tick": np.isfinite(sel_tick).astype(np.float64),
    }
    if wake_calls is not None:
        wake_cnt = per_agent_call_stats(wake_calls, n_agents)[0]
        values["wake_count"] = wake_cnt
        weights["wake_count"] = wake_cnt
    return values, weights


def order_bias_report(
    n_agents: int,
    selected_calls: Sequence[tuple[int, int]],
    wake_calls: Sequence[tuple[int, int]] | None = None,
) -> dict[str, Any]:
    """T5 の 3 量 × (Pearson, Spearman) を 1 表にする(**個体が一様な母集団向け**)。

    3 量 = 「アービタで選ばれた回数」「呼ばれた tick の平均」「起床(候補)回数」。
    起床候補は ``budget`` を外したランの呼数で代用する(``wake_calls``)。

    Warning:
        **W16 母集団では使わない**。``agent_id`` が種別ごとの塊になっているため、
        生の相関は「処理順のバイアス」ではなく**種別構成の差**を拾う
        (合成個体は i.i.d. なのでこの関数でよい)。実データは
        ``stratified_order_bias_report``(種別層内)を使うこと。
    """
    ids = np.arange(int(n_agents), dtype=np.float64)
    rows = {
        name: {"pearson": pearson(ids, v), "spearman": spearman(ids, v)}
        for name, v in _t5_metrics(n_agents, selected_calls, wake_calls)[0].items()
    }
    worst = max((abs(v) for r in rows.values() for v in r.values()), default=0.0)
    return {
        "n_agents": int(n_agents),
        "n_selected_calls": len(selected_calls),
        "rows": rows,
        "max_abs_r": float(worst),
        "threshold": T5_MAX_ABS_R,
        "ok": bool(worst <= T5_MAX_ABS_R),
    }


def _center_within_strata(x: np.ndarray, strata: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """層ごとに平均を引く(``mask`` の外は ``nan``)。部分相関の残差化。"""
    out = np.full(x.shape, np.nan, dtype=np.float64)
    for g in np.unique(strata[mask]):
        m = mask & (strata == g)
        if m.any():
            out[m] = x[m] - x[m].mean()
    return out


def stratified_order_bias_report(
    n_agents: int,
    strata: Sequence[int],
    selected_calls: Sequence[tuple[int, int]],
    wake_calls: Sequence[tuple[int, int]] | None = None,
    labels: Mapping[int, str] | None = None,
) -> dict[str, Any]:
    """**種別層内**の T5(実データ用)。

    なぜ層内か(親の確認・2026-09-09)
        W16 の ``agent_id`` は種別ごとの塊で並ぶ(住民 → 通勤 → 通学 → 来街 → 訪日 → 乗務 →
        指令)。種別ごとに起床の出方が違う(来街者はほとんど呼ばれない・通勤者は計画境界で呼ばれる)
        ので、**ID と起床回数の生の相関は種別構成の差を拾う**。T5(v1 の C-8)が検査したいのは
        **処理順のバイアス**なので、種別を層として固定したうえで層内の ID 順位との相関を見る。
        二層抽出(5,000 体)も種別順を保つので同じ話。

    判定(**主判定**・親指示 09-09 の格付け直し)
        - **呼数**で重み付けした層内 |ρ| の平均 ≤ ``T5_MAX_ABS_R``
          (体数で重み付けると、呼がほぼ 0 の層=来街者が平均を薄めるため。重みは指標ごとに
          「その指標へ情報を寄せた呼数」= ``selected_count``/``wake_count`` は呼数、
          ``mean_wake_tick`` は値を持つ体数)
        - **最大の層(体数最多の種別)単独**の |ρ| ≤ ``T5_MAX_ABS_R``
        - **kind を統制した部分相関** |r| ≤ ``T5_MAX_ABS_R``(層内で中心化した残差どうしの
          Pearson。層をまたいで同じ向きに乗るバイアスを 1 本の数字で見る)
        いずれも 3 量すべてについて。**生の相関は報告値**(種別構成を含むので判定に使わない)。

    Args:
        n_agents: 個体数。
        strata: 個体ごとの層(``agents.population.Population.kind`` を想定)。
        selected_calls / wake_calls: ``(agent_id, tick)`` の並び。
        labels: 層コード → 表示名(``agents.state.AgentKind`` の名前など)。

    Returns:
        ``raw``(生の相関=報告値)・``partial``(部分相関=**判定に入る**)・``strata``(層ごと)・
        ``weighted_abs_rho``・``weights``(指標ごとの総重み)・``largest_stratum``・``ok``。
    """
    n = int(n_agents)
    ids = np.arange(n, dtype=np.float64)
    kinds = np.asarray(strata, dtype=np.int64).ravel()[:n]
    if kinds.size != n:
        raise ValueError(f"strata の長さが個体数と違う: {kinds.size} != {n}")
    metrics, metric_weights = _t5_metrics(n, selected_calls, wake_calls)
    codes, sizes = np.unique(kinds, return_counts=True)
    largest = int(codes[int(np.argmax(sizes))])

    per_stratum: dict[str, dict[str, Any]] = {}
    for code, size in zip(codes.tolist(), sizes.tolist()):
        m = kinds == code
        name = (labels or {}).get(int(code), str(int(code)))
        row: dict[str, Any] = {
            "code": int(code),
            "n": int(size),
            "n_calls": float(metrics["selected_count"][m].sum()),
        }
        for metric, values in metrics.items():
            row[metric] = spearman(ids[m], values[m])
            row[f"w_{metric}"] = float(metric_weights[metric][m].sum())
        per_stratum[name] = row

    weighted: dict[str, float] = {}
    weight_totals: dict[str, float] = {}
    partial: dict[str, float] = {}
    raw: dict[str, dict[str, float]] = {}
    for metric, values in metrics.items():
        total_w = float(sum(r[f"w_{metric}"] for r in per_stratum.values()))
        weight_totals[metric] = total_w
        weighted[metric] = (
            float(sum(abs(r[metric]) * r[f"w_{metric}"] for r in per_stratum.values()) / total_w)
            if total_w > 0
            else 0.0
        )
        raw[metric] = {"pearson": pearson(ids, values), "spearman": spearman(ids, values)}
        mask = np.isfinite(values)
        partial[metric] = pearson(
            _center_within_strata(ids, kinds, mask), _center_within_strata(values, kinds, mask)
        )

    largest_name = next(k for k, v in per_stratum.items() if v["code"] == largest)
    largest_row = per_stratum[largest_name]
    ok = _t5_gate(metrics, weighted, largest_row, partial)
    return {
        "n_agents": n,
        "n_reports": 1,
        "n_selected_calls": len(selected_calls),
        "metrics": sorted(metrics),
        "strata": per_stratum,
        "weighted_abs_rho": weighted,
        "weights": weight_totals,
        "largest_stratum": {"name": largest_name, **largest_row},
        "raw": raw,
        "partial": partial,
        "threshold": T5_MAX_ABS_R,
        "ok": bool(ok),
    }


def _t5_gate(
    metrics: Iterable[str],
    weighted: Mapping[str, float],
    largest_row: Mapping[str, Any],
    partial: Mapping[str, float],
) -> bool:
    """主判定 3 条件(加重平均・最大層・部分相関)を 1 か所で持つ。"""
    return all(
        weighted[m] <= T5_MAX_ABS_R
        and abs(float(largest_row[m])) <= T5_MAX_ABS_R
        and abs(float(partial[m])) <= T5_MAX_ABS_R
        for m in metrics
    )


def reversal_symmetry(
    forward: Mapping[str, Any], reverse: Mapping[str, Any]
) -> dict[str, Any]:
    """**副判定**: 母集団を反転すると生の ρ の符号が返る(=種別構成の効果)ことの釘付け。

    処理順のバイアスは反転しても**同じ向き**に乗る(若い id が得をする規則は、
    誰が若い id になっても同じ)ので、``ρ_順 + ρ_逆`` が 0 に近ければ「符号が返った」
    =観測された生の相関は個体の並び方(構成)に由来する、と言える。
    残差 ``|ρ_順 + ρ_逆| ≤ T5_MAX_ABS_R`` を条件にする(親指示 09-09)。
    """
    metrics = [m for m in forward["metrics"] if m in reverse["metrics"]]
    rows = {
        m: {
            "forward": float(forward["raw"][m]["spearman"]),
            "reverse": float(reverse["raw"][m]["spearman"]),
            "residual": abs(
                float(forward["raw"][m]["spearman"]) + float(reverse["raw"][m]["spearman"])
            ),
        }
        for m in metrics
    }
    worst = max((r["residual"] for r in rows.values()), default=0.0)
    return {
        "metrics": metrics,
        "rows": rows,
        "max_residual": float(worst),
        "threshold": T5_MAX_ABS_R,
        "ok": bool(worst <= T5_MAX_ABS_R),
    }


def _fisher_mean(values: Sequence[float]) -> float:
    """相関係数の平均は Fisher z で取る(小さい ρ では素の平均とほぼ同じ)。"""
    z = np.arctanh(np.clip(np.asarray(values, dtype=np.float64), -0.999999, 0.999999))
    return float(np.tanh(z.mean())) if z.size else 0.0


def average_stratified_reports(reports: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """同じ母集団・違う run seed の層内報告を **Fisher z 平均**でまとめ、判定をやり直す。

    なぜ要るか(検出力・expedient)
        層内 ρ の標準誤差は約 ``1/√(層内で呼ばれた体数)``。5,000 体 × 24 tick では
        最大層(通勤 2,346 体)でも呼ばれるのは約 515 体 = SE≈0.044 で、閾値 0.05 と同じ桁。
        実測で ``mean_wake_tick`` の層内 ρ は seed ごとに −0.059/+0.049/+0.059 と**符号が飛ぶ**
        (バイアスではなく標本誤差)。seed を k 本平均すると SE は ``1/√k`` に縮むので、
        **3 seed の平均**に対して閾値を当てる。層の構成は同じでなければならない
        (= 母集団を固定して run seed だけ変えること)。
    """
    if not reports:
        raise ValueError("reports が空")
    metrics = list(reports[0]["metrics"])
    names = list(reports[0]["strata"])
    for r in reports:
        if list(r["metrics"]) != metrics or list(r["strata"]) != names:
            raise ValueError("層または指標が揃っていない(同じ母集団で回すこと)")

    strata: dict[str, dict[str, Any]] = {}
    for name in names:
        base = reports[0]["strata"][name]
        row: dict[str, Any] = {
            "code": base["code"],
            "n": base["n"],
            "n_calls": float(np.mean([r["strata"][name]["n_calls"] for r in reports])),
        }
        for m in metrics:
            row[m] = _fisher_mean([r["strata"][name][m] for r in reports])
            row[f"w_{m}"] = float(np.mean([r["strata"][name][f"w_{m}"] for r in reports]))
        strata[name] = row

    weighted: dict[str, float] = {}
    weight_totals: dict[str, float] = {}
    for m in metrics:
        total_w = float(sum(v[f"w_{m}"] for v in strata.values()))
        weight_totals[m] = total_w
        weighted[m] = (
            float(sum(abs(v[m]) * v[f"w_{m}"] for v in strata.values()) / total_w)
            if total_w > 0
            else 0.0
        )
    largest_name = max(strata, key=lambda k: strata[k]["n"])
    largest_row = strata[largest_name]
    partial = {m: _fisher_mean([r["partial"][m] for r in reports]) for m in metrics}
    ok = _t5_gate(metrics, weighted, largest_row, partial)
    return {
        "n_agents": int(reports[0]["n_agents"]),
        "n_reports": len(reports),
        "n_selected_calls": int(np.mean([r["n_selected_calls"] for r in reports])),
        "metrics": metrics,
        "strata": strata,
        "weighted_abs_rho": weighted,
        "weights": weight_totals,
        "largest_stratum": {"name": largest_name, **largest_row},
        "raw": {
            m: {
                k: _fisher_mean([r["raw"][m][k] for r in reports])
                for k in ("pearson", "spearman")
            }
            for m in metrics
        },
        "partial": partial,
        "threshold": T5_MAX_ABS_R,
        "ok": bool(ok),
    }


# ================================================================ 場面(指標B の事前登録)

#: 失敗理由の語(``agents.state.RESULT_TEXT`` の逐語)→ 種 id(= ``ResultCode`` 名の小文字)。
#: **表は ``RESULT_TEXT`` と 1 対 1**(``tests/c6/test_c6lib_scenes.py`` が突き合わせる)。
FAILURE_WORD_BY_KIND: Mapping[str, str] = {
    "unreachable": "到達不能",
    "interrupted": "途中打ち切り",
    "train_full": "満員",
    "fare_short": "運賃不足",
    "no_train": "列車なし",
    "no_stop": "その駅には止まらない",
    "money_short": "所持金不足",
    "out_of_stock": "在庫切れ",
    "closed": "営業時間外",
    "partner_busy": "相手が会話中",
    "refused": "断られた",
    "partner_gone": "去った",
    "no_bed": "寝る場所がない",
    "no_permission": "権限なし",
    "lost_arbitration": "先に取られた",
    "undefined_action": "未定義の行動",
    "bad_target": "対象を特定できない",
    "insufficient_ability": "能力不足",
}
FAILURE_KIND_BY_WORD: Mapping[str, str] = {v: k for k, v in FAILURE_WORD_BY_KIND.items()}

#: 指標B の**事前登録された 5 種**(知覚契約書 §8「制約種ごと n≥50(5種=250場面)」)。
#: どの 5 種かは契約書に無い = 本ハーネスの選択(**expedient・親判断待ち**)。
#: 在庫が足りないときは ``--kinds`` で差し替えられる(在庫表は全 18 種を出す)。
CONSTRAINT_KINDS: tuple[str, ...] = (
    "closed",  # 営業時間外
    "money_short",  # 所持金不足
    "train_full",  # 満員
    "unreachable",  # 移動不能(到達不能)
    "refused",  # 会話拒否(断られた)
)

#: 制約種 → 「そのまま繰り返したら違反」になる行動(``violation_flags`` の禁じ手表)。
#: 品質プローブv0 は場面ごとに ``violating_actions`` を持たせる形だが、実データ場面には
#: 無いので**種ごとに 1 語**へ固定した(expedient)。対象の取り違え(bad_target)など、
#: 同一行動の再試行が必ずしも違反にならない種は**表に載せない**(= 違反判定しない)。
BANNED_ACTION_BY_KIND: Mapping[str, str] = {
    "closed": "購入",
    "money_short": "購入",
    "out_of_stock": "購入",
    "train_full": "乗車",
    "fare_short": "乗車",
    "no_train": "乗車",
    "no_stop": "降車",
    "unreachable": "移動",
    "refused": "会話",
    "partner_busy": "会話",
    "partner_gone": "会話",
    "no_bed": "就寝",
}

#: B6 の失敗行(``perception.templates.TEMPLATES["B6.result_fail"]`` の形)。
_B6_FAIL_RE = re.compile(r"\[B6 結果\]\s*直前の(?P<action>[^はを]+?)は(?P<why>.+?)で失敗しました")
#: B5 内受容(閾値割れ分のみ描画される。空文言は「体調に変わりはありません」)。
_B5_INTERO_RE = re.compile(r"\[B5 内受容\]\s*(?P<body>.*)")
_B5_INTERO_EMPTY = "体調に変わりはありません"
#: B6 起床理由の行。
_B6_WAKE_RE = re.compile(r"\[B6 起床\]\s*(?P<body>.*)")

#: 「計画境界」起床の理由文(``perception.templates.WAKE_REASON_TEXT`` の 1・2 行目)。
PLAN_BOUNDARY_REASONS: tuple[str, ...] = (
    "眠りにつく時刻になったため",
    "仕事の区切りがついたため",
)


@dataclass(frozen=True)
class Scene:
    """1 呼 = 1 場面(指標B の抽出単位)。

    Attributes:
        constraint: 制約種 id(``CONSTRAINT_KINDS`` の鍵)。制約が無い場面は ``""``。
        determined: 「答えが決まる場面」か(駆動因が 1 つ以上)。
        drivers: 効いた駆動因(``intero`` / ``plan_boundary`` / ``last_failure``)。
        partial: プロンプトが**共有ブロックだけ**か(録画テープ由来= B5/B6 が無い)。
    """

    agent_id: int
    tick: int
    wake_class: int
    prompt: str
    response: str = ""
    constraint: str = ""
    determined: bool = False
    drivers: tuple[str, ...] = ()
    partial: bool = False
    prompt_hash: str = ""
    call_id: str = ""

    @property
    def key(self) -> str:
        """抽出順を決める決定論の鍵(sha256・16 桁)。"""
        raw = f"{self.agent_id}\x1f{self.tick}\x1f{self.wake_class}\x1f{self.prompt_hash}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_scene(prompt: str, wake_class: int = -1) -> tuple[str, bool, tuple[str, ...]]:
    """プロンプト本文 → (制約種 id, 答えが決まるか, 駆動因)。**純関数**。

    駆動因(expedient・§8 の mid 層の実データ版)
      - ``last_failure``: B6 に「…で失敗しました」がある(制約が提示されている)。
      - ``intero``: B5 内受容が空文言でない(閾値割れが描かれている)。
      - ``plan_boundary``: B6 起床理由が計画境界(就寝・就業の区切り)。
    """
    constraint = ""
    drivers: list[str] = []

    m = _B6_FAIL_RE.search(prompt)
    if m is not None:
        drivers.append("last_failure")
        constraint = FAILURE_KIND_BY_WORD.get(m.group("why").strip(), "")

    mi = _B5_INTERO_RE.search(prompt)
    if mi is not None and _B5_INTERO_EMPTY not in mi.group("body"):
        drivers.append("intero")

    mw = _B6_WAKE_RE.search(prompt)
    if mw is not None and any(r in mw.group("body") for r in PLAN_BOUNDARY_REASONS):
        drivers.append("plan_boundary")

    return constraint, bool(drivers), tuple(drivers)


def scene_from_record(rec: Mapping[str, Any]) -> Scene:
    """``RecordingLLM`` の 1 行(``scenes.jsonl``)→ ``Scene``。"""
    prompt = str(rec.get("prompt", ""))
    wake_class = int(rec.get("wake_class", -1))
    constraint, determined, drivers = classify_scene(prompt, wake_class)
    return Scene(
        agent_id=int(rec.get("agent_id", -1)),
        tick=int(rec.get("tick", -1)),
        wake_class=wake_class,
        prompt=prompt,
        response=str(rec.get("response", "")),
        constraint=constraint,
        determined=determined,
        drivers=drivers,
        partial=bool(rec.get("partial", False)),
        prompt_hash=str(rec.get("prompt_hash", "")),
        call_id=str(rec.get("call_id", "")),
    )


def scenes_from_jsonl(path: str | Path) -> list[Scene]:
    """``scenes.jsonl``(``RecordingLLM.dump``)→ 場面。"""
    out: list[Scene] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(scene_from_record(json.loads(line)))
    return out


def scenes_from_tape(tape: Any) -> list[Scene]:
    """録画テープ(``engine.tape.Tape`` かそのパス)→ 場面。

    **注意(C6-b で判明)**: テープの共有ブロックは B0-B4b だけで、**B5/B6(個体固有)は
    intern されない**(``engine.llm_bridge.SHARED_BLOCK_IDS``)。したがって実ランのテープから
    復元できるプロンプトは部分(``partial=True``)であり、制約種の抽出も再呼もできない。
    指標B は ``RecordingLLM`` が出す ``scenes.jsonl``(全文)を使うこと。
    本関数は **モックテープでの純関数テスト**と、テープしか無いときの診断用に置く。
    """
    from shibuya.engine.tape import Tape  # 遅延 import(pyarrow を要する)

    t = tape if isinstance(tape, Tape) else Tape(tape)
    out: list[Scene] = []
    for row in t.rows():
        text = "\n".join(t.block_text(b) for b in row.block_ids)
        constraint, determined, drivers = classify_scene(text, int(row.wake_class))
        partial = "[B6" not in text  # B6 が無い = 個体ブロックが落ちている
        out.append(
            Scene(
                agent_id=int(row.agent_id),
                tick=int(row.tick),
                wake_class=int(row.wake_class),
                prompt=text,
                response=str(row.response),
                constraint=constraint,
                determined=determined,
                drivers=drivers,
                partial=partial,
                prompt_hash=str(row.prompt_hash),
                call_id=str(row.call_id),
            )
        )
    return out


def scene_inventory(
    scenes: Sequence[Scene],
    kinds: Sequence[str] = CONSTRAINT_KINDS,
    per_kind: int = METRIC_B_PER_KIND,
    n_determined: int = METRIC_B_DETERMINED,
) -> dict[str, Any]:
    """場面の在庫表(全 18 種の件数・事前登録 5 種の充足・決まる場面の件数)。"""
    counts = Counter(s.constraint for s in scenes if s.constraint)
    determined = [s for s in scenes if s.determined]
    shortfall = {
        k: per_kind - int(counts.get(k, 0))
        for k in kinds
        if int(counts.get(k, 0)) < per_kind
    }
    return {
        "n_scenes": len(scenes),
        "n_partial": sum(1 for s in scenes if s.partial),
        "kinds": list(kinds),
        "per_kind": {k: int(counts.get(k, 0)) for k in kinds},
        "per_failure_kind_all": {k: int(v) for k, v in sorted(counts.items())},
        "n_determined": len(determined),
        "required_per_kind": int(per_kind),
        "required_determined": int(n_determined),
        "shortfall_per_kind": shortfall,
        "determined_shortfall": max(0, int(n_determined) - len(determined)),
        "ok": not shortfall and len(determined) >= int(n_determined),
    }


def select_metric_b_scenes(
    scenes: Sequence[Scene],
    per_kind: int = METRIC_B_PER_KIND,
    n_determined: int = METRIC_B_DETERMINED,
    kinds: Sequence[str] = CONSTRAINT_KINDS,
) -> dict[str, list[Scene]]:
    """事前登録の抽出(制約種ごと n・「答えが決まる場面」m)。**決定論**(``Scene.key`` 昇順)。

    「答えが決まる場面」は制約場面と重ならないように、制約枠に採った場面を除いてから採る
    (同じ場面を 2 回呼ばない=呼数の二重計上を避ける)。
    """
    picked: dict[str, list[Scene]] = {}
    used: set[str] = set()
    for kind in sorted(kinds):
        pool = sorted((s for s in scenes if s.constraint == kind), key=lambda s: s.key)
        chosen = pool[: int(per_kind)]
        picked[kind] = chosen
        used.update(s.key for s in chosen)
    pool = sorted(
        (s for s in scenes if s.determined and s.key not in used), key=lambda s: s.key
    )
    picked["determined"] = pool[: int(n_determined)]
    return picked


# ================================================================ 応答の採点


def score_texts(texts: Sequence[str]) -> dict[str, Any]:
    """応答本文の並び → 書式エラー率(実効/厳密)・別名率・行動分布・役割語率・未定義率。

    ``shibuya.llm.parser.parse_two_line`` と ``shibuya.llm.undefined.map_synonym`` を使う
    (採点の定義を 2 つ持たない)。

    書式エラー率は**二重**に出す(サブ Q のラベル別名許容が入ったため・親判断 **D-28**)
      - ``format_error_rate``(**実効**・受入表の主): C6 で足した別名ラベルを許した判定
        ``ParseResult.format_ok``。再生成の要否と同じ基準。
      - ``format_error_rate_strict``(**厳密**・併記): C6 以前の別名表だけで見た
        ``ParseResult.strict_format_ok``。B11(n=59・厳密2行)と地続きの数字。
      - ``alias_used_rate``: 正準ラベル以外の表層を 1 つでも使った割合(内訳は ``alias_surfaces``)。

    ``undefined_rate`` は「行動語彙に一致せず、**段0 辞書(``map_synonym``)でも救えなかった**」
    割合。辞書で救えた分は ``dictionary_mapped_rate`` に分け、行動分布では**写像先の契約語**
    として数える(エンジンの ``UndefinedActionRegistry.observe`` と同じ扱い)。
    """
    from shibuya.llm.contract import ROLE_ACTION_WORDS, is_role_action
    from shibuya.llm.parser import parse_two_line
    from shibuya.llm.undefined import map_synonym

    n = len(texts)
    actions: Counter[str] = Counter()
    alias_surfaces: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    n_format_err = n_strict_err = n_alias = 0
    n_role = n_undefined = n_mapped = n_strict_two_line = 0
    for t in texts:
        p = parse_two_line(t)
        if not p.format_ok:
            n_format_err += 1
        if not getattr(p, "strict_format_ok", p.format_ok):
            n_strict_err += 1
        if getattr(p, "alias_used", False):
            n_alias += 1
            alias_surfaces.update(getattr(p, "alias_surfaces", ()))
        if p.strict_two_line:
            n_strict_two_line += 1
        word = p.action
        if word is None:
            mapped, _hint = map_synonym(p.raw_action)
            if mapped is None:
                n_undefined += 1
                actions["(未定義)"] += 1
                continue
            n_mapped += 1
            word = mapped
        actions[word] += 1
        if is_role_action(word):
            n_role += 1
            role_counts[word] += 1
    lo, hi = wilson_ci(n_format_err, n) if n else (0.0, 1.0)
    slo, shi = wilson_ci(n_strict_err, n) if n else (0.0, 1.0)
    rate = (n_format_err / n) if n else 0.0
    strict_rate = (n_strict_err / n) if n else 0.0
    return {
        "n": n,
        "format_error_rate": rate,
        "format_error_ci95": [lo, hi],
        "format_error_rate_strict": strict_rate,
        "format_error_ci95_strict": [slo, shi],
        "format_error_gate": FORMAT_ERROR_MAX,
        "format_error_n_min": FORMAT_ERROR_MIN_N,
        "format_error_ok": bool(n >= FORMAT_ERROR_MIN_N and rate <= FORMAT_ERROR_MAX),
        "format_error_ok_strict": bool(
            n >= FORMAT_ERROR_MIN_N and strict_rate <= FORMAT_ERROR_MAX
        ),
        "alias_used_rate": (n_alias / n) if n else 0.0,
        "alias_surfaces": dict(alias_surfaces),
        "strict_two_line_rate": (n_strict_two_line / n) if n else 0.0,
        "role_action_rate": (n_role / n) if n else 0.0,
        "role_action_counts": dict(role_counts),
        "role_vocab": list(ROLE_ACTION_WORDS),
        "undefined_rate": (n_undefined / n) if n else 0.0,
        "dictionary_mapped_rate": (n_mapped / n) if n else 0.0,
        "dictionary_mapped": n_mapped,
        "action_counts": dict(actions),
    }


def violation_flags(scenes: Sequence[Scene], texts: Sequence[str]) -> list[int]:
    """制約違反フラグ(1=違反)。**制約種ごとに禁止行動を 1 つ持つ最小規則**。

    品質プローブv0 の ``check_constraints`` は場面ごとに ``violating_actions`` を持たせる形。
    実データ場面ではそれが無いので、``BANNED_ACTION_BY_KIND`` を固定表にした(expedient)。
    「直前の結果」が失敗として提示されている以上、**同じ行動をそのまま繰り返すのは制約違反**
    という判定(行動契約書 §6「いま可能」3 語が提示されている場面)。表に無い種は違反にしない。
    """
    from shibuya.llm.parser import parse_two_line

    out: list[int] = []
    for s, t in zip(scenes, texts):
        p = parse_two_line(t)
        bad = BANNED_ACTION_BY_KIND.get(s.constraint)
        out.append(1 if (bad is not None and p.action == bad) else 0)
    return out


# ================================================================ 記録用クライアント


class RecordingLLM:
    """任意の ``LLMClient`` を包んで **全プロンプトと応答**を記録する。

    録画テープには共有ブロック(B0-B4b)しか入らないため、指標B の「場面」を作るには
    プロンプト全文が要る。``run_day(llm=RecordingLLM(MockLLM(seed)))`` で採る。

    Note:
        ``fleet=`` を渡したランは LLM 経路が ``FleetBridge`` へ移り、本クラスは通らない
        (= 実 LLM 走行中の全文採取の口は無い。C6-b の親判断待ちへ記載)。
    """

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.records: list[dict[str, Any]] = []

    def complete(self, request: Any) -> Any:
        res = self.inner.complete(request)
        self.records.append(
            {
                "agent_id": int(request.agent_id),
                "tick": int(request.tick),
                "wake_class": int(request.wake_class),
                "prompt": str(request.prompt),
                "prompt_hash": str(getattr(request, "prompt_hash", "")),
                "call_id": str(getattr(request, "call_id", "")),
                "response": str(getattr(res, "text", "")),
                "partial": False,
            }
        )
        return res

    # ---- 診断 ----
    @property
    def calls(self) -> list[tuple[int, int]]:
        """``(agent_id, tick)`` の並び(T5 の素材)。"""
        return [(r["agent_id"], r["tick"]) for r in self.records]

    def dump(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            for r in self.records:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        return p


def reverse_population(pop: Any) -> Any:
    """個体の並びを**逆順**にした母集団(T5 の ID 写像反転の対照)。

    ``agent_id`` は行番号なので、行を逆順にすると「ID の意味」が反転する
    (W16 は種別ごとに固まって並ぶため、これを反転しても結果の分布が変わらないことが
    順序バイアスなしの証拠になる)。
    """
    import dataclasses

    n = int(pop.n)
    changed: dict[str, Any] = {}
    for f in dataclasses.fields(pop):
        v = getattr(pop, f.name)
        if isinstance(v, np.ndarray) and v.shape[:1] == (n,):
            changed[f.name] = v[::-1].copy()
    return dataclasses.replace(pop, **changed)


# ================================================================ ラン(シム)


def run_smoke(
    *,
    n_agents: int,
    seed: int,
    ticks: int,
    world_dir: str | Path | None,
    tape_path: str | Path | None = None,
    fleet: Any | None = None,
    llm: Any | None = None,
    checkpoint_every: int | None = None,
    extra: Mapping[str, Any] | None = None,
) -> tuple[Any, str]:
    """``shibuya.cli.run`` を叩く(台帳つきの標準入口)。

    別サブ O が結線中の ``run_day(..., fleet=...)`` を前提にするが、引数名が違っても
    落ちないように **1 段だけ後退**する(fleet を外して mock で回し、その旨を返す)。

    Returns:
        ``(RunResult, 使った経路の説明)``。
    """
    from shibuya import cli

    kwargs: dict[str, Any] = {
        "n_agents": int(n_agents),
        "seed": int(seed),
        "world_dir": str(world_dir) if world_dir is not None else None,
        "ticks": int(ticks),
        "checkpoint_every": int(checkpoint_every if checkpoint_every else max(1, ticks)),
    }
    if tape_path is not None:
        kwargs["tape_path"] = str(tape_path)
    if llm is not None:
        kwargs["llm"] = llm
    if extra:
        kwargs.update(dict(extra))
    if fleet is not None:
        try:
            return cli.run(fleet=fleet, **kwargs), "cli.run(fleet=…)"
        except TypeError as exc:
            if "fleet" not in str(exc):
                raise
            return cli.run(**kwargs), f"fleet 引数が通らない({exc})→ mock 経路へ後退"
    return cli.run(**kwargs), "cli.run(mock)"


def build_fleet_client(
    endpoints: Sequence[str],
    *,
    model: str = "",
    mode: str = "smoke",
    run_id: str = "",
    run_seed: int = 0,
    temperature: float = 0.0,
    max_tokens: int = 64,
    stream: bool = True,
) -> Any:
    """``llm.fleet.FleetClient`` を組む(実サーバーに繋ぐのは呼び出し側の責任)。"""
    from shibuya.llm.fleet import FleetClient, FleetConfig
    from shibuya.manifest.schema import Mode

    cfg = FleetConfig(
        endpoints=tuple(endpoints),
        model=model,
        mode=Mode(mode),
        run_id=run_id,
        run_seed=int(run_seed),
        temperature=float(temperature),
        t1_max_tokens=int(max_tokens),
        stream=bool(stream),
    )
    return FleetClient(cfg)


def in_flight_report(counters: Mapping[str, float], n_replicas: int, cap_per_gpu: int) -> dict[str, Any]:
    """``fleet_peak_in_flight_r*`` が L6(64 in-flight/GPU)を超えていないか。"""
    peaks = {
        k: float(v) for k, v in counters.items() if k.startswith("fleet_peak_in_flight_r")
    }
    worst = max(peaks.values(), default=0.0)
    total = sum(peaks.values())
    return {
        "peaks": peaks,
        "cap_per_gpu": int(cap_per_gpu),
        "cap_total": int(cap_per_gpu) * int(n_replicas),
        "max_peak": worst,
        "sum_peak": total,
        "ok": bool(worst <= cap_per_gpu and total <= cap_per_gpu * max(1, n_replicas)),
    }


# ================================================================ HTTP(実 LLM 呼び)


def discover_model(endpoint: str, timeout: float = 30.0) -> str:
    """``/v1/models`` の先頭 id(取れなければ ``""``)。"""
    import httpx

    try:
        r = httpx.get(endpoint.rstrip("/") + "/v1/models", timeout=timeout)
        r.raise_for_status()
        return str(r.json()["data"][0]["id"])
    except Exception:
        return ""


def chat_once(
    endpoint: str,
    model: str,
    system_block: str,
    user_block: str,
    *,
    max_tokens: int = 64,
    temperature: float = 0.0,
    seed: int | None = None,
    timeout: float = 300.0,
    no_thinking: bool = True,
    retries: int = 3,
) -> dict[str, Any]:
    """``/v1/chat/completions`` を 1 回叩く(品質プローブv0 ``run_probe.call_chat`` と同じ形)。

    Returns:
        ``{"text","prompt_tokens","completion_tokens","latency_ms","error"}``。
    """
    import httpx

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_block},
            {"role": "user", "content": user_block},
        ],
        "temperature": float(temperature),
        "top_p": 1.0,
        "max_tokens": int(max_tokens),
        "n": 1,
        "stream": False,
    }
    if seed is not None:
        payload["seed"] = int(seed)
    if no_thinking:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    last = ""
    import time as _time

    for attempt in range(int(retries)):
        t0 = _time.time()
        try:
            r = httpx.post(
                endpoint.rstrip("/") + "/v1/chat/completions", json=payload, timeout=timeout
            )
            if r.status_code == 400 and "chat_template_kwargs" in r.text and no_thinking:
                payload.pop("chat_template_kwargs", None)
                no_thinking = False
                continue
            r.raise_for_status()
            d = r.json()
            usage = d.get("usage") or {}
            return {
                "text": (d["choices"][0]["message"].get("content") or ""),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "latency_ms": (_time.time() - t0) * 1000.0,
                "error": "",
            }
        except Exception as exc:  # noqa: BLE001 - 実サーバー相手なので握って再試行
            last = f"{type(exc).__name__}: {exc}"
            _time.sleep(1.5 * (attempt + 1))
    return {
        "text": "",
        "prompt_tokens": None,
        "completion_tokens": None,
        "latency_ms": 0.0,
        "error": last or "unknown_error",
    }


def split_prompt(prompt: str) -> tuple[str, str]:
    """レンダラの本文 → (system 部, user 部)。

    ``llm.fleet.split_system_user`` と同じ切り方(B0 の末尾=出力規約の最後の行)を
    使えないときのための素朴版: ``[B1 `` の直前で割る。
    """
    idx = prompt.find("[B1 ")
    if idx <= 0:
        return "", prompt
    return prompt[:idx].rstrip("\n"), prompt[idx:]


# ================================================================ 出力


def markdown_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    """Markdown の表(数値の整形は呼び出し側)。"""
    out = ["| " + " | ".join(str(h) for h in headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join("" if c is None else str(c) for c in r) + " |")
    return "\n".join(out)


def write_outputs(out_dir: str | Path, stem: str, payload: Mapping[str, Any], md: str) -> dict[str, str]:
    """``<out>/<stem>.json`` と ``<out>/<stem>.md`` を書く。"""
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    jp = d / f"{stem}.json"
    mp = d / f"{stem}.md"
    jp.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    mp.write_text(md.rstrip("\n") + "\n", encoding="utf-8")
    return {"json": str(jp), "md": str(mp)}


def common_parser(description: str) -> argparse.ArgumentParser:
    """全ツール共通の引数(``--endpoints --world --agents --ticks --out``)。"""
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument(
        "--endpoints",
        default="",
        help="カンマ区切りの vLLM レプリカ(例 http://127.0.0.1:8000,http://127.0.0.1:8001)",
    )
    ap.add_argument("--world", default="data/world/v2", help="世界資産ディレクトリ")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--ticks", type=int, default=24, help="24step スモークが既定")
    ap.add_argument("--out", default="docs/bench/c6", help="結果 JSON/Markdown の出力先")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--model", default="", help="served-model-name(空なら /v1/models の先頭)")
    return ap


def endpoints_of(args: argparse.Namespace) -> list[str]:
    return [e.strip() for e in str(args.endpoints).split(",") if e.strip()]


def world_dir_of(args: argparse.Namespace) -> Path | None:
    p = Path(args.world)
    return p if p.exists() else None
