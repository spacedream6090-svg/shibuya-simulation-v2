# -*- coding: utf-8 -*-
"""固定の表 ``class_ids.py`` の鍵の書き換え(許可の一覧の (c))と鍵の守り。

- 鍵=今の「モジュール.クラス名」、値=凍結の名。鍵のモジュールの部分だけを対応表で新しい名にし、値は変えない。
- クラス名(``__qualname__``)は凍結の JSON(``tests/engine/state/class_ids_frozen.json``=凍結の名 → ``__qualname__``)から
  引く(鍵の末尾が ``.`` + ``__qualname__`` であることを確かめる)。
- 鍵の守り(再検収 L-a): 同じ ``__qualname__`` を持つクラスが 4 組ある(``Arbiter``・``GoodsLedger``・``Renderer``・
  ``Scheduler``)。書き換えた後の全行で、新しい鍵が対応表で古い鍵に戻り、その値が古い鍵の値と同じことを確かめる。対応表が
  1 対 1 でない(2 つの古いモジュールが同じ新しいモジュールへ行く)ときも止める。
- 並び: 表を作る道具(``docs/bench/analysis/move-346/tools/gen_class_ids.py``)は鍵の昇順で書くので、書き換えた後も
  鍵の昇順に並べ直す(1 行 1 組の表のときだけ。行の中身=鍵と値の組は変えない)。
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field

from pkgmove.model import Edit, Text


class ClassIdError(ValueError):
    """鍵の守りが止めた。"""


@dataclass
class ClassIdResult:
    edits: list[Edit] = field(default_factory=list)
    rewritten: int = 0
    resorted: bool = False


def find_table(tree: ast.Module, name: str = "CLASS_IDS") -> ast.Dict:
    for n in tree.body:
        tgt = n.target if isinstance(n, ast.AnnAssign) else (n.targets[0] if isinstance(n, ast.Assign) else None)
        if isinstance(tgt, ast.Name) and tgt.id == name:
            v = n.value
            d = v.args[0] if isinstance(v, ast.Call) else v
            if isinstance(d, ast.Dict):
                return d
    raise ClassIdError(f"{name} の表が見つからない")


def table_of(text: str) -> dict[str, str]:
    d = find_table(ast.parse(text))
    return {ast.literal_eval(k): ast.literal_eval(v) for k, v in zip(d.keys, d.values)}  # type: ignore[arg-type]


def _split_key(key: str, value: str, frozen_qual: dict[str, str]) -> tuple[str, str]:
    q = frozen_qual.get(value)
    if q is None:
        raise ClassIdError(f"凍結の JSON に無い値: {value}")
    if not key.endswith("." + q):
        raise ClassIdError(f"鍵の末尾が __qualname__ と違う: {key} ({q})")
    return key[: -(len(q) + 1)], q


def new_table(old: dict[str, str], modmap: dict[str, str], frozen_qual: dict[str, str]) -> dict[str, str]:
    """鍵だけを書き換えた表(値はそのまま)。"""
    out: dict[str, str] = {}
    for k, v in old.items():
        mod, q = _split_key(k, v, frozen_qual)
        nk = f"{modmap.get(mod, mod)}.{q}"
        if nk in out:
            raise ClassIdError(f"書き換えた鍵が重なる: {nk}")
        out[nk] = v
    return out


def check_keys(old: dict[str, str], new: dict[str, str], modmap: dict[str, str], frozen_qual: dict[str, str]) -> None:
    """鍵の守り: 全行で、新しい鍵が対応表で古い鍵に戻り、値が古い鍵の値と同じ。"""
    inv: dict[str, str] = {}
    for o, n in modmap.items():
        if n in inv and inv[n] != o:
            raise ClassIdError(f"対応表が 1 対 1 でない: {inv[n]} と {o} が {n} へ")
        inv[n] = o
    if len(new) != len(old):
        raise ClassIdError(f"表の行の数が変わった: {len(old)} → {len(new)}")
    if sorted(new.values()) != sorted(old.values()):
        raise ClassIdError("表の値(凍結の名)が変わった")
    for nk, v in new.items():
        mod, q = _split_key(nk, v, frozen_qual)
        back = f"{inv.get(mod, mod)}.{q}"
        if back not in old:
            raise ClassIdError(f"新しい鍵が対応表で古い鍵に戻らない: {nk} → {back}")
        if old[back] != v:
            raise ClassIdError(f"鍵の取り違え: {nk} の値 {v} が古い鍵 {back} の値 {old[back]} と違う")


def rewrite(text: str, modmap: dict[str, str], frozen_qual: dict[str, str], *,
            keyfn=None) -> tuple[str, ClassIdResult]:
    """``class_ids.py`` の文字列の鍵を書き換えた文字列と結果(鍵の守りを通らなければ :class:`ClassIdError`)。
    ``keyfn`` は試験の差し替えの口(鍵の表を作る関数=取り違えを入れた負の対照に使う)。"""
    tree = ast.parse(text)
    d = find_table(tree)
    t = Text(text)
    old = {ast.literal_eval(k): ast.literal_eval(v) for k, v in zip(d.keys, d.values)}  # type: ignore[arg-type]
    new = (keyfn or new_table)(old, modmap, frozen_qual)
    check_keys(old, new, modmap, frozen_qual)
    res = ClassIdResult()
    new_of_old = dict(zip(old.keys(), new.keys()))
    entries = list(zip(d.keys, d.values))
    one_per_line = all(k.lineno == v.end_lineno == k.end_lineno for k, v in entries)  # type: ignore[union-attr]
    lines_distinct = len({k.lineno for k, _ in entries}) == len(entries)  # type: ignore[union-attr]
    for k, _v in entries:
        ok_ = ast.literal_eval(k)  # type: ignore[arg-type]
        if new_of_old[ok_] != ok_:
            res.rewritten += 1
    if res.rewritten == 0:
        return text, res
    if one_per_line and lines_distinct:
        first = entries[0][0].lineno  # type: ignore[union-attr]
        last = entries[-1][0].lineno  # type: ignore[union-attr]
        rows: list[tuple[str, str]] = []
        for k, v in entries:
            ln = t.line(k.lineno)  # type: ignore[union-attr]
            ks, ke = t.span(k)
            ls = t.starts[k.lineno - 1]  # type: ignore[union-attr]
            line_text = ln[: ks - ls] + _requote(t.text[ks:ke], new_of_old[ast.literal_eval(k)]) + ln[ke - ls:]  # type: ignore[arg-type]
            rows.append((new_of_old[ast.literal_eval(k)], line_text))  # type: ignore[arg-type]
        between = [t.line(i) for i in range(first, last + 1)]
        if len(between) == len(rows):
            ordered = [lt for _k, lt in sorted(rows, key=lambda r: r[0])]
            res.resorted = [lt for _k, lt in rows] != ordered
            s = t.starts[first - 1]
            e = t.starts[last - 1] + len(t.line(last))
            res.edits.append(Edit(s, e, t.eol.join(ordered), "class_key", "CLASS_IDS", f"鍵 {res.rewritten}"))
            return _apply(text, res.edits), res
    for k, _v in entries:
        ok_ = ast.literal_eval(k)  # type: ignore[arg-type]
        if new_of_old[ok_] != ok_:
            ks, ke = t.span(k)
            res.edits.append(Edit(ks, ke, _requote(t.text[ks:ke], new_of_old[ok_]), "class_key", "CLASS_IDS", ok_))
    return _apply(text, res.edits), res


def _requote(lit: str, value: str) -> str:
    q = lit[0] if lit and lit[0] in "'\"" else '"'
    return f"{q}{value}{q}"


def _apply(text: str, edits: list[Edit]) -> str:
    from pkgmove.model import apply_edits

    return apply_edits(text, edits)
