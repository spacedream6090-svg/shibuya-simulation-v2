# -*- coding: utf-8 -*-
"""図 6 — 看板(広告)を消す/見る頻度を下げると購入はどれだけ動くか(AB6 09-10 と AB6b 09-17)。

何を示すか
    (a) 看板ありの腕に対する **購入シェアの差 Δ[pp]** を、09-10 の広告ゼロ腕(AB6-AD-ZERO・
    C7 期のコード・seed 1/2)と 09-17 の注視ゲート腕(AB6b-AD-NOTICE・seed 1〜)で並べる。
    正=看板を消す/減らすと購入が**増える**。AD1 の線(±1 pp)と、同構成で seed だけ違う
    2 ランの購入差(帰無の幅)を同じ軸に置く。(b) 会話の呼数、(c) 休憩シェア(09-17 の 4 腕)。

数値の出所(全て runner 出力 JSON・図は割り算しかしない)
    docs/bench/c8/ablation/ablation_AB6-AD-ZERO{,_seed2}.json(09-10)
    docs/bench/c8/ablation/ablation_AB6b-AD-NOTICE_s{N}.json(09-17・在るぶんだけ)
    購入シェア = action_counts["購入"] / n_texts。AD1 の線 = パターン台帳 第3封印行 S3/AD1
    「広告全消去で絶対 1pp 未満」。帰無の幅 = 看板あり腕の seed 1 vs seed 2 の購入差。

例::

    python tools/fig/fig_ab6b_signage.py --out docs/bench/figures
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

_HERE = Path(__file__).resolve().parent
REPO_ROOT = _HERE.parents[1]
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import _style as st  # noqa: E402

DEFAULT_OUT = "docs/bench/figures"
STEM = "fig6_ab6b_signage"
ABL_DIR = "docs/bench/c8/ablation"

#: AD1 の線[pp](パターン台帳 第3封印行 S3/AD1「広告全消去で絶対 1pp 未満」)。
AD1_LINE_PP = 1.0

#: 09-10 の広告ゼロ腕(C7 期のコード)。baseline=signage_on / 対照=signage_off。
LEGACY: tuple[dict[str, Any], ...] = (
    {"path": f"{ABL_DIR}/ablation_AB6-AD-ZERO.json", "seed": 1, "code": "09-10(C7 期)"},
    {"path": f"{ABL_DIR}/ablation_AB6-AD-ZERO_seed2.json", "seed": 2, "code": "09-10(C7 期)"},
)
LEGACY_BASE = "signage_on"
LEGACY_ARMS: tuple[dict[str, str], ...] = (
    {"tag": "signage_off", "ja": "看板なし", "en": "no signage"},
)

#: 09-17 の注視ゲート腕(HEAD 667ceb5)。baseline=p_see_1_00。seed は在るぶんだけ読む。
CURRENT_PATH = f"{ABL_DIR}/ablation_AB6b-AD-NOTICE_s{{seed}}.json"
CURRENT_SEEDS: tuple[int, ...] = (1, 2, 3)
CURRENT_BASE = "p_see_1_00"
CURRENT_ARMS: tuple[dict[str, str], ...] = (
    {"tag": "p_see_1_00", "ja": "現行(p_see 1.0)", "en": "current (p_see 1.0)"},
    {"tag": "ad_zero", "ja": "看板なし", "en": "no signage"},
    {"tag": "p_see_0_30", "ja": "p_see 0.30", "en": "p_see 0.30"},
    {"tag": "p_see_0_14", "ja": "p_see 0.14", "en": "p_see 0.14"},
)

#: 色は実体に付く: 現行コード(09-17)=青 / C7 期(09-10)=灰 / AD1 の線=赤(slot 8)。
COLOR_CURRENT = st.CAT[0]
COLOR_LEGACY = st.MUTED
COLOR_LINE = st.CAT[7]


def share_pct(run: Mapping[str, Any], word: str) -> float:
    """行動語のシェア[%] = action_counts[word] / n_texts × 100。**純関数**。"""
    n = float(run.get("n_texts") or 0)
    if n <= 0:
        return 0.0
    return 100.0 * float((run.get("action_counts") or {}).get(word, 0)) / n


def summarize_run(run: Mapping[str, Any]) -> dict[str, Any]:
    """runner の 1 ラン → 図に要る数だけ。**純関数**。"""
    gate = run.get("signage_gate") or {}
    return {
        "n_texts": int(run.get("n_texts") or 0),
        "llm_calls": int(run.get("llm_calls") or 0),
        "buy_pct": round(share_pct(run, "購入"), 4),
        "rest_pct": round(share_pct(run, "休憩"), 4),
        "move_pct": round(share_pct(run, "移動"), 4),
        "wait_pct": round(share_pct(run, "待機"), 4),
        "ride": int((run.get("action_counts") or {}).get("乗車", 0)),
        "talk": int((run.get("action_counts") or {}).get("会話", 0)),
        "prompt_tokens_mean": run.get("prompt_tokens_mean"),
        "signage_p_see": run.get("signage_p_see"),
        "shown_rate": gate.get("shown_rate"),
        "gate_draws": gate.get("draws"),
        "conserved": run.get("conserved"),
    }


def _load_doc(path: str | Path) -> dict[str, Any] | None:
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _jsd_for(doc: Mapping[str, Any], tag: str) -> float | None:
    for c in doc.get("comparisons") or []:
        if c.get("tag") == tag:
            return c.get("action_jsd")
    return None


def load_ab6b(legacy: Sequence[Mapping[str, Any]] = LEGACY,
              current_path: str = CURRENT_PATH,
              current_seeds: Sequence[int] = CURRENT_SEEDS) -> dict[str, Any]:
    """runner JSON 群 → 描画に要るデータ dict。"""
    rows: list[dict[str, Any]] = []          # (a) の行(対照腕だけ)
    runs: list[dict[str, Any]] = []          # 表用(baseline も含む全ラン)
    base_by_group: dict[str, dict[int, float]] = {"legacy": {}, "current": {}}

    for spec in legacy:
        doc = _load_doc(spec["path"])
        if not doc:
            continue
        by = {r.get("tag"): r for r in doc.get("runs", [])}
        base = summarize_run(by[LEGACY_BASE])
        base_by_group["legacy"][int(spec["seed"])] = base["buy_pct"]
        runs.append({"group": "legacy", "seed": int(spec["seed"]), "code": spec["code"], "tag": LEGACY_BASE,
                     "ja": "看板あり", "en": "signage on", "delta_buy_pp": 0.0, "jsd": None,
                     "path": st.rel(spec["path"]), **base})
        for arm in LEGACY_ARMS:
            s = summarize_run(by[arm["tag"]])
            row = {"group": "legacy", "seed": int(spec["seed"]), "code": spec["code"], "tag": arm["tag"],
                   "ja": arm["ja"], "en": arm["en"], "delta_buy_pp": round(s["buy_pct"] - base["buy_pct"], 4),
                   "jsd": _jsd_for(doc, arm["tag"]), "path": st.rel(spec["path"]), **s}
            rows.append(row)
            runs.append(row)

    for seed in current_seeds:
        path = current_path.format(seed=seed)
        doc = _load_doc(path)
        if not doc:
            continue
        by = {r.get("tag"): r for r in doc.get("runs", [])}
        base = summarize_run(by[CURRENT_BASE])
        base_by_group["current"][int(seed)] = base["buy_pct"]
        for arm in CURRENT_ARMS:
            s = summarize_run(by[arm["tag"]])
            row = {"group": "current", "seed": int(seed), "code": "09-17(HEAD 667ceb5)", "tag": arm["tag"],
                   "ja": arm["ja"], "en": arm["en"], "delta_buy_pp": round(s["buy_pct"] - base["buy_pct"], 4),
                   "jsd": _jsd_for(doc, arm["tag"]), "path": st.rel(path), **s}
            runs.append(row)
            if arm["tag"] != CURRENT_BASE:
                rows.append(row)

    null_pp: dict[str, float | None] = {}
    for g, d in base_by_group.items():
        seeds = sorted(d)
        null_pp[g] = round(abs(d[seeds[0]] - d[seeds[1]]), 4) if len(seeds) >= 2 else None
    return {
        "rows": rows,
        "runs": runs,
        "ad1_line_pp": AD1_LINE_PP,
        "null_seed_pp": null_pp,
        "current_seeds_found": sorted(base_by_group["current"]),
    }


# ---------------------------------------------------------------- 描画


def draw(data: Mapping[str, Any]):
    """データ dict → Figure。**ファイルを読まない**。"""
    import matplotlib.pyplot as plt

    st.use_style()
    rows = list(data["rows"])
    line = float(data["ad1_line_pp"])
    null_pp = data.get("null_seed_pp") or {}

    fig = plt.figure(figsize=(12.6, 6.4))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.15, 0.85], left=0.19, right=0.985,
                          top=0.885, bottom=0.215, wspace=0.30, hspace=0.55)
    ax = fig.add_subplot(gs[:, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 1])

    # ---- (a) Δ購入[pp](横棒・発散) ----
    labels = []
    for r in rows:
        code = "09-10" if r["group"] == "legacy" else "09-17"
        labels.append(st.T(f"{code} seed {r['seed']}  {r['ja']}", f"{code} seed {r['seed']}  {r['en']}"))
    y = np.arange(len(rows), dtype=float)
    vals = [float(r["delta_buy_pp"]) for r in rows]
    colors = [COLOR_LEGACY if r["group"] == "legacy" else COLOR_CURRENT for r in rows]
    span = max([line * 1.55] + [abs(v) * 1.35 for v in vals])
    nb = null_pp.get("legacy")
    if nb is not None:
        ax.axvspan(-nb, nb, color=st.GRID, zorder=1)
    ax.axvline(0, color=st.AXIS, linewidth=0.9, zorder=2)
    for x in (-line, line):
        ax.axvline(x, color=COLOR_LINE, linewidth=1.2, zorder=2)
    ax.barh(y, vals, height=0.62, color=colors, edgecolor=st.SURFACE, linewidth=1.0, zorder=3)
    for yi, v in zip(y, vals):
        ax.annotate(f"{v:+.2f}", xy=(v, yi), xytext=(5 if v >= 0 else -5, 0), textcoords="offset points",
                    va="center", ha="left" if v >= 0 else "right", fontsize=8.4, color=st.INK, zorder=5)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(-span, span)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel(st.T("購入シェアの差 Δ [pp](対 看板あり・正=看板を消す/減らすと購入が増える)",
                       "Δ buy share [pp] vs signage-on (positive = buying rises when signage is removed/reduced)"))
    ax.set_title(st.T("(a) 看板を消す/見る頻度を下げたときの購入の動き", "(a) buy share vs signage arm"),
                 fontsize=10, pad=6)
    ax.annotate(st.T(f"AD1 の線 ±{line:g} pp", f"AD1 line ±{line:g} pp"), xy=(line, -0.62), xytext=(3, 0),
                textcoords="offset points", fontsize=7.8, color=COLOR_LINE, ha="left", va="center",
                annotation_clip=False)
    if nb is not None:
        ax.annotate(st.T(f"seed 差 ±{nb:.2f} pp", f"seed-to-seed ±{nb:.2f} pp"),
                    xy=(0, (len(rows) - 1) / 2), xytext=(0, 0), textcoords="offset points", fontsize=7.6,
                    color=st.INK2, ha="center", va="center", rotation=90, zorder=6)
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLOR_LEGACY), plt.Rectangle((0, 0), 1, 1, color=COLOR_CURRENT)]
    ax.legend(handles, [st.T("09-10 の腕(C7 期のコード・看板なし)", "09-10 arm (C7-era code, no signage)"),
                        st.T("09-17 の腕(現行コード・注視ゲート)", "09-17 arm (current code, gaze gate)")],
              loc="lower left", handlelength=1.4)

    # ---- (b)(c) 09-17 seed 1 の 4 腕 ----
    cur = [r for r in data["runs"] if r["group"] == "current" and r["seed"] == min(data["current_seeds_found"] or [1])]
    order = [a["tag"] for a in CURRENT_ARMS]
    cur.sort(key=lambda r: order.index(r["tag"]) if r["tag"] in order else 99)
    xl = [st.T(r["ja"], r["en"]) for r in cur]
    xs = np.arange(len(cur))
    for axk, key, title, fmt, ylab in (
        (ax_b, "talk", "(b) 会話の呼数(09-17 seed 1)", lambda v: st.thousands(v), "呼"),
        (ax_c, "rest_pct", "(c) 休憩シェア(09-17 seed 1)", lambda v: f"{v:.2f}%", "%"),
    ):
        vals_k = [float(r[key]) for r in cur]
        axk.bar(xs, vals_k, width=0.62, color=COLOR_CURRENT, edgecolor=st.SURFACE, linewidth=1.0, zorder=3)
        for xi, v in zip(xs, vals_k):
            axk.annotate(fmt(v), xy=(xi, v), xytext=(0, 3), textcoords="offset points", ha="center",
                         va="bottom", fontsize=8.2, color=st.INK)
        axk.set_xticks(xs)
        axk.set_xticklabels(xl, fontsize=8.2)
        axk.set_ylim(0, (max(vals_k) if vals_k else 1) * 1.28)
        axk.grid(axis="x", visible=False)
        axk.set_title(st.T(title, title), fontsize=10, pad=6)
        axk.set_ylabel(st.T(ylab, ylab))
    for xi, r in zip(xs, cur):
        sr = r.get("shown_rate")
        if isinstance(sr, (int, float)) and r.get("gate_draws"):
            ax_c.annotate(st.T(f"実測注視率 {sr:.3f}", f"observed {sr:.3f}"), xy=(xi, 0), xytext=(0, -26),
                          textcoords="offset points", ha="center", va="top", fontsize=7.4, color=st.INK2,
                          annotation_clip=False)

    fig.suptitle(st.T("図6 看板(広告)は購入をどれだけ動かすか — 09-10 と 09-17 で符号が逆(AB6-AD-ZERO / AB6b-AD-NOTICE)",
                      "Fig.6 How much does signage move buying? Sign flipped between 09-10 and 09-17 (AB6 / AB6b)"),
                 x=0.008, y=0.985, ha="left", va="top", fontsize=12, fontweight="bold", color=st.INK)

    cur_null = null_pp.get("current")
    st.note(fig, [
        st.T("購入シェア = action_counts[購入] / n_texts(runner 出力)。AD1 の線 = パターン台帳 第3封印行 S3/AD1「広告全消去で絶対 1pp 未満」。"
             "帯 = 看板あり腕の seed 1 vs 2 の購入差" + (f"(09-17 は {cur_null:.2f} pp)" if cur_null is not None else "") + "。",
             "buy share = action_counts[buy] / n_texts (runner output). AD1 line = pattern ledger S3/AD1 (<1 pp under ad removal). "
             "band = seed-to-seed buy difference of the signage-on arm."),
        st.T("09-10 = 5,000 体×1 日・呼 50,000/腕・C7 期のコード(計画実行層・W17 v2・C9・第214 修正の前)。"
             "09-17 = 同規模・呼 ≈36,900/腕・HEAD 667ceb5(注視ゲート --signage-p-see・既定 1.0 は現行と 1 バイト同じ)。",
             "09-10 = 5,000 agents x 1 day, 50,000 calls/arm, C7-era code. 09-17 = same scale, ~36,900 calls/arm, HEAD 667ceb5 (gaze gate)."),
        st.T("(b)(c) は 09-17 seed 1 の 4 腕。注視ゲートの実測注視率は 抽選 shown/draws。数値は fig6_ab6b_signage.json。出典 ab6b_s1_parent_report.md。",
             "(b)(c): the four 09-17 arms (seed 1). observed gaze rate = shown/draws. numbers: fig6_ab6b_signage.json."),
    ])
    return fig


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="図6: 看板の購入効果(AB6 09-10 / AB6b 09-17)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    data = load_ab6b()
    fig = draw(data)
    paths = st.save(fig, args.out, STEM)
    payload = {
        "schema": "shibuya.tools.fig/ab6b_signage/1",
        "figure": STEM,
        "what": "看板あり腕に対する購入シェア差[pp](09-10 AB6-AD-ZERO seed 1/2・09-17 AB6b-AD-NOTICE seed 在るぶん)と 09-17 の会話・休憩。",
        "ad1_line_pp": data["ad1_line_pp"],
        "null_seed_pp": data["null_seed_pp"],
        "current_seeds_found": data["current_seeds_found"],
        "rows": data["rows"],
        "runs": data["runs"],
        "outputs": paths,
    }
    payload["sidecar"] = st.write_sidecar(args.out, STEM, payload)
    print(json.dumps({"outputs": paths, "sidecar": payload["sidecar"],
                      "rows": [(r["code"], r["seed"], r["tag"], r["delta_buy_pp"]) for r in data["rows"]],
                      "null_seed_pp": data["null_seed_pp"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
