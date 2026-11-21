"""変えたファイルの範囲から、重い組を回すかを決める道具(tools/ci/changed_scope.py・11-22 §3-2 の 1・5)。"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("changed_scope", REPO / "tools" / "ci" / "changed_scope.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


S = _load()
RT = ("docs/design/rules-table.json", "docs/design/v2-budget-declaration.md")


def test_documents_and_non_documents():
    for p in ("README.md", "CLAUDE.md", "STATUS.md", "docs/ops/report.md", "docs/design/spec/03-mind.md", "./docs/log/devlog.md",
              "docs\\research\\INDEX.md"):
        assert S.is_document(p, RT), p
    for p in ("src/shibuya/x.py", "tests/tools/test_x.py", "tools/ci/x.py", ".github/workflows/ci.yml", "pyproject.toml",
              "docs/bench/analysis/a/record.json", "docs/bench/analysis/a/tool.py", "tools/night5070/README.md",
              ".claude/skills/yomiyasu/SKILL.md", "docs/design/v2-budget-declaration.md", "docs/design/rules-table.json"):
        assert not S.is_document(p, RT), p


def test_classify_docs_only_skips_the_heavy_group():
    r = S.classify(["STATUS.md", "docs/log/devlog.md"], RT)
    assert r["docs_only"] is True and r["heavy"] is False and r["run_affecting"] is False


def test_classify_one_non_document_is_heavy():
    r = S.classify(["docs/log/devlog.md", "tools/ci/x.py"], RT)
    assert r["heavy"] is True and r["docs_only"] is False and r["run_affecting"] is False
    assert r["non_docs"] == ["tools/ci/x.py"]


def test_runtime_docs_are_heavy_and_run_affecting():
    # ランが実行時に開く文書は、Markdown でも「文書だけ」に数えない
    r = S.classify(["docs/design/v2-budget-declaration.md"], RT)
    assert r["heavy"] is True and r["run_affecting"] is True
    r = S.classify(["docs/design/rules-table.json", "README.md"], RT)
    assert r["heavy"] is True and r["run_affecting"] is True


def test_src_and_lock_affect_runs():
    assert S.classify(["src/shibuya/a.py"], RT)["run_affecting"] is True
    assert S.classify(["requirements-lock.txt"], RT)["run_affecting"] is True
    assert S.classify(["pyproject.toml"], RT)["run_affecting"] is True
    r = S.classify(["tests/engine/test_a.py", "tools/bytecheck/cli.py"], RT)
    assert r["heavy"] is True and r["run_affecting"] is False


def test_empty_list_is_unknown_so_heavy():
    r = S.classify([], RT)
    assert r["heavy"] is True and r["docs_only"] is False


def test_runtime_docs_come_from_the_bytecheck_list():
    """一覧の正は tools/bytecheck/tree.py の TRACKED_READS(二重に持たない)。5 本(ユーザーの言う「ランが読む文書」)を含む。"""
    rt = S.runtime_docs()
    assert len(rt) >= 5 and all(p.startswith("docs/") for p in rt)
    for must in ("docs/design/rules-table.json", "docs/design/bridging-ledger.json", "docs/design/v2-budget-declaration.md",
                 "docs/bench/anchors/hunger_energy_build_anchors_v0.json", "docs/bench/anchors/ssb2021_activity_prior_v0.json"):
        assert must in rt
    for p in rt:
        assert not S.is_document(p, rt)


def test_zero_or_missing_base_is_unknown():
    assert S.changed_paths("", "HEAD") is None
    assert S.changed_paths(S.ZERO_SHA, "HEAD") is None


def test_cli_with_git_and_github_output(tmp_path: Path, monkeypatch):
    if shutil.which("git") is None:
        pytest.skip("git が無い")
    repo = tmp_path / "r"
    (repo / "tools" / "bytecheck").mkdir(parents=True)
    (repo / "docs").mkdir()
    (repo / "tools" / "bytecheck" / "tree.py").write_text('TRACKED_READS = {"docs/rt.md": "x"}\n', encoding="utf-8")
    (repo / "docs" / "a.md").write_text("a\n", encoding="utf-8")
    (repo / "docs" / "rt.md").write_text("rt\n", encoding="utf-8")
    (repo / "tools" / "ci").mkdir()
    (repo / "tools" / "ci" / "test_shards.json").write_text(
        '{"groups": {"g1": {"weight": "heavy", "entries": ["engine"]}, "g2": {"entries": ["tools"]}}}', encoding="utf-8")

    def git(*a: str) -> str:
        cp = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *a],
                            capture_output=True, text=True, check=True)
        return cp.stdout.strip()

    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    git("add", ".")
    git("commit", "-q", "-m", "base")
    base = git("rev-parse", "HEAD")
    (repo / "docs" / "a.md").write_text("a2\n", encoding="utf-8")
    git("commit", "-q", "-am", "docs only")
    out = tmp_path / "gh_out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    assert S.main(["--base", base, "--github-output", "--root", str(repo)]) == 0
    assert out.read_text(encoding="utf-8") == "heavy=false\nrun_affecting=false\nskip_groups=g1\n"  # 重い組だけ飛ばす
    # ランが開く文書を変えると重い側
    docs_head = git("rev-parse", "HEAD")
    (repo / "docs" / "rt.md").write_text("rt2\n", encoding="utf-8")
    git("commit", "-q", "-am", "runtime doc")
    out.write_text("", encoding="utf-8")
    assert S.main(["--base", docs_head, "--github-output", "--root", str(repo)]) == 0
    assert out.read_text(encoding="utf-8") == "heavy=true\nrun_affecting=true\nskip_groups=\n"
    # 基準が無い commit(取れない)は重い側
    out.write_text("", encoding="utf-8")
    assert S.main(["--base", "deadbeef" * 5, "--github-output", "--root", str(repo)]) == 0
    assert out.read_text(encoding="utf-8") == "heavy=true\nrun_affecting=true\nskip_groups=\n"
    # GITHUB_OUTPUT が無ければ誤り(黙って通さない)
    monkeypatch.delenv("GITHUB_OUTPUT")
    assert S.main(["--base", base, "--github-output", "--root", str(repo)]) == 2


def test_heavy_groups_of_the_real_table():
    """本物の組の表: 重い組が 1 つ以上あり、軽い組も残る(文書だけの変更でも、文書を読む試験の組は回る)。"""
    import json

    heavy = S.heavy_groups()
    table = json.loads((REPO / S.SHARDS_REL).read_text(encoding="utf-8"))
    assert heavy and set(heavy) < set(table["groups"])
    assert all("engine" in " ".join(table["groups"][g]["entries"]) for g in heavy)
