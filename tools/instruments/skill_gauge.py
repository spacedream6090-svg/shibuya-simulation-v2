# -*- coding: utf-8 -*-
"""skill_gauge — 第 3 期 3-3b **CP14 の技量スコアの隣に生の点数を並べる器**(読むだけ・記録に JSON)。

正典
    決定 10-12 §4-5 CP14(単純な基準=去年の同じ日・平均・前の週より当たったかを技量スコアで測る・形式は Claude Code に任せる)・
    PENDING 仮-24(技量スコアには生の点数=fair CRPS・rank histogram・spread/skill を並べる・封印の証拠は手元の git+公開リポへの
    push)・答申 R-117 §2-3(Gneiting & Raftery 2007 の式 (8) の技量スコアは元の点数が proper でも一般に proper でない=優劣は生の点数で
    決める・Fortin ら 2014 の式 15=交換可能なら Skill ≈ √((M+1)/M)·Spread)。器の欄は ``shibuya.engine.experiment.ensemble.
    skill_container``(エンジンの側=事前登録の記録に入る)。この道具は値を埋める(``fill``)。

点数(負の向き=小さいほど良い・観測と同じ単位)
    - **CRPS(アンサンブル・fair)**: (1/M) Σ_i |x_i − y| − 1/(2M(M−1)) Σ_i Σ_j |x_i − x_j|(有限のメンバーの偏りを補正した
      推定量=scoringrules の ``estimator="fair"`` と同じ式。コードは写していない)。M=1 は定義しない(``ValueError``)。
    - **CRPS(点の予測)**: |x − y|(点の予測なら CRPS は絶対誤差に一致=Gneiting & Raftery 2007)=単純な基準の点数。
    - 参考に通常の CRPS(1/(2M²) の形)も並べる(``crps_ensemble``)。
    - **技量スコア**: 1 − 点数/基準の点数(``ensemble.skill_score`` と同じ式・基準の点数 0 は定義しない)。
    - **rank histogram**: 観測がメンバーの中で何番目か(0〜M)の度数。同じ値は乱数で順位を割る(seed つき=expedient)。
      平らは信頼度の必要条件で十分条件でない(R-117 §2-3)。時刻の近い標本は独立でないので、日や区域でまとめてから描く。
    - **広がりと誤差の比**: spread=√(平均の(1/(M−1)) の分散)・skill=アンサンブルの平均の RMSE・比=√((M+1)/M)·spread/skill
      (1 より小さければ広がり不足)。

入力(``score``)::

    {"metrics": {"<指標の id>": {"ensemble": [[x_11, …, x_1M], …],   # 事例 N × メンバー M
                                  "obs": [y_1, …, y_N],
                                  "baselines": {"mean": [b_1, …, b_N], …}}}}

使い方: ``python tools/instruments/skill_gauge.py score --input <…>.json --out <…>.json``。

読む守り(〔検収 L7〕): 入力の道筋に封印と検証側の語(``read_guard.GAUGE_DENY_TOKENS``)があれば開く前に落とす
(``read_guard.deny_hit``=慣らしと HM の計器と同じ線=較正側だけ)。答え合わせの段(外に出す予測=第 7 期)で検証側の観測を
読む線は、その段で決める(いまは開けない)。

逐次ループ宣言: 事例 × メンバー²(fair CRPS の対の和=メンバーの数は数十まで)。体の数に比例するループは無い。
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

HERE = Path(os.path.abspath(__file__)).parent
REPO = HERE.parent.parent
if str(REPO / "src") not in sys.path:  # pragma: no cover - 実行時の経路(器の欄はエンジンの側)
    sys.path.insert(0, str(REPO / "src"))

from shibuya.engine.experiment.ensemble import SKILL_BASELINES, skill_score  # noqa: E402

SCHEMA = "shibuya.tools.instruments/skill_gauge/1"
TIE_SEED = 0


def _read_guard() -> Any:
    name = "read_guard_skill"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HERE / "read_guard.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def check_path(path: str | Path) -> None:
    """入力の道筋に封印と検証側の語があれば開く前に落とす(``read_guard.deny_hit``・〔検収 L7〕)。"""
    hit = _read_guard().deny_hit(path)
    if hit:
        raise PermissionError(f"技量スコアの計器は封印と検証側を読まない(道筋に {hit!r})")


def _ens(x: Sequence[float]) -> np.ndarray:
    a = np.asarray(x, dtype=np.float64).ravel()
    if a.size == 0 or not np.all(np.isfinite(a)):
        raise ValueError("アンサンブルは有限の数の列で空でない")
    return a


def crps_fair(members: Sequence[float], obs: float) -> float:
    """fair CRPS(M ≥ 2)。"""
    x = _ens(members)
    m = x.size
    if m < 2:
        raise ValueError("fair CRPS はメンバー 2 本以上(1 本は点の予測=crps_point)")
    a = float(np.mean(np.abs(x - float(obs))))
    b = float(np.abs(x[:, None] - x[None, :]).sum()) / (2.0 * m * (m - 1))
    return a - b


def crps_ensemble(members: Sequence[float], obs: float) -> float:
    """通常の CRPS(経験分布の CRPS=1/(2M²) の形)。"""
    x = _ens(members)
    m = x.size
    return float(np.mean(np.abs(x - float(obs)))) - float(np.abs(x[:, None] - x[None, :]).sum()) / (2.0 * m * m)


def crps_point(forecast: float, obs: float) -> float:
    """点の予測の CRPS=絶対誤差。"""
    return abs(float(forecast) - float(obs))


def rank_histogram(ensemble: Sequence[Sequence[float]], obs: Sequence[float], *, seed: int = TIE_SEED) -> list[int]:
    """事例ごとの観測の順位(0〜M)の度数。同じ値は乱数で割る(seed つき)。"""
    e = np.asarray(ensemble, dtype=np.float64)
    y = np.asarray(obs, dtype=np.float64).ravel()
    if e.ndim != 2 or e.shape[0] != y.size or e.shape[1] < 1:
        raise ValueError("ensemble は 事例 N × メンバー M・obs は長さ N")
    rng = np.random.default_rng(int(seed))
    m = e.shape[1]
    counts = [0] * (m + 1)
    for i in range(y.size):  # 逐次ループ宣言: 事例の数ぶん
        below = int(np.sum(e[i] < y[i]))
        ties = int(np.sum(e[i] == y[i]))
        r = below + (int(rng.integers(0, ties + 1)) if ties else 0)
        counts[r] += 1
    return counts


def spread_skill(ensemble: Sequence[Sequence[float]], obs: Sequence[float]) -> dict[str, Any]:
    """広がり(√ 平均の 1/(M−1) の分散)・誤差(平均の RMSE)・比=√((M+1)/M)·広がり/誤差(Fortin ら 2014 の式 15)。"""
    e = np.asarray(ensemble, dtype=np.float64)
    y = np.asarray(obs, dtype=np.float64).ravel()
    if e.ndim != 2 or e.shape[0] != y.size or e.shape[1] < 2:
        raise ValueError("spread/skill はメンバー 2 本以上")
    m = e.shape[1]
    spread = float(np.sqrt(np.mean(np.var(e, axis=1, ddof=1))))
    rmse = float(np.sqrt(np.mean((e.mean(axis=1) - y) ** 2)))
    corr = math.sqrt((m + 1) / m)
    ratio = None if rmse == 0.0 else corr * spread / rmse
    return {"members": m, "cases": int(y.size), "spread": spread, "rmse": rmse, "correction": corr, "ratio": ratio,
            "note": "比 < 1 は広がり不足(交換可能なら 1 に近い)"}


def score_metric(ensemble: Sequence[Sequence[float]], obs: Sequence[float],
                 baselines: Mapping[str, Sequence[float]] | None = None, *, seed: int = TIE_SEED) -> dict[str, Any]:
    """1 つの指標の点数: 生の点数(fair CRPS の平均・基準の CRPS の平均・rank histogram・広がりと誤差の比)と技量スコア。"""
    e = np.asarray(ensemble, dtype=np.float64)
    y = np.asarray(obs, dtype=np.float64).ravel()
    fair = float(np.mean([crps_fair(e[i], y[i]) for i in range(y.size)]))
    raw = {"crps_fair": fair, "crps_ensemble": float(np.mean([crps_ensemble(e[i], y[i]) for i in range(y.size)])),
           "baseline_crps": {}, "rank_histogram": rank_histogram(e, y, seed=seed),
           "spread_skill": spread_skill(e, y), "members": int(e.shape[1]), "cases": int(y.size)}
    skill: dict[str, float | None] = {}
    for name, b in (baselines or {}).items():
        bb = np.asarray(b, dtype=np.float64).ravel()
        if bb.size != y.size:
            raise ValueError(f"基準 {name} の長さが観測と違う")
        bc = float(np.mean([crps_point(bb[i], y[i]) for i in range(y.size)]))
        raw["baseline_crps"][str(name)] = bc
        skill[str(name)] = None if bc == 0.0 else skill_score(fair, bc)
    return {"raw": raw, "error": fair, "baseline_error": dict(raw["baseline_crps"]), "skill": skill}


def fill(container: Mapping[str, Any], scores: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """技量スコアの器(``ensemble.skill_container``)に点数を埋めた写しを返す(器の欄の名は変えない)。"""
    out = copy.deepcopy(dict(container))
    for mid, sc in scores.items():
        if mid not in out["metrics"]:
            raise KeyError(f"器に指標 {mid!r} が無い")
        slot = out["metrics"][mid]
        slot["error"] = sc["error"]
        for b in SKILL_BASELINES:
            if b in sc["baseline_error"]:
                slot["baseline_error"][b] = sc["baseline_error"][b]
                slot["skill"][b] = sc["skill"][b]
                slot["raw"]["baseline_crps"][b] = sc["raw"]["baseline_crps"][b]
        for k in ("crps_fair", "rank_histogram", "spread_skill", "members"):
            slot["raw"][k] = sc["raw"][k]
    return out


def score(doc: Mapping[str, Any], *, seed: int = TIE_SEED) -> dict[str, Any]:
    """入力の全部の指標の点数(``SCHEMA``)。"""
    out = {"schema": SCHEMA, "tie_seed": int(seed), "metrics": {},
           "note": ("技量スコアは proper でない(Gneiting & Raftery 2007 の式 (8) の注意)=優劣は生の点数で決める。"
                    "rank histogram の平らさは信頼度の必要条件で十分条件でない")}
    for mid, m in doc["metrics"].items():
        out["metrics"][str(mid)] = score_metric(m["ensemble"], m["obs"], m.get("baselines"), seed=seed)
    return out


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("score")
    sp.add_argument("--input", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--seed", type=int, default=TIE_SEED)
    args = ap.parse_args(argv)
    check_path(args.input)
    doc = json.loads(Path(args.input).read_text(encoding="utf-8"))
    out = score(doc, seed=args.seed)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"[skill] {len(out['metrics'])} 指標")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
