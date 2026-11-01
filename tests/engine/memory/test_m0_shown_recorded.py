"""第 1 期 1-6 記憶の器 M0: 録画(MR16)=見せた記憶の行の記録(口の約束 1-6 の約束 (3)・``test_m0_shown_recorded``)。

- 腕 on: 描き方が B5 に載せた記憶の行ごとに、器の行に「最後に見せた時刻」を付け、テープに列 ``recalled_event_ids``
  (``recalled_rows`` と同じ並びの目印 ``"t_ns:seq"``・器の外の店の行は空文字)を 1 つ足す。テープの版は 4 のまま。
- 腕 off(既定): テープの列は版 4 の 21 列のまま(列を足さない)。列の無いテープを読むと空で埋める。
- テープの書き手の口(``TapeWriter.arm_columns``)は閉じた表(``ARM_COLUMNS``)の名だけ。
"""

from __future__ import annotations

import pyarrow.parquet as pq
import pytest

from shibuya.core.time_consts import NS_PER_STEP
from shibuya.engine.run import run_day
from shibuya.engine.tape import (
    ARM_COLUMNS,
    CALLS_FILENAME,
    CALLS_SCHEMA,
    TAPE_SCHEMA_VERSION,
    Replay,
    Tape,
    TapeRow,
    TapeWriter,
)

from tests.engine.memory._m0 import KW, run_with_arm


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("m0_shown")
    on = run_with_arm("events", run_day, tape_path=tmp / "on", **KW)
    off = run_with_arm("mem", run_day, tape_path=tmp / "off", **KW)
    return on, off, tmp


def test_arm_on_adds_one_column_inside_version_4(runs):
    on, off, tmp = runs
    s_on = pq.read_schema(tmp / "on" / CALLS_FILENAME)
    s_off = pq.read_schema(tmp / "off" / CALLS_FILENAME)
    assert s_off.names == CALLS_SCHEMA.names and len(s_off.names) == 21
    assert s_on.names == CALLS_SCHEMA.names + ["recalled_event_ids"]
    assert Tape(tmp / "on").schema_version == Tape(tmp / "off").schema_version == TAPE_SCHEMA_VERSION
    assert (on.final_hash, on.llm_calls) == (off.final_hash, off.llm_calls)
    t_on, t_off = Tape(tmp / "on"), Tape(tmp / "off")
    for name in CALLS_SCHEMA.names:  # 既存の列は 1 つも動かない
        assert t_on.column(name) == t_off.column(name), name
    assert t_off.column("recalled_event_ids") == [[] for _ in range(len(t_off))]  # 列の無いテープは空で読む
    assert len(Replay(tmp / "on")) == len(Replay(tmp / "off"))


def test_event_ids_follow_the_recalled_rows(runs):
    on, _off, tmp = runs
    t = Tape(tmp / "on")
    n_rows = int(on.memory_summary["memory_store"]["n_rows"])
    shown = 0
    shop = 0
    for agent, step, rows, ids in zip(t.column("agent_id"), t.column("tick"), t.column("recalled_rows"),
                                      t.column("recalled_event_ids")):
        assert len(rows) == len(ids)
        for r, s in zip(rows, ids):
            if r >= n_rows:  # 器の外(7c の店の評価の行)
                assert s == ""
                shop += 1
                continue
            t_ns, seq = (int(x) for x in s.split(":"))
            assert seq >= 0  # 〔第 2 期 2-3〕記録の出来事の id(前は仮の出来事=seq は −1−番地)
            assert 0 <= t_ns <= int(step) * NS_PER_STEP  # 見せた記憶はその呼び出しより前の出来事
            shown += 1
    assert shown > 0 and shop > 0
    c = on.memory_summary["memory_store"]["counts"]
    assert c["shown_rows"] == shown and c["tape_rows"] == len(t) == on.llm_calls
    assert c.get("tape_rows_without_shown", 0) == 0 and on.memory_summary["memory_store"]["tape_pending"] == 0
    assert c["shown_calls"] == on.llm_calls


def test_last_shown_time_matches_the_tape(runs, monkeypatch):
    """器の「最後に見せた時刻」=テープでその行(同じ目印)を見せた最後の呼び出しの時刻。"""
    from shibuya.engine.memory import MemoryLayer

    seen = {}
    orig = MemoryLayer.after_tick

    def after_tick(self, agents, tick, **kw):  # noqa: ANN001, ANN202
        seen["layer"] = self
        return orig(self, agents, tick, **kw)

    monkeypatch.setattr(MemoryLayer, "after_tick", after_tick)
    _on, _off, tmp = runs
    run_with_arm("events", run_day, tape_path=tmp / "again", **KW)
    ms = seen["layer"].memory_store
    t = Tape(tmp / "again")
    last: dict[tuple[int, int], tuple[int, str]] = {}
    for agent, step, rows, ids in zip(t.column("agent_id"), t.column("tick"), t.column("recalled_rows"),
                                      t.column("recalled_event_ids")):
        for r, s in zip(rows, ids):
            if r < ms.n_rows:
                last[(int(agent), int(r))] = (int(step), s)
    checked = 0
    for (a, r), (step, s) in last.items():
        eid = ms.event_id(a, r)
        if eid is not None and f"{eid[0]}:{eid[1]}" == s:  # 見せた後に重ねて目印が動いた行は比べない
            assert ms.shown_ns(a, r) == step * NS_PER_STEP
            checked += 1
    assert checked > 0


def test_tape_writer_arm_columns_are_a_closed_table(tmp_path):
    assert set(ARM_COLUMNS) == {"recalled_event_ids"}
    w = TapeWriter(tmp_path / "x")
    w.arm_columns["no_such_column"] = lambda row: []
    with pytest.raises(ValueError, match="腕の列"):
        w.append(TapeRow("c0", 1, 0, 0, "ph", (), "pa", "r"))
    empty = TapeWriter(tmp_path / "e")
    empty.arm_columns["recalled_event_ids"] = lambda row: ("1:-1",)
    empty.close()  # 行の無いテープも腕の列つきのスキーマ
    assert pq.read_schema(tmp_path / "e" / CALLS_FILENAME).names[-1] == "recalled_event_ids"
    w2 = TapeWriter(tmp_path / "y", flush_rows=2)
    w2.arm_columns["recalled_event_ids"] = lambda row: (f"{row.tick}:-1",)
    for i in range(5):
        w2.append(TapeRow(f"c{i}", 1, i, 0, f"ph{i}", (), "pa", "r", recalled_rows=(0,)))
    w2.close()
    assert Tape(tmp_path / "y").column("recalled_event_ids") == [[f"{i}:-1"] for i in range(5)]
