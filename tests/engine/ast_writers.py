"""書く口の AST の道具の共通の置き場(第 1 期 1-7 検収 M1)。試験の補助・src は読むだけ。

1-5 の ``tests/engine/rights/rights_writers.py`` の ``_LedgerScanner`` を、列の判定(``is_col``)・差し替えを数える名
(``replace_names``)・呼び手を数える口の名(``call_names``)を引数にして写した物(1-5 の道具はそのまま=取り込みの後に
この置き場へ寄せる候補)。数える形の広さは 1-5・1-9(``tests/economy/cp2/money_writers.py``)と同じ:

- 中身の書き(``content``): ``X.<列>[...] =``・``+=``(添字の鎖の根が列・的の ``Tuple``/``List``/``Starred`` を開く)・
  ``np.<ufunc>.at(X.<列>, ...)``・``X.<列>.fill(...)``(``put``・``sort``・``itemset``・``resize``・``setfield``・``partition``)・
  ``np.copyto/put/place/putmask/put_along_axis/fill_diagonal(X.<列>, ...)``(名だけで呼ぶ ``copyto(...)`` も)・キーワード
  ``out=X.<列>``(``out=(…,)`` のタプルも)。
- 局所の別名: ``c = X.<列>[...]``(添字・``.T``・``np.asarray``・``.view``・``.reshape``・``.ravel``・``enumerate``・``zip``・
  ``iter``・``reversed`` を通しても)・``c = getattr(X, "<列>")``・``for``/内包/``with`` で名に結ぶ。別名は 2 回集める(鎖)。
  その名への上の形の書きを列の書きとして数える。
- 差し替え(``replace``): ``X.<列> =``・``X.<名> =``(``replace_names``)・``setattr``/``object.__setattr__``/``delattr``/
  ``object.__delattr__``(名が定数ならその名・**名が式なら「?」**)・``vars(X)["<名>"] =``・``X.__dict__["<名>"] =``。
- ``getattr(X, <式>)``(名が式)は名の分からない列(「?」)として扱う(``getattr(x, nm)[i] = v`` も書きになる)。
- 呼び手(``call``): ``X.<口>(...)``(``call_names``)。

結果は ``Write``(関数の限定名・名・行・種類・形)の列。関数の限定名はモジュールの頂上の関数かクラスのメソッド
(``Class.method``・入れ子の関数は外の関数に帰属)・頂上の文は ``<module>``。

限界(1-5・1-9 と同じ): 関数をまたぐ別名(引数で渡した列への書き)と、名を変数で持って渡す外からの ``getattr`` は見えない。

逐次ループ宣言: なし(試験の道具)。
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Callable

__all__ = ["UNKNOWN", "Write", "WriterScanner", "scan_writes", "MUTATING_METHODS", "MUTATING_FUNCS"]

#: 中身を書くメソッド(1-5・1-9 と同じ)。
MUTATING_METHODS = frozenset({"fill", "put", "sort", "itemset", "resize", "setfield", "partition"})
#: 第 1 引数を書く numpy の関数(1-5・1-9 と同じ)。
MUTATING_FUNCS = frozenset({"copyto", "put", "place", "putmask", "put_along_axis", "fill_diagonal"})
#: 同じ中身を指す(写さない)属性・メソッド・関数(1-5・1-9 と同じ)。
VIEW_ATTRS = frozenset({"T", "flat", "real", "imag"})
VIEW_METHODS = frozenset({"view", "reshape", "ravel", "items", "values", "transpose", "swapaxes", "squeeze"})
VIEW_FUNCS = frozenset({"asarray", "asanyarray", "enumerate", "zip", "iter", "reversed", "atleast_1d"})
#: 名で属性を置く・消す関数。
SETTERS = frozenset({"setattr", "__setattr__", "delattr", "__delattr__"})
UNKNOWN = "?"


@dataclass(frozen=True)
class Write:
    func: str   # ``Class.method``・``関数``・``<module>``
    name: str   # 書いた列・欄・口の名(名が式なら ``?``)
    line: int
    kind: str   # ``content``(列の中身)・``replace``(属性の差し替え)・``call``(書く口を呼んだ)
    form: str


def _dict_key(t: ast.Subscript) -> str | None:
    """``vars(X)["名"]``・``X.__dict__["名"]`` への書きなら、その名(名が式なら ``?``)。"""
    v, key = t.value, t.slice
    hit = ((isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "vars")
           or (isinstance(v, ast.Attribute) and v.attr == "__dict__"))
    if not hit:
        return None
    if isinstance(key, ast.Constant) and isinstance(key.value, str):
        return key.value
    return UNKNOWN


class WriterScanner(ast.NodeVisitor):
    """列(``is_col`` が真の属性の名)の中身の書き・差し替え・書く口の呼び出しを集める。"""

    def __init__(self, is_col: Callable[[str], bool], *, replace_names: frozenset[str] = frozenset(),
                 call_names: frozenset[str] = frozenset()) -> None:
        self.is_col = is_col
        self.replace_names = frozenset(replace_names)
        self.call_names = frozenset(call_names)
        self.stack: list[str] = []
        self.out: list[Write] = []
        self.aliases: list[dict[str, str]] = [{}]

    def _owner(self) -> str:
        return self.stack[0] if self.stack else "<module>"

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if self.stack:
            self.generic_visit(node)
            return
        for b in node.body:
            if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._func(b, f"{node.name}.{b.name}")
            else:
                self.visit(b)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self.stack:
            self.generic_visit(node)
            return
        self._func(node, node.name)

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def _func(self, node: ast.AST, name: str) -> None:
        self.stack.append(name)
        self.aliases.append(self._collect_aliases(node))
        self.generic_visit(node)
        self.aliases.pop()
        self.stack.pop()

    # ---------------------------------------------------------------- 別名
    def _collect_aliases(self, fn: ast.AST) -> dict[str, str]:
        al: dict[str, str] = {}
        for _ in range(2):  # 2 回=別名の鎖(書いた順に依らない)
            for node in ast.walk(fn):
                if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                    a = self._root(node.value, al)
                    if a is None:
                        continue
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for t in targets:
                        if isinstance(t, ast.Name):
                            al[t.id] = a
                elif isinstance(node, (ast.For, ast.comprehension)):
                    a = self._root(node.iter, al)
                    if a is not None:
                        for nm in ast.walk(node.target):
                            if isinstance(nm, ast.Name):
                                al[nm.id] = a
                elif isinstance(node, ast.withitem) and node.optional_vars is not None:
                    a = self._root(node.context_expr, al)
                    if a is not None and isinstance(node.optional_vars, ast.Name):
                        al[node.optional_vars.id] = a
        return al

    def _root(self, e: ast.AST, al: dict[str, str] | None = None) -> str | None:
        """式が指す中身が列なら、その名(別名・添字・ビュー・``getattr`` を通す。名が式なら ``?``)。"""
        al = self.aliases[-1] if al is None else al
        while True:
            if isinstance(e, ast.Attribute):
                if self.is_col(e.attr):
                    return e.attr
                if e.attr in VIEW_ATTRS:
                    e = e.value
                    continue
                return None
            if isinstance(e, (ast.Subscript, ast.Starred)):
                e = e.value
                continue
            if isinstance(e, ast.Name):
                return al.get(e.id)
            if isinstance(e, ast.Call):
                f = e.func
                if isinstance(f, ast.Name) and f.id == "getattr" and len(e.args) >= 2:
                    a1 = e.args[1]
                    if isinstance(a1, ast.Constant) and isinstance(a1.value, str):
                        return a1.value if self.is_col(a1.value) else None
                    return UNKNOWN
                if isinstance(f, ast.Attribute) and f.attr in VIEW_METHODS:
                    e = f.value
                    continue
                fname = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
                if fname in VIEW_FUNCS:
                    for a in e.args:
                        r = self._root(a, al)
                        if r is not None:
                            return r
                return None
            return None

    # ---------------------------------------------------------------- 書き
    def _add(self, name: str | None, node: ast.AST, kind: str, form: str) -> None:
        if name is not None:
            self.out.append(Write(self._owner(), name, int(getattr(node, "lineno", 0)), kind, form))

    def _target(self, t: ast.AST, node: ast.AST, aug: bool) -> None:
        if isinstance(t, (ast.Tuple, ast.List)):
            for x in t.elts:
                self._target(x, node, aug)
        elif isinstance(t, ast.Starred):
            self._target(t.value, node, aug)
        elif isinstance(t, ast.Subscript):
            named = _dict_key(t)
            if named is not None:
                if named == UNKNOWN or self.is_col(named) or named in self.replace_names:
                    self._add(named, node, "replace", "vars/__dict__ の名前の書き")
                return
            self._add(self._root(t.value), node, "content", "添字への代入" + ("(+=)" if aug else ""))
        elif isinstance(t, ast.Attribute):
            if self.is_col(t.attr) or t.attr in self.replace_names:
                self._add(t.attr, node, "replace", "属性の差し替え" + ("(+=)" if aug else ""))
        elif isinstance(t, ast.Name) and aug:
            self._add(self.aliases[-1].get(t.id), node, "content", "別名への +=")

    def visit_Assign(self, node: ast.Assign) -> None:
        for t in node.targets:
            self._target(t, node, False)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self._target(node.target, node, False)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._target(node.target, node, True)
        self.generic_visit(node)

    def visit_Delete(self, node: ast.Delete) -> None:
        for t in node.targets:
            if isinstance(t, ast.Attribute) and (self.is_col(t.attr) or t.attr in self.replace_names):
                self._add(t.attr, node, "replace", "del")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        f = node.func
        fname = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        if fname in SETTERS and len(node.args) >= 2:
            a1 = node.args[1]
            if isinstance(a1, ast.Constant) and isinstance(a1.value, str):
                if self.is_col(a1.value) or a1.value in self.replace_names:
                    self._add(a1.value, node, "replace", fname)
            else:
                self._add(UNKNOWN, node, "replace", f"{fname}(名が式)")
        if isinstance(f, ast.Attribute):
            if f.attr == "at" and node.args:
                self._add(self._root(node.args[0]), node, "content", "ufunc.at")
            elif f.attr in MUTATING_METHODS:
                self._add(self._root(f.value), node, "content", f".{f.attr}()")
            if f.attr in MUTATING_FUNCS and node.args:
                self._add(self._root(node.args[0]), node, "content", f"np.{f.attr}")
            if f.attr in self.call_names:
                self._add(f.attr, node, "call", f.attr)
        elif isinstance(f, ast.Name):
            if f.id in MUTATING_FUNCS and node.args:
                self._add(self._root(node.args[0]), node, "content", f.id)
            if f.id in self.call_names:
                self._add(f.id, node, "call", f.id)
        for kw in node.keywords:
            if kw.arg == "out":
                vals = kw.value.elts if isinstance(kw.value, (ast.Tuple, ast.List)) else [kw.value]
                for v in vals:
                    self._add(self._root(v), node, "content", "out=")
        self.generic_visit(node)


def scan_writes(source: str, is_col: Callable[[str], bool], *, replace_names: frozenset[str] = frozenset(),
                call_names: frozenset[str] = frozenset()) -> list[Write]:
    """``source`` の中の書き(列の中身・差し替え・書く口の呼び出し)。"""
    sc = WriterScanner(is_col, replace_names=replace_names, call_names=call_names)
    sc.visit(ast.parse(source))
    return sc.out
