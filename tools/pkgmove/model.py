# -*- coding: utf-8 -*-
"""木(ファイルの中身を手元に持つ)とモジュールの索引・頭の再輸出の引き先。

- 木は、リポの根からの道筋(``/`` 区切り)→ 中身。Python のファイルは文字列(改行はファイルのまま=``\\r\\n`` も保つ)、
  ほかのファイル(移す JSON)はバイト列。読むのは ``src/shibuya`` の全部と ``tests``・``tools`` の ``.py``。
- 位置: AST の ``col_offset`` は行の中の UTF-8 のバイトの位置なので、:class:`Text` が文字の位置へ直す。
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Final, Iterator

SRC_PREFIX: Final[str] = "src/shibuya/"
PKG_NAME: Final[str] = "shibuya"
#: 書き換えない木の道筋(道具そのものと道具の試験=古い道筋を表として持つ)。
SELF_PATHS: Final[tuple[str, ...]] = ("tools/pkgmove/", "tests/tools/test_pkgmove.py")
_SKIP_DIRS: Final[frozenset[str]] = frozenset({"__pycache__", ".venv", ".git", ".pytest_cache", "node_modules"})
_EOL_RE = re.compile(r"\r\n|\r|\n")


@lru_cache(maxsize=8192)
def parse(text: str) -> ast.Module:
    """``ast.parse`` の覚え書き(同じ文字列は同じ木=木は書き換えない約束で使う)。"""
    return ast.parse(text)


def mod_of(rel_in_pkg: str) -> str:
    """``src/shibuya`` からの道筋 → モジュールの名(``core/rng.py`` → ``shibuya.core.rng``・頭は包みの名)。"""
    parts = rel_in_pkg[:-3].split("/") if rel_in_pkg.endswith(".py") else rel_in_pkg.split("/")
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join([PKG_NAME, *[p for p in parts if p]])


def rel_of_mod(mod: str, *, package: bool) -> str:
    """モジュールの名 → ``src/shibuya`` からの道筋。"""
    parts = mod.split(".")[1:]
    return "/".join([*parts, "__init__.py"]) if package else "/".join(parts) + ".py"


class Text:
    """1 本のファイルの文字列と、行と位置の換算。"""

    def __init__(self, text: str) -> None:
        self.text = text
        starts = [0]
        for m in _EOL_RE.finditer(text):
            starts.append(m.end())
        self.starts = starts

    @cached_property
    def eol(self) -> str:
        m = _EOL_RE.search(self.text)
        return m.group(0) if m else "\n"

    def line(self, lineno: int) -> str:
        """``lineno`` 行(1 から)の中身(改行を含まない)。"""
        a = self.starts[lineno - 1]
        b = self.starts[lineno] if lineno < len(self.starts) else len(self.text)
        s = self.text[a:b]
        return s.rstrip("\r\n")

    def off(self, lineno: int, col_bytes: int) -> int:
        """AST の位置(行・行の中のバイト)→ 文字列の位置。"""
        ln = self.line(lineno)
        return self.starts[lineno - 1] + len(ln.encode("utf-8")[:col_bytes].decode("utf-8"))

    def span(self, node: ast.AST) -> tuple[int, int]:
        return (self.off(node.lineno, node.col_offset),  # type: ignore[attr-defined]
                self.off(node.end_lineno, node.end_col_offset))  # type: ignore[attr-defined]


def docstring_ids(tree: ast.AST) -> set[int]:
    """docstring の定数(``id``)。"""
    out: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.body:
            b0 = n.body[0]
            if isinstance(b0, ast.Expr) and isinstance(b0.value, ast.Constant) and isinstance(b0.value.value, str):
                out.add(id(b0.value))
    return out


def symbol_map(tree: ast.Module) -> dict[int, str]:
    """木の中の各ノード(``id``)→ 記号の名。頂上の関数とクラスはその名(メソッドは ``クラス.メソッド``・関数の中の
    入れ子は外の関数の名)、頂上の代入は左辺の名(複数なら ``,`` でつなぐ)、クラスの本体の文はクラスの名、ほかの頂上の文は
    ``<module>``。飾り(デコレータ)は関数の記号に入る。"""
    out: dict[int, str] = {}

    def mark(node: ast.AST, sym: str) -> None:
        for x in ast.walk(node):
            out.setdefault(id(x), sym)

    for st in tree.body:
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
            mark(st, st.name)
        elif isinstance(st, ast.ClassDef):
            for s in st.body:
                if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    mark(s, f"{st.name}.{s.name}")
            mark(st, st.name)
        elif isinstance(st, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            tg = st.targets if isinstance(st, ast.Assign) else [st.target]
            names = [n.id for t in tg for n in ast.walk(t) if isinstance(n, ast.Name)]
            mark(st, ",".join(names) if names else "<module>")
        else:
            mark(st, "<module>")
    return out


@lru_cache(maxsize=8192)
def symbols_of(text: str) -> dict[int, str]:
    """:func:`symbol_map` の覚え書き(:func:`parse` の木に対して)。"""
    return symbol_map(parse(text))


@lru_cache(maxsize=8192)
def docstrings_of(text: str) -> frozenset[int]:
    """:func:`docstring_ids` の覚え書き(:func:`parse` の木に対して)。"""
    return frozenset(docstring_ids(parse(text)))


def area_of(path: str) -> str:
    """木の道筋の区分(``src``・``build``・``tests``・``tools``・``docs``・``other``)。"""
    if path.startswith(SRC_PREFIX + "build/"):
        return "build"
    if path.startswith(SRC_PREFIX):
        return "src"
    if path.startswith("tests/"):
        return "tests"
    if path.startswith("tools/"):
        return "tools"
    if path.startswith("docs/"):
        return "docs"
    return "other"


def is_self(path: str) -> bool:
    return any(path == p or (p.endswith("/") and path.startswith(p)) for p in SELF_PATHS)


@dataclass
class Tree:
    """木の中身。``files`` は Python(文字列)、``blobs`` は src の中のほかのファイル(バイト列)。"""

    files: dict[str, str]
    blobs: dict[str, bytes] = field(default_factory=dict)

    @classmethod
    def load(cls, root: Path, extra: tuple[str, ...] | list[str] = ()) -> "Tree":
        """``src/shibuya`` の全部と ``tests``・``tools`` の ``.py``。``extra`` は足して読む ``.py``(リポの根からの道筋=
        tests が読む docs の記録の道具。無ければ飛ばす)。"""
        files: dict[str, str] = {}
        blobs: dict[str, bytes] = {}
        for rel in extra:
            if (root / rel).is_file():
                files[rel] = (root / rel).read_bytes().decode("utf-8")
        for top in ("src/shibuya", "tests", "tools"):
            base = root / top
            if not base.is_dir():
                continue
            for p in _walk(base):
                rel = p.relative_to(root).as_posix()
                if p.suffix == ".py":
                    files[rel] = p.read_bytes().decode("utf-8")
                elif rel.startswith(SRC_PREFIX):
                    blobs[rel] = p.read_bytes()
        return cls(files=files, blobs=blobs)

    def copy(self) -> "Tree":
        return Tree(files=dict(self.files), blobs=dict(self.blobs))

    def exists(self, path: str) -> bool:
        return path in self.files or path in self.blobs

    def src_rels(self) -> list[str]:
        """src の中の道筋(``src/shibuya`` からの相対)。"""
        return sorted(p[len(SRC_PREFIX):] for p in [*self.files, *self.blobs] if p.startswith(SRC_PREFIX))


def _walk(base: Path) -> Iterator[Path]:
    for p in sorted(base.iterdir()):
        if p.is_dir():
            if p.name in _SKIP_DIRS:
                continue
            yield from _walk(p)
        elif p.is_file():
            yield p


@dataclass
class ModInfo:
    """モジュールの頂上の名: 定義した名と、import で結んだ名(名 → (モジュール, 元の名))。"""

    defs: set[str]
    imports: dict[str, tuple[str, str]]
    module_imports: dict[str, str]


class Index:
    """木の src のモジュールの索引(名 → 道筋)と、頭の再輸出の引き先。"""

    def __init__(self, tree: Tree) -> None:
        self.tree = tree
        self.mods: dict[str, str] = {}
        self.packages: set[str] = set()
        for rel in tree.src_rels():
            if not rel.endswith(".py"):
                continue
            m = mod_of(rel)
            self.mods[m] = SRC_PREFIX + rel
            if rel.endswith("__init__.py"):
                self.packages.add(m)
        self._info: dict[str, ModInfo] = {}

    def exists(self, mod: str) -> bool:
        return mod in self.mods

    def is_package(self, mod: str) -> bool:
        return mod in self.packages

    def longest_module(self, dotted: str) -> str | None:
        """``dotted`` の頭のうち、木にあるいちばん長いモジュールの名。"""
        parts = dotted.split(".")
        for i in range(len(parts), 0, -1):
            m = ".".join(parts[:i])
            if m in self.mods:
                return m
        return None

    def info(self, mod: str) -> ModInfo:
        if mod in self._info:
            return self._info[mod]
        path = self.mods.get(mod)
        defs: set[str] = set()
        imports: dict[str, tuple[str, str]] = {}
        module_imports: dict[str, str] = {}
        if path is not None:
            tree = parse(self.tree.files[path])
            pkg = mod if self.is_package(mod) else mod.rpartition(".")[0]
            for n in tree.body:
                for s in _top_statements(n):
                    if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        defs.add(s.name)
                    elif isinstance(s, ast.Assign):
                        for t in s.targets:
                            for nn in ast.walk(t):
                                if isinstance(nn, ast.Name):
                                    defs.add(nn.id)
                    elif isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name):
                        defs.add(s.target.id)
                    elif isinstance(s, ast.ImportFrom):
                        src = resolve_from(pkg, s)
                        if src is None:
                            continue
                        for a in s.names:
                            if a.name != "*":
                                imports[a.asname or a.name] = (src, a.name)
                    elif isinstance(s, ast.Import):
                        for a in s.names:
                            if a.asname:
                                module_imports[a.asname] = a.name
        self._info[mod] = ModInfo(defs=defs, imports=imports, module_imports=module_imports)
        return self._info[mod]

    def origin(self, mod: str, name: str, _depth: int = 0) -> tuple[str, str] | None:
        """``mod`` の名 ``name`` を定義したモジュールと元の名(import をたどる)。見つからなければ ``None``。"""
        if _depth > 20 or mod not in self.mods:
            return None
        inf = self.info(mod)
        if name in inf.defs:
            return mod, name
        if name in inf.imports:
            src, orig = inf.imports[name]
            sub = f"{src}.{orig}"
            if sub in self.mods:  # ``from P import submodule`` を結んだ名
                return None
            got = self.origin(src, orig, _depth + 1)
            return got if got is not None else (src, orig)
        return None


@dataclass
class Ctx:
    """選んだ段の書き換えの材料(木は移す前のもの)。"""

    index: Index
    #: 古いモジュールの名 → 新しいモジュールの名(移すファイルと、移す頭=包みの名)。
    modmap: dict[str, str]
    #: 頭を空にするか消す包み(古い名)。この頭を通る import は元のモジュールへ向ける。
    heads_changed: set[str]
    #: tests と tools の点の名のうち書き換えないもの(凍結のクラスの名など=凍結の値)。
    frozen_tokens: frozenset[str] = frozenset()

    def new_mod(self, mod: str) -> str:
        return self.modmap.get(mod, mod)


@dataclass(frozen=True)
class Edit:
    """1 か所の書き換え(文字列の位置 ``start``〜``end`` を ``new`` に)。``kind``: ``import``・``path``・``class_key``。"""

    start: int
    end: int
    new: str
    kind: str
    symbol: str = ""
    note: str = ""


def apply_edits(text: str, edits: list[Edit]) -> str:
    """重ならない書き換えを当てる(重なれば止める)。"""
    out = text
    last = len(text) + 1
    for e in sorted(edits, key=lambda e: (e.start, e.end), reverse=True):
        if e.end > last:
            raise ValueError(f"書き換えが重なる: {e}")
        out = out[: e.start] + e.new + out[e.end:]
        last = e.start
    return out


def _top_statements(n: ast.stmt) -> Iterator[ast.stmt]:
    """頂上の文(``if``・``try`` の中も頂上として見る)。"""
    if isinstance(n, ast.If):
        for s in [*n.body, *n.orelse]:
            yield from _top_statements(s)
    elif isinstance(n, ast.Try):
        for s in [*n.body, *n.orelse, *n.finalbody, *[x for h in n.handlers for x in h.body]]:
            yield from _top_statements(s)
    else:
        yield n


def resolve_from(pkg: str, node: ast.ImportFrom) -> str | None:
    """``from … import`` のモジュールの名(相対は ``pkg`` から解く)。"""
    if node.level == 0:
        return node.module
    parts = pkg.split(".")
    if node.level - 1 > len(parts):
        return None
    base = parts[: len(parts) - (node.level - 1)]
    return ".".join([*base, *(node.module.split(".") if node.module else [])])
