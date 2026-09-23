# -*- coding: utf-8 -*-
"""dashboard.py — **忠実度計器盤**(R14 G-1 の3面)を Markdown+JSON の 1 枚にまとめる。

正典
- 計器盤設計書(R14)**G-1**「計器盤を3面に分け、**ゲート(合否)は面2のみ**に置く。
  面1 較正面=報告のみ・合否線なし/面2 holdout 面=**k\\* 事前宣言はここにのみ**・判定は
  ラン単位でなく**アンサンブル単位**/面3 運用面=SRE 4 シグナル・**赤は症状のみ**」。
  「面1・面2 の乖離は『原因』であり赤にしない(観察)」「面2 の不合格は『落ちたら不合格・
  通っても合格とは言わない』(SBC の片側性)を見出しに明記し、世界被覆指標 WC-1〜6 と併読」。
- 同 **G-2**「``I_i = |mean_ens(y_i) − z_i| / sqrt(Var_ens + Var_obs + Var_disc)``・**I≤3 を合格**
  (Pukelsheim 3σ)・``I_M = max_i I_i`` を面2の見出し値」。
- 同 **G-3**(TRACE 8 要素 → 工程別受入基準)・**G-9**(赤は症状のみ・通知3階級・
  バーンレート・4 ゴールデンシグナルの写像)。
- 方法論「**世界被覆指標**…報告は5値ベクトル(C,Q,D,V,R)+X+孤児+カタログ版 SHA。
  **加重和にしない**。WC-5/WC-6 のみゲート」。
- 予算宣言表(W/P/M/L/S)・運用設計書 U8/U9 §1.4(T1-T9)・知覚契約書 §7(運用診断行5本)・
  §8(指標 B の事前登録)。

入力(**あるものだけ読む**。無い欄は「—」で残し、推測で埋めない)
    ``data/world/v2/build_manifest.json`` / ``w16_gates.json`` / ``w17_gates.json`` /
    ``wc_index.json`` ・``docs/bench/c6*/**.json``(書式・役割語率/指標B/ablation①)・
    ``tools/c8/ablations_v1.json`` ・``tools/c8/sensitivity_v1.json`` ・
    ``tools/c7/c7_accept`` の出力 JSON(``--accept``)・``docs/ops/build-report-C*.md``・
    ``PENDING.md``(「歪む場所」の宣言一覧)。

出力
    ``docs/ops/dashboard/dashboard.md`` と ``dashboard.json``(親が実行してコミットする)。

親が叩く例::

    python tools/c8/dashboard.py --out docs/ops/dashboard
    python tools/c8/dashboard.py --accept docs/bench/c7/c7_accept.json --out docs/ops/dashboard
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c8lib  # noqa: E402

ROOT = c8lib.REPO_ROOT
WORLD_DIR = ROOT / "data" / "world" / "v2"

#: 面3(運用)の予算行。R14 G-9 の 4 ゴールデンシグナル + 予算宣言表。
OPS_BUDGET_ROWS: tuple[str, ...] = ("W1", "W2", "P2", "P6", "M8", "M11", "S1", "L4", "L6")

#: 運用設計書 U8/U9 §1.4 の検証テスト(**名前は設計が正典**・状態は報告書から拾う)。
VERIFICATION_TESTS: tuple[tuple[str, str], ...] = (
    ("T1", "構築の再構築一致(CI・GPU なしの段)"),
    ("T2", "ラン決定論(同 seed 再ラン一致)"),
    ("T3", "並列不変性(スレッド 1/8/32 で同一結果)"),
    ("T4", "録画リプレイ(テープ完全一致)"),
    ("T5", "順序バイアス(個体 ID 順との相関 |r| ≤ 0.05)"),
    ("T6", "LLM 層 bit 再現"),
    ("T7", "LLM 層 分布同値"),
    ("T8", "アンサンブル(seed 群)の再現"),
    ("T9", "診断行 4 列 + 保存則 2 検算の存在"),
)


# ------------------------------------------------------------------ 収集(純関数)
def collect_build_gates(manifest: Mapping[str, Any] | None) -> dict[str, Any]:
    """build_manifest → 段階ごとのゲート合否(W0-W20)。"""
    if not manifest:
        return {"available": False, "stages": [], "n_fail": None}
    stages = []
    n_fail = 0
    for st in manifest.get("stages", ()):
        gates = st.get("gates", {})
        fails = [
            k for k, v in gates.items() if isinstance(v, Mapping) and v.get("pass") is False
        ]
        n_fail += len(fails)
        stages.append(
            {
                "stage": st.get("stage"),
                "n_gates": len(gates),
                "n_fail": len(fails),
                "failing": sorted(fails),
                "n_expedients": len(st.get("expedients", ())),
                "stage_version": st.get("stage_version"),
            }
        )
    return {
        "available": True,
        "build_hash": manifest.get("build_hash"),
        "stages": stages,
        "n_stages": len(stages),
        "n_gates": sum(s["n_gates"] for s in stages),
        "n_fail": n_fail,
        "n_expedients": sum(s["n_expedients"] for s in stages),
    }


def collect_coverage(wc: Mapping[str, Any] | None) -> dict[str, Any]:
    """wc_index → 世界被覆指標(5 値ベクトル+X+孤児)。**加重和にしない**。"""
    if not wc:
        return {"available": False}
    v = dict(wc.get("vector", {}))
    return {
        "available": True,
        "catalog_version": wc.get("catalog_version"),
        "catalog_sha16": wc.get("catalog_sha16"),
        "n_classes": wc.get("n_classes"),
        "C": v.get("C"),
        "C_quantified": v.get("C_quantified"),
        "Q": v.get("Q"),
        "D": v.get("D"),
        "V": v.get("V"),
        "R": v.get("R"),
        "X": wc.get("X"),
        "orphans": len(wc.get("orphans", ())),
        "dead_stock_candidates": len(wc.get("dead_stock_candidates", ())),
        "gate_wc5": "報告のみ(前ランより悪化で警告)",
        "gate_wc6": None if wc.get("orphans") is None else (len(wc.get("orphans", ())) == 0),
    }


def collect_calibration(
    w16: Mapping[str, Any] | None, w17: Mapping[str, Any] | None
) -> list[dict[str, Any]]:
    """面1(較正面)の主要行。**合否線を付けない**(良くて当たり前=R14 G-1)。"""
    rows: list[dict[str, Any]] = []
    if w16:
        rows += [
            {"id": "W16-SRMSE-AGE", "item": "住民の年齢 SRMSE", "value": w16.get("srmse_age_resident"), "limit": (w16.get("limits") or {}).get("srmse_age")},
            {"id": "W16-SRMSE-SEX", "item": "住民の性別 SRMSE", "value": w16.get("srmse_sex_resident"), "limit": (w16.get("limits") or {}).get("srmse_sex")},
            {"id": "W16-JSD-DIR", "item": "方面配分 JSD(最大)", "value": w16.get("jsd_direction_max"), "limit": (w16.get("limits") or {}).get("jsd_direction")},
            {"id": "W16-EMPTY", "item": "住居床>0 なのに住民 0 のセル", "value": w16.get("empty_residential_cells"), "limit": 0},
            {"id": "W16-N", "item": "母集団の体数", "value": w16.get("n_total"), "limit": None},
        ]
    if w17:
        rows += [
            {"id": "W17-MOD", "item": "スケジュールの修正率", "value": w17.get("modified_rate"), "limit": 0.20},
            {"id": "W17-JSD", "item": "目的別 開始時刻 JSD(最大・raking 後)", "value": (w17.get("raking") or {}).get("jsd_max_after"), "limit": None},
            {"id": "W17-PARSE", "item": "行パース失敗率", "value": w17.get("parse_fail_rate"), "limit": None},
            {"id": "W17-ACTS", "item": "活動数/体", "value": w17.get("activities_per_agent"), "limit": None},
        ]
    return rows


def collect_quality(
    fmt: Mapping[str, Any] | None,
    metric_b: Mapping[str, Any] | None,
    ablation1: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """書式/役割語率・指標 B・ablation ① の実測(面1の補助指標)。"""
    out: dict[str, Any] = {}
    if fmt:
        s = dict(fmt.get("score", {}))
        out["format"] = {
            "source": fmt.get("source"),
            "n": s.get("n"),
            "format_error_rate": s.get("format_error_rate"),
            "format_error_rate_strict": s.get("format_error_rate_strict"),
            "gate": s.get("format_error_gate"),
            "ok": s.get("format_error_ok"),
            "ok_strict": s.get("format_error_ok_strict"),
            "role_action_rate": s.get("role_action_rate"),
            "undefined_rate": s.get("undefined_rate"),
            "action_counts": s.get("action_counts"),
        }
    if metric_b:
        c = dict(metric_b.get("comparison", {}))
        pre = dict(metric_b.get("preregistration", {}))
        out["metric_b"] = {
            "n_selected": metric_b.get("n_selected"),
            "models": [p.get("model") for p in metric_b.get("passes", ())],
            "violation_rates": [p.get("violation_rate") for p in metric_b.get("passes", ())],
            "delta_violation_rate": c.get("delta_violation_rate"),
            "delta_ci95": c.get("delta_ci95"),
            "violation_gate": c.get("violation_gate"),
            "violation_ok": c.get("violation_ok"),
            "jsd_bits": c.get("jsd_bits"),
            "null_bootstrap_p95": c.get("null_bootstrap_p95"),
            "distribution_ok": c.get("distribution_ok"),
            "prereg": pre,
        }
    if ablation1:
        out["ablation1"] = {
            "switch_effective": (ablation1.get("switch_probe") or {}).get("switch_effective"),
            "jsd_bits": ablation1.get("jsd_bits"),
            "identical_runs": ablation1.get("identical_runs"),
            "arms": [
                {k: a.get(k) for k in ("arm", "llm_calls", "format_error_rate", "prompt_tokens_mean")}
                for a in ablation1.get("arms", ())
            ],
        }
    return out


def collect_ablations(
    table: Mapping[str, Any], results: Sequence[Mapping[str, Any]] = ()
) -> dict[str, Any]:
    """腕定義表 + 実行済み結果 → 面1の ablation 節。"""
    by_id = {str(r.get("arm")): r for r in results}
    rows = []
    for a in table.get("arms", ()):
        res = by_id.get(str(a.get("id")))
        cmps = list((res or {}).get("comparisons", ()))
        rows.append(
            {
                "id": a.get("id"),
                "index": a.get("index"),
                "name": a.get("name"),
                "switch_implemented": bool((a.get("switch") or {}).get("implemented")),
                "status": a.get("status"),
                "executed": bool((res or {}).get("executed")),
                "action_jsd": cmps[0].get("action_jsd") if cmps else None,
                "exceeds_null": cmps[0].get("exceeds_null") if cmps else None,
                "gpu_hours": (a.get("cost") or {}).get("gpu_hours"),
            }
        )
    return {
        "rows": rows,
        "n_arms": len(rows),
        "n_ready": sum(1 for r in rows if r["switch_implemented"]),
        "n_executed": sum(1 for r in rows if r["executed"]),
        "l2_reserve_hours": (table.get("budget") or {}).get("reserve_hours_per_sim_day"),
        "gpu_hours_planned": (table.get("totals") or {}).get("gpu_hours_with_shared_baseline"),
    }


def collect_sensitivity(ledger: Mapping[str, Any]) -> dict[str, Any]:
    """感度台帳 → 面1の expedient 感度節。"""
    rows = []
    for r in c8lib.iter_rows(ledger):
        res = r.get("result") or {}
        rows.append(
            {
                "id": r.get("id"),
                "design_anchor": r.get("design_anchor"),
                "exec_form": r.get("exec_form"),
                "status": r.get("status"),
                "jsd_bits": res.get("jsd_bits"),
                "null_p95": res.get("null_p95"),
                "verdict": res.get("verdict"),
            }
        )
    return {
        "rows": rows,
        "n_rows": len(rows),
        "n_done": sum(1 for r in rows if r["status"] == "done"),
        "n_not_driving": sum(1 for r in rows if r["verdict"] == "not_driving"),
        "n_needs_run": sum(1 for r in rows if r["verdict"] == "needs_run"),
        "n_process_ablations": len((ledger.get("process_ablations") or {}).get("ids", ())),
        "n_build_manifest_expedients": (ledger.get("build_manifest_expedients") or {}).get("count"),
    }


#: 面2(holdout)の行=面3には出さない(R14 G-1「ゲートは面2のみ」)。
FACE2_ROW_IDS: frozenset[str] = frozenset({"HOLD", "SEAL"})


def collect_ops(accept: Mapping[str, Any] | None) -> dict[str, Any]:
    """面3(運用面)。``tools/c7/c7_accept`` の受入表を行に使う(**holdout 行は除く**)。"""
    budget = {rid: c8lib.budget_row(rid) for rid in OPS_BUDGET_ROWS}
    rows = []
    if accept:
        for r in accept.get("rows", ()):
            if r.get("id") in FACE2_ROW_IDS:
                continue  # holdout は面2の受け持ち(同じ行を 2 面に出さない)
            rows.append(
                {
                    "id": r.get("id"),
                    "item": r.get("item"),
                    "measured": r.get("measured"),
                    "limit": r.get("limit"),
                    "judge": r.get("judge"),
                    "note": r.get("note"),
                }
            )
    reds = [r for r in rows if r.get("judge") is False]
    return {
        "available": bool(accept),
        "budget_declared": budget,
        "rows": rows,
        "n_red": len(reds),
        "red_ids": [r["id"] for r in reds],
        "alarm_rule": "R14 G-9: 赤は症状のみ(保存則残差超過・介入回数≠0・繰り延べ滞留が L6 超・RSS が M8 超・LLM 失敗率超)。1 tick の外れ値でなくバーンレートで判定。",
    }


def collect_holdout(accept: Mapping[str, Any] | None) -> dict[str, Any]:
    """面2(holdout 面)。**唯一のゲート**・判定はアンサンブル単位(R14 G-1/G-2)。"""
    row = None
    seal = None
    for r in (accept or {}).get("rows", ()):
        if r.get("id") == "HOLD":
            row = r
        if r.get("id") == "SEAL":
            seal = r
    return {
        "available": row is not None and row.get("measured") is not None,
        "holdout_row": row,
        "seal_row": seal,
        "metrics": ["H1 相関", "H2 ピーク時刻", "H3 平日休日比(測定不能→深夜残存率で代替)", "H4 エリア構成", "H5 属性構成"],
        "prereg_status": "案(tools/c7/c7lib.PREREG_V0・PENDING D-40)=**k\\* の凍結ファイルは未作成**",
        "implausibility": {
            "I_M": None,
            "gate": "I ≤ 3(Pukelsheim 3σ・R14 G-2)",
            "note": "**未計算**: I の計算には Var_ens(アンサンブル分散)が要る=EnsembleSpec の N 本ランが前提(C8 後半)。単一ランでは面2の判定を出さない(R14 G-1『判定はラン単位でなくアンサンブル単位』)。",
        },
        "one_sided": "落ちたら不合格・通っても合格とは言わない(SBC の片側性・R14 G-1)",
    }


_PENDING_ROW = re.compile(r"^\|\s*(D-\d+)\s*\|")


def collect_distortions(pending_text: str) -> list[dict[str, str]]:
    """PENDING.md から「歪む場所」の宣言候補を拾う(D-33/D-37/D-38 ほか)。

    §2 の表の行のうち、本文か推奨に **「歪む場所」** または **「宣言」** が現れるものを返す。
    """
    out: list[dict[str, str]] = []
    for line in pending_text.splitlines():
        m = _PENDING_ROW.match(line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        body = " ".join(cells[1:])
        if "歪む場所" not in body and "宣言" not in body:
            continue
        out.append(
            {
                "id": cells[0],
                "topic": cells[1][:200],
                "recommendation": cells[3][:160] if len(cells) > 3 else "",
                "kind": "歪む場所" if "歪む場所" in body else "宣言",
            }
        )
    return out


#: 「その行が検証テストの実測を語っている」と読める語(**当てずっぽうの引用を避けるため**)。
_EVIDENCE_WORDS: tuple[str, ...] = ("実測", "一致", "合格", "passed", "JSD", "再現", "不一致")

#: 「まだ結果ではない」と分かる語(工程表・予定の行を弾く)。
_PLAN_WORDS: tuple[str, ...] = ("実装中", "追記予定", "予定", "サブ ", "着手")


def _evidence_score(line: str) -> float:
    """報告書の 1 行が「検証テストの実測」らしいかの点数(**自前の並べ替え規則**)。

    箇条書き(親が結果を書く形)を表の行より上に、数値のある行を上に置く。
    工程表・予定の行は下げる。文献根拠は無い(引用の当てずっぽうを減らす経験則)。
    """
    score = 0.0
    stripped = line.strip()
    if stripped.startswith(("-", "*")):
        score += 3.0
    if stripped.startswith("|"):
        score -= 1.0
    score += sum(1.0 for w in _EVIDENCE_WORDS if w in line)
    score += 1.5 if re.search(r"\d+\.\d+", line) else 0.0
    score -= sum(2.0 for w in _PLAN_WORDS if w in line)
    return score


def collect_verification(report_texts: Mapping[str, str]) -> list[dict[str, Any]]:
    """T1-T9 の状態を受入報告(build-report-C*.md)の該当行から拾う(**報告の補助**)。

    ``T6`` のような短い token は誤爆しやすいので、**行頭・箇条書き頭・太字の直後**に
    現れ、かつ直後が区切り文字であるものだけを候補にし、``_evidence_score`` の高い行を
    採る(同点なら新しい工程の報告を優先)。根拠が見つからない行は**空欄のまま**
    (推測で埋めない)。
    """
    rows: list[dict[str, Any]] = []
    order = sorted(report_texts, reverse=True)
    for tid, item in VERIFICATION_TESTS:
        pat = re.compile(rf"(?:\*\*|^|[-・/\s(（\|])({re.escape(tid)})(?:[\s(（:：/・、。\|]|$)")
        best: tuple[float, int, str, str] | None = None
        for rank, name in enumerate(order):
            for line in report_texts[name].splitlines():
                if not pat.search(line) or not any(w in line for w in _EVIDENCE_WORDS):
                    continue
                cand = (_evidence_score(line), -rank, line.strip()[:240], name)
                if best is None or cand[:2] > best[:2]:
                    best = cand
        rows.append(
            {
                "id": tid,
                "item": item,
                "evidence": best[2] if best else "",
                "source": best[3] if best else "",
            }
        )
    return rows


# ------------------------------------------------------------------ 組み立て
def _load(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return None


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build(
    *,
    world_dir: Path = WORLD_DIR,
    bench_dir: Path = ROOT / "docs" / "bench",
    accept_path: str | Path | None = None,
    ablation_results: Sequence[str | Path] = (),
    root: Path = ROOT,
) -> dict[str, Any]:
    """計器盤の payload(**入力が欠けても落ちない**)。"""
    manifest = _load(world_dir / "build_manifest.json")
    wc = _load(world_dir / "wc_index.json")
    w16 = _load(world_dir / "w16_gates.json")
    w17 = _load(world_dir / "w17_gates.json")
    fmt = _load(bench_dir / "c6_day2" / "format_role_rates.json") or _load(
        bench_dir / "c6" / "format_role_rates.json"
    )
    metric_b = _load(bench_dir / "c6" / "metric_b_rerun.json")
    ablation1 = _load(bench_dir / "c6" / "ablation1_fixed_vs_ranking.json")
    accept = _load(accept_path)
    results = [r for r in (_load(p) for p in ablation_results) if r]
    reports = {
        p.name: _text(p) for p in sorted((root / "docs" / "ops").glob("build-report-C*.md"))
    }
    return {
        "schema": "shibuya.tools.c8/dashboard/1",
        "faces": {
            "face1_calibration": {
                "gate": False,
                "build_gates": collect_build_gates(manifest),
                "coverage": collect_coverage(wc),
                "calibration": collect_calibration(w16, w17),
                "quality": collect_quality(fmt, metric_b, ablation1),
                "ablations": collect_ablations(c8lib.load_ablations(), results),
                "sensitivity": collect_sensitivity(c8lib.load_sensitivity()),
                "verification": collect_verification(reports),
            },
            "face2_holdout": {"gate": True, **collect_holdout(accept)},
            "face3_ops": {"gate": False, **collect_ops(accept)},
        },
        "distortions": collect_distortions(_text(root / "PENDING.md")),
        "inputs": {
            "build_manifest": bool(manifest),
            "wc_index": bool(wc),
            "w16_gates": bool(w16),
            "w17_gates": bool(w17),
            "format_role_rates": bool(fmt),
            "metric_b": bool(metric_b),
            "ablation1": bool(ablation1),
            "c7_accept": bool(accept),
            "ablation_results": len(results),
            "build_reports": sorted(reports),
        },
    }


def render(payload: Mapping[str, Any]) -> str:
    """payload → 計器盤 1 枚(**純関数**)。"""
    f = payload["faces"]
    f1, f2, f3 = f["face1_calibration"], f["face2_holdout"], f["face3_ops"]
    md: list[str] = [
        "# 忠実度計器盤(R14 G-1 の3面)",
        "",
        "> **ゲート(合否)は面2のみ**。面1は報告のみ(良くて当たり前)、面3は症状だけを赤にする。",
        "> 面1・面2 の乖離は「原因」であって赤にしない(観察)。"
        "面2 は**落ちたら不合格・通っても合格とは言わない**(SBC の片側性)。",
        "",
        "## 面2 holdout(唯一のゲート・判定はアンサンブル単位)",
        "",
    ]
    imp = f2.get("implausibility", {})
    md += [
        c8lib.markdown_table(
            ["項目", "値"],
            [
                ["形状5指標", " / ".join(f2.get("metrics", ()))],
                ["照合", c8lib.fmt((f2.get("holdout_row") or {}).get("measured"))],
                ["開封記録(manifest)", c8lib.fmt((f2.get("seal_row") or {}).get("measured"))],
                ["事前登録(k\\*)", f2.get("prereg_status")],
                ["実行不能度 I_M", c8lib.fmt(imp.get("I_M"))],
                ["合格線", imp.get("gate")],
            ],
        ),
        "",
        f"> {imp.get('note')}",
        "",
        "## 面3 運用(症状のみ赤)",
        "",
    ]
    if f3.get("rows"):
        md += [
            c8lib.markdown_table(
                ["行", "項目", "実測", "上限/期待", "判定", "備考"],
                [
                    [
                        r["id"], r["item"], c8lib.fmt(r["measured"]), c8lib.fmt(r["limit"]),
                        "—" if r["judge"] is None else ("PASS" if r["judge"] else "**FAIL**"),
                        str(r.get("note", ""))[:80],
                    ]
                    for r in f3["rows"]
                ],
            ),
            "",
            f"- 赤 {f3['n_red']} 件 {f3['red_ids']}",
        ]
    else:
        md += [
            "受入表(`tools/c7/c7_accept`)の出力が渡されていない=**未測定**。宣言値だけ並べる。",
            "",
            c8lib.markdown_table(
                ["行", "項目", "宣言"],
                [
                    [rid, (row or {}).get("item", "—"), str((row or {}).get("declared", "—"))[:90]]
                    for rid, row in f3.get("budget_declared", {}).items()
                ],
            ),
        ]
    md += ["", f"> {f3.get('alarm_rule')}", "", "## 面1 較正(報告のみ)", "", "### 構築ゲート W0-W20", ""]
    bg = f1["build_gates"]
    if bg.get("available"):
        md += [
            c8lib.markdown_table(
                ["段階", "ゲート数", "不合格", "不合格の名前", "expedient"],
                [
                    [s["stage"], s["n_gates"], s["n_fail"], ", ".join(s["failing"]) or "—", s["n_expedients"]]
                    for s in bg["stages"]
                ],
            ),
            "",
            f"- build_hash `{str(bg.get('build_hash'))[:16]}…` ・ゲート {bg['n_gates']} 本中 **不合格 {bg['n_fail']}**"
            f" ・expedient {bg['n_expedients']} 行",
        ]
    else:
        md.append("build_manifest.json が無い=**未測定**。")
    cov = f1["coverage"]
    md += ["", "### 世界被覆指標(5値ベクトル+X+孤児・加重和にしない)", ""]
    if cov.get("available"):
        md += [
            c8lib.markdown_table(
                ["C", "C_quantified", "Q", "D", "V", "R", "X(過剰)", "孤児", "カタログ"],
                [
                    [
                        c8lib.fmt(cov["C"], 3), c8lib.fmt(cov["C_quantified"], 3), c8lib.fmt(cov["Q"], 3),
                        c8lib.fmt(cov["D"], 3), c8lib.fmt(cov["V"], 3), c8lib.fmt(cov["R"], 3),
                        c8lib.fmt(cov["X"], 4), cov["orphans"],
                        f"{cov['catalog_version']} `{cov['catalog_sha16']}`",
                    ]
                ],
            ),
            "",
            f"- ゲートは **WC-5(過剰)/WC-6(孤児)のみ**。WC-6={c8lib.fmt(cov.get('gate_wc6'))}"
            f"(孤児 {cov['orphans']} 件)・WC-5={cov.get('gate_wc5')}・死蔵候補 {cov['dead_stock_candidates']} 件。",
        ]
    else:
        md.append("wc_index.json が無い=**未測定**。")
    md += ["", "### 較正アンカー(合否線なし)", ""]
    md.append(
        c8lib.markdown_table(
            ["行", "項目", "実測", "参考帯"],
            [[r["id"], r["item"], c8lib.fmt(r["value"], 6), c8lib.fmt(r["limit"], 6)] for r in f1["calibration"]],
        )
        if f1["calibration"]
        else "w16_gates/w17_gates が無い=**未測定**。"
    )
    q = f1["quality"]
    md += ["", "### 書式・役割語率・指標 B・ablation ①", ""]
    rows = []
    if "format" in q:
        fm = q["format"]
        rows += [
            ["書式エラー率(実効)", c8lib.fmt(fm["format_error_rate"]), f"≤{c8lib.fmt(fm['gate'],2)}", c8lib.fmt(fm["ok"])],
            ["書式エラー率(厳密)", c8lib.fmt(fm["format_error_rate_strict"]), f"≤{c8lib.fmt(fm['gate'],2)}", c8lib.fmt(fm["ok_strict"])],
            ["役割語率", c8lib.fmt(fm["role_action_rate"]), "—", "—"],
            ["未定義率", c8lib.fmt(fm["undefined_rate"]), "—", "—"],
        ]
    if "metric_b" in q:
        mb = q["metric_b"]
        rows += [
            ["指標B Δ違反率", c8lib.fmt(mb["delta_violation_rate"]), f"|CI上限| ≤{c8lib.fmt(mb['violation_gate'],2)}", c8lib.fmt(mb["violation_ok"])],
            ["指標B 行動分布 JSD", c8lib.fmt(mb["jsd_bits"]), f"≤帰無95% {c8lib.fmt(mb['null_bootstrap_p95'])}", c8lib.fmt(mb["distribution_ok"])],
        ]
    if "ablation1" in q:
        ab = q["ablation1"]
        rows += [["ablation① 行動分布 JSD", c8lib.fmt(ab["jsd_bits"]), "§10.3「同等」(数値なし)", "—"]]
    md.append(
        c8lib.markdown_table(["指標", "実測", "合格線", "判定"], rows) if rows else "実測 JSON が無い=**未測定**。"
    )
    if "format" in q and q["format"].get("source"):
        md.append(f"\n- 出所: {q['format']['source']}(n={c8lib.fmt(q['format'].get('n'))})")
    ab = f1["ablations"]
    md += ["", "### ablation 第1陣 6 本(L2=20% 予約枠)", ""]
    md += [
        c8lib.markdown_table(
            ["§8", "id", "腕", "切替口", "実行", "行動分布 JSD", "帰無超え"],
            [
                [
                    r["index"], r["id"], str(r["name"])[:34],
                    "実装済" if r["switch_implemented"] else "**なし**",
                    c8lib.fmt(r["executed"]), c8lib.fmt(r["action_jsd"]), c8lib.fmt(r["exceeds_null"]),
                ]
                for r in ab["rows"]
            ],
        ),
        "",
        f"- 切替口のある腕 **{ab['n_ready']}/{ab['n_arms']}** ・実行済み {ab['n_executed']} ・"
        f"計画 GPU {c8lib.fmt(ab['gpu_hours_planned'], 2)} h / L2 枠 {c8lib.fmt(ab['l2_reserve_hours'], 1)} h",
    ]
    se = f1["sensitivity"]
    md += ["", "### expedient 感度試験", ""]
    md += [
        c8lib.markdown_table(
            ["id", "出典", "実行形", "状態", "JSD[bits]", "帰無95%", "判定"],
            [
                [
                    r["id"], r["design_anchor"], r["exec_form"],
                    "実行済" if r["status"] == "done" else "未実行",
                    c8lib.fmt(r["jsd_bits"]), c8lib.fmt(r["null_p95"]),
                    {"not_driving": "駆動していない", "needs_run": "ラン対照が要る"}.get(str(r["verdict"]), "—"),
                ]
                for r in se["rows"]
            ],
        ),
        "",
        f"- 台帳 {se['n_rows']} 行(実行済み {se['n_done']}・駆動していない {se['n_not_driving']}・"
        f"ラン対照が要る {se['n_needs_run']})+過程の感度試験 id {se['n_process_ablations']} 本。"
        f"build_manifest の expedient は {c8lib.fmt(se['n_build_manifest_expedients'])} 行=**宣言の穴**(親判断)。",
    ]
    md += ["", "### 検証テスト T1-T9(受入報告の該当行)", ""]
    md.append(
        c8lib.markdown_table(
            ["行", "項目", "根拠(報告書の行)", "出所"],
            [
                [r["id"], r["item"], (r["evidence"] or "—")[:110], r["source"] or "—"]
                for r in f1["verification"]
            ],
        )
    )
    md += ["", "## 「歪む場所」の宣言(PENDING より)", ""]
    md.append(
        c8lib.markdown_table(
            ["id", "種別", "内容", "推奨"],
            [
                [d["id"], d["kind"], d["topic"][:90], d["recommendation"][:60]]
                for d in payload["distortions"]
            ],
        )
        if payload["distortions"]
        else "PENDING.md から拾えず。"
    )
    md += ["", "## 入力の有無", "", c8lib.markdown_table(
        ["入力", "有無"],
        [
            [k, f"{len(v)} 件" if isinstance(v, list) else c8lib.fmt(v)]
            for k, v in payload["inputs"].items()
        ],
    )]
    return "\n".join(md)


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="忠実度計器盤(R14 G-1 の3面)を 1 枚にまとめる")
    ap.add_argument("--world", default=str(WORLD_DIR))
    ap.add_argument("--bench", default=str(ROOT / "docs" / "bench"))
    ap.add_argument("--accept", default="", help="tools/c7/c7_accept の出力 JSON")
    ap.add_argument("--ablation-result", action="append", default=[], help="tools/c8/ablation_runner の出力 JSON(複数可)")
    ap.add_argument("--out", default="docs/ops/dashboard")
    args = ap.parse_args(list(argv) if argv is not None else None)

    payload = build(
        world_dir=Path(args.world),
        bench_dir=Path(args.bench),
        accept_path=args.accept or None,
        ablation_results=args.ablation_result,
    )
    md = render(payload)
    paths = c8lib.write_outputs(args.out, "dashboard", payload, md)
    print(md)
    print(json.dumps({"out": paths}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
