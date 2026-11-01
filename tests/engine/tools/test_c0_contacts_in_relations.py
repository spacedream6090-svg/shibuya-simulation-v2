"""第 1 期 1-7 道具の台帳 C0(CT5): 個人の連絡先は関係の記憶に手段ごとの印(家族と職場は初めから)。

見るもの:
- 印の値: 初めの辺(世帯=通話・メッセージ・メール/職場=それに職場の連絡/学校ほか=0)・新しい相手は 0・押し出された欄は
  消える・同じ相手は残る・再開の作り直し。C0 では印=辺の種別の写像(状態台帳の行 CT5=導出)。
- 既存の ``rel_*`` の値は不変(印を書く口を止めたランと値まで同じ)・印は誰も読まない(乱しても final が同じ)。
- 書く口は ``RelationLayer._write_contacts`` の 1 つ(AST・負の対照)・系の宣言(memory=``CT5:rel_layer._contact_flags``)と段 B。
- 状態台帳の行 CT5(軸 1 diag=読み手は持ち主の数えの口 ``contact_tally`` だけ・軸 2 derivable・hash_skip)と、写しの番号が
  ``engine.relations`` と同じ。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import AgentState, ResultCode
from shibuya.core import write_permit as WP
from shibuya.engine import memory as M
from shibuya.engine import relations as RL
from shibuya.engine import state_ledger as SL
from shibuya.engine.run import run_day
from shibuya.engine.systems import conductor as CD
from shibuya.engine.systems import overrides as OV
from shibuya.engine.systems import probe as PR
from shibuya.engine.systems.table import SPECS
from shibuya.engine.tools import contacts as CT
from tests.engine.tools import contacts_writers as CW

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src" / "shibuya"
REL_PATH = (SRC / "engine" / "relations.py").as_posix()
OK = int(ResultCode.OK)
FAM, WORK = CT.ALL_PERSONAL, CT.ALL_PERSONAL | CT.WORK
KW = dict(n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0, sleep_suppression=False, vocab_version="v3",
          memory="on", relations="on", rel_copresent="on", store_memory="on", checkpoint_every=60)
#: 段 B の測り(全部の刻み)は短いラン(120 刻みで新しい相手の欄が消える刻みが 4 回=記録 c0/README.md §8)
KW_PROBE = {**KW, "ticks": 120}
world = pytest.mark.requires_data("world_v2", "world_v2:w16_population.parquet", "world_v2:w17_schedule.parquet")
WORLD_KW = dict(n_agents=2_000, seed=1, world_dir="data/world/v2", ticks=300, vocab_version="v3", memory="on",
                relations="on", checkpoint_every=150)


# ================================================================= 写しと台帳の行
def test_copies_of_the_relation_kinds():
    assert CT.KIND_HOUSEHOLD == RL.REL_KINDS["household"] and CT.KIND_WORK == RL.REL_KINDS["work"]
    assert dict(CT.KIND_NAMES) == dict(RL.REL_KIND_NAMES)
    assert CT.MEANS == ("通話", "メッセージ", "メール", "職場の連絡")
    assert [CT.MEANS_BITS[m] for m in CT.MEANS] == [1, 2, 4, 8]
    assert dict(CT.INITIAL_FLAGS_BY_KIND) == {1: FAM, 2: WORK}


def test_state_ledger_row_and_declaration():
    r = SL.row("CT5")
    assert (r.behavior, r.restore, r.items, r.hash_skip) == (
        SL.DIAG, SL.DERIVABLE, ("rel_layer._contact_flags",), ("rel_layer._contact_flags",))
    assert ("CT5", "rel_layer._contact_flags") not in SL.full_items()  # どちらのハッシュにも状態のファイルにも入らない
    writers = [s for s, sp in SPECS.items() if any(p.startswith("CT5:") for p in sp.writes.paths)]
    assert writers == ["memory"]


def test_flags_from_kinds():
    k = np.array([[1, 2, 3, 0], [5, 4, 2, 1]], dtype=np.uint8)
    p = np.array([[7, 8, 9, -1], [3, 4, -1, 6]])
    assert CT.flags_from_kinds(k).tolist() == [[FAM, WORK, 0, 0], [0, 0, WORK, FAM]]
    assert CT.flags_from_kinds(k, p).tolist() == [[FAM, WORK, 0, 0], [0, 0, 0, FAM]]  # 空の辺は 0
    with pytest.raises(ValueError):
        CT.flags_from_kinds(k, p[:, :2])
    t = CT.tally(CT.flags_from_kinds(k, p), k, p)
    assert t["edges_with_contact"] == 3 and t["edges_live"] == 6
    assert t["by_means"] == {"通話": 3, "メッセージ": 3, "メール": 3, "職場の連絡": 1}
    assert t["by_kind"]["household"] == 2 and t["by_kind"]["work"] == 1 and t["by_kind"]["school"] == 0


# ================================================================= 単体: 初めの辺・新しい相手・押し出し・再開
def _fill(rel, flags) -> None:  # noqa: ANN001
    """試験だけ: 書く口 ``_write_contacts`` を通して全部の欄に ``flags`` を書く(口の外からは書けない=検収 L1)。"""
    rows, cols = np.indices(rel.contact_flags.shape)
    rel._write_contacts(rows.reshape(-1), cols.reshape(-1), flags)


def test_runtime_guard_stops_writes_outside_the_writer():
    """検収 L1: 公開の欄は読み取り専用の view・付け替えと消去は止まる・書く口だけが書ける(負の対照)。"""
    a = _table()
    rel = _layer(a).relations
    with pytest.raises(ValueError):
        rel.contact_flags[0, 0] = 9                      # 口の外の書き
    with pytest.raises(ValueError):
        rel.contact_flags.fill(1)
    with pytest.raises(AttributeError):
        rel.contact_flags = np.zeros((6, 4), np.uint8)  # 付け替え(property に setter が無い)
    with pytest.raises(AttributeError):
        rel._contact_flags = np.zeros((6, 4), np.uint8)  # 中身の付け替え
    with pytest.raises(AttributeError):
        del rel._contact_flags
    with pytest.raises(AttributeError):
        del rel.contact_flags
    assert not rel.contact_flags.any()
    rel._write_contacts(np.array([1]), np.array([2]), CT.CALL)   # 書く口は書ける
    assert int(rel.contact_flags[1, 2]) == CT.CALL and int(np.count_nonzero(rel.contact_flags)) == 1
    v = rel.contact_flags
    assert not v.flags.writeable and np.shares_memory(v, rel._contact_flags)
    rel.stats["x"] = 1                                  # ほかの属性は今までどおり書ける
    rel._hits_tick = 5
    assert rel._hits_tick == 5


def _table(n: int = 6, k: int = 4) -> AgentState:
    a = AgentState(n, memory_columns=True, memory_n=32, relation_columns=True, rel_k=k)
    with a.writable():
        a.cell[:] = 3
    return a


def _layer(a: AgentState) -> M.MemoryLayer:
    lay = M.MemoryLayer(a.n, a.memory_n, minutes_per_tick=1.0)
    lay.enable_relations(a.rel_k, tau=-1.1)
    return lay


def _ep(lay, a, tick, agent, partner):  # noqa: ANN001
    return lay.record(a, tick, np.array([agent]), np.array([M.EVENT_KINDS["talk"]]), np.array([partner]),
                      np.array([-1]), np.array([OK]), np.array([3]))


def _init(u, v, kind, n=None, first=None):  # noqa: ANN001
    u, v, kind = (np.asarray(x, dtype=np.int64) for x in (u, v, kind))
    m = u.size
    return RL.InitialEdges(u=u, v=v, kind=kind, n=np.asarray(n if n is not None else [1] * m, dtype=np.int64),
                           first=np.asarray(first if first is not None else [0] * m, dtype=np.int64),
                           last=np.zeros(m, dtype=np.int64), minutes=np.zeros(m, dtype=np.int64), audit={})


def test_initial_edges_get_flags_for_family_and_work_only():
    a = _table()
    rel = _layer(a).relations
    assert rel.contact_flags.shape == (6, 4) and rel.contact_flags.dtype == np.uint8 and not rel.contact_flags.any()
    rel.seed_initial(a, _init([0, 0, 0, 1, 2], [1, 2, 3, 0, 4], [1, 2, 3, 1, 2]))
    f = rel.contact_flags
    assert f[0].tolist() == [FAM, WORK, 0, 0] and f[1].tolist() == [FAM, 0, 0, 0] and f[2].tolist() == [WORK, 0, 0, 0]
    r = a.registry
    assert np.array_equal(f, CT.flags_from_kinds(r.rel_kind, r.rel_partner))


def test_new_partner_has_no_flag_and_the_same_partner_keeps_it():
    a = _table()
    lay = _layer(a)
    rel = lay.relations
    rel.seed_initial(a, _init([0], [1], [1], n=[50], first=[-1000]))
    _ep(lay, a, 10, 0, 1)                         # 同じ相手=統合(n+1)・印は残る
    _ep(lay, a, 10, 0, 5)                         # 新しい相手=空の欄・知人(種別 5)・印 0
    r = a.registry
    j1 = int(np.flatnonzero(r.rel_partner[0] == 1)[0])
    j5 = int(np.flatnonzero(r.rel_partner[0] == 5)[0])
    assert (int(r.rel_kind[0, j1]), int(rel.contact_flags[0, j1])) == (1, FAM)
    assert (int(r.rel_kind[0, j5]), int(rel.contact_flags[0, j5])) == (5, 0)
    assert np.array_equal(rel.contact_flags, CT.flags_from_kinds(r.rel_kind, r.rel_partner))


def test_evicted_family_edge_loses_its_flag():
    a = _table(n=6, k=2)
    lay = _layer(a)
    rel = lay.relations
    rel.seed_initial(a, _init([0, 0], [1, 2], [1, 2]))  # n=1・first=0 の弱い初めの辺
    assert rel.contact_flags[0].tolist() == [FAM, WORK]
    _ep(lay, a, 500, 0, 3)                         # 満杯 → A の最小の辺を押し出す(新しい相手の A が上)
    r = a.registry
    assert rel.stats["evictions"] == 1 and 3 in r.rel_partner[0].tolist()
    j3 = int(np.flatnonzero(r.rel_partner[0] == 3)[0])
    assert rel.contact_flags[0, j3] == 0 and int(r.rel_kind[0, j3]) == 5
    assert np.array_equal(rel.contact_flags, CT.flags_from_kinds(r.rel_kind, r.rel_partner))


def test_rebuild_contacts_equals_the_map_of_kinds():
    a = _table()
    rel = _layer(a).relations
    rel.seed_initial(a, _init([0, 0, 1], [1, 2, 0], [1, 2, 1]))
    want = rel.contact_flags.copy()
    _fill(rel, 0)                                  # 再開の直後(初めの辺を作らない)と同じ空の印
    rel.rebuild_contacts(a)
    assert np.array_equal(rel.contact_flags, want)


def test_writing_contacts_does_not_change_the_existing_rel_columns(monkeypatch):
    """初めの辺・新しい相手・押し出しの全部で、印を書く口を止めた層と ``rel_*`` が値まで同じ。"""
    def scenario():  # noqa: ANN202
        a = _table(n=6, k=2)
        lay = _layer(a)
        lay.relations.seed_initial(a, _init([0, 0, 1], [1, 2, 0], [1, 2, 1]))
        _ep(lay, a, 5, 0, 1)
        _ep(lay, a, 500, 0, 3)
        _ep(lay, a, 501, 1, 4)
        r = a.registry
        return {c: np.array(getattr(r, c), copy=True) for c in ("rel_partner", "rel_kind", "rel_sign", "rel_first",
                                                                 "rel_last", "rel_n")}

    base = scenario()
    monkeypatch.setattr(RL.RelationLayer, "_write_contacts", lambda self, a, slot, flags: None)
    off = scenario()
    assert all(np.array_equal(base[c], off[c]) and base[c].dtype == off[c].dtype for c in base)


# ================================================================= ラン: 印は誰も読まない・rel_* は不変・段 B
def _capture(monkeypatch):  # noqa: ANN001
    made: list = []
    orig = RL.RelationLayer.__init__

    def init(self, *a, **kw):  # noqa: ANN001
        orig(self, *a, **kw)
        made.append(self)

    monkeypatch.setattr(RL.RelationLayer, "__init__", init)
    return made


def _rel_cols(res) -> dict:  # noqa: ANN001
    r = res.agents.registry
    return {c: np.array(getattr(r, c), copy=True) for c in ("rel_partner", "rel_kind", "rel_sign", "rel_first",
                                                             "rel_last", "rel_n")}


def test_flags_are_not_read_by_the_run(monkeypatch):
    """印を書く口を止めても、印を乱しても final と呼数と rel_* が同じ(合成の世界・記憶+関係+同席+店)。"""
    base = run_day(**KW)
    with monkeypatch.context() as m:
        m.setattr(RL.RelationLayer, "_write_contacts", lambda self, a, slot, flags: None)
        off = run_day(**KW)
    with monkeypatch.context() as m:
        orig = RL.RelationLayer.__init__

        def noisy(self, *a, **kw):  # noqa: ANN001
            orig(self, *a, **kw)
            _fill(self, np.random.default_rng(7).integers(0, 16, self.contact_flags.size))  # 書く口を通す(L1)

        m.setattr(RL.RelationLayer, "__init__", noisy)
        noise = run_day(**KW)
    for r in (off, noise):
        assert r.final_hash == base.final_hash and r.llm_calls == base.llm_calls
        assert all(np.array_equal(_rel_cols(r)[c], _rel_cols(base)[c]) for c in _rel_cols(base))


def _prefill(monkeypatch):  # noqa: ANN001
    """新しい相手の欄を消す書きが見えるように、印を全部 1 で始める(試験だけ)。"""
    orig = RL.RelationLayer.__init__

    def init(self, *a, **kw):  # noqa: ANN001
        orig(self, *a, **kw)
        _fill(self, CT.CALL)  # 書く口を通す(L1)

    monkeypatch.setattr(RL.RelationLayer, "__init__", init)


def test_memory_declares_the_contact_writes_in_stage_b(monkeypatch):
    prev = WP.enabled()
    WP.set_enabled(True)
    _prefill(monkeypatch)
    ticks = frozenset(range(KW_PROBE["ticks"]))  # 全部の刻み(新しい相手の欄が消える刻みを逃さない)
    try:
        pr = PR.Probe(check=CD.declared_check(SPECS), ticks=ticks)
        PR.ACTIVE = pr
        try:
            run_day(**KW_PROBE)
        finally:
            PR.ACTIVE = None
        hit = [(t, s) for t, s, _d, keys in pr.entries if any(k.startswith("CT5:") for k in keys)]
        assert hit and {s for _t, s in hit} == {"memory"}, hit[:5]
        assert not pr.violations, pr.violations[:5]
        # 負の対照: memory の宣言から外すと段 B が memory に出す
        pr2 = PR.Probe(check=None, ticks=ticks)
        PR.ACTIVE = pr2
        try:
            with OV.drop_path("memory", "CT5:rel_layer._contact_flags"):
                pr2.check = CD.declared_check(SPECS)
                run_day(**KW_PROBE)
        finally:
            PR.ACTIVE = None
        bad = [(t, s, k) for t, s, k in pr2.violations if k.startswith("CT5:")]
        assert bad and {s for _t, s, _k in bad} == {"memory"}, pr2.violations[:5]
    finally:
        WP.set_enabled(prev)


@world
def test_world_run_family_and_work_flags_and_rel_columns_unchanged(monkeypatch):
    from shibuya import cli

    made = _capture(monkeypatch)
    res = cli.run(**WORLD_KW)
    rel = made[-1]
    r = res.agents.registry
    assert np.array_equal(rel.contact_flags, CT.flags_from_kinds(r.rel_kind, r.rel_partner))  # C0 の不変
    t = res.run_manifest_fields()["tools"]["contact_flags"]
    assert t == {**CT.tally(rel.contact_flags, r.rel_kind, r.rel_partner), "means": list(CT.MEANS)}
    assert t["by_kind"]["work"] > 0 and t["edges_with_contact"] == t["by_kind"]["household"] + t["by_kind"]["work"]
    assert t["by_kind"]["school"] == t["by_kind"]["acquaintance"] == 0
    with monkeypatch.context() as m:
        m.setattr(RL.RelationLayer, "_write_contacts", lambda self, a, slot, flags: None)
        off = cli.run(**WORLD_KW)
    assert off.final_hash == res.final_hash and off.llm_calls == res.llm_calls
    assert all(np.array_equal(_rel_cols(off)[c], _rel_cols(res)[c]) for c in _rel_cols(res))


@world
def test_resume_rebuilds_the_same_flags(monkeypatch, tmp_path):
    from shibuya import cli

    made = _capture(monkeypatch)
    straight = cli.run(**WORLD_KW)
    want = made[-1].contact_flags.copy()
    a = cli.run(state_out=tmp_path / "state", stop_at_tick=150, **WORLD_KW)
    files = a.resume["state_files"]
    b = cli.run(resume_from=tmp_path / "state" / files[-1]["file"], **WORLD_KW)
    assert b.final_hash == straight.final_hash
    assert np.array_equal(made[-1].contact_flags, want) and int(np.count_nonzero(want)) > 0


# ================================================================= 書く口は 1 つ(AST・負の対照)
def test_only_the_writer_writes_the_flags():
    rel_writes, bad = CW.scan_tree(SRC)
    assert bad == [], bad
    by = {}
    for w in rel_writes:
        by.setdefault((w.kind, w.name), set()).add(w.func)
    assert by[("content", "_contact_flags")] == {"RelationLayer._write_contacts"}
    assert by[("replace", "_contact_flags")] == {"RelationLayer.__init__"}
    assert by[("call", "_write_contacts")] == {"RelationLayer._reset_slots", "RelationLayer.rebuild_contacts",
                                               "RelationLayer.seed_initial"}
    assert by[("replace", "?")] == {"RelationLayer.__setattr__", "RelationLayer.__delattr__"}  # 実行時の守りの中だけ
    assert ("content", "?") not in by and ("content", "contact_flags") not in by


NEG = '''
import numpy as np
from numpy import copyto
class X:
    def a(self):
        self.contact_flags[0] = 1
    def b(self):
        self.contact_flags[0, 1] += 2
    def c(self):
        self.contact_flags.fill(0)
    def d(self):
        np.copyto(self.contact_flags, 0)
    def e(self):
        np.bitwise_or.at(self.contact_flags, ([0], [0]), 1)
    def f(self):
        np.add(self.contact_flags, 1, out=self.contact_flags)
    def g(self):
        c = self.contact_flags[3]
        c[0] = 1
    def h(self):
        c = getattr(self, "contact_flags")
        c.put(0, 1)
    def i(self):
        c = np.asarray(self.contact_flags).reshape(-1)
        c[0] = 1
    def j(self):
        for row in self.contact_flags:
            row[0] = 1
    def q(self, y):
        self.contact_flags[0], y = 1, 2
    def r(self):
        for i, row in enumerate(self.contact_flags):
            row[0] = 1
    def s(self, ys):
        for row, y in zip(self.contact_flags, ys):
            row[0] = 1
    def t(self):
        d[0] = 1
        d = c
        c = self._contact_flags
    def u(self, nm):
        getattr(self, nm)[0] = 1
    def v(self):
        copyto(self._contact_flags, 0)
    def w(self, a, b):
        np.add(a, b, out=(self.contact_flags,))
    def k(self):
        self.contact_flags = np.zeros(3)
    def l(self):
        setattr(self, "contact_flags", None)
    def m(self):
        object.__setattr__(self, "_contact_flags", None)
    def n(self):
        vars(self)["contact_flags"] = None
    def o(self, nm):
        setattr(self, nm, None)
    def p(self):
        self._write_contacts(0, 0, 1)
    def ok(self):
        x = self.contact_flags.copy()
        x[0] = 1
'''


def test_negative_controls_are_found():
    """23 形(中身の書き 17・差し替え 4・名の分からない差し替え 1・書く口の呼び出し 1)と、写しへの書き(数えない)。"""
    by = {}
    for w in CW.scan_source(NEG):
        by.setdefault(w.func, set()).add((w.kind, w.name))
    for q in "abcdefghijrs":
        assert by.get(f"X.{q}") == {("content", "contact_flags")}, (q, by.get(f"X.{q}"))
    assert by.get("X.q") == {("content", "contact_flags")}                 # タプルの代入(検収 M1 の 1)
    assert by.get("X.t") == {("content", "_contact_flags")}                # 別名の鎖(書いた順と逆)
    assert by.get("X.u") == {("content", "?")}                             # getattr の名が式
    assert by.get("X.v") == {("content", "_contact_flags")}                # 名だけで呼ぶ copyto
    assert by.get("X.w") == {("content", "contact_flags")}                 # out=(…,)
    assert by.get("X.k") == {("replace", "contact_flags")} and by.get("X.l") == {("replace", "contact_flags")}
    assert by.get("X.m") == {("replace", "_contact_flags")} and by.get("X.n") == {("replace", "contact_flags")}
    assert by.get("X.o") == {("replace", "?")} and by.get("X.p") == {("call", "_write_contacts")}
    assert "X.ok" not in by
    # 許す所の表で見ると: 関係の置き場の外では名の分かる書きが全部違反(名の分からない書きは置き場の中だけを見る)・
    # 置き場の中なら名の分からない書きも違反(X.* は許す所でない)
    ws = CW.scan_source(NEG)
    assert len(CW.violations("engine/other.py", NEG)) == sum(1 for w in ws if w.name != "?") == 21
    assert len(CW.violations(CW.REL, NEG)) == len(ws) == 23
