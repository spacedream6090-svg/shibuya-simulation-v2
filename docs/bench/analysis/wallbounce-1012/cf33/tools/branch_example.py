"""第 3 期 3-3 分岐の例(記録 ``../README.md`` §4 の数)を回す道具。

世界資産 N 体(既定 1,000・``--agents 5000`` で担当の従業者のいる世界=親の判断 M3)・seed 1・2 日・語彙 v3・checkpoint 60 刻みの
基準のラン(録画・日の境目の状態・checkpoints)を作り、
T0=2 日目の正午に「正午に W7 で開いている店のうち番号の小さい 200 店の休業」(L1・告知は体 1〜3 と店の担当)の分岐を
``engine.experiment.branch.run_branch`` で回して、報告の要約を JSON に書く(絶対パスは書かない)。

使い方(リポの根で・``$W`` = 作業用の短いディレクトリ・``PYTHONPATH`` に作業木の ``src``)::

    python docs/bench/analysis/wallbounce-1012/cf33/tools/branch_example.py --scratch $W/cf33 --out <要約の JSON>
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

WORLD = Path("data/world/v2")
KW = dict(n_agents=1000, seed=1, world_dir=WORLD.as_posix(), sim_days=2, vocab_version="v3", checkpoint_every=60)


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
    t = time.perf_counter()
    out = BR.run_branch(f, base, runner=cli.run, run_kwargs=kw)
    br_s = time.perf_counter() - t
    rep = out.report
    c = rep["checks"]["c_first_divergence"]
    m = out.branch.run_manifest_fields()["experiment"]
    doc = {
        "schema": "cf33/branch-example/2", "kw": kw, "n_targets": len(f.subject["ids"]),
        "n_open_at_noon": len(open_), "staffed_pois": int((np.asarray(res.runner.opening.staff_of_poi) >= 0).sum()),
        "form_sha256": f.sha256(), "summary": rep["summary"], "T0_step": rep["T0_step"],
        "resume_from": rep["resume_from"], "runs": rep["runs"], "base_final": rep["base"]["final_hash"],
        "a_input_match": {k: {"ok": v["ok"], "config_diffs": v["config_diffs"],
                              "resume_derived": v["resume_derived"]} for k, v in rep["checks"]["a_input_match"].items()},
        "b_pre_t0": rep["checks"]["b_pre_t0"],
        "c_first_divergence": {"world": c["world"],
                               "any": None if c["any"] is None else {k: c["any"][k] for k in ("step", "system", "keys")},
                               "coarse": c["coarse"], "nonportable_keys": c["nonportable_keys"], "reason": c["reason"],
                               "window_steps": c["window_steps"], "probe_rows": c["probe_rows"],
                               "branch_repeat_same": c["branch_repeat_same"]},
        "execution": rep["execution"],
        "d_aa": rep["checks"]["d_aa"], "experiment_meter": m["meter"], "replay": m["replay"],
        "staffed_targets": rep["execution"]["branch"]["staffed_targets"],
        "opening_counters_branch": out.branch.runner.opening.counters(),
        "opening_counters_aa": out.twin_a.runner.opening.counters(),
        "wall_seconds": {"base": round(base_s, 1), "branch_runs": round(br_s, 1)},
    }
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                           newline="\n")
    print(json.dumps(doc["summary"], ensure_ascii=False), doc["wall_seconds"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
