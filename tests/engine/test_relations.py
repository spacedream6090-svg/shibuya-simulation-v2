"""C10 8a: **関係辺の表と導出**(R1 (a)・M12 (a)・D-93 (a)(b)(c)(d)・R6・第299)のテスト。

正典: ``docs/design/v2-c10-relations-implementation-agenda.md`` §1(段 8a の 1〜8)・§4。
見るもの: (a) 表は腕でだけ・16 B/辺 (b) 共在(同じセル・同じ 15 分)の分とブロック (c) 機械的初期化=世帯は
全ペア・職場/学校は共在の長い順・k で切る・τ で落とす・代表日の週の回数・密度の腕 (d) τ の逆算 (e) 書き手=
会話/手伝いのエピソード・符号は ResultCode・1 セッション 1 本・押し出し (f) 読み口(A ≥ τ・P・同セル・招待の
重み)(g) 知人の結線(B5 近接行の印・off は 1 バイトも変わらない)(h) 3 人会話の口 (i) ラン。
"""

from __future__ import annotations

import ast
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.agents.state import RELATION_FIELDS, AgentState, ResultCode
from shibuya.agents.weekly import WeeklySchedule
from shibuya.engine import memory as M
from shibuya.engine import relations as RL
from shibuya.engine.conversation import ConversationManager
from shibuya.perception import templates as T

SRC = Path("src/shibuya")
OK = int(ResultCode.OK)


def weekly(rows_per_agent: list[list[tuple[int, int, int]]]) -> WeeklySchedule:
    """体ごとの (開始分, 終了分, セル) の行(全部 曜日 0=実資産と同じ 1 日ぶんの表)。"""
    n = len(rows_per_agent)
    counts = np.zeros(n * 7, dtype=np.int64)
    st, en, cl = [], [], []
    for a, rows in enumerate(rows_per_agent):
        counts[a * 7] = len(rows)
        for s, e, c in rows:
            st.append(s)
            en.append(e)
            cl.append(c)
    off = np.zeros(n * 7 + 1, dtype=np.int64)
    np.cumsum(counts, out=off[1:])
    k = len(st)
    return WeeklySchedule(None, np.arange(n, dtype=np.int64), off, np.asarray(st, dtype=np.int16),
                          np.asarray(en, dtype=np.int16), np.zeros(k, dtype=np.int8),
                          np.ones(k, dtype=np.int8), np.asarray(cl, dtype=np.int32), np.zeros(k, dtype=np.int16))


def pop(household, org, school):
    return SimpleNamespace(n=len(household), household_id=np.asarray(household), org_id=np.asarray(org),
                           school_cell=np.asarray(school))


def table(n: int = 6, k: int = 15) -> AgentState:
    a = AgentState(n, memory_columns=True, memory_n=32, relation_columns=True, rel_k=k)
    with a.writable():
        a.cell[:] = 3
    return a


def layer(a: AgentState, **kw) -> M.MemoryLayer:
    lay = M.MemoryLayer(a.n, a.memory_n, minutes_per_tick=1.0)
    lay.enable_relations(a.rel_k, **kw)
    return lay


def ep(lay, a, tick, agent, kind, partner, result=OK):
    return lay.record(a, tick, np.array([agent]), np.array([M.EVENT_KINDS[kind]]), np.array([partner]),
                      np.array([-1]), np.array([result]), np.array([3]))


# ================================================================= (a) 表
def test_relation_columns_only_in_the_arm_16_bytes_per_edge():
    base = AgentState(4, memory_columns=True)
    assert not any(f in base.registry for f in RELATION_FIELDS)
    a = AgentState(4, memory_columns=True, relation_columns=True)
    assert a.rel_partner.shape == (4, RL.REL_K) == (4, 15) and (a.rel_partner == -1).all()
    assert a.declared_bytes_per_agent - base.declared_bytes_per_agent == 15 * 16 == 240
    assert (a.bytes_total() - base.bytes_total()) // 4 == 240
    assert RL.REL_ROW_BYTES_ACTUAL == RL.REL_ROW_BYTES_DECLARED == 16
    with pytest.raises(ValueError):
        AgentState(2, relation_columns=True, rel_k=0)


# ================================================================= (b)(c) 共在と初期化
def test_copresence_minutes_and_blocks():
    w = weekly([[(540, 1020, 7)], [(600, 720, 7), (780, 900, 7)], [(540, 1020, 8)]])
    sl = RL.slot_cells(w, np.arange(3))
    mins, blocks = RL.copresence(sl)
    assert mins[0, 1] == 240 and blocks[0, 1] == 2      # 10:00〜12:00 と 13:00〜15:00=2 塊
    assert mins[0, 2] == 0 and blocks[0, 2] == 0         # 別のセル
    assert mins[1, 0] == mins[0, 1] and mins[0, 0] == 0


def test_initial_edges_household_work_school_and_cap():
    # 体 0,1 は世帯(共在なし=域外の自宅)/ 体 2..7 は同じ組織(共在の長さが違う)/ 体 8,9 は同じ学校
    rows = [[], []] + [[(540, 540 + 60 * (j + 1), 5)] for j in range(6)] + [[(480, 900, 9)], [(480, 600, 9)]]
    w = weekly(rows)
    p = pop([1, 1, -1, -1, -1, -1, -1, -1, -1, -1], [-1, -1, 4, 4, 4, 4, 4, 4, -1, -1],
            [-1] * 8 + [9, 9])
    init = RL.initial_edges(p, w, 10, k=3, tau=None, tiebreak="id")
    got = {(int(u), int(v)): int(kd) for u, v, kd in zip(init.u, init.v, init.kind)}
    assert got[(0, 1)] == got[(1, 0)] == RL.REL_KINDS["household"]
    assert got[(8, 9)] == RL.REL_KINDS["school"]
    # 体 2 の職場の辺は共在の長い順に 3 本(体 7 が最長=体 2 と 60 分・…同点は相手の行番号)
    assert sorted(v for (u, v) in got if u == 2) == [3, 4, 5]
    assert sorted(v for (u, v) in got if u == 7) == [4, 5, 6]            # 体 7 から見て共在が長い 3 人
    assert init.audit["w17_single_day"] is True
    assert init.audit["candidate_pairs"] < init.audit["candidate_pairs_all"]      # 組の中で k に切った
    j = [i for i, (u, v) in enumerate(zip(init.u, init.v)) if (u, v) == (0, 1)][0]
    assert int(init.n[j]) == RL.HOUSEHOLD_MIN_BLOCKS_PER_WEEK * RL.REL_INIT_WEEKS     # 共在なしの世帯=毎日
    j = [i for i, (u, v) in enumerate(zip(init.u, init.v)) if (u, v) == (8, 9)][0]
    assert int(init.n[j]) == 1 * 5 * 13                                  # 代表日 1 塊 × 5 日 × 13 週
    assert int(init.first[j]) == -13 * 7 * 1440 and -1440 < int(init.last[j]) < 0   # 前日の 10:00 に終わる
    assert int(init.last[j]) == 600 - 1440
    # 既定(hash): 同点の 5 人(体 3〜7 は体 2 とどれも 60 分)から 3 人=行番号の順ではない選び方でも本数と種別は同じ
    h = RL.initial_edges(p, w, 10, k=3, tau=None)
    got_h = {(int(u), int(v)): int(kd) for u, v, kd in zip(h.u, h.v, h.kind)}
    assert len([1 for (u, _v) in got_h if u == 2]) == 3 and {v for (u, v) in got_h if u == 2} <= {3, 4, 5, 6, 7}
    assert sorted(v for (u, v) in got_h if u == 7) == [4, 5, 6]          # 同点の無い体は同じ
    assert h.audit["tiebreak"] == "hash" and init.audit["tiebreak"] == "id"
    with pytest.raises(ValueError):
        RL.initial_edges(p, w, 10, tiebreak="random")


def test_initial_edges_hash_tiebreak_spreads_in_degree():
    """同じ日課の大組織(40 人・全員同点)で、id の順は行番号の小さい 15 人に入次数が集まる/hash は散る。"""
    g = 40
    w = weekly([[(540, 1080, 5)] for _ in range(g)])
    p = pop([-1] * g, [3] * g, [-1] * g)
    by_id = RL.initial_edges(p, w, g, tau=None, tiebreak="id")
    by_hash = RL.initial_edges(p, w, g, tau=None)
    in_id = np.bincount(by_id.v, minlength=g)
    in_hash = np.bincount(by_hash.v, minlength=g)
    assert by_id.u.size == by_hash.u.size == g * 15                        # 出次数は同じ(k=15)
    assert int(in_id.max()) >= g - 2 and int((in_id == 0).sum()) >= g - 16    # 行番号の小さい体に集中
    assert int(in_hash.max()) < int(in_id.max()) and int((in_hash == 0).sum()) < int((in_id == 0).sum())
    again = RL.initial_edges(p, w, g, tau=None)
    assert np.array_equal(again.v, by_hash.v)                                # 決定論(seed に依らない)


def test_initial_edges_tau_and_density_arms():
    rows = [[(540, 1020, 5)], [(540, 600, 5)], [(540, 1020, 5)], [(900, 1020, 6)]]
    w = weekly(rows)
    p = pop([-1] * 4, [2, 2, 2, 2], [-1] * 4)
    base = RL.initial_edges(p, w, 4, tau=None)
    assert base.audit["candidate_pairs_copresent"] < base.audit["candidate_pairs_all"]   # 体 3 は共在 0
    assert not any(3 in (int(u), int(v)) for u, v in zip(base.u, base.v))
    dense = RL.initial_edges(p, w, 4, density=2.0, tau=None)
    assert any(3 in (int(u), int(v)) for u, v in zip(dense.u, dense.v))
    sparse = RL.initial_edges(p, w, 4, density=0.5, tau=None)
    assert sparse.u.size < base.u.size
    high = RL.initial_edges(p, w, 4, tau=10.0)
    assert high.u.size == 0 and high.audit["dropped_by_tau"] == base.u.size
    with pytest.raises(ValueError):
        RL.initial_edges(p, w, 4, density=3.0)


def test_tau_is_the_median_of_the_kth_edge():
    u = np.array([0, 0, 0, 1, 1, 1, 2])
    A = np.array([-1.0, -2.0, -0.5, -3.0, -1.5, -2.5, 0.0])
    r = RL.tau_from_edges(u, A, 4, k=3)
    # 体 0 の 3 番目=−2.0・体 1=−3.0・体 2,3 は 3 本無い=−∞ → 中央値=(−3.0 と −∞ の間)=−∞
    assert r["agents_with_k_edges"] == 2 and r["tau"] == -math.inf
    r2 = RL.tau_from_edges(u, A, 2, k=3)
    assert r2["tau"] == pytest.approx(-2.5)


# ================================================================= (e) 書き手
def test_writer_signs_from_result_codes_and_merges():
    a = table()
    lay = layer(a)
    ep(lay, a, 10, 0, "talk", 1)                                   # 会話の成立 +1(新しい辺=知人)
    ep(lay, a, 20, 0, "talk", 1, int(ResultCode.REFUSED))           # 断られた −1(統合)
    ep(lay, a, 30, 0, "talk", 2, int(ResultCode.PARTNER_BUSY))      # 相手の都合 0
    ep(lay, a, 40, 0, "talk", 3, int(ResultCode.BAD_TARGET))        # 辺にしない
    ep(lay, a, 50, 0, "help", 4, int(ResultCode.INSUFFICIENT_ABILITY))  # 辺にしない
    ep(lay, a, 60, 0, "buy", 5)                                     # 相互作用でない
    r = a.registry
    got = {int(p): (int(k), int(s), int(n)) for p, k, s, n in
           zip(r.rel_partner[0], r.rel_kind[0], r.rel_sign[0], r.rel_n[0]) if p >= 0}
    assert got == {1: (5, 0, 2), 2: (5, 0, 1)}
    j = int(np.flatnonzero(r.rel_partner[0] == 1)[0])
    assert int(r.rel_first[0, j]) == 10 and int(r.rel_last[0, j]) == 20
    st = lay.relations.stats
    assert st["events"] == 3 and st["events:sign+1"] == 1 and st["events:sign-1"] == 1 and st["merged"] == 1


def test_sessions_write_both_sides_and_utterances_do_not_add_n():
    a = table()
    lay = layer(a)
    s0 = SimpleNamespace(session_id=0, participants=[0, 1])
    lay.after_tick(a, 5, conv=SimpleNamespace(n_opened=1, sessions={0: s0}))
    for t_ in (6, 7, 8):
        lay.note_utterance(a, 0, t_, s0, "やあ")
    r = a.registry
    for u, v in ((0, 1), (1, 0)):
        j = int(np.flatnonzero(r.rel_partner[u] == v)[0])
        assert int(r.rel_n[u, j]) == 1 and int(r.rel_sign[u, j]) == 1      # 1 セッション 1 本


def test_full_table_evicts_the_lowest_activation():
    a = table(n=6, k=2)
    lay = layer(a)
    ep(lay, a, 0, 0, "talk", 1)
    ep(lay, a, 0, 0, "talk", 2)
    ep(lay, a, 1, 0, "talk", 2)                                     # 2 は n=2 で A が上
    ep(lay, a, 100, 0, "talk", 3)
    assert set(a.registry.rel_partner[0].tolist()) == {2, 3}
    assert lay.relations.stats["evictions"] == 1


# ================================================================= (f) 読み口
def test_readers_live_edges_strength_same_cell_and_invite_weights():
    a = table(n=20)
    lay = layer(a)
    rel = lay.relations
    for v in range(1, 9):
        ep(lay, a, 100, 0, "talk", v)
    ep(lay, a, 100, 1, "talk", 0)                                   # 体 1 の辺は 1 本
    for _ in range(3):
        ep(lay, a, 100, 0, "talk", 1)                               # 1 が一番強い
    e = rel.edges(a, 0, 101)
    assert e.partner[0] == 1 and len(e.partner) == 8 and (np.diff(e.A) <= 0).all()
    assert rel.strength(np.array([rel.tau]))[0] == 128 and rel.strength(np.array([rel.tau + 5]))[0] == 255
    assert rel.edges(a, 0, 100 + 10_000).partner.size == 0           # 古くなって τ を下回る(n=1 の辺)
    assert set(rel.acquaintances(a, 0, 101).tolist()) == set(range(1, 9))
    with a.writable():
        a.cell[:] = 3
        a.cell[5] = 7
    inc = rel.partners_in_cell(a, np.array([0]), 101)[0]
    assert set(inc[inc >= 0].tolist()) == set(range(1, 9)) - {5}
    p_, w_, rest = rel.weights_for_invite(a, 0, 101)
    assert w_[:5].sum() == pytest.approx(0.40) and w_[5:].sum() == pytest.approx(0.20) and rest == pytest.approx(0.40)
    _p, w2, rest2 = rel.weights_for_invite(a, 1, 101)
    assert rest2 == pytest.approx(0.60) and w2.sum() == pytest.approx(0.40)   # 辺 1 本=内側だけ


# ================================================================= (g) 知人の結線
def build_renderer(n: int = 8):
    from shibuya.agents.state import AgentKind
    from shibuya.perception.renderer import Renderer
    from shibuya.world.state import World

    w = World.synthetic(n_cells=9, seed=1)
    a = AgentState(n)
    g = np.random.default_rng(1)
    with a.writable():
        a.cell[:] = 0
        a.xy[:] = g.uniform(0.0, 50.0, size=(n, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = 4_000
        a.hunger[:] = 5
        a.last_result[:] = OK
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=7)
    r.prepare_tick(600)
    return r


def test_acquaintance_marks_in_the_near_line_and_off_is_unchanged():
    r = build_renderer()
    base = r.render(0, tick=600, wake_reason=3)
    near = [ln for ln in base.text.splitlines() if ln.startswith("[B5 近接]")][0]
    assert "(知人)" not in near and "(未知)" in near
    assert T.NEAR_PERSON_MARKS == ("未知", "知人")
    r.acquaintance_fn = lambda i, t: [7] if i == 0 else []
    got = r.render(0, tick=600, wake_reason=3)
    near2 = [ln for ln in got.text.splitlines() if ln.startswith("[B5 近接]")][0]
    assert "P-7(知人)" in near2                                      # 知人は常に載る・印が付く
    r.acquaintance_fn = None
    assert r.render(0, tick=600, wake_reason=3).prompt_hash == base.prompt_hash


# ================================================================= (h) 3 人会話の口
def test_three_person_join_and_counters():
    m2 = ConversationManager(master_seed=1)
    assert "sessions_joined" not in m2.counters()                    # 既定 2 の計数は変えない
    m = ConversationManager(master_seed=1, max_participants=3)
    s = m.invite(1, 2, tick=0, cell=5, same_cell=True, partner_idle=True, answered=True)
    assert s is not None and m.join(s, 3, tick=1) and not m.join(s, 4, tick=1)
    assert m.join_events == [(1, s.session_id, 3)]
    m._close(s, 2, "hard")
    c = m.counters()
    assert c["sessions_joined"] == 1 and c["session_size_3"] == 1 and c["session_size_2"] == 0
    # 記憶/関係の書き手: 参加した体と既存の参加者の間に会話の行(両向き)
    a = table(n=5)
    lay = layer(a)
    conv = SimpleNamespace(n_opened=0, sessions={s.session_id: s}, join_events=m.join_events)
    lay.after_tick(a, 1, conv=conv)
    got = {(u, int(v)) for u in range(5) for v in a.registry.rel_partner[u] if v >= 0}
    assert got == {(3, 1), (3, 2), (1, 3), (2, 3)}


# ================================================================= (i) ラン
WORLD = "data/world/v2"


def _real_world_or_skip() -> None:
    from shibuya.world.assets import assets_available

    if not assets_available(WORLD):
        pytest.skip("W 資産(data/world/v2)が無い")


def test_run_default_is_off_and_relations_on_keeps_behavior():
    _real_world_or_skip()
    from shibuya import cli

    kw = dict(n_agents=2000, seed=1, world_dir=WORLD, vocab_version="v3", memory="on")
    mem = cli.run(**kw)
    assert mem.run_manifest_fields()["relations"] == {}
    assert not any(f in mem.agents.registry for f in RELATION_FIELDS)
    mp = pytest.MonkeyPatch()
    mp.setattr(AgentState, "state_hash", lambda self: self.registry.state_hash(exclude=RELATION_FIELDS))
    try:
        on = cli.run(relations="on", **kw)
    finally:
        mp.undo()
    assert on.final_hash == mem.final_hash and on.llm_calls == mem.llm_calls     # 書くだけ(mock は描画を読まない)
    s = on.run_manifest_fields()["relations"]
    assert s["counts"]["init_edges"] > 0 and s["degree_regular"] is False
    assert s["init"]["w17_single_day"] is True and s["tau"] == RL.REL_TAU
    for key in ("edges_live_per_agent", "degree_histogram", "kinds", "signs", "A", "P", "dunbar_layers"):
        assert key in s


def test_arm_checks_and_cli_flags():
    from shibuya.engine.run import run_day

    for bad in (dict(relations="on"), dict(memory="on", relations="maybe"),
                dict(memory="on", relations="on", rel_init_density=3.0),
                dict(memory="on", conv_max_participants=4), dict(memory="on", relations="on", rel_d=1.5)):
        with pytest.raises(ValueError):
            run_day(n_agents=10, ticks=2, **bad)
    text = (SRC / "cli.py").read_text(encoding="utf-8")
    for flag in ('"--relations"', '"--rel-k"', '"--rel-tau"', '"--rel-d"', '"--rel-init-density"',
                 '"--conv-max-participants"'):
        assert flag in text


def test_readers_and_writer_rounds_are_array_ops():
    """P4: 読み口と 1 回の書き込みに for/while を書かない(体数比例の逐次ループなし)。"""
    tree = ast.parse((SRC / "engine/relations.py").read_text(encoding="utf-8"))
    names = {"activation", "strength", "edges", "acquaintances", "partners_in_cell", "_write_round",
             "copresence", "slot_cells", "_last_copresence_many"}
    def allowed(s: ast.AST, fn: str) -> bool:  # 宣言済み: 組の中のセルの数ぶん・種別の数ぶん(Counter)
        it = ast.unparse(s.iter) if isinstance(s, ast.For) else ""
        return fn == "copresence" or ".items()" in it

    bad = [f"{n.name}:{s.lineno}" for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef) and n.name in names
           for s in ast.walk(n) if isinstance(s, ast.While)
           or (isinstance(s, ast.For) and not allowed(s, n.name))]
    assert not bad, bad


def test_last_copresence_many_matches_scalar():
    """性能修正(挙動不変): 直近の共在の配列版は 1 辺ずつの版と同じ値(代表日・週の両方・共在なしの辺も)。"""
    rng = np.random.default_rng(7)
    for daily in (True, False):
        su = rng.integers(-1, 4, size=(300, RL._SLOTS)).astype(np.int32)
        sv = rng.integers(-1, 4, size=(300, RL._SLOTS)).astype(np.int32)
        if daily:
            su[:, RL._SLOTS_PER_DAY:] = -1
        sv[:40] = -1  # 共在なし
        for day_index in (0, 3, 6):
            got = RL._last_copresence_many(su, sv, day_index, daily)
            want = np.array([RL._last_copresence(su[j], sv[j], day_index, daily) for j in range(su.shape[0])])
            assert np.array_equal(got, want), (daily, day_index)


def test_join_in_the_tick_the_session_opened_is_written_once():
    """3 人目が開いた同じ tick に加わっても、会話の行は参加者の組ごとに 1 本(二重に書かない)。"""
    m = ConversationManager(master_seed=1, max_participants=3)
    s = m.invite(1, 2, tick=0, cell=5, same_cell=True, partner_idle=True, answered=True)
    assert s is not None and m.join(s, 3, tick=0)
    a = table(n=5)
    lay = layer(a)
    conv = SimpleNamespace(n_opened=m.n_opened, sessions=m.sessions, join_events=m.join_events)
    lay.after_tick(a, 0, conv=conv)
    r = a.registry
    got = {(u, int(v)): int(r.rel_n[u][j]) for u in range(5) for j, v in enumerate(r.rel_partner[u]) if v >= 0}
    assert got == {(1, 2): 1, (2, 1): 1, (1, 3): 1, (3, 1): 1, (2, 3): 1, (3, 2): 1}
    talk = M.EVENT_KINDS["talk"]
    rows = sorted((u, int(p)) for u in range(5) for k_, p in zip(r.mem_kind[u], r.mem_partner[u]) if int(k_) == talk)
    assert rows == [(1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2)]
