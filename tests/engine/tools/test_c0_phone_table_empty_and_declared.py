"""第 1 期 1-7 道具の台帳 C0(CT5): 店の番号の場所の表は空の表で用意し、空欄をつなぎの台帳に宣言する。

口の約束 1-7〔決定(回答 10-13b §3)〕: 店の番号の場所の表は OSM の ``phone`` タグから作る。本段は表を作らず(版上げ 2 回目
=計画 2-4 で埋める)、``phone`` タグを持つ要素の数を記録に書く(``c0/osm_phone_count.json``=同じ規則 ``osm_phone_of``)。
"""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType

import pytest

from shibuya.engine.bridging import ledger as BR
from shibuya.engine.run import run_day
from shibuya.engine.tools import places as PL
from shibuya.engine.tools.places import PhoneTable, osm_phone_of
from shibuya.engine.tools.registry import PHONE, PHONE_BRIDGE, default_registry

ROOT = Path(__file__).resolve().parents[3]
COUNT_JSON = ROOT / "docs" / "bench" / "analysis" / "wallbounce-1012" / "c0" / "osm_phone_count.json"
OSM_TAGS = ROOT / "data" / "realworld" / "osm" / "poi_tags_overpass_20260928.json"


def test_the_table_is_empty_and_answers_none():
    t = PhoneTable()
    assert len(t) == 0 and isinstance(t.rows, MappingProxyType)
    assert all(t.phone_of(i) is None for i in (0, 1, 2_336, 10**6))
    with pytest.raises(ValueError):
        t.phone_of(-1)
    with pytest.raises(ValueError):
        t.phone_of("3")  # type: ignore[arg-type]
    assert t.tally() == {"rows": 0, "source": "osm:phone", "bridge": PHONE_BRIDGE}


def test_the_table_is_read_only_after_construction():
    t = PhoneTable({3: " 03-0000-0000 "})
    assert t.phone_of(3) == "03-0000-0000" and len(t) == 1
    with pytest.raises(TypeError):
        t.rows[4] = "x"  # type: ignore[index]
    with pytest.raises(AttributeError):
        t.rows = {}  # type: ignore[misc]
    with pytest.raises(AttributeError):
        del t.rows
    with pytest.raises(AttributeError):
        object.__setattr__(t, "_rows", {})
    for bad in ({-1: "x"}, {1: ""}, {1: 3}, {"1": "x"}):
        with pytest.raises(ValueError):
            PhoneTable(bad)  # type: ignore[arg-type]


def test_the_blank_is_declared_in_the_bridging_ledger():
    row = {b.id: b for b in BR.default_ledger().active()}[PHONE_BRIDGE]
    # 〔第334・2-4〕外す段を改めた(親)=2-4 → 4-2(版上げ 2 回目では埋めなかった)
    assert row.remove_at == "4-2" and row.conf == "expedient" and row.status == "active"
    assert row.declared_in.startswith("docs/design/v2-foundation-contracts-2026-10-13.md")
    assert "src/shibuya/engine/tools/places.py" in row.code_at
    assert default_registry().get(PHONE).bridge == PHONE_BRIDGE


def test_osm_phone_rule():
    assert osm_phone_of({"phone": "+81 3-1234-5678"}) == "+81 3-1234-5678"
    assert osm_phone_of({"contact:phone": " 03-1 "}) == "03-1"
    assert osm_phone_of({"phone": "a", "contact:phone": "b"}) == "a"        # phone を先に
    assert osm_phone_of({"phone": "  ", "contact:phone": "b"}) == "b"
    assert osm_phone_of({"name": "x"}) is None and osm_phone_of(None) is None and osm_phone_of({}) is None
    assert PL.PHONE_TAGS == ("phone", "contact:phone") and PL.SOURCE == "osm:phone"


@pytest.mark.requires_data("osm:poi_tags_overpass_20260928.json")
def test_the_recorded_count_is_reproduced_with_the_same_rule():
    rec = json.loads(COUNT_JSON.read_text(encoding="utf-8"))
    el = json.loads(OSM_TAGS.read_text(encoding="utf-8"))["elements"]
    n = sum(1 for e in el if osm_phone_of(e.get("tags")) is not None)
    got = rec["files"]["poi_tags_overpass_20260928.json"]
    assert (got["elements"], got["with_phone"]) == (len(el), n) and n > 0


def test_manifest_reports_the_empty_table():
    res = run_day(n_agents=20, n_cells=9, ticks=30, seed=1)
    m = res.run_manifest_fields()["tools"]
    assert m["phone_table"] == {"rows": 0, "source": "osm:phone", "bridge": PHONE_BRIDGE}
    assert m["n_tools"] == 7 and m["groups"] is None and m["contact_flags"] is None  # 母集団なし・関係なし
    # 〔第 1 期 1-8b〕その後ろに speech_port・〔第 2 期 2-2 段 11a〕その後ろに proximity・〔第 3 期 3-3〕その後ろに experiment・
    # 〔第 3 期 3-2〕その後ろに batching・〔第 3 期 3-5〕その後ろに body・〔第 3 期 3-1〕その後ろ(末尾)に calendar_shadow
    assert list(res.run_manifest_fields())[-7:] == ["tools", "speech_port", "proximity", "experiment", "batching", "body",
                                                    "calendar_shadow"]
