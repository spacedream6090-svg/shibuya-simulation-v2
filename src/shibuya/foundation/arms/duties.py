"""engine.duties.arm — 店の仕事の腕(第 6 期 6-6 ② 第 1 部=開閉店・補充・廃棄を担当の体の判断に)。

腕(切替口): ``--duties {off,arm}``(環境変数 ``SHIBUYA_DUTIES``・:func:`set_arm`)。既定 ``off``=層を作らない(既定のランの
final・テープ・描画・manifest の既存の欄は今のまま)。``arm`` で組み立てが ``engine.duties.layer.DutiesLayer`` を作り、系
``duties`` が立ち、世界過程の開閉店・補充・廃棄は担当が店に居る店をエンジンが代わりにしなくなる(担当の居ない店は今の
conf 宣言つきのつなぎのまま)。腕は組み立てのときに読む。arm は結果を変えるので、設定の指紋に ``duties`` の鍵を足し
(``engine.systems.build``)、``cli.run`` のランの種類は腕(``arm``)に数える。

逐次ループ宣言: なし。
"""

from __future__ import annotations

import os
from typing import Any, Final

__all__ = ["ENV", "ARM_OFF", "ARM_ON", "ARMS", "FP_KEY", "LEDGER_ARM", "MANIFEST_KEY", "arm", "set_arm", "is_on",
           "config"]

ENV: Final[str] = "SHIBUYA_DUTIES"
ARM_OFF: Final[str] = "off"
ARM_ON: Final[str] = "arm"
ARMS: Final[tuple[str, ...]] = (ARM_OFF, ARM_ON)
#: 設定の指紋(``engine.resume.fingerprint``)に足す鍵(腕 arm のときだけ=既定のランの指紋は今のまま)。
FP_KEY: Final[str] = "duties"
#: 状態台帳の腕の行の腕の名(``LedgerRow.arm``・持ち主のクラスの定数 ``LEDGER_ARM`` と照合)。
LEDGER_ARM: Final[str] = "duties"
#: manifest の一番上の鍵(腕 arm のランだけ)。
MANIFEST_KEY: Final[str] = "duties"


def _env(name: str, default: str, allowed: tuple[str, ...]) -> str:
    v = os.environ.get(name, default).strip().lower() or default
    if v not in allowed:
        raise ValueError(f"{name} は {allowed} のどれか(いま {v!r})")
    return v


_ARM: str = _env(ENV, ARM_OFF, ARMS)


def arm() -> str:
    """いまの腕(``off``=既定・``arm``)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--duties``・試験の切替口)。"""
    global _ARM
    if str(name) not in ARMS:
        raise ValueError(f"--duties は {ARMS} のどれか(いま {name!r})")
    _ARM = str(name)


def is_on() -> bool:
    return _ARM == ARM_ON


def config() -> dict[str, Any] | None:
    """設定の指紋と manifest の設定の子に出す腕の組(腕 off は ``None``=指紋に何も足さない)。"""
    if not is_on():
        return None
    return {"arm": _ARM}
