"""2-3c の活性化の道具(``docs/bench/analysis/wallbounce-1012/tt23c/tools/activate_tt23c.py``)を合成の置き場で回す。

本段では本体の ``data/world/v2`` に apply しない(活性化は版上げ 3 回目=4-3)。ここでは合成の「本体」と「組んだ資産」で
plan → apply --dry-run(何も書かない)→ apply → verify → materialize → revert の道が sha256 と build_hash で閉じることと、
前提が違えば止まることを確かめる(data 不要)。
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "docs" / "bench" / "analysis" / "wallbounce-1012" / "tt23c" / "tools" / "activate_tt23c.py"


def _tool():
    spec = importlib.util.spec_from_file_location("activate_tt23c", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _write(root: Path, files: dict[str, bytes], build_hash: str) -> None:
    (root / "acceptance").mkdir(parents=True, exist_ok=True)
    for rel, b in files.items():
        (root / rel).write_bytes(b)
    (root / "build_manifest.json").write_text(json.dumps({"build_hash": build_hash}), encoding="utf-8")


def _snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_plan_apply_verify_materialize_revert(tmp_path):
    t = _tool()
    live, stage = tmp_path / "live", tmp_path / "stage"
    common = {"w12_timetables.parquet": b"same", "w12_external_nodes.parquet": b"nodes",
              "acceptance/summary.json": b"{}", "w17_prompts_x.jsonl": b"skip"}
    _write(live, {**common, "W12.header.json": b'{"v": "1.2.0"}'}, "a" * 64)
    _write(stage, {**common, "W12.header.json": b'{"v": "1.3.0"}', "w12_rail_events.parquet": b"events"}, "b" * 64)
    plan_p = tmp_path / "plan.json"
    assert t.main(["plan", "--live", str(live), "--stage", str(stage), "--plan", str(plan_p)]) == 0
    plan = json.loads(plan_p.read_text(encoding="utf-8"))
    assert plan["counts"] == {"same": 3, "moved": 2, "added": 1, "kept_live_only": 0}  # header・manifest・events
    assert {r["path"] for r in plan["rows"] if r["action"] == "added"} == {"w12_rail_events.parquet"}
    assert not any("w17_prompts" in r["path"] for r in plan["rows"])  # W17 の jsonl は比べない
    before = _snapshot(live)
    backup = tmp_path / "pre"
    args = ["--live", str(live), "--stage", str(stage), "--plan", str(plan_p), "--backup", str(backup)]
    assert t.main(["apply", *args, "--dry-run"]) == 0
    assert _snapshot(live) == before and not backup.exists()  # --dry-run は何も書かない
    assert t.main(["verify", "--live", str(live), "--plan", str(plan_p), "--want", "before"]) == 0
    assert t.main(["apply", *args]) == 0
    assert t.main(["verify", "--live", str(live), "--plan", str(plan_p), "--want", "after"]) == 0
    assert (live / "w12_rail_events.parquet").read_bytes() == b"events"
    assert t.main(["apply", *args, "--dry-run"]) == 2  # 本体がもう「前」ではない=止まる
    out = tmp_path / "materialized"
    assert t.main(["materialize", "--live", str(live), "--backup", str(backup), "--out", str(out)]) == 0
    assert {k: v for k, v in _snapshot(out).items()} == {k: v for k, v in before.items() if "w17_prompts" not in k}
    assert t.main(["revert", "--live", str(live), "--backup", str(backup)]) == 0
    assert _snapshot(live) == before


def test_apply_stops_when_the_stage_differs_from_the_plan(tmp_path):
    t = _tool()
    live, stage = tmp_path / "live", tmp_path / "stage"
    _write(live, {"W12.header.json": b"old"}, "a" * 64)
    _write(stage, {"W12.header.json": b"new"}, "b" * 64)
    plan_p = tmp_path / "plan.json"
    assert t.main(["plan", "--live", str(live), "--stage", str(stage), "--plan", str(plan_p)]) == 0
    (stage / "W12.header.json").write_bytes(b"changed after plan")
    assert t.main(["apply", "--live", str(live), "--stage", str(stage), "--plan", str(plan_p),
                   "--backup", str(tmp_path / "pre")]) == 2
    assert (live / "W12.header.json").read_bytes() == b"old"
