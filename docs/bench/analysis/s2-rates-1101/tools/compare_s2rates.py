"""11-01 段 2 の 3・4: 率の形の規則を外す前後の 5,000 体 × 1 日 mock の比べ(既定の CLI の引数・seed 1)。

使い方(リポの根で・PYTHONPATH に比べたい版の src):
    python docs/bench/analysis/s2-rates-1101/tools/compare_s2rates.py --label after --out <出力.json> [--rate-rules legacy]

``cli.main`` を ``--llm mock`` だけで回し(他は CLI の既定)、``cli.run`` の結果を受け取って数える。``--rate-rules`` は
今の版だけが持つ切替口(前の版のコードでは渡さない)。出力は JSON(絶対パスを書かない=ファイル名だけ)。

数えるもの: final(behavior-hash の先頭)・呼数・壁時計・到着の分布(鉄道で着く在圏ブロックの到着の時刻の時別・E1 便との
|便差|)・催しの人出(注入した体の数)・乗り残し(延べと確率で断られた数)・ごみ(街路ごみの発生と掃いた量・廃棄のビンの行・
当日の sink)・宅配(配達した個数)・倒れた人(事象と出動)・manifest の rate_rules(今の版だけ)。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rate-rules", default=None, choices=("off", "legacy"))
    a = ap.parse_args()

    from shibuya import cli

    box: dict = {}
    real = cli.run

    def _keep(*args, **kw):
        res = real(*args, **kw)
        box["res"] = res
        return res

    cli.run = _keep
    argv = ["--llm", "mock"] + (["--rate-rules", a.rate_rules] if a.rate_rules else [])
    t0 = time.perf_counter()
    cli.main(argv)
    wall = time.perf_counter() - t0
    res = box["res"]
    pc = dict(res.process_counters)
    runner = res.runner
    pr = getattr(runner, "presence", None)
    out: dict = {
        "label": a.label,
        "argv": argv,
        "final_hash16": str(res.final_hash)[:16],
        "llm_calls": int(res.llm_calls),
        "wall_seconds": round(wall, 1),
    }
    if pr is not None:
        tr = np.asarray(pr.arrival_train, dtype=np.int64)
        e1 = np.asarray(getattr(pr, "arrival_train_e1", tr), dtype=np.int64)
        rail_ok = tr >= 0
        arr_min = np.asarray(pr.arrival_tick, dtype=np.int64)[rail_ok]
        hours = np.bincount(np.clip(arr_min // 60, 0, 23), minlength=24)
        # E1 便との |便差|(便の索引の差=同じ線の時刻順の位置の差とは限らないので、到着の分の差も出す)
        enter = np.asarray(runner.rail.enter_tick, dtype=np.int64)
        dmin = (enter[tr[rail_ok]] - enter[e1[rail_ok]]) if rail_ok.any() else np.zeros(0, dtype=np.int64)
        out["arrivals"] = {
            "rail_blocks": int(rail_ok.sum()),
            "gate_blocks": int((~rail_ok).sum()),
            "moved_from_e1": int(np.count_nonzero(tr[rail_ok] != e1[rail_ok])),
            "minutes_vs_e1_min": int(dmin.min()) if dmin.size else 0,
            "minutes_vs_e1_max": int(dmin.max()) if dmin.size else 0,
            "minutes_vs_e1_mean": round(float(dmin.mean()), 3) if dmin.size else 0.0,
            "by_hour": hours.tolist(),
            "spread_moved": int(pr.n_spread_moved),
            "spread_overflow": int(pr.n_spread_overflow),
            "absent": int(np.count_nonzero(pr.absent)),
            "in_area_03_09_12": [pr.in_area_by_hour[h] for h in (3, 9, 12)],
        }
    keys = ("large_event.arrived", "large_event.left", "large_event.venues", "rail.board_applicants",
            "rail.left_behind", "rail.left_behind_by_rate", "street_cleaning.litter_generated_g",
            "street_cleaning.swept_g", "street_cleaning.litter_now_g", "waste.to_bin_rows", "waste.collected_g",
            "waste.day_waste_g", "waste.consumed", "last_mile.planned", "last_mile.delivered", "last_mile.batches",
            "salient.collapse", "salient.collapse_rate_per_10k", "salient.events", "salient.noticed",
            "actual_log.rows")
    out["counters"] = {k: pc.get(k) for k in keys}
    disp = getattr(runner, "dispatch", None)
    out["dispatch"] = {"dispatched": int(getattr(disp, "n_dispatched", 0)), "arrived": int(getattr(disp, "n_arrived", 0))}
    try:
        out["waste_t_per_day"] = round(float(runner.waste.projected_tonnes_per_day(runner.street_cleaning.swept_g)), 6)
    except Exception as e:  # 前の版でも同じ口(報告だけ)
        out["waste_t_per_day"] = f"n/a: {type(e).__name__}"
    m = res.run_manifest_fields()
    out["manifest_rate_rules"] = m.get("rate_rules")
    out["manifest_has_attendance_rate"] = "attendance_rate" in m
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{a.label}: final {out['final_hash16']} 呼 {out['llm_calls']:,} 壁 {out['wall_seconds']} 秒 → {Path(a.out).name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
