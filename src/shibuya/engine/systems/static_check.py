"""engine.systems.static_check — 系の宣言と系のコードを AST で突き合わせる(第 1 期 1-0・草案 §2-6 の D ①②③)。

系の関数(``SystemSpec.fn``)と、そこから呼ぶ ``engine.systems`` の中の関数(``SIO.relay_tables(b, …)``・
``functools.partial(_LLM_IO.utter, b)`` など・推移的に)の本体について:

- ``box_refs``: 箱の属性の参照 ``b.<箱>.<欄>``(読みと書きの両方)。D ③ の材料(宣言 ``reads.box`` に入っていること)。
- ``scratch_stores``: ``b.scratch.<欄> = …``(書き)。宣言 ``writes.scratch`` に入っていること。
- ``tally_stores``: ``RunStats`` の欄への書き(``b.runstats.<欄> = / +=`` と、``x = b.runstats.<欄>`` の別名を通した
  ``x[...] = / x[...] += / x.append / x += / x.update / x.clear``)。宣言 ``writes.tally`` に入っていること。
- ``resolve_calls``: resolve の口の直接の呼び出し ``R.<口>(…)``。宣言 ``resolve_ops`` に入っていること(D ①)。

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
_MUTATORS = {"append", "extend", "update", "clear", "pop", "setdefault", "add", "discard", "insert"}


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
    tally_alias: dict[str, str] = {}
    for node in ast.walk(fdef):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            r = _box_ref(node.value, bname)
            if r and r[0] == "runstats":
                tally_alias[node.targets[0].id] = TALLY_NAME.get(r[1], r[1])
            # rs = b.runstats → rs.<欄> も runstats の欄
            if (isinstance(node.value, ast.Attribute) and isinstance(node.value.value, ast.Name)
                    and node.value.value.id == bname and node.value.attr == "runstats"):
                tally_alias["@" + node.targets[0].id] = "runstats"
    rs_names = {k[1:] for k, v in tally_alias.items() if k.startswith("@")}
    for node in ast.walk(fdef):
        r = _box_ref(node, bname)
        if r:
            res.box_refs.add(f"{r[0]}.{r[1]}")
        # 書き
        tgts: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            tgts = list(node.targets)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            tgts = [node.target]
        flat: list[ast.AST] = []
        for t in tgts:
            flat.extend(t.elts if isinstance(t, (ast.Tuple, ast.List)) else [t])
        for t in flat:
            r = _box_ref(t, bname)
            if r and r[0] == "scratch":
                res.scratch_stores.add(r[1])
            if r and r[0] == "runstats":
                res.tally_stores.add(TALLY_NAME.get(r[1], r[1]))
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id in rs_names:
                res.tally_stores.add(TALLY_NAME.get(t.attr, t.attr))
            if isinstance(t, ast.Subscript):
                base = t.value
                while isinstance(base, ast.Subscript):
                    base = base.value
                if isinstance(base, ast.Name) and base.id in tally_alias:
                    res.tally_stores.add(tally_alias[base.id])
                r2 = _box_ref(base, bname)
                if r2 and r2[0] == "runstats":
                    res.tally_stores.add(TALLY_NAME.get(r2[1], r2[1]))
            if isinstance(t, ast.Name) and isinstance(node, ast.AugAssign) and t.id in tally_alias:
                res.tally_stores.add(tally_alias[t.id])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in _MUTATORS:
            base = node.func.value
            if isinstance(base, ast.Name) and base.id in tally_alias:
                res.tally_stores.add(tally_alias[base.id])
            r2 = _box_ref(base, bname)
            if r2 and r2[0] == "runstats":
                res.tally_stores.add(TALLY_NAME.get(r2[1], r2[1]))
        # resolve の口
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name) and node.func.value.id in ("R", "RES", "resolve")):
            res.resolve_calls.add(node.func.attr)
        # engine.systems の中の補助(推移的に)
        target = None
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id in aliases):
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
    _alias_refs(fdef, bname, res)
    return res


def _alias_refs(fdef: ast.FunctionDef, bname: str, res: SystemCode) -> None:
    """``sc = b.scratch``・``L, rs = b.layers, b.runstats`` のような箱の別名を通した ``sc.<欄>`` も箱の参照に数える。"""
    alias: dict[str, str] = {}
    for node in ast.walk(fdef):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt, val = node.targets[0], node.value
            pairs = []
            if isinstance(tgt, ast.Tuple) and isinstance(val, ast.Tuple) and len(tgt.elts) == len(val.elts):
                pairs = list(zip(tgt.elts, val.elts))
            else:
                pairs = [(tgt, val)]
            for t, v in pairs:
                if (isinstance(t, ast.Name) and isinstance(v, ast.Attribute) and isinstance(v.value, ast.Name)
                        and v.value.id == bname and v.attr in BOXES):
                    alias[t.id] = v.attr
    if not alias:
        return
    for node in ast.walk(fdef):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in alias:
            box = alias[node.value.id]
            res.box_refs.add(f"{box}.{node.attr}")
            if isinstance(node.ctx, ast.Store):
                if box == "scratch":
                    res.scratch_stores.add(node.attr)
                if box == "runstats":
                    res.tally_stores.add(TALLY_NAME.get(node.attr, node.attr))
        if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Attribute) \
                and isinstance(node.target.value, ast.Name) and alias.get(node.target.value.id) == "runstats":
            res.tally_stores.add(TALLY_NAME.get(node.target.attr, node.target.attr))


def analyze_spec(spec: Any) -> SystemCode | None:
    if spec.fn is None:
        return None
    return analyze(spec.fn)


def source_root() -> Path:
    return Path(__file__).resolve().parent
