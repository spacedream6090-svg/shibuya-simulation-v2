"""第 6 期 6-2 カレンダー 2 の試験の共通(腕の切替・合成の台・決まった判断の規則・グループの一覧を入れる口)。"""

from __future__ import annotations

import dataclasses
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any, Iterator

import numpy as np

from shibuya.agents.state import AgentState
from shibuya.core.time_consts import NS_PER_SECOND, STEP_SECONDS, STEPS_PER_DAY
from shibuya.engine.calendar2 import arm as A
from shibuya.engine.calendar2 import port as P
from shibuya.engine.calendar2.layer import Calendar2Layer
from shibuya.engine.contact import arm as AC
from shibuya.engine.events.log import EventLog
from shibuya.world.state import World

STEP_NS = STEP_SECONDS * NS_PER_SECOND
TPD = int(STEPS_PER_DAY)
#: 合成の世界の小さなラン(記憶+店の記憶・関係なし=C1 の宛先は家族のグループ)。
KW = dict(n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0, sleep_suppression=False, vocab_version="v3",
          memory="on", relations="off", store_memory="on", checkpoint_every=60)


@contextmanager
def ca2(*, on: bool = True, contact: bool = False) -> Iterator[None]:
    """腕 arm(と連絡の道具の腕 c1)を一時的に選ぶ(組み立てが読む)。"""
    prev, prev_c = A.arm(), AC.arm()
    A.set_arm(A.ARM_ON if on else A.ARM_OFF)
    AC.set_arm(AC.ARM_C1 if contact else AC.ARM_OFF)
    try:
        yield
    finally:
        A.set_arm(prev)
        AC.set_arm(prev_c)


def groups_fixture(monkeypatch: Any) -> None:
    """合成の世界(母集団が無い=グループの一覧が無い)に、体 2 人ずつの家族と 10 人ずつの職場を入れる(宛先を作る)。"""
    from shibuya.engine.tools import record as TR
    from shibuya.engine.tools.groups import GroupList

    real = TR.build_fixture

    def build(pop, n_agents, events):
        fx = real(pop, n_agents, events)
        if fx.groups is not None:
            return fx
        ids = np.arange(int(n_agents))
        return dataclasses.replace(fx, groups=GroupList(household_id=ids // 2, org_id=ids // 10))

    monkeypatch.setattr(TR, "build_fixture", build)


class Harness:
    """カレンダー 2 の層だけを回す合成の台(体 n・セル 9・対面の会話の器の代わり=開いている会話の番号の集合)。"""

    def __init__(self, *, n: int = 6, cells: Any = None, runner: Any = None) -> None:
        self.agents = AgentState(n)
        self.agents.registry.cell[:] = np.asarray(cells if cells is not None else [0] * n, dtype=np.int32)
        self.world = World.synthetic(n_cells=9, seed=0)
        rep = np.asarray(self.world.assets.cell_rep_node, dtype=np.int64)
        self.agents.registry.node[:] = rep[np.asarray(self.agents.registry.cell, dtype=np.int64)]  # 体はセルの代表の節に居る
        self.log = EventLog(enabled=True)
        self.live: set[int] = set()
        conv = SimpleNamespace(sessions=_Sessions(self.live))
        self.layer = Calendar2Layer(n_agents=n, seed=1, population_seed=1, day_key0=0, step_seconds=STEP_SECONDS,
                                    steps_per_day=TPD, events=self.log, agents=self.agents, world=self.world,
                                    conv=conv, runner=runner)

    def step(self, T: int, *, main: tuple[int, ...] = ()) -> None:
        """刻み T を 1 つ回す(``main``=その刻みに主の判断の呼びのあった体)。"""
        self.log.begin_step(int(T) * STEP_NS)
        decision = SimpleNamespace(selected=_Sel(np.asarray(main, dtype=np.int64)))
        self.layer.run_step(int(T), int(T) * STEP_NS, int(T) % TPD, int(T) // TPD, agents=self.agents,
                            world=self.world, decision=decision)

    def events(self, family: str = "約束") -> list[Any]:
        return [e for e in self.log.events() if str(e.what).startswith(f"{family}:")]


class _Sel:
    def __init__(self, agent_id: np.ndarray) -> None:
        self.agent_id = agent_id
        self.condition = np.zeros(agent_id.size, dtype=np.int64)

    def __len__(self) -> int:
        return int(self.agent_id.size)


class _Sessions(dict):
    """開いている会話の番号の集合を ``sessions.get(id).active`` の形で見せる。"""

    def __init__(self, live: set[int]) -> None:
        super().__init__()
        self._live = live

    def get(self, k: Any, default: Any = None) -> Any:  # type: ignore[override]
        return SimpleNamespace(active=True) if int(k) in self._live else default


@contextmanager
def choose(monkeypatch: Any, rule: Any) -> Iterator[None]:
    """仮のモデルの選びを試験の規則に差し替える(``rule(ctx, presented) -> 候補の id``)。"""
    monkeypatch.setattr(P.Calendar2Port, "_pick", lambda self, ctx, presented: rule(ctx, presented))
    yield


def by_pref(*prefs: str) -> Any:
    """候補の語か id の好みの順で選ぶ規則(どれも無ければ (語・id) の順の最初の候補)。"""
    def rule(ctx: Any, presented: Any) -> str:
        for k in prefs:
            for c in presented:
                if c.kind == k or c.id == k:
                    return c.id
        return sorted(presented, key=lambda c: (c.kind, c.id))[0].id
    return rule
