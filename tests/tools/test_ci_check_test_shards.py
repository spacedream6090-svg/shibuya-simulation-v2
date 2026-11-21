# -*- coding: utf-8 -*-
"""tools/ci/check_test_shards.py(ci-1 の組の表の検査・第348・返事その 9 §1 の 31)の試験。

- 本物のリポ: tests/ の直下(名だけ)が、ちょうど 1 つの組に入っていて、ci.yml の matrix が表と同じ=0。組の道筋は tests/ の下。
- 偽の木: 揃っている=0。新しいディレクトリを組に入れ忘れた・2 つの組にある・消えた名が残る・空の組・試験の外のディレクトリに
  試験のファイル・matrix の食い違い・``python_files`` を変えた型のファイル=1(どれも名が出る)。知らない組の道筋=2。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("_check_test_shards_under_test",
                                                  ROOT / "tools" / "ci" / "check_test_shards.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


S = _load()

CI = """name: ci
jobs:
  ci-1:
    name: ci-1 組 ${{{{ matrix.group }}}}
    strategy:
      fail-fast: false
      matrix:
        group: {groups}
    steps: []
"""


def _tree(tmp_path: Path, *, groups=None, not_tests=None, matrix=None, pyproject: str = "") -> Path:
    root = tmp_path / "repo"
    t = root / "tests"
    for d in ("a", "b", "fixtures", "__pycache__", ".hidden"):
        (t / d).mkdir(parents=True, exist_ok=True)
    (t / "fixtures" / "data.csv").write_text("x", encoding="utf-8")
    for f in ("test_x.py", "conftest.py", "helper.py", "__init__.py"):
        (t / f).write_text("", encoding="utf-8")
    groups = {"g1": ["a"], "g2": ["b", "test_x.py"]} if groups is None else groups
    table = {"groups": {g: {"about": "", "entries": e} for g, e in groups.items()},
             "not_tests": {"fixtures": "データ"} if not_tests is None else not_tests}
    (root / "tools" / "ci").mkdir(parents=True)
    (root / "tools" / "ci" / "test_shards.json").write_text(json.dumps(table, ensure_ascii=False), encoding="utf-8")
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "ci.yml").write_text(
        CI.format(groups=json.dumps(list(groups) if matrix is None else matrix)), encoding="utf-8")
    if pyproject:
        (root / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    return root


def _check(root: Path, capsys) -> tuple[int, str]:
    code = S.main(["--root", str(root), "check"])
    return code, capsys.readouterr().out


# ================================================================== 本物のリポ
def test_real_repo_is_complete(capsys):
    code = S.main(["check"])
    out = capsys.readouterr().out
    assert code == 0, out
    assert "→ 揃っている" in out


def test_real_groups_cover_tests_and_paths_are_under_tests(capsys):
    table = S.load_table(ROOT / S.TABLE_REL)
    assert list(table["groups"]) == S.ci_matrix(ROOT / S.CI_YML_REL) == ["g1", "g2", "g3"]
    for g in table["groups"]:
        paths = S.group_paths(table, g)
        assert paths and all(p.startswith("tests/") for p in paths)
        assert S.main(["paths", "--group", g]) == 0
        assert capsys.readouterr().out.split() == paths
    assert S.group_paths(table, "g1") == ["tests/engine"]


# ================================================================== 偽の木
def test_fake_complete_is_0(tmp_path: Path, capsys):
    code, out = _check(_tree(tmp_path), capsys)
    assert code == 0, out
    assert "tests/ の直下 4 個" in out  # a・b・fixtures・test_x.py(helper.py・conftest.py・__pycache__・.hidden は数えない)


def test_new_directory_left_out_is_1(tmp_path: Path, capsys):
    root = _tree(tmp_path)
    (root / "tests" / "newdir").mkdir()
    code, out = _check(root, capsys)
    assert code == 1, out
    assert "tests/newdir がどの組にも無い" in out


def test_new_root_test_file_left_out_is_1(tmp_path: Path, capsys):
    root = _tree(tmp_path)
    (root / "tests" / "test_new.py").write_text("", encoding="utf-8")
    code, out = _check(root, capsys)
    assert code == 1 and "tests/test_new.py がどの組にも無い" in out, out


def test_entry_in_two_groups_is_1(tmp_path: Path, capsys):
    code, out = _check(_tree(tmp_path, groups={"g1": ["a", "b"], "g2": ["b", "test_x.py"]}), capsys)
    assert code == 1 and "tests/b が 2 つ以上の組にある: ['g1', 'g2']" in out, out


def test_stale_entry_and_empty_group_are_1(tmp_path: Path, capsys):
    code, out = _check(_tree(tmp_path, groups={"g1": ["a", "gone"], "g2": ["b", "test_x.py"], "g3": []}), capsys)
    assert code == 1, out
    assert "の gone が tests/ の直下に無い" in out and "組 g3 が空" in out


def test_test_file_inside_not_tests_is_1(tmp_path: Path, capsys):
    root = _tree(tmp_path)
    (root / "tests" / "fixtures" / "deep").mkdir()
    (root / "tests" / "fixtures" / "deep" / "test_hidden.py").write_text("", encoding="utf-8")
    code, out = _check(root, capsys)
    assert code == 1 and "fixtures/deep/test_hidden.py" in out, out


def test_matrix_mismatch_is_1(tmp_path: Path, capsys):
    code, out = _check(_tree(tmp_path, matrix=["g1"]), capsys)
    assert code == 1 and "matrix の組 ['g1'] が表の組 ['g1', 'g2'] と違う" in out, out


def test_python_files_of_pyproject_are_used(tmp_path: Path, capsys):
    root = _tree(tmp_path, pyproject='[tool.pytest.ini_options]\npython_files = "check_*.py test_*.py"\n')
    (root / "tests" / "check_more.py").write_text("", encoding="utf-8")
    code, out = _check(root, capsys)
    assert code == 1 and "tests/check_more.py がどの組にも無い" in out, out


def test_paths_of_unknown_group_is_2(tmp_path: Path, capsys):
    root = _tree(tmp_path)
    assert S.main(["--root", str(root), "paths", "--group", "g2"]) == 0
    assert capsys.readouterr().out.strip() == "tests/b tests/test_x.py"
    assert S.main(["--root", str(root), "paths", "--group", "g9"]) == 2


def test_names_with_spaces_are_refused(tmp_path: Path, capsys):
    code, _ = _check(_tree(tmp_path, groups={"g1": ["a b"], "g2": ["b", "test_x.py"]}), capsys)
    assert code == 2
