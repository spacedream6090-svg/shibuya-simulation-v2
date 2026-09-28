"""D-120 7a: **店の評価の記憶**(N1 (a)・N2 (i)(iii)・N4 (a)・N5 (a)・第296)のテスト。

正典: ``docs/design/v2-store-memory-implementation-agenda.md`` §1(段 7a の 1〜7)・§4。
見るもの: (a) 表は腕でだけ・宣言 24 B/行 (b) 自分の訪問=結果コード → 向き・精度 1 (c) 看板=初見の
エピソードからだけ・向き 0・精度 1/16 (d) 統合・出どころのビット・満杯の追い出し (e) 読み口(A ≥ τ・
店の絞り込み・向きの下限) (f) σ と減衰の口 (g) ラン: 既定は表なし・on でも挙動は同じ・memory off では使えない。
"""

from __future__ import annotations

import ast
import math
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import (
    MEMORY_FIELDS,
    STORE_MEMORY_FIELDS,
    AgentState,
    ResultCode,
)
from shibuya.engine import memory as M
from shibuya.engine import store_memory as SM
from shibuya.engine.familiarity import place_thing

SRC = Path("src/shibuya")
OK = int(ResultCode.OK)
CLOSED = int(ResultCode.CLOSED)


def table(n: int = 3, rows: int = 32, mem_rows: int = 64) -> AgentState:
    a = AgentState(n, memory_columns=True, memory_n=mem_rows, store_memory_columns=True,
                   store_memory_n=rows)
    with a.writable():
        a.cell[:] = 3
    return a


def layer(a: AgentState, **kw) -> M.MemoryLayer:
    lay = M.MemoryLayer(a.n, a.memory_n, minutes_per_tick=1.0)
    lay.enable_store(a.store_memory_n, **kw)
    return lay


def ep(lay, a, tick, agent, kind, obj, result=OK):
    return lay.record(a, tick, np.array([agent]), np.array([M.EVENT_KINDS[kind]]), np.array([-1]),
                      np.array([obj]), np.array([result]), np.array([3]))


def row_of(a, agent, poi):
    hit = np.flatnonzero(a.sm_poi[agent] == poi)
    assert hit.size == 1
    return int(hit[0])


# ================================================================= (a) 表
def test_store_columns_only_in_the_arm_and_declare_24_bytes_per_row():
    base = AgentState(4, memory_columns=True)
    assert not any(f in base.registry for f in STORE_MEMORY_FIELDS)
    a = AgentState(4, memory_columns=True, store_memory_columns=True)
    assert a.sm_poi.shape == (4, SM.STORE_MEMORY_N) == (4, 32)
    assert (a.sm_poi == -1).all() and (a.sm_first == -1).all()
    assert a.declared_bytes_per_agent - base.declared_bytes_per_agent == 32 * 24 == 768
    assert (a.bytes_total() - base.bytes_total()) // 4 == 32 * SM.STORE_MEMORY_ROW_BYTES_ACTUAL
    assert SM.STORE_MEMORY_ROW_BYTES_ACTUAL == 23 and SM.STORE_MEMORY_ROW_BYTES_DECLARED == 24
    with pytest.raises(ValueError):
        AgentState(2, store_memory_columns=True, store_memory_n=0)


def test_valence_of_result():
    codes = [OK, int(ResultCode.OUT_OF_STOCK), CLOSED, int(ResultCode.LOST_ARBITRATION),
             int(ResultCode.TOO_FAR), int(ResultCode.MONEY_SHORT), int(ResultCode.BAD_TARGET)]
    assert SM.valence_of_result(np.array(codes)).tolist() == [1, -1, -1, -1, -1, 0, 0]


# ================================================================= (b)(c)(d) 書き手
def test_own_visits_write_valence_from_the_result_and_merge_by_poi():
    a = table()
    lay = layer(a)
    ep(lay, a, 10, 0, "buy", 5)
    ep(lay, a, 20, 0, "eat", 5, CLOSED)
    ep(lay, a, 30, 0, "queue", 5)
    j = row_of(a, 0, 5)
    assert float(a.sm_valence[0, j]) == 1.0 and float(a.sm_precision[0, j]) == 3.0  # +1 −1 +1
    assert int(a.sm_n[0, j]) == 3 and int(a.sm_first[0, j]) == 10 and int(a.sm_last[0, j]) == 30
    assert int(a.sm_source[0, j]) == SM.STORE_SOURCE_BIT["self"]
    st = lay.store.stats
    assert st["events:self"] == 3 and st["events:self:valence-1"] == 1 and st["merged"] == 2


def test_signage_rows_come_only_from_the_first_sight_episode():
    a = table()
    lay = layer(a)
    lay.after_tick(a, 5, signage=[(1, 70)])
    lay.after_tick(a, 6, signage=[(1, 70)])  # 2 回目は初見ではない=エピソードも店の行も増えない
    j = row_of(a, 1, 70)
    assert float(a.sm_valence[1, j]) == 0.0 and float(a.sm_precision[1, j]) == 1 / 16
    assert int(a.sm_source[1, j]) == SM.STORE_SOURCE_BIT["signage"] and int(a.sm_n[1, j]) == 1
    ep(lay, a, 9, 1, "buy", 70)  # 自分の訪問が足される=出どころ 自分+看板
    assert int(a.sm_source[1, j]) == 1 | 4 and float(a.sm_precision[1, j]) == 1 + 1 / 16
    assert lay.store.stats["source_added"] == 1


def test_non_poi_objects_and_other_kinds_are_not_store_rows():
    a = table()
    lay = layer(a)
    ep(lay, a, 1, 0, "buy", -1, int(ResultCode.BAD_TARGET))       # 対象不明の購入
    ep(lay, a, 1, 0, "move", int(place_thing(4)))                  # 場所
    lay.record(a, 1, np.array([0]), np.array([M.EVENT_KINDS["talk"]]), np.array([2]),
               np.array([33]), np.array([OK]), np.array([3]))       # 会話の行の店 ID は書かない
    ep(lay, a, 1, 0, "notice", int(place_thing(3)))
    assert (a.sm_poi[0] == -1).all()
    assert lay.store.stats["episodes_shop_without_poi"] == 1


def test_several_store_events_for_one_agent_in_one_tick_merge():
    a = table()
    lay = layer(a)
    lay.record(a, 7, np.array([0, 0, 1]), np.array([1, 2, 1]), np.array([-1, -1, -1]),
               np.array([5, 5, 6]), np.array([OK, OK, CLOSED]), np.array([3, 3, 3]))
    assert int(a.sm_n[0, row_of(a, 0, 5)]) == 2 and float(a.sm_valence[1, row_of(a, 1, 6)]) == -1.0


def test_full_table_evicts_the_lowest_store_score():
    a = table(rows=4)
    lay = layer(a)
    for j in range(4):
        ep(lay, a, 0, 0, "buy", 100 + j)
    ep(lay, a, 1, 0, "buy", 101)  # 101 は n=2・精度 2 で score が上
    ep(lay, a, 50, 0, "buy", 999)
    assert lay.store.stats["evictions"] == 1
    assert int(a.sm_poi[0, 0]) == 999  # 同点(100・102・103)は行番号の小さい方
    assert set(a.sm_poi[0].tolist()) == {999, 101, 102, 103}


# ================================================================= (e) 読み口
def test_store_rows_and_known_stores():
    a = table()
    lay = layer(a)
    ep(lay, a, 0, 0, "buy", 5)                    # 古い(A = ln2 − 0.5 ln(1001) ≈ −2.76 < −2.0)
    ep(lay, a, 990, 0, "eat", 6, CLOSED)          # 新しい・向き −1
    ep(lay, a, 995, 0, "buy", 7)                  # 新しい・向き +1
    rows = lay.store_rows(a, 0, 1000)
    by = dict(zip(rows.poi.tolist(), zip(rows.sign.tolist(), rows.recallable.tolist())))
    assert by == {5: (1, False), 6: (-1, True), 7: (1, True)}
    assert np.allclose(rows.A, [math.log(2) - 0.5 * math.log(1001), math.log(2) - 0.5 * math.log(11),
                                math.log(2) - 0.5 * math.log(6)])
    got = lay.known_stores(a, np.array([0, 1]), 1000)
    assert sorted(got[0][got[0] >= 0].tolist()) == [6, 7] and (got[1] == -1).all()
    mask = np.zeros(10, dtype=bool)
    mask[7] = True
    assert lay.known_stores(a, np.array([0]), 1000, mask=mask)[0].max() == 7
    assert sorted(x for x in lay.known_stores(a, np.array([0]), 1000, min_sign=0)[0].tolist() if x >= 0) == [7]
    lay.tau = -3.0  # τ は記憶の想起と同じ
    assert sorted(x for x in lay.known_stores(a, np.array([0]), 1000)[0].tolist() if x >= 0) == [5, 6, 7]


def test_reading_needs_the_arm():
    a = AgentState(2, memory_columns=True)
    lay = M.MemoryLayer(2, a.memory_n)
    with pytest.raises(RuntimeError):
        lay.store_rows(a, 0, 1)
    with pytest.raises(RuntimeError):
        lay.known_stores(a, np.array([0]), 1)


# ================================================================= (f) σ と減衰の口
def test_sigma_table_and_weights():
    assert SM.check_store_sigma(None) == {"self": 1.0, "wom": 2.0, "signage": 4.0, "net": 2.0}
    assert SM.check_store_sigma('{"signage": 1}')["signage"] == 1.0
    for bad in ('{"friend": 1}', '{"self": 0}', '{"self": -1}', "[1, 2]"):
        with pytest.raises(ValueError):
            SM.check_store_sigma(bad)
    a = table()
    lay = layer(a, sigma={"self": 2.0, "signage": 1.0})
    ep(lay, a, 1, 0, "buy", 5)
    lay.after_tick(a, 2, signage=[(0, 6)])
    assert float(a.sm_precision[0, row_of(a, 0, 5)]) == 0.25
    assert float(a.sm_precision[0, row_of(a, 0, 6)]) == 1.0


def test_decay_modes():
    with pytest.raises(ValueError):
        SM.check_store_decay("linear")
    a = table()
    lay = layer(a, decay="ga")
    ep(lay, a, 0, 0, "buy", 5)
    ep(lay, a, 120, 0, "buy", 5)
    rows = lay.store_rows(a, 0, 180)
    assert np.allclose(rows.A, [1.0 * math.log(0.995)])  # 最後から 1 時間(n は使わない)
    b = table()
    lay2 = layer(b, decay="citysim")
    ep(lay2, b, 0, 0, "buy", 5)
    ep(lay2, b, 2 * 1_440, 0, "buy", 5, CLOSED)  # 2 日後: +1 は e^{−0.06} に回帰してから −1 を足す
    j = row_of(b, 0, 5)
    assert math.isclose(float(b.sm_valence[0, j]), math.exp(-0.06) - 1.0, rel_tol=1e-5)
    got = lay2.store_rows(b, 0, 3 * 1_440)
    assert math.isclose(float(got.valence[0]), (math.exp(-0.06) - 1.0) * math.exp(-0.03), rel_tol=1e-5)
    assert int(got.sign[0]) == -1
    c = table()
    lay3 = layer(c)  # actr: 回帰しない
    ep(lay3, c, 0, 0, "buy", 5)
    ep(lay3, c, 2 * 1_440, 0, "buy", 5, CLOSED)
    assert float(c.sm_valence[0, row_of(c, 0, 5)]) == 0.0


# ================================================================= (g) ラン
@pytest.fixture(scope="module")
def runs():
    from shibuya.engine.run import run_day

    kw = dict(n_agents=100, seed=2, ticks=1440, vocab_version="v3")
    off = run_day(**kw)
    mem = run_day(memory="on", **kw)
    mp = pytest.MonkeyPatch()
    mp.setattr(AgentState, "state_hash",
               lambda self: self.registry.state_hash(exclude=STORE_MEMORY_FIELDS))
    try:
        store_wo = run_day(memory="on", store_memory="on", **kw)
    finally:
        mp.undo()
    mp = pytest.MonkeyPatch()
    mp.setattr(AgentState, "state_hash",
               lambda self: self.registry.state_hash(exclude=MEMORY_FIELDS + STORE_MEMORY_FIELDS))
    try:
        store_wo_all = run_day(memory="on", store_memory="on", **kw)
    finally:
        mp.undo()
    store = run_day(memory="on", store_memory="on", **kw)
    return off, mem, store_wo, store_wo_all, store


def test_default_has_no_store_table_and_store_on_keeps_behavior(runs):
    off, mem, store_wo, store_wo_all, store = runs
    m = off.run_manifest_fields()
    assert m["store_memory"] is False and m["store_memory_summary"] == {}
    assert not any(f in off.agents.registry for f in STORE_MEMORY_FIELDS)
    assert store_wo.final_hash == mem.final_hash                  # 書くだけ=記憶の腕と同じ挙動
    assert store_wo_all.final_hash == off.final_hash              # 記憶も店も混ぜなければ off と同じ
    assert store.final_hash != mem.final_hash                     # 店の欄は checkpoint に混ざる
    assert store.llm_calls == mem.llm_calls == off.llm_calls


def test_store_summary_in_the_manifest(runs):
    *_, store = runs
    s = store.run_manifest_fields()["store_memory_summary"]
    for key in ("counts", "rows_used_per_agent", "rows_by_source", "rows_with_source_bit",
                "valence_sign", "precision", "n_per_row", "A", "recallable_share", "sigma", "decay"):
        assert key in s
    assert s["n_rows"] == 32 and s["decay"] == "actr" and s["tau"] == M.RECALL_TAU
    assert s["counts"]["new_rows"] > 0 and s["rows_with_source_bit"]["signage"] > 0
    assert s["rows_with_source_bit"]["wom"] == 0 and s["rows_with_source_bit"]["net"] == 0


def test_store_memory_needs_memory_and_checks_its_knobs():
    from shibuya.engine.run import run_day

    with pytest.raises(ValueError):
        run_day(n_agents=10, ticks=2, store_memory="on")
    with pytest.raises(ValueError):
        run_day(n_agents=10, ticks=2, memory="on", store_memory="maybe")
    with pytest.raises(ValueError):
        run_day(n_agents=10, ticks=2, memory="on", store_memory="on", store_decay="linear")
    with pytest.raises(ValueError):
        run_day(n_agents=10, ticks=2, memory="on", store_memory="on", store_sigma='{"x": 1}')
    text = (SRC / "cli.py").read_text(encoding="utf-8")
    for flag in ('"--store-memory"', '"--store-memory-n"', '"--store-sigma"', '"--store-decay"'):
        assert flag in text


def test_store_readers_and_writer_rounds_are_array_ops():
    """P4: 読み口と 1 回の書き込みに for/while を書かない(体数比例の逐次ループなし)。"""
    tree = ast.parse((SRC / "engine/store_memory.py").read_text(encoding="utf-8"))
    names = {"activation", "valence_now", "scores", "rows", "known", "_write_round", "valence_of_result"}
    bad = [f"{n.name}:{s.lineno}" for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef) and n.name in names
           for s in ast.walk(n) if isinstance(s, (ast.For, ast.While))]
    assert not bad, bad
