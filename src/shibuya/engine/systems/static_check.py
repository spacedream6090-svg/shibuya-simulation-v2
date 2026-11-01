"""engine.systems.static_check — 系の宣言と系のコードを AST で突き合わせる(第 1 期 1-0・草案 §2-6 の D ①②③)。

系の関数(``SystemSpec.fn``)と、そこから呼ぶ ``engine.systems`` の中の関数(``SIO.relay_tables(b, …)``・
``functools.partial(_LLM_IO.utter, b)`` など・推移的に)の本体について:

- ``box_refs``: 箱の属性の参照 ``b.<箱>.<欄>``(読みと書きの両方・``sc = b.scratch`` のような箱の別名を通したものを含む)。
  D ③ の材料(宣言 ``reads.box`` に入っていること)。
- ``scratch_stores``: ``b.scratch.<欄> = …``(書き)。宣言 ``writes.scratch`` に入っていること。
- ``tally_stores``: ``RunStats`` の欄への書き。``b.runstats.<欄> = / +=``・``rs.<欄> = / +=``(``rs = b.runstats``)と、
  欄の別名(``x = b.runstats.<欄>``・``x = rs.<欄>``・組の代入 ``a, b = rs.p, rs.q`` を含む)を通した
  ``x[...] = / x[...] += / x.<変更のメソッド>(…) / x += / x.<属性> = …``。宣言 ``writes.tally`` に入っていること。
- ``resolve_calls``: resolve の口の直接の呼び出し。モジュールの別名(``R``・``RV``・``import shibuya.engine.resolve as X``)の
  ``X.<口>(…)`` と、素の import(``from shibuya.engine.resolve import <口> [as y]``・関数の中の import を含む)の
  ``<口>(…)``。宣言 ``resolve_ops`` に入っていること(D ①)。〔段 FIX・検収 §1 の 6〕素の import と別名も見る。

限界(草案 K6): 層のメソッドの中の読み・実行時の読みは見ない。``getattr(b, 変数)`` は見えない(系のコードには無い)。

逐次ループ宣言: なし(AST の走査は試験のときだけ)。
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

__all__ = ["SystemCode", "analyze", "analyze_spec"]

BOXES = ("cfg", "soa", "layers", "llm", "day", "buffers", "scratch", "runstats", "fx")
#: ``RunStats`` の欄の名 → 宣言(``writes.tally``)の名(HEAD の局所の名)。
TALLY_NAME = {"sleep_tally": "sleep_counts"}
_MUTATORS = {"append", "extend", "update", "clear", "pop", "setdefault", "add", "discard", "insert", "remove",
             "popitem", "sort", "fill"}
RESOLVE_MODULE = "shibuya.engine.resolve"


@dataclass
class SystemCode:
    box_refs: set[str] = field(default_factory=set)
    scratch_stores: set[str] = field(default_factory=set)
    tally_stores: set[str] = field(default_factory=set)
    resolve_calls: set[str] = field(default_factory=set)
    funcs: set[str] = field(default_factory=set)


def _box_ref(node: ast.AST, bname: str) -> tuple[str, str] | None:
    """``b.<箱>.<欄>`` なら (箱, 欄)。"""
    if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute)
            and isinstance(node.value.value, ast.Name) and node.value.value.id == bname
            and node.value.attr in BOXES):
        return node.value.attr, node.attr
    return None


def _module_aliases(mod: Any) -> dict[str, Any]:
    """モジュールの頂上の名前のうち ``engine.systems`` のモジュールを指すもの。"""
    out = {}
    for k, v in vars(mod).items():
        if inspect.ismodule(v) and v.__name__.startswith("shibuya.engine.systems."):
            out[k] = v
    return out


def _resolve_names(mod: Any, fdef: ast.FunctionDef) -> tuple[set[str], dict[str, str]]:
    """resolve のモジュールを指す名(別名)と、resolve の関数を素の名で指す名(名 → 口)。モジュールの頂上と関数の中の
    import の両方。"""
    mods, funcs = set(), {}
    for k, v in vars(mod).items():
        if inspect.ismodule(v) and v.__name__ == RESOLVE_MODULE:
            mods.add(k)
        elif callable(v) and getattr(v, "__module__", "") == RESOLVE_MODULE and hasattr(v, "__name__"):
            funcs[k] = v.__name__
    for n in ast.walk(fdef):
        if isinstance(n, ast.ImportFrom):
            for a in n.names:
                if n.module == "shibuya.engine" and a.name == "resolve":
                    mods.add(a.asname or a.name)
                elif n.module == RESOLVE_MODULE:
                    funcs[a.asname or a.name] = a.name
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name == RESOLVE_MODULE and a.asname:
                    mods.add(a.asname)
    return mods, funcs


def _pairs(node: ast.Assign) -> list[tuple[ast.AST, ast.AST]]:
    out = []
    for t in node.targets:
        if isinstance(t, (ast.Tuple, ast.List)) and isinstance(node.value, (ast.Tuple, ast.List)) \
                and len(t.elts) == len(node.value.elts):
            out += list(zip(t.elts, node.value.elts))
        else:
            out.append((t, node.value))
    return out


def analyze(fn: Callable[..., Any], *, _seen: set | None = None) -> SystemCode:
    """系の関数(か箱を受け取る補助)の本体を推移的に読む。"""
    seen = set() if _seen is None else _seen
    res = SystemCode()
    key = f"{fn.__module__}.{fn.__qualname__}"
    if key in seen:
        return res
    seen.add(key)
    res.funcs.add(key)
    mod = inspect.getmodule(fn)
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    fdef = tree.body[0]
    assert isinstance(fdef, ast.FunctionDef)
    params = [a.arg for a in fdef.args.args]
    bname = "b" if "b" in params else ("box" if "box" in params else "")
    aliases = _module_aliases(mod)
    r_mods, r_funcs = _resolve_names(mod, fdef)

    # ---- 箱の別名(sc = b.scratch)と RunStats の欄の別名(x = b.runstats.f・x = rs.f)
    box_alias: dict[str, str] = {}
    tally_alias: dict[str, str] = {}
    for n in ast.walk(fdef):
        if not isinstance(n, ast.Assign):
            continue
        for t, v in _pairs(n):
            if not isinstance(t, ast.Name):
                continue
            if (isinstance(v, ast.Attribute) and isinstance(v.value, ast.Name) and v.value.id == bname
                    and v.attr in BOXES):
                box_alias[t.id] = v.attr
    for n in ast.walk(fdef):
        if not isinstance(n, ast.Assign):
            continue
        for t, v in _pairs(n):
            if not isinstance(t, ast.Name):
                continue
            r = _box_ref(v, bname)
            if r and r[0] == "runstats":
                tally_alias[t.id] = TALLY_NAME.get(r[1], r[1])
            elif (isinstance(v, ast.Attribute) and isinstance(v.value, ast.Name)
                  and box_alias.get(v.value.id) == "runstats"):
                tally_alias[t.id] = TALLY_NAME.get(v.attr, v.attr)

    def tally_of(expr: ast.AST) -> str | None:
        """書きの的(の根)が RunStats の欄なら欄の名。"""
        base = expr
        while isinstance(base, (ast.Subscript, ast.Attribute)) and not _box_ref(base, bname):
            if isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name) \
                    and box_alias.get(base.value.id) == "runstats":
                return TALLY_NAME.get(base.attr, base.attr)
            base = base.value
        r = _box_ref(base, bname)
        if r and r[0] == "runstats":
            return TALLY_NAME.get(r[1], r[1])
        if isinstance(base, ast.Name) and base.id in tally_alias:
            return tally_alias[base.id]
        return None

    for node in ast.walk(fdef):
        r = _box_ref(node, bname)
        if r:
            res.box_refs.add(f"{r[0]}.{r[1]}")
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in box_alias:
            res.box_refs.add(f"{box_alias[node.value.id]}.{node.attr}")
        # ---- 書き
        tgts: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            tgts = list(node.targets)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            tgts = [node.target]
        flat: list[ast.AST] = []
        for t in tgts:
            flat.extend(t.elts if isinstance(t, (ast.Tuple, ast.List)) else [t])
        for t in flat:
            rr = _box_ref(t, bname)
            if rr and rr[0] == "scratch":
                res.scratch_stores.add(rr[1])
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and box_alias.get(t.value.id) == "scratch":
                res.scratch_stores.add(t.attr)
            if isinstance(t, ast.Name):
                if isinstance(node, ast.AugAssign) and t.id in tally_alias:
                    res.tally_stores.add(tally_alias[t.id])
                continue
            tl = tally_of(t)
            if tl:
                res.tally_stores.add(tl)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in _MUTATORS:
            tl = tally_of(node.func.value) if not isinstance(node.func.value, ast.Name) else \
                tally_alias.get(node.func.value.id)
            if tl:
                res.tally_stores.add(tl)
        # ---- resolve の口
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in r_mods:
                res.resolve_calls.add(f.attr)
            elif isinstance(f, ast.Name) and f.id in r_funcs:
                res.resolve_calls.add(r_funcs[f.id])
        # ---- engine.systems の中の補助(推移的に)
        target = None
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases:
            target = getattr(aliases[node.value.id], node.attr, None)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in vars(mod) \
                and node.id != fdef.name:
            cand = vars(mod)[node.id]
            if inspect.isfunction(cand) and cand.__module__ == mod.__name__:
                target = cand
        if inspect.isfunction(target) and target.__module__.startswith("shibuya.engine.systems."):
            sub = analyze(target, _seen=seen)
            res.box_refs |= sub.box_refs
            res.scratch_stores |= sub.scratch_stores
            res.tally_stores |= sub.tally_stores
            res.resolve_calls |= sub.resolve_calls
            res.funcs |= sub.funcs
    return res


def analyze_spec(spec: Any) -> SystemCode | None:
    if spec.fn is None:
        return None
    return analyze(spec.fn)


def source_root() -> Path:
    return Path(__file__).resolve().parent
