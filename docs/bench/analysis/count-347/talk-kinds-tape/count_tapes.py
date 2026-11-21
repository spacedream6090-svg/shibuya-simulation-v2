# -*- coding: utf-8 -*-
"""count-347 talk-kinds-tape: 9 月の実 LLM のテープ(記録 2-62)の発話と考えの文に混ざった機械向けの記号を数える
(返事その 8 §6-1 の 5)。

テープ(``calls.parquet``・``runtime/inference/tape.py`` の版 1〜4)を探し、応答の行(繰り延べでない・空でない)ごとに、
リポの読み口 ``act.intake.parser.parse_two_line`` で「理由」(=考え)と「ひと言」(=発話)の逐語(切り詰め前)を取り出し、
次を数える。文そのものは出さない(件数・種類・テープごとの総数だけ)。

(a) 出力の欄の語: 判断の出力の型の欄の名(``parser.LABEL_ALIASES_V3`` の表層=正準の 理由・行動・対象・ひと言・活動・まで と
    別名)。「欄の形」=表層の後にコロン(半角・全角)か、【】・[] で囲んだ形。参考に、正準の 5 語(まで を除く)の素の出現も
    別に数える(普通の語としての使い方を含む上限)。
(b) 観測のブロックの見出し: ``[B1 種別]`` などのテンプレの見出しの字面(``foundation.text.templates.TEMPLATES`` から集めた
    もの)・``[B<数字>`` で始まる括弧の見出し・``[憲法]``・素の ``B0``〜``B6``/``B4b``。
(c) チャットの区切りの記号: ``<|…|>`` の形(``<|im_start|>``・``<|im_end|>``・``<|endoftext|>`` ほか)と ``<think>``・
    ``</think>``。

あわせて応答全体(理由・ひと言の外を含む)で (b)(c) の出現と、同じ欄の見出し(欄の形)が 2 回以上出た応答の数を数える。

使い方: python count_tapes.py --root <探す置き場> [--root …] --out <数の JSON> [--skip-dir-name jinryu]
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


def build_patterns() -> dict[str, Any]:
    from shibuya.act.intake import parser as P
    from shibuya.foundation.text import templates as T

    surfaces = sorted(P.LABEL_ALIASES_V3, key=len, reverse=True)
    alt = "|".join(re.escape(s) for s in surfaces)
    label_form = re.compile(r"(?:[【\[]\s*(?P<a>" + alt + r")\s*[】\]])|(?:(?P<b>" + alt + r")\s*[:：])", re.I)
    canon = {s: P.LABEL_ALIASES_V3[s] for s in surfaces}
    heads = set()
    for v in T.TEMPLATES.values():
        for m in re.finditer(r"\[[^\]\n]{1,24}\]", str(v)):
            heads.add(m.group(0))
    head_alt = "|".join(re.escape(h) for h in sorted(heads, key=len, reverse=True))
    return {
        "label_form": label_form,
        "canon": canon,
        "bare": re.compile("|".join(re.escape(w) for w in ("理由", "行動", "対象", "ひと言", "活動"))),
        "head_template": re.compile(head_alt),
        "head_bracket_b": re.compile(r"[\[［]\s*[BＢ]\s*[0-6０-６][bｂ]?(?:[\s\]］]|$)"),
        "head_kenpo": re.compile(r"\[憲法\]"),
        "bare_block_id": re.compile(r"(?<![A-Za-z0-9])B[0-6]b?(?![A-Za-z0-9])"),
        "chat_token": re.compile(r"<\|[^|<>\n]{1,40}\|>"),
        "think_tag": re.compile(r"</?think>", re.I),
        "n_template_heads": len(heads),
        "parse": P.parse_two_line,
    }


def scan_text(pat: dict[str, Any], s: str) -> dict[str, Counter]:
    out: dict[str, Counter] = {"a_label_form": Counter(), "a_bare_word": Counter(), "b_heading": Counter(),
                               "c_chat": Counter()}
    for m in pat["label_form"].finditer(s):
        surf = m.group("a") or m.group("b")
        out["a_label_form"][pat["canon"].get(surf, surf)] += 1
    for m in pat["bare"].finditer(s):
        out["a_bare_word"][m.group(0)] += 1
    # 見出しは重ねて数えない: テンプレの見出し → 残りの [B… の括弧 → 残りの [憲法] → 残りの素の B0〜B6 の順に、数えた分を外す
    n_t = len(pat["head_template"].findall(s))
    if n_t:
        out["b_heading"]["template_heading"] += n_t
    s2 = pat["head_template"].sub(" ", s)
    n_b = len(pat["head_bracket_b"].findall(s2))
    if n_b:
        out["b_heading"]["bracket_B_heading"] += n_b
    s3 = pat["head_bracket_b"].sub(" ", s2)
    n_k = len(pat["head_kenpo"].findall(s3))
    if n_k:
        out["b_heading"]["kenpo_heading"] += n_k
    n_id = len(pat["bare_block_id"].findall(s3))
    if n_id:
        out["b_heading"]["bare_block_id"] += n_id
    for m in pat["chat_token"].finditer(s):
        out["c_chat"][m.group(0)] += 1
    for m in pat["think_tag"].finditer(s):
        out["c_chat"][m.group(0).lower()] += 1
    return out


def vocab_of(path: Path) -> str:
    name = path.parent.name.lower()
    if "vocab_v1" in name:
        return "v1"
    if "v2" in name:
        return "v2"
    return "v1"


def scan_tape(pat: dict[str, Any], calls: Path) -> dict[str, Any]:
    pf = pq.ParquetFile(calls)
    names = pf.schema_arrow.names
    md = pf.schema_arrow.metadata or {}
    version = (md.get(b"shibuya.tape.schema") or b"").decode() or "shibuya.tape/1(印なし)"
    cols = [c for c in ("response", "deferred", "observed_tick", "wake_class") if c in names]
    vocab = vocab_of(calls)
    n_rows = 0
    n_deferred = 0
    n_obs_ge0 = 0
    n_resp = 0
    n_thought = 0
    n_speech = 0
    n_speech_none = 0
    distinct: set[int] = set()
    res = {"thought": {k: Counter() for k in ("a_label_form", "a_bare_word", "b_heading", "c_chat")},
           "speech": {k: Counter() for k in ("a_label_form", "a_bare_word", "b_heading", "c_chat")},
           "whole": {k: Counter() for k in ("a_label_form", "b_heading", "c_chat")}}
    texts_with = {"thought": Counter(), "speech": Counter(), "whole": Counter()}
    dup_label_rows = 0
    dup_label_kinds: Counter = Counter()
    for batch in pf.iter_batches(columns=cols, batch_size=20_000):
        d = batch.to_pydict()
        resp = d["response"]
        dfr = d.get("deferred") or [0] * len(resp)
        obs = d.get("observed_tick")
        for i, r in enumerate(resp):
            n_rows += 1
            if obs is not None and obs[i] is not None and int(obs[i]) >= 0:
                n_obs_ge0 += 1
            if int(dfr[i] or 0) == 1:
                n_deferred += 1
                continue
            if not r:
                continue
            n_resp += 1
            distinct.add(hash(r))
            whole = scan_text(pat, r)
            per_label = whole["a_label_form"]
            if any(v >= 2 for v in per_label.values()):
                dup_label_rows += 1
                for k, v in per_label.items():
                    if v >= 2:
                        dup_label_kinds[k] += 1
            for k in ("a_label_form", "b_heading", "c_chat"):
                res["whole"][k].update(whole[k])
                if whole[k]:
                    texts_with["whole"][k] += 1
            p = pat["parse"](r, vocab)
            th = (p.raw_reason or "").strip()
            sp = (p.raw_comment or "").strip()
            if th:
                n_thought += 1
                got = scan_text(pat, th)
                for k, v in got.items():
                    res["thought"][k].update(v)
                    if v:
                        texts_with["thought"][k] += 1
            if sp:
                if sp in ("なし", "無し", "ナシ", "-", "ー", "—"):
                    n_speech_none += 1
                else:
                    n_speech += 1
                    got = scan_text(pat, sp)
                    for k, v in got.items():
                        res["speech"][k].update(v)
                        if v:
                            texts_with["speech"][k] += 1
    return {
        "schema": version, "vocab_used_for_parse": vocab, "rows": n_rows, "deferred_rows": n_deferred,
        "observed_tick_ge0_rows": n_obs_ge0 if "observed_tick" in names else None,
        "responses": n_resp, "distinct_responses": len(distinct),
        "thought_texts": n_thought, "speech_texts": n_speech, "speech_none": n_speech_none,
        "texts_with": {k: dict(v) for k, v in texts_with.items()},
        "occurrences": {g: {k: dict(v) for k, v in res[g].items()} for g in res},
        "responses_with_repeated_label": dup_label_rows,
        "repeated_label_kinds": dict(dup_label_kinds),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-dir-name", action="append", default=["jinryu"])
    ap.add_argument("--label-root", default="", help="出力の道筋を伏せる根(この根からの相対で書く)")
    a = ap.parse_args(argv)
    pat = build_patterns()
    found: list[Path] = []
    for root in a.root:
        for p in sorted(Path(root).rglob("calls.parquet")):
            if any(part in a.skip_dir_name for part in p.parts):
                continue
            found.append(p)
    base = Path(a.label_root) if a.label_root else None
    tapes = {}
    for p in found:
        key = str(p.parent.relative_to(base)).replace("\\", "/") if base else p.parent.name
        try:
            tapes[key] = scan_tape(pat, p)
        except Exception as e:  # 壊れたテープ(終わりの印が無い等)は読めなかったと書いて次へ
            tapes[key] = {"unreadable": type(e).__name__, "bytes": p.stat().st_size}
            print(key, "unreadable", type(e).__name__, flush=True)
            continue
        print(key, tapes[key]["responses"], flush=True)
    doc = {"about": "9 月の実 LLM のテープの発話(ひと言)と考え(理由)に混ざった機械向けの記号(返事その 8 §6-1 の 5)。文は出さない",
           "n_template_headings": pat["n_template_heads"], "tapes": tapes}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
