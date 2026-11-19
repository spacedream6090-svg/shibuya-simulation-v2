"""第346 旧道の切替口の削除: 消した切替口はランの入口で止まる(検収 H1・L1)。

- 消した切替口の環境変数(``engine.removed_switches.REMOVED_ENV``)を与えたランは、``run_day`` でも ``cli.main`` でも刻みに
  入る前に非ゼロで終わる(切替口を持っていたモジュールを毎回のランで import するとは限らない=組み立ての最初で見る)。
- 消した CLI の旗(``REMOVED_CLI_FLAGS``)は表に出さずに受けて引数の誤りで止める(略記で ``--proximity`` が ``--proximity-d``
  に読まれない)。
- 一覧と止める文は 1 か所(各モジュールの読み込みの止めも同じ文)。
記録 ``docs/bench/analysis/delete-346/README.md``。〔第347 止めた切替口の削除〕経済の段階 2 の切替口 off
(``SHIBUYA_ECONOMY_STAGE2``・``--economy-stage2``)と、率の規則と「無い」の過程の旧道(``SHIBUYA_RATE_RULES``・``--rate-rules``・
``SHIBUYA_ABSENT_PROCESSES``・``--absent-processes``)と、移動の旧道(``SHIBUYA_SPACE``・``--space``)と、空腹のモデルの旗
(``--hunger-model``=環境変数の無い旗だけの行)を足した。安定版のタグは消した段ごとに違う(``tag_of``)=記録
``docs/bench/analysis/switch-removal-347/README.md``。
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from shibuya.runtime.systems import assemble as _ASSEMBLE
from shibuya.runtime.systems import conductor as _CONDUCTOR

from shibuya.interfaces.cli import main as cli
from shibuya.foundation.arms import removed as RSW

TAG = "stable-v2-before-switch-removal-346"
TAG_347 = "stable-v2-before-switch-removal-347"
RUN_DAY = ("from shibuya.runtime.run import run_day\n"
           "run_day(n_agents=20, seed=1, n_cells=9, ticks=30, checkpoint_every=30, renderer='stub')\n"
           "print('RAN')\n")
CLI_MAIN = ("import sys\nfrom shibuya.interfaces.cli import main as cli\n"
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
            "SHIBUYA_RATE_RULES": TAG_347, "SHIBUYA_ABSENT_PROCESSES": TAG_347, "SHIBUYA_SPACE": TAG_347,
            "--seat-release": TAG, "--proximity": TAG, "--defect-fixes-1103": TAG, "--economy-stage2": TAG_347,
            "--rate-rules": TAG_347, "--absent-processes": TAG_347, "--space": TAG_347, "--hunger-model": TAG_347}


def test_the_list_and_the_message_are_in_one_place():
    assert RSW.REMOVED_SWITCH_TAG == TAG and RSW.REMOVED_SWITCH_TAG_347 == TAG_347
    assert set(RSW.REMOVED_ENV) == {"SHIBUYA_RULES_42B", "SHIBUYA_RULES_42", "SHIBUYA_SEAT_RELEASE", "SHIBUYA_PROXIMITY",
                                    "SHIBUYA_DEFECT_FIXES_1103", "SHIBUYA_ECONOMY_STAGE2",
                                    "SHIBUYA_RATE_RULES", "SHIBUYA_ABSENT_PROCESSES",  # 〔第347 ②b〕率の規則と「無い」の過程
                                    "SHIBUYA_SPACE"}  # 〔第347 ③a〕移動の旧道
    assert set(RSW.REMOVED_CLI_FLAGS) == {"--seat-release", "--proximity", "--defect-fixes-1103", "--economy-stage2",
                                          "--rate-rules", "--absent-processes", "--space",
                                          "--hunger-model"}  # 〔第347 ③b〕空腹のモデルの旗(環境変数は無い)
    # 旗の行の値は環境変数の一覧の名か、旗だけの行の None(〔第347 ③b〕--hunger-model)
    assert {v for v in RSW.REMOVED_CLI_FLAGS.values() if v is not None} <= set(RSW.REMOVED_ENV)
    assert [f for f, v in RSW.REMOVED_CLI_FLAGS.items() if v is None] == ["--hunger-model"]
    assert {name: RSW.tag_of(name) for name in WANT_TAG} == WANT_TAG
    # 第346 の行の文は前のまま(段の名とタグ)
    assert RSW.message("SHIBUYA_PROXIMITY") == ("SHIBUYA_PROXIMITY は消した切替口(第346 旧道の切替口の削除・旧値の再現は"
                                                f"安定版のタグ {TAG})=環境変数を外す")
    assert RSW.message("--economy-stage2") == ("--economy-stage2 は消した切替口(第347 止めた切替口の削除・旧値の再現は"
                                               f"安定版のタグ {TAG_347})=旗を外す")
    # 〔第347 ③b〕旗だけの行の文は、残る口(run_day と cli.run の引数)を書く
    assert RSW.message("--hunger-model") == ("--hunger-model は消した切替口(第347 止めた切替口の削除・旧値の再現は"
                                             f"安定版のタグ {TAG_347})=旗を外す。run_day と cli.run の引数 hunger_model は"
                                             "残る(既定は energy)。旧規則 v1 は Q13 の版上げで止めた=試験の中だけの口"
                                             "(world.body.energy の _HUNGER_V1_FOR_TESTS)")
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
    code = ("from shibuya.act.ops import body_writes as R\n"
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
                                  ["--economy-stage2"],
                                  # 〔第347 ②b〕率の規則と「無い」の過程(値に依らず・略記も。``--ab`` は ``--ablate`` と重なる)
                                  ["--rate-rules", "legacy"], ["--rate-rules", "off"], ["--rate-r", "legacy"],
                                  ["--absent-processes", "legacy"], ["--absent-processes", "stopped"],
                                  ["--absent", "legacy"],
                                  # 〔第347 ③a〕移動の旧道(値に依らず・略記も。``--sp`` は ``--speech-port`` と重なる。残す
                                  # ``--slope``・``--turn-weight`` は ``test_the_space_arm_flags_still_work_…``)
                                  ["--space", "legacy"], ["--space", "nav1"], ["--spa", "legacy"],
                                  # 〔第347 ③b〕空腹のモデルの旗(値に依らず・略記も。``--hunger`` は ``--hunger-words`` と
                                  # 重なる=``test_the_hunger_words_flag_still_works_…``)
                                  ["--hunger-model", "v1"], ["--hunger-model", "energy"], ["--hunger-m", "v1"]])
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


@pytest.mark.parametrize("argv", [["--economy-stage2-parts", "wages,tax"], ["--economy-stage2-parts=wages,tax"],
                                  ["--economy-stage2-p", "wages,tax"]])
def test_the_parts_flag_takes_a_right_value_the_equals_form_and_an_abbreviation(argv, monkeypatch):
    """〔第347・検収 A-7〕残す ``--economy-stage2-parts`` は、正しい値・``=`` つき・略記でも受けて部品を選ぶ(消した
    ``--economy-stage2`` に読まれない)。ランは回さない: ``cli.run`` を差し替えて、渡る前の部品と引数を見てから止める。
    〔③b〕CLI のランの空腹のモデルは旗が無くても energy(``CLI_DEFAULT_HUNGER_MODEL``)で渡ることも見る。"""
    from shibuya.economy import stage2_bind as ES2

    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)  # 試験の後に部品を戻す
    seen: dict = {}

    class _Stop(Exception):
        pass

    def _stub(**kw):  # noqa: ANN003, ANN202 — ランの代わり(部品と引数を写して止める)
        seen["parts"], seen["kw"] = ES2.active_parts(), kw
        raise _Stop

    monkeypatch.setattr(cli, "run", _stub)
    with pytest.raises(_Stop):
        cli.main([*argv, "--agents", "5", "--ticks", "1"])
    assert seen["parts"] == frozenset({"wages", "tax"})
    assert seen["kw"]["hunger_model"] == cli.CLI_DEFAULT_HUNGER_MODEL == "energy"


@pytest.mark.parametrize("flag", ["--slope", "--turn-weight"])
def test_the_space_arm_flags_still_work_and_are_not_read_as_the_removed_flag(flag, capsys):
    """〔第347 ③a〕移動の旗 ``--space`` を消しても、残す腕の旗 ``--slope``・``--turn-weight`` は今のまま受ける(値の誤りは
    その旗の選択肢の文で止まる=消した切替口の文でない)。"""
    with pytest.raises(SystemExit) as exc:
        cli.main([flag, "bogus", "--agents", "5", "--ticks", "1"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert flag in err and "bogus" in err and "消した切替口" not in err, err[-800:]


def test_the_hunger_words_flag_still_works_and_the_short_prefix_is_not_read_as_it(capsys):
    """〔第347 ③b〕旗 ``--hunger-model`` を消しても、残す腕の旗 ``--hunger-words`` は今のまま受ける(値の誤りはその旗の選択肢の
    文で止まる)。頭の重なる略記 ``--hunger`` は、消した旗と残す旗のどちらにも読まれず、あいまいな旗の誤りで止まる(黙って
    ``--hunger-words`` の値に読まれない)。"""
    with pytest.raises(SystemExit) as exc:
        cli.main(["--hunger-words", "bogus", "--agents", "5", "--ticks", "1"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "--hunger-words" in err and "bogus" in err and "消した切替口" not in err, err[-800:]
    with pytest.raises(SystemExit) as exc:
        cli.main(["--hunger", "all", "--agents", "5", "--ticks", "1"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "--hunger-model" in err and "--hunger-words" in err and "消した切替口" not in err, err[-800:]


def test_the_hidden_flags_are_not_in_the_help(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    out = capsys.readouterr().out
    assert "[--proximity-d " in out  # 使い方の行に出る旗の形
    for flag in RSW.REMOVED_CLI_FLAGS:
        assert f"[{flag} " not in out and f"[{flag}]" not in out, flag  # 使い方の行に出ない
        assert f"\n  {flag} " not in out and f"\n  {flag}\n" not in out, flag  # 旗の説明の行に出ない
