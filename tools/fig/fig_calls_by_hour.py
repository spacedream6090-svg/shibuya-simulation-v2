# -*- coding: utf-8 -*-
"""図 2 — 時刻別の LLM 呼数と起床クラス(c7-day-4)。

何を示すか
    1 シミュ日(1,440 tick = 1 分刻み)のあいだ、**どの時刻に・どんな理由で** LLM を
    呼んだか。上段は応答が返った呼(非繰り延べ)を起床クラスで積み上げ、下段 2 枚は
    応答が返らなかった呼(``deferred``)の件数と率。

``wake_class`` の意味
    テープの ``wake_class`` 列は ``shibuya.core.types.EventClass``
    (``INSTITUTION=-1 / CONVERSATION=0 / PLAN_BOUNDARY=1 / INDIVIDUAL=2 / CELL=3``)。
    エンジンは ``run.py`` で ``cls = decision.selected_eff_class[i]`` をそのまま
    ``LLMCall.wake_class`` に載せる。**昇順が優先**(会話ターン > 計画境界 > 個体変化 >
    セル変化)= 同 docstring §2.5。和名はその docstring の文面から写した(値と並びは
    enum から取るので、enum が変われば本スクリプトは例外で止まる)。

**右軸は作らない**(2 つの縦軸を 1 枚に重ねると相関を捏造する)。件数と率は
別パネルに分けて同じ x 軸を共有させる。

例::

    python tools/fig/fig_calls_by_hour.py --out docs/bench/figures
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
for _p in (str(_HERE), str(REPO_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _style as st  # noqa: E402

DEFAULT_TAPE = "data/server_retrieval/2026-09-16/v2_data/tape/c7-day-4/calls.parquet"
DEFAULT_ANCHORS = "docs/bench/anchors/presence_anchors_v0.json"
DEFAULT_OUT = "docs/bench/figures"
STEM = "fig2_calls_by_hour"

#: ``EventClass`` の和名(``src/shibuya/core/types.py`` の docstring §2.5 の文面)。
CLASS_JA: dict[str, str] = {
    "INSTITUTION": "制度(繰り延べ対象外)",
    "CONVERSATION": "会話ターン",
    "PLAN_BOUNDARY": "計画境界",
    "INDIVIDUAL": "個体変化",
    "CELL": "セル変化",
}
#: 同・英語(日本語書体が無い環境用)。
CLASS_EN: dict[str, str] = {
    "INSTITUTION": "institution",
    "CONVERSATION": "conversation turn",
    "PLAN_BOUNDARY": "plan boundary",
    "INDIVIDUAL": "individual change",
    "CELL": "cell change",
}

#: 1 tick = 1 分。
TICKS_PER_HOUR = 60


def event_classes() -> list[dict[str, Any]]:
    """``EventClass`` を**優先順(昇順)**に並べた記述。値と並びは src から取る。"""
    from shibuya.core.types import EventClass

    out: list[dict[str, Any]] = []
    for i, member in enumerate(sorted(EventClass, key=int)):
        name = member.name
        if name not in CLASS_JA:  # pragma: no cover - enum が増えたら止める
            raise KeyError(f"EventClass.{name} の和名が CLASS_JA に無い(src が変わった)")
        out.append({
            "value": int(member),
            "name": name,
            "ja": CLASS_JA[name],
            "en": CLASS_EN[name],
            "color": st.CAT[max(0, i - 1) % len(st.CAT)],
        })
    return out


# ---------------------------------------------------------------- 読み込み


def load_calls(tape_path: str | Path = DEFAULT_TAPE,
               anchors_path: str | Path | None = DEFAULT_ANCHORS,
               n_agents: int | None = None) -> dict[str, Any]:
    """``calls.parquet`` の必要 3 列だけを読む(``response`` 列は読まない=メモリ節約)。"""
    import pyarrow.parquet as pq

    path = Path(tape_path)
    t = pq.read_table(path, columns=["tick", "wake_class", "deferred"])
    tick = t.column("tick").to_numpy()
    wcls = t.column("wake_class").to_numpy()
    defd = t.column("deferred").to_numpy()
    hour = ((tick // TICKS_PER_HOUR) % 24).astype(np.int64)
    live = defd == 0

    classes = event_classes()
    seen = sorted({int(v) for v in np.unique(wcls)})
    used = [c for c in classes if c["value"] in seen]
    unknown = [v for v in seen if v not in {c["value"] for c in classes}]
    if unknown:  # pragma: no cover - EventClass 外の値
        raise ValueError(f"EventClass に無い wake_class: {unknown}")

    live_by = np.zeros((24, len(used)), dtype=np.int64)
    for j, c in enumerate(used):
        sel = live & (wcls == c["value"])
        live_by[:, j] = np.bincount(hour[sel], minlength=24)[:24]
    deferred_by = np.bincount(hour[~live], minlength=24)[:24]
    total_by = np.bincount(hour, minlength=24)[:24]

    reasons: dict[str, int] = {}
    if int((~live).sum()):
        rt = pq.read_table(path, columns=["deferred_reason"],
                           filters=[("deferred", "=", 1)])
        col = rt.column("deferred_reason").to_pylist()
        for v in col:
            key = str(v) or "(空)"
            reasons[key] = reasons.get(key, 0) + 1

    if n_agents is None and anchors_path and Path(anchors_path).exists():
        doc = json.loads(Path(anchors_path).read_text(encoding="utf-8"))
        fp = doc["anchors"].get("full_population")
        if fp:
            n_agents = int(fp["value"])

    n_rows = int(len(tick))
    n_live = int(live.sum())
    n_def = n_rows - n_live
    return {
        "hours": list(range(24)),
        "classes": used,
        "live_by_hour_class": live_by.tolist(),
        "deferred_by_hour": deferred_by.tolist(),
        "total_by_hour": total_by.tolist(),
        "deferred_rate_by_hour": [round(float(d) / float(t_), 6) if t_ else 0.0
                                  for d, t_ in zip(deferred_by.tolist(), total_by.tolist())],
        "deferred_reasons": dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
        "totals": {
            "rows": n_rows,
            "live": n_live,
            "deferred": n_def,
            "deferred_rate": round(n_def / n_rows, 6) if n_rows else 0.0,
            "n_agents": n_agents,
            "calls_per_agent_day": (round(n_live / n_agents, 4) if n_agents else None),
            "n_agents_source": ("docs/bench/anchors/presence_anchors_v0.json"
                               " anchors.full_population" if n_agents else None),
        },
        "input": st.rel(path),
    }


# ---------------------------------------------------------------- 描画


def _ink_on(hex_color: str) -> str:
    """塗りの上に置く文字色(明るい塗りには濃いインク・暗い塗りには地の色)。"""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    lin = [(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4) for c in (r, g, b)]
    lum = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return st.INK if lum > 0.42 else st.SURFACE


def draw(data: Mapping[str, Any]):
    """データ dict → Figure。**ファイルを読まない**。"""
    import matplotlib.pyplot as plt

    st.use_style()
    hours = np.asarray(data["hours"], dtype=float)
    classes = list(data["classes"])
    live = np.asarray(data["live_by_hour_class"], dtype=float)  # (24, K)
    deferred = np.asarray(data["deferred_by_hour"], dtype=float)
    rate = np.asarray(data["deferred_rate_by_hour"], dtype=float) * 100.0
    tot = data["totals"]

    fig, axes = plt.subplots(3, 1, figsize=(10.0, 8.2), sharex=True,
                             gridspec_kw={"height_ratios": [3.1, 1.0, 1.0]},
                             squeeze=False)
    axes = axes[:, 0]
    fig.subplots_adjust(left=0.095, right=0.815, top=0.860, bottom=0.180, hspace=0.36)

    # -- 上: 起床クラス別の積み上げ --
    ax = axes[0]
    bottom = np.zeros(24, dtype=float)
    top_total = float(live.sum(axis=1).max())
    marks: list[tuple[str, float, str]] = []
    for j, c in enumerate(classes):
        y = live[:, j]
        ax.bar(hours, y, bottom=bottom, width=0.80, color=c["color"],
               edgecolor=st.SURFACE, linewidth=1.2, zorder=3,
               label=st.T(c["ja"], c["en"]))
        # 直接ラベルは**その系列が最も太い 1 本だけ**(棒の中には置かない=はみ出すため)
        k = int(np.argmax(y))
        if y[k] > 0:
            marks.append((st.T(c["ja"], c["en"]) + "  " + st.thousands(y[k])
                          + st.T(" @" + str(k) + "時", " @" + str(k) + "h"),
                          bottom[k] + y[k] / 2.0, str(c["color"])))
        bottom = bottom + y
    ys = st.declutter([v for _n, v, _c in marks], min_gap=top_total * 0.085,
                      lo=0.0, hi=top_total)
    for (name, raw, color), yy in zip(marks, ys):
        ax.annotate(name, xy=(23.7, raw), xytext=(24.3, yy), xycoords="data",
                    textcoords="data", color=color, fontsize=8.2, va="center",
                    ha="left", annotation_clip=False,
                    arrowprops={"arrowstyle": "-", "color": color, "linewidth": 0.7,
                                "shrinkA": 1.5, "shrinkB": 1.5})
    ax.set_ylabel(st.T("非繰り延べ呼数(件/時)", "answered calls per hour"))
    ax.yaxis.set_major_formatter(lambda v, _p: st.thousands(v))
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.10), ncol=4, handlelength=1.6,
              columnspacing=1.6, borderaxespad=0.0)

    # -- 中: 繰り延べ件数 --
    axb = axes[1]
    axb.bar(hours, deferred, width=0.80, color=st.CAT[7], edgecolor=st.SURFACE,
            linewidth=1.2, zorder=3)
    k = int(np.argmax(deferred))
    axb.annotate(st.thousands(deferred[k]), xy=(hours[k], deferred[k]),
                 xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                 fontsize=8.2, color=st.CAT[7])
    axb.set_ylim(0, max(1.0, float(deferred.max())) * 1.30)
    axb.set_ylabel(st.T("繰り延べ(件/時)", "deferred / hour"))
    axb.yaxis.set_major_formatter(lambda v, _p: st.thousands(v))
    axb.set_title(st.T("応答が返らなかった呼(deferred)の件数",
                       "deferred calls (no response) per hour"), fontsize=10, pad=4)

    # -- 下: 繰り延べ率(右軸にはしない・同じ x を共有する別パネル) --
    axc = axes[2]
    axc.plot(hours, rate, color=st.CAT[7], linewidth=1.8, marker="o", markersize=3.4,
             zorder=3)
    k = int(np.argmax(rate))
    axc.annotate(f"{rate[k]:.2f}%", xy=(hours[k], rate[k]), xytext=(0, 5),
                 textcoords="offset points", ha="center", va="bottom", fontsize=8.2,
                 color=st.CAT[7])
    axc.set_ylim(0, max(0.5, float(rate.max())) * 1.35)
    axc.set_ylabel(st.T("繰り延べ率(%)", "deferred rate (%)"))
    axc.set_title(st.T("繰り延べ率 = 繰り延べ ÷ その時刻の全呼",
                       "deferred rate = deferred / all calls in that hour"),
                  fontsize=10, pad=4)
    axc.set_xlabel(st.T("世界内の時刻(時)", "hour of day"))
    axc.set_xlim(-0.7, 23.7)
    axc.set_xticks(list(range(0, 24, 3)) + [23])

    fig.suptitle(st.T("図2 時刻別の LLM 呼数と起床クラス(c7-day-4・390,067 体×1 シミュ日)",
                      "Fig.2 LLM calls per hour by wake class (c7-day-4, 390,067 agents x 1 sim day)"),
                 x=0.010, y=0.985, ha="left", va="top", fontsize=12, fontweight="bold",
                 color=st.INK)

    per_agent = tot.get("calls_per_agent_day")
    line1 = st.T(
        "総呼数 " + st.thousands(tot["rows"]) + " 件(= 発射数)。うち応答が返った呼 "
        + st.thousands(tot["live"]) + " 件・繰り延べ " + st.thousands(tot["deferred"])
        + " 件(" + f"{tot['deferred_rate'] * 100:.3f}" + "%)。",
        "total calls " + st.thousands(tot["rows"]) + "; answered " + st.thousands(tot["live"])
        + "; deferred " + st.thousands(tot["deferred"])
        + f" ({tot['deferred_rate'] * 100:.3f}%).")
    line2 = st.T(
        "呼/体/日 = 応答が返った呼 ÷ " + (st.thousands(tot["n_agents"]) if tot.get("n_agents") else "?")
        + " 体 = " + (f"{per_agent:.2f}" if per_agent else "?") + "。1 tick = 1 分・1,440 tick = 1 日。",
        "calls per agent-day = answered / " + (st.thousands(tot["n_agents"]) if tot.get("n_agents") else "?")
        + " = " + (f"{per_agent:.2f}" if per_agent else "?") + ". 1 tick = 1 minute, 1,440 ticks = 1 day.")
    line3 = st.T(
        "wake_class = shibuya.core.types.EventClass(昇順が優先)。24×クラスの表は fig2_calls_by_hour.json。",
        "wake_class = shibuya.core.types.EventClass (ascending = higher priority). Table: fig2_calls_by_hour.json.")
    st.note(fig, [line1, line2, line3])
    return fig


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="図2: 時刻別 LLM 呼数と起床クラス")
    ap.add_argument("--tape", default=DEFAULT_TAPE, help="calls.parquet")
    ap.add_argument("--anchors", default=DEFAULT_ANCHORS,
                    help="体数(full_population)の出どころ")
    ap.add_argument("--n-agents", type=int, default=None, help="体数の上書き")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    data = load_calls(args.tape, args.anchors, args.n_agents)
    fig = draw(data)
    paths = st.save(fig, args.out, STEM)
    payload = {
        "schema": "shibuya.tools.fig/calls_by_hour/1",
        "figure": STEM,
        "what": "c7-day-4 の 1 シミュ日ぶんの LLM 呼を時刻×起床クラスで数えた表。",
        "inputs": {"tape": data["input"], "anchors": st.rel(args.anchors)},
        "hours": data["hours"],
        "classes": [{k: v for k, v in c.items() if k != "color"} for c in data["classes"]],
        "live_by_hour_class": data["live_by_hour_class"],
        "live_by_class_total": [int(sum(row[j] for row in data["live_by_hour_class"]))
                                for j in range(len(data["classes"]))],
        "deferred_by_hour": data["deferred_by_hour"],
        "total_by_hour": data["total_by_hour"],
        "deferred_rate_by_hour": data["deferred_rate_by_hour"],
        "deferred_reasons": data["deferred_reasons"],
        "totals": data["totals"],
        "outputs": paths,
    }
    payload["sidecar"] = st.write_sidecar(args.out, STEM, payload)
    print(json.dumps({"outputs": paths, "sidecar": payload["sidecar"],
                      "totals": data["totals"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
