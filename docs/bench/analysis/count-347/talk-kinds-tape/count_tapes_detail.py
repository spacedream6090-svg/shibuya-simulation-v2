# -*- coding: utf-8 -*-
"""count-347 talk-kinds-tape: ``count_tapes.py`` の続き(9 月の実 LLM のテープ・記録 2-62)。文は出さない。

1. 応答の中で同じ欄の見出し(欄の形)が 2 回以上出たとき、2 回目以降がどこにあるかを数える
   (考えの行=最初の「理由」の後で最初の「行動」より前 / 発話=最初の「ひと言」の後の同じ行 / 発話の行より後の行 /
   そのほか=行動とひと言の間)。
2. 素の ``B0``〜``B6``(``B4b``)の後ろの 1 文字の種類(階・出口の「出」・番・号・ほかの漢字・かな・記号・数字・終わり)
   =見出しの字面か、駅の地下の階や出口の番号のような普通の語かを分けるため。文字そのものは「階」「出」「番」「号」だけ書く。
3. テープの中身の重なり(応答の列の並びの sha256)=同じ応答の列を持つテープを 1 本と数えるため。

使い方: python count_tapes_detail.py --root <置き場> [--root …] --label-root <伏せる根> --out <数の JSON>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label-root", default="")
    ap.add_argument("--skip-dir-name", action="append", default=["jinryu"])
    a = ap.parse_args(argv)

    from shibuya.act.intake import parser as P

    surfaces = sorted(P.LABEL_ALIASES_V3, key=len, reverse=True)
    alt = "|".join(re.escape(s) for s in surfaces)
    label_form = re.compile(r"(?:[【\[]\s*(?P<a>" + alt + r")\s*[】\]])|(?:(?P<b>" + alt + r")\s*[:：])", re.I)
    canon = {s.lower(): P.LABEL_ALIASES_V3[s] for s in surfaces}
    bare_b = re.compile(r"(?<![A-Za-z0-9])B[0-6]b?(?![A-Za-z0-9])")
    think = re.compile(r"<think>.*?</think>", re.S | re.I)

    def next_kind(ch: str) -> str:
        if ch == "":
            return "end"
        if ch in "階出番号":
            return ch
        name = unicodedata.name(ch, "")
        if "CJK UNIFIED" in name:
            return "other_kanji"
        if "HIRAGANA" in name or "KATAKANA" in name:
            return "kana"
        if ch.isdigit():
            return "digit"
        if ch.isspace():
            return "space"
        return "symbol"

    base = Path(a.label_root) if a.label_root else None
    out: dict[str, Any] = {}
    for root in a.root:
        for p in sorted(Path(root).rglob("calls.parquet")):
            if any(part in a.skip_dir_name for part in p.parts):
                continue
            key = str(p.parent.relative_to(base)).replace("\\", "/") if base else p.parent.name
            try:
                pf = pq.ParquetFile(p)
            except Exception as e:
                out[key] = {"unreadable": type(e).__name__}
                continue
            cols = [c for c in ("response", "deferred") if c in pf.schema_arrow.names]
            h = hashlib.sha256()
            rep_region: Counter = Counter()
            bnext: dict[str, Counter] = {"thought": Counter(), "speech": Counter(), "other": Counter()}
            n = 0
            for batch in pf.iter_batches(columns=cols, batch_size=50_000):
                d = batch.to_pydict()
                resp = d["response"]
                dfr = d.get("deferred") or [0] * len(resp)
                for i, r in enumerate(resp):
                    h.update((r or "").encode("utf-8"))
                    h.update(b"\x00")
                    if int(dfr[i] or 0) == 1 or not r:
                        continue
                    n += 1
                    t = think.sub("", r)
                    if "\n" not in t and "\\n" in t:
                        t = t.replace("\\n", "\n")
                    ms = [(canon.get((m.group("a") or m.group("b")).lower(), "?"), m.start(), m.end())
                          for m in label_form.finditer(t)]
                    first: dict[str, tuple[int, int]] = {}
                    for c, s, e in ms:
                        first.setdefault(c, (s, e))
                    r0 = first.get("理由")
                    a0 = first.get("行動")
                    c0 = first.get("ひと言")
                    c_line_end = t.find("\n", c0[1]) if c0 else -1
                    if c0 and c_line_end < 0:
                        c_line_end = len(t)

                    def region(pos: int) -> str:
                        if r0 and pos >= r0[1] and (a0 is None or pos < a0[0]):
                            nl = t.find("\n", r0[1])
                            return "thought_line" if (nl < 0 or pos < nl) else "after_thought_line"
                        if c0 and pos >= c0[1]:
                            return "speech_same_line" if pos < c_line_end else "after_speech_line"
                        return "between_action_and_speech"

                    seen: Counter = Counter()
                    for c, s, e in ms:
                        seen[c] += 1
                        if seen[c] >= 2:
                            rep_region[(c, region(s))] += 1
                    for m in bare_b.finditer(t):
                        nk = next_kind(t[m.end():m.end() + 1])
                        rg = region(m.start())
                        g = "thought" if rg == "thought_line" else ("speech" if rg == "speech_same_line" else "other")
                        bnext[g][nk] += 1
            out[key] = {"responses": n, "response_column_sha256": h.hexdigest(),
                        "repeated_label_region": {f"{c}|{rg}": v for (c, rg), v in sorted(rep_region.items())},
                        "bare_block_id_next_char": {g: dict(v) for g, v in bnext.items()}}
            print(key, n, flush=True)
    groups: dict[str, list[str]] = {}
    for k, v in out.items():
        if "response_column_sha256" in v:
            groups.setdefault(v["response_column_sha256"], []).append(k)
    doc = {"tapes": out, "same_response_column_groups": [g for g in groups.values() if len(g) > 1],
           "n_distinct_response_columns": len(groups)}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
