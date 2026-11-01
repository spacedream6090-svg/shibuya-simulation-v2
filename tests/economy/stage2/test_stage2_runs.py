"""第 2 期 2-1 経済の段階 2: 合成の世界の 2 日のラン(暦の口で開始日を 2026-08-24(月)=給料日 25 日をまたぐ)。

- 腕 on(部品は全部): 賃金が払われる(25 日の締め)・引き出しが起きる・カード払いが預金から引かれる・税が政府に入る・
  保存則の残差 0(毎日)・来街者の口座がある・``RunResult.conserved``(式に段階 2 の項を足した)が成り立つ。
- 部品を 1 つずつ止めると当該の流れが 0 になる(5 部品)。
- 負の対照: 営業時間の外の ATM では引き出せない。
- 腕 off: 段階 2 の欄が立たない・台帳に段階 2 が挿されない・生ログの方法の列は 0・保存則の検算は通る。
- 腕 port(候補の口)と一緒: 「お金を下ろす」の候補と支払いの注が出る・mock の行為は腕 legacy と同じ(final が同じ)。

合成の世界には OSM の ATM の点が乗らないので、ATM の表は試験の切替口(``set_atm_table``)で 8 セルに 1 つ 24 時間の ATM を置く。
財布が小さいときにカードと引き出しが起きるよう、世帯の初期の財布を 1/50 にした台帳で回す(試験の道具・入れ方は transfer)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.economy import census as CS
from shibuya.economy import stage2 as S2
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import Ledger
from shibuya.engine import economy_stage2 as ES2
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.run import run_day
from shibuya.world.state import World

H, S, E, B, G, W = (int(s) for s in Sector)
N = 300
START = "2026-08-24"


class _SmallWallets(Ledger):
    """初期の財布を 1/50 にする台帳(試験の道具)。入れ方は今のまま transfer(外界 → 世帯)。"""

    def endow_households(self, amounts, tick: int = 0, *, cause=None):  # noqa: ANN001
        a = np.maximum(np.asarray(amounts, dtype=np.int64) // 50, 1)
        return super().endow_households(a, tick, cause=cause)


def _atm_everywhere(n_cells: int, hours: str = "24/7", every: int = 8) -> ES2.AtmTable:
    """``every`` セルに 1 つ ATM を置く(全部のセルに置くと最初の判断で皆が下ろし、カード払いが起きない)。"""
    h = ES2.parse_opening_hours(hours)
    if h is None:
        h = np.full((7, 2, 2), -1, dtype=np.int16)
    cells = np.arange(0, n_cells, every, dtype=np.int64)
    return ES2.AtmTable(cell=cells, kind=np.zeros(cells.size, np.int8), hours=np.stack([h] * cells.size),
                        hours_from=np.zeros(cells.size, np.int8), n_cells=n_cells)


@pytest.fixture
def arm(monkeypatch):
    """腕と部品と ATM の表を試験の中だけ切り替える(終わったら元に戻す)。"""
    monkeypatch.setattr(ES2, "_ARM", ES2.ARM_OFF)
    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)
    monkeypatch.setattr(ES2, "_ATM_OVERRIDE", None)

    def set_(name: str, parts=ES2.PARTS, atm_hours: str | None = "24/7") -> None:
        ES2.set_arm(name)
        ES2.set_parts(parts)
        world = World.synthetic(n_cells=64, seed=2)
        ES2.set_atm_table(None if atm_hours is None else _atm_everywhere(world.n_cells, atm_hours))

    return set_


def _run(sim_days: int = 2, small: bool = True, **kw):
    world = World.synthetic(n_cells=64, seed=2)
    led = (_SmallWallets if small else Ledger)(N, world.n_poi)
    goods = GoodsLedger.from_pois(np.arange(world.n_poi) % 3, np.asarray(world.pois.stock),
                                  np.asarray(world.pois.price), n_agents=N)
    bundle = LedgerBundle(money=led, goods=goods, census=lambda d: CS.daily_census(led, goods, day=d))
    res = run_day(n_agents=N, seed=2, world=world, ticks=1_440, sim_days=sim_days, checkpoint_every=720,
                  ledger=bundle, start_sim_datetime=START, **kw)
    return res, led


def _flow(led: Ledger, code: AccountCode, a: int | None = None, b: int | None = None) -> int:
    f = sum(np.asarray(x) for x in led.flow_daily)
    sl = f[:, :, int(code)]
    if a is not None:
        sl = sl[a:a + 1]
    if b is not None:
        sl = sl[:, b:b + 1]
    return int(sl.sum())


@pytest.fixture
def on_run(arm):
    arm("on")
    return _run()


def test_all_parts_move_money_and_keep_the_books(on_run):
    res, led = on_run
    m = res.run_manifest_fields()
    s2 = m["economy"]["stage2"]
    assert s2["arm"] == "on" and s2["parts"] == list(ES2.PARTS)
    run = led.stage2.s2_meter["run"]
    # 賃金(25 日=1 日目の締め・店の担当従業者=店 → 世帯の口座・原資は外界の売上)
    assert [d["economy"]["stage2"]["payday"] for d in m["daily"]] == [False, True]
    assert run["wages"]["paid"] > 0 and _flow(led, AccountCode.WAGE) == run["wages"]["amount"] > 0
    assert _flow(led, AccountCode.CONSUMPTION, W, None) == run["wages"]["funding"] == run["wages"]["amount"]
    # 引き出し・カード・税・来街者の口座
    assert run["withdraw"]["count"] > 0 and run["withdraw"]["amount"] > 0
    assert run["payment"]["account_rows"] > 0 and run["payment"]["account_amount"] > 0
    # 〔第 4 期 4-2・Q1〕レジの税は店の預かり金に積む(期限 2027-03-31 の前=政府へは移らない)・政府に入るのは給料日の天引き
    assert run["tax"]["amount"] > 0 and _flow(led, AccountCode.TAX, S, G) == 0
    assert led.stage2.tax_deposit.held_total() == run["tax"]["amount"]
    assert int(np.asarray(led.balance(BalanceLine.CASH, G))[0]) == run["wages"]["employee_amount"] > 0
    assert run["endow"]["visitor_rows"] > 0
    kinds = led.stage2.kinds
    dep = np.asarray(led.balance(BalanceLine.DEPOSIT, H))
    assert (dep[np.isin(kinds, S2.VISITOR_KINDS)] >= 0).all() and run["endow"]["visitor_amount"] > 0
    # 保存則: 毎日 残差 0・登録の無い流れ 0・既存の四重記入の検算も通る
    for d in m["daily"]:
        c = d["economy"]["conservation"]
        assert c["ok"] is True and c["residual"] == 0 and c["unregistered"] == 0, c
        assert d["economy"]["flow_sum_ok"] is True and d["census_row"]["flow_ok"] is True
    # 〔第 2 期 2-4 V4〕店の売上の写し pois.revenue は税抜き=保存則の左辺から店から政府へ出たレジの税を引く
    assert res.conserved and led.stage2.cash_terms() > 0 and led.stage2.register_tax() == run["tax"]["amount"] > 0
    assert res.money_stage2_in == led.stage2.cash_terms() - led.stage2.register_tax()
    assert res.revenue_end == _flow(led, AccountCode.CONSUMPTION, H, S) - run["tax"]["amount"]  # 世帯 → 店の売上 − 税
    # 見張り: 財布と預金の分位(p10/p50/p90)が毎日・manifest に faucet/sink の表
    for d in m["daily"]:
        assert set(d["economy"]["stage2"]["wallet"]) == {"p10", "p50", "p90"}
    names = {r["name"] for r in s2["faucet_sink_registry"]}
    assert {"初期の預金", "賃金の原資(雇用主の外界の売上)", "消費税"} <= names
    assert all(r["kind"] != "UNREGISTERED" for r in s2["faucet_sink_by_cell"])
    assert s2["rules"]["minimum_wage"]["yen_per_hour"] == 1_226  # 2026-08-25 は表の 2025-10-03 の版(第337 で足した)


@pytest.mark.parametrize("off", ES2.PARTS)
def test_turning_one_part_off_zeroes_its_flow(arm, off):
    arm("on", parts=tuple(p for p in ES2.PARTS if p != off))
    res, led = _run()
    run = led.stage2.s2_meter["run"]
    for d in res.run_manifest_fields()["daily"]:
        assert d["economy"]["conservation"]["ok"] is True
    if off == "wages":
        assert _flow(led, AccountCode.WAGE) == 0 and run["wages"]["paid"] == 0
    if off == "withdraw":
        assert run["withdraw"]["count"] == 0 and run["withdraw"]["amount"] == 0
    if off == "payment":
        assert run["payment"]["account_rows"] == 0 and run["payment"]["fare_ic_rows"] == 0
        assert run["payment"]["cash_rows"] > 0
    if off == "tax":  # 〔第 4 期 4-2〕税の科目に残るのは給料日の天引き(世帯 → 政府)だけ
        assert _flow(led, AccountCode.TAX, S, G) == 0 and run["tax"]["amount"] == 0
        assert _flow(led, AccountCode.TAX) == run["wages"]["employee_amount"] and led.stage2.tax_deposit is None
    if off == "visitors":
        dep = np.asarray(led.balance(BalanceLine.DEPOSIT, H))
        vis = np.isin(led.stage2.kinds, S2.VISITOR_KINDS)
        assert run["endow"]["visitor_rows"] == 0 and run["endow"]["visitor_amount"] == 0
        assert vis.any() and int(dep[vis].max()) == 0  # 来街者の口座は空のまま(担当従業者は来街者でない=賃金も入らない)
    others = [p for p in ES2.PARTS if p != off]
    if "tax" in others:
        assert run["tax"]["amount"] > 0
    if "wages" in others:
        assert run["wages"]["paid"] > 0


def test_negative_a_closed_atm_gives_no_withdrawal(arm):
    """負の対照: どの ATM も営業時間の外(全部の曜日 off)なら、財布が小さくても引き出せない。"""
    arm("on", atm_hours="Mo-Su off")
    _res, led = _run(sim_days=1)
    w = led.stage2.s2_meter["run"]["withdraw"]
    assert w["asked"] == 0 and w["count"] == 0
    arm("on", atm_hours="Mo-Fr 09:00-09:01")  # 1 分だけ開く=その刻みに判断した体だけが下ろせる
    _res, led2 = _run(sim_days=1)
    assert led2.stage2.s2_meter["run"]["withdraw"]["asked"] < 300


def test_arm_off_changes_nothing_on_the_ledger(arm):
    arm("off")
    res, led = _run(sim_days=2)
    m = res.run_manifest_fields()
    assert led.stage2 is None and led.credit is None and led._stage2_pairs is False
    assert "stage2" not in m["economy"] and all("stage2" not in d["economy"] for d in m["daily"])
    assert (led.raw_methods() == 0).all()
    assert all(d["economy"]["conservation"]["ok"] for d in m["daily"])
    assert res.money_stage2_in == 0 and res.conserved
    assert m["decision_port"]["stage2"] is None


def test_off_parts_spec_without_the_arm_is_ignored(arm):
    arm("off", parts=("wages",))
    res, led = _run(sim_days=1)
    assert led.stage2 is None and "stage2" not in res.run_manifest_fields()["economy"]


def test_port_arm_shows_the_candidates_and_keeps_the_mock_actions(arm, monkeypatch):
    from shibuya.engine.decision import layer as DL

    arm("on")
    base, _ = _run(sim_days=1)
    monkeypatch.setattr(DL, "_ARM", DL.ARM_PORT)
    res, _led = _run(sim_days=1)
    dp = res.run_manifest_fields()["decision_port"]
    assert dp["arm"] == "port" and dp["mismatch"] == 0
    assert dp["stage2"]["withdraw_presented"] > 0 and dp["stage2"]["payment_noted"] > 0
    assert dp["stage2"]["withdraw_chosen"] == 0  # mock は行為の語彙の候補だけを選ぶ
    assert res.final_hash == base.final_hash and res.llm_calls == base.llm_calls


def test_atms_live_in_the_fixtures(arm):
    from shibuya.engine.systems import boxes as BX

    arm("on")
    seen = {}
    orig = BX.Fixtures.__init__

    def spy(self, *a, **k):  # noqa: ANN001
        orig(self, *a, **k)
        seen["atms"] = self.atms

    import unittest.mock as um

    with um.patch.object(BX.Fixtures, "__init__", spy):
        _res, led = _run(sim_days=1)
    assert seen["atms"] is led.stage2.atms and seen["atms"].n == 8
