"""第 1 期 1-9: 金の移動の目印の列と計器(状態台帳の行 ``A``=CP1 の A 湧かないもの)を書く系は ``writes.paths`` に ``A:ledger.*`` を宣言し、
原因を渡す移動(運賃=過程 rail)を書く phase_c は ``E:events.*`` も宣言する。宣言の外の書きは落ちる(1-0 の段 B・段 C と
1-3 の実行時の検査)。

- 宣言: ``A:ledger.*`` の系=world・phase_c・day_close・close_final(行 A の道筋に当たる)・``E:events.*`` に phase_c。
- 段 B(試験のときの全欄の差): 宣言どおりなら宣言の外 0。phase_c の宣言から ``A:ledger.*`` を外すと、差の測りが ``A:`` の
  道筋の変化を phase_c に出す(負の対照)。
- 実行時(data・世界資産 200 体): phase_c の宣言から ``E:events.*`` を外すと、運賃の出来事を書いた所で ``PermissionError``。
"""

from __future__ import annotations

import fnmatch

import numpy as np
import pytest

from shibuya.core import write_permit as WP
from shibuya.economy import census as CS
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import Ledger
from shibuya.engine import state_ledger as SL
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.run import run_day
from shibuya.engine.systems import conductor as CD
from shibuya.engine.systems import overrides as OV
from shibuya.engine.systems import probe as PR
from shibuya.engine.systems.table import SPECS, SYSTEMS
from shibuya.world.state import World

PAT = "A:ledger.*"
TICKS = frozenset(range(0, 720, 5)) | frozenset({719})


@pytest.fixture(autouse=True)
def _guard_on():
    prev = WP.enabled()
    WP.set_enabled(True)
    yield
    WP.set_enabled(prev)


def test_declaring_systems():
    assert [s.name for s in SYSTEMS if PAT in s.writes.paths] == ["world", "phase_c", "day_close", "close_final"]
    assert "E:events.*" in SPECS["phase_c"].writes.paths
    items = [f"{r.key}:{it}" for r in SL.external_rows() for it in r.items]
    c_items = [k for k in items if fnmatch.fnmatchcase(k, PAT)]
    assert c_items == ["A:ledger.money._raw_event_t_ns", "A:ledger.money._raw_event_seq", "A:ledger.money.meter",
                       "A:ledger.goods._dl_event_t_ns", "A:ledger.goods._dl_event_seq"]
    row = SL.row("A")
    assert (row.behavior, row.restore) == (SL.DIAG, SL.DISCARDABLE)
    assert not set(row.items) & {p for _k, p in SL.full_items()}  # どちらのハッシュにも状態のファイルにも入らない


def _probe_run(drop: str | None = None):
    world = World.synthetic(n_cells=64, seed=2)
    led = Ledger(120, world.n_poi)
    goods = GoodsLedger.from_pois(np.arange(world.n_poi) % 3, np.asarray(world.pois.stock),
                                  np.asarray(world.pois.price), n_agents=120)
    bundle = LedgerBundle(money=led, goods=goods, census=lambda d: CS.daily_census(led, goods, day=d))
    pr = PR.Probe(check=None, ticks=TICKS)
    PR.ACTIVE = pr
    try:
        if drop is None:
            pr.check = CD.declared_check(SPECS)
            run_day(n_agents=120, seed=2, world=world, ticks=720, checkpoint_every=360, ledger=bundle)
        else:
            with OV.drop_path("phase_c", drop):
                pr.check = CD.declared_check(SPECS)
                run_day(n_agents=120, seed=2, world=world, ticks=720, checkpoint_every=360, ledger=bundle)
    finally:
        PR.ACTIVE = None
    return pr, led


def test_declared_writes_cover_the_money_meter_changes():
    pr, led = _probe_run()
    assert pr.n_snap > 0 and not pr.violations, pr.violations[:10]
    writers = {s for _t, s, _d, keys in pr.entries if any(k.startswith("A:") for k in keys)}
    assert "phase_c" in writers and writers <= {"world", "phase_c", "day_close", "close_final", CD.TICK_HEAD, "END"}
    assert led.meter.rows > 0


def test_undeclared_money_meter_write_shows_in_stage_b():
    WP.set_enabled(False)  # 実行時の検査を外して段 B だけで見る(行 A は SoA でない=段 B が受け持つ)
    pr, _led = _probe_run(drop=PAT)
    bad = [(t, s, k) for t, s, k in pr.violations if k.startswith("A:")]
    assert bad and all(s == "phase_c" for _t, s, _k in bad), pr.violations[:5]


@pytest.mark.requires_data("world_v2:w17_schedule.parquet")
def test_phase_c_without_the_events_declaration_fails_at_the_first_fare():
    from shibuya import cli

    with OV.drop_path("phase_c", "E:events.*"):
        with pytest.raises(PermissionError, match="系 phase_c は出来事の記録"):
            cli.run(n_agents=200, seed=1, world_dir="data/world/v2", vocab_version="v3")
