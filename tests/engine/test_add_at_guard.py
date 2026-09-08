"""書き込みガードの**穴**(``numpy`` の ``ufunc.at`` は ``writeable=False`` を見ない)を塞ぐ検査。

背景
    ``AgentState.freeze()`` / ``World.freeze()`` は全配列を ``flags.writeable=False`` にして
    「resolve 以外は書けない」を機械強制している(運用設計書 §2.2「atomic 演算による直接更新は
    禁止」)。ところが ``np.add.at`` / ``np.maximum.at``(``ufunc.at``)は buffer protocol を
    経由せずに書くため、**このフラグを無視して書けてしまう**。

対策は二段
    1. **静的**(本ファイル): ``world.``/``agents.`` 由来の配列に対する ``np.<ufunc>.at`` は
       ``src/shibuya/engine/resolve.py`` にしか書けない。
    2. **動的**: ``resolve._require_thawed`` が ``_frozen`` フラグ(``frozen`` プロパティ)を
       撃つ前に検査する。``economy`` の内部配列(``_shelf``/``_lines`` 等)は世界状態ではなく
       台帳の私物で、独自の検査を持つので**対象外**。
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import AgentState
from shibuya.engine import resolve as R
from shibuya.world.state import World

SRC = Path("src/shibuya")
#: ``ufunc.at`` の第1引数が「世界状態」だと判断する根(``self.`` 経由も見る)。
STATE_ROOTS = ("world", "agents", "self.world", "self.agents")
#: 台帳の私物(独自検査を持つ)と実行時に import されない工程は対象外。
OUT_OF_SCOPE = ("economy/", "build/")


def _dotted(node: ast.AST) -> str:
    """``world.pois.stock`` / ``r.holdings`` / ``x[i]`` の**根から**のドット表記を作る。"""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else ""
    if isinstance(node, ast.Subscript):
        return _dotted(node.value)
    if isinstance(node, ast.Call):
        return _dotted(node.func)
    return ""


def _state_rooted(expr: str) -> bool:
    return any(expr == r or expr.startswith(r + ".") for r in STATE_ROOTS)


def _registry_aliases(tree: ast.AST) -> set[str]:
    """``holdings = agents.registry.holdings`` のような**別名**を集める(第1引数の判定用)。"""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Name) and _state_rooted(_dotted(node.value)):
                names.add(tgt.id)
    return names


def _ufunc_at_targets(path: Path) -> list[str]:
    """``np.<ufunc>.at(<第1引数>, ...)`` の第1引数のうち**世界状態のもの**を返す。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    aliases = _registry_aliases(tree)
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        # np.<ufunc>.at → Attribute(attr="at", value=Attribute(value=Name("np")))
        if not (isinstance(fn, ast.Attribute) and fn.attr == "at"):
            continue
        inner = fn.value
        if not (isinstance(inner, ast.Attribute) and _dotted(inner).startswith("np.")):
            continue
        if not node.args:
            continue
        first = _dotted(node.args[0])
        if _state_rooted(first) or first in aliases:
            hits.append(f"{path.as_posix()}:{node.lineno}: np.{inner.attr}.at({first}, …)")
    return hits


def _scanned_files() -> list[Path]:
    return [
        p
        for p in SRC.rglob("*.py")
        if not any(seg in p.as_posix() for seg in OUT_OF_SCOPE)
    ]


# ================================================================= 静的
def test_ufunc_at_on_world_or_agent_arrays_lives_only_in_resolve():
    """``np.add.at``(等)で世界状態を書けるのは resolve.py だけ。"""
    offenders = {
        p.as_posix(): _ufunc_at_targets(p)
        for p in _scanned_files()
        if _ufunc_at_targets(p)
    }
    assert set(offenders) == {"src/shibuya/engine/resolve.py"}, offenders


def test_resolve_actually_uses_ufunc_at_on_state():
    """検査が空振り(=検出ロジックの故障)でないことの陽性対照。"""
    hits = _ufunc_at_targets(SRC / "engine" / "resolve.py")
    assert len(hits) >= 3, hits


def test_arbiter_diagnostic_counters_are_not_flagged():
    """診断カウンタ(局所配列)への ``np.add.at`` は世界状態ではない=対象外。"""
    assert _ufunc_at_targets(SRC / "engine" / "arbiter.py") == []


def test_every_ufunc_at_in_resolve_is_preceded_by_the_frozen_check():
    """resolve の中でも、状態への ``ufunc.at`` の**直前**に ``_require_thawed`` がある。"""
    text = (SRC / "engine" / "resolve.py").read_text(encoding="utf-8").splitlines()
    for hit in _ufunc_at_targets(SRC / "engine" / "resolve.py"):
        lineno = int(hit.split(":")[1])
        window = "\n".join(text[max(0, lineno - 4) : lineno])
        assert "_require_thawed" in window, hit


# ================================================================= 動的
def test_numpy_ufunc_at_really_ignores_the_writeable_flag():
    """**穴の実在**を記録する(この振る舞いが変わったら静的検査を緩めてよい)。"""
    a = np.zeros(4, dtype=np.int32)
    a.flags.writeable = False
    with pytest.raises(ValueError):
        a[0] = 1  # 通常の代入は止まる
    np.add.at(a, [0], 1)  # ufunc.at は**素通りする**
    assert a[0] == 1


def test_frozen_flag_is_recorded_by_freeze_and_checked_by_resolve():
    agents = AgentState(4)
    world = World.synthetic(n_cells=4, seed=1)
    assert agents.frozen is False and world.frozen is False
    agents.freeze()
    world.freeze()
    assert agents.frozen is True and world.frozen is True
    with pytest.raises(ValueError):
        R._require_thawed(agents)
    with pytest.raises(ValueError):
        R._require_thawed(world)
    with agents.writable(), world.writable():
        R._require_thawed(agents, world)  # 窓の中では通る


def test_set_refractory_is_blocked_when_someone_forgets_the_window(monkeypatch):
    """``set_refractory`` は ``np.maximum.at`` を撃つ前に ``frozen`` を見る。"""
    agents = AgentState(4)
    agents.freeze()
    # writable() を無力化して「窓を開け忘れた」状況を作る(穴の再現)
    monkeypatch.setattr(AgentState, "writable", lambda self: _noop_ctx())
    with pytest.raises(ValueError):
        R.set_refractory(agents, np.array([0]), np.array([5]), 10)


class _noop_ctx:
    def __enter__(self):
        return None

    def __exit__(self, *exc):
        return False
