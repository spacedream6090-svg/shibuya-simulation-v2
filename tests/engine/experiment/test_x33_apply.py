"""第 3 期 3-3 効かせる口 ``apply(form, world, t)``(決定 10-12 §1-1 CP6・§4-5 CP5・CP12)。合成の世界で試す。

- L1(営業時間の変更・休業・催しの告知)と L0(天気の日付の差し替え・祝日)が合成の世界(``World.synthetic``+手書きの W7・W13)で
  効く。表を実行するのは世界の中の過程(営業時間の表は ``OpeningProcess.step`` が開け閉めする)。
- 決定は 1 回だけ出来事ログに書かれる(原因=実験の条件・口は ``gate.admit``)。日が替わると表へ当て直す・終わりで元に戻す。
- 効かせていない改変(対象が無い・種別が無い・W7/W13 が無い・期間の外・宣言して未実装)は ``unapplied`` に数えて続く。
- 告知は宛先ごとに「届いた情報」の行(``via``・``received_ns``)。宛先が無ければ数えて続く。
- 口は 1 つ: ``admit`` を呼ぶのは ``apply.py`` だけ・世界の表を書く口(``set_plan_rows`` など)を呼ぶのも ``apply.py`` だけ(AST・
  負の対照つき)。1-3 の負の対照(口の外から実験の条件を作れない)は残る。
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from shibuya.engine.events import log as EV
from shibuya.engine.experiment import apply as AP
from shibuya.engine.processes.opening import build_open_matrix

from tests.engine.experiment._x33 import NS_DAY, NS_HOUR, STEP_S, at, form, handle, rows, synthetic_world

pytestmark = pytest.mark.filterwarnings("ignore::shibuya.engine.processes.environment.WeatherWarning")
SRC = Path(__file__).resolve().parents[3] / "src" / "shibuya"
T0 = NS_DAY + 12 * NS_HOUR  # 1 日目の正午


def _exp_events(h):
    return [e for e in h.events.events() if e.what.startswith("実験:")]


def _w7_rows(sw, pois, row):
    a = sw.assets
    full = build_open_matrix(sw.world.n_poi, a.plan_poi, a.plan_day, a.plan_start, a.plan_end, row, a.plan_ph_poi)
    return full[np.asarray(pois)]


# ================================================================= L1 休業
def test_closure_enters_the_plan_once_and_the_opening_process_executes_it():
    sw = synthetic_world()
    h = handle(sw)
    f = form(subject={"level": "L1", "ids": [0, 1]})
    before = rows(sw, [0, 1, 2]).copy()
    assert before[:, 600].all()
    assert at(h, f, T0 - NS_HOUR) == 0 and np.array_equal(rows(sw, [0, 1, 2]), before)  # 始まりの前は何もしない
    assert at(h, f, T0) == 1
    assert not rows(sw, [0, 1]).any() and np.array_equal(rows(sw, [2]), before[[2]])  # 対象の店だけ表が空になる
    evs = _exp_events(h)
    assert [e.what for e in evs] == ["実験:改変"]
    ev = evs[0]
    assert type(ev.cause) is EV.Experiment and ev.cause.kind == "experiment"
    assert ev.cause.cond_id == f"{f.sha256()[:16]}:0" and ev.origin == AP.ORIGIN_OUTSIDE and ev.who == AP.WHO
    assert ev.where == ("poi", 0) and ev.how_much == 2 and ev.t_ns == T0
    assert at(h, f, T0) == 0 and len(_exp_events(h)) == 1  # 同じ刻みの 2 回目は何もしない
    rec = h.rec
    assert len(rec.applied) == 1 and rec.applied[0]["targets"] == 2 and rec.tallies["decided"] == 1
    # 実行は世界の中の過程(開け閉めの役割行動か今のつなぎ)=開閉の旗が閉じる
    step = T0 // (STEP_S * 10 ** 9)
    sw.opening.step(step)
    assert not sw.world.open_mask(step)[[0, 1]].any() and bool(sw.world.open_mask(step)[2])


def test_the_plan_is_put_again_after_the_day_head_and_restored_at_the_end():
    sw = synthetic_world()
    h = handle(sw)
    f = form(subject={"level": "L1", "ids": [1]}, end=2 * NS_DAY + 12 * NS_HOUR)
    at(h, f, T0)
    assert not rows(sw, [1]).any()
    sw.opening.relay_day(sw.calendar.opening_row(2))  # 2 日目の頭: 過程が W7 から表を張り直す
    assert rows(sw, [1]).any()
    assert at(h, f, 2 * NS_DAY) == 1 and not rows(sw, [1]).any() and h.rec.tallies["reapplied"] == 1
    assert at(h, f, 2 * NS_DAY + NS_HOUR) == 0  # 同じ日は当て直さない
    assert at(h, f, 2 * NS_DAY + 12 * NS_HOUR) == 1  # 終わり=W7 の行に戻す
    assert np.array_equal(rows(sw, [1]), _w7_rows(sw, [1], sw.calendar.opening_row(2)))
    assert h.rec.tallies["restored"] == 1 and len(_exp_events(h)) == 1


def test_opening_hours_and_event():
    sw = synthetic_world()
    h = handle(sw)
    f = form(content=[{"decision": "opening_hours", "hours": [[600, 900], [1380, 1500]]}, {"decision": "event"}],
             subject={"level": "L1", "ids": [2]})
    at(h, f, T0)
    want = AP.hours_mask([[600, 900], [1380, 1500]])
    assert np.array_equal(rows(sw, [2])[0], want) and want[0] and want[59] and not want[60] and want[1439]
    assert [e.what for e in _exp_events(h)] == ["実験:改変", "実験:改変"]  # 催しは表を変えず決定の行だけ
    assert [r["decision"] for r in h.rec.applied] == ["opening_hours", "event"]


# ================================================================= 告知(CP6=本段は「届いた情報」の行まで)
def test_notice_rows_per_recipient():
    sw = synthetic_world()
    h = handle(sw)
    f = form(subject={"level": "L1", "ids": [0]}, notice={"to": ["staff", 3, 999_999], "at": T0 + NS_HOUR, "via": "SNS"})
    at(h, f, T0)
    assert [e.what for e in _exp_events(h)] == ["実験:改変"]  # 告知はまだ(at の前)
    at(h, f, T0 + NS_HOUR)
    got = [e for e in _exp_events(h) if e.what == AP.WHAT_NOTICE]
    staff0 = int(sw.opening.staff_of_poi[0])
    assert staff0 >= 0
    assert sorted(e.whom for e in got) == sorted({staff0, 3})  # 範囲の外の番号は宛先にしない
    assert all(e.via == "SNS" and e.received_ns == T0 + NS_HOUR and e.origin == AP.ORIGIN_OUTSIDE for e in got)
    assert all(e.cause.cond_id == f"{f.sha256()[:16]}:notice" for e in got)
    assert h.rec.tallies["notices"] == 2
    at(h, f, T0 + 2 * NS_HOUR)
    assert h.rec.tallies["notices"] == 2  # 1 回だけ


def test_notice_without_recipients_is_counted_and_continues():
    sw = synthetic_world()
    h = handle(sw)
    f = form(notice={"to": [999_999], "via": "メッセージ"})
    at(h, f, T0)
    assert h.rec.tallies["notice_unreached"] == 1 and h.rec.unapplied[-1]["reason_key"] == "no_recipient"


# ================================================================= L0 天気の日付・祝日
def test_weather_date_swap_and_reapply():
    sw = synthetic_world()
    env = sw.environment
    env.pick_day(1)
    h = handle(sw)
    f = form(subject={"level": "L0", "ids": []}, content=[{"decision": "weather_date", "replay_date": "2026-08-20"}])
    actual = env.replay_date
    assert actual == "2026-07-14"
    at(h, f, T0)
    assert env.replay_date == "2026-08-20" and env._row == 2 and env.weather_days[1]["how"] == "experiment"
    ev = _exp_events(h)[0]
    assert ev.origin == AP.ORIGIN_NATURE and ev.where is None
    env.pick_day(2)  # 2 日目の頭: 過程がその日の天気を引き直す
    assert env.replay_date != "2026-08-20"
    assert at(h, f, 2 * NS_DAY) == 1 and env.replay_date == "2026-08-20" and h.rec.tallies["reapplied"] == 1


def test_holiday_for_a_later_day():
    sw = synthetic_world()
    h = handle(sw)
    cal = sw.calendar
    later = cal.date_of_day(3).isoformat()
    f = form(subject={"level": "L0", "ids": []}, content=[{"decision": "holiday", "date": later}])
    assert not cal.is_holiday(3)
    at(h, f, T0)
    assert cal.is_holiday(3) and cal.is_rest_day(3) and cal.holiday_name(3) == "休日"
    off = form(subject={"level": "L0", "ids": []}, content=[{"decision": "holiday", "date": later, "on": False}],
               start=T0 + NS_HOUR)
    at(h2 := handle(sw), off, T0 + NS_HOUR)
    assert not cal.is_holiday(3) and len(h2.rec.applied) == 1


# ================================================================= 効かせていない改変は記録して続ける
@pytest.mark.parametrize("over,key,world_kw", [
    (dict(subject={"level": "L1", "ids": [999]}), "no_target", {}),
    (dict(subject={"level": "L1", "ids": [], "category": "申込書の値の種別"}), "no_category", {}),
    (dict(subject={"level": "L1", "ids": [0]}), "no_w7", {"plan": False}),
    (dict(subject={"level": "L0", "ids": []}, content=[{"decision": "weather_date", "replay_date": "2026-09-01"}]),
     "no_replay_date", {}),
    (dict(subject={"level": "L0", "ids": []}, content=[{"decision": "weather_date", "replay_date": "2026-07-14"}]),
     "no_w13", {"weather": False}),
    (dict(subject={"level": "L0", "ids": []}, content=[{"decision": "holiday", "date": "2026-07-14"}]),
     "past_day", {}),
    (dict(subject={"level": "L2", "ids": [0]}, content=[{"decision": "passage"}]), "not_implemented", {}),
    (dict(subject={"level": "L4", "ids": []}, content=[{"decision": "fare", "amount_yen": 10}]), "not_implemented", {}),
])
def test_unapplied_is_recorded_and_the_run_continues(over, key, world_kw):
    sw = synthetic_world(**world_kw)
    h = handle(sw)
    f = form(**over)
    before = np.asarray(sw.opening.open_matrix).copy()
    assert at(h, f, T0) == 0
    rec = h.rec
    assert [r["reason_key"] for r in rec.unapplied] == [key] and rec.tallies["unapplied"] == 1 and not rec.applied
    assert _exp_events(h) == [] and np.array_equal(np.asarray(sw.opening.open_matrix), before)
    if key == "not_implemented":
        assert rec.unapplied[0]["reason"].endswith(f"({f.level})")
    assert at(h, f, T0 + NS_HOUR) == 0 and rec.tallies["unapplied"] == 1  # 続く(同じ決定は 1 回だけ数える)


def test_branch_from_a_state_without_the_form_marks_earlier_starts_out_of_period():
    sw = synthetic_world()
    h = handle(sw, begin_ns=2 * NS_DAY)  # 基準のラン(申込書なし)の 2 日目の頭から分岐
    at(h, form(), 2 * NS_DAY)
    assert [r["reason_key"] for r in h.rec.unapplied] == ["before_begin"]


def test_inherited_run_puts_the_tables_again_without_new_rows():
    """再開(親が同じ申込書): 始まりが再開の時刻より前の決定は表へ当てるだけ(出来事と告知は親のランが書いた)。"""
    sw = synthetic_world()
    cal = sw.calendar
    f = form(subject={"level": "L1", "ids": [0]}, notice={"to": [3], "via": "メッセージ"})
    h = handle(sw, begin_ns=2 * NS_DAY, inherited=True)
    assert at(h, f, 2 * NS_DAY) == 1 and not rows(sw, [0]).any()
    assert _exp_events(h) == [] and h.rec.tallies["reapplied"] == 1 and h.rec.notice_sent
    # 祝日は組み立ての中で日の頭より前に当てる(prime)
    hol = form(subject={"level": "L0", "ids": []}, content=[{"decision": "holiday", "date": cal.date_of_day(2).isoformat()}])
    h2 = handle(sw, begin_ns=2 * NS_DAY, inherited=True)
    assert AP.apply(hol, h2, 2 * NS_DAY, prime=True) == 1 and cal.is_holiday(2)


# ================================================================= 口は 1 つ(CP12)
GATE = "shibuya.engine.experiment.gate"
TABLE_WRITERS = {"set_plan_rows", "restore_plan_rows", "set_replay_date", "set_holiday"}  # 〔検収 L5〕暦の書き口も


def _gate_names(tree: ast.AST) -> tuple[set[str], set[str]]:
    """口の置き場の別名(``G.admit`` の ``G``)と、口を直に import した名(``admit``)。"""
    mods, funcs = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            if n.module == "shibuya.engine.experiment":
                mods |= {a.asname or a.name for a in n.names if a.name == "gate"}
            elif n.module == GATE:
                funcs |= {a.asname or a.name for a in n.names if a.name == "admit"}
        elif isinstance(n, ast.Import):
            mods |= {a.asname or a.name for a in n.names if a.name == GATE}
    return mods, funcs


def _calls(tree: ast.AST) -> list[int]:
    """口 ``gate.admit`` の呼び出しと、世界の表の書き口(``TABLE_WRITERS``)の呼び出しの行(別の物の ``admit`` は数えない)。"""
    mods, funcs = _gate_names(tree)
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = n.func
        if isinstance(fn, ast.Attribute):
            if fn.attr in TABLE_WRITERS or (fn.attr == "admit" and ast.unparse(fn.value) in mods | {GATE}):
                out.append(n.lineno)
        elif isinstance(fn, ast.Name) and fn.id in funcs:
            out.append(n.lineno)
    return sorted(out)


def test_admit_and_the_table_writers_are_called_only_from_apply():
    hits: dict[str, list[int]] = {}
    for p in sorted(SRC.rglob("*.py")):
        rel = p.relative_to(SRC).as_posix()
        got = _calls(ast.parse(p.read_text(encoding="utf-8")))
        if got:
            hits[rel] = got
    assert set(hits) == {"engine/experiment/apply.py"}, hits


def test_the_entry_check_catches_a_planted_call():
    """負の対照: 口の外で admit(別名・直の import)・表の書き口を呼ぶ形は見つかる。別の物の admit は数えない。"""
    planted = ast.parse("from shibuya.engine.experiment import gate as G\nG.admit(log, 'c', what='実験:改変', who='x')\n"
                        "runner.opening.set_plan_rows([0], m)\nenv.set_replay_date(1, '2026-07-14')\n"
                        "from shibuya.engine.experiment.gate import admit as a2\na2(log, 'c', what='x', who='y')\n"
                        "self.budget.admit(3)\n")
    assert _calls(planted) == [2, 3, 4, 6]


def test_the_cause_still_cannot_be_made_outside_the_gate():
    """1-3 の負の対照が残る: 口の外から実験の条件の原因を作ると落ちる。"""
    with pytest.raises(PermissionError, match="CP12"):
        EV.Experiment("x")


def test_vocabulary_has_the_two_words():
    from shibuya.engine.events import vocab as V

    assert V.code_of(AP.WHAT_DECISION) == 60 and V.code_of(AP.WHAT_NOTICE) == 61  # 2-1 の金の 2 語(58・59)の後ろ
    # 〔第 2 期 2-3〕その後ろに体の出来事の 3 語を足して版を events-vocab/2-3 にした(60・61 は動かない)
    assert V.family_of(AP.WHAT_NOTICE) == "実験" and V.VOCAB_VERSION == "events-vocab/6-6-w1"  # 〔第 6 期 6-4 C1〕連絡の族の 15 語を表の末尾に足して版を上げた(前 events-vocab/2-3・前の語のコードは動かない)・〔第 6 期 6-2 カレンダー 2〕約束の族の 13 語をその後ろに足して版を上げた(前 events-vocab/6-4)・〔第 6 期 6-2 カレンダー 3〕勤務の族の 8 語をその後ろに足して版を上げた(前 events-vocab/6-2-ca2)・〔第 6 期 6-6 ② 第 1 部〕仕事の族の 4 語をその後ろに足して版を上げた(前 events-vocab/6-2-ca3)


def test_module_tables_are_read_only():
    """〔検収 L6〕口の表(決定の実装・理由の語)と分岐の表は読み取り専用。"""
    from shibuya.engine.experiment import branch as BR

    for table in (AP._IMPL, AP.REASONS, BR.DERIVED_BY_DECISION, BR.RESUME_DERIVED):
        with pytest.raises(TypeError):
            table["x"] = None  # type: ignore[index]


def test_the_calendar_is_written_through_its_one_mouth():
    """〔検収 L5〕祝日の表を書くのは暦の口 ``SimCalendar.set_holiday`` だけ(apply は辞書を直に書かない)。"""
    src = (SRC / "engine" / "experiment" / "apply.py").read_text(encoding="utf-8")
    assert "set_holiday(" in src and "days[" not in src and ".pop(d" not in src
