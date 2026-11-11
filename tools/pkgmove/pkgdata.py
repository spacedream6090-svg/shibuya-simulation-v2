# -*- coding: utf-8 -*-
"""pyproject の ``[tool.setuptools.package-data]`` の鍵(親の裁定 2026-11-11・判断 2=許可の一覧の (f))。

- 書き換えてよいのは、この段で無くなる包みの名の鍵だけ。鍵の包みの頭(``__init__.py``)が書き換えた後の木に無く、その glob に
  当たっていたファイルが全部、同じ形の道(包みの道からの相対が同じ)で 1 つの新しい包みへ移ったとき、鍵をその包みの名にする
  (glob はそのまま)。行き先が 1 つに決まらなければ書き換えない=守りが止める。
- 守り: 鍵は全部、木に在る包み(頭が在る)で、glob は 1 本以上のファイルに当たる。
- pyproject のほかの行(``filterwarnings`` ほか)は触らない。
"""
from __future__ import annotations

import fnmatch
import re
import tomllib

from pkgmove.model import SRC_PREFIX, Tree, mod_of

SECTION = "[tool.setuptools.package-data]"


def entries(text: str) -> dict[str, list[str]]:
    return dict(tomllib.loads(text).get("tool", {}).get("setuptools", {}).get("package-data", {}))


def _pkg_dir(key: str) -> str:
    return SRC_PREFIX + "/".join(key.split(".")[1:]) if key != "shibuya" else SRC_PREFIX.rstrip("/")


def _matched(tree: Tree, key: str, globs: list[str]) -> list[str]:
    d = _pkg_dir(key) + "/"
    return sorted(p for p in [*tree.files, *tree.blobs] if p.startswith(d)
                  and any(fnmatch.fnmatch(p[len(d):], g) for g in globs))


def check(text: str, tree: Tree) -> list[str]:
    """鍵は全部、木に在る包みで、glob が 1 本以上に当たる。"""
    errs: list[str] = []
    for key, globs in entries(text).items():
        if not key.startswith("shibuya"):
            continue
        if _pkg_dir(key) + "/__init__.py" not in tree.files:
            errs.append(f"package-data の鍵の包みが木に無い: {key}")
        elif not _matched(tree, key, list(globs)):
            errs.append(f"package-data の glob がどのファイルにも当たらない: {key} {list(globs)}")
    return errs


def rewrite(text: str, before: Tree, after: Tree, file_moves: dict[str, str]) -> tuple[str, list[tuple[str, str]], list[str]]:
    """(書き換えた文, 書き換えた鍵 (古い, 新しい), 注意)。書き換えるのは、この段で無くなる包みの鍵だけ。"""
    changes: list[tuple[str, str]] = []
    warns: list[str] = []
    out = text
    for key, globs in entries(text).items():
        if not key.startswith("shibuya") or _pkg_dir(key) + "/__init__.py" in after.files:
            continue
        if _pkg_dir(key) + "/__init__.py" not in before.files:
            continue  # 前から無い=守りが止める
        d = _pkg_dir(key) + "/"
        bases: set[str] = set()
        ok = True
        for p in _matched(before, key, list(globs)):
            n = file_moves.get(p)
            r = p[len(d):]
            if n is None or not n.endswith("/" + r):
                ok = False
                break
            bases.add(n[: -len(r) - 1])
        if not ok or len(bases) != 1:
            warns.append(f"package-data の鍵 {key}: 行き先が 1 つに決まらない=書き換えない")
            continue
        new_key = mod_of(bases.pop()[len(SRC_PREFIX):] + "/__init__.py")
        new_out, n_sub = _replace_key(out, key, new_key)
        if n_sub != 1:
            warns.append(f"package-data の鍵 {key}: 字面が 1 か所に決まらない=書き換えない")
            continue
        out = new_out
        changes.append((key, new_key))
    return out, changes, warns


def _replace_key(text: str, key: str, new_key: str) -> tuple[str, int]:
    """``[tool.setuptools.package-data]`` の節の中の ``"<key>" =`` の行の鍵だけを置き換える。"""
    lines = text.splitlines(keepends=True)
    try:
        k = next(i for i, x in enumerate(lines) if x.strip() == SECTION)
    except StopIteration:
        return text, 0
    n = 0
    pat = re.compile(r'^(\s*)"' + re.escape(key) + r'"(\s*=)')
    for i in range(k + 1, len(lines)):
        if lines[i].lstrip().startswith("["):
            break
        m = pat.match(lines[i])
        if m:
            lines[i] = pat.sub(lambda mm: f'{mm.group(1)}"{new_key}"{mm.group(2)}', lines[i], count=1)
            n += 1
    return "".join(lines), n
