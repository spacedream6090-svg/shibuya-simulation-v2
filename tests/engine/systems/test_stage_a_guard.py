"""1-0 段 A: 系ごとの書きの許可(``core.write_permit``)・配列単位の ``_require_thawed``・静的な検査 D④⑤⑥⑦・閉包の道具。

草案 ``docs/design/v2-run-day-decomposition-draft.md`` §2-6(A ①②・D④〜⑦)・§3-1 の T1(ufunc.at の列の負の対照の
resolve の単位の分)。ランの単位の正と負の対照(系の許可から列を外すと落ちる)は進行役ができてから
``test_guard_runs.py`` で回す。
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import AgentState
from shibuya.core import write_permit as WP
from shibuya.engine import resolve as R
from shibuya.engine import state_ledger_ast as A
from shibuya.engine.systems import allow as AL
from shibuya.world.state import World

SRC = Path("src/shibuya")


@pytest.fixture(autouse=True)
def _guard_on():
    prev = WP.enabled()
    WP.set_enabled(True)
    yield
    WP.set_enabled(prev)


def _frozen_pair(n: int = 4):
    a = AgentState(n)
    w = World.synthetic(n_cells=4, seed=1)
    a.freeze()
    w.freeze()
    return a, w


# ================================================================= A ①: 解除口は許可の列だけを解く
def test_writable_thaws_only_permitted_columns():
    a, w = _frozen_pair()
    with WP.scope(frozenset({"agents.cell", "pois.stock"})):
        with a.writable(), w.writable():
            a.registry.cell[0] = 3
            w.pois.stock[0] = 0
            with pytest.raises(ValueError):
                a.registry.money[0] = 1
            with pytest.raises(ValueError):
                w.pois.revenue[0] = 1
            with pytest.raises(ValueError):
                w.cells.density[0] = 1
    # 窓を出たら全部が読み取り専用に戻る
    assert not any(arr.flags.writeable for arr in a.registry.arrays.values())
    assert a.frozen and w.frozen


def test_no_permit_means_everything_thaws_as_before():
    a, w = _frozen_pair()
    assert WP.current() is None
    with a.writable(), w.writable():
        a.registry.money[0] = 7
        w.pois.revenue[0] = 7
    assert int(a.registry.money[0]) == 7


def test_switch_off_restores_the_old_full_thaw():
    a, _w = _frozen_pair()
    WP.set_enabled(False)
    with WP.scope(frozenset({"agents.cell"})):
        assert WP.current() is None
        with a.writable():
            a.registry.money[0] = 5
    assert int(a.registry.money[0]) == 5


def test_scope_nests_and_restores():
    with WP.scope(frozenset({"agents.cell"})):
        with WP.scope(frozenset({"agents.money"})):
            assert WP.allows("agents", "money") and not WP.allows("agents", "cell")
        assert WP.allows("agents", "cell") and not WP.allows("agents", "money")
    assert WP.current() is None


def test_perception_state_thaws_only_permitted_columns():
    from shibuya.perception.state import PerceptionState

    ps = PerceptionState(4)
    ps.freeze()
    names = list(ps.registry.arrays)
    keep, other = names[0], names[1]
    with WP.scope(frozenset({f"perception.{keep}"})):
        with ps.writable():
            ps.registry.arrays[keep][0] = 1
            with pytest.raises(ValueError):
                ps.registry.arrays[other][0] = 1


# ================================================================= A ②: ufunc.at は配列ごとに旗を見る(T1 の resolve の単位)
def test_require_thawed_checks_each_array():
    a, _w = _frozen_pair()
    with WP.scope(frozenset({"agents.cell"})):
        with a.writable():
            R._require_thawed(a, a.registry.cell)  # 許可の列は通る
            with pytest.raises(ValueError):
                R._require_thawed(a, a.registry.refractory_until)  # 許可の外の列は止まる


def test_set_refractory_ufunc_at_is_blocked_outside_the_permit():
    """負の対照(T1・refractory_until): ``np.maximum.at`` は旗を見ないので配列単位の検査が止める。"""
    a, _w = _frozen_pair()
    before = a.registry.refractory_until.copy()
    with WP.scope(frozenset({"agents.cell"})):
        with pytest.raises(ValueError):
            R.set_refractory(a, np.array([0]), np.array([1]), 10)
    assert np.array_equal(a.registry.refractory_until, before)  # 書く前に止まった
    with WP.scope(frozenset({"agents.refractory_until"})):
        R.set_refractory(a, np.array([0]), np.array([1]), 10)  # 正の対照
    assert int(a.registry.refractory_until[0, 1]) > 10


def test_numpy_ufunc_at_still_ignores_the_flag():
    """穴の実在(この振る舞いが変われば配列単位の検査は要らなくなる)。"""
    x = np.zeros(3, dtype=np.int32)
    x.flags.writeable = False
    np.add.at(x, [0], 1)
    assert x[0] == 1


# ================================================================= D ⑦: ufunc.at の直前の検査が書く配列を引数に持つ
def _at_sites(tree: ast.AST):
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "at"
                and isinstance(node.func.value, ast.Attribute)
                and ast.unparse(node.func.value).startswith("np.") and node.args):
            yield node


def test_every_state_ufunc_at_in_resolve_checks_the_written_array():
    path = SRC / "engine" / "resolve.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    checked = 0
    for fn in funcs:
        req = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "_require_thawed"]
        for at in _at_sites(fn):
            first = ast.unparse(at.args[0])
            prev = sorted((r for r in req if r.lineno <= at.lineno and at.lineno - r.lineno <= 4),
                          key=lambda r: r.lineno)
            assert prev, f"resolve.py:{at.lineno} np.*.at({first}) の直前に _require_thawed が無い"
            args = {ast.unparse(x) for x in prev[-1].args}
            assert first in args, f"resolve.py:{at.lineno}: _require_thawed{sorted(args)} が書く配列 {first} を持たない"
            checked += 1
    assert checked >= 5, checked  # 陽性対照(refractory_until・stock・revenue ×2・holdings)


# ================================================================= D ⑤: 旗の直書きは決まった場所だけ
#: 旗を立て得る直書き(値が定数 False でない ``flags.writeable =``・``setflags(write=...)``)を許す (ファイル, 関数)。
FLAG_WRITERS = {
    ("agents/state.py", "thaw"), ("agents/state.py", "freeze"),
    ("world/state.py", "thaw"), ("world/state.py", "freeze"),
    ("perception/state.py", "_set_writeable"),
    ("economy/goods.py", "*"), ("economy/ledger.py", "*"),
    ("engine/resolve.py", "_restore_array_into"),
    # 〔第 3 期 3-5 検収 L7〕体の層の予約の列(BodySchedule)が自分の配列(SoA ではない)を書く口の中だけ書けるようにする
    ("engine/body/schedule.py", "_open_and_call"),
}


def _func_of(node: ast.AST, par: dict) -> str:
    p = par.get(node)
    while p is not None and not isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
        p = par.get(p)
    return p.name if p is not None else ""


def test_direct_flag_writes_live_only_in_known_places():
    offenders = []
    for fp in A.source_files(SRC):
        rel = fp.relative_to(SRC).as_posix()
        tree = ast.parse(fp.read_text(encoding="utf-8"))
        par = A._parents(tree)
        for node in ast.walk(tree):
            site = None
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Attribute) and t.attr == "writeable" and ast.unparse(t).endswith("flags.writeable"):
                        if not (isinstance(node.value, ast.Constant) and node.value.value is False):
                            site = node
            elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "setflags"):
                if any(k.arg == "write" and not (isinstance(k.value, ast.Constant) and k.value.value is False)
                       for k in node.keywords):
                    site = node
            if site is None:
                continue
            fn = _func_of(site, par)
            if (rel, fn) not in FLAG_WRITERS and (rel, "*") not in FLAG_WRITERS:
                offenders.append(f"{rel}:{site.lineno} [{fn}] {ast.unparse(site)[:80]}")
    assert not offenders, offenders


# ================================================================= D ⑥: SoA の配列・ビュー・別名を層の属性に持たせない
_SOA_TAILS = {"registry", "agents", "cells", "pois", "pstate"}
_EXEMPT_D6 = {"agents/state.py", "world/state.py", "perception/state.py", "engine/resolve.py", "core/soa.py"}
#: 許す属性(場所・代入の左辺・理由)。どれも凍結の後に作る読むだけの**写し**(int32 → int64 の dtype の変換=別の配列)。
D6_ALLOW = {
    ("engine/intent.py", "self._poi_cell"): "POI のセル(静的な列)を int64 の写しで持つ(dtype が違う=写し・凍結の後)",
    ("engine/store_choice.py", "self.poi_cell"): "同上",
    ("engine/store_choice.py", "self.price"): "POI の値段(静的な列)の int64 の写し",
}


def _soa_array_expr(v: ast.AST, names: set[str]) -> bool:
    while isinstance(v, ast.Subscript) or (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute)
                                           and v.func.attr in ("asarray", "asanyarray", "view", "reshape")):
        v = v.value if isinstance(v, ast.Subscript) else (v.args[0] if v.func.attr in ("asarray", "asanyarray") and v.args
                                                         else v.func.value)
    if isinstance(v, ast.Attribute) and v.attr in names:
        tail = v.value.attr if isinstance(v.value, ast.Attribute) else (v.value.id if isinstance(v.value, ast.Name) else "")
        return tail in _SOA_TAILS
    if (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and v.func.attr == "field"
            and v.args and isinstance(v.args[0], ast.Constant)):
        return True
    return False


def test_no_layer_holds_a_soa_array_or_view_as_an_attribute():
    decl = A.declared_columns(SRC)
    names = {c for v in decl.values() for c in v}
    offenders = []
    used: set = set()
    for fp in A.source_files(SRC):
        rel = fp.relative_to(SRC).as_posix()
        if rel in _EXEMPT_D6:
            continue
        for node in ast.walk(ast.parse(fp.read_text(encoding="utf-8"))):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
                continue
            tgs = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Attribute) for t in tgs) and _soa_array_expr(node.value, names):
                if any((rel, ast.unparse(t)) in D6_ALLOW for t in tgs):
                    used.add(next((rel, ast.unparse(t)) for t in tgs if (rel, ast.unparse(t)) in D6_ALLOW))
                    continue
                offenders.append(f"{rel}:{node.lineno} {ast.unparse(node)[:90]}")
    assert not offenders, offenders
    assert used == set(D6_ALLOW), set(D6_ALLOW) - used  # 古い許可を残さない


def test_d6_detector_catches_a_planted_alias(tmp_path):
    """負の対照(T2・D ⑥): 層の属性に SoA の列のビューを持たせる行をわざと書くと見つかる。"""
    decl = A.declared_columns(SRC)
    names = {c for v in decl.values() for c in v}
    planted = ast.parse("class L:\n    def bind(self, agents):\n        self.cur = agents.registry.cell[:]\n")
    hits = [n for n in ast.walk(planted) if isinstance(n, ast.Assign) and _soa_array_expr(n.value, names)]
    assert len(hits) == 1


# ================================================================= D ④: 系は解除口を呼ばない(test_two_phase の延長)
def test_systems_package_never_thaws():
    for fp in (SRC / "engine" / "systems").rglob("*.py"):
        for node in ast.walk(ast.parse(fp.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in ("writable", "thaw", "_set_writeable", "setflags"), (fp, node.lineno)


# ================================================================= 閉包の道具(宣言の正)
def test_closure_follows_tables_and_local_aliases():
    ix = AL.index()
    hits = {(f, n) for f, _ln, n in ix.alias_hits}
    assert ("set_refractory", "cur") in hits and ("consume", "holdings") in hits
    # ``apply`` の閉包は ``_APPLY`` の表を通して _apply_talk(talk_partner)まで届く
    assert "agents.talk_partner" in AL.writes_for_ops({"apply"})
    assert "agents.refractory_until" in AL.writes_for_ops({"set_refractory"})
    assert "agents.holdings" in AL.writes_for_ops({"consume"})


def test_alias_table_covers_ledger_money_writes():
    # 〔第 1 期 1-9〕台帳越しの agents.money(旧 _apply_cash の別名の 4 行)は基本操作 economy.ops.transfer の中に閉じた
    # =手の表から消え、帳簿の口(TRANSFER_PORTS_HOUSEHOLD)の呼び出しから AST で引く。閉包は前と同じ。
    callers = {f for f, _ln, _port in AL.index().transfer_callers}
    for fn in ("_complete_buy", "_complete_eat", "_board_riders", "initialize"):
        assert fn not in AL.ALIAS_WRITES, fn
        assert fn in callers, fn
        assert "agents.money" in AL.writes_for_ops({fn})
    assert not any("_apply_cash" in why for _w, why in AL.ALIAS_WRITES.values())
    assert set(AL.ALIAS_WRITES["apply_detection"][0]) == {
        "agents.fatigue_stage", "agents.hunger_stage", "agents.thermal_stage"}


def test_closure_is_an_upper_bound_of_resolve_ops():
    ops = {"apply"}
    assert ops <= AL.closure(ops)
    assert AL.writes_for_ops(set()) == frozenset()


def test_d5_detector_catches_a_planted_flag_write():
    """負の対照(T2・D ⑤): 決まった場所の外で旗を立てる行をわざと書くと見つかる。"""
    planted = ast.parse("def f(a):\n    a.flags.writeable = True\n    a.setflags(write=True)\n    a.flags.writeable = False\n")
    par = A._parents(planted)
    hits = []
    for node in ast.walk(planted):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Attribute) and t.attr == "writeable" for t in node.targets):
            if not (isinstance(node.value, ast.Constant) and node.value.value is False):
                hits.append(_func_of(node, par))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "setflags":
            hits.append(_func_of(node, par))
    assert hits == ["f", "f"] or sorted(hits) == ["f", "f"]
    assert ("probe.py", "f") not in FLAG_WRITERS
