# -*- coding: utf-8 -*-
"""R-86: AB7 の自由意図の腕(seed 1)のテープから行動の行を無作為に 300 件抜き、段0 辞書の写像を付ける。

- 読むもの: ``data/tape/c8_ab7_s1/AB7-OPEN-INTENT__open/calls.parquet``(``deferred=1`` の行は除く)。
- 抽出と写像は本番と同じ関数(``llm.parse_two_line`` と ``llm.undefined.map_synonym``・語彙 v1・
  辞書 ``SYNONYMS``=``undefined-synonyms-v2``)。
- 出力 1(リポに置く JSON): 抜いた行の call_id・agent_id・tick・行動欄の逐語・写像先だけ(自由文の原文は入れない)。
- 出力 2(手で読むための TSV・リポの外に置く): 理由・行動・対象・ひと言の原文。

使い方: python ab7_sample.py <tape_dir> <out_json> <out_tsv_outside_repo>
乱数: random.Random(86)。
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "src"))

import pyarrow.parquet as pq  # noqa: E402

from shibuya.llm import parse_two_line  # noqa: E402
from shibuya.llm.undefined import map_synonym, SYNONYM_TABLE_VERSION  # noqa: E402

N = 300
SEED = 86


def field(text: str, label: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(label + ":"):
            return line[len(label) + 1:].strip()
    return ""


def main(tape_dir: str, out_json: str, out_tsv: str) -> None:
    t = pq.read_table(Path(tape_dir) / "calls.parquet",
                      columns=["call_id", "agent_id", "tick", "response", "deferred"])
    rows = [r for r in t.to_pylist() if not int(r["deferred"])]
    stats = {"rows_scored": len(rows), "action_ok": 0, "mapped": 0, "unmapped": 0}
    for r in rows:
        p = parse_two_line(r["response"])
        r["_raw"] = p.raw_action or ""
        r["_ok"] = p.action
        if p.action is not None:
            stats["action_ok"] += 1
            r["_map"] = p.action
            r["_stage"] = "vocab"
        else:
            m, hint = map_synonym(r["_raw"])
            r["_map"] = m
            r["_stage"] = "stage0" if m else "undefined"
            stats["mapped" if m else "unmapped"] += 1
    rng = random.Random(SEED)
    pick = sorted(rng.sample(range(len(rows)), N))
    items = []
    tsv = ["i\tcall_id\traw_action\tmapped\tstage\treason\taction_line\tutterance"]
    for k, idx in enumerate(pick):
        r = rows[idx]
        items.append({"i": k, "row": idx, "call_id": r["call_id"], "agent_id": r["agent_id"],
                      "tick": r["tick"], "raw_action": r["_raw"], "stage0": r["_map"], "stage": r["_stage"]})
        resp = r["response"]
        tsv.append("\t".join([str(k), r["call_id"], r["_raw"], str(r["_map"]), r["_stage"],
                              field(resp, "理由"), field(resp, "行動"), ""]).replace("\n", " "))
    out = {"source": "data/tape/c8_ab7_s1/AB7-OPEN-INTENT__open/calls.parquet", "seed": SEED, "n": N,
           "synonym_table": SYNONYM_TABLE_VERSION, "population": stats, "sample": items}
    Path(out_json).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    Path(out_tsv).write_text("\n".join(tsv) + "\n", encoding="utf-8", newline="\n")
    print(stats)


if __name__ == "__main__":
    main(*sys.argv[1:4])
