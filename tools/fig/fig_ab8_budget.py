# -*- coding: utf-8 -*-
"""図 8 — LLM 呼数の予算(L4)を動かすと世界で起きることはどう変わるか(AB8-L4-SCALE・第247)。

何を示すか
    同構成(5,000 体×1 日・実 LLM・seed 1)で L4 の倍率を ×0.5 / ×1(現行)/ ×2 / 無制限にした
    4 ランを、横軸=**実際の呼/体/日**に並べる。(a) 実現した購入/体/日 (b) 売上 円/体
    (c) 実現した乗車/体/日 (d) 会話セッション/日 (e) 購入シェア[%](LLM の選択)(f) 購入/千呼。
    実現量(a〜d)は世界で起きたこと、(e) は LLM が選んだ割合、(f) は呼あたりの効率。

数値の出所(全て runner 出力 JSON・図は割り算しかしない)
    docs/bench/c8/ablation/ablation_AB8-L4-SCALE_s{N}.json(在る seed ぶん・図は最小 seed)
    realized.* / llm_calls / action_counts["購入"] / n_texts / scale.agents。

例::

    python tools/fig/fig_ab8_budget.py --out docs/bench/figures
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
STEM = "fig8_ab8_budget"
ABL_DIR = "docs/bench/c8/ablation"
PATH = f"{ABL_DIR}/ablation_AB8-L4-SCALE_s{{seed}}.json"
SEEDS: tuple[int, ...] = (1, 2, 3)

#: 腕の並び(予算の昇順)。
ARMS: tuple[dict[str, Any], ...] = (
    {"tag": "l4_x0.5", "ja": "×0.5", "en": "x0.5", "scale": 0.5},
    {"tag": "l4_x1", "ja": "×1(現行)", "en": "x1 (current)", "scale": 1.0},
    {"tag": "l4_x2", "ja": "×2", "en": "x2", "scale": 2.0},
    {"tag": "l4_unlimited", "ja": "無制限", "en": "unlimited", "scale": 0.0},
)
CURRENT_TAG = "l4_x1"

#: 色: 実現量=青(slot 1)・LLM の選択=灰・現行の点=赤の縁(slot 8)。
COLOR_REAL = st.CAT[0]
COLOR_CHOICE = st.MUTED
COLOR_CURRENT = st.CAT[7]


def summarize_run(run: Mapping[str, Any], n_agents: int) -> dict[str, Any]:
    """runner の 1 ラン → 図に要る数だけ。**純関数**(割り算だけ)。"""
    z = run.get("realized") or {}
    calls = float(run.get("llm_calls") or 0)
    n_texts = float(run.get("n_texts") or 0)
    buy_choice = float((run.get("action_counts") or {}).get("購入", 0))
    n = float(max(1, n_agents))
    return {
        "llm_calls": int(calls),
        "calls_per_agent_day": round(calls / n, 4),
        "budget_per_tick": run.get("budget_per_tick"),
        "l4_scale": run.get("l4_scale"),
        "purchases": int(z.get("purchases") or 0),
        "purchases_per_agent_day": round(float(z.get("purchases") or 0) / n, 4),
        "purchases_per_1k_calls": round(1000.0 * float(z.get("purchases") or 0) / calls, 2) if calls > 0 else None,
        "revenue_yen": int(z.get("revenue_end") or 0),
        "revenue_yen_per_agent": round(float(z.get("revenue_end") or 0) / n, 2),
        "boarded": int(z.get("n_boarded") or 0),
        "boarded_per_agent_day": round(float(z.get("n_boarded") or 0) / n, 4),
        "conversation_sessions": int(run.get("conversation_sessions") or 0),
        "buy_share_pct": round(100.0 * buy_choice / n_texts, 4) if n_texts > 0 else None,
        "deferred": int((run.get("diagnostics_day") or {}).get("deferred") or 0),
        "conserved": run.get("conserved"),
        "final_hash": (run.get("final_hash") or "")[:16],
    }


def _load_doc(path: str | Path) -> dict[str, Any] | None:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def load_ab8(path_tpl: str = PATH, seeds: Sequence[int] = SEEDS) -> dict[str, Any]:
    """runner JSON 群 → 描画に要るデータ dict(在る seed を全部読み、図は最小 seed)。"""
    by_seed: dict[int, list[dict[str, Any]]] = {}
    for seed in seeds:
        path = path_tpl.format(seed=seed)
        doc = _load_doc(path)
        if not doc:
            continue
        n_agents = int((doc.get("scale") or {}).get("agents") or 0)
        by = {r.get("tag"): r for r in doc.get("runs", [])}
        rows = []
        for arm in ARMS:
            if arm["tag"] not in by:
                continue
            rows.append({"seed": int(seed), "tag": arm["tag"], "ja": arm["ja"], "en": arm["en"],
                         "scale": arm["scale"], "path": st.rel(path), "n_agents": n_agents,
                         **summarize_run(by[arm["tag"]], n_agents)})
        if rows:
            by_seed[int(seed)] = rows
    if not by_seed:
        raise FileNotFoundError(f"AB8 の runner JSON が無い: {path_tpl}")
    first = min(by_seed)
    return {"rows": by_seed[first], "seed": first, "seeds_found": sorted(by_seed),
            "all_rows": [r for s in sorted(by_seed) for r in by_seed[s]]}


# ---------------------------------------------------------------- 描画

PANELS: tuple[dict[str, Any], ...] = (
    {"key": "purchases_per_agent_day", "ja": "(a) 実現した購入 / 体 / 日", "en": "(a) realized purchases / agent / day",
     "fmt": lambda v: f"{v:.2f}", "ylab": ("件/体/日", "per agent-day"), "kind": "real"},
    {"key": "revenue_yen_per_agent", "ja": "(b) 売上 円 / 体", "en": "(b) sales yen / agent",
     "fmt": lambda v: st.thousands(v), "ylab": ("円/体", "yen/agent"), "kind": "real"},
    {"key": "boarded_per_agent_day", "ja": "(c) 実現した乗車 / 体 / 日", "en": "(c) realized boardings / agent / day",
     "fmt": lambda v: f"{v:.3f}", "ylab": ("回/体/日", "per agent-day"), "kind": "real"},
    {"key": "conversation_sessions", "ja": "(d) 会話セッション / 日", "en": "(d) conversation sessions / day",
     "fmt": lambda v: f"{v:.0f}", "ylab": ("回/日(5,000 体)", "per day (5,000 agents)"), "kind": "real"},
    {"key": "buy_share_pct", "ja": "(e) 購入シェア[%](LLM の選択)", "en": "(e) buy share [%] (LLM choices)",
     "fmt": lambda v: f"{v:.1f}%", "ylab": ("%", "%"), "kind": "choice"},
    {"key": "purchases_per_1k_calls", "ja": "(f) 購入 / 千呼(効率)", "en": "(f) purchases per 1,000 calls",
     "fmt": lambda v: f"{v:.0f}", "ylab": ("件/千呼", "per 1k calls"), "kind": "choice"},
)


def draw(data: Mapping[str, Any]):
    """データ dict → Figure。**ファイルを読まない**。"""
    import matplotlib.pyplot as plt

    st.use_style()
    rows = list(data["rows"])
    seed = data.get("seed", 1)
    xs = np.array([float(r["calls_per_agent_day"]) for r in rows])
    cur_i = next((i for i, r in enumerate(rows) if r["tag"] == CURRENT_TAG), None)

    fig = plt.figure(figsize=(12.6, 7.2))
    gs = fig.add_gridspec(2, 3, left=0.065, right=0.985, top=0.875, bottom=0.235, wspace=0.34, hspace=0.62)
    for k, spec in enumerate(PANELS):
        ax = fig.add_subplot(gs[k // 3, k % 3])
        ys = np.array([float(r[spec["key"]] if r[spec["key"]] is not None else np.nan) for r in rows])
        color = COLOR_REAL if spec["kind"] == "real" else COLOR_CHOICE
        ax.plot(xs, ys, color=color, linewidth=1.6, zorder=3)
        ax.scatter(xs, ys, s=34, color=color, edgecolor=st.SURFACE, linewidth=0.8, zorder=4)
        if cur_i is not None:
            ax.scatter([xs[cur_i]], [ys[cur_i]], s=110, facecolor="none", edgecolor=COLOR_CURRENT,
                       linewidth=1.4, zorder=5)
        for i, (x, y, r) in enumerate(zip(xs, ys, rows)):
            if np.isnan(y):
                continue
            ax.annotate(spec["fmt"](y), xy=(x, y), xytext=(0, 7), textcoords="offset points", ha="center",
                        va="bottom", fontsize=8.0, color=st.INK, zorder=6)
        ax.set_xticks(xs)
        ax.set_xticklabels([st.T(f"{r['ja']}\n{x:.1f}", f"{r['en']}\n{x:.1f}") for x, r in zip(xs, rows)],
                           fontsize=7.8)
        lo, hi = float(np.nanmin(ys)), float(np.nanmax(ys))
        pad = (hi - lo) * 0.45 if hi > lo else max(abs(hi), 1.0) * 0.3
        ax.set_ylim(max(0.0, lo - pad * 0.6) if lo >= 0 else lo - pad, hi + pad)
        ax.set_xlim(xs.min() - 1.2, xs.max() + 1.2)
        ax.grid(axis="x", visible=False)
        ax.set_title(st.T(spec["ja"], spec["en"]), fontsize=10, pad=6)
        ax.set_ylabel(st.T(*spec["ylab"]))
        if k >= 3:
            ax.set_xlabel(st.T("実際の呼 / 体 / 日(腕=L4 の倍率)", "actual calls / agent / day (arm = L4 multiplier)"))

    handles = [plt.Line2D([], [], color=COLOR_REAL, marker="o", linewidth=1.6),
               plt.Line2D([], [], color=COLOR_CHOICE, marker="o", linewidth=1.6),
               plt.Line2D([], [], color="none", marker="o", markerfacecolor="none", markeredgecolor=COLOR_CURRENT,
                          markersize=9, markeredgewidth=1.4)]
    fig.legend(handles, [st.T("世界で実現した量(エンジンの計数)", "realized in the world (engine counts)"),
                         st.T("LLM の選択・効率", "LLM choices / efficiency"),
                         st.T("現行の予算(×1 = 400 万呼/日を体数按分)", "current budget (x1 = 4M calls/day scaled by agents)")],
               loc="upper right", bbox_to_anchor=(0.985, 0.955), ncol=3, fontsize=8.2, handlelength=1.6)

    fig.suptitle(st.T(f"図8 LLM 呼数の予算(L4)を動かすと世界で起きることはどう変わるか(AB8-L4-SCALE・5,000 体×1 日・seed {seed})",
                      f"Fig.8 What changes in the world when the LLM call budget (L4) moves (AB8-L4-SCALE, 5,000 agents x 1 day, seed {seed})"),
                 x=0.008, y=0.985, ha="left", va="top", fontsize=12, fontweight="bold", color=st.INK)
    st.note(fig, [
        st.T("4 ランは同構成(実 LLM 8B INT8・温度 0.7・看板 p_see 1.0・語彙 v1)で --l4-scale だけ違う。横軸は上限でなく**実際に応答した呼数**。無制限=1 tick の上限を体数に置いた腕。",
             "Four runs share everything but --l4-scale. x = calls actually answered, not the cap. unlimited = per-tick cap set to the agent count."),
        st.T("(a)〜(d) は RunResult の実現欄(購入=診断列の日合計・売上=日末残高・乗車=改札を通って列車に乗った件数・会話=開いたセッション)。(e) = action_counts[購入]/n_texts。(f) = 購入 ÷ 呼数 × 1,000。",
             "(a)-(d) from RunResult realized fields; (e) = action_counts[buy]/n_texts; (f) = purchases / calls x 1,000."),
        st.T("×1 は AB6b seed 1 の看板あり腕と final_hash まで一致。数値は fig8_ab8_budget.json。出典 ab8_s1_parent_report.md。",
             "x1 reproduces the AB6b seed 1 signage-on arm to the final hash. numbers: fig8_ab8_budget.json."),
    ])
    return fig


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="図8: L4 予算 vs 実現量(AB8-L4-SCALE)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    data = load_ab8()
    fig = draw(data)
    paths = st.save(fig, args.out, STEM)
    payload = {
        "schema": "shibuya.tools.fig/ab8_budget/1",
        "figure": STEM,
        "what": "L4 倍率 ×0.5/×1/×2/無制限 の 4 ランの 実際の呼/体/日 と 実現量(購入・売上・乗車・会話)・購入シェア・購入/千呼。",
        "seed": data["seed"],
        "seeds_found": data["seeds_found"],
        "rows": data["rows"],
        "all_rows": data["all_rows"],
        "outputs": paths,
    }
    payload["sidecar"] = st.write_sidecar(args.out, STEM, payload)
    print(json.dumps({"outputs": paths, "sidecar": payload["sidecar"],
                      "rows": [(r["tag"], r["calls_per_agent_day"], r["purchases_per_agent_day"], r["boarded_per_agent_day"])
                               for r in data["rows"]]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
