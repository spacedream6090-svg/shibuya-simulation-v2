# -*- coding: utf-8 -*-
"""A48(第347): 世界の資産の置き場ごとに、W13 の日の表(``w13_weather_days``)のどの日も、時の表(``w13_weather_hourly``)に
0〜23 時の行がそろうかを数える(A48 の後は欠けた行を引くと止まる=止まる置き場が無いかの確かめ)。読むのは日付と時の列だけ。

使い方(cwd は木の根): ``python w13_days_hours.py <出力の JSON>``(``data/world/*/`` の両方の表がある置き場だけを見る)。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pyarrow.parquet as pq


def main() -> int:
    out = []
    for d in sorted(Path("data/world").glob("*/")):
        fd, fh = d / "w13_weather_days.parquet", d / "w13_weather_hourly.parquet"
        if not (fd.exists() and fh.exists()):
            continue
        days = [str(x)[:10] for x in pq.read_table(fd, columns=["date"]).column("date").to_pylist()]
        h = pq.read_table(fh, columns=["date", "hour"]).to_pydict()
        have = {(str(a)[:10], int(b)) for a, b in zip(h["date"], h["hour"])}
        miss = sum(1 for x in days for hh in range(24) if (x, hh) not in have)
        out.append({"dir": d.name, "days": len(days), "first": min(days), "last": max(days),
                    "missing_day_hours": miss, "hourly_days_not_in_days": len({k[0] for k in have} - set(days))})
    Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for r in out:
        print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
