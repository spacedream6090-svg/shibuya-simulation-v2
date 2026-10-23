"""段 5-1b の計測(第 1 段階=3 案・第 2 段階=既定と legacy の 19 構成・道具・ランの外)。

    python docs/bench/analysis/spatial-2026-10/sp1b/tools/sp1b_measure.py side --label d --scratch <作業用> --out <出力>
        [--space legacy] [--density cell|neighborhood|unscaled] [--only 構成,…]

``one``: byte_check_10e の ``one`` と同じ 1 本(25 欄)を回し、同じプロセスで H1 の計器を足す(読むだけの包み=結果は変えない):
- 進めない体刻み(Kladek の係数 0 で動けなかった移動中の体 × 刻み)・同時の最大・詰まった刻みの数・最初と最後の刻み・上位のセル
- 速さ 0 のセル × 刻み(Kladek を評価した刻みの全セル)
- 人/m² の最大(1 日を通して・段を書く度=刻みの終わり)
- 段 5 のセル × 刻みと、そのうち歩ける面が 500 m² 未満の数・上位のセル
- 密度の段の変化(セル × 刻み=runs_sp1 と同じ数え方)と段の分布
- CELL_BLOCK の起床(変化検出の cell_wake_agents の延べ)
- p_notice に渡った密度区分の分布(候補の体の延べ)
``side``: 19 構成を 1 本ずつ(5,000 体のランは同時に回さない)。腕は環境変数(SHIBUYA_SPACE・SHIBUYA_NAV1_DENSITY)。

逐次ループ宣言: 構成の数ぶん(道具・ランの外)。
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4].parent
BC = REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "10e" / "byte_check_10e.py"
POP43 = REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "pop43" / "tools"


def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def install() -> dict[str, Any]:
    import numpy as np

    from shibuya.engine import change_detect as CD
    from shibuya.engine import resolve as R
    from shibuya.engine.geometry import kladek_speed_factor
    from shibuya.engine.space import nav1 as N
    from shibuya.perception import p_notice as PN

    m: dict[str, Any] = {"tick": -1, "apply_calls": 0, "stage_changes": 0, "stage_hist": {}, "prev": None,
                         "jam_agent_steps": 0, "jam_max_concurrent": 0, "jam_steps": 0, "jam_first": -1, "jam_last": -1,
                         "jam_by_cell": {}, "zero_cells_steps": 0, "kladek_calls": 0,
                         "max_per_m2": 0.0, "max_per_m2_cell": -1, "max_per_m2_tick": -1, "max_per_m2_area": 0.0,
                         "s5_cell_steps": 0, "s5_small": 0, "s5_by_cell": {}, "ds_calls": 0,
                         "cell_block_wakes": 0, "notice_class": {"0": 0, "1": 0, "2": 0}, "notice_calls": 0}

    orig_apply = R.apply

    def apply(plan_confirmed, losers, agents, world, tick, *a, **kw):
        m["tick"] = int(tick)
        out = orig_apply(plan_confirmed, losers, agents, world, tick, *a, **kw)
        m["apply_calls"] += 1
        st = np.asarray(world.cells.density_stage).copy()
        if m["prev"] is not None:
            m["stage_changes"] += int((st != m["prev"]).sum())
        m["prev"] = st
        for k, v in zip(*np.unique(st, return_counts=True)):
            m["stage_hist"][str(int(k))] = m["stage_hist"].get(str(int(k)), 0) + int(v)
        return out

    R.apply = apply

    orig_ds = N.NavSpace.density_stage

    def ds(self, density):
        st = orig_ds(self, density)
        pm = self.per_m2(density)
        m["ds_calls"] += 1
        c = int(np.argmax(pm))
        if float(pm[c]) > m["max_per_m2"]:
            m["max_per_m2"] = float(pm[c])
            m["max_per_m2_cell"] = c
            m["max_per_m2_tick"] = int(m["tick"])
            m["max_per_m2_area"] = float(self.walkable_area_raw_m2[c])
        s5 = np.flatnonzero(st >= 5)
        if s5.size:
            m["s5_cell_steps"] += int(s5.size)
            m["s5_small"] += int((self.walkable_area_raw_m2[s5] < 500.0).sum())
            for cc in s5.tolist():
                m["s5_by_cell"][str(cc)] = m["s5_by_cell"].get(str(cc), 0) + 1
        return st

    N.NavSpace.density_stage = ds

    orig_k = N.NavSpace.kladek_factor

    def kf(self, cell, density):
        fac = orig_k(self, cell, density)
        m["kladek_calls"] += 1
        fc = kladek_speed_factor(self.per_m2(density))
        m["zero_cells_steps"] += int((np.asarray(fc) <= 0.0).sum())
        jam = np.asarray(fac) <= 0.0
        n = int(jam.sum())
        if n:
            m["jam_agent_steps"] += n
            m["jam_steps"] += 1
            m["jam_max_concurrent"] = max(m["jam_max_concurrent"], n)
            if m["jam_first"] < 0:
                m["jam_first"] = int(m["tick"])
            m["jam_last"] = int(m["tick"])
            cc, nn = np.unique(np.asarray(cell, dtype=np.int64)[jam], return_counts=True)
            for a_, b_ in zip(cc.tolist(), nn.tolist()):
                m["jam_by_cell"][str(a_)] = m["jam_by_cell"].get(str(a_), 0) + int(b_)
        return fac

    N.NavSpace.kladek_factor = kf

    orig_det = CD.ChangeDetector.detect

    def det(self, *a, **kw):
        res = orig_det(self, *a, **kw)
        try:
            m["cell_block_wakes"] += int(np.asarray(res.cell_wake_agents).size)
        except AttributeError:
            pass
        return res

    CD.ChangeDetector.detect = det

    orig_ne = PN.notice_event

    def ne(*a, **kw):
        dc = kw.get("density_class")
        if dc is not None:
            m["notice_calls"] += 1
            v, n = np.unique(np.asarray(dc, dtype=np.int64).reshape(-1), return_counts=True)
            for a_, b_ in zip(v.tolist(), n.tolist()):
                m["notice_class"][str(a_)] = m["notice_class"].get(str(a_), 0) + int(b_)
        return orig_ne(*a, **kw)

    PN.notice_event = ne
    return m


def summarize(m: dict[str, Any], areas: Any) -> dict[str, Any]:
    def top(d: dict[str, int], k: int = 3) -> list[list[Any]]:
        rows = sorted(d.items(), key=lambda kv: (-kv[1], int(kv[0])))[:k]
        return [[int(c), int(n), round(float(areas[int(c)]), 2) if areas is not None else None] for c, n in rows]

    out = {k: v for k, v in m.items() if k not in ("prev", "tick", "jam_by_cell", "s5_by_cell")}
    out["max_per_m2"] = round(float(m["max_per_m2"]), 4)
    out["max_per_m2_area"] = round(float(m["max_per_m2_area"]), 2)
    out["jam_top_cells"] = top(m["jam_by_cell"])
    out["s5_top_cells"] = top(m["s5_by_cell"])
    return out


def cmd_one(a: argparse.Namespace) -> int:
    bc = _load(BC, "byte_check_10e")
    sys.path.insert(0, str(POP43))
    from runs_pop43 import _peak_working_set_bytes  # noqa: PLC0415

    m = install()
    areas: dict[str, Any] = {"v": None}
    from shibuya.engine.space import nav1 as N

    orig_init = N.NavSpace.__init__

    def init(self, *aa, **kw):
        orig_init(self, *aa, **kw)
        areas["v"] = self.walkable_area_raw_m2
        areas["mode"] = self.density_mode
        areas["nb"] = self.density_nb_info

    N.NavSpace.__init__ = init
    ns = argparse.Namespace(config=a.config, kw="", world=a.world, agents=a.agents, seed=a.seed, tape=a.tape,
                            drop_behavior_item="", multiset_items="")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        bc.cmd_one(ns)
    row = json.loads(buf.getvalue().strip().splitlines()[-1])
    row["h1"] = summarize(m, areas["v"])
    row["density_mode_seen"] = areas.get("mode")
    row["density_neighborhood"] = areas.get("nb")
    row["peak_ws_bytes"] = _peak_working_set_bytes()
    print(json.dumps(row, ensure_ascii=False, default=str))
    return 0


def cmd_side(a: argparse.Namespace) -> int:
    bc = _load(BC, "byte_check_10e")
    names = [s for s in a.only.split(",") if s] if a.only else list(bc._wave2().configs())
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    for k in ("SHIBUYA_SPACE", "SHIBUYA_NAV1_DENSITY"):
        env.pop(k, None)
    if a.space:
        env["SHIBUYA_SPACE"] = a.space
    if a.density:
        env["SHIBUYA_NAV1_DENSITY"] = a.density
    runs: dict[str, Any] = {}
    outp = Path(a.out)
    if outp.exists():
        runs = json.loads(outp.read_text(encoding="utf-8")).get("runs", {})
    for name in names:
        if name in runs and "error" not in runs[name]:
            continue
        cmd = [sys.executable, str(Path(__file__)), "one", "--config", name, "--world", a.world, "--agents",
               str(a.agents), "--seed", str(a.seed), "--tape", str(Path(a.scratch) / f"{a.label}_{name}")]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            runs[name] = {"config": name, "error": r.stderr[-3000:]}
        else:
            runs[name] = json.loads(r.stdout.strip().splitlines()[-1])
        row = runs[name]
        print(name, row.get("final"), row.get("calls"), row.get("meals"), (row.get("h1") or {}).get("jam_agent_steps"),
              row.get("wall_s"), (row.get("error") or "")[-300:], flush=True)
        doc = {"label": a.label, "space": a.space, "density": a.density, "agents": a.agents, "seed": a.seed,
               "env": {k: env[k] for k in ("SHIBUYA_SPACE", "SHIBUYA_NAV1_DENSITY") if k in env}, "runs": runs}
        outp.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("--config", required=True)
    o.add_argument("--world", default="data/world/v2")
    o.add_argument("--agents", type=int, default=5000)
    o.add_argument("--seed", type=int, default=1)
    o.add_argument("--tape", required=True)
    s = sub.add_parser("side")
    s.add_argument("--label", required=True)
    s.add_argument("--space", default="")
    s.add_argument("--density", default="")
    s.add_argument("--world", default="data/world/v2")
    s.add_argument("--agents", type=int, default=5000)
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--only", default="")
    s.add_argument("--scratch", required=True)
    s.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
