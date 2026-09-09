"""忠実度計器盤の**純関数**(モック入力)。R14 G-1 の3面の分け方を検査する。"""

from __future__ import annotations

from .conftest import real_data

MANIFEST = {
    "build_hash": "0123456789abcdef" * 4,
    "stages": [
        {
            "stage": "W0",
            "stage_version": "1.0.0",
            "gates": {"a": {"pass": True}, "b": {"pass": True}},
            "expedients": ["x"],
        },
        {
            "stage": "W9",
            "stage_version": "1.0.0",
            "gates": {"shadow_bytes": {"pass": False}, "c": {"pass": True}},
            "expedients": ["y", "z"],
        },
    ],
}

WC = {
    "catalog_version": "v0.2",
    "catalog_sha16": "34f9fa9d316587be",
    "n_classes": 57,
    "vector": {"C": 0.425, "C_quantified": 0.237, "Q": 0.204, "D": 0.327, "V": 0.0, "R": None},
    "X": 0.0041,
    "orphans": [],
    "dead_stock_candidates": ["a", "b"],
}

ACCEPT = {
    "rows": [
        {"id": "W1", "item": "壁時計/シミュ日", "measured": 25.0, "limit": 24.0, "judge": False, "note": ""},
        {"id": "M8", "item": "RSS", "measured": 12.0, "limit": 24.0, "judge": True, "note": ""},
        {"id": "P2", "item": "移動+密度", "measured": 1.2, "limit": 5.0, "judge": None, "note": "参考"},
        {"id": "HOLD", "item": "KDDI 形状5指標", "measured": "4/5 合格", "limit": "5 指標", "judge": False, "note": ""},
        {"id": "SEAL", "item": "開封記録", "measured": True, "limit": "有ること", "judge": True, "note": ""},
    ]
}


# ------------------------------------------------------------------ 収集
def test_collect_build_gates(dashboard):
    out = dashboard.collect_build_gates(MANIFEST)
    assert out["available"] is True
    assert out["n_stages"] == 2 and out["n_gates"] == 4 and out["n_fail"] == 1
    assert out["n_expedients"] == 3
    assert out["stages"][1]["failing"] == ["shadow_bytes"]


def test_collect_build_gates_missing(dashboard):
    """入力が無ければ「未測定」。**推測で埋めない**。"""
    out = dashboard.collect_build_gates(None)
    assert out == {"available": False, "stages": [], "n_fail": None}


def test_collect_coverage_vector_not_summed(dashboard):
    """5 値ベクトルは**加重和にしない**(方法論)=各値が別の欄で出ること。"""
    out = dashboard.collect_coverage(WC)
    assert [out["C"], out["Q"], out["D"], out["V"]] == [0.425, 0.204, 0.327, 0.0]
    assert out["R"] is None  # ランタイム実測が無ければ null のまま
    assert out["orphans"] == 0 and out["gate_wc6"] is True
    assert out["dead_stock_candidates"] == 2
    assert "score" not in out and "total" not in out


def test_collect_coverage_orphans_fail_gate(dashboard):
    out = dashboard.collect_coverage({**WC, "orphans": ["クラスA"]})
    assert out["gate_wc6"] is False


def test_collect_calibration_has_no_gate(dashboard):
    """面1は報告のみ=行に judge/pass を作らない。"""
    rows = dashboard.collect_calibration(
        {"srmse_age_resident": 0.1, "limits": {"srmse_age": 0.13}}, None
    )
    assert rows and all("judge" not in r and "pass" not in r for r in rows)
    assert rows[0]["value"] == 0.1 and rows[0]["limit"] == 0.13


def test_collect_calibration_empty(dashboard):
    assert dashboard.collect_calibration(None, None) == []


def test_collect_quality(dashboard):
    fmt = {"source": "tape=x", "score": {"n": 10, "format_error_rate": 0.01, "format_error_gate": 0.1, "format_error_ok": True, "role_action_rate": 0.0}}
    mb = {"n_selected": 350, "passes": [{"model": "8B", "violation_rate": 0.12}], "comparison": {"delta_violation_rate": -0.12, "violation_ok": False, "jsd_bits": 0.29, "distribution_ok": False}, "preregistration": {}}
    ab = {"switch_probe": {"switch_effective": True}, "jsd_bits": 0.0397, "identical_runs": False, "arms": [{"arm": "fixed_slots", "llm_calls": 833}]}
    out = dashboard.collect_quality(fmt, mb, ab)
    assert out["format"]["ok"] is True
    assert out["metric_b"]["violation_ok"] is False
    assert out["metric_b"]["models"] == ["8B"]
    assert out["ablation1"]["jsd_bits"] == 0.0397


def test_collect_quality_empty(dashboard):
    assert dashboard.collect_quality(None, None, None) == {}


def test_collect_ablations(dashboard, c8lib):
    table = c8lib.load_ablations()
    out = dashboard.collect_ablations(table)
    assert out["n_arms"] == 6
    assert out["n_ready"] == 4  # ①(C6)+ ②③⑥(C8・2026-09-09)
    assert out["n_executed"] == 0
    result = {"arm": "AB1-BUDGET-MODE", "executed": True, "comparisons": [{"action_jsd": 0.04, "exceeds_null": True}]}
    out2 = dashboard.collect_ablations(table, [result])
    assert out2["n_executed"] == 1
    assert out2["rows"][0]["action_jsd"] == 0.04


def test_collect_sensitivity(dashboard, c8lib):
    out = dashboard.collect_sensitivity(c8lib.load_sensitivity())
    assert out["n_rows"] >= 14
    assert out["n_process_ablations"] == 21
    assert out["n_done"] == out["n_not_driving"] + out["n_needs_run"]


def test_collect_ops_flags_only_symptoms(dashboard):
    """面3は症状だけ。**holdout(ゲート)の行は面2の受け持ちなので出さない**(R14 G-1)。"""
    out = dashboard.collect_ops(ACCEPT)
    assert out["available"] is True
    assert {r["id"] for r in out["rows"]}.isdisjoint(dashboard.FACE2_ROW_IDS)
    assert out["n_red"] == 1 and out["red_ids"] == ["W1"]
    assert "バーンレート" in out["alarm_rule"]
    assert out["budget_declared"]["W1"]["item"]


def test_collect_ops_without_accept_shows_declarations(dashboard):
    out = dashboard.collect_ops(None)
    assert out["available"] is False and out["rows"] == []
    assert set(dashboard.OPS_BUDGET_ROWS) <= set(out["budget_declared"])


def test_collect_holdout_is_the_only_gate(dashboard):
    out = dashboard.collect_holdout(ACCEPT)
    assert out["available"] is True
    assert out["holdout_row"]["judge"] is False
    assert out["implausibility"]["I_M"] is None  # アンサンブルが無い間は計算しない
    assert "Var_ens" in out["implausibility"]["note"]  # 計算しない理由が書いてあること
    assert "I ≤ 3" in out["implausibility"]["gate"]
    assert out["prereg_status"].startswith("案")  # k* はまだ凍結ファイルでない
    assert "片側" in out["one_sided"] or "通っても合格とは言わない" in out["one_sided"]


def test_collect_holdout_unopened(dashboard):
    out = dashboard.collect_holdout(None)
    assert out["available"] is False
    assert out["holdout_row"] is None


def test_collect_distortions(dashboard):
    text = (
        "| D-33 | **行動分布**: 会話 0.02% …「歪む場所」の宣言候補 | (a) 宣言のみ | **(a)+(c)** | (a) |\n"
        "| D-99 | 無関係な行 | (a) | **(a)** | (a) |\n"
        "| D-38 | **役割語率 0.0** | (a) 宣言(フォールバック被覆 100%) | **(a)** | (a) |\n"
        "本文の行は拾わない(歪む場所)\n"
    )
    out = dashboard.collect_distortions(text)
    assert [d["id"] for d in out] == ["D-33", "D-38"]
    assert out[0]["kind"] == "歪む場所"
    assert out[1]["kind"] == "宣言"


def test_collect_verification_prefers_measured_lines(dashboard):
    reports = {
        "build-report-C6.md": (
            "| C6-b | 検証テスト T7 分布同値 | サブ P | 実装中 |\n"
            "- **T7 LLM 層 分布同値(親実行)**: 行動語分布の JSD **0.0035 bit** で一致\n"
        )
    }
    rows = {r["id"]: r for r in dashboard.collect_verification(reports)}
    assert "0.0035" in rows["T7"]["evidence"]
    assert rows["T7"]["source"] == "build-report-C6.md"


def test_collect_verification_leaves_unknown_empty(dashboard):
    """根拠が無い行は空欄のまま(**推測で埋めない**)。"""
    rows = {r["id"]: r for r in dashboard.collect_verification({"x.md": "何も書いていない"})}
    assert rows["T8"]["evidence"] == "" and rows["T8"]["source"] == ""


def test_collect_verification_covers_t1_t9(dashboard):
    rows = dashboard.collect_verification({})
    assert [r["id"] for r in rows] == [f"T{i}" for i in range(1, 10)]


# ------------------------------------------------------------------ 描画
def _payload(dashboard, c8lib, accept=None):
    return {
        "faces": {
            "face1_calibration": {
                "gate": False,
                "build_gates": dashboard.collect_build_gates(MANIFEST),
                "coverage": dashboard.collect_coverage(WC),
                "calibration": dashboard.collect_calibration({"n_total": 5}, None),
                "quality": {},
                "ablations": dashboard.collect_ablations(c8lib.load_ablations()),
                "sensitivity": dashboard.collect_sensitivity(c8lib.load_sensitivity()),
                "verification": dashboard.collect_verification({}),
            },
            "face2_holdout": {"gate": True, **dashboard.collect_holdout(accept)},
            "face3_ops": {"gate": False, **dashboard.collect_ops(accept)},
        },
        "distortions": [],
        "inputs": {"build_manifest": True, "build_reports": ["a.md"]},
    }


def test_render_tables_are_well_formed(dashboard, c8lib):
    md = dashboard.render(_payload(dashboard, c8lib, ACCEPT))
    ncols = {}
    for line in md.splitlines():
        if not line.startswith("|"):
            ncols = {}
            continue
        n = line.replace("\\|", "").count("|")
        ncols.setdefault("n", n)
        assert n == ncols["n"], line


def test_render_marks_gate_only_on_face2(dashboard, c8lib):
    md = dashboard.render(_payload(dashboard, c8lib, ACCEPT))
    assert "**ゲート(合否)は面2のみ**" in md
    assert "面2 holdout(唯一のゲート・判定はアンサンブル単位)" in md
    assert "面1 較正(報告のみ)" in md
    assert "面3 運用(症状のみ赤)" in md


def test_render_without_inputs(dashboard, c8lib):
    md = dashboard.render(_payload(dashboard, c8lib, None))
    assert "未測定" in md


@real_data
def test_build_on_real_repo(dashboard):
    """実リポの入力で組み立てて落ちないこと(親が叩く経路)。"""
    payload = dashboard.build()
    assert payload["schema"] == "shibuya.tools.c8/dashboard/1"
    assert payload["faces"]["face1_calibration"]["build_gates"]["available"] is True
    assert payload["faces"]["face2_holdout"]["gate"] is True
    assert payload["distortions"]  # PENDING から「歪む場所」が拾えている
    md = dashboard.render(payload)
    assert md.startswith("# 忠実度計器盤")
