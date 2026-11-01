"""W13 の新旧の行を日付×時で突き合わせる(第330 B5 の記録)。

旧=退避先(35 日・アメダスの JSON が主)・新=年間化(etrn の 10 分値が主)。共通の日付について列ごとに
「同じ/違う」の数を出し、違う行を時の出どころ(旧の ``src``)で分けて数える。07-28 は全行を出す。

    python docs/bench/analysis/wallbounce-1012/10e/w13_rows_diff.py \\
        --old data/world/v2_pre_10e_2026-10-12 --new data/world/v2 \\
        --out docs/bench/analysis/wallbounce-1012/10e/b5_w13_rows_diff.json
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.parquet as pq


def _same(a, b) -> bool:
    if isinstance(a, float) and isinstance(b, float):
        return (math.isnan(a) and math.isnan(b)) or a == b
    return a == b


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--focus", default="2026-07-28")
    args = ap.parse_args(argv)
    oh = pq.read_table(Path(args.old) / "w13_weather_hourly.parquet").to_pylist()
    nh = pq.read_table(Path(args.new) / "w13_weather_hourly.parquet").to_pylist()
    od = {r["date"]: r for r in pq.read_table(Path(args.old) / "w13_weather_days.parquet").to_pylist()}
    nd = {r["date"]: r for r in pq.read_table(Path(args.new) / "w13_weather_days.parquet").to_pylist()}
    new_by = {(r["date"], r["hour"]): r for r in nh}
    cols = [c for c in oh[0] if c not in ("date", "hour")]
    by_col: dict[str, Counter] = defaultdict(Counter)
    by_src: dict[str, Counter] = defaultdict(Counter)
    focus_rows = []
    for r in oh:
        n = new_by.get((r["date"], r["hour"]))
        if n is None:
            by_col["_row_missing_in_new"]["n"] += 1
            continue
        diffs = [c for c in cols if c != "src" and c != "n_samples" and not _same(r[c], n[c])]
        for c in cols:
            by_col[c]["same" if _same(r[c], n[c]) else "diff"] += 1
        by_src[str(r["src"])]["rows_with_value_diff" if diffs else "rows_same_values"] += 1
        if r["date"] == args.focus:
            focus_rows.append({
                "hour": r["hour"], "old_src": r["src"], "new_src": n["src"], "diff_cols": diffs,
                **{f"{c}_old": r[c] for c in diffs}, **{f"{c}_new": n[c] for c in diffs},
            })
    day_cols = [c for c in next(iter(od.values())) if c != "date"]
    day_diff: dict[str, Counter] = defaultdict(Counter)
    day_changes = []
    for d, r in sorted(od.items()):
        n = nd[d]
        dd = [c for c in day_cols if not _same(r[c], n[c])]
        for c in day_cols:
            day_diff[c]["same" if _same(r[c], n[c]) else "diff"] += 1
        if dd:
            day_changes.append({"date": d, **{c: [r[c], n[c]] for c in dd}})
    out = {
        "old_rows": len(oh), "new_rows": len(nh), "common_dates": len(od),
        "hourly_by_column": {k: dict(v) for k, v in sorted(by_col.items())},
        "hourly_value_diff_by_old_src": {k: dict(v) for k, v in sorted(by_src.items())},
        "focus_date": args.focus, "focus_rows": focus_rows,
        "days_by_column": {k: dict(v) for k, v in sorted(day_diff.items())},
        "days_changed": day_changes,
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("old_rows", "new_rows", "hourly_value_diff_by_old_src", "days_by_column")}, ensure_ascii=False, default=str))
    print("focus rows with diff:", sum(1 for r in focus_rows if r["diff_cols"]), "/", len(focus_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
