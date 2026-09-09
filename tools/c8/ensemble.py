# -*- coding: utf-8 -*-
"""ensemble.py — アンサンブル運用(Phase 5・T8)の**設計だけ**: ラン構成 manifest の生成器。

**本ツールはランを回さない**(C8 後半で親がサーバーで回す)。作るのは
``EnsembleSpec``(R14 G-4)の JSON と、そこから出る GPU 時間の見積り・完了済みラン表の
スキーマ・面2の計器(CRPS・spread-skill)の計算式。

正典
- 計器盤設計書(R14)**G-4**「run manifest に実験型を2つ追加する。**EnsembleSpec**=同一
  パラメタで **seed のみ**変える(不確実性の測定・面2の判定単位)。**SweepSpec**=パラメタ/
  expedient を変える(感度・ablation)。**k\\* の判定は EnsembleSpec に対してのみ定義**。
  ラン定義の最小要素(BehaviorSpace に準拠)= 掃引変数 × repetitions × reporters
  (面1/面2 の指標のみ)× stop 条件 × setup/go」。
- 同 **G-5**「``seed = blake3(manifest_sha256 ‖ run_index)``(決定的写像)。OS 乱数・暗黙 seed を
  禁止し、U8 テストに『同一 (manifest, run_index) で状態ハッシュ一致』『異なる run_index で
  RNG 状態が衝突しない』を追加。出力は**逐次書き出し**(Parquet 日次+journal)を既定にし、
  終了時一括書き出しを禁止(中断耐性)」。
- 同 **G-6**「``(manifest_sha256, run_index)`` を主キーとする**完了済みラン表**(Parquet)を持ち、
  再開=未完了 index の再投入。checkpoint(6 時間毎)から途中再開。失敗ランは自動で 1 回
  再投入し、2 回目失敗は診断行へ」。**G-7**「自前ラン表(Parquet)+DuckDB。mlflow は Phase 5 で
  必要になったら閲覧用アダプタとして後付け」。
- 同 **G-8**「面2に **CRPS**(reliability/resolution 分解)と **spread-skill ratio**
  (アンサンブル幅/RMSE・≈1 が目安)を常設。『ランを増やせば良くなる』ではなく
  『**幅が正しいか**』を測る自己点検。ラン本数の根拠=Monte Carlo 標準誤差から逆算
  (Siepe et al. 2024 の式=**未確認**)→ 確認までは『**初回=seed 群 8 本**・spread-skill で
  再評価』の expedient」。
- 同 **G-2**「面2の合否=実行不能度 ``I_i = |mean_ens(y_i) − z_i| / sqrt(Var_ens + Var_obs + Var_disc)``・
  **I ≤ 3**・``I_M = max_i I_i``」。**Var_ens はアンサンブルが無いと計算できない**
  =単一ランで面2の判定を出してはいけない、の実装上の理由。
- 決定台帳「アンサンブル=**master_seed のみ変更**」・方法論「複数実行+感度分析の報告を標準に」。
- 予算宣言表 **W1**(≤24 時間/シミュ日)・**L2**(ablation 予約 20%)・**S1/S2**(記録)。

自前の細部(expedient・実装計画書 §8 へ写した)
- blake3 の 64 bit 切り出しと ``& (2**63−1)`` のマスク(G-5 は写像の形しか決めていない)。
- 完了済みラン表の列名(G-7「自前ラン表のスキーマ」が expedient と明記されている)。
- CRPS はアンサンブル標本からの標準推定量 ``mean|x−y| − ½·mean|x−x'|``(分解は未実装)。

親が叩く例::

    python tools/c8/ensemble.py --n 8 --agents 390067 --ticks 1440 \\
        --manifest-sha <run manifest の sha256> --out docs/ops/dashboard
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c8lib  # noqa: E402

#: R14 G-8「初回=seed 群 8 本」(**expedient**: Siepe et al. 2024 の反復回数式は未確認)。
DEFAULT_N_RUNS: int = 8

#: 予算宣言表 W1 の上限[時間/シミュ日](**本文が正典**・数値は見積りの突合にだけ使う)。
W1_HOURS: float = 24.0

#: G-5 の seed 写像で使う区切り(``core.rng`` の鍵導出と同じ 0x1F)。
SEED_SEP: bytes = b"\x1f"

#: 完了済みラン表の列(G-6/G-7・**列名は自前=expedient**)。
RUN_TABLE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("manifest_sha256", "str  主キー①(EnsembleSpec の同定)"),
    ("run_index", "int  主キー②(0..N−1)"),
    ("master_seed", "int  = blake3(manifest_sha256 ‖ run_index) の下位 63 bit"),
    ("state", "str  queued / running / done / failed"),
    ("attempts", "int  失敗ランは自動で 1 回再投入・2 回目失敗は診断行へ(G-6)"),
    ("started_utc", "datetime"),
    ("finished_utc", "datetime"),
    ("wall_seconds", "float  W1 の実測"),
    ("llm_calls", "int  L4 の実測"),
    ("final_hash", "str  最終 checkpoint(T2/T8 の突合)"),
    ("checkpoint_path", "str  6 時間毎・途中再開の入口(G-6)"),
    ("journal_path", "str  逐次書き出し(G-5「終了時一括書き出しを禁止」)"),
    ("reporters", "json  面1/面2 の指標だけ(G-4)"),
)

#: 面2の reporter(k\\* のアンカー)。**値の出所は c7lib.five_metrics**(形状のみ・絶対水準は返さない)。
FACE2_REPORTERS: tuple[str, ...] = ("H1", "H2", "H3", "H4", "H5")

#: 面1の reporter(報告のみ)。
FACE1_REPORTERS: tuple[str, ...] = (
    "action_distribution",
    "format_error_rate",
    "role_action_rate",
    "llm_calls",
    "conserved",
    "census_pass",
    "diagnostics_day",
)


def run_seed(manifest_sha256: str, run_index: int) -> int:
    """G-5 の seed 写像 ``seed = blake3(manifest_sha256 ‖ run_index)``。

    下位 63 bit を符号なし整数として返す(``cli.run(seed=…)`` にそのまま渡せる)。

    Example:
        >>> a = run_seed("deadbeef", 0)
        >>> b = run_seed("deadbeef", 1)
        >>> a == run_seed("deadbeef", 0) and a != b
        True
    """
    import blake3

    if int(run_index) < 0:
        raise ValueError("run_index は 0 以上")
    digest = blake3.blake3(
        str(manifest_sha256).encode("utf-8") + SEED_SEP + str(int(run_index)).encode("ascii")
    ).digest(8)
    return int.from_bytes(digest, "big") & ((1 << 63) - 1)


def ensemble_spec(
    manifest_sha256: str,
    *,
    n_runs: int = DEFAULT_N_RUNS,
    agents: int = 390_067,
    ticks: int = 1_440,
    world_dir: str = "data/world/v2",
    calls_per_run: int | None = None,
    label: str = "c8-ensemble-v1",
) -> dict[str, Any]:
    """EnsembleSpec(R14 G-4)を組む。**master_seed 以外は 1 バイトも変えない**。

    Args:
        manifest_sha256: 元になるラン manifest の sha256(**これが実験の同定子**)。
        n_runs: 本数(既定 8=G-8 の expedient)。
        agents / ticks / world_dir: 全ランで共通の構成。
        calls_per_run: 1 ラン当たりの呼数(``None`` なら 10 呼/体/日=L4 の制御目標で見積る)。
    """
    calls = int(calls_per_run if calls_per_run is not None else agents * 10)
    per_run_h = c8lib.gpu_hours_for_calls(calls)
    runs = [
        {
            "run_index": i,
            "master_seed": run_seed(manifest_sha256, i),
            "state": "queued",
            "attempts": 0,
        }
        for i in range(int(n_runs))
    ]
    return {
        "schema": "shibuya.tools.c8/ensemble_spec/1",
        "type": "EnsembleSpec",
        "label": label,
        "manifest_sha256": manifest_sha256,
        "varies": ["master_seed"],
        "varies_note": "決定台帳「アンサンブル=master_seed のみ変更」。パラメタを変えるなら SweepSpec(別型)。",
        "fixed": {"agents": agents, "ticks": ticks, "world_dir": world_dir},
        "repetitions": int(n_runs),
        "stop": {"ticks": ticks, "note": "1 シミュ日(W1 の単位)。多シミュ日は ticks を倍にする"},
        "setup": "python -m shibuya.cli --agents {agents} --ticks {ticks} --world {world_dir} "
                 "--seed {master_seed} --run-id {label}-{run_index} --llm fleet --endpoints <…> "
                 "--occupancy-every 60 --occupancy-out <…>",
        "reporters": {"face1": list(FACE1_REPORTERS), "face2": list(FACE2_REPORTERS)},
        "runs": runs,
        "seed_rule": "blake3(manifest_sha256 ‖ 0x1F ‖ run_index) の下位 63 bit(R14 G-5)",
        "budget": {
            "calls_per_run": calls,
            "calls_total": calls * int(n_runs),
            "gpu_hours_per_run": per_run_h,
            "gpu_hours_total": per_run_h * int(n_runs),
            "calls_per_second": c8lib.CALLS_PER_SECOND,
            "basis": "受入報告 C6 §2b(5,000 体×1,440 tick=呼 50,000 を 7×A5000 で約 29 分)からの外挿=expedient",
            "w1_limit_hours_per_sim_day": (c8lib.budget_row("W1") or {}).get("declared"),
            "w1_hours": W1_HOURS,
            "w1_exceeded": bool(per_run_h > W1_HOURS),
            "note": "W1 は**1 ラン**の壁時計の上限。アンサンブルは横に並べるので総 GPU 時間は N 倍になる(逐次実行の場合)。",
        },
        "run_table_columns": [{"name": n, "note": d} for n, d in RUN_TABLE_COLUMNS],
        "resume": {
            "key": ["manifest_sha256", "run_index"],
            "rule": "未完了 index の再投入。checkpoint(6 時間毎)から途中再開。失敗は自動 1 回再投入・2 回目は診断行(R14 G-6)。",
            "workflow_engine": "導入しない(expedient・必要になれば Snakemake)",
            "tracking": "自前ラン表(Parquet)+DuckDB(R14 G-7)。mlflow は Phase 5 の閲覧用アダプタとして後付け。",
        },
        "face2_gate": {
            "form": "I_i = |mean_ens(y_i) − z_i| / sqrt(Var_ens(y_i) + Var_obs(z_i) + Var_disc(i))",
            "limit": 3.0,
            "aggregate": "I_M = max_i I_i",
            "var_disc_initial": 0.0,
            "var_disc_note": "初回 0=expedient(ablation で学習)。Var_obs は台帳の出典から・不明なら宣言。",
            "one_sided": "落ちたら不合格・通っても合格とは言わない(SBC の片側性)",
            "prereg_file": "**未作成**: k\\*(アンカー集合・I≤3・Var 各項の出所・アンサンブル本数)をリポ内の凍結ファイル(SHA)に置く=親判断待ち",
        },
        "instruments": {
            "crps": "予測分布と実測点の距離(reliability/resolution 分解は未実装)",
            "spread_skill": "アンサンブル幅 / RMSE(≈1 が目安)。'ランを増やせば良くなる' ではなく '幅が正しいか' の自己点検",
            "scorecard": "行=アンカー・列=時間解像度・セル=有意差の色(ECMWF 様式・原文未読=expedient)",
        },
        "open_questions": (
            [
                f"**1 ラン {per_run_h:.1f} h > W1 {W1_HOURS:.0f} h**: この規模({agents:,} 体×"
                f"{ticks} tick・呼 {calls:,})は 1 ラン単体で予算上限を超える(C6 実測からの外挿)。"
                "体数・シミュ日・本数のどれを削るかは親判断。"
            ]
            if per_run_h > W1_HOURS
            else []
        ) + [
            "本数 8 本は expedient(Siepe et al. 2024 の反復回数式が未確認)。spread-skill を見て再評価する。",
            "実 LLM で N 本回すと総 GPU 時間が N 倍。W1 24 h/シミュ日 × 8 本=192 h=**サーバー返却期限と衝突**する(親判断: 体数を落とす/シミュ日を短くする/本数を減らす)。",
            "k\\* の凍結ファイルが未作成(R14 G-2『リポ内の凍結ファイル(SHA)に置く』)。",
        ],
    }


def crps_ensemble(forecast: Sequence[float], observation: float) -> float:
    """CRPS のアンサンブル標本推定量 ``mean|x−y| − ½·mean_{i,j}|x_i−x_j|``。**純関数**。

    小さいほど良い。決定論予測(全メンバー同値)なら絶対誤差に一致する。

    Example:
        >>> round(crps_ensemble([1.0, 1.0, 1.0], 2.0), 6)
        1.0
    """
    x = np.asarray(forecast, dtype=np.float64).ravel()
    if x.size == 0:
        raise ValueError("メンバーが 0 本")
    y = float(observation)
    term1 = float(np.abs(x - y).mean())
    term2 = float(np.abs(x[:, None] - x[None, :]).mean())
    return term1 - 0.5 * term2


def spread_skill_ratio(
    forecasts: Sequence[Sequence[float]], observations: Sequence[float]
) -> dict[str, float]:
    """spread-skill ratio(R14 G-8)。``sqrt(mean Var_ens) / RMSE(mean_ens, obs)``。**純関数**。

    Args:
        forecasts: ``(n_cases, n_members)``。
        observations: ``(n_cases,)``。

    Returns:
        ``spread``(アンサンブル幅)・``rmse``・``ratio``(≈1 が目安)・``n_cases``・``n_members``。
    """
    f = np.atleast_2d(np.asarray(forecasts, dtype=np.float64))
    o = np.asarray(observations, dtype=np.float64).ravel()
    if f.shape[0] != o.size:
        raise ValueError(f"件数が合わない: {f.shape[0]} vs {o.size}")
    if f.shape[1] < 2:
        raise ValueError("メンバーは 2 本以上")
    var = f.var(axis=1, ddof=1)
    err = f.mean(axis=1) - o
    rmse = float(np.sqrt((err**2).mean()))
    spread = float(np.sqrt(var.mean()))
    return {
        "spread": spread,
        "rmse": rmse,
        "ratio": spread / rmse if rmse > 0 else float("inf"),
        "n_cases": int(f.shape[0]),
        "n_members": int(f.shape[1]),
    }


def implausibility(
    ens_mean: float, obs: float, var_ens: float, var_obs: float = 0.0, var_disc: float = 0.0
) -> float:
    """実行不能度 ``I``(R14 G-2)。**I ≤ 3 が合格**(Pukelsheim 3σ)。

    Example:
        >>> round(implausibility(1.0, 1.0, 0.25), 6)
        0.0
    """
    denom = float(var_ens) + float(var_obs) + float(var_disc)
    if denom <= 0.0:
        raise ValueError("分散の合計が 0(Var_ens はアンサンブルが要る)")
    return abs(float(ens_mean) - float(obs)) / float(np.sqrt(denom))


def spec_markdown(spec: Mapping[str, Any]) -> str:
    """EnsembleSpec → Markdown(**純関数**)。"""
    b = spec["budget"]
    md = [
        f"# アンサンブル運用の設計(R14 G-4/G-5/G-6/G-8)— {spec['label']}",
        "",
        f"- 型 **{spec['type']}** ・振るもの **{spec['varies']}** ・本数 **{spec['repetitions']}**",
        f"- {spec['varies_note']}",
        f"- seed 規則: `{spec['seed_rule']}`",
        f"- 固定: {spec['fixed']}",
        "",
        "## ラン一覧(master_seed のみ違う)",
        "",
        c8lib.markdown_table(
            ["run_index", "master_seed", "状態"],
            [[r["run_index"], r["master_seed"], r["state"]] for r in spec["runs"]],
        ),
        "",
        "## 予算の見積り",
        "",
        c8lib.markdown_table(
            ["項目", "値"],
            [
                ["1 ラン当たりの呼数", f"{b['calls_per_run']:,}"],
                ["総呼数", f"{b['calls_total']:,}"],
                ["1 ラン当たり GPU 壁時計[h]", f"{b['gpu_hours_per_run']:.2f}"],
                ["総 GPU 壁時計[h](逐次)", f"{b['gpu_hours_total']:.2f}"],
                ["換算の根拠", b["basis"]],
                ["W1 宣言", str(b["w1_limit_hours_per_sim_day"])[:80]],
            ],
        ),
        "",
        f"> {b['note']}",
        "",
        "## 面2 のゲート(このアンサンブルに対してのみ定義)",
        "",
        c8lib.markdown_table(
            ["項目", "値"],
            [[k, v] for k, v in spec["face2_gate"].items()],
        ),
        "",
        "## 完了済みラン表(G-6/G-7・Parquet+DuckDB)",
        "",
        c8lib.markdown_table(
            ["列", "説明"], [[c["name"], c["note"]] for c in spec["run_table_columns"]]
        ),
        "",
        f"- 主キー {spec['resume']['key']} ・{spec['resume']['rule']}",
        f"- {spec['resume']['tracking']} ・ワークフローエンジン={spec['resume']['workflow_engine']}",
        "",
        "## 計器(G-8)",
        "",
        c8lib.markdown_table(["計器", "定義"], [[k, v] for k, v in spec["instruments"].items()]),
        "",
    ]
    for q in spec.get("open_questions", ()):
        md.append(f"- **親判断待ち**: {q}")
    return "\n".join(md)


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="アンサンブル運用(Phase 5・T8)の設計=ラン構成 manifest の生成")
    ap.add_argument("--manifest-sha", default="", help="元のラン manifest の sha256(空なら placeholder)")
    ap.add_argument("--n", type=int, default=DEFAULT_N_RUNS)
    ap.add_argument("--agents", type=int, default=390_067)
    ap.add_argument("--ticks", type=int, default=1_440)
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--calls-per-run", type=int, default=0, help="0 なら 10 呼/体/日で見積る")
    ap.add_argument("--label", default="c8-ensemble-v1")
    ap.add_argument("--out", default="docs/ops/dashboard")
    args = ap.parse_args(list(argv) if argv is not None else None)

    sha = args.manifest_sha or "PLACEHOLDER-run-manifest-sha256"
    spec = ensemble_spec(
        sha,
        n_runs=args.n,
        agents=args.agents,
        ticks=args.ticks,
        world_dir=args.world,
        calls_per_run=args.calls_per_run or None,
        label=args.label,
    )
    if not args.manifest_sha:
        spec["open_questions"].insert(
            0, "manifest_sha256 が placeholder=**seed は本番の manifest が固まってから引き直す**。"
        )
    md = spec_markdown(spec)
    paths = c8lib.write_outputs(args.out, "ensemble_v1", spec, md)
    print(md)
    print(json.dumps({"out": paths}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
