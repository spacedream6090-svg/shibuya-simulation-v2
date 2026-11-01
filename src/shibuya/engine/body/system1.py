"""engine.body.system1 — 意図しない System 1 の反応の**器だけ**の 3 件(第 3 期 3-5・値は空)。

正: 決定 10-12 §1-5 の ③ 群(ロンバード効果・混雑の中の歩き方と避け方・大きな音に注意が向く=本人の体と System 1 として
コードに残す・研究で「意図しない」と裏付けがあり選択を決めないものに限る)・計画 10-12 の 3-5 の行。洗い出し
(``wallbounce-1006/agentless-outcomes-inventory.md``)にこの 3 件の行は無い=今のコードに無い。値を作る仕組みは空間の段
(段 3 の音の伝わり方・段 1 の物理)で入る。本段は口と欄だけを置き、値は空(None)のまま返す=既定のランの結果・描画は
1 バイトも変わらない。

| 器 | 口 | 欄 | 値が入る段 |
|---|---|---|---|
| ロンバード効果(周りの騒音 → 話す大きさ) | :func:`speech_loudness`(値は空)・:func:`noise_stage_at`(10 の騒音の資産 W10 の読みの口=今の騒音の段を読む) | ``Percept.heard_speech``(聞こえる会話=誰に届くかが話す大きさで変わる) | 5-3 |
| 混雑の中の歩き方と避け方 | :func:`crowd_gait`(値は空) | なし(空間の段 1 の物理=歩く速さと向き) | 5-1 |
| 大きな音に注意が向く | :func:`loud_sound_notice`(値は空) | ``Percept.nearby_change`` の種類 ``loud_sound``(``perception.facts.NEARBY_CHANGE_KINDS``) | 5-3 |

expedient の宣言は :data:`SYSTEM1_EXPEDIENTS`(つなぎの台帳の ``BR-SYSTEM1-*`` の 3 行・外す段 5-3・5-1・5-3)。

逐次ループ宣言: なし(器の口は値を作らない)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

import numpy as np

from shibuya.perception.facts import NEARBY_CHANGE_KINDS

__all__ = ["SYSTEM1_EXPEDIENTS", "System1Slot", "SLOTS", "speech_loudness", "noise_stage_at", "crowd_gait",
           "loud_sound_notice", "manifest_rows", "LOUD_SOUND"]

#: 大きな音に注意が向く=``Percept.nearby_change`` の種類の値(``perception.facts.NEARBY_CHANGE_KINDS`` にある)。
LOUD_SOUND: Final[str] = "loud_sound"
if LOUD_SOUND not in NEARBY_CHANGE_KINDS:  # pragma: no cover - 語の表と食い違えば読み込みで止める
    raise ImportError("perception.facts.NEARBY_CHANGE_KINDS に loud_sound が無い")

#: 器だけの 3 件の宣言(つなぎの台帳の ``BR-SYSTEM1-*`` の 3 行と 1 対 1・文を変えたら台帳も直す)。
SYSTEM1_EXPEDIENTS: Final[tuple[str, ...]] = (
    "ロンバード効果(周りの騒音 → 話す大きさ)の器だけ=口 speech_loudness と W10 の騒音の段の読みの口(値は空=None・"
    "聞こえる会話 Percept.heard_speech に効く値は空間の段 3 の音の伝わり方で入る)",
    "混雑の中の歩き方と避け方の器だけ=口 crowd_gait(値は空=None・空間の段 1 の物理で入る)",
    "大きな音に注意が向くの器だけ=知覚の事実 Percept.nearby_change の種類 loud_sound と口 loud_sound_notice(値は空=None・"
    "空間の段 3 で入る)",
)


@dataclass(frozen=True, slots=True)
class System1Slot:
    """器 1 つ(id・中身・口・欄・値が入る段・つなぎの台帳の行)。"""

    id: str
    what: str
    port: str
    field: str
    stage: str
    bridge: str


SLOTS: Final[tuple[System1Slot, ...]] = (
    System1Slot("system1.lombard", "ロンバード効果(周りの騒音 → 話す大きさ)", "speech_loudness・noise_stage_at",
                "Percept.heard_speech", "5-3", "BR-SYSTEM1-LOMBARD"),
    System1Slot("system1.crowd_gait", "混雑の中の歩き方と避け方", "crowd_gait", "", "5-1", "BR-SYSTEM1-CROWD-GAIT"),
    System1Slot("system1.loud_sound", "大きな音に注意が向く", "loud_sound_notice",
                f"Percept.nearby_change[{LOUD_SOUND}]", "5-3", "BR-SYSTEM1-LOUD-SOUND"),
)


def speech_loudness(noise_stage: Any, *, agent_id: Any = None) -> None:
    """ロンバード効果の口: 周りの騒音の段 → 話す大きさ。**値は空**(None=仕組みがまだ無い・空間の段 3)。"""
    return None


def noise_stage_at(world: Any, cells: np.ndarray, step: int, step_seconds: int) -> np.ndarray:
    """W10 の騒音の段の読みの口(``World.noise_stage_for_tick`` の値をセルで引く・読むだけ)。舞台の外の体は 0。

    ロンバード効果の値(:func:`speech_loudness`)の入力。本段では読み手が居ない(器だけ)。
    """
    stage = np.asarray(world.noise_stage_for_tick(int(step), int(step_seconds)), dtype=np.uint8)
    c = np.asarray(cells).astype(np.int64)
    ok = (c >= 0) & (c < stage.size)
    out = np.zeros(c.shape, dtype=np.uint8)
    out[ok] = stage[c[ok]]
    return out


def crowd_gait(density_stage: Any, *, agent_id: Any = None) -> None:
    """混雑の中の歩き方と避け方の口。**値は空**(None=空間の段 1 の物理で入る)。"""
    return None


def loud_sound_notice(sound: Any, *, agent_id: Any = None) -> None:
    """大きな音に注意が向く口(知覚の事実 ``Percept.nearby_change`` の種類 ``loud_sound``)。**値は空**(None)。"""
    return None


def manifest_rows() -> list[dict[str, str]]:
    """manifest の ``body.system1``(器の一覧・設定)。"""
    return [{"id": s.id, "what": s.what, "port": s.port, "field": s.field, "stage": s.stage, "bridge": s.bridge,
             "value": "empty"} for s in SLOTS]
