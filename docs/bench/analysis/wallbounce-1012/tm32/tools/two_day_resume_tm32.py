"""第 3 期 3-2(tm32): 2 日のラン(5,000 体・seed 1・世界資産・既定 v3・テープつき)と再開=通しの控え。

``one`` は 1 本の「通し」か「止めて再開」を回して 1 行の JSON を出す(final・呼数・テープの calls と blocks の中身の sha・
manifest の batching の幅と窓の数)。``--mode`` は ``straight``(2 日の通し)・``day``(1 日目の終わり=刻み 1,440 で止めて
再開)・``mid``(2 日目の途中=刻み 2,211 で止めて再開)。幅の腕は環境変数 ``SHIBUYA_BATCH_WIDTH_S``(HEAD の写しは読まない)。
10e の ``two_day_check_act.py`` と同じ構成(``vocab_version="v3"``・``activity=True``)。絶対パスは書かない。

    PYTHONPATH=<HEAD の写しの src> python $D/two_day_resume_tm32.py one --mode straight --label head --scratch $W/h
    PYTHONPATH=src python $D/two_day_resume_tm32.py one --mode day --label w60_day --scratch $W/a
    SHIBUYA_BATCH_WIDTH_S=30 PYTHONPATH=src python $D/two_day_resume_tm32.py one --mode mid --label w30_mid --scratch $W/b
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

if str(Path(__file__).resolve().parents[5] / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "src"))

from shibuya.core.time_consts import STEPS_PER_DAY  # noqa: E402

TPD = STEPS_PER_DAY
STOPS = {"day": TPD, "mid": TPD + 771}


def _sha_table(path: Path) -> str:
    import pyarrow.parquet as pq

    t = pq.read_table(path)
    h = hashlib.sha256()
    for n in t.column_names:
        h.update(n.encode("utf-8"))
        h.update(json.dumps(t.column(n).to_pylist(), ensure_ascii=False, default=str).encode("utf-8"))
    return h.hexdigest()[:16]


def cmd_one(a: argparse.Namespace) -> int:
    import shibuya
    from shibuya import cli

    t0 = time.perf_counter()
    sc = Path(a.scratch)
    sc.mkdir(parents=True, exist_ok=True)
    kw = dict(n_agents=a.agents, seed=a.seed, world_dir=a.world, sim_days=2, vocab_version="v3", activity=True)
    out: dict = {"label": a.label, "mode": a.mode, "batch_width_env": os.environ.get("SHIBUYA_BATCH_WIDTH_S", ""),
                 "src_is_worktree": Path(shibuya.__file__).resolve().is_relative_to(Path.cwd().resolve() / "src")}
    if a.mode == "straight":
        res = cli.run(tape_path=sc / "tape", **kw)
        tapes = [sc / "tape"]
    else:
        stop = STOPS[a.mode]
        first = cli.run(state_out=sc / "state", stop_at_tick=stop, tape_path=sc / "tape_a", **kw)
        f = first.resume["state_files"][-1]["file"]
        res = cli.run(resume_from=sc / "state" / f, tape_path=sc / "tape_b", **kw)
        tapes = [sc / "tape_a", sc / "tape_b"]
        out.update({"stop_T": stop, "first_final": first.final_hash[:16], "first_calls": int(first.llm_calls)})
    man = res.run_manifest_fields()
    bat = man.get("batching") or {}
    out.update({
        "final": res.final_hash[:16], "calls": int(res.llm_calls),
        "checkpoints_behavior": [c.behavior_hash[:16] for c in res.checkpoints],
        "tape_calls_sha": [_sha_table(t / "calls.parquet") for t in tapes],
        "tape_blocks_sha": [_sha_table(t / "blocks.parquet") for t in tapes],
        "batching_width_s": bat.get("width_s"), "batching_windows": bat.get("windows"),
        "batching_carried": bat.get("carried"), "batching_pending_at_end": bat.get("pending_at_end"),
        "wall_s": round(time.perf_counter() - t0, 1),
    })
    print(json.dumps(out, ensure_ascii=False))
    return 0


def main(argv=None) -> int:  # noqa: ANN001
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("one")
    sp.add_argument("--mode", choices=("straight", "day", "mid"), required=True)
    sp.add_argument("--label", required=True)
    sp.add_argument("--scratch", required=True)
    sp.add_argument("--agents", type=int, default=5_000)
    sp.add_argument("--seed", type=int, default=1)
    sp.add_argument("--world", default="data/world/v2")
    a = ap.parse_args(argv)
    return {"one": cmd_one}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
