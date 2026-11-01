"""10e(版上げ 1 回目)B0 資産の指紋・B1 旧資産の切替口(第330)。

- **B0**: manifest の ``frozen_sources`` に、ランが実際に読んだ騒音の地図(W10 の 3 本)・天気(W13)・時刻表(W12)・
  影(W9・開いた日だけ)の sha256 を、読み手ごとの印(``world:``・``perception:``・``process:``)を付けて足す。
  騒音の地図は 2 か所(``world.assets._noise_stage_per_cell`` と ``perception.renderer._street_aggregate``)で読むので、
  集約後のセル別の段の指紋(``noise_stage_cells``)も両方に出す=2 つが同じ地図を読んだことが記録から分かる。
  final・checkpoint には入らない(manifest だけが動く)。
- **B1**: ``--world-assets-pre10e <dir>``(``run_day(world_assets_pre10e=…)``)で W10・W12・W13・W9 を 1 か所の
  退避先から読む。騒音の 2 つの読み手は同じ口(``world.assets.AssetSource``)を通す。**版上げ 1 回目の直後に消す**。
- 〔改訂(第330・RET)〕B1 の切替口を口ごと消した(ユーザーの答え 1-5)。B1 の 4 件(族の振り分けと止める 3 つ・今の資産を
  退避先から読んだランが既定と同じ・2 つの読み手が同じ地図を読む・CLI)は ACT の commit で通ったことを 10e の記録 §RET に
  書いて消し、「切替口が無い」ことを見る 1 件にした。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from shibuya.world import assets as WA

WORLD_DIR = Path(__file__).resolve().parents[2] / "data" / "world" / "v2"
HAS_WORLD = WA.assets_available(WORLD_DIR) and (WORLD_DIR / "w10_noise_stage_day.npy").is_file()
needs_world = pytest.mark.requires_data("world_v2", "world_v2:w10_noise_stage_day.npy")

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
    # 影は開いた日のファイルだけ(1 日のランは 1 日。legacy では再生日・calendar では暦の日付か近い日)
    shadows = sorted(k for k in fs if k.startswith("process:w9_shadow_"))
    sd = res.run_manifest_fields()["weather"]["days"][0]["shadow_date"]
    assert shadows == [f"process:w9_shadow_{sd}.npy"]
    assert fs[shadows[0]] == WA.file_sha256(WORLD_DIR / f"w9_shadow_{sd}.npy")
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


# ================================================================ B1 旧資産の切替口(〔第330・RET〕消した)
def test_b1_switch_is_gone():
    import argparse
    import inspect

    from shibuya import cli
    from shibuya.engine.run import add_calendar_args, run_day
    from shibuya.perception.renderer import PerceptionAssets

    for gone in ("AssetSource", "asset_source", "PRE10E_FAMILIES", "PRE10E_DEFAULT_DIR"):
        assert not hasattr(WA, gone), gone
    assert "world_assets_pre10e" not in inspect.signature(run_day).parameters
    assert "pre10e" not in inspect.signature(WA.load_assets).parameters
    assert "pre10e" not in inspect.signature(WA.load_process_assets).parameters
    assert "pre10e" not in inspect.signature(PerceptionAssets.load).parameters
    ap = argparse.ArgumentParser()
    add_calendar_args(ap)
    with pytest.raises(SystemExit):
        ap.parse_args(["--world-assets-pre10e", "data/world/v2_pre_10e_2026-10-12"])
    with pytest.raises(TypeError):
        cli.run(n_agents=4, ticks=2, world_dir=None, world_assets_pre10e="x")
