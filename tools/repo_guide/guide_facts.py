# -*- coding: utf-8 -*-
"""ファイルごとの事実を AST と本文の文字列から集める(対象のコードは import も実行もしない)。

集めるもの: 冒頭の説明・公開の関数とクラス・import・試験が道筋で指すファイル・CLI の引数・環境変数・決定の ID。
読み方の規則は ``guide_render.RULES`` に書いてカードの入口の索引に載せる。ここの正規表現を変えたら、そこも直す。
"""
from __future__ import annotations

import ast
import posixpath
import re
import sys
from dataclasses import dataclass, field

SKIP_ROOTS_FOR_SIBLING = ("src/",)  # src は絶対 import だけ(同じディレクトリの素の名前で解かない)
_ROOT_PACKAGES = ("tests", "tools")  # 素の import の先頭がこれならリポの根から(ほかは src/ の下)
_PY_NAME = re.compile(r"^[\w./-]+\.py$")
_PROJECT_ENV = re.compile(r"^SHIBUYA_[A-Z0-9_]+$")  # 読み口が関数の引数になる形(``os.environ.get(name)``)のために名前を拾う
_PATH_VALUES_CAP = 32  # 1 つの式か名前が指しうる道筋の数の上限(超えたら読めないとする)


@dataclass(frozen=True)
class ImportRef:
    module: str
    names: tuple[str, ...]
    level: int


@dataclass
class FileFacts:
    rel: str
    error: str = ""
    summary: str = ""
    public: list[tuple[str, str, str]] = field(default_factory=list)  # (種類, 名前, docstring の 1 行目)
    imports: list[ImportRef] = field(default_factory=list)
    path_mentions: set[str] = field(default_factory=set)
    syspath_dirs: set[str] = field(default_factory=set)
    syspath_unread: int = 0
    cli_args: dict[str, str | None] = field(default_factory=dict)  # 旗の名 → help の 1 行(``None``=定数でなく読めない)
    cli_subcommands: set[str] = field(default_factory=set)
    cli_unread: int = 0
    cli_argv: bool = False
    env_names: set[str] = field(default_factory=set)
    env_unread: int = 0
    env_whole: bool = False
    decision_ids: set[str] = field(default_factory=set)


def normalized_text(raw: bytes) -> str:
    """UTF-8(BOM は外す)で読み、改行を LF にする。読めなければ ``UnicodeDecodeError``。"""
    return raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def join_lines(lines: list[str]) -> str:
    """折り返しを 1 行に戻す(どちらかの端が ASCII でなければ空白を入れない)。"""
    out = ""
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if out and out[-1].isascii() and s[0].isascii():
            out += " "
        out += s
    return out


def first_paragraph(doc: str | None) -> str:
    if not doc:
        return ""
    return join_lines(doc.split("\n\n", 1)[0].split("\n"))


def first_line(doc: str | None) -> str:
    if not doc:
        return ""
    parts = doc.strip().split("\n", 1)
    return parts[0].strip() if parts else ""


def _public_of(tree: ast.Module) -> list[tuple[str, str, str]]:
    """頂上(``if``・``try``・``with`` の中を含む)の ``_`` で始まらない関数とクラス。名前で並べる。"""
    found: dict[str, tuple[str, str, str]] = {}
    stack: list[ast.stmt] = list(tree.body)
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not n.name.startswith("_"):
                kind = "クラス" if isinstance(n, ast.ClassDef) else "関数"
                doc = first_line(ast.get_docstring(n))
                cur = found.get(n.name)
                if cur is None or (not cur[2] and doc):
                    found[n.name] = (kind, n.name, doc)
        elif isinstance(n, (ast.If, ast.Try, ast.With)):
            for attr in ("body", "orelse", "handlers", "finalbody"):
                for ch in getattr(n, attr, []):
                    if isinstance(ch, ast.ExceptHandler):
                        stack.extend(ch.body)
                    else:
                        stack.append(ch)
    return [found[k] for k in sorted(found)]


def _imports_of(tree: ast.Module) -> list[ImportRef]:
    """関数の中を含む全部の import と ``import_module("文字列")``。"""
    refs: set[ImportRef] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                refs.add(ImportRef(a.name, (), 0))
        elif isinstance(n, ast.ImportFrom):
            refs.add(ImportRef(n.module or "", tuple(sorted(a.name for a in n.names)), n.level))
        elif (isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.Constant)
              and isinstance(n.args[0].value, str)):
            f = n.func
            fname = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            if fname == "import_module":
                refs.add(ImportRef(n.args[0].value, (), 0))
    return sorted(refs, key=lambda r: (r.module, r.level, r.names))


def _up(path: str, steps: int = 1) -> str | None:
    """親へ ``steps`` 段(リポの根は ``""``)。根より上は ``None``。"""
    parts = path.split("/") if path else []
    if steps > len(parts):
        return None
    return "/".join(parts[: len(parts) - steps])


def _join(left: str, right: str) -> str | None:
    """つないで ``..`` を畳む。根より上へ出れば ``None``。"""
    norm = posixpath.normpath(f"{left}/{right}" if left else right)
    if norm == ".":
        return ""
    return None if norm == ".." or norm.startswith("../") else norm


def _ups(values: set[str], steps: int = 1) -> set[str]:
    return {u for u in (_up(v, steps) for v in values) if u is not None}


def _joins(lefts: set[str], rights: set[str]) -> set[str]:
    """左が読めなければ右(分かる末尾)をリポからの道筋とみなす(``ROOT / "tools"`` の ``ROOT`` が引数のとき)。"""
    if not lefts:
        return rights
    return {j for j in (_join(a, b) for a in lefts for b in rights) if j is not None}


def _capped(values: set[str]) -> set[str]:
    return values if len(values) <= _PATH_VALUES_CAP else set()


def _is_path_module(f: ast.Attribute) -> bool:
    """``os.path.join``・``path.join`` か(``"/".join`` を除く)。"""
    v = f.value
    return (isinstance(v, ast.Attribute) and v.attr == "path") or (isinstance(v, ast.Name) and v.id in ("path", "osp"))


def _paths_of(node: ast.AST, names: dict[str, set[str]], rel: str) -> set[str]:
    """式が指しうるリポからの道筋の集合(空=読めない)。

    ``__file__`` はそのファイル。``Path(…)``・``str(…)``・``.resolve()``・``os.path.abspath(…)`` は透かし、``.parent``・
    ``.parents[n]``・``os.path.dirname(…)``・``/``・``os.path.join(…)``・``.joinpath(…)`` をたどる。名前は代入と ``for`` の値の和。
    """
    if isinstance(node, ast.Constant):
        return {node.value} if isinstance(node.value, str) else set()
    if isinstance(node, ast.Name):
        return {rel} if node.id == "__file__" else set(names.get(node.id, ()))
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return _capped(set().union(*(_paths_of(e, names, rel) for e in node.elts))) if node.elts else set()
    if isinstance(node, ast.IfExp):
        return _paths_of(node.body, names, rel) | _paths_of(node.orelse, names, rel)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _capped(_joins(_paths_of(node.left, names, rel), _paths_of(node.right, names, rel)))
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        return _ups(_paths_of(node.value, names, rel))
    if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "parents"
            and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int)):
        return _ups(_paths_of(node.value.value, names, rel), node.slice.value + 1)
    if isinstance(node, ast.Call):
        f = node.func
        fname = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        if fname in ("str", "Path", "fspath") and len(node.args) == 1:
            return _paths_of(node.args[0], names, rel)
        if fname in ("abspath", "realpath", "normpath") and len(node.args) == 1:
            return _paths_of(node.args[0], names, rel)
        if fname == "resolve" and isinstance(f, ast.Attribute):
            return _paths_of(f.value, names, rel)
        if fname == "absolute" and isinstance(f, ast.Attribute):
            return _paths_of(f.value, names, rel)
        if fname == "dirname" and len(node.args) == 1:
            return _ups(_paths_of(node.args[0], names, rel))
        if (fname == "joinpath" and isinstance(f, ast.Attribute)) or (
                fname == "join" and isinstance(f, ast.Attribute) and _is_path_module(f) and node.args):
            values = _paths_of(f.value, names, rel) if fname == "joinpath" else set()
            for a in node.args:
                values = _capped(_joins(values, _paths_of(a, names, rel)))
            return values
    return set()


def _bindings(tree: ast.Module) -> list[tuple[str, ast.AST]]:
    """(名前, 値の式)。代入・注釈つきの代入・``for``・内包の変数。"""
    out: list[tuple[str, ast.AST]] = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            out.append((n.targets[0].id, n.value))
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None:
            out.append((n.target.id, n.value))
        elif isinstance(n, (ast.For, ast.comprehension)) and isinstance(n.target, ast.Name):
            out.append((n.target.id, n.iter))
    return out


def _path_facts(tree: ast.Module, rel: str) -> tuple[set[str], set[str], int]:
    """(道筋で指すもの, ``sys.path`` に足すディレクトリ, 足す先を読めない呼び出しの数)。"""
    names: dict[str, set[str]] = {}
    bindings = _bindings(tree)
    for _ in range(4):  # 名前の参照が順に並ばない場合のために何度か通す(値は増えるだけ)
        for name, value in bindings:
            values = _paths_of(value, names, rel)
            if values:
                names[name] = _capped(names.get(name, set()) | values)
    doc_nodes = {id(n.value) for n in ast.walk(tree)
                 if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)}
    mentions: set[str] = set()
    syspaths: set[str] = set()
    unread = 0
    for n in ast.walk(tree):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
            mentions.update(p for p in _paths_of(n, names, rel) if p.endswith(".py"))
        elif (isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc_nodes
              and _PY_NAME.match(n.value)):
            mentions.add(n.value.removeprefix("./"))
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.args:
            f = n.func
            if f.attr in ("joinpath", "join"):
                mentions.update(p for p in _paths_of(n, names, rel) if p.endswith(".py"))
            on_syspath = (f.attr in ("insert", "append") and isinstance(f.value, ast.Attribute)
                          and f.value.attr == "path" and isinstance(f.value.value, ast.Name)
                          and f.value.value.id == "sys")
            if on_syspath or f.attr == "syspath_prepend":
                values = _paths_of(n.args[-1], names, rel)
                if values:
                    syspaths.update(values)
                else:
                    unread += 1
    return mentions, syspaths, unread


def _module_strings(tree: ast.Module) -> dict[str, str]:
    out: dict[str, str] = {}
    for n in tree.body:
        tgt = n.targets[0] if isinstance(n, ast.Assign) and len(n.targets) == 1 else (
            n.target if isinstance(n, ast.AnnAssign) else None)
        value = getattr(n, "value", None)
        if isinstance(tgt, ast.Name) and isinstance(value, ast.Constant) and isinstance(value.value, str):
            out[tgt.id] = value.value
    return out


def _str_of(node: ast.AST | None, strings: dict[str, str]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return strings.get(node.id)
    return None


def _collect_cli(tree: ast.Module, strings: dict[str, str], facts: FileFacts) -> None:
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and n.attr == "argv" and isinstance(n.value, ast.Name) and n.value.id == "sys":
            facts.cli_argv = True
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        if n.func.attr == "add_argument":
            flags = [_str_of(a, strings) for a in n.args]
            if not flags or any(f is None for f in flags):
                facts.cli_unread += 1
                continue
            help_text: str | None = ""
            for kw in n.keywords:
                if kw.arg == "help":
                    raw_help = _str_of(kw.value, strings)
                    help_text = None if raw_help is None else join_lines(raw_help.split("\n"))
            facts.cli_args["・".join(f for f in flags if f)] = help_text
        elif n.func.attr == "add_parser" and n.args:
            name = _str_of(n.args[0], strings)
            if name is None:
                facts.cli_unread += 1
            else:
                facts.cli_subcommands.add(name)


def _is_os_attr(node: ast.AST, attr: str) -> bool:
    return (isinstance(node, ast.Attribute) and node.attr == attr and isinstance(node.value, ast.Name)
            and node.value.id == "os")


def _collect_env(tree: ast.Module, strings: dict[str, str], facts: FileFacts) -> None:
    environ_names: set[str] = set()
    getenv_names: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module == "os" and n.level == 0:
            for a in n.names:
                if a.name == "environ":
                    environ_names.add(a.asname or a.name)
                elif a.name == "getenv":
                    getenv_names.add(a.asname or a.name)
        elif (isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
              and _is_os_attr(n.value, "environ")):
            environ_names.add(n.targets[0].id)

    def is_environ(x: ast.AST) -> bool:
        return _is_os_attr(x, "environ") or (isinstance(x, ast.Name) and x.id in environ_names)

    used: set[int] = set()  # 名前を読めた ``os.environ`` の節

    def note(name_node: ast.AST | None) -> None:
        name = _str_of(name_node, strings)
        if name is None:
            facts.env_unread += 1
        else:
            facts.env_names.add(name)

    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript) and is_environ(n.value):
            used.add(id(n.value))
            note(n.slice)
        elif isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute) and is_environ(f.value):
                used.add(id(f.value))
                if f.attr in ("get", "pop", "setdefault") and n.args:
                    note(n.args[0])
                elif f.attr not in ("get", "pop", "setdefault"):
                    facts.env_whole = True
            elif _is_os_attr(f, "getenv") or (isinstance(f, ast.Name) and f.id in getenv_names):
                note(n.args[0] if n.args else None)
        elif isinstance(n, ast.Compare) and len(n.comparators) == 1 and is_environ(n.comparators[0]):
            used.add(id(n.comparators[0]))
            note(n.left)
        elif isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            if is_environ(n.value):
                used.add(id(n.value))  # 別名を作るだけ
    for n in ast.walk(tree):
        if _is_os_attr(n, "environ") and id(n) not in used:
            facts.env_whole = True
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and _PROJECT_ENV.match(n.value):
            facts.env_names.add(n.value)


# ---------------------------------------------------------------- 決定の ID
_R_ID = re.compile(r"(?<![A-Za-z0-9-])R-\d+[a-z]?(?![A-Za-z0-9])")
_D_ID = re.compile(r"(?<![A-Za-z0-9-])D-\d+(?![A-Za-z0-9])")
#: 第 N は 3 桁以上だけ拾う(2 桁以下はコードでは第 1 期・第 2 波・第 1 陣・第 31 表のような序数がほとんど)。
#: 3 桁でも後ろがこの語か ``-数字`` なら devlog の番号でない。``段``・``層`` は入れない(``第340 段 2``・``第170 層2`` は devlog の番号)。
_COUNTER_WORDS = "期部回章節条号表種位次項版週日月年図案世代者類陣波弾批系"
_DAI = re.compile(r"第\s*([1-9]\d{2,})(?![\d-])(?!\s*[" + _COUNTER_WORDS + r"])")
_DECISION_TAIL = r"§?[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*"
_SP = r"[ \t\u3000]*"
#: 項目の番号 ``#N`` は別の文書の中の番号なので、前の接頭につながるものだけを拾う。続きの ``・#8``・``〜#18`` も同じ接頭につなぐ。
_ITEM_TAIL = (_SP + r"[(\uff08]?" + _SP + r"#(?P<num>[1-9]\d{0,3})"
              r"(?P<more>(?:" + _SP + r"[・、,〜~\uff5e]" + _SP + r"#[1-9]\d{0,3})*)(?![\w-])")
_ITEM_HEADS_FIXED = (
    r"(?<![A-Za-z0-9-])(?P<r>R-\d+[a-z]?)(?:" + _SP + r"§" + _SP + r"(?P<rsec>\d+(?:-\d+)*))?"
    r"|(?<![A-Za-z0-9-])(?P<d>D-\d+)"
    r"|第\s*(?P<dai>[1-9]\d{2,})")


@dataclass(frozen=True)
class DecisionRegexes:
    slash: re.Pattern[str] | None
    section: re.Pattern[str] | None
    bare: re.Pattern[str] | None
    item: re.Pattern[str]


def decision_regexes(prefixes: list[str]) -> DecisionRegexes:
    """決定の一覧の接頭から正規表現を作る(``接頭/ID``・``接頭 §番号``・接頭だけ・接頭につながる ``#N``)。"""
    if not prefixes:
        return DecisionRegexes(None, None, None, re.compile(r"(?:" + _ITEM_HEADS_FIXED + r")" + _ITEM_TAIL))
    alt = "|".join(re.escape(p) for p in sorted(prefixes, key=lambda s: (-len(s), s)))
    before = r"(?<![\d\-/.:A-Za-z])"
    head = before + r"(" + alt + r")"
    item_head = (before + r"(?P<dec>" + alt + r")(?:/(?P<dectail>" + _DECISION_TAIL + r")|" + _SP + r"§" + _SP
                 + r"(?P<decsec>\d+(?:-\d+)*))?")
    return DecisionRegexes(
        slash=re.compile(head + r"/(" + _DECISION_TAIL + r")"),
        section=re.compile(head + r"\s*§\s*(\d+(?:-\d+)*)"),
        bare=re.compile(head + r"(?![\w\-/])"),
        item=re.compile(r"(?:" + item_head + r"|" + _ITEM_HEADS_FIXED + r")" + _ITEM_TAIL),
    )


def _item_ids(text: str, item: re.Pattern[str]) -> set[str]:
    """前の接頭につながる ``#N``(``11-02r/§1 #7``・``R-116 §1-4 #46``・``第 275 #4``)。"""
    out: set[str] = set()
    for m in item.finditer(text):
        g = m.groupdict()
        if g.get("dec"):
            head = g["dec"]
            if g.get("dectail"):
                head += f"/{g['dectail']}"
            elif g.get("decsec"):
                head += f"/§{g['decsec']}"
        elif g.get("r"):
            head = g["r"] + (f" §{g['rsec']}" if g.get("rsec") else "")
        elif g.get("d"):
            head = g["d"]
        else:
            head = f"第 {int(g['dai'])}"
        for num in [g["num"], *re.findall(r"#(\d+)", g["more"])]:
            out.add(f"{head} #{num}")
    return out


def decision_ids(text: str, regexes: DecisionRegexes) -> set[str]:
    out = _item_ids(text, regexes.item)
    if regexes.slash is not None and regexes.section is not None and regexes.bare is not None:
        slash, section, bare = regexes.slash, regexes.section, regexes.bare
        for m in slash.finditer(text):
            out.add(f"{m.group(1)}/{m.group(2)}")
        text = slash.sub(" ", text)
        for m in section.finditer(text):
            out.add(f"{m.group(1)}/§{m.group(2)}")
        text = section.sub(" ", text)
        for m in bare.finditer(text):
            out.add(m.group(1))
    out.update(m.group(0) for m in _R_ID.finditer(text))
    out.update(m.group(0) for m in _D_ID.finditer(text))
    out.update(f"第 {int(m.group(1))}" for m in _DAI.finditer(text))
    return out


def _natural(s: str) -> list[tuple[int, int, str]]:
    return [(0, int(p), "") if p.isdigit() else (1, 0, p) for p in re.split(r"(\d+)", s) if p]


def decision_sort_key(id_text: str) -> tuple[int, list[tuple[int, int, str]], str]:
    """並び: 指示書と回答 → R- → D- → 第 N。数は数の順(末尾の ``id_text`` は同じ重みの字の並びの決め手)。"""
    if id_text.startswith("R-"):
        kind = 1
    elif id_text.startswith("D-"):
        kind = 2
    elif id_text.startswith("第"):
        kind = 3
    else:
        kind = 0
    return kind, _natural(id_text), id_text


# ---------------------------------------------------------------- 1 ファイル
def read_python(rel: str, raw: bytes, regexes: DecisionRegexes) -> FileFacts:
    """Python のファイル 1 本の事実(構文が読めなければ ``error`` に理由だけを入れる)。"""
    facts = FileFacts(rel=rel)
    try:
        text = normalized_text(raw)
    except UnicodeDecodeError:
        facts.error = "UTF-8 で読めない"
        return facts
    facts.decision_ids = decision_ids(text, regexes)
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError) as e:
        facts.error = f"構文を読めない({type(e).__name__})"
        return facts
    facts.summary = first_paragraph(ast.get_docstring(tree))
    facts.public = _public_of(tree)
    facts.imports = _imports_of(tree)
    facts.path_mentions, facts.syspath_dirs, facts.syspath_unread = _path_facts(tree, rel)
    strings = _module_strings(tree)
    _collect_cli(tree, strings, facts)
    _collect_env(tree, strings, facts)
    return facts


# ---------------------------------------------------------------- 内部の import を解く
class ModuleIndex:
    """リポの中の Python のファイルの一覧から、import の先のファイルを解く。"""

    def __init__(self, rels: list[str], facts: dict[str, FileFacts]) -> None:
        self.files = set(rels)
        self.facts = facts
        self.dirs: set[str] = {""}
        for r in rels:
            parts = r.split("/")[:-1]
            for i in range(1, len(parts) + 1):
                self.dirs.add("/".join(parts[:i]))
        self._dirs_cache: dict[str, list[str]] = {}
        self._by_name: dict[str, list[str]] = {}  # tests と tools の素の名前 → ファイル(``foo.py``・``foo/__init__.py``)
        for r in sorted(rels):
            if r.startswith(("tests/", "tools/")):
                stem = r.rsplit("/", 1)[-1].removesuffix(".py")
                if stem == "__init__":
                    stem = r.rsplit("/", 2)[-2]
                if stem != "conftest":
                    self._by_name.setdefault(stem, []).append(r)

    def _lookup(self, base: str) -> str | None:
        if f"{base}.py" in self.files:
            return f"{base}.py"
        if f"{base}/__init__.py" in self.files:
            return f"{base}/__init__.py"
        return None

    def _search_dirs(self, importer: str) -> list[str]:
        """素の名前を探す場所(tests と tools だけ)。

        同じディレクトリ・パッケージの中ならいちばん外のパッケージの 1 つ上・そのファイルと祖先の conftest と囲むパッケージの
        ``__init__.py`` が ``sys.path`` に足す所・そこから import する内部モジュールが足す所(import の時に ``sys.path`` が
        増えるので推移的に)。
        """
        if importer.startswith(SKIP_ROOTS_FOR_SIBLING):
            return []
        cached = self._dirs_cache.get(importer)
        if cached is not None:
            return cached
        here = importer.rsplit("/", 1)[0] if "/" in importer else ""
        dirs = [here]
        sources = [importer]
        parts = here.split("/") if here else []
        for i in range(len(parts), 0, -1):
            sources.append("/".join(parts[:i]) + "/conftest.py")
        outer = here
        while outer and f"{outer}/__init__.py" in self.files:  # 中のモジュールを import する前に __init__ が走る
            sources.append(f"{outer}/__init__.py")
            outer = outer.rsplit("/", 1)[0] if "/" in outer else ""
        if outer != here:
            dirs.append(outer)  # パッケージとして import できているなら、その外側は sys.path にある
        seen = {s for s in sources if s in self.facts}
        for s in sources:
            f = self.facts.get(s)
            if f is not None:
                dirs.extend(sorted(d for d in f.syspath_dirs if d in self.dirs and d not in dirs))
        grew = True
        while grew:  # 足す所が増えれば解ける import も増える(ファイルの数で止まる)
            grew = False
            for s in sorted(seen):
                own = s.rsplit("/", 1)[0] if "/" in s else ""
                for ref in self.facts[s].imports:
                    for t in self._resolve_in(s, ref, [own, *dirs]):
                        if t in seen or t.startswith(SKIP_ROOTS_FOR_SIBLING):
                            continue
                        seen.add(t)
                        grew = True
                        dirs.extend(sorted(d for d in self.facts[t].syspath_dirs if d in self.dirs and d not in dirs))
        self._dirs_cache[importer] = dirs
        return dirs

    def _from_base(self, base: str, names: tuple[str, ...]) -> set[str]:
        hits: set[str] = set()
        whole = self._lookup(base)
        for name in names:
            sub = self._lookup(f"{base}/{name}") if name != "*" else None
            if sub is not None:
                hits.add(sub)
            elif whole is not None:
                hits.add(whole)
        if not names and whole is not None:
            hits.add(whole)
        return hits

    def _resolve_in(self, importer: str, ref: ImportRef, search: list[str]) -> set[str]:
        path = ref.module.replace(".", "/")
        if ref.level > 0:
            parts = importer.split("/")[:-1]
            if ref.level - 1 > len(parts):
                return set()
            parts = parts[: len(parts) - (ref.level - 1)]
            base = "/".join(parts + ([path] if path else []))
            return self._from_base(base, ref.names)
        top = path.split("/", 1)[0]
        base = path if top in _ROOT_PACKAGES else f"src/{path}"
        hits = self._from_base(base, ref.names)
        if hits:
            return hits
        for d in search:
            hits = self._from_base(f"{d}/{path}" if d else path, ref.names)
            if hits:
                return hits
        return set()

    def resolve(self, importer: str, ref: ImportRef) -> set[str]:
        return self._resolve_in(importer, ref, self._search_dirs(importer))

    def unresolved_bare(self, importer: str) -> dict[str, str]:
        """解けなかった素の import のうち、tests と tools に同じ名のファイルが 1 つだけあるもの(名 → そのファイル)。"""
        if importer.startswith(SKIP_ROOTS_FOR_SIBLING):
            return {}
        out: dict[str, str] = {}
        for ref in self.facts[importer].imports:
            top = ref.module.split(".", 1)[0]
            if ref.level or not top or top in sys.stdlib_module_names:
                continue
            found = self._by_name.get(top, [])
            if len(found) == 1 and found[0] != importer and not self.resolve(importer, ref):
                out[top] = found[0]
        return out

    def mention_targets(self, importer: str) -> set[str]:
        """試験が道筋で指すファイル(リポの道筋そのまま・``src/shibuya/`` の下の道筋)。"""
        f = self.facts.get(importer)
        if f is None:
            return set()
        hits: set[str] = set()
        for p in f.path_mentions:
            for cand in (p, f"src/shibuya/{p}"):
                if cand in self.files and cand != importer:
                    hits.add(cand)
        return hits


def module_label(rel: str) -> str:
    """src の下は import の名前(``shibuya.engine.resolve``)、ほかはリポの道筋。"""
    if rel.startswith("src/"):
        body = rel[len("src/"):].removesuffix(".py").removesuffix("/__init__")
        return body.replace("/", ".")
    return rel
