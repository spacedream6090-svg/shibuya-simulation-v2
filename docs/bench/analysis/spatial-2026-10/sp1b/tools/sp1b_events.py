"""段 5-1b 第 2 段階の追加の計測(道具・ランの外・読むだけの包み=結果は変えない)。

``events``: 帰無腕(w6_golden_null_arm)などを 1 本回し、顕著行為の事象(倒れる・出動の到着)ごとに 刻み・種類・セル(層・歩ける
面積)・倒れた体(番号・活動・面の上か)・事象のセルに居た体・候補の体(セル+4 近傍の在席者=``SalientProcess._candidates``)・
候補のうち事象の点から 20 m/50 m/100 m の中の体・気づいた体を 1 行ずつ出す。
``perf``: v3 既定(5,000 体・1 日)を 1 本回し、壁時計・刻みあたり・最大の作業集合・CELL_BLOCK の起床の延べ・呼数を出す。
``--old-b4``: B4 の密度の段を前の形(セルの全員 ÷ 知覚の歩ける面積)で回す(``Renderer.prepare_tick`` の ``los_stage`` を捨て、
変化検出の ``los_from_stage`` を False にする=段 5-1b 第 2 段階の B4 の変更の前と同じ道・src は変えない)。

    python docs/bench/analysis/spatial-2026-10/sp1b/tools/sp1b_events.py events --config w6_golden_null_arm [--old-b4]
    python docs/bench/analysis/spatial-2026-10/sp1b/tools/sp1b_events.py perf [--old-b4]

腕は環境変数(SHIBUYA_SPACE・SHIBUYA_NAV1_DENSITY)。結果は 1 行の JSON(標準出力)。逐次ループ宣言: 事象の数ぶん(道具・ランの外)。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4].parent
WAVE2 = REPO / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"
POP43 = REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "pop43" / "tools"


def _configs() -> dict[str, dict[str, Any]]:
    spec = importlib.util.spec_from_file_location("wave2_bytecheck", WAVE2)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.configs()


def old_b4() -> None:
    """B4 の密度の段を前の形に戻す(読むだけの包み)。"""
    from shibuya.engine import change_detect as CD
    from shibuya.perception import renderer as RD

    orig_prep = RD.Renderer.prepare_tick

    def prep(self, tick, **kw):  # noqa: ANN001
        kw.pop("los_stage", None)
        return orig_prep(self, tick, **kw)

    RD.Renderer.prepare_tick = prep
    orig_cc = CD.ChangeDetector._cell_changes

    def cc(self, world, tick, field_rows=None):  # noqa: ANN001
        self.los_from_stage = False
        return orig_cc(self, world, tick, field_rows)

    CD.ChangeDetector._cell_changes = cc


def count_cell_block() -> dict[str, int]:
    from shibuya.engine import change_detect as CD

    m = {"cell_block_wakes": 0}
    orig = CD.ChangeDetector.detect

    def det(self, *a, **kw):  # noqa: ANN001
        res = orig(self, *a, **kw)
        m["cell_block_wakes"] += int(np.asarray(res.cell_wake_agents).size)
        return res

    CD.ChangeDetector.detect = det
    return m


def cmd_events(a: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.agents.state import Activity
    from shibuya.engine.processes import salient as S

    if a.old_b4:
        old_b4()
    m = count_cell_block()
    rows: list[dict[str, Any]] = []
    holder: dict[str, Any] = {}
    orig_init = S.SalientProcess.__init__
    orig_collapse = S.SalientProcess._collapse_events
    orig_step = S.SalientProcess.step

    def init(self, *aa, **kw):  # noqa: ANN001
        orig_init(self, *aa, **kw)
        holder["p"] = self

    def collapse(self, tick):  # noqa: ANN001
        r = self.agents.registry
        out = orig_collapse(self, tick)
        if out:
            # 倒れた体=事象の点に居る体(同じセル・同じ点)
            xy = np.asarray(r.xy, dtype=np.float64)
            for ev in out:
                d = np.hypot(xy[:, 0] - ev.xy[0], xy[:, 1] - ev.xy[1])
                cand = np.flatnonzero((d < 1e-6) & (np.asarray(r.cell) == ev.cell))
                holder.setdefault("collapsed", []).append(
                    (int(tick), int(ev.cell), [int(x) for x in cand[:3]],
                     [int(np.asarray(r.activity)[x]) for x in cand[:3]]))
        return out

    track = int(a.track_cell)
    share = {"in_area": 0, "in_track": 0, "steps": 0, "by_hour": {}}

    def step(self, tick):  # noqa: ANN001
        orig_step(self, tick)
        r = self.agents.registry
        cell = np.asarray(r.cell, dtype=np.int64)
        if track >= 0:  # 在圏の体のうち見張るセルに居た体の割合(倒れる体は在圏の体から引く)
            n_in, n_tr = int((cell >= 0).sum()), int((cell == track).sum())
            share["in_area"] += n_in
            share["in_track"] += n_tr
            share["steps"] += 1
            hh = share["by_hour"].setdefault(str(int(tick) // 60), [0, 0])
            hh[0] += n_in
            hh[1] += n_tr
        xy = np.asarray(r.xy, dtype=np.float64)
        act = np.asarray(r.activity)
        for ev in self.events:
            if ev.kind not in ("collapse", "police"):
                continue
            cand = self._candidates(ev.cell)
            d = np.hypot(xy[cand, 0] - ev.xy[0], xy[cand, 1] - ev.xy[1]) if cand.size else np.zeros(0)
            inc = cell == int(ev.cell)
            rows.append({"tick": int(tick), "kind": ev.kind, "cell": int(ev.cell),
                         "band": int(self.world.assets.cell_band[ev.cell]) if hasattr(self.world.assets, "cell_band")
                         else None,
                         "in_cell": int(inc.sum()), "in_cell_moving": int((inc & (act == int(Activity.MOVING))).sum()),
                         "candidates": int(cand.size), "within_20m": int((d <= 20).sum()),
                         "within_50m": int((d <= 50).sum()), "within_100m": int((d <= 100).sum()),
                         "noticed": int(np.asarray(ev.noticed).size), "xy": [round(ev.xy[0], 1), round(ev.xy[1], 1)]})

    S.SalientProcess.__init__ = init
    S.SalientProcess._collapse_events = collapse
    S.SalientProcess.step = step
    kw = dict(_configs()[a.config])
    res = cli.run(n_agents=a.agents, seed=a.seed, world_dir=a.world, **kw)
    man = res.run_manifest_fields()
    print(json.dumps({"config": a.config, "old_b4": bool(a.old_b4), "env": {k: os.environ[k] for k in
                      ("SHIBUYA_SPACE", "SHIBUYA_NAV1_DENSITY") if k in os.environ},
                      "space": man["space"]["effective"],
                      "density_mode": (man["space"].get("navmesh") or {}).get("density_mode"),
                      "final": res.final_hash[:16], "calls": int(res.llm_calls), "noticed": int(res.noticed),
                      "cell_block_wakes": m["cell_block_wakes"], "events": rows,
                      "collapsed": holder.get("collapsed", []),
                      "track_cell": track, "track_share": (round(share["in_track"] / share["in_area"], 5)
                                                          if share["in_area"] else None),
                      "track_share_by_hour": {h: round(v[1] / v[0], 4) if v[0] else None
                                              for h, v in share["by_hour"].items()}}, ensure_ascii=False))
    return 0


def cmd_perf(a: argparse.Namespace) -> int:
    from shibuya import cli

    sys.path.insert(0, str(POP43))
    from runs_pop43 import _peak_working_set_bytes  # noqa: PLC0415

    if a.old_b4:
        old_b4()
    m = count_cell_block()
    t0 = time.perf_counter()
    res = cli.run(n_agents=a.agents, seed=a.seed, world_dir=a.world, vocab_version="v3")
    wall = time.perf_counter() - t0
    man = res.run_manifest_fields()
    steps = int(getattr(res, "ticks", 0) or 1440)
    print(json.dumps({"old_b4": bool(a.old_b4), "env": {k: os.environ[k] for k in ("SHIBUYA_SPACE", "SHIBUYA_NAV1_DENSITY")
                                                       if k in os.environ},
                      "space": man["space"]["effective"],
                      "density_mode": (man["space"].get("navmesh") or {}).get("density_mode"),
                      "machine": f"{platform.system()} {platform.release()} {platform.machine()} cpu={os.cpu_count()}",
                      "final": res.final_hash[:16], "calls": int(res.llm_calls), "wall_s": round(wall, 1),
                      "run_wall_s": round(float(res.wall_seconds), 2),
                      "ms_per_step": round(1000.0 * float(res.wall_seconds) / max(1, steps), 2),
                      "peak_ws_bytes": _peak_working_set_bytes(), "cell_block_wakes": m["cell_block_wakes"],
                      "calls_cell_block": int(dict(res.calls_by_condition).get("CELL_BLOCK", -1))}, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("events", "perf"):
        s = sub.add_parser(name)
        s.add_argument("--world", default="data/world/v2")
        s.add_argument("--agents", type=int, default=5000)
        s.add_argument("--seed", type=int, default=1)
        s.add_argument("--old-b4", action="store_true")
        if name == "events":
            s.add_argument("--config", default="w6_golden_null_arm")
            s.add_argument("--track-cell", type=int, default=291)
    a = ap.parse_args(argv)
    return {"events": cmd_events, "perf": cmd_perf}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
