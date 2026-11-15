# -*- coding: utf-8 -*-
"""bytecheck.astsame — 文だけの直しの commit を、byte-check を回さずに確かめる(11-16 §1-12 の 2)。

src を変える commit のうち、docstring と注(コメント)だけを直したものは、ランを回さなくても
「docstring と注を除いた AST が前と同じ」ことを機械で確かめられる。本道具は、基準の commit と比べる側
(commit か今の作業木)で変わった ``.py`` を 1 本ずつ読み、次の 3 つに分ける。

- ``same``     : docstring と注のほかは同じ(AST が一致)。ランの値は変わらない。
- ``strings``  : 構造は同じで、値の文字列(docstring でない文字列の定数)だけが違う。警告の文・記録の文などが
                 変わりうるので、記録に「値の文字列が変わった」と書く(何か所か・どの行か)。
- ``structure``: 構造が違う(文だけの直しではない)。byte-check を回すこと。

足したファイル・消したファイル・名前を変えたファイルは ``structure`` に入れる(import の形が変わるため)。

    python tools/bytecheck/astsame.py --base <commit> [--head <commit>] [--paths src] [--out <記録の JSON>]

``--head`` を省くと今の作業木と比べる。終了コード: 0=全部 same・1=strings がある・2=structure がある(か誤り)。
文字列の中身は出さない(行の番号と長さだけ。``--show`` を付けたときだけ中身を出す)。

確かめないこと: ``.py`` でないファイル(JSON・TOML など)の中身・コメントに書かれた型の注(``# type:``)の働き・
実行時に docstring を読む作り(``__doc__`` を値として使う所)。最後のものは ``--doc-readers`` で数だけ出す。
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

SCHEMA = "shibuya.tools/bytecheck/astsame/1"

_DOC_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    """モジュール・クラス・関数の先頭の文字列の式(docstring)を取り除く。空になった本体には ``pass`` を置く。"""
    for node in ast.walk(tree):
        if isinstance(node, _DOC_OWNERS) and node.body:
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                node.body = node.body[1:] or [ast.Pass()]
    return tree


class _BlankStrings(ast.NodeTransformer):
    """文字列の定数を同じ印に置き換える(構造だけを比べるため)。"""

    def visit_Constant(self, node: ast.Constant) -> ast.AST:  # noqa: N802 - ast の決まりの名
        if isinstance(node.value, (str, bytes)):
            return ast.copy_location(ast.Constant(value="\x00"), node)
        return node


def _string_constants(tree: ast.AST) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)):
            value = node.value if isinstance(node.value, str) else node.value.decode("latin-1")
            out.append((getattr(node, "lineno", 0), value))
    return out


def _doc_readers(tree: ast.AST) -> int:
    """``__doc__`` を値として読む所の数(docstring を変えるとランの値が動きうる所)。"""
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "__doc__":
            n += 1
        elif isinstance(node, ast.Name) and node.id == "__doc__":
            n += 1
    return n


def compare_sources(old: str, new: str) -> dict[str, Any]:
    """2 つのソースを比べて、``verdict``(same・strings・structure)と数を返す。"""
    try:
        t_old = _strip_docstrings(ast.parse(old))
        t_new = _strip_docstrings(ast.parse(new))
    except SyntaxError as e:
        return {"verdict": "structure", "note": f"構文の誤り: {e.msg}(行 {e.lineno})"}
    doc_readers = _doc_readers(t_new)
    if ast.dump(t_old) == ast.dump(t_new):
        return {"verdict": "same", "doc_readers": doc_readers}
    s_old, s_new = _string_constants(t_old), _string_constants(t_new)
    b_old = ast.dump(_BlankStrings().visit(t_old))
    b_new = ast.dump(_BlankStrings().visit(t_new))
    if b_old == b_new and len(s_old) == len(s_new):
        changed = [
            {"line_old": lo, "line_new": ln, "len_old": len(vo), "len_new": len(vn), "old": vo, "new": vn}
            for (lo, vo), (ln, vn) in zip(s_old, s_new)
            if vo != vn
        ]
        return {"verdict": "strings", "changed_strings": changed, "doc_readers": doc_readers}
    return {"verdict": "structure", "doc_readers": doc_readers}


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} が失敗: {r.stderr.strip()[:300]}")
    return r.stdout


def _show(repo: Path, commit: str, path: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"git show {commit}:{path} が失敗: {r.stderr.decode('utf-8', 'replace').strip()[:300]}")
    return r.stdout.decode("utf-8")


def changed_files(repo: Path, base: str, head: str | None, paths: Sequence[str]) -> list[tuple[str, str]]:
    """基準と比べる側で変わったファイルの (状態, 道) の一覧(名前の変更は消した+足したに分ける)。"""
    args = ["diff", "--name-status", "--no-renames", base]
    if head:
        args.append(head)
    out = _git(repo, *args, "--", *paths)
    rows: list[tuple[str, str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        status, _, path = line.partition("\t")
        rows.append((status.strip()[:1], path.strip()))
    if not head:  # 作業木と比べるときは、追跡していない新しいファイルも足したものとして数える
        for line in _git(repo, "ls-files", "--others", "--exclude-standard", "--", *paths).splitlines():
            if line.strip():
                rows.append(("A", line.strip()))
    return sorted(set(rows), key=lambda r: r[1])


def check(repo: Path, base: str, head: str | None, paths: Sequence[str], show: bool = False) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for status, path in changed_files(repo, base, head, paths):
        row: dict[str, Any] = {"path": path, "status": status}
        if not path.endswith(".py"):
            row["verdict"] = "not_python"
        elif status != "M":
            row["verdict"] = "structure"
            row["note"] = "足したファイル" if status == "A" else "消したファイル"
        else:
            old = _show(repo, base, path)
            new = _show(repo, head, path) if head else (repo / path).read_text(encoding="utf-8")
            row.update(compare_sources(old, new))
            if "changed_strings" in row:
                row["n_changed_strings"] = len(row["changed_strings"])
                if not show:
                    for c in row["changed_strings"]:
                        c.pop("old", None)
                        c.pop("new", None)
        files.append(row)
    counts: dict[str, int] = {}
    for row in files:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    return {
        "schema": SCHEMA,
        "base": _git(repo, "rev-parse", base).strip(),
        "head": _git(repo, "rev-parse", head).strip() if head else "作業木",
        "paths": list(paths),
        "counts": counts,
        "doc_readers": sum(int(r.get("doc_readers", 0)) for r in files),
        "files": files,
    }


def exit_code(report: dict[str, Any]) -> int:
    counts = report["counts"]
    if counts.get("structure", 0) or counts.get("not_python", 0):
        return 2
    if counts.get("strings", 0):
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="文だけの直しの commit を AST で確かめる")
    ap.add_argument("--base", required=True, help="基準の commit")
    ap.add_argument("--head", default=None, help="比べる側の commit(省くと今の作業木)")
    ap.add_argument("--paths", nargs="*", default=["src"], help="比べる道(既定 src)")
    ap.add_argument("--repo", default=".", help="リポの根(既定=今の場所)")
    ap.add_argument("--out", default=None, help="記録の JSON の置き場")
    ap.add_argument("--show", action="store_true", help="変わった文字列の中身も出す")
    ns = ap.parse_args(argv)
    try:
        report = check(Path(ns.repo), ns.base, ns.head, ns.paths, show=ns.show)
    except RuntimeError as e:
        print(f"[astsame] 誤り: {e}", file=sys.stderr)
        return 2
    if ns.out:
        out = Path(ns.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    c = report["counts"]
    print(
        f"[astsame] 変わったファイル {len(report['files'])} 本: same {c.get('same', 0)}・"
        f"strings {c.get('strings', 0)}・structure {c.get('structure', 0)}・py でない {c.get('not_python', 0)}"
        f"(__doc__ を読む所 {report['doc_readers']})"
    )
    for row in report["files"]:
        if row["verdict"] != "same":
            extra = f" 文字列 {row.get('n_changed_strings', 0)} か所" if row["verdict"] == "strings" else ""
            print(f"  {row['verdict']:<10} {row['path']}{extra} {row.get('note', '')}".rstrip())
    return exit_code(report)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
