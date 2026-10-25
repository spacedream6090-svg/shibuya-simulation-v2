"""第 1 期 1-8 J0(1-3 の検収 M2): 出来事の記録の原因の表を列(SoA)にした(受入の試験 ``test_j0_cause_columns``)。

- 列(種類の番号・参照の番号・call_id の 3 つの整数・入力の出来事 id の範囲・選んだ候補の源と提示の番号=検収 M1)+入力の id の
  2 列。1 行 39 B・入力 1 つ 12 B。
- 読み口 ``event(i).cause`` は今の 3 型を組み立てて返す(テープの形の call_id も、そうでない call_id も・入力の id の並び
  まで)。実験の条件は口 ``gate.admit`` が作った物を返す(口の外では作らない)。
- 同じ原因の行は 1 つ: 過程と実験は名で・LLM の呼び出しは直前と同じときだけ。保持窓で詰め直しても読み返しが崩れない
  (無作為の書き込みと素朴な写しの突き合わせ)。種類の分布は詰め直しの前後で同じ。
- 呼び出しごとの Python の物を持たない(1 呼あたりの保持バイトが 1-3 の 198 B より十分小さい)。
- 腕 port のランの判断の出来事の原因は ``LlmCall(call_id, source=選んだ源, number=提示の番号)``=call_id はテープの call_id・
  源と番号の分布は口の計器と同じ(検収 M1)。1-3 の既存の試験(``tests/engine/events``)はそのまま通る(全体の試験で回す)。
- 成長の宣言: 腕 legacy は今のまま・腕 port は判断の出来事の行を足す(検収 L2)。
"""

from __future__ import annotations

import gc
import random
import tracemalloc

import pytest

from shibuya.core.time_consts import NS_PER_STEP, STEPS_PER_DAY
from shibuya.engine.events import log as EV
from shibuya.engine.events import vocab as V
from shibuya.engine.experiment import gate as GATE
from shibuya.engine.run import run_day

from tests.engine.decision._j0 import SMALL, decision_arm


def test_column_widths():
    assert EV.CAUSE_ROW_BYTES == 39 and EV.INPUT_ID_BYTES == 12 and EV.ROW_BYTES == 72
    log = EV.EventLog()
    assert log.n_causes == 0 and log.cause_nbytes == 0
    for name in ("_ev_causes", "_ev_cause_codes"):
        assert not hasattr(log, name)


def test_round_trip_of_the_three_kinds():
    log = EV.EventLog()
    log.begin_step(NS_PER_STEP)
    causes = [
        EV.LlmCall("60:12:3", ((0, 0), (NS_PER_STEP, 4))),
        EV.LlmCall("60:12:-1"),
        EV.LlmCall("call-x", ((7, 1),)),          # テープの形でない call_id
        EV.LlmCall("060:12:3"),                   # 先頭の 0=テープの形でない(組み立て直しで同じ文字列)
        EV.LlmCall("61:12:3", source="affordance", number=13),  # 検収 M1: 選んだ源と提示の番号
        EV.Process("rail"),
        EV.Process("day_close"),
    ]
    ids = [log.append(EV.Event(t_ns=NS_PER_STEP, who=1, what="行為:移動", cause=c)) for c in causes]
    got = [log.get(i).cause for i in ids]
    assert got == causes and [type(g) for g in got] == [type(c) for c in causes]
    assert log.cause_nbytes == log.n_causes * 39 + 3 * 12
    eid = GATE.admit(log, "cond-A", what="過程:opening", who="engine", origin="実験")
    exp = log.get(eid).cause
    assert type(exp) is EV.Experiment and exp.cond_id == "cond-A"
    assert log.cause_counts() == {"llm_call": 5, "process": 2, "experiment": 1}
    assert got[4].source == "affordance" and got[4].number == 13 and got[0].source is None and got[0].number is None


@pytest.mark.parametrize("kw", [dict(source="menu"), dict(number=0), dict(number=128), dict(number=True),
                                dict(number=1.5)])
def test_llm_call_source_and_number_are_checked(kw):
    with pytest.raises(ValueError):
        EV.LlmCall("1:2:3", **kw)
    assert EV.CANDIDATE_SOURCES == ("experience", "affordance", "plan", "continue", "deliberate", "vocab")
    from shibuya.engine.decision.port import ALL_SOURCES

    assert tuple(ALL_SOURCES) == EV.CANDIDATE_SOURCES


def test_same_cause_rows_are_merged():
    log = EV.EventLog()
    log.begin_step(0)
    c = EV.LlmCall("5:1:0", ((0, 0),))
    for _ in range(3):
        log.append(EV.Event(t_ns=0, who=1, what="行為:購入", cause=c))  # 続けて同じ呼び出し=1 行
    for _ in range(4):
        log.append(EV.Event(t_ns=0, who="runner.rail", what="過程:rail", cause=EV.Process("rail")))
    log.append(EV.Event(t_ns=0, who=1, what="行為:購入", cause=EV.LlmCall("5:1:0", ((0, 0),))))  # 間が空いても直前と同じ
    assert log.n_causes == 2
    log.append(EV.Event(t_ns=0, who=2, what="行為:購入", cause=EV.LlmCall("5:2:0")))
    log.append(EV.Event(t_ns=0, who=1, what="行為:購入", cause=c))  # 直前と違う=新しい行(呼び出しごとの表を持たない)
    assert log.n_causes == 4
    assert [e.cause for e in log.events()][-1] == c


def test_eviction_keeps_every_live_cause_against_a_naive_copy():
    rnd = random.Random(4)
    log = EV.EventLog(retention_days=2)
    naive: list[tuple[tuple[int, int], object]] = []
    for d in range(5):
        for k in range(30):
            t = (d * STEPS_PER_DAY + k) * NS_PER_STEP
            log.begin_step(t)
            for j in range(rnd.randint(1, 4)):
                r = rnd.random()
                if r < 0.5:
                    m = rnd.randint(0, 3)
                    c = EV.LlmCall(f"{d * STEPS_PER_DAY + k}:{rnd.randint(0, 50)}:{rnd.randint(-1, 3)}",
                                   tuple((rnd.randint(0, 10**12), rnd.randint(0, 9)) for _ in range(m)))
                elif r < 0.6:
                    c = EV.LlmCall(f"txt-{rnd.randint(0, 5)}", ((1, 1),) * rnd.randint(0, 2))
                else:
                    c = EV.Process(rnd.choice(V.PROCESS_NAMES))
                eid = log.append(EV.Event(t_ns=t, who=j, what="過程:rail", cause=c))
                naive.append((eid, c))
        log.close_day(d)
        keep = {(int(t), int(s)) for t, s in zip(*log.ids())}
        live = [(eid, c) for eid, c in naive if eid in keep]
        assert [log.get(eid).cause for eid, _c in live] == [c for _e, c in live]
        kinds: dict[str, int] = {}
        for _e, c in live:
            kinds[c.kind] = kinds.get(c.kind, 0) + 1
        assert log.cause_counts() == kinds
        # 表は生きている行が指す物だけ(過程は名ごとに 1 つ)
        assert log.n_causes <= len(live)
        assert log._ci_n == sum(len(log._cause_at(k).input_event_ids) for k in range(log.n_causes)
                                if log._cause_at(k).kind == "llm_call")


def test_bytes_per_call_are_far_below_the_object_table():
    """1-3 の表(呼び出しごとの Python の物)は 198 B/呼(入力 0 個・HEAD の実測=記録の cause_bytes)。列は 37 B+倍化の余り。"""
    n = 20_000
    gc.collect()
    tracemalloc.start()
    log = EV.EventLog(capacity=n + 16)
    gc.collect()
    base = tracemalloc.get_traced_memory()[0]
    log.begin_step(0)
    for i in range(n):
        log.append(EV.Event(t_ns=0, who=i, what="行為:移動", cause=EV.LlmCall(f"1000:{i}:3")))
    gc.collect()
    held = (tracemalloc.get_traced_memory()[0] - base) / n
    tracemalloc.stop()
    assert held < 100, held


def test_decision_events_carry_the_tape_call_id(tmp_path):
    import pyarrow.parquet as pq

    with decision_arm("port"):
        r = run_day(**SMALL, tape_path=tmp_path / "t")
    log = r.event_log
    rows = [e for e in log.events() if isinstance(e.cause, EV.LlmCall)]
    assert rows and all(e.what.startswith("行為:") and isinstance(e.who, int) for e in rows)
    tape_ids = set(pq.read_table(tmp_path / "t" / "calls.parquet").column("call_id").to_pylist())
    assert {e.cause.call_id for e in rows} <= tape_ids
    for e in rows:
        T, a, _c = e.cause.call_id.split(":")
        assert int(a) == e.who and int(T) * NS_PER_STEP == e.t_ns and e.cause.input_event_ids == ()
    assert log.cause_counts()["llm_call"] == len(rows)


@pytest.mark.parametrize("bad", ["", " "])
def test_llm_call_still_validates(bad):
    with pytest.raises(ValueError):
        EV.LlmCall(bad)


def test_decision_events_carry_the_source_and_the_number():
    """検収 M1(口の約束 1-8 の約束 (3)): 腕 port の判断の出来事を読むと、選んだ候補の源と提示の番号が判断ごとに取れる。
    分布は口の計器(manifest の chosen_by_source・chosen_number)と同じ。"""
    from collections import Counter

    with decision_arm("port"):
        r = run_day(**{**SMALL, "memory": "on", "relations": "on"})
    rows = [e for e in r.event_log.events() if isinstance(e.cause, EV.LlmCall)]
    dp = r.run_manifest_fields()["decision_port"]
    assert rows and dp["events_unlogged"] == 0 and len(rows) == dp["events"] == dp["decisions"]
    assert all(e.cause.source in EV.CANDIDATE_SOURCES and 1 <= e.cause.number <= 13 for e in rows)
    by_src = Counter(e.cause.source for e in rows)
    assert {k: v for k, v in dp["chosen_by_source"].items() if v} == dict(by_src)
    assert dp["chosen_number"] == {str(k): v for k, v in sorted(Counter(e.cause.number for e in rows).items())}
    assert len(by_src) >= 2  # 源が 1 つに偏っていない(続ける・語彙の残り・周りが示すできることほか)


def test_growth_declaration_adds_the_decision_events_only_on_the_port_arm():
    """検収 L2: 成長の宣言=腕 legacy は今のまま・腕 port は判断の出来事の行(出来事の行+原因の表の行)を足す。"""
    from shibuya.engine.decision import layer as DL

    log = EV.EventLog()
    base = log.growth_declaration()
    assert base.per_day_growth_coef == EV.ROW_BYTES and base.growth_per_simday == 1.0
    d = DL.DECISION_EVENT_ROWS_PER_AGENT_DAY
    port = log.growth_declaration(decision_rows_per_agent_day=d)
    assert port.per_day_growth_coef == EV.ROW_BYTES + d * (EV.ROW_BYTES + EV.CAUSE_ROW_BYTES)
    assert port.growth_per_simday == 1.0 + d and "1-8 J0" in port.note and "1-8 J0" not in base.note
    with decision_arm("port"):
        r = run_day(**{**SMALL, "ticks": 60})
    assert r.decision_layer.event_growth() == port
    with pytest.raises(ValueError):
        log.growth_declaration(decision_rows_per_agent_day=-1.0)


def test_check_process_names_round_trip():
    """〔取り込み・検収 H1〕過程の原因の番号は ``Process`` の検査と同じ表 ``V.CAUSE_PROCESS_NAMES``(1-5 の ``rights`` を含む)
    から作る=1-5 の検査の名でも書けて、読み返すと同じ ``Process``。"""
    assert set(V.PROCESS_NAMES) < set(V.CAUSE_PROCESS_NAMES) and "rights" in V.CAUSE_PROCESS_NAMES
    log = EV.EventLog()
    log.begin_step(0)
    ids = [log.append(EV.Event(t_ns=0, who="engine", what="過程:rail", cause=EV.Process(n)))
           for n in V.CAUSE_PROCESS_NAMES]
    assert [log.get(i).cause for i in ids] == [EV.Process(n) for n in V.CAUSE_PROCESS_NAMES]
    assert log.n_causes == len(V.CAUSE_PROCESS_NAMES) and log.cause_counts() == {"process": len(ids)}
