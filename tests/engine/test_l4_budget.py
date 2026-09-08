"""予算行 **L4**(上限 400 万呼/日 = 憲法1の監査点)の硬い上限。

正典
- 予算宣言表 **L4**: 「上限400万呼/日(o64)/**平均10呼/体/日が繰り延べアービタの制御目標**」。
- 知覚契約書 §6: 4クラス固定優先(会話ターン > 計画境界 > 個体変化 > セル変化)+縮退。

**バグ(2026-09-08 修正)**
    実データ 5,000 体・1 日のランは **56,488 呼 = 11.30 呼/体/日** で、按分上限 50,000 呼
    (``call_budget_per_tick(5000) × 1440``)を 13% 超えていた。原因は
    ``engine.arbiter.arbitrate`` が縮退実行を ``cost=0.5`` として累積コストで切っていたこと
    (縮退呼 2 件で 1 枠 → 呼数は上限の最大 2 倍)。縮退が減らすのは 1 呼あたりの
    トークン/計算量であって**呼の本数ではない**。修正後は呼数で必ず頭打ちになる。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya.core.types import EventClass
from shibuya.engine.arbiter import (
    DEGRADE_COST_FACTOR,
    POOL_CAP_TICKS,
    Arbiter,
    WakeCandidates,
    arbitrate,
    call_budget_per_tick,
)
from shibuya.engine.run import run_day
from shibuya.world.state import World

WORLD_DIR = Path("data/world/v2")
real_data = pytest.mark.skipif(
    not (WORLD_DIR / "w12_timetables.parquet").exists(), reason="実世界資産 data/world/v2 が無い"
)
SALT = b"l4-salt"


def _cands(ids, classes):
    a = np.asarray(ids, dtype=np.int64)
    return WakeCandidates(
        a,
        np.full(a.size, 10, dtype=np.int8),
        np.asarray([int(c) for c in classes], dtype=np.int64),
        np.zeros(a.size, dtype=np.int64),
    )


# ---------------------------------------------------------------- 純関数の側
def test_degraded_calls_no_longer_double_the_budget():
    c = _cands(list(range(40)), [EventClass.CELL] * 40)
    d = arbitrate(c, tick=0, budget=10.0, run_salt=SALT)
    assert d.n_calls == 10
    assert d.n_calls * DEGRADE_COST_FACTOR < 10.0  # コスト基準では 20 件通っていた


def test_a_tick_never_exceeds_the_floor_of_the_budget():
    for budget in (0.0, 0.5, 1.0, 3.7, 34.72):
        c = _cands(list(range(200)), [EventClass.CELL] * 200)
        d = arbitrate(c, tick=0, budget=budget, run_salt=SALT)
        assert d.n_calls <= int(np.floor(budget + 1e-9))


def test_the_daily_sum_never_exceeds_the_budget_times_ticks():
    """端数を繰り越しても Σ呼 ≤ Σ予算(繰越の在庫は 2 tick ぶんで頭打ち)。"""
    budget = call_budget_per_tick(5_000)
    arb = Arbiter(5_000, SALT, budget)
    total = 0
    for t in range(1_440):
        # 毎 tick 常に飽和させる(需要 > 予算)
        c = _cands(list(range(200)), [EventClass.CELL] * 200)
        total += arb.step(t, c).n_calls
    assert total <= int(budget * 1_440)
    assert total >= int(budget * 1_440) - 2  # 端数の繰越で上限にほぼ張り付く
    assert arb._pool <= budget * POOL_CAP_TICKS


def test_conversation_keeps_priority_inside_the_hard_cap():
    """会話ターンは固定優先の先頭=上限が効いても最優先で通る(設計どおり呼の 45%)。"""
    ids = list(range(30))
    classes = [EventClass.CELL] * 20 + [EventClass.CONVERSATION] * 10
    d = arbitrate(_cands(ids, classes), tick=0, budget=10.0, run_salt=SALT)
    assert d.n_calls == 10
    assert set(d.selected.agent_id.tolist()) == set(range(20, 30))


# ---------------------------------------------------------------- ランの側
def _cap(n_agents: int, ticks: int) -> int:
    return int(call_budget_per_tick(n_agents) * ticks)


def test_synthetic_run_stays_within_the_l4_cap():
    res = run_day(n_agents=5_000, seed=1, ticks=1_440, checkpoint_every=720, n_cells=139)
    assert res.llm_calls <= _cap(5_000, 1_440)
    assert res.llm_calls / 5_000 <= 10.0
    # 録画テープの成長宣言(L4 の平均 10 呼/体/日で O(N))を超えない
    assert res.growth_report is not None and res.growth_report.ok
    assert "tape_rows" not in res.growth_report.over_declared
    assert "tape_rows" not in res.growth_report.over_cap


@real_data
@pytest.mark.slow
def test_real_world_run_stays_within_the_l4_cap(capsys):
    world = World.load(WORLD_DIR)
    res = run_day(
        n_agents=5_000, seed=1, world=world, ticks=1_440, checkpoint_every=720,
        world_dir=WORLD_DIR,
    )
    cap = _cap(5_000, 1_440)
    with capsys.disabled():
        print(
            f"\n[L4] 実データ 5,000体×1日: {res.llm_calls:,} 呼 = "
            f"{res.llm_calls / 5_000:.2f} 呼/体/日 (上限 {cap:,} 呼 = 10.00 呼/体/日)"
        )
    assert res.llm_calls <= cap
    assert res.growth_report is not None and res.growth_report.ok
