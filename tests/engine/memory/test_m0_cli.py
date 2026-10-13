"""第 1 期 1-6 記憶の器 M0: CLI ``--memory-store`` は指定したとき環境変数 ``SHIBUYA_MEMORY_STORE`` より強い(検収 L9)。

環境変数は器のモジュールを読み込む時に読むので、子のプロセスで回す(合成の世界・40 体・120 刻み・記憶 on・テープつき)。
腕が立ったかはテープの列の数で見る(腕 on=22 列・off=21 列)。1-3 の検収 L3(CLI の on が環境変数に負けた)の再発防止。
"""

from __future__ import annotations

import os
import subprocess
import sys

import pyarrow.parquet as pq
import pytest

from shibuya.engine.tape import CALLS_FILENAME

ARGS = ["--agents", "40", "--seed", "1", "--world", "__no_such_dir__", "--cells", "9", "--ticks", "120",
        "--memory", "on"]


def _columns(tmp_path, name: str, env_arm: str, cli_arm: str | None) -> int:
    tape = tmp_path / name
    argv = [*ARGS, "--tape", str(tape)] + ([] if cli_arm is None else ["--memory-store", cli_arm])
    env = dict(os.environ, SHIBUYA_MEMORY_STORE=env_arm, PYTHONIOENCODING="utf-8")
    code = "import sys; from shibuya import cli; sys.exit(cli.main(sys.argv[1:]))"
    r = subprocess.run([sys.executable, "-c", code, *argv], capture_output=True, text=True, encoding="utf-8",
                       env=env, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return len(pq.read_schema(tape / CALLS_FILENAME).names)


@pytest.mark.parametrize("env_arm,cli_arm,want", [
    ("mem", "events", 22),   # CLI の events が環境変数の mem に勝つ
    ("events", "mem", 21),   # CLI の mem が環境変数の events に勝つ
    ("events", None, 22),    # CLI の指定が無ければ環境変数のとおり
    ("mem", None, 21),
])
def test_cli_memory_store_beats_the_environment(tmp_path, env_arm, cli_arm, want):
    assert _columns(tmp_path, f"{env_arm}_{cli_arm}", env_arm, cli_arm) == want
