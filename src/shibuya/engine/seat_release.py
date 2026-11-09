"""engine.seat_release — 在席の印を歩き出しで解く(第 2 期 2-4 V3・版上げ 2 回目)の見出しと再開の検査。

在店(購入・食事)の在席の印 ``agents.poi_ref``/``poi_since`` は、2-2 までは退去・乗車・滞在の上限(``crowd`` の
``DWELL_MAX_TICKS``=30 分)でしか解かれなかった=店を出て歩いている体にも印が残り、店の席を占め続けた(2-2 の探り=
在席の体 × 刻みの 4.3% が店のセルの外・記録 ``docs/bench/analysis/wallbounce-1012/prox22/README.md`` §14-2)。

ランは常に ``walk``=移動の意図(``engine.resolve._apply_move``)で**歩き出した**体(行き先のノードへ向かう=``MOVING`` に
なった体)の在席の印を解く(席が空く=``crowd`` の在室の数え方が変わる)。腕の名と解いた数は manifest の ``leave_effects`` の
``seat_release``(値は ``walk`` に固定)・``released_on_walk`` と、状態のファイルの見出しの ``seat_release``(``{"mode": "walk"}``
=見出しに無い状態のファイルは 2-4 より前のラン=再開できない)に出る。

〔第346 旧道の切替口の削除〕2-4 より前の挙動(歩き出しでは解かない)の再現の切替口 ``--seat-release legacy``(環境変数
``SHIBUYA_SEAT_RELEASE``・``set_arm``)は消した: 環境変数を与えると読み込みで止まる・CLI の旗は引数の誤り。旧値の再現は安定版の
タグ ``stable-v2-before-switch-removal-346``。``engine.resolve.apply`` の ``seat_release_walk=False``(関数の既定)は部品の単体
試験の基準の口として残す(ランの口からは選べない・つなぎの台帳に行は無かった=記録 ``delete-346/README.md`` だけ)。

範囲(発注=V3 は ``_apply_move`` だけ): 就寝の帰り道(``_apply_sleep`` の歩き出し)・乗車の意図でホームへ歩く体
(``_apply_board`` と計画の出口の乗車)は今のまま(乗車は乗った時に解く)。記録 ``vb24/README.md`` の V3 に残りの数を書く。

逐次ループ宣言(P4): なし(歩き出した体の配列に 1 回の添字の書き込み)。
"""

from __future__ import annotations

import os
from typing import Any, Final, Mapping

__all__ = ["MODE_WALK", "MODE_LEGACY", "DEFAULT_MODE", "ENV_REMOVED", "header_fields", "check_resume", "SCHEMA"]

MODE_WALK: Final[str] = "walk"
#: 見出しに ``seat_release`` の無い状態のファイルの読み(2-4 より前のラン=〔第346〕再開できない)。
MODE_LEGACY: Final[str] = "legacy"
#: ランの腕(2-4 V3・〔第346〕これだけ)。
DEFAULT_MODE: Final[str] = MODE_WALK
#: manifest の ``leave_effects.seat_release`` の値の形の版(欄の意味を変えたら上げる)。
SCHEMA: Final[str] = "shibuya.seat_release/1"

#: 〔第346〕消した切替口の環境変数(与えると止まる=黙って無視しない)。
ENV_REMOVED: Final[str] = "SHIBUYA_SEAT_RELEASE"
if os.environ.get(ENV_REMOVED, "").strip():
    raise ValueError(f"{ENV_REMOVED} は消した切替口(第346 旧道の切替口の削除・旧値の再現は安定版のタグ "
                     "stable-v2-before-switch-removal-346)=環境変数を外す")


def header_fields(mode: str = DEFAULT_MODE) -> dict[str, Any] | None:
    """状態のファイルの見出しの ``seat_release``(ランは常に ``{"mode": "walk"}``・walk の外の名は None)。"""
    return {"mode": MODE_WALK} if str(mode) == MODE_WALK else None


def check_resume(saved: Any) -> None:
    """再開のときに、保存したランの見出しの ``seat_release``(無ければ legacy=2-4 より前のラン)が walk かを確かめる(違えば止める)。"""
    s = saved if isinstance(saved, Mapping) else {}
    s_mode = str(s.get("mode", MODE_LEGACY))
    if s_mode != DEFAULT_MODE:
        raise ValueError(f"再開の在席の印の腕が親と違う(親 {s_mode}・今 {DEFAULT_MODE})=旧値の切替口 --seat-release legacy は"
                         "消した(安定版のタグ stable-v2-before-switch-removal-346 で回す)")
