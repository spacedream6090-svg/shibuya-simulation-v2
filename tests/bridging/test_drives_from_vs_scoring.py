"""第340 段 2 の 2: 循環の機械検査(回答 11-01 §3)=``drives_from`` とパターン台帳の「採点する系」・``burned`` の突き合わせ。

- (a) ``drives_from`` に系 X を持つ過程/つなぎが、``contributes`` で X を採点する行に入っていたら重なり。系は行の ID と
  「採点する系」の欄の語(``data:<id>``=出典の系)のどちらでも見る(検収 中-1)。例外=その行が ``burned``/``外す``・
  その過程が「無い」と宣言済み**かつ** ``engine_stopped=True`` で、その行が宣言の錨に入る(検収 中-3・低-2)。
  〔11-02r/§1 #6〕例外の付かない重なりは **2 段**: 宣言の無い重なり=落とす/宣言つき(``circularity.KNOWN_CIRCULARITIES``
  =既知の循環・外す段つき)=警告(``warnings.warn``=CI のログに出る)。どの重なりにも当たらない宣言(古い宣言)も落とす。
  車→D5′ は D5′ を ``burned``(今は入力と重なるので採点できない)にしたので例外の側。
- (b) 回答 11-01 §3 の 3 件(宅配 W2・倒れる率 W3・β と E7)の宣言。
- (c) 疑いの行(routing §6-B と E5 の納品)の ``contributes`` を確かめ、代打の条件 ⑤ の重なり(系 ``stand_in``)も (a) と同じ
  2 段で見る(記録 s2-ledger-1101 README §3-1 の表と同じ値+11-02r の E5)。
- 〔11-02r/§1 #7〕「無い」の過程 5 件(ごみ収集・清掃・道路工事・救急の出動・電気と水)は ``engine.absent_processes`` の既定
  stopped で止めた=``engine_stopped=True``。まだ動くのは納品(入力の宣言)だけ。
"""

from __future__ import annotations

import warnings

import pytest

from shibuya.world.ledger import absent as AB
from shibuya.validation.static import circularity as CI
from shibuya.world.ledger import constitution as C
from shibuya.world.ledger import first_batch as FB


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


#: (a) の宣言つきの重なり(11-02r/§1 #6=警告・宣言は circularity.KNOWN_CIRCULARITIES)。一覧が変わったら気づく形に固定する。
#: 車: klass 既定はセンサス R3 の同じ行=D5 の出典の系(D5′ は burned で例外の側へ移った=11-02r §1 #6)。
#: 騒音: W10 の静的騒音場は都環境局 R5 の 7 点で残差を照合する=D12′ の系(D12′ は burned=要確認)。
#: W17: 週の表の元は社会生活基本調査=A5〜A7 の系(どの表かは未確認)。
DECLARED_OVERLAPS = {
    ("world_process:vehicle_cross_section", "data:road_census_r3", "D5"),
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
#: 〔11-02r §1 #6〕D5′ に移った例外(burned)の重なり(前の版は警告の側だった 2 件)。
BURNED_D5P = {
    ("world_process:vehicle_cross_section", "data:road_census_r3", "D5′"),
    ("bridge:DEC-109-driveCars", "data:road_census_r3", "D5′"),
}


# ================================================================= 欄
def test_pattern_ledger_has_scoring_and_burned_for_every_row(scoring):
    assert set(scoring) == set(C.PATTERN_IDS)
    for pid, ps in scoring.items():
        assert pid in ps.systems and ps.burned, pid
    # 〔11-02r §1 #6〕D5′ を burned(今は入力と重なるので採点できない)へ
    assert {p for p, s in scoring.items() if s.exempt} == {"F1", "F2", "F3", "W3", "D11′", "D5′"}
    assert scoring["D5′"].burned.startswith("burned") and scoring["E5"].burned.startswith("既知の循環")
    assert {p for p, s in scoring.items() if s.known} == {"E5"}
    # 出典の系(中-1)
    assert "data:road_census_r3" in scoring["D5′"].systems and "data:road_census_r3" in scoring["D5"].systems
    assert "data:tokyo_noise_r5" in scoring["D12′"].systems
    assert {"A4", "A5", "A6", "A7"} <= {p for p, s in scoring.items() if "data:ssb" in s.systems}
    # W3 の文(低-8)
    assert "W3 は錨に残す・体の式ができるまで検証から外す" in scoring["W3"].burned


def test_d5p_and_e5_are_on_the_validation_side(scoring):
    """〔11-02r/§1 #6〕D5′ は検証へ移し「今は入力と重なるので採点できない(burned)」、E5 は検証(既知の循環として宣言)。"""
    d5p, e5 = scoring["D5′"], scoring["E5"]
    assert "検証" in d5p.category and "較正" not in d5p.category
    assert d5p.exempt and "今は入力と重なるので採点できない" in d5p.burned
    assert "検証" in e5.category and "較正" not in e5.category
    assert e5.known and not e5.exempt
    assert "配送の入荷が店の発注と配達員の行動になる段" in e5.burned
    k = [x for x in CI.KNOWN_CIRCULARITIES if x.pattern_id == "E5"]
    # 〔検収 中-2・親の判断〕循環はユーザーの決定・外す段は親の案(決定の文に無い)=basis は inferred。出典を分けて書く
    assert len(k) == 1 and k[0].remove_at == "配送の入荷が店の発注と配達員の行動になる段" and k[0].basis == "inferred"
    assert k[0].system == CI.STAND_IN and k[0].decided == "11-02r/§1 #6"
    for text in (k[0].reason, e5.burned):
        assert "ユーザー決定" in text and "親の案(第342)" in text and "delivery_inbound" in text
    assert {x.basis for x in CI.KNOWN_CIRCULARITIES} == {"inferred"} and len(CI.KNOWN_CIRCULARITIES) == 9


def test_known_rows_in_the_pattern_ledger_have_a_declaration(scoring):
    """台帳の「既知の循環」の行には宣言の表の行がある(2 か所の突き合わせ)。宣言の行は台帳に有る ID だけ。"""
    declared = {k.pattern_id for k in CI.KNOWN_CIRCULARITIES}
    assert {p for p, s in scoring.items() if s.known} <= declared
    assert declared <= set(scoring)
    for k in CI.KNOWN_CIRCULARITIES:
        assert k.remove_at.strip() and k.reason.strip() and k.decided.startswith("11-02r/"), k
        assert not scoring[k.pattern_id].exempt, k  # 例外の行に宣言は要らない(宣言だけが残る)


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
    # 「既知の循環」の印は例外にしない(警告の側=11-02r §1 #6)
    sc4 = {"K": CI.PatternScoring("K", "K", "既知の循環(外す段: x)")}
    assert sc4["K"].known and not sc4["K"].exempt
    assert [o.exempt for o in CI.find_overlaps([CI.Subject("bridge", "b", ("K",), ("K",))], sc4)] == [""]


def _check_two_tiers(found: list, known=CI.KNOWN_CIRCULARITIES) -> list:
    """CI の 2 段: 宣言の無い重なりは落とす(AssertionError)・宣言つきは警告(warnings.warn=CI のログ)。警告の対を返す。"""
    fail, warn = CI.classify(found, known)
    for line in CI.warning_lines(warn):
        warnings.warn(line, UserWarning, stacklevel=2)
    bad = [o.as_dict() for o in fail]
    assert bad == [], f"宣言の無い重なり(burned でも、止めた無いの宣言でも、既知の循環の宣言でもない)=落とす: {bad}"
    return warn


def test_two_tiers_on_a_synthetic_example():
    """〔11-02r §1 #6〕合成の例: 宣言の無い重なりで落ち、宣言つきで警告だけ。例外(burned)はどちらにも入らない。"""
    sc = {"X1": CI.PatternScoring("X1", "X1", "—"), "X2": CI.PatternScoring("X2", "X2", "burned(較正)")}
    found = CI.find_overlaps([CI.Subject("world_process", "p", ("X1",), ("X1",)),
                              CI.Subject("bridge", "q", ("X2",), ("X2",))], sc)
    decl = (CI.KnownCircularity("X1", "X1", ("world_process:p",), "合成の循環", "外す段の例"),)
    # 宣言が無い=落ちる(例外の X2 は落ちる側に入らない)
    with pytest.raises(AssertionError, match="宣言の無い重なり"):
        _check_two_tiers(found, ())
    fail, warn = CI.classify(found, ())
    assert [(o.subject, o.pattern_id) for o in fail] == [("world_process:p", "X1")] and warn == []
    # 宣言つき=警告だけ(落ちない)
    with pytest.warns(UserWarning, match="既知の循環.*world_process:p の X1 → X1。外す段: 外す段の例"):
        got = _check_two_tiers(found, decl)
    assert [(o.subject, k.remove_at) for o, k in got] == [("world_process:p", "外す段の例")]
    # 主体が違えば宣言に当たらない=落ちる
    other = (CI.KnownCircularity("X1", "X1", ("world_process:zz",), "別の主体", "段"),)
    with pytest.raises(AssertionError):
        _check_two_tiers(found, other)
    assert CI.stale_declarations(found, other) == [(other[0], "world_process:zz")]
    assert CI.stale_declarations(found, decl) == []
    # 外す段の無い宣言は作れない
    with pytest.raises(ValueError, match="外す段"):
        CI.KnownCircularity("X1", "X1", ("world_process:p",), "理由", " ")


def test_no_undeclared_circularity(overlaps):
    """〔11-02r §1 #6〕例外の付かない重なりは全部宣言つき(警告)。宣言の無い重なりは 0(=落とす)。"""
    warn = _check_two_tiers(overlaps)
    got = {(o.subject, o.system, o.pattern_id) for o, _ in warn}
    assert got == DECLARED_OVERLAPS, "宣言つきの重なりが変わった=一覧と記録の表を直す"
    burned = {(o.subject, o.system, o.pattern_id) for o in overlaps if o.exempt == "burned" and o.pattern_id == "D5′"}
    assert burned == BURNED_D5P


def test_no_stale_declaration(overlaps):
    """どの重なりにも当たらない宣言は残さない(代打の条件 ⑤ の宣言は (c) で見る)。"""
    stale = [(k.pattern_id, k.system, subj) for k, subj in CI.stale_declarations(overlaps)
             if k.system != CI.STAND_IN]
    assert stale == []


def test_no_mismatch_after_rate_rules(overlaps):
    """宣言はあるがエンジンがまだ動かしている重なり(中-3)=率の規則を外す段(ce52662)の後は 0。"""
    assert sorted({(o.subject, o.pattern_id) for o in overlaps if CI.MISMATCH in o.detail}) == []


def test_engine_stopped_flags():
    """True=口が無い判断・採用と解雇・発注と、率の規則(``engine.rate_rules`` の既定 off)で止まった 5 件と、〔11-02r §1 #7〕
    「無い」の過程(``engine.absent_processes`` の既定 stopped)で止まった 5 件。まだ動くのは納品だけ。"""
    from shibuya.world.laws import switch_absent as AP
    from shibuya.world.laws import switch_rate as RR

    ab = AB.by_id()
    stopped_by_rate = {"absent.parcel_delivery": "parcels", "absent.collapse": "collapse",
                       "absent.event_injection": "event_injection", "absent.litter": "litter",
                       "absent.discard_unsold": "leftover_waste"}
    assert RR.DEFAULT_MODE == RR.MODE_OFF
    for aid, rule in stopped_by_rate.items():
        assert ab[aid].engine_stopped and rule in RR.RULES and rule in ab[aid].engine_now, aid
    stopped_by_absent = {v["absent"]: k for k, v in AP.STOPPED_PROCESSES.items()}
    assert set(stopped_by_absent) == {"absent.waste_collection", "absent.street_cleaning", "absent.road_works",
                                      "absent.public_service_dispatch", "absent.power_water"}
    assert AP.DEFAULT_MODE == AP.MODE_STOPPED
    for aid, name in stopped_by_absent.items():
        a = ab[aid]
        assert a.engine_stopped and name in AP.PROCESSES and f"「無い」の過程 {name}" in a.engine_now, aid
        assert a.world_process_id == AP.STOPPED_PROCESSES[name]["world_process"] and a.stage == "next-bump", aid
    assert [a.id for a in AB.ABSENCES if not a.engine_stopped] == ["absent.inbound_delivery"]
    assert {a.id for a in AB.ABSENCES if a.engine_stopped} == (
        {a.id for a in AB.NO_PORT + AB.NO_PORT_EXTRA} | set(stopped_by_rate) | set(stopped_by_absent)
        | {"absent.hiring_firing", "absent.ordering"})


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


# ================================================================= (c) 疑いの行(routing §6-B・回答 11-01 §3・11-02r §1 #6)
#: (疑い, 行, 結ぶ過程, 疑いの錨, 期待する ⑤ の重なり, drives_from の重なり)=記録 README §3-1 の表(+11-02r の納品→E5)。
#: 〔11-02r §1 #6〕車→D5′ の drives_from の重なりは D5′ の burned で例外の側へ移った(False)。
SUSPECTS = (
    ("席 30 分→D8", "DEC-31-leaveSeat", "indoor_occupancy", ("D8",), ("D8",), False),
    ("補充→W1/E5", "DEC-98-restock", "shelf_stock_restock", ("W1", "E5"), ("W1", "E5"), False),
    ("納品→E5", "DEC-102-inboundDelivery", "delivery_inbound", ("E5",), ("E5",), False),
    ("家で使う→W1", "DEC-41-homeUse", "goods_conservation", ("W1",), ("W1",), False),
    ("車→D5′", "DEC-109-driveCars", "vehicle_cross_section", ("D5′",), ("D5′",), False),
    ("バス→D11′", "DEC-108-runBuses", "bus_taxi_operation", ("D11′",), (), False),
)


def _stand_in_overlaps(reg, scoring) -> list:
    """疑いの行の ⑤ の重なりを系 ``stand_in`` の Overlap に(例外の行=burned/外す は exempt の印)。"""
    procs = {x.id: x for x in (*reg.processes, *reg.plan_specs)}
    out = []
    for _label, row, proc, anchors, _e5, _ed in SUSPECTS:
        for a in CI.stand_in_overlap(procs[proc].contributes, anchors):
            ps = scoring.get(a)
            out.append(CI.Overlap(f"bridge:{row}", CI.STAND_IN, a, "burned" if ps is not None and ps.exempt else ""))
    return out


@pytest.mark.parametrize("label,row,proc,anchors,expect5,expect_drive", SUSPECTS, ids=[s[0] for s in SUSPECTS])
def test_suspect_rows_contributes(reg, by_id, overlaps, label, row, proc, anchors, expect5, expect_drive):
    assert by_id[row]["world_process"] == proc
    p = {x.id: x for x in (*reg.processes, *reg.plan_specs)}[proc]
    got5 = CI.stand_in_overlap(p.contributes, anchors)
    assert got5 == expect5, (label, p.contributes)
    drive = any(o.pattern_id in anchors and o.subject.endswith((proc, row)) and not o.exempt for o in overlaps)
    assert drive is expect_drive, label


def test_stand_in_overlaps_are_declared(reg, scoring):
    """〔11-02r §1 #6〕代打の条件 ⑤ の重なりも 2 段: 宣言の無いものは落とす・宣言つきは警告。宣言は全部当たる。"""
    found = _stand_in_overlaps(reg, scoring)
    warn = _check_two_tiers(found)
    assert {(o.subject, o.pattern_id) for o, _ in warn} == {
        ("bridge:DEC-31-leaveSeat", "D8"), ("bridge:DEC-98-restock", "W1"), ("bridge:DEC-98-restock", "E5"),
        ("bridge:DEC-102-inboundDelivery", "E5"), ("bridge:DEC-41-homeUse", "W1")}
    # 車→D5′ の ⑤ は D5′ の burned で例外の側
    assert [(o.subject, o.exempt) for o in found if o.pattern_id == "D5′"] == [("bridge:DEC-109-driveCars", "burned")]
    known5 = tuple(k for k in CI.KNOWN_CIRCULARITIES if k.system == CI.STAND_IN)
    assert CI.stale_declarations(found, known5) == []


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
    # 回答 11-01 §2 の 9 件(#101=Calvo)+ routing の「すぐ外せる」(#104・106・110・111)+〔11-02r §1 #7〕既定で止めた「無い」の
    # 過程のうち、もとは別の段だった #43(電気と水=7)と #103(ごみ収集=6-6)
    assert nb == [2, 3, 10, 22, 42, 43, 83, 99, 101, 103, 104, 105, 106, 110, 111]
