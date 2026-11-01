"""W21 段 1「人数の枠」: 層 × 人数の目安を 1 行 1 出典で ``w21_frame.json`` に書く(構築側だけ)。

正: 答申 R-116 §4(段 1 の枠の下書き=構築側の材料だけ)・PENDING 仮-23(都市圏に住む人の私事と業務の来街は構築側の錨を
置かず**空欄**=段 7 で「来るか」を本人の判断の結果として出す・席は経済センサス・人数は国勢調査)・計画 第 4 期 段 1
(較正用のデータだけを使い、検証専用の一覧=パターン台帳 §10 は使わない)。

- 値は 2 種類: **計算**(本段が読んだ構築側の表から出した値=住民と周りの輪)と **引**(R-116 §4 が R-109 の構築側の部分から
  引いた値。原典の一次確認は R-109・R-116 の親検収)。
- **書かない値**: 人流・PT の集中量(0240〜0243)・b-4 の滞留・駅の事業者別の利用者数(D10)・R-109 §8-1 の 1 か月と 1 日の
  来街の幅(検証側の集中量を含む)。〔灰〕の欄(朝 1 時間の集中率・定期券の割合・着時間帯の供給の形)も書かない。
- 空欄の行は ``value`` が ``null`` で、理由(``blank_reason``)を書く。

逐次ループ宣言(P4): 行の数ぶん(14)。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final

__all__ = ["FRAME_ROWS", "build_frame", "FORBIDDEN_TERMS", "freeze", "thaw"]


def freeze(obj: Any) -> Any:
    """辞書は読み取り専用の写像に・リストはタプルに(入れ子も)=表を書き換えられないようにする(検収 L3)。"""
    if isinstance(obj, dict):
        return MappingProxyType({k: freeze(v) for k, v in obj.items()})
    if isinstance(obj, (list, tuple)):
        return tuple(freeze(v) for v in obj)
    return obj


def thaw(obj: Any) -> Any:
    """``freeze`` の逆(JSON に書くため)。"""
    if isinstance(obj, (dict, MappingProxyType)):
        return {k: thaw(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [thaw(v) for v in obj]
    return obj

#: 枠の表に書いてはいけない語(検証側の値の印)。``build_frame`` の出力を照らす(試験の負の対照)。
FORBIDDEN_TERMS: Final[tuple[str, ...]] = ("集中量", "滞留人口", "人流", "乗降人員", "265", "330 万")

#: 層の行(引の値は R-116 §4 の写し)。``value`` は 1 日の別々の人(平日)の目安の幅 [下, 上](人)。行は読み取り専用。
FRAME_ROWS: Final[tuple[Any, ...]] = freeze([
    {"band": "in_area", "layer": "resident", "label": "住民",
     "value": "computed:residents", "month": "same_as_day",
     "source": "国勢調査 2020 小地域 第1表(町丁目の人口)× 2025 第2-1表(区の総数)÷ 2020 の区の総数 × 町丁目の被覆率",
     "mark": "計算", "note": "2020 の按分は 43,588(W16)。時点の混ぜ方は宣言(つなぎの台帳)"},
    {"band": "in_area", "layer": "workers_and_students_from_outside", "label": "外から来て働く人と学ぶ人",
     "value": [185_000, 250_000], "month": "same_people",
     "source": "R-109 §5-1・§8-1 の国勢調査(昼間人口からの推測)と経済センサス(所属で数えた人)の部分(R-116 §4 が引いた)",
     "mark": "引", "note": "下=国勢調査の昼間人口から推測・上=経済センサスの所属で数えた人(席は経済センサス・人数は国勢調査=仮-23)"},
    {"band": "in_area", "layer": "workers_in_ward", "label": "(参考)渋谷区で働く人(区全体・従業地)",
     "value": "computed:workers_in_ward", "month": "same_people",
     "source": "国勢調査 2020 従業地・通学地集計 第11-1表(従業地=渋谷区の 15 歳以上就業者)", "mark": "計算",
     "note": "区全体の値=舞台の分ではない(舞台の席は経済センサス=段 4)"},
    {"band": "in_area", "layer": "students_from_outside", "label": "うち学ぶ人", "value": None,
     "blank_reason": "舞台の分は学校の定員が要る(区へ通学する人は 15 歳未満を含めて 42,833・うち他の市区町村から 31,560"
                     "=国勢調査 2020 第4表・区全体)", "source": "国勢調査 2020 従業地・通学地集計 第4表(R-116 §4)",
     "mark": "空欄"},
    {"band": "in_area", "layer": "visitors_metro_private_business", "label": "来街(都市圏に住む人の私事と業務)",
     "value": None,
     "blank_reason": "構築側の錨を置かない(PENDING 仮-23)=段 7 で範囲の外の人が「来るか」を本人の判断の結果として出す",
     "reference": {"value": [86_000, 112_000], "unit": "トリップ/日",
                   "what": "自宅以外からの私事(PT 2018 の構築側=回答 10-13b §1 1-3・舞台の中だけの移動を含む・R-116 §4 が引いた)"},
     "source": "—", "mark": "空欄"},
    {"band": "in_area", "layer": "visitors_inbound", "label": "来街(訪日客)", "value": [43_000, 85_000],
     "month": {"value": 1_300_000, "unit": "旅の数"},
     "source": "R-109 §2-1・§2-2(都 訪都旅行者数 2024・行動特性調査の渋谷の訪問率)", "mark": "引", "note": "推測の幅"},
    {"band": "in_area", "layer": "visitors_domestic_outside_metro", "label": "来街(都市圏の外の国内客)",
     "value": None, "blank_reason": "構築側の材料が無い(R-116 §空欄 3)", "source": "—", "mark": "空欄"},
    {"band": "in_area", "layer": "transfer_only", "label": "駅で乗り換えるだけの人(直通で乗ったままを含む)",
     "value": [700_000, 800_000], "month": None,
     "source": "R-109 §3-1(大都市交通センサスの降車の和と乗換え=W12 の入力と同じ系の構築側の欄)",
     "mark": "引", "note": "回数 140〜158 万。上の端 158 万=1,799,223 − 222,701(構築側だけから出る)。下の端の出どころは未確認(R-116 §6 の 3)"},
    {"band": "in_area", "layer": "through_jr", "label": "JR で電車に乗ったまま通る人", "value": [460_000, 460_000],
     "month": None, "source": "R-109 §3-1(回数 917,279)", "mark": "引", "note": "腕 (b) では周りの輪"},
    {"band": "in_area", "layer": "crew_dispatch_public", "label": "乗務員・指令・公共の要員", "value": None,
     "blank_reason": "段 4 で作り直す(今の W16 は v1 の在庫 1,258+指令 24)", "source": "R-100・R-109 §5-1", "mark": "空欄"},
    {"band": "ring", "layer": "ward_rest_residents", "label": "渋谷区の残りの町丁目(夜間)",
     "value": "computed:ring_residents", "month": "same_as_day",
     "source": "国勢調査 2025 第2-1表(区の総数)− 住民(上の行)", "mark": "計算", "note": "昼間 約 33 万(2020・引)"},
    {"band": "far", "layer": "potential_visitors", "label": "来る可能性のある人(来るかを判断する人)", "value": None,
     "blank_reason": "1 日の人数は段 7 の結果。1 か月の下限の目安は「通勤通学の 18.5〜25 万+訪日 約 130 万+都市圏の私事"
                     "(空欄)」(R-116 §4)", "month": {"value": [1_485_000, 1_550_000], "unit": "人(下限・都市圏の私事を除く)"},
     "source": "R-116 §4・流入元は第4表の 1,896 市区町村の重み", "mark": "空欄"},
    {"band": "far", "layer": "bodiless_contacts", "label": "体のない遠くの人(連絡だけ)", "value": None,
     "blank_reason": "未リサーチ(候補: 人々のつながりに関する基礎調査の会う頻度・2025 の市区町村の世帯の表)",
     "source": "R-99", "mark": "空欄"},
])


def build_frame(residents: int, workers_in_ward: float, ward_total_2025: float, *, version: str) -> dict[str, Any]:
    """枠の表(JSON の中身)。``computed:*`` の値を計算の値で置き換える。"""
    computed = {
        "computed:residents": [int(residents), int(residents)],
        "computed:workers_in_ward": [int(round(workers_in_ward)), int(round(workers_in_ward))],
        "computed:ring_residents": [int(round(ward_total_2025 - residents))] * 2,
    }
    rows = []
    for r in FRAME_ROWS:  # 逐次: 行の数ぶん
        row = thaw(r)
        if isinstance(row.get("value"), str):
            row["value"] = computed[row["value"]]
        rows.append(row)
    return {
        "schema": "w21.frame/1",
        "version": version,
        "unit": "1 日の別々の人(平日)の目安の幅 [下, 上]",
        "policy": ("構築側の材料だけ(パターン台帳 §10 の検証専用の一覧と R-116 §1 の検証側の 11 行は使わず、値も書かない)。"
                   "都市圏の私事・業務の来街は空欄(仮-23)"),
        "rows": rows,
        "blank_layers": [r["layer"] for r in rows if r.get("value") is None],
    }
