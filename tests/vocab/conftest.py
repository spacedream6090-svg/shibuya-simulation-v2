"""tests.vocab の共通フィクスチャ。

``tools/vocab`` は実行スクリプト置き場でパッケージではない(親が
``python tools/vocab/adjudicate.py …`` と直接叩く)。テストからは ``sys.path`` に足して
素のモジュール名で import する(``tests/c6``・``tests/c7``・``tests/c8`` の conftest と同じ作法)。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_VOCAB = REPO_ROOT / "tools" / "vocab"
TAPE_S1 = REPO_ROOT / "data" / "tape" / "c8_ab7_s1" / "AB7-OPEN-INTENT__open"

if str(TOOLS_VOCAB) not in sys.path:
    sys.path.insert(0, str(TOOLS_VOCAB))

#: AB7 の実テープが無い環境(CI)では実データのテストを飛ばす。
real_tape = pytest.mark.skipif(
    not (TAPE_S1 / "calls.parquet").exists(), reason="AB7 seed 1 のテープが無い"
)


@pytest.fixture(scope="session")
def adjudicate():
    import adjudicate as _m

    return _m


@pytest.fixture(scope="session")
def registry_from_tape():
    import registry_from_tape as _m

    return _m
