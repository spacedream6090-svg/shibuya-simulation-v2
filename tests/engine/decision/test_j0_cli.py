"""第 1 期 1-8 J0: CLI ``--decision-port`` は指定したとき環境変数 ``SHIBUYA_DECISION_PORT`` より強い(1-3 の検収 L3・1-6 の L9 と同じ形)。

環境変数は層のモジュールを読み込む時に読むので、子のプロセスで回す(合成の世界・40 体・360 刻み)。腕は ``--checkpoints-out`` の
manifest の ``decision_port.arm`` で見る。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

ARGS = ["--agents", "40", "--seed", "1", "--world", "__no_such_dir__", "--cells", "9", "--ticks", "360"]


def _arm(tmp_path, name: str, env_arm: str, cli_arm: str | None) -> tuple[str, object]:
    out = tmp_path / f"{name}.json"
    argv = [*ARGS, "--checkpoints-out", str(out)] + ([] if cli_arm is None else ["--decision-port", cli_arm])
    env = dict(os.environ, SHIBUYA_DECISION_PORT=env_arm, PYTHONIOENCODING="utf-8")
    code = "import sys; from shibuya import cli; sys.exit(cli.main(sys.argv[1:]))"
    r = subprocess.run([sys.executable, "-c", code, *argv], capture_output=True, text=True, encoding="utf-8",
                       env=env, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    dp = json.loads(out.read_text(encoding="utf-8"))["manifest"]["decision_port"]
    return dp["arm"], dp["decisions"]


@pytest.mark.parametrize("env_arm,cli_arm,want", [
    ("legacy", "port", "port"),     # CLI の port が環境変数の legacy に勝つ
    ("port", "legacy", "legacy"),   # CLI の legacy が環境変数の port に勝つ
    ("port", None, "port"),         # CLI の指定が無ければ環境変数のとおり
])
def test_cli_decision_port_beats_the_environment(tmp_path, env_arm, cli_arm, want):
    arm, decisions = _arm(tmp_path, f"{env_arm}_{cli_arm}", env_arm, cli_arm)
    assert arm == want and ((decisions is None) == (want == "legacy"))
