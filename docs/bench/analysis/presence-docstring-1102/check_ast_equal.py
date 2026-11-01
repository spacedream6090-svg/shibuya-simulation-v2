"""2 つの Python ファイルが docstring を除いて同じ構文木かを確かめる(標準ライブラリだけ・11-02)。

使い方: python check_ast_equal.py <前の版.py> <後の版.py>

両方を ``ast.parse`` で読み、モジュール・クラス・関数(async を含む)の先頭の文字列の文(docstring)を
外してから ``ast.dump``(行番号なし)を比べる。注釈(``#`` のコメント)は構文木に入らないので比べない。
同じなら exit 0・違えば最初に食い違う箇所の前後を出して exit 1。
"""

from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path

_DOC_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _strip_docstrings(tree: ast.AST) -> int:
    """木の中の docstring を外す(外した数を返す)。本体が docstring だけなら ``pass`` を置く。"""
    n = 0
    for node in ast.walk(tree):
        if not isinstance(node, _DOC_OWNERS):
            continue
        body = node.body
        if (body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            node.body = body[1:] or [ast.Pass()]
            n += 1
    return n


def _dump(path: Path) -> tuple[str, int, int]:
    src = path.read_bytes().decode("utf-8")
    tree = ast.parse(src, filename=str(path))
    n_doc = _strip_docstrings(tree)
    n_nodes = sum(1 for _ in ast.walk(tree))
    return ast.dump(tree, include_attributes=False), n_doc, n_nodes


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    a, b = Path(argv[1]), Path(argv[2])
    da, na, ka = _dump(a)
    db, nb, kb = _dump(b)
    ha = hashlib.sha256(da.encode("utf-8")).hexdigest()
    hb = hashlib.sha256(db.encode("utf-8")).hexdigest()
    print(f"before: docstrings={na} nodes(after strip)={ka} dump_sha256={ha}")
    print(f"after : docstrings={nb} nodes(after strip)={kb} dump_sha256={hb}")
    if da == db:
        print("RESULT: EQUAL (docstring を除いた構文木が同一)")
        return 0
    i = next((k for k in range(min(len(da), len(db))) if da[k] != db[k]), min(len(da), len(db)))
    print("RESULT: DIFFERENT")
    print("before ...", da[max(0, i - 120):i + 120])
    print("after  ...", db[max(0, i - 120):i + 120])
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
