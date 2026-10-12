"""10e(版上げ 1 回目)B0 資産の指紋・B1 旧資産の切替口(第330)。

- **B0**: manifest の ``frozen_sources`` に、ランが実際に読んだ騒音の地図(W10 の 3 本)・天気(W13)・時刻表(W12)・
  影(W9・開いた日だけ)の sha256 を、読み手ごとの印(``world:``・``perception:``・``process:``)を付けて足す。
  騒音の地図は 2 か所(``world.assets._noise_stage_per_cell`` と ``perception.renderer._street_aggregate``)で読むので、
  集約後のセル別の段の指紋(``noise_stage_cells``)も両方に出す=2 つが同じ地図を読んだことが記録から分かる。
  final・checkpoint には入らない(manifest だけが動く)。
- **B1**: ``--world-assets-pre10e <dir>``(``run_day(world_assets_pre10e=…)``)で W10・W12・W13・W9 を 1 か所の
  退避先から読む。騒音の 2 つの読み手は同じ口(``world.assets.AssetSource``)を通す。**版上げ 1 回目の直後に消す**。
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from shibuya.world import assets as WA

WORLD_DIR = Path(__file__).resolve().parents[2] / "data" / "world" / "v2"
HAS_WORLD = WA.assets_available(WORLD_DIR) and (WORLD_DIR / "w10_noise_stage_day.npy").is_file()
needs_world = pytest.mark.skipif(not HAS_WORLD, reason="世界資産(gitignore 下)が無い環境")

#: 小さな実ラン(世界資産・40 体・5 tick)。
SMALL = dict(n_agents=40, seed=1, ticks=5, checkpoint_every=5)


# ================================================================ 合成の W10(セル 4 つ・点 12)
def _tiny_grid():
    cell_ix = np.array([0, 1, 0, 1], dtype=np.int32)
    cell_iy = np.array([0, 0, 1, 1], dtype=np.int32)
    cell_band = np.zeros(4, dtype=np.int8)
    return cell_ix, cell_iy, cell_band


def _write_w10(d: Path, day: np.ndarray, night: np.ndarray) -> None:
    d.mkdir(parents=True, exist_ok=True)
    xs = np.array([10, 20, 30, 110, 120, 130, 10, 20, 30, 110, 120, 130], dtype=np.float64)
    ys = np.array([10, 10, 10, 10, 10, 10, 110, 110, 110, 110, 110, 110], dtype=np.float64)
    pq.write_table(pa.table({"x": xs, "y": ys, "band": ["GL"] * 12}), d / "w10_street_points.parquet")
    np.save(d / "w10_noise_stage_day.npy", day.astype(np.uint8))
    np.save(d / "w10_noise_stage_night.npy", night.astype(np.uint8))


def test_b0_world_reader_records_the_file_and_cell_hashes(tmp_path):
    day = np.array([0, 0, 1, 2, 2, 3, 1, 1, 1, 0, 0, 0])
    night = np.zeros(12)
    _write_w10(tmp_path / "a", day, night)
    d1, n1, s1 = WA._noise_stage_per_cell(tmp_path / "a", *_tiny_grid())
    assert d1.tolist() == [0, 2, 1, 0] and n1.tolist() == [0, 0, 0, 0]
    assert set(s1) == {"w10_noise_stage_day.npy", "w10_noise_stage_night.npy", "w10_street_points.parquet",
                       "noise_stage_cells"}
    for name in ("w10_noise_stage_day.npy", "w10_noise_stage_night.npy", "w10_street_points.parquet"):
        assert s1[name] == WA.file_sha256(tmp_path / "a" / name)
    assert s1["noise_stage_cells"] == WA.array_sha256(d1, n1)
    # 同じ中身の写し=同じ指紋 / 1 点だけ変えた地図=ファイルの指紋も段の指紋も変わる
    _write_w10(tmp_path / "b", day, night)
    assert WA._noise_stage_per_cell(tmp_path / "b", *_tiny_grid())[2] == s1
    day2 = day.copy()
    day2[0] = 3
    day2[1] = 3
    _write_w10(tmp_path / "c", day2, night)
    d3, _, s3 = WA._noise_stage_per_cell(tmp_path / "c", *_tiny_grid())
    assert d3.tolist() == [3, 2, 1, 0]
    assert s3["w10_noise_stage_day.npy"] != s1["w10_noise_stage_day.npy"]
    assert s3["noise_stage_cells"] != s1["noise_stage_cells"]
    assert s3["w10_noise_stage_night.npy"] == s1["w10_noise_stage_night.npy"]
    # W10 が無い=指紋も空
    assert WA._noise_stage_per_cell(tmp_path / "none", *_tiny_grid()) == (None, None, {})


@needs_world
def test_b0_manifest_lists_what_the_run_read_and_the_two_noise_readers_agree():
    from shibuya import cli

    res = cli.run(world_dir=str(WORLD_DIR), **SMALL)
    fs = res.run_manifest_fields()["frozen_sources"]
    noise = ("w10_noise_stage_day.npy", "w10_noise_stage_night.npy", "w10_street_points.parquet")
    for name in noise:
        assert fs[f"world:{name}"] == fs[f"perception:{name}"] == WA.file_sha256(WORLD_DIR / name)
    assert fs["world:noise_stage_cells"] == fs["perception:noise_stage_cells"]
    assert fs["world:noise_stage_cells"] == WA.array_sha256(
        res.runner.world.assets.noise_stage_day, res.runner.world.assets.noise_stage_night
    )
    for name in ("w13_weather_days.parquet", "w13_weather_hourly.parquet", "w12_timetables.parquet",
                 "w12_external_nodes.parquet", "w10_street_points.parquet"):
        assert fs[f"process:{name}"] == WA.file_sha256(WORLD_DIR / name)
    assert fs["perception:w13_weather_hourly.parquet"] == WA.file_sha256(WORLD_DIR / "w13_weather_hourly.parquet")
    # 影は開いた日のファイルだけ(既定のランは再生日 1 日)
    shadows = sorted(k for k in fs if k.startswith("process:w9_shadow_"))
    replay = res.run_manifest_fields()["replay_date"]
    assert shadows == [f"process:w9_shadow_{replay}.npy"]
    assert fs[shadows[0]] == WA.file_sha256(WORLD_DIR / f"w9_shadow_{replay}.npy")
    # W14・W15 の凍結文の欄は今のまま(印なし)
    assert {k for k in fs if ":" not in k} >= {"w14_signage.parquet", "w15_cell_static.parquet"}


@needs_world
def test_b0_hashes_stay_out_of_the_final(monkeypatch):
    from shibuya import cli
    from shibuya.engine.processes import environment as ENV
    from shibuya.perception import renderer as REN

    a = cli.run(world_dir=str(WORLD_DIR), **SMALL)
    fake = lambda path: "0" * 64  # noqa: E731
    for mod in (WA, REN, ENV):
        monkeypatch.setattr(mod, "file_sha256", fake)
    b = cli.run(world_dir=str(WORLD_DIR), **SMALL)
    fa, fb = a.run_manifest_fields()["frozen_sources"], b.run_manifest_fields()["frozen_sources"]
    assert fa != fb and set(fa) == set(fb)
    assert a.final_hash == b.final_hash
    assert [c.combined for c in a.checkpoints] == [c.combined for c in b.checkpoints]
    assert a.llm_calls == b.llm_calls


# ================================================================ B1 旧資産の切替口
def _copy_families(dst: Path, families=("W10", "W12", "W13", "W9")) -> Path:
    """今の資産のうち、エンジンが読む族のファイルを ``dst`` に写す(退避先が空でも試験できる)。"""
    dst.mkdir(parents=True, exist_ok=True)
    for fam in families:
        names = WA.PRE10E_FAMILIES[fam] or tuple(p.name for p in WORLD_DIR.glob(WA.SHADOW_GLOB))
        for name in names:
            shutil.copy2(WORLD_DIR / name, dst / name)
    return dst


def test_b1_asset_source_routes_by_family(tmp_path):
    wd = tmp_path / "world"
    wd.mkdir()
    # 切替口を使わない=全部 world_dir
    src = WA.asset_source(wd, None)
    assert src.alt_dir is None and src.manifest() is None
    assert src.path("w10_noise_stage_day.npy") == wd / "w10_noise_stage_day.npy"
    # 無い退避先・空の退避先・族の一部だけ=止める
    with pytest.raises(ValueError, match="無い"):
        WA.asset_source(wd, tmp_path / "nope")
    (tmp_path / "empty").mkdir()
    with pytest.raises(ValueError, match="どれも無い"):
        WA.asset_source(wd, tmp_path / "empty")
    part = tmp_path / "part"
    part.mkdir()
    (part / "w10_noise_stage_day.npy").write_bytes(b"x")
    with pytest.raises(ValueError, match="W10 が欠けている"):
        WA.asset_source(wd, part)
    # 段ごとの写し(W12 だけ)=W12 だけを退避先から読む
    steps = tmp_path / "B3"
    steps.mkdir()
    for name in WA.PRE10E_FAMILIES["W12"]:
        (steps / name).write_bytes(b"x")
    src = WA.asset_source(wd, steps)
    assert src.families == ("W12",)
    assert src.path("w12_timetables.parquet") == steps / "w12_timetables.parquet"
    assert src.path("w13_weather_days.parquet") == wd / "w13_weather_days.parquet"
    assert src.path("w2_cells.parquet") == wd / "w2_cells.parquet"   # 族の外は常に world_dir
    assert src.shadow_dir() == wd
    assert src.manifest() == {"dir": steps.as_posix(), "families": ["W12"]}
    (steps / "w9_shadow_2026-07-13.npy").write_bytes(b"x")
    src = WA.asset_source(wd, steps)
    assert src.families == ("W12", "W9") and src.shadow_dir() == steps
    assert src.path("w9_shadow_2026-07-13.npy") == steps / "w9_shadow_2026-07-13.npy"


@needs_world
def test_b1_the_current_assets_read_from_the_alt_dir_give_the_same_run(tmp_path):
    from shibuya import cli

    alt = _copy_families(tmp_path / "pre10e")
    a = cli.run(world_dir=str(WORLD_DIR), **SMALL)
    b = cli.run(world_dir=str(WORLD_DIR), world_assets_pre10e=str(alt), **SMALL)
    assert a.final_hash == b.final_hash
    assert [c.combined for c in a.checkpoints] == [c.combined for c in b.checkpoints]
    ma, mb = a.run_manifest_fields(), b.run_manifest_fields()
    assert ma["frozen_sources"] == mb["frozen_sources"]   # 同じ中身=同じ指紋
    assert "world_assets_pre10e" not in ma                 # 既定の manifest は欄が増えない
    assert mb["world_assets_pre10e"] == {"dir": alt.as_posix(), "families": ["W10", "W12", "W13", "W9"]}
    assert b.runner.assets.shadow_dir == str(alt)


@needs_world
def test_b1_both_noise_readers_switch_together_and_a_one_sided_read_stops(tmp_path):
    from shibuya import cli
    from shibuya.engine.run import run_day
    from shibuya.world.state import World

    alt = _copy_families(tmp_path / "pre10e", families=("W10",))
    day = np.load(alt / "w10_noise_stage_day.npy")
    np.save(alt / "w10_noise_stage_day.npy", np.full_like(day, 3))   # 昼の地図を全部「段 3」にした旧資産
    base = cli.run(world_dir=str(WORLD_DIR), **SMALL)
    res = cli.run(world_dir=str(WORLD_DIR), world_assets_pre10e=str(alt), **SMALL)
    fs, fb = res.run_manifest_fields()["frozen_sources"], base.run_manifest_fields()["frozen_sources"]
    sha = WA.file_sha256(alt / "w10_noise_stage_day.npy")
    assert fs["world:w10_noise_stage_day.npy"] == fs["perception:w10_noise_stage_day.npy"] == sha
    assert fs["world:noise_stage_cells"] == fs["perception:noise_stage_cells"] != fb["world:noise_stage_cells"]
    wa = res.runner.world.assets
    assert int(wa.noise_stage_day[wa.noise_stage_day > 0].min()) == 3   # 街路のあるセルは全部 段 3
    assert fs["process:w13_weather_days.parquet"] == fb["process:w13_weather_days.parquet"]  # 族の外は今の資産
    assert res.run_manifest_fields()["world_assets_pre10e"]["families"] == ["W10"]
    # 片方だけ旧い地図(world は今の資産で読み、run_day には退避先を渡す)=止める
    world = World.load_or_synthetic(WORLD_DIR, seed=1)
    with pytest.raises(ValueError, match="2 か所"):
        run_day(world=world, world_dir=str(WORLD_DIR), world_assets_pre10e=str(alt), **SMALL)


def test_b1_cli_switch_and_defaults():
    import argparse

    from shibuya.engine.run import add_calendar_args, calendar_kwargs_from_args

    ap = argparse.ArgumentParser()
    add_calendar_args(ap)
    assert "world_assets_pre10e" not in calendar_kwargs_from_args(ap.parse_args([]))
    kw = calendar_kwargs_from_args(ap.parse_args(["--world-assets-pre10e", WA.PRE10E_DEFAULT_DIR]))
    assert kw["world_assets_pre10e"] == "data/world/v2_pre_10e_2026-10-12"
