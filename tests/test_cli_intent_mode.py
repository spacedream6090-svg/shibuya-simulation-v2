"""CLI ``--intent-mode {vocab,open,hint}``(AB7 自由意図の腕の切替口・仕様書 §2 の表)。

``--no-signage`` の往復テスト(``tests/perception/test_ablation6_signage.py``)と同じ書き方:
``cli.run`` を差し替えて ``main`` が何を渡したかを見る + 実際に回して run manifest を見る。
"""

from __future__ import annotations

import pytest

from shibuya.perception.templates import DEFAULT_INTENT_MODE, INTENT_MODES

SMALL = dict(
    n_agents=32, seed=1, world_dir=None, n_cells=9, ticks=2, checkpoint_every=2,
    processes=False, conversations=False,
)


@pytest.mark.parametrize("mode", ["open", "hint"])
def test_cli_run_passes_intent_mode_through_kwargs(mode):
    from shibuya import cli

    res = cli.run(intent_mode=mode, **SMALL)
    assert res.run_manifest_fields()["intent_mode"] == mode
    assert res.intent_mode == mode


def test_cli_run_defaults_to_vocab():
    from shibuya import cli

    res = cli.run(**SMALL)
    assert res.run_manifest_fields()["intent_mode"] == DEFAULT_INTENT_MODE == "vocab"


@pytest.mark.parametrize(
    "argv,expected",
    [
        ([], "vocab"),
        (["--intent-mode", "open"], "open"),
        (["--intent-mode", "vocab"], "vocab"),
        (["--intent-mode", "hint"], "hint"),
    ],
)
def test_cli_main_has_the_intent_mode_flag(monkeypatch, argv, expected):
    from shibuya import cli

    seen: dict = {}

    class _Stub:
        fleet_fields: dict = {}

        def summary(self) -> str:
            return "(stub)"

    monkeypatch.setattr(cli, "run", lambda **kw: (seen.update(kw), _Stub())[1])
    assert cli.main(["--agents", "8", "--world", "__no_such_dir__", "--cells", "9", *argv]) == 0
    assert seen["intent_mode"] == expected


def test_cli_choices_come_from_the_templates_module(capsys):
    """choices は ``templates.INTENT_MODES`` が正典(文字列を CLI 側に二重に持たない)。"""
    from shibuya import cli

    with pytest.raises(SystemExit):
        cli.main(["--intent-mode", "free"])
    err = capsys.readouterr().err
    for mode in INTENT_MODES:
        assert mode in err
