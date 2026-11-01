"""第 6 期 6-5 思い浮かぶ/見覚え(MR4)と人も記憶の一つ(器=腕 ``--memory-people memory``)。

- 器の単体: 人の行の鍵は (種類, 相手)・重要度 0・関係の種類は重ねても前の値・思い浮かぶ=A ≥ τ・見覚え=目の前の手がかりを
  足すと超える(思い浮かばない人も見覚えはある)・忘れる=消す(満杯の体に空きを作るとき)・それでも足りなければ幅を倍に。
- 最初の関係はデータから(``seed_people``=開始前の経験=負の時刻・n と最初と最後の時刻)。
- 関係の読み口(``PeopleRelationLayer``): 関係の表 ``rel_*`` を読まない・書かない(AST=子のクラスと、子が上書きしない親の
  メソッドのうち子の道で呼ばれるもの)。負の対照: 腕 table のランは ``write_relations`` を呼ぶ・腕 memory のランは呼ばない。
- 上限なしの道: 最初の幅を 4 にして合成の世界の 1 日=幅が倍に広がっても壊れない・体あたりの行が 4 を超える。
  (``slow``)世界資産 5,000 体の 1 日=幅 8 から広がる・関係の読み口が人の行から辺を返す。
- 再開: 上限なしの腕は止める(器が表の写しでない=本段の限界)。
- 〔検収 M2〕種類ごとの上限(出来事・人): 器の行の幅は上限の和まで倍に・その種類の行が上限に届いた体は思い浮かぶ強さ A
  (手がかり無し)の一番低い行を消す(同点は最後に触れた時刻の古い順・次に行の番号)・計数(幅を倍にした回・消した行)・
  最初の関係も上限の中。〔検収 M4〕店の評価の行も同じ作り(``engine.memory_shops``=幅 32 から倍に・上限で A の一番低い行を
  上書き)・腕 memory のランは体の表の ``sm_*`` を書かず店の行の表に書く・小さな上限でも壊れない。
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from pathlib import Path

import numpy as np
import pytest

from shibuya.core.time_consts import NS_PER_SECOND, STEPS_PER_DAY
from shibuya.engine import memory_m1 as M1
from shibuya.engine import relations as REL
from shibuya.engine import relations_people as RP
from shibuya.engine import resolve as R
from shibuya.engine.memory_store import LegacyEvent, MemoryStore
from shibuya.engine.run import run_day

from tests.engine.memory._mr65 import KW, arms, mr65

S = NS_PER_SECOND
ROOT = Path(__file__).resolve().parents[3]
WORLD = ROOT / "data" / "world" / "v2"
P = M1.PERSON_KIND


def _store(n: int = 4, rows: int = 4) -> MemoryStore:
    ms = MemoryStore(n, rows, step_seconds=60, minutes_per_step=1.0)
    ms.enable_arms(m1=M1.M1State(n, n * rows, tau=M1.tau_from_m0(-2.0), seed=1), uncapped=True)
    return ms


def _touch(ms: MemoryStore, a: int, p: int, t_s: int, rel: int = 5) -> int:
    return int(ms.remember(a, LegacyEvent(t_s * S, P, p, rel, 0, 1), 0, "legacy")[0])


def test_person_rows_key_importance_and_kind_kept():
    ms = _store()
    r1 = _touch(ms, 0, 2, 60, rel=1)
    r2 = _touch(ms, 0, 2, 120, rel=5)  # 同じ人=同じ行(関係の種類は前の 1 のまま)
    assert r1 == r2 and int(ms._ms_n[r1]) == 2 and int(ms._lg_object[r1]) == 1 and int(ms._ms_imp[r1]) == 0
    partner, rel, A, A_fam, row = ms.people_rows(np.asarray([0, 1]), 180 * S)
    assert partner[0, r1] == 2 and rel[0, r1] == 1 and np.isfinite(A[0, r1]) and (partner[1] == -1).all()
    # 人の行は出来事の想起に出ない
    assert ms.recall(0, 180 * S, 3) == ()


def test_recall_and_recognition_and_forgetting():
    ms = _store(n=16, rows=2)
    b = int(np.flatnonzero((ms.m1.scale >= 0.6) & (ms.m1.scale <= 0.9))[0])
    _touch(ms, b, 1, 0)
    day = 24 * 3600
    # 1 回会っただけの人: 少し後は思い浮かぶ・5 日後は思い浮かばないが見覚えはある(目の前の手がかりで超える)
    p, _rel, A, Af, _r = ms.people_rows(np.asarray([b]), 60 * S)
    assert A[0][p[0] == 1][0] >= ms.m1.tau
    p, _rel, A, Af, _r = ms.people_rows(np.asarray([b]), 5 * day * S)
    j = p[0] == 1
    assert A[0][j][0] < ms.m1.tau
    assert M1.recognize_mask(Af[0][j], ms.m1.tau, True)[0] and not M1.recognize_mask(Af[0][j], ms.m1.tau, False)[0]
    # 忘れる=消す: 見覚えにも届かない古さの行は、満杯の体に空きを作るときに消える(幅は広げない)。倍率が 0.9 以上の体で
    # (倍率が小さい体=忘れるのが遅い体は int64 の時刻の範囲で忘れない=宣言)
    ms2 = _store(n=8, rows=2)
    a = int(np.flatnonzero(ms2.m1.scale >= 0.9)[0])
    far = 2 * 10**9  # 約 63 年(1 回だけ会った人は約 5 か月で消える=memory_m1.D_FAMILIAR の注)
    _touch(ms2, a, 1, 0)
    _touch(ms2, a, 2, 0)
    _touch(ms2, a, 3, far)
    assert ms2.n_rows == 2 and ms2.store_counts.get("forgotten", 0) >= 1
    p, *_ = ms2.people_rows(np.asarray([a]), far * S)
    assert 3 in p[0].tolist()
    # 負の対照: まだ見覚えのある人(少し後)は消さずに幅を広げる
    ms3 = _store(n=8, rows=2)
    _touch(ms3, a, 1, 0)
    _touch(ms3, a, 2, 0)
    _touch(ms3, a, 3, 3600)
    assert ms3.n_rows == 4 and ms3.store_counts.get("forgotten", 0) == 0


def test_full_agent_doubles_the_width_when_nothing_is_forgotten():
    ms = _store(n=3, rows=2)
    for j in range(5):
        _touch(ms, 1, 10 + j, 60 * (j + 1))
    assert ms.n_rows == 8 and ms.store_counts["rows_resized"] == 2
    p, *_ = ms.people_rows(np.asarray([1]), 400 * S)
    assert sorted(x for x in p[0].tolist() if x >= 0) == [10, 11, 12, 13, 14]
    assert ms.m1.recent_ns.shape == (3 * 8, M1.K_RECENT)


def test_seed_people_from_the_initial_edges():
    ms = _store(n=3, rows=2)
    ns = 60 * S
    got = ms.seed_people([0, 0, 0, 1], [1, 2, 1, 0], [1, 2, 1, 1], [91, 65, 91, 91],
                         np.asarray([-13 * 7 * 1440, -8 * 7 * 1440, -1, -13 * 7 * 1440]) * ns,
                         np.asarray([-60, -600, -1, -60]) * ns)
    assert got == 3  # 同じ (体, 相手) は 1 行
    p, rel, A, _Af, _r = ms.people_rows(np.asarray([0, 1]), 0)
    assert sorted(x for x in p[0].tolist() if x >= 0) == [1, 2] and np.isfinite(A[0][p[0] >= 0]).all()
    assert sorted(x for x in rel[0].tolist() if x > 0) == [1, 2] and p[1].tolist().count(0) == 1
    with pytest.raises(RuntimeError, match="1 回だけ"):
        ms.seed_people([2], [0], [1], [1], [0], [0])


# ---------------------------------------------------------------- 関係の表を読まない(AST)
_REL_COLS = {"rel_partner", "rel_kind", "rel_sign", "rel_first", "rel_last", "rel_n"}


def _attrs(fn) -> set[str]:
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    return {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}


def test_people_layer_does_not_touch_the_relation_table():
    src = Path(RP.__file__).read_text(encoding="utf-8")
    names = {n.attr for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Attribute)}
    assert not (names & _REL_COLS) and "write_relations" not in names
    sub = {k for k, v in vars(RP.PeopleRelationLayer).items() if callable(v) or isinstance(v, (property, staticmethod))}
    # 親のメソッドで関係の表を読むものは、子が全部上書きする(choose_talk_partners は読み口 _partner_rows・activation を通る)
    base_readers = {name for name, fn in vars(REL.RelationLayer).items()
                    if inspect.isfunction(fn) and (_attrs(fn) & _REL_COLS or "write_relations" in _attrs(fn))}
    assert base_readers and base_readers <= sub, sorted(base_readers - sub)
    cho = _attrs(REL.RelationLayer.choose_talk_partners)
    assert not (cho & _REL_COLS) and {"_partner_rows", "activation"} <= cho


def test_people_arm_run_never_writes_the_relation_table(monkeypatch):
    calls = {"n": 0}
    orig = R.write_relations

    def spy(*a, **k):
        calls["n"] += 1
        return orig(*a, **k)

    monkeypatch.setattr(R, "write_relations", spy)
    with arms("events", model="m1"):
        run_day(**KW)
    table_calls = calls["n"]
    calls["n"] = 0
    with arms("events", model="m1", people="memory", rows0=4):
        r = run_day(**KW)
    assert table_calls > 0 and calls["n"] == 0  # 負の対照: 腕 table は書く・腕 memory は書かない
    m = mr65(r)
    assert m["arms"]["people"] == "memory" and m["people"]["rows"] > 0
    man = r.run_manifest_fields()
    assert man["memory_summary"]["memory_store"]["n_rows"] > 4  # 幅が広がっても壊れない
    assert man["relations"]["counts"].get("acq_wake_requested_unavailable", 0) == 1


def test_people_arm_refuses_to_resume(tmp_path):
    kw = dict(KW, ticks=int(STEPS_PER_DAY), sim_days=2, checkpoint_every=60)
    with arms("events", model="m1", people="memory"):
        a = run_day(state_out=tmp_path / "state", stop_at_tick=int(STEPS_PER_DAY), **kw)
        with pytest.raises(RuntimeError, match="再開に対応しない"):
            run_day(resume_from=tmp_path / "state" / a.resume["state_files"][-1]["file"], **kw)


@pytest.mark.slow
@pytest.mark.requires_data("world_v2:w17_schedule.parquet")
def test_world_5000_one_day_uncapped_grows_and_reads_people():
    from shibuya import cli

    with arms("events", model="m1", people="memory", rows0=8):
        r = cli.run(n_agents=5000, seed=1, world_dir=str(WORLD), vocab_version="v3", memory="on", relations="on",
                    store_memory="on")
    man = r.run_manifest_fields()
    ms = man["memory_summary"]["memory_store"]
    assert ms["n_rows"] > 8 and ms["mr65"]["people"]["rows"] > 0
    assert man["relations"]["edges_live_total"] > 0 and man["relations"]["counts"]["init_edges"] > 0
    # 〔検収 M2・M4〕器の幅は上限の中・店の行の表に書いた(体の表の sm_* は書かない)・壊れない
    cap = ms["mr65"]["capacity"]
    assert cap["width"] <= cap["width_max"] and cap["episode_per_agent_max"] <= cap["caps"]["episode"]
    shops = ms["mr65"]["shops"]
    assert shops["rows"] > 0 and shops["width"] <= shops["cap"]
    assert man["store_memory_summary"]["rows_used_total"] == shops["rows"]


# ---------------------------------------------------------------- 〔検収 M2〕種類ごとの上限と A で消す
def _capped(n: int, rows: int, **caps: int) -> MemoryStore:
    import shibuya.engine.memory_store as MS

    prev = MS.row_caps()
    MS.set_row_caps(**caps)
    try:
        return _store(n=n, rows=rows)
    finally:
        MS.set_row_caps(**prev)


def _ep(ms: MemoryStore, a: int, obj: int, t_s: int) -> int:
    return int(ms.remember(a, LegacyEvent(t_s * S, 1, -1, obj, 0, 1), 1, "legacy")[0])


def _rows_of(ms: MemoryStore, a: int) -> list[tuple[int, int, int]]:
    g = np.arange(a * ms.n_rows, (a + 1) * ms.n_rows)
    on = ms._ms_origin[g] >= 0
    return [(int(k), int(p), int(o)) for k, p, o in zip(ms._lg_kind[g][on], ms._lg_partner[g][on], ms._lg_object[g][on])]


def test_row_caps_bound_the_width_and_evict_the_lowest_a_row():
    ms = _capped(2, 1, episode=3, person=2)
    assert ms.max_width == 5 and dict(ms.caps)["shop"] == 256
    for j in range(3):
        _ep(ms, 0, 100 + j, 60 * (j + 1))
    assert ms.n_rows == 4  # 1 → 2 → 4(倍に)
    _ep(ms, 0, 100, 600)  # 100 は 2 回=強い・101 と 102 は 1 回(101 が古い=A が一番低い)
    now = 700
    g = np.arange(0, ms.n_rows)
    on = ms._ms_origin[g] >= 0
    A = ms.m1.strength(g[on], 0, now * S, ms._ms_n[g[on]], ms._ms_first_ns[g[on]], ms._lg_kind[g[on]],
                       ms._ms_imp[g[on]])
    victim = int(ms._lg_object[g[on]][int(np.argmin(A))])
    assert victim == 101
    _ep(ms, 0, 200, now)  # 出来事の上限 3 に届いている=A の一番低い行(101)を消して入れる・幅は広げない
    objs = sorted(o for k, _p, o in _rows_of(ms, 0) if k != P)
    assert objs == [100, 102, 200] and ms.n_rows == 4
    assert ms.m1._m1_stats["evicted_by_a"] == 1 and ms.store_counts["evicted_by_a:episode"] == 1
    # 人の上限 2(出来事の行は触らない)。幅は上限の和 5 まで(4 → min(8, 5))
    _touch(ms, 0, 7, now + 60)
    _touch(ms, 0, 8, now + 120)
    assert ms.n_rows == 5
    _touch(ms, 0, 9, now + 180)  # 人の上限に届いている=一番古い 1 回だけの人(7)を消す
    persons = sorted(p for k, p, _o in _rows_of(ms, 0) if k == P)
    assert persons == [8, 9] and ms.n_rows == 5
    assert sorted(o for k, _p, o in _rows_of(ms, 0) if k != P) == [100, 102, 200]
    assert ms.store_counts["evicted_by_a:person"] == 1 and ms.store_counts["evicted_by_a"] == 2
    assert ms.m1._m1_stats["grown"] == 3 and ms.store_counts["rows_resized"] == 3  # 1→2→4→5
    # 「忘れた=見覚えも無い」で消す規則は前のまま(上の test_recall_and_recognition_and_forgetting)=ここでは消えていない
    assert ms.store_counts.get("forgotten", 0) == 0


def test_cap_eviction_ties_go_to_the_lower_row():
    ms = _capped(1, 2, episode=2, person=1)
    r1 = _ep(ms, 0, 1, 60)
    r2 = _ep(ms, 0, 2, 60)  # 同じ時刻・同じ回数=A も最後の時刻も同じ
    assert (r1, r2) == (0, 1)
    got = _ep(ms, 0, 3, 120)
    assert got == 0 and sorted(o for _k, _p, o in _rows_of(ms, 0)) == [2, 3]  # 同点は行の番号の小さい方


def test_seed_people_over_the_person_cap_is_refused():
    ms = _capped(2, 2, episode=4, person=2)
    with pytest.raises(ValueError, match="人の行の上限"):
        ms.seed_people([0, 0, 0], [1, 2, 3], [1, 1, 1], [1, 1, 1], [-60 * S] * 3, [-60 * S] * 3)


def test_rows0_over_the_width_cap_is_refused():
    import shibuya.engine.memory_store as MS

    prev = (MS.row_caps(), MS.rows0())
    MS.set_row_caps(episode=2, person=1)
    MS.set_rows0(8)
    try:
        ms = MemoryStore(2, 4, step_seconds=60, minutes_per_step=1.0)
        with pytest.raises(ValueError, match="上限"):
            ms.enable_arms(m1=M1.M1State(2, 8, tau=-3.0, seed=1), uncapped=True)
    finally:
        MS.set_row_caps(**prev[0])
        MS.set_rows0(prev[1])


# ---------------------------------------------------------------- 〔検収 M4〕店の評価の行も同じ作り
def _shop_store(width: int = 2, cap: int = 4):
    from shibuya.engine.memory_shops import ShopTable, UncappedStoreMemory

    tab = ShopTable(2, width, cap=cap)
    return tab, UncappedStoreMemory(2, table=tab, minutes_per_tick=1.0)


def _visit(st, tick: int, poi: int, agent: int = 0) -> int:
    # agents=None: 腕 memory の店の記憶は体の表(agents.registry.sm_*)を読まない・書かない(読めば落ちる)
    return int(st.write(None, tick, np.asarray([agent]), np.asarray([poi]), np.asarray([1]), np.asarray([1]))[0])


def test_shop_table_grows_to_the_cap_then_overwrites_the_lowest_a():
    tab, st = _shop_store(2, 4)
    assert (_visit(st, 10, 5), _visit(st, 20, 6)) == (0, 1)
    assert _visit(st, 30, 7) == 2 and tab.width == 4 and tab._shop_stats["grown"] == 1  # 満杯=幅を倍に
    _visit(st, 40, 5)  # 同じ店=重ねる(n=2)
    assert _visit(st, 50, 8) == 3
    A = st.activation(None, np.asarray([0]), 60)[0]
    assert int(tab.columns().poi[0][int(np.argmin(A))]) == 6  # 一番古い 1 回だけの店
    assert _visit(st, 60, 9) == 1  # 上限 4=A の一番低い行(店 6)を上書き・幅は広げない
    assert sorted(tab.columns().poi[0].tolist()) == [5, 7, 8, 9] and tab.width == 4
    assert tab._shop_stats["evicted_by_a"] == 1 and st.stats["evictions_by_a"] == 1 and st.stats.get("evictions", 0) == 0
    rows = st.rows(None, 0, 60, tau=-99.0)
    assert sorted(rows.poi.tolist()) == [5, 7, 8, 9] and int(rows.n[rows.poi == 5][0]) == 2
    assert (tab.columns().poi[1] == -1).all()
    with pytest.raises(ValueError):
        st.columns(None).poi[0, 0] = 1  # 読み口は読み取り専用
    with pytest.raises(AttributeError):
        tab._poi = np.zeros((2, 4), dtype=np.int32)
    with pytest.raises(AttributeError):
        del tab._n


def test_shop_table_ties_and_bounds():
    from shibuya.engine.memory_shops import ShopTable

    with pytest.raises(ValueError):
        ShopTable(2, 8, cap=4)
    tab, st = _shop_store(1, 2)
    _visit(st, 10, 1)
    assert _visit(st, 10, 2) == 1  # 1 → 2 に広げた(上限 2)
    assert _visit(st, 20, 3) == 0  # 同じ A・同じ最後の時刻=行の番号の小さい方
    with pytest.raises(RuntimeError, match="上限"):
        tab.grow()


def test_people_arm_run_keeps_shops_in_the_store_table():
    from shibuya.agents.state import STORE_MEMORY_EMPTY

    box = {}
    import shibuya.engine.memory as MEM
    from shibuya.engine.memory_shops import UncappedStoreMemory

    orig = MEM.MemoryLayer.enable_store
    orig_eps = UncappedStoreMemory.on_episodes

    def spy(self, *a, **k):
        got = orig(self, *a, **k)
        box["layer"] = self
        return got

    def spy_eps(self, agents, *a, **k):
        box["agents"] = agents
        return orig_eps(self, agents, *a, **k)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(MEM.MemoryLayer, "enable_store", spy)
        mp.setattr(UncappedStoreMemory, "on_episodes", spy_eps)
        with arms("events", model="m1", people="memory"):
            r = run_day(**KW)
        with arms("events", model="m1", people="memory", rows0=2, caps={"episode": 6, "person": 3, "shop": 4}):
            r2 = run_day(**dict(KW, store_memory_n=2))
    man = r.run_manifest_fields()
    shops = mr65(r)["shops"]
    assert shops["rows"] > 0 and man["store_memory_summary"]["rows_used_total"] == shops["rows"]
    assert mr65(r)["capacity"]["evicted_by_a"] == 0  # 1 日・80 体では上限に届かない
    # 小さな上限でも壊れない(幅を倍に・上限で上書き)・幅は上限の中
    m2 = mr65(r2)
    assert m2["shops"]["width"] == 4 and m2["shops"]["counts"]["grown"] >= 1 and m2["shops"]["per_agent_max"] <= 4
    assert m2["capacity"]["width"] <= m2["capacity"]["width_max"] == 9 and m2["capacity"]["evicted_by_a"] > 0
    assert m2["m1"]["counts"]["evicted_by_a"] == m2["capacity"]["evicted_by_a"]
    # 体の表の sm_* は書かない(この腕では空のまま)
    layer = box["layer"]
    assert layer.store._tab is layer.memory_store.shops
    assert (box["agents"].registry.sm_poi == STORE_MEMORY_EMPTY).all()
