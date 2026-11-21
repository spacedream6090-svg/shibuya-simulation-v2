"""段 1 の移動(本物の世界・組んだ資産 ``data/world/v2_stage_5-1``・データの無い所では飛ばす)。

- 旧のセルの移動(legacy)は資産のある世界でも今のセルの移動(nav1 の欄を作らない・manifest の space.effective=legacy)。
  〔第347 止めた切替口の削除〕切替口 ``--space legacy``(``space="legacy"``・環境変数 ``SHIBUYA_SPACE``)は消した=legacy は
  試験の中だけの口(案 s1=``tests/engine/space/_legacy.py``)で回す。``space="legacy"`` と環境変数は止まる。
- 資産の無い合成の世界で nav1 を頼むと legacy で回り、理由を書く。〔段 1 の検収 問い 4〕本番の世界(build_manifest.json の
  build_hash を持つ世界)で資産が無ければ止める。〔L4〕前は ``space`` の指定が環境変数 ``SHIBUYA_SPACE`` より強いことを見た
  (〔第347〕環境変数は消した=置けばランの入口で止まる)。
- nav1 のランは final が動き、再開=通し(止めて書いて続けた checkpoint が通しと同じ)。
- 段 B の宣言の外 0(書きの守りを入れたまま回る=系の宣言の外の列を書けば落ちる)。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shibuya.interfaces.cli import main as cli
from shibuya.world.model.space import nav1 as N
from shibuya.world.model.navmesh import navmesh_available
from tests.engine.space._legacy import legacy_space

STAGE = Path("data/world/v2_stage_5-1")
needs_stage = pytest.mark.skipif(not navmesh_available(STAGE), reason="組んだ資産 v2_stage_5-1 が無い")

KW = dict(n_agents=150, seed=1, ticks=360, vocab_version="v3", activity=True)
TAG_347 = "stable-v2-before-switch-removal-347"


def _run(space, world=STAGE, **extra):
    return cli.run(world_dir=str(world), space=space, **KW, **extra)


@pytest.fixture(scope="module")
def legacy_stage():
    """〔第347〕前は ``_run("legacy")``(切替口)。試験の中だけの口で旧のセルの移動にする。"""
    with pytest.MonkeyPatch.context() as mp:
        legacy_space(mp)
        return _run(None)


@pytest.fixture(scope="module")
def nav1_stage():
    return _run("nav1")


@needs_stage
def test_legacy_on_the_staged_world_is_legacy(legacy_stage):
    sp = legacy_stage.run_manifest_fields()["space"]
    assert sp["requested"] == "legacy" and sp["effective"] == "legacy" and sp["meter"] is None
    assert sp["reason"] == N.LEGACY_FOR_TESTS_REASON  # 〔第347〕試験の中だけの口で選んだと書く
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


def test_m1_a_run_on_the_test_only_port_is_an_arm_run_through_cli_run(tmp_path, monkeypatch):
    """〔第347・検収 M1〕試験の中だけの口(印)で旧のセルの移動にしたランは、``cli.run`` のランの種類で腕に数える(前の頼み方
    ``space="legacy"`` は ``run_arms`` に入って arm だった)。印を立てないランは前と同じ(ほかに腕の無い引数なら reproduction)。
    ランの種類は試験の中では ``test`` になるので、pytest の印の環境変数を外して見る。合成の世界・2 刻み。"""
    from shibuya.experiments.port import run_kind as RK

    monkeypatch.delenv(RK.PYTEST_ENV, raising=False)
    kw = dict(n_agents=30, seed=1, ticks=2, vocab_version="v3", world_dir=str(tmp_path / "none"))  # ほかに腕の無い引数
    base = cli.run(**kw)
    assert base.run_kind == RK.REPRODUCTION and base.run_manifest_fields()["space"]["requested"] == "nav1"
    with pytest.MonkeyPatch.context() as mp:
        legacy_space(mp)
        res = cli.run(**kw)
    assert res.run_kind == RK.ARM
    assert res.run_manifest_fields()["space"]["requested"] == "legacy"
    assert N.legacy_for_tests() is False  # 印は戻った


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
def test_q4_production_world_without_assets_stops_and_legacy_runs(monkeypatch):
    """本番の形で資産が無ければ nav1 は止まる・旧のセルの移動なら回る。〔第347〕前は ``space="legacy"`` で回した(切替口)=
    今は ``space="legacy"`` は止まる(消した口)。旧のセルの移動は試験の中だけの口で回す。止める文は安定版のタグを書く。"""
    assert not navmesh_available(PRE)
    with pytest.raises(FileNotFoundError, match=f"安定版のタグ {TAG_347}"):
        cli.run(n_agents=50, seed=1, ticks=2, world_dir=str(PRE), space="nav1")
    with pytest.raises(ValueError, match=f"space='legacy' は消した口.*{TAG_347}.*試験の中だけの口"):
        cli.run(n_agents=50, seed=1, ticks=2, world_dir=str(PRE), space="legacy")
    legacy_space(monkeypatch)
    res = cli.run(n_agents=50, seed=1, ticks=2, world_dir=str(PRE))
    assert res.run_manifest_fields()["space"]["effective"] == "legacy"


@needs_stage
def test_l4_the_space_env_stops_a_run_and_the_argument_takes_only_nav1(monkeypatch):
    """〔第347 止めた切替口の削除〕前(``test_l4_space_argument_beats_the_environment_in_a_run``)は「環境変数 legacy を置いても
    引数 nav1 が勝つ・引数なしは環境変数の legacy」。環境変数は消した: 置けばランの入口で止まる(引数 nav1 でも)。引数は nav1 と
    None だけ受け、どちらも nav1 で回る。"""
    monkeypatch.setenv("SHIBUYA_SPACE", "legacy")
    for space in ("nav1", None):
        with pytest.raises(ValueError, match=f"SHIBUYA_SPACE は消した切替口.*{TAG_347}"):
            cli.run(n_agents=50, seed=1, ticks=2, world_dir=str(STAGE), space=space)
    monkeypatch.delenv("SHIBUYA_SPACE")
    a = cli.run(n_agents=50, seed=1, ticks=2, world_dir=str(STAGE), space="nav1")
    b = cli.run(n_agents=50, seed=1, ticks=2, world_dir=str(STAGE))
    for res in (a, b):
        sp = res.run_manifest_fields()["space"]
        assert sp["requested"] == "nav1" and sp["effective"] == "nav1"
    assert a.final_hash == b.final_hash


# 〔段 5-1b・版上げ 4 回目〕既定は nav1+密度の推定 neighborhood。golden は資産を足した本番の世界(apply の後)でだけ回す
MAIN = Path("data/world/v2")
#: w6_v3_default(5,000 体・seed 1・1 日・v3)の final と呼数(記録 spatial-2026-10/sp1b)。既定=nav1+neighborhood・腕は
#: 環境変数 SHIBUYA_NAV1_DENSITY(cell・unscaled)。段 1 の nav1(cell・B4 の密度の段は人/セル)の値は d8b2d497eef28887/61,261
#: 〔11-01 段 2 の 4〕率の形の規則を外して動いた(前 None 7bfe215641b792ac / 62_176・cell 6cc4f835866c1ebd / 63_853・unscaled
#: ef9999b0d56e50da / 61_234=SHIBUYA_RATE_RULES=legacy で戻る・記録 s2-rates-1101)
NAV1_GOLDEN = {
    None: ("c8d68704b7b0760d", 60_939),  # 〔11-03 §3〕棚卸し B の欠陥 4 件の直しで動いた(前 73aa01d9afb206d0 / 61_066=SHIBUYA_DEFECT_FIXES_1103=legacy で戻る・記録 fix4-1103)
    "cell": ("ab503d82e499ccfe", 62_543),  # 〔11-03 §3〕棚卸し B の欠陥 4 件の直しで動いた(前 7b976b2272ef57e4 / 62_600=SHIBUYA_DEFECT_FIXES_1103=legacy で戻る・記録 fix4-1103)
    "unscaled": ("2d1c84ef289fb54d", 60_211),  # 〔11-03 §3〕棚卸し B の欠陥 4 件の直しで動いた(前 7a27bf218610714c / 60_191=SHIBUYA_DEFECT_FIXES_1103=legacy で戻る・記録 fix4-1103)
}


@pytest.mark.skipif(not navmesh_available(MAIN), reason="本番の世界に nav1 の資産が無い(活性化の前)")
@pytest.mark.parametrize("density", [None, pytest.param("cell", marks=pytest.mark.slow),
                                     pytest.param("unscaled", marks=pytest.mark.slow)])
def test_nav1_golden_w6_v3_default_on_the_activated_world(monkeypatch, density):
    from tests import golden_env as GE

    monkeypatch.delenv("SHIBUYA_SPACE", raising=False)
    if density is None:
        monkeypatch.delenv("SHIBUYA_NAV1_DENSITY", raising=False)
    else:
        monkeypatch.setenv("SHIBUYA_NAV1_DENSITY", density)
    res = cli.run(n_agents=5000, seed=1, world_dir=str(MAIN), vocab_version="v3")
    sp = res.run_manifest_fields()["space"]
    assert sp["effective"] == "nav1" and sp["navmesh"]["density_mode"] == (density or "neighborhood")
    if GE.platform_id() in GE.REGISTERED:
        assert (res.final_hash[:16], int(res.llm_calls)) == NAV1_GOLDEN[density]
    else:
        GE.warn_unregistered(f"nav1 の w6_v3_default({density or '既定'})")


@needs_stage
def test_default_is_nav1_on_the_staged_world(monkeypatch):
    monkeypatch.delenv("SHIBUYA_SPACE", raising=False)
    res = cli.run(n_agents=50, seed=1, ticks=2, world_dir=str(STAGE))
    sp = res.run_manifest_fields()["space"]
    assert sp["requested"] == "nav1" and sp["effective"] == "nav1"
