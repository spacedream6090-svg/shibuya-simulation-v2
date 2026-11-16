# -*- coding: utf-8 -*-
"""A48(第347・検収の直し): 世界の資産の置き場ごとに、ごく短いラン(10 体・2 刻み)を世界過程のあり・なしで回し、組み立てで
止まるか(天気の資産の片方だけ=両向き・行の欠け)を数える。ランの中身は変えない。止まったときは止める文を残す。

段の途中の置き場(nav1 の資産が無い本番の形の世界)は、天気の結線より前の移動の確かめで止まる(切替口 ③a の後=旧のセルの移動は
試験の中だけの口)。そうした置き場は、試験と同じ口(``nav1._LEGACY_FOR_TESTS``)で旧のセルの移動にして回し直し、印 ``space_legacy``
を付ける(天気の結線の確かめに届かせるため・天気の結果には効かない)。

使い方(cwd は木の根・PYTHONPATH は木の src): ``python stop_paths_a48.py <出力の JSON>``(``data/world/*/`` の全部)。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _one(cli, d: Path, processes: bool) -> dict:  # noqa: ANN001
    try:
        res = cli.run(n_agents=10, seed=1, world_dir=str(d).replace("\\", "/"), ticks=2, checkpoint_every=2,
                      processes=processes)
        m = res.run_manifest_fields()
        return {"stopped": False, "declared": "declared" in m["weather"], "replay_date": m["replay_date"]}
    except Exception as e:  # noqa: BLE001 - 止まった文を数える
        return {"stopped": True, "error": f"{type(e).__name__}: {str(e)[:160]}"}


def main() -> int:
    from shibuya import cli
    from shibuya.perception.renderer import PerceptionAssets
    from shibuya.world.model.space import nav1 as NAV1

    out = []
    for d in sorted(Path("data/world").glob("*/")):
        row = {"dir": d.name, "perception_files": PerceptionAssets.available(d),
               "w13_both": (d / "w13_weather_days.parquet").exists() and (d / "w13_weather_hourly.parquet").exists()}
        for processes in (True, False):
            key = "processes" if processes else "no_processes"
            got = _one(cli, d, processes)
            if got["stopped"] and "nav1_" in got.get("error", ""):
                NAV1._LEGACY_FOR_TESTS = True
                try:
                    got = dict(_one(cli, d, processes), space_legacy=True)
                finally:
                    NAV1._LEGACY_FOR_TESTS = False
            row[key] = got
        out.append(row)
        print(json.dumps(row, ensure_ascii=False))
    Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
