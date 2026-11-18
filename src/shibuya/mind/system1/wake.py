"""mind.system1.wake — 割る段で ``engine/arbiter.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``runtime/arbiter.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
import numpy as np

__all__ = [
    "WakeCandidates",
]


@dataclass(frozen=True)
class WakeCandidates:
    """1 tick 分の起床候補(全て同じ長さの配列)。

    Attributes:
        agent_id: int64。
        condition: int8(``agents.state.WakeCondition``)。
        class_rank: int64(``core.types.EventClass``)。
        since_tick: int64(**最初に起床条件が立った tick**。待ち時間の基準)。
        sleep_exempt: bool(**就寝中でも通す**印。D-56。既定=全 False)。
            立てるのは呼の**源**であって条件ではない(顕著行為由来と変化検出由来は
            どちらも ``CELL_BLOCK`` なので条件では区別できない)。
    """

    agent_id: np.ndarray
    condition: np.ndarray
    class_rank: np.ndarray
    since_tick: np.ndarray
    sleep_exempt: np.ndarray | None = None

    def __post_init__(self) -> None:
        n = self.agent_id.size
        for name in ("condition", "class_rank", "since_tick"):
            if getattr(self, name).size != n:
                raise ValueError(f"WakeCandidates.{name} の長さが agent_id と違う")
        if self.sleep_exempt is None:
            object.__setattr__(self, "sleep_exempt", np.zeros(n, dtype=bool))
        else:
            ex = np.asarray(self.sleep_exempt, dtype=bool)
            if ex.size != n:
                raise ValueError("WakeCandidates.sleep_exempt の長さが agent_id と違う")
            object.__setattr__(self, "sleep_exempt", ex)

    def __len__(self) -> int:
        return int(self.agent_id.size)

    @classmethod
    def empty(cls) -> "WakeCandidates":
        return cls(
            np.empty(0, dtype=np.int64),
            np.empty(0, dtype=np.int8),
            np.empty(0, dtype=np.int64),
            np.empty(0, dtype=np.int64),
            np.empty(0, dtype=bool),
        )

    @classmethod
    def concat(cls, parts: Sequence["WakeCandidates"]) -> "WakeCandidates":
        parts = [p for p in parts if len(p)]
        if not parts:
            return cls.empty()
        return cls(
            np.concatenate([p.agent_id for p in parts]),
            np.concatenate([p.condition for p in parts]),
            np.concatenate([p.class_rank for p in parts]),
            np.concatenate([p.since_tick for p in parts]),
            np.concatenate([p.sleep_exempt for p in parts]),
        )

    def take(self, idx: np.ndarray) -> "WakeCandidates":
        return WakeCandidates(
            self.agent_id[idx], self.condition[idx], self.class_rank[idx], self.since_tick[idx],
            np.asarray(self.sleep_exempt)[idx],
        )
