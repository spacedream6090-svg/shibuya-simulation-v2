# -*- coding: utf-8 -*-
"""prereg_v13 — 事前登録 **v1.3**(3 seed のアンサンブル判定)の純関数。

位置づけ
    ``docs/bench/c7/prereg_arms_v1.md`` §7(v1.3・第210・ユーザー決定 D-79 (a) / D-83 ①)を
    機械で実行できる形にしたもの。``holdout_compare.py`` が ``--prereg-version v1.3`` の
    ときだけ呼ぶ。**合格線 H1〜H5 の値は v1.2 から 1 つも変えない**(§7「変えないもの」)。
    v1.2(1 ラン)の経路はこのモジュールを一切通らない=既定の挙動は不変。

v1.2 から変わるのは「**線の当て方**」だけ

1. **家族 95%**(Currie & Cheng 2016 §6.2「C=5 で個別 90% は家族 50%」)
   5 指標を家族として扱い、Bonferroni で指標あたり α=0.01(両側)。
   平均の区間半幅 = ``t(0.995, n−1)·SD/√n``(SD は ddof=1)。
   ``t`` の表は ``seed_ensemble.t_quantile_995``(scipy が無い環境の表)を**共有**する。
2. **同値検定の形**(Sargent, Goldsman & Yaacoub 2016 の区間仮説)
   線が上限 U だけなら H0: D ≤ U。区間 [平均−半幅, 平均+半幅] が
   **全部内側→ pass** / **全部外側→ fail** / **またぐ→ undecided**(検出力不足)。
   下限だけ・両側・整数比較も同じ規則。α(製作者危険)=0.01/指標を欄に出す。
   β(利用者危険)は**計算しない**——代わりに「この SD で undecided を解くのに要る
   seed 数」 N=(t·SD/|平均−線|)² を n=3..10 で探す(t は n で変わるので逐次探索)。
3. **深夜(0〜5 時)の格下げ**(第209 の親再計算: 3 seed の家族 95% は ±18.6%)
   H3(平日休日比の代替=深夜残存率)は**判定から外し記述欄へ**。``n_measured`` に数えない。
   H1 は**判定用を 6〜23 時で再計算**し、24 h 版を記述として併記する。H2/H4/H5 は変えない。
4. **GET 包絡は記述のみ**(Myllymäki & Mrkvička): s=3 seed の大域包絡は p ≥ 1/s=1/3
   =**検定ではない**。図と時刻数だけ出し、合否に使わない。
5. **fair CRPS**(Ferro 2014・ECMWF): CRPS = E|X−y| − ½E|X−X'| の**第 2 項に M/(M−1)**
   を掛ける(M=3 なら ×1.5)。raw と fair の比を併記する。
6. **停止則**: 開封後に seed を足しても主張を変えない(追加 seed は記述の更新のみ)。

「線と比較する統計量」の選び方(``METRIC_STATS``)
    ``c7lib.five_metrics`` の各指標の ``pass`` 判定式**そのもの**から取った。
    判定式は全て「統計量 ≤ 上限」「統計量 ≥ 下限」の AND なので、その統計量ごとに
    区間を作り、指標の判定は 3 値の AND(1 つでも fail → fail・残りに undecided が
    あれば undecided)にする。

    | 指標 | 統計量(``five_metrics`` の欄) | 線 | 向き | 判定式(``c7lib``) |
    |---|---|---|---|---|
    | H1 | ``jsd_mean`` | ``jsd_mean_max`` (0.0122) | 上限 | ``_pass(mean(per_area_jsd), H1.jsd_area_hour_mean_max)`` |
    | H1 | ``pearson_r`` | ``pearson_min`` (0.80) | 下限 | ``_pass(r, H1.pearson_min, upper=False)`` |
    | H2 | ``n_within``(整数) | ``n_within_min`` (5) | 下限 | ``(abs(Δh) ≤ abs_hour_diff_max=1).sum() >= n_within_min`` |
    | H2 | ``kendall_tau`` | ``tau_min`` (0.60) | 下限 | ``_pass(tau2, H2.tau_min, upper=False)`` |
    | H3 | ``abs_diff_max`` | ``abs_diff_max`` (0.05) | 上限 | ``_pass(max abs(Δ), H3.abs_diff_max)``(**v1.3 は記述**) |
    | H3 | ``kendall_tau`` | ``tau_min`` (0.60) | 下限 | ``_pass(tau3, H3.tau_min, upper=False)``(**v1.3 は記述**) |
    | H4 | ``jsd`` | ``jsd_max`` (0.0122) | 上限 | ``_pass(d4, H4.jsd_max)`` |
    | H4 | ``abs_share_diff_max`` | ``abs_share_diff_max`` (0.05) | 上限 | ``_pass(m4, H4.abs_share_diff_max)`` |
    | H5 | ``jsd_mean`` | ``jsd_mean_max`` (0.02) | 上限 | ``_pass(mean(per), H5.jsd_mean_max)`` |
    | H5 | ``abs_share_diff_max`` | ``abs_share_diff_max`` (0.10) | 上限 | ``_pass(m5, H5.abs_share_diff_max)`` |

    ``n_within``(H2)は**整数**なので、平均±半幅の区間ではなく **seed ごとの値の
    最小/最大**を区間の代用にする(``interval_kind`` 欄に明示)。線は ``five_metrics``
    が返した ``res[H*]["limit"]`` から読む(``prereg`` の鍵名と ``limit`` の鍵名が H1 だけ
    違う=``jsd_area_hour_mean_max`` vs ``jsd_mean_max`` ので、**実際に判定に使われた側**を
    読む=写し事故を避ける)。全 seed で線が一致しなければ例外で止まる。

expedient(v1.3 §7 の表に書かれておらず、実装で決めたもの)
- ``kendall_tau`` が 1 本でも未定義(``tau_undefined``)なら、その統計量は ``fail``
  (1 ラン版 ``_pass(nan, ...)`` が False を返すのと同じ扱い)。区間は作らない。
- 判定対象の指標が 1 本でも ``measured=False`` なら、その指標は ``n_measured`` に数えない
  (``five_metrics`` と同じ規則)。
- H1 の昼窓は **6〜23 時**(v1.3 §7「深夜(0〜5 時)は記述に格下げ」の補集合)。
  ``five_metrics`` に時間帯を絞る口が無いので、入力表を切って渡す(``h1_day_window``)。
- Bonferroni の分母は **5 のまま**(H3 を記述に落としても事前登録の家族は 5 指標)。
- 指標の判定 = 統計量の 3 値 AND。``fail`` が優先(1 ラン版の AND と同じ向き)。
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

_HERE = Path(os.path.abspath(__file__)).parent
_TOOLS_C8 = _HERE.parent / "c8"
for _p in (str(_HERE), str(_TOOLS_C8)):
    if _p not in sys.path:  # pragma: no cover - 実行時の経路
        sys.path.insert(0, _p)

import c7lib  # noqa: E402
import ensemble as c8_ensemble  # noqa: E402  (tools/c8 の CRPS を流用=新実装を作らない)
from seed_ensemble import FAMILY_ALPHA_PER_METRIC, t_quantile_995  # noqa: E402

SCHEMA = "shibuya.tools.c7/prereg_v13/1"
PREREG_VERSION = "v1.3"

#: 家族 = 形状 5 指標(Bonferroni の分母)。H3 を記述に落としても**分母は 5 のまま**
#: (事前登録で 5 指標を家族と宣言したので、事後に減らすと α が甘くなる)。
FAMILY_SIZE = 5

#: v1.3 で**判定に使う**指標(H3 は深夜なので記述へ格下げ・§7)。
JUDGED_METRICS: tuple[str, ...] = ("H1", "H2", "H4", "H5")
#: v1.3 で**記述だけ**にする指標。
DESCRIPTIVE_METRICS: tuple[str, ...] = ("H3",)
ALL_METRICS: tuple[str, ...] = ("H1", "H2", "H3", "H4", "H5")

#: H1 の判定窓(6〜23 時)。0〜5 時は記述へ。
DAY_HOURS: tuple[int, ...] = tuple(range(6, 24))
#: 記述に格下げした時間帯。
NIGHT_HOURS_DEMOTED: tuple[int, ...] = tuple(range(0, 6))

#: 「要る seed 数」を探す範囲(``t_quantile_995`` の表が df=1..10 まで)。
N_NEEDED_MIN = 3
N_NEEDED_MAX = 10

STOPPING_RULE = "開封後に seed を足しても主張を変えない(追加 seed は記述の更新のみ)"

#: 統計量の定義。``bound`` は ``upper``(線は上限)/``lower``(線は下限)/``both``。
METRIC_STATS: dict[str, tuple[dict[str, Any], ...]] = {
    "H1": (
        {"key": "jsd_mean", "limit_key": "jsd_mean_max", "bound": "upper", "kind": "float",
         "why": "five_metrics H1: _pass(mean(per_area_jsd), H1.jsd_area_hour_mean_max)"},
        {"key": "pearson_r", "limit_key": "pearson_min", "bound": "lower", "kind": "float",
         "why": "five_metrics H1: _pass(r, H1.pearson_min, upper=False)"},
    ),
    "H2": (
        {"key": "n_within", "limit_key": "n_within_min", "bound": "lower", "kind": "int",
         "why": "five_metrics H2: (abs(Δh) <= abs_hour_diff_max).sum() >= n_within_min"},
        {"key": "kendall_tau", "limit_key": "tau_min", "bound": "lower", "kind": "float",
         "why": "five_metrics H2: _pass(tau2, H2.tau_min, upper=False)"},
    ),
    "H3": (
        {"key": "abs_diff_max", "limit_key": "abs_diff_max", "bound": "upper", "kind": "float",
         "why": "five_metrics H3: _pass(max abs(Δ深夜残存率), H3.abs_diff_max)"},
        {"key": "kendall_tau", "limit_key": "tau_min", "bound": "lower", "kind": "float",
         "why": "five_metrics H3: _pass(tau3, H3.tau_min, upper=False)"},
    ),
    "H4": (
        {"key": "jsd", "limit_key": "jsd_max", "bound": "upper", "kind": "float",
         "why": "five_metrics H4: _pass(d4, H4.jsd_max)"},
        {"key": "abs_share_diff_max", "limit_key": "abs_share_diff_max", "bound": "upper",
         "kind": "float", "why": "five_metrics H4: _pass(m4, H4.abs_share_diff_max)"},
    ),
    "H5": (
        {"key": "jsd_mean", "limit_key": "jsd_mean_max", "bound": "upper", "kind": "float",
         "why": "five_metrics H5: _pass(mean(per_area_jsd), H5.jsd_mean_max)"},
        {"key": "abs_share_diff_max", "limit_key": "abs_share_diff_max", "bound": "upper",
         "kind": "float", "why": "five_metrics H5: _pass(m5, H5.abs_share_diff_max)"},
    ),
}


# ---------------------------------------------------------------- 区間と判定


def interval_verdict(lo: float, hi: float, *, lower: float | None = None,
                     upper: float | None = None) -> str:
    """区間 ``[lo, hi]`` と線の関係を 3 値で返す(Sargent 2016 の区間仮説)。

    ``"pass"`` = 区間が全部線の内側(同値)/ ``"fail"`` = 全部外側 /
    ``"undecided"`` = 線をまたぐ(**検出力不足**・追加 seed でしか解けない)。
    """
    if lower is None and upper is None:
        raise ValueError("線が 1 本も無い(上限も下限も None)")
    inside = True
    outside = False
    if upper is not None:
        inside = inside and (hi <= upper)
        outside = outside or (lo > upper)
    if lower is not None:
        inside = inside and (lo >= lower)
        outside = outside or (hi < lower)
    if inside:
        return "pass"
    if outside:
        return "fail"
    return "undecided"


def family_half_width(sd: float, n_seeds: int, *,
                      alpha_per_metric: float = FAMILY_ALPHA_PER_METRIC) -> float:
    """平均の家族 95% 区間の半幅 = ``t(0.995, n−1)·SD/√n``(第209 の親再計算と同じ式)。"""
    if abs(alpha_per_metric - FAMILY_ALPHA_PER_METRIC) > 1e-12:
        raise ValueError(
            f"α は {FAMILY_ALPHA_PER_METRIC}/指標のみ(t の表が 0.995 分位しかない)。"
            f"α={alpha_per_metric} を使うなら scipy を入れて t 分位を計算すること。")
    return float(t_quantile_995(n_seeds - 1) * float(sd) / math.sqrt(n_seeds))


def seeds_needed(sd: float, distance: float, *, n_min: int = N_NEEDED_MIN,
                 n_max: int = N_NEEDED_MAX) -> int | None:
    """``N=(t(0.995,N−1)·SD/距離)²`` を満たす最小の N(``n_min..n_max``)。無ければ None。

    t は n で変わるので閉形式にせず逐次に探す。距離 0(平均が線の上)は**解けない**=None。
    """
    d = float(distance)
    s = float(sd)
    if math.isnan(d) or math.isnan(s) or not (d > 0.0):
        return None
    if s <= 0.0:
        return n_min
    for n in range(n_min, n_max + 1):
        if t_quantile_995(n - 1) * s / math.sqrt(n) <= d:
            return n
    return None


def _values(per_seed_metric: Sequence[Mapping[str, Any]], key: str) -> list[float] | None:
    """seed ごとの統計量。1 本でも欠け/未定義なら None(**推測で埋めない**)。"""
    out: list[float] = []
    for m in per_seed_metric:
        v = m.get(key)
        if v is None:
            return None
        v = float(v)
        if math.isnan(v):
            return None
        out.append(v)
    return out


def stat_entry(values: Sequence[float], *, kind: str, lower: float | None,
               upper: float | None, alpha_per_metric: float = FAMILY_ALPHA_PER_METRIC
               ) -> dict[str, Any]:
    """1 統計量の seed ごとの値 → 平均・SD・家族 95% 区間・同値検定の判定・要る seed 数。"""
    arr = np.asarray(list(values), dtype=np.float64)
    n = int(arr.size)
    if n < 2:
        raise ValueError("seed は 2 本以上(SD が定義できない)")
    mean = float(arr.mean())
    sd = float(arr.std(ddof=1))
    if kind == "int":
        lo, hi = float(arr.min()), float(arr.max())
        half: float | None = None
        interval_kind = "min_max"
        note = "整数指標なので seed ごとの値の最小/最大で区間を代用(平均±半幅は使わない)"
    else:
        half = family_half_width(sd, n, alpha_per_metric=alpha_per_metric)
        lo, hi = mean - half, mean + half
        interval_kind = "family95_t"
        note = "半幅 = t(0.995, n−1)·SD/√n(5 指標 Bonferroni・指標あたり両側 α)"
    verdict = interval_verdict(lo, hi, lower=lower, upper=upper)
    dists = [abs(mean - x) for x in (lower, upper) if x is not None]
    distance = min(dists) if dists else float("nan")
    return {
        "per_seed": [float(v) for v in arr],
        "n": n,
        "mean": mean,
        "sd_ddof1": sd,
        "half_width": half,
        "interval": [lo, hi],
        "interval_kind": interval_kind,
        "interval_note": note,
        "line": {"lower": lower, "upper": upper},
        "alpha_per_metric": float(alpha_per_metric),
        "alpha_meaning": "製作者危険(producer risk)。β(利用者危険)は計算しない=要る seed 数で代える",
        "verdict": verdict,
        "distance_to_line": distance,
        "n_needed": seeds_needed(sd, distance),
        "n_needed_formula": "N=(t(0.995, N−1)·SD/|平均−線|)² を満たす最小の N(N=3..10)",
        "t_quantile": float(t_quantile_995(n - 1)),
    }


def _combine(verdicts: Sequence[str]) -> str:
    """指標の判定 = 統計量の 3 値 AND(1 つでも fail → fail・残りに undecided → undecided)。"""
    if any(v == "fail" for v in verdicts):
        return "fail"
    if any(v == "undecided" for v in verdicts):
        return "undecided"
    return "pass"


def _limit_of(per_seed_metric: Sequence[Mapping[str, Any]], limit_key: str) -> float:
    """全 seed で線が一致することを確かめてから返す(混ざった prereg を弾く)。"""
    vals = []
    for m in per_seed_metric:
        lim = m.get("limit") or {}
        if limit_key not in lim:
            raise KeyError(f"線 {limit_key!r} が five_metrics の limit に無い: {sorted(lim)}")
        vals.append(float(lim[limit_key]))
    if max(vals) - min(vals) > 0.0:
        raise ValueError(f"seed 間で線 {limit_key!r} が違う: {vals}(prereg が混ざっている)")
    return vals[0]


def _metric_entry(per_seed_metric: Sequence[Mapping[str, Any]], metric: str, *,
                  judged: bool, alpha_per_metric: float) -> dict[str, Any]:
    name = per_seed_metric[0].get("name", metric)
    measured = all(bool(m.get("measured")) for m in per_seed_metric)
    entry: dict[str, Any] = {
        "name": name,
        "judged": judged,
        "measured": measured,
        "per_seed_pass_v12": [m.get("pass") for m in per_seed_metric],
    }
    if not judged:
        entry["demoted_reason"] = (
            "v1.3 §7: 深夜(0〜5 時)は 3 seed の家族 95% が ±18.6%(第209 の親再計算)"
            "=判定に使わず記述へ。n_measured にも数えない")
    if not measured:
        entry["verdict"] = None
        entry["stats"] = {}
        entry["reason"] = per_seed_metric[0].get("reason", "1 本以上の seed で未測定")
        return entry
    stats: dict[str, Any] = {}
    verdicts: list[str] = []
    for spec in METRIC_STATS[metric]:
        key = spec["key"]
        line = _limit_of(per_seed_metric, spec["limit_key"])
        lower = line if spec["bound"] in ("lower", "both") else None
        upper = line if spec["bound"] in ("upper", "both") else None
        vals = _values(per_seed_metric, key)
        if vals is None:
            stats[key] = {
                "per_seed": [m.get(key) for m in per_seed_metric],
                "verdict": "fail",
                "line": {"lower": lower, "upper": upper},
                "reason": "1 本以上の seed で統計量が未定義(τ-b の分母 0 など)"
                          "=1 ラン版 _pass(nan, ...) と同じく不合格に倒す(expedient)",
                "why_this_stat": spec["why"],
            }
            verdicts.append("fail")
            continue
        st = stat_entry(vals, kind=spec["kind"], lower=lower, upper=upper,
                        alpha_per_metric=alpha_per_metric)
        st["why_this_stat"] = spec["why"]
        stats[key] = st
        verdicts.append(st["verdict"])
    entry["stats"] = stats
    entry["verdict"] = _combine(verdicts)
    return entry


def ensemble_verdict(per_seed_results: list[dict], prereg: Mapping[str, Any] | None = None,
                     alpha_per_metric: float = FAMILY_ALPHA_PER_METRIC, *,
                     per_seed_h1_day: Sequence[Mapping[str, Any]] | None = None,
                     labels: Sequence[str] | None = None) -> dict[str, Any]:
    """事前登録 v1.3 のアンサンブル判定。**純関数**(テストの入口)。

    Args:
        per_seed_results: seed ごとの ``c7lib.five_metrics`` の結果(2 本以上)。
        prereg: 記録用の合格線(既定=1 本目の ``res["prereg"]``)。**線はここから読まない**
            (実際に判定に使われた ``res[H*]["limit"]`` を読む=写し事故を避ける)。
        alpha_per_metric: 指標あたりの製作者危険。既定 0.01(5 指標 Bonferroni の家族 95%)。
        per_seed_h1_day: ``h1_day_window`` で 6〜23 時に切り直した seed ごとの H1。
            与えれば **H1 の判定はこちら**を使い、24 h 版は ``descriptive_24h`` へ回す。
        labels: seed の名前(報告用)。

    Returns:
        指標ごとの ``stats``(seed ごとの値・平均・SD・家族 95% 区間・線・判定・要る seed 数)と
        総合(``n_pass``/``n_measured``/``n_undecided``/``pass``)。
    """
    n = len(per_seed_results)
    if n < 2:
        raise ValueError("v1.3 のアンサンブル判定は seed 2 本以上(1 本なら v1.2)")
    if per_seed_h1_day is not None and len(per_seed_h1_day) != n:
        raise ValueError(f"per_seed_h1_day の本数が合わない: {len(per_seed_h1_day)} != {n}")

    metrics: dict[str, Any] = {}
    for m in ALL_METRICS:
        judged = m in JUDGED_METRICS
        if m == "H1" and per_seed_h1_day is not None:
            entry = _metric_entry(list(per_seed_h1_day), "H1", judged=judged,
                                  alpha_per_metric=alpha_per_metric)
            entry["window"] = "06-23"
            entry["window_note"] = (
                "v1.3 §7: 深夜(0〜5 時)を判定から外したので H1 は 6〜23 時で再計算した"
                "(24 h 版は descriptive_24h)")
            d24 = _metric_entry([r["H1"] for r in per_seed_results], "H1", judged=False,
                                alpha_per_metric=alpha_per_metric)
            d24["demoted_reason"] = "24 h 版は記述(判定は 6〜23 時版)"
            entry["descriptive_24h"] = d24
        else:
            entry = _metric_entry([r[m] for r in per_seed_results], m, judged=judged,
                                  alpha_per_metric=alpha_per_metric)
            if m == "H1":
                entry["window"] = "00-23"
                entry["window_note"] = (
                    "per_seed_h1_day が与えられなかったので 24 h のまま判定した"
                    "(v1.3 §7 は 6〜23 時を求める=呼び出し側の欠落)")
        metrics[m] = entry

    judged_measured = [m for m in JUDGED_METRICS if metrics[m]["measured"]]
    verdicts = [metrics[m]["verdict"] for m in judged_measured]
    return {
        "schema": SCHEMA,
        "prereg_version": PREREG_VERSION,
        "n_seeds": n,
        "labels": list(labels) if labels is not None else None,
        "alpha_per_metric": float(alpha_per_metric),
        "family": {
            "size": FAMILY_SIZE,
            "alpha_family": float(alpha_per_metric) * FAMILY_SIZE,
            "correction": "Bonferroni(Currie & Cheng 2016 §6.2)",
            "df": n - 1,
            "t_quantile_995": float(t_quantile_995(n - 1)),
            "half_width_formula": "t(0.995, n−1)·SD/√n",
        },
        "beta_note": "β(利用者危険)は計算しない——代わりに『要る seed 数』N=(t·SD/距離)² を出す",
        "judged_metrics": list(JUDGED_METRICS),
        "descriptive_metrics": list(DESCRIPTIVE_METRICS),
        "metrics": metrics,
        "prereg": dict(prereg) if prereg is not None else dict(per_seed_results[0].get("prereg", {})),
        "n_measured": len(judged_measured),
        "n_pass": sum(1 for v in verdicts if v == "pass"),
        "n_fail": sum(1 for v in verdicts if v == "fail"),
        "n_undecided": sum(1 for v in verdicts if v == "undecided"),
        "pass": bool(verdicts) and all(v == "pass" for v in verdicts),
        "stopping_rule": STOPPING_RULE,
    }


# ---------------------------------------------------------------- H1 の昼窓


def apply_ensemble_verdict(payload: dict, v13: Mapping[str, Any]) -> dict:
    """v1.3 では **トップレベルの ``n_pass``/``n_measured``/``pass`` をアンサンブル判定で置く**(親判断・第216)。

    理由: ``tools/c7/c7_accept.py`` の HOLD 行はトップレベルを読むので、v1.3 で走らせたのに
    seed 1 の v1.2 点判定が受入表に載るのを防ぐ。seed 1 の点判定は ``seed1_v12`` に残す
    (v1.2 のときは呼ばれない=既定不変)。**純関数**(入力を壊さず新しい dict を返す)。
    """
    out = dict(payload)
    out["seed1_v12"] = {k: payload[k] for k in ("n_pass", "n_measured", "pass")}
    out["n_pass"] = int(v13["n_pass"])
    out["n_measured"] = int(v13["n_measured"])
    out["pass"] = bool(v13["pass"])
    out["verdict_source"] = "v1.3 ensemble(H3 は記述・undecided は合格にしない)"
    return out


def h1_day_window(sim_table: np.ndarray, obs_share: np.ndarray, *,
                  hours: Sequence[int] = DAY_HOURS,
                  prereg: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """H1(相関)を**昼 6〜23 時だけ**で計算し直す。

    ``c7lib.five_metrics`` に**時間帯を絞る口が無い**ので、入力表 ``(24, 5)`` と観測
    ``(5, 24)`` を ``hours`` の列だけに切って渡す(観測は切ったあとエリアごとに再正規化=
    ラン側 ``hour_share`` が窓内で正規化するのと揃える。揃えないと Pearson r がずれる)。
    切った表では **H2**(``peak_hours`` の既定ラベルが 0..len−1 になる)と **H3**
    (``NIGHT_HOURS``=1〜4 時が窓の外)は意味を持たないので、**H1 だけを返す**。
    """
    hs = list(hours)
    t = np.asarray(sim_table, dtype=np.float64)[hs, :]
    o = np.asarray(obs_share, dtype=np.float64)[:, hs]
    tot = o.sum(axis=1, keepdims=True)
    o = np.divide(o, np.where(tot > 0.0, tot, 1.0))
    res = c7lib.five_metrics(t, o, prereg=prereg)
    h1 = dict(res["H1"])
    h1["hours"] = hs
    h1["window"] = "06-23"
    return h1


# ---------------------------------------------------------------- GET 包絡(記述のみ)


def get_envelope(sim_shares: Sequence[np.ndarray], obs_share: np.ndarray,
                 area_ids: Sequence[str] = c7lib.AREA_IDS) -> dict[str, Any]:
    """seed 間の min/max 包絡と、holdout が内側にある時刻数。**検定ではない**。

    s 本の大域包絡(GET)で言える最小の p は 1/s(Myllymäki & Mrkvička)。s=3 なら
    p ≥ 1/s=1/3=0.333 なので α=0.05 には届かない=**合否に使わない**(v1.3 §7)。
    """
    stack = np.stack([np.asarray(s, dtype=np.float64) for s in sim_shares])
    if stack.ndim != 3:
        raise ValueError(f"sim_shares は (n, area, hour) の束: 得た形 {stack.shape}")
    obs = np.asarray(obs_share, dtype=np.float64)
    if obs.shape != stack.shape[1:]:
        raise ValueError(f"形が違う: sim {stack.shape[1:]} vs obs {obs.shape}")
    n_seeds = int(stack.shape[0])
    lo = stack.min(axis=0)
    hi = stack.max(axis=0)
    inside = (obs >= lo) & (obs <= hi)
    n_hours = int(obs.shape[1])
    per_area: dict[str, Any] = {}
    for i, aid in enumerate(list(area_ids)[: obs.shape[0]]):
        per_area[aid] = {
            "n_inside": int(inside[i].sum()),
            "n_hours": n_hours,
            "hours_outside": [int(h) for h in np.nonzero(~inside[i])[0]],
            "envelope_width_mean": float((hi[i] - lo[i]).mean()),
        }
    return {
        "is_test": False,
        "p_floor": 1.0 / n_seeds,
        "note": (f"s={n_seeds} 本の大域包絡(GET)で言える最小の p は 1/s="
                 f"{1.0 / n_seeds:.3f}=**検定ではない**(記述のみ・合否に使わない)"),
        "n_seeds": n_seeds,
        "n_cells": int(obs.size),
        "n_inside_total": int(inside.sum()),
        "per_area": per_area,
    }


# ---------------------------------------------------------------- fair CRPS


def crps_fair_terms(forecast: Sequence[float], observation: float) -> dict[str, float]:
    """CRPS と **fair CRPS**(Ferro 2014)の 2 項を分けて返す。**純関数**。

    標準の標本推定量 ``CRPS = E|X−y| − ½E|X−X'|``(第 2 項は ``1/(2M²)ΣΣ|xi−xj|``)。
    fair 版は第 2 項の分母を ``2M(M−1)`` にする=**第 2 項に M/(M−1) を掛ける**
    (M=3 なら ×1.5)。raw の値は ``tools/c8/ensemble.crps_ensemble`` を**流用**して
    求める(同じ定義の実装を 2 本持たない)。
    """
    x = np.asarray(forecast, dtype=np.float64).ravel()
    m = int(x.size)
    if m < 2:
        raise ValueError(f"fair CRPS はメンバー 2 本以上(M={m})")
    y = float(observation)
    term1 = float(np.abs(x - y).mean())
    term2_raw = 0.5 * float(np.abs(x[:, None] - x[None, :]).mean())
    factor = m / (m - 1.0)
    term2_fair = term2_raw * factor
    return {
        "m": float(m),
        "term1": term1,
        "term2_raw": term2_raw,
        "term2_fair": term2_fair,
        "fair_factor": factor,
        "crps": float(c8_ensemble.crps_ensemble(x, y)),
        "crps_fair": term1 - term2_fair,
    }


def fair_crps_table(sim_shares: Sequence[np.ndarray], obs_share: np.ndarray,
                    area_ids: Sequence[str] = c7lib.AREA_IDS) -> dict[str, Any]:
    """エリア×時刻ごとの在圏シェアの アンサンブル CRPS と fair CRPS(平均・比)。"""
    stack = np.stack([np.asarray(s, dtype=np.float64) for s in sim_shares])
    obs = np.asarray(obs_share, dtype=np.float64)
    if obs.shape != stack.shape[1:]:
        raise ValueError(f"形が違う: sim {stack.shape[1:]} vs obs {obs.shape}")
    m = int(stack.shape[0])
    n_area, n_hour = obs.shape
    raw = np.zeros((n_area, n_hour), dtype=np.float64)
    fair = np.zeros_like(raw)
    t2r = np.zeros_like(raw)
    t2f = np.zeros_like(raw)
    for i in range(n_area):
        for h in range(n_hour):
            d = crps_fair_terms(stack[:, i, h], float(obs[i, h]))
            raw[i, h] = d["crps"]
            fair[i, h] = d["crps_fair"]
            t2r[i, h] = d["term2_raw"]
            t2f[i, h] = d["term2_fair"]
    raw_mean = float(raw.mean())
    fair_mean = float(fair.mean())
    t2r_mean = float(t2r.mean())
    t2f_mean = float(t2f.mean())
    return {
        "m": m,
        "fair_factor": m / (m - 1.0),
        "definition": "CRPS = E|X−y| − ½E|X−X'| / fair は第 2 項に M/(M−1)(Ferro 2014・ECMWF)",
        "n_cells": int(obs.size),
        "crps_mean": raw_mean,
        "crps_fair_mean": fair_mean,
        "ratio_fair_over_raw": (fair_mean / raw_mean) if raw_mean != 0.0 else float("nan"),
        "term2_raw_mean": t2r_mean,
        "term2_fair_mean": t2f_mean,
        "term2_ratio": (t2f_mean / t2r_mean) if t2r_mean != 0.0 else float("nan"),
        "per_area_crps_fair": {list(area_ids)[i]: float(fair[i].mean())
                               for i in range(min(n_area, len(area_ids)))},
    }


# ---------------------------------------------------------------- 報告


_VERDICT_JA = {"pass": "PASS(同値)", "fail": "FAIL", "undecided": "UNDECIDED(検出力不足)"}


def _fmt(v: Any, digits: int = 5) -> str:
    if v is None:
        return "—"
    v = float(v)
    if math.isnan(v):
        return "nan"
    return f"{v:.{digits}f}"


def _line_text(line: Mapping[str, Any]) -> str:
    lo, hi = line.get("lower"), line.get("upper")
    if lo is not None and hi is not None:
        return f"{_fmt(lo)} ≤ D ≤ {_fmt(hi)}"
    if hi is not None:
        return f"D ≤ {_fmt(hi)}"
    return f"D ≥ {_fmt(lo)}"


def _stat_rows(metric: str, entry: Mapping[str, Any]) -> list[list[str]]:
    rows: list[list[str]] = []
    for key, st in (entry.get("stats") or {}).items():
        if "mean" not in st:
            rows.append([metric, key, "—", "—", _line_text(st.get("line", {})),
                         _VERDICT_JA.get(str(st.get("verdict")), "?"), "—",
                         str(st.get("reason", ""))])
            continue
        half = st.get("half_width")
        mid = (f"{_fmt(st['mean'])} ± {_fmt(half)}" if half is not None
               else f"{_fmt(st['mean'])}(SD {_fmt(st['sd_ddof1'])})")
        iv = f"[{_fmt(st['interval'][0])}, {_fmt(st['interval'][1])}]"
        nn = st.get("n_needed")
        rows.append([
            metric, key, mid, iv, _line_text(st["line"]),
            _VERDICT_JA.get(str(st["verdict"]), "?"),
            ("—" if nn is None else str(nn)),
            "seed: " + " / ".join(_fmt(v) for v in st["per_seed"]),
        ])
    return rows


def report_v13(verdict: Mapping[str, Any], envelope: Mapping[str, Any] | None = None,
               crps: Mapping[str, Any] | None = None,
               labels: Sequence[str] | None = None) -> str:
    """v1.3 節の Markdown(``holdout_compare.report`` の末尾に足す)。"""
    lab = list(labels or verdict.get("labels") or [])
    seed_text = (", ".join(f"`{x}`" for x in lab) if lab
                 else f"{verdict['n_seeds']} 本(名前未指定)")
    fam = verdict["family"]
    out: list[str] = [
        f"## 事前登録 v1.3(seed アンサンブル判定・{verdict['n_seeds']} 本)",
        "",
        f"- seed: {seed_text}",
        f"- 家族 95%: {fam['size']} 指標 Bonferroni → 指標あたり α={verdict['alpha_per_metric']}"
        f"(**製作者危険**・両側)/ 半幅 = {fam['half_width_formula']} / "
        f"t(0.995, {fam['df']}) = {fam['t_quantile_995']:.3f}",
        f"- {verdict['beta_note']}",
        "- 判定は**同値検定**(Sargent, Goldsman & Yaacoub 2016 の区間仮説): 区間が全部線の"
        "内側=`pass`・全部外側=`fail`・またぐ=`undecided`(検出力不足)。"
        "**線 H1〜H5 の値は v1.2 から変えていない**。",
        f"- 判定に使う指標: {', '.join(verdict['judged_metrics'])} / 記述のみ: "
        f"{', '.join(verdict['descriptive_metrics'])}",
        "",
    ]
    rows: list[list[str]] = []
    for m in verdict["judged_metrics"]:
        entry = verdict["metrics"][m]
        if not entry.get("measured"):
            rows.append([m, "—", "測定不能", "—", "—", "—", "—", str(entry.get("reason", ""))])
            continue
        rows.extend(_stat_rows(m, entry))
    out.append(c7lib.markdown_table(
        ["指標", "統計量", "平均 ± 半幅", "区間", "線", "判定", "要る seed 数", "seed ごとの値"],
        rows))
    out.append("")

    # --- 記述: H3 と H1 の 24 h 版 ---
    h3 = verdict["metrics"].get("H3", {})
    out += [
        "### 記述(判定に使わない)",
        "",
        f"**H3 深夜残存率(平日休日比の代替)**: {h3.get('demoted_reason', '')}。",
        "",
    ]
    if h3.get("measured"):
        out.append(c7lib.markdown_table(
            ["指標", "統計量", "平均 ± 半幅", "区間", "線(参考)", "参考判定", "要る seed 数",
             "seed ごとの値"], _stat_rows("H3", h3)))
    else:
        out.append(f"- H3 は測定不能: {h3.get('reason', '')}")
    out.append("")
    h1 = verdict["metrics"].get("H1", {})
    out.append(f"**H1 の窓**: 判定は `{h1.get('window', '?')}`。{h1.get('window_note', '')}")
    out.append("")
    d24 = h1.get("descriptive_24h")
    if d24 and d24.get("measured"):
        out.append(c7lib.markdown_table(
            ["指標", "統計量", "平均 ± 半幅", "区間", "線(参考)", "参考判定", "要る seed 数",
             "seed ごとの値"], _stat_rows("H1(24 h)", d24)))
        out.append("")

    # --- GET 包絡 ---
    if envelope is not None:
        out += ["### GET 包絡(記述のみ・**検定ではない**)", "",
                f"- {envelope['note']}",
                f"- holdout が seed 間 min/max 包絡の内側にある時刻数: "
                f"{envelope['n_inside_total']}/{envelope['n_cells']}(エリア×時刻)",
                ""]
        out.append(c7lib.markdown_table(
            ["エリア", "内側の時刻数", "外れた時刻", "包絡の幅(平均)"],
            [[a, f"{d['n_inside']}/{d['n_hours']}",
              (", ".join(str(h) for h in d["hours_outside"]) or "—"),
              _fmt(d["envelope_width_mean"], 6)]
             for a, d in envelope["per_area"].items()]))
        out.append("")

    # --- fair CRPS ---
    if crps is not None:
        out += ["### fair CRPS(Ferro 2014・ECMWF)", "",
                f"- 定義: {crps['definition']}",
                f"- M={crps['m']} → 第 2 項の係数 M/(M−1) = {crps['fair_factor']:.3f}"
                f"(実測の第 2 項比 {crps['term2_ratio']:.3f})",
                f"- エリア×時刻 {crps['n_cells']} セルの平均: CRPS {crps['crps_mean']:.6f} / "
                f"fair CRPS {crps['crps_fair_mean']:.6f} / fair÷raw "
                f"{crps['ratio_fair_over_raw']:.3f}",
                ""]

    # --- 総合 ---
    out += [
        "### 総合(v1.3)",
        "",
        f"- **{verdict['n_pass']}/{verdict['n_measured']} 合格**"
        f"(判定対象は H3 を除く {len(verdict['judged_metrics'])} 指標・"
        f"うち測定できたのは {verdict['n_measured']})・"
        f"undecided {verdict['n_undecided']} / fail {verdict['n_fail']}"
        f" → **{'PASS' if verdict['pass'] else 'NOT PASS'}**",
        f"- 停止則: {verdict['stopping_rule']}",
        "",
    ]
    return "\n".join(out)
