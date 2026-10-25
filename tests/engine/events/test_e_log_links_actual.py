"""第 1 期 1-3 出来事の記録: ActualLog の行と出来事が 1 対 1 に目印で結ばれる(口の約束 1-3 の約束 (2)・受入の試験
``test_e_log_links_actual``)。1-3 で配線した系(世界過程=world・最後の便=close_final)の分。

- 口の単体: ``append``・``append_many`` の行ごとに出来事が 1 行・id の目印が付く・保持窓で行を落としても目印が行に付いたまま。
  口が無い・記録しないときは目印が無い(seq=-1)。
- ランの上(合成の世界・data 無し): ActualLog の生存行の全部に目印があり、目印はどれも記録にある別々の id で、出来事の
  ``what``・``who``・``cause`` は行の過程から決まる値。ActualLog の行の数=過程の出来事の数。
- 世界資産のラン(data あり・200 体): 同じ 1 対 1。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.core.time_consts import NS_PER_STEP, STEPS_PER_DAY
from shibuya.engine.events import log as EV
from shibuya.engine.events.links import ActualLogLink
from shibuya.engine.processes.runner import PROCESS_ORDER
from shibuya.engine.run import run_day
from shibuya.world.processes.actual_log import ActualLog
from shibuya.world.processes.records import DeviationVocab


def _log_with_link(enabled=True):
    ev = EV.EventLog(enabled=enabled)
    al = ActualLog("t", retention_days=1)
    al.event_sink = ActualLogLink(ev, {"rail_operation_static": "rail", "store_opening": "opening"})
    return ev, al


def test_unit_append_and_append_many_link_one_to_one():
    ev, al = _log_with_link()
    ev.begin_step(3 * NS_PER_STEP)
    al.append("rail_operation_static", 7, 3, DeviationVocab.SCHEDULED)
    al.append_many("store_opening", [1, 2, 3], [3, 3, 3], [DeviationVocab.SCHEDULED] * 3)
    t, s = al.event_ids()
    assert len(al) == 4 and len(ev) == 4
    ids = list(zip(t.tolist(), s.tolist()))
    assert ids == [(3 * NS_PER_STEP, k) for k in range(4)]
    got = [ev.get(i) for i in ids]
    assert [g.what for g in got] == ["過程:rail"] + ["過程:opening"] * 3
    assert [g.who for g in got] == ["runner.rail"] + ["runner.opening"] * 3
    assert [g.cause for g in got] == [EV.Process("rail")] + [EV.Process("opening")] * 3


def test_unit_eviction_keeps_the_links_on_their_rows():
    ev, al = _log_with_link()
    for day in range(3):
        T = day * STEPS_PER_DAY + 10
        ev.begin_step(T * NS_PER_STEP)
        al.append_many("rail_operation_static", [day, day + 10], [T, T], [DeviationVocab.SCHEDULED] * 2)
    assert al.evict_expired(2 * STEPS_PER_DAY + 10) == 4  # 保持窓 1 日=日 0・日 1 の 4 行を落とす
    t, s = al.event_ids()
    assert al.rows()["subject_id"].tolist() == [2, 12]
    assert [ev.get((int(a), int(b))).t_ns // NS_PER_STEP for a, b in zip(t, s)] == [2 * STEPS_PER_DAY + 10] * 2


def test_unit_no_sink_or_disabled_means_no_mark():
    al = ActualLog("t")
    al.append("x", 1, 0, DeviationVocab.SCHEDULED)
    assert al.event_ids()[1].tolist() == [-1]
    ev, al2 = _log_with_link(enabled=False)
    al2.append("rail_operation_static", 1, 0, DeviationVocab.SCHEDULED)
    assert al2.event_ids()[1].tolist() == [-1] and len(ev) == 0


def test_unit_unknown_process_id_is_an_error():
    ev, al = _log_with_link()
    with pytest.raises(ValueError, match="実行器の表に無い"):
        al.append("no_such_process", 1, 0, DeviationVocab.SCHEDULED)
    with pytest.raises(ValueError, match="語彙表の外"):
        ActualLogLink(ev, {"x": "not_a_process"})


def _check_one_to_one(res):
    log, ev = res.runner.log, res.event_log
    t, s = log.event_ids()
    assert len(log) > 0 and (s >= 0).all(), "ActualLog の生存行に目印の無い行がある"
    ids = list(zip(t.tolist(), s.tolist()))
    assert len(set(ids)) == len(ids), "2 つの行が同じ出来事を指す"
    key_of = {pid: key for key in PROCESS_ORDER for pid in getattr(res.runner._procs[key], "process_ids", ())}
    names = log.process_ids
    for (tt, ss), row in zip(ids, log.rows()):
        e = ev.get((tt, ss))
        key = key_of[names[int(row["process"])]]
        assert (e.what, e.who, e.cause) == (f"過程:{key}", f"runner.{key}", EV.Process(key))
        assert e.t_ns % NS_PER_STEP == 0
    # 過程の出来事の数(区切り=checkpoint・day_close を除く)=ActualLog に書いた行の数(保持窓の内なので落としていない)
    n_proc = sum(c for w, c in ev.what_counts().items() if w.split(":", 1)[1] in PROCESS_ORDER)
    assert n_proc == log.n_appended == len(log)


def test_run_links_every_actual_log_row():
    res = run_day(n_agents=60, seed=3, n_cells=9, ticks=STEPS_PER_DAY, budget=60.0, vocab_version="v3",
                  checkpoint_every=240)
    _check_one_to_one(res)


@pytest.mark.requires_data("world_v2:w17_schedule.parquet")
def test_real_world_run_links_every_actual_log_row():
    from shibuya import cli

    res = cli.run(n_agents=200, seed=1, world_dir="data/world/v2", vocab_version="v3")
    _check_one_to_one(res)
    whats = res.event_log.what_counts()
    assert whats.get("過程:rail", 0) > 0 and whats.get("過程:opening", 0) > 0  # 鉄道と開閉店の行が実際に入る
