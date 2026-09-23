# -*- coding: utf-8 -*-
"""図 7 — 語彙 v2 で乗車が半減し休憩が倍増した理由(D-91 (a) 診断・AB7c seed 1 のテープ)。

何を示すか
    (a) 朝 06〜10 時の呼のうち「乗車」を選んだ率を、条件(種別×駅の可視・起床クラス)で切って
    v1 と v2 で並べる。どの条件でも同じ比で薄まる=特定の状況で乗車が消えたのではない。
    (b) 直前の行動が「購入」(v1)/「食事」(v2)/「購入」(v2)だった呼の次手の分布。
    食事のあとは休憩が 3 倍選ばれる=休憩倍増は食後連鎖。

数値の出所
    テープ ``data/tape/c8_ab7c_s1/AB7c-VOCAB-V2__{vocab_v1,vocab_v2}``(calls + blocks)。
    種別は B1 ブロック(「あなたは通勤者です」)、駅の可視は B2 ブロックに「駅」を含むか、
    起床クラスは ``wake_class``(EventClass: 会話 0 / 計画境界 1 / 個体 2 / セル 3)。
    行動語は図 5 と同じ手順(parse_two_line + 段0 辞書)。診断書は
    docs/bench/c8/ablation/ab7c_s1_d91_diagnosis.md。

例::

    python tools/fig/fig_d91_ride_chain.py --out docs/bench/figures
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

_HERE = Path(__file__).resolve().parent
REPO_ROOT = _HERE.parents[1]
for _p in (str(_HERE), str(REPO_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _style as st  # noqa: E402

DEFAULT_TAPE_ROOT = "data/tape/c8_ab7c_s1"
DEFAULT_ARM = "AB7c-VOCAB-V2"
DEFAULT_OUT = "docs/bench/figures"
STEM = "fig7_d91_ride_chain"

ARMS: tuple[dict[str, str], ...] = (
    {"tag": "vocab_v1", "vocab": "v1", "ja": "語彙 v1", "en": "vocab v1", "color": st.CAT[0]},
    {"tag": "vocab_v2", "vocab": "v2", "ja": "語彙 v2(+食事)", "en": "vocab v2 (+ eat)", "color": st.CAT[2]},
)
MORNING = (6, 10)
WAKE_JA = {0: "会話", 1: "計画境界", 2: "個体", 3: "セル"}
WAKE_EN = {0: "conversation", 1: "plan boundary", 2: "individual", 3: "cell"}

#: (a) の条件(順序固定)。
CONDITIONS: tuple[dict[str, Any], ...] = (
    {"key": "commuter_station", "ja": "通勤者 × 駅が見える", "en": "commuter x station visible"},
    {"key": "commuter_nostation", "ja": "通勤者 × 駅が見えない", "en": "commuter x no station"},
    {"key": "wake_0", "ja": "起床: 会話", "en": "wake: conversation"},
    {"key": "wake_1", "ja": "起床: 計画境界", "en": "wake: plan boundary"},
    {"key": "wake_2", "ja": "起床: 個体", "en": "wake: individual"},
    {"key": "wake_3", "ja": "起床: セル", "en": "wake: cell"},
    {"key": "all", "ja": "朝の呼 全体", "en": "all morning calls"},
)

#: (b) の次手の箱と色(実体に付く: 休憩=橙で強調)。
NEXT_WORDS: tuple[str, ...] = ("移動", "休憩", "待機", "購入", "食事", "乗車", "その他")
NEXT_COLOR: dict[str, str] = {"移動": st.CAT[0], "休憩": st.CAT[1], "待機": st.CAT[3], "購入": st.CAT[2],
                              "食事": st.CAT[4], "乗車": st.CAT[6], "その他": st.MUTED}
#: (b) の行: (腕 tag, 直前の行動)。
CHAIN_ROWS: tuple[tuple[str, str], ...] = (("vocab_v1", "購入"), ("vocab_v2", "食事"), ("vocab_v2", "購入"))


def _cond_hit(key: str, row: Mapping[str, Any]) -> bool:
    if key == "all":
        return True
    if key == "commuter_station":
        return row["kind"] == "通勤者" and bool(row["station"])
    if key == "commuter_nostation":
        return row["kind"] == "通勤者" and not row["station"]
    if key.startswith("wake_"):
        return int(row["wc"]) == int(key.split("_")[1])
    raise KeyError(key)


def summarize(rows_by_arm: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    """行(agent/tick/hour/kind/station/wc/action/prev)→ (a)(b) の数。**純関数**。"""
    out: dict[str, Any] = {"conditions": [], "chains": [], "overlap": {}}
    lo, hi = MORNING
    for c in CONDITIONS:
        entry: dict[str, Any] = {"key": c["key"], "ja": c["ja"], "en": c["en"]}
        for tag, rows in rows_by_arm.items():
            mor = [r for r in rows if lo <= int(r["hour"]) <= hi and _cond_hit(c["key"], r)]
            n_ride = sum(1 for r in mor if r["action"] == "乗車")
            entry[tag] = {"n": len(mor), "ride": n_ride,
                          "rate_pct": round(100.0 * n_ride / len(mor), 4) if mor else 0.0}
        out["conditions"].append(entry)
    for tag, prev in CHAIN_ROWS:
        rows = rows_by_arm.get(tag, [])
        nxt = [r for r in rows if r["prev"] == prev]
        cnt: Counter[str] = Counter()
        for r in nxt:
            cnt[r["action"] if r["action"] in NEXT_WORDS else "その他"] += 1
        n = len(nxt)
        out["chains"].append({"tag": tag, "prev": prev, "n": n,
                              "share_pct": {w: round(100.0 * cnt.get(w, 0) / n, 4) if n else 0.0 for w in NEXT_WORDS},
                              "counts": {w: int(cnt.get(w, 0)) for w in NEXT_WORDS}})
    sets = {tag: {int(r["agent"]) for r in rows if r["action"] == "乗車" and lo <= int(r["hour"]) <= hi}
            for tag, rows in rows_by_arm.items()}
    tags = list(sets)
    out["overlap"] = {tag: len(s) for tag, s in sets.items()}
    if len(tags) >= 2:
        out["overlap"]["common"] = len(sets[tags[0]] & sets[tags[1]])
    return out


# ---------------------------------------------------------------- 読み込み


def read_arm(tape_dir: str | Path, vocab_version: str) -> list[dict[str, Any]]:
    """1 腕のテープ → 行の list(agent 昇順・tick 昇順・直前行動つき)。"""
    from shibuya.engine.tape import Tape
    from shibuya.llm.parser import parse_two_line
    from shibuya.llm.undefined import map_synonym

    tape = Tape(Path(tape_dir))
    kind_cache: dict[str, str] = {}
    station_cache: dict[str, bool] = {}
    rows: list[dict[str, Any]] = []
    for r in tape.rows():
        if r.deferred:
            continue
        kind = "?"
        station = False
        for bid in r.block_ids:
            if bid in kind_cache:
                kind = kind_cache[bid]
                continue
            if bid in station_cache:
                station = station_cache[bid]
                continue
            t = tape.block_text(bid)
            if t.startswith("[B1"):
                m = re.search(r"あなたは(.+?)です", t)
                kind_cache[bid] = m.group(1) if m else "?"
                kind = kind_cache[bid]
            elif t.startswith("[B2"):
                station_cache[bid] = "駅" in t
                station = station_cache[bid]
        p = parse_two_line(str(r.response), vocab_version)
        action = p.action
        if action is None:
            raw = (p.raw_action or "").strip()
            mapped, _hint = map_synonym(raw, vocab_version=vocab_version) if raw else (None, "")
            action = mapped or "(未定義)"
        rows.append({"agent": int(r.agent_id), "tick": int(r.tick), "hour": int(r.tick) // 60 % 24,
                     "kind": kind, "station": station, "wc": int(r.wake_class), "action": action})
    rows.sort(key=lambda x: (x["agent"], x["tick"]))
    prev: dict[int, str] = {}
    for x in rows:
        x["prev"] = prev.get(x["agent"], "(初回)")
        prev[x["agent"]] = x["action"]
    return rows


def load_d91(tape_root: str | Path = DEFAULT_TAPE_ROOT, arm: str = DEFAULT_ARM,
             arms: Sequence[Mapping[str, str]] = ARMS) -> dict[str, Any]:
    rows_by_arm = {str(a["tag"]): read_arm(Path(tape_root) / f"{arm}__{a['tag']}", str(a["vocab"])) for a in arms}
    data = summarize(rows_by_arm)
    data["arms"] = [dict(a) for a in arms]
    data["n_live"] = {tag: len(rows) for tag, rows in rows_by_arm.items()}
    data["inputs"] = {"tape_root": st.rel(tape_root), "arm": arm, "morning_hours": list(MORNING)}
    return data


# ---------------------------------------------------------------- 描画


def draw(data: Mapping[str, Any]):
    """データ dict → Figure。**ファイルを読まない**。"""
    import matplotlib.pyplot as plt

    st.use_style()
    arms = list(data["arms"])
    t0, t1 = str(arms[0]["tag"]), str(arms[1]["tag"])
    c0, c1 = str(arms[0]["color"]), str(arms[1]["color"])
    conds = list(data["conditions"])
    chains = list(data["chains"])

    fig = plt.figure(figsize=(12.6, 6.2))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.0], left=0.155, right=0.985, top=0.885,
                          bottom=0.22, wspace=0.42)
    ax = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])

    # ---- (a) 乗車率の dumbbell ----
    y = np.arange(len(conds), dtype=float)
    xmax = 0.0
    for yi, c in zip(y, conds):
        r0, r1 = float(c[t0]["rate_pct"]), float(c[t1]["rate_pct"])
        xmax = max(xmax, r0, r1)
        ax.plot([r1, r0], [yi, yi], color=st.AXIS, linewidth=2.2, zorder=2, solid_capstyle="round")
        ax.plot([r0], [yi], marker="o", markersize=8, color=c0, zorder=4, linestyle="none")
        ax.plot([r1], [yi], marker="o", markersize=8, color=c1, zorder=4, linestyle="none")
        ax.annotate(f"{r0:.1f}%", xy=(r0, yi), xytext=(7, 0), textcoords="offset points", va="center",
                    ha="left", fontsize=8.0, color=c0, zorder=5)
        ax.annotate(f"{r1:.1f}%", xy=(r1, yi), xytext=(-7, 0), textcoords="offset points", va="center",
                    ha="right", fontsize=8.0, color=c1, zorder=5)
        ax.annotate(st.T(f"n {st.thousands(c[t0]['n'])} / {st.thousands(c[t1]['n'])}",
                         f"n {st.thousands(c[t0]['n'])} / {st.thousands(c[t1]['n'])}"),
                    xy=(0, yi), xytext=(-4, -10), textcoords="offset points", va="top", ha="left",
                    fontsize=6.8, color=st.MUTED, annotation_clip=False)
    ax.set_yticks(y)
    ax.set_yticklabels([st.T(c["ja"], c["en"]) for c in conds])
    ax.invert_yaxis()
    ax.set_xlim(0, xmax * 1.35 if xmax else 1)
    ax.xaxis.set_major_formatter(lambda v, _p: f"{v:.0f}%")
    ax.grid(axis="y", visible=False)
    lo, hi = data.get("inputs", {}).get("morning_hours", MORNING)
    ax.set_xlabel(st.T(f"「乗車」を選んだ呼の割合({lo:02d}〜{hi:02d} 時の呼)", f"share of calls choosing 乗車 ({lo:02d}-{hi:02d}h)"))
    ax.set_title(st.T("(a) 朝の乗車率は条件を切っても一様に薄まる", "(a) morning ride rate thins uniformly"),
                 fontsize=10, pad=6)
    ax.plot([], [], marker="o", color=c0, linestyle="none", label=st.T(arms[0]["ja"], arms[0]["en"]))
    ax.plot([], [], marker="o", color=c1, linestyle="none", label=st.T(arms[1]["ja"], arms[1]["en"]))
    ax.legend(loc="lower right", handlelength=1.2)

    # ---- (b) 次手の 100% 積み上げ ----
    yb = np.arange(len(chains), dtype=float)
    arm_ja = {str(a["tag"]): str(a["ja"]) for a in arms}
    arm_en = {str(a["tag"]): str(a["en"]) for a in arms}
    for yi, ch in zip(yb, chains):
        left = 0.0
        for w in NEXT_WORDS:
            v = float(ch["share_pct"].get(w, 0.0))
            if v <= 0:
                continue
            ax_b.barh(yi, v, left=left, height=0.58, color=NEXT_COLOR[w], edgecolor=st.SURFACE,
                      linewidth=1.0, zorder=3)
            if v >= 4.0:
                ax_b.annotate(f"{w} {v:.0f}%" if v >= 9 else f"{v:.0f}%", xy=(left + v / 2, yi), ha="center",
                              va="center", fontsize=7.6,
                              color=(st.SURFACE if w in ("移動", "購入", "乗車", "その他") else st.INK), zorder=5)
            left += v
    ax_b.set_yticks(yb)
    ax_b.set_yticklabels([st.T(f"{arm_ja[ch['tag']]}\n直前 = {ch['prev']}(n {st.thousands(ch['n'])})",
                              f"{arm_en[ch['tag']]}\nprev = {ch['prev']} (n {st.thousands(ch['n'])})") for ch in chains],
                         fontsize=8.4)
    ax_b.invert_yaxis()
    ax_b.set_xlim(0, 100)
    ax_b.xaxis.set_major_formatter(lambda v, _p: f"{v:.0f}%")
    ax_b.grid(axis="y", visible=False)
    ax_b.set_xlabel(st.T("次の呼で選んだ行動の割合", "share of the next call's action"))
    ax_b.set_title(st.T("(b) 食事のあとは休憩が 3 倍選ばれる", "(b) after eating, rest is chosen 3x more"),
                   fontsize=10, pad=24)
    handles = [plt.Rectangle((0, 0), 1, 1, color=NEXT_COLOR[w]) for w in NEXT_WORDS]
    ax_b.legend(handles, [st.T(w, w) for w in NEXT_WORDS], loc="lower center", bbox_to_anchor=(0.5, 1.0),
                ncol=7, handlelength=1.1, columnspacing=1.0, borderaxespad=0.2)

    fig.suptitle(st.T("図7 語彙 v2 で乗車が半減し休憩が倍増した理由(D-91 診断・AB7c seed 1 のテープ)",
                      "Fig.7 Why ridership halved and rest doubled under vocab v2 (D-91 diagnosis, AB7c seed 1)"),
                 x=0.008, y=0.985, ha="left", va="top", fontsize=12, fontweight="bold", color=st.INK)
    ov = data.get("overlap") or {}
    st.note(fig, [
        st.T(f"朝 {lo:02d}〜{hi:02d} 時に乗車を選んだ体: v1 {ov.get(t0, 0)} 体 / v2 {ov.get(t1, 0)} 体 / 共通 {ov.get('common', 0)} 体"
             "=乗車は予定に結びついた行動ではなく呼ごとの散発的な選択。呼数・起床クラス構成は 2 腕で同じ(診断書 §2)。",
             f"agents choosing 乗車 in the morning: v1 {ov.get(t0, 0)} / v2 {ov.get(t1, 0)} / common {ov.get('common', 0)}; "
             "call counts and wake-class mix are identical across arms (diagnosis §2)."),
        st.T("種別 = B1 ブロック・駅の可視 = B2 ブロックに「駅」を含む・起床クラス = wake_class(EventClass)。行動語は図 5 と同じ手順。"
             "B5(空腹)と B6(直前の結果)はテープに無いので条件にできない(限界)。",
             "kind = B1 block; station visible = B2 contains 駅; wake class = EventClass. B5/B6 are not in the tape (limit)."),
        st.T("ラン = 5,000 体×1,440 tick・実 LLM(7×Qwen3-8B INT8)・seed 1。数値は fig7_d91_ride_chain.json・診断書 docs/bench/c8/ablation/ab7c_s1_d91_diagnosis.md。",
             "run = 5,000 agents x 1,440 ticks, real LLM, seed 1. numbers: fig7_d91_ride_chain.json."),
    ])
    return fig


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="図7: D-91 診断(乗車率の条件別・食後連鎖)")
    ap.add_argument("--tape-root", default=DEFAULT_TAPE_ROOT)
    ap.add_argument("--arm", default=DEFAULT_ARM)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    data = load_d91(args.tape_root, args.arm)
    fig = draw(data)
    paths = st.save(fig, args.out, STEM)
    payload = {
        "schema": "shibuya.tools.fig/d91_ride_chain/1",
        "figure": STEM,
        "what": "AB7c seed 1: 朝の乗車率の条件別(v1 vs v2)と、直前行動別の次手分布(食後連鎖)。",
        "inputs": data["inputs"],
        "arms": data["arms"],
        "n_live": data["n_live"],
        "conditions": data["conditions"],
        "chains": data["chains"],
        "overlap": data["overlap"],
        "outputs": paths,
    }
    payload["sidecar"] = st.write_sidecar(args.out, STEM, payload)
    print(json.dumps({"outputs": paths, "sidecar": payload["sidecar"], "overlap": data["overlap"],
                      "all": next(c for c in data["conditions"] if c["key"] == "all")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
