"""D-13 店舗参入資本の按分(economy.entry_capital)のテスト。

門にすること
- POI カテゴリ → 産業大分類の**写像表が全カテゴリを覆う**(実資産 13 値 + 合成 3 値)。
- 非負・合計=個別和・決定論(乱数なし)。
- 参入資本の注入は ``endow_stores``(外界 → 店舗)のまま=**ex nihilo 禁止**が守られる。
- 単調性(hypothesis): k・母集団比・年商のどれを上げても参入資本は下がらない。
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shibuya.economy import entry_capital as EC
from shibuya.economy import goods as GD
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.ledger import Ledger

#: 実資産 ``data/world/v2/w6_poi.parquet`` の cat 13 値(親が実データで確認・2026-09-09)。
REAL_POI_CATS = (
    "food", "shop", "nightlife", "office", "service", "hotel", "school",
    "landmark", "leisure", "hall", "attraction", "cinema", "education",
)
#: 合成世界 ``world.assets.SYNTHETIC_POI_CATS``。
SYNTHETIC_POI_CATS = ("コンビニ", "飲食", "物販")


# ---------------------------------------------------------------- 写像表
def test_mapping_covers_every_poi_category():
    """実資産 13 値 + 合成 3 値のすべてに大分類がつく(既定へ落ちない)。"""
    for cat in (*REAL_POI_CATS, *SYNTHETIC_POI_CATS):
        assert cat in EC.POI_CAT_TO_INDUSTRY, cat
        code = EC.industry_of(cat)
        assert code in EC.SALES_PER_ESTABLISHMENT_BY_INDUSTRY, (cat, code)
    assert len(EC.POI_CAT_TO_INDUSTRY) == 16


def test_unknown_category_falls_back_to_the_declared_default():
    assert EC.industry_of("未知のカテゴリ") == EC.DEFAULT_INDUSTRY
    assert EC.DEFAULT_INDUSTRY in EC.SALES_PER_ESTABLISHMENT_BY_INDUSTRY


def test_every_mapped_industry_has_published_sales():
    """写像先が「調査していないもの(･･･)/秘匿(X)」の大分類になっていない。"""
    used = set(EC.POI_CAT_TO_INDUSTRY.values()) | {EC.DEFAULT_INDUSTRY}
    assert used.isdisjoint(EC.UNPUBLISHED_INDUSTRIES.keys())
    for code in used:
        assert EC.SALES_PER_ESTABLISHMENT_BY_INDUSTRY[code] > 0
        assert code in EC.INDUSTRY_NAMES


def test_census_values_are_the_raw_156_2021_figures():
    """センサス 156-2021(万円)× 10,000。**親が JSON で一次確認した生値**。

    設計書 §2.5 と ``anchors.SALES_PER_ESTABLISHMENT`` は I と N が末尾 1 桁落ちの
    転記(1億3,152万/2,253万)になっている=**親判断待ち**。ここでは生値を正とする。
    """
    S = EC.SALES_PER_ESTABLISHMENT_BY_INDUSTRY
    assert S["M"] == 8_532 * 10_000  # 宿泊業，飲食サービス業
    assert S["I"] == 131_523 * 10_000  # 卸売業，小売業
    assert S["N"] == 22_527 * 10_000  # 生活関連サービス業，娯楽業
    assert S["L"] == 44_401 * 10_000
    assert S["R2"] == 64_043 * 10_000
    assert S["O2"] == 15_439 * 10_000
    assert all(v > 0 for v in S.values())


def test_price_band_matches_world_assets_hash_free_cat_code():
    """層契約で複製した ``price_band`` が world 側の正典と一致する(等価テスト)。"""
    from shibuya.world.assets import hash_free_cat_code

    for cat in (*REAL_POI_CATS, *SYNTHETIC_POI_CATS, "未知", "cafe", "restaurant"):
        assert EC.price_band(cat) == hash_free_cat_code(cat), cat


def test_cost_ratio_comes_from_the_goods_category_k():
    """原価率は ``goods.CATEGORY_K`` の逆数(新しい定数を置いていない)。"""
    assert len(EC.COST_RATIO_BY_BAND) == len(GD.CATEGORY_K) == 3
    for r, k in zip(EC.COST_RATIO_BY_BAND, GD.CATEGORY_K):
        assert r == pytest.approx(1.0 / k)
    assert EC.COST_RATIO_BY_BAND[0] == pytest.approx(0.20)  # コンビニ


def test_full_scale_agents_matches_the_l4_budget_denominator():
    """母集団比の分母は L4 予算の按分分母と同じ 400,000(engine 側が正典)。"""
    from shibuya.engine.arbiter import L4_REFERENCE_AGENTS

    assert EC.FULL_SCALE_AGENTS == L4_REFERENCE_AGENTS


# ---------------------------------------------------------------- 金額
def test_capital_is_non_negative_and_within_the_declared_bounds():
    cap = EC.store_entry_capital(REAL_POI_CATS * 10, n_agents=5_000)
    assert cap.dtype == np.int64
    assert (cap >= 0).all()
    assert (cap >= EC.MIN_ENTRY_CAPITAL_YEN).all()
    assert (cap <= EC.MAX_ENTRY_CAPITAL_YEN).all()
    assert (cap % EC.ROUND_TO_YEN == 0).all()


def test_bounds_are_multiples_of_the_rounding_step():
    assert EC.MIN_ENTRY_CAPITAL_YEN % EC.ROUND_TO_YEN == 0
    assert EC.MAX_ENTRY_CAPITAL_YEN % EC.ROUND_TO_YEN == 0


def _unclipped(cats, **kw) -> np.ndarray:
    return EC.store_entry_capital(cats, min_yen=0, max_yen=10**15, **kw)


def test_neither_bound_binds_at_the_operating_scales():
    """下限・上限は運用スケール(5,000〜400,000 体)で**発動しない**(按分がそのまま出る)。"""
    for n in (5_000, 40_000, 400_000):
        cap = EC.store_entry_capital(REAL_POI_CATS, n_agents=n)
        assert np.array_equal(cap, _unclipped(REAL_POI_CATS, n_agents=n)), n


def test_the_floor_binds_only_below_about_1900_agents():
    """最小カテゴリ(M 宿泊飲食)が下限に当たるのは約 1,883 体未満(境界を固定する)。"""
    assert _unclipped(["food"], n_agents=1_000)[0] < EC.MIN_ENTRY_CAPITAL_YEN
    assert EC.store_entry_capital(["food"], n_agents=1_000)[0] == EC.MIN_ENTRY_CAPITAL_YEN
    assert _unclipped(["food"], n_agents=1_900)[0] >= EC.MIN_ENTRY_CAPITAL_YEN


def test_is_deterministic_no_rng():
    cats = list(REAL_POI_CATS) * 7
    a = EC.store_entry_capital(cats, n_agents=5_000)
    b = EC.store_entry_capital(cats, n_agents=5_000)
    assert np.array_equal(a, b)
    # 順序を入れ替えても、同じカテゴリには同じ額(位置に依存しない)
    idx = np.arange(len(cats))[::-1]
    c = EC.store_entry_capital([cats[i] for i in idx], n_agents=5_000)
    assert np.array_equal(c, a[idx])


def test_total_equals_the_sum_of_the_parts():
    cats = list(REAL_POI_CATS) * 3
    cap = EC.store_entry_capital(cats, n_agents=5_000)
    rep = EC.entry_capital_report(cap, cats, scale=EC.population_scale(5_000))
    assert rep.total_yen == int(cap.sum()) == sum(int(x) for x in cap)
    assert rep.n_stores == len(cats)
    assert sum(n for _, n, _, _ in rep.by_industry) == len(cats)
    assert sum(t for _, _, t, _ in rep.by_industry) == rep.total_yen


def test_empty_world_gives_an_empty_array():
    cap = EC.store_entry_capital([], n_agents=5_000)
    assert cap.shape == (0,)
    assert int(cap.sum()) == 0


def test_apportionment_differentiates_categories():
    """一律ではない: 卸売・小売(shop)は宿泊飲食(food)より大きい。"""
    cap = EC.store_entry_capital(["food", "shop", "hotel"], n_agents=5_000)
    assert cap[1] > cap[0]
    assert len(set(cap.tolist())) >= 2


def test_population_scale_is_one_at_full_scale():
    assert EC.population_scale(EC.FULL_SCALE_AGENTS) == 1.0
    assert EC.population_scale(None) == 1.0
    assert EC.population_scale(5_000) == pytest.approx(0.0125)


def test_report_carries_the_money_supply_share():
    cats = list(REAL_POI_CATS)
    cap = EC.store_entry_capital(cats, n_agents=5_000)
    rep = EC.entry_capital_report(cap, cats, household_cash_yen=1_000_000)
    assert rep.money_supply_yen == rep.total_yen + 1_000_000
    assert 0.0 < rep.share_of_money_supply < 1.0
    assert "参入資本" in rep.as_text()


# ---------------------------------------------------------------- 台帳(保存則)
def test_endowment_is_a_transfer_from_the_row_not_ex_nihilo():
    """按分版でも注入は外界 → 店舗の transfer(§2.3 ex nihilo 禁止)。"""
    cats = list(REAL_POI_CATS)
    cap = EC.store_entry_capital(cats, n_agents=5_000)
    led = Ledger(10, len(cats))
    led.endow_stores(cap, tick=0)
    cash = led.sector_totals(BalanceLine.CASH)
    assert int(cash[int(Sector.STORE)]) == int(cap.sum())
    assert int(cash[int(Sector.ROW)]) == -int(cap.sum())  # 外界が出した(湧いていない)
    assert int(cash.sum()) == 0  # 行和 0(検算①)
    flow = np.asarray(led.flow)
    assert int(flow[int(Sector.ROW), int(Sector.STORE), int(AccountCode.ENTRY_CAPITAL)]) == int(
        cap.sum()
    )


def test_share_of_money_supply_from_the_ledger():
    cats = list(REAL_POI_CATS)
    cap = EC.store_entry_capital(cats, n_agents=5_000)
    led = Ledger(4, len(cats))
    led.endow_households(np.full(4, 100_000, dtype=np.int64), 0)
    led.endow_stores(cap, tick=0)
    store, m, share = EC.ledger_entry_capital_share(led)
    assert store == int(cap.sum())
    assert m == store + 400_000
    assert share == pytest.approx(store / m)


# ---------------------------------------------------------------- hypothesis(単調性)
@settings(max_examples=60, deadline=None)
@given(
    days=st.floats(min_value=1.0, max_value=365.0),
    bump=st.floats(min_value=1.0, max_value=50.0),
    n=st.integers(min_value=1_000, max_value=400_000),
    mult=st.floats(min_value=1.0, max_value=20.0),
)
def test_capital_is_monotone_in_k_and_in_the_population_scale(days, bump, n, mult):
    """k・母集団比を上げると参入資本は**下がらない**(丸めと上限の範囲で単調)。"""
    cats = list(REAL_POI_CATS)
    lo = EC.store_entry_capital(cats, n_agents=n, days=days)
    hi = EC.store_entry_capital(cats, n_agents=n, days=days * bump)
    assert (hi >= lo).all()
    scaled = EC.store_entry_capital(cats, scale=EC.population_scale(n) * mult, days=days)
    assert (scaled >= lo).all()
    # 売上基準(原価率をかけない)は仕入基準より必ず大きいか等しい
    gross = EC.store_entry_capital(cats, n_agents=n, days=days, cost_basis=False)
    assert (gross >= lo).all()
