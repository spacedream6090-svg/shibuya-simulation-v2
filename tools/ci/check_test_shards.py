# -*- coding: utf-8 -*-
"""CI の ci-1 を同時に回す組の表(``tools/ci/test_shards.json``)の検査と、組の道筋の出力(第348・返事その 9 §1 の 31)。

    python tools/ci/check_test_shards.py check            # ci-0 で回す。落ちこぼれる試験があれば 1
    python tools/ci/check_test_shards.py paths --group g1 # ci-1 の組が pytest に渡す道筋(空白区切り)

``check`` が確かめること(どれかに当たれば終了コード 1):

1. ``tests/`` の直下の全部(ディレクトリと、pytest が集める名のファイル)が、ちょうど 1 つの組に入っている
   (どの組にも無い=その試験は CI で回らない・2 つ以上の組にある=2 回回る)。``__pycache__`` と ``.`` で始まる名は数えない。
   試験の外として表の ``not_tests`` に載せたディレクトリは組に入れない(中に試験のファイルの名が在れば 1)。
2. 表の名が ``tests/`` の直下に在る(消えた名が残っていない)。空の組が無い。
3. ``ci.yml`` の ci-1 の matrix の組の名が、表の組の名と同じ並び(表に組を足して matrix に足し忘れると、その組は回らない)。

見るのは ``tests/`` の直下の名だけ(組に入れたディレクトリの中は開かない・歩かない)。pytest が集めるファイルの名の型は
``pyproject.toml`` の ``[tool.pytest.ini_options] python_files``(無ければ pytest の既定 ``test_*.py``・``*_test.py``)。

終了コード: 0=揃っている・1=落ちこぼれ・重なり・食い違いがある・2=誤り(表が読めない・知らない組)。
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
import tomllib
from pathlib import Path
from typing import Any, Final, Sequence

ROOT = Path(__file__).resolve().parents[2]
TABLE_REL: Final[str] = "tools/ci/test_shards.json"
CI_YML_REL: Final[str] = ".github/workflows/ci.yml"
#: 組の重さ。heavy=文書だけの変更では回さない組(engine)。light=いつも回す組
WEIGHTS: Final[tuple[str, ...]] = ("heavy", "light")
#: ci.yml の中で組を回す仕事の名と、matrix の鍵。
CI_JOB: Final[str] = "ci-1"
MATRIX_KEY: Final[str] = "group"
#: pytest の既定の ``python_files``。
DEFAULT_PYTHON_FILES: Final[tuple[str, ...]] = ("test_*.py", "*_test.py")

EXIT_OK, EXIT_BAD, EXIT_ERROR = 0, 1, 2


def python_files(root: Path) -> tuple[str, ...]:
    """pytest が集めるファイルの名の型(``pyproject.toml`` の ``python_files``・無ければ既定)。"""
    p = root / "pyproject.toml"
    if not p.is_file():
        return DEFAULT_PYTHON_FILES
    ini = tomllib.loads(p.read_text(encoding="utf-8")).get("tool", {}).get("pytest", {}).get("ini_options", {})
    v = ini.get("python_files")
    if v is None:
        return DEFAULT_PYTHON_FILES
    return tuple(v.split()) if isinstance(v, str) else tuple(str(x) for x in v)


def is_test_file(name: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def top_entries(tests_dir: Path, patterns: Sequence[str]) -> list[str]:
    """``tests/`` の直下のディレクトリと試験のファイルの名(中には入らない)。"""
    out: list[str] = []
    with os.scandir(tests_dir) as it:
        for e in it:
            if e.name.startswith(".") or e.name == "__pycache__":
                continue
            if e.is_dir(follow_symlinks=False) or (e.is_file() and is_test_file(e.name, patterns)):
                out.append(e.name)
    return sorted(out)


def load_table(path: Path) -> dict[str, Any]:
    """組の表を読む(形が違えば ``ValueError``)。"""
    doc = json.loads(path.read_text(encoding="utf-8"))
    groups = doc.get("groups")
    if not isinstance(groups, dict) or not groups:
        raise ValueError("groups が無いか空")
    for g, body in groups.items():
        entries = body.get("entries") if isinstance(body, dict) else None
        if not isinstance(entries, list) or not all(isinstance(x, str) for x in entries):
            raise ValueError(f"組 {g} の entries が文字列の list でない")
        for x in [g, *entries]:
            if not x or any(c.isspace() for c in x) or "/" in x or "\\" in x:
                raise ValueError(f"名に空白か区切りの字がある: {x!r}")
        # 〔第349・11-22 §3-2 の 1〕重い組(文書だけの変更では回さない)の印。無ければ軽い組
        if body.get("weight", "light") not in WEIGHTS:
            raise ValueError(f"組 {g} の weight が {WEIGHTS} のどれでもない: {body.get('weight')!r}")
    if all(b.get("weight", "light") == "heavy" for b in groups.values()):
        raise ValueError("全部の組が heavy(文書だけの変更で、試験が 1 本も回らなくなる)")
    not_tests = doc.get("not_tests", {})
    if not isinstance(not_tests, dict):
        raise ValueError("not_tests が辞書でない")
    return doc


def heavy_groups(table: dict[str, Any]) -> list[str]:
    """重い組の名(表の並び)。文書だけの変更では回さない(``tools/ci/changed_scope.py`` が使う)。"""
    return [g for g, b in table["groups"].items() if b.get("weight", "light") == "heavy"]


def ci_matrix(ci_yml: Path) -> list[str]:
    """ci.yml の ci-1 の matrix の組の名(無ければ ``ValueError``)。"""
    import yaml  # ロックに入っている(PyYAML)

    doc = yaml.safe_load(ci_yml.read_text(encoding="utf-8"))
    try:
        got = doc["jobs"][CI_JOB]["strategy"]["matrix"][MATRIX_KEY]
    except (KeyError, TypeError):
        raise ValueError(f"{CI_YML_REL} の jobs.{CI_JOB}.strategy.matrix.{MATRIX_KEY} が無い") from None
    return [str(x) for x in got]


def problems(table: dict[str, Any], entries: Sequence[str], *, tests_dir: Path, patterns: Sequence[str],
             matrix: Sequence[str] | None) -> list[str]:
    """揃っていない所の文(空なら揃っている)。"""
    out: list[str] = []
    groups: dict[str, list[str]] = {g: list(b["entries"]) for g, b in table["groups"].items()}
    not_tests: dict[str, str] = dict(table.get("not_tests", {}))
    where: dict[str, list[str]] = {}
    for g, names in groups.items():
        if not names:
            out.append(f"組 {g} が空(空の組は pytest に道筋を渡さない=全部を回してしまう)")
        for n in names:
            where.setdefault(n, []).append(g)
    present = set(entries)
    for n in entries:
        if n in not_tests:
            continue
        gs = where.get(n, [])
        if not gs:
            out.append(f"tests/{n} がどの組にも無い(CI で回らない)。{TABLE_REL} のどれかの組に足す")
        elif len(gs) > 1:
            out.append(f"tests/{n} が 2 つ以上の組にある: {gs}")
    for n, gs in sorted(where.items()):
        if n not in present:
            out.append(f"組 {gs} の {n} が tests/ の直下に無い(消えた名が残っている)")
        if n in not_tests:
            out.append(f"{n} が組 {gs} と not_tests の両方にある")
    for n in sorted(not_tests):
        d = tests_dir / n
        if n not in present or not d.is_dir():
            out.append(f"not_tests の {n} が tests/ の直下のディレクトリでない")
            continue
        found = sorted(os.path.relpath(os.path.join(dp, f), tests_dir).replace("\\", "/")
                       for dp, _dirs, files in os.walk(d) for f in files if is_test_file(f, patterns))
        if found:
            out.append(f"not_tests の {n} に試験のファイルがある(組に入れる): {found[:5]}")
    if matrix is not None and list(matrix) != list(groups):
        out.append(f"{CI_YML_REL} の {CI_JOB} の matrix の組 {list(matrix)} が表の組 {list(groups)} と違う")
    return out


def group_paths(table: dict[str, Any], group: str) -> list[str]:
    """組の pytest に渡す道筋(``tests/<名>``・表の並び)。知らない組・空の組は ``KeyError``。"""
    groups = table["groups"]
    if group not in groups or not groups[group]["entries"]:
        raise KeyError(f"知らない組か空の組: {group!r}(組は {list(groups)})")
    return [f"tests/{n}" for n in groups[group]["entries"]]


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=Path, default=ROOT, help="リポの根(既定はこのファイルから 2 つ上・試験の口)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="tests/ の直下が、ちょうど 1 つの組に入っているかを確かめる")
    sp = sub.add_parser("paths", help="組の道筋を空白区切りで出す")
    sp.add_argument("--group", required=True)
    a = ap.parse_args(argv)
    root = a.root.resolve()
    try:
        table = load_table(root / TABLE_REL)
        if a.cmd == "paths":
            print(" ".join(group_paths(table, a.group)))
            return EXIT_OK
        patterns = python_files(root)
        tests_dir = root / "tests"
        entries = top_entries(tests_dir, patterns)
        matrix = ci_matrix(root / CI_YML_REL)
    except (OSError, ValueError, KeyError) as e:
        print(f"誤り: {e}", file=sys.stderr)
        return EXIT_ERROR
    bad = problems(table, entries, tests_dir=tests_dir, patterns=patterns, matrix=matrix)
    sizes = "・".join(f"{g} {len(b['entries'])}" for g, b in table["groups"].items())
    print(f"tests/ の直下 {len(entries)} 個(試験の外 {len(table.get('not_tests', {}))} 個)・組 {sizes}"
          f" → {'揃っていない' if bad else '揃っている'}")
    for line in bad:
        print(f"  {line}")
    return EXIT_BAD if bad else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
