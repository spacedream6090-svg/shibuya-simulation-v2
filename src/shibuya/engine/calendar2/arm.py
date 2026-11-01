"""engine.calendar2.arm — カレンダー 2 の腕(第 6 期 6-2・CA2 (c)(d)・CA3・CA4・CA6・CA7・CA8)。

腕(切替口): ``--calendar-2 {off,arm}``(環境変数 ``SHIBUYA_CALENDAR_2``・:func:`set_arm`)。既定 ``off``=層を作らない(既定の
ランの final・テープ・描画・manifest の既存の欄は今のまま)。``arm`` で組み立てが ``engine.calendar2.layer.Calendar2Layer`` を作り、
系 ``calendar_2`` が立つ。腕は組み立てのときに読む(ランの途中で変えても、そのランは変わらない)。arm は結果を変える(本人が
約束の場所へ歩く)ので、設定の指紋に ``calendar_2`` の鍵を足し(``engine.systems.build``)、``cli.run`` のランの種類は腕(``arm``)
に数える。既定化はカレンダー段 2+C1 の版上げ(実 LLM の後=6-2 の版上げ)。

逐次ループ宣言: なし。
"""

from __future__ import annotations

import os
from typing import Any, Final

__all__ = ["ENV", "ARM_OFF", "ARM_ON", "ARMS", "FP_KEY", "LEDGER_ARM", "MANIFEST_KEY", "arm", "set_arm", "is_on",
           "config"]

ENV: Final[str] = "SHIBUYA_CALENDAR_2"
ARM_OFF: Final[str] = "off"
ARM_ON: Final[str] = "arm"
ARMS: Final[tuple[str, ...]] = (ARM_OFF, ARM_ON)
#: 設定の指紋(``engine.resume.fingerprint``)に足す鍵(腕 arm のときだけ=既定のランの指紋は今のまま)。
FP_KEY: Final[str] = "calendar_2"
#: 状態台帳の腕の行の腕の名(``LedgerRow.arm``・持ち主のクラスの定数 ``LEDGER_ARM`` と照合)。
LEDGER_ARM: Final[str] = "calendar-2"
#: manifest の一番上の鍵(腕 arm のランだけ)。
MANIFEST_KEY: Final[str] = "calendar_2"


def _env() -> str:
    v = os.environ.get(ENV, ARM_OFF).strip().lower() or ARM_OFF
    if v not in ARMS:
        raise ValueError(f"{ENV} は {ARMS} のどれか(いま {v!r})")
    return v


_ARM: str = _env()


def arm() -> str:
    """いまの腕(``off``=既定・``arm``)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--calendar-2``・試験の切替口)。"""
    global _ARM
    if str(name) not in ARMS:
        raise ValueError(f"--calendar-2 は {ARMS} のどれか(いま {name!r})")
    _ARM = str(name)


def is_on() -> bool:
    return _ARM == ARM_ON


def config() -> dict[str, Any] | None:
    """設定の指紋と manifest の設定の子に出す腕の組(腕 off は ``None``=指紋に何も足さない)。"""
    if not is_on():
        return None
    return {"arm": _ARM}
