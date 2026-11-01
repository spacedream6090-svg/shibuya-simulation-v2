"""resolve の公開の口(と _ で始まる口)を、どのファイル・どの関数が呼ぶか(HEAD 0389689・AST・読むだけ)。"""
import ast, json, sys
from collections import defaultdict
from pathlib import Path
from shibuya.engine import state_ledger_ast as A
ROOT = Path(sys.argv[1]); OUT = Path(sys.argv[2])
rtree = ast.parse((ROOT / "engine/resolve.py").read_text(encoding="utf-8"))
rfuncs = {n.name for n in rtree.body if isinstance(n, ast.FunctionDef)}
calls = defaultdict(lambda: defaultdict(list))
for fp in A.source_files(ROOT):
    rel = fp.relative_to(ROOT).as_posix()
    tree = ast.parse(fp.read_text(encoding="utf-8")); par = A._parents(tree)
    aliases = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module == "shibuya.engine" and any(a.name == "resolve" for a in n.names):
            aliases |= {a.asname or a.name for a in n.names if a.name == "resolve"}
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "shibuya.engine.resolve": aliases.add(a.asname or "resolve")
    direct = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module == "shibuya.engine.resolve":
            direct |= {a.asname or a.name for a in n.names}
    def qual(node):
        out=[]; p=par.get(node)
        while p is not None:
            if isinstance(p,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)): out.append(p.name)
            p=par.get(p)
        return ".".join(reversed(out)) or "<module>"
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call): continue
        f = n.func; name = None
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in aliases and f.attr in rfuncs:
            name = f.attr
        elif isinstance(f, ast.Name) and f.id in direct and f.id in rfuncs:
            name = f.id
        elif rel == "engine/resolve.py" and isinstance(f, ast.Name) and f.id in rfuncs:
            name = f.id
        if name: calls[name][f"{rel}:{qual(n)}"].append(n.lineno)
res = {k: {kk: sorted(vv) for kk, vv in v.items()} for k, v in sorted(calls.items())}
ext = {k: sorted({kk.split(":")[0] for kk in v if not kk.startswith("engine/resolve.py")}) for k, v in res.items()}
OUT.write_text(json.dumps({"calls": res, "external_files": ext}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
for k, v in ext.items():
    if v: print(k, v)
