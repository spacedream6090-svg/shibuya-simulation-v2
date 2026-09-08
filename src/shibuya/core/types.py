"""core.types — 時刻・ID・イベントクラスの固定 dtype 定義。

正典: 実装計画書 §3(core=SoAレジストリ・dtype/バイト予算宣言・Philox・ハッシュ・**時刻/ID型**)、
運用設計書 §2.5(タイブレーク=(t_sim_ns, class_rank[institution −1・conversation 0・
plan_boundary 1・individual 2・cell 3], blake3(…), subject_id))、§2.3(δ_perc は世界時刻を進めず
tick 内のナノ秒欄としてのみ使う)。

時刻の二層
- ``tick``: シミュレーション開始からの**分**(既定 tick_seconds=60)。int64。
- ``t_sim_ns``: 同じ時刻をナノ秒で表す int64 = ``tick * tick_seconds * 1e9 + offset_ns``。
  ``offset_ns`` は tick 内の秒オフセット(δ_perc=0.2〜1.5秒)を表す 0 以上 tick 長未満の値。
  **世界時刻は tick でしか進まない**(§2.3)。offset は同一 tick 内の順序専用。

層契約: 本モジュールは標準ライブラリと NumPy のみ(shibuya の他パッケージを import しない)。

逐次ループ宣言(P4): なし(本モジュールは型と定数のみ・ループを持たない)。

expedient(本モジュール分)
- ID の幅 int32(AgentId/CellId/ResourceId): 設計書は幅を明記していない。40万体・453セル・
  資源数は int32 で十分(±21億)であり、SoA のバイト予算(M2 ≤128B/体)に効く選択として固定した。
- ``INVALID_*`` 番兵 = −1: 設計書に規定なし。欠損を NaN でなく −1 で表すのは配列 dtype を
  整数に保つための自前規約。
"""

from __future__ import annotations

from enum import IntEnum
from typing import Final, NewType

import numpy as np

__all__ = [
    "AgentId",
    "CellId",
    "ResourceId",
    "AGENT_ID_DTYPE",
    "CELL_ID_DTYPE",
    "RESOURCE_ID_DTYPE",
    "TICK_DTYPE",
    "T_SIM_NS_DTYPE",
    "OFFSET_NS_DTYPE",
    "CLASS_RANK_DTYPE",
    "HASH_U64_DTYPE",
    "ID_MIN",
    "ID_MAX",
    "INVALID_AGENT_ID",
    "INVALID_CELL_ID",
    "INVALID_RESOURCE_ID",
    "NS_PER_SECOND",
    "SECONDS_PER_MINUTE",
    "DEFAULT_TICK_SECONDS",
    "MINUTES_PER_SIM_DAY",
    "EventClass",
    "CLASS_RANKS",
    "DEFERRAL_CLASSES",
    "as_agent_id",
    "as_cell_id",
    "as_resource_id",
    "t_sim_ns",
    "split_t_sim_ns",
    "max_tick",
    "INT64_MIN",
    "INT64_MAX",
]

# ---- ID 型(NewType=静的型検査用の別名・実体は int) ----
AgentId = NewType("AgentId", int)
CellId = NewType("CellId", int)
ResourceId = NewType("ResourceId", int)

AGENT_ID_DTYPE: Final = np.dtype(np.int32)
CELL_ID_DTYPE: Final = np.dtype(np.int32)
RESOURCE_ID_DTYPE: Final = np.dtype(np.int32)

#: tick(分)・t_sim_ns(ナノ秒)・tick 内オフセット・class_rank は全て int64 で持つ。
#: (lexsort の鍵を同一 dtype に揃え、符号つき比較の混在を避けるため)
TICK_DTYPE: Final = np.dtype(np.int64)
T_SIM_NS_DTYPE: Final = np.dtype(np.int64)
OFFSET_NS_DTYPE: Final = np.dtype(np.int64)
CLASS_RANK_DTYPE: Final = np.dtype(np.int64)

#: blake3 先頭8バイトの u64(タイブレーク鍵・優先度キー)。
HASH_U64_DTYPE: Final = np.dtype(np.uint64)

ID_MIN: Final[int] = 0
ID_MAX: Final[int] = 2**31 - 1
INVALID_AGENT_ID: Final[int] = -1
INVALID_CELL_ID: Final[int] = -1
INVALID_RESOURCE_ID: Final[int] = -1

NS_PER_SECOND: Final[int] = 1_000_000_000
SECONDS_PER_MINUTE: Final[int] = 60
DEFAULT_TICK_SECONDS: Final[int] = 60  # 運用設計書 §1.2 設定節 tick_seconds
MINUTES_PER_SIM_DAY: Final[int] = 1_440
INT64_MIN: Final[int] = -(2**63)
INT64_MAX: Final[int] = 2**63 - 1


class EventClass(IntEnum):
    """イベントクラスと class_rank(運用設計書 §2.5・昇順が優先)。

    値そのものが class_rank(``int(EventClass.CONVERSATION) == 0``)。
    ``INSTITUTION=-1`` は「営業時間外の購入を防ぐ」実装都合=**expedient**(§2.5 に明記)。

    繰り延べアービタの4クラス固定優先(知覚契約書 §6)= 会話ターン > 計画境界 > 個体変化 >
    セル変化 は ``CONVERSATION < PLAN_BOUNDARY < INDIVIDUAL < CELL`` と同順序
    (§2.4「規則を2つ持たない」)。
    """

    INSTITUTION = -1
    CONVERSATION = 0
    PLAN_BOUNDARY = 1
    INDIVIDUAL = 2
    CELL = 3


#: 宣言順(=昇順=優先順)のクラス一覧。
CLASS_RANKS: Final[tuple[EventClass, ...]] = (
    EventClass.INSTITUTION,
    EventClass.CONVERSATION,
    EventClass.PLAN_BOUNDARY,
    EventClass.INDIVIDUAL,
    EventClass.CELL,
)

#: 繰り延べアービタが扱う4クラス(知覚契約書 §6。制度=−1 はエンジン側イベントで繰り延べ対象外)。
DEFERRAL_CLASSES: Final[tuple[EventClass, ...]] = (
    EventClass.CONVERSATION,
    EventClass.PLAN_BOUNDARY,
    EventClass.INDIVIDUAL,
    EventClass.CELL,
)


def _check_id(value: int, name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{name} に bool は使えない")
    v = int(value)
    if v < ID_MIN or v > ID_MAX:
        raise ValueError(f"{name} は {ID_MIN}..{ID_MAX}(int32 非負)の範囲: {value!r}")
    return v


def as_agent_id(value: int) -> AgentId:
    """範囲検査つきの AgentId 変換。"""
    return AgentId(_check_id(value, "agent_id"))


def as_cell_id(value: int) -> CellId:
    """範囲検査つきの CellId 変換。"""
    return CellId(_check_id(value, "cell_id"))


def as_resource_id(value: int) -> ResourceId:
    """範囲検査つきの ResourceId 変換。"""
    return ResourceId(_check_id(value, "resource_id"))


def t_sim_ns(tick: int, offset_ns: int = 0, tick_seconds: int = DEFAULT_TICK_SECONDS) -> int:
    """(tick, tick 内オフセット[ns]) → t_sim_ns(int64 ナノ秒)。

    Args:
        tick: シミュレーション開始からの tick 数(負も可=開始前の予約は禁止だが型は許す)。
        offset_ns: tick 内オフセット(0 以上 ``tick_seconds*1e9`` 未満)。
        tick_seconds: 1 tick の秒数(既定 60)。

    Raises:
        ValueError: offset_ns が tick 長の範囲外・tick_seconds が非正。
        OverflowError: 結果が int64 に収まらない(tick_seconds=60 なら |tick| >
            153,722,867 ≈ 292 年ぶんの分)。ナノ秒欄の表現限界を**黙って回さない**。
    """
    if tick_seconds <= 0:
        raise ValueError("tick_seconds は正の整数")
    span = tick_seconds * NS_PER_SECOND
    if not (0 <= offset_ns < span):
        raise ValueError(f"offset_ns は 0..{span - 1} の範囲(tick_seconds={tick_seconds}): {offset_ns}")
    value = int(tick) * span + int(offset_ns)
    if not (INT64_MIN <= value <= INT64_MAX):
        raise OverflowError(
            f"t_sim_ns が int64 の範囲外(tick={tick}, tick_seconds={tick_seconds})。"
            f"|tick| の上限は {max_tick(tick_seconds)}"
        )
    return value


def max_tick(tick_seconds: int = DEFAULT_TICK_SECONDS) -> int:
    """t_sim_ns が **tick 内のどのオフセットでも** int64 に収まる tick の絶対値上限。

    hypothesis が見つけた境界(C4・09-08): 旧定義 ``INT64_MAX // span`` は offset=0 でしか
    成立せず、offset が大きいと ``tick*span+offset`` が INT64_MAX を 1 超えた。
    """
    if tick_seconds <= 0:
        raise ValueError("tick_seconds は正の整数")
    span = tick_seconds * NS_PER_SECOND
    return (INT64_MAX - (span - 1)) // span


def split_t_sim_ns(value: int, tick_seconds: int = DEFAULT_TICK_SECONDS) -> tuple[int, int]:
    """t_sim_ns → (tick, offset_ns)。``t_sim_ns`` の逆写像(floor 除算=負時刻でも整合)。"""
    if tick_seconds <= 0:
        raise ValueError("tick_seconds は正の整数")
    span = tick_seconds * NS_PER_SECOND
    return divmod(int(value), span)
