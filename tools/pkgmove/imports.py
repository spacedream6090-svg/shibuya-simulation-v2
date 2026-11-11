# -*- coding: utf-8 -*-
"""import の文の書き換え(許可の一覧の (a))。

- ``from P import a, b as c`` の P がファイルのモジュールで移すなら、モジュールの名だけを書き換える(文の形と注は保つ)。
- P が包み(頭)なら名ごとに見る: ``P.a`` が子のモジュールで移すなら ``from 新しい親 import 新しい葉 [as a]``。
  ``a`` が頭の再輸出なら(頭を空にするか消す段・元のモジュールか頭の直の引き先が移る段)、定義したモジュールへ向ける
  (「再輸出の頭を通る import は元のモジュールへ」)。
- ``import P.Q as X`` は、名の全体が移すモジュール(ファイルか頭)なら書き換える。別名の無い ``import P.Q`` も書き換えるが、
  コードの中の ``P.Q.x`` の連なりは書き換えない(注意として報告する)。
- 名の行き先が 1 つなら、モジュールの名と別名の部分だけを書き換える(改行・注・括弧はそのまま)。行き先が 2 つ以上に分かれる
  ときだけ文を作り直す(1 つの文を行き先ごとの文に分け、名の行の注は名に付けて残す)。
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from pkgmove.model import SRC_PREFIX, Ctx, Edit, Text, mod_of, resolve_from

_FROM_RE = re.compile(r"from(\s+)([\w.]+)(\s+)import")
_LINE_MAX = 120


@dataclass
class Target:
    """書き換えた後の 1 つの名(モジュール・名・別名)。"""

    module: str
    name: str
    asname: str | None
    alias: ast.alias | None = None


@dataclass
class ImportStats:
    statements: int = 0
    via_head: int = 0
    #: 包みから子のモジュールを読む文(``from P import 子``)で、子が移すもの(計画の「頭を通る」の数え方の候補として報告)。
    via_package: int = 0
    split: int = 0
    warnings: list[str] = field(default_factory=list)


def _alias_text(name: str, asname: str | None) -> str:
    return f"{name} as {asname}" if asname else name


def plan_from(ctx: Ctx, node: ast.ImportFrom) -> tuple[list[Target] | None, bool, list[str]]:
    """``from … import`` の書き換えの計画(変わらなければ ``None``)・頭を通したか・注意(子のモジュールを読んだ印は
    注意の並びの頭の ``"@sub"``)。"""
    if node.level != 0 or not node.module or not (node.module == "shibuya" or node.module.startswith("shibuya.")):
        return None, False, []
    P = node.module
    ix = ctx.index
    warns: list[str] = []
    out: list[Target] = []
    changed = via_head = False
    pkg = ix.is_package(P)
    for a in node.names:
        if a.name == "*":
            if P in ctx.modmap:
                out.append(Target(ctx.modmap[P], "*", None, a))
                changed = True
                warns.append(f"from {P} import * を書き換えた(中身の名は確かめていない)")
            else:
                out.append(Target(P, "*", None, a))
            continue
        if pkg:
            sub = f"{P}.{a.name}"
            reexp = ix.info(P).imports.get(a.name)
            if ix.exists(sub):
                if reexp is not None and f"{reexp[0]}.{reexp[1]}" != sub:
                    warns.append(f"{P} の {a.name} は子のモジュールと頭の再輸出の両方にある(子のモジュールとして扱った)")
                if sub in ctx.modmap:
                    if "@sub" not in warns:
                        warns.insert(0, "@sub")
                    new = ctx.modmap[sub]
                    parent, _, leaf = new.rpartition(".")
                    asname = a.asname or (a.name if leaf != a.name else None)
                    out.append(Target(parent, leaf, asname, a))
                    changed = True
                    if sub in ctx.heads_changed:
                        warns.append(f"from {P} import {a.name}: 包み {sub} の頭を空にする段=属性で頭の名を読む所は壊れる")
                else:
                    out.append(Target(P, a.name, a.asname, a))
                continue
            if reexp is not None:
                org = ix.origin(P, a.name)
                direct = reexp[0]
                if org is None:
                    org = reexp
                D, on = org
                if P in ctx.heads_changed or D in ctx.modmap or direct in ctx.modmap:
                    asname = a.asname or (a.name if on != a.name else None)
                    out.append(Target(ctx.new_mod(D), on, asname, a))
                    changed = True
                    via_head = True
                    continue
                out.append(Target(P, a.name, a.asname, a))
                continue
            if a.name in ix.info(P).defs:
                if P in ctx.heads_changed:
                    warns.append(f"from {P} import {a.name}: 頭で定義した名を、頭を空にする段で読む(書き換えていない)")
                out.append(Target(ctx.new_mod(P), a.name, a.asname, a))
                changed = changed or P in ctx.modmap
                continue
            if P in ctx.modmap or P in ctx.heads_changed:
                warns.append(f"from {P} import {a.name}: 名の出どころが見つからない(書き換えていない)")
            out.append(Target(P, a.name, a.asname, a))
            continue
        if P in ctx.modmap:
            out.append(Target(ctx.modmap[P], a.name, a.asname, a))
            changed = True
        else:
            out.append(Target(P, a.name, a.asname, a))
    return (out if changed else None), via_head, warns


def plan_import(ctx: Ctx, node: ast.Import) -> tuple[list[tuple[ast.alias, str]] | None, list[str]]:
    """``import …`` の書き換え(別名の名ごとに新しい名)。"""
    out: list[tuple[ast.alias, str]] = []
    warns: list[str] = []
    for a in node.names:
        if a.name in ctx.modmap:
            out.append((a, ctx.modmap[a.name]))
            if not a.asname:
                warns.append(f"import {a.name}(別名なし)を書き換えた: コードの中の {a.name}.… の連なりは書き換えていない")
            if a.name in ctx.heads_changed:
                warns.append(f"import {a.name}: 包みの頭を空にする段=属性で頭の名を読む所は壊れる")
    return (out or None), warns


def _groups(targets: list[Target]) -> list[tuple[str, list[Target]]]:
    order: list[str] = []
    by: dict[str, list[Target]] = {}
    for t in targets:
        if t.module not in by:
            order.append(t.module)
            by[t.module] = []
        by[t.module].append(t)
    return [(m, by[m]) for m in order]


def _comments(text: Text, node: ast.ImportFrom) -> tuple[str, dict[int, str], dict[int, list[str]]]:
    """文の中の注: 頭の行の注・名の行の注(名の ``id`` → 注)・名の前の注だけの行(名の ``id`` → 注の並び)。"""
    head = ""
    trailing: dict[int, str] = {}
    before: dict[int, list[str]] = {}
    by_line: dict[int, list[ast.alias]] = {}
    for a in node.names:
        by_line.setdefault(a.lineno, []).append(a)
    pending: list[str] = []
    for ln in range(node.lineno, node.end_lineno + 1):  # type: ignore[operator]
        s = text.line(ln)
        if ln == node.end_lineno:
            s = s[: len(s.encode("utf-8")[: node.end_col_offset].decode("utf-8"))]  # type: ignore[index]
        if "#" not in s:
            continue
        c = s[s.index("#"):].rstrip()
        if ln in by_line:
            trailing[id(by_line[ln][-1])] = c
        elif ln == node.lineno:
            head = c
        else:
            pending.append(c)
            nxt = next((a for a in node.names if a.lineno > ln), None)
            if nxt is not None:
                before.setdefault(id(nxt), []).extend(pending)
                pending = []
    if pending:
        trailing.setdefault(id(node.names[-1]), "")
        trailing[id(node.names[-1])] = (trailing[id(node.names[-1])] + "  " + "  ".join(pending)).strip()
    return head, trailing, before


def render_from(groups: list[tuple[str, list[Target]]], *, indent: str, eol: str, multiline: bool, inline: bool,
                comments: tuple[str, dict[int, str], dict[int, list[str]]]) -> str:
    """行き先ごとの ``from … import`` の文(1 つ目は元の位置から始まる=頭の空白を含まない)。"""
    head_c, trailing, before = comments
    stmts: list[str] = []
    for gi, (mod, ts) in enumerate(groups):
        names = [_alias_text(t.name, t.asname) for t in ts]
        has_c = any(id(t.alias) in trailing or id(t.alias) in before for t in ts) or (gi == 0 and head_c)
        one = f"from {mod} import {', '.join(names)}"
        if inline or (not multiline and not has_c and len(indent) + len(one) <= _LINE_MAX):
            stmts.append(one)
            continue
        lines = [f"from {mod} import (" + (f"  {head_c}" if gi == 0 and head_c else "")]
        for t, nm in zip(ts, names):
            for c in before.get(id(t.alias), []):
                lines.append(f"{indent}    {c}")
            c = trailing.get(id(t.alias), "")
            lines.append(f"{indent}    {nm}," + (f"  {c}" if c else ""))
        lines.append(f"{indent})")
        stmts.append(eol.join(lines))
    sep = "; " if inline else eol + indent
    return sep.join(stmts)


def rewrite_file(ctx: Ctx, path: str, text: str, tree: ast.Module, symbols: dict[int, str],
                 stats: ImportStats) -> list[Edit]:
    """1 本のファイルの import の文の書き換え。"""
    t = Text(text)
    edits: list[Edit] = []
    own = mod_of(path[len(SRC_PREFIX):]) if path.startswith(SRC_PREFIX) else ""
    pkg = own if path.endswith("/__init__.py") else own.rpartition(".")[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level > 0:
            target = resolve_from(pkg, node) if own else None
            if own in ctx.modmap or (target is not None and (target in ctx.modmap or any(
                    f"{target}.{a.name}" in ctx.modmap for a in node.names))):
                stats.warnings.append(f"{path}:{node.lineno}: 相対の import(書き換えない=移すファイルか移すモジュールに"
                                      f"かかる。検収 L-5)")
            continue
        if isinstance(node, ast.ImportFrom):
            targets, via, warns = plan_from(ctx, node)
            sub = bool(warns) and warns[0] == "@sub"
            stats.warnings += [f"{path}:{node.lineno}: {w}" for w in warns if w != "@sub"]
            if targets is None:
                continue
            edits += _edits_from(t, node, targets, path, symbols, stats)
            stats.statements += 1
            stats.via_head += int(via)
            stats.via_package += int(sub)
        elif isinstance(node, ast.Import):
            plan, warns = plan_import(ctx, node)
            stats.warnings += [f"{path}:{node.lineno}: {w}" for w in warns]
            if plan is None:
                continue
            for a, new in plan:
                s, e = t.span(a)
                edits.append(Edit(s, e, _alias_text(new, a.asname), "import", symbols.get(id(node), ""),
                                  f"import {a.name}"))
            stats.statements += 1
    return edits


def _edits_from(t: Text, node: ast.ImportFrom, targets: list[Target], path: str, symbols: dict[int, str],
                stats: ImportStats) -> list[Edit]:
    sym = symbols.get(id(node), "")
    groups = _groups(targets)
    s, e = t.span(node)
    if len(groups) == 1:
        mod, ts = groups[0]
        m = _FROM_RE.match(t.text, s)
        if not m:
            raise ValueError(f"{path}:{node.lineno}: from の文の形が読めない")
        out = [Edit(m.start(2), m.end(2), mod, "import", sym, f"from {node.module}")] if mod != node.module else []
        for tg in ts:
            a = tg.alias
            assert a is not None
            if tg.name != a.name or tg.asname != a.asname:
                a0, a1 = t.span(a)
                out.append(Edit(a0, a1, _alias_text(tg.name, tg.asname), "import", sym, f"from {node.module}"))
        return out
    stats.split += 1
    prefix = t.text[t.starts[node.lineno - 1]: s]
    inline = prefix.strip() != ""
    indent = "" if inline else prefix
    new = render_from(groups, indent=indent, eol=t.eol, multiline=node.end_lineno > node.lineno, inline=inline,
                      comments=_comments(t, node))
    return [Edit(s, e, new, "import", sym, f"from {node.module}(行き先 {len(groups)} つに分けた)")]


def head_drops(ctx: Ctx, path: str, text: str, tree: ast.Module) -> tuple[list[Edit], list[str], list[str]]:
    """この段で空にしない包みの頭の再輸出のうち、出どころのモジュールが包みの外へ移るものの import の文を除く
    (再輸出の口を残さない=計画 §7-4。頭を通る import はこの段で元のモジュールへ向け直すので、読み手は残らない)。

    残すと、移したモジュールが古い包みに残る兄弟を読むときに古い頭が走り、頭が移したモジュールを読み返して循環の import に
    なる(予行で ``agents/schedule.py`` → ``world/facts/mock_schedule.py`` と ``llm/parser.py`` → ``act/intake/parser.py``)。
    頭の中でその名を使っていれば除かずに注意を出す。戻り値=(書き換え, 除いた名, 注意)。``__all__`` から名を除くのは
    :func:`all_drops`(呼び手が除いた名で呼ぶ)。
    """
    if not path.startswith(SRC_PREFIX) or not path.endswith("/__init__.py"):
        return [], [], []
    pkg = mod_of(path[len(SRC_PREFIX):])
    t = Text(text)
    edits: list[Edit] = []
    dropped: list[str] = []
    warns: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        src = resolve_from(pkg, node)
        if src is None or src not in ctx.modmap or ctx.modmap[src].startswith(pkg + "."):
            continue
        names = [a.asname or a.name for a in node.names]
        used = sorted({n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id in names
                       and not (node.lineno <= n.lineno <= node.end_lineno)})  # type: ignore[operator]
        if used:
            warns.append(f"{path}:{node.lineno}: 頭が再輸出の名 {used} を中で使う=除かない(循環の import が残りうる)")
            continue
        a = t.starts[node.lineno - 1]
        e = t.starts[node.end_lineno] if node.end_lineno < len(t.starts) else len(text)  # type: ignore[operator]
        edits.append(Edit(a, e, "", "import", "<module>", f"頭の再輸出を除いた: from {src} import {', '.join(names)}"))
        dropped += names
    if dropped:
        warns.append(f"{path}: 頭の再輸出 {len(dropped)} 個を除いた")
    return edits, dropped, warns


#: ``__all__`` の 1 行 1 要素の行(字下げ・引用符の名・「,」・行の終わりの注)。
_ALL_LINE_RE = re.compile(r"""^(?P<ind>[ \t]*)(?P<q>["'])(?P<name>[A-Za-z_]\w*)(?P=q)[ \t]*,?[ \t]*(?P<com>#.*)?$""")


def head_all_node(tree: ast.Module) -> ast.List | ast.Tuple | None:
    """頂上の ``__all__ = [...]``(か ``(...)``)の値。無ければ ``None``。"""
    for n in tree.body:
        if (isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id == "__all__" and isinstance(n.value, (ast.List, ast.Tuple))):
            return n.value
    return None


def all_drops(path: str, text: str, tree: ast.Module, names: list[str]) -> tuple[list[Edit], list[str], list[str]]:
    """〔親の裁定 review3 の 2〕頭から除いた再輸出の名を、その頭の ``__all__`` からも除く(頭が自己整合であること)。

    書き換えてよいのは ``__all__`` の要素のうち ``names`` に入るものだけ(許可の一覧の (e))。1 行 1 要素の行だけを扱い、行ごと
    除く(行の終わりに注があれば注の行として残す)。ほかの形(1 行に 2 つ以上・式)は除かずに注意を出す=守り
    (:func:`pkgmove.guard.check_head_all`)が止める。戻り値=(書き換え, 除いた名, 注意)。
    """
    node = head_all_node(tree)
    want = set(names)
    if node is None or not want:
        return [], [], []
    t = Text(text)
    edits: list[Edit] = []
    removed: list[str] = []
    warns: list[str] = []
    for e in node.elts:
        if not (isinstance(e, ast.Constant) and isinstance(e.value, str) and e.value in want):
            continue
        m = _ALL_LINE_RE.match(t.line(e.lineno)) if e.lineno == e.end_lineno else None
        if m is None or m.group("name") != e.value:
            warns.append(f"{path}:{e.lineno}: 頭の __all__ の要素 {e.value!r} が 1 行 1 要素の形でない=除かない")
            continue
        a = t.starts[e.lineno - 1]
        b = t.starts[e.lineno] if e.lineno < len(t.starts) else len(text)
        new = (m.group("ind") + m.group("com") + t.eol) if m.group("com") else ""
        edits.append(Edit(a, b, new, "head_all", "__all__", f"頭の __all__ から除いた: {e.value}"))
        removed.append(e.value)
    return edits, removed, warns


def rewrite_code(ctx: Ctx, code: str) -> list[tuple[str, str]] | None:
    """文字列の中の Python のコード(子のプロセスに渡す文など)の import の文の書き換え: (元の文, 新しい文) の並び。
    コードとして読めなければ ``None``。"""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    t = Text(code)
    out: list[tuple[str, str]] = []
    st = ImportStats()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        sub = rewrite_file(ctx, "<code>", code, ast.Module(body=[node], type_ignores=[]), {}, st)
        if not sub:
            continue
        s, e = t.span(node)
        old = code[s:e]
        new = old
        for ed in sorted(sub, key=lambda x: x.start, reverse=True):
            new = new[: ed.start - s] + ed.new + new[ed.end - s:]
        out.append((old, new))
    return out
