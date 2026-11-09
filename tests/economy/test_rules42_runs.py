"""第 4 期 4-2 のランの形(合成の世界の 2 日=給料日 2026-08-25 をまたぐ)。

- 既定: レジの税は店の預かり金に積まれる(期限は 2027-03-31=2 日のランでは政府へ移らない)・給料日に世帯の口座 → 政府の
  本人の分が動く(合成の世界は母集団が無い=加入の判定の材料なし=源泉と住民税だけ)・保存則と預かり金の検算は毎日 残差 0・
  ``RunResult.conserved`` が成り立つ・manifest に腕と預かり金。
- 〔第346〕4-2 の前の値の切替口 ``SHIBUYA_RULES_42=off`` は消した: 環境変数を与えると読み込みで止まる・見出しに
  ``rules_42=on`` の無い状態のファイルからは再開できない(旧値の再現は安定版のタグ)。4-2 の前の値の部品の口(``law`` の無い
  ``Stage2Plan``)は ``test_rules42_ledger.py`` が見る。
- 再開(日の境目と給料日の昼)=通しと同じ(預かり金の状態は腕の行 TXD で戻る・slow・data)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.economy import census as CS
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import Ledger
from shibuya.engine import economy_rules as ER
from shibuya.engine import economy_stage2 as ES2
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.run import run_day
from shibuya.world.state import World

H, S, E, B, G, W = (int(s) for s in Sector)
N = 300


@pytest.fixture
def law(monkeypatch):
    monkeypatch.setattr(ES2, "_ARM", ES2.ARM_ON)
    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)
    monkeypatch.setattr(ES2, "_ATM_OVERRIDE", None)


def _run(sim_days: int = 2):
    world = World.synthetic(n_cells=64, seed=2)
    led = Ledger(N, world.n_poi)
    goods = GoodsLedger.from_pois(np.arange(world.n_poi) % 3, np.asarray(world.pois.stock),
                                  np.asarray(world.pois.price), n_agents=N)
    bundle = LedgerBundle(money=led, goods=goods, census=lambda d: CS.daily_census(led, goods, day=d))
    res = run_day(n_agents=N, seed=2, world=world, ticks=1_440, sim_days=sim_days, checkpoint_every=720,
                  ledger=bundle, start_sim_datetime="2026-08-24")
    return res, led


def _flow(led: Ledger, code: AccountCode, a: int, b: int) -> int:
    f = sum(np.asarray(x) for x in led.flow_daily)
    return int(f[a, b, int(code)])


def test_on_keeps_the_register_tax_in_the_deposit_and_deducts_on_payday(law):
    res, led = _run()
    s2 = led.stage2
    run = s2.s2_meter["run"]
    m = res.run_manifest_fields()
    assert s2.law is not None and s2.tax_deposit is not None
    assert run["tax"]["amount"] > 0 and s2.tax_deposit.held_total() == run["tax"]["amount"]
    assert _flow(led, AccountCode.TAX, S, G) == 0  # 期限(2027-03-31)の前=政府は消費税を受け取らない
    assert run["wages"]["paid"] > 0 and run["wages"]["employee_amount"] > 0
    assert _flow(led, AccountCode.TAX, H, G) == run["wages"]["employee_amount"]
    assert run["wages"]["employee_income_tax"] + run["wages"]["employee_resident_tax"] == run["wages"]["employee_amount"]
    assert run["wages"]["no_basis"] == run["wages"]["paid"] and run["wages"]["employer_share_amount"] == 0
    assert int(np.asarray(led.balance(BalanceLine.CASH, G))[0]) == run["wages"]["employee_amount"]
    for d in m["daily"]:
        c = d["economy"]["conservation"]
        assert c["ok"] is True and c["residual"] == 0 and c["unregistered"] == 0
        assert d["economy"]["stage2"]["tax"]["deposit_check"]["residual"] == 0
    assert res.conserved
    st = m["economy"]["stage2"]
    assert st["plan"]["rules_42"] == "on" and st["plan"]["law"]["source"] == "no_population"
    # 〔検収 H1〕抽出で動く数は観測の rules.payroll_inputs(設定の節 plan.law には出どころ・語・定数だけ)
    assert set(st["plan"]["law"]) == {"source", "role_vocab", "full_time_weekly_hours", "non_employee_roles"}
    assert st["rules"]["payroll_inputs"]["bodies"] == N and res.money_stage2_deposit_ok is True
    assert st["tax"]["deposit"]["held"] == run["tax"]["amount"]
    assert st["tax"]["deposit"]["periods"]["2026"]["due"] == "2027-03-31"
    assert st["rules"]["invoice_rounding"]["method"] == "切り捨て"


def test_removed_rules_42_switch_env_stops():
    """〔第346〕消した切替口: 環境変数 SHIBUYA_RULES_42 を与えると読み込みで止まる・腕を選ぶ口は無い。"""
    import os
    import subprocess
    import sys

    assert ER.ENV_42_REMOVED == "SHIBUYA_RULES_42"
    for name in ("arm", "set_arm", "ARMS", "DEFAULT_ARM", "_ARM"):
        assert not hasattr(ER, name), name
    for value in ("off", "on"):
        env = {**os.environ, "SHIBUYA_RULES_42": value, "PYTHONIOENCODING": "utf-8"}
        r = subprocess.run([sys.executable, "-c", "import shibuya.engine.economy_rules"], env=env, capture_output=True,
                           text=True, encoding="utf-8")
        assert r.returncode != 0 and "消した切替口" in r.stderr and ER.REMOVED_SWITCH_TAG in r.stderr


@pytest.mark.slow
@pytest.mark.requires_data("world_v2:w17_schedule.parquet", "osm:poi_tags_overpass_20260928.json", "calendar")
@pytest.mark.parametrize("stop", [1_440, 2_190])
def test_resume_equals_straight_with_the_deposit(tmp_path, law, stop):
    from shibuya import cli

    kw = dict(n_agents=300, seed=1, world_dir="data/world/v2", sim_days=2, vocab_version="v3",
              start_sim_datetime="2026-08-24", checkpoint_every=360)
    straight = cli.run(**kw)
    a = cli.run(state_out=tmp_path / "s", stop_at_tick=stop, **kw)
    b = cli.run(resume_from=tmp_path / "s" / a.resume["state_files"][-1]["file"], **kw)
    assert b.final_hash == straight.final_hash
    d1, d2 = b.ledger.money.stage2.tax_deposit, straight.ledger.money.stage2.tax_deposit
    assert d1.held_total() == d2.held_total() > 0 and d1.totals == d2.totals
    for line in (BalanceLine.CASH, BalanceLine.DEPOSIT):
        for s in Sector:
            assert np.array_equal(np.asarray(b.ledger.money.balance(line, s)),
                                  np.asarray(straight.ledger.money.balance(line, s))), (line, s)


def test_resume_refuses_a_header_without_rules_42(law):
    """見出しの ``rules_42`` が無い状態のファイル(4-2 の前のラン)からは再開できない(〔第346〕切替口は消した・天引きは状態を
    持たない=見出しで見る)。"""
    import types

    plan = types.SimpleNamespace(parts=ES2.PARTS, wage_model=ES2.wage_arm(), law=object())
    head = ES2.header_fields(plan)
    assert head["rules_42"] == "on"
    ES2.check_resume(head)
    off = {k: v for k, v in head.items() if k != "rules_42"}
    with pytest.raises(ValueError, match="規則の表の中身の腕.*消した.*stable-v2-before-switch-removal-346"):
        ES2.check_resume(off)
    assert ES2.header_fields(types.SimpleNamespace(parts=ES2.PARTS, wage_model=ES2.wage_arm(), law=None)).get(
        "rules_42") is None  # law の無い部品の口は見出しに書かない


def test_conserved_fails_when_the_deposit_check_breaks(law):
    """〔検収 L4〕預かり金の検算(積んだ − 移した − 残高=0)が ``RunResult.conserved`` に入る(負の対照)。"""
    import dataclasses

    res, led = _run(sim_days=1)
    assert res.conserved and led.stage2.tax_deposit_ok()
    led.stage2.tax_deposit.totals["collected"] += 1
    assert led.stage2.tax_deposit_ok() is False
    assert dataclasses.replace(res, money_stage2_deposit_ok=False).conserved is False
