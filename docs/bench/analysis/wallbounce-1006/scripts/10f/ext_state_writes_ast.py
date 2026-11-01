"""10f の材料(軸 2=「再開で戻す要るか」の静的な候補): 持ち主のクラスの属性のうち、``__init__`` の外のメソッドで
書き換える(代入・``+=``・``self.x[...] =``・``self.x.append/extend/pop/clear/update/add/...``)属性を数え、台帳の
軸 2 と除外の分類に突き合わせる(src は読むだけ)。

考え方(実行役の自前の構成=未リサーチ(expedient)): ラン中に書き換わり、別の時点で読まれる属性は「tick をまたぐ
状態」の候補。軸 2 が ``discardable`` か、除外の分類が ``const``(定数・設定)なのに ``__init__`` の外で書き換わる
属性は、保存し忘れの候補として人が見る。10d で漏れた 14 項目がこの規則で拾えるかを確かめる。

使い方::

    python docs/bench/analysis/wallbounce-1006/scripts/10f/ext_state_writes_ast.py --out <json>
"""

from __future__ import annotations

import argparse
import ast
import collections
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
SRC = REPO / "src" / "shibuya"
MUTATORS = {"append", "extend", "pop", "popitem", "clear", "update", "add", "discard", "remove", "insert",
            "setdefault", "appendleft", "popleft", "sort", "fill", "move_to_end"}
INIT_LIKE = {"__init__", "__post_init__"}
LEAKED_14 = {
    "presence._pulled_in_today", "classical._ipf_cache", "conv.n_opened",
    "ledger.money._snap", "ledger.money._flow_daily", "ledger.money._raw_pos", "ledger.money._raw_head",
    "ledger.money._day_marks", "ledger.money.n_raw_dropped", "ledger.money.n_transfers",
    "ledger.goods._dl_pos", "ledger.goods._dl_head", "ledger.goods._dl_marks", "ledger.goods.n_delivery_dropped",
}


def _self_attr(t: ast.AST) -> str | None:
    while isinstance(t, ast.Subscript):
        t = t.value
    if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
        return t.attr
    return None


def mutated_outside_init(tree: ast.Module, cls: str) -> dict[str, list[str]]:
    c = next((n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == cls), None)
    out: dict[str, list[str]] = collections.defaultdict(list)
    if c is None:
        return out
    for fn in c.body:
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) or fn.name in INIT_LIKE:
            continue
        for n in ast.walk(fn):
            names: list[str] = []
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    for e in (t.elts if isinstance(t, (ast.Tuple, ast.List)) else [t]):
                        a = _self_attr(e)
                        if a:
                            names.append(a)
            elif isinstance(n, (ast.AugAssign, ast.AnnAssign)):
                a = _self_attr(n.target)
                if a:
                    names.append(a)
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in MUTATORS:
                a = _self_attr(n.func.value)
                if a:
                    names.append(a)
            elif isinstance(n, ast.Delete):
                for t in n.targets:
                    a = _self_attr(t)
                    if a:
                        names.append(a)
            for a in names:
                out[a].append(f"{fn.name}:{n.lineno}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    sys.path.insert(0, str(REPO / "src"))
    from shibuya.engine import state_ledger as SL

    t0 = time.perf_counter()
    trees: dict[str, ast.Module] = {}
    attr_info: dict[str, dict] = {}
    for r in SL.external_rows():
        for it in r.items:
            if it in SL.OWNER_CLASSES:
                continue
            owner, attr = it.rsplit(".", 1)
            if owner in SL.OWNER_CLASSES:
                attr_info[it] = {"kind": "row", "row": r.key, "behavior": r.behavior, "restore": r.restore}
    for owner, attrs in SL.excluded_attrs().items():
        for attr, e in attrs.items():
            attr_info[f"{owner}.{attr}"] = {"kind": "excluded", "excl_kind": e.kind}
    mutated: dict[str, list[str]] = {}
    for owner, (rel, cls) in SL.OWNER_CLASSES.items():
        classes = [(rel, cls)] + list(SL.OWNER_ALT_CLASSES.get(owner, ()))
        for rel2, cls2 in classes:
            if rel2 not in trees:
                trees[rel2] = ast.parse((SRC / rel2).read_text(encoding="utf-8"))
            for attr, where in mutated_outside_init(trees[rel2], cls2).items():
                mutated.setdefault(f"{owner}.{attr}", []).extend(where)
    secs = time.perf_counter() - t0

    def bucket(path: str) -> str:
        info = attr_info.get(path)
        if info is None:
            return "台帳にも除外にも無い(網羅の検査が落とすはず)"
        if info["kind"] == "row":
            return f"行・軸 2={info['restore']}"
        return f"除外・{info['excl_kind']}"

    by_bucket = collections.Counter(bucket(p) for p in mutated)
    flagged = sorted(p for p in mutated if bucket(p) in ("行・軸 2=discardable", "除外・const", "除外・cache"))
    flagged_rows = {p: {"bucket": bucket(p), "where": mutated[p][:4]} for p in flagged}
    leaked_hit = {p: (p in mutated) for p in sorted(LEAKED_14)}
    out = {
        "schema": "10f/ext_state_writes_ast/1",
        "seconds": round(secs, 3),
        "n_attrs_mutated_outside_init": len(mutated),
        "by_bucket": dict(by_bucket),
        "leaked_10d_mutated_outside_init": leaked_hit,
        "n_flagged(discardable・const・cache で __init__ の外で書き換わる)": len(flagged),
        "flagged": flagged_rows,
    }
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("seconds", "n_attrs_mutated_outside_init", "by_bucket",
                                          "n_flagged(discardable・const・cache で __init__ の外で書き換わる)")},
                     ensure_ascii=False, indent=1))
    print("leaked hit:", sum(leaked_hit.values()), "/", len(leaked_hit), [k for k, v in leaked_hit.items() if not v])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
