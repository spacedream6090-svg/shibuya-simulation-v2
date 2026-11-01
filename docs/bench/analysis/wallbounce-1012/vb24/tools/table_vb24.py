"""第 2 期 2-4: byte-check の 2 つの side(``10e/byte_check_10e.py side`` の出力)から段ごとの「動いた量」の表(Markdown)を作る。

    python docs/bench/analysis/wallbounce-1012/vb24/tools/table_vb24.py --a <前の side> --b <後の side> [--only 構成,…]

欄: final(先頭 16 桁)・呼数・呼数の差・気づいた延べ・食事・行動の件数・blocks の行・動いた欄の数(比べる 25 欄のうち)。
最後に呼数の合計の行。絶対パスは書かない(side の JSON は作業用の置き場=git の外)。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

#: 比べる欄(``byte_check_10e.COMPARE_KEYS`` と同じ)。
KEYS = ("final", "calls", "blocks_rows", "blocks_sha", "calls_rows", "calls_column_names", "calls_columns_sha",
        "action_usage_total", "action_usage_sha", "calls_by_condition", "salient_events", "collapse",
        "noticed", "dispatches", "arrived", "mean_delay_min", "meals", "behavior_last", "full_last",
        "end_of_day", "start_sim_datetime", "replay_date", "calendar_weekday", "rng_scheme", "frozen_sources")


def _n(x: int) -> str:
    return f"{int(x):,}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--only", default="")
    a_ns = ap.parse_args(argv)
    A = json.loads(Path(a_ns.a).read_text(encoding="utf-8"))["runs"]
    B = json.loads(Path(a_ns.b).read_text(encoding="utf-8"))["runs"]
    names = [s for s in a_ns.only.split(",") if s] or list(A)
    print("| 構成 | 前 final / 呼数 | 後 final / 呼数 | 呼数の差 | 気づいた延べ | 食事 | 行動の件数 | blocks の行 | 動いた欄 |")
    print("|---|---|---|---|---|---|---|---|---|")
    ta = tb = 0
    for n in names:
        ra, rb = A[n], B.get(n, {})
        if "error" in ra or "error" in rb:
            print(f"| {n} | (エラー) | | | | | | | |")
            continue
        moved = sum(1 for k in KEYS if ra.get(k) != rb.get(k))
        ta += int(ra["calls"])
        tb += int(rb["calls"])
        print(f"| {n} | `{ra['final']}` / {_n(ra['calls'])} | `{rb['final']}` / {_n(rb['calls'])} | "
              f"{int(rb['calls']) - int(ra['calls']):+,} | {_n(ra['noticed'])} → {_n(rb['noticed'])} | "
              f"{_n(ra['meals'])} → {_n(rb['meals'])} | {_n(ra['action_usage_total'])} → {_n(rb['action_usage_total'])} | "
              f"{_n(ra['blocks_rows'])} → {_n(rb['blocks_rows'])} | {moved}/{len(KEYS)} |")
    print(f"| 呼数の合計 | {_n(ta)} | {_n(tb)} | {tb - ta:+,} | | | | | |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
