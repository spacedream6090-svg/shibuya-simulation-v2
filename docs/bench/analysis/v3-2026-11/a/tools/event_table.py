"""R-130 (a) §4 の表: 35 万体の 1 日の事象の数(種類 × 時間帯)。measure_core.py・count_world_events.py などの出力を読むだけ。

時間帯: 深夜 0〜6 時・朝 6〜10 時・昼 11〜14 時・夕夜 17〜23 時・その他(10〜11・14〜17・23〜24 時)。
体の数に比例する事象は mock 5,000 体の値 × (345,858 ÷ 5,000) で換算する(線形の仮定)。
使い方: python event_table.py data/bench/v3-2026-11-a > event_table.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

N = 345_858
SCALE = N / 5_000
BANDS = {"deep_0_6": range(0, 6), "morning_6_10": range(6, 10), "noon_11_14": range(11, 14),
         "evening_17_23": range(17, 23), "other_10_11_14_17_23_24": [10, 14, 15, 16, 23]}
SIGNAL_POINTS = 208          # R-82 §4: OSM highway=crossing のうち crossing=traffic_signals(W1 の bbox)
SIGNAL_CYCLE_S = 120         # 仮の値(未リサーチ・expedient)
SIGNAL_CHANGES_PER_CYCLE = 3  # 仮の値(青→点滅→赤→青のうち 3 つの切り替え・未リサーチ)


def bands(by_hour, scale=1.0):
    out = {k: round(sum(by_hour[h] for h in hs) * scale) for k, hs in BANDS.items()}
    out["total"] = round(sum(by_hour) * scale)
    return out


def main() -> int:
    d = Path(sys.argv[1])
    m = json.loads((d / "n5000_t60.json").read_text(encoding="utf-8"))
    dg = m["by_hour_diag"]
    wc = json.loads((d / "tape_n5000_wake_class.json").read_text(encoding="utf-8"))["wake_class_by_hour"]
    w17 = json.loads((d / "w17_events.json").read_text(encoding="utf-8"))["day0"]
    we = json.loads((d / "world_events.json").read_text(encoding="utf-8"))
    op = json.loads((d / "opening_events.json").read_text(encoding="utf-8"))["monday"]
    rows = {}
    rows["area_enter_W17"] = bands(w17["enter_by_hour"])
    rows["area_leave_W17"] = bands(w17["leave_by_hour"])
    rows["plan_block_boundaries_W17"] = bands(w17["boundaries_by_hour"])
    rows["walk_arrivals_mock_x69"] = bands(dg["arrived"], SCALE)
    rows["llm_calls_mock_x69"] = bands(dg["calls"], SCALE)
    rows["llm_calls_scheduled_planclass_mock_x69"] = bands(wc["1"], SCALE)
    rows["llm_calls_reactive_individual_mock_x69"] = bands(wc["2"], SCALE)
    rows["llm_calls_reactive_cell_mock_x69"] = bands(wc["3"], SCALE)
    rows["llm_calls_conversation_turn_mock_x69"] = bands(wc["0"], SCALE)
    rows["responses_applied_mock_x69"] = bands(dg["pending_apply"], SCALE)
    rows["conversation_acts_mock_x69"] = bands(dg["conversations"], SCALE)
    rows["conversations_opened_mock_x69"] = bands(dg["conversations_opened"], SCALE)
    rows["purchases_mock_x69"] = bands(dg["purchases"], SCALE)
    rows["intents_mock_x69"] = bands(dg["intents"], SCALE)
    rows["wake_candidates_system1_mock_x69"] = bands(dg["candidates"], SCALE)
    rows["walker_ticks_mock_x69"] = bands(dg["moved"], SCALE)
    rows["train_departures_weekday_W12"] = bands(we["timetable"]["Weekday"]["by_hour"])
    rows["shop_open_W7_monday"] = bands(op["opens_by_hour"])
    rows["shop_close_W7_monday"] = bands(op["closes_by_hour"])
    sig_per_hour = SIGNAL_POINTS * (3600 / SIGNAL_CYCLE_S) * SIGNAL_CHANGES_PER_CYCLE
    rows["signal_changes_assumed"] = bands([sig_per_hour] * 24)
    print(json.dumps({"N": N, "scale": SCALE, "bands": {k: list(v) if not isinstance(v, range) else list(v)
                                                       for k, v in BANDS.items()}, "rows": rows,
                      "signal_assumption": {"points": SIGNAL_POINTS, "cycle_s": SIGNAL_CYCLE_S,
                                            "changes_per_cycle": SIGNAL_CHANGES_PER_CYCLE}},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
