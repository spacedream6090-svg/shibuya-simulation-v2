# -*- coding: utf-8 -*-
"""数える役 A(weather-noise): byte-check の構成を 1 本回し、A48(天気の最頻値の補い)と A49(6 時と 22 時の騒音の段の
切り替えで起こされる住民)を数える。ランの中身は変えない(関数を包んで読むだけ)。

包む関数(どれも元の関数をそのまま呼び、戻り値を変えない):
- ``PerceptionAssets.weather``(``perception/renderer.py``): 呼ばれた回数と、(日付, 時)の行が表に無く補いの枝
  (``weather_by_hour``=最頻値、合成の資産では決まった表)に落ちた回数。資産が読んだもの(loaded)か合成(synthetic)かで分ける。
- ``Renderer._time_view``(同じファイル): 天気の語をどの口で引いたか(環境の過程の口 words_fn/再生日の口 date_fn/暦の日付)。
- ``ChangeDetector.detect``(``engine/change_detect.py``): 前の刻みの B4 の欄と比べ、騒音の欄(列 1)が変わったマスと、そこで
  起床の候補(CELL_BLOCK)になった体。騒音だけが変わったマスと、ほかの欄(密度の段・流れ・顕著行為)も変わったマスを分ける。
- ``WorldProcessRunner.salient_wake_candidates``: 同じ刻みの顕著行為の候補(CELL_BLOCK と同じ条件なので分けるため)。
- ``Arbiter.step``(``engine/arbiter.py``): 騒音の体の CELL_BLOCK の行が裁定でどうなったか(域外・就寝・不応期で落ちた/
  生きて呼ばれた)と、同じ体にほかの起床の行があったか。

使い方(cwd はリポの根・PYTHONPATH はリポの src・PYTHONHASHSEED=0=byte-check と同じ):
    python count_run.py --config w6_v3_default --tape <テープの置き場> --out <出力の JSON>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

W: dict = {"calls_loaded": 0, "fallback_loaded": 0, "calls_synthetic": 0, "fallback_synthetic": 0,
           "fallback_default_tuple": 0, "fallback_keys": Counter()}
TV: Counter = Counter()
NOISE: dict[int, dict] = {}
SAL: dict = {"tick": -1, "agents": np.empty(0, dtype=np.int64)}


def _install() -> dict:
    from shibuya.agents.state import WakeCondition
    from shibuya.engine import arbiter as AR
    from shibuya.engine import change_detect as CD
    from shibuya.perception import renderer as RD
    from shibuya.world.laws import runner as RN

    cb = int(WakeCondition.CELL_BLOCK)
    info = {"cell_block": cb}

    _weather = RD.PerceptionAssets.weather

    def weather(self, when):  # noqa: ANN001
        key = (when.strftime("%Y-%m-%d"), int(when.hour))
        src = "synthetic" if self.source == "synthetic" else "loaded"
        W["calls_" + src] += 1
        if key not in self.weather_by_date_hour:
            W["fallback_" + src] += 1
            W["fallback_keys"][f"{src}|{key[0]}"] += 1
            if int(when.hour) not in self.weather_by_hour:
                W["fallback_default_tuple"] += 1
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

    _det = CD.ChangeDetector.detect

    def detect(self, world, agents, tick, *, field_rows=None, scope=None):  # noqa: ANN001
        prev = None if self._prev_raw is None else self._prev_raw.copy()
        res = _det(self, world, agents, tick, field_rows=field_rows, scope=scope)
        raw = self._prev_raw
        if prev is not None and raw is not None and prev.shape == raw.shape:
            diff = raw != prev
            noise = diff[:, 1]
            if noise.any():
                other = diff[:, 0] | diff[:, 2] | diff[:, 3]
                only_c = noise & ~other
                mixed_c = noise & other
                cell = np.asarray(agents.registry.cell, dtype=np.int64)
                wake = np.asarray(res.cell_wake_agents, dtype=np.int64)
                wc = cell[wake]
                ok = wc >= 0
                wake, wc = wake[ok], wc[ok]
                up = int(np.count_nonzero(noise & (raw[:, 1] > prev[:, 1])))
                down = int(np.count_nonzero(noise & (raw[:, 1] < prev[:, 1])))
                NOISE[int(tick)] = {
                    "n_cells": int(raw.shape[0]),
                    "cells_noise_changed": int(np.count_nonzero(noise)),
                    "cells_noise_up": up,
                    "cells_noise_down": down,
                    "cells_noise_only": int(np.count_nonzero(only_c)),
                    "cells_noise_and_other": int(np.count_nonzero(mixed_c)),
                    "agents_only": wake[only_c[wc]].copy(),
                    "agents_mixed": wake[mixed_c[wc]].copy(),
                    "b5_agents": np.asarray(res.b5_wake_agents, dtype=np.int64).copy(),
                }
        return res

    CD.ChangeDetector.detect = detect  # type: ignore[method-assign]

    _sal = RN.WorldProcessRunner.salient_wake_candidates

    def sal(self, tick):  # noqa: ANN001
        out = _sal(self, tick)
        SAL["tick"] = int(tick)
        SAL["agents"] = np.asarray(out[0], dtype=np.int64).copy()
        return out

    RN.WorldProcessRunner.salient_wake_candidates = sal  # type: ignore[method-assign]

    _step = AR.Arbiter.step

    def step(self, tick, candidates, refractory_until=None, asleep=None, outside=None):  # noqa: ANN001
        t = int(tick)
        rec = NOISE.get(t)
        if rec is None:
            return _step(self, tick, candidates, refractory_until, asleep, outside)
        pend = self._pending
        merged = AR.WakeCandidates.concat([pend, candidates])
        m_agent = np.asarray(merged.agent_id, dtype=np.int64).copy()
        m_cond = np.asarray(merged.condition, dtype=np.int64).copy()
        new_agent = np.asarray(candidates.agent_id, dtype=np.int64).copy()
        new_cond = np.asarray(candidates.condition, dtype=np.int64).copy()
        asl = None if asleep is None else np.asarray(asleep, dtype=bool).copy()
        outm = None if outside is None else np.asarray(outside, dtype=bool).copy()
        dec = _step(self, tick, candidates, refractory_until, asleep, outside)
        rec["arbiter"] = _analyze(rec, t, m_agent, m_cond, new_agent, new_cond, asl, outm, dec, cb)
        return dec

    AR.Arbiter.step = step  # type: ignore[method-assign]
    return info


def _cb_agents(c, cb: int) -> set[int]:  # noqa: ANN001
    a = np.asarray(c.agent_id, dtype=np.int64)
    k = np.asarray(c.condition, dtype=np.int64)
    return set(int(x) for x in a[k == cb])


def _analyze(rec, t, m_agent, m_cond, new_agent, new_cond, asl, outm, dec, cb) -> dict:  # noqa: ANN001
    sal = set(int(x) for x in SAL["agents"]) if SAL["tick"] == t else set()
    b5 = set(int(x) for x in rec["b5_agents"])
    rows_per_agent = Counter(int(x) for x in m_agent)
    new_cb = set(int(x) for x in new_agent[new_cond == cb])
    out10 = _cb_agents(dec.outside_suppressed, cb)
    sl10 = _cb_agents(dec.sleep_suppressed, cb)
    ref10 = _cb_agents(dec.suppressed, cb)
    sel_agent = np.asarray(dec.selected.agent_id, dtype=np.int64)
    sel_cond = np.asarray(dec.selected.condition, dtype=np.int64)
    selected = {int(a): int(c) for a, c in zip(sel_agent, sel_cond)}
    deferred = set(int(x) for x in np.asarray(dec.deferred.agent_id, dtype=np.int64))
    out: dict = {}
    for grp in ("only", "mixed"):
        ag = [int(x) for x in rec["agents_" + grp]]
        n = len(ag)
        reach = [a for a in ag if a in new_cb]  # CELL_BLOCK の行が裁定まで届いた(検出の後の抑止で落ちていない)
        r_out = [a for a in reach if a in out10]
        r_sl = [a for a in reach if a in sl10 and a not in out10]
        r_ref = [a for a in reach if a in ref10 and a not in out10 and a not in sl10]
        live = [a for a in reach if a not in out10 and a not in sl10 and a not in ref10]
        woken = [a for a in live if a in selected]
        dfr = [a for a in live if a not in selected and a in deferred]
        # 重なり: 同じ刻みにこの体のほかの起床の行(内受容・計画境界・会話・満了・繰り延べの保留・顕著行為)がある
        alone = [a for a in woken if rows_per_agent[a] == 1 and a not in sal]
        overlap_rows = [a for a in woken if a not in alone]
        rep = Counter(selected[a] for a in woken)
        other_conds = Counter()
        for a in overlap_rows:
            ks = sorted(set(int(c) for c in m_cond[m_agent == a] if int(c) != cb))
            other_conds["+".join(str(k) for k in ks) if ks else ("salient" if a in sal else "dup_cell_block")] += 1
        out[grp] = {
            "agents_in_cells": n,
            "asleep_at_arbiter": int(sum(1 for a in ag if asl is not None and asl[a])),
            "outside_at_arbiter": int(sum(1 for a in ag if outm is not None and outm[a])),
            "dropped_before_arbiter": n - len(reach),
            "reached_arbiter": len(reach),
            "suppressed_outside": len(r_out),
            "suppressed_sleep": len(r_sl),
            "suppressed_refractory": len(r_ref),
            "live_cell_block_row": len(live),
            "woken_called": len(woken),
            "woken_called_alone": len(alone),
            "woken_called_with_other_rows": len(overlap_rows),
            "woken_with_b5_same_tick": int(sum(1 for a in woken if a in b5)),
            "deferred": len(dfr),
            "representative_condition_of_woken": {str(k): v for k, v in sorted(rep.items())},
            "other_conditions_of_overlap": dict(sorted(other_conds.items())),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--tape", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    sys.path.insert(0, os.getcwd())
    from tools.bytecheck import configs as BC

    info = _install()
    from shibuya import cli

    kwd = dict(BC.configs()[args.config])
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape, **kwd)
    wall = time.perf_counter() - t0
    man = res.run_manifest_fields()

    # 静的: 昼と夜で段が違うマス(世界の資産・World.noise_stage_for_tick が読む表)
    from shibuya.world.model.state import World

    world = World.load_or_synthetic(Path(args.world), n_cells=139, seed=args.seed)
    wa = world.assets
    static = {}
    if wa.has_noise_field:
        d = np.asarray(wa.noise_stage_day, dtype=np.int64)
        nt = np.asarray(wa.noise_stage_night, dtype=np.int64)
        static = {"n_cells": int(d.size), "cells_day_ne_night": int(np.count_nonzero(d != nt)),
                  "cells_night_lower": int(np.count_nonzero(nt < d)), "cells_night_higher": int(np.count_nonzero(nt > d)),
                  "day_hist": np.bincount(d, minlength=4).tolist(), "night_hist": np.bincount(nt, minlength=4).tolist()}

    noise_out = {}
    for t, rec in sorted(NOISE.items()):
        noise_out[str(t)] = {k: v for k, v in rec.items() if k not in ("agents_only", "agents_mixed", "b5_agents")}
    tick_seconds = int(man.get("tick_seconds", 60))
    payload = {
        "config": args.config,
        "kw": kwd,
        "agents": args.agents,
        "seed": args.seed,
        "world": str(args.world).replace("\\", "/"),
        "final16": res.final_hash[:16],
        "llm_calls": int(res.llm_calls),
        "calls_by_condition": {str(k): int(v) for k, v in dict(res.calls_by_condition).items()},
        "replay_date": str(man.get("replay_date", "")),
        "start_sim_datetime": str(man.get("start_sim_datetime", "")),
        "weather_days": man.get("weather", {}).get("days", []),
        "wall_s": round(wall, 1),
        "a48": {
            "weather_calls_loaded": W["calls_loaded"], "weather_fallback_loaded": W["fallback_loaded"],
            "weather_calls_synthetic": W["calls_synthetic"], "weather_fallback_synthetic": W["fallback_synthetic"],
            "fallback_default_tuple": W["fallback_default_tuple"],
            "fallback_keys": dict(sorted(W["fallback_keys"].items())),
            "time_view_path": dict(sorted(TV.items())),
        },
        "a49": {
            "cell_block_condition": info["cell_block"],
            "tick_seconds": tick_seconds,
            "noise_change_ticks": {k: f"{int(k) * tick_seconds // 3600:02d}:{int(k) * tick_seconds % 3600 // 60:02d}"
                                   for k in noise_out},
            "static_noise_field": static,
            "by_tick": noise_out,
        },
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"config": args.config, "final16": payload["final16"], "calls": payload["llm_calls"],
                      "a48": {k: v for k, v in payload["a48"].items() if k != "fallback_keys"},
                      "noise_ticks": list(noise_out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
