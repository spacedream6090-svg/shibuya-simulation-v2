"""T0: prove HEAD vs worktree are the same program modulo (a) docstrings, (b) names from core.time_consts
substituted by their values, (c) int<->float of integral constants in true-division / float-multiplication operands.

usage: ast_equiv.py <repo> [<rev>=HEAD]
Prints one line per changed src/shibuya/*.py file: SAME / DIFF (with first differing dump context).
"""
import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

repo = Path(sys.argv[1])
rev = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
spec = importlib.util.spec_from_file_location("tc", repo / "src/shibuya/core/time_consts.py")
TC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(TC)
TCV = {k: getattr(TC, k) for k in TC.__all__ if isinstance(getattr(TC, k), (int, str))}
MOD = "shibuya.core.time_consts"


def git(*a):
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, encoding="utf-8").stdout


class Norm(ast.NodeTransformer):
    def __init__(self, names):
        self.names = names  # local name -> value

    def _strip_doc(self, node):
        b = getattr(node, "body", None)
        if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) and isinstance(b[0].value.value, str):
            b[0] = ast.Expr(ast.Constant(""))
        return node

    def visit_Module(self, node):
        self._strip_doc(node)
        body = []
        for st in node.body:
            if isinstance(st, ast.ImportFrom) and st.module == MOD:
                continue
            # module-level re-definition of a time_consts name with the same constant value
            if isinstance(st, (ast.AnnAssign, ast.Assign)):
                tg = st.target if isinstance(st, ast.AnnAssign) else (st.targets[0] if len(st.targets) == 1 else None)
                v = st.value
                if isinstance(tg, ast.Name) and tg.id in TCV and isinstance(v, ast.Constant) and v.value == TCV[tg.id] \
                        and type(v.value) is int:
                    continue
            body.append(st)
        node.body = body
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        self._strip_doc(node)
        self.generic_visit(node)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self._strip_doc(node)
        self.generic_visit(node)
        return node

    def visit_ImportFrom(self, node):
        if node.module == MOD:
            return None
        return node

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id in self.names:
            return ast.copy_location(ast.Constant(self.names[node.id]), node)
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == "float" and len(node.args) == 1 and not node.keywords \
                and isinstance(node.args[0], ast.Constant) and type(node.args[0].value) is int:
            return ast.copy_location(ast.Constant(float(node.args[0].value)), node)
        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)

        def isnum(n):
            return isinstance(n, ast.Constant) and type(n.value) in (int, float)

        floaty = isinstance(node.op, ast.Div) or (
            isinstance(node.op, ast.Mult) and any(isnum(x) and type(x.value) is float for x in (node.left, node.right)))
        if floaty:
            for side in ("left", "right"):
                x = getattr(node, side)
                if isnum(x) and float(x.value).is_integer() and abs(x.value) < 2 ** 53:
                    setattr(node, side, ast.copy_location(ast.Constant(float(x.value)), x))
        return node


def _module_value(mod, name, source):
    """value of module-level ``name`` in shibuya module ``mod`` (source text), if it is a time_consts value."""
    t = ast.parse(source)
    for st in t.body:
        if isinstance(st, ast.ImportFrom) and st.module == MOD and any((a.asname or a.name) == name for a in st.names):
            return TCV[next(a.name for a in st.names if (a.asname or a.name) == name)]
        if isinstance(st, (ast.AnnAssign, ast.Assign)):
            tg = st.target if isinstance(st, ast.AnnAssign) else (st.targets[0] if len(st.targets) == 1 else None)
            if isinstance(tg, ast.Name) and tg.id == name and isinstance(st.value, ast.Constant):
                return st.value.value
    return None


SIDE = {"old": None}


def imported_names(tree):
    out = {}
    for st in ast.walk(tree):
        if isinstance(st, ast.ImportFrom) and st.module == MOD:
            for a in st.names:
                out[a.asname or a.name] = TCV[a.name]
        elif isinstance(st, ast.ImportFrom) and (st.module or "").startswith("shibuya."):
            for a in st.names:
                if a.name in TCV and a.asname is None:
                    f = "src/" + st.module.replace(".", "/") + ".py"
                    src = git("show", f"{rev}:{f}") if SIDE["old"] else (repo / f).read_text(encoding="utf-8")
                    if _module_value(st.module, a.name, src) == TCV[a.name]:
                        out[a.name] = TCV[a.name]
    return out


def norm(text):
    tree = ast.parse(text)
    names = imported_names(tree)
    for st in tree.body:  # module-level duplicate definitions of a time_consts name (same int value) read as the value
        if isinstance(st, (ast.AnnAssign, ast.Assign)):
            tg = st.target if isinstance(st, ast.AnnAssign) else (st.targets[0] if len(st.targets) == 1 else None)
            if isinstance(tg, ast.Name) and tg.id in TCV and isinstance(st.value, ast.Constant)                     and type(st.value.value) is int and st.value.value == TCV[tg.id]:
                names[tg.id] = TCV[tg.id]
    tree = Norm(names).visit(tree)
    ast.fix_missing_locations(tree)
    return ast.dump(tree, include_attributes=False)


changed = [l for l in git("diff", "--name-only", rev, "--", "src/shibuya").splitlines() if l.endswith(".py")]
untracked = [l for l in git("ls-files", "--others", "--exclude-standard", "src/shibuya").splitlines() if l.endswith(".py")]
n_same = 0
for f in changed:
    old = git("show", f"{rev}:{f}")
    new = (repo / f).read_text(encoding="utf-8")
    SIDE["old"] = True
    a = norm(old)
    SIDE["old"] = False
    b = norm(new)
    if a == b:
        n_same += 1
        print("SAME", f)
    else:
        k = next(i for i in range(min(len(a), len(b))) if a[i] != b[i]) if a[:min(len(a), len(b))] != b[:min(len(a), len(b))] else min(len(a), len(b))
        print("DIFF", f, "\n   old:", a[max(0, k - 200):k + 200], "\n   new:", b[max(0, k - 200):k + 200])
print(f"changed={len(changed)} same={n_same} untracked(new files)={untracked}")
