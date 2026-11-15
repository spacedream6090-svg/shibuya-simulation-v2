"""engine.removed_switches — 消した旧道の切替口の一覧と、渡されたら止める口(第346 旧道の切替口の削除)。

正: 返事その 6 §3-2 の 1(旧道の切替口を消す・消すたびに byte-check・安定版のタグ)。記録
``docs/bench/analysis/delete-346/README.md``。旧値の再現は安定版のタグ :data:`REMOVED_SWITCH_TAG` で回す。

消した切替口の環境変数を与えたランは、黙って既定で回さずに止める。止める所は 2 つ:

- ランの入口: 組み立て(``engine.systems.build.build`` の最初=刻みに入る前)が :func:`check_environment` を呼ぶ。切替口を
  持っていたモジュールを毎回のランで import するとは限らないので、入口で一覧を見る(検収 H1)。
- 切替口を持っていたモジュールの読み込み: 各モジュールが :func:`stop_if_set` を呼ぶ(ランの外で直に import したとき)。

CLI の旗(:data:`REMOVED_CLI_FLAGS`)は ``shibuya.cli`` が表に出さない旗として受け、渡されたら引数の誤りで止める(略記で
別の旗に読まれないように=検収 L1)。

時間の方針: 本モジュールは時刻を持たない。逐次ループ宣言: なし(名の数ぶん)。
"""

from __future__ import annotations

import os
from types import MappingProxyType
from typing import Final, Mapping

__all__ = ["REMOVED_SWITCH_TAG", "REMOVED_ENV", "REMOVED_CLI_FLAGS", "message", "stop_if_set", "check_environment"]

#: 旧道の切替口を消す前の安定版のタグ(旧値の再現はこのタグで回す)。
REMOVED_SWITCH_TAG: Final[str] = "stable-v2-before-switch-removal-346"

#: 消した切替口の環境変数 → 何の旧道だったか(与えると止まる=黙って無視しない)。
REMOVED_ENV: Final[Mapping[str, str]] = MappingProxyType({
    "SHIBUYA_RULES_42B": "規則の表の空欄 3 件を埋める前の 4-2 の値(engine.economy_rules)",
    "SHIBUYA_RULES_42": "規則の表の中身を挿す前の 4-2 の前の値(engine.economy_rules)",
    "SHIBUYA_SEAT_RELEASE": "在席の印を歩き出しで解かない 2-4 より前の挙動(engine.seat_release)",
    "SHIBUYA_PROXIMITY": "近接を同じセルで判定する 2-2 までの値(engine.proximity)",
    "SHIBUYA_DEFECT_FIXES_1103": "棚卸し B の欠陥 4 件を直す前の値(engine.defect_fixes_1103)",
})

#: 消した CLI の旗 → 対応する環境変数(``shibuya.cli`` が表に出さない旗として受けて止める)。
REMOVED_CLI_FLAGS: Final[Mapping[str, str]] = MappingProxyType({
    "--seat-release": "SHIBUYA_SEAT_RELEASE",
    "--proximity": "SHIBUYA_PROXIMITY",
    "--defect-fixes-1103": "SHIBUYA_DEFECT_FIXES_1103",
})


def message(name: str) -> str:
    """止めるときの文(名・消した段・安定版のタグ)。"""
    return (f"{name} は消した切替口(第346 旧道の切替口の削除・旧値の再現は安定版のタグ {REMOVED_SWITCH_TAG})"
            + ("=環境変数を外す" if name.startswith("SHIBUYA_") else "=旗を外す"))


def stop_if_set(*names: str, environ: Mapping[str, str] | None = None) -> None:
    """``names`` の環境変数のどれかが置かれていれば(空でない値)止める(``ValueError``)。"""
    env = os.environ if environ is None else environ
    for name in names:
        if str(env.get(name, "")).strip():
            raise ValueError(message(name))


def check_environment(environ: Mapping[str, str] | None = None) -> None:
    """消した切替口の環境変数(:data:`REMOVED_ENV` の全部)のどれかが置かれていれば止める(ランの入口で呼ぶ)。"""
    stop_if_set(*REMOVED_ENV, environ=environ)
