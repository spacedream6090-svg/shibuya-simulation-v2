"""expedient 感度試験の**台帳**(漏れ検出つき)と、構築段階の対照(小データ)。"""

from __future__ import annotations

import json

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from .conftest import real_data, real_estat


@pytest.fixture(scope="module")
def ledger(c8lib):
    return c8lib.load_sensitivity()


# ------------------------------------------------------------------ 台帳と設計書の突合
def test_ledger_validates(sensitivity, ledger):
    """自己検査+**設計書との突合**(漏れがあればここで落ちる)。"""
    assert sensitivity.validate_ledger(ledger) == []


def test_every_design_sensitivity_is_covered(c8lib, ledger):
    """構築仕様書 §2 の『感度: …』14 行が**全部**台帳にあること(漏れ検出の本体)。"""
    gaps = c8lib.ledger_gaps(c8lib.scan_build_spec_sensitivities(), ledger)
    assert gaps["missing"] == []


def test_missing_row_is_detected(c8lib, sensitivity, ledger):
    """1 行落とすと『漏れ』として検出されること(検出器そのものの検査)。"""
    broken = json.loads(json.dumps(ledger))
    broken["rows"] = [r for r in broken["rows"] if r["design_anchor"] != "D-W16"]
    problems = sensitivity.validate_ledger(broken)
    assert any("D-W16" in p and "漏れ" in p for p in problems)


def test_process_ablation_ids_match_source(c8lib, ledger):
    """世界過程の AB-* id は**コードが正典**(台帳が古くなったら落ちる)。"""
    assert set(ledger["process_ablations"]["ids"]) == set(c8lib.scan_engine_ablation_ids())


def test_process_ablation_caveat_is_recorded(ledger):
    """``--ablate AB-PNOTICE-A0`` が salient 過程ごと止める罠を台帳が持っていること。"""
    assert "salient" in ledger["process_ablations"]["caveat"]


def test_runner_names_exist(sensitivity, ledger):
    for r in ledger["rows"]:
        if r.get("runner") is not None:
            assert r["runner"] in sensitivity.RUNNERS


def test_done_rows_have_results(ledger):
    for r in ledger["rows"]:
        if r["status"] == "done":
            assert r["result"], r["id"]
            assert r["result"].get("verdict") in ("not_driving", "needs_run")


def test_required_row_is_marked(ledger):
    """『感度(必須)』は D-W8 だけ=台帳もそう持つこと。"""
    required = {r["design_anchor"] for r in ledger["rows"] if r.get("required")}
    assert required == {"D-W8"}


def test_criterion_is_one_sided(ledger):
    assert "片側" in ledger["criterion_note"]
    assert "駆動しえない" in ledger["criterion_note"]


def test_open_questions_flag_the_gap(ledger):
    """設計書が感度を宣言していない expedient(122−14)が親判断待ちとして残っていること。"""
    assert ledger["build_manifest_expedients"]["count"] == 122
    assert any("122" in q for q in ledger["open_questions"])


def test_ledger_markdown_is_a_valid_table(sensitivity, ledger):
    md = sensitivity.ledger_markdown(ledger)
    body = [ln for ln in md.splitlines() if ln.startswith("|")]
    ncol = body[0].count("|")
    for line in body:
        assert line.replace("\\|", "").count("|") == ncol, line


# ------------------------------------------------------------------ 構築対照(小データ)
def _weather_parquet(path, temps, rh=60.0, wind=1.0, solar=0.5):
    n = len(temps)
    pq.write_table(
        pa.table(
            {
                "temp_c": pa.array(temps, pa.float64()),
                "rh": pa.array([rh] * n, pa.float64()),
                "wind_ms": pa.array([wind] * n, pa.float64()),
                "solar_kw_est": pa.array([solar] * n, pa.float64()),
                "wbgt_est": pa.array([1.0] * n, pa.float64()),
            }
        ),
        path,
    )


def test_w13_temp_plus_small(sensitivity, tmp_path):
    """気温 +1.5 ℃ の対照: 段階が上がった行だけが数えられること。"""
    _weather_parquet(tmp_path / "w13_weather_hourly.parquet", [10.0, 10.0, 40.0, 40.0])
    out = sensitivity.w13_temp_plus(tmp_path)
    assert out["n_hours"] == 4
    assert out["mean_d_wbgt"] > 0.0
    assert sum(out["declared_hist"].values()) == 4
    assert sum(out["control_hist"].values()) == 4
    assert 0 <= out["stage_changed"] <= 4


def test_w13_temp_plus_zero_delta_is_no_op(sensitivity, tmp_path):
    """Δ=0 なら分布は 1 バイトも動かない(対照の健全性)。"""
    _weather_parquet(tmp_path / "w13_weather_hourly.parquet", [20.0, 25.0, 30.0])
    out = sensitivity.w13_temp_plus(tmp_path, delta_c=0.0)
    assert out["stage_changed"] == 0
    assert out["jsd_bits"] == 0.0
    assert out["detected"] is False


def test_w13_temp_plus_skips_missing_rows(sensitivity, tmp_path):
    p = tmp_path / "w13_weather_hourly.parquet"
    pq.write_table(
        pa.table(
            {
                "temp_c": pa.array([20.0, None], pa.float64()),
                "rh": pa.array([60.0, 60.0], pa.float64()),
                "wind_ms": pa.array([1.0, 1.0], pa.float64()),
                "solar_kw_est": pa.array([0.5, 0.5], pa.float64()),
                "wbgt_est": pa.array([1.0, None], pa.float64()),
            }
        ),
        p,
    )
    assert sensitivity.w13_temp_plus(tmp_path)["n_hours"] == 1


def test_w12_hour_uniform_small(sensitivity, tmp_path):
    """全部 8 時に寄った重み vs 一様=最大級の差(JSD が帰無を大きく超える)。"""
    pq.write_table(
        pa.table({"hour": pa.array([8] * 24, pa.int64()), "weight": pa.array([1.0] * 24)}),
        tmp_path / "w12_generation_weights.parquet",
    )
    out = sensitivity.w12_hour_uniform(tmp_path)
    assert out["n_weight_rows"] == 24
    assert out["declared_share"][8] == pytest.approx(1.0)
    assert out["jsd_bits"] > out["null_p95"]
    assert out["detected"] is True


def test_w12_hour_uniform_already_uniform(sensitivity, tmp_path):
    """既に一様なら対照と一致=**駆動しえない**側の答えが出せること。"""
    pq.write_table(
        pa.table(
            {"hour": pa.array(list(range(24)), pa.int64()), "weight": pa.array([1.0] * 24)}
        ),
        tmp_path / "w12_generation_weights.parquet",
    )
    out = sensitivity.w12_hour_uniform(tmp_path)
    assert out["jsd_bits"] == pytest.approx(0.0, abs=1e-12)
    assert out["detected"] is False


def _timetable_parquet(path, minutes, source="equal_interval_expedient"):
    n = len(minutes)
    pq.write_table(
        pa.table(
            {
                "line": pa.array(["JR山手"] * n),
                "operator": pa.array(["JR"] * n),
                "direction": pa.array(["内回り"] * n),
                "calendar": pa.array(["weekday"] * n),
                "departure": pa.array(["-"] * n),
                "departure_min": pa.array(minutes, pa.int64()),
                "source": pa.array([source] * n),
            }
        ),
        path,
    )


def test_w12_jr_phase_shifts_only_expedient_rows(sensitivity, tmp_path):
    """実ダイヤ(``source='real'``)は動かさない。"""
    _timetable_parquet(tmp_path / "w12_timetables.parquet", list(range(0, 1440, 10)), source="real")
    out = sensitivity.w12_jr_phase(tmp_path)
    assert out["n_shifted"] == 0
    assert out["jsd_bits"] == pytest.approx(0.0)
    assert out["detected"] is False


def test_w12_jr_phase_moves_10min_bins(sensitivity, tmp_path):
    """等間隔 15 分の便を半運転間隔(7.5 分)ずらすと 10 分ビンは動く/時別は動かない。

    (10 分間隔の便を 5 分ずらしても 10 分ビンの数は変わらない=ビンと位相が同期する。
    エンジンの tick は 1 分なので、ビンで見えない移動も乗車判断には効く。)
    """
    _timetable_parquet(tmp_path / "w12_timetables.parquet", list(range(0, 1440, 15)))
    out = sensitivity.w12_jr_phase(tmp_path)
    assert out["n_shifted"] == 96
    assert out["median_headway_min"] == pytest.approx(15.0)
    assert out["detected_hour"] is False  # 時別のヒストグラムは変わらない
    assert out["jsd_bits_10min"] > 0.0
    assert out["detected"] is True  # 判定は保守側(10 分で動いたら needs_run)


def test_w12_jr_phase_hour_bins_can_be_blind(sensitivity, tmp_path):
    """10 分間隔を 5 分ずらすとどのビンでも数が変わらない=**測れない**ことの記録。"""
    _timetable_parquet(tmp_path / "w12_timetables.parquet", list(range(0, 1440, 10)))
    out = sensitivity.w12_jr_phase(tmp_path)
    assert out["n_shifted"] == 144
    assert out["jsd_bits"] == pytest.approx(0.0)
    assert out["jsd_bits_10min"] == pytest.approx(0.0)
    assert out["max_abs_delta_trains_per_hour"] == 0.0


# ------------------------------------------------------------------ 実資産(あるときだけ)
@real_data
@real_estat
def test_w16_area_apportionment_real(sensitivity, world_dir, data_dir):
    """床面積按分 vs 面積按分: 人数は保存され、配置は入れ替わる。"""
    out = sensitivity.w16_area_apportionment(world_dir, data_dir)
    assert out["n_declared"] == out["n_control"] == out["n_residents"]
    assert out["unplaced"] == 0
    assert out["n_chome"] == 80
    assert out["jsd_bits"] > out["null_p95"]  # 入力が動く=ラン対照が要る
    assert 0.0 < out["tvd"] < 1.0


@real_data
def test_w13_and_w12_real_assets(sensitivity, world_dir):
    t = sensitivity.w13_temp_plus(world_dir)
    assert t["n_hours"] == 840
    u = sensitivity.w12_hour_uniform(world_dir)
    assert u["n_weight_rows"] > 0
    j = sensitivity.w12_jr_phase(world_dir)
    assert j["n_shifted"] > 0 and j["n_departures"] > j["n_shifted"]


@real_data
def test_run_row_fills_verdict(sensitivity, world_dir, data_dir):
    row = {"id": "X", "runner": "w13_temp_plus"}
    res = sensitivity.run_row(row, world_dir=world_dir, data_dir=data_dir)
    assert res["verdict"] in ("not_driving", "needs_run")
    assert res["measured_at"]
    assert res["seconds"] >= 0.0
