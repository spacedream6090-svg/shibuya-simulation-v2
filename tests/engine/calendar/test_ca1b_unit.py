"""第 6 期 6-2 カレンダー 1b(``engine.calendar_self``・腕 ``--calendar 1b``)の合成の単体の試験。

- 置き場所ごとの思い出し方(AT1): アプリ=本人が決めた時刻の通知・アラーム=鳴る・手帳=見たとき(おおよその時刻)・
  頭の中=時計を見る習慣(MR7 までは入力に載る)。機会はどれも本人の記録を参照に持つ(逆算して起こさない)。
- CA4: 壊れた予定だけ拒む・重なりは警告。
- AT2: 見積りの幅と直近の平均・経過時間の実感(R-111 §1 の形)と丸め。
- TM8: 時計を見たときだけ分単位。
- 候補の口の形(J0 の約束どおり): 候補の源・番号は口が振る・並べ替えても同じ中身を選ぶ・Choice の欄。
- 宣言(manifest の節・状態台帳の腕の行・系の表の書く欄・道具の台帳の行・W20 の場所の語の写し)。
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.engine import calendar_self as CS1
from shibuya.engine import calendar_shadow as CSH
from shibuya.engine import manifest_sections as MS
from shibuya.engine import state_ledger as SL
from shibuya.engine.decision.port import (
    DELIBERATE_KIND, SOURCE_CONTINUE, SOURCE_DELIBERATE, SOURCE_PLAN, Choice, DecisionContext, DecisionPort,
)
from shibuya.engine.systems.table import SPECS


# ================================================================= 宣言
def test_arm_names_and_switch():
    assert CS1.DEFAULT_MODE == CS1.MODE_W17 and CS1.MODES == ("w17", "1b")
    prev = CS1.arm()
    try:
        CS1.set_arm("1b")
        assert CS1.is_on()
        with pytest.raises(ValueError):
            CS1.set_arm("1a")
    finally:
        CS1.set_arm(prev)


def test_manifest_section_ledger_rows_and_system_declarations():
    assert CS1.MANIFEST_KEY in MS.MIXED and MS.PATHS[CS1.MANIFEST_KEY] == MS.OBSERVED
    for k in CS1.MANIFEST_CONFIG:
        assert MS.section_of(f"{CS1.MANIFEST_KEY}.{k}") == MS.CONFIG, k
    for k in CS1.MANIFEST_OBSERVED:
        assert MS.section_of(f"{CS1.MANIFEST_KEY}.{k}") == MS.OBSERVED, k
    assert CS1.manifest_fields(None) == {}
    r = SL.row("C1B")
    assert r.behavior == SL.BEHAVIOR and r.restore == SL.REQUIRED and r.arm == CS1.LEDGER_ARM_NAME
    assert r.items == ("calendar_self.cal_store",)
    m = SL.row("C1BM")
    assert m.behavior == SL.DIAG and m.restore == SL.REQUIRED and m.arm == CS1.LEDGER_ARM_NAME
    assert SL.OWNER_CLASSES["calendar_self"] == ("engine/calendar_self.py", "CalendarSelf")
    assert CS1.CalendarSelf.LEDGER_ARM == CS1.LEDGER_ARM_NAME
    assert not any(k in ("C1B", "C1BM") for k, _p in SL.full_items())  # 腕の行=既定のハッシュに入らない
    assert SL.arm_items({"calendar_self": None}, behavior=True) == ()
    for name in ("day_head", "presence"):
        assert "C1B*:calendar_self.*" in SPECS[name].writes.paths and "layers.calendar_self" in SPECS[name].reads.box
    assert "begin_walk_to" in SPECS["presence"].resolve_ops and "E:events.*" in SPECS["presence"].writes.paths
    assert "layers.calendar_self" in SPECS["close_final"].reads.box


def test_w20_place_words_are_the_build_side_copy():
    from shibuya.build.sched import w20_calendar_1a as W

    assert CS1.W20_PLACE_WORDS == W.PLACE_WORDS


def test_tool_registry_has_clock_and_forecast():
    from shibuya.engine.tools import registry as TR

    reg = TR.default_registry()
    assert reg.get(TR.CLOCK).stage == "6-2" and reg.get(TR.FORECAST).stage == "6-2"
    assert reg.get(TR.FORECAST).bridge == "DOC-ca1b-forecast-blank" and reg.get(TR.FORECAST).content_origin == "無し"
    assert TR.CLOCK not in reg.in_use() and TR.FORECAST not in reg.in_use()  # 既定の世界では使わない(腕 1b の段)
    assert TR.affordance_words(reg, 0, ()) == ()


def test_bridges_rows_are_in_the_ledger():
    from shibuya.engine.bridging import ledger as BR

    led = BR.default_ledger()
    for b in CS1.BRIDGES:
        assert led.get(b).status == "active", b
    assert "〔第 6 期 6-2・腕 --calendar 1b〕" in led.get("BR-W17-IO-SLEEP").why
    assert "〔第 6 期 6-2・腕 --calendar 1b〕" in led.get("BR-E4-EXIT-VANISH").why
    assert led.get("BR-W17-IO-SLEEP").status == led.get("BR-E4-EXIT-VANISH").status == "active"


# ================================================================= TM8・実感・丸め
def test_clock_minutes_only_when_looked():
    assert CS1.observe_time(487, precise=True) == (487, "8:07")
    t, w = CS1.observe_time(487, precise=False)
    assert t == 480 and w == "8:00ごろ"
    assert CS1.observe_time(500, precise=False) == (510, "8:30ごろ")
    assert CS1.observe_time(1500, precise=True)[1] == "翌1:00"


def test_felt_time_form_and_rounding():
    assert CS1.felt_minutes(30.0, 0.0) == pytest.approx(30.0)  # 待ちが無ければ比 1(空欄=係数を置かない)
    assert CS1.felt_minutes(30.0, 5.0) == pytest.approx(25.0 + 1.9 + 0.72 * 5.0)  # 待ちは長く(R-111 §1-2 #1)
    # 〔検収 L12〕出典の範囲(待ち 3〜15 分)の外は比 1
    assert CS1.felt_minutes(2.0, 2.0) == pytest.approx(2.0) and CS1.felt_minutes(40.0, 20.0) == pytest.approx(40.0)
    assert CS1.felt_minutes(10.0, 3.0) == pytest.approx(7.0 + 1.9 + 0.72 * 3.0)
    assert CS1.FELT_WAIT_RANGE_MIN == (3.0, 15.0)
    assert (CS1.FELT_WAIT_INTERCEPT, CS1.FELT_WAIT_SLOPE) == (1.9, 0.72)
    assert CS1.duration_words(33.0) == "35 分ほど" and CS1.duration_words(31.0) == "30 分ほど"
    assert CS1.duration_words(0.5) == "5 分ほど"


# ================================================================= AT2 見積り
def test_estimate_width_and_recent_mean():
    init = CS1.Estimate(lo=30.0, hi=36.0)
    assert CS1.update_estimate([np.nan] * 5, init) == init  # 経験が無ければ最初の幅
    one = CS1.update_estimate([40.0, np.nan, np.nan, np.nan, np.nan], init)
    assert one.center == pytest.approx(40.0) and (one.hi - one.lo) == pytest.approx(6.0)  # 1 回=最初の幅のまま
    many = CS1.update_estimate([30.0, 34.0, 38.0, np.nan, np.nan], init)
    assert many.center == pytest.approx(34.0) and (many.lo, many.hi) == (pytest.approx(30.0), pytest.approx(38.0))


def test_route_steps_counts_nodes_on_the_walk_graph():
    nxt = np.array([[0, 1, 1, 1], [0, 1, 2, 2], [1, 1, 2, 3], [2, 2, 2, 3]])
    nxt[0, 3] = 1
    world = SimpleNamespace(graph=SimpleNamespace(route_next_node=lambda u, v: nxt[np.asarray(u), np.asarray(v)]))
    got = CS1.route_steps(world, np.array([0, 3, 2, -1]), np.array([3, 0, 2, 1]))
    assert got.tolist() == [3, 3, 0, -1]


# ================================================================= CA4
def test_only_broken_commitments_are_rejected_and_overlaps_warn():
    bad, pairs = CS1.validate_commitments([480, 600, 700, -1, 900], [540, 600, 760, 30, 1000],
                                          kind=[1, 1, 1, 1, 1], place_kind=[1, 1, 0, 1, 1])
    assert bad.tolist() == [False, True, True, True, False]  # 終わり ≤ 始まり・場所が空・時刻が空
    assert pairs == []
    bad2, pairs2 = CS1.validate_commitments([480, 500, 900], [600, 560, 960])
    assert not bad2.any() and pairs2 == [(0, 1)]  # 重なりは警告だけ(行は残す)


# ================================================================= J0 の口の形
def _pred(trip: int = CS1.TRIP_GO, **kw) -> CS1.Prediction:
    base = dict(trip=CS1.TRIPS[trip], kind="勤務", start_min=540, end_min=1080, place="建物", est_lo_min=40.0,
                est_hi_min=46.0, est_words="40 分ほど〜45 分ほど", margin_min=10, look_interval_min=30)
    base.update(kw)
    return CS1.Prediction(**base)


def _ctx(obs: CS1.Observation, pred: CS1.Prediction, agent: int = 7, step: int = 400) -> DecisionContext:
    return DecisionContext(agent_id=agent, step=step, t_ns=step * 60 * 10**9, wake_class=-1, condition=-1, cell=3,
                           call_id=f"cal1b:{step}:{agent}:0", percept=obs, prediction=pred)


def test_candidates_follow_the_j0_contract():
    go = CS1.commute_candidates(_pred())
    assert [c.source for c in go] == [SOURCE_PLAN, SOURCE_CONTINUE, SOURCE_DELIBERATE]
    assert go[0].kind == "移動" and "9:00" in go[0].text and "建物" in go[0].text and go[2].kind == DELIBERATE_KIND
    assert all(c.number is None for c in go)  # 番号は口が最後に振る(C-2)
    back = CS1.commute_candidates(_pred(CS1.TRIP_BACK))
    assert back[0].id == "plan:帰る" and "18:00" in back[0].text
    port = CS1.CommuteMockPort(seed=1, day_key0=0, step_seconds=60)
    assert isinstance(port, DecisionPort) and port.name == "mock" and CS1.CommuteClassicalPort.name == "classical"
    obs = CS1.Observation(time_min=500, precise=True, words="8:20", where="域外", trigger="アプリの通知")
    ch = port.choose(_ctx(obs, _pred()), go)
    assert isinstance(ch, Choice) and 1 <= ch.number <= len(go) and ch.surprise is None and ch.hesitation is None
    # 並べ替え(種・刻み・体)を変えても同じ中身を選ぶ(中身で選ぶ=提示の位置に左右されない)
    picks = {CS1.CommuteMockPort(seed=s, day_key0=0, step_seconds=60).choose(_ctx(obs, _pred(), agent=a, step=st), go)
             .candidate_id for s in (1, 2, 3) for a in (1, 9) for st in (400, 401)}
    assert picks == {ch.candidate_id}


def test_mock_departs_as_planned_and_classical_uses_the_center():
    pred = _pred()  # 9:00 始まり・幅 40〜46 分・余裕 10 分 → 予定の出発 8:04(mock)/ 8:07(古典)
    mock = CS1.CommuteMockPort(seed=1, day_key0=0, step_seconds=60)
    cls = CS1.CommuteClassicalPort(seed=1, day_key0=0, step_seconds=60)
    assert mock.planned_departure(pred) == 540 - 46 - 10 and cls.planned_departure(pred) == 540 - 43 - 10
    cands = CS1.commute_candidates(pred)
    early = CS1.Observation(time_min=470, precise=True, words="7:50", where="域外", trigger="時計を見た")
    ch = mock.choose(_ctx(early, pred), cands)
    assert ch.candidate_id == "continue:まだ" and ch.continuous["next_look_min"] == 484.0  # 次は予定の出発に見る
    now = CS1.Observation(time_min=484, precise=True, words="8:04", where="域外", trigger="アラーム")
    assert mock.choose(_ctx(now, pred), cands).candidate_id == "plan:出発"
    assert cls.choose(_ctx(now, pred), cands).candidate_id == "continue:まだ"  # 古典は真ん中=3 分あと
    rough = CS1.Observation(time_min=450, precise=False, words="7:30ごろ", where="域外", trigger="手帳を見た")
    assert mock.choose(_ctx(rough, pred), cands).continuous["next_look_min"] == 480.0  # おおよそなら時計を見る間隔の後
    over = CS1.Observation(time_min=1100, precise=True, words="18:20", where="域外", trigger="時計を見た")
    ch2 = mock.choose(_ctx(over, pred), cands)
    assert ch2.candidate_id == "continue:まだ" and ch2.continuous["next_look_min"] == -1.0  # 終わった約束には行かない
    bc = CS1.commute_candidates(_pred(CS1.TRIP_BACK))
    end = CS1.Observation(time_min=1080, precise=True, words="18:00", where="舞台の中", trigger="終わりの時刻")
    assert mock.choose(_ctx(end, _pred(CS1.TRIP_BACK)), bc).candidate_id == "plan:帰る"


# ================================================================= AT1 置き場所ごとの思い出し方(器を合成の世界で張る)
class _Cal:
    def __init__(self, start: date = date(2026, 7, 13)) -> None:
        self.start = start

    def date_of_day(self, d: int) -> date:
        return self.start + timedelta(days=int(d))

    def table_weekday(self, d: int) -> int:
        return self.date_of_day(d).weekday()


def _layer(n: int = 4) -> CS1.CalendarSelf:
    shape = (n, 1, 7)
    commit = np.zeros(shape, dtype=np.int64)
    commit[:, :, :5] = CSH.COMMIT_WORK
    start = np.where(commit > 0, 540, -1)
    end = np.where(commit > 0, 1080, -1)
    cols = {"commit": commit, "start_min": start, "end_min": end, "depart_min": start - 40, "return_min": end + 40,
            "lead_min": np.where(commit > 0, 40, -1), "place_kind": np.where(commit > 0, 1, 0),
            "target_cell": np.where(commit > 0, 3, -1), "recurrence": np.where(commit > 0, 1, 0),
            "certainty": np.where(commit > 0, 1, 0)}
    table = CSH.CalendarTable(n=n, n_weeks=1, cols=cols, found=np.ones(n, dtype=bool), version={"file": "x"},
                              agent_id=np.arange(n))
    nxt = np.array([[0, 1, 1, 1], [0, 1, 2, 2], [1, 1, 2, 3], [2, 2, 2, 3]])
    world = SimpleNamespace(
        assets=SimpleNamespace(cell_rep_node=np.arange(4)),
        graph=SimpleNamespace(route_next_node=lambda u, v: nxt[np.asarray(u), np.asarray(v)]))
    presence = SimpleNamespace(rail=None, home_cell=np.full(n, -1), line_of_agent=np.full(n, -1), absent=None,
                               blocks=None, arrival_tick=None, _exit_cells=lambda: np.array([0]))
    agents = SimpleNamespace(n=n, registry=SimpleNamespace(transit_state=np.full(n, 2, dtype=np.int8)))
    port = CS1.CommuteMockPort(seed=1, day_key0=0, step_seconds=60)
    layer = CS1.CalendarSelf(table, calendar=_Cal(), agents=agents, world=world, presence=presence, port=port,
                             agent_key=np.arange(100, 100 + n), seed=1, step_seconds=60, steps_per_day=1440)
    layer.cal_store["placement"][:] = [CS1.PL_APP, CS1.PL_ALARM, CS1.PL_PLANNER, CS1.PL_HEAD][:n]
    return layer


def test_placement_decides_how_the_plan_comes_back():
    layer = _layer()
    layer.relay_day(0)
    s = layer.cal_store
    assert s["managed"].all() and (s["route"] == CS1.RT_IN).all()
    # 見積り(AT2)=駅の口(セル 0)から職場(セル 3)まで 3 節+域外 37 分・幅 0(路線なし=便の間隔なし)
    assert s["est_lo"].tolist() == [40.0] * 4 and s["walk_go"].tolist() == [3] * 4 and s["d_out"].tolist() == [37] * 4
    plan = s["plan_T"]
    # 〔検収 M2 (b)〕予定の出発は通知とアラームを置く体だけ判断の口の答えから(手帳と頭の中は口を通さない=空欄)
    assert (plan[:2] == 540 - 40 - s["margin"][:2]).all() and (plan[2:] == -1).all()
    assert s["next_trig"].tolist() == [CS1.TR_APP, CS1.TR_ALARM, CS1.TR_PLANNER, CS1.TR_HEAD]
    assert s["next_T"][0] == plan[0] and s["next_T"][1] == plan[1]  # アプリ=通知・アラーム=鳴る(本人が置いた時刻)
    assert s["next_T"][2] == 0  # 手帳=その日の最初に起きている刻みに見る
    assert s["next_T"][3] == int(s["look_phase"][3])  # 頭の中=時計を見る習慣の位相
    # どの機会も本人の記録を参照に持つ(置いた通知・アラームは新しい id・手帳と頭の中は見る習慣の id)
    assert (s["next_ref"] > 0).all()
    assert s["next_ref"][2] == s["habit_ref"][2] and s["next_ref"][3] == s["habit_ref"][3]
    assert s["next_ref"][0] != s["habit_ref"][0]
    rec = layer.cal_meter["cur"]
    assert rec["managed"] == 4 and rec["by_placement"] == {"アプリ": 1, "アラーム": 1, "手帳": 1, "頭の中": 1}
    assert s["watch"].all() and layer.io_off.all()  # この 4 体は計画実行層の到着・退出を実行しない


def test_relay_excludes_broken_school_and_home_work():
    layer = _layer(4)
    cols = {k: np.array(v) for k, v in layer.table.cols.items()}
    cols["end_min"][0] = 500  # 終わり ≤ 始まり=壊れた予定(CA4)
    cols["commit"][1] = np.where(cols["commit"][1] > 0, CSH.COMMIT_SCHOOL, 0)  # 授業(時刻は渡さない段)
    cols["place_kind"][2] = np.where(cols["commit"][2] > 0, 7, 0)  # 自宅で働く
    table = CSH.CalendarTable(n=4, n_weeks=1, cols=cols, found=np.ones(4, dtype=bool), version={"file": "x"},
                              agent_id=np.arange(4))
    object.__setattr__(layer, "table", table)
    layer.relay_day(0)
    rec = layer.cal_meter["cur"]
    assert layer.cal_store["managed"].tolist() == [False, False, False, True]
    assert rec["rejected_broken"] == 1 and rec["excluded"]["壊れた予定"] == 1
    assert rec["excluded"]["授業(時刻が空欄)"] == 1 and rec["excluded"]["自宅で働く"] == 1
    layer.relay_day(5)  # 土曜=約束なし
    assert not layer.cal_store["managed"].any() and str(0) in layer.cal_meter["days"]


# ================================================================= 〔検収 M2 (b)〕通知とアラームの時刻は判断の口を通す
class _NoTimePort(CS1.CommuteMockPort):
    """答えに「次に見る時刻」を返さない口(植えた写し)。"""

    def _answer(self, ctx, presented):  # noqa: ANN001, ANN201
        cid, _extra = super()._answer(ctx, presented)
        return next(c.id for c in presented if c.source == SOURCE_CONTINUE), {}


def test_reminder_times_come_through_choose():
    layer = _layer()
    calls = []
    orig = layer.port.choose

    def spy(ctx, cands):  # noqa: ANN001, ANN202
        calls.append(ctx.call_id)
        return orig(ctx, cands)

    layer.port.choose = spy
    layer.relay_day(0)
    assert len(calls) == 2 and all(c.startswith("cal1b-set:") for c in calls)  # アプリとアラームの 2 体
    assert layer.cal_meter["cur"]["reminders_set"] == 2
    # 負の対照: 答えに時刻の無い口では空欄(0 時にしない)
    bad = _layer()
    object.__setattr__(bad, "port", _NoTimePort(seed=1, day_key0=0, step_seconds=60))
    bad.relay_day(0)
    s = bad.cal_store
    assert s["next_T"][0] == -1 and s["next_T"][1] == -1 and bad.cal_meter["cur"]["reminders_blank"] == 2
    assert s["next_T"][2] == 0 and s["next_T"][3] == int(s["look_phase"][3])  # 手帳と頭の中は口を通さない習慣


def test_clock_tool_row_decides_minute_reading():
    """〔検収 L4〕時計の道具の行を読む(知っていれば分単位で読める)。"""
    from shibuya.engine.tools import registry as TR

    layer = _layer()
    assert layer._clock_known(0)  # 台帳が無ければ知っている扱い
    object.__setattr__(layer, "tools", TR.default_registry())
    assert layer._clock_known(0)
    reg = TR.ToolRegistry([TR.Tool(name=TR.CLOCK, known_by=TR.NOBODY, owner="本人", content_writer="機械", stage="6-2")])
    object.__setattr__(layer, "tools", reg)
    assert not layer._clock_known(0)


def test_first_entering_train_reads_the_rail_table():
    rail = SimpleNamespace(enter_tick=np.array([10, 5, 30, 20, 20]), train_line=np.array([0, 1, 0, 0, 0]))
    assert CS1.first_entering_train(rail, 0, 11) == 3  # 同着(20)は索引の小さい方
    assert CS1.first_entering_train(rail, 0, 0) == 0 and CS1.first_entering_train(rail, 1, 6) == -1


# ================================================================= 〔検収 M1〕逆算の AST の検査
FORBIDDEN_STRICT = frozenset({"start_T", "d_out", "walk_go", "lead"})


def _str_keys(node, tainted):  # noqa: ANN001, ANN202
    import ast

    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.add(n.value)
        elif isinstance(n, ast.Name) and n.id in tainted:
            out |= tainted[n.id]
    return out


def _store_key(tgt):  # noqa: ANN001, ANN202
    import ast

    # s["next_T"][...] = … / s["next_T"] = …
    while isinstance(tgt, ast.Subscript):
        if isinstance(tgt.slice, ast.Constant) and isinstance(tgt.slice.value, str):
            return tgt.slice.value
        tgt = tgt.value
    return None


def backward_assignments(src: str) -> list[tuple[str, str, list[str]]]:
    """機会の時刻(``next_T``・``plan_T``)を約束の始まりや道のり(``start_T``・``d_out``・``walk_go``・``lead``)から作る代入と、
    到着の時刻(``arr_T``)を約束の始まりから作る代入(域外の時間から前へ進める到着=物理は許す)。局所の名を通して追う。"""
    import ast

    hits = []
    for fn in ast.walk(ast.parse(src)):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        tainted: dict[str, set[str]] = {}
        assigns = [n for n in ast.walk(fn) if isinstance(n, (ast.Assign, ast.AugAssign))]
        for _ in range(4):  # 局所の名の受け渡しを固定点まで
            for n in assigns:
                tg = n.targets if isinstance(n, ast.Assign) else [n.target]
                keys = _str_keys(n.value, tainted)
                for t in tg:
                    if isinstance(t, ast.Name):
                        tainted[t.id] = tainted.get(t.id, set()) | keys
        for n in assigns:
            tg = n.targets if isinstance(n, ast.Assign) else [n.target]
            keys = _str_keys(n.value, tainted)
            for t in tg:
                k = _store_key(t)
                if k in ("next_T", "plan_T"):
                    bad = sorted(keys & FORBIDDEN_STRICT)
                elif k == "arr_T":
                    bad = sorted(keys & {"start_T"})
                else:
                    continue
                if bad:
                    hits.append((fn.name, k, bad))
    return hits


def test_no_backward_assignment_in_the_layer():
    src = Path(CS1.__file__).read_text(encoding="utf-8")
    assert backward_assignments(src) == []


def test_negative_backward_assignment_with_a_reference_id_is_caught():
    planted = (Path(CS1.__file__).read_text(encoding="utf-8") + """

def _planted(self, ids):
    s = self.cal_store
    true_travel = self._steps(s["d_out"][ids] + s["walk_go"][ids])
    when = s["start_T"][ids] - true_travel
    s["next_T"][ids] = when
    s["next_ref"][ids] = s["habit_ref"][ids]  # 参照の id を付けたまま
""")
    hits = backward_assignments(planted)
    assert ("_planted", "next_T", ["d_out", "start_T", "walk_go"]) in hits
