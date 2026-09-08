"""build.audit の統合テスト(実データ必須・CI では skip)。

**全段階**(W0-W20)を tmp_path へ通しで構築し、W18/W19/W20 のゲートと出力を検める。
W8 を含むので数分かかる想定。
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from shibuya.build import run as build_run
from shibuya.build.geo import common as C
from shibuya.manifest.world_catalog import FROZEN_N_CLASSES, FROZEN_SHA16

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
OSM = DATA_DIR / "realworld" / "osm" / "shibuya_osm_wide_v8.json"
TERRAIN = DATA_DIR / "plateau" / "terrain.npz"
KASYO = DATA_DIR / "realworld" / "road_census_r3" / "kasyo13.csv"

pytestmark = pytest.mark.skipif(
    not (OSM.exists() and TERRAIN.exists() and KASYO.exists()), reason="data/ absent (CI)"
)


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> tuple[Path, dict, float]:
    out = tmp_path_factory.mktemp("world_v2_audit")
    ctx = C.Ctx(data=DATA_DIR, out=out)
    t0 = time.perf_counter()
    build_run.run_all(ctx, list(build_run.ALL_STAGES), verbose=False)
    manifest = build_run.write_build_manifest(ctx)
    return out, manifest, time.perf_counter() - t0


def _header(manifest: dict, stage: str) -> dict:
    for h in manifest["stages"]:
        if h["stage"] == stage:
            return h
    raise AssertionError(f"段階 {stage} がヘッダに無い")


def _gate(manifest: dict, stage: str, name: str) -> dict:
    return _header(manifest, stage)["gates"][name]


def test_stage_order_is_numeric_and_complete(built):
    _out, manifest, _dt = built
    assert manifest["stage_order"] == list(build_run.ALL_STAGES)
    assert manifest["stage_order"][-3:] == ["W18", "W19", "W20"]
    # W8/W9 は W7 と W10 の間(数値順)
    order = manifest["stage_order"]
    assert order.index("W7") < order.index("W8") < order.index("W9") < order.index("W10")


def test_w18_coverage_index(built):
    out, manifest, _dt = built
    assert _gate(manifest, "W18", "catalog_sha16_frozen")["value"] == FROZEN_SHA16
    assert _gate(manifest, "W18", "catalog_n_classes")["value"] == FROZEN_N_CLASSES
    assert _gate(manifest, "W18", "wc6_world_orphans")["value"] == 0

    wc = C.load_json(out / "wc_index.json")
    assert wc["catalog_sha16"] == FROZEN_SHA16
    assert len(wc["per_class"]) == FROZEN_N_CLASSES
    v = wc["vector"]
    for key in ("C", "C_quantified", "Q", "D", "V"):
        assert 0.0 < v[key] <= 1.0 or (key == "V" and v[key] == 0.0)
    assert v["R"] is None  # ランタイム実測
    assert wc["orphans"] == []
    assert isinstance(wc["X"], float)
    # 実装済みは 10 クラス以上(W0-W13 + W8/W9 が埋める)
    impl = [c for c in wc["per_class"] if c["implemented"]]
    assert len(impl) >= 10
    for name in ("建物", "街路(歩行グラフ)", "POI/店舗", "昼夜・日照・影"):
        assert any(c["class"] == name for c in impl), f"{name} が実装済みになっていない"
    # 数量が一致する代表クラス
    by_name = {c["class"]: c for c in wc["per_class"]}
    assert by_name["建物"]["n_sim"] == by_name["建物"]["n_real"] == 7210.0
    assert by_name["街路(歩行グラフ)"]["n_sim"] == 4944.0

    rev = C.load_json(out / "wc_reverse_index.json")
    assert set(rev["class_to_stages"]) == {c["class"] for c in wc["per_class"]}
    assert rev["class_to_stages"]["建物"]


def test_w19_freeze_assets_and_seal(built):
    out, manifest, _dt = built
    assert _gate(manifest, "W19", "data_assets_missing")["value"] == 0
    assert _gate(manifest, "W19", "holdout_not_referenced_in_build_code")["value"] == 0
    frz = C.load_json(out / "w19_freeze.json")
    assert frz["holdout_seal"]["seal_scheme"] == "S"
    names = {lyr["name"] for lyr in frz["holdout_seal"]["layers"]}
    assert names == {"kddi_la", "shibuya_jinryu", "boundary_counts"}
    for lyr in frz["holdout_seal"]["layers"]:
        assert lyr["opened"] is False
        assert len(lyr["member_hash"]) == 64
        assert lyr["sealed_utc"].endswith("Z")
        assert lyr["members"], f"{lyr['name']} のメンバーが空"
    assert frz["data_assets"], "データ資産表が空"
    for a in frz["data_assets"]:
        assert len(a["sha256"]) == 64 and a["bytes"] > 0
        assert not a["path"].startswith("/") and ".." not in a["path"]
    # 資産表に holdout は入らない
    assert not any(
        tok in a["path"] for a in frz["data_assets"]
        for tok in ("kddi_la", "shibuya_jinryu", "boundary_counts")
    )
    # 各段階のダイジェストが並んでいる(W0..W18)
    stages = [s["stage"] for s in frz["stage_digests"]]
    assert stages == [s for s in build_run.ALL_STAGES if int(s[1:]) < 19]


def test_w20_acceptance_pack(built):
    out, manifest, _dt = built
    pack = out / "acceptance"
    for name in (
        "cells.png", "exits.png", "noise_day.png", "visibility.png", "shadow_noon.png",
        "gate_table.md", "summary.json",
    ):
        assert (pack / name).exists(), f"検収パックに {name} が無い"
        assert (pack / name).stat().st_size > 0
    for name in ("cells.png", "exits.png", "noise_day.png", "visibility.png", "shadow_noon.png"):
        assert (pack / name).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

    md = (pack / "gate_table.md").read_text(encoding="utf-8")
    assert "ゲート結果表" in md
    summary = C.load_json(pack / "summary.json")
    assert summary["world_coverage"]["catalog_sha16"] == FROZEN_SHA16
    assert summary["holdout_seal"]["seal_scheme"] == "S"
    assert len(summary["stages"]) == len(build_run.ALL_STAGES) - 1  # W20 自身は含まない
    # 落ちたゲートは隠さない
    failed = {(g["stage"], g["gate"]) for g in summary["gates_failed"]}
    assert ("W9", "shadow_bytes_per_day_le_10mb") in failed
    for stage, name in failed:
        assert f"| {stage} | {name} |" in md


def test_build_manifest_carries_assets_and_seal(built):
    """build_manifest.json が(W19 ヘッダ経由で)資産表と封印を持つ。"""
    _out, manifest, _dt = built
    notes = _header(manifest, "W19")["notes"]
    assert notes["data_assets_count"] > 0
    assert len(notes["holdout_seal"]["layers"]) == 3
    assert all(not lyr["opened"] for lyr in notes["holdout_seal"]["layers"])
    assert len(manifest["build_hash"]) == 64


@pytest.mark.slow
def test_full_rebuild_gives_identical_build_hash(built, tmp_path):
    """D-W20 の再構築テスト T1(W8 込みなので slow)。"""
    _out1, manifest1, _dt = built
    out2 = tmp_path / "rebuild_all"
    ctx = C.Ctx(data=DATA_DIR, out=out2)
    build_run.run_all(ctx, list(build_run.ALL_STAGES), verbose=False)
    manifest2 = build_run.write_build_manifest(ctx)
    assert manifest2["build_hash"] == manifest1["build_hash"]
    for stage in build_run.ALL_STAGES:
        a = C.canonical_json_bytes(_header(manifest1, stage))
        b = C.canonical_json_bytes(_header(manifest2, stage))
        assert a == b, f"{stage} のヘッダが再構築で一致しない"
