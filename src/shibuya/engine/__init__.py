"""engine: 時計/スケジューラ/繰り延べアービタ/resolve/二相コミット=世界状態への唯一の書き込み口。

層契約: docs/design/v2-implementation-plan.md §3(import-linter で強制)。
本パッケージが engine から外へ出す名前をここに集約する。
C2 第1弾=時計・スケジューラ・繰り延べ待ち行列・録画テープ。
C2 第2弾=変化検出(P6)・繰り延べアービタの裁定規則・二相コミット(Phase A/B)・
resolve(Phase C=唯一の書き手)・1シミュ日ラン(W2)・状態成長宣言(D-R2-6)。
"""

from shibuya.engine.arbiter import (
    Arbiter,
    ArbiterDecision,
    WakeCandidates,
    arbitrate,
    call_budget_per_tick,
)
from shibuya.engine.change_detect import ChangeDetector, DetectResult
from shibuya.engine.clock import SimClock
from shibuya.engine.commit import (
    ACTION_CODES,
    ACTION_WORDS,
    ENGINE_STEP,
    CommitPlan,
    IntentBatch,
    ResourceSpace,
    arbitrate_resources,
    parse_action,
)
from shibuya.engine.scheduler import (
    DIAG_COLUMNS,
    HORIZON_TICKS,
    DeferralQueue,
    Scheduler,
    TickState,
    coalesce_agents,
    order_indices,
    ordered_events,
    scheduler,
)
from shibuya.engine.tape import Replay, Tape, TapeMiss, TapeRow, TapeWriter

__all__ = [
    # C2 第1弾
    "SimClock",
    "Scheduler",
    "TickState",
    "scheduler",
    "order_indices",
    "ordered_events",
    "coalesce_agents",
    "DeferralQueue",
    "DIAG_COLUMNS",
    "HORIZON_TICKS",
    "Tape",
    "TapeWriter",
    "TapeRow",
    "Replay",
    "TapeMiss",
    # C2 第2弾
    "ChangeDetector",
    "DetectResult",
    "Arbiter",
    "ArbiterDecision",
    "WakeCandidates",
    "arbitrate",
    "call_budget_per_tick",
    "IntentBatch",
    "ResourceSpace",
    "CommitPlan",
    "arbitrate_resources",
    "parse_action",
    "ACTION_WORDS",
    "ACTION_CODES",
    "ENGINE_STEP",
]
