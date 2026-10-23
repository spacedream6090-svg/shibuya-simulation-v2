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

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

import numpy as np

from shibuya.agents.weekly import ACTIVITY_WORDS
from shibuya.core.time_consts import MINUTES_PER_DAY

__all__ = [
    "MODE_W17", "MODE_1A", "MODES", "DEFAULT_MODE", "SCHEMA", "FILE_NAME", "HEADER_NAME", "WEEK0_MONDAY",
    "arm", "set_arm", "is_on", "resolve_path", "CalendarTable", "load_table", "CalendarShadow", "manifest_fields",
    "MANIFEST_CONFIG", "MANIFEST_OBSERVED",
]

MODE_W17: Final[str] = "w17"
MODE_1A: Final[str] = "1a"
MODES: Final[tuple[str, ...]] = (MODE_W17, MODE_1A)
#: 既定(影を作らない=今と同じ)。
DEFAULT_MODE: Final[str] = MODE_W17
#: manifest の ``calendar_shadow`` の形の版。
SCHEMA: Final[str] = "shibuya.calendar_shadow/1"
#: W20 の週の表とヘッダ(構築側の段 W20cal の出力の名=``build.sched.w20_calendar_1a`` と同じ・試験が突き合わせる)。
FILE_NAME: Final[str] = "w20_calendar_1a.parquet"
#: 組んだ資産の置き場(リポの根からの相対・本体の data/world/v2 への活性化は版上げ 3 回目)。〔検収 低 7〕この名は
#: ここだけに書く(計器 ``tools/instruments/anchor_gauge.py``・記録の道具・試験はこの定数を読む)。
STAGE_DIR: Final[str] = "data/world/v2_stage_3-1"
HEADER_NAME: Final[str] = "calendar_1a.header.json"
#: 週 0 の月曜(W20 の ``WEEK0_MONDAY``・暦の ``DEFAULT_WORLD_START`` と同じ日)。
WEEK0_MONDAY: Final[date] = date(2026, 7, 13)
N_DAYS: Final[int] = 7
#: 15 分の枠(1 日 96)。
SLOT_MIN: Final[int] = 15
N_SLOTS: Final[int] = MINUTES_PER_DAY // SLOT_MIN
COMMIT_WORK: Final[int] = 1
COMMIT_SCHOOL: Final[int] = 2
#: W17 の「勤務」の活動語コード(``agents.weekly.ACTIVITY_WORDS`` の索引)。
W17_WORK_CODE: Final[int] = ACTIVITY_WORDS.index("勤務")
#: manifest の子の鍵(設定/観測=``engine.manifest_sections`` の表と同じ・試験が突き合わせる)。
MANIFEST_CONFIG: Final[tuple[str, ...]] = ("schema", "source", "w20", "weeks")
MANIFEST_OBSERVED: Final[tuple[str, ...]] = ("days", "shadows", "blanks")
_COLS: Final[tuple[str, ...]] = ("commit", "start_min", "end_min", "depart_min", "return_min", "lead_min",
                                 "place_kind", "target_cell", "recurrence", "certainty")

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


def resolve_path(world_dir: str | Path | None) -> Path | None:
    """W20 の週の表の道筋(環境変数 ``SHIBUYA_CALENDAR_W20`` があればそれ・無ければ ``<world_dir>/w20_calendar_1a.parquet``)。"""
    env = os.environ.get("SHIBUYA_CALENDAR_W20", "").strip()
    if env:
        return Path(env)
    if world_dir is None:
        return None
    return Path(world_dir) / FILE_NAME


@dataclass(frozen=True)
class CalendarTable:
    """ランの体の並びに引き直した W20 の週の表(配列は ``(体, 週, 曜日)``)と版の記録。

    Attributes:
        n: 体の数(ランの体行の先頭から。表に無い体は ``found=False``=空欄)。
        n_weeks: 表の週の数。
        cols: 欄 → ``(n, n_weeks, 7)`` の配列(:data:`_COLS`)。
        found: 表に行がある体。
        version: 版の記録(段・版・表の sha256・入力と設定の指紋)。
        agent_id: ランの体の W16 の ``agent_id``(引き直しに使った並び)。
    """

    n: int
    n_weeks: int
    cols: Mapping[str, np.ndarray]
    found: np.ndarray
    version: Mapping[str, Any]
    agent_id: np.ndarray | None = None

    def __post_init__(self) -> None:
        """〔検収 中 3〕実行時の守り: 欄の辞書は ``MappingProxyType``・配列は書けない形(``setflags(write=False)``)。"""
        object.__setattr__(self, "cols", MappingProxyType({k: _readonly(v) for k, v in dict(self.cols).items()}))
        object.__setattr__(self, "found", _readonly(np.asarray(self.found, dtype=bool)))
        object.__setattr__(self, "version", _freeze(dict(self.version)))
        if self.agent_id is not None:
            object.__setattr__(self, "agent_id", _readonly(np.asarray(self.agent_id, dtype=np.int64)))


def _readonly(a: Any) -> np.ndarray:
    """書けない写し(元の配列は触らない)。"""
    out = np.array(a, copy=True)
    out.setflags(write=False)
    return out


def _freeze(v: Any) -> Any:
    """記録の値を書けない形に(dict → MappingProxyType・list → tuple・配列 → 書けない写し)。"""
    if isinstance(v, Mapping):
        return MappingProxyType({k: _freeze(x) for k, x in v.items()})
    if isinstance(v, (list, tuple)):
        return tuple(_freeze(x) for x in v)
    if isinstance(v, np.ndarray):
        return _readonly(v)
    return v


def _thaw(v: Any) -> Any:
    """manifest に書く形に戻す(MappingProxyType → dict・tuple → list)。"""
    if isinstance(v, Mapping):
        return {k: _thaw(x) for k, x in v.items()}
    if isinstance(v, tuple):
        return [_thaw(x) for x in v]
    return v


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_table(path: str | Path, agent_ids: Any) -> CalendarTable:
    """W20 の週の表を読み、ランの体の並び(``agent_ids``=W16 の ``agent_id``)に引き直す。

    Raises:
        FileNotFoundError: 表が無い(腕 1a は表が要る=``--world data/world/v2_stage_3-1`` か ``SHIBUYA_CALENDAR_W20``)。
        ValueError: 表の行が (agent_id, week, weekday) の密な昇順でない。
    """
    import pyarrow.parquet as pq  # 遅延 import(腕 1a のランだけ)

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"腕 --calendar-shadow 1a には W20 の週の表が要る: {p.name}(置き場 {STAGE_DIR} か "
                                "SHIBUYA_CALENDAR_W20)")
    t = pq.read_table(p, columns=["agent_id", "week", "weekday", *_COLS])
    aid = np.asarray(t.column("agent_id").to_numpy(), dtype=np.int64)
    week = np.asarray(t.column("week").to_numpy(), dtype=np.int64)
    wd = np.asarray(t.column("weekday").to_numpy(), dtype=np.int64)
    n_weeks = int(week.max()) + 1 if week.size else 1
    per = n_weeks * N_DAYS
    if aid.size % per or not (np.array_equal(wd, np.tile(np.arange(N_DAYS), aid.size // N_DAYS))
                              and np.array_equal(week, np.tile(np.repeat(np.arange(n_weeks), N_DAYS), aid.size // per))):
        raise ValueError(f"{p.name} が (agent_id, week, weekday) の密な昇順でない")
    agents = aid[::per]
    if agents.size > 1 and np.any(agents[1:] <= agents[:-1]):
        raise ValueError(f"{p.name} の agent_id が昇順でない")
    want = np.asarray(agent_ids, dtype=np.int64).ravel()
    pos = np.searchsorted(agents, want)
    safe = np.clip(pos, 0, max(agents.size - 1, 0))
    found = (agents[safe] == want) if (want.size and agents.size) else np.zeros(want.size, dtype=bool)
    found = np.asarray(found, dtype=bool)
    cols: dict[str, np.ndarray] = {}
    for c in _COLS:
        v = np.asarray(t.column(c).to_numpy(), dtype=np.int64).reshape(agents.size, n_weeks, N_DAYS)
        out = v[safe].copy() if agents.size else np.zeros((want.size, n_weeks, N_DAYS), dtype=np.int64)
        out[~found] = 0 if c in ("commit", "place_kind", "recurrence", "certainty") else -1
        cols[c] = out
    head: dict[str, Any] = {}
    hp = p.with_name(HEADER_NAME)
    if hp.exists():
        h = json.loads(hp.read_text(encoding="utf-8"))
        head = {"stage": h.get("stage"), "stage_version": h.get("stage_version"),
                "input_hash": str(h.get("input_hash", ""))[:16], "param_hash": str(h.get("param_hash", ""))[:16]}
    version = {**head, "file": p.name, "sha256": _sha256(p)[:16], "rows": int(aid.size), "agents": int(agents.size)}
    return CalendarTable(n=int(want.size), n_weeks=n_weeks, cols=cols, found=found, version=version,
                         agent_id=want.copy())


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
