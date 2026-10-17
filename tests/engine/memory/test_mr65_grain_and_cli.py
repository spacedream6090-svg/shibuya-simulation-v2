"""第 6 期 6-5: 体の出来事の粒度の腕(``--memory-grain day``=2-3 の 14.6 行/体/日を減らす案)と CLI の腕。

- 粒度 day: 同じ記憶の行は日に 1 行だけ記録へ書く(2 回目からは目印を前のまま・回数と M1 の時刻は進める)。合成の世界で
  記録の体の出来事の行が減る・想起の候補はそのまま(テープの既存の列=``recalled_event_ids`` の外は全部同じ・final も同じ)・
  目印は前のままの記録の出来事(記録にある・同じ日)。再開は止める(本段の限界)。
- CLI: ``--memory-model``・``--memory-cue``・``--memory-embed-model``・``--memory-people``・``--memory-grain`` は指定したとき
  環境変数より強い(子のプロセス)。腕を選んだ ``cli.run`` のランの種類は「腕」。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import numpy as np
import pytest

from shibuya.core.time_consts import STEPS_PER_DAY
from shibuya.engine.run import run_day
from shibuya.engine.tape import Tape

from tests.engine.memory._mr65 import KW, arms, mr65
from tests.engine.multiday._md import Capture


def _cols(path):
    t = Tape(path)
    return {c: list(t.column(c)) for c in t.calls.column_names if c != "recalled_event_ids"}


def test_grain_day_writes_fewer_rows_and_keeps_the_recall(monkeypatch, tmp_path):
    cap = Capture(monkeypatch)
    with arms("events"):
        a = run_day(tape_path=tmp_path / "each", **KW)
    n_each = int(cap.log.n_appended)
    cap2 = Capture(monkeypatch)
    with arms("events", grain="day"):
        b = run_day(tape_path=tmp_path / "day", **KW)
    n_day = int(cap2.log.n_appended)
    assert b.final_hash == a.final_hash and b.llm_calls == a.llm_calls
    assert _cols(tmp_path / "day") == _cols(tmp_path / "each")
    kept = b.run_manifest_fields()["memory_summary"]["memory_store"]["counts"]["pointer_kept"]
    assert kept > 0 and n_day == n_each - kept  # 減った行=目印を前のままにした回
    assert mr65(b)["arms"]["grain"] == "day"
    # 目印は記録にある出来事(同じ日の前の回)
    ms = cap2.store
    g = np.flatnonzero(ms._ms_origin == 0)
    pos = cap2.log.positions(ms._ms_ev_t_ns[g], ms._ms_ev_seq[g].astype(np.int64))
    assert (pos >= 0).all()


def test_grain_day_refuses_to_resume(tmp_path):
    kw = dict(KW, ticks=int(STEPS_PER_DAY), sim_days=2, checkpoint_every=60)
    with arms("events", grain="day"):
        a = run_day(state_out=tmp_path / "state", stop_at_tick=int(STEPS_PER_DAY), **kw)
        with pytest.raises(RuntimeError, match="再開に対応しない"):
            run_day(resume_from=tmp_path / "state" / a.resume["state_files"][-1]["file"], **kw)


ARGS = ["--agents", "40", "--seed", "1", "--world", "__no_such_dir__", "--cells", "9", "--ticks", "120",
        "--memory", "on", "--memory-store", "events"]
CODE = ("import sys, json; from shibuya import cli; from shibuya.engine import memory_m1 as M; "
        "rc = cli.main(sys.argv[1:]); print('ARMS=' + json.dumps(M.arms()._asdict())); sys.exit(rc)")


def _arms(env: dict, extra: list[str]) -> dict:
    r = subprocess.run([sys.executable, "-c", CODE, *ARGS, *extra], capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, PYTHONIOENCODING="utf-8", **env), timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    line = next(x for x in r.stdout.splitlines() if x.startswith("ARMS="))
    return json.loads(line[len("ARMS="):])


def test_cli_memory_arms_beat_the_environment():
    got = _arms({"SHIBUYA_MEMORY_MODEL": "m0", "SHIBUYA_MEMORY_GRAIN": "day"},
                ["--memory-model", "m1", "--memory-cue", "embed", "--memory-embed-model", "ngram-test",
                 "--memory-grain", "each"])
    assert (got["model"], got["cue"], got["embed_model"], got["grain"], got["people"]) == (
        "m1", "embed", "ngram-test", "each", "table")
    got = _arms({"SHIBUYA_MEMORY_MODEL": "m1", "SHIBUYA_MEMORY_PEOPLE": "memory"}, [])
    assert (got["model"], got["people"]) == ("m1", "memory")
    # 〔検収 M1〕人ごとの忘れる速さの seed は腕の大域の値に持たない(組み立てがランの母集団の seed を渡す=test_m1_runs)
    assert "rate_seed" not in got


def test_cli_run_kind_counts_the_memory_arms(monkeypatch):
    from shibuya import cli
    from shibuya.engine import run_kind as RK

    monkeypatch.delenv(RK.PYTEST_ENV, raising=False)  # 試験の中は種類が test になる=外して腕の数え方を見る
    kw = dict(n_agents=30, seed=1, n_cells=9, ticks=60, memory="on", vocab_version="v3")
    with arms("events", model="m1"):
        k1 = cli.run(**kw).run_manifest_fields()["run_kind"]
    with arms("events"):
        k0 = cli.run(**kw).run_manifest_fields()["run_kind"]
    assert k1 == "arm" and k0 != "test"
