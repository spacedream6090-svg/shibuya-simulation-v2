"""W13 の年間化(第330 B5)の検算: etrn の 10 分値とアメダスの JSON(35 日)を 10 分ごとに突き合わせる。

同じ観測(東京・北の丸公園=アメダス 44132=etrn の 47662)なら一致するはず(材料 §4-3 の推測)。
列: 気温・相対湿度・平均風速・10 分間降水量・10 分間日照時間(分)。etrn の値の記号は
``w13_weather._etrn_num`` で解く(``--``=現象なし=0)。日照の空欄(夜)はアメダスの値と並べて数える。

    python docs/bench/analysis/wallbounce-1012/10e/w13_amedas_crosscheck.py --data data \\
        --out docs/bench/analysis/wallbounce-1012/10e/b5_w13_amedas_crosscheck.json
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from collections import Counter, defaultdict
from pathlib import Path

from shibuya.build.field import w13_weather as W13

#: アメダスの JSON の値の名前 → etrn の 10 分値の CSV の列。
PAIRS = (
    ("temp", "temp_c"),
    ("humidity", "rh_pct"),
    ("wind", "wind_ms"),
    ("precipitation10m", "precip_mm"),
    ("sun10m", "sunshine_min"),
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    data = Path(args.data)
    etrn: dict[tuple[str, str], dict[str, str]] = {}
    csv_path = data / "realworld" / "jma_etrn" / "tokyo47662_10min_2025-09-01_2026-08-31.csv"
    with csv_path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            d = dt.date.fromisoformat(row["date"])
            hh, mm = row["time"].split(":")
            if hh == "24":  # 24:00 は翌日の 00:00
                d, hh = d + dt.timedelta(days=1), "00"
            etrn[(d.isoformat(), f"{hh}:{mm}")] = row
    files = sorted((data / "realworld" / "amedas").rglob("amedas_*.json"))
    n_rec = 0
    missing_in_etrn = []
    by_col: dict[str, Counter] = defaultdict(Counter)
    mismatch_rows: list[dict] = []
    blank_sun_vs_amedas: Counter = Counter()
    for p in files:
        doc = json.loads(p.read_text(encoding="utf-8"))
        date = str(doc["_meta"]["date_jst"])
        if not ("2025-09-01" <= date <= "2026-08-31"):
            continue
        for rec in doc["data"]:
            key = (date, str(rec["obs_time_jst"])[11:16])
            n_rec += 1
            e = etrn.get(key)
            if e is None:
                missing_in_etrn.append("T".join(key))
                continue
            for a_name, e_col in PAIRS:
                av = rec["values"].get(a_name)
                raw = e[e_col]
                ev = W13._etrn_num(raw)
                if e_col == "sunshine_min" and (raw or "").strip() == "":
                    blank_sun_vs_amedas[repr(av)] += 1
                same = (av is None and ev is None) or (
                    av is not None and ev is not None and abs(float(av) - float(ev)) < 1e-9
                )
                by_col[e_col]["same" if same else "diff"] += 1
                if not same and len(mismatch_rows) < 200:
                    mismatch_rows.append({"at": "T".join(key), "col": e_col, "amedas": av, "etrn_raw": raw})
    out = {
        "what": "etrn 10 分値 × アメダス JSON の突き合わせ(10 分ごと)",
        "amedas_files": len(files),
        "amedas_records_in_window": n_rec,
        "records_missing_in_etrn": missing_in_etrn[:50],
        "by_column": {k: dict(v) for k, v in sorted(by_col.items())},
        "etrn_blank_sunshine_vs_amedas_value": dict(blank_sun_vs_amedas),
        "mismatch_rows_first_200": mismatch_rows,
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("amedas_files", "amedas_records_in_window", "by_column", "etrn_blank_sunshine_vs_amedas_value")}, ensure_ascii=False))
    print("mismatches:", len(mismatch_rows), mismatch_rows[:10])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
