# -*- coding: utf-8 -*-
"""``tools/c7/seed_exchangeability.py``(D-83 ⑦)の検収。合成 checkpoints.json のみ。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "c7"))
import seed_exchangeability as sx  # noqa: E402


def _doc(seed: int, **over):
    d = {
        "schema": "shibuya.cli/checkpoints/1", "run_id": f"r-s{seed}", "n_agents": 100, "seed": seed, "ticks": 24,
        "final_hash": f"h{seed}",
        "checkpoints": [{"tick": 5, "population_hash": "P", "schedule_hash": "S", "world_hash": "W", "agents_hash": f"A{seed}"},
                        {"tick": 11, "population_hash": "P", "schedule_hash": "S", "world_hash": "W", "agents_hash": f"B{seed}"}],
        "manifest": {"derive_rule": "v2.1", "attendance_rate": 1.0, "fleet": {"cache_salt": f"salt{seed}", "mode": "calibration"},
                     "intent_mode": "vocab", "ablations": ["x"]},
    }
    for k, v in over.items():
        if k.startswith("manifest."):
            d["manifest"][k.split(".", 1)[1]] = v
        else:
            d[k] = v
    return d


def test_identical_config_is_exchangeable_with_only_allowed_diffs():
    res = sx.compare([_doc(1), _doc(2), _doc(3)], ["s1", "s2", "s3"])
    assert res["exchangeable"] is True
    assert {r["key"] for r in res["diff_allowed"]} == {"seed", "run_id", "final_hash", "manifest.fleet.cache_salt"}
    assert res["diff_unexplained"] == [] and res["diff_declared_equivalent"] == []
    assert res["checkpoint_ticks"] == [5, 11]
    assert res["population_seed_independent"] is True
    assert res["hash_identity"]["agents_hash"]["identical_all_ticks"] is False  # 状態は seed で違って当然


def test_unexplained_manifest_diff_fails():
    res = sx.compare([_doc(1), _doc(2, **{"manifest.attendance_rate": 0.8})], ["s1", "s2"])
    assert res["exchangeable"] is False
    assert [r["key"] for r in res["diff_unexplained"]] == ["manifest.attendance_rate"]
    assert res["diff_unexplained"][0]["values"] == {"s1": "1.0", "s2": "0.8"}


def test_declared_equivalent_passes_with_reason_and_only_for_listed_values():
    eq = sx.parse_equivalents(["manifest.intent_mode=None|vocab:AB7 以後の既定名・挙動同一"])
    res = sx.compare([_doc(1, **{"manifest.intent_mode": None}), _doc(2)], ["s1", "s2"], eq)
    assert res["exchangeable"] is True
    assert res["diff_declared_equivalent"][0]["reason"] == "AB7 以後の既定名・挙動同一"
    # 宣言に無い値(open)が混ざれば未説明に戻る
    res2 = sx.compare([_doc(1, **{"manifest.intent_mode": "open"}), _doc(2)], ["s1", "s2"], eq)
    assert res2["exchangeable"] is False and res2["diff_unexplained"][0]["key"] == "manifest.intent_mode"


def test_must_match_and_tick_list_mismatch_fail():
    res = sx.compare([_doc(1), _doc(2, n_agents=101)], ["s1", "s2"])
    assert res["exchangeable"] is False and res["must_match_failures"] == ["n_agents"]
    d2 = _doc(2); d2["checkpoints"] = d2["checkpoints"][:1]
    res2 = sx.compare([_doc(1), d2], ["s1", "s2"])
    assert res2["exchangeable"] is False and res2["checkpoint_ticks_match"] is False


def test_population_hash_dependence_is_reported_not_failed():
    d2 = _doc(2)
    for c in d2["checkpoints"]:
        c["population_hash"] = "P2"
    res = sx.compare([_doc(1), d2], ["s1", "s2"])
    assert res["exchangeable"] is True and res["population_seed_independent"] is False


def test_flatten_and_equivalent_parsing():
    assert sx.flatten({"a": {"b": 1, "c": [1, 2]}, "d": None}) == {"a.b": 1, "a.c": "[1, 2]", "d": None}
    with pytest.raises(SystemExit):
        sx.parse_equivalents(["no-reason=1|2"])


def test_cli_writes_json_and_refuses_overwrite(tmp_path: Path):
    p1, p2 = tmp_path / "s1.json", tmp_path / "s2.json"
    p1.write_text(json.dumps(_doc(1)), encoding="utf-8"); p2.write_text(json.dumps(_doc(2)), encoding="utf-8")
    out = tmp_path / "x.json"
    assert sx.main(["--checkpoints", f"s1={p1}", "--checkpoints", f"s2={p2}", "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["exchangeable"] is True
    assert sx.main(["--checkpoints", f"s1={p1}", "--checkpoints", f"s2={p2}", "--out", str(out)]) == 2
