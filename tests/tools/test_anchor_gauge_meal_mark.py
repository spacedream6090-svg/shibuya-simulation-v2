# -*- coding: utf-8 -*-
"""2-0 の計器の「第 18-1 表と比べた食事時刻の結果」の印(小さな版上げ・回答 10-13b §7 の 2)。

置き換えの前の版(腕 validation・欄なし)=無効(作る側に使われている)・置き換えの後(w17 でエンジンが検証側の空腹の錨を
開いていない)=検証可。計器は第 18-1 表と比べない(〔検〕は読まない)=印だけ。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_DIR = ROOT / "tools" / "instruments"


def _load(name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _DIR / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def G():
    return _load("anchor_gauge")


def test_mark_is_invalid_before_the_replacement_and_valid_after(G):
    old = G.meal_time_validation_mark({"record_opened_files": [
        {"path": "docs/bench/anchors/hunger_energy_validation_anchors_v0.json", "gauge_deny_token": "x"}]})
    assert old["meal_default"] == "(欄なし)" and old["status"] == G.MEAL_T18_INVALID
    assert G.meal_time_validation_mark({"meal_default": "validation"})["status"] == G.MEAL_T18_INVALID
    new = G.meal_time_validation_mark({"meal_default": "w17", "record_opened_files": [
        {"path": "docs/bench/anchors/hunger_energy_build_anchors_v0.json", "gauge_deny_token": None}]})
    assert new["status"] == G.MEAL_T18_VALID and new["engine_opened_validation_hunger_anchors"] == []
    # 負の対照: w17 でも検証側の空腹の錨を開いていたら無効のまま
    bad = G.meal_time_validation_mark({"meal_default": "w17", "record_opened_files": [
        {"path": "docs/bench/anchors/hunger_energy_validation_anchors_v0.json", "gauge_deny_token": "x"}]})
    assert bad["status"] == G.MEAL_T18_INVALID


def test_markdown_carries_the_mark(G, monkeypatch):
    doc = {"arms": {"mock": {"meta": {"manifest": {}}, "meal_time_vs_t18_1": G.meal_time_validation_mark(
        {"meal_default": "w17"})}, "classical": {"meta": {"manifest": {}}}}, "area_map": {}, "declared": {},
           "inputs_read": []}
    monkeypatch.setattr(G, "_md_arm", lambda arm, a: [])
    md = G.render_markdown(doc)
    assert f"mock={G.MEAL_T18_VALID}" in md and f"classical={G.MEAL_T18_INVALID}" in md
