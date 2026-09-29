"""C10 8b(会話の起点と相手選択+8a の直し)の検査。

正典: ``docs/design/v2-c10-relations-implementation-agenda.md`` §2(8b の 1〜6)・§1 の第299 印(Q89〜Q99)。
- 招待の相手=関係辺の重み(内側 5 人 40%・次の 10 人 20%・残り 40%・居る層で再正規化=Q99)+seed つき乱択
- 偶然=2 m 内の知人を第一候補・起点の種別(招待/偶然/知人出現)
- 知人出現の起床(前 tick は同セルでなかった・同一相手 60 分・1 tick 目は出さない)
- 同席の書き手(同セル・2 m 内・連続 5 分で 1 本・相手ごと 1 日 1 本・表に居る相手だけ)
- 新しい相手も辺として比べる(表の最弱以下なら新しい方を落とす)
- 会話マネージャの起点の計数(既定の計数は 1 字も変えない)・classical の「最初の未知の人」
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import AgentState, ResultCode, WakeCondition
from shibuya.engine import memory as M
from shibuya.engine import relations as RL
from shibuya.engine.conversation import ConversationManager

SRC = Path("src/shibuya")
OK = int(ResultCode.OK)
ACQ = int(WakeCondition.ACQUAINTANCE)


def table(n: int = 12, k: int = 15) -> AgentState:
    a = AgentState(n, memory_columns=True, memory_n=32, relation_columns=True, rel_k=k)
    with a.writable():
        a.cell[:] = 3
        a.xy[:] = np.column_stack([np.arange(n) * 10.0, np.zeros(n)])  # 互いに 10 m 以上離す
    return a


def layer(a: AgentState, tau: float = -1.1) -> tuple[M.MemoryLayer, RL.RelationLayer]:
    lay = M.MemoryLayer(a.n, a.memory_n, minutes_per_tick=1.0)
    rel = lay.enable_relations(a.rel_k, tau=tau)
    return lay, rel


def talk(lay: M.MemoryLayer, a: AgentState, tick: int, agent: int, partner: int, times: int = 1) -> None:
    for _ in range(times):
        lay.record(a, tick, np.array([agent]), np.array([M.EVENT_KINDS["talk"]]), np.array([partner]),
                   np.array([-1]), np.array([OK]), np.array([3]))


# ================================================================= (a) 重み(Q99)
def test_layer_weights_renormalize_over_present_layers():
    rank = np.array([[0, 1, 2, 3, 4, 5, 6, -1], [0, -1, -1, -1, -1, -1, -1, -1], [0, 1, 15, 16, -1, -1, -1, -1]])
    cand = rank >= 0
    w, w_rest = RL._layer_weights(rank, cand, np.array([True, True, False]))
    assert np.allclose(w.sum(axis=1) + w_rest, 1.0)
    assert w[0, :5].sum() == pytest.approx(0.40) and w[0, 5:7].sum() == pytest.approx(0.20)
    assert w_rest[0] == pytest.approx(0.40) and w[0, 0] == pytest.approx(0.08)          # 層の中は等分
    assert w[1, 0] == pytest.approx(0.5) and w_rest[1] == pytest.approx(0.5)            # 内側+残り → 半々
    # 16 番目以降の辺(k=50 の腕)は「残り」の層=残りの人が居なくてもその 2 本で 40% を分ける
    assert w[2, 0] + w[2, 1] == pytest.approx(0.5) and w[2, 2] == w[2, 3] == pytest.approx(0.25)
    none_w, none_r = RL._layer_weights(np.full((1, 3), -1), np.zeros((1, 3), bool), np.array([False]))
    assert none_w.sum() == 0.0 and none_r[0] == 0.0


# ================================================================= (b) 招待の相手
def _eight_edges() -> tuple[AgentState, M.MemoryLayer, RL.RelationLayer]:
    a = table()
    lay, rel = layer(a, tau=-10.0)                              # 3,000 tick の間どの辺も生きている
    for v in range(1, 9):
        talk(lay, a, 100, 0, v, times=1 + (9 - v))   # 1 が一番強い … 8 が一番弱い
    rel.enable_invite(b"salt")
    return a, lay, rel


def test_choose_partners_follows_dunbar_layers_and_is_deterministic():
    a, _lay, rel = _eight_edges()
    got = []
    for tick in range(101, 3101):
        out, origin = rel.choose_talk_partners(a, tick, np.array([0]), np.array([9]), np.array([False]),
                                               np.array([3]))
        got.append(int(out[0]))
        assert origin[0] == 0                                   # 2 m 内の知人は居ない=招待
    got = np.asarray(got)
    inner = np.isin(got, [1, 2, 3, 4, 5]).mean()
    nxt = np.isin(got, [6, 7, 8]).mean()
    rest = (got == 9).mean()
    assert inner == pytest.approx(0.40, abs=0.04) and nxt == pytest.approx(0.20, abs=0.03)
    assert rest == pytest.approx(0.40, abs=0.04)
    again = [int(rel.choose_talk_partners(a, t, np.array([0]), np.array([9]), np.array([False]),
                                          np.array([3]))[0][0]) for t in range(101, 201)]
    assert again == got[:100].tolist()                          # 同じ salt・tick・体=同じ相手
    assert int(rel.chosen_count.sum()) >= 3000                  # T5 の材料(選ばれた回数)


def test_named_rows_keep_partner_and_no_edges_in_cell_keeps_fallback():
    a, _lay, rel = _eight_edges()
    out, _o = rel.choose_talk_partners(a, 101, np.array([0]), np.array([5]), np.array([True]), np.array([3]))
    assert out[0] == 5                                          # 名指しは変えない
    with a.writable():
        a.cell[1:9] = 7                                         # 辺の相手が全員よそのセル
    out, origin = rel.choose_talk_partners(a, 101, np.array([0]), np.array([9]), np.array([False]),
                                           np.array([3]))
    assert out[0] == 9 and origin[0] == 0                       # 従来どおり(D-31 (a))


def test_chance_puts_acquaintances_within_2m_first_and_origin_labels():
    a, _lay, rel = _eight_edges()
    with a.writable():
        a.xy[7] = a.xy[0] + np.array([1.0, 0.0], dtype=np.float32)   # 体 7 だけ 1 m
    outs = {int(rel.choose_talk_partners(a, t, np.array([0]), np.array([9]), np.array([False]),
                                         np.array([3]))[0][0]) for t in range(101, 201)}
    assert outs == {7}                                          # 2 m 内の知人が第一候補(残りの層は付けない)
    _out, origin = rel.choose_talk_partners(a, 150, np.array([0]), np.array([9]), np.array([False]),
                                            np.array([3]))
    assert origin[0] == 1 and rel.pop_origin(0) == 1 and rel.pop_origin(0) == 0
    _out, origin = rel.choose_talk_partners(a, 150, np.array([0]), np.array([9]), np.array([False]),
                                            np.array([ACQ]))
    assert origin[0] == 2                                       # 知人出現の起床の呼
    rel.origin_of.clear()
    _out, _origin = rel.choose_talk_partners(a, 150, np.array([0]), np.array([9]), np.array([False]),
                                             np.array([3]), record_origin=False)
    assert 0 not in rel.origin_of


def test_invite_off_only_labels_origins():
    a = table()
    lay, rel = layer(a)
    talk(lay, a, 100, 0, 1)
    out, origin = rel.choose_talk_partners(a, 101, np.array([0]), np.array([9]), np.array([False]),
                                           np.array([3]))
    assert out[0] == 9 and origin[0] == 0 and rel.chosen_count is None   # 抽選の口を開いていない


# ================================================================= (c) 知人出現の起床
def test_acquaintance_appearance_wakes_once_per_pair_hour():
    a = table()
    lay, rel = layer(a, tau=-10.0)
    talk(lay, a, 0, 0, 1)
    talk(lay, a, 0, 1, 0)
    rel.enable_acquaintance_wake()
    with a.writable():
        a.cell[1] = 5
    got = rel.acquaintance_candidates(a, 1)
    assert got[0].size == 0                                     # 1 tick 目は「前 tick」が無い
    with a.writable():
        a.cell[1] = 3                                           # 体 1 が体 0 のセルへ来た
    ag, cond, cls = rel.acquaintance_candidates(a, 2)
    assert sorted(ag.tolist()) == [0, 1] and (cond == ACQ).all()   # 両方から見て「現れた」
    rel.stamp_acquaintance(np.array([0]), 2)                    # 体 0 だけ呼ばれた
    with a.writable():
        a.cell[1] = 5
    rel.acquaintance_candidates(a, 3)
    with a.writable():
        a.cell[1] = 3
    ag, _c, _k = rel.acquaintance_candidates(a, 4)
    assert ag.tolist() == [1] and rel.stats["acq_pair_refractory"] == 1   # 体 0 は同一相手 60 分
    with a.writable():
        a.cell[1] = 5
    rel.acquaintance_candidates(a, 70)
    with a.writable():
        a.cell[1] = 3
    ag, _c, _k = rel.acquaintance_candidates(a, 71, eligible=np.arange(a.n) != 1)
    assert ag.tolist() == [0]                                   # 60 分を過ぎた・体 1 は候補外(寝ている等)


def test_acquaintance_ignores_edges_below_tau():
    a = table()
    lay, rel = layer(a, tau=5.0)                                # 誰も生きていない
    talk(lay, a, 0, 0, 1)
    rel.enable_acquaintance_wake()
    with a.writable():
        a.cell[1] = 5
    rel.acquaintance_candidates(a, 1)
    with a.writable():
        a.cell[1] = 3
    assert rel.acquaintance_candidates(a, 2)[0].size == 0 and rel.stats["acq_not_live"] >= 1


# ================================================================= (d) 同席の書き手(Q91)
def test_copresent_writes_once_per_pair_day_after_5_minutes_within_2m():
    a = table()
    lay, rel = layer(a)
    talk(lay, a, 0, 0, 1)
    rel.enable_copresent()
    r = a.registry
    n0 = int(r.rel_n[0, 0])
    with a.writable():
        a.xy[1] = a.xy[0] + np.array([1.5, 0.0], dtype=np.float32)
    for tick in range(1, 5):
        rel.copresent_step(a, tick)
    assert int(r.rel_n[0, 0]) == n0                             # 4 分ではまだ
    rel.copresent_step(a, 5)
    assert int(r.rel_n[0, 0]) == n0 + 1 and int(r.rel_last[0, 0]) == 5
    for tick in range(6, 200):
        rel.copresent_step(a, tick)
    assert int(r.rel_n[0, 0]) == n0 + 1                          # 同じ日はもう書かない
    for tick in range(1440, 1445):
        rel.copresent_step(a, tick)
    assert int(r.rel_n[0, 0]) == n0 + 2                          # 次の日にまた 1 本
    assert int(r.rel_sign[0, 0]) == 1                            # 符号は +0(会話の +1 のまま)
    with a.writable():
        a.xy[1] = a.xy[0] + np.array([2.5, 0.0], dtype=np.float32)
    for tick in range(2880, 2900):
        rel.copresent_step(a, tick)
    assert int(r.rel_n[0, 0]) == n0 + 2                          # 2 m より遠い
    assert rel.stats["copresent_events"] == 2
    assert int((r.rel_partner[2] != -1).sum()) == 0              # 表に居ない同席者は書かない


# ================================================================= (e) 押し出し(新しい相手も辺として比べる)
def test_newcomer_is_dropped_when_the_table_is_all_stronger():
    a = table(n=6, k=2)
    lay, rel = layer(a)
    talk(lay, a, 100, 0, 1, times=5)
    talk(lay, a, 100, 0, 2, times=5)
    talk(lay, a, 100, 0, 3)                                     # 表(2 本)はどちらも n=5 > 新しい n=1
    assert set(a.registry.rel_partner[0].tolist()) == {1, 2} and rel.stats["newcomer_dropped"] == 1
    talk(lay, a, 100 + 100_000, 0, 4)                           # 古くなった表の最弱より新しい方が強い
    assert 4 in a.registry.rel_partner[0].tolist() and rel.stats["evictions"] == 1


# ================================================================= (f) 会話マネージャの起点の計数
def test_conversation_origin_counts_and_default_counters_unchanged():
    base = ConversationManager(master_seed=1)
    assert not any(k.startswith("origin") for k in base.counters())
    m = ConversationManager(master_seed=1)
    m.track_origins(RL.REL_ORIGINS)
    assert m.register_pending(1, 2, 0, 5, same_cell=True, origin=1)
    m.note_origin(1, "invites")
    s = m.resolve_pending(2, 1, accepted=True)
    assert s is not None and s.origin == 1
    assert m.register_pending(3, 4, 0, 5, same_cell=True, origin=2)
    m.note_origin(2, "invites")
    m.expire_pending(10_000)
    got = m.origin_summary()
    assert got["chance"]["accepted"] == 1 and got["chance"]["accept_rate"] == 1.0
    assert got["acquaintance"]["expired"] == 1 and got["invite"]["invites"] == 0
    m.note_origin(-1, "invites")                                 # 記録しない行は何もしない
    assert set(m.counters()) == set(base.counters())             # 既定の計数の鍵は同じ


# ================================================================= (g) classical の「最初の未知の人」
def test_classical_near_strangers_and_rest_pick_is_hashed():
    from shibuya.engine.classical import _near_strangers

    prompt = "x\n[B5 近接] 近くの人物: P-3(知人)(距離 2m)、P-8(未知)(距離 5m)、P-9(未知)\ny"
    assert _near_strangers(prompt, 0) == [8, 9]
    assert _near_strangers(prompt, 8) == [9]
    assert _near_strangers("[B5 近接] 近くの人物: P-3(知人)", 0) == []
    a = table()
    _lay, rel = layer(a)
    assert rel.pick_rest(5, 0, [4, 2]) == 2                     # 抽選の口が無い=小さい方(従来に近い)
    rel.enable_invite(b"salt")
    got = [rel.pick_rest(t, 0, list(range(1, 11))) for t in range(2000)]
    assert rel.pick_rest(7, 0, [3, 9]) == rel.pick_rest(7, 0, [9, 3])        # 決定論・並びに依らない
    assert np.mean(got) == pytest.approx(5.5, abs=0.3)          # id の小さい人に寄らない
    assert rel.pick_rest(1, 0, []) == -1 and rel.pick_rest(1, 0, [0]) == -1


# ================================================================= (h) 在職期間と τ
def test_default_tau_is_the_rederived_value_and_a_single_talk_lives_hours():
    """第300 訂正(8b′): n=共在の日数で再逆算した τ=−2.346(旧=在職期間ハッシュ v1)。第2波 §2A 項 2: 在職期間の
    ハッシュを直した v2(既定)で同じ手順で再逆算した τ=−2.322。会話 1 回の辺(n=1)はどちらでも約 7 時間生きる
    (v1 7.3 時間・v2 6.9 時間)。"""
    assert RL.REL_TAU_V1 == pytest.approx(-2.346) and RL.REL_TAU_V2 == pytest.approx(-2.322)
    assert RL.REL_TAU == RL.REL_TAU_V2 and RL.DEFAULT_REL_TENURE_HASH == "v2"
    assert RL.REL_TAU_BY_TENURE_HASH == {"v2": RL.REL_TAU_V2, "v1": RL.REL_TAU_V1}
    assert RL.REL_TENURE_WEEKS == 13.0
    for tau in (RL.REL_TAU_V1, RL.REL_TAU_V2):
        a = table()
        lay, rel = layer(a, tau=tau)
        talk(lay, a, 100, 0, 1)
        assert rel.edges(a, 0, 100).partner.tolist() == [1]          # ln 2 ≥ τ(会話 1 回で知人になる)
        assert rel.edges(a, 0, 100 + 6 * 60).partner.tolist() == [1]   # 6 時間後もまだ
        assert rel.edges(a, 0, 100 + 8 * 60).partner.size == 0          # 8 時間後には τ を下回る


def test_copresence_days_counts_weekdays_with_any_shared_slot():
    from shibuya.agents.weekly import WeeklySchedule

    # 体 0,1 が曜日 0 と 2 に同じセル(曜日 2 は 15 分だけ)・体 2 は別のセル
    rows = {0: [(0, 540, 600, 5), (2, 540, 600, 5)], 1: [(0, 560, 700, 5), (2, 590, 610, 5)], 2: [(0, 540, 600, 6)]}
    n = 3
    counts = np.zeros(n * 7, dtype=np.int64)
    st, en, cl = [], [], []
    for a_ in range(n):
        for d, s, e, c in rows[a_]:
            counts[a_ * 7 + d] += 1
    order = []
    for a_ in range(n):
        for d in range(7):
            for dd, s, e, c in rows[a_]:
                if dd == d:
                    order.append((s, e, c))
    for s, e, c in order:
        st.append(s)
        en.append(e)
        cl.append(c)
    off = np.zeros(n * 7 + 1, dtype=np.int64)
    np.cumsum(counts, out=off[1:])
    k = len(st)
    w = WeeklySchedule(None, np.arange(n, dtype=np.int64), off, np.asarray(st, dtype=np.int16),
                       np.asarray(en, dtype=np.int16), np.zeros(k, dtype=np.int8), np.ones(k, dtype=np.int8),
                       np.asarray(cl, dtype=np.int32), np.zeros(k, dtype=np.int16))
    days = RL.copresence_days(RL.slot_cells(w, np.arange(n)))
    assert days[0, 1] == days[1, 0] == 2 and days[0, 2] == 0 and days[0, 0] == 0


# ================================================================= (i) ラン
WORLD = "data/world/v2"


def _real_world_or_skip() -> None:
    from shibuya.world.assets import assets_available

    if not assets_available(WORLD):
        pytest.skip("W 資産(data/world/v2)が無い")


def test_run_8b_on_is_deterministic_and_reports_origins_and_l4_share():
    _real_world_or_skip()
    from shibuya import cli

    kw = dict(n_agents=1500, seed=1, world_dir=WORLD, vocab_version="v3", memory="on", relations="on",
              ticks=720)
    r1 = cli.run(**kw)
    r2 = cli.run(**kw)
    assert r1.final_hash == r2.final_hash and r1.llm_calls == r2.llm_calls
    m = r1.run_manifest_fields()
    assert 0.0 <= m["l4_conversation_share"] <= 1.0 and m["l4_conversation_line"] == 0.15
    rs = m["relations"]
    assert set(rs["origins"]) == set(RL.REL_ORIGINS) and rs["acquaintance_wake"] and rs["invite_weights"]
    assert m["calls_by_condition"]["ACQUAINTANCE"] == rs["counts"].get("acq_woken", 0)
    assert "conversation_origins" in m["decision_layers"]
    off = cli.run(**{**kw, "relations": "off"})
    assert "conversation_origins" not in off.run_manifest_fields()["decision_layers"]
    with pytest.raises(ValueError):
        cli.run(**{**kw, "relations": "off", "rel_copresent": "on"})


def test_cli_has_the_8b_flags():
    text = (SRC / "cli.py").read_text(encoding="utf-8")
    for flag in ('"--rel-tenure-weeks"', '"--rel-invite"', '"--rel-acq-wake"', '"--rel-copresent"'):
        assert flag in text


def test_8b_per_tick_paths_are_array_ops():
    """P4: 毎 tick の検出・同席・抽選に体数比例の for/while を書かない(宣言した小さな反復だけ)。"""
    tree = ast.parse((SRC / "engine/relations.py").read_text(encoding="utf-8"))
    names = {"choose_talk_partners", "copresent_step", "acquaintance_candidates", "stamp_acquaintance",
             "_layer_weights", "_rank_live", "lifetime_days"}
    allowed_iters = ("REL_INVITE_LAYERS", ".items()", "zip(a.tolist(), origin.tolist())", "(('inner'",
                     "(('initial'")

    def ok(s: ast.AST) -> bool:
        it = ast.unparse(s.iter) if isinstance(s, ast.For) else ""
        return any(x in it for x in allowed_iters)

    bad = [f"{n.name}:{s.lineno}" for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef) and n.name in names
           for s in ast.walk(n) if isinstance(s, ast.While) or (isinstance(s, ast.For) and not ok(s))]
    assert not bad, bad
