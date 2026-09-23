# -*- coding: utf-8 -*-
"""図 9 — 看板(広告)の効果は呼数の上限を外しても残るか(AB6b 上限あり vs AB6c 無制限・第246)。

何を示すか
    (a) 看板あり腕に対する **購入シェアの差 Δ[pp]** を、上限あり(AB6b・seed 1/2)と無制限
    (AB6c・`--l4-scale 0`)で並べる。AD1 の線(±1 pp)と同構成 seed 差の帯を同じ軸に置く。
    (b) 会話の呼数 (c) 休憩シェア を、上限あり seed 1 と無制限で 4 腕ずつ並べる
    (会話・休憩の付随効果が上限の有無に依らず残る=文面の注意配分の効果、を見る)。

数値の出所(全て runner 出力 JSON・図は割り算しかしない)
    docs/bench/c8/ablation/ablation_AB6b-AD-NOTICE_s{N}.json(上限あり・在る seed ぶん)
    docs/bench/c8/ablation/ablation_AB6c-AD-NOTICE-UNCAPPED_s{N}.json(無制限・在る seed ぶん)
    購入シェア = action_counts["購入"] / n_texts。AD1 の線 = パターン台帳 第3封印行 S3/AD1。

例::

    python tools/fig/fig_ab6c_uncapped.py --out docs/bench/figures
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
from fig_ab6b_signage import AD1_LINE_PP, CURRENT_ARMS, CURRENT_BASE, share_pct, summarize_run  # noqa: E402

DEFAULT_OUT = "docs/bench/figures"
STEM = "fig9_ab6c_uncapped"
ABL_DIR = "docs/bench/c8/ablation"
CAPPED_PATH = f"{ABL_DIR}/ablation_AB6b-AD-NOTICE_s{{seed}}.json"
UNCAPPED_PATH = f"{ABL_DIR}/ablation_AB6c-AD-NOTICE-UNCAPPED_s{{seed}}.json"
SEEDS: tuple[int, ...] = (1, 2, 3)

#: 色は実体に付く: 上限あり=青(slot 1)・無制限=アクア(slot 3)・AD1 の線=赤(slot 8)。
COLOR_CAPPED = st.CAT[0]
COLOR_UNCAPPED = st.CAT[2]
COLOR_LINE = st.CAT[7]


def _load_doc(path: str | Path) -> dict[str, Any] | None:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _jsd_for(doc: Mapping[str, Any], tag: str) -> float | None:
    for c in doc.get("comparisons") or []:
        if c.get("tag") == tag:
            return c.get("action_jsd")
    return None


def _collect(group: str, path_tpl: str, seeds: Sequence[int]) -> tuple[list[dict[str, Any]], dict[int, float]]:
    runs: list[dict[str, Any]] = []
    base_buy: dict[int, float] = {}
    for seed in seeds:
        path = path_tpl.format(seed=seed)
        doc = _load_doc(path)
        if not doc:
            continue
        by = {r.get("tag"): r for r in doc.get("runs", [])}
        if CURRENT_BASE not in by:
            continue
        base = summarize_run(by[CURRENT_BASE])
        base_buy[int(seed)] = base["buy_pct"]
        for arm in CURRENT_ARMS:
            if arm["tag"] not in by:
                continue
            s = summarize_run(by[arm["tag"]])
            z = by[arm["tag"]].get("realized") or {}
            runs.append({"group": group, "seed": int(seed), "tag": arm["tag"], "ja": arm["ja"], "en": arm["en"],
                         "delta_buy_pp": round(s["buy_pct"] - base["buy_pct"], 4),
                         "delta_rest_pp": round(s["rest_pct"] - base["rest_pct"], 4),
                         "jsd": _jsd_for(doc, arm["tag"]), "path": st.rel(path),
                         "boarded": z.get("n_boarded"), "purchases": z.get("purchases"),
                         "revenue_yen": z.get("revenue_end"), "sessions": by[arm["tag"]].get("conversation_sessions"),
                         **s})
    return runs, base_buy


def load_ab6c(capped_path: str = CAPPED_PATH, uncapped_path: str = UNCAPPED_PATH,
              seeds: Sequence[int] = SEEDS) -> dict[str, Any]:
    """runner JSON 群 → 描画に要るデータ dict。"""
    capped, base_c = _collect("capped", capped_path, seeds)
    uncapped, base_u = _collect("uncapped", uncapped_path, seeds)
    if not uncapped:
        raise FileNotFoundError(f"AB6c の runner JSON が無い: {uncapped_path}")
    runs = capped + uncapped
    rows = [r for r in runs if r["tag"] != CURRENT_BASE]

    def _null(d: Mapping[int, float]) -> float | None:
        ks = sorted(d)
        return round(abs(d[ks[0]] - d[ks[1]]), 4) if len(ks) >= 2 else None

    return {"rows": rows, "runs": runs, "ad1_line_pp": AD1_LINE_PP,
            "null_seed_pp": {"capped": _null(base_c), "uncapped": _null(base_u)},
            "capped_seeds_found": sorted(base_c), "uncapped_seeds_found": sorted(base_u)}


# ---------------------------------------------------------------- 描画


def draw(data: Mapping[str, Any]):
    """データ dict → Figure。**ファイルを読まない**。"""
    import matplotlib.pyplot as plt

    st.use_style()
    rows = list(data["rows"])
    line = float(data["ad1_line_pp"])
    null_pp = data.get("null_seed_pp") or {}

    fig = plt.figure(figsize=(12.6, 6.6))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.1, 0.9], left=0.185, right=0.985,
                          top=0.885, bottom=0.225, wspace=0.30, hspace=0.60)
    ax = fig.add_subplot(gs[:, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 1])

    # ---- (a) Δ購入[pp] ----
    labels, vals, colors = [], [], []
    for r in rows:
        g = st.T("上限あり", "capped") if r["group"] == "capped" else st.T("無制限", "uncapped")
        labels.append(st.T(f"{g} seed {r['seed']}  {r['ja']}", f"{g} seed {r['seed']}  {r['en']}"))
        vals.append(float(r["delta_buy_pp"]))
        colors.append(COLOR_CAPPED if r["group"] == "capped" else COLOR_UNCAPPED)
    y = np.arange(len(rows), dtype=float)
    span = max([line * 1.55] + [abs(v) * 1.35 for v in vals])
    nb = null_pp.get("capped")
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
    ax.set_title(st.T("(a) 看板の購入効果: 上限あり vs 無制限", "(a) signage effect on buying: capped vs uncapped"),
                 fontsize=10, pad=6)
    ax.annotate(st.T(f"AD1 の線 ±{line:g} pp", f"AD1 line ±{line:g} pp"), xy=(line, -0.62), xytext=(3, 0),
                textcoords="offset points", fontsize=7.8, color=COLOR_LINE, ha="left", va="center",
                annotation_clip=False)
    if nb is not None:
        ax.annotate(st.T(f"seed 差 ±{nb:.2f} pp", f"seed-to-seed ±{nb:.2f} pp"),
                    xy=(0, -0.62), xytext=(0, 0), textcoords="offset points", fontsize=7.6,
                    color=st.INK2, ha="center", va="center", annotation_clip=False, zorder=6)
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLOR_CAPPED), plt.Rectangle((0, 0), 1, 1, color=COLOR_UNCAPPED)]
    ax.legend(handles, [st.T("上限あり(×1・7.4 呼/体/日)", "capped (x1, 7.4 calls/agent-day)"),
                        st.T("無制限(15.5 呼/体/日)", "uncapped (15.5 calls/agent-day)")],
              loc="lower left", handlelength=1.2, fontsize=8.0, borderaxespad=0.4)

    # ---- (b)(c) 4 腕ずつ・上限あり seed 1 と 無制限 seed 1 ----
    order = [a["tag"] for a in CURRENT_ARMS]
    def _first(group: str) -> list[dict[str, Any]]:
        seeds = [r["seed"] for r in data["runs"] if r["group"] == group]
        if not seeds:
            return []
        s0 = min(seeds)
        rs = [r for r in data["runs"] if r["group"] == group and r["seed"] == s0]
        rs.sort(key=lambda r: order.index(r["tag"]) if r["tag"] in order else 99)
        return rs
    cap, unc = _first("capped"), _first("uncapped")
    xs = np.arange(len(order))
    w = 0.38
    for axk, key, title, fmt, ylab in (
        (ax_b, "talk", "(b) 会話の呼数(seed 1)", lambda v: st.thousands(v), "呼"),
        (ax_c, "rest_pct", "(c) 休憩シェア(seed 1)", lambda v: f"{v:.2f}%", "%"),
    ):
        top = 0.0
        for off, rs, color in ((-w / 2, cap, COLOR_CAPPED), (w / 2, unc, COLOR_UNCAPPED)):
            if not rs:
                continue
            v = [float(r[key]) for r in rs]
            top = max(top, max(v))
            axk.bar(xs + off, v, width=w, color=color, edgecolor=st.SURFACE, linewidth=1.0, zorder=3)
            for xi, vi in zip(xs + off, v):
                axk.annotate(fmt(vi), xy=(xi, vi), xytext=(0, 3), textcoords="offset points", ha="center",
                             va="bottom", fontsize=7.6, color=st.INK)
        axk.set_xticks(xs)
        axk.set_xticklabels([st.T(a["ja"], a["en"]) for a in CURRENT_ARMS], fontsize=8.0)
        axk.set_ylim(0, (top or 1.0) * 1.28)
        axk.grid(axis="x", visible=False)
        axk.set_title(st.T(title, title), fontsize=10, pad=6)
        axk.set_ylabel(st.T(ylab, ylab))

    fig.suptitle(st.T("図9 看板(広告)の効果は呼数の上限を外しても残るか — 購入は 0・会話と休憩の付随効果は残る(AB6b / AB6c)",
                      "Fig.9 Does the signage effect survive removing the call cap? Buying: none. Conversation/rest side-effects: persist (AB6b / AB6c)"),
                 x=0.008, y=0.985, ha="left", va="top", fontsize=12, fontweight="bold", color=st.INK)
    nu = null_pp.get("uncapped")
    st.note(fig, [
        st.T("購入シェア = action_counts[購入] / n_texts(runner 出力)。AD1 の線 = パターン台帳 第3封印行 S3/AD1「広告全消去で絶対 1pp 未満」。帯 = 上限あり腕の seed 1 vs 2 の購入差"
             + (f"・無制限は {nu:.2f} pp" if nu is not None else "(無制限は seed 1 のみ)") + "。",
             "buy share = action_counts[buy] / n_texts. AD1 line = pattern ledger S3/AD1. band = seed-to-seed buy difference of the capped signage-on arm."),
        st.T("上限あり = AB6b(5,000 体×1 日・L4 ×1・呼 ≈36,900/腕)。無制限 = AB6c(同構成に --l4-scale 0 を重ねる・呼 ≈77,300/腕・繰り延べ 0)。同じ seed・同じ看板ゲート。",
             "capped = AB6b (5,000 agents x 1 day, L4 x1, ~36,900 calls/arm). uncapped = AB6c (same + --l4-scale 0, ~77,300 calls/arm, no deferrals)."),
        st.T("(b)(c) は seed 1 の 4 腕を上限あり/無制限で並べる。無制限では購入シェアの水準自体が 43.8→36.4% に下がる(起床構成の差・図8)。数値は fig9_ab6c_uncapped.json。出典 ab6c_s1_parent_report.md。",
             "(b)(c): the four seed-1 arms, capped vs uncapped. numbers: fig9_ab6c_uncapped.json."),
    ])
    return fig


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="図9: 看板の効果は上限を外しても残るか(AB6b / AB6c)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    data = load_ab6c()
    fig = draw(data)
    paths = st.save(fig, args.out, STEM)
    payload = {
        "schema": "shibuya.tools.fig/ab6c_uncapped/1",
        "figure": STEM,
        "what": "看板あり腕に対する購入シェア差[pp]を 上限あり(AB6b seed 1/2)と無制限(AB6c)で並べ、会話・休憩の付随効果を 4 腕ずつ比べる。",
        "ad1_line_pp": data["ad1_line_pp"],
        "null_seed_pp": data["null_seed_pp"],
        "capped_seeds_found": data["capped_seeds_found"],
        "uncapped_seeds_found": data["uncapped_seeds_found"],
        "rows": data["rows"],
        "runs": data["runs"],
        "outputs": paths,
    }
    payload["sidecar"] = st.write_sidecar(args.out, STEM, payload)
    print(json.dumps({"outputs": paths, "sidecar": payload["sidecar"],
                      "rows": [(r["group"], r["seed"], r["tag"], r["delta_buy_pp"]) for r in data["rows"]]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
