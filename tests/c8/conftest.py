"""tests.c8 の共通フィクスチャ。

``tools/c8`` は実行スクリプト置き場でパッケージではない(親がサーバーで
``python tools/c8/xxx.py`` と直接叩く)。テストからは ``sys.path`` に足して素の
モジュール名で import する(``tests/c6``・``tests/c7`` の conftest と同じ作法)。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_C8 = REPO_ROOT / "tools" / "c8"
WORLD_DIR = REPO_ROOT / "data" / "world" / "v2"
DATA_DIR = REPO_ROOT / "data"

if str(TOOLS_C8) not in sys.path:
    sys.path.insert(0, str(TOOLS_C8))

#: 実世界資産が無い環境(CI)では実データのテストを飛ばす。
real_data = pytest.mark.skipif(
    not (WORLD_DIR / "w12_generation_weights.parquet").exists(),
    reason="実世界資産 data/world/v2 が無い",
)

#: 国勢調査の小地域境界(W16 の対照に要る)。
real_estat = pytest.mark.skipif(
    not (DATA_DIR / "realworld" / "estat" / "r2ka13113" / "r2ka13113.shp").exists(),
    reason="e-Stat 小地域境界が無い",
)


@pytest.fixture(scope="session")
def c8lib():
    import c8lib as _m

    return _m


@pytest.fixture(scope="session")
def ablation_runner():
    import ablation_runner as _m

    return _m


@pytest.fixture(scope="session")
def sensitivity():
    import sensitivity as _m

    return _m


@pytest.fixture(scope="session")
def dashboard():
    import dashboard as _m

    return _m


@pytest.fixture(scope="session")
def ensemble():
    import ensemble as _m

    return _m


@pytest.fixture(scope="session")
def world_dir() -> Path:
    return WORLD_DIR


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return DATA_DIR
