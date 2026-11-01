"""第 3 期 3-1 エンジン側の影を読む口(``engine.calendar_shadow``・腕 ``--calendar-shadow {w17,1a}``)の受入の試験。

- 既定 w17 は影を作らない(manifest の ``calendar_shadow`` は源だけ・観測の子は null)=19 構成の byte-check は記録。
- 腕 1a: 1 日のランで勤務の影が W20 の週の表から来る(出勤・始業・終業・帰宅の 15 分の分布が表の行と一致)・挙動は不変
  (final・behavior-hash・計画実行層の計数=W17 のつなぎの行は不変)・再開=通し(2 日・日の境目)・1a のランだけ設定の指紋。
- 宣言(状態台帳の行 CAL=軸 1 diag・軸 2 derivable・hash_skip・manifest の節・系の表の書く欄)と構築側との定数の一致。
"""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from shibuya import cli
from shibuya.engine import calendar_shadow as CS
from shibuya.engine import manifest_sections as MS
from shibuya.engine import state_ledger as SL
from shibuya.engine.run import run_day
from shibuya.engine.systems.table import SPECS

WORLD = Path("data/world/v2")
real_data = pytest.mark.requires_data("world_v2:w17_schedule.parquet")
TPD = 1_440


@pytest.fixture
def arm_1a():
    prev = CS.arm()
    CS.set_arm(CS.MODE_1A)
    try:
        yield
    finally:
        CS.set_arm(prev)


# ================================================================= 宣言と定数
def test_constants_match_the_build_side_and_the_calendar():
    from shibuya.build.sched import w20_calendar_1a as W
    from shibuya.engine.calendar import DEFAULT_WORLD_START

    assert CS.FILE_NAME == W.OUTPUT_NAME and CS.HEADER_NAME == W.HEADER_NAME
    assert CS.WEEK0_MONDAY == date.fromisoformat(W.WEEK0_MONDAY) == DEFAULT_WORLD_START.date()
    assert CS.WEEK0_MONDAY.weekday() == 0
    assert CS.COMMIT_WORK == W.COMMIT_WORK and CS.COMMIT_SCHOOL == W.COMMIT_SCHOOL
    assert set(CS._COLS) <= set(W.TABLE_SCHEMA.names)
    assert CS.DEFAULT_MODE == CS.MODE_W17 and CS.MODES == ("w17", "1a")
    with pytest.raises(ValueError):
        CS.set_arm("w20")


def test_manifest_section_ledger_row_and_system_declarations():
    assert "calendar_shadow" in MS.MIXED and MS.PATHS["calendar_shadow"] == MS.OBSERVED
    for k in CS.MANIFEST_CONFIG:
        assert MS.section_of(f"calendar_shadow.{k}") == MS.CONFIG, k
    for k in CS.MANIFEST_OBSERVED:
        assert MS.section_of(f"calendar_shadow.{k}") == MS.OBSERVED, k
    assert set(CS.manifest_fields(None)) == set(CS.MANIFEST_CONFIG) | set(CS.MANIFEST_OBSERVED)
    r = SL.row("CAL")
    assert r.behavior == SL.DIAG and r.restore == SL.DERIVABLE and set(r.hash_skip) == set(r.items) and not r.arm
    assert SL.OWNER_CLASSES["calendar_shadow"] == ("engine/calendar_shadow.py", "CalendarShadow")
    assert not any(k == "CAL" for k, _p in SL.full_items())
    assert "CAL:calendar_shadow.*" in SPECS["day_head"].writes.paths
    assert "layers.calendar_shadow" in SPECS["day_head"].reads.box


def test_default_has_no_shadow():
    res = run_day(n_agents=20, n_cells=9, ticks=30, seed=1, renderer="stub", processes=False)
    m = res.run_manifest_fields()["calendar_shadow"]
    assert m == CS.manifest_fields(None) and m["source"] == "w17" and m["days"] is None
    assert getattr(res, "calendar_shadow_layer", "x") is None


def test_arm_1a_needs_the_population(arm_1a):
    with pytest.raises(ValueError, match="母集団"):
        run_day(n_agents=20, n_cells=9, ticks=30, seed=1, renderer="stub", processes=False)


# ================================================================= 単体(作り物の表と暦)
class _Cal:
    def __init__(self, start: date, holidays: set[int] = frozenset()):
        self.start, self.holidays = start, set(holidays)

    def date_of_day(self, d: int) -> date:
        from datetime import timedelta

        return self.start + timedelta(days=int(d))

    def table_weekday(self, d: int) -> int:
        return 6 if d in self.holidays else self.date_of_day(d).weekday()

    def is_holiday(self, d: int) -> bool:
        return d in self.holidays


def _table(n: int = 6, weeks: int = 1) -> CS.CalendarTable:
    shape = (n, weeks, 7)
    commit = np.zeros(shape, dtype=np.int64)
    commit[:4, :, :5] = CS.COMMIT_WORK
    commit[4, :, :5] = CS.COMMIT_SCHOOL
    start = np.full(shape, -1, dtype=np.int64)
    end = np.full(shape, -1, dtype=np.int64)
    dep = np.full(shape, -1, dtype=np.int64)
    ret = np.full(shape, -1, dtype=np.int64)
    lead = np.full(shape, -1, dtype=np.int64)
    w = commit == CS.COMMIT_WORK
    dep[w] = np.repeat(np.array([420, 450, 480, 1290])[:, None], weeks * 5).reshape(4, weeks, 5).ravel()
    lead[w] = 30
    start[w] = dep[w] + 30
    ret[w] = np.where(dep[w] == 1290, 1890, dep[w] + 600)
    end[w] = ret[w] - 30
    cols = {"commit": commit, "start_min": start, "end_min": end, "depart_min": dep, "return_min": ret,
            "lead_min": lead, "place_kind": np.where(commit > 0, 1, 0), "target_cell": np.where(commit > 0, 3, -1),
            "recurrence": np.where(commit > 0, 1, 0), "certainty": np.where(commit > 0, 1, 0)}
    return CS.CalendarTable(n=n, n_weeks=weeks, cols=cols, found=np.ones(n, dtype=bool), version={"file": "x"},
                            agent_id=np.arange(n))


def test_unit_relay_day_records_follow_the_table():
    layer = CS.CalendarShadow(_table(), calendar=_Cal(date(2026, 7, 13)))
    layer.relay_day(0)
    r = layer.shadow_day_log[0]
    assert r["date"] == "2026-07-13" and r["weekday"] == 0 and r["week"] == 0 and not r["week_wrapped"]
    assert r["shadows"] == {"work": 4, "school": 1}
    assert r["blanks"] == {"no_commitment": 1, "school_time": 1, "not_in_table": 0}
    assert sum(r["depart_hist15"]) == 4 and r["depart_hist15"][420 // 15] == 1 and r["depart_hist15"][1290 // 15] == 1
    assert r["next_day_end"] == 1  # 夜の勤務(21:30 → 翌 7:00)
    rate = r["actor_rate15"]
    assert rate[0] == 0.0 and rate[600 // 15] == pytest.approx(3 / 6)
    layer.relay_day(5)  # 土曜=約束なし
    assert layer.shadow_day_log[5]["shadows"] == {"work": 0, "school": 0}
    layer.relay_day(9)  # 2 週目=1 週の表を巻き戻して使う(記録に印)
    assert layer.shadow_day_log[9]["week_wrapped"] and layer.shadow_day_log[9]["week"] == 0
    m = layer.manifest()
    assert [d["day"] for d in m["days"]] == [0, 5, 9] and m["shadows"]["work"] == 8 and m["source"] == "1a"
    hol = CS.CalendarShadow(_table(), calendar=_Cal(date(2026, 7, 13), {1}))
    hol.relay_day(1)
    h1 = hol.shadow_day_log[1]
    assert h1["holiday"] and h1["table_weekday"] == 6 and h1["shadows"]["work"] == 0


def test_guards_refuse_direct_writes():
    """〔検収 中 3〕影は計器だけ=外からの付け替え・消去・中身の書き込みは実行時に止まる(張り直しは relay_day の中だけ)。"""
    tab = _table()
    layer = CS.CalendarShadow(tab, calendar=_Cal(date(2026, 7, 13)))
    layer.relay_day(0)
    for name in ("table", "calendar", "weekly", "n", "source", "today", "shadow_day_log"):
        with pytest.raises(AttributeError):
            setattr(layer, name, None)
        with pytest.raises(AttributeError):
            delattr(layer, name)
    with pytest.raises(TypeError):
        layer.today["commit"] = None
    with pytest.raises(ValueError):
        layer.today["commit"][0] = 9
    with pytest.raises(TypeError):
        layer.shadow_day_log[1] = {}
    with pytest.raises(TypeError):
        layer.shadow_day_log[0]["shadows"]["work"] = 0
    with pytest.raises(TypeError):
        tab.cols["commit"] = np.zeros(1)
    with pytest.raises(TypeError):
        tab.version["file"] = "y"
    with pytest.raises(dataclasses.FrozenInstanceError):
        tab.cols = {}  # type: ignore[misc]
    for a in (*tab.cols.values(), tab.found, tab.agent_id):
        assert not a.flags.writeable
        with pytest.raises(ValueError):
            a[...] = 0
    src = np.zeros((2, 1, 7), dtype=np.int64)  # 渡した元の配列は書けるまま(写しを取る)
    t2 = CS.CalendarTable(n=2, n_weeks=1, cols={**{c: src for c in CS._COLS}}, found=np.ones(2, dtype=bool),
                          version={"file": "x"})
    assert src.flags.writeable and not t2.cols["commit"].flags.writeable
    layer.relay_day(1)  # 中の道の張り直しは通る・manifest は今の JSON の形(dict と list)
    m = layer.manifest()
    assert [d["day"] for d in m["days"]] == [0, 1] and type(m["days"][0]["shadows"]) is dict
    assert type(m["days"][0]["depart_hist15"]) is list and type(m["w20"]) is dict
    json.dumps(m)


def test_load_table_restricts_to_the_run_agents(tmp_path):
    from tests.build_sched.test_w20_calendar_1a import attrs, build
    from shibuya.build.geo import common as C
    from shibuya.build.sched import w20_calendar_1a as W

    a = attrs(60)
    t = build(a)["columns"]
    C.write_parquet(tmp_path, CS.FILE_NAME, t, schema=W.TABLE_SCHEMA)
    want = np.array([1005, 1001, 99999, 1059])
    tab = CS.load_table(tmp_path / CS.FILE_NAME, want)
    assert tab.found.tolist() == [True, True, False, True] and tab.n == 4 and tab.n_weeks == 1
    s = t["start_min"].reshape(60, 7)
    assert np.array_equal(tab.cols["start_min"][0, 0], s[5]) and np.array_equal(tab.cols["start_min"][3, 0], s[59])
    assert (tab.cols["commit"][2] == 0).all() and (tab.cols["start_min"][2] == -1).all()
    assert not tab.found.flags.writeable and not tab.cols["commit"].flags.writeable  # 〔検収 中 3〕
    with pytest.raises(FileNotFoundError):
        CS.load_table(tmp_path / "none.parquet", want)


# ================================================================= 実データ(世界資産・腕 1a)
@pytest.fixture(scope="module")
def w20_table(tmp_path_factory):
    """W16 の全員に作り物の材料で W20 の週の表を作る(エンジンの読み口の試験=表の中身の正しさは構築側の試験)。"""
    if not (WORLD / "w16_population.parquet").is_file():
        pytest.skip("requires_data: world_v2:w16_population.parquet が無い")
    import pyarrow.parquet as pq

    from tests.build_sched.test_w20_calendar_1a import ANCHOR, materials
    from shibuya.build.geo import common as C
    from shibuya.build.sched import w20_calendar_1a as W

    cols = pq.read_table(WORLD / "w16_population.parquet").to_pydict()
    a = W.attributes_from_columns(cols, {})
    m = materials()
    out = W.calendar_from_attributes(a, W.draw_employment_status(a, m, ANCHOR), m, ANCHOR)
    d = tmp_path_factory.mktemp("w20")
    C.write_parquet(d, CS.FILE_NAME, out["columns"], schema=W.TABLE_SCHEMA)
    return d / CS.FILE_NAME


KW = dict(n_agents=300, seed=1, world_dir=str(WORLD))


@pytest.fixture(scope="module")
def one_day_pair(w20_table):
    mp = pytest.MonkeyPatch()
    mp.setenv("SHIBUYA_CALENDAR_W20", str(w20_table))
    try:
        base = cli.run(**KW)
        prev = CS.arm()
        CS.set_arm(CS.MODE_1A)
        try:
            shadow = cli.run(**KW)
        finally:
            CS.set_arm(prev)
    finally:
        mp.undo()
    return base, shadow


@real_data
def test_1a_does_not_move_behavior_and_keeps_the_w17_bridges(one_day_pair):
    base, shadow = one_day_pair
    assert shadow.final_hash == base.final_hash
    assert [c.behavior_hash for c in shadow.checkpoints] == [c.behavior_hash for c in base.checkpoints]
    assert [c.full_hash for c in shadow.checkpoints] == [c.full_hash for c in base.checkpoints]
    assert shadow.llm_calls == base.llm_calls
    # W17 のつなぎの行(出入り・退出・就寝=計画実行層の計数)は不変
    assert shadow.presence_counters == base.presence_counters
    assert shadow.presence_exit == base.presence_exit
    mb = base.run_manifest_fields()
    ms = shadow.run_manifest_fields()
    diff = sorted(k for k in mb if mb[k] != ms[k] and k not in ("resume", "environment", "env_id", "run_kind"))
    assert diff == ["calendar_shadow"], diff


@real_data
def test_1a_shadow_comes_from_the_w20_table(one_day_pair, w20_table):
    """1 日のランの勤務の影は W20 の表の行(その日の曜日・ランの体)そのもの(出勤・始業・終業・帰宅の分布が一致)。"""
    import pyarrow.parquet as pq

    _base, shadow = one_day_pair
    layer = shadow.calendar_shadow_layer
    m = shadow.run_manifest_fields()["calendar_shadow"]
    assert m["source"] == "1a" and m["weeks"] == 1 and m["w20"]["file"] == CS.FILE_NAME
    rec = m["days"][0]
    assert rec["date"] == "2026-07-13" and rec["table_weekday"] == 0 and rec["agents"] == 300
    t = pq.read_table(w20_table).to_pydict()
    aid = np.asarray(t["agent_id"])
    wd = np.asarray(t["weekday"])
    sel = np.isin(aid, layer.table.agent_id) & (wd == 0)
    commit = np.asarray(t["commit"])[sel]
    w = commit == CS.COMMIT_WORK
    assert rec["shadows"] == {"work": int(w.sum()), "school": int((commit == CS.COMMIT_SCHOOL).sum())}
    for key, col in (("depart_hist15", "depart_min"), ("start_hist15", "start_min"), ("end_hist15", "end_min"),
                     ("return_hist15", "return_min")):
        v = np.asarray(t[col])[sel][w].astype(np.int64)
        assert rec[key] == np.bincount((v % TPD) // 15, minlength=96).tolist(), key
    assert rec["commute_min"]["n"] == int(w.sum())
    assert "w17_ref" in rec and rec["w17_ref"]["both"] + rec["w17_ref"]["w20_only"] == int(w.sum())


@real_data
def test_1a_fingerprint_and_missing_table(arm_1a, tmp_path, monkeypatch):
    """1a のランだけ設定の指紋に入る(既定は今の指紋)・表が無ければ組み立てで止まる。"""
    monkeypatch.delenv("SHIBUYA_CALENDAR_W20", raising=False)
    empty = tmp_path / "w"
    empty.mkdir()
    monkeypatch.setenv("SHIBUYA_CALENDAR_W20", str(empty / CS.FILE_NAME))
    with pytest.raises(FileNotFoundError):
        cli.run(**KW, ticks=5)


@real_data
def test_1a_resume_equals_straight_over_two_days(w20_table, tmp_path, monkeypatch, arm_1a):
    """2 日のランを日の境目で止めて再開=通しと同じ final と同じ影の記録(影は W20・暦・日番号だけから決まる)。
    腕を違えた再開は設定の指紋で止まる。"""
    monkeypatch.setenv("SHIBUYA_CALENDAR_W20", str(w20_table))
    kw = dict(KW, sim_days=2, vocab_version="v3", activity=True)
    straight = cli.run(**kw)
    a = cli.run(state_out=tmp_path / "state", stop_at_tick=TPD, **kw)
    f = tmp_path / "state" / a.resume["state_files"][-1]["file"]
    b = cli.run(resume_from=f, **kw)
    assert b.final_hash == straight.final_hash
    ms, mb = straight.run_manifest_fields()["calendar_shadow"], b.run_manifest_fields()["calendar_shadow"]
    assert [d["day"] for d in ms["days"]] == [0, 1] and ms["days"] == mb["days"]
    assert ms["days"][1]["date"] == "2026-07-14" and ms["days"][1]["table_weekday"] == 1
    CS.set_arm(CS.MODE_W17)
    with pytest.raises(ValueError, match="再開の設定が親と違う"):
        cli.run(resume_from=f, **kw)


@real_data
def test_1a_writes_stay_inside_the_declarations(w20_table, monkeypatch, arm_1a):
    """段 B(``SHIBUYA_SYSTEMS_CHECK``): 腕 1a の 2 日のランで、系の前後で変わった欄は宣言の書く欄の中(日の頭の
    ``CAL:calendar_shadow.*``)。"""
    monkeypatch.setenv("SHIBUYA_CALENDAR_W20", str(w20_table))
    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "60")
    res = cli.run(n_agents=200, seed=1, world_dir=str(WORLD), sim_days=2, vocab_version="v3", activity=True)
    assert [d["day"] for d in res.run_manifest_fields()["calendar_shadow"]["days"]] == [0, 1]


# ================================================================= CLI(検収 低 8)
@pytest.fixture
def keep_arm():
    prev = CS.arm()
    try:
        yield
    finally:
        CS.set_arm(prev)


NO_WORLD = ["--agents", "20", "--seed", "1", "--world", "__no_such_dir__", "--cells", "9", "--ticks", "30"]


def _cli_sub(tmp_path, name: str, env_arm: str, extra: list[str]) -> subprocess.CompletedProcess:
    """別のプロセスの CLI(環境変数 ``SHIBUYA_CALENDAR_SHADOW`` は import のときに読まれる)。試験の印は外す。"""
    out = tmp_path / f"{name}.json"
    e = {k: v for k, v in os.environ.items() if k != "PYTEST_CURRENT_TEST"}
    e.update(PYTHONIOENCODING="utf-8", SHIBUYA_CALENDAR_SHADOW=env_arm)
    code = "import sys; from shibuya import cli; sys.exit(cli.main(sys.argv[1:]))"
    return subprocess.run([sys.executable, "-c", code, *NO_WORLD, "--checkpoints-out", str(out), *extra],
                          capture_output=True, text=True, encoding="utf-8", env=e, timeout=600)


def test_cli_flag_beats_the_environment(tmp_path):
    """``--calendar-shadow`` は環境変数より強い: 環境 1a でも w17 を渡せば母集団の無いランが通る(源 w17・ランの種類 reproduction)。
    環境 w17 でも 1a を渡せば母集団の無いランは止まる(腕が置かれた)。何も渡さなければ環境変数の腕。"""
    ok = _cli_sub(tmp_path, "env1a_cliw17", "1a", ["--calendar-shadow", "w17"])
    assert ok.returncode == 0, ok.stderr[-2000:]
    m = json.loads((tmp_path / "env1a_cliw17.json").read_text(encoding="utf-8"))["manifest"]
    assert m["calendar_shadow"]["source"] == "w17" and m["calendar_shadow"]["days"] is None
    assert m["run_kind"] == "reproduction"
    for name, env_arm, extra in (("envw17_cli1a", "w17", ["--calendar-shadow", "1a"]), ("env1a_none", "1a", [])):
        r = _cli_sub(tmp_path, name, env_arm, extra)
        assert r.returncode != 0 and "母集団" in r.stderr, (name, r.stderr[-2000:])


@real_data
def test_cli_run_kind_and_fingerprint_follow_the_arm(w20_table, tmp_path, monkeypatch, keep_arm):
    """CLI の 1a はランの種類 arm(w17 は reproduction)・設定の指紋には 1a のときだけ ``calendar_shadow: "1a"``。"""
    from shibuya.engine import resume as RS

    monkeypatch.setenv("SHIBUYA_CALENDAR_W20", str(w20_table))
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)  # ランの種類を CLI の規則で決めさせる(試験の印を外す)
    argv = ["--agents", "200", "--seed", "1", "--world", str(WORLD), "--ticks", "60"]
    got = {}
    for arm in ("w17", "1a"):
        out = tmp_path / f"{arm}.json"
        assert cli.main([*argv, "--calendar-shadow", arm, "--checkpoints-out", str(out)]) == 0
        assert CS.arm() == arm
        got[arm] = json.loads(out.read_text(encoding="utf-8"))["manifest"]
    assert got["w17"]["run_kind"] == "reproduction" and got["1a"]["run_kind"] == "arm"
    assert got["w17"]["calendar_shadow"]["source"] == "w17" and got["1a"]["calendar_shadow"]["source"] == "1a"
    heads = {}
    for arm in ("w17", "1a"):
        CS.set_arm(arm)
        r = cli.run(n_agents=200, seed=1, world_dir=str(WORLD), state_out=tmp_path / f"st_{arm}", stop_at_tick=30)
        heads[arm] = RS.read_state(tmp_path / f"st_{arm}" / r.resume["state_files"][-1]["file"]).header["fingerprint"]
    assert "calendar_shadow" not in heads["w17"] and heads["1a"]["calendar_shadow"] == "1a"
    assert {k: v for k, v in heads["1a"].items() if k != "calendar_shadow"} == heads["w17"]
