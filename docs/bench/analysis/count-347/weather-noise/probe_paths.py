# -*- coding: utf-8 -*-
"""数える役 A(weather-noise)・A48: 環境の過程が無い走らせ方ほかで、天気の補いの枝が通るかを小さなランで確かめる。

``count_run.py`` と同じ包み(``PerceptionAssets.weather``・``Renderer._time_view``)を入れ、``shibuya.cli.run`` を 1 本回す。
体数・刻みは引数で小さくする(補いが通るかは体数に依らない=天気の語は 5 分の帯ごとに 1 回引く)。

使い方(cwd はリポの根・PYTHONPATH はリポの src):
    python probe_paths.py --name <名> --out <JSON> [--world data/world/v2|none] [--no-processes] [--start 2026-09-14]
                          [--weather-perturb] [--agents 200] [--ticks 1440] [--sim-days 1]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--no-processes", action="store_true")
    ap.add_argument("--start", default="")
    ap.add_argument("--weather-perturb", action="store_true")
    ap.add_argument("--agents", type=int, default=200)
    ap.add_argument("--ticks", type=int, default=1440)
    ap.add_argument("--sim-days", type=int, default=1)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import count_run as CR  # 同じ置き場の包み

    CR._install()
    from shibuya import cli

    kw: dict = {"vocab_version": "v3"}
    if args.no_processes:
        kw["processes"] = False
    if args.start:
        kw["start_sim_datetime"] = args.start
    if args.weather_perturb:
        kw["weather_perturb"] = True
    if args.sim_days != 1:
        kw["sim_days"] = int(args.sim_days)
    world = None if args.world.lower() == "none" else args.world
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=world, ticks=args.ticks, **kw)
    man = res.run_manifest_fields()
    payload = {
        "name": args.name,
        "kw": kw,
        "world": "synthetic(None)" if world is None else str(world).replace("\\", "/"),
        "agents": args.agents,
        "ticks": args.ticks,
        "replay_date": str(man.get("replay_date", "")),
        "start_sim_datetime": str(man.get("start_sim_datetime", "")),
        "weather_days": (man.get("weather") or {}).get("days", []),
        "process_ids_n": len(man.get("process_ids") or ()),
        "a48": {
            "weather_calls_loaded": CR.W["calls_loaded"], "weather_fallback_loaded": CR.W["fallback_loaded"],
            "weather_calls_synthetic": CR.W["calls_synthetic"], "weather_fallback_synthetic": CR.W["fallback_synthetic"],
            "fallback_default_tuple": CR.W["fallback_default_tuple"],
            "fallback_keys": dict(sorted(CR.W["fallback_keys"].items())),
            "time_view_path": dict(sorted(CR.TV.items())),
        },
        "wall_s": round(time.perf_counter() - t0, 1),
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("name", "replay_date", "start_sim_datetime", "a48")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
