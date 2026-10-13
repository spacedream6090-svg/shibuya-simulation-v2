"""engine.events.links — 既存の記録の行に出来事の id の目印を付ける口(第 1 期 1-3・口の約束 1-3 の約束 (2))。

ActualLog(``world.processes.actual_log``)は world の層にあり engine を import できない(層の契約)。ActualLog は
``event_sink`` の欄に置かれた呼べる物を、行を書いた直後に ``sink(process_id, n)`` の形で呼び、返った id の 2 列
``(t_ns, seq)`` を行の目印の列に書く。この口がその呼べる物(``ActualLogLink``)。

- 1 行の ActualLog に 1 行の出来事(1 対 1)。出来事は ``who="runner.<過程>"``(持ち主の名)・``what="過程:<過程>"``・
  ``cause=Process(<過程>)``・時刻は記録の時計(その刻みの頭)。ActualLog の行の中身(対象の id・予定の刻み・逸脱の語・
  遅れ)は ActualLog に残す(載せ替えない=後の段)。
- 過程の id(台帳の id ``rail_operation_static`` など)→ 実行器の過程の名(``rail``)の表は実行器が渡す。

逐次ループ宣言: ``__call__`` は行数ぶん(``EventLog.append`` を 1 行ずつ)。1-3 の 1 日の行数は記録の README。
"""

from __future__ import annotations

from typing import Mapping

import numpy as np

from shibuya.engine.events import vocab as V
from shibuya.engine.events.log import Event, EventLog, Process

__all__ = ["ActualLogLink"]


class ActualLogLink:
    """ActualLog の ``event_sink``(過程の id → 出来事を ``n`` 行書いて id の 2 列を返す)。"""

    __slots__ = ("log", "_proc_of", "_proto")

    def __init__(self, log: EventLog, proc_of: Mapping[str, str]) -> None:
        for pid, key in proc_of.items():
            if key not in V.WORLD_PROCESSES:
                raise ValueError(f"過程の名が語彙表の外: {pid!r} → {key!r}")
        self.log = log
        self._proc_of = dict(proc_of)
        self._proto: dict[str, Event] = {}

    def _event_of(self, process_id: str) -> Event:
        ev = self._proto.get(process_id)
        if ev is None or ev.t_ns != self.log.now_ns:
            key = self._proc_of.get(process_id)
            if key is None:
                raise ValueError(f"ActualLog の過程の id が実行器の表に無い: {process_id!r}")
            ev = Event(t_ns=self.log.now_ns, who=f"runner.{key}", what=V.word(V.FAMILY_PROCESS, key),
                       cause=Process(key))
            self._proto[process_id] = ev
        return ev

    def __call__(self, process_id: str, n: int) -> tuple[np.ndarray, np.ndarray] | None:
        """``n`` 行の出来事を書き、id の 2 列 ``(t_ns, seq)`` を返す(記録しないときは ``None``)。"""
        if not self.log.enabled or n <= 0:
            return None
        ev = self._event_of(process_id)
        t = np.empty(n, dtype=np.int64)
        s = np.empty(n, dtype=np.int32)
        for k in range(n):  # 逐次ループ宣言: ActualLog の行数ぶん
            eid = self.log.append(ev)
            t[k], s[k] = eid  # type: ignore[misc]
        return t, s
