"""CLI ``--vocab-version {v1,v2}``(語彙成長 v0 の切替口・D-71 §3 F)。

``--intent-mode`` の往復テスト(``tests/test_cli_intent_mode.py``)と同じ書き方:
``cli.run`` を差し替えて ``main`` が何を渡したかを見る + 実際に回して run manifest を見る。
"""

from __future__ import annotations

import pytest

from shibuya.foundation.text.templates import DEFAULT_VOCAB_VERSION, VOCAB_VERSIONS

SMALL = dict(
    n_agents=32, seed=1, world_dir=None, n_cells=9, ticks=2, checkpoint_every=2,
    processes=False, conversations=False,
)


def test_cli_run_passes_vocab_version_through_kwargs():
    from shibuya import cli

    res = cli.run(vocab_version="v2", **SMALL)
    assert res.run_manifest_fields()["vocab_version"] == "v2"
    # C9b(G5 対象ヒント)で段0 辞書は v4 へ
    assert res.run_manifest_fields()["synonym_table_version"] == "undefined-synonyms-v4"
    assert res.vocab_version == "v2"


def test_cli_run_defaults_to_v3():
    """〔Q13・第347〕``cli.run`` の既定は CLI と同じ v3(前はライブラリの既定 v1)。"""
    from shibuya import cli

    res = cli.run(**SMALL)
    fields = res.run_manifest_fields()
    assert fields["vocab_version"] == cli.CLI_DEFAULT_VOCAB_VERSION == "v3"
    assert fields["synonym_table_version"] == "undefined-synonyms-v5"
    assert "action_usage" in fields


def test_the_default_run_is_byte_identical_with_the_explicit_v3():
    """〔Q13・第347〕既定のランは v3 の明示と同じ(前は v1 の明示と同じ)。"""
    from shibuya import cli

    base = cli.run(**SMALL)
    explicit = cli.run(vocab_version="v3", **SMALL)
    assert base.final_hash == explicit.final_hash
    assert cli.checkpoints_payload(base)["checkpoints"] == (
        cli.checkpoints_payload(explicit)["checkpoints"]
    )
    assert base.run_manifest_fields() == explicit.run_manifest_fields()


@pytest.mark.parametrize(
    "argv,expected",
    # 第277(二層の段 3): **CLI の既定は v3**(〔Q13〕ライブラリ ``run_day``/``cli.run`` の既定も v3=同じ 1 つの値)
    [([], "v3"), (["--vocab-version", "v1"], "v1"), (["--vocab-version", "v2"], "v2"),
     (["--vocab-version", "v3"], "v3")],
)
def test_cli_main_has_the_vocab_version_flag(monkeypatch, argv, expected):
    from shibuya import cli

    seen: dict = {}

    class _Stub:
        fleet_fields: dict = {}

        def summary(self) -> str:
            return "(stub)"

    monkeypatch.setattr(cli, "run", lambda **kw: (seen.update(kw), _Stub())[1])
    assert cli.main(["--agents", "8", "--world", "__no_such_dir__", "--cells", "9", *argv]) == 0
    assert seen["vocab_version"] == expected
    assert seen["intent_mode"] == "vocab", "腕と版は直交(既定は両方そのまま)"


def test_cli_choices_come_from_the_templates_module(capsys):
    """choices は ``templates.VOCAB_VERSIONS`` が正典(文字列を CLI 側に二重に持たない)。"""
    from shibuya import cli

    with pytest.raises(SystemExit):
        cli.main(["--vocab-version", "v9"])  # 第274 で v3 は choices に入った
    err = capsys.readouterr().err
    for version in VOCAB_VERSIONS:
        assert version in err


def test_intent_mode_and_vocab_version_are_orthogonal():
    """3 腕 × 2 版のどの組み合わせでも回り、manifest に両方が載る。"""
    from shibuya import cli

    # 第276(段 2): v3 のエンジン側が入った=全版を回す。**v3 は vocab 腕だけ**
    # (open/hint × v3 の B0 は未定義=``templates.b0_system`` が ValueError・段 1 の決め)。
    for mode in ("vocab", "open", "hint"):
        for ver in VOCAB_VERSIONS:
            if ver == "v3" and mode != "vocab":
                with pytest.raises(ValueError):
                    cli.run(intent_mode=mode, vocab_version=ver, **SMALL)
                continue
            res = cli.run(intent_mode=mode, vocab_version=ver, **SMALL)
            fields = res.run_manifest_fields()
            assert (fields["intent_mode"], fields["vocab_version"]) == (mode, ver)
            assert fields["activity"] is (ver == "v3"), "活動層は v3 でだけ立つ(既定 on)"


@pytest.mark.parametrize("argv,expected", [([], True), (["--activity", "on"], True),
                                           (["--activity", "off"], False)])
def test_cli_main_has_the_activity_flag(monkeypatch, argv, expected):
    """二層の段 2: ``--activity {on,off}``(既定 on)が ``run(activity=...)`` へ届く。"""
    from shibuya import cli

    seen: dict = {}

    class _Stub:
        fleet_fields: dict = {}

        def summary(self) -> str:
            return "(stub)"

    monkeypatch.setattr(cli, "run", lambda **kw: (seen.update(kw), _Stub())[1])
    assert cli.main(["--agents", "8", "--world", "__no_such_dir__", "--cells", "9", *argv]) == 0
    assert seen["activity"] is expected


def test_cli_and_run_default_vocab_are_one_value():
    """〔Q13・第347〕ランの入口の既定(``run_day``・``cli.run``・``RunResult``)と CLI の既定は同じ 1 つの値 v3
    (``engine.run.RUN_DEFAULT_VOCAB_VERSION``)。低い層の既定(``DEFAULT_VOCAB_VERSION`` の 2 か所)は v1 のまま(Q13 (s1)=
    パーサの中で低い層の既定に頼る所はユーザーの判断待ち)。"""
    import inspect

    from shibuya import cli
    # 〔割る段 5b の G2〕別名 RUN を割り先ごとに分けた(RUN=runtime.run・RES=runtime.result の名)
    from shibuya.runtime import run as RUN
    from shibuya.runtime import result as RES
    from shibuya.foundation.vocab.actions import DEFAULT_VOCAB_VERSION as LIB_DEFAULT

    assert cli.CLI_DEFAULT_VOCAB_VERSION == RES.RUN_DEFAULT_VOCAB_VERSION == "v3"
    assert inspect.signature(RUN.run_day).parameters["vocab_version"].default == "v3"
    assert RES.RunResult.__dataclass_fields__["vocab_version"].default == "v3"
    assert LIB_DEFAULT == DEFAULT_VOCAB_VERSION == "v1"
    assert cli.run(**SMALL).run_manifest_fields()["vocab_version"] == "v3"


@pytest.mark.parametrize("mode", ["open", "hint"])
def test_open_and_hint_arms_need_an_explicit_v1_or_v2_on_the_cli(mode, monkeypatch, capsys):
    """v3 の B0 は vocab 腕だけ=CLI の既定(v3)のまま open/hint を頼むと usage で落とす。"""
    from shibuya import cli

    monkeypatch.setattr(cli, "run", lambda **kw: None)
    with pytest.raises(SystemExit):
        cli.main(["--agents", "8", "--world", "__no_such_dir__", "--intent-mode", mode])
    assert "--vocab-version" in capsys.readouterr().err
