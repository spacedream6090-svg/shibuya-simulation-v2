"""〔第 2 期 2-4 V4〕経済の段階 2 の既定 on・切替口 off・効いている腕で見る再開の検査・店の売上の写しは税抜き。

記録 ``docs/bench/analysis/wallbounce-1012/vb24/README.md`` の V4。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.economy import stage2 as S2
from shibuya.engine import economy_stage2 as ES2


def test_default_arm_is_on_and_off_is_the_switch(monkeypatch):
    assert ES2.DEFAULT_ARM == ES2.ARM_ON
    monkeypatch.setattr(ES2, "_ARM", ES2.DEFAULT_ARM)
    assert ES2.arm() == "on" and ES2.active_parts() == frozenset(ES2.PARTS)
    monkeypatch.setattr(ES2, "_ARM", ES2.ARM_OFF)
    assert ES2.active_parts() == frozenset()


def test_resume_check_uses_the_effective_arm(monkeypatch):
    """金の台帳の無いラン(台帳なしの run_day)は腕 on でも段階 2 を挿さない=見出しに書かない=off と同じに扱う。"""
    monkeypatch.setattr(ES2, "_ARM", ES2.ARM_ON)
    ES2.check_resume(None, effective=False)  # 台帳なし=off どうし
    with pytest.raises(ValueError, match="経済の段階 2 の腕"):
        ES2.check_resume(None)  # 台帳あり=親 off・今 on
    # 〔賃金の小さな版上げ〕腕 on の見出しは賃金の腕も持つ(見出しに無い=w17=版上げの前の状態)
    want = {"arm": "on", "parts": list(ES2.PARTS)}
    want["wage"] = ES2.wage_arm()  # 〔第 2 部〕見出しは賃金の道も持つ
    from shibuya.engine import economy_rules as ER  # 〔第 4 期 4-2〕既定 on の見出しは規則の表の中身の腕も持つ

    if ER.arm() != ER.ARM_OFF:
        want["rules_42"] = ER.arm()
        if ER.arm_42b() != ER.ARM_OFF:  # 〔第 4 期 4-2b〕空欄 3 件を埋めた値の腕(off の見出しは 4-2 のまま)
            want["rules_42b"] = ER.arm_42b()
    ES2.check_resume(want)
    with pytest.raises(ValueError):
        ES2.check_resume(want, effective=False)


def test_tax_of_and_the_last_purchase_rows():
    from fractions import Fraction

    a = np.array([110, 1100, 0, 5], dtype=np.int64)
    assert S2.tax_of(a, Fraction(1, 10)).tolist() == [10, 100, 0, 0]  # 税込の額 × 10/110 の切り捨て


def test_revenue_is_tax_exclusive_on_a_synthetic_run(monkeypatch):
    """合成の世界(台帳つき)の 1 日: 店の売上の写しの合計=世帯 → 店の消費支出 − レジの税・保存則が通る。"""
    from shibuya import cli
    from shibuya.economy.accounts import AccountCode, Sector

    monkeypatch.setattr(ES2, "_ARM", ES2.ARM_ON)
    res = cli.run(n_agents=200, seed=2, world_dir=None, use_population=False, vocab_version="v3")
    led = res.ledger.money
    if led.stage2 is None:
        pytest.skip("合成の世界の組み立てでは段階 2 が挿さらない")
    flow = sum(np.asarray(x) for x in led.flow_daily) + np.asarray(led.flow)
    cons = int(flow[int(Sector.HOUSEHOLD), int(Sector.STORE), int(AccountCode.CONSUMPTION)])
    tax = led.stage2.register_tax()
    assert res.conserved and res.revenue_end == cons - tax
