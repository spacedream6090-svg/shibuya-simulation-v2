"""第 2 期 2-2 段 11a: 判定を切り替えた所(合成の体)。

- 離脱(``ConversationManager.step`` の ``near_fn``): 同じ層・距離 ≤ d+1 m・同じ B5 の単位なら続く。別セルでも近ければ続く。
- 同席(``RelationLayer.copresent_step``): 「同じセル・2 m」→「届く」(別セルの 1 m でも数える・同セルの 3 m は数えない)。
- 偶然と招待の相手(``choose_talk_partners``): 届く知人が第一候補(別セルの 1 m 隣の知人を選ぶ・同セルの 30 m は選ばない)。
- 知人出現(``acquaintance_candidates``): 気づく確率 p(d) の抽選・1 刻み目は出さない・気づいた相手は範囲の中に居る間は
  気づいたまま(毎刻み起きない)・範囲の外に出て戻ると引き直す・起床の後 60 分は同じ相手で起きない。
- 会話の相手(``commit``): 名指しは届くときだけ・フォールバックは届く束の体のうち並びの鍵が最小(総当たりと一致)。
- 既定(proximity なし)は今の判定のまま(負の対照)。
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.agents.state import AgentState, ResultCode, WakeCondition
from shibuya.engine import commit as C
from shibuya.engine import memory as M
from shibuya.engine import proximity as P
from shibuya.engine.conversation import ConversationManager

OK = int(ResultCode.OK)
ACQ = int(WakeCondition.ACQUAINTANCE)
RULE = P.ProximityRule(d=2.0, seed=22)


def table(n: int = 12, k: int = 15) -> AgentState:
    a = AgentState(n, memory_columns=True, memory_n=32, relation_columns=True, rel_k=k)
    with a.writable():
        a.cell[:] = 3
        a.xy[:] = np.column_stack([np.arange(n) * 10.0, np.zeros(n)])   # 互いに 10 m 以上離す
    return a


def layer(a: AgentState, tau: float = -10.0):
    lay = M.MemoryLayer(a.n, a.memory_n, minutes_per_tick=1.0)
    rel = lay.enable_relations(a.rel_k, tau=tau)
    return lay, rel


def talk(lay, a, tick, agent, partner):
    lay.record(a, tick, np.array([agent]), np.array([M.EVENT_KINDS["talk"]]), np.array([partner]),
               np.array([-1]), np.array([OK]), np.array([3]))


def place(a: AgentState, i: int, xy, cell=None):
    with a.writable():
        a.xy[i] = np.asarray(xy, dtype=np.float32)
        if cell is not None:
            a.cell[i] = cell


# ================================================================= 離脱
def test_leave_uses_the_rule_with_hysteresis_and_ignores_cells():
    ag = SimpleNamespace(registry=SimpleNamespace(
        xy=np.zeros((3, 2), np.float32), cell=np.array([3, 4, 3], np.int32), band=np.zeros(3, np.int8),
        poi_ref=np.full(3, -1, np.int32)), n=3)
    conv = ConversationManager(master_seed=1, walk_over_ticks=0)
    s = conv.invite(0, 1, tick=0, cell=3, same_cell=True, partner_idle=True, answered=True)
    conv.step(1)
    near = lambda a_, b_: RULE.stay(ag, a_, b_)  # noqa: E731
    ag.registry.xy[1] = (2.5, 0.0)                              # 別セル・成立 2 m より遠いが離脱 3 m の内
    conv.utterance(0, 2)
    assert conv.step(2, cell=ag.registry.cell, near_fn=near) == []
    assert conv.sessions[s.session_id].close_reason == ""      # 今の判定(セル)なら別セル=閉じる所
    ag.registry.xy[1] = (3.5, 0.0)
    conv.step(3, near_fn=near)
    assert conv.sessions[s.session_id].close_reason == "left_cell"


# ================================================================= 同席
def test_copresent_counts_reachable_edges_not_same_cell():
    a = table()
    lay, rel = layer(a)
    talk(lay, a, 0, 0, 1)
    talk(lay, a, 0, 0, 2)
    rel.enable_copresent()
    r = a.registry
    place(a, 1, (0.0, 1.0), cell=4)                             # 別セルの 1 m
    place(a, 2, (3.0, 0.0))                                     # 同セルの 3 m
    j1 = int(np.flatnonzero(r.rel_partner[0] == 1)[0])
    j2 = int(np.flatnonzero(r.rel_partner[0] == 2)[0])
    n1, n2 = int(r.rel_n[0, j1]), int(r.rel_n[0, j2])
    for t in range(1, 6):
        rel.copresent_step(a, t, proximity=RULE)
    assert int(r.rel_n[0, j1]) == n1 + 1 and int(r.rel_n[0, j2]) == n2
    # 負の対照: 今の判定(同セル・2 m)では逆(体 1 は別セル・体 2 は 3 m)=どちらも数えない
    a2 = table()
    lay2, rel2 = layer(a2)
    talk(lay2, a2, 0, 0, 1)
    rel2.enable_copresent()
    place(a2, 1, (0.0, 1.0), cell=4)
    m0 = int(a2.registry.rel_n[0, 0])
    for t in range(1, 6):
        rel2.copresent_step(a2, t)
    assert int(a2.registry.rel_n[0, 0]) == m0


# ================================================================= 偶然・招待の相手
def test_chance_picks_reachable_acquaintance_across_cells():
    a = table()
    lay, rel = layer(a, tau=-10.0)
    for p in (1, 2, 3):
        talk(lay, a, 100, 0, p)
    rel.enable_invite(b"salt")
    place(a, 1, (0.0, 1.0), cell=4)                             # 別セルの 1 m=届く
    place(a, 2, (30.0, 0.0))                                    # 同セルの 30 m=届かない
    outs, origins = set(), set()
    for t in range(101, 151):
        out, origin = rel.choose_talk_partners(a, t, np.array([0]), np.array([9]), np.array([False]),
                                               np.array([3]), proximity=RULE)
        outs.add(int(out[0]))
        origins.add(int(origin[0]))
    assert outs == {1} and origins == {1}                       # 届く知人が第一候補=偶然
    # 届く知人が居なければ残り(フォールバック)=招待
    place(a, 1, (50.0, 50.0), cell=4)
    out, origin = rel.choose_talk_partners(a, 200, np.array([0]), np.array([9]), np.array([False]),
                                           np.array([3]), proximity=RULE)
    assert int(out[0]) == 9 and int(origin[0]) == 0
    # 負の対照(今の判定): 同セルの知人 2・3 も候補(30 m でも)
    got = {int(rel.choose_talk_partners(a, t, np.array([0]), np.array([9]), np.array([False]),
                                        np.array([3]))[0][0]) for t in range(300, 400)}
    assert {2, 3} <= got


# ================================================================= 知人出現(気づく確率)
def _acq_setup():
    a = table()
    lay, rel = layer(a, tau=-10.0)
    talk(lay, a, 0, 0, 1)
    talk(lay, a, 0, 1, 0)
    rel.enable_acquaintance_wake()
    return a, rel


def test_acquaintance_first_step_marks_only_and_appearance_needs_a_new_notice():
    a, rel = _acq_setup()
    place(a, 1, (0.5, 0.0), cell=4)                             # 別セルの 0.5 m
    got = rel.acquaintance_candidates(a, 1, proximity=RULE)
    assert got[0].size == 0                                     # 1 刻み目は出さない(印だけ)
    # 気づいた欄は印が付く=範囲の中に居る間は気づいたまま(毎刻み起きない)。1 刻み目に気づかなかった向きだけ、後で
    # 1 回気づいて起きうる=各向き高々 1 回
    woke = [rel.acquaintance_candidates(a, t, proximity=RULE)[0].tolist() for t in range(2, 40)]
    flat = [x for w in woke for x in w]
    assert set(flat) <= {0, 1} and len(flat) == len(set(flat))


def test_acquaintance_appears_when_coming_into_range_and_respects_refractory():
    a, rel = _acq_setup()
    place(a, 1, (500.0, 0.0), cell=9)                           # 範囲(100 m)の外
    assert rel.acquaintance_candidates(a, 1, proximity=RULE)[0].size == 0
    place(a, 1, (0.0, 0.0), cell=4)                             # 0 m に来た(p ≈ 0.945)
    seen: list[int] = []
    t = 2
    while not seen and t < 50:
        seen = rel.acquaintance_candidates(a, t, proximity=RULE)[0].tolist()
        t += 1
    assert seen and set(seen) <= {0, 1}
    rel.stamp_acquaintance(np.array(seen), t - 1)
    for tt in range(t, t + 59):                                 # 起床の後 60 分は同じ相手で起きない
        got = rel.acquaintance_candidates(a, tt, proximity=RULE)[0].tolist()
        assert not (set(got) & set(seen))
    # 範囲の外へ出て(印が切れて)、60 分の後に戻ると、また気づいて起きうる
    place(a, 1, (500.0, 0.0), cell=9)
    for tt in range(t + 59, t + 70):
        rel.acquaintance_candidates(a, tt, proximity=RULE)
    place(a, 1, (0.0, 0.0), cell=4)
    again = []
    for tt in range(t + 70, t + 120):
        again += rel.acquaintance_candidates(a, tt, proximity=RULE)[0].tolist()
    assert set(again) & set(seen)
    assert rel.stats["acq_notice_draws"] > 0 and rel.stats["acq_noticed"] > 0


def test_aware_of_reads_the_marks():
    """検収 L1: 描画の知人は関係の層の印を読む(``aware_of``)=気づいた相手は範囲の中に居る間は真・辺に居ない相手は偽。"""
    a, rel = _acq_setup()
    place(a, 1, (0.0, 0.0), cell=4)
    assert rel.aware_of(a, 0, [1, 5], 1).tolist() == [False, False]   # 引く前は気づいていない
    t, noticed = 1, False
    while not noticed and t < 60:
        rel.acquaintance_candidates(a, t, proximity=RULE)
        noticed = bool(rel.aware_of(a, 0, [1], t + 1)[0])
        t += 1
    assert noticed
    assert rel.aware_of(a, 0, [5], t).tolist() == [False]       # 辺に居ない相手
    snapshot = rel._acq_until.copy()
    rel.aware_of(a, 0, [1, 2, 3], t)
    assert np.array_equal(snapshot, rel._acq_until)             # 読むだけ


def test_acquaintance_far_or_other_band_is_rarely_or_never_noticed():
    a, rel = _acq_setup()
    rel.acquaintance_candidates(a, 1, proximity=RULE)
    place(a, 1, (80.0, 0.0), cell=4)                            # 80 m: p ≈ 2.6e-5
    far = sum(rel.acquaintance_candidates(a, t, proximity=RULE)[0].size for t in range(2, 200))
    assert far == 0
    with a.writable():
        a.band[1] = 1                                           # デッキ(層が違う)
    place(a, 1, (0.0, 0.0))
    other = sum(rel.acquaintance_candidates(a, t, proximity=RULE)[0].size for t in range(200, 400))
    assert other == 0


# ================================================================= 会話の相手(commit)
def test_batch_partners_match_bruteforce():
    rng = np.random.default_rng(5)
    n = 300
    reg = SimpleNamespace(
        xy=rng.uniform(0, 12, (n, 2)).astype(np.float32), cell=rng.integers(-1, 4, n).astype(np.int32),
        band=rng.integers(0, 2, n).astype(np.int8), poi_ref=np.where(rng.random(n) < 0.2, rng.integers(0, 3, n), -1)
        .astype(np.int32))
    ag = SimpleNamespace(registry=reg, n=n)
    batch = rng.permutation(n)[:200].astype(np.int64)
    key = rng.integers(0, 1 << 62, batch.size).astype(np.uint64)
    rows = np.arange(0, batch.size, 3)
    got = P.batch_partners(ag, RULE, batch, rows, key)
    for k, r in enumerate(rows.tolist()):
        me = int(batch[r])
        ok = RULE.reach(ag, np.full(batch.size, me), batch) & (batch != me) & (reg.cell[me] >= 0)
        cand = np.flatnonzero(ok)
        if cand.size == 0:
            assert got[k] == -1
        else:
            best = cand[np.lexsort((batch[cand], key[cand]))[0]]
            assert got[k] == batch[best]


def test_commit_talk_partner_named_only_when_reachable():
    ag = AgentState(4)
    with ag.writable():
        ag.cell[:] = [3, 4, 3, 3]
        ag.xy[:] = np.array([[0, 0], [0, 1], [30, 0], [0, 1.5]], np.float32)
    a = np.array([0, 2, 3], dtype=np.int64)
    is_talk = np.array([True, True, False])
    named = np.array([1, 0, -1])
    partner, source = C._talk_partners_reach(ag, a, is_talk, named, None, RULE)
    # 体 0 → 名指し 1(別セルの 1 m=届く)。体 2 → 名指し 0 は 30 m=届かない → 届く束の体も無い
    assert partner.tolist()[:2] == [1, -1] and source.tolist()[:2] == [0, 2]
    # 負の対照(今の判定): 体 0 の名指し 1 は別セル=フォールバック(同セルの束の体 2 か 3)
    p_now, s_now = C.talk_partners(a, ag.cell[a].astype(np.int64), named, ag.cell, 4, None)
    assert int(s_now[0]) == 1 and int(p_now[0]) in (2, 3)
