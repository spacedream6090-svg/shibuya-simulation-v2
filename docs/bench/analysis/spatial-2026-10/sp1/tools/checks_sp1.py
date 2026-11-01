"""第 5 期 空間の段 1: 段 B(宣言の外の変化 0)+負の対照・記録 on/off で final が同じか(nav1・本物の世界の資産)。

``stageb``: ``SHIBUYA_SYSTEMS_CHECK=1`` で 300 体を回し(全刻みの snapshot)、宣言の外の変化 0 を見る。負の対照は phase_c の
宣言の SoA から ``agents.nav_t`` を外して同じランを回し、段 B が見つける(``AssertionError``)ことを確かめる。
``events``: 出来事の記録(``SHIBUYA_EVENTS``)の on/off で behavior-hash と full-hash が同じか(500 体)。

    python $D/tools/checks_sp1.py stageb --world data/world/v2_stage_5-1
    python $D/tools/checks_sp1.py events --world data/world/v2_stage_5-1

結果は 1 行の JSON(標準出力)。逐次ループ宣言: なし(道具・ランの外)。
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()


def _one_stageb(world: str, negative: bool, agents: int, ticks: int) -> dict:
    os.environ["SHIBUYA_SYSTEMS_CHECK"] = "1"
    from shibuya import cli
    from shibuya.engine.systems import table as T

    if negative:
        sp = T.SPECS["phase_c"]
        w = sp.writes
        soa = frozenset(x for x in w.soa if x != "agents.nav_t")
        assert soa != w.soa, "phase_c の宣言に agents.nav_t が無い"
        T.SPECS["phase_c"] = dataclasses.replace(sp, writes=dataclasses.replace(w, soa=soa))
    try:
        res = cli.run(n_agents=agents, seed=1, ticks=ticks, world_dir=world, space="nav1", vocab_version="v3")
        return {"negative": negative, "ok": True, "final": res.final_hash[:16],
                "effective": res.run_manifest_fields()["space"]["effective"]}
    except AssertionError as e:
        msg = str(e)
        return {"negative": negative, "ok": False, "error": msg[:300]}


def _one_events(world: str, on: bool, agents: int, ticks: int) -> dict:
    os.environ["SHIBUYA_EVENTS"] = "on" if on else "off"
    from shibuya import cli

    res = cli.run(n_agents=agents, seed=1, ticks=ticks, world_dir=world, space="nav1", vocab_version="v3")
    return {"events": on, "final": res.final_hash[:16], "behavior": [c.behavior_hash[:16] for c in res.checkpoints],
            "full": [c.full_hash[:16] for c in res.checkpoints],
            "effective": res.run_manifest_fields()["space"]["effective"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=("stageb", "events", "_stageb1", "_events1"))
    ap.add_argument("--world", default="data/world/v2_stage_5-1")
    ap.add_argument("--negative", action="store_true")
    ap.add_argument("--on", action="store_true")
    ap.add_argument("--agents", type=int, default=0)
    ap.add_argument("--ticks", type=int, default=1440)
    a = ap.parse_args(argv)
    if a.what == "_stageb1":
        print(json.dumps(_one_stageb(a.world, a.negative, a.agents or 300, a.ticks), ensure_ascii=False))
        return 0
    if a.what == "_events1":
        print(json.dumps(_one_events(a.world, a.on, a.agents or 500, a.ticks), ensure_ascii=False))
        return 0
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    rows = []
    variants = ((["--negative"] if neg else []) for neg in (False, True)) if a.what == "stageb" else \
        ((["--on"] if on else []) for on in (False, True))
    sub = "_stageb1" if a.what == "stageb" else "_events1"
    for extra in variants:  # 逐次ループ宣言: 2 本(1 本ずつ別のプロセス)
        r = subprocess.run([sys.executable, str(HERE), sub, "--world", a.world, "--ticks", str(a.ticks)] + extra,
                           capture_output=True, text=True, encoding="utf-8", env=env)
        rows.append(json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else
                    {"error": r.stderr[-1500:]})
    out = {"what": a.what, "rows": rows}
    if a.what == "events" and all("final" in x for x in rows):
        out["same_final"] = rows[0]["final"] == rows[1]["final"]
        out["same_behavior"] = rows[0]["behavior"] == rows[1]["behavior"]
        out["same_full"] = rows[0]["full"] == rows[1]["full"]
    if a.what == "stageb" and len(rows) == 2:
        out["pass"] = bool(rows[0].get("ok")) and rows[1].get("ok") is False
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
