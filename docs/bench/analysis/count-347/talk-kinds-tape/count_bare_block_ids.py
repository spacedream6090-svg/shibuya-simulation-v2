# -*- coding: utf-8 -*-
"""count-347 talk-kinds-tape: テープの応答に出た素の B0〜B6(B4b)の後ろの語の種類を数える(文は出さない)。

種類: 見出しの語(テンプレの見出し [Bn 語] の語が続く)/ 助詞(の・に・で・を・が・は・と・から・へ・も・や・より)/
出口(出口・出)/ ほか。数えるのは応答の「理由」の行(1 行目の理由のラベルの後)とそれ以外に分けて。
使い方: python count_bare_block_ids.py --root <置き場> [--root …] --out <数の JSON>
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from shibuya.foundation.text import templates as T

    words: dict[str, set[str]] = {}
    for v in T.TEMPLATES.values():
        for m in re.finditer(r"\[(B[0-6]b?)\s+([^\]\n]{1,12})\]", str(v)):
            words.setdefault(m.group(1), set()).add(m.group(2))
    bare = re.compile(r"(?<![A-Za-z0-9\[])B[0-6]b?(?![A-Za-z0-9])")
    particle = re.compile(r"^\s*(?:の|に|で|を|が|は|と|から|へ|も|や|より)")
    out: Counter = Counter()
    for root in a.root:
        for p in sorted(Path(root).rglob("calls.parquet")):
            if "jinryu" in p.parts:
                continue
            try:
                pf = pq.ParquetFile(p)
            except Exception:
                continue
            for batch in pf.iter_batches(columns=["response"], batch_size=50_000):
                for r in batch.column(0).to_pylist():
                    if not r or "B" not in r:
                        continue
                    first_nl = r.find("\n")
                    for m in bare.finditer(r):
                        where = "reason_line" if (first_nl < 0 or m.start() < first_nl) else "later_lines"
                        rest = r[m.end():m.end() + 14]
                        bid = m.group(0)
                        if any(rest.lstrip().startswith(w) for w in words.get(bid, ())):
                            k = "heading_word"
                        elif particle.match(rest):
                            k = "particle"
                        elif rest.lstrip().startswith("出"):
                            k = "exit"
                        else:
                            k = "other"
                        out[f"{where}|{k}"] += 1
    Path(a.out).write_text(json.dumps(dict(sorted(out.items())), ensure_ascii=False, indent=1), encoding="utf-8")
    print(dict(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
