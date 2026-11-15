# -*- coding: utf-8 -*-
"""tools/bytecheck/astsame.py の試験(11-16 §1-12 の 2=文だけの直しの commit を AST で確かめる)。"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("_astsame_under_test", ROOT / "tools" / "bytecheck" / "astsame.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


A = _load()

OLD = '''"""古い説明。"""
import os

LIMIT = 3  # 古い注


def f(x):
    """古い docstring。"""
    if x > LIMIT:
        raise ValueError("大きすぎる")
    return os.sep


class K:
    """クラスの説明。"""
'''


def test_docstring_and_comment_only_is_same():
    new = OLD.replace("古い説明", "新しい説明").replace("古い注", "新しい注").replace("古い docstring", "新しい文")
    new = new.replace("クラスの説明", "直したクラスの説明")
    r = A.compare_sources(OLD, new)
    assert r["verdict"] == "same"


def test_changed_message_string_is_strings():
    new = OLD.replace("大きすぎる", "上限を超えた")
    r = A.compare_sources(OLD, new)
    assert r["verdict"] == "strings"
    assert len(r["changed_strings"]) == 1
    assert r["changed_strings"][0]["len_old"] == len("大きすぎる")


def test_changed_number_is_structure():
    r = A.compare_sources(OLD, OLD.replace("LIMIT = 3", "LIMIT = 4"))
    assert r["verdict"] == "structure"


def test_added_statement_is_structure():
    r = A.compare_sources(OLD, OLD + "\nEXTRA = 1\n")
    assert r["verdict"] == "structure"


def test_removed_docstring_is_same():
    # docstring を消しただけなら、本体に pass が要る形でも同じとみなす(クラスの本体が docstring だけの場合)
    new = OLD.replace('    """クラスの説明。"""\n', "    pass\n")
    assert A.compare_sources(OLD, new)["verdict"] == "same"


def test_string_that_is_not_a_docstring_counts():
    # 関数の途中に置いた文字列の式は docstring ではない
    old = "def g():\n    x = 1\n    'メモ'\n    return x\n"
    new = "def g():\n    x = 1\n    '別のメモ'\n    return x\n"
    assert A.compare_sources(old, new)["verdict"] == "strings"


def test_doc_readers_are_counted():
    src = '"""説明。"""\nTEXT = __doc__\n'
    r = A.compare_sources(src, src.replace("説明", "別の説明"))
    assert r["verdict"] == "same"
    assert r["doc_readers"] == 1


def test_syntax_error_is_structure():
    assert A.compare_sources("x = 1\n", "x = (\n")["verdict"] == "structure"


def test_exit_code_order():
    assert A.exit_code({"counts": {"same": 3}}) == 0
    assert A.exit_code({"counts": {"same": 3, "strings": 1}}) == 1
    assert A.exit_code({"counts": {"strings": 1, "structure": 1}}) == 2
    assert A.exit_code({"counts": {"not_python": 1}}) == 2


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_check_over_a_small_git_repo(tmp_path: Path):
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git が無い")
    repo = tmp_path / "r"
    (repo / "src").mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "core.autocrlf", "false")
    (repo / "src" / "a.py").write_text(OLD, encoding="utf-8", newline="\n")
    (repo / "src" / "b.py").write_text("X = 1\n", encoding="utf-8", newline="\n")
    (repo / "src" / "c.py").write_text("Y = 1\n", encoding="utf-8", newline="\n")
    _git(repo, "add", "src/a.py", "src/b.py", "src/c.py")
    _git(repo, "commit", "-q", "-m", "base")
    (repo / "src" / "a.py").write_text(OLD.replace("古い説明", "新しい説明"), encoding="utf-8", newline="\n")
    (repo / "src" / "b.py").write_text("X = 2\n", encoding="utf-8", newline="\n")
    (repo / "src" / "d.py").write_text("Z = 1\n", encoding="utf-8", newline="\n")
    report = A.check(repo, "HEAD", None, ["src"])
    by = {r["path"]: r for r in report["files"]}
    assert by["src/a.py"]["verdict"] == "same"
    assert by["src/b.py"]["verdict"] == "structure"
    assert by["src/d.py"]["verdict"] == "structure" and by["src/d.py"]["status"] == "A"
    assert "src/c.py" not in by
    assert A.exit_code(report) == 2
    # 文だけの直しだけなら 0
    (repo / "src" / "b.py").write_text("X = 1\n", encoding="utf-8", newline="\n")
    (repo / "src" / "d.py").unlink()
    report = A.check(repo, "HEAD", None, ["src"])
    assert A.exit_code(report) == 0 and report["counts"] == {"same": 1}


def test_strings_are_hidden_unless_show(tmp_path: Path):
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git が無い")
    repo = tmp_path / "r"
    (repo / "src").mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "core.autocrlf", "false")
    (repo / "src" / "a.py").write_text(OLD, encoding="utf-8", newline="\n")
    _git(repo, "add", "src/a.py")
    _git(repo, "commit", "-q", "-m", "base")
    (repo / "src" / "a.py").write_text(OLD.replace("大きすぎる", "上限を超えた"), encoding="utf-8", newline="\n")
    hidden = A.check(repo, "HEAD", None, ["src"])
    row = hidden["files"][0]
    assert row["verdict"] == "strings" and row["n_changed_strings"] == 1
    assert "old" not in row["changed_strings"][0] and "new" not in row["changed_strings"][0]
    shown = A.check(repo, "HEAD", None, ["src"], show=True)
    assert shown["files"][0]["changed_strings"][0]["new"] == "上限を超えた"
