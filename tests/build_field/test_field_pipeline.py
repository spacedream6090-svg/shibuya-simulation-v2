"""build.field の統合テスト(実データ必須・CI では skip)。

- 地理レーン込みで**全段階**を ``tmp_path`` へ構築する(``shibuya.build.run``)。
- ゲートの合否を**既知の落ち方**と突き合わせる(落ちるゲートは仕様書の空欄・入力欠落が
  原因であり、値を合わせにいかない=調整禁止。理由は各ヘッダの notes に書いてある)。
- 2回目の構築で ``build_hash`` とヘッダのバイト列が一致すること(D-W20 の再構築テスト T1)。
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from shibuya.build import run as build_run
from shibuya.build.geo import common as C

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
OSM = DATA_DIR / "realworld" / "osm" / "shibuya_osm_wide_v8.json"
KASYO = DATA_DIR / "realworld" / "road_census_r3" / "kasyo13.csv"

pytestmark = pytest.mark.skipif(
    not (OSM.exists() and KASYO.exists()), reason="data/ absent (CI)"
)

#: 実データで**現に落ちる**ゲート(理由つき)。増減したら気づけるように固定する。
KNOWN_FAILING_GATES: dict[tuple[str, str], str] = {
    ("W10", "primary_secondary_sections_matched"): (
        "w1_edges/OSM v8 に道路名が無く kasyo13.csv に座標が無い=対応表を作れない"
    ),
    ("W10", "calibration_max_abs_residual_db"): (
        "遮音壁を見ない(ΔL=0)ため高速3号の点が過大・路線中央値が点の実区間と一致しない"
    ),
    # ("W13", "days_with_missing_hours") は 2026-09-08 に etrn 時別値の補完で解消(親レーン)。
    ("W9", "shadow_bytes_per_day_le_10mb"): (
        "D-W10 の 8.6MB/日 は 239,028点前提。街路格子は W10 と同じ 356,732点なので"
        "288面×44,592B=12.84MB。点を間引いて予算に合わせることはしない(可視性レーン)"
    ),
}


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> tuple[Path, dict, float]:
    out = tmp_path_factory.mktemp("world_v2_field")
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


def test_all_stages_present_in_w_order(built):
    _out, manifest, _dt = built
    assert manifest["stage_order"] == list(build_run.ALL_STAGES)
    assert manifest["schema"] == build_run.MANIFEST_SCHEMA


def test_only_known_gates_fail(built):
    _out, manifest, _dt = built
    failed = {
        (h["stage"], k)
        for h in manifest["stages"]
        for k, v in h["gates"].items()
        if not v["pass"]
    }
    assert failed == set(KNOWN_FAILING_GATES), f"落ちたゲートの集合が変わった: {failed}"


def test_build_is_fast_enough(built):
    _out, _manifest, dt = built
    assert dt < 300.0, f"通し構築が 5 分を超えた: {dt:.1f}s"


def test_w7_plan_spec(built):
    out, manifest, _dt = built
    assert (out / "w7_plan_spec.parquet").exists()
    rows_gate = _gate(manifest, "W7", "plan_spec_rows")
    assert rows_gate["value"] == 2337 and rows_gate["expected"] == 2337  # D-W7 の POI 数
    assert _gate(manifest, "W7", "category_defaults_cover_all_catsub")["value"] == 0
    # 適用後は必ず 0(不変条件)・適用前は報告のみ(法規の窓に食い込んでいた区間数)
    assert _gate(manifest, "W7", "intervals_over_law_cap_after_apply")["value"] == 0
    before = _gate(manifest, "W7", "intervals_over_law_cap_before_apply")
    assert before["expected"] is None and before["value"] > 0
    # 切り詰めの内訳を開店側/閉店側の**両方**で数えている(D-W8 の営業不可時間欄)。
    # 現データでは開店側 0(ぱちんこ/ゲームセンターの既定開店 10:00 が窓の明けと同時刻・
    # OSM 実値にも窓へ食い込む開店が無い)・閉店側 17。開店側の規則そのものは単体テスト
    # (test_law_cap_clips_opening_side_pachinko ほか)で検査する。
    n_open = _gate(manifest, "W7", "law_cap_truncated_open_side")["value"]
    n_close = _gate(manifest, "W7", "law_cap_truncated_close_side")["value"]
    n_any = _gate(manifest, "W7", "law_cap_truncated")["value"]
    assert n_close > 0
    assert max(n_open, n_close) <= n_any <= n_open + n_close
    notes7 = _header(manifest, "W7")["notes"]
    assert notes7["law_cap_truncated_poi_open_side"] == n_open
    assert notes7["law_cap_truncated_poi_close_side"] == n_close
    # 窓に食い込んでいた区間は、開店側/閉店側/消滅/分割の**どれか**で必ず処理されている
    handled = (
        notes7["law_cap_intervals_opening_moved"]
        + notes7["law_cap_intervals_closing_moved"]
        + notes7["law_cap_intervals_dropped"]
        + notes7["law_cap_intervals_split"]
    )
    assert handled >= before["value"] > 0
    assert _gate(manifest, "W7", "osm_opening_hours_candidates")["value"] == 565
    notes = _header(manifest, "W7")["notes"]
    assert notes["osm_parse_rate"] >= 0.90
    srcs = notes["src_counts"]
    assert set(srcs) <= {"osm_opening_hours", "chain_default", "category_default"}
    assert sum(srcs.values()) == 2337
    cols = C.read_parquet_columns(out / "w7_plan_spec.parquet")
    for name in (
        "id",
        "poi_id",
        "kind",
        "content",
        "valid_from",
        "valid_to",
        "version",
        "revising_authority",
        "norm_kind",
        "violability",
        "announcement_scope",
        "compliance_obs_field",
        "src",
        "law_cap_applied",
        "law_cap_rule",
    ):
        assert name in cols, f"PlanSpec 列が無い: {name}"
    # content は 7要素の週表
    assert all(len(json.loads(c)) == 7 for c in cols["content"][:50])


def test_w10_noise(built):
    out, manifest, _dt = built
    for name in (
        "w10_street_points.parquet",
        "w10_noise_day.npy",
        "w10_noise_night.npy",
        "w10_noise_stage_day.npy",
        "w10_noise_stage_night.npy",
    ):
        assert (out / name).exists()
    n = _gate(manifest, "W10", "street_points")["value"]
    assert n > 100_000
    assert _gate(manifest, "W10", "noise_arrays_len")["value"] == n
    assert _gate(manifest, "W10", "points_with_at_least_one_source")["value"] == n
    calib = _header(manifest, "W10")["notes"]["calibration_rows"]
    assert len(calib) == 7
    ok = [r for r in calib if r["status"] == "OK"]
    assert len(ok) == 6  # 区道887号はセンサス対象外
    # 評価できた点は**全て**残差がヘッダに載っていること(隠さない)
    for row in ok:
        assert row["residual_day_db"] is not None, f"No.{row['no']} の昼残差が空"
        assert row["residual_night_db"] is not None, f"No.{row['no']} の夜残差が空"
        assert row["model_day_db"] is not None and row["measured_day_db"] is not None
        assert row["residual_day_db"] == pytest.approx(
            row["model_day_db"] - row["measured_day_db"], abs=0.05
        )
    for row in calib:
        if row["status"] != "OK":
            assert row["status"].startswith("NOT_EVALUABLE")
            assert row["residual_day_db"] is None and row["residual_night_db"] is None
    # ゲートの値=評価できた点の残差の最大絶対値(ヘッダの表と突き合う)
    worst = max(
        max(abs(r["residual_day_db"]), abs(r["residual_night_db"])) for r in ok
    )
    assert _gate(manifest, "W10", "calibration_max_abs_residual_db")["value"] == pytest.approx(
        round(worst, 1)
    )
    assert _gate(manifest, "W10", "calibration_points_evaluable")["value"] == len(ok)
    # 渋谷区の一般道3点(No.78/79/80)は残差 ±3 dB 以内であること
    shibuya = [r for r in ok if r["no"] in ("78", "79", "80")]
    assert len(shibuya) == 3
    for row in shibuya:
        assert abs(row["residual_day_db"]) <= 3.0
        assert abs(row["residual_night_db"]) <= 3.0


@pytest.mark.xfail(
    reason="W10 区間突合=ユーザー判断待ち(PENDING)", strict=True
)
def test_w10_calibration_all_seven_points_within_3db(built):
    """D-W11 の完了条件: **R5 の7点すべて**で残差 ≤3 dB(宣言値)。

    現状で落ちる理由は2つ: (a) No.82 区道887号は道路交通センサスの対象外で評価できない、
    (b) No.61(渋谷経堂線)・No.75(高速3号)・No.81(角筈和泉線)が超過する
    (遮音壁 ΔL=0 と路線中央値の当てはめ)。区間突合(手動対応表)を作るかはユーザー判断待ち
    なので、要件を**テストの中に見えるように**置いて xfail にする(隠さない)。
    """
    _out, manifest, _dt = built
    calib = _header(manifest, "W10")["notes"]["calibration_rows"]
    assert len(calib) == 7
    for row in calib:
        assert row["residual_day_db"] is not None, f"No.{row['no']} が評価不能"
        assert abs(row["residual_day_db"]) <= 3.0, f"No.{row['no']} 昼"
        assert abs(row["residual_night_db"]) <= 3.0, f"No.{row['no']} 夜"


def test_w12_external_nodes(built):
    out, manifest, _dt = built
    assert _gate(manifest, "W12", "external_nodes")["value"] == 10
    assert _gate(manifest, "W12", "every_node_has_cell")["value"] == 1
    assert _gate(manifest, "W12", "generation_weights_sum_to_1")["pass"]
    assert _gate(manifest, "W12", "metro_timetable_rows")["value"] > 0
    nodes = C.read_parquet_columns(out / "w12_external_nodes.parquet")
    assert all(c >= 1 for c in nodes["n_attached_cells"])
    tt = C.read_parquet_columns(out / "w12_timetables.parquet")
    assert set(tt["source"]) == {"real", "equal_interval_expedient"}
    assert set(tt["calendar"]) == {"Weekday", "SaturdayHoliday"}
    weights = C.read_parquet_columns(out / "w12_generation_weights.parquet")
    assert abs(sum(weights["weight"]) - 1.0) < 1e-9
    header = _header(manifest, "W12")
    assert "用途=W16/W17生成入力・較正・検証のみ(D-W14)" in header["notes"]["generation_weights_usage"]
    # 土休のオフピーク比は**土休ダイヤ自身**から導く(平日の値を借りない)
    ratios = header["notes"]["offpeak_ratio_by_calendar"]
    assert ratios["SaturdayHoliday"] != ratios["Weekday"]
    assert header["notes"]["metro_peak_am_trains_holiday"] > 0
    assert header["notes"]["pm_peak_assumed_equal_to_am"] is True
    # 等間隔ダイヤの本数が曜日種別で実際に変わる(比の分岐が効いている)
    exp_rows = [
        (c, d)
        for c, d, src in zip(tt["calendar"], tt["departure_min"], tt["source"])
        if src == "equal_interval_expedient"
    ]
    n_weekday = sum(1 for c, _d in exp_rows if c == "Weekday")
    n_holiday = sum(1 for c, _d in exp_rows if c == "SaturdayHoliday")
    assert n_weekday > 0 and n_holiday > 0 and n_weekday != n_holiday
    # 初終発の妥当域(04:30-01:30)
    assert 270 <= min(tt["departure_min"]) <= 330
    assert 1410 <= max(tt["departure_min"]) <= 1530


def test_w13_weather(built):
    out, manifest, _dt = built
    assert _gate(manifest, "W13", "weather_days")["value"] == 35
    days = C.read_parquet_columns(out / "w13_weather_days.parquet")
    assert len(days["date"]) == 35
    assert set(days["weekday_kind"]) == {"平日", "土休"}
    assert "2026-08-11" in days["date"]
    idx = days["date"].index("2026-08-11")
    assert days["weekday_kind"][idx] == "土休" and days["holiday_name"][idx] == "山の日"
    hourly = C.read_parquet_columns(out / "w13_weather_hourly.parquet")
    assert set(hourly["daylight"]) <= {"夜明け前", "日中", "日没後"}
    assert set(hourly["weather"]) <= {"晴", "薄曇", "曇", "小雨", "雨"}
    header = _header(manifest, "W13")
    assert header["notes"]["candidate_days"] == 35
    assert "未取得" in header["notes"]["candidate_set_note"]


def test_headers_declare_expedients_and_catalog(built):
    _out, manifest, _dt = built
    for stage in ("W7", "W10", "W12", "W13"):
        h = _header(manifest, stage)
        assert h["expedients"], f"{stage} に expedient 宣言が無い"
        assert h["catalog_classes"], f"{stage} にカタログ写像が無い"
        assert h["input_hash"] and h["param_hash"] and h["stage_version"]
        assert h["outputs"], f"{stage} に出力が無い"


def test_rebuild_is_byte_identical(built, tmp_path):
    out1, manifest1, _dt = built
    out2 = tmp_path / "rebuild"
    ctx = C.Ctx(data=DATA_DIR, out=out2)
    build_run.run_all(ctx, list(build_run.ALL_STAGES), verbose=False)
    manifest2 = build_run.write_build_manifest(ctx)
    assert manifest2["build_hash"] == manifest1["build_hash"]
    for stage in build_run.ALL_STAGES:
        a = (out1 / f"{stage}.header.json").read_bytes()
        b = (out2 / f"{stage}.header.json").read_bytes()
        assert a == b, f"{stage} のヘッダが再構築で一致しない"
    assert (out1 / build_run.MANIFEST_NAME).read_bytes() == (
        out2 / build_run.MANIFEST_NAME
    ).read_bytes()
