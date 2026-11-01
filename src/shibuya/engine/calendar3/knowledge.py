"""engine.calendar3.knowledge — 暦の常識(祝日の問い合わせの口と常識の文)と店の決まりの口(第 6 期 6-2 カレンダー 3)。

正: 決定 10-12 §4-1 CA11「日付・曜日・祝日・大型連休は、全員が常識として知っています(厳密にしない)。学校の休みはその学校の人、
給料日は本人、店の休業日は常連/検索/行って分かる人が知ります」・§1-1 CP6 と §2 の 2(例外=社会の決まり=暦・祝日は外からの
決定=L0 環境)。祝日の表は暦の口 ``engine.calendar.SimCalendar``(内閣府「国民の祝日」CSV ``data/calendar/syukujitsu.csv``)を
読むだけ(写しを持たない)。

- :class:`CommonCalendar`(問い合わせの口): 体は誰でも ``ask(day)`` で「その日の日付・曜日・祝日の名」を引ける(全員が知る=体を
  問わない=CA11)。状態を持たない(引いた数は持ち主の計器)。本人の判断の候補の文(雇い主の「その日の枠」・働く人の「休みたい日」)はこの口から
  日の言葉を作る。
- :func:`common_line`: 常識の文の 1 行(「今日は 7 月 20 日(月・海の日)。」)。判断の入力の常識の文に足す 1 行の形
  (仮のモデルは文を読まない=manifest に例を出す)。
- :class:`StoreRules`(店の決まりの口=組織の口が知らせる): 店の休業日の知らせ。**本段は枠だけ**(中身は空=常連/検索/行って分かる
  人が知る形は C4 以降・店のエージェントの段=6-6 ②)。状態を持たない。

逐次ループ宣言: なし(``holidays_between`` は暦の口の 1 回)。
"""

from __future__ import annotations

from typing import Any, Final

__all__ = ["WEEKDAY_WORDS", "CommonCalendar", "common_line", "StoreRules"]

#: 曜日の語(暦の口の曜日 0=月 … 6=日)。
WEEKDAY_WORDS: Final[str] = "月火水木金土日"


class CommonCalendar:
    """暦の常識の問い合わせの口(全員が知る=CA11)。暦の口を読むだけ。"""

    def __init__(self, calendar: Any) -> None:
        self.calendar = calendar

    def ask(self, day: int) -> tuple[str, str, str]:
        """``day`` 日目の (日付 ISO・曜日の語・祝日の名=無ければ空)。引いた数は持ち主の計器が数える。"""
        c = self.calendar
        if c is None:
            return "", "", ""
        d = int(day)
        return c.date_of_day(d).isoformat(), WEEKDAY_WORDS[int(c.weekday(d))], str(c.holiday_name(d) or "")

    def words(self, day: int) -> str:
        """日の言葉(「7/20(月・海の日)」の形)。"""
        iso, wd, hol = self.ask(day)
        if not iso:
            return f"{int(day)} 日目"
        _y, m, dd = iso.split("-")
        return f"{int(m)}/{int(dd)}({wd}{'・' + hol if hol else ''})"


def common_line(cc: CommonCalendar, day: int) -> str:
    """常識の文の 1 行(判断の入力に足す形)。"""
    iso, wd, hol = cc.ask(day)
    if not iso:
        return ""
    _y, m, dd = iso.split("-")
    return f"今日は {int(m)} 月 {int(dd)} 日({wd}{'・' + hol if hol else ''})。"


class StoreRules:
    """店の決まりの口(組織の口が知らせる)。本段は**枠だけ**=休業日の知らせは空(つなぎ ``DOC-ca3-store-closed-days-frame``)。"""

    def closed_days(self, unit: int, days: Any) -> tuple[int, ...]:
        """単位 ``unit`` の ``days`` のうち店の決まりの休業日(本段は空)。呼んだ数は持ち主の計器が数える。"""
        return ()
