# -*- coding: utf-8 -*-
"""図 1 — 在圏の 24 時間曲線 vs 現実アンカー。

何を示すか
    5 エリア(= 渋谷駅周辺 139 ha 区域に対応)の在圏人数を 24 時間ぶん並べ、現実側の
    アンカー(内閣府 PT の日中滞在ピーク・深夜在圏の推定帯・中核 9 町丁目の昼間人口)と
    同じ軸に置く。ラン 3 本(c7-day-2 → day-3 → day-4)の**並び**が D-66(域外常住者が
    深夜も域内に居た)の修正の効きで、mock40-v21 は実 LLM 無しの対照。

数え方は既存物に任せる(二重実装しない)
    セル→5 エリア写像 ``tools/c7/occupancy_series.build_map``(``area_axes_v0.json``)・
    journal の読み ``occupancy_series.load_journal``・時×エリア集計
    ``c7lib.OccupancySeries.area_hour_table``。本スクリプトは**合計して描くだけ**。
    出した値は ``docs/bench/c7/yardstick/.../presence_yardstick.json`` と突き合わせて
    サイドカー JSON に一致を記録する(``yardstick_check``)。

**KDDI holdout は開かない**(封印 ``data/world/v2/w19_freeze.json``)。現実側の数値は全て
``docs/bench/anchors/presence_anchors_v0.json``(source/tag/verified_by つき)から読む。

例::

    python tools/fig/fig_presence_24h.py --out docs/bench/figures
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
for _p in (str(_HERE), str(REPO_ROOT / "tools" / "c7")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _style as st  # noqa: E402

#: 既定の入力。
DEFAULT_RUNS_DIR = "data/server_retrieval/2026-09-16/v2_data/runs"
DEFAULT_WORLD = "data/world/v2"
DEFAULT_AXES = "tools/c7/area_axes_v0.json"
DEFAULT_ANCHORS = "docs/bench/anchors/presence_anchors_v0.json"
DEFAULT_YARDSTICK = ("docs/bench/c7/yardstick/after_c7-day-4_vs_c7-day-3/"
                     "presence_yardstick.json")
DEFAULT_OUT = "docs/bench/figures"
STEM = "fig1_presence_24h"

#: 描く系列(id・種別・色・線幅・線種)。**順序 = 色の順序**(ラン 3 本は順序尺度の青ランプ)。
SERIES: tuple[dict[str, Any], ...] = (
    {"run": "c7-day-2", "kind": "run", "color": st.ORDINAL_BLUE3[0], "lw": 2.0, "ls": "-"},
    {"run": "c7-day-3", "kind": "run", "color": st.ORDINAL_BLUE3[1], "lw": 2.0, "ls": "-"},
    {"run": "c7-day-4", "kind": "run", "color": st.ORDINAL_BLUE3[2], "lw": 2.4, "ls": "-"},
    {"run": "mock40-v21", "kind": "mock", "color": st.MUTED, "lw": 1.3, "ls": (0, (5, 3))},
)

#: yardstick JSON が持っている時刻(3 時間刻み)= 突き合わせの対象。
YARDSTICK_HOURS: tuple[int, ...] = (0, 3, 6, 9, 12, 15, 18, 21)


# ---------------------------------------------------------------- 読み込み


def load_presence(runs_dir: str | Path = DEFAULT_RUNS_DIR,
                  world_dir: str | Path = DEFAULT_WORLD,
                  axes_path: str | Path = DEFAULT_AXES,
                  anchors_path: str | Path = DEFAULT_ANCHORS,
                  yardstick_path: str | Path | None = DEFAULT_YARDSTICK,
                  series: Sequence[Mapping[str, Any]] = SERIES) -> dict[str, Any]:
    """journal(``occupancy.npz``)とアンカー台帳 → 描画に要るデータ dict。"""
    import occupancy_series as occ  # tools/c7(sys.path 済み)

    amap, gate = occ.build_map(world_dir, axes_path)
    out_series: dict[str, Any] = {}
    for spec in series:
        run = str(spec["run"])
        path = Path(runs_dir) / run / "occupancy.npz"
        s = occ.load_journal(path)
        five = np.asarray(s.area_hour_table(amap), dtype=np.float64).sum(axis=1)
        out_series[run] = {
            "label": run,
            "kind": spec["kind"],
            "color": spec["color"],
            "lw": spec["lw"],
            "ls": spec["ls"],
            "five_area": [round(float(v), 1) for v in five],
            "path": st.rel(path),
        }

    doc = json.loads(Path(anchors_path).read_text(encoding="utf-8"))
    a = doc["anchors"]
    anchors = {
        "pt_area_daytime_peak": {
            "value": float(a["pt_area_daytime_peak"]["value"]),
            "tag": a["pt_area_daytime_peak"]["tag"],
            "scope": a["pt_area_daytime_peak"]["scope"],
            "source": a["pt_area_daytime_peak"]["source"],
        },
        "night_presence_estimate": {
            "low": float(a["night_presence_estimate"]["low"]),
            "high": float(a["night_presence_estimate"]["high"]),
            "tag": a["night_presence_estimate"]["tag"],
            "scope": a["night_presence_estimate"]["scope"],
            "source": a["night_presence_estimate"]["source"],
        },
        "core9_daytime_population": {
            "value": float(a["core9_daytime_population"]["value"]),
            "tag": a["core9_daytime_population"]["tag"],
            "scope": a["core9_daytime_population"]["scope"],
            "source": a["core9_daytime_population"]["source"],
        },
    }
    wake = a.get("wake_rate_tokyo_weekday")
    wake_rate = None
    if wake and len(wake.get("values", [])) == 24:
        wake_rate = {
            "values": [float(v) for v in wake["values"]],
            "unit": wake.get("unit", "%"),
            "tag": wake.get("tag"),
            "scope": wake.get("scope"),
            "caveat": wake.get("caveat"),
            "source": wake.get("source"),
        }

    data: dict[str, Any] = {
        "hours": list(range(24)),
        "series": out_series,
        "anchors": anchors,
        "wake_rate_anchor": wake_rate,
        "area_map": {
            "cells": amap.counts(),
            "area_ha": amap.area_ha(),
            "gate_ok": bool(gate["ok"]),
            "tag": "expedient",
        },
        "inputs": {
            "runs_dir": st.rel(runs_dir), "world": st.rel(world_dir),
            "axes": st.rel(axes_path), "anchors": st.rel(anchors_path),
        },
    }
    if yardstick_path and Path(yardstick_path).exists():
        data["yardstick_check"] = check_against_yardstick(out_series, yardstick_path)
        data["inputs"]["yardstick"] = st.rel(yardstick_path)
    return data


def check_against_yardstick(series: Mapping[str, Any],
                            yardstick_path: str | Path) -> dict[str, Any]:
    """自分で npz から出した値が既存の集計 JSON と一致するかを測る。**純関数**。

    ``presence_yardstick.json`` は ``after`` = c7-day-4 / ``before`` = c7-day-3 を持つ。
    ``presence_by_hour[]`` は 3 時間刻み・``area_hour_counts`` は 24 時間ぶんの (24,5)。
    """
    doc = json.loads(Path(yardstick_path).read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for slot in ("after", "before"):
        blob = doc.get(slot)
        if not blob:
            continue
        run = str(blob.get("label"))
        mine = series.get(run)
        if mine is None:
            continue
        by_hour = {int(r["hour"]): float(r["five_area"]) for r in blob["presence_by_hour"]}
        full = [round(float(sum(row)), 1) for row in blob["area_hour_counts"]]
        diffs = [abs(mine["five_area"][h] - full[h]) for h in range(24)]
        rows.append({
            "slot": slot,
            "run": run,
            "hours_3h": list(YARDSTICK_HOURS),
            "expected_3h": [by_hour.get(h) for h in YARDSTICK_HOURS],
            "computed_3h": [mine["five_area"][h] for h in YARDSTICK_HOURS],
            "expected_24h": full,
            "max_abs_diff_24h": round(float(max(diffs)) if diffs else 0.0, 4),
            "ok": bool(max(diffs) <= 0.05) if diffs else False,
        })
    return {"path": st.rel(yardstick_path), "runs": rows,
            "ok": bool(rows) and all(r["ok"] for r in rows)}


# ---------------------------------------------------------------- 描画


def draw(data: Mapping[str, Any]):
    """データ dict → Figure。**ファイルを読まない**(テストは合成データで呼べる)。"""
    import matplotlib.pyplot as plt

    st.use_style()
    hours = np.asarray(data["hours"], dtype=float)
    anc = data["anchors"]
    peak = anc["pt_area_daytime_peak"]["value"]
    night_lo = anc["night_presence_estimate"]["low"]
    night_hi = anc["night_presence_estimate"]["high"]
    core9 = anc["core9_daytime_population"]["value"]
    wake = data.get("wake_rate_anchor")

    nrows = 2 if wake else 1
    heights = [3.0, 1.0] if wake else [1.0]
    fig, axes = plt.subplots(nrows, 1, figsize=(10.0, 6.5 if wake else 5.2),
                             sharex=True, gridspec_kw={"height_ratios": heights},
                             squeeze=False)
    axes = axes[:, 0]
    ax = axes[0]
    fig.subplots_adjust(left=0.085, right=0.815, top=0.845, bottom=0.200, hspace=0.32)

    band_label = st.T(
        "夜間帯 " + st.thousands(night_lo) + "–" + st.thousands(night_hi) + "(estimate)",
        "night band " + st.thousands(night_lo) + "-" + st.thousands(night_hi) + " (estimate)")
    peak_label = st.T(
        "日中滞在ピーク " + st.thousands(peak) + "(anchor)",
        "daytime peak " + st.thousands(peak) + " (anchor)")
    core9_label = st.T(
        "参考 中核9町丁目 " + st.thousands(core9) + "(面積差あり)",
        "ref. core-9 " + st.thousands(core9) + " (different area)")

    # -- 現実側(橙)を先に敷く: 系列の下に来る --
    ax.fill_between([0, 3], [night_lo, night_lo], [night_hi, night_hi],
                    color=st.ANCHOR, alpha=0.16, linewidth=0, zorder=1, label=band_label)
    ax.axhline(peak, color=st.ANCHOR, linewidth=1.6, zorder=2, label=peak_label)
    ax.axhline(core9, color=st.MUTED, linewidth=1.1, linestyle=(0, (1, 2.2)), zorder=2,
               label=core9_label)

    # -- ラン系列 --
    label_pts: list[tuple[str, float, str]] = []
    for _run, s in data["series"].items():
        y = np.asarray(s["five_area"], dtype=float)
        suffix = st.T("(mock)", " (mock)") if s["kind"] == "mock" else ""
        name = str(s["label"]) + suffix
        ax.plot(hours, y, color=s["color"], linewidth=s["lw"], linestyle=s["ls"],
                solid_capstyle="round", zorder=4, label=name)
        label_pts.append((name, float(y[-1]), str(s["color"])))

    top = max([peak] + [max(s["five_area"]) for s in data["series"].values()]) * 1.09
    ax.set_ylim(0, top)
    ax.set_xlim(-0.5, 23.5)
    ax.set_xticks(list(range(0, 24, 3)) + [23])
    ax.yaxis.set_major_formatter(lambda v, _pos: st.thousands(v))
    ax.set_ylabel(st.T("在圏(人)", "presence (people)"))
    fig.suptitle(st.T("図1 渋谷駅周辺 139 ha の在圏 24 時間曲線 と 現実アンカー",
                      "Fig.1 24-hour presence in the 139 ha Shibuya area vs real-world anchors"),
                 x=0.010, y=0.982, ha="left", va="top", fontsize=12, fontweight="bold",
                 color=st.INK)

    # 直接ラベル(右端・重なりをほどく)。凡例と併置だが 4 系列では必須(dataviz)。
    ys = st.declutter([v for _n, v, _c in label_pts], min_gap=top * 0.048, lo=0.0, hi=top)
    for (name, raw, color), y in zip(label_pts, ys):
        short = name.split("(")[0]
        ax.annotate(short + "  " + st.thousands(raw), xy=(23.5, raw), xytext=(24.15, y),
                    xycoords="data", textcoords="data", color=color, fontsize=8.4,
                    va="center", ha="left", annotation_clip=False,
                    arrowprops={"arrowstyle": "-", "color": color, "linewidth": 0.7,
                                "shrinkA": 1.5, "shrinkB": 1.5})
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.010, 0.945),
               ncol=4, handlelength=1.8, columnspacing=1.6, borderaxespad=0.0)

    # -- 副パネル: 起床率 a(h) --
    if wake:
        ax2 = axes[1]
        ax2.plot(hours, np.asarray(wake["values"], dtype=float), color=st.ANCHOR,
                 linewidth=1.8, marker="o", markersize=3.2, zorder=3)
        ax2.set_ylim(0, 112)
        ax2.set_ylabel(st.T("起床率(%)", "wake rate (%)"))
        ax2.set_yticks([0, 50, 100])
        ax2.set_title(
            st.T("起床率 a(h) = 100 − 睡眠率(東京都・平日・10歳以上/ 総務省 令和3年社会生活基本調査・anchor)",
                 "wake rate a(h) = 100 - sleep rate (Tokyo weekday, age 10+, MIC 2021, anchor)"),
            fontsize=9, pad=4)
        ax2.set_xlabel(st.T("世界内の時刻(時)", "hour of day"))
    else:
        ax.set_xlabel(st.T("世界内の時刻(時)", "hour of day"))

    st.note(fig, [
        st.T("在圏 = 5 エリア合計(139 ha 区域に対応)。セル→5エリア写像 area_axes_v0 は expedient: 境界を ±50 m 動かすと −50 m で 5.6% / +50 m で 8.3% のセルが移動する。",
             "presence = sum of the 5 areas (139 ha). cell-to-area map area_axes_v0 is expedient: +-50 m moves 5.6% / 8.3% of cells."),
        st.T("mock40-v21 は実 LLM を使わない対照ラン(細い破線)。縦軸は生の体数(縮尺なし・n=390,067)。",
             "mock40-v21 is the no-LLM control (thin dashed). y-axis is raw agent counts (no scaling, n=390,067)."),
        st.T("KDDI holdout は未開封・未使用。数値は fig1_presence_24h.json。",
             "The KDDI holdout is sealed and unused. Numbers: fig1_presence_24h.json."),
    ])
    return fig


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="図1: 在圏の 24 時間曲線 vs 現実アンカー")
    ap.add_argument("--runs-dir", default=DEFAULT_RUNS_DIR)
    ap.add_argument("--world", default=DEFAULT_WORLD)
    ap.add_argument("--axes", default=DEFAULT_AXES)
    ap.add_argument("--anchors", default=DEFAULT_ANCHORS)
    ap.add_argument("--yardstick", default=DEFAULT_YARDSTICK,
                    help="集計済み JSON との突き合わせ(空文字で省略)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    data = load_presence(args.runs_dir, args.world, args.axes, args.anchors,
                         args.yardstick or None)
    fig = draw(data)
    paths = st.save(fig, args.out, STEM)
    payload = {
        "schema": "shibuya.tools.fig/presence_24h/1",
        "figure": STEM,
        "what": "5 エリア(139 ha)の在圏 24 時間曲線と現実アンカー。KDDI holdout 未使用。",
        "inputs": data["inputs"],
        "hours": data["hours"],
        "series": {k: {kk: vv for kk, vv in v.items() if kk not in ("color", "lw", "ls")}
                   for k, v in data["series"].items()},
        "anchors": data["anchors"],
        "wake_rate_anchor": data["wake_rate_anchor"],
        "area_map": data["area_map"],
        "yardstick_check": data.get("yardstick_check"),
        "outputs": paths,
    }
    payload["sidecar"] = st.write_sidecar(args.out, STEM, payload)
    print(json.dumps({"outputs": paths, "sidecar": payload["sidecar"],
                      "yardstick_ok": (data.get("yardstick_check") or {}).get("ok")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
