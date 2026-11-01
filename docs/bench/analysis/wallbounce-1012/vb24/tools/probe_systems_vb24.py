"""第 2 期 2-4: 系ごとの指紋(ec21 の ``tools/probe_ec21.py side`` の JSON 2 つ)から「動いた系の一覧」を作る。

``probe_ec21.py compare`` は最初の食い違いだけを出すので、本道具は全部の刻みの (T, 系, 変わった欄の digest) を並べて、
系ごとに食い違った刻みの数・最初の刻み・食い違った欄の名を数える(前の段の値は切替口で再現=同じ src の 2 つの side)。

    python docs/bench/analysis/wallbounce-1012/vb24/tools/probe_systems_vb24.py --a <前の side> --b <後の side> --out <JSON>
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def _entries(doc: dict, name: str) -> list:
    return doc["runs"][name]["entries"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--out", required=True)
    a_ns = ap.parse_args(argv)
    A = json.loads(Path(a_ns.a).read_text(encoding="utf-8"))
    B = json.loads(Path(a_ns.b).read_text(encoding="utf-8"))
    out: dict = {"a": A.get("label"), "b": B.get("label"), "runs": {}}
    for name in A["runs"]:
        ea, eb = _entries(A, name), _entries(B, name)
        by_sys: dict[str, dict] = defaultdict(lambda: {"ticks_differ": 0, "first_T": None, "keys": set()})
        def keyed(es: list) -> dict:
            seen: dict = defaultdict(int)
            out_: dict = {}
            for x in es:  # (T, 系, 変わった欄の digest, 変わった欄の名)=同じ (T, 系) は出た順に番号
                k = (x[0], x[1], seen[(x[0], x[1])])
                seen[(x[0], x[1])] += 1
                out_[k] = (x[2], tuple(x[3]) if len(x) > 3 else ())
            return out_

        ka_, kb_ = keyed(ea), keyed(eb)
        for k in sorted(set(ka_) | set(kb_), key=lambda z: (int(z[0]), str(z[1]), z[2])):
            va, vb = ka_.get(k), kb_.get(k)
            if va == vb:
                continue
            s = by_sys[k[1]]
            s["ticks_differ"] += 1
            if s["first_T"] is None:
                s["first_T"] = k[0]
            fa = set(va[1]) if va else set()
            fb = set(vb[1]) if vb else set()
            s["keys"] |= (fa ^ fb) or fa or fb
        out["runs"][name] = {
            "final_a": A["runs"][name]["final"], "final_b": B["runs"][name]["final"],
            "calls_a": A["runs"][name]["calls"], "calls_b": B["runs"][name]["calls"],
            "n_entries": [len(ea), len(eb)],
            "systems_moved": {k: {"ticks_differ": v["ticks_differ"], "first_T": v["first_T"],
                                  "keys": sorted(v["keys"])} for k, v in sorted(by_sys.items())},
        }
    Path(a_ns.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    for name, r in out["runs"].items():
        print(name, r["final_a"][:16] if r["final_a"] else "", "→", r["final_b"][:16] if r["final_b"] else "",
              {k: v["ticks_differ"] for k, v in r["systems_moved"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
