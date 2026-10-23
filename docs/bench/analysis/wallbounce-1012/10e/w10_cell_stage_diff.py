"""W10 の騒音段階のセル別の最頻値(エンジンが読む形)を 2 つの資産で比べる(第330 B4 の記録)。

エンジンの集約 ``world.assets._noise_stage_per_cell``(=``perception.renderer._street_aggregate`` と同じ規則)を
そのまま呼ぶ。セルは ``w2_cells.parquet`` の行(ix・iy・band)。

    python docs/bench/analysis/wallbounce-1012/10e/w10_cell_stage_diff.py \\
        --a data/world/v2_pre_10e_2026-10-12 --b data/world/v2 --cells data/world/v2
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from shibuya.world import assets as A


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--cells", default="data/world/v2")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)
    c = pq.read_table(Path(args.cells) / "w2_cells.parquet", columns=["ix", "iy", "band"]).to_pydict()
    ix = np.asarray(c["ix"], dtype=np.int32)
    iy = np.asarray(c["iy"], dtype=np.int32)
    band = np.array([A.BAND_CODES[str(b)] for b in c["band"]], dtype=np.int8)
    da, na = A._noise_stage_per_cell(Path(args.a), ix, iy, band)  # noqa: SLF001
    db, nb = A._noise_stage_per_cell(Path(args.b), ix, iy, band)  # noqa: SLF001
    out = {
        "cells": int(ix.size),
        "day_changed": int((da != db).sum()),
        "night_changed": int((na != nb).sum()),
        "day_sha_a": hashlib.sha256(np.ascontiguousarray(da).tobytes()).hexdigest()[:16],
        "day_sha_b": hashlib.sha256(np.ascontiguousarray(db).tobytes()).hexdigest()[:16],
        "night_sha_a": hashlib.sha256(np.ascontiguousarray(na).tobytes()).hexdigest()[:16],
        "night_sha_b": hashlib.sha256(np.ascontiguousarray(nb).tobytes()).hexdigest()[:16],
        "day_transitions": {
            f"{int(x)}->{int(y)}": int(((da == x) & (db == y)).sum())
            for x in range(4) for y in range(4) if x != y and ((da == x) & (db == y)).any()
        },
        "night_transitions": {
            f"{int(x)}->{int(y)}": int(((na == x) & (nb == y)).sum())
            for x in range(4) for y in range(4) if x != y and ((na == x) & (nb == y)).any()
        },
    }
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8", newline="\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
