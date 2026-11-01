"""系ごとの「書いてよい SoA の列」を作る(HEAD 0389689・読むだけ)。〔改訂(第330・検収 K4)〕

宣言の正 = 静的な閉包: 系が呼ぶ resolve の口(``resolve_ops``)から resolve.py の中の呼び出しをたどった関数の、
AST で見える書き(``state_ledger_ast._is_write``)の和 + 手で書いた別名の表(AST で見えない書き)。
置き場(agents・cells・pois・perception)は書きの式の手前の文字列から決める(``pois``→pois・``cells``→cells・
``pstate``/``perception``→perception・ほか→agents)。

``resolve_ops`` の素案は、6 構成で系ごとに実際に呼ばれた口(rcalls_*.json)。本番の宣言は手で書く表で、
6 構成で通らない腕の口は手で足す(草案 §2-5)。動的な観測(dyn_agg.json)は**漏れの検査**にだけ使う:
観測で変わった列 ⊆ 宣言、を確かめ、外れた列を ``leaks`` に出す。
"""
from __future__ import annotations

import ast
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

from shibuya.engine import state_ledger_ast as A

HERE = Path(sys.argv[1])
SRC = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("src/shibuya")

#: AST で見えない書き(手で書く別名の表・根拠つき)。
ALIAS_WRITES: dict[str, tuple[tuple[str, ...], str]] = {
    "_complete_buy": (("agents.money",), "economy/ledger.py:_apply_cash が世帯の現金=agents.money を np.add.at で書く(別名)"),
    "_complete_eat": (("agents.money",), "同上(purchase_many)"),
    "apply_detection": (("agents.fatigue_stage", "agents.hunger_stage", "agents.thermal_stage"),
                        "registry.field(crossing.stage_field)[...] = の名前の変数で書く(AST で解けない)"),
}

tree = ast.parse((SRC / "engine/resolve.py").read_text(encoding="utf-8"))
par = A._parents(tree)
funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
decl = A.declared_columns(SRC)
names = {c for v in decl.values() for c in v}


def place_of(expr_text: str) -> str:
    if "pois" in expr_text:
        return "pois"
    if "cells" in expr_text:
        return "cells"
    if "pstate" in expr_text or "perception" in expr_text:
        return "perception"
    return "agents"


#: モジュールの頂上の表(辞書・組)に入っている関数の名(表の名 → 関数の名)。
tables: dict[str, set[str]] = {}
for n in tree.body:
    tgt = n.targets[0] if isinstance(n, ast.Assign) and len(n.targets) == 1 else (n.target if isinstance(n, ast.AnnAssign) else None)
    if isinstance(tgt, ast.Name) and getattr(n, "value", None) is not None:
        refs = {x.id for x in ast.walk(n.value) if isinstance(x, ast.Name) and (x.id in funcs or x.id in tables)}
        refs = set().union(*({r} if r in funcs else tables[r] for r in refs)) if refs else set()
        if refs:
            tables[tgt.id] = refs  # 表が別の表を含むとき({**_APPLY, ...})は中の関数まで開く
direct_w: dict[str, set[str]] = defaultdict(set)
alias_hits: list = []
calls: dict[str, set[str]] = defaultdict(set)
for fname, fn in funcs.items():
    for node in ast.walk(fn):
        if isinstance(node, ast.Attribute) and node.attr in names and A._is_write(node, par) \
                and not isinstance(node.ctx, ast.Store):
            direct_w[fname].add(f"{place_of(ast.unparse(node.value))}.{node.attr}")
        if isinstance(node, ast.Attribute) and node.attr in names and isinstance(node.ctx, ast.Store):
            direct_w[fname].add(f"{place_of(ast.unparse(node.value))}.{node.attr}")
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del)):
            v = node.value
            if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and v.func.attr == "field" \
                    and v.args and isinstance(v.args[0], ast.Constant) and v.args[0].value in names:
                direct_w[fname].add(f"{place_of(ast.unparse(v.func.value))}.{v.args[0].value}")
        # 呼び出しだけでなく名前の参照も辺にする(_HANDLERS = {ACT_TALK: _apply_talk} のような表を通す呼び出し)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in funcs and node.id != fname:
                calls[fname].add(node.id)
            elif node.id in tables:
                calls[fname] |= tables[node.id]
    # 局所の別名(holdings = agents.registry.holdings → np.add.at(holdings, ...)・cur[...] = )の書きも拾う
    alias = {}
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)                 and isinstance(node.value, ast.Attribute) and node.value.attr in names:
            alias[node.targets[0].id] = f"{place_of(ast.unparse(node.value.value))}.{node.value.attr}"
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "at"                 and node.args and isinstance(node.args[0], ast.Name) and node.args[0].id in alias:
            direct_w[fname].add(alias[node.args[0].id]); alias_hits.append((fname, node.lineno, node.args[0].id))
        if isinstance(node, (ast.Assign, ast.AugAssign)):
            for x in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                if isinstance(x, ast.Subscript) and isinstance(x.value, ast.Name) and x.value.id in alias:
                    direct_w[fname].add(alias[x.value.id]); alias_hits.append((fname, node.lineno, x.value.id))
    if fname in ALIAS_WRITES:
        direct_w[fname] |= set(ALIAS_WRITES[fname][0])


def closure(fn: str) -> set[str]:
    seen, stack = set(), [fn]
    while stack:
        f = stack.pop()
        if f in seen:
            continue
        seen.add(f)
        stack.extend(calls.get(f, ()))
    return seen


called: dict[str, set[str]] = defaultdict(set)
for f in glob.glob(str(HERE / "rcalls_*.json")):
    d = json.loads(Path(f).read_text(encoding="utf-8"))
    for s, fns in d["by_segment"].items():
        called[s] |= set(fns)
agg = json.loads((HERE / "dyn_agg.json").read_text(encoding="utf-8"))
order = [s for s in agg["order"] if s != "END"]
allow, leaks = {}, {}
for s in order:
    ops = sorted(called.get(s, ()))
    reach = set().union(*(closure(o) for o in ops)) if ops else set()
    stat = set().union(*(direct_w.get(f, set()) for f in reach)) if reach else set()
    seen = set(agg["segments"].get(s, {}).get("soa", []))
    allow[s] = {"resolve_ops_observed": ops, "resolve_closure": sorted(reach), "allow": sorted(stat),
                "observed_changed": sorted(seen), "leaks": sorted(seen - stat)}
    if seen - stat:
        leaks[s] = sorted(seen - stat)
out = {s: allow[s] for s in order}
(HERE / "allow.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
(HERE / "alias_writes.json").write_text(json.dumps({k: {"writes": list(v[0]), "why": v[1]} for k, v in ALIAS_WRITES.items()},
                                                  ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("局所の別名の書き:", alias_hits)
for s in order:
    print(s, len(allow[s]["allow"]), "ops", len(allow[s]["resolve_ops_observed"]), "leaks", allow[s]["leaks"])
print("systems with leaks:", leaks)
