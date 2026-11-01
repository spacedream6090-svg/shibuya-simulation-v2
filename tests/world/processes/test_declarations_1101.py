"""第340 段 2 の 6・7: 宣言の 3 欄(``drives_from``・``absent``・``input_decl``)と一覧(回答 11-01 §1・§2・§10-3)。

- 3 欄は ``as_dict`` に入らない=``registry_hash`` は第340 の前と同じ(整理の段は 1 バイト不変)。
- 「無いと宣言」: 回答 11-01 §10-3 の過程 8 つ・納品(入力)と発注(初期の予定)・口が無い判断 13 件(+手伝い・断る)。
- 入力の宣言: 既存の 5 つ(filled・出典の行つき)・新しい 7 つ(欄だけ)・納品(欄だけ)。
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest

from shibuya.world.processes import absent as AB
from shibuya.world.processes import first_batch as FB
from shibuya.world.processes import inputs as INP
from shibuya.world.processes.records import Absence, InputDecl
from tests.world.processes.conftest import make_plan_spec, make_process

ROOT = Path(__file__).resolve().parents[3]
ROUTING = (ROOT / "docs" / "reference" / "decision-routing-2026-11-01.md").read_text(encoding="utf-8")

#: 第340 の前(c0729a4)の ``build_registry().registry_hash()``。宣言の 3 欄を足しても変わらない。
REGISTRY_HASH_BEFORE = "1a5fcb8ce4a7e24fea4edec40a6f3ca84f40601f37abf2320a3a1d7c31095743"


# ================================================================= 型
def test_declaration_fields_do_not_enter_as_dict_or_the_registry_hash():
    reg = FB.build_registry()
    assert reg.registry_hash() == REGISTRY_HASH_BEFORE
    for p in (*reg.processes, *reg.plan_specs):
        d = p.as_dict()
        assert not {"drives_from", "absence", "input_decl"} & set(d), p.id
        ex = p.declaration_extras()
        assert ex["id"] == p.id and ex["drives_from"] == list(p.drives_from)


def test_drives_from_none_is_alone():
    make_process(drives_from=("none",))
    with pytest.raises(ValueError, match="単独"):
        make_process(drives_from=("none", "W2"))
    with pytest.raises(ValueError, match="重複"):
        make_process(drives_from=("W2", "W2"))
    with pytest.raises(TypeError, match="absence"):
        make_process(absence="無い")
    with pytest.raises(TypeError, match="input_decl"):
        make_plan_spec(input_decl="気象")


def test_absence_requires_statement_reason_and_remove_at():
    a = AB.by_id()["absent.parcel_delivery"]
    for f in ("statement", "reason", "remove_at"):
        with pytest.raises(ValueError, match=f):
            dataclasses.replace(a, **{f: " "})
    with pytest.raises(ValueError, match="kind"):
        dataclasses.replace(a, kind="gone")
    with pytest.raises(ValueError, match="routing_rows"):
        dataclasses.replace(a, routing_rows=(113,))


def test_filled_input_needs_every_value_and_a_source_row():
    w = INP.WEATHER
    with pytest.raises(ValueError, match="値の欄"):
        dataclasses.replace(w, perturbation="")
    with pytest.raises(ValueError, match="出典の行"):
        dataclasses.replace(w, source_rows=())
    InputDecl(id="input.x", name="x", status="fields_only")  # 欄だけは値が空でよい


# ================================================================= 無いと宣言
def test_absent_processes_of_answer_10_3():
    subjects = {a.subject for a in AB.NO_ACTOR}
    assert subjects == {"ごみ収集", "街路の清掃", "道路工事", "救急と警察の出動", "催しの人の注入", "採用と解雇",
                        "電気と水の負荷", "宅配"}
    assert {(a.subject, a.kind) for a in AB.REPLACED} == {("納品", "input"), ("発注", "initial_plan")}
    assert len(AB.NO_PORT) == 13 and len(AB.NO_PORT_EXTRA) == 1
    assert {a.subject for a in AB.RATE_REMOVED} == {"ポイ捨て", "売れ残りの廃棄"}  # 回答 11-01 §2(検収 中-3)
    assert len(AB.by_id()) == len(AB.ABSENCES) == 26


def test_routing_absent_rows_all_have_a_declaration():
    """routing §1 の行き先「無いと宣言」の 6 行は宣言がある(#102 納品は入力として)。"""
    rows = [int(m.group(1)) for m in re.finditer(r"^\| (\d+) \|[^|]+\|[^|]+\| 無いと宣言 \|", ROUTING, re.M)]
    assert sorted(rows) == [102, 103, 104, 105, 106, 110]
    declared = {r for a in AB.ABSENCES for r in a.routing_rows}
    assert set(rows) <= declared


def test_statements_are_copied_from_routing_section_3():
    """routing §3 に文案のある宣言は文案の写し(「」の中=鉤括弧の文と一致)。"""
    s3 = ROUTING.split("## §3", 1)[1].split("## §4", 1)[0]
    drafts = set(re.findall(r"「([^」]*(?:『[^』]*』[^」]*)*)」", s3))
    copied = [a for a in AB.ABSENCES if a.source.startswith(AB.ROUTING_DOC) and "W3 の文" not in a.source]
    # §3-1 の 7(電気と水は文案なし)+ §3-2 の 13 + 手伝い・断る − W3 の文を統一した 2(救急と倒れる=検収 低-8)
    assert len(copied) == 19
    for a in copied:
        assert a.statement in drafts, a.id


def test_attached_to_world_processes():
    reg = FB.build_registry()
    attached = {p.id: p.absence.id for p in reg.processes if p.absence is not None}
    assert attached == {
        "waste_collection": "absent.waste_collection",
        "street_cleaning": "absent.street_cleaning",
        "delivery_last_mile": "absent.parcel_delivery",
        "road_works_occupancy": "absent.road_works",
        "public_service_dispatch": "absent.public_service_dispatch",
        "large_event": "absent.event_injection",
        "infra_daily_load": "absent.power_water",
    }
    for pid, aid in attached.items():
        assert AB.by_id()[aid].world_process_id == pid


# ================================================================= 入力の宣言
def test_inputs_existing_five_filled_and_new_seven_fields_only():
    assert [d.id for d in INP.EXISTING] == ["input.weather", "input.timetable", "input.calendar",
                                            "input.external_nodes", "input.row_sales"]
    assert all(d.status == "filled" for d in INP.EXISTING)
    assert len(INP.NEW) == 7 and all(d.status == "fields_only" for d in INP.NEW)
    assert INP.INBOUND_GOODS.status == "fields_only"
    # 世界の台帳に記録の無い入力は置き場を書く(検収 低-4)
    assert {d.id for d in INP.EXISTING if not d.world_process_id} == {"input.calendar", "input.external_nodes",
                                                                       "input.row_sales"}
    assert all(d.carrier for d in INP.EXISTING if not d.world_process_id)
    assert "EXTERNAL_STORE_SALES_YEN=0" in INP.ROW_SALES.version
    assert INP.WEATHER.interpolation.startswith("無し") and "_heat_now" in INP.WEATHER.interpolation  # 中-2
    for d in INP.INPUTS:
        for row in d.source_rows:
            path = row.split(" ", 1)[0].split("(", 1)[0]
            assert (ROOT / path).is_file(), (d.id, row)


def test_inputs_attached_to_world_processes():
    reg = FB.build_registry()
    att = {p.id: p.input_decl.id for p in (*reg.processes, *reg.plan_specs) if p.input_decl is not None}
    assert att == {
        "weather": "input.weather",
        "delivery_inbound": "input.inbound_goods",
        "vehicle_cross_section": "input.through_traffic",
        "press_official_release": "input.ward_policy",
        "large_event": "input.event_info",
        "plan.rail_timetable": "input.timetable",
    }
    for pid, iid in att.items():
        assert INP.by_id()[iid].world_process_id == pid


def test_absence_type_is_frozen():
    a = AB.by_id()["absent.collapse"]
    assert isinstance(a, Absence)
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.statement = "x"  # type: ignore[misc]
