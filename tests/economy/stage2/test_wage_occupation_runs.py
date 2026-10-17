"""賃金を職業ごとの実データから(小さな版上げ・2026-10-17): 世界資産の 2 日のラン(開始日 2026-08-24=1 日目の締めが給料日)。

- 5,000 体・腕 occupation(既定)と w17(旧値の再現): 毎日 保存則の残差 0・0 日目(給料日の前)は帳簿の流れが両腕で同じ・
  1 日目は賃金と原資(外界 → 雇用主・店の消費支出)の科目だけが動く(給料日は日の締め=ほかの科目は同じ)・既定の賃金は
  w17 の 4 倍を超える(1/4 の宣言を解く)・雇用の行のある体の職種 × 性の月の賃金の中央値が R-107 第18表の中位数の
  0.75〜1.15 倍(記録 wage_occ §3)。
- 1,000 体・両腕: 1 日目の昼(2,190)で止めて再開=通しのランと同じ(final・帳簿の残高・保存則の検算)。

``slow``・data が要る。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.economy import wages as WG
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.engine import economy_stage2 as ES2

pytestmark = [pytest.mark.slow,
              pytest.mark.requires_data("world_v2:w17_schedule.parquet", "osm:poi_tags_overpass_20260928.json",
                                        "calendar", "persona_pool")]

KW = dict(seed=1, world_dir="data/world/v2", sim_days=2, vocab_version="v3", start_sim_datetime="2026-08-24")


def _arm(monkeypatch, wage: str) -> None:
    monkeypatch.setattr(ES2, "_ARM", ES2.ARM_ON)
    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)
    monkeypatch.setattr(ES2, "_ATM_OVERRIDE", None)
    monkeypatch.setattr(ES2, "_WAGE", wage)


@pytest.fixture(scope="module")
def two_arms():
    if WG.load_wage_tables() is None:
        pytest.skip("requires_data: 賃金の表の写し(research_cache/pop41b/derived)が無い")
    from shibuya import cli

    mp = pytest.MonkeyPatch()
    out = {}
    try:
        for wage in ("occupation", "w17"):
            _arm(mp, wage)
            out[wage] = cli.run(n_agents=5_000, **KW)
    finally:
        mp.undo()
    return out


def test_conservation_and_only_the_wage_accounts_move(two_arms):
    occ, w17 = two_arms["occupation"], two_arms["w17"]
    for res in (occ, w17):
        for d in res.run_manifest_fields()["daily"]:
            c = d["economy"]["conservation"]
            assert c["ok"] is True and c["residual"] == 0, c
        assert res.conserved
    fo, fw = occ.ledger.money.flow_daily, w17.ledger.money.flow_daily
    assert np.array_equal(np.asarray(fo[0]), np.asarray(fw[0]))  # 給料日の前の日は同じ
    d1o, d1w = np.asarray(fo[1]).copy(), np.asarray(fw[1]).copy()
    wage = int(AccountCode.WAGE)
    cons = int(AccountCode.CONSUMPTION)
    row = int(Sector.ROW)
    dep = int(AccountCode.DEPOSIT_NET)
    for f, res in ((d1o, occ), (d1w, w17)):
        # 賃金は世帯の口座へ=預金純増(世帯 → 銀行)の行も同じ額(1 日目の預け入れは賃金だけ)
        assert int(f[int(Sector.HOUSEHOLD), int(Sector.BANK), dep]) == int(f[:, :, wage].sum()) > 0
        f[int(Sector.HOUSEHOLD), int(Sector.BANK), dep] = 0
    for f in (d1o, d1w):
        f[:, :, wage] = 0
        f[row, int(Sector.EMPLOYER), cons] = 0  # 原資(外界 → 雇用主)
        f[row, int(Sector.STORE), cons] = 0  # 原資(外界 → 店=担当従業者の賃金・店の外界の売上は 0)
    assert np.array_equal(d1o, d1w)  # 賃金と原資のほかの科目は同じ(給料日は日の締め)
    so = occ.ledger.money.stage2.s2_meter["run"]["wages"]
    sw = w17.ledger.money.stage2.s2_meter["run"]["wages"]
    # w17 は W17 の勤務の時間が 0 の体(no_hours)に払わない=occupation は雇用の行のある体の全部に払う
    assert so["paid"] == sw["paid"] + sw["no_hours"] > 0 and so["no_hours"] == 0
    assert so["funding"] == so["amount"] and sw["funding"] == sw["amount"]
    assert so["amount"] > 4 * sw["amount"]  # 1/4 の宣言を解く


def test_median_matches_r107(two_arms):
    occ = two_arms["occupation"]
    st2 = occ.ledger.money.stage2
    agents, _sec, _idx = st2.plan.employment(1)
    winp = st2.plan.wage_inputs
    rows = WG.median_check(WG.load_wage_tables(), st2.monthly_wage, st2.wage_basis, winp.occ_code, winp.occ_vocab,
                           winp.emp_code, winp.emp_vocab, winp.sex, who=np.asarray(agents), min_n=30)
    assert len(rows) >= 6
    for r in rows:
        assert 0.75 <= r["ratio"] <= 1.15, r
    m = st2.s2_meter["rules"]["wage_model"]
    assert m["paid_by_basis"]["occupation"] > 0.95 * m["employed"]
    man = occ.run_manifest_fields()["economy"]["stage2"]
    assert man["plan"]["wage_path"] == "occupation" and man["plan"]["wage_model"] == "occupation"
    assert man["rules"]["wage_build"]["inputs"]["source"] == "persona_pool"
    assert man["hours_source"] == "none(wage=occupation)"


@pytest.mark.parametrize("wage", ["occupation", "w17"])
def test_resume_equals_straight(tmp_path, monkeypatch, wage):
    from shibuya import cli

    if WG.load_wage_tables() is None:
        pytest.skip("requires_data: 賃金の表の写しが無い")
    _arm(monkeypatch, wage)
    kw = dict(n_agents=1_000, checkpoint_every=360, **KW)
    straight = cli.run(**kw)
    a = cli.run(state_out=tmp_path / "s", stop_at_tick=2_190, **kw)
    b = cli.run(resume_from=tmp_path / "s" / a.resume["state_files"][-1]["file"], **kw)
    assert b.final_hash == straight.final_hash
    for line in (BalanceLine.CASH, BalanceLine.DEPOSIT):
        for s in Sector:
            assert np.array_equal(np.asarray(b.ledger.money.balance(line, s)),
                                  np.asarray(straight.ledger.money.balance(line, s))), (line, s)
    s_days = {int(d["day"]): d["economy"] for d in straight.daily}
    for d in b.daily:
        assert d["economy"]["conservation"] == s_days[int(d["day"])]["conservation"]
    assert straight.ledger.money.stage2.s2_meter["run"]["wages"]["paid"] > 0
    # 腕の違う再開は止まる
    other = "w17" if wage == "occupation" else "occupation"
    monkeypatch.setattr(ES2, "_WAGE", other)
    with pytest.raises(ValueError, match="賃金の腕"):
        cli.run(resume_from=tmp_path / "s" / a.resume["state_files"][-1]["file"], **kw)
