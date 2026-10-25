"""engine.calendar3.arm — カレンダー 3 の腕(第 6 期 6-2・雇い主・祝日=C3 職場の連絡と束ねる・CA1・CA9・CA10・CA11)。

腕(切替口): ``--calendar-3 {off,arm}``(環境変数 ``SHIBUYA_CALENDAR_3``・:func:`set_arm`)。既定 ``off``=層を作らない(既定の
ランの final・テープ・描画・manifest の既存の欄は今のまま)。``arm`` で組み立てが ``engine.calendar3.layer.Calendar3Layer`` を作り、
系 ``calendar_3`` が立つ。腕 arm は連絡の道具 C1(``--contact c1``=職場の連絡を送る口)とカレンダー 2(``--calendar-2 arm``=
本人の予定の器 ``PromiseBook``)の層を**再利用**する(二重に作らない)=どちらかが無いランは組み立てで止める(``ValueError``)。
腕は組み立てのときに読む。arm は結果を変える(職場の連絡が C1 の口を通る)ので、設定の指紋に ``calendar_3`` の鍵を足し
(``engine.systems.build``)、``cli.run`` のランの種類は腕(``arm``)に数える。

下の腕(環境変数だけ・arm のときだけ効く):

- ``SHIBUYA_CALENDAR_3_TRIAL`` = ``off``(既定)/``on``: **試験用の印**(分析に使わない印=決定 10-12 §4-1 CA10「試験用(分析に
  使わない印)」)。on のランだけ、開始日の検査の規則の違反(0 日目が月曜でない・0 日目が祝日・連続する平日に収まらない)を止めずに
  manifest の ``calendar_3.trial`` に記録する(日曜 → 月曜の 2 日・祝日を含む日付のランを回す口)。止める違反(祝日の表が読めない・
  表の範囲の外)は今のまま止める。印は設定の指紋にも入る(取り違えの再開を止める)。

逐次ループ宣言: なし。
"""

from __future__ import annotations

import os
from typing import Any, Final

__all__ = ["ENV", "ARM_OFF", "ARM_ON", "ARMS", "ENV_TRIAL", "TRIAL_ARMS", "FP_KEY", "LEDGER_ARM", "MANIFEST_KEY",
           "TRIAL_MARK", "arm", "set_arm", "is_on", "trial", "set_trial", "trial_on", "config"]

ENV: Final[str] = "SHIBUYA_CALENDAR_3"
ARM_OFF: Final[str] = "off"
ARM_ON: Final[str] = "arm"
ARMS: Final[tuple[str, ...]] = (ARM_OFF, ARM_ON)
ENV_TRIAL: Final[str] = "SHIBUYA_CALENDAR_3_TRIAL"
TRIAL_ARMS: Final[tuple[str, ...]] = ("off", "on")
#: 設定の指紋(``engine.resume.fingerprint``)に足す鍵(腕 arm のときだけ=既定のランの指紋は今のまま)。
FP_KEY: Final[str] = "calendar_3"
#: 状態台帳の腕の行の腕の名(``LedgerRow.arm``・持ち主のクラスの定数 ``LEDGER_ARM`` と照合)。
LEDGER_ARM: Final[str] = "calendar-3"
#: manifest の一番上の鍵(腕 arm のランだけ)。
MANIFEST_KEY: Final[str] = "calendar_3"
#: 試験用の印の語(manifest の ``calendar_3.trial.mark``)。
TRIAL_MARK: Final[str] = "試験用(分析に使わない)"


def _env(name: str, default: str, allowed: tuple[str, ...]) -> str:
    v = os.environ.get(name, default).strip().lower() or default
    if v not in allowed:
        raise ValueError(f"{name} は {allowed} のどれか(いま {v!r})")
    return v


_ARM: str = _env(ENV, ARM_OFF, ARMS)
_TRIAL: str = _env(ENV_TRIAL, "off", TRIAL_ARMS)


def arm() -> str:
    """いまの腕(``off``=既定・``arm``)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--calendar-3``・試験の切替口)。"""
    global _ARM
    if str(name) not in ARMS:
        raise ValueError(f"--calendar-3 は {ARMS} のどれか(いま {name!r})")
    _ARM = str(name)


def is_on() -> bool:
    return _ARM == ARM_ON


def trial() -> str:
    """試験用の印の下の腕(``off``・``on``)。"""
    return _TRIAL


def set_trial(name: str) -> None:
    global _TRIAL
    if str(name) not in TRIAL_ARMS:
        raise ValueError(f"{ENV_TRIAL} は {TRIAL_ARMS} のどれか(いま {name!r})")
    _TRIAL = str(name)


def trial_on() -> bool:
    """試験用の印が効くか(腕 arm で下の腕 on のときだけ)。"""
    return is_on() and _TRIAL == "on"


def config() -> dict[str, Any] | None:
    """設定の指紋と manifest の設定の子に出す腕の組(腕 off は ``None``=指紋に何も足さない)。"""
    if not is_on():
        return None
    return {"arm": _ARM, "trial": _TRIAL}
