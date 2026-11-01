"""第 4 期 4-2 権利台帳の種類(Q3=PENDING 仮-40): 信用の契約(credit)・道路の区間・看板・閉じた表の「所有 → 店」。

- 前からの種類と番号の空間の列のコードは不変(末尾に足した)。
- credit の行は体 → 信用の契約(信用の器の行の番号)で読み書きできる。許可は店・道路の区間・看板に取れる。
- 所有 → 店(W21b の店の持ち主の行の形=組織 → 店)が閉じた表の中に入る。初期の行(段 10)は変えない=行は 0 のまま。
"""

from __future__ import annotations

import pytest

from shibuya.engine.rights import initial as RI
from shibuya.engine.rights import ledger as L


def test_old_codes_are_kept_and_new_kinds_are_appended():
    assert L.KINDS[:4] == ("own", "lease", "employ", "licence") and L.KINDS[4] == "credit"
    assert L.ENTITY_KINDS[:5] == ("agent", "org", "store", "parcel", "dwelling")
    assert L.ENTITY_KINDS[5:] == ("road_segment", "signboard", "credit_contract")
    assert L.KIND_WORDS["credit"] == "信用"
    assert L.OBJECTS_OF_KIND["own"] == ("parcel", "dwelling", "store")
    assert L.OBJECTS_OF_KIND["licence"] == ("store", "road_segment", "signboard")
    assert L.OBJECTS_OF_KIND["credit"] == ("credit_contract",)


def test_credit_rows_read_and_write():
    book = L.Rights(capacity=4)
    i = book.grant(L.Right(holder=(L.AGENT, 7), object=(L.CREDIT_CONTRACT, 0), kind=L.CREDIT, since_ns=10,
                           source="試験:信用の器の行 0"))
    assert book.holds((L.AGENT, 7), L.CREDIT, (L.CREDIT_CONTRACT, 0), 11)
    assert not book.holds((L.AGENT, 7), L.CREDIT, (L.CREDIT_CONTRACT, 0), 9)
    assert book.right(i).kind == "credit" and book.right(i).object == ("credit_contract", 0)
    book.revoke(i, 20, None)
    assert not book.holds_any((L.AGENT, 7), L.CREDIT, 21)
    t = book.tally()
    assert t["by_kind"]["credit"] == 1 and t["by_object_kind"]["credit_contract"] == 1
    assert t["by_object_kind"]["road_segment"] == 0 and t["by_object_kind"]["signboard"] == 0
    with pytest.raises(ValueError):
        L.Right(holder=(L.AGENT, 7), object=(L.STORE, 0), kind=L.CREDIT, source="x")


def test_licences_on_road_segments_and_signboards():
    book = L.Rights(capacity=2)
    book.grant(L.Right(holder=(L.STORE, 3), object=(L.ROAD_SEGMENT, 12), kind=L.LICENCE, source="試験:道路の占用"))
    book.grant(L.Right(holder=(L.STORE, 3), object=(L.SIGNBOARD, 1), kind=L.LICENCE, source="試験:屋外広告物"))
    assert book.holders_of((L.ROAD_SEGMENT, 12), L.LICENCE, 0) == (("store", 3),)
    assert book.holders_of((L.SIGNBOARD, 1), L.LICENCE, 0) == (("store", 3),)


def test_own_store_is_in_the_closed_table():
    book = L.Rights(capacity=1)
    book.grant(L.Right(holder=(L.ORG, 5), object=(L.STORE, 2), kind=L.OWN, source="宣言:店の持ち主(試験)"))
    assert book.holds((L.ORG, 5), L.OWN, (L.STORE, 2), 0)


def test_initial_rows_are_unchanged_no_owner_credit_road_or_signboard_rows():
    import numpy as np

    r = RI.build_initial(np.array([2, 2, 3]), 3, org_of_agent=np.array([0, -1, 1]))
    t = r.tally()
    assert t["by_kind"]["own"] == 0 and t["by_kind"]["credit"] == 0 and t["by_kind"]["licence"] == 0
    assert t["by_object_kind"]["road_segment"] == 0 and t["by_object_kind"]["signboard"] == 0
