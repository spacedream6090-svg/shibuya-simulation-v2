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

〔割る段 5a〕割るファイル(``PathRules.names``)の道は、既定で主な割り先(``relmap``)へ。ただし文字列の全体が割るファイルの道で、
同じ組(タプル・リスト・呼び出しの引数)に割るファイルの頂上の名(``関数``・``クラス.メソッド`` の頭)の文字列があれば、その名の
割り先へ(計画 c9=乱数の検査の ``(道, 関数, 用途名)`` など)。組の名が 2 つの割り先を指せば書き換えずに報告する。点の道は
名の単位の写像(``Ctx.namemap``)で、名が無ければ主な割り先(``Ctx.split_main``)へ。

〔割る段 5b・E2・E3〕割るモジュールの名だけの点の道(名の無い点の道=``"shibuya.engine.run"``)は、主な割り先へ黙って向けない
(:func:`split_nameless`): 入口の転送を残すモジュール(``Ctx.split_forwarders``)は書き換えない・``-m`` の文脈(文字列の中の
``-m <名>``・並びや呼び出しの引数で 1 つ前の要素が ``"-m"``)なら入口の割り先(``Ctx.split_entry``)へ・それ以外は書き換えずに
「手で直す」(注意の頭 :data:`pkgmove.imports.MANUAL`)。

〔割る段 5b の G0 の直し〕高-1: ``tests/_places.py`` の割る行の口(:data:`TABLE_KEY_CALLS`)の第 1 引数は対応表の鍵(元の道=値
そのもの)なので書き換えない(:func:`is_table_key`)。高-2: 文字列の中のコード(子のプロセスの台本・シェルの文)の
``from <包み> import <割るモジュール>`` の形を拾い(:func:`code_import_hits`)、コードとして読めれば import の書き換え(別名の
割り先が 1 つなら機械で・決まらなければ手で直す)へ、読めなければ「手で直す」へ出す。f 文字列の部分の中のものも「手で直す」。

〔割る段 6・E8・親の裁定 Q8〕道の文字列の割り先の宣言(``PathRules.declared``=(ファイル, 記号) → 割り先・割る道具の
``split.SPLIT_PATH_DESTS``)。割るファイルの道(斜線の道・``/`` の連鎖・名の無い点の道)の行き先は、宣言 → 同じ組の名 →(割り先が
1 つの行なら)主な割り先、の順(:func:`split_path_dest`)。宣言も名の手がかりも無く、割り先が 2 つ以上の行
(``PathRules.nameless_manual``)の道は、主な割り先へ黙って向けず「手で直す」。宣言と組の名が食い違えば「手で直す」。使った宣言は
``StrStats.declared_used`` に数える(使われなかった宣言は割る道具が止める)。
"""
from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass, field, replace

from pkgmove import imports as IM
from pkgmove.model import Ctx, Edit, Text, docstrings_of, mod_of

SLASH_RE = re.compile(r"(?<![\w./\\-])((?:src/)?shibuya/)?((?:[A-Za-z_]\w*/)+[A-Za-z_]\w*\.(?:py|json))(?![\w/])")
DOT_RE = re.compile(r"(?<![\w.])shibuya(?:\.[A-Za-z_]\w*)+")
#: 包みの名で始まる点の名(``shibuya.`` の無い形=乱数の用途名・manifest の文など。拾いの報告だけ)。
BARE_DOT_RE = re.compile(r"(?<![\w.])(?:agents|census|core|economy|engine|llm|manifest|perception|world)(?:\.[A-Za-z_]\w*)+")


@dataclass
class PathRules:
    """移すファイルの道(``src/shibuya`` からの相対)。"""

    relmap: dict[str, str]
    #: 〔割る段 5a〕割るファイルの道 → {頂上の名 → 割り先の道}(同じ組の名で割り先を選ぶ)。
    names: dict[str, dict[str, str]] = field(default_factory=dict)
    #: 〔割る段 6・E8〕(ファイル, 記号) → 割り先の道(その記号の中の、名の手がかりの無い割るファイルの道の行き先)。
    declared: dict[tuple[str, str], str] = field(default_factory=dict)
    #: 〔割る段 6・E8〕宣言も名の手がかりも無い道を主な割り先へ向けず「手で直す」にする割るファイル(割り先が 2 つ以上の行)。
    nameless_manual: frozenset[str] = frozenset()


@dataclass
class StrStats:
    rewritten: Counter = field(default_factory=Counter)
    sites: Counter = field(default_factory=Counter)
    skipped: list[dict] = field(default_factory=list)
    #: 〔割る段 6・E8〕使った道の文字列の割り先の宣言((ファイル, 記号) → 当てた道の数)。
    declared_used: Counter = field(default_factory=Counter)


#: 〔割る段 6・E8〕「手で直す」に出した割るファイルの道の種類(斜線の道の全体・文の中の斜線の道・``/`` の連鎖)。
SPLIT_NAMELESS = "split_nameless"
SLASH_NAMELESS = "slash_nameless"
CHAIN_NAMELESS = "chain_nameless"


def split_path_dest(rules: PathRules, path: str, sym: str, rel: str, sib: str | None = None
                    ) -> tuple[str | None, str | None, bool]:
    """〔割る段 6・E8〕割るファイル ``rel`` の道の行き先: (割り先の道か ``None``=書き換えない, 手で直す理由か ``None``, 宣言を
    引いたか)。宣言(``(path, sym)``)→ 同じ組の名(``sib``)→ 割り先が 1 つの行なら主な割り先(``relmap``・元が主な割り先なら
    ``None``=そのまま)、の順。宣言と組の名が食い違えば手で直す(宣言は引いた=使われなかったとは言わない)。宣言も名の
    手がかりも無く、割り先が 2 つ以上の行なら手で直す。"""
    decl = rules.declared.get((path, sym))
    if decl is not None:
        if sib is not None and sib != decl:
            return None, (f"{IM.MANUAL} 割るファイルの道 {rel} の宣言の割り先 {decl} と、同じ組の名の割り先 {sib} が"
                          f"食い違う"), True
        return decl, None, True
    if sib is not None:
        return sib, None, False
    if rel in rules.nameless_manual:
        return None, _nameless_reason(rel), False
    return rules.relmap.get(rel), None, False


def _nameless_reason(rel: str) -> str:
    return (f"{IM.MANUAL} 名の手がかりの無い割るファイルの道 {rel}(割り先が 2 つ以上・道の文字列の割り先の宣言"
            f"(split.SPLIT_PATH_DESTS)が無い=主な割り先へ黙って向けない)")


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
    if L in ctx.namemap:  # 〔割る段 5a〕割るモジュール: 名の割り先へ・名が無ければ主な割り先へ
        if rest and rest[0] in ctx.namemap[L]:
            return ctx.namemap[L][rest[0]] + tail
        return ctx.split_main.get(L, L) + tail
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


_M_BEFORE_RE = re.compile(r"(?:^|\s)-m\s*$")
#: 〔割る段 5b の G0 の直し 高-1〕対応表の割る行の鍵(元の道)を第 1 引数に取る試験の補助(``tests/_places.py``)の口。鍵は表の値
#: そのもの(割った後も元の道のまま=``STRING_EXCLUDE`` の固定の一覧と同じ見方)なので、割る道具は書き換えない。呼び出しの形で
#: 見る(新しい試験の鍵も黙って漏れない)。
TABLE_KEY_CALLS: frozenset[str] = frozenset({"split_files", "split_source", "split_module_names", "_split_names"})
_FROM_IMPORT_RE = re.compile(r"\bfrom\s+([A-Za-z_][\w.]*)\s+import\s+\(?\s*([A-Za-z_][\w \t,]*)")
_IMPORT_RE = re.compile(r"\bimport\s+([A-Za-z_][\w.]*)")


def is_table_key(par: dict[int, ast.AST], n: ast.Constant) -> bool:
    """〔割る段 5b の G0 の直し 高-1〕文字列 ``n`` が :data:`TABLE_KEY_CALLS` の呼び出しの第 1 引数(か ``old=``)か。"""
    p = par.get(id(n))
    if not isinstance(p, ast.Call):
        return False
    f = p.func
    name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
    if name not in TABLE_KEY_CALLS:
        return False
    return bool(p.args and p.args[0] is n) or any(k.arg == "old" and k.value is n for k in p.keywords)


def code_import_hits(ctx: Ctx, value: str) -> list[str]:
    """〔割る段 5b の G0 の直し 高-2〕文字列の中のコードが割るモジュール(``Ctx.namemap``)を読む import(``from <包み> import
    <葉>``・``from <モジュール> import <名>``・``import <モジュール>``)。コードとして読めればその import の文で、読めなければ
    字面の形で探す(子のプロセスに渡す台本・シェルの文の中のコード)。前は点の道と斜線の道の字面だけで文字列を選んだので、
    ``"from shibuya import cli; …"`` の形を書き換えも「手で直す一覧」へも出さずに残した。"""
    if not ctx.namemap or "import" not in value:
        return []
    mods = set(ctx.namemap)
    out: list[str] = []

    def hit_from(mod: str, names: list[str]) -> None:
        if mod in mods:  # 割るモジュールから名を読む
            out.append(f"from {mod} import {', '.join(names)}")
            return
        out.extend(f"from {mod} import {a}" for a in names if f"{mod}.{a}" in mods)  # 包みから割るモジュールを読む

    try:
        tree = ast.parse(value)
    except SyntaxError:
        tree = None
    if tree is not None:
        for x in ast.walk(tree):
            if isinstance(x, ast.ImportFrom) and x.level == 0 and x.module:
                hit_from(x.module, [a.name for a in x.names])
            elif isinstance(x, ast.Import):
                out += [f"import {a.name}" for a in x.names if a.name in mods or any(a.name.startswith(m + ".") for m in mods)]
        return out
    for m in _FROM_IMPORT_RE.finditer(value):
        hit_from(m.group(1), [p.split()[0] for p in m.group(2).split(",") if p.split()])
    for m in _IMPORT_RE.finditer(value):
        if m.group(1) in mods or any(m.group(1).startswith(s + ".") for s in mods):
            out.append(f"import {m.group(1)}")
    return out


def split_nameless(ctx: Ctx, tok: str, m_context: bool, declared: str | None = None
                   ) -> tuple[str | None, tuple[str, str, str] | None]:
    """〔割る段 5b・E2・E3〕割るモジュールの名の無い点の道 ``tok`` の行き先: (新しい字面か ``None``, 触らなかった印か ``None``)。
    転送を残すモジュールは書き換えない・``-m`` の文脈なら入口の割り先・それ以外は主な割り先へ黙って向けず「手で直す」。
    〔割る段 6・E8〕``-m`` の入口でなく、その記号に道の文字列の割り先の宣言(``declared``=割り先のモジュールの名)があればそこへ。"""
    if tok in ctx.split_forwarders:
        return None, ("dotted_forwarder", tok, "入口の転送の名(転送が残り -m で動き続ける)=書き換えない")
    if m_context and tok in ctx.split_entry:
        return ctx.split_entry[tok], None
    if declared is not None:
        return declared, None
    why = "-m の文脈だが入口の割り先の宣言が無い" if m_context else "-m の文脈でない"
    return None, ("dotted_nameless", tok, f"{IM.MANUAL} 名の無い点の道 {tok}(割るモジュール・{why}=主な割り先へ黙って向けない)")


def _plain_reps(ctx: Ctx, rules: PathRules, value: str, lo: int, hi: int,
                skipped: list[tuple[str, str, str]], *, after_m: bool = False, declared: str | None = None,
                used: list[str] | None = None) -> list[tuple[int, int, str, str]]:
    """値の ``lo``〜``hi`` の斜線の道と点の道の書き換え: (始め, 終わり, 新しい字面, 種類)。``after_m``: 値の全体が ``-m`` の
    次の要素(並びや呼び出しの引数で 1 つ前が ``"-m"``)。〔割る段 6・E8〕``declared`` はその記号の道の文字列の割り先の宣言(割り先の
    道)。割るファイルの道(名の手がかりの無い形)は宣言へ・宣言が無く割り先が 2 つ以上の行なら「手で直す」。宣言を当てたら
    ``used`` に足す。"""
    out: list[tuple[int, int, str, str]] = []
    seg = value[lo:hi]
    for m in SLASH_RE.finditer(seg):
        rel = m.group(2)
        if rel in rules.names:  # 〔割る段 6・E8〕割るファイルの道(文の中の斜線の道=組の名の手がかりは無い)
            if declared is not None:
                out.append((lo + m.start(), lo + m.end(), (m.group(1) or "") + declared, "slash"))
                if used is not None:
                    used.append(rel)
            elif rel in rules.nameless_manual:
                skipped.append((SLASH_NAMELESS, m.group(0), _nameless_reason(rel)))
            elif rel in rules.relmap:
                out.append((lo + m.start(), lo + m.end(), (m.group(1) or "") + rules.relmap[rel], "slash"))
            continue
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
        if tok in ctx.namemap and ctx.index.longest_module(tok) == tok:  # 〔割る段 5b・E2・E3〕名の無い点の道
            if tok in ctx.frozen_tokens:
                skipped.append(("dotted", tok, "凍結の名(クラスの凍結の名ほか)=書き換えない"))
                continue
            s, e = lo + m.start(), lo + m.end()
            m_ctx = (after_m and s == 0 and e == len(value)) or bool(_M_BEFORE_RE.search(value[:s]))
            dmod = mod_of(declared) if declared is not None else None
            new, sk = split_nameless(ctx, tok, m_ctx, dmod)
            if sk is not None:
                skipped.append(sk)
            if new is not None:
                out.append((s, e, new, "dotted_entry"))
                if new == dmod and not (m_ctx and tok in ctx.split_entry) and used is not None:
                    used.append(tok)  # 〔割る段 6・E8〕宣言の割り先へ向けた
            continue
        new = dotted_new(ctx, tok)
        if new == tok:
            continue
        if tok in ctx.frozen_tokens:
            skipped.append(("dotted", tok, "凍結の名(クラスの凍結の名ほか)=書き換えない"))
            continue
        out.append((lo + m.start(), lo + m.end(), new, "dotted"))
    return out


def rewrite_value(ctx: Ctx, rules: PathRules, value: str, *, after_m: bool = False, declared: str | None = None,
                  used: list[str] | None = None
                  ) -> tuple[str, list[tuple[int, int, str, str]], list[tuple[str, str, str]]]:
    """文字列の値の書き換え(``paths`` の規則): 新しい値・書き換え(値の位置)・触らなかったもの(種類・字面・理由)。
    ``after_m``: 値の全体が ``-m`` の次の要素(〔割る段 5b・E3〕)。``declared``・``used``: 〔割る段 6・E8〕その記号の道の文字列の
    割り先の宣言と、当てた道を足す並び(:func:`_plain_reps`)。"""
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
                saved = ctx.alias_dests
                if ctx.namemap:  # 〔割る段 5a〕コードの文字列の中の別名は、その文字列の中の読みで割り先を引く
                    ctx.alias_dests = IM.alias_dests(ctx, value, "<code>")
                try:
                    for ed in IM.rewrite_file(ctx, "<code>", value, tree, {}, st):
                        reps.append((ed.start, ed.end, ed.new, "code_import"))
                finally:
                    ctx.alias_dests = saved
                for w in st.warnings:
                    if IM.MANUAL in w:
                        skipped.append(("code_import", value[:80], w))
                code_spans = sorted(t.span(n) for n in nodes)
    if not is_code and ctx.namemap:  # 〔割る段 5b の G0 の直し 高-2〕コードとして読めない文字列の中の import(シェルの文ほか)
        hits = code_import_hits(ctx, value)
        if hits:
            skipped.append(("code_import_text", value[:80], f"{IM.MANUAL} コードとして読めない文字列の中の import が割る"
                                                           f"モジュールを読む({', '.join(hits)})=書き換えられない"))
    if not is_code and not value.isascii():
        tmp: list[tuple[str, str, str]] = []
        for _s, _e, _n, kind in _plain_reps(ctx, rules, value, 0, len(value), tmp, after_m=after_m):
            skipped.append((kind, value[_s:_e], "ASCII の外の字を含む文(記録の文)=書き換えない"))
        # 記録の文の中の名の無い点の道と、〔割る段 6・E8〕名の手がかりの無い割るファイルの斜線の道は手で直す一覧に入れない(5a と
        # 同じく記録の文は書き換えない)
        skipped += [(k, tok, "ASCII の外の字を含む文(記録の文)=書き換えない") if k in ("dotted_nameless", SLASH_NAMELESS)
                    else (k, tok, why) for k, tok, why in tmp]
        return value, [], skipped
    cur = 0
    for s, e in [*code_spans, (len(value), len(value))]:
        if s > cur:
            reps += _plain_reps(ctx, rules, value, cur, s, skipped, after_m=after_m, declared=declared, used=used)
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


def _after_m(par: dict[int, ast.AST], n: ast.Constant) -> bool:
    """〔割る段 5b・E3〕文字列 ``n`` が並び(リスト・タプル)か呼び出しの位置引数の要素で、1 つ前の要素が ``"-m"`` か。"""
    p = par.get(id(n))
    if isinstance(p, (ast.List, ast.Tuple)):
        elts: list[ast.AST] = list(p.elts)
    elif isinstance(p, ast.Call):
        elts = list(p.args)
    else:
        return False
    i = next((k for k, e in enumerate(elts) if e is n), -1)
    prev = elts[i - 1] if i > 0 else None
    return isinstance(prev, ast.Constant) and prev.value == "-m"


def sibling_dest(par: dict[int, ast.AST], n: ast.Constant, rules: PathRules, rel: str) -> str | None:
    """〔割る段 5a〕全体が割るファイルの道 ``rel`` の文字列 ``n`` の、同じ組の中の頂上の名が指す割り先(無ければ ``None``)。
    組の中の名が 2 つの割り先を指せば ``ValueError``。"""
    names = rules.names.get(rel)
    p = par.get(id(n))
    if not names or p is None:
        return None
    if isinstance(p, (ast.Tuple, ast.List)):
        elts: list[ast.AST] = list(p.elts)
    elif isinstance(p, ast.Call):
        elts = [*p.args, *[k.value for k in p.keywords]]
    else:
        return None
    found: set[str] = set()
    stack = [e for e in elts if e is not n]
    while stack:
        e = stack.pop()
        if isinstance(e, ast.Constant) and isinstance(e.value, str):
            head = e.value.split(".")[0]
            if head in names:
                found.add(names[head])
        elif isinstance(e, (ast.Tuple, ast.List)):
            stack += list(e.elts)
    if len(found) > 1:
        raise ValueError(f"組の中の名が 2 つの割り先を指す: {rel} → {sorted(found)}")
    return found.pop() if found else None


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
            cands = [*rules.relmap, *[r for r in rules.names if r not in rules.relmap]]  # 〔割る段 6・E8〕元が主な割り先の行も
            hit = next((r for r in cands if joined == r or joined.endswith("/" + r)), None)
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
            if hit in rules.names:  # 〔割る段 6・E8〕割るファイルの連鎖(組の名の手がかりは無い)=宣言か、手で直すか、主な割り先
                dest, why, by_decl = split_path_dest(rules, path, sym, hit)
                if by_decl:
                    stats.declared_used[(path, sym)] += 1
                if why is not None:
                    stats.skipped.append({"file": path, "symbol": sym, "kind": CHAIN_NAMELESS, "token": joined,
                                          "reason": why})
                    continue
                if dest is None:
                    continue
            else:
                dest = rules.relmap[hit]
            qch = seg[0] if seg[0] in "'\"" else '"'
            new = " / ".join(f"{qch}{x}{qch}" for x in dest.split("/"))
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
            hits = code_import_hits(ctx, n.value) if rule == "paths" else []
            if hits:  # 〔割る段 5b の G0 の直し 高-2〕f 文字列の中のコードが割るモジュールを読む=黙って残さない
                stats.skipped.append({"file": path, "symbol": sym, "kind": "fstring_code_import", "token": n.value[:80],
                                      "reason": f"{IM.MANUAL} f 文字列の部分の中のコードが割るモジュールを読む"
                                                f"({', '.join(hits)})=書き換えられない"})
            elif rule == "paths" and (SLASH_RE.search(n.value) or DOT_RE.search(n.value)):
                stats.skipped.append({"file": path, "symbol": sym, "kind": "fstring", "token": n.value[:80],
                                      "reason": "f 文字列の部分=書き換えない"})
            continue
        if ctx.namemap and is_table_key(par, n):  # 〔割る段 5b の G0 の直し 高-1〕対応表の割る行の鍵=値そのもの
            stats.skipped.append({"file": path, "symbol": sym, "kind": "table_key", "token": n.value[:80],
                                  "reason": "対応表の割る行の鍵(元の道=値そのもの・tests/_places の割る行の口の第 1 引数)"
                                            "=書き換えない"})
            continue
        whole = n.value[12:] if n.value.startswith("src/shibuya/") else n.value
        sib = None
        dest_whole: str | None = None
        used: list[str] = []
        if whole in rules.names:  # 〔割る段 5a〕割るファイルの道=同じ組の名の割り先(無ければ主な割り先)
            try:
                sib = sibling_dest(par, n, rules, whole)
            except ValueError as e:
                stats.skipped.append({"file": path, "symbol": sym, "kind": "split_sibling", "token": n.value[:80],
                                      "reason": f"{e}=書き換えない"})
                continue
            # 〔割る段 6・E8〕宣言 → 組の名 → (割り先が 1 つの行なら)主な割り先。宣言も名の手がかりも無ければ手で直す
            dest_whole, why, by_decl = split_path_dest(rules, path, sym, whole, sib)
            if why is not None:
                if by_decl:  # 宣言と組の名が食い違う=宣言は引いた(使われなかったとは言わない)・手で直す一覧へ
                    stats.declared_used[(path, sym)] += 1
                stats.skipped.append({"file": path, "symbol": sym, "kind": SPLIT_NAMELESS, "token": n.value[:80],
                                      "reason": why})
                continue
            if by_decl:
                used.append(whole)
        if rule == "exact":
            if whole in rules.names:
                new_rel = None if dest_whole is None else (dest_whole if n.value == whole else "src/shibuya/" + dest_whole)
            else:
                new_rel = rules.relmap.get(n.value)
                if new_rel is None and n.value.startswith("src/shibuya/") and n.value[12:] in rules.relmap:
                    new_rel = "src/shibuya/" + rules.relmap[n.value[12:]]  # 〔親の決定 2〕リポの根からの道の形
            if used:
                stats.declared_used[(path, sym)] += len(used)
            if new_rel is None:
                continue
            reps = [(0, len(n.value), new_rel, "src_table")]
            new_value = new_rel
            skipped: list[tuple[str, str, str]] = []
        else:
            if whole in rules.names:  # 全体が割るファイルの道=上で決めた行き先へ(宣言と手で直す判定は済み)
                r2 = replace(rules, relmap={**rules.relmap, **({whole: dest_whole} if dest_whole is not None else {})},
                             declared={}, nameless_manual=rules.nameless_manual - {whole})
                decl = None
            else:
                r2 = rules
                decl = rules.declared.get((path, sym))
            # 〔割る段 6・E8〕宣言の口は宣言のある記号でだけ渡す(無ければ前と同じ呼び方=試験の差し替えの口もそのまま)
            kw: dict = {"declared": decl, "used": used} if decl is not None else {}
            if ctx.namemap and _after_m(par, n):  # 〔割る段 5b・E3〕並びの 1 つ前が "-m"
                new_value, reps, skipped = rewrite_value(ctx, r2, n.value, after_m=True, **kw)
            else:
                new_value, reps, skipped = rewrite_value(ctx, r2, n.value, **kw)
            if used:
                stats.declared_used[(path, sym)] += len(used)
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
