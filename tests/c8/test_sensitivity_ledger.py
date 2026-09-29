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
    """設計書が感度を宣言していない expedient が親判断待ちとして残っていること。

    第307(Q141): 09-09 の 122 行 → 現行の build_manifest の 121 行(段の改版 W6 +1・W7 +5・W10 +1・W17 −8)。
    旧注記は ``note_2026_09_09`` に残す。
    """
    be = ledger["build_manifest_expedients"]
    assert be["count"] == 121 == ledger["build_manifest_judgment"]["count"]
    assert "W6 +1・W7 +5・W10 +1・W17 −8" in be["note"] and "122 行" in be["note_2026_09_09"]
    assert any("121" in q for q in ledger["open_questions"])


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


# ------------------------------------------------------------------ D-44 (a) の一括判定(第306)
def test_manifest_judgment_block_is_consistent(sensitivity, ledger):
    """build_manifest の expedient 全行の判定列(3 値+既存の台帳行)が行・集計・規則の文言と合うこと。"""
    j = ledger["build_manifest_judgment"]
    assert j["count"] == len(j["rows"]) == 121
    assert j["covered"] + j["judged"] == j["count"]
    assert set(j["tally"]) == set(sensitivity.MANIFEST_VERDICTS)
    assert j["tally"] == {v: sum(r["verdict"] == v for r in j["rows"]) for v in sensitivity.MANIFEST_VERDICTS}
    ids = {r["id"] for r in ledger["rows"]}
    for r in j["rows"]:
        assert (r["verdict"] == "covered") == (r["covered_by"] is not None), r["key"]
        if r["covered_by"] is not None:
            assert r["covered_by"] in ids
        if r["verdict"] in ("not_driving", "needs_run"):
            assert r["input_jsd"] is not None and r["null_p95"] is not None
        if r["verdict"] == "undetermined":
            assert r["input_jsd"] is None
    assert "片側" in j["rule_note"] and "駆動しえない" in j["rule_note"]
    assert "f≈1" in j["rule_note"] and "第200" in j["rule_note"]  # 検出可能効果量の床
    # 既存の 19 行・過程の id は触らない(判定列は別の鍵)
    assert len(ledger["rows"]) == 19 and ledger["build_manifest_expedients"]["count"] == 121


def test_manifest_judgment_validation_catches_bad_rows(sensitivity, ledger):
    broken = json.loads(json.dumps(ledger))
    broken["build_manifest_judgment"]["rows"][0]["verdict"] = "maybe"
    assert any("verdict" in p for p in sensitivity.validate_ledger(broken))
    broken = json.loads(json.dumps(ledger))
    broken["build_manifest_judgment"]["tally"]["undetermined"] += 1
    assert any("tally" in p for p in sensitivity.validate_ledger(broken))


def test_manifest_judgment_markdown_has_the_rule_and_the_table(sensitivity, ledger):
    md = sensitivity.ledger_markdown(ledger)
    assert "D-44 (a) build_manifest の expedient 121 行の一括判定" in md
    assert "検出可能効果量の床" in md
    assert md.count("判定不能(JSD 無し)") == ledger["build_manifest_judgment"]["tally"]["undetermined"]


@real_data
def test_manifest_judgment_matches_the_live_manifest(c8lib, sensitivity, ledger, world_dir):
    """台帳の判定列は data/world/v2/build_manifest.json から作り直しても同じ(既存の台帳行の書き出しは 1 行ずつに当たる)。"""
    live = sensitivity.build_manifest_verdicts(c8lib.load_json(world_dir / "build_manifest.json"), ledger)
    # 第307/第308: 判定不能の行に足した依存グラフの列(engine_reads*)と 3 分類(triage)は (a) の判定列の比較からは外す
    stored = [{k: v for k, v in r.items() if not k.startswith("engine_reads") and k != "triage"}
              for r in ledger["build_manifest_judgment"]["rows"]]
    assert live["rows"] == stored
    assert live["manifest_build_hash"] == ledger["build_manifest_judgment"]["manifest_build_hash"]
    for stage, prefix, rid in sensitivity.COVERED_EXPEDIENTS:
        hits = [r for r in live["rows"] if r["stage"] == stage and r["expedient"].startswith(prefix)]
        assert len(hits) == 1 and hits[0]["covered_by"] == rid, (stage, prefix)


# ------------------------------------------------------------------ D-44 (c) 依存グラフ(第307)
def test_read_graph_column_is_consistent(sensitivity, ledger):
    """判定不能の行だけに 3 値(読む/読まない/不明)・集計・読まない行の一覧が合う。既存の判定列は変えない。"""
    j = ledger["build_manifest_judgment"]
    rg = j["read_graph"]
    und = [r for r in j["rows"] if r["verdict"] == "undetermined"]
    assert all(r.get("engine_reads") in sensitivity.READ_VERDICTS for r in und)
    assert all(r.get("engine_reads") is None for r in j["rows"] if r["verdict"] != "undetermined")
    assert sum(rg["tally"].values()) == len(und) == j["tally"]["undetermined"]
    assert rg["tally"] == {v: sum(r.get("engine_reads") == v for r in und) for v in sensitivity.READ_VERDICTS}
    assert rg["n_direct"] + rg["n_transitive"] == rg["tally"]["reads"]
    assert rg["not_read_rows"] == [r["key"] for r in und if r["engine_reads"] == "not_read"]
    # 「読まない」は検査・画像の段(W18〜W20)に限る=推測で読まないにしない
    assert all(k.split("#")[0] in sensitivity.AUDIT_STAGES for k in rg["not_read_rows"])
    for st, si in rg["stages"].items():
        if si["verdict"] == "reads":
            assert si["engine_sites"] or si["reach"].startswith("transitive:")
        if si["verdict"] == "not_read":
            assert not si["engine_sites"] and all(c in sensitivity.AUDIT_STAGES for c in si["consumers"])
    assert "推測で読まないにしない" in rg["rule_note"]
    assert not sensitivity.validate_ledger(ledger)


def test_read_graph_validation_catches_bad_rows(sensitivity, ledger):
    broken = json.loads(json.dumps(ledger))
    row = next(r for r in broken["build_manifest_judgment"]["rows"] if r["verdict"] == "undetermined")
    row["engine_reads"] = "maybe"
    assert any("engine_reads" in p for p in sensitivity.validate_ledger(broken))


def test_code_strings_skip_docstrings(sensitivity, tmp_path):
    """読み口は**コードの**文字列だけ(docstring・式文の文字列は数えない)。"""
    f = tmp_path / "m.py"
    f.write_text('''"""w99_doc.parquet は docstring"""
X = "w99_code.parquet"


def g():
    """w99_fn.parquet"""
    "w99_expr.parquet"
    return f"w99_shadow_{1}.npy"
''', encoding="utf-8")
    vals = [v for _ln, v in sensitivity._code_strings(f)]
    assert "w99_code.parquet" in vals and any(v.startswith("w99_shadow_") for v in vals)
    assert not any("doc" in v or "fn" in v or "expr" in v for v in vals)
    assert sensitivity._output_token("w9_shadow_2026-07-28.npy") == "w9_shadow_"
    assert sensitivity._output_token("acceptance/cells.png") == "cells.png"


def test_read_graph_matches_the_source(c8lib, sensitivity, ledger, world_dir):
    """台帳の依存グラフはいまの src から作り直しても同じ(実データの manifest があるとき)。"""
    mp = world_dir / "build_manifest.json"
    if not mp.exists():
        pytest.skip("実世界資産 data/world/v2 が無い")
    g = sensitivity.engine_read_graph(c8lib.load_json(mp))
    stored = ledger["build_manifest_judgment"]["read_graph"]["stages"]
    for st, si in g["stages"].items():
        assert si["verdict"] == stored[st]["verdict"], st
        assert si["engine_sites"] == stored[st]["engine_sites"], st
        assert si["consumers"] == stored[st]["consumers"], st


# ------------------------------------------------------------------ Q146 読む行の 3 分類(第308)
def test_triage_column_is_consistent(c8lib, sensitivity, ledger):
    """エンジンが読む行だけに 3 分類(i/ii/iii)・対照の候補・費用の見込み。集計と表(未リサーチの明記)が合う。"""
    j = ledger["build_manifest_judgment"]
    ts = j["triage_summary"]
    reads = [r for r in j["rows"] if r.get("engine_reads") == "reads"]
    assert ts["n_reads_rows"] == len(reads) == 96
    assert all(r["triage"]["class"] in sensitivity.TRIAGE_CLASSES and r["triage"]["control"] for r in reads)
    assert all("triage" not in r for r in j["rows"] if r.get("engine_reads") != "reads")
    assert ts["tally"] == {c: sum(r["triage"]["class"] == c for r in reads) for c in sensitivity.TRIAGE_CLASSES}
    assert sum(ts["tally"].values()) == 96
    # (i) だけが費用の見込み(秒)を持つ・合計が合う
    for r in reads:
        has_cost = r["triage"]["cost_seconds_estimate"] is not None
        assert has_cost == (r["triage"]["class"] == "i"), r["key"]
    assert ts["i_cost_seconds_sum_one_at_a_time"] == sum(
        r["triage"]["cost_seconds_estimate"] for r in reads if r["triage"]["class"] == "i")
    assert "未リサーチ" in ts["note"] and "自前" in ts["note"]
    # 表(tools/c8/expedient_triage_v1.json)は読む行とちょうど同じ鍵
    table = c8lib.load_json(sensitivity.TRIAGE_PATH)
    assert set(table["rows"]) == {r["key"] for r in reads}
    assert not sensitivity.validate_ledger(ledger)


def test_triage_validation_catches_bad_rows(sensitivity, ledger):
    broken = json.loads(json.dumps(ledger))
    row = next(r for r in broken["build_manifest_judgment"]["rows"] if r.get("triage"))
    row["triage"]["class"] = "iv"
    assert any("triage" in p for p in sensitivity.validate_ledger(broken))
