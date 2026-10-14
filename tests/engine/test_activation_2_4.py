"""〔第 2 期 2-4 V1〕版上げ 2 回目の世界資産の活性化(2-3b の W12 1.2.0 実ダイヤ+2-3 の W9 の影 7 日の窓)。

本体の ``data/world/v2`` に ``docs/bench/analysis/wallbounce-1012/vb24/tools/activate_vb24.py apply`` で写した後の資産を見る
(写す前の作業木・本体では落ちる=10e ACT と同じ。記録 ``docs/bench/analysis/wallbounce-1012/vb24/README.md`` の V1)。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shibuya.build.vis import w9_shadow as W9
from shibuya.engine.processes import environment as ENV
from shibuya.world.assets import SHADOW_GLOB

REPO_ROOT = Path(__file__).resolve().parents[2]
WORLD = REPO_ROOT / "data" / "world" / "v2"
RECORD = REPO_ROOT / "docs" / "bench" / "analysis" / "wallbounce-1012" / "vb24" / "v1_activation_plan.json"

pytestmark = pytest.mark.requires_data("world_v2:build_manifest.json")


def _manifest() -> dict:
    return json.loads((WORLD / "build_manifest.json").read_text(encoding="utf-8"))


def test_v1_build_hash_is_the_activated_one():
    plan = json.loads(RECORD.read_text(encoding="utf-8"))
    assert _manifest()["build_hash"] == plan["build_hash_after"]


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


def test_v1_window_days_read_their_own_shadow():
    """窓の 7 日(2026-07-13〜07-19)は暦の日付の影を読む(近い日の影=つなぎ BR-SHADOW-NEAREST-DAY は窓の外の日だけ)。"""
    have = {p.name[len("w9_shadow_"):-len(".npy")] for p in WORLD.glob(SHADOW_GLOB)}
    for d in ("2026-07-13", "2026-07-14", "2026-07-15", "2026-07-16", "2026-07-17", "2026-07-18", "2026-07-19"):
        assert ENV.nearest_shadow_date(tuple(sorted(have)), d) == d
