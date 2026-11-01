"""第 1 期 1-8 J0: 候補の口を書く系の宣言(口の約束の共通の約束「SYSTEMS の宣言に書き手を足す=段 B で宣言の外 0」)。

- 段 B(正): 腕 port のランで、系の前後で変わった欄(SoA・外の道筋・scratch ほか)⊆ 宣言(候補の口の行 J0=``J0:decision.*``・
  判断の出来事=``E:events.*``)。
- 負の対照: decide の宣言から ``J0:decision.*`` を外すと段 B が宣言の外の変化を見つける。``E:events.*`` を外すと判断の出来事を
  書く所で出来事の記録の実行時の検査が落とす。
"""

from __future__ import annotations

import pytest

from shibuya.core import write_permit as WP
from shibuya.engine.run import run_day
from shibuya.engine.systems import conductor as CD
from shibuya.engine.systems import overrides as OV
from shibuya.engine.systems import probe as PR
from shibuya.engine.systems.table import SPECS

from tests.engine.decision._j0 import SMALL, decision_arm

FAM = ("soa", "ext", "stats", "buffers", "scratch")
KW = {**SMALL, "memory": "on", "relations": "on"}


@pytest.fixture(autouse=True)
def _guard_on():
    prev = WP.enabled()
    WP.set_enabled(True)
    yield
    WP.set_enabled(prev)


def _probe_run():
    pr = PR.Probe(check=CD.declared_check(SPECS), ticks=frozenset(range(0, 360, 3)), families=FAM)
    PR.ACTIVE = pr
    try:
        with decision_arm("port"):
            r = run_day(**KW)
    finally:
        PR.ACTIVE = None
    return pr, r


def test_declared_writes_cover_the_port_changes():
    pr, r = _probe_run()
    assert pr.n_snap > 0 and not pr.violations, pr.violations[:10]
    assert r.run_manifest_fields()["decision_port"]["decisions"] > 0


def test_dropping_the_j0_path_is_caught_by_stage_b():
    with OV.drop_path("decide", "J0:decision.*"):
        pr, _r = _probe_run()
    assert pr.violations and any("decision" in str(v) for v in pr.violations), pr.violations[:5]


def test_dropping_the_events_path_fails_where_the_decision_event_is_written():
    with OV.drop_path("decide", "E:events.*"), decision_arm("port"), pytest.raises(PermissionError, match="E:events"):
        run_day(**KW)
