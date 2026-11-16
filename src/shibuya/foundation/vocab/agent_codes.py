"""foundation.vocab.agent_codes — 割る段で ``agents/state.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``world/model/agent_table.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from enum import IntEnum
from typing import Final
import numpy as np
from shibuya.foundation.types import EventClass

__all__ = [
    "AgentKind", "MOCK_KIND_COUNT", "Activity", "FOCUS_NONE", "focus_code_for_person", "focus_code_for_poi",
    "focus_is_person", "focus_is_poi", "focus_poi_of", "ResultCode", "WakeCondition", "N_WAKE_CONDITIONS",
    "N_WAKE_CONDITIONS_ALL", "ActivityKind", "ACTIVITY_UNTIL_NONE", "IntentKind", "INTENT_NONE", "INTENT_FIELDS",
    "FAMILIARITY_FIELDS", "FAMILIARITY_EMPTY", "ENERGY_FIELDS", "MEMORY_FIELDS", "STORE_MEMORY_FIELDS",
    "STORE_MEMORY_EMPTY", "RELATION_FIELDS", "REL_EMPTY", "REFRACTORY_MINUTES", "WAKE_CONDITION_CLASS",
    "RESULT_TEXT",
]


#: ``focus_target`` の「焦点なし」(C9b G4)。
FOCUS_NONE: Final[int] = -1


def focus_code_for_person(agent_id) -> np.ndarray:
    """個体 id → ``focus_target`` の符号化(そのまま=非負)。"""
    return np.asarray(agent_id, dtype=np.int64)


def focus_code_for_poi(poi_id) -> np.ndarray:
    """POI 索引 → ``focus_target`` の符号化(``-2 - poi_id`` ≤ -2)。

    **欄を 2 本に増やさないための符号化**(4 B/体のまま人とオブジェクトの両方を指す)。
    ``-1`` は「焦点なし」に取ってあるので POI 0 は ``-2`` になる。
    """
    return -2 - np.asarray(poi_id, dtype=np.int64)


def focus_is_person(code) -> np.ndarray:
    """``focus_target`` が個体を指しているか。"""
    return np.asarray(code, dtype=np.int64) >= 0


def focus_is_poi(code) -> np.ndarray:
    """``focus_target`` が POI を指しているか。"""
    return np.asarray(code, dtype=np.int64) <= -2


def focus_poi_of(code) -> np.ndarray:
    """``focus_target`` → POI 索引(POI でない要素は ``-1``)。"""
    c = np.asarray(code, dtype=np.int64)
    return np.where(c <= -2, -2 - c, -1)


class AgentKind(IntEnum):
    """個体の種別。

    0-4 は C2 の mock 用に置いた 5 値、**5-8 は C5(W16 母集団合成)で足した 4 値**。
    値は**固定**(``economy.anchors.WalletKind`` の写し・``perception.templates.KIND_WORDS``
    の索引・W16 出力 ``w16_population.parquet`` の ``kind`` 列と 1 対 1)。知覚契約書 §2.2
    「B1 種別(約10)」の枠内。

    W16 の割り当て規約(``build.pop.w16_population``)
      - ``RESIDENT``  : 舞台に常住し、舞台内の組織に勤めていない体(域外通勤・在宅・非就業)
      - ``WORKER``    : 舞台に常住し、舞台内の組織に勤める体(=在区就業)
      - ``COMMUTER``  : 域外常住・舞台内の組織に勤める体
      - ``STUDENT``   : 域外常住・舞台内の学校に通う体
      - ``VISITOR`` / ``FOREIGN_VISITOR`` / ``REGULAR_VISITOR``: 来街者(訪日・定期の別)
      - ``CREW``      : 乗務員・駅務・警察/消防などの職務者
      - ``DISPATCHER``: 運行/警備の指令
    """

    COMMUTER = 0  # 通勤者
    VISITOR = 1  # 来街者
    WORKER = 2  # 従業者
    RESIDENT = 3  # 居住者
    DISPATCHER = 4  # 指令(権限行動の観測用・C2 では行動しない)
    STUDENT = 5  # 通学者(W16)
    REGULAR_VISITOR = 6  # 定期来街者(W16)
    FOREIGN_VISITOR = 7  # 訪日来街者(W16)
    CREW = 8  # 乗務員・職務者(W16)


#: C2 の mock 合成日課が引く種別の数(0..3=通勤/来街/従業/居住)。**指令以降は出さない**。
#: ``len(AgentKind)`` を使うと C5 で種別を足したときに mock の乱数列が動くので定数で釘付ける。
MOCK_KIND_COUNT: Final[int] = 4


class Activity(IntEnum):
    """現在の行動状態(行動契約書 §2.1 の効果が落ちる先)。"""

    IDLE = 0
    MOVING = 1  # 移動
    WAITING = 2  # 待機
    RESTING = 3  # 休憩
    SLEEPING = 4  # 就寝
    SHOPPING = 5  # 購入(店頭滞在)
    CONVERSING = 6  # 会話
    RIDING = 7  # 乗車


class ResultCode(IntEnum):
    """「直前の結果」コード(行動契約書 §2.1 失敗の意味論 / §6 の 50 tok 欄の素材)。

    0 は成功。1 以上が失敗の型。``RESULT_TEXT`` に契約書の文言を持つ。
    """

    OK = 0
    UNREACHABLE = 1  # 到達不能
    INTERRUPTED = 2  # 途中打ち切り(混雑・閉鎖)
    TRAIN_FULL = 3  # 満員
    FARE_SHORT = 4  # 運賃不足
    NO_TRAIN = 5  # 列車なし
    NO_STOP = 6  # その駅には止まらない
    MONEY_SHORT = 7  # 所持金不足
    OUT_OF_STOCK = 8  # 在庫切れ
    CLOSED = 9  # 営業時間外
    PARTNER_BUSY = 10  # 相手が会話中
    REFUSED = 11  # 断られた
    PARTNER_GONE = 12  # 去った
    NO_BED = 13  # 寝る場所がない
    NO_PERMISSION = 14  # 権限なし
    LOST_ARBITRATION = 15  # 資源競合に落選(二相コミット Phase B)
    UNDEFINED_ACTION = 16  # 未定義行動(§7 段1)
    BAD_TARGET = 17
    INSUFFICIENT_ABILITY = 18  # 能力不足(手伝い・行動契約書 §2.1)
    NOT_IN_EATERY = 19  # 飲食店にいない(語彙 v2「食事」・D-71 §3 E)
    TARGET_GONE = 20  # 対象が去った(C9 G11・最後に見た位置へ着いても居なかった)
    TOO_FAR = 21  # 遠すぎて時間切れ(段 2c・経路は在るが意図の上限 tick のうちに着かなかった)


#: 契約書の文言(「直前の結果」の 50 tok 欄で使う短句)。
RESULT_TEXT: Final[dict[int, str]] = {
    ResultCode.OK: "成功",
    ResultCode.UNREACHABLE: "到達不能",
    ResultCode.INTERRUPTED: "途中打ち切り",
    ResultCode.TRAIN_FULL: "満員",
    ResultCode.FARE_SHORT: "運賃不足",
    ResultCode.NO_TRAIN: "列車なし",
    ResultCode.NO_STOP: "その駅には止まらない",
    ResultCode.MONEY_SHORT: "所持金不足",
    ResultCode.OUT_OF_STOCK: "在庫切れ",
    ResultCode.CLOSED: "営業時間外",
    ResultCode.PARTNER_BUSY: "相手が会話中",
    ResultCode.REFUSED: "断られた",
    ResultCode.PARTNER_GONE: "去った",
    ResultCode.NO_BED: "寝る場所がない",
    ResultCode.NO_PERMISSION: "権限なし",
    ResultCode.LOST_ARBITRATION: "先に取られた",
    ResultCode.UNDEFINED_ACTION: "未定義の行動",
    ResultCode.BAD_TARGET: "対象を特定できない",
    ResultCode.INSUFFICIENT_ABILITY: "能力不足",
    ResultCode.NOT_IN_EATERY: "飲食店にいない",
    ResultCode.TARGET_GONE: "対象が去った",
    ResultCode.TOO_FAR: "遠すぎて時間切れ",
}


class WakeCondition(IntEnum):
    """起床条件(知覚契約書 §6 不応期表の**11 行と 1 対 1**)+ **活動の満了**(二層・段 2)。

    値は ``refractory_until`` の列番号。行の並びは契約書の表の順。``ACTIVITY_EXPIRY`` だけは
    **不応期表の外**(列を持たない=``refractory_until`` の幅は 11 のまま・モジュール注記)。
    """

    CONVERSATION_TURN = 0  # (iv) 会話ターン
    PLAN_SLEEPING = 1  # (iii) 計画境界: 睡眠中
    PLAN_WORKING = 2  # (iii) 計画境界: 就業/就学中
    PLAN_GENERAL = 3  # (iii) 計画境界: 一般活動
    PLAN_TRANSIT = 4  # (iii) 計画境界: 移動・待機中
    INTEROCEPTION = 5  # (ii) 内受容閾値
    ACQUAINTANCE = 6  # (ii) 知人出現
    PROXIMITY_SWAP = 7  # (ii) 近接入替
    BEING_WATCHED = 8  # (ii) 被注視
    OVERHEARD = 9  # (ii) 傍受
    CELL_BLOCK = 10  # (i) セル動的ブロック変化
    ACTIVITY_EXPIRY = 11  # 活動の満了(起床入口 5・D-116・不応期表の外)


#: 条件数 K(``refractory_until`` の列数)=**§6 不応期表の行数**。``ACTIVITY_EXPIRY`` は含まない。
N_WAKE_CONDITIONS: Final[int] = 11
#: 起床条件の総数(不応期表の 11 行 + 活動の満了)。
N_WAKE_CONDITIONS_ALL: Final[int] = len(WakeCondition)

#: 不応期[分](知覚契約書 §6 の表。睡眠中は「起床まで≥360 分」を 360 で表す)。
REFRACTORY_MINUTES: Final[tuple[int, ...]] = (
    0,  # 会話ターン(mechanism・床なし)
    360,  # 計画境界: 睡眠中(mechanism)
    150,  # 計画境界: 就業/就学中(expedient・GATSim 就業値)
    60,  # 計画境界: 一般活動(expedient)
    15,  # 計画境界: 移動・待機中(expedient)
    45,  # 内受容閾値(expedient・ヒステリシスで置換を試す)
    10,  # 知人出現(expedient・同一相手 60 分は relations.REL_ACQ_PAIR_REFRACTORY_MIN=関係 on で働く。〔第334 訂正〕前の注「C2 未実装」は古い)
    15,  # 近接入替(expedient・最大の暴発源)
    5,  # 被注視(expedient)
    5,  # 傍受(expedient・同一話者 30 分は C2 未実装)〔11-03 棚卸し A §4-1〕会話の側に招待の間隔 30(conversation.SPEAKER_INVITE_REFRACTORY_TICKS)がある=傍受の起床の不応期と同じものかは不明=仕分け待ち
    30,  # セル動的ブロック変化(expedient)
)

#: 起床条件 → 繰り延べアービタの 4 クラス(知覚契約書 §6・運用設計書 §2.5 と同順序)。
WAKE_CONDITION_CLASS: Final[tuple[EventClass, ...]] = (
    EventClass.CONVERSATION,
    EventClass.PLAN_BOUNDARY,
    EventClass.PLAN_BOUNDARY,
    EventClass.PLAN_BOUNDARY,
    EventClass.PLAN_BOUNDARY,
    EventClass.INDIVIDUAL,
    EventClass.INDIVIDUAL,
    EventClass.INDIVIDUAL,
    EventClass.INDIVIDUAL,
    EventClass.INDIVIDUAL,
    EventClass.CELL,
    EventClass.PLAN_BOUNDARY,  # 活動の満了(自分で決めた持続の区切り=計画境界と同じ級・expedient)
)

assert len(REFRACTORY_MINUTES) == N_WAKE_CONDITIONS
assert len(WAKE_CONDITION_CLASS) == N_WAKE_CONDITIONS_ALL
assert int(WakeCondition.ACTIVITY_EXPIRY) == N_WAKE_CONDITIONS  # 表の直後=列を持たない


class ActivityKind(IntEnum):
    """活動の種別(``activity_kind``・二層の実装アジェンダ §2 の表)。"""

    NONE = 0  # 活動なし(未設定・就寝)
    MOVE_TO = 1  # 目的地つき移動(移動・乗車)
    WANDER = 2  # あたり(近傍を歩き回る)
    IN_SHOP = 3  # 在店(購入・食事・並ぶ)
    IN_PLACE = 4  # その場(なし・会話・その他)


#: ``activity_until`` の「活動なし」。
ACTIVITY_UNTIL_NONE: Final[int] = -1


class IntentKind(IntEnum):
    """意図の対象の種類(``intent_kind``・段 2c)。``intent_target`` の意味を決める。"""

    NONE = 0  # 意図なし
    POI_NAMED = 1  # 名指しの店(``intent_target``=POI 索引)
    POI_CATEGORY = 2  # カテゴリ語で近傍から選んだ店(``intent_target``=POI 索引)
    PERSON = 3  # 会話の相手(``intent_target``=個体 id)
    BED = 4  # 寝床(``intent_target``=自宅セル)


#: ``intent_action`` の「意図なし」(行動コードと衝突しない負値)。
INTENT_NONE: Final[int] = -1
#: 親しみの表の 5 欄(4 段目・``familiarity_columns`` のランだけ確保)。
FAMILIARITY_FIELDS: Final[tuple[str, ...]] = (
    "fam_thing", "fam_first", "fam_last", "fam_visits", "fam_exposures",
)
#: 親しみの表の空行(``fam_thing``)。
FAMILIARITY_EMPTY: Final[int] = -1

#: 記憶の表の 9 欄(6 段目 6a・``memory_columns`` のランだけ確保)。
MEMORY_FIELDS: Final[tuple[str, ...]] = (
    "mem_kind", "mem_tick", "mem_last", "mem_cell", "mem_partner", "mem_object",
    "mem_result", "mem_importance", "mem_n",
)

#: 店の評価の記憶の 7 欄(D-120 7a・``store_memory_columns`` のランだけ確保)。
STORE_MEMORY_FIELDS: Final[tuple[str, ...]] = (
    "sm_poi", "sm_valence", "sm_precision", "sm_first", "sm_last", "sm_n", "sm_source",
)
#: 店の評価の記憶の空行(``sm_poi``)。
STORE_MEMORY_EMPTY: Final[int] = -1

#: 関係辺の 6 欄(C10 8a・``relation_columns`` のランだけ確保)。
RELATION_FIELDS: Final[tuple[str, ...]] = (
    "rel_partner", "rel_kind", "rel_sign", "rel_first", "rel_last", "rel_n",
)
#: 関係辺の空行(``rel_partner``)。
REL_EMPTY: Final[int] = -1

#: 体のエネルギー収支の 4 欄(5 段目 5a・``energy_columns`` のランだけ確保)。
ENERGY_FIELDS: Final[tuple[str, ...]] = (
    "weight_kg", "eer_kcal", "since_meal_kcal", "energy_balance",
)

#: 意図の 4 欄(段 2c)。``Registry.state_hash(exclude=INTENT_FIELDS)`` で「欄を足す前」の
#: checkpoint と挙動が同じことを確かめる(監査用)。
INTENT_FIELDS: Final[tuple[str, ...]] = (
    "intent_action", "intent_target", "intent_kind", "intent_since",
)

#: 内受容 3 変数の並び(``<名前>_stage`` フィールドの順序)。
INTEROCEPTION_FIELDS: Final[tuple[str, ...]] = ("hunger", "fatigue", "thermal")
