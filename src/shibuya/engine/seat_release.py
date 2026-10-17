"""engine.seat_release — 在席の印を歩き出しで解く切替口(第 2 期 2-4 V3・版上げ 2 回目)。

在店(購入・食事)の在席の印 ``agents.poi_ref``/``poi_since`` は、2-2 までは退去・乗車・滞在の上限(``crowd`` の
``DWELL_MAX_TICKS``=30 分)でしか解かれなかった=店を出て歩いている体にも印が残り、店の席を占め続けた(2-2 の探り=
在席の体 × 刻みの 4.3% が店のセルの外・記録 ``docs/bench/analysis/wallbounce-1012/prox22/README.md`` §14-2)。

腕(切替口): ``--seat-release {walk,legacy}``(環境変数 ``SHIBUYA_SEAT_RELEASE``・:func:`set_arm`)。既定 ``walk``=
移動の意図(``engine.resolve._apply_move``)で**歩き出した**体(行き先のノードへ向かう=``MOVING`` になった体)の在席の印を解く
(席が空く=``crowd`` の在室の数え方が変わる)。``legacy``=2-4 より前の挙動(歩き出しでは解かない)=旧値の再現。腕は組み立ての
ときに読む(``run_day`` の引数にしない=設定の指紋に入れない=近接・経済の段階 2 の腕と同じ扱い)。腕の名と解いた数は manifest の
``leave_effects`` の ``seat_release``・``released_on_walk`` と、状態のファイルの見出しの ``seat_release``(既定の walk のランだけ
書く=見出しに無い状態のファイルは legacy=2-4 より前のラン)に出る(再開のときに今の腕と違えば止める)。

範囲(発注=V3 は ``_apply_move`` だけ): 就寝の帰り道(``_apply_sleep`` の歩き出し)・乗車の意図でホームへ歩く体
(``_apply_board`` と計画の出口の乗車)は今のまま(乗車は乗った時に解く)。記録 ``vb24/README.md`` の V3 に残りの数を書く。

逐次ループ宣言(P4): なし(歩き出した体の配列に 1 回の添字の書き込み)。
"""

from __future__ import annotations

import os
from typing import Any, Final, Mapping

__all__ = ["MODE_WALK", "MODE_LEGACY", "MODES", "DEFAULT_MODE", "arm", "set_arm", "is_walk", "header_fields",
           "check_resume", "SCHEMA"]

MODE_WALK: Final[str] = "walk"
MODE_LEGACY: Final[str] = "legacy"
MODES: Final[tuple[str, ...]] = (MODE_WALK, MODE_LEGACY)
#: 既定(2-4 V3)。``legacy`` は切替口(2-4 より前の値の再現)。
DEFAULT_MODE: Final[str] = MODE_WALK
#: manifest の ``leave_effects.seat_release`` の値の形の版(欄の意味を変えたら上げる)。
SCHEMA: Final[str] = "shibuya.seat_release/1"

_ARM: str = os.environ.get("SHIBUYA_SEAT_RELEASE", DEFAULT_MODE).strip().lower() or DEFAULT_MODE
if _ARM not in MODES:
    raise ValueError(f"SHIBUYA_SEAT_RELEASE は {MODES} のどれか(いま {_ARM!r})")


def arm() -> str:
    """いまの腕(``walk``=既定・``legacy``=切替口)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--seat-release``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。"""
    global _ARM
    if str(name) not in MODES:
        raise ValueError(f"--seat-release は {MODES} のどれか(いま {name!r})")
    _ARM = str(name)


def is_walk(mode: str | None = None) -> bool:
    """``mode``(省略=今の腕)が歩き出しで解く腕か。"""
    return str(_ARM if mode is None else mode) == MODE_WALK


def header_fields(mode: str) -> dict[str, Any] | None:
    """状態のファイルの見出しの ``seat_release``(legacy のランは書かない=None=2-4 より前の見出しのまま)。"""
    return {"mode": MODE_WALK} if str(mode) == MODE_WALK else None


def check_resume(saved: Any) -> None:
    """再開のときに、保存したランの腕(見出しの ``seat_release``・無ければ legacy)と今の腕が同じかを確かめる(違えば止める)。"""
    s = saved if isinstance(saved, Mapping) else {}
    s_mode = str(s.get("mode", MODE_LEGACY))
    if s_mode != _ARM:
        raise ValueError(f"再開の在席の印の腕が親と違う(親 {s_mode}・今 {_ARM})=--seat-release(環境変数 "
                         "SHIBUYA_SEAT_RELEASE)を親にそろえる")
