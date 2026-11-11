"""古い commit の写し(試験の材料)を固定する道具(試験の補助)。

写し(``tests/perception/facts/head_renderer_136fdbb.py``・``tests/economy/cp2/head_*_136fdbb.py``)は古い commit の
ファイルのバイトそのままで、中に ``shibuya`` を読む import の文がある。コードの区分の移動(段 4)では、移す道具が
ほかのファイルと同じく import の文のモジュールの道を書き換え、行き先が 2 つ以上に分かれる文は分ける(分けた文の順は
段の当て方で入れ替わることがある)。だから固定は次の 3 つにする(親の決定 10・検収 M-1 の後の改め)。

1. **字面**(:func:`text_sha256`): ``shibuya`` を読む import の文は取り除かず、**その位置に印の行を残す**。隣り合う文(間に
   空行か注だけ)は 1 つの束にまとめ、束ごとに「字下げ・空行の数・置く名を並べた一覧・束の中の注(行末と括弧の中と、文の
   間の注の行)を並べた一覧」を 1 行に書く。その全体の sha256。束の外の全部のバイトと、束の位置・字下げ・空行・置く名・注を
   覆う。覆わないのは、読むモジュールの道と、束の中の文の分け方と順。
2. **文の順**(:func:`statement_names`・:func:`order_problems`): 束の中で、元の文ごとの置く名の組が元の順に並ぶ(1 本の文が
   2 本以上に分かれてよい。分けた文どうしの順は問わない)。2 本の文の入れ替えや、名を別の文へ移す形を止める。
3. **意味**(:func:`refs` と :func:`ref_problems`・写しを読み込んだ後): import の文が置いた名ごとに、指している物の**元の
   置き場**(``tests/_places.py`` の対応で、今の置き場 → 元の置き場)。モジュールは元のモジュールの名、関数とクラスは
   (元のモジュールの名, ``__qualname__``)、それ以外の値は(文が読むモジュールが包みの頭でなければその元の名, 値の ``repr``
   の sha256 の頭 16 字)。別名の入れ替えや、別名はそのままで読む名だけを替える形を止める。

固定の表の名は ``shibuya.`` を外して書く(凍結の名と同じく、移す道具に書き換えさせない=元の置き場の名のまま)。
移す前の木でも、移した後の木でも同じ値になる。

逐次ループ宣言: なし(試験の道具)。
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import io
import json
import tokenize
from collections import Counter
from pathlib import Path
from types import ModuleType

from tests import _places as PL

ROOT_NAME = PL.PKG.name


def _is_shibuya(name: str | None) -> bool:
    return name is not None and (name == ROOT_NAME or name.startswith(ROOT_NAME + "."))


def shibuya_imports(tree: ast.AST) -> list[ast.Import | ast.ImportFrom]:
    """``shibuya`` を読む import の文(関数の中も含む・相対の import は数えない)。"""
    out: list[ast.Import | ast.ImportFrom] = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import) and any(_is_shibuya(a.name) for a in n.names):
            out.append(n)
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and _is_shibuya(n.module):
            out.append(n)
    return sorted(out, key=lambda n: (n.lineno, n.col_offset))


def _bound(n: ast.Import | ast.ImportFrom) -> list[str]:
    """文が名前空間に置く名(``as`` の名か読む名。``import shibuya.x`` は ``shibuya``)を文の中の順に。"""
    if isinstance(n, ast.Import):
        return [a.asname or a.name.partition(".")[0] for a in n.names]
    return [a.asname or a.name for a in n.names]


def _data(path: Path, lf: bool) -> bytes:
    data = path.read_bytes()
    return data.replace(b"\r\n", b"\n") if lf else data


def _bundles(data: bytes, stmts: list[ast.Import | ast.ImportFrom]) -> list[list[ast.Import | ast.ImportFrom]]:
    """隣り合う文(間の行が空か注だけ)を束にまとめる。"""
    lines = data.splitlines(keepends=True)
    out: list[list[ast.Import | ast.ImportFrom]] = []
    for n in stmts:
        if out:
            prev = out[-1][-1]
            between = lines[prev.end_lineno: n.lineno - 1]
            if prev.end_lineno < n.lineno and all(not ln.strip() or ln.strip().startswith(b"#") for ln in between):
                out[-1].append(n)
                continue
        out.append([n])
    return out


def _parsed(path: Path, lf: bool) -> tuple[bytes, list[bytes], list[list[ast.Import | ast.ImportFrom]]]:
    data = _data(path, lf)
    tree = ast.parse(data)
    lines = data.splitlines(keepends=True)
    stmts = shibuya_imports(tree)
    for n in stmts:
        assert n.end_lineno is not None and n.end_col_offset is not None
        # col_offset と end_col_offset は UTF-8 のバイトの位置
        head = lines[n.lineno - 1][: n.col_offset]
        assert not head.strip(), f"{path.name}:{n.lineno}: import の文の前に別の字がある"
        tail = lines[n.end_lineno - 1][n.end_col_offset:].strip()
        assert not tail or tail.startswith(b"#"), f"{path.name}:{n.end_lineno}: import の文の後に別の文がある"
    return data, lines, _bundles(data, stmts)


def text_sha256(path: Path, *, lf: bool = False) -> str:
    """字面の固定: 束を印の行に替えた全体の sha256(``lf`` なら先に CRLF を LF に揃える)。"""
    data, lines, bundles = _parsed(path, lf)
    comments: list[tuple[int, str]] = [(t.start[0], t.string) for t in tokenize.tokenize(io.BytesIO(data).readline)
                                       if t.type == tokenize.COMMENT]
    replace: dict[int, bytes] = {}
    drop: set[int] = set()
    for b in bundles:
        first, last = b[0].lineno, b[-1].end_lineno
        assert last is not None
        mark = {
            "indent": sorted({n.col_offset for n in b}),  # 文の数に依らない(1 本の文を分けても同じ)
            "blank": sum(1 for ln in lines[first - 1: last] if not ln.strip()),
            "names": sorted(x for n in b for x in _bound(n)),
            "comments": sorted(s for row, s in comments if first <= row <= last),
        }
        replace[first - 1] = b"#<shibuya-import-bundle " + json.dumps(mark, ensure_ascii=False).encode("utf-8") + b">\n"
        drop.update(range(first - 1, last))
    out = b"".join(replace.get(i, b"") if i in drop else ln for i, ln in enumerate(lines))
    return hashlib.sha256(out).hexdigest()


def statement_names(path: Path, *, lf: bool = False) -> tuple[tuple[tuple[str, ...], ...], ...]:
    """束ごとに、文ごとの置く名(文の中の順)。移す前の写しで作ったものが文の順の固定の表になる。"""
    _data_, _lines, bundles = _parsed(path, lf)
    return tuple(tuple(tuple(_bound(n)) for n in b) for b in bundles)


def order_problems(path: Path, want: tuple[tuple[tuple[str, ...], ...], ...], *, lf: bool = False) -> list[str]:
    """文の順の固定と違う所: 束の数・束ごとに、文を元の文の組の順に、組の名を使い切るまで割り当てられるか。"""
    got = statement_names(path, lf=lf)
    if len(got) != len(want):
        return [f"束の数 {len(got)}(固定 {len(want)})"]
    out: list[str] = []
    for k, (gb, wb) in enumerate(zip(got, want)):
        i, rest = 0, Counter()
        for s in gb:
            if not rest:
                if i >= len(wb):
                    out.append(f"束 {k}: 元の文より後に余る文 {s}")
                    break
                rest = Counter(wb[i])
                i += 1
            if Counter(s) - rest:
                out.append(f"束 {k}: 文 {s} が元の {i - 1} 番目の文 {wb[i - 1]} の名に収まらない")
                break
            rest -= Counter(s)
        else:
            if rest or i != len(wb):
                out.append(f"束 {k}: 元の文の名が足りない(残り {sorted(rest.elements())}・使った組 {i}/{len(wb)})")
    return out


def _short(name: str) -> str:
    """固定の表に書くモジュールの名(``shibuya.`` を外す・根は ``<root>``・外のモジュールは ``ext:``)。"""
    if name == ROOT_NAME:
        return "<root>"
    if name.startswith(ROOT_NAME + "."):
        return name[len(ROOT_NAME) + 1:]
    return "ext:" + name


def _describe(obj: object, stmt_module: str) -> str:
    if inspect.ismodule(obj):
        return f"module {_short(PL.origin_module(obj.__name__))}"
    mod, qual = getattr(obj, "__module__", None), getattr(obj, "__qualname__", None)
    if isinstance(mod, str) and isinstance(qual, str) and (isinstance(obj, type) or callable(obj)):
        return f"def {_short(PL.origin_module(mod))} {qual}"
    # 集合は要素の repr を並べて書く(文字列の集合の並びはハッシュの種で変わる)
    r = (f"{type(obj).__name__}{sorted(map(repr, obj))!r}" if isinstance(obj, (set, frozenset)) else repr(obj))
    assert " at 0x" not in r, f"repr に番地が入る値は固定できない: {r[:80]}"
    where = _short(PL.origin_module(stmt_module)) if stmt_module else "-"
    return f"value {where} {hashlib.sha256(r.encode('utf-8')).hexdigest()[:16]}"


def refs(mod: ModuleType, path: Path, *, lf: bool = False) -> dict[str, str]:
    """意味の固定: 読み込んだ写し ``mod`` の、``shibuya`` を読む import の文が置いた名 → 指す物の元の置き場。

    文はモジュールの頂上にあること(関数の中の文は名前空間に名を置かないので、ここでは止める)。値の文が読むモジュールは、
    木のモジュールで包みの頭でなければ元の名を書く(頭からの再輸出は、移す道具が定義したモジュールへ向け直すので書かない)。
    """
    tree = ast.parse(_data(path, lf))
    top = {id(n) for n in tree.body}
    out: dict[str, str] = {}
    for n in shibuya_imports(tree):
        assert id(n) in top, f"{path.name}:{n.lineno}: shibuya を読む import の文がモジュールの頂上に無い"
        stmt_module = ""
        if isinstance(n, ast.ImportFrom):
            rel = PL._rel_by_module().get(n.module or "")
            stmt_module = n.module if rel is not None and not rel.endswith("__init__.py") else ""
        for name in _bound(n):
            assert name not in out, f"{path.name}: 名 {name} を 2 回置く"
            out[name] = _describe(getattr(mod, name), stmt_module)
    return dict(sorted(out.items()))


def ref_problems(mod: ModuleType, path: Path, want: dict[str, str], *, lf: bool = False) -> list[str]:
    got = refs(mod, path, lf=lf)
    return [f"{k}: {got.get(k)!r}(固定 {want.get(k)!r})" for k in sorted(set(got) | set(want)) if got.get(k) != want.get(k)]
