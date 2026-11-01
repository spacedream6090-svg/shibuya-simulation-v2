"""第 4 期 4-1 段 1〜3 の活性化の道具(``pop41/tools/stage_pop41.py``)を合成の置き場で通す。

本段では本体の v2 に apply しない(親が段 10=4-3 で決める)。ここでは小さな合成の置き場で plan → apply --dry-run(何も
書かない)→ apply → verify(後)→ revert → verify(前)→ materialize が形どおり動くことだけを確かめる。
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "pop41" / "tools" / "stage_pop41.py"


@pytest.fixture(scope="module")
def tool():
    spec = importlib.util.spec_from_file_location("stage_pop41", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _tree(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def _snapshot(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): p.read_text(encoding="utf-8") for p in sorted(root.rglob("*")) if p.is_file()}


def test_plan_apply_verify_revert_materialize(tool, tmp_path):
    live, stage = tmp_path / "v2", tmp_path / "stage"
    base = {"build_manifest.json": json.dumps({"build_hash": "aaa"}), "w16_population.parquet": "w16",
            "w17_prompts.0of7.jsonl": "skip", "acceptance/summary.json": "{}"}
    _tree(live, base)
    _tree(stage, {**{k: v for k, v in base.items() if not k.startswith("w17_prompts")},
                  "w21_persons.parquet": "w21", "w21_manifest.json": "{}"})
    steps, backup = tmp_path / "steps", tmp_path / "pre"
    ns = type("A", (), {})
    a = ns()
    a.live, a.stage, a.steps, a.record, a.dry_run = str(live), str(stage), str(steps), "", False
    assert tool.cmd_plan(a) == 0
    plan = json.loads((steps / "plan.json").read_text(encoding="utf-8"))
    assert plan["counts"] == {"same": 3, "moved": 0, "added": 2, "kept_live_only": 0}
    assert plan["build_hash_before"] == plan["build_hash_after"] == "aaa"  # W21 は build_hash を動かさない
    before = _snapshot(live)
    b = ns()
    b.live, b.steps, b.backup, b.dry_run = str(live), str(steps), str(backup), True
    assert tool.cmd_apply(b) == 0 and _snapshot(live) == before and not backup.exists()  # dry-run は書かない
    v = ns()
    v.live, v.steps, v.want = str(live), str(steps), "before"
    assert tool.cmd_verify(v) == 0
    b.dry_run = False
    assert tool.cmd_apply(b) == 0
    v.want = "after"
    assert tool.cmd_verify(v) == 0 and (live / "w21_persons.parquet").exists()
    m = ns()
    m.live, m.backup, m.out = str(live), str(backup), str(tmp_path / "mat")
    assert tool.cmd_materialize(m) == 0
    assert not (tmp_path / "mat" / "w21_persons.parquet").exists() and (tmp_path / "mat" / "w16_population.parquet").exists()
    r = ns()
    r.live, r.backup, r.dry_run = str(live), str(backup), False
    assert tool.cmd_revert(r) == 0 and _snapshot(live) == before
    v.want = "before"
    assert tool.cmd_verify(v) == 0


def test_apply_refuses_when_live_differs_from_plan(tool, tmp_path):
    live, stage = tmp_path / "v2", tmp_path / "stage"
    _tree(live, {"build_manifest.json": json.dumps({"build_hash": "aaa"}), "a.json": "1"})
    _tree(stage, {"build_manifest.json": json.dumps({"build_hash": "aaa"}), "a.json": "1", "w21_frame.json": "x"})
    ns = type("A", (), {})
    a = ns()
    a.live, a.stage, a.steps, a.record, a.dry_run = str(live), str(stage), str(tmp_path / "steps"), "", False
    tool.cmd_plan(a)
    (live / "w21_frame.json").write_text("other", encoding="utf-8")  # 本体の v2 が plan の前と違う
    b = ns()
    b.live, b.steps, b.backup, b.dry_run = str(live), str(tmp_path / "steps"), str(tmp_path / "pre"), True
    assert tool.cmd_apply(b) == 2
