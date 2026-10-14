"""〔第 2 期 2-4 V1〕版上げ 2 回目の世界資産の活性化(2-3b の W12 1.2.0 実ダイヤ+2-3 の W9 の影 7 日の窓)。

本体の ``data/world/v2`` に ``docs/bench/analysis/wallbounce-1012/vb24/tools/activate_vb24.py apply`` で写した後の資産を見る
(写す前の作業木・本体では落ちる=10e ACT と同じ。記録 ``docs/bench/analysis/wallbounce-1012/vb24/README.md`` の V1)。

〔2-4 検収 M1〕退避 ``data/world/v2_pre_2-4`` は置き換えた 11 本と ``MANIFEST.sha256``・``plan.json`` だけ=前の資産そのもの
ではない。道具の ``materialize`` は作業用の置き場に前の資産を組み、plan の「前」と同じかを確かめる。その試験は合成の
置き場(tmp dir)で回す=世界の資産は要らない(``requires_data`` の印は本物の資産を見る 3 本だけ)。
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from shibuya.build.vis import w9_shadow as W9
from shibuya.engine.processes import environment as ENV
from shibuya.world.assets import SHADOW_GLOB

REPO_ROOT = Path(__file__).resolve().parents[2]
WORLD = REPO_ROOT / "data" / "world" / "v2"
RECORD = REPO_ROOT / "docs" / "bench" / "analysis" / "wallbounce-1012" / "vb24" / "v1_activation_plan.json"
TOOL = REPO_ROOT / "docs" / "bench" / "analysis" / "wallbounce-1012" / "vb24" / "tools" / "activate_vb24.py"

#: 本物の資産(活性化した本体の v2)を見る試験の印。〔2-4 検収 M1〕前はモジュール全体に付けていた。
_needs_world = pytest.mark.requires_data("world_v2:build_manifest.json")


def _manifest() -> dict:
    return json.loads((WORLD / "build_manifest.json").read_text(encoding="utf-8"))


@_needs_world
def test_v1_build_hash_is_the_activated_one():
    plan = json.loads(RECORD.read_text(encoding="utf-8"))
    assert _manifest()["build_hash"] == plan["build_hash_after"]


@_needs_world
def test_v1_w12_is_the_real_timetable_version_and_w9_has_the_window():
    stages = {s["stage"]: s for s in _manifest()["stages"]}
    assert stages["W12"]["stage_version"] == "1.2.0"
    assert stages["W12"]["notes"]["equal_interval_lines_remaining"] == []
    assert stages["W9"]["params"]["shadow_dates"] == list(W9.SHADOW_DATES)
    have = sorted(p.name[len("w9_shadow_"):-len(".npy")] for p in WORLD.glob(SHADOW_GLOB))
    assert have == sorted(W9.SHADOW_DATES)
    # 〔2-4〕W9 の容量のゲートは宣言を実測に合わせた=PASS(落ちたゲートに W9 は無い)
    assert stages["W9"]["gates"]["shadow_bytes_per_day_le_budget"]["pass"] is True
    summary = json.loads((WORLD / "acceptance" / "summary.json").read_text(encoding="utf-8"))
    assert not any(g["stage"] == "W9" for g in summary["gates_failed"])


@_needs_world
def test_v1_window_days_read_their_own_shadow():
    """窓の 7 日(2026-07-13〜07-19)は暦の日付の影を読む(近い日の影=つなぎ BR-SHADOW-NEAREST-DAY は窓の外の日だけ)。"""
    have = {p.name[len("w9_shadow_"):-len(".npy")] for p in WORLD.glob(SHADOW_GLOB)}
    for d in ("2026-07-13", "2026-07-14", "2026-07-15", "2026-07-16", "2026-07-17", "2026-07-18", "2026-07-19"):
        assert ENV.nearest_shadow_date(tuple(sorted(have)), d) == d


# ---------------------------------------------------------------- 〔2-4 検収 M1〕前の資産を組む(合成の置き場)


def _tool():
    spec = importlib.util.spec_from_file_location("activate_vb24", TOOL)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _write(root: Path, files: dict[str, bytes], build_hash: str) -> None:
    (root / "acceptance").mkdir(parents=True, exist_ok=True)
    for rel, body in files.items():
        (root / rel).write_bytes(body)
    (root / "build_manifest.json").write_text(json.dumps({"build_hash": build_hash}), encoding="utf-8")


@pytest.fixture()
def activated(tmp_path):
    """合成の「前」の資産 → 組んだ資産 → plan → apply まで回した置き場(本体の v2 の代わり=``live``)。"""
    T = _tool()
    before, stage = tmp_path / "before", tmp_path / "stage"
    common = {"W1.header.json": b'{"w": 1}', "w1_cells.parquet": b"cells", "acceptance/summary.json": b"{}"}
    _write(before, {**common, "W12.header.json": b'{"v": "1.1.0"}', "w12_timetables.parquet": b"old"}, "aaaa")
    _write(stage, {**common, "W12.header.json": b'{"v": "1.2.0"}', "w12_timetables.parquet": b"new",
                   "w9_shadow_2026-07-18.npy": b"shadow"}, "bbbb")
    # W17 の jsonl は道具が写さない(エンジンは読まない)=前の資産にも組まない
    (before / "w17_prompts_x.jsonl").write_bytes(b"{}\n")
    steps, live, backup = tmp_path / "steps", tmp_path / "live", tmp_path / "pre"
    assert T.main(["plan", "--live", str(before), "--stage", str(stage), "--steps", str(steps)]) == 0
    _write(live, {**common, "W12.header.json": b'{"v": "1.1.0"}', "w12_timetables.parquet": b"old"}, "aaaa")
    (live / "w17_prompts_x.jsonl").write_bytes(b"{}\n")
    assert T.main(["apply", "--live", str(live), "--steps", str(steps), "--backup", str(backup)]) == 0
    assert T.main(["verify", "--live", str(live), "--steps", str(steps), "--want", "after"]) == 0
    return T, tmp_path, live, backup, steps


def test_m1_materialize_builds_the_previous_asset(activated):
    """退避(置き換えた 3 本)+本体の変わっていないファイル → 前の資産。足したファイルは除く。verify --want before が通る。"""
    T, tmp, live, backup, steps = activated
    assert sorted(p.name for p in backup.iterdir() if p.is_file()) == sorted(
        ["MANIFEST.sha256", "plan.json", "W12.header.json", "w12_timetables.parquet", "build_manifest.json"])
    out = tmp / "prev"
    assert T.main(["materialize", "--live", str(live), "--backup", str(backup), "--out", str(out)]) == 0
    assert T.main(["verify", "--live", str(out), "--steps", str(steps), "--want", "before"]) == 0
    assert T.build_hash(out) == "aaaa"
    assert sorted(T.asset_files(out)) == sorted(T.asset_files(tmp / "before"))  # 足した影は無い・W17 の jsonl も写さない
    for rel, q in T.asset_files(tmp / "before").items():
        assert (out / rel).read_bytes() == q.read_bytes(), rel
    assert T.build_hash(live) == "bbbb"  # 本体の代わりは書かない


def test_m1_materialize_stops_on_a_missing_backup_file(activated):
    """負の対照: 退避のファイルが欠けていたら組まずに止める(終了コード 2・置き場は作らない)。"""
    T, tmp, live, backup, steps = activated
    (backup / "w12_timetables.parquet").unlink()
    out = tmp / "prev"
    assert T.main(["materialize", "--live", str(live), "--backup", str(backup), "--out", str(out)]) == 2
    assert not out.exists()


def test_m1_materialize_refuses_a_non_empty_out_and_a_wrong_live(activated):
    """負の対照: 置き場が空でない・本体が plan の前とも後とも違う → 止める(終了コード 2)。"""
    T, tmp, live, backup, steps = activated
    out = tmp / "prev"
    out.mkdir()
    (out / "x").write_bytes(b"x")
    assert T.main(["materialize", "--live", str(live), "--backup", str(backup), "--out", str(out)]) == 2
    (live / "w12_timetables.parquet").write_bytes(b"other")
    assert T.main(["materialize", "--live", str(live), "--backup", str(backup), "--out", str(tmp / "prev2")]) == 2
