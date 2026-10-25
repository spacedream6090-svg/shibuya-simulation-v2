"""engine.calendar — 暦の口(指示書 10-03 §3-1 A1・A1-1・A1-2・A1-3)。

ランの中で「今日は何日か・何曜日か・祝日か・季節は何か・給料日か・営業日か」を引く箇所は、
すべてこの 1 つの口(``SimCalendar``)を通す。入力は ``start_sim_datetime``(T=0 の世界内日時)と
通しの時刻 T(``T = 日 × 1 日の tick 数 + 日の中の tick``)だけ。

曜日: ``start_sim_datetime`` の実の曜日と内閣府の祝日表から引く(``real``)。祝日は「土休」として扱い、
曜日 7 日の表(古典の事前分布・W17 の曜日の行)では**日曜**の行を使う(親案「祝日は土休扱い」に沿った
expedient・未リサーチ)。W7 の営業時間は PH の行(構築側の列 ``holiday_content``・規則の無い店は日曜の行)。
〔第330・RET〕10e より前の曜日の決め方 ``day_index``(曜日 = ``(day_index + 日) % 7``・祝日を見ない)と切替口
``--calendar-weekday``・``--weather-scheme legacy``・定数 ``CALENDAR_UNIFIED`` は版上げ 1 回目の後に消した
(旧値の再現は第330 ACT の commit で記録)。

祝日の表(A1-2): 内閣府「国民の祝日」CSV(``data/calendar/syukujitsu.csv``・cp932・列
``国民の祝日・休日月日``・``国民の祝日・休日名称``・1955/1/1〜2027/11/23)。振替休日と国民の休日は
名称「休日」の行として入っている。ファイルが無いときは祝日を空にして警告を 1 回だけ出す
(既定のランを壊さない)。読んだファイルの md5 を manifest に記録する。

季節: 気象庁の季節の区分(春=3〜5 月・夏=6〜8 月・秋=9〜11 月・冬=12〜2 月)を日付の月から引く。

開始日を渡さないランの暦の開始日は ``DEFAULT_WORLD_START``=2026-07-13(月)+ ``day_index`` 日(ユーザーの答え 1-4)。
W7 の祝日(``PH``)の行は ``opening_row`` で引く(祝日=``OPENING_ROW_PH``。資産に PH の行が無い店は日曜の行)。

給料日: 規則は賃金の段(指示書 §6 ⑧)で決める。既定 ``payday_day_of_month=None`` は給料日なし
(``is_payday`` は常に False)。日を渡したときは「毎月その日。土休なら前の営業日へ寄せる」
(expedient・未リサーチ。今は誰も読まない)。

営業日: ``is_business_day`` = 土休でない日(``real`` では祝日を含む土休を除く)。年末年始などの
慣行の休みは入れていない(未リサーチ・宣言)。

開始日の検査(A1-1・A1-3): ``check_start`` が「祝日でない平日の月曜」「複数日なら連続する平日」
「学校の長期休みの区間に当たらない」「祝日表の範囲の中」を見る。違反で止める(``ValueError``)。学校の長期休みの区間の表は
manifest の欄(``school_holidays``)で渡す形だけを作り、中身は空(K7 の判断待ち)。

逐次ループ宣言(P4): ``load_holidays`` が CSV の行数ぶん(約 1,070 行・起動時 1 回)。ほかはなし。
"""

from __future__ import annotations

import csv
import hashlib
import io
import warnings
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Final, Iterable, Mapping

from shibuya.core.types import DEFAULT_TICK_SECONDS, MINUTES_PER_SIM_DAY
from shibuya.core.time_consts import SECONDS_PER_MINUTE

__all__ = [
    "CalendarWarning",
    "DEFAULT_HOLIDAY_CSV",
    "DEFAULT_WORLD_START",
    "OPENING_ROW_PH",
    "WEATHER_SCHEME",
    "WEEKDAY_MODE",
    "HOLIDAY_CSV_COLUMNS",
    "HolidayTable",
    "SEASON_OF_MONTH",
    "SimCalendar",
    "holidays_between",
    "load_holidays",
    "parse_school_holidays",
    "parse_start",
    "resolve_repo_path",
    "ticks_per_day",
]

#: 祝日 CSV の既定の場所(リポのルートからの相対・gitignore 下)。manifest の欄 ``holiday_csv``。
DEFAULT_HOLIDAY_CSV: Final[str] = "data/calendar/syukujitsu.csv"
#: 内閣府 CSV の列名(見出しの行)。
HOLIDAY_CSV_COLUMNS: Final[tuple[str, str]] = ("国民の祝日・休日月日", "国民の祝日・休日名称")
#: 〔第330・10e E3〕既定の開始日(ユーザーの答え 1-4: 2026-07-13(月)・世界の資産の時点に最も近く季節が同じで学期中)。
#: 開始日を渡さないランの暦の 0 日目(``+ day_index`` 日)。
DEFAULT_WORLD_START: Final[datetime] = datetime(2026, 7, 13, 0, 0)
#: 曜日の決め方の名前(manifest の ``calendar.calendar_weekday``・テープの脇の meta の値)。〔第330・RET〕``real`` だけ。
WEEKDAY_MODE: Final[str] = "real"
#: 天気の規則の名前(manifest の ``weather.scheme``・テープの脇の meta の値)。天気は再生日・太陽と影は暦の日付
#: (ユーザーの答え 1-3)。〔第330・RET〕``calendar`` だけ(10e より前の ``legacy`` は消した)。
WEATHER_SCHEME: Final[str] = "calendar"
#: 〔第330・10e E3〕W7 の営業時間の祝日の行(``PH``)の番号(曜日 0〜6 の次)。``opening_row`` が祝日に返す。
OPENING_ROW_PH: Final[int] = 7
#: 気象庁の季節の区分(月 → 季節)。
SEASON_OF_MONTH: Final[Mapping[int, str]] = {
    3: "春", 4: "春", 5: "春",
    6: "夏", 7: "夏", 8: "夏",
    9: "秋", 10: "秋", 11: "秋",
    12: "冬", 1: "冬", 2: "冬",
}
#: 古典の事前分布の曜日の鍵(``engine.classical.day_kind_of`` と同じ語)。
_DAY_KIND_OF_WEEKDAY: Final[tuple[str, ...]] = (
    "weekday", "weekday", "weekday", "weekday", "weekday", "saturday", "sunday",
)
#: 祝日を曜日 7 日の表で引くときの行(日曜)。
HOLIDAY_TABLE_WEEKDAY: Final[int] = 6


class CalendarWarning(UserWarning):
    """暦の口の警告(祝日 CSV が無い)。"""


def ticks_per_day(tick_seconds: int = DEFAULT_TICK_SECONDS) -> int:
    """1 日の tick 数(``tick_seconds`` が 1 日を割り切らなければ ``ValueError``)。"""
    ts = int(tick_seconds)
    if ts <= 0:
        raise ValueError("tick_seconds は正の整数")
    seconds = MINUTES_PER_SIM_DAY * SECONDS_PER_MINUTE
    if seconds % ts:
        raise ValueError(f"tick_seconds={ts} は 1 日を割り切らない")
    return seconds // ts


# ------------------------------------------------------------------ 祝日の表
@dataclass(frozen=True)
class HolidayTable:
    """祝日の表(日付 → 名称)と出どころ。

    Attributes:
        days: 日付 → 名称(名称「休日」=振替休日・国民の休日)。
        path: 読んだ場所(渡されたままの文字列=相対パス。manifest に載せる)。
        md5: 読んだファイルの md5(無ければ空文字)。
        first / last: 収録の最初と最後の日(無ければ None)。
        loaded: ファイルを読めたか。
    """

    days: Mapping[date, str] = field(default_factory=dict)
    path: str = ""
    md5: str = ""
    first: date | None = None
    last: date | None = None
    loaded: bool = False

    def covers(self, d: date) -> bool:
        """``d`` が収録の範囲の中か(読めていなければ False)。"""
        return self.loaded and self.first is not None and self.last is not None and self.first <= d <= self.last


#: 「CSV が無い」の警告を出した場所(1 回だけ出すため)。
_WARNED_MISSING: set[str] = set()


def _parse_ymd(text: str) -> date:
    y, m, d = (int(x) for x in str(text).strip().split("/"))
    return date(y, m, d)


#: リポの根(``src/shibuya/engine/calendar.py`` から 3 つ上)。相対パスの祝日 CSV はここから解決する。
REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[3]


def resolve_repo_path(path: str | Path) -> Path:
    """相対パスはリポの根から、絶対パスはそのまま(検収後 P4: 作業ディレクトリに依らない)。"""
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def load_holidays(path: str | Path = DEFAULT_HOLIDAY_CSV) -> HolidayTable:
    """内閣府の祝日 CSV を読む(cp932)。無ければ空の表を返し、警告を 1 回だけ出す。

    相対パスはリポの根から解決する(作業ディレクトリに依らない・検収後 P4)。manifest には渡された文字列を書く。
    見出しの列名が ``HOLIDAY_CSV_COLUMNS`` でない・日付が昇順でない・同じ日が 2 行ある、は
    ファイルの形が想定と違うので ``ValueError`` で止める(黙って読み違えない)。
    """
    p = resolve_repo_path(path)
    shown = str(path)
    if not p.is_file():
        if shown not in _WARNED_MISSING:
            _WARNED_MISSING.add(shown)
            warnings.warn(
                f"祝日 CSV が無い({shown})。祝日を空として回す(既定のランは祝日を見ない)",
                CalendarWarning,
                stacklevel=2,
            )
        return HolidayTable(path=shown)
    raw = p.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    text = raw.decode("cp932")
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if header is None or tuple(h.strip() for h in header[:2]) != HOLIDAY_CSV_COLUMNS:
        raise ValueError(f"祝日 CSV の見出しが想定と違う({shown}: {header!r})")
    days: dict[date, str] = {}
    prev: date | None = None
    for row in reader:  # 逐次ループ宣言: CSV の行数ぶん(起動時 1 回)
        if not row or not str(row[0]).strip():
            continue
        d = _parse_ymd(row[0])
        if prev is not None and d <= prev:
            raise ValueError(f"祝日 CSV の日付が昇順でない・重複がある({shown}: {d})")
        days[d] = str(row[1]).strip() if len(row) > 1 else ""
        prev = d
    if not days:
        raise ValueError(f"祝日 CSV に行が無い({shown})")
    keys = list(days)
    return HolidayTable(days=days, path=shown, md5=md5, first=keys[0], last=keys[-1], loaded=True)


def parse_start(value: Any) -> datetime | None:
    """開始日の欄(``--start-date``)→ ``datetime``。``None``/空は ``None``(既定の導き方)。

    受け取る形: ``datetime``(そのまま)・``date``(0:00)・``"YYYY-MM-DD"``・ISO の日時の文字列。
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    text = str(value).strip()
    if len(text) == 10:
        d = date.fromisoformat(text)
        return datetime(d.year, d.month, d.day)
    return datetime.fromisoformat(text)


def parse_school_holidays(spec: Any) -> tuple[tuple[date, date], ...]:
    """学校の長期休みの区間の一覧(manifest の欄 ``school_holidays``)を ``(始, 終)`` の組に直す。

    受け取る形: ``None``/空 → 空。``"YYYY-MM-DD:YYYY-MM-DD,..."`` の文字列、または
    ``[(始, 終), ...]``(各要素は ``date`` か ISO の文字列)。区間は両端を含む。始 > 終は ``ValueError``。
    """
    if spec is None or spec == "" or spec == ():
        return ()
    items: Iterable[Any]
    if isinstance(spec, str):
        items = [tuple(part.split(":", 1)) for part in spec.split(",") if part.strip()]
    else:
        items = spec
    out: list[tuple[date, date]] = []
    for it in items:
        if len(it) != 2:
            raise ValueError(f"school_holidays の区間は (始, 終) の 2 つ組(いま {it!r})")
        lo, hi = (x if isinstance(x, date) else date.fromisoformat(str(x).strip()) for x in it)
        if lo > hi:
            raise ValueError(f"school_holidays の区間の始が終より後({lo} > {hi})")
        out.append((lo, hi))
    return tuple(sorted(out))


# ------------------------------------------------------------------ 暦
@dataclass(frozen=True)
class SimCalendar:
    """ランの暦(``start_sim_datetime`` と T から日付・曜日・祝日・季節・給料日・営業日を返す)。

    Attributes:
        start_sim_datetime: T=0 の世界内日時。
        tick_seconds: 1 tick の秒数。
        day_index: 開始日を ``DEFAULT_WORLD_START`` から何日ずらしたか(manifest の記録だけ・曜日は日付から)。
        holidays: 祝日の表。
        school_holidays: 学校の長期休みの区間(両端を含む・今は空)。
        payday_day_of_month: 給料日の日(None=給料日なし・既定)。
    """

    start_sim_datetime: datetime
    tick_seconds: int = DEFAULT_TICK_SECONDS
    day_index: int = 0
    holidays: HolidayTable = field(default_factory=HolidayTable)
    school_holidays: tuple[tuple[date, date], ...] = ()
    payday_day_of_month: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.start_sim_datetime, datetime):
            raise TypeError("start_sim_datetime は datetime")
        ticks_per_day(self.tick_seconds)  # 割り切れない tick 長はここで止める
        # 検収後 P2: T=0 は日の頭(0:00)。日の中の tick(``T % 1 日の tick 数``)と時計の時刻を一致させるため、
        # 0:00 でない開始時刻は止める(tz の有無は問わない)。
        st = self.start_sim_datetime
        if (st.hour, st.minute, st.second, st.microsecond) != (0, 0, 0, 0):
            raise ValueError(f"start_sim_datetime は 0:00 ちょうど(いま {st.isoformat()})")
        if self.payday_day_of_month is not None and not (1 <= int(self.payday_day_of_month) <= 31):
            raise ValueError("payday_day_of_month は 1〜31 か None")

    @classmethod
    def default(cls, day_index: int = 0, *, tick_seconds: int = DEFAULT_TICK_SECONDS) -> "SimCalendar":
        """暦を渡されない呼び手(過程の単体の組み立て)のための暦: ``DEFAULT_WORLD_START + day_index`` 日・祝日の表なし。

        〔第330・RET〕旧い口 ``legacy``(``day_index`` の曜日・開始日 2026-07-28)の置き換え。曜日は日付から
        (2026-07-13 は月曜=``day_index % 7`` と同じ)・日の鍵は日番号。
        """
        return cls(DEFAULT_WORLD_START + timedelta(days=int(day_index)), tick_seconds=tick_seconds,
                   day_index=int(day_index))

    def with_start(self, start_sim_datetime: datetime) -> "SimCalendar":
        """開始の日時だけを差し替えた暦(祝日の表はそのまま)。"""
        return replace(self, start_sim_datetime=start_sim_datetime)

    # ---- T ----
    @property
    def ticks_per_day(self) -> int:
        """1 日の tick 数(``tick_seconds=60`` なら 1,440)。"""
        return ticks_per_day(self.tick_seconds)

    def day_of(self, T: int) -> int:
        """通しの時刻 T → 日番号(0 日目から)。"""
        return int(T) // self.ticks_per_day

    def tick_of_day(self, T: int) -> int:
        """通しの時刻 T → 日の中の tick(0〜1 日の tick 数−1)。"""
        return int(T) % self.ticks_per_day

    def to_T(self, day: int, tick_of_day: int) -> int:
        """(日, 日の中の tick)→ 通しの時刻 T。"""
        return int(day) * self.ticks_per_day + int(tick_of_day)

    def datetime_of(self, T: int) -> datetime:
        """通しの時刻 T → 世界内日時(``start_sim_datetime + T × tick_seconds``)。"""
        return self.start_sim_datetime + timedelta(seconds=int(T) * int(self.tick_seconds))

    # ---- 日 ----
    def date_of_day(self, day: int) -> date:
        """日番号 → 日付(開始日 + 日数)。"""
        return self.start_sim_datetime.date() + timedelta(days=int(day))

    def weekday(self, day: int) -> int:
        """日番号 → 曜日(0=月曜・日付から)。"""
        return self.date_of_day(day).weekday()

    def is_holiday(self, day: int) -> bool:
        """その日付が祝日の表にあるか(日付の事実)。"""
        return self.date_of_day(day) in self.holidays.days

    def holiday_name(self, day: int) -> str:
        """祝日の名称(祝日でなければ空文字)。"""
        return str(self.holidays.days.get(self.date_of_day(day), ""))

    def set_holiday(self, d: date, *, on: bool, name: str = "") -> bool:
        """〔第 3 期 3-3〕祝日の表を書く唯一の口(申込書の L0 祝日の決定=``engine.experiment.apply`` だけが呼ぶ)。

        表はランごとに読み直した辞書(``load_holidays``)=そのランの中だけ。``on`` で ``d`` を祝日に(名は ``name``)・外す。
        表が書けない形(辞書でない)なら何もせず ``False``。
        """
        days = self.holidays.days
        if not isinstance(days, dict):
            return False
        if on:
            days[d] = str(name)
        else:
            days.pop(d, None)
        return True

    def is_rest_day(self, day: int) -> bool:
        """土休か(土日と祝日)。"""
        return self.weekday(day) >= 5 or self.is_holiday(day)

    def table_weekday(self, day: int) -> int:
        """曜日 7 日の表を引くときの曜日(祝日は日曜の行)。"""
        if self.is_holiday(day):
            return HOLIDAY_TABLE_WEEKDAY
        return self.weekday(day)

    def opening_row(self, day: int) -> int:
        """W7 の営業時間の表の行(〔第330・10e E3〕)。祝日は ``OPENING_ROW_PH``(祝日の行・無い店は日曜の行)、
        ほかは ``table_weekday`` と同じ。"""
        if self.is_holiday(day):
            return OPENING_ROW_PH
        return self.table_weekday(day)

    def day_kind(self, day: int) -> str:
        """古典の事前分布の曜日の鍵(``weekday``/``saturday``/``sunday``)。"""
        return _DAY_KIND_OF_WEEKDAY[self.table_weekday(day)]

    def season(self, day: int) -> str:
        """季節(気象庁の区分・日付の月から)。"""
        return SEASON_OF_MONTH[self.date_of_day(day).month]

    def is_business_day(self, day: int) -> bool:
        """営業日(土休でない日)。"""
        return not self.is_rest_day(day)

    def is_payday(self, day: int) -> bool:
        """給料日か(規則が無ければ常に False)。"""
        dom = self.payday_day_of_month
        if dom is None:
            return False
        d = self.date_of_day(day)
        # 検収後 P5: 前の営業日への寄せは月をまたぐ(例: 1 日が土曜なら前月の末日)ので、
        # 当月の給料日の寄せ先と翌月の給料日の寄せ先のどちらかなら給料日とする。
        nxt_month = (d.year + (d.month == 12), d.month % 12 + 1)
        return int(day) in (self._payday_target(d.year, d.month), self._payday_target(*nxt_month))

    def _payday_target(self, year: int, month: int) -> int:
        """その月の給料日(月末を越える日は月末)を、土休なら前の営業日へ寄せた日番号。"""
        nxt = date(year + (month == 12), month % 12 + 1, 1)
        last = (nxt - timedelta(days=1)).day
        target_day = int(self.day_index_of(date(year, month, min(int(self.payday_day_of_month), last))))
        # 逐次ループ宣言: 遡る日数ぶん(≤ 数日)
        while not self.is_business_day(target_day):
            target_day -= 1
        return target_day

    def day_index_of(self, d: date) -> int:
        """日付 → 日番号(開始日より前は負)。"""
        return (d - self.start_sim_datetime.date()).days

    def day_key(self, day: int) -> int:
        """日ごとの乱数・締めの鍵の日番号(日番号そのもの=10a の real。〔第330・RET〕``day_index + 日`` の旧い鍵は消した)。"""
        return int(day)

    def in_school_holiday(self, day: int) -> bool:
        """学校の長期休みの区間に当たるか。"""
        d = self.date_of_day(day)
        return any(lo <= d <= hi for lo, hi in self.school_holidays)

    # ---- 開始日の検査(A1-1・A1-3) ----
    def start_problems(self, sim_days: int = 1) -> tuple[list[str], list[str]]:
        """開始日の検査。``(止める違反, 規則の違反)`` を返す。

        止める違反: 祝日の表の範囲外の日を含む(表が読めていて範囲の外)・祝日の表が読めていない。
        規則の違反(止める): 0 日目が月曜でない・0 日目が祝日・
        どれかの日が土休(連続する平日に収まらない)・どれかの日が学校の長期休みの区間。
        """
        n = int(sim_days)
        if n < 1:
            raise ValueError("sim_days は 1 以上")
        fatal: list[str] = []
        rule: list[str] = []
        if self.holidays.loaded:
            out = [self.date_of_day(d) for d in range(n) if not self.holidays.covers(self.date_of_day(d))]
            if out:
                fatal.append(
                    f"祝日の表の範囲外の日を含む({out[0]}・表は {self.holidays.first}〜{self.holidays.last})"
                )
        else:
            fatal.append("祝日の表が読めていない(祝日を確かめられない)")
        if self.weekday(0) != 0:
            rule.append(f"0 日目が月曜でない(曜日 {self.weekday(0)}・{self.date_of_day(0)})")
        if self.is_holiday(0):
            rule.append(f"0 日目が祝日({self.date_of_day(0)} {self.holiday_name(0)})")
        rest = [d for d in range(n) if self.is_rest_day(d) or self.is_holiday(d)]
        if n > 1 and rest:
            rule.append(f"複数日が連続する平日に収まらない({rest[0]} 日目={self.date_of_day(rest[0])})")
        school = [d for d in range(n) if self.in_school_holiday(d)]
        if school:
            rule.append(f"学校の長期休みの区間に当たる({school[0]} 日目={self.date_of_day(school[0])})")
        return fatal, rule

    def check_start(self, sim_days: int = 1) -> list[str]:
        """開始日の検査を走らせる。違反があれば ``ValueError``(〔第330・RET〕``day_index`` の「警告だけ」は消した)。

        Returns:
            空の一覧(manifest の ``start_check`` の欄=違反が無かった)。
        """
        fatal, rule = self.start_problems(sim_days)
        if fatal:
            raise ValueError("開始日の検査で止めた: " + " / ".join(fatal))
        if rule:
            raise ValueError("開始日の検査で止めた(real): " + " / ".join(rule))
        return []

    # ---- manifest ----
    def manifest_fields(self, sim_days: int = 1) -> dict[str, Any]:
        """manifest の欄(開始日・曜日の決め方・祝日の表の出どころ・学校の休み・0 日目の暦)。"""
        return {
            "start_sim_datetime": self.start_sim_datetime.isoformat(),
            "tick_seconds": int(self.tick_seconds),
            "ticks_per_day": int(self.ticks_per_day),
            "sim_days": int(sim_days),
            "calendar_weekday": WEEKDAY_MODE,
            "day_index": int(self.day_index),
            "holiday_csv": str(self.holidays.path),
            # 検収後 P4: 読めなかったときは明示的に null(空文字・空の列と取り違えない)
            "holiday_csv_md5": str(self.holidays.md5) if self.holidays.loaded else None,
            "holiday_csv_range": (
                [self.holidays.first.isoformat(), self.holidays.last.isoformat()]
                if (self.holidays.loaded and self.holidays.first is not None and self.holidays.last is not None)
                else None
            ),
            "school_holidays": [[lo.isoformat(), hi.isoformat()] for lo, hi in self.school_holidays],
            "payday_day_of_month": self.payday_day_of_month,
            "days": [
                {
                    "day": d,
                    "date": self.date_of_day(d).isoformat(),
                    "weekday": self.weekday(d),
                    "holiday": self.holiday_name(d),
                    "rest_day": self.is_rest_day(d),
                    "season": self.season(d),
                }
                for d in range(int(sim_days))
            ],
        }


def holidays_between(table: HolidayTable, lo: date, hi: date) -> dict[str, str]:
    """``lo``〜``hi``(両端を含む)の祝日(ISO の日付 → 名称)。"""
    return {d.isoformat(): n for d, n in table.days.items() if lo <= d <= hi}
