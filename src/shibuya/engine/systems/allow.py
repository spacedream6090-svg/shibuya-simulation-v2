"""engine.systems.allow — 系の「書いてよい SoA の列」を resolve の口の静的な閉包から作る(第 1 期 1-0・段 A)。

草案 §2-5〔親の決め〕: **宣言の正は静的な閉包**。系の宣言 ``resolve_ops``(呼んでよい resolve の口=手で書く表)から、
``engine/resolve.py`` の中の呼び出しをたどった関数の、AST で見える書き+手で書く別名の表(AST で見えない書き)の和を
``writes.soa`` にする(手で書かない)。動的な観測(試験のランで系の前後に変わった列)は**漏れの検査**にだけ使う。

試作 ``docs/bench/analysis/wallbounce-1012/run-day-decomp/build_allow.py`` を正式な道具にしたもの(規則は同じ):

- 辺 = 関数の中の名前の参照(呼び出しに限らない。``_APPLY = {ACT_TALK: _apply_talk}`` のような頂上の表を通す呼び出しも、
  表の中の関数まで開く。表が別の表を含む ``{**_APPLY, ...}`` も開く)。
- 書き = ``state_ledger_ast._is_write`` の形(代入の左辺・``X.c[...] =``・``np.*.at(X.c, ...)``・``fill``・``out=``)+
  ``X.field("c")[...] =`` + 局所の別名(``holdings = agents.registry.holdings`` → ``np.add.at(holdings, ...)``・``cur[...] =``)。
- 置き場は書きの式の手前の文字列で決める(``pois``→pois・``cells``→cells・``pstate``/``perception``→perception・
  ほか→agents)。同じ名の列(``pois.cell`` など)が余分に入る=閉包は**上限**(「宣言の外」は「閉包の外」の意味)。

限界(草案 §6・再検収 §3): resolve.py の外へ出る呼び出し(台帳・在庫・``rail.pay_fares``)はたどらない=手の表
``ALIAS_WRITES`` に頼る。描画と方策へ差し込んだ関数を通る経路は ``resolve_ops`` を手で書く。

逐次ループ宣言: なし(AST の走査は起動時に 1 回・関数の数ぶん)。
"""

from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterable

__all__ = ["ALIAS_WRITES", "ResolveIndex", "index", "closure", "writes_for_ops", "place_of", "src_root"]

#: AST で見えない書き(手で書く別名の表・根拠つき)。関数の名 → (書く列, 根拠)。
#: 〔第330・再検収の残る点 (1)〕``_board_riders`` と ``initialize`` の台帳越しの ``agents.money`` を足した
#: (どちらも ``money`` を属性で直接も書くので許可は変わらない=表を「AST で見えない書きの全部」にするため)。
ALIAS_WRITES: dict[str, tuple[tuple[str, ...], str]] = {
    "_complete_buy": (("agents.money",),
                      "economy/ledger.py:_apply_cash が世帯の現金=agents.money を np.add.at で書く(別名・purchase_many)"),
    "_complete_eat": (("agents.money",), "同上(purchase_many)"),
    "_board_riders": (("agents.money",),
                      "運賃: out.rail.pay_fares → engine/processes/rail.py → ledger.transfer_many → _apply_cash(別名)"),
    "initialize": (("agents.money",),
                   "初期の財布: endow_households → ledger.transfer_many → _apply_cash(別名・組み立ての中)"),
    "apply_detection": (("agents.fatigue_stage", "agents.hunger_stage", "agents.thermal_stage"),
                        "registry.field(crossing.stage_field)[...] = の名前の変数で書く(AST で解けない)"),
}


def src_root() -> Path:
    """``src/shibuya`` の場所(このファイルから 2 つ上)。"""
    return Path(__file__).resolve().parents[2]


def place_of(expr_text: str) -> str:
    """書きの式の手前の文字列から置き場を決める(``pois``・``cells``・``perception``・ほかは ``agents``)。"""
    if "pois" in expr_text:
        return "pois"
    if "cells" in expr_text:
        return "cells"
    if "pstate" in expr_text or "perception" in expr_text:
        return "perception"
    return "agents"


@dataclass
class ResolveIndex:
    """resolve.py の関数ごとの直接の書きと辺(静的)。"""

    funcs: frozenset[str]
    direct: dict[str, frozenset[str]]
    calls: dict[str, frozenset[str]]
    #: 局所の別名を通した書き(関数・行・別名)。
    alias_hits: tuple[tuple[str, int, str], ...] = ()
    tables: dict[str, frozenset[str]] = field(default_factory=dict)


@lru_cache(maxsize=4)
def index(root: str | None = None) -> ResolveIndex:
    """``engine/resolve.py`` を読んで関数ごとの書きと辺を作る(``root`` は ``src/shibuya``・既定はこのパッケージ)。"""
    from shibuya.engine import state_ledger_ast as A

    base = Path(root) if root is not None else src_root()
    tree = ast.parse((base / "engine" / "resolve.py").read_text(encoding="utf-8"))
    par = A._parents(tree)
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    decl = A.declared_columns(base)
    names = {c for v in decl.values() for c in v}

    tables: dict[str, set[str]] = {}
    for n in tree.body:
        tgt = (n.targets[0] if isinstance(n, ast.Assign) and len(n.targets) == 1
               else (n.target if isinstance(n, ast.AnnAssign) else None))
        if isinstance(tgt, ast.Name) and getattr(n, "value", None) is not None:
            refs = {x.id for x in ast.walk(n.value) if isinstance(x, ast.Name) and (x.id in funcs or x.id in tables)}
            refs = set().union(*({r} if r in funcs else tables[r] for r in refs)) if refs else set()
            if refs:
                tables[tgt.id] = refs
    direct: dict[str, set[str]] = defaultdict(set)
    calls: dict[str, set[str]] = defaultdict(set)
    alias_hits: list[tuple[str, int, str]] = []
    for fname, fn in funcs.items():
        for node in ast.walk(fn):
            if isinstance(node, ast.Attribute) and node.attr in names and A._is_write(node, par):
                direct[fname].add(f"{place_of(ast.unparse(node.value))}.{node.attr}")
            if isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del)):
                v = node.value
                if (isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and v.func.attr == "field"
                        and v.args and isinstance(v.args[0], ast.Constant) and v.args[0].value in names):
                    direct[fname].add(f"{place_of(ast.unparse(v.func.value))}.{v.args[0].value}")
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id in funcs and node.id != fname:
                    calls[fname].add(node.id)
                elif node.id in tables:
                    calls[fname] |= tables[node.id]
        alias: dict[str, str] = {}
        for node in ast.walk(fn):
            if (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                    and isinstance(node.value, ast.Attribute) and node.value.attr in names):
                alias[node.targets[0].id] = f"{place_of(ast.unparse(node.value.value))}.{node.value.attr}"
        for node in ast.walk(fn):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "at"
                    and node.args and isinstance(node.args[0], ast.Name) and node.args[0].id in alias):
                direct[fname].add(alias[node.args[0].id])
                alias_hits.append((fname, node.lineno, node.args[0].id))
            if isinstance(node, (ast.Assign, ast.AugAssign)):
                for x in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                    if isinstance(x, ast.Subscript) and isinstance(x.value, ast.Name) and x.value.id in alias:
                        direct[fname].add(alias[x.value.id])
                        alias_hits.append((fname, node.lineno, x.value.id))
        if fname in ALIAS_WRITES:
            direct[fname] |= set(ALIAS_WRITES[fname][0])
    return ResolveIndex(
        funcs=frozenset(funcs),
        direct={k: frozenset(v) for k, v in direct.items()},
        calls={k: frozenset(v) for k, v in calls.items()},
        alias_hits=tuple(sorted(set(alias_hits))),
        tables={k: frozenset(v) for k, v in tables.items()},
    )


def closure(ops: Iterable[str], idx: ResolveIndex | None = None) -> frozenset[str]:
    """resolve の口の集合から、resolve.py の中でたどれる関数の全部(口そのものを含む)。"""
    ix = idx if idx is not None else index()
    seen: set[str] = set()
    stack = [o for o in ops]
    while stack:
        f = stack.pop()
        if f in seen:
            continue
        seen.add(f)
        stack.extend(ix.calls.get(f, ()))
    return frozenset(seen)


def writes_for_ops(ops: Iterable[str], idx: ResolveIndex | None = None) -> frozenset[str]:
    """resolve の口の集合の静的な書き集合の閉包(``"agents.cell"`` の形)。=系の ``writes.soa``。"""
    ix = idx if idx is not None else index()
    out: set[str] = set()
    for f in closure(ops, ix):
        out |= ix.direct.get(f, frozenset())
    return frozenset(out)
