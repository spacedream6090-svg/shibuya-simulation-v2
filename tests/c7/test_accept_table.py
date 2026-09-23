# -*- coding: utf-8 -*-
"""C7 受入表(``c7_accept.py``)とラン要約の読み取りの検査。"""

from __future__ import annotations

import json

import pytest

#: 実ランの ``RunResult.summary()`` から採った本物の書式(200体×60tick・mock)。
SUMMARY = """[run] n=400000 cells=520 seed=1 ticks=1440 world=data/world/v2
  壁時計 61200.00s (W2 上限 600s) / 移動+密度 3.210 ms/tick (P2 上限 5 ms)
  LLM呼 3,912,004 = 9.78 呼/体/日 (L4 制御目標 10)
  書式エラー率 実効 0.031 / 厳密 0.062 (受入 ≤0.10) ・別名 0.010 ・位置読み 0.002 ・辞書写像 0.001
  保存則 Σmoney 1,427,163 + Σrevenue 900 + Σ運賃 120 = 1,428,183 (初期 1,428,183) OK / 最小在庫 0
  checkpoint 12 点 最終 043a630f49a9af30…
  内訳[ms/tick] phase_a 0.08 / detect 1.89 / llm 0.31 / 合計 42.50
  movement 壁 3.210 / CPU 3.100 ms/tick (P2 上限 5) ・待ち割合 0.03
  世界過程 台帳 1a5fcb8ce4a7e24f… 憲法5 OK / 再生日 2026-07-28 / 乗車 12 降車 12 待ち行列 3 乗り残し 0(0.0000) / ActualLog 44 行 遵守率 0.912
  C4後半: 補充 10 / 納品 3 / 宅配 2 / バス到着 5 / ホテル泊 1 / 顕著行為 4(気づき 9・出動 1) / 廃棄 12.500 t/日 (band 9.0-17.0) OK
  日次センサス(§2.4・締めた day=0): 残差 12 / 貨幣供給 1,000 / faucet 5 / sink 3 / 棚卸差異 0 / 廃棄 900g / ゲート PASS
  診断 deferred: 397
  診断 promoted: 12
  診断 degraded: 83
  診断 suppressed: 1
  診断 parse_error_rate: 0.0310 / undefined_action_count: 4 / tape_miss_count: 0 / conversation_sessions: 25
"""

TIME_V = """\tCommand being timed: "python -m shibuya.engine.run"
\tElapsed (wall clock) time (h:mm:ss or m:ss): 17:00:00
\tMaximum resident set size (kbytes): 18874368
"""


def test_parse_run_summary(c7lib):
    got = c7lib.parse_run_summary(SUMMARY)
    assert got["n_agents"] == 400_000
    assert got["n_cells"] == 520
    assert got["ticks"] == 1440
    assert got["wall_seconds"] == pytest.approx(61200.0)
    assert got["movement_ms_per_tick"] == pytest.approx(3.21)
    assert got["llm_calls"] == 3_912_004
    assert got["calls_per_agent"] == pytest.approx(9.78)
    assert got["parse_error_rate"] == pytest.approx(0.031)
    assert got["parse_error_rate_strict"] == pytest.approx(0.062)
    assert got["conserved"] is True
    assert got["census_gate"] is True
    assert got["census_residual"] == 12
    assert got["constitution_ok"] is True
    assert got["waste_band_ok"] is True
    assert got["n_checkpoints"] == 12
    assert got["final_hash"] == "043a630f49a9af30"
    for col in c7lib.REQUIRED_DIAG_ROWS:
        assert col in got["diagnostics"]
    assert got["diagnostics"]["promoted"] == 12


def test_parse_run_summary_missing_fields_stay_none(c7lib):
    """読めなかった欄は None のまま(**推測で埋めない**)。"""
    got = c7lib.parse_run_summary("[run] n=5 cells=1 seed=1 ticks=1 world=synthetic\n")
    assert got["wall_seconds"] is None
    assert got["conserved"] is None
    assert got["census_gate"] is None
    assert got["diagnostics"] == {}


def test_parse_time_v(c7lib):
    got = c7lib.parse_time_v(TIME_V)
    assert got["max_rss_kb"] == 18_874_368
    assert got["elapsed_seconds"] == pytest.approx(61_200.0)


def test_dir_bytes(c7lib, tmp_path):
    (tmp_path / "a.bin").write_bytes(b"x" * 10)
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.bin").write_bytes(b"y" * 5)
    assert c7lib.dir_bytes(tmp_path) == 15
    assert c7lib.dir_bytes(tmp_path / "a.bin") == 10


def test_budget_limits_reads_markdown(c7lib):
    lim = c7lib.budget_limits(("W1", "M8", "S1"))
    assert lim["W1"]["limit"] == pytest.approx(24.0)
    assert lim["M8"]["limit"] == pytest.approx(24.0)
    assert lim["M8"]["unit"] == "GB"
    assert lim["S1"]["limit"] == pytest.approx(5.0)


# ---------------------------------------------------------------- 決定論


def _ckpt(*hashes, ticks=None, pop="p", sch="s"):
    tk = ticks or list(range(len(hashes)))
    return {"checkpoints": [{"tick": t, "combined": h, "population_hash": pop,
                             "schedule_hash": sch} for t, h in zip(tk, hashes)]}


def test_determinism_full_match(accept):
    got = accept.determinism_rows(_ckpt("a", "b", "c"), _ckpt("a", "b", "c"), label="x")
    assert got["match"] and got["first_mismatch"] is None


def test_determinism_detects_divergence(accept):
    got = accept.determinism_rows(_ckpt("a", "b", "c"), _ckpt("a", "z", "c"), label="x")
    assert not got["match"] and got["first_mismatch"] == 1


def test_determinism_prefix_mode(accept):
    """T2-b: 部分再ランは前方一致で合格・食い違えば不合格。"""
    full = _ckpt("a", "b", "c", "d")
    head_ok = _ckpt("a", "b")
    head_ng = _ckpt("a", "x")
    assert accept.determinism_rows(full, head_ok, label="b", prefix_ok=True)["match"]
    assert not accept.determinism_rows(full, head_ng, label="b", prefix_ok=True)["match"]


def test_determinism_reads_run_hash_payload(accept):
    """``tools/c6/run_hash.py`` の payload(文字列リスト)も読める。"""
    a = {"checkpoints": ["h1", "h2"]}
    assert accept.determinism_rows(a, a, label="x")["match"]


def test_selfconsistency(accept):
    ok = accept.selfconsistency(_ckpt("a", "b", ticks=[119, 239]))
    assert ok["ok"] and ok["n_checkpoints"] == 2
    ng_order = accept.selfconsistency(_ckpt("a", "b", ticks=[239, 119]))
    assert not ng_order["ok"] and "昇順" in ng_order["reasons"][0]
    doc = _ckpt("a", "b")
    doc["checkpoints"][1]["population_hash"] = "other"
    ng_pop = accept.selfconsistency(doc)
    assert not ng_pop["ok"]
    assert accept.selfconsistency({"checkpoints": []})["ok"] is False


# ---------------------------------------------------------------- 受入表


def test_build_table_full_pass(accept, c7lib):
    summary = c7lib.parse_run_summary(SUMMARY)
    time_v = c7lib.parse_time_v(TIME_V)
    table = accept.build_table(
        summary=summary,
        time_v=time_v,
        s1_bytes=3 * 1024 ** 3,
        manifest={"holdout_open": {"run_id": "r1"}},
        wc={"orphans": [], "X": 0.01},
        t2a={"match": True, "detail": "12 点 vs 12 点"},
        t2b={"match": True, "detail": "前方 1 点一致"},
        t2c={"ok": True, "reasons": []},
        holdout={"n_pass": 4, "n_measured": 4, "pass": True},
    )
    by_id = {r["id"]: r for r in table["rows"]}
    assert by_id["W1"]["judge"] is True          # 17.0h ≤ 24h
    assert by_id["M8"]["judge"] is True          # 18GB ≤ 24GB
    assert by_id["S1"]["judge"] is True          # 3GB ≤ 5GB
    assert by_id["WC-6"]["judge"] is True
    assert by_id["DIAG"]["judge"] is True
    assert by_id["CONS-1"]["judge"] is True
    assert by_id["CONS-2"]["judge"] is True
    assert by_id["SEAL"]["judge"] is True
    assert by_id["P2"]["judge"] is None          # 参考行(40万体の宣言が無い)
    assert table["pass"], [r for r in table["rows"] if r["judge"] is False]


def test_build_table_flags_budget_overrun(accept, c7lib):
    over = SUMMARY.replace("壁時計 61200.00s", "壁時計 90000.00s")
    table = accept.build_table(
        summary=c7lib.parse_run_summary(over),
        time_v={"max_rss_kb": 30 * 1024 ** 2, "elapsed_seconds": 90000.0},
        s1_bytes=6 * 1024 ** 3,
        wc={"orphans": ["幽霊クラス"], "X": 0.4},
    )
    by_id = {r["id"]: r for r in table["rows"]}
    assert by_id["W1"]["judge"] is False
    assert by_id["M8"]["judge"] is False
    assert by_id["S1"]["judge"] is False
    assert by_id["WC-6"]["judge"] is False
    assert not table["pass"]


def test_build_table_missing_inputs_are_unjudged(accept):
    table = accept.build_table()
    assert table["n_judged"] < table["n_rows"]
    assert all(r["measured"] in (None, {}) or r["id"] in ("L4", "DIAG", "HOLD", "SEAL", "WC-5")
               for r in table["rows"] if r["judge"] is None)


def test_build_table_missing_diag_rows(accept, c7lib):
    text = SUMMARY.replace("  診断 suppressed: 1\n", "")
    table = accept.build_table(summary=c7lib.parse_run_summary(text))
    diag = next(r for r in table["rows"] if r["id"] == "DIAG")
    assert diag["judge"] is False and "suppressed" in diag["note"]


def test_table_markdown_mentions_t2_substitution(accept, c7lib):
    md = accept.table_markdown(accept.build_table(summary=c7lib.parse_run_summary(SUMMARY)))
    assert "T2 そのものではない" in md
    assert "C7 受入表" in md
    for rid in ("W1", "M8", "S1", "T2-a", "T2-b", "T2-c", "WC-6", "HOLD"):
        assert rid in md


def test_cli_writes_outputs(accept, tmp_path):
    s = tmp_path / "summary.txt"
    s.write_text(SUMMARY, encoding="utf-8")
    t = tmp_path / "time.txt"
    t.write_text(TIME_V, encoding="utf-8")
    out = tmp_path / "out"
    rc = accept.main(["--summary", str(s), "--time-v", str(t), "--out-bytes", "1000",
                      "--out", str(out)])
    assert rc in (0, 1)
    doc = json.loads((out / "c7_accept.json").read_text(encoding="utf-8"))
    assert doc["n_rows"] == len(doc["rows"])
    assert (out / "c7_accept.md").exists()


# ---------------------------------------------------------------- T2-c 再生 final_hash(D-54)


def test_selfconsistency_checks_replay_final_hash_prefix(accept):
    """--full(テープ再生)は本番 summary の 16 桁 final_hash と前方一致することも要求する。"""
    doc = _ckpt("aaaa", "bbbb", ticks=[359, 719])
    doc["final_hash"] = "043a630f49a9af30" + "0" * 48
    assert accept.selfconsistency(doc, expect_final_prefix="043a630f49a9af30")["ok"] is True
    ng = accept.selfconsistency(doc, expect_final_prefix="deadbeefdeadbeef")
    assert ng["ok"] is False and "再生 final_hash" in ng["reasons"][0]
    # final_hash 欄が無ければ最後の combined で判定
    doc2 = _ckpt("aaaa", "043a630f49a9af30ffff", ticks=[359, 719])
    assert accept.selfconsistency(doc2, expect_final_prefix="043a630f49a9af30")["ok"] is True
    # 期待値なし=従来どおり自己整合だけ
    assert accept.selfconsistency(doc)["ok"] is True


def test_cli_full_option_fills_t2c_only(accept, tmp_path):
    s = tmp_path / "summary.txt"
    s.write_text(SUMMARY, encoding="utf-8")  # 最終 043a630f49a9af30…
    full = tmp_path / "replay.json"
    doc = _ckpt("x1", "x2", "x3", "043a630f49a9af30" + "1" * 48, ticks=[359, 719, 1079, 1439])
    doc["final_hash"] = "043a630f49a9af30" + "1" * 48
    full.write_text(json.dumps(doc), encoding="utf-8")
    out = tmp_path / "out"
    accept.main(["--summary", str(s), "--full", str(full), "--out-bytes", "1", "--out", str(out)])
    rows = {r["id"]: r for r in json.loads((out / "c7_accept.json").read_text(encoding="utf-8"))["rows"]}
    assert rows["T2-c"]["judge"] is True
    assert rows["T2-b"]["judge"] is None  # T2-b は未判定のまま(回していない)
    # 本番と食い違う再生は FAIL
    doc["final_hash"] = "f" * 64
    full.write_text(json.dumps(doc), encoding="utf-8")
    accept.main(["--summary", str(s), "--full", str(full), "--out-bytes", "1", "--out", str(out)])
    rows = {r["id"]: r for r in json.loads((out / "c7_accept.json").read_text(encoding="utf-8"))["rows"]}
    assert rows["T2-c"]["judge"] is False and "再生 final_hash" in rows["T2-c"]["note"]
