"""第 1 期 1-8b 発話の口: CLI ``--speech-port`` と腕の扱い(1-8 J0 の ``--decision-port`` と同じ形)。

- CLI の指定は環境変数 ``SHIBUYA_SPEECH_PORT`` より強い(子のプロセス=環境変数は層のモジュールを読み込む時に読む)。腕は
  ``--checkpoints-out`` の manifest の ``speech_port.arm`` で見る。
- 腕 on は結果を変える=ランの種類は腕(``cli.run`` の決め方・試験の外)・設定の指紋に on のときだけ ``speech_port``。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from shibuya import cli
from shibuya.engine import run_kind as RK
from tests.engine.speech._s8b import speech_arm

ARGS = ["--agents", "40", "--seed", "1", "--world", "__no_such_dir__", "--cells", "9", "--ticks", "360"]


def _arm(tmp_path, name: str, env_arm: str, cli_arm: str | None) -> str:
    out = tmp_path / f"{name}.json"
    argv = [*ARGS, "--checkpoints-out", str(out)] + ([] if cli_arm is None else ["--speech-port", cli_arm])
    env = dict(os.environ, SHIBUYA_SPEECH_PORT=env_arm, PYTHONIOENCODING="utf-8")
    code = "import sys; from shibuya import cli; sys.exit(cli.main(sys.argv[1:]))"
    r = subprocess.run([sys.executable, "-c", code, *argv], capture_output=True, text=True, encoding="utf-8",
                       env=env, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(out.read_text(encoding="utf-8"))["manifest"]["speech_port"]["arm"]


@pytest.mark.parametrize("env_arm,cli_arm,want", [
    ("off", "on", "on"),     # CLI の on が環境変数の off に勝つ
    ("on", "off", "off"),    # CLI の off が環境変数の on に勝つ
    ("on", None, "on"),      # CLI の指定が無ければ環境変数のとおり
])
def test_cli_speech_port_beats_the_environment(tmp_path, env_arm, cli_arm, want):
    assert _arm(tmp_path, f"{env_arm}_{cli_arm}", env_arm, cli_arm) == want


def test_the_on_arm_is_an_arm_run(monkeypatch):
    """ランの種類(試験の外): 既定 off の既定の構成=再現・腕 on=腕(指紋の on の欄は ``test_speech_arm_rows_resume`` と
    ``test_speech_default_off_invariance`` が状態のファイルの見出しで見る)。"""
    kw = dict(n_agents=20, seed=1, world_dir=None, n_cells=9, ticks=30, checkpoint_every=10, vocab_version="v3")
    monkeypatch.delenv(RK.PYTEST_ENV, raising=False)
    with speech_arm("off"):
        off = cli.run(**kw)
    with speech_arm("on"):
        on = cli.run(**kw)
    assert (off.run_kind, on.run_kind) == ("reproduction", "arm")
