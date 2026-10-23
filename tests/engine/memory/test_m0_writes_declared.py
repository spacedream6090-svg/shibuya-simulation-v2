"""第 1 期 1-6 記憶の器 M0: 器を書く系の宣言(口の約束の共通の約束「SYSTEMS の宣言に書き手を足す=段 B で宣言の外 0」)。

- 段 B(正): 腕 on のランで、系の前後で変わった欄(SoA・外の道筋・scratch ほか)⊆ 宣言(器の行 M0・M0R を含む)。
- 負の対照: 宣言(``writes.paths``)から器の道筋を外すと、書いた所で器の口の実行時の検査が落とす(memory の M0・
  decide の M0*・drain は艦隊の無いランでは書かない)。
"""

from __future__ import annotations

import pytest

from shibuya.core import write_permit as WP
from shibuya.engine.run import run_day
from shibuya.engine.systems import conductor as CD
from shibuya.engine.systems import overrides as OV
from shibuya.engine.systems import probe as PR
from shibuya.engine.systems.table import SPECS

from tests.engine.memory._m0 import KW, arm

FAM = ("soa", "ext", "stats", "buffers", "scratch")


@pytest.fixture(autouse=True)
def _guard_on():
    prev = WP.enabled()
    WP.set_enabled(True)
    yield
    WP.set_enabled(prev)


def test_declared_writes_cover_the_store_changes():
    pr = PR.Probe(check=CD.declared_check(SPECS), ticks=frozenset(range(0, 720, 7)), families=FAM)
    PR.ACTIVE = pr
    try:
        with arm("events"):
            run_day(**KW)
    finally:
        PR.ACTIVE = None
    assert pr.n_snap > 0 and not pr.violations, pr.violations[:10]


@pytest.mark.parametrize("system,path", [
    ("memory", "M0*:mem_layer.memory_store.*"),
    ("decide", "M0*:mem_layer.memory_store.*"),
])
def test_dropping_the_store_path_fails_where_it_is_written(system, path):
    with OV.drop_path(system, path), arm("events"), pytest.raises(PermissionError, match="記憶の器"):
        run_day(**KW)
