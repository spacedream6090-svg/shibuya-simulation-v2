"""第 6 期 6-4 C1 の試験の共通(腕の切替・合成の層・決まった判断の仮のモデル)。"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import numpy as np

from shibuya.agents.state import AgentState
from shibuya.core.time_consts import NS_PER_SECOND, STEP_SECONDS, STEPS_PER_DAY
from shibuya.engine import batching as BA
from shibuya.engine.contact import arm as A
from shibuya.engine.contact import port as P
from shibuya.engine.contact.layer import ContactLayer
from shibuya.engine.events.log import EventLog
from shibuya.engine.tools.groups import GroupList
from shibuya.world.state import World

ROOT = Path(__file__).resolve().parents[3]
WORLD = ROOT / "data" / "world" / "v2"
STEP_NS = STEP_SECONDS * NS_PER_SECOND
#: 合成の世界の小さなラン(記憶+関係+店の記憶=6-5 の試験と同じ形)。
KW = dict(n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0, sleep_suppression=False, vocab_version="v3",
          memory="on", relations="on", store_memory="on", checkpoint_every=60)


@contextmanager
def c1(*, unnoticed: str | None = None, send: str | None = None, on: bool = True) -> Iterator[None]:
    """腕 c1(と下の腕)を一時的に選ぶ(組み立てが読む)。"""
    prev = (A.arm(), A.unnoticed(), A.send())
    A.set_arm(A.ARM_C1 if on else A.ARM_OFF)
    if unnoticed is not None:
        A.set_unnoticed(unnoticed)
    if send is not None:
        A.set_send(send)
    try:
        yield
    finally:
        A.set_arm(prev[0])
        A.set_unnoticed(prev[1])
        A.set_send(prev[2])


class Harness:
    """連絡の層だけを回す合成の台(体 6・セル 9・家族 2 組と職場 1 つ・待ち行列つき)。

    体 0・1=家族(世帯 0)・体 2・3=家族(世帯 1)・体 0・1・2=職場(組織 5)・体 4・5=どこにも属さない。
    """

    def __init__(self, *, n: int = 6, width_s: int = STEP_SECONDS, cells: Any = None, send: str = "b",
                 unnoticed: str = "i", events: bool = True) -> None:
        self.agents = AgentState(n)
        self.agents.registry.cell[:] = np.asarray(cells if cells is not None else [0] * n, dtype=np.int32)
        self.world = World.synthetic(n_cells=9, seed=0)
        self.log = EventLog(enabled=events)
        hh = np.array([0, 0, 1, 1, -1, -1] + [-1] * (n - 6))[:n]
        org = np.array([5, 5, 5, -1, -1, -1] + [-1] * (n - 6))[:n]
        self.groups = GroupList(household_id=hh, org_id=org)
        self.layer = ContactLayer(n_agents=n, seed=1, population_seed=1, day_key0=0, step_seconds=STEP_SECONDS,
                                  events=self.log, agents=self.agents, world=self.world, groups=self.groups,
                                  unnoticed_arm=unnoticed, send_arm=send)
        self.queue = BA.WindowQueue(width_s=width_s, start_ns=0, step_s=STEP_SECONDS)
        self.T = 0

        def on_step(t_ns: int, _a: Any, _s: Any) -> None:
            T = int(t_ns) // STEP_NS
            self.queue.schedule(int(t_ns) + STEP_NS, BA.WORLD, BA.KIND_STEP)
            self.log.begin_step(int(t_ns))
            self.layer.run_step(T, int(t_ns), T % STEPS_PER_DAY, agents=self.agents, world=self.world, conv=None,
                                runner=None, decision=None)
            self.T = T

        self.queue.register(BA.KIND_STEP, "step", on_step, rank=0)
        self.layer.bind_queue(self.queue)
        self.queue.schedule(0, BA.WORLD, BA.KIND_STEP)

    def run(self, steps: int) -> None:
        """刻み ``steps`` 個ぶんの窓を回す(幅が刻みより狭ければ窓の数は増える)。"""
        end = int(self.queue.head_ns) + int(steps) * STEP_NS
        while self.queue.head_ns < end:
            self.queue.run_window()

    def events(self, family: str = "連絡") -> list[Any]:
        return [e for e in self.log.events() if str(e.what).startswith(f"{family}:")]


@contextmanager
def choose(monkeypatch: Any, rule: Any) -> Iterator[None]:
    """仮のモデルの選びを試験の規則に差し替える(``rule(ctx, presented) -> 候補の id``)。"""
    monkeypatch.setattr(P.ContactPort, "_pick", lambda self, ctx, presented: rule(ctx, presented))
    yield


def by_kind(*prefs: str) -> Any:
    """候補の語の好みの順で選ぶ規則(どれも無ければ最初の候補)。"""
    def rule(ctx: Any, presented: Any) -> str:
        for k in prefs:
            for c in presented:
                if c.kind == k:
                    return c.id
        return sorted(presented, key=lambda c: (c.kind, c.id))[0].id
    return rule
