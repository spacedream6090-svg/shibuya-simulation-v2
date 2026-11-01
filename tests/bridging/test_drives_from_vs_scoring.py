"""第340 段 2 の 2: 循環の機械検査(回答 11-01 §3)=``drives_from`` とパターン台帳の「採点する系」・``burned`` の突き合わせ。

- (a) ``drives_from`` に系 X を持つ過程/つなぎが、``contributes`` で X を採点する行に入っていたら落とす。系は行の ID と
  「採点する系」の欄の語(``data:<id>``=出典の系)のどちらでも見る(検収 中-1)。例外=その行が ``burned``/``外す``・
  その過程が「無い」と宣言済み**かつ** ``engine_stopped=True`` で、その行が宣言の錨に入る(検収 中-3・低-2)。
  疑いの行(車→D5′・D5、騒音→D12′、W17→A5〜A7)は警告の印で通す=落とすのは親が決める。
  〔検収 中-3〕率の規則を外す段(ce52662・既定 off)の後なので、宅配の W2 は engine_stopped=True の宣言で例外に入る。
- (b) 回答 11-01 §3 の 3 件(宅配 W2・倒れる率 W3・β と E7)の宣言。
- (c) 疑いの 5 行(routing §6-B)の ``contributes`` を確かめて表にする(記録 README §3-1 の表と同じ値)。
"""

from __future__ import annotations

import warnings

import pytest

from shibuya.world.processes import absent as AB
from shibuya.world.processes import circularity as CI
from shibuya.world.processes import constitution as C
from shibuya.world.processes import first_batch as FB


@pytest.fixture(scope="module")
def reg():
    return FB.build_registry()


@pytest.fixture(scope="module")
def scoring():
    return CI.parse_pattern_scoring()


@pytest.fixture(scope="module")
def rows():
    return CI.load_ledger_rows()


@pytest.fixture(scope="module")
def by_id(rows):
    return {r["id"]: r for r in rows}


@pytest.fixture(scope="module")
def subjects(reg, rows):
    return CI.subjects_from_registry(reg) + CI.subjects_from_ledger(rows, reg)


@pytest.fixture(scope="module")
def overlaps(subjects, scoring):
    return CI.find_overlaps(subjects, scoring)


#: (a) の疑いの重なり(落とさず警告の印・親が決める)。
#: 車: klass 既定はセンサス R3 の同じ行=D5′・D5 の出典の系(回答 11-01 §10-1「D5′ を較正から検証へ」・§10-2 の区間の分け方)。
#: 騒音: W10 の静的騒音場は都環境局 R5 の 7 点で残差を照合する=D12′ の系(D12′ は burned=要確認)。
#: W17: 週の表の元は社会生活基本調査=A5〜A7 の系(どの表かは未確認)。
SUSPECT_OVERLAPS = {
    ("world_process:vehicle_cross_section", "data:road_census_r3", "D5′"),
    ("world_process:vehicle_cross_section", "data:road_census_r3", "D5"),
    ("bridge:DEC-109-driveCars", "data:road_census_r3", "D5′"),
    ("bridge:DEC-109-driveCars", "data:road_census_r3", "D5"),
    ("world_process:static_noise_field", "data:tokyo_noise_r5", "D12′"),
    ("bridge:DEC-63-weeklyPlan", "data:ssb", "A5"),
    ("bridge:DEC-63-weeklyPlan", "data:ssb", "A6"),
    ("bridge:DEC-63-weeklyPlan", "data:ssb", "A7"),
    ("bridge:DEC-69-sleepOnPlan", "data:ssb", "A5"),
    ("bridge:DEC-69-sleepOnPlan", "data:ssb", "A6"),
    ("bridge:DEC-71-wakeUp", "data:ssb", "A5"),
    ("bridge:DEC-71-wakeUp", "data:ssb", "A6"),
}


# ================================================================= 欄
def test_pattern_ledger_has_scoring_and_burned_for_every_row(scoring):
    assert set(scoring) == set(C.PATTERN_IDS)
    for pid, ps in scoring.items():
        assert pid in ps.systems and ps.burned, pid
    assert {p for p, s in scoring.items() if s.exempt} == {"F1", "F2", "F3", "W3", "D11′"}
    assert scoring["D5′"].burned.startswith("—") and scoring["E5"].burned.startswith("要確認")
    # 出典の系(中-1)
    assert "data:road_census_r3" in scoring["D5′"].systems and "data:road_census_r3" in scoring["D5"].systems
    assert "data:tokyo_noise_r5" in scoring["D12′"].systems
    assert {"A4", "A5", "A6", "A7"} <= {p for p, s in scoring.items() if "data:ssb" in s.systems}
    # W3 の文(低-8)
    assert "W3 は錨に残す・体の式ができるまで検証から外す" in scoring["W3"].burned


def test_drives_from_values_are_known_systems(reg, rows, scoring):
    ok = set(C.PATTERN_IDS)
    systems = {x for s in scoring.values() for x in s.systems}
    vals = [v for p in (*reg.processes, *reg.plan_specs) for v in p.drives_from]
    vals += [v for r in rows for v in r.get("drives_from", ())]
    assert vals
    for v in vals:
        assert v in ok or v == "none" or v.startswith(("data:", "input:")), v
    # data の語は「採点する系」の語とそろえる(両方に出る語の一覧を固定=語が割れたら気づく)
    data_words = {v for v in vals if v.startswith("data:")}
    assert data_words & systems == {"data:road_census_r3", "data:tokyo_noise_r5", "data:ssb", "data:pt2018"}
    procs = {p.id for p in (*reg.processes, *reg.plan_specs)}
    for r in rows:
        if r.get("world_process"):
            assert r["world_process"] in procs, (r["id"], r["world_process"])
        for c in [*r.get("contributes", ()), *r.get("calibration_declined", ())]:
            assert c in ok, (r["id"], c)


def test_every_declared_process_has_drives_from(reg):
    """世界の台帳の過程と PlanSpec は全部 drives_from を書いた(未記入は 0)。"""
    assert [p.id for p in (*reg.processes, *reg.plan_specs) if not p.drives_from] == []


# ================================================================= (a) 突き合わせ
def test_negative_control_overlap_fails_unless_burned_or_stopped_absence():
    sc = {"X1": CI.PatternScoring("X1", "X1", "—"), "X2": CI.PatternScoring("X2", "X2", "burned(較正)")}
    s = CI.Subject("world_process", "p", ("X1",), ("X1",))
    assert [o.exempt for o in CI.find_overlaps([s], sc)] == [""]
    assert [o.exempt for o in CI.find_overlaps([CI.Subject("bridge", "b", ("X2",), ("X2",))], sc)] == ["burned"]
    stopped = CI.Subject("world_process", "p", ("X1",), ("X1",), "absent.x", True, ("X1",))
    assert [o.exempt for o in CI.find_overlaps([stopped], sc)] == ["absent"]
    # 宣言はあるが規則がまだ動く=例外にしない(中-3)
    running = CI.Subject("world_process", "p", ("X1",), ("X1",), "absent.x", False, ("X1",))
    got = CI.find_overlaps([running], sc)
    assert [o.exempt for o in got] == [""] and CI.MISMATCH in got[0].detail
    # 宣言の錨に入らない行は例外にしない(低-2)
    other = CI.Subject("bridge", "b", ("X1",), ("X1",), "absent.x", True, ("X9",))
    assert [o.exempt for o in CI.find_overlaps([other], sc)] == [""]
    assert CI.find_overlaps([CI.Subject("world_process", "p", ("none",), ("X1",))], sc) == []
    assert CI.find_overlaps([CI.Subject("world_process", "p", ("X1",), ("X2",))], sc) == []
    # 「採点する系」で出典の系を名指しした行も重なる(中-1)
    sc2 = {"Y": CI.PatternScoring("Y", "Y・data:z", "—")}
    assert [o.pattern_id for o in CI.find_overlaps([CI.Subject("bridge", "b", ("data:z",), ("Y",))], sc2)] == ["Y"]
    sc3 = {"Z": CI.PatternScoring("Z", "Z", "要確認(較正に使用)")}
    assert [o.exempt for o in CI.find_overlaps([CI.Subject("bridge", "b", ("Z",), ("Z",))], sc3)] == [""]


def test_no_unexpected_circularity(overlaps):
    """〔中-3〕率の規則を外す前は宅配(W2)で落ちた(宣言と実装が食い違う)。いまは無いの宣言で通る。"""
    found = {(o.subject, o.system, o.pattern_id) for o in overlaps if not o.exempt}
    for o in sorted(found & SUSPECT_OVERLAPS):
        warnings.warn(f"循環の疑い(親が決める): {o}", UserWarning, stacklevel=1)
    bad = [o.as_dict() for o in overlaps if not o.exempt and (o.subject, o.system, o.pattern_id) not in SUSPECT_OVERLAPS]
    assert bad == [], f"drives_from と採点する系が重なる(burned でも、止めた無いの宣言でもない): {bad}"
    assert found == SUSPECT_OVERLAPS, "疑いの重なりが変わった=一覧と記録の表を直す"


def test_no_mismatch_after_rate_rules(overlaps):
    """宣言はあるがエンジンがまだ動かしている重なり(中-3)=率の規則を外す段(ce52662)の後は 0。"""
    assert sorted({(o.subject, o.pattern_id) for o in overlaps if CI.MISMATCH in o.detail}) == []


def test_engine_stopped_flags():
    """True=口が無い判断・採用と解雇・発注と、率の規則(``engine.rate_rules`` の既定 off)で止まった 5 件。
    まだ動く 5 件(ごみ収集・清掃・道路工事・救急の出動の過程そのもの・電気と水)と納品は False。"""
    from shibuya.engine import rate_rules as RR

    ab = AB.by_id()
    stopped_by_rate = {"absent.parcel_delivery": "parcels", "absent.collapse": "collapse",
                       "absent.event_injection": "event_injection", "absent.litter": "litter",
                       "absent.discard_unsold": "leftover_waste"}
    assert RR.DEFAULT_MODE == RR.MODE_OFF
    for aid, rule in stopped_by_rate.items():
        assert ab[aid].engine_stopped and rule in RR.RULES and rule in ab[aid].engine_now, aid
    still = {"absent.waste_collection", "absent.street_cleaning", "absent.road_works",
             "absent.public_service_dispatch", "absent.power_water", "absent.inbound_delivery"}
    assert all(not ab[i].engine_stopped for i in still)
    assert {a.id for a in AB.ABSENCES if a.engine_stopped} == (
        {a.id for a in AB.NO_PORT + AB.NO_PORT_EXTRA} | set(stopped_by_rate) | {"absent.hiring_firing", "absent.ordering"})


# ================================================================= (b) 回答 11-01 §3 の 3 件
def test_case_parcel_delivery_w2_is_absent_and_w2_stays_an_anchor(reg, scoring, overlaps):
    p = {x.id: x for x in reg.processes}["delivery_last_mile"]
    assert p.drives_from == ("W2",) and "W2" in p.contributes
    assert p.absence is not None and p.absence.kind == "no_actor" and p.absence.keeps_anchor == ("W2",)
    assert "宅配は世界に無い" in p.absence.statement
    assert not scoring["W2"].exempt  # W2 は錨に残す(burned にしない)
    hits = [o for o in overlaps if o.pattern_id == "W2"]
    assert hits
    want = "absent" if p.absence.engine_stopped else ""
    assert all(o.exempt == want for o in hits)


def test_case_collapse_rate_w3_is_out_of_validation_until_the_body_formula(scoring, overlaps, by_id):
    assert scoring["W3"].burned.startswith("外す") and "体の式" in scoring["W3"].burned
    assert by_id["DEC-83-collapse"]["drives_from"] == ["W3"] and by_id["DEC-83-collapse"]["contributes"] == ["W3"]
    hits = [o for o in overlaps if o.pattern_id == "W3"]
    assert {o.subject for o in hits} == {"world_process:public_service_dispatch", "bridge:DEC-83-collapse",
                                         "bridge:DEC-110-dispatch"}
    assert all(o.exempt == "burned" for o in hits)
    for aid in ("absent.collapse", "absent.public_service_dispatch"):
        a = AB.by_id()[aid]
        assert a.keeps_anchor == ("W3",) and "W3 は錨に残す・体の式ができるまで検証から外す" in a.statement


def test_case_price_beta_is_not_calibrated_to_e7(subjects, scoring, by_id):
    assert all("E7" not in s.drives_from for s in subjects)
    r = by_id["DEC-101-changePrice"]
    assert r["calibration_declined"] == ["E7"] and r["drives_from"] == ["none"]
    assert not scoring["E7"].exempt  # E7 は検証に残す
    assert AB.by_id()["absent.change_price"].keeps_anchor == ("E7",)


# ================================================================= (c) 疑いの 5 行(routing §6-B・回答 11-01 §3)
#: (疑い, 行, 結ぶ過程, 疑いの錨, 期待する ⑤ の重なり, drives_from の重なり)=記録 README §3-1 の表。
SUSPECTS = (
    ("席 30 分→D8", "DEC-31-leaveSeat", "indoor_occupancy", ("D8",), ("D8",), False),
    ("補充→W1/E5", "DEC-98-restock", "shelf_stock_restock", ("W1", "E5"), ("W1", "E5"), False),
    ("家で使う→W1", "DEC-41-homeUse", "goods_conservation", ("W1",), ("W1",), False),
    ("車→D5′", "DEC-109-driveCars", "vehicle_cross_section", ("D5′",), ("D5′",), True),
    ("バス→D11′", "DEC-108-runBuses", "bus_taxi_operation", ("D11′",), (), False),
)


@pytest.mark.parametrize("label,row,proc,anchors,expect5,expect_drive", SUSPECTS, ids=[s[0] for s in SUSPECTS])
def test_suspect_rows_contributes(reg, by_id, overlaps, label, row, proc, anchors, expect5, expect_drive):
    assert by_id[row]["world_process"] == proc
    p = {x.id: x for x in (*reg.processes, *reg.plan_specs)}[proc]
    got5 = CI.stand_in_overlap(p.contributes, anchors)
    assert got5 == expect5, (label, p.contributes)
    drive = any(o.pattern_id in anchors and o.subject.endswith((proc, row)) and not o.exempt for o in overlaps)
    assert drive is expect_drive, label
    if got5:
        warnings.warn(f"代打の出力が錨に入る疑い(⑤・親が決める): {label} → {got5}", UserWarning, stacklevel=1)


# ================================================================= 外す段の 2 か所(中-4)
def test_absence_stage_matches_the_dec_row(by_id):
    decs = {r["routing_row"]: r for r in by_id.values() if r["id"].startswith("DEC-")}
    for a in AB.ABSENCES:
        if a.routing_rows:
            assert a.stage == decs[a.routing_rows[0]]["remove_at"], (a.id, a.stage)
        else:
            assert a.stage == "7", a.id


def test_next_bump_rows(by_id):
    nb = sorted(r["routing_row"] for r in by_id.values() if r["id"].startswith("DEC-") and r["remove_at"] == "next-bump")
    # 回答 11-01 §2 の 9 件(#101=Calvo)+ routing の「すぐ外せる」(#104・106・110・111)
    assert nb == [2, 3, 10, 22, 42, 83, 99, 101, 104, 105, 106, 110, 111]
