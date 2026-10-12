"""SoA の列の「書き手」を AST で数える(HEAD 0389689・読むだけ)。

10b の読み手の数え方(engine/state_ledger_ast.py の _is_write)をそのまま使い、書きの場所を
(ファイル, 関数の道筋)ごとに集める。限界: 局所の別名(``c = r.cell; c[i] = x``)の書きは拾えない。
同じ名前の列(agents.cell と pois.cell など)は区別できない。
"""
from __future__ import annotations

import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

from shibuya.engine import state_ledger as SL
from shibuya.engine import state_ledger_ast as A

ROOT = Path(sys.argv[1])  # src/shibuya
OUT = Path(sys.argv[2])

declared = A.declared_columns(ROOT)
names = {n for v in declared.values() for n in v}
place_of = defaultdict(list)
for p, v in declared.items():
    for n in v:
        place_of[n].append(p)

writes = defaultdict(lambda: defaultdict(list))  # col -> (path:qual) -> [line]
alias_hits = []
for fp in A.source_files(ROOT):
    rel = fp.relative_to(ROOT).as_posix()
    text = fp.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        continue
    par = A._parents(tree)

    def qual(node):
        out = []
        p = par.get(node)
        while p is not None:
            if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.append(p.name)
            p = par.get(p)
        return ".".join(reversed(out)) or "<module>"

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in names and A._is_write(node, par):
            # 代入の左辺の素の属性(``self.cell = …`` のような束縛)は列の書きでない可能性が高い=印を付ける
            bind_only = isinstance(node.ctx, ast.Store)
            writes[node.attr][f"{rel}:{qual(node)}"].append(int(node.lineno) * (-1 if bind_only else 1))
        # ``X.field("c")[...] = …``・``X.arrays["c"][...] = …``
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del)):
            v = node.value
            nm = None
            if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and v.func.attr == "field" \
                    and v.args and isinstance(v.args[0], ast.Constant) and v.args[0].value in names:
                nm = v.args[0].value
            if isinstance(v, ast.Subscript) and isinstance(v.slice, ast.Constant) and v.slice.value in names \
                    and "arrays" in ast.unparse(v.value):
                nm = v.slice.value
            if nm:
                writes[nm][f"{rel}:{qual(node)}"].append(int(node.lineno))

out_cols = {}
for col in sorted(names):
    w = writes.get(col, {})
    real = {k: sorted(abs(x) for x in v if x > 0) for k, v in w.items() if any(x > 0 for x in v)}
    out_cols[col] = {"places": place_of[col], "writers": real, "n_writer_funcs": len(real),
                     "n_files": len({k.split(":")[0] for k in real})}
by_func = defaultdict(set)
for col, d in out_cols.items():
    for k in d["writers"]:
        by_func[k].add(col)
by_file = defaultdict(set)
for col, d in out_cols.items():
    for k in d["writers"]:
        by_file[k.split(":")[0]].add(col)
res = {
    "source": "src/shibuya @ HEAD 0389689",
    "n_columns": len(names),
    "n_columns_with_writer": sum(1 for d in out_cols.values() if d["writers"]),
    "columns_no_static_writer": sorted(c for c, d in out_cols.items() if not d["writers"]),
    "columns_multi_file_writers": {c: sorted({k.split(':')[0] for k in d["writers"]})
                                   for c, d in out_cols.items() if d["n_files"] >= 2},
    "by_file": {k: sorted(v) for k, v in sorted(by_file.items())},
    "by_func": {k: sorted(v) for k, v in sorted(by_func.items())},
    "columns": out_cols,
}
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(json.dumps({k: res[k] for k in ("n_columns", "n_columns_with_writer")}, ensure_ascii=False))
print("no writer:", res["columns_no_static_writer"])
print("multi-file:", json.dumps(res["columns_multi_file_writers"], ensure_ascii=False))
print("files:", {k: len(v) for k, v in res["by_file"].items()})
