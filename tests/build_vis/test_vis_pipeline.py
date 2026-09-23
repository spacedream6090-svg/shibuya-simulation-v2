"""build.vis の統合テスト(実データ必須・CI では skip)。

W0-W13 を tmp_path へ構築してから W8/W9 を回し、ゲートを**既知の落ち方**と突き合わせる。
落ちるゲート(W9 のバイト予算)は仕様書の点数前提と実装の点数が違うことが原因で、
値を合わせにいかない(点を間引いて予算に収めることはしない)。
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest

from shibuya.build import run as build_run
from shibuya.build.geo import common as C
from shibuya.build.vis import run as vis_run

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
OSM = DATA_DIR / "realworld" / "osm" / "shibuya_osm_wide_v8.json"
TERRAIN = DATA_DIR / "plateau" / "terrain.npz"
KASYO = DATA_DIR / "realworld" / "road_census_r3" / "kasyo13.csv"

pytestmark = pytest.mark.skipif(
    not (OSM.exists() and TERRAIN.exists() and KASYO.exists()), reason="data/ absent (CI)"
)

#: 実データで**現に落ちる**ゲート(理由つき)。
KNOWN_FAILING: dict[tuple[str, str], str] = {
    ("W9", "shadow_bytes_per_day_le_10mb"): (
        "D-W10 の 8.6MB/日 は 239,028点前提。本実装の街路格子は W10 と同じ 356,732点なので"
        "288×44,592B=12.84MB になる。点を間引いて予算に合わせることはしない"
    ),
}

#: §1 W8 のゲート「前計算 ≤5分」。
W8_PRECOMPUTE_BUDGET_S = 300.0
#: 予算書 M10。
M10_BYTES = 512 * 1024 * 1024
#: W8/W9 の前段(可視性・監査レーンを除く全段階)。
# W8 の上流=地理(GEO)と場(FIELD)の段階だけ。可視性(VIS)・静的言語化(LANG・W15 は W8 出力を読む)・
# 母集団(POP)・監査(AUDIT)は W8 の下流なので除く(09-09: W14/W15 登録で明示化)。
_UPSTREAM = [
    s
    for s in build_run.RUN_ORDER
    if s not in build_run.VIS_STAGES
    and s not in build_run.LANG_STAGES
    and s not in build_run.POP_STAGES
    and s not in build_run.SCHED_STAGES
    and s not in build_run.AUDIT_STAGES
]


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> tuple[Path, dict, float]:
    out = tmp_path_factory.mktemp("world_v2_vis")
    ctx = C.Ctx(data=DATA_DIR, out=out)
    build_run.run_all(ctx, _UPSTREAM, verbose=False)
    t0 = time.perf_counter()
    results = vis_run.run_stages(ctx, ["W8", "W9"], verbose=False)
    dt = time.perf_counter() - t0
    return out, {r.stage: r.to_json() for r in results}, dt


def _gate(headers: dict, stage: str, name: str) -> dict:
    return headers[stage]["gates"][name]


def test_only_known_gates_fail(built):
    _out, headers, _dt = built
    failed = {
        (stage, name)
        for stage, h in headers.items()
        for name, g in h["gates"].items()
        if not g["pass"]
    }
    assert failed == set(KNOWN_FAILING), f"落ちたゲートの集合が変わった: {failed}"


def test_w8_precompute_budget_and_m10(built):
    _out, headers, dt = built
    assert dt < W8_PRECOMPUTE_BUDGET_S, f"W8+W9 の前計算が 5 分を超えた: {dt:.1f}s"
    total = _gate(headers, "W8", "output_bytes_le_m10_512mb")["value"]
    assert total <= M10_BYTES


def test_w8_outputs_and_shapes(built):
    out, headers, _dt = built
    for name in ("w8_targets.parquet", "w8_t1.parquet", "w8_t1_cell.parquet", "w8_t2.npy"):
        assert (out / name).exists()
    notes = headers["W8"]["notes"]
    n_pts = notes["viewpoints"]
    pts = C.read_parquet_columns(out / "w10_street_points.parquet", ["x"])
    assert n_pts == len(pts["x"])  # W10 と同じ台を共有している
    assert set(notes["viewpoints_by_band"]) == {"GL", "DECK", "UG"}
    assert notes["targets_by_kind"]["poi"] == 2337
    assert notes["targets_by_kind"]["exit"] == 45
    assert notes["targets_by_kind"]["building"] == 7210

    t1 = C.read_parquet_columns(out / "w8_t1.parquet", ["point_idx", "n_visible", "targets"])
    assert len(t1["point_idx"]) == n_pts
    assert all(len(t) == n for t, n in zip(t1["targets"][:500], t1["n_visible"][:500]))
    assert max(t1["n_visible"]) <= 256  # T1 の上限
    # T1 の行数ゲートは W10 の視点数(入力)を期待値に取り、視点添字が1回ずつ出ることも問う
    rows_gate = _gate(headers, "W8", "t1_rows")
    assert rows_gate["expected"] == len(pts["x"]) and rows_gate["value"] == len(t1["point_idx"])
    assert _gate(headers, "W8", "t1_each_viewpoint_index_once")["value"] is True
    assert sorted(t1["point_idx"]) == list(range(len(pts["x"])))

    t2 = np.load(out / "w8_t2.npy")
    cells = C.read_parquet_columns(out / "w2_cells.parquet", ["place_id"])
    assert t2.shape == (len(cells["place_id"]), len(cells["place_id"]))
    assert t2.dtype == np.float16
    assert np.array_equal(t2, t2.T)
    assert float(t2.max()) <= 1.0 and float(t2.min()) >= 0.0


def test_w8_band_separation_and_reasonable_visibility(built):
    out, headers, _dt = built
    assert _gate(headers, "W8", "band_separation_violations")["value"] == 0
    notes = headers["W8"]["notes"]
    # 街の中の視点が「何も見えない」ばかりだったら、それは遮蔽が壊れている合図
    assert 0.0 < notes["mean_visible_targets_per_viewpoint"] < 256.0
    assert notes["share_viewpoints_zero_targets"] < 0.5
    # UG 視点は地下街の対象しか見えない(層分離)
    targets = C.read_parquet_columns(out / "w8_targets.parquet", ["band"])
    assert "UG" in set(targets["band"])


def test_w9_shadow_planes(built):
    out, headers, _dt = built
    notes = headers["W9"]["notes"]
    date = notes["replay_date"]
    days = C.read_parquet_columns(out / "w13_weather_days.parquet", ["date"])
    assert date == days["date"][0]
    planes = np.load(out / f"w9_shadow_{date}.npy")
    assert planes.shape == (288, (notes["points"] + 7) // 8)
    assert planes.dtype == np.uint8
    # 夜(高度≤0)の面は全影・正午は全影ではない
    assert _gate(headers, "W9", "night_planes_all_shadow")["value"] is True
    noon = np.unpackbits(planes[144])[: notes["points"]]
    assert 0.0 < float(noon.mean()) < 1.0
    assert float(noon.mean()) == pytest.approx(notes["shadow_fraction_noon"], abs=1e-4)
    # UG の点は常に影
    band = np.asarray(C.read_parquet_columns(out / "w10_street_points.parquet", ["band"])["band"])
    assert int(noon[band == "UG"].sum()) == int((band == "UG").sum())
    # 面ごとの太陽高度が W13 の日の出/日の入と整合(昼の面数 > 0)
    planes_tbl = C.read_parquet_columns(out / "w9_shadow_planes.parquet")
    assert len(planes_tbl["plane_idx"]) == 288
    assert max(planes_tbl["solar_elev_deg"]) > 40.0


def test_headers_declare_expedients_and_catalog(built):
    _out, headers, _dt = built
    for stage in ("W8", "W9"):
        h = headers[stage]
        assert h["expedients"], f"{stage} に expedient 宣言が無い"
        assert h["catalog_classes"], f"{stage} にカタログ写像が無い"
        assert h["input_hash"] and h["param_hash"] and h["stage_version"]
        assert h["outputs"]


def test_rebuild_is_byte_identical(built, tmp_path):
    """D-W20 の T1: W8/W9 を作り直しても出力 sha256 が一致する。"""
    out1, headers1, _dt = built
    out2 = tmp_path / "rebuild"
    ctx = C.Ctx(data=DATA_DIR, out=out2)
    build_run.run_all(ctx, _UPSTREAM, verbose=False)
    results = {r.stage: r.to_json() for r in vis_run.run_stages(ctx, ["W8", "W9"], verbose=False)}
    for stage in ("W8", "W9"):
        a = {o["path"]: o["sha256"] for o in headers1[stage]["outputs"]}
        b = {o["path"]: o["sha256"] for o in results[stage]["outputs"]}
        assert a == b, f"{stage} の出力が再構築で一致しない"
        assert headers1[stage]["input_hash"] == results[stage]["input_hash"]
        assert headers1[stage]["param_hash"] == results[stage]["param_hash"]
