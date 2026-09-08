"""manifest 機械化規則の追加検査(層2レビュー指摘・C0出口): MARLIN atomic add の禁止・phases の固定列。"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from shibuya.manifest import schema

FIXTURE = Path(__file__).parent / "fixtures" / "manifest_example.yaml"


def _load_dict() -> dict:
    with FIXTURE.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_fixture_declares_marlin_atomic_add_off():
    d = _load_dict()
    assert d["llm_fleet"]["env"][schema.MARLIN_ATOMIC_ADD_ENV] == schema.MARLIN_ATOMIC_ADD_REQUIRED


def test_marlin_atomic_add_required_for_verification_modes():
    d = _load_dict()
    d["identity"]["mode"] = "calibration"
    d["llm_fleet"]["env"][schema.MARLIN_ATOMIC_ADD_ENV] = "1"
    with pytest.raises(ValueError, match="MARLIN"):
        schema.RunManifest.model_validate(d)


def test_marlin_atomic_add_not_enforced_for_smoke():
    d = _load_dict()
    assert d["identity"]["mode"] == "smoke"
    d["llm_fleet"]["env"][schema.MARLIN_ATOMIC_ADD_ENV] = "1"
    schema.RunManifest.model_validate(d)  # 検証ラン以外では拒否しない


def test_phases_are_fixed_sequence():
    d = _load_dict()
    assert d["concurrency"]["phases"] == list(schema.REQUIRED_PHASES)
    d["concurrency"]["phases"] = ["arbitrate", "read_intent", "commit"]
    with pytest.raises(ValueError, match="phases"):
        schema.RunManifest.model_validate(d)
