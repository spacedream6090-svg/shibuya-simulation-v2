"""第 1 期 1-8b 発話の口: 口を書く系の宣言(口の約束の共通の約束「SYSTEMS の宣言に書き手を足す=段 B で宣言の外 0」)。

- 段 B(正): 腕 on のランで、系の前後で変わった欄(SoA・外の道筋・scratch ほか)⊆ 宣言(発話の口の腕の行=``S8:speech.*``・
  ``S8M:speech.*``・発話の出来事=``E:events.*``)。書く系は decide(届ける・話す)と llm_receive(到着の発話)。
- 負の対照: decide の宣言から ``S8:speech.*`` を外すと段 B が宣言の外の変化を見つける。``E:events.*`` を外すと発話の出来事を
  書く所で出来事の記録の実行時の検査が落とす。
"""

from __future__ import annotations

import pytest

from shibuya.core import write_permit as WP
from shibuya.engine.run import run_day
from shibuya.engine.systems import conductor as CD
from shibuya.engine.systems import overrides as OV
from shibuya.engine.systems import probe as PR
from shibuya.engine.systems.table import SPECS, SYSTEMS

from tests.engine.speech._s8b import SMALL, speech_arm

FAM = ("soa", "ext", "stats", "buffers", "scratch")


@pytest.fixture(autouse=True)
def _guard_on():
    prev = WP.enabled()
    WP.set_enabled(True)
    yield
    WP.set_enabled(prev)


def _probe_run():
    pr = PR.Probe(check=CD.declared_check(SPECS), ticks=frozenset(range(0, 720, 2)), families=FAM)
    PR.ACTIVE = pr
    try:
        with speech_arm("on"):
            r = run_day(**SMALL)
    finally:
        PR.ACTIVE = None
    return pr, r


def test_the_writing_systems_are_declared():
    got = {s.name for s in SYSTEMS if "S8:speech.*" in s.writes.paths}
    assert got == {"decide", "llm_receive"}
    assert {s.name for s in SYSTEMS if "S8M:speech.*" in s.writes.paths} == got
    assert all("E:events.*" in SPECS[n].writes.paths for n in got)
    assert all("layers.speech" in SPECS[n].reads.box for n in got | {"close_final"})


def test_declared_writes_cover_the_port_changes():
    pr, r = _probe_run()
    assert pr.n_snap > 0 and not pr.violations, pr.violations[:10]
    m = r.run_manifest_fields()["speech_port"]
    assert m["said"] > 0 and m["delivered"] > 0


def test_dropping_the_s8_path_is_caught_by_stage_b():
    with OV.drop_path("decide", "S8:speech.*"):
        pr, _r = _probe_run()
    assert pr.violations and any("speech" in str(v) for v in pr.violations), pr.violations[:5]


def test_dropping_the_events_path_fails_where_the_utterance_is_written():
    with OV.drop_path("decide", "E:events.*"), speech_arm("on"), pytest.raises(PermissionError, match="E:events"):
        run_day(**SMALL)
