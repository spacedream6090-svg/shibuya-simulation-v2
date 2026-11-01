"""10f の材料(K19): ``stream()``・``philox()`` の呼び手を AST で一覧にする(src は読むだけ)。

各呼び手について: 用途名(文字列か、モジュールの文字列定数を解決したもの)・カウンタの語の数・1 語目の式の種類
(無い / 定数 / 式)・返り値から引くメソッドと引数(静的に語数が決まるか)を出す。

静的に語数を決める規則(実行役の自前の構成=未リサーチ(expedient)):
- ``random()``・``integers(..)`` で size が無い → 1 語(31 bit 未満の整数は 1 語から 2 個取ることがあるが上限は 1)。
- ``random(n)``・``random((a, b))``・``random_raw(n)`` で n が定数 → n 語(倍精度の一様乱数は 1 語 1 個)。
- ``standard_normal``・``normal``・``exponential``・``lognormal``・``geometric``・``poisson``・``gamma`` など
  棄却のある分布 → 「不定(棄却)」。
- ``permutation``・``shuffle``・``choice(replace=False)``・size が式 → 「不定(大きさが式)」。

使い方::

    python docs/bench/analysis/wallbounce-1006/scripts/10f/stream_sites_ast.py --out <json>
"""

from __future__ import annotations

import argparse
import ast
import json
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
SRC = REPO / "src" / "shibuya"
FUNCS = {"stream", "philox"}
REJECT = {"standard_normal", "normal", "exponential", "lognormal", "geometric", "poisson", "gamma", "beta",
          "standard_exponential", "standard_gamma", "binomial", "negative_binomial", "zipf", "hypergeometric",
          "multinomial", "dirichlet", "multivariate_normal", "weibull", "pareto", "vonmises", "logseries"}
VARSIZE = {"permutation", "shuffle", "permuted", "choice"}


def _str_consts(tree: ast.Module) -> dict[str, str]:
    out: dict[str, str] = {}
    for n in tree.body:
        tg = None
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            tg, val = n.targets[0].id, n.value
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None:
            tg, val = n.target.id, n.value
        if tg and isinstance(val, ast.Constant) and isinstance(val.value, str):
            out[tg] = val.value
    return out


def _fname(call: ast.Call) -> str | None:
    f = call.func
    if isinstance(f, ast.Name) and f.id in FUNCS:
        return f.id
    if isinstance(f, ast.Attribute) and f.attr in FUNCS:
        return f.attr
    return None


def _domain(node: ast.AST | None, consts: dict[str, str]) -> str:
    if node is None:
        return "?"
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and node.id in consts:
        return consts[node.id]
    if isinstance(node, ast.JoinedStr):
        return "f-string:" + ast.unparse(node)
    return "expr:" + ast.unparse(node)


def _kind(node: ast.AST | None) -> str:
    if node is None:
        return "none"
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return f"const({node.value})"
    return "expr"


def _words(meth: str, call: ast.Call) -> str:
    size = None
    for kw in call.keywords:
        if kw.arg == "size":
            size = kw.value
    if meth in REJECT:
        return "不定(棄却)"
    if meth in VARSIZE:
        if meth == "choice" and size is None and len(call.args) <= 1 and not call.keywords:
            return "1"
        return "不定(大きさが式)" if meth != "choice" else "不定(choice)"
    if meth in {"random", "random_raw", "integers", "uniform", "bytes"}:
        arg = size
        if arg is None:
            if meth in {"random", "random_raw"} and call.args:
                arg = call.args[0]
            elif meth == "integers" and len(call.args) >= 3:
                arg = call.args[2]
            elif meth == "uniform" and len(call.args) >= 3:
                arg = call.args[2]
        if arg is None:
            return "1"
        if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
            return str(arg.value)
        if isinstance(arg, ast.Tuple) and all(isinstance(e, ast.Constant) for e in arg.elts):
            p = 1
            for e in arg.elts:
                p *= int(e.value)
            return str(p)
        return "不定(大きさが式)"
    return f"不明({meth})"


def scan() -> dict:
    t0 = time.perf_counter()
    sites = []
    files = [p for p in sorted(SRC.rglob("*.py")) if "build" not in p.relative_to(SRC).parts]
    for p in files:
        rel = p.relative_to(SRC).as_posix()
        if rel == "core/rng.py":
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        consts = _str_consts(tree)
        par: dict[ast.AST, ast.AST] = {}
        for n in ast.walk(tree):
            for ch in ast.iter_child_nodes(n):
                par[ch] = n
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            fn = _fname(n)
            if fn is None:
                continue
            args = n.args
            dom = _domain(args[1] if len(args) > 1 else None, consts)
            ctrs = args[2:]
            starred = any(isinstance(c, ast.Starred) for c in ctrs)
            draws: list[str] = []
            # 連鎖: stream(...).random(n) / Generator(philox(...)).xxx
            up = par.get(n)
            if isinstance(up, ast.Call) and isinstance(up.func, ast.Name) and up.func.id == "Generator":
                up = par.get(up)
                node_for_chain = par.get(n)
            else:
                node_for_chain = n
            pa = par.get(node_for_chain)
            if isinstance(pa, ast.Attribute) and isinstance(par.get(pa), ast.Call):
                draws.append(f"{pa.attr}:{_words(pa.attr, par[pa])}")
            # 代入: g = stream(...) → 同じ関数の中の g.xxx(...)
            st = pa
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], (ast.Name, ast.Attribute)):
                tgt = ast.unparse(st.targets[0])
                fn_node = st
                while fn_node is not None and not isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
                    fn_node = par.get(fn_node)
                for m in ast.walk(fn_node) if fn_node is not None else []:
                    if (isinstance(m, ast.Call) and isinstance(m.func, ast.Attribute)
                            and ast.unparse(m.func.value) == tgt):
                        draws.append(f"{m.func.attr}:{_words(m.func.attr, m)}")
                if not draws:
                    draws.append(f"(返り値を {tgt} に保持・同じ関数の中で引かない)")
            elif not draws:
                draws.append("(返り値を渡す・保持=静的には追えない)")
            fixed = [d.split(":", 1)[1] for d in draws if ":" in d]
            static_total = None
            if fixed and all(x.isdigit() for x in fixed):
                static_total = sum(int(x) for x in fixed)
            w0 = _kind(ctrs[0] if ctrs else None)
            if starred:
                w0 = "starred"
            risk = ("1 語目が定数か無い=隣の流れが無い" if (w0 == "none" or w0.startswith("const"))
                    else ("静的に 4 語以内" if static_total is not None and static_total <= 4
                          else ("静的に 4 語を超える" if static_total is not None else "静的には決まらない(実行時の検査が要る)")))
            sites.append({
                "path": rel, "line": n.lineno, "func": fn, "domain": dom, "n_counters": len(ctrs),
                "word0": w0, "word0_expr": ast.unparse(ctrs[0]) if ctrs else "", "draws": draws,
                "static_words": static_total, "verdict": risk,
            })
    summary: dict[str, int] = {}
    for s in sites:
        summary[s["verdict"]] = summary.get(s["verdict"], 0) + 1
    return {"schema": "10f/stream_sites_ast/1", "n_sites": len(sites), "files": len(files),
            "seconds": round(time.perf_counter() - t0, 3), "verdicts": summary, "sites": sites}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    res = scan()
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"n_sites": res["n_sites"], "seconds": res["seconds"], "verdicts": res["verdicts"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
