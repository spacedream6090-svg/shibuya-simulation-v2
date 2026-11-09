"""第346 旧道の切替口の削除: 消した切替口はランの入口で止まる(検収 H1・L1)。

- 消した切替口の環境変数(``engine.removed_switches.REMOVED_ENV``)を与えたランは、``run_day`` でも ``cli.main`` でも刻みに
  入る前に非ゼロで終わる(切替口を持っていたモジュールを毎回のランで import するとは限らない=組み立ての最初で見る)。
- 消した CLI の旗(``REMOVED_CLI_FLAGS``)は表に出さずに受けて引数の誤りで止める(略記で ``--proximity`` が ``--proximity-d``
  に読まれない)。
- 一覧と止める文は 1 か所(各モジュールの読み込みの止めも同じ文)。
記録 ``docs/bench/analysis/delete-346/README.md``。
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from shibuya import cli
from shibuya.engine import removed_switches as RSW

TAG = "stable-v2-before-switch-removal-346"
RUN_DAY = ("from shibuya.engine.run import run_day\n"
           "run_day(n_agents=20, seed=1, n_cells=9, ticks=30, checkpoint_every=30, renderer='stub')\n"
           "print('RAN')\n")
CLI_MAIN = ("import sys\nfrom shibuya import cli\n"
            "rc = cli.main(['--agents', '20', '--seed', '1', '--world', '__no_such_dir__', '--cells', '9', '--ticks', '30'])\n"
            "print('RAN')\nsys.exit(rc)\n")
#: 止まってよい系の置き場(進行役 conductor が最初に呼ぶ組み立て build の中=刻みの前)。ほかの系(刻みの中・日の終わり・
#: report)の中で落ちたら、刻みに入った後に止まった=入口で止まっていない。
_BEFORE_TICKS = {"conductor.py", "build.py"}


def _system_frames(stderr: str) -> list[str]:
    """traceback の ``engine/systems`` の下の置き場の名(呼ばれた順)。"""
    out = []
    for line in stderr.splitlines():
        line = line.strip().replace("\\", "/")
        if line.startswith('File "') and "/engine/systems/" in line:
            out.append(line.split('"')[1].rsplit("/", 1)[-1])
    return out


def test_the_list_and_the_message_are_in_one_place():
    assert RSW.REMOVED_SWITCH_TAG == TAG
    assert set(RSW.REMOVED_ENV) == {"SHIBUYA_RULES_42B", "SHIBUYA_RULES_42", "SHIBUYA_SEAT_RELEASE", "SHIBUYA_PROXIMITY",
                                    "SHIBUYA_DEFECT_FIXES_1103"}
    assert set(RSW.REMOVED_CLI_FLAGS) == {"--seat-release", "--proximity", "--defect-fixes-1103"}
    assert set(RSW.REMOVED_CLI_FLAGS.values()) <= set(RSW.REMOVED_ENV)
    RSW.check_environment({})
    RSW.check_environment({name: "" for name in RSW.REMOVED_ENV})  # 空の値は置いていない扱い
    for name in RSW.REMOVED_ENV:
        with pytest.raises(ValueError, match=f"{name} は消した切替口.*{TAG}"):
            RSW.check_environment({name: "on"})


@pytest.mark.parametrize("entry", ["run_day", "cli_main"])
@pytest.mark.parametrize("name", sorted(RSW.REMOVED_ENV))
def test_a_run_with_a_removed_switch_env_stops_before_the_ticks(name, entry):
    """値によらず(既定の値でも)止まる。止まるのは組み立ての最初か、切替口を持っていたモジュールの読み込み=刻みの前。"""
    for value in ("legacy", "on"):
        env = {**os.environ, name: value, "PYTHONIOENCODING": "utf-8"}
        code = RUN_DAY if entry == "run_day" else CLI_MAIN
        r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, encoding="utf-8",
                           timeout=600)
        assert r.returncode != 0, (name, value, r.stdout[-500:])
        assert "RAN" not in r.stdout
        assert f"{name} は消した切替口" in r.stderr and TAG in r.stderr, r.stderr[-1500:]
        frames = _system_frames(r.stderr)
        assert set(frames) <= _BEFORE_TICKS, (frames, r.stderr[-1500:])  # 読み込みか組み立ての最初で止まった
        assert not frames or frames[-1] == "build.py", frames


@pytest.mark.parametrize("argv", [["--proximity", "1.0"], ["--proximity", "cell"], ["--proximity"],
                                  ["--seat-release", "walk"], ["--seat-rel", "legacy"], ["--defect-fixes-1103", "on"],
                                  ["--defect", "legacy"]])
def test_a_removed_cli_flag_stops_even_when_abbreviated(argv, capsys):
    """〔検収 L1〕``--proximity 1.0`` が略記で ``--proximity-d`` の感度の腕として通らない。"""
    with pytest.raises(SystemExit) as exc:
        cli.main([*argv, "--agents", "5", "--ticks", "1"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "は消した切替口" in err and TAG in err


def test_the_hidden_flags_are_not_in_the_help(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    out = capsys.readouterr().out
    assert "[--proximity-d " in out  # 使い方の行に出る旗の形
    for flag in RSW.REMOVED_CLI_FLAGS:
        assert f"[{flag} " not in out and f"[{flag}]" not in out, flag  # 使い方の行に出ない
        assert f"\n  {flag} " not in out and f"\n  {flag}\n" not in out, flag  # 旗の説明の行に出ない
