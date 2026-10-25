"""1-0 段 FIX(検収 §1 の 9): 外の状態の道筋の宣言の粗さを数える(宣言の数・``*`` の数・宣言上の (系, 道筋) の対と
観測の対)。観測は ``probe_run.py`` の JSON(系ごとの変わった欄)から。直しはしない(1-0 は行を割らない約束)。

使い方(リポの根で): ``python $D/ext_coarse.py <probe の JSON …> --out $D/ext_coarse.json``。絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("probes", nargs="*")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from shibuya.engine.systems import probe as PR
    from shibuya.engine.systems.conductor import path_allowed
    from shibuya.engine.systems.table import SYSTEMS

    rows = [f"{k}:{p}" for k, p in PR._ext_rows()]
    decl = [(s.name, pat) for s in SYSTEMS for pat in sorted(s.writes.paths)]
    star = [d for d in decl if "*" in d[1]]
    pairs = {(s.name, r) for s in SYSTEMS for r in rows if path_allowed(r, s.writes.paths)}
    obs: set[tuple[str, str]] = set()
    for fp in args.probes:
        d = json.loads(Path(fp).read_text(encoding="utf-8"))
        for e in d["entries"]:
            for k in e[3]:
                if ":" in k and not k.startswith(("stats.", "buffers.", "scratch.")):
                    obs.add((e[1], k))
    doc = {
        "format": "shibuya.bench/1-0/ext-coarse/1",
        "probes": [f"{Path(p).parent.name}/{Path(p).name}" for p in args.probes],
        "ledger_ext_rows": len(rows),
        "declarations": len(decl),
        "declarations_with_star": len(star),
        "declared_pairs": len(pairs),
        "observed_pairs": len(obs),
        "observed_outside_declared": sorted(f"{s} {k}" for s, k in obs - pairs),
        "ratio_declared_to_observed": round(len(pairs) / max(1, len(obs)), 2),
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in doc.items() if k != "observed_outside_declared"}, ensure_ascii=False))
    print("outside:", doc["observed_outside_declared"][:10])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
