# -*- coding: utf-8 -*-
"""第333(R-114): 渋谷区の人流の再取得で 2025 年以降の行が開封済みの層に混ざらない(合成の行だけ・実データは読まない)。"""
from __future__ import annotations

from tools.realworld_fetch import shibuya_jinryu as J


def _rec(year, month="1月", n=1):
    return {"名称": "A", "種別": "滞在人口", "年": year, "月": month, "人数 の合計": n, "ObjectId": 1}


def test_split_k5_keeps_2024_and_earlier_and_splits_later_years():
    rows = [_rec("2018年"), _rec("2024年"), _rec("2025年"), _rec("2026年"), _rec("")]
    keep, k5 = J.split_k5(rows)
    assert [r["年"] for r in keep] == ["2018年", "2024年", ""]
    assert [r["年"] for r in k5] == ["2025年", "2026年"]


def test_year_parsing_tolerates_formats():
    assert J._year_of({"年": "2024"}) == 2024
    assert J._year_of({"年": "2025年"}) == 2025
    assert J._year_of({"年": "R7"}) is None
    assert J._year_of({}) is None


def test_opened_layer_max_year_is_the_last_opened_year():
    assert J.OPENED_LAYER_MAX_YEAR == 2024
    assert J.K5_SOURCE == "shibuya_jinryu_k5"
