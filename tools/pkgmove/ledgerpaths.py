# -*- coding: utf-8 -*-
"""(d) つなぎの台帳の道の対応の表 ``engine/bridging/ledger_paths.py`` の ``LEDGER_PATHS`` を書き足す(親の決定 1=案 (b))。

- 表は「今の道(リポの根からの道筋)→ 台帳に書いてある道」。段で移したファイル(``.py``・頭を除く)ごとに 1 行を足す。
  前の段で移したファイルをまた動かすときは、古い今の道の行を外し、台帳の道を引き継ぐ。
- 台帳(``docs/design/bridging-ledger.json``)は書き換えない。表は鍵の昇順・1 行 1 組で書く(dict の字面だけを書き換える)。
- 守り(:func:`check`): 表の今の道は木にある・台帳の道が重ならない・台帳のコードの行の道は全部、表を通して木の今の
  ファイルに届く。
"""
from __future__ import annotations

import ast
import json

from pkgmove.classids import find_table
from pkgmove.model import Text


class LedgerPathsError(ValueError):
    """表の守りが止めた。"""


def table_of(text: str) -> dict[str, str]:
    d = find_table(ast.parse(text), "LEDGER_PATHS")
    return {ast.literal_eval(k): ast.literal_eval(v) for k, v in zip(d.keys, d.values)}  # type: ignore[arg-type]


def updated(old: dict[str, str], moves: dict[str, str]) -> dict[str, str]:
    """``moves``(古い今の道 → 新しい今の道)を当てた表。"""
    out = dict(old)
    for o, n in moves.items():
        led = out.pop(o, o)
        if n in out:
            raise LedgerPathsError(f"表の今の道が重なる: {n}")
        out[n] = led
    vals = list(out.values())
    if len(vals) != len(set(vals)):
        raise LedgerPathsError("表の台帳の道が重なる")
    return dict(sorted(out.items()))


def rewrite(text: str, moves: dict[str, str]) -> tuple[str, int]:
    """表の字面を書き換えた文字列と、足した行の数。"""
    if not moves:
        return text, 0
    tree = ast.parse(text)
    d = find_table(tree, "LEDGER_PATHS")
    t = Text(text)
    s, e = t.span(d)
    new = updated(table_of(text), moves)
    eol = t.eol
    body = "".join(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},{eol}"
                   for k, v in new.items())
    lit = "{" + eol + body + "}"
    return text[:s] + lit + text[e:], len(moves)


def check(table: dict[str, str], exists, ledger_text: str | None) -> list[str]:
    """表の今の道は木にある・台帳の道が重ならない・台帳のコードの行の道は表を通して木にある。"""
    errs: list[str] = []
    for now in table:
        if not exists(now):
            errs.append(f"表の今の道が木に無い: {now}")
    vals = list(table.values())
    if len(vals) != len(set(vals)):
        errs.append("表の台帳の道が重なる")
    if ledger_text is not None:
        inv = {v: k for k, v in table.items()}
        rows = json.loads(ledger_text).get("bridges", [])
        for r in rows:
            di = str(r.get("declared_in", ""))
            if not di.startswith("src/") or "#" not in di:
                continue
            path = di.split("#", 1)[0].split(" ", 1)[0]
            cur = inv.get(path, path)
            if not exists(cur):
                errs.append(f"台帳の道が今のファイルに届かない: {r.get('id')} {path} → {cur}")
    return errs
