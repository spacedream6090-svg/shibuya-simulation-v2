"""第 1 期 1-9(独立検収 M2): 台帳の配列を書ける窓を開けるのは基本操作 ``economy.ops.transfer`` だけ。

前は公開の ``Ledger.unlocked()`` があり、``with led.unlocked(): led.balance(line, s)[i] = x`` で transfer の外から残高を
書けた(書き手の AST の検査は関数をまたぐ別名を追えず、実行時の守りは窓が開いていて効かない)。直し:

- 窓を内部の名 ``Ledger._unlocked`` にした(公開の ``unlocked`` は無い・``MoneyLedger`` の口からも外した)。
- src の全部で、窓の名(``_unlocked``・旧 ``unlocked``)への参照(呼び出し・別名・属性の鎖・``getattr`` などの名前の文字列)と、
  ``self`` 以外を受け手にした ``_open`` の参照は、``economy/ops.py`` の ``transfer`` の中だけ(この試験の AST)。
- 名前の文字列でお金の列を書く形(``setattr``・``object.__setattr__``・``vars(X)[...]``・``X.__dict__[...]``)は書き手の AST
  (``money_writers.py``)が数える。

負の対照: 窓+``balance`` の書き(新旧の名)・別名・属性の鎖・``getattr`` の文字列・``_open`` を外から・``setattr``・
``object.__setattr__``・``vars``・``__dict__``。試験(tests/)は窓を開けてよい(検算が残高の直の書きを捕まえる試験のため)。
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import numpy as np
import pytest

from shibuya.economy.accounts import BalanceLine, Sector
from shibuya.economy.ledger import Ledger
from shibuya.engine import ledger_api as API

from tests.economy.cp2 import money_writers as MW

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[2] / "src" / "shibuya"
DECLARED = {(w["path"], w["func"]): set(w["attrs"])
            for w in json.loads((HERE / "money_writers_frozen.json").read_text(encoding="utf-8"))["writers"]}
WINDOW_NAMES = frozenset({"_unlocked", "unlocked"})
ALLOWED = {("economy/ops.py", "transfer")}


class _WindowScan(ast.NodeVisitor):
    """窓の名への参照(一番外の関数に帰属)。"""

    def __init__(self, path: str) -> None:
        self.path = path
        self.stack: list[str] = []
        self.out: list[tuple[str, str, int, str]] = []

    def _owner(self) -> str:
        return self.stack[0] if self.stack else "<module>"

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if self.stack:
            self.generic_visit(node)
            return
        for b in node.body:
            if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.stack.append(f"{node.name}.{b.name}")
                self.generic_visit(b)
                self.stack.pop()
            else:
                self.visit(b)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self.stack:
            self.generic_visit(node)
            return
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in WINDOW_NAMES:
            self.out.append((self.path, self._owner(), node.lineno, f".{node.attr}"))
        elif node.attr == "_open" and not (isinstance(node.value, ast.Name) and node.value.id == "self"):
            self.out.append((self.path, self._owner(), node.lineno, "._open(self 以外)"))
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str) and node.value in WINDOW_NAMES | {"_open"}:
            self.out.append((self.path, self._owner(), node.lineno, f"文字列 {node.value!r}"))


def window_refs(text: str, path: str) -> list[tuple[str, str, int, str]]:
    sc = _WindowScan(path)
    sc.visit(ast.parse(text))
    return sc.out


def _outside(refs):
    return [r for r in refs if (r[0], r[1]) not in ALLOWED]


# ================================================================= 本物の src
def test_only_the_primitive_opens_the_ledger_window():
    refs = []
    for rel, text in MW.iter_sources(SRC):
        refs += window_refs(text, rel)
    assert _outside(refs) == [], _outside(refs)
    # 正の対照: transfer は窓を開けている(道具が参照を見ている)
    assert [(p, f) for p, f, _ln, _form in refs] == [("economy/ops.py", "transfer")]


def test_the_public_window_is_gone():
    assert not hasattr(Ledger, "unlocked") and hasattr(Ledger, "_unlocked")
    assert "unlocked" not in {n for n in dir(API.MoneyLedger) if not n.startswith("__")}
    led = Ledger(2, 2)
    with pytest.raises(AttributeError):
        led.unlocked()  # type: ignore[attr-defined]
    # 窓の外では残高の配列は読み取り専用(実行時の守り)
    with pytest.raises(ValueError):
        led.balance(BalanceLine.CASH, Sector.STORE)[0] = 1


# ================================================================= 負の対照
def test_negative_window_and_balance_write():
    """負の対照 1: 窓を開けて ``balance`` の配列に書く(新旧の名・別名・属性の鎖・getattr の文字列・_open を外から)。"""
    forms = {
        "新しい名": "def f(led):\n    with led._unlocked():\n        led.balance(0, 1)[2] = 9\n",
        "旧い名": "def f(led):\n    with led.unlocked():\n        led.balance(0, 1)[2] = 9\n",
        "別名": "def f(led):\n    u = led._unlocked\n    with u():\n        led.balance(0, 1)[2] = 9\n",
        "属性の鎖": "def f(b):\n    with b.layers.ledger.money._unlocked():\n        pass\n",
        "getattr": "def f(led):\n    with getattr(led, '_unlocked')():\n        pass\n",
        "_open": "def f(led):\n    with led.money._open():\n        pass\n",
    }
    for name, code in forms.items():
        assert _outside(window_refs(code, "engine/resolve.py")), name
    # ops.py でも transfer の外なら落ちる
    assert _outside(window_refs("def helper(led):\n    with led._unlocked():\n        pass\n", "economy/ops.py"))
    # 自分の _open(self)は窓の参照ではない(会話の管理の _open など)
    assert window_refs("class C:\n    def g(self):\n        return self._open()\n", "engine/conversation.py") == []


def test_negative_setattr_and_named_writes():
    """負の対照 2: 名前の文字列でお金の列を書く形は書き手の AST が数える(凍結の表の外=落ちる)。"""
    code = ("def leak(led, a):\n"
            "    setattr(led, '_raw_pos', 0)\n"
            "    object.__setattr__(led, '_flow', None)\n"
            "    vars(led)['_lines'] = {}\n"
            "    a.__dict__['money'] = 0\n"
            "    setattr(led, 'not_money', 1)\n")
    bad = MW.violations(MW.scan_source(code, "engine/resolve.py"), DECLARED)
    assert [(w.attr, w.form) for w in bad] == [("_raw_pos", "setattr"), ("_flow", "setattr"),
                                              ("_lines", "vars/__dict__ の名前の書き"),
                                              ("money", "vars/__dict__ の名前の書き")], bad


def test_the_old_route_wrote_balances_and_the_new_one_cannot_be_reached_from_src():
    """記録: 窓を開ければ(試験が意図して開ける)残高は書ける=守りは「窓を開けるのは transfer だけ」の静的な検査。"""
    led = Ledger(2, 2)
    led.endow_stores(np.array([1_000, 0]), 0)
    with led._unlocked():
        led.balance(BalanceLine.CASH, Sector.STORE)[0] -= 1  # 試験だけが開けてよい
    assert int(led.balance(BalanceLine.CASH, Sector.STORE)[0]) == 999
