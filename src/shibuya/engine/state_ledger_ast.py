"""追加 C の静的な検査: SoA の列ごとの読み手を AST で数え、状態台帳の軸 1 と食い違えば知らせる(10b)。

試作 ``docs/bench/analysis/wallbounce-1003/10b/soa_readers_ast.py`` を元にした(数え方の規則は同じ。実行役の
自前の構成=**未リサーチ(expedient)**):

- 列名は ``agents/state.py``・``world/state.py``・``perception/state.py`` の ``declare("名前", ...)`` から AST で取る。
- 走査は ``src/shibuya`` 全体(``build/`` を除く。``engine/`` だけでは ``world/``・``perception/`` の読み手を
  見落とす=材料 §2-4)。
- 属性 ``X.列名`` を書き(代入の左辺・``X.c[...] =``・``np.*.at(X.c, ...)``・``X.c.fill``・``out=X.c``)と読みに分ける。
  ``X.c.dtype`` などの型の参照と、同じ列への代入の右辺の読み(自己更新)は読みから外す。
- 文字列は ``field("c")``(``f = r.field`` の別名も)・``getattr(r, "c")``・``arrays["c"]`` の形を読みとする。
- 名前の表を回す読み(``for v, sf in INTERO_VARS: r.field(sf)``)は、頂上の文字列の表を解決して表の中の全列の
  読みに数える。ループの対象が文字列の組の**直書き**(``for a, b in (("hunger", ...), ...)``)でも同じ。
  解決できない ``field(変数)`` の読みと、SoA らしい持ち主への ``getattr(持ち主, 変数)``(検収 2-5 (i))は
  ``unresolved`` に場所を出す。``X.arrays.get("c")``・``operator.attrgetter("c")`` の文字列も読みに数える。
  自己更新は「左辺と同じ列の右辺の読み」だけを外す(組の代入は要素を対にして見る)。
- **strict** = 属性の手前の式が SoA を指していそうなもの(末尾が ``registry``・``r``・``agents``・``cells`` など)だけ。
  **loose** = 手前の式を問わない全部の読み(同じ名前の別物も入る)。

検査(``check``):

1. 軸 1 が ``behavior`` の列は strict の読み手が 1 つ以上(0 なら死蔵の見落とし)。
2. 軸 1 が ``no``/``diag`` の列は loose の読み手が 0。ただし行の ``ast_allow``(場所の文字列と根拠)に載る読みは許す。
3. 解決できない ``field(変数)`` の読みは ``UNRESOLVED_ALLOW`` に載っていること。
4. ``ast_allow`` と ``UNRESOLVED_ALLOW`` の各項が実際にどこかの読みに当たること(古くなった許可を残さない)。
5. 同じ名前の列(``agents.cell`` と ``pois.cell`` など)は軸 1 が同じであること(AST では区別できないため)。
6. 宣言の列の集合と台帳の SoA の行の集合が一致すること。

限界: 配列を関数に渡した先の読み・``getattr(obj, 変数)``・描画の文字列の組み立ての中の読みは静的には
追い切れない。だから揺らし試験(動的・``tests/engine/test_state_ledger_10b.py`` の T5)と組にする。
"""

from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from shibuya.engine import state_ledger as SL

DECL_FILES: dict[str, str] = {
    "agents": "agents/state.py",
    "world": "world/state.py",
    "perception": "perception/state.py",
}
SOA_BASE_TAILS = frozenset({
    "registry", "r", "R", "reg", "agents", "cells", "pois", "pstate", "ps", "state",
    "rows", "v", "f", "A", "st", "s", "ag", "world_cells", "world_pois",
})
WRITE_FUNCS = frozenset({"copyto", "put", "place", "putmask"})
META_ATTRS = frozenset({"dtype", "shape", "size", "ndim", "itemsize", "nbytes"})

#: 解決できない ``field(変数)`` の読みのうち許すもの(場所の文字列と根拠)。
UNRESOLVED_ALLOW: tuple[SL.AstAllow, ...] = (
    SL.AstAllow("engine/run.py", "old = np.asarray(r.field(c.stage_field))",
                "内受容の段の跨ぎの診断の数え(_count_intero_crossings)。読むのは段の 3 列(どれも behavior)"),
    SL.AstAllow("agents/state.py", 'return self.__dict__["registry"].field(name)',
                "AgentState.__getattr__ の転送。読み手は呼び手の側の属性の読みとして数える"),
    SL.AstAllow("perception/state.py", 'return self.__dict__["registry"].field(name)',
                "PerceptionState.__getattr__ の転送。同上"),
    SL.AstAllow("engine/state_hashes.py", "_feed(f, getattr(v, fl.name), depth + 1, ordered)",
                "ハッシュの直列化の書き手が dataclass の欄を読む(SoA の列ではない・状態を読んで挙動を決めない)"),
    SL.AstAllow("engine/state_codec.py", "out[s] = getattr(v, s)",
                "10f: 状態のファイルの書き手が値のクラスの __slots__ の属性を読む(SoA の列ではない・挙動を決めない)"),
)


@dataclass(frozen=True)
class Site:
    """読みの場所(``path`` は ``src/shibuya`` からの相対・``text`` はその行の文字列)。"""

    path: str
    line: int
    text: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}"


@dataclass
class ScanResult:
    #: 列名 → strict の読み(属性・文字列・名前の表)。
    strict: dict[str, list[Site]] = field(default_factory=lambda: defaultdict(list))
    #: 列名 → loose の読み(手前の式を問わない)。
    loose: dict[str, list[Site]] = field(default_factory=lambda: defaultdict(list))
    #: 解決できない ``field(変数)`` の読み。
    unresolved: list[Site] = field(default_factory=list)
    #: 宣言: 置き場 → 列名の宣言順。
    declared: dict[str, list[str]] = field(default_factory=dict)
    files: int = 0


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    p: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for ch in ast.iter_child_nodes(node):
            p[ch] = node
    return p


def _target_names(stmt: ast.AST) -> set[str]:
    tg: list[ast.AST] = []
    if isinstance(stmt, ast.Assign):
        tg = list(stmt.targets)
    elif isinstance(stmt, (ast.AugAssign, ast.AnnAssign)):
        tg = [stmt.target]
    out: set[str] = set()
    for t in tg:
        for n in ast.walk(t):
            if isinstance(n, ast.Attribute):
                out.add(n.attr)
    return out


def _contains(tree: ast.AST, node: ast.AST) -> bool:
    return any(n is node for n in ast.walk(tree))


def _attr_names(tree: ast.AST) -> set[str]:
    return {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}


def _is_self_update(node: ast.Attribute, st: ast.AST | None) -> bool:
    """``node``(列 c の読み)が「左辺と同じ列 c の右辺の読み」=自己更新か(検収 2-5 (iv))。

    文単位ではなく、組の代入は左辺と右辺の要素を対にして見る
    (``r.money[a], r.fail_streak[a] = r.money[a] - r.fail_streak[a], 0`` の ``fail_streak`` は自己更新ではない)。
    左辺の中(添字)の読みは、その左辺が同じ列を書くときだけ自己更新。
    """
    c = node.attr
    if isinstance(st, (ast.AugAssign, ast.AnnAssign)):
        return st.target is not None and c in _attr_names(st.target)
    if not isinstance(st, ast.Assign):
        return False
    for tg in st.targets:
        if _contains(tg, node):
            return c in _attr_names(tg)
    val = st.value
    for tg in st.targets:
        if (isinstance(tg, (ast.Tuple, ast.List)) and isinstance(val, (ast.Tuple, ast.List))
                and len(tg.elts) == len(val.elts)):
            for te, ve in zip(tg.elts, val.elts):
                if _contains(ve, node) and c in _attr_names(te):
                    return True
        elif c in _attr_names(tg):
            return True
    return False


def _soa_like(expr: ast.AST) -> bool:
    return _base_tail(expr) in SOA_BASE_TAILS or "registry" in ast.unparse(expr)


def _enclosing_stmt(node: ast.AST, par: dict) -> ast.AST | None:
    cur = node
    while cur in par:
        cur = par[cur]
        if isinstance(cur, ast.stmt):
            return cur
    return None


def _is_write(node: ast.Attribute, par: dict) -> bool:
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
        if up.args and up.args[0] is node and (fname == "at" or fname in WRITE_FUNCS):
            return True
    if isinstance(up, ast.keyword) and up.arg == "out":
        return True
    return False


def _base_tail(expr: ast.AST) -> str:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    if isinstance(expr, ast.Call):
        return _base_tail(expr.func)
    return ""


def _const_strings(node: ast.AST) -> set[str] | None:
    """文字列だけの組(入れ子可)なら文字列の集合。そうでなければ None。"""
    if not isinstance(node, (ast.Tuple, ast.List)):
        return None
    ss: set[str] = set()
    for n in ast.walk(node):
        if n is node:
            continue
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            ss.add(n.value)
        elif not isinstance(n, (ast.Tuple, ast.List, ast.Load, ast.Constant)):
            return None
    return ss or None


def _str_tables(trees: Iterable[ast.Module]) -> dict[str, set[str]]:
    tabs: dict[str, set[str]] = {}
    for tree in trees:
        for node in tree.body:
            tgt = val = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                tgt, val = node.targets[0], node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                tgt, val = node.target, node.value
            if isinstance(tgt, ast.Name) and val is not None:
                ss = _const_strings(val)
                if ss:
                    tabs[tgt.id] = ss
    return tabs


def _dynamic_reads(node: ast.Call, par: dict, tabs: dict[str, set[str]], argi: int = 0) -> set[str]:
    """``field(変数)``(``getattr(持ち主, 変数)`` は ``argi=1``)の変数が、名前の表(か直書きの文字列の組)を
    回すループの変数なら、その文字列の集合。"""
    arg = node.args[argi]
    if not isinstance(arg, ast.Name):
        return set()
    cur: ast.AST = node
    while cur in par:
        cur = par[cur]
        iters: list[ast.AST] = []
        if isinstance(cur, ast.For):
            iters = [cur.iter]
        elif isinstance(cur, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            iters = [g.iter for g in cur.generators]
        for it in iters:
            lit = _const_strings(it)
            if lit:
                return lit
            for n in ast.walk(it):
                if isinstance(n, ast.Name) and n.id in tabs:
                    return tabs[n.id]
    return set()


def declared_columns(root: Path) -> dict[str, list[str]]:
    """``declare("名前", ...)`` の列名(置き場 ``agents``・``cells``・``pois``・``perception`` → 宣言順)。"""
    out: dict[str, list[str]] = {p: [] for p in SL.SOA_PLACES}
    for group, rel in DECL_FILES.items():
        tree = ast.parse((root / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "declare" and node.args
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                owner = ast.unparse(node.func.value)
                place = group if group != "world" else ("cells" if "cells" in owner else "pois")
                if node.args[0].value not in out[place]:
                    out[place].append(node.args[0].value)
    return out


def source_files(root: Path) -> list[Path]:
    """走査の対象(``src/shibuya`` 全体・``build/`` を除く)。"""
    return sorted(p for p in root.rglob("*.py") if "build" not in p.relative_to(root).parts)


def scan(root: Path, files: Iterable[Path] | None = None, names: Iterable[str] | None = None) -> ScanResult:
    """``root``(= ``src/shibuya``)の下を走査する。``files``・``names`` を渡せばその範囲だけ(試験用)。"""
    root = Path(root)
    res = ScanResult()
    try:
        res.declared = declared_columns(root)
    except FileNotFoundError:
        res.declared = {p: [] for p in SL.SOA_PLACES}
    nameset = set(names) if names is not None else {n for v in res.declared.values() for n in v}
    fl = list(files) if files is not None else source_files(root)
    res.files = len(fl)
    parsed: list[tuple[str, list[str], ast.Module]] = []
    for fp in fl:
        text = fp.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        parsed.append((fp.relative_to(root).as_posix(), text.split("\n"), tree))
    tabs = _str_tables(t for _, _, t in parsed)
    for rel, lines, tree in parsed:
        par = _parents(tree)

        def site(node: ast.AST) -> Site:
            ln = int(getattr(node, "lineno", 0))
            return Site(rel, ln, lines[ln - 1] if 0 < ln <= len(lines) else "")

        field_alias = {"field", "getattr"}
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Attribute)
                    and node.value.attr == "field"):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        field_alias.add(t.id)
        for node in ast.walk(tree):
            # ---- field(変数): 名前の表を回す読み ----
            if (isinstance(node, ast.Call) and node.args and not isinstance(node.args[0], ast.Constant)
                    and ((isinstance(node.func, ast.Attribute) and node.func.attr == "field")
                         or (isinstance(node.func, ast.Name) and node.func.id in field_alias
                             and node.func.id != "getattr"))):
                up = par.get(node)
                is_w = isinstance(up, ast.Subscript) and up.value is node and isinstance(up.ctx, (ast.Store, ast.Del))
                if is_w:
                    continue
                ss = _dynamic_reads(node, par, tabs)
                if not ss:
                    res.unresolved.append(site(node))
                    continue
                for nm in ss & nameset:
                    res.strict[nm].append(site(node))
                    res.loose[nm].append(site(node))
                continue
            # ---- getattr(持ち主, 変数)(検収 2-5 (i)): 名前の表で解決できなければ解決できない読み ----
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr"
                    and len(node.args) >= 2 and not isinstance(node.args[1], ast.Constant)
                    and _soa_like(node.args[0])):
                ss = _dynamic_reads(node, par, tabs, argi=1)
                if not ss:
                    res.unresolved.append(site(node))
                    continue
                for nm in ss & nameset:
                    res.strict[nm].append(site(node))
                    res.loose[nm].append(site(node))
                continue
            # ---- 属性 X.列名 ----
            if isinstance(node, ast.Attribute) and node.attr in nameset:
                if _is_write(node, par):
                    continue
                up = par.get(node)
                if isinstance(up, ast.Attribute) and up.value is node and up.attr in META_ATTRS:
                    continue
                st = _enclosing_stmt(node, par)
                if _is_self_update(node, st):
                    continue  # 自己更新(X.c[a] = X.c[a] + 1)
                s = site(node)
                res.loose[node.attr].append(s)
                tail = _base_tail(node.value)
                if tail in SOA_BASE_TAILS or "registry" in ast.unparse(node.value):
                    res.strict[node.attr].append(s)
                continue
            # ---- 文字列 "列名" ----
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in nameset:
                up = par.get(node)
                if isinstance(up, ast.Call):
                    f = up.func
                    fname = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
                    if fname == "declare":
                        continue
                    # 検収 2-5 (ii) ``X.arrays.get("c")``・(iii) ``operator.attrgetter("c")``
                    if ((fname == "get" and isinstance(f, ast.Attribute)
                         and ("arrays" in ast.unparse(f.value) or "registry" in ast.unparse(f.value)))
                            or fname == "attrgetter"):
                        res.strict[node.value].append(site(node))
                        res.loose[node.value].append(site(node))
                        continue
                    if fname in field_alias and node in up.args:
                        up2 = par.get(up)
                        if (isinstance(up2, ast.Subscript) and up2.value is up
                                and isinstance(up2.ctx, (ast.Store, ast.Del))):
                            continue
                        res.strict[node.value].append(site(node))
                        res.loose[node.value].append(site(node))
                        continue
                if isinstance(up, ast.Subscript) and up.slice is node:
                    tx = ast.unparse(up.value)
                    if "arrays" in tx or "registry" in tx or tx in SOA_BASE_TAILS:
                        if isinstance(up.ctx, (ast.Store, ast.Del)):
                            continue
                        res.strict[node.value].append(site(node))
                        res.loose[node.value].append(site(node))
    return res


def _allowed(s: Site, allows: Iterable[SL.AstAllow]) -> SL.AstAllow | None:
    for a in allows:
        if s.path == a.path and a.contains in s.text:
            return a
    return None


def check(res: ScanResult, ledger: Iterable[SL.LedgerRow] | None = None,
          unresolved_allow: Iterable[SL.AstAllow] = UNRESOLVED_ALLOW, *,
          check_declared: bool = True) -> list[str]:
    """台帳の軸 1 と AST の読み手の食い違い(空なら合格)。"""
    rows_ = [r for r in (ledger if ledger is not None else SL.LEDGER) if r.is_soa]
    out: list[str] = []
    used: set[tuple[str, str]] = set()
    by_name: dict[str, list[SL.LedgerRow]] = defaultdict(list)
    for r in rows_:
        by_name[r.name].append(r)
    for nm, rs in by_name.items():
        if len({r.behavior for r in rs}) > 1:
            out.append(f"同名の列で軸 1 が違う(AST では区別できない): {[r.key for r in rs]}")
    for r in rows_:
        if r.behavior == SL.BEHAVIOR:
            if not res.strict.get(r.name):
                out.append(f"{r.key}: 軸 1 が behavior なのに読み手 0(死蔵の見落とし)")
        else:
            bad = []
            for s in res.loose.get(r.name, []):
                a = _allowed(s, r.ast_allow)
                if a is None:
                    bad.append(str(s))
                else:
                    used.add((r.key, a.contains))
            if bad:
                out.append(f"{r.key}: 軸 1 が {r.behavior} なのに読み手がある {sorted(set(bad))}")
    ua = tuple(unresolved_allow)
    for s in res.unresolved:
        a = _allowed(s, ua)
        if a is None:
            out.append(f"解決できない動的な読み(field(変数)・getattr(持ち主, 変数)): {s}  {s.text.strip()}")
        else:
            used.add(("unresolved", a.contains))
    for r in rows_:
        for a in r.ast_allow:
            if (r.key, a.contains) not in used:
                out.append(f"{r.key}: 許可 {a.path} 「{a.contains}」がどの読みにも当たらない(古い許可)")
    for a in ua:
        if ("unresolved", a.contains) not in used:
            out.append(f"許可 {a.path} 「{a.contains}」がどの解決できない読みにも当たらない(古い許可)")
    if check_declared:
        for place in SL.SOA_PLACES:
            want = [r.name for r in rows_ if r.place == place]
            got = res.declared.get(place, [])
            if set(want) != set(got):
                out.append(f"{place}: 宣言と台帳の列が違う 宣言のみ={sorted(set(got) - set(want))} "
                           f"台帳のみ={sorted(set(want) - set(got))}")
    return out


def reader_counts(res: ScanResult) -> dict[str, dict[str, int]]:
    """台帳の SoA の行ごとの読み手の数(記録用)。"""
    out: dict[str, dict[str, int]] = {}
    for r in SL.LEDGER:
        if r.is_soa:
            out[r.key] = {"strict": len(res.strict.get(r.name, [])), "loose": len(res.loose.get(r.name, []))}
    return out


# ---------------------------------------------------------------- 外の状態の持ち主の属性の網羅(10b-2・親の答え 1)
def _self_targets(node: ast.AST) -> list[str]:
    """代入の左辺から ``self.x`` の ``x`` を取る(``self.x[...]`` の添字の中・呼び出しの中は見ない)。"""
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
        return [node.attr]
    if isinstance(node, (ast.Subscript, ast.Attribute)):
        return _self_targets(node.value)
    if isinstance(node, (ast.Tuple, ast.List)):
        return [a for e in node.elts for a in _self_targets(e)]
    if isinstance(node, ast.Starred):
        return _self_targets(node.value)
    return []


def class_attrs(root: Path, rel: str, cls: str) -> list[str]:
    """クラス ``cls`` の属性(メソッドの中の ``self.x = …``・``self.x += …``・``self.x[...] = …`` とクラスの欄)。"""
    tree = ast.parse((Path(root) / rel).read_text(encoding="utf-8"))
    c = next((n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == cls), None)
    if c is None:
        raise KeyError(f"{rel} に class {cls} が無い")
    out: list[str] = []
    for n in ast.walk(c):
        if isinstance(n, ast.Assign):
            tgs = list(n.targets)
        elif isinstance(n, (ast.AnnAssign, ast.AugAssign)):
            tgs = [n.target]
        else:
            continue
        for t in tgs:
            for a in _self_targets(t):
                if a not in out:
                    out.append(a)
    for s in c.body:
        if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name) and s.target.id not in out:
            out.append(s.target.id)
    return out


def coverage(root: Path) -> tuple[dict[str, list[str]], list[str]]:
    """``(持ち主 → 台帳にも除外にも無い属性, 食い違い)``。食い違い=除外と行の両方に載る・クラスに無い属性を載せた。"""
    root = Path(root)
    items = SL.item_attrs()
    excl = SL.excluded_attrs()
    uncovered: dict[str, list[str]] = {}
    problems: list[str] = []
    for e in SL.EXCLUDED:
        if e.kind not in SL.EXCLUDE_KINDS or not e.reason:
            problems.append(f"除外の分類か理由が無い: {e.owner} {e.attrs}")
        if e.owner not in SL.OWNER_CLASSES:
            problems.append(f"除外の持ち主が OWNER_CLASSES に無い: {e.owner}")
    for owner, (rel, cls) in SL.OWNER_CLASSES.items():
        attrs = class_attrs(root, rel, cls)
        for rel2, cls2 in SL.OWNER_ALT_CLASSES.get(owner, ()):  # 構成で入れ替わるクラス・子クラス
            attrs += [a for a in class_attrs(root, rel2, cls2) if a not in attrs]
        have = set(attrs)
        it = items.get(owner, set())
        ex = set(excl.get(owner, {}))
        children = {k[len(owner) + 1:] for k in SL.OWNER_CLASSES
                    if k.startswith(owner + ".") and "." not in k[len(owner) + 1:]}
        for a in sorted(it & ex):
            problems.append(f"{owner}.{a}: 行と除外の両方に載る")
        for a in sorted((it - {"*"}) - have):
            problems.append(f"{owner}.{a}: 行の items に載るがクラス {cls} に無い")
        for a in sorted(ex - have):
            problems.append(f"{owner}.{a}: 除外に載るがクラス {cls} に無い(古い除外)")
        if "*" in it:
            continue  # 持ち主そのものが 1 つの行(O61 の ActualLog など)
        unc = [a for a in attrs if a not in it and a not in ex and a not in children]
        if unc:
            uncovered[owner] = unc
    return uncovered, problems


def runtime_uncovered(owners: "dict[str, object]") -> dict[str, list[str]]:
    """実行時の網羅(検収 2-6): 各持ち主の**インスタンス**の ``vars()``(と ``__slots__``)を台帳+除外の一覧に
    突き合わせ、どちらにも無い属性を返す(子クラスや構成で入れ替わるクラスはこれで拾う)。"""
    items = SL.item_attrs()
    excl = SL.excluded_attrs()
    out: dict[str, list[str]] = {}
    for owner in SL.OWNER_CLASSES:
        head, *rest = owner.split(".")
        obj = owners.get(head)
        for name in rest:
            obj = getattr(obj, name, None) if obj is not None else None
        if obj is None or "*" in items.get(owner, set()):
            continue
        names = set(getattr(obj, "__dict__", {}))
        for cls in type(obj).__mro__:
            sl = getattr(cls, "__slots__", ())
            names |= {sl} if isinstance(sl, str) else set(sl)
        children = {k[len(owner) + 1:] for k in SL.OWNER_CLASSES
                    if k.startswith(owner + ".") and "." not in k[len(owner) + 1:]}
        unc = sorted(n for n in names
                     if n not in items.get(owner, set()) and n not in excl.get(owner, {}) and n not in children
                     and n != "__dict__" and n != "__weakref__")
        if unc:
            out[owner] = unc
    return out


# ================================================================ 10f(K24 (a)): 外の状態の軸 1 の AST
# 実行役の自前の構成(**未リサーチ(expedient)**・10f の材料 §3-5 の案 1):
#
# - 外の状態の行が指す属性(持ち主のクラスの属性)のうち、**全部の行で軸 1 が no/diag** の属性について、持ち主の
#   クラスの外の読み(属性 ``obj.x``・``getattr(obj, "x")``)を集める。持ち主のクラスの中の ``self.x`` は数えない
#   (挙動のためか診断のためかを AST では分けられない=軸 2 と同じく実行時の検査の受け持ち)。
# - 読みは次のどれかなら許す: (1) 直列化・ハッシュ・保存と戻しの書き手(``GENERIC_FILES``・``resolve.restore_*``)
#   (2) 診断の出口の関数(``DIAG_EXITS``)(3) ``engine/run.py`` の ``result.…`` への代入の文(ランの結果の組み立て)
#   (4) 名前の衝突(同じ名前の属性を別のクラスも持つ)で、受け手の名前が持ち主を指していない読み(``EXT_NAME_COLLISIONS``
#   の理由つき)(5) 場所ごとの許可(``EXT_AST_ALLOW``)。
# - 書き(代入の左辺・``x[...] =``・``del``)は読みに数えない。``x.clear()`` などの変更のメソッドの呼び出しは読みに数える
#   (持ち主の外で中身を変える=見る価値がある)。
# - 古い許可(どの読みにも当たらない許可・衝突の表の余り)も落とす。
#
# 限界: ``getattr(obj, 変数)``・``vars()``・持ち主ごと関数に渡した先・持ち主の中の ``self.x`` の目的は見えない。
# 限界(10f 第 3 段の検収 U6): 名前の衝突の 20 属性は、受け手の名前が持ち主と違えば(``conv_mgr.n_blocks`` など)
# 衝突として許すので見えない。受け手の名前が持ち主を指せば(``conv.n_blocks``)落ちる。衝突でない属性は別名
# (``al = act_layer; al.n_wander_bad``)でも落ちる。``getattr(obj, 変数)`` は見えない。文ごとに見るので、
# ``result.… = …`` の行に ``;`` で挙動の読みを足すと落ちる。

#: 直列化・ハッシュ・保存と戻しの書き手(属性を読むが挙動を決めない)。
GENERIC_FILES: tuple[str, ...] = (
    "engine/state_hashes.py", "engine/resume.py", "engine/state_ledger.py", "engine/state_ledger_ast.py",
    "engine/state_codec.py",
)


@dataclass(frozen=True)
class DiagExit:
    """診断の出口の関数(``qualname`` は ``クラス.メソッド`` か関数名。末尾の ``.*`` はそのクラスの全メソッド)。"""

    path: str
    qualname: str
    reason: str

    def hits(self, path: str, qual: str) -> bool:
        if path != self.path:
            return False
        if self.qualname == "*":
            return True
        if self.qualname.endswith(".*"):
            return qual.startswith(self.qualname[:-1])
        return qual == self.qualname


#: 診断の出口(ランの結果・要約・センサス・計器の数え・manifest)。
DIAG_EXITS: tuple[DiagExit, ...] = (
    DiagExit("engine/run.py", "RunResult.*", "ランの結果(RunResult)の要約・manifest の組み立て"),
    DiagExit("economy/census.py", "*", "日次・月次のセンサス(保存則の検査と報告)"),
    DiagExit("cli.py", "checkpoints_payload", "checkpoints の JSON の組み立て(報告)"),
    DiagExit("cli.py", "undefined_registry_payload", "未定義行動の台帳の書き出し(報告)"),
    DiagExit("engine/processes/runner.py", "WorldProcessRunner.counters", "世界過程の計数の要約(報告)"),
    DiagExit("engine/processes/runner.py", "WorldProcessRunner.summary", "世界過程の要約(報告)"),
    DiagExit("engine/processes/runner.py", "WorldProcessRunner.waste_sink_report", "廃棄の帯の報告(第304 Q135)"),
    DiagExit("engine/processes/runner.py", "WorldProcessRunner.projected_waste_tonnes_per_day",
             "廃棄の見込みの報告(RunResult.waste_tonnes_per_day)"),
    DiagExit("engine/processes/runner.py", "WorldProcessRunner.compliance", "法令遵守率の報告(RunResult)"),
    DiagExit("engine/llm_bridge.py", "PerceptionRendererAdapter.counters", "描画の計数の要約(報告)"),
    DiagExit("engine/norm_meter.py", "GroupNormMeter.summary", "集団規範の計器の要約(報告)"),
    DiagExit("engine/presence.py", "PlanExecutor.counters", "計画実行層の計数の要約(報告)"),
)

#: 受け手の名前で持ち主を指す別名(``run_day`` の局所の名前など)。既定は持ち主の道筋の最後の名前。
OWNER_RECEIVER_ALIASES: dict[str, tuple[str, ...]] = {
    "classical": ("classical_policy",),
    "renderer": ("_rr", "_nr", "_fam_renderer"),
    "undefined": ("registry", "undefined_registry"),
}


@dataclass(frozen=True)
class ExtSite:
    """持ち主の外の読みの場所(``func`` は ``クラス.メソッド`` か関数名・入れ子は ``.`` でつなぐ)。"""

    path: str
    line: int
    text: str
    attr: str
    recv: str
    func: str
    result_stmt: bool

    def __str__(self) -> str:
        return f"{self.path}:{self.line} [{self.func}] {self.recv}.{self.attr}"


@dataclass
class ExtScan:
    #: 属性の名前 → 持ち主の外の読み(軸 1 が no/diag の属性だけ)。
    sites: dict[str, list[ExtSite]] = field(default_factory=lambda: defaultdict(list))
    #: 属性の名前 → (持ち主の道筋, 行の鍵, 軸 1) の組。
    rows: dict[str, list[tuple[str, str, str]]] = field(default_factory=dict)
    #: 属性の名前 → 同じ名前を持つ持ち主の外のクラス(``path:Class``)。
    collisions: dict[str, set[str]] = field(default_factory=dict)
    files: int = 0


def ext_attr_rows(ledger: Iterable[SL.LedgerRow] | None = None) -> dict[str, list[tuple[str, str, str]]]:
    """外の状態の行が指す持ち主のクラスの属性の名前 → (持ち主, 行の鍵, 軸 1)。``run_day`` の局所の行は除く。"""
    out: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for r in (ledger if ledger is not None else SL.LEDGER):
        if r.is_soa:
            continue
        for it in r.items:
            if it in SL.OWNER_CLASSES:
                continue
            owner, attr = it.rsplit(".", 1)
            if owner in SL.OWNER_CLASSES:
                out[attr].append((owner, r.key, r.behavior))
    return dict(out)


def _owner_classes(owner: str) -> set[str]:
    rel, cls = SL.OWNER_CLASSES[owner]
    return {f"{rel}:{cls}"} | {f"{a}:{b}" for a, b in SL.OWNER_ALT_CLASSES.get(owner, ())}


def class_defined_names(parsed: Iterable[tuple[str, ast.Module]]) -> dict[str, set[str]]:
    """属性の名前 → それを持つクラス(``path:Class``)。``self.x = …``(どのメソッドでも)・クラスの本体の代入と注釈・
    メソッドとプロパティの名前。"""
    out: dict[str, set[str]] = defaultdict(set)
    for rel, tree in parsed:
        for c in ast.walk(tree):
            if not isinstance(c, ast.ClassDef):
                continue
            key = f"{rel}:{c.name}"
            for s in c.body:
                if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[s.name].add(key)
                elif isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name):
                    out[s.target.id].add(key)
                elif isinstance(s, ast.Assign):
                    for t in s.targets:
                        if isinstance(t, ast.Name):
                            out[t.id].add(key)
            for n in ast.walk(c):
                tgs: list[ast.AST] = []
                if isinstance(n, ast.Assign):
                    tgs = list(n.targets)
                elif isinstance(n, (ast.AnnAssign, ast.AugAssign)):
                    tgs = [n.target]
                for t in tgs:
                    for a in _self_targets(t):
                        out[a].add(key)
    return out


def _root_name(expr: ast.AST) -> str:
    while isinstance(expr, (ast.Attribute, ast.Subscript, ast.Starred)):
        expr = expr.value
    return expr.id if isinstance(expr, ast.Name) else ""


def _is_result_stmt(st: ast.AST | None) -> bool:
    """``result.x = …``・``result.x[...] = …``・``result.x += …``(左辺が全部 ``result`` から始まる代入の文)。"""
    if isinstance(st, ast.Assign):
        tgs = list(st.targets)
    elif isinstance(st, (ast.AugAssign, ast.AnnAssign)):
        tgs = [st.target]
    else:
        return False
    flat: list[ast.AST] = []
    for t in tgs:
        flat.extend(t.elts if isinstance(t, (ast.Tuple, ast.List)) else [t])
    return bool(flat) and all(_root_name(t) == "result" and not isinstance(t, ast.Name) for t in flat)


def scan_external(root: Path, files: Iterable[Path] | None = None,
                  ledger: Iterable[SL.LedgerRow] | None = None) -> ExtScan:
    """``root``(= ``src/shibuya``)の下で、軸 1 が no/diag の外の状態の属性の「持ち主の外の読み」を集める。"""
    root = Path(root)
    res = ExtScan()
    res.rows = ext_attr_rows(ledger)
    checked = {a for a, rs in res.rows.items() if all(b != SL.BEHAVIOR for _o, _k, b in rs)}
    fl = list(files) if files is not None else source_files(root)
    res.files = len(fl)
    parsed: list[tuple[str, list[str], ast.Module]] = []
    for fp in fl:
        text = fp.read_text(encoding="utf-8")
        try:
            parsed.append((fp.relative_to(root).as_posix(), text.split("\n"), ast.parse(text)))
        except SyntaxError:
            continue
    defined = class_defined_names((rel, t) for rel, _l, t in parsed)
    owner_cls = {a: set().union(*(_owner_classes(o) for o, _k, _b in res.rows[a])) for a in checked}
    res.collisions = {a: defined.get(a, set()) - owner_cls[a] for a in checked if defined.get(a, set()) - owner_cls[a]}
    for rel, lines, tree in parsed:
        par = _parents(tree)

        def where(node: ast.AST) -> tuple[str, str | None]:
            names: list[str] = []
            cls: str | None = None
            p = par.get(node)
            while p is not None:
                if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.append(p.name)
                    if isinstance(p, ast.ClassDef) and cls is None:
                        cls = p.name
                p = par.get(p)
            return ".".join(reversed(names)), cls

        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr"
                    and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant)
                    and isinstance(node.args[1].value, str) and node.args[1].value in checked):
                attr, recv_node = node.args[1].value, node.args[0]
            elif isinstance(node, ast.Attribute) and node.attr in checked and isinstance(node.ctx, ast.Load):
                up = par.get(node)
                if isinstance(up, ast.Subscript) and up.value is node and isinstance(up.ctx, (ast.Store, ast.Del)):
                    continue
                attr, recv_node = node.attr, node.value
            else:
                continue
            qual, cls = where(node)
            if cls is not None and f"{rel}:{cls}" in owner_cls[attr]:
                continue  # 持ち主のクラスの中
            ln = int(getattr(node, "lineno", 0))
            st = _enclosing_stmt(node, par)
            recv = ast.unparse(recv_node)
            if _self_update_stmt(st, attr, recv):
                continue  # 自己更新(``o.x = getattr(o, "x", 0) + 1``・``o.x += 1``)は書き
            res.sites[attr].append(ExtSite(rel, ln, lines[ln - 1] if 0 < ln <= len(lines) else "", attr,
                                           recv, qual, _is_result_stmt(st)))
    return res


def _self_update_stmt(st: ast.AST | None, attr: str, recv: str) -> bool:
    """文が同じ受け手の同じ属性への代入か(右辺の読みは自己更新)。"""
    if isinstance(st, ast.Assign):
        tgs = list(st.targets)
    elif isinstance(st, (ast.AugAssign, ast.AnnAssign)):
        tgs = [st.target]
    else:
        return False
    return any(isinstance(t, ast.Attribute) and t.attr == attr and ast.unparse(t.value) == recv for t in tgs)


def _owner_recv(site: ExtSite, owners: Iterable[str]) -> bool:
    """受け手の名前(最後の名前)が持ち主を指すか。"""
    tail = site.recv.split(".")[-1].split("(")[0].split("[")[0].strip()
    for o in owners:
        if tail == o.split(".")[-1] or tail in OWNER_RECEIVER_ALIASES.get(o, ()):
            return True
    return False


def ext_reason(site: ExtSite, scan: ExtScan) -> str | None:
    """規則で許す理由の種類(``generic``・``exit``・``result``・``collision``)。``None`` なら規則では許さない。"""
    if site.path in GENERIC_FILES or (site.path == "engine/resolve.py" and site.func.startswith("restore")):
        return "generic"
    if any(d.hits(site.path, site.func) for d in DIAG_EXITS):
        return "exit"
    if site.path == "engine/run.py" and site.result_stmt:
        return "result"
    owners = [o for o, _k, _b in scan.rows.get(site.attr, [])]
    if site.attr in scan.collisions and not _owner_recv(site, owners):
        return "collision"
    return None


def check_external(scan: ExtScan, allow: Iterable[ExtAllow] | None = None,
                   collisions_allow: dict[str, str] | None = None) -> list[str]:
    """外の状態の軸 1 の検査(空なら合格)。場所ごとの許可は当たる数が宣言と同じであること(U5)。"""
    allow_t = tuple(EXT_AST_ALLOW if allow is None else allow)
    coll = EXT_NAME_COLLISIONS if collisions_allow is None else collisions_allow
    out: list[str] = []
    hits: dict[int, int] = defaultdict(int)
    for attr, sites in sorted(scan.sites.items()):
        for s in sites:
            why = ext_reason(s, scan)
            if why == "collision" and not coll.get(attr):
                why = None
            if why is not None:
                continue
            i = next((j for j, e in enumerate(allow_t)
                      if e.attr == attr and e.allow.path == s.path and e.allow.contains in s.text), None)
            if i is not None:
                hits[i] += 1
                continue
            rows = ",".join(f"{k}:{o}.{attr}({b})" for o, k, b in scan.rows.get(attr, []))
            out.append(f"{rows}: 軸 1 が no/diag なのに持ち主の外で読まれる {s}  {s.text.strip()[:100]}")
    for j, e in enumerate(allow_t):
        if hits[j] == 0:
            out.append(f"{e.attr}: 許可 {e.allow.path} 「{e.allow.contains}」がどの読みにも当たらない(古い許可)")
        elif hits[j] != e.count:
            out.append(f"{e.attr}: 許可 {e.allow.path} 「{e.allow.contains}」の当たる数が {hits[j]}(宣言は {e.count})")
        if not e.allow.reason:
            out.append(f"{e.attr}: 許可 {e.allow.path} の理由が空")
    for a in sorted(set(scan.collisions) - set(coll)):
        out.append(f"{a}: 名前の衝突({sorted(scan.collisions[a])[:3]})の理由が EXT_NAME_COLLISIONS に無い")
    for a in sorted(set(coll) - set(scan.collisions)):
        out.append(f"{a}: EXT_NAME_COLLISIONS に載るが衝突が無い(古い許可)")
    for a, r in coll.items():
        if not r:
            out.append(f"{a}: EXT_NAME_COLLISIONS の理由が空")
    return out


#: 名前の衝突(軸 1 が no/diag の属性と同じ名前を、持ち主の外のクラスも持つ)。受け手の名前が持ち主を指す読みは
#: 衝突として許さず、ほかの規則で見る。
EXT_NAME_COLLISIONS: dict[str, str] = {
    "_agents": "同じ名前を DeferralQueue も持つ(受け手の型は AST で分からない)",
    "_blocks": "同じ名前を StubRenderer も持つ(受け手の型は AST で分からない)",
    "_rows": "同じ名前を ActualLog も持つ(受け手の型は AST で分からない)",
    "_start": "同じ名前を SalientProcess も持つ(受け手の型は AST で分からない)",
    "blocks": "同じ名前を AnnouncementScope・LLMCall・Rendered・RenderedPrompt ほか 2 も持つ(受け手の型は AST で分からない)",
    "cache_hits": "同じ名前を Rendered も持つ(受け手の型は AST で分からない)",
    "cache_misses": "同じ名前を Rendered も持つ(受け手の型は AST で分からない)",
    "home_cell": "同じ名前を MockWeeklySchedule・PlanExecutor・Population・_HomeShim も持つ(受け手の型は AST で分からない)",
    "log": "同じ名前を BusTaxiProcess・DeliveryInboundProcess・HotelProcess・LargeEventProcess ほか 9 も持つ(受け手の型は AST で分からない)",
    "n_arrived": "同じ名前を ResolveOutcome も持つ(受け手の型は AST で分からない)",
    "n_blocks": "同じ名前を PlanBlocks・Tape・TapeWriter も持つ(受け手の型は AST で分からない)",
    "n_board_timeout": "同じ名前を ResolveOutcome・RunResult も持つ(受け手の型は AST で分からない)",
    "n_board_waiting": "同じ名前を ResolveOutcome・RunResult も持つ(受け手の型は AST で分からない)",
    "n_calls": "同じ名前を ArbiterDecision・MockLLM・TapeLLM も持つ(受け手の型は AST で分からない)",
    "n_deferred_rows": "同じ名前を Replay・TapeWriter も持つ(受け手の型は AST で分からない)",
    "n_meals": "同じ名前を ResolveOutcome も持つ(受け手の型は AST で分からない)",
    "n_noticed": "同じ名前を NoticeResult も持つ(受け手の型は AST で分からない)",
    "phase_seconds": "同じ名前を RunResult も持つ(受け手の型は AST で分からない)",
    "tick": "同じ名前を ActualLogEntry・ArbiterDecision・BridgeResult・Checkpoint ほか 16 も持つ(受け手の型は AST で分からない)",
    "top": "同じ名前を MemoryLayer も持つ(受け手の型は AST で分からない)",
}

@dataclass(frozen=True)
class ExtAllow:
    """外の状態の軸 1 の場所ごとの許可(属性の名前・当たる数・場所と理由)。"""

    attr: str
    count: int
    allow: SL.AstAllow


#: 場所ごとの許可(属性の名前・場所・当たる数)。10f の時点で規則に当たらなかった持ち主の外の読みを 1 つずつ見て理由を書いた。
#: 当たる数を固定する(同じ文字列の行を挙動の場所に写すと数が増えて落ちる=第 3 段の検収 U5)。
EXT_AST_ALLOW: tuple[ExtAllow, ...] = (
    ExtAllow("last_habit", 1, SL.AstAllow("engine/poi_target.py", 'getattr(self.chooser, "last_habit", -1)',
                               "店の決め手の名前(named/habit/visible)を StoreChoice.note に渡すだけ。決め手は O13 の"
                               "choice_reason と O68 の決め手別の数え(diag)にしか入らない")),
    ExtAllow("n_arrivals", 1, SL.AstAllow("engine/run.py", "_pres0 = int(presence.n_arrivals)",
                               "層別の起床の数え(layer_counts=診断の表)の差分の基準")),
    ExtAllow("n_arrivals", 1, SL.AstAllow("engine/run.py", "int(presence.n_arrivals) + int(presence.n_departures) - _pres0",
                               "同上(層別の起床の数えの差分)")),
    ExtAllow("n_departures", 1, SL.AstAllow("engine/run.py", "_pres0 = int(presence.n_arrivals)", "同上")),
    ExtAllow("n_departures", 1, SL.AstAllow("engine/run.py",
                                 "int(presence.n_arrivals) + int(presence.n_departures) - _pres0", "同上")),
    ExtAllow("n_tape_misses", 2, SL.AstAllow("engine/run.py", "prev_tape_misses = bridge.n_tape_misses",
                                  "診断の行(RunResult.diagnostics)の差分の基準(10d 検収 L1)")),
    ExtAllow("n_tape_misses", 1, SL.AstAllow("engine/run.py", "bridge.n_tape_misses - prev_tape_misses",
                                  "診断の行の列(テープに無い呼の数)")),
    ExtAllow("n_transfers", 1, SL.AstAllow("engine/run.py", 'int(getattr(ledger.money, "n_transfers", 0)) != 0',
                                "再開に渡す台帳の検査(参入資本や財布を入れた台帳なら止める=挙動ではなく誤用の拒否)")),
    ExtAllow("origin_of", 1, SL.AstAllow("engine/run.py", "rel_layer.origin_of.clear()",
                              "tick の終わりに会話の起点の控え(O19・diag)を捨てる書き。読みではない")),
    ExtAllow("seconds", 1, SL.AstAllow("engine/clock.py", "delta.seconds",
                            "標準ライブラリの timedelta.seconds(GroupNormMeter.seconds とは別物)")),
    ExtAllow("signage_exposures", 1, SL.AstAllow("engine/run.py", '_fam_renderer is not None and getattr(',
                                      "**挙動の読み**: 描画が集めた看板の露出を、同じ tick の 6 段目で記憶と親しみの層が"
                                      "読んで空にする。tick の中だけの口(checkpoint の時点では常に空)なので O64 の"
                                      "軸 1 no・軸 2 discardable のままでもハッシュと再開は変わらない(10f で親に確かめる点)")),
    ExtAllow("signage_exposures", 1, SL.AstAllow("engine/run.py", "_exp = list(_fam_renderer.signage_exposures)", "同上")),
    ExtAllow("signage_exposures", 1, SL.AstAllow("engine/run.py", "_fam_renderer.signage_exposures.clear()", "同上(空にする書き)")),
    ExtAllow("sleep_counts", 1, SL.AstAllow("engine/run.py", "for _k, _v in presence.sleep_counts.items():",
                                 "RunResult.planned_sleep_counts の組み立て(ランの最後)")),
    ExtAllow("stats", 1, SL.AstAllow("engine/run.py", '_cs = getattr(getattr(poi_resolver, "chooser", None), "stats", None)',
                          "RunResult.chooser_stats の組み立て(ランの最後)")),
    ExtAllow("stats", 1, SL.AstAllow("engine/run.py", "for k, v in fam_layer.stats.items()",
                          "RunResult.familiarity_summary の組み立て(ランの最後)")),
    ExtAllow("text_id", 1, SL.AstAllow("engine/run.py", "+ act_layer.until_kind.nbytes + act_layer.text_id.nbytes",
                            "成長の検査(RunResult.growth_measured)のバイト数")),
)
