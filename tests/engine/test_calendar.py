"""10a(指示書 10-03 §3-1 A1・A1-1・A1-2・A1-3): 暦の口 ``engine.calendar`` の既知の答え。

見るもの
- 祝日 CSV(内閣府・cp932)の読み方: 名称「休日」の行(2026/5/6・2026/9/22)が祝日になる・md5・範囲・
  形が違うファイルは止める・無いときは祝日を空にして警告を 1 回だけ出す。
- 曜日: 2026-07-28 は火曜(real)。``day_index`` モードは ``(day_index + 日) % 7`` で祝日を見ない
  (=今のコードが引いていた値と同じ)。
- 開始日の検査: 月曜・祝日の月曜・日曜・範囲外・学校の休みの区間・複数日の連続する平日。
- 既定(``day_index``)の暦が、付け替えた箇所の旧い式(``day_index % 7 >= 5`` など)と同じ値を返す。

本物の CSV(gitignore 下)が無い環境でも回るよう、2026 年の行と範囲の端の行だけを持つ小さい CSV を
テストの中で cp932 で書いて読む。本物の CSV の検査は、ファイルがあるときだけ回す。
"""

from __future__ import annotations

import hashlib
import warnings
from datetime import date, datetime
from pathlib import Path

import pytest

from shibuya.engine import calendar as CAL
from shibuya.engine.calendar import CalendarWarning, SimCalendar, load_holidays, parse_school_holidays
from shibuya.engine.classical import day_kind_of

REAL_CSV = Path(CAL.DEFAULT_HOLIDAY_CSV)

#: 内閣府 CSV の 2026 年の 18 行(本物の CSV から写した)と範囲の端の 2 行。
ROWS_2026 = [
    ("1955/1/1", "元日"),
    ("2026/1/1", "元日"), ("2026/1/12", "成人の日"), ("2026/2/11", "建国記念の日"),
    ("2026/2/23", "天皇誕生日"), ("2026/3/20", "春分の日"), ("2026/4/29", "昭和の日"),
    ("2026/5/3", "憲法記念日"), ("2026/5/4", "みどりの日"), ("2026/5/5", "こどもの日"),
    ("2026/5/6", "休日"), ("2026/7/20", "海の日"), ("2026/8/11", "山の日"),
    ("2026/9/21", "敬老の日"), ("2026/9/22", "休日"), ("2026/9/23", "秋分の日"),
    ("2026/10/12", "スポーツの日"), ("2026/11/3", "文化の日"), ("2026/11/23", "勤労感謝の日"),
    ("2027/11/23", "勤労感謝の日"),
]


def write_csv(path: Path, rows=ROWS_2026, header=CAL.HOLIDAY_CSV_COLUMNS) -> Path:
    text = ",".join(header) + "\r\n" + "".join(f"{d},{n}\r\n" for d, n in rows)
    path.write_bytes(text.encode("cp932"))
    return path


@pytest.fixture
def table(tmp_path):
    return load_holidays(write_csv(tmp_path / "syukujitsu.csv"))


# ================================================================= 祝日の表
def test_holiday_rows_named_kyujitsu_are_holidays(table):
    assert table.loaded and table.md5
    assert table.days[date(2026, 5, 6)] == "休日"       # 振替休日
    assert table.days[date(2026, 9, 22)] == "休日"      # 国民の休日(敬老の日と秋分の日の間)
    assert date(2026, 5, 7) not in table.days
    assert table.first == date(1955, 1, 1) and table.last == date(2027, 11, 23)
    assert table.covers(date(2027, 11, 23)) and not table.covers(date(2027, 11, 24))
    assert sum(1 for d in table.days if d.year == 2026) == 18


def test_md5_is_of_the_file_bytes(tmp_path):
    p = write_csv(tmp_path / "h.csv")
    assert load_holidays(p).md5 == hashlib.md5(p.read_bytes()).hexdigest()


def test_bad_files_stop(tmp_path):
    with pytest.raises(ValueError):  # 見出しが違う
        load_holidays(write_csv(tmp_path / "a.csv", header=("date", "name")))
    with pytest.raises(ValueError):  # 昇順でない
        load_holidays(write_csv(tmp_path / "b.csv", rows=[("2026/5/6", "休日"), ("2026/5/5", "こどもの日")]))
    with pytest.raises(ValueError):  # 同じ日が 2 行
        load_holidays(write_csv(tmp_path / "c.csv", rows=[("2026/5/6", "休日"), ("2026/5/6", "休日")]))


def test_missing_csv_gives_an_empty_table_and_warns_once(tmp_path):
    p = tmp_path / "nothing.csv"
    with pytest.warns(CalendarWarning):
        t = load_holidays(p)
    assert not t.loaded and t.days == {} and t.md5 == ""
    with warnings.catch_warnings():
        warnings.simplefilter("error", CalendarWarning)
        load_holidays(p)  # 2 回目は警告しない


@pytest.mark.skipif(not REAL_CSV.is_file(), reason="本物の祝日 CSV(gitignore 下)が無い環境")
def test_the_real_cabinet_office_csv():
    t = load_holidays(REAL_CSV)
    assert t.md5 == "733fabb6b488794a0cd3d94df4b1f24a"
    assert len(t.days) == 1_067
    assert t.first == date(1955, 1, 1) and t.last == date(2027, 11, 23)
    assert t.days[date(2026, 5, 6)] == "休日" and t.days[date(2026, 9, 22)] == "休日"
    # W13 の構築の手書きの 2 行と一致する(材料 §2-5)
    assert t.days[date(2026, 7, 20)] == "海の日" and t.days[date(2026, 8, 11)] == "山の日"
    got = {d: n for d, n in t.days.items() if d.year == 2026}
    assert got == {_d(s): n for s, n in ROWS_2026 if s.startswith("2026/")}


def _d(s: str) -> date:
    y, m, d = (int(x) for x in s.split("/"))
    return date(y, m, d)


# ================================================================= 曜日・日付・季節
def test_real_weekday_and_holidays(table):
    c = SimCalendar(datetime(2026, 7, 28), weekday_mode="real", holidays=table)
    assert c.weekday(0) == 1                      # 2026-07-28 は火曜
    c = SimCalendar(datetime(2026, 5, 4), weekday_mode="real", holidays=table)
    assert [c.weekday(d) for d in range(4)] == [0, 1, 2, 3]
    assert [c.holiday_name(d) for d in range(4)] == ["みどりの日", "こどもの日", "休日", ""]
    assert [c.is_rest_day(d) for d in range(4)] == [True, True, True, False]
    assert [c.table_weekday(d) for d in range(4)] == [6, 6, 6, 3]   # 祝日は日曜の行
    assert [c.day_kind(d) for d in range(4)] == ["sunday", "sunday", "sunday", "weekday"]
    assert c.is_business_day(3) and not c.is_business_day(2)


def test_day_index_mode_ignores_holidays_and_keeps_the_old_values(table):
    """既定の暦は今の式と同じ値: 曜日 = (day_index + 日) % 7・土休 = 曜日 >= 5・祝日は効かない。"""
    for day_index in range(0, 15):
        c = SimCalendar(datetime(2026, 5, 4), weekday_mode="day_index", day_index=day_index, holidays=table)
        for d in range(0, 9):
            wd = (day_index + d) % 7
            assert c.weekday(d) == wd
            assert c.table_weekday(d) == wd                     # #7・#13〜#16・#19 の旧い値
            assert c.is_rest_day(d) == (wd >= 5)                # #2・#10・#12 の旧い式
            assert c.day_kind(d) == day_kind_of(day_index + d)  # #18 の旧い式
            assert c.day_key(d) == day_index + d                # #20・#21 の旧い鍵
    # 祝日の事実は返すが、土休には入らない(2026-05-04 は祝日の月曜)
    c = SimCalendar(datetime(2026, 5, 4), holidays=table)
    assert c.is_holiday(0) and not c.is_rest_day(0) and c.table_weekday(0) == 0


def test_legacy_calendar_equals_day_index_mode():
    for di in (0, 3, 5, 6, 9):
        c = SimCalendar.legacy(di)
        assert c.weekday_mode == "day_index" and c.weekday(0) == di % 7 and not c.holidays.loaded


def test_T_and_datetime():
    c = SimCalendar(datetime(2026, 7, 28), tick_seconds=60)
    assert c.ticks_per_day == 1_440
    assert c.to_T(1, 10) == 1_450 and c.day_of(1_450) == 1 and c.tick_of_day(1_450) == 10
    assert c.datetime_of(1_450) == datetime(2026, 7, 29, 0, 10)
    assert c.datetime_of(0) == datetime(2026, 7, 28)
    assert SimCalendar(datetime(2026, 7, 28), tick_seconds=30).ticks_per_day == 2_880
    with pytest.raises(ValueError):
        SimCalendar(datetime(2026, 7, 28), tick_seconds=7)


def test_season_follows_the_jma_months():
    c = SimCalendar(datetime(2026, 2, 27))
    assert [c.date_of_day(d) for d in (0, 2, 93, 94)] == [
        date(2026, 2, 27), date(2026, 3, 1), date(2026, 5, 31), date(2026, 6, 1)]
    assert [c.season(d) for d in (0, 2, 93, 94)] == ["冬", "春", "春", "夏"]
    assert SimCalendar(datetime(2026, 9, 1)).season(0) == "秋"
    assert SimCalendar(datetime(2026, 12, 1)).season(0) == "冬"


def test_payday_is_off_by_default_and_moves_to_the_previous_business_day(table):
    c = SimCalendar(datetime(2026, 7, 1), weekday_mode="real", holidays=table)
    assert not any(c.is_payday(d) for d in range(60))
    c = SimCalendar(datetime(2026, 7, 1), weekday_mode="real", holidays=table, payday_day_of_month=25)
    # 2026-07-25 は土曜 → 前の営業日 07-24(金)。2026-08-25 は火曜。
    got = [c.date_of_day(d) for d in range(62) if c.is_payday(d)]
    assert got == [date(2026, 7, 24), date(2026, 8, 25)]


# ================================================================= 開始日の検査
def _real(start, table, **kw):
    return SimCalendar(start, weekday_mode="real", holidays=table, **kw)


def test_start_check_known_dates(table):
    assert _real(datetime(2026, 7, 27), table).check_start(1) == []        # 祝日でない月曜
    assert _real(datetime(2026, 7, 27), table).check_start(5) == []        # 月〜金
    with pytest.raises(ValueError, match="祝日"):
        _real(datetime(2026, 7, 20), table).check_start(1)                 # 海の日(月曜)
    with pytest.raises(ValueError, match="月曜でない"):
        _real(datetime(2026, 7, 26), table).check_start(1)                 # 日曜
    with pytest.raises(ValueError, match="連続する平日"):
        _real(datetime(2026, 7, 27), table).check_start(6)                 # 土曜を含む
    with pytest.raises(ValueError, match="連続する平日"):
        _real(datetime(2026, 9, 14), table).check_start(2 + 7)             # 9/21・9/22 を含む
    with pytest.raises(ValueError, match="範囲外"):
        _real(datetime(2027, 11, 29), table).check_start(1)                # CSV の最後の日より後
    with pytest.raises(ValueError, match="範囲外"):
        _real(datetime(2027, 11, 23), table).check_start(2)                # 2 日目(11/24)が範囲外
    school = parse_school_holidays("2026-07-21:2026-08-31")
    with pytest.raises(ValueError, match="学校の長期休み"):
        _real(datetime(2026, 7, 27), table, school_holidays=school).check_start(1)
    assert _real(datetime(2026, 9, 7), table, school_holidays=school).check_start(1) == []


def test_day_index_mode_only_warns_but_still_stops_out_of_range(table):
    c = SimCalendar(datetime(2026, 7, 28), weekday_mode="day_index", day_index=5, holidays=table)
    with pytest.warns(CalendarWarning, match="月曜でない"):
        assert c.check_start(1)
    c = SimCalendar(datetime(2026, 7, 28), weekday_mode="day_index", day_index=0, holidays=table)
    with warnings.catch_warnings():
        warnings.simplefilter("error", CalendarWarning)
        assert c.check_start(1) == []      # 既定のランの開始日(day_index=0)は警告も出ない
        assert c.check_start(2) == []      # 2 日の mock(月・火)
    with pytest.raises(ValueError, match="範囲外"):
        SimCalendar(datetime(2028, 1, 3), holidays=table).check_start(1)


def test_real_mode_without_a_holiday_table_stops():
    c = SimCalendar(datetime(2026, 7, 27), weekday_mode="real")
    with pytest.raises(ValueError, match="祝日の表"):
        c.check_start(1)


def test_parse_school_holidays_forms():
    assert parse_school_holidays(None) == () and parse_school_holidays("") == ()
    assert parse_school_holidays("2026-12-25:2027-01-07,2026-07-21:2026-08-31") == (
        (date(2026, 7, 21), date(2026, 8, 31)), (date(2026, 12, 25), date(2027, 1, 7)))
    assert parse_school_holidays([("2026-03-25", date(2026, 4, 5))]) == ((date(2026, 3, 25), date(2026, 4, 5)),)
    with pytest.raises(ValueError):
        parse_school_holidays("2026-08-31:2026-07-21")


def test_parse_start_forms():
    assert CAL.parse_start(None) is None and CAL.parse_start("") is None
    assert CAL.parse_start("2026-08-03") == datetime(2026, 8, 3)
    assert CAL.parse_start(date(2026, 8, 3)) == datetime(2026, 8, 3)
    assert CAL.parse_start("2026-08-03T06:30:00") == datetime(2026, 8, 3, 6, 30)


def test_manifest_fields(table):
    c = SimCalendar(datetime(2026, 5, 4), weekday_mode="real", holidays=table,
                    school_holidays=parse_school_holidays("2026-07-21:2026-08-31"))
    m = c.manifest_fields(3)
    assert m["start_sim_datetime"] == "2026-05-04T00:00:00" and m["tick_seconds"] == 60
    assert m["calendar_weekday"] == "real" and m["holiday_csv_md5"] == table.md5
    assert m["holiday_csv_range"] == ["1955-01-01", "2027-11-23"]
    assert m["school_holidays"] == [["2026-07-21", "2026-08-31"]]
    assert [x["holiday"] for x in m["days"]] == ["みどりの日", "こどもの日", "休日"]
