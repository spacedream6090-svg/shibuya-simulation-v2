"""W6 POI 分類(``build.geo.poi_class``)の単体テスト(データ不要・CI で常に走る)。

固定する欠陥(答申 ``docs/research/v2-hobby-preference-research.md`` §5-2/§5-3)
- 公園 POI が場所語「娯楽施設」に潰れ、``PLACE_PARK`` へ写る POI が 0 件だった。
- ``hall`` / ``attraction`` / ``leisure`` の subcat 付け漏れ。
- 書店・楽器店・図書館が種別でも subcat でも引けなかった。

方針の検査
- 分類の一次根拠は **OSM タグ**。名前一致は最後の手段で、cat を跨いで当たらない。
- cat の語彙 13 種は 1 つも動かない。
"""

from __future__ import annotations

import pytest

from shibuya.build.geo import poi_class as PC
from shibuya.build.geo import w6_poi_org as W6
from shibuya.build.sched import vocab as V
from shibuya.build.sched import w17_schedule as W17

# v8 が凍結している subcat 語彙(``shibuya_osm_wide_v8.json`` の ``meta.subcat_vocab``)。
V8_FROZEN_SUBCATS = (
    "arcade",
    "childcare",
    "club",
    "convenience",
    "hospital",
    "karaoke",
    "love_hotel",
    "net_cafe",
    "pachinko",
    "sauna",
    "worship",
)

# 本改訂(2026-09-17)で足した subcat 20 語。
ADDED_SUBCATS = (
    "park",
    "gym",
    "sports_centre",
    "theatre",
    "music_venue",
    "events_venue",
    "museum",
    "gallery",
    "library",
    "books",
    "music_shop",
    "musical_instrument",
    "video_games",
    "hobby",
    "art_supply",
    "stationery",
    "photo",
    "florist",
    "sports_shop",
    "bicycle",
)

# cat の語彙(``build/lang/w14_signage.py`` の CAT_WORDS と同じ 13 種)。
CAT_VOCAB = (
    "attraction",
    "cinema",
    "education",
    "food",
    "hall",
    "hotel",
    "landmark",
    "leisure",
    "nightlife",
    "office",
    "school",
    "service",
    "shop",
)


def _place_of(cat: str, subcat: str | None) -> int:
    """W17 と同じ引き方(``open_share`` の 1 行)で場所種別を出す。"""
    return W17.SUBCAT_TO_PLACE.get(str(subcat), W17.CAT_TO_PLACE.get(str(cat), -1))


# --- 一次: OSM タグ → subcat ---------------------------------------------------------


@pytest.mark.parametrize(
    "tags,expected",
    [
        # 欠陥 1: 公園。leisure=park/garden/playground はすべて park。
        ({"leisure": "park"}, "park"),
        ({"leisure": "garden"}, "park"),
        ({"leisure": "playground"}, "park"),
        # 欠陥 2: leisure の中に同居していた業態。
        ({"leisure": "fitness_centre"}, "gym"),
        ({"amenity": "gym"}, "gym"),
        ({"leisure": "sports_centre"}, "sports_centre"),
        # 欠陥 2: hall の中に同居していた業態。
        ({"amenity": "theatre"}, "theatre"),
        ({"amenity": "music_venue"}, "music_venue"),
        ({"amenity": "events_venue"}, "events_venue"),
        ({"amenity": "conference_centre"}, "events_venue"),
        # 欠陥 2: attraction の中に同居していた業態。
        ({"tourism": "museum"}, "museum"),
        ({"tourism": "gallery"}, "gallery"),
        # 欠陥 3: 名前でしか引けなかった 3 種。
        ({"shop": "books"}, "books"),
        ({"shop": "musical_instrument"}, "musical_instrument"),
        ({"amenity": "library"}, "library"),
        # 趣味の受け皿(要る物)。
        ({"shop": "music"}, "music_shop"),
        ({"shop": "video_games"}, "video_games"),
        ({"shop": "stationery"}, "stationery"),
        ({"shop": "photo"}, "photo"),
        ({"shop": "florist"}, "florist"),
        ({"shop": "sports"}, "sports_shop"),
        ({"shop": "outdoor"}, "sports_shop"),
        ({"shop": "fishing"}, "sports_shop"),
        ({"shop": "bicycle"}, "bicycle"),
        ({"shop": "art"}, "art_supply"),
        ({"shop": "hobby"}, "hobby"),
        # v1 から凍結している 11 語(規則の移植が 1 バイトずれていないこと)。
        ({"shop": "convenience"}, "convenience"),
        ({"amenity": "gambling"}, "pachinko"),
        ({"amenity": "karaoke_box"}, "karaoke"),
        ({"amenity": "nightclub"}, "club"),
        ({"amenity": "internet_cafe"}, "net_cafe"),
        ({"leisure": "sauna"}, "sauna"),
        ({"leisure": "amusement_arcade"}, "arcade"),
        ({"amenity": "place_of_worship"}, "worship"),
        ({"amenity": "hospital"}, "hospital"),
        ({"amenity": "love_hotel"}, "love_hotel"),
        ({"amenity": "kindergarten"}, "childcare"),
        # 見ないキー・当てはまらない値。
        ({"building": "yes"}, None),
        ({"highway": "crossing"}, None),
        ({"shop": "clothes"}, None),
        ({}, None),
    ],
)
def test_poi_subcategory_from_raw_tags(tags, expected):
    assert PC.poi_subcategory(tags) == expected


def test_poi_subcategory_never_reads_the_name():
    """名前は一次規則に一切入らない(タグが無ければ None)。"""
    assert PC.poi_subcategory({"name": "代々木公園", "name:ja": "代々木公園"}) is None


def test_poi_subcategory_is_deterministic_in_rule_order():
    """複数の値が当たるときは SUBCAT_TAG_VALUES の並び順で決まる。"""
    # shop=books(後ろ)と amenity=hospital(前)が同時にあるときは hospital。
    assert PC.poi_subcategory({"amenity": "hospital", "shop": "books"}) == "hospital"


# --- 一次: OSM タグ → cat -----------------------------------------------------------


def test_poi_category_keeps_park_in_leisure_cat():
    """cat の語彙は動かさない。公園は cat=leisure のまま、subcat で分ける。"""
    tags = {"leisure": "park", "name": "代々木公園"}
    assert PC.poi_category(tags) == "leisure"
    assert PC.poi_subcategory(tags) == "park"


@pytest.mark.parametrize(
    "tags,expected",
    [
        ({"amenity": "restaurant"}, "food"),
        ({"amenity": "cinema"}, "cinema"),
        ({"amenity": "theatre"}, "hall"),
        ({"amenity": "library"}, "service"),
        ({"shop": "books"}, "shop"),
        ({"tourism": "museum"}, "attraction"),
        ({"leisure": "fitness_centre"}, "leisure"),
        ({"name": "忠犬ハチ公像"}, "landmark"),
        ({"highway": "crossing"}, None),
    ],
)
def test_poi_category_from_raw_tags(tags, expected):
    assert PC.poi_category(tags) == expected


def test_poi_category_stays_inside_the_frozen_cat_vocabulary():
    seen = {PC.poi_category(t) for t in ({"shop": "books"}, {"leisure": "park"}, {"amenity": "bar"})}
    assert seen <= set(CAT_VOCAB)
    assert set(PC.SUBCAT_TOPCAT.values()) <= set(CAT_VOCAB)


# --- 語彙の閉じ方 --------------------------------------------------------------------


def test_every_tag_rule_has_a_topcat():
    assert {s for s, _ in PC.SUBCAT_TAG_VALUES} <= set(PC.SUBCAT_TOPCAT)


def test_every_name_rule_has_a_topcat():
    assert {s for s, _ in PC.NAME_SUBCAT_RULES} <= set(PC.SUBCAT_TOPCAT)


def test_pattern_ledger_gate_every_subcat_states_its_use():
    """パターン台帳ゲート: どの現実パターン照合で使うか 1 行で書けない語は足さない。"""
    missing = sorted(set(PC.SUBCAT_TOPCAT) - set(PC.SUBCAT_PATTERN_USE))
    assert missing == []
    assert all(PC.SUBCAT_PATTERN_USE[s].strip() for s in PC.SUBCAT_TOPCAT)


def test_v1_frozen_subcats_are_still_there_with_the_same_topcat():
    for sub in V8_FROZEN_SUBCATS:
        assert sub in PC.SUBCAT_TOPCAT, sub
    assert PC.SUBCAT_TOPCAT["arcade"] == "leisure"
    assert PC.SUBCAT_TOPCAT["pachinko"] == "shop"
    assert PC.SUBCAT_TOPCAT["worship"] == "landmark"


def test_tag_rule_order_starts_with_the_v1_eleven():
    """v1 の 11 語を先頭に固定する(判定順が変わると既存 POI の subcat が動きうる)。"""
    assert [s for s, _ in PC.SUBCAT_TAG_VALUES][:11] == [
        "convenience",
        "pachinko",
        "karaoke",
        "club",
        "net_cafe",
        "sauna",
        "arcade",
        "worship",
        "hospital",
        "love_hotel",
        "childcare",
    ]


def test_catsub_pairs_closure_matches_topcat_table():
    assert set(PC.CATSUB_PAIRS) == {(PC.SUBCAT_TOPCAT[s], s) for s in PC.SUBCAT_TOPCAT}


# --- 最後の手段: 名前一致(expedient)-------------------------------------------------


@pytest.mark.parametrize(
    "name,cat,expected",
    [
        ("こもれび大和田図書館", "service", "library"),
        ("代々木公園", "leisure", "park"),
        ("宇田川公園", "leisure", "park"),
        ("鶯谷緑地", "leisure", "park"),
        ("代々木第一体育館", "leisure", "sports_centre"),
        ("猿楽トレーニングジム", "leisure", "gym"),
        ("エニタイムフィットネス", "leisure", "gym"),
        ("渋谷区立松濤美術館", "attraction", "museum"),
        ("ギャラリー・ルデコ", "attraction", "gallery"),
        ("パルコ劇場", "hall", "theatre"),
        ("シアター代官山", "hall", "theatre"),
        ("渋谷ライブハウス代官山LOOP", "hall", "music_venue"),
        # 業種を表す語が無ければ当てない(=空欄のまま残す)。
        ("NHKホール", "hall", None),
        ("WWW", "hall", None),
        ("", "leisure", None),
    ],
)
def test_subcat_from_name(name, cat, expected):
    assert PC.subcat_from_name(name, cat) == expected


def test_name_rules_do_not_cross_the_cat():
    """「代々木公園陸上競技場」は cat=hall。名前に「公園」があっても park にしない。"""
    assert PC.subcat_from_name("代々木公園陸上競技場", "hall") is None
    assert PC.subcat_from_name("代々木公園", "shop") is None


# --- 3 層の合成 ----------------------------------------------------------------------


def test_resolve_prefers_raw_tags_over_frozen_value():
    sub, src = PC.resolve_subcat("nightlife", "どこかの店", None, {"amenity": "nightclub"})
    assert (sub, src) == ("club", "osm_tag")


def test_resolve_falls_back_to_frozen_when_no_tags():
    sub, src = PC.resolve_subcat("shop", "どこかの店", "convenience", None)
    assert (sub, src) == ("convenience", "frozen")


def test_resolve_uses_name_only_as_the_last_resort():
    sub, src = PC.resolve_subcat("service", "こもれび大和田図書館", None, None)
    assert (sub, src) == ("library", "name")


def test_resolve_name_layer_can_be_switched_off():
    sub, src = PC.resolve_subcat(
        "service", "こもれび大和田図書館", None, None, use_name_rules=False
    )
    assert (sub, src) == (None, "none")


def test_resolve_drops_a_tag_subcat_that_contradicts_the_cat():
    """cat=attraction の POI に shop=hobby(topcat=shop)が付いていても採らない。"""
    sub, src = PC.resolve_subcat("attraction", "東京アニメセンター", None, {"shop": "hobby"})
    assert (sub, src) == (None, "none")


def test_resolve_returns_none_for_a_plain_shop():
    assert PC.resolve_subcat("shop", "どこかの店", None, {"shop": "clothes"}) == (None, "none")


# --- Overpass 文書の突き合わせ --------------------------------------------------------


def test_tag_index_uses_the_w7_poi_id_convention():
    doc = {
        "elements": [
            {"type": "node", "id": 123, "tags": {"leisure": "park"}},
            {"type": "way", "id": 456, "tags": {"shop": "books"}},
            {"type": "node", "id": 789},  # tags なしは載せない
        ]
    }
    idx = PC.tag_index(doc)
    assert idx == {"p_n123": {"leisure": "park"}, "p_w456": {"shop": "books"}}


def test_tag_index_merges_documents():
    a = {"elements": [{"type": "node", "id": 1, "tags": {"leisure": "park"}}]}
    b = {"elements": [{"type": "node", "id": 1, "tags": {"name": "宮下公園"}}]}
    assert PC.tag_index(a, b) == {"p_n1": {"leisure": "park", "name": "宮下公園"}}


def test_tag_index_accepts_an_empty_document():
    assert PC.tag_index({}) == {}


# --- 合成の POI 行 → 場所種別(この改訂の本体)-----------------------------------------


def test_a_park_poi_now_routes_to_place_park():
    """合成の POI 行: OSM タグ leisure=park → subcat=park → 場所語「公園」。"""
    sub, _src = PC.resolve_subcat("leisure", "宮下公園", None, {"leisure": "park"})
    assert sub == "park"
    assert _place_of("leisure", sub) == V.PLACE_PARK
    assert V.PLACE_WORDS[_place_of("leisure", sub)] == "公園"


def test_the_defect_itself_a_park_without_subcat_falls_into_place_leisure():
    """改訂前の姿(subcat 無しの公園)を固定する=回帰したら気づける。"""
    assert _place_of("leisure", None) == V.PLACE_LEISURE
    assert V.PLACE_WORDS[V.PLACE_LEISURE] == "娯楽施設"


def test_a_bookshop_poi_is_reachable_by_subcat_and_stays_a_shop():
    sub, src = PC.resolve_subcat("shop", "大盛堂書店", None, {"shop": "books"})
    assert (sub, src) == ("books", "osm_tag")
    assert _place_of("shop", sub) == V.PLACE_SHOP


def test_a_library_poi_is_reachable_by_subcat():
    sub, _src = PC.resolve_subcat("service", "こもれび大和田図書館", None, {"amenity": "library"})
    assert sub == "library"
    assert _place_of("service", sub) == V.PLACE_SHOP  # 場所語 12 語に「図書館」は無い


def test_the_added_subcats_are_exactly_these_twenty():
    """足した語を明示的に固定する(黙って語彙が増えない)。"""
    assert sorted(set(PC.SUBCAT_TOPCAT) - set(V8_FROZEN_SUBCATS)) == sorted(ADDED_SUBCATS)


def test_only_park_changes_the_place_word_among_the_new_subcats():
    """新しい subcat のうち、場所語を変えるのは park だけ(場所語 12 語は不変)。"""
    changed = {
        sub
        for sub in ADDED_SUBCATS
        if _place_of(PC.SUBCAT_TOPCAT[sub], sub) != _place_of(PC.SUBCAT_TOPCAT[sub], None)
    }
    assert changed == {"park"}


def test_place_park_is_not_in_the_opening_envelope():
    """公園に開店時刻は無い(営業エンベロープを掛けない)。"""
    assert V.PLACE_PARK not in W17.ENVELOPE_PLACES


# --- W6 の宣言 ------------------------------------------------------------------------


def test_w6_declares_the_raw_tag_inputs():
    names = {parts[-1] for parts in W6.INPUT_FILES}
    assert "poi_opening_hours_overpass_20260907.json" in names
    assert "street_features_overpass_20260907.json" in names


def test_w6_stage_version_moved():
    assert W6.STAGE_VERSION == "1.1.0"


def test_w6_park_gate_is_not_zero():
    """改訂前は PLACE_PARK へ写る POI が 0 件だった。期待値は 0 であってはならない。"""
    assert W6.EXPECTED_SUBCAT_PARK > 0
