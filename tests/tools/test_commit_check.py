# -*- coding: utf-8 -*-
"""tools/commit_check.py(第330): 一覧の改行の正規化とステージとの突き合わせ。git を使わない部分だけを試す。"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_P = Path(__file__).resolve().parents[2] / "tools" / "commit_check.py"


@pytest.fixture(scope="module")
def cc():
    spec = importlib.util.spec_from_file_location("commit_check", _P)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


def test_normalize_handles_crlf_bom_blank_and_comment(cc):
    text = "\ufeffsrc/a.py\r\ndocs/b.md\r\n\r\n# 注\n tests/c.py \ntools\\d.py"
    assert cc.normalize_lines(text) == ["src/a.py", "docs/b.md", "tests/c.py", "tools/d.py"]


def test_compare_reports_missing_extra_and_dup(cc):
    missing, extra, dup = cc.compare(["a", "b", "b"], {"a", "c"})
    assert missing == ["b"]
    assert extra == ["c"]
    assert dup == ["b"]


def test_compare_ok_when_sets_match_regardless_of_order(cc):
    assert cc.compare(["b", "a"], {"a", "b"}) == ([], [], [])


def test_bad_path_pattern_hits_absolute_paths_but_not_repo_paths(cc):
    bs = chr(92)
    # 文字列は部品からつなぐ(本ファイル自体が道筋の検査に当たらないように)
    assert cc._BAD_PATH.search("/".join(["C:", "Users", "someone", "Desktop", "repo", "x.md"]))
    assert cc._BAD_PATH.search(bs.join(["C:", "Users", "someone", "Desktop", "x"]))
    assert cc._BAD_PATH.search("/".join(["", "home", "someone", "x"]))
    assert not cc._BAD_PATH.search("src/shibuya/engine/run.py")
    assert not cc._BAD_PATH.search("docs/bench/analysis/x/README.md")


def test_read_expect_from_crlf_file(cc, tmp_path: Path):
    f = tmp_path / "expect.txt"
    f.write_bytes(b"src/a.py\r\nsrc/b.py\r\n")  # 第329 の事故の形(CRLF)
    assert cc.read_expect(f) == ["src/a.py", "src/b.py"]
