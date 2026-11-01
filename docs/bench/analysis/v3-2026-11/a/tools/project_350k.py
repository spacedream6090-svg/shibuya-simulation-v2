"""R-130 (a) §2 の表: 系ごとの刻み比例/事象比例と 35 万体への換算(split_fixed_event.py の出力を読むだけ)。

換算の仮定(線形・親の確認用に明記):
- 刻み比例(1 刻みの固定費)= c0 + c1・N(N=500・1,500・5,000 の 3 点の最小二乗)。
- 事象比例 = (5,000 体の事象比例の ms/刻み)× N / 5,000(体あたりの事象の率が 5,000 体の mock と同じと置く)。
- 判断(decide)は呼数に比例するので、c7-day-4 の呼の率(6.94 呼/体/日)でも別に出す(mock は 12.21)。
使い方: python project_350k.py data/bench/v3-2026-11-a/split_t60.json 345858
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    N = int(sys.argv[2]) if len(sys.argv) > 2 else 345_858
    run5k = [r for r in d["runs"] if r["agents"] == 5000][0]
    fit = d["fixed_vs_N"]
    rows = []
    tot_fixed = tot_event = tot_event_c7 = 0.0
    for name, v in sorted(run5k["systems"].items(), key=lambda kv: -kv[1]["ms_per_tick"]):
        if v["ms_per_tick"] <= 0:
            continue
        f5 = v["fixed_ms_per_tick"]
        e5 = max(0.0, v["ms_per_tick"] - f5)
        c = fit.get(name, {})
        fN = max(0.0, c.get("c0_ms", f5) + c.get("c1_ms_per_agent", 0.0) * N)
        eN = e5 * N / 5000
        eN_c7 = eN * (6.94 / 12.21) if name == "decide" else eN
        rows.append({"system": name, "ms_per_tick_5k": round(v["ms_per_tick"], 3), "fixed_5k": round(f5, 3),
                     "event_5k": round(e5, 3), "floor_idle_5k": v["floor_ms_idle_median"],
                     "fixed_share_5k": v["fixed_share"], "fixed_N": round(fN, 1), "event_N": round(eN, 1),
                     "event_N_c7rate": round(eN_c7, 1)})
        tot_fixed += fN
        tot_event += eN
        tot_event_c7 += eN_c7
    out = {"N": N, "rows": rows, "total_fixed_N_ms": round(tot_fixed, 1), "total_event_N_ms": round(tot_event, 1),
           "total_event_N_c7rate_ms": round(tot_event_c7, 1),
           "fixed_share_N": round(tot_fixed / (tot_fixed + tot_event), 4),
           "fixed_share_N_c7rate": round(tot_fixed / (tot_fixed + tot_event_c7), 4)}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
