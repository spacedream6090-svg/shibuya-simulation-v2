# -*- coding: utf-8 -*-
"""道の文字列の書き換え(許可の一覧の (b))と、触らなかった道の形の文字列の拾い。

規則
    ``exact``(src の表): 文字列の全体が、移すファイルの今の道(``src/shibuya`` からの相対か、``src/shibuya/`` から始まる
        リポの根からの道)なら新しい道へ。
    ``paths``(tests と tools): 文字列の中の
        - 斜線の道 ``[src/shibuya/|shibuya/]<道>.py|.json``(移すファイルなら道の部分を新しい道へ)
        - 点の道 ``shibuya.<モジュール>[.<名>…]``(移すモジュールなら頭を新しい名へ。包みの頭の再輸出は元のモジュールへ。
          後ろが ``/`` のもの=版の ID は触らない。凍結の名=``Ctx.frozen_tokens`` は触らない。包みの名だけのもの
          (``"shibuya.engine"``)は行き先が 1 つに決まらないので触らずに注意に出す=検収 L-7)
        - Python のコードとして読める文字列(子のプロセスに渡す文)の import の文(:mod:`pkgmove.imports` と同じ規則)
        - ``/`` の結合 ``X / "engine" / "clock.py"``(2 つ以上の定数にまたがる道)
      日本語などの ASCII の外の字を含む文(コードとして読めるものを除く)は記録の文として触らない。f 文字列の部分も触らない。
書き換えは文字列の値で作り、ソースの字面へ同じ順に当て、``ast.literal_eval`` で値が合うかを確かめる(合わなければ触らずに報告)。
"""
from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass, field

from pkgmove import imports as IM
from pkgmove.model import Ctx, Edit, Text, docstrings_of

SLASH_RE = re.compile(r"(?<![\w./\\-])((?:src/)?shibuya/)?((?:[A-Za-z_]\w*/)+[A-Za-z_]\w*\.(?:py|json))(?![\w/])")
DOT_RE = re.compile(r"(?<![\w.])shibuya(?:\.[A-Za-z_]\w*)+")
#: 包みの名で始まる点の名(``shibuya.`` の無い形=乱数の用途名・manifest の文など。拾いの報告だけ)。
BARE_DOT_RE = re.compile(r"(?<![\w.])(?:agents|census|core|economy|engine|llm|manifest|perception|world)(?:\.[A-Za-z_]\w*)+")


@dataclass
class PathRules:
    """移すファイルの道(``src/shibuya`` からの相対)。"""

    relmap: dict[str, str]


@dataclass
class StrStats:
    rewritten: Counter = field(default_factory=Counter)
    sites: Counter = field(default_factory=Counter)
    skipped: list[dict] = field(default_factory=list)


def _parents(tree: ast.AST) -> dict[int, ast.AST]:
    out: dict[int, ast.AST] = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            out[id(c)] = n
    return out


def dotted_new(ctx: Ctx, tok: str) -> str:
    """点の道の書き換え(変わらなければそのまま)。"""
    ix = ctx.index
    L = ix.longest_module(tok)
    if L is None:
        return tok
    rest = tok[len(L) + 1:].split(".") if len(tok) > len(L) else []
    tail = ("." + ".".join(rest)) if rest else ""
    if not ix.is_package(L):
        return ctx.modmap[L] + tail if L in ctx.modmap else tok
    if not rest:
        return ctx.modmap.get(L, tok)
    r1 = rest[0]
    inf = ix.info(L)
    if r1 in inf.imports:
        org = ix.origin(L, r1) or inf.imports[r1]
        D, on = org
        if L in ctx.heads_changed or D in ctx.modmap or inf.imports[r1][0] in ctx.modmap:
            return ctx.new_mod(D) + "." + on + ("." + ".".join(rest[1:]) if rest[1:] else "")
        return tok
    if r1 in inf.defs and L in ctx.modmap:
        return ctx.modmap[L] + tail
    return tok


def _plain_reps(ctx: Ctx, rules: PathRules, value: str, lo: int, hi: int,
                skipped: list[tuple[str, str, str]]) -> list[tuple[int, int, str, str]]:
    """値の ``lo``〜``hi`` の斜線の道と点の道の書き換え: (始め, 終わり, 新しい字面, 種類)。"""
    out: list[tuple[int, int, str, str]] = []
    seg = value[lo:hi]
    for m in SLASH_RE.finditer(seg):
        rel = m.group(2)
        if rel in rules.relmap:
            out.append((lo + m.start(), lo + m.end(), (m.group(1) or "") + rules.relmap[rel], "slash"))
    for m in DOT_RE.finditer(seg):
        tok = m.group(0)
        if seg[m.end(): m.end() + 1] == "/":
            continue  # 版の ID・形式の名(shibuya.<名>/…)
        if ctx.index.is_package(tok) and (tok in ctx.modmap or tok in ctx.heads_changed):
            # 〔検収 L-7〕包み(ディレクトリ)の名だけ: 中のファイルが 2 つ以上の包みへ分かれるので行き先が 1 つに決まらない
            skipped.append(("dotted_package", tok, "包みの名だけ=行き先が 1 つに決まらない(書き換えない=注意)"))
            continue
        new = dotted_new(ctx, tok)
        if new == tok:
            continue
        if tok in ctx.frozen_tokens:
            skipped.append(("dotted", tok, "凍結の名(クラスの凍結の名ほか)=書き換えない"))
            continue
        out.append((lo + m.start(), lo + m.end(), new, "dotted"))
    return out


def rewrite_value(ctx: Ctx, rules: PathRules, value: str) -> tuple[str, list[tuple[int, int, str, str]],
                                                                    list[tuple[str, str, str]]]:
    """文字列の値の書き換え(``paths`` の規則): 新しい値・書き換え(値の位置)・触らなかったもの(種類・字面・理由)。"""
    skipped: list[tuple[str, str, str]] = []
    reps: list[tuple[int, int, str, str]] = []
    code_spans: list[tuple[int, int]] = []
    is_code = False
    if ("import" in value) and ("shibuya" in value):
        try:
            tree = ast.parse(value)
        except SyntaxError:
            tree = None
        if tree is not None:
            nodes = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
            if nodes:
                is_code = True
                t = Text(value)
                st = IM.ImportStats()
                for ed in IM.rewrite_file(ctx, "<code>", value, tree, {}, st):
                    reps.append((ed.start, ed.end, ed.new, "code_import"))
                code_spans = sorted(t.span(n) for n in nodes)
    if not is_code and not value.isascii():
        tmp: list[tuple[str, str, str]] = []
        for _s, _e, _n, kind in _plain_reps(ctx, rules, value, 0, len(value), tmp):
            skipped.append((kind, value[_s:_e], "ASCII の外の字を含む文(記録の文)=書き換えない"))
        skipped += tmp
        return value, [], skipped
    cur = 0
    for s, e in [*code_spans, (len(value), len(value))]:
        if s > cur:
            reps += _plain_reps(ctx, rules, value, cur, s, skipped)
        cur = max(cur, e)
    reps.sort()
    out = []
    pos = 0
    for s, e, new, _k in reps:
        if s < pos:
            raise ValueError(f"文字列の中の書き換えが重なる: {value[:80]!r}")
        out.append(value[pos:s])
        out.append(new)
        pos = e
    out.append(value[pos:])
    return "".join(out), reps, skipped


def literal_source(text: Text, node: ast.Constant, old_value: str, new_value: str,
                   reps: list[tuple[int, int, str, str]]) -> str | None:
    """字面へ書き換えを同じ順に当てた新しい字面(値が合わなければ ``None``)。"""
    s, e = text.span(node)
    seg = text.text[s:e]
    try:
        if ast.literal_eval("(" + seg + "\n)") != old_value:
            return None
    except (SyntaxError, ValueError):
        return None
    out: list[str] = []
    cur = 0
    for rs, re_, new, _k in reps:
        old = old_value[rs:re_]
        i = seg.find(old, cur)
        if i < 0:
            return None
        out.append(seg[cur:i])
        out.append(new)
        cur = i + len(old)
    out.append(seg[cur:])
    new_seg = "".join(out)
    try:
        ok = ast.literal_eval("(" + new_seg + "\n)") == new_value
    except (SyntaxError, ValueError):
        return None
    return new_seg if ok else None


def _chain_ops(n: ast.BinOp) -> list[ast.expr]:
    ops: list[ast.expr] = []
    cur: ast.expr = n
    while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Div):
        ops.append(cur.right)
        cur = cur.left
    ops.append(cur)
    ops.reverse()
    return ops


def chain_edits(text: Text, tree: ast.Module, rules: PathRules, symbols: dict[int, str], allowed: set[str] | None,
                path: str, stats: StrStats) -> list[Edit]:
    """``X / "engine" / "clock.py"`` の連なりのうち、道が 2 つ以上の定数にまたがるもの。"""
    par = _parents(tree)
    out: list[Edit] = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div)):
            continue
        p = par.get(id(n))
        if isinstance(p, ast.BinOp) and isinstance(p.op, ast.Div) and p.left is n:
            continue  # 連なりの頂だけを見る
        sym = symbols.get(id(n), "")
        ops = _chain_ops(n)
        runs: list[list[ast.Constant]] = []
        cur: list[ast.Constant] = []
        for o in ops:
            if isinstance(o, ast.Constant) and isinstance(o.value, str):
                cur.append(o)
            else:
                if cur:
                    runs.append(cur)
                cur = []
        if cur:
            runs.append(cur)
        for run in runs:
            if len(run) < 2:
                continue
            comps: list[tuple[int, str]] = []  # (定数の番号, 部品)
            for i, c in enumerate(run):
                comps += [(i, x) for x in c.value.split("/") if x]
            joined = "/".join(x for _, x in comps)
            hit = next((r for r in rules.relmap if joined == r or joined.endswith("/" + r)), None)
            if hit is None:
                continue
            k = len(comps) - len(hit.split("/"))
            ci = comps[k][0]
            first = run[ci]
            if ci == len(run) - 1:
                continue  # 道が 1 つの定数に入る=斜線の道の規則が受け持つ
            if allowed is not None and sym not in allowed:
                continue
            if k > 0 and comps[k - 1][0] == ci:
                stats.skipped.append({"file": path, "symbol": sym, "kind": "chain", "token": joined,
                                      "reason": "道の頭が定数の途中から始まる=書き換えない"})
                continue
            s, _ = text.span(first)
            _, e = text.span(run[-1])
            seg = text.text[s:e]
            if "\n" in seg or "\r" in seg or "#" in seg:
                stats.skipped.append({"file": path, "symbol": sym, "kind": "chain", "token": joined,
                                      "reason": "連なりが行をまたぐか注を含む=書き換えない"})
                continue
            qch = seg[0] if seg[0] in "'\"" else '"'
            new = " / ".join(f"{qch}{x}{qch}" for x in rules.relmap[hit].split("/"))
            out.append(Edit(s, e, new, "path", sym, f"chain {joined}"))
            stats.rewritten["chain"] += 1
            stats.sites[(path, sym)] += 1
    return out


def rewrite_file_strings(ctx: Ctx, rules: PathRules, path: str, text: str, tree: ast.Module, symbols: dict[int, str],
                         rule_of: dict[str, str], stats: StrStats, *, scan_all: bool = False) -> list[Edit]:
    """1 本のファイルの許可の一覧の記号の中の文字列の書き換え。``rule_of``: 記号 → 規則(``exact``・``paths``)。
    ``scan_all`` なら全部の記号を ``paths`` で見る(許可の一覧を作る走査)。"""
    t = Text(text)
    ds = docstrings_of(text)
    par = _parents(tree)
    edits: list[Edit] = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Constant) and isinstance(n.value, str)) or id(n) in ds:
            continue
        sym = symbols.get(id(n), "")
        rule = "paths" if scan_all else rule_of.get(sym)
        if rule is None:
            continue
        if isinstance(par.get(id(n)), ast.JoinedStr):
            if rule == "paths" and (SLASH_RE.search(n.value) or DOT_RE.search(n.value)):
                stats.skipped.append({"file": path, "symbol": sym, "kind": "fstring", "token": n.value[:80],
                                      "reason": "f 文字列の部分=書き換えない"})
            continue
        if rule == "exact":
            new_rel = rules.relmap.get(n.value)
            if new_rel is None and n.value.startswith("src/shibuya/") and n.value[12:] in rules.relmap:
                new_rel = "src/shibuya/" + rules.relmap[n.value[12:]]  # 〔親の決定 2〕リポの根からの道の形
            if new_rel is None:
                continue
            reps = [(0, len(n.value), new_rel, "src_table")]
            new_value = new_rel
            skipped: list[tuple[str, str, str]] = []
        else:
            new_value, reps, skipped = rewrite_value(ctx, rules, n.value)
        for kind, tok, why in skipped:
            stats.skipped.append({"file": path, "symbol": sym, "kind": kind, "token": tok, "reason": why})
        if new_value == n.value:
            continue
        seg = literal_source(t, n, n.value, new_value, reps)
        if seg is None:
            stats.skipped.append({"file": path, "symbol": sym, "kind": "literal", "token": n.value[:80],
                                  "reason": "字面へ当てられない(エスケープほか)=書き換えない"})
            continue
        s, e = t.span(n)
        edits.append(Edit(s, e, seg, "path", sym, ",".join(sorted({k for *_x, k in reps}))))
        for *_x, k in reps:
            stats.rewritten[k] += 1
        stats.sites[(path, sym)] += 1
    edits += chain_edits(t, tree, rules, symbols, None if scan_all else {s for s, r in rule_of.items() if r == "paths"},
                         path, stats)
    return edits


# ------------------------------------------------------------------ 触らなかった道の形の文字列の拾い(報告だけ)
def untouched_in_file(ctx: Ctx, rules: PathRules, path: str, text: str, tree: ast.Module, symbols: dict[int, str],
                      skip_symbols: set[str]) -> tuple[list[dict], int]:
    """許可の一覧の外の文字列の定数のうち、移すモジュールの道の形を含むもの(ファイル・記号・種類・字面)と、
    どのモジュールでも道の形を含む定数の数(広い数え)。"""
    ds = docstrings_of(text)
    out: list[dict] = []
    broad = 0
    ix = ctx.index
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Constant) and isinstance(n.value, str)) or id(n) in ds:
            continue
        sym = symbols.get(id(n), "")
        if sym in skip_symbols:
            continue
        v = n.value
        kinds: list[tuple[str, str]] = []
        any_shape = False
        for m in SLASH_RE.finditer(v):
            if m.group(2) in rules.relmap:
                kinds.append(("slash", m.group(0)))
            if ix.exists(_mod_from_rel(m.group(2))):
                any_shape = True
        for m in DOT_RE.finditer(v):
            if v[m.end(): m.end() + 1] == "/":
                continue
            L = ix.longest_module(m.group(0))
            if L is not None and L != "shibuya":
                any_shape = True
                if dotted_new(ctx, m.group(0)) != m.group(0):
                    kinds.append(("dotted", m.group(0)))
        for m in BARE_DOT_RE.finditer(v):
            L = ix.longest_module("shibuya." + m.group(0))
            if L is not None and L != "shibuya" and L.count(".") >= 2:
                any_shape = True
                if L in ctx.modmap or dotted_new(ctx, "shibuya." + m.group(0)) != "shibuya." + m.group(0):
                    kinds.append(("bare_dotted", m.group(0)))
        broad += int(any_shape)
        for k, tok in kinds:
            out.append({"file": path, "symbol": sym, "kind": k, "token": tok,
                        "line": getattr(n, "lineno", 0), "excerpt": v[:120]})
    return out, broad


def _mod_from_rel(rel: str) -> str:
    if not rel.endswith(".py"):
        return ""
    parts = rel[:-3].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(["shibuya", *parts])
