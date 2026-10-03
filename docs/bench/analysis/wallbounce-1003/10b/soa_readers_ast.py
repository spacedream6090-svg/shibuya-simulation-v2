"""10b の準備: SoA の列名の「読み手」と「書き手」を AST で数える(追加 C の検査の実現性の確認)。

使い方(リポのルートで・src は git archive HEAD の写しを渡す):

    python soa_readers_ast.py <src の根(shibuya の親)> <出力 JSON>

やり方(実行役の自前の構成=未リサーチ):
- 列名は ``agents/state.py``・``world/state.py``・``perception/state.py`` の ``declare("名前", ...)`` から
  AST で取る(手で列挙しない)。
- 走査の範囲は 2 つ: ``shibuya/engine/``(指示の範囲)と ``shibuya/`` 全体(``build/`` を除く)。
- 属性 ``X.列名`` を次の規則で「書き」と「読み」に分ける。
  書き = 代入の左辺(``X.c = ``・``X.c[i] = ``・``X.c[i] += ``)・``np.*.at(X.c, ...)`` の第 1 引数・
  ``np.copyto(X.c, ...)``・``X.c.fill(...)``・``out=X.c``。それ以外は読み。ただし
  ``X.c.dtype`` などの型の参照は ``meta``、同じ列への代入文の右辺に現れる読み(``X.c[a] = X.c[a] + 1``)は
  ``rmw``(自己更新)として読みから外す。
- ``r.field(変数)`` の変数が、頂上で定義した名前の表(``INTERO_VARS`` など)を回すループの変数なら、
  表の中の列名をすべて ``read_dyn``(動的な読み)として数え、``read_strict`` にも足す。表に解決できない
  ``field(変数)`` は ``dynamic_unresolved`` に場所を出す(検査はここが空であることを求める形にできる)。
- 文字列 ``"列名"`` は ``field("c")``(``f = r.field`` の別名も)・``getattr(r, "c")``・``arrays["c"]`` / ``registry["c"]`` の形だけを読みとして数え、
  ``declare("c")`` は宣言として除く。タプルやリストの中の文字列(名前の表で回す書き方)は ``str_in_seq`` として別に数える。
- 列名が一般的な語(``cell``・``kind`` など)だと別のオブジェクトの属性と衝突する。属性の手前の式が
  SoA を指していそうなもの(末尾が ``registry``・``r``・``R``・``reg``・``agents``・``cells``・``pois``・``pstate``・
  ``ps``・``state`` など)だけを数えた ``strict`` の数も出す。

絶対パスは JSON に書かない(src の根からの相対パスだけ)。
"""

from __future__ import annotations

import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

DECL_FILES = {
    "agents": "shibuya/agents/state.py",
    "world": "shibuya/world/state.py",
    "perception": "shibuya/perception/state.py",
}

SOA_BASE_TAILS = {
    "registry", "r", "R", "reg", "agents", "cells", "pois", "pstate", "ps", "state",
    "rows", "v", "f", "A", "st", "s", "ag", "world_cells", "world_pois",
}
WRITE_FUNCS = {"copyto", "put", "place", "putmask"}
META_ATTRS = {"dtype", "shape", "size", "ndim", "itemsize", "nbytes"}


def target_names(stmt: ast.AST) -> set[str]:
    """代入文の左辺に現れる列名(``X.c[...] = X.c[...] + 1`` の自己更新の判定に使う)。"""
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


def enclosing_stmt(node: ast.AST, par: dict) -> ast.AST | None:
    cur = node
    while cur in par:
        cur = par[cur]
        if isinstance(cur, ast.stmt):
            return cur
    return None


def declared_columns(root: Path) -> dict[str, dict]:
    cols: dict[str, dict] = {}
    for group, rel in DECL_FILES.items():
        tree = ast.parse((root / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "declare" and node.args
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                name = node.args[0].value
                owner = ast.unparse(node.func.value)
                sub = group
                if group == "world":
                    sub = "cells" if "cells" in owner else "pois"
                key = f"{sub}.{name}"
                cols.setdefault(key, {"name": name, "group": sub, "decl": []})
                cols[key]["decl"].append(f"{rel.removeprefix('shibuya/')}:{node.lineno}")
    return cols


def parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    p: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for ch in ast.iter_child_nodes(node):
            p[ch] = node
    return p


def is_write(node: ast.Attribute, par: dict) -> bool:
    if isinstance(node.ctx, (ast.Store, ast.Del)):
        return True
    up = par.get(node)
    # X.c[...] = / X.c[...] += / del X.c[...]
    if isinstance(up, ast.Subscript) and up.value is node and isinstance(up.ctx, (ast.Store, ast.Del)):
        return True
    if isinstance(up, ast.AugAssign) and up.target is node:
        return True
    # X.c.fill(...)
    if isinstance(up, ast.Attribute) and up.value is node and up.attr == "fill":
        return True
    if isinstance(up, ast.Call):
        f = up.func
        fname = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        if up.args and up.args[0] is node:
            if fname == "at" or fname in WRITE_FUNCS:
                return True
    if isinstance(up, ast.keyword) and up.arg == "out":
        return True
    return False


def base_tail(expr: ast.AST) -> str:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    if isinstance(expr, ast.Call):
        return base_tail(expr.func)
    return ""


def str_tables(files: list[Path]) -> dict[str, set[str]]:
    """モジュールの頂上で文字列(か文字列の組)のタプル/リストを代入した名前 → 文字列の集合。"""
    tabs: dict[str, set[str]] = {}
    for fp in files:
        try:
            tree = ast.parse(fp.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in tree.body:
            tgt = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                tgt, val = node.targets[0], node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                tgt, val = node.target, node.value
            if not isinstance(tgt, ast.Name) or not isinstance(val, (ast.Tuple, ast.List)):
                continue
            ss = {n.value for n in ast.walk(val) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
            if ss and all(isinstance(n, (ast.Constant, ast.Tuple, ast.List, ast.Load)) for n in ast.walk(val)
                          if n is not val):
                tabs[tgt.id] = ss
    return tabs


def dynamic_reads(node: ast.Call, par: dict, tabs: dict[str, set[str]]) -> tuple[str, set[str]]:
    """``field(変数)`` の変数が、名前の表を回すループの変数なら (表の名前, 表の中身) を返す。"""
    arg = node.args[0]
    if not isinstance(arg, ast.Name):
        return "", set()
    cur = node
    while cur in par:
        cur = par[cur]
        iters: list[ast.AST] = []
        if isinstance(cur, ast.For):
            iters = [cur.iter]
        elif isinstance(cur, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            iters = [g.iter for g in cur.generators]
        for it in iters:
            for n in ast.walk(it):
                if isinstance(n, ast.Name) and n.id in tabs:
                    return n.id, tabs[n.id]
    return "", set()


def scan(root: Path, files: list[Path], names: set[str], tabs: dict[str, set[str]] | None = None
         ) -> dict[str, dict[str, list[str]]]:
    out: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    tabs = tabs or {}
    for fp in files:
        rel = fp.relative_to(root).as_posix().removeprefix("shibuya/")
        try:
            tree = ast.parse(fp.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        par = parents(tree)
        # ``f = r.field`` のような別名(memory.py の書き方)を集める
        field_alias = {"field", "getattr"}
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Attribute)
                    and node.value.attr == "field"):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        field_alias.add(t.id)
        for node in ast.walk(tree):
            # 名前の表を回す動的な読み(``for v, sf in INTERO_VARS: r.field(sf)``)
            if (isinstance(node, ast.Call) and node.args and not isinstance(node.args[0], ast.Constant)
                    and ((isinstance(node.func, ast.Attribute) and node.func.attr == "field")
                         or (isinstance(node.func, ast.Name) and node.func.id in field_alias
                             and node.func.id != "getattr"))):
                tab, ss = dynamic_reads(node, par, tabs)
                loc = f"{rel}:{node.lineno}"
                if not tab:
                    out["__dynamic_unresolved__"]["sites"].append(loc)
                else:
                    st = enclosing_stmt(node, par)
                    is_w = isinstance(par.get(node), ast.Subscript) and isinstance(par[node].ctx, ast.Store)
                    for nm in ss & names:
                        out[nm]["write_dyn" if is_w else "read_dyn"].append(f"{loc}({tab})")
                        if not is_w:
                            out[nm]["read_strict"].append(f"{loc}({tab})")
            if isinstance(node, ast.Attribute) and node.attr in names:
                loc = f"{rel}:{node.lineno}"
                w = is_write(node, par)
                kind = "write" if w else "read"
                up = par.get(node)
                if not w and isinstance(up, ast.Attribute) and up.value is node and up.attr in META_ATTRS:
                    out[node.attr]["meta"].append(loc)
                    continue
                if not w:
                    st = enclosing_stmt(node, par)
                    if st is not None and node.attr in target_names(st):
                        out[node.attr]["rmw"].append(loc)
                        continue
                out[node.attr][kind].append(loc)
                tail = base_tail(node.value)
                if tail in SOA_BASE_TAILS or "registry" in ast.unparse(node.value):
                    out[node.attr][kind + "_strict"].append(loc)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in names:
                up = par.get(node)
                loc = f"{rel}:{node.lineno}"
                if isinstance(up, ast.Call):
                    f = up.func
                    fname = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
                    if fname == "declare" and up.args and up.args[0] is node:
                        out[node.value]["declare"].append(loc)
                        continue
                    if fname in field_alias and node in up.args:
                        up2 = par.get(up)
                        if (isinstance(up2, ast.Subscript) and up2.value is up
                                and isinstance(up2.ctx, (ast.Store, ast.Del))):
                            out[node.value]["write_str"].append(loc)
                            out[node.value]["write"].append(loc)
                            continue
                        out[node.value]["read_str"].append(loc)
                        out[node.value]["read_strict"].append(loc)
                        continue
                if isinstance(up, ast.Subscript) and up.slice is node:
                    t = ast.unparse(up.value)
                    if "arrays" in t or "registry" in t or t in SOA_BASE_TAILS:
                        kind = "write" if isinstance(up.ctx, (ast.Store, ast.Del)) else "read"
                        out[node.value][kind + "_str"].append(loc)
                        out[node.value][kind + "_strict"].append(loc)
                        continue
                if isinstance(up, (ast.Tuple, ast.List, ast.Set)):
                    out[node.value]["str_in_seq"].append(loc)
                    continue
                out[node.value]["str_other"].append(loc)
    return out


def main(argv: list[str]) -> int:
    root = Path(argv[1])
    dst = Path(argv[2])
    cols = declared_columns(root)
    names = {c["name"] for c in cols.values()}
    eng_files = sorted((root / "shibuya/engine").rglob("*.py"))
    all_files = sorted(p for p in (root / "shibuya").rglob("*.py") if "/build/" not in p.as_posix())
    tabs = str_tables(all_files)
    eng = scan(root, eng_files, names, tabs)
    allsrc = scan(root, all_files, names, tabs)
    rows = {}
    for key, c in cols.items():
        n = c["name"]
        e = eng.get(n, {})
        a = allsrc.get(n, {})
        rows[key] = {
            "decl": c["decl"],
            "engine": {k: len(v) for k, v in e.items()},
            "all_src": {k: len(v) for k, v in a.items()},
            "engine_read_strict_sites": sorted(set(e.get("read_strict", [])))[:40],
            "all_read_strict_sites_outside_engine": sorted(
                s for s in set(a.get("read_strict", [])) if not s.startswith("engine/")
            )[:40],
            "all_read_sites_outside_engine_nonstrict": sorted(
                s for s in set(a.get("read", [])) if not s.startswith("engine/")
                and s not in set(a.get("read_strict", []))
            )[:20],
            "str_in_seq": sorted(set(a.get("str_in_seq", [])))[:20],
        }
    meta = {
        "dynamic_unresolved_engine": sorted(set(eng.get("__dynamic_unresolved__", {}).get("sites", []))),
        "dynamic_unresolved_all": sorted(set(allsrc.get("__dynamic_unresolved__", {}).get("sites", []))),
        "files_engine": len(eng_files),
        "files_all_src": len(all_files),
        "columns": len(cols),
        "note": "src は git archive HEAD の写し。パスは shibuya/ からの相対",
    }
    dst.write_text(json.dumps({"meta": meta, "columns": rows}, ensure_ascii=False, indent=1),
                   encoding="utf-8", newline="\n")
    print(json.dumps(meta, ensure_ascii=False))
    for key, r in rows.items():
        e, a = r["engine"], r["all_src"]
        print(f"{key:28s} eng R{e.get('read', 0):4d} Rs{e.get('read_strict', 0):4d} W{e.get('write', 0):3d} "
              f"rmw{e.get('rmw', 0):2d} meta{e.get('meta', 0):2d} dyn{e.get('read_dyn', 0):2d} | "
              f"all R{a.get('read', 0):4d} Rs{a.get('read_strict', 0):4d} W{a.get('write', 0):3d} "
              f"seq{a.get('str_in_seq', 0):3d} oth{a.get('str_other', 0):3d}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
