"""第 6 期 6-2 カレンダー 1b(腕 ``--calendar 1b``)のランの受入の試験。

- 既定(w17)は層を作らない(manifest に ``calendar_1b`` が無い・2 日の再開=通し)。19 構成の byte-check は記録の JSON。
- 腕 1b: ランが最後まで回る・出発と帰宅が本人の判断の記録(候補の口の記録=源 plan・提示の番号)から出ている・
  エンジンが時刻で強制退出した体 0・逆算して起こした体 0・間に合う便を選んだ 0・E4 の消去 0(負の対照=それぞれを植えた写しで
  検査が落ちる)・就寝と起床は W17 のまま(就寝の事象の数が同じ)・計器の表が出る・再開=通し・段 B(書く欄が宣言の中)。
- 5,000 体(w6_v3_default=語彙 v3・活動層・1 日)は slow。
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from shibuya import cli
from shibuya.engine import calendar_self as CS1
from shibuya.engine import resolve as R
from shibuya.engine.presence import EventType, PlanExecutor
from shibuya.engine.run import run_day

WORLD = Path("data/world/v2")
#: W20 の週の表。〔第 4 期 4-3 段 10〕世界資産が自分の表を持てばそれ(差し替えの世界=W21 の体の表・エンジンの既定の道筋
#: ``<world_dir>/w20_calendar_1a.parquet`` と同じ)・無ければ段の資産 v2_stage_3-1 の表(W16 の世界・前のまま)。
W20 = (WORLD / "w20_calendar_1a.parquet" if (WORLD / "w20_calendar_1a.parquet").is_file()
       else Path("data/world/v2_stage_3-1") / "w20_calendar_1a.parquet")
real_data = pytest.mark.requires_data("world_v2:w17_schedule.parquet")
TPD = 1_440
KW = dict(n_agents=300, seed=1, world_dir=str(WORLD), vocab_version="v3", activity=True)


@pytest.fixture
def w20(monkeypatch):
    if not W20.is_file():
        pytest.skip("requires_data: W20 の週の表(data/world/v2 か v2_stage_3-1 の w20_calendar_1a.parquet)が無い")
    monkeypatch.setenv("SHIBUYA_CALENDAR_W20", str(W20))
    return W20


@pytest.fixture
def arm_1b():
    prev = CS1.arm()
    CS1.set_arm(CS1.MODE_1B)
    try:
        yield
    finally:
        CS1.set_arm(prev)


def _cal(res) -> dict:
    return res.run_manifest_fields()[CS1.MANIFEST_KEY]


#: 就寝の境界の事象の内訳(``resolve.begin_planned_sleep`` の 7 つ=事象 1 つが 1 つに入る)。``woke``(起こした体)と
#: ``arrived``(就寝地へ歩いて着いて寝た体)は体の居場所で変わる=事象の数ではない。
SLEEP_EVENT_KEYS = ("slept", "walking", "riding", "outside", "conversing", "asleep", "unreachable")


def _sleep_events(res) -> int:
    c = dict(res.planned_sleep_counts)
    return int(sum(int(c.get(k, 0)) for k in SLEEP_EVENT_KEYS))


# ================================================================= 既定(w17)
def test_default_has_no_layer_and_no_manifest_key():
    res = run_day(n_agents=20, n_cells=9, ticks=30, seed=1, renderer="stub", processes=False)
    assert CS1.MANIFEST_KEY not in res.run_manifest_fields()
    assert getattr(res, "calendar_self_layer", "x") is None


def test_arm_1b_needs_the_population_and_the_plan_executor(arm_1b):
    with pytest.raises(ValueError, match="母集団"):
        run_day(n_agents=20, n_cells=9, ticks=30, seed=1, renderer="stub", processes=False)


@real_data
def test_default_two_days_resume_equals_straight(tmp_path, w20):
    """既定(w17)の 2 日のランの再開=通し(層は無い・manifest に 1b の節は無い)。"""
    kw = dict(KW, sim_days=2)
    straight = cli.run(**kw)
    a = cli.run(state_out=tmp_path / "s", stop_at_tick=TPD, **kw)
    b = cli.run(resume_from=tmp_path / "s" / a.resume["state_files"][-1]["file"], **kw)
    assert b.final_hash == straight.final_hash
    assert CS1.MANIFEST_KEY not in straight.run_manifest_fields()


# ================================================================= 腕 1b(300 体・1 日)
@pytest.fixture(scope="module")
def pair():
    if not W20.is_file():
        pytest.skip("requires_data: W20 の週の表(data/world/v2 か v2_stage_3-1 の w20_calendar_1a.parquet)が無い")
    mp = pytest.MonkeyPatch()
    mp.setenv("SHIBUYA_CALENDAR_W20", str(W20))
    counts: dict[str, dict[int, int]] = {}
    orig = PlanExecutor._run_type
    label = {"run": "w17"}

    def counted(self, ty, ids, arg, tick, act, place):  # noqa: ANN001, ANN202
        c = counts.setdefault(label["run"], {})
        c[int(ty)] = c.get(int(ty), 0) + int(np.asarray(ids).size)  # 〔検収 L11〕計画実行層が配った事象の数(種類ごと)
        return orig(self, ty, ids, arg, tick, act, place)

    mp.setattr(PlanExecutor, "_run_type", counted)
    prev = CS1.arm()
    try:
        base = cli.run(**KW)
        CS1.set_arm(CS1.MODE_1B)
        label["run"] = "1b"
        arm = cli.run(**KW)
    finally:
        CS1.set_arm(prev)
        mp.undo()
    base.event_counts, arm.event_counts = counts["w17"], counts["1b"]
    return base, arm


def _check_decisions_drive_trips(layer, m) -> None:
    s = layer.cal_store
    tr = {k: np.asarray(v) for k, v in layer.cal_meter["cur"]["trips"].items()}  # 〔検収 L6〕判断の行は日ごと
    man = s["managed"]
    go = np.flatnonzero(man & (s["go_T"] >= 0))
    back = np.flatnonzero(man & (s["back_T"] >= 0))
    assert go.size > 0 and back.size > 0
    key = set(zip(tr["agent"].tolist(), tr["trip"].tolist(), tr["T"].tolist()))
    assert all((int(a), CS1.TRIP_GO, int(s["go_T"][a])) in key for a in go)  # 出発=本人の判断の記録
    assert all((int(a), CS1.TRIP_BACK, int(s["back_T"][a])) in key for a in back)  # 帰る=本人の判断の記録
    assert set(tr["source"].tolist()) == {"plan"} and set(tr["n_cand"].tolist()) == {3}
    assert set(tr["number"].tolist()) <= {1, 2, 3}
    # 着いた体はどれも出発の判断の後(体は判断なしに動かない)
    arr = np.flatnonzero(man & (s["arrive_T"] >= 0))
    assert (s["go_T"][arr] >= 0).all() and (s["arrive_T"][arr] >= s["go_T"][arr]).all()
    home = np.flatnonzero(man & (s["home_T"] >= 0))
    assert (s["back_T"][home] >= 0).all() and (s["home_T"][home] >= s["back_T"][home]).all()
    ch = m["checks"]
    assert ch["exits_unexplained"] == 0 and ch["exits_during_walk"] == 0 and ch["appear_unexplained"] == 0
    assert ch["backward_wakes"] == 0 and ch["selected_trains"] == 0 and ch["inbound_checked"] > 0


@real_data
def test_1b_runs_and_the_person_decides_the_trips(pair):
    base, arm = pair
    layer = arm.calendar_self_layer
    m = _cal(arm)
    assert layer is not None and m["mode"] == "1b" and m["port"] == "mock" and m["schema"] == CS1.SCHEMA
    _check_decisions_drive_trips(layer, m)
    d = m["days"][0]
    assert d["managed"] > 0 and d["go"]["decided"] > 0 and d["back"]["decided"] > 0
    assert d["suppressed_w17"]["arrive"] > 0 and d["suppressed_w17"]["depart"] > 0  # W17 の出入りを実行していない
    assert d["decisions"]["by_trigger"]["終わりの時刻"] == m["checks"]["end_notices"]
    # 計器の表(CA8)の欄
    for k in ("go", "back", "commute", "plan_match", "at_rate15", "switches", "decisions", "excluded", "w17_ref"):
        assert k in d, k
    for k in ("arrive_minus_start", "early5", "late", "late_rate", "impossible", "forgot", "forgot_rate"):
        assert k in d["go"], k
    assert m["bridges"]["count"] is not None and set(m["bridges"]["rows"]) == set(CS1.BRIDGES)
    json.dumps(m, ensure_ascii=False)
    # 判断の出来事(1-3)=行為:移動・原因 LlmCall(源 plan と番号)。既定のランには無い
    assert arm.run_manifest_fields()["run_kind"] in ("test", "arm")
    assert CS1.MANIFEST_KEY not in base.run_manifest_fields()


@real_data
def test_1b_keeps_the_w17_sleep_and_wake(pair):
    base, arm = pair
    assert _sleep_events(arm) == _sleep_events(base) > 0  # 就寝の境界の事象の数は W17 のまま
    pr = arm.calendar_self_layer.presence
    assert int(np.count_nonzero(pr.ev_type == EventType.SLEEP)) > 0 and int(np.count_nonzero(pr.ev_type == EventType.WAKE)) > 0
    # 〔検収 L11〕起床の事象も同じ数(計画実行層が配った就寝と起床の事象=W17 のまま)・到着と退出は管理する体の分だけ止まる前の配り
    eb, ea = base.event_counts, arm.event_counts
    assert ea[EventType.SLEEP] == eb[EventType.SLEEP] > 0 and ea[EventType.WAKE] == eb[EventType.WAKE] > 0


@real_data
def test_1b_counts_the_place_by_the_body_position_and_reoffers_after_leaving(pair):
    """〔検収 H1〕計画一致率と 15 分の在場率は体の位置で数える(段の値は *_phase)。勤務中に本人の行為で舞台を出た体には、
    約束が続いている間は次の機会を出す(段は「約束の場所」のまま域外に居る体が残らない)。"""
    _base, arm = pair
    layer = arm.calendar_self_layer
    d = _cal(arm)["days"][0]
    pm = [(a, b) for a, b in zip(d["plan_match"], d["plan_match_phase"]) if a is not None]
    assert pm and all(a <= b + 1e-9 for a, b in pm)  # 位置で数えた値は段の値を超えない
    assert {"left_bodies", "returned_bodies", "left", "returned"} <= set(d["away"])
    assert d["away"]["left"] == d["left_at_work"] and d["away"]["returned"] == d["back_to_work"]
    s = layer.cal_store
    st = np.asarray(layer.agents.registry.transit_state)
    last = int(layer.cal_meter["last_T"])
    stuck = (s["managed"] & (s["phase"] == CS1.PH_AT) & (st == 2) & (s["place_kind"] != CS1._PK_OUTSIDE)
             & (s["end_T"] > last))
    assert int(stuck.sum()) == 0


@real_data
def test_inbound_trains_by_the_rail_table_and_on_time(pair):
    """〔検収 L2・L1〕到着の便を実装と別に鉄道の表から直に引く(準備の時刻以降に最初にホームへ入るその路線の便)・着いた刻み
    =その便がホームへ入る刻み(1 刻み遅れない)。"""
    _base, arm = pair
    layer = arm.calendar_self_layer
    rows = layer.cal_meter["cur"]["inbound"]
    assert rows
    enter = np.asarray(layer.rail.enter_tick, dtype=np.int64)
    line_of = np.asarray(layer.rail.train_line, dtype=np.int64)
    for agent, ready, train, line, at in rows:
        cand = np.flatnonzero((line_of == line) & (enter >= ready))
        first = cand[np.lexsort((cand, enter[cand]))][0]
        assert int(first) == int(train), (agent, ready, train)
        assert int(at) == int(enter[train]), (agent, at, int(enter[train]))


@real_data
def test_attendance_lottery_below_one_is_kept(w20, arm_1b):
    """〔検収 L3〕出勤率 < 1: くじで休む体は管理しない(計画実行層のくじと同じ体)。"""
    # 300 体の抽出は出勤率の対象の種別(通勤者 0・通学者 5)を含まない=1,000 体・日の頭だけ(5 刻み)
    res = cli.run(**{**KW, "n_agents": 1000}, attendance_rate=0.5, ticks=5)
    layer = res.calendar_self_layer
    absent = np.asarray(layer.presence.absent, dtype=bool)
    assert absent.any() and np.array_equal(layer._absent(0), absent)
    assert not (layer.cal_store["managed"] & absent).any()
    assert _cal(res)["days"][0]["excluded"]["出勤率のくじ"] > 0


# ================================================================= 負の対照(植えた写しで検査が落ちる)
def _run_1b() -> dict:
    prev = CS1.arm()
    CS1.set_arm(CS1.MODE_1B)
    try:
        return _cal(cli.run(**KW))
    finally:
        CS1.set_arm(prev)


@real_data
def test_negative_forced_exit_by_time_is_caught(w20, monkeypatch):
    """植えた写し: 計画実行層が管理する体の W17 の DEPART を実行する(時刻で強制的に退出)→ 検査が数える。"""
    orig = PlanExecutor._do_depart

    def forced(self, ids, lines, tick):  # noqa: ANN001, ANN202
        hook = self.io_hook
        self.io_hook = None
        try:
            orig(self, ids, lines, tick)
        finally:
            self.io_hook = hook

    monkeypatch.setattr(PlanExecutor, "_do_depart", forced)
    assert _run_1b()["checks"]["exits_unexplained"] > 0


@real_data
def test_negative_backward_wake_is_caught(w20, monkeypatch):
    """植えた写し: エンジンが本当の道のり(域外の時間+歩き)から逆算した時刻に起こす(本人の記録を参照しない)→ 検査が数える。"""
    orig = CS1.CalendarSelf._set_reminders

    def backward(self, ids, T0):  # noqa: ANN001, ANN202
        orig(self, ids, T0)
        s = self.cal_store
        true_travel = self._steps(s["d_out"][ids] + s["walk_go"][ids])
        s["next_T"][ids] = np.maximum(s["start_T"][ids] - true_travel, T0)
        s["next_ref"][ids] = -1
        s["next_trig"][ids] = CS1.TR_HEAD

    monkeypatch.setattr(CS1.CalendarSelf, "_set_reminders", backward)
    assert _run_1b()["checks"]["backward_wakes"] > 0


@real_data
def test_negative_selecting_the_train_in_time_is_caught(w20, monkeypatch):
    """植えた写し: エンジンが約束に間に合う最も遅い便(E1)を選ぶ → 到着の便が「来た便」でないので検査が数える。"""
    orig = CS1.CalendarSelf._inbound

    def e1(self, ids, ready, trip):  # noqa: ANN001, ANN202
        orig(self, ids, ready, trip)
        s = self.cal_store
        for a in np.asarray(ids).tolist():
            line = int(s["line"][a])
            tab = self._line_tab.get(line)
            if tab is None or s["arr_train"][a] < 0:
                continue
            ent, order = tab
            want = int(s["start_T"][a]) - int(self._steps(s["walk_go"][a]))
            k = int(np.searchsorted(ent, want, side="right")) - 1
            if k >= 0 and int(ent[k]) >= int(s["arr_ready_T"][a]):
                s["arr_train"][a] = int(order[k])
                s["arr_T"][a] = int(ent[k])

    monkeypatch.setattr(CS1.CalendarSelf, "_inbound", e1)
    assert _run_1b()["checks"]["selected_trains"] > 0


@real_data
def test_negative_e4_vanish_is_caught(w20, monkeypatch):
    """植えた写し(E4): 歩きが途切れた体をその場で域外へ消す → 検査が歩きの途中の消去を数える。"""

    def vanish(self, ids, T):  # noqa: ANN001, ANN202
        R.rail_depart(self.agents, ids, np.full(np.asarray(ids).size, -1, dtype=np.int64))

    monkeypatch.setattr(CS1.CalendarSelf, "_interrupt", vanish)
    ch = _run_1b()["checks"]
    assert ch["exits_during_walk"] > 0 and ch["exits_unexplained"] >= ch["exits_during_walk"]


# ================================================================= 再開=通し・段 B・CLI
@real_data
def test_1b_resume_equals_straight_over_two_days(tmp_path, w20, arm_1b):
    kw = dict(KW, sim_days=2)
    straight = cli.run(**kw)
    a = cli.run(state_out=tmp_path / "state", stop_at_tick=TPD, **kw)
    f = tmp_path / "state" / a.resume["state_files"][-1]["file"]
    b = cli.run(resume_from=f, **kw)
    assert b.final_hash == straight.final_hash
    ms, mb = _cal(straight), _cal(b)
    assert [d["day"] for d in ms["days"]] == [0, 1] and ms["days"] == mb["days"] and ms["checks"] == mb["checks"]
    assert ms["days"][1]["date"] == "2026-07-14" and ms["days"][1]["table_weekday"] == 1
    assert ms["checks"]["exits_unexplained"] == 0 and ms["checks"]["backward_wakes"] == 0
    CS1.set_arm(CS1.MODE_W17)
    with pytest.raises(ValueError, match="再開の設定が親と違う"):
        cli.run(resume_from=f, **kw)


@real_data
def test_1b_writes_stay_inside_the_declarations(w20, monkeypatch, arm_1b):
    """段 B(``SHIBUYA_SYSTEMS_CHECK``): 腕 1b の 2 日のランで、系の前後で変わった欄は宣言の書く欄の中。"""
    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "60")
    res = cli.run(n_agents=200, seed=1, world_dir=str(WORLD), sim_days=2, vocab_version="v3", activity=True)
    assert [d["day"] for d in _cal(res)["days"]] == [0, 1]


@real_data
def test_cli_flag_run_kind_and_fingerprint(w20, tmp_path, monkeypatch):
    from shibuya.engine import resume as RS

    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)  # ランの種類を CLI の規則で決めさせる
    prev = CS1.arm()
    try:
        argv = ["--agents", "200", "--seed", "1", "--world", str(WORLD), "--ticks", "60"]
        got = {}
        for mode in ("w17", "1b"):
            out = tmp_path / f"{mode}.json"
            assert cli.main([*argv, "--calendar", mode, "--checkpoints-out", str(out)]) == 0
            assert CS1.arm() == mode
            got[mode] = json.loads(out.read_text(encoding="utf-8"))["manifest"]
        assert got["w17"]["run_kind"] == "reproduction" and got["1b"]["run_kind"] == "arm"
        assert CS1.MANIFEST_KEY not in got["w17"] and got["1b"][CS1.MANIFEST_KEY]["mode"] == "1b"
        heads = {}
        for mode in ("w17", "1b"):
            CS1.set_arm(mode)
            r = cli.run(n_agents=200, seed=1, world_dir=str(WORLD), state_out=tmp_path / f"st_{mode}", stop_at_tick=30)
            heads[mode] = RS.read_state(tmp_path / f"st_{mode}" / r.resume["state_files"][-1]["file"]).header["fingerprint"]
        assert CS1.FP_KEY not in heads["w17"] and heads["1b"][CS1.FP_KEY] == "1b"
        assert {k: v for k, v in heads["1b"].items() if k != CS1.FP_KEY} == heads["w17"]
    finally:
        CS1.set_arm(prev)


# ================================================================= 5,000 体(w6_v3_default・1 日)
@pytest.mark.slow
@real_data
def test_1b_5000_bodies_one_day(w20):
    kw = dict(n_agents=5000, seed=1, world_dir=str(WORLD), vocab_version="v3", activity=True)
    prev = CS1.arm()
    try:
        base = cli.run(**kw)
        CS1.set_arm(CS1.MODE_1B)
        arm = cli.run(**kw)
    finally:
        CS1.set_arm(prev)
    m = _cal(arm)
    _check_decisions_drive_trips(arm.calendar_self_layer, m)
    d = m["days"][0]
    assert d["managed"] > 2000 and d["go"]["arrived"] > 0.95 * d["managed"]
    assert _sleep_events(arm) == _sleep_events(base)
