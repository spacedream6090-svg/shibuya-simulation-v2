"""c8lib の純関数と**設計書の走査**(漏れ検出の分母)。"""

from __future__ import annotations

import pytest


# ------------------------------------------------------------------ 表の整形
def test_markdown_table_escapes_pipes(c8lib):
    """セルの ``|`` を逃がさないと表が崩れる(T5 の「|r| ≤ 0.05」で実際に崩れた)。"""
    md = c8lib.markdown_table(["a"], [["|r| ≤ 0.05"]])
    assert "\\|r\\| ≤ 0.05" in md
    body = md.splitlines()[2]
    assert body.replace("\\|", "").count("|") == 2  # 逃がしていない ``|`` は行の両端だけ


def test_md_cell_none_and_newline(c8lib):
    assert c8lib.md_cell(None) == "—"
    assert c8lib.md_cell("a\nb") == "a b"


def test_fmt(c8lib):
    assert c8lib.fmt(None) == "—"
    assert c8lib.fmt(True) == "はい"
    assert c8lib.fmt(False) == "いいえ"
    assert c8lib.fmt(1234) == "1,234"
    assert c8lib.fmt(0.12345, 3) == "0.123"
    assert c8lib.fmt(float("nan")) == "—"


# ------------------------------------------------------------------ 判定の道具
def test_null_jsd_p95_is_small_for_large_samples(c8lib):
    """同じ分布から 2 回引いた JSD は N が大きいほど小さい(帰無参照の性質)。"""
    small = c8lib.null_jsd_p95([100.0] * 5, reps=200)
    large = c8lib.null_jsd_p95([10_000.0] * 5, reps=200)
    assert 0.0 < large < small


def test_null_jsd_p95_degenerate(c8lib):
    assert c8lib.null_jsd_p95([]) == 0.0
    assert c8lib.null_jsd_p95([5.0]) == 0.0
    assert c8lib.null_jsd_p95([0.0, 0.0]) == 0.0


def test_null_jsd_p95_is_deterministic(c8lib):
    a = c8lib.null_jsd_p95([50.0, 30.0, 20.0], reps=100, seed=7)
    b = c8lib.null_jsd_p95([50.0, 30.0, 20.0], reps=100, seed=7)
    assert a == b


def test_compare_counts_identical(c8lib):
    """同じ分布どうしは JSD 0・TVD 0・帰無参照を超えない。"""
    out = c8lib.compare_counts([300.0, 200.0, 100.0], [300.0, 200.0, 100.0], reps=200)
    assert out["jsd_bits"] == 0.0
    assert out["tvd"] == 0.0
    assert out["detected"] is False


def test_compare_counts_shifted(c8lib):
    out = c8lib.compare_counts([600.0, 0.0], [0.0, 600.0], reps=200, labels=["a", "b"])
    assert out["jsd_bits"] == pytest.approx(1.0, abs=1e-9)  # bits の上限
    assert out["tvd"] == pytest.approx(1.0)
    assert out["detected"] is True
    assert [t["label"] for t in out["top_shifts"]] == ["a", "b"]


def test_compare_counts_length_mismatch(c8lib):
    with pytest.raises(ValueError):
        c8lib.compare_counts([1.0, 2.0], [1.0])


def test_verdict_is_one_sided(c8lib):
    assert c8lib.verdict_from_stage(False) == "not_driving"
    assert c8lib.verdict_from_stage(True) == "needs_run"


def test_gpu_hours_for_calls(c8lib):
    """受入報告 C6 の実測(呼 50,000=約 29 分)を再現する換算であること。"""
    assert c8lib.gpu_hours_for_calls(50_000) == pytest.approx(29.0 / 60.0, rel=1e-9)
    with pytest.raises(ValueError):
        c8lib.gpu_hours_for_calls(1.0, calls_per_second=0.0)


def test_budget_row_reads_markdown(c8lib):
    """予算宣言表は **Markdown が正典**(数値をツールに複製しない)。"""
    row = c8lib.budget_row("L2")
    assert row is not None and "20%" in row["declared"]
    assert c8lib.budget_row("ZZ9") is None


# ------------------------------------------------------------------ 設計書の走査
def test_scan_build_spec_finds_inline_sensitivities(c8lib):
    """``- expedient: …。感度: …`` の**行の途中**の宣言も拾えること。"""
    rows = c8lib.scan_build_spec_sensitivities()
    anchors = {r.anchor for r in rows}
    # 行頭が「感度:」の行
    assert {"D-W6", "D-W8", "D-W11", "D-W13", "D-W14", "D-W16"} <= anchors
    # 行の途中で宣言している行(旧実装では落ちていた)
    assert {"D-W2", "D-W3", "D-W5", "D-W7", "D-W9", "D-W10", "D-W15", "D-W17"} <= anchors
    assert all(r.source.endswith("v2-world-data-build-spec.md") for r in rows)
    assert all(r.text for r in rows)


def test_scan_build_spec_marks_required(c8lib):
    """『感度(必須)』は D-W8(既定営業時間±2h)だけ。"""
    rows = c8lib.scan_build_spec_sensitivities()
    assert {r.anchor for r in rows if r.required} == {"D-W8"}


def test_scan_build_spec_ignores_outside_headings(c8lib, tmp_path):
    doc = tmp_path / "spec.md"
    doc.write_text(
        "## §2 決定項\n"
        "- 感度: 見出しの外(拾わない)\n"
        "### D-W1 範囲\n"
        "- expedient: なし。感度: 中身(拾う)\n"
        "## §3 取得レーン\n"
        "- 感度: §3 の行(拾わない)\n",
        encoding="utf-8",
    )
    rows = c8lib.scan_build_spec_sensitivities(doc)
    assert [(r.anchor, r.text) for r in rows] == [("D-W1", "中身(拾う)")]


def test_scan_first_wave_arms_is_six(c8lib):
    """知覚契約書 §8 の第1陣は **6 本**(数が変わったら設計が動いた合図)。"""
    arms = c8lib.scan_first_wave_arms()
    assert len(arms) == 6
    assert "単一ランキング" in arms[0]
    assert "d50" in arms[1]
    assert "不応期" in arms[2]
    assert "SNR" in arms[3]
    assert "内省" in arms[4]
    assert "広告ゼロ" in arms[5]


def test_scan_engine_ablation_ids(c8lib):
    """世界過程は 1 行 1 感度試験 id(AB-*)を持つ。"""
    ids = c8lib.scan_engine_ablation_ids()
    assert len(ids) == 21
    assert all(k.startswith("AB-") for k in ids)
    assert {f"AB-PNOTICE-A{k}" for k in range(5)} <= set(ids)
    assert ids["AB-SHELF-REORDER"] == "goods_flow.py"


def test_ledger_gaps(c8lib):
    rows = [c8lib.SensitivityRow("s.md", "D-W1", "t"), c8lib.SensitivityRow("s.md", "D-W2", "t")]
    gaps = c8lib.ledger_gaps(rows, {"rows": [{"design_anchor": "D-W1"}, {"design_anchor": "X"}]})
    assert gaps["missing"] == ["D-W2"]
    assert gaps["extra"] == ["X"]


def test_scan_plan_sensitivities_is_report_only(c8lib):
    """実装計画書 §8 の走査は**報告用**(網羅は保証しない)。落ちずに何か返ること。"""
    rows = c8lib.scan_plan_sensitivities()
    assert rows
    assert all(r.source.endswith("v2-implementation-plan.md") for r in rows)
