# -*- coding: utf-8 -*-
"""図 5 — 語彙 v1 vs v2(+open_v2)の行動分布と、乗車・休憩の時刻別(AB7c-VOCAB-V2・seed 1)。

何を示すか
    24 語の契約語彙に「食事」を 1 語足した語彙 v2 で、エンジンが受け取る行動語の分布が
    どう変わるか。(a) 3 腕の解決後分布、(b) 乗車の時刻別、(c) 休憩の時刻別(v1 vs v2)。
    第227 親報告(docs/bench/c8/ablation/ab7c_s1_parent_report.md)と第235 診断
    (ab7c_s1_d91_diagnosis.md)の数字を図にしたもの。

解決の手順は既存物をそのまま使う(図 3 と同じ・採点の定義を 2 つ持たない)
    ``parse_two_line(text, vocab_version=腕の版)`` で 2 行形を解き、契約語に直接一致しなければ
    ``map_synonym(raw, vocab_version=腕の版)``(段0 辞書)を引く。どちらでも解けない語は
    ``(未定義)`` として独立の箱に数える(= runner の ``action_counts`` と同じ定義)。

自己検査
    腕ごとの計数を runner 出力 JSON の ``action_counts`` と突き合わせ、語ごとの最大絶対差を
    サイドカー ``runner_check`` に書く(移動・待機は段0 辞書の写像分で数件ずれうる)。

例::

    python tools/fig/fig_ab7c_vocab.py --out docs/bench/figures
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

_HERE = Path(__file__).resolve().parent
REPO_ROOT = _HERE.parents[1]
for _p in (str(_HERE), str(REPO_ROOT / "src"), str(REPO_ROOT / "tools" / "c6")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _style as st  # noqa: E402

DEFAULT_TAPE_ROOT = "data/tape/c8_ab7c_s1"
DEFAULT_ARM = "AB7c-VOCAB-V2"
DEFAULT_RUNNER = "docs/bench/c8/ablation/ablation_AB7c-VOCAB-V2_s1.json"
DEFAULT_OUT = "docs/bench/figures"
STEM = "fig5_ab7c_vocab"

#: 腕(テープの接尾辞)・語彙版・表示・色。色は実体に付く: vocab 系=青 / v2=aqua / open=橙(図 3 と同じ橙)。
ARMS: tuple[dict[str, str], ...] = (
    {"tag": "vocab_v1", "vocab": "v1", "ja": "語彙 v1(24 語・現行)", "en": "vocab v1 (24 words)",
     "color": st.CAT[0]},
    {"tag": "vocab_v2", "vocab": "v2", "ja": "語彙 v2(+食事)", "en": "vocab v2 (+ eat)",
     "color": st.CAT[2]},
    {"tag": "open_v2", "vocab": "v2", "ja": "自由文 + v2 辞書", "en": "open + v2 dictionary",
     "color": st.CAT[1]},
)

#: 時刻別パネルに出す行動語。
HOURLY_WORDS: tuple[str, ...] = ("乗車", "休憩")
#: (a) で並べる語の上限(残りは両腕とも少数)。
MAX_WORDS = 10
HOURS = list(range(24))


def entropy_bits(counts: Mapping[str, float]) -> float:
    """計数辞書のシャノンエントロピー[bits]。**純関数**。"""
    n = float(sum(counts.values()))
    if n <= 0:
        return 0.0
    return -sum((c / n) * math.log2(c / n) for c in counts.values() if c > 0)


def fold_meal(counts: Mapping[str, int]) -> dict[str, int]:
    """「食事」を「購入」に畳んだ計数(v1 の語彙で読むときの対応表)。**純関数**。"""
    out = dict(counts)
    if "食事" in out:
        out["購入"] = out.get("購入", 0) + out.pop("食事")
    return out


# ---------------------------------------------------------------- 読み込み


def analyze_arm(tape_dir: str | Path, vocab_version: str) -> dict[str, Any]:
    """1 腕のテープ → 行動分布・時刻別分布。"""
    from shibuya.engine.tape import Tape
    from shibuya.llm.parser import parse_two_line
    from shibuya.llm.undefined import map_synonym

    rows = list(Tape(Path(tape_dir)).rows())
    live = [r for r in rows if not r.deferred]
    counts: Counter[str] = Counter()
    hourly: dict[str, list[int]] = {w: [0] * 24 for w in HOURLY_WORDS}
    for r in live:
        p = parse_two_line(str(r.response), vocab_version)
        action = p.action
        if action is None:
            raw = (p.raw_action or "").strip()
            mapped, _hint = map_synonym(raw, vocab_version=vocab_version) if raw else (None, "")
            action = mapped or "(未定義)"
        counts[action] += 1
        if action in hourly:
            hourly[action][int(r.tick) // 60 % 24] += 1
    return {
        "n_rows": len(rows),
        "n_live": len(live),
        "deferred": len(rows) - len(live),
        "action_counts": dict(counts),
        "hourly": hourly,
        "entropy_bits": round(entropy_bits(counts), 4),
        "path": st.rel(tape_dir),
    }


def load_ab7c(tape_root: str | Path = DEFAULT_TAPE_ROOT, arm: str = DEFAULT_ARM,
              runner_path: str | Path | None = DEFAULT_RUNNER,
              arms: Sequence[Mapping[str, str]] = ARMS) -> dict[str, Any]:
    """3 腕のテープ → 描画に要るデータ dict(runner との突き合わせつき)。"""
    import c6lib

    per: dict[str, Any] = {}
    for spec in arms:
        tag = str(spec["tag"])
        per[tag] = analyze_arm(Path(tape_root) / f"{arm}__{tag}", str(spec["vocab"]))
        per[tag].update({"ja": spec["ja"], "en": spec["en"], "color": spec["color"],
                         "vocab": spec["vocab"]})

    runner: dict[str, Any] | None = None
    runner_check: dict[str, Any] | None = None
    if runner_path and Path(runner_path).exists():
        doc = json.loads(Path(runner_path).read_text(encoding="utf-8"))
        runs = {r.get("tag"): r for r in doc.get("runs", [])}
        runner = {
            "path": st.rel(runner_path),
            "per_arm": {
                tag: {
                    "llm_calls": runs[tag].get("llm_calls"),
                    "action_counts": runs[tag].get("action_counts"),
                    "format_error_rate_strict": runs[tag].get("format_error_rate_strict"),
                    "meals": runs[tag].get("meals"),
                    "meal_yen": runs[tag].get("meal_yen"),
                    "prompt_tokens_mean": runs[tag].get("prompt_tokens_mean"),
                }
                for tag in per if tag in runs
            },
            "comparisons": doc.get("comparisons"),
        }
        runner_check = {}
        for tag in per:
            if tag not in runs:
                continue
            rc = runs[tag].get("action_counts") or {}
            mine = per[tag]["action_counts"]
            words = set(rc) | set(mine)
            diffs = {w: int(mine.get(w, 0)) - int(rc.get(w, 0)) for w in words}
            runner_check[tag] = {
                "max_abs_diff": max((abs(v) for v in diffs.values()), default=0),
                "diffs_nonzero": {w: d for w, d in diffs.items() if d},
            }

    v1, v2 = per[arms[0]["tag"]], per[arms[1]["tag"]]
    jsd_raw = float(c6lib.jsd_counts(v1["action_counts"], v2["action_counts"]))
    jsd_fold = float(c6lib.jsd_counts(fold_meal(v1["action_counts"]), fold_meal(v2["action_counts"])))

    totals: Counter[str] = Counter()
    for tag in per:
        totals.update(per[tag]["action_counts"])
    words = [w for w, _c in totals.most_common(MAX_WORDS)]
    return {
        "arms": [dict(s) for s in arms],
        "per_arm": per,
        "words_shown": words,
        "words_omitted": [w for w in totals if w not in words],
        "jsd_bits": {"raw": round(jsd_raw, 6), "meal_folded_into_buy": round(jsd_fold, 6)},
        "runner": runner,
        "runner_check": runner_check,
        "inputs": {"tape_root": st.rel(tape_root), "arm": arm},
    }


# ---------------------------------------------------------------- 描画


def draw(data: Mapping[str, Any]):
    """データ dict → Figure。**ファイルを読まない**。"""
    import matplotlib.pyplot as plt

    st.use_style()
    arms = list(data["arms"])
    per = data["per_arm"]
    tags = [str(a["tag"]) for a in arms]
    words = list(data["words_shown"])

    fig = plt.figure(figsize=(12.6, 6.6))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 0.95], height_ratios=[1, 1],
                          left=0.075, right=0.985, top=0.885, bottom=0.20,
                          wspace=0.26, hspace=0.48)
    ax = fig.add_subplot(gs[:, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 1], sharex=ax_b)

    # ---- (a) 3 腕の分布(横棒・グループ) ----
    n = len(tags)
    h = 0.8 / n
    ypos = np.arange(len(words), dtype=float)
    xmax = 1
    for k, tag in enumerate(tags):
        ac = per[tag]["action_counts"]
        vals = [int(ac.get(w, 0)) for w in words]
        xmax = max(xmax, max(vals) if vals else 1)
        off = (k - (n - 1) / 2) * h
        ax.barh(ypos + off, vals, height=h * 0.92, color=per[tag]["color"],
                edgecolor=st.SURFACE, linewidth=1.0, zorder=3,
                label=st.T(per[tag]["ja"], per[tag]["en"]))
        for y, val in zip(ypos + off, vals):
            ax.annotate(st.thousands(val), xy=(val, y), xytext=(3, 0), textcoords="offset points",
                        va="center", ha="left", fontsize=7.2, color=st.INK2, zorder=5)
    ax.set_yticks(ypos)
    ax.set_yticklabels(words)
    ax.invert_yaxis()
    ax.set_xlim(0, xmax * 1.22)
    ax.xaxis.set_major_formatter(lambda v, _p: st.thousands(v))
    ax.set_xlabel(st.T("解決後の呼数(件・1 シミュ日)", "resolved calls per sim-day"))
    ax.grid(axis="y", visible=False)
    ax.set_title(st.T("(a) 行動語の分布(3 腕)", "(a) action words, three arms"), fontsize=10, pad=6)
    ax.legend(loc="lower right", handlelength=1.6)

    # ---- (b)(c) 時刻別(v1 vs v2) ----
    pair = tags[:2]
    for axh, word, title in ((ax_b, HOURLY_WORDS[0], "(b)"), (ax_c, HOURLY_WORDS[1], "(c)")):
        for tag in pair:
            ys = per[tag]["hourly"][word]
            axh.plot(HOURS, ys, color=per[tag]["color"], marker="o", zorder=3,
                     label=st.T(per[tag]["ja"], per[tag]["en"]))
            tot = int(sum(ys))
            axh.annotate(st.T(f"計 {st.thousands(tot)}", f"total {st.thousands(tot)}"),
                         xy=(23, ys[23]), xytext=(4, 0), textcoords="offset points",
                         va="center", ha="left", fontsize=7.6, color=per[tag]["color"])
        axh.set_xlim(0, 24.6)
        axh.set_xticks(range(0, 24, 3))
        axh.xaxis.set_major_formatter(lambda v, _p: f"{int(v):02d}")
        axh.set_ylim(0, None)
        axh.set_title(st.T(f"{title} 「{word}」の時刻別(v1 vs v2)", f"{title} '{word}' by hour (v1 vs v2)"),
                      fontsize=10, pad=6)
        axh.set_ylabel(st.T("件/時", "calls per hour"))
    ax_c.set_xlabel(st.T("時刻(シミュ内)", "hour of sim-day"))
    ax_b.tick_params(labelbottom=False)
    ax_b.legend(loc="upper right", handlelength=1.6)

    fig.suptitle(st.T("図5 語彙に「食事」を 1 語足すと行動分布はどう変わるか(AB7c-VOCAB-V2・seed 1)",
                      "Fig.5 Adding one word (eat) to the vocabulary (AB7c-VOCAB-V2, seed 1)"),
                 x=0.008, y=0.985, ha="left", va="top", fontsize=12, fontweight="bold", color=st.INK)

    jsd = data["jsd_bits"]
    r = data.get("runner") or {}
    meals = ((r.get("per_arm") or {}).get(pair[1]) or {}).get("meals")
    e = {tag: per[tag]["entropy_bits"] for tag in tags}
    meal_line = (st.T(f"実現した食事 {st.thousands(meals)} 回(v2・{meals / 5000:.2f} 回/体/日)。",
                      f"realized meals {st.thousands(meals)} (v2, {meals / 5000:.2f} per agent-day).")
                 if isinstance(meals, (int, float)) and meals else "")
    st.note(fig, [
        st.T(f"v1 vs v2 の行動分布 JSD = {jsd['raw']:.4f} bits。食事を購入に畳むと {jsd['meal_folded_into_buy']:.4f} bits"
             f"(=差の大半は購入→食事の付け替え)。エントロピー " + " / ".join(f"{per[t]['ja'].split('(')[0]} {e[t]:.2f}" for t in tags) + " bits。",
             f"action JSD v1 vs v2 = {jsd['raw']:.4f} bits; folding eat into buy: {jsd['meal_folded_into_buy']:.4f} bits. "
             f"entropy " + " / ".join(f"{t} {e[t]:.2f}" for t in tags) + " bits."),
        st.T("ラン = 5,000 体×1,440 tick(1 シミュ日)・実 LLM(7×Qwen3-8B INT8・温度 0.7)・seed 1・3 腕の呼数 "
             + " / ".join(st.thousands(per[t]["n_live"]) for t in tags) + "。" + meal_line,
             "run = 5,000 agents x 1,440 ticks, real LLM (7x Qwen3-8B INT8, temperature 0.7), seed 1; calls "
             + " / ".join(st.thousands(per[t]["n_live"]) for t in tags) + ". " + meal_line),
        st.T("(b)(c) の乗車半減・休憩倍増の診断は docs/bench/c8/ablation/ab7c_s1_d91_diagnosis.md(図 7)。数値は fig5_ab7c_vocab.json。",
             "diagnosis of (b)(c): docs/bench/c8/ablation/ab7c_s1_d91_diagnosis.md (Fig.7). numbers: fig5_ab7c_vocab.json."),
    ])
    return fig


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="図5: 語彙 v1 vs v2 の行動分布と時刻別(AB7c seed 1)")
    ap.add_argument("--tape-root", default=DEFAULT_TAPE_ROOT)
    ap.add_argument("--arm", default=DEFAULT_ARM)
    ap.add_argument("--runner", default=DEFAULT_RUNNER, help="runner 出力 JSON との突き合わせ(空文字で省略)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    data = load_ab7c(args.tape_root, args.arm, args.runner or None)
    fig = draw(data)
    paths = st.save(fig, args.out, STEM)
    per = data["per_arm"]
    payload = {
        "schema": "shibuya.tools.fig/ab7c_vocab/1",
        "figure": STEM,
        "what": "AB7c-VOCAB-V2 seed 1 の行動語分布(語彙 v1 / v2 / open_v2)と乗車・休憩の時刻別。",
        "inputs": data["inputs"],
        "words_shown": data["words_shown"],
        "words_omitted": data["words_omitted"],
        "jsd_bits": data["jsd_bits"],
        "runner": data["runner"],
        "runner_check": data["runner_check"],
        "arms": {
            tag: {
                "label": per[tag]["ja"],
                "vocab_version": per[tag]["vocab"],
                "path": per[tag]["path"],
                "n_rows": per[tag]["n_rows"],
                "n_live": per[tag]["n_live"],
                "deferred": per[tag]["deferred"],
                "action_counts": per[tag]["action_counts"],
                "entropy_bits": per[tag]["entropy_bits"],
                "hourly": per[tag]["hourly"],
            }
            for tag in per
        },
        "outputs": paths,
    }
    payload["sidecar"] = st.write_sidecar(args.out, STEM, payload)
    print(json.dumps({"outputs": paths, "sidecar": payload["sidecar"], "jsd_bits": data["jsd_bits"],
                      "runner_check": data["runner_check"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
