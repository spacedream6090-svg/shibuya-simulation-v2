"""削除候補台帳ファイル(``runs/`` へ冪等追記)の検査。"""

from __future__ import annotations

import json

import pytest

from shibuya.world.processes.constitution import DeletionCandidate
from shibuya.world.processes.deletion_candidates import (
    DEFAULT_LEDGER_PATH,
    append_candidates,
    load_candidates,
    write_candidates,
)


def _c(sid="a", reason="消えた", targets=("D1′",), when=""):
    return DeletionCandidate("world_process", sid, reason, tuple(targets), when)


def test_default_path_is_under_runs():
    assert DEFAULT_LEDGER_PATH.parts[0] == "runs"
    assert "docs" not in DEFAULT_LEDGER_PATH.parts


def test_docs_path_is_refused(tmp_path):
    bad = tmp_path / "docs" / "x.json"
    with pytest.raises(ValueError, match="docs"):
        append_candidates(bad, [_c()])


def test_load_missing_file_is_empty(tmp_path):
    assert load_candidates(tmp_path / "none.json") == ()


def test_append_creates_and_reloads(tmp_path):
    p = tmp_path / "runs" / "deletion_candidates.json"
    rows = append_candidates(p, [_c("a"), _c("b")])
    assert [r.subject_id for r in rows] == ["a", "b"]
    assert p.is_file()
    assert load_candidates(p) == rows


def test_append_is_idempotent(tmp_path):
    p = tmp_path / "d.json"
    append_candidates(p, [_c("a")])
    again = append_candidates(p, [_c("a")])
    assert len(again) == 1
    third = append_candidates(p, [_c("a"), _c("a", reason="別の理由")])
    assert len(third) == 2  # 同じ id でも理由が違えば別行


def test_first_seen_is_preserved(tmp_path):
    p = tmp_path / "d.json"
    append_candidates(p, [_c("a", when="2026-09-08")])
    rows = append_candidates(p, [_c("a", when="2026-12-31")])
    assert rows[0].detected_at == "2026-09-08"


def test_vanished_targets_are_merged(tmp_path):
    p = tmp_path / "d.json"
    append_candidates(p, [_c("a", targets=("D1′",))])
    rows = append_candidates(p, [_c("a", targets=("D4′",))])
    assert rows[0].vanished_targets == ("D1′", "D4′")


def test_file_is_deterministic_and_sorted(tmp_path):
    p1, p2 = tmp_path / "a.json", tmp_path / "b.json"
    write_candidates(p1, [_c("z"), _c("a"), _c("m")])
    write_candidates(p2, [_c("m"), _c("z"), _c("a")])
    assert p1.read_text(encoding="utf-8") == p2.read_text(encoding="utf-8")
    payload = json.loads(p1.read_text(encoding="utf-8"))
    assert [r["subject_id"] for r in payload["rows"]] == ["a", "m", "z"]
    assert payload["version"] == 1


def test_broken_file_raises(tmp_path):
    p = tmp_path / "d.json"
    p.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="rows"):
        load_candidates(p)
