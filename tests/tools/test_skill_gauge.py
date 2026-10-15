# -*- coding: utf-8 -*-
"""tools/instruments/skill_gauge.py(第 3 期 3-3b・CP14 の技量スコアの隣の生の点数)の試験。

- fair CRPS の既知の値(手で計算)・通常の CRPS・点の予測は絶対誤差・メンバー 1 本の fair CRPS は定義しない。
- rank histogram(順位の度数・同じ値の割り方は seed つき)・広がりと誤差の比(√((M+1)/M) の補正つき・手で計算)。
- 技量スコア=1 − fair CRPS/基準の CRPS(``ensemble.skill_score`` と同じ式)を生の点数の隣に並べ、器(``skill_container``)を埋める。
- mock のアンサンブル(合成の世界の小さなランを偶然の seed で 5 本+観測の代わりの 1 本)で点数が出る。
- 〔検収 L7〕入力の道筋に読む守り(封印と検証側の語=``read_guard.deny_hit``・大文字の形も)=開く前に落ちる。
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from shibuya.engine.experiment import ensemble as EN

from tests.engine.experiment._x33 import form

ROOT = Path(__file__).resolve().parents[2]
_PATH = ROOT / "tools" / "instruments" / "skill_gauge.py"


@pytest.fixture(scope="module")
def S():
    name = "skill_gauge"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _PATH)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def test_crps_known_values(S):
    assert S.crps_fair([1.0, 2.0, 3.0], 2.0) == pytest.approx(0.0)  # 2/3 − 8/12
    assert S.crps_ensemble([1.0, 2.0, 3.0], 2.0) == pytest.approx(2.0 / 9.0)  # 2/3 − 8/18
    assert S.crps_fair([0.0, 2.0], 1.0) == pytest.approx(0.0)
    assert S.crps_fair([0.0, 0.0], 1.0) == pytest.approx(1.0)  # 広がり 0 は絶対誤差
    assert S.crps_fair([0.0, 4.0], 0.0) == pytest.approx(2.0 - 8.0 / 4.0)
    assert S.crps_point(3.0, 1.0) == 2.0
    with pytest.raises(ValueError):
        S.crps_fair([1.0], 1.0)
    # fair は通常より広がりの項を大きく引く(有限のメンバーの偏りの補正)
    x = list(np.random.default_rng(0).normal(0.0, 1.0, 8))
    assert S.crps_fair(x, 0.3) < S.crps_ensemble(x, 0.3)


def test_rank_histogram_and_spread_skill(S):
    ens = [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [1.0, 2.0, 3.0]]
    obs = [0.0, 1.5, 2.5, 9.0]
    assert S.rank_histogram(ens, obs) == [1, 1, 1, 1]
    tie = S.rank_histogram([[1.0, 1.0]], [1.0], seed=0)
    assert sum(tie) == 1 and tie == S.rank_histogram([[1.0, 1.0]], [1.0], seed=0)  # seed つき=決定的
    ss = S.spread_skill([[0.0, 2.0], [1.0, 3.0]], [1.0, 1.0])
    # 分散(1/(M−1))は 2 と 2 → 広がり √2・平均 1 と 2 → RMSE √(0.5)・補正 √(3/2)
    assert ss["spread"] == pytest.approx(math.sqrt(2.0)) and ss["rmse"] == pytest.approx(math.sqrt(0.5))
    assert ss["ratio"] == pytest.approx(math.sqrt(1.5) * math.sqrt(2.0) / math.sqrt(0.5))
    with pytest.raises(ValueError):
        S.spread_skill([[1.0]], [1.0])


def test_skill_next_to_raw_scores_and_fill_the_container(S):
    ens = [[9.0, 11.0], [19.0, 21.0]]
    obs = [10.0, 20.0]
    sc = S.score_metric(ens, obs, {"mean": [12.0, 18.0], "previous_week": [10.0, 20.0]})
    assert sc["raw"]["crps_fair"] == pytest.approx(0.0) and sc["raw"]["baseline_crps"]["mean"] == 2.0
    assert sc["skill"]["mean"] == pytest.approx(EN.skill_score(0.0, 2.0)) == pytest.approx(1.0)
    assert sc["skill"]["previous_week"] is None  # 基準の点数 0 は定義しない
    c = S.fill(EN.skill_container(form()), {"calls": sc})
    slot = c["metrics"]["calls"]
    assert slot["error"] == pytest.approx(0.0) and slot["skill"]["mean"] == pytest.approx(1.0)
    assert slot["raw"]["crps_fair"] == pytest.approx(0.0) and slot["raw"]["members"] == 2
    assert slot["raw"]["rank_histogram"] == sc["raw"]["rank_histogram"]
    assert c["metrics"]["final_len"]["error"] is None  # 埋めない指標は空のまま
    assert EN.skill_container(form())["metrics"]["calls"]["error"] is None  # 元の器は変えない
    with pytest.raises(KeyError):
        S.fill(EN.skill_container(form()), {"nope": sc})


def test_scores_of_a_mock_ensemble(S, tmp_path):
    from shibuya import cli

    kw = dict(n_agents=20, world_dir=None, n_cells=9, ticks=600, renderer="stub", vocab_version="v3",
              population_seed=1, environment_seed=1)
    members = [float(cli.run(seed=s, **kw).llm_calls) for s in range(1, 6)]  # 偶然 5 本(初期状態は同じ)
    obs = float(cli.run(seed=9, **kw).llm_calls)  # 観測の代わり(合成)
    doc = {"metrics": {"calls": {"ensemble": [members], "obs": [obs], "baselines": {"mean": [float(np.mean(members))]}}}}
    (tmp_path / "in.json").write_text(json.dumps(doc), encoding="utf-8")
    assert S.main(["score", "--input", str(tmp_path / "in.json"), "--out", str(tmp_path / "out.json")]) == 0
    out = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    m = out["metrics"]["calls"]
    assert m["raw"]["members"] == 5 and sum(m["raw"]["rank_histogram"]) == 1 and len(m["raw"]["rank_histogram"]) == 6
    assert m["raw"]["crps_fair"] == pytest.approx(S.crps_fair(members, obs))
    assert m["raw"]["baseline_crps"]["mean"] == pytest.approx(abs(float(np.mean(members)) - obs))
    assert len(set(members)) > 1  # 偶然の seed で動く=広がりがある


# ================================================================= 〔検収 L7〕読む守り
def test_read_guard_on_the_input(S, tmp_path):
    for p in ("data/realworld_live/x.json", "data/KDDI_LA/x.json", "docs/bench/c7/holdout/obs.json",
              "docs/bench/anchors/Hunger_Energy_Validation_Anchors_v0.json"):
        with pytest.raises(PermissionError, match="封印"):
            S.check_path(p)
    S.check_path(tmp_path / "plain.json")  # 語の無い道筋は通る(正の対照)
    # CLI は開く前に落とす(ファイルが無くても PermissionError=開いていない)
    with pytest.raises(PermissionError):
        S.main(["score", "--input", str(tmp_path / "holdout" / "x.json"), "--out", str(tmp_path / "out.json")])
    assert not (tmp_path / "out.json").exists()
