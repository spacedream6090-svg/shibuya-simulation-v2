"""engine.processes.rail_events — 渋谷の発着の表(W12 1.3.0)を読む口の器(第 2 期 2-3c・**既定は読まない**)。

構築側の W12(``src/shibuya/build/field/w12_rail_events.py``)は 1.3.0 で渋谷の到着の行と直通のまとめの列を
``w12_rail_events.parquet`` に足した。エンジンの鉄道の過程(``engine.processes.rail``)は今も発車の表
``w12_timetables.parquet`` だけを読み、着く体も発車の便から降りる(つなぎの台帳 ``EX-build.field.w12_external_nodes-ea8dc0c1``・
``HD-engine.processes.rail-1af925f4``)。本モジュールはその表を**読むだけの器**で、どの過程からも呼ばれない
(:data:`READ_RAIL_EVENTS` = False・呼ぶと決めるのは資産の活性化=版上げ 3 回目 4-3 の段)。

読むのは列 ``event・call_kind・line・calendar・time_min・departure_row・merged_into_row・counted``(列の意味は構築側の
docstring)。分は運行日の分を 1 日の分(0〜1439)に畳む(``world.assets`` の発車の表と同じ畳み方)。表が無い資産
(1.2.0 まで・合成の世界)では ``None``。

逐次ループ宣言: なし(列を 1 回ずつ読むだけ・起動時に 1 回)。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np

from shibuya.core.time_consts import MINUTES_PER_DAY

__all__ = ["RAIL_EVENTS_FILE", "READ_RAIL_EVENTS", "EVENTS", "CALL_KINDS", "RailEventsAsset", "load_rail_events"]

#: 資産のファイルの名(構築側 ``EVENTS_FILE`` と同じ=試験で照らす)。
RAIL_EVENTS_FILE: Final[str] = "w12_rail_events.parquet"
#: 既定は読まない(結果不変)。True にする段は 4-3(資産の活性化と一緒に決める)。
READ_RAIL_EVENTS: Final[bool] = False
#: ``event`` の値の番号(0=発車・1=到着)。
EVENTS: Final[tuple[str, ...]] = ("departure", "arrival")
#: ``call_kind`` の値の番号。
CALL_KINDS: Final[tuple[str, ...]] = ("origin", "terminal", "through", "unknown")
_COLUMNS: Final[tuple[str, ...]] = (
    "event", "call_kind", "line", "calendar", "time_min", "departure_row", "merged_into_row", "counted",
)


@dataclass(frozen=True)
class RailEventsAsset:
    """発着の表の SoA(行の順は資産のまま)。``lines`` は線の名(昇順)・``line_idx`` はその索引。

    配列はどれも読み取り専用(``setflags(write=False)``=書くと ``ValueError``)。
    """

    lines: tuple[str, ...]
    event: np.ndarray
    call_kind: np.ndarray
    line_idx: np.ndarray
    calendar: np.ndarray
    minute_of_day: np.ndarray
    departure_row: np.ndarray
    merged_into_row: np.ndarray
    counted: np.ndarray

    @property
    def n(self) -> int:
        return int(self.event.size)

    def arrivals(self) -> np.ndarray:
        """到着の行の索引。"""
        return np.flatnonzero(self.event == EVENTS.index("arrival"))


def load_rail_events(world_dir: str | Path, *, enabled: bool | None = None) -> RailEventsAsset | None:
    """資産の置き場から発着の表を読む。``enabled`` を省くと :data:`READ_RAIL_EVENTS`(既定 False=読まずに ``None``)。

    表が無いときも ``None``。知らない ``event``・``call_kind`` の値は ``ValueError``(黙って通さない)。
    """
    on = READ_RAIL_EVENTS if enabled is None else bool(enabled)
    p = Path(world_dir) / RAIL_EVENTS_FILE
    if not on or not p.exists():
        return None
    import pyarrow.parquet as pq  # noqa: PLC0415(読むときだけ)

    t = pq.read_table(p, columns=list(_COLUMNS)).to_pydict()
    bad = sorted({str(x) for x in t["event"]} - set(EVENTS)) + sorted({str(x) for x in t["call_kind"]} - set(CALL_KINDS))
    if bad:
        raise ValueError(f"発着の表に知らない値: {bad}")
    lines = tuple(sorted({str(x) for x in t["line"]}))
    lidx = {name: i for i, name in enumerate(lines)}
    arrays = {
        "event": np.array([EVENTS.index(str(x)) for x in t["event"]], dtype=np.int8),
        "call_kind": np.array([CALL_KINDS.index(str(x)) for x in t["call_kind"]], dtype=np.int8),
        "line_idx": np.array([lidx[str(x)] for x in t["line"]], dtype=np.int16),
        "calendar": np.array([0 if str(c) == "Weekday" else 1 for c in t["calendar"]], dtype=np.int8),
        "minute_of_day": (np.asarray(t["time_min"], dtype=np.int64) % MINUTES_PER_DAY).astype(np.int32),
        "departure_row": np.array(t["departure_row"], dtype=np.int32),
        "merged_into_row": np.array(t["merged_into_row"], dtype=np.int32),
        "counted": np.array(t["counted"], dtype=bool),
    }
    for a in arrays.values():  # 〔検収 L3〕読むだけの資産=書き換えられないようにする
        a.setflags(write=False)
    return RailEventsAsset(lines=lines, **arrays)
