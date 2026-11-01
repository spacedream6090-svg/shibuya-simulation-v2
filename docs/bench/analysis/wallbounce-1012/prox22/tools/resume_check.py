"""第 2 期 2-2: 腕 distance の再開 == 通し(世界資産 1,000 体・1 日・語彙 v3・記憶+関係+同席・止める 750)の控え。

試験 ``tests/engine/proximity/test_runs.py::test_world_resume_equals_straight_and_the_marks_matter`` と同じ構成を回し、
通し・前半・再開の final・呼数・止めた後の checkpoint のハッシュの一致と、気づく抽選の本数を JSON に書く。
状態のファイルは一時の置き場(終わったら消す)。絶対パスは書かない。

    PYTHONPATH=src python docs/bench/analysis/wallbounce-1012/prox22/tools/resume_check.py --out <記録の置き場>/resume_rebased.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

STOP = 750
WRES = dict(n_agents=1_000, seed=1, world_dir="data/world/v2", vocab_version="v3", memory="on", relations="on",
            rel_copresent="on", checkpoint_every=60)


def _hashes(res, from_T):
    return [(c.tick, c.combined, c.behavior_hash, c.full_hash) for c in res.checkpoints if c.tick >= from_T]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from shibuya import cli
    from shibuya.engine import proximity as P

    P.set_arm("distance")
    P.set_d(2.0)
    tmp = Path(tempfile.mkdtemp(prefix="prox22_resume_"))
    try:
        straight = cli.run(**WRES)
        a = cli.run(state_out=tmp / "st", stop_at_tick=STOP, **WRES)
        f = tmp / "st" / a.resume["state_files"][-1]["file"]
        b = cli.run(resume_from=f, **WRES)
        hs, hb = _hashes(straight, STOP), _hashes(b, STOP)
        rel = straight.run_manifest_fields()["relations"]["counts"]
        doc = {
            "schema": "shibuya.bench/prox22/resume/1",
            "config": {**{k: v for k, v in WRES.items() if k != "world_dir"}, "proximity": "distance", "d_m": 2.0,
                       "stop_at": STOP},
            "straight": {"final16": straight.final_hash[:16], "llm_calls": int(straight.llm_calls)},
            "first_half": {"llm_calls": int(a.llm_calls)},
            "resumed": {"final16": b.final_hash[:16], "llm_calls": int(b.llm_calls)},
            "final_equal": b.final_hash == straight.final_hash,
            "calls_equal": int(a.llm_calls) + int(b.llm_calls) == int(straight.llm_calls),
            "checkpoints_after_stop": len(hs), "checkpoint_hashes_equal": hs == hb,
            "acq_notice_draws": int(rel.get("acq_notice_draws", 0)), "acq_noticed": int(rel.get("acq_noticed", 0)),
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    doc["all_equal"] = bool(doc["final_equal"] and doc["calls_equal"] and doc["checkpoint_hashes_equal"])
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc, ensure_ascii=False))
    return 0 if doc["all_equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
