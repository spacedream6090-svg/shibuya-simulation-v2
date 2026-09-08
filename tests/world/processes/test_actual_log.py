"""追記専用 ActualLog: 追記・増分索引・保持窓と日次集約・遵守率・成長宣言(D-R2-6)。"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.core.growth import check_growth
from shibuya.world.processes import first_batch as FB
from shibuya.world.processes.actual_log import (
    ACTUAL_LOG_DTYPE,
    ENTRIES_PER_SUBJECT_PER_DAY,
    RAW_ROW_BYTES,
    RETENTION_DAYS,
    TICKS_PER_DAY,
    ActualLog,
    plan_compliance,
)
from shibuya.world.processes.records import DeviationVocab


def _log(**kw) -> ActualLog:
    return ActualLog("actual_log", **kw)


# ---------------------------------------------------------------- 固定幅レコード
def test_dtype_is_fixed_width_and_frozen():
    assert ACTUAL_LOG_DTYPE.names == (
        "subject_id",
        "tick",
        "process",
        "deviation",
        "delay_min",
    )
    assert ACTUAL_LOG_DTYPE.itemsize == 23
    assert RAW_ROW_BYTES == 31  # レコード23 + 索引8


# ---------------------------------------------------------------- 追記
def test_append_and_entries():
    log = _log()
    e = log.append("rail", 7, 100, DeviationVocab.SCHEDULED)
    assert (e.entry_id, e.subject_id, e.tick) == (0, 7, 100)
    log.append("rail", 8, 101, DeviationVocab.DELAY, 4)
    assert len(log) == 2 and log.n_appended == 2
    rows = log.entries()
    assert rows[1].deviation is DeviationVocab.DELAY and rows[1].delay_minutes == 4
    assert log.max_tick == 101


def test_append_rejects_bad_delay():
    log = _log()
    with pytest.raises(ValueError):
        log.append("rail", 1, 1, DeviationVocab.CANCELED, 5)


def test_rows_view_is_read_only():
    log = _log()
    log.append("rail", 1, 1, DeviationVocab.SCHEDULED)
    with pytest.raises(ValueError):
        log.rows()["tick"][0] = 9


def test_append_many_is_vectorized():
    log = _log()
    n = log.append_many(
        "rail",
        np.arange(5),
        np.arange(5) + 10,
        [DeviationVocab.SCHEDULED] * 5,
    )
    assert n == 5 and len(log) == 5
    assert log.rows_for("rail")["subject_id"].tolist() == [0, 1, 2, 3, 4]


def test_append_many_checks_delay_rule():
    log = _log()
    with pytest.raises(ValueError, match="DELAY"):
        log.append_many("rail", [1], [1], [DeviationVocab.SCHEDULED], [3])
    with pytest.raises(ValueError, match="長さ"):
        log.append_many("rail", [1, 2], [1], [DeviationVocab.SCHEDULED])


def test_capacity_grows():
    log = _log(capacity=2)
    for i in range(10):
        log.append("rail", i, i, DeviationVocab.SCHEDULED)
    assert len(log) == 10
    assert log.rows()["subject_id"].tolist() == list(range(10))


# ---------------------------------------------------------------- 増分索引
def test_index_is_per_process_and_incremental():
    log = _log()
    log.append("rail", 1, 1, DeviationVocab.SCHEDULED)
    log.append("bus", 2, 2, DeviationVocab.SCHEDULED)
    log.append("rail", 3, 3, DeviationVocab.SCHEDULED)
    assert log.index_for("rail").tolist() == [0, 2]
    assert log.index_for("bus").tolist() == [1]
    assert log.index_for("missing").size == 0
    assert log.rows_for("rail")["subject_id"].tolist() == [1, 3]


# ---------------------------------------------------------------- 保持窓と日次集約
def test_evict_folds_old_days_into_daily_counts():
    log = _log(retention_days=RETENTION_DAYS)
    # 10日ぶん・1日1件
    for day in range(10):
        log.append("rail", day, day * TICKS_PER_DAY + 5, DeviationVocab.SCHEDULED)
    now = 9 * TICKS_PER_DAY + 100
    dropped = log.evict_expired(now)
    assert dropped == 3  # cutoff_day = 9-7+1 = 3 → day 0,1,2 を畳む
    assert len(log) == 7
    counts = log.daily_counts("rail")
    assert set(counts) == {0, 1, 2}
    assert counts[0][0] == 1  # SCHEDULED が1件
    assert log.n_appended == 10  # 追記総数は減らない


def test_evict_remaps_the_index():
    log = _log(retention_days=1)
    log.append("rail", 1, 0, DeviationVocab.SCHEDULED)  # day 0
    log.append("bus", 2, 0, DeviationVocab.SCHEDULED)  # day 0
    log.append("rail", 3, TICKS_PER_DAY + 1, DeviationVocab.SCHEDULED)  # day 1
    log.evict_expired(TICKS_PER_DAY + 10)
    assert len(log) == 1
    assert log.index_for("rail").tolist() == [0]
    assert log.index_for("bus").tolist() == []
    assert log.rows_for("rail")["subject_id"].tolist() == [3]


def test_evict_is_a_noop_without_retention():
    log = _log(retention_days=None)
    log.append("rail", 1, 0, DeviationVocab.SCHEDULED)
    assert log.evict_expired(100 * TICKS_PER_DAY) == 0
    assert len(log) == 1


# ---------------------------------------------------------------- 遵守率
def test_compliance_rate_is_the_scheduled_share():
    log = _log()
    for i in range(8):
        log.append("rail", i, 10 + i, DeviationVocab.SCHEDULED)
    log.append("rail", 8, 20, DeviationVocab.CANCELED)
    log.append("rail", 9, 21, DeviationVocab.DELAY, 5)
    r = log.compliance_rate("rail")
    assert (r.n_total, r.n_scheduled) == (10, 8)
    assert r.rate == pytest.approx(0.8)
    assert r.by_deviation == {"SCHEDULED": 8, "CANCELED": 1, "DELAY": 1}


def test_compliance_rate_windowed():
    log = _log()
    log.append("rail", 1, 0, DeviationVocab.CANCELED)
    log.append("rail", 2, 100, DeviationVocab.SCHEDULED)
    r = log.compliance_rate("rail", window_ticks=10, now_tick=100)
    assert (r.n_total, r.n_scheduled) == (1, 1) and r.rate == 1.0


def test_compliance_rate_counts_aggregated_days():
    """保持窓で畳まれた日も数え落とさない(集約の意味が守られる)。"""
    log = _log(retention_days=2)
    for day in range(5):
        log.append("rail", day, day * TICKS_PER_DAY + 1, DeviationVocab.SCHEDULED)
    log.append("rail", 99, 4 * TICKS_PER_DAY + 2, DeviationVocab.CANCELED)
    log.evict_expired(4 * TICKS_PER_DAY + 10)
    assert len(log) < 6
    r = log.compliance_rate("rail")
    assert r.n_total == 6 and r.n_scheduled == 5
    assert r.from_aggregate > 0 and r.from_raw > 0
    without = log.compliance_rate("rail", include_aggregate=False)
    assert without.n_total == r.from_raw


def test_compliance_rate_is_nan_without_observations():
    r = _log().compliance_rate("rail")
    assert r.n_total == 0 and r.rate != r.rate  # NaN


def test_plan_compliance_uses_realizes_relations():
    reg = FB.build_registry()
    log = _log()
    log.append("rail_operation_static", 1, 10, DeviationVocab.SCHEDULED)
    log.append("rail_operation_static", 2, 11, DeviationVocab.SKIPPED)
    spec = reg.plan_spec("plan.rail_timetable")
    r = plan_compliance(log, spec, reg.relations)
    assert r.process_ids == ("rail_operation_static",)
    assert r.rate == pytest.approx(0.5)


def test_plan_compliance_without_realizes_raises():
    reg = FB.build_registry()
    spec = reg.plan_spec("plan.rail_timetable")
    with pytest.raises(ValueError, match="realizes"):
        plan_compliance(_log(), spec, [])


# ---------------------------------------------------------------- 成長宣言(D-R2-6)
def test_growth_declarations_have_retention_and_a_fold_target():
    decls = _log().growth_declarations()
    raw = decls["actual_log_raw"]
    agg = decls["actual_log_daily"]
    assert raw.retention.days == RETENTION_DAYS
    assert "actual_log_daily" in raw.retention.target
    assert raw.order == "O(N)"  # 1日あたり増分。累積は coef×N×D = O(N·t)
    assert agg.order == "O(1)"
    assert raw.declared_projected_bytes(30, n_entities=1000) < raw.cap


def test_24step_smoke_extrapolates_within_cap():
    """D-R2-6 のゲート: 24step スモークの実測を 1日/30日 へ外挿して cap と突き合わせる。"""
    n_subjects = 1_500
    steps = 24
    log = _log()
    # 宣言どおりの発生率(1対象1日 ENTRIES_PER_SUBJECT_PER_DAY 件)を 24 分ぶん出す。
    n_rows = int(round(n_subjects * ENTRIES_PER_SUBJECT_PER_DAY * steps / TICKS_PER_DAY))
    log.append_many(
        "rail_operation_static",
        np.arange(n_rows) % n_subjects,
        np.arange(n_rows) % steps,
        np.zeros(n_rows, dtype=np.int8),  # SCHEDULED
    )
    measured = {"actual_log_raw": log.nbytes, "actual_log_daily": 0}
    report = check_growth(
        log.growth_declarations(),
        measured,
        steps=steps,
        minutes_per_step=1,
        horizon_days=30,
        n_entities=n_subjects,
        declared_tolerance=1.05,
    )
    assert report.ok, report.as_text()
    assert report.over_declared == ()
    raw = next(r for r in report.rows if r.name == "actual_log_raw")
    assert raw.effective_days == RETENTION_DAYS  # 保持窓が効いている(30日ではない)
    assert raw.measured_over_declared == pytest.approx(1.0, rel=0.02)


def test_growth_gate_fails_when_the_log_grows_faster_than_declared():
    log = _log()
    decls = dict(log.growth_declarations())
    report = check_growth(
        decls,
        {"actual_log_raw": 10**12, "actual_log_daily": 0},
        steps=24,
        minutes_per_step=1,
        n_entities=1_500,
    )
    assert not report.ok and "actual_log_raw" in report.over_cap
