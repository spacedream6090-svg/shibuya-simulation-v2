"""R-130 (a) §4 の材料: 世界の資産から 1 日の事象の数を数える(読むだけ)。

- W12 の時刻表(``w12_timetables.parquet``): 暦ごとの発車の数 × 時間帯。
- W6 の POI(``w6_poi.parquet``): 営業時間の列があれば開店と閉店の数 × 時間帯。
出力は JSON(標準出力)。封印の層は読まない。
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

BANDS = (("deep_0_6", 0, 6), ("morning_6_10", 6, 10), ("late_morning_10_11", 10, 11), ("noon_11_14", 11, 14),
         ("afternoon_14_17", 14, 17), ("evening_17_23", 17, 23), ("late_23_24", 23, 24))


def band_of(h: int) -> str:
    for name, a, b in BANDS:
        if a <= h < b:
            return name
    return "?"


def main() -> int:
    w = Path(sys.argv[1] if len(sys.argv) > 1 else "data/world/v2")
    out: dict = {}
    t = pq.read_table(w / "w12_timetables.parquet").to_pydict()
    cal = Counter(t["calendar"])
    tt: dict = {}
    for c in cal:
        idx = [i for i, x in enumerate(t["calendar"]) if x == c]
        bands = Counter(band_of((int(t["departure_min"][i]) // 60) % 24) for i in idx)
        lines = Counter(t["line"][i] for i in idx)
        tt[c] = {"departures": len(idx), "lines": len(lines), "by_band": dict(bands),
                 "by_hour": [sum(1 for i in idx if (int(t["departure_min"][i]) // 60) % 24 == h) for h in range(24)]}
    out["timetable"] = tt
    p = pq.read_table(w / "w6_poi.parquet")
    out["poi_columns"] = p.schema.names
    out["poi_rows"] = p.num_rows
    d = p.to_pydict()
    cand_open = [c for c in p.schema.names if "open" in c.lower()]
    cand_close = [c for c in p.schema.names if "close" in c.lower()]
    out["poi_open_cols"] = cand_open
    out["poi_close_cols"] = cand_close
    for c in cand_open + cand_close:
        vals = d[c]
        out.setdefault("poi_hist", {})[c] = Counter(str(v) for v in vals).most_common(12)
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
