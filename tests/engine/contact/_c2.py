"""第 6 期 6-4 C2(連絡の道具の残り)の試験の共通: 家・勤め先・習慣の腕・店の番号の表を渡せる合成の台。"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import numpy as np

from shibuya.agents.state import AgentState
from shibuya.core.time_consts import STEP_SECONDS, STEPS_PER_DAY
from shibuya.engine import batching as BA
from shibuya.engine.contact import arm as A
from shibuya.engine.contact import device as DV
from shibuya.engine.contact.layer import ContactLayer
from shibuya.engine.events.log import EventLog
from shibuya.engine.tools.groups import GroupList
from shibuya.world.state import World

from tests.engine.contact._c1 import STEP_NS


class Harness2:
    """連絡の層だけを回す合成の台(体 6・セル 9・家族 2 組と職場 1 つ・待ち行列つき)+家(``home_cell``)・勤め先・習慣の腕・
    店の番号の表。体 0・1=家族(世帯 0)・体 2・3=家族(世帯 1)・体 0・1・2=職場(組織 5)・体 4・5=どこにも属さない。
    ``decision_fn(T)`` は系 contact に渡す判断の写し(起床の条件=割り込み)を返す口(既定 None)。"""

    def __init__(self, *, n: int = 6, cells: Any = None, home_cell: Any = None, work_cell: Any = None,
                 habit: bool = False, phones: Any = None, events: bool = True, world: Any = None) -> None:
        self.agents = AgentState(n)
        self.agents.registry.cell[:] = np.asarray(cells if cells is not None else [0] * n, dtype=np.int32)
        self.world = world if world is not None else World.synthetic(n_cells=9, seed=0)
        self.log = EventLog(enabled=events)
        hh = np.array([0, 0, 1, 1, -1, -1] + [-1] * (n - 6))[:n]
        org = np.array([5, 5, 5, -1, -1, -1] + [-1] * (n - 6))[:n]
        self.groups = GroupList(household_id=hh, org_id=org)
        self.layer = ContactLayer(n_agents=n, seed=1, population_seed=1, day_key0=0, step_seconds=STEP_SECONDS,
                                  events=self.log, agents=self.agents, world=self.world, groups=self.groups,
                                  unnoticed_arm="i", send_arm="b", home_cell=home_cell, work_cell=work_cell,
                                  habit=habit, phones=phones)
        self.queue = BA.WindowQueue(width_s=STEP_SECONDS, start_ns=0, step_s=STEP_SECONDS)
        self.T = 0
        self.decision_fn: Any = None
        self.before_step: Any = None

        def on_step(t_ns: int, _a: Any, _s: Any) -> None:
            T = int(t_ns) // STEP_NS
            self.queue.schedule(int(t_ns) + STEP_NS, BA.WORLD, BA.KIND_STEP)
            self.log.begin_step(int(t_ns))
            if self.before_step is not None:
                self.before_step(self, T)
            dec = None if self.decision_fn is None else self.decision_fn(T)
            self.layer.run_step(T, int(t_ns), T % STEPS_PER_DAY, agents=self.agents, world=self.world, conv=None,
                                runner=None, decision=dec)
            self.T = T

        self.queue.register(BA.KIND_STEP, "step", on_step, rank=0)
        self.layer.bind_queue(self.queue)
        self.queue.schedule(0, BA.WORLD, BA.KIND_STEP)

    def run(self, steps: int) -> None:
        end = int(self.queue.head_ns) + int(steps) * STEP_NS
        while self.queue.head_ns < end:
            self.queue.run_window()

    def events(self, family: str = "連絡") -> list[Any]:
        return [e for e in self.log.events() if str(e.what).startswith(f"{family}:")]

    def of(self, what: str) -> list[Any]:
        return [e for e in self.log.events() if e.what == what]


def loud(h: Any) -> None:
    """全員の電話を手に持ち・音あり・イヤホンなし(気づく道を決める)。"""
    d = h.layer.dev
    d._manner[:] = False
    d._place[:] = DV.PLACE_HAND
    d._home[:] = DV.PLACE_HAND
    d._ear[:] = False


@contextmanager
def habit_arm(on: bool) -> Iterator[None]:
    prev = A.habit()
    A.set_habit("on" if on else "off")
    try:
        yield
    finally:
        A.set_habit(prev)
