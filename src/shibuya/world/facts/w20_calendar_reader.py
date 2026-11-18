"""world.facts.w20_calendar_reader — 割る段で ``engine/calendar_shadow.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``society/calendar_shadow.py`` に残した元の docstring を読むこと。
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

__all__ = [
    "FILE_NAME", "HEADER_NAME", "WEEK0_MONDAY", "resolve_path", "CalendarTable", "load_table",
]


#: W20 の週の表とヘッダ(構築側の段 W20cal の出力の名=``build.sched.w20_calendar_1a`` と同じ・試験が突き合わせる)。
FILE_NAME: Final[str] = "w20_calendar_1a.parquet"
#: 組んだ資産の置き場(リポの根からの相対・本体の data/world/v2 への活性化は版上げ 3 回目)。〔検収 低 7〕この名は
#: ここだけに書く(計器 ``tools/instruments/anchor_gauge.py``・記録の道具・試験はこの定数を読む)。
STAGE_DIR: Final[str] = "data/world/v2_stage_3-1"
HEADER_NAME: Final[str] = "calendar_1a.header.json"
#: 週 0 の月曜(W20 の ``WEEK0_MONDAY``・暦の ``DEFAULT_WORLD_START`` と同じ日)。
WEEK0_MONDAY: Final[date] = date(2026, 7, 13)
N_DAYS: Final[int] = 7
COMMIT_WORK: Final[int] = 1
COMMIT_SCHOOL: Final[int] = 2
_COLS: Final[tuple[str, ...]] = ("commit", "start_min", "end_min", "depart_min", "return_min", "lead_min",
                                 "place_kind", "target_cell", "recurrence", "certainty")


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
