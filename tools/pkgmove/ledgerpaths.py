# -*- coding: utf-8 -*-
"""(d) つなぎの台帳の道の対応の表 ``engine/bridging/ledger_paths.py`` の ``LEDGER_PATHS`` を書き足す(親の決定 1=案 (b))。

- 表は「今の道(リポの根からの道筋)→ 台帳に書いてある道」。段で移したファイル(``.py``・頭を除く)ごとに 1 行を足す。
  前の段で移したファイルをまた動かすときは、古い今の道の行を外し、台帳の道を引き継ぐ。
- 台帳(``docs/design/bridging-ledger.json``)は書き換えない。表は鍵の昇順・1 行 1 組で書く(dict の字面だけを書き換える)。
- 守り(:func:`check`): 表の今の道は木にある・台帳の道が重ならない・台帳のコードの行の道は全部、表を通して木の今の
  ファイルに届く。

〔割る段 6・E7・親の裁定 Q1 の (ii)〕前向きだけの N 対 1 の表 ``LEDGER_PATHS_SPLIT``(:data:`SPLIT_TABLE`)。割る段で 2 つ目以降の
割り先になったファイルの今の道 → 台帳の道(値は ``LEDGER_PATHS`` の値と重なってよい)。字面は ``LEDGER_PATHS`` と同じ形。

- 前向きに引く(:func:`ledger_of`)のは ``LEDGER_PATHS`` → ``LEDGER_PATHS_SPLIT`` → そのまま、の順。逆向き(台帳の道 → 今の道)は
  ``LEDGER_PATHS`` だけ(:func:`check` の台帳の行の確かめも ``LEDGER_PATHS`` だけで引く)。
- 前向きの表に行を足すのは割る道具だけ(:func:`rewrite` の ``split_add``・手で足さない=裁定 Q1 の条件 ③)。表が無い木(src の側の
  下ごしらえ S6-A の前)に行を足そうとすれば「前向きの表が無い」で止める(黙って通さない)。
- 移す(``moves``)とき、前向きの表に載った今の道の鍵は前向きの表のまま付いて行く(``LEDGER_PATHS`` へ移らない=値が
  ``LEDGER_PATHS`` の値と重なってよいのは前向きの表だけ)。前向きの表は中身が変わったときだけ書き直す(字面を保つ)。
- 守り(:func:`check` の ``split``): 前向きの表の今の道は木にある・同じ今の道が 2 つの表の両方に無い。
"""
from __future__ import annotations

import ast
import json

from pkgmove.classids import ClassIdError, find_table
from pkgmove.model import Text

#: 1 対 1 の表と、〔割る段 6・E7〕前向きだけの N 対 1 の表の名(``ledger_paths.py`` の頂上の代入の左辺)。
MAIN_TABLE = "LEDGER_PATHS"
SPLIT_TABLE = "LEDGER_PATHS_SPLIT"


class LedgerPathsError(ValueError):
    """表の守りが止めた。"""


def table_of(text: str, name: str = MAIN_TABLE) -> dict[str, str]:
    d = find_table(ast.parse(text), name)
    return {ast.literal_eval(k): ast.literal_eval(v) for k, v in zip(d.keys, d.values)}  # type: ignore[arg-type]


def split_table_of(text: str) -> dict[str, str] | None:
    """〔E7〕前向きの表(``LEDGER_PATHS_SPLIT``)。木に表が無ければ ``None``。"""
    try:
        return table_of(text, SPLIT_TABLE)
    except ClassIdError:
        return None


def ledger_of(main: dict[str, str], split: dict[str, str] | None, path: str) -> str:
    """〔E7〕今の道 → 台帳の道(``LEDGER_PATHS`` → ``LEDGER_PATHS_SPLIT`` → そのまま、の順で引く)。"""
    if path in main:
        return main[path]
    if split and path in split:
        return split[path]
    return path


def updated(old: dict[str, str], moves: dict[str, str], *, unique_values: bool = True) -> dict[str, str]:
    """``moves``(古い今の道 → 新しい今の道)を当てた表。``unique_values`` が偽(前向きの表)なら台帳の道の重なりを許す。"""
    out = dict(old)
    for o, n in moves.items():
        led = out.pop(o, o)
        if n in out:
            raise LedgerPathsError(f"表の今の道が重なる: {n}")
        out[n] = led
    if unique_values:
        vals = list(out.values())
        if len(vals) != len(set(vals)):
            raise LedgerPathsError("表の台帳の道が重なる")
    return dict(sorted(out.items()))


def _render(text: str, name: str, table: dict[str, str]) -> tuple[int, int, str]:
    """表 ``name`` の dict の字面の位置と、``table`` を鍵の昇順・1 行 1 組で書いた字面(空なら ``{`` の次の行が ``}``)。"""
    d = find_table(ast.parse(text), name)
    t = Text(text)
    s, e = t.span(d)
    eol = t.eol
    body = "".join(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},{eol}"
                   for k, v in table.items())
    return s, e, "{" + eol + body + "}"


def rewrite(text: str, moves: dict[str, str], split_add: dict[str, str] | None = None) -> tuple[str, int]:
    """表の字面を書き換えた文字列と、足した行の数(移した行と、〔E7〕前向きの表に足した行)。

    〔割る段 6・E7〕``split_add``(2 つ目以降の割り先の今の道 → 台帳の道)は前向きの表に足す。前向きの表に載った今の道の移しは
    前向きの表のまま付いて行く。前向きの表が無い木に行を足そうとすれば :class:`LedgerPathsError`(前向きの表が無い)。"""
    add = dict(split_add or {})
    if not moves and not add:
        return text, 0
    main = table_of(text)
    split = split_table_of(text)
    if split is None:
        if add:
            raise LedgerPathsError(f"台帳の道の前向きの表 {SPLIT_TABLE} が無い(前向きの表が無い)=2 つ目以降の割り先 "
                                   f"{sorted(add)} のつなぎの宣言を表せない(src の側の表を先に入れる)")
        s, e, lit = _render(text, MAIN_TABLE, updated(main, moves))
        return text[:s] + lit + text[e:], len(moves)
    new_main = updated(main, {o: n for o, n in moves.items() if o not in split})
    new_split = updated(split, {o: n for o, n in moves.items() if o in split}, unique_values=False)
    for k, v in add.items():
        if k in new_split or k in new_main:
            raise LedgerPathsError(f"前向きの表に足す今の道が表に既に在る: {k}")
        new_split[k] = v
    new_split = dict(sorted(new_split.items()))
    both = sorted(set(new_main) & set(new_split))
    if both:
        raise LedgerPathsError(f"同じ今の道が 2 つの表の両方に在る: {both}")
    edits = [_render(text, MAIN_TABLE, new_main)]
    if new_split != split:
        edits.append(_render(text, SPLIT_TABLE, new_split))
    out = text
    for s, e, lit in sorted(edits, reverse=True):
        out = out[:s] + lit + out[e:]
    return out, len(moves) + len(add)


def check(table: dict[str, str], exists, ledger_text: str | None, split: dict[str, str] | None = None) -> list[str]:
    """表の今の道は木にある・台帳の道が重ならない・台帳のコードの行の道は表を通して木にある。〔E7〕``split``(前向きの表)を
    渡せば、その今の道も木にある・同じ今の道が 2 つの表の両方に無い(台帳の行の逆向きは ``table`` だけで引く)。"""
    errs: list[str] = []
    for now in table:
        if not exists(now):
            errs.append(f"表の今の道が木に無い: {now}")
    vals = list(table.values())
    if len(vals) != len(set(vals)):
        errs.append("表の台帳の道が重なる")
    if split:
        for now in split:
            if not exists(now):
                errs.append(f"前向きの表の今の道が木に無い: {now}")
        both = sorted(set(table) & set(split))
        if both:
            errs.append(f"同じ今の道が 2 つの表の両方に在る: {both}")
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
