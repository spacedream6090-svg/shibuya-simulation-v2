"""D-120 7c: **想起優先の候補合成**(N6 (a))・**到達可能性**(N7 (a))・**決め手**(N8 (a))・B5 の店の項(v1.3)の
テスト(第298)。

正典: ``docs/design/v2-store-memory-implementation-agenda.md`` §3(段 7c の 1〜6)。
見るもの: (a) 想起できた店=A ≥ τ ∧ 向き ≥ 0(看板だけも入る)∧ 意図に合う ∧ 営業中 ∧ 到達可能 ∧ 願望水準 →
精度の分布 (b) 到達可能性=次の予定までの歩ける距離(上限つきの制約) (c) 選び手 classical だけ・名指しは
想起優先を通らない・セル外の店は名指しの意図 (d) 決め手と初回率・店頭の割合 (e) B5: 店の行がエピソードと
同じ score 順に競う・同じ店は 1 件・項の定型 ≤15 tok (f) ラン: 既定は 1 バイトも変わらない・腕の切替口。
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.agents.state import AgentState, IntentKind, ResultCode
from shibuya.engine import memory as M
from shibuya.engine import store_memory as SM
from shibuya.engine.chooser import ClassicalChooser, NearestChooser
from shibuya.engine.poi_target import TargetResolver
from shibuya.engine.store_choice import CHOICE_REASONS, StoreChoice, walk_m_per_tick
from shibuya.perception import templates as T
from shibuya.perception.channels import estimate_tokens
from shibuya.perception.renderer import memory_item_text
from shibuya.world.state import World

SRC = Path("src/shibuya")
OK = int(ResultCode.OK)
SELF, WOM, SIGN = (SM.STORE_SOURCE_BIT[s] for s in ("self", "wom", "signage"))


def world() -> World:
    return World.synthetic(n_cells=9, seed=1)


def setup(n: int = 3, *, walk: float = 10.0, boundary: tuple[tuple[int, int], ...] = ()):
    w = world()
    a = AgentState(n, memory_columns=True, memory_n=16, store_memory_columns=True, store_memory_n=8)
    with a.writable():
        a.cell[:] = 0
        a.money[:] = 10_000
        a.hunger[:] = 5
    lay = M.MemoryLayer(n, 16, minutes_per_tick=1.0)
    lay.enable_store(8, poi_cell=np.asarray(w.pois.cell))
    ba = np.array([b[0] for b in boundary], dtype=np.int64)
    bt = np.array([b[1] for b in boundary], dtype=np.int64)
    sc = StoreChoice(lay, w, n, seed=1, boundary_agent=ba, boundary_tick=bt,
                     walk_m_per_tick=np.full(n, walk), intent_max_ticks=60)
    return w, a, lay, sc


def put(lay, a, tick, agent, poi, valence, bit):
    lay.store.write(a, tick, np.array([agent]), np.array([poi]), np.array([valence]), np.array([bit]))


def masks(w):
    n = w.n_poi
    eat = np.asarray(w.eatery_mask, dtype=bool)
    return eat, np.ones(n, dtype=bool), np.ones(n, dtype=bool), eat


# ================================================================= (a)(b) 想起優先
def test_recall_picks_recallable_fitting_reachable_stores_by_precision():
    w, a, lay, sc = setup()
    fit, open_now, stock, eat = masks(w)
    eats = np.flatnonzero(eat)            # 飲食店(セル 1・3・4・5 …)
    p_self, p_sign, p_bad = int(eats[0]), int(eats[1]), int(eats[2])
    put(lay, a, 100, 0, p_self, 1, SELF)   # 自分の訪問 +1(精度 1)
    put(lay, a, 100, 0, p_sign, 0, SIGN)   # 看板だけ(向き 0・精度 1/16)=候補に入る(Q76)
    put(lay, a, 100, 0, p_bad, -1, SELF)   # 向き −1 は入らない
    got = {sc.recall(a, 0, 101 + t, 0, fit, open_now, stock, eat, True)[0] for t in range(200)}
    assert got == {p_self, p_sign}
    # 分布は精度に比例(自分 1 : 看板 1/16)
    picks = [sc.recall(a, 0, 101 + t, 0, fit, open_now, stock, eat, True)[0] for t in range(400)]
    assert picks.count(p_self) > 10 * picks.count(p_sign) > 0
    assert sc.recall(a, 0, 101, 0, fit, open_now, stock, eat, True)[1] in ("self", "signage")
    # A < τ(古い)は想起できない
    assert sc.recall(a, 0, 100 + 5_000, 0, fit, open_now, stock, eat, True) == (-1, "")
    assert sc.stats["recall:none_fit"] >= 1


def test_recall_respects_fit_open_and_aspiration():
    w, a, lay, sc = setup()
    fit, open_now, stock, eat = masks(w)
    p = int(np.flatnonzero(eat)[0])
    put(lay, a, 100, 0, p, 1, SELF)
    closed = open_now.copy()
    closed[p] = False
    assert sc.recall(a, 0, 101, 0, fit, closed, stock, eat, True)[0] == -1           # 閉店
    assert sc.recall(a, 0, 101, 0, ~fit, open_now, stock, eat, True)[0] == -1        # 意図に合わない
    with a.writable():
        a.money[0] = 0
    assert sc.recall(a, 0, 101, 0, fit, open_now, stock, eat, True)[0] == -1         # 予算外
    assert sc.stats["recall:none_aspiration"] == 1
    with a.writable():
        a.hunger[0] = 10                                                              # とても空腹=条件なし
    assert sc.recall(a, 0, 101, 0, fit, open_now, stock, eat, True)[0] == p


def test_reachability_is_a_capped_constraint_not_a_distance_decay():
    w, a, lay, sc = setup(walk=10.0, boundary=((0, 110),))                            # 次の予定まで 9 tick
    fit, open_now, stock, eat = masks(w)
    pc = np.asarray(w.pois.cell)
    far = int(next(j for j in np.flatnonzero(eat) if w.assets.cell_dist[0, pc[j]] >= 100))
    put(lay, a, 100, 0, far, 1, SELF)
    assert sc.recall(a, 0, 101, 0, fit, open_now, stock, eat, True)[0] == -1         # 100 m ÷ 10 m/tick > 9
    assert sc.stats["recall:none_reachable"] == 1
    w2, a2, lay2, sc2 = setup(walk=50.0, boundary=((0, 110),))                        # 歩速が速ければ届く
    put(lay2, a2, 100, 0, far, 1, SELF)
    assert sc2.recall(a2, 0, 101, 0, fit, open_now, stock, eat, True)[0] == far
    assert sc.ticks_to_next_plan(1, 101) == 1 << 30                                   # 予定の無い体は上限なし
    assert walk_m_per_tick(w, 2)[0] == pytest.approx(float(np.mean(w.assets.edge_len_m)))


# ================================================================= (c) 解決の経路
def resolver(chooser, sc):
    w = sc.world
    r = TargetResolver(w, chooser, seed=1)
    r.store_choice = sc
    return r


def test_resolver_uses_recall_first_only_with_classical_and_unnamed_targets():
    from shibuya.engine import commit as Cm

    w, a, lay, sc = setup()
    _fit, _o, _s, eat = masks(w)
    pc = np.asarray(w.pois.cell)
    here = int(np.flatnonzero(eat & (pc == 1))[0])
    away = int(np.flatnonzero(eat & (pc == 3))[0])
    t0 = 700  # 11:40=営業中(合成世界の既定 10:00〜22:00)
    with a.writable():
        a.cell[:] = 1
    put(lay, a, t0 - 5, 0, away, 1, SELF)
    r = resolver(ClassicalChooser(), sc)
    intents: dict = {}
    got = r.resolve(a, t0, np.array([0]), np.array([Cm.ACT_EAT]), None, is_eat=np.array([True]),
                    is_buy_like=np.array([False]), intent_out=intents)
    assert got[0] == -1 and intents == {0: (away, int(IntentKind.POI_NAMED))}     # セル外 → 名指しの意図
    assert r.stats["intent:recall"] == 1 and sc.stats["choice:self"] == 1
    put(lay, a, t0 - 5, 1, here, 0, SIGN)
    got = r.resolve(a, t0, np.array([1]), np.array([Cm.ACT_EAT]), None, is_eat=np.array([True]),
                    is_buy_like=np.array([False]), intent_out={})
    assert got[0] == here and sc.stats["choice:signage"] == 1                       # セル内 → その場で
    # 選び手 nearest は想起優先を通らない(決め手は可視順)
    w3, a3, lay3, sc3 = setup()
    with a3.writable():
        a3.cell[:] = 1
    put(lay3, a3, t0 - 5, 0, away, 1, SELF)
    r3 = resolver(NearestChooser(), sc3)
    got = r3.resolve(a3, t0, np.array([0]), np.array([Cm.ACT_EAT]), None, is_eat=np.array([True]),
                     is_buy_like=np.array([False]), intent_out={})
    assert got[0] >= 0 and int(pc[got[0]]) == 1 and sc3.stats["recall:attempts"] == 0
    assert sc3.stats["choice:visible"] == 1


# ================================================================= (d) 決め手・初回率・店頭
def test_reasons_by_hour_and_first_visits_and_storefront_share():
    w, a, lay, sc = setup()
    sc.note(0, 5, "visible", 61)
    sc.note(1, 7, "self", 125)
    # 体 0 が店 5 で食事の成立(行が無い=初回)・体 1 が店 7 で購入の成立(自分の行あり=再訪)
    put(lay, a, 10, 1, 7, 1, SELF)
    lay.record(a, 130, np.array([0, 1]), np.array([M.EVENT_KINDS["eat"], M.EVENT_KINDS["buy"]]),
               np.array([-1, -1]), np.array([5, 7]), np.array([OK, OK]), np.array([0, 0]))
    s = sc.summary()
    assert s["choices_by_hour"][1]["visible"] == 1 and s["choices_by_hour"][2]["self"] == 1
    assert s["visits"] == 2 and s["first_visit_no_row"] == 1 and s["first_visit_no_self"] == 1
    assert s["first_visit_no_self_by_reason"]["visible"] == 1
    assert s["storefront_share_of_first_no_self"] == 1.0
    assert list(CHOICE_REASONS) == ["named", "visible", "nearby", "habit", "self", "wom", "signage", "net"]


# ================================================================= (e) B5 の店の項
def test_store_rows_compete_with_episodes_in_recall_and_dedupe_by_store():
    w, a, lay, sc = setup()
    put(lay, a, 100, 0, 3, 1, SELF | SIGN)         # 店 3: 精度 1+1/16
    put(lay, a, 100, 0, 5, 0, SIGN)                # 店 5: 看板だけ
    lay.record(a, 100, np.array([0]), np.array([M.EVENT_KINDS["buy"]]), np.array([-1]), np.array([3]),
               np.array([OK]), np.array([1]))       # 同じ店 3 のエピソード
    got = lay.recall(a, 0, 101, int(M.WakeCondition.CONVERSATION_TURN))
    stores = [g for g in got if g.kind == M.STORE_ITEM_KIND]
    assert {g.obj for g in got} == {3, 5} and len(got) == 2                          # 同じ店 3 は 1 件だけ
    assert lay.recall_stats["store_dedup_skipped"] >= 1
    assert all(g.row >= lay.n_rows for g in stores)                                  # 店の行は N 以上
    lay.store_recall_scope = "conversation"
    assert all(g.kind != M.STORE_ITEM_KIND for g in lay.recall(a, 0, 101, 3))        # 会話だけの腕


def item(**kw):
    base = dict(row=0, last_tick=0, kind=M.STORE_ITEM_KIND, partner=-1, obj=0, result=0, cell=1, gist="",
                valence=0, source=0)
    base.update(kw)
    return SimpleNamespace(**base)


def test_store_item_templates_and_cap():
    names = ["スターバックス", "高等学校前の店" + "あ" * 40]

    def fmt(it):
        return memory_item_text(it, hhmm="9:05", poi_names=names, place_ids=["c0", "c1"], result_text={})

    assert fmt(item(valence=1, source=SELF)) == "最近 スターバックス に行った(良かった)。"
    assert fmt(item(valence=0, source=SELF | SIGN)) == "最近 スターバックス に行った(知っている)。"
    assert fmt(item(valence=-1, source=SELF)) == "最近 スターバックス に行った(よくなかった)。"
    assert fmt(item(valence=0, source=SIGN)) == "スターバックス を知っている。"
    assert fmt(item(valence=1, source=WOM)) == "スターバックス は良いと聞いた。"
    assert fmt(item(valence=-1, source=WOM)) == "スターバックス はよくないと聞いた。"
    assert fmt(item(obj=1, valence=1, source=SELF)) == "最近 c1 に行った(良かった)。"      # ⑥ 等 → セル ID
    long = memory_item_text(item(obj=0, valence=1, source=SELF), hhmm="", poi_names=["ラ" * 60],
                            place_ids=["c0", "c1"], result_text={})
    assert estimate_tokens(long) <= T.MEMORY_STORE_ITEM_MAX_TOKENS == 15
    assert T.TEMPLATE_VERSION == "v1.3"
    from shibuya.perception import renderer as Rn

    assert Rn._STORE_ITEM_KIND == M.STORE_ITEM_KIND and Rn._STORE_SELF_BIT == SELF


# ================================================================= (f) ラン
WORLD = "data/world/v2"


def _real_world_or_skip() -> None:
    from shibuya.world.assets import assets_available

    if not assets_available(WORLD):
        pytest.skip("W 資産(data/world/v2)が無い")


def test_run_default_is_unchanged_and_store_choice_is_reported():
    _real_world_or_skip()
    from shibuya import cli

    kw = dict(n_agents=300, seed=1, world_dir=WORLD, vocab_version="v3", policy="classical",
              chooser="classical", memory="on")
    mem = cli.run(**kw)
    assert mem.run_manifest_fields()["store_choice"] == {}
    on = cli.run(store_memory="on", **kw)
    s = on.run_manifest_fields()["store_choice"]
    assert s["counts"]["recall:attempts"] > 0 and s["counts"].get("recall:chosen", 0) > 0
    assert s["visits"] > 0 and s["arms"] == {"store_wom": True, "store_signage": True,
                                             "store_recall_scope": "all", "chooser": "classical"}
    assert sum(s["choices_by_reason"].values()) == sum(sum(h.values()) for h in s["choices_by_hour"])
    off_sign = cli.run(store_memory="on", store_signage="off", **kw)
    ss = off_sign.run_manifest_fields()["store_memory_summary"]
    assert ss["rows_with_source_bit"]["signage"] == 0


def test_arm_switches_are_checked():
    from shibuya.engine.run import run_day

    for bad in (dict(store_wom="maybe"), dict(store_signage="x"), dict(store_recall_scope="some")):
        with pytest.raises(ValueError):
            run_day(n_agents=10, ticks=2, memory="on", store_memory="on", **bad)
    text = (SRC / "cli.py").read_text(encoding="utf-8")
    for flag in ('"--store-wom"', '"--store-signage"', '"--store-recall-scope"'):
        assert flag in text


def test_recall_first_is_array_ops():
    """P4: 想起優先と到達可能性は 1 体の ≤ 32 行の配列演算(for/while を書かない)。"""
    tree = ast.parse((SRC / "engine/store_choice.py").read_text(encoding="utf-8"))
    names = {"recall", "reachable", "ticks_to_next_plan", "on_visit"}
    bad = [f"{n.name}:{s.lineno}" for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef) and n.name in names
           for s in ast.walk(n) if isinstance(s, (ast.For, ast.While))]
    assert not bad, bad
