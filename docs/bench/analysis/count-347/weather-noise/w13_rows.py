# -*- coding: utf-8 -*-
"""数える役 A(weather-noise)・A48: W13 の「引いた日のその時刻の行」が欠けるかを数える(ランはしない)。

ランと同じ読み口で読む: ``World.load_or_synthetic`` → ``PerceptionAssets.load``(住民に見せる天気の語の表=
``weather_by_date_hour``)と ``load_process_assets_or_synthetic``(環境の過程が再生日を引く候補=``weather_dates``)。
再生日の候補(days の表)の各日 × 0〜23 時のうち、知覚の表に行が無いもの(=補いの枝に落ちるもの)を数える。
最頻値の補いの値が、その日その時の実際の値と違う割合も数える(補いが使われたときに語がどれほど変わるかの目安)。

使い方(cwd はリポの根・PYTHONPATH はリポの src):
    python w13_rows.py --world data/world/v2 --out <出力の JSON>
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from shibuya.perception.renderer import PerceptionAssets
    from shibuya.world.assets import load_process_assets_or_synthetic
    from shibuya.world.model.state import World

    wd = Path(args.world)
    world = World.load_or_synthetic(wd, n_cells=139, seed=1)
    pa = PerceptionAssets.load(wd, world)
    proc = load_process_assets_or_synthetic(wd, world.assets)

    by_dh = pa.weather_by_date_hour
    by_hour = pa.weather_by_hour
    dates = list(proc.weather_dates)
    hourly_dates = sorted({d for d, _h in by_dh})
    missing = [(d, h) for d in dates for h in range(24) if (d, h) not in by_dh]
    miss_by_date = Counter(d for d, _h in missing)
    extra_dates = sorted(set(hourly_dates) - set(dates))
    # 補いの値(最頻値)がその日その時の実際の値と違う割合(語の 3 つ組ごと・語ごと)
    diff_triple = 0
    diff_parts = [0, 0, 0]
    n = 0
    for (d, h), val in by_dh.items():
        if d not in dates:
            continue
        mode = by_hour.get(h)
        n += 1
        if mode != val:
            diff_triple += 1
        for k in range(3):
            if mode is None or mode[k] != val[k]:
                diff_parts[k] += 1
    hours_with_mode = sorted(by_hour)
    out = {
        "what": "A48: W13 の再生日の候補 × 0〜23 時のうち、知覚の天気の表に行が無い数(=補いの枝に落ちる数)",
        "world": str(args.world).replace("\\", "/"),
        "n_replay_candidate_dates": len(dates),
        "first_date": dates[0] if dates else "",
        "last_date": dates[-1] if dates else "",
        "n_hourly_rows_in_perception_table": len(by_dh),
        "n_hourly_dates": len(hourly_dates),
        "n_missing_date_hours": len(missing),
        "n_dates_with_missing_hours": len(miss_by_date),
        "missing_by_date_head": dict(sorted(miss_by_date.items())[:20]),
        "dates_in_hourly_not_in_days": extra_dates[:20],
        "n_dates_in_hourly_not_in_days": len(extra_dates),
        "mode_table_hours": hours_with_mode,
        "mode_vs_actual": {
            "n_date_hours": n,
            "n_triple_differs": diff_triple,
            "n_weather_word_differs": diff_parts[0],
            "n_daylight_word_differs": diff_parts[1],
            "n_heat_word_differs": diff_parts[2],
        },
        "has_weather_process_side": bool(proc.has_weather),
        "process_hourly_wbgt_nan": int(
            0 if proc.hourly_wbgt is None else int(__import__("numpy").isnan(proc.hourly_wbgt).sum())
        ),
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k not in ("missing_by_date_head",)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
