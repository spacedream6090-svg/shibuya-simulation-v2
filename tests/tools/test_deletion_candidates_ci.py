# -*- coding: utf-8 -*-
"""tools/instruments/deletion_candidates_ci.py の試験(11-16 §1-3 の 5=削除候補を CI の出力に出す・落とさない)。"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from shibuya.world.ledger.constitution import DeletionCandidate

ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "_deletion_candidates_ci_under_test", ROOT / "tools" / "instruments" / "deletion_candidates_ci.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


D = _load()

FAKE = (
    DeletionCandidate("detail", "b_detail", "届き先が全部消えた", ("D1′", "K9")),
    DeletionCandidate("process", "a_process", "宣言が無い", ()),
)


def test_runs_on_the_real_registry_and_exits_zero(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    out = tmp_path / "runs" / "deletion_candidates.json"
    assert D.main(["--out", str(out)]) == 0
    text = capsys.readouterr().out
    data = json.loads(out.read_text(encoding="utf-8"))
    assert text.splitlines()[0] == f"削除候補 {len(data['rows'])} 件(D-R2-4・落とす条件ではない)"
    assert len(data["rows"]) == len(D.collect())


def test_candidates_do_not_fail_ci_and_names_are_printed(tmp_path: Path, capsys, monkeypatch):
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    out = tmp_path / "runs" / "deletion_candidates.json"
    assert D.main(["--out", str(out)], collect_fn=lambda: FAKE) == 0  # 候補が在っても 0
    text = capsys.readouterr().out
    assert "削除候補 2 件" in text
    assert "process a_process: 宣言が無い(消えた届き先: なし)" in text
    assert "detail b_detail: 届き先が全部消えた(消えた届き先: D1′・K9)" in text
    assert "| detail | b_detail |" in summary.read_text(encoding="utf-8")
    rows = json.loads(out.read_text(encoding="utf-8"))["rows"]
    assert [r["subject_id"] for r in rows] == ["a_process", "b_detail"]  # (名前, 理由) の昇順


def test_same_rows_are_not_added_twice(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    out = tmp_path / "runs" / "deletion_candidates.json"
    assert D.main(["--out", str(out)], collect_fn=lambda: FAKE) == 0
    assert D.main(["--out", str(out)], collect_fn=lambda: FAKE) == 0
    assert len(json.loads(out.read_text(encoding="utf-8"))["rows"]) == 2


def test_docs_path_is_refused(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    out = tmp_path / "docs" / "deletion_candidates.json"
    assert D.main(["--out", str(out)], collect_fn=lambda: FAKE) == 2  # docs/ の下には書かない
    assert not out.exists()
