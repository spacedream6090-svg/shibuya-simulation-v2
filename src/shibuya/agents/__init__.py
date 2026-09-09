"""agents: 個体状態SoA/T0習慣/記憶/関係。core に依存。

層契約: docs/design/v2-implementation-plan.md §3(import-linter で強制)。
C2 第2弾で入るのは**個体状態 SoA**(state)と**mock 専用の合成日課**(schedule)。
C5 で **W16 母集団の読み込みと二層抽出**(population)が加わる。
"""

from shibuya.agents.population import (
    Population,
    load_population,
    population_available,
    sample_population,
)
from shibuya.agents.schedule import MockWeeklySchedule, synthesize
from shibuya.agents.state import (
    N_WAKE_CONDITIONS,
    REFRACTORY_MINUTES,
    RESULT_TEXT,
    WAKE_CONDITION_CLASS,
    Activity,
    AgentKind,
    AgentState,
    MOCK_KIND_COUNT,
    ResultCode,
    WakeCondition,
)

__all__ = [
    "AgentState",
    "AgentKind",
    "Activity",
    "ResultCode",
    "WakeCondition",
    "N_WAKE_CONDITIONS",
    "REFRACTORY_MINUTES",
    "WAKE_CONDITION_CLASS",
    "RESULT_TEXT",
    "MockWeeklySchedule",
    "synthesize",
    "Population",
    "load_population",
    "population_available",
    "sample_population",
    "MOCK_KIND_COUNT",
]
