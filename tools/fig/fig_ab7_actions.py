# -*- coding: utf-8 -*-
"""図 3 — 行動分布 vocab vs open(AB7-OPEN-INTENT・seed 1)。

何を示すか
    LLM に**横断 12 語のホワイトリストを見せる腕(vocab・契約語彙は全 24 語)**と、**自由文で意図を書かせる腕
    (open)**で、エンジンが最終的に受け取る行動語の分布がどう変わるか。左は解決後の
    分布、右は open 腕の**生の表層**が段0 辞書でどこへ落ちたか。

解決の手順は既存物をそのまま使う(採点の定義を 2 つ持たない)
    ``shibuya.llm.parser.parse_two_line`` で 2 行形を解き、契約語に直接一致しなければ
    ``shibuya.llm.undefined.map_synonym``(段0 辞書)を引く。どちらでも解けない語は
    エンジンが段1 で ``待機`` に畳む(``UndefinedActionRegistry.observe`` と同じ扱い)。
    分布・JSD は ``tools/c6/c6lib`` の ``score_texts`` / ``jsd_counts`` を使う。

JSD は 2 通り出す(定義で値が変わるため)
    - ``action_counts``(``(未定義)`` を独立の箱として数える)= runner の ``action_jsd``。
    - ``resolved``(``(未定義)`` を ``待機`` に畳んだあと)。
    図の注記は前者(runner と同じ定義)を使い、両方をサイドカー JSON に書く。

例::

    python tools/fig/fig_ab7_actions.py --out docs/bench/figures
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

DEFAULT_TAPE_ROOT = "data/tape/c8_ab7_s1"
DEFAULT_ARM = "AB7-OPEN-INTENT"
DEFAULT_RUNNER = "docs/bench/c8/ablation/ablation_AB7-OPEN-INTENT_s1.json"
DEFAULT_OUT = "docs/bench/figures"
STEM = "fig3_ab7_actions"

#: 腕の名前(テープの接尾辞)と表示。
ARMS: tuple[dict[str, str], ...] = (
    {"tag": "vocab", "ja": "vocab(横断 12 語を見せる)", "en": "vocab (12-word whitelist)",
     "color": st.CAT[0]},
    {"tag": "open", "ja": "open(自由文の意図)", "en": "open (free-text intent)",
     "color": st.CAT[1]},
)

#: 生の表層を何語まで出すか(右パネル)。
TOP_SURFACES = 10

#: 解決経路の色。「契約語に着地」= open の色 / 「未定義→待機」= 別色(slot 7 violet)。
ROUTE_COLOR: dict[str, str] = {"direct": st.CAT[1], "stage0": st.CAT[1],
                               "undefined": st.CAT[6]}
ROUTE_JA: dict[str, str] = {"direct": "直接", "stage0": "段0", "undefined": "段1"}


def entropy_bits(counts: Mapping[str, float]) -> float:
    """計数辞書のシャノンエントロピー[bits]。**純関数**。"""
    n = float(sum(counts.values()))
    if n <= 0:
        return 0.0
    return -sum((c / n) * math.log2(c / n) for c in counts.values() if c > 0)


# ---------------------------------------------------------------- 読み込み


def analyze_arm(tape_dir: str | Path) -> dict[str, Any]:
    """1 腕のテープ → 行動分布・生表層・解決経路。"""
    import c6lib
    from shibuya.engine.tape import Tape
    from shibuya.llm.parser import parse_two_line
    from shibuya.llm.undefined import map_synonym

    rows = list(Tape(Path(tape_dir)).rows())
    live = [r for r in rows if not r.deferred]
    texts = [str(r.response) for r in live]
    sc = c6lib.score_texts(texts)

    action_counts = Counter(sc["action_counts"])          # (未定義) を含む
    n_undef = int(action_counts.pop("(未定義)", 0))
    resolved = Counter(action_counts)                     # 段1 で 待機 に畳む
    resolved["待機"] += n_undef

    surfaces: Counter[str] = Counter()
    routes: dict[str, dict[str, Any]] = {}
    empty_action = 0
    for r in live:
        p = parse_two_line(str(r.response))
        raw = (p.raw_action or "").strip()
        if not raw:
            empty_action += 1
            surfaces["(空)"] += 1
            routes.setdefault("(空)", {"route": "undefined", "to": "待機"})
            continue
        surfaces[raw] += 1
        if raw in routes:
            continue
        if p.action is not None:
            routes[raw] = {"route": "direct", "to": p.action}
        else:
            mapped, _hint = map_synonym(raw)
            routes[raw] = ({"route": "stage0", "to": mapped} if mapped
                           else {"route": "undefined", "to": "待機"})

    return {
        "n_rows": len(rows),
        "n_live": len(live),
        "deferred": len(rows) - len(live),
        "action_counts": dict(action_counts) | ({"(未定義)": n_undef} if n_undef else {}),
        "resolved": dict(resolved),
        "n_undefined": n_undef,
        "empty_action_rows": empty_action,
        "surfaces": dict(surfaces.most_common()),
        "routes": routes,
        "entropy_resolved_bits": round(entropy_bits(resolved), 4),
        "entropy_excl_undefined_bits": round(entropy_bits(action_counts), 4),
        "format_error_rate": round(float(sc["format_error_rate"]), 6),
        "path": st.rel(tape_dir),
    }


def load_ab7(tape_root: str | Path = DEFAULT_TAPE_ROOT, arm: str = DEFAULT_ARM,
             runner_path: str | Path | None = DEFAULT_RUNNER,
             arms: Sequence[Mapping[str, str]] = ARMS) -> dict[str, Any]:
    """両腕のテープ → 描画に要るデータ dict(比較指標つき)。"""
    import c6lib
    from shibuya.llm.contract import ALL_ACTION_WORDS

    per: dict[str, Any] = {}
    for spec in arms:
        tag = str(spec["tag"])
        per[tag] = analyze_arm(Path(tape_root) / f"{arm}__{tag}")
        per[tag]["ja"] = spec["ja"]
        per[tag]["en"] = spec["en"]
        per[tag]["color"] = spec["color"]

    v, o = per[arms[0]["tag"]], per[arms[1]["tag"]]
    jsd_action = float(c6lib.jsd_counts(v["action_counts"], o["action_counts"]))
    jsd_resolved = float(c6lib.jsd_counts(v["resolved"], o["resolved"]))

    runner: dict[str, Any] | None = None
    if runner_path and Path(runner_path).exists():
        doc = json.loads(Path(runner_path).read_text(encoding="utf-8"))
        cmp0 = (doc.get("comparisons") or [{}])[0]
        runner = {
            "path": st.rel(runner_path),
            "action_jsd": cmp0.get("action_jsd"),
            "null_reference_bits": cmp0.get("null_reference_bits"),
            "exceeds_null": cmp0.get("exceeds_null"),
            "llm_calls": {r.get("tag"): r.get("llm_calls") for r in doc.get("runs", [])},
            "scale": doc.get("scale"),
        }

    words = [w for w in ALL_ACTION_WORDS
             if v["resolved"].get(w, 0) or o["resolved"].get(w, 0)]
    words.sort(key=lambda w: -(v["resolved"].get(w, 0) + o["resolved"].get(w, 0)))
    return {
        "arms": [dict(s) for s in arms],
        "per_arm": per,
        "vocab_size": len(ALL_ACTION_WORDS),
        "words_shown": words,
        "words_all_zero": [w for w in ALL_ACTION_WORDS if w not in words],
        "jsd_bits": {"action_counts": round(jsd_action, 6),
                     "resolved": round(jsd_resolved, 6)},
        "runner": runner,
        "inputs": {"tape_root": st.rel(tape_root), "arm": arm},
    }


# ---------------------------------------------------------------- 描画


def draw(data: Mapping[str, Any]):
    """データ dict → Figure。**ファイルを読まない**。"""
    import matplotlib.pyplot as plt

    st.use_style()
    arms = list(data["arms"])
    per = data["per_arm"]
    a0, a1 = str(arms[0]["tag"]), str(arms[1]["tag"])
    words = list(data["words_shown"])

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 6.2),
                             gridspec_kw={"width_ratios": [1.0, 1.08]}, squeeze=False)
    axes = axes[0]
    fig.subplots_adjust(left=0.072, right=0.985, top=0.880, bottom=0.185, wspace=0.30)

    # ---- 左: 解決後の分布(2 腕を並べる) ----
    ax = axes[0]
    ypos = np.arange(len(words), dtype=float)
    h = 0.36
    xmax = max([1] + [max(per[a0]["resolved"].get(w, 0), per[a1]["resolved"].get(w, 0))
                      for w in words])
    for k, tag in enumerate((a0, a1)):
        vals = [per[tag]["resolved"].get(w, 0) for w in words]
        off = (0.5 - k) * h
        ax.barh(ypos + off, vals, height=h * 0.94, color=per[tag]["color"],
                edgecolor=st.SURFACE, linewidth=1.2, zorder=3,
                label=st.T(per[tag]["ja"], per[tag]["en"]))
        for y, val in zip(ypos + off, vals):
            ax.annotate(st.thousands(val), xy=(val, y), xytext=(4, 0),
                        textcoords="offset points", va="center", ha="left",
                        fontsize=7.8, color=st.INK2, zorder=5)
    ax.set_yticks(ypos)
    ax.set_yticklabels(words)
    ax.invert_yaxis()
    ax.set_xlim(0, xmax * 1.26)
    ax.xaxis.set_major_formatter(lambda v, _p: st.thousands(v))
    ax.set_xlabel(st.T("解決後の呼数(件)", "resolved calls"))
    ax.grid(axis="y", visible=False)
    ax.set_title(st.T("(a) 解決後の行動語の分布(段1 の未定義は 待機 に畳んだあと)",
                      "(a) resolved action words (undefined folded into 待機)"),
                 fontsize=10, pad=6)
    ax.legend(loc="lower right", handlelength=1.6)
    zero = len(data["words_all_zero"])

    # ---- 右: open 腕の生の表層 上位 N と写像先 ----
    ax2 = axes[1]
    open_arm = per[a1]
    top = list(open_arm["surfaces"].items())[:TOP_SURFACES]
    y2 = np.arange(len(top), dtype=float)
    vals = [c for _s, c in top]
    colors = [ROUTE_COLOR[open_arm["routes"][s]["route"]] for s, _c in top]
    ax2.barh(y2, vals, height=0.62, color=colors, edgecolor=st.SURFACE, linewidth=1.2,
             zorder=3)
    xmax2 = max([1] + vals)
    for y, (surface, count) in zip(y2, top):
        r = open_arm["routes"][surface]
        tail = st.T(f"{st.thousands(count)}  → {r['to']}({ROUTE_JA[r['route']]})",
                    f"{st.thousands(count)}  -> {r['to']} ({r['route']})")
        ax2.annotate(tail, xy=(count, y), xytext=(5, 0), textcoords="offset points",
                     va="center", ha="left", fontsize=8.0,
                     color=(st.CAT[6] if r["route"] == "undefined" else st.INK2), zorder=5)
    ax2.set_yticks(y2)
    ax2.set_yticklabels([s for s, _c in top])
    ax2.invert_yaxis()
    ax2.set_xlim(0, xmax2 * 1.52)
    ax2.xaxis.set_major_formatter(lambda v, _p: st.thousands(v))
    ax2.set_xlabel(st.T("生の表層の出現数(件)", "raw surface count"))
    ax2.grid(axis="y", visible=False)
    ax2.set_title(st.T("(b) open 腕の生の表層 上位 10 と、その落ちた先",
                       "(b) open arm: top-10 raw surfaces and where each lands"),
                  fontsize=10, pad=6)
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=st.CAT[1]),
        plt.Rectangle((0, 0), 1, 1, color=st.CAT[6]),
    ]
    ax2.legend(handles,
               [st.T("契約語に着地(直接一致 / 段0 辞書)", "lands on a contract word (direct / stage-0)"),
                st.T("未定義 → 待機(段1)", "undefined -> 待機 (stage-1)")],
               loc="lower right", handlelength=1.6)

    jsd = data["jsd_bits"]["action_counts"]
    null = (data.get("runner") or {}).get("null_reference_bits")
    e0 = per[a0]["entropy_resolved_bits"]
    e1 = per[a1]["entropy_resolved_bits"]
    fig.suptitle(st.T("図3 行動語の分布はホワイトリストを外すとどう変わるか(AB7-OPEN-INTENT・seed 1)",
                      "Fig.3 Action-word distribution with and without the 24-word whitelist (AB7-OPEN-INTENT, seed 1)"),
                 x=0.008, y=0.985, ha="left", va="top", fontsize=12, fontweight="bold",
                 color=st.INK)

    ratio = (f"(帰無 {null} の {jsd / null:.1f} 倍)" if null else "")
    ratio_en = (f"(null {null}, x{jsd / null:.1f})" if null else "")
    st.note(fig, [
        st.T(f"行動分布の JSD = {jsd:.4f} bits {ratio}。エントロピー {e0:.2f} → {e1:.2f} bits。"
             f"vocab {st.thousands(per[a0]['n_live'])} 呼 / open {st.thousands(per[a1]['n_live'])} 呼。",
             f"action JSD = {jsd:.4f} bits {ratio_en}. entropy {e0:.2f} -> {e1:.2f} bits. "
             f"vocab {st.thousands(per[a0]['n_live'])} calls / open {st.thousands(per[a1]['n_live'])} calls."),
        st.T("ラン = 5,000 体×1,440 tick(1 シミュ日)・実 LLM(7×Qwen3-8B INT8・温度 0.7)・seed 1"
             "(出典 docs/bench/c8/ablation/ab7_s1_parent_report.md)。",
             "run = 5,000 agents x 1,440 ticks, real LLM (7x Qwen3-8B INT8, temperature 0.7), seed 1."),
        st.T("段0 辞書 = shibuya.llm.undefined.map_synonym / 段1 = 未定義行動を 待機 に畳むエンジン既定。数値は fig3_ab7_actions.json。",
             "stage-0 dictionary = shibuya.llm.undefined.map_synonym; stage-1 folds undefined into 待機. Numbers: fig3_ab7_actions.json."),
        st.T(f"(a) は残り {zero} 語(全 {data['vocab_size']} 語のうち)を省いた(両腕とも 0 件)。",
             f"(a) omits the remaining {zero} of {data['vocab_size']} words (zero in both arms)."),
    ])
    return fig


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="図3: 行動分布 vocab vs open(AB7 seed 1)")
    ap.add_argument("--tape-root", default=DEFAULT_TAPE_ROOT)
    ap.add_argument("--arm", default=DEFAULT_ARM)
    ap.add_argument("--runner", default=DEFAULT_RUNNER,
                    help="runner 出力 JSON との突き合わせ(空文字で省略)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    data = load_ab7(args.tape_root, args.arm, args.runner or None)
    fig = draw(data)
    paths = st.save(fig, args.out, STEM)
    per = data["per_arm"]
    payload = {
        "schema": "shibuya.tools.fig/ab7_actions/1",
        "figure": STEM,
        "what": "AB7-OPEN-INTENT seed 1 の行動語分布(vocab vs open)と open 腕の生表層。",
        "inputs": data["inputs"],
        "vocab_size": data["vocab_size"],
        "words_shown": data["words_shown"],
        "words_all_zero": data["words_all_zero"],
        "jsd_bits": data["jsd_bits"],
        "runner": data["runner"],
        "arms": {
            tag: {
                "label": per[tag]["ja"],
                "path": per[tag]["path"],
                "n_rows": per[tag]["n_rows"],
                "n_live": per[tag]["n_live"],
                "deferred": per[tag]["deferred"],
                "action_counts": per[tag]["action_counts"],
                "resolved": per[tag]["resolved"],
                "n_undefined": per[tag]["n_undefined"],
                "empty_action_rows": per[tag]["empty_action_rows"],
                "entropy_resolved_bits": per[tag]["entropy_resolved_bits"],
                "entropy_excl_undefined_bits": per[tag]["entropy_excl_undefined_bits"],
                "format_error_rate": per[tag]["format_error_rate"],
                "top_surfaces": [
                    {"surface": s, "count": c,
                     "route": per[tag]["routes"][s]["route"],
                     "to": per[tag]["routes"][s]["to"]}
                    for s, c in list(per[tag]["surfaces"].items())[:20]
                ],
            }
            for tag in (str(a["tag"]) for a in data["arms"])
        },
        "outputs": paths,
    }
    payload["sidecar"] = st.write_sidecar(args.out, STEM, payload)
    print(json.dumps({"outputs": paths, "sidecar": payload["sidecar"],
                      "jsd_bits": data["jsd_bits"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
