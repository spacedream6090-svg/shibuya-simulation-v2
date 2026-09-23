"""W7 営業時間・価格帯(PlanSpec)(§1 W7・D-W8)。

3段構成(D-W8):
  ①**法規上限をハードキャップ**(mechanism・F13 の条文=親一次確認済み)。D-W8 の
     「営業不可時間」欄を毎日繰り返す窓として区間から引くので、閉店側だけでなく
     **開店側も切り上がる**(ぱちんこ 09:00-23:30 → 10:00-23:00)。
  ②カテゴリ既定値(cat×subcat・expedient)。
  ③OSM ``opening_hours`` 実取得分で上書き(mechanism・Overpass attic 2026-09-07・565件)。
     ③b **チェーン既定**=同一 brand で ③の実値が2件以上あるとき、その最頻文面を
     同 brand の未取得 POI へ写す(D-W8 の段(2)を **手入力ではなく OSM 実値の伝播**で実装。
     公式サイトの手入力表は未取得=空表 ``CHAIN_MANUAL_HOURS``)。

出力: ``w7_plan_spec.parquet``(世界過程設計書 §2 の PlanSpec 型の列を持つ)。

expedient(全文は ``EXPEDIENTS``=段階ヘッダに載る台帳。ここは要旨)
- カテゴリ既定営業時間・価格帯(cat×subcat 44行。うち 20 行は W6 subcat 改訂 2026-09-17 で現れた対で、親 cat の行をそのまま継ぐ=営業窓も価格帯も動かさない)。
- 改訂権者=``store_manager`` 固定(店主エージェントが開け閉めする=世界過程設計書 §1-1)。
- 違反可能性=法規上限のある業態は ``enforced``・それ以外の自主営業時間は ``unenforced``(軸4)。
- ラブホテル(subcat=love_hotel)は旅館業法営業か店舗型性風俗特殊営業かが OSM タグから
  判定できないため**上限なし**として扱う(判定不能を宣言)。
- 接待飲食等(1-3号)は OSM タグに現れないため nightlife 既定は深夜酒類提供(上限なし)。
- **地域条件なしの一律適用**(D-72 ①・2026-09-16 の法規一次確認 §3 ①)。
- **特別日なし**(D-72 ⑦)/青少年条例16条1項の**一・二号の未写像**(⑧)/D-W8 表の
  **条例8条・6条が未実装**(④)。

法規の記録修正(2026-09-17・D-72 (a)・**数値は動かさない**)
    答申 ``docs/research/v2-w7-law-primary-check-research.md``(等級A・親一次確認)の
    §3 ②(citation の条ずれ)を直し、①⑦⑧④ を ``EXPEDIENTS`` へ登録した。
    ③(``minor_entry_limit`` の violability)は**保留**——``violability`` は
    ``w7_plan_spec.parquet`` の**生成列**で、直すと 18 行が unenforced→enforced に動く
    (=W7 の再構築が要る)。保留の事実そのものを ``EXPEDIENTS`` に載せた。
"""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any, NamedTuple, Sequence

import numpy as np
import pyarrow as pa

from . import common as C

STAGE = "W7"
STAGE_VERSION = "1.0.0"

INPUT_FILES: tuple[tuple[str, ...], ...] = (
    ("realworld", "osm", "poi_opening_hours_overpass_20260907.json"),
)

#: OSM 抽出日(Overpass attic・§0-2 版の凍結)。
OSM_OPENING_HOURS_ATTIC = "2026-09-07"

#: 仕様書 §1 W6 / D-W7 の POI 数。PlanSpec は POI と1対1なのでこの数と一致する
#: (W6 の POI 表が変わったら気づけるように定数で置く=自明ゲートにしない)。
EXPECTED_POI_ROWS = 2337

# --- ① 法規上限表(D-W8・F13・親一次確認済み)-------------------------------------------
# D-W8 の表は「営業不可時間」と「閉店上限」の2欄を持つ。**両方を適用する**:
#   closed_windows_min = 営業不可時間を「開店日0時からの分」で表した窓の並び(end>start・
#   日をまたぐ窓は end>1440)。窓は**毎日**繰り返す(23:00-翌10:00 は当日の 0:00-10:00 でもある)。
#   区間 (open, close) はこの窓との差集合を取る=閉店側だけでなく**開店側も切り上がる**。
# close_cap_min = D-W8 の「閉店上限」欄(=窓から導かれる閉店の上限・診断と params 用の再掲)。
#   None = 閉店上限なし(24h 可)。closed_window は語彙・診断用の文字列。
LAW_CAPS: dict[str, dict[str, Any]] = {
    "settai_inshoku": {
        "label": "接待飲食等営業(1-3号)",
        # 条ずれの修正(D-72 ②・答申 §3 ②): 規則6条2項は**時**(午前1時)であって地域ではない。
        # 地域の根拠は 条例4条の2第2項(商業地域のうち規則で定める地域)+規則5条(公安委員会告示)。
        "citation": (
            "風営法13条1項ただし書+東京都風俗営業等の規制及び業務の適正化等に関する法律"
            "施行条例4条の3第2号+同施行規則6条2項(延長後の時=午前1時)"
            "/地域=同条例4条の2第2項+同施行規則5条+公安委員会告示"
            "(営業延長許容地域=渋谷区26町丁)"
        ),
        "closed_window": "1:00-6:00",
        "closed_windows_min": ((60, 360),),
        "close_cap_min": 1500,
    },
    "pachinko_mahjong": {
        "label": "ぱちんこ・麻雀(4号)",
        "citation": "東京都風俗営業等の規制及び業務の適正化等に関する法律施行条例5条(都内全域)",
        "closed_window": "23:00-翌10:00",
        "closed_windows_min": ((1380, 2040),),
        "close_cap_min": 1380,
    },
    "game_center": {
        "label": "ゲームセンター(5号)",
        # 同上(D-72 ②)。条例5条 表は**地域別3行**で、ここで採っているのは
        # 「営業延長許容地域」の行(1:00-10:00)だけ=地域条件は EXPEDIENTS に登録(①)。
        "citation": (
            "東京都風俗営業等の規制及び業務の適正化等に関する法律施行条例5条 表"
            "(営業延長許容地域の行)+同施行規則6条2項(時=午前1時)"
            "/地域=同条例4条の2第2項+同施行規則5条+公安委員会告示"
        ),
        "closed_window": "1:00-10:00",
        "closed_windows_min": ((60, 600),),
        "close_cap_min": 1500,
    },
    "tokutei_yukyo": {
        "label": "特定遊興飲食店(クラブ・ライブハウス)",
        "citation": "風営法31条の23(13条1項の準用除外)+東京都同施行条例13条",
        "closed_window": "5:00-6:00",
        "closed_windows_min": ((300, 360),),
        "close_cap_min": 1740,
    },
    "shinya_shurui": {
        "label": "深夜酒類提供飲食店(バー・居酒屋)",
        "citation": "風営法33条(届出)+東京都同施行条例15条(禁止は住居集合地域のみ・渋谷駅周辺は商業地域)",
        "closed_window": "なし",
        "closed_windows_min": (),
        "close_cap_min": None,
    },
    "ippan_inshoku": {
        "label": "一般飲食店",
        "citation": "風営法32条(構造設備のみ)",
        "closed_window": "なし",
        "closed_windows_min": (),
        "close_cap_min": None,
    },
    "tenpo_seifuzoku": {
        "label": "店舗型性風俗特殊営業",
        "citation": "東京都風俗営業等の規制及び業務の適正化等に関する法律施行条例11条",
        "closed_window": "0:00-6:00",
        "closed_windows_min": ((0, 360),),
        "close_cap_min": 1440,
    },
    "minor_entry_limit": {
        "label": "18歳未満の立入制限(興行場・カラオケボックス・ネットカフェ等)",
        "citation": "東京都青少年の健全な育成に関する条例16条(23:00-4:00 立入禁止=営業時間の上限ではない)",
        "closed_window": "23:00-4:00(立入)",
        # 立入制限であって営業時間の規制ではない(D-W8 の閉店上限欄は「—」)=窓を当てない。
        "closed_windows_min": (),
        "close_cap_min": None,
    },
    "none": {
        "label": "上限なし(法規の営業時間規制に該当しない業態)",
        "citation": "",
        "closed_window": "なし",
        "closed_windows_min": (),
        "close_cap_min": None,
    },
}

#: (cat, subcat) → 法規上限表のキー。OSM タグでの絞り込みは ``OSM_TAG_LAW_OVERRIDE`` が優先。
LAW_KEY_BY_CATSUB: dict[tuple[str, str | None], str] = {
    ("shop", "pachinko"): "pachinko_mahjong",
    ("leisure", "arcade"): "game_center",
    ("nightlife", "club"): "tokutei_yukyo",
    ("nightlife", None): "shinya_shurui",
    ("nightlife", "karaoke"): "minor_entry_limit",
    ("nightlife", "net_cafe"): "minor_entry_limit",
    ("nightlife", "sauna"): "none",
    ("food", None): "ippan_inshoku",
}

#: OSM タグからの業態の絞り込み(タグが明示している場合のみ・上から順に評価)。
OSM_TAG_LAW_OVERRIDE: tuple[tuple[str, str, str], ...] = (
    ("amenity", "nightclub", "tokutei_yukyo"),
    ("amenity", "casino", "pachinko_mahjong"),
    ("amenity", "gambling", "pachinko_mahjong"),
    ("leisure", "adult_gaming_centre", "pachinko_mahjong"),
    ("leisure", "amusement_arcade", "game_center"),
    ("amenity", "internet_cafe", "minor_entry_limit"),
    ("amenity", "bar", "shinya_shurui"),
    ("amenity", "pub", "shinya_shurui"),
    ("amenity", "restaurant", "ippan_inshoku"),
    ("amenity", "cafe", "ippan_inshoku"),
    ("amenity", "fast_food", "ippan_inshoku"),
)

# --- ①b expedient 台帳(段階ヘッダの ``expedients`` 欄=方法論「全cap/近似にタグ」)-------
# 記録だけの表(生成値には触れない)。法規側の 4 行は 2026-09-17(D-72 (a))に足したもので、
# 出典は ``docs/research/v2-w7-law-primary-check-research.md``(等級A・親が条文を一次確認)。
EXPEDIENTS: tuple[str, ...] = (
    "カテゴリ既定営業時間・価格帯(cat×subcat 44行・感度=既定±2h対照)",
    "18歳未満の立入制限(青少年条例16条)は営業時間の窓として当てない(D-W8 の閉店上限欄=—)",
    "改訂権者=store_manager 固定",
    "違反可能性の割当(法規上限のある業態=enforced・それ以外=unenforced)",
    "love_hotel は旅館業/店舗型性風俗の判定不能→上限なし",
    "接待飲食等(1-3号)は OSM タグに現れず nightlife 既定=深夜酒類提供(上限なし)",
    "PH(祝日)規則は 7日週モデルに写像せず無視",
    "チェーン既定=OSM 実値の brand 内最頻伝播(公式表の手入力は未取得=空表)",
    # ---- D-72 (a) 2026-09-17 追加(法規一次確認 §3 の不一致) ----
    "**地域条件なしの一律適用**(D-72 ①): 1-3号・5号・深夜酒類提供の窓は"
    "営業延長許容地域/住居集合地域の別で決まる(条例4条の2第2項・5条 表・15条)が、"
    "law_key_for は cat・subcat・OSM タグだけで決めて全 POI に同じ窓を当てる。"
    "告示26町丁の外の54町丁では 1-3号・5号の上限は 0:00(60分厳しい)・"
    "住居集合地域では 23:00・深夜酒類は 0:00-6:00 禁止。"
    "許容地域の外縁は規則5条ただし書の 20m 緩衝帯で削られる(幹線道路50mは除外しない)。"
    "座標・町丁・用途地域を見ないので世界の営業時間が告示外で 60〜120 分ずれる",
    "**特別日なし**(D-72 ⑦): 条例4条の2第1項・4条の3第1号・規則6条1項の"
    "「習俗的行事等の特別の事情のある日」の延長(許容地域外でも 1:00 または告示の時)を"
    "実装していない。スナップショット日が特別日でなければ無害",
    "**青少年条例16条1項の一・二号が未写像**(D-72 ⑧): minor_entry_limit は"
    "karaoke/net_cafe/internet_cafe(三・四号)だけに当たっており、"
    "一 興行場(映画館等)・二 ボウリング/スケート/水泳施設が対象に入っていない"
    "(写像の追加は W7 の再構築が要るので本修正では行わない)",
    "**D-W8 表にあってコードに無い 2 行=未実装**(D-72 ④): 条例8条"
    "(16歳未満のゲームセンター 18:00-22:00 保護者同伴)・条例6条(騒音 dB)",
    "**violability の修正は保留**(D-72 ③): minor_entry_limit は罰則つき"
    "(青少年条例26条六号・30万円以下の罰金)なので enforced 相当だが、"
    "窓が空のため現在は unenforced と記録される。violability は生成列で、"
    "直すと 18 行が動く=W7 の再構築が要るため親判断待ち",
)

# --- ② カテゴリ既定表(expedient・cat×subcat)---------------------------------------------
# open/close = 0時からの分(close>1440 は日跨ぎ)。closed_days = 定休曜日(0=月 .. 6=日)。
# price_tier ∈ {free, low, mid, high}(経済台帳 wage_tier と整合させる語彙)。
CATEGORY_DEFAULTS: dict[tuple[str, str | None], dict[str, Any]] = {
    ("attraction", None): {"open": 600, "close": 1200, "closed_days": (), "price_tier": "mid"},
    ("cinema", None): {"open": 540, "close": 1440, "closed_days": (), "price_tier": "mid"},
    ("education", None): {"open": 540, "close": 1260, "closed_days": (5, 6), "price_tier": "mid"},
    ("food", None): {"open": 660, "close": 1380, "closed_days": (), "price_tier": "mid"},
    ("hall", None): {"open": 600, "close": 1320, "closed_days": (), "price_tier": "high"},
    ("hotel", None): {"open": 0, "close": 1440, "closed_days": (), "price_tier": "high"},
    ("hotel", "love_hotel"): {"open": 0, "close": 1440, "closed_days": (), "price_tier": "mid"},
    ("landmark", None): {"open": 0, "close": 1440, "closed_days": (), "price_tier": "free"},
    ("landmark", "worship"): {"open": 360, "close": 1020, "closed_days": (), "price_tier": "free"},
    ("leisure", None): {"open": 600, "close": 1320, "closed_days": (), "price_tier": "mid"},
    ("leisure", "arcade"): {"open": 600, "close": 1440, "closed_days": (), "price_tier": "low"},
    ("nightlife", None): {"open": 1020, "close": 1740, "closed_days": (), "price_tier": "mid"},
    ("nightlife", "club"): {"open": 1320, "close": 1800, "closed_days": (), "price_tier": "high"},
    ("nightlife", "karaoke"): {"open": 660, "close": 1740, "closed_days": (), "price_tier": "low"},
    ("nightlife", "net_cafe"): {"open": 0, "close": 1440, "closed_days": (), "price_tier": "low"},
    ("nightlife", "sauna"): {"open": 660, "close": 1740, "closed_days": (), "price_tier": "mid"},
    ("office", None): {"open": 540, "close": 1080, "closed_days": (5, 6), "price_tier": "free"},
    ("school", None): {"open": 480, "close": 1020, "closed_days": (5, 6), "price_tier": "free"},
    ("school", "childcare"): {"open": 450, "close": 1140, "closed_days": (6,), "price_tier": "mid"},
    ("service", None): {"open": 540, "close": 1080, "closed_days": (5, 6), "price_tier": "mid"},
    ("service", "hospital"): {"open": 0, "close": 1440, "closed_days": (), "price_tier": "high"},
    ("shop", None): {"open": 660, "close": 1260, "closed_days": (), "price_tier": "mid"},
    ("shop", "convenience"): {"open": 0, "close": 1440, "closed_days": (), "price_tier": "low"},
    ("shop", "pachinko"): {"open": 600, "close": 1380, "closed_days": (), "price_tier": "mid"},
    # --- W6 の subcat 改訂(2026-09-17・geo/poi_class.py)で現れる対 ---
    # **親 cat の行をそのまま継ぐ**(= 既定の営業窓・価格帯は 1 件も動かない
    # → w7_plan_spec.parquet はバイト不変)。公園を 0-1440/free に、図書館を
    # 公立図書館の窓にするなどの**実態に合わせた改訂は別の判断**(親決定待ち)。
    ("attraction", "gallery"): {"open": 600, "close": 1200, "closed_days": (), "price_tier": "mid"},
    ("attraction", "museum"): {"open": 600, "close": 1200, "closed_days": (), "price_tier": "mid"},
    ("hall", "events_venue"): {"open": 600, "close": 1320, "closed_days": (), "price_tier": "high"},
    ("hall", "music_venue"): {"open": 600, "close": 1320, "closed_days": (), "price_tier": "high"},
    ("hall", "theatre"): {"open": 600, "close": 1320, "closed_days": (), "price_tier": "high"},
    ("leisure", "gym"): {"open": 600, "close": 1320, "closed_days": (), "price_tier": "mid"},
    ("leisure", "park"): {"open": 600, "close": 1320, "closed_days": (), "price_tier": "mid"},
    ("leisure", "sports_centre"): {
        "open": 600,
        "close": 1320,
        "closed_days": (),
        "price_tier": "mid",
    },
    ("service", "library"): {"open": 540, "close": 1080, "closed_days": (5, 6), "price_tier": "mid"},
    ("shop", "art_supply"): {"open": 660, "close": 1260, "closed_days": (), "price_tier": "mid"},
    ("shop", "bicycle"): {"open": 660, "close": 1260, "closed_days": (), "price_tier": "mid"},
    ("shop", "books"): {"open": 660, "close": 1260, "closed_days": (), "price_tier": "mid"},
    ("shop", "florist"): {"open": 660, "close": 1260, "closed_days": (), "price_tier": "mid"},
    ("shop", "hobby"): {"open": 660, "close": 1260, "closed_days": (), "price_tier": "mid"},
    ("shop", "music_shop"): {"open": 660, "close": 1260, "closed_days": (), "price_tier": "mid"},
    ("shop", "musical_instrument"): {
        "open": 660,
        "close": 1260,
        "closed_days": (),
        "price_tier": "mid",
    },
    ("shop", "photo"): {"open": 660, "close": 1260, "closed_days": (), "price_tier": "mid"},
    ("shop", "sports_shop"): {"open": 660, "close": 1260, "closed_days": (), "price_tier": "mid"},
    ("shop", "stationery"): {"open": 660, "close": 1260, "closed_days": (), "price_tier": "mid"},
    ("shop", "video_games"): {"open": 660, "close": 1260, "closed_days": (), "price_tier": "mid"},
}

#: D-W8 段(2)「チェーン公式営業時間表の手入力」。**未取得=空表**(法務レーン確認前)。
CHAIN_MANUAL_HOURS: dict[str, list[list[tuple[int, int]]]] = {}

WEEK = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
_DAY_IDX = {d: i for i, d in enumerate(WEEK)}
_TIME_RANGE = re.compile(r"^(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})$")
_DAY_TOKEN = re.compile(r"^(Mo|Tu|We|Th|Fr|Sa|Su)(?:-(Mo|Tu|We|Th|Fr|Sa|Su))?$")
#: 規則の先頭にある曜日セレクタ(``Mo-Fr``・``Sa, Su``・``Su,PH``)と本体の分割。
_RULE = re.compile(
    r"^(?P<days>(?:(?:Mo|Tu|We|Th|Fr|Sa|Su|PH|SH)"
    r"(?:\s*-\s*(?:Mo|Tu|We|Th|Fr|Sa|Su))?\s*,?\s*)+)?(?P<body>.*)$"
)
#: ``Mo-Fr 11:00-22:00, Sa 11:00-21:00`` のように **カンマで規則を並べた**書き方の検出。
_STARTS_DAY_TIME = re.compile(r"^(Mo|Tu|We|Th|Fr|Sa|Su)(?:-(Mo|Tu|We|Th|Fr|Sa|Su))?\s+\d{1,2}:\d{2}")
_HAS_TIME = re.compile(r"\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}")


def _split_comma_rules(rule: str) -> list[str]:
    """``;`` 区切りの1規則を、カンマで並べられた複数規則へ割る。

    「直前までに時刻範囲があり、かつ次の断片が『曜日 + 時刻』で始まる」ときだけ割る。
    ``Mo-Th, Su 17:00-02:00``(曜日の列挙)は割らない。
    """
    frags = rule.split(",")
    groups: list[list[str]] = [[frags[0]]]
    for frag in frags[1:]:
        current = ",".join(groups[-1])
        if _STARTS_DAY_TIME.match(frag.strip()) and _HAS_TIME.search(current):
            groups.append([frag])
        else:
            groups[-1].append(frag)
    return [",".join(g) for g in groups]


class OpeningHoursParseError(ValueError):
    """OSM ``opening_hours`` の対応部分集合の外。"""


def _parse_days(selector: str) -> list[int]:
    """``Mo-Fr``・``Sa,Su,PH``・``Mo,We`` → 曜日番号列。PH(祝日)は 7日週モデルに無いので無視。

    PH/SH だけのセレクタは**空リスト**を返す(呼び側でその規則ごと無視する)。
    """
    days: list[int] = []
    for tok in selector.split(","):
        tok = tok.strip()
        if not tok:
            continue
        if tok in ("PH", "SH"):  # 祝日・学校休業日は週モデル外(宣言して落とす)
            continue
        m = _DAY_TOKEN.match(tok.replace(" ", ""))
        if not m:
            raise OpeningHoursParseError(f"曜日セレクタ非対応: {tok!r}")
        a = _DAY_IDX[m.group(1)]
        b = _DAY_IDX[m.group(2)] if m.group(2) else a
        i = a
        while True:
            days.append(i)
            if i == b:
                break
            i = (i + 1) % 7
    return sorted(set(days))


def _parse_time_ranges(text: str) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for part in text.split(","):
        part = part.strip()
        m = _TIME_RANGE.match(part)
        if not m:
            raise OpeningHoursParseError(f"時刻範囲非対応: {part!r}")
        oh, om, ch, cm = (int(g) for g in m.groups())
        if om > 59 or cm > 59 or oh > 48 or ch > 48:
            raise OpeningHoursParseError(f"時刻の値域外: {part!r}")
        o = oh * 60 + om
        c = ch * 60 + cm
        if c <= o:  # 日跨ぎ(11:30-02:00)
            c += 1440
        out.append((o, c))
    return sorted(out)


def parse_opening_hours(value: str) -> list[list[tuple[int, int]]]:
    """OSM ``opening_hours`` の**共通部分集合**を 7×区間リストへ。

    対応: ``24/7``・``Mo-Su 10:00-22:00``・曜日範囲/列挙・``;`` 区切りの複数規則・
    複数時刻範囲(``11:00-14:00,17:00-23:00``)・曜日省略(全曜日)・``off``/``closed``・
    ``PH``/``SH`` は無視(7日週モデル外)。
    それ以外(月指定・``sunrise``・``week``・コメント等)は例外。

    Raises:
        OpeningHoursParseError: 対応部分集合の外。
    """
    text = value.strip()
    if not text:
        raise OpeningHoursParseError("空文字")
    if text in ("24/7", "24/7 open", "Mo-Su 00:00-24:00", "Mo-Su,PH 00:00-24:00"):
        return [[(0, 1440)] for _ in range(7)]
    week: list[list[tuple[int, int]]] = [[] for _ in range(7)]
    touched = [False] * 7
    rules: list[str] = []
    for chunk in text.split(";"):
        chunk = chunk.strip()
        if chunk:
            rules.extend(_split_comma_rules(chunk))
    for rule in rules:
        rule = rule.strip()
        if not rule:
            continue
        m = _RULE.match(rule)
        assert m is not None  # (?P<body>.*) は必ず一致する
        selector = (m.group("days") or "").strip()
        body = m.group("body").strip()
        if selector:
            days = _parse_days(selector)
            if not days:  # PH/SH だけの規則は 7日週モデル外=無視
                continue
        else:
            days = list(range(7))
        if not body:
            raise OpeningHoursParseError(f"時刻部が空: {rule!r}")
        if body in ("off", "closed"):
            for d in days:
                week[d] = []
                touched[d] = True
            continue
        ranges = _parse_time_ranges(body)
        for d in days:
            if touched[d]:
                week[d] = sorted(week[d] + ranges)
            else:
                week[d] = list(ranges)
                touched[d] = True
    if not any(touched):
        raise OpeningHoursParseError(f"規則が空: {value!r}")
    return week


def default_week(cat: str, subcat: str | None) -> list[list[tuple[int, int]]]:
    """カテゴリ既定表 → 7×区間リスト。表に無い組は KeyError(ゲートで検出)。"""
    row = CATEGORY_DEFAULTS[(cat, subcat)]
    week: list[list[tuple[int, int]]] = []
    for d in range(7):
        week.append([] if d in row["closed_days"] else [(int(row["open"]), int(row["close"]))])
    return week


def law_key_for(cat: str, subcat: str | None, tags: dict[str, str]) -> str:
    """POI → 法規上限表のキー(OSM タグの明示があればそちらを優先)。"""
    for key, value, law in OSM_TAG_LAW_OVERRIDE:
        if tags.get(key) == value:
            return law
    if (cat, subcat) in LAW_KEY_BY_CATSUB:
        return LAW_KEY_BY_CATSUB[(cat, subcat)]
    return LAW_KEY_BY_CATSUB.get((cat, None), "none")


#: 区間を評価する絶対軸の幅 [分](開店日0時 → 翌々日0時)。日跨ぎ区間の上界。
SPAN_MIN = 2880


class LawCapEffect(NamedTuple):
    """法規上限の適用で何が起きたか(区間数)。"""

    opening_moved: int  # 開店側が後ろへ動いた区間数
    closing_moved: int  # 閉店側が前へ動いた区間数
    dropped: int  # 丸ごと消えた区間数
    split: int  # 営業不可窓に割られて2つ以上になった区間数

    @property
    def changed(self) -> bool:
        return bool(self.opening_moved or self.closing_moved or self.dropped or self.split)


def prohibited_intervals(
    closed_windows: Sequence[tuple[int, int]], span_min: int = SPAN_MIN
) -> list[tuple[int, int]]:
    """毎日繰り返す営業不可窓を絶対軸 ``[0, span_min)`` へ展開する。

    ``(1380, 2040)``(23:00-翌10:00)は前日分の折返し ``(0, 600)`` も生む。
    """
    out: list[tuple[int, int]] = []
    for start, end in closed_windows:
        if end <= start:
            raise ValueError(f"営業不可窓は end>start でなければならない: {(start, end)}")
        k = -(end // 1440) - 1
        while start + 1440 * k < span_min:
            a = start + 1440 * k
            b = end + 1440 * k
            k += 1
            a2, b2 = max(a, 0), min(b, span_min)
            if b2 > a2:
                out.append((a2, b2))
    return sorted(out)


def _subtract(interval: tuple[int, int], windows: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    """1区間から営業不可窓を引く(差集合・開店側/閉店側の両方を切る)。"""
    segs = [interval]
    for a, b in windows:
        nxt: list[tuple[int, int]] = []
        for o, c in segs:
            if b <= o or a >= c:
                nxt.append((o, c))
                continue
            if o < a:
                nxt.append((o, min(c, a)))
            if c > b:
                nxt.append((max(o, b), c))
        segs = nxt
    return [(o, c) for o, c in segs if c > o]


def apply_law_cap(
    week: list[list[tuple[int, int]]], closed_windows: Sequence[tuple[int, int]]
) -> tuple[list[list[tuple[int, int]]], LawCapEffect]:
    """営業不可窓(D-W8)で各区間を切る。**開店側も閉店側も**切る。

    戻り値 = (切り詰め後の週表, 何が起きたかの内訳)。
    """
    if not closed_windows:
        return week, LawCapEffect(0, 0, 0, 0)
    pw = prohibited_intervals(closed_windows)
    n_open = n_close = n_drop = n_split = 0
    out: list[list[tuple[int, int]]] = []
    for day in week:
        row: list[tuple[int, int]] = []
        for o, c in day:
            segs = _subtract((o, c), pw)
            if not segs:
                n_drop += 1
                continue
            if segs[0][0] > o:
                n_open += 1
            if segs[-1][1] < c:
                n_close += 1
            if len(segs) > 1:
                n_split += 1
            row.extend(segs)
        out.append(sorted(row))
    return out, LawCapEffect(n_open, n_close, n_drop, n_split)


def intervals_in_prohibited_window(
    week: list[list[tuple[int, int]]], closed_windows: Sequence[tuple[int, int]]
) -> int:
    """営業不可窓と重なる区間の数(適用前後の不変条件の計測に使う)。"""
    if not closed_windows:
        return 0
    pw = prohibited_intervals(closed_windows)
    return sum(
        1
        for day in week
        for o, c in day
        if any(min(c, b) > max(o, a) for a, b in pw)
    )


def weekly_open_minutes(week: list[list[tuple[int, int]]]) -> int:
    return int(sum(c - o for day in week for o, c in day))


def run(ctx: C.Ctx) -> C.StageResult:
    paths = [ctx.path(*parts) for parts in INPUT_FILES]
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"W7 入力が無い: {p}")
    poi_p = ctx.out / "w6_poi.parquet"
    if not poi_p.exists():
        raise FileNotFoundError(f"W7 は W6 の出力を必要とする: {poi_p}")

    overpass = C.load_json(paths[0])
    tags_by_poi: dict[str, dict[str, str]] = {}
    for el in overpass["elements"]:
        tags_by_poi[f"p_{el['type'][0]}{el['id']}"] = {
            k: str(v) for k, v in (el.get("tags") or {}).items()
        }

    poi = C.read_parquet_columns(poi_p, ["poi_id", "cat", "subcat"])
    n_poi = len(poi["poi_id"])

    present_pairs = sorted(
        {(c, s) for c, s in zip(poi["cat"], poi["subcat"])}, key=lambda t: (t[0], t[1] or "")
    )
    missing_pairs = [p for p in present_pairs if p not in CATEGORY_DEFAULTS]

    # --- ③ OSM opening_hours の解析 ---
    osm_raw = {p: t["opening_hours"] for p, t in tags_by_poi.items() if "opening_hours" in t}
    parsed_ok: dict[str, list[list[tuple[int, int]]]] = {}
    parse_fail: dict[str, str] = {}
    for pid, value in sorted(osm_raw.items()):
        try:
            parsed_ok[pid] = parse_opening_hours(value)
        except OpeningHoursParseError as exc:
            parse_fail[pid] = f"{value} :: {exc}"

    # --- ③b チェーン既定(同一 brand の最頻文面を OSM 実値から伝播)---
    brand_of: dict[str, str] = {}
    for pid, tg in tags_by_poi.items():
        brand = tg.get("brand") or tg.get("brand:ja")
        if brand:
            brand_of[pid] = brand
    brand_votes: dict[str, Counter] = {}
    for pid, week in parsed_ok.items():
        brand = brand_of.get(pid)
        if brand:
            brand_votes.setdefault(brand, Counter())[C.json_text(week)] += 1
    chain_week: dict[str, list[list[tuple[int, int]]]] = {}
    for brand, votes in sorted(brand_votes.items()):
        if sum(votes.values()) >= 2:
            top = sorted(votes.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            chain_week[brand] = [[(int(o), int(c)) for o, c in day] for day in json.loads(top)]

    # --- 行の組み立て ---
    ids: list[str] = []
    contents: list[str] = []
    srcs: list[str] = []
    law_keys: list[str] = []
    law_applied: list[bool] = []
    law_rules: list[str] = []
    valid_from: list[str] = []
    weekly_min: list[int] = []
    price_tier: list[str] = []
    violability: list[str] = []
    n_by_src: Counter = Counter()
    n_capped = 0
    n_capped_open = 0
    n_capped_close = 0
    n_intervals_open_moved = 0
    n_intervals_close_moved = 0
    n_intervals_dropped = 0
    n_intervals_split = 0
    over_cap_before = 0
    over_cap_after = 0

    for pid, cat, subcat in zip(poi["poi_id"], poi["cat"], poi["subcat"]):
        tg = tags_by_poi.get(pid, {})
        brand = brand_of.get(pid)
        if pid in parsed_ok:
            week = parsed_ok[pid]
            src = "osm_opening_hours"
            vfrom = OSM_OPENING_HOURS_ATTIC
        elif brand is not None and brand in CHAIN_MANUAL_HOURS:
            week = CHAIN_MANUAL_HOURS[brand]
            src = "chain_default"
            vfrom = ""
        elif brand is not None and brand in chain_week:
            week = chain_week[brand]
            src = "chain_default"
            vfrom = OSM_OPENING_HOURS_ATTIC
        else:
            week = default_week(cat, subcat)
            src = "category_default"
            vfrom = ""
        law = law_key_for(cat, subcat, tg)
        windows = LAW_CAPS[law]["closed_windows_min"]
        over_cap_before += intervals_in_prohibited_window(week, windows)
        week, eff = apply_law_cap(week, windows)
        over_cap_after += intervals_in_prohibited_window(week, windows)
        changed = eff.changed
        if changed:
            n_capped += 1
        if eff.opening_moved:
            n_capped_open += 1
        if eff.closing_moved:
            n_capped_close += 1
        n_intervals_open_moved += eff.opening_moved
        n_intervals_close_moved += eff.closing_moved
        n_intervals_dropped += eff.dropped
        n_intervals_split += eff.split
        ids.append(f"ps_oh_{pid}")
        contents.append(C.json_text(week))
        srcs.append(src)
        law_keys.append(law)
        law_applied.append(bool(changed))
        law_rules.append(str(LAW_CAPS[law]["citation"]))
        valid_from.append(vfrom)
        weekly_min.append(weekly_open_minutes(week))
        price_tier.append(str(CATEGORY_DEFAULTS[(cat, subcat)]["price_tier"]))
        # D-72 ③(2026-09-17・**保留**): minor_entry_limit は窓が空なので unenforced に
        # なるが、青少年条例16条1項違反は罰則つき(同26条六号・30万円以下の罰金)=enforced 相当。
        # ``violability`` は**生成列**なので直すと 18 行が動く(W7 の再構築)=親判断待ち。
        violability.append("enforced" if windows else "unenforced")
        n_by_src[src] += 1

    cols = {
        "id": ids,
        "poi_id": list(poi["poi_id"]),
        "kind": ["opening_hours"] * n_poi,
        "content": contents,
        "weekly_open_minutes": np.array(weekly_min, dtype=np.int32),
        "price_tier": price_tier,
        "valid_from": valid_from,
        "valid_to": [""] * n_poi,
        "version": np.ones(n_poi, dtype=np.int32),
        "revising_authority": ["store_manager"] * n_poi,
        "norm_kind": ["regulative"] * n_poi,
        "violability": violability,
        "announcement_scope": ["storefront_sign"] * n_poi,
        "compliance_obs_field": [""] * n_poi,
        "src": srcs,
        "law_cap_key": law_keys,
        "law_cap_applied": pa.array(law_applied, type=pa.bool_()),
        "law_cap_rule": law_rules,
    }

    params: dict[str, Any] = {
        "law_caps": {
            k: {
                **{kk: v[kk] for kk in ("label", "citation", "close_cap_min")},
                "closed_windows_min": [list(w) for w in v["closed_windows_min"]],
            }
            for k, v in LAW_CAPS.items()
        },
        "category_defaults": {
            f"{c}|{s or ''}": {**v, "closed_days": list(v["closed_days"])}
            for (c, s), v in CATEGORY_DEFAULTS.items()
        },
        "law_key_by_catsub": {f"{c}|{s or ''}": v for (c, s), v in LAW_KEY_BY_CATSUB.items()},
        "osm_tag_law_override": [list(t) for t in OSM_TAG_LAW_OVERRIDE],
        "osm_attic": OSM_OPENING_HOURS_ATTIC,
        "chain_rule": "same brand, modal parsed OSM opening_hours, >=2 votes",
        "law_cap_rule": (
            "D-W8 の営業不可時間を毎日繰り返す窓として展開し、週表の各区間との差集合を取る"
            "(開店側=窓明けまで繰り下げ・閉店側=窓入りで打ち切り・窓に割られる区間は分割)"
        ),
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash([*paths, poi_p]),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=["POI/店舗", "計画仕様(PlanSpec)", "営業時間", "価格帯"],
        expedients=list(EXPEDIENTS),
        notes={
            "osm_opening_hours_in_file": len(osm_raw),
            "osm_opening_hours_parsed": len(parsed_ok),
            "osm_parse_rate": round(len(parsed_ok) / len(osm_raw), 4) if osm_raw else 0.0,
            "osm_parse_failures_sample": sorted(parse_fail.values())[:40],
            "chain_brands_used": len(chain_week),
            "law_key_counts": dict(sorted(Counter(law_keys).items())),
            "law_cap_truncated_poi": n_capped,
            "law_cap_truncated_poi_open_side": n_capped_open,
            "law_cap_truncated_poi_close_side": n_capped_close,
            "law_cap_intervals_opening_moved": n_intervals_open_moved,
            "law_cap_intervals_closing_moved": n_intervals_close_moved,
            "law_cap_intervals_dropped": n_intervals_dropped,
            "law_cap_intervals_split": n_intervals_split,
            "law_cap_windows": {
                k: v["closed_window"] for k, v in LAW_CAPS.items() if v["closed_windows_min"]
            },
            "catsub_pairs_present": [f"{c}|{s or ''}" for c, s in present_pairs],
            "poi_matched_in_overpass_file": sum(1 for p in poi["poi_id"] if p in tags_by_poi),
            "osm_oh_rows_not_in_w6_poi": sum(1 for p in osm_raw if p not in set(poi["poi_id"])),
            "src_counts": dict(sorted(n_by_src.items())),
            "price_tier_counts": dict(sorted(Counter(price_tier).items())),
        },
    )
    res.outputs.append(C.write_parquet(ctx.out, "w7_plan_spec.parquet", cols))
    res.gates = [
        C.Gate("plan_spec_rows", n_poi, EXPECTED_POI_ROWS),
        C.Gate("category_defaults_cover_all_catsub", len(missing_pairs), 0),
        # 適用前=報告のみ(法規の窓に食い込んでいた区間数)・適用後=不変条件(必ず 0)。
        C.Gate("intervals_over_law_cap_before_apply", over_cap_before, None),
        C.Gate("intervals_over_law_cap_after_apply", over_cap_after, 0),
        C.Gate("osm_opening_hours_candidates", len(osm_raw), 565),
        C.Gate("osm_opening_hours_parsed", len(parsed_ok), None),
        C.Gate("src_osm_opening_hours", n_by_src["osm_opening_hours"], None),
        C.Gate("src_chain_default", n_by_src["chain_default"], None),
        C.Gate("src_category_default", n_by_src["category_default"], None),
        C.Gate("law_cap_truncated", n_capped, None),
        C.Gate("law_cap_truncated_open_side", n_capped_open, None),
        C.Gate("law_cap_truncated_close_side", n_capped_close, None),
        C.Gate(
            "src_partition_complete",
            n_by_src["osm_opening_hours"]
            + n_by_src["chain_default"]
            + n_by_src["category_default"],
            n_poi,
        ),
    ]
    return res
