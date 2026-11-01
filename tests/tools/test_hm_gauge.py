# -*- coding: utf-8 -*-
"""tools/instruments/hm_gauge.py(第 3 期 3-3b・ヒストリーマッチングの直接判定の器)の試験(合成の値だけ=器だけ)。

- 非含意度の式 I = |z − 平均| / √(Var_ens + Var_obs + Var_disc)(手で計算した値)・分母 0 は落ちる。
- 束ね: 2 つ以上の指標は 2 番目に大きい値・1 つは最大。閾値 3 で残す/除く。残りが空なら警告。
- 守り(負の対照): 候補は離散の seed の組だけ(係数の欄は ValueError)・観測は較正側だけ(検証側は PermissionError)・
  封印と検証側の道筋は開く前に落ちる。CLI の入出力。
- 〔検収 M2〕読む守りは大文字の形とつなぎ(junction・名に語を含まない)の形も落とす(``read_guard.deny_hit``)。
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_PATH = ROOT / "tools" / "instruments" / "hm_gauge.py"


@pytest.fixture(scope="module")
def H():
    name = "hm_gauge"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _PATH)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


OBS = {"a": {"z": 10.0, "var_obs": 1.0, "var_disc": 2.0, "side": "calibration"},
       "b": {"z": 0.0, "var_obs": 0.5, "var_disc": 0.5, "side": "calibration"},
       "c": {"z": 5.0, "var_obs": 0.0, "var_disc": 1.0, "side": "calibration"}}


def test_implausibility_formula(H):
    assert H.implausibility(10.0, 7.0, 6.0, 1.0, 2.0) == pytest.approx(1.0)
    assert H.implausibility(0.0, 4.0, 0.0, 0.5, 0.5) == pytest.approx(4.0)
    with pytest.raises(ValueError):
        H.implausibility(1.0, 0.0, 0.0, 0.0, 0.0)
    assert H.combine([1.0, 5.0, 2.0]) == (2.0, "second_max") and H.combine([4.0]) == (4.0, "max")
    assert H.THRESHOLD == 3.0


def test_judge_keeps_and_drops_by_the_second_largest(H):
    cands = [{"population_seed": 11, "environment_seed": 11}, {"population_seed": 12, "environment_seed": 12},
             {"population_seed": 13, "environment_seed": 13}]
    runs = [
        [{"a": 9.0, "b": 0.5, "c": 5.0}, {"a": 11.0, "b": -0.5, "c": 5.0}],     # 合う
        [{"a": 10.0, "b": 9.0, "c": 5.0}, {"a": 10.0, "b": 9.0, "c": 5.0}],     # b だけ外れる(2 番目は小さい=残る)
        [{"a": 30.0, "b": 9.0, "c": 5.0}, {"a": 30.0, "b": 9.0, "c": 5.0}],     # 2 つ外れる=除く
    ]
    out = H.judge(cands, runs, OBS)
    r0, r1, r2 = out["rows"]
    # 候補 1: a の平均 10・分散 2 → I=0 / b の平均 0・分散 0.5 → I=0
    assert r0["metrics"]["a"]["I"] == pytest.approx(0.0) and r0["metrics"]["a"]["var_ens"] == pytest.approx(2.0)
    assert r0["plausible"] and r0["combine"] == "second_max"
    assert r1["I_M"] == pytest.approx(9.0) and r1["I_combined"] == pytest.approx(0.0) and r1["plausible"]
    assert r2["metrics"]["a"]["I"] == pytest.approx(20.0 / math.sqrt(3.0)) and not r2["plausible"]
    assert out["kept"] == [cands[0], cands[1]] and out["n_kept"] == 2 and out["warning"] is None
    none = H.judge(cands[2:], runs[2:], OBS)
    assert none["kept"] == [] and "警告" in none["warning"]
    one = H.judge(cands[:1], [[{"a": 10.0}]], {"a": OBS["a"]})
    assert one["rows"][0]["combine"] == "max" and one["rows"][0]["metrics"]["a"]["var_ens"] == 0.0


def test_guards(H, tmp_path):
    runs = [[{"a": 10.0}]]
    with pytest.raises(ValueError, match="係数"):
        H.judge([{"population_seed": 1, "environment_seed": 1, "beta": 0.3}], runs, {"a": OBS["a"]})
    with pytest.raises(ValueError, match="整数"):
        H.judge([{"population_seed": 1.5, "environment_seed": 1}], runs, {"a": OBS["a"]})
    with pytest.raises(PermissionError, match="較正側"):
        H.judge([{"population_seed": 1, "environment_seed": 1}], runs, {"a": {**OBS["a"], "side": "validation"}})
    with pytest.raises(PermissionError, match="封印"):
        H.check_path("docs/bench/c7/holdout/x.json")
    with pytest.raises(PermissionError):
        H.check_path("data/kddi_la/x.json")
    doc = {"candidates": [{"population_seed": 11, "environment_seed": 11}], "runs": [[{"a": 9.0}, {"a": 11.0}]],
           "observations": {"a": OBS["a"]}}
    (tmp_path / "in.json").write_text(json.dumps(doc), encoding="utf-8")
    assert H.main(["judge", "--input", str(tmp_path / "in.json"), "--out", str(tmp_path / "out.json")]) == 0
    out = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert out["schema"] == H.SCHEMA and out["n_kept"] == 1 and out["candidate_keys"] == ["population_seed",
                                                                                          "environment_seed"]


# ================================================================= 〔検収 M2〕読む守り(大文字・つなぎ)
def _junction(link: Path, target: Path) -> bool:
    """名に語を含まないつなぎ(Windows=junction・ほか=symlink)。作れなければ False。"""
    target.mkdir(parents=True, exist_ok=True)
    try:
        if os.name == "nt":
            import _winapi

            _winapi.CreateJunction(str(target), str(link))
        else:
            os.symlink(target, link, target_is_directory=True)
    except (OSError, AttributeError, ImportError):
        return False
    return True


def test_read_guard_catches_upper_case_and_junction(H, tmp_path):
    for p in ("data/KDDI_LA/x.json", "docs/bench/anchors/Presence_Validation_Anchors_v0.json",
              "data/REALWORLD_LIVE/x.json", "DOCS/BENCH/C7/HOLDOUT/x.json"):
        with pytest.raises(PermissionError):
            H.check_path(p)
    H.check_path(tmp_path / "plain.json")  # 語の無い道筋は通る(正の対照)
    link = tmp_path / "plain_dir"
    if not _junction(link, tmp_path / "jinryu_fake"):
        pytest.skip("つなぎを作れない")
    try:
        assert "jinryu" not in str(link / "x.json").lower()  # 生の形には語が無い=実体の道筋で落ちる
        with pytest.raises(PermissionError, match="jinryu"):
            H.check_path(link / "x.json")
    finally:
        os.rmdir(link) if os.name == "nt" else os.unlink(link)
