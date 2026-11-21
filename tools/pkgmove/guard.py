# -*- coding: utf-8 -*-
"""凍結の値の守りと、許可の一覧の外が変わらないことの確かめ(書き換えた後の木で。1 つでも当たれば書かずに止める)。

1. ``names_frozen``: ``tests/engine/state/names_frozen.json`` の静的な欄(乱数の領域の名の 3 つの表の鍵・道の形の領域の名と
   接尾とほかの名のランの側の src に出てくる数・版の ID とハッシュの見出しの多重集合)を、書き換えた後の src から集め直して比べる
   (集め方は ``docs/bench/analysis/move-346/tools/gen_frozen_names.py`` と同じ形の別の実装=手元の木の文字列から)。
2. ``class_ids``: 書き換えた後の固定の表の値と置き場の宣言(``CLASS_ID``)が凍結の JSON の写像(凍結の名 → ``__qualname__``)と
   同じ・表の鍵とクラスの宣言(src の AST の全部のクラス=build を除く)が 1 対 1(網羅)。
3. ``shaped``: ランから拾った道の形の名 74 種(凍結 ``run_path_shaped``)が、ランの側の src の文字列の定数(許可の一覧の
   記号と固定の表の鍵を除く)に出てくる数が前と同じ。
4. ``outside``: 許可の一覧の外の文字列とバイト列の定数(docstring を含む)が、ファイルごとに 1 つも変わらない(移したファイルは
   古い道と新しい道で比べる)。docstring は許可の一覧の記号の中でも比べる。許可の一覧の中でも、凍結の値(クラスの凍結の名・乱数の用途名・接尾・版の ID・見出し・ほかの名・
   点の形の 74 種)を含む定数は変わらない。空にした頭・消した頭は比べない(別に一覧にする)。
5. ``head_all``(親の裁定 review3 の 2): 空にしない頭の ``__all__`` の名は、全部その頭で結ばれている(定義・代入・import・
   子のモジュール)。頭から再輸出を除いた段では、``__all__`` は「前の ``__all__`` から除いた名を抜いたもの」と同じ。
"""
from __future__ import annotations

import ast
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterable

from pkgmove.model import SRC_PREFIX, Tree, _top_statements, docstrings_of, mod_of, parse, symbols_of

NAMES_FROZEN_REL = "tests/engine/state/names_frozen.json"
CLASS_FROZEN_REL = "tests/engine/state/class_ids_frozen.json"
TABLES = ("POPULATION_RNG_DOMAINS", "ENVIRONMENT_RNG_DOMAINS", "MOTION_RNG_DOMAINS")
SUFFIX_NAMES = ("_MOVE_TARGET_DOMAIN_SUFFIX", "_SHOP_TARGET_DOMAIN_SUFFIX")
VERSION_RE = re.compile(r"^shibuya\.[A-Za-z0-9_.]+/")


@dataclass
class Frozen:
    """凍結の値(2 本の JSON)。"""

    names: dict
    class_qual: dict[str, str]

    @classmethod
    def load(cls, read) -> "Frozen":
        return cls(names=json.loads(read(NAMES_FROZEN_REL)), class_qual=json.loads(read(CLASS_FROZEN_REL))["names"])

    def shaped_kinds(self) -> list[str]:
        runs = self.names.get("run_path_shaped", {})
        return sorted({k for d in runs.values() for v in d.values() for k in v})

    def id_tokens(self) -> set[str]:
        """書き換えてはいけない ID の字面(クラスの凍結の名・乱数の用途名・接尾・版の ID・見出し・ほかの名・点の形の 74 種)。"""
        n = self.names
        out = set(self.class_qual)
        out |= {k for v in n["rng_domains"].values() for k in v}
        out |= set(n["rng_domain_suffixes"]) | set(n["other_path_shaped"])
        vids = {v for _k, v in n["version_ids"]}
        out |= vids | set(n["hash_headers"])
        # 点の形の 74 種。ただし版の ID の頭(``shibuya.engine.batching`` ← ``shibuya.engine.batching/…``)は、ID としては
        # 後ろに ``/`` が続く形だけが凍結(版の ID の多重集合で守る)で、同じ字面のモジュールの名は移す道具が書き換える。
        out |= {k for k in self.shaped_kinds()
                if "/" not in k and not any(v.startswith(k + "/") for v in vids)}
        return {x for x in out if x}


@dataclass
class GuardReport:
    errors: list[str] = field(default_factory=list)
    checked: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


@lru_cache(maxsize=8192)
def _consts(text: str) -> tuple[str | bytes, ...]:
    tree = parse(text)
    ds = docstrings_of(text)
    return tuple(n.value for n in ast.walk(tree)
                 if isinstance(n, ast.Constant) and isinstance(n.value, (str, bytes)) and id(n) not in ds)


def _src_files(tree: Tree, *, build: bool) -> list[str]:
    return sorted(p for p in tree.files if p.startswith(SRC_PREFIX) and (build or not p.startswith(SRC_PREFIX + "build/")))


def _table_keys(tree: Tree, files: list[str], name: str) -> list[str]:
    found: list[list[str]] = []
    for p in files:
        for n in parse(tree.files[p]).body:
            tgt = n.target if isinstance(n, ast.AnnAssign) else (n.targets[0] if isinstance(n, ast.Assign) else None)
            if isinstance(tgt, ast.Name) and tgt.id == name:
                d = n.value.args[0] if isinstance(n.value, ast.Call) else n.value
                found.append([ast.literal_eval(k) for k in d.keys])  # type: ignore[union-attr]
    if len(found) != 1:
        raise ValueError(f"{name} の定義が {len(found)} 個")
    return sorted(found[0])


def collect_names(tree: Tree, frozen: Frozen) -> dict:
    """``names_frozen.json`` の静的な欄を木から集める(道の形の領域の名は凍結の鍵ごとの数)。"""
    run_side = _src_files(tree, build=False)
    every = _src_files(tree, build=True)
    tables = {t: _table_keys(tree, run_side, t) for t in TABLES}
    run_count: Counter = Counter()
    for p in run_side:
        run_count.update(c for c in _consts(tree.files[p]) if isinstance(c, str))
    consts_all: list[str | bytes] = []
    for p in every:
        consts_all += list(_consts(tree.files[p]))
    suffix: dict[str, str] = {}
    for p in run_side:
        for n in parse(tree.files[p]).body:
            tgt = n.target if isinstance(n, ast.AnnAssign) else (n.targets[0] if isinstance(n, ast.Assign) else None)
            if isinstance(tgt, ast.Name) and tgt.id in SUFFIX_NAMES:
                suffix[tgt.id] = ast.literal_eval(n.value)  # type: ignore[arg-type]
    vids = sorted([["b", c.decode("utf-8")] if isinstance(c, bytes) else ["s", c] for c in consts_all
                   if (isinstance(c, bytes) and re.match(rb"^shibuya\.[A-Za-z0-9_.]+/", c))
                   or (isinstance(c, str) and VERSION_RE.match(c))])
    heads = sorted(c.decode("utf-8") for c in consts_all if isinstance(c, bytes) and c.startswith(b"shibuya."))
    return {
        "rng_domains": tables,
        "rng_domains_path_shaped": {k: run_count[k] for k in frozen.names["rng_domains_path_shaped"]},
        "rng_domain_suffixes": {s: run_count[s] for s in sorted(suffix.values())},
        "version_ids": vids,
        "hash_headers": heads,
        "other_path_shaped": {v: run_count[v] for v in frozen.names["other_path_shaped"]},
    }


def check_names(tree: Tree, frozen: Frozen) -> list[str]:
    got = collect_names(tree, frozen)
    return [f"names_frozen の {k} が凍結と違う" for k, v in got.items() if v != frozen.names.get(k)]


def check_class_ids(tree: Tree, frozen: Frozen, table_path: str, decl_attr: str = "CLASS_ID") -> list[str]:
    """固定の表の値と宣言 → 凍結の写像・表の鍵と宣言 = src の全部のクラス(build を除く)。"""
    from pkgmove import classids as CI

    errs: list[str] = []
    table = CI.table_of(tree.files[table_path])
    classes: dict[str, str] = {}
    declared: dict[str, str] = {}
    for p in _src_files(tree, build=False):
        mod = mod_of(p[len(SRC_PREFIX):])
        t = parse(tree.files[p])
        for q, node in _class_defs(t):
            name = f"{mod}.{q}"
            classes[name] = q
            for s in node.body:
                tgt = s.target if isinstance(s, ast.AnnAssign) else (s.targets[0] if isinstance(s, ast.Assign) else None)
                if isinstance(tgt, ast.Name) and tgt.id == decl_attr and s.value is not None:
                    declared[name] = ast.literal_eval(s.value)
    keys = set(table)
    want = set(classes) - set(declared)
    if keys != want:
        errs.append(f"固定の表の鍵が src のクラスと合わない(表だけ {sorted(keys - want)[:5]}・src だけ {sorted(want - keys)[:5]})")
    mapping: dict[str, str] = {}
    for k, v in [*table.items(), *declared.items()]:
        if v in mapping:
            errs.append(f"凍結の名が重なる: {v}")
        mapping[v] = classes.get(k, "?")
    if mapping != frozen.class_qual:
        diff = sorted(set(mapping.items()) ^ set(frozen.class_qual.items()))[:6]
        errs.append(f"固定の表の値と宣言が凍結の写像と違う: {diff}")
    return errs


def _class_defs(tree: ast.AST) -> list[tuple[str, ast.ClassDef]]:
    out: list[tuple[str, ast.ClassDef]] = []

    def visit(node: ast.AST, prefix: str) -> None:
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, ast.ClassDef):
                q = f"{prefix}{ch.name}"
                out.append((q, ch))
                visit(ch, q + ".")
            elif isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit(ch, f"{prefix}{ch.name}.<locals>.")
            else:
                visit(ch, prefix)

    visit(tree, "")
    return out


def _token_re(tok: str) -> re.Pattern:
    return re.compile(r"(?<![\w./])" + re.escape(tok) + r"(?![\w/])")


def shaped_counts(tree: Tree, kinds: Iterable[str], skip_values: set[str], class_table: str) -> dict[str, int]:
    """74 種がランの側の src の文字列の定数に出てくる数。数えないのは、固定の表の鍵と、値の全体が移すファイルの道そのもの
    (``skip_values``=許可の一覧の道の表の行・台帳の道の表の行)の定数だけ。許可の一覧の記号の中でも、文の中に出てくる道の形
    (manifest に出る文など)は数える(検収 m04=許可の記号に入った文の書き換えも見つける)。"""
    pats = {k: _token_re(k) for k in kinds}
    out: Counter = Counter()
    for p in _src_files(tree, build=False):
        t = parse(tree.files[p])
        ds = docstrings_of(tree.files[p])
        keys: set[int] = set()
        if p == class_table:
            from pkgmove.classids import find_table

            keys = {id(k) for k in find_table(t).keys}
        for n in ast.walk(t):
            if not (isinstance(n, ast.Constant) and isinstance(n.value, str)) or id(n) in ds or id(n) in keys:
                continue
            if n.value in skip_values:
                continue
            for k, pat in pats.items():
                c = len(pat.findall(n.value))
                if c:
                    out[k] += c
    return {k: out[k] for k in kinds}


def const_table(text: str) -> Counter:
    """(記号, docstring か, 値) の多重集合(docstring を含む全部の文字列とバイト列の定数)。"""
    t = parse(text)
    syms = symbols_of(text)
    ds = docstrings_of(text)
    return Counter((syms.get(id(n), ""), id(n) in ds, n.value) for n in ast.walk(t)
                   if isinstance(n, ast.Constant) and isinstance(n.value, (str, bytes)))


def id_pattern(id_tokens: Iterable[str]) -> re.Pattern | None:
    toks = sorted({x for x in id_tokens if x}, key=len, reverse=True)
    if not toks:
        return None
    return re.compile(r"(?<![\w./])(?:" + "|".join(re.escape(x) for x in toks) + r")(?![\w/])")


def check_outside(before: Tree, after: Tree, moved: dict[str, str], allowed: set[tuple[str, str]],
                  skip_files: set[str], id_tokens: set[str], key_sites: set[tuple[str, str]]) -> list[str]:
    """許可の一覧の外の定数がファイルごとに同じ・許可の一覧の中でも凍結の値の字面の出てくる数は同じ
    (``key_sites``=固定の表は鍵が変わるので 2 は値の守り=:func:`check_class_ids` に任せる)。"""
    errs: list[str] = []
    big = id_pattern(id_tokens)
    for p, text in before.files.items():
        if p in skip_files:
            continue
        q = moved.get(p, p)
        if q not in after.files:
            errs.append(f"書き換えた後の木にファイルが無い: {p} → {q}")
            continue
        if after.files[q] == text:
            continue
        a, b = const_table(text), const_table(after.files[q])
        # docstring は許可の一覧の記号の中でも比べる(docstring はどこでも書き換えない=検収 L-9)
        out_a = Counter({k: v for k, v in a.items() if (p, k[0]) not in allowed or k[1]})
        out_b = Counter({k: v for k, v in b.items() if (p, k[0]) not in allowed or k[1]})
        if out_a != out_b:
            d = sorted(set((out_a - out_b).elements()) | set((out_b - out_a).elements()), key=repr)[:4]
            errs.append(f"許可の一覧の外の定数が変わった: {p} {d}")
        if big is not None:
            def toks(c: Counter) -> Counter:
                out: Counter = Counter()
                for (sym, _doc, v), n in c.items():
                    if (p, sym) in allowed and (p, sym) not in key_sites and isinstance(v, str):
                        for m in big.finditer(v):
                            out[m.group(0)] += n
                return out
            ta, tb = toks(a), toks(b)
            if ta != tb:
                d = sorted(set((ta - tb).elements()) | set((tb - ta).elements()))[:4]
                errs.append(f"許可の一覧の中で凍結の値の字面が変わった: {p} {d}")
    return errs


def bound_names(text: str) -> Counter:
    """ファイルの import の文が結ぶ名の多重集合(``import a.b`` は ``a``・別名があれば別名・関数の中の import を含む)。"""
    out: Counter = Counter()
    for n in ast.walk(parse(text)):
        if isinstance(n, ast.Import):
            for a in n.names:
                out[a.asname or a.name.split(".")[0]] += 1
        elif isinstance(n, ast.ImportFrom):
            for a in n.names:
                out[a.asname or a.name] += 1
    return out


def check_bound_names(before: Tree, after: Tree, moved: dict[str, str], skip_files: set[str],
                      dropped: dict[str, list[str]]) -> list[str]:
    """書き換えの前後で、各ファイルの import の文が結ぶ名(別名を含む)の多重集合が同じ(検収 m14)。頭から除いた再輸出の
    名(``dropped``)だけは減ってよい。空にした頭・消した頭(``skip_files``)は比べない。"""
    errs: list[str] = []
    for p, text in before.files.items():
        if p in skip_files:
            continue
        q = moved.get(p, p)
        if q not in after.files or after.files[q] == text:
            continue
        a = bound_names(text)
        for name in dropped.get(p, []):
            a[name] -= 1
        a = +a
        b = bound_names(after.files[q])
        if a != b:
            d = sorted(set((a - b).elements()) | set((b - a).elements()))[:6]
            errs.append(f"import の文が結ぶ名が変わった: {p} {d}")
    return errs


def head_all_names(text: str) -> list[str] | None:
    """頭の頂上の ``__all__ = [...]`` の名(文字列の要素)。``__all__`` が無ければ ``None``。"""
    from pkgmove.imports import head_all_node

    node = head_all_node(parse(text))
    if node is None:
        return None
    return [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]


def _head_bound(t: ast.Module) -> set[str]:
    out: set[str] = set()
    for n in t.body:
        for s in _top_statements(n):
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(s.name)
            elif isinstance(s, ast.Assign):
                out |= {x.id for tg in s.targets for x in ast.walk(tg) if isinstance(x, ast.Name)}
            elif isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name):
                out.add(s.target.id)
            elif isinstance(s, ast.ImportFrom):
                out |= {a.asname or a.name for a in s.names}
            elif isinstance(s, ast.Import):
                out |= {a.asname or a.name.split(".")[0] for a in s.names}
    return out


def check_head_all(tree: Tree) -> list[str]:
    """空にしない頭(中身のある ``src/shibuya/**/__init__.py``)の ``__all__`` の名が、全部その頭で結ばれている
    (定義・代入・import で結んだ名・子のモジュール=同じディレクトリの ``<名>.py`` か ``<名>/__init__.py``)。"""
    errs: list[str] = []
    for p in sorted(tree.files):
        text = tree.files[p]
        if not (p.startswith(SRC_PREFIX) and p.endswith("__init__.py")) or not text.strip():
            continue
        names = head_all_names(text)
        if not names:
            continue
        bound = _head_bound(parse(text))
        d = p[: -len("__init__.py")]
        missing = [x for x in names if x not in bound and (d + x + ".py") not in tree.files
                   and (d + x + "/__init__.py") not in tree.files]
        if missing:
            errs.append(f"頭の __all__ に頭で結ばれない名がある: {p} {len(missing)} 個 {missing[:6]}")
    return errs
