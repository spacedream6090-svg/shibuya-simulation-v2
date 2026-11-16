# -*- coding: utf-8 -*-
"""A48(第347)の後の数え直し: 天気の語をどの口で引いたか・資産の表に行が無かった回数(=前なら補いに落ちた回数)・
組み立てと日の頭の確かめの回数を、ランを 1 本回して数える。ランの中身は変えない(関数を包んで読むだけ)。

前の数え(``docs/bench/analysis/count-347/weather-noise/count_run.py``)は消した欄 ``weather_by_hour`` を読むので直さず、
ここに新しく置く。包む関数(どれも元の関数をそのまま呼び、戻り値を変えない):

- ``PerceptionAssets.weather``: 呼ばれた回数を、実データの資産の行あり(``loaded_row``)・合成の世界の行あり
  (``synthetic_row``)・合成の世界の宣言した天気(``synthetic_declared``)・行が無い(``missing``=A48 の後は止まる・前なら補い)に分ける。
- ``Renderer._time_view``: 天気の語の口(環境の過程の口 ``words_fn``・再生日の口 ``date_fn``・暦の日付 ``calendar_date``)。
- ``PerceptionAssets.require_weather_days``: 呼ばれた回数と確かめた日の数(組み立て=引きうる再生日の全部・日の頭=1 日)。

使い方(cwd は木の根・PYTHONPATH は木の src・PYTHONHASHSEED=0=byte-check と同じ):
    python count_weather_a48.py --config w6_v3_default --out <JSON>           # byte-check の構成(5,000 体・1 日)
    python count_weather_a48.py --probe no_processes --out <JSON> [--start 2026-09-14] [--agents 200] [--ticks 1440]
    python count_weather_a48.py --probe synthetic --out <JSON>                # 合成の世界(世界過程あり)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

W: Counter = Counter()
TV: Counter = Counter()
REQ: Counter = Counter()


def _install() -> None:
    from shibuya.perception import renderer as RD

    _weather = RD.PerceptionAssets.weather

    def weather(self, when):  # noqa: ANN001
        key = (when.strftime("%Y-%m-%d"), int(when.hour))
        if key in self.weather_by_date_hour:
            W["synthetic_row" if self.is_synthetic else "loaded_row"] += 1
        elif self.is_synthetic:
            W["synthetic_declared"] += 1
        else:
            W["missing"] += 1
        return _weather(self, when)

    RD.PerceptionAssets.weather = weather  # type: ignore[method-assign]

    _tv = RD.Renderer._time_view

    def time_view(self, tc):  # noqa: ANN001
        if self.weather_words_fn is not None:
            TV["words_fn"] += 1
        elif self.weather_date_fn is not None and self.weather_date_fn():
            TV["date_fn"] += 1
        else:
            TV["calendar_date"] += 1
        return _tv(self, tc)

    RD.Renderer._time_view = time_view  # type: ignore[method-assign]

    _req = RD.PerceptionAssets.require_weather_days

    def require(self, dates):  # noqa: ANN001
        dates = list(dates)
        REQ["calls"] += 1
        REQ["dates_checked"] += len(dates)
        if self.is_synthetic:
            REQ["calls_synthetic"] += 1
        return _req(self, dates)

    RD.PerceptionAssets.require_weather_days = require  # type: ignore[method-assign]


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--config")
    g.add_argument("--probe", choices=("no_processes", "synthetic"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--ticks", type=int, default=1440)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--start", default="")
    args = ap.parse_args()

    sys.path.insert(0, os.getcwd())
    _install()
    from shibuya import cli

    if args.config:
        from tools.bytecheck import configs as BC

        kwd = dict(BC.configs()[args.config])
        world = args.world
    elif args.probe == "no_processes":
        kwd = {"processes": False, "vocab_version": "v3"}
        world = args.world
    else:
        kwd = {"vocab_version": "v3"}
        world = None
    if args.start:
        kwd["start_sim_datetime"] = args.start
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=world, ticks=args.ticks, **kwd)
    wall = time.perf_counter() - t0
    man = res.run_manifest_fields()
    wx = man.get("weather", {})
    payload = {
        "config": args.config or args.probe,
        "kw": {k: (str(v) if not isinstance(v, (int, float, bool, str)) else v) for k, v in kwd.items()},
        "agents": args.agents,
        "ticks": args.ticks,
        "seed": args.seed,
        "world": None if world is None else str(world).replace("\\", "/"),
        "final16": res.final_hash[:16],
        "llm_calls": int(res.llm_calls),
        "weather_days": wx.get("days", []),
        "weather_declared": "declared" in wx,
        "wall_s": round(wall, 1),
        "weather_calls": dict(sorted(W.items())),
        "time_view_port": dict(sorted(TV.items())),
        "require_weather_days": dict(sorted(REQ.items())),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("config", "final16", "llm_calls", "weather_calls", "time_view_port",
                                              "require_weather_days", "wall_s")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
