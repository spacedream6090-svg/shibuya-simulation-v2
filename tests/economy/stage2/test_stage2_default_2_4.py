"""〔第 2 期 2-4 V4〕経済の段階 2 の既定 on・切替口 off・効いている腕で見る再開の検査・店の売上の写しは税抜き。

記録 ``docs/bench/analysis/wallbounce-1012/vb24/README.md`` の V4。〔第347 止めた切替口の削除〕切替口 off は消した
(記録 ``docs/bench/analysis/switch-removal-347/README.md`` の ②a)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.economy import stage2 as S2
from shibuya.economy import stage2_bind as ES2


def test_stage2_is_always_on_and_the_off_switch_is_removed(monkeypatch):
    """〔第347〕前(``test_default_arm_is_on_and_off_is_the_switch``)は「既定 on・切替口 off で部品が空」。切替口 off を消した:
    腕を選ぶ名が無い・部品はいつも効く・消した環境変数の名と安定版のタグは止める一覧にある(止まることは
    ``tests/engine/test_removed_switches_346.py``)。"""
    from shibuya.foundation.arms import removed as RSW

    for name in ("ARMS", "DEFAULT_ARM", "_ARM", "arm", "set_arm"):
        assert not hasattr(ES2, name), name
        assert name not in ES2.__all__, name
    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)
    assert ES2.active_parts() == frozenset(ES2.PARTS)
    monkeypatch.setattr(ES2, "_PARTS", ("wages",))
    assert ES2.active_parts() == frozenset({"wages"})
    assert ES2.ENV_REMOVED == "SHIBUYA_ECONOMY_STAGE2" and ES2.ENV_REMOVED in RSW.REMOVED_ENV
    assert RSW.tag_of(ES2.ENV_REMOVED) == RSW.REMOVED_SWITCH_TAG_347 == "stable-v2-before-switch-removal-347"
    assert (ES2.ARM_ON, ES2.ARM_OFF) == ("on", "off")  # 見出しの値と、見出しに無いときの読み(残す)


def test_resume_check_uses_the_effective_arm(monkeypatch):
    """金の台帳の無いラン(台帳なしの run_day)は腕 on でも段階 2 を挿さない=見出しに書かない=off と同じに扱う。"""
    ES2.check_resume(None, effective=False)  # 台帳なし=off どうし
    # 〔第347・検収 A-8〕止める文は、消した切替口と旧値の再現の安定版のタグも書く(前は文の前半だけを見ていた)
    with pytest.raises(ValueError, match="経済の段階 2 の腕が親と違う.*--economy-stage2 off は消した.*"
                                         "stable-v2-before-switch-removal-347 で回す"):
        ES2.check_resume(None)  # 台帳あり=親 off・今 on
    # 〔賃金の小さな版上げ〕腕 on の見出しは賃金の腕も持つ(見出しに無い=w17=版上げの前の状態)
    want = {"arm": "on", "parts": list(ES2.PARTS)}
    want["wage"] = ES2.wage_arm()  # 〔第 2 部〕見出しは賃金の道も持つ
    # 〔第 4 期 4-2・4-2b〕見出しは規則の表の中身と空欄 3 件を埋めた値も持つ(〔第346〕切替口 SHIBUYA_RULES_42・42B は消した)
    want["rules_42"] = "on"
    want["rules_42b"] = "on"
    ES2.check_resume(want)
    with pytest.raises(ValueError):
        ES2.check_resume(want, effective=False)


def test_tax_of_and_the_last_purchase_rows():
    from fractions import Fraction

    a = np.array([110, 1100, 0, 5], dtype=np.int64)
    assert S2.tax_of(a, Fraction(1, 10)).tolist() == [10, 100, 0, 0]  # 税込の額 × 10/110 の切り捨て


def test_revenue_is_tax_exclusive_on_a_synthetic_run(monkeypatch):
    """合成の世界(台帳つき)の 1 日: 店の売上の写しの合計=世帯 → 店の消費支出 − レジの税・保存則が通る。"""
    from shibuya.interfaces.cli import main as cli
    from shibuya.economy.accounts import AccountCode, Sector

    monkeypatch.setattr(ES2, "_PARTS", ES2.PARTS)  # 部品をモジュールの既定に押さえる(ほかの試験の漏れに依らない)
    res = cli.run(n_agents=200, seed=2, world_dir=None, use_population=False, vocab_version="v3")
    led = res.ledger.money
    # 〔第347・検収 L2〕前は「段階 2 が挿さらなければ飛ばす」だった。切替口 off を消した後(②a)は、cli の台帳はいつも段階 2 の
    # 口を持つ=挿さらないのは欠陥=飛ばさず落とす
    assert led.stage2 is not None, "cli の台帳に段階 2 が挿さらなかった"
    flow = sum(np.asarray(x) for x in led.flow_daily) + np.asarray(led.flow)
    cons = int(flow[int(Sector.HOUSEHOLD), int(Sector.STORE), int(AccountCode.CONSUMPTION)])
    tax = led.stage2.register_tax()
    assert tax > 0  # 税の部品が働いた(空振りしない)
    assert res.conserved and res.revenue_end == cons - tax
