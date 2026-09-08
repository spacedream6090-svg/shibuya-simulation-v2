"""予算宣言表リーダの検収(docs/design/v2-budget-declaration.md を正典として読む)。

門前条件(CLAUDE.md §4)の機械可読な足場。表が壊れた/黙って行が消えたら落ちる。
"""

from __future__ import annotations

import re

import pytest

from shibuya.core.budget import (
    BudgetRow,
    budget_by_id,
    load_budget_table,
    parse_limit,
)

# 予算宣言表 §1〜§5 の中核5系列(W/P/M/L/S)= 33行。
CORE_IDS = frozenset(
    [f"W{i}" for i in range(1, 4)]
    + [f"P{i}" for i in range(1, 8)]
    + [f"M{i}" for i in range(1, 13)]
    + [f"L{i}" for i in range(1, 8)]
    + [f"S{i}" for i in range(1, 5)]
)

# §4 の表に同居する初期化予算(2026-09-07 新設・「1回限り・W1の対象外」)。
# 中核5系列とは別勘定なので id 系列も別(I)。表の行としては実在するため読む。
EXTRA_IDS = frozenset({"I1"})

EXPECTED_IDS = CORE_IDS | EXTRA_IDS


@pytest.fixture(scope="module")
def rows() -> tuple[BudgetRow, ...]:
    return load_budget_table()


@pytest.fixture(scope="module")
def by_id(rows: tuple[BudgetRow, ...]) -> dict[str, BudgetRow]:
    return budget_by_id(rows)


def test_core_series_is_33_rows(by_id: dict[str, BudgetRow]) -> None:
    """W1-W3・P1-P7・M1-M12・L1-L7・S1-S4 の33行が過不足なく揃っている。"""
    core = {i for i in by_id if i in CORE_IDS}
    assert core == set(CORE_IDS)
    assert len(core) == 33


def test_id_set_and_row_count(rows: tuple[BudgetRow, ...], by_id: dict[str, BudgetRow]) -> None:
    """表の全行 = 中核33行 + I1(初期化予算)= 34行。"""
    assert set(by_id) == set(EXPECTED_IDS)
    assert len(rows) == len(EXPECTED_IDS) == 34
    assert len(by_id) == len(rows), "id が重複していない"


def test_rows_are_in_document_order(rows: tuple[BudgetRow, ...]) -> None:
    ids = [r.id for r in rows]
    assert ids[:3] == ["W1", "W2", "W3"]
    assert ids[-4:] == ["S1", "S2", "S3", "S4"]


def test_category_matches_first_letter(rows: tuple[BudgetRow, ...]) -> None:
    for r in rows:
        assert r.category == r.id[0]
        assert re.match(r"^[WPMLSI]\d+$", r.id), r.id


def test_sections_are_1_to_5(rows: tuple[BudgetRow, ...], by_id: dict[str, BudgetRow]) -> None:
    """§6(ハードウェアプロファイル)の表は読み込まれていない。"""
    sections = {r.section for r in rows}
    assert len(sections) == 5
    assert all(s[0] in "12345" and s[1] == "." for s in sections)
    assert by_id["W1"].section.startswith("1.")
    assert by_id["M8"].section.startswith("3.")
    assert by_id["S1"].section.startswith("5.")
    # §6 の実測表(| 項目 | 実測値… |)を拾っていない証拠
    assert not any("RTX A5000" in r.declared for r in rows)


def test_every_row_has_item_and_declared(rows: tuple[BudgetRow, ...]) -> None:
    for r in rows:
        assert r.item, f"{r.id}: 項目が空"
        assert r.declared, f"{r.id}: 宣言値が空"


def test_parse_limit_m8_rss() -> None:
    """M8 = RSS総額 ≤24GB(太字セル)。"""
    assert parse_limit("**≤24GB**") == (24.0, "GB")


def test_parse_limit_m8_from_table(by_id: dict[str, BudgetRow]) -> None:
    assert parse_limit(by_id["M8"].declared) == (24.0, "GB")


def test_parse_limit_s1_storage(by_id: dict[str, BudgetRow]) -> None:
    """S1 = 恒久記録 ≤5GB/シミュ日(太字でないセルからも拾える)。"""
    limit = parse_limit(by_id["S1"].declared)
    assert limit is not None
    value, unit = limit
    assert value == 5.0
    assert "GB" in unit


@pytest.mark.parametrize(
    ("declared", "expected"),
    [
        ("**≤24GB**", (24.0, "GB")),
        ("**≤24時間/シミュ日**", (24.0, "時間/シミュ日")),
        ("**≥10万イベント/秒**", (100000.0, "イベント/秒")),
        ("**≤50ms/フレーム**", (50.0, "ms/フレーム")),
        ("**≤10分**", (10.0, "分")),
        ("**≤2.0x**", (2.0, "x")),
        ("**入力≤1,300**", (1300.0, "")),
        ("恒常規則(宣言なきフィールドはマージ不可)", None),
    ],
)
def test_parse_limit_cases(declared: str, expected: tuple[float, str] | None) -> None:
    assert parse_limit(declared) == expected


def test_parse_limit_known_table_rows(by_id: dict[str, BudgetRow]) -> None:
    """表の実セルからの抽出(best-effort だが主要行は当たること)。"""
    assert parse_limit(by_id["P1"].declared) == (50.0, "ms/フレーム")
    assert parse_limit(by_id["P3"].declared) == (100000.0, "イベント/秒")
    assert parse_limit(by_id["W2"].declared) == (10.0, "分")
    assert parse_limit(by_id["M7"].declared) == (2.0, "x")
    assert parse_limit(by_id["S2"].declared) == (17.0, "GB/シミュ日")


def test_bad_id_raises(tmp_path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text(
        "## 1. テスト\n\n"
        "| # | 項目 | 宣言値(仮) | 根拠 | 改訂条件 |\n"
        "|---|---|---|---|---|\n"
        "| X9 | ダミー | **≤1GB** | なし | 恒常 |\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="不正な予算行 id"):
        load_budget_table(bad)


def test_duplicate_id_raises(tmp_path) -> None:
    dup = tmp_path / "dup.md"
    dup.write_text(
        "## 1. テスト\n\n"
        "| # | 項目 | 宣言値(仮) | 根拠 | 改訂条件 |\n"
        "|---|---|---|---|---|\n"
        "| W1 | ダミー | **≤1GB** | なし | 恒常 |\n"
        "| W1 | ダミー2 | **≤2GB** | なし | 恒常 |\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="重複"):
        load_budget_table(dup)


def test_env_override(tmp_path, monkeypatch) -> None:
    md = tmp_path / "override.md"
    md.write_text(
        "## 1. テスト\n\n"
        "| # | 項目 | 宣言値(仮) | 根拠 | 改訂条件 |\n"
        "|---|---|---|---|---|\n"
        "| W1 | ダミー | **≤3GB** | なし | 恒常 |\n"
        "\n## 6. ハードウェア\n\n"
        "| 項目 | 実測値 |\n|---|---|\n| GPU | A5000 |\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SHIBUYA_BUDGET_MD", str(md))
    rows = load_budget_table()
    assert [r.id for r in rows] == ["W1"]
    assert parse_limit(rows[0].declared) == (3.0, "GB")
