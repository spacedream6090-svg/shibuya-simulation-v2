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
