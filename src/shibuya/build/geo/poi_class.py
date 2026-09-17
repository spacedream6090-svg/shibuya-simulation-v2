"""W6 POI の種別(cat)・サブカテゴリ(subcat)分類。**OSM タグが一次**。

背景(この段の欠陥・答申 `docs/research/v2-hobby-preference-research.md` §5-2/§5-3)
-------------------------------------------------------------------------------
v1 の地図生成器 ``scripts/build_map.py`` は ``leisure`` キーの値 park / garden /
playground / pitch / fitness_centre / sports_centre を**すべて cat=``leisure`` の 1 袋**へ
落とし、その 6 値に対応する subcat を 1 つも定義しなかった(v1 の
``SUBCAT_TAG_VALUES`` は 11 語=convenience/pachinko/karaoke/club/net_cafe/sauna/
arcade/worship/hospital/love_hotel/childcare のみ)。結果:

- 渋谷 bbox の公園 POI が ``cat=leisure, subcat=None`` になり、
  ``build/sched/w17_schedule.py`` の ``CAT_TO_PLACE["leisure"] = PLACE_LEISURE`` で
  **場所語「娯楽施設」**になる。場所語 12 語のうち「公園」(``PLACE_PARK``)へ写る POI が
  **0 件**=語彙の孤児。
- ジム・体育館も同じ袋に入り、劇場/ライブハウス/貸会議室(``hall`` 18)と
  美術館/ギャラリー(``attraction`` 12)は subcat 自体が無い。
- 書店・楽器店・図書館は種別でも subcat でも引けず、**POI 名の一致でしか**引けなかった。

本モジュールはその分類規則を v2 側へ持ち込み、**OSM の生タグを一次根拠**として
subcat 語彙を広げる。名前一致の規則は §「最後の手段」に**分けて**置き、W6 は
どの層が決めたか(``osm_tag`` / ``frozen`` / ``name``)を件数で報告する。

生タグの所在(v2 リポで実際に読めるもの)
-----------------------------------------
``data/realworld/osm/shibuya_osm_wide_v8.json`` の ``pois`` は
``id/name/cat/x/y/node/building/floor/subcat`` しか持たない(**生タグは落ちている**)。
生タグは別の 2 ファイルに残っている:

- ``poi_opening_hours_overpass_20260907.json`` … W7 が既に使う。店舗系 1,746 件に一致。
- ``street_features_overpass_20260907.json`` … ``leisure=park/garden/pitch/playground``
  ほかを含む。公園系に一致。

どちらも Overpass の ``out tags;`` 形式で、要素キー ``f"p_{type[0]}{id}"`` が
v8 の ``poi_id`` と同じ規約(``build/field/w7_planspec.py`` の既存の突き合わせと同一)。

expedient
---------
- ``NAME_SUBCAT_RULES``(名前一致)は **expedient**。生タグが 2 ファイルのどちらにも
  無い POI だけに、業種を表す一般名詞(「図書館」「公園」「体育館」…)で当てる。
  固有名・ブランド名は使わない。W6 の ``use_name_rules=False`` で切れる。
"""

from __future__ import annotations

from typing import Any, Final, Iterable, Mapping

__all__ = [
    "SUBCAT_TAG_KEYS",
    "SUBCAT_TAG_VALUES",
    "SUBCAT_TOPCAT",
    "SUBCAT_PATTERN_USE",
    "NAME_SUBCAT_RULES",
    "LANDMARK_NAME_KWS",
    "CATSUB_PAIRS",
    "poi_subcategory",
    "poi_category",
    "subcat_from_name",
    "resolve_subcat",
    "tag_index",
]

# ============================================================ 一次: OSM タグの規則

#: 業態を載せうる OSM のキー(この 4 つ以外は見ない=建物タグ等の誤爆を避ける)。
#: v1 ``scripts/build_map.py`` と同一。**キーを固定せず値の集合で照合する**のは、日本の
#: OSM が同じ業態を別キーに載せる揺れが大きいため(渋谷 bbox 実測: ラブホ
#: ``amenity=love_hotel`` 63 / ``tourism=love_hotel`` 0、ゲーセン
#: ``leisure=amusement_arcade`` 3 / ``amenity=amusement_arcade`` 0、カラオケ
#: ``amenity=karaoke_box`` 16 / ``leisure=karaoke`` 2、パチンコ ``amenity=gambling`` 8 /
#: ``shop=pachinko`` 0)。
SUBCAT_TAG_KEYS: Final[tuple[str, ...]] = ("amenity", "shop", "leisure", "tourism")

#: subcat 判定表(上から順に評価する決定論)。
#:
#: **前半 11 語は v1 と 1 バイト同じ**(凍結済み資産 ``w6_poi.parquet`` の subcat を
#: 生タグから再計算したとき、既存 255 件すべてが同値になることを W6 のゲートで確かめる)。
#: 後半は本改訂で足した 20 語。足す根拠はすべて「その値を持つ POI が渋谷 bbox に実在し、
#: 社会生活基本調査(R3)の趣味・娯楽/スポーツの**種目**の受け皿になる」こと
#: (→ ``SUBCAT_PATTERN_USE`` と ``docs/design/v2-hobby-affordance-map.md``)。
SUBCAT_TAG_VALUES: Final[tuple[tuple[str, frozenset[str]], ...]] = (
    # --- v1 から凍結(順序も値も変えない)---
    ("convenience", frozenset({"convenience"})),
    ("pachinko", frozenset({"pachinko", "gambling"})),
    ("karaoke", frozenset({"karaoke_box", "karaoke"})),
    ("club", frozenset({"nightclub"})),
    ("net_cafe", frozenset({"internet_cafe", "manga_cafe"})),
    ("sauna", frozenset({"sauna", "public_bath"})),
    ("arcade", frozenset({"amusement_arcade", "adult_gaming_centre"})),
    ("worship", frozenset({"place_of_worship"})),
    ("hospital", frozenset({"hospital"})),
    ("love_hotel", frozenset({"love_hotel"})),
    ("childcare", frozenset({"childcare", "kindergarten"})),
    # --- 本改訂(2026-09-17)で追加 ---
    ("park", frozenset({"park", "garden", "playground"})),
    ("gym", frozenset({"fitness_centre", "fitness_station", "gym"})),
    ("sports_centre", frozenset({"sports_centre", "sports_hall"})),
    ("theatre", frozenset({"theatre"})),
    ("music_venue", frozenset({"music_venue", "concert_hall"})),
    ("events_venue", frozenset({"events_venue", "conference_centre", "exhibition_centre"})),
    ("museum", frozenset({"museum"})),
    ("gallery", frozenset({"gallery"})),
    ("library", frozenset({"library"})),
    ("books", frozenset({"books"})),
    ("music_shop", frozenset({"music", "video"})),
    ("musical_instrument", frozenset({"musical_instrument"})),
    ("video_games", frozenset({"video_games"})),
    ("hobby", frozenset({"hobby", "anime", "games", "collector", "toys"})),
    ("art_supply", frozenset({"art", "craft", "frame", "pottery"})),
    ("stationery", frozenset({"stationery"})),
    ("photo", frozenset({"photo"})),
    ("florist", frozenset({"florist", "garden_centre"})),
    ("sports_shop", frozenset({"sports", "outdoor", "fishing"})),
    ("bicycle", frozenset({"bicycle"})),
)

#: subcat → top cat。**cat の語彙 13 種は 1 つも動かさない**(``build/lang/w14_signage.py``
#: の ``CAT_WORDS``・``build/sched/w17_schedule.py`` の ``CAT_TO_PLACE``・
#: ``build/field/w7_planspec.py`` の ``CATEGORY_DEFAULTS`` が cat に依存する)。
SUBCAT_TOPCAT: Final[dict[str, str]] = {
    # v1 から凍結
    "convenience": "shop",
    "pachinko": "shop",
    "karaoke": "nightlife",
    "club": "nightlife",
    "net_cafe": "nightlife",
    "sauna": "nightlife",
    "arcade": "leisure",
    "worship": "landmark",
    "hospital": "service",
    "love_hotel": "hotel",
    "childcare": "school",
    # 本改訂
    "park": "leisure",
    "gym": "leisure",
    "sports_centre": "leisure",
    "theatre": "hall",
    "music_venue": "hall",
    "events_venue": "hall",
    "museum": "attraction",
    "gallery": "attraction",
    "library": "service",
    "books": "shop",
    "music_shop": "shop",
    "musical_instrument": "shop",
    "video_games": "shop",
    "hobby": "shop",
    "art_supply": "shop",
    "stationery": "shop",
    "photo": "shop",
    "florist": "shop",
    "sports_shop": "shop",
    "bicycle": "shop",
}

#: **パターン台帳ゲート**(v2-methodology.md): 各 subcat を「どの現実パターン照合で使うか」
#: 1 行で書く。書けない語は足さない。種目名は社会生活基本調査(令和3年)生活行動編の
#: 種目(趣味・娯楽 35 / スポーツ 23 / 学習 7)。
SUBCAT_PATTERN_USE: Final[dict[str, str]] = {
    "convenience": "24h 営業の時刻分布(W7 営業エンベロープ)",
    "pachinko": "SSB 趣味「パチンコ」(東京 4.4%)の行き先",
    "karaoke": "SSB 趣味「カラオケ」(東京 16.1%)の行き先",
    "club": "深夜の滞留(特定遊興飲食店の営業窓)",
    "net_cafe": "SSB 趣味「マンガを読む」の屋外受け皿・深夜滞留",
    "sauna": "深夜の滞留(公衆浴場)",
    "arcade": "SSB 趣味「スマホ・家庭用ゲーム機などによるゲーム」の屋外受け皿",
    "worship": "初詣・参拝の時刻分布(landmark の中の宗教施設)",
    "hospital": "医療施設の場所語(PLACE_CLINIC)",
    "love_hotel": "宿泊施設の中の時間帯偏り",
    "childcare": "通園の時刻分布(学校の中の保育施設)",
    "park": "SSB スポーツ「ウォーキング・軽い体操」(東京 52.3%=最大種目)・"
    "「ジョギング・マラソン」の行き先。場所語 PLACE_PARK の唯一の供給源",
    "gym": "SSB スポーツ「器具を使ったトレーニング」(東京 15.0%)・「ヨガ」(8.4%)",
    "sports_centre": "SSB 趣味「スポーツ観覧・観戦」(東京 15.1%)・屋内競技",
    "theatre": "SSB 趣味「演芸・演劇・舞踊鑑賞」(東京 12.6%)",
    "music_venue": "SSB 趣味「ポピュラー音楽・歌謡曲鑑賞」(8.3%)・"
    "「クラシック音楽鑑賞」(6.2%)のコンサート会場",
    "events_venue": "趣味ではない hall(貸会議室・イベントスペース)を劇場から分ける",
    "museum": "SSB 趣味「美術鑑賞」(東京 17.8%)",
    "gallery": "SSB 趣味「美術鑑賞」(同上・画廊側)",
    "library": "SSB 趣味「趣味としての読書」(東京 43.4%)の無償の受け皿",
    "books": "SSB 趣味「趣味としての読書」(43.4%)・「マンガを読む」(43.2%)",
    "music_shop": "SSB 趣味「CD・スマホ等による音楽鑑賞」(東京 64.4%=最大種目)",
    "musical_instrument": "SSB 趣味「楽器の演奏」(東京 14.5%)の要る物",
    "video_games": "SSB 趣味「スマホ・家庭用ゲーム機などによるゲーム」(48.3%)の要る物",
    "hobby": "SSB 趣味「マンガを読む」・模型/玩具の要る物",
    "art_supply": "SSB 趣味「絵画・彫刻の制作」(3.4%)・「陶芸・工芸」(1.6%)の要る物",
    "stationery": "SSB 趣味「書道」(3.4%)・「詩・和歌・俳句・小説などの創作」(2.2%)の要る物",
    "photo": "SSB 趣味「写真の撮影・プリント」(東京 27.2%)の要る物",
    "florist": "SSB 趣味「華道」(1.3%)・「園芸・庭いじり・ガーデニング」(22.3%)の要る物",
    "sports_shop": "SSB スポーツ「登山・ハイキング」(9.8%)・「つり」(5.0%)の要る物",
    "bicycle": "SSB スポーツ「サイクリング」(東京 14.4%)の要る物",
}

#: 待ち合わせ名所に名前で寄せる語(v1 ``LANDMARK_NAME_KWS`` と同一・渋谷固有)。
LANDMARK_NAME_KWS: Final[tuple[str, ...]] = ("ハチ公", "モヤイ", "忠犬")

#: 実在しうる (cat, subcat) 対の閉包。``(cat, None)`` は cat 13 種ぶん別に数える。
#: W7 ``CATEGORY_DEFAULTS`` はこの閉包を必ず覆う(``tests/build_field`` で検査)。
CATSUB_PAIRS: Final[tuple[tuple[str, str], ...]] = tuple(
    sorted((SUBCAT_TOPCAT[s], s) for s in SUBCAT_TOPCAT)
)


def poi_subcategory(tags: Mapping[str, Any]) -> str | None:
    """OSM 生タグ → subcat(閉じた語彙)。判らなければ ``None``。

    **名前を見ない純関数**。判定順は :data:`SUBCAT_TAG_VALUES` の並び=決定論。
    """
    values = {tags.get(k) for k in SUBCAT_TAG_KEYS}
    values.discard(None)
    if not values:
        return None
    vals = {str(v) for v in values}
    for sub, candidates in SUBCAT_TAG_VALUES:
        if vals & candidates:
            return sub
    return None


def poi_category(
    tags: Mapping[str, Any], landmark_name_kws: tuple[str, ...] = LANDMARK_NAME_KWS
) -> str | None:
    """OSM 生タグ → cat(13 種)。判らなければ ``None``。

    v1 ``scripts/build_map.py`` の規則をそのまま移した(cat の語彙は動かさない)。
    v1 の判定で決まらなかったときだけ subcat 由来の top cat へ落とす。

    Note:
        W6 は**この関数を凍結済み POI に掛け直さない**(cat は v8 の値のまま)。
        ここに置くのは、次に OSM を取り直すときの一次規則を v2 側に持つため、および
        「``leisure=park`` が cat=leisure になる」という欠陥の出所をテストで固定するため。
    """
    name = str(tags.get("name:ja") or tags.get("name") or "")
    if landmark_name_kws and any(kw in name for kw in landmark_name_kws):
        return "landmark"
    amenity = str(tags.get("amenity", ""))
    if amenity in ("restaurant", "cafe", "fast_food", "food_court", "ice_cream"):
        return "food"
    if amenity in ("bar", "pub", "nightclub", "karaoke_box", "izakaya"):
        return "nightlife"
    if amenity == "cinema":
        return "cinema"
    if (
        amenity in ("theatre", "events_venue", "conference_centre")
        or tags.get("leisure") == "stadium"
    ):
        return "hall"
    if amenity in ("bank", "pharmacy", "clinic", "dentist", "post_office", "police", "library"):
        return "service"
    if amenity in ("school", "university", "college", "kindergarten") or tags.get("building") in (
        "school",
        "university",
    ):
        return "school"
    if "shop" in tags:
        return "shop"
    if "office" in tags:
        return "office"
    if tags.get("tourism") in ("hotel", "hostel", "guest_house"):
        return "hotel"
    if (
        tags.get("tourism") in ("attraction", "artwork")
        or tags.get("man_made") == "statue"
        or tags.get("historic") in ("memorial", "monument")
    ):
        return "landmark"
    if tags.get("tourism") in ("museum", "gallery"):
        return "attraction"
    if tags.get("leisure") in (
        "park",
        "garden",
        "playground",
        "pitch",
        "fitness_centre",
        "sports_centre",
    ):
        return "leisure"
    sub = poi_subcategory(tags)
    if sub is not None:
        return SUBCAT_TOPCAT[sub]
    return None


# ================================================== 最後の手段: POI 名の一致(expedient)

#: **expedient**。生タグがリポのどのファイルにも残っていない POI にだけ掛ける。
#: 語は「業種を表す一般名詞」に限る(固有名・ブランド名・店名は書かない)。
#: 上から順に評価し、**その subcat の top cat が POI の cat と一致するときだけ**当てる
#: (=名前が種別をまたいで当たることは無い。例:「代々木公園陸上競技場」は cat=hall
#: なので「公園」では当たらない)。
NAME_SUBCAT_RULES: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("library", ("図書館",)),
    ("museum", ("美術館", "博物館", "史料館", "資料館", "記念館")),
    ("gallery", ("ギャラリー", "Gallery", "アトリエ")),
    ("theatre", ("劇場", "シアター", "Theater", "Theatre", "演芸場")),
    ("music_venue", ("ライブハウス", "音楽堂", "公会堂", "能楽堂")),
    ("events_venue", ("会議室", "カンファレンス", "イベントホール")),
    ("sports_centre", ("体育館", "競技場")),
    (
        "gym",
        ("ジム", "GYM", "Gym", "フィットネス", "トレーニング", "スポーツクラブ", "スポーツセンター"),
    ),
    ("park", ("公園", "児童遊園", "緑地", "庭園")),
)


def subcat_from_name(name: str, cat: str) -> str | None:
    """**expedient**: POI 名 → subcat。``cat`` と矛盾する語は当てない。"""
    text = str(name)
    if not text:
        return None
    for sub, keywords in NAME_SUBCAT_RULES:
        if SUBCAT_TOPCAT[sub] != cat:
            continue
        if any(kw in text for kw in keywords):
            return sub
    return None


# ================================================================== 解決(3 層の合成)

#: 解決の出所。``osm_tag`` 一次 → ``frozen``(v8 が持っていた値) → ``name``(expedient)。
SUBCAT_SOURCES: Final[tuple[str, ...]] = ("osm_tag", "frozen", "name", "none")


def resolve_subcat(
    cat: str,
    name: str,
    frozen_subcat: str | None,
    tags: Mapping[str, Any] | None,
    *,
    use_name_rules: bool = True,
) -> tuple[str | None, str]:
    """1 件の POI の subcat を決める → ``(subcat, source)``。

    Args:
        cat: v8 が持つ cat(**変えない**)。
        name: POI 名(``use_name_rules`` が真のときだけ読む)。
        frozen_subcat: v8 が持つ subcat(生タグが無いときの控え)。
        tags: この POI の OSM 生タグ(無ければ ``None``)。
        use_name_rules: 名前一致の層(expedient)を使うか。切ると ``name`` は 0 件になる。

    Note:
        生タグから出た subcat が ``SUBCAT_TOPCAT[subcat] != cat`` のときは**採らない**
        (対の閉包を壊さないため)。この件数は W6 のゲートで 0 を要求する。
    """
    if tags:
        sub = poi_subcategory(tags)
        if sub is not None and SUBCAT_TOPCAT[sub] == cat:
            return sub, "osm_tag"
    if frozen_subcat:
        return str(frozen_subcat), "frozen"
    if use_name_rules:
        sub = subcat_from_name(name, cat)
        if sub is not None:
            return sub, "name"
    return None, "none"


def tag_index(*documents: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    """Overpass の ``out tags;`` 文書 → ``poi_id`` → 生タグ。

    キーの規約は ``build/field/w7_planspec.py`` と同一の ``f"p_{type[0]}{id}"``
    (``p_n123`` / ``p_w456``)。同じ要素が複数文書に出たらタグを重ねる。
    """
    index: dict[str, dict[str, str]] = {}
    for doc in documents:
        elements: Iterable[Mapping[str, Any]] = doc.get("elements") or ()
        for el in elements:
            tags = el.get("tags")
            if not tags:
                continue
            key = f"p_{str(el['type'])[0]}{el['id']}"
            index.setdefault(key, {}).update({k: str(v) for k, v in tags.items()})
    return index
