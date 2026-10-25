"""第 1 期 1-5(検収 M1): 権利台帳の中身を書く所を AST で集める道具(試験の補助・src は読むだけ)。

書く形の広さは 1-9 の ``tests/economy/cp2/money_writers.py``(お金の列の書き手)と同じにした(本体の 1-9 はこの枝の
rebase の後に来るので、規則をここに写した。rebase の後に共通化できれば共通化する):

- 中身の書き: ``X.<列>[...] =``・``+=``(添字の鎖の根が列)・``np.<ufunc>.at(X.<列>, ...)``・``X.<列>.fill(...)``(``put``・
  ``sort``・``itemset``・``resize``・``setfield``・``partition`` も)・``np.copyto/put/place/putmask/...(X.<列>, ...)``・
  キーワード ``out=X.<列>``。
- 局所の別名: ``c = X.<列>[...]``(添字・``.T``・``np.asarray``・``.view``・``.reshape``・``.ravel`` を通しても)・
  ``c = getattr(X, "<列>")``・``for a in X.<列>`` で名に結び、その名への上の形の書きを列の書きとして数える。
- 差し替え: ``X.<名> =``(列・``n``・``sources``・``source_codes``)・``setattr``/``object.__setattr__``/``delattr``/
  ``object.__delattr__``(名が定数ならその名・**名が式なら「?」=名の分からない差し替え**)・``vars(X)["<名>"] =``・
  ``X.__dict__["<名>"] =``。
- ``getattr(X, <式>)``(名が式)は名の分からない列(「?」)として扱う(``getattr(st, name)[i] = v`` も書きになる)。

列=名が ``_r_`` で始まる属性(``engine/rights/ledger.py`` の ``_COLS``)。台帳の中の名=``n``・``sources``・``source_codes``
(``_Store`` の欄)と名を変えた slot ``_Rights__st``(source には ``self.__st`` と書く)。

- ``ledger_writes``: 台帳の置き場(``ledger.py``)の中の書きを「クラス.メソッド」に帰属させて集める。試験は、列の中身の書きが
  ``Rights._write`` だけ・差し替えが ``_Store.__init__``・``Rights.__init__``・``Rights.grant``・``Rights._grow`` だけ・
  ``_write`` を呼ぶのが ``grant``・``revoke`` だけ・``_grow`` を呼ぶのが ``grant`` だけ、を見る。
- ``outside_touches``: 台帳の置き場の外(src の全部)から中身に触る所(列の名・名を変えた slot・``_Store``・``_COL_NAMES``・
  ``_COLS`` の参照、名を組み立てる文字列=定数の足し算と f 文字列の頭、中の名への ``setattr`` の 4 形、他の物の ``_write``/
  ``_grow``)を集める。

限界: 名を変数で持って渡す外からの ``getattr(rights, name)`` は見えない(名を組み立てる所が別のファイルにあれば見えない)・
関数をまたぐ別名(引数で渡した列への書き)も見えない(1-9 と同じ)。実行時は ``Rights`` が ``__slots__`` だけなので
``object.__setattr__(rights, "_n", …)`` など名の無い属性は置けないが、名を変えた slot の名を知って触る形は止まらない。

逐次ループ宣言: なし(試験の道具)。
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

#: 列の名の頭(``ledger._COLS``)。
COL_PREFIX = "_r_"
#: ``_Store`` の列でない欄(差し替えを数える)。
STORE_FIELDS = frozenset({"n", "sources", "source_codes"})
#: 名を変えた slot(source の名と実の名)。
SLOT_NAMES = frozenset({"__st", "_Rights__st"})
#: 台帳の置き場の外から触ってはいけない名(属性・import の名・文字列)。
INTERNAL_NAMES = frozenset({"_Rights__st", "__st", "_COL_NAMES", "_COLS", "_Store", "_source_codes"})
#: 外から ``setattr`` の 4 形で置いてはいけない名(旧い名 ``_n``・``_sources`` も=実行時には置けないが試みを数える)。
OUTSIDE_SET_NAMES = frozenset({"_n", "_sources", "_source_codes", "_Rights__st"})
#: 中身を書くメソッド(1-9 と同じ)。
MUTATING_METHODS = frozenset({"fill", "put", "sort", "itemset", "resize", "setfield", "partition"})
#: 第 1 引数を書く numpy の関数(1-9 と同じ)。
MUTATING_FUNCS = frozenset({"copyto", "put", "place", "putmask", "put_along_axis", "fill_diagonal"})
#: 同じ中身を指す(写さない)属性・メソッド・関数(1-9 と同じ)。
VIEW_ATTRS = frozenset({"T", "flat", "real", "imag"})
VIEW_METHODS = frozenset({"view", "reshape", "ravel", "items", "values", "transpose", "swapaxes", "squeeze"})
VIEW_FUNCS = frozenset({"asarray", "asanyarray", "enumerate", "zip", "iter", "reversed", "atleast_1d"})
#: 名で属性を置く・消す関数。
SETTERS = frozenset({"setattr", "__setattr__", "delattr", "__delattr__"})
UNKNOWN = "?"


def is_col(name: str) -> bool:
    return name.startswith(COL_PREFIX)


@dataclass(frozen=True)
class Write:
    func: str   # ``Rights.grant``・``_Store.__init__``・``<module>``
    name: str   # 書いた列・欄の名(名が式なら ``?``)
    line: int
    kind: str   # ``content``(列の中身)・``replace``(属性の差し替え)・``call``(``_write``/``_grow`` を呼んだ)
    form: str


class _LedgerScanner(ast.NodeVisitor):
    def __init__(self) -> None:
        self.stack: list[str] = []
        self.cls: str | None = None
        self.out: list[Write] = []
        self.aliases: list[dict[str, str]] = [{}]

    def _owner(self) -> str:
        return self.stack[0] if self.stack else "<module>"

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if self.stack:
            self.generic_visit(node)
            return
        prev, self.cls = self.cls, node.name
        for b in node.body:
            if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._func(b, f"{node.name}.{b.name}")
            else:
                self.visit(b)
        self.cls = prev

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
        for _ in range(2):
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
        """式が指す中身が台帳の列なら、その名(別名・添字・ビュー・``getattr`` を通す。名が式なら ``?``)。"""
        al = self.aliases[-1] if al is None else al
        while True:
            if isinstance(e, ast.Attribute):
                if is_col(e.attr):
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
                        return a1.value if is_col(a1.value) else None
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
                self._add(named, node, "replace", "vars/__dict__ の名前の書き")
                return
            self._add(self._root(t.value), node, "content", "添字への代入" + ("(+=)" if aug else ""))
        elif isinstance(t, ast.Attribute):
            if is_col(t.attr) or t.attr in STORE_FIELDS or t.attr in SLOT_NAMES:
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

    def visit_Call(self, node: ast.Call) -> None:
        f = node.func
        fname = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        if fname in SETTERS and len(node.args) >= 2:
            a1 = node.args[1]
            if isinstance(a1, ast.Constant) and isinstance(a1.value, str):
                if is_col(a1.value) or a1.value in STORE_FIELDS or a1.value in SLOT_NAMES:
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
            if f.attr in ("_write", "_grow"):
                self._add(f.attr, node, "call", f.attr)
        elif isinstance(f, ast.Name) and f.id in MUTATING_FUNCS and node.args:
            self._add(self._root(node.args[0]), node, "content", f.id)
        for kw in node.keywords:
            if kw.arg == "out":
                vals = kw.value.elts if isinstance(kw.value, (ast.Tuple, ast.List)) else [kw.value]
                for v in vals:
                    self._add(self._root(v), node, "content", "out=")
        self.generic_visit(node)


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


def ledger_writes(source: str) -> list[Write]:
    """台帳の置き場の中の書き(列の中身・差し替え・``_write``/``_grow`` の呼び出し)。"""
    sc = _LedgerScanner()
    sc.visit(ast.parse(source))
    return sc.out


#: 書きの種類ごとに許す所(関数の名)。
ALLOWED: dict[str, frozenset[str]] = {
    "content": frozenset({"Rights._write"}),
    "replace": frozenset({"_Store.__init__", "Rights.__init__", "Rights.grant", "Rights._grow"}),
}
ALLOWED_CALLS: dict[str, frozenset[str]] = {
    "_write": frozenset({"Rights.grant", "Rights.revoke"}),
    "_grow": frozenset({"Rights.grant"}),
}
#: 差し替えのうち、``Right`` の凍結の中の置き(``object.__setattr__(self, "holder", …)``)は数えない(名が台帳の名でない)。


def ledger_violations(source: str) -> list[str]:
    out: list[str] = []
    for w in ledger_writes(source):
        if w.kind == "call":
            if w.func not in ALLOWED_CALLS[w.name]:
                out.append(f"{w.func}:{w.line} {w.name} を呼ぶ")
        elif w.func not in ALLOWED[w.kind]:
            out.append(f"{w.func}:{w.line} {w.kind} {w.name} ({w.form})")
    return out


# ================================================================ 台帳の置き場の外
def _fold_str(e: ast.AST) -> str | None:
    """定数の文字列の足し算と f 文字列の頭(定数の部分)を畳む(名を組み立てる形を見るため)。"""
    if isinstance(e, ast.Constant) and isinstance(e.value, str):
        return e.value
    if isinstance(e, ast.BinOp) and isinstance(e.op, ast.Add):
        a = _fold_str(e.left)
        if a is None:
            return None
        b = _fold_str(e.right)
        return a + (b if b is not None else "\x00")
    if isinstance(e, ast.JoinedStr):
        head = ""
        for v in e.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                head += v.value
            else:
                return head + "\x00"
        return head
    return None


def _internal_str(s: str) -> bool:
    return s.startswith(COL_PREFIX) or s.startswith("_Rights__") or s.split("\x00", 1)[0] in INTERNAL_NAMES


def outside_touches(source: str, path: str) -> list[str]:
    """台帳の置き場の外から中身に触る所(``path:行 形``)。"""
    out: list[str] = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        if isinstance(node, ast.Attribute):
            if is_col(node.attr) or node.attr in INTERNAL_NAMES:
                out.append(f"{path}:{line} 属性 {node.attr}")
            elif node.attr in ("_write", "_grow", "_sources") and not (
                    isinstance(node.value, ast.Name) and node.value.id == "self"):
                out.append(f"{path}:{line} 他の物の {ast.unparse(node)}")  # 自分の self._grow は別の物
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith("shibuya.engine.rights"):
            for a in node.names:
                if a.name in INTERNAL_NAMES:
                    out.append(f"{path}:{line} import {a.name}")
        elif isinstance(node, (ast.BinOp, ast.JoinedStr)) or (
                isinstance(node, ast.Constant) and isinstance(node.value, str)):
            s = _fold_str(node)
            if s is not None and _internal_str(s):
                out.append(f"{path}:{line} 文字列 {s.split(chr(0), 1)[0]!r}")
        if isinstance(node, ast.Call):
            f = node.func
            fname = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            if fname in SETTERS and len(node.args) >= 2:
                s = _fold_str(node.args[1])
                on_self = isinstance(node.args[0], ast.Name) and node.args[0].id == "self"
                # ``_n``・``_sources`` は広く使う名=自分(self)の欄の置きは数えない(規則の表 ``Rules`` も ``_n`` を持つ)
                if s is not None and (_internal_str(s) or (s in OUTSIDE_SET_NAMES and not on_self)):
                    out.append(f"{path}:{line} {fname} {s.split(chr(0), 1)[0]!r}")
        if isinstance(node, ast.Subscript):
            k = _dict_key(node)
            if k is not None and k != UNKNOWN and (k in OUTSIDE_SET_NAMES or _internal_str(k)):
                out.append(f"{path}:{line} vars/__dict__ {k!r}")
    return sorted(set(out))


def iter_sources(root: Path, skip: Path) -> Iterator[tuple[str, str]]:
    for fp in sorted(root.rglob("*.py")):
        if fp.resolve() == skip.resolve():
            continue
        yield fp.relative_to(root).as_posix(), fp.read_text(encoding="utf-8")
