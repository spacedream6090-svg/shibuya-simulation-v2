"""第 6 期 6-2 カレンダー 3 のランの試験(合成 80 体・組織と雇用の行つき): 雇い主が週 1 回だけ組む・正規は触らない・候補の枠が W20 の
約束の形から来る(労働時間の行と営業時間は読むだけ=超えたら記録)・働く人の行がカレンダー 2 の形で入る・休みの申し出 → 受ける/断るが
本人の判断・C3 の連絡が C1 の口を通る(監査 0)・祝日の日付のラン・2 日(日 → 月)と再開=通し・段 B 0・記録 on/off 同じ・既定 off で
層が無い・腕の取り違えの再開は止まる・CLI・AST の負の対照(エンジンが時刻や中身を決める直書きが無い)。"""

from __future__ import annotations

import ast
import dataclasses
from collections import Counter
from pathlib import Path

import pytest

from shibuya.engine import manifest_sections as MS
from shibuya.engine import resume as RS
from shibuya.engine import state_ledger as SL
from shibuya.engine.calendar2 import book as B2
from shibuya.engine.calendar3 import arm as A3
from shibuya.engine.calendar3 import layer as LY
from shibuya.engine.calendar3 import port as P3
from shibuya.engine.contact import layer as CL
from shibuya.engine.contact import port as PC
from shibuya.engine.run import run_day
from shibuya.engine.systems import table as TB

from tests.engine.calendar3._ca3 import (FRAME_LONG, HOLIDAY_SUNDAY, KW, MANAGER, STEP_NS, TPD, UNIT, by_pref, ca3,
                                         choose, roster_fixture)

SRC = Path(__file__).resolve().parents[3] / "src" / "shibuya" / "engine" / "calendar3"


@pytest.fixture
def with_roster(monkeypatch):
    roster_fixture(monkeypatch)
    yield


def _work(r):
    return [e for e in r.event_log.events() if str(e.what).startswith("勤務:")]


# ================================================================= 既定 off・腕の前提
def test_default_off_builds_nothing(tmp_path):
    """既定 off: 層・manifest の節・状態のファイルの calendar3.* の項・設定の指紋の鍵・勤務の族の出来事・C1 の控えの口が 0。"""
    with ca3(on=False, trial=False, contact=False, calendar2=False):
        r = run_day(state_out=tmp_path / "state", stop_at_tick=120,
                    **dict(KW, ticks=240, start_sim_datetime=None))
    assert getattr(r, "calendar3_layer", "missing") is None
    m = r.run_manifest_fields()
    assert [k for k in m if k == "calendar_3"] == []
    assert sum(1 for e in r.event_log.events() if str(e.what).startswith("勤務:")) == 0
    bundle = RS.read_state(tmp_path / "state" / r.resume["state_files"][-1]["file"])
    assert [p for p in bundle.items if p.startswith("calendar3.")] == []
    assert [k for k in bundle.header["fingerprint"] if k == A3.FP_KEY] == []
    assert "calendar_3" not in m["calls_by_model"]
    assert TB.SPECS["calendar_3"].when == "calendar3"


def test_arm_needs_contact_and_calendar2(with_roster):
    with ca3(contact=False), pytest.raises(ValueError, match="--contact c1"):
        run_day(**dict(KW, ticks=10))
    with ca3(calendar2=False), pytest.raises(ValueError, match="--calendar-2 arm"):
        run_day(**dict(KW, ticks=10))


def test_sunday_start_without_the_trial_mark_still_stops(with_roster):
    """試験用の印の無いランは開始日の検査を今のまま止める(日曜始まり)。"""
    with ca3(trial=False), pytest.raises(ValueError, match="月曜でない"):
        run_day(**dict(KW, ticks=10))


# ================================================================= 腕 arm の合成のラン(日曜 1 日)
@pytest.fixture(scope="module")
def sunday_run():
    mp = pytest.MonkeyPatch()
    roster_fixture(mp)
    try:
        with ca3():
            r = run_day(**KW)
    finally:
        mp.undo()
    return r


def test_employer_composes_once_a_week_for_weekly_workers_only(sunday_run):
    r = sunday_run
    lay = r.calendar3_layer
    ro = lay.roster
    m = r.run_manifest_fields()["calendar_3"]
    assert m["trial"]["mark"] == A3.TRIAL_MARK and any("月曜でない" in v for v in m["trial"]["start_rule_violations"])
    assert m["composed"]["units"] == ro.n_units and m["composed"]["begun"] == len(lay.sched_units)
    assert m["composed"]["begun_on_trial_day0"] == 1  # 日曜始まり=試験用の印の 0 日目の頭に 1 回(金曜は来ない)
    assert m["composed"]["workers"] == len(ro.unit_of)
    assert set(lay._composed.values()) == {1}  # 翌週の最初の日(月曜=1 日目)
    frames = [e for e in _work(r) if e.what == LY.W_FRAME]
    # 週 1 回だけ: 雇い主ごと・働く人ごとに 7 日ぶん 1 回ずつ(組んだ刻みは雇い主ごとに 1 つ)
    assert len(frames) == 7 * len(ro.unit_of)
    by_emp: dict[int, set[int]] = {}
    for e in frames:
        by_emp.setdefault(int(e.who), set()).add(int(e.t_ns) // STEP_NS)
        assert int(e.who) == ro.scheduler[ro.unit_of[int(e.whom)]]  # 組むのはその単位のシフトを組む人
    assert all(len(v) == 1 for v in by_emp.values())
    assert MANAGER in by_emp  # 店長の役割の体が組む
    # 正規(毎週固定=偶数の体)は触らない: 勤務の行も枠の判断も無い
    assert all(int(e.whom) % 2 == 1 for e in frames)
    assert all(int(row["owner"]) % 2 == 1 for row in lay.book.rows.values() if row["kind"] == B2.K_WORK)


def test_work_rows_have_the_calendar2_form(sunday_run):
    r = sunday_run
    lay = r.calendar3_layer
    rows = [row for row in lay.book.rows.values() if row["kind"] == B2.K_WORK]
    assert rows
    for row in rows:
        assert row["placement"] == B2.PL_APP and row["certain"] == 1 and row["state"] in (B2.ST_LIVE, B2.ST_CANCELLED)
        assert len(row["origin"]) == 3 and row["origin"][0] in ("メッセージ", "グループ", "通話", "本人")
        info = lay._work_rows[int(row["id"])]
        assert row["with"] == [info[2]] and int(row["owner"]) == info[0]
        start_min = (int(row["start_ns"]) % (TPD * STEP_NS)) // (60 * 10 ** 9)
        assert int(row["start_ns"]) // (TPD * STEP_NS) == info[3] >= 1  # 翌週の日
        assert [start_min, (int(row["end_ns"]) - int(row["start_ns"])) // (60 * 10 ** 9)] in (
            [540, 480], [600, 480], [480, 600])  # W20 の約束の形の枠のどれか
    writes = [e for e in _work(r) if e.what == LY.W_WRITE]
    assert len(writes) == r.run_manifest_fields()["calendar_3"]["rows"]["written"] >= len(rows)


def test_c3_contacts_go_through_the_c1_mouth_and_audits_are_clean(sunday_run):
    r = sunday_run
    evs = list(r.event_log.events())
    assert LY.audit_causes(evs, step_ns=STEP_NS, issued=r.calendar3_layer.issued_keys())["violations"] == 0
    assert CL.audit_causes(evs, step_ns=STEP_NS, issued=r.contact_layer.issued_keys())["violations"] == 0
    c = r.run_manifest_fields()["calendar_3"]["contacts"]
    sent = sum(v for k, v in c.items() if k.startswith("sent:"))
    assert sent > 0 and c.get("received:シフトの知らせ", 0) > 0
    assert c["c1_judge_calls"] >= sent  # 送る判断(宛先と手段)は C1 の判断の口
    cm = r.contact_layer._meter
    assert sum(v for k, v in cm.items() if k.startswith("c3:") and not k.startswith("c3:cannot")) == sent
    # 送った C3 の連絡は C1 の「送った」か「電話をかけた」の行(原因=C1 の宛先の判断)
    whom = [e for e in evs if e.what in (CL.W_SENT, CL.W_DIAL)]
    assert whom and all(PC.purpose_of_serial(PC.parse_call_id(e.cause.call_id)[2]) in (PC.P_WHOM, PC.P_GROUP,
                                                                                          PC.P_REPLY, PC.P_STAMP)
                        for e in whom if PC.parse_call_id(e.cause.call_id) is not None)


def test_labor_rows_and_store_hours_are_only_recorded(sunday_run):
    m = sunday_run.run_manifest_fields()["calendar_3"]
    assert m["labor"]["enforced"] is False and m["labor"]["max_hours_per_day"] == 8
    over = m["labor_over"]
    # 水曜の長い枠(10 時間)を雇い主が選べば 1 日 8 時間を超える=記録だけ(止めない=枠はそのまま知らせる)
    long_rows = [row for row in sunday_run.calendar3_layer.book.rows.values()
                 if row["kind"] == B2.K_WORK and int(row["end_ns"]) - int(row["start_ns"])
                 == (FRAME_LONG[1] - FRAME_LONG[0]) * 60 * 10 ** 9]
    if long_rows:
        assert over.get("over_day_hours", 0) > 0
    hist = m["work_days_per_week"]
    assert sum(hist.values()) == m["composed"]["workers"]


def test_manifest_section_and_calls_by_model(sunday_run):
    r = sunday_run
    m = r.run_manifest_fields()
    cc = m["calendar_3"]
    assert set(cc) == set(LY.CONFIG_KEYS) | set(LY.OBSERVED_KEYS)
    assert {p.split(".", 1)[1] for p, s in MS.PATHS.items() if p.startswith("calendar_3.") and s == MS.CONFIG} \
        == set(LY.CONFIG_KEYS)
    assert {p.split(".", 1)[1] for p, s in MS.PATHS.items() if p.startswith("calendar_3.") and s == MS.OBSERVED} \
        == set(LY.OBSERVED_KEYS)
    assert MS.unlisted_in_mixed(m) == []
    j3, t3 = r.calendar3_layer.model_calls()
    cbm = m["calls_by_model"]
    assert cbm["calendar_3"] == {"judge_model": j3, "llm": t3} and j3 > 0
    jc, _tc = r.contact_layer.model_calls()
    j2, _t2 = r.calendar2_layer.model_calls()
    assert cbm["judge_model"] == j3 + jc + j2
    assert cc["common_knowledge"]["line"].startswith("今日は 7 月 26 日(日)")


# ================================================================= 休みの申し出(本人の判断)
def test_rest_request_answer_and_apply_are_decisions(with_roster, monkeypatch):
    with choose(monkeypatch, by_pref(P3.K_ASK_REST, P3.K_ACCEPT, P3.K_APPLY, "frame:0")), ca3():
        r = run_day(**KW)
    by = Counter(e.what for e in _work(r))
    assert by[LY.W_ASK_REST] > 0 and by[LY.W_ACCEPT] > 0 and by[LY.W_DECLINE] == 0
    assert LY.audit_causes(r.event_log.events(), step_ns=STEP_NS,
                           issued=r.calendar3_layer.issued_keys())["violations"] == 0
    m = r.run_manifest_fields()["calendar_3"]
    assert m["rest"]["accept_rate"] == 1.0
    # 返事を読んだ働く人だけが自分の行を休みにした(雇い主の行・ほかの人の行は変わらない)
    lay = r.calendar3_layer
    cancelled = [row for row in lay.book.rows.values() if row["kind"] == B2.K_WORK and row["state"] == B2.ST_CANCELLED]
    assert len(cancelled) == by[LY.W_APPLY] == m["rest"].get("applied", 0)
    applied = {int(e.who) for e in _work(r) if e.what == LY.W_APPLY}
    assert {int(row["owner"]) for row in cancelled} == applied
    # 雇い主の記録も受けた日を休みに直した
    for e in (e for e in _work(r) if e.what == LY.W_ACCEPT):
        assert int(e.who) == lay.roster.scheduler[lay.roster.unit_of[int(e.whom)]]


def test_declined_rest_keeps_the_row(with_roster, monkeypatch):
    with choose(monkeypatch, by_pref(P3.K_ASK_REST, P3.K_DECLINE, P3.K_APPLY, "frame:0")), ca3():
        r = run_day(**dict(KW, ticks=TPD // 2))
    by = Counter(e.what for e in _work(r))
    assert by[LY.W_DECLINE] > 0 and by[LY.W_ACCEPT] == 0 and by[LY.W_APPLY] == 0


# ================================================================= 祝日の日付のラン(試験用の印)
def test_holiday_run_is_common_knowledge_and_runs(with_roster, monkeypatch):
    seen: list[str] = []

    def rule(ctx, presented):
        seen.extend(c.text for c in presented)
        return sorted(presented, key=lambda c: (c.kind, c.id))[0].id

    with choose(monkeypatch, rule), ca3():
        r = run_day(**dict(KW, sim_days=2, start_sim_datetime=HOLIDAY_SUNDAY))
    m = r.run_manifest_fields()["calendar_3"]
    assert any("海の日" in t for t in seen)  # 日の言葉は暦の常識の口(祝日の名つき)
    assert m["holiday"].get("ランの中の祝日", 0) == 1
    assert m["holiday"].get("frames_off", 0) + m["holiday"].get("frames_work", 0) == m["composed"]["workers"]
    assert any("祝日" in v or "連続する平日" in v for v in m["trial"]["start_rule_violations"])
    assert LY.audit_causes(r.event_log.events(), step_ns=STEP_NS,
                           issued=r.calendar3_layer.issued_keys())["violations"] == 0


# ================================================================= 2 日(日 → 月)と再開
def _cp(r):
    return [(int(c.tick), c.behavior_hash, c.full_hash) for c in r.checkpoints if int(c.tick) >= TPD]


def test_two_days_sunday_to_monday_and_resume_is_the_straight_run(with_roster, tmp_path):
    kw = dict(KW, sim_days=2)
    with ca3():
        straight = run_day(tape_path=tmp_path / "s", **kw)
        a = run_day(state_out=tmp_path / "state", stop_at_tick=TPD, tape_path=tmp_path / "a", **kw)
        path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
        b = run_day(resume_from=path, tape_path=tmp_path / "b", **kw)
    assert b.final_hash == straight.final_hash and _cp(b) == _cp(straight) and _cp(b)
    bundle = RS.read_state(path)
    arm_paths = [p for _k, p in SL.arm_items({"calendar3": a.calendar3_layer}, behavior=False)]
    assert arm_paths and set(arm_paths) <= set(bundle.items)
    assert bundle.header["fingerprint"][A3.FP_KEY] == {"arm": "arm", "trial": "on"}
    ms, mb = straight.run_manifest_fields()["calendar_3"], b.run_manifest_fields()["calendar_3"]
    for k in ("roster", "composed", "work_days_per_week", "rest", "contacts", "rows", "late", "labor_over", "live", "calls"):
        assert ms[k] == mb[k], k
    # 月曜(1 日目)に勤務の行の知らせが鳴り、遅れの判断の機会がある
    assert ms["rows"].get("notified", 0) > 0


def test_resuming_with_the_arm_off_stops(with_roster, tmp_path, monkeypatch):
    from shibuya.engine.calendar import SimCalendar

    kw = dict(KW, sim_days=2)
    with ca3():
        a = run_day(state_out=tmp_path / "state", stop_at_tick=TPD, **kw)
    path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
    monkeypatch.setattr(SimCalendar, "check_start", lambda self, n=1: [])  # 日曜始まりの検査を外して指紋の照合まで進める
    with ca3(on=False), pytest.raises(ValueError, match="calendar_3"):
        run_day(resume_from=path, **kw)


# ================================================================= 段 B・記録 on/off・腕の行・系の宣言・CLI
def test_stage_b_has_no_undeclared_writes(with_roster, monkeypatch):
    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "1")
    with ca3():
        r = run_day(**dict(KW, ticks=360))
    c = r.run_manifest_fields()["calendar_3"]
    assert c["composed"]["units"] > 0 and sum(v for k, v in c["contacts"].items() if k.startswith("received:")) > 0


def test_stage_b_negative_control_without_the_read_declaration_fails(with_roster, monkeypatch):
    spec = TB.SPECS["contact"]
    paths = frozenset(p for p in spec.writes.paths if not p.startswith("CA3G:"))
    monkeypatch.setitem(TB.SPECS, "contact", dataclasses.replace(spec, writes=dataclasses.replace(spec.writes, paths=paths)))
    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "1")
    with ca3(), pytest.raises(AssertionError, match="宣言の外"):
        run_day(**dict(KW, ticks=360))


def test_event_log_on_off_does_not_change_the_arm_run(with_roster):
    from shibuya.engine.events import log as EV

    prev = EV.enabled()
    try:
        with ca3():
            EV.set_enabled(True)
            on = run_day(**dict(KW, ticks=720))
            EV.set_enabled(False)
            off = run_day(**dict(KW, ticks=720))
    finally:
        EV.set_enabled(prev)
    assert on.final_hash == off.final_hash
    assert [(c.tick, c.behavior_hash) for c in on.checkpoints] == [(c.tick, c.behavior_hash) for c in off.checkpoints]
    assert not off.calendar3_layer._c3_event_of


def test_arm_rows_enter_the_hashes_only_when_the_owner_exists():
    assert all(r.arm != "calendar-3" for r in SL.arm_rows() if SL.arm_items({"calendar3": None}, behavior=False))
    keys = {r.key for r in SL.arm_rows() if r.arm == "calendar-3"}
    assert keys == {"CA3S", "CA3P", "CA3G", "CA3M", "CA3Q"}
    for r in SL.arm_rows():
        if r.arm == "calendar-3":
            assert r.items and all(it.startswith("calendar3.") for it in r.items), r.key
    beh = {r.key for r in SL.arm_rows() if r.arm == "calendar-3" and r.behavior == SL.BEHAVIOR}
    assert beh == {"CA3S", "CA3P", "CA3G"}


def test_system_declarations():
    sp = TB.SPECS["calendar_3"]
    assert sp.when == "calendar3"
    order = list(TB.TICK_ORDER)
    assert order.index("contact") < order.index("calendar_3") < order.index("calendar_2") < order.index("memory")
    assert "CA3G:calendar3._reads" in TB.SPECS["contact"].writes.paths
    for p in ("CA2B:calendar2.book.*", "CT1*:contact.*", "BW:batching.*", "CA2G:calendar2._turns"):
        assert p in sp.writes.paths, p


def test_cli_flag_and_run_kind(with_roster, monkeypatch):
    from shibuya import cli
    from shibuya.engine import run_kind as RK

    monkeypatch.delenv(RK.PYTEST_ENV, raising=False)
    kw = dict(n_agents=30, seed=1, world_dir=None, n_cells=9, ticks=30, checkpoint_every=30, vocab_version="v3",
              start_sim_datetime=KW["start_sim_datetime"], activity="off")
    with ca3():
        r1 = cli.run(**kw)
    assert r1.run_kind == "arm" and "calendar_3" in r1.run_manifest_fields()
    seen = {}

    def fake_run(**k):
        seen["arm"] = A3.arm()
        raise SystemExit(0)

    monkeypatch.setattr(cli, "run", fake_run)
    with ca3(on=False):
        with pytest.raises(SystemExit):
            cli.main(["--calendar-3", "arm", "--agents", "5", "--ticks", "1"])
        assert seen["arm"] == "arm"


# ================================================================= AST の負の対照
_PERSON = {"W_FRAME", "W_WRITE", "W_ASK_REST", "W_ACCEPT", "W_DECLINE", "W_APPLY", "W_LATE"}
_ENGINE = {"W_NOTIFY"}


def _decide_names(fn: ast.FunctionDef) -> set[str]:
    out = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) \
                and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "_decide":
            for t in node.targets:
                if isinstance(t, ast.Tuple):
                    out |= {e.id for e in t.elts if isinstance(e, ast.Name)}
    return out


def _cause_problems(src: str) -> list[str]:
    """本人の語の出来事の原因が判断の口の答え(同じ関数の ``self._decide`` の戻り)だけか・道具の語の原因が過程 calendar3 だけか。"""
    tree = ast.parse(src)
    bad: list[str] = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        dn = _decide_names(fn)
        for node in ast.walk(fn):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "_log"):
                continue
            what = node.args[2] if len(node.args) > 2 else None
            cause = node.args[3] if len(node.args) > 3 else None
            names = {n.id for n in ast.walk(what) if isinstance(n, ast.Name)} if what is not None else set()
            if names & _PERSON and not (isinstance(cause, ast.Name) and cause.id in dn):
                bad.append(f"{fn.name}: 本人の語 {sorted(names & _PERSON)} の原因が判断の口の答えでない(行 {node.lineno})")
            if names & _ENGINE and not (isinstance(cause, ast.Name) and cause.id == "_P_CAL3"):
                bad.append(f"{fn.name}: 道具の語の原因が過程 calendar3 でない(行 {node.lineno})")
    return bad


def test_ast_person_events_come_only_from_decisions():
    assert _cause_problems((SRC / "layer.py").read_text(encoding="utf-8")) == []


def test_ast_negative_control_catches_planted_causes():
    planted = '''
class X:
    def _engine_writes(self, T, t_ns, a):
        self._log(t_ns, a, W_WRITE, _P_CAL3, how_much=1)
        self._log(t_ns, a, W_FRAME, LlmCall("1:2:-2097169"), how_much=1)
        self._log(t_ns, a, W_NOTIFY, LlmCall("1:2:-2097169"))
        self._log(t_ns, a, W_ACCEPT if 1 else W_DECLINE, _P_CAL3)
'''
    assert len(_cause_problems(planted)) == 4


#: 帳面に事象を置いてよい関数・行の時刻の欄を作ってよい関数(届いた連絡の中身=雇い主が選んだ枠から作る所だけ)・組む機会を開く関数。
_AGENDA_OK = {"_schedule_row"}
_TIME_KEY_OK = {"_write_rows"}
_COMPOSE_OK = {"_begin_compose", "_act"}


def _time_problems(src: str) -> list[str]:
    """エンジンが時刻や中身を決める直書きが無いか: (1) 帳面に事象を置く ``self._at`` は ``_schedule_row`` だけ・(2) 知らせの刻みは
    行の ``notify_ns`` と ``written_ns`` だけから(始まりから逆算しない)・(3) 行の ``start_ns``・``end_ns``・``notify_ns`` を作る辞書は
    ``_write_rows`` だけ(届いた中身の日と枠と本人の選んだ知らせから)・(4) 考えた刻み ``_think`` に入れる値は刻み ``T`` だけ・
    (5) 組む機会(``_compose_due``)を書くのは ``_begin_compose`` と ``_act`` だけ・(6) 枠の番号(``fi``)は判断の答えの id からだけ。"""
    tree = ast.parse(src)
    bad: list[str] = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "_at":
                if fn.name not in _AGENDA_OK:
                    bad.append(f"{fn.name}: 帳面に事象を置いた(行 {node.lineno})")
                code = node.args[1] if len(node.args) > 1 else None
                if isinstance(code, ast.Name) and code.id == "_AG_NOTIFY":
                    keys = {s.slice.value for s in ast.walk(node.args[0]) if isinstance(s, ast.Subscript)
                            and isinstance(s.slice, ast.Constant)}
                    if not keys <= {"notify_ns", "written_ns"}:
                        bad.append(f"{fn.name}: 知らせの刻みを {sorted(keys)} から作った(行 {node.lineno})")
            if isinstance(node, ast.Dict) and fn.name not in _TIME_KEY_OK:
                ks = {k.value for k in node.keys if isinstance(k, ast.Constant)}
                if ks & {"start_ns", "end_ns", "notify_ns"} and "kind" in ks:
                    bad.append(f"{fn.name}: 行の時刻の欄を作った(行 {node.lineno})")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "setdefault" \
                    and isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "_think":
                v = node.args[1] if len(node.args) > 1 else None
                if not (isinstance(v, ast.Call) and getattr(v.func, "id", "") == "int"
                        and isinstance(v.args[0], ast.Name) and v.args[0].id == "T"):
                    bad.append(f"{fn.name}: 考えた刻みを刻み T でない値にした(行 {node.lineno})")
            if isinstance(node, (ast.Assign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for t in targets:
                    if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Attribute) \
                            and t.value.attr == "_compose_due" and fn.name not in _COMPOSE_OK:
                        bad.append(f"{fn.name}: 組む機会を開いた(行 {node.lineno})")
                    if isinstance(t, ast.Name) and t.id == "fi" and not ("c.id" in ast.unparse(node.value)):
                        bad.append(f"{fn.name}: 枠の番号を判断の答えの外から作った(行 {node.lineno})")
    return bad


def test_ast_engine_does_not_decide_times_or_contents():
    assert _time_problems((SRC / "layer.py").read_text(encoding="utf-8")) == []


def test_ast_negative_control_catches_engine_rules():
    planted = '''
class X:
    def _schedule_row(self, rid):
        row = self.book.rows[rid]
        self._at(self._step_of(int(row["start_ns"])) - 30, _AG_NOTIFY, rid)

    def _wake(self, a, row, T):
        self._think.setdefault(a, self._step_of(int(row["start_ns"])) - 30)
        self._at(5, _AG_END, 1)
        fields = {"kind": 5, "start_ns": 5}
        self._compose_due[a] = 3
        fi = 0
'''
    assert len(_time_problems(planted)) == 6, _time_problems(planted)


def test_ast_book_is_written_only_through_its_ports():
    tree = ast.parse((SRC / "layer.py").read_text(encoding="utf-8"))
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                src = ast.unparse(t)
                if src.startswith(("row[", "self.book.rows", "self.calendar2.book")):
                    bad.append(f"行 {node.lineno}: {src}")
    assert bad == []


def test_workers_per_unit_match_the_roster_fixture():
    from tests.engine.calendar3._ca3 import synthetic_roster

    ro = synthetic_roster(80)
    assert all(len(w) == UNIT // 2 for w in ro.workers)


# ================================================================= 〔検収 H1〕雇い主の口の表は権利台帳から最初の刻みの頭に作る
@pytest.fixture
def with_real_rights(monkeypatch):
    """雇い主の口の表は差し替えない(権利台帳=合成の世界の開閉の過程の台帳から本物の道で作る)。W20 の週の表(世界の資産)と
    グループの一覧だけを合成の値にする。"""
    from shibuya.engine.calendar3 import roster as R3
    from tests.engine.calendar3._ca3 import synthetic_table

    roster_fixture(monkeypatch)
    monkeypatch.setattr(R3, "roster_for_run", _REAL_ROSTER_FOR_RUN)
    monkeypatch.setattr(R3, "w20_table_for_run", lambda world_dir, pop: synthetic_table(KW["n_agents"]))
    yield


from shibuya.engine.calendar3.roster import roster_for_run as _REAL_ROSTER_FOR_RUN  # noqa: E402


def _roster_view(lay):
    ro = lay.roster
    return (ro.unit_kind, ro.unit_obj, ro.scheduler, ro.sched_by, ro.workers, ro.store_of, ro.head_counts,
            sorted(lay.sched_units.items()))


def test_roster_is_built_after_restore_and_resume_matches_without_monkeypatch(with_real_rights, tmp_path):
    kw = dict(KW, sim_days=2)
    with ca3():
        straight = run_day(**kw)
        a = run_day(state_out=tmp_path / "state", stop_at_tick=TPD, **kw)
        path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
        b = run_day(resume_from=path, **kw)
    assert straight.calendar3_layer.roster.n_units > 0  # 権利台帳(店の担当の行)から単位ができた
    assert _roster_view(b.calendar3_layer) == _roster_view(straight.calendar3_layer)
    ms, mb = straight.run_manifest_fields()["calendar_3"], b.run_manifest_fields()["calendar_3"]
    assert ms["roster"] == mb["roster"] and ms["composed"] == mb["composed"] and ms["rest"] == mb["rest"]
    assert b.final_hash == straight.final_hash


def test_roster_is_not_built_at_assembly():
    """組み立ての口は表を作る口だけを渡す(表は最初の刻みの頭=ensure_roster)。"""
    src = (Path(__file__).resolve().parents[3] / "src" / "shibuya" / "engine" / "systems" / "build.py").read_text(
        encoding="utf-8")
    assert "roster_fn=lambda: _R3.roster_for_run(" in src and "roster=_R3." not in src


# ================================================================= 〔検収 M1〕組む機会は金曜の頭
def test_compose_on_friday_without_the_trial_mark(with_roster):
    """試験用の印の無い月曜始まりの 5 日(連続する平日)でも金曜(4 日目)に翌週(次の月曜=7 日目)を組む。"""
    with ca3(trial=False):
        r = run_day(**dict(KW, sim_days=5, start_sim_datetime="2026-07-27"))
    lay = r.calendar3_layer
    m = r.run_manifest_fields()["calendar_3"]
    assert m["trial"] is None
    assert m["composed"]["begun"] == len(lay.sched_units) and m["composed"]["begun_on_friday"] == 1
    assert "begun_on_trial_day0" not in m["composed"]
    assert m["composed"]["units"] == lay.roster.n_units and set(lay._composed.values()) == {7}
    frames = [e for e in _work(r) if e.what == LY.W_FRAME]
    assert frames and {int(e.t_ns) // (TPD * STEP_NS) for e in frames} == {4}  # 組んだのは金曜(4 日目)だけ
    assert m["composed"]["weekday:4"] == lay.roster.n_units


def test_seven_days_with_the_trial_mark_compose_once_on_friday(with_roster):
    """月曜始まりの 7 日(週末を含む=試験用の印): 組むのは金曜の 1 回だけ(0 日目は月曜=0 日目の組む機会は無い)。"""
    with ca3():
        r = run_day(**dict(KW, sim_days=7, start_sim_datetime="2026-07-27"))
    lay = r.calendar3_layer
    m = r.run_manifest_fields()["calendar_3"]
    assert m["composed"]["begun"] == len(lay.sched_units) and m["composed"]["begun_on_friday"] == 1
    assert "begun_on_trial_day0" not in m["composed"]
    assert m["composed"]["units"] == lay.roster.n_units and set(lay._composed.values()) == {7}
    assert sum(m["composed"]["hour_of_day"].values()) == lay.roster.n_units
    assert LY.audit_causes(r.event_log.events(), step_ns=STEP_NS,
                           issued=r.calendar3_layer.issued_keys())["violations"] == 0
    # 〔つなぎ BR-CT1-CHARGE-AT-HOME〕家で充電する=7 日でも電池 0 の体が残らず、金曜の知らせが C1 の口を通る(控えに残る 0・
    # 電源が無くて送れない 0=充電の前は 80 体全員が電池 0 で控え 39・送れない 338)
    # 〔第 6 期 6-4 C2〕つなぎを外し、充電は本人の判断になった(仮のモデルは一様)=電源の切れた体が 0 になるとは限らない。本人が
    # 充電して(差した体だけ電池が増える)、80 体全員が電池 0 にはならず、金曜の知らせが C1 の口を通る
    dev = r.run_manifest_fields()["contact_c1"]["devices"]
    assert dev["off"] < 80 and dev["battery_zero"] < 80
    assert r.contact_layer._meter.get("charge:plugged", 0) > 0 and r.contact_layer._meter.get("charge:agent_steps", 0) > 0
    assert m["contacts"].get("received:シフトの知らせ", 0) > 0 and m["rows"]["written"] > 0


def test_seven_days_negative_control_no_charge_decision(with_roster, monkeypatch):
    """〔第 6 期 6-4 C2 検収 L10〕負の対照: 充電の判断を「このまま」に固定すると、7 日で誰も充電せず(電池が増えない)、電源の切れた体と
    電源が無くて送れない C3 の連絡が、本人が充電するランより多い。"""
    from shibuya.engine.contact import port as CP

    kw = dict(KW, sim_days=7, start_sim_datetime="2026-07-27")
    with ca3():
        r = run_day(**kw)
    real = CP.ContactPort._pick

    def never(self, ctx, presented):
        for c in presented:
            if c.kind == CP.K_NO_CHARGE:
                return c.id
        return real(self, ctx, presented)

    monkeypatch.setattr(CP.ContactPort, "_pick", never)
    with ca3():
        r0 = run_day(**kw)
    m, m0 = r.contact_layer._meter, r0.contact_layer._meter
    assert m0.get("charge:plugged", 0) == 0 and m0.get("charge:agent_steps", 0) == 0 and m0.get("charge:declined", 0) > 0
    d, d0 = r.run_manifest_fields()["contact_c1"]["devices"], r0.run_manifest_fields()["contact_c1"]["devices"]
    assert d0["off"] > d["off"]
    assert m0.get("c3:cannot_send:device_off", 0) >= m.get("c3:cannot_send:device_off", 0)


# ================================================================= 〔検収 L1・L7〕
def test_trial_run_fills_the_start_check_field(sunday_run):
    sc = sunday_run.run_manifest_fields()["calendar"]["start_check"]
    assert sc and all(s.startswith(A3.TRIAL_MARK) for s in sc) and any("月曜でない" in s for s in sc)


def test_contact_without_calendar3_has_no_sinks_and_no_window_paths(with_roster):
    from shibuya.engine.systems import conductor as CD

    with ca3(on=False, trial=False):
        r = run_day(**dict(KW, ticks=60, start_sim_datetime=None))
        check = CD.declared_check(TB.SPECS)
        assert r.contact_layer is not None and r.calendar3_layer is None
        assert r.contact_layer.sent_sink is None and r.contact_layer.read_sink is None
        assert not check(CD.WINDOW_MARK, "CA3P:calendar3._out") and check(CD.WINDOW_MARK, "CT1I:contact.mail._inbox")
    with ca3():
        assert CD.declared_check(TB.SPECS)(CD.WINDOW_MARK, "CA3P:calendar3._out")
