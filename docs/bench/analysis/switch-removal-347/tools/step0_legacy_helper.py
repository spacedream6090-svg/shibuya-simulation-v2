# -*- coding: utf-8 -*-
"""手順 0 の続き: 旧道の切替口(モジュールの腕)と、試験の中だけの助け(実行器の初期化に部品の口を挿す)が同じランになるか。

使い方(リポの根で・``PYTHONPATH`` に ``src`` とリポの根): python step0_legacy_helper.py <構成 r4|r11> <腕 arm|helper> <出力 JSON>
切替口(``--rate-rules``・``--absent-processes`` の腕)が在る木(②b の前)でだけ回る。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(cfg: str, variant: str, path: str) -> None:
    import pytest

    from shibuya.world.laws import switch_absent as AP
    from shibuya.world.laws import switch_rate as RR

    mp = pytest.MonkeyPatch()
    if cfg == "r4":  # test_resume_10d::test_counter_rng_resume_draws_once の通しのラン
        from shibuya.engine.run import run_day

        kw = dict(n_agents=200, seed=1, n_cells=25, ticks=1_440, sim_days=2, checkpoint_every=10)
        if variant == "arm":
            RR.set_arm("legacy")
            AP.set_arm("legacy")
            res = run_day(salient_rate_per_10k=3000.0, **kw)
        else:
            from tests.engine._legacy_world import legacy_world_rules

            legacy_world_rules(mp, salient_rate=3000.0)
            res = run_day(**kw)
    elif cfg == "r11":  # test_rate_rules_1101 の day_runs の legacy(世界資産 200 体・台帳つき・1 日)
        from shibuya import cli

        kw = dict(n_agents=200, seed=3, world_dir="data/world/v2", ticks=1_440, checkpoint_every=360)
        if variant == "arm":
            RR.set_arm("legacy")
            res = cli.run(**kw)
        else:
            from tests.engine._legacy_world import legacy_world_rules

            legacy_world_rules(mp, absent=False)
            res = cli.run(**kw)
    else:
        raise SystemExit(cfg)
    m = res.run_manifest_fields()
    out = {
        "final": res.final_hash, "calls": int(res.llm_calls),
        "cp": [(int(c.tick), c.combined, c.full_hash) for c in res.checkpoints],
        "salient_events": int(res.salient_events), "dispatches": int(res.dispatches), "noticed": int(res.noticed),
        "process_counters": {k: v for k, v in sorted(dict(res.process_counters).items()) if "removed" not in k
                             and "stopped" not in k},
        "rate_counts": m["rate_rules"]["counts"], "absent_counts": m["absent_processes"]["counts"],
        "rate_mode": m["rate_rules"]["mode"], "absent_mode": m["absent_processes"]["mode"],
        "waste_sink": m.get("waste_sink"),
    }
    Path(path).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("書いた", path)


if __name__ == "__main__":
    main(*sys.argv[1:4])
