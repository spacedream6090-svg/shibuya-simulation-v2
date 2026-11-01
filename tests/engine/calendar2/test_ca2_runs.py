"""第 6 期 6-2 カレンダー 2 のランの試験: 既定 off は層を作らない・腕 arm の合成のラン(各自の行・出来事の記録の数が計器と合う・
manifest の節と節の表・監査)・2 日と日の境目の再開=通し・腕を取り違えた再開は止まる・段 B(宣言の外 0)と負の対照・腕の行・
CLI の引数とランの種類・AST の負の対照(エンジンが時刻と回数を決める直書きが無い・本人の語の原因は判断の呼びだけ・器は口だけで
書く)。"""

from __future__ import annotations

import ast
import dataclasses
from collections import Counter
from pathlib import Path

import pytest

from shibuya.engine import manifest_sections as MS
from shibuya.engine import resume as RS
from shibuya.engine import state_ledger as SL
from shibuya.engine.calendar2 import arm as A
from shibuya.engine.calendar2 import layer as LY
from shibuya.engine.run import run_day
from shibuya.engine.systems import table as TB

from tests.engine.calendar2._ca2 import KW, STEP_NS, TPD, ca2, groups_fixture

SRC = Path(__file__).resolve().parents[3] / "src" / "shibuya" / "engine" / "calendar2"


@pytest.fixture
def with_groups(monkeypatch):
    groups_fixture(monkeypatch)
    yield


def test_default_off_builds_nothing(tmp_path):
    """〔検収 L6〕既定 off: 層・manifest の節・状態のファイルの calendar2.* の項・設定の指紋の鍵・約束の族の出来事が 0。"""
    with ca2(on=False):
        r = run_day(state_out=tmp_path / "state", stop_at_tick=120, **dict(KW, ticks=240))
    assert getattr(r, "calendar2_layer", "missing") is None
    m = r.run_manifest_fields()
    assert [k for k in m if k == "calendar_2"] == []
    assert sum(1 for e in r.event_log.events() if str(e.what).startswith("約束:")) == 0
    bundle = RS.read_state(tmp_path / "state" / r.resume["state_files"][-1]["file"])
    assert [p for p in bundle.items if p.startswith("calendar2.")] == []
    assert [k for k in bundle.header["fingerprint"] if k == A.FP_KEY] == []
    assert TB.SPECS["calendar_2"].when == "calendar2"  # 立つ条件のある系(層の無いランでは呼ばない)


def test_arm_run_rows_events_and_manifest(with_groups):
    with ca2(contact=True):
        r = run_day(**KW)
    m = r.run_manifest_fields()
    cc = m["calendar_2"]
    assert set(cc) == set(LY.CONFIG_KEYS) | set(LY.OBSERVED_KEYS)
    assert {p.split(".", 1)[1] for p, s in MS.PATHS.items() if p.startswith("calendar_2.") and s == MS.CONFIG} \
        == set(LY.CONFIG_KEYS)
    assert {p.split(".", 1)[1] for p, s in MS.PATHS.items() if p.startswith("calendar_2.") and s == MS.OBSERVED} \
        == set(LY.OBSERVED_KEYS)
    assert MS.unlisted_in_mixed(m) == []
    layer = r.calendar2_layer
    evs = [e for e in r.event_log.events() if str(e.what).startswith("約束:")]
    assert LY.audit_causes(r.event_log.events(), step_ns=STEP_NS, issued=layer.issued_keys())["violations"] == 0
    by = Counter(e.what for e in evs)
    meter = cc["meter"]
    # 計器の数と出来事の記録の行が合う
    assert by[LY.W_OFFER] == meter["offers"] > 0
    assert by[LY.W_WRITE] == sum(v for k, v in meter.items() if k.startswith("written:")) \
        + meter.get("intentions:アラーム", 0) + meter.get("intentions:出来事", 0) + meter.get("outside_plan:書いた", 0)
    assert by[LY.W_ACCEPT] == meter.get("answers:受ける", 0) and by[LY.W_DECLINE] == meter.get("answers:断る", 0)
    assert by[LY.W_TENTATIVE] == meter.get("answers:仮で受ける", 0)
    edits = sum(by[w] for w in (LY.W_EDIT_TIME, LY.W_EDIT_PLACE, LY.W_EDIT_CERTAIN, LY.W_CANCEL))
    assert edits == sum(v for k, v in meter.items() if k.startswith("changes:"))  # 変更 1 回=記録 1 行
    assert by[LY.W_ACCEPT] + by[LY.W_TENTATIVE] > 0 and cc["promises"]["rows_promise"] > 0
    # 各自の行: 行の持ち主は 1 人・自分は相手の欄に居ない・同じ誘いの行は持ち主が違う
    owners_by_offer: dict[int, list[int]] = {}
    for row in layer.book.rows.values():
        assert int(row["owner"]) not in row["with"]
        if row["kind"] == 0:
            owners_by_offer.setdefault(int(row["offer"]), []).append(int(row["owner"]))
    assert owners_by_offer and all(len(v) == len(set(v)) for v in owners_by_offer.values())
    assert any(len(v) >= 2 for v in owners_by_offer.values())  # 二人の約束=2 人がそれぞれ自分の行
    vias = {e.via for e in evs if e.what == LY.W_OFFER}
    assert {"メッセージ", "グループ"} & vias  # 連絡の道具 C1 の口(メッセージ・チャット)からも約束が生まれる
    assert cc["read_delay_minutes"]["source"] == "contact_c1.read_delay_minutes"
    assert cc["initial"]["rows"] == 0  # 初めの個人の予定は空で始める(つなぎ)


def _cp(r):
    return [(int(c.tick), c.behavior_hash, c.full_hash) for c in r.checkpoints if int(c.tick) >= TPD]


def test_two_days_and_resume_is_the_straight_run(with_groups, tmp_path):
    kw = dict(KW, ticks=TPD, sim_days=2, checkpoint_every=60)
    with ca2(contact=True):
        straight = run_day(tape_path=tmp_path / "s", **kw)
        a = run_day(state_out=tmp_path / "state", stop_at_tick=TPD, tape_path=tmp_path / "a", **kw)
        path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
        b = run_day(resume_from=path, tape_path=tmp_path / "b", **kw)
    assert b.final_hash == straight.final_hash and _cp(b) == _cp(straight) and _cp(b)
    bundle = RS.read_state(path)
    arm_paths = [p for _k, p in SL.arm_items({"calendar2": a.calendar2_layer}, behavior=False)]
    assert arm_paths and set(arm_paths) <= set(bundle.items)
    assert bundle.header["fingerprint"][A.FP_KEY] == {"arm": "arm"}
    ms, mb = straight.run_manifest_fields()["calendar_2"], b.run_manifest_fields()["calendar_2"]
    assert ms["promises"] == mb["promises"] and ms["arrival"] == mb["arrival"] and ms["forgot"] == mb["forgot"]
    assert straight.run_manifest_fields()["calendar_2"]["promises"]["days"] == 2


def test_resuming_with_the_arm_off_stops(with_groups, tmp_path):
    kw = dict(KW, ticks=TPD, sim_days=2, checkpoint_every=60)
    with ca2():
        a = run_day(state_out=tmp_path / "state", stop_at_tick=TPD, **kw)
    path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
    with ca2(on=False), pytest.raises(ValueError, match="calendar_2"):
        run_day(resume_from=path, **kw)


def test_stage_b_has_no_undeclared_writes(with_groups, monkeypatch):
    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "1")
    with ca2(contact=True):
        r = run_day(**dict(KW, ticks=360))
    meter = r.run_manifest_fields()["calendar_2"]["meter"]
    assert meter.get("decisions:turn", 0) > 0  # 会話の番の控え(連絡の系)を同じ刻みに読んだ


def test_stage_b_negative_control_without_the_turn_declaration_fails(with_groups, monkeypatch):
    spec = TB.SPECS["contact"]
    paths = frozenset(p for p in spec.writes.paths if not p.startswith("CA2G:"))
    monkeypatch.setitem(TB.SPECS, "contact", dataclasses.replace(spec, writes=dataclasses.replace(spec.writes, paths=paths)))
    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "1")
    with ca2(contact=True), pytest.raises(AssertionError, match="宣言の外"):
        run_day(**dict(KW, ticks=360))


def test_arm_rows_enter_the_hashes_only_when_the_owner_exists():
    owners = {"calendar2": None}
    assert all(r.arm != "calendar-2" for r in SL.arm_rows() if SL.arm_items(owners, behavior=False))
    keys = {r.key for r in SL.arm_rows() if r.arm == "calendar-2"}
    assert keys == {"CA2B", "CA2O", "CA2G", "CA2M", "CA2Q"}
    for r in SL.arm_rows():
        if r.arm == "calendar-2":
            assert r.items and all(it.startswith("calendar2.") for it in r.items), r.key
    beh = {r.key for r in SL.arm_rows() if r.arm == "calendar-2" and r.behavior == SL.BEHAVIOR}
    assert beh == {"CA2B", "CA2O", "CA2G"}


def test_system_declarations():
    sp = TB.SPECS["calendar_2"]
    assert sp.when == "calendar2" and "begin_walk_to" in sp.resolve_ops
    order = list(TB.TICK_ORDER)
    assert order.index("contact") < order.index("calendar_2") < order.index("memory")
    for name in ("decide", "llm_receive", "contact"):
        assert "CA2G:calendar2._turns" in TB.SPECS[name].writes.paths, name


def test_cli_flag_and_run_kind(monkeypatch):
    from shibuya import cli
    from shibuya.engine import run_kind as RK

    monkeypatch.delenv(RK.PYTEST_ENV, raising=False)
    kw = dict(n_agents=30, seed=1, world_dir=None, n_cells=9, ticks=30, checkpoint_every=30, vocab_version="v3")
    with ca2():
        r1 = cli.run(**kw)
    with ca2(on=False):
        r0 = cli.run(**kw)
    assert r1.run_kind == "arm" and "calendar_2" in r1.run_manifest_fields()
    assert r0.run_kind != "arm" and "calendar_2" not in r0.run_manifest_fields()
    seen = {}

    def fake_run(**k):
        seen["arm"] = A.arm()
        raise SystemExit(0)

    monkeypatch.setattr(cli, "run", fake_run)
    with ca2(on=False):
        with pytest.raises(SystemExit):
            cli.main(["--calendar-2", "arm", "--agents", "5", "--ticks", "1"])
        assert seen["arm"] == "arm"


# ================================================================= AST の負の対照
_PERSON = {"W_OFFER", "W_ACCEPT", "W_TENTATIVE", "W_DECLINE", "W_WRITE", "W_EDIT_TIME", "W_EDIT_PLACE",
           "W_EDIT_CERTAIN", "W_CANCEL", "W_DEPART", "W_NOT_GO"}
_ENGINE = {"W_REJECT", "W_NOTIFY"}


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
    """本人の語の出来事の原因が判断の口の答え(``self._decide`` の戻り=同じ関数の中か、それを渡す引数 ``cause``)だけか・
    道具の語の原因が過程 calendar2 だけかを AST で見る。"""
    tree = ast.parse(src)
    fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    bad: list[str] = []
    # 引数 cause を持つ関数は、呼び手が判断の口の答えを渡すこと
    for fn in fns.values():
        dn = _decide_names(fn)
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in fns \
                    and node.func.attr != "_log" and "cause" in {a.arg for a in fns[node.func.attr].args.args}:
                callee = fns[node.func.attr]
                idx = [a.arg for a in callee.args.args].index("cause") - 1  # self を除く
                arg = node.args[idx] if len(node.args) > idx else None
                if not (isinstance(arg, ast.Name) and (arg.id in dn or arg.id == "cause")):
                    bad.append(f"{fn.name}: {callee.name} に判断の口の答えでない cause を渡した(行 {node.lineno})")
    for fn in fns.values():
        dn = _decide_names(fn)
        params = {a.arg for a in fn.args.args}
        for node in ast.walk(fn):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "_log"):
                continue
            what = node.args[2] if len(node.args) > 2 else None
            cause = node.args[3] if len(node.args) > 3 else None
            wname = what.id if isinstance(what, ast.Name) else (
                what.value.id if isinstance(what, ast.Subscript) and isinstance(what.value, ast.Name) else "")
            person = wname in _PERSON or wname == "_ANSWER_WORDS"
            if person and not (isinstance(cause, ast.Name) and (cause.id in dn or (cause.id == "cause" and "cause" in params))):
                bad.append(f"{fn.name}: 本人の語 {wname} の原因が判断の口の答えでない(行 {node.lineno})")
            if wname in _ENGINE and not (isinstance(cause, ast.Name) and cause.id == "_P_CAL2"):
                bad.append(f"{fn.name}: 道具の語 {wname} の原因が過程 calendar2 でない(行 {node.lineno})")
    return bad


def test_ast_person_events_come_only_from_decisions():
    assert _cause_problems((SRC / "layer.py").read_text(encoding="utf-8")) == []


def test_ast_negative_control_catches_planted_rules():
    planted = '''
class X:
    def _engine_departs(self, T, t_ns, a, row):
        self._log(t_ns, a, W_DEPART, _P_CAL2, how_much=1)
        self._log(t_ns, a, W_WRITE, LlmCall("1:2:-1048593"), how_much=1)
        self._log(t_ns, a, W_NOTIFY, LlmCall("1:2:-1048593"))

    def _go(self, T, t_ns, a, row, cause):
        self._log(t_ns, a, W_DEPART, cause)

    def _caller(self, T, t_ns, a, row):
        self._go(T, t_ns, a, row, _P_CAL2)
'''
    got = _cause_problems(planted)
    assert len(got) == 4, got


#: 帳面に事象を置く口と、知らせの時刻・行の時刻の欄を作ってよい関数(本人の判断の答えから作る所だけ)。
_AGENDA_OK = {"_schedule_row"}
_TIME_KEY_OK = {"_write_own", "_outside"}


def _time_problems(src: str) -> list[str]:
    """エンジンが時刻を決める直書きが無いか: (1) 帳面に事象を置く ``self._at`` は ``_schedule_row`` だけ・(2) 知らせの事象の
    刻みは行の ``notify_ns`` と ``written_ns`` だけから(始まりから逆算しない)・(3) 行の ``start_ns``・``end_ns``・``notify_ns``
    の値を作る辞書は ``_write_own`` と ``_outside`` だけ(ほかは本人の判断の答え=``_when`` を通した ``book.edit``)・(4) 機会の
    「考えた」は主の判断の呼びのあった体と知らせからだけ(``self._think`` に入れる値は刻み ``T`` だけ)。"""
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
    return bad


def test_ast_engine_does_not_decide_times():
    assert _time_problems((SRC / "layer.py").read_text(encoding="utf-8")) == []


def test_ast_negative_control_catches_a_backward_reminder():
    planted = '''
class X:
    def _schedule_row(self, rid):
        row = self.book.rows[rid]
        self._at(self._step_of(int(row["start_ns"])) - 30, _AG_NOTIFY, rid)

    def _wake(self, a, row):
        self._think.setdefault(a, self._step_of(int(row["start_ns"])) - 30)
        self._at(5, _AG_START, 1)
        fields = {"kind": 0, "start_ns": 5}
'''
    got = _time_problems(planted)
    assert len(got) == 4, got


def test_ast_book_is_written_only_through_its_ports():
    """層は本人の予定の器の行を口(write・edit・observe・drop)だけで書く(行の欄への直の代入が無い)。"""
    tree = ast.parse((SRC / "layer.py").read_text(encoding="utf-8"))
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                src = ast.unparse(t)
                if src.startswith(("row[", "r[", "self.book.rows", "off[\"content\"]")):
                    bad.append(f"行 {node.lineno}: {src}")
    assert bad == []


# ================================================================= 〔検収 M3〕記録の有無で腕のランの behavior-hash と final が同じ
def test_event_log_on_off_does_not_change_the_arm_run(with_groups):
    from shibuya.engine.events import log as EV

    prev = EV.enabled()
    try:
        with ca2():
            EV.set_enabled(True)
            on = run_day(**KW)
            EV.set_enabled(False)
            off = run_day(**KW)
    finally:
        EV.set_enabled(prev)
    assert on.final_hash == off.final_hash
    assert [(c.tick, c.behavior_hash) for c in on.checkpoints] == [(c.tick, c.behavior_hash) for c in off.checkpoints]
    lay = on.calendar2_layer
    assert lay._c2_event_of and not off.calendar2_layer._c2_event_of  # 目印は診断の表だけ
    assert all("event" not in row for row in lay.book.rows.values())


def test_calls_by_model_has_the_calendar_2_breakdown(with_groups):
    """〔問い 2〕calls_by_model に内訳 calendar_2(manifest と日次の記録)=C1 の M5 と同じ形。"""
    with ca2(contact=True):
        r = run_day(**dict(KW, ticks=240))
    cbm = r.run_manifest_fields()["calls_by_model"]
    j2, t2 = r.calendar2_layer.model_calls()
    jc, tc = r.contact_layer.model_calls()
    assert cbm["calendar_2"] == {"judge_model": j2, "llm": t2} and j2 > 0
    assert cbm["judge_model"] == j2 + jc and cbm["contact"] == {"judge_model": jc, "llm": tc}
