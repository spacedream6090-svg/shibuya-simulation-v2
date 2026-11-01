"""`python -m shibuya.cli --help` が描けること(第342・R-130 が見つけた既存の不具合=help の文の `%` が
`・` の前で書式の指定として読まれ ValueError になっていた。argparse の help では `%` は `%%` と書く)。"""

from __future__ import annotations

import pytest

from shibuya import cli


def test_help_renders_and_exits_zero(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "--memory-model" in out
    assert "15%・境目" in out
    assert "%%" not in out
