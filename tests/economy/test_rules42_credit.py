"""第 4 期 4-2 総量規制の検査と利息の上限(信用の器・呼び手なし=結果不変・R-118 §2-7)。

- 総量規制: 借入れの合計(残高+新しい額)が年収などの 3 分の 1 以下なら貸せる(貸金業法 13 条の 2 第 2 項)。
- 収入の書類(欄だけ): この貸し手で 50 万円超、または他社と合わせて 100 万円超(13 条 3 項)。
- 利息の上限: 元本 10 万円未満 20%・100 万円未満 18%・それ以上 15%(利息制限法 1 条)。
- カードの枠の割合は未確認=空欄(``CARD_LIMIT_RATIO`` は None)。
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from shibuya.economy import credit as CR

ASOF = "2026-07-13"
SRC = Path(__file__).resolve().parents[2] / "src" / "shibuya"


def test_total_volume_cap_is_one_third_of_the_income():
    inc = np.full(4, 3_000_000)
    got = CR.total_volume_check(inc, np.array([900_000, 900_000, 0, 1_000_000]), np.zeros(4),
                                np.array([100_000, 100_001, 1_000_000, 0]), ASOF)
    assert got["ok"].tolist() == [True, False, True, True]
    assert got["source"] == "rules:credit.total_volume_cap@2025-10-01"


def test_income_document_rule_is_a_field():
    got = CR.total_volume_check(np.full(4, 9_000_000), np.array([0, 0, 600_000, 600_001]), np.array([0, 0, 0, 0]),
                                np.array([500_000, 500_001, 400_000, 400_000]), ASOF)
    assert got["document"].tolist() == [False, True, False, True]


def test_before_the_lower_bound_the_check_stops():
    """〔検収 L5〕総量規制の行の asof は下限の印=それより前の日は「規則なし」にせず止まる。"""
    from shibuya.engine.rules import table as RT

    with pytest.raises(RT.RuleNotInForce):
        CR.total_volume_check(np.array([0]), np.array([0]), np.array([0]), np.array([1]), "2020-01-01")


def test_interest_cap_bands():
    r, src = CR.interest_cap_rate(np.array([99_999, 100_000, 999_999, 1_000_000]), ASOF)
    assert r.tolist() == [2_000, 1_800, 1_800, 1_500] and src == "rules:credit.interest_cap@2010-06-18"


def test_card_limit_ratio_is_blank_and_nothing_calls_the_checks():
    assert CR.CARD_LIMIT_RATIO is None
    calls = []
    for p in SRC.rglob("*.py"):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in (
                    "total_volume_check", "interest_cap_rate"):
                calls.append(p.relative_to(SRC).as_posix())
    assert calls == []  # 呼び手は無い(借りる判断の段の後)=結果不変
