"""段 1 の移動の切替口(本物の世界・組んだ資産 ``data/world/v2_stage_5-1``・データの無い所では飛ばす)。

- ``--space legacy`` は資産のある世界でも今のセルの移動(nav1 の欄を作らない・manifest の space.effective=legacy)。
- 資産の無い合成の世界で nav1 を頼むと legacy で回り、理由を書く。〔段 1 の検収 問い 4〕本番の世界(build_manifest.json の
  build_hash を持つ世界)で資産が無ければ止める。〔L4〕``space`` の指定は環境変数 ``SHIBUYA_SPACE`` より強い。
- nav1 のランは final が動き、再開=通し(止めて書いて続けた checkpoint が通しと同じ)。
- 段 B の宣言の外 0(書きの守りを入れたまま回る=系の宣言の外の列を書けば落ちる)。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shibuya import cli
from shibuya.world.navmesh import navmesh_available

STAGE = Path("data/world/v2_stage_5-1")
needs_stage = pytest.mark.skipif(not navmesh_available(STAGE), reason="組んだ資産 v2_stage_5-1 が無い")

KW = dict(n_agents=150, seed=1, ticks=360, vocab_version="v3", activity=True)


def _run(space, world=STAGE, **extra):
    return cli.run(world_dir=str(world), space=space, **KW, **extra)


@pytest.fixture(scope="module")
def legacy_stage():
    return _run("legacy")


@pytest.fixture(scope="module")
def nav1_stage():
    return _run("nav1")


@needs_stage
def test_legacy_on_the_staged_world_is_legacy(legacy_stage):
    sp = legacy_stage.run_manifest_fields()["space"]
    assert sp["requested"] == "legacy" and sp["effective"] == "legacy" and sp["meter"] is None
    assert not any(k.startswith("nav1:") for k in legacy_stage.frozen_sources)


@needs_stage
def test_nav1_moves_the_final_and_records_the_meter(legacy_stage, nav1_stage):
    sp = nav1_stage.run_manifest_fields()["space"]
    assert sp["effective"] == "nav1" and sp["meter"]["routes_planned"] > 0
    assert nav1_stage.final_hash != legacy_stage.final_hash
    assert any(k.startswith("nav1:") for k in nav1_stage.frozen_sources)


def test_nav1_without_assets_runs_legacy_and_says_why(tmp_path):
    res = cli.run(n_agents=50, seed=1, ticks=60, n_cells=16, world_dir=str(tmp_path / "none"), space="nav1")
    sp = res.run_manifest_fields()["space"]
    assert sp["effective"] == "legacy" and sp["reason"]


@needs_stage
def test_nav1_resume_equals_straight(tmp_path, nav1_stage):
    a = _run("nav1", state_out=tmp_path / "s", stop_at_tick=200)
    f = a.resume["state_files"][-1]["file"]
    b = _run("nav1", resume_from=tmp_path / "s" / f)
    straight = [(c.tick, c.combined) for c in nav1_stage.checkpoints if c.tick >= 200]
    resumed = [(c.tick, c.combined) for c in b.checkpoints if c.tick >= 200]
    assert resumed and resumed == straight
    assert b.run_manifest_fields()["space"]["meter"]["replans_on_resume"] >= 0


PRE = Path("data/world/v2_pre_4-3")  # 本番の形の世界(build_hash あり)で nav1 の資産の無い置き場(退避)


@pytest.mark.skipif(not (PRE / "build_manifest.json").exists(), reason="退避の世界 v2_pre_4-3 が無い")
def test_q4_production_world_without_assets_stops_and_legacy_runs():
    assert not navmesh_available(PRE)
    with pytest.raises(FileNotFoundError):
        cli.run(n_agents=50, seed=1, ticks=2, world_dir=str(PRE), space="nav1")
    res = cli.run(n_agents=50, seed=1, ticks=2, world_dir=str(PRE), space="legacy")
    assert res.run_manifest_fields()["space"]["effective"] == "legacy"


@needs_stage
def test_l4_space_argument_beats_the_environment_in_a_run(monkeypatch):
    monkeypatch.setenv("SHIBUYA_SPACE", "legacy")
    a = cli.run(n_agents=50, seed=1, ticks=2, world_dir=str(STAGE), space="nav1")
    b = cli.run(n_agents=50, seed=1, ticks=2, world_dir=str(STAGE))
    assert a.run_manifest_fields()["space"]["effective"] == "nav1"
    assert b.run_manifest_fields()["space"]["effective"] == "legacy"
    assert a.run_manifest_fields()["space"]["requested"] == "nav1"


# 〔段 1 の再検収 H1・親の判断〕段 1 は既定 legacy の腕。nav1 の腕の golden は資産を足した本番の世界(apply の後)でだけ回す
MAIN = Path("data/world/v2")
#: nav1 の腕の w6_v3_default(5,000 体・seed 1・1 日・v3)の final と呼数(記録 spatial-2026-10/sp1 §8-1)
NAV1_ARM_GOLDEN = ("d8b2d497eef28887", 61_261)


@pytest.mark.skipif(not navmesh_available(MAIN), reason="本番の世界に nav1 の資産が無い(活性化の前)")
def test_nav1_arm_golden_w6_v3_default_on_the_activated_world():
    from tests import golden_env as GE

    res = cli.run(n_agents=5000, seed=1, world_dir=str(MAIN), vocab_version="v3", space="nav1")
    assert res.run_manifest_fields()["space"]["effective"] == "nav1"
    if GE.platform_id() in GE.REGISTERED:
        assert (res.final_hash[:16], int(res.llm_calls)) == NAV1_ARM_GOLDEN
    else:
        GE.warn_unregistered("nav1 の腕の w6_v3_default")


@needs_stage
def test_default_is_legacy_on_the_staged_world():
    res = cli.run(n_agents=50, seed=1, ticks=2, world_dir=str(STAGE))
    sp = res.run_manifest_fields()["space"]
    assert sp["requested"] == "legacy" and sp["effective"] == "legacy"
