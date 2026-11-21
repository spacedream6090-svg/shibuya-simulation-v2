"""foundation.vocab.place_words — 割る段で ``world/assets.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``world/model/assets.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "CATEGORY_WORDS", "GENERIC_WORDS", "BUYABLE_CATS",
]


#: 合成 POI のカテゴリと価格[円](expedient)。
SYNTHETIC_POI_CATS: Final[tuple[str, ...]] = ("コンビニ", "飲食", "物販")


#: **対応表 v0(第286・宣言)**(expedient・親決定 Q11=起草を v0 として採用): 対象欄の語 →
#: W6 の (cat の集合, subcat の集合)。POI が「cat が集合に入る **または** subcat が集合に入る」
#: とき一致。長い語から照合する。59 語。
CATEGORY_WORDS: Final[tuple[tuple[str, frozenset[str], frozenset[str]], ...]] = tuple(
    (w, frozenset(c), frozenset(s))
    for w, c, s in (
        # ---- 飲食(W14 CAT_WORDS food=「飲食店」・nightlife=「夜間営業の飲食店」)----
        ("夜間営業の飲食店", ("nightlife",), ()),
        ("飲食店", ("food",), ()),
        ("レストラン", ("food",), ()),
        ("食堂", ("food",), ()),
        ("飲食", ("food",), ()),
        ("ラーメン", ("food",), ()),
        ("カフェ", ("food",), ()),
        ("喫茶店", ("food",), ()),
        ("喫茶", ("food",), ()),
        ("居酒屋", ("nightlife",), ()),
        ("バー", ("nightlife",), ()),
        # ---- 食品・飲み物(買う物)= 飲食店+コンビニ ----
        ("食品カテゴリ", ("food",), ("convenience",)),
        ("食料品", ("food",), ("convenience",)),
        ("食品店", ("food",), ("convenience",)),
        ("食品", ("food",), ("convenience",)),
        ("食料", ("food",), ("convenience",)),
        ("食べ物", ("food",), ("convenience",)),
        ("食事", ("food",), ()),
        ("飲み物", ("food",), ("convenience",)),
        ("ドリンク", ("food",), ("convenience",)),
        ("飲料", ("food",), ("convenience",)),
        ("コーヒー", ("food",), ("convenience",)),
        # ---- 物販(W14 shop=「物販店」・convenience=「コンビニエンスストア」)----
        ("コンビニエンスストア", (), ("convenience",)),
        ("コンビニ", (), ("convenience",)),
        ("物販店", ("shop",), ()),
        ("物販", ("shop",), ()),
        ("スーパー", ("shop",), ()),
        ("書店", (), ("books",)),
        ("本屋", (), ("books",)),
        ("楽器店", (), ("musical_instrument",)),
        ("文房具", (), ("stationery",)),
        ("花屋", (), ("florist",)),
        ("自転車", (), ("bicycle",)),
        ("スポーツ用品", (), ("sports_shop",)),
        # ---- サービス(W14 service=「サービス店」・hospital=「病院」)----
        ("サービス店", ("service",), ()),
        ("薬局", ("service", "shop"), ()),
        ("ドラッグストア", ("service", "shop"), ()),
        ("病院", (), ("hospital",)),
        ("図書館", (), ("library",)),
        # ---- 娯楽・その他(W14 の業種語)----
        ("カラオケ店", (), ("karaoke",)),
        ("カラオケ", (), ("karaoke",)),
        ("ナイトクラブ", (), ("club",)),
        ("ゲームセンター", (), ("arcade",)),
        ("ぱちんこ店", (), ("pachinko",)),
        ("パチンコ", (), ("pachinko",)),
        ("サウナ", (), ("sauna",)),
        ("インターネットカフェ", (), ("net_cafe",)),
        ("ネットカフェ", (), ("net_cafe",)),
        ("映画館", ("cinema",), ()),
        ("宿泊施設", ("hotel",), ()),
        ("ホテル", ("hotel",), ()),
        ("娯楽施設", ("leisure",), ()),
        ("観光施設", ("attraction",), ()),
        ("集会施設", ("hall",), ()),
        ("事務所", ("office",), ()),
        ("公園", (), ("park",)),
        ("劇場", (), ("theatre",)),
        ("美術館", (), ("museum",)),
        ("博物館", (), ("museum",)),
    )
)


#: 総称語(対応表 v0・親決定 Q11): 「店」「店舗」「ショップ」「お店」は業態を指さない=**なし**として読む
#: (POI 名の「入力 ⊂ 名」に当てない=「〇〇ショップ」の名指しにしない)。
GENERIC_WORDS: Final[frozenset[str]] = frozenset({"店", "店舗", "ショップ", "お店"})

#: **購入/並ぶの候補になる cat**(店舗系・親決定 Q12=D-114 (a) の「意図に合う」・宣言)。W6 の cat 実測:
#: food 823・shop 721・nightlife 259・service 114・leisure 42・cinema 7・attraction 12。
#: 除く: office・hotel・school・landmark・hall・education。
BUYABLE_CATS: Final[frozenset[str]] = frozenset(
    {"food", "shop", "nightlife", "service", "leisure", "cinema", "attraction"}
)
#: 合成世界(``world.assets.SYNTHETIC_POI_CATS``=コンビニ/飲食/物販)の POI は**作りからして全部店**
#: なので購入/並ぶの候補に入れる(実資産の cat 名とは重ならない=実世界の挙動には効かない)。
SYNTHETIC_BUYABLE_CATS: Final[frozenset[str]] = frozenset(SYNTHETIC_POI_CATS)
