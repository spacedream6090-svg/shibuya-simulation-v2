"""段 1b(D-96 nightlife (b)): 飲食店の切替口 ``eatery={food, place_food}``。

- ``food``(既定)= 現行の ``hash_free_cat_code(cat) == 1``=checkpoint はバイト不変。
- ``place_food`` = ``food`` ∨ (``cat == "nightlife"`` ∧ subcat ∉ {club, karaoke, sauna, net_cafe})
  = W17 の場所語「飲食店」に写る POI と**同じ集合**(実資産 1,042 件)。価格は動かさない。
- エンジンが W6 の ``subcat`` を読む最初の口(``WorldAssets.poi_subcat``)。
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest

from shibuya.engine.run import run_day
from shibuya.world.state import (
    DEFAULT_EATERY_MODE,
    EATERY_MODES,
    PLACE_FOOD_EXCLUDED_NIGHTLIFE_SUBCATS,
    World,
    check_eatery_mode,
)

WORLD_DIR = Path("data/world/v2")
real_data = pytest.mark.skipif(
    not (WORLD_DIR / "w6_poi.parquet").exists(), reason="実世界資産が無い"
)


def _world_with(cats: list[str], subcats: list[str] | None) -> World:
    """合成世界の POI の cat/subcat だけを差し替えた World(数は合成世界と同じ)。"""
    base = World.synthetic(n_cells=16, seed=1).assets
    n = base.n_poi
    cats = (cats * (n // len(cats) + 1))[:n]
    sub = () if subcats is None else tuple((subcats * (n // len(subcats) + 1))[:n])
    return World(dataclasses.replace(base, poi_cat=tuple(cats), poi_subcat=sub))


# ------------------------------------------------------------------ 値の検査・既定
def test_eatery_modes_and_default():
    assert EATERY_MODES == ("food", "place_food")
    assert DEFAULT_EATERY_MODE == "food"
    assert check_eatery_mode("place_food") == "place_food"
    with pytest.raises(ValueError):
        check_eatery_mode("nightlife")


def test_run_day_rejects_an_unknown_eatery_before_running():
    with pytest.raises(ValueError):
        run_day(n_agents=10, seed=1, ticks=2, renderer="stub", eatery="bar")


# ------------------------------------------------------------------ マスクの意味
def test_place_food_adds_nightlife_except_the_four_amusement_subcats():
    cats = ["food", "nightlife", "nightlife", "nightlife", "nightlife", "nightlife", "shop"]
    subs = ["", "", "club", "karaoke", "sauna", "net_cafe", "convenience"]
    w = _world_with(cats, subs)
    food = np.asarray(w.eatery_mask).copy()
    w.set_eatery_mode("place_food")
    place = np.asarray(w.eatery_mask)
    got = {(c, s): bool(m) for c, s, m in zip(w.assets.poi_cat, w.assets.poi_subcat, place)}
    assert got[("food", "")] is True
    assert got[("nightlife", "")] is True          # bar/pub=subcat 無し → 食事の場
    for s in ("club", "karaoke", "sauna", "net_cafe"):
        assert got[("nightlife", s)] is False      # 遊興の 4 種は外す
    assert got[("shop", "convenience")] is False
    assert not np.any(food & ~place), "place_food は food を含む(増えるだけ)"
    # 戻せる(キャッシュを捨てて組み直す)
    w.set_eatery_mode("food")
    assert np.array_equal(np.asarray(w.eatery_mask), food)


def test_place_food_refuses_a_world_without_subcat_when_nightlife_exists():
    w = _world_with(["food", "nightlife"], None)
    with pytest.raises(ValueError):
        w.set_eatery_mode("place_food")


def test_place_food_equals_food_on_the_synthetic_world():
    """合成世界(nightlife なし・subcat なし)では 2 つの腕は同じ集合=final も同じ。"""
    w = World.synthetic(n_cells=16, seed=1)
    food = np.asarray(w.eatery_mask).copy()
    w.set_eatery_mode("place_food")
    assert np.array_equal(np.asarray(w.eatery_mask), food)
    a = run_day(n_agents=40, seed=1, ticks=30, renderer="stub", vocab_version="v2",
                checkpoint_every=30, eatery="food")
    b = run_day(n_agents=40, seed=1, ticks=30, renderer="stub", vocab_version="v2",
                checkpoint_every=30, eatery="place_food")
    assert a.final_hash == b.final_hash
    assert a.run_manifest_fields()["eatery"] == "food"
    assert b.run_manifest_fields()["eatery"] == "place_food"


def test_run_day_resets_the_eatery_of_a_reused_world():
    """同じ World を使い回しても前のランの切替口は残らない(run_day が毎ラン書く)。"""
    w = _world_with(["food", "nightlife"], ["", ""])
    w.set_eatery_mode("place_food")
    res = run_day(n_agents=10, seed=1, ticks=2, renderer="stub", world=w)
    assert w.eatery_mode == "food" and res.eatery == "food"


def test_the_excluded_subcats_match_the_w17_place_word_table():
    """二重定義の一致: nightlife の subcat のうち W17 で「飲食店」以外へ写るもの。"""
    from shibuya.build.geo import poi_class as PC
    from shibuya.build.sched import vocab as V
    from shibuya.build.sched import w17_schedule as W17

    nightlife_subcats = {s for s, c in PC.SUBCAT_TOPCAT.items() if c == "nightlife"}
    to_other = {
        s for s in nightlife_subcats if W17.SUBCAT_TO_PLACE.get(s, V.PLACE_FOOD) != V.PLACE_FOOD
    }
    assert W17.CAT_TO_PLACE["nightlife"] == V.PLACE_FOOD
    assert to_other == set(PLACE_FOOD_EXCLUDED_NIGHTLIFE_SUBCATS)


# ------------------------------------------------------------------ 実資産
@real_data
def test_place_food_is_exactly_the_w17_place_word_food_set():
    """実資産: place_food の集合 = W17 の場所語「飲食店」へ写る POI(1,042 件)。food は 823 件。"""
    from shibuya.build.sched import vocab as V
    from shibuya.build.sched import w17_schedule as W17

    w = World.load_or_synthetic(WORLD_DIR, n_cells=139, seed=1)
    assert len(w.assets.poi_subcat) == w.n_poi
    food = np.asarray(w.eatery_mask).copy()
    w.set_eatery_mode("place_food")
    place = np.asarray(w.eatery_mask)
    place_word_food = np.array(
        [
            W17.SUBCAT_TO_PLACE.get(str(s), W17.CAT_TO_PLACE.get(str(c), -1)) == V.PLACE_FOOD
            for c, s in zip(w.assets.poi_cat, w.assets.poi_subcat)
        ],
        dtype=bool,
    )
    assert int(food.sum()) == 823
    assert int(place.sum()) == 1_042
    assert np.array_equal(place, place_word_food)
    # 価格は動かさない(nightlife は 1,500 円のまま)
    night = np.array([c == "nightlife" for c in w.assets.poi_cat])
    assert set(np.asarray(w.pois.price)[night].tolist()) == {1_500}
