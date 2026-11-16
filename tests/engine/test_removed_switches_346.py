"""第346 旧道の切替口の削除: 消した切替口はランの入口で止まる(検収 H1・L1)。

- 消した切替口の環境変数(``engine.removed_switches.REMOVED_ENV``)を与えたランは、``run_day`` でも ``cli.main`` でも刻みに
  入る前に非ゼロで終わる(切替口を持っていたモジュールを毎回のランで import するとは限らない=組み立ての最初で見る)。
- 消した CLI の旗(``REMOVED_CLI_FLAGS``)は表に出さずに受けて引数の誤りで止める(略記で ``--proximity`` が ``--proximity-d``
  に読まれない)。
- 一覧と止める文は 1 か所(各モジュールの読み込みの止めも同じ文)。
記録 ``docs/bench/analysis/delete-346/README.md``。〔第347 止めた切替口の削除〕経済の段階 2 の切替口 off
(``SHIBUYA_ECONOMY_STAGE2``・``--economy-stage2``)を足した。安定版のタグは消した段ごとに違う(``tag_of``)=記録
``docs/bench/analysis/switch-removal-347/README.md``。
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from shibuya.runtime.systems import assemble as _ASSEMBLE
from shibuya.runtime.systems import conductor as _CONDUCTOR

from shibuya import cli
from shibuya.foundation.arms import removed as RSW

TAG = "stable-v2-before-switch-removal-346"
TAG_347 = "stable-v2-before-switch-removal-347"
RUN_DAY = ("from shibuya.engine.run import run_day\n"
           "run_day(n_agents=20, seed=1, n_cells=9, ticks=30, checkpoint_every=30, renderer='stub')\n"
           "print('RAN')\n")
CLI_MAIN = ("import sys\nfrom shibuya import cli\n"
            "rc = cli.main(['--agents', '20', '--seed', '1', '--world', '__no_such_dir__', '--cells', '9', '--ticks', '30'])\n"
            "print('RAN')\nsys.exit(rc)\n")
#: 系の置き場(traceback の道の一部)。〔第347 見つけた欠陥の直し〕前は文字列 ``/engine/systems/`` と ``build.py`` を
#: 書いていた=移す段 4(``engine/systems/build.py`` → ``runtime/systems/assemble.py``)の後は何も拾わず、下の「刻みの前で
#: 止まった」の確かめが空振りしていた。モジュールの名から作る(置き場が動いても追う)。負の対照は
#: ``test_the_frame_check_catches_a_stop_inside_the_ticks``。
_SYSTEMS_DIR = "/" + _CONDUCTOR.__name__.rsplit(".", 1)[0].replace(".", "/") + "/"
_ASSEMBLE_FILE = _ASSEMBLE.__name__.rsplit(".", 1)[1] + ".py"
#: 止まってよい系の置き場(進行役 conductor が最初に呼ぶ組み立て assemble の中=刻みの前)。ほかの系(刻みの中・日の終わり・
#: report)の中で落ちたら、刻みに入った後に止まった=入口で止まっていない。
_BEFORE_TICKS = {_CONDUCTOR.__name__.rsplit(".", 1)[1] + ".py", _ASSEMBLE_FILE}


def _system_frames(stderr: str) -> list[str]:
    """traceback の系の置き場(``runtime/systems``)の下のファイルの名(呼ばれた順)。"""
    out = []
    for line in stderr.splitlines():
        line = line.strip().replace("\\", "/")
        if line.startswith('File "') and _SYSTEMS_DIR in line:
            out.append(line.split('"')[1].rsplit("/", 1)[-1])
    return out


#: 〔第347〕名 → 旧値の再現の安定版のタグ(第346 の行は前のタグのまま)。
WANT_TAG = {"SHIBUYA_RULES_42B": TAG, "SHIBUYA_RULES_42": TAG, "SHIBUYA_SEAT_RELEASE": TAG, "SHIBUYA_PROXIMITY": TAG,
            "SHIBUYA_DEFECT_FIXES_1103": TAG, "SHIBUYA_ECONOMY_STAGE2": TAG_347,
            "--seat-release": TAG, "--proximity": TAG, "--defect-fixes-1103": TAG, "--economy-stage2": TAG_347}


def test_the_list_and_the_message_are_in_one_place():
    assert RSW.REMOVED_SWITCH_TAG == TAG and RSW.REMOVED_SWITCH_TAG_347 == TAG_347
    assert set(RSW.REMOVED_ENV) == {"SHIBUYA_RULES_42B", "SHIBUYA_RULES_42", "SHIBUYA_SEAT_RELEASE", "SHIBUYA_PROXIMITY",
                                    "SHIBUYA_DEFECT_FIXES_1103", "SHIBUYA_ECONOMY_STAGE2"}
    assert set(RSW.REMOVED_CLI_FLAGS) == {"--seat-release", "--proximity", "--defect-fixes-1103", "--economy-stage2"}
    assert set(RSW.REMOVED_CLI_FLAGS.values()) <= set(RSW.REMOVED_ENV)
    assert {name: RSW.tag_of(name) for name in WANT_TAG} == WANT_TAG
    # 第346 の行の文は前のまま(段の名とタグ)
    assert RSW.message("SHIBUYA_PROXIMITY") == ("SHIBUYA_PROXIMITY は消した切替口(第346 旧道の切替口の削除・旧値の再現は"
                                                f"安定版のタグ {TAG})=環境変数を外す")
    assert RSW.message("--economy-stage2") == ("--economy-stage2 は消した切替口(第347 止めた切替口の削除・旧値の再現は"
                                               f"安定版のタグ {TAG_347})=旗を外す")
    RSW.check_environment({})
    RSW.check_environment({name: "" for name in RSW.REMOVED_ENV})  # 空の値は置いていない扱い
    for name in RSW.REMOVED_ENV:
        with pytest.raises(ValueError, match=f"{name} は消した切替口.*{WANT_TAG[name]}"):
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
        assert f"{name} は消した切替口" in r.stderr and WANT_TAG[name] in r.stderr, r.stderr[-1500:]
        frames = _system_frames(r.stderr)
        assert set(frames) <= _BEFORE_TICKS, (frames, r.stderr[-1500:])  # 読み込みか組み立ての最初で止まった
        assert not frames or frames[-1] == _ASSEMBLE_FILE, frames


def test_the_frame_check_catches_a_stop_inside_the_ticks():
    """〔第347 見つけた欠陥の直し・負の対照〕刻みの中の系(本人の体の系が呼ぶ ``resolve.advance_body``)で止まったランは、
    traceback の系の置き場に刻みの前の外の名が出る=上の「刻みの前で止まった」の確かめ(``set(frames) <= _BEFORE_TICKS``)が
    落ちる。直す前の文字列(``/engine/systems/``)では何も拾わず、この形でも通っていた(記録 switch-removal-347)。"""
    code = ("from shibuya.engine import resolve as R\n"
            "def _stop(*a, **k):\n"
            "    raise ValueError('刻みの中で止めた(負の対照)')\n"
            "R.advance_body = _stop\n" + RUN_DAY)
    r = subprocess.run([sys.executable, "-c", code], env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                       capture_output=True, text=True, encoding="utf-8", timeout=600)
    assert r.returncode != 0 and "RAN" not in r.stdout and "刻みの中で止めた" in r.stderr, r.stderr[-1500:]
    frames = _system_frames(r.stderr)
    assert frames and frames[0] in _BEFORE_TICKS, frames  # 進行役から入った
    assert not set(frames) <= _BEFORE_TICKS, frames  # 刻みの中の系の名が出る=入口の確かめが落ちる形
    assert frames[-1] not in _BEFORE_TICKS, frames


@pytest.mark.parametrize("argv", [["--proximity", "1.0"], ["--proximity", "cell"], ["--proximity"],
                                  ["--seat-release", "walk"], ["--seat-rel", "legacy"], ["--defect-fixes-1103", "on"],
                                  ["--defect", "legacy"],
                                  # 〔第347〕``--economy-stage2-parts``(残す感度の腕)の頭=完全に一致する旗で止める
                                  ["--economy-stage2", "off"], ["--economy-stage2", "on"], ["--economy-stage2=off"],
                                  ["--economy-stage2"]])
def test_a_removed_cli_flag_stops_even_when_abbreviated(argv, capsys):
    """〔検収 L1〕``--proximity 1.0`` が略記で ``--proximity-d`` の感度の腕として通らない。〔第347〕``--economy-stage2 off`` が
    ``--economy-stage2-parts`` の略記として通らない(部品の名の誤りでなく、消した切替口の文で止まる)。"""
    with pytest.raises(SystemExit) as exc:
        cli.main([*argv, "--agents", "5", "--ticks", "1"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    flag = next(f for f in RSW.REMOVED_CLI_FLAGS if f.startswith(argv[0].split("=", 1)[0]))
    assert "は消した切替口" in err and WANT_TAG[flag] in err, err[-800:]


def test_the_parts_flag_still_works_and_is_not_read_as_the_removed_flag(capsys):
    """〔第347〕残す感度の腕 ``--economy-stage2-parts`` は今のまま受ける(名の誤りは部品の文で止まる=消した切替口の文でない)。"""
    with pytest.raises(SystemExit) as exc:
        cli.main(["--economy-stage2-parts", "wages,bonus", "--agents", "5", "--ticks", "1"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "--economy-stage2-parts は" in err and "消した切替口" not in err, err[-800:]


def test_the_hidden_flags_are_not_in_the_help(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    out = capsys.readouterr().out
    assert "[--proximity-d " in out  # 使い方の行に出る旗の形
    for flag in RSW.REMOVED_CLI_FLAGS:
        assert f"[{flag} " not in out and f"[{flag}]" not in out, flag  # 使い方の行に出ない
        assert f"\n  {flag} " not in out and f"\n  {flag}\n" not in out, flag  # 旗の説明の行に出ない
