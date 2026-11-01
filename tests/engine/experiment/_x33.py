"""第 3 期 3-3 の試験の共通の材料(申込書の雛形・合成の世界の組み立て)。"""

from __future__ import annotations

import copy
import dataclasses
from types import SimpleNamespace
from typing import Any

import numpy as np

from shibuya.core.time_consts import NS_PER_SECOND, SECONDS_PER_DAY, SECONDS_PER_HOUR
from shibuya.engine.calendar import DEFAULT_WORLD_START, SimCalendar
from shibuya.engine.events.log import EventLog
from shibuya.engine.experiment import apply as AP
from shibuya.engine.experiment.form import ExperimentForm
from shibuya.engine.processes.environment import EnvironmentProcess
from shibuya.engine.processes.opening import OpeningProcess

from tests.engine.processes.conftest import fake_plan_assets, fake_weather_assets, make_agents, make_world

STEP_S = 60
STEPS_PER_DAY = SECONDS_PER_DAY // STEP_S
NS_DAY = SECONDS_PER_DAY * NS_PER_SECOND
NS_HOUR = SECONDS_PER_HOUR * NS_PER_SECOND

BASE: dict[str, Any] = {
    "kind": "explore",
    "subject": {"level": "L1", "ids": [0]},
    "content": [{"decision": "closure"}],
    "start": NS_DAY + 12 * NS_HOUR,
    "question": "店を休むと人の流れはどう変わるか",
    "metrics": {"primary": {"id": "calls", "path": "manifest.llm_calls_total"},
                "secondary": [{"id": "final_len", "path": "n_agents"}]},
}


def form_dict(**over: Any) -> dict[str, Any]:
    d = copy.deepcopy(BASE)
    d.update(over)
    return d


def form(**over: Any) -> ExperimentForm:
    return ExperimentForm.from_dict(form_dict(**over))


#: 合成の世界の W7(店 0〜2 は月〜日 9:00-21:00・店 3 は区間なし)と W13(3 日)。
PLAN_ROWS = [(j, d, 540, 1260) for j in range(3) for d in range(7)]
WEATHER_DATES = ("2026-07-13", "2026-07-14", "2026-08-20")


def synthetic_world(n_cells: int = 9, n_agents: int = 24, *, weather: bool = True, plan: bool = True):
    """合成の世界(``World.synthetic``)+手書きの W7・W13 の世界過程 2 つ(営業時間・天気)と暦と出来事の記録。"""
    world = make_world(n_cells)
    agents, _ = make_agents(world, n_agents)
    pa = fake_plan_assets(PLAN_ROWS if plan else [])
    if weather:
        wa = fake_weather_assets(n_cells, dates=WEATHER_DATES)
        wa = dataclasses.replace(wa, weather_type=("晴", "雨", "晴"))
        pa = dataclasses.replace(pa, **{f.name: getattr(wa, f.name) for f in dataclasses.fields(wa)
                                       if f.name.startswith(("weather", "hourly", "sun", "cell_street", "n_street"))})
    cal = SimCalendar(DEFAULT_WORLD_START, tick_seconds=STEP_S)  # 祝日の表はこの暦だけの空の辞書
    op = OpeningProcess(world, agents, pa, day_index=cal.opening_row(0))
    env = EnvironmentProcess(world, agents, pa, master_seed=1, tick_seconds=STEP_S, calendar=cal)
    runner = SimpleNamespace(opening=op, environment=env)
    return SimpleNamespace(world=world, agents=agents, assets=pa, calendar=cal, opening=op, environment=env,
                           runner=runner)


def handle(sw, *, begin_ns: int = 0, inherited: bool = False, events: EventLog | None = None) -> AP.WorldHandle:
    return AP.WorldHandle(world=sw.world, runner=sw.runner, calendar=sw.calendar,
                          events=EventLog() if events is None else events, step_seconds=STEP_S,
                          steps_per_day=STEPS_PER_DAY, n_agents=int(sw.agents.n), begin_ns=begin_ns,
                          inherited=inherited, rec=AP.ApplyRecord())


def at(h: AP.WorldHandle, f: ExperimentForm, t_ns: int) -> int:
    """刻みの頭の時刻 ``t_ns`` で口を 1 回(記録の時計をその刻みに置いてから)。"""
    if h.events is not None:
        h.events.begin_step(t_ns)
    return AP.apply(f, h, t_ns)


def rows(sw, pois) -> np.ndarray:
    return np.asarray(sw.opening.open_matrix)[np.asarray(pois)]
