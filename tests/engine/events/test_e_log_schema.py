"""第 1 期 1-3 出来事の記録: ``Event`` の欄・凍結・id の決定性(口の約束 1-3 の受入の試験 ``test_e_log_schema``)。

- 欄の名と順は口の約束のとおり(``id``・``t_ns``・``who``・``what``・``whom``・``where``・``how_much``・``via``・
  ``received_ns``・``read_ns``・``origin``・``cause``)。凍結(書き換えると落ちる)・``__slots__``。
- id は ``(t_ns, seq)``: 同じ時刻の中で 0 から通し・刻みが進むと 0 から。書き手は id を付けない(付けた行は書けない)。
- 同じランを 2 回回すと同じ id の列(決定的)。刻みの境目からの再開のランの id は、通しのランの同じ時刻からの id と同じ。
- 日の締めの計器(行数・バイト・種類の分布)と保持窓(古い行を落とし、原因の表を詰め直す)。
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from shibuya.core.time_consts import NS_PER_STEP, STEPS_PER_DAY
from shibuya.engine.events import log as EV
from shibuya.engine.events import vocab as V
from shibuya.engine.run import run_day

CONTRACT_FIELDS = ("id", "t_ns", "who", "what", "whom", "where", "how_much", "via", "received_ns", "read_ns",
                   "origin", "cause")
PROC = EV.Process("rail")
W = "過程:rail"


def _ev(**kw):
    base = dict(t_ns=0, who="runner.rail", what=W, cause=PROC)
    base.update(kw)
    return EV.Event(**base)


def test_fields_follow_the_contract():
    assert EV.EVENT_FIELDS == CONTRACT_FIELDS
    assert tuple(f.name for f in dataclasses.fields(EV.Event)) == CONTRACT_FIELDS
    e = _ev()
    assert (e.id, e.whom, e.where, e.how_much, e.via, e.received_ns, e.read_ns, e.origin) == (
        None, None, None, None, "無し", None, None, None)


def test_event_is_frozen_and_slotted():
    e = _ev()
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.what = "過程:opening"  # type: ignore[misc]
    assert not hasattr(e, "__dict__")
    log = EV.EventLog()
    assert not hasattr(log, "__dict__")
    with pytest.raises(AttributeError):
        log.extra = 1  # type: ignore[attr-defined]


def test_ids_are_time_and_sequence():
    log = EV.EventLog()
    t1, t2 = 5 * NS_PER_STEP, 6 * NS_PER_STEP
    log.begin_step(t1)
    a = [log.append(_ev(t_ns=t1)) for _ in range(3)]
    log.begin_step(t2)
    b = [log.append(_ev(t_ns=t2)) for _ in range(2)]
    assert a == [(t1, 0), (t1, 1), (t1, 2)] and b == [(t2, 0), (t2, 1)]
    assert sorted(a + b) == a + b  # 並べると時刻順
    t, s = log.ids()
    assert list(zip(t.tolist(), s.tolist())) == a + b
    assert log.get((t1, 1)).id == (t1, 1) and log.index_of((t2, 5)) == -1


def test_writer_cannot_set_the_id_or_write_into_the_past():
    log = EV.EventLog()
    log.begin_step(10 * NS_PER_STEP)
    with pytest.raises(ValueError, match="id"):
        log.append(_ev(id=(10 * NS_PER_STEP, 0), t_ns=10 * NS_PER_STEP))
    with pytest.raises(ValueError, match="前"):
        log.append(_ev(t_ns=9 * NS_PER_STEP))
    with pytest.raises(TypeError):
        log.append({"t_ns": 0})  # type: ignore[arg-type]
    eid = log.append(_ev(t_ns=10 * NS_PER_STEP))
    back = log.get(eid)
    with pytest.raises(ValueError, match="id"):
        log.append(back)  # 読み返した行は書き戻せない


def test_round_trip_of_every_field():
    log = EV.EventLog()
    log.begin_step(NS_PER_STEP)
    e = _ev(t_ns=NS_PER_STEP, who=12, what="行為:会話", whom="runner.shelf", where=("poi", 7), how_much=-350,
            via="メッセージ", received_ns=2 * NS_PER_STEP, read_ns=3 * NS_PER_STEP, origin="範囲の外",
            cause=EV.LlmCall("60:12:3", ((0, 0), (NS_PER_STEP, 4))))
    eid = log.append(e)
    got = log.get(eid)
    assert got == dataclasses.replace(e, id=eid)
    assert got.cause.input_event_ids == ((0, 0), (NS_PER_STEP, 4))


@pytest.mark.parametrize("kw,err", [
    (dict(t_ns=-1), ValueError), (dict(t_ns=True), ValueError), (dict(t_ns=1.5), ValueError),
    (dict(who=-3), ValueError), (dict(who=""), ValueError), (dict(who=None), ValueError),
    (dict(whom=-1), ValueError), (dict(where=("room", 1)), ValueError), (dict(where=("cell", -1)), ValueError),
    (dict(how_much=1.5), ValueError), (dict(via="手紙"), ValueError),
    (dict(t_ns=10, received_ns=5), ValueError), (dict(read_ns=20), ValueError),
    (dict(received_ns=20, read_ns=10), ValueError), (dict(origin=""), ValueError),
    (dict(cause=None), TypeError), (dict(cause="rail"), TypeError),
])
def test_invalid_fields_are_rejected(kw, err):
    with pytest.raises(err):
        _ev(**kw)


def test_numpy_integers_are_normalized():
    e = _ev(t_ns=np.int64(NS_PER_STEP), who=np.int32(4), how_much=np.int64(9), where=("cell", np.int64(3)))
    assert type(e.t_ns) is int and type(e.who) is int and type(e.how_much) is int and type(e.where[1]) is int


def test_disabled_log_writes_nothing():
    log = EV.EventLog(enabled=False)
    assert log.append(_ev()) is None and len(log) == 0
    rec = log.close_day(0)
    assert rec["on"] is False and rec["rows"] == 0


def test_close_day_counts_and_retention():
    log = EV.EventLog(retention_days=2)
    per_day = []
    for d in range(4):
        n = 0
        for k in range(3):
            t = (d * STEPS_PER_DAY + k) * NS_PER_STEP
            log.begin_step(t)
            log.append(_ev(t_ns=t, cause=EV.LlmCall(f"{d}:{k}:0")))  # 原因は呼び出しごとに 1 つ
            log.append(_ev(t_ns=t, what="金:賃金", how_much=100))
            n += 2
        rec = log.close_day(d)
        per_day.append(rec)
        assert rec["rows"] == n and rec["bytes"] == n * EV.ROW_BYTES
        assert rec["by_what"] == {W: 3, "金:賃金": 3} and rec["by_cause"] == {"llm_call": 3, "process": 3}
    # 保持窓 2 日: 日 2 の締めで日 0 の 6 行・日 3 の締めで日 1 の 6 行を落とす
    assert [r["evicted"] for r in per_day] == [0, 0, 6, 6]
    assert len(log) == 12 and log.n_appended == 24 and log.n_evicted == 12
    days = {int(t) // EV.NS_PER_DAY for t in log.ids()[0]}
    assert days == {2, 3}
    # 原因の表は生きている行の分だけ(LLM の呼び出し 6 つ+過程 1 つ)・読み返しが崩れていない
    assert log.n_causes == 7
    assert {e.cause.call_id for e in log.events() if isinstance(e.cause, EV.LlmCall)} == {
        f"{d}:{k}:0" for d in (2, 3) for k in range(3)}


# ================================================================= ランの上での決定性
KW = dict(n_agents=60, seed=3, n_cells=9, ticks=720, budget=60.0, vocab_version="v3", checkpoint_every=120)


def _rows(log):
    return [(e.id, e.what, e.who, e.cause) for e in log.events()]


def test_same_run_gives_the_same_ids():
    a, b = run_day(**KW), run_day(**KW)
    assert a.final_hash == b.final_hash
    ra, rb = _rows(a.event_log), _rows(b.event_log)
    assert ra == rb and len(ra) > 0
    # E(診断)の区切りの行: checkpoint の数と日の締めの数
    whats = [w for _i, w, _p, _c in ra]
    assert whats.count("過程:checkpoint") == len(a.checkpoints)
    assert whats.count("過程:day_close") == 1


def test_resume_at_a_step_boundary_gives_the_same_ids(tmp_path):
    kw = dict(KW, ticks=STEPS_PER_DAY, sim_days=2)
    straight = run_day(**kw)
    stop = STEPS_PER_DAY + 300
    first = run_day(state_out=tmp_path / "s", stop_at_tick=stop, **kw)
    path = tmp_path / "s" / first.resume["state_files"][-1]["file"]
    resumed = run_day(resume_from=path, **kw)
    assert resumed.final_hash == straight.final_hash
    t0 = stop * NS_PER_STEP
    tail = [r for r in _rows(straight.event_log) if r[0][0] >= t0]
    got = _rows(resumed.event_log)
    assert got == tail and len(got) > 0


def test_row_bytes_and_growth_declaration():
    """1 行のバイト(列の型の和)と D-R2-6 の 5 欄の宣言(1-3 の見込み=expedient・ランの成長の報告にはまだ載せない)。"""
    assert EV.ROW_BYTES == 72
    log = EV.EventLog()
    d = log.growth_declaration(rows_per_agent_day=5.2)
    assert d.name == "event_log" and d.per_day_growth == "O(N)" and d.retention.days == EV.RETENTION_DAYS == 7
    assert d.bytes_per_unit == EV.ROW_BYTES and d.mechanism is False
