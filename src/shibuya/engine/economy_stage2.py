"""engine.economy_stage2 — 経済の段階 2 の腕と engine の側の組み立て(第 2 期 2-1・CP2 の段階 2)。

腕(切替口): ``--economy-stage2 {off,on}``(環境変数 ``SHIBUYA_ECONOMY_STAGE2``・:func:`set_arm`)。既定 ``off``=何も
作らない(final・帳簿・台帳の行は今のまま)。``on`` で部品(``--economy-stage2-parts``・環境変数
``SHIBUYA_ECONOMY_STAGE2_PARTS``・既定=全部 ``wages,withdraw,payment,tax,visitors``)を 1 つずつ測れる。腕は組み立ての
ときに読む(ランの途中で変えても、そのランは変わらない)。``run_day`` の引数でも設定の指紋でもない(出来事の記録・記憶の器・
候補の口の腕と同じ扱い)。腕と部品は manifest の ``economy.stage2`` に出る。

engine の側の受け持ち(engine は economy を import できない=層の契約。お金の中身は ``economy.stage2.MoneyStage2``):

- ``Stage2Plan``: 部品・体の種別・月の労働時間(W17 の「勤務」)・ATM の表・給料日(暦の口 ``SimCalendar.is_payday``=毎月
  25 日・土休なら前の営業日)・雇用の行(権利台帳の ``employ``・``Rights.pairs``)・原因(``Process("payroll"|"atm"|
  "register")``)。組み立て(``attach``)が作って ``Ledger.attach_stage2`` に渡す。
- ``AtmTable``(``Fixtures.atms``): OSM の ``amenity=atm``・``atm=yes``(コンビニ)・``amenity=bank``(銀行の支店=
  ``atm`` の印に関わらず全部・〔検収 L3〕)の点をセルに写し、営業時間(``opening_hours``)を曜日 × 分の区間に。
- 引き出しの場所と時刻の検査(``atm_open_cells``): 行為の解決(``engine.resolve.apply``)と候補の口(腕 port の源
  affordance)が読む。

逐次ループ宣言(P4): ``build_atm_table`` は OSM の要素の数(約 3,500)と引き出しの点の数(数十)ぶん・組み立てで 1 回。
``parse_opening_hours`` は規則の数ぶん。ほかは配列演算(刻みごとの営業中のセルは ATM の数ぶんの配列演算)。

**未リサーチ(expedient)**(つなぎの台帳 ``DOC-ec21-*``・記録 ``ec21/README.md``): ATM の表は組み立てで OSM から作る
(2-4 で W6 の POI に ATM の行を足す)・営業時間の無い ATM は 24 時間・祝日は曜日の規則のまま(OSM の ``PH`` を読まない)・
セルは地上の層を先に(無ければ同じ格子のほかの層)・営業時間の無い(読めない)銀行の支店は平日 9:00-15:00・土日は閉
(``BANK_DEFAULT_HOURS``・つなぎの台帳 ``DOC-ec21-bank-branch-default-hours``)・
給料日=毎月 25 日。
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Iterable, Mapping

import numpy as np

from shibuya.core.time_consts import MINUTES_PER_DAY, MINUTES_PER_HOUR, NS_PER_SECOND, SECONDS_PER_MINUTE

__all__ = [
    "ARM_OFF", "ARM_ON", "ARMS", "PARTS", "arm", "set_arm", "parts", "set_parts", "parse_parts", "active_parts",
    "WITHDRAW_WORD", "PAYMENT_NOTE", "CAUSE_NAMES", "PAYDAY_DAY_OF_MONTH", "OSM_TAGS_RELPATH", "OSM_HOURS_RELPATH",
    "ORIGIN_LATLON", "M_PER_DEG_LAT", "M_PER_DEG_LON", "CELL_M", "AtmTable", "parse_opening_hours",
    "build_atm_table", "set_atm_table", "Stage2Plan", "weekly_work_hours", "attach", "money_stage2",
    "atm_open_cells", "WEEKS_PER_MONTH", "population_total",
]

ARM_OFF: Final[str] = "off"
ARM_ON: Final[str] = "on"
ARMS: Final[tuple[str, ...]] = (ARM_OFF, ARM_ON)
#: 部品(``economy.stage2.PARTS`` と同じ並び=試験が突き合わせる)。
PARTS: Final[tuple[str, ...]] = ("wages", "withdraw", "payment", "tax", "visitors")
#: 腕 port の候補の語(源 affordance=営業中の ATM のセルで出す)。行為の語彙 12 語には足さない(副の判断)。
WITHDRAW_WORD: Final[str] = "お金を下ろす"
#: 腕 port の購入・食事の候補の文に添える注(支払いの方法=EC3)。プロンプトの既定は変えない。
PAYMENT_NOTE: Final[str] = "支払いは現金かカード"
#: 段階 2 の原因の過程の名(``engine.events.vocab.ECONOMY_PROCESSES`` と同じ)。
CAUSE_NAMES: Final[tuple[str, ...]] = ("payroll", "atm", "register")
#: 給料日(毎月この日・``economy.stage2.PAYDAY_DAY_OF_MONTH`` と同じ)。
PAYDAY_DAY_OF_MONTH: Final[int] = 25
#: 月の週の数(年 52 週 ÷ 12 か月=W17 の週の勤務の分 → 月の労働時間)。
WEEKS_PER_MONTH: Final[float] = 52.0 / 12.0

#: OSM の取得物(許可済み・ODbL・ライセンス台帳に記載済み=発注)。
OSM_TAGS_RELPATH: Final[str] = "data/realworld/osm/poi_tags_overpass_20260928.json"
OSM_HOURS_RELPATH: Final[str] = "data/realworld/osm/poi_opening_hours_overpass_20260907.json"
#: 世界の座標の原点と 1 度あたりのメートル(``build.geo.common`` の写し=build は実行時に import できない・試験が突き合わせる)。
ORIGIN_LATLON: Final[tuple[float, float]] = (35.6595, 139.70062)
M_PER_DEG_LAT: Final[float] = 111132.9
M_PER_DEG_LON: Final[float] = 111320.0 * math.cos(math.radians(ORIGIN_LATLON[0]))
CELL_M: Final[float] = 100.0

_ARM: str = os.environ.get("SHIBUYA_ECONOMY_STAGE2", ARM_OFF).strip().lower() or ARM_OFF
if _ARM not in ARMS:
    raise ValueError(f"SHIBUYA_ECONOMY_STAGE2 は {ARMS} のどれか(いま {_ARM!r})")


def parse_parts(spec: Any) -> tuple[str, ...]:
    """部品の指定(``"wages,withdraw"``・並び・空=全部)→ 部品の並び(``PARTS`` の順)。"""
    if spec is None:
        return PARTS
    items = [s.strip() for s in (spec.split(",") if isinstance(spec, str) else spec) if str(s).strip()]
    if not items or items == ["all"]:
        return PARTS
    if items == ["none"]:
        return ()
    bad = sorted(set(items) - set(PARTS))
    if bad:
        raise ValueError(f"--economy-stage2-parts は {PARTS} の中(いま {bad})")
    return tuple(p for p in PARTS if p in items)


_PARTS: tuple[str, ...] = parse_parts(os.environ.get("SHIBUYA_ECONOMY_STAGE2_PARTS") or None)


def arm() -> str:
    """いまの腕(``off``=既定・``on``)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--economy-stage2``・試験の切替口)。"""
    global _ARM
    if str(name) not in ARMS:
        raise ValueError(f"--economy-stage2 は {ARMS} のどれか(いま {name!r})")
    _ARM = str(name)


def parts() -> tuple[str, ...]:
    """いまの部品(腕が off でも指定は持つ=腕が on のときだけ効く)。"""
    return _PARTS


def set_parts(spec: Any) -> None:
    """部品を選ぶ(CLI ``--economy-stage2-parts``・試験の切替口)。"""
    global _PARTS
    _PARTS = parse_parts(spec)


def active_parts() -> frozenset[str]:
    """腕が on のときの部品(off なら空)。"""
    return frozenset(_PARTS) if _ARM == ARM_ON else frozenset()


def header_fields(plan: Any) -> dict[str, Any] | None:
    """〔検収 A5〕状態のファイルの見出しの ``economy_stage2``(腕 off のランは書かない=None=今の見出しのまま)。"""
    if plan is None:
        return None
    return {"arm": ARM_ON, "parts": list(plan.parts)}


def check_resume(saved: Any) -> None:
    """〔検収 A5〕再開のときに、保存したランの腕と部品(見出しの ``economy_stage2``・無ければ off)と今の腕が同じかを
    確かめる(違えば止める)。腕は設定の指紋に入れない(``run_day`` の引数ではない)ので指紋の検査では見つからない=ここで
    見る(2-2 の近接の腕と同じ形)。
    """
    s = saved if isinstance(saved, Mapping) else {}
    s_arm = str(s.get("arm", ARM_OFF))
    s_parts = tuple(str(p) for p in s.get("parts", ()))
    now_parts = tuple(p for p in PARTS if p in active_parts())
    if s_arm != _ARM or (_ARM == ARM_ON and s_parts != now_parts):
        raise ValueError(f"再開の経済の段階 2 の腕が親と違う(親 arm={s_arm} parts={list(s_parts)}・今 arm={_ARM} "
                         f"parts={list(now_parts)})=--economy-stage2・--economy-stage2-parts(環境変数 "
                         "SHIBUYA_ECONOMY_STAGE2・SHIBUYA_ECONOMY_STAGE2_PARTS)を親にそろえる")


# ================================================================ ATM の表(Fixtures.atms)
_DAY_NAMES: Final[tuple[str, ...]] = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
_N_DAYS: Final[int] = 7
#: 1 つの曜日に持てる営業の区間の数(OSM の点は 1 つ=夜をまたぐ区間を分けた分の余り)。
_SLOTS: Final[int] = 2
#: 営業時間の無い(読めない)銀行の支店の営業時間(窓口の時間=平日 9:00-15:00・土日は閉・祝日は曜日の規則のまま)。
#: **未リサーチ(expedient)**(つなぎの台帳 ``DOC-ec21-bank-branch-default-hours``・外す段 2-4=W6 の POI に営業時間)。
BANK_DEFAULT_HOURS: Final[str] = "Mo-Fr 09:00-15:00"
_TIME = re.compile(r"^(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$")


def _days_of(spec: str) -> list[int] | None:
    out: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if part == "PH":
            continue  # 祝日の規則は読まない(宣言=祝日は曜日の規則のまま)
        if "-" in part:
            a, b = part.split("-", 1)
            if a not in _DAY_NAMES or b not in _DAY_NAMES:
                return None
            i, j = _DAY_NAMES.index(a), _DAY_NAMES.index(b)
            out.extend((i + d) % _N_DAYS for d in range((j - i) % _N_DAYS + 1))
        elif part in _DAY_NAMES:
            out.append(_DAY_NAMES.index(part))
        else:
            return None
    return out


def parse_opening_hours(text: str | None) -> np.ndarray | None:
    """OSM の ``opening_hours`` → 曜日 × 区間の ``(7, 2, 2)`` int16(``[曜日, 区間, (始め, 終わり)]`` の分・空は -1)。

    読める形: ``24/7``・``<曜日> HH:MM-HH:MM[,HH:MM-HH:MM]``・``<曜日> off``・``;`` で並べた規則(後の規則が前の規則の
    曜日を上書き=OSM の規則)。曜日の無い規則は毎日。夜をまたぐ区間は翌日の 0 時からに分ける。読めない文字は ``None``
    (呼び手が 24 時間として数える=宣言)。``None`` の入力も ``None``。
    """
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None
    out = np.full((_N_DAYS, _SLOTS, 2), -1, dtype=np.int16)
    if s == "24/7":
        out[:, 0, 0], out[:, 0, 1] = 0, MINUTES_PER_DAY
        return out
    for rule in (r.strip() for r in s.split(";") if r.strip()):  # 逐次ループ宣言: 規則の数ぶん
        toks = rule.split(" ", 1)
        if len(toks) == 1:
            days, times = list(range(_N_DAYS)), toks[0]
        else:
            days = _days_of(toks[0])
            times = toks[1].strip()
            if days is None:
                days, times = list(range(_N_DAYS)), rule
        spans: list[tuple[int, int, int]] = []  # (曜日のずれ, 始め, 終わり)
        if times != "off":
            for t in times.split(","):
                m = _TIME.match(t.strip())
                if m is None:
                    return None
                a = int(m.group(1)) * MINUTES_PER_HOUR + int(m.group(2))
                b = int(m.group(3)) * MINUTES_PER_HOUR + int(m.group(4))
                if not (0 <= a <= MINUTES_PER_DAY and 0 <= b <= MINUTES_PER_DAY):
                    return None
                if b > a:
                    spans.append((0, a, b))
                else:  # 夜をまたぐ(終わりが始め以下)
                    spans.append((0, a, MINUTES_PER_DAY))
                    if b > 0:
                        spans.append((1, 0, b))
        for d in days:
            out[d] = -1
        for d in days:
            for shift, a, b in spans:
                dd = (d + shift) % _N_DAYS
                free = np.flatnonzero(out[dd, :, 0] < 0)
                if free.size == 0:
                    return None
                out[dd, free[0]] = (a, b)
    return out


@dataclass(frozen=True)
class AtmTable:
    """ATM の表(``Fixtures.atms``・状態台帳の行 ATM=軸 1 behavior・軸 2 derivable・中身は hash_skip)。銀行名は持たない。

    Attributes:
        cell: ATM ごとのセル(``world`` のセルの番号)。
        kind: 0=単独の ATM(``amenity=atm``)・1=店の中(``shop`` で ``atm=yes``)・2=銀行の支店(``amenity=bank``=
            ``atm`` の印に関わらず全部・窓口の引き出しを含む・〔検収 L3〕)。
        hours: ``(ATM, 7, 2, 2)`` の営業の区間(``parse_opening_hours``)。
        hours_from: 0=要素の ``opening_hours``・1=営業時間の取得物(2026-09-07)・2=無い(24 時間=宣言)・3=読めない(24 時間)・
            4=銀行の支店で無いか読めない(``BANK_DEFAULT_HOURS``=平日 9:00-15:00・土日は閉=宣言)。
        n_cells: 世界のセルの数。
        dropped: セルに写せなかった点の数(範囲の外)。
        sources: 取得物の名と md5。
    """

    cell: np.ndarray
    kind: np.ndarray
    hours: np.ndarray
    hours_from: np.ndarray
    n_cells: int
    dropped: int = 0
    sources: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # 〔検収 L1〕実行時に書き換えられない表(配列は写しを読み取り専用に・出どころは MappingProxyType)
        for name in ("cell", "kind", "hours", "hours_from"):
            a = np.array(getattr(self, name), copy=True)
            a.setflags(write=False)
            object.__setattr__(self, name, a)
        object.__setattr__(self, "sources", MappingProxyType(dict(self.sources)))

    @property
    def n(self) -> int:
        return int(self.cell.size)

    def open_at(self, weekday: int, minute: int) -> np.ndarray:
        """ATM ごとに曜日 ``weekday``(0=月)・日の中の分 ``minute`` に営業中か。"""
        h = self.hours[:, int(weekday) % _N_DAYS]  # (ATM, 区間, 2)
        m = int(minute)
        return ((h[:, :, 0] >= 0) & (h[:, :, 0] <= m) & (m < h[:, :, 1])).any(axis=1)

    def open_cells(self, weekday: int, minute: int) -> np.ndarray:
        """セルごとに営業中の ATM が 1 つでもあるか(``(n_cells,)`` bool)。"""
        out = np.zeros(int(self.n_cells), dtype=bool)
        if self.n:
            c = self.cell[self.open_at(weekday, minute)]
            out[c[(c >= 0) & (c < out.size)]] = True
        return out

    def record(self) -> dict[str, Any]:
        """manifest の ``economy.stage2.atms``(点の数・種類・営業時間の出どころ・セルの数・出どころの md5)。"""
        kinds = np.bincount(self.kind.astype(np.int64), minlength=3) if self.n else np.zeros(3, np.int64)
        src = np.bincount(self.hours_from.astype(np.int64), minlength=5) if self.n else np.zeros(5, np.int64)
        return {
            "n": int(self.n), "cells": int(np.unique(self.cell).size) if self.n else 0, "dropped": int(self.dropped),
            "kind": {"atm": int(kinds[0]), "shop": int(kinds[1]), "bank": int(kinds[2])},
            "hours_from": {"tag": int(src[0]), "hours_file": int(src[1]), "none_24h": int(src[2]),
                           "unparsed_24h": int(src[3]), "bank_default": int(src[4])},
            "sources": dict(self.sources),
        }


def _md5(p: Path) -> str:
    h = hashlib.md5()  # noqa: S324 — 同定の印(暗号ではない)
    h.update(p.read_bytes())
    return h.hexdigest()


def _cell_lookup(world: Any) -> tuple[dict[tuple[int, int], list[tuple[int, int]]], int]:
    a = world.assets
    ix = np.asarray(a.cell_ix, dtype=np.int64)
    iy = np.asarray(a.cell_iy, dtype=np.int64)
    band = np.asarray(a.cell_band, dtype=np.int64)
    by: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for c in range(ix.size):  # 逐次ループ宣言: セルの数(520)・組み立てで 1 回
        by.setdefault((int(ix[c]), int(iy[c])), []).append((int(band[c]), c))
    return by, int(ix.size)


def build_atm_table(world: Any, *, tags_path: str | Path | None = None,
                    hours_path: str | Path | None = None) -> AtmTable:
    """OSM の取得物から引き出しの場所の表を作る(``amenity=atm``・``atm=yes``・``amenity=bank``=銀行の支店は全部)。

    セル: 緯度経度 → 世界のローカル座標(``build.geo.common.latlon_to_local`` の写し)→ 100 m の格子 → 地上の層(GL)の
    セル(無ければ同じ格子の DECK・UG の順)。取得物が無い写し(データの無い試験)は空の表(警告を 1 回)。
    """
    from shibuya.engine.calendar import resolve_repo_path

    tp = resolve_repo_path(tags_path or OSM_TAGS_RELPATH)
    hp = resolve_repo_path(hours_path or OSM_HOURS_RELPATH)
    by, n_cells = _cell_lookup(world)
    empty = AtmTable(cell=np.zeros(0, np.int64), kind=np.zeros(0, np.int8), hours=np.zeros((0, _N_DAYS, _SLOTS, 2),
                     np.int16), hours_from=np.zeros(0, np.int8), n_cells=n_cells, sources={})
    if not tp.exists():
        warnings.warn(f"ATM の表の取得物 {OSM_TAGS_RELPATH} が無い写し: ATM は 0 点", RuntimeWarning, stacklevel=2)
        return empty
    els = json.loads(tp.read_text(encoding="utf-8")).get("elements", [])
    hours_map: dict[tuple[str, int], str] = {}
    sources = {Path(OSM_TAGS_RELPATH).name: _md5(tp)}
    if hp.exists():
        for e in json.loads(hp.read_text(encoding="utf-8")).get("elements", []):  # 逐次ループ宣言: 要素の数
            oh = (e.get("tags") or {}).get("opening_hours")
            if oh:
                hours_map[(str(e.get("type")), int(e.get("id")))] = str(oh)
        sources[Path(OSM_HOURS_RELPATH).name] = _md5(hp)
    cells: list[int] = []
    kinds: list[int] = []
    hours: list[np.ndarray] = []
    hfrom: list[int] = []
    dropped = 0
    full = parse_opening_hours("24/7")
    bank_default = parse_opening_hours(BANK_DEFAULT_HOURS)
    for e in els:  # 逐次ループ宣言: OSM の要素の数(約 3,500)・組み立てで 1 回
        t = e.get("tags") or {}
        if not (t.get("amenity") in ("atm", "bank") or t.get("atm") == "yes"):
            continue
        kind = 0 if t.get("amenity") == "atm" else (2 if t.get("amenity") == "bank" else 1)
        if "lat" in e and "lon" in e:
            lat, lon = float(e["lat"]), float(e["lon"])
        elif "center" in e:
            lat, lon = float(e["center"]["lat"]), float(e["center"]["lon"])
        else:
            dropped += 1
            continue
        x = (lon - ORIGIN_LATLON[1]) * M_PER_DEG_LON
        y = (lat - ORIGIN_LATLON[0]) * M_PER_DEG_LAT
        key = (int(math.floor(x / CELL_M)), int(math.floor(y / CELL_M)))
        cand = sorted(by.get(key, []), key=lambda bc: (bc[0] != 0, -bc[0]))  # GL(0)→ DECK(1)→ UG(-1)
        if not cand:
            dropped += 1
            continue
        oh = t.get("opening_hours")
        src = 0
        if not oh:
            oh = hours_map.get((str(e.get("type")), int(e.get("id"))))
            src = 1 if oh else 2
        parsed = parse_opening_hours(oh) if oh else None
        if parsed is None and kind == 2:  # 〔検収 L3〕銀行の支店: 平日 9:00-15:00・土日は閉(宣言)
            parsed = bank_default
            src = 4
        elif parsed is None:
            parsed = full
            src = 2 if not oh else 3
        cells.append(int(cand[0][1]))
        kinds.append(kind)
        hours.append(parsed)
        hfrom.append(src)
    if not cells:
        return dataclasses.replace(empty, dropped=dropped, sources=sources)
    return AtmTable(cell=np.asarray(cells, dtype=np.int64), kind=np.asarray(kinds, dtype=np.int8),
                    hours=np.stack(hours).astype(np.int16), hours_from=np.asarray(hfrom, dtype=np.int8),
                    n_cells=n_cells, dropped=dropped, sources=sources)


#: 試験の切替口: 組み立ての ATM の表を差し替える(合成の世界=OSM の点がセルに乗らない)。``None``=OSM から作る。
_ATM_OVERRIDE: AtmTable | None = None


def set_atm_table(table: AtmTable | None) -> None:
    """試験の切替口(合成の世界の ATM の表を渡す)。``None`` で OSM から作る既定に戻す。"""
    global _ATM_OVERRIDE
    _ATM_OVERRIDE = table


# ================================================================ 段階 2 の組み立ての物
def weekly_work_hours(weekly: Any, n_agents: int) -> tuple[np.ndarray | None, str]:
    """W17 の週次表の「勤務」の週の分 → 月の労働時間[時](``WEEKS_PER_MONTH`` 週)。W17 の無いランは ``(None, "default")``。

    週次表の体の行は ``restrict_to(母集団の agent_id)`` の後=ランの体の番号の順(計画実行層と同じ並び)。
    """
    if weekly is None:
        return None, "default"
    from shibuya.agents.weekly import ACTIVITY_WORDS

    work = ACTIVITY_WORDS.index("勤務")
    n = int(n_agents)
    off = np.asarray(weekly.day_offset, dtype=np.int64)
    rows = np.repeat(np.arange(int(weekly.n_agents), dtype=np.int64), np.diff(off[:: _N_DAYS][: int(weekly.n_agents) + 1]))
    dur = (np.asarray(weekly.end_min, dtype=np.int64) - np.asarray(weekly.start_min, dtype=np.int64))
    is_work = np.asarray(weekly.activity) == work
    m = min(rows.size, dur.size)
    minutes = np.bincount(rows[:m][is_work[:m]], weights=dur[:m][is_work[:m]].astype(np.float64),
                          minlength=int(weekly.n_agents))
    out = np.zeros(n, dtype=np.float64)
    k = min(n, minutes.size)
    out[:k] = minutes[:k] * WEEKS_PER_MONTH / float(MINUTES_PER_HOUR)
    return out, "w17_work"


class Stage2Plan:
    """engine の側の段階 2 の組み立ての物(``Ledger.attach_stage2`` に渡す・``MoneyStage2.plan``)。

    dataclass でない(状態台帳の行 EC の中の参照=同一性だけを見る)。組み立てが作り、ランの間は ``runner`` の後付けの外は
    書かない。
    """

    def __init__(self, *, parts: Iterable[str], kinds: Any, monthly_hours: Any, hours_source: str,
                 atms: AtmTable | None, calendar: Any, tick_seconds: int, n_agents: int,
                 population_scale: float | None, causes: Mapping[str, Any]) -> None:
        self.parts = tuple(p for p in PARTS if p in set(parts))
        self.kinds = np.array(kinds, dtype=np.int64, copy=True)
        self.monthly_hours = None if monthly_hours is None else np.array(monthly_hours, dtype=np.float64, copy=True)
        self.hours_source = str(hours_source)
        self.hourly = None  # W16/W17 に賃金の属性が無い=最低賃金(規則の表)
        self.atms = atms
        self.calendar = calendar
        self.payday_calendar = dataclasses.replace(calendar, payday_day_of_month=PAYDAY_DAY_OF_MONTH)
        self.tick_seconds = int(tick_seconds)
        self.tpd = int(calendar.ticks_per_day)
        self.n_agents = int(n_agents)
        self.population_scale = population_scale
        self.causes = MappingProxyType(dict(causes))
        #: 世界過程の実行器(権利台帳の持ち主=開閉の過程)。組み立てが実行器を作った後に 1 回だけ置く。
        self.runner: Any = None
        for a in (self.kinds, self.monthly_hours):
            if a is not None:
                a.setflags(write=False)
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name: str, value: Any) -> None:
        """〔検収 L1〕組み立ての後は ``runner`` を 1 回置く外は書けない。"""
        if getattr(self, "_sealed", False):
            if name != "runner" or getattr(self, "runner", None) is not None:
                raise AttributeError(f"Stage2Plan は組み立ての後は書けない({name})")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"Stage2Plan の属性は消せない({name})")

    # ---- 暦の口 ----
    def is_payday(self, day: int) -> bool:
        return bool(self.payday_calendar.is_payday(int(day)))

    def date_of(self, day: int) -> Any:
        return self.calendar.date_of_day(int(day))

    def date_of_step(self, step: int) -> Any:
        return self.calendar.datetime_of(int(step)).date()

    def close_step(self, day: int) -> int:
        """日の締めの刻み(その日の最後の刻みの頭)。"""
        return int(self.calendar.to_T(int(day), self.tpd - 1))

    def weekday_minute(self, step: int) -> tuple[int, int]:
        """刻み → (曜日, 日の中の分)。祝日は曜日の規則のまま(宣言)。"""
        day = int(step) // self.tpd
        minute = (int(step) % self.tpd) * self.tick_seconds // SECONDS_PER_MINUTE
        return int(self.calendar.weekday(day)), int(minute)

    # ---- 原因・雇用 ----
    def cause(self, name: str) -> Any:
        return self.causes.get(str(name))

    def llm_cause(self, call_id: Any) -> Any:
        """〔検収 A1〕呼の id → 原因 ``LlmCall(call_id)``(1-3 の型・economy は engine.events を読めない=依存逆転)。"""
        from shibuya.engine.events.log import LlmCall

        return LlmCall(str(call_id))

    def employment(self, day: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """その日の締めの時刻に効いている雇用の行(体 → 雇用主の組織=部門 雇用主・店=部門 店舗)を体ごとに 1 行(最初の行)。"""
        from shibuya.engine.ledger_api import SECTOR_EMPLOYER, SECTOR_STORE
        from shibuya.engine.rights.ledger import AGENT, EMPLOY, ORG, STORE

        e = np.zeros(0, dtype=np.int64)
        rights = getattr(self.runner, "rights", None) if self.runner is not None else None
        if rights is None:
            return e, e, e
        t_ns = self.close_step(day) * self.tick_seconds * NS_PER_SECOND
        ha, oa = rights.pairs(EMPLOY, AGENT, ORG, t_ns)
        hs, os_ = rights.pairs(EMPLOY, AGENT, STORE, t_ns)
        who = np.concatenate([ha, hs]).astype(np.int64)
        sec = np.concatenate([np.full(ha.size, SECTOR_EMPLOYER, np.int64), np.full(hs.size, SECTOR_STORE, np.int64)])
        idx = np.concatenate([oa, os_]).astype(np.int64)
        if who.size == 0:
            return e, e, e
        _u, first = np.unique(who, return_index=True)
        first = np.sort(first)
        return who[first], sec[first], idx[first]

    def record(self) -> dict[str, Any]:
        """manifest の ``economy.stage2.plan``(暦・縮小の比・労働時間の出どころ)。"""
        return {"payday_rule": f"毎月 {PAYDAY_DAY_OF_MONTH} 日・土休なら前の営業日(暦の口)",
                "population_scale": self.population_scale, "hours_source": self.hours_source,
                "hourly_source": "最低賃金(規則の表・asof)", "external_store_sales": "0(範囲の外の取引先の資料なし)"}


def atm_open_cells(plan: Stage2Plan, step: int) -> np.ndarray:
    """刻み ``step`` に営業中の ATM のあるセル(``(n_cells,)`` bool・ATM の表が無ければ全部 False)。"""
    atms = plan.atms
    if atms is None or atms.n == 0:
        return np.zeros(0 if atms is None else int(atms.n_cells), dtype=bool)
    wd, minute = plan.weekday_minute(step)
    return atms.open_cells(wd, minute)


def money_stage2(ledger_bundle: Any) -> Any:
    """台帳の束から economy の段階 2 の中身(``MoneyStage2``)を引く(腕の無いランは ``None``)。"""
    money = getattr(ledger_bundle, "money", None) if ledger_bundle is not None else None
    return getattr(money, "stage2", None) if money is not None else None


def population_total(world_dir: Any) -> int | None:
    """W16 母集団の体の数(縮小ランの比の分母・Parquet の見出しだけを読む)。無ければ ``None``。"""
    if world_dir is None:
        return None
    from shibuya.agents.population import POPULATION_FILE

    p = Path(world_dir) / POPULATION_FILE
    if not p.exists():
        return None
    import pyarrow.parquet as pq

    return int(pq.read_metadata(p).num_rows)


def attach(ledger_bundle: Any, *, schedule: Any, weekly: Any, calendar: Any, world: Any, n_agents: int,
           tick_seconds: int, pop: Any = None, world_dir: Any = None) -> Stage2Plan | None:
    """腕が on なら段階 2 を組み立てて金の台帳に挿す(世帯の初期の財布の前=``resolve.initialize`` の前に呼ぶ)。

    Returns:
        ``Stage2Plan``(腕が off・金の台帳が無いランは ``None``=何もしない)。
    """
    if _ARM != ARM_ON:
        return None
    money = getattr(ledger_bundle, "money", None) if ledger_bundle is not None else None
    if money is None or not hasattr(money, "attach_stage2"):
        return None
    from shibuya.engine.events.log import Process

    atms = _ATM_OVERRIDE if _ATM_OVERRIDE is not None else build_atm_table(world)
    hours, src = weekly_work_hours(weekly, n_agents)
    total = population_total(world_dir) if pop is not None else None
    scale = (float(n_agents) / float(total)) if total else None
    plan = Stage2Plan(parts=_PARTS, kinds=np.asarray(schedule.kind)[: int(n_agents)], monthly_hours=hours,
                      hours_source=src, atms=atms, calendar=calendar, tick_seconds=tick_seconds, n_agents=n_agents,
                      population_scale=scale, causes={n: Process(n) for n in CAUSE_NAMES})
    money.attach_stage2(plan)
    return plan
