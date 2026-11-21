"""engine.calendar_shadow — 暦 1a の影(第 3 期 3-1・決定 10-12 §4-1 CA2 (a)・CA8)。

腕(切替口): ``--calendar-shadow {w17,1a}``(環境変数 ``SHIBUYA_CALENDAR_SHADOW``・:func:`set_arm`)。既定 ``w17``=影を
作らない(計画実行層の勤務と授業の出入りは W17 の週次表のまま=**今と同じ・19 構成で不変**)。``1a``=計画実行層の
「勤務と授業の影」の源を W17 から W20(構築側の段 W20cal の週の表 ``w20_calendar_1a.parquet``)に替える。

影の段(CA2 (a))
    影は**計器だけ**: 出入り・退出・就寝は今の計画実行層が W17 で動かす(``engine.presence``)。影は日の頭に、その日の
    暦の日付・曜日・週から W20 の行(体 × 曜日)を引き、出勤・始業・終業・帰宅の時刻・通勤時間・15 分ごとの約束の
    行動者率・空欄の数を数えて manifest の ``calendar_shadow`` に出す(CA8 の計器=診断・合否にしない)。W17 の勤務の行との
    差は参考(CA2 の答え=影の段は現実のデータと比べる=検証側=S1 の後)。食事・買い物・就寝(W17 のつなぎ)は今のまま。
    状態台帳の行 ``CAL``(軸 1 diag・軸 2 derivable・中身は hash_skip=どちらのハッシュにも状態のファイルにも入らない=
    腕 1a のランの final も既定と同じ)。日の記録は W20 と暦と日番号だけから決まる=再開のランも同じ記録を作り直す
    (再開=通し)。

腕の扱い: 組み立てのときに読む(``run_day`` の引数にしない)。1a のランだけ設定の指紋に ``calendar_shadow`` を足す
(既定の指紋は今のまま=発話の口の腕と同じ形)。W20 の表は ``<world_dir>/w20_calendar_1a.parquet``(環境変数
``SHIBUYA_CALENDAR_W20`` で道筋を替えられる=試験と作業用)。表に無い体(合成の体)は空欄に数える。

層契約: engine の中・``world``/``agents`` は読むだけ・``build`` は import しない(週の表は parquet を読む)。
逐次ループ宣言(P4): 日の頭に 1 回(曜日の行を引く=体の配列のベクトル演算・15 分の枠の数 96 の累積)。体の数に比例する
Python のループは無い。
"""

from __future__ import annotations

import os
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping
import numpy as np
from shibuya.world.facts.weekly_reader import ACTIVITY_WORDS
from shibuya.foundation.time_consts import MINUTES_PER_DAY
from shibuya.world.facts.w20_calendar_reader import (
    COMMIT_SCHOOL,
    COMMIT_WORK,
    CalendarTable,
    N_DAYS,
    WEEK0_MONDAY,
    _freeze,
    _thaw,
    load_table,
    resolve_path,
)

__all__ = [
    "MODE_W17", "MODE_1A", "MODES", "DEFAULT_MODE", "SCHEMA", "arm", "set_arm", "is_on", "CalendarShadow",
    "manifest_fields", "MANIFEST_CONFIG", "MANIFEST_OBSERVED",
]


MODE_W17: Final[str] = "w17"
MODE_1A: Final[str] = "1a"
MODES: Final[tuple[str, ...]] = (MODE_W17, MODE_1A)
#: 既定(影を作らない=今と同じ)。
DEFAULT_MODE: Final[str] = MODE_W17
#: manifest の ``calendar_shadow`` の形の版。
SCHEMA: Final[str] = "shibuya.calendar_shadow/1"
#: 15 分の枠(1 日 96)。
SLOT_MIN: Final[int] = 15
N_SLOTS: Final[int] = MINUTES_PER_DAY // SLOT_MIN
#: W17 の「勤務」の活動語コード(``agents.weekly.ACTIVITY_WORDS`` の索引)。
W17_WORK_CODE: Final[int] = ACTIVITY_WORDS.index("勤務")
#: manifest の子の鍵(設定/観測=``engine.manifest_sections`` の表と同じ・試験が突き合わせる)。
MANIFEST_CONFIG: Final[tuple[str, ...]] = ("schema", "source", "w20", "weeks")
MANIFEST_OBSERVED: Final[tuple[str, ...]] = ("days", "shadows", "blanks")

_ARM: str = os.environ.get("SHIBUYA_CALENDAR_SHADOW", DEFAULT_MODE).strip().lower() or DEFAULT_MODE
if _ARM not in MODES:
    raise ValueError(f"SHIBUYA_CALENDAR_SHADOW は {MODES} のどれか(いま {_ARM!r})")


def arm() -> str:
    """いまの腕(``w17``=既定・``1a``=影を W20 から作る)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--calendar-shadow``・試験の切替口)。組み立ての時に読む。"""
    global _ARM
    if str(name) not in MODES:
        raise ValueError(f"--calendar-shadow は {MODES} のどれか(いま {name!r})")
    _ARM = str(name)


def is_on(mode: str | None = None) -> bool:
    return str(_ARM if mode is None else mode) == MODE_1A


def _hist15(m: np.ndarray) -> list[int]:
    x = np.asarray(m, dtype=np.int64)
    x = x[x >= 0]
    return np.bincount((x % MINUTES_PER_DAY) // SLOT_MIN, minlength=N_SLOTS)[:N_SLOTS].astype(int).tolist()


def _stats(x: np.ndarray) -> dict[str, Any]:
    v = np.asarray(x, dtype=np.float64)
    if v.size == 0:
        return {"n": 0, "mean": None, "p10": None, "p50": None, "p90": None}
    q = np.quantile(v, [0.1, 0.5, 0.9])
    return {"n": int(v.size), "mean": round(float(v.mean()), 3), "p10": round(float(q[0]), 1),
            "p50": round(float(q[1]), 1), "p90": round(float(q[2]), 1)}


def _active15(start: np.ndarray, end: np.ndarray, n_den: int) -> list[float]:
    """約束の区間 [start, end)(その日の中=翌日の分は畳まない)が 15 分の枠の頭を含む体の割合(分母=影の体の数)。

    逐次ループ宣言: 枠の数ぶん(96)の累積(体はベクトル)。
    """
    if n_den <= 0:
        return [0.0] * N_SLOTS
    s = np.clip(np.asarray(start, dtype=np.int64), 0, MINUTES_PER_DAY)
    e = np.clip(np.asarray(end, dtype=np.int64), 0, MINUTES_PER_DAY)
    first = -(-s // SLOT_MIN)  # 頭が start 以上の最初の枠
    last = -(-e // SLOT_MIN)   # 頭が end 以上の最初の枠(含まない)
    diff = np.zeros(N_SLOTS + 1, dtype=np.int64)
    ok = last > first
    np.add.at(diff, np.minimum(first[ok], N_SLOTS), 1)
    np.add.at(diff, np.minimum(last[ok], N_SLOTS), -1)
    cnt = np.cumsum(diff)[:N_SLOTS]
    return [round(float(c) / n_den, 5) for c in cnt]


def _w17_work_span(weekly: Any, day: int, n: int) -> tuple[np.ndarray, np.ndarray]:
    """W17 の曜日 ``day`` の勤務の行の最初の始まりと最後の終わり(体行・無ければ −1)。``weekly`` の公開の列だけを読む。"""
    s_out = np.full(n, -1, dtype=np.int64)
    e_out = np.full(n, -1, dtype=np.int64)
    if weekly is None:
        return s_out, e_out
    m = min(n, int(weekly.n_agents))
    off = np.asarray(weekly.day_offset, dtype=np.int64)
    d = int(day) % N_DAYS
    lo = off[d::N_DAYS][:m]
    hi = off[d + 1::N_DAYS][:m]
    counts = hi - lo
    total = int(counts.sum())
    if total == 0:
        return s_out, e_out
    rows = np.repeat(np.arange(m, dtype=np.int64), counts)
    base = np.repeat(np.cumsum(counts) - counts, counts)
    idx = np.repeat(lo, counts) + (np.arange(total, dtype=np.int64) - base)
    act = np.asarray(weekly.activity, dtype=np.int64)[idx]
    st = np.asarray(weekly.start_min, dtype=np.int64)[idx]
    en = np.asarray(weekly.end_min, dtype=np.int64)[idx]
    w = act == W17_WORK_CODE
    big = np.iinfo(np.int64).max
    first = np.full(m, big, dtype=np.int64)
    np.minimum.at(first, rows[w], st[w])
    last = np.full(m, -1, dtype=np.int64)
    np.maximum.at(last, rows[w], en[w])
    s_out[:m] = np.where(first < big, first, -1)
    e_out[:m] = last
    return s_out, e_out


class CalendarShadow:
    """暦 1a の影(状態台帳の行 ``CAL``・軸 1 diag・軸 2 derivable・中身は hash_skip)。

    Args:
        table: :func:`load_table` の表(ランの体の並び)。
        calendar: ``engine.calendar.SimCalendar``(読むだけ)。
        weekly: W17 の週次表(ランの体行へ ``restrict_to`` 済み・参考の差を数える・``None`` 可)。
        n_agents: ランの体の数(表に無い体=空欄)。
    """

    def __init__(self, table: CalendarTable, *, calendar: Any, weekly: Any = None, n_agents: int | None = None) -> None:
        self.table = table
        self.calendar = calendar
        self.weekly = weekly
        self.n = int(table.n if n_agents is None else n_agents)
        self.source = MODE_1A
        #: その日の影(体ごとの約束の種類・時刻・場所=書けない形)。日の頭に張り直す(W20・暦・日番号だけから決まる)。
        self.today: Mapping[str, Any] = MappingProxyType({})
        #: 日ごとの計器の記録(日番号 → 記録=書けない形・再開のランも同じ値を作り直す)。
        self.shadow_day_log: Mapping[int, Mapping[str, Any]] = MappingProxyType({})

    def __setattr__(self, name: str, value: Any) -> None:
        """〔検収 中 3〕欄は組み立てで 1 回だけ置ける(付け替えは ``AttributeError``)。日の頭の張り直しは ``relay_day`` の中だけ。"""
        if name in self.__dict__:
            raise AttributeError(f"暦 1a の影の欄 {name} は付け替えられない(日の頭の relay_day だけが張り直す)")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"暦 1a の影の欄 {name} は消せない")

    # ------------------------------------------------------------------ 日の頭
    def relay_day(self, day: int, *, w17_weekday: int | None = None) -> None:
        """``day`` 日目の影を張り直し、その日の計器の記録を作る(体の状態は読まない・書かない)。

        ``w17_weekday`` はその日に計画実行層が引く W17 の曜日の行(K9 のつなぎ=月曜の行)。参考の差だけに使う。
        """
        d = int(day)
        cal = self.calendar
        dt = cal.date_of_day(d)
        twd = int(cal.table_weekday(d))
        wk_raw = (dt - WEEK0_MONDAY).days // N_DAYS
        wk = wk_raw % max(self.table.n_weeks, 1)
        m = min(self.n, self.table.n)
        col = {c: np.asarray(v)[:m, wk, twd] for c, v in self.table.cols.items()}
        commit = col["commit"]
        work = commit == COMMIT_WORK
        school = commit == COMMIT_SCHOOL
        object.__setattr__(self, "today", _freeze({"day": d, "week": int(wk), "weekday": twd, **col}))
        rec: dict[str, Any] = {
            "day": d, "date": dt.isoformat(), "weekday": int(dt.weekday()), "table_weekday": twd,
            "holiday": bool(cal.is_holiday(d)), "week": int(wk), "week_wrapped": bool(wk != wk_raw),
            "agents": int(self.n),
            "shadows": {"work": int(work.sum()), "school": int(school.sum())},
            "blanks": {"no_commitment": int(self.n - work.sum() - school.sum()),
                       "school_time": int((school & (col["start_min"] < 0)).sum()),
                       "not_in_table": int(self.n - int(np.count_nonzero(self.table.found[:m])))},
            "depart_hist15": _hist15(col["depart_min"][work]),
            "start_hist15": _hist15(col["start_min"][work]),
            "end_hist15": _hist15(col["end_min"][work]),
            "return_hist15": _hist15(col["return_min"][work]),
            "next_day_end": int((col["end_min"][work] >= MINUTES_PER_DAY).sum()),
            "commute_min": _stats(col["lead_min"][work & (col["lead_min"] >= 0)]),
            "actor_rate15": _active15(col["start_min"][work], col["end_min"][work], int(self.n)),
            "place_kind": {int(k): int(v) for k, v in zip(*np.unique(col["place_kind"][work | school],
                                                                     return_counts=True))},
            "recurrence": {int(k): int(v) for k, v in zip(*np.unique(col["recurrence"][work | school],
                                                                     return_counts=True))},
        }
        if self.weekly is not None:
            wwd = twd if w17_weekday is None else int(w17_weekday)
            ws, we = _w17_work_span(self.weekly, wwd, m)
            w17 = ws >= 0
            both = work & w17
            rec["w17_ref"] = {
                "w17_weekday": int(wwd), "both": int(both.sum()), "w20_only": int((work & ~w17).sum()),
                "w17_only": int((~work & w17).sum()),
                "start_diff_min": _stats(col["start_min"][both] - ws[both]),
                "end_diff_min": _stats(col["end_min"][both] - we[both]),
                "w17_start_hist15": _hist15(ws[w17]),
            }
        object.__setattr__(self, "shadow_day_log", MappingProxyType({**dict(self.shadow_day_log), d: _freeze(rec)}))

    # ------------------------------------------------------------------ manifest
    def manifest(self) -> dict[str, Any]:
        days = [_thaw(self.shadow_day_log[k]) for k in sorted(self.shadow_day_log)]
        return {
            "schema": SCHEMA, "source": self.source, "w20": dict(self.table.version), "weeks": int(self.table.n_weeks),
            "days": days,
            "shadows": {"work": sum(r["shadows"]["work"] for r in days),
                        "school": sum(r["shadows"]["school"] for r in days)},
            "blanks": {"no_commitment": sum(r["blanks"]["no_commitment"] for r in days),
                       "school_time": sum(r["blanks"]["school_time"] for r in days)},
        }


def manifest_fields(layer: CalendarShadow | None) -> dict[str, Any]:
    """manifest の ``calendar_shadow``(腕 w17 のランは源だけ・ほかの子は null)。"""
    if layer is None:
        return {"schema": SCHEMA, "source": MODE_W17, "w20": None, "weeks": None, "days": None, "shadows": None,
                "blanks": None}
    return layer.manifest()


def build(world_dir: str | Path | None, pop: Any, *, calendar: Any, weekly: Any, n_agents: int) -> CalendarShadow | None:
    """組み立ての口: 腕 1a のランの影を作り、0 日目を張る(腕 w17 は ``None``)。

    Raises:
        ValueError: 腕 1a で母集団(W16)の無いラン(影は W16 の体に W20 の行を引く=合成の体には引けない)。
        FileNotFoundError: W20 の週の表が無い。
    """
    if not is_on():
        return None
    if pop is None:
        raise ValueError("腕 --calendar-shadow 1a は母集団(W16)のあるランだけ(影は W16 の体に W20 の週の表を引く)")
    path = resolve_path(world_dir)
    if path is None:
        raise FileNotFoundError("腕 --calendar-shadow 1a には世界資産の置き場(world_dir)か SHIBUYA_CALENDAR_W20 が要る")
    table = load_table(path, np.asarray(pop.source_agent_id, dtype=np.int64))
    layer = CalendarShadow(table, calendar=calendar, weekly=weekly, n_agents=min(int(n_agents), table.n))
    layer.relay_day(0, w17_weekday=int(calendar.table_weekday(0)))
    return layer
