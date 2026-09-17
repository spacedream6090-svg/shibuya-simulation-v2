"""build.geo の統合テスト(実データ必須・CI では skip)。

- 全段階を ``tmp_path`` へ構築し、**全ゲートが pass** することを確かめる。
- 2回目の構築で ``build_hash`` とヘッダのバイト列が一致すること(D-W20 の再構築テスト T1)。
- 主要ゲートの値を仕様書の期待値で固定する(453 セル・785 対・1,242 街区・186,741m・
  3,531 マッチ・45 出口・9,872 組織・2,337 POI)。
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pytest

from shibuya.build.geo import STAGES, common as C
from shibuya.build.geo import run as geo_run

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
OSM = DATA_DIR / "realworld" / "osm" / "shibuya_osm_wide_v8.json"

pytestmark = pytest.mark.skipif(not OSM.exists(), reason="data/ absent (CI)")


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> tuple[Path, dict, float]:
    out = tmp_path_factory.mktemp("world_v2")
    ctx = C.Ctx(data=DATA_DIR, out=out)
    t0 = time.perf_counter()
    geo_run.run_stages(ctx, list(STAGES), verbose=False)
    manifest = geo_run.write_build_manifest(ctx)
    return out, manifest, time.perf_counter() - t0


def _gate(manifest: dict, stage: str, name: str):
    for h in manifest["stages"]:
        if h["stage"] == stage:
            return h["gates"][name]
    raise AssertionError(f"段階 {stage} がヘッダに無い")


def test_all_gates_pass(built):
    _out, manifest, _dt = built
    failed = [
        (h["stage"], k)
        for h in manifest["stages"]
        for k, v in h["gates"].items()
        if not v["pass"]
    ]
    assert failed == []


def test_stage_order_is_w_order(built):
    _out, manifest, _dt = built
    assert manifest["stage_order"] == list(STAGES)


def test_spec_numbers(built):
    _out, manifest, _dt = built
    assert _gate(manifest, "W1", "n_nodes")["value"] == 3499
    assert _gate(manifest, "W1", "n_edges")["value"] == 4944
    assert _gate(manifest, "W1", "total_edge_length_m")["value"] == 186741.0
    assert _gate(manifest, "W1", "components_after_pendant_prune")["value"] == 1
    assert _gate(manifest, "W2", "n_cells_gl")["value"] == 453
    assert _gate(manifest, "W2", "cell_4neighbour_pairs_gl")["value"] == 785
    assert _gate(manifest, "W2", "block_euler_count")["value"] == 1242
    assert _gate(manifest, "W2", "block_to_cell_surjective")["value"] is True
    assert _gate(manifest, "W3", "cell_matrix_symmetric")["value"] == 0
    assert _gate(manifest, "W3", "triangle_violations")["value"] == 0
    assert _gate(manifest, "W4", "plateau_matched")["value"] == 3531
    assert _gate(manifest, "W4", "plateau_h_median_m")["value"] == 14.3
    assert _gate(manifest, "W4", "plateau_h_max_m")["value"] == 231.0
    assert _gate(manifest, "W5", "station_exits")["value"] == 45
    # 出口**自身**の格子セルが W2 のセル集合にあること(最寄りノードのセルではない)
    assert _gate(manifest, "W5", "station_exits_in_banded_cell")["value"] == 45
    assert _gate(manifest, "W5", "station_exit_own_grid_cell_missing")["value"] == 0
    assert _gate(manifest, "W11", "exit_own_grid_cell_missing")["value"] == 0
    assert _gate(manifest, "W6", "poi_total")["value"] == 2337
    assert _gate(manifest, "W6", "orgs_total")["value"] == 9872
    assert _gate(manifest, "W6", "poi_building_binding_rate")["value"] == 0.688
    assert _gate(manifest, "W11", "station_exits")["value"] == 45
    assert _gate(manifest, "W11", "floorguide_connections")["value"] == 22


def test_w6_subcat_is_rebuilt_from_raw_osm_tags(built):
    """W6 subcat 改訂(2026-09-17)を実データで固定する。

    - 生タグで決めた subcat が v8 の凍結値と食い違う件数は 0(規則の移植が正しい)。
    - ``PLACE_PARK`` へ写る POI が **0 件ではなくなった**(欠陥の本体)。
    - subcat が付いた POI は 255 → 393 件。
    """
    _out, manifest, _dt = built
    assert _gate(manifest, "W6", "poi_subcat_tag_vs_frozen_mismatch")["value"] == 0
    assert _gate(manifest, "W6", "poi_subcat_topcat_conflict")["value"] == 0
    assert _gate(manifest, "W6", "poi_catsub_pairs_in_closure")["value"] is True
    assert _gate(manifest, "W6", "poi_subcat_park")["value"] == 27
    assert _gate(manifest, "W6", "poi_subcat_total")["value"] == 393
    # 一次(生タグ)が多数派で、名前一致(expedient)は少数にとどまる。
    notes = next(h for h in manifest["stages"] if h["stage"] == "W6")["notes"]
    src = notes["poi_subcat_source_counts"]
    assert src["osm_tag"] == 274 and src["frozen"] == 98 and src["name"] == 21
    assert notes["poi_raw_tags_matched"] == 1889
    # cat は 1 件も動かない(語彙 13 種・件数も改訂前と同じ)。
    assert notes["poi_cat_counts"] == {
        "attraction": 12,
        "cinema": 7,
        "education": 1,
        "food": 823,
        "hall": 18,
        "hotel": 89,
        "landmark": 56,
        "leisure": 42,
        "nightlife": 259,
        "office": 124,
        "school": 71,
        "service": 114,
        "shop": 721,
    }
    # 答申 §5-2 が「名前でしか引けない」と書いた 3 種が subcat で引ける。
    counts = notes["poi_subcat_counts"]
    assert counts["books"] == 10
    assert counts["musical_instrument"] == 8
    assert counts["library"] == 1


def test_outputs_exist_and_hashes_match(built):
    out, manifest, _dt = built
    for h in manifest["stages"]:
        for o in h["outputs"]:
            path = out / o["path"]
            assert path.exists(), o["path"]
            assert path.stat().st_size == o["bytes"]
            assert C.sha256_file(path) == o["sha256"]


def test_next_hop_matrix_shape_and_dtype(built):
    out, _manifest, _dt = built
    arr = np.load(out / "w3_next_hop.npy", mmap_mode="r")
    assert arr.dtype == np.int32
    assert arr.shape == (3499, 3499)
    cell = np.load(out / "w3_cell_dist.npy")
    assert cell.dtype == np.uint16
    assert cell.shape[0] == cell.shape[1]
    assert np.array_equal(cell, cell.T)
    assert int(np.diagonal(cell).max()) == 0


def test_catalog_classes_declared(built):
    _out, manifest, _dt = built
    declared = {c for h in manifest["stages"] for c in h["catalog_classes"]}
    assert {"建物", "街路(歩行グラフ)", "街区", "セル(場所100m+層)", "POI/店舗", "駅・出口"} <= declared


def test_rebuild_is_reproducible(built, tmp_path):
    out1, manifest1, _dt = built
    ctx = C.Ctx(data=DATA_DIR, out=tmp_path / "again")
    geo_run.run_stages(ctx, list(STAGES), verbose=False)
    manifest2 = geo_run.write_build_manifest(ctx)
    assert manifest2["build_hash"] == manifest1["build_hash"]
    # ヘッダもバイト一致(時刻等の非決定値を持たない)
    for st in STAGES:
        a = (out1 / f"{st}.header.json").read_bytes()
        b = (ctx.out / f"{st}.header.json").read_bytes()
        assert a == b, st
    assert (
        (out1 / geo_run.MANIFEST_NAME).read_bytes()
        == (ctx.out / geo_run.MANIFEST_NAME).read_bytes()
    )


def test_runtime_budget(built):
    _out, _manifest, dt = built
    # 統合テストの目安(numba のコンパイル込みでも余裕がある値)
    assert dt < 180.0


def test_cli_partial_stage(tmp_path):
    rc = geo_run.main(
        ["--out", str(tmp_path / "part"), "--data", str(DATA_DIR), "--stage", "W0", "--quiet"]
    )
    assert rc == 0
    manifest = json.loads((tmp_path / "part" / geo_run.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest["stage_order"] == ["W0"]
    crs = json.loads((tmp_path / "part" / "world_crs.json").read_text(encoding="utf-8"))
    assert crs["origin_latlon"] == [35.6595, 139.70062]
    assert crs["ground0_m"] == 15.18
