"""**T3 並列不変性**(運用設計書 §1.4「スレッド 1/8/32 で同一結果」)。

コード側に「並列度の口」は無い
    エンジンは単一プロセスで、``prange``(numba の並列ループ)を持つのは ``build.geo`` /
    ``build.vis``(世界構築=ランの外)だけ。ラン中の numba は
    ``engine.change_detect._cell_wake_numba`` の **nogil 逐次カーネル 1 本**である
    (``grep -rn "prange" src/shibuya/engine`` = 0 件)。
    したがって T3 は「**スレッド数を変えた別プロセスで同じ結果が出るか**」として測る:
    ``NUMBA_NUM_THREADS`` / ``OMP_NUM_THREADS`` / ``MKL_NUM_THREADS`` を 1 と 8 にした
    2 プロセスで ``tools/c6/run_hash.py`` を回し、checkpoint ハッシュを突き合わせる。
    (設計書の「32」も同じ仕掛けで測れるが、CI の時間を食うので 1/8 を既定にした=expedient。
    ``--threads`` 引数でプロセス内 ``numba.set_num_threads`` も試す。)

同一プロセス内では ``engine.change_detect`` の numba 版と NumPy 版のバイト一致
(``tests/engine/test_change_detect_p6.py``)が並列度非依存性の内側の保証になっている。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from .conftest import TOOLS_C6, real_data

SMALL = ["--agents", "400", "--ticks", "24", "--cells", "25", "--world", "__no_such_dir__"]


def _run_hash(threads: str, extra: list[str] | None = None) -> dict:
    env = dict(os.environ)
    env.update(
        {
            "PYTHONUTF8": "1",
            "NUMBA_NUM_THREADS": threads,
            "OMP_NUM_THREADS": threads,
            "MKL_NUM_THREADS": threads,
            "OPENBLAS_NUM_THREADS": threads,
        }
    )
    cmd = [sys.executable, str(TOOLS_C6 / "run_hash.py"), *SMALL, *(extra or [])]
    p = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8", timeout=600)
    assert p.returncode == 0, p.stderr[-2000:]
    return json.loads(p.stdout.strip().splitlines()[-1])


def test_no_parallel_loop_exists_in_the_engine_at_run_time():
    """「並列度の口」の不在を機械で固定する(増えたら T3 の測り方を変える合図)。"""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "src" / "shibuya" / "engine"
    hits = [
        p.name
        for p in root.rglob("*.py")
        if "prange" in p.read_text(encoding="utf-8")
        or "parallel=True" in p.read_text(encoding="utf-8")
    ]
    assert hits == [], f"engine に並列ループが増えた: {hits}(T3 の測り方を見直すこと)"


@pytest.mark.slow
def test_t3_final_hash_is_identical_across_thread_counts(capsys):
    a = _run_hash("1")
    b = _run_hash("8")
    with capsys.disabled():
        print(
            f"\n[T3] NUMBA_NUM_THREADS 1 vs 8: final_hash "
            f"{a['final_hash'][:16]}… / {b['final_hash'][:16]}…"
        )
    assert a["final_hash"] == b["final_hash"]
    assert a["checkpoints"] == b["checkpoints"]
    assert a["agents_hashes"] == b["agents_hashes"]
    assert a["world_hashes"] == b["world_hashes"]
    assert a["llm_calls"] == b["llm_calls"]
    assert a["diagnostics_day"] == b["diagnostics_day"]


@pytest.mark.slow
def test_t3_in_process_set_num_threads_does_not_change_the_result():
    a = _run_hash("1", ["--threads", "1"])
    b = _run_hash("8", ["--threads", "8"])
    assert a["final_hash"] == b["final_hash"]


@real_data
@pytest.mark.slow
def test_t3_on_the_real_world_at_5000_agents(capsys):
    """実データ 5,000 体 × 24 tick(§9.1 C6 のスモーク規模)。"""
    args = ["--agents", "5000", "--ticks", "24", "--world", "data/world/v2"]

    def go(threads: str) -> dict:
        env = dict(os.environ)
        env.update(
            {"PYTHONUTF8": "1", "NUMBA_NUM_THREADS": threads, "OMP_NUM_THREADS": threads}
        )
        p = subprocess.run(
            [sys.executable, str(TOOLS_C6 / "run_hash.py"), *args],
            env=env, capture_output=True, text=True, encoding="utf-8", timeout=900,
        )
        assert p.returncode == 0, p.stderr[-2000:]
        return json.loads(p.stdout.strip().splitlines()[-1])

    a, b = go("1"), go("8")
    with capsys.disabled():
        print(f"\n[T3 実データ] 呼 {a['llm_calls']:,} / final {a['final_hash'][:16]}…")
    assert a["final_hash"] == b["final_hash"]
    assert a["diagnostics_day"] == b["diagnostics_day"]
