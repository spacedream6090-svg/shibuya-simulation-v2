# -*- coding: utf-8 -*-
"""状態台帳の持ち主の行と系の書きの許可を、ソースの AST だけから読む(対象のコードは import も実行もしない)。

読む場所(``src/shibuya`` の下):

- ``engine/state_ledger.py``: 行の表(``_SOA``・``_EXT`` の ``_s(…)``・``_o(…)``・``LedgerRow(…)``)と持ち主の表
  (``OWNER_CLASSES``・``OWNER_ALT_CLASSES``)。外の状態の行の持ち主 = 道筋の最も長い前方が ``OWNER_CLASSES`` にある所。
- ``engine/state_ledger_ast.py``: SoA の列の宣言のファイル(``DECL_FILES``)と書きの関数の名(``WRITE_FUNCS``)。
  SoA の行の持ち主 = 宣言のファイル(cells・pois は world の宣言)。
- ``engine/systems/table.py``: 系の表 ``SYSTEMS`` の ``make(…)``。
- ``engine/systems/allow.py`` と ``engine/resolve.py``: ``writes.soa`` の静的な閉包。``allow.index`` と ``writes_for_ops``
  の規則を AST の上でなぞる(import しないので写しになる=試験 ``tests/tools/test_repo_guide.py`` が実物と比べる)。

読めない所は ``Permits.problems`` に書き、推測で埋めない。
"""
from __future__ import annotations

import ast
import fnmatch
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from guide_facts import normalized_text

SRC = "src/shibuya"


def _src_file(module: str) -> str:
    """モジュールの名(``shibuya.…``)→ リポの根からの道筋(``src/shibuya/….py``)。対象のコードは import しない。

    〔移す段 4 の下ごしらえ〕道は f 文字列で持たない(移す道具 tools/pkgmove は f 文字列の部分を書き換えない)。モジュールの名は
    ``shibuya.`` で始まる点の道なので、移す道具が許可の一覧で拾って新しい置き場の名へ書き換える。"""
    return "src/" + module.replace(".", "/") + ".py"


LEDGER_FILE = _src_file("shibuya.runtime.state.ledger")
LEDGER_AST_FILE = _src_file("shibuya.runtime.state.ledger_ast")
TABLE_FILE = _src_file("shibuya.runtime.systems.table")
ALLOW_FILE = _src_file("shibuya.runtime.systems.allow")
RESOLVE_FILE = _src_file("shibuya.engine.resolve")


class Unread(Exception):
    """AST から値を決められない。"""


# ---------------------------------------------------------------- 値の静的な評価(定数と f 文字列と単純な内包だけ)
def static_eval(node: ast.AST, env: dict[str, object]) -> object:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise Unread(node.id)
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        out: list[object] = []
        for e in node.elts:
            if isinstance(e, ast.Starred):
                out.extend(_iterable(static_eval(e.value, env)))
            else:
                out.append(static_eval(e, env))
        if isinstance(node, ast.List):
            return out
        return frozenset(out) if isinstance(node, ast.Set) else tuple(out)
    if isinstance(node, ast.Dict):
        d: dict[object, object] = {}
        for k, v in zip(node.keys, node.values):
            if k is None:
                sub = static_eval(v, env)
                if not isinstance(sub, dict):
                    raise Unread("** の中身")
                d.update(sub)
            else:
                d[static_eval(k, env)] = static_eval(v, env)
        return d
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return static_eval(node.left, env) + static_eval(node.right, env)  # type: ignore[operator]
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for v in node.values:
            if isinstance(v, ast.Constant):
                parts.append(str(v.value))
            elif isinstance(v, ast.FormattedValue) and v.format_spec is None and v.conversion == -1:
                parts.append(str(static_eval(v.value, env)))
            else:
                raise Unread("f 文字列の書式")
        return "".join(parts)
    if isinstance(node, (ast.GeneratorExp, ast.ListComp)):
        if len(node.generators) != 1 or node.generators[0].ifs or not isinstance(node.generators[0].target, ast.Name):
            raise Unread("内包の形")
        gen = node.generators[0]
        name = gen.target.id
        return tuple(static_eval(node.elt, {**env, name: x}) for x in _iterable(static_eval(gen.iter, env)))
    if isinstance(node, ast.Call):
        f = node.func
        fname = f.id if isinstance(f, ast.Name) else ""
        if fname in ("tuple", "frozenset", "set", "list", "MappingProxyType") and len(node.args) == 1 and not node.keywords:
            v = static_eval(node.args[0], env)
            if fname == "MappingProxyType":
                return v
            return {"tuple": tuple, "frozenset": frozenset, "set": frozenset, "list": list}[fname](_iterable(v))
    raise Unread(type(node).__name__)


def _iterable(v: object) -> tuple[object, ...]:
    if isinstance(v, (tuple, list, frozenset)):
        return tuple(v)
    raise Unread("繰り返せない値")


def module_constants(tree: ast.Module) -> dict[str, object]:
    """頂上の代入のうち静的に決まるものだけ(順に。決まらない代入は飛ばす)。"""
    env: dict[str, object] = {}
    for n in tree.body:
        if isinstance(n, ast.Assign):
            for tgt in n.targets:
                try:
                    v = static_eval(n.value, env)
                except Unread:
                    continue
                if isinstance(tgt, ast.Name):
                    env[tgt.id] = v
                elif isinstance(tgt, ast.Tuple) and isinstance(v, tuple) and len(tgt.elts) == len(v):
                    for t, x in zip(tgt.elts, v):
                        if isinstance(t, ast.Name):
                            env[t.id] = x
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None:
            try:
                env[n.target.id] = static_eval(n.value, env)
            except Unread:
                continue
    return env


def _parse(root: Path, rel: str) -> ast.Module | None:
    p = root / rel
    if not p.is_file():
        return None
    return ast.parse(normalized_text(p.read_bytes()))


def read_constant(path: Path, name: str) -> object:
    """1 ファイルの頂上の定数を AST で読む(無ければ ``KeyError``)。"""
    return module_constants(ast.parse(normalized_text(path.read_bytes())))[name]


# ---------------------------------------------------------------- 台帳
@dataclass(frozen=True)
class Row:
    key: str
    name: str
    place: str
    behavior: str
    restore: str
    arm: str
    dead: bool
    items: tuple[str, ...]


@dataclass(frozen=True)
class System:
    name: str
    group: str
    timing: str
    fn_file: str
    fn_name: str
    resolve_ops: tuple[str, ...]
    soa: tuple[str, ...]
    paths: tuple[str, ...]
    scratch: tuple[str, ...]
    buffers: tuple[str, ...]
    tally: tuple[str, ...]
    when: str
    calls_llm: str


@dataclass
class Permits:
    rows: list[Row] = field(default_factory=list)
    owners: dict[str, tuple[str, str]] = field(default_factory=dict)  # 持ち主の道筋 → (ファイル, クラス)
    alts: dict[str, tuple[tuple[str, str], ...]] = field(default_factory=dict)
    soa_files: dict[str, str] = field(default_factory=dict)  # 置き場 → 宣言のファイル
    systems: list[System] = field(default_factory=list)
    direct: dict[str, frozenset[str]] = field(default_factory=dict)
    op_systems: dict[str, list[str]] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)

    def owner_of(self, item: str) -> str | None:
        parts = item.split(".")
        for i in range(len(parts), 0, -1):
            prefix = ".".join(parts[:i])
            if prefix in self.owners:
                return prefix
        return None

    def writers_of_item(self, key: str, item: str) -> set[str]:
        """宣言 ``writes.paths`` の照合(``systems.spec.path_allowed`` と同じ規則=一致か、``*`` を含む型の照合)。"""
        target = f"{key}:{item}"
        return {s.name for s in self.systems
                if target in s.paths or any(fnmatch.fnmatchcase(target, p) for p in s.paths if "*" in p)}

    def writers_of_soa(self, key: str) -> set[str]:
        return {s.name for s in self.systems if key in s.soa}

    def unowned_rows(self) -> list[tuple[Row, tuple[str, ...]]]:
        """外の状態の行のうち、持ち主を引けない道筋を持つ行(道筋なしの行を含む)。"""
        out: list[tuple[Row, tuple[str, ...]]] = []
        for r in self.rows:
            if r.place in self.soa_files:
                continue
            miss = tuple(i for i in r.items if self.owner_of(i) is None)
            if miss or not r.items:
                out.append((r, miss))
        return out


def _bind(call: ast.Call, params: list[str]) -> dict[str, ast.AST]:
    bound = dict(zip(params, call.args))
    for kw in call.keywords:
        if kw.arg is not None:
            bound[kw.arg] = kw.value
    return bound


def _params_of_def(tree: ast.Module, name: str) -> list[str]:
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return [a.arg for a in n.args.posonlyargs + n.args.args]
    return []


def _fields_of_class(tree: ast.Module, name: str) -> list[str]:
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and n.name == name:
            return [s.target.id for s in n.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)]
    return []


def _opt(bound: dict[str, ast.AST], name: str, env: dict[str, object], default: object) -> object:
    return static_eval(bound[name], env) if name in bound else default


def _row_of_call(call: ast.Call, env, s_params, o_params, row_fields) -> Row:
    f = call.func.id if isinstance(call.func, ast.Name) else ""
    if f == "_s":
        b = _bind(call, s_params)
        place, name = static_eval(b["place"], env), static_eval(b["name"], env)
        return Row(key=f"{place}.{name}", name=str(name), place=str(place), behavior=str(static_eval(b["behavior"], env)),
                   restore=str(static_eval(b["restore"], env)), arm="", dead=bool(_opt(b, "dead", env, False)), items=())
    if f == "_o":
        b = _bind(call, o_params)
        external = env.get("EXTERNAL", "external")
        return Row(key=f"O{static_eval(b['n'], env)}", name=str(static_eval(b["name"], env)), place=str(external),
                   behavior=str(static_eval(b["behavior"], env)), restore=str(static_eval(b["restore"], env)),
                   arm="", dead=False, items=tuple(static_eval(b["items"], env)))  # type: ignore[arg-type]
    if f == "LedgerRow":
        b = _bind(call, row_fields)
        return Row(key=str(static_eval(b["key"], env)), name=str(static_eval(b["name"], env)),
                   place=str(static_eval(b["place"], env)), behavior=str(static_eval(b["behavior"], env)),
                   restore=str(static_eval(b["restore"], env)), arm=str(_opt(b, "arm", env, "")),
                   dead=bool(_opt(b, "dead", env, False)), items=tuple(_opt(b, "items", env, ())))  # type: ignore[arg-type]
    raise Unread(f"行の形 {f or type(call.func).__name__}")


def _read_ledger(root: Path, out: Permits) -> None:
    tree = _parse(root, LEDGER_FILE)
    if tree is None:
        out.problems.append(f"{LEDGER_FILE} が無い(状態台帳の行を載せない)")
        return
    env = module_constants(tree)
    s_params, o_params = _params_of_def(tree, "_s"), _params_of_def(tree, "_o")
    row_fields = _fields_of_class(tree, "LedgerRow")
    tables: list[ast.AST] = []
    for n in tree.body:
        tgt = n.target if isinstance(n, ast.AnnAssign) else (n.targets[0] if isinstance(n, ast.Assign) else None)
        if isinstance(tgt, ast.Name) and tgt.id in ("_SOA", "_EXT") and getattr(n, "value", None) is not None:
            tables.append(n.value)
    if not tables:
        out.problems.append(f"{LEDGER_FILE} に行の表 _SOA・_EXT が見つからない")
    for t in tables:
        if not isinstance(t, ast.Tuple):
            out.problems.append(f"{LEDGER_FILE} の行の表が組の直書きでない(読まない)")
            continue
        for call in t.elts:
            if not isinstance(call, ast.Call):
                out.problems.append(f"{LEDGER_FILE} の行の表に呼び出しでない要素がある")
                continue
            try:
                out.rows.append(_row_of_call(call, env, s_params, o_params, row_fields))
            except (Unread, KeyError, TypeError) as e:
                out.problems.append(f"{LEDGER_FILE} の行を読めない({type(e).__name__}: {e})")
    owners = env.get("OWNER_CLASSES")
    alts = env.get("OWNER_ALT_CLASSES")
    if isinstance(owners, dict):
        out.owners = {str(k): (f"{SRC}/{v[0]}", str(v[1])) for k, v in owners.items()}
    else:
        out.problems.append(f"{LEDGER_FILE} の OWNER_CLASSES を読めない")
    if isinstance(alts, dict):
        out.alts = {str(k): tuple((f"{SRC}/{x[0]}", str(x[1])) for x in v) for k, v in alts.items()}


# ---------------------------------------------------------------- 書きの閉包(allow.index の規則を AST でなぞる)
def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    p: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for ch in ast.iter_child_nodes(node):
            p[ch] = node
    return p


def _is_write(node: ast.Attribute, par: dict, write_funcs: frozenset) -> bool:
    if isinstance(node.ctx, (ast.Store, ast.Del)):
        return True
    up = par.get(node)
    if isinstance(up, ast.Subscript) and up.value is node and isinstance(up.ctx, (ast.Store, ast.Del)):
        return True
    if isinstance(up, ast.AugAssign) and up.target is node:
        return True
    if isinstance(up, ast.Attribute) and up.value is node and up.attr == "fill":
        return True
    if isinstance(up, ast.Call):
        f = up.func
        fname = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        if up.args and up.args[0] is node and (fname == "at" or fname in write_funcs):
            return True
    if isinstance(up, ast.keyword) and up.arg == "out":
        return True
    return False


def _place_of(expr_text: str) -> str:
    if "pois" in expr_text:
        return "pois"
    if "cells" in expr_text:
        return "cells"
    if "pstate" in expr_text or "perception" in expr_text:
        return "perception"
    return "agents"


def _declared_columns(root: Path, decl_files: dict[str, str]) -> set[str]:
    names: set[str] = set()
    for rel in decl_files.values():
        tree = _parse(root, f"{SRC}/{rel}")
        if tree is None:
            continue
        for n in ast.walk(tree):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "declare" and n.args
                    and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)):
                names.add(n.args[0].value)
    return names


def _resolve_index(root: Path, out: Permits, decl_files: dict[str, str], write_funcs: frozenset):
    """``allow.index`` と同じ規則の (直接の書き, 辺)。"""
    tree = _parse(root, RESOLVE_FILE)
    allow_tree = _parse(root, ALLOW_FILE)
    if tree is None or allow_tree is None:
        out.problems.append(f"{RESOLVE_FILE} か {ALLOW_FILE} が無い(書きの閉包を作らない)")
        return {}, {}
    allow_env = module_constants(allow_tree)
    alias_writes = allow_env.get("ALIAS_WRITES", {})
    ports = allow_env.get("TRANSFER_PORTS_HOUSEHOLD", {})
    transfer_writes = allow_env.get("TRANSFER_WRITES", ())
    if not (isinstance(alias_writes, dict) and isinstance(ports, dict) and isinstance(transfer_writes, tuple)):
        out.problems.append(f"{ALLOW_FILE} の表を読めない")
        return {}, {}
    par = _parents(tree)
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    names = _declared_columns(root, decl_files)
    tables: dict[str, set[str]] = {}
    for n in tree.body:
        tgt = (n.targets[0] if isinstance(n, ast.Assign) and len(n.targets) == 1
               else (n.target if isinstance(n, ast.AnnAssign) else None))
        if isinstance(tgt, ast.Name) and getattr(n, "value", None) is not None:
            refs = {x.id for x in ast.walk(n.value) if isinstance(x, ast.Name) and (x.id in funcs or x.id in tables)}
            refs = set().union(*({r} if r in funcs else tables[r] for r in refs)) if refs else set()
            if refs:
                tables[tgt.id] = refs
    direct: dict[str, set[str]] = defaultdict(set)
    calls: dict[str, set[str]] = defaultdict(set)
    for fname, fn in funcs.items():
        for node in ast.walk(fn):
            if isinstance(node, ast.Attribute) and node.attr in names and _is_write(node, par, write_funcs):
                direct[fname].add(f"{_place_of(ast.unparse(node.value))}.{node.attr}")
            if isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del)):
                v = node.value
                if (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and v.func.attr == "field"
                        and v.args and isinstance(v.args[0], ast.Constant) and v.args[0].value in names):
                    direct[fname].add(f"{_place_of(ast.unparse(v.func.value))}.{v.args[0].value}")
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id in funcs and node.id != fname:
                    calls[fname].add(node.id)
                elif node.id in tables:
                    calls[fname] |= tables[node.id]
        alias: dict[str, str] = {}
        for node in ast.walk(fn):
            if (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                    and isinstance(node.value, ast.Attribute) and node.value.attr in names):
                alias[node.targets[0].id] = f"{_place_of(ast.unparse(node.value.value))}.{node.value.attr}"
        for node in ast.walk(fn):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "at"
                    and node.args and isinstance(node.args[0], ast.Name) and node.args[0].id in alias):
                direct[fname].add(alias[node.args[0].id])
            if isinstance(node, (ast.Assign, ast.AugAssign)):
                for x in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                    if isinstance(x, ast.Subscript) and isinstance(x.value, ast.Name) and x.value.id in alias:
                        direct[fname].add(alias[x.value.id])
        for node in ast.walk(fn):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ports):
                direct[fname] |= set(transfer_writes)
        if fname in alias_writes:
            direct[fname] |= set(alias_writes[fname][0])
    return {k: frozenset(v) for k, v in direct.items()}, {k: frozenset(v) for k, v in calls.items()}


def _closure_writes(ops: tuple[str, ...], direct, calls) -> tuple[str, ...]:
    seen: set[str] = set()
    stack = list(ops)
    writes: set[str] = set()
    while stack:
        f = stack.pop()
        if f in seen:
            continue
        seen.add(f)
        writes |= direct.get(f, frozenset())
        stack.extend(calls.get(f, ()))
    return tuple(sorted(writes))


# ---------------------------------------------------------------- 系の表
def _import_aliases(tree: ast.Module) -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    for n in tree.body:
        if isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            for a in n.names:
                out[a.asname or a.name] = (n.module, a.name)
    return out


def _fn_place(node: ast.AST | None, aliases: dict[str, tuple[str, str]]) -> tuple[str, str]:
    """系の関数の (ファイル, 関数の名)。分からなければ ``("", "")``。"""
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases:
        mod, sub = aliases[node.value.id]
        return f"src/{mod.replace('.', '/')}/{sub}.py", node.attr
    if isinstance(node, ast.Name):
        if node.id in aliases:
            mod, sub = aliases[node.id]
            return f"src/{mod.replace('.', '/')}.py", sub
        return TABLE_FILE, node.id
    return "", ""


def _split_names(v: object) -> tuple[str, ...]:
    if isinstance(v, str):
        return tuple(sorted(set(v.split())))
    return tuple(sorted(set(_iterable(v))))  # type: ignore[arg-type]


def _read_systems(root: Path, out: Permits, direct, calls) -> None:
    tree = _parse(root, TABLE_FILE)
    if tree is None:
        out.problems.append(f"{TABLE_FILE} が無い(書きの許可を載せない)")
        return
    env = module_constants(tree)
    aliases = _import_aliases(tree)
    table = None
    for n in tree.body:
        tgt = n.target if isinstance(n, ast.AnnAssign) else (n.targets[0] if isinstance(n, ast.Assign) else None)
        if isinstance(tgt, ast.Name) and tgt.id == "SYSTEMS":
            table = getattr(n, "value", None)
    if not isinstance(table, ast.Tuple):
        out.problems.append(f"{TABLE_FILE} の SYSTEMS が組の直書きでない(読まない)")
        return
    positional = ["name", "group", "timing", "fn"]
    for call in table.elts:
        try:
            if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "make"):
                raise Unread("make でない要素")
            b = _bind(call, positional)
            ops = _split_names(_opt(b, "resolve_ops", env, ()))
            fn_file, fn_name = _fn_place(b.get("fn"), aliases)
            out.systems.append(System(
                name=str(static_eval(b["name"], env)), group=str(static_eval(b["group"], env)),
                timing=str(static_eval(b["timing"], env)), fn_file=fn_file, fn_name=fn_name, resolve_ops=ops,
                soa=_closure_writes(ops, direct, calls), paths=_split_names(_opt(b, "paths", env, ())),
                scratch=_split_names(_opt(b, "scratch_w", env, ())), buffers=_split_names(_opt(b, "buffers_w", env, ())),
                tally=_split_names(_opt(b, "tally", env, ())), when=str(_opt(b, "when", env, "")),
                calls_llm=str(_opt(b, "calls_llm", env, "")),
            ))
        except (Unread, KeyError, TypeError) as e:
            out.problems.append(f"{TABLE_FILE} の系を読めない({type(e).__name__}: {e})")
    for s in out.systems:
        for op in s.resolve_ops:
            out.op_systems.setdefault(op, []).append(s.name)
    for op in out.op_systems:
        out.op_systems[op].sort()


def read_permits(root: Path) -> Permits:
    out = Permits()
    _read_ledger(root, out)
    ast_tree = _parse(root, LEDGER_AST_FILE)
    decl_files: dict[str, str] = {}
    write_funcs: frozenset = frozenset()
    if ast_tree is None:
        out.problems.append(f"{LEDGER_AST_FILE} が無い(SoA の宣言のファイルを引かない)")
    else:
        env = module_constants(ast_tree)
        d = env.get("DECL_FILES")
        w = env.get("WRITE_FUNCS")
        if isinstance(d, dict):
            decl_files = {str(k): str(v) for k, v in d.items()}
        else:
            out.problems.append(f"{LEDGER_AST_FILE} の DECL_FILES を読めない")
        if isinstance(w, frozenset):
            write_funcs = w
        else:
            out.problems.append(f"{LEDGER_AST_FILE} の WRITE_FUNCS を読めない")
    for group, rel in decl_files.items():
        places = ("cells", "pois") if group == "world" else (group,)
        for p in places:
            out.soa_files[p] = f"{SRC}/{rel}"
    direct, calls = _resolve_index(root, out, decl_files, write_funcs)
    out.direct = direct
    _read_systems(root, out, direct, calls)
    return out
