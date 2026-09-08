"""P3 ゲート: イベント処理スループット **≥10万イベント/秒**(予算宣言表 P3)。

100万件の起床を 1,440 tick(=1 シミュ日)へ撒き、全部を取り出して消化するまでの
壁時計から events/s を測る。閾値は**予算表から読む**(コードに数値を複製しない)。
絶対値ゲートは本来セルフホスト機の asv で見る(実装計画書 §6)——本テストは
開発機での回帰検出用。数値は ``-s`` で表示される。
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from shibuya.core.budget import budget_by_id, load_budget_table, parse_limit
from shibuya.engine.scheduler import Scheduler

N_EVENTS = 1_000_000
N_TICKS = 1_440


def _p3_threshold() -> float:
    row = budget_by_id(load_budget_table())["P3"]
    value, unit = parse_limit(row.declared)
    assert unit == "イベント/秒", f"P3 の単位が変わった: {unit!r}"
    return value


@pytest.mark.slow
def test_p3_event_throughput(capsys):
    threshold = _p3_threshold()
    rng = np.random.default_rng(42)
    agents = rng.integers(0, 400_000, N_EVENTS).astype(np.int64)
    ticks = rng.integers(0, N_TICKS, N_EVENTS).astype(np.int64)
    offsets = rng.integers(200_000_000, 1_500_000_000, N_EVENTS).astype(np.int64)
    classes = rng.integers(0, 4, N_EVENTS).astype(np.int64)

    s = Scheduler(run_salt=b"p3-gate")
    t0 = time.perf_counter()
    s.schedule_many(agents, ticks, offsets, classes)
    t1 = time.perf_counter()
    drained = 0
    for t in range(N_TICKS):
        drained += int(s.due(t).size)
        s.consume(t)
    t2 = time.perf_counter()

    schedule_rate = N_EVENTS / (t1 - t0)
    drain_rate = drained / (t2 - t1)
    e2e_rate = N_EVENTS / (t2 - t0)
    with capsys.disabled():
        print(
            f"\n[P3] 予約 {schedule_rate:,.0f}/s ・ 取り出し {drain_rate:,.0f}/s ・ "
            f"通し {e2e_rate:,.0f} events/s (閾値 {threshold:,.0f}/s ・ {N_EVENTS:,}件/{N_TICKS} tick)"
        )
    assert drained == N_EVENTS
    assert s.pending == 0
    assert e2e_rate >= threshold, f"P3 未達: {e2e_rate:,.0f} events/s < {threshold:,.0f}"
