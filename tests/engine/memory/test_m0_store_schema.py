"""第 1 期 1-6 記憶の器 M0: 器の形(口の約束 1-6 の口・受入の試験 ``test_m0_store_schema``)。

- 記憶の行の欄: 目印 ``event_id``(1-3 の ``EventId``)・強さ(System 1 の数=回数・重要度・最初の時刻)・注釈・出どころ・
  録画(``shown``)。体ごとの行の範囲(SoA の列)。仮の出来事の表(行と同じ番地・目印の seq は負)。
- 書く口は ``remember``・``mark_shown`` の 2 つ(作り直しの ``rebuild`` と録画の控えの ``take_shown``)。欄の付け替えは
  ``__setattr__`` が落とす。系の宣言(``writes.paths`` の ``M0``・``M0R``)の外からは書けない(実行時の検査)。
- ``MemoryView`` は言葉(はっきり/うろ覚え)と中身の粗さと中身の ID だけ(強さの数を持たない=MR-0)。
- 状態台帳: 行 M0(軸 1 no・軸 2 derivable・中身は全部 hash_skip)と M0R(diag・discardable)=どちらのハッシュにも状態の
  ファイルにも入らない。持ち主のクラスの属性は全部載る(AST と実行時)。
- 置き場: ``shibuya.engine.memory_store``(1 本のモジュール・親の判断)。``engine/memory.py`` は package にしない。
  層の契約は import-linter(本物の検査)が見る。ここでは置き場と、器の import の層を念のため AST でも確かめる。
"""

from __future__ import annotations

import ast
from collections import OrderedDict
from pathlib import Path

import numpy as np
import pytest

from shibuya.core import write_permit as WP
from shibuya.core.time_consts import NS_PER_STEP
from shibuya.engine import state_ledger as SL
from shibuya.engine import state_ledger_ast as SA
from shibuya.engine.memory import GIST_PER_AGENT, IMPORTANCE_MAX, MemoryLayer
from shibuya.engine import memory_store as MS
from shibuya.engine.systems import guard as G
from shibuya.engine.systems.table import SPECS

SRC = Path(__file__).resolve().parents[3] / "src" / "shibuya"


def _store(n: int = 3, rows: int = 4) -> MS.MemoryStore:
    return MS.MemoryStore(n, rows, step_seconds=60, minutes_per_step=1.0)


def _ev(step: int, kind: int, partner: int = -1, obj: int = 5, result: int = 0, cell: int = 7) -> MS.LegacyEvent:
    return MS.LegacyEvent(step * NS_PER_STEP, kind, partner, obj, result, cell)


# ================================================================= 置き場と層
def test_store_is_one_module_beside_the_memory_table():
    import shibuya.engine.memory as M

    assert Path(MS.__file__).resolve() == (SRC / "engine" / "memory_store.py").resolve()
    assert MS.__name__ == "shibuya.engine.memory_store"
    assert Path(M.__file__).name == "memory.py" and not hasattr(M, "__path__")  # 今の表のモジュールは package にしない
    assert not (SRC / "engine" / "memory").exists()


def test_store_imports_only_allowed_layers():
    """器は engine の層の契約(engine > perception|llm > world|agents > core)を守る(import-linter と同じ向き)。"""
    tree = ast.parse((SRC / "engine" / "memory_store.py").read_text(encoding="utf-8"))
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            mods.add(n.module)
        elif isinstance(n, ast.Import):
            mods |= {a.name for a in n.names}
    inner = {m for m in mods if m.startswith("shibuya")}
    assert inner and all(m.split(".")[1] in ("engine", "perception", "llm", "agents", "world", "core") for m in inner)
    assert not any(m.startswith(("shibuya.economy", "shibuya.census", "shibuya.build")) for m in inner)


# ================================================================= 欄
def test_row_columns_bytes_and_ranges():
    ms = _store(3, 4)
    assert MS.ROW_BYTES == 32 and MS.LEGACY_BYTES == 14
    assert ms.rows_of(0) == range(0, 4) and ms.rows_of(2) == range(8, 12)
    with pytest.raises(IndexError):
        ms.rows_of(3)
    for name, dt, fill in MS._ROW_COLS + MS._LEGACY_COLS:
        a = getattr(ms, name)
        assert a.dtype == np.dtype(dt) and a.shape == (12,) and (a == fill).all(), name
    assert not ms.has_rows(0) and ms.event_id(0, 0) is None
    assert MS.ORIGINS == (None, "legacy") and MS.CLARITY_WORDS == ("はっきり", "うろ覚え")
    # 〔第 2 期 2-3・親の判断 M3〕「要旨だけ」=目印の先が記録の保持窓の外に出た行
    assert MS.GRAIN_WORDS == ("そのまま", "要旨だけ") and MS.TAPE_COLUMN == "recalled_event_ids"


def test_view_has_words_and_content_but_no_strength_number():
    fields = set(MS.MemoryView._fields)
    assert {"clarity", "grain", "kind", "partner", "obj", "result", "cell", "annotation", "when_ns"} <= fields
    assert {"event_id", "origin", "row", "first_ns"} <= fields  # 録画の同定(描き方は使わない)
    assert not fields & {"n", "importance", "imp", "strength", "A", "score", "activation", "first_tick", "last_tick"}
    assert MS.clarity_of(-1.0, -1.0) == "はっきり" and MS.clarity_of(-1.01, -1.0) == "うろ覚え"


def test_setattr_guard_and_slots():
    ms = _store()
    with pytest.raises(AttributeError):
        ms._ms_n = np.zeros(12, dtype=np.uint16)  # 欄の付け替え
    with pytest.raises(AttributeError):
        ms.new_state = 1  # 宣言に無い欄(__slots__)
    with pytest.raises(AttributeError):
        ms.tau = 0.0
    with pytest.raises(AttributeError):
        ms.tape_on = True  # テープの印は口(attach_tape)の中だけ(検収 L4)
    with pytest.raises(AttributeError):
        ms._ms_last = MS.RecallReport(True, 0, 0, 0, 0, 0, 0, 0)  # 最後の想起の計数も口の中だけ
    ms.attach_tape()
    assert ms.tape_on is True


def test_delattr_is_closed():
    """検収 L1: 欄を消してから付け替える抜け道を閉じる(負の対照)。"""
    ms = _store()
    with pytest.raises(AttributeError, match="消せない"):
        del ms._ms_origin
    with pytest.raises(AttributeError):
        ms._ms_origin = np.zeros(12, dtype=np.int8)
    assert ms._ms_origin.size == 12


def test_closed_tables_cannot_be_changed():
    """検収 L2: 閉じた表(器の列の表・テープの腕の列の表)は書き換えられない。"""
    from shibuya.engine import tape as TP

    with pytest.raises(TypeError):
        MS._COL_SPEC["_ms_new"] = (np.int8, 0)  # type: ignore[index]
    with pytest.raises(TypeError):
        TP.ARM_COLUMNS["new_column"] = (None, ())  # type: ignore[index]


# ================================================================= 書く口 1: remember(今の表と同じ規則)
def test_remember_new_merge_and_pointer_to_the_last_occurrence():
    ms = _store(2, 3)
    got = ms.remember(np.asarray([0, 1]), MS.LegacyEvent(np.full(2, 10 * NS_PER_STEP), [1, 7], [-1, 1], [5, 3],
                                                         [0, 0], [7, 2]), [1, 2], "legacy")
    assert got.tolist() == [0, 0]
    assert ms.event_id(0, 0) == (10 * NS_PER_STEP, -1) and ms.event_id(1, 0) == (10 * NS_PER_STEP, -1 - 3)
    assert ms.origin(0, 0) == "legacy" and ms._ms_n[0] == 1 and ms._ms_imp[0] == 2  # 新しい行=base+初回 1
    assert ms._ms_imp[3] == 3
    # 同じ鍵(種類・相手・対象・結果)=重ねる: 回数+1・重要度は base・最初の時刻はそのまま・目印は最後の回(セルも)
    got = ms.remember(0, _ev(20, 1, cell=9), 1, "legacy")
    assert got.tolist() == [0]
    assert ms._ms_n[0] == 2 and ms._ms_imp[0] == 1 and ms._ms_first_ns[0] == 10 * NS_PER_STEP
    assert ms.event_id(0, 0) == (20 * NS_PER_STEP, -1) and ms._lg_cell[0] == 9
    # 違う鍵=空の行
    assert ms.remember(0, _ev(21, 1, obj=6), 1, "legacy").tolist() == [1]
    assert ms.store_counts["merged"] == 1 and ms.store_counts["new_rows"] == 3


def test_remember_evicts_the_lowest_score_row_like_the_table():
    """満杯=score 最小の行(同点は番号の小さい方)を追い出す。今の ``MemoryLayer._write`` と行が同じ。"""
    from shibuya.agents.state import AgentState

    n_rows = 3
    agents = AgentState(1, memory_columns=True, memory_n=n_rows)
    layer = MemoryLayer(1, n_rows)
    layer.enable_memory_store(step_seconds=60)
    events = [(0, 1, 5, 0), (1, 2, 6, 0), (2, 7, -1, 0), (30, 1, 7, 2), (31, 1, 5, 0), (90, 9, -1, 0), (91, 10, 8, 0)]
    for step, kind, obj, res in events:
        layer.record(agents, step, np.asarray([0]), np.asarray([kind]), np.asarray([-1 if kind != 7 else 3]),
                     np.asarray([obj]), np.asarray([res]), np.asarray([4]))  # _write が行の食い違いを落とす
    assert layer.memory_store.store_counts["evictions"] == layer.stats["evictions"] >= 1
    assert np.array_equal(agents.registry.mem_n[0].astype(np.int64), layer.memory_store._ms_n.astype(np.int64))


def test_remember_rejects_what_m0_cannot_hold():
    ms = _store()
    with pytest.raises(ValueError, match="legacy"):
        ms.remember(0, (0, 0), 1, None)  # 記録の出来事への目印は体の出来事を記録に載せる段で
    with pytest.raises(TypeError):
        ms.remember(0, (0, 0), 1, "legacy")
    with pytest.raises(ValueError, match="1 体 1 件"):
        ms.remember(np.asarray([0, 0]), MS.LegacyEvent(np.zeros(2), 1, -1, 5, 0, 7), 1, "legacy")
    with pytest.raises(ValueError, match="同じ刻み"):
        ms.remember(np.asarray([0, 1]), MS.LegacyEvent(np.asarray([0, NS_PER_STEP]), 1, -1, 5, 0, 7), 1, "legacy")
    with pytest.raises(IndexError):
        ms.remember(9, _ev(0, 1), 1, "legacy")


def test_annotations_follow_the_gist_rules():
    """注釈=今の要旨と同じ規則(体あたり 16 件・古い順に落とす・追い出した行の注釈は落とす・同じ行に置き直すと最後へ)。"""
    ms = _store(1, 40)
    for j in range(GIST_PER_AGENT + 2):
        ms.remember(0, _ev(j, 7, partner=j, obj=-1), 2, "legacy", annotation=[f"話した{j}"])
    assert len(ms._ms_note) == GIST_PER_AGENT and ms.annotation(0, 0) is None and ms.annotation(0, 2) == "話した2"
    ms.remember(0, _ev(50, 7, partner=2, obj=-1), 2, "legacy", annotation=["また話した"])
    assert list(ms._ms_note_order[0])[-1] == 2 and ms.annotation(0, 2) == "また話した"
    assert ms.store_counts["notes_dropped"] == 2


def test_strength_is_capped_like_the_fixed_table():
    ms = _store(1, 2)
    ms.remember(0, _ev(0, 1, result=3), 3, "legacy")  # 失敗 3+初回 1=4(上限)
    assert ms._ms_imp[0] == IMPORTANCE_MAX
    ms.remember(0, _ev(1, 1, result=3), 3, "legacy")  # 重ねた行は base(初回の +1 を外す)
    assert ms._ms_imp[0] == 3 and ms._ms_n[0] == 2


def test_value_drift_from_the_table_is_caught_at_write(monkeypatch):
    """検収 M1: 行の番号が同じでも、器の値(ここでは重要度)が表とずれたら書いた所で落ちる(負の対照)。"""
    from shibuya.agents.state import AgentState

    def write_some(layer, agents):
        for step, kind, obj in ((0, 1, 5), (1, 2, 6), (2, 1, 5)):
            layer.record(agents, step, np.asarray([0]), np.asarray([kind]), np.asarray([-1]), np.asarray([obj]),
                         np.asarray([0]), np.asarray([4]))

    agents = AgentState(1, memory_columns=True, memory_n=4)
    layer = MemoryLayer(1, 4)
    layer.enable_memory_store(step_seconds=60)
    write_some(layer, agents)  # 正: ずれなければ落ちない
    orig = MS.MemoryStore.remember

    def drift(self, agent, event_id, strength, origin, **kw):  # noqa: ANN001, ANN202
        got = orig(self, agent, event_id, strength, origin, **kw)
        g = np.atleast_1d(np.asarray(agent, dtype=np.int64)) * self.n_rows + got
        self._ms_imp[g] = self._ms_imp[g] - 1  # 重要度を 1 減らす(行の番号は同じ)
        return got

    monkeypatch.setattr(MS.MemoryStore, "remember", drift)
    agents2 = AgentState(1, memory_columns=True, memory_n=4)
    layer2 = MemoryLayer(1, 4)
    layer2.enable_memory_store(step_seconds=60)
    with pytest.raises(RuntimeError, match="重要度"):
        write_some(layer2, agents2)


# ================================================================= 書く口 2: mark_shown・控え
def test_mark_shown_records_the_time_and_returns_the_pointer_text():
    ms = _store(2, 3)
    ms.remember(0, _ev(5, 1), 1, "legacy")
    ids = ms.mark_shown(0, (0, 2, 3 + 1), 9 * NS_PER_STEP, call=(0, 9 * NS_PER_STEP, 2))
    assert ids == (f"{5 * NS_PER_STEP}:-1", "", "")  # 空の行・器の外の行(店の行=n_rows 以上)は空文字
    assert ms.shown_ns(0, 0) == 9 * NS_PER_STEP and ms.shown_ns(0, 1) == -1
    assert ms.take_shown((0, 9 * NS_PER_STEP, 2)) == ()  # テープの無いランは控えない
    ms.attach_tape()
    ms.mark_shown(0, (0,), 9 * NS_PER_STEP, call=(0, 9 * NS_PER_STEP, 2))
    ms.mark_shown(0, (), 9 * NS_PER_STEP, call=(0, 9 * NS_PER_STEP, 2))
    assert ms.take_shown((0, 9 * NS_PER_STEP, 2)) == (f"{5 * NS_PER_STEP}:-1",)  # 古い順
    assert ms.take_shown((0, 9 * NS_PER_STEP, 2)) == ()
    assert ms.summary()["tape_pending"] == 0
    # 新しく覚えた行(追い出し・空の行)はまだ見せていない
    ms.remember(0, _ev(10, 2), 1, "legacy")
    assert ms.shown_ns(0, 1) == -1


# ================================================================= 実行時の検査(writes.paths)
@pytest.fixture
def guard_on():
    prev = WP.enabled()
    WP.set_enabled(True)
    yield
    WP.set_enabled(prev)


def test_writes_outside_the_declaration_fail(guard_on):
    ms = _store()
    with G.system_scope("phase_a", frozenset(), frozenset(), None, frozenset({"O4:intent_layer.*"})):
        with pytest.raises(PermissionError, match="M0"):
            ms.remember(0, _ev(0, 1), 1, "legacy")
        with pytest.raises(PermissionError, match="M0R"):
            ms.mark_shown(0, (0,), 0)
        with pytest.raises(PermissionError, match="M0R"):
            ms.recall(0, 0, 2)
    with G.system_scope("x", frozenset(), frozenset(), None, frozenset({"M0:mem_layer.memory_store.*"})):
        with pytest.raises(PermissionError, match="M0R"):
            ms.remember(0, _ev(0, 1), 1, "legacy")  # 覚えると計数と新しい行の録画の印(M0R)も書く
        with pytest.raises(PermissionError):
            ms.mark_shown(0, (0,), 0)  # 行 M0 だけの宣言では録画(M0R)は書けない
    with G.system_scope("y", frozenset(), frozenset(), None, frozenset({"M0R:mem_layer.memory_store.*"})):
        with pytest.raises(PermissionError, match="M0:"):
            ms.remember(0, _ev(0, 1), 1, "legacy")
        ms.mark_shown(0, (0,), 0)
    with G.system_scope("decide", frozenset(), frozenset(), None, frozenset({"M0*:mem_layer.memory_store.*"})):
        ms.remember(0, _ev(0, 1), 1, "legacy")
        ms.mark_shown(0, (0,), 0)
        ms.recall(0, 0, 2)


def test_systems_declare_the_store_paths():
    decl = {s: SPECS[s].writes.paths for s in ("memory", "decide", "llm_receive", "drain")}
    assert "M0*:mem_layer.memory_store.*" in decl["memory"]
    assert "M0*:mem_layer.memory_store.*" in decl["decide"] and "M0*:mem_layer.memory_store.*" in decl["llm_receive"]
    assert "M0R:mem_layer.memory_store.*" in decl["drain"]
    others = [s for s in SPECS if s not in decl and any("memory_store" in p for p in SPECS[s].writes.paths)]
    assert others == []


# ================================================================= 状態台帳
def test_ledger_rows_are_out_of_both_hashes_and_the_state_file():
    m0, m0r = SL.row("M0"), SL.row("M0R")
    assert (m0.behavior, m0.restore, set(m0.hash_skip) == set(m0.items)) == (SL.NO, SL.DERIVABLE, True)
    assert (m0r.behavior, m0r.restore) == (SL.DIAG, SL.DISCARDABLE)
    paths = [p for _k, p in SL.full_items()] + [p for _k, p in SL.behavior_items()]
    assert not [p for p in paths if "memory_store" in p]
    assert SL.OWNER_CLASSES["mem_layer.memory_store"] == ("engine/memory_store.py", "MemoryStore")
    slots = set(MS.MemoryStore.__slots__)
    # 〔第 2 期 2-3〕記録の目印の seq は腕の行 M0L(軸 1 no・軸 2 required=腕のランだけ full-hash と状態のファイル)
    m0l = SL.row("M0L")
    assert (m0l.behavior, m0l.restore, m0l.arm, m0l.arm_owner) == (SL.NO, SL.REQUIRED, "memory-store",
                                                                   "mem_layer.memory_store")
    declared = {it.rsplit(".", 1)[1] for r in (m0, m0r, m0l) for it in r.items}
    excluded = set(SL.excluded_attrs()["mem_layer.memory_store"])
    # 〔第 2 期 2-3〕腕の行の腕の名 LEDGER_ARM はクラスの定数(slots の外)=除外の一覧に載る
    assert slots | {"LEDGER_ARM"} == declared | excluded and not declared & excluded
    assert "bridge.tape._arm_values" in SL.row("O87").items
    assert "arm_columns" in SL.excluded_attrs()["bridge.tape"]


def test_runtime_owner_coverage_with_the_store():
    layer = MemoryLayer(2, 3)
    layer.enable_memory_store(step_seconds=60)
    owners = {k.split(".")[0]: None for k in SL.OWNER_CLASSES}
    owners["mem_layer"] = layer
    assert SA.runtime_uncovered(owners) == {}
    uncovered, problems = SA.coverage(SRC)
    assert uncovered == {} and problems == []


# ================================================================= 作り直し(再開)
def test_rebuild_from_the_table_gives_the_same_rows():
    from shibuya.agents.state import AgentState

    from tests.engine.memory._m0 import table_vs_store

    agents = AgentState(2, memory_columns=True, memory_n=4)
    layer = MemoryLayer(2, 4)
    layer.enable_memory_store(step_seconds=60)
    for step, a, kind, obj in ((0, 0, 1, 5), (1, 1, 7, -1), (2, 0, 1, 5), (3, 0, 2, 6), (4, 1, 10, -3)):
        layer.record(agents, step, np.asarray([a]), np.asarray([kind]), np.asarray([1 if kind == 7 else -1]),
                     np.asarray([obj]), np.asarray([0]), np.asarray([2]))
    layer.gist[(1, 0)] = "要旨"
    layer._gist_order.setdefault(1, OrderedDict())[0] = None
    before = {n: getattr(layer.memory_store, n).copy() for n, _t, _f in MS._LEGACY_COLS + MS._ROW_COLS[:-1]}
    layer.memory_store.mark_shown(0, (0,), 5 * NS_PER_STEP)
    counts = dict(layer.memory_store.store_counts)
    assert layer.rebuild_memory_store(agents) == 4
    for n, v in before.items():
        assert np.array_equal(getattr(layer.memory_store, n), v), n
    assert layer.memory_store.annotation(1, 0) == "要旨"
    # 検収 L3: 作り直すのは行 M0 だけ(録画・計数=行 M0R は触らない)・作り直しの数は記憶の層の計数へ
    assert layer.memory_store.shown_ns(0, 0) == 5 * NS_PER_STEP and layer.memory_store.store_counts == counts
    assert layer.stats["memory_store_rebuilt_rows"] == 4
    assert table_vs_store(agents, layer) == []


def test_rebuild_only_outside_systems(guard_on):
    """検収 L3: 作り直しは再開の組み立て(系の外)だけ。系の中(M0* を宣言した系でも)では落ちる。"""
    ms = _store()
    z = np.zeros((3, 4), dtype=np.int64)
    with G.system_scope("decide", frozenset(), frozenset(), None, frozenset({"M0*:mem_layer.memory_store.*"})):
        with pytest.raises(RuntimeError, match="系の外"):
            ms.rebuild(z, z, z, z, z, z, z, z, z, {}, {})
    assert ms.rebuild(z, z, z, z, z, z, z, z, z, {}, {}) == 0


# ================================================================= 腕(切替口)
def test_arm_switch():
    assert MS.ARMS == ("mem", "events") and MS.arm() in MS.ARMS
    prev = MS.arm()
    try:
        MS.set_arm("events")
        assert MS.arm() == "events"
        with pytest.raises(ValueError):
            MS.set_arm("vector")
    finally:
        MS.set_arm(prev)
