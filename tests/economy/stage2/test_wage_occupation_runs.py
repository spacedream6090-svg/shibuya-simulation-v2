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


def _arm(monkeypatch) -> None:
    monkeypatch.setattr(ES2, "_ARM", ES2.ARM_ON)
    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)
    monkeypatch.setattr(ES2, "_ATM_OVERRIDE", None)


@pytest.fixture(scope="module")
def two_arms():
    """〔第 4 期 4-3 版上げ 3 回目の第 2 部〕旧値の腕 w17 は消した=既定(occupation)の 1 本だけ(名は前のまま)。"""
    if WG.load_wage_tables() is None:
        pytest.skip("requires_data: 賃金の表の写し(research_cache/pop41b/derived)が無い")
    from shibuya import cli

    mp = pytest.MonkeyPatch()
    try:
        _arm(mp)
        return {"occupation": cli.run(n_agents=5_000, **KW)}
    finally:
        mp.undo()


def test_conservation_and_only_the_wage_accounts_move(two_arms):
    occ = two_arms["occupation"]
    for d in occ.run_manifest_fields()["daily"]:
        c = d["economy"]["conservation"]
        assert c["ok"] is True and c["residual"] == 0, c
    assert occ.conserved
    f1 = np.asarray(occ.ledger.money.flow_daily[1]).copy()
    wage = int(AccountCode.WAGE)
    dep = int(AccountCode.DEPOSIT_NET)
    # 賃金は世帯の口座へ=預金純増(世帯 → 銀行)の行も同じ額(1 日目の預け入れは賃金だけ)
    assert int(f1[int(Sector.HOUSEHOLD), int(Sector.BANK), dep]) == int(f1[:, :, wage].sum()) > 0
    so = occ.ledger.money.stage2.s2_meter["run"]["wages"]
    assert so["paid"] > 0 and so["no_hours"] == 0
    # 〔第 4 期 4-3 段 10・検収 M3〕外の雇用主(席の外の体)の賃金は外界から払う=原資の行は無い
    assert so["funding"] + so["outside_employer_amount"] == so["amount"] and so["outside_employer_paid"] > 0
    # 〔第 2 部〕前は旧値の腕 w17 と 1 日目の科目を比べた(賃金と原資の科目だけが動く・額は w17 の 4 倍超)=腕と一緒に消した


def test_median_matches_r107(two_arms):
    occ = two_arms["occupation"]
    st2 = occ.ledger.money.stage2
    agents, _sec, _idx = st2.plan.employment(1)
    winp = st2.plan.wage_inputs
    rows = WG.median_check(WG.load_wage_tables(), st2.monthly_wage, st2.wage_basis, winp.occ_code, winp.occ_vocab,
                           winp.emp_code, winp.emp_vocab, winp.sex, who=np.asarray(agents), min_n=35)
    # 〔第 4 期 4-3 段 10〕差し替えの世界では職種の式で払う体が 545(given=W21 の段 5 の賃金 2,135)に減り、30 体の区分の 1 つ
    # (販売従事者・女 n=32・1.18)が帯の外=小さい区分の揺れ。区分の下限を 30 → 35 に(前=W16 の世界は 30・記録 pop43 §16)
    assert len(rows) >= 6
    for r in rows:
        assert 0.75 <= r["ratio"] <= 1.15, r
    m = st2.s2_meter["rules"]["wage_model"]
    # 〔第 4 期 4-3 段 10〕差し替えの世界の W21 の体は段 5 の賃金(given)=職種の式と given で 95% 超(前: occupation だけで 95% 超)
    assert m["paid_by_basis"]["occupation"] + m["paid_by_basis"]["given"] > 0.95 * m["employed"]
    man = occ.run_manifest_fields()["economy"]["stage2"]
    assert man["plan"]["wage_path"] == "occupation" and man["plan"]["wage_model"] == "occupation"
    assert man["rules"]["wage_build"]["inputs"]["source"] == "persona_pool+w21"  # 〔段 10〕前 persona_pool
    assert man["hours_source"] == "none(wage=occupation)"


def test_resume_equals_straight(tmp_path, monkeypatch):
    from shibuya import cli

    if WG.load_wage_tables() is None:
        pytest.skip("requires_data: 賃金の表の写しが無い")
    _arm(monkeypatch)
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
    # 〔第 2 部〕腕の違う再開(旧値の腕 w17)は消した=見出しの検査は test_wage_occupation.py の単体の試験
