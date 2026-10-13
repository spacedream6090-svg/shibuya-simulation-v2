"""第 1 期 1-9 K17(回答 10-13b §3): 金の生ログの輪の容量を実測 4.07 行/体/日の 1.5 倍以上に広げて宣言し、溢れた件数を
manifest と計器に出す。試験は溢れ 0 件が条件・溢れたら記録して続ける(止めない)。

口の約束 1-9 の受入の試験 ``test_cp2_k17_capacity_and_overflow.py``:

- 係数 ``TRANSFERS_PER_AGENT_PER_DAY`` = 6.5 ≥ 4.07 × 1.5(=6.105)・容量 = max(16,384, ⌈6.5 × N⌉ × 保持日数)。
- 宣言(D-R2-6): ``transfer_log`` は 156 B/体/日・cap(容量 × 24 B)≥ 宣言投影=``declared_over_cap`` にならない。
  目印の列は別の宣言 ``transfer_log_event_ids``(12 B/行)。
- 溢れると記録して続ける: 小さな輪で意図的に溢れさせる → 計器・manifest の ``economy.raw_overflow``・日次の記録の
  ``economy.overflow`` に数が出て、ランは最後まで回り、final は溢れないランと同じ(輪は診断=軸 1 diag)。
- 既定の容量では溢れ 0 件(合成の世界の mock・(slow・data)世界資産の 19 構成 300 体と 5,000 体の既定 v3)。
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from shibuya.core.growth import check_growth
from shibuya.economy import census as CS
from shibuya.economy import ledger as LED
from shibuya.economy.accounts import AccountCode, Sector
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import (
    K17_MARGIN,
    MEASURED_TRANSFERS_PER_AGENT_DAY,
    MIN_RAW_CAPACITY,
    RAW_LINK_BYTES,
    RAW_ROW_BYTES,
    TRANSFERS_PER_AGENT_PER_DAY,
    Ledger,
    raw_capacity_for,
)
from shibuya.engine.ledger_api import EntityRef, LedgerBundle
from shibuya.engine.run import run_day
from shibuya.world.state import World

ROOT = Path(__file__).resolve().parents[3]


def test_the_coefficient_is_at_least_one_and_a_half_times_the_measurement():
    assert TRANSFERS_PER_AGENT_PER_DAY == 6.5
    assert MEASURED_TRANSFERS_PER_AGENT_DAY == 4.07 and K17_MARGIN == 1.5
    assert TRANSFERS_PER_AGENT_PER_DAY >= MEASURED_TRANSFERS_PER_AGENT_DAY * K17_MARGIN  # 6.105


@pytest.mark.parametrize("n, days, want", [
    (0, 1, MIN_RAW_CAPACITY), (2_000, 1, MIN_RAW_CAPACITY), (5_000, 1, 32_500), (5_001, 1, 32_507),
    (390_067, 1, 2_535_436), (390_067, 3, 3 * 2_535_436), (5_000, 2, 65_000)])
def test_capacity_formula(n, days, want):
    assert raw_capacity_for(n, days) == want == max(MIN_RAW_CAPACITY, math.ceil(6.5 * n) * days)


@pytest.mark.parametrize("n", [5_000, 5_001, 390_067])
def test_declarations_fit_their_caps(n):
    led = Ledger(n, 50)
    assert led.raw_capacity == raw_capacity_for(n) and led.raw_rows_per_agent_day == 6.5
    decls = led.growth_declarations()
    t = decls["transfer_log"]
    assert t.per_day_growth_coef == 6.5 * RAW_ROW_BYTES == 156.0
    assert t.cap == led.raw_capacity * RAW_ROW_BYTES >= t.declared_projected_bytes(30, n)
    link = decls["transfer_log_event_ids"]
    assert link.per_day_growth_coef == 6.5 * RAW_LINK_BYTES == 78.0
    assert link.cap == led.raw_capacity * RAW_LINK_BYTES >= link.declared_projected_bytes(30, n)
    rep = check_growth(decls, dict(led.growth_measured()), steps=1_440, minutes_per_step=1, n_entities=n)
    assert rep.declared_over_cap == () and rep.ok, rep.as_text()
    rec = led.economy_record()
    assert rec["raw_capacity"] == led.raw_capacity and rec["raw_overflow"] == 0
    assert rec["raw_rows_per_agent_day"] == 6.5 and rec["raw_row_bytes"] == 24 and rec["raw_link_bytes"] == 12


def test_overflow_is_counted_and_the_ledger_goes_on():
    """輪(8 行)を溢れさせる: 古い行を上書きして続け、溢れた行の数を数える。残高と流れの表は全部の行を含む。"""
    led = Ledger(4, 2, raw_capacity=8, retention_days=1)
    led.endow_households(np.full(4, 10_000), 0)  # 4 行
    for t in range(1, 11):  # 10 行
        st = led.transfer(EntityRef(Sector.HOUSEHOLD, t % 4), EntityRef(Sector.STORE, 0), 100,
                          AccountCode.CONSUMPTION, t)
        assert int(st) == 0
    assert led.meter.rows == 14 and led.meter.overflow == 6 == led.n_raw_dropped
    rows = led.raw_rows()
    assert rows.shape[0] == 8 and rows[:, 0].tolist() == list(range(3, 11))  # 新しい 8 行が残る
    assert int(led.flow[int(Sector.HOUSEHOLD), int(Sector.STORE), int(AccountCode.CONSUMPTION)]) == 1_000
    led.on_day_end(0)
    day = led.meter.last_day
    assert day["overflow"] == 6 and day["rows"] == 14 and day["flow_sum_ok"] is True
    assert led.economy_record()["raw_overflow"] == 6
    # 締めの後も続く: 保持窓(1 日)の中の前の日の 8 行で輪は満ちている=次の 1 行も上書きして数える
    led.transfer(EntityRef(Sector.HOUSEHOLD, 0), EntityRef(Sector.STORE, 1), 50, AccountCode.CONSUMPTION, 1_500)
    assert led.meter.overflow == 7 == led.n_raw_dropped and led.meter.rows == 15
    # 次の締めで保持窓の外の行を落とす(保持窓の落とし=溢れには数えない・落ちた行の数 n_raw_dropped にだけ入る)
    led.on_day_end(1)
    assert led.meter.overflow == 7 and led.n_raw_dropped == 14 and led.raw_rows().shape[0] == 1


def _bundle(world: World, n: int, cap: int | None = None) -> LedgerBundle:
    led = Ledger(n, world.n_poi, raw_capacity=cap)
    goods = GoodsLedger.from_pois(np.arange(world.n_poi) % 3, np.asarray(world.pois.stock),
                                  np.asarray(world.pois.price), n_agents=n)
    return LedgerBundle(money=led, goods=goods, census=lambda d: CS.daily_census(led, goods, day=d))


def _run(cap: int | None, days: int = 1):
    world = World.synthetic(n_cells=64, seed=2)
    bundle = _bundle(world, 300, cap)
    res = run_day(n_agents=300, seed=2, world=world, ticks=1_440, sim_days=days, checkpoint_every=720,
                  ledger=bundle)
    return res, bundle


@pytest.fixture(scope="module")
def small_and_default():
    return _run(64), _run(None)


def test_overflow_in_a_run_is_recorded_and_the_run_finishes(small_and_default):
    """小さな輪(64 行)で意図的に溢れさせる: manifest と日次の記録に溢れの数・ランは最後まで・final は同じ。"""
    (small, b_small), (dflt, b_dflt) = small_and_default
    m = small.run_manifest_fields()
    eco = m["economy"]
    assert eco["raw_capacity"] == 64 and eco["raw_overflow"] > 0
    assert eco["raw_overflow"] == b_small.money.meter.overflow == b_small.money.n_raw_dropped
    assert sum(d["economy"]["overflow"] for d in m["daily"]) == eco["raw_overflow"]
    assert m["finished"] is True
    # 輪は診断(軸 1 diag)=溢れても final・呼数・残高は溢れないランと同じ
    assert small.final_hash == dflt.final_hash and small.llm_calls == dflt.llm_calls
    assert small.money_end == dflt.money_end
    assert b_small.money.state_hash() == b_dflt.money.state_hash()


def test_default_capacity_does_not_overflow(small_and_default):
    """既定の容量(⌈6.5 × N⌉・下限 16,384)では溢れ 0 件。manifest の economy の欄の中身と日次の記録の和。"""
    _small, (res, b) = small_and_default
    m = res.run_manifest_fields()
    eco = m["economy"]
    assert eco["raw_capacity"] == raw_capacity_for(300) and eco["raw_overflow"] == 0
    assert eco["transfers_total"] == b.money.meter.rows > 0
    assert eco["transfers_total"] == sum(d["economy"]["rows"] for d in m["daily"])
    assert eco["transfers_amount"] == sum(d["economy"]["amount"] for d in m["daily"])
    assert all(d["economy"]["flow_sum_ok"] for d in m["daily"])
    assert eco["raw_overflow_policy"] == "上書きして数える(止めない)"


def test_manifest_economy_is_empty_without_a_ledger():
    res = run_day(n_agents=40, seed=1, n_cells=9, ticks=120, processes=False, renderer="stub")
    m = res.run_manifest_fields()
    assert m["economy"] == {} and all(d["economy"] == {} for d in m["daily"])


# ---------------------------------------------------------------- slow・data: 19 構成と 5,000 体
def _wave2():
    path = ROOT / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"
    spec = importlib.util.spec_from_file_location("wave2_bytecheck_cp2", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck_cp2"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


#: byte-check の 19 構成の名(wave2 の表=docs の道具から読む。読めないときは空=試験は集まらない)。
def _config_names() -> list[str]:
    try:
        return list(_wave2().configs())
    except Exception:  # noqa: BLE001 — 道具が無い checkout
        return []


@pytest.mark.slow
@pytest.mark.requires_data("world_v2:w17_schedule.parquet")
@pytest.mark.parametrize("name", _config_names())
def test_nineteen_configs_stay_under_the_coefficient(name):
    """byte-check の 19 構成(世界資産・**5,000 体**・1 日)ごとに、行/体/日 < 6.5(K17 の係数)と溢れ 0 件。

    検収 L2: 前は 300 体で回していた=行(約 3,300)が輪の下限 16,384 行に遠く届かず「溢れ 0」は必ず成り立った(空振り)。
    300 体では店の参入資本の行(POI ごとに 1 行=2,337 行・体の数に依らない)が行/体/日を押し上げる(下限が受け持つ)ので、
    係数の確かめは体の行が支配する 5,000 体で行う(1 構成 約 40〜60 秒)。
    """
    from shibuya import cli

    assert len(_config_names()) == 19
    kw = _wave2().configs()[name]
    res = cli.run(n_agents=5_000, seed=1, world_dir="data/world/v2", **kw)
    eco = res.run_manifest_fields()["economy"]
    assert eco["raw_capacity"] == 32_500 and eco["raw_overflow"] == 0, (name, eco)
    assert 0 < eco["transfers_total"] / 5_000 < LED.TRANSFERS_PER_AGENT_PER_DAY, (name, eco)
    assert eco["transfers_total"] <= eco["raw_capacity"]


@pytest.mark.slow
@pytest.mark.requires_data("world_v2:w17_schedule.parquet")
def test_5k_default_day_does_not_overflow():
    """5,000 体の既定 v3 の 1 日: 実測の行/体/日は 6.5 未満=溢れ 0 件(HEAD の 3.0 では 3,978 行が落ちていた)。"""
    from shibuya import cli

    res = cli.run(n_agents=5_000, seed=1, world_dir="data/world/v2", vocab_version="v3")
    eco = res.run_manifest_fields()["economy"]
    assert eco["raw_capacity"] == 32_500 and eco["raw_overflow"] == 0
    assert eco["transfers_total"] / 5_000 < LED.TRANSFERS_PER_AGENT_PER_DAY
