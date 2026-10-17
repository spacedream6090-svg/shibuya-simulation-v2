"""第 1 期 1-9(CP2 の段階 1): お金の列(C 金)の書き手を AST で集める道具(試験の補助・src は読むだけ)。

お金の列は ``economy.ops.MONEY_PATHS``(属性の名 ``MONEY_ATTRS`` と頭 ``_raw_``)。数える書きの形:

- 中身の書き: ``X.<名>[...] =``・``X.<名>[...] +=``(添字の鎖の根が名)・``np.<ufunc>.at(X.<名>, ...)``・
  ``X.<名>.fill(...)``(``put``・``sort``・``itemset``・``resize``・``setfield`` も)・``np.copyto/put/place/putmask(X.<名>, ...)``・
  キーワード ``out=X.<名>``。
- 台帳の中の名(``_lines``・``_flow``・``_last_change_day``・``_raw_*``)は属性の差し替え ``X.<名> =``・``X.<名> +=`` も数える
  (``money``・``revenue`` は台帳の束の欄 ``LedgerBundle.money`` と同じ名なので差し替えは数えない)。
- 局所の別名: ``c = X.<名>[...]``(添字・``.T``・``np.asarray``・``.view``・``.reshape``・``.ravel`` を通しても)・
  ``for a in X.<名>``(``.items()``・``.values()``・``enumerate``・``zip`` を通しても)で名に結び、その名への上の形の書き
  (``c[...] =``・``np.add.at(c, ...)``・``c += ...`` など)を元の名の書きとして数える。
- ``X.field("money")`` も ``money`` の列として扱う。
- 〔検収 M2〕名前を文字列で渡す書き: ``setattr(X, "<名>", v)``・``object.__setattr__(X, "<名>", v)``・
  ``vars(X)["<名>"] = v``・``X.__dict__["<名>"] = v``(名が定数の文字列のときだけ。変数の名は見えない=限界)。

書きは「その書きを含む一番外の関数」(``関数`` か ``クラス.メソッド``)に帰属させる(入れ子の関数・内包は外の関数)。

限界(記録 cp2/README.md): 名を値で持つ動的な書き(``reg.field(name)[...] =``・``setattr``)・タプルの中の別名・関数を
またぐ別名(引数で渡した配列への書き)は見えない。再開の書き手(``resolve.restore_soa``・``restore_items``)はこの形で
状態を戻す=名を書かないので数えない(状態のファイルの中身を戻すだけ=移動ではない)。

逐次ループ宣言: なし(試験の道具)。
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

from shibuya.economy import ops as OPS

#: 台帳の中の名(差し替えも書きとして数える)。
LEDGER_INTERNAL = frozenset({"_lines", "_flow", "_last_change_day"})
#: 中身を書くメソッド。
MUTATING_METHODS = frozenset({"fill", "put", "sort", "itemset", "resize", "setfield", "partition"})
#: 第 1 引数を書く numpy の関数。
MUTATING_FUNCS = frozenset({"copyto", "put", "place", "putmask", "put_along_axis", "fill_diagonal"})
#: 同じ中身を指す(写さない)属性・メソッド・関数。
VIEW_ATTRS = frozenset({"T", "flat", "real", "imag"})
VIEW_METHODS = frozenset({"view", "reshape", "ravel", "items", "values", "transpose", "swapaxes", "squeeze"})
VIEW_FUNCS = frozenset({"asarray", "asanyarray", "enumerate", "zip", "iter", "reversed", "atleast_1d"})


def is_money_attr(name: str) -> bool:
    return name in OPS.MONEY_ATTRS or name.startswith(OPS.MONEY_ATTR_PREFIX)


@dataclass(frozen=True)
class Write:
    """お金の列への書き 1 つ。"""

    path: str  # src/shibuya からの相対(``economy/ops.py``)
    func: str  # ``transfer``・``Ledger.on_day_end``・``<module>``
    attr: str  # 書いた列の属性の名
    line: int
    form: str  # 書きの形


class _Scanner(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.stack: list[str] = []
        self.out: list[Write] = []
        self.aliases: list[dict[str, str]] = [{}]

    # ---------------------------------------------------------------- 帰属
    def _owner(self) -> str:
        return self.stack[0] if self.stack else "<module>"

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if self.stack:  # 関数の中のクラス=外の関数に帰属
            self.generic_visit(node)
            return
        self._cls = node.name
        for b in node.body:
            if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._func(b, f"{node.name}.{b.name}")
            else:
                self.visit(b)
        self._cls = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self.stack:
            self.generic_visit(node)  # 入れ子=外の関数(別名の表も同じ)
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
        """関数の中の局所の別名(名 → 列の属性の名)。代入の順に 2 回回して鎖(``a = X._lines``・``b = a[0]``)も解く。"""
        al: dict[str, str] = {}
        for _ in range(2):
            for node in ast.walk(fn):
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    value = node.value
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    if value is None:
                        continue
                    a = self._root(value, al)
                    if a is None:
                        continue
                    for t in targets:
                        if isinstance(t, ast.Name):
                            al[t.id] = a
                elif isinstance(node, (ast.For, ast.comprehension)):
                    a = self._root(node.iter, al)
                    if a is None:
                        continue
                    for nm in ast.walk(node.target):
                        if isinstance(nm, ast.Name):
                            al[nm.id] = a
                elif isinstance(node, ast.withitem) and node.optional_vars is not None:
                    a = self._root(node.context_expr, al)
                    if a is not None and isinstance(node.optional_vars, ast.Name):
                        al[node.optional_vars.id] = a
        return al

    def _root(self, e: ast.AST, al: dict[str, str] | None = None) -> str | None:
        """式が指す中身がお金の列なら、その属性の名(別名・添字・ビューを通す)。"""
        al = self.aliases[-1] if al is None else al
        while True:
            if isinstance(e, ast.Attribute):
                if is_money_attr(e.attr):
                    return e.attr
                if e.attr in VIEW_ATTRS:
                    e = e.value
                    continue
                return None
            if isinstance(e, ast.Subscript):
                e = e.value
                continue
            if isinstance(e, ast.Starred):
                e = e.value
                continue
            if isinstance(e, ast.Name):
                return al.get(e.id)
            if isinstance(e, ast.Call):
                f = e.func
                if isinstance(f, ast.Attribute) and f.attr == "field" and e.args:
                    a0 = e.args[0]
                    if isinstance(a0, ast.Constant) and isinstance(a0.value, str) and is_money_attr(a0.value):
                        return a0.value
                    return None
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
            return None

    # ---------------------------------------------------------------- 書き
    def _add(self, attr: str | None, node: ast.AST, form: str) -> None:
        if attr is not None:
            self.out.append(Write(self.path, self._owner(), attr, int(getattr(node, "lineno", 0)), form))

    def _target(self, t: ast.AST, node: ast.AST, aug: bool) -> None:
        if isinstance(t, (ast.Tuple, ast.List)):
            for x in t.elts:
                self._target(x, node, aug)
        elif isinstance(t, ast.Starred):
            self._target(t.value, node, aug)
        elif isinstance(t, ast.Subscript):
            named = _dict_key_write(t)
            if named is not None:
                self._add(named, node, "vars/__dict__ の名前の書き")
                return
            self._add(self._root(t.value), node, "添字への代入" + ("(+=)" if aug else ""))
        elif isinstance(t, ast.Attribute):
            if t.attr in LEDGER_INTERNAL or t.attr.startswith(OPS.MONEY_ATTR_PREFIX):
                self._add(t.attr, node, "属性の差し替え" + ("(+=)" if aug else ""))
        elif isinstance(t, ast.Name) and aug:
            self._add(self.aliases[-1].get(t.id), node, "別名への +=")

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

    def visit_Call(self, node: ast.Call) -> None:
        f = node.func
        fname = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        if fname in ("setattr", "__setattr__") and len(node.args) >= 2:  # setattr(X, "名", v)・object.__setattr__
            a1 = node.args[1]
            if isinstance(a1, ast.Constant) and isinstance(a1.value, str) and is_money_attr(a1.value):
                self._add(a1.value, node, "setattr")
        if isinstance(f, ast.Attribute):
            if f.attr == "at" and node.args:  # np.<ufunc>.at(X, ...)
                self._add(self._root(node.args[0]), node, f"ufunc.at")
            elif f.attr in MUTATING_METHODS:
                self._add(self._root(f.value), node, f".{f.attr}()")
            if f.attr in MUTATING_FUNCS and node.args:
                self._add(self._root(node.args[0]), node, f"np.{f.attr}")
        elif isinstance(f, ast.Name) and f.id in MUTATING_FUNCS and node.args:
            self._add(self._root(node.args[0]), node, f.id)
        for kw in node.keywords:
            if kw.arg == "out":
                vals = kw.value.elts if isinstance(kw.value, (ast.Tuple, ast.List)) else [kw.value]
                for v in vals:
                    self._add(self._root(v), node, "out=")
        self.generic_visit(node)


def _dict_key_write(t: ast.Subscript) -> str | None:
    """``vars(X)["名"]``・``X.__dict__["名"]`` への書きなら、その名(お金の列の名のときだけ)。"""
    v, key = t.value, t.slice
    if not (isinstance(key, ast.Constant) and isinstance(key.value, str) and is_money_attr(key.value)):
        return None
    if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "vars":
        return key.value
    if isinstance(v, ast.Attribute) and v.attr == "__dict__":
        return key.value
    return None


def scan_source(text: str, path: str) -> list[Write]:
    """1 つのファイルの中身からお金の列への書きを集める。"""
    sc = _Scanner(path)
    sc._cls = None  # type: ignore[attr-defined]
    sc.visit(ast.parse(text))
    return sc.out


def iter_sources(root: Path) -> Iterator[tuple[str, str]]:
    for p in sorted(root.rglob("*.py")):
        yield str(p.relative_to(root)).replace("\\", "/"), p.read_text(encoding="utf-8")


def scan_tree(root: Path) -> list[Write]:
    out: list[Write] = []
    for rel, text in iter_sources(root):
        out.extend(scan_source(text, rel))
    return out


#: 基本操作(お金の書き手)の置き場と名。
PRIMITIVE = ("economy/ops.py", "transfer")


def violations(writes: Iterable[Write], declared: dict[tuple[str, str], set[str]]) -> list[Write]:
    """基本操作の外で、宣言の表(置き場, 関数)→ 列の名 に無い書き。"""
    bad: list[Write] = []
    for w in writes:
        if (w.path, w.func) == PRIMITIVE:
            continue
        if w.attr in declared.get((w.path, w.func), set()):
            continue
        bad.append(w)
    return bad
