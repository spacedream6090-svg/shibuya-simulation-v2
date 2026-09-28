"""6 段目 6a: 記憶 第 1 段の**記録**(D-95・記憶アジェンダ v1 M1〜M4・修正 1・第294)のテスト。

正典: ``docs/design/v2-memory-stage1-implementation-agenda.md`` §1・§4。#56(親しみの表)と同じ流儀。
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.agents.state import MEMORY_FIELDS, AgentState, ResultCode
from shibuya.engine import commit as C
from shibuya.engine import memory as M
from shibuya.engine.familiarity import place_thing

SRC = Path("src/shibuya")


def table(n: int = 4, rows: int = 8, *, familiarity: bool = False) -> AgentState:
    a = AgentState(n, memory_columns=True, memory_n=rows, familiarity_columns=familiarity,
                   familiarity_k=8)
    with a.writable():
        a.cell[:] = 3
    return a


def one(layer, a, tick, agent, kind, partner=-1, obj=-1, result=0, cell=3):
    return layer.record(a, tick, np.array([agent]), np.array([M.EVENT_KINDS[kind]]),
                        np.array([partner]), np.array([obj]), np.array([result]), np.array([cell]))


# ================================================================= 表
def test_memory_columns_only_in_the_arm_and_declare_32_bytes_per_row():
    base = AgentState(10)
    on = AgentState(10, memory_columns=True)
    assert not any(f in base.registry.arrays for f in MEMORY_FIELDS)
    assert all(f in on.registry.arrays for f in MEMORY_FIELDS)
    assert on.registry.declared_bytes_per_entity - base.registry.declared_bytes_per_entity == 32 * 128
    assert (on.bytes_total() - base.bytes_total()) // 10 == 25 * 128  # 実 25 B/行
    assert on.mem_kind.shape == (10, M.MEMORY_N) and int(on.mem_kind.max()) == 0  # 空行=0
    with pytest.raises(ValueError):
        AgentState(2, memory_columns=True, memory_n=0)


# ================================================================= 統合・importance・忘却
def test_same_key_merges_and_keeps_the_first_tick():
    a = table()
    lay = M.MemoryLayer(4, 8)
    r0 = one(lay, a, 10, 1, "buy", obj=42)
    r1 = one(lay, a, 25, 1, "buy", obj=42)
    assert r0[0] == r1[0]
    row = int(r0[0])
    assert (int(a.mem_n[1, row]), int(a.mem_tick[1, row]), int(a.mem_last[1, row])) == (2, 10, 25)
    # 結果が違えば別の行(鍵=kind・partner・object・result)
    r2 = one(lay, a, 26, 1, "buy", obj=42, result=int(ResultCode.CLOSED))
    assert int(r2[0]) != row
    assert lay.stats["merged"] == 1 and lay.stats["new_rows"] == 2
    assert lay.stats["failures:CLOSED"] == 1


def test_importance_table():
    kinds = np.array([M.EVENT_KINDS[k] for k in ("buy", "talk", "notice", "signage", "buy", "talk")])
    res = np.array([0, 0, 0, 0, int(ResultCode.CLOSED), int(ResultCode.REFUSED)])
    got = M.importance_of(kinds, res, np.array([False] * 6))
    np.testing.assert_array_equal(got, [1, 2, 1, 1, 3, 3])
    first = M.importance_of(kinds, res, np.array([True] * 6))
    np.testing.assert_array_equal(first, [2, 3, 2, 2, 4, 4])  # 初回 +1・上限 4


def test_several_events_for_one_agent_in_one_tick_get_distinct_rows():
    a = table()
    lay = M.MemoryLayer(4, 8)
    rows = lay.record(a, 5, np.array([2, 2, 2]), np.array([1, 4, 11]), np.array([-1, -1, -1]),
                      np.array([7, -5, 9]), np.array([0, 0, 0]), np.array([3, 3, 3]))
    assert len(set(rows.tolist())) == 3
    assert int((a.mem_kind[2] != 0).sum()) == 3


def test_full_table_evicts_the_lowest_score_row_and_its_gist():
    a = table(rows=4)
    lay = M.MemoryLayer(4, 4)
    for j in range(4):
        one(lay, a, 0, 0, "buy", obj=100 + j)
    one(lay, a, 1, 0, "buy", obj=100)  # 100 は n=2 で score が上
    lay._put_gist(0, 1, "あとで落ちる要旨")
    got = one(lay, a, 50, 0, "buy", obj=999)
    assert lay.stats["evictions"] == 1
    assert int(got[0]) == 1  # 同点(101・102・103)は行番号の小さい方
    assert (0, 1) not in lay.gist
    assert int(a.mem_object[0, 1]) == 999


def test_activation_and_scores_and_top():
    a = table()
    lay = M.MemoryLayer(4, 8, minutes_per_tick=1.0)
    one(lay, a, 0, 0, "buy", obj=1)
    one(lay, a, 0, 0, "buy", obj=1)       # n=2(第294 Q56: 統合は base に戻す=importance 1)
    one(lay, a, 90, 0, "buy", obj=2, result=int(ResultCode.CLOSED))  # importance 4
    s = lay.scores(a, np.array([0]), 100)[0]
    A = M.activation_rows(np.array([2, 1]), np.array([0, 90]), 100, 1.0)
    np.testing.assert_allclose(A, [np.log(2 / 0.5) - 0.5 * np.log(101), np.log(1 / 0.5) - 0.5 * np.log(11)])
    np.testing.assert_allclose(s[:2], A + 0.5 * np.array([1, 4]), rtol=1e-6)
    assert np.isneginf(s[2:]).all()
    assert lay.top(a, 0, 1, 100).tolist() == [1]
    mask = np.zeros(8, dtype=bool)
    mask[0] = True
    assert lay.top(a, 0, 5, 100, mask).tolist() == [0]


# ================================================================= 書き手
def test_action_outcomes_use_last_action_and_the_applied_targets():
    a = table(n=6)
    lay = M.MemoryLayer(6, 8)
    with a.writable():
        a.last_result_tick[:] = 7
        a.last_action[:] = [C.ACT_BUY, C.ACT_MOVE, C.ACT_MOVE, C.ACT_TALK, C.ACT_TALK, C.ACT_NONE]
        a.last_result[:] = [0, 0, int(ResultCode.UNREACHABLE), 0, int(ResultCode.PARTNER_BUSY), 0]
        a.poi_ref[:] = -1
    lay.after_tick(
        a, 7,
        applied=((np.arange(6), np.array([55, 12, 13, 4, 5, -1])),),
        visits=([np.array([0])], [np.array([77])]),
    )
    kinds = {i: [(M.KIND_NAMES[int(k)], int(o), int(p), int(r))
                 for k, o, p, r in zip(a.mem_kind[i], a.mem_object[i], a.mem_partner[i], a.mem_result[i])
                 if k] for i in range(6)}
    assert kinds[0] == [("buy", 77, -1, 0)]                           # 成立した店=訪問の控え
    assert kinds[1] == []                                             # 移動の開始は記録しない
    assert kinds[2] == [("move", int(place_thing(13)), -1, int(ResultCode.UNREACHABLE))]
    assert kinds[3] == []                                             # 会話の成功は会話の行だけ
    assert kinds[4] == [("talk", -1, 5, int(ResultCode.PARTNER_BUSY))]
    assert kinds[5] == []                                             # なし は記録しない
    assert int(lay._target.max()) == -1                               # 散らした対象は戻す


def test_arrivals_conversations_noticed_and_signage():
    a = table(n=4)
    lay = M.MemoryLayer(4, 8)
    with a.writable():
        a.cell[:] = [3, 4, 5, 6]
        a.poi_ref[:] = [-1, 30, -1, -1]
    s0 = SimpleNamespace(session_id=0, participants=[0, 1])
    conv = SimpleNamespace(n_opened=1, sessions={0: s0})
    ev = SimpleNamespace(cell=8, noticed=np.array([2, 3]))
    lay.after_tick(a, 9, arrived=[np.array([3])], conv=conv, salient_events=[ev],
                   signage=[(2, 70), (2, 70)])
    rows = {i: sorted((M.KIND_NAMES[int(k)], int(o), int(p))
                      for k, o, p in zip(a.mem_kind[i], a.mem_object[i], a.mem_partner[i]) if k)
            for i in range(4)}
    assert rows[0] == [("talk", -1, 1)]
    assert rows[1] == [("talk", 30, 0)]                               # 会話の行の店 ID=在席の POI
    assert rows[2] == sorted([("notice", int(place_thing(8)), -1), ("signage", 70, -1)])
    assert rows[3] == sorted([("move", int(place_thing(6)), -1), ("notice", int(place_thing(8)), -1)])
    # 発話: 会話の行の mem_n+1・最初の空でない ひと言 を 40 字まで
    lay.note_utterance(a, 0, 10, s0, "なし")
    lay.note_utterance(a, 0, 11, s0, "あ" * 50)
    lay.note_utterance(a, 0, 12, s0, "二度目は要旨にしない")
    row = int(np.flatnonzero(a.mem_kind[0] == M.EVENT_KINDS["talk"])[0])
    assert int(a.mem_n[0, row]) == 4
    assert lay.gist == {(0, row): "あ" * 40}
    assert lay.stats["utterances_without_comment"] == 1
    # 看板は初見だけ(2 回目の同じ POI は記録しない)
    lay.after_tick(a, 20, signage=[(2, 70)])
    assert int((a.mem_kind[2] == M.EVENT_KINDS["signage"]).sum()) == 1
    assert lay.stats["events:signage"] == 1


def test_signage_first_sight_is_judged_by_the_memory_table_even_with_familiarity():
    """第294 Q58: 初見は記憶の表で判定(描画による露出=意識的な初見)。親しみの表の「入った回」は使わない。"""
    a = table(n=2, familiarity=True)
    with a.writable():
        a.fam_thing[0, 0] = 70  # 体 0 は看板 70 に親しみの表では「入った回」で触れている
    lay = M.MemoryLayer(2, 8)
    lay.after_tick(a, 3, signage=[(0, 70), (1, 70)])
    assert int((a.mem_kind[0] != 0).sum()) == 1 and int((a.mem_kind[1] != 0).sum()) == 1
    lay.after_tick(a, 4, signage=[(0, 70)])  # 2 回目は記憶の表にあるので書かない
    assert int((a.mem_kind[0] != 0).sum()) == 1


def test_merged_rows_return_importance_to_base():
    """第294 Q56: 同じ鍵の反復(統合)は「初回 +1」を外して base に戻す。新しい行だけ +1。"""
    a = table()
    lay = M.MemoryLayer(4, 8)
    r0 = one(lay, a, 0, 0, "buy", obj=5, result=int(ResultCode.CLOSED))
    assert int(a.mem_importance[0, int(r0[0])]) == 4
    one(lay, a, 1, 0, "buy", obj=5, result=int(ResultCode.CLOSED))
    assert int(a.mem_importance[0, int(r0[0])]) == 3 and int(a.mem_n[0, int(r0[0])]) == 2


def test_gist_falls_back_to_the_reason_field_in_vocab_v3():
    """第294 Q57(親の暫定): ひと言が空/「なし」なら理由欄の先頭 40 字を要旨にする。"""
    a = table(n=2)
    lay = M.MemoryLayer(2, 8)
    s0 = SimpleNamespace(session_id=0, participants=[0, 1])
    lay.after_tick(a, 1, conv=SimpleNamespace(n_opened=1, sessions={0: s0}))
    lay.note_utterance(a, 0, 2, s0, "", "い" * 50)
    lay.note_utterance(a, 1, 2, s0, "なし", "")
    row = int(np.flatnonzero(a.mem_kind[0] == M.EVENT_KINDS["talk"])[0])
    assert lay.gist == {(0, row): "い" * 40}
    assert lay.stats["gist_source:reason"] == 1 and lay.stats["utterances_without_comment"] == 2


def test_gists_are_capped_per_agent():
    lay = M.MemoryLayer(1, 32)
    for j in range(20):
        lay._put_gist(0, j, f"要旨{j}")
    assert len(lay.gist) == M.GIST_PER_AGENT and (0, 0) not in lay.gist and (0, 19) in lay.gist


# ================================================================= ラン
def test_run_default_is_off_and_memory_on_keeps_mock_behavior(monkeypatch):
    from shibuya.engine.run import run_day

    kw = dict(n_agents=100, seed=2, ticks=1440, vocab_version="v3")
    off = run_day(**kw)
    assert off.memory is False and off.memory_summary == {}
    assert off.run_manifest_fields()["memory"] is False
    monkeypatch.setattr(AgentState, "state_hash",
                        lambda self: self.registry.state_hash(exclude=MEMORY_FIELDS))
    on = run_day(memory="on", **kw)
    # 6b: on は B5 に記憶の行が載る(描画が変わる)が、mock は描画の本文を読まない=挙動は同じ
    assert on.final_hash == off.final_hash and on.llm_calls == off.llm_calls
    m = on.run_manifest_fields()
    assert m["memory"] is True and m["memory_n"] == 128
    s = m["memory_summary"]
    for key in ("counts", "rows_used_per_agent", "rows_by_kind", "importance", "A", "gists"):
        assert key in s
    assert s["counts"]["new_rows"] > 0
    with pytest.raises(ValueError):
        run_day(memory="maybe", **{**kw, "ticks": 5})


def test_cli_flags():
    text = (SRC / "cli.py").read_text(encoding="utf-8")
    assert '"--memory"' in text and '"--memory-n"' in text


def test_row_writers_are_array_ops():
    """P4: 1 回の書き込み(統合/新規/追い出し)と読み口に for/while を書かない。"""
    tree = ast.parse((SRC / "engine/memory.py").read_text(encoding="utf-8"))
    names = {"scores", "importance_of", "activation_rows"}
    bad = [f"{n.name}:{s.lineno}" for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef) and n.name in names
           for s in ast.walk(n) if isinstance(s, (ast.For, ast.While))]
    assert not bad, bad
    src = (SRC / "engine/memory.py").read_text(encoding="utf-8")
    assert "逐次ループ宣言" in src
