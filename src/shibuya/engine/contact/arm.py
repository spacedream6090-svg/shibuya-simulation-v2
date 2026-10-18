"""engine.contact.arm — 連絡の道具 C1 の腕(第 6 期 6-4)。

腕(切替口): ``--contact {off,c1}``(環境変数 ``SHIBUYA_CONTACT``・:func:`set_arm`)。既定 ``off``=層を作らない(既定のランの
final・テープ・描画・manifest の既存の欄は今のまま)。``c1`` で組み立てが ``engine.contact.layer.ContactLayer`` を作り、系
``contact`` が立つ。腕は組み立てのときに読む(ランの途中で変えても、そのランは変わらない)。c1 は結果を変えるので、設定の指紋に
``contact`` の鍵(腕と下の腕)を足し(``engine.systems.build``)、``cli.run`` のランの種類は腕(``arm``)に数える。

下の腕(環境変数だけ・c1 のときだけ効く):

- ``SHIBUYA_CONTACT_UNNOTICED`` = ``i``(既定)/``ii``/``iii``: 関心の的が他のときに割り込めなかった周りの出来事の入力への載せ方
  (決定 10-12 §4-4 CT0 の 3 つの腕=(i) 載せない (ii) 隅に粗い 1 行 (iii) そのまま)。既定 (i) は「割り込めたときだけ処理される」
  の文のまま=仮採用(検証に合う構造は 3 つを比べて選ぶ)。
- ``SHIBUYA_CONTACT_SEND`` = ``b``(既定)/``c``: 送る文(CT2 の既定 (b)=文は LLM の口=mock では定型の文・比べる腕 (c)=判断の
  選択の言葉をそのまま送る)。

逐次ループ宣言: なし。
"""

from __future__ import annotations

import os
from typing import Any, Final

__all__ = [
    "ENV", "ARM_OFF", "ARM_C1", "ARMS", "ENV_UNNOTICED", "UNNOTICED_ARMS", "DEFAULT_UNNOTICED", "ENV_SEND",
    "SEND_ARMS", "DEFAULT_SEND", "FP_KEY", "LEDGER_ARM", "arm", "set_arm", "is_on", "unnoticed", "set_unnoticed",
    "send", "set_send", "config",
]

ENV: Final[str] = "SHIBUYA_CONTACT"
ARM_OFF: Final[str] = "off"
ARM_C1: Final[str] = "c1"
ARMS: Final[tuple[str, ...]] = (ARM_OFF, ARM_C1)

ENV_UNNOTICED: Final[str] = "SHIBUYA_CONTACT_UNNOTICED"
#: 割り込めなかった出来事の載せ方((i) 載せない・(ii) 隅に粗い 1 行・(iii) そのまま)。
UNNOTICED_ARMS: Final[tuple[str, ...]] = ("i", "ii", "iii")
DEFAULT_UNNOTICED: Final[str] = "i"

ENV_SEND: Final[str] = "SHIBUYA_CONTACT_SEND"
#: 送る文の腕((b)=文は LLM の口・(c)=判断の選択の言葉をそのまま)。
SEND_ARMS: Final[tuple[str, ...]] = ("b", "c")
DEFAULT_SEND: Final[str] = "b"

#: 設定の指紋(``engine.resume.fingerprint``)に足す鍵(腕 c1 のときだけ=既定のランの指紋は今のまま)。
FP_KEY: Final[str] = "contact"
#: 状態台帳の腕の行の腕の名(``LedgerRow.arm``・持ち主のクラスの定数 ``LEDGER_ARM`` と照合)。
LEDGER_ARM: Final[str] = "contact-c1"


def _env(name: str, default: str, allowed: tuple[str, ...]) -> str:
    v = os.environ.get(name, default).strip().lower() or default
    if v not in allowed:
        raise ValueError(f"{name} は {allowed} のどれか(いま {v!r})")
    return v


_ARM: str = _env(ENV, ARM_OFF, ARMS)
_UNNOTICED: str = _env(ENV_UNNOTICED, DEFAULT_UNNOTICED, UNNOTICED_ARMS)
_SEND: str = _env(ENV_SEND, DEFAULT_SEND, SEND_ARMS)


def arm() -> str:
    """いまの腕(``off``=既定・``c1``)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--contact``・試験の切替口)。"""
    global _ARM
    if str(name) not in ARMS:
        raise ValueError(f"--contact は {ARMS} のどれか(いま {name!r})")
    _ARM = str(name)


def is_on() -> bool:
    return _ARM == ARM_C1


def unnoticed() -> str:
    """割り込めなかった出来事の載せ方の腕(``i``・``ii``・``iii``)。"""
    return _UNNOTICED


def set_unnoticed(name: str) -> None:
    global _UNNOTICED
    if str(name) not in UNNOTICED_ARMS:
        raise ValueError(f"{ENV_UNNOTICED} は {UNNOTICED_ARMS} のどれか(いま {name!r})")
    _UNNOTICED = str(name)


def send() -> str:
    """送る文の腕(``b``・``c``)。"""
    return _SEND


def set_send(name: str) -> None:
    global _SEND
    if str(name) not in SEND_ARMS:
        raise ValueError(f"{ENV_SEND} は {SEND_ARMS} のどれか(いま {name!r})")
    _SEND = str(name)


def config() -> dict[str, Any] | None:
    """設定の指紋と manifest の設定の子に出す腕の組(腕 off は ``None``=指紋に何も足さない)。"""
    if not is_on():
        return None
    return {"arm": _ARM, "unnoticed": _UNNOTICED, "send": _SEND}
