# -*- coding: utf-8 -*-
"""表 1〜3 — 検証ラン(ablation)の結果表(PNG + SVG + Markdown + JSON)。

何を示すか
    図 5〜7 のサイドカー JSON **だけ**から表を組む(数値の出所を 1 つにする)。
    表 1 = 語彙 v1 / v2 / 自由文+v2 の行動分布(AB7c seed 1)。
    表 2 = 看板の腕(09-10 AB6 seed 1/2・09-17 AB6b seed 在るぶん)の購入・会話・休憩・注視率。
    表 3a = 朝の乗車率の条件別(v1 vs v2)。表 3b = 直前行動別の次手分布。

出力
    docs/bench/figures/tbl{1,2,3a,3b}_*.{png,svg} と、貼り付け用の Markdown を 1 本
    (``tbl_ablation.md``)、セルの値をそのまま持つ ``tbl_ablation.json``。

例::

    python tools/fig/tbl_ablation.py --out docs/bench/figures
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path
from typing import Any, Mapping, Sequence

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import _style as st  # noqa: E402

DEFAULT_FIG_DIR = "docs/bench/figures"
DEFAULT_OUT = "docs/bench/figures"
MD_STEM = "tbl_ablation"

ACTIONS_T1: tuple[str, ...] = ("移動", "購入", "食事", "休憩", "待機", "乗車", "会話", "(未定義)")


def _pct(count: float, n: float) -> str:
    return f"{100.0 * count / n:.2f}%" if n else "—"


def _fmt(v: Any, nd: int = 2) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


# ---------------------------------------------------------------- 表の組み立て(純関数)


def table1(fig5: Mapping[str, Any]) -> dict[str, Any]:
    arms = fig5["arms"]
    tags = list(arms)
    runner = (fig5.get("runner") or {}).get("per_arm") or {}
    cols = ["行動"] + [str(arms[t]["label"]) for t in tags]
    rows: list[list[str]] = []
    for w in ACTIONS_T1:
        if not any(arms[t]["action_counts"].get(w) for t in tags):
            continue
        rows.append([w] + [f"{_fmt(int(arms[t]['action_counts'].get(w, 0)))} ({_pct(arms[t]['action_counts'].get(w, 0), arms[t]['n_live'])})"
                           for t in tags])
    rows.append(["呼数(非繰り延べ)"] + [_fmt(int(arms[t]["n_live"])) for t in tags])
    rows.append(["エントロピー [bits]"] + [_fmt(float(arms[t]["entropy_bits"]), 3) for t in tags])
    rows.append(["書式エラー率(厳密)"] + [_fmt((runner.get(t) or {}).get("format_error_rate_strict"), 3) for t in tags])
    rows.append(["実現した食事 [回]"] + [_fmt((runner.get(t) or {}).get("meals")) for t in tags])
    rows.append(["入力トークン 平均"] + [_fmt((runner.get(t) or {}).get("prompt_tokens_mean"), 1) for t in tags])
    jsd = fig5.get("jsd_bits") or {}
    note = (f"v1 vs v2 の JSD {jsd.get('raw', 0):.4f} bits・食事を購入に畳むと {jsd.get('meal_folded_into_buy', 0):.4f} bits。"
            "5,000 体×1,440 tick・実 LLM(7×Qwen3-8B INT8・温度 0.7)・seed 1。出典 fig5_ab7c_vocab.json。")
    return {"stem": "tbl1_ab7c_vocab", "title": "表1 語彙 v1 / v2 / 自由文+v2 の行動分布(AB7c-VOCAB-V2・seed 1)",
            "columns": cols, "rows": rows, "note": note, "align": ["left"] + ["right"] * len(tags)}


def table2(fig6: Mapping[str, Any]) -> dict[str, Any]:
    cols = ["コード", "seed", "腕", "購入", "Δ購入 [pp]", "会話 [呼]", "休憩", "注視率(実測)", "入力 tok"]
    rows: list[list[str]] = []
    for r in fig6["runs"]:
        code = "09-10(C7 期)" if r["group"] == "legacy" else "09-17(現行)"
        sr = r.get("shown_rate")
        gate = _fmt(float(sr), 3) if isinstance(sr, (int, float)) and r.get("gate_draws") else ("1.000" if r["tag"] != "ad_zero" and r["tag"] != "signage_off" else "—")
        rows.append([code, str(r["seed"]), str(r["ja"]), f"{r['buy_pct']:.2f}%",
                     ("0(基準)" if r["delta_buy_pp"] == 0 else f"{r['delta_buy_pp']:+.2f}"),
                     _fmt(int(r["talk"])), f"{r['rest_pct']:.2f}%", gate, _fmt(r.get("prompt_tokens_mean"), 1)])
    null = fig6.get("null_seed_pp") or {}
    note = (f"Δ購入 = 購入シェア − 看板あり(同コード・同 seed)。正=看板を消す/減らすと購入が増える。AD1 の線 ±{fig6.get('ad1_line_pp', 1.0):g} pp。"
            f"seed 差の幅(看板あり腕・seed 1 vs 2): 09-10 {_fmt(null.get('legacy'))} pp"
            + (f"・09-17 {_fmt(null.get('current'))} pp" if null.get("current") is not None else "") + "。出典 fig6_ab6b_signage.json。")
    return {"stem": "tbl2_ab6b_signage", "title": "表2 看板(広告)の腕: 購入・会話・休憩(09-10 AB6-AD-ZERO / 09-17 AB6b-AD-NOTICE)",
            "columns": cols, "rows": rows, "note": note,
            "align": ["left", "right", "left", "right", "right", "right", "right", "right", "right"]}


def table3a(fig7: Mapping[str, Any]) -> dict[str, Any]:
    arms = fig7["arms"]
    t0, t1 = str(arms[0]["tag"]), str(arms[1]["tag"])
    l0, l1 = str(arms[0]["ja"]), str(arms[1]["ja"])
    lo, hi = fig7.get("inputs", {}).get("morning_hours", [6, 10])
    cols = ["条件", f"{l0} 呼数", f"{l0} 乗車", f"{l0} 乗車率", f"{l1} 呼数", f"{l1} 乗車", f"{l1} 乗車率", "比 v2/v1"]
    rows: list[list[str]] = []
    for c in fig7["conditions"]:
        a, b = c[t0], c[t1]
        ratio = (b["rate_pct"] / a["rate_pct"]) if a["rate_pct"] else None
        rows.append([str(c["ja"]), _fmt(int(a["n"])), _fmt(int(a["ride"])), f"{a['rate_pct']:.2f}%",
                     _fmt(int(b["n"])), _fmt(int(b["ride"])), f"{b['rate_pct']:.2f}%", _fmt(ratio, 2)])
    ov = fig7.get("overlap") or {}
    note = (f"{lo:02d}〜{hi:02d} 時の呼。朝に乗車を選んだ体: v1 {ov.get(t0, 0)} / v2 {ov.get(t1, 0)} / 共通 {ov.get('common', 0)}。"
            "種別 = B1・駅の可視 = B2 に「駅」・起床クラス = wake_class。出典 fig7_d91_ride_chain.json。")
    return {"stem": "tbl3a_d91_ride_rate", "title": "表3a 朝の乗車率の条件別(AB7c seed 1・語彙 v1 vs v2)",
            "columns": cols, "rows": rows, "note": note, "align": ["left"] + ["right"] * 7}


def table3b(fig7: Mapping[str, Any]) -> dict[str, Any]:
    arms = {str(a["tag"]): str(a["ja"]) for a in fig7["arms"]}
    words = list((fig7["chains"][0]["share_pct"] if fig7["chains"] else {}).keys())
    cols = ["腕", "直前の行動", "n"] + [f"{w}" for w in words]
    rows: list[list[str]] = []
    for ch in fig7["chains"]:
        rows.append([arms.get(ch["tag"], ch["tag"]), str(ch["prev"]), _fmt(int(ch["n"]))]
                    + [f"{ch['share_pct'][w]:.1f}%" for w in words])
    note = "同じ体の次の呼で選ばれた行動の割合(行 = 100%)。出典 fig7_d91_ride_chain.json。"
    return {"stem": "tbl3b_d91_next_action", "title": "表3b 直前の行動別の次手(AB7c seed 1)",
            "columns": cols, "rows": rows, "note": note, "align": ["left", "left", "right"] + ["right"] * len(words)}


def build_tables(fig5: Mapping[str, Any], fig6: Mapping[str, Any], fig7: Mapping[str, Any]) -> list[dict[str, Any]]:
    """3 つのサイドカー → 表 4 枚の仕様。**純関数**。"""
    return [table1(fig5), table2(fig6), table3a(fig7), table3b(fig7)]


def to_markdown(spec: Mapping[str, Any]) -> str:
    """表の仕様 → Markdown(GFM)。**純関数**。"""
    cols = list(spec["columns"])
    align = list(spec.get("align") or ["left"] * len(cols))
    sep = ["---:" if a == "right" else ":---" for a in align]
    lines = [f"**{spec['title']}**", "", "| " + " | ".join(cols) + " |", "| " + " | ".join(sep) + " |"]
    for r in spec["rows"]:
        lines.append("| " + " | ".join(str(c) for c in r) + " |")
    if spec.get("note"):
        lines += ["", f"_{spec['note']}_"]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 描画


def render_table(spec: Mapping[str, Any]):
    """表の仕様 → Figure(matplotlib の table)。**ファイルを読まない**。"""
    import matplotlib.pyplot as plt

    st.use_style()
    cols = list(spec["columns"])
    rows = [list(map(str, r)) for r in spec["rows"]]
    align = list(spec.get("align") or ["left"] * len(cols))
    n_rows, n_cols = len(rows), len(cols)
    widths = [max(len(str(cols[j])), *(len(r[j]) for r in rows)) for j in range(n_cols)]
    total_w = sum(widths)
    fig_w = min(15.0, max(7.0, 0.115 * total_w + 0.8))
    note_lines = textwrap.wrap(str(spec.get("note") or ""), width=max(20, int(fig_w * 9.5)))
    head_in, note_in = 0.55, 0.22 + 0.16 * len(note_lines)
    fig_h = 0.30 * (n_rows + 1) + head_in + note_in
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.subplots_adjust(left=0.01, right=0.99, top=1 - head_in / fig_h, bottom=note_in / fig_h)
    ax.axis("off")
    ax.grid(False)
    tbl = ax.table(cellText=rows, colLabels=cols, bbox=[0, 0, 1, 1], cellLoc="right",
                   colWidths=[w / total_w for w in widths])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.6)
    for (i, j), cell in tbl.get_celld().items():
        cell.set_edgecolor(st.GRID)
        cell.set_linewidth(0.7)
        cell.get_text().set_color(st.INK)
        if i == 0:
            cell.set_facecolor(st.GRID)
            cell.get_text().set_fontweight("bold")
            cell.get_text().set_color(st.INK2)
            cell.get_text().set_ha("center")
        else:
            cell.set_facecolor(st.SURFACE)
            cell.get_text().set_ha("left" if align[j] == "left" else "right")
            cell.PAD = 0.04
    fig.suptitle(spec["title"], x=0.01, y=0.985, ha="left", va="top", fontsize=11, fontweight="bold", color=st.INK)
    if note_lines:
        st.note(fig, note_lines, y=0.02)
    return fig


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="表1〜3: 検証ランの結果表(図 5〜7 のサイドカーから)")
    ap.add_argument("--fig-dir", default=DEFAULT_FIG_DIR, help="fig5/6/7 のサイドカー JSON の置き場")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    fd = Path(args.fig_dir)
    fig5 = json.loads((fd / "fig5_ab7c_vocab.json").read_text(encoding="utf-8"))
    fig6 = json.loads((fd / "fig6_ab6b_signage.json").read_text(encoding="utf-8"))
    fig7 = json.loads((fd / "fig7_d91_ride_chain.json").read_text(encoding="utf-8"))
    specs = build_tables(fig5, fig6, fig7)
    outputs: dict[str, Any] = {}
    md_parts = ["# 検証ラン(ablation)の結果表(図 5〜7 のサイドカーから生成・tools/fig/tbl_ablation.py)", ""]
    for spec in specs:
        fig = render_table(spec)
        outputs[spec["stem"]] = st.save(fig, args.out, spec["stem"])
        md_parts.append(to_markdown(spec))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{MD_STEM}.md"
    md_path.write_text("\n".join(md_parts), encoding="utf-8", newline="\n")
    payload = {
        "schema": "shibuya.tools.fig/tbl_ablation/1",
        "what": "図 5〜7 のサイドカー JSON から組んだ結果表 4 枚(セルの文字列をそのまま持つ)。",
        "inputs": {k: st.rel(fd / f"{k}.json") for k in ("fig5_ab7c_vocab", "fig6_ab6b_signage", "fig7_d91_ride_chain")},
        "tables": [{k: v for k, v in s.items()} for s in specs],
        "outputs": outputs,
        "markdown": st.rel(md_path),
    }
    payload["sidecar"] = st.write_sidecar(args.out, MD_STEM, payload)
    print(json.dumps({"outputs": outputs, "markdown": payload["markdown"], "sidecar": payload["sidecar"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
