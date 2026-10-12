"""10e E3(第330): 暦の一本化。

〔改訂(第330・RET)〕ACT で既定を切り替えた後、RET で切替口(``CALENDAR_UNIFIED``・``--calendar-weekday day_index``・
``--weather-scheme legacy``)を消した。前の試験(定数 1 つの切り替え・legacy の 2 日のランと比べる)は、ACT の commit で
通ったことを 10e の記録 §RET に書いて、今の規則だけを見る形に直した。

- 既定の開始日は ``DEFAULT_WORLD_START`` = 2026-07-13(月)(ユーザーの答え 1-4)。曜日・祝日は日付と内閣府 CSV から。
- W7 の祝日(``PH``)の行は暦の口(内閣府 CSV)で引く(``SimCalendar.opening_row``・``opening.rows_of_day``)。
- 2 日のランで日付が進み(07-13 → 07-14)、曜日の行(W7・W17・鉄道・古典)が暦から引かれる。
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from shibuya.engine import calendar as CAL
from shibuya.engine.calendar import SimCalendar, load_holidays
from shibuya.engine.processes import opening as OP

REPO = Path(__file__).resolve().parents[2]
WORLD_DIR = REPO / "data" / "world" / "v2"
HOLIDAYS = REPO / "data" / "calendar" / "syukujitsu.csv"
needs_world = pytest.mark.skipif(not (WORLD_DIR / "w7_plan_spec.parquet").is_file(), reason="世界資産が無い環境")
needs_csv = pytest.mark.skipif(not HOLIDAYS.is_file(), reason="祝日 CSV が無い環境")


# ================================================================ 切り替えは 1 か所
def test_e3_defaults_come_from_one_constant():
    # 〔改訂(第330・RET)〕切り替えの定数と切替口を消した(ACT では定数 1 つで既定がそろって切り替わることを見た)
    assert CAL.DEFAULT_WORLD_START == datetime(2026, 7, 13) and CAL.DEFAULT_WORLD_START.weekday() == 0
    assert (CAL.WEEKDAY_MODE, CAL.WEATHER_SCHEME) == ("real", "calendar")
    for gone in ("CALENDAR_UNIFIED", "WEEKDAY_MODES", "WEATHER_SCHEMES", "DEFAULT_WEEKDAY_MODE", "DEFAULT_WEATHER_SCHEME",
                 "check_weekday_mode", "check_weather_scheme"):
        assert not hasattr(CAL, gone), gone
    assert "weekday_mode" not in {f.name for f in __import__("dataclasses").fields(SimCalendar)}
    assert not hasattr(SimCalendar, "legacy")
    d = SimCalendar.default(3)
    assert d.date_of_day(0) == date(2026, 7, 16) and d.weekday(0) == 3 and d.day_key(0) == 0


def test_e3_run_day_and_cli_defaults_are_unchanged():
    # 〔改訂(第330・RET)〕run_day と CLI に暦の切替口(calendar_weekday・weather_scheme)は無い(前: 既定 None)
    import argparse
    import inspect

    from shibuya.engine.run import add_calendar_args, calendar_kwargs_from_args, run_day

    sig = inspect.signature(run_day)
    assert "weather_scheme" not in sig.parameters and "calendar_weekday" not in sig.parameters
    ap = argparse.ArgumentParser()
    add_calendar_args(ap)
    assert sig.parameters["weather_perturb"].default is False
    d = calendar_kwargs_from_args(ap.parse_args([]))
    assert "weather_scheme" not in d and "weather_perturb" not in d and "calendar_weekday" not in d
    assert calendar_kwargs_from_args(ap.parse_args(["--weather-perturb"]))["weather_perturb"] is True
    for flag in ("--weather-scheme", "--calendar-weekday"):
        with __import__("pytest").raises(SystemExit):
            ap.parse_args([flag, "real"])


# ================================================================ W7 の祝日の行
@needs_csv
def test_e3_opening_row_takes_holidays_from_the_cabinet_office_csv():
    table = load_holidays(HOLIDAYS)
    real = SimCalendar(datetime(2026, 7, 13), holidays=table)
    # 7/13(月)〜7/19(日)・7/20(海の日)・7/21(火)
    assert [real.opening_row(d) for d in range(9)] == [0, 1, 2, 3, 4, 5, 6, CAL.OPENING_ROW_PH, 1]
    assert real.table_weekday(7) == 6                     # 曜日 7 日の表(W17・古典)は今のまま日曜の行
    # 〔改訂(第330・RET)〕前は day_index の暦(祝日を見ない=opening_row は table_weekday と同じ)とも比べた(消した)


def test_e3_ph_row_uses_the_ph_spans_or_the_sunday_row():
    # 店 0: 月〜日 9:00-18:00・祝日は休み(PH=[]) / 店 1: 日曜 10:00-12:00・祝日の規則なし / 店 2: 祝日 13:00-14:00
    plan_poi = np.array([0] * 7 + [1, 2], dtype=np.int32)
    plan_day = np.array(list(range(7)) + [6, 7], dtype=np.int8)
    plan_start = np.array([540] * 7 + [600, 780], dtype=np.int32)
    plan_end = np.array([1080] * 7 + [720, 840], dtype=np.int32)
    ph_poi = np.array([0, 2])
    m = OP.build_open_matrix(3, plan_poi, plan_day, plan_start, plan_end, OP.PH_ROW, ph_poi)
    assert not m[0].any()                                   # PH の規則=休み
    assert m[1, 600:720].all() and m[1].sum() == 120        # 規則なし=日曜の行
    assert m[2, 780:840].all() and m[2].sum() == 60
    # 曜日 0〜6 は今と同じ(PH の区間は混ざらない)
    for wd in range(7):
        old = np.zeros((3, 1440), dtype=bool)
        for k in np.flatnonzero(plan_day == wd):
            old[plan_poi[k], plan_start[k]:plan_end[k]] = True
        assert np.array_equal(OP.build_open_matrix(3, plan_poi, plan_day, plan_start, plan_end, wd, ph_poi), old)
    # PH の店が無い資産(今の W7)=祝日は全部日曜の行(10a の「祝日は土休扱い」と同じ)
    assert np.array_equal(OP.build_open_matrix(3, plan_poi, plan_day, plan_start, plan_end, OP.PH_ROW, None),
                          OP.build_open_matrix(3, plan_poi, plan_day, plan_start, plan_end, 6, None))


def test_act_w7_reader_takes_the_holiday_content_column_as_ph(tmp_path):
    # 〔改訂(第330・ACT)〕親の決定 (1): W7 の PH は構築側の列 ``holiday_content``(W7 1.1.0)から読む
    # (旧: 週の 8 つ目の要素=実行役の提案の形・資産に無かった)。``[]``=祝日は休み・空文字=規則なし=日曜の行。
    from shibuya.world.assets import load_process_assets, synthetic_assets

    wa = synthetic_assets(n_cells=4, seed=1)
    ids = [f"p{j}" for j in range(wa.n_poi)]
    pq.write_table(pa.table({"poi_id": ids, "cat": list(wa.poi_cat)}), tmp_path / "w6_poi.parquet")
    week7 = [[[540, 1080]]] * 7
    contents = [json.dumps(week7)] * wa.n_poi
    contents[3] = json.dumps(week7 + [[[1, 2]]])      # 週表の 8 つ目の要素は読まない(PH は列から)
    hol = ["[]", "[[600, 660], [700, 720]]", "", ""] + [""] * (wa.n_poi - 4)
    pq.write_table(pa.table({"poi_id": ids, "kind": ["opening_hours"] * wa.n_poi, "content": contents,
                             "holiday_content": hol}), tmp_path / "w7_plan_spec.parquet")
    pa_ = load_process_assets(tmp_path, wa)
    assert pa_.plan_ph_poi.tolist() == [0, 1]
    ph = pa_.plan_day == 7
    assert pa_.plan_poi[ph].tolist() == [1, 1] and pa_.plan_start[ph].tolist() == [600, 700]
    assert int((pa_.plan_day < 7).sum()) == 7 * wa.n_poi and int(pa_.plan_day.max()) == 7
    # 列の無い W7(1.1.0 より前の資産)=PH の規則なし(祝日は全部日曜の行)
    pq.write_table(pa.table({"poi_id": ids, "kind": ["opening_hours"] * wa.n_poi, "content": contents}),
                   tmp_path / "w7_plan_spec.parquet")
    pb_ = load_process_assets(tmp_path, wa)
    assert pb_.plan_ph_poi is None and int(pb_.plan_day.max()) == 6


@needs_world
def test_act_holiday_opening_hours_come_from_holiday_content_or_the_sunday_row():
    # 〔第330・ACT〕世界資産の W7: 祝日に PH の規則を持つ店(40・うち休み 1)の営業時間は列 holiday_content の区間、
    # 持たない店は日曜の行(週表 content の 7 つ目)。期待値は parquet の列から直に作る
    from shibuya.world.assets import load_assets, load_process_assets

    wa = load_assets(WORLD_DIR)
    pa_ = load_process_assets(WORLD_DIR, wa)
    poi_ids = pq.read_table(WORLD_DIR / "w6_poi.parquet", columns=["poi_id"]).to_pydict()["poi_id"]
    idx = {str(x): i for i, x in enumerate(poi_ids)}
    t = pq.read_table(WORLD_DIR / "w7_plan_spec.parquet",
                      columns=["poi_id", "kind", "content", "holiday_content"]).to_pydict()
    n = len(poi_ids)
    want = np.zeros((n, 1440), dtype=bool)
    ph_rows = closed = 0
    for pid, kind, content, hol in zip(t["poi_id"], t["kind"], t["content"], t["holiday_content"]):
        j = idx.get(str(pid), -1)
        if kind != "opening_hours" or j < 0:
            continue
        spans = json.loads(hol) if hol else json.loads(content)[6]
        ph_rows += bool(hol)
        closed += hol == "[]"
        for s, e in spans:
            want[j, max(0, s):min(1440, e)] = True
            if e > 1440:
                want[j, 0:min(1440, e - 1440)] = True
    assert ph_rows == 40 and closed == 1 and len(pa_.plan_ph_poi) == 40
    got = OP.build_open_matrix(n, pa_.plan_poi, pa_.plan_day, pa_.plan_start, pa_.plan_end, OP.PH_ROW,
                               pa_.plan_ph_poi)
    assert np.array_equal(got, want)
    # PH の規則が日曜と違う店がある(列が効いている)・曜日 0〜6 は PH の行を混ぜない
    sun = OP.build_open_matrix(n, pa_.plan_poi, pa_.plan_day, pa_.plan_start, pa_.plan_end, 6, pa_.plan_ph_poi)
    assert int((got != sun).any(axis=1).sum()) >= 1
    assert np.array_equal(sun, OP.build_open_matrix(n, pa_.plan_poi, pa_.plan_day, pa_.plan_start,
                                                    pa_.plan_end, 6, None))


# ================================================================ 世界の日付と再生日・2 日のラン
def test_e3_two_days_advance_on_the_calendar_and_the_weekday_rows_come_from_it(monkeypatch):
    """〔改訂(第330・RET)〕前は legacy(day_index)の 2 日のランと曜日の行を比べた(legacy を消した)。今は暦の値だけを見る。"""
    from shibuya import cli
    from shibuya.engine.presence import PlanExecutor

    seen: dict[str, list] = {"opening": [], "presence": []}
    _o, _p = OP.OpeningProcess.relay_day, PlanExecutor.relay_day

    def spy_o(self, wd):
        seen["opening"].append(int(wd))
        return _o(self, wd)

    def spy_p(self, d, *a, **k):
        seen["presence"].append((int(d), int(k["weekday"])))
        return _p(self, d, *a, **k)

    monkeypatch.setattr(OP.OpeningProcess, "relay_day", spy_o)
    monkeypatch.setattr(PlanExecutor, "relay_day", spy_p)
    res = cli.run(n_agents=40, seed=1, world_dir=str(WORLD_DIR), sim_days=2, ticks=1440, checkpoint_every=1440)
    m = res.run_manifest_fields()
    r = res.runner
    assert m["start_sim_datetime"] == "2026-07-13T00:00:00"
    assert [d["date"] for d in m["calendar"]["days"]] == ["2026-07-13", "2026-07-14"]
    assert r.calendar.date_of_day(1) == date(2026, 7, 14)
    # 曜日の行(W7・W17・鉄道・古典)は暦から=月曜・火曜
    assert [d["weekday"] for d in m["calendar"]["days"]] == [0, 1]
    assert [r.calendar.opening_row(0)] + seen["opening"] == [0, 1]
    assert seen["presence"] == [(1, 0)]  # 計画実行層の W17 は K9 のつなぎ=月曜の行(10d README・前の legacy と同じ値)
    assert [r.rail.calendar.is_rest_day(d) for d in (0, 1)] == [False, False]
    assert [r.calendar.day_kind(d) for d in (0, 1)] == ["weekday", "weekday"]


