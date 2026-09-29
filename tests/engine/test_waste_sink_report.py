"""第304 Q135 (a)(小さいもの 第 2 批④): ラン要約の廃棄帯=**店だけの静的な帯**+内訳 3 つ(報告だけ)。

- 帯 = 店舗の期限切れ在庫の静的な期待値(初期在庫 × SKU 廃棄率(切り捨て)× 質量)× (1 ± 30%)・体数に依らない。
- OK/NG は**店の収集量**で判定。内訳=店・世帯の消費・街路(と物の台帳のその他)。区の総排出量との比較は保留。
- 報告だけ=checkpoint は動かない(物の台帳の ``waste_band``=W1 の区の総量はそのまま・月次センサスが使う)。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya import cli
from shibuya.economy.anchors import WASTE_BAND_RATIO, WASTE_TONNES_PER_DAY
from shibuya.economy.goods import GoodsLedger, SkuRegistry

WORLD_DIR = Path(__file__).resolve().parents[2] / "data" / "world" / "v2"


def test_static_store_waste_is_floor_of_stock_times_rate_times_mass():
    reg = SkuRegistry.default()
    cats = np.array([0, 1, 2, 0])            # コンビニ / 飲食 / 物販 / コンビニ
    stock = np.array([64, 64, 64, 10])
    g = GoodsLedger(cats, stock, np.full(4, 100, dtype=np.int64), registry=reg)
    shelf = np.asarray(g.shelf, dtype=np.int64)
    sku = np.asarray(g.poi_sku, dtype=np.int64)
    want = 0.0
    for r in range(4):
        for s in range(sku.shape[1]):
            if sku[r, s] >= 0:
                want += np.floor(shelf[r, s] * reg.waste_rate[sku[r, s]]) * reg.mass_g[sku[r, s]]
    assert g.static_store_waste_g == pytest.approx(want)
    assert g.static_store_waste_g > 0
    e, lo, hi = g.store_waste_band()
    assert (e, lo, hi) == pytest.approx((want / 1e6, want / 1e6 * (1 - WASTE_BAND_RATIO), want / 1e6 * (1 + WASTE_BAND_RATIO)))
    # 物の台帳の W1(区の総量)の帯は変えない(月次センサスが使う)
    band = g.waste_band(days=1)
    assert (band.low, band.high) == pytest.approx((WASTE_TONNES_PER_DAY * (1 - WASTE_BAND_RATIO),
                                                   WASTE_TONNES_PER_DAY * (1 + WASTE_BAND_RATIO)))


def test_run_summary_uses_the_store_band_and_lists_three_sources():
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "c7"))
    import c7lib

    res = cli.run(n_agents=200, seed=3, world_dir=None, n_cells=16, ticks=720, checkpoint_every=360)
    ws = res.waste_sink
    assert set(ws["breakdown_t"]) == {"store_expired_stock", "household_consumption", "street_litter", "other_goods"}
    lo, hi = res.waste_band
    e = ws["expected_store_t"]
    assert (lo, hi) == pytest.approx((e * 0.7, e * 1.3)) and e > 0
    b = ws["breakdown_t"]
    total = b["store_expired_stock"] + b["household_consumption"] + b["street_litter"] + b["other_goods"]
    assert total == pytest.approx(ws["total_t"], abs=1e-5)
    assert res.waste_tonnes_per_day == pytest.approx(ws["total_t"], abs=1e-5)
    assert res.waste_band_ok == ws["band_ok"] == (lo <= b["store_expired_stock"] <= hi)
    assert "区" in ws["ward_total_comparison"] and "保留" in ws["ward_total_comparison"]  # noqa: RUF001
    assert res.run_manifest_fields()["waste_sink"] == ws
    text = res.summary()
    assert "店の帯 (band" in text and "区の総排出量との比較は保留" in text
    assert "自己整合性の検査" in text and "現実との照合ではない" in text          # 第305 Q138
    assert "自己整合性の検査" in ws["band_check"]
    got = c7lib.parse_run_summary(text)  # 受入表の読み口は変えない
    assert got["waste_tonnes_per_day"] == pytest.approx(round(res.waste_tonnes_per_day, 3))
    assert got["waste_band_ok"] is res.waste_band_ok


@pytest.mark.skipif(not (WORLD_DIR / "w2_cells.parquet").exists(), reason="実世界資産 data/world/v2 が無い")
def test_real_world_store_band_is_0_911_t_per_day_for_any_agent_count():
    """実世界(2,337 POI・初期在庫 64): 0.911 t/日 ±30% = 0.64〜1.18(体数に依らない)。"""
    from shibuya.world.assets import hash_free_cat_code
    from shibuya.world.state import World

    w = World.load_or_synthetic(WORLD_DIR, n_cells=139, seed=1)
    cats = np.array([hash_free_cat_code(c) for c in w.assets.poi_cat], dtype=np.int64)
    got = {n: GoodsLedger.from_pois(cats, np.asarray(w.pois.stock), np.asarray(w.pois.price), n_agents=n)
           .static_store_waste_g for n in (5_000, 390_067)}
    assert got[5_000] == got[390_067] == pytest.approx(910_750.0)


def test_monthly_census_uses_the_store_band_and_the_store_collected_mass():
    """第305 Q137: 月次センサスの帯も店だけの帯(判定=店の回収量 t/日)・帯の意味を明記(報告だけ)。"""
    from shibuya.economy import census as CS

    res = cli.run(n_agents=200, seed=3, world_dir=None, n_cells=16, ticks=720, checkpoint_every=360)
    goods = res.ledger.goods
    e, lo, hi = goods.store_waste_band()
    mer = CS.monthly_mer(res.ledger.money, goods, month=0, days=1)
    assert mer["waste_band"] == (lo, hi)
    assert mer["waste_store_tonnes_per_day"] == pytest.approx(res.waste_sink["breakdown_t"]["store_expired_stock"], abs=1e-6)
    assert mer["waste_band_ok"] is res.waste_band_ok
    assert mer["waste_band_check"] == goods.STORE_WASTE_BAND_NOTE
    assert "自己整合性の検査" in goods.STORE_WASTE_BAND_NOTE and "現実との照合ではない" in goods.STORE_WASTE_BAND_NOTE
    # 総量(物の台帳=店+世帯の消費)は従来の欄のまま
    assert mer["waste_tonnes_per_day"] == pytest.approx(goods.waste_band(days=1).tonnes_per_day)
