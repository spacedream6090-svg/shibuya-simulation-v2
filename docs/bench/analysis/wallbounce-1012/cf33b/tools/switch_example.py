"""第 3 期 3-3b T からの切り替えの例(記録 ``../README.md`` §2 の数)を回す道具。

世界資産 N 体(既定 1,000)・seed 1・2 日・語彙 v3・checkpoint 60 刻みの基準のラン(録画・日の境目の状態・checkpoints)を作り、
T0=2 日目の正午に「正午に W7 で開いている店のうち番号の小さい 200 店の休業」(L1・告知は体 1〜3 と店の担当)の分岐を
``engine.experiment.branch.run_branch``(切り替えの口 ``switch.ReplaySwitch``)で 2 通り回す:

- ``mock``: T からの口=ランの口(mock=決定論の札)。決定論の確認(A/A の枝 2 本が厳密に同じ・final=基準)・床 0。
- ``stand_in``: T からだけ答えがずれる口(作るたびに種の違う mock=実 LLM の非決定の代わり・札 ``llm_stand_in``)。(d) は T より前の
  一致だけ・床は 0 でない・(c) は A/A の枝 2 本の最初の食い違いとの刻みの差。

要約を JSON に書く(絶対パスは書かない)。使い方(リポの根で・``PYTHONPATH`` に作業木の ``src``)::

    python docs/bench/analysis/wallbounce-1012/cf33b/tools/switch_example.py --scratch <作業用> --out <要約の JSON>
"""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import time
from pathlib import Path

import numpy as np

WORLD = Path("data/world/v2")
KW = dict(n_agents=1000, seed=1, world_dir=WORLD.as_posix(), sim_days=2, vocab_version="v3", checkpoint_every=60)


class StandIn:
    """T からだけ答えがずれる口(作るたびに種の違う mock)。"""

    source = "llm_stand_in"
    _ids = itertools.count(1)

    def __init__(self, inner):
        self.inner = copy.copy(inner)
        self.inner.master_seed = f"{inner.master_seed}:stand_in{next(self._ids)}"

    def complete(self, request):
        return self.inner.complete(request)


def _open_at_noon_on_day2() -> list[int]:
    from shibuya.engine.calendar import DEFAULT_WORLD_START, SimCalendar, load_holidays
    from shibuya.engine.processes.opening import rows_of_day
    from shibuya.world.assets import load_process_assets_or_synthetic
    from shibuya.world.state import World

    w = World.load(WORLD)
    pa = load_process_assets_or_synthetic(WORLD, w.assets)
    row = SimCalendar(DEFAULT_WORLD_START, holidays=load_holidays()).opening_row(1)
    sel = rows_of_day(pa.plan_poi, pa.plan_day, row, pa.plan_ph_poi) & (pa.plan_start <= 720) & (pa.plan_end > 720)
    return sorted({int(x) for x in np.asarray(pa.plan_poi)[sel]})


def _summary(out, wall: float) -> dict:
    rep = out.report
    c = rep["checks"]["c_first_divergence"]
    m = out.branch.run_manifest_fields()["experiment"]
    return {
        "summary": rep["summary"], "switch": rep["switch"], "runs": rep["runs"],
        "b_pre_t0": {k: (None if v is None else {x: v.get(x) for x in ("ok", "checkpoints_before_T0",
                                                                        "tape_miss_before_t0", "box_left")})
                     for k, v in rep["checks"]["b_pre_t0"].items() if k != "resume_state"},
        "c": {"coarse_first_step": c["coarse"]["first_step"], "world": None if c["world"] is None else
              {k: c["world"][k] for k in ("step", "system", "keys")}, "aa_coarse_first_step": c["aa_coarse"]["first_step"],
              "vs_aa": c["vs_aa"]},
        "d_determinism": rep["checks"]["d_determinism"],
        "d_floor": {k: v for k, v in rep["checks"]["d_floor"].items() if k != "note"},
        "replay": m["replay"], "wall_seconds": round(wall, 1),
    }


def main() -> int:
    from shibuya import cli
    from shibuya.core.time_consts import NS_PER_SECOND, SECONDS_PER_DAY
    from shibuya.engine.experiment import branch as BR
    from shibuya.engine.experiment.form import ExperimentForm

    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--agents", type=int, default=1000)
    a = ap.parse_args()
    kw = dict(KW, n_agents=int(a.agents))
    base = Path(a.scratch) / "base"
    t = time.perf_counter()
    res = cli.run(tape_path=base / BR.BASE_TAPE, state_out=base / BR.BASE_STATE, **kw)
    (base / BR.BASE_CHECKPOINTS).write_text(json.dumps(cli.checkpoints_payload(res), ensure_ascii=False, default=str),
                                            encoding="utf-8")
    base_s = time.perf_counter() - t
    open_ = _open_at_noon_on_day2()
    f = ExperimentForm.from_dict({
        "kind": "explore", "subject": {"level": "L1", "ids": open_[:200]}, "content": [{"decision": "closure"}],
        "start": (SECONDS_PER_DAY + SECONDS_PER_DAY // 2) * NS_PER_SECOND,
        "notice": {"to": ["staff", 1, 2, 3], "via": "メッセージ"},
        "question": "正午に店を休むと人の流れはどう変わるか",
        "metrics": {"primary": {"id": "calls", "path": "manifest.llm_calls_total"}},
    })
    doc = {"schema": "cf33b/switch-example/1", "kw": kw, "form_sha256": f.sha256(), "n_targets": len(f.subject["ids"]),
           "base_final": res.final_hash, "base_wall_seconds": round(base_s, 1), "arms": {}}
    for name, live in (("mock", None), ("stand_in", StandIn)):
        t = time.perf_counter()
        out = BR.run_branch(f, base, runner=cli.run, run_kwargs=kw, live=live,
                            out_dir=Path(a.scratch) / "branches" / name)
        doc["arms"][name] = _summary(out, time.perf_counter() - t)
        print(name, json.dumps(doc["arms"][name]["summary"], ensure_ascii=False))
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                           newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
