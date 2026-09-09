"""tests.c6 の共通フィクスチャ。

``tools/c6`` は実行スクリプト置き場でパッケージではない(サーバーで
``python tools/c6/xxx.py`` と直接叩く)。テストからは ``sys.path`` に足して素の
モジュール名で import する。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_C6 = REPO_ROOT / "tools" / "c6"
WORLD_DIR = REPO_ROOT / "data" / "world" / "v2"

if str(TOOLS_C6) not in sys.path:
    sys.path.insert(0, str(TOOLS_C6))

#: 実世界資産が無い環境(CI)では実データのテストを飛ばす。
real_data = pytest.mark.skipif(
    not (WORLD_DIR / "w12_timetables.parquet").exists(),
    reason="実世界資産 data/world/v2 が無い",
)


@pytest.fixture(scope="session")
def c6lib():
    import c6lib as _m

    return _m


@pytest.fixture(scope="session")
def world_dir() -> Path:
    return WORLD_DIR


@pytest.fixture(scope="session")
def tools_dir() -> Path:
    return TOOLS_C6
