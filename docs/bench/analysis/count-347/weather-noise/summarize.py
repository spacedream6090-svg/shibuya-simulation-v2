# -*- coding: utf-8 -*-
"""数える役 A(weather-noise): ``runs/*.json``(count_run.py の出力)と ``probes/*.json``(probe_paths.py の出力)を
1 本の要約(summary.json)にまとめ、報告の表の行を標準出力に出す(標準ライブラリだけ)。

使い方: python summarize.py --dir <この置き場> [--bytecheck-side <byte-check の side の JSON=final を突き合わせる>]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ORDER = (
    "w6_v3_default", "w6_v3_activity_off", "w6_v1_default", "w6_v1_derive_v2_1", "w6_v2", "w6_v1_edge", "w6_v2_edge",
    "w6_v1_edge_plateau", "w6_old_v1_default", "w6_old_v1_derive_v2_1", "w6_old_v2", "w6_old_v1_edge", "w6_old_v2_edge",
    "w6_old_v1_edge_plateau", "w6_golden_null_arm", "v3_mem_store", "v3_mem_rel", "v3_classical", "v3_classical_mem_rel",
)
KEYS = ("agents_in_cells", "dropped_before_arbiter", "suppressed_sleep", "suppressed_refractory", "suppressed_outside",
        "woken_called", "woken_called_alone", "woken_called_with_other_rows", "deferred")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--bytecheck-side", default="")
    args = ap.parse_args()
    base = Path(args.dir)
    rec = {}
    if args.bytecheck_side:
        rec = json.loads(Path(args.bytecheck_side).read_text(encoding="utf-8"))["runs"]
    rows = []
    for c in ORDER:
        p = base / "runs" / f"{c}.json"
        if not p.is_file():
            rows.append({"config": c, "missing": True})
            continue
        j = json.loads(p.read_text(encoding="utf-8"))
        row = {"config": c, "final16": j["final16"], "calls": j["llm_calls"],
               "final_matches_bytecheck": (rec[c]["final"] == j["final16"]) if c in rec else None,
               "calls_matches_bytecheck": (rec[c]["calls"] == j["llm_calls"]) if c in rec else None,
               "replay_date": j["replay_date"], "a48": j["a48"],
               "cell_block_calls": j["calls_by_condition"].get("CELL_BLOCK", 0), "a49": {}}
        for t, v in j["a49"]["by_tick"].items():
            ar = v.get("arbiter", {})
            tot = {k: sum(int(ar.get(g, {}).get(k, 0)) for g in ("only", "mixed")) for k in KEYS}
            row["a49"][t] = {"cells_noise_changed": v["cells_noise_changed"], "cells_noise_only": v["cells_noise_only"],
                             "cells_noise_and_other": v["cells_noise_and_other"],
                             "total": tot, "only": {k: ar.get("only", {}).get(k) for k in KEYS},
                             "mixed": {k: ar.get("mixed", {}).get(k) for k in KEYS},
                             "other_conditions_of_overlap": ar.get("only", {}).get("other_conditions_of_overlap", {})}
        rows.append(row)
    probes = []
    for p in sorted((base / "probes").glob("*.json")):
        j = json.loads(p.read_text(encoding="utf-8"))
        probes.append({"name": j["name"], "kw": j["kw"], "world": j["world"], "replay_date": j["replay_date"],
                       "start_sim_datetime": j["start_sim_datetime"], "a48": j["a48"]})
    out = {"what": "A48・A49 の数(count_run.py・probe_paths.py の出力の要約)", "configs": rows, "probes": probes}
    (base / "summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in rows:
        if r.get("missing"):
            print(f"| {r['config']} | (無い) |")
            continue
        a = r["a48"]
        x = r["a49"].get("360", {}).get("total", {})
        y = r["a49"].get("1320", {}).get("total", {})
        # 「騒音だけ」=騒音の欄だけが変わったマス(only)にいて、同じ刻みにほかの起床の行が無く、呼ばれた体。
        # 騒音とほかの欄が一緒に変わったマス(mixed)の体は、呼ばれても「重なり」に数える。
        xa = r["a49"].get("360", {}).get("only", {}).get("woken_called_alone", 0) or 0
        ya = r["a49"].get("1320", {}).get("only", {}).get("woken_called_alone", 0) or 0
        xw = x.get("woken_called", 0) or 0
        yw = y.get("woken_called", 0) or 0
        print(f"| {r['config']} | {a['weather_calls_loaded']} | {a['weather_fallback_loaded'] + a['weather_fallback_synthetic']} | "
              f"{x.get('agents_in_cells')} | {xw} | {xa} | {xw - xa} | "
              f"{y.get('agents_in_cells')} | {yw} | {ya} | {yw - ya} | "
              f"{xw + yw} | {xa + ya} | {r['cell_block_calls']} | "
              f"{'一致' if r['final_matches_bytecheck'] else r['final_matches_bytecheck']} |")
    for p in probes:
        a = p["a48"]
        print(p["name"], p["replay_date"], a["weather_calls_loaded"], a["weather_fallback_loaded"],
              a["weather_calls_synthetic"], a["weather_fallback_synthetic"], a["time_view_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
