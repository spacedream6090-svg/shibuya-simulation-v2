# -*- coding: utf-8 -*-
"""R-86: AB7 seed 1 自由意図の腕の全行(deferred を除く 36,868 行)の行動欄の表層を数える(無作為 300 の補い=珍しい語の一覧)。
使い方: python ab7_surface_counts.py <tape_dir> <out_json>
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "src"))
import pyarrow.parquet as pq  # noqa: E402
from shibuya.llm import parse_two_line  # noqa: E402
from shibuya.llm.undefined import map_synonym  # noqa: E402


def main(tape_dir: str, dst: str) -> None:
    t = pq.read_table(Path(tape_dir) / "calls.parquet", columns=["response", "deferred"])
    c: Counter = Counter()
    for r in t.to_pylist():
        if int(r["deferred"]):
            continue
        p = parse_two_line(r["response"])
        raw = p.raw_action or ""
        if p.action is not None:
            c[(raw, p.action, "vocab")] += 1
        else:
            m, _ = map_synonym(raw)
            c[(raw, m, "stage0" if m else "undefined")] += 1
    rows = [{"raw": a, "mapped": b, "stage": s, "n": n} for (a, b, s), n in c.most_common()]
    out = {"n_rows": sum(c.values()), "n_surfaces": len(rows), "surfaces": rows}
    Path(dst).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(out["n_rows"], out["n_surfaces"])
    for r in rows[:80]:
        print(r)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
